#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=03:00:00
#PBS -b 1

# Main sweep payload is about 70 minutes.  The registered inner maximum is
# dependency 300 + build/witness 1800 + sweep/retry 7200 + collection 300 +
# finalize 600 = 10200 seconds, strictly below the 10800 second request.
set -Eeuo pipefail
umask 077

CURRENT_STAGE=bootstrap
FAILURE_WRITTEN=0
PY=""
OUTPUT=""

write_failure_receipt() {
  local rc=$1 stage=$2 message=$3
  [[ "$FAILURE_WRITTEN" -eq 0 ]] || return 0
  FAILURE_WRITTEN=1
  [[ -n "$OUTPUT" && -n "$PY" ]] || {
    printf 'ss2pl lock study failure before receipt path/interpreter: rc=%s stage=%s %s\n' \
      "$rc" "$stage" "$message" >&2
    return 0
  }
  local receipt="${OUTPUT}.job-failure.json"
  "$PY" -I -B - "$receipt" "$rc" "$stage" "$message" \
    "${PBS_JOBID:-}" "${SS2PL_STUDY_MODE:-}" <<'PY' || true
import json, os, pathlib, sys, tempfile, time
path, rc, stage, message, job, mode = sys.argv[1:]
destination = pathlib.Path(path)
destination.parent.mkdir(parents=True, exist_ok=True)
doc = {
    "schema_version": "ss2pl-lock-study-job-failure/v1",
    "recorded_epoch_s": int(time.time()),
    "pbs_jobid": job,
    "mode": mode,
    "stage": stage,
    "returncode": int(rc),
    "message": message,
}
fd, temporary = tempfile.mkstemp(prefix="." + destination.name + ".", dir=destination.parent)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    json.dump(doc, handle, sort_keys=True, indent=2)
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
os.replace(temporary, destination)
PY
}

on_error() {
  local rc=$? line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure_receipt "$rc" "$CURRENT_STAGE" "command failed at line $line"
  exit "$rc"
}
trap on_error ERR

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID and PBS_O_WORKDIR are required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

MODE=${SS2PL_STUDY_MODE:-}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "--mode requires a value" >&2; exit 2; }
      MODE=$2
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done
case "$MODE" in
  sweep|controls|replication) ;;
  *) echo "mode must be sweep, controls, or replication" >&2; exit 2 ;;
esac
export SS2PL_STUDY_MODE=$MODE

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
unset LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH
unset COMPILER_PATH GCC_EXEC_PREFIX CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE
unset CMAKE_GENERATOR CMAKE_GENERATOR_INSTANCE CMAKE_GENERATOR_PLATFORM
unset CMAKE_GENERATOR_TOOLSET
unset CMAKE_PROJECT_INCLUDE CMAKE_PROJECT_INCLUDE_BEFORE
unset CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_C_COMPILER_LAUNCHER
unset CMAKE_CXX_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS
while IFS= read -r env_name; do
  case "$env_name" in
    GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*) unset "$env_name" ;;
  esac
done < <(compgen -e)

