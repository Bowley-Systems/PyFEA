"""
Filename: domain.py

Description:
    Defines the dataclasses for the domain. 
    Which holds the boundary type, material
    and parts.
"""

from dataclasses import dataclass

from pyfea.core.units import Q, DynamicLoader
from pyfea.core.geometry.elements.assemblies import Component
from pyfea.core.geometry.definitions import CoordinateSystem, BoundaryType
from pyfea.core.geometry.elements.vectors import CSGNode, VectorGeometry


@dataclass(slots=True)
class Domain:
    """ FEA simulation domain """
    parts: tuple[Component, ...]
    boundary_type: BoundaryType
    material: DynamicLoader
    coordinate_system: CoordinateSystem
    shape: VectorGeometry | CSGNode
    temperature: Q

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Part=(parts={self.parts}, "
            f"boundary={self.boundary_type}, "
            f"material={self.material}, "
            f"shape={self.shape}, "
            f"Coordinate System={self.coordinate_system})>"
        )

    def __str__(self) -> str:
        """ Returns self._name """
        return self._name

    def __repr__(self) -> str:
        """ Returns self._name """
        return self._name
