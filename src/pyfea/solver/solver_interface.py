"""
Filename: solver_interface.py
Author: William Bowley

Description:
    Abstract base class which defines the interface for solvers.

    - BaseSolver: Core generic modules for all solvers
"""


from abc import ABC, abstractmethod

from typing import Any
from pathlib import Path
from enum import Enum, auto

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.geometry.definitions import CoordinateSystem

from pyfea.solver.renderer_interface import BaseRenderer

class Outputs(Enum):
    """ Temporary enum to hold known outputs to be selected """
    circuit_inductance = auto()
    circuit_resistance = auto()


class Solutions:
    """ 'ABC' Expandable mixin for outputs as enums """
    
    @property
    def _name(self):
        """ Enum output name based on its properties """
        return f"<Solutions outputs: {self.value}>"  

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name


class BaseSolver(BaseRenderer, ABC):
    """ Core interface for all solver renderers """
    @abstractmethod
    def __init__(
        self,
        folder_path: Path,
        coordinate_system: CoordinateSystem,
        simulation_domain: Domain,
        outputs: Outputs,
        elements: Quantity
    ) -> Any:
        """ Initializes the solver and renderers the geometry """

    @abstractmethod
    def solve(self) -> Solutions:
        """ Solves the problem defined by user during initialization """
    
    @abstractmethod
    def _clean_up(self) -> None:
        """ Cleans up any temporary files and closes the solver. """
    