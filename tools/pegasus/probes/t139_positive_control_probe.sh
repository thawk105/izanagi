#!/bin/bash
set -euo pipefail

arg_count() {
  awk -v expected="$2" '$0 == expected { count++ } END { print count + 0 }' "$1"
}

arg_prefix_count() {
  awk -v prefix="$2" 'index($0, prefix) == 1 { count++ } END { print count + 0 }' "$1"
}

grep_count() {
  local file=$1 pattern=$2 value rc
  set +e
  value=$(grep -Ec "$pattern" "$file")
  rc=$?
  set -e
  (( rc == 0 || rc == 1 )) || return "$rc"
  printf '%s\n' "$value"
}

deadline_run() {
  local cap=$1 remaining limit
  shift
  remaining=$((IZANAGI_ABSOLUTE_DEADLINE_EPOCH - $(date +%s)))
  (( remaining > 0 )) || { step "absolute deadline exhausted"; exit 8; }
  limit=$cap
  (( limit < remaining )) || limit=$remaining
  timeout --foreground "$limit" "$@"
}

validate_compile_argv() {
  local file=$1 arm=$2 analysis=$3 mode1=0 modex=0
  [[ -s $file && $(arg_prefix_count "$file" -DTRACE=) -eq 1 &&
     $(arg_count "$file" -DTRACE=0) -eq 1 &&
     $(arg_prefix_count "$file" -DADD_ANALYSIS=) -eq 1 &&
     $(arg_count "$file" "-DADD_ANALYSIS=$analysis") -eq 1 ]] || return 1
  [[ $(arg_prefix_count "$file" -DIZANAGI_T139_PC_MODE1=) -le 1 &&
     $(arg_prefix_count "$file" -DIZANAGI_T139_PC_MODEX=) -le 1 ]] || return 1
  case $arm in
    stock) ;;
    mode1) mode1=1 ;;
    modeX) modex=1 ;;
    *) return 1 ;;
  esac
  [[ $(arg_count "$file" -DIZANAGI_T139_PC_MODE1=1) -eq $mode1 &&
     $(arg_count "$file" -DIZANAGI_T139_PC_MODEX=1) -eq $modex ]]
}

capture_compile_argv() {
  deadline_run 10 python3 -I -B - "$1" "$2" <<'PY'
import json
import os
import shlex
import sys

entries = json.load(open(sys.argv[1], encoding="utf-8"))
targets = {
    "transaction": ("/cc/silo/transaction.cc", "/CMakeFiles/ycsb_silo.exe.dir/transaction.cc.o"),
    "result": ("/common/result.cc", None),
    "util": ("/common/util.cc", None),
}
matches = {name: [] for name in targets}
for entry in entries:
    argv = entry.get("arguments") or shlex.split(entry["command"])
    source = os.path.realpath(os.path.join(entry["directory"], entry["file"]))
    output = entry.get("output")
    if output is None:
        output_args = [argv[index + 1] for index, arg in enumerate(argv[:-1]) if arg == "-o"]
        if len(output_args) != 1:
            raise SystemExit(f"compile entry output arguments: {len(output_args)}: {source}")
        output = output_args[0]
    output = os.path.realpath(os.path.join(entry["directory"], output))
    for name, (source_suffix, output_suffix) in targets.items():
        if source.endswith(source_suffix) and (output_suffix is None or output.endswith(output_suffix)):
            matches[name].append(argv)
for name, found in matches.items():
    if len(found) != 1:
        raise SystemExit(f"{name} compile entries: {len(found)}")
for name, found in matches.items():
    path = f"{sys.argv[2]}.{name}.argv"
    with open(path + ".tmp", "w", encoding="utf-8") as handle:
        for arg in found[0]:
            handle.write(arg + "\n")
    os.replace(path + ".tmp", path)
PY
}

validate_compile_set() {
  local prefix=$1 arm=$2 analysis=$3 component
  for component in transaction result util; do
    validate_compile_argv "$prefix.$component.argv" "$arm" "$analysis" || return 1
  done
}

