"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    thermostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the thermostatic
    problem within the FEMM suite. 
"""

import femm
from shapely.geometry import (
    Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon
)
from math import cos, sin, radians
from pyfea.domain.units import (
    Material, Quantity, kelvin, dimensionless, THERMAL_CONDUCTIVITY,
    VOLUMETRIC_HEAT_CAPACITY, VOLUMETRIC_HEATING, watt, meter, TIME
)

from pyfea.domain.geometry.domain import Domain, BoundaryType, CoordinateSystem
from pyfea.domain.geometry.elements.metadata import ThermalData

from pyfea.solver.renderer_interface import ThermalRenderer, RendererError
from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.femm.base_renderer import FEMMRenderer, FEMMPhysicsTypes 

class FEMMThermostaticRenderer(FEMMRenderer, ThermalRenderer):
    """ Thermostatic renderer for FEMM (finite element magnetic methods) """

    def _suite_define(
        self, problem_type: FEMMPhysicsTypes, depth: float | int, 
        time_step: Quantity = None, solution_file: str = None
    ) -> None:
        """ Defines the suite problem as magnetostatic """
        if time_step:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                problem_type,               # Planar or Axial Symmetric
                self.tolerance,             # Meshing tolerance
                depth,                      # Planar depth extrusion
                30,
                str(solution_file),
                float(self._strip_quantity(time_step, TIME))
            )
        else:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                problem_type,               # Planar or Axial Symmetric
                self.tolerance,             # Meshing tolerance
                depth,                      # Planar depth extrusion
            )
        
        # Saves problem definitions for marching
        self.problem_type = problem_type
        self.depth = depth
    
    def tolerance_march(
        self, new_tolerance: float, 
        time_step: Quantity = None, solution_file: str = None
    ) -> None:
        """ Defines the suite problem with new tolerance """
        if time_step:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                self.problem_type,          # Problem type defined during setup
                float(new_tolerance),       # New meshing tolerance
                self.depth,                 # Depth of problem defined during setup
                30,
                str(solution_file),
                float(self._strip_quantity(time_step, TIME))
            )
        else:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                self.problem_type,          # Planar or Axial Symmetric
                float(new_tolerance),       # Meshing tolerance
                self.depth,                 # Planar depth extrusion
            )

        self.tolerance = new_tolerance
    
    def draw_domain(self, domain: Domain):
        """ Defines the domain and than draws the elements within """
        self.environmental_data = domain.meta_data
        environmental_boundary_name = (
            self._create_environmental_boundary_property(domain.boundary_type)
        )

        # Draws the domain boundary and add boundary condition
        CSG_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon_boundaries(CSG_domain, self.environmental_data, environmental_boundary_name)
        
        # Draws part boundaries and labels solids for all parts
        domain_parts = domain.parts
        parts_geometries = []

        if not isinstance(domain_parts, (list, tuple)):
            domain_parts = [domain_parts]

        for part in domain_parts:
            # Constructs shapely geometry via csg tree evaluation
            CSG_polygon = FEMMCSG.evaluate_csg_tree(part.geometry)
            parts_geometries.append(CSG_polygon)
            
            # Draws outer and inter boundary to FEMM
            self._draw_polygon_boundaries(CSG_polygon)
            element_coord = FEMMCSG.polygon_solid_centroid(CSG_polygon, self.tolerance)
            self._add_properties(element_coord, part.metadata)

        # Computes part region complement
        parts_complement = FEMMCSG.part_complement(parts_geometries, CSG_domain, self.tolerance)
        
        if parts_complement.is_empty:
            RendererError("Environmental regions are empty; Check geometry overlaps")
        
        if isinstance(parts_complement, ShapelyPolygon):
            self._draw_polygon_boundaries(
                parts_complement, self.environmental_data, environmental_boundary_name, False
            )
            self._label_environmental_region(parts_complement)

        elif isinstance(parts_complement, ShapelyMultiPolygon):
            for polygon in parts_complement.geoms:
                self._draw_polygon_boundaries(
                    polygon, self.environmental_data, environmental_boundary_name, False
                )
                self._label_environmental_region(polygon)
        
        else:
            msg = f"Unexpected environmental geometry type: {type(parts_complement)}"
            raise RendererError(msg)
        
        self._save_changes()
    
    def move_element(
        self, element_id: Quantity, magnitude: Quantity, angle: Quantity
    ) -> None:
        """ Moves a element by a vector; expects degrees """
        raise RendererError(f"move element not implemented for {self.__class__.__name__}")

    def rotate_element(
        self, element_id: Quantity, axis: Quantity, angle: Quantity
    ) -> None:
        """ Rotates a element by angle around a center axis; expects degrees"""
        raise RendererError(f"move rotate not implemented for {self.__class__.__name__}")
    
    @classmethod
    def pre_defined(cls, name: str, loaded: list[str]) -> str:
        """ Checks to see if a material has already been loaded """
        for loaded_material in loaded:
            if loaded_material == name:
                return loaded_material
            
        msg = f"{name!r} is an uninitialized material, cannot edit"
        raise RendererError(msg)
    
    def update_conductor_heat_source(self, element, magnitude):
        return super().update_conductor_heat_source(element, magnitude)

    def update_volumetric_heat_source(
        self, material: Material, magnitude: Quantity
    ) -> None:
        """ Updates a material volumetric heat """
        self.check_active()
        
        # Extracts the material data and name
        material_name = material.keys()
        block_name = self.pre_defined(material_name, self.materials)
        
        try:
            volumetric_heating = self._strip_quantity(magnitude, VOLUMETRIC_HEATING)
            femm.hi_modifymaterial(block_name, 3, float(volumetric_heating))
            self._save_changes()

        except Exception as err:
            msg = f"Failed to update {material_name!r} within femm: {err}"
            raise RendererError(msg)
    
    def _draw_polygon_boundaries(
        self, polygon: ShapelyPolygon,
        meta_data: ThermalData = None, 
        boundary_name: str = None, 
        draw: bool = True
    ) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)

        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            if draw:
                femm.hi_drawline(x1, y1, x2, y2)

            if boundary_name and meta_data:
                femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.hi_setsegmentprop(boundary_name, 0, 0, 0, meta_data.group.value, "")
                femm.hi_clearselected()
                
            if meta_data and not boundary_name:
                femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.hi_setsegmentprop(
                    "", 0, 0, 0, meta_data.heating_index.value, meta_data.group.value
                )
                femm.hi_clearselected()
                  
        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                if draw:
                    femm.hi_drawline(x1, y1, x2, y2)

                if boundary_name and meta_data:
                    femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.hi_setsegmentprop(boundary_name, 0, 0, 0, meta_data.group.value, "")
                    femm.hi_clearselected()
                
                if meta_data and not boundary_name:
                    femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.hi_setsegmentprop(
                        "", 0, 0, 0, meta_data.heating_index.value, meta_data.group.value
                    )
                    femm.hi_clearselected()
                    
    
    def _label_environmental_region(self, polygon: ShapelyPolygon) -> None:
        """ Adds environmental label to a single polygon region """
        coordinates = FEMMCSG.polygon_solid_centroid(polygon, self.tolerance)
        self._add_properties(coordinates, self.environmental_data)
    
    def _add_properties(
        self, coordinates: tuple[float, float], metadata: ThermalData
    ) -> None:
        """ Sets element properties via adding a block-label """
        try:
            femm.hi_addblocklabel(float(coordinates[0]), float(coordinates[1]))
            femm.hi_selectlabel(float(coordinates[0]), float(coordinates[1]))
            
            # Adds or retrieve the material name and converts element id
            material_name = self._add_material(metadata)
            element_id = self._strip_quantity(metadata.group, dimensionless)
            
            femm.hi_setblockprop(
                material_name,
                1,                  # Mesher automatically chooses the mesh density
                0,                  # Size constraint on the mesh in the block
                element_id          # Member of group 'number group'
            )

            femm.hi_clearselected()
        
        except Exception as err:
            name = self.__class__.__name__
            msg = f"Failed to set properties for {element_id!r} in {name}: {err}"
            raise RendererError(msg)

    def _create_environmental_boundary_property(self, property: BoundaryType) -> str:
        """ Adds boundary property to the outer domain boundary """
        self.check_active()
        meta_data: ThermalData = self.environmental_data
        
        match property:
            case BoundaryType.DIRICHLET:
                try:
                    temperature = self._strip_quantity(meta_data.temperature, kelvin)
                    boundary_name = str(temperature)
                    femm.hi_addboundprop("Fixed Temperature", 0, temperature, 0, 0, 0, 0)
                    return boundary_name

                except Exception as err:
                    msg = f"Failed to create dirichlet boundary condition: {err}"
                    raise RendererError(msg)

            case BoundaryType.CONVECTION:
                try:
                    temperature = self._strip_quantity(meta_data.temperature, kelvin)
                    heat_transfer = self._strip_quantity(
                        meta_data.convection_coefficient, watt / (meter **2 * kelvin)
                    )
                    
                    boundary_name = str(f"{heat_transfer}_{temperature}")
                    femm.hi_addboundprop(
                        boundary_name, 2, 0, 0, temperature, heat_transfer, 0
                    )
                    return boundary_name
    
                except Exception as err:
                    msg = f"Failed to create convection boundary condition: {err}"
                    raise RendererError(msg)    
            case _:
                msg = f"{property!r} not supported by {self.__class__.__name__}"
                raise RendererError(msg)

    def _add_material(self, metadata: ThermalData) -> str:
        """ Adds a material to the FEMM suite using .UIV material"""
        if not isinstance(metadata, ThermalData):
            name = self.__class__.__name__
            msg = f"{name} can only load ThermalData, not {metadata}"
            raise RendererError(msg)
    
        # Extracts the material data and name
        material = metadata.material
        material_name = material.keys()
        material_qualities = material.values()
        
        # Bypasses already loaded materials from being reloaded
        for loaded_material in self.materials:
            if loaded_material == material_name:
                return loaded_material
            
        try:
            volumetric_heat_capacity = material_qualities.thermal.volumetric_heat_capacity
            thermal_conductivity = material_qualities.thermal.conductivity     
            volumetric_heating = metadata.volumetric_heating

            # Checks unit and removes quantity
            volumetric_heat_capacity = self._strip_quantity(
                volumetric_heat_capacity, VOLUMETRIC_HEAT_CAPACITY
            )

            thermal_conductivity = self._strip_quantity(
                thermal_conductivity, THERMAL_CONDUCTIVITY
            )
            
            if volumetric_heating:
                volumetric_heating = self._strip_quantity(
                    volumetric_heating, VOLUMETRIC_HEATING
                )
            else:
                volumetric_heating = 0.0
            
            femm.hi_addmaterial(
                str(material_name),
                float(thermal_conductivity[0]),
                float(thermal_conductivity[1]),
                float(volumetric_heating),
                float(volumetric_heat_capacity / 1e6) 
            )
            
            # Temperature conductivity table
            tk_data = getattr(material_qualities.thermal, 'temp_dependence', None)
            
            if tk_data:
                for row in tk_data:
                    t_val = self._strip_quantity(row[0], kelvin)
                    k_val = self._strip_quantity(row[1], THERMAL_CONDUCTIVITY)
                    
                    femm.hi_addtkpoint(material_name, float(t_val), float(k_val))
            
            self.materials.append(material_name)
            return material_name
       
        except Exception as err:
            msg = f"Failed to add {material_name!r} as a material within femm: {err}"
            raise RendererError(msg)

    def _save_changes(self):
        """ Manages the changes to the femm file """
        self.check_active()
        
        resolve_path_str = str(self.file_path.resolve())
        femm.hi_saveas(resolve_path_str)