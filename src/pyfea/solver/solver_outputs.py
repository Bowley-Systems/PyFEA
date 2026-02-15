"""
Filename: solver_outputs.py
Description:
    Defines the configuration enums and the 
    SolverOutput Class for requiring outputs.
    
    And also defines the 
"""

from typing import Any, Iterable
from enum import Enum, auto

from pyfea.domain.circuits.builder import Circuit

class CircuitOptions(Enum):
    """ Defines the different possible circuit output variables """
    POWER           =   auto()
    VOLTAGE         =   auto()
    CURRENT         =   auto()
    RESISTANCE      =   auto()
    FLUX_LINKAGE    =   auto()


class MagneticOptions(Enum):
    """ Defines the different possible magnetic output variables """
    VOLUME                  = auto()
    CROSS_SECTION           = auto()
    FORCE_LORENTZ           = auto()
    TORQUE_LORENTZ          = auto()
    FIELD_ENERGY            = auto()
    B_FIELD                 = auto()
    FORCE_STRESS_TENSOR     = auto()
    TORQUE_STRESS_TENSOR    = auto()

class ThermalOptions(Enum):
    """ Defines the different possible thermal output variables """
    VOLUME                  = auto()
    CROSS_SECTION           = auto()
    AVERAGE_TEMPERATURE     = auto()
    FLUX_OVER_ELEMENT       = auto()
    GRADIENT_OVER_ELEMENT   = auto()


class SolverOutputs:
    """ Select outputs for the solver to compute """
    def __init__(self):
        """ Initializes the internal map for reference """
        # Tuple storage as key ensures that each combination is unique
        self.registry: dict[tuple[Any, Any], Any] = {}

    def _register(self, entity: Any, outputs: Any | Iterable[Any]) -> None:
        """Handles both single output objects and lists/tuples of outputs."""
        # Treat strings as single items, otherwise check if it's iterable
        if isinstance(outputs, (list, tuple)):
            for opt in outputs:
                self.registry[(entity, opt)] = entity
        else:
            self.registry[(entity, outputs)] = entity

    def add_circuit(
        self, circuit: Circuit, output: CircuitOptions | list[CircuitOptions]
    ) -> None:
        """" Requests a circuit output and the circuit to probe """
        self._register(circuit, output)

    def add_magnetic(
        self, element_id: Any, output: MagneticOptions | list[MagneticOptions]
    ) -> None:
        """ Requests a magnetic output and the element to probe """
        self._register(element_id, output)

    def add_thermal(
        self, element_id: Any, output: ThermalOptions | list[ThermalOptions]
    ) -> None:
        """ Requests a thermal output and the element to probe """
        self._register(element_id, output)


class SolverSolutions:
    def __init__(self, data_dict: dict = None, **kwargs):
        """ Dynamically adds solutions as attribute """
        data = data_dict or {}
        data.update(kwargs)

        for key, val in data.items():
            clean_key = key.lower().replace(" ", "_")
            if isinstance(val, dict):
                setattr(self, clean_key, SolverSolutions(val))

            else:
                setattr(self, clean_key, val)
    
    @property
    def _name(self):
        """ Returns """
        items = ", ".join([k for k in self.__dict__ if not k.startswith('_')])
        return f"<Solutions outputs: {items}>"
    
    def __str__(self) -> str:
        """ Returns the points name from self._name"""
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from self._name """
        return self._name


# Default class initialized for user to required from
RequestedOutputs = SolverOutputs()