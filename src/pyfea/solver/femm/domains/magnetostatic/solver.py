"""
Filename: solver.py
Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

from pathlib import Path

from pyfea.solver.solver_interface import BaseOutputs

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.circuits.builder import Circuits

from pyfea.solver.femm.base_solver import FEMMSolver
from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.magnetostatic.renderer import FEMMMagnetostaticRenderer


class FEMMMagnetostaticSolver(FEMMSolver):
    """ Magnetostatic Solver for FEMM (finite element magnetic methods) """
    def _create_renderer(self, tolerance: float) -> FEMMMagnetostaticRenderer:
        femm_file = self.folder_path / "magnetostatic.fem"
        
        return FEMMMagnetostaticRenderer(
            femm_file, FEMMPhysicsTypes.magnetostatic, tolerance
        )
    
    def _domain_analyse(self, outputs):
        return super()._domain_analyse(outputs)
    
    def _change_tolerance(self, tolerance):
        return super()._change_tolerance(tolerance)
    
    def move_element(self, element_id, magnitude, angles):
        return super().move_element(element_id, magnitude, angles)
    
    def move_elements(self, element_ids, magnitude, angles):
        return super().move_elements(element_ids, magnitude, angles)
    
    def rotate_element(self, element_id, axis, angles):
        return super().rotate_element(element_id, axis, angles)
    
    def rotate_elements(self, element_ids, axis, angles):
        return super().rotate_elements(element_ids, axis, angles)
    