"""
File: geometry_test.py
Author: William Bowley
Version: 0.1
Description:
    Script for testing features as their built out
    in pyfea
"""
from pyfea import millimeter as mm, dimensionless
from pyfea.domain.materials.manager import MaterialManager
from pyfea.domain.geometry.builder import Builder
from pyfea.domain.geometry.elements.metadata import MagneticData
from pyfea.domain.geometry.domain import Domain, BoundaryType

# Pulls materials into the script from package library
manager = MaterialManager()
iron = manager.use_material("pure_iron")
copper = manager.use_material("pure_copper")
stc_air = manager.use_material("stc_air")

# Builds the transformer core
iron_square = Builder.create_rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
iron_cutout = Builder.create_rectangle((15 * mm, 20 * mm), 85 * mm, 60 * mm)

core = iron_square.subtract(iron_cutout)
core = Builder.promote_to_part(core, MagneticData(1 * dimensionless, iron))

# Positive coil slot
positive_slot = Builder.create_rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = Builder.promote_to_part(
    positive_slot, 
    MagneticData(2 * dimensionless, copper, "Phase A", 100 * dimensionless, 0.1 * mm)
)

# Negative coil slot
negative_slot = Builder.create_rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = Builder.promote_to_part(
    negative_slot, 
    MagneticData(2 * dimensionless, copper, "Phase A", -100 * dimensionless, 0.1 * mm)
)

# Defines problem domain
domain_shape = Builder.create_circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)

simulation_domain = Domain(
     (positive_slot, negative_slot, core), 
    3 * dimensionless, BoundaryType.NEUMANN, stc_air, domain_shape
)

print(simulation_domain)