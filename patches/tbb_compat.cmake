# Injected at configure time to provide a usable TBB link target without editing submodules

if(NOT TARGET tbb)
  # Try to locate a usable libtbb shared object inside common env locations
  set(_TBB_HINT_DIRS
    "$ENV{CONDA_PREFIX}/lib"
    "${CMAKE_PREFIX_PATH}/lib"
    "${CMAKE_PREFIX_PATH}"
    "${CMAKE_CURRENT_LIST_DIR}/../.pixi/envs/default/lib"
  )
  find_library(TBB_LIB
    NAMES libtbb.so libtbb.so.12 tbb
    HINTS ${_TBB_HINT_DIRS}
  )
  if(TBB_LIB)
    add_library(tbb UNKNOWN IMPORTED)
    set_property(TARGET tbb PROPERTY IMPORTED_LOCATION "${TBB_LIB}")
    message(STATUS "tbb imported target provided by tbb_compat.cmake: ${TBB_LIB}")
  else()
    message(WARNING "tbb_compat.cmake could not locate libtbb; build may fail linking -ltbb")
  endif()
endif()

# Also provide TBB::tbb if needed by other projects
if(NOT TARGET TBB::tbb AND TARGET tbb)
  add_library(TBB::tbb ALIAS tbb)
endif()

