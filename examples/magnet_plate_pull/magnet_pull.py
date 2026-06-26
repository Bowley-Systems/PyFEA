"""
Filename: magnet_plate_pull.py

Description:
    Magnetostatic magnet attraction force simulation using 
    FEMM solver to get force vs temperature curve due to 
    the magnet losing coercivity. 
    
    This example shows a simple usage of pyfea for analysis.
"""

from pathlib import Path

from pyfea import N, K, mm, nullset
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder, MagneticData
from pyfea.domain.geometry.domain import Domain, BoundaryType, CoordinateSystem

from pyfea.solver.solver_outputs import SolverOutputs, MagneticOptions, ImageOptions
from pyfea.solver.femm.domains.magnetostatic.solver import FEMMMagnetostaticSolver

# FEA file output
BASE_DIR = Path(__file__).parent

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("iron")
NdFeB_45 = manager.use_material("NdFeB", grade="N45")
stc_air = manager.use_material("air")
print(NdFeB_45.tree())
# Builds the magnet and iron plate
plate = Builder.rectangle((0 * mm, 0 * mm), 100 * mm, 5 * mm)
plate = Builder.promote_to_part(plate, MagneticData(1 * nullset, iron))

magnet = Builder.rectangle((30 * mm, 45 * mm), 40 * mm, 10 * mm)
magnet = Builder.promote_to_part(
    magnet, MagneticData(2 * nullset, NdFeB_45, magnetization=90 * nullset)
)

# Defines problem domain
domain_shape = Builder.rectangle((-10 * mm, -10 * mm), 120 * mm, 120 * mm)
domain_temperature = 297.15 * K

simulation_domain = Domain(
    parts               =   (plate, magnet),
    boundary_type       =   BoundaryType.DIRICHLET,
    meta_data           =   MagneticData(3 * nullset, stc_air),
    coordinate_system   =   CoordinateSystem.PLANAR,
    shape               =   domain_shape,
    temperature         =   domain_temperature
)

# Defines required outputs
outputs = SolverOutputs()
outputs.add_magnetic(magnet, MagneticOptions.force_stress_tensor)
outputs.add_image(ImageOptions.field_contour)

solver = FEMMMagnetostaticSolver(BASE_DIR / "")
solver.setup(simulation_domain, "magnet_plate", depth=40 * mm)

temperature_step = 5 * K
max_temperature = 350 * K

temperature = []
magnetic_force = []

# print("========== Temperature Response ==========")
# while domain_temperature < max_temperature:
solver.update_temperature((plate, magnet), domain_temperature)
results = solver.solve(outputs)

#     # Extracts and calculates force
#     fx, fy = results[magnet].force_stress_tensor
#     force_mag = (fx**2 + fy**2) ** 0.5

#     print(f"Solved model at {domain_temperature:.3f}, force {force_mag:.3f}")

#     # Appends and increases domain temperature
#     temperature.append(domain_temperature)
#     magnetic_force.append(force_mag)

#     domain_temperature += temperature_step

# # Calculates the N/K gradient across the simulated range
# dF_DT = 0.0 * (N / K)
# for i in range(1, len(temperature)):
#     dF_DT += (magnetic_force[i] - magnetic_force[i-1]) / (temperature[i] - temperature[i-1])

# dF_DT /= len(temperature) - 1

# # Calculates the average force over the operational range
# avg = 0.0 * N
# for i in magnetic_force:
#     avg += i
# avg /= len(magnetic_force)


# print("===== NdFeB_45 Performance =====")
# print(f"Temperature range: {min(temperature)} to {max(temperature)}")
# print(f"Gradient | force/temperature: {dF_DT:.3f}")
# print(f"Average Pulling force: {avg:.3f}")
# print("=====================================")
