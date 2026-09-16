#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=06:00:00
#PBS -b 1
#
# Compute-only job body for the D95 paper-story A-1 exploratory study. Legacy
# v2 remains one job; each v3 invocation owns exactly one workload job root and
# consumes the create-only exact-triple group receipt. This file is not a submitter.
set -Eeuo pipefail
umask 077

EXPECTED_QUEUE="gen_S"
SUBMISSION_SCHEMA="paper-story-a1-paired-submission/v1"
ACCOUNTING_STARTED_EPOCH_S=""
ACCOUNTING_STARTED_MONOTONIC_S=""
ACCOUNTING_TIMES_BASELINE_RAW=""
ACCOUNTING_ENDED_EPOCH_S=""
ACCOUNTING_ENDED_MONOTONIC_S=""
ACCOUNTING_TIMES_FINAL_RAW=""
ACCOUNTING_TIMES_BASELINE_PATH=""
ACCOUNTING_TIMES_FINAL_PATH=""
ACCOUNTING_SESSION_BASELINE_PATH=""
ACCOUNTING_PROCESS_SET_SURVIVORS_PATH=""
ACCOUNTING_PROCESS_SET_BASELINE_ERROR_PATH=""
ACCOUNTING_PROCESS_SET_ERROR_PATH=""
DRIVER_RELATIVE="orchestrator/campaign/paper_story_a1_paired.py"
PIPELINE_RELATIVE="orchestrator/campaign/pipeline.py"
JOB_RELATIVE="tools/pegasus/paper_story_a1_paired.sh"
PEGASUS_POLICY_RELATIVE="tools/pegasus/policy.json"

refuse() {
  printf 'paper-story A-1 job refused: %s\n' "$1" >&2
  exit 2
}

REQUESTED_STUDY_ID=${IZANAGI_A1_STUDY_ID:-}
V3_STUDY=0
case "$REQUESTED_STUDY_ID" in
  paper-story-a1-20260826-sized-v1)
    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
    POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v2.json"
    ;;
  paper-story-a1-20260901-balanced5-pilot-v1)
    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
    POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
    V3_STUDY=1
    ;;
  paper-story-a1-20260901-balanced5-sized-v1)
    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
    POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v3-sized.json"
    V3_STUDY=1
    ;;
  *)
    refuse "study ID differs"
    ;;
esac
NON_CERTIFYING_SOURCE_RELATIVE_PATHS=(
  "orchestrator/campaign/paper_story_a1_paired.py"
  "orchestrator/campaign/paper_story_a1_paired.v2.json"
  "orchestrator/campaign/pipeline.py"
  "tools/pegasus/paper_story_a1_paired.sh"
  "orchestrator/campaign/campaign_lock.py"
  "orchestrator/campaign/ident.py"
  "orchestrator/campaign/wal.py"
  "orchestrator/campaign/loop.py"
  "orchestrator/campaign/trial_registry.py"
)
if [[ "$V3_STUDY" -eq 1 ]]; then
  NON_CERTIFYING_SOURCE_RELATIVE_PATHS[1]="$POLICY_RELATIVE"
  NON_CERTIFYING_SOURCE_RELATIVE_PATHS+=("orchestrator/calibrator/runner.py")
fi

