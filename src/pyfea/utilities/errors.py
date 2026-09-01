"""
Filename: errors.py

Description:
    Defines the errors within PyFEA 
    ensuring descriptive error messages 
    are returned.
"""

# Generic Errors
class MaterialError(TypeError):
    """ Exception for Material Loader Error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = f"{caller!r} raised error: {error} "
        super().__init__(msg)

class GeometryDimensionError(TypeError):
    """ Exception for geometry dimension error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = f"{caller} raised error: {error}. "
        super().__init__(msg)

class PartError(TypeError):
    """ Exception for part error """
    def __init__(self, caller: str, error: str):
        """ Returns a custom error message """
        msg = f"{caller} raised error: {error}. "
        super().__init__(msg)
