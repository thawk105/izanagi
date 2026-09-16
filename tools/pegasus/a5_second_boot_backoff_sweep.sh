#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=02:00:00
#PBS -b 1

set -Eeuo pipefail
umask 077

# 内側の全 timeout cap は 30 + 120 + 180 + 5400 + 120 + 300 = 6150 秒。
# 終了余裕 1049 秒を足しても外側 walltime 7200 秒より小さい (7199 秒)。
# この上限は実測で証明されていない。実際に走る correctness は legacy workload
# (200 records / 4 threads / extime=1) であって full-scale verify ではない。
# 旧走の campaign 内 elapsed は write-heavy 605.614 秒 / balanced 314.775 秒だが、
# これは旧環境の記述値であって現行の上限ではない。
QSTAT_CAP_S=30
WORKTREE_SETUP_CAP_S=120
DEPENDENCY_BUILD_CAP_S=180
SWEEP_CAP_S=5400
WORKTREE_CLEANUP_CAP_S=120
FINALIZE_CAP_S=300
FINAL_MARGIN_S=1049
EXPECTED_WALLTIME_S=7200
INNER_CAP_TOTAL_S=$((QSTAT_CAP_S + WORKTREE_SETUP_CAP_S \
  + DEPENDENCY_BUILD_CAP_S + SWEEP_CAP_S + WORKTREE_CLEANUP_CAP_S \
  + FINALIZE_CAP_S))
[[ $((INNER_CAP_TOTAL_S + FINAL_MARGIN_S)) -lt "$EXPECTED_WALLTIME_S" ]] || {
  echo "A-5 internal timeout budget does not fit the PBS walltime" >&2
  exit 2
}

BUILD_NETWORK_PROXY_URL=http://10.120.96.1:8080
CURRENT_STAGE=bootstrap
PY=""
OUTPUT_ROOT=""
OUTPUT_ROOT_READY=0
REPO_BASE=""
JOB_REPO=""
CCBENCH_BASE=""
JOB_CCBENCH=""

write_failure_receipt() {
  local rc=$1
  local line=$2
  [[ -n "$PY" && -n "$OUTPUT_ROOT" && "$OUTPUT_ROOT_READY" -eq 1 ]] || return 0
  "$PY" -I -B - "$OUTPUT_ROOT" "$rc" "$CURRENT_STAGE" "$line" \
    "${PBS_JOBID:-}" <<'PY' || true
import hashlib, json, os, pathlib, sys
root, rc, stage, line, job = sys.argv[1:]
base = pathlib.Path(root)
path = pathlib.Path(root + ".failure.json")
wals = []
for candidate in sorted(base.glob("campaigns/*/runs/wal.jsonl")):
    if not candidate.is_file() or candidate.is_symlink():
        continue
    raw = candidate.read_bytes()
    last_terminal = None
    for row in raw.splitlines():
        if not row:
            continue
        try:
            parsed = json.loads(row)
        except json.JSONDecodeError:
            continue
        if parsed.get("stage") in {"commit", "abort"}:
            last_terminal = {
                "stage": parsed.get("stage"),
                "variant": parsed.get("variant"),
                "timestamp": parsed.get("ts"),
            }
    wals.append({
        "path": candidate.relative_to(base).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "last_terminal": last_terminal,
    })
document = {
    "schema_version": "a5-second-boot-job-failure/v1",
    "returncode": int(rc),
    "stage": stage,
    "line": int(line),
    "pbs_jobid": job,
    "campaign_wals": wals,
}
try:
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, payload) != len(payload):
            raise OSError("short failure receipt write")
        os.fsync(fd)
    finally:
        os.close(fd)
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

