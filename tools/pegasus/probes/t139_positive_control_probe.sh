#!/bin/bash
set -euo pipefail
[[ $# -eq 1 && -n "${IZANAGI_REPO_ROOT:-}" && -n "${IZANAGI_PROBE_STAGE:-}" ]] || exit 2
REPO=$(realpath -e "$IZANAGI_REPO_ROOT"); STAGE=$(realpath -e "$IZANAGI_PROBE_STAGE"); OUT=$1
PATCH="$REPO/tools/pegasus/probes/t139_positive_control.patch"
[[ -s "$PATCH" && -d "${IZANAGI_THIRDPARTY_SOURCE_ROOT:-}" ]] || exit 2
mkdir "$OUT"; exec 3>>"$OUT/steps.log"
unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS CMAKE_TOOLCHAIN_FILE
step() { printf '[%(%FT%TZ)T] %s\n' -1 "$*" >&3; }
solo() {
  load1=$(cut -d' ' -f1 /proc/loadavg); printf 'load1=%s ' "$load1" >>"$OUT/solo-checks.txt"; uptime >>"$OUT/solo-checks.txt"
  awk -v value="$load1" 'BEGIN { exit !(value <= 48.0) }' || { step "load competition"; exit 7; }
  if pgrep -a -f 'ycsb_.*\.exe' >>"$OUT/solo-checks.txt"; then step "competition"; exit 7; fi
  printf 'ycsb_processes=0\n' >>"$OUT/solo-checks.txt"
}
cp -a "$REPO/external/ccbench" "$STAGE/src-stock"
cp -a "$STAGE/src-stock" "$STAGE/src-probe"
(cd "$STAGE/src-probe" && patch -p1 --forward) <"$PATCH" >"$OUT/patch-apply.log"
PREFIX="${IZANAGI_GFLAGS_INSTALL};${IZANAGI_GLOG_INSTALL}"
TP="$IZANAGI_THIRDPARTY_SOURCE_ROOT"
COMMON=(-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=0
 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0 -DCCBENCH_CCACHE=OFF
 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER_LAUNCHER= -DCMAKE_CXX_COMPILER_LAUNCHER=
 -DRULE_LAUNCH_COMPILE= -DCMAKE_TOOLCHAIN_FILE= "-DCMAKE_PREFIX_PATH=$PREFIX"
 "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$TP/masstree"
 "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$TP/mimalloc"
 "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$TP/googletest"
 "-DIZANAGI_GFLAGS_SRC_HEAD=$IZANAGI_GFLAGS_SRC_HEAD"
 "-DIZANAGI_GLOG_SRC_HEAD=$IZANAGI_GLOG_SRC_HEAD"
 "-DCMAKE_C_COMPILER=$(command -v gcc)" "-DCMAKE_CXX_COMPILER=$(command -v g++)")
declare -A SRC=([stock]="$STAGE/src-stock" [mode1]="$STAGE/src-probe" [mode2]="$STAGE/src-probe" [stock-live]="$STAGE/src-probe" [mode1-live]="$STAGE/src-probe" [mode2-live]="$STAGE/src-probe")
declare -A DEF=([stock]="" [mode1]="-DIZANAGI_T139_PC_MODE1=1" [mode2]="-DIZANAGI_T139_PC_MODE2=1" [stock-live]="" [mode1-live]="-DIZANAGI_T139_PC_MODE1=1" [mode2-live]="-DIZANAGI_T139_PC_MODE2=1")
printf 'arm\tmode1_symbols\tmode2_symbols\ttrace_symbols\n' >"$OUT/nm-witness.tsv"
for arm in stock mode1 mode2 stock-live mode1-live mode2-live; do
  extra=("-DCMAKE_CXX_FLAGS=${DEF[$arm]}")
  [[ $arm == *-live ]] && extra+=("-DCCBENCH_ADD_ANALYSIS=1")
  timeout 600 cmake -S "${SRC[$arm]}" -B "$STAGE/build-$arm" "${COMMON[@]}" "${extra[@]}" >"$OUT/configure-$arm.log" 2>&1
  timeout 900 cmake --build "$STAGE/build-$arm" --target ycsb_silo.exe -j 48 >"$OUT/build-$arm.log" 2>&1
  bin="$STAGE/build-$arm/cc/silo/ycsb_silo.exe"; nm -a "$bin" >"$OUT/nm-$arm.txt"
  m1=$(grep -c 'izanagi_t139_pc_mode1_identity' "$OUT/nm-$arm.txt" || true)
  m2=$(grep -c 'izanagi_t139_pc_mode2_identity' "$OUT/nm-$arm.txt" || true)
  tr=$(grep -c 'izanagi_trace' "$OUT/nm-$arm.txt" || true)
  printf '%s\t%s\t%s\t%s\n' "$arm" "$m1" "$m2" "$tr" >>"$OUT/nm-witness.tsv"
  [[ $tr -eq 0 && ( $arm == stock* && $m1 -eq 0 && $m2 -eq 0 || $arm == mode1* && $m1 -ge 1 && $m2 -eq 0 || $arm == mode2* && $m1 -eq 0 && $m2 -ge 1 ) ]] || exit 5
done
W1=(-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=10000 -ycsb_max_ope=10 -thread_num=48 -extime=3)
W2=(-ycsb_rratio=50 -ycsb_zipf_skew=0.5 -ycsb_tuple_num=100000 -ycsb_max_ope=10 -thread_num=48 -extime=3)
printf 'workload\tarm\tworker\tever_committed\n' >"$OUT/liveness.tsv"
for workload in W1 W2; do
  [[ $workload == W1 ]] && args=("${W1[@]}") || args=("${W2[@]}")
  for arm in stock mode1 mode2; do
    solo; log="$OUT/liveness-$workload-$arm.log"
    T139_PROBE_LIVENESS=1 timeout 240 "$STAGE/build-$arm-live/cc/silo/ycsb_silo.exe" "${args[@]}" >"$log" 2>&1
    for worker in $(seq 0 47); do
      [[ $(grep -c "^izanagi_t139_pc.worker\[$worker\]=1$" "$log" || true) -eq 1 ]] || exit 6
      printf '%s\t%s\t%s\t1\n' "$workload" "$arm" "$worker" >>"$OUT/liveness.tsv"
    done
  done
done
printf 'ordinal\tworkload\trep\tposition\tarm\n' >"$OUT/order.tsv"
printf 'workload\tarm\trep\tthroughput_tps\n' >"$OUT/throughput.tsv"; ordinal=0
for workload in W1 W2; do
  [[ $workload == W1 ]] && args=("${W1[@]}") || args=("${W2[@]}")
  for rep in 1 2 3 4 5; do
    position=0
    while read -r arm; do
      ordinal=$((ordinal+1)); position=$((position+1)); printf '%s\t%s\t%s\t%s\t%s\n' "$ordinal" "$workload" "$rep" "$position" "$arm" >>"$OUT/order.tsv"
      solo; log="$OUT/run-$ordinal-$workload-$arm-r$rep.log"
      timeout 240 "$STAGE/build-$arm/cc/silo/ycsb_silo.exe" "${args[@]}" >"$log" 2>&1
      tps=$(sed -n 's/^throughput\[tps\]:[[:space:]]*\([0-9][0-9]*\)$/\1/p' "$log")
      [[ $tps =~ ^[0-9]+$ ]] || exit 6
      printf '%s\t%s\t%s\t%s\n' "$workload" "$arm" "$rep" "$tps" >>"$OUT/throughput.tsv"
    done < <(shuf -e stock mode1 mode2)
  done
done
awk -F '\t' 'NR>1{w=$1;a=$2;t=$4;c[w,a]++; if(c[w,a]==1||t<lo[w,a])lo[w,a]=t; if(c[w,a]==1||t>hi[w,a])hi[w,a]=t} END{ok=1; for(n=1;n<=2;n++){w="W"n; cell=(c[w,"mode1"]==5&&c[w,"mode2"]==5&&c[w,"stock"]==5&&hi[w,"mode1"]<lo[w,"mode2"]&&hi[w,"mode2"]<lo[w,"stock"]); print w "\tall_samples_mode1_lt_mode2_lt_stock\t" cell; if(!cell)ok=0} print "all_workloads\tall_samples_mode1_lt_mode2_lt_stock\t" ok; exit !ok}' "$OUT/throughput.tsv" >"$OUT/verdict.tsv"
step "probe complete"
