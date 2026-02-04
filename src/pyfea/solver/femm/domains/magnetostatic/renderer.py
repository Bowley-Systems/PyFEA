"""
Filename: renderer.py
Description:
    Renderer adaptor interface for FEMM (finite element magnetic methods)
    magnetostatic simulation domain.
    
    Uses the FEMMRenderer as a parent to construct the magnetostatic
    problem within the FEMM suite. 
"""

from pyfea.solver.renderer_interface import MagneticRenderer
from pyfea.solver.femm.base_renderer import FEMMRenderer


class FEMMMagnetostaticRenderer(FEMMRenderer, MagneticRenderer):
    """ Magnetostatic renderer for FEMM (finite element magnetic methods) """
    