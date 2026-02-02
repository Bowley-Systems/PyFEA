"""
Filename: vectors.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines the dataclasses and enums for vector object
    and CSG system within the protocol
"""

from __future__ import annotations
from typing import Union, Any

from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto

from pyfea import meter, Quantity
from pyfea.domain.geometry.definitions import GeometricPrimitives, GeometryDimensionError

""" A geometric element can be either a leaf (geometry) or a branch (node)"""
GeometryElement = Union["VectorGeometry", "CSGNode"]


class PrimitivesShapes(Enum):
    """
    Fundamental Shape, all connections within the shape rotates clockwise
    """
    POLYGON = auto()
    ELLIPSOID = auto()
    PATH = auto()
    COMPOSITE = auto()

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return f"<PrimitiveShapes={self.name}>"

    def __str__(self) -> str:
        """ Returns the points name from PrimitivesShapes.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from PrimitivesShapes.type """
        return self._name


class CSOperation(Enum):
    """ Different types of CSG operation """
    UNION = auto()
    SUBTRACT = auto()
    INTERSECT = auto()
    EXTRUSION = auto()

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return f"<CSOperation={self.name}>"

    def __str__(self) -> str:
        """ Returns the points name from CSOperation.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from CSOperation.type """
        return self._name


class GeometryElement(ABC):
    """ Defines the construct solid geometry operations """
    def union(self, geometry_object: GeometryElement) -> CSGNode:
        return CSGNode(CSOperation.UNION, operands=(self, geometry_object))

    def subtract(self, geometry_object: GeometryElement) -> CSGNode:
        return CSGNode(CSOperation.SUBTRACT, operands=(self, geometry_object))

    def intersect(self, geometry_object: GeometryElement) -> CSGNode:
        return CSGNode(CSOperation.INTERSECT, operands=(self, geometry_object))

    def extrude(
        self, 
        height: Quantity,
        direction: Quantity = (0, 0, 1) * meter,
        manifold: bool = True
    ) -> GeometryElement:
        """Extrudes the 2D VectorGeometry into 3D geometry"""
        if not isinstance(height, Quantity) or not isinstance(direction, Quantity):
            msg = "3D geometry requires both height and direction to be quantities"
            raise GeometryDimensionError(self.__class__.__name__, msg)
        
        if height.value == 0 or height.unit != meter:
            msg = f"3D geometry height cannot be zero and has to be type {meter}"
            raise GeometryDimensionError(self.__class__.__name__, msg)
        
        if direction.magnitude == 0 or direction.unit != meter:
            msg = (
                f"3D geometry direction cannot have zero magnitude "
                f"and has to be type {meter}"
            )
            raise GeometryDimensionError(self.__class__.__name__, msg)
        
        return CSGNode(
            operation=CSOperation.EXTRUSION,
            operands=(self,),
            params={
                "height": height,
                "direction": direction,
                "manifold": manifold
            }
        )


@dataclass(slots=True)
class CSGNode(GeometricPrimitives, GeometryElement):
    """Construct solid geometry node with optional parameters"""
    operation: CSOperation
    operands: tuple[GeometryElement, ...]
    params: dict[str, Any] | None = None

    @property
    def _name(self) -> str:
        param_str = f", params={self.params}" if self.params else ""
        operand_str = ", ".join(str(o) for o in self.operands)
        return f"<CSGNode: {self.operation.name}({operand_str}{param_str})>"


@dataclass(slots=True)
class VectorGeometry(GeometricPrimitives, GeometryElement):
    """ Representation of a vector geometry element """
    shape: PrimitivesShapes
    data: Any

    @property
    def _name(self) -> str:
        """ Returns a clean, scannable string representation """

        return (
            f"<VectorGeometry: shape={self.shape.name}>"
        )