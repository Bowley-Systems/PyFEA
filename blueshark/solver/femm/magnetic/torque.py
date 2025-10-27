"""
File: torque.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14
Description:
    Torque calculation utilities for
    FEMMagneticSolver

"""

from blueshark.domain.constants import PRECISION
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.units import Unit, NEWTON_METER


def lorentz(element_id: int) -> tuple[float, Unit]:
    """
    Calculates the Lorentz torque on a given element.

    Args:
        element_id: element identifier
    """
    torque = utils.get_block_integral(element_id, 15)
    torque = round(torque, PRECISION)

    return torque, NEWTON_METER


def weighted_stress_tensor(element_id: int) -> tuple[float, Unit]:
    """
    Calculates the weighted stress tensor torque on a given element.

    Args:
        element_id: element identifier
    """

    torque = utils.get_block_integral(element_id, 22)
    torque = round(torque, PRECISION)

    return torque, NEWTON_METER
