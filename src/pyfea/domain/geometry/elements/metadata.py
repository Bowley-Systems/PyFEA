"""
Filename: metadata.py
Description:
    Defines the dataclasses for 
    different types of metadata
"""

from dataclasses import dataclass

from pyfea import dimensionless, meter, Quantity, Material
from pyfea.domain.geometry.definitions import GeometryDimensionError


@dataclass(slots=True)
class MagneticData:
    """ Construct solid geometry node between two objects """
    group: Quantity
    material: Material
    circuit: str = None
    turns: Quantity = None
    diameter: Quantity = None

    def __post_init__(self) -> None:
        """ Validates that metadata dimensions """
        if not isinstance(self.material, Material):
            msg = f"Material must be a Material, not {type(self.material)}"
            raise ValueError(msg)

        if not isinstance(self.group, Quantity):
            msg = f"Group must be a Quantity not, {type(self.group)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if not isinstance(self.circuit, str) and self.circuit is not None:
            msg = f"Circuit must be str, not {type(self.circuit)}"
            raise ValueError(msg)
    
        if not isinstance(self.diameter, Quantity) and self.diameter is not None:
            msg = f"Diameter must be a Quantity not, {type(self.group)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if not isinstance(self.turns, Quantity) and self.turns is not None:
            msg = f"Turns must be a Quantity not, {type(self.group)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.group.unit != dimensionless:
            msg = f"Group must be a dimensionless not, {self.group.unit}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.diameter is not None:

            if self.diameter.unit != meter:
                msg = f"Diameter must have unit {meter} not, {self.group.unit}"
                raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.turns is not None:
            if self.turns.unit != dimensionless:
                msg = f"Turns must be a dimensionless not, {self.group.unit}"
                raise GeometryDimensionError(self.__class__.__name__, msg)

    @property
    def _name(self) -> str:
        """ Returns its name as the auto definition """
        return (
            f"<Metadata=(group={self.group}, material={self.material}, "
            f"circuit={self.circuit}, turns={self.turns})>"
        )

    def __str__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name

    def __repr__(self) -> str:
        """ Returns the points name from Metadata.type """
        return self._name
