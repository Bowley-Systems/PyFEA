"""
Filename: interpreter.py

Description:
    Interprets pyfea intermediate representation (IR) of 
    circuit topology to ngspice net-list structure
"""

from pyfea.domain.circuits.domain import Domain
from pyfea.domain.circuits.nodes import Abstract, Device, Component

from pyfea.solver.renderer_interface import RendererError

class NGspiceInterpreter:
    """ Interprets pyfea circuit IR to ngspice net-list structure """
    @classmethod
    def transverse_tree(cls, domain: Domain) -> None:
        """ Transverse the Abstract tree and begins interpretation"""
        linked = domain.linked

        parts: list[Abstract | Device] = []
        for link in linked:
            for terminals in link:
                parent = terminals.parent

                if isinstance(parent, Domain) or parent in parts:
                    continue

                if isinstance(parent, Abstract):
                    cls.local_topology(parent)
                    parts.append(parent)
                    continue

                elif isinstance(parent, Device):
                    cls.construct_device(parent)
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
            return

        name = "NGspiceInterpreter"
        msg = f"Not all terminals are connected, {terminals!r} needs to be connected"
        raise RendererError(msg)

    @classmethod
    def local_topology(cls, topology: Abstract):
        """ Interprets local abstract topology """
        return

    @classmethod
    def construct_device(cls, device: Device):
        """ Constructs a device within the simulation domain """
        return

    @classmethod
    def construct_component(cls, component: Component):
        """ Constructs a component within the simulation domain """
        return