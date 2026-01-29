"""
File: manager.py
Author: William Bowley
Version: 1.5

Description:
    Manages material request from the renderers
    and enforces specific parameters for material types.

    NOTE:
        Material manager is independent of specific renderer/
        solver implementations.

        This manager handles only static material definitions.
        Do Not attempt to modify simulation-specific dynamic properties
        here those must be managed within the renderer.
"""


from typing import Optional, Any
from importlib import resources

from picounits.extensions.parser import Parser



class MaterialManager:
    """
    Manages material (STATIC definitions) for the user.
    Enforces specific parameters, keeps track of used materials

    Note:
        This manager does NOT track simulation-specific dynamic properties
        - e.g: volumetric_heat_source, current_density, or temperature.
    """
    def __init__(
        self,
        library_path: Optional[str] = None
    ) -> None:
        """
        Initialization of the material manager

        Args:
            library_path: Optional path to an external material library (TOML)
        """
        self.used_materials: list[str] = []
        self.materials: dict[str, dict[str, Any]] = {}
        
        