#!/usr/bin/env bash
# Reproduction body only; this file is not a registered execution entrypoint.
# Submit it with an explicit job token as the first job-body argument:
# python3 tools/pegasus/dispatch_compute.py --task generic --walltime 05:00:00 \
#   /bin/bash output/insights/2026-08-26_b10-balanced-profile/job-body.sh <JOB_TOKEN>
# The generic queue-wait limit remains a separate 900 seconds; it is not walltime.

set -euo pipefail

REPO_ROOT=$(pwd -P)
POLICY_PATH="$REPO_ROOT/tools/pegasus/policy.json"
DISPATCH_WALLTIME=05:00:00
WALLTIME_SECONDS=18000
DEPENDENCY_BUILD_BUDGET_SECONDS=540
CCBENCH_BUILD_BUDGET_SECONDS=$((7 * 900))
RECORD_BUDGET_SECONDS=$((7 * 3 * 180))
REPORT_BUDGET_SECONDS=$((7 * 3 * 180))
SHUTDOWN_MARGIN_SECONDS=600
INNER_BUDGET_SECONDS=$((
  DEPENDENCY_BUILD_BUDGET_SECONDS
  + CCBENCH_BUILD_BUDGET_SECONDS
  + RECORD_BUDGET_SECONDS
  + REPORT_BUDGET_SECONDS
))
TOTAL_BUDGET_SECONDS=$((INNER_BUDGET_SECONDS + SHUTDOWN_MARGIN_SECONDS))
test "$TOTAL_BUDGET_SECONDS" -lt "$WALLTIME_SECONDS"

JOB_TOKEN=${1:?JOB_TOKEN argument is required for the job-specific build roots}
JOB_TOKEN=${JOB_TOKEN//[^A-Za-z0-9._-]/_}
SCRATCH_USER_ROOT="/scr/${USER:?USER is required}"
JOB_ROOT="$SCRATCH_USER_ROOT/izanagi-b10-balanced-profile-$JOB_TOKEN"
DEPENDENCY_PREFIX="$JOB_ROOT/dependency-prefix"
CCBENCH_CACHE_ROOT="$JOB_ROOT/ccbench-cache"
TMPDIR="$JOB_ROOT/tmp"
DEPENDENCY_LOG_PARENT="$REPO_ROOT/output/insights/2026-08-26_b10-balanced-profile/job-logs"
DEPENDENCY_BUILD_LOG="$DEPENDENCY_LOG_PARENT/.$JOB_TOKEN.staging"
DEPENDENCY_PUBLISH_LOG="$DEPENDENCY_LOG_PARENT/$JOB_TOKEN"

mkdir -p "$SCRATCH_USER_ROOT" "$DEPENDENCY_LOG_PARENT"
test ! -e "$JOB_ROOT"
test ! -e "$DEPENDENCY_BUILD_LOG"
test ! -e "$DEPENDENCY_PUBLISH_LOG"
mkdir "$JOB_ROOT"
mkdir "$DEPENDENCY_PREFIX" "$CCBENCH_CACHE_ROOT" "$TMPDIR"
mkdir "$DEPENDENCY_BUILD_LOG"
export TMPDIR

mapfile -t DEPENDENCY_CONFIG < <(python3 - "$POLICY_PATH" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
for key in (
    "gflags_source_path",
    "gflags_expected_head",
    "glog_source_path",
    "glog_expected_head",
):
    value = policy[key]
    if not isinstance(value, str) or not value:
        raise SystemExit(f"invalid policy field: {key}")
    print(value)
PY
)

GFLAGS_SOURCE=${DEPENDENCY_CONFIG[0]}
GFLAGS_PIN=${DEPENDENCY_CONFIG[1]}
GLOG_SOURCE=${DEPENDENCY_CONFIG[2]}
GLOG_PIN=${DEPENDENCY_CONFIG[3]}

verify_pinned_clean_source() {
  local name=$1
  local source=$2
  local expected=$3
  local observed
  local status
  observed=$(git -C "$source" rev-parse HEAD)
  status=$(git -C "$source" status --porcelain --untracked-files=all)
  if [[ "$observed" != "$expected" ]]; then
    printf '%s source HEAD mismatch: expected=%s observed=%s\n' \
      "$name" "$expected" "$observed" >&2
    return 2
  fi
  if [[ -n "$status" ]]; then
    printf '%s source is dirty\n' "$name" >&2
    return 2
  fi
  printf '%s\n' "$observed"
}

GFLAGS_ACTUAL_HEAD=$(verify_pinned_clean_source gflags "$GFLAGS_SOURCE" "$GFLAGS_PIN")
GLOG_ACTUAL_HEAD=$(verify_pinned_clean_source glog "$GLOG_SOURCE" "$GLOG_PIN")

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
GFLAGS_BUILD="$JOB_ROOT/gflags-build"
GLOG_BUILD="$JOB_ROOT/glog-build"
mkdir "$GFLAGS_BUILD" "$GLOG_BUILD"

timeout 60 cmake -S "$GFLAGS_SOURCE" -B "$GFLAGS_BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$DEPENDENCY_PREFIX" \
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" \
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")" \
  >"$DEPENDENCY_BUILD_LOG/gflags-configure.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/gflags-configure.stderr"
