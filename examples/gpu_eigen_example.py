#!/usr/bin/env python3
"""
Minimal GPU/Eigen test: check is_gpu_available() and eigen_matrix_multiply()
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
    sys.exit(1)

print("Checking GPU availability...")
gpu_available = ppc.is_gpu_available()
if gpu_available:
    gpu_info = ppc.get_gpu_info()
    print(f"GPU Info: '{gpu_info}'")
else:
    print("GPU not available, skipping GPU info.")

print(f"GPU Available: {gpu_available}")

# Test with 512x512 random matrices
size = 2048
a = np.random.rand(size, size).astype(np.float32)
b = np.random.rand(size, size).astype(np.float32)

# Convert to lists for the C++ extension
a_list = a.tolist()
b_list = b.tolist()

# Eigen (CPU) only multiplication
print("Running Eigen method...")
t0 = time.time()
result_cpu = ppc.eigen_matrix_multiply_fallback(a_list, b_list)
t1 = time.time()
print(f"Eigen (CPU) method time taken: {t1-t0:.4f} seconds") 

# GPU multiplication
print("Running Eigen (GPU) method...")
t0 = time.time()
result_gpu = ppc.eigen_matrix_multiply(a_list, b_list)
t1 = time.time()
print(f"Eigen (GPU) method time taken: {t1-t0:.4f} seconds")

# GPU multiplication
print("Running GPU method...")
t0 = time.time()
result_gpu = ppc.gpu_matrix_multiply(a_list, b_list)
t1 = time.time()
print(f"GPU method time taken: {t1-t0:.4f} seconds")