"""
Filename: manager.py

Description:
    Manages static material definitions for
    problem construction.
"""

from typing import Any
from importlib import resources

from pyfea.domain.units import Parser, DynamicLoader
from pyfea.utilities.errors import MaterialError


class MaterialManager:
    """ Manages static material definitions from library """
    def __init__(self) -> None:
        """ Initialization of the material manager """
        self.material_library: DynamicLoader = None

        # Loads the package library
        self._load_from_package()

    def display_materials(self) -> None:
        """ Displays the materials tree to the user. """
        if isinstance(self.material_library, DynamicLoader):
            self.material_library.info()

        msg = "Failed to display material tree due to loading error."
        raise MaterialError("MaterialManager", msg)

    def use_material(self, name: str, **params: Any) -> DynamicLoader:
        """ Retrieve a material by name and applies required parameters """
        _, _ = name, params
        return

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            library = resources.files("library")
            materials_path = library / "materials.uiv"

            self.material_library = Parser.open(materials_path)

        except Exception as err:
            msg = f"Failed to load library from package resources: {err}"
            raise MaterialError("MaterialManager", msg) from err
