"""
Filename: dynamic_analysis.py
Author: William Bowley
Version: 0.1
Date: 2025-10-09

Description:
    Performs a dynamic analysis of the
    launch conditions of the proposed
    linear motor design and visualizes results.
"""

import logging
import math
import matplotlib.pyplot as plt
import time as timelib
import sys

from typing import Sequence
from dataclasses import dataclass

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.renderer.femm.magnetic.renderer import FEMMagneticRenderer
from blueshark.simulate.static import static_simulation
from blueshark.solver.femm.magnetic.solver import FEMMagneticSolver
from blueshark.domain.physics.ripple import ripple_percent

from blueshark.models.tubular_linear_motor.physics.physics import (
    Currents,
    Voltages,
    rk_2nd_order_currents,
    inverse_park_transform,
    inverse_clarke_transform,
    clark_transform,
    park_transform,
    electrical_angle,
    instantaneous_rms,
    time_averaged_rms
)


@dataclass
class DynamicResults:
    """ Holds the dynamic results """
    input_output: float     # Output / Input Ratio
    average_force: float    # Average force
    force_I_rms: float      # N / A
    force_ripple: float     # % Peak-to-Peak
    displacement: float     # Displacement to reach target (m)
    power_loss: float       # Power loss (W)
    total_power: float      # Electrical input power (W)


@dataclass
class _FrameResults:
    """ Holds the magneto-static frame results """
    flux_linkage: tuple[float, float, float]    # Webers
    lorentz_force: tuple[float, float]  # N & angle (radians)
    power: float                        # Total instantaneous power (W)


def _magneto_static_frame(
    renderer: FEMMagneticRenderer,
    groups: int,
    phases: list[str],
    displacement: tuple[float, float],
    currents: tuple[float, float, float],
) -> _FrameResults:
    """ Returns magneto static results for a given instant in time. """
    try:
        angles = [displacement[1], 0, 0]
        renderer.move_element(groups, displacement[0], angles)

        for index, phase in enumerate(phases):
            renderer.change_circuit_current(phase, currents[index])

        # Clear renderer state
        renderer.clean_up()

        results = static_simulation(
            renderer,
            FEMMagneticSolver,
            ["circuit_flux_linkage", "circuit_power", "force_lorentz"],
            elements=groups,
            circuits=phases
        )

        # Extraction of values and calculations
        linkage = list(results["circuit_flux_linkage"].values())
        power = sum(list(results["circuit_power"].values()))

        force_data = results["force_lorentz"][groups]
        force = force_data[0]
        angle = math.radians(force_data[1])

        return _FrameResults(linkage, (force, angle), power)

    except Exception as e:
        msg = f"Magneto-static frame failed for {renderer}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def _clipping_current(
    I_limit: float,
    currents: Currents
) -> tuple[bool, Currents]:
    """ Artificially clips the current to the maximum allowed by the supply """
    i_d = currents.d
    i_q = currents.q

    state = False
    I_total = math.sqrt(i_d**2 + i_q**2)

    if I_total > I_limit:
        # Calculates a scaling factor
        state = True
        scale_factor = I_limit / I_total

        i_d = i_d * scale_factor
        i_q = i_q * scale_factor

    return state, Currents(i_d, i_q)


