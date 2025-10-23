"""
Filename: static_analysis.py
Author: William Bowley
Version: 0.3
Date: 2025-10-22

Description:
    Performs a single magneto-static
    simulation of the proposed design
"""

import logging
import numpy as np

from blueshark.renderer.renderer_interface import MagneticRenderer
from blueshark.solver.solver_interface import BaseSolver
from blueshark.simulate.static import static_simulation

from blueshark.models.coilgun_multi_stage.main import MultiStageCoilGun
from blueshark.models.coilgun_multi_stage.physics import dc_resistance


def get_circuit_values(
    coilgun: MultiStageCoilGun,
    solver: BaseSolver,
    num_steps: int = 5
) -> list[float, float]:
    """
    Gets the dc resistance and inductance for each stage using small
    test currents.

    NOTE:
        Assumes the inductance and resistance are
        approximately the same across coil 1, coil 2 and coil n
    """
    renderer: MagneticRenderer = coilgun.renderer
    try:
        coil_len = len(coilgun.CIRCUITS)
        middle_index = coil_len // 2
        coil = coilgun.CIRCUITS[middle_index]

        flux = []
        current = []
        resistances = []
        for i in range(1, num_steps + 1):
            # Increments current by current = test_current * 10^i
            frame_current = coilgun.load.test_current * 10 ** i
            renderer.change_circuit_current(coil, frame_current)
            result_circuit = static_simulation(
                renderer,
                solver,
                ["circuit_flux_linkage", "circuit_voltage"],
                circuits=coil
            )

            voltage = result_circuit["circuit_voltage"][coil]
            flux_linkage = result_circuit["circuit_flux_linkage"][coil]

            flux.append(flux_linkage)
            current.append(frame_current)

            resistances.append(dc_resistance(voltage, frame_current))

        # Average resistance and incremental inductance
        resistance = sum(resistances) / len(resistances)

        # Uses linear regression to appox df/di ~= inductance
        coefficient = np.polyfit(current, flux, 1)
        inductance = float(coefficient[0])

        # Resets all coil circuits to zero current
        for circuit in coilgun.CIRCUITS:
            renderer.change_circuit_current(circuit, 0)

        print(f"Coil 0->{coil_len} results collected..")
        return resistance, inductance

    except Exception as e:
        msg = f"Coil-gun circuit analysis failed | {coilgun}: {e}"
        logging.error(msg)
        raise RuntimeError(msg)
