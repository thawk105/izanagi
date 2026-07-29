#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=03:00:00

# T-141: trace-disabled stock Silo builds の perf region 分布を採取する。
# qsub は submit 側が行い、-v IZANAGI_ROOT=... を必ず渡す。
# T141_OUT_ROOT は必要なら同じ -v で上書きする。
set -uo pipefail
umask 077
export GIT_OPTIONAL_LOCKS=0

if [[ -z "${IZANAGI_ROOT:-}" ]]; then
  printf 'IZANAGI_ROOT is required (pass it with qsub -v)\n' >&2
  exit 2
fi
T141_OUT_ROOT=${T141_OUT_ROOT:-"$IZANAGI_ROOT/output/env/pegasus/profile/t141-directive-calibration"}
JOB_START_SECONDS=$SECONDS
WALLTIME_S=10800
FINALIZE_RESERVE_S=600
INTERNAL_DEADLINE_S=$((WALLTIME_S - FINALIZE_RESERVE_S))

JOB_DIR=""
JOB_DIR_CREATED=0
ARTIFACT_DIR=""
LOG_DIR=""
OUTPUT_DIR=""
CURRENT_STAGE="bootstrap"
failure_written=0

write_failure() {
  local rc=$1
  local stage=$2
  local reason=$3
  local write_rc=0

  if [[ "$failure_written" -ne 0 ]]; then
    return 0
  fi
  if [[ -z "$OUTPUT_DIR" || ! -d "$OUTPUT_DIR" ]]; then
    printf 'failure before output directory was available: stage=%s reason=%s rc=%s\n' \
      "$stage" "$reason" "$rc" >&2
    return 1
  fi
  python3 - "$OUTPUT_DIR/failure.json" "${PBS_JOBID:-unavailable}" \
    "$rc" "$stage" "$reason" <<'PY' || write_rc=$?
import json
import sys
import time

path, job_id, rc, stage, reason = sys.argv[1:]
payload = {
    "schema_version": "t141-region-profile-failure/v1",
    "pbs_jobid": job_id,
    "rc": int(rc),
    "stage": stage,
    "reason": reason,
    "recorded_epoch": int(time.time()),
}
try:
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
except FileExistsError:
    pass
PY
  if [[ "$write_rc" -eq 0 ]]; then
    failure_written=1
  else
    printf 'could not write failure.json (rc=%s): stage=%s reason=%s\n' \
      "$write_rc" "$stage" "$reason" >&2
  fi
  return "$write_rc"
}

fail() {
  local rc=$1
  local stage=$2
  local reason=$3

  if [[ "$rc" -eq 0 ]]; then
    rc=1
  fi
  write_failure "$rc" "$stage" "$reason" || true
  printf 'T-141 profile failed: stage=%s reason=%s rc=%s\n' \
    "$stage" "$reason" "$rc" >&2
  exit "$rc"
}

