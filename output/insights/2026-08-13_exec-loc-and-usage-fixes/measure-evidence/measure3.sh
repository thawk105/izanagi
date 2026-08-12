#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:10:00
#PBS -b 1

# §7.0 実測 job 第 3 走 (2026-08-13)。collect_wave_usage のみ。
# 第 2 走の欠陥修正: --project は等号形でないと先頭 - が option と解釈される。
set -u
set -o pipefail

if [[ -z "${PBS_JOBID:-}" ]]; then
  echo "PBS_JOBID is required" >&2
  exit 2
fi

BASE=/work/SFC/tanab/dev-wave-jobs/rulings8-measure
RUN_DIR="$BASE/run3-${PBS_JOBID//:/_}"
mkdir "$RUN_DIR" || exit 2
exec > "$RUN_DIR/job.log" 2>&1

WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings8-20260813
PROJECTS=/home/SFC/tanab/.claude/projects

echo "host=$(hostname) date=$(date -Is) jobid=$PBS_JOBID"
cd "$WT" || exit 2
git rev-parse HEAD > "$RUN_DIR/commit.txt" 2>&1 || true
du -sb "$PROJECTS/-work-1-SFC-tanab-izanagi" > "$RUN_DIR/input-bytes.txt"
find "$PROJECTS/-work-1-SFC-tanab-izanagi" -name '*.jsonl' | wc -l > "$RUN_DIR/input-files.txt"

V2PATH=$(awk -F: '$1=="0"{print $3}' /proc/self/cgroup | head -1)
MEMFILE="/sys/fs/cgroup$V2PATH/memory.current"
echo "memfile=$MEMFILE isolation=shared-service-delta"

measure() {
  local name=$1; shift
  local flag="$RUN_DIR/.sampling-$name"
  touch "$flag"
  (
    peak=0
    while [[ -f "$flag" ]]; do
      v=$(cat "$MEMFILE" 2>/dev/null || echo 0)
      [[ "$v" =~ ^[0-9]+$ ]] && (( v > peak )) && peak=$v
    done
    echo "$peak" > "$RUN_DIR/$name.peak"
  ) &
  local sampler=$!
  cat "$MEMFILE" > "$RUN_DIR/$name.base"
  "$@" > "$RUN_DIR/$name.stdout" 2> "$RUN_DIR/$name.stderr"
  echo $? > "$RUN_DIR/$name.rc"
  rm -f "$flag"
  wait "$sampler"
  echo "[$name] base=$(cat "$RUN_DIR/$name.base") peak=$(cat "$RUN_DIR/$name.peak") rc=$(cat "$RUN_DIR/$name.rc")"
}

for i in 1 2 3; do
  measure "usage-$i" python3 tools/collect_wave_usage.py \
    --wave-id rulings8-measure \
    --out "$RUN_DIR/usage-artifact-$i.json" \
    --project=-work-1-SFC-tanab-izanagi \
    --cwd-under /work/1/SFC/tanab/izanagi \
    --projects-root "$PROJECTS"
done

date -Is > "$RUN_DIR/finished.txt"
touch "$RUN_DIR/.done"
echo "done"
