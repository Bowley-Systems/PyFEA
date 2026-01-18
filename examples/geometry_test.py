from picounits.constants import MILLI, LENGTH, DIMENSIONLESS
from pyfea.domain.geometry.builder import GeometryBuilder
from pyfea.domain.geometry.elements.parts import Metadata

Builder = GeometryBuilder
MM = 1 * MILLI * LENGTH

iron_square = Builder.create_rectangle((-1 * MM, -2.5 * MM), 3 * MM, 7.5 * MM)
iron_cutout = Builder.create_rectangle(
    (-0.75 * MM, -2.25 * MM), 2 * MM, 6.50 * MM
)

core = iron_square.subtract(iron_cutout)
core_part = Builder.promote_to_part(
    core, Metadata(1 * DIMENSIONLESS, "Copper", "phase A", 120 * DIMENSIONLESS)
)
print(core_part)