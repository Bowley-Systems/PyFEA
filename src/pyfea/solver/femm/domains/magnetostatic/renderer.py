"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

from math import cos, sin, radians

from shapely.geometry import (
    point as ShapelyPoint,
    Polygon as ShapelyPolygon,
    MultiPolygon as ShapelyMultiPolygon,
)

import femm

from pyfea.domain.units import Quantity as Q
from pyfea import (
    LENGTH, COERCIVITY, CONDUCTIVITY, CURRENT, FLUX_DENSITY, K, nullset
)

from pyfea.domain.geometry.definitions import BoundaryType, CoordinateSystem
from pyfea.domain.geometry.elements.metadata import MagneticData
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.renderer_interface import MagneticRenderer, RendererError
from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.femm.base_renderer import FEMMRenderer, FEMMPhysicsTypes
from pyfea.domain.circuits.builder import Circuit, Configuration


class FEMMMagnetostaticRenderer(FEMMRenderer, MagneticRenderer):
    """ Magnetostatic renderer for FEMM (finite element magnetic methods) """
    def suite_define(
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

    def tolerance_march(self, tolerance: float) -> None:
        """ Defines the suite problem with new tolerance """
        femm.mi_probdef(
            0,                          # Frequency (Not Used)
            self.femm_unit,             # Default length unit in suite
            self.problem_type,          # Problem type defined during setup
            float(tolerance),           # New meshing tolerance
            self.depth                  # Depth of problem defined during setup
        )

        self.tolerance = tolerance

    def draw_domain(self, domain: Domain):
        """ Defines the domain and than draws the elements within """
        # Builds the environmental magnetic metadata
        self.environmental_data = domain.meta_data
        self._create_boundary_property(domain.boundary_type)

        # Draws the domain boundary and add boundary condition
        CSG_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon_boundaries(CSG_domain, True, self.environmental_data)

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
            self._draw_polygon_boundaries(CSG_polygon, metadata=part.metadata)
            element_coord = FEMMCSG.polygon_solid_centroid(CSG_polygon, self.tolerance)
            self._add_properties(element_coord, part.metadata)

        # Computes part region complement
        parts_complement = FEMMCSG.part_complement(parts_geometries, CSG_domain)

        if parts_complement.is_empty:
            msg = "Environmental regions are empty; Check geometry overlaps"
            raise RendererError(msg)

        # Label environmental regions
        if isinstance(parts_complement, ShapelyPolygon):
            self._label_environmental_region(parts_complement)
        elif isinstance(parts_complement, ShapelyMultiPolygon):
            for poly in parts_complement.geoms:
                self._label_environmental_region(poly)
        else:
            msg = f"Unexpected environmental geometry type: {type(parts_complement)}"
            raise RendererError(msg)

        self._save_changes()

    def move_element(self, element_id: Q, magnitude: Q, angles: Q) -> None:
        """ Moves a element by a vector; expects degrees """
        self.check_active()

        try:
            if not isinstance(element_id, (list, tuple)):
                groups_to_move = [element_id]
            else:
                groups_to_move = element_id

            for group in groups_to_move:
                group = self._strip_quantity(group, nullset)
                femm.mi_selectgroup(group)

            magnitude = self._strip_quantity(magnitude, LENGTH)
            angle = self._strip_quantity(angles, nullset)

            # Edge case: (yaw, pitch, roll is used) as input
            if len(angle) > 1:
                angle = angle[0]

            rad_angle = radians(angle)
            dx = magnitude * cos(rad_angle)
            dy = magnitude * sin(rad_angle)

            femm.mi_movetranslate(dx, dy)

            femm.mi_clearselected()
            self._save_changes()

        except Exception as err:
            msg = f"Failed to move element {element_id!r} due to {err}"
            raise RendererError(msg) from err

    def rotate_element(self, element_id: Q, axis: Q, angles: Q) -> None:
        """ Rotates a element by angle around a center axis; expects degrees"""

        self.check_active()
        if self.coordinate_system == CoordinateSystem.AXI_SYMMETRIC:
            msg = "Element cannot be rotated in axially symmetrical models"
            raise RendererError(msg)

        try:
            if isinstance(element_id.value, (int, float)):
                groups_to_move = [element_id]
            else:
                groups_to_move = element_id

            for group in groups_to_move:
                group = self._strip_quantity(group, nullset)
                femm.mi_selectgroup(group)

            axis = self._strip_quantity(axis, LENGTH)
            angle = self._strip_quantity(angles, nullset)

            # Edge case: (yaw, pitch, roll is used) as input
            if len(angle) > 1:
                angle = angle[0]

            x, y = axis
            femm.mi_moverotate(x, y, angle)

            femm.mi_clearselected()
            self._save_changes()

        except Exception as err:
            msg = f"Failed to rotate element {element_id!r} due to {err}"
            raise RendererError(msg) from err

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
            raise RendererError(msg) from err

    @classmethod
    def pre_defined(cls, name: str, loaded: list[str]) -> str:
        """ Checks to see if a material has already been loaded """
        for loaded_material in loaded:
            if loaded_material == name:
                return loaded_material

        msg = f"{name!r} is an uninitialized material, cannot edit"
        raise RendererError(msg)

    @classmethod
    def _linear_interpolate(cls, points: Q, value: Q) -> Q:
        """ Linear interpolates a quantity list from a specific linked value """
        if value <= points[0][0]:
            return points[0][1]

        if value >= points[-1][0]:
            return points[-1][1]

        # finds specific interval
        for index in range(len(points) - 1):
            x0, x1 = points[index][0], points[index + 1][0]
            y0, y1 = points[index][1], points[index + 1][1]

            if x0 <= value <= x1:
                slope = (y1 - y0) / (x1 - x0)
                return y0 + slope * (value - x0)

    def update_temperature(self, material, temperature):
        """ Updates a material definition to reflect a change in temperature """
        self.check_active()
        changes = []

        material_name = material.keys()
        material_qualities = material.values()
        block_name = self.pre_defined(material_name, self.materials)

        magnet_check = getattr(material_qualities, 'temp_coefficients', None)
        if magnet_check:
            hc_ref = material_qualities.magnetic.coercivity
            hc_min = material_qualities.temp_coefficients.Hc_min_temperature
            hc_max = material_qualities.temp_coefficients.Hc_max_temperature

            co_coercivity = material_qualities.temp_coefficients.coercivity

            if hc_min < temperature < hc_max:
                hc = hc_ref * (1 + co_coercivity * (temperature - 298.15 * K))
                hc = self._strip_quantity(hc, COERCIVITY)
            else:
                hc = 0.0
            changes.append((3, hc))

        try:
            conductivity_temp_dep = material_qualities.electrical.temp_dependence
            conductivity = self._linear_interpolate(conductivity_temp_dep, temperature)
            conductivity = self._strip_quantity(conductivity, CONDUCTIVITY)
            changes.append((5, conductivity/1e6))   # Femm requires MS/m

            for property_name, value in changes:
                femm.mi_modifymaterial(block_name, property_name, value)

            self._save_changes()

        except Exception as err:
            msg = f"Failed to update {material_name!r} within femm: {err}"
            raise RendererError(msg) from err

    def _draw_polygon_boundaries(
        self, polygon: ShapelyPolygon, boundary: bool = False,
        metadata: MagneticData = None
    ) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)

        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            femm.mi_drawline(x1, y1, x2, y2)
            if boundary and metadata:
                femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.mi_setsegmentprop(self.boundary_name, 0, 0, 0, metadata.group.value)
                femm.mi_clearselected()

            if metadata and not boundary:
                femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.mi_setsegmentprop("", 0, 0, 0, metadata.group.value)
                femm.mi_clearselected()

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                femm.mi_drawline(x1, y1, x2, y2)
                if boundary and metadata:
                    femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.mi_setsegmentprop(
                        self.boundary_name, 0, 0, 0, metadata.group.value
                    )
                    femm.mi_clearselected()

                if metadata and not boundary:
                    femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.mi_setsegmentprop("", 0, 0, 0, metadata.group.value)
                    femm.mi_clearselected()

    def _is_already_defined(self, pt: ShapelyPoint) -> bool:
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

    def _label_environmental_region(self, polygon: ShapelyPolygon) -> None:
        """ Adds environmental label to a single polygon region """
        if polygon.is_empty or polygon.area < self.junk_scale:
            return

        # Early exit if we already have a label very close by (Assumes defined)
        coordinates = FEMMCSG.polygon_solid_centroid(polygon, self.tolerance)
        if self._is_already_defined(coordinates):
            return

        # If coordinate not known, we add properties and accept it as defined.
        self.defined_area.append(coordinates)
        self._add_properties(coordinates, self.environmental_data)

    def _create_boundary_property(self, boundary: BoundaryType) -> None:
        """ Adds boundary property to the outer domain boundary """
        self.check_active()
        match boundary.name:
            case BoundaryType.DIRICHLET.name:
                try:
                    femm.mi_addboundprop("A=0", 0, 0, 0, 0)
                    self.boundary_name = "A=0"

                except Exception as err:
                    msg = f"Failed to create dirichlet boundary condition: {err}"
                    raise RendererError(msg) from err
            case _:
                msg = f"{boundary!r} not supported by {self.__class__.__name__}"
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
            raise RendererError(msg) from err

    def _add_properties(
        self,
        coordinates: ShapelyPoint,
        metadata: MagneticData
    ) -> None:
        """ Sets element properties via adding a block-label """
        try:
            femm.mi_addblocklabel(float(coordinates.x), float(coordinates.y))
            femm.mi_selectlabel(float(coordinates.x), float(coordinates.y))

            # Adds or retrieve the material name and converts element id
            material_name = self._add_material(metadata)
            element_id = self._strip_quantity(metadata.group, nullset)

            # Converts quantity if value is defined (not none)
            circuit = (
                self._create_circuit(metadata.circuit)
                if metadata.circuit else None
            )
            turns = (
                self._strip_quantity(metadata.turns, nullset)
                if metadata.turns else 1
            )
            magnetization = (
                self._strip_quantity(metadata.magnetization, nullset)
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
            raise RendererError(msg) from None

    def _add_material(self, metadata: MagneticData) -> str:
        """ Adds a material to the FEMM suite using .UIV material """
        if not isinstance(metadata, MagneticData):
            name = self.__class__.__name__
            msg = f"{name} can only load MagneticData, not {metadata}"
            raise RendererError(msg)

        # Extracts the material data and name
        material = metadata.material
        material_name = material.keys()
        material_qualities = material.values()

        # Variables for lamination properties within FEMM Suite
        wire_diameter = 0 * LENGTH                  # 0 = Non-stranded material
        material_lamination = 0                     # 0 = Solid material
        number_of_strands = 0                       # 0 = Solid material
        lamination_thickness = 0 * LENGTH           # 0 = Solid lamination

        if metadata.diameter is not None:
            wire_diameter = metadata.diameter
            material_lamination = 3     # FEMM: 3 = Magnet Wire
            number_of_strands = 1

            # material_name = f"{material_name}_{metadata.diameter.value}"

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
            relative_perm = self._strip_quantity(relative_permeability, nullset)

            coercivity = self._strip_quantity(coercivity, COERCIVITY)
            conductivity = self._strip_quantity(conductivity, CONDUCTIVITY)
            wire_diameter = self._strip_quantity(wire_diameter, LENGTH)
            lamination_thickness = self._strip_quantity(lamination_thickness, LENGTH)

            femm.mi_addmaterial(
                material_name,
                float(relative_perm[0]),
                float(relative_perm[1]),
                float(coercivity),
                0,                              # current density (not supported yet)
                float(conductivity) / 1e6,      # FEMM requires MS/m not S/m
                float(lamination_thickness),
                0.0,                            # Phi_h_max (not supported yet)
                1.0,                            # Lamination fill (not supported yet)
                int(material_lamination),
                0,                              # Phi_hx (not supported yet)
                0,                              # Phi_hy (not supported yet)
                int(number_of_strands),
                float(wire_diameter) * 1000     # FEMM requires mm not m for diameter
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
            raise RendererError(msg) from err

    def _save_changes(self):
        """ Manages the changes to the femm file """
        self.check_active()

        resolve_path_str = str(self.file_path.resolve())
        femm.mi_saveas(resolve_path_str)
