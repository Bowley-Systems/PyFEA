"""
Filename: domain.py

Description:
    Defines the dataclasses for the domain. 
    Which holds the boundary type, material
    and parts.
"""

from dataclasses import dataclass

from pyfea.domain.units import Q
from pyfea.domain.geometry.definitions import CoordinateSystem, BoundaryType
from pyfea.domain.geometry.elements.parts import Part
from pyfea.domain.geometry.elements.vectors import CSGNode, VectorGeometry
from pyfea.domain.geometry.elements.metadata import MagneticData, ThermalData


@dataclass(slots=True)
class Domain:
    """ FEA simulation domain """
    parts: tuple[Part, ...]
    boundary_type: BoundaryType
    meta_data: MagneticData | ThermalData
    coordinate_system: CoordinateSystem
    shape: VectorGeometry | CSGNode
    temperature: Q

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Part=(parts={self.parts}, "
            f"boundary={self.boundary_type}, meta_data={self.meta_data}, "
            f"shape={self.shape}, Coordinate System={self.coordinate_system})>"
        )

    def __str__(self) -> str:
        """ Returns self._name """
        return self._name

    def __repr__(self) -> str:
        """ Returns self._name """
        return self._name
