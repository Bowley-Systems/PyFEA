"""
Filename: solver.py
Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

import femm

from typing import Any

from pyfea.domain.units import Quantity, ampere, volt, weber
from pyfea.solver.solver_interface import MagneticSolver
from pyfea.solver.solver_outputs import (
    SolverOutputs, CircuitOptions, MagneticOptions, SolverSolutions
)

from pyfea.solver.femm.base_solver import FEMMSolver, SolverError
from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.magnetostatic.renderer import FEMMMagnetostaticRenderer
from pyfea.domain.circuits.builder import Circuit


class FEMMMagnetostaticSolver(FEMMSolver, MagneticSolver):
    """ Magnetostatic Solver for FEMM (finite element magnetic methods) """
    def _create_renderer(self, tolerance: float) -> FEMMMagnetostaticRenderer:
        femm_file = self.folder_path / "magnetostatic.fem"
        
        return FEMMMagnetostaticRenderer(
            femm_file, FEMMPhysicsTypes.magnetostatic, tolerance
        )
    
    @classmethod
    def _add_result(
        cls, result: dict, name: Any, key: Any, data: Any
    ) -> dict:
        """ Adds a new result to the result dictionary """
        if name not in result:
            result[name] = {}

        result[name][key.name] = data 
        return result
    
    def _domain_analyse(self, outputs: SolverOutputs):
        """ Solves the problem defined within the FEMM suite """
        femm.mi_analyse(1)   # Hidden FEMM window
        femm.mi_loadsolution()

        results = {}
        for (target, option), _ in outputs.registry.items():

            if isinstance(option, CircuitOptions):
                data = self._circuit_outputs(option, target)
                results = self._add_result(results, target.name, option, data)

            elif isinstance(option, MagneticOptions):
                pass
                
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
    
    def update_current(self, circuit: Circuit) -> None:
        """ Updates the the current in a specific circuit """
        self._setup_check("updating currents")
        self.renderer.update_current(circuit)
    
    def _circuit_outputs(
        self, option: CircuitOptions, circuit: Circuit
    ) -> Quantity:
        """ Gets the requested circuit output from the FEMM suite """
        circuit_properties = self._get_circuit_properties(circuit)

        match option:
            case CircuitOptions.CURRENT: return circuit_properties[0]
            case CircuitOptions.VOLTAGE: return circuit_properties[1]
            case CircuitOptions.FLUX_LINKAGE: return circuit_properties[2]
            case CircuitOptions.POWER: return circuit_properties[0] * circuit_properties[1]
            case CircuitOptions.RESISTANCE:
                current = circuit_properties[0]
                tolerance = self.renderer.tolerance

                if abs(current) > tolerance * ampere: 
                    return circuit_properties[1] / current

                msg  = f"Failed to calculate resistance, {current} < {tolerance}"
                raise SolverError(msg)

            case _:
                name = name = self.__class__.__name__
                msg = f"{option!r} is an unknown or unsupported output for {name}"
                print(msg)
                raise SolverError(msg)

    def _get_circuit_properties(self, circuit: Circuit) -> tuple[Quantity]:
        """ Safely retrieves the properties of a specified circuit from FEMM suite """
        try:
            circuit_name = str(circuit.name)
            properties = femm.mo_getcircuitproperties(circuit_name)
            return (
                properties[0] * ampere, 
                properties[1] * volt,
                properties[2] * weber
            )
        except Exception as err:
            msg = f"Failed to get properties from circuit {circuit.name!r}: {err}"
            raise SolverError(msg)
