"""
File: number_turns.py
Author: William Bowley
Version: 1.3
Date: 2025-09-15
Description:
    Utility function to estimate the number of turns in rectangular
    or square slot/coils.
"""

import logging
from math import ceil


def estimate_turns(
    length: float,
    height: float,
    wire_diameter: float,
    fill_factor: float = 0.7
) -> int:
    """
    Estimate the number of turns that can fit in a
    rectangular or square slot/coil.

    Args:
        length: Slot length.
        height: Slot height.
        wire_diameter: Diameter of the wire including insulation (mm).
        fill_factor: Fraction of slot area filled by copper; Default 0.7

    Returns:
        int: Estimated number of turns.
    """
    if length <= 0 or height <= 0 or wire_diameter <= 0:
        msg = "All dimensions must be positive and non-zero."
        logging.error(msg)
        raise ValueError(msg)

    if not (0 < fill_factor <= 1):
        msg = "Fill factor must be between 0 and 1."
        logging.error(msg)
        raise ValueError(msg)

    slot_area = length * height
    wire_area = wire_diameter ** 2
    effective_area = slot_area * fill_factor

    turns = effective_area / wire_area
    return ceil(turns)