timeout 60 cmake --build "$GFLAGS_BUILD" -j 48 \
  >"$DEPENDENCY_BUILD_LOG/gflags-build.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/gflags-build.stderr"
timeout 60 cmake --install "$GFLAGS_BUILD" \
  >"$DEPENDENCY_BUILD_LOG/gflags-install.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/gflags-install.stderr"

timeout 120 cmake -S "$GLOG_SOURCE" -B "$GLOG_BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DWITH_GTEST=OFF \
  -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF \
  "-DCMAKE_PREFIX_PATH=$DEPENDENCY_PREFIX" \
  "-DCMAKE_INSTALL_PREFIX=$DEPENDENCY_PREFIX" \
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" \
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")" \
  >"$DEPENDENCY_BUILD_LOG/glog-configure.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/glog-configure.stderr"
timeout 120 cmake --build "$GLOG_BUILD" -j 48 \
  >"$DEPENDENCY_BUILD_LOG/glog-build.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/glog-build.stderr"
timeout 120 cmake --install "$GLOG_BUILD" \
  >"$DEPENDENCY_BUILD_LOG/glog-install.stdout" \
  2>"$DEPENDENCY_BUILD_LOG/glog-install.stderr"

python3 - "$DEPENDENCY_BUILD_LOG/dependency-provenance.json" \
  "$GFLAGS_SOURCE" "$GFLAGS_ACTUAL_HEAD" "$GFLAGS_PIN" \
  "$GLOG_SOURCE" "$GLOG_ACTUAL_HEAD" "$GLOG_PIN" \
  "$DEPENDENCY_PREFIX" "$CCBENCH_CACHE_ROOT" "$DEPENDENCY_PUBLISH_LOG" \
  "$DISPATCH_WALLTIME" "$WALLTIME_SECONDS" \
  "$DEPENDENCY_BUILD_BUDGET_SECONDS" "$CCBENCH_BUILD_BUDGET_SECONDS" \
  "$RECORD_BUDGET_SECONDS" "$REPORT_BUDGET_SECONDS" \
  "$INNER_BUDGET_SECONDS" "$SHUTDOWN_MARGIN_SECONDS" \
  "$TOTAL_BUDGET_SECONDS" <<'PY'
import json
import sys

document = {
    "gflags_source": sys.argv[2],
    "gflags_pin": sys.argv[3],
    "gflags_expected_pin": sys.argv[4],
    "glog_source": sys.argv[5],
    "glog_pin": sys.argv[6],
    "glog_expected_pin": sys.argv[7],
    "dependency_prefix": sys.argv[8],
    "ccbench_cache_root": sys.argv[9],
    "dependency_build_log": sys.argv[10],
    "time_budget": {
        "dispatch_walltime": sys.argv[11],
        "walltime_seconds": int(sys.argv[12]),
        "dependency_build_budget_seconds": int(sys.argv[13]),
        "ccbench_build_budget_seconds": int(sys.argv[14]),
        "record_budget_seconds": int(sys.argv[15]),
        "report_budget_seconds": int(sys.argv[16]),
        "inner_budget_seconds": int(sys.argv[17]),
        "shutdown_margin_seconds": int(sys.argv[18]),
        "total_budget_seconds": int(sys.argv[19]),
        "strictly_below_walltime": int(sys.argv[19]) < int(sys.argv[12]),
    },
    "dependency_prefix_cache_identity_bound": False,
    "limitation": (
        "legacy buildcache.build does not bind the dependency prefix into its cache identity; "
        "this job-specific cache root prevents inheritance of an older cache"
    ),
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(document, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

export CMAKE_PREFIX_PATH="$DEPENDENCY_PREFIX"
export IZANAGI_BACKOFF_PROFILE_CACHE_ROOT="$CCBENCH_CACHE_ROOT"
export IZANAGI_BACKOFF_PROFILE_DEPENDENCY_LOG="$DEPENDENCY_BUILD_LOG"
export IZANAGI_BACKOFF_PROFILE_DEPENDENCY_PUBLISH_LOG="$DEPENDENCY_PUBLISH_LOG"

python3.10 orchestrator/campaign/backoff_profile.py balanced \
  > >(tee "$DEPENDENCY_BUILD_LOG/profile.stdout") \
  2> >(tee "$DEPENDENCY_BUILD_LOG/profile.stderr" >&2)

mv -T "$DEPENDENCY_BUILD_LOG" "$DEPENDENCY_PUBLISH_LOG"
