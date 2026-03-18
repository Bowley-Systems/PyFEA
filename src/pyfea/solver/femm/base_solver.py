"""
Filename: base_solver.py

Description:
    Base Solver adaptor interface for FEMM (finite element magnetic methods)
    
    Orchestrates the problem creation through the FEMMRenderer and than 
    solves the problem with tolerance marching
"""

import logging

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
        tolerance: float = 1e-012,
        max_tolerance: float = 1e-04,
        max_attempts: int = 8
    ) -> None:
        """ Initializes the FEMM solver and FEMM renderer """  
        self._folder_path_exist(folder_path)

        self.filename = ""
        self.tolerance = tolerance
        self.max_attempts = max_attempts
        self.max_tolerance = max_tolerance

        # Overrides the FEMMRenderer on BaseRenderer
        self.renderer: FEMMRenderer = None
        self.problem_setup = False

    def solve(self, outputs: SolverOutputs):
        """ Solves the problem constructed by the FEMMRenderer """
        self._setup_check("solving")
        for attempt in range(0, self.max_attempts):
            try:
                # Opens FEMM suite as a hidden window
                self.renderer.check_active()

                solution = self._domain_analyse(outputs)
                msg = (
                    f"Solved problem with tolerance {self.renderer.tolerance} "
                    f"on attempt {attempt}"
                )
                logging.info(msg)

                self._clean_up()
                return solution

            except Exception as err:
                if (
                    self.renderer.tolerance > self.max_tolerance or 
                    attempt == self.max_attempts
                ):
                    msg = (
                        f"Solver failed after {attempt} attempts with tolerance "
                        f"{self.renderer.tolerance}: {err}"
                    )
                    raise SolverError(msg) from None

                # reentry with lower tolerance; Increases the tolerance by a factor of 10
                new_tolerance = self.renderer.tolerance * 10
                self._change_tolerance(new_tolerance)

    def _setup_check(self, method: str) -> None:
        """ Checks if the problem has be setup """
        if self.problem_setup:
            return

        path = f"{self.__class__.__name__}.setup"
        msg = f"Problem has to be setup before {method}, run {path}"
        raise SolverError(msg)

    def _change_tolerance(self, tolerance: float) -> None:
        """ Changes the required tolerance within FEMM problem """
        self.renderer.check_active()

        try:
            self.renderer.tolerance_march(tolerance)
        except Exception as err:
            msg = f"Failed change the tolerance of the FEMM problem due to {err}"
            raise SolverError(msg) from None

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
