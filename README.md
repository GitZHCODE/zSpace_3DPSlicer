# COMPAS + C++ Integration Project

A minimal implementation demonstrating the integration between COMPAS (Python geometry library) and custom C++ code using nanobind for basic operations, GPU computing with gpu.cpp and Dawn WebGPU, and linear algebra with Eigen.

## Project Overview

This project shows how to:
- Use nanobind to create Python bindings for C++ code
- Integrate COMPAS geometry objects with C++ calculations
- Perform GPU-accelerated computations using gpu.cpp and Dawn WebGPU
- Execute fast matrix operations using Eigen
- Set up a modern C++/Python development environment with automatic dependency management

## Features

- **Fast C++ operations** using nanobind
- **GPU computing** using gpu.cpp with Dawn WebGPU implementation for cross-platform GPU operations
- **Eigen integration** for matrix operations and linear algebra
- **COMPAS integration** for Python-side geometry handling
- **Performance benchmarks** comparing CPU vs GPU operations
- **Simple examples** showing all libraries working together
- **Automatic dependency management** - downloads Eigen, gpu.cpp, and Dawn binaries during build

## Requirements

- Python 3.9+
- C++20 compatible compiler (GCC, Clang, or MSVC)
- CMake 3.15+
- COMPAS 2.0+
- GPU with WebGPU support (for GPU operations)
- Windows: Visual Studio 2019+ or MinGW-w64
- macOS: Xcode Command Line Tools
- Linux: GCC 9+ or Clang 10+

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd zspace_3DPSlicer
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Build the C++ extensions:**
   ```bash
   pip install -e .
   ```

   This will automatically:
   - Download Eigen 3.4.0 (header-only library)
   - Download gpu.cpp 0.1.0 (GPU computing library)
   - Download Dawn WebGPU binaries for your platform (Windows/macOS/Linux)
   - Build the C++ extensions using nanobind
   - Install the package in development mode
   - Copy all necessary runtime files to the correct locations

## Project Structure

```
zspace_3DPSlicer/
├── src/
│   ├── z3DPSlicer/
│   │   ├── __init__.py          # Main Python package
│   │   ├── _primitives.pyd      # Basic C++ operations
│   │   ├── _gpu_ops.pyd         # GPU operations using gpu.cpp
│   │   ├── _eigen_ops.pyd       # Eigen matrix operations
│   │   └── dawn.dll             # Dawn WebGPU runtime (Windows)
│   ├── compas.h                 # Precompiled header
│   ├── primitives.cpp           # Basic C++ operations
│   ├── gpu_ops.cpp             # GPU operations using gpu.cpp
│   └── eigen_ops.cpp           # Eigen matrix operations
├── external/                    # External dependencies (auto-downloaded)
│   ├── eigen/                   # Eigen headers
│   ├── gpu.cpp/                 # gpu.cpp library
│   └── dawn/                    # Dawn WebGPU binaries
├── examples/
│   ├── basic_example.py         # Simple demo
│   └── gpu_eigen_example.py     # GPU and Eigen demo
├── CMakeLists.txt              # CMake configuration
├── pyproject.toml              # Python package configuration
└── requirements.txt            # Python dependencies
```

## Usage

### Basic Usage

```python
import z3DPSlicer as ppc
import compas
from compas.geometry import Point, Vector

# Use C++ add function
result = ppc.add(5, 3)
print(f"5 + 3 = {result}")

# Create COMPAS objects
point = Point(1.0, 2.0, 3.0)
vector = Vector(4.0, 5.0, 6.0)

# Use C++ function with COMPAS data
x_sum = ppc.add(int(point.x), int(vector.x))
print(f"Sum of x coordinates: {x_sum}")
```

### GPU Operations

```python
import z3DPSlicer as ppc

# Check GPU availability
print(f"GPU Available: {ppc.is_gpu_available()}")
print(f"GPU Info: {ppc.get_gpu_info()}")

# Initialize GPU
ppc.init_gpu()

# Perform GPU vector operations
a = [1.0, 2.0, 3.0, 4.0, 5.0]
b = [2.0, 3.0, 4.0, 5.0, 6.0]

# GPU vector addition
result_add = ppc.gpu_vector_add(a, b)
print(f"GPU addition: {result_add}")

# GPU vector multiplication
result_mul = ppc.gpu_vector_mul(a, b)
print(f"GPU multiplication: {result_mul}")
```