append_compile_summary() {
  local arm=$1 prefix=$2 output=$3 component file trace analysis mode1 modex
  for component in transaction result util; do
    file="$prefix.$component.argv"
    if ! trace=$(arg_count "$file" -DTRACE=0) ||
       ! analysis=$(arg_count "$file" -DADD_ANALYSIS=1) ||
       ! mode1=$(arg_count "$file" -DIZANAGI_T139_PC_MODE1=1) ||
       ! modex=$(arg_count "$file" -DIZANAGI_T139_PC_MODEX=1); then
      return 1
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$arm" "$component" \
      "$trace" "$analysis" "$mode1" "$modex" >>"$output"
  done
}

validate_liveness() {
  awk -F '\t' '
    NR == 1 {
      if (NF != 5 || $1 != "workload" || $2 != "arm" ||
          $3 != "window" || $4 != "worker" || $5 != "committed") bad=1
      next
    }
    {
      rows++
      if (NF != 5 || ($1 != "W1" && $1 != "W2") ||
          ($2 != "stock" && $2 != "mode1" && $2 != "modeX") ||
          ($3 != "1" && $3 != "2") || $4 !~ /^[0-9]+$/ ||
          $4 < 0 || $4 > 47 || $5 != "1") { bad=1; next }
      count[$1 SUBSEP $2 SUBSEP $3 SUBSEP $4]++
    }
    END {
      if (rows != 576) bad=1
      for (w=1; w<=2; w++) for (a=1; a<=3; a++)
        for (window=1; window<=2; window++) for (worker=0; worker<48; worker++) {
          arm=(a==1 ? "stock" : (a==2 ? "mode1" : "modeX"))
          if (count["W" w SUBSEP arm SUBSEP window SUBSEP worker] != 1) bad=1
        }
      exit bad ? 1 : 0
    }' "$1"
}

validate_throughput() {
  local input=$1 output=$2
  awk -F '\t' '
    BEGIN { structural=1 }
    NR == 1 {
      if (NF != 4 || $1 != "workload" || $2 != "arm" ||
          $3 != "rep" || $4 != "throughput_tps") structural=0
      next
    }
    {
      rows++
      if (NF != 4 || ($1 != "W1" && $1 != "W2") ||
          ($2 != "stock" && $2 != "mode1" && $2 != "modeX") ||
          $3 !~ /^[1-5]$/ || $4 !~ /^[0-9]+$/) { structural=0; next }
      key=$1 SUBSEP $2 SUBSEP $3
      count[key]++
      arm_count[$1 SUBSEP $2]++
      value=$4 + 0
      if (arm_count[$1 SUBSEP $2] == 1 || value < lo[$1 SUBSEP $2])
        lo[$1 SUBSEP $2]=value
      if (arm_count[$1 SUBSEP $2] == 1 || value > hi[$1 SUBSEP $2])
        hi[$1 SUBSEP $2]=value
    }
    END {
      if (rows != 30) structural=0
      for (w=1; w<=2; w++) for (a=1; a<=3; a++) for (rep=1; rep<=5; rep++) {
        arm=(a==1 ? "stock" : (a==2 ? "mode1" : "modeX"))
        if (count["W" w SUBSEP arm SUBSEP rep] != 1) structural=0
      }
      all=structural
      print "scope\tengineering_screen_J1_uncalibrated_nonqualification"
      print "row_structure\texact_30_cells\t" structural
      for (w=1; w<=2; w++) {
        name="W" w
        separated=(arm_count[name SUBSEP "mode1"] == 5 &&
          arm_count[name SUBSEP "modeX"] == 5 &&
          arm_count[name SUBSEP "stock"] == 5 &&
          hi[name SUBSEP "mode1"] < lo[name SUBSEP "modeX"] &&
          hi[name SUBSEP "modeX"] < lo[name SUBSEP "stock"])
        print name "\tall_samples_mode1_lt_modeX_lt_stock\t" separated
        if (!separated) all=0
      }
      print "all_workloads\tall_samples_mode1_lt_modeX_lt_stock\t" all
      exit all ? 0 : 1
    }' "$input" >"$output"
}

