"""
File: renderer_interface.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14
Description:
    Abstract base classes defining the interface for renderers.

    - BaseRenderer: Core generic methods
    - MagneticRenderer: Magnetic-specific extensions
    - ThermalRenderer: Thermal-specific extensions
    - ElectricalRenderer: Electrical-specific extensions
"""

from pathlib import Path
from typing import Any, Optional
from abc import ABC, abstractmethod

from blueshark.domain.constants import SETUP_CURRENT
from blueshark.domain.definitions import (
    Geometry, RendererUnit, CoordinateSystem, CircuitType,
    CurrentPolarity, BoundaryType
)


class BaseRenderer(ABC):
    """
    Core interface for all renderers.
    """
    @abstractmethod
    def __init__(self, file_path: Path) -> Any:
        """
        Initializes the renderer under the file_path
        given by the user
        """
        self.file_path = file_path

    @abstractmethod
    def setup(
        self,
        system: CoordinateSystem,
        RendererUnit: RendererUnit
    ) -> Any:
        """
        Setup the rendering environment or simulation space
        """

    @abstractmethod
    def draw(
        self,
        shape: Geometry,
        material: dict[str, Any],
        element_id: int
    ) -> Any:
        """
        Draw shape with given material and element_id
        """

    @abstractmethod
    def draw_domain_boundary(
        self,
        shape: Geometry,
        material: dict[str, Any],
        boundary_type: BoundaryType,
        shells: Optional[int]
    ) -> None:
        """
        draw domain boundary for the problem
        """

    @abstractmethod
    def move_element(
        self,
        element_ids: list[int] | int,
        magnitude: float,
        angles: tuple[float, float, float],
    ) -> None:
        """
        Moves an element by a vector with magnitude and angles
        """

    @abstractmethod
    def rotate_element(
        self,
        element_ids: list[int] | int,
        axis: tuple[float, float, float],
        angles: tuple[float, float, float]
    ) -> None:
        """
        Rotates a group by an angle around an axis
        """

    @abstractmethod
    def clean_up(self) -> None:
        """
        Removes any temp files and closes the renderer.
        """


class MagneticRenderer(BaseRenderer, ABC):
    """
    Renderer with magnetic simulation capabilities.
    """
    @abstractmethod
    def draw(
        self,
        shape: Geometry,
        material: dict[str, Any],
        element_id: int,
        circuit: Optional[str],
        polarity: Optional[CurrentPolarity],
        turns: Optional[int] = 1,
        magnetization: Optional[float] = 0.0
    ) -> Any:
        """
        Draw shape with given material and element_id
        """

    @abstractmethod
    def create_circuit(
        self,
        circuit_name: str,
        circuit: CircuitType,
        initial_current: float = SETUP_CURRENT
    ) -> Any:
        """
        Adds a circuit to the environment either in
        series or parallel.
        """

    @abstractmethod
    def change_circuit_current(
        self,
        circuit: str,
        current: float
    ) -> Any:
        """
        Changes the current flowing through a circuit
        """


class ThermalRenderer(BaseRenderer, ABC):
    """
    Renderer with thermal simulation capabilities.
    """
    @abstractmethod
    def add_heat_source(
        self,
        material: dict[str, Any],
        initial_volumetric_heat: float
    ) -> Any:
        """
        Adds a new material based on material that has
        volumetric heat defined in its material definition
        """

    @abstractmethod
    def change_heating(
        self,
        material: dict[str, Any],
        volumetric_heat_source: float
    ) -> Any:
        """
        Changes the volumetric heating in a material.
        """


class ElectricalRenderer(BaseRenderer, ABC):
    """
    Renderer with electrical simulation capabilities.
    """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
