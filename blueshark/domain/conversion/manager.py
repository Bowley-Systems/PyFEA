"""
Filename: manager.py
Author: William Bowley
Version: 0.2
Date: 2025-12-02

Description:
    Converts different size units within the framework.
    Also validates that the units are the same

    These are independent of specific renderer/
    solver implementations.
"""

from dataclasses import dataclass
from blueshark.domain.units import Unit, Dimension, DIMENSIONLESS


def _combine_unit(first: Unit, second: Unit, division: bool = False) -> Unit:
    """ Combines or divides two units via their dimension exponents """
    combined_dims = {}
    for dim in first.dims:
        key = dim.base
        combined_dims[key] = (dim.prefix, dim.exponent)

    for dim in second.dims:
        key = dim.base
        exponent_change = dim.exponent * (-1 if division else 1)

        if key in combined_dims:
            prefix, current_exponent = combined_dims[key]
            new_exponent = current_exponent + exponent_change
            combined_dims[key] = (prefix, new_exponent)
        else:
            combined_dims[key] = (dim.prefix, dim.exponent) 

    # Removes dimensions who's exponent is zero within the rebuild unit
    new_dims = []
    for base, (prefix, exponent) in combined_dims.items():
        if exponent != 0:
            new_dims.append(
                Dimension(base=base, prefix=prefix, exponent=exponent)
            )

    # Handles dimensionless edge case
    return DIMENSIONLESS if not new_dims else Unit(*new_dims)


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


@dataclass
class PhysicalQuantity:
    """ Physical Quantity within the framework """
    value: float | int
    unit: Unit

    def to_unit(self, target_unit: Unit) -> float:
        """
        Converts the quantity to a target unit and returns only the value.
        """
        converted_value, _ = conversion(self.value, self.unit, target_unit)
        return converted_value

    def to_quantity(self, target_unit: Unit) -> 'PhysicalQuantity':
        """
        Converts the quantity to a target unit and
        returns a new Quantity object,
        """
        new_value, new_unit = conversion(self.value, self.unit, target_unit)
        return PhysicalQuantity(new_value, new_unit)

    def _get_other_quantity(self, other):
        """ Checking other quantity method for arithmetic methods """
        if not isinstance(other, PhysicalQuantity):
            return PhysicalQuantity(other, DIMENSIONLESS)

        return other

    # Dunder methods for forward/reverse arithmetic and others

    def __add__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the addition operator (+)."""
        other = self._get_other_quantity(other)

        # Unit addition scaling
        _valid_conversion(self.unit, other.unit)
        converted_other_value = other.to_unit(self.unit)

        new_value = self.value + converted_other_value
        return PhysicalQuantity(new_value, self.unit)

    def __sub__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the subtraction operator (-)."""
        other = self._get_other_quantity(other)

        # Unit subtraction scaling
        _valid_conversion(self.unit, other.unit)
        converted_other_value = other.to_unit(self.unit)

        new_value = self.value - converted_other_value
        return PhysicalQuantity(new_value, self.unit)

    def __mul__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the multiplication operator (*)."""
        other = self._get_other_quantity(other)
        new_value = self.value * other.value
        new_unit = _combine_unit(self.unit, other.unit)

        return PhysicalQuantity(new_value, new_unit)

    def __truediv__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the true division operator (/)."""
        other = self._get_other_quantity(other)
        if other.value == 0:
            raise ZeroDivisionError(
                "Cannot divide a PhysicalQuantity by zero."
            )
        new_value = self.value / other.value
        new_unit = _combine_unit(self.unit, other.unit, True)

        return PhysicalQuantity(new_value, new_unit)

    def __floordiv__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the floor division operator (//)."""
        other = self._get_other_quantity(other)
        if other.value == 0:
            raise ZeroDivisionError(
                "Cannot floor-divide a PhysicalQuantity by zero."
            )
        new_value = self.value // other.value
        new_unit = _combine_unit(self.unit, other.unit, True)

        return PhysicalQuantity(new_value, new_unit)

    def __mod__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the modulo operator (%)."""
        other = self._get_other_quantity(other)
        if other.value == 0:
            raise ZeroDivisionError(
                "Cannot use modulo operator with PhysicalQuantity of zero."
            )

        if other.unit is not DIMENSIONLESS:
            raise TypeError(
                "Cannot perform modulo operator when both "
                "qualities are have dimensions"
            )

        new_value = self.value % other.value
        return PhysicalQuantity(new_value, self.unit)

    def __pow__(self, other: 'PhysicalQuantity'):
        """Defines behavior for the power operator (**)."""
        other = self._get_other_quantity(other)
        if other.unit is not DIMENSIONLESS:
            raise TypeError(
                "Cannot perform power operator when both "
                "qualities are have dimensions"
            )

        new_value = self.value ** other.value
        return PhysicalQuantity(new_value, self.unit)

    def __radd__(self, other):
        """ Defines behavior for right-hand addition (other + self). """
        return self.__add__(other)

    def __rsub__(self, other):
        """ Defines behavior for right-hand subtraction (other - self). """

        # Promote 'other' to a same dimensional Quantity.
        other_q = PhysicalQuantity(other, self.unit)
        return other_q.__sub__(self)

    def __rmul__(self, other):
        """ Defines behavior for right-hand multiplication (other * self). """
        return self.__mul__(other)

    def __rtruediv__(self, other):
        """ Defines behavior for right-hand true division (other / self). """

        # Promote 'other' to a dimensionless Quantity.
        other_q = PhysicalQuantity(other, DIMENSIONLESS)
        return other_q.__truediv__(self)

    def __rfloordiv__(self, other: float | int):
        """
        Defines behavior for right-hand floor division (other // self).
        """
        # Promote 'other' to a dimensionless Quantity.
        other_q = PhysicalQuantity(other, DIMENSIONLESS)
        return other_q.__floordiv__(self)

    def __rmod__(self, other: float | int):
        """
        Defines behavior for right-hand modulo (other % self).
        """
        # Promote 'other' to a dimensionless Quantity.
        other_q = PhysicalQuantity(other, DIMENSIONLESS)
        return other_q.__mod__(self)

    def __rpow__(self, other: float | int):
        """
        Defines behavior for right-hand power (other ** self).
        """
        # Promote 'other' to a dimensionless Quantity.
        other_q = PhysicalQuantity(other, DIMENSIONLESS)
        return other_q.__pow__(self)

    def __round__(self, n=0):
        """Defines behavior for the built-in round() function."""
        new_value = round(self.value, n)
        return PhysicalQuantity(new_value, self.unit)

    def __repr__(self) -> str:
        """ Formatted physical quantity representation. """
        return f"{self.value} {self.unit}"
