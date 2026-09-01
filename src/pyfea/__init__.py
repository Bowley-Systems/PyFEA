# pylint: skip-file
# pyfea/__init__.py

import logging
from pathlib import Path
from os import getcwd
from importlib import resources

from abc import ABC, abstractmethod
from dataclasses import fields

from pyfea.domain.units import *


try:
    # Attempts to inject the unit frame & imports derived units
    library = resources.files("library")

    inject_unit_frame(library / ".picounits")
    Parser.import_derived(library / "si_metric.ut")

except Exception as e:
    print(f"Warning: failed to load derived units: {e}")


def _setup_logging(path: Path = None) -> None:
    """ Sets up logging configuration for the package """
    if path is None: 
        # Adds `pyfea.log` to working directory
        path = Path(getcwd()) / "pyfea.log"

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        # Handles non-configured root logging
        logging.basicConfig(
            filename=path,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filemode="a",
        )

        root_logger.info("Logging has been configured at %s", path)


# Unit boundary class "Validate Boundary"
class SystemBoundary(ABC):
    """ Unit boundary checking for dataclass construction""" 
    def validate_units(self) -> None:
        """ Generic validator that uses field metadata """
        for f in fields(self):
            required_unit = f.metadata.get(Q)
            if required_unit is None:
                continue

            attribute = getattr(self, f.name)
            if attribute is None:
                return

            if not isinstance(attribute, Q):
                msg = f"{f.name!r} must be a quantity, not {type(attribute)}"
                raise TypeError(msg)

            if attribute.unit != required_unit:
                msg = f"{f.name!r} must be {required_unit} not {attribute.unit}"
                raise UnitError(msg)

    @property
    @abstractmethod
    def _name(self) -> str:
        """ Constructs a name based on attributes """

    def __post_init__(self) -> None:
        """ Pipes users input variables into validation schema """
        self.validate_units()

    def __repr__(self) -> str:
        """ Returns the dataclasses name """""
        return self._name

    def __str__(self) -> str:
        """ Returns the dataclasses name """
        return self._name


# Begins logging to `pyfea.log`
_setup_logging()
