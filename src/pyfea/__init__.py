# pylint: skip-file
# pyfea/__init__.py

from logging import getLogger, basicConfig, INFO
from os import getcwd
from pathlib import Path
from importlib import resources

from pyfea.domain.units import *
from pyfea.utilities.boundaries import SystemBoundary

# Reference different pyfea primitives
_ = SystemBoundary


# Attempts to inject the unit frame & imports derived units
try:
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

    root_logger = getLogger()
    if not root_logger.handlers:
        # Handles non-configured logger
        format = "%(asctime)s - %(levelname)s - %(message)s"
        basicConfig(filename=path, level=INFO, format=format, filemode="a",)
        root_logger.info("Logging has been configured at %s", path)


# Begins logging to `pyfea.log`
_setup_logging()
