"""
Filename: solver_outputs.py
Description:
    Defines the configuration enums and the 
    SolverOutput Class for requiring outputs.
    
    And also defines the 
"""

from typing import Any
from enum import Enum, auto
from abc import ABC
from dataclasses import dataclass

from pyfea.domain.circuits.builder import Circuit

class circuit_outputs(Enum):
    """ Defines the different possible circuit output variables """
    POWER           =   auto()
    VOLTAGE         =   auto()
    CURRENT         =   auto()
    RESISTANCE      =   auto()
    FLUX_LINKAGE    =   auto()


class magnetic_outputs(Enum):
    """ Defines the different possible magnetic output variables """
    FORCE_LORENTZ           = auto()
    TORQUE_LORENTZ          = auto()
    FIELD_ENERGY            = auto()
    B_FIELD                 = auto()
    FORCE_STRESS_TENSOR     = auto()
    TORQUE_STRESS_TENSOR    = auto()


class SolverOutputs:
    """ Output selector for solvers """
    def __init__(self):
        """ Initializes the internal map for reference """
        self._registry: dict[Any, Any] = {}
    
    def add_circuit(
        self, circuit: Circuit, outputs: circuit_outputs
    ) -> None:
        """ Requests a circuit output and the circuit to probe """
        self._registry[outputs] = circuit
        
    def add_magnetic(
        self, element_id: float | int, outputs: magnetic_outputs
    ) -> None:
        """ Requests a magnetic output and the element to probe """
        self._registry[outputs] = element_id
        

@dataclass(slots=True)
class SolverSolutions(ABC):
    """ Expandable for outputs """
    
    @property
    def _name(self):
        """ Enum output name based on its properties """
        return f"<Solutions outputs: {self.value}>"  

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name
