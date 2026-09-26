#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=03:00:00
#PBS -N izs4loop

# 親が直接投入する compute-only job body であり、投入器ではない。
set -Eeuo pipefail
umask 077

refuse() {
  echo "p3 S4 loop job refused: $1" >&2
  exit 2
}

required_env=(
  PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR
  IZANAGI_S4_REPO_ROOT IZANAGI_S4_EXPECTED_HEAD
  IZANAGI_S4_EVIDENCE_ROOT IZANAGI_S4_THIRDPARTY_SOURCE_ROOT
)
for name in "${required_env[@]}"; do
  [[ -n "${!name:-}" ]] || refuse "missing required environment: $name"
done

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
  refuse "P3 S4 loop job body is compute-only"
fi

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
unset LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH
unset COMPILER_PATH GCC_EXEC_PREFIX CONFIG_SITE
unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE
unset CMAKE_GENERATOR CMAKE_GENERATOR_INSTANCE CMAKE_GENERATOR_PLATFORM
unset CMAKE_GENERATOR_TOOLSET CMAKE_PROJECT_INCLUDE CMAKE_PROJECT_INCLUDE_BEFORE
unset CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_C_COMPILER_LAUNCHER
unset CMAKE_CXX_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS
unset IZANAGI_OFFICIAL_OUTPUT_ROOT IZANAGI_EXPLORATION_OUTPUT_ROOT
unset IZANAGI_B10_BINARY_PATH_POLICY
while IFS= read -r env_name; do
  case "$env_name" in
    GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*) unset "$env_name" ;;
  esac
done < <(compgen -e)

export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"
export GIT_OPTIONAL_LOCKS=0
export http_proxy="http://10.120.96.1:8080"
export https_proxy="http://10.120.96.1:8080"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1

