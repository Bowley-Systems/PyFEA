"""
File: physics.py
Author: William Bowley
Version: 0.1
Date: 2025-11-03
Description:
    Physics module for the `tubular_linear_motor` module

    Uses mm-g-s units:
        - Millimeter, gram, second, ampere
"""


from math import cos, sin, sqrt, pi
from dataclasses import dataclass


@dataclass
class Currents:
    """ Holds the d-q frame currents """
    d: float
    q: float


@dataclass
class Voltages:
    """ Holds the d-q frame voltages """
    d: float
    q: float


def dc_resistance(voltage: float, current: float) -> float:
    """ Calculates the DC resistance using Ohms Law: V = IR """
    return voltage / current


def electrical_angle(displacement: float, pitch: float) -> float:
    """
    Calculates the electrical angle of the armature.
    θ_e = π * displacement / pitch
    """
    return pi * displacement / pitch


def inverse_park_transform(
    currents: Currents, electrical_angle: float
) -> Currents:
    """ Converts d-q frame currents to stationary a-b frame. """
    i_d, i_q = currents.d, currents.q
    alpha = i_d * cos(electrical_angle) - i_q * sin(electrical_angle)
    beta = i_d * sin(electrical_angle) + i_q * cos(electrical_angle)
    return alpha, beta


def inverse_clarke_transform(
    alpha: float, beta: float
) -> tuple[float, float, float]:
    """ Converts a-b stationary frame currents to three-phase (a,b,c). """
    phase_a = alpha
    phase_b = 0.5 * (sqrt(3) * beta - alpha)
    phase_c = 0.5 * (-sqrt(3) * beta - alpha)
    return phase_a, phase_b, phase_c


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


def format_time(seconds: float) -> str:
    """ Converts seconds into HH:MM:SS. """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


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
