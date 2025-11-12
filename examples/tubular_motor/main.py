"""
Filename: main.py
Author: William Bowley
Version: 0.3
Date: 2025-10-19

Description:
    Closed-loop quasi-transient magnetic analysis for V1.0 TLSM.
    Reference: configuration.yaml

    NOTE:
    - This is a prototype example it will not function correctly.
      It is not finished.
"""

from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver

from blueshark.models.tubular_linear_motor.unpack import MotorUnpacker
from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.models.tubular_linear_motor.simulate import (
    get_magnet_flux, get_phase_values, find_optimal_phase_shift
)

# Defines the unpacker & renderer dependency
parameter_file = "examples/tubular_motor/configuration.yaml"
unpacker = MotorUnpacker(parameter_file)

renderer_file = f"{unpacker.folder_path}/{unpacker.file_name}.fem"
renderer = FEMMagneticRenderer(renderer_file)

# Creates the motor instant, builds motor and defines domain
motor = TubularLinearMotor(renderer, unpacker)
motor.build()

# Note: Femm cannot automatically fill domain; hence user has too.
tag = (unpacker.slot_outer_radius * 1.2, 0)
material = motor.boundary_material
renderer.define_environment_region(motor.BOUNDARY, tag, material)

# Performs a series of static frames to get key parameters
print("1. Beginning static characterization of the motor...")
magnet_flux = get_magnet_flux(motor, renderer, FEMMagneticSolver)
resistance, inductance = get_phase_values(motor, renderer, FEMMagneticSolver)
phase_shift = find_optimal_phase_shift(motor, renderer, FEMMagneticSolver)

# print(magnet_flux, resistance, inductance, phase_shift)

# Performs a close loop quasi transient analysis of the between two points
print("2. Beginning point to point launch of the motor...")
