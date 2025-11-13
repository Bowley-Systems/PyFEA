"""
File: main.py
Author: William Bowley
Version: 0.2
Date: 2025-10-14

Description:
    Basic model of a tubular linear motor for use in
    the simulation framework.

    Parameters are defined through the unpacker dependency
"""

from blueshark.domain.material_manager.manager import MaterialManager
from blueshark.domain.units import MILLIMETER
from blueshark.renderer.renderer_interface import (
    BaseRenderer, MagneticRenderer
)
from blueshark.domain.definitions import (
    ShapeType,
    Geometry,
    Problem,
    BoundaryType,
    CircuitType,
    CoordinateSystem,
    CurrentPolarity
)

from blueshark.models.tubular_linear_motor.unpack import MotorUnpacker
from blueshark.models.tubular_linear_motor.modelling.number_turns import (
    estimate_turns
)


class TubularLinearMotor:
    """ Generic model of a tubular linear motor (TLSM) """

    # Circuits
    PHASES: list[str] = ["a", "b", "c"]

    # Elements
    BOUNDARY: int = -1
    SLOT: int = 1
    POLE: int = 2

    def __init__(
        self,
        renderer: BaseRenderer,
        unpacker: MotorUnpacker
    ) -> None:
        """ Initializes the class & defines dependencies """
        self.renderer = renderer
        self.manager = MaterialManager()
        self.problem = Problem(
            unit=MILLIMETER,
            type=CoordinateSystem.AXI_SYMMETRIC
        )

        # Defines unpacker & load materials parameters
        self.load = unpacker
        self._load_materials()

        # Defines universal parameters
        self.slot_pitch = None
        self.pole_pitch = None
        self.armature_length = None
        self.total_number_poles = None
        self._compute_geometry()

        # Choose physics strategy based on renderer type
        if isinstance(renderer, MagneticRenderer):
            self.physics_impl = MagneticPhysics(self)
        else:
            msg = f"Unsupported renderer type: {type(renderer)}"
            raise ValueError(msg)

    def build(self) -> None:
        """ Setups the renderer problem, draw motor and sets its properties """
        self.renderer.setup(self.problem.type, self.problem.unit)

        # Delegate to physics-specific implementation
        self.physics_impl.build()

    def _load_materials(self) -> None:
        """ Loads materials into class variables. """
        self.slot_material = self.manager.use_material(
            self.load.slot_material,
            wire_diameter=self.load.slot_wire_diameter
        )
        self.pole_material = self.manager.use_material(
            self.load.pole_material,
            grade=self.load.pole_grade
        )
        self.boundary_material = self.manager.use_material(
            self.load.boundary_material,
        )

    def _compute_geometry(self) -> None:
        """ Computes geometric features based off parameters """
        # Calculates the slot pitch (start-to-start)
        self.slot_pitch = (
            self.load.slot_axial_length + self.load.slot_axial_spacing
        )

        # Have to remove the spacing for the last slot
        pattern_length = self.slot_pitch * self.load.number_slots
        pattern_length -= self.load.slot_axial_spacing

        self.armature_length = pattern_length
        # Calculates the pole_pitch (start-to-start)
        self.pole_pitch = self.armature_length / (2 * self.load.number_pairs)

        # Overlapping poles / slots check
        if self.pole_pitch < self.load.pole_axial_length:
            msg = (
                "Design failed to generate due to overlapping poles: "
                f"{self.pole_pitch} : {self.load.pole_axial_length} mm"
            )
            raise ValueError(msg)

        # Extra pairs, added symmetrically on both sides
        self.total_number_poles = (
            4 * self.load.boundary_pairs + 2 * self.load.number_pairs
        )

    def _rectangle_geometry(
        self,
        bottom_left: tuple[float, float],
        axial_length: float,
        radial_thickness: float
    ) -> Geometry:
        """ Returns a rectangular geometry from bottom-left vertex. """
        r, z = bottom_left
        return Geometry(
            shape=ShapeType.RECTANGLE,
            enclosed=True,
            points=[
                (r, z),
                (r + radial_thickness, z),
                (r + radial_thickness, z + axial_length),
                (r, z + axial_length)
            ]
        )