self_check() {
  SELF_TMP=$(mktemp -d "${TMPDIR:-/tmp}/t139-self-check.XXXXXX")
  local self_tmp=$SELF_TMP
  trap 'rm -rf -- "$SELF_TMP"' EXIT

  printf 'workload\tarm\trep\tthroughput_tps\n' >"$self_tmp/throughput-good.tsv"
  local workload arm rep base
  for workload in W1 W2; do
    for arm in mode1 modeX stock; do
      case $arm in mode1) base=100;; modeX) base=200;; stock) base=300;; esac
      for rep in 1 2 3 4 5; do
        printf '%s\t%s\t%s\t%s\n' "$workload" "$arm" "$rep" "$((base + rep))" \
          >>"$self_tmp/throughput-good.tsv"
      done
    done
  done
  awk -F '\t' 'BEGIN{OFS="\t"} NR==2{$4=500} {print}' \
    "$self_tmp/throughput-good.tsv" >"$self_tmp/throughput-verdict-bad.tsv"
  cp "$self_tmp/throughput-good.tsv" "$self_tmp/throughput-row-bad.tsv"
  printf 'W1\tmode1\t1\t101\n' >>"$self_tmp/throughput-row-bad.tsv"

  printf 'workload\tarm\twindow\tworker\tcommitted\n' >"$self_tmp/liveness-good.tsv"
  for workload in W1 W2; do for arm in stock mode1 modeX; do
    for window in 1 2; do for worker in $(seq 0 47); do
      printf '%s\t%s\t%s\t%s\t1\n' "$workload" "$arm" "$window" "$worker" \
        >>"$self_tmp/liveness-good.tsv"
    done; done
  done; done
  head -n 576 "$self_tmp/liveness-good.tsv" >"$self_tmp/liveness-bad.tsv"

  IZANAGI_ABSOLUTE_DEADLINE_EPOCH=$(( $(date +%s) + 60 ))
  python3 -I -B - "$self_tmp/compile-good.json" <<'PY'
import json
import sys

common = ["g++", "-DTRACE=0", "-DADD_ANALYSIS=0", "-DIZANAGI_T139_PC_MODEX=1"]
entries = []
for target in ("ycsb", "tpcc", "bomb", "sbomb"):
    entries.append({
        "directory": "/build/cc/silo",
        "file": "/src/cc/silo/transaction.cc",
        "arguments": common + ["-o", f"CMakeFiles/{target}_silo.exe.dir/transaction.cc.o", "-c", "/src/cc/silo/transaction.cc"],
    })
for source in ("result", "util"):
    entries.append({
        "directory": "/build",
        "file": f"/src/common/{source}.cc",
        "arguments": common + ["-o", f"CMakeFiles/ccbench_common.dir/common/{source}.cc.o", "-c", f"/src/common/{source}.cc"],
    })
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(entries, handle)
PY
  python3 -I -B - "$self_tmp/compile-good.json" \
    "$self_tmp/compile-missing.json" "$self_tmp/compile-duplicate.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    entries = json.load(handle)
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(entries[1:], handle)
with open(sys.argv[3], "w", encoding="utf-8") as handle:
    json.dump([entries[0], *entries], handle)
