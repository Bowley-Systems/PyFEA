"""
Filename: solver.py

Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""

import logging

from typing import Any

import femm

from pyfea.domain.units import Quantity, Material, ampere, volt, weber, newton, meter, tesla
from pyfea.solver.solver_interface import MagneticSolver
from pyfea.solver.solver_outputs import (
    SolverOutputs, CircuitOptions, MagneticOptions, SolverSolutions
)

from pyfea.domain.geometry.domain import Domain
from pyfea.domain.circuits.definitions import StaticCircuit
from pyfea.solver.femm.base_solver import FEMMSolver, SolverError
from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.magnetostatic.renderer import FEMMMagnetostaticRenderer


class FEMMMagnetostaticSolver(FEMMSolver, MagneticSolver):
    """ Magnetostatic Solver for FEMM (finite element magnetic methods) """
    def _create_renderer(
        self, filename: str, tolerance: float
    ) -> FEMMMagnetostaticRenderer:
        femm_file = self.folder_path / f"{filename}.fem"

        self.filename = filename
        return FEMMMagnetostaticRenderer(femm_file, FEMMPhysicsTypes.magnetostatic, tolerance)

    def setup(
        self,
        simulation_domain: Domain,
        filename: str = "magnetostatic",
        depth: Quantity = 0 * meter
    ) -> SolverSolutions:
        """ Setups the problem in FEMMRenderer """
        # Sets up the FEMM suite under the users coordinate system
        coordinate_system = simulation_domain.coordinate_system
        self.renderer = self._create_renderer(filename, self.tolerance)
        self.renderer.setup(coordinate_system, depth)

        # Draws the domain to the FEMM suite
        self.renderer.draw_domain(simulation_domain)
        self.problem_setup = True

        # Displays modelling assumptions to the user.
        print("=== model assumptions ===")
        for line in self.renderer.verbose:
            print(f"  • {line}")
        print("=========================")

    def _domain_analyse(self, outputs: SolverOutputs):
        """ Solves the problem defined within the FEMM suite """
        femm.mi_analyse(1)   # Hidden FEMM window
        femm.mi_loadsolution()

        results = {}
        for (target, option), _ in outputs.registry.items():

            if isinstance(option, CircuitOptions):
                data = self._circuit_outputs(option, target)
                results = self._add_result(results, target, option, data)

            elif isinstance(option, MagneticOptions):
                data = self._element_outputs(option, target)
                results = self._add_result(results, target, option, data)

            else:
                name = self.__class__.__name__
                msg = f"{type(option)!r} category is not supported by {name}"
                raise SolverError(msg)

        return SolverSolutions(results)

    def move_element(
        self, element_id: Quantity, magnitude: Quantity, angles: Quantity
    ):
        """ Moves an element within the simulation domain """
        self._setup_check("moving an element")
        self.renderer.move_element(element_id, magnitude, angles)

    def move_elements(
        self, element_ids: tuple[Quantity], magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves an element within the simulation domain """
        self._setup_check("moving an element")
        self.renderer.move_element(element_ids, magnitude, angles)

    def rotate_element(
        self, element_id: Quantity, axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates a element around an axis in the simulation domain """
        self._setup_check("rotating an element")
        self.renderer.rotate_element(element_id, axis, angles)

    def update_current(self, circuit: StaticCircuit) -> None:
        """ Updates the the current in a specific circuit """
        self._setup_check("updating currents")
        self.renderer.update_current(circuit)

    def update_temperature(self, material: list[Material] | Material, temperature):
        """ Update temperature of materials within FEMM suite """
        if not isinstance(material, (list, tuple)):
            material = [material]

        self._setup_check("updating temperature")
        for mat in material:
            self.renderer.update_temperature(mat, temperature)

    def _circuit_outputs(
        self, option: CircuitOptions, circuit: StaticCircuit
    ) -> Quantity:
        """ Gets the requested circuit output from the FEMM suite """
        circuit_properties = self._get_circuit_properties(circuit)

        match option:
            case CircuitOptions.current: return circuit_properties[0]
            case CircuitOptions.voltage: return circuit_properties[1]
            case CircuitOptions.flux_linkage: return circuit_properties[2]
            case CircuitOptions.power:
                return circuit_properties[0] * circuit_properties[1]

            case CircuitOptions.resistance:
                current = circuit_properties[0]
                tolerance = self.renderer.tolerance

                if abs(current) > tolerance * ampere:
                    return circuit_properties[1] / current

                msg = f"Failed to calculate resistance, {current} < {tolerance}"
                logging.error(msg)
                return 0.0 * (circuit_properties[1].unit / current.unit)

            case _:
                name = name = self.__class__.__name__
                msg = f"{option!r} is an unknown or unsupported output for {name}"
                raise SolverError(msg)

    def _element_outputs(
        self, option: MagneticOptions, element_id: Quantity
    ) -> Quantity:
        """ Gets the requested magnetic output from the FEMM suite """
        """NOTE: Might have to add a raise for axi; given axi torque might not work"""
        match option:
            case MagneticOptions.field_energy:
                return self._get_block_integral(element_id, 2) * (newton * meter)
            case MagneticOptions.cross_section:
                return self._get_block_integral(element_id, 5) * meter ** 2
            case MagneticOptions.b_field:
                return (
                    self._get_block_integral(element_id, 8),
                    self._get_block_integral(element_id, 9)
                ) * (tesla * meter ** 3)
            case MagneticOptions.volume:
                return self._get_block_integral(element_id, 10) * meter ** 3
            case MagneticOptions.force_lorentz:
                return (
                    self._get_block_integral(element_id, 11),
                    self._get_block_integral(element_id, 12)
                ) * newton
            case MagneticOptions.torque_lorentz:
                return self._get_block_integral(element_id, 15) * (newton * meter)
            case MagneticOptions.force_stress_tensor:
                return (
                    self._get_block_integral(element_id, 18),
                    self._get_block_integral(element_id, 19)
                ) * newton
            case MagneticOptions.torque_stress_tensor:
                return self._get_block_integral(element_id, 22) * (newton * meter)

            case _:
                name = name = self.__class__.__name__
                msg = f"{option!r} is an unknown or unsupported output for {name}"
                raise SolverError(msg)

    def _get_circuit_properties(self, circuit: StaticCircuit) -> tuple[Quantity]:
        """ Safely retrieves the properties of a specified circuit from FEMM suite """
        try:
            circuit_name = str(circuit.name)
            properties = femm.mo_getcircuitproperties(circuit_name)
            return (
                properties[0] * ampere,
                properties[1] * volt,
                properties[2] * weber
            )
        except Exception as err:
            msg = f"Failed to get properties from circuit {circuit.name!r}: {err}"
            raise SolverError(msg) from err

    def _get_block_integral(self, group: Quantity, integral_type: int) -> Any:
        """ Safely calculates a block integral on a specific group """
        try:
            femm.mo_groupselectblock(group.value)
            result = femm.mo_blockintegral(integral_type)
            femm.mo_clearblock()
            return result

        except Exception as err:
            msg = (
                f"Failed to calculate block integral of type {integral_type} "
                f"for element {group}: {err}"
            )
            raise SolverError(msg) from err

    def _clean_up(self) -> None:
        """ Closes FEMM and removes the .ans file """
        self.renderer.clean_up()
