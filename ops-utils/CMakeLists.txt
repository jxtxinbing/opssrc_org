# Copyright (C) 2015-2016 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

cmake_minimum_required (VERSION 2.8)

set (UTILS_LIBS opsutils)
project (${UTILS_LIBS})
set (SRC_DIR src)
set (INCL_DIR include)

# Rules to locate needed libraries
include(FindPkgConfig)
pkg_check_modules(OVSCOMMON REQUIRED libovscommon)
pkg_check_modules(OVSDB REQUIRED libovsdb)

# Source files to build ops-utils library
set (SOURCES ${SRC_DIR}/nl-utils.c ${SRC_DIR}/ops-utils.c ${SRC_DIR}/vrf-utils.c
     ${SRC_DIR}/l3-utils.c ${SRC_DIR}/ping-send.c ${SRC_DIR}/source-interface-utils.c)

include_directories (${PROJECT_BINARY_DIR} ${PROJECT_SOURCE_DIR}/${INCL_DIR}
                     ${OVSCOMMON_INCLUDE_DIRS}
                    )
# Rules to build ops-utils library
add_library (${UTILS_LIBS} SHARED ${SOURCES})

target_link_libraries (${UTILS_LIBS} ${OVSCOMMON_LIBRARIES}
                       ${OVSDB_LIBRARIES}
                       -lpthread -lrt)
# Define compile flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99 -Wall -Werror")

set(OPS_U_VER_MAJOR "0")
set(OPS_U_VER_MINOR "1")
set(OPS_U_VER_PATCH "0")
set(OPSUTILS_VERSION "${OPS_U_VER_MAJOR}.${OPS_U_VER_MINOR}.${OPS_U_VER_PATCH}")
set_target_properties(${UTILS_LIBS} PROPERTIES VERSION ${OPSUTILS_VERSION})

configure_file(${SRC_DIR}/opsutils.pc.in ${SRC_DIR}/opsutils.pc @ONLY)

# Rules to stage ops-utils library and header files
install(TARGETS ${UTILS_LIBS}
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
)

install(FILES ${INCL_DIR}/nl-utils.h ${INCL_DIR}/ops-utils.h ${INCL_DIR}/vrf-utils.h
        ${INCL_DIR}/l3-utils.h ${INCL_DIR}/source-interface-utils.h
        DESTINATION include)

    install(FILES ${CMAKE_BINARY_DIR}/${SRC_DIR}/opsutils.pc DESTINATION lib/pkgconfig)
