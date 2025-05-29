# zSpace 3DPSlicer - A C++ SDF-based Mesh Slicing Library

![zSpace Logo](documentation/Assets/zSpace_logo.png)

## Introduction

zSpace 3DPSlicer is a powerful C++ library for SDF (Signed Distance Field) based mesh slicing. We provide comprehensive functionality for generating profile curves for 3DPrinting, including construction of scalar fields, boolean operations, and contour extraction. The library is designed to work seamlessly with complex architectural geometries and supports advanced manufacturing workflows.

It is **a header-only library** built on the zSpace framework. You do not need to compile anything to use, just include the necessary headers (e.g. `#include <zTsSDFSlicer.h>`) and run. The library is tailored to operate on triangle meshes and provides robust SDF computation for slicing operations.

*Optionally* the library may also be pre-compiled into a statically linked library, for faster compile times with your projects. This only affects compile time (run-time performance and behavior is identical).

We use the **zSpace framework** extensively in our code, providing a solid foundation for computational geometry operations and 3DPrinting workflows.

## Tutorial

The library includes comprehensive documentation and examples. Start with our main tutorial:

**[SDF Slicer Tutorial](documentation/zTsSDFSlicer.md)** - WIP guide to using the SDF-based mesh slicing functionality

## Pilot Projects

We provide pilot projects showing the use cases of zSpace 3DPSlicer for real-world applications:

* **[Striatus Bridge](https://www.zaha-hadid.com/design/striatus/)** - Large-scale pedestrian bridge, Venice, 2021
* **[Striatus Bridge 2.0: Phoenix](https://www.zaha-hadid.com/2024/01/05/phoenix-the-new-3d-printed-concrete-bridge/)** - Large-scale pedestrian bridge, Lyon, 2024
* **[NatpowerH Hydrogen Refuelling Stations](https://www.zaha-hadid.com/architecture/natpower-h-hydrogen-refuelling-stations/)** - Larger-scale 3D printed infrastructures, Venice, ongoing

## Installation

zSpace 3DPSlicer is a **header-only** library with visualization capabilities provided by the ALICE viewer.

### Requirements
* Visual Studio 2019+ (Windows)
* [zSpace ALICE platform](https://github.com/GitZHCODE/zspace_alice) for visualization

### Setup
```bash
# Clone the slicer library
git clone https://github.com/GitZHCODE/zspace_3DPSlicer.git
```

### Usage
1. **Include headers**: Add `include/` to your project's include path
2. **Launch viewer**: Build and run `zspace_alice/ALICE_PLATFORM/ALICE.sln` (Release_zSpaceDLL configuration)
3. **Integrate**: Use ALICE viewer for visualizing meshes, scalar fields, and slicing results

### Quick Test
```cpp
#include <zTsSDFSlicer.h>

int main() {
    zTsSDFSlicer mySlicer;
    mySlicer.setFromJSON("data/example/", 1);
    
    zDomain<zPoint> bb(zPoint(-1, -1, 0), zPoint(1, 1, 0));
    mySlicer.createFieldMesh(bb, 256, 256);
    return 0;
}
```

## Dependencies

### Required Dependencies

* **zSpace Framework** - Core computational geometry framework
* **Eigen3** - Linear algebra library
* **C++11/14 compiler** - Modern C++ standard support
* **OpenGL** - For visualization components
* **JSON** - For data import/export functionality

Dependencies are organized by directory structure in the `include/` folder. Core functionality depends only on zSpace and Eigen.

## Quick Start

1. **Set up your project**: Include the necessary headers
2. **Initialize the slicer**: Create a `zTsSDFSlicer` object
3. **Load geometry**: Use `setFromJSON()` to load your mesh data
4. **Create field**: Set up the scalar field with `createFieldMesh()`
5. **Compute slices**: Run `computePrintBlocks()` to generate slicing data
6. **Export results**: Use `exportJSON()` to save your results

For detailed examples, see our [complete tutorial](documentation/zTsSDFSlicer.md).

## License

zSpace 3DPSlicer is licensed under [LICENSE_TYPE]. Some components may have different licenses - please check individual files for details.

## Citation

If you use zSpace 3DPSlicer in your academic projects, please cite our work:

```bibtex
@misc{zspace3dslicer,
  title = {{zSpace 3DPSlicer}: A C++ SDF-based Mesh Slicing Library},
  author = {[Author Names]},
  note = {https://github.com/GitZHCODE/zspace_3DPSlicer},
  year = {2024},
}
```

## Copyright

2024 zSpace Development Team and Contributors.

Please see individual files for appropriate copyright notices.

---

*ZHACODE | Computation and Design Group, Zaha Hadid Architects*
