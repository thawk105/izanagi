#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=05:00:00
#PBS -b 1

set -Eeuo pipefail
umask 077

# 31/24 scaling plus detached worktree and dependency build:
# 120 + 180 + 11700 + 3900 + 300 + 120 + 300 = 16620 seconds.
# A five-hour reservation therefore retains the preregistered 1380-second reserve.
WORKTREE_SETUP_CAP_S=120
DEPENDENCY_BUILD_CAP_S=180
SWEEP_CAP_S=11700
AA_CAP_S=3900
REPORT_CAP_S=300
WORKTREE_CLEANUP_CAP_S=120
FINALIZE_CAP_S=300
EXPECTED_WALLTIME_S=18000
EXPECTED_RESERVE_S=1380
EXPECTED_FREEZE_TREES_SHA256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3
BUILD_NETWORK_PROXY_URL=http://10.120.96.1:8080
CURRENT_STAGE=bootstrap
PY=""
OUTPUT_ROOT=""
OUTPUT_ROOT_READY=0
CCBENCH_BASE=""
CCBENCH_WORKTREE=""
B10_RUN_KIND=${B10_RUN_KIND:-extended}

write_failure_receipt() {
  local rc=$1
  local line=$2
  [[ -n "$PY" && -n "$OUTPUT_ROOT" && "$OUTPUT_ROOT_READY" -eq 1 ]] || return 0
  "$PY" -I -B - "$OUTPUT_ROOT" "$rc" "$CURRENT_STAGE" "$line" \
    "${PBS_JOBID:-}" "$B10_RUN_KIND" <<'PY' || true
import hashlib, json, os, pathlib, sys
root, rc, stage, line, job, run_kind = sys.argv[1:]
path = pathlib.Path(root + ".failure.json")
base = pathlib.Path(root)
wal_receipts = []
last_committed = None
for candidate in sorted(base.glob("campaigns/*/runs/wal.jsonl")):
    raw = candidate.read_bytes()
    committed = None
    for row in raw.splitlines():
        if not row:
            continue
        try:
            parsed = json.loads(row)
        except json.JSONDecodeError:
            continue
        if parsed.get("stage") == "commit":
            committed = {
                "variant": parsed.get("variant"),
                "build_attempt_id": parsed.get("payload", {}).get("build_attempt_id"),
                "timestamp": parsed.get("ts"),
            }
    receipt = {
        "path": candidate.relative_to(base).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "last_committed": committed,
    }
    wal_receipts.append(receipt)
    if committed is not None:
        last_committed = {**committed, "wal_path": receipt["path"],
                          "wal_sha256": receipt["sha256"]}
aa_receipts = []
last_aa = None
for candidate in sorted(base.glob("campaigns/*/reports/b10-backoff-overthrottle-*.jsonl")):
    raw = candidate.read_bytes()
    rows = [row for row in raw.splitlines() if row]
    parsed = None
    for row in reversed(rows):
        try:
            parsed = json.loads(row)
        except json.JSONDecodeError:
            continue
        break
    receipt = {
        "path": candidate.relative_to(base).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "last_record": None if parsed is None else {
            "workload": parsed.get("workload"),
            "label": parsed.get("label"),
            "rep": parsed.get("rep"),
            "reference_variant_id": parsed.get("reference_variant_id"),
        },
    }
    aa_receipts.append(receipt)
    if receipt["last_record"] is not None:
        last_aa = {**receipt["last_record"], "path": receipt["path"],
                   "sha256": receipt["sha256"]}
report_receipts = []
for candidate in sorted(base.glob("campaigns/*/reports/*")):
    if not candidate.is_file() or candidate.name.endswith(".jsonl"):
        continue
    raw = candidate.read_bytes()
    report_receipts.append({
        "path": candidate.relative_to(base).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    })
top_level_receipts = []
for candidate in sorted(base.glob("b10-backoff-grid-*.json")):
    if candidate.is_file():
        raw = candidate.read_bytes()
        top_level_receipts.append({
            "path": candidate.relative_to(base).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
        })
document = {
    "schema_version": "b10-backoff-grid-job-failure/v1",
    "run_kind": run_kind,
    "returncode": int(rc),
    "stage": stage,
    "line": int(line),
    "pbs_jobid": job,
    "last_persisted": {"wal_commit": last_committed, "aa_record": last_aa},
    "campaign_wals": wal_receipts,
    "aa_jsonl": aa_receipts,
    "reports": report_receipts,
    "typed_receipts": top_level_receipts,
}
try:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
except FileExistsError:
    pass
PY
}

