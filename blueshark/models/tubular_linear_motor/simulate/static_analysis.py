"""
Filename: static_analysis.py
Author: William Bowley
Version: 0.4
Date: 2025-11-14

Description:
    Performs a series of characterization
    runs to define the motor before launch
"""

import logging
import numpy as np

from math import sqrt
from bayes_opt import BayesianOptimization
from functools import partial

from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.simulate.static import static_simulation
from blueshark.domain.conversion.manager import conversion
from blueshark.domain.units import (
    Unit, HENRY, OHM, VOLT, WEBER, NEWTON, NEWTON_AMPERE, DIMENSIONLESS
)

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.models.tubular_linear_motor.modelling.physics import (
    dc_resistance, Currents, inverse_clarke_transform, inverse_park_transform,
    electrical_angle
)


def _get_force(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver,
    phase_shift: float
) -> tuple[float, Unit]:
    """
    Gets the magnetic force for a specific phase shift
    """
    try:
        # Calculates the currents in that position
        current = motor.load.current_limit
        current = Currents(0, current)
        alpha, beta = inverse_park_transform(current, phase_shift)
        currents = inverse_clarke_transform(alpha, beta)   # ia, ib, ic

        # Sets the motor phases to ia, ib, ic
        phases = motor.PHASES
        for index, phase in enumerate(phases):
            renderer.change_circuit_current(phase, currents[index])

        results = static_simulation(
            renderer, solver, ["force_lorentz"], elements=motor.SLOT
        )

        # Extracting the force result and converting to NEWTON
        results = results["force_lorentz"]
        force, _, unit = results[motor.SLOT]
        force, _ = conversion(force, unit, NEWTON)

        return force, NEWTON

    except Exception as e:
        msg = f"get force simulation failed for {motor}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def get_magnet_flux(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver,
    verbose: bool = True,
) -> tuple[tuple[float, Unit], tuple[float, Unit], tuple[float, Unit]]:
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
            renderer, solver, ["circuit_flux_linkage"], circuits=phases
        )

        flux_dict = results_magnet["circuit_flux_linkage"]

        flux = []
        for phase, unit in flux_dict.values():
            phase, unit = conversion(phase, unit, WEBER)
            flux.append((phase, unit))

        msg = "Motor magnet flux results collected"
        logging.info(msg)
        if verbose:
            print(msg)

        return flux

    except Exception as e:
        msg = f"Get magnet flux simulation failed for {motor}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def get_phase_values(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver,
    num_steps: int = 5,
    verbose: bool = True,
) -> tuple[tuple[float, Unit], tuple[float, Unit]]:
    """
    Gets the phase inductance and average DC resistance using multiple
    small test currents.

    NOTE:
        Assumes the inductance and resistance are
        approximately the same across phase A, phase B and phase C
    """
    renderer: MagneticRenderer = motor.renderer

    if num_steps < 2:
        raise ValueError("Not enough current steps for regression.")

    try:
        coil = motor.PHASES[0]

        flux = []
        current = []
        resistances = []
        for i in range(1, num_steps + 1):
            # Increments current by current = test_current * 10^i
            frame_current = motor.load.test_current * 10 ** i
            if frame_current > 10:
                msg = "Frame current is too high. Decrease test_current"
                raise ValueError(msg)

            renderer.change_circuit_current(coil, frame_current)
            result_circuit = static_simulation(
                renderer,
                solver,
                ["circuit_flux_linkage", "circuit_voltage"],
                circuits=coil
            )

            # Extracts values, unit from solver
            voltage, unit_volt = result_circuit["circuit_voltage"][coil]
            linkage, unit_flux = result_circuit["circuit_flux_linkage"][coil]

            # Checks and converts to correct unit
            voltage, _ = conversion(voltage, unit_volt, VOLT)
            linkage, _ = conversion(linkage, unit_flux, WEBER)

            flux.append(linkage)
            current.append(frame_current)
            resistances.append(dc_resistance(voltage, frame_current))

        # Average resistance and incremental inductance
        resistance = sum(resistances) / len(resistances)

        # Uses linear regression to appox df/di ~= inductance
        coefficient = np.polyfit(current, flux, 1)
        inductance = float(coefficient[0])

        # Resets phase A to 0 amps
        renderer.change_circuit_current(coil, 0)

        msg = "Phase circuit values collected"
        logging.info(msg)
        if verbose:
            print(msg)

        return (resistance, OHM), (inductance, HENRY)

    except Exception as e:
        msg = f"Linear motor circuit analysis failed | {motor}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)


def get_force(
    motor: TubularLinearMotor,
    renderer: MagneticRenderer,
    solver: BaseSolver,
    iterations: int = 25,
    verbose: bool = True,
) -> tuple[tuple[float, Unit], tuple[float, Unit]]:
    """ Finds the optimal initial phase shift for sync """

    # Defines a partial function with the phase shift argument missing
    f_partial = partial(
        _get_force,
        motor=motor,
        renderer=renderer,
        solver=solver
    )

    # Defines the get_force function as a black box (input -> output)
    def black_box(phase_shift: float) -> float:
        force, _ = f_partial(phase_shift=phase_shift)
        return force

    # Optimization bounds [-pi, pi]
    lower = electrical_angle(-motor.pole_pitch, motor.pole_pitch)
    upper = electrical_angle(motor.pole_pitch, motor.pole_pitch)
    bound = {'phase_shift': (lower, upper)}

    optimizer = BayesianOptimization(
        f=black_box,
        pbounds=bound,
        random_state=42,
        verbose=0
    )

    # Maximizes the force via phase shift
    optimizer.maximize(
        init_points=5,
        n_iter=iterations-5,
    )

    msg = "Motor optimal phase shift collected"
    logging.info(msg)
    if verbose:
        print(msg)

    # Returns the shift for the maximum force (RADIANS)
    optimal_shift = float(optimizer.max['params']['phase_shift'])

    # Returns the force constant as force / rms_current
    current_rms = motor.load.current_limit / sqrt(2)
    force_constant = float(optimizer.max['target']) / current_rms

    return (optimal_shift, DIMENSIONLESS), (force_constant, NEWTON_AMPERE)
