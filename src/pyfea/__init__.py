# pyfea/__init__.py

import logging

from pathlib import Path
from os import getcwd

from pyfea.domain.units import *


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
