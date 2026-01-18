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

from dataclasses import dataclass
from enum import Enum, auto

from pyfea.domain.geometry.definitions import GeometricPrimitives

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


@dataclass(slots=True)
class CSGNode(GeometricPrimitives):
    """ Construct solid geometry node between two objects """
    operation: CSOperation
    object_a: GeometryElement
    object_b: GeometryElement

    @property
    def _name(self) -> str:
        return (
            f"<CSGNode: {self.operation.name}({self.object_a}, "
            f"{self.object_b})>"
        )


@dataclass(slots=True)
class VectorGeometry(GeometricPrimitives):
    """ Representation of a vector geometry element """
    shape: PrimitivesShapes
    data: Any

    @property
    def _name(self) -> str:
        """ Returns a clean, scannable string representation """
        return (
            f"<VectorGeometry: shape={self.shape.name}, "
            f"items={len(self.data)}>"
        )

    def union(self, geometry_object: VectorGeometry) -> CSGNode:
        """ Performs a union between this instance and another """
        return CSGNode(CSOperation.UNION, self, geometry_object)

    def subtract(self, geometry_object: VectorGeometry) -> CSGNode:
        """ Performs a subtract between this instance and another """
        return CSGNode(CSOperation.SUBTRACT, self, geometry_object)

    def intersect(self, geometry_object: VectorGeometry) -> CSGNode:
        """ Perform a intersect between this instance and another """
        return CSGNode(CSOperation.INTERSECT, self, geometry_object)
