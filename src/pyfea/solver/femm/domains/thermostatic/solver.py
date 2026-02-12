"""
Filename: solver.py
Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    thermostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

import femm
import logging

from pathlib import Path
from typing import Any
from pyfea.solver.solver_interface import ThermalSolver
from pyfea.solver.femm.base_solver import FEMMSolver, SolverError
from pyfea.solver.solver_outputs import (
    SolverOutputs, ThermalOptions, SolverSolutions
)

from pyfea.domain.units import Quantity, LENGTH, TIME
from pyfea.domain.geometry.domain import Domain

from pyfea.domain.units import Quantity, Material, meter, kelvin, watt
from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.thermostatic.renderer import FEMMThermostaticRenderer

class FEMMThermostaticSolver(FEMMSolver, ThermalSolver):
    """ Thermostatic Solver for FEMM (finite element magnetic methods) """
    def _create_renderer(self, tolerance: float) -> FEMMThermostaticRenderer:
        femm_file = self.folder_path / "Thermostatic.feh"
        
        return FEMMThermostaticRenderer(
            femm_file, FEMMPhysicsTypes.thermostatic, tolerance
        )

    def solve(self, outputs: SolverOutputs, time_step: Quantity = 0 * TIME):
        """ Solves the problem constructed by the FEMMRenderer """
        self._setup_check("solving")
        if time_step:
            ans_path = Path("Thermostatic.anh")
            self.renderer._suite_define(
                self.renderer.problem_type,
                self.renderer.depth,
                time_step,
                ans_path
            )
        
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

                self._change_tolerance(new_tolerance, time_step)

    def _change_tolerance(self, tolerance: float, time_step: Quantity) -> None:
        """ Changes the required tolerance within FEMM problem """
        self.renderer.check_active()
        
        try:
            if time_step:
                ans_path = Path("Thermostatic.anh")
                self.renderer.tolerance_march(tolerance, time_step, ans_path)

        except Exception as err:
            msg = f"Failed change the tolerance of the FEMM problem due to {err}"
            raise SolverError(msg)   
    
    def _domain_analyse(self, outputs: SolverOutputs):
        """ Solves the problem defined within the FEMM suite """
        femm.hi_analyse(1)   # Hidden FEMM window
        femm.hi_loadsolution()

        results = {}
        for (target, option), _ in outputs.registry.items():

            if isinstance(option, ThermalOptions):
                data = self._operations(option, target)
                results = self._add_result(
                    results, f"element_{target.value}", option, data
                )

            else:
                name = self.__class__.__name__
                msg = f"{type(option)!r} category is not supported by {name}"
                raise SolverError(msg)

        return SolverSolutions(results)
    
    def move_element(self, element_id, magnitude, angles):
        self._setup_check("moving an element")
        self.renderer.move_element(element_id, magnitude, angles)

    def rotate_element(self, element_id, axis, angles):
        self._setup_check("rotating an element")
        self.renderer.rotate_element(element_id, axis, angles)
    
    def update_heat_source(self, id: Quantity | Material, magnitude):
        """ Updates a heat source within the femm suite """
        self._setup_check("updating a heat source")
 
        if isinstance(id, Quantity):
            self.renderer.update_conductor_heat_source(id, magnitude)
        elif isinstance(id, Material):
            self.renderer.update_volumetric_heat_source(id, magnitude)

    def _operations(
        self, option: ThermalOptions, element: ThermalOptions
    ) -> Quantity:
        """ Gets the requested thermal output from the FEMM suite """
        match option:
            case ThermalOptions.AVERAGE_TEMPERATURE:
                return self._get_block_integral(element, 0)[0] * kelvin
            case ThermalOptions.CROSS_SECTION: 
                return self._get_block_integral(element, 1)[0] * meter ** 2
            case ThermalOptions.VOLUME: 
                return self._get_block_integral(element, 2)[0] * meter ** 3
            case ThermalOptions.GRADIENT_OVER_ELEMENT:
                return self._get_block_integral(element, 3) * (kelvin / meter)
            case ThermalOptions.FLUX_OVER_ELEMENT:
                return self._get_block_integral(element, 4) * (watt / meter ** 2)
 
            case _:
                name = name = self.__class__.__name__
                msg = f"{option!r} is an unknown or unsupported output for {name}"
                print(msg)
                raise SolverError(msg)
    
    
    def _get_block_integral(self, group: Quantity, integral_type: int) -> Any:
        """ Safely calculates a block integral on a specific group """
        try:
            femm.ho_groupselectblock(group.value)
            result = femm.ho_blockintegral(integral_type)
            femm.ho_clearblock()
            return result

        except Exception as e:
            msg = (
                f"Failed to calculate block integral of type {integral_type} "
                f"for element {group}: {e}"
            )
            raise SolverError(msg)
        
    def _clean_up(self) -> None:
        """ Closes FEMM and removes the .ans file """
        self.renderer._clean_up()
        
        # ans_path = self.renderer.file_path.with_suffix(".anh")
        # if ans_path.exists():
        #     try:
        #         ans_path.unlink()
        #     except Exception as err:
        #         msg = f"{self.__class__.__name__} could not delete .anh file: {err}"
        #         logging.warning(msg)