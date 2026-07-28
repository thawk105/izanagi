#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=01:00:00
#PBS -b 1

# izanagi [T-139] 劣化梯子の生死 probe — gap leg (使い捨て、DW-G01)。
# stock / candidate A (CAS gate) / candidate B (commit gate) を同一計算ノードで
# trace-disabled build し、2 workload x 5 reps interleaved で throughput の方向を測る。
# probe 値であり headline 非混入 (runbook §7)。git 非依存 (cp + patch -p1)。
set -u
set -o pipefail

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" ]] || { echo "need PBS env" >&2; exit 2; }
REPO=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
JOB_TAG=${PBS_JOBID//:/_}
OUT="$REPO/output/env/pegasus/t139-probe/$JOB_TAG"
mkdir -p "$REPO/output/env/pegasus/t139-probe" || exit 2
mkdir "$OUT" || { echo "create-only violated: $OUT" >&2; exit 2; }
PATCH="$REPO/output/env/pegasus/t139-probe/t139-probe-degradation.patch"
[[ -s "$PATCH" ]] || { echo "patch missing: $PATCH" >&2; exit 2; }

# 単独性の記録 (Exclusive submit=OFF: 専有保証なし → 実測記録、runbook §1/§7)
hostname -f > "$OUT/node.txt"
uptime > "$OUT/loadavg-before.txt"
pgrep -a -f 'ycsb_.*\.exe' > "$OUT/pgrep-ycsb.txt"; echo "pgrep_rc=$?" >> "$OUT/pgrep-ycsb.txt"
gcc --version | head -1 > "$OUT/compiler.txt"; realpath "$(command -v g++)" >> "$OUT/compiler.txt"

STAGE="${TMPDIR:-/scr}/t139_$JOB_TAG"
mkdir -p "$STAGE" || exit 2
trap 'rm -rf "$STAGE"' EXIT

step() { echo "[$(date +%H:%M:%S)] $*" >> "$OUT/steps.log"; }

# gflags / glog static build (certify §iv と同作法、pinned source)
for dep in gflags glog; do
  extra=""
  [[ $dep == glog ]] && extra="-DWITH_GTEST=OFF -DWITH_UNWIND=OFF -DCMAKE_PREFIX_PATH=$STAGE/gflags-install"
  timeout 300 cmake -S "$HOME/github/$dep" -B "$STAGE/$dep-build" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
    $extra "-DCMAKE_INSTALL_PREFIX=$STAGE/$dep-install" > "$OUT/$dep-cfg.log" 2>&1 || exit 3
  timeout 300 cmake --build "$STAGE/$dep-build" -j 48 > "$OUT/$dep-build.log" 2>&1 || exit 3
  timeout 60 cmake --install "$STAGE/$dep-build" > /dev/null 2>&1 || exit 3
  step "$dep ok"
done

# ソース staging: stock = pristine copy / probe = copy + patch -p1
cp -a "$REPO/external/ccbench" "$STAGE/src-stock" || exit 4
rm -rf "$STAGE/src-stock/.git"
cp -a "$STAGE/src-stock" "$STAGE/src-probe" || exit 4
( cd "$STAGE/src-probe" && patch -p1 --forward ) < "$PATCH" > "$OUT/patch-apply.log" 2>&1 || exit 4
step "staging ok"

CFG_COMMON=(-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=0
  -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
  -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0
  "-DCMAKE_PREFIX_PATH=$STAGE/gflags-install;$STAGE/glog-install")
declare -A SRC=([stock]="$STAGE/src-stock" [A]="$STAGE/src-probe" [B]="$STAGE/src-probe")
declare -A MACRO=([stock]="" [A]="-DIZANAGI_T139_PROBE_CAS_GATE=1" [B]="-DIZANAGI_T139_PROBE_COMMIT_GATE=1")

for v in stock A B; do
  flags=(); [[ -n "${MACRO[$v]}" ]] && flags=("-DCMAKE_CXX_FLAGS=${MACRO[$v]}")
  timeout 600 cmake -S "${SRC[$v]}" -B "$STAGE/build-$v" "${CFG_COMMON[@]}" "${flags[@]}" \
    > "$OUT/build-$v-cfg.log" 2>&1 || exit 5
  timeout 900 cmake --build "$STAGE/build-$v" --target ycsb_silo.exe -j 48 \
    > "$OUT/build-$v.log" 2>&1 || exit 5
  nm -C "$STAGE/build-$v/cc/silo/ycsb_silo.exe" > "$STAGE/nm-$v.txt" 2>/dev/null
  probe_syms=$(grep -c izanagi_t139_probe "$STAGE/nm-$v.txt" || true)
  trace_syms=$(grep -c izanagi_trace "$STAGE/nm-$v.txt" || true)
  echo "$v probe_syms=$probe_syms trace_syms=$trace_syms" >> "$OUT/nm-witness.txt"
  if [[ $v == stock && $probe_syms -ne 0 ]] || [[ $v != stock && $probe_syms -eq 0 ]] \
     || [[ $trace_syms -ne 0 ]]; then echo "nm witness failed for $v" >&2; exit 5; fi
  step "build $v ok"
done

W1="-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=10000 -ycsb_max_ope=10 -thread_num=48 -extime=3"
W2="-ycsb_rratio=50 -ycsb_zipf_skew=0.5 -ycsb_tuple_num=100000 -ycsb_max_ope=10 -thread_num=48 -extime=3"
echo -e "workload\tvariant\trep\ttps" > "$OUT/summary.tsv"
for w in W1 W2; do
  wl_var=$w; wl=${!wl_var}
  for rep in 1 2 3 4 5; do
    for v in stock A B; do
      log="$OUT/run-$w-$v-$rep.txt"
      timeout 240 "$STAGE/build-$v/cc/silo/ycsb_silo.exe" $wl > "$log" 2>&1 || { echo "run failed: $w $v $rep" >&2; exit 6; }
      tps=$(grep -oP 'throughput\[tps\]:\s*\K[0-9]+' "$log" | head -1)
      [[ -n "$tps" ]] || { echo "no tps: $w $v $rep" >&2; exit 6; }
      echo -e "$w\t$v\t$rep\t$tps" >> "$OUT/summary.tsv"
    done
  done
  step "$w done"
done
uptime > "$OUT/loadavg-after.txt"
echo OK > "$OUT/status.txt"
