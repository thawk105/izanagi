set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING "static backoff")
set(CCBENCH_BACKOFF_NOINLINE 0 CACHE STRING "diagnostic switch")

function(ccbench_universal_definitions out_var)
  set(${out_var}
    BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}
    BACKOFF_NOINLINE=${CCBENCH_BACKOFF_NOINLINE}
    PARENT_SCOPE)
endfunction()