harness_mode=${IZANAGI_S4_T2849_MODE-}
harness_env_names=(COHORT COHORT_ROOT WORKLOAD BLOCK N_EVAL ARM SERIES A_LIMIT B_LIMIT BLOCK_STOCK_SESSIONS)
if [[ -v IZANAGI_S4_T2849_MODE ]]; then
  case "${IZANAGI_S4_T2849_PROTOCOL-silo}" in
    silo|mocc) ;;
    *) refuse "invalid T-2849 protocol" ;;
  esac
  case "$harness_mode" in
    series|block-controls) ;;
    *) refuse "invalid T-2849 mode" ;;
  esac
  if [[ -v IZANAGI_S4_B5_MODE || -v IZANAGI_S4_PROPOSAL_PATH \
     || -v IZANAGI_S4_FIXTURE_VALUE || "${IZANAGI_S4_STOCK_CONTROL-}" == 1 ]]; then
    refuse "T-2849 excludes B-5, proposal, fixture, and stock-control"
  fi
  harness_required=(COHORT COHORT_ROOT WORKLOAD BLOCK N_EVAL)
  if [[ "$harness_mode" == series ]]; then
    harness_required+=(ARM SERIES A_LIMIT B_LIMIT)
    [[ ! -v IZANAGI_S4_T2849_BLOCK_STOCK_SESSIONS ]] || refuse "series excludes block stock sessions"
  else
    harness_required+=(BLOCK_STOCK_SESSIONS)
    for suffix in ARM SERIES A_LIMIT B_LIMIT; do
      name="IZANAGI_S4_T2849_$suffix"
      [[ ! -v $name ]] || refuse "block-controls excludes series environment"
    done
  fi
  for suffix in "${harness_required[@]}"; do
    name="IZANAGI_S4_T2849_$suffix"
    [[ -n "${!name:-}" ]] || refuse "missing T-2849 environment: $name"
  done
  [[ "$IZANAGI_S4_T2849_COHORT_ROOT" == /* ]] || refuse "T-2849 cohort root must be absolute"
else
  for suffix in "${harness_env_names[@]}"; do
    name="IZANAGI_S4_T2849_$suffix"
    [[ ! -v $name ]] || refuse "T-2849 environment requires mode"
  done
fi

b5_mode=${IZANAGI_S4_B5_MODE-}
b5_env_names=(
  IZANAGI_S4_B5_ARM IZANAGI_S4_B5_WORKLOAD IZANAGI_S4_B5_SERIES
  IZANAGI_S4_B5_BLOCK IZANAGI_S4_B5_LEDGER_ROOT
)
if [[ -v IZANAGI_S4_B5_MODE ]]; then
  case "$b5_mode" in
    series|block-stock) ;;
    *) refuse "IZANAGI_S4_B5_MODE must be series or block-stock" ;;
  esac
  for name in "${b5_env_names[@]}"; do
    [[ -n "${!name:-}" ]] || refuse "missing B-5 environment: $name"
  done
  case "${IZANAGI_S4_B5_PURPOSE-pilot}" in
    pilot|registered) ;;
    *) refuse "IZANAGI_S4_B5_PURPOSE must be pilot or registered" ;;
  esac
  case "$b5_mode:$IZANAGI_S4_B5_ARM" in
    series:llm|series:random|series:sweep-matched|block-stock:stock) ;;
    *) refuse "invalid B-5 arm for mode" ;;
  esac
  case "$IZANAGI_S4_B5_WORKLOAD" in
    write-heavy|balanced|read-heavy) ;;
    *) refuse "invalid B-5 workload" ;;
  esac
  [[ "$IZANAGI_S4_B5_SERIES" =~ ^([1-9]|1[0-2])$ ]] \
    || refuse "invalid B-5 series"
  [[ "$IZANAGI_S4_B5_BLOCK" =~ ^[1-3]$ ]] || refuse "invalid B-5 block"
  [[ "$IZANAGI_S4_B5_LEDGER_ROOT" == /* ]] || refuse "B-5 ledger root must be absolute"
  if [[ -v IZANAGI_S4_PROPOSAL_PATH || -v IZANAGI_S4_FIXTURE_VALUE \
     || "${IZANAGI_S4_STOCK_CONTROL-}" == 1 ]]; then
    refuse "B-5 mode excludes proposal, fixture, and stock-control"
  fi
else
  for name in "${b5_env_names[@]}" IZANAGI_S4_B5_PURPOSE; do
    [[ ! -v $name ]] || refuse "B-5 environment requires IZANAGI_S4_B5_MODE"
  done
fi

k2_env_names=(
  IZANAGI_S4_KNOWLEDGE_MANIFEST
  IZANAGI_S4_CODER_ROLE
  IZANAGI_S4_KNOWLEDGE_CLASSIFICATION
  IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM
)
k2_required_env_names=(
  IZANAGI_S4_KNOWLEDGE_MANIFEST
  IZANAGI_S4_CODER_ROLE
)
k2_requested=false
for name in "${k2_env_names[@]}"; do
  if [[ -v $name ]]; then
    k2_requested=true
    break
  fi
done

if [[ -n "$b5_mode" ]]; then
  if [[ "$IZANAGI_S4_B5_ARM" == llm ]]; then
    for name in "${k2_env_names[@]}"; do
      [[ -n "${!name:-}" ]] || refuse "B-5 llm requires K2 environment: $name"
    done
    [[ "$IZANAGI_S4_CODER_ROLE" == coder-v4-autonomous-k2 ]] \
      || refuse "B-5 llm requires coder-v4-autonomous-k2"
  elif [[ "$k2_requested" == true ]]; then
    refuse "B-5 non-llm arm excludes K2 environment"
  fi
fi

if [[ -n "$harness_mode" && "$k2_requested" == true ]]; then
  refuse "T-2849 K0 excludes K2 environment"
fi
k2_argv=()
if [[ "$k2_requested" == true ]]; then
  for name in "${k2_required_env_names[@]}"; do
    [[ -n "${!name:-}" ]] || refuse "missing K2 environment: $name"
  done
  k2_argv=(
    --knowledge-manifest "$IZANAGI_S4_KNOWLEDGE_MANIFEST"
    --coder-role "$IZANAGI_S4_CODER_ROLE"
  )
  if [[ -v IZANAGI_S4_KNOWLEDGE_CLASSIFICATION ]]; then
    [[ -n "$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION" ]] \
      || refuse "empty K2 environment: IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"
    k2_argv+=(
      --knowledge-classification "$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"
    )
  fi
  if [[ -v IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM ]]; then
    [[ -n "$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM" ]] \
      || refuse "empty K2 environment: IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM"
    k2_argv+=(
      --knowledge-de-novo-claim "$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM"
    )
  fi
  [[ ( "$b5_mode" == series && "${IZANAGI_S4_B5_ARM-}" == llm ) \
     || -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \
    || refuse "K2 environment requires IZANAGI_S4_PROPOSAL_PATH"
fi

case "${IZANAGI_S4_STOCK_CONTROL-0}" in
  0) stock_control=false ;;
  1) stock_control=true ;;
  *) refuse "IZANAGI_S4_STOCK_CONTROL must be 0 or 1" ;;
esac
pair_argv=()
if [[ "$stock_control" == true ]]; then
  [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \
    || refuse "IZANAGI_S4_STOCK_CONTROL=1 requires IZANAGI_S4_PROPOSAL_PATH"
  pair_argv=(--stock-control)
fi

if [[ ! -d "$IZANAGI_S4_REPO_ROOT" || -L "$IZANAGI_S4_REPO_ROOT" ]]; then
  refuse "repository root is unavailable"
fi
if [[ ! -d "$IZANAGI_S4_EVIDENCE_ROOT" || -L "$IZANAGI_S4_EVIDENCE_ROOT" ]]; then
  refuse "evidence root is unavailable"
fi
if [[ ! -d "$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT" \
   || -L "$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT" ]]; then
  refuse "third-party source root is unavailable"
fi
repo=$(cd -- "$IZANAGI_S4_REPO_ROOT" && pwd -P) \
  || refuse "cannot resolve repository root"
evidence_root=$(cd -- "$IZANAGI_S4_EVIDENCE_ROOT" && pwd -P) \
  || refuse "cannot resolve evidence root"
export IZANAGI_S4_EVIDENCE_ROOT="$evidence_root"
thirdparty_root=$(cd -- "$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT" && pwd -P) \
  || refuse "cannot resolve third-party source root"
case "$repo/" in
  *"/.claude/worktrees/"*|*"/.codex/worktrees/"*)
    refuse "repository root must not be inside an AI worktree container"
    ;;
esac
git_common_dir=$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir) \
  || refuse "cannot resolve git common directory"
[[ "$git_common_dir" == /* ]] || refuse "git common directory is not absolute"
git_common_repo=${git_common_dir%/.git}
if [[ -n "$harness_mode" ]]; then
  harness_cohort_root=$(realpath -m -- "$IZANAGI_S4_T2849_COHORT_ROOT") \
    || refuse "cannot resolve T-2849 cohort root"
  if [[ "$harness_cohort_root" == "$repo" || "$harness_cohort_root" == "$repo/"* \
     || "$harness_cohort_root" == "$git_common_repo" || "$harness_cohort_root" == "$git_common_repo/"* ]]; then
    refuse "T-2849 cohort root resolves inside a repository"
  fi
fi
if [[ -n "$b5_mode" ]]; then
  b5_ledger_root=$(realpath -m -- "$IZANAGI_S4_B5_LEDGER_ROOT") \
    || refuse "cannot resolve B-5 ledger root"
  if [[ "$b5_ledger_root" == "$repo" || "$b5_ledger_root" == "$repo/"* \
     || "$b5_ledger_root" == "$git_common_repo" || "$b5_ledger_root" == "$git_common_repo/"* ]]; then
    refuse "B-5 ledger root resolves inside a repository"
  fi
fi
if [[ "$evidence_root" == "$repo" || "$evidence_root" == "$repo/"* \
   || "$evidence_root" == "$git_common_repo" \
   || "$evidence_root" == "$git_common_repo/"* ]]; then
  refuse "evidence root resolves inside a repository"
fi

result=$evidence_root/compute-result.json
if [[ -e "$result" || -L "$result" ]]; then
  refuse "compute result already exists"
fi
pbs_jobid_path_component=${PBS_JOBID//:/_}
PY=""
python_sha256=""
finish() {
  rc=$?
  trap - EXIT
  tmp=$evidence_root/.compute-result.${pbs_jobid_path_component}.tmp
  if [[ -e "$tmp" || -L "$tmp" ]]; then
    echo "p3 S4 loop job refused: compute result temporary already exists" >&2
    exit 2
  fi
  printf '{"schema_version":"p3-s4-loop-compute-result/v1","driver_rc":%s,"pbs_jobid":"%s","python_realpath":"%s","python_sha256":"%s"}\n' \
    "$rc" "$PBS_JOBID" "$PY" "$python_sha256" >"$tmp"
  sync "$tmp"
  if ! ln "$tmp" "$result"; then
    rm "$tmp"
    exit 2
  fi
  rm "$tmp"
  sync "$evidence_root"
  exit "$rc"
}
trap finish EXIT

resolve_python() {
  local candidate resolved selected="" selected_realpath=""
  for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v -- "$candidate" 2>/dev/null || true)
    [[ -n "$resolved" && -x "$resolved" ]] || continue
    if (
      cd "$repo"
      "$resolved" -B -c \
        'import sys; sys.version_info[:2] == (3, 10) or sys.exit(1); import orchestrator.campaign.p3_s4_loop' \
        >/dev/null 2>&1
    ); then
      selected_realpath=$("$resolved" -I -B -c \
        'import os, sys; print(os.path.realpath(sys.executable))')
      if [[ "$selected_realpath" == /* && -x "$selected_realpath" ]]; then
        selected=$selected_realpath
        break
      fi
    fi
  done
  [[ -n "$selected" ]] \
    || refuse "Python 3.10 capable of importing the P3 S4 loop is required"
  PY=$selected
}
resolve_python
python_sha256=$(sha256sum -- "$PY")
python_sha256=${python_sha256%% *}
[[ "$python_sha256" =~ ^[0-9a-f]{64}$ ]] \
  || refuse "Python interpreter SHA-256 is unavailable"

scratch_base=/scr/$USER/p3-s4-loop-pegasus
scratch=$scratch_base/${pbs_jobid_path_component}
if [[ -e "$scratch" || -L "$scratch" ]]; then
  refuse "scratch root is not fresh"
fi
mkdir -p -m 0700 -- "$scratch_base"
mkdir -m 0700 -- "$scratch"
export TMPDIR=$scratch
shim_dir=$scratch/python-shim
mkdir -m 0700 -- "$shim_dir"
ln -s -- "$PY" "$shim_dir/python3"
shopt -s nullglob dotglob
shim_entries=("$shim_dir"/*)
shopt -u nullglob dotglob
if [[ ${#shim_entries[@]} -ne 1 || "${shim_entries[0]##*/}" != python3 \
   || ! -L "${shim_entries[0]}" ]]; then
  refuse "Python shim directory must contain only python3"
fi
SANITIZED_PATH="$shim_dir:/usr/bin:/bin"
for candidate in /opt/nec/nqsv/bin /system/tool/bin; do
  [[ -d "$candidate" ]] || continue
  SANITIZED_PATH="${SANITIZED_PATH}:$candidate"
done
export PATH="$SANITIZED_PATH"

cd "$repo"
if [[ ! "$IZANAGI_S4_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]]; then
  refuse "expected HEAD must be a full lowercase commit"
fi
observed_head=$(git rev-parse HEAD) || refuse "repository HEAD cannot be resolved"
if [[ "$observed_head" != "$IZANAGI_S4_EXPECTED_HEAD" ]]; then
  refuse "expected HEAD mismatch"
fi
if ! superproject_status=$(git status --porcelain --untracked-files=no \
  --ignore-submodules=all); then
  refuse "cannot inspect superproject tracked status"
fi
[[ -z "$superproject_status" ]] || \
  refuse "superproject tracked worktree is not clean"

ccbench_dir=$repo/external/ccbench
if [[ ! -d "$ccbench_dir" || -L "$ccbench_dir" ]]; then
  refuse "CCBench source root is unavailable"
fi
campaign_pin=$(
  "$PY" -B -c 'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)'
)
if [[ ! "$campaign_pin" =~ ^[0-9a-f]{40}$ ]]; then
  refuse "P3 S4 campaign pin must be a full lowercase commit"
fi
if ! ccbench_full_head=$(
  git -C "$ccbench_dir" rev-parse --verify 'HEAD^{commit}'
); then
  refuse "CCBench HEAD cannot be resolved"
fi
if ! resolved_campaign_pin=$(
  git -C "$ccbench_dir" rev-parse --verify "${campaign_pin}^{commit}"
); then
  refuse "P3 S4 campaign pin cannot be resolved"
fi
if [[ ! "$ccbench_full_head" =~ ^[0-9a-f]{40}$ \
   || ! "$resolved_campaign_pin" =~ ^[0-9a-f]{40}$ \
   || "$ccbench_full_head" != "$resolved_campaign_pin" \
   || "$ccbench_full_head" != "$campaign_pin"* ]]; then
  refuse "CCBench P3 S4 campaign pin mismatch"
fi
if ! ccbench_status=$(git -C "$ccbench_dir" status --porcelain \
  --untracked-files=no); then
  refuse "cannot inspect CCBench tracked status"
fi
[[ -z "$ccbench_status" ]] || refuse "CCBench source tree is not clean"

qstat_jobid=${PBS_JOBID#0:}
allocation_qstat_stdout=$evidence_root/allocation-qstat.stdout
allocation_qstat_stderr=$evidence_root/allocation-qstat.stderr
if [[ -e "$allocation_qstat_stdout" || -L "$allocation_qstat_stdout" \
   || -e "$allocation_qstat_stderr" || -L "$allocation_qstat_stderr" ]]; then
  refuse "allocation qstat evidence is not fresh"
fi
qstat -f "$qstat_jobid" >"$allocation_qstat_stdout" 2>"$allocation_qstat_stderr"
sync "$allocation_qstat_stdout" "$allocation_qstat_stderr"
readarray -t reservation_observation < <(
  "$PY" - "$allocation_qstat_stdout" <<'PY'
import re
import subprocess
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
limits = re.findall(
    r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S",
    text,
)
started = None
for key in ("Started Request Time", "stime", "start_time", "start"):
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
    if match is None:
        continue
    raw = match.group(1).strip()
    if raw.isdigit() and int(raw) > 1_000_000_000:
        started = raw
        break
    parsed = subprocess.run(
        ["date", "-d", raw, "+%s"], capture_output=True, text=True)
    if parsed.returncode == 0 and parsed.stdout.strip().isdigit():
        started = parsed.stdout.strip()
        break
if len(limits) != 1 or started is None:
    raise SystemExit(2)
print(started)
print(limits[0])
PY
)
if [[ ${#reservation_observation[@]} -ne 2 ]]; then
  refuse "scheduler reservation observation is incomplete"
fi
scheduler_started_epoch=${reservation_observation[0]}
requested_s=${reservation_observation[1]}
deadline_epoch=$((scheduler_started_epoch + requested_s))
boot_id=$(tr -d '\n' </proc/sys/kernel/random/boot_id)
job_body=$repo/tools/pegasus/p3_s4_loop_pegasus.sh
if [[ ! -f "$job_body" || -L "$job_body" || -z "$boot_id" ]]; then
  refuse "reservation observation inputs are unavailable"
fi
script_sha256=$(sha256sum -- "$job_body")
script_sha256=${script_sha256%% *}
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$requested_s"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$scheduler_started_epoch"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"
export IZANAGI_RESERVATION_HOST="$host"
export IZANAGI_RESERVATION_BOOT_ID="$boot_id"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$script_sha256"
export IZANAGI_RESERVATION_NONCE="$PBS_JOBID"
reservation_result=$evidence_root/reservation.json
if [[ -e "$reservation_result" || -L "$reservation_result" ]]; then
  refuse "reservation result is not fresh"
fi
"$PY" - "$reservation_result" "$allocation_qstat_stdout" \
  "$allocation_qstat_stderr" <<'PY'
import hashlib
import json
import os
import sys

destination, stdout_path, stderr_path = sys.argv[1:]
keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
environment = {
    "IZANAGI_RESERVATION_" + key: os.environ["IZANAGI_RESERVATION_" + key]
    for key in keys
}
def file_record(path):
    with open(path, "rb") as source:
        payload = source.read()
    return {
        "path": path,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
record = {
    "schema_version": "p3-s4-loop-reservation-result/v1",
    "environment": environment,
    "allocation_qstat_stdout": file_record(stdout_path),
    "allocation_qstat_stderr": file_record(stderr_path),
}
with open(destination, "x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
sync "$evidence_root"

claim_root="$repo/output/env/pegasus/claims"
mkdir -p -m 0700 -- "$claim_root"
if [[ -L "$claim_root" || ! -d "$claim_root" ]]; then
  refuse "campaign claim root provisioning failed"
fi

POLICY=$repo/tools/pegasus/policy.json
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  refuse "policy file missing, not regular, or a symlink"
fi
policy_output=$(
  "$PY" -I -B - "$POLICY" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
keys = (
    "gflags_expected_head",
    "glog_expected_head",
)
for key in keys:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
for key in keys:
    print(policy[key])
PY
)
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 2 ]]; then
  refuse "policy yielded an unexpected field count"
fi
THIRDPARTY_SOURCE_ROOT="$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT"
GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=${policy_values[0]}
GLOG_EXPECTED_HEAD=${policy_values[1]}

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)

# 出典: floor_scoping.sh:205-283。pinned gflags/glog build prologue を同手順で踏襲。
if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  refuse "gflags source path missing"
fi
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  refuse "gflags source HEAD mismatch"
fi
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)
if [[ -n "$GFLAGS_STATUS" ]]; then
  refuse "gflags working tree is dirty"
fi

GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
mkdir "$GFLAGS_BUILD_DIR"
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}"
timeout 60 "${gflags_build_argv[@]}"
timeout 60 "${gflags_install_argv[@]}"

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  refuse "glog source path missing"
fi
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  refuse "glog source HEAD mismatch"
fi
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)
if [[ -n "$GLOG_STATUS" ]]; then
  refuse "glog working tree is dirty"
fi

GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
mkdir "$GLOG_BUILD_DIR"
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
timeout 120 "${glog_configure_argv[@]}"
timeout 120 "${glog_build_argv[@]}"
timeout 120 "${glog_install_argv[@]}"

export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"

prebuild_source_root=$scratch/prebuild-sources
mkdir -m 0700 -- "$prebuild_source_root"
masstree_head=""
mimalloc_head=""
googletest_head=""
for source_name in masstree mimalloc googletest; do
  source=$thirdparty_root/$source_name
  destination=$prebuild_source_root/${source_name}-src
  if [[ ! -d "$source" || -L "$source" ]]; then
    refuse "third-party source is unavailable: $source_name"
  fi
  source_head=$(git -C "$source" rev-parse --verify 'HEAD^{commit}') \
    || refuse "third-party source HEAD cannot be resolved: $source_name"
  if [[ ! "$source_head" =~ ^[0-9a-f]{40}$ ]]; then
    refuse "third-party source HEAD is not a full commit: $source_name"
  fi
  if ! source_status=$(git -C "$source" status --porcelain \
    --untracked-files=no); then
    refuse "cannot inspect third-party source tracked status: $source_name"
  fi
  [[ -z "$source_status" ]] || \
    refuse "third-party source tree is not clean: $source_name"
  mkdir -m 0700 -- "$destination"
  cp -a "$source"/. "$destination"/
  case "$source_name" in
    masstree) masstree_head=$source_head ;;
    mimalloc) mimalloc_head=$source_head ;;
    googletest) googletest_head=$source_head ;;
  esac
