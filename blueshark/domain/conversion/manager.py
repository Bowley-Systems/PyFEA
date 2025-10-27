"""
Filename: manager.py
Author: William Bowley
Version: 0.1
Date: 2025-10-23

Description:
    Converts different size units within the framework.
    Also validates that the units are the same

    These are independent of specific renderer/
    solver implementations.
"""

from blueshark.domain.units import Unit


def _valid_conversion(old: Unit, new: Unit) -> None:
    """ Validates that the two units are compatible for conversion. """

    # Check for same length between units
    if len(old.dims) != len(new.dims):
        raise ValueError("The units don't have the same length")

    # Check correctness between units
    old_lookup = {(dim.base, dim.exponent): dim for dim in old.dims}
    new_lookup = {(dim.base, dim.exponent): dim for dim in new.dims}
    if old_lookup.keys() != new_lookup.keys():
        msg = f"Units are not compatible between {new} : {old}"
        raise ValueError(msg)


def _computes_scale(old: Unit, new: Unit) -> float:
    """
    Compute the conversion factor for converting from `old` to `new` unit
    """
    lookup = {(dim.base, dim.exponent): dim for dim in new.dims}
    factor = 1.0

    for old_dim in old.dims:
        key = (old_dim.base, old_dim.exponent)
        new_dim = lookup[key]

        # Calculates the prefix difference
        # Ex. Base (0) - Kilo (3) = -3 Hence base exponent of -3
        prefix_diff = old_dim.prefix.value - new_dim.prefix.value

        # Scales the prefix_diff by the base exponent
        total_exponent = prefix_diff * old_dim.exponent
        factor *= 10 ** total_exponent

    return factor


def conversion(
    raw: float | int, old: Unit, new: Unit
) -> tuple[float | int, Unit]:
    """ Convert a numeric value from `old` unit to `new` unit. """

    _valid_conversion(old, new)
    factor = _computes_scale(old, new)

    return raw * factor, new


def valid_unit(
    reference: Unit, result: Unit
) -> bool | None:
    """ Validates that the units are the same """
    # Check for same length between units
    if len(reference.dims) != len(result.dims):
        raise ValueError("The units don't have the same length")

    # Check correctness between units
    old_lookup = {
        (dim.base, dim.prefix, dim.exponent): dim for dim in reference.dims
    }
    new_lookup = {
        (dim.base, dim.prefix, dim.exponent): dim for dim in result.dims
    }

    if old_lookup.keys() != new_lookup.keys():
        msg = f"Units are not the same: {result} | {reference}"
        raise ValueError(msg)

    return True
