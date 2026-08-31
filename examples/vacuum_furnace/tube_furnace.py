"""
Filename: vacuum_furnace

Description:
    Thermostatic simulation using FEMM solver to 
    calculate the temperature under asymptotic
    diffusion conditions.
"""

from math import pi
from pathlib import Path

from pyfea import Parser, linear_interpolate, mm, nullset, kelvin
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder, ThermalData
from pyfea.domain.geometry.domain import Domain, BoundaryType, CoordinateSystem

from pyfea.solver.solver_outputs import SolverOutputs, ThermalOptions
from pyfea.solver.femm.domains.thermostatic.solver import FEMMThermostaticSolver

# FEA file output
BASE_DIR = Path(__file__).parent
param = Parser.open(BASE_DIR / "parameters.uiv")

# Materials
manager = MaterialManager()
environmental = manager.use_material(param.problem.environmental)
sample_area = manager.use_material(param.sample.material)
tube_material = manager.use_material(param.tube.material)
heater_material = manager.use_material(param.heater.material)
insulation_material = manager.use_material(param.insulation.material)

# Initial radius and radial thicknesses
initial_radius = param.sample.radial_length

tube_thickness = param.tube.radial_thickness
tube_radius = initial_radius + tube_thickness

heater_thickness = param.heater.radial_thickness
heater_radius = tube_radius + heater_thickness

insulation_thickness = param.insulation.radial_thickness
insulation_radius = heater_radius + insulation_thickness

# Builds the sample area
container = Builder.rectangle((0 * mm, 0 * mm), initial_radius, param.sample.axial_length)
meta_data = ThermalData(1 * nullset, sample_area)
sample_container = Builder.promote_to_part(container, meta_data)

# Builds the tube around the sample
tube = Builder.rectangle(
    (0 * mm, - tube_thickness),
    param.sample.radial_length + tube_thickness, 
    param.tube.axial_length + 2 * tube_thickness
)

csg_glass_tube = tube.subtract(container)
glass_tube = Builder.promote_to_part(csg_glass_tube, ThermalData(1 * nullset, tube_material))

# Builds the resistive heater
area = heater_thickness * param.heater.axial_length
wire_area = param.heater.wire_diameter ** 2

effective_area = area * param.heater.fill_factor
turns = int(effective_area / wire_area)

avg_radius = (tube_radius + heater_radius) / 2
length = (2 * pi * avg_radius) * turns

conductivity = heater_material.electrical.temperature_conductivity
conductivity = linear_interpolate(conductivity, param.problem.temperature)
r_linear = 1 / (conductivity * wire_area)

resistance = r_linear * length
current = param.problem.constant_current
if param.problem.supply_limit / resistance < current:
    current = param.problem.supply_limit / resistance

power = current**2 * resistance

# Calculate volumes
inner = pi * tube_radius **2 * param.heater.axial_length
outer = pi * heater_radius ** 2 * param.heater.axial_length
volume = outer - inner

volumetric_heating = power / volume

heater = Builder.rectangle(
    (tube_radius, (param.tube.axial_length - param.heater.axial_length) / 2), 
    heater_radius, param.heater.axial_length
)

heater_csg = heater.subtract(csg_glass_tube)
meta_data = ThermalData(2 * nullset, heater_material, volumetric_heating=volumetric_heating)
heater = Builder.promote_to_part(heater_csg, meta_data)

# Builds the insulation around the heat and sample
insulation = Builder.rectangle(
    (tube_radius, 0 * mm), insulation_radius, param.insulation.axial_length
)
csg_insulation = insulation.subtract(container)
csg_insulation = csg_insulation.subtract(csg_glass_tube)
csg_insulation = csg_insulation.subtract(heater_csg)
insulation = Builder.promote_to_part(
    csg_insulation, ThermalData(3 * nullset, insulation_material)
)

# Defines problem domain
domain_shape = Builder.rectangle(
    (0 * mm, -15 * tube_thickness),
    2 * insulation_radius, param.tube.axial_length + 30 * tube_thickness,
)

conditions = ThermalData(
    5 * nullset, environmental,
    temperature=param.problem.temperature,
    convection_coefficient=param.problem.convection
)

simulation_domain = Domain(
    parts               =   (sample_container, glass_tube, heater, insulation),
    boundary_type       =   BoundaryType.DIRICHLET,
    meta_data           =   conditions,
    coordinate_system   =   CoordinateSystem.AXI_SYMMETRIC,
    shape               =   domain_shape,
    temperature         =   297.15 * kelvin
)

solver = FEMMThermostaticSolver(BASE_DIR)
solver.setup(simulation_domain, "tube_furnace")

# Defines required outputs
outputs = SolverOutputs()
outputs.add_thermal(sample_container, ThermalOptions.average_temperature)


results = solver.solve(outputs)
temp = results[sample_container].average_temperature

print("==== tube_furnace ====")
print(f"Resistance: {resistance:.3f}")
print(f"Power: {volumetric_heating:.3f}")
print(f"Tube temperature: {temp:.3f}")
print("======================")