### Eigen Matrix Operations

```python
import z3DPSlicer as ppc

# Matrix multiplication
matrix_a = [[1.0, 2.0], [3.0, 4.0]]
matrix_b = [[5.0, 6.0], [7.0, 8.0]]

result = ppc.eigen_matrix_multiply(matrix_a, matrix_b)
print(f"Matrix multiplication result: {result}")

# Vector operations
vec_a = [1.0, 2.0, 3.0]
vec_b = [4.0, 5.0, 6.0]

dot_product = ppc.eigen_dot_product(vec_a, vec_b)
cross_product = ppc.eigen_cross_product(vec_a, vec_b)

print(f"Dot product: {dot_product}")
print(f"Cross product: {cross_product}")
```

### Running the Examples

```bash
# Basic example
python examples/basic_example.py

# GPU and Eigen example
python examples/gpu_eigen_example.py
```

## Available Functions

### Basic Operations
- `add(a, b)` - Add two integers

### GPU Operations
- `init_gpu()` - Initialize GPU context
- `is_gpu_available()` - Check if GPU is available
- `get_gpu_info()` - Get GPU information
- `gpu_vector_add(a, b)` - Add two vectors on GPU
- `gpu_vector_mul(a, b)` - Multiply two vectors on GPU

### Eigen Operations
- `eigen_matrix_multiply(a, b)` - Multiply two matrices
- `eigen_matrix_transpose(matrix)` - Transpose a matrix
- `eigen_matrix_determinant(matrix)` - Calculate matrix determinant
- `eigen_identity_matrix(size)` - Create identity matrix
- `eigen_dot_product(a, b)` - Calculate dot product of two vectors
- `eigen_cross_product(a, b)` - Calculate cross product of two 3D vectors

## Performance

The GPU operations provide significant speedup for large vector operations:

- **Vector addition**: 10-100x speedup for large vectors (1M+ elements)
- **Vector multiplication**: 10-100x speedup for large vectors (1M+ elements)
- **Matrix operations**: Eigen provides optimized linear algebra operations

## Development

### Adding New C++ Functions

1. Add the function to the appropriate C++ file:
   - `src/primitives.cpp` for basic operations
   - `src/gpu_ops.cpp` for GPU operations
   - `src/eigen_ops.cpp` for Eigen operations

2. Add the binding in the `NB_MODULE` section
3. Update `src/z3DPSlicer/__init__.py` to export the function

### Building from Source

```bash
# Clean build
rm -rf build/ dist/
pip install -e . --force-reinstall
```

### Debugging

For debugging C++ extensions:

```bash
# Set debug build
export CMAKE_BUILD_TYPE=Debug
pip install -e . --force-reinstall
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure to build the extensions with `pip install -e .`
2. **COMPAS not found**: Install with `pip install compas`
3. **Build errors**: Ensure you have a C++20 compatible compiler
4. **Eigen download fails**: Check internet connection and try again
5. **GPU not available**: Ensure your GPU supports WebGPU and drivers are up to date
6. **gpu.cpp download fails**: Check internet connection and try again

### Platform-Specific Notes

- **Windows**: Requires Visual Studio 2019+ or MinGW-w64
- **macOS**: Requires Xcode Command Line Tools
- **Linux**: Requires GCC 9+ or Clang 10+
- **GPU Support**: Requires WebGPU-compatible GPU and drivers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [COMPAS](https://compas.dev/) - Computational framework for research and collaboration in architecture, engineering, and digital fabrication
- [nanobind](https://nanobind.readthedocs.io/) - Seamless operability between C++11 and Python
- [Eigen](https://eigen.tuxfamily.org/) - C++ template library for linear algebra
- [gpu.cpp](https://github.com/AnswerDotAI/gpu.cpp) - Lightweight library for portable low-level GPU computation using WebGPU 