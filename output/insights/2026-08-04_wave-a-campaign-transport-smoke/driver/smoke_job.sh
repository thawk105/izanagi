#!/bin/bash
# 出典: tools/pegasus/dispatch_compute.py:26-27
# 出典: tools/pegasus/dispatch_compute.py:452-455
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=6:00:00
#PBS -N izanagi-wave-a-smoke
# 出典: tools/pegasus/floor_campaign.sh:14-15
set -Eeuo pipefail
umask 077

if [[ $# -ne 0 ]]; then
  echo "usage: qsub -v IZANAGI_SMOKE_PROGRESS_DIR=/work/ABSOLUTE_PROGRESS_DIR smoke_job.sh" >&2
  exit 2
fi
if [[ -z "${IZANAGI_SMOKE_PROGRESS_DIR:-}" ]]; then
  echo "IZANAGI_SMOKE_PROGRESS_DIR is required and must not be empty" >&2
  exit 2
fi
PROGRESS_DIR=$IZANAGI_SMOKE_PROGRESS_DIR
if [[ "$PROGRESS_DIR" != /work/* || "$PROGRESS_DIR" == *$'\n'* ]]; then
  echo "progress-dir must be an absolute path below /work" >&2
  exit 2
fi
mkdir -p -- "$PROGRESS_DIR"
PROGRESS_DIR=$(realpath -e -- "$PROGRESS_DIR")
if [[ "$PROGRESS_DIR" != /work/* || ! -d "$PROGRESS_DIR" ]]; then
  echo "resolved progress-dir must be a directory below /work" >&2
  exit 2
fi
JOB_PROGRESS="$PROGRESS_DIR/job-progress.jsonl"
RESULT="$PROGRESS_DIR/job-failure.json"
MARKER="$PROGRESS_DIR/compute-visible.json"

write_job_marker() {
  local event=$1
  local rc=${2:-}
  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if [[ -n "$rc" ]]; then
    printf '{"event":"%s","rc":%d,"ts":"%s"}\n' "$event" "$rc" "$now" >>"$JOB_PROGRESS"
  else
    printf '{"event":"%s","ts":"%s"}\n' "$event" "$now" >>"$JOB_PROGRESS"
  fi
  sync -d "$JOB_PROGRESS"
}

write_failure() {
  local rc stage message
  if [[ $# -eq 1 ]]; then
    rc=16
    stage=$1
    message="dispatch-compatible admission failure"
  else
    rc=$1
    stage=$2
    message=$3
  fi
  local tmp="${RESULT}.tmp.$$"
  printf '{"stage":"%s","child_rc":%d,"message":"%s","pbs_jobid":"%s"}\n' \
    "$stage" "$rc" "$message" "${PBS_JOBID:-unknown}" >"$tmp"
  mv "$tmp" "$RESULT"
  sync -d "$RESULT"
  write_job_marker "failure-$stage" "$rc"
}

on_exit() {
  local rc=$?
  trap - EXIT ERR
  write_job_marker job-end "$rc" || true
  exit "$rc"
}
on_err() {
  local rc=$?
  trap - ERR
  write_failure "$rc" shell "command failed at line ${BASH_LINENO[0]:-unknown}"
  exit "$rc"
}
trap on_exit EXIT
trap on_err ERR
write_job_marker job-start

# 出典: tools/pegasus/floor_campaign.sh:18-33
if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

REPO=$(cd "$PBS_O_WORKDIR" && pwd -P)
PROBE="$TMPDIR/interpreter_probe.py"
printf '%s\n' \
  'import sys' \
  'if sys.version_info < (3, 10):' \
  '    raise SystemExit(1)' \
  'raise SystemExit(0)' >"$PROBE"
sync -d "$PROBE"

# 出典: tools/pegasus/dispatch_compute.py:474-482
host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
    write_failure hostname
    exit 16
fi
marker_tmp="${MARKER}.tmp.$$"
printf '{"schema_version":"pegasus-compute-visible/v1","pbs_jobid":"%s","hostname":"%s"}\n' \
    "${PBS_JOBID:-unknown}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

# 出典: tools/pegasus/dispatch_compute.py:129-133
# 出典: tools/pegasus/dispatch_compute.py:484-495
selected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
if [[ -z "$selected" ]]; then
    write_failure interpreter
    exit 16
fi

# 出典: tools/pegasus/dispatch_compute.py:497-502
if ! cd "$REPO"; then
    write_failure cwd
    exit 16
fi

export PATH="$(dirname "$selected"):$PATH"

PY=$selected
TOOLS="$REPO/tools/pegasus"
POLICY="$TOOLS/policy.json"
FLOOR_POLICY="$TOOLS/policies/floor_v1.json"
ATTEMPT_DIR="$PROGRESS_DIR/deps"
mkdir "$ATTEMPT_DIR"
write_job_marker deps-start

# 出典: tools/pegasus/floor_campaign.sh:200-270
printf '%s\n' "$PY" >"$ATTEMPT_DIR/python3.realpath"
"$PY" -I -B --version >"$ATTEMPT_DIR/python3.version" 2>&1
NUMACTL_PATH=$(command -v numactl 2>/dev/null || true)
printf '%s' "$NUMACTL_PATH" >"$ATTEMPT_DIR/numactl.command-v.stdout"
: >"$ATTEMPT_DIR/numactl-hardware.stdout"
: >"$ATTEMPT_DIR/numactl-hardware.stderr"
: >"$ATTEMPT_DIR/numactl-show.stdout"
: >"$ATTEMPT_DIR/numactl-show.stderr"
if [[ -n "$NUMACTL_PATH" ]]; then
  "$NUMACTL_PATH" --hardware >"$ATTEMPT_DIR/numactl-hardware.stdout" \
    2>"$ATTEMPT_DIR/numactl-hardware.stderr" || true
  "$NUMACTL_PATH" --show >"$ATTEMPT_DIR/numactl-show.stdout" \
    2>"$ATTEMPT_DIR/numactl-show.stderr" || true
fi

# 出典: certify_calibration.sh:105-141 @ e9b6f69
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  write_failure 2 policy "policy file missing, not regular, or a symlink"
  exit 2
fi
if [[ ! -f "$FLOOR_POLICY" || -L "$FLOOR_POLICY" ]]; then
  write_failure 2 policy "floor policy file missing, not regular, or a symlink"
  exit 2
fi
policy_output=""
policy_rc=0
policy_output=$("$PY" -I -B - "$POLICY" "$FLOOR_POLICY" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    floor_policy = json.load(handle)
text_fields = (
    "project",
    "queue",
    "gflags_source_path",
    "gflags_expected_head",
    "glog_source_path",
    "glog_expected_head",
)
for key in text_fields:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
if type(policy.get("nodes")) is not int or policy["nodes"] <= 0:
    raise SystemExit("invalid policy field: nodes")
if (
    type(floor_policy.get("floor_walltime_s")) is not int
    or floor_policy["floor_walltime_s"] <= 0
):
    raise SystemExit("invalid floor policy field: floor_walltime_s")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(floor_policy["floor_walltime_s"])
print(policy["gflags_source_path"])
print(policy["gflags_expected_head"])
print(policy["glog_source_path"])
print(policy["glog_expected_head"])
PY
) || policy_rc=$?
if [[ "$policy_rc" -ne 0 ]]; then
  write_failure 2 policy "cannot parse required floor policy"
  exit 2
fi
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 8 ]]; then
  write_failure 2 policy "floor policy yielded an unexpected field count"
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
FLOOR_WALLTIME_S=${policy_values[3]}
GFLAGS_SOURCE_PATH=${policy_values[4]}
GFLAGS_EXPECTED_HEAD=${policy_values[5]}
GLOG_SOURCE_PATH=${policy_values[6]}
GLOG_EXPECTED_HEAD=${policy_values[7]}

if [[ "$PROJECT" != SFC || "$QUEUE" != gen_S || "$NODES" != 1 ]]; then
  write_failure 2 policy "policy does not match the fixed PBS request"
  exit 2
fi

# 出典: tools/pegasus/floor_campaign.sh:703-878
CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
CMAKE_PATH=$(command -v cmake)
realpath -e "$CC_PATH" >"$ATTEMPT_DIR/compiler.path"
realpath -e "$CXX_PATH" >"$ATTEMPT_DIR/cxx.path"
realpath -e "$CMAKE_PATH" >"$ATTEMPT_DIR/cmake.path"
"$CC_PATH" --version >"$ATTEMPT_DIR/compiler.version" 2>&1
"$CXX_PATH" --version >"$ATTEMPT_DIR/cxx.version" 2>&1
"$CMAKE_PATH" --version >"$ATTEMPT_DIR/cmake.version" 2>&1

# 出典: certify_calibration.sh:376-510 @ e9b6f69
if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  write_failure 2 gflags "gflags source path missing"
  exit 2
fi
gflags_head_rc=0
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD \
  2>"$ATTEMPT_DIR/gflags-source-head.stderr") || gflags_head_rc=$?
if [[ "$gflags_head_rc" -ne 0 ]]; then
  write_failure "$gflags_head_rc" gflags "cannot resolve gflags source HEAD"
  exit "$gflags_head_rc"
fi
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$ATTEMPT_DIR/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  write_failure 2 gflags "gflags source HEAD mismatch"
  exit 2
fi
gflags_status_rc=0
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$ATTEMPT_DIR/gflags-source-status.stderr") || gflags_status_rc=$?
if [[ "$gflags_status_rc" -ne 0 ]]; then
  write_failure "$gflags_status_rc" gflags "cannot inspect gflags working tree"
  exit "$gflags_status_rc"
fi
printf '%s' "$GFLAGS_STATUS" >"$ATTEMPT_DIR/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  write_failure 2 gflags "gflags working tree is dirty"
  exit 2
fi

GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
gflags_rc=0
mkdir "$GFLAGS_BUILD_DIR" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "cannot create gflags build directory"
  exit "$gflags_rc"
fi
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-configure.stdout" \
  2>"$ATTEMPT_DIR/gflags-configure.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags configure failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_build_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-build.stdout" \
  2>"$ATTEMPT_DIR/gflags-build.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags build failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_install_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-install.stdout" \
  2>"$ATTEMPT_DIR/gflags-install.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags install failed"
  exit "$gflags_rc"
fi

# 出典: certify_calibration.sh:423-486 @ e9b6f69
if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  write_failure 2 glog "glog source path missing"
  exit 2
fi
glog_head_rc=0
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD \
  2>"$ATTEMPT_DIR/glog-source-head.stderr") || glog_head_rc=$?
if [[ "$glog_head_rc" -ne 0 ]]; then
  write_failure "$glog_head_rc" glog "cannot resolve glog source HEAD"
  exit "$glog_head_rc"
fi
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$ATTEMPT_DIR/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  write_failure 2 glog "glog source HEAD mismatch"
  exit 2
fi
glog_status_rc=0
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$ATTEMPT_DIR/glog-source-status.stderr") || glog_status_rc=$?
if [[ "$glog_status_rc" -ne 0 ]]; then
  write_failure "$glog_status_rc" glog "cannot inspect glog working tree"
  exit "$glog_status_rc"
fi
printf '%s' "$GLOG_STATUS" >"$ATTEMPT_DIR/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  write_failure 2 glog "glog working tree is dirty"
  exit 2
fi

GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
glog_rc=0
mkdir "$GLOG_BUILD_DIR" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "cannot create glog build directory"
  exit "$glog_rc"
fi
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
timeout 120 "${glog_configure_argv[@]}" \
  >"$ATTEMPT_DIR/glog-configure.stdout" \
  2>"$ATTEMPT_DIR/glog-configure.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog configure failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_build_argv[@]}" \
  >"$ATTEMPT_DIR/glog-build.stdout" \
  2>"$ATTEMPT_DIR/glog-build.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog build failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_install_argv[@]}" \
  >"$ATTEMPT_DIR/glog-install.stdout" \
  2>"$ATTEMPT_DIR/glog-install.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog install failed"
  exit "$glog_rc"
fi

CMAKE_PREFIX_PATH_PREVIOUSLY_SET=false
CMAKE_PREFIX_PATH_PREVIOUS_VALUE=""
if [[ ${CMAKE_PREFIX_PATH+x} ]]; then
  CMAKE_PREFIX_PATH_PREVIOUSLY_SET=true
  CMAKE_PREFIX_PATH_PREVIOUS_VALUE=$CMAKE_PREFIX_PATH
fi
export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"
"$PY" -I -B - "$ATTEMPT_DIR/cmake-prefix-path.json" "$CMAKE_PREFIX_PATH_PREVIOUSLY_SET" \
  "$CMAKE_PREFIX_PATH_PREVIOUS_VALUE" "$CMAKE_PREFIX_PATH" <<'PY'
import json
import sys
import time

path, previously_set, previous_value, effective_value = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "previously_set": previously_set == "true",
            "previous_value": previous_value,
            "effective_value": effective_value,
            "overwritten": previously_set == "true",
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

write_job_marker deps-done
DRIVER="$REPO/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py"
write_job_marker driver-start
driver_rc=0
"$selected" -I -B "$DRIVER" \
  --progress-dir "$PROGRESS_DIR" \
  --disposable-smoke-i-understand-this-is-not-sanctioned \
  --allow-coder-derived-build || driver_rc=$?
write_job_marker driver-rc "$driver_rc"
exit "$driver_rc"
