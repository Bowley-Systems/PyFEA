"""
Filename: units.py
Description:
    Defines unit notation for pyFEA 
    based on its 'SI Metric' unit frame
"""

from typing import Any
from importlib import resources

from picounits.constants import *
from picounits.core import Quantity
from picounits.extensions.parser import Parser
from picounits.extensions.loader import DynamicLoader

# Reference for material manager to use without leaking picounits abstraction
MaterialParser = Parser

class Material(DynamicLoader):
    """ Class for materials using the dynamic loader from picounits """
    @property
    def _name(self) -> str:
        """ Returns the material direct members """
        keys = self.keys()
        items = ', '.join(keys) if isinstance(keys, list) else keys
        return f'Material({items})'

    def __repr__(self):
        """ Returns the material name """
        return self._name


class Configuration(DynamicLoader):
    """ Class for configuration files using the dynamic loader from picounits """
    @property
    def _name(self) -> str:
        """ Returns the configuration direct members """
        keys = self.keys()
        items = ', '.join(keys) if isinstance(keys, list) else keys
        return f'Configuration({items})'

    def __repr__(self):
        """ Returns the configuration name """
        return self._name


class UnitError(TypeError):
    """ Exception for Unit Error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


def strip_quantity(quantity: Quantity, ref: Quantity) -> Any:
    """ Strips quantity from value returns raw value """
    if not isinstance(quantity, Quantity):
        msg = f"{type(quantity)!r} is not a physical quantity object"
        raise UnitError(msg)

    if not isinstance(ref, (Unit, Quantity)):
        msg = f"Reference unit must be either a quantity or unit, not {type(ref)}"
        raise UnitError(msg)

    if isinstance(ref, Quantity):
        if quantity.unit != ref.unit:
            msg = f"Expected {ref.unit!r}, got {quantity.unit!r}"
            raise UnitError(msg)

    if isinstance(ref, Unit):
        if quantity.unit != ref:
            msg = f"Expected {ref!r}, got {quantity.unit!r}"
            raise UnitError(msg)

    return quantity.value


""" =============== Base units (SI names) =============== """

second          =   TIME
meter           =   LENGTH
kilogram        =   MASS
ampere          =   CURRENT
kelvin          =   TEMPERATURE
mole            =   AMOUNT
candela         =   LUMINOSITY
dimensionless   =   DIMENSIONLESS


""" =============== Predefined scales for quantities =============== """

GIGA                    = PrefixScale.GIGA
MEGA                    = PrefixScale.MEGA
KILO                    = PrefixScale.KILO
CENTI                   = PrefixScale.CENTI
MILLI                   = PrefixScale.MILLI
MICRO                   = PrefixScale.MICRO
NANO                    = PrefixScale.NANO
PICO                    = PrefixScale.PICO


""" =============== Scaled length units =============== """

kilometer   = 1 * KILO  * meter
centimeter  = 1 * CENTI * meter
millimeter  = 1 * MILLI * meter
micrometer  = 1 * MICRO * meter
nanometer   = 1 * NANO  * meter
picometer   = 1 * PICO  * meter


""" =============== Scaled time units =============== """

millisecond = 1 * MILLI * second
microsecond = 1 * MICRO * second
nanosecond  = 1 * NANO  * second


""" =============== Mass units =============== """

gram       = 1 * MILLI * kilogram
milligram  = 1 * MICRO * kilogram


""" =============== Derived named units =============== """

newton      = FORCE
joule       = ENERGY
watt        = POWER
pascal      = PRESSURE
hertz       = FREQUENCY
coulomb     = CHARGE
volt        = VOLTAGE
ohm         = RESISTANCE
farad       = CAPACITANCE
henry       = INDUCTANCE
tesla       = MAGNETIC_FIELD
weber       = MAGNETIC_FLUX
