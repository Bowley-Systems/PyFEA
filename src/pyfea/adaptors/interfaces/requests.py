"""
Filename: requests.py

Description:
    Defines the outputs that can be 
    requested for adaptors.
"""

from enum import Enum, auto


class CircuitOptions(Enum):
    """ Defines the different possible circuit output variables """
    power                   = auto()
    gain                    = auto()
    phase                   = auto()
    voltage                 = auto()
    current                 = auto()
    resistance              = auto()
    flux_linkage            = auto()


class MagneticOptions(Enum):
    """ Defines the different possible magnetic output variables """
    volume                  = auto()
    cross_section           = auto()
    force_lorentz           = auto()
    torque_lorentz          = auto()
    field_energy            = auto()
    b_field                 = auto()
    force_stress_tensor     = auto()
    torque_stress_tensor    = auto()


class ThermalOptions(Enum):
    """ Defines the different possible thermal output variables """
    volume                  = auto()
    cross_section           = auto()
    average_temperature     = auto()
    flux_over_element       = auto()
