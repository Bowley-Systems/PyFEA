"""
Filename: physics.py
Author: William Bowley
Version: 0.2
Date: 2025-10-09

Description:
    Contains the physical equations (DEs, formulas)
    used in static and dynamic analysis for FOC
    and general electromechanical modeling.
"""

from math import cos, sin, sqrt, pi, atan
from dataclasses import dataclass


@dataclass
class Currents:
    """
    Holds the d-q frame currents
    """
    d: float
    q: float


@dataclass
class Voltages:
    """
    Holds the d-q frame voltages
    """
    d: float
    q: float


def dc_resistance(voltage: float, current: float) -> float:
    """
    Calculates the DC resistance using Ohms Law: V = IR
    """
    return voltage / current


def instantaneous_rms(currents: Currents) -> float:
    """
    Calculates the instantaneous rms current through
    the motor via taking the magnitude and dividing by sqrt(2)
    """
    i_d = currents.d
    i_q = currents.q

    peak = sqrt(i_d ** 2 + i_q ** 2)
    rms = peak / sqrt(2)
    return rms


def time_averaged_rms(i_rms_series: list[float]) -> float:
    """
    Calculates the final time-averaged RMS current
    squared -> mean -> root
    """
    samples = len(i_rms_series)
    squared_sum = sum(i**2 for i in i_rms_series)
    mean_square = squared_sum / samples
    i_rms_avg = sqrt(mean_square)

    return i_rms_avg


def electrical_angle(displacement: float, pitch: float) -> float:
    """
    Calculates the electrical angle of the armature.
    θ_e = π * displacement / pitch
    """
    return pi * displacement / pitch


def electrical_frequency(velocity: float, pole_pitch: float) -> float:
    """
    Calculates electrical frequency of the motor at a given instant.
    f_e = velocity / (2 * pole_pitch)
    """
    return velocity / (2 * pole_pitch)


def inductive_reactance(frequency: float, inductance: float) -> float:
    """
    Calculates inductive reactance of a phase.
    X_L = 2πfL
    """
    return 2 * pi * frequency * inductance


def phase_shift(reactance: float, resistance: float) -> float:
    """
    Calculates phase shift (radians) from reactance and resistance.
    φ = atan(X_L / R)

    NOTE: Returns phase shift in radians
    """
    return atan(reactance / resistance)


def active_power(
    voltage: float, current: float, phase_shift: float
) -> float:
    """
    Calculates the active (real) power.
    P = VI * cos(φ)

    NOTE: Has to be radians for phase shift
    """
    return voltage * current * cos(phase_shift)


def reactive_power(
    voltage: float, current: float, phase_shift: float
) -> float:
    """
    Calculates the reactive power.
    Q = VI * sin(φ)

    NOTE: Has to be radians for phase shift
    """
    return voltage * current * sin(phase_shift)


def induced_voltage(delta_flux_linkage: float, delta_time: float) -> float:
    """
    Calculates total induced (back-EMF) voltage.
    E = Δψ / Δt
    """
    return delta_flux_linkage / delta_time


def differential_d_current(time, i_d, v_d, R, L, e_induced) -> float:
    """
    Differential equation for d-axis current.
    di_d/dt = (v_d - R*i_d) / L
    (Uncoupled from q-axis)
    """
    _ = time
    return (v_d - R * i_d - e_induced) / L


def differential_q_current(time, i_q, v_q, R, L, e_induced) -> float:
    """
    Differential equation for q-axis current.
    di_q/dt = (v_q - R*i_q - e_induced) / L
    (Uncoupled from d-axis)
    """
    _ = time
    return (v_q - R * i_q - e_induced) / L


def clark_transform(a: float, b: float, c: float) -> tuple[float, float]:
    """
    Converts a, b, c values into alpha-beta components
    """
    alpha = (2 / 3) * (a - 0.5 * b - 0.5 * c)
    beta = (1 / sqrt(3)) * (b - c)
    return alpha, beta


def park_transform(
    alpha: float, beta: float, theta: float
) -> tuple[float, float]:
    """
    Converts alpha-beta stationary frame values to d-q frame values
    """
    d = alpha * cos(theta) + beta * sin(theta)
    q = beta * cos(theta) - alpha * sin(theta)
    return d, q


def inverse_park_transform(
    currents: Currents, electrical_angle: float
) -> Currents:
    """
    Converts d-q frame currents to stationary a-b frame.
    """
    i_d, i_q = currents.d, currents.q
    alpha = i_d * cos(electrical_angle) - i_q * sin(electrical_angle)
    beta = i_d * sin(electrical_angle) + i_q * cos(electrical_angle)
    return alpha, beta


def inverse_clarke_transform(
    alpha: float, beta: float
) -> tuple[float, float, float]:
    """
    Converts a-b stationary frame currents to three-phase (a,b,c).
    """
    phase_a = alpha
    phase_b = 0.5 * (sqrt(3) * beta - alpha)
    phase_c = 0.5 * (-sqrt(3) * beta - alpha)
    return phase_a, phase_b, phase_c


def rk_2nd_order_currents(
    time: float,
    currents: Currents,
    voltages: Voltages,
    resistance: float,
    inductance: float,
    delta_flux_linkage: tuple[float, float],
    step_size: float
) -> Currents:
    """
    Solves the differential equations for the
    d-axis and q-axis currents using Ralston's method
    """
    i_d, i_q = currents.d, currents.q
    v_d, v_q = voltages.d, voltages.q
    f_d, f_q = delta_flux_linkage

    d_induced = induced_voltage(f_d, step_size)
    q_induced = induced_voltage(f_q, step_size)

    k1_d = differential_d_current(
        time, i_d, v_d, resistance, inductance, d_induced
    )
    k1_q = differential_q_current(
        time, i_q, v_q, resistance, inductance, q_induced
    )

    k2_d = differential_d_current(
        time + 3 / 4 * step_size,
        i_d + 3 / 4 * step_size * k1_d,
        v_d,
        resistance,
        inductance,
        d_induced
    )

    k2_q = differential_q_current(
        time + 3 / 4 * step_size,
        i_q + 3 / 4 * step_size * k1_q,
        v_q,
        resistance,
        inductance,
        q_induced
    )

    # Final update using weighted average
    i_d += (1 / 3 * k1_d + 2 / 3 * k2_d) * step_size
    i_q += (1 / 3 * k1_q + 2 / 3 * k2_q) * step_size

    currents.d = i_d
    currents.q = i_q
    return currents
