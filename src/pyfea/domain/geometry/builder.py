"""
Filename: builder.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines the GeometryBuilder class
    for constructing and defining solid geometry
"""


from picounits.core import Quantity
from picounits.constants import DIMENSIONLESS

from pyfea.domain.geometry.elements.vectors import (
    VectorGeometry, PrimitivesShapes, GeometryElement
)
from pyfea.domain.geometry.elements.primitives import (
    Point, LineSegment, Ellipsoid
)
from pyfea.domain.geometry.elements.parts import Metadata, Part


class GeometryBuilder:
    """ Builds geometry with vector objects and CSG system """

    @staticmethod
    def create_rectangle(
        bottom_left: tuple[Quantity, Quantity],
        length: Quantity,
        height: Quantity
    ) -> VectorGeometry:
        """ Creates a square vector geometry """
        x, y = bottom_left

        # Defines the four edges of the square
        bl, tl = Point(x, y), Point(x, y + height)
        br, tr = Point(x + length, y), Point(x + length, y + height)

        # Constructs the rectangle as a series of line segments
        data = (
            LineSegment(bl, tl), LineSegment(tl, tr),
            LineSegment(tr, br), LineSegment(br, bl)
        )

        return VectorGeometry(PrimitivesShapes.POLYGON, data)

    @staticmethod
    def create_circle(
        center: tuple[Quantity, Quantity],
        radius: Quantity
    ) -> VectorGeometry:
        """ Creates a circle from a center point and a radius """
        # Translates and validates the central point
        center = Point(center[0], center[1])

        circle = Ellipsoid(
            center, radius, 1 * DIMENSIONLESS, 1 * DIMENSIONLESS
        )
        return VectorGeometry(PrimitivesShapes.ELLIPSOID, circle)

    @staticmethod
    def promote_to_part(
        element: GeometryElement,
        metadata: Metadata
    ) -> Part:
        """ Promotes a CSNode or VectorGeometry class to a part """
        return Part(element, metadata)
