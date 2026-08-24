#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=06:00:00
#PBS -N paper-a2-cert
set -euo pipefail

required_env=(
  PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR
  IZANAGI_A2_REPO_ROOT IZANAGI_A2_EXPECTED_HEAD IZANAGI_A2_CURRENT_PIN
  IZANAGI_A2_CCBENCH_ROOT IZANAGI_A2_ATTEMPT_ROOT
  IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE
)
for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "missing required environment: $name" >&2
    exit 2
  fi
done

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
  echo "paper-story A-2 job body is compute-only" >&2
  exit 2
fi

repo=$IZANAGI_A2_REPO_ROOT
attempt=$IZANAGI_A2_ATTEMPT_ROOT
raw_root=$attempt/raw
dependency_source=$IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE
ccbench_root=$IZANAGI_A2_CCBENCH_ROOT
if [[ ! -d "$repo" || -L "$repo" || ! -d "$attempt" || -L "$attempt" ]]; then
  echo "repo or durable attempt root is unavailable" >&2
  exit 2
fi
result=$attempt/compute-result.json
if [[ -e "$result" || -L "$result" ]]; then
  echo "compute result already exists" >&2
  exit 2
fi
finish() {
  rc=$?
  trap - EXIT
  tmp=$attempt/.compute-result.${PBS_JOBID}.tmp
  printf '{"schema_version":"paper-story-a2-compute-result/v1","driver_rc":%s,"pbs_jobid":"%s","current_pin":"%s"}\n' \
    "$rc" "$PBS_JOBID" "$IZANAGI_A2_CURRENT_PIN" >"$tmp"
  sync "$tmp"
  if ! ln "$tmp" "$result"; then
    rm "$tmp"
    exit 2
  fi
  rm "$tmp"
  sync "$attempt"
  exit "$rc"
}
trap finish EXIT

if [[ ! -d "$dependency_source" || -L "$dependency_source" ]]; then
  echo "pinned dependency source is unavailable" >&2
  exit 2
fi

