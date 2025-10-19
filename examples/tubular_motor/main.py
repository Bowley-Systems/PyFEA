"""
Filename: main.py
Author: William Bowley
Version: 0.3
Date: 2025-10-19

Description:
    Quasi-transient magnetic analysis for V1.0 TLSM.

    NOTE:
    - This is a prototype example it may or may not function
      correctly depending on many factors.
"""

from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver

from blueshark.models.tubular_linear_motor.unpack import MotorUnpacker
from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.models.tubular_linear_motor.simulate import (
    run_dynamic, get_magnet_flux, get_phase_values
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
resistance, inductance = get_phase_values(motor, renderer, FEMMagneticSolver)
magnet_flux = get_magnet_flux(motor, renderer, FEMMagneticSolver)

# Performs a quasi transient simulation of the motor
results = run_dynamic(motor, resistance, inductance, magnet_flux, True)

# Return results to the user via console
simulation_results = {
    "phase_resistance": resistance,
    "phase_inductance": inductance,
    "magnet_flux": magnet_flux,
    "dynamic_results": results
}
print(f"\n{simulation_results}")
