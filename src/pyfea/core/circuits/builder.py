"""
Filename: builder.py

Description:
    Defines the CircuitBuilder class
    for constructing and defining circuit topology
"""


from pyfea.core.units import Q, check_quantity, ohm, farad, volt, kelvin, ampere

from pyfea.core.circuits.domain import Domain
from pyfea.core.circuits.definitions import Configuration, MockCircuit
from pyfea.core.circuits.nodes import Component, ComponentTypes, Abstract, Device


class Builder:
    """ Builds circuit topology using groups and relative configurations """
    @staticmethod
    def feed_circuit(current: Q, config: Configuration):
        """ Creates a feed circuit for FEA solvers """
        # Ensures units are correct before constructing the feeder circuit
        check_quantity(current, ampere)

        return MockCircuit(current, config)

    @staticmethod
    def capacitor(
        capacitance: Q, esr: Q = 0 * ohm, esl: Q = 0 * ohm,
    ) -> Component:
        """ Creates a capacitor component """
        # Ensures units are correct before constructing the component
        check_quantity(capacitance, farad)
        check_quantity(esr, ohm)
        check_quantity(esl, ohm)

        # Constructs parameters as a series of value : units
        parameters = {"capacitance": capacitance, "esr": esr, "esl": esl}
        return Component(ComponentTypes.CAPACITOR, parameters)

    @staticmethod
    def source(amplitude: Q) -> Component:
        """ Creates a source component """
        # Ensures units are correct before constructing the component
        check_quantity(amplitude, volt)

        # Constructs parameters as a series of value : units
        parameters = {"amplitude": amplitude}
        source = Component(ComponentTypes.SOURCE, parameters, False)
        return Device(source, ("out", "gnd"))

    @staticmethod
    def resistor(resistance: Q) -> Component:
        """ Creates a source component """
        # Ensures units are correct before constructing the component
        check_quantity(resistance, ohm)

        # Constructs parameters as a series of value : units
        parameters = {"resistance": resistance}
        return Component(ComponentTypes.RESISTOR, parameters)

    @staticmethod
    def abstract(config: Configuration, *components: Component | Abstract) -> Abstract:
        """ Configures a series of components / Abstract into a larger Abstract """
        return Abstract(config, *components)

    @staticmethod
    def domain(temperature: Q, nominal_temp: Q
    ) -> Domain:
        """ Builds the lumped parameter domain """
        # Ensures units are correct before construction
        check_quantity(temperature, kelvin)
        check_quantity(nominal_temp, kelvin)

        return Domain(temperature, nominal_temp)
