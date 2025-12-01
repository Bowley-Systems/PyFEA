"""
File: circuits.py
Author: William Bowley
Version: 1.4.2
Date: 2025-12-02
Description:
    Circuit analysis utilities for FEMMagnaticSolver
"""

import logging

from blueshark.domain.constants import PRECISION, EPSILON
from blueshark.solver.femm.magnetic import utils
from blueshark.domain.conversion.manager import PhysicalQuantity
from blueshark.domain.units import VOLT, AMPERE, WEBER, WATT, OHM


def voltage(circuit_name: str) -> PhysicalQuantity:
    """
    Get the voltage drop across the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """
    circuit_props = utils.get_circuit_properties(circuit_name)
    voltage = round(circuit_props[1], PRECISION)

    return PhysicalQuantity(voltage, VOLT)


def current(circuit_name: str) -> PhysicalQuantity:
    """
    Get the instantaneous current of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """
    circuit_props = utils.get_circuit_properties(circuit_name)
    current = round(circuit_props[0], PRECISION)

    return PhysicalQuantity(current, AMPERE)


def flux_linkage(circuit_name: str) -> PhysicalQuantity:
    """
    Get the flux linkage of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    flux_linkage = round(circuit_props[2], PRECISION)

    return PhysicalQuantity(flux_linkage, WEBER)


def power(circuit_name: str) -> PhysicalQuantity:
    """
    Calculate the instantaneous power of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)

    # Power = voltage * current
    power = circuit_props[0] * circuit_props[1]
    power = round(power, PRECISION)
    return PhysicalQuantity(power, WATT)


def resistance(circuit_name: str) -> PhysicalQuantity:
    """
    Calculates the resistance of the specified circuit.

    Args:
        circuit_name (str): Name of the circuit.
    """

    circuit_props = utils.get_circuit_properties(circuit_name)
    circuit_current = circuit_props[0]

    if abs(circuit_current) > EPSILON:
        # Resistance = voltage / current
        resistance = circuit_props[1] / circuit_current
    else:
        resistance = 0.0
        msg = (
            f"Failed to calculate resistance, {circuit_current} < {EPSILON};"
            f"Defaulting Resistance to 0.0 {OHM}"
        )
        logging.error(msg)

    resistance = round(resistance, PRECISION)
    return PhysicalQuantity(resistance, OHM)
