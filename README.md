<p align="center">
  <img 
  src="https://raw.githubusercontent.com/Bowley-Systems/PyFEA/refs/heads/main/media/logo.png" 
  alt="pyFea" 
  style="width:100%; max-width:100%; display:block;"
> 
</p>
<p align="center">
  Define Topology, Attach Metadata, Solve.
  <br>
  Keep consistent representation across physics.
</p>

### Overview

![License](https://img.shields.io/badge/License-MIT-219EBC?style=flat-square)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-ffb703?style=flat-square)

This branch contains the original `prototype` for the `PyFEA` solver-adaptor engine.  
This implementation is not supported and merely serves as a reference for past development.

---

### Modelling Example

Why use arbitrary models when you can parametrically model and compile every time?

```py
# Builds the core geometry using construct solid geometry (CSG)
core_bulk = GBuilder.rectangle((0 * mm, 0 * mm), 115 * mm, 110 * mm)
core_window = GBuilder.rectangle((15 * mm, 25 * mm), 85 * mm, 60 * mm)

finalized_core = core_bulk.subtract(core_window)
core = GBuilder.promote_to_component(finalized_core, MagneticData(Materials.iron))

# Builds the phase circuit & then slot geometry using CSG
phase = Cbuilder.feed_circuit(1 * ampere, Configuration.series)

# Constructs the positive slot
slot = MagneticData(Materials.copper, phase, 100, 0.1 * mm)
positive_slot = GBuilder.rectangle((77.5 * mm, 40 * mm), 7.5 * mm, 20 * mm)
positive_slot = GBuilder.promote_to_part(positive_slot, slot)

# Constructs the negative slot
slot = MagneticData(Materials.copper, phase, -100, 0.1 * mm)
negative_slot = GBuilder.rectangle((130 * mm, 40 * mm), 7.5 * mm, 20 * mm)
negative_slot = GBuilder.promote_to_part(negative_slot, slot)

slots = GBuilder.promote_to_component((negative_slot, positive_slot))

# Builds the domain shape and defines the solution domain
finalized_domain = GBuilder.circle((115 / 2 * mm, 101 / 2 *mm), 200 * mm)
```

> Example is of a u-inductor with a ferromagnetic core material.

---

### Installation

To install,

```bash
pip install -e .
```

---