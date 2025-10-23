"""
Filename: definitions.py
Author: William Bowley
Version: 1.3
Date: 2025-09-13

Description:
    This file defines enums that are used
    throughout the framework.

    These are independent of specific renderer/
    solver implementations.
"""

from typing import TypedDict, Optional
from dataclasses import dataclass
from enum import Enum, auto


class CoordinateSystem(Enum):
    """
    Types of coordinate systems.
    """
    AXI_SYMMETRIC = auto()
    PLANAR = auto()
    SPATIAL = auto()


class PhysicsType(Enum):
    """
    Defines the type of physics being simulated.
    """
    THERMAL = auto()       # Heat flow, temperature distribution
    MAGNETIC = auto()      # Magnetic fields, Lorentz forces

    # Haven't been implemented yet
    ELECTRIC = auto()      # Current, voltage, electrostatics
    MECHANICAL = auto()    # Force, stress, motion
    # MULTIPHYSICS = auto()  # Combined physics simulations


class RendererUnit(Enum):
    """
    All measurement units supported by the renderer & solvers.
    """
    MICROMETERS = auto()
    CENTIMETERS = auto()
    MILLIMETER = auto()
    METER = auto()


@dataclass
class Problem:
    """
    Defines the problem for the solver
    """
    frequency: Optional[float] = None
    RendererUnit: Optional[str] = None
    type: Optional[str] = None
    depth: Optional[float] = None
    tolerance: float = 0


class ShapeType(Enum):
    """
    Universal shapes within the framework.
    """
    POLYGON = auto()
    RECTANGLE = auto()
    CIRCLE = auto()
    ANNULUS_SECTOR = auto()
    ANNULUS_CIRCLE = auto()
    HYBRID = auto()


class Connectors(str, Enum):
    """
    Types of connectors for hybrid shapes.
    """
    LINE = "line"
    ARC = "arc"


class Connection(TypedDict, total=False):
    """
    Describes a connection in a hybrid geometry.
    """
    type: Connectors
    start: tuple[float, float]              # Start point for line/arc
    end: tuple[float, float]                # End point for line/arc
    center: Optional[tuple[float, float]]   # Center for arcs/circle
    start_angle: Optional[float]            # start angle for arcs
    end_angle: Optional[float]              # start angle for arcs
    radius: Optional[float]                 # Radius for circle/arc


class Geometry(TypedDict, total=False):
    """
    Describes the geometry of an element.
    Uses the RendererUnit selected by the user.
    Fields are optional depending on shape.
    """
    shape: ShapeType
    points: Optional[list[tuple[float, float]]]     # For POLYGON/RECTANGLE
    radius: Optional[float]                         # For CIRCLE
    radius_inner: Optional[float]                   # For arcs with thickness
    radius_outer: Optional[float]                   # For arcs with thickness
    center: Optional[tuple[float, float]]           # Center point
    start_angle: Optional[float]                    # Degrees, for arcs
    end_angle: Optional[float]                      # Degrees, for arcs
    enclosed: Optional[bool]                        # Enclosed [true] / [false]
    edges: Optional[list[Connection]]               # For HYBRID


class BoundaryType(Enum):
    """
    Different boundary types available
    """
    DIRICHLET = auto()
    NEUMANN = auto()


class CircuitType(Enum):
    """
    Different circuit configurations
    """
    PARALLEL = auto()
    SERIES = auto()


class CurrentPolarity(Enum):
    """
    Describes how current passes through an element.
    """
    FORWARD = auto()
    REVERSE = auto()
