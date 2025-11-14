# Blueshark/models/tubular_linear_motor/simulate/__init__.py

from .static_analysis import get_magnet_flux, get_phase_values, get_force

__all__ = [
    "get_magnet_flux",
    "get_phase_values",
    "get_force"
]
