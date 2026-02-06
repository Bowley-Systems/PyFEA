"""
Filename: base_renderer.py
Description:
    Renderer adaptor for FEMM (finite element magnetic methods)
    uses shapely to translate CSG (Construct Solid Geometry) to
    FEMM native primitives (Point, Line, Arc and Block label)
"""

import femm
import logging

from typing import Any
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path

from pyfea.domain.units import Quantity, LENGTH
from pyfea.domain.geometry.definitions import CoordinateSystem

from pyfea.solver.renderer_interface import RendererError, BaseRenderer


class FEMMPhysicsTypes(Enum):
    """ Enum of Physics types within FEMM (finite element magnetic methods) """
    magnetostatic = 0
    electrostatic = 1
    heat_flow = 2
    current_flow = 3


class FEMMRenderer(BaseRenderer, ABC):
    """ Base Renderer for FEMM (finite element magnetic methods) """

    def __init__(
        self, file_path: Path, physics_type: FEMMPhysicsTypes, tolerance: float
    ) -> None:
        """ Initializes the renderer under the file_path and physics_type"""
        self.file_path = Path(file_path)
        self.physics_type = physics_type
        
        # Solver variables
        self.femm_unit = "meters"
        self.suite_is_active = False
        self.tolerance = tolerance
        
        # Simulation variables
        self.environmental_data: Any = ""
        self.materials: list[str] = []
        self.circuits: list[str] = []
        
        # NOTE: 'Any' as these primitives are not used currently
        self.boundaries: dict[str, Any] = {}
        self.conductor: dict[str, Any] = {}
        

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
                depth = 0
                
        elif system == CoordinateSystem.PLANAR:
            problem_type = "planar"
            
            if depth <= 0:
                logging.warning(
                    "Planar simulation cannot have negative or zero depth, "
                    f"got {depth}; defaulting to depth = 1"
                )
                depth = 1
        else:
            msg = f"{system!r} isn't supported by {self.__class__.__name__}"
            raise RendererError(msg)
        
        try:
            # Ensures the users file path exist
            self._file_path_exist()
            
            # Opens FEMM in a hidden window (1) and defines physics type
            femm.openfemm(1)
            femm.newdocument(int(self.physics_type.value))
            
            # Defines the problem within the FEMM suite
            self._suite_define(problem_type, depth)
            
            # Change the activation state and save changes
            self.suite_is_active = True
            self._save_changes()
                
        except Exception as err:
            msg = f"{self.__class__.__name__} failed to initialize the FEMM suite: {err}"
            raise RendererError(msg)

    @abstractmethod
    def _suite_define(problem_type: str, depth: float | int) -> None:
        """ Defines the suite problem definition """
    
    @abstractmethod
    def _save_changes() -> None:
        """ Saves changes to the femm suite to file """

    @abstractmethod
    def _add_material(metadata) -> None:
        """ Adds a material to the FEMM suite using .UIV material """
    
    def check_active(self) -> None:
        """ Checks if the FEMM suite is active """
        if self.suite_is_active:
            return

        try:
            femm.openfemm(1)       # Opens FEMM in a hidden window (1)
            femm.opendocument(str(self.file_path.resolve()))
            self.suite_is_active = True

        except Exception as err:
            msg = f"{self.__class__.__name__} failed to reactivate: {err}"
            raise RendererError(msg)
    
    def _clean_up(self) -> None:
        """ Manages the FEMM suite environment cleanup """
        try:
            if self.suite_is_active:
                femm.closefemm()
                self.suite_is_active == False

        except Exception as err:
            msg = f'{self.__class__.__name__} failed to perform cleanup due to {err}'
            logging.warning(msg)
            