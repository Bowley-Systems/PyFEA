"""
Filename: units.py

Description:
    Defines unit notation for pyFEA 
    based on its 'SI Metric' unit frame
"""


from picounits.constants import *
from picounits.extensions.parser import Parser
from picounits.extensions.loader import DynamicLoader
from picounits import Q, Quantity, strip_quantity, check_quantity


# Reference for material manager to use without leaking picounits abstraction
MaterialParser = Parser


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


def linear_interpolate(points: Q, value: Q) -> Q:
    """ Linear interpolates a quantity list from a specific linked value """
    if value <= points[0][0]: return points[0][1]
    if value >= points[-1][0]: return points[-1][1]

    # finds specific interval
    for index in range(len(points) - 1):
        x0, x1 = points[index][0], points[index + 1][0]
        y0, y1 = points[index][1], points[index + 1][1]

        if x0 <= value <= x1:
            slope = (y1 - y0) / (x1 - x0)
            return y0 + slope * (value - x0)


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
MILLI   = _  = PrefixScale.MILLI
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
