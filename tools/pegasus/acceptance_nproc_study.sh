#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=04:00:00
#PBS -b 1

# Full: setup 900 + 7 blocks * (600 + 600 + 600) + finalize 300 =
# 13800 seconds, strictly below the requested 14400 seconds.
set -Eeuo pipefail
umask 077

CURRENT_STAGE=bootstrap
FAILURE_WRITTEN=0
PY=""
OUTPUT=""
MODE="${IZANAGI_ACCEPTANCE_NPROC_MODE:-}"

write_failure_receipt() {
  local rc=$1 stage=$2 message=$3
  [[ "$FAILURE_WRITTEN" -eq 0 ]] || return 0
  FAILURE_WRITTEN=1
  [[ -n "$OUTPUT" && -n "$PY" ]] || {
    printf 'acceptance nproc study failed before receipt setup: rc=%s stage=%s %s\n' \
      "$rc" "$stage" "$message" >&2
    return 0
  }
  local receipt="${OUTPUT}.job-failure.json"
  "$PY" -I -B - "$receipt" "$rc" "$stage" "$message" \
    "${PBS_JOBID:-}" "$MODE" <<'PY' || true
import json, os, pathlib, sys, time
path, rc, stage, message, job, mode = sys.argv[1:]
document = {
    "message": message,
    "mode": mode,
    "pbs_jobid": job,
    "recorded_epoch_s": int(time.time()),
    "returncode": int(rc),
    "schema_version": "izanagi-acceptance-nproc-study-job-failure/v1",
    "stage": stage,
}
destination = pathlib.Path(path)
destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
    json.dump(document, handle, ensure_ascii=True, indent=2, sort_keys=True)
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
directory_fd = os.open(destination.parent, os.O_RDONLY)
try:
    os.fsync(directory_fd)
finally:
    os.close(directory_fd)
PY
}

on_error() {
  local rc=$? line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure_receipt "$rc" "$CURRENT_STAGE" "command failed at line $line"
  exit "$rc"
}

on_signal() {
  local signum=$1
  local rc=$((128 + signum))
  trap - ERR TERM HUP INT
  write_failure_receipt "$rc" "$CURRENT_STAGE" "job script received signal $signum"
  exit "$rc"
}

on_exit() {
  local rc=$?
  if [[ "$rc" -ne 0 ]]; then
    write_failure_receipt "$rc" "$CURRENT_STAGE" "job script exited nonzero"
  fi
}

trap on_error ERR
trap 'on_signal 15' TERM
trap 'on_signal 1' HUP
trap 'on_signal 2' INT
trap on_exit EXIT

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID and PBS_O_WORKDIR are required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi
case "$MODE" in
  smoke|full) ;;
  *) echo "IZANAGI_ACCEPTANCE_NPROC_MODE must be smoke or full" >&2; exit 2 ;;
esac

