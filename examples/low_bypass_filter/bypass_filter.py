"""
Filename: bypass_filter.py

Description:
    Lumped parameter low bypass filter simulation
    using ngspice via pyspice to calculate the
    frequency response.
    
    This example shows how pyfea can be used to 
    construct circuit without touching net-lists.
    
    NOTE:
    This is a concept file. Not runnable.
"""


from pyfea import volt, ohm, farad, k, u, K, Hz, M
from pyfea.domain.circuits import Configuration, Sources
from pyfea.domain.circuits.builder import Builder

from pyfea.solver.solver_outputs import SolverOutputs, CircuitOptions
from pyfea.solver.ngspice.solver import NGSpiceSolverAC


# Constructs components (source, capacitor, resistor)
source = Builder.source(Sources.AC, 1 * volt)
capacitor = Builder.capacitor(1 * u * farad, esr=0.1 * ohm)
resistor = Builder.resistor(1 * k * ohm)

# Construct geometric relations and circuit
branch = Builder.group(Configuration.SERIES, capacitor, resistor)
group = Builder.group(Configuration.NONE, branch, source)

circuit = Builder.domain(group, 298.15 * K, 298.15 * K)

# Defines requested outputs
outputs = SolverOutputs()
outputs.add_circuit(capacitor, CircuitOptions.gain)
outputs.add_circuit(capacitor, CircuitOptions.phase)

# Solves configured circuit
solver = NGSpiceSolverAC.setup(1 * u * Hz, 10 * M * Hz, samples=1000)
solution = solver.solve(outputs)

# Extract solution
phase_vs_frequency = outputs[capacitor].phase