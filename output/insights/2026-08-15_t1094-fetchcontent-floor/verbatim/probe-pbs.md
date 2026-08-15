# probe 逐語 — t1094_floor_probe.pbs

実体は repo 外 (job tmp)。実装面の `.py` / `.pbs` を repo へ入れない規約に従い逐語で貼る。
著者 = Codex author (段 5 + 段 6 fix)。

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:45:00
#PBS -b 1

# Probe-only budget, independent of the 36,000-second floor budget.
# Durable observations used for this envelope:
# - t139 R4 completed in about 614 s; its two CCBench configure/build pairs
#   were 1.48/14.00 s and 1.52/4.59 s.
# - t316 completed in about 85-99 s.
# - t419 completed in about 6-93 s across four recorded runs (latest two were
#   about 90-93 s).
# This probe adds dependency installs, two FetchContent configures, and two
# bounded masstree targets.  The Python caps fit in 2,520 s, leaving 180 s for
# interpreter admission, create-only scratch, JSON fsync, and PBS teardown.

set -euo pipefail

[[ -n ${PBS_JOBID:-} && -n ${PBS_O_WORKDIR:-} &&
   -n ${IZANAGI_T1094_EXPECTED_COMMIT:-} &&
   -n ${IZANAGI_T1094_EXPECTED_WORKTREE_ROOT:-} &&
   -n ${IZANAGI_T1094_PROBE_PY:-} &&
   -n ${IZANAGI_T1094_PROBE_OUTPUT:-} &&
   -n ${IZANAGI_PEGASUS_THIRDPARTY_CACHE:-} &&
   -n ${IZANAGI_THIRDPARTY_SOURCE_ROOT:-} &&
   $PBS_JOBID =~ ^[A-Za-z0-9._:-]+$ &&
   $IZANAGI_T1094_EXPECTED_COMMIT =~ ^[0-9a-f]{40}$ &&
   $IZANAGI_T1094_EXPECTED_WORKTREE_ROOT == /* &&
   $IZANAGI_T1094_PROBE_PY == /* &&
   $IZANAGI_T1094_PROBE_OUTPUT == /* &&
   $IZANAGI_PEGASUS_THIRDPARTY_CACHE == /* &&
   $IZANAGI_THIRDPARTY_SOURCE_ROOT == /* ]] || exit 2

umask 077

bounded() {
  local cap=$1
  shift
  timeout --foreground --signal=TERM --kill-after=5s "${cap}s" "$@"
}

PY_CANDIDATE=$(bounded 5 bash -c 'command -v python3.10') || exit 3
PY=$(bounded 5 realpath -e -- "$PY_CANDIDATE") || exit 3
bounded 5 "$PY" -I -B - <<'PY'
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)
PY

REPO=$(bounded 5 realpath -e -- "$PBS_O_WORKDIR") || exit 3
EXPECTED_ROOT=$(bounded 5 realpath -e -- "$IZANAGI_T1094_EXPECTED_WORKTREE_ROOT") || exit 3
# NQSV runs a spooled copy of this wrapper, so its location cannot locate the payload.
PROBE_PY=$(bounded 5 realpath -e -- "$IZANAGI_T1094_PROBE_PY") || exit 3
CACHE_ROOT=$(bounded 5 realpath -e -- "$IZANAGI_PEGASUS_THIRDPARTY_CACHE") || exit 3
SOURCE_ROOT=$(bounded 5 realpath -e -- "$IZANAGI_THIRDPARTY_SOURCE_ROOT") || exit 3
OUTPUT_PARENT_RAW=${IZANAGI_T1094_PROBE_OUTPUT%/*}
[[ -n $OUTPUT_PARENT_RAW ]] || OUTPUT_PARENT_RAW=/
OUTPUT_PARENT=$(bounded 5 realpath -e -- "$OUTPUT_PARENT_RAW") || exit 3
[[ $REPO == "$EXPECTED_ROOT" && -d $REPO && ! -L $REPO &&
   -f $PROBE_PY && ! -L $PROBE_PY && ! -L $IZANAGI_T1094_PROBE_PY &&
   -d $CACHE_ROOT && ! -L $CACHE_ROOT &&
   -d $SOURCE_ROOT && ! -L $SOURCE_ROOT &&
   -d $OUTPUT_PARENT && ! -L $OUTPUT_PARENT &&
   ! -e $IZANAGI_T1094_PROBE_OUTPUT && ! -L $IZANAGI_T1094_PROBE_OUTPUT ]] || exit 3

HOST=$(bounded 5 hostname) || exit 3
HOST_SHORT=${HOST%%.*}
[[ $HOST_SHORT =~ ^bnode[0-9]+$ ]] || exit 5

JOB_TAG=${PBS_JOBID//:/_}
[[ $JOB_TAG =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $JOB_TAG != . && $JOB_TAG != .. ]] || exit 3
SCRATCH=/scr/$JOB_TAG
[[ ! -e $SCRATCH && ! -L $SCRATCH ]] || exit 3
bounded 5 mkdir -m 700 -- "$SCRATCH" || exit 3

cleanup() {
  local rc=$?
  trap - EXIT TERM INT
  set +e
  bounded 30 chmod -R u+w -- "$SCRATCH"
  bounded 120 rm -rf -- "$SCRATCH"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

SHIM=$SCRATCH/python-shim
bounded 5 mkdir -m 700 -- "$SHIM" || exit 3
bounded 5 ln -s -- "$PY" "$SHIM/python3" || exit 3
PY_DIR=${PY%/*}
export PATH="$SHIM:$PY_DIR:/usr/bin:/bin"
export TMPDIR=$SCRATCH
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP SSH_AUTH_SOCK

# The outer cap bounds imported production helpers as a last resort.  The
# Python program independently bounds each direct subprocess and reserves
# time to publish its single create-only JSON receipt.
bounded 2580 "$PY" -I -B "$PROBE_PY" \
  --repo-root "$REPO" \
  --scratch-root "$SCRATCH" \
  --cache-root "$CACHE_ROOT" \
  --source-root "$SOURCE_ROOT" \
  --expected-commit "$IZANAGI_T1094_EXPECTED_COMMIT" \
  --output "$IZANAGI_T1094_PROBE_OUTPUT"
```
