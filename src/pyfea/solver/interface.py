"""
Filename: interface.py

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
from pyfea.domain.geometry.domain import Domain, Component as GComponent
from pyfea.domain.circuits.builder import MockCircuit

from pyfea.solver.outputs import SolverOutputs, SolverSolutions


class RendererError(Exception):
    """ Exception for renderer Error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class BaseRenderer(ABC):
    """ Core interface for all solver renderers """

    @abstractmethod
    def __init__(self, file_path: Path) -> Any:
        """ Setups the rendering environment in file_path """
        self.file_path = file_path

    @abstractmethod
    def draw_domain(self, domain: Domain) -> None:
        """ Defines the domain and than draws the elements within """

    @abstractmethod
    def move_element(self, part: GComponent, magnitude: Quantity, angles: Quantity) -> None:
        """ Moves an part within the simulation domain """

    @abstractmethod
    def rotate_element(self, part: GComponent, axis: Quantity, angles: Quantity) -> None:
        """ Rotates an part around an axis in the simulation domain """

    @abstractmethod
    def clean_up(self) -> None:
        """ Removes any temporary files and closes the renderer """

    def _file_path_exist(self) -> None:
        """ Checks to ensure the file path given by the solver exists """
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.touch(exist_ok=True)

        except Exception:
            msg = (
                f"File path given to {self.__class__.__name__} invalid or inaccessible"
            )
            raise RendererError(msg) from None

    def _strip_quantity(self, quantity: Quantity, ref: Quantity) -> Any:
        """ Strips quantity from value returns raw value """


class MagneticRenderer(BaseRenderer, ABC):
    """ Renderer interface for magnetic problems """
    @abstractmethod
    def update_current(self, circuit: MockCircuit) -> Any:
        """ Changes the current within a circuit element """

    @abstractmethod
    def update_temperature(self, part: GComponent, temperature: Quantity) -> Any:
        """ Updates the materials based on temperature """


class ThermalRenderer(BaseRenderer, ABC):
    """ Renderer interface for thermal problems """
    @abstractmethod
    def update_volumetric_heat_source(self, part: GComponent, magnitude: Quantity) -> Any:
        """ Updates a volumetric heat source within the simulation domain """

class ElectricRenderer(BaseRenderer, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc


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
        self.simulation_domain = None

    @abstractmethod
    def setup(
        self,
        simulation_domain: Domain,
        filename: str
    ) -> None:
        """ Setups the solver problem via the renderer """
        self.simulation_domain = simulation_domain
        self.renderer: BaseRenderer = self._create_renderer(filename, self.tolerance)

    @abstractmethod
    def solve(self,  outputs: SolverOutputs) -> SolverSolutions:
        """ Solves the problem defined by user during initialization """

    @abstractmethod
    def _create_renderer(self, filename: str, tolerance: float) -> BaseRenderer:
        """ Subclasses instantiate their specific renderer """

    @abstractmethod
    def clean_up(self) -> None:
        """ Cleans up any temporary files and closes the solver. """

    def move_element(
        self, part: GComponent, magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves an part within the simulation domain """
        self.renderer.move_element(GComponent, magnitude, angles)

    def move_elements(
        self, parts: tuple[GComponent], magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves a series of part within the simulation domain """
        for part in parts:
            self.move_element(part, magnitude, angles)

    def rotate_element(
        self, part: GComponent, axis: Quantity, angles: Quantity
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

    def update_current(self, circuit: MockCircuit) -> Any:
        """ Changes the current within a circuit element """
        self.renderer.update_current(circuit)

    def update_temperature(
        self, parts: list[Part] | Part, temperature: Quantity
    ) -> Any:
        """ Updates the materials based on temperature """

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

class ElectricSolver(BaseSolver, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
