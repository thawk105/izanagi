#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:12:00
#PBS -b 1

# §7.0 実行場所分類の実測 job (rulings 第 7 束のユーザー委任、2026-08-13)。
# 対象: tools/claude_session_ledger.py (既定 argv) と tools/collect_wave_usage.py (実運用 argv)。
# login node では guard が unknown 実行体を拒否するため、計算ノードの job cgroup で
# charged memory のピークを sampling する (runbook §7.0 の測り方を job cgroup へ適用)。
set -u
set -o pipefail

if [[ -z "${PBS_JOBID:-}" ]]; then
  echo "PBS_JOBID is required" >&2
  exit 2
fi

BASE=/work/SFC/tanab/dev-wave-jobs/rulings8-measure
RUN_DIR="$BASE/run-$PBS_JOBID"
mkdir "$RUN_DIR" || exit 2
exec > "$RUN_DIR/job.log" 2>&1

WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings8-20260813
PROJECTS=/home/SFC/tanab/.claude/projects

echo "host=$(hostname) date=$(date -Is)"
cd "$WT" || exit 2
git rev-parse HEAD > "$RUN_DIR/commit.txt" 2>&1 || echo "git unavailable" > "$RUN_DIR/commit.txt"

# 入力面の記録
if ! ls "$PROJECTS" > /dev/null 2>&1; then
  echo "projects root unreadable from compute node" >&2
  exit 3
fi
du -sb "$PROJECTS" > "$RUN_DIR/input-bytes.txt"
find "$PROJECTS" -name '*.jsonl' | wc -l > "$RUN_DIR/input-files.txt"

# job cgroup の memory 使用量ファイルを特定 (v2 → v1 の順)
MEMFILE=""
CGLINE=$(awk -F: '$2==""{print $3}' /proc/self/cgroup | head -1)
if [[ -n "$CGLINE" && -r "/sys/fs/cgroup$CGLINE/memory.current" ]]; then
  MEMFILE="/sys/fs/cgroup$CGLINE/memory.current"
else
  CGV1=$(awk -F: '$2~/(^|,)memory(,|$)/{print $3}' /proc/self/cgroup | head -1)
  if [[ -n "$CGV1" && -r "/sys/fs/cgroup/memory$CGV1/memory.usage_in_bytes" ]]; then
    MEMFILE="/sys/fs/cgroup/memory$CGV1/memory.usage_in_bytes"
  fi
fi
if [[ -z "$MEMFILE" ]]; then
  echo "no readable cgroup memory file" >&2
  exit 4
fi
echo "memfile=$MEMFILE"

measure() {
  # $1 = 記録名、残り = command
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
  local base
  base=$(cat "$MEMFILE")
  echo "$base" > "$RUN_DIR/$name.base"
  "$@" > "$RUN_DIR/$name.stdout" 2> "$RUN_DIR/$name.stderr"
  echo $? > "$RUN_DIR/$name.rc"
  rm -f "$flag"
  wait "$sampler"
  echo "[$name] base=$(cat "$RUN_DIR/$name.base") peak=$(cat "$RUN_DIR/$name.peak") rc=$(cat "$RUN_DIR/$name.rc")"
}

for i in 1 2 3; do
  measure "ledger-$i" python3 tools/claude_session_ledger.py --json
done

for i in 1 2 3; do
  measure "usage-$i" python3 tools/collect_wave_usage.py \
    --wave-id rulings8-measure \
    --out "$RUN_DIR/usage-artifact-$i.json" \
    --cwd-under /work/1/SFC/tanab/izanagi \
    --projects-root "$PROJECTS"
done

date -Is > "$RUN_DIR/finished.txt"
touch "$RUN_DIR/.done"
echo "done"
