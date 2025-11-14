"""
File: controller.py
Author: William Bowley
Version: 0.1
Date: 2025-11-13
Description:
    Cascaded PD-PI Controller for the Tubular Synchronous Linear Motor
"""

from math import sqrt

from blueshark.models.tubular_linear_motor.main import TubularLinearMotor
from blueshark.domain.conversion.manager import conversion
from blueshark.domain.units import (
    Unit, VOLT, AMPERE, HENRY, OHM, NEWTON_AMPERE,
    KILOGRAM, SECOND, METER, METER_SECOND
)


class CascadedController:
    """ Cascaded PD & PI controller for the TLSM """
    def __init__(
        self,
        motor: TubularLinearMotor,
        time_step: tuple[float, Unit],
        armature_mass: tuple[float, Unit],
        force_constant: tuple[float, Unit],
        phase_resistance: tuple[float, Unit],
        phase_inductance: tuple[float, Unit],
    ) -> None:
        """ Initializes the class & calculates loop terms """
        self.load = motor.load

        # Converts input units into controller internal units
        self._converts_quantities(
            time_step, armature_mass, force_constant,
            phase_resistance, phase_inductance
        )

        """ NOTE: Cannot check units for these currently. Future Fix """
        self.current_limit = float(self.load.current_limit)  # Assume Amperes
        self.voltage_limit = float(self.load.supply_voltage)  # Assume Volts
        motor_load = float(self.load.mass)  # Assume kg

        # Defines controller constants
        freq = self.phase_resistance / self.phase_inductance
        bandwidth = freq
        mass = self.armature_mass + motor_load

        # Defines position loop
        n_freq = freq / 5     # 1/5 of current loop to ensure separation
        damping_ratio = sqrt(2) / 2

        self.pos_kp = (mass * n_freq ** 2) / self.force_constant
        self.pos_kd = (2 * mass * damping_ratio * n_freq) / self.force_constant
        self.target_position = 0

        # Defines current loop
        self.cur_kp = self.phase_inductance * bandwidth
        self.cur_ki = self.phase_resistance * bandwidth

        self.cur_summation = 0
        self.cur_target = 0

    def set_target_position(self, position: tuple[float, Unit]) -> None:
        """ Sets a new target position for the controller """
        position, unit = position
        position, _ = conversion(position, unit, METER)
        self.target_position = position

    def step(
        self,
        position: tuple[float, Unit],
        velocity: tuple[float, Unit],
        current: tuple[float, Unit],
    ) -> tuple[float, Unit]:
        """
        Calculates the voltage to drive the motor from position & current
        """
        position, unit = position
        position, _ = conversion(position, unit, METER)
        velocity, unit = velocity
        velocity, _ = conversion(velocity, unit, METER_SECOND)
        current, unit = current
        current, _ = conversion(current, unit, AMPERE)

        self.cur_target = self._position_pd(position, velocity)
        return self._current_pi(current)

    def reset(self):
        """ Resets the controller """
        self.cur_summation = 0
        self.target_position = 0
        self.cur_target = 0

    def _position_pd(self, position: float, velocity: float) -> float:
        """ Calculates the current for the PI current controller """
        error = self.target_position - position
        proportional = self.pos_kp * error

        derivative = - self.pos_kd * velocity
        current = proportional + derivative
        if abs(current) > self.current_limit:
            # Ensures that the directionality of the current is maintained
            return self.current_limit if current > 0 else -self.current_limit

        return current

    def _current_pi(self, current: float) -> tuple[float, Unit]:
        """ Calculates the voltage for the motor q axis """
        error = self.cur_target - current
        proportional = self.cur_kp * error

        # Predicted voltage with current integrator state
        tentative = proportional + self.cur_summation * self.cur_ki

        if abs(tentative) <= self.voltage_limit:
            self.cur_summation += error * self.time_step
            voltage = tentative
        else:
            # Clamp and prevent windup
            voltage = (
                self.voltage_limit if tentative > 0 else -self.voltage_limit
            )

        return voltage, VOLT

    def _converts_quantities(
        self,
        time_step: tuple[float, Unit],
        armature_mass: tuple[float, Unit],
        force_constant: tuple[float, Unit],
        phase_resistance: tuple[float, Unit],
        phase_inductance: tuple[float, Unit],
    ) -> None:
        """ Converts units of quantities to internal units and scales """
        step, unit = time_step
        self.time_step, _ = conversion(step, unit, SECOND)
        mass, unit = armature_mass
        self.armature_mass, _ = conversion(mass, unit, KILOGRAM)
        force, unit = force_constant
        self.force_constant, _ = conversion(force, unit, NEWTON_AMPERE)
        resistance, unit = phase_resistance
        self.phase_resistance, _ = conversion(resistance, unit, OHM)
        inductance, unit = phase_inductance
        self.phase_inductance, _ = conversion(inductance, unit, HENRY)
