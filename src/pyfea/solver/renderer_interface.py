"""
Filename: renderer_interface.py
Description:
    Abstract base class which defines the interface for 
    solver renderers
    
    - BaseRenderer: Core generic methods for all renderers
    - MagneticRenderer: Magnetic-specific extensions
    - HeatRenderer: Heat-specific extensions
    - ElectricRenderer: Electric-specific extensions
"""

from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from pyfea.domain.units import Quantity, Material, strip_quantity
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.circuits.builder import Circuit


class RendererError(Exception):
    """ Exception for renderer Error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class BaseRenderer(ABC):
    """ Core interface for all solver renderers """
        
    @abstractmethod
    def __init__(self, file_path: Path) -> Any:
        """ Setups the rendering environment in file_path """
        self.file_path = file_path
    
    @abstractmethod
    def draw_domain(self, domain: Domain) -> None:
        """ Defines the domain and than draws the elements within """
        
    @abstractmethod
    def move_element(
        self, element_id: Quantity, magnitude: Quantity, angles: Quantity
    ) -> None:
        """ Moves an element within the simulation domain """
    
    @abstractmethod
    def rotate_element(
        self, element_id: Quantity, axis: Quantity, angles: Quantity
    ) -> None:
        """ Rotates an element around an axis in the simulation domain """
    
    @abstractmethod
    def _clean_up(self) -> None:
        """ Removes any temporary files and closes the renderer """

    def _file_path_exist(self) -> None:
        """ Checks to ensure the file path given by the solver exists """
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.touch(exist_ok=True)
    
        except Exception:
            msg = f"File path given to {self.__class__.__name__} invalid or inaccessible"
            raise RendererError(msg)

    def _strip_quantity(self, quantity: Quantity, ref: Quantity) -> Any:
        """ Strips quantity from value returns raw value """
        return strip_quantity(quantity, ref)
            

class MagneticRenderer(BaseRenderer, ABC):
    """ Renderer interface for magnetic problems """
    @abstractmethod
    def update_current(self, circuit: Circuit, current: Quantity) -> Any:
        """ Changes the current within a circuit element """

    @abstractmethod
    def update_temperature(
        self, material: Material, temperature: Quantity
    ) -> Any:
        """ Updates the materials based on temperature """

class ThermalRenderer(BaseRenderer, ABC):
    """ Renderer interface for thermal problems """
    @abstractmethod
    def update_volumetric_heat_source(self, material: Material, magnitude: Quantity) -> Any:
        """ Updates a volumetric heat source within the simulation domain """
    
    @abstractmethod
    def update_conductor_heat_source(self, element: Quantity, magnitude: Quantity) -> Any:
        """ Updates a conductor heat source within the simulation domain"""

class ElectricRenderer(BaseRenderer, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
