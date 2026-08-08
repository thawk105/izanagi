#!/bin/bash
set -uo pipefail

[[ $# -eq 1 && -n ${IZANAGI_T139_R4_PYTHON:-} &&
   -n ${IZANAGI_T139_R4_CONTRACT_BLOB:-} &&
   -n ${IZANAGI_CCBENCH_SNAPSHOT:-} &&
   -n ${IZANAGI_THIRDPARTY_SOURCE_ROOT:-} &&
   -n ${IZANAGI_GFLAGS_INSTALL:-} && -n ${IZANAGI_GLOG_INSTALL:-} &&
   -n ${IZANAGI_GFLAGS_SRC_HEAD:-} && -n ${IZANAGI_GLOG_SRC_HEAD:-} &&
   -n ${IZANAGI_RUN_COMMIT:-} && -n ${PBS_JOBID:-} ]] || exit 2

OUT=$(realpath -e "$1") || exit 2
PYTHON=$(realpath -e "$IZANAGI_T139_R4_PYTHON") || exit 2
CONTRACT=$(realpath -e "$IZANAGI_T139_R4_CONTRACT_BLOB") || exit 2
SNAPSHOT=$(realpath -e "$IZANAGI_CCBENCH_SNAPSHOT") || exit 2
TP=$(realpath -e "$IZANAGI_THIRDPARTY_SOURCE_ROOT") || exit 2
GFLAGS_INSTALL=$(realpath -e "$IZANAGI_GFLAGS_INSTALL") || exit 2
GLOG_INSTALL=$(realpath -e "$IZANAGI_GLOG_INSTALL") || exit 2
STATE="$OUT/state.json"
STAGE=${IZANAGI_PROBE_STAGE:-${TMPDIR:-/tmp}}
PREFIX="$GFLAGS_INSTALL;$GLOG_INSTALL"
export LC_ALL=C
unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS CMAKE_TOOLCHAIN_FILE

DRIVER_START_MONOTONIC_NS=$(python3 -I -B "$PYTHON" monotonic-ns) || exit 2
DRIVER_CAP_NS=1895000000000

driver_run() {
  local phase_cap_s=$1 now_ns remaining_ns remaining_s limit_s
  shift
  now_ns=$(python3 -I -B "$PYTHON" monotonic-ns) || return 8
  remaining_ns=$((DRIVER_START_MONOTONIC_NS + DRIVER_CAP_NS - now_ns))
  (( remaining_ns > 0 )) || return 8
  remaining_s=$(((remaining_ns + 999999999) / 1000000000))
  limit_s=$phase_cap_s
  (( limit_s < remaining_s )) || limit_s=$remaining_s
  timeout --foreground --signal=TERM --kill-after=10 "${limit_s}s" "$@"
}

FINALIZED=0
finalize_driver() {
  local original_rc=$? final_rc=0
  trap - EXIT TERM INT
  set +e
  if [[ $FINALIZED -eq 0 && -s $STATE ]]; then
    FINALIZED=1
    python3 -I -B "$PYTHON" finalize --state "$STATE" --output "$OUT" \
      --exit-rc "$original_rc" \
      >"$OUT/decision.txt" 2>"$OUT/finalize.stderr"
    final_rc=$?
  fi
  if (( original_rc == 0 && final_rc != 0 )); then
    original_rc=$final_rc
  fi
  exit "$original_rc"
}
trap finalize_driver EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

python3 -I -B "$PYTHON" init-state --contract "$CONTRACT" --state "$STATE" \
  --commit "$IZANAGI_RUN_COMMIT" --jobid "$PBS_JOBID" || exit 2

mkdir "$STAGE/ccbench-stock"
if ! driver_run 75 cp -a "$SNAPSHOT/." "$STAGE/ccbench-stock/"; then
  exit 8
fi
if ! driver_run 15 diff --brief --recursive --no-dereference \
    "$SNAPSHOT" "$STAGE/ccbench-stock" >/dev/null; then
  exit 8
fi
chmod -R u+w "$STAGE/ccbench-stock"
SOURCE=$(realpath -e "$STAGE/ccbench-stock") || exit 2

if ! driver_run 15 python3 -I -B "$PYTHON" capture-compilers --state "$STATE" \
    --output "$OUT"; then
  exit 13
