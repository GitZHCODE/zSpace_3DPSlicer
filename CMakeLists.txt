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

# Setup Dawn binaries
set(DAWN_DIR "${EXTERNAL_DIR}/dawn")
set(DAWN_LIB_DIR "${DAWN_DIR}/lib")

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

# Download Dawn binaries for all platforms
if(NOT EXISTS "${DAWN_DIR}")
  message(STATUS "Downloading Dawn binaries...")
  
  # Determine platform-specific Dawn binary
  if(WIN32)
    set(DAWN_URL "https://github.com/jspanchu/webgpu-dawn-binaries/releases/download/v127.0.6535.0/webgpu-dawn-127.0.6535-win64.zip")
    set(DAWN_LIB_NAME "dawn.dll")
  elseif(APPLE)
    set(DAWN_URL "https://github.com/jspanchu/webgpu-dawn-binaries/releases/download/v127.0.6535.0/webgpu-dawn-127.0.6535-Darwin.zip")
    set(DAWN_LIB_NAME "libdawn.dylib")
  else()
    set(DAWN_URL "https://github.com/jspanchu/webgpu-dawn-binaries/releases/download/v127.0.6535.0/webgpu-dawn-127.0.6535-Linux.zip")
    set(DAWN_LIB_NAME "libdawn.so")
  endif()
  
  ExternalProject_Add(
      dawn_download
      URL ${DAWN_URL}
      SOURCE_DIR "${DAWN_DIR}"
      CONFIGURE_COMMAND ""
      BUILD_COMMAND ""
      INSTALL_COMMAND ""
      LOG_DOWNLOAD ON
      UPDATE_COMMAND ""
      PATCH_COMMAND ""
      TLS_VERIFY ON
  )
  add_dependencies(external_downloads dawn_download)
endif()

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Get Python executable directory for DLL copying
get_filename_component(PYTHON_EXECUTABLE_DIR ${Python_EXECUTABLE} DIRECTORY)

# Add include directories
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${EIGEN_INCLUDE_DIR}
  ${GPU_CPP_DIR}
  ${GPU_CPP_THIRD_PARTY_DIR}
  ${DAWN_DIR}/include
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
  
  # For GPU operations, we need to ensure Dawn DLL is available at runtime
  if(${name} STREQUAL "_gpu_ops" OR ${name} STREQUAL "_webgpu_ops")
    # Link against dawn.lib on Windows and copy dawn.dll to output
    if(WIN32)
      target_link_libraries(${name} PRIVATE "${DAWN_DIR}/lib/dawn.lib")
      add_custom_command(TARGET ${name} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DAWN_DIR}/bin/dawn.dll"
        $<TARGET_FILE_DIR:${name}>
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DAWN_DIR}/bin/dawn.dll"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/z3DPSlicer/"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DAWN_DIR}/bin/dawn.dll"
        "${PYTHON_EXECUTABLE_DIR}"
      )
    elseif(APPLE)
      add_custom_command(TARGET ${name} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DAWN_DIR}/lib/libdawn.dylib"
        $<TARGET_FILE_DIR:${name}>
      )
    else()
      add_custom_command(TARGET ${name} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DAWN_DIR}/lib/libdawn.so"
        $<TARGET_FILE_DIR:${name}>
      )
    endif()
  endif()
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION z3DPSlicer)
  
  # Copy the built module to the Python package directory for development
  add_custom_command(TARGET ${name} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    $<TARGET_FILE:${name}>
    "${CMAKE_CURRENT_SOURCE_DIR}/src/z3DPSlicer/"
  )
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
message(STATUS "Dawn Dir: ${DAWN_DIR}")
message(STATUS "Dawn Lib Dir: ${DAWN_LIB_DIR}")
message(STATUS "Python Executable: ${Python_EXECUTABLE}")
message(STATUS "Python Executable Dir: ${PYTHON_EXECUTABLE_DIR}")
message(STATUS "=======================================")