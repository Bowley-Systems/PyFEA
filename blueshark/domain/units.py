"""
Filename: units.py
Author: William Bowley
Version: 0.1
Date: 2025-10-23

Description:
    This file defines enums that are used
    throughout the framework to define units.

    These are independent of specific renderer/
    solver implementations.
"""

from enum import Enum, auto
from dataclasses import dataclass


class PrefixScale(Enum):
    """ Unit Prefix Conversion Scale """
    KILO = 3
    HECTO = 2
    DEKA = 1
    BASE = 0
    DECI = -1
    CENTI = -2
    MILLI = -3


class SIBase(Enum):
    """ SI base dimensions """
    SECOND = auto()
    METER = auto()
    GRAM = auto()
    AMPERE = auto()
    KELVIN = auto()


@dataclass()
class Dimension:
    """ Defines a dimension within the framework """
    base: SIBase
    prefix: PrefixScale = PrefixScale.BASE
    exponent: int = 1


@dataclass
class Unit:
    """ Defines a unit via its dimensions """
    def __init__(
        self, *dimensions: list[Dimension] | Dimension
    ) -> None:
        self.dims = dimensions

    def __repr__(self) -> str:
        """ Formatted unit representation """
        parts = []
        for dim in self.dims:
            prefix = "" if dim.prefix is PrefixScale.BASE else dim.prefix.name
            exponent = "" if abs(dim.exponent) == 1 else f"^{dim.exponent}"
            base = dim.base.name
            parts.append(f"{prefix}{base}{exponent}")

        return " ".join(parts)


""" Defines default units for the framework / user """
# Defining Newton
NEWTON = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER),
    Dimension(SIBase.SECOND, exponent=-2)
)

# Defining Joule
JOULE = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-2)
)

# Defining watt
WATT = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-3)
)
