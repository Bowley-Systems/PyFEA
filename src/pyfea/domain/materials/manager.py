"""
File: manager.py
Author: William Bowley
Version: 1.6

Description:
    Manages material request from the renderers
    and enforces specific parameters for material types.
"""


from typing import Optional
from importlib import resources

from picounits.extensions.parser import Parser
from picounits.extensions.loader import DynamicLoader

class MaterialLoadError(TypeError):
    """ Exception for Material Loader Error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class MaterialManager:
    """
    Manages material (STATIC definitions) for the user.
    Enforces specific parameters, keeps track of used materials

    NOTE:
        This manager handles only static material definitions.
        Do Not attempt to modify simulation-specific dynamic properties
        here those must be managed within the renderer.
    """
    def __init__(self, library_path: Optional[str] = None) -> None:
        """ Initialization of the material manager """
        self.used_materials: list[DynamicLoader] = []
        self.parsed_materials: DynamicLoader = None

        if library_path is None:
            # Loads default materials.uiv library
            self._load_from_package()
        else:
            # Loads custom user material library
            return None

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            with resources.open_text("library", "materials.uiv") as f:
                self.materials = Parser.open(f)
        except Exception as err:
            msg = """Failed to load material library from package resources"""
            msg += f": {err}"
            raise MaterialLoadError(msg) from None


manager = MaterialManager()
