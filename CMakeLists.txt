cmake_minimum_required(VERSION 3.15)
project(z3DPSlicer LANGUAGES CXX)

# Build configuration
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(ENABLE_PRECOMPILED_HEADERS "Enable precompiled headers for the build" ON)

# External dependencies
include(ExternalProject)

# Setup Eigen (header-only library)
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")
set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")

# Setup gpu.cpp
set(GPU_CPP_DIR "${EXTERNAL_DIR}/gpu.cpp")
set(GPU_CPP_THIRD_PARTY_DIR "${GPU_CPP_DIR}/third_party/headers")

# Create external downloads target
add_custom_target(external_downloads ALL)

# Download Eigen if not already present
if(NOT EXISTS "${EIGEN_INCLUDE_DIR}")
  message(STATUS "Downloading Eigen...")
  ExternalProject_Add(
      eigen_download
      URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
      SOURCE_DIR "${EIGEN_INCLUDE_DIR}"
      CONFIGURE_COMMAND ""
      BUILD_COMMAND ""
      INSTALL_COMMAND ""
      LOG_DOWNLOAD ON
      UPDATE_COMMAND ""
      PATCH_COMMAND ""
      TLS_VERIFY ON
  )
  add_dependencies(external_downloads eigen_download)
endif()

# Download gpu.cpp release if not already present
if(NOT EXISTS "${GPU_CPP_DIR}")
  message(STATUS "Downloading gpu.cpp...")
  ExternalProject_Add(
      gpu_cpp_download
      URL https://github.com/AnswerDotAI/gpu.cpp/archive/refs/tags/0.1.0.zip
      SOURCE_DIR "${GPU_CPP_DIR}"
      CONFIGURE_COMMAND ""
      BUILD_COMMAND ""
      INSTALL_COMMAND ""
      LOG_DOWNLOAD ON
      UPDATE_COMMAND ""
      PATCH_COMMAND ""
      TLS_VERIFY ON
  )
  add_dependencies(external_downloads gpu_cpp_download)
endif()

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Add include directories
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${EIGEN_INCLUDE_DIR}
  ${GPU_CPP_DIR}
  ${GPU_CPP_THIRD_PARTY_DIR}
)

# Define a function to add a nanobind module with common settings
function(add_nanobind_extension name source)
  nanobind_add_module(
    ${name}
    STABLE_ABI
    NB_STATIC
    ${source}
  )
  
  # Apply precompiled headers
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Include directories
  target_include_directories(${name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${GPU_CPP_DIR}
    ${GPU_CPP_THIRD_PARTY_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  # Add dependencies
  add_dependencies(${name} external_downloads)
  
  # Link libraries
  target_link_libraries(${name} PRIVATE Threads::Threads)
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION z3DPSlicer)
endfunction()

# Create individual extension modules for each C++ file
add_nanobind_extension(_primitives src/primitives.cpp)
add_nanobind_extension(_gpu_ops src/gpu_ops.cpp)
add_nanobind_extension(_eigen_ops src/eigen_ops.cpp)

message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "GPU.cpp Include Dir: ${GPU_CPP_DIR}")
message(STATUS "GPU.cpp Third Party Dir: ${GPU_CPP_THIRD_PARTY_DIR}")
message(STATUS "=======================================")