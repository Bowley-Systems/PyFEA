"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

import femm

from shapely import geometry as shapely_geometry
from shapely.geometry import Polygon as ShapelyPolygon

from pyfea.domain.units import Quantity
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.renderer_interface import MagneticRenderer, RendererError
from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.femm.base_renderer import FEMMRenderer, FEMMPhysicsTypes 


class FEMMMagnetostaticRenderer(FEMMRenderer, MagneticRenderer):
    """ Magnetostatic renderer for FEMM (finite element magnetic methods) """
    def _suite_define(
        self, problem_type: FEMMPhysicsTypes, depth: float | int
    ) -> None:
        """ Defines the suite problem as magnetostatic """
        femm.mi_probdef(
            0,                          # Frequency (Not Used)
            self.femm_unit,             # Default length unit in suite
            problem_type,               # Planar or Axial Symmetric
            self.tolerance,             # Meshing tolerance
            depth                       # Planar depth extrusion 
        )
    
    def draw_domain(self, domain: Domain):
        """ Defines the domain and than draws the elements within """
        domain_parts = domain.parts
        for i in domain_parts:
            csg = FEMMCSG.evaluate_csg_tree(i.geometry)
            print(csg)
            self._draw_shape(csg, None, None)
    
    def move_element(self, element_id, magnitude, angles):
        return super().move_element(element_id, magnitude, angles)
    
    def rotate_element(self, element_id, axis, angles):
        return super().rotate_element(element_id, axis, angles)
    
    def create_circuit(self, circuit):
        return super().create_circuit(circuit)
    
    def update_current(self, circuit, current):
        return super().update_current(circuit, current)
    
    
    def _draw_shape(
        self, shape: shapely_geometry, block_label: str, material_label: str
    ) -> None:
        """ Draws the shapely geometry to the FEMM suite """
        self.check_active()
        match shape.geom_type:
            case "Polygon":
                self._draw_polygon(shape, block_label, material_label)
            case _:
                msg = f"{shape.geom_type!r} is not supported by {self.__class__.__name__}"
                raise RendererError(msg)

    def _draw_polygon(
        self, polygon: ShapelyPolygon, block_label: str, material_label: str, background_label: str
    ) -> None:
        """ Draws a shapely polygon to the FEMM suite """
        exterior = list(polygon.exterior.coords)
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            femm.mi_drawline(x1, y1, x2, y2)

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                femm.mi_drawline(x1, y1, x2, y2)
                
            hole_poly = ShapelyPolygon(interior)
            cx, cy = FEMMCSG.get_polygon_solid_centroid(hole_poly, self.tolerance)
            femm.mi_addblocklabel(cx, cy)
        
        cx, cy = FEMMCSG.get_polygon_solid_centroid(polygon, self.tolerance)
        femm.mi_addblocklabel(cx, cy)

    
        self._save_changes()

    def _save_changes(self):
        """ Manages the changes to the femm file """
        self.check_active()
        
        resolve_path_str = str(self.file_path.resolve())
        femm.mi_saveas(resolve_path_str)