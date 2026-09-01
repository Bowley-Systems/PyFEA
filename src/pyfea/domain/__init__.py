# pylint: skip-file
# domain/__init__.py

from pyfea.domain.geometry.builder import Builder as GBuilder
from pyfea.domain.geometry.elements.metadata import MagneticData


# References pyfea geometric primitives
_, _ = GBuilder, MagneticData