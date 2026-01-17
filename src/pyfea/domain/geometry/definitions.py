"""
Filename: definitions.py
Author: William Bowley
Date: 2025-09-22

Description:
    Dataclasses/Enums to define geometric protocol
    primitives and shapes

    NOTE:
    Build a ABC just for simple things like names that is needed for
    every class anyways
"""

from dataclasses import dataclass
# from enum import Enum, auto

from picounits.core import Quantity


class GeometryDimensionError(TypeError):
    """ Exception for geometry dimension error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = (
            f"{caller} raised error {error}. "
            "This usually means a dimension was required as an input"
        )
        super().__init__(msg)


@dataclass(frozen=True, slots=True)
class Point:
    """ Representation of a point within the cartesian coordinate system """
    x: Quantity
    y: Quantity

    def __post_init__(self) -> None:
        """ Validates that type objects """
        if self.x and self.y:
            return

        error = (
            "Coordinate 1 and 2 must be Quantities, "
            f"not {type(self.x)} and {type(self.y)}"
        )
        raise GeometryDimensionError(Point.__name__, error)

    @property
    def name(self) -> str:
        """ Returns the point name as its x and y values """
        return f"<{self.x}, {self.y}>"

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name


@dataclass(frozen=True, slots=True)
class LineSegment:
    """ Representation of a direct line segment using the Point dataclass """
    p1: Point
    p2: Point

    @property
    def name(self) -> str:
        """ Returns the line segment name as its point 1 and point 2 """
        return f"<{self.p1}, {self.p2}>"

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name


@dataclass(frozen=True, slots=True)
class ArcSegment:
    """
    Representation of a arc segment using the point dataclass
    NOTE: Angle should be in radians unless stated otherwise
    """
    p1: Point
    p2: Point
    angle: Quantity

    @property
    def name(self) -> str:
        """ Returns the point name as its points and angle """
        return f"<({self.p1}, {self.p2}), {self.angle}>"

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self.name
