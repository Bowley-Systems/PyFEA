"""
Filename: u_inductor.py

Description:
    Quasi-static simulation using the FEMM solver
    to calculate the secant inductance and then
    approximate impedance at 50 Hz.
"""

from pyfea import mm, ampere, kelvin
from pyfea.domain import GBuilder, Cbuilder, Configuration
from pyfea.domain import Materials, MagneticData

from pyfea.domain import Domain, BoundaryType, CoordinateSystem
from pyfea.solver import SolverRequests, CircuitOptions


# Builds the core geometry using construct solid geometry (CSG)
core_bulk = GBuilder.rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
core_window = GBuilder.rectangle((15 * mm, 25 * mm), 85 * mm, 60 * mm)

finalized_core = core_bulk.subtract(core_window)
core = GBuilder.promote_to_component(finalized_core, MagneticData(Materials.iron))

# Builds the phase circuit & then slot geometry using CSG
phase = Cbuilder.feed_circuit(1 * ampere, Configuration.series)

# Constructs the positive slot
slot = MagneticData(Materials.copper, phase, 100, 0.1 * mm)
positive_slot = GBuilder.rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = GBuilder.promote_to_part(positive_slot, slot)

# Constructs the negative slot
slot = MagneticData(Materials.copper, phase, -100, 0.1 * mm)
negative_slot = GBuilder.rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = GBuilder.promote_to_part(negative_slot, slot)

slots = GBuilder.promote_to_component((negative_slot, positive_slot))

# Builds the domain shape and defines the solution domain
finalized_domain = GBuilder.circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)

domain = Domain(
    (core, slots),
    BoundaryType.DIRICHLET,
    Materials.air,
    CoordinateSystem.PLANAR,
    finalized_domain,
    297.15 * kelvin
)

# Defines the required outputs for the simulation
request = SolverRequests()
request.circuit(phase, CircuitOptions.resistance)
request.circuit(phase, CircuitOptions.flux_linkage)
request.circuit(phase, CircuitOptions.current)
request.circuit(phase, CircuitOptions.voltage)
