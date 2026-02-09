"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

import femm

from math import cos, sin, radians
from shapely.geometry import (
    Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon
)
from pyfea.domain.units import (
    LENGTH, PERMEABILITY, COERCIVITY, CONDUCTIVITY, DIMENSIONLESS, CURRENT,
    FLUX_DENSITY, Quantity
)

from pyfea.domain.geometry.domain import Domain, CoordinateSystem, BoundaryType
from pyfea.domain.geometry.elements.metadata import MagneticData

from pyfea.solver.renderer_interface import MagneticRenderer, RendererError
from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.femm.base_renderer import FEMMRenderer, FEMMPhysicsTypes 
from pyfea.domain.circuits.builder import Circuit, Configuration


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
        
        # Saves problem definitions for marching
        self.problem_type = problem_type
        self.depth = depth
    
    def tolerance_march(self, new_tolerance: float) -> None:
        """ Defines the suite problem with new tolerance """
        femm.mi_probdef(
            0,                          # Frequency (Not Used)
            self.femm_unit,             # Default length unit in suite
            self.problem_type,          # Problem type defined during setup
            float(new_tolerance),       # New meshing tolerance
            self.depth                  # Depth of problem defined during setup
        )
        
        self.tolerance = new_tolerance
    
    def draw_domain(self, domain: Domain):
        """ Defines the domain and than draws the elements within """
        # Builds the environmental magnetic metadata
        self.environmental_data = MagneticData(domain.group, domain.material)
        self._create_boundary_property(domain.boundary_type)
        
        # Draws the domain boundary and add boundary condition
        CSG_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon_boundaries(CSG_domain, True)
        
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
    
    def move_element(
        self, element_id: Quantity, magnitude: Quantity, angle: Quantity
    ) -> None:
        """ Moves a element by a vector; expects degrees """
        self.check_active()
        
        try:
            element_id = self._strip_quantity(element_id, DIMENSIONLESS) 
            magnitude = self._strip_quantity(magnitude, LENGTH)
            angle = self._strip_quantity(angle, DIMENSIONLESS)
            
            rad_angle = radians(angle)
            dx = magnitude * cos(rad_angle)
            dy = magnitude * sin(rad_angle)
            
            femm.mi_selectgroup(element_id)
            femm.mi_movetranslate(dx, dy)
            femm.mi_clearselected()

        except Exception as err:
            # NOTE: Add a fallback that rebuilds the geometry from scratch
            msg = f"Failed to move element {element_id!r} due to {err}"
            raise RendererError(msg)
    
    def rotate_element(
        self, element_id: Quantity, axis: Quantity, angle: Quantity
    ) -> None:
        """ Rotates a element by angle around a center axis; expects degrees"""
        self.check_active()
        if self.coordinate_system == CoordinateSystem.AXI_SYMMETRIC:
            msg = f"Element cannot be rotated in axially symmetrical models"
            raise RendererError(msg)

        try:
            element_id = self._strip_quantity(element_id, DIMENSIONLESS)
            axis = self._strip_quantity(axis, LENGTH)
            angle = self._strip_quantity(angle, DIMENSIONLESS)
            
            x, y = axis
            
            femm.mi_selectgroup(element_id)
            femm.mi_moverotate(x, y, angle)
            
            femm.mi_clearselected()
            self._save_changes()
        
        except Exception as err:
            # NOTE: Add a fallback that rebuilds the geometry from scratch
            msg = f"Failed to rotate element {element_id!r} due to {err}"
            raise RendererError(msg)
    
    def update_current(
        self, circuit: Circuit
    ) -> None:
        """ Changes the magnitude of the current flowing through a circuit """
        self.check_active()
        
        if circuit.name not in self.circuits:
            msg = f"{circuit!r} is not defined within the FEMM suite"
            raise RendererError(msg)
        
        try:
            current = self._strip_quantity(circuit.current, CURRENT)
            femm.mi_setcurrent(str(circuit.name), float(current))
            
        except Exception as err:
            msg = f"Failed to update current within circuit {circuit.name!r}: {err}"
            raise RendererError(msg)

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
            wire_diameter = metadata.diameter
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
                float(wire_diameter) * 1000             # FEMM requires mm not m for diameter
            )

            # Add b-h curve if values exist
            bh_data = getattr(material_qualities.magnetic, 'bh_curve', None)
            
            if bh_data:
                for row in bh_data:
                    b_val = self._strip_quantity(row[0], FLUX_DENSITY)
                    h_val = self._strip_quantity(row[1], COERCIVITY)
                    
                    femm.mi_addbhpoint(material_name, float(b_val), float(h_val))
            
            self.materials.append(material_name)
            return material_name
            
        except Exception as err:
            msg = f"Failed to add {material_name!r} as a material within femm: {err}"
            raise RendererError(msg)

    def _draw_polygon_boundaries(
        self, polygon: ShapelyPolygon, boundary: bool = False
    ) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)

        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            femm.mi_drawline(x1, y1, x2, y2)
            if boundary:
                femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.mi_setsegmentprop(self.boundary_name, 0, 0, 0, 0)
                femm.mi_clearselected()

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                femm.mi_drawline(x1, y1, x2, y2)
                if boundary:
                    femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.mi_setsegmentprop(self.boundary_name, 0, 0, 0, 0)
                    femm.mi_clearselected()
    
    def _label_environmental_region(self, polygon: ShapelyPolygon) -> None:
        """ Adds environmental label to a single polygon region """
        coordinates = FEMMCSG.polygon_solid_centroid(polygon, self.tolerance)
        self._add_properties(coordinates, self.environmental_data)

    def _create_boundary_property(self, property: BoundaryType) -> None:
        """ Adds boundary property to the outer domain boundary """
        self.check_active()
        match property:
            case BoundaryType.DIRICHLET:
                try:
                    femm.mi_addboundprop("A=0", 0, 0, 0, 0)
                    self.boundary_name = "A=0"

                except Exception as err:
                    msg = f"Failed to add dirichlet boundary to outer domain boundary"
                    raise RendererError(msg)
            case _:
                msg = f"{property!r} not supported by {self.__class__.__name__}"
                raise RendererError(msg)
        
    def _create_circuit(self, circuit: Circuit):
        """ Adds a new circuit to the FEMM suite via circuit dataclass """
        femm_circuit_type = None
        if circuit.configuration == Configuration.PARALLEL:
            femm_circuit_type = 0 
        elif circuit.configuration == Configuration.SERIES:
            femm_circuit_type = 1
        else:
            msg = f"Circuit type {circuit.configuration!r} is not supported by FEMM"
            raise RendererError(msg)
        
        try:
            # Bypasses already loaded materials from being reloaded
            for loaded_circuit in self.circuits:
                if loaded_circuit == circuit.name:
                    return loaded_circuit
            
            current = self._strip_quantity(circuit.current, CURRENT)
            femm.mi_addcircprop(
                str(circuit.name),
                float(current),
                int(femm_circuit_type)
            )

            self.circuits.append(circuit.name)
            return circuit.name
        
        except Exception as err:
            msg = f"Failed to add circuit {circuit.name!r} to FEMM: {err}"
            raise RendererError(msg)

    def _add_properties(
        self,
        coordinates: tuple[float, float],
        metadata: MagneticData
    ) -> None:
        """ Sets element properties via adding a block-label """
        try:
            femm.mi_addblocklabel(float(coordinates[0]), float(coordinates[1]))
            femm.mi_selectlabel(float(coordinates[0]), float(coordinates[1]))
            
            # Adds or retrieve the material name and converts element id
            material_name = self._add_material(metadata)
            element_id = self._strip_quantity(metadata.group, DIMENSIONLESS)
            
            # Converts quantity if value is defined (not none)
            circuit = (
                self._create_circuit(metadata.circuit)
                if metadata.circuit else None
            )
            
            turns = (
                self._strip_quantity(metadata.turns, DIMENSIONLESS) 
                if metadata.turns else 1
            ) 

            magnetization = (
                self._strip_quantity(metadata.magnetization, DIMENSIONLESS)
                if metadata.magnetization else 0.0
            )
            
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