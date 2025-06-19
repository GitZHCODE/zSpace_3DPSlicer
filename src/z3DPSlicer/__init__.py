"""
z3DPSlicer - A minimal C++/Python project using nanobind and COMPAS
"""

__version__ = "0.1.0"

# Import C++ extensions
try:
    from . import _primitives
    from . import _gpu_ops
    from . import _eigen_ops
    
    # Import functions from primitives
    from ._primitives import add
    
    # Import functions from GPU operations
    from ._gpu_ops import (
        is_gpu_available, get_gpu_info,
        eigen_matrix_multiply as gpu_eigen_matrix_multiply,
        gpu_matrix_multiply, eigen_matrix_multiply_fallback
    )
    
    # Import functions from Eigen operations
    from ._eigen_ops import (
        eigen_matrix_multiply, eigen_matrix_transpose, eigen_matrix_determinant,
        eigen_identity_matrix, eigen_dot_product, eigen_cross_product
    )
    
except ImportError as e:
    print(f"Warning: C++ extensions not available: {e}")
    print("Make sure to build the extensions with: pip install -e .")
    
    # Define fallback functions
    def add(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def is_gpu_available():
        return False
    
    def get_gpu_info():
        return "GPU not available - C++ extensions not built"
    
    def gpu_eigen_matrix_multiply(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def gpu_matrix_multiply(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_matrix_multiply_fallback(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_matrix_multiply(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_matrix_transpose(matrix):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_matrix_determinant(matrix):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_identity_matrix(size):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_dot_product(a, b):
        raise ImportError("C++ extensions not built. Run: pip install -e .")
    
    def eigen_cross_product(a, b):
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
    # Basic operations
    "add",
    
    # GPU availability
    "is_gpu_available", "get_gpu_info",
    
    # GPU operations
    "gpu_matrix_multiply", "eigen_matrix_multiply_fallback",
    
    # Eigen operations (from both modules)
    "eigen_matrix_multiply", "eigen_matrix_transpose", "eigen_matrix_determinant",
    "eigen_identity_matrix", "eigen_dot_product", "eigen_cross_product",
    
    # GPU module Eigen operations (for testing)
    "gpu_eigen_matrix_multiply"
] 