"""
File: unit_physics.py
Author: William Bowley
Version: 1.4
Date: 2025-09-13

Description:
    Tests functions within domain/physics
"""

import unittest

from blueshark.domain.constants import PRECISION
from blueshark.domain.physics.thermal import calculate_volumetric_heating
from blueshark.domain.physics.ripple import (
    ripple_peak_to_peak,
    ripple_percent,
    ripple_rms
)


test_series = [55, 10, 52, 18, 58, 77, 64, 16, 72, 45]


class RippleSeries(unittest.TestCase):
    """
    Tests the different ripple series
    """
    def test_peak_to_peak(self) -> None:
        """
        Tests peak to peak ripple analysis using the test
        series
        """
        expected = 77 - 10
        result = ripple_peak_to_peak(test_series)
        self.assertEqual(expected, result)

    def test_percent(self) -> None:
        """
        Tests percent ripple analysis using the test series
        """
        expected = round(((77 - 10) / 46.7) * 100, PRECISION)
        result = ripple_percent(test_series)
        self.assertEqual(expected, result)

    def test_rms(self) -> None:
        """
        Tests rms ripple analysis using the test series
        """
        expected = 22.799342095771
        result = ripple_rms(test_series)
        self.assertEqual(expected, result)

    def invalid_peak_to_peak(self) -> None:
        """
        No series input to test error handling
        """
        with self.assertRaises(ValueError):
            ripple_peak_to_peak([])

    def invalid_rms(self) -> None:
        """
        Series of strings to test error handling
        """
        series = ["I", "d", "e", "k"]

        with self.assertRaises(ValueError):
            ripple_peak_to_peak(series)
            

class VolumetricHeating(unittest.TestCase):
    """
    Test volumetric heating function
    """
    def test_standard_heating_problem(self) -> None:
        """
        Tests with standard in range values
        """
        current = 10
        resistance = 2
        volume = 10

        expected = (100*2) / 10
        result = calculate_volumetric_heating(
            current,
            resistance,
            volume
        )
        self.assertEqual(expected, result)

    def test_zero_case(self) -> None:
        """
        Test for zero case when current is zero
        """
        current = 0
        resistance = 2
        volume = 10

        expected = 0
        result = calculate_volumetric_heating(
            current,
            resistance,
            volume
        )
        self.assertEqual(expected, result)

    def test_invalid_volume(self) -> None:
        """
        Test with negative volume
        """
        current = 10
        resistance = 2
        volume = -10

        with self.assertRaises(ValueError):
            calculate_volumetric_heating(
                current,
                resistance,
                volume
            )