fail() {
  local rc=$1
  local message=$2
  local line=${BASH_LINENO[0]:-0}
  echo "$message" >&2
  trap - ERR
  write_failure_receipt "$rc" "$line"
  exit "$rc"
}

on_error() {
  local rc=$?
  local line=${BASH_LINENO[0]:-0}
  trap - ERR
  write_failure_receipt "$rc" "$line"
  exit "$rc"
}
trap on_error ERR

remove_ccbench_worktree() {
  local cleanup_rc=0
  [[ -n "$CCBENCH_BASE" && -n "$CCBENCH_WORKTREE" ]] || return 0
  timeout "$WORKTREE_CLEANUP_CAP_S" \
    git -C "$CCBENCH_BASE" worktree remove --force "$CCBENCH_WORKTREE" \
    >>"$OUTPUT_ROOT/env/worktree-remove.stdout" \
    2>>"$OUTPUT_ROOT/env/worktree-remove.stderr" || cleanup_rc=$?
  printf '%s\n' "$cleanup_rc" >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
  [[ "$cleanup_rc" -eq 0 ]] || return "$cleanup_rc"
  CCBENCH_WORKTREE=""
}

cleanup_worktree() {
  local original_rc=$?
  local cleanup_rc=0
  trap - EXIT ERR
  remove_ccbench_worktree || cleanup_rc=$?
  if [[ "$original_rc" -eq 0 && "$cleanup_rc" -ne 0 ]]; then
    original_rc=$cleanup_rc
  fi
  exit "$original_rc"
}
trap cleanup_worktree EXIT

case "$B10_RUN_KIND" in
  extended|t2266-tail|t2418-explore|t2500-tail-formal) ;;
  *) fail 2 "B10_RUN_KIND must be extended, t2266-tail, t2418-explore, or t2500-tail-formal" ;;
esac

[[ -n "${PBS_JOBID:-}" && -n "${PBS_NODEFILE:-}" \
  && -n "${PBS_O_WORKDIR:-}" && -n "${B10_SUBMISSION_NONCE:-}" \
  && -n "${JOB_SCRIPT_SHA256:-}" ]] || \
  fail 2 "PBS_JOBID, PBS_NODEFILE, PBS_O_WORKDIR, B10_SUBMISSION_NONCE, and JOB_SCRIPT_SHA256 are required"
[[ "$B10_SUBMISSION_NONCE" =~ ^[0-9a-f]{32}$ ]] || \
  fail 2 "B10_SUBMISSION_NONCE must be 32 lowercase hex characters"
[[ "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]] || \
  fail 2 "JOB_SCRIPT_SHA256 must be 64 lowercase hex characters"

WORKLOAD=${1:-${B10_WORKLOAD:-}}
case "$WORKLOAD" in
  write-heavy|balanced|read-heavy) ;;
  *) fail 2 "workload must be write-heavy, balanced, or read-heavy" ;;
esac

export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" && -x "$resolved" ]] || continue
  if "$resolved" -I -B -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 10))'; then
    PY=$("$resolved" -I -B -c 'import os,sys; print(os.path.realpath(sys.executable))')
    break
  fi
done
[[ -n "$PY" ]] || fail 2 "Python 3.10 is required"

export http_proxy="$BUILD_NETWORK_PROXY_URL"
export https_proxy="$BUILD_NETWORK_PROXY_URL"
# This gate runs in the PBS payload on the allocated compute node.
for command_name in \
  git cmake cc c++ make ar ranlib as ld numactl timeout qstat sha256sum \
  hostname mkdir realpath tr date env; do
  command -v -- "$command_name" >/dev/null 2>&1 || \
    fail 2 "required command is unavailable: $command_name"
done

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LD_PRELOAD LD_LIBRARY_PATH
unset CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH COMPILER_PATH GCC_EXEC_PREFIX
unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE
unset CMAKE_PROJECT_INCLUDE CMAKE_PROJECT_INCLUDE_BEFORE
unset CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_C_COMPILER_LAUNCHER
unset CMAKE_CXX_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS
while IFS='=' read -r env_name _; do
  case "$env_name" in
    GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*) unset "$env_name" ;;
  esac
