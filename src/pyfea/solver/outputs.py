"""
Filename: solver_outputs.py

Description:
    Defines the configuration enums and the 
    SolverOutput Class for requiring outputs.
    
    And also defines the 
"""

from typing import Any, Iterable
from enum import Enum, auto

from pyfea.domain.geometry.domain import Component as GComponent
from pyfea.domain.circuits.builder import Component as CComponent


class ImageOptions(Enum):
    """Defines the different possible image outputs"""
    field_contour           = auto()
    field_heatmap           = auto()
    vector_field            = auto()
    streamline              = auto()


class CircuitOptions(Enum):
    """ Defines the different possible circuit output variables """
    power                   = auto()
    gain                    = auto()
    phase                   = auto()
    voltage                 = auto()
    current                 = auto()
    resistance              = auto()
    flux_linkage            = auto()


class MagneticOptions(Enum):
    """ Defines the different possible magnetic output variables """
    volume                  = auto()
    cross_section           = auto()
    force_lorentz           = auto()
    torque_lorentz          = auto()
    field_energy            = auto()
    b_field                 = auto()
    force_stress_tensor     = auto()
    torque_stress_tensor    = auto()


class ThermalOptions(Enum):
    """ Defines the different possible thermal output variables """
    volume                  = auto()
    cross_section           = auto()
    average_temperature     = auto()
    flux_over_element       = auto()


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

    def image(self, output: ImageOptions, component: GComponent | None = None) -> None:
        """ Requests an image of the field effects across the simulation. """
        self._add(component, output)


class SolverSolutions:
    """ Loads solution from solver into class attributes """
    def __init__(self, data: dict = None):
        """ Dynamically adds solutions keyed by object reference """
        self._store = data or {}

    def __getitem__(self, key):
        """ Returns solution for a given object reference """
        if key not in self._store:
            raise KeyError(f"No solution found for {key!r}")
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
            raise AttributeError(msg) from None

    @property
    def name(self):
        """ Constructs the name based on state """
        items = ", ".join([k.name if hasattr(k, 'name') else k for k in self._store])
        return f"<Solutions outputs: {items}>"

    def __str__(self) -> str: return self.name
    def __repr__(self) -> str: return self.name
