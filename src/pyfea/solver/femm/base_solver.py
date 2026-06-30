"""
Filename: base_solver.py

Description:
    Base Solver adaptor interface for FEMM (finite element magnetic methods)
    
    Orchestrates the problem creation through the FEMMRenderer and than 
    solves the problem and extracts variables.
"""

from pathlib import Path
from typing import Any
from abc import ABC, abstractmethod

from pyfea.solver.solver_outputs import SolverOutputs, SolverSolutions
from pyfea.solver.solver_interface import BaseSolver, SolverError

from pyfea.solver.femm.base_renderer import FEMMRenderer


class FEMMSolver(BaseSolver, ABC):
    """" Base solver for FEMM (finite element magnetic methods) """ 
    def __init__(
        self,
        folder_path: Path,
        verbose: bool = True,
        tolerance: float = 1e-012,
    ) -> None:
        """ Initializes the FEMM solver and FEMM renderer """  
        self._folder_path_exist(folder_path)

        self.verbose = verbose
        self.tolerance = tolerance
        self.filename: str = None

        # Overrides the FEMMRenderer on BaseRenderer
        self.renderer = None
        self.problem_setup = False

    def solve(self, outputs: SolverOutputs):
        """ Solves the problem constructed by the FEMMRenderer """
        try:
            # Opens FEMM suite as a hidden window
            self._setup_check("solving")
            self.renderer.check_active()

            solution = self._domain_analyse(outputs)
            return solution

        except Exception as err:
            msg = f"FEMMSolver failed to solve problem due to {err}"
            raise SolverError(msg) from err

    def _setup_check(self, method: str) -> None:
        """ Checks if the problem has be setup """
        if self.problem_setup:
            return

        path = f"{self.__class__.__name__}.setup"
        msg = f"Problem has to be setup before {method}, run {path}"
        raise SolverError(msg)

    @classmethod
    def _add_result(
        cls, result: dict, name: Any, key: Any, data: Any
    ) -> dict:
        """ Adds a new result to the result dictionary """
        if name not in result:
            result[name] = {}

        result[name][key.name] = data
        return result

    @abstractmethod
    def _create_renderer(self, filename: str, tolerance: float) -> FEMMRenderer:
        """ Overrides the BaseSolver abstractmethod to include tolerance """

    @abstractmethod
    def _domain_analyse(self, outputs: SolverOutputs) -> SolverSolutions:
        """ Solves the problem defined within the FEMM suite """
