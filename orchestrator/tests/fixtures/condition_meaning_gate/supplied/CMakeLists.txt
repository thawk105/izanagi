cmake_minimum_required(VERSION 3.16)
project(condition_gate_fixture LANGUAGES CXX)

include(cmake/Options.cmake)
ccbench_universal_definitions(condition_gate_defines)
add_executable(ycsb_silo.exe cc/silo/transaction.cc)
target_compile_definitions(ycsb_silo.exe PRIVATE ${condition_gate_defines})
