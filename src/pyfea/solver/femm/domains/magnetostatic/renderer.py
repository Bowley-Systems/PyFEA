"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

import femm

from shapely.geometry import (
    Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon
)
from pyfea.domain.units import (
    LENGTH, PERMEABILITY, COERCIVITY, CONDUCTIVITY, DIMENSIONLESS
)

from pyfea.domain.geometry.domain import Domain
from pyfea.domain.geometry.elements.metadata import MagneticData

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
        # Builds the environmental magnetic metadata
        self.environmental_data = MagneticData(domain.group, domain.material)
        
        # Draws part boundaries and labels solids for all parts
        domain_parts = domain.parts
        parts_geometries = []
        for part in domain_parts:
            # Constructs shapely geometry via csg tree evaluation
            CSG_polygon = FEMMCSG.evaluate_csg_tree(part.geometry)
            parts_geometries.append(CSG_polygon)
            
            # Draws outer and inter boundary to FEMM
            self._draw_polygon_boundaries(CSG_polygon)
            element_coord = FEMMCSG.polygon_solid_centroid(CSG_polygon, self.tolerance)
            self._add_properties(element_coord, part.metadata)
        
        # Draws the domain boundary
        CSG_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon_boundaries(CSG_domain)
        
        # Computes part region complement
        parts_complement = FEMMCSG.part_complement(parts_geometries, CSG_domain)
        
        if parts_complement.is_empty:
            RendererError("Environmental regions are empty; Check geometry overlaps")
        
        if isinstance(parts_complement, ShapelyPolygon):
            self._label_environmental_region(parts_complement)
        elif isinstance(parts_complement, ShapelyMultiPolygon):
            for polygon in parts_complement.geoms:
                self._label_environmental_region(polygon)
        
        else:
            msg = f"Unexpected environmental geometry type: {type(parts_complement)}"
            raise RendererError(msg)
        
        self._save_changes()
    
    def move_element(self, element_id, magnitude, angles):
        return super().move_element(element_id, magnitude, angles)
    
    def rotate_element(self, element_id, axis, angles):
        return super().rotate_element(element_id, axis, angles)
    
    def create_circuit(self, circuit):
        return super().create_circuit(circuit)
    
    def update_current(self, circuit, current):
        return super().update_current(circuit, current)

    def _add_material(self, metadata: MagneticData) -> None:
        """ Adds a material to the FEMM suite using .UIV material """
        if not isinstance(metadata, MagneticData):
            name = self.__class__.__name__
            msg = f"{name} can only load MagneticData, not {metadata}"
            raise RendererError(msg)
        
        # Extracts the material data and name
        material = metadata.material
        material_name = material.keys()[0]
        material_qualities = material.values()[0]
        
        # Variables for lamination properties within FEMM Suite
        wire_diameter = 0 * LENGTH                  # 0 = Non-stranded material
        material_lamination = 0                     # 0 = Solid material
        number_of_strands = 0                       # 0 = Solid material
        lamination_thickness = 0 * LENGTH           # 0 = Solid lamination

        if metadata.diameter is not None:
            material_lamination = 3     # FEMM: 3 = Magnet Wire
            number_of_strands = 1

            material_name = f"{material_name}_{metadata.diameter.value}"

        # Bypasses already loaded materials from being reloaded
        for loaded_material in self.materials:
            if loaded_material == material_name:
                return loaded_material

        try:
            # Takes values from material loader
            relative_permeability = material_qualities.magnetic.relative_permeability
            coercivity = material_qualities.magnetic.coercivity
            conductivity = material_qualities.electrical.conductivity
            
            # Checks unit and removes quantity
            relative_perm = self._strip_quantity(relative_permeability, PERMEABILITY)
            
            coercivity = self._strip_quantity(coercivity, COERCIVITY)
            conductivity = self._strip_quantity(conductivity, CONDUCTIVITY)
            wire_diameter = self._strip_quantity(wire_diameter, LENGTH)
            lamination_thickness = self._strip_quantity(lamination_thickness, LENGTH)
            
            femm.mi_addmaterial(
                material_name,
                float(relative_perm[0]),
                float(relative_perm[1]),
                float(coercivity),
                0,                                      # current density (not supported yet)
                float(conductivity) / 1e6,              # FEMM requires MS/m not S/m
                float(lamination_thickness),
                0.0,                                    # Phi_h_max (not supported yet)
                1.0,                                    # Lamination fill (not supported yet)
                int(material_lamination),
                0,                                      # Phi_hx (not supported yet)
                0,                                      # Phi_hy (not supported yet)
                int(number_of_strands),
                float(wire_diameter)
            )

            self.materials.append(material_name)
            return material_name
            
        except Exception as err:
            msg = f"Failed to add {material_name!r} as a material within femm: {err}"
            raise RendererError(msg)
        
    def _draw_polygon_boundaries(self, polygon: ShapelyPolygon) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)
        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            femm.mi_drawline(x1, y1, x2, y2)

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                femm.mi_drawline(x1, y1, x2, y2)
    
    def _label_environmental_region(self, poly: ShapelyPolygon) -> None:
        """ Adds environmental label to a single polygon region """
        coordinates = FEMMCSG.polygon_solid_centroid(poly, self.tolerance)
        self._add_properties(coordinates, self.environmental_data)

    def _add_properties(
        self,
        coordinates: tuple[float, float],
        metadata: MagneticData
    ) -> None:
        """ Sets element properties via adding a block-label """
        try:
            femm.mi_addblocklabel(float(coordinates[0]), float(coordinates[1]))
            femm.mi_selectlabel(float(coordinates[0]), float(coordinates[1]))
            
            # Adds material & circuit
            material_name = self._add_material(metadata)
            circuit = None      # Placeholder for now
            
            # Converts from quantities to raw
            element_id = self._strip_quantity(metadata.group, DIMENSIONLESS)
            
            # Converts from quantity to raw if not none
            turns = 1
            if metadata.turns: 
                turns = self._strip_quantity(metadata.turns, DIMENSIONLESS)

            magnetization = 0.0
            if metadata.magnetization: 
                magnetization = self._strip_quantity(metadata.magnetization, DIMENSIONLESS)

            femm.mi_setblockprop(
                material_name,
                1,                  # Mesher automatically chooses mesh density
                0,                  # Size constraint for mesh in block
                circuit,
                magnetization,
                element_id,
                turns
            )

            femm.mi_clearselected()
        
        except Exception as err:
            name = self.__class__.__name__
            msg = f"Failed to set properties for {element_id!r} in {name}: {err}"
            raise RendererError(msg)
    
    def _save_changes(self):
        """ Manages the changes to the femm file """
        self.check_active()
        
        resolve_path_str = str(self.file_path.resolve())
        femm.mi_saveas(resolve_path_str)