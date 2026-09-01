"""
Filename: manager.py

Description:
    Manages static material definitions for
    problem construction.
"""

from typing import Any
from importlib import resources

from pyfea import DynamicLoader
from pyfea.domain.units import MaterialParser


_ = Any

class MaterialManagerError(TypeError):
    """ Exception for Material Loader Error """
    def __init__(self, error: str):
        """ Returns a custom error message """
        msg = f"raised error: {error}. "
        super().__init__(msg)


class MaterialManager:
    """ Manages static material definitions from library """
    def __init__(self) -> None:
        """ Initialization of the material manager """
        self.material_library: DynamicLoader = None
        self.materials: dict[str, DynamicLoader] = {}

        # Loads the package library
        self._load_from_package()

    def display_materials(self) -> None:
        """ Displays the materials tree to the user. """
        self.material_library.info()

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            library = resources.files("library")
            materials_path = library / "materials.uiv"

            self.material_library = MaterialParser.open(materials_path)

        except Exception as err:
            msg = f"Failed to load library from package resources: {err}"
            raise MaterialManagerError(msg) from None
