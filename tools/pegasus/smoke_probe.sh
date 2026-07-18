#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:10:00
#PBS -b 1

# Pegasus 計算ノードの前提を実測する探索 job。個別 command の rc も観測対象なので、
# capture は失敗を記録して残りの独立観測を続ける。保存失敗と probe 失敗は job 全体を非 0 にする。
set -u
set -o pipefail

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
BASE="$REPO_ROOT/output/env/pegasus/smoke"
RUN_DIR="$BASE/$PBS_JOBID"
mkdir -p "$BASE" || exit 2
if ! mkdir "$RUN_DIR"; then
  echo "smoke output already exists (create-only): $RUN_DIR" >&2
  exit 2
fi

overall_rc=0

capture() {
  local name=$1
  shift
  local stdout="$RUN_DIR/${name}.stdout"
  local stderr="$RUN_DIR/${name}.stderr"
  local rcfile="$RUN_DIR/${name}.rc"
  timeout 60 "$@" >"$stdout" 2>"$stderr"
  local rc=$?
  printf '%s\n' "$rc" >"$rcfile" || exit 2
  return 0
}

capture_shell() {
  local name=$1
  shift
  local stdout="$RUN_DIR/${name}.stdout"
  local stderr="$RUN_DIR/${name}.stderr"
  local rcfile="$RUN_DIR/${name}.rc"
  timeout 60 bash -lc "$*" >"$stdout" 2>"$stderr"
  local rc=$?
  printf '%s\n' "$rc" >"$rcfile" || exit 2
  return 0
}

capture hostname hostname -f
QSTAT_JOBID=${PBS_JOBID#0:}
capture qstat_job qstat -f "$QSTAT_JOBID"
capture qstat_jobs qstat
capture qstat_all_detail qstat -f
capture qstat_queues qstat -Q
capture qstat_queue_detail qstat -Q -f gen_S
capture pegasusinfo pegasusinfo

# module は shell function の環境が必要。stdout/stderr を分離し、stderr 非空を失敗扱いしない。
capture_shell module_list 'module -t list'
capture_shell module_avail 'module -t avail'

# Pegasus には gcc/cmake module がない。既定環境から見える system toolchain の
# command lookup、version 先頭行、canonical path をそれぞれ raw capture する。
capture toolchain_which which gcc g++ cmake
capture_shell toolchain_versions 'set -euo pipefail; for tool in gcc g++ cmake; do version=$("$tool" --version); IFS= read -r first_line <<<"$version"; printf "%s\t%s\n" "$tool" "$first_line"; done'
capture_shell toolchain_realpaths 'for tool in gcc g++ cmake; do printf "%s\t" "$tool"; realpath "$(command -v "$tool")"; done'

capture proc_mounts cat /proc/mounts
capture proc_findmnt findmnt -T /proc -o TARGET,SOURCE,FSTYPE,OPTIONS
capture proc2_comm cat /proc/2/comm
capture status_self cat /proc/self/status

capture numactl_hardware numactl --hardware
capture lscpu lscpu
capture cpuinfo cat /proc/cpuinfo
capture affinity taskset -pc "$$"

capture uptime uptime
capture loadavg cat /proc/loadavg
capture pressure_cpu cat /proc/pressure/cpu
capture pressure_memory cat /proc/pressure/memory
capture pressure_io cat /proc/pressure/io
capture process_overview ps -eo user,pid,ppid,psr,pcpu,pmem,stat,lstart,time,args --sort=-pcpu

{
  printf 'PBS_JOBID=%s\n' "$PBS_JOBID"
  printf 'PBS_O_WORKDIR=%s\n' "$PBS_O_WORKDIR"
  printf 'TMPDIR=%s\n' "${TMPDIR:-unavailable}"
  if [[ -e /scr ]]; then printf 'scr_exists=true\n'; else printf 'scr_exists=false\n'; fi
  if [[ -d /scr ]]; then printf 'scr_is_dir=true\n'; else printf 'scr_is_dir=false\n'; fi
  if [[ -w /scr ]]; then printf 'scr_writable=true\n'; else printf 'scr_writable=false\n'; fi
} >"$RUN_DIR/scratch.stdout" 2>"$RUN_DIR/scratch.stderr"
scratch_rc=0
scratch_canary="/scr/izanagi-smoke-${PBS_JOBID}-$$"
if [[ -d /scr && -w /scr ]]; then
  if ( set -o noclobber; : >"$scratch_canary" ) 2>>"$RUN_DIR/scratch.stderr"; then
    rm -f -- "$scratch_canary" 2>>"$RUN_DIR/scratch.stderr" || scratch_rc=$?
  else
    scratch_rc=$?
  fi
else
  scratch_rc=1
fi
printf '%s\n' "$scratch_rc" >"$RUN_DIR/scratch.rc" || exit 2
capture scratch_df df -h /scr
capture scratch_stat stat /scr

probe_file="$RUN_DIR/observation.json"
python3 "$REPO_ROOT/tools/pegasus/run_probe.py" --output "$probe_file" \
  >"$RUN_DIR/run_probe.stdout" 2>"$RUN_DIR/run_probe.stderr"
probe_rc=$?
printf '%s\n' "$probe_rc" >"$RUN_DIR/run_probe.rc" || exit 2
if [[ "$probe_rc" -ne 0 ]]; then
  overall_rc=$probe_rc
fi

python3 - "$RUN_DIR" <<'PY'
import hashlib
import json
import os
import sys
import time

root = sys.argv[1]
target = os.path.join(root, "manifest.json")
records = []
for name in sorted(os.listdir(root)):
    path = os.path.join(root, name)
    if name == "manifest.json" or not os.path.isfile(path):
        continue
    with open(path, "rb") as handle:
        data = handle.read()
    records.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
payload = {
    "schema_version": "pegasus-smoke-manifest/v1",
    "created_epoch": int(time.time()),
    "files": records,
}
with open(target, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
manifest_rc=$?
if [[ "$manifest_rc" -ne 0 ]]; then
  exit "$manifest_rc"
fi

exit "$overall_rc"
