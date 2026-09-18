"""
Filename: picomats.py

Description:
    Defines the unit &

    Defines unit notation for pyFEA 
    based on its 'SI Metric' unit frame
"""

from picomats import Materials
from picomats import Q, Material, Parser
from picomats import UnitError, strip_quantity, check_quantity, expects

from picomats.physical.units import *
from picomats.physical.constants import *

# References different primitives
_, _ = Q, UnitError
_, _, _ = strip_quantity, check_quantity, expects


# Reference the parser & dynamic loader
_, _ = Parser, Material

# References the material Library
_ = Materials