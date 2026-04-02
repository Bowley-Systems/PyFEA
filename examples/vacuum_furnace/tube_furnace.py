"""
Filename: vacuum_furnace

Description:
    Thermostatic simulation using FEMM solver to calculate
    the temperature under asymptotic diffusion conditions.
    
    This example shows how pyfea can be used to model
    thermo-electric problems without a GUI.
"""

from pathlib import Path

from pyfea import Parser
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder, ThermalData

# FEA file output
BASE_DIR = Path(__file__).parent
parameters = Parser.open(BASE_DIR / "parameters.uiv")

