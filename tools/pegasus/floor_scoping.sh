#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=03:00:00
#PBS -b 1
set -Eeuo pipefail
umask 077

if [[ $# -ne 0 ]]; then
  echo "floor_scoping.sh accepts environment variables only" >&2
  exit 2
fi
if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi
if [[ -z "${IZANAGI_SCOPING_OUT_DIR:-}" ]]; then
  echo "IZANAGI_SCOPING_OUT_DIR is required" >&2
  exit 2
fi

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
TOOLS="$REPO_ROOT/tools/pegasus"
POLICY="$TOOLS/policy.json"
OUT_DIR=$(realpath -m -- "$IZANAGI_SCOPING_OUT_DIR") || exit 2
if [[ "$OUT_DIR" == "$REPO_ROOT" || "$OUT_DIR" == "$REPO_ROOT/"* ]]; then
  echo "IZANAGI_SCOPING_OUT_DIR must resolve outside the repository" >&2
  exit 2
fi

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

if ! mkdir "$OUT_DIR"; then
  echo "scoping out-dir already exists or cannot be created (create-only): $OUT_DIR" >&2
  exit 2
fi
PROVENANCE_DIR="$OUT_DIR/provenance"
if ! mkdir "$PROVENANCE_DIR"; then
  echo "cannot create provenance directory (create-only): $PROVENANCE_DIR" >&2
  exit 2
fi
set -o noclobber

fail() {
  local rc=$1
  shift
  printf '%s\n' "$*" >&2
  exit "$rc"
}

# 出典: floor_campaign.sh:157-178。計算 node の python3=3.9 を拒否する版数 gate。
PY=""
py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if "$py_resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY="$py_resolved"
    break
  fi
  py_rejected+="${py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$PY" ]]; then
  fail 2 "no python3 >= 3.10 (rejected: ${py_rejected:-none})"
fi

perf_attempts=()
perf_probe_rc=0
perf stat -x, -e cycles -- /bin/true >/dev/null 2>&1 || perf_probe_rc=$?
perf_command_rc=0
perf_command=$(command -v -- perf 2>/dev/null) || perf_command_rc=$?
perf_attempts+=("PATH perf=${perf_command:-not-found} command_rc=$perf_command_rc probe_rc=$perf_probe_rc")

perf_selected=""
perf_from_fallback=false
if [[ $perf_probe_rc -eq 0 && $perf_command_rc -eq 0 ]]; then
  perf_realpath_rc=0
  perf_selected=$(realpath -e -- "$perf_command" 2>/dev/null) || perf_realpath_rc=$?
  if [[ $perf_realpath_rc -ne 0 || ! -x "$perf_selected" ]]; then
    perf_attempts+=("PATH perf realpath=${perf_selected:-unresolved} realpath_rc=$perf_realpath_rc executable=no")
    perf_selected=""
  fi
fi

if [[ -z "$perf_selected" ]]; then
  for cand in /usr/lib/linux-tools/*/perf /usr/lib/linux-tools-*/perf; do
    cand_realpath_rc=0
    cand_realpath=$(realpath -e -- "$cand" 2>/dev/null) || cand_realpath_rc=$?
    if [[ $cand_realpath_rc -ne 0 ]]; then
      perf_attempts+=("candidate=$cand realpath_rc=$cand_realpath_rc")
      continue
    fi
    if [[ ! -x "$cand_realpath" ]]; then
      perf_attempts+=("candidate=$cand realpath=$cand_realpath executable=no")
      continue
    fi

    cand_probe_rc=0
    "$cand_realpath" stat -x, -e cycles -- /bin/true >/dev/null 2>&1 || cand_probe_rc=$?
    perf_attempts+=("candidate=$cand realpath=$cand_realpath probe_rc=$cand_probe_rc")
    if [[ $cand_probe_rc -eq 0 ]]; then
      perf_selected="$cand_realpath"
      perf_from_fallback=true
      break
    fi
  done
fi

if [[ -z "$perf_selected" ]]; then
  printf '%s\n' "${perf_attempts[@]}" >"$PROVENANCE_DIR/perf-unavailable.txt"
  fail 2 "no usable perf found"
fi

if [[ "$perf_from_fallback" == true ]]; then
  export PATH="${perf_selected%/*}:$PATH"
  hash -r
  perf_recheck_rc=0
  perf stat -x, -e cycles -- /bin/true >/dev/null 2>&1 || perf_recheck_rc=$?
  perf_command_rc=0
  perf_command=$(command -v -- perf 2>/dev/null) || perf_command_rc=$?
  perf_attempts+=("PATH-after-prepend perf=${perf_command:-not-found} command_rc=$perf_command_rc probe_rc=$perf_recheck_rc")
  if [[ $perf_recheck_rc -ne 0 || $perf_command_rc -ne 0 ]]; then
    printf '%s\n' "${perf_attempts[@]}" >"$PROVENANCE_DIR/perf-unavailable.txt"
    fail 2 "selected perf failed after PATH prepend"
  fi
fi

