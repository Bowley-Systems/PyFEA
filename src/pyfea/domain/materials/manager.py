"""
Filename: manager.py

Description:
    Manages material request from the renderers
    and enforces specific parameters for material types.
"""


from typing import Optional, Any
from pathlib import Path
from importlib import resources

from pyfea import DynamicLoader
from pyfea.domain.units import MaterialParser


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
        self.material_library: DynamicLoader = None
        self.materials: dict[str, DynamicLoader] = {}
        self.path_name = "library/material.uiv"

        if library_path is None:
            self._load_from_package()

        else:
            self._load_from_path(Path(library_path))
            self.path_name = library_path


    def use_material(self, name: str, **params: Any) -> DynamicLoader:
        """ Retrieve a material by name and apply required parameters """
        material = self.material_library.find(name)

        if not material:
            msg = f"Cannot find material {name!r} in {self.path_name!r}"
            raise MaterialManagerError(msg)

        material_tag = material.meta.type
        match material_tag:
            case "magnet_material":
                if "grade" not in params:
                    msg = f"Material {name!r} requires parameter 'grade'"
                    raise MaterialManagerError(msg)

                grade_value = params["grade"]
                if not isinstance(grade_value, str):
                    msg = f"'grade' must be a string not {type(grade_value)}"
                    raise MaterialManagerError(msg)

                try:
                    grade = material.grades.find(grade_value)
                    if grade is None:
                        msg = "Grade not found within material library"
                        raise MaterialManagerError(msg) from None

                    coercivity, remanence = grade[0], grade[1]

                    material.magnetic.remanence = remanence
                    material.magnetic.coercivity = coercivity

                except Exception:
                    msg = "Failed to extract grade values for magnetic material"
                    raise MaterialManagerError(msg) from None

        self.materials[name] = material
        return material

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            library = resources.files("library")
            materials_path = library / "materials.uiv"

            self.material_library = MaterialParser.open(materials_path)

        except Exception as err:
            msg = f"Failed to load library from package resources: {err}"
            raise MaterialManagerError(msg) from None

    def _load_from_path(self, file_path: Path) -> None:
        """ Loads the user material library from path """
        try:
            self.material_library = MaterialParser.open(file_path)

        except Exception as err:
            msg = f"""Failed to load library from {file_path!r}: {err}"""
            raise MaterialManagerError(msg) from None