def _format_time(seconds: float) -> str:
    """ Converts seconds into HH:MM:SS. """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _time_progress(
    step, total_steps, start_time, interval=1
) -> None:
    """ Displays progress updates with elapsed time and ETA in hh:mm:ss """
    if step % interval != 0 and step != total_steps:
        return

    elapsed = timelib.time() - start_time
    progress = step / total_steps if total_steps > 0 else 0
    eta = (elapsed / progress - elapsed) if progress > 0 else 0

    msg = (
        f"\r[Progress: {progress*100:6.2f}%] "
        f"Elapsed: {_format_time(elapsed)} | "
        f"ETA: {_format_time(eta)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()

    if step == total_steps:
        print(f"\nSimulation complete in {_format_time(elapsed)}")


def debug_plotting(
    time_series: Sequence[float],
    pa_series: Sequence[float],
    pb_series: Sequence[float],
    pc_series: Sequence[float],
    force_series: Sequence[float],
    velocity_series: Sequence[float],
) -> None:
    """ Plot dynamic simulation results for debugging purposes. """

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # --- Three-phase currents ---
    axes[0].plot(time_series, pa_series, label="Phase A", color="#8B4513",
                 linewidth=2)
    axes[0].plot(time_series, pb_series, label="Phase B", color="#FF8C00",
                 linewidth=2)
    axes[0].plot(time_series, pc_series, label="Phase C", color="#3CB371",
                 linewidth=2)
    axes[0].set_title("Three-Phase Currents vs Time", fontsize=14)
    axes[0].set_ylabel("Current (A)")
    axes[0].legend(loc="upper right", ncol=3, frameon=True)
    axes[0].tick_params(axis="both", which="major", labelsize=10)

    # --- Force vs Time ---
    axes[1].plot(time_series, force_series, label="Lorentz Force (N)",
                 color="#DC143C", linewidth=2)
    axes[1].set_title("Force vs Time", fontsize=14)
    axes[1].set_ylabel("Force (N)")
    axes[1].legend(loc="upper right", frameon=True)
    axes[1].tick_params(axis="both", which="major", labelsize=10)

    # --- Velocity vs Time ---
    axes[2].plot(time_series, velocity_series, label="Velocity (m/s)",
                 color="#1E90FF", linewidth=2)
    axes[2].set_title("Velocity vs Time", fontsize=14)
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Velocity (m/s)")
    axes[2].legend(loc="upper left", frameon=True)
    axes[2].tick_params(axis="both", which="major", labelsize=10)

    # Adjust layout
    fig.tight_layout(pad=2.0)
    plt.show()


def run_dynamic(
    motor: TubularLinearMotor,
    resistance: float,
    inductance: float,
    flux: tuple[float, float, float],
    debugging: bool = False
) -> DynamicResults:
    """
    Performs a launch of the proposed motor design converts all
    FEMM outputs to (mm) to match the units in the motor.yaml.

    NOTE:
    - Remember this function converts to (mm) without considering
      your changes to FEMM or the motor.yaml file.
    """
    # 1/25 of electrical step seemed to work as a rule.*
    variant = motor.load
    time_step = inductance / (5 * resistance)
    maximum_steps = variant.de_maximum_steps

    # Initial loop values
    currents = Currents(0.0, 0.0)
    current_limit = 2.5
    voltages = Voltages(0.0, variant.supply_voltage)
    flux = list(flux)     # Flux (a, b, c)

    time = 0.0
    I_a, I_b, I_c = 0.0, 0.0, 0.0

    angle = 0.0     # Electrical angle of the motor
    axial_force, axial_angle = 0.0, 90   # linear displacement from origin
    velocity = 0.0
    displacement = 0.0
    electrical_energy = 0.0
    mechanical_energy = 0.0
    force_data = [axial_force]  # Needed for ripple analysis
    ripple_force_data = []
    current_rms = [instantaneous_rms(currents)]

    # Data collection for plotting during debugging
    if debugging:
        time_data = [time]
        pa_data = [I_a]
        pb_data = [I_b]
        pc_data = [I_c]

        velocity_data = [velocity]

    # Times for the user
    start_time = timelib.time()
    for step in range(maximum_steps + 1):
        # Converting target speed from mms^-1 to ms^-1
        if velocity >= variant.target_speed / 1000:
            break

        # Calculates the change in q_flux for the frame
        angle = electrical_angle(displacement * 1000, motor.pole_pitch)
        flux_alpha, flux_beta = clark_transform(*flux)
        d_flux, q_flux = park_transform(flux_alpha, flux_beta, angle)

        # Each step needs to calculate the q_flux before so (n-1),
        # hence for n, we skip the first step
        if step > 0:
            # Calculates the phase A,B,C currents from i_d, i_q frames
            state, currents = _clipping_current(current_limit, currents)
            I_alpha, I_beta = inverse_park_transform(currents, angle)
            I_a, I_b, I_c = inverse_clarke_transform(I_alpha, I_beta)

            # Solves mechanical DE's through explicit euler method
            acceleration = axial_force / (variant.mass / 1000)
            delta = velocity * time_step
            displacement += delta

            # Solves velocity for the next frame
            velocity += acceleration * time_step

            results = _magneto_static_frame(
                motor.renderer,
                motor.SLOT,
                motor.PHASES,
                (delta * 1000, axial_angle),  # Converts meters to mm
                (I_a, I_b, I_c)
            )
            if results is None:
                # Incases the step fails to simulate correctly
                return None

            # Extracts values from static frame
            power = results.power
            axial_force, axial_angle = results.lorentz_force
            frame_flux = list(results.flux_linkage)

            # Axial direction is vertical whereas radial is horizontal
            axial_force = axial_force * math.sin(axial_angle)

            # Calculates the current flux linkage for the frame
            flux_alpha, flux_beta = clark_transform(*frame_flux)
            d_flux_frame, q_flux_frame = park_transform(
                flux_alpha, flux_beta, angle
            )

            d_delta_flux = d_flux_frame - d_flux
            q_delta_flux = q_flux_frame - q_flux
            # Solves the i_d and i_q DE using Runge-Kutta / Ralston's method
            currents = rk_2nd_order_currents(
                time,
                currents,
                voltages,
                resistance,
                inductance,
                (d_delta_flux, q_delta_flux),
                time_step
            )

            flux = frame_flux

            # Energy tracking
            mechanical_energy += axial_force * velocity * time_step
            electrical_energy += power * time_step
            time += time_step

            # Collects data only during steady state current conditions
            if state:
                ripple_force_data.append(axial_force)
                current_rms.append(instantaneous_rms(currents))

            # Collects data for graphing during debugging
            if debugging:
                _time_progress(step, maximum_steps, start_time)
                time_data.append(time)
                pa_data.append(I_a)
                pb_data.append(I_b)
                pc_data.append(I_c)
                force_data.append(axial_force)
                velocity_data.append(velocity)

    if velocity >= variant.target_speed:
        return None

    if debugging:
        debug_plotting(
            time_data, pa_data, pb_data, pc_data, force_data, velocity_data
        )

    # Calculates outputs based on quasi-transient loop outputs
    av_rms_current = time_averaged_rms(current_rms)
    force_ripple = ripple_percent(ripple_force_data)

    av_force = sum(i for i in ripple_force_data) / len(ripple_force_data)
    force_I_rms = av_force / av_rms_current

    ratio = mechanical_energy / electrical_energy if electrical_energy else 0
    losses = (electrical_energy - mechanical_energy) / time if time > 0 else 0

    return DynamicResults(
        average_force=av_force,
        input_output=ratio,
        force_I_rms=force_I_rms,
        force_ripple=force_ripple,
        displacement=displacement,
        power_loss=losses,
        total_power=(electrical_energy / time) if time > 0 else 0.0
    )
