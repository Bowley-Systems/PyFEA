import matplotlib.pyplot as plt

from pyfea import dimensionless
from pyfea.models.tubular_linear_motor.main import TubularLinearMotor
from pyfea.solver.femm.domains.magnetostatic.solver import FEMMMagnetostaticSolver
from pyfea.solver.femm.domains.thermostatic.solver import FEMMThermostaticSolver

from pyfea.solver.solver_outputs import (
    SolverOutputs, CircuitOptions, MagneticOptions, ThermalOptions
)

# Defines configuration file path and solver output file path
path_lib = "examples/linear_motor/default_configuration.uiv"
solver_folder = "examples/linear_motor"

# Defines the magneto and thermo solvers
magneto = FEMMMagnetostaticSolver(solver_folder)
thermo = FEMMThermostaticSolver(solver_folder)

# Defines the tubular linear motor model
tubular = TubularLinearMotor(path_lib)

# Creates and solves a magnetostatic problem to get resistance
domain, circuit = tubular.build_domain(magneto)
magneto.setup(domain)

magneto_outputs = SolverOutputs()
magneto_outputs.add_circuit(circuit[1], CircuitOptions.RESISTANCE)
magneto_outputs.add_magnetic(tubular.SLOT_ID, MagneticOptions.VOLUME)

magneto_results = magneto.solve(magneto_outputs)

# Calculates the maximum current with that resistance
supply_voltage = tubular.config.circuit.supply_voltage
maximum_current = supply_voltage / magneto_results.phase_b.resistance

print(" ==== Motor Magnetostatic Results === ")
print(f"Resistance: {magneto_results.phase_b.resistance:.3f}")
print(f"volume: {magneto_results.element_1.volume:.3f}")

# Creates a thermostatic problem to get operating temperature at difference current
domain, source = tubular.build_domain(thermo)
thermo.setup(domain)
thermal_outputs = SolverOutputs()
thermal_outputs.add_thermal(tubular.SLOT_ID, ThermalOptions.AVERAGE_TEMPERATURE)
thermal_outputs.add_thermal(tubular.POLE_ID, ThermalOptions.AVERAGE_TEMPERATURE)

currents = []
slot_tem = []
pole_tem = []
for index in range(1, 10):
    current = (maximum_current / 10) * index
    power = current ** 2 * magneto_results.phase_b.resistance
    volumetric = power / magneto_results.element_1.volume
    
    thermo.update_heat_source(source, volumetric)
    thermo_results = thermo.solve(thermal_outputs)
    
    print(f" === Motor Thermostatic results at {current:.3f}, {power:.3f}")
    print(f"Slot average temperature: {thermo_results.element_1.average_temperature}")
    print(f"Pole average temperature: {thermo_results.element_3.average_temperature}")
    
    # Appends values for plotting
    currents.append(current.magnitude)
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
    f'Linear Motor - Constant Voltage Mode\n'
    f'V = {voltage:.2f} | h = {cooling:.2f}'
)

ax.legend()
ax.grid(True)

fig.tight_layout()
plt.show(block=True)