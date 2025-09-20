# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/external/zspace")
  file(MAKE_DIRECTORY "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/external/zspace")
endif()
file(MAKE_DIRECTORY
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src/zspace_download-build"
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix"
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/tmp"
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src/zspace_download-stamp"
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src"
  "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src/zspace_download-stamp"
)

set(configSubDirs Debug;Release;MinSizeRel;RelWithDebInfo)
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src/zspace_download-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "C:/Users/Wo.Lin/source/repos/zSpace_3DPSlicer/zspace_download-prefix/src/zspace_download-stamp${cfgdir}") # cfgdir has leading slash
endif()
