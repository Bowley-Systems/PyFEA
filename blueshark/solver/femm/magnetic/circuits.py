"""
File: circuits.py
Author: William Bowley
Version: 1.4.1
Date: 2025-10-24
Description:
    Circuit analysis utilities for
    FEMMagnaticSolver
"""

import logging

from blueshark.domain.constants import PRECISION, EPSILON
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.units import (
    Unit, VOLT, AMPERE, WEBER, WATT, OHM, HENRY
)


def voltage(circuit_name: str) -> tuple[float, Unit]:
    """
    Get the voltage drop across the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """
    circuit_props = utils.get_circuit_properties(circuit_name)
    voltage = circuit_props[1]
    voltage = round(voltage, PRECISION)

    return voltage, VOLT


def current(circuit_name: str) -> tuple[float, Unit]:
    """
    Get the instantaneous current of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """
    circuit_props = utils.get_circuit_properties(circuit_name)
    current = circuit_props[0]
    current = round(current, PRECISION)

    return current, AMPERE


def flux_linkage(circuit_name: str) -> tuple[float, Unit]:
    """
    Get the flux linkage of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    flux_linkage = circuit_props[2]
    flux_linkage = round(flux_linkage, PRECISION)

    return flux_linkage, WEBER


def power(circuit_name: str) -> tuple[float, Unit]:
    """
    Calculate the instantaneous power of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    current = circuit_props[0]
    voltage = circuit_props[1]

    power = current * voltage
    power = round(power, PRECISION)
    return power, WATT


def resistance(circuit_name: str) -> tuple[float, Unit]:
    """
    Calculates the resistance of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    current = circuit_props[0]
    voltage = circuit_props[1]

    if abs(current) > EPSILON:
        resistance = voltage / current
    else:
        resistance = 0.0
        msg = (
            f"Failed to calculate resistance, {current} < {EPSILON};"
            "Resistance = 0.0"
        )
        logging.error(msg)

    resistance = round(resistance, PRECISION)
    return resistance, OHM


# This method can be numerically unstable
def inductance(circuit_name: str) -> tuple[float, Unit]:
    """
    Calculate the inductance of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    current = circuit_props[0]
    flux_linkage = circuit_props[2]

    if abs(current) > EPSILON:
        inductance = flux_linkage / current
    else:
        inductance = 0.0
        msg = (
            f"Failed to calculate inductance, {current} < {EPSILON};"
            "inductance = 0.0"
        )
        logging.error(msg)

    inductance = round(abs(inductance), PRECISION)
    return inductance, HENRY
