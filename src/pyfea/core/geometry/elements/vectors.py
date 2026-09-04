"""
Filename: vectors.py

Description:
    Defines the dataclasses and enums for vector object
    and CSG system within the protocol
"""

from __future__ import annotations
from typing import Any

from abc import ABC
from dataclasses import dataclass

from pyfea.core.units import Q, meter
from pyfea.core.geometry.definitions import GeometricPrimitives
from pyfea.core.geometry.definitions import PrimitivesShapes, CSOperation

from pyfea.utilities.errors import GeometryDimensionError


class GeometryElement(ABC):
    """ Defines the construct solid geometry operations """
    def union(self, geometry_object: GeometryElement) -> CSGNode:
        """ Preforms a union between different geometric elements """
        return CSGNode(CSOperation.UNION, operands=(self, geometry_object))

    def subtract(self, geometry_object: GeometryElement) -> CSGNode:
        """ Preforms an subtraction between different geometric elements """
        return CSGNode(CSOperation.SUBTRACT, operands=(self, geometry_object))

    def intersect(self, geometry_object: GeometryElement) -> CSGNode:
        """ Preforms an intersection between different geometric elements """
        return CSGNode(CSOperation.INTERSECT, operands=(self, geometry_object))

    def extrude(
        self,
        height: Q,
        direction: Q = (0, 0, 1) * meter,
        manifold: bool = True
    ) -> GeometryElement:
        """Extrudes the 2D VectorGeometry into 3D geometry"""
        if not isinstance(height, Q) or not isinstance(direction, Q):
            msg = "3D geometry requires both height and direction to be quantities"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if height.value == 0 or height.unit != meter:
            msg = f"3D geometry height cannot be zero and has to be type {meter}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if direction.magnitude == 0 or direction.unit != meter:
            msg = f"3D geometry direction cannot have zero magnitude and has to be type {meter}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        return CSGNode(
            operation=CSOperation.EXTRUSION,
            operands=(self,),
            params={"height": height, "direction": direction, "manifold": manifold}
        )

    def smoothing_fillets(self, radius: Q) -> GeometryElement:
        """ Full Smoothing of part for both convex and concave """
        if not isinstance(radius, Q):
            msg = "Smoothing fillet requires a radius to be a quantity"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if radius.unit != meter:
            msg = f"Radius must be a LENGTH quantity not {type(radius)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        return CSGNode(
            operation=CSOperation.FILLET,
            operands=(self,),
            params={"radius": radius}
        )


@dataclass(slots=True, eq=False)
class CSGNode(GeometricPrimitives, GeometryElement):
    """Construct solid geometry node with optional parameters"""
    operation: CSOperation
    operands: tuple[GeometryElement, ...]
    params: dict[str, Any] | None = None

    @property
    def _name(self) -> str:
        """ Returns a clean, scannable string representation """
        param_str = f", params={self.params}" if self.params else ""
        operand_str = ", ".join(str(o) for o in self.operands)
        return f"<CSGNode: {self.operation.name}({operand_str}{param_str})>"


@dataclass(slots=True, eq=False)
class VectorGeometry(GeometricPrimitives, GeometryElement):
    """ Representation of a vector geometry element """
    shape: PrimitivesShapes
    data: Any

    @property
    def _name(self) -> str:
        """ Returns a clean, scannable string representation """
        return f"<VectorGeometry: shape={self.shape.name}>"
