#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:30:00
#PBS -b 1
#
# Compute-side Mocc trace pilot.  The workload tuple is parent-selected pilot
# data and is not a reproduction of historical T-816 measurements.
set -Eeuo pipefail
umask 077

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi
if [[ -z "${IZANAGI_SUBMISSION_NONCE:-}" ||
      ! "$IZANAGI_SUBMISSION_NONCE" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "IZANAGI_SUBMISSION_NONCE is missing or unsafe" >&2
  exit 2
fi
if [[ ! "${IZANAGI_MOCC_TRACE_MODE:-}" =~ ^[01]$ ]]; then
  echo "IZANAGI_MOCC_TRACE_MODE must be 0 or 1" >&2
  exit 2
fi

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
TOOLS="$REPO_ROOT/tools/pegasus"
POLICY="$TOOLS/mocc_trace_v1_policy.json"
ATTEMPTS_ROOT="$REPO_ROOT/output/env/pegasus/mocc-trace/attempts"
JOB_STAGING_ROOT="$REPO_ROOT/output/env/pegasus/mocc-trace/job-staging"
mkdir -p "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"
ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"
if ! mkdir "$ATTEMPT_DIR"; then
  echo "attempt already exists (create-only): $ATTEMPT_DIR" >&2
  exit 2
fi

failure_written=0
CCBENCH_BASE=""
BUILD_SOURCE=""
ATTEMPT_RECEIPT=""
CURRENT_COMMIT=""
CURRENT_SCRIPT_SHA=""
BINARY=""
BINARY_SHA=""
BUILD_DIR=""
TRACE_DIR=""
RUN_STDOUT=""
RUN_STDERR=""
RUN_ARGV_JSON=""
COMMIT_COUNT=""
RUN_ELAPSED_NS=""
CHECKER_RC="not-run"
VERIFIER_RC="not-run"
RUN_RC="not-run"
TRACE_MODE=$IZANAGI_MOCC_TRACE_MODE

write_failure() {
  local rc=$1
  local stage=$2
  local message=$3
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    python3 - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" "$message" <<'PY' || true
import json
import sys
import time

path, job_id, rc, stage, message = sys.argv[1:]
payload = {
    "schema_version": "mocc-trace-pilot-failure/v1",
    "pbs_jobid": job_id,
    "rc": int(rc),
    "stage": stage,
    "message": message,
    "recorded_epoch": int(time.time()),
}
try:
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
except FileExistsError:
    pass
PY
  fi
}

on_err() {
  local rc=$?
  local line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "shell" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR

on_signal() {
  local signal=$1
  trap - EXIT ERR INT TERM HUP
  write_failure 128 "signal" "received $signal"
  exit 128
}
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap 'on_signal HUP' HUP

cleanup_worktree() {
  local original_rc=$?
  trap - EXIT
  if [[ -n "$CCBENCH_BASE" && -n "$BUILD_SOURCE" ]]; then
    git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
      >>"$ATTEMPT_DIR/worktree-cleanup.stdout" \
      2>>"$ATTEMPT_DIR/worktree-cleanup.stderr" || true
  fi
  exit "$original_rc"
}
trap cleanup_worktree EXIT

if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  write_failure 2 policy "Mocc trace policy is missing or is a symlink"
  exit 2
fi

readarray -t policy_values < <(python3 - "$POLICY" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
trace = policy["mocc_trace"]
workload = trace["workload"]
if set(workload) != {
    "records", "threads", "zipf_skew", "ycsb_rratio", "ycsb_rmw", "extime_s"
}:
    raise SystemExit("mocc_trace.workload keys differ")
if trace["cmake_target"] != "ycsb_mocc.exe":
    raise SystemExit("mocc_trace cmake target differs")
for key, expected in (
    ("trace1_defines", {"CCBENCH_TRACE": "1"}),
    ("trace0_defines", {"CCBENCH_TRACE": "0"}),
):
    if trace[key] != expected:
        raise SystemExit(f"{key} differs")
for key in ("base_oid", "new_oid"):
    value = trace[key]
    if type(value) is not str or len(value) != 40 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise SystemExit(f"{key} is not a full lowercase OID")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(policy["pilot_walltime_s"])
print(policy["finalize_reserve_s"])
print(policy["expected_cpu_model"])
print(policy["expected_physical_cores"])
print(policy["gflags_source_path"])
print(policy["gflags_expected_head"])
print(policy["glog_source_path"])
print(policy["glog_expected_head"])
print(policy["third_party_cache_env"])
print(trace["base_oid"])
print(trace["new_oid"])
print(trace["cmake_target"])
print(json.dumps(workload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
PY
)
if [[ ${#policy_values[@]} -ne 16 ]]; then
  write_failure 2 policy "Mocc trace policy parse failed"
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
REQUESTED_S=${policy_values[3]}
FINALIZE_RESERVE_S=${policy_values[4]}
EXPECTED_CPU=${policy_values[5]}
EXPECTED_CORES=${policy_values[6]}
GFLAGS_SOURCE_PATH=${policy_values[7]}
GFLAGS_EXPECTED_HEAD=${policy_values[8]}
GLOG_SOURCE_PATH=${policy_values[9]}
GLOG_EXPECTED_HEAD=${policy_values[10]}
THIRD_PARTY_CACHE_ENV=${policy_values[11]}
BASE_OID=${policy_values[12]}
NEW_OID=${policy_values[13]}
CMAKE_TARGET=${policy_values[14]}
WORKLOAD_JSON=${policy_values[15]}

SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE"
SUBMIT_SOURCE="$SUBMISSION_DIR/submit-receipt.json"
for _ in $(seq 1 60); do
  [[ -f "$SUBMIT_SOURCE" ]] && break
  sleep 1
done
if [[ ! -f "$SUBMIT_SOURCE" ]]; then
  write_failure 2 submit_binding "submit receipt did not appear within 60 seconds"
  exit 2
fi
cp "$SUBMIT_SOURCE" "$ATTEMPT_DIR/submit-receipt.json"
ATTEMPT_RECEIPT="$ATTEMPT_DIR/submit-receipt.json"

CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)
if [[ ! "$CURRENT_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  write_failure 2 source_identity "outer source commit is not a full OID"
  exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all -- . ':(exclude)output')" ]]; then
  write_failure 2 source_identity "working tree became dirty before job start"
  exit 2
fi
CURRENT_SCRIPT_SHA=$(sha256sum "$TOOLS/mocc_trace_pilot.sh" | awk '{print $1}')
python3 - "$ATTEMPT_RECEIPT" "$CURRENT_COMMIT" "$CURRENT_SCRIPT_SHA" "$PBS_JOBID" \
  "$PROJECT" "$QUEUE" "$NODES" "$REQUESTED_S" "$BASE_OID" "$NEW_OID" \
  "$TRACE_MODE" "$WORKLOAD_JSON" <<'PY'
import json
import sys

(
    path, commit, script_sha, job_id, project, queue, nodes, requested_s,
    base_oid, new_oid, trace_mode, workload_json
) = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    receipt = json.load(handle)
qsub = receipt["qsub"]
mocc = receipt["mocc_trace"]

def normalized(value):
    value = str(value)
    return value[2:] if value.startswith("0:") else value

checks = {
    "dry_run": receipt.get("dry_run") is False,
    "source_commit": receipt.get("source_commit") == commit,
    "job_script_sha256": receipt.get("job_script_sha256") == script_sha,
    "request_id": normalized(qsub.get("request_id")) == normalized(job_id),
    "project": qsub.get("project") == project,
    "queue": qsub.get("queue") == queue,
    "nodes": qsub.get("nodes") == int(nodes),
    "walltime": qsub.get("elapstim_req_s") == int(requested_s),
    "base_oid": mocc.get("base_oid") == base_oid,
    "new_oid": mocc.get("new_oid") == new_oid,
    "trace_mode": mocc.get("trace_mode") == int(trace_mode),
    "workload": mocc.get("workload") == json.loads(workload_json),
}
if not all(checks.values()):
    raise SystemExit("submit binding mismatch: " + repr(checks))
PY

QSTAT_JOBID=${PBS_JOBID#0:}
qstat_rc=0
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-f.stdout" \
  2>"$ATTEMPT_DIR/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$ATTEMPT_DIR/qstat-f.rc"
HOSTNAME_SHORT=$(hostname)
HOSTNAME_FQDN=$(hostname -f 2>/dev/null || hostname)
printf '%s\n' "$HOSTNAME_SHORT" >"$ATTEMPT_DIR/hostname.stdout"
printf '%s\n' "$HOSTNAME_FQDN" >"$ATTEMPT_DIR/hostname-f.stdout"

readarray -t qstat_values < <(python3 - "$ATTEMPT_DIR/qstat-f.stdout" "$HOSTNAME_SHORT" "$qstat_rc" <<'PY'
import re
import subprocess
import sys

path, observed, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
if rc == "0":
    for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
        if match:
            raw = match.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    if assigned == "unavailable":
        match = re.search(
            r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
            text,
        )
        if match and match.group(1).lower() != "none":
            assigned = match.group(1)
    if assigned == "unavailable" and observed.split(".")[0] in text:
        assigned = observed.split(".")[0]
    for key in ("stime", "start_time", "start", "Started Request Time"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = raw
            break
        proc = subprocess.run(["date", "-d", raw, "+%s"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip().isdigit():
            started = proc.stdout.strip()
            break
print(assigned)
print(started)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable || "$SCHEDULER_STARTED_EPOCH" == unavailable ]]; then
  python3 - "$ATTEMPT_DIR/allocation-unavailable.json" "$PBS_JOBID" "$qstat_rc" \
    "$ASSIGNED_HOST" "$HOSTNAME_SHORT" "$SCHEDULER_STARTED_EPOCH" <<'PY'
import json
import sys
import time

path, job, rc, assigned, host, started = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-pilot-allocation/v1",
            "pbs_jobid": job,
            "qstat_rc": int(rc),
            "assigned_host_qstat": assigned,
            "hostname_observed": host,
            "scheduler_started_epoch": started,
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  write_failure 2 allocation "qstat allocation/start binding unavailable"
  exit 2
fi
if [[ "$ASSIGNED_HOST" != "$HOSTNAME_SHORT" &&
      "$ASSIGNED_HOST" != "$HOSTNAME_FQDN" ]]; then
  write_failure 2 allocation "qstat assigned host has no exact hostname observation"
  exit 2
fi

BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$HOSTNAME_SHORT"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$CURRENT_SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"

python3 - "$ATTEMPT_DIR/reservation.json" <<'PY'
import json
import os
import sys
import time

keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
payload = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key]
    for key in keys
}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    payload[key] = int(payload[key])
payload["recorded_epoch"] = int(time.time())
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

check_window() {
  local now remaining
  now=$(date +%s)
  remaining=$((DEADLINE_EPOCH - now - FINALIZE_RESERVE_S))
  printf '%s\n' "$remaining" >"$ATTEMPT_DIR/window-remaining-${1}.stdout"
  if [[ "$remaining" -le 0 ]]; then
    write_failure 2 reservation "no measured window remains before finalize reserve ($1)"
    exit 2
  fi
}
check_window before-build

python3 - "$ATTEMPT_DIR/topology.json" "$EXPECTED_CORES" <<'PY'
import json
import os
import pathlib
import sys

path, expected = sys.argv[1:]
visible = sorted(os.sched_getaffinity(0))
pairs = set()
for cpu in visible:
    root = pathlib.Path("/sys/devices/system/cpu") / f"cpu{cpu}" / "topology"
    try:
        package = int((root / "physical_package_id").read_text().strip())
        core = int((root / "core_id").read_text().strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot derive physical core topology: {exc}")
    pairs.add((package, core))
payload = {
    "affinity_cpus": visible,
    "cpuset_size": len(visible),
    "physical_visible": len(pairs),
    "ht_off": len(visible) == len(pairs),
    "expected_physical_cores": int(expected),
}
if len(pairs) != int(expected) or len(visible) != int(expected):
    raise SystemExit("cpuset/physical core count differs from policy")
with open(path, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

CPU_MODEL=$(awk -F: '/^model name[[:space:]]*:/ {gsub(/^[[:space:]]+/, "", $2); print $2; exit}' /proc/cpuinfo)
printf '%s\n' "$CPU_MODEL" >"$ATTEMPT_DIR/cpu-model.stdout"
if [[ "$CPU_MODEL" != "$EXPECTED_CPU" ]]; then
  write_failure 2 environment "CPU model differs from policy"
  exit 2
fi

module_rc=0
module -t list >"$ATTEMPT_DIR/module-list.stdout" 2>"$ATTEMPT_DIR/module-list.stderr" || module_rc=$?
printf '%s\n' "$module_rc" >"$ATTEMPT_DIR/module-list.rc"
if [[ "$module_rc" -ne 0 ]]; then
  write_failure "$module_rc" environment "module -t list failed"
  exit "$module_rc"
fi

CC_PATH=$(realpath "$(command -v gcc)")
CXX_PATH=$(realpath "$(command -v g++)")
CMAKE_PATH=$(realpath "$(command -v cmake)")
printf '%s\n' "$CC_PATH" >"$ATTEMPT_DIR/compiler-gcc.path"
printf '%s\n' "$CXX_PATH" >"$ATTEMPT_DIR/compiler-gxx.path"
printf '%s\n' "$CMAKE_PATH" >"$ATTEMPT_DIR/cmake.path"
"$CC_PATH" --version >"$ATTEMPT_DIR/compiler-gcc.version" 2>&1
"$CXX_PATH" --version >"$ATTEMPT_DIR/compiler-gxx.version" 2>&1
"$CMAKE_PATH" --version >"$ATTEMPT_DIR/cmake.version" 2>&1

if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  write_failure 2 gflags "gflags source path missing"
  exit 2
fi
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$ATTEMPT_DIR/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  write_failure 2 gflags "gflags source HEAD mismatch"
  exit 2
fi
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GFLAGS_STATUS" >"$ATTEMPT_DIR/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  write_failure 2 gflags "gflags working tree is dirty"
  exit 2
fi
GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
mkdir "$GFLAGS_BUILD_DIR"
gflags_configure_argv=(
  cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$CC_PATH"
  "-DCMAKE_CXX_COMPILER=$CXX_PATH"
)
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
python3 - "$ATTEMPT_DIR/gflags-configure.argv.json" "${gflags_configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
timeout 60 "${gflags_configure_argv[@]}" >"$ATTEMPT_DIR/gflags-configure.stdout" 2>"$ATTEMPT_DIR/gflags-configure.stderr"
timeout 60 "${gflags_build_argv[@]}" >"$ATTEMPT_DIR/gflags-build.stdout" 2>"$ATTEMPT_DIR/gflags-build.stderr"
timeout 60 "${gflags_install_argv[@]}" >"$ATTEMPT_DIR/gflags-install.stdout" 2>"$ATTEMPT_DIR/gflags-install.stderr"

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  write_failure 2 glog "glog source path missing"
  exit 2
fi
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$ATTEMPT_DIR/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  write_failure 2 glog "glog source HEAD mismatch"
  exit 2
fi
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GLOG_STATUS" >"$ATTEMPT_DIR/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  write_failure 2 glog "glog working tree is dirty"
  exit 2
fi
GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
mkdir "$GLOG_BUILD_DIR"
glog_configure_argv=(
  cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DWITH_GTEST=OFF
  -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF
  "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$CC_PATH"
  "-DCMAKE_CXX_COMPILER=$CXX_PATH"
)
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
python3 - "$ATTEMPT_DIR/glog-configure.argv.json" "${glog_configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
timeout 120 "${glog_configure_argv[@]}" >"$ATTEMPT_DIR/glog-configure.stdout" 2>"$ATTEMPT_DIR/glog-configure.stderr"
timeout 120 "${glog_build_argv[@]}" >"$ATTEMPT_DIR/glog-build.stdout" 2>"$ATTEMPT_DIR/glog-build.stderr"
timeout 120 "${glog_install_argv[@]}" >"$ATTEMPT_DIR/glog-install.stdout" 2>"$ATTEMPT_DIR/glog-install.stderr"

export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"
CACHE_ROOT=${!THIRD_PARTY_CACHE_ENV:-}
if [[ -z "$CACHE_ROOT" ]]; then
  write_failure 2 third_party "$THIRD_PARTY_CACHE_ENV is missing"
  exit 2
fi
python3 "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT" \
  --cache-root "$CACHE_ROOT" >"$ATTEMPT_DIR/third-party-hydrate.json" \
  2>"$ATTEMPT_DIR/third-party-hydrate.stderr"
THIRD_PARTY_SOURCE_ROOT=$(python3 - "$ATTEMPT_DIR/third-party-hydrate.json" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
value = payload.get("source_root")
if type(value) is not str or not os.path.isabs(value):
    raise SystemExit("hydrate output .source_root is not an absolute path")
print(value)
PY
)
if [[ ! -d "$THIRD_PARTY_SOURCE_ROOT" ]]; then
  write_failure 2 third_party "hydrate source_root is missing"
  exit 2
fi
printf '%s\n' "$THIRD_PARTY_SOURCE_ROOT" >"$ATTEMPT_DIR/third-party-source-root.stdout"

CCBENCH_BASE="$REPO_ROOT/external/ccbench"
if [[ ! -d "$CCBENCH_BASE" ]]; then
  write_failure 2 source_materialization "external/ccbench is missing"
  exit 2
fi
RESOLVED_NEW=$(git -C "$CCBENCH_BASE" rev-parse "$NEW_OID^{commit}")
if [[ "$RESOLVED_NEW" != "$NEW_OID" ]]; then
  write_failure 2 source_materialization "policy new_oid is absent from submodule"
  exit 2
fi
if ! git -C "$CCBENCH_BASE" merge-base --is-ancestor "$BASE_OID" "$NEW_OID"; then
  write_failure 2 source_materialization "policy base_oid is not an ancestor of new_oid"
  exit 2
fi
printf '%s\n' "$(git -C "$CCBENCH_BASE" rev-parse HEAD)" >"$ATTEMPT_DIR/submodule-head.stdout"
git -C "$CCBENCH_BASE" status --porcelain --untracked-files=all \
  >"$ATTEMPT_DIR/submodule-status.stdout"
if [[ -s "$ATTEMPT_DIR/submodule-status.stdout" ]]; then
  write_failure 2 source_materialization "submodule working tree is dirty"
  exit 2
fi
BUILD_SOURCE="$TMPDIR/ccbench-source"
git -C "$CCBENCH_BASE" worktree add --detach "$BUILD_SOURCE" "$NEW_OID" \
  >"$ATTEMPT_DIR/worktree-add.stdout" 2>"$ATTEMPT_DIR/worktree-add.stderr"

build_mode() {
  local mode=$1
  BUILD_DIR="$BUILD_SOURCE-build-trace$mode"
  mkdir "$BUILD_DIR"
  local -a configure_argv=(
    cmake -S "$BUILD_SOURCE" -B "$BUILD_DIR"
    -DCMAKE_BUILD_TYPE=Release
    -DENABLE_SANITIZER=OFF
    "-DCCBENCH_TRACE=$mode"
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
    "-DCMAKE_PREFIX_PATH=$CMAKE_PREFIX_PATH"
    "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$THIRD_PARTY_SOURCE_ROOT/masstree"
    "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$THIRD_PARTY_SOURCE_ROOT/mimalloc"
    "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$THIRD_PARTY_SOURCE_ROOT/googletest"
    "-DIZANAGI_GFLAGS_SRC_HEAD=$GFLAGS_SOURCE_HEAD"
    "-DIZANAGI_GLOG_SRC_HEAD=$GLOG_SOURCE_HEAD"
    "-DCMAKE_C_COMPILER=$CC_PATH"
    "-DCMAKE_CXX_COMPILER=$CXX_PATH"
    -DCMAKE_CXX_FLAGS=
  )
  local -a build_argv=(cmake --build "$BUILD_DIR" --target "$CMAKE_TARGET" -j 48)
  python3 - "$ATTEMPT_DIR/configure-trace$mode.argv.json" "${configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
  timeout 180 "${configure_argv[@]}" \
    >"$ATTEMPT_DIR/configure-trace$mode.stdout" \
    2>"$ATTEMPT_DIR/configure-trace$mode.stderr"
  timeout 600 "${build_argv[@]}" \
    >"$ATTEMPT_DIR/build-trace$mode.stdout" \
    2>"$ATTEMPT_DIR/build-trace$mode.stderr"
  BINARY="$BUILD_DIR/cc/mocc/$CMAKE_TARGET"
  if [[ ! -x "$BINARY" ]]; then
    write_failure 2 build "Mocc binary is missing after TRACE=$mode build"
    exit 2
  fi
  BINARY_SHA=$(sha256sum "$BINARY" | awk '{print $1}')
  printf '%s\n' "$BINARY_SHA" >"$ATTEMPT_DIR/binary-trace$mode.sha256"
  realpath "$BINARY" >"$ATTEMPT_DIR/binary-trace$mode.path"
  "$CXX_PATH" --version >"$ATTEMPT_DIR/compiler-used.version" 2>&1
}

if [[ "$TRACE_MODE" -eq 0 ]]; then
  # D297 checker is deliberately a hard gate.  Its nonzero result means that
  # TRACE=0 execution is skipped; no fallback or relaxed branch is permitted.
  build_mode 0
  CHECKER_RC=0
  python3 "$REPO_ROOT/tools/check_trace0_preprocess_identity.py" \
    --repo "$BUILD_SOURCE" --old "$BASE_OID" --new "$NEW_OID" \
    --cxx "$CXX_PATH" --expect-paths cc/mocc/transaction.cc \
    >"$ATTEMPT_DIR/trace0-preprocess-identity.json" \
    2>"$ATTEMPT_DIR/trace0-preprocess-identity.stderr" || CHECKER_RC=$?
  printf '%s\n' "$CHECKER_RC" >"$ATTEMPT_DIR/trace0-preprocess-identity.rc"
  if [[ "$CHECKER_RC" -ne 0 ]]; then
    python3 - "$ATTEMPT_DIR/trace0-execution.json" "$CHECKER_RC" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace0-execution/v1",
            "status": "skipped",
            "reason": "TRACE=0 preprocess identity checker failed closed",
            "checker_rc": int(sys.argv[2]),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
    write_failure "$CHECKER_RC" trace0_preprocess_identity \
      "TRACE=0 workload skipped because preprocess identity checker failed closed"
    exit "$CHECKER_RC"
  fi
else
  build_mode 1
fi

check_window before-workload

RUN_DIR="$ATTEMPT_DIR/run"
TRACE_DIR="$RUN_DIR/trace"
mkdir "$RUN_DIR"
mkdir "$TRACE_DIR"
RUN_STDOUT="$RUN_DIR/workload.stdout"
RUN_STDERR="$RUN_DIR/workload.stderr"
RUN_ARGV_JSON="$RUN_DIR/workload.argv.json"

# These are the exact gflags spellings observed in the existing probe.  The
# policy's semantic keys are intentionally not treated as CLI flag names.
RECORDS=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["records"])
PY
)
THREADS=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["threads"])
PY
)
ZIPF_SKEW=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["zipf_skew"])
PY
)
RRATIO=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["ycsb_rratio"])
PY
)
RMW=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["ycsb_rmw"])
PY
)
EXTIME=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["extime_s"])
PY
)
if [[ "$RMW" == 0 ]]; then
  RMW_FLAG=0
