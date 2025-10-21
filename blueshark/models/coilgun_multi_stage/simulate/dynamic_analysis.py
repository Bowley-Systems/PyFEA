"""
Filename: dynamic_analysis.py
Author: William Bowley
Version: 0.1
Date: 2025-10-09

Description:
    Performs a dynamic launch of the proposed
    coilgun design and visualizes results.
"""

import math
import time
import sys
import matplotlib.pyplot as plt
from typing import Sequence

from dataclasses import dataclass

from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.simulate.static import static_simulation

from blueshark.models.coilgun_multi_stage.physics.coil import coil
from blueshark.models.coilgun_multi_stage.main import MultiStageCoilGun
from blueshark.models.coilgun_multi_stage.physics.physics import (
    format_time, projectile_drag
)


@dataclass
class DynamicResults:
    """ Holds the dynamic launch results """
    final_velocity: float       # final velocity of the projectile (mms^-1)
    input_output: float         # Output / Input Ratio
    power_loss: float           # Power loss (W)
    total_power: float          # Electrical input power (W)


def _debug_plotting(
    time_series: Sequence[float],
    position_series: Sequence[float],
    force_series: Sequence[float],
    velocity_series: Sequence[float]
) -> None:
    """Plots the dynamic simulation results for debugging."""

    plt.style.use("dark_background")
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Set window title
    fig.canvas.manager.set_window_title("Coilgun Dynamic Simulation Results")

    # Position vs Time
    axes[0].plot(time_series, position_series, color="#00BFFF", linewidth=2)
    axes[0].set_ylabel("Position (mm)", color="white")
    axes[0].set_title("Projectile Position vs Time", color="white")
    axes[0].tick_params(colors="white")

    # Force vs Time
    axes[1].plot(time_series, force_series, color="#FF4500", linewidth=2)
    axes[1].set_ylabel("Force (N)", color="white")
    axes[1].set_title("Projectile Force vs Time", color="white")
    axes[1].tick_params(colors="white")

    # Velocity vs Time
    axes[2].plot(time_series, velocity_series, color="#7CFC00", linewidth=2)
    axes[2].set_xlabel("Time (s)", color="white")
    axes[2].set_ylabel("Velocity (mm/s)", color="white")
    axes[2].set_title("Projectile Velocity vs Time", color="white")
    axes[2].tick_params(colors="white")

    fig.tight_layout(pad=2.0)
    plt.show()


def _calculate_mass(
    model: MultiStageCoilGun,
) -> float:
    """ Calculates the mass of the projectile for the launch """

    # Calculates the projectile volume
    height = model.load.projectile_axial_length
    volume_1 = math.pi * model.load.projectile_inner_radi ** 2 * height
    volume_2 = math.pi * model.load.projectile_outer_radi ** 2 * height
    total_volume = volume_2 - volume_1

    # Calculates the projectiles mass
    mass = total_volume * model.load.projectile_density
    return mass


def launch_dynamic(
    model: MultiStageCoilGun,
    solver: BaseSolver,
    resistance: float,
    inductance: float,
    debugging: bool = False
) -> DynamicResults:

    # Creates the coil instances
    instances: list[coil] = []
    for n in range(0, model.load.stages):
        instances.append(
            coil(
                model,
                model.coil_origins[n],
                model.CIRCUITS[n],
                model.COILS[n],
                resistance,
                inductance
            )
        )

    # Displacement goal, element list, mass & time step
    target_displacement = model.accelerator_length + model.coil_pitch
    target_displacement = target_displacement

    elements = []
    elements.extend(model.COILS)
    elements.append(model.PROJECTILE)

    time_step = model.load.time_step
    projectile_mass = _calculate_mass(model)

    # Initial loop values
    currents = None
    loop_time = 0.0
    force = 0.0
    velocity = 0.0

    # Front axial position of the projectile
    position = model.projectile_origin[1] + model.load.projectile_axial_length
    displacement = 0.0

    electrical_energy = 0.0
    mechanical_energy = 0.0

    # Data collection for matplotlib / json
    time_series = []
    force_series = []
    velocity_series = []
    position_series = []

    start_time = time.time()
    while displacement < target_displacement:
        # Updates the display for the user
        elapsed = time.time() - start_time
        progress = (
            displacement / target_displacement if displacement > 0 else 0
        )
        eta = (elapsed / progress - elapsed) if progress > 0 else 0
        msg = (
            f"\r[Progress: {progress*100:6.2f}%]"
            f" Elapsed {format_time(elapsed)} | ETA: {format_time(eta)} |"
            f" Net force: {force:6.2f} uN | Currents: {currents} A |"
            f" Position: {position:6.2f} mm"
        )
        sys.stdout.write(msg)
        sys.stdout.flush()

        # Calculates the values from the last frame
        result = static_simulation(
            model.renderer,
            solver,
            [
                "circuit_power",
                "circuit_flux_linkage",
                "circuit_resistance",
                "force_stress_tensor"
            ],
            elements=elements,
            circuits=model.CIRCUITS
        )
        # Calculates power usage
        power = 0.0
        power_results = result["circuit_power"]
        for circuit in model.CIRCUITS:
            power += abs(power_results[circuit])

        # Calculates magnetic and drag forces and updates trackers
        force, angle = result["force_stress_tensor"][model.PROJECTILE]
        force = force * 1e6     # Scales FEM newton output to g * mm * s^-2

        angle = math.radians(angle)
        magnetic_force = force * math.sin(angle)    # Axially aligned force

        drag_force = projectile_drag(
            velocity,
            model.load.atmospheric_density,
            model.load.projectile_co_drag,
            model.load.projectile_outer_radi
        )

        net_force = (magnetic_force + drag_force)
        acceleration = net_force / projectile_mass
        mechanical_energy += net_force * velocity * time_step
        electrical_energy += power * time_step

        force = net_force

        # Solves DE's for velocity, position using euler methods
        velocity += acceleration * time_step
        dz = velocity * time_step
        position += dz
        displacement += dz

        # Update coils
        currents = []
        for instant in instances:
            circuit = instant.circuit
            flux = result["circuit_flux_linkage"][circuit]
            resistance = result["circuit_resistance"][circuit]

            current = instant.update(position, resistance, flux)
            currents.append(current)

        # Updates current & position
        renderer: MagneticRenderer = model.renderer
        renderer.move_element(model.PROJECTILE, dz, (math.pi / 2, 0, 0))

        for index, current in enumerate(currents):
            renderer.change_circuit_current(model.CIRCUITS[index], current)

        # Updates global time
        loop_time += time_step

        # Saving frame results (Next frame)
        time_series.append(loop_time)
        force_series.append(net_force / 1e6)
        velocity_series.append(velocity)
        position_series.append(position)

    if debugging:
        _debug_plotting(
            time_series, position_series, force_series, velocity_series
        )

    # Calculates outputs based on quasi-transient loop outputs
    ratio = mechanical_energy / electrical_energy if electrical_energy else 0
    losses = (
        (electrical_energy - mechanical_energy) / loop_time
        if loop_time > 0 else 0
    )

    results = DynamicResults(
        velocity,
        ratio,
        losses,
        electrical_energy
    )

    return results
