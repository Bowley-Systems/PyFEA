"""
Filename: builder.py

Description:
    Defines the CircuitBuilder class
    for constructing and defining circuit topology
"""


from dataclasses import dataclass

from pyfea import Quantity as Q, check_quantity, ohm, farad, volt, kelvin

from pyfea.domain.circuits.domain import Domain
from pyfea.domain.circuits.definitions import Configuration
from pyfea.domain.circuits.nodes import Component, ComponentTypes, Branch


class Builder:
    """ Builds circuit topology using groups and relative configurations """
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
        return Component(ComponentTypes.SOURCE, parameters, False)

    @staticmethod
    def resistor(resistance: Q) -> Component:
        """ Creates a source component """
        # Ensures units are correct before constructing the component
        check_quantity(resistance, ohm)

        # Constructs parameters as a series of value : units
        parameters = {"resistance": resistance}
        return Component(ComponentTypes.RESISTOR, parameters)

    @staticmethod
    def branch(config: Configuration, *components: Component | Branch) -> Branch:
        """ Configures a series of components / branches into a larger branch """
        return Branch(config, *components)

    @staticmethod
    def domain(
        source: Component, branches: Branch, temperature: Q, nominal_temp: Q
    ) -> Domain:
        """ Builds the lumped parameter domain """
        # Ensures units are correct before construction
        check_quantity(temperature, kelvin)
        check_quantity(nominal_temp, kelvin)

        if source.Linkable:
            msg = f"{source!r} is not a defined correctly must be non linkable"
            raise TypeError(msg)

        return Domain(source, branches, temperature, nominal_temp)


@dataclass
class Circuit:
    """ Temp. Class to not break FEA solver adaptors. """
    name: str
    current: Q
    configuration: Configuration
    
    def __hash__(self):
        """ Hash based class attributes """
        return hash(
            (self.name, self.current, self.configuration)
        )