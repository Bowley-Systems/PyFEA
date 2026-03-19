"""
Filename: domain.py

Description:
    Defines the dataclasses for the domain. 
    Which holds the branches and temperature conditions
"""


from pyfea import Quantity as Q
from pyfea.domain.circuits.nodes import Terminal



class Domain:
    """ Lumped circuit simulation domain """
    def __init__(self, temperature: Q, nominal_temperature: Q) -> None:
        """ Initialise the circuit domain"""
        self.temperature = temperature
        self.nominal_temperature = nominal_temperature
        self.linked = []
        self.gnd = Terminal("gnd", self)

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        seen = {}
        for item in self.linked:
            for terminal in item:
                if terminal.parent is not self:
                    seen[terminal.parent.name] = None

        parts = ", ".join(seen.keys())

        return (
            f"<Domain=(parts={parts}, "
            f"temperature={self.temperature:.3f}, "
            f"nominal_temp={self.nominal_temperature:.3f})>"
        )
    def link(self, *terminals: Terminal) -> None:
        """ Links different abstracts terminals together """
        self.linked.append(terminals)

    def __str__(self) -> str:
        """ Returns self._name """
        return self._name

    def __repr__(self) -> str:
        """ Returns self._name """
        return self._name
