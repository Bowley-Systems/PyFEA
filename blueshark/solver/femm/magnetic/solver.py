"""
File: solver.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14
Description:
    Solver based on BaseSolver for
    FEMM magnetic simulations.

    Solves the problem defined by the
    renderer and returns outputs through
    the output interface class.
"""

import logging
import femm

from pathlib import Path
from typing import Union, Any
from blueshark.solver.solver_interface import BaseSolver
from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.output_selector import FEMMagneticSelector
from blueshark.domain.constants import (
    MAXIMUM_TOLERANCE, MAXIMUM_FAILS
)


class FEMMagneticSolver(BaseSolver):
    """
    Magnetic solver for FEMM:Magnetic.
    """
    def __init__(
        self,
        renderer: FEMMagneticRenderer,
        requested_outputs: Union[str, list[str]] = "all",
        elements: list[int] = None,
        circuits: list[str] = None
    ) -> None:
        """
        Initializes the solver with the FEMMagneticRenderer.

        Args:
            renderer: FEMMagneticRenderer instance.
            requested_outputs: Output(s) to compute (or "all").
            elements: List of element IDs for element-based outputs.
            circuits: List of circuit names for circuit-based outputs.
        """
        renderer.clean_up()
        self.is_active = renderer.is_active

        self.file_path = Path(renderer.file_path)
        self.problem = renderer.problem
        self.original_tolerance = renderer.original_tolerance

        self.selector = FEMMagneticSelector(requested_outputs)
        self.subjects = {
            "elements": elements or [],
            "circuits": circuits or []
        }

    def solve(self) -> dict[str, Any]:
        """
        Solves the problem defined by the FEMMagneticRenderer.
        Returns a dictionary of requested outputs.
        """
        tolerance = self.problem.tolerance

        for attempt in range(1, MAXIMUM_FAILS + 1):
            try:
                femm.openfemm(1)  # Hidden FEMM window
                femm.opendocument(str(self.file_path.resolve()))
                self.is_active = True

                femm.mi_analyse(1)  # Hidden FEMM window
                femm.mi_loadsolution()
                msg = (
                    f"Solved problem with tolerance {tolerance} "
                    f"on attempt {attempt}"
                )
                logging.info(msg)
                break

            except RuntimeError as e:
                if tolerance > MAXIMUM_TOLERANCE or attempt == MAXIMUM_FAILS:
                    msg = (
                        f"Solver failed after {attempt} attempts with "
                        f"tolerance {tolerance}: {e}"
                    )
                    logging.error(msg)
                    raise RuntimeError(msg) from e

                msg = (
                    f"Solver failed on attempt {attempt} with "
                    f"tolerance {tolerance}: {e}. Retrying..."
                )
                logging.warning(msg)

                # Increase tolerance for next attempt
                tolerance *= 10
                self._change_tolerance(tolerance)

        outputs = self.selector.compute(
            elements=self.subjects.get("elements"),
            circuits=self.subjects.get("circuits")
        )

        # Resets the tolerance to user tolerance for next step
        self._change_tolerance(self.original_tolerance)
        self.clean_up()

        return outputs

    def _change_tolerance(self, tolerance: float) -> None:
        """
        Changes the required tolerance of the FEMM magnetic problem.
        """
        self._check_active()
        self.problem.tolerance = tolerance

        femm.mi_probdef(
            float(self.problem.frequency),
            self.problem.RendererUnit,
            self.problem.type,
            float(self.problem.tolerance),
            float(self.problem.depth)
        )

        self._save_changes()

    def _save_changes(self) -> None:
        """Saves the FEMM file."""
        self._check_active()
        femm.mi_saveas(str(self.file_path.resolve()))

    def _check_active(self) -> None:
        """Ensures FEMM is active and the document is open."""

        if self.is_active:
            return
        try:
            femm.openfemm(1)
            femm.opendocument(str(self.file_path.resolve()))
            self.is_active = True

        except Exception as e:
            msg = f"FEMMagnetic solver failed to reactivate: {e}"
            logging.critical(msg)
            raise RuntimeError(msg) from e

    def clean_up(self) -> None:
        """Closes FEMM and removes the temp .ans file"""
        if self.is_active:
            try:
                femm.closefemm()
                self.is_active = False

            except Exception as e:
                logging.warning(f"Could not close FEMM instance: {e}")

        ans_path = self.file_path.with_suffix(".ans")
        if ans_path.exists():
            try:
                ans_path.unlink()
            except Exception as e:
                logging.warning(f"Could not delete .ans file: {e}")
