"""
Filename: metadata.py

Description:
    Defines the dataclasses for different types of metadata
    such as magnetic metadata which contains parameters like
    magnetization and diameter.
"""

from typing import Optional
from dataclasses import dataclass, field

from pyfea.domain.geometry.definitions import GeometryDimensionError
from pyfea.domain.circuits.builder import StaticCircuit

from pyfea import (
    Quantity as Q, Material, SystemBoundary, nullset, meter, watt, kelvin, h
)


@dataclass(slots=True)
class MagneticData(SystemBoundary):
    """ Defines magnetic properties for a geometry group """
    group:          Q                       = field(metadata={Q: nullset})
    material:       Material
    circuit:        Optional[StaticCircuit] = field(default=None, metadata={})
    turns:          Optional[Q]             = field(default=None, metadata={Q: nullset})
    diameter:       Optional[Q]             = field(default=None, metadata={Q: meter})
    magnetization:  Optional[Q]             = field(default=None, metadata={Q: nullset})

    def __post_init__(self) -> None:
        """ Validates that non-typed parameters are correct """
        if not isinstance(self.material, Material):
            msg = f"Material must be a Material, not {type(self.material)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.circuit is not None and not isinstance(self.circuit, StaticCircuit):
            msg = f"Circuit must be a Circuit, not {type(self.circuit)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        self.validate_units()

    @property
    def _name(self) -> str:
        return (
            f"<MagneticData=(group={self.group}, material={self.material}, "
            f"circuit={self.circuit}, turns={self.turns}, diameter={self.diameter})>"
        )


@dataclass(slots=True)
class ThermalData(SystemBoundary):
    """ Defines thermal properties and heat sources for a geometry group """
    group:                  Q           = field(metadata={Q: nullset})
    material:               Material
    heating_index:          Optional[Q] = field(default=None, metadata={})
    temperature:            Optional[Q] = field(default=None, metadata={Q: kelvin})
    heat_flow_value:        Optional[Q] = field(default=None, metadata={Q: watt})
    volumetric_heating:     Optional[Q] = field(default=None, metadata={Q:watt/meter**3})
    convection_coefficient: Optional[Q] = field(default=None, metadata={Q: h})
    ambient_temperature:    Optional[Q] = field(default=None, metadata={Q: kelvin})

    def __post_init__(self) -> None:
        if not isinstance(self.material, Material):
            msg = f"Material must be a Material, not {type(self.material)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        self.validate_units()

    @property
    def _name(self) -> str:
        return (
            f"<ThermalData=(group={self.group}, material={self.material}, "
            f"T={self.temperature}, Q_flow={self.heat_flow_value}, "
            f"Q_vol={self.volumetric_heating}, h={self.convection_coefficient}, "
            f"T_amb={self.ambient_temperature})>"
        )
