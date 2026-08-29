#!/usr/bin/env bash
# Reproduction body only; dispatch through the existing generic compute task:
# python3 tools/pegasus/dispatch_compute.py --task generic --walltime 02:00:00 \
#   --queue-wait-timeout 86400 -- \
#   /bin/bash output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh \
#   <JOB_TOKEN>

set -Eeuo pipefail
umask 077

REPO_ROOT=$(pwd -P)
POLICY_PATH="$REPO_ROOT/tools/pegasus/policy.json"
REFERENCE_ROOT=/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-balanced
DIAGNOSTIC_PARENT=/work/1/SFC/tanab/b10-backoff-requested-us-runs
FETCH_PROXY=http://10.120.96.1:8080
DISPATCH_WALLTIME=02:00:00
WALLTIME_SECONDS=7200
ALLOCATION_EVIDENCE_BUDGET_SECONDS=30
SOURCE_PREPARATION_BUDGET_SECONDS=120
DEPENDENCY_BUILD_BUDGET_SECONDS=540
PROVENANCE_BUDGET_SECONDS=60
CCBENCH_BUILD_BUDGET_SECONDS=1800
RECORD_BUDGET_SECONDS=300
SHUTDOWN_MARGIN_SECONDS=600
DRIVER_BUDGET_SECONDS=$((CCBENCH_BUILD_BUDGET_SECONDS + RECORD_BUDGET_SECONDS))
TOTAL_BUDGET_SECONDS=$((
  ALLOCATION_EVIDENCE_BUDGET_SECONDS
  + SOURCE_PREPARATION_BUDGET_SECONDS
  + DEPENDENCY_BUILD_BUDGET_SECONDS
  + PROVENANCE_BUDGET_SECONDS
  + DRIVER_BUDGET_SECONDS
  + SHUTDOWN_MARGIN_SECONDS
))

