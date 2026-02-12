"""
Filename: tubular_motor.py

Description:
    Magnetostatic into thermostatic co-simulation loop for
    modelling temperature raise via resistive losses within
    a tubular linear motor
    
    This example shows how pyfea can be used to construct
    co-simulation pipelines however geometry/metadata construction
    is handled by the 'TubularLinearMotor' for briefness.
    
    NOTE: 
    Ignore import namespace; pyfea namespace hasn't been
    streamlined yet.
"""

import matplotlib.pyplot as plt

from pyfea.models.tubular_linear_motor.main import TubularLinearMotor
from pyfea.solver.femm.domains.magnetostatic.solver import FEMMMagnetostaticSolver
from pyfea.solver.femm.domains.thermostatic.solver import FEMMThermostaticSolver

from pyfea.solver.solver_outputs import (
    SolverOutputs, CircuitOptions, MagneticOptions, ThermalOptions
)

# Defines configuration file path and solver output folder path
path_lib = "examples/thermal_analysis_linear_motor/default_configuration.uiv"
solver_folder = "examples/thermal_analysis_linear_motor"

# Defines the magneto and thermo solvers
magneto = FEMMMagnetostaticSolver(solver_folder)
thermo = FEMMThermostaticSolver(solver_folder)

# Defines the tubular linear motor model
tubular = TubularLinearMotor(path_lib)

# Creates and solves a magnetostatic problem to get resistance
domain = tubular.build_domain(magneto)
magneto.setup(domain)

magneto_outputs = SolverOutputs()
magneto_outputs.add_circuit(tubular.PHASES[1], CircuitOptions.RESISTANCE)
magneto_outputs.add_magnetic(tubular.SLOT_ID, MagneticOptions.VOLUME)

magneto_results = magneto.solve(magneto_outputs)

# Calculates the maximum current with that resistance
supply_voltage = tubular.config.circuit.supply_voltage
maximum_current = supply_voltage / magneto_results.phase_b.resistance

print(" ==== Motor Magnetostatic Results === ")
print(f"Resistance: {magneto_results.phase_b.resistance:.3f}")
print(f"volume: {magneto_results.element_1.volume:.3f}")

# Creates a thermostatic problem to get operating temperature at difference current
domain = tubular.build_domain(thermo)
thermo.setup(domain)
thermal_outputs = SolverOutputs()
thermal_outputs.add_thermal(tubular.SLOT_ID, ThermalOptions.AVERAGE_TEMPERATURE)
thermal_outputs.add_thermal(tubular.POLE_ID, ThermalOptions.AVERAGE_TEMPERATURE)
thermo_results = thermo.solve(thermal_outputs)

currents = []
slot_tem = []
pole_tem = []

last_pole_tem = thermo_results.element_1.average_temperature
last_slot_tem = thermo_results.element_3.average_temperature

for index in range(1, 10):
    voltage = (supply_voltage / 10) * index
    magneto.update_temperature(tubular.stator_poles_material, last_pole_tem)
    magneto.update_temperature(tubular.armature_slots_material, last_slot_tem)

    magneto_results = magneto.solve(magneto_outputs)
    resistance = magneto_results.phase_b.resistance
    maximum_current = voltage / resistance

    power = maximum_current ** 2 * magneto_results.phase_b.resistance
    volumetric = power / magneto_results.element_1.volume
    
    thermo.update_heat_source(tubular.armature_slots_material, volumetric)
    thermo_results = thermo.solve(thermal_outputs)
    
    print(f" === Motor results at {maximum_current:.3f}, {resistance:.3f}, {power:.3f}")
    print(f"Slot average temperature: {thermo_results.element_1.average_temperature}")
    print(f"Pole average temperature: {thermo_results.element_3.average_temperature}")
    
    last_pole_tem = thermo_results.element_3.average_temperature
    last_slot_tem = thermo_results.element_1.average_temperature

    # Appends values for plotting
    currents.append(maximum_current.magnitude)
    slot_tem.append(thermo_results.element_1.average_temperature.magnitude)
    pole_tem.append(thermo_results.element_3.average_temperature.magnitude)
    

plt.style.use("seaborn-v0_8-darkgrid")

fig, ax = plt.subplots(figsize=(8, 5))

ax.set_xlabel('Current (A)')
ax.set_ylabel('Temperature (K)')

ax.plot(
    currents, slot_tem,
    marker='o', linewidth=2,
    label='Slot temperature'
)

ax.plot(
    currents, pole_tem,
    marker='s', linewidth=2,
    label='Pole temperature'
)

cooling = tubular.config.thermal.convection_coefficient
voltage = tubular.config.circuit.supply_voltage
ax.set_title(
    f'Linear Motor \n Convection Coefficient = {cooling:.2f}'
)

ax.legend()
ax.grid(True)

fig.tight_layout()
plt.show(block=True)