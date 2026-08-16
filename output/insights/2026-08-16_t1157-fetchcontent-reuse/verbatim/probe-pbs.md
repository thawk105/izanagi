# probe 逐語 — t1157_probe.pbs

実体は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/wave-t1157-fetchcontent-reuse/`)。
実装面の `.py` / `.pbs` を repo へ入れない規約に従い逐語で貼る。
著者 = Codex `role=author` (段 5 + 段 6 fix 第 1〜4 巡)。

権威走行 = `Request 912911.nqsv` / `bnode009` / 2026-08-16 09:43-09:45 JST。

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=01:30:00
#PBS -b 1

set -euo pipefail

[[ -n ${PBS_JOBID:-} && -n ${PBS_O_WORKDIR:-} &&
   -n ${IZANAGI_T1157_PROBE_PY:-} &&
   -n ${IZANAGI_T1157_PROBE_OUTPUT:-} ]] || exit 2

bounded() {
  local cap=$1
  shift
  timeout --foreground --signal=TERM --kill-after=5s "${cap}s" "$@"
}

[[ $PBS_JOBID =~ ^[A-Za-z0-9._:-]+$ &&
   $PBS_O_WORKDIR == /* &&
   $IZANAGI_T1157_PROBE_PY == /* &&
   $IZANAGI_T1157_PROBE_OUTPUT == /* ]] || exit 3

umask 077

PY_CANDIDATE=$(bounded 5 bash -c 'command -v python3.10') || exit 3
PY=$(bounded 5 realpath -e -- "$PY_CANDIDATE") || exit 3
[[ -f $PY && -x $PY && ! -L $PY ]] || exit 3
bounded 5 "$PY" -I -B - <<'PY'
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)
PY

REPO=$(bounded 5 realpath -e -- "$PBS_O_WORKDIR") || exit 3
# NQSV executes a spooled copy, so $0 cannot locate the submitted payload.
PROBE_PY=$(bounded 5 realpath -e -- "$IZANAGI_T1157_PROBE_PY") || exit 3
OUTPUT_PARENT_RAW=${IZANAGI_T1157_PROBE_OUTPUT%/*}
[[ -n $OUTPUT_PARENT_RAW ]] || OUTPUT_PARENT_RAW=/
OUTPUT_PARENT=$(bounded 5 realpath -e -- "$OUTPUT_PARENT_RAW") || exit 3
[[ -d $REPO && ! -L $PBS_O_WORKDIR &&
   -f $PROBE_PY && ! -L $IZANAGI_T1157_PROBE_PY &&
   -d $OUTPUT_PARENT && ! -L $OUTPUT_PARENT_RAW &&
   ! -e $IZANAGI_T1157_PROBE_OUTPUT &&
   ! -L $IZANAGI_T1157_PROBE_OUTPUT ]] || exit 3

case "$IZANAGI_T1157_PROBE_OUTPUT" in
  "$REPO"|"$REPO"/*) exit 3 ;;
esac

HOST=$(bounded 5 hostname) || exit 3
HOST_SHORT=${HOST%%.*}
[[ $HOST_SHORT =~ ^bnode[0-9]+$ ]] || exit 5

JOB_TAG=${PBS_JOBID//:/_}
[[ $JOB_TAG =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ &&
   $JOB_TAG != . && $JOB_TAG != .. ]] || exit 3
SCRATCH=/scr/$JOB_TAG
case "$IZANAGI_T1157_PROBE_OUTPUT" in
  "$SCRATCH"|"$SCRATCH"/*) exit 3 ;;
esac
[[ ! -e $SCRATCH && ! -L $SCRATCH ]] || exit 3
bounded 5 mkdir -m 700 -- "$SCRATCH" || exit 3

cleanup() {
  local rc=$?
  trap - EXIT TERM INT
  set +e
  bounded 30 chmod -R u+w -- "$SCRATCH"
  bounded 120 rm -rf -- "$SCRATCH"
  bounded 30 git -C "$REPO/external/ccbench" worktree prune
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

export TMPDIR=$SCRATCH
SHIM=$SCRATCH/python-shim
bounded 5 mkdir -m 700 -- "$SHIM" || exit 3
bounded 5 ln -s -- "$PY" "$SHIM/python3" || exit 3
PY_DIR=${PY%/*}
export PATH="$SHIM:$PY_DIR:/usr/bin:/bin"
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP SSH_AUTH_SOCK

# The Python probe has per-command caps and reserves time to publish JSON.
# This cap is the final wall-clock backstop inside the 90-minute PBS envelope.
bounded 4800 "$PY" -I -B "$PROBE_PY" \
  --repo-root "$REPO" \
  --output "$IZANAGI_T1157_PROBE_OUTPUT"
```
