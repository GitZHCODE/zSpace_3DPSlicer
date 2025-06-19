#include "compas.h"
#include <Eigen/Dense>
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <vector>

namespace nb = nanobind;

// Matrix multiplication using Eigen
std::vector<std::vector<float>> eigen_matrix_multiply(
    const std::vector<std::vector<float>>& a,
    const std::vector<std::vector<float>>& b) {
    
    if (a.empty() || b.empty() || a[0].empty() || b[0].empty()) {
        throw std::invalid_argument("Matrices cannot be empty");
    }
    
    if (a[0].size() != b.size()) {
        throw std::invalid_argument("Matrix dimensions do not match for multiplication");
    }
    
    // Convert to Eigen matrices
    Eigen::MatrixXf eigen_a(a.size(), a[0].size());
    Eigen::MatrixXf eigen_b(b.size(), b[0].size());
    
    // Fill matrix A
    for (size_t i = 0; i < a.size(); ++i) {
        for (size_t j = 0; j < a[i].size(); ++j) {
            eigen_a(i, j) = a[i][j];
        }
    }
    
    // Fill matrix B
    for (size_t i = 0; i < b.size(); ++i) {
        for (size_t j = 0; j < b[i].size(); ++j) {
            eigen_b(i, j) = b[i][j];
        }
    }
    
    // Perform multiplication
    Eigen::MatrixXf result = eigen_a * eigen_b;
    
    // Convert back to vector of vectors
    std::vector<std::vector<float>> output(result.rows(), std::vector<float>(result.cols()));
    for (int i = 0; i < result.rows(); ++i) {
        for (int j = 0; j < result.cols(); ++j) {
            output[i][j] = result(i, j);
        }
    }
    
    return output;
}

// Vector dot product using Eigen
float eigen_dot_product(const std::vector<float>& a, const std::vector<float>& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Vector sizes must match");
    }
    
    if (a.empty()) {
        return 0.0f;
    }
    
    // Convert to Eigen vectors
    Eigen::Map<const Eigen::VectorXf> eigen_a(a.data(), a.size());
    Eigen::Map<const Eigen::VectorXf> eigen_b(b.data(), b.size());
    
    return eigen_a.dot(eigen_b);
}

// Vector cross product (3D only)
std::vector<float> eigen_cross_product(const std::vector<float>& a, const std::vector<float>& b) {
    if (a.size() != 3 || b.size() != 3) {
        throw std::invalid_argument("Cross product requires 3D vectors");
    }
    
    // Convert to Eigen vectors
    Eigen::Vector3f eigen_a(a[0], a[1], a[2]);
    Eigen::Vector3f eigen_b(b[0], b[1], b[2]);
    
    // Perform cross product
    Eigen::Vector3f result = eigen_a.cross(eigen_b);
    
    return {result(0), result(1), result(2)};
}

// Matrix transpose
std::vector<std::vector<float>> eigen_matrix_transpose(const std::vector<std::vector<float>>& matrix) {
    if (matrix.empty() || matrix[0].empty()) {
        throw std::invalid_argument("Matrix cannot be empty");
    }
    
    // Convert to Eigen matrix
    Eigen::MatrixXf eigen_matrix(matrix.size(), matrix[0].size());
    
    for (size_t i = 0; i < matrix.size(); ++i) {
        for (size_t j = 0; j < matrix[i].size(); ++j) {
            eigen_matrix(i, j) = matrix[i][j];
        }
    }
    
    // Transpose
    Eigen::MatrixXf transposed = eigen_matrix.transpose();
    
    // Convert back to vector of vectors
    std::vector<std::vector<float>> output(transposed.rows(), std::vector<float>(transposed.cols()));
    for (int i = 0; i < transposed.rows(); ++i) {
        for (int j = 0; j < transposed.cols(); ++j) {
            output[i][j] = transposed(i, j);
        }
    }
    
    return output;
}

// Matrix determinant
float eigen_matrix_determinant(const std::vector<std::vector<float>>& matrix) {
    if (matrix.empty() || matrix.size() != matrix[0].size()) {
        throw std::invalid_argument("Matrix must be square");
    }
    
    // Convert to Eigen matrix
    Eigen::MatrixXf eigen_matrix(matrix.size(), matrix.size());
    
    for (size_t i = 0; i < matrix.size(); ++i) {
        for (size_t j = 0; j < matrix[i].size(); ++j) {
            eigen_matrix(i, j) = matrix[i][j];
        }
    }
    
    return eigen_matrix.determinant();
}

// Create identity matrix
std::vector<std::vector<float>> eigen_identity_matrix(int size) {
    if (size <= 0) {
        throw std::invalid_argument("Matrix size must be positive");
    }
    
    Eigen::MatrixXf identity = Eigen::MatrixXf::Identity(size, size);
    
    std::vector<std::vector<float>> output(size, std::vector<float>(size));
    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < size; ++j) {
            output[i][j] = identity(i, j);
        }
    }
    
    return output;
}

NB_MODULE(_eigen_ops, m) {
    m.doc() = "Eigen-based linear algebra operations";
    
    // Matrix operations
    m.def("eigen_matrix_multiply", &eigen_matrix_multiply, "a"_a, "b"_a, "Multiply two matrices using Eigen");
    m.def("eigen_matrix_transpose", &eigen_matrix_transpose, "matrix"_a, "Transpose a matrix using Eigen");
    m.def("eigen_matrix_determinant", &eigen_matrix_determinant, "matrix"_a, "Calculate matrix determinant using Eigen");
    m.def("eigen_identity_matrix", &eigen_identity_matrix, "size"_a, "Create identity matrix using Eigen");
    
    // Vector operations
    m.def("eigen_dot_product", &eigen_dot_product, "a"_a, "b"_a, "Calculate dot product of two vectors using Eigen");
    m.def("eigen_cross_product", &eigen_cross_product, "a"_a, "b"_a, "Calculate cross product of two 3D vectors using Eigen");
} 