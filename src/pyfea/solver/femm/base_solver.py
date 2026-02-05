"""
Filename: base_solver.py
Description:
    Base Solver adaptor interface for FEMM (finite element magnetic methods)
    
    Orchestrates the problem creation through the FEMMRenderer and than 
    solves the problem with tolerance marching
"""

import femm
import logging

from pathlib import Path
from abc import ABC, abstractmethod

from pyfea.domain.units import Quantity, LENGTH
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.solver_interface import (
    BaseSolver, BaseOutputs, BaseSolutions, SolverError
)

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
        self.folder_path = Path(folder_path)
        self.folder_path.mkdir(parents=True, exist_ok=True)

        self.max_attempts = max_attempts
        self.max_tolerance = max_tolerance
        
        # Overrides the FEMMRenderer on BaseRenderer
        self.renderer: FEMMRenderer = self._create_renderer(tolerance)

    def solve(
        self, 
        simulation_domain: Domain, 
        outputs: BaseOutputs, 
        depth: Quantity = 1 * LENGTH
    ) -> BaseSolutions:
        """ Solves the problem constructed by the FEMMRenderer """
        # Sets up the FEMM suite under the users coordinate system
        coordinate_system = simulation_domain.coordinate_system
        self.renderer.setup(coordinate_system, depth)

        # Draws the domain to the FEMM suite 
        self.renderer.draw_domain(simulation_domain)
        
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
                    raise SolverError(msg)

                # Increases the tolerance by a factor of 10
                new_tolerance = self.renderer.tolerance * 10

                # Log reentry attempt under lower tolerance 
                msg = (
                    f"Solver failed on attempt {attempt} with tolerance "
                    f"{self.renderer.tolerance}: {err}. "
                    f"Retrying with tolerance {new_tolerance}"
                )
                logging.info(msg)
                
                self._change_tolerance(new_tolerance)
           
    def _clean_up(self) -> None:
        """ Closes FEMM and removes the .ans file """
        self.renderer._clean_up()
        
        ans_path = self.renderer.file_path.with_suffix(".ans")
        if ans_path.exists():
            try:
                ans_path.unlink()
            except Exception as err:
                msg = f"{self.__class__.__name__} could not delete .ans file: {err}"
                logging.warning(msg)
                
    @abstractmethod
    def _create_renderer(self, tolerance: float) -> FEMMRenderer:
        """ Overrides the BaseSolver abstractmethod to include tolerance """
        
    @abstractmethod
    def _domain_analyse(self, outputs: BaseOutputs) -> BaseSolutions:
        """ Solves the problem defined within the FEMM suite """
        
    @abstractmethod
    def _change_tolerance(self, tolerance: float) -> None:
        """ Changes the tolerance of the FEMM suite """