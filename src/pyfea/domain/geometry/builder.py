"""
Filename: builder.py

Description:
    Defines the GeometryBuilder class
    for constructing and defining solid geometry
"""

from pyfea.domain.units import Q, nullset
from pyfea.domain.geometry.elements.assemblies import Part, Component
from pyfea.domain.geometry.elements.metadata import MagneticData, ThermalData

from pyfea.domain.geometry.elements.primitives import Point, LineSegment, Ellipsoid
from pyfea.domain.geometry.elements.vectors import VectorGeometry, PrimitivesShapes, GeometryElement


class Builder:
    """ Builds geometry with vector objects and CSG system """
    @staticmethod
    def rectangle(bottom_left: tuple[Q, Q], length: Q, height: Q) -> VectorGeometry:
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
    def circle(center: tuple[Q, Q], radius: Q) -> VectorGeometry:
        """ Creates a circle from a center point and a radius """
        # Translates and validates the central point
        center = Point(center[0], center[1])

        circle = Ellipsoid(center, radius, 1 * nullset, 1 * nullset)
        return VectorGeometry(PrimitivesShapes.ELLIPSOID, circle)

    @staticmethod
    def promote_to_part(element: GeometryElement, metadata: MagneticData | ThermalData) -> Part:
        """ Promotes a CSNode or VectorGeometry class to a part """
        return Part(element, metadata)

    @staticmethod
    def promote_to_component(
        objects: Part | GeometryElement | list[Part] | list[GeometryElement],
        metadata: MagneticData | ThermalData | None = None
    ) -> Component:
        """ Promotes a part or geometry to a component """
        # Handle tuple input
        if isinstance(objects, tuple):
            items = list(objects)

        elif not isinstance(objects, list):
            items = [objects]
        else:
            items = objects

        if not items:
            # Check for empty list
            msg = "Cannot create component from empty list"
            raise ValueError(msg)

        # Check if all items are Parts or all are GeometryElements
        reference_item = items[0]
        is_part = isinstance(reference_item, Part)
        is_geometry = isinstance(reference_item, GeometryElement)

        if is_part:
            # Verifies that the list contains the all the same type
            if not all(isinstance(item, Part) for item in items):
                msg = "Cannot mix Parts with GeometryElements in a component"
                raise TypeError(msg)

            if metadata is not None:
                msg = "Cannot add metadata to Parts. Parts already contain their own metadata."
                raise ValueError(msg)

            return Component(items)

        if is_geometry:
            if not all(isinstance(item, GeometryElement) for item in items):
                # If the list isn't all geometry elements
                msg = "Cannot mix GeometryElements with Parts in a component"
                raise TypeError(msg)

            if metadata is None:
                # If the part doesn't have the required metadata
                msg = "Metadata is required when promoting GeometryElements to a component"
                raise ValueError(msg)

            parts = []
            for item in items:
                parts.append(Builder.promote_to_part(item, metadata))

            return Component(parts)

        msg = "Failed to create component as the inputs were incorrect"
        raise TypeError(msg)
