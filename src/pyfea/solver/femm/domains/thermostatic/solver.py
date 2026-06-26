"""
Filename: solver.py

Description:
    Solver adaptor interface for FEMM (finite element magnetic methods)
    thermostatic simulation domain. 
    
    Uses the FEMMRenderer and FEMMConstructSolidGeometry classes to construct
    physics problems and than solves them with tolerance marching. 
"""


from pathlib import Path
from typing import Any

import femm

from pyfea.solver.solver_interface import ThermalSolver
from pyfea.solver.femm.base_solver import FEMMSolver, SolverError
from pyfea.solver.solver_outputs import (
    SolverOutputs, ThermalOptions, SolverSolutions
)

from pyfea.domain.units import Quantity, second, meter, kelvin, watt
from pyfea.domain.geometry.domain import Domain

from pyfea.solver.femm.base_renderer import FEMMPhysicsTypes
from pyfea.solver.femm.domains.thermostatic.renderer import FEMMThermostaticRenderer


class FEMMThermostaticSolver(FEMMSolver, ThermalSolver):
    """ Thermostatic Solver for FEMM (finite element magnetic methods) """
    def __init__(
        self,
        folder_path: Path,
        verbose: bool = True,
        tolerance: float = 1e-012,
    ) -> None:
        """ Initializes the FEMM solver and FEMM renderer """  
        self._folder_path_exist(folder_path)

        self.verbose = verbose
        self.tolerance = tolerance
        self.filename: str = None

        # Overrides the FEMMRenderer on BaseRenderer
        self.renderer: FEMMThermostaticRenderer = None
        self.problem_setup = False

    def _create_renderer(
        self, filename: str, tolerance: float
    ) -> FEMMThermostaticRenderer:
        """ Creates the renderer under specific conditions and file path"""
        femm_file = self.folder_path / f"{filename}.feh"

        self.filename = filename
        solver_type = FEMMPhysicsTypes.thermostatic
        return FEMMThermostaticRenderer(femm_file, solver_type, tolerance)

    def setup(
        self,
        simulation_domain: Domain,
        filename: str = "thermostatic",
        depth: Quantity = 0 * meter,
    ) -> SolverSolutions:
        """ Setups the problem in FEMMRenderer """
        # Sets up the FEMM suite under the users coordinate system
        coordinate_system = simulation_domain.coordinate_system
        self.simulation_domain = simulation_domain
        self.renderer = self._create_renderer(filename, self.tolerance)
        self.renderer.setup(coordinate_system, depth)

        # Draws the domain to the FEMM suite
        self.renderer.draw_domain(simulation_domain)
        self.problem_setup = True

        # Displays modelling assumptions to the user.
        if self.verbose is True:
            print("=== model assumptions ===")
            for line in self.renderer.verbose:
                print(f"  • {line}")
            print("=========================")

    def solve(self, outputs: SolverOutputs, time_step: Quantity = 0 * second) -> Any:
        """ Solves the problem constructed by the FEMMRenderer """
        try:
            # Opens FEMM suite as a hidden window
            self._setup_check("solving FEM problem")
            self.renderer.check_active()

            if time_step.value > 0:
                ans_path = Path(f"{self.filename}.anh")
                self.renderer.suite_define(
                    self.renderer.problem_type,
                    self.renderer.depth,
                    time_step,
                    ans_path
                )
            else:
                self.renderer.suite_define(
                    self.renderer.problem_type, self.renderer.depth, time_step,
                )

            solution = self._domain_analyse(outputs)

            self._clean_up()
            return solution

        except Exception as err:
            msg = f"FEMMSolver failed to solve problem due to {err}"
            raise SolverError(msg) from err

    def _domain_analyse(self, outputs: SolverOutputs) -> Any:
        """ Solves the problem defined within the FEMM suite """
        femm.hi_analyse(1)   # Hidden FEMM window
        femm.hi_loadsolution()

        results = {}
        for (target, option), _ in outputs.registry.items():
            if isinstance(option, ThermalOptions):
                data = self._operations(option, target.metadata.group)
                results = self._add_result(results, target, option, data)

            else:
                name = self.__class__.__name__
                msg = f"{type(option)!r} category is not supported by {name}"
                raise SolverError(msg)

        return SolverSolutions(results)

    def _operations(
        self, option: ThermalOptions, element: ThermalOptions
    ) -> Quantity:
        """ Gets the requested thermal output from the FEMM suite """
        match option:
            case ThermalOptions.average_temperature:
                return self._get_block_integral(element, 0)[0] * kelvin
            case ThermalOptions.cross_section:
                return self._get_block_integral(element, 1)[0] * meter ** 2
            case ThermalOptions.volume:
                return self._get_block_integral(element, 2)[0] * meter ** 3
            case ThermalOptions.gradient_over_element:
                return self._get_block_integral(element, 3) * (kelvin / meter)
            case ThermalOptions.flux_over_element:
                return self._get_block_integral(element, 4) * (watt / meter ** 2)

            case _:
                name = name = self.__class__.__name__
                msg = f"{option!r} is an unknown or unsupported output for {name}"
                print(msg)
                raise SolverError(msg)

    def _get_block_integral(self, group: Quantity, integral_type: int) -> Any:
        """ Safely calculates a block integral on a specific group """
        try:
            femm.ho_groupselectblock(group.value)
            result = femm.ho_blockintegral(integral_type)
            femm.ho_clearblock()
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