CURRENT_STAGE=interpreter
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" && -x "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)' \
      >/dev/null 2>&1; then
    resolved_python=$("$resolved" -I -B -c \
      'import os, sys; print(os.path.realpath(sys.executable))')
    if [[ "$resolved_python" == /* && -x "$resolved_python" ]]; then
      PY=$resolved_python
      break
    fi
  fi
done
[[ -n "$PY" ]] || { echo "Python 3.10 is required" >&2; exit 2; }

export PATH="/usr/bin:/bin"
for command_name in mkdir ln; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required bootstrap command is unavailable: $command_name" >&2
    exit 2
  }
done

export TMPDIR="/scr/${PBS_JOBID//:/_}-ss2pl-lock-study"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created: $TMPDIR" >&2
  exit 2
fi
mkdir "$TMPDIR/python-shim"
ln -s "$PY" "$TMPDIR/python-shim/python3"
SANITIZED_PATH="$TMPDIR/python-shim:/usr/bin:/bin"
for candidate in /opt/nec/nqsv/bin /system/tool/bin; do
  [[ -d "$candidate" ]] || continue
  SANITIZED_PATH="${SANITIZED_PATH}:$candidate"
done
export PATH="$SANITIZED_PATH"

REQUIRED_COMMANDS=(git cmake cc c++ make as ld ar ranlib nm strings timeout date)
MISSING_COMMANDS=()
for command_name in "${REQUIRED_COMMANDS[@]}"; do
  command -v -- "$command_name" >/dev/null 2>&1 || MISSING_COMMANDS+=("$command_name")
done
if [[ ${#MISSING_COMMANDS[@]} -ne 0 ]]; then
  echo "required commands are unavailable before study start: ${MISSING_COMMANDS[*]}" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
POLICY="$REPO_ROOT/tools/pegasus/policy.json"
PATCH=${SS2PL_STUDY_PATCH:-"$REPO_ROOT/patches/ss2pl-lock-protocol-study.patch"}
OUTPUT=${SS2PL_STUDY_OUTPUT:-}
THIRDPARTY_ROOT=${SS2PL_STUDY_THIRDPARTY_ROOT:-}
[[ -n "$OUTPUT" && "$OUTPUT" == /* ]] || {
  echo "SS2PL_STUDY_OUTPUT must be an absolute, job-unique path" >&2
  exit 2
}
[[ -n "$THIRDPARTY_ROOT" && "$THIRDPARTY_ROOT" == /* ]] || {
  echo "SS2PL_STUDY_THIRDPARTY_ROOT must be absolute" >&2
  exit 2
}
[[ -f "$PATCH" && ! -L "$PATCH" ]] || { echo "patch is missing or a symlink" >&2; exit 2; }
[[ ! -e "$OUTPUT" && ! -e "${OUTPUT}.job-failure.json" ]] || {
  echo "output or failure receipt already exists" >&2
  exit 2
}

CURRENT_STAGE=policy_budget
readarray -t POLICY_VALUES < <("$PY" -I -B - "$POLICY" "$MODE" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))["ss2pl_lock_study"]
mode = sys.argv[2]
for value in (
    policy["walltime_s"], policy["dependency_build_cap_s"],
    policy["build_and_witness_cap_s"], policy["mode_run_cap_s"][mode],
    policy["collection_cap_s"], policy["finalize_reserve_s"],
    policy["max_block_retries"], policy["clocks_per_us"],
):
    print(value)
PY
)
[[ ${#POLICY_VALUES[@]} -eq 8 ]]
WALLTIME_S=${POLICY_VALUES[0]}
DEPENDENCY_CAP_S=${POLICY_VALUES[1]}
BUILD_CAP_S=${POLICY_VALUES[2]}
RUN_CAP_S=${POLICY_VALUES[3]}
COLLECTION_CAP_S=${POLICY_VALUES[4]}
FINALIZE_RESERVE_S=${POLICY_VALUES[5]}
MAX_BLOCK_RETRIES=${POLICY_VALUES[6]}
CLOCKS_PER_US=${POLICY_VALUES[7]}
INNER_TOTAL_S=$((DEPENDENCY_CAP_S + BUILD_CAP_S + RUN_CAP_S + COLLECTION_CAP_S + FINALIZE_RESERVE_S))
if [[ "$WALLTIME_S" -ne 10800 || "$INNER_TOTAL_S" -ge "$WALLTIME_S" ]]; then
  echo "inner budgets plus finalize reserve must be strictly below PBS walltime" >&2
  exit 2
fi

CURRENT_STAGE=dependency_policy
readarray -t DEPENDENCIES < <("$PY" -I -B - "$POLICY" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
block = policy["ss2pl_lock_study"]
for name in ("gflags", "glog"):
    print("\t".join((name, policy[name + "_source_path"], block["dependency_pins"][name])))
PY
)
[[ ${#DEPENDENCIES[@]} -eq 2 ]]
for row in "${DEPENDENCIES[@]}"; do
  IFS=$'\t' read -r name source expected_head <<<"$row"
  [[ -d "$source" && ! -L "$source" ]]
  observed_head=$(git -C "$source" rev-parse HEAD)
  observed_status=$(git -C "$source" status --porcelain --untracked-files=all)
  if [[ "$observed_head" != "$expected_head" || -n "$observed_status" ]]; then
    echo "$name dependency source is not pinned-clean" >&2
    exit 2
  fi
  if [[ "$name" == gflags ]]; then GFLAGS_SOURCE=$source; else GLOG_SOURCE=$source; fi
done

GFLAGS_PREFIX="$TMPDIR/gflags-install"
GLOG_PREFIX="$TMPDIR/glog-install"
DEPENDENCY_DEADLINE=$((SECONDS + DEPENDENCY_CAP_S))
dependency_run() {
  local remaining=$((DEPENDENCY_DEADLINE - SECONDS))
  [[ "$remaining" -gt 0 ]] || return 124
  timeout "$remaining" "$@"
}

CURRENT_STAGE=dependency_build
dependency_run cmake -S "$GFLAGS_SOURCE" -B "$TMPDIR/gflags-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_PREFIX"
dependency_run cmake --build "$TMPDIR/gflags-build" --parallel 48
dependency_run cmake --install "$TMPDIR/gflags-build"
dependency_run cmake -S "$GLOG_SOURCE" -B "$TMPDIR/glog-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_PREFIX" \
  "-DCMAKE_INSTALL_PREFIX=$GLOG_PREFIX"
dependency_run cmake --build "$TMPDIR/glog-build" --parallel 48
dependency_run cmake --install "$TMPDIR/glog-build"

CURRENT_STAGE=driver
DRIVER_FINALIZE_CAP_S=$((FINALIZE_RESERVE_S / 2))
SHELL_FINALIZE_CAP_S=$((FINALIZE_RESERVE_S - DRIVER_FINALIZE_CAP_S))
DRIVER_CAP_S=$((BUILD_CAP_S + RUN_CAP_S + COLLECTION_CAP_S + DRIVER_FINALIZE_CAP_S))
OCCASION_ID="${MODE}-${PBS_JOBID//:/_}-$(date -u +%Y%m%dT%H%M%SZ)"
timeout "$DRIVER_CAP_S" "$PY" -I -B \
  "$REPO_ROOT/tools/pegasus/run_ss2pl_lock_study.py" \
  --repo-root "$REPO_ROOT" \
  --patch "$PATCH" \
  --output "$OUTPUT" \
  --scratch-root "$TMPDIR" \
  --gflags-prefix "$GFLAGS_PREFIX" \
  --glog-prefix "$GLOG_PREFIX" \
  --thirdparty-root "$THIRDPARTY_ROOT" \
  --clocks-per-us "$CLOCKS_PER_US" \
  --mode "$MODE" \
  --max-block-retries "$MAX_BLOCK_RETRIES" \
  --jobs 48 \
  --build-cap-s "$BUILD_CAP_S" \
  --run-cap-s "$RUN_CAP_S" \
  --collection-cap-s "$COLLECTION_CAP_S" \
  --occasion-id "$OCCASION_ID"

CURRENT_STAGE=finalize
timeout "$SHELL_FINALIZE_CAP_S" "$PY" -I -B - "$OUTPUT" "$MODE" "$PBS_JOBID" <<'PY'
import json, sys
path, mode, job = sys.argv[1:]
document = json.load(open(path, encoding="utf-8"))
assert document["schema_version"] == "ss2pl-lock-study/v1"
assert document["status"] == "complete"
assert document["mode"] == mode
assert document["occasion"]["pbs_jobid"] == job
assert document["cleanup"] == {
    "reverse_attempted": True,
    "reverse_succeeded": True,
    "git_status_porcelain": "",
}
PY
exit 0