PY

  validate_throughput "$self_tmp/throughput-good.tsv" "$self_tmp/verdict-good.tsv"
  printf 'verdict\tpositive\taccepted\n'
  if validate_throughput "$self_tmp/throughput-verdict-bad.tsv" "$self_tmp/verdict-bad.tsv"; then
    return 1
  fi
  printf 'verdict\tnegative\trejected\n'
  validate_throughput "$self_tmp/throughput-good.tsv" "$self_tmp/row-good.tsv"
  printf 'row_structure\tpositive\taccepted\n'
  if validate_throughput "$self_tmp/throughput-row-bad.tsv" "$self_tmp/row-bad.tsv"; then
    return 1
  fi
  printf 'row_structure\tnegative\trejected\n'
  validate_liveness "$self_tmp/liveness-good.tsv"
  printf 'liveness\tpositive\taccepted\n'
  if validate_liveness "$self_tmp/liveness-bad.tsv"; then return 1; fi
  printf 'liveness\tnegative\trejected\n'
  capture_compile_argv "$self_tmp/compile-good.json" "$self_tmp/compile-good"
  validate_compile_set "$self_tmp/compile-good" modeX 0
  printf 'compile_json_four_transaction_entries\tpositive\taccepted\n'
  if capture_compile_argv "$self_tmp/compile-missing.json" \
      "$self_tmp/compile-missing" 2>/dev/null; then
    return 1
  fi
  printf 'compile_json_ycsb_missing\tnegative\trejected\n'
  if capture_compile_argv "$self_tmp/compile-duplicate.json" \
      "$self_tmp/compile-duplicate" 2>/dev/null; then
    return 1
  fi
  printf 'compile_json_ycsb_duplicate\tnegative\trejected\n'
}

