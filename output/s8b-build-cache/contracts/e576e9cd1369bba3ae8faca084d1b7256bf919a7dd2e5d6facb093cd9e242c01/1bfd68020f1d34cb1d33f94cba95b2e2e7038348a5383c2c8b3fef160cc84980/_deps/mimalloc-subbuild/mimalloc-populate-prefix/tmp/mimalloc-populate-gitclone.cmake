# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

if(EXISTS "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitclone-lastrun.txt" AND EXISTS "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitinfo.txt" AND
  "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitclone-lastrun.txt" IS_NEWER_THAN "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitinfo.txt")
  message(STATUS
    "Avoiding repeated git clone, stamp file is up to date: "
    "'/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitclone-lastrun.txt'"
  )
  return()
endif()

execute_process(
  COMMAND ${CMAKE_COMMAND} -E rm -rf "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-src"
  RESULT_VARIABLE error_code
)
if(error_code)
  message(FATAL_ERROR "Failed to remove directory: '/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-src'")
endif()

# try the clone 3 times in case there is an odd git clone issue
set(error_code 1)
set(number_of_tries 0)
while(error_code AND number_of_tries LESS 3)
  execute_process(
    COMMAND "/bin/git" 
            clone --no-checkout --depth 1 --no-single-branch --config "advice.detachedHead=false" "https://github.com/microsoft/mimalloc.git" "mimalloc-src"
    WORKING_DIRECTORY "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps"
    RESULT_VARIABLE error_code
  )
  math(EXPR number_of_tries "${number_of_tries} + 1")
endwhile()
if(number_of_tries GREATER 1)
  message(STATUS "Had to git clone more than once: ${number_of_tries} times.")
endif()
if(error_code)
  message(FATAL_ERROR "Failed to clone repository: 'https://github.com/microsoft/mimalloc.git'")
endif()

execute_process(
  COMMAND "/bin/git" 
          checkout "v2.3.2" --
  WORKING_DIRECTORY "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-src"
  RESULT_VARIABLE error_code
)
if(error_code)
  message(FATAL_ERROR "Failed to checkout tag: 'v2.3.2'")
endif()

set(init_submodules TRUE)
if(init_submodules)
  execute_process(
    COMMAND "/bin/git" 
            submodule update --recursive --init 
    WORKING_DIRECTORY "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-src"
    RESULT_VARIABLE error_code
  )
endif()
if(error_code)
  message(FATAL_ERROR "Failed to update submodules in: '/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-src'")
endif()

# Complete success, update the script-last-run stamp file:
#
execute_process(
  COMMAND ${CMAKE_COMMAND} -E copy "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitinfo.txt" "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitclone-lastrun.txt"
  RESULT_VARIABLE error_code
)
if(error_code)
  message(FATAL_ERROR "Failed to copy script-last-run stamp file: '/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t748-pilot-path/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/.staging-2169677-3109830a897143b8e06ca45b443d19c0/_deps/mimalloc-subbuild/mimalloc-populate-prefix/src/mimalloc-populate-stamp/mimalloc-populate-gitclone-lastrun.txt'")
endif()
