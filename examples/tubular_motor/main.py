"""
Filename: main.py
Author: William Bowley
Version: 1.3
Date: 2025-10-14

Description:
    Quasi-transient magnetic analysis for V1.0 TLSM.

    NOTE:
    - This is a prototype example it may or may not function
      correctly depending on many factors.
"""

from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver
from blueshark.models.tlsm.unpack import MotorUnpacker
from blueshark.models.tlsm.motor import TubularLinearMotor
from blueshark.models.tlsm.simulate.dynamic_analysis import run_dynamic
from blueshark.models.tlsm.simulate.static_analysis import (
    get_phase_values, get_magnet_flux
)

renderer_file = "examples/tubular_motor/configuration.yaml"

unpacker = MotorUnpacker(renderer_file)
renderer = FEMMagneticRenderer(
    f"{unpacker.folder_path}/{unpacker.file_name}.fem"
)
motor = TubularLinearMotor(renderer, unpacker)
motor.build()

# Femm cannot automatically fill domain
renderer.define_environment_region(
    motor.BOUNDARY, (100, 100), motor.boundary_material
)

resistance, inductance = get_phase_values(motor, renderer, FEMMagneticSolver)
magnet_flux = get_magnet_flux(motor, renderer, FEMMagneticSolver)
print(
    run_dynamic(
        motor, resistance, inductance, list(magnet_flux.values()), True
    )
)
