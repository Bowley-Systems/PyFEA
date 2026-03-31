"""
Filename: renderer.py

Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

import femm
from shapely.geometry import Polygon, MultiPolygon, Point


from pyfea import meter, ampere, tesla, nullset, siemens
from pyfea.domain.units import Q, Material, linear_interpolate
from pyfea.domain.geometry.domain import Domain, BoundaryType, MagneticData
from pyfea.domain.circuits.definitions import StaticCircuit, Configuration

from pyfea.solver.femm.shapely_csg import FEMMConstructSolidGeometry as FEMMCSG
from pyfea.solver.renderer_interface import MagneticRenderer, RendererError
from pyfea.solver.femm.base_renderer import FEMMRenderer, FEMMPhysicsTypes


class FEMMMagnetostaticRenderer(FEMMRenderer, MagneticRenderer):
    """ Magnetostatic renderer for FEMM (finite element magnetic methods) """
    def suite_define(
        self, problem_type: FEMMPhysicsTypes, depth: Q, time_step = None
    ) -> None:
        """ Defines the suite problem as magnetostatic """
        del time_step

        femm.mi_probdef(
            0,                  # Frequency (Not used for magnetostatic)
            self.femm_unit,     # Default length unit in suite
            problem_type,       # Planar or Axial symmetric modelling
            self.tolerance,     # Meshing tolerance for problem
            depth
        )
        self.verbose.append("Frequency=0Hz, asymptotic field conditions")

    def draw_domain(self, domain: Domain) -> None:
        """ Defines the domain and than draws the elements within it """
        self.environmental_data = domain
        self._create_boundary(domain.boundary_type)

        # Evaluates Domain boundary and add boundary condition
        problem_domain = FEMMCSG.evaluate_csg_tree(domain.shape)
        self._draw_polygon(problem_domain, True, self.environmental_data.meta_data)

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
            self._draw_polygon(csg_part, metadata=domain.meta_data)

            element_coord = FEMMCSG.polygon_solid_centroid(csg_part, self.tolerance)
            self._add_properties(element_coord, part.metadata)

        # Computes complement region of parts & labels as environmental region
        parts_complement = FEMMCSG.part_complement(processed_parts, problem_domain)

        if isinstance(parts_complement, Polygon):
            self._label_environmental_region(parts_complement)
        elif isinstance(parts_complement, MultiPolygon):
            for poly in parts_complement.geoms:
                self._label_environmental_region(poly)

        else:
            msg = f"Unexpected environmental geometry type: {type(parts_complement)}"
            raise RendererError(msg)

        self._save_changes()

    def update_current(self, circuit: StaticCircuit) -> None:
        """ Changes the magnitude of the current flowing through a circuit """
        self.check_active()

        if circuit.name not in self.circuits:
            msg = f"{circuit!r} is not defined within the FEMM suite"
            raise RendererError(msg)

        try:
            current = self._strip_quantity(circuit.current, ampere)
            femm.mi_setcurrent(str(circuit.name), float(current))

        except Exception as err:
            msg = f"Failed to update current within circuit {circuit.name!r}: {err}"
            raise RendererError(msg) from err

    def move_element(self, element_id: Q, magnitude: Q, angles: Q) -> None:
        """ Moves an element within the simulation domain """
        return

    def rotate_element(self, element_id: Q, axis: Q, angles: Q) -> None:
        """ Rotates an element around an axis in the simulation domain """
        return

    def update_temperature(self, material: Material, temperature: Q) -> None:
        """ Updates the materials based on temperature """
        return

    def _create_boundary(self, boundary: BoundaryType) -> None:
        """ Adds boundary property to the outer domain boundary """
        self.check_active()
        try:
            match boundary:
                case BoundaryType.DIRICHLET:
                    femm.mi_addboundprop("A=0", 0, 0, 0, 0)
                    self.boundary = "A=0"
                    self.verbose.append("Dirichlet Boundary (A=0), Flux boundary shunt")

                case _:
                    msg = f"{boundary!r} not supported by {self.__class__.__name__}"
                    raise RendererError(msg)

        except Exception as err:
            msg = f"Failed to create dirichlet boundary condition: {err}"
            raise RendererError(msg) from err

    def _draw_polygon(
        self, polygon: Polygon, boundary: bool = False, metadata: MagneticData = None
    ) -> None:
        """ Draws polygon boundaries (exterior and interiors) """
        exterior = list(polygon.exterior.coords)

        # Draws exterior boundary
        for (x1, y1), (x2, y2) in zip(exterior, exterior[1:]):
            femm.mi_drawline(x1, y1, x2, y2)
            if boundary and metadata:
                # Add boundary conditions to segment
                femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.mi_setsegmentprop(self.boundary, 0, 0, 0, metadata.group.value)
                femm.mi_clearselected()

            if metadata and not boundary:
                # Adds element group to segment
                femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                femm.mi_setsegmentprop("", 0, 0, 0, metadata.group.value)
                femm.mi_clearselected()

        # Draw interior rings (holes)
        for interior in polygon.interiors:
            hole_coords = list(interior.coords)
            for (x1, y1), (x2, y2) in zip(hole_coords, hole_coords[1:]):
                femm.mi_drawline(x1, y1, x2, y2)
                if boundary and metadata:
                    # Add boundary conditions to segment
                    femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.mi_setsegmentprop(self.boundary, 0, 0, 0, metadata.group.value)
                    femm.mi_clearselected()

                if metadata and not boundary:
                    # Adds element group to segment
                    femm.mi_selectsegment((x1 + x2) / 2, (y1 + y2) / 2)
                    femm.mi_setsegmentprop("", 0, 0, 0, metadata.group.value)
                    femm.mi_clearselected()

    def _add_properties(self, coordinates: Point, meta: MagneticData) -> None:
        """ Sets element properties via adding a block-label"""
        try:
            femm.mi_addblocklabel(float(coordinates.x), float(coordinates.y))
            femm.mi_selectlabel(float(coordinates.x), float(coordinates.y))

            # Adds or retrieve the material name and converts element id
            material_name = self._add_material(meta)
            element_id = self._strip_quantity(meta.group, nullset)

            # Converts quantity if value is defined (not none)
            circuit = self._create_circuit(meta.circuit) if meta.circuit else None
            turns = self._strip_quantity(meta.turns, nullset) if meta.turns else 1

            magnetization = 0.0
            if meta.magnetization:
                magnetization = self._strip_quantity(meta.magnetization, nullset)

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
        """ Adds material to the FEMM suite using .UIV material """
        if not isinstance(metadata, MagneticData):
            msg = f"{self.__class__.__name__} can only load MagneticData, not {metadata!r}"
            raise RendererError(msg)

        # Extracts the material data, name and diameter from metadata
        material = metadata.material
        material_name, qualities = material.keys(), material.values()
        wire_diameter, number_of_strands, material_lamination = 0 * meter, 0, 0

        if metadata.diameter:
            wire_diameter = metadata.diameter
            material_lamination, number_of_strands = 3, 1
            material_name = f"{material_name}_{wire_diameter:.3f}"

        # Bypasses already loaded materials from being reloaded
        for loaded_material in self.materials:
            if loaded_material == material_name:
                return loaded_material

        # Extracts materials
        conductivity = getattr(qualities.electrical, 'temperature_conductivity', None)
        rel_perm = getattr(qualities.magnetic, 'relative_permeability', None)
        hysteresis = getattr(qualities.magnetic, "magnetic_hysteresis", None)
        coercivity = getattr(qualities.magnetic, 'coercivity', None)

        # Fails if missing materials and updates assumptions for sort missing comm
        if conductivity is None:
            msg = f"{material} must have a temperature electrical conductivity table"
            raise RendererError(msg)

        if rel_perm is None:
            rel_perm = [1, 1] * nullset
            if hysteresis is None:
                self.verbose.append(
                    f"{material_name} relative permeability assumed to be [1, 1]"
                )

        if coercivity is None:
            coercivity = 0 * ampere / meter
            self.verbose.append(f"{material_name} coercivity assumed to be {coercivity}")

        # Calculates the electrical conductivity at domain temperature
        conductivity = linear_interpolate(conductivity, self.environmental_data.temperature)

        # Extracts value from value:unit pairs
        relative_permeability = self._strip_quantity(rel_perm, nullset)
        conductivity = self._strip_quantity(conductivity, siemens / meter)
        coercivity = self._strip_quantity(coercivity, ampere / meter)
        wire_diameter = self._strip_quantity(wire_diameter, meter)
        try:
            femm.mi_addmaterial(
                str(material_name),
                float(relative_permeability[0]),
                float(relative_permeability[1]),
                float(coercivity),
                0,                                  # current density       (not supported)
                float(conductivity) / 1e6,          # FEMM requires MS/m not S/m
                0,                                  # Lamination thickness  (not supported)
                0,                                  # Phi_h_max             (not supported)
                1,                                  # Lamination fill       (not supported)
                int(material_lamination),
                0,                                  # Phi_hx                (not supported)
                0,                                  # Phi_hy                (not supported)
                int(number_of_strands),             # Number of strands     (not supported)
                float(wire_diameter) * 1000         # FEMM requires mm not meter
            )

            if hysteresis:
                self.verbose.append(f"{material_name} is using magnetic hysteresis curve")
                for row in hysteresis:
                    b_value = self._strip_quantity(row[0], tesla)
                    h_value = self._strip_quantity(row[1], ampere / meter)

                    femm.mi_addbhpoint(material_name, float(b_value), float(h_value))

            self._save_changes()
            self.materials.append(material_name)
            return material_name

        except Exception as err:
            msg = f"Failed to add {material_name} as material within femm: {err!r}"
            raise RendererError(msg) from err

    def _create_circuit(self, circuit: StaticCircuit) -> str:
        """ Adds a new circuit to the FEMM suite via static circuit dataclass """
        femm_circuit_type = None
        if circuit.configuration == Configuration.parallel:
            femm_circuit_type = 0
        elif circuit.configuration == Configuration.series:
            femm_circuit_type = 1
        else:
            msg = f"Circuit type {circuit.configuration!r} is not supported by FEMM"
            raise RendererError(msg)

        # Bypasses already loaded circuits from being reloaded
        for loaded_circuit in self.circuits:
            if loaded_circuit == circuit.name:
                return loaded_circuit

        self.verbose.append(f"{circuit.name} is assumed to be a constant current source")
        try:
            current = self._strip_quantity(circuit.current, ampere)
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

    def _save_changes(self):
        """ Manages the changes to the femm file """
        self.check_active()

        resolve_path_str = str(self.file_path.resolve())
        femm.mi_saveas(resolve_path_str)    
