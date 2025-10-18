"""
File: physics.py
Author: William Bowley
Version: 1.4
Date: 2025-10-13
Description:
    Physics module for the `coilgun.py` example
    script using FEM: Magnetic Renderer & Solver

    Uses mm-g-s Units:
        - Millimeter, gram, second, ampere
"""

from math import ceil, pi
from blueshark.domain.constants import EPSILON


def calculate_inductance(field_energy: float, current: float) -> float:
    """ Calculates the inductance via the energy stored within the field """
    if abs(current) < EPSILON or abs(current) < EPSILON:
        return 0.0

    ind = (2*field_energy) / (current ** 2)
    return ind


def induced_voltage(delta_flux_linkage: float, delta_time: float) -> float:
    """
    Calculates total induced (back-EMF) voltage.
    E = Δψ / Δt
    """
    return delta_flux_linkage / delta_time


def estimate_turns(
    axial_length: float,
    inner_radi: float,
    outer_radi: float,
    wire_dia: float,
    factor: float
) -> int:
    """ Calculates the number of turns within section of the coil"""
    slot_area = axial_length * (outer_radi - inner_radi)
    wire_area = wire_dia ** 2
    effective = slot_area * factor

    return ceil(effective / wire_area)


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
    drag_force = 0.5 * density * velocity * abs(velocity) * area * coefficient
    return drag_force


def clipping_current(current_limit: float, current: float) -> float:
    """ Limits the current to simulate a current limiting supply """
    return min(current_limit, current)


def differential_currents(
    time, current, voltage, inductance, resistance
) -> float:
    """ Differential equation for current within the system """
    _ = time

    return (voltage - resistance * current) / inductance


def rk_2nd_order_currents(
    time: float,
    current: float,
    voltage: float,
    resistance: float,
    inductance: float,
    step_size: float
) -> float:
    """
    Solves the differential equations for the currents
    using Ralston's method
    """
    k1 = differential_currents(
        time, current, voltage, inductance, resistance
    )

    k2 = differential_currents(
        time + 3 / 4 * step_size,
        current + 3 / 4 * step_size * k1,
        voltage,
        inductance,
        resistance,
    )

    # Final update using weighted average
    current += (1 / 3 * k1 + 2 / 3 * k2) * step_size
    return current, voltage


def format_time(seconds: float) -> str:
    """ Converts seconds into HH:MM:SS. """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
