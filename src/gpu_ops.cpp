#include "compas.h"
#include <Eigen/Dense>
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <vector>
#include <string>

namespace nb = nanobind;

// Simple GPU availability check
bool is_gpu_available() {
    // For now, we'll return true since we're using Eigen operations
    // In the future, this could check for actual GPU availability
    return true;
}

// Get GPU device info
std::string get_gpu_info() {
    // For now, return a simple message since we're not using actual GPU
    return "GPU operations using Eigen (CPU-based matrix operations)";
}

// Simple Eigen matrix multiplication for testing
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

NB_MODULE(_gpu_ops, m) {
    m.doc() = "Simple Eigen matrix operations for testing";
    
    // GPU availability
    m.def("is_gpu_available", &is_gpu_available, "Check if GPU operations are available");
    m.def("get_gpu_info", &get_gpu_info, "Get GPU device information");
    
    // Matrix operations
    m.def("eigen_matrix_multiply", &eigen_matrix_multiply, "a"_a, "b"_a, "Multiply two matrices using Eigen");
} 