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


def electrical_angle(displacement: float, pitch: float) -> float:
    """
    Calculates the electrical angle of the armature.
    θ_e = π * displacement / pitch
    """
    return pi * displacement / pitch


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
