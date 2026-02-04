"""
Filename: solver.py
Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

from pathlib import Path

from pyfea.solver.solver_interface import BaseSolver, BaseOutputs

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.circuits.builder import Circuits

from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.magnetostatic.renderer import FEMMMagnetostaticRenderer


class FEMMMagnetostaticSolver(BaseSolver):
    """ Magnetostatic Solver for FEMM (finite element magnetic methods) """