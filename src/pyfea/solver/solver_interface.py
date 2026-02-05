"""
Filename: solver_interface.py
Description:
    Abstract base class which defines the interface for solvers.

    - BaseSolver: Core generic modules for all solvers
"""


from abc import ABC, ABCMeta, abstractmethod

from typing import Any
from pathlib import Path
from enum import Enum, EnumMeta
from dataclasses import dataclass

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.renderer_interface import BaseRenderer


class SolverError(Exception):
    """ Exception for solver error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class ABCEnumMeta(ABCMeta, EnumMeta):
    """ Abstract Enum Class"""
    pass


class BaseOutputs(Enum, metaclass=ABCEnumMeta):
    """ Abstract output class for solver implementation """
    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
    
    def __repr__(self) -> str:
        return str(self)


@dataclass(slots=True)
class BaseSolutions(ABC):
    """ Expandable for outputs as enums """
    
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


class BaseSolver(ABC):
    """ Core interface for all solver renderers """
    @abstractmethod
    def __init__(self, folder_path: Path) -> Any:
        """ Initializes the solver and renderers the geometry """
        # Renderer 
        self.renderer: BaseRenderer = self._create_renderer()

    @abstractmethod
    def solve(
        self, 
        simulation_domain: Domain, 
        outputs: BaseOutputs,
    ) -> BaseSolutions:
        """ Solves the problem defined by user during initialization """
    
    @abstractmethod
    def _create_renderer(self) -> BaseRenderer:
        """ Subclasses instantiate their specific renderer """
        pass
    
    @abstractmethod
    def _clean_up(self) -> None:
        """ Cleans up any temporary files and closes the solver. """
    
    def move_element(
        self, element_id: Quantity, magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves an element within the simulation domain """
        self.renderer.move_element(element_id, magnitude, angles)
    
    def move_elements(
        self, element_ids: tuple[Quantity], magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves a series of element within the simulation domain """
        for element in element_ids:
            self.move_element(element, magnitude, angles)
    
    def rotate_element(
        self, element_id: Quantity, axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates a element around an axis in the simulation domain """
        self.renderer.rotate_element(element_id, axis, angles)
    
    def rotate_elements(
        self, element_ids: tuple[Quantity], axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates a series of element around an axis in the simulation domain """
        for element in element_ids:
            self.rotate_element(element, axis, angles)
