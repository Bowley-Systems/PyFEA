# Blueshark/models/coilgun_multi_stage/physics/__init__.py

from .physics import dc_resistance
from .number_turns import estimate_turns

__all__ = [
    "dc_resistance",
    "estimate_turns"
]
