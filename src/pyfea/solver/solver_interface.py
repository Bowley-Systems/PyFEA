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

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain, Part
from pyfea.domain.circuits.builder import StaticCircuit

from pyfea.solver.solver_outputs import SolverOutputs, SolverSolutions
from pyfea.solver.renderer_interface import BaseRenderer, MagneticRenderer, ThermalRenderer


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
        self, part: Part, magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves an part within the simulation domain """
        self.renderer.move_element(part, magnitude, angles)

    def move_elements(
        self, parts: tuple[Part], magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves a series of part within the simulation domain """
        for part in parts:
            self.move_element(part, magnitude, angles)

    def rotate_element(
        self, part: Part, axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates a part around an axis in the simulation domain """
        self.renderer.rotate_element(part, axis, angles)

    def rotate_elements(
        self, parts: tuple[Part], axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates a series of part around an axis in the simulation domain """
        for part in parts:
            self.rotate_element(part, axis, angles)

    def _folder_path_exist(self, path: Path) -> None:
        """ Check if the folder path exist if not creates the path """
        self.folder_path = Path(path)
        self.folder_path.mkdir(parents=True, exist_ok=True)


class MagneticSolver(BaseSolver, ABC):
    """ Solver interface for magnetic problems """
    @abstractmethod
    def __init__(
        self, folder_path: Path, verbose: bool = True, tolerance: float = 1e-012
    ) -> Any:
        """ Initializes the solver and renderers the geometry """
        # Renderer & folder path
        self._folder_path_exist(folder_path)
        self.verbose = verbose

        self.tolerance = 1e-10
        self.renderer: MagneticRenderer = None

    def update_current(self, circuit: StaticCircuit) -> Any:
        """ Changes the current within a circuit element """
        self.renderer.update_current(circuit)

    def update_temperature(
        self, parts: list[Part] | Part, temperature: Quantity
    ) -> Any:
        """ Updates the materials based on temperature """
        if not isinstance(parts, (list, tuple)):
            self.renderer.update_temperature(parts, temperature)

        for part in parts:
            self.renderer.update_temperature(part, temperature)

class ThermalSolver(BaseSolver, ABC):
    """ Solver interface for thermal problems """
    @abstractmethod
    def __init__(
        self, folder_path: Path, verbose: bool = True, tolerance: float = 1e-012
    ) -> Any:
        """ Initializes the solver and renderers the geometry """
        # Renderer & folder path
        self._folder_path_exist(folder_path)
        self.verbose = verbose

        self.tolerance = 1e-10
        self.renderer: ThermalRenderer = None

    def update_heat_source(self, part: Part, magnitude: Quantity) -> None:
        """ Updates a volumetric heat source within the femm suite """
        self.renderer.update_volumetric_heat_source(part, magnitude)

class ElectricSolver(BaseSolver, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