if [[ "$POLICY_RELATIVE" == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json" ||
      "$POLICY_RELATIVE" == "orchestrator/campaign/paper_story_a1_paired.v3-sized.json" ]]; then
  if [[ "$POLICY_RELATIVE" == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json" ]]; then
    SOURCE_CONTRACT_RELATIVE="orchestrator/campaign/paper_story_a1_source.v1.json"
    SOURCE_AMENDMENT_RELATIVE="output/insights/2026-09-11/t2397-a1-source-amendment/README.md"
  else
    SOURCE_CONTRACT_RELATIVE="orchestrator/campaign/paper_story_a1_source.v2.json"
    SOURCE_AMENDMENT_RELATIVE="output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md"
  fi
  NON_CERTIFYING_SOURCE_RELATIVE_PATHS+=(
    "$SOURCE_CONTRACT_RELATIVE"
    "orchestrator/campaign/paper_story_a1_source.py"
    "patches/silo-backoff-fixed.patch"
    "$SOURCE_AMENDMENT_RELATIVE"
  )
fi

[[ -n "${PBS_JOBID:-}" ]] || refuse "PBS_JOBID is required"
[[ "$PBS_JOBID" =~ ^(0:)?[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || refuse "unsafe PBS_JOBID"
[[ -n "${PBS_O_HOST:-}" ]] || refuse "PBS_O_HOST is required"
[[ -n "${PBS_O_WORKDIR:-}" ]] || refuse "PBS_O_WORKDIR is required"
[[ "${IZANAGI_A1_STUDY_ID:-}" == "$EXPECTED_STUDY_ID" ]] || refuse "study ID differs"
[[ "${IZANAGI_EXPECTED_HEAD:-}" =~ ^[0-9a-f]{40}$ ]] || refuse "expected HEAD is invalid"
[[ -n "${IZANAGI_A1_ATTEMPT_ROOT:-}" ]] || refuse "attempt root is required"
[[ -n "${IZANAGI_A1_ACQUISITION_RECEIPT:-}" ]] || refuse "acquisition receipt is required"
[[ -n "${IZANAGI_A1_COMPLETION_RECEIPT:-}" ]] || refuse "completion receipt is required"
[[ -n "${IZANAGI_SUBMISSION_NONCE:-}" ]] || refuse "submission nonce is required"
[[ "$IZANAGI_SUBMISSION_NONCE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || \
  refuse "submission nonce is unsafe"
if [[ "$V3_STUDY" -eq 1 ]]; then
  case "${IZANAGI_A1_WORKLOAD:-}" in
    write-heavy|balanced|read-heavy) ;;
    *) refuse "v3 workload selector differs" ;;
  esac
  ACCOUNTING_STARTED_EPOCH_S=$(date +%s.%N) || refuse "cannot start accounting epoch"
  ACCOUNTING_STARTED_MONOTONIC_S=$(cut -d' ' -f1 /proc/uptime) || \
    refuse "cannot start accounting monotonic clock"
  ACCOUNTING_TIMES_BASELINE_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-times-baseline.raw"
  ACCOUNTING_TIMES_FINAL_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-times-final.raw"
  ACCOUNTING_SESSION_BASELINE_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-session-baseline.pids"
  ACCOUNTING_PROCESS_SET_SURVIVORS_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-process-set-survivors.pids"
  ACCOUNTING_PROCESS_SET_BASELINE_ERROR_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-process-set-baseline.error"
  ACCOUNTING_PROCESS_SET_ERROR_PATH="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD/accounting-process-set-audit.error"
  set -o noclobber
  if ! LC_ALL=C times >"$ACCOUNTING_TIMES_BASELINE_PATH" 2>&1; then
    set +o noclobber
    refuse "cannot capture accounting baseline"
  fi
  set +o noclobber
  ACCOUNTING_TIMES_BASELINE_RAW=$(<"$ACCOUNTING_TIMES_BASELINE_PATH")
fi
# The calibration job's dependency staging uses /scr. Preserve that compute
# path, and retain the incoming TMPDIR only as the fallback when /scr is absent.
DEPENDENCY_SCRATCH_PARENT=/scr
if [[ ! -d "$DEPENDENCY_SCRATCH_PARENT" ]]; then
  DEPENDENCY_SCRATCH_PARENT=${TMPDIR:-}
fi
[[ "$IZANAGI_A1_ATTEMPT_ROOT" = /* ]] || refuse "attempt root must be absolute"
[[ "$IZANAGI_A1_ACQUISITION_RECEIPT" = /* ]] || refuse "acquisition receipt must be absolute"
[[ "$IZANAGI_A1_COMPLETION_RECEIPT" = /* ]] || refuse "completion receipt must be absolute"

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -f "$REPO_ROOT/$DRIVER_RELATIVE" ]] || refuse "tracked driver is missing"
[[ -f "$REPO_ROOT/$POLICY_RELATIVE" ]] || refuse "tracked policy is missing"
[[ -f "$REPO_ROOT/$JOB_RELATIVE" ]] || refuse "tracked job body is missing"
[[ -f "$REPO_ROOT/$PEGASUS_POLICY_RELATIVE" ]] || refuse "Pegasus policy is missing"
for relative in "${NON_CERTIFYING_SOURCE_RELATIVE_PATHS[@]}"; do
  [[ -f "$REPO_ROOT/$relative" ]] || refuse "non-certifying source closure is missing"
done
CURRENT_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD) || refuse "cannot resolve HEAD"
[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]] || refuse "HEAD mismatch"
if [[ "$V3_STUDY" -eq 1 ]]; then
  PARENT_STATUS=$(git -C "$REPO_ROOT" status --ignore-submodules=all \
    --porcelain --untracked-files=all) || refuse "cannot inspect working tree"
else
  PARENT_STATUS=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all) || \
    refuse "cannot inspect working tree"
fi
[[ -z "$PARENT_STATUS" ]] || refuse "working tree is dirty"
CURRENT_SCRIPT_SHA=$(sha256sum "$REPO_ROOT/$JOB_RELATIVE" | awk '{print $1}') || \
  refuse "cannot hash tracked job body"
[[ "$CURRENT_SCRIPT_SHA" =~ ^[0-9a-f]{64}$ ]] || refuse "tracked job body SHA is invalid"
ATTEMPT_CHILD=${IZANAGI_A1_ATTEMPT_ROOT##*/}
if [[ "$V3_STUDY" -eq 1 ]]; then
  [[ "$IZANAGI_SUBMISSION_NONCE" == \
    "$ATTEMPT_CHILD.$IZANAGI_A1_WORKLOAD" ]] || \
    refuse "submission nonce differs from workload attempt child"
else
  [[ "$IZANAGI_SUBMISSION_NONCE" == "$ATTEMPT_CHILD" ]] || \
    refuse "submission nonce differs from attempt child"
fi

PYTHON_BIN=""
for candidate in python3.10 python3.11 python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && \
      "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v "$candidate")
    break
  fi
done
[[ -n "$PYTHON_BIN" ]] || refuse "Python 3.10 or newer is required"

if [[ "$V3_STUDY" -eq 1 ]]; then
  set -o noclobber
  if ! "$PYTHON_BIN" - "$$" >"$ACCOUNTING_SESSION_BASELINE_PATH" \
    2>"$ACCOUNTING_PROCESS_SET_BASELINE_ERROR_PATH" <<'PY'
import os
import pathlib
import sys

root = int(sys.argv[1])
uid = os.geteuid()
members = []

def identity(candidate):
    info = candidate.stat(follow_symlinks=False)
    if info.st_uid != uid:
        return None
    raw = (candidate / "stat").read_text()
    closing = raw.rfind(")")
    fields = raw[closing + 2:].split() if closing >= 0 else []
    if len(fields) <= 19:
        raise RuntimeError(f"cannot parse process identity: {candidate.name}")
    return int(candidate.name), int(fields[19])

for candidate in pathlib.Path("/proc").iterdir():
    if not candidate.name.isdigit():
        continue
    try:
        observed = identity(candidate)
        if observed is not None:
            members.append(observed)
    except (FileNotFoundError, ProcessLookupError):
        continue
print("single-tenant-same-uid-process-set/v1")
for pid, starttime in sorted(members):
    print(pid, starttime)
PY
  then
    set +o noclobber
    refuse "cannot capture accounting session baseline"
  fi
  set +o noclobber
fi

audit_v3_job_process_set() {
  local scan_rc
  local survivors
  set -o noclobber
  if "$PYTHON_BIN" - "$$" "$ACCOUNTING_SESSION_BASELINE_PATH" \
    >"$ACCOUNTING_PROCESS_SET_SURVIVORS_PATH" \
    2>"$ACCOUNTING_PROCESS_SET_ERROR_PATH" <<'PY'
import os
import pathlib
import sys

root = int(sys.argv[1])
baseline_path = pathlib.Path(sys.argv[2])
uid = os.geteuid()
checker = os.getpid()
method = "single-tenant-same-uid-process-set/v1"
lines = baseline_path.read_text().splitlines()
if not lines or lines[0] != method:
    raise SystemExit("job process-set baseline method is unavailable")
try:
    baseline = {
        (int(row.split()[0]), int(row.split()[1]))
        for row in lines[1:]
        if row
    }
except (IndexError, ValueError) as exc:
    raise SystemExit("job process-set baseline is corrupt") from exc

def identity(candidate):
    info = candidate.stat(follow_symlinks=False)
    if info.st_uid != uid:
        return None
    raw = (candidate / "stat").read_text()
    closing = raw.rfind(")")
    fields = raw[closing + 2:].split() if closing >= 0 else []
    if len(fields) <= 19:
        raise RuntimeError(f"cannot parse process identity: {candidate.name}")
    return int(candidate.name), int(fields[19])

def parent_pid(pid):
    raw = pathlib.Path(f"/proc/{pid}/stat").read_text()
    closing = raw.rfind(")")
    fields = raw[closing + 2:].split() if closing >= 0 else []
    if len(fields) <= 1:
        raise RuntimeError(f"cannot parse process parent: {pid}")
    return int(fields[1])

try:
    job_session = os.getsid(root)
except ProcessLookupError as exc:
    raise SystemExit("job shell disappeared during process-set audit") from exc
ancestors = set()
cursor = root
while cursor > 1:
    try:
        cursor = parent_pid(cursor)
    except (FileNotFoundError, ProcessLookupError, ValueError, RuntimeError):
        break
    ancestors.add(cursor)

observed = []
for candidate in pathlib.Path("/proc").iterdir():
    if not candidate.name.isdigit():
        continue
    pid = int(candidate.name)
    if pid in {root, checker} or pid in ancestors:
        continue
    try:
        process_identity = identity(candidate)
        if process_identity is None:
            continue
        created_during_job = process_identity not in baseline
        in_job_session = False
        if os.getsid(pid) == job_session:
            in_job_session = True
        if created_during_job or in_job_session:
            observed.append(process_identity)
    except (FileNotFoundError, ProcessLookupError):
        continue
    except (OSError, RuntimeError) as exc:
        raise SystemExit(
            f"job process-set membership is unavailable for pid {pid}: {exc}"
        ) from exc
for pid, starttime in sorted(set(observed)):
    print(pid, starttime)
PY
  then
    scan_rc=0
  else
    scan_rc=$?
  fi
  set +o noclobber
  if [[ "$scan_rc" -ne 0 ]]; then
    printf 'paper-story A-1 job refused: process-set audit unavailable; see %s\n' \
      "$ACCOUNTING_PROCESS_SET_ERROR_PATH" >&2
    return 70
  fi
  survivors=$(<"$ACCOUNTING_PROCESS_SET_SURVIVORS_PATH")
  if [[ -n "$survivors" ]]; then
    printf 'paper-story A-1 job refused: unreaped job processes remain: %s\n' \
      "$survivors" >&2
    return 70
  fi
}

"$PYTHON_BIN" - "$REPO_ROOT" <<'PY' || refuse "Pegasus compute site check failed"
import sys

repo = sys.argv[1]
sys.path.insert(0, repo)
from orchestrator.campaign import site_policy

if site_policy.current_site() != site_policy.PEGASUS_COMPUTE:
    raise SystemExit("not Pegasus compute")
PY

if [[ "$V3_STUDY" -eq 1 ]]; then
  CCBENCH_CANONICAL_PIN=$("$PYTHON_BIN" - \
    "$REPO_ROOT/$POLICY_RELATIVE" "$EXPECTED_STUDY_ID" <<'PY'
import json
import re
import sys

def reject_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value

with open(sys.argv[1], encoding="utf-8") as stream:
    policy = json.load(stream, object_pairs_hook=reject_duplicates)
acceptance = policy.get("ccbench_acceptance")
pin = acceptance.get("canonical_pin") if type(acceptance) is dict else None
if (
    policy.get("schema_version") != "paper-story-a1-paired-policy/v3"
    or policy.get("study_id") != sys.argv[2]
    or type(pin) is not str
    or re.fullmatch(r"[0-9a-f]{40}", pin) is None
):
    raise SystemExit("v3 policy CCBench binding differs")
print(pin)
PY
  ) || refuse "CCBench job-preflight policy binding differs"
  [[ "$CCBENCH_CANONICAL_PIN" == \
    "511c9538e4e8efa54b45cda62e72389ed3b706ec" ]] || \
    refuse "CCBench job-preflight canonical pin differs"
  CCBENCH_ROOT="$REPO_ROOT/external/ccbench"
  CCBENCH_HEAD=$(git -C "$CCBENCH_ROOT" rev-parse HEAD) || \
    refuse "CCBench job-preflight cannot resolve HEAD"
  [[ "$CCBENCH_HEAD" == "$CCBENCH_CANONICAL_PIN" ]] || \
    refuse "CCBench job-preflight canonical HEAD mismatch"
  CCBENCH_TRACKED_STATUS=$(git -C "$CCBENCH_ROOT" status \
    --porcelain --untracked-files=no) || \
    refuse "CCBench job-preflight cannot inspect tracked status"
  [[ -z "$CCBENCH_TRACKED_STATUS" ]] || \
    refuse "CCBench job-preflight tracked files are dirty"
fi

capture_v3_accounting_end() {
  ACCOUNTING_ENDED_EPOCH_S=$(date +%s.%N) || return 70
  ACCOUNTING_ENDED_MONOTONIC_S=$(cut -d' ' -f1 /proc/uptime) || return 70
  set -o noclobber
  if ! LC_ALL=C times >"$ACCOUNTING_TIMES_FINAL_PATH" 2>&1; then
    set +o noclobber
    return 70
  fi
  set +o noclobber
  ACCOUNTING_TIMES_FINAL_RAW=$(<"$ACCOUNTING_TIMES_FINAL_PATH")
}

write_v3_prebench_failure_terminal() {
  local reason=$1
  local job_root="$IZANAGI_A1_ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD"
  local terminal_path="$job_root/job-terminal.json"
  wait
  audit_v3_job_process_set || return 70
  capture_v3_accounting_end || return 70
  IZANAGI_A1_ACCOUNTING_STARTED_EPOCH_S="$ACCOUNTING_STARTED_EPOCH_S" \
  IZANAGI_A1_ACCOUNTING_ENDED_EPOCH_S="$ACCOUNTING_ENDED_EPOCH_S" \
  IZANAGI_A1_ACCOUNTING_STARTED_MONOTONIC_S="$ACCOUNTING_STARTED_MONOTONIC_S" \
  IZANAGI_A1_ACCOUNTING_ENDED_MONOTONIC_S="$ACCOUNTING_ENDED_MONOTONIC_S" \
  IZANAGI_A1_ACCOUNTING_TIMES_BASELINE_RAW="$ACCOUNTING_TIMES_BASELINE_RAW" \
  IZANAGI_A1_ACCOUNTING_TIMES_FINAL_RAW="$ACCOUNTING_TIMES_FINAL_RAW" \
  "$PYTHON_BIN" - "$terminal_path" "$REPO_ROOT" "$POLICY_RELATIVE" \
    "$EXPECTED_STUDY_ID" \
    "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" "$IZANAGI_A1_WORKLOAD" \
    "$IZANAGI_A1_ATTEMPT_ROOT" "$IZANAGI_A1_COMPLETION_RECEIPT" \
    "$PBS_O_HOST" "$PBS_O_WORKDIR" "$reason" <<'PY'
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time

(
    path, repo, policy_relative, study_id, expected_head, pbs_jobid, workload,
    attempt_root, completion_path, pbs_o_host, pbs_o_workdir, reason,
) = sys.argv[1:]
ordinal = ("write-heavy", "balanced", "read-heavy").index(workload)
pattern = re.compile(r"([0-9]+)m([0-9]+(?:\.[0-9]+)?)s")

def values(raw):
    found = pattern.findall(raw)
    if len(found) != 4:
        raise SystemExit("accounting times snapshot shape differs")
    return [float(minutes) * 60.0 + float(seconds) for minutes, seconds in found]

baseline_raw = os.environ["IZANAGI_A1_ACCOUNTING_TIMES_BASELINE_RAW"]
final_raw = os.environ["IZANAGI_A1_ACCOUNTING_TIMES_FINAL_RAW"]
deltas = [
    max(0.0, end - start)
    for start, end in zip(values(baseline_raw), values(final_raw))
]
started_monotonic = float(
    os.environ["IZANAGI_A1_ACCOUNTING_STARTED_MONOTONIC_S"]
)
ended_monotonic = float(os.environ["IZANAGI_A1_ACCOUNTING_ENDED_MONOTONIC_S"])

def git(*args):
    completed = subprocess.run(
        ["git", "-C", repo, *args], text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("terminal git binding failed")
    return completed.stdout.strip()

source_paths = (
    "orchestrator/campaign/paper_story_a1_paired.py",
    policy_relative,
    "orchestrator/campaign/pipeline.py",
    "tools/pegasus/paper_story_a1_paired.sh",
    "orchestrator/calibrator/runner.py",
)
if policy_relative in ("orchestrator/campaign/paper_story_a1_paired.v3-pilot.json",
                       "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"):
    source_paths += (
        "orchestrator/campaign/paper_story_a1_source.v1.json"
        if policy_relative == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
        else "orchestrator/campaign/paper_story_a1_source.v2.json",
        "orchestrator/campaign/paper_story_a1_source.py",
        "patches/silo-backoff-fixed.patch",
        "output/insights/2026-09-11/t2397-a1-source-amendment/README.md"
        if policy_relative == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
        else "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md",
    )
files = {}
for relative in source_paths:
    if not relative:
        continue
    candidate = os.path.join(repo, relative)
    with open(candidate, "rb") as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    files[relative] = {
        "git_blob_oid": git("rev-parse", f"{expected_head}:{relative}"),
        "working_sha256": digest,
    }
attempt_info = os.stat(attempt_root, follow_symlinks=False)
document = {
    "schema_version": "paper-story-a1-paired-workload-job-terminal/v1",
    "study_id": study_id,
    "workload": workload,
    "ordinal": ordinal,
    "pbs_jobid": pbs_jobid,
    "expected_head": expected_head,
    "observed_head": git("rev-parse", "HEAD"),
    "porcelain": git("status", "--ignore-submodules=all", "--porcelain", "--untracked-files=all"),
    "driver_rc": 125,
    "shell_rc": 2,
    "status": "failed",
    "result_sha256": None,
    "receipt_sha256": None,
    "submission_receipt_sha256": None,
    "completion_receipt_path": completion_path,
    "pbs_observation": {
        "pbs_jobid": pbs_jobid,
        "pbs_o_host": pbs_o_host,
        "pbs_o_workdir": pbs_o_workdir,
    },
    "reservation_binding": None,
    "accounting": {
        "method": "bash-times-delta-reaped-descendants/v1",
        "started_epoch_s": float(os.environ["IZANAGI_A1_ACCOUNTING_STARTED_EPOCH_S"]),
        "ended_epoch_s": float(os.environ["IZANAGI_A1_ACCOUNTING_ENDED_EPOCH_S"]),
        "started_monotonic_s": started_monotonic,
        "ended_monotonic_s": ended_monotonic,
        "elapsed_s": ended_monotonic - started_monotonic,
        "shell_user_s": deltas[0],
        "shell_system_s": deltas[1],
        "reaped_descendants_user_s": deltas[2],
        "reaped_descendants_system_s": deltas[3],
        "cpu_total_s": sum(deltas),
        "times_baseline_raw": baseline_raw,
        "times_final_raw": final_raw,
        "unreaped_descendants": [],
    },
    "attempt_identity": {"st_dev": attempt_info.st_dev, "st_ino": attempt_info.st_ino},
    "terminal_source_binding": {
        "measurement_source_commit": expected_head,
        "files": files,
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    },
    "recorded_epoch": int(time.time()),
}
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(path, flags, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

for ((WAITED=0; WAITED<60; WAITED++)); do
  [[ -e "$IZANAGI_A1_ACQUISITION_RECEIPT" ]] && break
  sleep 1
done
if [[ ! -e "$IZANAGI_A1_ACQUISITION_RECEIPT" ]]; then
  if [[ "$V3_STUDY" -eq 1 ]]; then
    write_v3_prebench_failure_terminal "group-submission-receipt-timeout" || \
      refuse "failed to record group receipt timeout terminal"
  fi
  refuse "acquisition receipt did not appear within 60 seconds"
fi

if [[ "$V3_STUDY" -eq 1 ]]; then
  ACQUISITION_SHA=$("$PYTHON_BIN" - \
    "$IZANAGI_A1_ACQUISITION_RECEIPT" "$REPO_ROOT" \
    "$EXPECTED_STUDY_ID" "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" \
    "$IZANAGI_A1_WORKLOAD" "$PBS_O_HOST" "$PBS_O_WORKDIR" <<'PY'
import hashlib
import os
import pathlib
import sys

(
    path_raw, repo_raw, study_id, source_commit, request_id, workload,
    pbs_o_host, pbs_o_workdir,
) = sys.argv[1:]
repo = pathlib.Path(repo_raw).resolve(strict=True)
sys.path.insert(0, os.fspath(repo))
from orchestrator.campaign import paper_story_a1_paired as paired

path = pathlib.Path(path_raw)
raw = paired._read_bytes_once(path)
receipt = paired._decode_json_bytes(raw, "group acquisition receipt")
policy, _ = paired._load_policy_for_study(study_id)
paired.validate_acquisition_receipt(
    receipt,
    repo_root=repo,
    study_id=study_id,
    source_commit=source_commit,
    request_id=request_id,
    pbs_observation={
        "pbs_jobid": request_id,
        "pbs_o_host": pbs_o_host,
        "pbs_o_workdir": pbs_o_workdir,
    },
    policy=policy,
    workload=workload,
)
intent = paired._read_json(paired._attempt_intent_path(pathlib.Path(receipt["attempt_root"])))
expected_source = intent["jobs"][paired.WORKLOAD_ORDER.index(workload)]["qsub_options"]["variables"].get(
    "IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT")
if os.environ.get("IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT") != expected_source:
    raise SystemExit("third-party source root differs from submission intent")
print(hashlib.sha256(raw).hexdigest())
PY
  ) || {
    write_v3_prebench_failure_terminal "group-submission-receipt-invalid" || \
      refuse "failed to record invalid group receipt terminal"
    refuse "group acquisition receipt validation failed"
  }
else
  ACQUISITION_SHA=$("$PYTHON_BIN" - \
  "$IZANAGI_A1_ACQUISITION_RECEIPT" "$REPO_ROOT" "$SUBMISSION_SCHEMA" \
  "$EXPECTED_STUDY_ID" "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" \
  "$IZANAGI_A1_ATTEMPT_ROOT" "$IZANAGI_A1_COMPLETION_RECEIPT" \
  "$POLICY_RELATIVE" "$JOB_RELATIVE" "$PBS_O_HOST" "$PBS_O_WORKDIR" \
  "$EXPECTED_QUEUE" <<'PY'
import hashlib
import json
import os
import pathlib
import re
import stat
import sys

(
    path, repo_raw, schema, study, source, request_id, attempt_raw,
    completion_raw, policy_relative, job_relative, pbs_o_host, pbs_o_workdir,
    expected_queue,
) = sys.argv[1:]
repo = pathlib.Path(repo_raw).resolve(strict=True)
sys.path.insert(0, os.fspath(repo))
from orchestrator.campaign.paper_story_a1_paired import NQSV_QSTAT_STATES

receipt_path = pathlib.Path(path)
if not receipt_path.is_absolute() or receipt_path.resolve(strict=True) != receipt_path:
    raise SystemExit("acquisition receipt path is not canonical absolute")
flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(path, flags)
try:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit("acquisition receipt is not regular")
    raw = b""
    while len(raw) < info.st_size:
        block = os.read(fd, info.st_size - len(raw))
        if not block:
            raise SystemExit("acquisition receipt shortened")
        raw += block
    if os.fstat(fd).st_size != info.st_size:
        raise SystemExit("acquisition receipt changed")
finally:
    os.close(fd)

def reject_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value

request_pattern = re.compile(r"Request\s+(\S+)\s+submitted")
normalized_pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

def normalize_request_id(value):
    if type(value) is not str:
        raise SystemExit("request ID is not a string")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise SystemExit("request ID is empty")
    if normalized_pattern.fullmatch(normalized) is None:
        raise SystemExit("request ID is unsafe")
    return normalized

def parse_request_id(stdout):
    if type(stdout) is not str:
        raise SystemExit("qsub stdout is not a string")
    match = request_pattern.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise SystemExit("qsub stdout does not contain one request ID")

document = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
if type(document) is not dict or set(document) != {
    "schema_version", "route", "study_id", "source_commit",
    "attempt_root", "request_id", "submission_receipt_path",
    "completion_receipt_path", "qsub_argv", "qsub_options",
    "submit_observation",
}:
    raise SystemExit("submission receipt shape differs")
for key, expected in {
    "schema_version": schema,
    "route": "direct-qsub",
    "study_id": study,
    "source_commit": source,
    "attempt_root": attempt_raw,
}.items():
    if document.get(key) != expected:
        raise SystemExit(f"submission receipt identity differs: {key}")
receipt_request_id = document.get("request_id")
if normalize_request_id(receipt_request_id) != normalize_request_id(request_id):
    raise SystemExit("submission receipt request ID differs from PBS_JOBID")
attempt = pathlib.Path(attempt_raw)
if not attempt.is_absolute() or attempt.resolve(strict=False) != attempt:
    raise SystemExit("attempt root is not canonical absolute")
with open(repo / policy_relative, encoding="utf-8") as stream:
    policy = json.load(stream, object_pairs_hook=reject_duplicates)
base_raw = policy.get("execution", {}).get("durable_measurement_base")
if type(base_raw) is not str:
    raise SystemExit("durable measurement base is missing")
base = pathlib.Path(base_raw)
if not base.is_absolute() or base.resolve(strict=False) != base:
    raise SystemExit("durable measurement base is not canonical absolute")
if attempt.parent != base or attempt == base:
    raise SystemExit("attempt root is not one direct durable-base child")
if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", attempt.name) is None:
    raise SystemExit("attempt child name is unsafe")
if os.path.lexists(attempt):
    raise SystemExit("attempt root already exists")
stem = attempt.name
submission = base / f"{stem}.submission.json"
completion = base / f"{stem}.completion.json"
stdout_path = base / f"{stem}.stdout"
stderr_path = base / f"{stem}.stderr"
if receipt_path != submission or pathlib.Path(completion_raw) != completion:
    raise SystemExit("durable receipt topology differs")
variables = {
    "IZANAGI_EXPECTED_HEAD": source,
    "IZANAGI_A1_STUDY_ID": study,
    "IZANAGI_A1_ATTEMPT_ROOT": str(attempt),
    "IZANAGI_A1_ACQUISITION_RECEIPT": str(submission),
    "IZANAGI_A1_COMPLETION_RECEIPT": str(completion),
    "IZANAGI_SUBMISSION_NONCE": attempt.name,
}
variable_text = ",".join(f"{key}={value}" for key, value in variables.items())
options = {
    "v": variable_text,
    "variables": variables,
    "o": str(stdout_path),
    "e": str(stderr_path),
}
argv = [
    "qsub", "-v", variable_text, "-o", str(stdout_path),
    "-e", str(stderr_path), str((repo / job_relative).resolve(strict=True)),
]
if document.get("submission_receipt_path") != str(submission):
    raise SystemExit("submission receipt path differs")
if document.get("completion_receipt_path") != str(completion):
    raise SystemExit("completion receipt path differs")
if document.get("qsub_argv") != argv or document.get("qsub_options") != options:
    raise SystemExit("canonical qsub request differs")
observation = document.get("submit_observation")
if type(observation) is not dict or set(observation) != {
    "submit_host", "qsub_stdout", "qsub_stdout_sha256", "qsub_stderr",
    "qsub_stderr_sha256", "qstat_visibility",
}:
    raise SystemExit("submit observation shape differs")
if (
    type(observation["submit_host"]) is not str
    or not observation["submit_host"]
    or any(ord(character) < 0x20 for character in observation["submit_host"])
):
    raise SystemExit("submit host observation differs")
if observation["submit_host"] != pbs_o_host:
    raise SystemExit("submit host does not match PBS_O_HOST")
if pbs_o_workdir != str(repo):
    raise SystemExit("PBS_O_WORKDIR does not match repository")
qsub_stdout = observation["qsub_stdout"]
if observation["qsub_stderr"] != "":
    raise SystemExit("qsub stdout/stderr observation differs")
if normalize_request_id(parse_request_id(qsub_stdout)) != normalize_request_id(
    receipt_request_id
):
    raise SystemExit("qsub stdout request ID differs")
if observation["qsub_stdout_sha256"] != hashlib.sha256(qsub_stdout.encode()).hexdigest():
    raise SystemExit("qsub stdout hash differs")
if observation["qsub_stderr_sha256"] != hashlib.sha256(b"").hexdigest():
    raise SystemExit("qsub stderr hash differs")
visibility = observation["qstat_visibility"]
if type(visibility) is not dict or set(visibility) != {
    "request_id", "visible", "state", "queue", "observed_epoch",
}:
    raise SystemExit("qstat visibility shape differs")
if (
    visibility["visible"] is not True
    or type(visibility["state"]) is not str
    or visibility["state"] not in NQSV_QSTAT_STATES
    or visibility["queue"] != expected_queue
    or type(visibility["observed_epoch"]) is not int
    or visibility["observed_epoch"] <= 0
):
    raise SystemExit("qstat visibility observation differs")
if normalize_request_id(visibility["request_id"]) != normalize_request_id(
    receipt_request_id
):
    raise SystemExit("qstat visibility request ID differs")
print(hashlib.sha256(raw).hexdigest())
PY
  ) || refuse "acquisition receipt validation failed"
fi
[[ "$ACQUISITION_SHA" =~ ^[0-9a-f]{64}$ ]] || refuse "acquisition receipt SHA is invalid"

ATTEMPT_ROOT="$IZANAGI_A1_ATTEMPT_ROOT"
if [[ "$V3_STUDY" -eq 1 ]]; then
  JOB_ROOT="$ATTEMPT_ROOT/jobs/$IZANAGI_A1_WORKLOAD"
  RAW_ROOT="$JOB_ROOT/raw"
  CACHE_ROOT="$JOB_ROOT/cache"
else
  JOB_ROOT="$ATTEMPT_ROOT"
  RAW_ROOT="$ATTEMPT_ROOT/raw"
  CACHE_ROOT="$ATTEMPT_ROOT/cache"
fi
MEASURE_WORKLOAD_ARGS=()
if [[ "$V3_STUDY" -eq 1 ]]; then
  MEASURE_WORKLOAD_ARGS=(--workload "$IZANAGI_A1_WORKLOAD")
fi
OUTPUT_ROOT="$RAW_ROOT/campaign-output"
RESULT_ROOT="$RAW_ROOT/results"
TMP_ROOT="$RAW_ROOT/tmp"
if [[ "$V3_STUDY" -eq 0 ]]; then
  if ! mkdir -- "$ATTEMPT_ROOT"; then
    refuse "attempt root cannot be exclusive-created"
  fi
else
  [[ -d "$ATTEMPT_ROOT" && ! -L "$ATTEMPT_ROOT" ]] || \
    refuse "group attempt root is unavailable"
  [[ -d "$JOB_ROOT" && ! -L "$JOB_ROOT" ]] || \
    refuse "workload job root is unavailable"
fi
if ! mkdir -- "$RAW_ROOT"; then
  refuse "raw root cannot be exclusive-created"
fi
if ! mkdir -- "$TMP_ROOT"; then
  refuse "temporary root cannot be exclusive-created"
fi
export TMPDIR="$TMP_ROOT"
export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"

readarray -t REQUESTED_WALLTIMES < <(
  sed -n -E \
    's/^#PBS[[:space:]]+-l[[:space:]]+elapstim_req=([0-9]{2}:[0-9]{2}:[0-9]{2})[[:space:]]*$/\1/p' \
    "$REPO_ROOT/$JOB_RELATIVE"
)
[[ ${#REQUESTED_WALLTIMES[@]} -eq 1 ]] || \
  refuse "job body must declare exactly one HH:MM:SS elapstim_req"
IFS=: read -r REQUESTED_HOURS REQUESTED_MINUTES REQUESTED_SECONDS \
  <<< "${REQUESTED_WALLTIMES[0]}"
((10#$REQUESTED_MINUTES < 60 && 10#$REQUESTED_SECONDS < 60)) || \
  refuse "job body elapstim_req minute/second is invalid"
REQUESTED_S=$((
  10#$REQUESTED_HOURS * 3600
  + 10#$REQUESTED_MINUTES * 60
  + 10#$REQUESTED_SECONDS
))
((REQUESTED_S > 0)) || refuse "job body elapstim_req must be positive"

qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$RAW_ROOT/qstat-f.stdout" \
  2>"$RAW_ROOT/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$RAW_ROOT/qstat-f.rc"
HOSTNAME_SHORT=$(hostname) || refuse "cannot observe hostname"
HOSTNAME_FQDN=$(hostname -f) || refuse "cannot observe hostname -f"
readarray -t qstat_values < <("$PYTHON_BIN" - \
  "$RAW_ROOT/qstat-f.stdout" "$HOSTNAME_SHORT" "$qstat_rc" <<'PY'
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
        parsed = subprocess.run(
            ["date", "-d", raw, "+%s"], capture_output=True, text=True
        )
        if parsed.returncode == 0 and parsed.stdout.strip().isdigit():
            started = parsed.stdout.strip()
            break
print(assigned)
print(started)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable \
      || "$SCHEDULER_STARTED_EPOCH" == unavailable ]]; then
  refuse "qstat allocation/start binding unavailable"
fi
if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]; then
  RESERVATION_HOST="$HOSTNAME_SHORT"
elif [[ "$ASSIGNED_HOST" == "$HOSTNAME_FQDN" ]]; then
  RESERVATION_HOST="$HOSTNAME_FQDN"
else
  refuse "qstat assigned host has no exact hostname/hostname-f observation"
fi
BOOT_ID=$(< /proc/sys/kernel/random/boot_id) || refuse "cannot read boot ID"
[[ -n "$BOOT_ID" ]] || refuse "boot ID is empty"
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$RESERVATION_HOST"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$CURRENT_SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"

DRIVER_RC=125
if [[ "$V3_STUDY" -eq 1 ]]; then
  TERMINAL_PATH="$JOB_ROOT/job-terminal.json"
  case "$IZANAGI_A1_WORKLOAD" in
    write-heavy) WORKLOAD_ORDINAL=0 ;;
    balanced) WORKLOAD_ORDINAL=1 ;;
    read-heavy) WORKLOAD_ORDINAL=2 ;;
  esac
else
  TERMINAL_PATH="$RAW_ROOT/job-terminal.json"
  WORKLOAD_ORDINAL=-1
fi
DEPENDENCY_ROOT=""
DEPENDENCY_ROOT_OWNED=0

write_terminal() {
  local shell_rc=$1
  [[ ! -e "$TERMINAL_PATH" ]] || return 66
  IZANAGI_A1_TERMINAL_DRIVER_RELATIVE="$DRIVER_RELATIVE" \
  IZANAGI_A1_TERMINAL_POLICY_RELATIVE="$POLICY_RELATIVE" \
  IZANAGI_A1_TERMINAL_PIPELINE_RELATIVE="$PIPELINE_RELATIVE" \
  IZANAGI_A1_TERMINAL_JOB_RELATIVE="$JOB_RELATIVE" \
  IZANAGI_A1_TERMINAL_RUNNER_RELATIVE="orchestrator/calibrator/runner.py" \
  IZANAGI_A1_ACCOUNTING_STARTED_EPOCH_S="$ACCOUNTING_STARTED_EPOCH_S" \
  IZANAGI_A1_ACCOUNTING_ENDED_EPOCH_S="$ACCOUNTING_ENDED_EPOCH_S" \
  IZANAGI_A1_ACCOUNTING_STARTED_MONOTONIC_S="$ACCOUNTING_STARTED_MONOTONIC_S" \
  IZANAGI_A1_ACCOUNTING_ENDED_MONOTONIC_S="$ACCOUNTING_ENDED_MONOTONIC_S" \
  IZANAGI_A1_ACCOUNTING_TIMES_BASELINE_RAW="$ACCOUNTING_TIMES_BASELINE_RAW" \
  IZANAGI_A1_ACCOUNTING_TIMES_FINAL_RAW="$ACCOUNTING_TIMES_FINAL_RAW" \
  "$PYTHON_BIN" - "$TERMINAL_PATH" "$REPO_ROOT" "$EXPECTED_STUDY_ID" \
  "$V3_STUDY" "$PBS_JOBID" "$IZANAGI_EXPECTED_HEAD" "$DRIVER_RC" "$shell_rc" \
    "$RESULT_ROOT" "$IZANAGI_A1_ACQUISITION_RECEIPT" "$ACQUISITION_SHA" \
    "$IZANAGI_A1_COMPLETION_RECEIPT" "$ATTEMPT_ROOT" \
    "$PBS_O_HOST" "$PBS_O_WORKDIR" "${IZANAGI_A1_WORKLOAD:-}" \
    "$WORKLOAD_ORDINAL" <<'PY'
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time

(
    path, repo, study_id, v3_study_raw, pbs_jobid, expected_head, driver_rc_raw,
    shell_rc_raw, result_root, acquisition_path, acquisition_sha,
    completion_path, attempt_root, pbs_o_host, pbs_o_workdir, workload,
    workload_ordinal_raw,
) = sys.argv[1:]
if v3_study_raw not in {"0", "1"}:
    raise SystemExit("terminal v3 selector differs")
v3_study = v3_study_raw == "1"
source_paths = [
    os.environ[key]
    for key in (
        "IZANAGI_A1_TERMINAL_DRIVER_RELATIVE",
        "IZANAGI_A1_TERMINAL_POLICY_RELATIVE",
        "IZANAGI_A1_TERMINAL_PIPELINE_RELATIVE",
        "IZANAGI_A1_TERMINAL_JOB_RELATIVE",
    )
]
if v3_study:
    source_paths.append(os.environ["IZANAGI_A1_TERMINAL_RUNNER_RELATIVE"])
if os.environ["IZANAGI_A1_TERMINAL_POLICY_RELATIVE"] in (
        "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json",
        "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"):
    source_paths.extend([
        "orchestrator/campaign/paper_story_a1_source.v1.json"
        if os.environ["IZANAGI_A1_TERMINAL_POLICY_RELATIVE"] == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
        else "orchestrator/campaign/paper_story_a1_source.v2.json",
        "orchestrator/campaign/paper_story_a1_source.py",
        "patches/silo-backoff-fixed.patch",
        "output/insights/2026-09-11/t2397-a1-source-amendment/README.md"
        if os.environ["IZANAGI_A1_TERMINAL_POLICY_RELATIVE"] == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
        else "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md",
    ])
source_paths = tuple(source_paths)
driver_rc = int(driver_rc_raw)
shell_rc = int(shell_rc_raw)
workload_ordinal = int(workload_ordinal_raw)

def digest(candidate):
    if not os.path.isfile(candidate):
        return None
    value = hashlib.sha256()
    with open(candidate, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def git(*args):
    proc = subprocess.run(
        ["git", "-C", repo, *args], text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise SystemExit(f"terminal git check failed: {' '.join(args)}")
    return proc.stdout.strip()

observed_head = git("rev-parse", "HEAD")
status_args = ["status"]
if v3_study:
    status_args.append("--ignore-submodules=all")
status_args.extend(("--porcelain", "--untracked-files=all"))
porcelain = git(*status_args)
files = {}
for relative in source_paths:
    files[relative] = {
        "git_blob_oid": git("rev-parse", f"{expected_head}:{relative}"),
        "working_sha256": digest(os.path.join(repo, relative)),
    }
source_binding = {
    "measurement_source_commit": expected_head,
    "files": files,
    "evidence_level": "source-routed-trace0",
    "artifact_standalone_proof": False,
}
reservation_keys = (
    "JOB_ID",
    "REQUESTED_S",
    "SCHEDULER_STARTED_EPOCH",
    "DEADLINE_EPOCH",
    "HOST",
    "BOOT_ID",
    "SCRIPT_SHA256",
    "NONCE",
)
reservation_binding = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key]
    for key in reservation_keys
}
reservation_binding["requested_s"] = int(reservation_binding["requested_s"])
for key in ("scheduler_started_epoch", "deadline_epoch"):
    reservation_binding[key] = float(reservation_binding[key])
result_path = os.path.join(result_root, "result.json")
receipt_path = os.path.join(result_root, "receipt.json")
result_sha = digest(result_path)
receipt_sha = digest(receipt_path)
terminal_acquisition_sha = digest(acquisition_path)
attempt_info = os.stat(attempt_root, follow_symlinks=False)
if not stat.S_ISDIR(attempt_info.st_mode):
    raise SystemExit("terminal attempt root is not a real directory")
source_ok = observed_head == expected_head and porcelain == ""
success_inputs = [
    driver_rc == 0,
    shell_rc == 0,
    result_sha is not None,
    receipt_sha is not None,
    terminal_acquisition_sha == acquisition_sha,
    source_ok,
]
if not v3_study:
    success_inputs.append(
        digest(os.path.join(result_root, "non-certifying-observation.json"))
        is not None
    )
success = all(success_inputs)
accounting = None
if v3_study:
    duration_pattern = re.compile(r"([0-9]+)m([0-9]+(?:\.[0-9]+)?)s")

    def times_values(raw):
        matches = duration_pattern.findall(raw)
        if len(matches) != 4:
            raise SystemExit("accounting times snapshot shape differs")
        return [float(minutes) * 60.0 + float(seconds) for minutes, seconds in matches]

    baseline_raw = os.environ["IZANAGI_A1_ACCOUNTING_TIMES_BASELINE_RAW"]
    final_raw = os.environ["IZANAGI_A1_ACCOUNTING_TIMES_FINAL_RAW"]
    baseline = times_values(baseline_raw)
    final = times_values(final_raw)
    deltas = [end - start for start, end in zip(baseline, final)]
    if any(value < -1e-9 for value in deltas):
        raise SystemExit("accounting times delta is negative")
    deltas = [max(0.0, value) for value in deltas]
    started_epoch = float(os.environ["IZANAGI_A1_ACCOUNTING_STARTED_EPOCH_S"])
    ended_epoch = float(os.environ["IZANAGI_A1_ACCOUNTING_ENDED_EPOCH_S"])
    started_monotonic = float(
        os.environ["IZANAGI_A1_ACCOUNTING_STARTED_MONOTONIC_S"]
    )
    ended_monotonic = float(
        os.environ["IZANAGI_A1_ACCOUNTING_ENDED_MONOTONIC_S"]
    )
    accounting = {
        "method": "bash-times-delta-reaped-descendants/v1",
        "started_epoch_s": started_epoch,
        "ended_epoch_s": ended_epoch,
        "started_monotonic_s": started_monotonic,
        "ended_monotonic_s": ended_monotonic,
        "elapsed_s": ended_monotonic - started_monotonic,
        "shell_user_s": deltas[0],
        "shell_system_s": deltas[1],
        "reaped_descendants_user_s": deltas[2],
        "reaped_descendants_system_s": deltas[3],
        "cpu_total_s": sum(deltas),
        "times_baseline_raw": baseline_raw,
        "times_final_raw": final_raw,
        "unreaped_descendants": [],
    }
document = {
    "schema_version": (
        "paper-story-a1-paired-workload-job-terminal/v1"
        if v3_study else "paper-story-a1-paired-job-terminal/v3"
    ),
    "study_id": study_id,
    "pbs_jobid": pbs_jobid,
    "expected_head": expected_head,
    "observed_head": observed_head,
    "porcelain": porcelain,
    "driver_rc": driver_rc,
    "shell_rc": shell_rc,
    "status": "finished" if success else "failed",
    "result_sha256": result_sha,
    "receipt_sha256": receipt_sha,
    "submission_receipt_sha256": terminal_acquisition_sha,
    "completion_receipt_path": completion_path,
    "pbs_observation": {
        "pbs_jobid": pbs_jobid,
        "pbs_o_host": pbs_o_host,
        "pbs_o_workdir": pbs_o_workdir,
    },
    "reservation_binding": reservation_binding,
    "attempt_identity": {
        "st_dev": attempt_info.st_dev,
        "st_ino": attempt_info.st_ino,
    },
    "terminal_source_binding": source_binding,
    "recorded_epoch": int(time.time()),
}
if v3_study:
    if workload not in {"write-heavy", "balanced", "read-heavy"}:
        raise SystemExit("terminal workload differs")
    document["workload"] = workload
    document["ordinal"] = workload_ordinal
    document["accounting"] = accounting
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(path, flags, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
raise SystemExit(0 if success or driver_rc != 0 or shell_rc != 0 else 3)
PY
}

cleanup_dependency_root() {
  if [[ "$DEPENDENCY_ROOT_OWNED" -eq 1 ]]; then
    [[ -n "$DEPENDENCY_ROOT" ]] || return 70
    /bin/rm -rf -- "$DEPENDENCY_ROOT"
  fi
}

on_exit() {
  local shell_rc=$?
  local cleanup_rc
  local writer_rc
  trap - EXIT
  set +e
  cleanup_dependency_root
  cleanup_rc=$?
  if [[ "$cleanup_rc" -ne 0 ]]; then
    shell_rc=70
  fi
  if [[ "$V3_STUDY" -eq 1 ]]; then
    wait
    audit_v3_job_process_set || exit 70
    capture_v3_accounting_end || exit 70
  fi
  write_terminal "$shell_rc"
  writer_rc=$?
  set -e
  if [[ "$writer_rc" -ne 0 ]]; then
    exit 70
  fi
  exit "$shell_rc"
}
trap on_exit EXIT

# The dependency build is disposable node-local staging. The attempt root and
# all evidence remain in the durable base validated above.
DEPENDENCY_EVIDENCE_ROOT="$RAW_ROOT/dependency-staging"
if ! mkdir -- "$DEPENDENCY_EVIDENCE_ROOT"; then
  refuse "dependency evidence root cannot be exclusive-created"
fi
readarray -t DEPENDENCY_POLICY_VALUES < <(
  "$PYTHON_BIN" - "$REPO_ROOT/$PEGASUS_POLICY_RELATIVE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    policy = json.load(stream)
for key in (
    "gflags_expected_head",
    "glog_expected_head",
):
    value = policy[key]
    if type(value) is not str or not value:
        raise SystemExit(f"Pegasus dependency pin is invalid: {key}")
    print(value)
PY
)
[[ ${#DEPENDENCY_POLICY_VALUES[@]} -eq 2 ]] || \
  refuse "Pegasus dependency pins are incomplete"
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=${DEPENDENCY_POLICY_VALUES[0]}
GLOG_EXPECTED_HEAD=${DEPENDENCY_POLICY_VALUES[1]}
[[ "$GFLAGS_SOURCE_PATH" = /* && "$GLOG_SOURCE_PATH" = /* ]] || \
  refuse "dependency source paths must be absolute"
[[ "$GFLAGS_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  refuse "gflags expected HEAD is invalid"
[[ "$GLOG_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  refuse "glog expected HEAD is invalid"

if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  refuse "gflags source path is missing"
fi
gflags_head_rc=0
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-head.stderr") || gflags_head_rc=$?
if [[ "$gflags_head_rc" -ne 0 ]]; then
  refuse "cannot resolve gflags source HEAD"
fi
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  refuse "gflags source HEAD mismatch"
fi
gflags_status_rc=0
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-status.stderr") || gflags_status_rc=$?
if [[ "$gflags_status_rc" -ne 0 ]]; then
  refuse "cannot inspect gflags working tree"
fi
printf '%s' "$GFLAGS_STATUS" >"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  refuse "gflags working tree is dirty"
fi

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  refuse "glog source path is missing"
fi
glog_head_rc=0
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-source-head.stderr") || glog_head_rc=$?
if [[ "$glog_head_rc" -ne 0 ]]; then
  refuse "cannot resolve glog source HEAD"
fi
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$DEPENDENCY_EVIDENCE_ROOT/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  refuse "glog source HEAD mismatch"
fi
glog_status_rc=0
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-source-status.stderr") || glog_status_rc=$?
if [[ "$glog_status_rc" -ne 0 ]]; then
  refuse "cannot inspect glog working tree"
fi
printf '%s' "$GLOG_STATUS" >"$DEPENDENCY_EVIDENCE_ROOT/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  refuse "glog working tree is dirty"
fi

[[ -n "$DEPENDENCY_SCRATCH_PARENT" ]] || \
  refuse "dependency scratch parent is unavailable"
[[ "$DEPENDENCY_SCRATCH_PARENT" = /* ]] || \
  refuse "dependency scratch parent must be absolute"
[[ -d "$DEPENDENCY_SCRATCH_PARENT" ]] || \
  refuse "dependency scratch parent is unavailable"
if ! DEPENDENCY_ROOT=$(mktemp -d -- \
  "$DEPENDENCY_SCRATCH_PARENT/${PBS_JOBID//:/_}.${IZANAGI_SUBMISSION_NONCE}.XXXXXXXX"); then
  refuse "dependency scratch root cannot be exclusive-created"
fi
DEPENDENCY_ROOT_OWNED=1
readonly DEPENDENCY_ROOT DEPENDENCY_ROOT_OWNED
CC_PATH=$(command -v gcc) || refuse "gcc is unavailable"
CXX_PATH=$(command -v g++) || refuse "g++ is unavailable"
command -v cmake >/dev/null 2>&1 || refuse "cmake is unavailable"

GFLAGS_BUILD_DIR="$DEPENDENCY_ROOT/gflags-build"
GFLAGS_INSTALL_DIR="$DEPENDENCY_ROOT/gflags-install"
if ! mkdir -- "$GFLAGS_BUILD_DIR"; then
  refuse "cannot create gflags build directory"
fi
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
gflags_rc=0
timeout 60 "${gflags_configure_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-configure.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-configure.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags configure failed"
fi
timeout 60 "${gflags_build_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-build.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-build.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags build failed"
fi
timeout 60 "${gflags_install_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-install.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-install.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags install failed"
fi

GLOG_BUILD_DIR="$DEPENDENCY_ROOT/glog-build"
GLOG_INSTALL_DIR="$DEPENDENCY_ROOT/glog-install"
if ! mkdir -- "$GLOG_BUILD_DIR"; then
  refuse "cannot create glog build directory"
fi
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
glog_rc=0
timeout 120 "${glog_configure_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-configure.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-configure.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog configure failed"
fi
timeout 120 "${glog_build_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-build.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-build.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog build failed"
fi
timeout 120 "${glog_install_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-install.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-install.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog install failed"
fi
DEPENDENCY_PREFIX="$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"

THIRD_PARTY_ARGS=()
if [[ "$POLICY_RELATIVE" == "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json" ||
      "$POLICY_RELATIVE" == "orchestrator/campaign/paper_story_a1_paired.v3-sized.json" ]]; then
  THIRD_PARTY_SOURCE=${IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT:?hydrated source root required}
  [[ "$THIRD_PARTY_SOURCE" = /* && ! -L "$THIRD_PARTY_SOURCE" ]] || refuse "unsafe third-party source root"
  THIRD_PARTY_ROOT="$DEPENDENCY_ROOT/fetchcontent"
  mkdir -- "$THIRD_PARTY_ROOT"
  for name in masstree mimalloc googletest; do
    [[ -d "$THIRD_PARTY_SOURCE/$name" && ! -L "$THIRD_PARTY_SOURCE/$name" ]] || refuse "missing hydrated source"
    cp -a "$THIRD_PARTY_SOURCE/$name" "$THIRD_PARTY_ROOT/$name-src"
  done
  THIRD_PARTY_ARGS=(--third-party-source-root "$THIRD_PARTY_ROOT")
fi

set +e
"$PYTHON_BIN" "$REPO_ROOT/$DRIVER_RELATIVE" measure \
  --study-id "$EXPECTED_STUDY_ID" \
  --expected-head "$IZANAGI_EXPECTED_HEAD" \
  --pbs-jobid "$PBS_JOBID" \
  --acquisition-receipt "$IZANAGI_A1_ACQUISITION_RECEIPT" \
  --acquisition-receipt-sha256 "$ACQUISITION_SHA" \
  --output-root "$OUTPUT_ROOT" \
  --cache-root "$CACHE_ROOT" \
  --result-root "$RESULT_ROOT" \
  --dependency-prefix "$DEPENDENCY_PREFIX" \
  "${THIRD_PARTY_ARGS[@]}" \
  "${MEASURE_WORKLOAD_ARGS[@]}"
DRIVER_RC=$?
set -e
exit "$DRIVER_RC"
