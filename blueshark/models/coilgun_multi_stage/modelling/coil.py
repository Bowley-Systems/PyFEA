"""
Filename: coil.py
Author: William Bowley
Version: 0.1
Date: 2025-10-09

Description:
    Defines a coil instant for the dynamic launch
    analysis script `dynamic_analysis`.
"""

from blueshark.models.coilgun_multi_stage.main import MultiStageCoilGun
from blueshark.models.coilgun_multi_stage.modelling.physics import (
    calculate_inductor_voltage,
    calculate_inductance,
    rk_2nd_order_currents,
    clipping_current
)


class Coil:
    """ Model of a single coil within the coilgun with physics """

    def __init__(
        self,
        model: MultiStageCoilGun,
        origin: tuple[float, float],
        circuit: str,
        group: int,
        initial_resistance: float,
        initial_inductance: float,
    ) -> None:
        """ Initializes the class & defines dependencies"""
        self.model = model

        # FEM information
        self.origin = origin
        self.group = group
        self.circuit = circuit

        # Defines universal parameters
        self.initial_inductance = initial_inductance
        self.initial_resistance = initial_resistance

        self.activate = origin[1] + self.model.gap_activate
        self.deactivate = origin[1] + self.model.coil_deactivate
        self.supply = self.model.load.supply_voltage
        self.TIME_STEP = self.model.load.time_step

        # Dynamic parameters
        self.time: float = 0.0
        self.current: float = 0.0
        self.voltage: float = 0.0
        self.inductance: float = 0.0
        self.resistance: float = 0.0
        self.last_inductance: float = initial_inductance

    def update(
        self,
        position: float,
        resistance: float,
        flux_linkage: float
    ) -> float:
        """ Updates the class and runs the switching mechanism"""

        # Activation logic for the coil
        if position >= self.activate:
            if position >= self.deactivate:
                self.supply = 0.0

            # Updates resistance and inductance
            self.resistance = resistance
            self.inductance = calculate_inductance(
                self.initial_inductance, flux_linkage, self.current
            )

            # Calculates induced voltage and inductor voltage
            # This represents the motional EMF of the system
            induced_voltage = - self.current * (
                self.inductance - self.last_inductance
            ) / self.TIME_STEP

            self.last_inductance = self.inductance

            self.voltage = calculate_inductor_voltage(
                self.supply, self.current, self.resistance, induced_voltage
            )

            # Calculates the current within the inductor via di/dt = v/l
            self.current = rk_2nd_order_currents(
                self.current,
                self.voltage,
                self.inductance,
                self.resistance,
                self.TIME_STEP
            )

            # Limits the maximum current to supply max
            self.current = clipping_current(
                self.model.load.current_limit, self.current
            )

            # Steps across the instants time
            self.time += self.TIME_STEP

        return self.current

    @classmethod
    def create(
        cls,
        model: MultiStageCoilGun,
        origin: tuple[float, float],
        circuit: str,
        group: int,
        initial_resistance: float,
        initial_inductance: float
    ):
        """ Factory that returns a new coil instance """
        return cls(
            model, origin, circuit, group,
            initial_resistance, initial_inductance
        )
