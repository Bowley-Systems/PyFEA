"""
Filename: u_transformer.py

Description:
    Quasi-static simulation using the FEMM solver
    to calculate the secant inductance and then
    approximate impedance at 50 Hz.
"""

from pyfea.domain.materials.manager import MaterialManager


manager = MaterialManager()
manager.display_materials()