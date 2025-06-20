"""
z3DPSlicer - A minimal C++/Python project using nanobind and COMPAS
"""

__version__ = "0.1.0"

# Import C++ extensions
try:
    from . import _primitives
    from . import _test_slicer
    from . import _slicer
    # Import the add function directly
    from ._primitives import add
    # Import test function
    from ._test_slicer import test_function
    # Import slicer classes
    from ._slicer import zSlicer, zMesh, zPlane
except ImportError as e:
    print(f"Warning: C++ extensions not available: {e}")
    print("Make sure to build the extensions with: pip install -e .")
    # Define a fallback function
    def add(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    def test_function():
        raise ImportError("C++ extensions not built. Run: pip install -e .")

# Import COMPAS for Python-side functionality
try:
    import compas
    from compas.geometry import Point, Vector, Frame
    from compas.geometry import Box, Sphere, Cylinder
    from compas.geometry import Transformation
except ImportError:
    print("Warning: COMPAS not available. Install with: pip install compas")

# Re-export useful functions
__all__ = [
    "add",
    "test_function",
    "zSlicer",
    "zMesh", 
    "zPlane",
] 