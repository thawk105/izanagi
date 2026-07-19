#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:05:00
#PBS -b 1
LOG="${PBS_O_WORKDIR:-/tmp}/output/env/pegasus/debug/perf-${PBS_JOBID//:/_}.log"
exec > "$LOG" 2>&1
set -x
uname -r
ls /usr/lib/linux-tools/ 2>&1 || true
ls -d /usr/lib/linux-tools-* 2>&1 || true
cat /proc/sys/kernel/perf_event_paranoid
for p in /usr/lib/linux-tools/*/perf /usr/lib/linux-tools-*/perf; do
  [ -x "$p" ] || continue
  echo "== $p"
  "$p" --version 2>&1 | head -1
  "$p" stat -e cache-misses,instructions -- sleep 0.1 2>&1 | tail -4
done
echo done