elif [[ "$RMW" == 1 ]]; then
  RMW_FLAG=true
else
  RMW_FLAG="$RMW"
fi
WORKLOAD_ARGV=(
  "-ycsb_tuple_num=$RECORDS"
  "-thread_num=$THREADS"
  "-ycsb_zipf_skew=$ZIPF_SKEW"
  "-ycsb_rratio=$RRATIO"
  "-ycsb_rmw=$RMW_FLAG"
  "-ycsb_max_ope=10"
  "-extime=$EXTIME"
)
python3 - "$RUN_ARGV_JSON" "$TRACE_MODE" "$WORKLOAD_JSON" "${WORKLOAD_ARGV[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "trace_mode": int(sys.argv[2]),
            "workload": json.loads(sys.argv[3]),
            "argv": sys.argv[4:],
            "argv_source": "t139_r4_env_probe.py gflags spelling",
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

RUN_START_NS=$(python3 - <<'PY'
import time
print(time.monotonic_ns())
PY
)
pushd "$TRACE_DIR" >/dev/null
set +e
timeout --foreground --signal=TERM --kill-after=30 120 "$BINARY" "${WORKLOAD_ARGV[@]}" \
  >"$RUN_STDOUT" 2>"$RUN_STDERR"
RUN_RC=$?
set -e
popd >/dev/null
RUN_END_NS=$(python3 - <<'PY'
import time
print(time.monotonic_ns())
PY
)
RUN_ELAPSED_NS=$((RUN_END_NS - RUN_START_NS))
printf '%s\n' "$RUN_RC" >"$RUN_DIR/workload.rc"
printf '%s\n' "$RUN_ELAPSED_NS" >"$RUN_DIR/workload.elapsed_ns"
if [[ "$RUN_RC" -ne 0 ]]; then
  write_failure "$RUN_RC" workload "Mocc workload returned nonzero"
  exit "$RUN_RC"
