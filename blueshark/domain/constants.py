"""
Filename: constants.py
Author: William Bowley
Version: 1.4
Date: 2025-09-13

Description:
    This file contains fixed values and
    general constants within the simulator.

    These are independent of specific renderer/
    solver implementations.
"""

from math import pi

PRECISION: int = 12
# Number of decimal places for rounding or formatting output.

EPSILON: float = 1e-10
# Minimum threshold to treat floating-point values as effectively zero.
# Prevents division-by-zero errors or instability due to numerical noise.

MAXIMUM_FAILS: int = 5
# Maximum allowed consecutive simulation failures (e.g., solver not converging)
# before aborting a run or skipping a parameter set.

DEFAULT_TOLERANCE: float = 1e-8
# Default tolerance for the solver to meet

MAXIMUM_TOLERANCE: float = 1e-2
# Maximum allowed tolerance for retries. Aborts solving the problem

SETUP_CURRENT = 0  # Amps

ROOM_TEMPERATURE = 293  # Kelvin
ROOM_CONVECTION = 10    # W/(m^2 * K)
# Defines room temperature & convection on Earth.

PI = pi
TWO_PI = 2 * pi
# Precompute π and 2π to avoid repeated calculations.
