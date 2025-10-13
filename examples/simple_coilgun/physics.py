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

from math import ceil, pi, exp
from blueshark.domain.constants import EPSILON


def calculate_inductance(field_energy: float, current: float) -> float:
    """ Calculates the inductance via the energy stored within the field """
    if abs(current) < EPSILON or abs(current) < EPSILON:
        return 0.0

    ind = (2*field_energy) / (current ** 2)
    return ind


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


def inst_current_charge(
    time: float,
    resistance: float,
    inductance: float,
    voltage: float
) -> float:
    """Calculates the current during charging in an RL circuit"""
    if abs(inductance) < EPSILON or abs(resistance) < EPSILON:
        return 0.0

    tau = inductance / resistance
    max_i = voltage / resistance
    return max_i * (1 - exp((-time) / tau))


def inst_current_discharge(
    time: float,
    time_offset: float,
    initial_current: float,
    resistance: float,
    inductance: float
) -> float:
    """Calculates the current during discharging an RL circuit"""
    if abs(inductance) < EPSILON or abs(resistance) < EPSILON:
        return 0.0

    tau = inductance / resistance
    return initial_current * exp(-(time - time_offset) / tau)


def clipping_current(current_limit: float, current: float) -> float:
    """ Limits the current to simulate a current limiting supply """
    return min(current_limit, current)