collect_build_logs() {
  local raw_log
  local copy_rc=0
  local -a build_logs=()

  if [[ ! -d "$LOG_DIR" || ! -d "$ARTIFACT_DIR" ]]; then
    return 0
  fi
  mkdir -p "$ARTIFACT_DIR/build-logs" || return $?
  shopt -s nullglob
  build_logs=(
    "$LOG_DIR"/*-configure.log
    "$LOG_DIR"/*-build.log
    "$LOG_DIR"/*-install.log
  )
  shopt -u nullglob
  for raw_log in "${build_logs[@]}"; do
    rsync -a "$raw_log" "$ARTIFACT_DIR/build-logs/" || copy_rc=$?
    if [[ "$copy_rc" -ne 0 ]]; then
      return "$copy_rc"
    fi
  done
  return 0
}

write_success() {
  local completed_at=$1

  python3 - "$OUTPUT_DIR/attestation.txt" "$OUTPUT_DIR/success.marker" \
    "$completed_at" <<'PY'
import os
import sys

attestation_path, marker_path, completed_at = sys.argv[1:]
attestation_tmp = attestation_path + ".complete.tmp"
marker_tmp = marker_path + ".tmp"
try:
    with open(attestation_path, encoding="utf-8") as source:
        attestation = source.read()
    with open(attestation_tmp, "x", encoding="utf-8") as target:
        target.write(attestation)
        target.write(f"completed_at={completed_at}\n")
    with open(marker_tmp, "x", encoding="utf-8") as marker:
        marker.write(f"completed_at={completed_at}\n")
    os.replace(attestation_tmp, attestation_path)
    try:
        os.replace(marker_tmp, marker_path)
    except BaseException:
        try:
            with open(attestation_tmp, "x", encoding="utf-8") as target:
                target.write(attestation)
            os.replace(attestation_tmp, attestation_path)
        except BaseException:
            try:
                os.unlink(marker_path)
            except FileNotFoundError:
                pass
        raise
finally:
    for path in (attestation_tmp, marker_tmp):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
PY
}

finalize() {
  local original_rc=$?
  local final_rc=$original_rc
  local action_rc=0
  local completed_at=""

  trap - EXIT
  trap - INT TERM HUP
  if [[ "$original_rc" -ne 0 && "$failure_written" -eq 0 ]]; then
    write_failure "$original_rc" "$CURRENT_STAGE" "unexpected shell exit" || true
  fi

  if [[ "$JOB_DIR_CREATED" -eq 1 ]]; then
    collect_build_logs || action_rc=$?
    if [[ "$action_rc" -ne 0 ]]; then
      write_failure "$action_rc" finalize "could not collect complete build logs" || true
      final_rc=$action_rc
    fi

    action_rc=0
    if [[ -d "$ARTIFACT_DIR" && -d "$OUTPUT_DIR" ]]; then
      rsync -a "$ARTIFACT_DIR/" "$OUTPUT_DIR/" || action_rc=$?
      if [[ "$action_rc" -ne 0 ]]; then
        write_failure "$action_rc" finalize "could not publish artifacts" || true
        final_rc=$action_rc
      fi
    fi

    action_rc=0
    case "$JOB_DIR" in
      /scr/*)
        rm -rf -- "$JOB_DIR" || action_rc=$?
        ;;
      *)
        action_rc=2
        ;;
    esac
    if [[ "$action_rc" -ne 0 ]]; then
      write_failure "$action_rc" cleanup "could not remove validated /scr job directory" || true
      final_rc=$action_rc
    fi
  fi

  if [[ "$final_rc" -eq 0 && "$original_rc" -eq 0 ]]; then
    completed_at=$(date --iso-8601=seconds) || action_rc=$?
    if [[ "$action_rc" -eq 0 ]]; then
      write_success "$completed_at" || action_rc=$?
    fi
    if [[ "$action_rc" -ne 0 ]]; then
      write_failure "$action_rc" finalize "could not write post-publish success marker" || true
      final_rc=$action_rc
    fi
  fi
  exit "$final_rc"
}

on_signal() {
  local signal=$1
  trap - INT TERM HUP
  fail 128 signal "received $signal"
}

trap finalize EXIT
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap 'on_signal HUP' HUP

run_logged() {
  local stage=$1
  local reason=$2
  local logfile=$3
  local rc=0
  shift 3

  CURRENT_STAGE=$stage
  "$@" >"$logfile" 2>&1 || rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" "$stage" "$reason"
  fi
}

attest() {
  local key=$1
  local value=$2
  local rc=0

  printf '%s=%s\n' "$key" "$value" >>"$ARTIFACT_DIR/attestation.txt" || rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" attestation "could not append $key"
  fi
}

shell_join() {
  local arg
  local joined=""
  local quoted

  for arg in "$@"; do
    printf -v quoted '%q' "$arg"
    if [[ -n "$joined" ]]; then
      joined+=" "
    fi
    joined+="$quoted"
  done
  printf '%s\n' "$joined"
}

ensure_deadline() {
  local stage=$1
  local required_s=$2
  local elapsed=$((SECONDS - JOB_START_SECONDS))

  if (( elapsed + required_s > INTERNAL_DEADLINE_S )); then
    fail 2 "$stage" \
      "insufficient time before internal deadline (elapsed=${elapsed}s required=${required_s}s deadline=${INTERNAL_DEADLINE_S}s)"
  fi
}

if [[ -z "${PBS_JOBID:-}" ]]; then
  printf 'PBS_JOBID is required\n' >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  printf 'unsafe PBS_JOBID: %s\n' "$PBS_JOBID" >&2
  exit 2
fi
if [[ -z "${PBS_ENVIRONMENT:-}" ]]; then
  if [[ -z "${PBS_NODEFILE:-}" || ! -f "$PBS_NODEFILE" ]]; then
    printf 'PBS_NODEFILE or PBS_ENVIRONMENT is required for batch-node execution\n' >&2
    exit 2
  fi
fi
case "$T141_OUT_ROOT" in
  /*) ;;
  *)
    printf 'T141_OUT_ROOT must be absolute: %s\n' "$T141_OUT_ROOT" >&2
    exit 2
    ;;
esac
if ! command -v realpath >/dev/null 2>&1; then
  printf 'realpath is required to validate T141_OUT_ROOT\n' >&2
  exit 2
fi
T141_OUT_ROOT_REAL=$(realpath -m "$T141_OUT_ROOT")
rc=$?
if [[ "$rc" -ne 0 || -z "$T141_OUT_ROOT_REAL" ]]; then
  printf 'T141_OUT_ROOT could not be normalized: %s\n' "$T141_OUT_ROOT" >&2
  exit 2
fi
case "$T141_OUT_ROOT_REAL" in
  /scr|/scr/*)
    printf 'T141_OUT_ROOT must not resolve under /scr: %s\n' "$T141_OUT_ROOT_REAL" >&2
    exit 2
    ;;
esac
T141_OUT_ROOT=$T141_OUT_ROOT_REAL
JOB_ID_SAFE=${PBS_JOBID//:/_}
OUTPUT_DIR="$T141_OUT_ROOT/$JOB_ID_SAFE"

CURRENT_STAGE="output"
mkdir -p "$T141_OUT_ROOT"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" output "could not create T141_OUT_ROOT"
fi
mkdir "$OUTPUT_DIR"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" output "job output directory already exists or cannot be created"
fi

JOB_DIR="/scr/$JOB_ID_SAFE"
CURRENT_STAGE="scratch"
mkdir "$JOB_DIR"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" scratch "job scratch directory already exists or cannot be created"
fi
JOB_DIR_CREATED=1
ARTIFACT_DIR="$JOB_DIR/artifacts"
LOG_DIR="$JOB_DIR/logs"
export TMPDIR="$JOB_DIR/tmp"
mkdir "$ARTIFACT_DIR" "$LOG_DIR" "$TMPDIR"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" scratch "could not create scratch artifact/log/temp directories"
fi

for required_command in python3 git rsync cmake gcc g++ realpath timeout pgrep \
  awk sed grep sha256sum sleep ps lscpu sort wc tar date hostname uname; do
  command -v "$required_command" >/dev/null 2>&1
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" preflight "required command is unavailable: $required_command"
  fi
done

CURRENT_STAGE="preflight"
case "$IZANAGI_ROOT" in
  /*) ;;
  *) fail 2 preflight "IZANAGI_ROOT must be absolute" ;;
esac
ROOT_REAL=$(realpath -e "$IZANAGI_ROOT")
rc=$?
if [[ "$rc" -ne 0 || ! -d "$ROOT_REAL" ]]; then
  fail 2 preflight "IZANAGI_ROOT does not resolve to a directory"
fi
IZANAGI_ROOT=$ROOT_REAL
POLICY="$IZANAGI_ROOT/tools/pegasus/policy.json"
CCBENCH_BASE="$IZANAGI_ROOT/external/ccbench"
if [[ ! -f "$POLICY" ]]; then
  fail 2 policy "policy.json is missing"
fi
if [[ ! -d "$CCBENCH_BASE" ]]; then
  fail 2 ccbench_source "external/ccbench is missing"
fi

# policy.json is trusted configuration; later source-tree checks bind the pinned inputs.
CURRENT_STAGE="policy"
python3 - "$POLICY" >"$JOB_DIR/policy-values.txt" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
print(policy["expected_cpu_model"])
print(policy["expected_physical_cores"])
print(policy["gflags_source_path"])
print(policy["gflags_expected_head"])
print(policy["glog_source_path"])
print(policy["glog_expected_head"])
for candidate in policy["perf_candidates"]:
    print(candidate)
PY
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" policy "could not parse node/dependency/perf policy"
fi
mapfile -t POLICY_VALUES <"$JOB_DIR/policy-values.txt"
rc=$?
if [[ "$rc" -ne 0 || ${#POLICY_VALUES[@]} -lt 7 ]]; then
  fail 2 policy "node/dependency/perf policy is incomplete"
fi
EXPECTED_CPU_MODEL=${POLICY_VALUES[0]}
EXPECTED_PHYSICAL_CORES=${POLICY_VALUES[1]}
GFLAGS_SOURCE_PATH=${POLICY_VALUES[2]}
GFLAGS_EXPECTED_HEAD=${POLICY_VALUES[3]}
GLOG_SOURCE_PATH=${POLICY_VALUES[4]}
GLOG_EXPECTED_HEAD=${POLICY_VALUES[5]}
PERF_CANDIDATES=("${POLICY_VALUES[@]:6}")
if [[ ! "$EXPECTED_PHYSICAL_CORES" =~ ^[1-9][0-9]*$ \
    || ${#PERF_CANDIDATES[@]} -eq 0 ]]; then
  fail 2 policy "expected physical cores or perf candidates are invalid"
fi

# (i) attestation-lite plus fatal node identity gate.
CURRENT_STAGE="attestation"
DATE_VALUE=$(date --iso-8601=seconds)
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" attestation "date failed"
fi
HOST_VALUE=$(hostname)
rc=$?
if [[ "$rc" -ne 0 || -z "$HOST_VALUE" ]]; then
  fail 2 attestation "hostname failed"
fi
KERNEL_VALUE=$(uname -r)
rc=$?
if [[ "$rc" -ne 0 || -z "$KERNEL_VALUE" ]]; then
  fail 2 attestation "uname -r failed"
fi
MODEL_VALUE=$(awk -F: '/^[[:space:]]*model name[[:space:]]*:/ {
  sub(/^[[:space:]]+/, "", $2); print $2; exit
}' /proc/cpuinfo)
rc=$?
if [[ "$rc" -ne 0 || -z "$MODEL_VALUE" ]]; then
  fail 2 attestation "could not read one CPU model-name line"
fi
MODEL_NORMALIZED=$(sed -E \
  's/\((R|TM)\)//g; s/[[:space:]]+/ /g; s/^[[:space:]]+//; s/[[:space:]]+$//' \
  <<<"$MODEL_VALUE")
rc=$?
if [[ "$rc" -ne 0 || -z "$MODEL_NORMALIZED" ]]; then
  fail 2 node_gate "could not normalize CPU model name"
fi
PHYSICAL_CORES=$(lscpu -p=Core,Socket | grep -v '^#' | sort -u | wc -l)
rc=$?
if [[ "$rc" -ne 0 || ! "$PHYSICAL_CORES" =~ ^[0-9]+$ ]]; then
  fail 2 node_gate "could not determine physical core count"
fi
if [[ "$MODEL_NORMALIZED" != "$EXPECTED_CPU_MODEL" ]]; then
  fail 2 node_gate \
    "CPU model mismatch: expected=$EXPECTED_CPU_MODEL observed=$MODEL_NORMALIZED"
fi
if [[ "$PHYSICAL_CORES" -ne "$EXPECTED_PHYSICAL_CORES" ]]; then
  fail 2 node_gate \
    "physical core mismatch: expected=$EXPECTED_PHYSICAL_CORES observed=$PHYSICAL_CORES"
fi
SCRIPT_PATH=$(realpath -e "${BASH_SOURCE[0]}")
rc=$?
if [[ "$rc" -ne 0 || ! -f "$SCRIPT_PATH" ]]; then
  fail 2 attestation "could not resolve running script path"
fi
SCRIPT_SHA256=$(sha256sum "$SCRIPT_PATH" | awk '{print $1}')
rc=$?
if [[ "$rc" -ne 0 || ! "$SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  fail 2 attestation "could not hash running script"
fi
attest date "$DATE_VALUE"
attest hostname "$HOST_VALUE"
attest PBS_JOBID "$PBS_JOBID"
attest PBS_ENVIRONMENT "${PBS_ENVIRONMENT:-unavailable}"
attest PBS_NODEFILE "${PBS_NODEFILE:-unavailable}"
attest uname_r "$KERNEL_VALUE"
attest cpu_model_name "$MODEL_VALUE"
attest cpu_model_name_normalized "$MODEL_NORMALIZED"
attest physical_cores "$PHYSICAL_CORES"
attest expected_cpu_model "$EXPECTED_CPU_MODEL"
attest expected_physical_cores "$EXPECTED_PHYSICAL_CORES"
attest script_path "$SCRIPT_PATH"
attest script_sha256 "$SCRIPT_SHA256"

CC_PATH=""
CXX_PATH=""
CMAKE_PATH=""
for tool_name in gcc g++ cmake; do
  TOOL_PATH=$(command -v "$tool_name")
  rc=$?
  if [[ "$rc" -ne 0 || -z "$TOOL_PATH" ]]; then
    fail 2 attestation "could not resolve $tool_name"
  fi
  TOOL_REAL=$(realpath -e "$TOOL_PATH")
  rc=$?
  if [[ "$rc" -ne 0 || -z "$TOOL_REAL" ]]; then
    fail 2 attestation "could not resolve real path for $tool_name"
  fi
  "$TOOL_REAL" --version >"$LOG_DIR/${tool_name}-version.log" 2>&1
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" attestation "$tool_name --version failed"
  fi
  TOOL_VERSION=$(sed -n '1p' "$LOG_DIR/${tool_name}-version.log")
  rc=$?
  if [[ "$rc" -ne 0 || -z "$TOOL_VERSION" ]]; then
    fail 2 attestation "could not capture $tool_name version"
  fi
  case "$tool_name" in
    gcc) CC_PATH=$TOOL_REAL ;;
    g++) CXX_PATH=$TOOL_REAL ;;
    cmake) CMAKE_PATH=$TOOL_REAL ;;
  esac
  attest "${tool_name}_path" "$TOOL_REAL"
  attest "${tool_name}_version" "$TOOL_VERSION"
done

# (ii) Canonical admission plus non-job CPU-load exclusion.
check_high_cpu() {
  local label=$1
  local ps_file="$ARTIFACT_DIR/ps-${label}.txt"
  local tree_file="$ARTIFACT_DIR/ps-tree-${label}.txt"
  local competitors_file="$ARTIFACT_DIR/high-cpu-${label}.txt"
  local ps_rc=0
  local tree_rc=0
  local classify_rc=0
  local snapshot_pid

  LC_ALL=C ps -eo pid,user,pcpu,comm >"$ps_file" 2>&1 &
  snapshot_pid=$!
  wait "$snapshot_pid" || ps_rc=$?
  if [[ "$ps_rc" -ne 0 ]]; then
    fail "$ps_rc" isolation "ps failed while checking high-CPU competitors for $label"
  fi
  LC_ALL=C ps -eo pid=,ppid= >"$tree_file" 2>&1 || tree_rc=$?
  if [[ "$tree_rc" -ne 0 ]]; then
    fail "$tree_rc" isolation "ps failed while capturing process tree for $label"
  fi
  python3 - "$ps_file" "$tree_file" "$$" "$snapshot_pid" \
    >"$competitors_file" <<'PY' || classify_rc=$?
import sys

path, tree_path, root_text, snapshot_text = sys.argv[1:]
root = int(root_text)
snapshot_pid = int(snapshot_text)
rows = []
parents = {}
with open(tree_path, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        fields = line.split()
        if len(fields) != 2:
            raise SystemExit(2)
        try:
            parents[int(fields[0])] = int(fields[1])
        except ValueError:
            raise SystemExit(2)
with open(path, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        fields = line.split(None, 3)
        if fields and fields[0] == "PID":
            continue
        if len(fields) != 4:
            raise SystemExit(2)
        try:
            pid = int(fields[0])
            pcpu = float(fields[2])
        except ValueError:
            raise SystemExit(2)
        rows.append((pid, fields[1], pcpu, fields[3]))

own_tree = {root, snapshot_pid}
changed = True
while changed:
    changed = False
    for pid, ppid in parents.items():
        if ppid in own_tree and pid not in own_tree:
            own_tree.add(pid)
            changed = True

competitors = [row for row in rows if row[2] > 50.0 and row[0] not in own_tree]
for pid, user, pcpu, command in competitors:
    print(f"{pid}\t{user}\t{pcpu:.1f}\t{command}")
raise SystemExit(1 if competitors else 0)
PY
  if [[ "$classify_rc" -eq 1 ]]; then
    fail 2 isolation "non-job process above 50% CPU detected for $label"
  fi
  if [[ "$classify_rc" -ne 0 ]]; then
    fail "$classify_rc" isolation "could not classify process tree for $label"
  fi
}

check_isolation() {
  local label=$1
  local probe_stdout="$JOB_DIR/isolation.stdout"
  local probe_stderr="$JOB_DIR/isolation.stderr"
  local probe_rc=0
  local checked_at
  local competitors=""
  local append_rc=0

  CURRENT_STAGE="isolation"
  check_high_cpu "$label"
  : >"$probe_stdout"
  : >"$probe_stderr"
  pgrep -af 'ycsb_.*\.exe' >"$probe_stdout" 2>"$probe_stderr" || probe_rc=$?
  checked_at=$(date --iso-8601=seconds)
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" isolation "date failed while recording isolation result"
  fi
  {
    printf 'label=%s\nchecked_at=%s\nargv=pgrep -af ycsb_.*\\\\.exe\nrc=%s\n' \
      "$label" "$checked_at" "$probe_rc"
    printf '%s\n' '--- stdout ---'
    sed -n '1,200p' "$probe_stdout"
    printf '%s\n' '--- stderr ---'
    sed -n '1,200p' "$probe_stderr"
  } >>"$ARTIFACT_DIR/isolation.txt" || append_rc=$?
  if [[ "$append_rc" -ne 0 ]]; then
    fail "$append_rc" isolation "could not save isolation result"
  fi

  if [[ "$probe_rc" -eq 1 && ! -s "$probe_stdout" && ! -s "$probe_stderr" ]]; then
    printf 'status=pass\n\n' >>"$ARTIFACT_DIR/isolation.txt" || append_rc=$?
    if [[ "$append_rc" -ne 0 ]]; then
      fail "$append_rc" isolation "could not save isolation pass"
    fi
    return 0
  fi
  if [[ "$probe_rc" -eq 0 && -s "$probe_stdout" ]]; then
    competitors=$(awk -v own="$$" '
      NF {
        if ($1 ~ /^[0-9]+$/ && $1 == own) next
        print
      }
    ' "$probe_stdout")
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      fail "$rc" isolation "could not classify pgrep output"
    fi
    if [[ -z "$competitors" && ! -s "$probe_stderr" ]]; then
      printf 'status=pass (self only)\n\n' >>"$ARTIFACT_DIR/isolation.txt" || append_rc=$?
      if [[ "$append_rc" -ne 0 ]]; then
        fail "$append_rc" isolation "could not save self-only isolation pass"
      fi
      return 0
    fi
    printf 'status=fail\ncompetitors:\n%s\n\n' "$competitors" \
      >>"$ARTIFACT_DIR/isolation.txt" || true
    fail 2 isolation "competing ycsb measurement process detected"
  fi
  printf 'status=fail (probe contract violation)\n\n' \
    >>"$ARTIFACT_DIR/isolation.txt" || true
  fail 2 isolation "pgrep could not establish absence of competing measurement processes"
}

check_isolation initial

check_pinned_source() {
  local label=$1
  local source_path=$2
  local expected_head=$3
  local observed_head
  local source_status
  local source_rc=0

  CURRENT_STAGE=$label
  if [[ ! -d "$source_path" ]]; then
    fail 2 "$label" "$label source path is missing"
  fi
  observed_head=$(git -C "$source_path" rev-parse HEAD \
    2>"$LOG_DIR/${label}-source-head.stderr") || source_rc=$?
  if [[ "$source_rc" -ne 0 ]]; then
    fail "$source_rc" "$label" "could not resolve source HEAD"
  fi
  printf '%s\n' "$observed_head" >"$LOG_DIR/${label}-source-head.log"
  if [[ "$observed_head" != "$expected_head" ]]; then
    fail 2 "$label" "source HEAD does not match policy expected_head"
  fi
  source_rc=0
  source_status=$(git -C "$source_path" status --porcelain --untracked-files=all \
    2>"$LOG_DIR/${label}-source-status.stderr") || source_rc=$?
  if [[ "$source_rc" -ne 0 ]]; then
    fail "$source_rc" "$label" "could not inspect source working tree"
  fi
  printf '%s' "$source_status" >"$LOG_DIR/${label}-source-status.log"
  if [[ -n "$source_status" ]]; then
    fail 2 "$label" "source working tree is dirty"
  fi
  attest "${label}_source_path" "$source_path"
  attest "${label}_source_head" "$observed_head"
}

check_pinned_source gflags "$GFLAGS_SOURCE_PATH" "$GFLAGS_EXPECTED_HEAD"
check_pinned_source glog "$GLOG_SOURCE_PATH" "$GLOG_EXPECTED_HEAD"

# (iii) gflags/glog: certify (iv) の static/PIC build を /scr に簡約移植。
GFLAGS_BUILD="$JOB_DIR/gflags-build"
GFLAGS_INSTALL="$JOB_DIR/gflags-install"
GLOG_BUILD="$JOB_DIR/glog-build"
GLOG_INSTALL="$JOB_DIR/glog-install"
mkdir "$GFLAGS_BUILD"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" gflags "could not create build directory"
fi
gflags_configure=(
  "$CMAKE_PATH" -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL"
  "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH"
)
GFLAGS_CONFIGURE_TEXT=$(shell_join "${gflags_configure[@]}")
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" gflags "could not serialize gflags configure argv"
fi
attest gflags_configure_argv "$GFLAGS_CONFIGURE_TEXT"
run_logged gflags "gflags configure failed" "$LOG_DIR/gflags-configure.log" \
  timeout 60 "${gflags_configure[@]}"
run_logged gflags "gflags build failed" "$LOG_DIR/gflags-build.log" \
  timeout 60 "$CMAKE_PATH" --build "$GFLAGS_BUILD" -j 48
run_logged gflags "gflags install failed" "$LOG_DIR/gflags-install.log" \
  timeout 60 "$CMAKE_PATH" --install "$GFLAGS_BUILD"

mkdir "$GLOG_BUILD"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" glog "could not create build directory"
fi
glog_configure=(
  "$CMAKE_PATH" -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL"
  "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH"
)
GLOG_CONFIGURE_TEXT=$(shell_join "${glog_configure[@]}")
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" glog "could not serialize glog configure argv"
fi
attest glog_configure_argv "$GLOG_CONFIGURE_TEXT"
run_logged glog "glog configure failed" "$LOG_DIR/glog-configure.log" \
  timeout 120 "${glog_configure[@]}"
run_logged glog "glog build failed" "$LOG_DIR/glog-build.log" \
  timeout 120 "$CMAKE_PATH" --build "$GLOG_BUILD" -j 48
run_logged glog "glog install failed" "$LOG_DIR/glog-install.log" \
  timeout 120 "$CMAKE_PATH" --install "$GLOG_BUILD"

# (iv) pinned-clean CCBench を /scr へコピーし、以後 repo 本体には触れない。
CURRENT_STAGE="ccbench_source"
CCBENCH_HEAD=$(git -C "$CCBENCH_BASE" rev-parse HEAD \
  2>"$LOG_DIR/ccbench-source-head.stderr")
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "could not resolve ccbench HEAD"
fi
git -C "$IZANAGI_ROOT" ls-tree HEAD external/ccbench \
  >"$LOG_DIR/ccbench-gitlink.log" 2>"$LOG_DIR/ccbench-gitlink.stderr"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "could not resolve repository ccbench gitlink"
fi
CCBENCH_GITLINK=$(awk 'NR == 1 {print $3}' "$LOG_DIR/ccbench-gitlink.log")
rc=$?
if [[ "$rc" -ne 0 || -z "$CCBENCH_GITLINK" || "$CCBENCH_HEAD" != "$CCBENCH_GITLINK" ]]; then
  fail 2 ccbench_source "ccbench HEAD does not match repository gitlink"
fi
CCBENCH_STATUS=$(git -C "$CCBENCH_BASE" status --porcelain --untracked-files=all \
  2>"$LOG_DIR/ccbench-source-status.stderr")
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "could not inspect ccbench working tree"
fi
printf '%s' "$CCBENCH_STATUS" >"$LOG_DIR/ccbench-source-status.log"
if [[ -n "$CCBENCH_STATUS" ]]; then
  fail 2 ccbench_source "ccbench working tree is dirty"
fi

CCBENCH_SOURCE="$JOB_DIR/ccbench-source"
mkdir "$CCBENCH_SOURCE"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "could not create copied source root"
fi
# git archive は tree 内 .gitattributes の export-ignore で cc/oze を落とすため使わない。
git -C "$CCBENCH_BASE" ls-files -z \
  | tar -C "$CCBENCH_BASE" --null -T - -cf - \
  | tar -x -C "$CCBENCH_SOURCE"
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "tracked-file tar copy of ccbench failed"
fi
CCBENCH_SOURCE=$(realpath -e "$CCBENCH_SOURCE")
rc=$?
if [[ "$rc" -ne 0 ]]; then
  fail "$rc" ccbench_source "could not resolve copied source root"
fi
attest ccbench_source_root "$CCBENCH_SOURCE"
attest ccbench_source_head "$CCBENCH_HEAD"
attest ccbench_copy_method "git-ls-files-tar"

# (v) Stock S/V: Release codegen + diagnostic -g, trace and sanitizer disabled.
declare -A BINARIES
for build_tag in S V; do
  if [[ "$build_tag" == "S" ]]; then
    backoff=0
    build_name="stock-backoff-off"
  else
    backoff=1
    build_name="stock-backoff-on"
  fi
  BUILD_DIR="$JOB_DIR/ccbench-build-$build_tag"
  mkdir "$BUILD_DIR"
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" "build_$build_tag" "could not create ccbench build directory"
  fi
  configure_argv=(
    "$CMAKE_PATH" -S "$CCBENCH_SOURCE" -B "$BUILD_DIR"
    -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF
    -DCCBENCH_TRACE=0 "-DCCBENCH_BACK_OFF=$backoff"
    -DCCBENCH_CCACHE=OFF "-DCMAKE_CXX_FLAGS=-g"
    "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL;$GLOG_INSTALL"
    "-DCMAKE_C_COMPILER=$CC_PATH" "-DCMAKE_CXX_COMPILER=$CXX_PATH"
  )
  CONFIGURE_TEXT=$(shell_join "${configure_argv[@]}")
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" "build_$build_tag" "could not serialize cmake configure argv"
  fi
  attest "build_${build_tag}_configure_argv" "$CONFIGURE_TEXT"
  run_logged "build_$build_tag" "$build_name configure failed" \
    "$LOG_DIR/ccbench-${build_tag}-configure.log" \
    timeout 900 "${configure_argv[@]}"
  run_logged "build_$build_tag" "$build_name build failed" \
    "$LOG_DIR/ccbench-${build_tag}-build.log" \
    timeout 900 "$CMAKE_PATH" --build "$BUILD_DIR" --target ycsb_silo.exe -j 48
  BINARY="$BUILD_DIR/cc/silo/ycsb_silo.exe"
  if [[ ! -x "$BINARY" ]]; then
    fail 2 "build_$build_tag" "$build_name binary is missing or not executable"
  fi
  BINARY_SHA256=$(sha256sum "$BINARY" | awk '{print $1}')
  rc=$?
  if [[ "$rc" -ne 0 || ! "$BINARY_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
    fail 2 "build_$build_tag" "$build_name binary sha256 could not be captured"
  fi
  BINARIES[$build_tag]=$BINARY
  attest "build_${build_tag}_name" "$build_name"
  attest "build_${build_tag}_backoff" "$backoff"
  attest "build_${build_tag}_trace" "0"
  attest "build_${build_tag}_binary" "$BINARY"
  attest "build_${build_tag}_binary_sha256" "$BINARY_SHA256"
  sleep 30
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" "build_$build_tag" "post-build cooldown failed"
  fi
  attest "build_${build_tag}_cooldown_s" "30"
done

# (vi) policy candidate selection: version + exact cycles,instructions stat smoke.
CURRENT_STAGE="perf_select"
PERF_SELECTED=""
PERF_SELECTED_REAL=""
PERF_SELECTED_VERSION=""
for perf_index in "${!PERF_CANDIDATES[@]}"; do
  perf_candidate=${PERF_CANDIDATES[$perf_index]}
  version_file="$ARTIFACT_DIR/perf-candidate-${perf_index}.version.txt"
  smoke_file="$ARTIFACT_DIR/perf-candidate-${perf_index}.smoke.txt"
  delay_smoke_file="$ARTIFACT_DIR/perf-candidate-${perf_index}.delay-smoke.txt"
  delay_smoke_data="$JOB_DIR/perf-delay-smoke-${perf_index}.data"
  if [[ ! -x "$perf_candidate" ]]; then
    printf 'candidate=%s\nstatus=not-executable\n' "$perf_candidate" >"$version_file"
    continue
  fi
  perf_rc=0
  timeout 10 "$perf_candidate" --version >"$version_file" 2>&1 || perf_rc=$?
  if [[ "$perf_rc" -ne 0 ]]; then
    continue
  fi
  perf_rc=0
  timeout 10 "$perf_candidate" stat -e cycles,instructions -- sleep 0.1 \
    >"$smoke_file" 2>&1 || perf_rc=$?
  if [[ "$perf_rc" -ne 0 ]]; then
    continue
  fi
  grep -Eqi '<not (supported|counted)>' "$smoke_file"
  grep_rc=$?
  if [[ "$grep_rc" -eq 0 ]]; then
    continue
  fi
  if [[ "$grep_rc" -gt 1 ]]; then
    fail "$grep_rc" perf_select "could not inspect perf smoke output"
  fi
  perf_rc=0
  timeout 10 "$perf_candidate" record -D 10 -o "$delay_smoke_data" \
    -e cycles,instructions -- sleep 0.1 >"$delay_smoke_file" 2>&1 || perf_rc=$?
  if [[ "$perf_rc" -ne 0 || ! -s "$delay_smoke_data" ]]; then
    rm -f -- "$delay_smoke_data"
    continue
  fi
  rm -f -- "$delay_smoke_data"
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" perf_select "could not remove perf delay-smoke data"
  fi
  PERF_SELECTED=$perf_candidate
  PERF_SELECTED_REAL=$(realpath -e "$perf_candidate")
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    fail "$rc" perf_select "could not resolve selected perf candidate"
  fi
  PERF_SELECTED_VERSION=$(sed -n '1p' "$version_file")
  rc=$?
  if [[ "$rc" -ne 0 || -z "$PERF_SELECTED_VERSION" ]]; then
    fail 2 perf_select "selected perf version is empty"
  fi
  break
done
if [[ -z "$PERF_SELECTED" ]]; then
  fail 2 perf_select "no policy perf candidate passed version, event, and record -D smoke"
fi
attest perf_path "$PERF_SELECTED_REAL"
attest perf_version "$PERF_SELECTED_VERSION"
attest perf_events "cycles,instructions"
attest perf_record_delay_smoke_ms "10"

# (vii) one timing probe per build/workload, then 2 builds x 2 workloads x 3 reps.
parse_throughput() {
  local stdout_path=$1

  python3 - "$stdout_path" <<'PY'
import math
import re
import sys

values = []
pattern = re.compile(
    r"^throughput\[tps\]:[ \t]*"
    r"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)"
    r"[ \t]*$"
)
with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
    for line in handle:
        match = pattern.match(line.rstrip("\n"))
        if match:
            values.append(float(match.group(1)))
if len(values) != 1 or not math.isfinite(values[0]) or values[0] <= 0:
    raise SystemExit(2)
print(format(values[0], ".17g"))
PY
}

validate_srcline_report() {
  local report_path=$1

  python3 - "$report_path" <<'PY'
import re
import sys

sample_pattern = re.compile(
    r"""^# Samples:\s+([0-9][0-9,.]*(?:\.[0-9]+)?[KMG]?)"""
    r"""\s+of event ['"]([^'"]+)['"]"""
)
row_pattern = re.compile(r"^\s*[0-9]+(?:\.[0-9]+)?%\s+")
scales = {"": 1, "K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
samples = {}
current_event = None
cycles_rows = 0
with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
    for line in handle:
        match = sample_pattern.match(line)
        if match:
            token = match.group(1).replace(",", "")
            suffix = token[-1] if token[-1] in scales and not token[-1].isdigit() else ""
            number = token[:-1] if suffix else token
            current_event = match.group(2)
            samples[current_event] = int(float(number) * scales[suffix])
        if current_event == "cycles" and row_pattern.match(line):
            cycles_rows += 1
if set(samples) != {"cycles", "instructions"}:
    raise SystemExit(2)
if samples["cycles"] < 1_000 or cycles_rows < 1:
    raise SystemExit(2)
print(samples["cycles"])
print(samples["instructions"])
print(cycles_rows)
PY
}

count_report_rows() {
  local report_path=$1

  python3 - "$report_path" <<'PY'
import re
import sys

pattern = re.compile(r"^\s*[0-9]+(?:\.[0-9]+)?%\s+")
with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
    rows = sum(1 for line in handle if pattern.match(line))
if rows < 1:
    raise SystemExit(2)
print(rows)
PY
}

record_loadavg() {
  local label=$1
  local loadavg_value

  loadavg_value=$(< /proc/loadavg)
  rc=$?
  if [[ "$rc" -ne 0 || -z "$loadavg_value" ]]; then
    fail 2 "$label" "could not capture pre-run loadavg"
  fi
  attest "${label}_loadavg" "$loadavg_value"
}

DELAY_MARGIN_S="1.0"
attest perf_record_delay_margin_s "$DELAY_MARGIN_S"
declare -A DELAY_MS_BY_PAIR
declare -A ESTIMATED_SAMPLE_WINDOW_S_BY_PAIR
for build_tag in S V; do
  for workload in write-heavy balanced; do
    case "$workload" in
      write-heavy) workload_flags=(-ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0) ;;
      balanced) workload_flags=(-ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0) ;;
    esac
    pair_id="${build_tag}-${workload}"
    timing_stage="timing_${pair_id}"
    ensure_deadline "$timing_stage" 185
    record_loadavg "$timing_stage"
    check_isolation "$timing_stage"
    timing_argv=(
      "${BINARIES[$build_tag]}"
      -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100
      "${workload_flags[@]}"
    )
    TIMING_ARGV_TEXT=$(shell_join "${timing_argv[@]}")
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      fail "$rc" "$timing_stage" "could not serialize timing benchmark argv"
    fi
    attest "${timing_stage}_bench_argv" "$TIMING_ARGV_TEXT"
    TIMING_START=$(date +%s.%N)
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      fail "$rc" "$timing_stage" "could not record timing start"
    fi
    timing_rc=0
    CURRENT_STAGE=$timing_stage
    timeout --signal=TERM 180 "${timing_argv[@]}" \
      >"$ARTIFACT_DIR/timing-stdout-${pair_id}.txt" \
      2>"$ARTIFACT_DIR/timing-stderr-${pair_id}.txt" || timing_rc=$?
    TIMING_END=$(date +%s.%N)
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      fail "$rc" "$timing_stage" "could not record timing end"
    fi
    if [[ "$timing_rc" -ne 0 ]]; then
      fail "$timing_rc" "$timing_stage" "unprofiled timing benchmark failed"
    fi
    TIMING_TPS=$(parse_throughput "$ARTIFACT_DIR/timing-stdout-${pair_id}.txt")
    rc=$?
    if [[ "$rc" -ne 0 || -z "$TIMING_TPS" ]]; then
      fail 2 "$timing_stage" "timing benchmark throughput[tps] is missing or non-positive"
    fi
    TIMING_METRICS_FILE="$JOB_DIR/timing-metrics-${pair_id}.txt"
    python3 - "$TIMING_START" "$TIMING_END" "$DELAY_MARGIN_S" \
      >"$TIMING_METRICS_FILE" <<'PY'
import math
import sys

start, end, delay_margin = map(float, sys.argv[1:])
wall = end - start
if (
    not math.isfinite(wall)
    or wall <= 0
    or not math.isfinite(delay_margin)
    or delay_margin < 0
):
    raise SystemExit(2)
delay_ms = int(round(max(0.0, wall - 3.0 + delay_margin) * 1000.0))
estimated_sample_window = max(0.0, wall - delay_ms / 1000.0)
print(f"{wall:.6f}")
print(delay_ms)
print(f"{estimated_sample_window:.6f}")
PY
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      fail "$rc" "$timing_stage" "could not derive perf record delay"
    fi
    mapfile -t TIMING_METRICS <"$TIMING_METRICS_FILE"
    rc=$?
    if [[ "$rc" -ne 0 || ${#TIMING_METRICS[@]} -ne 3 \
        || ! "${TIMING_METRICS[1]}" =~ ^[0-9]+$ \
        || ! "${TIMING_METRICS[2]}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      fail 2 "$timing_stage" "derived timing metrics are malformed"
    fi
    TIMING_WALL_S=${TIMING_METRICS[0]}
    DELAY_MS=${TIMING_METRICS[1]}
    ESTIMATED_SAMPLE_WINDOW_S=${TIMING_METRICS[2]}
    DELAY_MS_BY_PAIR[$pair_id]=$DELAY_MS
    ESTIMATED_SAMPLE_WINDOW_S_BY_PAIR[$pair_id]=$ESTIMATED_SAMPLE_WINDOW_S
    attest "${timing_stage}_wall_s" "$TIMING_WALL_S"
    attest "${timing_stage}_throughput_tps" "$TIMING_TPS"
    attest "${timing_stage}_delay_ms" "$DELAY_MS"
    attest "${timing_stage}_estimated_sample_window_s" "$ESTIMATED_SAMPLE_WINDOW_S"
  done
done

for build_tag in S V; do
  for workload in write-heavy balanced; do
    case "$workload" in
      write-heavy) workload_flags=(-ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0) ;;
      balanced) workload_flags=(-ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0) ;;
    esac
    pair_id="${build_tag}-${workload}"
    DELAY_MS=${DELAY_MS_BY_PAIR[$pair_id]}
    ESTIMATED_SAMPLE_WINDOW_S=${ESTIMATED_SAMPLE_WINDOW_S_BY_PAIR[$pair_id]}
    for rep in 1 2 3; do
      run_id="${pair_id}-r${rep}"
      cell_stage="cell_${run_id}"
      ensure_deadline "$cell_stage" 425
      record_loadavg "$cell_stage"
      check_isolation "$run_id"
      RUN_DIR="$JOB_DIR/run-$run_id"
      mkdir "$RUN_DIR"
      rc=$?
      if [[ "$rc" -ne 0 ]]; then
        fail "$rc" "$cell_stage" "could not create run directory"
      fi
      PERF_DATA="$RUN_DIR/perf.data"
      workload_bench_argv=(
        "${BINARIES[$build_tag]}"
        -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100
        "${workload_flags[@]}"
      )
      bench_argv=(
        "$PERF_SELECTED_REAL" record -D "$DELAY_MS"
        -o "$PERF_DATA" -e cycles,instructions --
        "${workload_bench_argv[@]}"
      )
      BENCH_ARGV_TEXT=$(shell_join "${bench_argv[@]}")
      rc=$?
      if [[ "$rc" -ne 0 ]]; then
        fail "$rc" "$cell_stage" "could not serialize benchmark argv"
      fi
      attest "${cell_stage}_bench_argv" "$BENCH_ARGV_TEXT"
      attest "${cell_stage}_delay_ms" "$DELAY_MS"
      attest "${cell_stage}_estimated_sample_window_s" "$ESTIMATED_SAMPLE_WINDOW_S"
      CURRENT_STAGE=$cell_stage
      bench_rc=0
      timeout --signal=TERM 180 "${bench_argv[@]}" \
        >"$ARTIFACT_DIR/bench-stdout-${run_id}.txt" \
        2>"$ARTIFACT_DIR/bench-stderr-${run_id}.txt" || bench_rc=$?
      if [[ "$bench_rc" -ne 0 ]]; then
        fail "$bench_rc" "$cell_stage" "perf record or benchmark failed"
      fi
      CELL_TPS=$(parse_throughput "$ARTIFACT_DIR/bench-stdout-${run_id}.txt")
      rc=$?
      if [[ "$rc" -ne 0 || -z "$CELL_TPS" ]]; then
        fail 2 "$cell_stage" "benchmark throughput[tps] is missing or non-positive"
      fi
      attest "${cell_stage}_throughput_tps" "$CELL_TPS"
      if [[ ! -s "$PERF_DATA" ]]; then
        fail 2 "$cell_stage" "perf record succeeded without non-empty perf.data"
      fi

      SRCLINE_REPORT="$ARTIFACT_DIR/report-srcline-${run_id}.txt"
      SYMBOL_REPORT="$ARTIFACT_DIR/report-symbol-${run_id}.txt"
      report_rc=0
      timeout --signal=TERM 120 "$PERF_SELECTED_REAL" report \
        -i "$PERF_DATA" --stdio --percent-limit 0 --sort=srcline \
        >"$SRCLINE_REPORT" \
        2>"$ARTIFACT_DIR/report-srcline-${run_id}.stderr.txt" || report_rc=$?
      if [[ "$report_rc" -ne 0 ]]; then
        fail "$report_rc" "$cell_stage" "perf srcline report failed"
      fi
      SRCLINE_METRICS_FILE="$JOB_DIR/report-srcline-metrics-${run_id}.txt"
      validate_srcline_report "$SRCLINE_REPORT" >"$SRCLINE_METRICS_FILE"
      rc=$?
      if [[ "$rc" -ne 0 ]]; then
        fail "$rc" "$cell_stage" \
          "srcline report lacks both event sample headers, 1000 cycles samples, or cycles data rows"
      fi
      mapfile -t SRCLINE_METRICS <"$SRCLINE_METRICS_FILE"
      rc=$?
      if [[ "$rc" -ne 0 || ${#SRCLINE_METRICS[@]} -ne 3 ]]; then
        fail 2 "$cell_stage" "srcline report metrics are malformed"
      fi
      attest "${cell_stage}_cycles_samples" "${SRCLINE_METRICS[0]}"
      attest "${cell_stage}_instructions_samples" "${SRCLINE_METRICS[1]}"
      attest "${cell_stage}_srcline_rows" "${SRCLINE_METRICS[2]}"

      report_rc=0
      timeout --signal=TERM 120 "$PERF_SELECTED_REAL" report \
        -i "$PERF_DATA" --stdio --percent-limit 0 --sort=symbol \
        >"$SYMBOL_REPORT" \
        2>"$ARTIFACT_DIR/report-symbol-${run_id}.stderr.txt" || report_rc=$?
      if [[ "$report_rc" -ne 0 ]]; then
        fail "$report_rc" "$cell_stage" "perf symbol report failed"
      fi
      SYMBOL_ROWS=$(count_report_rows "$SYMBOL_REPORT")
      rc=$?
      if [[ "$rc" -ne 0 || ! "$SYMBOL_ROWS" =~ ^[0-9]+$ ]]; then
        fail 2 "$cell_stage" "symbol report lacks data rows"
      fi
      attest "${cell_stage}_symbol_rows" "$SYMBOL_ROWS"
      rm -f -- "$PERF_DATA"
      rc=$?
      if [[ "$rc" -ne 0 ]]; then
        fail "$rc" "$cell_stage" "could not discard scratch perf.data"
      fi
    done
  done
done

exit 0
