"""
Filename: dynamic_analysis.py
Author: William Bowley
Version: 1.0

Description:
    Performs a Quasi-transient Electro-Magneto-Mechanical
    analysis for the tubular synchronous linear motor from
    origin to a target position and visualizes results

    NOTE: ITS QUITE A MESSY; Will refactor  
"""

import logging
import time
import sys
import matplotlib.pyplot as plt

from typing import Sequence
from math import sin, radians
from dataclasses import dataclass

from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.simulate.static import static_simulation
from blueshark.domain.conversion.manager import conversion
from blueshark.domain.units import (
    Unit, SIBase, PrefixScale, AMPERE, KILOGRAM,
    NEWTON, SECOND, JOULE, METER_SECOND, METER, WATT, WEBER, VOLT
)

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.models.tubular_linear_motor.modelling.controller import (
    CascadedController
)
from blueshark.models.tubular_linear_motor.modelling.physics import (
    Currents, Voltages, format_time, electrical_angle, clark_transform,
    park_transform, inverse_clarke_transform, inverse_park_transform,
    rk_2nd_order_currents
)

# Defines units
GRAM = KILOGRAM.with_prefix(SIBase.GRAM, PrefixScale.BASE)
MILLIMETER = METER.with_prefix(SIBase.METER, PrefixScale.MILLI)
MILLIMETER_SECOND = METER_SECOND.with_prefix(SIBase.METER, PrefixScale.MILLI)

MICRO_NEWTON = NEWTON.with_prefix(SIBase.GRAM, PrefixScale.BASE)\
                        .with_prefix(SIBase.METER, PrefixScale.MILLI)

NANO_JOULE = JOULE.with_prefix(SIBase.GRAM, PrefixScale.BASE)\
                    .with_prefix(SIBase.METER, PrefixScale.MILLI)

NANO_WATT = WATT.with_prefix(SIBase.GRAM, PrefixScale.BASE)\
                    .with_prefix(SIBase.METER, PrefixScale.MILLI)


@dataclass
class SimulationResults:
    """ Holds the simulation results """
    efficiency: tuple[float, Unit]      # % Input / Output
    average_force: tuple[float, Unit]
    ripple_force: tuple[float, Unit]    # % Peak-to-Peak
    average_power_loss: tuple[float, Unit]
    average_input_power: tuple[float, Unit]


@dataclass
class _FrameResults:
    """ Holds the magneto-static frame results """
    flux_linkage: tuple[tuple[float, Unit]]
    lorentz_force: tuple[float, float, Unit]    # Force, Angle
    power: tuple[float, Unit]


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


