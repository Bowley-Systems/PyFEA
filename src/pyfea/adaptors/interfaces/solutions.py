"""
Filename: solver_outputs.py

Description:
    Defines the configuration enums and the 
    SolverOutput Class for requiring outputs.
    
    And also defines the 
"""

from typing import Any, Iterable

from pyfea.core.geometry.domain import Component as GComponent
from pyfea.core.circuits.builder import Component as CComponent

from pyfea.adaptors.interfaces.requests import *
from pyfea.utilities.errors import ResultsError


class SolverRequests:
    """ Holds the users requested outputs from the solver. """
    def __init__(self):
        """ Initializes the internal map for reference """
        self.registry: dict[tuple[GComponent, CComponent]] = {}

    def _add(self, entity: Any, outputs: Any | Iterable[Any]) -> None:
        """ Handles both single output objects and lists/tuples of outputs. """
        if isinstance(outputs, (list, tuple)):
            # Check if it's iterable
            for opt in outputs:
                self.registry[(entity, opt)] = entity
        else:
            self.registry[(entity, outputs)] = entity

    def circuit(self, node: GComponent | CComponent, output: CircuitOptions) -> None:
        """" Requests a circuit output and the circuit to probe """
        self._add(node, output)

    def magnetic(self, component: GComponent, output: MagneticOptions)-> None:
        """ Requests a magnetic output and the element to probe """
        self._add(component, output)

    def thermal(self, component: GComponent, output: ThermalOptions) -> None:
        """ Requests a thermal output and the element to probe """
        self._add(component, output)


class SolverSolutions:
    """ Loads solution from solver into class attributes """
    def __init__(self, data: dict = None):
        """ Dynamically adds solutions keyed by object reference """
        self._store = data or {}

    def __getitem__(self, key):
        """ Returns solution for a given object reference """
        if key not in self._store:
            msg = f"{key!r} not found within solution results."
            raise ResultsError("SolverSolutions", msg)

        val = self._store[key]
        if isinstance(val, dict):
            return SolverSolutions(val)

        return val

    def __contains__(self, key):
        """ Checks if a solution exists for a given object reference """
        return key in self._store

    def __getattr__(self, key):
        """ Gets values stored within the parent """
        try:
            return self._store[key]

        except KeyError:
            msg = f"No solution for {key!r}"
            raise ResultsError("SolverSolutions", msg) from None

    @property
    def name(self):
        """ Constructs the name based on state """
        formatted_items = []
        for k in self._store:
            if hasattr(k, 'name'):
                formatted_items.append(k.name)
            else:
                formatted_items.append(k)

        items = ", ".join(formatted_items)
        return f"<Solutions outputs: {items}>"

    def __str__(self) -> str: return self.name
    def __repr__(self) -> str: return self.name
