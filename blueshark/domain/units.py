"""
Filename: units.py
Author: William Bowley
Version: 0.2
Date: 2025-10-24

Description:
    This file defines enums that are used
    throughout the framework to define units.

    These are independent of specific renderer/
    solver implementations.
"""

from typing import Union
from enum import Enum, auto
from dataclasses import dataclass


class PrefixScale(Enum):
    """ Unit Prefix Conversion Scale """
    MEGA = 6
    KILO = 3
    HECTO = 2
    DEKA = 1
    BASE = 0
    DECI = -1
    CENTI = -2
    MILLI = -3
    MICRO = -6
    NANO = -9


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

    def with_prefix(self, new_prefix: PrefixScale) -> "Dimension":
        """ Return a new Dimension with a different prefix. """
        return Dimension(self.base, new_prefix, self.exponent)


class Unit:
    """ Defines a unit composed of multiple dimensions. """

    def __init__(self, *dimensions: Union[Dimension, list[Dimension]]) -> None:
        dims = []
        for d in dimensions:
            if isinstance(d, list):
                dims.extend(d)
            else:
                dims.append(d)
        self.dims: list[Dimension] = dims

    def __repr__(self) -> str:
        """ Formatted unit representation. """
        parts = []
        for dim in self.dims:
            prefix = "" if dim.prefix is PrefixScale.BASE else dim.prefix.name
            exponent = "" if dim.exponent == 1 else f"^{dim.exponent}"
            base = dim.base.name
            parts.append(f"{prefix}{base}{exponent}")
        return " ".join(parts)

    def with_prefix(self, base: SIBase, new_prefix: PrefixScale) -> "Unit":
        """ Return a new Unit with one dimensions prefix changed. """
        new_dims = [
            dim.with_prefix(new_prefix) if dim.base == base else dim
            for dim in self.dims
        ]
        return Unit(*new_dims)

    def get_dimension(self, base: SIBase) -> Dimension:
        """ Return the dimension corresponding to a base unit. """
        for dim in self.dims:
            if dim.base == base:
                return dim
        raise KeyError(f"Base {base.name} not found in this Unit.")


""" Defines default units for the framework / user """

# Time: Second (s)
SECOND = Unit(Dimension(SIBase.SECOND))

# Velocity (ms⁻¹):
METER_SECOND = Unit(
    Dimension(SIBase.METER),
    Dimension(SIBase.SECOND, exponent=2)
)

# Volume: cubic-meter (m³)
CUBIC_METER = Unit(Dimension(SIBase.METER, exponent=3))

# Area: square-meter (m²)
SQUARE_METER = Unit(Dimension(SIBase.METER, exponent=2))

# Length: meter (m)
METER = Unit(Dimension(SIBase.METER))

# Length: millimeter (mm)
MILLIMETER = METER.with_prefix(SIBase.METER, PrefixScale.MILLI)

# Length: centimeter (cm)
CENTIMETER = METER.with_prefix(SIBase.METER, PrefixScale.CENTI)

# Length: micrometer (µm)
MICROMETER = METER.with_prefix(SIBase.METER, PrefixScale.MICRO)

# Mass: (kg)
KILOGRAM = Unit(Dimension(SIBase.GRAM, PrefixScale.KILO))

# Force: Newton (kg·m/s²)
NEWTON = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER),
    Dimension(SIBase.SECOND, exponent=-2)
)

# Energy: Joule (kg·m²/s²)
JOULE = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-2)
)

# Power: Watt (kg·m²/s³)
WATT = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-3)
)

# Torque: Newton-meter (kg·m²/s²)
NEWTON_METER = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-2)
)

# Electric potential: Volt (kg·m²/s³·A⁻¹)
VOLT = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-3),
    Dimension(SIBase.AMPERE, exponent=-1)
)

# Electrical current: Ampere (A)
AMPERE = Unit(Dimension(SIBase.AMPERE))

# Electrical resistance: Ohm (kg·m²/s³·A⁻²)
OHM = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-3),
    Dimension(SIBase.AMPERE, exponent=-2)
)

# Magnetic flux: Weber (kg·m²/s²·A⁻¹)
WEBER = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-2),
    Dimension(SIBase.AMPERE, exponent=-1)
)

# Magnetic flux density: Tesla (kg/s²·A⁻¹)
TESLA = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.SECOND, exponent=-2),
    Dimension(SIBase.AMPERE, exponent=-1)
)

# Inductance: Henry (kg·m²/s²·A⁻²)
HENRY = Unit(
    Dimension(SIBase.GRAM, PrefixScale.KILO),
    Dimension(SIBase.METER, exponent=2),
    Dimension(SIBase.SECOND, exponent=-2),
    Dimension(SIBase.AMPERE, exponent=-2)
)

