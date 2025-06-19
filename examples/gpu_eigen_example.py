#!/usr/bin/env python3
"""
GPU and Eigen operations example demonstrating:
1. GPU availability check and device info
2. GPU matrix multiplication vs Eigen matrix multiplication
3. Performance comparison between GPU and CPU operations
"""

import sys
import os
import time
import numpy as np

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

def demo_gpu_availability():
    """Demonstrate GPU availability check and device info."""
    print("\n" + "="*60)
    print("GPU AVAILABILITY CHECK")
    print("="*60)
    
    # Check GPU availability
    print("Checking GPU availability...")
    gpu_available = ppc.is_gpu_available()
    print(f"GPU Available: {gpu_available}")
    
    # Get GPU device info
    print("\nGetting GPU device information...")
    gpu_info = ppc.get_gpu_info()
    print(f"GPU Info: {gpu_info}")
    
    if gpu_available:
        print("✓ GPU operations are available")
    else:
        print("✗ GPU operations are not available")
        print("Note: Will fallback to CPU-based Eigen operations")

def demo_matrix_multiplication():
    """Demonstrate matrix multiplication using GPU and Eigen."""
    print("\n" + "="*60)
    print("MATRIX MULTIPLICATION COMPARISON")
    print("="*60)
    
    # Create test matrices
    print("Creating test matrices...")
    matrix_a = [
        [1.0, 2.0, 3.0, 4.0],
        [5.0, 6.0, 7.0, 8.0],
        [9.0, 10.0, 11.0, 12.0],
        [13.0, 14.0, 15.0, 16.0]
    ]
    
    matrix_b = [
        [16.0, 15.0, 14.0, 13.0],
        [12.0, 11.0, 10.0, 9.0],
        [8.0, 7.0, 6.0, 5.0],
        [4.0, 3.0, 2.0, 1.0]
    ]
    
    print(f"Matrix A (4x4):\n{matrix_a}")
    print(f"Matrix B (4x4):\n{matrix_b}")
    
    # Test Eigen-only matrix multiplication
    print("\nPerforming matrix multiplication using Eigen only...")
    try:
        result_eigen = ppc.eigen_matrix_multiply_fallback(matrix_a, matrix_b)
        print(f"Result (A × B) from Eigen:\n{result_eigen}")
    except Exception as e:
        print(f"✗ Eigen multiplication failed: {e}")
    
    # Test GPU matrix multiplication
    print("\nPerforming matrix multiplication using GPU...")
    try:
        result_gpu = ppc.gpu_matrix_multiply(matrix_a, matrix_b)
        print(f"Result (A × B) from GPU:\n{result_gpu}")
    except Exception as e:
        print(f"✗ GPU multiplication failed: {e}")
    
    # Test hybrid approach (GPU with Eigen fallback)
    print("\nPerforming matrix multiplication using GPU with Eigen fallback...")
    try:
        result_hybrid = ppc.gpu_eigen_matrix_multiply(matrix_a, matrix_b)
        print(f"Result (A × B) from hybrid approach:\n{result_hybrid}")
    except Exception as e:
        print(f"✗ Hybrid multiplication failed: {e}")
    
    # Verify results match (if all succeeded)
    try:
        eigen_hybrid_match = result_eigen == result_hybrid
        print(f"\nEigen vs Hybrid results match: {eigen_hybrid_match}")
        
        if 'result_gpu' in locals():
            gpu_hybrid_match = result_gpu == result_hybrid
            print(f"GPU vs Hybrid results match: {gpu_hybrid_match}")
    except:
        print("Could not compare results due to errors")
    
    # Performance comparison
    print("\nPerformance comparison...")
    
    # Time Eigen-only multiplication
    try:
        start_time = time.time()
        for _ in range(1000):
            ppc.eigen_matrix_multiply_fallback(matrix_a, matrix_b)
        eigen_time = time.time() - start_time
        print(f"Eigen-only time (1000 iterations): {eigen_time:.4f} seconds")
    except Exception as e:
        print(f"✗ Eigen performance test failed: {e}")
        eigen_time = 0
    
    # Time GPU multiplication
    try:
        start_time = time.time()
        for _ in range(1000):
            ppc.gpu_matrix_multiply(matrix_a, matrix_b)
        gpu_time = time.time() - start_time
        print(f"GPU-only time (1000 iterations): {gpu_time:.4f} seconds")
    except Exception as e:
        print(f"✗ GPU performance test failed: {e}")
        gpu_time = 0
    
    # Time hybrid approach
    try:
        start_time = time.time()
        for _ in range(1000):
            ppc.gpu_eigen_matrix_multiply(matrix_a, matrix_b)
        hybrid_time = time.time() - start_time
        print(f"Hybrid approach time (1000 iterations): {hybrid_time:.4f} seconds")
    except Exception as e:
        print(f"✗ Hybrid performance test failed: {e}")
        hybrid_time = 0
    
    # Calculate speedups
    if eigen_time > 0 and gpu_time > 0:
        speedup = eigen_time / gpu_time
        print(f"GPU speedup over Eigen: {speedup:.2f}x")
    
    if eigen_time > 0 and hybrid_time > 0:
        speedup = eigen_time / hybrid_time
        print(f"Hybrid speedup over Eigen: {speedup:.2f}x")