fi
mapfile -t COMPILER_PATHS < <(python3 -I -B - "$STATE" <<'PY'
import json
import sys
state = json.load(open(sys.argv[1], encoding="utf-8"))
print(state["compilers"]["gcc"]["realpath"])
print(state["compilers"]["gxx"]["realpath"])
PY
)
[[ ${#COMPILER_PATHS[@]} -eq 2 ]] || exit 13
GCC_REAL=${COMPILER_PATHS[0]}
GXX_REAL=${COMPILER_PATHS[1]}

build_status() {
  python3 -I -B - "$STATE" "$1" <<'PY'
import json
import sys
state = json.load(open(sys.argv[1], encoding="utf-8"))
index = {"trace0": 0, "trace1": 1}[sys.argv[2]]
raise SystemExit(0 if state["builds"][index]["status"] == "success" else 1)
PY
}

record_one_build() {
  local kind=$1 trace=$2 analysis=$3 configure_cap=$4 build_cap=$5
  local build_dir="$STAGE/build-$kind"
  local configure_log="$OUT/configure-$kind.log" build_log="$OUT/build-$kind.log"
  local argv_json="$OUT/configure-$kind.argv.json"
  local config_start config_end build_start build_end config_elapsed=0 build_elapsed=0
  local config_rc=0 build_rc=0 rc=0 status=success

  local -a configure_argv=(
    cmake -S "$SOURCE" -B "$build_dir"
    -DCMAKE_BUILD_TYPE=Release
    -DENABLE_SANITIZER=OFF
    "-DCCBENCH_TRACE=$trace"
    -DCCBENCH_BACK_OFF=0
    -DCCBENCH_BACKOFF_FIXED=-1
    -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
    -DCCBENCH_NO_WAIT_OF_TICTOC=0
    -DCCBENCH_WAL=0
    -DCCBENCH_CCACHE=OFF
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
    -DCMAKE_C_COMPILER_LAUNCHER=
    -DCMAKE_CXX_COMPILER_LAUNCHER=
    -DRULE_LAUNCH_COMPILE=
    -DCMAKE_TOOLCHAIN_FILE=
    "-DCMAKE_PREFIX_PATH=$PREFIX"
    "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$TP/masstree"
    "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$TP/mimalloc"
    "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$TP/googletest"
    "-DIZANAGI_GFLAGS_SRC_HEAD=$IZANAGI_GFLAGS_SRC_HEAD"
    "-DIZANAGI_GLOG_SRC_HEAD=$IZANAGI_GLOG_SRC_HEAD"
    "-DCMAKE_C_COMPILER=$GCC_REAL"
    "-DCMAKE_CXX_COMPILER=$GXX_REAL"
    "-DCCBENCH_ADD_ANALYSIS=$analysis"
    -DCMAKE_CXX_FLAGS=
  )
  python3 -I -B - "$argv_json" "${configure_argv[@]}" <<'PY'
import json
import sys
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False)
    handle.write("\n")
PY

  if ! driver_run 15 python3 -I -B "$PYTHON" recheck-compilers \
      --state "$STATE" --label "before-$kind-configure"; then
    status=failed
    rc=13
    : >"$configure_log"
    : >"$build_log"
  else
    config_start=$(python3 -I -B "$PYTHON" monotonic-ns)
    driver_run "$configure_cap" "${configure_argv[@]}" >"$configure_log" 2>&1
    config_rc=$?
    config_end=$(python3 -I -B "$PYTHON" monotonic-ns)
    config_elapsed=$((config_end - config_start))
    if (( config_rc != 0 )); then
      status=failed
      rc=$config_rc
      : >"$build_log"
    else
      build_start=$(python3 -I -B "$PYTHON" monotonic-ns)
      driver_run "$build_cap" cmake --build "$build_dir" --target ycsb_silo.exe -j 48 \
        >"$build_log" 2>&1
      build_rc=$?
      build_end=$(python3 -I -B "$PYTHON" monotonic-ns)
      build_elapsed=$((build_end - build_start))
      if (( build_rc != 0 )); then
        status=failed
        rc=$build_rc
      fi
    fi
  fi

  local -a record=(
    python3 -I -B "$PYTHON" record-build
    --state "$STATE" --kind "$kind" --status "$status" --returncode "$rc"
    --configure-elapsed-ns "$config_elapsed" --build-elapsed-ns "$build_elapsed"
    --configure-argv-json "$argv_json" --configure-log "$configure_log"
    --build-log "$build_log"
  )
  if [[ -f $build_dir/CMakeCache.txt ]]; then
    record+=(--cache "$build_dir/CMakeCache.txt")
  fi
  if [[ -f $build_dir/compile_commands.json ]]; then
    record+=(--compile-commands "$build_dir/compile_commands.json")
  fi
  if [[ -f $build_dir/cc/silo/ycsb_silo.exe ]]; then
    record+=(--binary "$build_dir/cc/silo/ycsb_silo.exe")
  fi
  "${record[@]}"
}

# The preflight window is intentionally after this TRACE=0 build and its
# CMakeCache/compile argv/prebuilt-binary validation.
record_one_build trace0 0 0 60 180
TRACE0_READY=0
if build_status trace0; then
  TRACE0_READY=1
  driver_run 810 python3 -I -B "$PYTHON" sample --state "$STATE" \
    --binary "$STAGE/build-trace0/cc/silo/ycsb_silo.exe" --output "$OUT"
  SAMPLE_RC=$?
else
  SAMPLE_RC=12
fi

# TRACE=1 is a build-only witness after every attempted observation window.
# Its independently frozen caps are configure=90 seconds and build=420 seconds.
record_one_build trace1 1 1 90 420

python3 -I -B "$PYTHON" finalize --state "$STATE" --output "$OUT" \
  --exit-rc 0 \
  >"$OUT/decision.txt" 2>"$OUT/finalize.stderr"
FINAL_RC=$?
if [[ -s $OUT/receipt.json ]]; then FINALIZED=1; fi
if (( TRACE0_READY == 0 || SAMPLE_RC != 0 || FINAL_RC != 0 )); then
  exit 12
fi
exit 0
