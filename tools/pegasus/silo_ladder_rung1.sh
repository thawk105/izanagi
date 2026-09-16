#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=02:00:00
#PBS -b 1

# build 3本 <=2700s + dependency build <=180s + 32 run slot 約300s
# (24 perf + 4 liveness + 4 attestation/recovery margin)
# + attestation/収集 margin + finalize reserve 600s < request 7200s。
set -Eeuo pipefail
umask 077
FINALIZE_CAP_S=600
JOB_START_EPOCH=$(date +%s)
FINALIZE_DEADLINE_EPOCH=$((JOB_START_EPOCH + 7200))
CURRENT_STAGE=contract_bootstrap

verify_third_party_pinned_clean() {
  local source=$1 pin=$2 name=$3
  [[ -d "$source" && ! -L "$source" ]] || {
    echo "third-party source is not a real directory: $name" >&2
    return 1
  }
  THIRD_PARTY_VERIFIED_HEAD=$(git -C "$source" rev-parse --verify HEAD) || return
  THIRD_PARTY_VERIFIED_STATUS=$(
    git -C "$source" status --porcelain --untracked-files=all
  ) || return
  if [[ "$THIRD_PARTY_VERIFIED_HEAD" != "$pin" \
      || -n "$THIRD_PARTY_VERIFIED_STATUS" ]]; then
    echo "third-party source is not pinned-clean: $name" >&2
    return 1
  fi
}

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi
if [[ -z "${IZANAGI_SUBMISSION_NONCE:-}" \
    || ! "$IZANAGI_SUBMISSION_NONCE" =~ ^[0-9a-f]{32}$ ]]; then
  echo "IZANAGI_SUBMISSION_NONCE must be 32 lowercase hex" >&2
  exit 2
fi

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
unset LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH
unset COMPILER_PATH GCC_EXEC_PREFIX CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE
unset CMAKE_PROJECT_INCLUDE CMAKE_PROJECT_INCLUDE_BEFORE
unset CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_C_COMPILER_LAUNCHER
unset CMAKE_CXX_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS
while IFS='=' read -r env_name _; do
  case "$env_name" in
    GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*) unset "$env_name" ;;
  esac