SEED=${IZANAGI_ACCEPTANCE_NPROC_SEED:-}
OUTPUT=${IZANAGI_ACCEPTANCE_NPROC_OUTPUT:-}
[[ -n "$SEED" ]] || { echo "IZANAGI_ACCEPTANCE_NPROC_SEED is required" >&2; exit 2; }
[[ -n "$OUTPUT" && "$OUTPUT" == /* ]] || {
  echo "IZANAGI_ACCEPTANCE_NPROC_OUTPUT must be an absolute, job-unique path" >&2
  exit 2
}
[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" && ! -e "${OUTPUT}.job-failure.json" ]] || {
  echo "output or failure receipt already exists" >&2
  exit 2
}

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
unset LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH
unset COMPILER_PATH GCC_EXEC_PREFIX CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTEST_ADDOPTS PYTEST_PLUGINS MAKEFLAGS
while IFS= read -r env_name; do
  case "$env_name" in
    GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*|XDG_*) unset "$env_name" ;;
  esac
done < <(compgen -e)

CURRENT_STAGE=interpreter
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" && -x "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY=$resolved
    break
  fi
done
[[ -n "$PY" ]] || { echo "Python 3.10 is required" >&2; exit 2; }

export PATH="/usr/bin:/bin"
for candidate in /opt/nec/nqsv/bin /system/tool/bin; do
  [[ -d "$candidate" ]] || continue
  PATH="${PATH}:$candidate"
done
export PATH
for command_name in git qstat timeout mkdir ln; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required command is unavailable: $command_name" >&2
    exit 2
  }
done

export TMPDIR="/scr/${PBS_JOBID//:/_}-acceptance-nproc-study"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created: $TMPDIR" >&2
  exit 2
fi
mkdir "$TMPDIR/python-shim" "$TMPDIR/job-home" "$TMPDIR/job-xdg"
ln -s "$PY" "$TMPDIR/python-shim/python3"
ln -s "$PY" "$TMPDIR/python-shim/python3.10"
export PATH="$TMPDIR/python-shim:$PATH"
export HOME="$TMPDIR/job-home"
export XDG_CACHE_HOME="$TMPDIR/job-xdg/cache"
export XDG_CONFIG_HOME="$TMPDIR/job-xdg/config"
export XDG_DATA_HOME="$TMPDIR/job-xdg/data"
export XDG_STATE_HOME="$TMPDIR/job-xdg/state"
mkdir "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME"

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
DRIVER="$REPO_ROOT/tools/pegasus/run_acceptance_nproc_study.py"
[[ -f "$DRIVER" && ! -L "$DRIVER" ]] || { echo "study driver is missing or a symlink" >&2; exit 2; }

REQUESTED_ELAPSTIM_S=14400
SETUP_CAP_S=${IZANAGI_ACCEPTANCE_NPROC_SETUP_CAP_S:-900}
TIMEOUT_16_S=${IZANAGI_ACCEPTANCE_NPROC_TIMEOUT_16_S:-600}
TIMEOUT_32_S=${IZANAGI_ACCEPTANCE_NPROC_TIMEOUT_32_S:-600}
TIMEOUT_48_S=${IZANAGI_ACCEPTANCE_NPROC_TIMEOUT_48_S:-600}
FINALIZE_RESERVE_S=${IZANAGI_ACCEPTANCE_NPROC_FINALIZE_RESERVE_S:-300}
MARGIN_S=${IZANAGI_ACCEPTANCE_NPROC_MARGIN_S:-60}
for numeric_value in \
  "$SETUP_CAP_S" "$TIMEOUT_16_S" "$TIMEOUT_32_S" "$TIMEOUT_48_S" \
  "$FINALIZE_RESERVE_S" "$MARGIN_S"; do
  [[ "$numeric_value" =~ ^[1-9][0-9]*$ ]] || {
    echo "all study budget overrides must be positive decimal integers" >&2
    exit 2
  }
done
if [[ "$MODE" == full ]]; then BLOCKS=7; else BLOCKS=1; fi
PLANNED_S=$((SETUP_CAP_S + BLOCKS * (TIMEOUT_16_S + TIMEOUT_32_S + TIMEOUT_48_S) + FINALIZE_RESERVE_S))
if [[ "$PLANNED_S" -ge "$REQUESTED_ELAPSTIM_S" ]]; then
  echo "study budget must be strictly below the requested elapstim" >&2
  exit 2
fi

CURRENT_STAGE=driver
DRIVER_CAP_S=$((REQUESTED_ELAPSTIM_S - MARGIN_S))
timeout --signal=TERM --kill-after=10 "$DRIVER_CAP_S" \
  "$PY" -I -B "$DRIVER" \
  --repo-root "$REPO_ROOT" \
  --output "$OUTPUT" \
  --scratch-root "$TMPDIR" \
  --mode "$MODE" \
  --seed "$SEED" \
  --requested-elapstim-s "$REQUESTED_ELAPSTIM_S" \
  --setup-cap-s "$SETUP_CAP_S" \
  --arm-timeout-s "16=$TIMEOUT_16_S" \
  --arm-timeout-s "32=$TIMEOUT_32_S" \
  --arm-timeout-s "48=$TIMEOUT_48_S" \
  --finalize-reserve-s "$FINALIZE_RESERVE_S" \
  --margin-s "$MARGIN_S" \
  --python-command python3.10

CURRENT_STAGE=finalize
timeout 120 "$PY" -I -B "$DRIVER" \
  --validate-receipt "$OUTPUT" --expected-mode "$MODE"

CURRENT_STAGE=complete
exit 0
