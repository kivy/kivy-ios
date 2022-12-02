cmake_minimum_required(VERSION 3.18)
project(cffi)

set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

add_library(_cffi_backend STATIC _cffi_backend.c)

find_package (Python3 COMPONENTS Interpreter Development)
include_directories(${Python3_INCLUDE_DIRS})

#include_directories(${LIBFFI_INCLUDE_DIR})
include_directories(libffi_arm64/include)