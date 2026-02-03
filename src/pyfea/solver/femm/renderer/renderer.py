"""
Filename: renderer.py
Description:
    Renderer adaptor for FEMM (finite element magnetic methods)
    uses shapely to translate CSG (Construct Solid Geometry) to
    FEMM native primitives (Point, Line, Arc and Block label)
"""

import femm
import logging

from enum import Enum
from pathlib import Path
from typing import Any

from pyfea.domain.units import Material, Quantity, LENGTH
from pyfea.domain.circuits.builder import Circuits

from pyfea.domain.geometry.domain import Domain
from pyfea.domain.geometry.definitions import CoordinateSystem

from pyfea.solver.renderer_interface import (
    RendererError, BaseRenderer, MagneticRenderer, 
    ElectricRenderer, HeatRenderer
)

class FEMMPhysicsTypes(Enum):
    """ Enum of Physics types within FEMM (finite element magnetic methods) """
    magnetostatic = 0
    electrostatic = 1
    heat_flow = 2
    current_flow = 3


class FEMMRenderer(BaseRenderer, MagneticRenderer, ElectricRenderer, HeatRenderer):
    """ Base Renderer for FEMM (finite element magnetic methods) """

    def __init__(self, file_path: Path, physics_type: FEMMPhysicsTypes) -> None:
        """ Initializes the renderer under the file_path and physics_type"""
        self.file_path = Path(file_path)
        self.physics_type = physics_type
        
        # Solver variables
        self.femm_unit = "meters"
        self.suite_is_active = False
        self.tolerance = 1e-008

        # Simulation variables
        self.materials: set[Material] = set()
        self.circuits: set[Circuits] = set()
        
        # NOTE: 'Any' as these primitives are not used currently
        self.boundaries: set[Any] = set()
        self.conductor: set[Any] = set()
        
    def setup(self, system: CoordinateSystem, depth: Quantity) -> None:
        """ Setup the rendering environment and simulation space """
        # Strips depth of quantity at boundary between femm
        depth: float | int = self._strip_quantity(depth, 0 * LENGTH)
        
        problem_type = None
        if system == CoordinateSystem.AXI_SYMMETRIC:
            problem_type = "axi"
            
            if depth != 0:
                logging.warning(
                    "Axial symmetric simulation cannot have depth, "
                    f"got {depth}; defaulting to depth = 0"
                )
        elif system == CoordinateSystem.PLANAR:
            problem_type = "planar"

        else:
            msg = f"{system!r} isn't supported by {self.__class__.__name__}"
            raise RendererError(msg)
        
        try:
            # Ensures the users file path exist
            self._file_path_exist()
            
            # Opens FEMM in a new window (1) and defines physics type
            femm.openfemm()
            femm.newdocument(int(self.physics_type))
            
            # Defines the problem within the FEMM suite
            if (
                self.physics_type == FEMMPhysicsTypes.magnetostatic or
                self.physics_type == FEMMPhysicsTypes.current_flow
            ):
                femm.mi_probdef(
                    0,                          # Frequency (Not Used)
                    self.femm_unit,             # Default length unit in suite
                    problem_type,               # Planar or Axial Symmetric
                    self.tolerance,             # Meshing tolerance
                    depth                       # Planar depth extrusion 
                )
            
            if (
                self.physics_type == FEMMPhysicsTypes.electrostatic or
                self.physics_type == FEMMPhysicsTypes.heat_flow
            ):
                femm.mi_probdef(
                    self.femm_unit,             # Default length unit in suite
                    problem_type,               # Planar or Axial Symmetric
                    self.tolerance,             # Meshing tolerance
                    depth                       # Planar depth extrusion 
                )
                
            self.suite_is_active = True
            self._save_changes()
                
        except Exception as err:
            msg = f"{self.__class__.__name__} failed to initialize the FEMM suite: {err}"
            raise RendererError(msg)

    def draw_domain(self, domain: Domain) -> None:
        """ Draws the simulation domain to the FEMM suite """
        self._check_active()        # Check suite state
        


    def _save_changes(self) -> None:
        """ Saves the changes to the femm file """
        self._check_active()
        femm.mi_saveas(str(self.file_path.resolve()))

    def _check_active(self) -> None:
        """ Checks if the FEMM suite is active """
        if self.suite_is_active:
            return

        try:
            femm.openfemm(int(self.physics_type))
            femm.opendocument(str(self.file_path.resolve()))
            self.suite_is_active = True

        except Exception as err:
            msg = f"{self.__class__.__name__} failed to reactivate: {err}"
            raise RendererError(msg)