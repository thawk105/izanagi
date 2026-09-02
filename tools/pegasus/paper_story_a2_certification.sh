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
  IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE IZANAGI_A2_WORKLOAD
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
workload=$IZANAGI_A2_WORKLOAD
job_root=$attempt/jobs/$workload
raw_root=$job_root/raw
campaign_root=$job_root/campaigns
cache_root=$job_root/cache
scheduler_root=$job_root/scheduler
dependency_source=$IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE
ccbench_root=$IZANAGI_A2_CCBENCH_ROOT
if [[ ! -d "$repo" || -L "$repo" || ! -d "$attempt" || -L "$attempt" \
   || ! -d "$job_root" || -L "$job_root" \
   || ! -d "$campaign_root" || -L "$campaign_root" \
   || ! -d "$cache_root" || -L "$cache_root" \
   || ! -d "$scheduler_root" || -L "$scheduler_root" ]]; then
  echo "repo or durable workload job root is unavailable" >&2
  exit 2
fi
result=$job_root/compute-result.json
if [[ -e "$result" || -L "$result" ]]; then
  echo "compute result already exists" >&2
  exit 2
fi
pbs_jobid_path_component=${PBS_JOBID//:/_}
finish() {
  rc=$?
  trap - EXIT
  tmp=$job_root/.compute-result.${pbs_jobid_path_component}.tmp
  printf '{"schema_version":"paper-story-a2-compute-result/v2","workload":"%s","driver_rc":%s,"pbs_jobid":"%s","current_pin":"%s"}\n' \
    "$workload" "$rc" "$PBS_JOBID" "$IZANAGI_A2_CURRENT_PIN" >"$tmp"
  sync "$tmp"
  if ! ln "$tmp" "$result"; then
    rm "$tmp"
    exit 2
  fi
  rm "$tmp"
  sync "$job_root"
  exit "$rc"
}
trap finish EXIT

resolve_python() {
  local candidate resolved selected=""
  for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && (
      cd "$repo" &&
      "$resolved" -B -c \
        'import sys; sys.version_info >= (3, 10) or sys.exit(1); import orchestrator.campaign.paper_story_a2_certification' \
        >/dev/null 2>&1
    ); then
      selected=$resolved
      break
    fi
  done
  if [[ -z "$selected" ]]; then
    echo "no Python 3.10+ interpreter can import the A-2 driver" >&2
    return 2
  fi
  PY=$selected
  export PATH="$(dirname "$selected"):$PATH"
}
resolve_python || exit 2
POLICY_SELECTION=${IZANAGI_A2_POLICY_PATH:-}
readarray -t POLICY_VALUES < <(
  cd "$repo"
  "$PY" -B - "$POLICY_SELECTION" "$workload" <<'PY'
import sys
from orchestrator.campaign import paper_story_a2_certification as a2

selected, workload = sys.argv[1:]
policy = (a2.load_policy(a2.canonical_policy_path(selected))
          if selected else a2.load_policy())
if a2.workload_ids(policy).count(workload) != 1:
    raise SystemExit("IZANAGI_A2_WORKLOAD is not an exact selected-policy member")
print(policy.path)
print(policy.document["scheduler"]["job_body"])
PY
)
[[ ${#POLICY_VALUES[@]} -eq 2 ]] || {
  echo "selected policy or workload is invalid" >&2
  exit 2
}
POLICY_PATH=${POLICY_VALUES[0]}
JOB_BODY_RELATIVE=${POLICY_VALUES[1]}
POLICY_ARGS=()
if [[ -n "$POLICY_SELECTION" ]]; then
  POLICY_ARGS=(--policy "$POLICY_PATH")
fi

if [[ ! -d "$dependency_source" || -L "$dependency_source" ]]; then
  echo "pinned dependency source is unavailable" >&2
  exit 2
fi

qstat_jobid=${PBS_JOBID#0:}
allocation_qstat_stdout=$scheduler_root/allocation-qstat.stdout
allocation_qstat_stderr=$scheduler_root/allocation-qstat.stderr
if [[ -e "$allocation_qstat_stdout" || -L "$allocation_qstat_stdout" \
   || -e "$allocation_qstat_stderr" || -L "$allocation_qstat_stderr" ]]; then
  echo "allocation qstat evidence is not fresh" >&2
  exit 2
fi
qstat -f "$qstat_jobid" >"$allocation_qstat_stdout" 2>"$allocation_qstat_stderr"
sync "$allocation_qstat_stdout" "$allocation_qstat_stderr"
readarray -t reservation_observation < <(
  "$PY" - "$allocation_qstat_stdout" <<'PY'
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
job_body=$repo/$JOB_BODY_RELATIVE
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
reservation_result=$job_root/reservation.json
if [[ -e "$reservation_result" || -L "$reservation_result" ]]; then
  echo "reservation result is not fresh" >&2
  exit 2
fi
"$PY" - "$reservation_result" "$allocation_qstat_stdout" \
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
sync "$job_root"

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
repository_current_pin=$(
  "$PY" -B -c 'from orchestrator.campaign.pin import CURRENT_PIN; print(CURRENT_PIN)'
)
if [[ ! "$repository_current_pin" =~ ^[0-9a-f]{7}$ \
   || ! "$IZANAGI_A2_CURRENT_PIN" =~ ^[0-9a-f]{7}$ \
   || "$IZANAGI_A2_CURRENT_PIN" != "$repository_current_pin" ]]; then
  echo "CCBench current pin must be a short lowercase commit" >&2
  exit 2
fi
if ! ccbench_full_head=$(
  git -C "$ccbench_root" rev-parse --verify 'HEAD^{commit}'
); then
  echo "CCBench HEAD cannot be resolved" >&2
  exit 2
fi
if ! resolved_current_pin=$(
  git -C "$ccbench_root" rev-parse --verify "${IZANAGI_A2_CURRENT_PIN}^{commit}"
); then
  echo "CCBench current pin cannot be resolved" >&2
  exit 2
fi
if [[ ! "$ccbench_full_head" =~ ^[0-9a-f]{40}$ \
   || ! "$resolved_current_pin" =~ ^[0-9a-f]{40}$ \
   || "$ccbench_full_head" != "$resolved_current_pin" \
   || "$ccbench_full_head" != "$IZANAGI_A2_CURRENT_PIN"* ]]; then
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
scratch=$scratch_base/${pbs_jobid_path_component}
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
"$PY" -B -m orchestrator.campaign.paper_story_a2_certification \
  "${POLICY_ARGS[@]}" compute-preflight \
  --workload "$workload" \
  --attempt-root "$attempt" \
  --raw-root "$raw_root" \
  --expected-head "$IZANAGI_A2_EXPECTED_HEAD" \
  --repo-root "$repo" \
  --dependency-prefix "$dependency_prefix"

"$PY" -B -m orchestrator.campaign.paper_story_a2_certification \
  "${POLICY_ARGS[@]}" run-workload \
  --workload "$workload" \
  --attempt-root "$attempt" \
  --raw-root "$raw_root" \
  --current-pin "$IZANAGI_A2_CURRENT_PIN" \
  --dependency-prefix "$dependency_prefix" \
  --ccbench-dir "$ccbench_root"
