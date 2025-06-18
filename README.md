# COMPAS + C++ Integration Project

A minimal implementation demonstrating the integration between COMPAS (Python geometry library) and custom C++ code using nanobind for basic operations.

## Project Overview

This project shows how to:
- Use nanobind to create Python bindings for C++ code
- Integrate COMPAS geometry objects with C++ calculations
- Set up a modern C++/Python development environment

## Features

- **Fast C++ operations** using nanobind
- **COMPAS integration** for Python-side geometry handling
- **Simple example** showing both libraries working together

## Requirements

- Python 3.9+
- C++20 compatible compiler (GCC, Clang, or MSVC)
- CMake 3.15+
- COMPAS 2.0+

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

   This will:
   - Download Eigen (if not present)
   - Build the C++ extensions using nanobind
   - Install the package in development mode

## Project Structure

```
zspace_3DPSlicer/
├── src/
│   ├── z3DPSlicer/
│   │   └── __init__.py          # Main Python package
│   ├── compas.h                 # Precompiled header
│   └── primitives.cpp           # C++ implementation
├── examples/
│   └── basic_example.py         # Simple demo
├── external/                    # External dependencies (Eigen)
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

### Running the Example

```bash
python examples/basic_example.py
```

This will demonstrate:
- Basic arithmetic operations
- COMPAS geometry objects
- Integration between C++ and COMPAS

## Available C++ Functions

### Basic Operations
- `add(a, b)` - Add two integers

## Development

### Adding New C++ Functions

1. Add the function to `src/primitives.cpp`
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

### Platform-Specific Notes

- **Windows**: Requires Visual Studio 2019+ or MinGW-w64
- **macOS**: Requires Xcode Command Line Tools
- **Linux**: Requires GCC 9+ or Clang 10+

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