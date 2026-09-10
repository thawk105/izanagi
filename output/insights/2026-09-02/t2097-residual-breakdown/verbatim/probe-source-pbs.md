# PBS 逐語 (計算ノードで 10 arm を走らせた script)

```text
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=01:00:00
#PBS -b 1
#PBS -N t2097-residual

set -uo pipefail
umask 077

REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp
SHARED=/work/1/SFC/tanab/.izanagi-acceptance-shards
PROBE_DIR=${IZANAGI_T2097_PROBE_RUNTIME:-/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/probe-runtime}

if [[ "$PROBE_DIR" != /* || ! -d "$PROBE_DIR" || -L "$PROBE_DIR" ]]; then
  echo "external absolute probe runtime directory is unavailable: $PROBE_DIR" >&2
  exit 2
fi
PROBE_DIR=$(realpath -e -- "$PROBE_DIR") || exit 2
if [[ "$PROBE_DIR" == "$REPO" || "$PROBE_DIR" == "$REPO/"* ]]; then
  echo "probe runtime directory must be outside the measured repository" >&2
  exit 2
fi
PROBE="$PROBE_DIR/_t2097_residual_probe.py"
PBS_SOURCE="$PROBE_DIR/_t2097_residual_probe.pbs"

if [[ -z "${PBS_JOBID:-}" ]]; then
  echo "PBS_JOBID is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

COMPUTE_HOST=$(hostname 2>/dev/null || true)
if [[ ! "$COMPUTE_HOST" =~ ^bnode[0-9]+([.].*)?$ ]]; then
  echo "T-2097 residual probe is compute-only: hostname=$COMPUTE_HOST" >&2
  exit 2
fi
if [[ ! -d "$REPO" || -L "$REPO" || ! -f "$PROBE" || -L "$PROBE" || ! -f "$PBS_SOURCE" || -L "$PBS_SOURCE" ]]; then
  echo "probe source or repository is unavailable" >&2
  exit 2
fi
if [[ ! -d "$SHARED" || -L "$SHARED" ]]; then
  echo "shared artifact root is unavailable" >&2
  exit 2
fi

PY=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10 python3; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' >/dev/null 2>&1; then
    PY=$(realpath -e -- "$resolved")
    break
  fi
done
if [[ -z "$PY" ]]; then
  echo "Python 3.10 or newer is required" >&2
  exit 2
fi

JOB_TAG="t2097-${PBS_JOBID//:/_}"
if [[ ! "$JOB_TAG" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe job tag" >&2
  exit 2
fi
SUMMARY="$SHARED/$JOB_TAG-summary.json"
PREFLIGHT="$SHARED/$JOB_TAG-consumer-preflight.json"

cd "$REPO" || exit 2
unset PYTHONHOME PYTHONSTARTUP PYTHONPATH PYTEST_ADDOPTS PYTEST_PLUGINS
unset IZANAGI_T2097_MODE IZANAGI_T2097_TIMING IZANAGI_T2097_OUTPUT
unset IZANAGI_T2097_INJECTION_ENV_BACKUP
export IZANAGI_TEST_NPROC=48
export IZANAGI_TASK_RUN_AUTO_RECORD=0

if ! "$PY" "$PROBE" preflight-consumers --root "$SHARED" --out "$PREFLIGHT"; then
  "$PY" "$PROBE" summarize --root "$SHARED" --job-tag "$JOB_TAG" --out "$SUMMARY"
  exit 4
fi

status=0
run_arm() {
  local arm=$1
  local shard=$2
  local probe_mode=$3
  local worktree_status
  local worktree_status_record="$SHARED/$JOB_TAG-$arm-worktree-status.txt"
  if ! worktree_status=$(/usr/bin/git -C "$REPO" status --porcelain --untracked-files=all 2>&1); then
    printf '%s\n' "$worktree_status" >"$worktree_status_record"
    echo "failed to inspect measured worktree before $arm; recorded: $worktree_status_record" >&2
    status=4
    return 1
  fi
  if [[ -n "$worktree_status" ]]; then
    printf '%s\n' "$worktree_status" >"$worktree_status_record"
    echo "measured worktree is not clean before $arm; recorded: $worktree_status_record" >&2
    status=4
    return 1
  fi
  if ! "$PY" "$PROBE" run-arm \
      --root "$SHARED" \
      --job-tag "$JOB_TAG" \
      --arm "$arm" \
      --shard "$shard" \
      --probe "$probe_mode" \
      --repo "$REPO" \
      --python "$PY" \
      --probe-source "$PROBE" \
      --pbs-source "$PBS_SOURCE"; then
    status=4
    return 1
  fi
  if ! "$PY" "$PROBE" check-progress --root "$SHARED" --job-tag "$JOB_TAG"; then
    status=4
    return 1
  fi
  return 0
}

run_arm R2-A1 2 none || true
if [[ $status -eq 0 ]]; then run_arm R2-B1 2 timing || true; fi
if [[ $status -eq 0 ]]; then run_arm R1-B1 1 timing || true; fi
if [[ $status -eq 0 ]]; then run_arm R1-A1 1 none || true; fi
if [[ $status -eq 0 ]]; then run_arm R1-A2 1 none || true; fi
if [[ $status -eq 0 ]]; then run_arm R1-B2 1 timing || true; fi
if [[ $status -eq 0 ]]; then run_arm R2-B2 2 timing || true; fi
if [[ $status -eq 0 ]]; then run_arm R2-A2 2 none || true; fi
if [[ $status -eq 0 ]]; then run_arm Z-S1 2 selector || true; fi
if [[ $status -eq 0 ]]; then run_arm Z-B1 2 timing || true; fi

if ! "$PY" "$PROBE" summarize --root "$SHARED" --job-tag "$JOB_TAG" --out "$SUMMARY"; then
  status=4
fi
exit "$status"
```
