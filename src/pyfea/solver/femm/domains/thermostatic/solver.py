"""
Filename: solver.py
Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    thermostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

import femm

from typing import Any
from pyfea.solver.solver_interface import ThermalSolver
from pyfea.solver.femm.base_solver import FEMMSolver, SolverError
from pyfea.solver.solver_outputs import (
    SolverOutputs, ThermalOptions, SolverSolutions
)

from pyfea.domain.units import Quantity, meter, kelvin, watt
from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.thermostatic.renderer import FEMMThermostaticRenderer

class FEMMThermostaticSolver(FEMMSolver, ThermalSolver):
    """ Thermostatic Solver for FEMM (finite element magnetic methods) """
    def _create_renderer(self, tolerance: float) -> FEMMThermostaticRenderer:
        femm_file = self.folder_path / "Thermostatic.feh"
        
        return FEMMThermostaticRenderer(
            femm_file, FEMMPhysicsTypes.thermostatic, tolerance
        )
    
    def _domain_analyse(self, outputs: SolverOutputs):
        """ Solves the problem defined within the FEMM suite """
        femm.hi_analyse(1)   # Hidden FEMM window
        femm.hi_loadsolution()

        results = {}
        for (target, option), _ in outputs.registry.items():

            if isinstance(option, ThermalOptions):
                data = self._operations(option, target)
                results = self._add_result(
                    results, f"element{target.value}", option, data
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
    
    def update_heat_source(self, id, magnitude):
        return super().update_heat_source(id, magnitude)
    
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
    
    
    def _get_block_integral(self, group: int, integral_type: int) -> Any:
        """ Safely calculates a block integral on a specific group """
        if not isinstance(group.value, int) or group.value <= 0:
            msg = f"Group must be a positive integer, got {group}."
            raise SolverError(msg)
        
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