#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:05:00
#PBS -b 1
LOG="${PBS_O_WORKDIR:-/tmp}/output/env/pegasus/debug/run-${PBS_JOBID//[^A-Za-z0-9._:-]/_}.log"
exec > "$LOG" 2>&1
set -x
echo "=== early debug $(date) ==="
echo "PBS_JOBID=$PBS_JOBID"
echo "PBS_O_WORKDIR=$PBS_O_WORKDIR"
env | grep -E "IZANAGI|PEGASUS" || echo "NO injected vars"
ls -ld "/scr/$PBS_JOBID" 2>&1 || echo "scr jobdir ABSENT"
mkdir "/scr/$PBS_JOBID"; echo "mkdir rc=$?"
ls -ld "/scr/$PBS_JOBID" 2>&1
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; echo "regex rc=$?"
bash --version | head -1
echo "=== done ==="
