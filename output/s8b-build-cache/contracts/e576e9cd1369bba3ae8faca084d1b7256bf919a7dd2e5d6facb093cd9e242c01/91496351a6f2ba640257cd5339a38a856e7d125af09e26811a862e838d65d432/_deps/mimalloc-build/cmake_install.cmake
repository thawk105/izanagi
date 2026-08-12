# Install script for directory: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/x86_64-linux-gnu-objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/mimalloc-2.3" TYPE STATIC_LIBRARY FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-build/libmimalloc.a")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3/mimalloc.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3/mimalloc.cmake"
         "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-build/CMakeFiles/Export/0c39a190abd935ce55228f450627e544/mimalloc.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3/mimalloc-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3/mimalloc.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-build/CMakeFiles/Export/0c39a190abd935ce55228f450627e544/mimalloc.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-build/CMakeFiles/Export/0c39a190abd935ce55228f450627e544/mimalloc-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/include/mimalloc.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/include/mimalloc-override.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/include/mimalloc-new-delete.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/include/mimalloc-stats.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/cmake/mimalloc-config.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/mimalloc-2.3" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-src/cmake/mimalloc-config-version.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-6b773f712657fb7b013c074a73e134fa/_deps/mimalloc-build/mimalloc.pc")
endif()

