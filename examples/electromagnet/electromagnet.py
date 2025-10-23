"""
File: electromagnet.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14
Description:
    Simple script to do analysis of
    a electromagnet in FEMM: Magnetic
"""

from blueshark.domain.material_manager.manager import MaterialManager
from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver
from blueshark.simulate.static import static_simulation

from blueshark.domain.definitions import (
    Geometry, ShapeType, RendererUnit, CoordinateSystem, CircuitType,
    CurrentPolarity, BoundaryType
)

# Gets materials from static material manager
manager = MaterialManager()
copper = manager.use_material("Copper Wire", wire_diameter=0.315)
iron = manager.use_material("Pure Iron")
air = manager.use_material("Air")

# Initializes renderer, defines problems and circuit
file_location = "examples/electromagnet/outputs/electromagnet.fem"
renderer = FEMMagneticRenderer(file_location)
renderer.setup(CoordinateSystem.PLANAR, RendererUnit.CENTIMETERS, depth=10)
renderer.create_circuit("phase_1", CircuitType.SERIES, 1)

# Defines the shapes and boundary geometry
domain = Geometry(shape=ShapeType.CIRCLE, center=(0, 0), radius=20)

core = Geometry(
    shape=ShapeType.RECTANGLE,
    enclosed=True,
    points=[(1, -2.5), (1, 2.5), (-1, 2.5), (-1, -2.5)]
)

positive = Geometry(
    shape=ShapeType.RECTANGLE,
    enclosed=True,
    points=[(1, -2.5), (1, 2.5), (3.5, 2.5), (3.5, -2.5)]
)

negative = Geometry(
    shape=ShapeType.RECTANGLE,
    enclosed=True,
    points=[(-1, -2.5), (-1, 2.5), (-3.5, 2.5), (-3.5, -2.5)]
)

# Draws the shapes to the renderer
renderer.draw(core, iron, 2)

renderer.draw(
    positive, copper, 1,
    circuit="phase_1", polarity=CurrentPolarity.FORWARD, turns=200
)

renderer.draw(
    negative, copper, 1,
    circuit="phase_1", polarity=CurrentPolarity.REVERSE, turns=200
)

# Adds a neumann boundary condition
renderer.draw_domain_boundary(domain, boundary_type=BoundaryType.NEUMANN)
renderer.define_environment_region(-1, (18, 0), air)

# Solves the magnetic problem and returns; all parameters from selector
result = static_simulation(
    renderer, FEMMagneticSolver, "all", [1, 2], "phase_1"
)
print(result)
