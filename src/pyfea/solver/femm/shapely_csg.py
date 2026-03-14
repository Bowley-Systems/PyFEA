"""
Filename: shapely_csg.py
Description:
    Shapely implementation to allow CSG/Vector inputs for FEMM
    (finite element magnetic methods) translate CSG/Vector to
    FEMM native primitives for the FEMMRenderer.
"""

from typing import Any

from shapely.affinity import scale
from shapely.ops import unary_union
from shapely.geometry import Polygon as ShapelyPolygon, Point as ShapelyPoint
from shapely.geometry.base import BaseGeometry as ShapelyGeometry
from shapely.algorithms.polylabel import polylabel

from pyfea.domain.units import Quantity, strip_quantity, DIMENSIONLESS, LENGTH

from pyfea.solver.renderer_interface import RendererError
from pyfea.domain.geometry.elements.primitives import LineSegment, Ellipsoid
from pyfea.domain.geometry.elements.vectors import (
    GeometryElement, CSGNode, VectorGeometry, CSOperation, PrimitivesShapes
)


class FEMMConstructSolidGeometry:
    """
    Constructs Solid Geometry for FEMM (finite element magnetic method) using shapely 
    """
    @classmethod
    def vector_to_shapely(cls, geometry: VectorGeometry) -> ShapelyPolygon:
        """ Transforms PrimitivesShapes into shapely polygons """
        match geometry.shape:
            case PrimitivesShapes.POLYGON:
                coords: list[tuple[ShapelyPoint, ShapelyPoint]] = []

                for segment in geometry.data:
                    segment: LineSegment = segment
                    # Appends point one from segment to coords
                    coords.append((
                           cls._strip_quantity(segment.p1.x, 1 * LENGTH),
                           cls._strip_quantity(segment.p1.y, 1 * LENGTH)
                        )
                    )
                
                return ShapelyPolygon(coords)
                    
            case PrimitivesShapes.ELLIPSOID:
                ellipse: Ellipsoid = geometry.data

                # Extracts the central point and radius
                shapely_point = ShapelyPoint(
                    cls._strip_quantity(ellipse.center.x, 1 * LENGTH),
                    cls._strip_quantity(ellipse.center.y, 1 * LENGTH)
                )
                radius = cls._strip_quantity(ellipse.radius, 1 * LENGTH)
                
                # Extracts x and y dilation
                x_dilation = cls._strip_quantity(ellipse.x_dilation, 1 * DIMENSIONLESS)
                y_dilation = cls._strip_quantity(ellipse.y_dilation, 1 * DIMENSIONLESS)
                
                # Creates a circle and than scales relative to p
                circle = shapely_point.buffer(radius)
                shapely_ellipse = scale(
                    circle,
                    xfact=x_dilation,
                    yfact=y_dilation,
                    origin=shapely_point
                )
                
                return shapely_ellipse

            case _:
                msg = f"{geometry.shape!r} is not supported by FEMMConstructSolidGeometry"
                raise RendererError(msg)

    @classmethod
    def evaluate_csg_tree(cls, geometry: GeometryElement) -> ShapelyPolygon:
        """ Collapses pyfea csg tree notation into shapely geometry """
        if isinstance(geometry, VectorGeometry):
            return cls.vector_to_shapely(geometry)

        if isinstance(geometry, CSGNode):
            shapes: list[ShapelyPolygon] = [
                cls.evaluate_csg_tree(op) for op in geometry.operands
            ]

            if geometry.operation == CSOperation.UNION:
                base_shape = shapes[0]
                if not shapes:
                    raise RendererError("Empty union")

                result = unary_union(shapes)
                if not result.is_valid:
                    result = result.buffer(0)

                return result

            elif geometry.operation == CSOperation.SUBTRACT:
                base_shape = shapes[0]
                
                for shape in shapes[1:]:
                    base_shape = base_shape.difference(shape)
                    
                return base_shape
                
            elif geometry.operation == CSOperation.INTERSECT:
                base_shape = shapes[0]
                
                for shape in shapes[1:]:
                    base_shape = base_shape.intersection(shape)
                    
                return base_shape
                
            elif geometry.operation == CSOperation.FILLET:       
                radius = cls._strip_quantity(geometry.params["radius"], LENGTH)

                # Combines all the shapes into a union
                shape = unary_union(shapes)

                # Rounds both the outside corners and the inside elbows.
                buffer_dilation = shape.buffer(radius, join_style=1)
                buffer_erosion = buffer_dilation.buffer(-2 * radius, join_style=1)
                buffer_restoration = buffer_erosion.buffer(radius, join_style=1)
                
                return buffer_restoration

            else:
                msg = f"{geometry.operation!r} not supported by FEMMConstructSolidGeometry"   
                raise RendererError(msg)
        
        msg = f"{type(geometry)!r} is not supported by FEMMConstructSolidGeometry"
        raise RendererError(msg)
    
    @classmethod
    def polygon_solid_centroid(
        cls, polygon: ShapelyPolygon, tolerance: float
    ) -> ShapelyPoint:
        """ Returns a point guaranteed to be inside of the solid material of a polygon """
        return polylabel(polygon, tolerance)
    
    @classmethod
    def part_complement(
        cls, parts: list[ShapelyPolygon], domain: ShapelyPolygon
    ) -> ShapelyGeometry:
        """ Computes the complement of the part regions within domain set"""
        domain_union = unary_union(parts)
        return domain.difference(domain_union)
    
    @classmethod
    def _strip_quantity(cls, quantity: Quantity, ref: Quantity) -> Any:
        """ Strips quantity from value returns raw value """
        return strip_quantity(quantity, ref)