# pylint: skip-file
# domain/__init__.py

from pyfea.domain.geometry.builder import Builder as GBuilder
from pyfea.domain.geometry.elements.metadata import MagneticData

from pyfea.domain.materials.manager import Materials

from pyfea.domain.circuits.builder import Builder as Cbuilder, Configuration

from pyfea.domain.geometry.domain import Domain, BoundaryType, CoordinateSystem

# References pyfea geometric primitives
_, _ = GBuilder, MagneticData

# Reference pyfea material primitives
_ = Materials

# References pyfea circuit primitives
_, _ = Cbuilder, Configuration

# References pyfea domain primitives
_, _, _ = Domain, BoundaryType, CoordinateSystem