done < <(env)

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
POLICY="$REPO_ROOT/tools/pegasus/policy.json"
RUNTIME="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging"
ATTEMPTS="$RUNTIME/campaigns"
SUBMISSION="$RUNTIME/submissions/$IZANAGI_SUBMISSION_NONCE"
SUBMIT_RECEIPT="$SUBMISSION/submit-receipt.json"
JOB_TAG=${PBS_JOBID//:/_}
JOB_STAGING="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/$JOB_TAG"
mkdir -p "$ATTEMPTS" "$(dirname "$JOB_STAGING")"
if ! mkdir "$JOB_STAGING"; then
  echo "job staging already exists (create-only): $JOB_STAGING" >&2
  exit 2
fi
set -o noclobber

publish_shell_create_only() {
  local staged=$1 destination=$2
  sync -f "$staged" 2>/dev/null || true
  ln "$staged" "$destination"
  sync -f "$(dirname "$destination")" 2>/dev/null || true
  rm -f "$staged"
}

write_shell_file_receipts() {
  local root=$1 excluded=$2 first=1 path relative digest
  while IFS= read -r path; do
    [[ "$path" == "$excluded" || "$(basename "$path")" == raw-manifest.json ]] \
      && continue
    relative=${path#"$root"/}
    digest=$(sha256sum "$path")
    digest=${digest%% *}
    if [[ "$first" -eq 0 ]]; then printf ',\n'; fi
    first=0
    printf '    {"path":"%s","sha256":"%s"}' "$relative" "$digest"
  done < <(find "$root" -type f -print | LC_ALL=C sort)
  printf '\n'
}

write_interpreter_failure() {
  local attempt=${IZANAGI_ATTEMPT_NUMBER:-1}
  local wait_count campaign_id recorded_epoch raw raw_rel
  local submit_sha receipt_sha seal_path seal_sha schedule_path staged
  CURRENT_STAGE=interpreter_resolution
  for ((wait_count=0; wait_count<60; wait_count++)); do
    [[ -f "$SUBMIT_RECEIPT" && ! -L "$SUBMIT_RECEIPT" ]] && break
    sleep 1
  done
  [[ -f "$SUBMIT_RECEIPT" && ! -L "$SUBMIT_RECEIPT" ]] || return 1
  schedule_path="$SUBMISSION/schedule-receipt.json"
  [[ -f "$schedule_path" && ! -L "$schedule_path" ]] || return 1
  campaign_id=$(sed -n \
    's/^[[:space:]]*"campaign_id": "\\([0-9a-f]\\{64\\}\\)",[[:space:]]*$/\\1/p' \
    "$SUBMIT_RECEIPT")
  [[ "$campaign_id" =~ ^[0-9a-f]{64}$ ]] || return 1
  raw="$JOB_STAGING/attempt-$attempt/raw"
  mkdir -p "$raw"
  cp "$SUBMIT_RECEIPT" "$raw/submit-receipt.json"
  recorded_epoch=$(date +%s)
  staged="$JOB_STAGING/.failure-interpreter.$$.staging"
  printf '{"attempt_number":%s,"failure_class":"infra","message":"no compatible python3 >= 3.10","pbs_jobid":"%s","rc":2,"reason_code":"nonzero_returncode","recorded_epoch":%s,"schema_version":"silo_ladder_rung1-failure/v1","stage":"interpreter_resolution"}\n' \
    "$attempt" "$PBS_JOBID" "$recorded_epoch" >"$staged"
  publish_shell_create_only "$staged" "$JOB_STAGING/failure.json"
  cp "$JOB_STAGING/failure.json" "$raw/wrapper-failure.json"

  staged="$raw/.attempt-receipt.$$.staging"
  {
    printf '{"schema_version":"silo_ladder_rung1-attempt-receipt/v1","attempt":%s,"files":[\n' "$attempt"
    write_shell_file_receipts "$raw" "$staged"
    printf ']}\n'
  } >"$staged"
  publish_shell_create_only "$staged" "$raw/attempt-receipt.json"
  receipt_sha=$(sha256sum "$raw/attempt-receipt.json")
  receipt_sha=${receipt_sha%% *}

  staged="$raw/.raw-manifest.$$.staging"
  {
    printf '{"schema_version":"silo_ladder_rung1-raw-manifest/v1","files":[\n'
    write_shell_file_receipts "$raw" "$staged"
    printf ']}\n'
  } >"$staged"
  publish_shell_create_only "$staged" "$raw/raw-manifest.json"

  submit_sha=$(sha256sum "$SUBMIT_RECEIPT")
  submit_sha=${submit_sha%% *}
  seal_path="$ATTEMPTS/$campaign_id/attempt-$attempt/attempt-root-receipt.json"
  staged="$(dirname "$seal_path")/.attempt-root.$$.staging"
  printf '{"schema_version":"silo_ladder_rung1-campaign-attempt-root/v1","campaign_id":"%s","attempt":%s,"job_id":"%s","nonce":"%s","submit_receipt_sha256":"%s","attempt_receipt_sha256":"%s","failure_class":"infra","reason_code":"nonzero_returncode"}\n' \
    "$campaign_id" "$attempt" "$PBS_JOBID" "$IZANAGI_SUBMISSION_NONCE" \
    "$submit_sha" "$receipt_sha" >"$staged"
  publish_shell_create_only "$staged" "$seal_path"
  seal_sha=$(sha256sum "$seal_path")
  seal_sha=${seal_sha%% *}
  raw_rel=${raw#"$REPO_ROOT"/}

  staged="$JOB_STAGING/.gap-result-interpreter.$$.staging"
  {
    printf '{"schema_version":"silo_ladder_rung1-gap-job/v1","pbs_jobid":"%s","attempt_number":%s,"campaign_id":"%s","submission_nonce":"%s","submit_receipt_sha256":"%s","campaign_attempt_root_receipt":{"path":"%s","sha256":"%s"},"schedule_receipt":' \
      "$PBS_JOBID" "$attempt" "$campaign_id" "$IZANAGI_SUBMISSION_NONCE" \
      "$submit_sha" "${seal_path#"$REPO_ROOT"/}" "$seal_sha"
    tr -d '\n' <"$schedule_path"
    printf ',"status":"infra-failure","failure_class":"infra","reason_code":"nonzero_returncode","message":"no compatible python3 >= 3.10","attempt_receipt_sha256":"%s","raw_root":"%s","raw_paths":[]}\n' \
      "$receipt_sha" "$raw_rel"
  } >"$staged"
  publish_shell_create_only "$staged" "$JOB_STAGING/gap-result.json"
}
PY=""
py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if "$py_resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY="$py_resolved"
    break
  fi
  py_rejected+="${py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$PY" ]]; then
  write_interpreter_failure || true
  exit 2
fi

failure_written=0
write_failure() {
  local rc=$1 stage=$2 message=$3
  local now remaining finalizer_timeout
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    if [[ -f "$JOB_STAGING/gap-result.json" ]]; then
      mv "$JOB_STAGING/gap-result.json" "$JOB_STAGING/completed-gap-result.json" \
        2>/dev/null || true
    fi
    now=$(date +%s)
    remaining=$((FINALIZE_DEADLINE_EPOCH - now))
    finalizer_timeout=$FINALIZE_CAP_S
    if [[ "$remaining" -lt "$finalizer_timeout" ]]; then
      finalizer_timeout=$remaining
    fi
    [[ "$finalizer_timeout" -gt 0 ]] || return
    timeout "$finalizer_timeout" "$PY" -I -B - \
      "$JOB_STAGING/failure.json" "$PBS_JOBID" "$rc" \
      "$stage" "$message" "$IZANAGI_ATTEMPT_NUMBER" "$SUBMIT_RECEIPT" <<'PY' || true
import json, sys, time
path, job, rc, stage, message, attempt, submit_path = sys.argv[1:]
from pathlib import Path
sys.path.insert(0, str(Path(path).resolve().parents[6]))
from orchestrator.campaign.silo_ladder_rung1 import (
    classify_wrapper_failure, publish_create_only_json, sha256_file,
    write_attempt_receipt, write_raw_manifest,
)
failure_class,reason_code=classify_wrapper_failure(stage,int(rc))
raw=Path(path).parent/f"attempt-{int(attempt)}"/"raw"
driver_failure=raw/"driver-failure.json"
if driver_failure.is_file():
    try:
        pending=json.load(open(driver_failure,encoding="utf-8"))
        failure_class=pending["failure_class"]
        reason_code=pending["reason_code"]
        message=pending["message"]
    except (OSError,KeyError,TypeError,ValueError) as exc:
        failure_class,reason_code="contract","contract_failure"
        message=f"invalid driver failure receipt: {type(exc).__name__}: {exc}"
doc={"schema_version":"silo_ladder_rung1-failure/v1",
     "pbs_jobid": job, "rc": int(rc), "stage": stage,
     "message": message, "recorded_epoch": int(time.time()),
     "failure_class":failure_class,"reason_code":reason_code,
     "attempt_number":int(attempt)}
publish_create_only_json(Path(path),doc,staging_dir=Path(path).parent)
submit_file=Path(submit_path)
if submit_file.is_file():
    submit=json.load(open(submit_file,encoding="utf-8"))
    raw.mkdir(parents=True,exist_ok=True)
    if not (raw/"submit-receipt.json").exists():
        publish_create_only_json(
            raw/"submit-receipt.json",submit,staging_dir=raw
        )
    publish_create_only_json(raw/"wrapper-failure.json",doc,staging_dir=raw)
    receipt=write_attempt_receipt(raw,int(attempt))
    write_raw_manifest(raw)
    submit_sha=sha256_file(submit_file)
    repo=Path(path).resolve().parents[6]
    campaign_identity=repo/submit["campaign_root_receipt"]["path"]
    campaign_root=campaign_identity.parent
    seal_doc={
        "schema_version":"silo_ladder_rung1-campaign-attempt-root/v1",
        "campaign_id":submit["campaign_id"],"attempt":int(attempt),
        "job_id":job,"nonce":submit["nonce"],
        "submit_receipt_sha256":submit_sha,
        "attempt_receipt_sha256":sha256_file(receipt),
        "failure_class":failure_class,"reason_code":reason_code,
    }
    seal_path=campaign_root/f"attempt-{int(attempt)}"/"attempt-root-receipt.json"
    publish_create_only_json(seal_path,seal_doc,staging_dir=seal_path.parent)
    status=(
        "infra-failure" if failure_class=="infra"
        else "substantive-negative"
        if failure_class=="substantive-negative"
        else "contract-failure"
    )
    gap={"schema_version":"silo_ladder_rung1-gap-job/v1",
         "pbs_jobid":job,"attempt_number":int(attempt),
         "campaign_id":submit["campaign_id"],"submission_nonce":submit["nonce"],
         "submit_receipt_sha256":submit_sha,
         "campaign_attempt_root_receipt":{
             "path":seal_path.relative_to(repo).as_posix(),
             "sha256":sha256_file(seal_path),
         },
         "schedule_receipt":submit["schedule_receipt"],
         "status":status,
         "failure_class":failure_class,"reason_code":reason_code,
         "message":message,"attempt_receipt_sha256":sha256_file(receipt),
         "raw_root":str(raw.relative_to(Path(path).resolve().parents[6])),
         "raw_paths":[
             p.relative_to(raw).as_posix() for p in sorted(raw.rglob("*"))
             if p.is_file()
         ]}
    pending_path=Path(path).parent/"pending-gap-result.json"
    if pending_path.is_file():
        pending=json.load(open(pending_path,encoding="utf-8"))
        for key in ("performance_runs","builds","gap_leg","provenance","checks"):
            if key in pending:
                gap[key]=pending[key]
    publish_create_only_json(Path(path).parent/"gap-result.json",gap,
                             staging_dir=Path(path).parent)
PY
  fi
}
on_err() {
  local rc=$? line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "$CURRENT_STAGE" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR
CURRENT_STAGE=interpreter_resolution
printf '%s\n' "$PY" >"$JOB_STAGING/python.realpath"
"$PY" -I -B --version >"$JOB_STAGING/python.version" 2>&1

# qsub/receipt の開始競合は bounded wait。raw receipt は必ず job 内へ copy する。
CURRENT_STAGE=submit_binding_contract
for ((wait_count=0; wait_count<60; wait_count++)); do
  if [[ -f "$SUBMIT_RECEIPT" && ! -L "$SUBMIT_RECEIPT" ]] \
      && "$PY" -I -B -c 'import json,sys; json.load(open(sys.argv[1],encoding="utf-8"))' \
        "$SUBMIT_RECEIPT" 2>/dev/null; then
    break
  fi
  sleep 1
done
if [[ ! -f "$SUBMIT_RECEIPT" || -L "$SUBMIT_RECEIPT" ]]; then
  write_failure 2 submit_binding_contract \
    "submit receipt did not appear within 60 seconds"
  exit 2
fi

CURRENT_STAGE=policy_contract
readarray -t policy_values < <("$PY" -I -B - "$POLICY" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))["silo_ladder_rung1"]
for key in ("project", "queue", "nodes", "walltime_s", "build_cap_s",
            "dependency_build_cap_s", "attestation_cap_s",
            "run_group_cap_s", "collection_cap_s",
            "finalize_reserve_s", "max_attempts", "solo_load1_threshold"):
    print(p[key])
PY
)
[[ ${#policy_values[@]} -eq 12 ]]
[[ ${policy_values[0]} == SFC && ${policy_values[1]} == gen_S ]]
[[ ${policy_values[2]} -eq 1 && ${policy_values[3]} -eq 7200 ]]
[[ ${policy_values[4]} -eq 2700 && ${policy_values[5]} -eq 180 ]]
[[ ${policy_values[6]} -eq 180 && ${policy_values[7]} -eq 900 ]]
[[ ${policy_values[8]} -eq 300 && ${policy_values[9]} -eq 600 ]]
[[ ${policy_values[10]} -eq 2 ]]
[[ ${policy_values[11]} == 48.0 ]]
FINALIZE_CAP_S=${policy_values[9]}

# login node が凍結した FetchContent source を /scr へ複製し、実 HEAD を再照合する。
CURRENT_STAGE=third_party_copy_contract
THIRD_PARTY_PERSISTENT="$RUNTIME/thirdparty-src"
THIRD_PARTY_SCRATCH="$TMPDIR/thirdparty-src"
mkdir "$THIRD_PARTY_SCRATCH"
readarray -t third_party_rows < <("$PY" -I -B - "$REPO_ROOT" "$SUBMIT_RECEIPT" <<'PY'
import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from orchestrator.campaign.silo_ladder_rung1 import third_party_policy
policy=third_party_policy(pathlib.Path(sys.argv[1]))
submit=json.load(open(sys.argv[2],encoding="utf-8"))
heads=submit.get("bindings",{}).get("third_party_heads")
expected={item["name"]:item["pin"] for item in policy}
if heads != expected:
    raise SystemExit("submit third-party HEAD binding differs from policy")
for item in policy:
    print("\t".join((item["name"],item["source_name"],item["pin"])))
PY
)
[[ ${#third_party_rows[@]} -eq 3 ]]
# find_package dependencies are separate from the three FetchContent sources.
readarray -t build_dependency_rows < <("$PY" -I -B - "$POLICY" <<'PY_BUILD_DEPS'
import json, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
for name in ("gflags", "glog"):
    print("\t".join((name, name, policy[f"{name}_expected_head"])))
PY_BUILD_DEPS
)
[[ ${#build_dependency_rows[@]} -eq 2 ]]
for row in "${third_party_rows[@]}" "${build_dependency_rows[@]}"; do
  IFS=$'\t' read -r third_name third_source_name third_pin <<<"$row"
  [[ "$third_name" =~ ^[a-z][a-z0-9_-]*$ ]]
  [[ "$third_source_name" =~ ^[a-z][a-z0-9_-]*$ ]]
  [[ "$third_pin" =~ ^[0-9a-f]{40}$ ]]
  persistent="$THIRD_PARTY_PERSISTENT/$third_source_name"
  scratch="$THIRD_PARTY_SCRATCH/$third_source_name"
  verify_third_party_pinned_clean \
    "$persistent" "$third_pin" "$third_name"
  printf '%s' "$THIRD_PARTY_VERIFIED_STATUS" \
    >"$JOB_STAGING/$third_name-thirdparty-persistent-status.txt"
  printf '%s\n' "$THIRD_PARTY_VERIFIED_HEAD" \
    >"$JOB_STAGING/$third_name-thirdparty-persistent-head.txt"
  cp -a -- "$persistent" "$scratch"
  verify_third_party_pinned_clean "$scratch" "$third_pin" "$third_name"
  printf '%s' "$THIRD_PARTY_VERIFIED_STATUS" \
    >"$JOB_STAGING/$third_name-thirdparty-scratch-status.txt"
  printf '%s\n' "$THIRD_PARTY_VERIFIED_HEAD" \
    >"$JOB_STAGING/$third_name-thirdparty-scratch-head.txt"
done
export IZANAGI_THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SCRATCH"

# source-surface witness。output 増分を除外した検査であり whole-tree clean と称さない。
CURRENT_STAGE=source_identity_contract
git -C "$REPO_ROOT" status --porcelain --untracked-files=all \
  -- . ':(exclude)output' >"$JOB_STAGING/source-surface-status.txt"
if [[ -s "$JOB_STAGING/source-surface-status.txt" ]]; then
  write_failure 2 source_identity_contract "source surface became dirty"
  exit 2
fi
git -C "$REPO_ROOT" rev-parse HEAD >"$JOB_STAGING/source-head.txt"
git -C "$REPO_ROOT" ls-tree HEAD external/ccbench >"$JOB_STAGING/ccbench-gitlink.txt"

QSTAT_JOBID=${PBS_JOBID#0:}
CURRENT_STAGE=qstat_initial
QSTAT_BASE_EPOCH=$(date +%s)
timeout 30 qstat -f "$QSTAT_JOBID" >"$JOB_STAGING/qstat-f.stdout" \
  2>"$JOB_STAGING/qstat-f.stderr"
readarray -t elapse_values < <("$PY" -I -B - "$JOB_STAGING/qstat-f.stdout" <<'PY'
import re,sys
text=open(sys.argv[1],encoding="utf-8",errors="replace").read()
limits=re.findall(
    r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)",
    text,
)
remaining=re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$",text)
if len(limits) != 1 or len(remaining) != 1:
    raise SystemExit("qstat elapse fields are unavailable or ambiguous")
print(limits[0])
print(remaining[0])
PY
)
[[ ${#elapse_values[@]} -eq 2 ]]
SCHEDULER_LIMIT_S=${elapse_values[0]}
SCHEDULER_REMAINING_S=${elapse_values[1]}
QSTAT_END_EPOCH=$((QSTAT_BASE_EPOCH + SCHEDULER_REMAINING_S))
if [[ "$QSTAT_END_EPOCH" -lt "$FINALIZE_DEADLINE_EPOCH" ]]; then
  FINALIZE_DEADLINE_EPOCH=$QSTAT_END_EPOCH
fi
REQUIRED_REMAINING_S=$((180 + 180 + 2700 + 900 + 300 + 600))
if [[ "$SCHEDULER_LIMIT_S" -ne 7200 \
    || "$SCHEDULER_REMAINING_S" -lt "$REQUIRED_REMAINING_S" ]]; then
  write_failure 2 qstat_initial "scheduler walltime/remaining capacity mismatch"
  exit 2
fi
"$PY" -I -B - "$JOB_STAGING/scheduler-elapse.json" \
  "$SCHEDULER_LIMIT_S" "$SCHEDULER_REMAINING_S" "$REQUIRED_REMAINING_S" <<'PY'
import json,sys
path,limit_s,remaining_s,required_s=sys.argv[1:]
with open(path,"x",encoding="utf-8") as handle:
    json.dump({"limit_s":int(limit_s),"remaining_s":int(remaining_s),
               "required_remaining_s":int(required_s),"policy_match":True},
              handle,sort_keys=True,indent=2)
    handle.write("\n")
PY
uptime >"$JOB_STAGING/load-before.txt"
pgrep -a -f 'ycsb_.*\.exe' >"$JOB_STAGING/pgrep-before.txt" || true

# 登録済み dependency source を fresh /scr build。driver へ install prefix だけ渡す。
CURRENT_STAGE=dependency_policy_contract
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=$("$PY" -I -B - "$POLICY" <<'PY'
import json,sys
print(json.load(open(sys.argv[1], encoding="utf-8"))[
    "silo_ladder_rung1"]["dependency_pins"]["gflags"])
PY
)
GLOG_EXPECTED_HEAD=$("$PY" -I -B - "$POLICY" <<'PY'
import json,sys
print(json.load(open(sys.argv[1], encoding="utf-8"))[
    "silo_ladder_rung1"]["dependency_pins"]["glog"])
PY
)
for dep in gflags glog; do
  if [[ "$dep" == gflags ]]; then
    dep_source=$GFLAGS_SOURCE
    dep_expected=$GFLAGS_EXPECTED_HEAD
  else
    dep_source=$GLOG_SOURCE
    dep_expected=$GLOG_EXPECTED_HEAD
  fi
  dep_head=$(git -C "$dep_source" rev-parse --verify HEAD)
  printf '%s\n' "$dep_head" >"$JOB_STAGING/$dep-source-head.txt"
  git -C "$dep_source" status --porcelain --untracked-files=all \
    >"$JOB_STAGING/$dep-source-status.txt"
  if [[ "$dep_head" != "$dep_expected" \
      || -s "$JOB_STAGING/$dep-source-status.txt" ]]; then
    write_failure 2 dependency_policy_contract \
      "$dep source is not pinned-clean"
    exit 2
  fi
done
GFLAGS_INSTALL="$TMPDIR/gflags-install"
GLOG_INSTALL="$TMPDIR/glog-install"
DEPENDENCY_DEADLINE=$((SECONDS + 180))
dependency_run() {
  local remaining=$((DEPENDENCY_DEADLINE - SECONDS))
  [[ "$remaining" -gt 0 ]] || {
    write_failure 124 dependency_build "dependency group deadline exhausted"
    return 124
  }
  timeout "$remaining" "$@"
}
CURRENT_STAGE=dependency_build
dependency_run cmake -S "$GFLAGS_SOURCE" -B "$TMPDIR/gflags-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL" \
  >"$JOB_STAGING/gflags-configure.stdout" 2>"$JOB_STAGING/gflags-configure.stderr"
dependency_run cmake --build "$TMPDIR/gflags-build" -j 48 \
  >"$JOB_STAGING/gflags-build.stdout" 2>"$JOB_STAGING/gflags-build.stderr"
dependency_run cmake --install "$TMPDIR/gflags-build" \
  >"$JOB_STAGING/gflags-install.stdout" 2>"$JOB_STAGING/gflags-install.stderr"
dependency_run cmake -S "$GLOG_SOURCE" -B "$TMPDIR/glog-build" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF \
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL" \
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL" \
  >"$JOB_STAGING/glog-configure.stdout" 2>"$JOB_STAGING/glog-configure.stderr"
dependency_run cmake --build "$TMPDIR/glog-build" -j 48 \
  >"$JOB_STAGING/glog-build.stdout" 2>"$JOB_STAGING/glog-build.stderr"
dependency_run cmake --install "$TMPDIR/glog-build" \
  >"$JOB_STAGING/glog-install.stdout" 2>"$JOB_STAGING/glog-install.stderr"
export IZANAGI_GFLAGS_INSTALL="$GFLAGS_INSTALL"
export IZANAGI_GLOG_INSTALL="$GLOG_INSTALL"

# dependency 終了後、driver 起動直前の scheduler remaining から絶対 deadline
# を作る。driver は自前 policy deadline との min を採る。
CURRENT_STAGE=qstat_driver
DRIVER_QSTAT_BASE_EPOCH=$(date +%s)
timeout 30 qstat -f "$QSTAT_JOBID" >"$JOB_STAGING/qstat-driver.stdout" \
  2>"$JOB_STAGING/qstat-driver.stderr"
DRIVER_REMAINING_S=$("$PY" -I -B - "$JOB_STAGING/qstat-driver.stdout" <<'PY'
import re,sys
text=open(sys.argv[1],encoding="utf-8",errors="replace").read()
values=re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$",text)
if len(values) != 1:
    raise SystemExit("driver qstat remaining is unavailable or ambiguous")
print(values[0])
PY
)
[[ "$DRIVER_REMAINING_S" -gt "${policy_values[9]}" ]]
DRIVER_QSTAT_END_EPOCH=$((DRIVER_QSTAT_BASE_EPOCH + DRIVER_REMAINING_S))
if [[ "$DRIVER_QSTAT_END_EPOCH" -lt "$FINALIZE_DEADLINE_EPOCH" ]]; then
  FINALIZE_DEADLINE_EPOCH=$DRIVER_QSTAT_END_EPOCH
fi
DRIVER_DEADLINE_EPOCH=$((FINALIZE_DEADLINE_EPOCH - ${policy_values[9]}))

CURRENT_STAGE=driver_gap
"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/silo_ladder_rung1.py" \
  gap-job --job-staging "$JOB_STAGING" --submit-receipt "$SUBMIT_RECEIPT" \
  --scheduler-deadline-epoch "$DRIVER_DEADLINE_EPOCH" \
  >"$JOB_STAGING/driver.stdout" 2>"$JOB_STAGING/driver.stderr"

CURRENT_STAGE=post_driver_finalize
uptime >"$JOB_STAGING/load-after.txt"
"$PY" -I -B - "$JOB_STAGING/success.json" "$PBS_JOBID" <<'PY'
import pathlib,sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve().parents[6]))
from orchestrator.campaign.silo_ladder_rung1 import publish_create_only_json, utc_now
publish_create_only_json(
    pathlib.Path(sys.argv[1]),
    {"schema_version":"silo_ladder_rung1-success-sentinel/v1",
     "pbs_jobid":sys.argv[2],"exit_status":0,"completed_at_utc":utc_now()},
    staging_dir=pathlib.Path(sys.argv[1]).parent,
)
PY
exit 0
