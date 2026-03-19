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
    NodalPrimitives, Configuration, ComponentTypes
)


@dataclass(slots=True)
class Component(NodalPrimitives):
    """ Fundamental node that holds component details. (Primary; Non branching) """
    type: ComponentTypes
    params: dict[str, Any]
    Linkable: bool = True

    @property
    def name(self) -> str:
        """ Returns a clean, scannable string representation """
        return f"<Component={self.type}, properties={len(self.params)}>"


class Branch(NodalPrimitives):
    """ 
    Relational branch defines how component nodes and branches relate to each other
    """
    __slots__ = ('configuration', 'component')

    def __init__(
        self,
        configuration: Configuration,
        *components: Component | Branch
    ) -> None:
        """ Initialize the branch; Configuration enum and"""
        if not isinstance(configuration, Configuration):
            msg = f"Relations must be defined use {Configuration}, not {configuration}"
            raise TypeError(msg)

        for item in components:
            if not isinstance(item, (Component, Branch)):
                msg = f"item must be 'Component' or 'Branch' not {type(item).__name__}"
                raise TypeError(msg)

            if isinstance(item, Component):
                if not item.Linkable:
                    msg = f"{item!r} is a non-linkable component. It cannot be in a branch"
                    raise TypeError(msg)

        self.components = components
        self.configuration = configuration

    @property
    def name(self) -> str:
        parts = ', '.join(
            item.name if isinstance(item, Branch) else str(item.type)
            for item in self.components
        )
        return f"<Branch={self.configuration}, components=({parts})>"
