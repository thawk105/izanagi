#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:12:00
#PBS -b 1

# §7.0 実行場所分類の実測 job 第 2 走 (2026-08-13)。
# 変更点: (1) cgroup を probe し、可能なら専有 sub-cgroup / per-job v1 cgroup を使う。
# (2) collect_wave_usage へ必須の --project を渡す。(3) ledger の rc=2 は走査完了後の
# fatal flag と判明したため、rc とともにピークを記録する。
set -u
set -o pipefail

if [[ -z "${PBS_JOBID:-}" ]]; then
  echo "PBS_JOBID is required" >&2
  exit 2
fi

BASE=/work/SFC/tanab/dev-wave-jobs/rulings8-measure
RUN_DIR="$BASE/run2-${PBS_JOBID//:/_}"
mkdir "$RUN_DIR" || exit 2
exec > "$RUN_DIR/job.log" 2>&1

WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings8-20260813
PROJECTS=/home/SFC/tanab/.claude/projects

echo "host=$(hostname) date=$(date -Is) jobid=$PBS_JOBID"
cd "$WT" || exit 2
git rev-parse HEAD > "$RUN_DIR/commit.txt" 2>&1 || true
du -sb "$PROJECTS" > "$RUN_DIR/input-bytes.txt"
find "$PROJECTS" -name '*.jsonl' | wc -l > "$RUN_DIR/input-files.txt"

# --- cgroup probe ---
cat /proc/self/cgroup > "$RUN_DIR/proc-self-cgroup.txt"
echo "--- probe ---"
cat "$RUN_DIR/proc-self-cgroup.txt"

MEMFILE=""
ISOLATION="shared-service"

# 1) per-job v1 memory cgroup (path に request 由来の固有要素があるか)
V1PATH=$(awk -F: '$2~/(^|,)memory(,|$)/{print $3}' /proc/self/cgroup | head -1)
if [[ -n "${V1PATH:-}" && "$V1PATH" != "/" && -r "/sys/fs/cgroup/memory$V1PATH/memory.usage_in_bytes" ]]; then
  MEMFILE="/sys/fs/cgroup/memory$V1PATH/memory.usage_in_bytes"
  PEAKFILE="/sys/fs/cgroup/memory$V1PATH/memory.max_usage_in_bytes"
  ISOLATION="v1-job-cgroup:$V1PATH"
fi

# 2) v2 で自分の cgroup に sub-cgroup を作れるか (delegation されていれば専有化できる)
if [[ -z "$MEMFILE" ]]; then
  V2PATH=$(awk -F: '$1=="0"{print $3}' /proc/self/cgroup | head -1)
  CG="/sys/fs/cgroup$V2PATH"
  if [[ -d "$CG" && -w "$CG" ]] && mkdir "$CG/izmeas" 2>/dev/null; then
    if echo $$ > "$CG/izmeas/cgroup.procs" 2>/dev/null; then
      MEMFILE="$CG/izmeas/memory.current"
      PEAKFILE="$CG/izmeas/memory.peak"
      [[ -r "$PEAKFILE" ]] || PEAKFILE=""
      ISOLATION="v2-subcgroup"
    else
      rmdir "$CG/izmeas" 2>/dev/null
    fi
  fi
fi

# 3) fallback: 共有 service cgroup の delta sampling (第 1 走と同じ、汚染注記つき)
if [[ -z "$MEMFILE" ]]; then
  V2PATH=$(awk -F: '$1=="0"{print $3}' /proc/self/cgroup | head -1)
  MEMFILE="/sys/fs/cgroup$V2PATH/memory.current"
  PEAKFILE=""
  ISOLATION="shared-service-delta"
fi
echo "memfile=$MEMFILE isolation=$ISOLATION peakfile=${PEAKFILE:-none}"
echo "$ISOLATION" > "$RUN_DIR/isolation.txt"

measure() {
  local name=$1; shift
  local flag="$RUN_DIR/.sampling-$name"
  # kernel peak が使えるならリセットを試みる (v1 は 0 書き込みでリセット可のことがある)
  if [[ -n "${PEAKFILE:-}" && -w "$PEAKFILE" ]]; then
    echo 0 > "$PEAKFILE" 2>/dev/null || true
  fi
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
  if [[ -n "${PEAKFILE:-}" && -r "$PEAKFILE" ]]; then
    cat "$PEAKFILE" > "$RUN_DIR/$name.kernelpeak" 2>/dev/null || true
  fi
  echo "[$name] base=$(cat "$RUN_DIR/$name.base") peak=$(cat "$RUN_DIR/$name.peak") kernelpeak=$(cat "$RUN_DIR/$name.kernelpeak" 2>/dev/null || echo -) rc=$(cat "$RUN_DIR/$name.rc")"
}

for i in 1 2 3; do
  measure "ledger-$i" python3 tools/claude_session_ledger.py --json
done

for i in 1 2 3; do
  measure "usage-$i" python3 tools/collect_wave_usage.py \
    --wave-id rulings8-measure \
    --out "$RUN_DIR/usage-artifact-$i.json" \
    --project -work-1-SFC-tanab-izanagi \
    --cwd-under /work/1/SFC/tanab/izanagi \
    --projects-root "$PROJECTS"
done

date -Is > "$RUN_DIR/finished.txt"
touch "$RUN_DIR/.done"
echo "done"
