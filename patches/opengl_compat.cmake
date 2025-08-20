# Ensure OpenGL imported targets exist for consumers that expect OpenGL::OpenGL

if(NOT TARGET OpenGL::OpenGL)
    find_package(OpenGL REQUIRED COMPONENTS OpenGL)

    if(TARGET OpenGL::GL AND NOT TARGET OpenGL::OpenGL)
        add_library(OpenGL::OpenGL ALIAS OpenGL::GL)
    endif()

    if(TARGET OpenGL::GL AND NOT TARGET OpenGL::EGL)
        add_library(OpenGL::EGL ALIAS OpenGL::GL)
    endif()

    if(NOT TARGET OpenGL::OpenGL AND DEFINED OpenGL_LIBRARIES)
        add_library(OpenGL::OpenGL INTERFACE IMPORTED)
        target_link_libraries(OpenGL::OpenGL INTERFACE ${OpenGL_LIBRARIES})
        if(DEFINED OpenGL_INCLUDE_DIR)
            target_include_directories(OpenGL::OpenGL INTERFACE ${OpenGL_INCLUDE_DIR})
        elseif(DEFINED OpenGL_INCLUDE_DIRS)
            target_include_directories(OpenGL::OpenGL INTERFACE ${OpenGL_INCLUDE_DIRS})
        endif()
    endif()
endif()


