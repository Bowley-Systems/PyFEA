"""
Filename: parts.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines dataclasses and enum's for physical
    parts within the protocol.
"""

from dataclasses import dataclass
from picounits.core import Quantity
from picounits.constants import DIMENSIONLESS

from pyfea.domain.geometry.elements.vectors import CSGNode, VectorGeometry
from pyfea.domain.geometry.definitions import GeometryDimensionError


@dataclass(slots=True)
class Metadata:
    """ Construct solid geometry node between two objects """
    group: Quantity
    material: str   # Temp. Placeholder for the pointer to the material lib
    circuit: str | None = None
    turns: Quantity | None = None

    def __post_init__(self) -> None:
        """ Validates that metadata dimensions """
        if not isinstance(self.material, str):
            msg = f"Material must be str, not {type(self.material)}"
            raise ValueError(msg)

        if not isinstance(self.circuit, str):
            msg = f"Circuit must be str, not {type(self.circuit)}"
            raise ValueError(msg)

        if not isinstance(self.group, Quantity):
            msg = f"Group must be a Quantity not, {type(self.group)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if not isinstance(self.turns, Quantity):
            msg = f"Turns must be a Quantity not, {type(self.group)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.group.unit != DIMENSIONLESS:
            msg = f"Group must be a dimensionless not, {self.group.unit}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.group.unit != DIMENSIONLESS:
            msg = f"Group must be a dimensionless not, {self.group.unit}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Metadata=(group={self.group}, material={self.material}, "
            f"circuit={self.circuit}, turns={self.turns})>"
        )

    def __str__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name


@dataclass(slots=True)
class Part:
    """ Defines a physical part with physical metadata"""
    geometry: VectorGeometry | CSGNode
    metadata: Metadata

    def __post_init__(self) -> None:
        """ Validates that metadata and geometry is correct type """
        if not isinstance(self.geometry, (VectorGeometry, CSGNode)):
            msg = (
                "self.geometry must be type CSGNode or VectorGeometry, not "
                f"{type(self.geometry)}"
            )
            raise TypeError(msg)

        if not isinstance(self.metadata, Metadata):
            msg = (
                "self.metadata must be type Metadata, not "
                f"{type(self.metadata)}"
            )
            raise TypeError(msg)

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Part=(Geometry={self.geometry}, metadata={self.metadata})>"
        )

    def __str__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name
