# BlueShark: Idealized Linear Motor Design Explorer
<img src="media/BlueShark.png" alt="BlueShark Logo"/> 

## Note: A work in progress 
This repository is an active work in progress. It represents a core set of functionalities that were submitted as an early-release version for the RMIT Early Entry application. The code is currently being refactored from <code>v1.3-dev</code> to <code>release</code> and is also expanded upon.
 
## Overview  
This package serves to explore linear motor designs quickly, providing easy integration for optimizers. It targets applications such as 3D printers, pick-and-place machines, laser cutters, and other electromechanical systems.

This initial release supports FEMM (Finite Element Method Magnetics) as the primary solver and renderer. Planned future releases will expand support to include additional solvers.

## Example Simulation
This example demonstrates a **quasi-transient simulation** of a **Tubular Linear Synchronous Motor (TLSM)**. The figure below represents the key time-domain performance metrics: *Current, Force, and Velocity vs. Time*.

<img src="media/dynamic_analysis.png" alt="Dynamic analysis example" height="750"/>

*The full configuration and simulation code for this analysis is available here:
[`tubular_motor`](./examples/tubular_motor/)*
## Installation 

1.  **Install FEMM**<br>  `(Windows Only)`
    FEMM (Finite Element Method Magnetics) is a free, open-source tool for low-frequency electromagnetic simulations, ideal for motor design.

    Download and install FEMM from the official website:  
    [https://www.femm.info/wiki/HomePage](https://www.femm.info/wiki/HomePage)

    > Ensure FEMM is added to your system PATH or installed in the default location (usually `C:\femm42` on Windows) so the simulator can call it without issues.

2.  **Install BlueShark**  
    Clone the repository and install the package locally in editable mode:

    ```bash
    git clone https://github.com/wgbowley/BlueShark-FEA.git
    cd blueshark
    pip install -e .
    ```

## Usage
This section is under development. A detailed usage example will be provided here soon.
- *Example of what the universal 2D ```PyFEA``` framework may look like: [`electromagnet`](./examples/electromagnet/electromagnet.py)*
