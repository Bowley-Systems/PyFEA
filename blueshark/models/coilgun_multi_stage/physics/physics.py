"""
File: physics.py
Author: William Bowley
Version: 0.1
Date: 2025-10-19
Description:
    Physics module for the `coilgun.py` example
    script using FEM: Magnetic Renderer & Solver

    Uses mm-g-s Units:
        - Millimeter, gram, second, ampere
"""

from math import pi


def dc_resistance(voltage: float, current: float) -> float:
    """
    Calculates the DC resistance using Ohms Law: V = IR
    """
    return voltage / current


def projectile_drag(
    density: float,
    velocity: float,
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
    return min(current_limit, current)


def differential_currents(
    time, voltage, inductance
) -> float:
    """ Differential equation for current within the system """
    _ = time

    return (voltage) / inductance


def rk_2nd_order_currents(
    time: float,
    current: float,
    voltage: float,
    inductance: float,
    step_size: float
) -> float:
    """
    Solves the differential equation for the current within
    the inductor using Ralston's method
    """
    k1 = differential_currents(time, voltage, inductance)
    k2 = differential_currents(
        time + 3 / 4 * step_size,
        current + 3 / 4 * step_size * k1,
        inductance
    )

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
    v_drop = - current * resistance
    v_inductor = supply_voltage - v_drop - induced_voltage

    return v_inductor


def format_time(seconds: float) -> str:
    """ Converts seconds into HH:MM:SS. """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
