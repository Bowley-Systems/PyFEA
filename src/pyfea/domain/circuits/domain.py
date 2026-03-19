"""
Filename: domain.py

Description:
    Defines the dataclasses for the domain. 
    Which holds the branches and temperature conditions
"""

from dataclasses import dataclass

from pyfea import Quantity as Q
from pyfea.domain.circuits.nodes import Branch, Component


@dataclass(slots=True)
class Domain:
    """ Lumped circuit simulation domain """
    source: Component
    branches: list[Branch] | Branch
    temperature: Q
    nominal_temperature: Q

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Domain=(branches={self.branches}, "
            f"temperature={self.temperature:.3f}, "
            f"nominal_temp={self.nominal_temperature:.3f})>"
        )

    def __str__(self) -> str:
        """ Returns self._name """
        return self._name

    def __repr__(self) -> str:
        """ Returns self._name """
        return self._name
