"""
Filename: metadata.py

Description:
    Defines the dataclasses for different types of metadata
    such as magnetic metadata which contains parameters like
    magnetization and diameter.
"""

from typing import Optional
from dataclasses import dataclass, field

from pyfea.domain.circuits.builder import StaticCircuit
from pyfea.utilities.errors import GeometryDimensionError

from pyfea.domain.units import Q, DynamicLoader, nullset, meter, watt, kelvin, h
from pyfea.utilities.boundaries import SystemBoundary


@dataclass(slots=True, eq=False)
class MagneticData(SystemBoundary):
    """ Defines magnetic properties for a geometry group """
    group:          Q                       = field(metadata={Q: nullset})
    material:       DynamicLoader
    circuit:        Optional[StaticCircuit] = field(default=None, metadata={})
    turns:          Optional[Q]             = field(default=None, metadata={Q: nullset})
    diameter:       Optional[Q]             = field(default=None, metadata={Q: meter})
    magnetization:  Optional[Q]             = field(default=None, metadata={Q: nullset})

    def __post_init__(self) -> None:
        """ Validates that non-typed parameters are correct """
        if not isinstance(self.material, DynamicLoader):
            msg = f"Material must be a Material, not {type(self.material)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        if self.circuit is not None and not isinstance(self.circuit, StaticCircuit):
            msg = f"Circuit must be a Circuit, not {type(self.circuit)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        self.validate_units()

    def __eq__(self, other: object) -> bool:
        """ Checks to see if both magnetic data are equivalent """
        if not isinstance(other, MagneticData):
            return NotImplemented
        return (
            self.group        == other.group
            and self.material == other.material
            and self.circuit  == other.circuit
            and self.turns    == other.turns
            and self.diameter == other.diameter
            and self.magnetization == other.magnetization
        )

    def __hash__(self) -> int:
        """ Hashes the metadata for use in lookup tables """
        return hash((
            self.group,
            self.material,
            self.circuit,
            self.turns,
            self.diameter,
            self.magnetization,
        ))

    @property
    def _name(self) -> str:
        return (
            f"<MagneticData=(group={self.group}, material={self.material}, "
            f"circuit={self.circuit}, turns={self.turns}, diameter={self.diameter})>"
        )


@dataclass(slots=True, eq=False)
class ThermalData(SystemBoundary):
    """ Defines thermal properties and heat sources for a geometry group """
    group:                  Q           = field(metadata={Q: nullset})
    material:               DynamicLoader
    heating_index:          Optional[Q] = field(default=None, metadata={})
    temperature:            Optional[Q] = field(default=None, metadata={Q: kelvin})
    heat_flow_value:        Optional[Q] = field(default=None, metadata={Q: watt})
    volumetric_heating:     Optional[Q] = field(default=None, metadata={Q:watt/meter**3})
    convection_coefficient: Optional[Q] = field(default=None, metadata={Q: h})
    ambient_temperature:    Optional[Q] = field(default=None, metadata={Q: kelvin})

    def __post_init__(self) -> None:
        if not isinstance(self.material, DynamicLoader):
            msg = f"Material must be a Material, not {type(self.material)}"
            raise GeometryDimensionError(self.__class__.__name__, msg)

        self.validate_units()

    def __eq__(self, other: object) -> bool:
        """ Hashes the metadata for use in lookup tables """
        if not isinstance(other, ThermalData):
            return NotImplemented
        return (
            self.group                  == other.group
            and self.material           == other.material
            and self.heating_index      == other.heating_index
            and self.temperature        == other.temperature
            and self.heat_flow_value    == other.heat_flow_value
            and self.volumetric_heating == other.volumetric_heating
            and self.convection_coefficient == other.convection_coefficient
            and self.ambient_temperature    == other.ambient_temperature
        )

    def __hash__(self) -> int:
        """ Hashes the metadata for use in lookup tables """
        return hash((
            self.group,
            self.material,
            self.heating_index,
            self.temperature,
            self.heat_flow_value,
            self.volumetric_heating,
            self.convection_coefficient,
            self.ambient_temperature,
        ))

    @property
    def _name(self) -> str:
        return (
            f"<ThermalData=(group={self.group}, material={self.material}, "
            f"T={self.temperature}, Q_flow={self.heat_flow_value}, "
            f"Q_vol={self.volumetric_heating}, h={self.convection_coefficient}, "
            f"T_amb={self.ambient_temperature})>"
        )
