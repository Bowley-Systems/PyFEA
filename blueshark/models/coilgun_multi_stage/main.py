"""
File: main.py
Author: William Bowley
Version: 0.1
Date: 2025-10-19

Description:
    Model of a multi stage coilgun for use in
    the simulation framework.

    Parameters are defined through the unpacker dependency
"""

from blueshark.domain.material_manager.manager import MaterialManager
from blueshark.renderer.renderer_interface import (
    BaseRenderer, MagneticRenderer
)
from blueshark.domain.definitions import (
    Units,
    ShapeType,
    Geometry,
    Problem,
    BoundaryType,
    CircuitType,
    CoordinateSystem,
    CurrentPolarity
)

from blueshark.models.coilgun_multi_stage.unpack import CoilGunUnpacker
from blueshark.models.coilgun_multi_stage.physics.number_turns import (
    estimate_turns
)


class MultiStageCoilGun:
    """ Model of a multi stage coil gun (MSCG) """

    def __init__(
        self,
        renderer: BaseRenderer,
        unpacker: CoilGunUnpacker
    ) -> None:
        """ Initializes the class & defines dependencies """
        self.renderer = renderer
        self.manager = MaterialManager()
        self.problem = Problem(
            units=Units.MILLIMETER,
            type=CoordinateSystem.AXI_SYMMETRIC
        )

        # Defines unpacker & load materials parameters
        self.load = unpacker
        self._load_materials()

        # Defines universal & computes geometric parameters
        self.coil_pitch: float = None
        self.gap_activate: float = None
        self.coil_deactivate: float = None
        self.accelerator_length: float = None
        self._compute_geometry()

        # Groups & circuits
        self.BOUNDARY: int = 0
        self.PROJECTILE: int = 1

        # Note: Shifted by 1 to not interfere with the groups before it
        self.COILS: list[int] = [i for i in range(1, self.load.stages+1)]
        self.CIRCUITS: list[str] = [f"{i}" for i in self.COILS]

        # Choose physics strategy based on renderer type
        if isinstance(renderer, MagneticRenderer):
            self.physics_impl = MagneticPhysics(self)
        else:
            msg = f"Unsupported renderer type: {type(renderer)}"
            raise ValueError(msg)

    def build(self) -> None:
        """ Setups the renderer problem, draw motor and sets its properties """
        self.renderer.setup(self.problem.type, self.problem.units)

        # Delegate to physics-specific implementation
        self.physics_impl.build()

    def _load_materials(self) -> None:
        """ Loads materials into class variables. """
        self.coil_material = self.manager.use_material(
            self.load.coil_material,
            wire_diameter=self.load.coil_wire_diameter
        )
        self.shell_material = self.manager.use_material(
            self.load.shell_material
        )
        self.projectile_material = self.manager.use_material(
            self.load.projectile_material
        )
        self.boundary_material = self.manager.use_material(
            self.load.boundary_material
        )

    def _compute_geometry(self) -> None:
        """ Computes geometric features based off parameters """
        # Calculates the coil pitch (start-to-start)
        self.coil_pitch = self.load.coil_axial_length + self.load.stage_gap

        # Have to remove the spacing for the last coil
        self.accelerator_length = self.coil_pitch * self.load.stages
        self.accelerator_length -= self.load.stage_gap

        # Calculates the activate & deactivate lengths
        self.gap_activate = self.load.stage_gap * self.load.activate_fraction
        self.coil_deactivate = (
            self.load.coil_axial_length * self.load.deactivate_fraction
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
    def __init__(self, coilgun: MultiStageCoilGun):
        self.coilgun = coilgun
        self.load = coilgun.load
        self.renderer: MagneticRenderer = coilgun.renderer

    def build(self) -> None:
        """ Called by MultiStageCoilGun.setup() """
        self._create_circuits()
        self._add_stages()
        self._add_projectile()
        self._add_boundary()

    def _add_stages(self) -> None:
        """ Adds the stages to the simulation space """
        # Generates coil origins according to rule:
        # Origin = (coil_inner, coil_pitch * coil + offset)
        origins = []

        offset = -0.5 * self.coilgun.coil_pitch * self.load.stages
        for coil in range(self.load.stages):
            z = self.coilgun.coil_pitch * coil + offset
            r = self.load.coil_inner_radi
            origins.append((r, z))

        # Calculates turns within the coil cross section
        turns = estimate_turns(
            self.load.coil_axial_length,
            self.load.coil_radial_thickness,
            self.load.coil_wire_diameter,
            self.load.coil_fill_factor
        )

        for index, origin in enumerate(origins):
            # Defines the coilgun circuit
            circuit = self.coilgun.CIRCUITS[index]
            group = self.coilgun.COILS[index]

            # Draw the coil  and assign its physical / material properties
            coil = self.coilgun._rectangle_geometry(
                origin,
                self.load.coil_axial_length,
                self.load.coil_radial_thickness
            )

            self.renderer.draw(
                coil,
                self.coilgun.coil_material,
                group,
                circuit=circuit,
                turns=turns,
                polarity=CurrentPolarity.FORWARD
            )

            # Draws the shell if enabled
            if self.load.shell_state:
                origin = (self.load.shell_inner_radi, origin[1])

                # Draw the shell and assign its physical / material properties
                shell = self.coilgun._rectangle_geometry(
                    origin,
                    self.load.shell_axial_length,
                    self.load.shell_radial_thickness
                )
                self.renderer.draw(shell, self.coilgun.shell_material, group)

    def _add_projectile(self) -> None:
        """ Adds the projectile to the simulation space """
        # Projectile origin
        z_offset = -0.5 * self.coilgun.coil_pitch * self.load.stages
        origin = (
            self.load.projectile_inner_radi,
            z_offset - self.load.projectile_axial_length
        )

        # Draw the projectile and assign its physical / material properties
        projectile = self.coilgun._rectangle_geometry(
            origin,
            self.load.projectile_axial_length,
            self.load.projectile_radial_thickness
        )

        group = self.coilgun.PROJECTILE
        self.renderer.draw(projectile, self.coilgun.projectile_material, group)

    def _add_boundary(self) -> None:
        """ Adds the Neumann boundary with a safety margin """
        travel_radi = 0.5 * (self.load.stages + 3) * self.coilgun.coil_pitch
        coil_radi = self.load.coil_outer_radi

        # Creates the geometry with a safety factor of 20%
        shape = Geometry(
            shape=ShapeType.CIRCLE,
            center=(0, -self.load.coil_axial_length),
            radius=max(travel_radi, coil_radi) * 1.2
        )

        self.renderer.draw_domain_boundary(
            shape,
            self.coilgun.boundary_material,
            BoundaryType.NEUMANN,
            self.load.boundary_shells
        )

    def _create_circuits(self) -> None:
        """ Creates circuits for each phase of the motor """
        for circuit in self.coilgun.CIRCUITS:
            self.renderer.create_circuit(
                circuit,
                CircuitType.SERIES
            )


class ThermalPhysics:
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
