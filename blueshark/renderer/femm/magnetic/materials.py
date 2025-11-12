"""
Filename: femm_materials.py
Author: William Bowley
Version: 1.4
Date: 2025-09-14
Description:
    Adds custom material from material manager
    to the FEMMagneticRenderer
"""

import logging
import femm

from typing import Any


def femm_add_material(material: dict[str, Any]) -> None:
    """
    Adds a material to FEMM using properties from a material dictionary.

    Args:
        material: Material dictionary from material manager
    """
    name = material.get("name", "unknown")
    tag = material.get("tag", "").lower()

    physical_data = material.get("physical", {}) or {}
    magnetic_data = material.get("magnetic", {}) or {}
    electric_data = material.get("electrical", {}) or {}
    lamination = physical_data.get("lamination", "solid")
    lamination_fill = physical_data.get("lamination_fill", 1.0)
    lamination_thickness = physical_data.get("lamination_thickness", 0.0)
    wire_diameter = physical_data.get("wire_diameter", 0.0)
    number_of_strands = 1 if wire_diameter > 0 else 0

    match lamination:
        case "solid":        femm_lamination = 0
        case "laminated_x":  femm_lamination = 1
        case "laminated_y":  femm_lamination = 2
        case "magnet_wire":  femm_lamination = 3
        case _:
            femm_lamination = 0
            msg = (
                f"'{lamination}' not supported by FEMM; defaulting to 'solid'"
            )
            logging.warning(msg)

    relative_permeability = magnetic_data.get(
        "relative_permeability",
        [1.0, 1.0]
    )
    coercivity = magnetic_data.get("coercivity", 0.0)        # A/m
    current_density = magnetic_data.get("current_density", 0.0)  # A/mm²

    # Maxwell stress tensor is only valid in non-conductive environments
    # Assumes (conductivity=0)
    if tag != "environmental":
        conductivity = electric_data.get("conductivity", 0.0)    # expect S/m
        conductivity_ms = conductivity / 1e6    # FEMM expects MS/m
    else:
        conductivity_ms = 0

    # Phi_h_max, Phi_hx, Phi_hy are set to 0.0; hysteresis not yet supported
    femm.mi_addmaterial(
        name,
        relative_permeability[0],
        relative_permeability[1],
        coercivity,
        current_density,
        conductivity_ms,
        lamination_thickness,
        0.0,                   # Phi_h_max (not supported yet)
        lamination_fill,
        femm_lamination,
        0.0,                   # Phi_hx
        0.0,                   # Phi_hy
        number_of_strands,
        wire_diameter
    )
