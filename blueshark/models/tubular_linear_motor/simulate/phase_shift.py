"""
Filename: phase_shift.py
Author: William Bowley
Version: 0.1
Date: 2025-11-12

Description:
    Finds the optimal initial phase shift
    to align the armature and stator via
    bayesian optimization
"""

import logging
from math import sqrt
from bayes_opt import BayesianOptimization
from functools import partial

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.domain.conversion.manager import conversion
from blueshark.simulate.static import static_simulation
from blueshark.domain.units import Unit, NEWTON, NEWTON_AMPERE, DIMENSIONLESS

from blueshark.models.tubular_linear_motor.modelling.physics import (
    Currents, inverse_clarke_transform, inverse_park_transform,
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
