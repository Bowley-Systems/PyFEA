"""
Filename: main.py
Description:
    Magnetic and thermal model of a tubular linear 
    motor for usage in co-simulations.
"""

from __future__ import annotations

from pathlib import Path
from math import ceil, sin, pi
from pyfea import (
    ampere as A, meter as M, millimeter as mm, dimensionless, watt, Quantity
)

from pyfea.domain.units import Parser, Configuration 
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.definitions import CoordinateSystem

from pyfea.solver.solver_interface import BaseSolver, MagneticSolver, ThermalSolver
from pyfea.domain.geometry.builder import Builder, VectorGeometry
from pyfea.domain.geometry.elements.vectors import CSGNode
from pyfea.domain.geometry.domain import Domain, BoundaryType
from pyfea.domain.geometry.elements.metadata import MagneticData, ThermalData

from pyfea.domain.circuits.builder import Circuit, Configuration as CircuitConfig


class ModelError(Exception):
    """ Exception for model error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class TubularLinearMotor:
    """ Electro-magneto-thermal-mechanical Linear Motor """
    # Default configuration path
    MODEL_PATH = "default_configuration.uiv"

    # Simulation elements
    ENVIRONMENT_ID = 0 * dimensionless
    SLOT_ID = 1 * dimensionless
    CORE_ID = 2 * dimensionless
    POLE_ID = 3 * dimensionless
    TUBE_ID = 4 * dimensionless 
    
    PHASES = [
        Circuit("phase_a", 0 * A, CircuitConfig.SERIES), 
        Circuit("phase_b", 0 * A, CircuitConfig.SERIES),
        Circuit("phase_c", 0 * A, CircuitConfig.SERIES)
    ]
    
    def __init__(self, configuration_path: Path) -> None:
        """ Initializes the class & defines dependencies """
        self.config = self._get_configuration(configuration_path)
        
        # Material and coordinate system definitions
        self.manager = MaterialManager()
        self.coordinate_system = CoordinateSystem.AXI_SYMMETRIC
        
        # Derived parameters & loads materials
        self._derived_parameters()
        self._load_material()
    
    def build_domain(self, solver: BaseSolver) -> Domain:
        """ Builds the domain based on solver physics domain """
        solver_interfaces = solver.__class__.__bases__

        for solver in solver_interfaces:
            if solver == ThermalSolver:
                return thermal_domain.build(self)

            if solver == MagneticSolver:
                return magnetic_domain.build(self)

        msg = f"{solver_interfaces!r} is not supported by {self.__class__.__name__}"
        raise ModelError(msg)
    
    def build_boundary(self) -> VectorGeometry:
        """ Builds the boundary shape """
        config = self.config
        return Builder.create_rectangle(
            (
                0 * mm, 
                -self.total_poles * self.pole_pitch * 3 / 2
            ),
            config.armature_core.outer_radius * 3,
            self.total_poles * self.pole_pitch * 3
        )
        
    def build_core(self) -> CSGNode:
        """ Builds the core geometry """
        config = self.config   
        core_thickness = (
            config.armature_core.outer_radius - 
            config.armature_core.inner_radius
        )
        
        armature = Builder.create_rectangle(
            (
                config.armature_core.inner_radius, 
                - self.armature_length / 2
            ),
            core_thickness, self.armature_length
        )
        
        for slot in range(0, config.model.number_slots.value):
            offset = (
                - (self.armature_length - config.armature_slots.axial_length) / 2
            )
            bottom_left = offset + slot * self.slot_pitch
            
            # Subtracts slot from core material
            slot_subtract = Builder.create_rectangle(
                (config.armature_slots.inner_radius, bottom_left),
                config.armature_slots.outer_radius - config.armature_slots.inner_radius,
                config.armature_slots.axial_length
            )
            armature.subtract(slot_subtract)
        
        return armature

    def build_slots(self) -> list[VectorGeometry]:
        """ Builds the armature slots which are partly enclosed within the armature """
        config = self.config
        
        slots = []
        for slot in range(0, config.model.number_slots.value):
            offset = (
                - (self.armature_length - config.armature_slots.axial_length) / 2
            )
            bottom_left = offset + slot * self.slot_pitch
            
            slots.append(
                Builder.create_rectangle(
                    (config.armature_slots.inner_radius, bottom_left),
                    config.armature_slots.outer_radius - config.armature_slots.inner_radius,
                    config.armature_slots.axial_length
                )
            )
        
        return slots
  
    def build_tube(self) -> VectorGeometry:
        """ Builds the stator tube which encloses the stator poles """
        config = self.config
        return Builder.create_rectangle(
            (
                config.stator_poles.outer_radius,
                - self.total_poles * self.pole_pitch / 2
            ),
            config.stator_tube.outer_radius - config.stator_tube.inner_radius,
            self.total_poles * self.pole_pitch
        )
    
    def build_poles(self) -> list[VectorGeometry]:
        """ Builds the stator poles which are enclosed within the stator tube """
        config = self.config
        
        poles = []
        for pole in range(0, self.total_poles.value):
            offset = - self.total_poles * self.pole_pitch / 2
            bottom_left = offset + pole * self.pole_pitch
            
            poles.append(
                Builder.create_rectangle(
                    (0 * mm, bottom_left),
                    config.stator_poles.outer_radius, 
                    self.pole_pitch
                )
            )
        return poles
    
    def _load_material(self) -> None:
        """ Builds out the material manager with materials """
        manager = self.manager
        
        # Finds the material in the .uiv material library
        self.environmental_material = manager.use_material(
            self.config.model.environmental_material
        )
        self.armature_core_material = manager.use_material(
            self.config.armature_core.material
        )
        self.armature_slots_material = manager.use_material(
            self.config.armature_slots.material
        )
        self.stator_tube_material = manager.use_material(
            self.config.stator_tube.material
        )
        self.stator_poles_material = manager.use_material(
            self.config.stator_poles.material, grade = self.config.stator_poles.grade
        )
    
    def _derived_parameters(self) -> None:
        """ Calculates derived parameters from base parameters """
        # Segment (number under the armature), boundary (approx for infinite track)
        segment_poles = 2 * self.config.model.number_pairs
        boundary_poles =  4 * self.config.model.boundary_pairs
        self.total_poles = segment_poles + boundary_poles

        # Slot pitch is the distance between adjacent slots (start 1 -> start 2)
        self.slot_pitch = (
            self.config.armature_slots.axial_length + 
            self.config.armature_core.axial_slot_spacing
        )
        
        # Physical length and effective magnetic length of the armature 
        self.armature_length = self.slot_pitch * self.config.model.number_slots
        self.magnetic_armature_length = (
            self.armature_length - self.config.armature_core.axial_slot_spacing
        )
        
        # Pole pitch is the distance between adjacent poles (start 1 -> start 2)
        self.pole_pitch = self.magnetic_armature_length / segment_poles
        
        axial_length = self.config.stator_poles.axial_length
        if self.pole_pitch > axial_length:
            msg = "Failed to derive parameters, overlapping stator poles: "
            msg += f"{self.pole_pitch:.3f} : {axial_length:.3f}"
            raise ModelError(msg)
        
    def _get_configuration(self, path: Path) -> None:
        """ Attempts to resolve user configuration file. Default to model path """
        target = Path(path).expanduser().resolve()
        
        if not target.exists():
            target = Path(__file__).parent / self.MODEL_PATH

        return Parser.open(target, Configuration)
    

class magnetic_domain:
    """ Magnetic Implementation of linear motor """   
    @classmethod
    def calculate_number_turns(cls, default: TubularLinearMotor) -> int:
        """ Calculates the approximate number of turns within the motor """
        config = default.config
        radius = config.armature_slots.outer_radius - config.armature_slots.inner_radius
        
        # Calculates the cross sectional area, wire area and than effective area
        slot_area = radius * config.armature_slots.axial_length
        wire_area = config.armature_slots.wire_diameter ** 2
        
        effective_area = slot_area * config.armature_slots.fill_factor
        turns = ceil(effective_area / wire_area)
        
        if turns < 0:
            msg = f"Derived parameter 'turns' cannot be {turns}. Slots must have non-zero area"
            raise ModelError(msg)

        return turns
    
    @classmethod
    def build(cls, default: TubularLinearMotor) -> tuple[Domain, tuple[Circuit]]:
        """ Builds the magnetic simulation for the tubular linear motor """
        # Builds Armature and Stator geometry
        core, slots = default.build_core(), default.build_slots()
        tube, poles = default.build_tube(), default.build_poles()
    
        # Defines simulation parts via promoting and metadata
        parts = []
        parts.append(
            Builder.promote_to_part(
                core,
                MagneticData(default.CORE_ID, default.armature_core_material)
            )
        )
        
        parts.append(
            Builder.promote_to_part(
                tube,
                MagneticData(default.TUBE_ID, default.stator_tube_material)
            )
        )
        
        # Updates the current based on the configuration
        initial = default.config.numerical.initial_current
        phases = []
        for index, phase in enumerate(default.PHASES):
            phase.current = initial * sin((5 * pi) / 6 + (4 * pi) / 3 * index)
            phases.append(phase)

        turns = cls.calculate_number_turns(default)
        for index, slot in enumerate(slots):
            # Sets phase of slot in pattern [a, b, c] & Alternate polarity slot with pattern
            phase = phases[index % len(phases)]
            polarity = +1 if index % 2 == 0 else -1
            
            parts.append(
                Builder.promote_to_part(
                    slot,
                    MagneticData(
                        default.SLOT_ID, default.armature_slots_material,
                        phase, turns * polarity,
                        default.config.armature_slots.wire_diameter
                    )
                )
            )
            
        for index, pole in enumerate(poles):
            # Alternate magnetization direction every pole (e.g., N-S-N-S)
            pole_magnetization = 90 if index % 2 == 0 else - 90
            
            parts.append(
                Builder.promote_to_part(
                    pole,
                    MagneticData(
                        default.POLE_ID, default.stator_poles_material,
                        magnetization = pole_magnetization * dimensionless
                    )
                )
            )
        
        # Overall simulation problem defined for magnetic
        simulation_domain = Domain(
            parts, BoundaryType.DIRICHLET, 
            MagneticData(default.ENVIRONMENT_ID, default.environmental_material), 
            default.coordinate_system,
            default.build_boundary()
        )

        return simulation_domain
        

class thermal_domain:
    """ Thermal Implementation of linear motor """
    INITIAL_WATTAGE = 0 * watt / M ** 3
    
    @classmethod
    def build(cls, default: TubularLinearMotor) -> tuple[Domain, Quantity]:
        """ Builds the thermal simulation for the tubular linear motor """
        # Builds Armature and Stator geometry
        core, slots = default.build_core(), default.build_slots()
        tube, poles = default.build_tube(), default.build_poles()
        
        # Defines simulation parts via promoting and metadata
        parts = []
        parts.append(
            Builder.promote_to_part(
                core,
                ThermalData(default.CORE_ID, default.armature_core_material)
            )
        )
        
        parts.append(
            Builder.promote_to_part(
                tube,
                ThermalData(default.TUBE_ID, default.stator_tube_material)
            )
        )
        
        data = ThermalData(
            default.SLOT_ID,default.armature_slots_material,
            volumetric_heating=cls.INITIAL_WATTAGE
        )
        for slot in slots: parts.append(Builder.promote_to_part(slot, data))
        
        data = ThermalData(default.POLE_ID, default.stator_poles_material)
        for pole in poles: parts.append(Builder.promote_to_part(pole, data))
        data = ThermalData(
            default.ENVIRONMENT_ID, default.environmental_material,
            temperature=default.config.thermal.atmospheric_temperature,
            convection_coefficient=default.config.thermal.convection_coefficient
        )

        simulation_domain = Domain(
            parts, BoundaryType.CONVECTION, data, default.coordinate_system,
            default.build_boundary()
        )

        return simulation_domain