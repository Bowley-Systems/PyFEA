# pyfea/__init__.py

import logging
from pathlib import Path
from os import getcwd

# --- ensure derived units are loaded globally ---
from importlib import resources
from picounits import unit_validator
from picounits.configuration.config import get_derived_units
from pyfea.domain.units import *


try:
    library = resources.files("library")
    derived_path = library / "si_metric.ut"

    # Adds derived units to pyfea
    get_derived_units(derived_file=Path(str(derived_path)))
except Exception as e:
    print(f"Warning: failed to load derived units: {e}")
# ---------------------------------------------------

def _setup_logging(path: Path = None) -> None:
    """ Sets up logging configuration for the package """

    if path is None:
        path = Path(getcwd()) / "pyfea.log"

    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            filename=path,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filemode="a",
        )

        root_logger.info("Logging has been configured at %s", path)


_setup_logging()
