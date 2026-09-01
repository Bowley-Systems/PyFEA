"""
Filename: builder.py

Description:
    Defines the GeometryBuilder class
    for constructing and defining solid geometry
"""


from pyfea import Quantity as Q, nullset
from pyfea.domain.geometry.elements.parts import Part
from pyfea.domain.geometry.elements.metadata import MagneticData, ThermalData

from pyfea.domain.geometry.elements.primitives import Point, LineSegment, Ellipsoid
from pyfea.domain.geometry.elements.vectors import VectorGeometry, PrimitivesShapes, GeometryElement


class Builder:
    """ Builds geometry with vector objects and CSG system """

    @staticmethod
    def rectangle(
        bottom_left: tuple[Q, Q], length: Q, height: Q
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
    def circle(
        center: tuple[Q, Q], radius: Q
    ) -> VectorGeometry:
        """ Creates a circle from a center point and a radius """
        # Translates and validates the central point
        center = Point(center[0], center[1])

        circle = Ellipsoid(center, radius, 1 * nullset, 1 * nullset)
        return VectorGeometry(PrimitivesShapes.ELLIPSOID, circle)

    @staticmethod
    def promote_to_part(
        element: GeometryElement, metadata: MagneticData | ThermalData
    ) -> Part:
        """ Promotes a CSNode or VectorGeometry class to a part """
        return Part(element, metadata)
