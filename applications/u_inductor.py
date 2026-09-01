"""
Filename: u_inductor.py

Description:
    Quasi-static simulation using the FEMM solver
    to calculate the secant inductance and then
    approximate impedance at 50 Hz.
"""

from pyfea import mm
from pyfea.domain import GBuilder

# Builds the core geometry using construct solid geometry (CSG)
core_bulk = GBuilder.rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
core_window = GBuilder.rectangle((15 * mm, 25 * mm), 85 * mm, 60 * mm)

finalized_core = core_bulk.subtract(core_window)

# Builds the slots & domain geometry using CSG
positive_slot = GBuilder.rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = GBuilder.rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)

domain = GBuilder.circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)
