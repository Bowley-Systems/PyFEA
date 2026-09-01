"""
Filename: manager.py

Description:
    Manages static material definitions for
    problem construction.
"""


from typing import Any
from importlib import resources

from pyfea.domain.units import Parser, DynamicLoader, inject_unit_frame
from pyfea.utilities.errors import MaterialError


class _MaterialManager:
    """ Manages static material definitions from library """
    def __init__(self) -> None:
        """ Initialization of the material manager """
        self._library: DynamicLoader = None

        # Loads the package library & attaches attributes
        self._load_from_package()
        self._import_attributes()

    def display_materials(self) -> None:
        """ Displays the materials tree to the user. """
        if isinstance(self._library, DynamicLoader):
            self._library.info("Materials")
            return

        msg = "Failed to display material tree due to library loading error."
        raise MaterialError("MaterialManager", msg)

    def _import_attributes(self) -> None:
        """ Imports all attributes from Library """
        if self._library is None:
            return

        for name in dir(self._library):
            if name.startswith('_') or name.startswith('lx_'):
                # Skips private/magic attributes and loader internals
                continue

            try:
                # Set it as an attribute on this instance
                node = getattr(self._library, name)
                setattr(self, name, node)

            except AttributeError:
                # Attempts to set next attribute
                continue

    def __getattr__(self, key: str) -> Any:
        """ Allows dynamic attribute accesses """
        msg = f"{key!r} not found within material library."
        raise MaterialError("MaterialManager", msg)

    def _load_from_package(self) -> None:
        """ Loads the default material library """
        try:
            library = resources.files("library")
            materials_path = library / "materials.uiv"

            inject_unit_frame(library / ".picounits")
            Parser.import_derived(library / "si_metric.ut")

            self._library = Parser.open(materials_path)

        except Exception as err:
            msg = f"Failed to load library from package resources: {err}"
            raise MaterialError("MaterialManager", msg) from err


# Initializes the global reference
Materials = _MaterialManager()
