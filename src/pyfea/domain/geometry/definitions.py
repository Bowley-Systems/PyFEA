"""
Filename: definitions.py
Author: William Bowley
Date: 2026-01-18

Description:
    Defines the global geometry errors,
    dataclasses and enums.
"""

from abc import ABC, abstractmethod


class GeometryDimensionError(TypeError):
    """ Exception for geometry dimension error """
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
