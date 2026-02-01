<p align="center">
  <img src="media/banner.png" alt="pyFea" style="max-width:600px;">
  <br>
  <em>A Solver-Adaptor Engine for Multi-Physics Simulation & Optimization
   – Built with headaches by <a href="https://github.com/wgbowley">William Bowley</a></em>
</p>


## Overview

Sick of glue code and brittle pipelines? Annoyed by having to learn 10 different APIs? What if we could have a single high-level API handle all translation, leaving us to focus on what we're good at? PyFea is a solver-adaptor engine that functions as a single high-level API for finite element and lumped parameter multi-physics problems. PyFea levarges PicoUnits DSL and runtime checking for configuration files and material libraries. Currently, PyFea supports these physics domains: thermal, magnetic, electric, and electric circuits.

## Details

![Work in Progress](https://img.shields.io/badge/status-wip-blue)
![License](https://img.shields.io/badge/license-MIT-white)
![Python Version](https://img.shields.io/badge/python-3.10+-blue)


PyFea is designed to be used as a high-level API for multi-solver physics problems. It is built around abstract base functions, essentially contracts that all solvers have to meet. Implementing a solver consists of two parts: a renderer and the solver interface. The renderer understands how to translate PyFea's native vector geometry to a non-native geometry type. It can be thought of as a preloader for the solver. The solver interface simply communicates with the external solver while doing boundary unit checks to ensure dimensional consistency. 

> [!NOTE]
> [FEMM](https://www.femm.info/wiki/HomePage) and [PySpice](https://pyspicepyspice.fabrice-salvaire.f) are the only supported solvers currently; future releases will support additional solvers.

PyFea includes solver-generic model implementations and a unit-informed universal material library. The current model library includes:

- A PD-PI controlled tubular linear motor running under quasi-transient + static conditions
- A multi-stage coil-gun running under quasi-transient conditions
- A magnetic latching system for a 3D printer's toolhead running under quasi-transient conditions
- A lumped-parameter model for a multi-stage coil-gun (reference model for FEM)


## Installation

### 1. Install PyFea
Clone the repository and install the package locally in editable mode:

```bash
git clone https://github.com/wgbowley/pyfea.git
cd pyfea
pip install -e .
```

## Usage
This section is under development. A detailed usage example will be provided here soon.