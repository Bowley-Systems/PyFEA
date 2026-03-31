"""
Filename: solver_interface.py

Description:
    Abstract base class which defines the interface for solvers.
    
    - BaseSolver: Core generic methods for all solvers
    - MagneticSolver: Magnetic-specific extensions
    - ThermalSolver: Thermal-specific extensions
"""

from abc import ABC, abstractmethod

from typing import Any
from pathlib import Path

from pyfea.domain.units import Quantity, Material
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.circuits.builder import StaticCircuit

from pyfea.solver.solver_outputs import SolverOutputs, SolverSolutions
from pyfea.solver.renderer_interface import BaseRenderer


class SolverError(Exception):
    """ Exception for solver error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class BaseSolver(ABC):
    """ Core interface for all solver renderers """
    @abstractmethod
    def __init__(
        self, folder_path: Path, verbose: bool = True, tolerance: float = 1e-012
    ) -> Any:
        """ Initializes the solver and renderers the geometry """
        # Renderer & folder path
        self._folder_path_exist(folder_path)
        self.verbose = verbose

        self.tolerance = 1e-10
        self.renderer = None

    @abstractmethod
    def setup(
        self,
        simulation_domain: Domain,
        filename: str
    ) -> None:
        """ Setups the solver problem via the renderer """
        self.renderer: BaseRenderer = self._create_renderer(filename, self.tolerance)

    @abstractmethod
    def solve(self,  outputs: SolverOutputs) -> SolverSolutions:
        """ Solves the problem defined by user during initialization """

    @abstractmethod
    def _create_renderer(self, filename: str, tolerance: float) -> BaseRenderer:
        """ Subclasses instantiate their specific renderer """

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

    def _folder_path_exist(self, path: Path) -> None:
        """ Check if the folder path exist if not creates the path """
        self.folder_path = Path(path)
        self.folder_path.mkdir(parents=True, exist_ok=True)


class MagneticSolver(BaseSolver, ABC):
    """ Solver interface for magnetic problems """
    @abstractmethod
    def update_current(self, circuit: StaticCircuit, current: Quantity) -> Any:
        """ Changes the current within a circuit element """

    @abstractmethod
    def update_temperature(
        self, material: Material | list[Material], temperature: Quantity
    ) -> Any:
        """ Updates the materials based on temperature """


class ThermalSolver(BaseSolver, ABC):
    """ Solver interface for thermal problems """
    @abstractmethod
    def update_heat_source(self, element: Quantity, magnitude: Quantity) -> Any:
        """ Updates a volumetric heat source within the simulation domain """


class ElectricSolver(BaseSolver, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
