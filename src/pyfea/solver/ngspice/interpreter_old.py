"""
Filename: interpreter.py

Description:
    Interprets pyfea intermediate representation (IR) of 
    circuit topology to ngspice net-list structure
"""

from pyfea import volt
from pyfea.domain.units import strip_quantity

from pyfea.domain.circuits.domain import Domain
from pyfea.domain.circuits.definitions import ComponentTypes, Configuration
from pyfea.domain.circuits.nodes import Abstract, Device, Component

from pyfea.solver.renderer_interface import RendererError

class NGspiceInterpreter:
    """ Interprets pyfea circuit IR to ngspice net-list structure """
    @classmethod
    def transverse_tree(cls, domain: Domain) -> str:
        """ Transverse the Abstract tree and begins interpretation"""
        states = [0, 0, 0, 0, 0]
        spice, states = cls.find_source(domain, states)

        linked = domain.linked
        parts: list[Abstract | Device] = []
        for link in linked:
            for terminals in link:
                parent = terminals.parent

                if isinstance(parent, Domain) or parent in parts:
                    continue

                if isinstance(parent, Abstract):
                    print(link)
                    spice, states = cls.local_topology(parent, spice, states)
                    parts.append(parent)
                    continue

                elif isinstance(parent, Device):
                    if parent.component.type == ComponentTypes.SOURCE:
                        continue

                    # spice, num = cls.construct_device(parent, spice, num)
                    parts.append(parent)
                    continue

                name = "NGspiceInterpreter"
                msg = f"{parent!r} not supported by {name}"
                raise RendererError(msg)

        terminals = [t for part in parts for t in part.terminals.values()]
        for link in linked:
            for terminal in link:
                if terminal in terminals:
                    terminals.remove(terminal)

        if len(terminals) == 0:
            print(states)
            return spice

        msg = f"Not all terminals are connected, {terminals!r} needs to be connected"
        raise RendererError(msg)

    @classmethod
    def find_source(cls, domain: Domain, states: list[int]) -> tuple[str, int]:
        """ Finds the source within the domain and creates it """
        linked = domain.linked
        spice = ""
        found = []

        for link in linked:
            for terminals in link:
                parent = terminals.parent

                if isinstance(parent, Device):
                    if parent in found:
                        continue

                    if parent.component.type != ComponentTypes.SOURCE:
                        continue

                    found.append(parent)
                    amplitude = parent.component.params["amplitude"]
                    amplitude = strip_quantity(amplitude, volt)
                    spice += f"""V{len(found)} {len(found)} 0 DC {amplitude}V"""

        states[0] = len(found)
        return spice, states

    @classmethod
    def local_topology(
        cls, topology: Abstract, spice: str, states: list[int]
    ) -> tuple[str, int]:
        """ Interprets local abstract topology """
        relation = topology.configuration
        num = sum(states)

        match relation:
            case Configuration.series:
                print(topology.terminals)
                return spice, states

            case Configuration.parallel:
                return spice, states

            case _:
                msg = f"{topology!r} has an unknown configuration, {topology.configuration}"
                raise RendererError(msg)
    
    @classmethod
    def construct_device(cls, device: Device, spice: str, num: int):
        """ Constructs a device within the simulation domain """
        return

    @classmethod
    def construct_component(cls, component: Component, net: str) -> str:
        """ Constructs a component within the simulation domain """
        match component.type:
            case ComponentTypes.RESISTOR:
                return ""

            case ComponentTypes.CAPACITOR:
                return ""

            case _:
                msg = f"{component.type!r} is unknown must be valid {ComponentTypes}"