# Install script for directory: /scr/0_906428.nqsv/izanagi_wt_c1ru25c5/wt

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

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/_deps/mimalloc-build/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/_deps/googletest-build/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/cicada/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/d2pl/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/ermia/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/mocc/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/mvto/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/oze/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/si/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/silo/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/ss2pl/cmake_install.cmake")
  include("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/cc/tictoc/cmake_install.cmake")

endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-789626-0850f6764b6bfb0d1f6ea174fdffa691/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
