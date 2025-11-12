"""
File: unpack.py
Author: William Bowley
Version: 0.1
Date: 2025-10-04

Description:
    Unpacks data from the .YAML file for the multi stage
    coil-gun to use later.

    NOTE:
        Handles only static parameter definitions.
        Specific dynamic definitions are handled by `main.py`
"""

import yaml
import logging
import pathlib

from typing import Any
from importlib import resources


class CoilGunUnpacker:
    """ Loads coil-gun parameters from YAML into class attributes """

    DEFAULT_FILE_NAME = "default.yaml"
    REQUIRED = [
        "output", "model", "boundary",
        "controller", "coil", "shell", "projectile"
    ]

    def __init__(
        self,
        parameter_file: str | None = None,
        debugging: bool = True
    ) -> None:
        """ Initializes the class and unpacks the .YAML file """
        if parameter_file is None:
            parameter_file = self.DEFAULT_FILE_NAME

        self.file = pathlib.Path(parameter_file)
        self.debugging = debugging

        if not self.file.exists():
            msg = (
                f"Parameter file `{self.file}` not found."
                f"Copying default coil-gun parameters from package"
            )
            logging.warning(msg)

            if self.debugging:
                print(msg)

            self._load_from_package()

        self._unpack(self.file)

    def _unpack(self, param_file: pathlib.Path) -> None:
        """ Main entry point: load YAML and dispatch to section unpackers """

        if not param_file.exists():
            msg = f"Parameter file '{param_file}' was not found."
            raise FileNotFoundError(msg)

        if param_file.suffix.lower() != ".yaml":
            msg = f"File '{param_file}' has wrong extension; expected '.yaml'"
            raise ValueError(msg)

        try:
            with open(param_file, "r", encoding="utf-8") as file:
                parameters = yaml.safe_load(file)
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML file '{param_file}' : {e}"
            raise ValueError(msg) from e

        # Required section from the .yaml file
        for section in self.REQUIRED:
            if section not in parameters:
                msg = f"Missing required key '{section}' in {param_file}"
                raise KeyError(msg)

        # Dispatched unpacking
        self._unpack_output(parameters["output"])
        self._unpack_model(parameters["model"])
        self._unpack_boundary(parameters["boundary"])
        self._unpack_controller(parameters["controller"])
        self._unpack_coil(parameters["coil"])
        self._unpack_shell(parameters["shell"])
        self._unpack_projectile(parameters["projectile"])

        # Calculated parameters
        self._calculated_parameters()

    def _unpack_output(self, output: dict) -> None:
        """ Unpacks values from the output section """
        self.folder_path = self._require("folder_path", output)
        self.file_name = self._require("file_name", output)

    def _unpack_model(self, model: dict) -> None:
        """ Unpacks values from the model section """
        self.stages = self._require("stages", model)
        self.stage_gap = self._require("stage_gap", model)
        self.time_step = self._require("time_step", model)
        self.test_current = self._require("test_current", model)
        self.atmospheric_density = self._require("atmospheric_density", model)

        if not isinstance(self.stages, int) or self.stages < 1:
            raise ValueError("stages must be a positive integer")

    def _unpack_boundary(self, boundary: dict) -> None:
        """ Unpacks values from the boundary section """
        self.boundary_material = self._require("boundary_material", boundary)
        self.boundary_shells = self._require("boundary_shells", boundary)

    def _unpack_controller(self, controller: dict) -> None:
        """ Unpacks values from the controller section """
        self.supply_voltage = self._require("supply_voltage", controller)
        self.current_limit = self._require("current_limit", controller)
        self.activate_fraction = self._require("activate_fraction", controller)
        self.deactivate_fraction = self._require(
            "deactivate_fraction", controller
        )

        if not (0.0 < self.activate_fraction < 1.0):
            raise ValueError("activate_fraction must be between 0.0 and 1.0")

        if not (0.0 < self.deactivate_fraction < 1.0):
            raise ValueError("deactivate_fraction must be between 0.0 and 1.0")

    def _unpack_coil(self, coil: dict) -> None:
        """ Unpacks values from the coil section """
        self.coil_inner_radi = self._require("inner_radi", coil)
        self.coil_outer_radi = self._require("outer_radi", coil)
        self.coil_axial_length = self._require("axial_length", coil)
        self.coil_material = self._require("material", coil)
        self.coil_wire_diameter = self._require("wire_diameter", coil)
        self.coil_fill_factor = self._require("fill_factor", coil)

    def _unpack_shell(self, shell: dict) -> None:
        """ Unpacks values from the shell section """
        self.shell_state = self._require("enabled", shell)
        self.shell_inner_radi = self._require("inner_radi", shell)
        self.shell_outer_radi = self._require("outer_radi", shell)
        self.shell_axial_length = self._require("axial_length", shell)
        self.shell_material = self._require("material", shell)

    def _unpack_projectile(self, projectile: dict) -> None:
        """ Unpacks values from the projectile section """
        self.projectile_inner_radi = self._require("inner_radi", projectile)
        self.projectile_outer_radi = self._require("outer_radi", projectile)
        self.projectile_material = self._require("material", projectile)
        self.projectile_density = self._require("material_density", projectile)
        self.projectile_co_drag = self._require("coefficient_drag", projectile)
        self.projectile_axial_length = self._require(
            "axial_length", projectile
        )

    def _calculated_parameters(self) -> None:
        """ Calculates parameters from unpacked values """
        self.coil_radial_thickness = (
            self.coil_outer_radi - self.coil_inner_radi
        )
        self.shell_radial_thickness = (
            self.shell_outer_radi - self.shell_inner_radi
        )
        self.projectile_radial_thickness = (
            self.projectile_outer_radi - self.projectile_inner_radi
        )

    def _require(self, key: str, section: dict) -> Any:
        """ Require a key from a section; raises KeyError if missing """
        if key not in section:
            msg = f"Missing required key `{key}` of `{self.file}`"
            raise KeyError(msg)

        return section[key]

    def _load_from_package(self) -> None:
        """ Loads the default coil-gun parameters """
        try:
            with resources.open_text(
                "blueshark.models.coilgun_multi_stage",
                self.DEFAULT_FILE_NAME
            ) as file:
                default_yaml = file.read()

                # Ensures the folder exists; if not creates it
                self.file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file, "w", encoding="utf-8") as f:
                    f.write(default_yaml)

                msg = f"Copied default coil-gun parameters to '{self.file}'"
                logging.info(msg)

                if self.debugging:
                    print(msg)

        except Exception as error:
            msg = (
                "Failed to load default parameters from package resources: "
                f"{error}"
            )
            raise RuntimeError(msg) from error

    def __repr__(self):
        """ Debug representation """
        return (
            f"<CoilGunUnpacker file='{getattr(self, 'stages', '?')}' "
            f"stages={getattr(self, 'stages', '?')} "
            f"Current limit={getattr(self, 'current_limit', '?')}>"
        )
