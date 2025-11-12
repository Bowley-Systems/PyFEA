"""
File: unpack.py
Author: William Bowley
Version: 0.1
Date: 2025-10-04

Description:
    Unpacks data from the .YAML file for the tubular
    linear motor to use later.

    NOTE:
        Handles only static parameter definitions.
        Specific dynamic definitions are handled by `main.py`
"""

import yaml
import logging
import pathlib

from typing import Any
from importlib import resources


class MotorUnpacker:
    """ Loads motor parameters from YAML into class attributes. """

    DEFAULT_FILE_NAME = "default.yaml"
    REQUIRED = ["output", "operation", "model", "armature", "stator"]

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
                f"Copying default motor parameters from package"
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
        self._unpack_operation(parameters["operation"])
        self._unpack_model(parameters["model"])
        self._unpack_armature(parameters["armature"])
        self._unpack_stator(parameters["stator"])

        # Calculated parameters
        self._calculated_parameters()

    def _unpack_output(self, output: dict) -> None:
        """ Unpacks values from the output section """
        self.folder_path = self._require("folder_path", output)
        self.file_name = self._require("file_name", output)

    def _unpack_operation(self, operation: dict) -> None:
        """ Unpacks values from the operation section """
        self.mass = self._require("mass", operation)
        self.target_speed = self._require("target_speed", operation)
        self.supply_voltage = self._require("supply_voltage", operation)
        self.current_limit = self._require("current_limit", operation)
        self.test_current = self._require("test_current", operation)
        self.de_maximum_steps = self._require(
            "de_solver_maximum_steps",
            operation
        )

    def _unpack_model(self, model: dict) -> None:
        """ Unpacks values from the model section """
        self.number_pairs = self._require("number_pairs", model)
        self.number_slots = self._require("number_slots", model)
        self.fill_factor = self._require("fill_factor", model)
        self.boundary_pairs = self._require("boundary_pairs", model)
        self.boundary_material = self._require("boundary_material", model)
        self.boundary_shells = self._require("boundary_shells", model)

    def _unpack_armature(self, armature: dict) -> None:
        """ Unpacks values from the armature section """
        self.slot_inner_radius = self._require("inner_radius", armature)
        self.slot_outer_radius = self._require("outer_radius", armature)
        self.slot_axial_length = self._require("axial_length", armature)
        self.slot_axial_spacing = self._require("axial_spacing", armature)

        # Armature materials
        self.slot_material = self._require("slot_material", armature)
        self.slot_wire_diameter = self._require("slot_wire_diameter", armature)

    def _unpack_stator(self, stator: dict) -> None:
        """ Unpacks values from the stator section """
        self.pole_inner_radius = self._require("inner_radius", stator)
        self.pole_outer_radius = self._require("outer_radius", stator)
        self.pole_axial_length = self._require("axial_length", stator)

        # Stator Materials
        self.pole_material = self._require("pole_material", stator)
        self.pole_grade = self._require("pole_grade", stator)

    def _calculated_parameters(self) -> None:
        """ Calculates parameters from unpacked values"""
        self.slot_radial_thickness = (
            self.slot_outer_radius - self.slot_inner_radius
        )
        self.pole_radial_thickness = (
            self.pole_outer_radius - self.pole_inner_radius
        )

    def _require(self, key: str, section: dict) -> Any:
        """ Require a key from a section; raises KeyError if missing """
        if key not in section:
            msg = f"Missing required key `{key}` of `{self.file}`"
            raise KeyError(msg)

        return section[key]

    def _load_from_package(self) -> None:
        """ Loads the default motor parameters """
        try:
            with resources.open_text(
                "blueshark.models.tlsm",
                self.DEFAULT_FILE_NAME
            ) as file:
                default_yaml = file.read()

                # Ensures the folder exists; if not creates it
                self.file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file, "w", encoding="utf-8") as f:
                    f.write(default_yaml)

                msg = f"Copied default motor parameters to '{self.file}'"
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
            f"<MotorUnpacker file='{getattr(self, 'file_name', '?')}' "
            f"slots={getattr(self, 'number_slots', '?')} "
            f"pairs={getattr(self, 'number_pairs', '?')}>"
        )
