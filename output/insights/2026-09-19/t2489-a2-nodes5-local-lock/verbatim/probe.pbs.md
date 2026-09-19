#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 2
#PBS -l elapstim_req=00:05:00
#PBS -N t2489-lock
set -euo pipefail
: "${T2489_PROBE_OUT:?fresh shared output directory required}"
: "${T2489_REPO_ROOT:?repository root required}"
: "${PBS_NODEFILE:?}"
if [[ ! "${PBS_JOBID:-}" =~ ^(0|[1-9][0-9]*):(.+)$ ]]; then
  echo 'PBS_JOBID is not a numbered request ID' >&2
  exit 2
fi
rank=${BASH_REMATCH[1]}
[[ "$rank" == 0 || "$rank" == 1 ]] || exit 2
cd "$T2489_REPO_ROOT"
export PYTHONDONTWRITEBYTECODE=1
exec python3.10 -B t2489_lock_probe.py "$rank"
