"""
File: manager.py
Author: William Bowley
Date: 02-02-2026

Description:
    Manages material request from the renderers
    and enforces specific parameters for material types.
"""


from typing import Optional, Any
from pathlib import Path
from importlib import resources

from pyfea.domain.units import Material, Parser

class MaterialManagerError(TypeError):
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
        self.materials: Material = None
        self.path_name = "library/material.uiv"

        if library_path is None:
            self._load_from_package()
        else:
            self._load_from_path(Path(library_path))
            self.path_name = library_path


    def use_material(self, name: str, **params: Any) -> Material:
        """ Retrieve a material by name and apply required parameters """
        material = self.materials.find(name)

        if not material.occupied:
            msg = f"Cannot find material {name!r} in {self.path_name!r}"
            raise MaterialManagerError(msg)

        """
        Need to add logic for applying required parameters such as magnet grade
        """
        _ = params

        return material

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            with resources.open_text("library", "materials.uiv") as f:
                self.materials = Parser.open(f)

        except Exception as err:
            msg = f"""Failed to load library from package resources: {err}"""
            raise MaterialManagerError(msg) from None

    def _load_from_path(self, file_path: Path) -> None:
        """ Loads the user material library from path """
        try:
            self.materials = Parser.open(file_path)

        except Exception as err:
            msg = f"""Failed to load library from {file_path!r}: {err}"""
            raise MaterialManagerError(msg) from None
