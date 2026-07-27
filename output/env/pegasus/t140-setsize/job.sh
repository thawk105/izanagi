#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:40:00
#PBS -b 1

# [T-140] 実 set-size 分布の実測ジョブ (dev-wave t140-setsize)。
# 目的: S2 verify 構成 verbatim (pipeline.py S2_FLAGS + extime=3) の trace-enabled
# stock silo を 1 run し、commit 時 |read_set_|/|write_set_| の分布 digest を持ち帰る。
# 性能値は取らない・使わない (規律1)。raw trace は /scr に置き job 終了時に消す (D31)。
# 予約式 (秒): deps build (gflags 180 + glog 360) + ccbench build 900 + smoke 120
# + s2 run 120 + parse 600 + 予備 120 = 2280 < 2400 (00:40:00)。
# build 手順は tools/pegasus/certify_calibration.sh の実測済み経路を踏襲 (leaner)。
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

# /scr のパスに ':' を含めない (runbook §7.1: CMake が ':' をリスト区切り化する)
export TMPDIR="/scr/${PBS_JOBID//:/_}-t140"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists (create-only): $TMPDIR" >&2
  exit 2
fi

HERE=$(cd "$PBS_O_WORKDIR" && pwd -P)
REPO_ROOT=$(cd "$HERE/../../../.." && pwd -P)
if [[ ! -d "$REPO_ROOT/external/ccbench" || ! -f "$REPO_ROOT/tools/pegasus/policy.json" ]]; then
  echo "repo root resolution failed: $REPO_ROOT" >&2
  exit 2
fi
STAGE="$HERE/job-staging/$PBS_JOBID"
mkdir -p "$HERE/job-staging"
if ! mkdir "$STAGE"; then
  echo "staging already exists (create-only): $STAGE" >&2
  exit 2
fi

CCBENCH_BASE="$REPO_ROOT/external/ccbench"
BUILD_SOURCE=""
cleanup() {
  if [[ -n "$BUILD_SOURCE" && -d "$BUILD_SOURCE" ]]; then
    git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMPDIR" || true
}
trap cleanup EXIT

# ---- (i) 環境の記録 + interpreter 版検査 (runbook §7: 検査せず使わない) ----
{
  echo "jobid: $PBS_JOBID"
  echo "host: $(hostname)"
  echo "kernel: $(uname -r)"
  echo "nproc: $(nproc)"
  echo "date_start: $(date -Is)"
  grep -m1 "model name" /proc/cpuinfo || true
} >"$STAGE/env.txt"
module -t list >"$STAGE/module-list.txt" 2>&1 || true

PY=python3
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)'; then
  if [[ -x /usr/bin/python3.10 ]]; then
    PY=/usr/bin/python3.10
  else
    echo "no usable python3 (>=3.6)" >&2
    exit 2
  fi
fi
"$PY" -V >"$STAGE/python.version" 2>&1

FREE_GB=$(df -BG --output=avail "$TMPDIR" | tail -1 | tr -dc '0-9')
echo "scr_free_gb: $FREE_GB" >>"$STAGE/env.txt"
if [[ "$FREE_GB" -lt 20 ]]; then
  echo "/scr free ${FREE_GB}GB < 20GB" >&2
  exit 2
fi

CC_PATH=$(realpath "$(command -v gcc)")
CXX_PATH=$(realpath "$(command -v g++)")
"$CC_PATH" --version >"$STAGE/compiler.version" 2>&1
cmake --version >"$STAGE/cmake.version" 2>&1

