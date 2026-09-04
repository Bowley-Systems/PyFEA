# pylint: skip-file
# domain/__init__.py

from pyfea.core.geometry.builder import Builder as GBuilder
from pyfea.core.geometry.elements.metadata import MagneticData

from pyfea.core.materials.manager import Materials

from pyfea.core.circuits.builder import Builder as Cbuilder, Configuration

from pyfea.core.geometry.domain import Domain, BoundaryType, CoordinateSystem

# References pyfea geometric primitives
_, _ = GBuilder, MagneticData

# Reference pyfea material primitives
_ = Materials

# References pyfea circuit primitives
_, _ = Cbuilder, Configuration

# References pyfea domain primitives
_, _, _ = Domain, BoundaryType, CoordinateSystem