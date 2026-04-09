"""
Filename: interpreter.py

Description:
    Interprets pyfea intermediate representation (IR) of 
    circuit topology to ngspice net-list structure
"""

from __future__ import annotations
from dataclasses import dataclass

from typing import Any

from pyfea.domain.circuits.domain import Domain
from pyfea.domain.circuits.definitions import Terminal


@dataclass
class SpiceObjects:
    """ Tracks the usage of different components """
    source: int
    resistor: int
    capacitor: int
    inductor: int
    transistor: int

    @classmethod
    def create(cls) -> SpiceObjects:
        """ Factory method to create set with units """
        return cls(0, 0, 0, 0, 0)

    @property
    def magnitude(self) -> int:
        """ Calculates the magnitude of the dataclass """
        return sum(vars(self).values())

    @property
    def _name(self) -> str:
        """ Constructs a name based on attributes """
        return  (
            f"<objects(s:{self.source}, r:{self.resistor}, c:{self.capacitor}, "
            f"l:{self.inductor}, t:{self.transistor})>"
        )

    def __repr__(self) -> str: return self._name


class NGspiceInterpreter:
    """ Interprets pyfea circuit IR to ngspice net-list structure """
    def __init__(self, domain: Domain) -> None:
        """ Initializes the class and defines state variables """
        self.domain = domain

        # States
        self.node_map = {}
        self.objects = SpiceObjects.create()
        self.lines = []
        
        print(domain.linked)

    # def get_node(self, link: Terminal) -> Any:
    #     """ Translates a link object to a SPICE integer """
    #     link_in = id(link)
    #     if link_in not in self.node_map:
            