done
masstree_source_dir=$prebuild_source_root/masstree-src
mimalloc_source_dir=$prebuild_source_root/mimalloc-src
googletest_source_dir=$prebuild_source_root/googletest-src
if [[ -e "$masstree_source_dir/config.h" || -L "$masstree_source_dir/config.h" ]]; then
  refuse "scratch masstree source is not fresh"
fi
fetchcontent_base_dir=$prebuild_source_root
prebuild_receipt=$evidence_root/masstree-prebuild-receipt.json
if [[ -e "$prebuild_receipt" || -L "$prebuild_receipt" ]]; then
  refuse "masstree prebuild receipt is not fresh"
fi

"$PY" - "$prebuild_receipt" "$ccbench_dir" "$fetchcontent_base_dir" \
  "$prebuild_source_root" "$masstree_source_dir" "$mimalloc_source_dir" \
  "$googletest_source_dir" "$masstree_head" "$mimalloc_head" \
  "$googletest_head" "$PBS_JOBID" "$GFLAGS_INSTALL_DIR" \
  "$GLOG_INSTALL_DIR" <<'PY'
import hashlib
import json
import os
import sys

from orchestrator.campaign import buildcache

(
    receipt_path,
    ccbench_dir,
    fetchcontent_base_dir,
    source_root,
    masstree_source_dir,
    mimalloc_source_dir,
    googletest_source_dir,
    masstree_head,
    mimalloc_head,
    googletest_head,
    pbs_jobid,
    gflags_install_dir,
    glog_install_dir,
) = sys.argv[1:]
expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
    *buildcache.compilers_for_current_site()
)
prepared = buildcache.prepare_masstree_fetchcontent(
    ccbench_dir=ccbench_dir,
    fetchcontent_base_dir=fetchcontent_base_dir,
    expected_toolchain_manifest=expected_toolchain_manifest,
    configure_timeout_s=900,
    target_timeout_s=900,
    dependency_prefix=";".join([gflags_install_dir, glog_install_dir]),
    masstree_source_dir=masstree_source_dir,
    mimalloc_source_dir=mimalloc_source_dir,
    googletest_source_dir=googletest_source_dir,
)
config_h_candidate = os.path.join(masstree_source_dir, "config.h")
if not os.path.isfile(config_h_candidate) or os.path.islink(config_h_candidate):
    raise SystemExit("masstree prebuild did not create a regular config.h")
