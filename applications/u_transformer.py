"""
Filename: u_transformer.py

Description:
    Quasi-static simulation using the FEMM solver
    to calculate the secant inductance and then
    approximate impedance at 50 Hz.
"""

from pyfea.domain.materials.manager import Materials

# Pulls model materials
copper = Materials.copper
iron = Materials.iron
Materials.display_materials()