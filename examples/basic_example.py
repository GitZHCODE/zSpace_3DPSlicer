#!/usr/bin/env python3
"""
Basic example demonstrating the integration between COMPAS and C++ extensions.

This example shows how to:
1. Use C++ functions for basic operations
2. Work with COMPAS geometry objects
3. Convert between COMPAS and C++ data types
"""

import sys
import os

# Add the project to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import z3DPSlicer as ppc
    print("✓ Successfully imported z3DPSlicer")
except ImportError as e:
    print(f"✗ Failed to import z3DPSlicer: {e}")
    print("Make sure to build the C++ extensions first with: pip install -e .")
    sys.exit(1)

try:
    import compas
    from compas.geometry import Point, Vector, Frame, Box, Sphere
    print("✓ Successfully imported COMPAS")
except ImportError as e:
    print(f"✗ Failed to import COMPAS: {e}")
    print("Install COMPAS with: pip install compas")
    sys.exit(1)

def demo_basic_arithmetic():
    """Demonstrate basic arithmetic operations."""
    print("\n" + "="*50)
    print("BASIC ARITHMETIC OPERATIONS")
    print("="*50)
    
    # C++ arithmetic
    result_add = ppc.add(5, 3)
    
    print(f"C++ add(5, 3) = {result_add}")
    
    # Test with different values
    print(f"C++ add(10, 20) = {ppc.add(10, 20)}")
    print(f"C++ add(-5, 8) = {ppc.add(-5, 8)}")

def demo_compas_integration():
    """Demonstrate COMPAS integration."""
    print("\n" + "="*50)
    print("COMPAS INTEGRATION")
    print("="*50)
    
    # Create COMPAS geometry objects
    point = Point(1.0, 2.0, 3.0)
    vector = Vector(4.0, 5.0, 6.0)
    
    print(f"COMPAS Point: {point}")
    print(f"COMPAS Vector: {vector}")
    
    # Use C++ function with COMPAS data
    # Convert COMPAS coordinates to integers for demonstration
    x_sum = ppc.add(int(point.x), int(vector.x))
    y_sum = ppc.add(int(point.y), int(vector.y))
    z_sum = ppc.add(int(point.z), int(vector.z))
    
    print(f"Sum of x coordinates: {x_sum}")
    print(f"Sum of y coordinates: {y_sum}")
    print(f"Sum of z coordinates: {z_sum}")

def main():
    """Run all demonstrations."""
    print("COMPAS + C++ Integration Demo")
    print("="*50)
    
    try:
        demo_basic_arithmetic()
        demo_compas_integration()
        
        print("\n" + "="*50)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 