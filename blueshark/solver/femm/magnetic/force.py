"""
File: force.py
Author: William Bowley
Version: 1.2.1
Date: 2025-12-02
Description:
    Force calculation utilities for FEMMagnaticSolver
"""

import math

from blueshark.domain.constants import PRECISION
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.conversion.manager import PhysicalQuantity
from blueshark.domain.units import NEWTON, DIMENSIONLESS


def lorentz(element_id: int) -> tuple[PhysicalQuantity, PhysicalQuantity]:
    """
    Calculates the Lorentz force magnitude and angle on a given element.

    Args:
        element_id: element identifier
    """

    fx = utils.get_block_integral(element_id, 11)
    fy = utils.get_block_integral(element_id, 12)

    # Calculates the magnitude of the force
    magnitude = math.hypot(fx, fy)
    magnitude = round(magnitude, PRECISION)
    magnitude = PhysicalQuantity(magnitude, NEWTON)

    # Calculates the angle of the force
    angle = (math.degrees(math.atan2(fy, fx)) + 360) % 360
    angle = round(angle, PRECISION)
    angle = PhysicalQuantity(angle, DIMENSIONLESS)

    return magnitude, angle


def weighted_stress_tensor(
    element_id: int
) -> tuple[PhysicalQuantity, PhysicalQuantity]:
    """
    Calculates the weighted stress tensor force magnitude
    and angle on a given element.

    Args:
        element_id: element identifier
    """

    fx = utils.get_block_integral(element_id, 18)
    fy = utils.get_block_integral(element_id, 19)

    # Calculates the magnitude of the force
    magnitude = math.hypot(fx, fy)
    magnitude = round(magnitude, PRECISION)
    magnitude = PhysicalQuantity(magnitude, NEWTON)

    # Calculates the angle of the force
    angle = (math.degrees(math.atan2(fy, fx)) + 360) % 360
    angle = round(angle, PRECISION)
    angle = PhysicalQuantity(angle, DIMENSIONLESS)

    return magnitude, angle
