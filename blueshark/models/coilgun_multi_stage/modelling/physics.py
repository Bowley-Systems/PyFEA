"""
File: physics.py
Author: William Bowley
Version: 0.1
Date: 2025-10-19
Description:
    Physics module for the `coilgun_multi_stage` module

    Uses mm-g-s units:
        - Millimeter, gram, second, ampere
"""

from math import pi

from blueshark.domain.constants import EPSILON


def dc_resistance(voltage: float, current: float) -> float:
    """
    Calculates the DC resistance using Ohms Law: V = IR
    """
    return voltage / current


def calculate_inductance(
    initial: float, flux_linkage: float, current: float
) -> float:
    """ Calculates the inductance via flux linkage """
    if abs(current) < EPSILON or abs(flux_linkage) < EPSILON:
        return initial

    ind = flux_linkage / current
    return ind


def projectile_drag(
    velocity: float,
    density: float,
    coefficient: float,
    radius: float
) -> float:
    """
    Calculates the drag force on the projectile
    """
    area = pi * radius ** 2
    velocity = velocity * abs(velocity)     # ABS ensure direction
    drag_force = -0.5 * density * velocity * area * coefficient
    return drag_force


def clipping_current(current_limit: float, current: float) -> float:
    """ Limits the current to simulate a current limiting supply """
    # Current clipping only applies to the positive peak as the negative
    # peak for a coilgun is caused by the field collapsing which isn't clamped
    return min(current_limit, current)


def differential_currents(voltage, inductance) -> float:
    """ Differential equation for current within the system """
    return voltage / inductance


def rk_2nd_order_currents(
    current: float,
    voltage: float,
    inductance: float,
    resistance: float,
    step_size: float
) -> float:
    """
    Solves the differential equation for the current within
    the inductor using Ralston's method
    """
    k1 = differential_currents(voltage, inductance)

    # Updates the voltage for the next predicted frame
    voltage = voltage - resistance * 3 / 4 * step_size * k1
    k2 = differential_currents(voltage, inductance)

    # Updates final using weighted average
    current += (1 / 3 * k1 + 2 / 3 * k2) * step_size
    return current


def calculate_inductor_voltage(
    supply_voltage: float,
    current: float,
    resistance: float,
    induced_voltage: float
) -> float:
    """
    Computes the inductor voltage during simulation
    """
    v_drop = current * resistance
    v_inductor = supply_voltage - v_drop + induced_voltage

    return v_inductor


def format_time(seconds: float) -> str:
    """ Converts seconds into HH:MM:SS. """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
