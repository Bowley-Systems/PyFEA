"""
Filename: definitions.py

Description:
    Defines the global circuit errors,
    dataclasses and enums within the 
    circuit modules.
"""

from typing import Any

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from pyfea.domain.units import Q


class NodalPrimitives(ABC):
    """ Defines the behavior of nodal primitives when displayed """
    @property
    @abstractmethod
    def name(self) -> str:
        """ Dataclass name should be based of its properties """
        return ""

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name


class Configuration(Enum):
    """ Different circuit configuration available """
    series = auto()
    parallel = auto()
    none = auto()


class ComponentTypes(Enum):
    """ Fundamental components types """
    SOURCE = auto()
    SWITCH = auto()
    RESISTOR = auto()
    INDUCTOR = auto()
    CAPACITOR = auto()

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return f"<ComponentTypes={self.name}>"

    def __str__(self) -> str:
        """ Returns the points name from ComponentTypes.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from ComponentTypes.type """
        return self._name


class Terminal:
    """ Represents a terminal (connection point)"""
    def __init__(self, name, parent: Any):
        self.name = name
        self.parent = parent

    def __repr__(self):
        return f"<Terminal {self.name}>"


@dataclass
class MockCircuit:
    """ Fully controllable circuit object. """
    current: Q
    configuration: Configuration

    def __hash__(self):
        """ Hash based class attributes """
        return hash((self.current, self.configuration))