config_h_path = os.path.realpath(config_h_candidate)
with open(config_h_path, "rb") as stream:
    config_h_sha256 = hashlib.sha256(stream.read()).hexdigest()
record = {
    "schema_version": "p3-s4-loop-masstree-prebuild/v1",
    "fetchcontent_base_dir": prepared.fetchcontent_base_dir,
    "source_root": os.path.realpath(source_root),
    "sources": [
        {"name": "masstree", "head_commit": masstree_head},
        {"name": "mimalloc", "head_commit": mimalloc_head},
        {"name": "googletest", "head_commit": googletest_head},
    ],
    "config_h_path": config_h_path,
    "config_h_sha256": config_h_sha256,
    "configure_argv": list(prepared.configure_argv),
    "build_argv": list(prepared.build_argv),
    "toolchain_manifest": expected_toolchain_manifest,
    "pbs_jobid": pbs_jobid,
}
with open(receipt_path, "x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
sync "$prebuild_receipt"
sync "$evidence_root"

if [[ -n "$harness_mode" ]]; then
  harness_argv=("run-$harness_mode"
    --cohort "$IZANAGI_S4_T2849_COHORT" --cohort-root "$harness_cohort_root"
    --workload "$IZANAGI_S4_T2849_WORKLOAD" --block "$IZANAGI_S4_T2849_BLOCK"
    --n-eval "$IZANAGI_S4_T2849_N_EVAL"
    --fetchcontent-prebuild-receipt "$prebuild_receipt")
  if [[ "${IZANAGI_S4_T2849_PROTOCOL-silo}" == mocc ]]; then
    harness_argv+=(--protocol mocc)
  fi
  if [[ "$harness_mode" == series ]]; then
    harness_argv+=(--arm "$IZANAGI_S4_T2849_ARM" --series "$IZANAGI_S4_T2849_SERIES"
      --a-limit "$IZANAGI_S4_T2849_A_LIMIT" --b-limit "$IZANAGI_S4_T2849_B_LIMIT")
  else
    harness_argv+=(--block-stock-sessions "$IZANAGI_S4_T2849_BLOCK_STOCK_SESSIONS")
  fi
  harness_rc=0
  export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
  "$PY" -B -m orchestrator.campaign.t2849_comparison_harness "${harness_argv[@]}" || harness_rc=$?
  exit "$harness_rc"
fi

if [[ -n "$b5_mode" ]]; then
  b5_argv=("run-$b5_mode")
  if [[ "$b5_mode" == series ]]; then
    b5_argv+=(--arm "$IZANAGI_S4_B5_ARM" --series "$IZANAGI_S4_B5_SERIES")
  fi
  b5_argv+=(--workload "$IZANAGI_S4_B5_WORKLOAD" --block "$IZANAGI_S4_B5_BLOCK"
    --ledger-root "$b5_ledger_root" --fetchcontent-prebuild-receipt "$prebuild_receipt")
  if [[ "$IZANAGI_S4_B5_ARM" == llm ]]; then
    b5_argv+=(--knowledge-manifest "$IZANAGI_S4_KNOWLEDGE_MANIFEST"
      --knowledge-classification "$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"
      --knowledge-de-novo-claim "$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM")
  fi
  if [[ "${IZANAGI_S4_B5_PURPOSE-pilot}" == registered ]]; then
    b5_argv+=(--purpose registered)
  fi
  b5_rc=0
  export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
  "$PY" -B -m orchestrator.campaign.b5_generator_contrast "${b5_argv[@]}" || b5_rc=$?
  exit "$b5_rc"
fi

candidate_rc=0
if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]; then
  "$PY" -B -m orchestrator.campaign.p3_s4_loop \
    --allow-coder-derived-build \
    --isolate-worktree \
    --fetchcontent-prebuild-receipt "$prebuild_receipt" \
    "${k2_argv[@]}" "${pair_argv[@]}" \
    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH" || candidate_rc=$?
else
  "$PY" -B -m orchestrator.campaign.p3_s4_loop \
    --allow-coder-derived-build \
    --isolate-worktree \
    --fetchcontent-prebuild-receipt "$prebuild_receipt" \
    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}" || candidate_rc=$?
fi

exit "$candidate_rc"
