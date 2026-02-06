"""
Filename: domain.py
Description:
    Defines the dataclasses for the domain. 
    Which holds the boundary type, material
    and parts.
"""

from enum import Enum, auto
from dataclasses import dataclass

from pyfea.domain.units import Quantity, Material
from pyfea.domain.geometry.definitions import CoordinateSystem
from pyfea.domain.geometry.elements.parts import Part
from pyfea.domain.geometry.elements.vectors import CSGNode, VectorGeometry


class BoundaryType(Enum):
    """ Different boundary types available """
    DIRICHLET = auto()
    

@dataclass(slots=True)
class Domain:
    parts: tuple[Part, ...]
    group: Quantity
    boundary_type: BoundaryType
    material: Material
    coordinate_system: CoordinateSystem  
    shape: VectorGeometry | CSGNode
    
    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Part=(parts={self.parts}, group={self.group}, "
            f"boundary={self.boundary_type}, material={self.material}, "
            f"shape={self.shape}, Coordinate System={self.coordinate_system})>"
        )
        
    def __str__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name     