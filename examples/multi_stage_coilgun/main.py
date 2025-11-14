"""
Filename: main.py
Author: William Bowley
Version: 0.1
Date: 2025-10-19

Description:
    Quasi-transient Electro-Magneto-Mechanical analysis
    for single or multi-stage coilgun.

    Parameter file: configuration.yaml
"""

from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver

from blueshark.models.coilgun_multi_stage.main import MultiStageCoilGun
from blueshark.models.coilgun_multi_stage.unpack import CoilGunUnpacker
from blueshark.models.coilgun_multi_stage.simulate import (
    get_circuit_values, launch_dynamic
)

# Defines the unpacker & renderer dependency
parameter_file = "examples/multi_stage_coilgun/configuration.yaml"
unpacker = CoilGunUnpacker(parameter_file)

renderer_path = f"{unpacker.folder_path}/{unpacker.file_name}.fem"
renderer = FEMMagneticRenderer(renderer_path)

# Builds the coil-gun from unpacker data
coilgun = MultiStageCoilGun(renderer, unpacker)
coilgun.build()

# Femm cannot automatically fill domain
tag = (unpacker.shell_outer_radi * 1.2, 0)
material = coilgun.boundary_material
renderer.define_environment_region(coilgun.BOUNDARY, tag, material)

# Performs a series of static frames to get resistance, inductance
print("1. Beginning static characterization of the coilgun")
resistance, inductance = get_circuit_values(coilgun, FEMMagneticSolver)

# # Performs a dynamic launch of the coilgun
print("2. Beginning quasi-transient launch of the coilgun")
result = launch_dynamic(coilgun, FEMMagneticSolver, resistance, inductance)
print(f"3. Launch results: \n{result}")
