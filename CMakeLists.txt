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

# Setup zSpace
set(ZSPACE_DIR "${EXTERNAL_DIR}/zspace")
set(ZSPACE_INCLUDE_DIR "${ZSPACE_DIR}")
set(ZSPACE_LIB_DIR "${ZSPACE_DIR}")

# Add DLL directory to PATH
if(WIN32)
    set(ENV{PATH} "$ENV{PATH};${ZSPACE_LIB_DIR}")
endif()

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

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)

find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Add include directories
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${EIGEN_INCLUDE_DIR}
  ${ZSPACE_INCLUDE_DIR}
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
    ${ZSPACE_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )

  message(   ${ZSPACE_INCLUDE_DIR})
  
  # Add dependencies
  add_dependencies(${name} external_downloads)
  
  # Link zSpace library if needed
  if(${name} STREQUAL "_zspace")
    target_link_directories(${name} PRIVATE ${ZSPACE_LIB_DIR})
    target_link_libraries(${name} PRIVATE 
      zSpace_External
      zSpace_InterOp
      zSpace_Interface
      zSpace_Core
      zSpace_Toolsets
      freeglut
    )
    
    # Set DLL directory for runtime
    set_target_properties(${name} PROPERTIES
      RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/cp39-cp39-win_amd64/Release"
      VS_DEBUGGER_ENVIRONMENT "PATH=${ZSPACE_LIB_DIR};$ENV{PATH}"
    )

    # Copy DLLs to Python package directory
    add_custom_command(TARGET ${name} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${ZSPACE_LIB_DIR}/zSpace_External.dll"
        "${ZSPACE_LIB_DIR}/zSpace_InterOp.dll"
        "${ZSPACE_LIB_DIR}/zSpace_Interface.dll"
        "${ZSPACE_LIB_DIR}/zSpace_Core.dll"
        "${ZSPACE_LIB_DIR}/zSpace_Toolsets.dll"
        "${ZSPACE_LIB_DIR}/freeglut.dll"
        "${CMAKE_SOURCE_DIR}/src/z3DPSlicer"
    )
  endif()
  
  # Install the module and DLLs
  install(TARGETS ${name} LIBRARY DESTINATION z3DPSlicer)
  if(${name} STREQUAL "_zspace")
    install(FILES
      "${ZSPACE_LIB_DIR}/zSpace_External.dll"
      "${ZSPACE_LIB_DIR}/zSpace_InterOp.dll"
      "${ZSPACE_LIB_DIR}/zSpace_Interface.dll"
      "${ZSPACE_LIB_DIR}/zSpace_Core.dll"
      "${ZSPACE_LIB_DIR}/zSpace_Toolsets.dll"
      "${ZSPACE_LIB_DIR}/freeglut.dll"
      DESTINATION z3DPSlicer
    )
  endif()
endfunction()

# Create individual extension modules for each C++ file
# Copy this line with new file name and module name
add_nanobind_extension(_zspace src/zspace_bindings.cpp)

message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "zSpace Include Dir: ${ZSPACE_INCLUDE_DIR}")
message(STATUS "zSpace Lib Dir: ${ZSPACE_LIB_DIR}")
message(STATUS "=======================================")