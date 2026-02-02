"""
Filename: renderer_interface.py
Author: William Bowley

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

from pyfea.domain.units import Quality
from pyfea.domain.geometry.domain import Domain
from pyfea.domain.geometry.definitions import CoordinateSystem


class BaseRenderer(ABC):
    """ Core interface for all solver renderers """
        
    @abstractmethod
    def _setup(
        self,
        file_path: Path,
        system: CoordinateSystem,
    ) -> Any:
        """ Setups the rendering environment for coordinate system in file_path """
    
    @abstractmethod
    def _draw_domain(self, domain: Domain) -> None:
        """ Defines the domain and than draws the elements within """
        
    @abstractmethod
    def move_element(
        self, element_id: Quality, magnitude: Quality, angles: Quality
    ) -> None:
        """ Moves an element within the simulation domain """
    
    @abstractmethod
    def rotate_element(
        self, element_id: Quality, axis: Quality, angles: Quality
    ) -> None:
        """ Rotates an element around an axis in the simulation domain """
    
    
    @abstractmethod
    def _clean_up(self) -> None:
        """ Removes any temporary files and closes the renderer """
    
    def move_elements(
        self, element_ids: tuple[Quality], magnitude: Quality, angles: Quality
    ) -> None:
        """ Moves a series of element within the simulation domain """
        for element in element_ids:
            self.move_element(element, magnitude, angles)
    
    def rotate_elements(
        self, element_ids: tuple[Quality], axis: Quality, angles: Quality
    ) -> None:
        """ Rotates a series of element around an axis in the simulation domain """
        for element in element_ids:
            self.rotate_element(element, axis, angles)
            
            
class MagneticRenderer(BaseRenderer, ABC):
    """ Renderer interface for magnetic problems """
    @abstractmethod
    def create_circuit(self, circuit: Any) -> Any:
        """ Creates a circuit within the simulation domain """
        """ NOTE: Haven't added the circuit modules yet for PYFEA """
        
    @abstractmethod
    def update_current(self, circuit: Any, current: Quality) -> Any:
        """ Changes the current within a circuit element """
        """ NOTE: Haven't added the circuit modules yet for PYFEA """


class HeatRenderer(BaseRenderer, ABC):
    """ Renderer interface for heat problems """
    @abstractmethod
    def add_volumetric_heat_source(
        self, element: Quality, magnitude: Quality
    ) -> Any:
        """ Adds a volumetric heat source to a element within the simulation domain """
    
    @abstractmethod
    def update_heat_source(self, element: Quality, magnitude: Quality) -> Any:
        """ Updates a volumetric heat source within the simulation domain """
    

class ElectricRenderer(BaseRenderer, ABC):
    """ Renderer interface for electric problems """
    # Placeholder for future electric-specific methods
    # Setting electric circuits (conductors), changing voltage, etc
