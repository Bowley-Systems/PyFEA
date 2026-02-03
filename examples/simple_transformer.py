"""
File: simple_transformer.py

Description:
    Script for testing features as their built out
    in pyfea
    
    NOTE: THIS IS JUST A CONCEPT MODEL I WROTE FOR A MENTAL MODEL
"""

from math import pi

from pyfea import millimeter as mm, ampere as A, hertz as Hz, dimensionless
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder
from pyfea.domain.geometry.elements.metadata import MagneticData
from pyfea.domain.geometry.domain import Domain, BoundaryType

from pyfea.domain.circuits import circuit
from pyfea.solver import FEMMagneticSolver, Outputs

# FEA file output
folder_location = "examples/electromagnet/outputs/"

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("pure_iron")
copper = manager.use_material("pure_copper")
stc_air = manager.use_material("stc_air")

# Defines the 'phase A' circuit
phase_a = circuit.define("Phase A", 1 * A)

# Builds the transformer core
iron_square = Builder.create_rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
iron_cutout = Builder.create_rectangle((15 * mm, 20 * mm), 85 * mm, 60 * mm)

core = iron_square.subtract(iron_cutout)
core = core.extrude(10 * mm)
core = Builder.promote_to_part(core, MagneticData(1 * dimensionless, iron))

# Positive coil slot
positive_slot = Builder.create_rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = positive_slot.extrude(10 * mm)
positive_slot = Builder.promote_to_part(
    positive_slot, 
    MagneticData(2 * dimensionless, copper, phase_a, 100 * dimensionless, 0.1 * mm)
)

# Negative coil slot
negative_slot = Builder.create_rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = negative_slot.extrude(10 * mm)
negative_slot = Builder.promote_to_part(
    negative_slot, 
    MagneticData(2 * dimensionless, copper, phase_a, -100 * dimensionless, 0.1 * mm)
)

# Defines problem domain
domain_shape = Builder.create_circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)
domain_shape.extrude(10 * mm)
simulation_domain = Domain(
    (positive_slot, negative_slot, core), 
    3 * dimensionless, BoundaryType.NEUMANN, stc_air, domain_shape
)

# Solve the magnetic problem and returns; all problems from selector
solver = FEMMagneticSolver(
    folder_location, simulation_domain 
    [Outputs.circuit_inductance, Outputs.circuit_resistance], phase_a
)
result = solver.solve()

# Assumed dynamic frequency of 50 HZ
x_inductive = 2 * pi * result.circuit_inductance * 50 * Hz
impedance = (result.circuit_resistance ** 2 + x_inductive ** 2) ** 0.5

print(f"FEMM outputs: {result!result}")
print(f"Approximate AC impedance at 50 Hz: {impedance}")
