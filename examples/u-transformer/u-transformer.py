"""
Filename: u-transformer.py

Description:
    Magnetostatic u-transformer simulation using 
    FEMM solver to calculate the inductance and 
    approximate impedance at 50Hz.
    
    This example shows how pyfea can be used to 
    construct geometry without touching primitives
"""

from math import pi
from pathlib import Path

from pyfea import A, Hz, H, mm, ohm, nullset
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder, MagneticData
from pyfea.domain.geometry.domain import Domain, BoundaryType, CoordinateSystem
from pyfea.domain.circuits.builder import Circuit, Configuration

from pyfea.solver.solver_outputs import SolverOutputs, CircuitOptions
from pyfea.solver.femm.domains.magnetostatic.solver import FEMMMagnetostaticSolver

# FEA file output
BASE_DIR = Path(__file__).parent.parent.parent

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("pure_iron")
copper = manager.use_material("pure_copper")
stc_air = manager.use_material("stc_air")

# Builds the transformer core
iron_square = Builder.rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
iron_cutout = Builder.rectangle((15 * mm, 25 * mm), 85 * mm, 60 * mm)

core = iron_square.subtract(iron_cutout)
core = Builder.promote_to_part(core, MagneticData(1 * nullset, iron))

# Positive coil slot
phase_a = Circuit("Phase A", 1 * A, Configuration.series)
slot = MagneticData(2 * nullset, copper, phase_a, 100 * nullset, 0.1 * mm)

positive_slot = Builder.rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = Builder.promote_to_part(positive_slot, slot)

# Negative coil slot
slot = MagneticData(2 * nullset, copper, phase_a, -100 * nullset, 0.1 * mm)
negative_slot = Builder.rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = Builder.promote_to_part(negative_slot, slot)

# Defines problem domain
domain_shape = Builder.circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)

simulation_domain = Domain(
    parts               =   (positive_slot, negative_slot, core),
    boundary_type       =   BoundaryType.DIRICHLET,
    meta_data           =   MagneticData(3 * nullset, stc_air),
    coordinate_system   =   CoordinateSystem.PLANAR,
    shape               =   domain_shape
)

# Defines required outputs
outputs = SolverOutputs()
outputs.add_circuit(phase_a, CircuitOptions.resistance)
outputs.add_circuit(phase_a, CircuitOptions.flux_linkage)
outputs.add_circuit(phase_a, CircuitOptions.current)
outputs.add_circuit(phase_a, CircuitOptions.voltage)

solver = FEMMMagnetostaticSolver(BASE_DIR / "examples/u-transformer/")
solver.setup(simulation_domain, "iron-core_u_transformer", depth=20 * mm)

flux_linkage = []
current = []
voltage = []

print("========== Dynamic Response ==========")
for index in range(1, 10):
    phase_a.current = 1 / 10 * A * index
    solver.update_current(phase_a)
    results = solver.solve(outputs)
    secant_inductance = results[phase_a].flux_linkage / phase_a.current

    print(
        f"Solved model at {phase_a.current:.3f}, "
        f"secant inductance {secant_inductance:.3f}"
    )

    current.append(phase_a.current)
    flux_linkage.append(results[phase_a].flux_linkage)
    voltage.append(results[phase_a].voltage)


def gradient_via_regression(output_1: list, output_2: list):
    """ Calculates the gradient via regression """
    x = [i.value for i in output_1]
    y = [i.value for i in output_2]

    sample_space = len(x)
    sum_product = sum(a * b for a, b in zip(x, y))
    sum_squared = sum(a ** 2 for a in x)

    numerator = sample_space * (sum_product) - sum(y) * sum(x)
    denominator = sample_space * sum_squared - sum(x) ** 2

    return numerator / denominator

# Calculates inductance (df/di ~= inductance) and resistance (r = v/i)
inductance = gradient_via_regression(current, flux_linkage) * H
resistance = gradient_via_regression(current, voltage) * ohm

# Calculates impedance assumes no capacitive impedance
frequency = 50 * Hz
x_inductive = 2 * pi * inductance * frequency
impedance = (resistance ** 2 + x_inductive ** 2) ** 0.5

print("===== U-transformer Performance =====")
print(f"Resistance: {resistance:.3f}")
print(f"Inductance: {inductance:.3f}")
print(f"Impedance at {frequency:.3f} : {impedance:.3f}")
print("=====================================")
