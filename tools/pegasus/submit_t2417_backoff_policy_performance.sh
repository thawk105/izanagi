#!/bin/bash

set -Eeuo pipefail
umask 077

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
CANONICAL_ROOT=$(git -C "$REPO_ROOT" rev-parse --show-toplevel)
CANONICAL_ROOT=$(realpath -e -- "$CANONICAL_ROOT")
if [[ "$REPO_ROOT" != "$CANONICAL_ROOT" ]]; then
  echo "repository root is not canonical" >&2
  exit 2
fi
REPO_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD)
if [[ ! "$REPO_HEAD" =~ ^[0-9a-f]{40}$ ]]; then
  echo "submission checkout HEAD must be an exact commit" >&2
  exit 2
fi
if git -C "$REPO_ROOT" symbolic-ref -q HEAD >/dev/null; then
  echo "submission requires one detached checkout" >&2
  exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]]; then
  echo "submission checkout must be clean" >&2
  exit 2
fi
PREREGISTRATION="$REPO_ROOT/docs/backoff-policy-performance-preregistration.md"
PBS_BODY="$REPO_ROOT/tools/pegasus/probes/t2187_adaptive_const_probe.pbs"
if [[ ! -f "$PREREGISTRATION" || -L "$PREREGISTRATION" ||
      ! -f "$PBS_BODY" || -L "$PBS_BODY" ]]; then
  echo "preregistration or PBS body is unavailable" >&2
  exit 2
fi

P0='cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0'
P1='cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1'
P2='cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2'
PERMUTATIONS=(
  "$P0+$P1+$P2"
  "$P0+$P2+$P1"
  "$P1+$P0+$P2"
  "$P1+$P2+$P0"
  "$P2+$P0+$P1"
  "$P2+$P1+$P0"
)
SEEDS=(
  7170359757993337886
  17989269546948137795
  3716960512023197351
  2309627334396074330
  17927187949116432153
  3065832495472073934
  4312234405970990967
  427285116805996036
  3640648522570663905
  6418011988295890983
  8628608498907907249
  3020250207517407008
  2373385927424670485
  12508141252750115867
  5818589253263944573
  13760661656174455019
  16587099826641119208
  13478069633953621058
)
WORKLOADS='write-heavy+balanced+read-heavy'
THREADS='6+12+18+24+30+36+42+48'
POLICY_OUTPUT_PREFIX=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2417-policy
ATTEMPT_ID=${1:-$(date -u +%Y%m%dT%H%M%SZ)}
if [[ ! "$ATTEMPT_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "attempt id is not a safe label" >&2
  exit 2
fi
OUT_DIR="$POLICY_OUTPUT_PREFIX/$ATTEMPT_ID"

cd "$REPO_ROOT"
submitted=0
for rep in {0..17}; do
  order_index=$((rep % 6))
  order=${PERMUTATIONS[$order_index]}
  seed=${SEEDS[$rep]}
  qsub_environment="IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=$OUT_DIR,IZANAGI_T2187_CELLS=$order,IZANAGI_T2187_WORKLOADS=$WORKLOADS,IZANAGI_T2187_THREADS=$THREADS,IZANAGI_T2187_REP_INDEX=$rep,IZANAGI_T2187_STEP_POLICY_SEED=$seed,IZANAGI_T2187_STAGE=1"
  if ! job_id=$(qsub -v "$qsub_environment" "$PBS_BODY"); then
    echo "qsub failed for rep $rep after $submitted successful submissions" >&2
    exit 1
  fi
  if [[ ! "$job_id" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
    echo "qsub returned an invalid job id for rep $rep" >&2
    exit 1
  fi
  printf '{"job_id":"%s","rep_index":%d,"order_index":%d,"order":"%s","seed":"%s"}\n' \
    "$job_id" "$rep" "$order_index" "$order" "$seed"
  submitted=$((submitted + 1))
done

if [[ "$submitted" -ne 18 ]]; then
  echo "submission count mismatch: expected 18, got $submitted" >&2
  exit 1
fi
echo "submitted $submitted policy-performance blocks" >&2
