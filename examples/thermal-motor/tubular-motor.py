"""
Filename: thermal-motor.py
Description:
    Thermostatic model of a linear tubular motor 
    using FEMM solver to calculate the static
    operational temperature.
    
    This example shows how to model thermostatic
    problems within pyfea.
    
    NOTE: 
    Ignore import namespace; pyfea namespace hasn't been
    streamlined yet. 
"""

from math import pi
from pyfea import millimeter as mm, dimensionless, watt, kelvin, meter

from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder

from pyfea.domain.geometry.elements.metadata import ThermalData
from pyfea.solver.femm.domains.thermostatic.solver import FEMMThermostaticSolver

from pyfea.domain.geometry.domain import Domain, BoundaryType
from pyfea.domain.geometry.definitions import CoordinateSystem

from pyfea.solver.solver_outputs import RequestedOutputs, ThermalOptions
# Model variables

number_pairs = 2 * dimensionless
boundary_pairs = 1 * dimensionless
number_slots = 12 * dimensionless

armature_core_inner_radius = 6.5 * mm
armature_coil_inner_radius = 7 * mm
armature_core_outer_radius = 10 * mm
armature_coil_axial_length = 2 * mm
armature_core_axial_length = 1.33 * mm

stator_magnet_outer_radius = 5 * mm
stator_magnet_axial_length = 10 * mm

stator_pipe_outer_radius = 6 * mm

air_volume = pi * armature_coil_inner_radius ** 2 * armature_coil_axial_length
core_slot_volume = pi * armature_core_outer_radius ** 2 * armature_coil_axial_length
slots_volume = (core_slot_volume - air_volume) * number_slots

power = 100 * watt
resistance_power_loss = 3 / 10 * power

volumetric_heating = resistance_power_loss / slots_volume
volume_heating_name = 1 * dimensionless

# FEA file output
folder_location = "examples/thermal-motor/"

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("pure_iron")
copper = manager.use_material("pure_copper")
stc_air = manager.use_material("stc_air")
pa6cf = manager.use_material("isotropic_pa6cf")
carbon_fibre = manager.use_material("isotropic_carbon_fibre")
NdFeB = manager.use_material("NdFeB")


# Builds geometry using parametric CSG
total_poles = 4 * boundary_pairs + 2 * number_pairs
slot_pitch = armature_coil_axial_length + armature_core_axial_length
armature_length = slot_pitch * number_slots

pole_pitch = armature_length / (2 * number_pairs)
if pole_pitch > stator_magnet_axial_length: 
    msg = "Design failed to generate due to overlapping poles: "
    msg += f"{pole_pitch} : {stator_magnet_axial_length}"
    raise ValueError(msg)

tube = Builder.create_rectangle(
    (stator_magnet_outer_radius, - total_poles * pole_pitch / 2),
    stator_pipe_outer_radius - stator_magnet_outer_radius,
    total_poles * pole_pitch
)

armature = Builder.create_rectangle(
    (armature_core_inner_radius, - armature_length / 2), 
    armature_core_outer_radius - armature_core_inner_radius, armature_length
)

slots = []
for slot in range(0, number_slots.value):
    offset = - (armature_length) / 2 + armature_core_axial_length / 2
    bottom_left = offset + slot * slot_pitch
    
    # Subtracts coil slot from armature material
    coil_subtract = Builder.create_rectangle(
        (armature_coil_inner_radius, bottom_left),
        armature_core_outer_radius, armature_coil_axial_length
    )
    armature = armature.subtract(coil_subtract)
    
    # Adds the coil shape to a list
    slots.append(
        Builder.create_rectangle(
            (armature_coil_inner_radius, bottom_left),
            armature_core_outer_radius - armature_coil_inner_radius, 
            armature_coil_axial_length
        )
    )

poles = []
for pole in range(0, total_poles.value):
    offset = - total_poles * pole_pitch / 2
    bottom_left = offset + pole * pole_pitch
    poles.append(
        Builder.create_rectangle(
            (0 * mm, bottom_left),
            stator_magnet_outer_radius, pole_pitch
        )
    )

parts = []
parts.append(Builder.promote_to_part(armature, ThermalData(1 * dimensionless, pa6cf)))
parts.append(Builder.promote_to_part(tube, ThermalData(2 * dimensionless, carbon_fibre)))

data = ThermalData(1 * dimensionless, copper, volumetric_heating = volumetric_heating)
for slot in slots: 
    parts.append(Builder.promote_to_part(slot, data))
    
for pole in poles:
    parts.append(Builder.promote_to_part(pole, ThermalData(2 * dimensionless, NdFeB)))
    
domain_shape = Builder.create_rectangle(
    (0 * mm, -total_poles * pole_pitch * 1.2 / 2),
    armature_core_outer_radius * 1.2, total_poles * pole_pitch * 1.2
)

simulation_domain = Domain(
    parts               =   parts, 
    boundary_type       =   BoundaryType.CONVECTION, 
    meta_data           =   ThermalData(
        4 * dimensionless, stc_air, 
        temperature = 298.15 * kelvin,
        convection_coefficient = 100 * (watt / (meter **2 * kelvin))
    ),
    coordinate_system   =   CoordinateSystem.AXI_SYMMETRIC,
    shape               =   domain_shape
)

solver = FEMMThermostaticSolver(folder_location)
solver.setup(simulation_domain)

RequestedOutputs.add_thermal(1 * dimensionless, ThermalOptions.AVERAGE_TEMPERATURE)
RequestedOutputs.add_thermal(2 * dimensionless, ThermalOptions.AVERAGE_TEMPERATURE)

results = solver.solve(RequestedOutputs)


print(f"==== Motor Performance =====")
print(f"Resistance losses: {resistance_power_loss:.3f} at {298.15 * kelvin}")
print(f"Average temperature of slots: {results.element1.average_temperature:.3f}")
print(f"Average temperature of stator: {results.element2.average_temperature:.3f}")