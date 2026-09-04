# pylint: skip-file
# # pyfea/solver/__init__.py

from pyfea.adaptors.interfaces.outputs import SolverRequests
from pyfea.adaptors.interfaces.outputs import ImageOptions, CircuitOptions, MagneticOptions, ThermalOptions

# References pyfea output classes
_ = SolverRequests
_, _, _, _ = ImageOptions, CircuitOptions, ThermalOptions, MagneticOptions