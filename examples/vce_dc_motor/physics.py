"""
File: physics.py
Author: William Bowley
Version: 1.4
Date: 2025-10-13
Description:
    Physics module for the `dc_motor.py` example
    script using FEM: Magnetic Renderer & Solver

    Uses mm-g-s Units:
        - Millimeter, gram, second, ampere
"""


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


def angular_acceleration(torque: float, mass: float, radius: float) -> float:
    """
    Calculates the angular acceleration.
    a = (torque) / (mass * radius ^ 2)
    """
    return torque / (mass * radius ** 2)


def current_de(
    time: float,
    current: float,
    e_induced: float,
    resistance: float,
    inductance: float,
    supply_voltage: float,
) -> float:
    """
    Differential equation for current within the motor.
    di/dt = (v_d - e_induced - current * resistance) / inductance
    """
    _ = time
    return (supply_voltage - e_induced - current * resistance) / inductance


def rk_2nd_current(
    time: float,
    current: float,
    e_induced: float,
    resistance: float,
    inductance: float,
    supply_voltage: float,
    step_size: float
) -> float:
    """
    Solves the differential equation for the current
    within the motor using Ralston's method
    """

    k1 = current_de(
        time, current, e_induced, resistance, inductance, supply_voltage
    )

    k2 = current_de(
        time + 3 / 4 * step_size,
        current + 3 / 4 * step_size * k1,
        e_induced,
        resistance,
        inductance,
        supply_voltage
    )

    current += (1 / 3 * k1 + 2 / 3 * k2) * step_size
    return current