# ---- (ii) pinned-clean gflags/glog を /scr で static build (certify と同引数) ----
read -r GFLAGS_SRC GFLAGS_HEAD_EXPECT GLOG_SRC GLOG_HEAD_EXPECT < <("$PY" -c '
import json
p = json.load(open("'"$REPO_ROOT"'/tools/pegasus/policy.json"))
print(p["gflags_source_path"], p["gflags_expected_head"],
      p["glog_source_path"], p["glog_expected_head"])
')
for name in gflags glog; do
  if [[ "$name" == gflags ]]; then src="$GFLAGS_SRC"; expect="$GFLAGS_HEAD_EXPECT";
  else src="$GLOG_SRC"; expect="$GLOG_HEAD_EXPECT"; fi
  head=$(git -C "$src" rev-parse HEAD)
  [[ "$head" == "$expect" ]] || { echo "$name HEAD mismatch: $head" >&2; exit 2; }
  [[ -z "$(git -C "$src" status --porcelain --untracked-files=all)" ]] \
    || { echo "$name working tree dirty" >&2; exit 2; }
done

GFLAGS_INSTALL="$TMPDIR/gflags-install"
timeout 60 cmake -S "$GFLAGS_SRC" -B "$TMPDIR/gflags-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL" \
  "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH" \
  >"$STAGE/gflags-configure.log" 2>&1
timeout 60 cmake --build "$TMPDIR/gflags-build" -j 48 >"$STAGE/gflags-build.log" 2>&1
timeout 60 cmake --install "$TMPDIR/gflags-build" >"$STAGE/gflags-install.log" 2>&1

GLOG_INSTALL="$TMPDIR/glog-install"
timeout 120 cmake -S "$GLOG_SRC" -B "$TMPDIR/glog-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL" \
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL" \
  "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH" \
  >"$STAGE/glog-configure.log" 2>&1
timeout 120 cmake --build "$TMPDIR/glog-build" -j 48 >"$STAGE/glog-build.log" 2>&1
timeout 120 cmake --install "$TMPDIR/glog-build" >"$STAGE/glog-install.log" 2>&1

# ---- (iii) pinned-clean CCBench を使い捨て worktree で trace-enabled build ----
CCBENCH_HEAD=$(git -C "$CCBENCH_BASE" rev-parse HEAD)
GITLINK=$(git -C "$REPO_ROOT" ls-tree HEAD external/ccbench | awk '{print $3}')
[[ "$CCBENCH_HEAD" == "$GITLINK" ]] || { echo "ccbench not at gitlink" >&2; exit 2; }
[[ -z "$(git -C "$CCBENCH_BASE" status --porcelain --untracked-files=no)" ]] \
  || { echo "ccbench dirty" >&2; exit 2; }
echo "ccbench_head: $CCBENCH_HEAD" >>"$STAGE/env.txt"

BUILD_SOURCE="$TMPDIR/ccbench-source"
BUILD_DIR="$TMPDIR/ccbench-build"
git -C "$CCBENCH_BASE" worktree add --detach "$BUILD_SOURCE" "$CCBENCH_HEAD" \
  >"$STAGE/worktree-add.log" 2>&1
mkdir "$BUILD_DIR"
# stock genome (s2_verify_calibration.STOCK_G) + trace-enabled。既定と同値でも明示凍結
timeout 900 cmake -S "$BUILD_SOURCE" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=1 \
  -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 \
  -DCCBENCH_WAL=0 "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL;$GLOG_INSTALL" \
  "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH" \
  >"$STAGE/ccbench-configure.log" 2>&1
timeout 900 cmake --build "$BUILD_DIR" --target ycsb_silo.exe -j 48 \
  >"$STAGE/ccbench-build.log" 2>&1
BINARY="$BUILD_DIR/cc/silo/ycsb_silo.exe"
[[ -x "$BINARY" ]] || { echo "binary missing: $BINARY" >&2; exit 2; }
sha256sum "$BINARY" >"$STAGE/binary.sha256"
# trace build なので izanagi_trace シンボルは「在る」ことを必須にする (perf 側 nm guard の逆)。
# 注意: pipefail 下の `nm | grep -q` は grep 側の早期終了で nm が SIGPIPE(141) になり
# 偽赤を出す (job 872881 で実測)。パイプを使わずファイル経由で検査する
nm -C "$BINARY" >"$TMPDIR/binary.symbols"
grep -i izanagi_trace "$TMPDIR/binary.symbols" >"$STAGE/trace-symbols.txt" \
  || { echo "trace symbols MISSING in trace build" >&2; exit 2; }

PARSER="$HERE/parse_trace.py"
[[ -f "$PARSER" ]] || { echo "parser missing: $PARSER" >&2; exit 2; }

run_and_parse() {
  # $1=label $2=trace_dir $3=result_json、$4... = binary flags
  local label="$1" tdir="$2" out="$3"; shift 3
  mkdir "$tdir" "$tdir/log"
  ( cd "$tdir" && IZANAGI_TRACE_DIR="$tdir" timeout 120 "$@" ) \
    >"$STAGE/run-$label.stdout" 2>"$STAGE/run-$label.stderr"
  local commits
  # 最初のマッチで sed 自身が quit する (pipefail 下で head へのパイプを作らない)
  commits=$(sed -n '/^commit_counts_:/{s/[^0-9]*\([0-9][0-9]*\).*/\1/p;q}' \
    "$STAGE/run-$label.stdout")
  [[ -n "$commits" ]] || { echo "$label: commit_counts_ not found in stdout" >&2; exit 2; }
  du -sb "$tdir" >"$STAGE/trace-size-$label.txt"
  timeout 600 "$PY" "$PARSER" "$tdir" "$out" --expect-commits "$commits"
  rm -rf "$tdir"
}

# ---- (iv) 生死確認 (DW-G01): 小規模 legacy CorrectnessWorkload で parser を検証 ----
run_and_parse smoke "$TMPDIR/trace-smoke" "$STAGE/smoke-result.json" \
  "$BINARY" -ycsb_tuple_num=200 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 \
  -ycsb_rmw=true -ycsb_max_ope=5 -thread_num=4 -extime=1 -clocks_per_us=2100

# ---- (v) 本測定: S2 構成 verbatim (S2_FLAGS + extime=3、pegasus 登録 clocks=2100) ----
cat /proc/loadavg >"$STAGE/loadavg-before-s2.txt"
ps -eo user,pid,pcpu,comm --sort=-pcpu | head -20 >"$STAGE/ps-before-s2.txt" || true
run_and_parse s2 "$TMPDIR/trace-s2" "$STAGE/result.json" \
  "$BINARY" -ycsb_tuple_num=1000000 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 \
  -ycsb_rmw=false -ycsb_max_ope=10 -thread_num=48 -extime=3 -clocks_per_us=2100

echo "date_end: $(date -Is)" >>"$STAGE/env.txt"
echo "OK" >"$STAGE/status.txt"