qstat_jobid=${PBS_JOBID#0:}
allocation_qstat_stdout=$attempt/scheduler/allocation-qstat.stdout
allocation_qstat_stderr=$attempt/scheduler/allocation-qstat.stderr
if [[ -e "$allocation_qstat_stdout" || -L "$allocation_qstat_stdout" \
   || -e "$allocation_qstat_stderr" || -L "$allocation_qstat_stderr" ]]; then
  echo "allocation qstat evidence is not fresh" >&2
  exit 2
fi
qstat -f "$qstat_jobid" >"$allocation_qstat_stdout" 2>"$allocation_qstat_stderr"
sync "$allocation_qstat_stdout" "$allocation_qstat_stderr"
readarray -t reservation_observation < <(
  python3 - "$allocation_qstat_stdout" <<'PY'
import re
import subprocess
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
limits = re.findall(
    r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S",
    text,
)
started = None
for key in ("Started Request Time", "stime", "start_time", "start"):
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
    if match is None:
        continue
    raw = match.group(1).strip()
    if raw.isdigit() and int(raw) > 1_000_000_000:
        started = raw
        break
    parsed = subprocess.run(
        ["date", "-d", raw, "+%s"], capture_output=True, text=True)
    if parsed.returncode == 0 and parsed.stdout.strip().isdigit():
        started = parsed.stdout.strip()
        break
if len(limits) != 1 or started is None:
    raise SystemExit(2)
print(started)
print(limits[0])
PY
)
if [[ ${#reservation_observation[@]} -ne 2 ]]; then
  echo "scheduler reservation observation is incomplete" >&2
  exit 2
fi
scheduler_started_epoch=${reservation_observation[0]}
requested_s=${reservation_observation[1]}
deadline_epoch=$((scheduler_started_epoch + requested_s))
boot_id=$(tr -d '\n' </proc/sys/kernel/random/boot_id)
job_body=$repo/tools/pegasus/paper_story_a2_certification.sh
if [[ ! -f "$job_body" || -L "$job_body" || -z "$boot_id" ]]; then
  echo "reservation observation inputs are unavailable" >&2
  exit 2
fi
script_sha256=$(sha256sum -- "$job_body")
script_sha256=${script_sha256%% *}
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$requested_s"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$scheduler_started_epoch"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"
export IZANAGI_RESERVATION_HOST="$host"
export IZANAGI_RESERVATION_BOOT_ID="$boot_id"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$script_sha256"
export IZANAGI_RESERVATION_NONCE="$PBS_JOBID"
reservation_result=$attempt/reservation.json
if [[ -e "$reservation_result" || -L "$reservation_result" ]]; then
  echo "reservation result is not fresh" >&2
  exit 2
fi
python3 - "$reservation_result" "$allocation_qstat_stdout" \
  "$allocation_qstat_stderr" <<'PY'
import hashlib
import json
import os
import sys

destination, stdout_path, stderr_path = sys.argv[1:]
keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
environment = {
    "IZANAGI_RESERVATION_" + key: os.environ["IZANAGI_RESERVATION_" + key]
    for key in keys
}
def file_record(path):
    with open(path, "rb") as source:
        payload = source.read()
    return {
        "path": path,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
record = {
    "schema_version": "paper-story-a2-reservation-result/v1",
    "environment": environment,
    "allocation_qstat_stdout": file_record(stdout_path),
    "allocation_qstat_stderr": file_record(stderr_path),
}
with open(destination, "x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
sync "$attempt"

cd "$repo"
observed_head=$(git rev-parse HEAD)
if [[ "$observed_head" != "$IZANAGI_A2_EXPECTED_HEAD" ]]; then
  echo "expected HEAD mismatch" >&2
  exit 2
fi
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "tracked worktree is not clean" >&2
  exit 2
fi
if [[ ! -d "$ccbench_root" || -L "$ccbench_root" ]]; then
  echo "CCBench source root is unavailable" >&2
  exit 2
fi
if [[ "$(git -C "$ccbench_root" rev-parse HEAD)" != "$IZANAGI_A2_CURRENT_PIN" ]]; then
  echo "CCBench current pin mismatch" >&2
  exit 2
fi
if [[ -n "$(git -C "$ccbench_root" status --porcelain --untracked-files=no)" ]]; then
  echo "CCBench source tree is not clean" >&2
  exit 2
fi
if [[ -e "$raw_root" || -L "$raw_root" ]]; then
  echo "raw result root is not fresh" >&2
  exit 2
fi

scratch_base=/scr/${USER}/paper-story-a2-certification
scratch=$scratch_base/${PBS_JOBID}
dependency_prefix=$scratch/dependencies
if [[ -e "$scratch" || -L "$scratch" ]]; then
  echo "scratch root is not fresh" >&2
  exit 2
fi
mkdir -p "$scratch_base"
mkdir "$scratch"
mkdir "$dependency_prefix"
cp -a "$dependency_source"/. "$dependency_prefix"/

export PYTHONDONTWRITEBYTECODE=1
python3 -m orchestrator.campaign.paper_story_a2_certification \
  compute-preflight \
  --attempt-root "$attempt" \
  --raw-root "$raw_root" \
  --expected-head "$IZANAGI_A2_EXPECTED_HEAD" \
  --repo-root "$repo" \
  --dependency-prefix "$dependency_prefix"

python3 -m orchestrator.campaign.paper_story_a2_certification \
  run-workload \
  --workload rr5 \
  --attempt-root "$attempt" \
  --raw-root "$raw_root" \
  --current-pin "$IZANAGI_A2_CURRENT_PIN" \
  --dependency-prefix "$dependency_prefix" \
  --ccbench-dir "$ccbench_root"

python3 -m orchestrator.campaign.paper_story_a2_certification \
  run-workload \
  --workload rr50 \
  --attempt-root "$attempt" \
  --raw-root "$raw_root" \
  --current-pin "$IZANAGI_A2_CURRENT_PIN" \
  --dependency-prefix "$dependency_prefix" \
  --ccbench-dir "$ccbench_root"

python3 -m orchestrator.campaign.paper_story_a2_certification \
  finalize-raw \
  --attempt-root "$attempt" \
  --current-pin "$IZANAGI_A2_CURRENT_PIN"
