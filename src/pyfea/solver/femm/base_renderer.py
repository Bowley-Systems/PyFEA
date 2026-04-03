"""
Filename: base_renderer.py

Description:
    Renderer adaptor for FEMM (finite element magnetic methods)
    uses shapely to translate CSG (Construct Solid Geometry) to
    FEMM native primitives (Point, Line, Arc and Block label)
"""

import logging

from typing import Any
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
from shapely import Point, Polygon

import femm

from pyfea.domain.units import Q, meter, second
from pyfea.domain.geometry.definitions import CoordinateSystem
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.renderer_interface import RendererError, BaseRenderer


class FEMMPhysicsTypes(Enum):
    """ Enum of Physics types within FEMM (finite element magnetic methods) """
    magnetostatic = 0
    electrostatic = 1
    thermostatic = 2
    current_flow = 3


class FEMMRenderer(BaseRenderer, ABC):
    """ Base Renderer for FEMM (finite element magnetic methods) """

    def __init__(
        self, file_path: Path, physics_type: FEMMPhysicsTypes, tolerance: float
    ) -> None:
        """ Initializes the renderer under the file_path and physics_type"""
        self.file_path = Path(file_path)
        self.physics_type = physics_type
        self.problem_type = None

        # Solver variables
        self.coordinate_system = None
        self.femm_unit = "meters"
        self.suite_is_active = False
        self.tolerance = tolerance
        self.junk_scale = 1e-16

        # Renderer variables
        self.depth = 1 * meter
        self.verbose: list[str] = []

        # Simulation variables
        self.defined_area: list[Point] = []
        self.boundary: str = ""
        self.environmental_data: Domain = ""
        self.materials: list[str] = []
        self.circuits: list[str] = []
        self.boundaries: list[str] = {}
        self.conductor: list[str]= {}

    def setup(
        self, system: CoordinateSystem, depth: Q, time_step: Q = 0 * second
    ) -> None:
        """ Setup the rendering environment and simulation space """
        # Strips depth of quantity at boundary between femm
        depth: float | int = self._strip_quantity(depth, meter)

        if system == CoordinateSystem.AXI_SYMMETRIC:
            problem_type = "axi"
            if depth != 0:
                msg = f"Axial symmetric cannot have depth, got {depth}"
                raise RendererError(msg)
        elif system == CoordinateSystem.PLANAR:
            problem_type = "planar"
            if depth <= 0:
                msg = f"Planar cannot have negative or zero depth, got {depth}"
                raise RendererError(msg)

        else:
            msg = f"{system!r} isn't supported by {self.__class__.__name__}"
            raise RendererError(msg)

        # Saves coordinate system for later (rotations and motions)
        self.coordinate_system = system
        try:
            # Ensures the users file path exist
            self._file_path_exist()

            # Opens FEMM in a hidden window (1) and defines physics type
            femm.openfemm(1)
            femm.newdocument(int(self.physics_type.value))

            # Defines the problem within the FEMM suite
            self.suite_define(problem_type, depth, time_step)

            # Change the activation state and save changes
            self.suite_is_active = True
            self._save_changes()

        except Exception as err:
            msg = f"{self.__class__.__name__} failed to initialize the FEMM suite: {err}"
            raise RendererError(msg) from err

    @abstractmethod
    def suite_define(
        self, problem_type: str, depth: float | int, time_step: float = None
    ) -> None:
        """ Defines the suite problem definition """

    def check_active(self) -> None:
        """ Checks if the FEMM suite is active """
        if self.suite_is_active: return

        try:
            # Opens FEMM in a hidden window (1) & resolve/open file
            femm.openfemm(1)
            femm.opendocument(str(self.file_path.resolve()))
            self.suite_is_active = True

        except Exception as err:
            msg = f"{self.__class__.__name__} failed to reactivate: {err}"
            raise RendererError(msg) from err

    def clean_up(self) -> None:
        """ Manages the FEMM suite environment cleanup """
        try:
            if self.suite_is_active:
                femm.closefemm()
                self.suite_is_active = False

        except Exception as err:
            msg = f'{self.__class__.__name__} failed to perform cleanup due to {err}'
            logging.warning(msg)

    def _is_already_defined(self, pt: Point) -> bool:
        """Check if this point is close enough to any previously placed label"""
        px, py = pt.x, pt.y

        for existing in self.defined_area:
            ex, ey = existing.x, existing.y
            # rounded coordinate equality than checks (primary check)
            if (round(px, 7) == round(ex, 7) and
                round(py, 7) == round(ey, 7)):
                return True

            # Distance-based check (secondary check)
            if ((px - ex)**2 + (py - ey)**2) < self.tolerance**2:
                return True

        return False

    def _label_environmental_region(self, polygon: Polygon) -> None:
        """ Adds environmental label to a single polygon region """
        if polygon.is_empty or polygon.area < self.junk_scale:
            return

        # Early exit if we already have a label very close by (Assumes defined)
        coordinates = FEMMCSG.polygon_solid_centroid(polygon, self.tolerance)
        if self._is_already_defined(coordinates):
            return

        # If coordinate not known, we add properties and accept it as defined.
        self.defined_area.append(coordinates)
        self._add_properties(coordinates, self.environmental_data.meta_data)

    def is_on_axis(self, x1: float, x2: float) -> bool:
        """ Helper function to check if a segment lies on the axis of symmetry """
        return (
            abs(x1) < 1e-7 and
            abs(x2) < 1e-7 and
            self.problem_type == "axi"
        )

    @classmethod
    def _pre_defined(cls, name: str, loaded: list[str]) -> str:
        """ Checks to see if a material has already been loaded """
        for loaded_material in loaded:
            if loaded_material == name:
                return loaded_material

        msg = f"{name!r} is an uninitialized material, cannot edit"
        raise RendererError(msg)

    @abstractmethod
    def _save_changes(self) -> None:
        """ Saves changes to the femm suite to file """

    @abstractmethod
    def _add_material(self, metadata) -> None:
        """ Adds a material to the FEMM suite using .UIV material """

    @abstractmethod
    def _add_properties(self, coordinates: Polygon, meta: Any) -> None:
        """ Sets element properties via adding a block-label """
