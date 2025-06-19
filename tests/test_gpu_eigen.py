#!/usr/bin/env python3
"""
Tests for GPU and Eigen operations.
"""

import pytest
import sys
import os

# Add the project to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import z3DPSlicer as ppc
except ImportError:
    pytest.skip("z3DPSlicer not available", allow_module_level=True)

class TestGPUOperations:
    """Test GPU operations."""
    
    def test_gpu_availability(self):
        """Test GPU availability check."""
        # This should not raise an exception
        available = ppc.is_gpu_available()
        assert isinstance(available, bool)
    
    def test_gpu_info(self):
        """Test GPU info retrieval."""
        info = ppc.get_gpu_info()
        assert isinstance(info, str)
        assert len(info) > 0
    
    def test_gpu_vector_add(self):
        """Test GPU vector addition."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [2.0, 3.0, 4.0, 5.0, 6.0]
        expected = [3.0, 5.0, 7.0, 9.0, 11.0]
        
        try:
            result = ppc.gpu_vector_add(a, b)
            assert result == expected
        except Exception as e:
            if "GPU not available" in str(e) or "Failed to initialize" in str(e):
                pytest.skip("GPU not available for testing")
            else:
                raise
    
    def test_gpu_vector_mul(self):
        """Test GPU vector multiplication."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [2.0, 3.0, 4.0, 5.0, 6.0]
        expected = [2.0, 6.0, 12.0, 20.0, 30.0]
        
        try:
            result = ppc.gpu_vector_mul(a, b)
            assert result == expected
        except Exception as e:
            if "GPU not available" in str(e) or "Failed to initialize" in str(e):
                pytest.skip("GPU not available for testing")
            else:
                raise
    
    def test_gpu_vector_empty(self):
        """Test GPU operations with empty vectors."""
        try:
            result_add = ppc.gpu_vector_add([], [])
            assert result_add == []
            
            result_mul = ppc.gpu_vector_mul([], [])
            assert result_mul == []
        except Exception as e:
            if "GPU not available" in str(e) or "Failed to initialize" in str(e):
                pytest.skip("GPU not available for testing")
            else:
                raise
    
    def test_gpu_vector_mismatch(self):
        """Test GPU operations with mismatched vector sizes."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0]  # Different size
        
        try:
            with pytest.raises(Exception):
                ppc.gpu_vector_add(a, b)
            
            with pytest.raises(Exception):
                ppc.gpu_vector_mul(a, b)
        except Exception as e:
            if "GPU not available" in str(e) or "Failed to initialize" in str(e):
                pytest.skip("GPU not available for testing")
            else:
                raise

class TestEigenOperations:
    """Test Eigen operations."""
    
    def test_eigen_matrix_multiply(self):
        """Test Eigen matrix multiplication."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        expected = [[19.0, 22.0], [43.0, 50.0]]
        
        result = ppc.eigen_matrix_multiply(a, b)
        assert result == expected
    
    def test_eigen_matrix_transpose(self):
        """Test Eigen matrix transpose."""
        matrix = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        expected = [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
        
        result = ppc.eigen_matrix_transpose(matrix)
        assert result == expected
    
    def test_eigen_matrix_determinant(self):
        """Test Eigen matrix determinant."""
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        expected = -2.0  # 1*4 - 2*3 = 4 - 6 = -2
        
        result = ppc.eigen_matrix_determinant(matrix)
        assert abs(result - expected) < 1e-6
    
    def test_eigen_identity_matrix(self):
        """Test Eigen identity matrix creation."""
        size = 3
        expected = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        
        result = ppc.eigen_identity_matrix(size)
        assert result == expected
    
    def test_eigen_dot_product(self):
        """Test Eigen dot product."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        expected = 32.0  # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        
        result = ppc.eigen_dot_product(a, b)
        assert abs(result - expected) < 1e-6
    
    def test_eigen_cross_product(self):
        """Test Eigen cross product."""
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        expected = [0.0, 0.0, 1.0]  # Cross product of unit vectors
        
        result = ppc.eigen_cross_product(a, b)
        assert all(abs(r - e) < 1e-6 for r, e in zip(result, expected))
    
    def test_eigen_empty_matrix(self):
        """Test Eigen operations with empty matrices."""
        with pytest.raises(Exception):
            ppc.eigen_matrix_multiply([], [])
        
        with pytest.raises(Exception):
            ppc.eigen_matrix_transpose([])
        
        with pytest.raises(Exception):
            ppc.eigen_matrix_determinant([])
    
    def test_eigen_matrix_dimension_mismatch(self):
        """Test Eigen operations with dimension mismatches."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0], [2.0]]  # 2x1 matrix
        
        with pytest.raises(Exception):
            ppc.eigen_matrix_multiply(a, b)
    
    def test_eigen_non_square_determinant(self):
        """Test Eigen determinant with non-square matrix."""
        matrix = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]  # 2x3 matrix
        
        with pytest.raises(Exception):
            ppc.eigen_matrix_determinant(matrix)
    
    def test_eigen_cross_product_wrong_dimension(self):
        """Test Eigen cross product with wrong dimensions."""
        a = [1.0, 2.0]  # 2D vector
        b = [3.0, 4.0, 5.0]  # 3D vector
        
        with pytest.raises(Exception):
            ppc.eigen_cross_product(a, b)
    
    def test_eigen_identity_matrix_invalid_size(self):
        """Test Eigen identity matrix with invalid size."""
        with pytest.raises(Exception):
            ppc.eigen_identity_matrix(0)
        
        with pytest.raises(Exception):
            ppc.eigen_identity_matrix(-1)

class TestBasicOperations:
    """Test basic operations."""
    
    def test_add(self):
        """Test basic addition."""
        assert ppc.add(5, 3) == 8
        assert ppc.add(-1, 1) == 0
        assert ppc.add(0, 0) == 0

if __name__ == "__main__":
    pytest.main([__file__]) 