""" Physics specific implementations """


class MagneticPhysics:
    """ Magnetic Implementation of the TLSM """
    def __init__(self, motor: TubularLinearMotor):
        self.motor = motor
        self.load = motor.load
        self.renderer: MagneticRenderer = motor.renderer

    def build(self) -> None:
        """ Called by TubularLinearMotor.setup() """
        self._add_stator()
        self._create_circuits()
        self._add_armature()
        self._add_boundary()

    def _add_armature(self) -> None:
        """ Adds the armature to the simulation space """
        # Generates slot origins according to rule:
        # Origin = (slot_inner, slot_pitch * slot + offset)
        origins = []

        offset = -0.5 * self.motor.slot_pitch * self.load.number_slots
        for slot in range(self.load.number_slots):
            z = self.motor.slot_pitch * slot + offset
            r = self.load.slot_inner_radius
            origins.append((r, z))

        # Calculates turns within the slot cross section
        turns = estimate_turns(
            self.load.slot_axial_length,
            self.load.slot_radial_thickness,
            self.load.slot_wire_diameter,
            self.load.fill_factor
        )

        for index, origin in enumerate(origins):
            # Sets phase of slot in pattern [a, b, c]
            phases = self.motor.PHASES
            phase = phases[index % len(phases)]

            # Alternate polarity slot with pattern
            if index % 2 == 0:
                polarity = CurrentPolarity.FORWARD
            else:
                polarity = CurrentPolarity.REVERSE

            # Draw the slot and assign its physical / material properties
            slot = self.motor._rectangle_geometry(
                origin,
                self.load.slot_axial_length,
                self.load.slot_radial_thickness,
            )

            self.renderer.draw(
                slot,
                self.motor.slot_material,
                self.motor.SLOT,
                circuit=phase,
                turns=turns,
                polarity=polarity
            )

    def _add_stator(self) -> None:
        """ Adds the stator to the simulation space """
        # Generates pole origins according to rule:
        # Origin = (0, pitch * n - offset)
        origins = []

        offset = self.motor.total_number_poles * self.motor.pole_pitch / 2
        for pole in range(self.motor.total_number_poles):
            r = 0
            z = self.motor.pole_pitch * pole - offset
            origins.append((r, z))

        for index, origin in enumerate(origins):
            # Alternate magnetization direction every pole (e.g., N-S-N-S)
            pole_magnetization = 90 if index % 2 == 0 else - 90

            # Draw the pole and assign its physical / material properties
            pole = self.motor._rectangle_geometry(
                origin,
                self.load.pole_axial_length,
                self.load.pole_radial_thickness,
            )

            self.renderer.draw(
                pole,
                self.motor.pole_material,
                self.motor.POLE,
                magnetization=pole_magnetization
            )

    def _add_boundary(self) -> None:
        """ Adds the Neumann boundary with a safety margin """
        stator = 0.5 * self.motor.total_number_poles * self.motor.pole_pitch
        armature = self.load.slot_outer_radius

        # Creates the geometry with a safety factor of 20%
        shape = Geometry(
            shape=ShapeType.CIRCLE,
            center=(0, -self.load.pole_axial_length),
            radius=max(stator, armature) * 1.2
        )

        self.renderer.draw_domain_boundary(
            shape,
            self.motor.boundary_material,
            BoundaryType.NEUMANN,
            self.load.boundary_shells
        )

    def _create_circuits(self) -> None:
        """ Creates circuits for each phase of the motor """
        for phase in self.motor.PHASES:
            self.renderer.create_circuit(
                phase,
                CircuitType.SERIES
            )


class ThermalPhysics:
    """ Template for thermal physics """
    """ Thermal implementation of the tubular linear motor """
    def __init__(self, motor):
        self.motor = motor

    def setup(self):
        self._add_heating_elements()
        self._add_convection_boundaries()

    def _add_heating_elements(self):
        # Thermal-specific logic
        pass

    def _add_convection_boundaries(self):
        # Thermal-specific logic
        pass
