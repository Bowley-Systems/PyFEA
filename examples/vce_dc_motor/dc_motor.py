"""
Filename: dc_motor.py
Author: William Bowley
Version: 1.4
Date: 2025-09-15

Description:
    Runs a dc motor under quasi-transient
    approximation. To show lorentz force vectoring,
    flux change and faraday law of induction.

    NOTE:
    - Currently this doesn't function correctly.
"""

import matplotlib.pyplot as plt
from math import pi

from blueshark.domain.material_manager.manager import MaterialManager
from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver
from blueshark.simulate.static import static_simulation
from blueshark.domain.definitions import (
    CoordinateSystem, Units, CircuitType, ShapeType, Geometry,
    CurrentPolarity, BoundaryType
)

from physics import (
    calculate_inductance, induced_voltage, rk_2nd_current, angular_acceleration
)

# Simulation Constants (mm, s)
TEST_CURRENT = 1    # Used for calculating the inductance and resistance
TIME_STEP = 5e-3
BOUNDARY_MATERIAL = "air"
BOUNDARY_GROUP = 0
FILE_LOCATION = "examples/vce_dc_motor/dc_motor.fem"
depth = 40

# Circuit Parameters (amps)
voltage = 8

# Armature (mm)
coil_material = "Copper Wire"
coil_wire_dia = 0.3
coil_turns = 20
coil_mass = 0.0020
COIL_GROUP = 1

# Stator (magnets) (mm)
magnet_length = 20
magnet_height = 10
magnet_material = "NdFeB"
magnet_grade = "N52"
MAGNET_GROUP = 2

# Simulation setup (Material Manager & Renderer)
manager = MaterialManager()
boundary_material = manager.use_material(BOUNDARY_MATERIAL)
stator_material = manager.use_material(magnet_material, grade=magnet_grade)
armature_material = manager.use_material(
    coil_material, wire_diameter=coil_wire_dia
)

renderer = FEMMagneticRenderer(FILE_LOCATION)
renderer.setup(CoordinateSystem.PLANAR, Units.MILLIMETER, depth)
renderer.create_circuit("phase_coil", CircuitType.SERIES, TEST_CURRENT)

# Defines problem geometry using geometry enums
domain: Geometry = {
    "shape": ShapeType.CIRCLE, "center": (0, 0),
    "radius": 5 * magnet_length
}

# Motor windings
positive: Geometry = {
    "shape": ShapeType.CIRCLE,
    "center": (-1 / 2 * magnet_height, 0),
    "radius": 5 * coil_wire_dia / 2
}

negative: Geometry = {
    "shape": ShapeType.CIRCLE,
    "center": (1 / 2 * magnet_height, 0),
    "radius": 5 * coil_wire_dia / 2
}

# Motor magnets
left_magnet: Geometry = {
    "shape": ShapeType.RECTANGLE,
    "enclosed": True,
    "points": [
        (-2 * magnet_length, - 1 / 2 * magnet_height),
        (-1 * magnet_length, - 1 / 2 * magnet_height),
        (-1 * magnet_length, 1 / 2 * magnet_height),
        (-2 * magnet_length, 1 / 2 * magnet_height)
    ]
}

right_magnet: Geometry = {
    "shape": ShapeType.RECTANGLE,
    "enclosed": True,
    "points": [
        (magnet_length, - 1 / 2 * magnet_height),
        (magnet_length, 1 / 2 * magnet_height),
        (2 * magnet_length, 1 / 2 * magnet_height),
        (2 * magnet_length, - 1 / 2 * magnet_height)
    ]
}

# Draws the armature to the renderer
renderer.draw(
    positive, armature_material, COIL_GROUP, circuit="phase_coil",
    polarity=CurrentPolarity.FORWARD, turns=coil_turns
)

renderer.draw(
    negative, armature_material, COIL_GROUP, circuit="phase_coil",
    polarity=CurrentPolarity.REVERSE, turns=coil_turns
)

# Draws the left and right magnet to the renderer
renderer.draw(left_magnet, stator_material, MAGNET_GROUP)
renderer.draw(right_magnet, stator_material, MAGNET_GROUP)

