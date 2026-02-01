"""
Filename: units.py
Author: William Bowley
Version: 0.2
Date: 2025-02-01

Description:
    Defines unit notation for pyFEA 
    based on its 'SI Metric' unit frame
"""

from picounits.constants import *


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