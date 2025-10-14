"""
File: coilgun.py
Author: William Bowley
Version: 1.4
Date: 2025-10-13
Description:
    Simple script to do perform time-domain
    analysis of a single stage battery powered
    coil gun using FEM: Magnetic Renderer & Solver

    Uses mm-g-s Units:
        - Millimeter, gram, second, ampere
"""

import matplotlib.pyplot as plt
import time
import sys

from math import sin, radians, pi

from blueshark.domain.material_manager.manager import MaterialManager
from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver
from blueshark.simulate.static import static_simulation
from blueshark.domain.definitions import (
    CoordinateSystem, Units, CircuitType, ShapeType, Geometry,
    CurrentPolarity, BoundaryType
)

from physics import (
    estimate_turns, calculate_inductance, format_time,
    projectile_drag, clipping_current, rk_2nd_order_currents
)

# Simulation CONSTANTS (mm, g, s)
INITIAL_CURRENT = 1e-4  # Needed for the inductance calculations
FLUID_DENSITY = 1.225e-6
COEFFICIENT_DRAG = 0.82
TIME_STEP = 5e-4
BOUNDARY_MATERIAL = "air"
BOUNDARY_GROUP = 1
FILE_LOCATION = "examples/simple_coilgun/coilgun.fem"

# Circuit Parameters (volts, amp)
voltage = 18            # Supply voltage
current_limit = 40      # Maximum current before clipping

# Coil Parameters (mm)
coil_length = 50
coil_inner_radi = 6.25
coil_outer_radi = 17.5
coil_material = "Copper Wire"
coil_wire_dia = 1.25
coil_fill_factor = 0.65
COIL_GROUP = 2

# Projectile Parameters (mm, g)
projectile_radi = 4
projectile_length = 50
projectile_material = "Pure Iron"
projectile_mass = 20
PROJECTILE_GROUP = 3

# Simulation setup (Material Manager & Renderer)
manager = MaterialManager()
boundary_material = manager.use_material(BOUNDARY_MATERIAL)
projectile_material = manager.use_material(projectile_material)
coil_material = manager.use_material(
    coil_material, wire_diameter=coil_wire_dia
)

renderer = FEMMagneticRenderer(FILE_LOCATION)
renderer.setup(CoordinateSystem.AXI_SYMMETRIC, Units.MILLIMETER)
renderer.create_circuit("stage_coil", CircuitType.SERIES, INITIAL_CURRENT)

# Defines problem geometry using geometry enums
domain = Geometry(
    shape=ShapeType.CIRCLE,
    center=(0, 0),
    radius=projectile_length * 4
)

coil = Geometry(
    shape=ShapeType.RECTANGLE,
    enclosed=True,
    points=[
        (coil_inner_radi, 0),
        (coil_outer_radi, 0),
        (coil_outer_radi, coil_length),
        (coil_inner_radi, coil_length)
    ]
)

projectile = Geometry(
    shape=ShapeType.RECTANGLE,
    enclosed=True,
    points=[
        (0, -projectile_length),
        (projectile_radi, -projectile_length),
        (projectile_radi, 0),
        (0, 0)
    ]
)

# Draws the problem geometry to the renderer
renderer.draw(projectile, projectile_material, PROJECTILE_GROUP)

# Estimates the number of turns within the cross section of the coil
turns = estimate_turns(
    coil_length, coil_inner_radi, coil_outer_radi,
    coil_wire_dia, coil_fill_factor
)
renderer.draw(
    coil, coil_material, COIL_GROUP, circuit="stage_coil",
    polarity=CurrentPolarity.FORWARD, turns=turns
)

# Defines outer domain and boundary
renderer.draw_domain_boundary(domain, boundary_type=BoundaryType.NEUMANN)
renderer.define_environment_region(BOUNDARY_GROUP, (50, 0), boundary_material)

# Loop variables
target_displacement = 2.5 * coil_length

loop_time = 0.0
flux = 0.0
current = INITIAL_CURRENT

inductance = 0.0
resistance = 0.0

velocity = 0.0
position = 0.0
switch = False

# Data collection for matplotlib
time_series = []
voltage_series = []
current_series = []
velocity_series = []

start_time = time.time()
while position < target_displacement:
    # Updates the display for the user
    elapsed = time.time() - start_time
    progress = position / target_displacement if position > 0 else 0
    msg = f"\r[Progress: {progress*100:6.2f}%] Elapsed {format_time(elapsed)}"
    sys.stdout.write(msg)
    sys.stdout.flush()

    # Calculates the values from the last frame
    result = static_simulation(
        renderer,
        FEMMagneticSolver,
        [
            "field_energy",
            "circuit_resistance",
            "circuit_flux_linkage",
            "force_stress_tensor"
        ],
        elements=[COIL_GROUP, PROJECTILE_GROUP],
        circuits="stage_coil"
    )

    # Extracts the values and calculates parameters
    dc_resistance = result["circuit_resistance"]["stage_coil"]
    stored_field_energy = sum(list(result["field_energy"].values()))
    frame_flux = result["circuit_flux_linkage"]["stage_coil"]
    force, theta = result["force_stress_tensor"][PROJECTILE_GROUP]

    inductance = calculate_inductance(stored_field_energy, current)
    delta_flux = frame_flux - flux
    flux = frame_flux

    # Calculates the current for the next frame
    current, voltage = rk_2nd_order_currents(
        loop_time, current, voltage, dc_resistance, inductance,
        delta_flux, TIME_STEP
    )
    current = clipping_current(current_limit, current)

    # Calculates magnetic and drag forces
    force = force * 1e6     # Scales FEM Newton output to mN
    theta = radians(theta)
    axial_force = force * sin(theta)

    drag = projectile_drag(
        FLUID_DENSITY, velocity, COEFFICIENT_DRAG, projectile_radi
    )
    net_force = (axial_force - drag)
    acceleration = net_force / projectile_mass

    # Solves DE's for velocity, position using euler methods
    velocity += acceleration * TIME_STEP
    dz = velocity * TIME_STEP
    position += dz

    # Moves the projectile element by the dz distance
    renderer.move_element(PROJECTILE_GROUP, dz, (pi / 2, 0, 0))
    renderer.change_circuit_current("stage_coil", current)
    loop_time += TIME_STEP

    # Switching mechanism
    if position >= (coil_length / 2.0) and switch is False:
        # Voltage spikes very negatively at switching
        voltage = -5 * voltage
        switch = True

    # Saving results for output
    time_series.append(loop_time)
    voltage_series.append(voltage)
    current_series.append(current)
    velocity_series.append(velocity)

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

# Velocity Vs Time plot
ax1.plot(time_series, velocity_series, color='blue', label='Velocity')
ax1.set_ylabel("velocity (mm/s)")
ax1.set_title("Projectile Velocity vs Time")
ax1.grid(True)
ax1.legend()

# Current Vs Time plot
ax2.plot(time_series, current_series, color='red', label='Current')
ax2.set_xlabel("time (s)")
ax2.set_ylabel("current (A)")
ax2.set_title("Coil Current vs Time")
ax2.grid(True)
ax2.legend()

# voltage Vs Time plot
ax3.plot(time_series, voltage_series, color='green', label='Voltage')
ax3.set_xlabel("time (s)")
ax3.set_ylabel("voltage (V)")
ax3.set_title("Coil Voltage vs Time")
ax3.grid(True)
ax3.legend()

plt.tight_layout()
plt.show()
