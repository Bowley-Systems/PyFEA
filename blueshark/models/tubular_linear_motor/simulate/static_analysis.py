"""
Filename: static_analysis.py
Author: William Bowley
Version: 0.2
Date: 2025-10-09

Description:
    Performs a single magneto-static
    simulation of the proposed design
"""

import logging

from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.simulate.static import static_simulation

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.models.tubular_linear_motor.physics.physics import dc_resistance

# Constant variables
TEST_CURRENT = 1e-2  # Ampere's


def get_magnet_flux(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver
) -> list[float, float, float]:
    """
    Gets the magnet flux when there is zero current flowing
    through the phases within the motor.
    """
    try:
        # Sets the current within all the phases to zero.
        phases = motor.PHASES
        for phase in phases:
            renderer.change_circuit_current(phase, 0)

        # Simulate to get the zero_current magnetic flux
        results_magnet = static_simulation(
            renderer,
            solver,
            ["circuit_flux_linkage"],
            circuits=phases
        )

        flux_dict = results_magnet["circuit_flux_linkage"]

        print("Magnet flux results collected..")

        return [
            value_unit_tuple[0] for value_unit_tuple in flux_dict.values()
        ]

    except Exception as e:
        msg = f"Get magnet flux simulation failed for {motor}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def get_phase_values(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver,
    num_steps: int = 5
) -> tuple[float, float]:
    """
    Gets the phase inductance and average DC resistance using multiple
    small test currents.

    NOTE:
        Assumes the inductance and resistance are
        approximately the same across phase A, phase B and phase C
    """
    try:
        phases_a = motor.PHASES[0]

        flux = []
        current = []
        resistances = []
        for i in range(1, num_steps + 1):
            frame_current = TEST_CURRENT * i
            renderer.change_circuit_current(phases_a, frame_current)

            result_circuit = static_simulation(
                renderer,
                solver,
                ["circuit_flux_linkage", "circuit_voltage"],
                circuits=phases_a
            )

            voltage, _ = result_circuit["circuit_voltage"][phases_a]
            flux_linkage, _ = result_circuit["circuit_flux_linkage"][phases_a]

            flux.append(flux_linkage)
            current.append(frame_current)

            resistances.append(dc_resistance(voltage, frame_current))

        # Average resistance and incremental inductance
        resistance = sum(resistances) / len(resistances)
        inductance = (flux[-1] - flux[0]) / (current[-1] - current[0])

        # Resets all phases to zero current
        phases = motor.PHASES
        for phase in phases:
            renderer.change_circuit_current(phase, 0)

        print("Phase A, B and C results collected..")
        return resistance, inductance

    except Exception as e:
        msg = f"Get phases values simulation failed for {motor}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)
