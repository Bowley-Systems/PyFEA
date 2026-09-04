# pylint: skip-file
# # pyfea/solver/__init__.py

from pyfea.adaptors.interfaces.solutions import SolverRequests
from pyfea.adaptors.interfaces.requests import CircuitOptions, MagneticOptions, ThermalOptions

# References pyfea output classes
_ = SolverRequests
_, _, _ = CircuitOptions, ThermalOptions, MagneticOptions