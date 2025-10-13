"""
Filename: output_selector.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14

Description:
    OutputSelector dynamically selects and executes
    FEMMagneticSolver modules based on user requests.

    All outputs:
    - all

    Element-based outputs:
    - force_lorentz
    - torque_lorentz
    - force_stress_tensor
    - torque_stress_tensor
    - field_energy
    - aj_interaction
    - vector_potential
    - element_volume

    Circuit-based outputs:
    - circuit_power
    - circuit_voltage
    - circuit_current
    - circuit_resistance
    - circuit_flux_linkage
"""

from typing import Any, Callable, Union, Optional

from blueshark.solver.output_interface import BaseSelector
from blueshark.solver.femm.magnetic import (
    circuits,
    force,
    torque,
    elements
)


class FEMMagneticSelector(BaseSelector):
    """
    Output selector for FEMMagneticSolver
    """
    def __init__(
        self,
        requested_outputs: Union[str, list[str]] = "all",
    ) -> None:
        """
        Initializes the output selector with requested output names.

        Args:
            requested_outputs: Outputs to compute. Can be "all" or a list
                of names that must be a subset of available outputs.
        """
        self.available_outputs = {
            "force_lorentz":    (force.lorentz, self._run_element),
            "torque_lorentz":   (torque.lorentz, self._run_element),
            "force_stress_tensor": (
                force.weighted_stress_tensor,
                self._run_element
            ),
            "torque_stress_tensor": (
                torque.weighted_stress_tensor,
                self._run_element
            ),
            "field_energy":     (elements.field_energy, self._run_element),
            "aj_interaction":   (elements.aj_interaction, self._run_element),
            "vector_potential": (elements.vector_potential, self._run_element),
            "element_volume":   (elements.element_volume, self._run_element),
            "circuit_power":    (circuits.power, self._run_circuit),
            "circuit_voltage":  (circuits.voltage, self._run_circuit),
            "circuit_current":  (circuits.current, self._run_circuit),
            "circuit_resistance":   (circuits.resistance, self._run_circuit),
            "circuit_flux_linkage": (circuits.flux_linkage, self._run_circuit),
        }

        if isinstance(requested_outputs, str):
            if requested_outputs.lower() == "all":
                self.outputs = list(self.available_outputs.keys())

        else:
            # Convert requested outputs to lowercase
            requested_lower = [out.lower() for out in requested_outputs]
            unknown = set(requested_lower) - set(self.available_outputs.keys())
            if unknown:
                msg = (
                    f"Unknown outputs requested: {unknown}. "
                    f"Available: {list(self.available_outputs.keys())}"
                )
                raise ValueError(msg)
            self.outputs = requested_lower

    def compute(
        self,
        elements: Optional[list[int]] = None,
        circuits: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Compute all requested outputs.

        Args:
            elements: List of element IDs (for element-based outputs)
            circuits: List of circuit names (for circuit-based outputs)

        Returns:
            dict: Mapping output names -> results
                  (always keyed by element ID or circuit name)
        """
        results = {}
        subjects = {"elements": elements, "circuits": circuits}

        for name in self.outputs:
            func, runner = self.available_outputs[name]
            results[name] = runner(func, subjects)

        return results

    def _run_element(
        self,
        function: Callable[[int], Any],
        subjects: dict
    ) -> dict[int, Any]:
        """
        Apply an element-based output function.

        Args:
            function: Callable expecting an element ID.
            subjects: Must include 'elements'.

        Returns:
            dict: Element ID -> result
        """
        elements = subjects.get("elements")
        if not elements:
            msg = f"Missing 'elements' key; keys={list(subjects.keys())}"
            raise ValueError(msg)

        if not isinstance(elements, (list, tuple)):
            elements = [elements]

        return {element: function(element) for element in elements}

    def _run_circuit(
        self,
        function: Callable[[str], Any],
        subjects: dict
    ) -> dict[str, Any]:
        """
        Apply a circuit-based output function.

        Args:
            function: Callable expecting a circuit name.
            subjects: Must include 'circuits'.

        Returns:
            dict: Circuit name -> result
        """
        circuits_list = subjects.get("circuits")
        if not circuits_list:
            msg = f"Missing 'circuits' key; keys={list(subjects.keys())}"
            raise ValueError(msg)

        if not isinstance(circuits_list, (list, tuple)):
            circuits_list = [circuits_list]

        return {circuit: function(circuit) for circuit in circuits_list}