def _magneto_static_frame(
    model: TubularLinearMotor,
    solver: BaseSolver,
    displacement: tuple[float, float, Unit],
    currents: tuple[tuple[float, Unit]]
) -> _FrameResults:
    """ Returns magneto static results for a given instant """
    try:
        displacement, angle, unit = displacement
        displacement, _ = conversion(displacement, unit, model.unit)
        angles = [angle, 0, 0]  # Framework requirement

        renderer: MagneticRenderer = model.renderer

        # Changes phase currents & moves armature
        renderer.move_element(model.SLOT, displacement, angles)
        for index, phase in enumerate(model.PHASES):
            current, unit = currents[index]
            current, _ = conversion(current, unit, AMPERE)
            renderer.change_circuit_current(phase, current)

        # renderer.clean_up()     # Clears renderer state
        results = static_simulation(
            renderer,
            solver,
            ["circuit_flux_linkage", "circuit_power", "force_lorentz"],
            elements=model.SLOT,
            circuits=model.PHASES
        )

        # Extraction & Conversion
        force, angle, unit = results["force_lorentz"][model.SLOT]
        force = conversion(force, unit, MICRO_NEWTON)   # (force, unit)

        linkage = []
        flux_linkage = results["circuit_flux_linkage"]
        for phase in model.PHASES:
            flux, unit = flux_linkage[phase]
            flux, unit = conversion(flux, unit, WEBER)
            linkage.extend((flux, unit))

        total_power = 0
        circuit_power = results["circuit_power"]
        for phase in model.PHASES:
            power, unit = circuit_power[phase]
            power, _ = conversion(power, unit, NANO_WATT)
            total_power += abs(power)

        return _FrameResults(linkage, force, (total_power, NANO_WATT))

    except Exception as e:
        msg = f"Magneto-static frame failed for {renderer}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def dynamic_ptp(
    model: TubularLinearMotor,
    solver: BaseSolver,
    target_position: tuple[float, Unit],
    resistance: tuple[float, Unit],
    inductance: tuple[float, Unit],
    phase_shift: tuple[float, Unit],
    force_constant: tuple[float, Unit],
    magnet_flux: tuple[tuple[float, Unit]],
    debugging: bool = True
) -> SimulationResults:
    """ Performs a PD-PI controlled point to point analysis of the TLSM """
    inductance, _ = inductance
    resistance, _ = resistance
    time_step = inductance / (10 * resistance)
    system_mass = model.load.mass   # Temp. Assumes load = motor mass
    controller = CascadedController(
        model, time_step, system_mass, force_constant, resistance, inductance
    )

    # Loop variables
    currents = Currents(0.0, 0.0)
    voltages = Voltages(0.0, 0.0)
    flux = []
    for phase in magnet_flux:
        phase_flux, unit = phase
        phase_flux, _ = conversion(phase_flux, unit, WEBER)
        flux.append(phase_flux)
    phase_shift, unit = phase_shift

    loop_time, _ = 0.0, SECOND
    I_a, I_b, I_c = (0.0, AMPERE), (0.0, AMPERE), (0.0, AMPERE)
    force, force_unit = 0.0, MICRO_NEWTON
    force_angle = 90
    velocity, _ = 0.0, MILLIMETER_SECOND
    displacement, displacement_unit = 0.0, MILLIMETER

    target, target_unit = target_position
    target, target_unit = conversion(target, target_unit, displacement_unit)

    electrical_energy, energy_unit = 0.0, NANO_JOULE
    mechanical_energy, energy_unit = 0.0, NANO_JOULE

    # Data collection for matplotlib / json
    time_series = []
    pa_data = []
    pb_data = []
    pc_data = []
    force_series = []
    velocity_series = []
    position_series = []

    first_loop = True
    prev_msg_len = 0
    start_time = time.time()
    while abs(displacement - target) > 1e-4:
        # Updates the display for the user
        elapsed = time.time() - start_time
        progress = displacement / target
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
            f" Currents: {Currents} {AMPERE}|"
            f" Position: {displacement:6.2f} {displacement_unit}"
        )

        # Pad just enough spaces to clear leftovers
        clear_msg = msg + " " * max(prev_msg_len - len(msg), 0)
        sys.stdout.write(clear_msg)
        sys.stdout.flush()

        prev_msg_len = len(msg)

        angle = electrical_angle(displacement, model.pole_pitch) + phase_shift
        flux_alpha, flux_beta = clark_transform(*flux)
        d_flux, q_flux = park_transform(flux_alpha, flux_beta, angle)

        # Each step needs to calculate the q_flux before so (n-1),
        # hence for n, we skip the first step
        if not first_loop:
            I_alpha, I_beta = inverse_park_transform(currents, angle)
            I_a, I_b, I_c = inverse_clarke_transform(I_alpha, I_beta)

            # Solves mechanical DE's through explicit euler method
            acceleration = force / system_mass
            delta = velocity * time_step
            displacement += delta

            # Solves velocity for the next frame
            velocity += acceleration * time_step

            results = _magneto_static_frame(
                model, solver, (displacement, force_angle, MILLIMETER),
                ((I_a, AMPERE), (I_b, AMPERE), (I_c, AMPERE))
            )

            # Extracts values from static frame
            r_power, r_unit = results.power
            power, _ = conversion(r_power, r_unit, NANO_WATT)
            r_force, force_angle, r_unit = results.lorentz_force
            force, _ = conversion(r_force, r_unit, force_unit)
            frame_flux = []
            r_flux = list(results.flux_linkage)
            for phase in r_flux:
                p_flux, unit = phase
                p_flux, _ = conversion(p_flux, unit, WEBER)
                frame_flux.extend(p_flux)

            # Tracks mechanical and electrical
            force = force * sin(radians(force_angle))        # Axial force
            mechanical_energy += force * velocity * time_step
            electrical_energy += power * time_step

            # Calculates the current flux linkage for the fra
            flux_alpha, flux_beta = clark_transform(*frame_flux)
            d_flux_frame, q_flux_frame = park_transform(
                flux_alpha, flux_beta, angle
            )

            d_delta_flux = d_flux_frame - d_flux
            q_delta_flux = q_flux_frame - q_flux

            # Updates the system voltage via the pd-pi controller
            q_voltage, unit = controller.step(
                displacement, velocity, (currents.q, AMPERE)
            )
            q_voltage, _ = conversion(q_voltage, unit, VOLT)
            voltages.q = q_voltage

            currents = rk_2nd_order_currents(
                loop_time,
                currents,
                voltages,
                resistance[0],
                inductance[0],
                (d_delta_flux, q_delta_flux),
                time_step
            )

            flux = frame_flux
            loop_time += time_step

            if debugging:
                time_series.append(loop_time)
                pa_data.append(I_a)
                pb_data.append(I_b)
                pc_data.append(I_c)
                position_series.append(displacement)
                force_series.append(force)
                velocity_series.append(velocity)

    if debugging:
        _debug_plotting(
            time_series, position_series, force_series, velocity_series
        )

    mechanical_energy, _ = conversion(mechanical_energy, energy_unit, JOULE)
    electrical_energy, _ = conversion(electrical_energy, energy_unit, JOULE)
    velocity, _ = conversion(velocity, MILLIMETER_SECOND, METER_SECOND)

    # Calculates outputs based on quasi-transient loop outputs
    ratio = mechanical_energy / electrical_energy if electrical_energy else 0
    ratio = 0 if ratio < 0 or ratio > 1 else ratio

    losses = (
        (electrical_energy - mechanical_energy) / loop_time
        if loop_time > 0 else 0
    )

    # New calculation for average total power (Power = Energy / Time)
    input_power = electrical_energy / loop_time if loop_time > 0 else 0

    return SimulationResults(ratio, 0, 0, losses, input_power)