if [[ ${1:-} == --self-check ]]; then
  [[ $# -eq 1 ]]
  self_check
  exit 0
fi

[[ $# -eq 1 && -n ${IZANAGI_PROBE_STAGE:-} &&
   -n ${IZANAGI_ABSOLUTE_DEADLINE_EPOCH:-} &&
   -n ${IZANAGI_DEPENDENCY_WITNESS:-} && -n ${IZANAGI_PROBE_BUNDLE:-} &&
   -n ${IZANAGI_CONSUMER_COPY_WITNESS:-} &&
   -n ${IZANAGI_CCBENCH_SNAPSHOT:-} && -n ${IZANAGI_RUN_COMMIT:-} &&
   -n ${IZANAGI_CCBENCH_PIN:-} && -n ${IZANAGI_PREREGISTRATION_BLOB:-} &&
   -n ${IZANAGI_RUNTIME_PBS_SHA256:-} &&
   -n ${IZANAGI_T139_STATE_DIR:-} ]] || exit 2
STAGE=$(realpath -e "$IZANAGI_PROBE_STAGE")
BUNDLE=$(realpath -e "$IZANAGI_PROBE_BUNDLE")
CCBENCH_SNAPSHOT=$(realpath -e "$IZANAGI_CCBENCH_SNAPSHOT")
PREREGISTRATION=$(realpath -e "$IZANAGI_PREREGISTRATION_BLOB")
STATE_DIR=$(realpath -e "$IZANAGI_T139_STATE_DIR")
OUT=$1
PATCH="$BUNDLE/t139_positive_control.patch"
POLICY="$BUNDLE/policy.json"
[[ -s $PATCH && -s $POLICY && -d $CCBENCH_SNAPSHOT &&
   -d ${IZANAGI_THIRDPARTY_SOURCE_ROOT:-} && -s $IZANAGI_DEPENDENCY_WITNESS &&
   -s $IZANAGI_CONSUMER_COPY_WITNESS &&
   -s $PREREGISTRATION && -d $OUT && $IZANAGI_RUN_COMMIT =~ ^[0-9a-f]{40}$ &&
   $IZANAGI_CCBENCH_PIN =~ ^[0-9a-f]{40}$ &&
   $IZANAGI_RUNTIME_PBS_SHA256 =~ ^[0-9a-f]{64}$ ]] || exit 2
exec 3>>"$OUT/steps.log"
unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS CMAKE_TOOLCHAIN_FILE

step() { printf '[%(%FT%TZ)T] %s\n' -1 "$*" >&3; }

write_state_file() {
  local name=$1 value=$2 detail=$3 tmp
  tmp="$STATE_DIR/.$name.$$"
  printf 'state\t%s\ndetail\t%s\nrun_commit\t%s\n' \
    "$value" "$detail" "$IZANAGI_RUN_COMMIT" >"$tmp"
  mv -f "$tmp" "$STATE_DIR/$name"
}

terminal_reject() {
  local state=$1 detail=$2 rc=$3
  write_state_file terminal-state.tsv "$state" "$detail"
  exit "$rc"
}

JOB_SID=$(ps -o sid= -p $$ | tr -d ' ')
limited_check() {
  local label=$1 phase=$2 snapshot
  snapshot="$OUT/limited-$label-$phase-processes.txt"
  ps -eo pid=,ppid=,sid=,psr=,stat=,comm=,args= |
    awk -v sid="$JOB_SID" '$3 != sid' >"$snapshot"
  {
    taskset -pc $$
    sed -n '/^Cpus_allowed_list:/p' /proc/self/status
  } >"$OUT/limited-$label-$phase-affinity.txt"
  LIMITED_LOAD=$(cut -d' ' -f1 /proc/loadavg)
  printf 'load1=%s\n' "$LIMITED_LOAD" >>"$OUT/limited-$label-$phase-affinity.txt"
  awk -v value="$LIMITED_LOAD" 'BEGIN { exit !(value <= 48.0) }' || {
    step "limited screen load competition"; exit 7;
  }
  if awk '$0 ~ /ycsb_.*\.exe/ { found=1; print } END { exit !found }' \
      "$snapshot" >>"$OUT/limited-$label-$phase-affinity.txt"; then
    step "limited screen foreign ycsb process"; exit 7
  fi
}

cp "$IZANAGI_DEPENDENCY_WITNESS" "$OUT/dependency-witness.tsv"
cp "$PREREGISTRATION" "$OUT/preregistration.md"
declare -A BUNDLE_SHA
for file in t139_positive_control.patch t139_positive_control_probe.sh \
    t139_positive_control_probe.pbs; do
  BUNDLE_SHA[$file]=$(sha256sum "$BUNDLE/$file" | awk '{print $1}')
done
policy_sha=$(sha256sum "$POLICY" | awk '{print $1}')
preregistration_sha=$(sha256sum "$PREREGISTRATION" | awk '{print $1}')
{
  printf 'field\tvalue\n'
  printf 'study\tengineering_screen_J1_uncalibrated_nonqualification\n'
  printf 'repo_head\t%s\n' "$IZANAGI_RUN_COMMIT"
  printf 'ccbench_head\t%s\n' "$IZANAGI_CCBENCH_PIN"
  printf 'runtime_pbs_sha256\t%s\n' "$IZANAGI_RUNTIME_PBS_SHA256"
  for file in t139_positive_control.patch t139_positive_control_probe.sh t139_positive_control_probe.pbs; do
    printf '%s_sha256\t%s\n' "$file" "${BUNDLE_SHA[$file]}"
  done
  printf 'policy_sha256\t%s\n' "$policy_sha"
  printf 'preregistration_sha256\t%s\n' "$preregistration_sha"
} >"$OUT/preregistration-witness.tsv"

# Driver inner caps: writable copies/identity/patch 180 + six
# configure/build/receipt groups 1500 + six liveness runs 180 + thirty
# performance runs 450 = 2310 seconds; PBS
# gives the whole driver a 2400-second cap.
make_writable_consumer_copy() {
  local destination=$1 name=$2
  deadline_run 75 bash -c '
    set -euo pipefail
    snapshot=$1; consumer=$2; witness=$3; name=$4
    cp -a "$snapshot" "$consumer"
    chmod -R u+w "$consumer"
    diff --brief --recursive --no-dereference "$snapshot" "$consumer" >/dev/null
    printf "%s\t%s\t%s\t1\n" "$name" "$snapshot" "$consumer" >>"$witness"
  ' _ "$CCBENCH_SNAPSHOT" "$destination" "$IZANAGI_CONSUMER_COPY_WITNESS" \
    "$name"
}
make_writable_consumer_copy "$STAGE/src-stock" ccbench_stock
make_writable_consumer_copy "$STAGE/src-probe" ccbench_probe
cp "$IZANAGI_CONSUMER_COPY_WITNESS" "$OUT/consumer-copy-witness.tsv"
deadline_run 30 patch -d "$STAGE/src-probe" -p1 --forward -i "$PATCH" \
  >"$OUT/patch-apply.log"

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
declare -A SRC=([stock]="$STAGE/src-stock" [mode1]="$STAGE/src-probe"
 [modeX]="$STAGE/src-probe" [stock-live]="$STAGE/src-probe"
 [mode1-live]="$STAGE/src-probe" [modeX-live]="$STAGE/src-probe")
declare -A DEF=([stock]="" [mode1]="-DIZANAGI_T139_PC_MODE1=1"
 [modeX]="-DIZANAGI_T139_PC_MODEX=1" [stock-live]=""
 [mode1-live]="-DIZANAGI_T139_PC_MODE1=1"
 [modeX-live]="-DIZANAGI_T139_PC_MODEX=1")
printf 'arm\tsource\ttrace_zero_count\tadd_analysis_one_count\tmode1_count\tmodeX_count\n' \
  >"$OUT/compile-argv.tsv"
printf 'arm\tmode1_mutex_symbols\tmodeX_mutex_symbols\ttrace_symbols\n' \
  >"$OUT/nm-witness.tsv"
for arm in stock mode1 modeX stock-live mode1-live modeX-live; do
  analysis=0
  [[ $arm == *-live ]] && analysis=1
  base_arm=${arm%-live}
  extra=("-DCCBENCH_ADD_ANALYSIS=$analysis" "-DCMAKE_CXX_FLAGS=${DEF[$arm]}")
  deadline_run 60 cmake -S "${SRC[$arm]}" -B "$STAGE/build-$arm" \
    "${COMMON[@]}" "${extra[@]}" >"$OUT/configure-$arm.log" 2>&1
  deadline_run 180 cmake --build "$STAGE/build-$arm" --target ycsb_silo.exe -j 48 \
    >"$OUT/build-$arm.log" 2>&1
  argv_prefix="$OUT/compile-argv-$arm"
  capture_compile_argv "$STAGE/build-$arm/compile_commands.json" "$argv_prefix"
  validate_compile_set "$argv_prefix" "$base_arm" "$analysis" || \
    terminal_reject correctness_reject "compile_argv_mismatch:$arm" 10
  grep -Fx "CCBENCH_TRACE:STRING=0" "$STAGE/build-$arm/CMakeCache.txt" >/dev/null || \
    terminal_reject correctness_reject "trace_cache_mismatch:$arm" 10
  grep -Fx "CCBENCH_ADD_ANALYSIS:STRING=$analysis" \
    "$STAGE/build-$arm/CMakeCache.txt" >/dev/null || \
    terminal_reject correctness_reject "analysis_cache_mismatch:$arm" 10
  append_compile_summary "$arm" "$argv_prefix" "$OUT/compile-argv.tsv" || \
    terminal_reject correctness_reject "compile_summary_failed:$arm" 10

  bin="$STAGE/build-$arm/cc/silo/ycsb_silo.exe"
  nm -a "$bin" >"$OUT/nm-$arm.txt"
  if ! m1=$(grep_count "$OUT/nm-$arm.txt" \
      ' [BbDd] _ZN29izanagi_t139_positive_control4gateE$') ||
     ! mx=$(grep_count "$OUT/nm-$arm.txt" \
      ' [BbDd] _ZN29izanagi_t139_positive_control5gatesE$') ||
     ! tr=$(grep_count "$OUT/nm-$arm.txt" 'izanagi_trace'); then
    terminal_reject correctness_reject "nm_witness_read_failed:$arm" 10
  fi
  printf '%s\t%s\t%s\t%s\n' "$arm" "$m1" "$mx" "$tr" >>"$OUT/nm-witness.tsv"
  [[ $tr -eq 0 &&
     ( $base_arm == stock && $m1 -eq 0 && $mx -eq 0 ||
       $base_arm == mode1 && $m1 -ge 1 && $mx -eq 0 ||
       $base_arm == modeX && $m1 -eq 0 && $mx -ge 1 ) ]] || \
    terminal_reject correctness_reject "nm_witness_mismatch:$arm" 10
done

W1=(-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=10000
 -ycsb_max_ope=10 -thread_num=48 -extime=3)
W2=(-ycsb_rratio=50 -ycsb_zipf_skew=0.5 -ycsb_tuple_num=100000
 -ycsb_max_ope=10 -thread_num=48 -extime=3)
printf 'run\tpre_load1\tpost_load1\tpass\n' >"$OUT/limited-screen.tsv"
printf 'workload\tarm\twindow\tworker\tcommitted\n' >"$OUT/liveness.tsv"
for workload in W1 W2; do
  [[ $workload == W1 ]] && args=("${W1[@]}") || args=("${W2[@]}")
  for arm in stock mode1 modeX; do
    label="live-$workload-$arm"
    limited_check "$label" pre; pre_load=$LIMITED_LOAD
    log="$OUT/liveness-$workload-$arm.log"
    if ! deadline_run 30 "$STAGE/build-$arm-live/cc/silo/ycsb_silo.exe" \
        "${args[@]}" >"$log" 2>&1; then
      terminal_reject liveness_reject "liveness_run_failed:$workload:$arm" 11
    fi
    limited_check "$label" post; post_load=$LIMITED_LOAD
    printf '%s\t%s\t%s\t1\n' "$label" "$pre_load" "$post_load" \
      >>"$OUT/limited-screen.tsv"
    for window in 1 2; do for worker in $(seq 0 47); do
      [[ $(grep -c "^izanagi_t139_pc.window\[$window\].worker\[$worker\]=1$" \
        "$log" || true) -eq 1 ]] || \
        terminal_reject liveness_reject \
          "liveness_cell_missing_or_duplicate:$workload:$arm:$window:$worker" 11
      printf '%s\t%s\t%s\t%s\t1\n' "$workload" "$arm" "$window" "$worker" \
        >>"$OUT/liveness.tsv"
    done; done
  done
done
validate_liveness "$OUT/liveness.tsv" || \
  terminal_reject liveness_reject "liveness_table_invalid" 11

write_state_file phase.tsv performance_started "before_first_performance_run"

printf 'ordinal\tworkload\trep\tposition\tarm\n' >"$OUT/order.tsv"
printf 'workload\tarm\trep\tthroughput_tps\n' >"$OUT/throughput.tsv"
printf 'ordinal\tworkload\tarm\trep\tattempt_rate_per_s\tattempt_reason\tabort_rate\tabort_reason\n' \
  >"$OUT/diagnostics.tsv"
ordinal=0
for workload in W1 W2; do
  [[ $workload == W1 ]] && args=("${W1[@]}") || args=("${W2[@]}")
  for rep in 1 2 3 4 5; do
    case $rep in
      1) schedule=(stock mode1 modeX) ;;
      2) schedule=(mode1 modeX stock) ;;
      3) schedule=(modeX stock mode1) ;;
      4) schedule=(stock modeX mode1) ;;
      5) schedule=(modeX mode1 stock) ;;
    esac
    position=0
    for arm in "${schedule[@]}"; do
      ordinal=$((ordinal + 1)); position=$((position + 1))
      printf '%s\t%s\t%s\t%s\t%s\n' "$ordinal" "$workload" "$rep" \
        "$position" "$arm" >>"$OUT/order.tsv"
      label="run-$ordinal-$workload-$arm-r$rep"
      limited_check "$label" pre; pre_load=$LIMITED_LOAD
      log="$OUT/$label.log"
      deadline_run 15 "$STAGE/build-$arm/cc/silo/ycsb_silo.exe" \
        "${args[@]}" >"$log" 2>&1
      limited_check "$label" post; post_load=$LIMITED_LOAD
      printf '%s\t%s\t%s\t1\n' "$label" "$pre_load" "$post_load" \
        >>"$OUT/limited-screen.tsv"
      if ! tps=$(sed -n \
          's/^throughput\[tps\]:[[:space:]]*\([0-9][0-9]*\)$/\1/p' "$log"); then
        terminal_reject post_performance_failure "throughput_read_failed:$label" 12
      fi
      [[ $tps =~ ^[0-9]+$ ]] || \
        terminal_reject post_performance_failure "throughput_parse_failed:$label" 12
      printf '%s\t%s\t%s\t%s\n' "$workload" "$arm" "$rep" "$tps" \
        >>"$OUT/throughput.tsv"
      diagnostic_commands_ok=1
      if ! commits=$(sed -n \
          's/^commit_counts_:[[:space:]]*\([0-9][0-9]*\)$/\1/p' "$log"); then
        commits=
        diagnostic_commands_ok=0
      fi
      if ! aborts=$(sed -n \
          's/^abort_counts_:[[:space:]]*\([0-9][0-9]*\)$/\1/p' "$log"); then
        aborts=
        diagnostic_commands_ok=0
      fi
      abort_rate_command_ok=1
      if ! abort_rate=$(sed -n \
          's/^abort_rate:[[:space:]]*\([0-9][0-9]*\.[0-9][0-9]*\)$/\1/p' \
          "$log"); then
        abort_rate=
        abort_rate_command_ok=0
      fi
      attempt_reason=ok
      if [[ $diagnostic_commands_ok -eq 1 && $commits =~ ^[0-9]+$ &&
            $aborts =~ ^[0-9]+$ ]]; then
        if ! attempt_rate=$(awk -v commits="$commits" -v aborts="$aborts" \
            'BEGIN { printf "%.6f", (commits + aborts) / 3.0 }'); then
          attempt_rate=NA
          attempt_reason=calculation_failed
        fi
      else
        attempt_rate=NA
        if [[ $diagnostic_commands_ok -eq 1 ]]; then
          attempt_reason=commit_or_abort_count_missing_nonexact
        else
          attempt_reason=diagnostic_read_failed
        fi
      fi
      abort_reason=ok
      if [[ $abort_rate_command_ok -ne 1 ]]; then
        abort_rate=NA
        abort_reason=diagnostic_read_failed
      elif [[ ! $abort_rate =~ ^[0-9]+\.[0-9]+$ ]]; then
        abort_rate=NA
        abort_reason=abort_rate_missing_nonexact
      fi
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$ordinal" "$workload" \
        "$arm" "$rep" "$attempt_rate" "$attempt_reason" "$abort_rate" \
        "$abort_reason" >>"$OUT/diagnostics.tsv"
    done
  done
done

awk -F '\t' 'NR==1 { next } { rows++; if ($4 != 1 || seen[$1]++) bad=1 }
  END { exit !(rows == 36 && !bad) }' "$OUT/limited-screen.tsv" || \
  terminal_reject post_performance_failure "limited_screen_table_invalid" 12
if validate_throughput "$OUT/throughput.tsv" "$OUT/verdict.tsv"; then
  write_state_file terminal-state.tsv verdict_true "exact_primary_verdict_true"
  step "probe complete: exact verdict true"
else
  if grep -Fx $'row_structure\texact_30_cells\t1' "$OUT/verdict.tsv" >/dev/null; then
    write_state_file terminal-state.tsv verdict_false "exact_primary_verdict_false"
    step "probe complete: exact verdict false (terminal, scheduler rc=0)"
  else
    terminal_reject post_performance_failure "throughput_table_invalid" 12
  fi
fi
