#include "compas.h"
#include "gpu.h"
#include <Eigen/Dense>
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <vector>
#include <string>
#include <memory>
#include <future>

namespace nb = nanobind;
using namespace gpu;

// Global GPU context
std::unique_ptr<Context> g_gpu_context = nullptr;

// Actual GPU availability check
bool is_gpu_available() {
    if (g_gpu_context) {
        return true; // Already initialized
    }
    
    try {
        g_gpu_context = std::make_unique<Context>(createContext());
        return true;
    } catch (const std::exception& e) {
        return false;
    }
}

// Get GPU device info using gpu.cpp API
std::string get_gpu_info() {
    if (!is_gpu_available()) {
        return "GPU not available";
    }
    try {
        WGPUAdapterInfo adapterInfo = WGPU_ADAPTER_INFO_INIT;
        WGPUStatus status = wgpuAdapterGetInfo(g_gpu_context->adapter, &adapterInfo);
        if (status == WGPUStatus_Success) {
            std::string info = "";
            if (adapterInfo.vendor && std::string(adapterInfo.vendor).length() > 0) {
                info += std::string(adapterInfo.vendor) + " ";
            }
            if (adapterInfo.device && std::string(adapterInfo.device).length() > 0) {
                info += std::string(adapterInfo.device);
            }
            info = info.empty() ? "Unknown GPU" : info;
            wgpuAdapterInfoFreeMembers(adapterInfo);
            return info;
        } else {
            return "Unknown GPU";
        }
    } catch (const std::exception& e) {
        return std::string("GPU info not available");
    }
}

// GPU matrix multiplication using gpu.cpp
std::vector<std::vector<float>> gpu_matrix_multiply(
    const std::vector<std::vector<float>>& a,
    const std::vector<std::vector<float>>& b) {
    if (!is_gpu_available()) {
        throw std::runtime_error("GPU not available for matrix multiplication");
    }
    if (a.empty() || b.empty() || a[0].empty() || b[0].empty()) {
        throw std::invalid_argument("Matrices cannot be empty");
    }
    if (a[0].size() != b.size()) {
        throw std::invalid_argument("Matrix dimensions do not match for multiplication");
    }
    int M = static_cast<int>(a.size());      // rows of A
    int K = static_cast<int>(a[0].size());   // cols of A / rows of B
    int N = static_cast<int>(b[0].size());   // cols of B
    std::vector<float> flat_a;
    std::vector<float> flat_b;
    for (const auto& row : a) flat_a.insert(flat_a.end(), row.begin(), row.end());
    for (const auto& row : b) flat_b.insert(flat_b.end(), row.begin(), row.end());
    Tensor tensor_a = createTensor(*g_gpu_context, Shape{static_cast<size_t>(M), static_cast<size_t>(K)}, kf32, flat_a.data());
    Tensor tensor_b = createTensor(*g_gpu_context, Shape{static_cast<size_t>(K), static_cast<size_t>(N)}, kf32, flat_b.data());
    Tensor result_tensor = createTensor(*g_gpu_context, Shape{static_cast<size_t>(M), static_cast<size_t>(N)}, kf32);
    // Updated kernel for arbitrary sizes
    const char* kernel_code = R"(
@group(0) @binding(0) var<storage, read> A: array<f32>;
@group(0) @binding(1) var<storage, read> B: array<f32>;
@group(0) @binding(2) var<storage, read_write> C: array<f32>;
@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {
    let row = global_id.x;
    let col = global_id.y;
    let M = " + std::to_string(M) + R"u;
    let N = " + std::to_string(N) + R"u;
    let K = " + std::to_string(K) + R"u;
    if (row >= M || col >= N) {
        return;
    }
    var total: f32 = 0.0;
    for (var k = 0u; k < K; k = k + 1u) {
        total += A[row * K + k] * B[k * N + col];
    }
    C[row * N + col] = total;
}
)";
    // Compose kernel code with actual sizes
    std::string kernel_code_str(kernel_code);
    KernelCode kernel_code_obj = {kernel_code_str, Shape{16, 16, 1}};
    Kernel kernel = createKernel(*g_gpu_context, kernel_code_obj, 
                                Bindings{tensor_a, tensor_b, result_tensor},
                                cdiv(Shape{static_cast<size_t>(M), static_cast<size_t>(N), 1}, Shape{16, 16, 1}));
    std::promise<void> promise;
    std::future<void> future = promise.get_future();
    dispatchKernel(*g_gpu_context, kernel, promise);
    wait(*g_gpu_context, future);
    std::vector<float> result_vector(M * N);
    toCPU(*g_gpu_context, result_tensor, result_vector.data(), result_vector.size() * sizeof(float));
    std::vector<std::vector<float>> output(M, std::vector<float>(N));
    for (int i = 0; i < M; ++i) {
        for (int j = 0; j < N; ++j) {
            output[i][j] = result_vector[i * N + j];
        }
    }
    return output;
}

// Eigen matrix multiplication fallback
std::vector<std::vector<float>> eigen_matrix_multiply_fallback(
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

// Main matrix multiplication function with GPU fallback to Eigen
std::vector<std::vector<float>> eigen_matrix_multiply(
    const std::vector<std::vector<float>>& a,
    const std::vector<std::vector<float>>& b) {
    
    // Try GPU first, fallback to Eigen
    if (is_gpu_available()) {
        try {
            return gpu_matrix_multiply(a, b);
        } catch (const std::exception& e) {
            // Fallback to Eigen if GPU fails
        }
    }
    
    // Eigen fallback
    return eigen_matrix_multiply_fallback(a, b);
}

NB_MODULE(_gpu_ops, m) {
    m.doc() = "GPU operations using gpu.cpp backend with Eigen fallback";
    
    // GPU availability
    m.def("is_gpu_available", &is_gpu_available, "Check if GPU operations are available");
    m.def("get_gpu_info", &get_gpu_info, "Get GPU device information");
    
    // Matrix operations
    m.def("eigen_matrix_multiply", &eigen_matrix_multiply, "a"_a, "b"_a, "Multiply two matrices using GPU with Eigen fallback");
    m.def("gpu_matrix_multiply", &gpu_matrix_multiply, "a"_a, "b"_a, "Multiply two matrices using GPU only");
    m.def("eigen_matrix_multiply_fallback", &eigen_matrix_multiply_fallback, "a"_a, "b"_a, "Multiply two matrices using Eigen only");
} 