done < <(env)

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
  [[ "${B10_PREREGISTRATION_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || \
    fail 2 "B10_PREREGISTRATION_COMMIT must be 40 lowercase hex characters"
  [[ "${B10_EXPLORE_CAMPAIGN:-}" == /* \
      && -d "$B10_EXPLORE_CAMPAIGN" && ! -L "$B10_EXPLORE_CAMPAIGN" ]] || \
    fail 2 "B10_EXPLORE_CAMPAIGN must be an absolute, existing, non-symlink directory"
  "$PY" -I -B - "$REPO_ROOT" "$B10_EXPLORE_CAMPAIGN" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=True)
if target == repo or repo in target.parents or target in repo.parents:
    print("explore campaign must be outside the repository", file=sys.stderr)
    raise SystemExit(2)
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    print("explore campaign has a repository ancestor", file=sys.stderr)
    raise SystemExit(2)
PY
fi
OUTPUT_ROOT=${B10_OUTPUT_ROOT:-}
[[ -n "$OUTPUT_ROOT" && "$OUTPUT_ROOT" == /* && ! -e "$OUTPUT_ROOT" ]] || \
  fail 2 "B10_OUTPUT_ROOT must be an absolute, job-unique, uncreated path"
"$PY" -I -B - "$REPO_ROOT" "$OUTPUT_ROOT" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=False)
if target == repo or repo in target.parents or target in repo.parents:
    raise SystemExit("official output root must be outside the repository")
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    raise SystemExit("official output root has a repository ancestor")
PY

HOSTNAME_SHORT=$(hostname) || fail 2 "cannot observe compute hostname"
HOSTNAME_FQDN=$(hostname -f) || fail 2 "cannot observe compute hostname -f"
[[ "$HOSTNAME_SHORT" =~ ^bnode[0-9]+([.].*)?$ ]] || \
  fail 2 "B-10 job body is compute-node-only"
[[ -f "$PBS_NODEFILE" && ! -L "$PBS_NODEFILE" ]] || \
  fail 2 "PBS_NODEFILE must be a regular non-symlink file"

export TMPDIR="/scr/${PBS_JOBID//:/_}-b10-backoff-grid-${WORKLOAD}"
mkdir -m 0700 "$TMPDIR"
export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
export B10_BUILD_CACHE_ROOT="$TMPDIR/build-cache"
mkdir -m 0700 "$B10_BUILD_CACHE_ROOT"
mkdir -m 0700 "$OUTPUT_ROOT"
OUTPUT_ROOT_READY=1
mkdir -m 0700 "$OUTPUT_ROOT/campaigns" "$OUTPUT_ROOT/campaign-locks" "$OUTPUT_ROOT/env"

CURRENT_STAGE=allocation_reservation
qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$OUTPUT_ROOT/qstat-f.stdout" \
  2>"$OUTPUT_ROOT/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$OUTPUT_ROOT/qstat-f.rc"
readarray -t qstat_values < <(
  "$PY" -I -B - "$OUTPUT_ROOT/qstat-f.stdout" "$qstat_rc" <<'PY'
import re
import subprocess
import sys

path, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
limit_s = "unavailable"
if rc == "0":
    section = re.search(
        r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
        text,
    )
    if section and section.group(1).lower() != "none":
        assigned = section.group(1)
    if assigned == "unavailable":
        for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
            match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
            if not match:
                continue
            raw = match.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    for key in ("Started Request Time", "stime", "start_time", "start"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = str(int(raw))
            break
        parsed = subprocess.run(
            ["date", "-d", raw, "+%s"], capture_output=True, text=True,
        )
        if parsed.returncode == 0 and parsed.stdout.strip().isdigit():
            started = str(int(parsed.stdout.strip()))
            break
    limits = re.findall(
        r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)",
        text,
    )
    if len(limits) == 1 and int(limits[0]) > 0:
        limit_s = str(int(limits[0]))
print(assigned)
print(started)
print(limit_s)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
REQUESTED_S=${qstat_values[2]:-unavailable}
[[ "$qstat_rc" -eq 0 && "$ASSIGNED_HOST" != unavailable \
  && "$SCHEDULER_STARTED_EPOCH" != unavailable && "$REQUESTED_S" != unavailable ]] || \
  fail 2 "qstat allocation, start, or walltime binding is unavailable"
[[ "$REQUESTED_S" -eq "$EXPECTED_WALLTIME_S" ]] || \
  fail 2 "qstat walltime differs from the B-10 PBS envelope"
if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]; then
  RESERVATION_HOST=$HOSTNAME_SHORT
elif [[ "$ASSIGNED_HOST" == "$HOSTNAME_FQDN" ]]; then
  RESERVATION_HOST=$HOSTNAME_FQDN
else
  fail 2 "qstat assigned host has no exact hostname or hostname-f observation"
fi
"$PY" -I -B - "$PBS_NODEFILE" "$HOSTNAME_SHORT" <<'PY'
import pathlib, sys
nodefile, observed = sys.argv[1:]
entries = [line.strip().split(".")[0] for line in pathlib.Path(nodefile).read_text().splitlines()]
if observed.split(".")[0] not in entries:
    raise SystemExit("PBS_NODEFILE does not contain the observed compute host")
PY
CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})
CCBENCH_BASE="$REPO_ROOT/external/ccbench"
[[ -d "$CCBENCH_BASE" && ! -L "$CCBENCH_BASE" ]] || \
  fail 2 "CCBench submodule base is not a real directory"
read -r CCBENCH_GITLINK_MODE CCBENCH_GITLINK_TYPE \
  CCBENCH_EXPECTED_COMMIT CCBENCH_GITLINK_PATH < <(
    git -C "$REPO_ROOT" ls-tree "$CURRENT_COMMIT" -- external/ccbench
  )
[[ "$CCBENCH_GITLINK_MODE" == 160000 \
    && "$CCBENCH_GITLINK_TYPE" == commit \
    && "$CCBENCH_EXPECTED_COMMIT" =~ ^[0-9a-f]{40}$ \
    && "$CCBENCH_GITLINK_PATH" == external/ccbench ]] || \
  fail 2 "CCBench gitlink binding is invalid"
git -C "$CCBENCH_BASE" cat-file -e "$CCBENCH_EXPECTED_COMMIT^{commit}" || \
  fail 2 "CCBench gitlink commit is unavailable from the submodule repository"
SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
EXECUTING_SCRIPT_SHA256=$(sha256sum -- "$SCRIPT_PATH")
EXECUTING_SCRIPT_SHA256=${EXECUTING_SCRIPT_SHA256%% *}
COMMITTED_SCRIPT_SHA256=$(
  git -C "$REPO_ROOT" cat-file blob \
    "$CURRENT_COMMIT:tools/pegasus/b10_backoff_grid.sh" | sha256sum
)
COMMITTED_SCRIPT_SHA256=${COMMITTED_SCRIPT_SHA256%% *}
[[ "$EXECUTING_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" \
    && "$COMMITTED_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" ]] || \
  fail 2 "job script SHA binding mismatch"
BOOT_ID=$(tr -d '\n' </proc/sys/kernel/random/boot_id) || \
  fail 2 "cannot read compute boot id"
[[ -n "$BOOT_ID" ]] || fail 2 "compute boot id is empty"
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$RESERVATION_HOST"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$COMMITTED_SCRIPT_SHA256"
export IZANAGI_RESERVATION_NONCE="$B10_SUBMISSION_NONCE"
"$PY" -I -B - "$OUTPUT_ROOT/reservation.json" \
  "$OUTPUT_ROOT/qstat-f.stdout" "$OUTPUT_ROOT/qstat-f.stderr" \
  "$CURRENT_COMMIT" "$CCBENCH_EXPECTED_COMMIT" "$B10_RUN_KIND" <<'PY'
import hashlib, json, os, pathlib, sys
destination, stdout_path, stderr_path, repo_commit, ccbench_commit, run_kind = sys.argv[1:]
keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
binding = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key] for key in keys
}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    binding[key] = int(binding[key])
def evidence(path):
    raw = pathlib.Path(path).read_bytes()
    return {"filename": pathlib.Path(path).name, "sha256": hashlib.sha256(raw).hexdigest()}
document = {
    "schema_version": "b10-backoff-grid-reservation/v1",
    "run_kind": run_kind,
    "binding": binding,
    "source_binding": {
        "repository_commit": repo_commit,
        "ccbench_gitlink_commit": ccbench_commit,
    },
    "qstat_stdout": evidence(stdout_path),
    "qstat_stderr": evidence(stderr_path),
}
with open(destination, "x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, separators=(",", ":"))
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
PY

# Each job patches and builds an isolated detached CCBench worktree. The base
# submodule supplies Git objects and worktree administration only; its checkout
# is never changed by this payload.
CURRENT_STAGE=ccbench_worktree_setup
CCBENCH_WORKTREE="$TMPDIR/ccbench-source"
WORKTREE_SETUP_DEADLINE=$((SECONDS + WORKTREE_SETUP_CAP_S))
worktree_setup_run() {
  local remaining=$((WORKTREE_SETUP_DEADLINE - SECONDS))
  [[ "$remaining" -gt 0 ]] || fail 124 "CCBench worktree setup deadline exhausted"
  timeout "$remaining" "$@"
}
worktree_setup_run git -C "$CCBENCH_BASE" worktree add --detach \
  "$CCBENCH_WORKTREE" "$CCBENCH_EXPECTED_COMMIT" \
  >"$OUTPUT_ROOT/env/worktree-add.stdout" \
  2>"$OUTPUT_ROOT/env/worktree-add.stderr"
[[ -d "$CCBENCH_WORKTREE" && ! -L "$CCBENCH_WORKTREE" \
    && -f "$CCBENCH_WORKTREE/.git" && ! -L "$CCBENCH_WORKTREE/.git" ]] || \
  fail 2 "CCBench detached worktree was not materialized"
CCBENCH_WORKTREE_TOP=$(
  worktree_setup_run git -C "$CCBENCH_WORKTREE" rev-parse --show-toplevel
)
CCBENCH_WORKTREE_TOP=$(realpath -e -- "$CCBENCH_WORKTREE_TOP")
CCBENCH_WORKTREE_HEAD=$(
  worktree_setup_run git -C "$CCBENCH_WORKTREE" rev-parse --verify HEAD^{commit}
)
CCBENCH_WORKTREE_STATUS=$(
  worktree_setup_run git -C "$CCBENCH_WORKTREE" \
    status --porcelain --untracked-files=no
)
[[ "$CCBENCH_WORKTREE_TOP" == "$CCBENCH_WORKTREE" \
    && "$CCBENCH_WORKTREE_HEAD" == "$CCBENCH_EXPECTED_COMMIT" \
    && -z "$CCBENCH_WORKTREE_STATUS" ]] || \
  fail 2 "CCBench detached worktree identity or cleanliness mismatch"
"$PY" -I -B - "$OUTPUT_ROOT/env/ccbench-worktree.json" \
  "$CCBENCH_WORKTREE" "$CCBENCH_EXPECTED_COMMIT" "$CCBENCH_WORKTREE_HEAD" <<'PY'
import json, os, sys
destination, path, expected, observed = sys.argv[1:]
document = {
    "schema_version": "b10-ccbench-worktree/v1",
    "path": path,
    "detached": True,
    "expected_gitlink_commit": expected,
    "observed_head_commit": observed,
    "tracked_clean": True,
}
with open(destination, "x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, separators=(",", ":"))
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
PY

# Build registered dependency sources in fresh job scratch. Only the two install
# prefixes cross the boundary into the campaign drivers.
CURRENT_STAGE=dependency_policy_contract
POLICY="$REPO_ROOT/tools/pegasus/policy.json"
readarray -t dependency_policy_values < <("$PY" -I -B - "$POLICY" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
for key in (
    "gflags_expected_head",
    "glog_expected_head",
):
    print(policy[key])
PY
)
[[ ${#dependency_policy_values[@]} -eq 2 ]] || \
  fail 2 "dependency policy values are unavailable"
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=${dependency_policy_values[0]}
GLOG_EXPECTED_HEAD=${dependency_policy_values[1]}
[[ "$GFLAGS_SOURCE" == /* && "$GLOG_SOURCE" == /* \
  && "$GFLAGS_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ \
  && "$GLOG_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  fail 2 "dependency policy values are invalid"

DEPENDENCY_EVIDENCE="$OUTPUT_ROOT/env/dependencies"
mkdir -m 0700 "$DEPENDENCY_EVIDENCE"
for dep in gflags glog; do
  if [[ "$dep" == gflags ]]; then
    dep_source=$GFLAGS_SOURCE
    dep_expected=$GFLAGS_EXPECTED_HEAD
  else
    dep_source=$GLOG_SOURCE
    dep_expected=$GLOG_EXPECTED_HEAD
  fi
  [[ -d "$dep_source" && ! -L "$dep_source" ]] || \
    fail 2 "$dep source is not a real directory"
  dep_head=$(git -C "$dep_source" rev-parse --verify HEAD)
  printf '%s\n' "$dep_head" >"$DEPENDENCY_EVIDENCE/$dep-source-head.txt"
  git -C "$dep_source" status --porcelain --untracked-files=all \
    >"$DEPENDENCY_EVIDENCE/$dep-source-status.txt"
  if [[ "$dep_head" != "$dep_expected" \
      || -s "$DEPENDENCY_EVIDENCE/$dep-source-status.txt" ]]; then
    fail 2 "$dep source is not pinned-clean"
  fi
done

GFLAGS_INSTALL="$TMPDIR/gflags-install"
GLOG_INSTALL="$TMPDIR/glog-install"
DEPENDENCY_DEADLINE=$((SECONDS + DEPENDENCY_BUILD_CAP_S))
dependency_run() {
  local remaining=$((DEPENDENCY_DEADLINE - SECONDS))
  [[ "$remaining" -gt 0 ]] || \
    fail 124 "dependency group deadline exhausted"
  timeout "$remaining" "$@"
}
CURRENT_STAGE=dependency_build
dependency_run cmake -S "$GFLAGS_SOURCE" -B "$TMPDIR/gflags-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL"
dependency_run cmake --build "$TMPDIR/gflags-build" -j 48
dependency_run cmake --install "$TMPDIR/gflags-build"
dependency_run cmake -S "$GLOG_SOURCE" -B "$TMPDIR/glog-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL" \
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL"
dependency_run cmake --build "$TMPDIR/glog-build" -j 48
dependency_run cmake --install "$TMPDIR/glog-build"
export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL:$GLOG_INSTALL"

ENV_TAG=$("$PY" -I -B - "$REPO_ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign import p2_2
print(p2_2.resolve_site_runtime()[1].env_tag)
PY
)
mkdir -m 0700 "$OUTPUT_ROOT/env/$ENV_TAG" "$OUTPUT_ROOT/env/$ENV_TAG/claims"
export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"

freeze_digest() {
  "$PY" -I -B - "$REPO_ROOT" <<'PY'
import hashlib, pathlib, sys
repo = pathlib.Path(sys.argv[1])
digest = hashlib.sha256()
for relative in ("output/s1-freeze", "output/s8b-freeze"):
    root = repo / relative
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(repo).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
print(digest.hexdigest())
PY
}

FREEZE_BEFORE=$(freeze_digest)
[[ "$FREEZE_BEFORE" == "$EXPECTED_FREEZE_TREES_SHA256" ]] || \
  fail 2 "freeze trees do not match the B-10 preregistered bytes"
if [[ "$B10_RUN_KIND" == "t2266-tail" ]]; then
  CURRENT_STAGE=t2266_tail_sweep
elif [[ "$B10_RUN_KIND" == "t2418-explore" ]]; then
  CURRENT_STAGE=t2418_explore_sweep
else
  CURRENT_STAGE=extended_sweep
fi
if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
  CURRENT_STAGE=t2500_tail_formal_sweep
fi
SWEEP_COMMAND=("$PY" -I -B \
  "$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep.py" \
  "$WORKLOAD" --output-root "$OUTPUT_ROOT" \
  --cache-root "$B10_BUILD_CACHE_ROOT" \
  --ccbench-dir "$CCBENCH_WORKTREE")
if [[ "$B10_RUN_KIND" == "t2266-tail" \
    || "$B10_RUN_KIND" == "t2418-explore" ]]; then
  SWEEP_COMMAND+=(--run-kind "$B10_RUN_KIND")
fi
if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
  SWEEP_COMMAND=("$PY" -I -B \
    "$REPO_ROOT/orchestrator/campaign/b10_backoff_static_tail_formal.py" \
    --preregistration-commit "$B10_PREREGISTRATION_COMMIT" \
    run "$WORKLOAD" \
    --explore-campaign "$B10_EXPLORE_CAMPAIGN" \
    --output-root "$OUTPUT_ROOT" \
    --cache-root "$B10_BUILD_CACHE_ROOT" \
    --ccbench-dir "$CCBENCH_WORKTREE")
fi
timeout "$SWEEP_CAP_S" "${SWEEP_COMMAND[@]}"

if [[ "$B10_RUN_KIND" == "extended" ]]; then
  CURRENT_STAGE=add_analysis
  timeout "$AA_CAP_S" "$PY" -I -B \
    "$REPO_ROOT/orchestrator/campaign/backoff_overthrottle.py" \
    "$WORKLOAD" --output-root "$OUTPUT_ROOT" \
    --cache-root "$B10_BUILD_CACHE_ROOT" \
    --ccbench-dir "$CCBENCH_WORKTREE"

  CURRENT_STAGE=report
  timeout "$REPORT_CAP_S" "$PY" -I -B \
    "$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep_report.py" \
    "$WORKLOAD" --output-root "$OUTPUT_ROOT" --defer-plot
fi

CURRENT_STAGE=ccbench_worktree_cleanup
remove_ccbench_worktree

CURRENT_STAGE=finalize
FREEZE_AFTER=$(freeze_digest)
[[ "$FREEZE_AFTER" == "$EXPECTED_FREEZE_TREES_SHA256" ]] || \
  fail 2 "freeze trees changed during the job"
timeout "$FINALIZE_CAP_S" "$PY" -I -B - \
  "$OUTPUT_ROOT" "$WORKLOAD" "$PBS_JOBID" "$FREEZE_AFTER" \
  "$B10_RUN_KIND" <<'PY'
import hashlib, json, pathlib, sys
root, workload, job, freeze_hash, run_kind = sys.argv[1:]
base = pathlib.Path(root)
campaigns = [path for path in (base / "campaigns").iterdir() if path.is_dir()]
if len(campaigns) != 1:
    raise SystemExit(f"expected exactly one campaign, found {len(campaigns)}")
if run_kind == "t2266-tail":
    wal_path = campaigns[0] / "runs" / "wal.jsonl"
    commits = {
        parsed.get("variant")
        for row in wal_path.read_bytes().splitlines()
        if row
        for parsed in [json.loads(row)]
        if parsed.get("stage") == "commit"
    }
    if len(commits) != 8 or None in commits:
        raise SystemExit(f"T-2266 requires eight committed genomes, found {len(commits)}")
    report_stem = (
        campaigns[0] / "reports" / f"t2266-backoff-static-tail-{workload}"
    )
    for suffix in (".dat", ".json"):
        report = pathlib.Path(f"{report_stem}{suffix}")
        if not report.is_file() or report.is_symlink():
            raise SystemExit(f"T-2266 report artifact is missing: {report.name}")
elif run_kind == "t2418-explore":
    wal_path = campaigns[0] / "runs" / "wal.jsonl"
    commits = {
        parsed.get("variant")
        for row in wal_path.read_bytes().splitlines()
        if row
        for parsed in [json.loads(row)]
        if parsed.get("stage") == "commit"
    }
    if len(commits) != 5 or None in commits:
        raise SystemExit(f"T-2418 requires five committed genomes, found {len(commits)}")
    report_stem = (
        campaigns[0] / "reports" / f"t2418-backoff-static-explore-{workload}"
    )
    for suffix in (".dat", ".json"):
        report = pathlib.Path(f"{report_stem}{suffix}")
        if not report.is_file() or report.is_symlink():
            raise SystemExit(f"T-2418 report artifact is missing: {report.name}")
elif run_kind == "t2500-tail-formal":
    wal_path = campaigns[0] / "runs" / "wal.jsonl"
    commits = {
        parsed.get("variant")
        for row in wal_path.read_bytes().splitlines()
        if row
        for parsed in [json.loads(row)]
        if parsed.get("stage") == "commit"
    }
    if len(commits) != 8 or None in commits:
        raise SystemExit(f"T-2500 requires eight committed genomes, found {len(commits)}")
    report = campaigns[0] / "reports" / "t2500-backoff-static-tail-formal-execution.json"
    if not report.is_file() or report.is_symlink():
        raise SystemExit(f"T-2500 execution artifact is missing: {report.name}")
artifacts = {}
for path in sorted(item for item in campaigns[0].rglob("*") if item.is_file()):
    artifacts[path.relative_to(base).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
document = {
    "schema_version": "b10-backoff-grid-job-complete/v1",
    "status": "complete",
    "run_kind": run_kind,
    "workload": workload,
    "pbs_jobid": job,
    "campaign_id": campaigns[0].name,
    "freeze_trees_sha256": freeze_hash,
    "build_network": {
        "external_fetch_via_proxy": True,
        "dependency_revisions": "sha-pinned",
    },
    "artifacts": artifacts,
}
with (base / "completion.json").open("x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY
