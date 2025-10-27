"""
File: elements.py
Author: William Bowley
Version: 1.2
Date: 2025-07-28
Description:
    Magnetic properties calculation
    utilities for FEMMagnaticSolver
"""

from blueshark.domain.constants import PRECISION
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.units import (
    Unit, Dimension, SIBase, PrefixScale, CUBIC_METER, JOULE
)


# Tesla Meter ^ 3 (kg/s²·A⁻¹·M³)
TESLA_CUBIC_METER = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.SECOND, exponent=-2),
    Dimension(SIBase.AMPERE, exponent=-1),
    Dimension(SIBase.METER, exponent=3)
)


def field_energy(element_id: int) -> tuple[float, Unit]:
    """
    Calculates the magnetic field energy of a block elements
    under the element_id

    args:
        element_id: element identifier
    """
    energy = utils.get_block_integral(element_id, 2)
    energy = round(energy, PRECISION)
    return energy, JOULE


def element_volume(element_id: int) -> tuple[float, Unit]:
    """
    Calculates the volume of the block elements
    under the element_id

    args:
        element_id: element identifier
    """
    volume = utils.get_block_integral(element_id, 10)
    volume = round(volume, PRECISION)
    return volume, CUBIC_METER


def b_field_over_block(element_id: int) -> tuple[float, float, Unit]:
    """
    Calculates the b-field over block elements under the element_id

    args:
        element_id: element identifier
    """
    bx_or_br = utils.get_block_integral(element_id, 8)
    bx_or_br = round(bx_or_br, PRECISION)

    by_or_bz = utils.get_block_integral(element_id, 9)
    by_or_bz = round(by_or_bz, PRECISION)

    return bx_or_br, by_or_bz, TESLA_CUBIC_METER
