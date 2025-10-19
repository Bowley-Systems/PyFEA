# Blueshark/models/tubular_linear_motor/simulate/__init__.py

from .dynamic_analysis import run_dynamic
from .static_analysis import get_magnet_flux, get_phase_values

__all__ = [
    "run_dynamic",
    "get_magnet_flux",
    "get_phase_values"
]
