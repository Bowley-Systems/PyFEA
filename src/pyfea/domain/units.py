"""
Filename: units.py
Description:
    Defines unit notation for pyFEA 
    based on its 'SI Metric' unit frame
"""

from typing import Any

from picounits.constants import *
from picounits.core import Quantity
from picounits.extensions.parser import Parser
from picounits.extensions.loader import DynamicLoader


class Material(DynamicLoader):
    """ Class for materials using the dynamic loader from picounits """
    @property
    def _name(self) -> str:
        """ Returns the material direct members """
        items = ', '.join(self.keys())
        return f'Material({items})'

    def __repr__(self):
        """ Returns the material name """
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
        msg = f"{quantity!r} is not a physical quantity"
        raise UnitError(msg)
    
    if quantity.unit != ref.unit:
        msg = f"Expected {ref.unit!r}, got {quantity.unit!r}"
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