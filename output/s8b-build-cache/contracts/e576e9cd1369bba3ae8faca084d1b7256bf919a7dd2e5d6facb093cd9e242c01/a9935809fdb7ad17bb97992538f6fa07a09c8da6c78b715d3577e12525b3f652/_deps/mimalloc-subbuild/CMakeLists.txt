# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.25.0)

# We name the project and the target for the ExternalProject_Add() call
# to something that will highlight to the user what we are working on if
# something goes wrong and an error message is produced.

project(mimalloc-populate NONE)


# Pass through things we've already detected in the main project to avoid
# paying the cost of redetecting them again in ExternalProject_Add()
set(GIT_EXECUTABLE [==[/bin/git]==])
set(GIT_VERSION_STRING [==[2.34.1]==])
set_property(GLOBAL PROPERTY _CMAKE_FindGit_GIT_EXECUTABLE_VERSION
  [==[/bin/git;2.34.1]==]
)


include(ExternalProject)
ExternalProject_Add(mimalloc-populate
                     "UPDATE_DISCONNECTED" "False" "GIT_REPOSITORY" "https://github.com/microsoft/mimalloc.git" "GIT_TAG" "v2.3.2" "GIT_SHALLOW" "TRUE"
                    SOURCE_DIR          "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-a284fe3a5508fbbeb433b9036c5bb694/_deps/mimalloc-src"
                    BINARY_DIR          "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-a284fe3a5508fbbeb433b9036c5bb694/_deps/mimalloc-build"
                    CONFIGURE_COMMAND   ""
                    BUILD_COMMAND       ""
                    INSTALL_COMMAND     ""
                    TEST_COMMAND        ""
                    USES_TERMINAL_DOWNLOAD  YES
                    USES_TERMINAL_UPDATE    YES
                    USES_TERMINAL_PATCH     YES
)


