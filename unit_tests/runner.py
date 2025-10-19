"""
File: run_tests.py
Author: William Bowley
Version: 1.3
Date: 2025-08-12

Description:
    Runs tests:
    - domain/test_generation
    - domain/test_physics
    - domain/test_material_manager
"""

import unittest
import domain.test_geometry as test_gen
import domain.test_physics as test_phy
import domain.test_material_manager as test_mm

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Domain/test_geometry
suite.addTests(loader.loadTestsFromTestCase(test_gen.ShapeArea))
suite.addTests(loader.loadTestsFromTestCase(test_gen.GraphicalCentroid))
suite.addTests(loader.loadTestsFromTestCase(test_gen.ValidateShape))
suite.addTests(loader.loadTestsFromTestCase(test_gen.MidPoints))
suite.addTests(loader.loadTestsFromTestCase(test_gen.FindCenterArc))
suite.addTests(loader.loadTestsFromTestCase(test_gen.ScalePolygon))
suite.addTests(loader.loadTestsFromTestCase(test_gen.ScaleGeometry))

# domain/test_physics
suite.addTests(loader.loadTestsFromTestCase(test_phy.ConvertMeters))
suite.addTests(loader.loadTestsFromTestCase(test_phy.ConvertSquareMeters))
suite.addTests(loader.loadTestsFromTestCase(test_phy.RippleSeries))

# domain/test_material_manager
suite.addTests(loader.loadTestsFromTestCase(test_mm.ManagerTest))

runner = unittest.TextTestRunner(verbosity=2)

if __name__ == "__main__":
    result = runner.run(suite)
