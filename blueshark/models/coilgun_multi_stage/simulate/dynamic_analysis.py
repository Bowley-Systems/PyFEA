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
from blueshark.domain.conversion.manager import conversion
from blueshark.domain.units import (
    Unit, SIBase, PrefixScale, AMPERE, KILOGRAM,
    NEWTON, SECOND, JOULE, METER_SECOND, METER
)

from blueshark.models.coilgun_multi_stage.modelling.coil import Coil
from blueshark.models.coilgun_multi_stage.main import MultiStageCoilGun
from blueshark.models.coilgun_multi_stage.modelling.physics import (
    format_time, projectile_drag
)

# Defines units
GRAM = KILOGRAM.with_prefix(SIBase.GRAM, PrefixScale.BASE)
MILLIMETER = METER.with_prefix(SIBase.METER, PrefixScale.MILLI)
MILLIMETER_SECOND = METER_SECOND.with_prefix(SIBase.METER, PrefixScale.MILLI)

MICRO_NEWTON = NEWTON.with_prefix(SIBase.GRAM, PrefixScale.BASE)\
                        .with_prefix(SIBase.METER, PrefixScale.MILLI)

NANO_JOULE = JOULE.with_prefix(SIBase.GRAM, PrefixScale.BASE)\
                    .with_prefix(SIBase.METER, PrefixScale.MILLI)


@dataclass
class DynamicResults:
    """ Holds the dynamic launch results """
    final_velocity: float       # final velocity of the projectile (m/s)
    input_output: float         # Output / Input Ratio
    average_power_loss: float   # Average Power loss (W)
    average_input_power: float  # Average Electrical input power (W)


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
    axes[0].set_ylabel("Position (m)", color="white")
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
    axes[2].set_ylabel("Velocity (m/s)", color="white")
    axes[2].set_title("Projectile Velocity vs Time", color="white")
    axes[2].tick_params(colors="white")

    fig.tight_layout(pad=2.0)
    plt.show()


def _calculate_mass(
    model: MultiStageCoilGun,
) -> tuple[float, Unit]:
    """
    Calculates the mass of the projectile for the launch
    - Units in parameter file is in g-mm-s
    """
    # Calculates the projectile volume
    height = model.load.projectile_axial_length
    volume_1 = math.pi * model.load.projectile_inner_radi ** 2 * height
    volume_2 = math.pi * model.load.projectile_outer_radi ** 2 * height
    total_volume = volume_2 - volume_1

    # Calculates the projectiles mass
    mass = total_volume * model.load.projectile_density
    return mass, GRAM


def launch_dynamic(
    model: MultiStageCoilGun,
    solver: BaseSolver,
    resistance: tuple[float, Unit],
    inductance: tuple[float, Unit],
    debugging: bool = True
) -> DynamicResults:

    # Creates the coil instances
    instances: list[Coil] = []
    for n in range(0, model.load.stages):
        instances.append(
            Coil(
                model,
                model.coil_origins[n],
                model.CIRCUITS[n],
                model.COILS[n],
                resistance[0],
                inductance[0]
            )
        )

    # Displacement goal, element list, mass & time step
    target_displacement = model.accelerator_length + model.coil_pitch

    elements = []
    elements.extend(model.COILS)
    elements.append(model.PROJECTILE)

    time_step = model.load.time_step
    projectile_mass, mass_unit = _calculate_mass(model)

    # Initial loop values
    currents, current_unit = None, AMPERE
    loop_time, _ = 0.0, SECOND
    force, force_unit = 0.0, MICRO_NEWTON
    velocity, velocity_unit = 0.0, MILLIMETER_SECOND

    # Front axial position of the projectile
    position = model.projectile_origin[1] + model.load.projectile_axial_length
    displacement, displacement_unit = 0.0, MILLIMETER

    electrical_energy, energy_unit = 0.0, NANO_JOULE
    mechanical_energy, energy_unit = 0.0, NANO_JOULE

    # Data collection for matplotlib / json
    time_series = []
    force_series = []
    velocity_series = []
    position_series = []

    prev_msg_len = 0
    start_time = time.time()
    while displacement < target_displacement:
        # Updates the display for the user
        elapsed = time.time() - start_time
        progress = displacement / target_displacement
        if progress > 1e-6:
            eta = (elapsed / progress) - elapsed
        else:
            eta = float('inf')

        eta = eta if progress > 0 else 0
        msg = (
            f"\r[Progress: {progress*100:6.2f}%]"
            f" Elapsed {format_time(elapsed)} |"
            f" ETA: {format_time(eta) if eta != float('inf') else eta} |"
            f" Net force: {force:6.2f} {force_unit} |"
            f" Currents: {currents} {current_unit} |"
            f" Position: {displacement:6.2f} {displacement_unit}"
        )

        # Pad just enough spaces to clear leftovers
        clear_msg = msg + " " * max(prev_msg_len - len(msg), 0)
        sys.stdout.write(clear_msg)
        sys.stdout.flush()

        prev_msg_len = len(msg)

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
            value, _ = power_results[circuit]
            power += abs(value)

        # Calculates magnetic and drag forces and updates trackers
        force, angle, unit = result["force_stress_tensor"][model.PROJECTILE]
        force, _ = conversion(force, unit, force_unit)

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
            flux, _ = result["circuit_flux_linkage"][circuit]
            resistance, _ = result["circuit_resistance"][circuit]

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
        graph_force, _ = conversion(net_force, force_unit, NEWTON)
        graph_velocity, _ = conversion(velocity, velocity_unit, METER_SECOND)
        graph_position, _ = conversion(position, MILLIMETER, METER)

        time_series.append(loop_time)
        force_series.append(graph_force)
        velocity_series.append(graph_velocity)
        position_series.append(graph_position)

    if debugging:
        _debug_plotting(
            time_series, position_series, force_series, velocity_series
        )

    # Converting nJ to J
    mechanical_energy, _ = conversion(mechanical_energy, energy_unit, JOULE)
    velocity, _ = conversion(velocity, MILLIMETER_SECOND, METER_SECOND)
    projectile_mass, _ = conversion(projectile_mass, mass_unit, KILOGRAM)

    # Calculates outputs based on quasi-transient loop outputs
    ke = 1/2 * projectile_mass * velocity ** 2
    ratio = ke / electrical_energy if electrical_energy else 0
    ratio = 0 if ratio < 0 or ratio > 1 else ratio

    losses = (
        (electrical_energy - ke) / loop_time
        if loop_time > 0 else 0
    )

    # New calculation for average total power (Power = Energy / Time)
    average_input_power = electrical_energy / loop_time if loop_time > 0 else 0

    results = DynamicResults(
        velocity,
        ratio,
        losses,                 # Average Power Loss (W)
        average_input_power     # Average Electrical Input Power (W)
    )

    return results
