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
    estimate_turns, calculate_inductance,
    inst_current_charge, inst_current_discharge,
    projectile_drag, clipping_current
)

# Simulation CONSTANTS (mm, g, s)
INITIAL_CURRENT = 1e-4  # Needed for the inductance calculations
FLUID_DENSITY = 1.225e-6
COEFFICIENT_DRAG = 0.82
TIME_STEP = 5e-4
BOUNDARY_MATERIAL = "air"
BOUNDARY_GROUP = 0
FILE_LOCATION = "examples/simple_coilgun/coilgun.fem"

# Circuit Parameters (volts, amp)
voltage = 12            # Supply voltage
current_limit = 40      # Maximum current before clipping

# Coil Parameters (mm)
coil_length = 50
coil_inner_radi = 6.25
coil_outer_radi = 17.5
coil_material = "Copper Wire"
coil_wire_dia = 1.25
coil_fill_factor = 0.65
COIL_GROUP = 1

# Projectile Parameters (mm, g)
projectile_radi = 4
projectile_length = 50
projectile_material = "Pure Iron"
projectile_mass = 20
PROJECTILE_GROUP = 2

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
domain: Geometry = {
    "shape": ShapeType.CIRCLE, "center": (0, 0),
    "radius": projectile_length * 4
}

coil: Geometry = {
    "shape": ShapeType.RECTANGLE,
    "enclosed": True,
    "points": [
        (coil_inner_radi, 0),
        (coil_outer_radi, 0),
        (coil_outer_radi, coil_length),
        (coil_inner_radi, coil_length)
    ]
}

projectile: Geometry = {
    "shape": ShapeType.RECTANGLE,
    "enclosed": True,
    "points": [
        (0, -projectile_length),
        (projectile_radi, -projectile_length),
        (projectile_radi, 0),
        (0, 0)
    ]
}

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
target_displacement = 2 * coil_length

time = 0.0
time_offset = 0.0
frame_current = INITIAL_CURRENT
decay_current = 0.0

velocity = 0.0
position = 0.0

switch_off = False

# Data collection for matplotlib
time_series = []
current_series = []
velocity_series = []
while position < target_displacement:
    # Given the need for current within the system to appox. inductance
    # System has to time step before to ensure the I≠0 at t=0.
    time += TIME_STEP

    percentage = position / target_displacement * 100
    msg = f"Simulation is {percentage:3f} % finished, time = {time:4f}s"
    print(msg)

    # Builds the frame and solves the problem for inductance and resistance
    result = static_simulation(
        renderer,
        FEMMagneticSolver,
        ["field_energy", "circuit_resistance"],
        elements=COIL_GROUP,
        circuits="stage_coil"
    )

    dc_resistance = result["circuit_resistance"]["stage_coil"]
    stored_field_energy = result["field_energy"][COIL_GROUP]
    inductance = calculate_inductance(stored_field_energy, frame_current)

    # Exponential increase during switch on vs Exponential decay during off
    if switch_off:
        # Exponential decay of the current and len's law
        frame_current = inst_current_discharge(
            time, time_offset, decay_current, dc_resistance, inductance
        )
    else:
        frame_current = inst_current_charge(
            time, dc_resistance, inductance, voltage
        )

    # Sets the coil_stage current defined by the charge/discharge model
    frame_current = clipping_current(current_limit, frame_current)
    renderer.change_circuit_current("stage_coil", frame_current)

    # Builds the frame and solves specifically for the force stress tensor
    result = static_simulation(
        renderer,
        FEMMagneticSolver,
        ["force_stress_tensor"],
        elements=PROJECTILE_GROUP
    )

    # Calculates magnetic and drag forces
    force, theta = result["force_stress_tensor"][PROJECTILE_GROUP]
    force = force * 1e6    # Scales FEM Newton output to mN
    theta = radians(theta)  # Converts degrees from FEM to radians
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

    # Switching mechanism
    if position >= (coil_length / 2.0) and not switch_off:
        time_offset = time
        switch_off = True

    # Sets the initial current for the exponential decay stage
    if switch_off is False:
        decay_current = frame_current

    # Saving results for output
    time_series.append(time)
    current_series.append(frame_current)
    velocity_series.append(velocity)


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

# Velocity plot
ax1.plot(time_series, velocity_series, color='blue', label='Velocity')
ax1.set_ylabel("velocity (mm/s)")
ax1.set_title("Projectile Velocity vs Time")
ax1.grid(True)
ax1.legend()

# Current plot
ax2.plot(time_series, current_series, color='red', label='Current')
ax2.set_xlabel("time (s)")
ax2.set_ylabel("current (A)")
ax2.set_title("Coil Current vs Time")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()
