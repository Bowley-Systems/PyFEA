"""
Filename: renderer.py

Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    thermostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the thermostatic
    problem within the FEMM suite. 
"""

import femm
from shapely.geometry import Polygon, MultiPolygon, Point

from pyfea import meter, kelvin, watt, joule, kilogram, nullset
from pyfea.domain.units import Q, linear_interpolate

from pyfea.domain.geometry.domain import Domain, Part, ThermalData, BoundaryType

from pyfea.solver.femm.base_renderer import FEMMRenderer
from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.renderer_interface import ThermalRenderer, RendererError

class FEMMThermostaticRenderer(FEMMRenderer, ThermalRenderer):
    """ Thermostatic renderer for FEMM (finite element magnetic methods) """
    def suite_define(
        self, problem_type: str, depth: float, time_step: float, solution_file: str = None
    ) -> None:
        """ Defines the suite problem as magnetostatic """
        self.verbose.append(f"Coordinates={problem_type}, depth={depth * meter:.3f}")
        if time_step > 0:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                problem_type,               # Planar or Axial Symmetric
                self.tolerance,             # Meshing tolerance
                depth,                      # Planar depth extrusion
                30,
                str(solution_file),
                float(time_step)
            )
            self.verbose.append(f"Frequency={1/time_step:.3f}Hz, dynamic diffusion conditions")
        else:
            femm.hi_probdef(
                self.femm_unit,             # Default length unit in suite
                problem_type,               # Planar or Axial Symmetric
                self.tolerance,             # Meshing tolerance
                depth,                      # Planar depth extrusion
            )
            self.verbose.append("Frequency=0Hz, asymptotic diffusion conditions")

        # Saves problem definitions for marching
        self.problem_type = problem_type
        self.depth = depth


    def draw_domain(self, domain: Domain) -> None:
        """ Defines the domain and than draws the elements within it """
        self.environmental_data = domain
        boundary_name = self._create_boundary(domain.boundary_type)

        # Evaluates Domain boundary and add boundary condition
        problem_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon(problem_domain, domain.meta_data, boundary_name)

        # Domain parts and labels solids for all parts
        pre_processed_parts = domain.parts
        processed_parts = []

        if not isinstance(pre_processed_parts, (list, tuple)):
            pre_processed_parts = [pre_processed_parts]

        # Constructs via CSG evaluation & draws to polygon with properties to domain
        for part in pre_processed_parts:
            csg_part = FEMMCSG.evaluate_csg_tree(part.geometry)
            processed_parts.append(csg_part)

            # Draws part geometry to FEMM suite & set properties to part
            self._draw_polygon(csg_part)

            element_coord = FEMMCSG.polygon_solid_centroid(csg_part, self.tolerance)
            self._add_properties(element_coord, part.metadata)

        # Computes complement region of parts & labels as environmental region
        parts_complement = FEMMCSG.part_complement(processed_parts, problem_domain)

        if isinstance(parts_complement, Polygon):
            self._draw_polygon(parts_complement, domain.meta_data, boundary_name, False)
            self._label_environmental_region(parts_complement)

        elif isinstance(parts_complement, MultiPolygon):
            for poly in parts_complement.geoms:
                self._draw_polygon(poly, domain.meta_data, boundary_name, False)
                self._label_environmental_region(poly)

        else:
            msg = f"Unexpected environmental geometry type: {type(parts_complement)}"
            raise RendererError(msg)

        self._save_changes()

    def update_volumetric_heat_source(self, part: Part, magnitude: Q) -> None:
        """ Updates a material volumetric heat """
        self.check_active()

        # Extract material properties and metadata
        material = part.metadata.material
        name = material.keys()

        # Updates name if part is setup as a heat source
        if part.metadata.volumetric_heating:
            name = f"source_{part.metadata.group}_{name}"
        else:
            msg = f"{part} must be configured as a heat source during setup"
            raise RendererError(msg)

        block_name = self._pre_defined(name, self.materials)
        try:
            volumetric_heating = self._strip_quantity(magnitude, joule / meter ** 3)
            femm.hi_modifymaterial(block_name, 3, float(volumetric_heating))
            self._save_changes()

        except Exception as err:
            msg = f"Failed to update {block_name!r} within femm: {err}"
            raise RendererError(msg) from err

    def update_conductor_heat_source(self, part: Part, magnitude: Q) -> None:
        """ Update conductor heat source """
        del part, magnitude

        msg = f"Conductors are not supported by {self.__class__.__name__}"
        raise RendererError(msg)

    def move_element(self, part: Part, magnitude: Q, angles: Q) -> None:
        """ Moves a element by a vector; expects degrees """
        del part, magnitude, angles

        msg = f"Moving element not implemented for {self.__class__.__name__}"
        raise RendererError(msg)

    def rotate_element(self, part: Part, axis: Q, angles: Q) -> None:
        """ Rotates a element by angle around a center axis; expects degrees"""
        del part, axis, angles

        msg = f"move rotate not implemented for {self.__class__.__name__}"
        raise RendererError(msg)

    def _create_boundary(self, boundary: BoundaryType) -> str:
        """ Adds boundary property to the outer domain boundary """
        self.check_active()
        meta = self.environmental_data.meta_data

        try:
            match boundary:
                case BoundaryType.DIRICHLET:
                    temperature = self._strip_quantity(meta.temperature, kelvin)
                    femm.hi_addboundprop("Fixed Temperature", 0, temperature, 0, 0, 0, 0)
                    self.verbose.append(
                        f"Dirichlet Boundary, Fixed temp = {temperature:.3f} K"
                    )

                    return str(temperature)

                case BoundaryType.CONVECTION:
                    temperature = self._strip_quantity(meta.temperature, kelvin)

                    conv = watt / (meter ** 2 * kelvin)
                    transfer = self._strip_quantity(meta.convection_coefficient, conv)

                    name = str(f"{transfer}_{temperature}")
                    femm.hi_addboundprop(name, 2, 0, 0, temperature, transfer, 0)
                    self.verbose.append(
                        f"Convection Boundary, Temp={temperature:.3f} | Conv: {transfer:.3f}"
                    )

                case _:
                    msg = f"{boundary!r} not supported by {self.__class__.__name__}"
                    raise RendererError(msg)

        except Exception as err:
            msg = f"Failed to create boundary condition: {err}"
            raise RendererError(msg) from err

    def _draw_polygon(
        self,
        polygon: Polygon,
        metadata: ThermalData = None,
        boundary: str = None,
        draw: bool = True
    ) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)

        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            if draw:
                # Adds polygon to domain
                femm.hi_drawline(x1, y1, x2, y2)

            if boundary and metadata:
                # Add boundary conditions to segment
                femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.hi_setsegmentprop(boundary, 0, 0, 0, metadata.group.value, "")
                femm.hi_clearselected()

            if metadata and not boundary:
                # Adds element group to segment
                femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.hi_setsegmentprop(
                    "", 0, 0, 0, metadata.heating_index.value, metadata.group.value
                )
                femm.hi_clearselected()

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                if draw:
                    # Adds polygon to domain
                    femm.hi_drawline(x1, y1, x2, y2)

                if boundary and metadata:
                    # Add boundary conditions to segment
                    femm.hi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.hi_setsegmentprop(boundary, 0, 0, 0, metadata.group.value, "")
                    femm.hi_clearselected()

    def _add_properties(self, coordinates: Point, meta: ThermalData) -> None:
        """ Sets region properties via adding a block-label """
        try:
            femm.hi_addblocklabel(float(coordinates.x), float(coordinates.y))
            femm.hi_selectlabel(float(coordinates.x), float(coordinates.y))

            # Adds or retrieve the material name and converts element id
            element_id = self._strip_quantity(meta.group, nullset)
            name = self._add_material(meta)
            if meta.volumetric_heating:
                name = f"source_{meta.group.stripped}_{name}"

            femm.hi_setblockprop(
                str(name),          # Material name to assign
                1,                  # Mesher automatically chooses the mesh density
                0,                  # Size constraint on the mesh in the block
                int(element_id)     # Member of group 'number group'
            )

            femm.hi_clearselected()

        except Exception as err:
            name = self.__class__.__name__
            msg = f"Failed to set properties for {element_id!r} in {name}: {err}"
            raise RendererError(msg) from err

    def _add_material(self, metadata: ThermalData) -> str:
        """ Adds material to FEMM suite using .UIV material """
        if not isinstance(metadata, ThermalData):
            msg = f"{self.__class__.__name__} can only load ThermalData, not {metadata!r}"
            raise RendererError(msg)

        # Extracts the material data, name and diameter from metadata
        name, qualities = metadata.material.keys(), metadata.material.values()

        # Bypasses already loaded materials from being reloaded
        for loaded_material in self.materials:
            if loaded_material == name: return loaded_material

        # Extracts materials
        volumetric_heating = metadata.volumetric_heating
        heat_capacity = getattr(qualities.thermal, 'specific_heat', None)
        cond_table = getattr(qualities.thermal, 'temperature_conductivity', None)

        # Fails if missing materials and updates assumptions for sort missing comm
        if volumetric_heating:
            name = f"source_{metadata.group.stripped}_{name}"
            self.verbose.append(
                f"{name} is a volumetric heat source at {volumetric_heating:.3f}"
            )

        if cond_table is None:
            msg = f"{name} must have a temperature thermal conductivity table"
            raise RendererError(msg)

        if heat_capacity is None:
            msg = f"{name} must have a heat capacity value for transient sims; Assuming=0"
            self.verbose.append(msg)

        # Calculates the thermal conductivity at domain temperature
        conductivity = linear_interpolate(cond_table, self.environmental_data.temperature)

        # Extracts value from value:unit pairs
        conductivity = self._strip_quantity(conductivity, watt / (meter ** 2 * kelvin))
        heat_capacity = self._strip_quantity(heat_capacity, joule / (kilogram * kelvin))
        volumetric_heating = self._strip_quantity(volumetric_heating, watt / meter ** 3)

        try:
            self.check_active()
            femm.hi_addmaterial(
                str(name),
                float(conductivity), float(conductivity),       # x,y conductivity
                float(volumetric_heating),                      # Volumetric heating (w/m^3)
                float(heat_capacity) /  1e6                     # Volume heat generation
            )

            conductivity = watt / (meter ** 2 * kelvin)
            for row in cond_table:
                t_val = self._strip_quantity(row[0], kelvin)
                k_val = self._strip_quantity(row[1], conductivity)

                femm.hi_addtkpoint(str(name), float(t_val), float(k_val))

            self.materials.append(name)
            return name

        except Exception as err:
            msg = f"Failed to add {name!r} as a material within femm: {err}"
            raise RendererError(msg) from err

    def _save_changes(self) -> None:
        """ Manages the changes to the femm file """
        self.check_active()

        resolve_path_str = str(self.file_path.resolve())
        femm.hi_saveas(resolve_path_str)