fi

counter_witness_rc=0
python3 - "$RUN_STDOUT" "$ATTEMPT_DIR/commit-count.json" <<'PY' || counter_witness_rc=$?
import json
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
patterns = (
    re.compile(r"(?im)^\s*#?\s*commit_counts?[_ ]*[:=]\s*(\d+)\s*$"),
    re.compile(r"(?im)^\s*#?\s*committed[_ ]+(?:transactions?|txns?|count)[_ ]*[:=]\s*(\d+)\s*$"),
)
matches = []
for pattern in patterns:
    matches.extend(pattern.finditer(text))
if len(matches) != 1:
    raise SystemExit(
        "expected exactly one commit counter witness line; "
        f"observed {len(matches)}"
    )
match = matches[0]
count = int(match.group(1))
if count < 0:
    raise SystemExit("commit counter must be non-negative")
with open(sys.argv[2], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-commit-counter-witness/v1",
            "count": count,
            "matched_line": match.group(0),
            "source": "CCBench stdout commit_counts_ witness",
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
if [[ "$counter_witness_rc" -ne 0 ]]; then
  write_failure "$counter_witness_rc" commit_counter \
    "CCBench stdout commit_counts_ witness was absent or ambiguous"
  exit "$counter_witness_rc"
fi
COMMIT_COUNT=$(python3 - "$ATTEMPT_DIR/commit-count.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    value = json.load(handle)["count"]
if type(value) is not int or value < 0:
    raise SystemExit("invalid commit count witness")
print(value)
PY
)

if [[ "$TRACE_MODE" -eq 1 ]]; then
  python3 - "$TRACE_DIR" "$ATTEMPT_DIR/trace-manifest.json" <<'PY'
import hashlib
import json
import pathlib
import sys

trace_dir = pathlib.Path(sys.argv[1])
paths = sorted(trace_dir.glob("trace_*.log"))
records = []
for path in paths:
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"trace artifact is not a regular file: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    records.append({"name": path.name, "sha256": digest, "size_bytes": path.stat().st_size})
with open(sys.argv[2], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-artifact-manifest/v1",
            "trace_dir": str(trace_dir),
            "files": records,
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  verifier_rc=0
  python3 -m orchestrator.verifier verify "$TRACE_DIR" --json \
    --expected-commits "$COMMIT_COUNT" \
    >"$ATTEMPT_DIR/verifier.json" 2>"$ATTEMPT_DIR/verifier.stderr" || verifier_rc=$?
  VERIFIER_RC=$verifier_rc
  printf '%s\n' "$VERIFIER_RC" >"$ATTEMPT_DIR/verifier.rc"
  if [[ "$VERIFIER_RC" -ne 0 ]]; then
    write_failure "$VERIFIER_RC" verifier \
      "TRACE=1 verifier did not certify the captured trace"
    exit "$VERIFIER_RC"
  fi
else
  python3 - "$ATTEMPT_DIR/throughput.json" "$COMMIT_COUNT" "$RUN_ELAPSED_NS" <<'PY'
import json
import sys

path, count, elapsed_ns = sys.argv[1:]
count_i = int(count)
elapsed_i = int(elapsed_ns)
if elapsed_i <= 0:
    raise SystemExit("workload elapsed time must be positive")
elapsed_s = elapsed_i / 1_000_000_000
throughput = count_i / elapsed_s
average_latency_s = elapsed_s / count_i if count_i else None
average_latency_us = average_latency_s * 1_000_000 if average_latency_s is not None else None
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-throughput/v1",
            "measurement_role": "pilot-only; not official calibration",
            "completed_txns": count_i,
            "elapsed_ns": elapsed_i,
            "elapsed_s": elapsed_s,
            "throughput_txns_per_s": throughput,
            "average_latency_s": average_latency_s,
            "average_latency_us": average_latency_us,
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
fi

# Recollect scheduler/accounting material after the run.  It is evidence, not a
# success shortcut: missing or malformed scheduler data remains visible in rc files.
qstat_final_rc=0
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-final.stdout" \
  2>"$ATTEMPT_DIR/qstat-final.stderr" || qstat_final_rc=$?
printf '%s\n' "$qstat_final_rc" >"$ATTEMPT_DIR/qstat-final.rc"
qstat_accounting_rc=0
timeout 30 qstat -x -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-accounting.stdout" \
  2>"$ATTEMPT_DIR/qstat-accounting.stderr" || qstat_accounting_rc=$?
printf '%s\n' "$qstat_accounting_rc" >"$ATTEMPT_DIR/qstat-accounting.rc"

python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" "$ATTEMPT_RECEIPT" \
  "$ATTEMPT_DIR/topology.json" "$CURRENT_COMMIT" "$CURRENT_SCRIPT_SHA" \
  "$PBS_JOBID" "$HOSTNAME_SHORT" "$HOSTNAME_FQDN" "$CPU_MODEL" "$TRACE_MODE" \
  "$CXX_PATH" \
  "$BASE_OID" "$NEW_OID" "$BUILD_DIR" "$BINARY" "$BINARY_SHA" "$RUN_DIR" \
  "$TRACE_DIR" "$RUN_ARGV_JSON" "$COMMIT_COUNT" "$RUN_ELAPSED_NS" \
  "$CHECKER_RC" "$VERIFIER_RC" "$RUN_RC" "$qstat_final_rc" \
  "$qstat_accounting_rc" "$WORKLOAD_JSON" "$CMAKE_TARGET" <<'PY'
import json
import os
import sys
import time

(
    output, submit_receipt_path, topology_path, outer_commit, script_sha,
    job_id, host, host_fqdn, cpu_model, trace_mode, cxx_path, base_oid, new_oid,
    build_dir, binary, binary_sha, run_dir, trace_dir, run_argv_path,
    commit_count, elapsed_ns, checker_rc, verifier_rc, run_rc,
    qstat_final_rc, qstat_accounting_rc, workload_json, cmake_target,
) = sys.argv[1:]
with open(submit_receipt_path, encoding="utf-8") as handle:
    submit_receipt = json.load(handle)
with open(topology_path, encoding="utf-8") as handle:
    topology = json.load(handle)
with open(run_argv_path, encoding="utf-8") as handle:
    run_argv = json.load(handle)
mocc_trace = dict(submit_receipt["mocc_trace"])
mocc_trace["trace_mode"] = int(trace_mode)
mocc_trace["base_oid"] = base_oid
mocc_trace["new_oid"] = new_oid
mocc_trace["cmake_target"] = cmake_target
mocc_trace["workload"] = json.loads(workload_json)
mocc_trace["workload_note"] = (
    "parent-selected pilot workload; not a reproduction of historical T-816 measurements"
)
payload = {
    "schema_version": "mocc-trace-pilot-receipt/v1",
    "status": "completed",
    "pilot": True,
    "eligible_for_refreeze": False,
    "official_certification": False,
    "created_epoch": int(time.time()),
    "pbs": {
        "jobid": job_id,
        "queue": os.environ.get("PBS_QUEUE", "gen_S"),
        "account": os.environ.get("PBS_ACCOUNT", "SFC"),
        "requested_s": int(os.environ.get("IZANAGI_RESERVATION_REQUESTED_S", "0")),
        "hostname": host,
        "hostname_fqdn": host_fqdn,
        "qstat_final_rc": int(qstat_final_rc),
        "qstat_accounting_rc": int(qstat_accounting_rc),
        "scheduler_material": {
            "qstat_final": "qstat-final.stdout/stderr/rc",
            "qstat_accounting": "qstat-accounting.stdout/stderr/rc",
        },
    },
    "environment": {
        "environment_tag": "pegasus",
        "cpu_model": cpu_model,
        "expected_cpu_model": submit_receipt["policy"]["expected_cpu_model"],
        "topology": topology,
        "compiler": {
            "path": cxx_path,
            "version": open(os.path.join(os.path.dirname(output), "compiler-used.version"), encoding="utf-8").read().strip(),
        },
    },
    "source": {
        "outer_repo_commit": outer_commit,
        "submodule_base_oid": base_oid,
        "submodule_new_oid": new_oid,
        "materialization": "git worktree add --detach in qsub job body",
        "outer_gitlink_advanced": False,
    },
    "mocc_trace": mocc_trace,
    "build": {
        "cmake_target": cmake_target,
        "trace_mode": int(trace_mode),
        "build_dir": build_dir,
        "binary": binary,
        "binary_sha256": binary_sha,
        "compiler_path": cxx_path,
    },
    "workload": {
        "config": json.loads(workload_json),
        "argv": run_argv["argv"],
        "argv_source": run_argv["argv_source"],
        "completed_txns": int(commit_count),
        "elapsed_ns": int(elapsed_ns),
        "elapsed_s": int(elapsed_ns) / 1_000_000_000,
    },
    "artifacts": {
        "attempt_dir": os.path.dirname(output),
        "run_dir": run_dir,
        "trace_dir": trace_dir,
        "submit_receipt": "submit-receipt.json",
        "verifier_json": "verifier.json" if int(trace_mode) == 1 else None,
        "throughput_json": "throughput.json" if int(trace_mode) == 0 else None,
    },
    "gates": {
        "trace0_preprocess_identity_rc": checker_rc,
        "verifier_rc": verifier_rc,
        "workload_rc": run_rc,
    },
}
with open(output, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY

RECEIPT_SHA=$(sha256sum "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" | awk '{print $1}')
python3 - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$RECEIPT_SHA" \
  "$BINARY_SHA" "$CURRENT_SCRIPT_SHA" <<'PY'
import json
import sys
import time

path, job_id, receipt_sha, binary_sha, script_sha = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-pilot-job-result/v1",
            "pbs_jobid": job_id,
            "receipt_sha256": receipt_sha,
            "binary_sha256": binary_sha,
            "job_script_sha256": script_sha,
            "completed_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
  >"$ATTEMPT_DIR/worktree-remove.stdout" \
  2>"$ATTEMPT_DIR/worktree-remove.stderr"
BUILD_SOURCE=""
exit 0