remove_worktrees() {
  local cleanup_rc=0
  local command_rc=0
  local deadline=$((SECONDS + WORKTREE_CLEANUP_CAP_S))
  local remaining
  if [[ -n "$CCBENCH_BASE" && -n "$JOB_CCBENCH" ]]; then
    remaining=$((deadline - SECONDS))
    if [[ "$remaining" -le 0 ]]; then
      cleanup_rc=124
    else
      timeout "$remaining" git -C "$CCBENCH_BASE" worktree remove --force \
        "$JOB_CCBENCH" >>"$OUTPUT_ROOT/env/ccbench-worktree-remove.stdout" \
        2>>"$OUTPUT_ROOT/env/ccbench-worktree-remove.stderr" || command_rc=$?
      [[ "$command_rc" -eq 0 ]] || cleanup_rc=$command_rc
      [[ "$command_rc" -eq 0 ]] && JOB_CCBENCH=""
    fi
  fi
  command_rc=0
  if [[ -n "$REPO_BASE" && -n "$JOB_REPO" ]]; then
    remaining=$((deadline - SECONDS))
    if [[ "$remaining" -le 0 ]]; then
      [[ "$cleanup_rc" -ne 0 ]] || cleanup_rc=124
    else
      timeout "$remaining" git -C "$REPO_BASE" worktree remove --force \
        "$JOB_REPO" >>"$OUTPUT_ROOT/env/repo-worktree-remove.stdout" \
        2>>"$OUTPUT_ROOT/env/repo-worktree-remove.stderr" || command_rc=$?
      [[ "$cleanup_rc" -ne 0 || "$command_rc" -eq 0 ]] || cleanup_rc=$command_rc
      [[ "$command_rc" -eq 0 ]] && JOB_REPO=""
    fi
  fi
  {
    printf '%s\n' "$cleanup_rc"
    [[ -z "$JOB_CCBENCH" ]] || \
      printf 'remaining_ccbench_path=%s\n' "$JOB_CCBENCH"
    [[ -z "$JOB_REPO" ]] || \
      printf 'remaining_repo_path=%s\n' "$JOB_REPO"
  } >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
  return "$cleanup_rc"
}

cleanup_worktrees() {
  local original_rc=$?
  local cleanup_rc=0
  trap - EXIT ERR
  if [[ "$OUTPUT_ROOT_READY" -eq 1 ]]; then
    CURRENT_STAGE=worktree_cleanup
    remove_worktrees || cleanup_rc=$?
  fi
  if [[ "$original_rc" -eq 0 && "$cleanup_rc" -ne 0 ]]; then
    write_failure_receipt "$cleanup_rc" "${BASH_LINENO[0]:-0}"
    original_rc=$cleanup_rc
  fi
  exit "$original_rc"
}
trap cleanup_worktrees EXIT

[[ -n "${PBS_JOBID:-}" && -n "${PBS_NODEFILE:-}" \
  && -n "${PBS_O_WORKDIR:-}" && -n "${A5_WORKLOAD:-}" \
  && -n "${A5_OUTPUT_ROOT:-}" && -n "${A5_SUBMISSION_NONCE:-}" \
  && -n "${A5_EXPECTED_HEAD:-}" && -n "${JOB_SCRIPT_SHA256:-}" ]] || \
  fail 2 "PBS and A-5 submission bindings are required"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || \
  fail 2 "PBS_JOBID contains unsafe characters"
[[ "$A5_SUBMISSION_NONCE" =~ ^[0-9a-f]{32}$ ]] || \
  fail 2 "A5_SUBMISSION_NONCE must be 32 lowercase hex characters"
