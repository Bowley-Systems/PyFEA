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

from picounits.blueprints.boundary_class import ValidBoundary

# Reference for material manager to use without leaking picounits abstraction
MaterialParser = Parser
SystemBoundary = ValidBoundary

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


def check_quantity(quantity: Quantity, ref: Quantity) -> None:
    """ Checks if the quantity has the correct reference unit """
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


def strip_quantity(quantity: Quantity, reference: Quantity) -> Any:
    """ Strips quantity from value returns raw value """
    check_quantity(quantity, reference)

    return quantity.value


""" =============== Base units (SI names) =============== """
second          = s         = TIME
meter           = m         = LENGTH
kilogram        = kg        = MASS
ampere          = A         = CURRENT
kelvin          = K         = TEMPERATURE
mole            = mol       = AMOUNT
candela         = cd        = LUMINOSITY
dimensionless   = nullset   = DIMENSIONLESS


""" =============== Predefined scales for quantities =============== """
GIGA    = G  = PrefixScale.GIGA
MEGA    = M  = PrefixScale.MEGA
KILO    = k  = PrefixScale.KILO
CENTI   = c  = PrefixScale.CENTI
MILLI   = m  = PrefixScale.MILLI
MICRO   = u  = PrefixScale.MICRO
NANO    = n  = PrefixScale.NANO
PICO    = p  = PrefixScale.PICO


""" =============== Scaled length units =============== """
kilometer   = km = 1 * KILO  * meter
centimeter  = cm = 1 * CENTI * meter
millimeter  = mm = 1 * MILLI * meter
micrometer  = um = 1 * MICRO * meter
nanometer   = nm = 1 * NANO  * meter
picometer   = pm = 1 * PICO  * meter


""" =============== Scaled time units =============== """
millisecond = ms = 1 * MILLI * second
microsecond = us = 1 * MICRO * second
nanosecond  = ns = 1 * NANO  * second


""" =============== Mass units =============== """
gram        = g  = 1 * MILLI * kilogram
milligram   = mg = 1 * MICRO * kilogram


""" =============== Derived named units =============== """
newton          = N     = FORCE
joule           = J     = ENERGY
watt            = W     = POWER
pascal          = Pa    = PRESSURE
hertz           = Hz    = FREQUENCY
coulomb         = C     = CHARGE
volt            = V     = VOLTAGE
ohm             = Ω     = RESISTANCE
farad           = F     = CAPACITANCE
henry           = H     = INDUCTANCE
tesla           = T     = MAGNETIC_FIELD
weber           = Wb    = MAGNETIC_FLUX
siemens         = S     = CONDUCTANCE

""" =============== Heat transfer units =============== """
volumetric_capacity     = VOLUMETRIC_HEAT_CAPACITY
volumetric_heating      = VOLUMETRIC_HEATING
convection_coefficient  = h = watt/(meter ** 2 * kelvin)
