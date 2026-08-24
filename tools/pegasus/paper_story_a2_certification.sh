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
  IZANAGI_RESERVATION_JOB_ID IZANAGI_RESERVATION_HOST
  IZANAGI_RESERVATION_DEADLINE
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
if [[ ! -d "$dependency_source" || -L "$dependency_source" ]]; then
  echo "pinned dependency source is unavailable" >&2
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