[[ "$A5_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  fail 2 "A5_EXPECTED_HEAD must be a full lowercase commit id"
[[ "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]] || \
  fail 2 "JOB_SCRIPT_SHA256 must be 64 lowercase hex characters"

WORKLOAD=$A5_WORKLOAD
case "$WORKLOAD" in
  write-heavy|balanced) ;;
  *) fail 2 "workload must be write-heavy or balanced" ;;
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

# FetchContent dependencies use the same proxy path as B-10; the campaign
# driver has no binding for the former third-party cache environment variable.
export http_proxy="$BUILD_NETWORK_PROXY_URL"
export https_proxy="$BUILD_NETWORK_PROXY_URL"
for command_name in \
  git cmake cc c++ make ar ranlib as ld numactl timeout qstat sha256sum \
  hostname mkdir rmdir realpath date env; do
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

REPO_BASE=$(realpath -e -- "$PBS_O_WORKDIR")
[[ -d "$REPO_BASE" && ! -L "$REPO_BASE" ]] || \
  fail 2 "PBS_O_WORKDIR must identify the repository root"
CURRENT_COMMIT=$(git -C "$REPO_BASE" rev-parse --verify HEAD^{commit})
[[ "$CURRENT_COMMIT" == "$A5_EXPECTED_HEAD" ]] || \
  fail 2 "repository HEAD differs from the submitted commit"

OUTPUT_ROOT=$A5_OUTPUT_ROOT
[[ "$OUTPUT_ROOT" == /* && ! -e "$OUTPUT_ROOT" ]] || \
  fail 2 "A5_OUTPUT_ROOT must be an absolute, job-unique, uncreated path"
"$PY" -I -B - "$REPO_BASE" "$OUTPUT_ROOT" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=False)
if target == repo or repo in target.parents or target in repo.parents:
    raise SystemExit("official output root must be outside the repository")
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    raise SystemExit("official output root has a repository ancestor")
PY
mkdir -m 0700 "$OUTPUT_ROOT"
OUTPUT_ROOT_READY=1
mkdir -m 0700 "$OUTPUT_ROOT/campaigns" "$OUTPUT_ROOT/campaign-locks" \
  "$OUTPUT_ROOT/env"

export TMPDIR="/scr/${PBS_JOBID//:/_}-a5-second-boot-${WORKLOAD}"
mkdir -m 0700 "$TMPDIR"
export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"

HOSTNAME_SHORT=$(hostname) || fail 2 "cannot observe compute hostname"
HOSTNAME_FQDN=$(hostname -f) || fail 2 "cannot observe compute hostname -f"
[[ "$HOSTNAME_SHORT" =~ ^bnode[0-9]+([.].*)?$ ]] || \
  fail 2 "A-5 job body is compute-node-only"
[[ -f "$PBS_NODEFILE" && ! -L "$PBS_NODEFILE" ]] || \
  fail 2 "PBS_NODEFILE must be a regular non-symlink file"

CURRENT_STAGE=allocation_reservation
qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout "$QSTAT_CAP_S" qstat -f "$QSTAT_JOBID" >"$OUTPUT_ROOT/qstat-f.stdout" \
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
  fail 2 "qstat walltime differs from the A-5 PBS envelope"
if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]; then
  RESERVATION_HOST=$HOSTNAME_SHORT
elif [[ "$ASSIGNED_HOST" == "$HOSTNAME_FQDN" ]]; then
  RESERVATION_HOST=$HOSTNAME_FQDN
else
  fail 2 "qstat assigned host has no exact hostname observation"
fi
"$PY" -I -B - "$PBS_NODEFILE" "$HOSTNAME_SHORT" <<'PY'
import pathlib, sys
nodefile, observed = sys.argv[1:]
entries = [line.strip().split(".")[0] for line in pathlib.Path(nodefile).read_text().splitlines()]
if observed.split(".")[0] not in entries:
    raise SystemExit("PBS_NODEFILE does not contain the observed compute host")
PY

CCBENCH_BASE="$REPO_BASE/external/ccbench"
[[ -d "$CCBENCH_BASE" && ! -L "$CCBENCH_BASE" ]] || \
  fail 2 "CCBench submodule base is not a real directory"
read -r CCBENCH_GITLINK_MODE CCBENCH_GITLINK_TYPE \
  CCBENCH_EXPECTED_COMMIT CCBENCH_GITLINK_PATH < <(
    git -C "$REPO_BASE" ls-tree "$CURRENT_COMMIT" -- external/ccbench
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
  git -C "$REPO_BASE" cat-file blob \
    "$CURRENT_COMMIT:tools/pegasus/a5_second_boot_backoff_sweep.sh" | sha256sum
)
COMMITTED_SCRIPT_SHA256=${COMMITTED_SCRIPT_SHA256%% *}
[[ "$EXECUTING_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" \
    && "$COMMITTED_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" ]] || \
  fail 2 "job script SHA binding mismatch"

readarray -t boot_values < <("$PY" -I -B - <<'PY'
from pathlib import Path
boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
rows = [line.split() for line in Path("/proc/stat").read_text().splitlines()
        if line.startswith("btime ")]
if len(rows) != 1 or len(rows[0]) != 2 or not rows[0][1].isdigit():
    raise SystemExit("/proc/stat must contain exactly one valid btime row")
if not boot_id:
    raise SystemExit("compute boot id is empty")
print(boot_id)
print(int(rows[0][1]))
PY
)
BOOT_ID=${boot_values[0]:-}
BOOT_EPOCH=${boot_values[1]:-}
[[ -n "$BOOT_ID" && "$BOOT_EPOCH" =~ ^[0-9]+$ ]] || \
  fail 2 "node boot evidence is unavailable"
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$RESERVATION_HOST"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$COMMITTED_SCRIPT_SHA256"
export IZANAGI_RESERVATION_NONCE="$A5_SUBMISSION_NONCE"
"$PY" -I -B - "$OUTPUT_ROOT/reservation.json" \
  "$OUTPUT_ROOT/qstat-f.stdout" "$OUTPUT_ROOT/qstat-f.stderr" \
  "$CURRENT_COMMIT" "$CCBENCH_EXPECTED_COMMIT" "$HOSTNAME_SHORT" \
  "$HOSTNAME_FQDN" "$BOOT_EPOCH" <<'PY'
import hashlib, json, os, pathlib, sys
(destination, stdout_path, stderr_path, repo_commit, ccbench_commit,
 hostname, fqdn, boot_epoch) = sys.argv[1:]
keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
binding = {key.lower(): os.environ["IZANAGI_RESERVATION_" + key] for key in keys}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    binding[key] = int(binding[key])
def evidence(path):
    raw = pathlib.Path(path).read_bytes()
    return {"filename": pathlib.Path(path).name, "sha256": hashlib.sha256(raw).hexdigest()}
document = {
    "schema_version": "a5-second-boot-reservation/v1",
    "binding": binding,
    "node_boot_evidence": {
        "hostname": hostname,
        "fqdn": fqdn,
        "boot_id": binding["boot_id"],
        "boot_epoch": int(boot_epoch),
        "pbs_jobid": binding["job_id"],
    },
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

# The campaign driver resolves external/ccbench relative to its own repository.
# Materialize both repositories in scratch so the submitted checkout is never patched.
CURRENT_STAGE=scratch_worktree_setup
JOB_REPO="$TMPDIR/job-repo"
WORKTREE_SETUP_DEADLINE=$((SECONDS + WORKTREE_SETUP_CAP_S))
worktree_setup_run() {
  local remaining=$((WORKTREE_SETUP_DEADLINE - SECONDS))
  [[ "$remaining" -gt 0 ]] || fail 124 "scratch worktree setup deadline exhausted"
  timeout "$remaining" "$@"
}
worktree_setup_run git -C "$REPO_BASE" worktree add --detach \
  "$JOB_REPO" "$CURRENT_COMMIT" >"$OUTPUT_ROOT/env/repo-worktree-add.stdout" \
  2>"$OUTPUT_ROOT/env/repo-worktree-add.stderr"
[[ -d "$JOB_REPO" && ! -L "$JOB_REPO" \
    && -f "$JOB_REPO/.git" && ! -L "$JOB_REPO/.git" ]] || \
  fail 2 "superproject detached worktree was not materialized"
[[ -d "$JOB_REPO/external/ccbench" && ! -L "$JOB_REPO/external/ccbench" ]] || \
  fail 2 "superproject gitlink checkout is unavailable"
rmdir "$JOB_REPO/external/ccbench" || \
  fail 2 "superproject gitlink checkout is not empty"
JOB_CCBENCH="$JOB_REPO/external/ccbench"
worktree_setup_run git -C "$CCBENCH_BASE" worktree add --detach \
  "$JOB_CCBENCH" "$CCBENCH_EXPECTED_COMMIT" \
  >"$OUTPUT_ROOT/env/ccbench-worktree-add.stdout" \
  2>"$OUTPUT_ROOT/env/ccbench-worktree-add.stderr"
[[ -d "$JOB_CCBENCH" && ! -L "$JOB_CCBENCH" \
    && -f "$JOB_CCBENCH/.git" && ! -L "$JOB_CCBENCH/.git" ]] || \
  fail 2 "CCBench detached worktree was not materialized"
JOB_REPO_HEAD=$(worktree_setup_run git -C "$JOB_REPO" rev-parse --verify HEAD^{commit})
JOB_REPO_STATUS=$(worktree_setup_run git -C "$JOB_REPO" status --porcelain --untracked-files=no)
JOB_CCBENCH_HEAD=$(worktree_setup_run git -C "$JOB_CCBENCH" rev-parse --verify HEAD^{commit})
JOB_CCBENCH_STATUS=$(worktree_setup_run git -C "$JOB_CCBENCH" status --porcelain --untracked-files=no)
[[ "$JOB_REPO_HEAD" == "$CURRENT_COMMIT" && -z "$JOB_REPO_STATUS" \
    && "$JOB_CCBENCH_HEAD" == "$CCBENCH_EXPECTED_COMMIT" \
    && -z "$JOB_CCBENCH_STATUS" ]] || \
  fail 2 "scratch worktree identity or cleanliness mismatch"
"$PY" -I -B - "$OUTPUT_ROOT/env/scratch-worktrees.json" "$JOB_REPO" \
  "$CURRENT_COMMIT" "$JOB_CCBENCH" "$CCBENCH_EXPECTED_COMMIT" <<'PY'
import json, os, sys
destination, repo, repo_commit, ccbench, ccbench_commit = sys.argv[1:]
document = {
    "schema_version": "a5-scratch-worktrees/v1",
    "superproject": {"path": repo, "commit": repo_commit, "detached": True, "tracked_clean": True},
    "ccbench": {"path": ccbench, "commit": ccbench_commit, "detached": True, "tracked_clean": True},
}
with open(destination, "x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, separators=(",", ":"))
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
PY

CURRENT_STAGE=dependency_policy_contract
POLICY="$JOB_REPO/tools/pegasus/policy.json"
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
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_BASE/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
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
  [[ "$remaining" -gt 0 ]] || fail 124 "dependency group deadline exhausted"
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

ENV_TAG=$("$PY" -I -B - "$JOB_REPO" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign import p2_2
print(p2_2.resolve_site_runtime()[1].env_tag)
PY
)
[[ "$ENV_TAG" == pegasus ]] || fail 2 "A-5 requires the Pegasus environment contract"
mkdir -m 0700 "$OUTPUT_ROOT/env/pegasus" "$OUTPUT_ROOT/env/pegasus/claims"
export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"

CURRENT_STAGE=backoff_sweep
timeout "$SWEEP_CAP_S" "$PY" -I -B \
  "$JOB_REPO/orchestrator/campaign/backoff_sweep.py" "$WORKLOAD"

CURRENT_STAGE=finalize
timeout "$FINALIZE_CAP_S" "$PY" -I -B - \
  "$JOB_REPO" "$OUTPUT_ROOT" "$WORKLOAD" "$PBS_JOBID" "$HOSTNAME_SHORT" \
  "$HOSTNAME_FQDN" "$BOOT_ID" "$BOOT_EPOCH" "$CURRENT_COMMIT" \
  "$CCBENCH_EXPECTED_COMMIT" <<'PY'
import hashlib
import json
import math
import os
import pathlib
import statistics
import sys

(job_repo, root, workload, pbs_jobid, hostname, fqdn, boot_id, boot_epoch,
 repository_commit, ccbench_commit) = sys.argv[1:]
sys.path.insert(0, job_repo)

from orchestrator.calibrator import perf_preflight
from orchestrator.campaign import backoff_sweep, wal
from orchestrator.campaign.build_admission import GeneratorId, build_run_context
from orchestrator.campaign.layout import CampaignLayout

EXPECTED_GENOME_COUNT = 8
EXPECTED_TPS_COUNT = 5
BASELINE_FLAGS = {"BACK_OFF": 0, "BACKOFF_FIXED": -1}
TARGET_FIXED_US = {"write-heavy": 10, "balanced": 5}

base = pathlib.Path(root)
campaign_entries = list((base / "campaigns").iterdir())
campaigns = [
    path for path in campaign_entries
    if path.is_dir() and not path.is_symlink()
]
if len(campaign_entries) != 1 or len(campaigns) != 1:
    raise SystemExit(
        f"expected exactly one real campaign directory, found "
        f"{len(campaign_entries)} entries / {len(campaigns)} real directories"
    )
campaign = campaigns[0]
layout = CampaignLayout(str(campaign))
wal_path = pathlib.Path(layout.wal_file)
lock_path = pathlib.Path(layout.lock_file)
if (not wal_path.is_file() or wal_path.is_symlink()
        or not lock_path.is_file() or lock_path.is_symlink()):
    raise SystemExit("campaign WAL and lock must be regular non-symlink files")

wal_before = wal_path.read_bytes()
lock_before = lock_path.read_bytes()
policy = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP).policy
states = wal.replay(layout, admission_policy=policy)
records = wal.read_records(layout)
wal_after = wal_path.read_bytes()
lock_after = lock_path.read_bytes()
if wal_before != wal_after or lock_before != lock_after:
    raise SystemExit("campaign WAL or lock changed during finalizer replay")

expected_genome_objects = backoff_sweep.genomes()
expected_genomes = {genome.canonical() for genome in expected_genome_objects}
if len(expected_genomes) != EXPECTED_GENOME_COUNT:
    raise SystemExit("driver no longer defines exactly eight unique genomes")
flags_by_genome = {
    genome.canonical(): dict(genome.flags) for genome in expected_genome_objects
}
abort_count = sum(record.stage == "abort" for record in records)
if (len(states) != EXPECTED_GENOME_COUNT
        or abort_count != 0
        or any(not state.committed or state.aborted for state in states.values())):
    raise SystemExit(
        "A-5 requires exactly eight committed genomes and zero abort records"
    )

def one_attempt_record(variant, attempt_id, stage):
    matches = [
        record for record in records
        if record.variant == variant and record.stage == stage
        and record.payload.get("build_attempt_id") == attempt_id
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"expected one {stage} record for committed attempt {variant}, "
            f"found {len(matches)}"
        )
    return matches[0]

committed = {}
toolchains = []
preflights = []
counter_statuses = []
for variant, state in states.items():
    if (state.committed_attempt_id is None
            or state.committed_build_start is None
            or state.committed_bench is None
            or state.last_terminal is None
            or state.last_terminal.stage != "commit"):
        raise SystemExit(f"committed projection is incomplete for {variant}")
    canonical = state.committed_build_start.payload.get("genome")
    if canonical not in expected_genomes or canonical in committed:
        raise SystemExit("committed genome set is noncanonical or duplicated")
    bench_payload = state.committed_bench.payload
    samples = bench_payload.get("tps")
    if (type(samples) is not list or len(samples) != EXPECTED_TPS_COUNT
            or any(type(value) not in {int, float} or isinstance(value, bool)
                   or not math.isfinite(value) or value <= 0 for value in samples)):
        raise SystemExit(f"{canonical} must have exactly five finite positive TPS samples")
    median = statistics.median(samples)
    if bench_payload.get("median_tps") != median:
        raise SystemExit(f"bench median does not match the five TPS samples: {canonical}")
    if state.last_terminal.payload.get("fitness_tps") != median:
        raise SystemExit(f"commit fitness does not match the bench median: {canonical}")

    build_done = one_attempt_record(
        variant, state.committed_attempt_id, "build_done",
    )
    toolchain = build_done.payload.get("toolchain")
    if type(toolchain) is not dict or not toolchain:
        raise SystemExit(f"toolchain evidence is missing: {canonical}")
    observation = perf_preflight.validate_perf_observation(
        bench_payload.get("perf_observation"),
        run_cmd=bench_payload.get("run_cmd"),
        leading_indicators=bench_payload.get("leading_indicators"),
    )
    committed[canonical] = {
        "samples": list(samples),
        "median": median,
        "flags": flags_by_genome[canonical],
    }
    toolchains.append(toolchain)
    preflights.append(observation["preflight"])
    counter_statuses.append(observation["counter_status"])

committed_genomes = set(committed)
if committed_genomes != expected_genomes:
    raise SystemExit("all eight canonical genomes must commit")

def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

if len({canonical_json(value) for value in toolchains}) != 1:
    raise SystemExit("toolchain evidence differs across committed genomes")
if len({canonical_json(value) for value in preflights}) != 1:
    raise SystemExit("perf preflight evidence differs across committed genomes")

def selected_by_flags(flags):
    matches = [
        value for value in committed.values()
        if {key: value["flags"][key] for key in ("BACK_OFF", "BACKOFF_FIXED")}
        == flags
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one genome with flags {flags!r}")
    return matches[0]

target_fixed_us = TARGET_FIXED_US[workload]
baseline = selected_by_flags(BASELINE_FLAGS)
target = selected_by_flags({"BACK_OFF": 1, "BACKOFF_FIXED": target_fixed_us})
ratio = target["median"] / baseline["median"]
improvement_percent = (target["median"] / baseline["median"] - 1) * 100
if not math.isfinite(ratio) or not math.isfinite(improvement_percent):
    raise SystemExit("headline ratio is not finite")

reservation = json.loads((base / "reservation.json").read_text(encoding="utf-8"))
node = reservation.get("node_boot_evidence")
source = reservation.get("source_binding")
expected_node = {
    "hostname": hostname,
    "fqdn": fqdn,
    "boot_id": boot_id,
    "boot_epoch": int(boot_epoch),
    "pbs_jobid": pbs_jobid,
}
expected_source = {
    "repository_commit": repository_commit,
    "ccbench_gitlink_commit": ccbench_commit,
}
if node != expected_node or source != expected_source:
    raise SystemExit("reservation provenance does not match finalizer inputs")

document = {
    "schema_version": "a5-second-boot-result/v1",
    "status": "complete",
    "workload": workload,
    "target_fixed_us": target_fixed_us,
    "no_backoff_median_tps": baseline["median"],
    "target_median_tps": target["median"],
    "no_backoff_tps": baseline["samples"],
    "target_tps": target["samples"],
    "ratio": ratio,
    "improvement_percent": improvement_percent,
    "campaign_id": campaign.name,
    "wal_sha256": hashlib.sha256(wal_after).hexdigest(),
    "lock_sha256": hashlib.sha256(lock_after).hexdigest(),
    "pbs_jobid": pbs_jobid,
    "hostname": hostname,
    "fqdn": fqdn,
    "boot_id": boot_id,
    "boot_epoch": int(boot_epoch),
    "repository_commit": repository_commit,
    "ccbench_commit": ccbench_commit,
    "toolchain": toolchains[0],
    "perf_preflight": preflights[0],
    "perf_counter_statuses": sorted(set(counter_statuses)),
}
payload = (canonical_json(document) + "\n").encode("utf-8")
destination = base / "result.json"
temporary = base / f".result.json.tmp.{os.getpid()}"
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(temporary, flags, 0o600)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
except BaseException:
    temporary.unlink(missing_ok=True)
    raise
try:
    os.link(temporary, destination, follow_symlinks=False)
finally:
    temporary.unlink(missing_ok=True)
parent_fd = os.open(base, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
try:
    os.fsync(parent_fd)
finally:
    os.close(parent_fd)
PY

CURRENT_STAGE=complete
