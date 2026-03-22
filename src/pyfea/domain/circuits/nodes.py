"""
Filename: nodes.py

Description:
    Defines the dataclasses and enums for node 
    object and branches within the protocol
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from pyfea.domain.circuits.definitions import (
    NodalPrimitives, Configuration, ComponentTypes, Terminal
)


@dataclass(slots=True, frozen=True)
class Component(NodalPrimitives):
    """ Fundamental node that holds component details. (Primary; Non branching) """
    type: ComponentTypes
    params: dict[str, Any]
    Linkable: bool = True

    @property
    def name(self) -> str:
        """ Returns a clean, scannable string representation """
        return f"<Component={self.type}, properties={len(self.params)}>"

    def __hash__(self):
        """ Ensures that each component has different hashes"""
        return hash(frozenset(self.params.items()))


class Device(NodalPrimitives):
    """ Abstract component that cannot have a internal configuration """
    def __init__(
        self,
        component: Component,
        terminals: list = ("main", "out")
    ) -> None:
        """ Initialize the device """
        if not isinstance(component, (Component, Abstract)):
            msg = f"item must be 'Component' or 'Branch' not {type(component).__name__}"
            raise TypeError(msg)

        self.component = component 

        # Constructs connection terminals
        self.terminals = {}
        for name in terminals:
            terminal = Terminal(name, self)
            self.terminals[name] = terminal
            setattr(self, name, terminal)

    @property
    def name(self) -> str:
        return f"<Device=({self.component})>"


class Abstract(NodalPrimitives):
    """ Abstract component defines how component and/or Abstract components relate """
    def __init__(
        self,
        configuration: Configuration,
        *components: Component | Abstract,
        terminals: list = ("main", "out")
    ) -> None:
        """ Initialize the branch; Configuration enum and"""
        if not isinstance(configuration, Configuration):
            msg = f"Relations must be defined use {Configuration}, not {configuration}"
            raise TypeError(msg)

        for item in components:
            if not isinstance(item, (Component, Abstract)):
                msg = f"item must be 'Component' or 'Branch' not {type(item).__name__}"
                raise TypeError(msg)

        self.components = components
        self.configuration = configuration

        # Constructs connection terminals
        self.terminals = {}
        for name in terminals:
            terminal = Terminal(name, self)
            self.terminals[name] = terminal
            setattr(self, name, terminal)

    @property
    def name(self) -> str:
        parts = ', '.join(
            item.name if isinstance(item, Abstract) else str(item.type)
            for item in self.components
        )
        return f"<abstract={self.configuration}, components=({parts})>"
