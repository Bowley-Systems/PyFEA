"""
Filename: primitives.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines dataclasses and enum's for geometric
    primitives within the protocol
"""

from dataclasses import dataclass

from pyfea import meter, dimensionless, Quantity
from pyfea.domain.geometry.definitions import (
    GeometryDimensionError, GeometricPrimitives
)


@dataclass(frozen=True, slots=True)
class Point(GeometricPrimitives):
    """ Representation of a point within the cartesian coordinate system """
    x: Quantity
    y: Quantity

    def __post_init__(self) -> None:
        """ Validates that x and y coordinate Quantities """
        if not (isinstance(self.x, Quantity) and isinstance(self.y, Quantity)):
            error = (
                "Coordinates must be Quantities, "
                f"not {type(self.x)} and {type(self.y)}"
            )
            raise GeometryDimensionError(self.__class__.__name__, error)

        if self.x.unit != meter or self.y.unit != meter:
            error = (
                "Coordinates must have LENGTH dimensions, "
                f"not {self.x.unit} and {self.y.unit}"
            )
            raise GeometryDimensionError(self.__class__.__name__, error)

    @property
    def _name(self) -> str:
        """ Returns the point name as its x and y values """
        return f"<Point=({self.x}, {self.y})>"


@dataclass(frozen=True, slots=True)
class LineSegment(GeometricPrimitives):
    """ Representation of a direct line segment using the Point dataclass """
    p1: Point
    p2: Point

    def __post_init__(self) -> None:
        """ Validates that both p1 and p2 are Point objects """
        if isinstance(self.p1, Point) and isinstance(self.p2, Point):
            return

        error = (
            "Both p1 and p2 must be type Point, "
            f"not {type(self.p1)} and {type(self.p2)}"
        )
        raise GeometryDimensionError(self.__class__.__name__, error)

    @property
    def _name(self) -> str:
        """ Returns the line segment name as its point 1 and point 2 """
        return f"<LineSegment=({self.p1}, {self.p2})>"


@dataclass(frozen=True, slots=True)
class ArcSegment(GeometricPrimitives):
    """
    Representation of a arc segment using the point dataclass
    NOTE: Angle should be in radians unless stated otherwise
    """
    p1: Point
    p2: Point
    angle: Quantity

    def __post_init__(self) -> None:
        """
        Validates that both p1 and p2 are Point objects and angle is a Quantity
        """
        if not (isinstance(self.p1, Point) and isinstance(self.p2, Point)):
            error = (
                "Both p1 and p2 must be type Point, "
                f"not {type(self.p1)} and {type(self.p2)}"
            )
            raise GeometryDimensionError(self.__class__.__name__, error)

        if not isinstance(self.angle, Quantity):
            error = f"Angle must be type Quantity, not {type(self.angle)}"
            raise GeometryDimensionError(self.__class__.__name__, error)

        if self.angle.unit != dimensionless:
            error = f"Angle must be dimensionless, not {self.angle.unit}"
            raise GeometryDimensionError(self.__class__.__name__, error)

    @property
    def _name(self) -> str:
        """ Returns the point name as its points and angle """
        return f"<ArcSegment=(({self.p1}, {self.p2}), Angle={self.angle})>"


@dataclass(frozen=True, slots=True)
class Ellipsoid(GeometricPrimitives):
    """
    Representation of a Ellipsoid using the ellipsoid formula
    """
    center: Point
    radius: Quantity
    x_dilation: Quantity
    y_dilation: Quantity

    def __post_init__(self) -> None:
        """
        Validates that both p1 and p2 are Point objects and angle is a Quantity
        """
        if not isinstance(self.center, Point):
            error = f"Center must be type Point, not {type(self.center)}"
            raise GeometryDimensionError(self.__class__.__name__, error)

        for value in (self.radius, self.x_dilation, self.y_dilation):
            if not isinstance(value, Quantity):
                error = (
                    "Radius, x_dilation and y_dilation must all be quantities"
                )
                raise GeometryDimensionError(self.__class__.__name__, error)

        if self.radius.unit != meter:
            error = (
                f"Radius must have LENGTH dimension, not {self.radius.unit}"
            )
            raise GeometryDimensionError(self.__class__.__name__, error)

        for value in (self.x_dilation, self.y_dilation):
            if value.unit != dimensionless:
                error = (
                    "x_dilation and y_dilation must all be "
                    "defined dimensionless"
                )
                raise GeometryDimensionError(self.__class__.__name__, error)

    @property
    def _name(self) -> str:
        """ Returns the point name as its points and angle """
        name = (
            f"<Ellipsoid=({self.center}, radius={self.radius}, "
            f"dilation=({self.x_dilation}, {self.y_dilation})>"
        )
        return name
