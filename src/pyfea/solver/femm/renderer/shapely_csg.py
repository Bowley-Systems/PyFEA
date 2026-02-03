"""
Filename: shapely_csg.py
Description:
    Shapely implementation to allow CSG/Vector inputs for FEMM
    (finite element magnetic methods) translate CSG/Vector to
    FEMM native primitives for the FEMMRenderer.
"""

from pyfea.domain.geometry.elements.parts import Part
from pyfea.domain.geometry.elements.vectors import GeometryElement, CSGNode, VectorGeometry

class FEMMConstructSolidGeometry:
    """
    Constructs Solid Geometry for FEMM (finite element magnetic method) using shapely 
    """
    
    @classmethod
    def evaluate_part(cls, part: Part):
        """ Evaluate part within the simulation domain """
        cls.evaluate_csg_tree(part.geometry)
    
    @classmethod
    def evaluate_csg_tree(cls, geometry: GeometryElement) -> None:
        if isinstance(geometry, VectorGeometry):
            print(f"Primitive: {geometry!r}")
            return

        if isinstance(geometry, CSGNode):
            print(f"CSG op: {geometry.operation}")

            for operand in geometry.operands:
                cls.evaluate_csg_tree(operand)
            return

        raise TypeError(f"Unknown geometry type: {type(geometry)}")