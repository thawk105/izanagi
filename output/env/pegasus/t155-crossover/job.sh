#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:15:00
#PBS -b 1

# [T-155] write set 探索構造の crossover マイクロベンチ (dev-wave t155-crossover)。
# 目的: 計算ノード上で bench.cc (単体・単一スレッド) を build し、n* sweep の JSON を持ち帰る。
# 本番 (external/ccbench) には触れない。性能値はこのジョブの結果だけを使う (ログインノードの
# 実行値は使わない)。予約式 (秒): compile 60 + selfcheck 30 + 本走 240 + 予備 210 = 540 < 900。
# 検査はパイプ (grep -q 等) を使わずファイル経由で行う (F44: pipefail + SIGPIPE の偽赤)。
set -Eeuo pipefail
umask 077

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

# /scr のパスに ':' を含めない (runbook §7.1)
TMPDIR="/scr/${PBS_JOBID//:/_}-t155"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists (create-only): $TMPDIR" >&2
  exit 2
fi
cleanup() { rm -rf "$TMPDIR" || true; }
trap cleanup EXIT

HERE=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -f "$HERE/bench.cc" ]] || { echo "bench.cc missing in $HERE" >&2; exit 2; }
STAGE="$HERE/job-staging/$PBS_JOBID"
mkdir -p "$HERE/job-staging"
if ! mkdir "$STAGE"; then
  echo "staging already exists (create-only): $STAGE" >&2
  exit 2
fi

# ---- (i) 環境の記録 ----
{
  echo "jobid: $PBS_JOBID"
  echo "host: $(hostname)"
  echo "kernel: $(uname -r)"
  echo "nproc: $(nproc)"
  echo "date_start: $(date -Is)"
  grep -m1 "model name" /proc/cpuinfo || true
  echo "bench_cpu: 2 (taskset)"
} >"$STAGE/env.txt"
module -t list >"$STAGE/module-list.txt" 2>&1 || true

CXX_PATH=$(realpath "$(command -v g++)")
"$CXX_PATH" --version >"$STAGE/compiler.version" 2>&1

# ---- (ii) build (計測と同一ノード・同一 toolchain) ----
CXXFLAGS="-O3 -std=c++17 -Wall -Wextra"
echo "cxxflags: $CXXFLAGS" >>"$STAGE/env.txt"
timeout 120 "$CXX_PATH" $CXXFLAGS -o "$TMPDIR/bench" "$HERE/bench.cc" \
  >"$STAGE/build.log" 2>&1
sha256sum "$TMPDIR/bench" >"$STAGE/binary.sha256"

# ---- (iii) 生死確認 (DW-G01): selfcheck = 4 候補の意味論一致 ----
timeout 60 "$TMPDIR/bench" "$TMPDIR/selfcheck.json" --selfcheck-only \
  >"$STAGE/selfcheck.stdout" 2>"$STAGE/selfcheck.stderr"

# ---- (iv) 単独性の確認 (F3: 割当てを専有の保証と見なさない) ----
cat /proc/loadavg >"$STAGE/loadavg-before.txt"
ps -eo user,pid,pcpu,comm --sort=-pcpu >"$TMPDIR/ps-before.txt" || true
head -25 "$TMPDIR/ps-before.txt" >"$STAGE/ps-before.txt" || true
# 他プロセスの高負荷を検知したら記録して赤にする (再計測は親の判断)
awk -v me="$(id -un)" 'NR>1 && $1 != me && $3 > 50.0 {print}' \
  "$TMPDIR/ps-before.txt" >"$STAGE/contention.txt" || true
if [[ -s "$STAGE/contention.txt" ]]; then
  echo "single-tenancy check failed: foreign process >50% cpu" >&2
  exit 4
fi

# ---- (v) 本走 (単一コアへ pin) ----
timeout 360 taskset -c 2 "$TMPDIR/bench" "$STAGE/result.json" \
  >"$STAGE/run.stdout" 2>"$STAGE/run.stderr"

cat /proc/loadavg >"$STAGE/loadavg-after.txt"
ps -eo user,pid,pcpu,comm --sort=-pcpu >"$TMPDIR/ps-after.txt" || true
head -25 "$TMPDIR/ps-after.txt" >"$STAGE/ps-after.txt" || true

[[ -s "$STAGE/result.json" ]] || { echo "result.json missing/empty" >&2; exit 2; }
echo "date_end: $(date -Is)" >>"$STAGE/env.txt"
echo "OK" >"$STAGE/status.txt"
