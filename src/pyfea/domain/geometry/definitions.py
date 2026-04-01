"""
Filename: definitions.py
Description:
    Defines the global geometry errors,
    dataclasses and enums within the 
    geometry modules.
"""
from abc import ABC, abstractmethod
from enum import Enum, auto


class GeometryDimensionError(TypeError):
    """ Exception for geometry dimension error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = f"{caller} raised error: {error}. "
        super().__init__(msg)


class PartError(TypeError):
    """ Exception for part error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = f"{caller} raised error: {error}. "
        super().__init__(msg)


class GeometricPrimitives(ABC):
    """ Defines the behavior of geometry primitives when displayed """
    @property
    @abstractmethod
    def _name(self) -> str:
        """ Dataclass name should be based of its properties """
        return ""

    def __str__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Point.name """
        return self._name

    def __eq__(self, other: object) -> bool:
        """ Checks equality by comparing string representations """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        """ Hashes the primitive by its string representation """
        return hash(self._name)


class PrimitivesShapes(Enum):
    """
    Fundamental Shape, all connections within the shape rotates clockwise
    """
    POLYGON   = auto()
    ELLIPSOID = auto()
    PATH      = auto()
    COMPOSITE = auto()

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return f"<PrimitiveShapes={self.name}>"

    def __str__(self) -> str:
        """ Returns the points name from PrimitivesShapes.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from PrimitivesShapes.type """
        return self._name


class CSOperation(Enum):
    """ Different types of CSG operation """
    UNION     = auto()
    SUBTRACT  = auto()
    INTERSECT = auto()
    EXTRUSION = auto()
    FILLET    = auto()

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return f"<CSOperation={self.name}>"

    def __str__(self) -> str:
        """ Returns the points name from CSOperation.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from CSOperation.type """
        return self._name


class CoordinateSystem(Enum):
    """ Types of coordinate systems """
    AXI_SYMMETRIC = auto()
    PLANAR        = auto()


class BoundaryType(Enum):
    """ Different boundary types available """
    DIRICHLET  = auto()
    CONVECTION = auto()