printf '%s\n' "$perf_selected" >"$PROVENANCE_DIR/perf.realpath"
perf_version_rc=0
perf version >"$PROVENANCE_DIR/perf.version" 2>&1 || perf_version_rc=$?
if [[ $perf_version_rc -ne 0 ]]; then
  fail 2 "perf version failed"
fi

printf '%s\n' "$PY" >"$PROVENANCE_DIR/python3.realpath"
"$PY" -I -B --version >"$PROVENANCE_DIR/python3.version" 2>&1
git -C "$REPO_ROOT" rev-parse HEAD >"$PROVENANCE_DIR/git-head.txt"
sha256sum "$0" | awk '{print $1}' >"$PROVENANCE_DIR/executing-script.sha256"
hostname >"$PROVENANCE_DIR/hostname.txt"
qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$PROVENANCE_DIR/qstat-f.stdout" \
  2>"$PROVENANCE_DIR/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$PROVENANCE_DIR/qstat-f.rc"

if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  fail 2 "policy file missing, not regular, or a symlink"
fi
policy_output=$(
  "$PY" -I -B - "$POLICY" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
keys = (
    "gflags_expected_head",
    "glog_expected_head",
)
for key in keys:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
for key in keys:
    print(policy[key])
PY
)
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 2 ]]; then
  fail 2 "policy yielded an unexpected field count"
fi
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=${policy_values[0]}
GLOG_EXPECTED_HEAD=${policy_values[1]}

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
CMAKE_PATH=$(command -v cmake)
realpath -e "$CC_PATH" >"$PROVENANCE_DIR/compiler.path"
realpath -e "$CXX_PATH" >"$PROVENANCE_DIR/cxx.path"
realpath -e "$CMAKE_PATH" >"$PROVENANCE_DIR/cmake.path"
"$CC_PATH" --version >"$PROVENANCE_DIR/compiler.version" 2>&1
"$CXX_PATH" --version >"$PROVENANCE_DIR/cxx.version" 2>&1
"$CMAKE_PATH" --version >"$PROVENANCE_DIR/cmake.version" 2>&1

# 出典: floor_campaign.sh:703-878。pinned gflags/glog build prologue を同手順で踏襲。
if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  fail 2 "gflags source path missing"
fi
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$PROVENANCE_DIR/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  fail 2 "gflags source HEAD mismatch"
fi
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GFLAGS_STATUS" >"$PROVENANCE_DIR/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  fail 2 "gflags working tree is dirty"
fi

GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
mkdir "$GFLAGS_BUILD_DIR"
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}" \
  >"$PROVENANCE_DIR/gflags-configure.stdout" \
  2>"$PROVENANCE_DIR/gflags-configure.stderr"
timeout 60 "${gflags_build_argv[@]}" \
  >"$PROVENANCE_DIR/gflags-build.stdout" \
  2>"$PROVENANCE_DIR/gflags-build.stderr"
timeout 60 "${gflags_install_argv[@]}" \
  >"$PROVENANCE_DIR/gflags-install.stdout" \
  2>"$PROVENANCE_DIR/gflags-install.stderr"

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  fail 2 "glog source path missing"
fi
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$PROVENANCE_DIR/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  fail 2 "glog source HEAD mismatch"
fi
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GLOG_STATUS" >"$PROVENANCE_DIR/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  fail 2 "glog working tree is dirty"
fi

GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
mkdir "$GLOG_BUILD_DIR"
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
  >"$PROVENANCE_DIR/glog-configure.stdout" \
  2>"$PROVENANCE_DIR/glog-configure.stderr"
timeout 120 "${glog_build_argv[@]}" \
  >"$PROVENANCE_DIR/glog-build.stdout" \
  2>"$PROVENANCE_DIR/glog-build.stderr"
timeout 120 "${glog_install_argv[@]}" \
  >"$PROVENANCE_DIR/glog-install.stdout" \
  2>"$PROVENANCE_DIR/glog-install.stderr"

CMAKE_PREFIX_PATH_PREVIOUSLY_SET=false
CMAKE_PREFIX_PATH_PREVIOUS_VALUE=""
if [[ ${CMAKE_PREFIX_PATH+x} ]]; then
  CMAKE_PREFIX_PATH_PREVIOUSLY_SET=true
  CMAKE_PREFIX_PATH_PREVIOUS_VALUE=$CMAKE_PREFIX_PATH
fi
export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"
"$PY" -I -B - "$PROVENANCE_DIR/cmake-prefix-path.json" \
  "$CMAKE_PREFIX_PATH_PREVIOUSLY_SET" "$CMAKE_PREFIX_PATH_PREVIOUS_VALUE" \
  "$CMAKE_PREFIX_PATH" <<'PY'
import json
import sys

path, previously_set, previous_value, effective_value = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "previously_set": previously_set == "true",
            "previous_value": previous_value,
            "effective_value": effective_value,
            "overwritten": previously_set == "true",
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

driver_rc=0
"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/pegasus_floor_scoping.py" \
  --out-dir "$OUT_DIR" || driver_rc=$?
exit "$driver_rc"