# Defines outer domain and boundary
renderer.draw_domain_boundary(domain, boundary_type=BoundaryType.NEUMANN)

tag = (3 * magnet_length, 2 * magnet_height)
renderer.define_environment_region(BOUNDARY_GROUP, tag, boundary_material)


# Loop variables
armature_radius = magnet_length
target_time = 1
first_loop = True
resistance = 0.0
inductance = 0.0
last_flux = 0.0

time = 0.0
torque = 0.0
current = 0.0
theta = pi / 90     # Starts with 2 degree angle
angular_velocity = 0.0

# Data collection for matplotlib
time_series = []
theta_series = []
torque_series = []
flux_series = []
induced_series = []

while time < target_time:
    # Gets values for dc resistance and inductance
    # for the motor on first loop
    print(theta, time / target_time * 100)
    if first_loop:
        result = static_simulation(
            renderer,
            FEMMagneticSolver,
            ["field_energy", "circuit_resistance", "circuit_flux_linkage"],
            elements=COIL_GROUP,
            circuits="phase_coil"
        )

        # Extracts values from results and calculate parameters
        resistance = result["circuit_resistance"]["phase_coil"]
        stored_field_energy = result["field_energy"][COIL_GROUP]
        last_flux = result["circuit_flux_linkage"]["phase_coil"]
        inductance = calculate_inductance(stored_field_energy, TEST_CURRENT)

        renderer.rotate_element(COIL_GROUP, (0, 0, 0), (theta, 0, 0))
        first_loop = False

    # Solves mechanical DE's through explicit euler method
    acceleration = angular_acceleration(torque, coil_mass, armature_radius)
    angular_velocity += acceleration * TIME_STEP
    d_theta_rad = angular_velocity * TIME_STEP
    theta += d_theta_rad

    # Updates position and currents than solves problem
    renderer.change_circuit_current("phase_coil", current)
    renderer.rotate_element(COIL_GROUP, (0, 0, 0), (d_theta_rad, 0, 0))
    result = static_simulation(
        renderer,
        FEMMagneticSolver,
        ["torque_stress_tensor", "circuit_flux_linkage"],
        elements=COIL_GROUP,
        circuits="phase_coil"
    )

    # Extracts values from static frame
    torque = result["torque_stress_tensor"][COIL_GROUP]
    frame_flux = result["circuit_flux_linkage"]["phase_coil"]
    delta_flux = frame_flux - last_flux

    e_induced = induced_voltage(delta_flux, TIME_STEP)
    current = rk_2nd_current(
        time, current, e_induced, resistance, inductance, voltage, TIME_STEP
    )

    last_flux = frame_flux
    time += TIME_STEP

    time_series.append(time)
    theta_series.append(theta)
    torque_series.append(torque)
    flux_series.append(frame_flux)
    induced_series.append(current)

plt.figure(figsize=(10, 9))

# --- Plot 1: Torque vs. Angle ---
plt.subplot(3, 1, 1)
plt.plot(theta_series, torque_series, label="Net Torque", color="tab:blue")
plt.title("Net Torque vs. Angular Position (theta)")
plt.xlabel("Angle ($\theta$, rad)")
plt.ylabel("Torque (N·m)")
plt.grid(True)
plt.legend()

# --- Plot 2: Flux Linkage vs. Angle ---
plt.subplot(3, 1, 2)
plt.plot(
    theta_series, flux_series,
    label="Flux Linkage (Wb)", color="tab:green"
)
plt.title("Total Flux Linkage vs. Angular Position (theta)")
plt.xlabel("Angle (rad)")
plt.ylabel("Flux Linkage (Wb)")
plt.grid(True)
plt.legend()

# Plot 3: Induced Voltage (Back-EMF) vs. Angle
plt.subplot(3, 1, 3)
plt.plot(
    theta_series, induced_series,
    label="Induced Voltage ($E_b$)", color="tab:red"
)
plt.title("Induced Voltage (Back-EMF) vs. Angular Position (theta)")
plt.xlabel("Angle (rad)")
plt.ylabel("Voltage (V)")
plt.grid(True)
plt.legend()

# Adjust graphs to fit the figure area and shows them
plt.tight_layout()
plt.show()
