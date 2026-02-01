"""
Filename: parts.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines dataclasses and enum's for physical
    parts within the protocol.
"""

from dataclasses import dataclass

from pyfea.domain.geometry.elements.vectors import CSGNode, VectorGeometry
from pyfea.domain.geometry.elements.metadata import MagneticData
from pyfea.domain.geometry.definitions import PartError


@dataclass(slots=True)
class Part:
    """ Defines a physical part with physical metadata"""
    geometry: VectorGeometry | CSGNode
    metadata: MagneticData

    def __post_init__(self) -> None:
        """ Validates that metadata and geometry is correct type """
        if not isinstance(self.geometry, (VectorGeometry, CSGNode)):
            msg = (
                "self.geometry must be type CSGNode or VectorGeometry, not "
                f"{type(self.geometry)}"
            )
            raise PartError(self.__class__.__name__, msg)

        if not isinstance(self.metadata, (MagneticData)):
            msg = (
                "self.metadata must be type Metadata, not "
                f"{type(self.metadata)}"
            )
            raise PartError(self.__class__.__name__, msg)

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Part=(Geometry={self.geometry}, metadata={self.metadata})>"
        )

    def __str__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name
