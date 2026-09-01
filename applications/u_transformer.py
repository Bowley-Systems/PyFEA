"""
Filename: u_transformer.py

Description:
    Quasi-static simulation using the FEMM solver
    to calculate the secant inductance and then
    approximate impedance at 50 Hz.
"""

from pyfea import mm
from pyfea.domain.geometry.builder import Builder, MagneticData


# Builds the geometry using construct solid geometry