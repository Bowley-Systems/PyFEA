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

from pyfea.domain.units import Quantity, strip_quantity, LENGTH

from pyfea.solver.renderer_interface import RendererError
from pyfea.domain.geometry.elements.parts import Part
from pyfea.domain.geometry.elements.primitives import Point, LineSegment, Ellipsoid
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
                ellipse: Ellipsoid = geometry
                
                # Extracts the central point and radius
                shapely_point = ShapelyPoint(
                    cls._strip_quantity(ellipse.center.x, 1 * LENGTH),
                    cls._strip_quantity(ellipse.center.y, 1 * LENGTH)
                )
                radius = cls._strip_quantity(ellipse.radius, 1 * LENGTH)
                
                # Extracts x and y dilation
                x_dilation = cls._strip_quantity(ellipse.x_dilation, 1 * LENGTH)
                y_dilation = cls._strip_quantity(ellipse.y_dilation, 1 * LENGTH)
                
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
        if isinstance(geometry, VectorGeometry):
            return cls.vector_to_shapely(geometry)

        if isinstance(geometry, CSGNode):
            shapes: list[ShapelyPolygon] = [
                cls.evaluate_csg_tree(op) for op in geometry.operands
            ]

            if geometry.operation == CSOperation.UNION:
                return unary_union(shapes)

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
                
            else:
                msg = f"{geometry.operation!r} not supported by FEMMConstructSolidGeometry"   
                raise RendererError(msg)
        
        msg = f"{type(geometry)!r} is not supported by FEMMConstructSolidGeometry"
        raise RendererError(msg)
    
    @classmethod
    def _strip_quantity(cls, quantity: Quantity, ref: Quantity) -> Any:
        """ Strips quantity from value returns raw value """
        return strip_quantity(quantity, ref)