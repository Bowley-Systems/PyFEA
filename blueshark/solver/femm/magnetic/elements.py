"""
File: elements.py
Author: William Bowley
Version: 1.2.1
Date: 2025-12-02
Description:
    Magnetic properties calculation utilities for FEMMagnaticSolver
"""

from blueshark.domain.constants import PRECISION
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.conversion.manager import PhysicalQuantity
from blueshark.domain.units import (
    Unit, Dimension, SIBase, PrefixScale, CUBIC_METER, JOULE
)


# CUSTOM UNIT: Tesla Meter ^ 3 (kg/s²·A⁻¹·M³)
TESLA_CUBIC_METER = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.SECOND, exponent=-2),
    Dimension(SIBase.AMPERE, exponent=-1),
    Dimension(SIBase.METER, exponent=3)
)


def field_energy(element_id: int) -> PhysicalQuantity:
    """
    Calculates the magnetic field energy of a block elements
    under the element_id

    args:
        element_id: element identifier
    """
    energy = utils.get_block_integral(element_id, 2)
    energy = round(energy, PRECISION)

    return PhysicalQuantity(energy, JOULE)


def element_volume(element_id: int) -> tuple[float, Unit]:
    """
    Calculates the volume of the block elements
    under the element_id

    args:
        element_id: element identifier
    """
    volume = utils.get_block_integral(element_id, 10)
    volume = round(volume, PRECISION)

    return PhysicalQuantity(volume, CUBIC_METER)


def b_field_over_block(
    element_id: int
) -> dict[str, PhysicalQuantity]:
    """
    Calculates the b-field over block elements under the element_id

    args:
        element_id: element identifier
    """
    bx_or_br = round(utils.get_block_integral(element_id, 8), PRECISION)
    bx_or_br = PhysicalQuantity(bx_or_br, TESLA_CUBIC_METER)

    by_or_bz = round(utils.get_block_integral(element_id, 9), PRECISION)
    by_or_bz = PhysicalQuantity(by_or_bz, TESLA_CUBIC_METER)

    return {'xr': bx_or_br, 'yz': by_or_bz}
