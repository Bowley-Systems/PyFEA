"""
Filename: builder.py
Description:
    Currently this module defines the placeholder
    enum and dataclass for circuit definition within
    pyfea.
"""



from dataclasses import dataclass
from enum import Enum, auto

from pyfea.domain.units import Quantity


class Configuration(Enum):
    """ Different circuit configuration available """
    SERIES = auto()
    PARALLEL = auto()

@dataclass
class Circuit:
    name: str
    current: Quantity
    configuration: Configuration
    
    def __hash__(self):
        """ Hash based class attributes """
        return hash(
            (self.name, self.current, self.configuration)
        )