"""
Filename: simple_transformer.py
Description:
    Magnetostatic u-transformer simulation using 
    FEMM solver to calculate the inductance and 
    approximate impedance at 50Hz.
    
    This example shows how pyfea can be used to 
    construct complex geometry without touching primitives
    
    NOTE: 
    Ignore import namespace; pyfea namespace hasn't been
    streamlined yet.
"""

from math import pi

from pyfea import millimeter as mm, dimensionless, ampere as A, hertz as Hz
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder
from pyfea.domain.geometry.elements.metadata import MagneticData
from pyfea.domain.geometry.domain import Domain, BoundaryType
from pyfea.domain.geometry.definitions import CoordinateSystem
from pyfea.domain.circuits.builder import Circuit, Configuration

from pyfea.solver.solver_outputs import RequestedOutputs, CircuitOptions
from pyfea.solver.femm.domains.magnetostatic.solver import FEMMMagnetostaticSolver

# FEA file output
folder_location = "examples/electromagnet/outputs/"

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("pure_iron")
copper = manager.use_material("pure_copper")
stc_air = manager.use_material("stc_air")

# Builds the transformer core
iron_square = Builder.create_rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
iron_cutout = Builder.create_rectangle((15 * mm, 25 * mm), 85 * mm, 60 * mm)

core = iron_square.subtract(iron_cutout)
core = core.smoothing_fillets(7 * mm)
core = Builder.promote_to_part(core, MagneticData(1 * dimensionless, iron))

# Positive coil slot
phase_a = Circuit("Phase A", 1 * A, Configuration.SERIES)
slot = MagneticData(2 * dimensionless, copper, phase_a, 100 * dimensionless, 0.1 * mm)

positive_slot = Builder.create_rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = Builder.promote_to_part(positive_slot, slot)

# Negative coil slot
slot = MagneticData(2 * dimensionless, copper, phase_a, -100 * dimensionless, 0.1 * mm)
negative_slot = Builder.create_rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = Builder.promote_to_part(negative_slot, slot)

# Defines problem domain
domain_shape = Builder.create_circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)

simulation_domain = Domain(
    parts               =   (positive_slot, negative_slot, core), 
    group               =   3 * dimensionless, 
    boundary_type       =   BoundaryType.DIRICHLET, 
    material            =   stc_air, 
    coordinate_system   =   CoordinateSystem.PLANAR,
    shape               =   domain_shape
)

# Defines required outputs
RequestedOutputs.add_circuit(phase_a, CircuitOptions.RESISTANCE)
RequestedOutputs.add_circuit(phase_a, CircuitOptions.FLUX_LINKAGE)
RequestedOutputs.add_circuit(phase_a, CircuitOptions.CURRENT)

solver = FEMMMagnetostaticSolver(folder_location)
result = solver.solve(simulation_domain, RequestedOutputs, 20*mm)

# Calculates inductance via faraday law of induction
inductance = result.phase_a.flux_linkage / result.phase_a.current

# Calculates impedance assumes no capacitive impedance
frequency = 50 * Hz
x_inductive = 2 * pi * inductance * frequency
impedance = (result.phase_a.resistance ** 2 + x_inductive ** 2) ** 0.5

print(f"==== U-transformer Performance =====")
print(f"Resistance: {result.phase_a.resistance:.3f}")
print(f"inductance: {inductance:.3f}")
print(f"impedance at {frequency:.3f} : {impedance:.3f}")