def demo_availability_check():
    """Demonstrate simple availability check."""
    print("\n" + "="*60)
    print("AVAILABILITY CHECK")
    print("="*60)
    
    # Check if modules are available
    print("Checking module availability...")
    
    try:
        import z3DPSlicer._primitives
        print("✓ _primitives module available")
    except ImportError:
        print("✗ _primitives module not available")
    
    try:
        import z3DPSlicer._eigen_ops
        print("✓ _eigen_ops module available")
    except ImportError:
        print("✗ _eigen_ops module not available")
    
    try:
        import z3DPSlicer._gpu_ops
        print("✓ _gpu_ops module available")
    except ImportError:
        print("✗ _gpu_ops module not available")
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test add function
    try:
        result = ppc.add(5, 3)
        print(f"✓ add(5, 3) = {result}")
    except Exception as e:
        print(f"✗ add function failed: {e}")
    
    # Test Eigen matrix multiplication
    try:
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        result = ppc.eigen_matrix_multiply_fallback(a, b)
        print(f"✓ eigen_matrix_multiply_fallback works: {result}")
    except Exception as e:
        print(f"✗ eigen_matrix_multiply_fallback failed: {e}")
    
    # Test GPU matrix multiplication
    try:
        result = ppc.gpu_matrix_multiply(a, b)
        print(f"✓ gpu_matrix_multiply works: {result}")
    except Exception as e:
        print(f"✗ gpu_matrix_multiply failed: {e}")
    
    # Test hybrid approach
    try:
        result = ppc.gpu_eigen_matrix_multiply(a, b)
        print(f"✓ gpu_eigen_matrix_multiply works: {result}")
    except Exception as e:
        print(f"✗ gpu_eigen_matrix_multiply failed: {e}")

def demo_compas_integration():
    """Demonstrate integration with COMPAS geometry."""
    print("\n" + "="*60)
    print("COMPAS INTEGRATION")
    print("="*60)
    
    # Create COMPAS geometry objects
    point = Point(1.0, 2.0, 3.0)
    vector = Vector(4.0, 5.0, 6.0)
    
    print(f"COMPAS Point: {point}")
    print(f"COMPAS Vector: {vector}")
    
    # Convert COMPAS objects to matrices for multiplication
    point_matrix = [[point.x, point.y, point.z]]
    vector_matrix = [[vector.x], [vector.y], [vector.z]]
    
    print(f"Point as matrix: {point_matrix}")
    print(f"Vector as matrix: {vector_matrix}")
    
    # Use matrix multiplication with COMPAS data
    try:
        result = ppc.eigen_matrix_multiply_fallback(point_matrix, vector_matrix)
        print(f"Matrix multiplication result (Eigen): {result}")
        
        # This should give us the dot product
        dot_product = result[0][0]
        print(f"Dot product of point and vector: {dot_product}")
    except Exception as e:
        print(f"Matrix multiplication failed: {e}")

def main():
    """Run all demonstrations."""
    print("GPU + Eigen Operations Demo")
    print("="*60)
    
    try:
        demo_gpu_availability()
        demo_matrix_multiplication()
        demo_availability_check()
        demo_compas_integration()
        
        print("\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 