JOB_TOKEN=${1:?JOB_TOKEN argument is required}
JOB_TOKEN=${JOB_TOKEN//[^A-Za-z0-9._-]/_}
SCRATCH_USER_ROOT="/scr/${USER:?USER is required}"
JOB_ROOT="$SCRATCH_USER_ROOT/izanagi-backoff-requested-us-$JOB_TOKEN"
DEPENDENCY_PREFIX="$JOB_ROOT/dependency-prefix"
CCBENCH_CACHE_ROOT="$JOB_ROOT/ccbench-cache"
TMPDIR="$JOB_ROOT/tmp"
DIAGNOSTIC_ROOT="$DIAGNOSTIC_PARENT/backoff-requested-us-$JOB_TOKEN"
LOG_PARENT="$REPO_ROOT/output/insights/2026-08-28_t1941-backoff-requested-us/job-logs"
STAGING_LOG="$LOG_PARENT/.$JOB_TOKEN.staging"
PUBLISHED_LOG="$LOG_PARENT/$JOB_TOKEN"
CURRENT_STAGE=bootstrap
FAILURE_LINE=0
PUBLISH_READY=0
PUBLISHED=0
PYTHON_BIN=$(command -v python3.10 || command -v python3)
COMPUTE_HOSTNAME=$(hostname 2>/dev/null || printf UNKNOWN)
COMPUTE_SITE=UNKNOWN

write_job_status() {
  local status=$1
  local rc=$2
  local line=$3
  "$PYTHON_BIN" -I -B - "$STAGING_LOG/.job-status.tmp" \
    "$STAGING_LOG/job-status.json" "$status" "$rc" "$CURRENT_STAGE" \
    "$line" "$JOB_TOKEN" "$COMPUTE_HOSTNAME" "${COMPUTE_SITE:-UNKNOWN}" <<'PY'
import json
import os
import sys

(
    temporary,
    destination,
    status,
    rc,
    stage,
    line,
    job_token,
    compute_hostname,
    compute_site,
) = sys.argv[1:]
document = {
    "schema_version": "backoff-requested-us-job-status/v2",
    "job_token": job_token,
    "compute_hostname": compute_hostname,
    "compute_site": compute_site,
    "status": status,
    "returncode": int(rc),
    "stage": stage,
    "line": int(line),
}
with open(temporary, "x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, separators=(",", ":"))
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
os.replace(temporary, destination)
parent_fd = os.open(os.path.dirname(destination), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
try:
    os.fsync(parent_fd)
finally:
    os.close(parent_fd)
PY
}

publish_job_log() {
  local status=$1
  local rc=$2
  local line=$3
  write_job_status "$status" "$rc" "$line"
  mv -T "$STAGING_LOG" "$PUBLISHED_LOG"
  PUBLISHED=1
}

on_error() {
  local rc=$?
  FAILURE_LINE=${BASH_LINENO[0]:-0}
  return "$rc"
}

on_exit() {
  local rc=$?
  local publish_rc=0
  local status=failure
  trap - ERR EXIT
  set +e
  if [[ "$PUBLISH_READY" -eq 1 && "$PUBLISHED" -eq 0 ]]; then
    if [[ "$rc" -eq 0 ]]; then
      status=success
    fi
    publish_job_log "$status" "$rc" "$FAILURE_LINE" || publish_rc=$?
    if [[ "$publish_rc" -ne 0 ]]; then
      printf 'failed to publish job log: rc=%s staging=%s\n' \
        "$publish_rc" "$STAGING_LOG" >&2
      if [[ "$rc" -eq 0 ]]; then
        rc=$publish_rc
      fi
    fi
  fi
  exit "$rc"
}

trap on_error ERR
trap on_exit EXIT

mkdir -p "$LOG_PARENT"
test ! -e "$STAGING_LOG"
test ! -e "$PUBLISHED_LOG"
mkdir "$STAGING_LOG"
PUBLISH_READY=1

ALLOCATION_EVIDENCE_DEADLINE=$((SECONDS + ALLOCATION_EVIDENCE_BUDGET_SECONDS))
allocation_evidence_run() {
  local remaining=$((ALLOCATION_EVIDENCE_DEADLINE - SECONDS))
  test "$remaining" -gt 0
  timeout "$remaining" "$@"
}

CURRENT_STAGE=compute_site
COMPUTE_SITE=$(
  allocation_evidence_run "$PYTHON_BIN" -I -B - "$REPO_ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign import site_policy
site = site_policy.current_site(require_evidence=True)
print(site)
if site != site_policy.PEGASUS_COMPUTE:
    raise SystemExit(f"PEGASUS_COMPUTE is required, observed={site}")
PY
)
test "$COMPUTE_SITE" = PEGASUS_COMPUTE

CURRENT_STAGE=dispatch_budget
IFS=: read -r WALLTIME_HOURS WALLTIME_MINUTES WALLTIME_REMAINDER \
  <<<"$DISPATCH_WALLTIME"
test -n "$WALLTIME_HOURS"
test -n "$WALLTIME_MINUTES"
test -n "$WALLTIME_REMAINDER"
CALCULATED_WALLTIME_SECONDS=$((
  10#$WALLTIME_HOURS * 3600
  + 10#$WALLTIME_MINUTES * 60
  + 10#$WALLTIME_REMAINDER
))
test "$DISPATCH_WALLTIME" = 02:00:00
test "$WALLTIME_SECONDS" -eq 7200
test "$WALLTIME_SECONDS" -eq "$CALCULATED_WALLTIME_SECONDS"
test "$DEPENDENCY_BUILD_BUDGET_SECONDS" -gt 0
test "$SOURCE_PREPARATION_BUDGET_SECONDS" -gt 0
test "$PROVENANCE_BUDGET_SECONDS" -gt 0
test "$CCBENCH_BUILD_BUDGET_SECONDS" -gt 0
test "$RECORD_BUDGET_SECONDS" -gt 0
test "$SHUTDOWN_MARGIN_SECONDS" -gt 0
test "$DRIVER_BUDGET_SECONDS" -eq \
  "$((CCBENCH_BUILD_BUDGET_SECONDS + RECORD_BUDGET_SECONDS))"
test "$TOTAL_BUDGET_SECONDS" -lt "$WALLTIME_SECONDS"

CURRENT_STAGE=workspace_setup
mkdir -p "$SCRATCH_USER_ROOT" "$DIAGNOSTIC_PARENT"
test -d "$REFERENCE_ROOT"
test ! -e "$JOB_ROOT"
test ! -e "$DIAGNOSTIC_ROOT"
mkdir "$JOB_ROOT"
mkdir "$DEPENDENCY_PREFIX" "$CCBENCH_CACHE_ROOT" "$TMPDIR"
export TMPDIR

SOURCE_PREPARATION_DEADLINE=$((SECONDS + SOURCE_PREPARATION_BUDGET_SECONDS))
source_preparation_run() {
  local remaining=$((SOURCE_PREPARATION_DEADLINE - SECONDS))
  test "$remaining" -gt 0
  timeout "$remaining" "$@"
}

CURRENT_STAGE=dependency_policy
mapfile -t DEPENDENCY_CONFIG < <(source_preparation_run \
  "$PYTHON_BIN" -I -B - "$POLICY_PATH" <<'PY'
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
  observed=$(source_preparation_run git -C "$source" rev-parse HEAD)
  status=$(source_preparation_run \
    git -C "$source" status --porcelain --untracked-files=all)
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

CURRENT_STAGE=dependency_source_verification
GFLAGS_ACTUAL_HEAD=$(verify_pinned_clean_source gflags "$GFLAGS_SOURCE" "$GFLAGS_PIN")
GLOG_ACTUAL_HEAD=$(verify_pinned_clean_source glog "$GLOG_SOURCE" "$GLOG_PIN")

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
CC_PATH=$(source_preparation_run realpath "$CC_PATH")
CXX_PATH=$(source_preparation_run realpath "$CXX_PATH")
GFLAGS_BUILD="$JOB_ROOT/gflags-build"
GLOG_BUILD="$JOB_ROOT/glog-build"
mkdir "$GFLAGS_BUILD" "$GLOG_BUILD"

DEPENDENCY_BUILD_DEADLINE=$((SECONDS + DEPENDENCY_BUILD_BUDGET_SECONDS))
dependency_build_run() {
  local step_cap=$1
  shift
  local remaining=$((DEPENDENCY_BUILD_DEADLINE - SECONDS))
  test "$remaining" -gt 0
  if [[ "$remaining" -gt "$step_cap" ]]; then
    remaining=$step_cap
  fi
  timeout "$remaining" "$@"
}

CURRENT_STAGE=dependency_build
dependency_build_run 60 cmake -S "$GFLAGS_SOURCE" -B "$GFLAGS_BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$DEPENDENCY_PREFIX" \
  "-DCMAKE_C_COMPILER=$CC_PATH" \
  "-DCMAKE_CXX_COMPILER=$CXX_PATH" \
  >"$STAGING_LOG/gflags-configure.stdout" \
  2>"$STAGING_LOG/gflags-configure.stderr"
dependency_build_run 60 cmake --build "$GFLAGS_BUILD" -j 48 \
  >"$STAGING_LOG/gflags-build.stdout" \
  2>"$STAGING_LOG/gflags-build.stderr"
dependency_build_run 60 cmake --install "$GFLAGS_BUILD" \
  >"$STAGING_LOG/gflags-install.stdout" \
  2>"$STAGING_LOG/gflags-install.stderr"

dependency_build_run 120 cmake -S "$GLOG_SOURCE" -B "$GLOG_BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DWITH_GTEST=OFF \
  -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF \
  "-DCMAKE_PREFIX_PATH=$DEPENDENCY_PREFIX" \
  "-DCMAKE_INSTALL_PREFIX=$DEPENDENCY_PREFIX" \
  "-DCMAKE_C_COMPILER=$CC_PATH" \
  "-DCMAKE_CXX_COMPILER=$CXX_PATH" \
  >"$STAGING_LOG/glog-configure.stdout" \
  2>"$STAGING_LOG/glog-configure.stderr"
dependency_build_run 120 cmake --build "$GLOG_BUILD" -j 48 \
  >"$STAGING_LOG/glog-build.stdout" \
  2>"$STAGING_LOG/glog-build.stderr"
dependency_build_run 120 cmake --install "$GLOG_BUILD" \
  >"$STAGING_LOG/glog-install.stdout" \
  2>"$STAGING_LOG/glog-install.stderr"

CURRENT_STAGE=provenance
timeout "$PROVENANCE_BUDGET_SECONDS" "$PYTHON_BIN" -I -B - \
  "$STAGING_LOG/dependency-provenance.json" \
  "$GFLAGS_SOURCE" "$GFLAGS_ACTUAL_HEAD" "$GFLAGS_PIN" \
  "$GLOG_SOURCE" "$GLOG_ACTUAL_HEAD" "$GLOG_PIN" \
  "$DEPENDENCY_PREFIX" "$CCBENCH_CACHE_ROOT" "$DIAGNOSTIC_ROOT" \
  "$REFERENCE_ROOT" "$TOTAL_BUDGET_SECONDS" "$WALLTIME_SECONDS" \
  "$DISPATCH_WALLTIME" "$FETCH_PROXY" "$COMPUTE_HOSTNAME" "$COMPUTE_SITE" \
  "$ALLOCATION_EVIDENCE_BUDGET_SECONDS" \
  "$SOURCE_PREPARATION_BUDGET_SECONDS" \
  "$DEPENDENCY_BUILD_BUDGET_SECONDS" "$PROVENANCE_BUDGET_SECONDS" \
  "$CCBENCH_BUILD_BUDGET_SECONDS" "$RECORD_BUDGET_SECONDS" \
  "$SHUTDOWN_MARGIN_SECONDS" <<'PY'
import json
import sys

components = {
    "allocation_evidence": int(sys.argv[18]),
    "source_preparation": int(sys.argv[19]),
    "dependency_build": int(sys.argv[20]),
    "provenance": int(sys.argv[21]),
    "ccbench_build": int(sys.argv[22]),
    "record": int(sys.argv[23]),
    "shutdown_margin": int(sys.argv[24]),
}
if sum(components.values()) != int(sys.argv[12]):
    raise SystemExit("published component budgets do not sum to total")
if int(sys.argv[12]) >= int(sys.argv[13]):
    raise SystemExit("published total budget is not below dispatch walltime")
document = {
    "gflags_source": sys.argv[2],
    "gflags_pin": sys.argv[3],
    "gflags_expected_pin": sys.argv[4],
    "glog_source": sys.argv[5],
    "glog_pin": sys.argv[6],
    "glog_expected_pin": sys.argv[7],
    "dependency_prefix": sys.argv[8],
    "ccbench_cache_root": sys.argv[9],
    "diagnostic_root": sys.argv[10],
    "reference_root": sys.argv[11],
    "reference_root_mode": "read-only-input",
    "diagnostic_root_mode": "separate-create-only-output",
    "time_budget": {
        "total_budget_seconds": int(sys.argv[12]),
        "walltime_seconds": int(sys.argv[13]),
        "strictly_below_walltime": int(sys.argv[12]) < int(sys.argv[13]),
        "source": "generic-dispatch-argv",
        "dispatch_walltime": sys.argv[14],
        "parent_receipt_authority": "request-walltime-accounting",
        "components_seconds": components,
    },
    "execution_hostname": sys.argv[16],
    "execution_site": sys.argv[17],
    "build_time_network_fetch": True,
    "fetch_proxy": sys.argv[15],
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(document, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

export CMAKE_PREFIX_PATH="$DEPENDENCY_PREFIX"
export http_proxy="$FETCH_PROXY"
export https_proxy="$FETCH_PROXY"

CURRENT_STAGE=diagnostic_driver
timeout "$DRIVER_BUDGET_SECONDS" "$PYTHON_BIN" -I -B \
  orchestrator/campaign/backoff_requested_us.py \
  --reference-root "$REFERENCE_ROOT" \
  --diagnostic-root "$DIAGNOSTIC_ROOT" \
  --cache-root "$CCBENCH_CACHE_ROOT" \
  --build-timeout-seconds "$CCBENCH_BUILD_BUDGET_SECONDS" \
  --record-timeout-seconds "$RECORD_BUDGET_SECONDS" \
  >"$STAGING_LOG/diagnostic.stdout" \
  2>"$STAGING_LOG/diagnostic.stderr"

CURRENT_STAGE=complete
