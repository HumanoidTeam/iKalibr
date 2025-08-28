# Combined compatibility configuration for iKalibr
# This file includes both OpenGL and TBB compatibility fixes

# Include OpenGL compatibility
include(${CMAKE_CURRENT_LIST_DIR}/opengl_compat.cmake)

# Include TBB compatibility
include(${CMAKE_CURRENT_LIST_DIR}/tbb_compat.cmake)
