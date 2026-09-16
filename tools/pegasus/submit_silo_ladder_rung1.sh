#!/bin/bash
# ログインノード専用。schedule と clean source を凍結して rung1 job を投入する。
set -Eeuo pipefail
umask 077

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

usage() {
  echo "usage: submit_silo_ladder_rung1.sh (--correctness-json PATH | --prepare-third-party-only) [--attempt-number 1|2] [--prior-gap-result PATH] [--dry-run] [--repo-root PATH]" >&2
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)
CORRECTNESS_JSON=""
DRY_RUN=0
ATTEMPT_NUMBER=1
PRIOR_GAP_RESULT=""
PREPARE_THIRD_PARTY_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --correctness-json) CORRECTNESS_JSON=${2:?}; shift 2 ;;
    --attempt-number) ATTEMPT_NUMBER=${2:?}; shift 2 ;;
    --prior-gap-result) PRIOR_GAP_RESULT=${2:?}; shift 2 ;;
    --repo-root) REPO_ROOT=$(cd "${2:?}" && pwd -P); shift 2 ;;
    --prepare-third-party-only) PREPARE_THIRD_PARTY_ONLY=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
[[ "$ATTEMPT_NUMBER" == 1 || "$ATTEMPT_NUMBER" == 2 ]] || {
  echo "attempt number must be 1 or 2" >&2; exit 2;
}
if [[ "$PREPARE_THIRD_PARTY_ONLY" -eq 0 ]]; then
  [[ -f "$CORRECTNESS_JSON" && ! -L "$CORRECTNESS_JSON" ]] || {
    echo "correctness JSON is missing or a symlink" >&2; exit 2;
  }
elif [[ -n "$CORRECTNESS_JSON" || "$DRY_RUN" -ne 0 ]]; then
  echo "prepare-only cannot be combined with correctness/dry-run" >&2
  exit 2
fi

POLICY="$REPO_ROOT/tools/pegasus/policy.json"
JOB_SCRIPT="$REPO_ROOT/tools/pegasus/silo_ladder_rung1.sh"
DRIVER="$REPO_ROOT/orchestrator/campaign/silo_ladder_rung1.py"
readarray -t policy_values < <(python3 -I -B - "$POLICY" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding="utf-8"))["silo_ladder_rung1"]
for key in ("project","queue","nodes","walltime","walltime_s","max_attempts"):
    print(p[key])
PY
)
[[ ${#policy_values[@]} -eq 6 ]]
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
WALLTIME=${policy_values[3]}
WALLTIME_S=${policy_values[4]}
MAX_ATTEMPTS=${policy_values[5]}
[[ "$PROJECT" == SFC && "$QUEUE" == gen_S && "$NODES" -eq 1 ]]
[[ "$WALLTIME" == 02:00:00 && "$WALLTIME_S" -eq 7200 && "$MAX_ATTEMPTS" -eq 2 ]]
PRIOR_GAP_SHA=""
PRIOR_GAP_REL=""
if [[ "$ATTEMPT_NUMBER" -eq 1 ]]; then
  [[ -z "$PRIOR_GAP_RESULT" ]] || {
    echo "attempt 1 must not have a prior gap result" >&2; exit 2;
  }
else
  [[ -f "$PRIOR_GAP_RESULT" && ! -L "$PRIOR_GAP_RESULT" ]] || {
    echo "attempt 2 requires a regular prior gap result" >&2; exit 2;
  }
  python3 -I -B - "$PRIOR_GAP_RESULT" "$POLICY" "$REPO_ROOT" <<'PY'
import hashlib,json,pathlib,sys
prior=json.load(open(sys.argv[1],encoding="utf-8"))
policy=json.load(open(sys.argv[2],encoding="utf-8"))["silo_ladder_rung1"]
if prior.get("attempt_number") != 1 or prior.get("status") != "infra-failure":
    raise SystemExit("attempt 2 is allowed only after attempt 1 infra failure")
if prior.get("reason_code") not in policy["infra_retry_reasons"]:
    raise SystemExit("prior failure reason is not retryable infrastructure")
repo=pathlib.Path(sys.argv[3])
raw=repo/prior["raw_root"]
sys.path.insert(0,str(repo))
from orchestrator.campaign.silo_ladder_rung1 import (
    sha256_file, validate_attempt_subtree,
)
validate_attempt_subtree(raw, 1)
if sha256_file(raw/"attempt-receipt.json") != prior["attempt_receipt_sha256"]:
    raise SystemExit("prior attempt seal hash mismatch")
seal_ref=prior["campaign_attempt_root_receipt"]
seal=repo/seal_ref["path"]
if sha256_file(seal) != seal_ref["sha256"]:
    raise SystemExit("prior campaign-root attempt receipt hash mismatch")
seal_doc=json.load(open(seal,encoding="utf-8"))
if not (
    seal_doc["campaign_id"] == prior["campaign_id"]
    and seal_doc["attempt"] == 1
    and seal_doc["job_id"] == prior["pbs_jobid"]
    and seal_doc["nonce"] == prior["submission_nonce"]
    and seal_doc["submit_receipt_sha256"] == prior["submit_receipt_sha256"]
    and seal_doc["attempt_receipt_sha256"] == prior["attempt_receipt_sha256"]
    and seal_doc["failure_class"] == "infra"
    and seal_doc["reason_code"] == prior["reason_code"]
):
    raise SystemExit("prior campaign-root attempt receipt content mismatch")
PY
  PRIOR_GAP_SHA=$(sha256sum "$PRIOR_GAP_RESULT" | awk '{print $1}')
  PRIOR_GAP_REAL=$(realpath -e -- "$PRIOR_GAP_RESULT")
  case "$PRIOR_GAP_REAL" in
    "$REPO_ROOT"/output/env/pegasus/silo_ladder_rung1/job-staging/*/gap-result.json) ;;
    *) echo "prior gap result is outside the rung1 job-staging namespace" >&2; exit 2 ;;
  esac
  PRIOR_GAP_REL=${PRIOR_GAP_REAL#"$REPO_ROOT"/}
fi

SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD)
[[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]
WHOLE_TREE_STATUS=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)
if [[ -n "$WHOLE_TREE_STATUS" ]]; then
  echo "whole tree is not clean; submission aborted" >&2
  exit 2
fi

NONCE=$(python3 -I -B - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)
RUNTIME="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging"
ATTEMPTS="$RUNTIME/campaigns"
SUBMISSION="$RUNTIME/submissions/$NONCE"
mkdir -p "$RUNTIME/submissions" "$ATTEMPTS"
mkdir "$SUBMISSION"
set -o noclobber

# Compute node は network/DNS を持たないため、login node 上で pinned clone を永続化する。
# 既存 clone は fetch せず、HEAD と clean status だけを照合する。
THIRD_PARTY_ROOT="$RUNTIME/thirdparty-src"
mkdir -p "$THIRD_PARTY_ROOT"
readarray -t third_party_rows < <(python3 -I -B - "$REPO_ROOT" <<'PY'
import pathlib,sys
sys.path.insert(0,sys.argv[1])
from orchestrator.campaign.silo_ladder_rung1 import third_party_policy
items=third_party_policy(pathlib.Path(sys.argv[1]))
for item in items:
    print("\t".join((
        item["name"],item["source_name"],item["url"],item["pin"],
    )))
PY
)
[[ ${#third_party_rows[@]} -eq 3 ]]
# find_package dependencies are separate from the three FetchContent sources.
readarray -t build_dependency_rows < <(python3 -I -B - "$POLICY" <<'PY_BUILD_DEPS'
import json, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
for name in ("gflags", "glog"):
    print("\t".join((name, name, policy[f"{name}_source_url"], policy[f"{name}_expected_head"])))
PY_BUILD_DEPS
)
[[ ${#build_dependency_rows[@]} -eq 2 ]]
for row in "${third_party_rows[@]}" "${build_dependency_rows[@]}"; do
  IFS=$'\t' read -r third_name third_source_name third_url third_pin <<<"$row"
  [[ "$third_name" =~ ^[a-z][a-z0-9_-]*$ ]]
  [[ "$third_source_name" =~ ^[a-z][a-z0-9_-]*$ ]]
  [[ "$third_url" == https://github.com/*.git ]]
  [[ "$third_pin" =~ ^[0-9a-f]{40}$ ]]
  destination="$THIRD_PARTY_ROOT/$third_source_name"
  if [[ ! -e "$destination" && ! -L "$destination" ]]; then
    stage=$(mktemp -d "$THIRD_PARTY_ROOT/.${third_source_name}.XXXXXX")
    if ! git clone --no-checkout -- "$third_url" "$stage/repo"; then
      rm -rf -- "$stage"
      echo "third-party clone failed: $third_name" >&2
      exit 2
    fi
    if ! git -C "$stage/repo" checkout --detach "$third_pin"; then
      rm -rf -- "$stage"
      echo "third-party checkout failed: $third_name" >&2
      exit 2
    fi
    if ! python3 -I -B - "$stage/repo" "$destination" <<'PY'
import os,sys
os.rename(sys.argv[1],sys.argv[2])
PY
    then
      rm -rf -- "$stage"
      echo "third-party publish race/failure: $third_name" >&2
      exit 2
    fi
    rmdir "$stage"
  fi
  verify_third_party_pinned_clean \
    "$destination" "$third_pin" "$third_name" || exit 2
done
THIRD_PARTY_HEADS="$SUBMISSION/third-party-heads.json"
python3 -I -B - "$POLICY" "$THIRD_PARTY_ROOT" "$THIRD_PARTY_HEADS" <<'PY'
import json,pathlib,subprocess,sys
policy=json.load(open(sys.argv[1],encoding="utf-8"))["silo_ladder_rung1"][
    "third_party_sources"
]
root=pathlib.Path(sys.argv[2])
heads={}
for item in policy:
    source=root/item["source_name"]
    head=subprocess.run(
        ["git","-C",str(source),"rev-parse","--verify","HEAD"],
        check=True,capture_output=True,text=True,
    ).stdout.strip()
    status=subprocess.run(
        ["git","-C",str(source),"status","--porcelain","--untracked-files=all"],
        check=True,capture_output=True,text=True,
    ).stdout
    if head != item["pin"] or status:
        raise SystemExit(f"{item['name']} changed during receipt freeze")
    heads[item["name"]]=head
with open(sys.argv[3],"x",encoding="utf-8") as handle:
    json.dump(heads,handle,sort_keys=True,indent=2)
    handle.write("\n")
PY

if [[ "$PREPARE_THIRD_PARTY_ONLY" -eq 1 ]]; then
  rm -f -- "$THIRD_PARTY_HEADS"
  rmdir "$SUBMISSION"
  echo "third-party sources prepared: $THIRD_PARTY_ROOT"
  exit 0
fi

python3 -I -B - "$CORRECTNESS_JSON" "$REPO_ROOT" \
  >"$SUBMISSION/correctness-verify.stdout" \
  2>"$SUBMISSION/correctness-verify.stderr" <<'PY'
import json,sys
sys.path.insert(0,sys.argv[2])
from orchestrator.campaign import silo_ladder_rung1 as driver
leg=json.load(open(sys.argv[1],encoding="utf-8"))
failures=driver._validate_correctness(leg)
if failures:
    raise SystemExit(repr(failures))
print("correctness-leg accepted")
PY
python3 -I -B - "$SUBMISSION/schedule-receipt.json" "$REPO_ROOT" \
  "$ATTEMPT_NUMBER" "$PRIOR_GAP_RESULT" <<'PY'
import json,sys
sys.path.insert(0, sys.argv[2])
from orchestrator.campaign.silo_ladder_rung1 import generate_schedule
if int(sys.argv[3]) == 1:
    schedule=generate_schedule()
else:
    schedule=json.load(open(sys.argv[4],encoding="utf-8"))["schedule_receipt"]
from pathlib import Path
from orchestrator.campaign.silo_ladder_rung1 import publish_create_only_json
publish_create_only_json(Path(sys.argv[1]), schedule,
                         staging_dir=Path(sys.argv[1]).parent)
PY

capture() {
  local name=$1
  shift
  set +e
  "$@" >"$SUBMISSION/$name.stdout" 2>"$SUBMISSION/$name.stderr"
  local rc=$?
  set -e
  printf '%s\n' "$rc" >"$SUBMISSION/$name.rc"
  return "$rc"
}
if [[ "$DRY_RUN" -eq 0 ]]; then
  preflight_rc=0
  capture qstat_Q qstat -Q || preflight_rc=1
  capture pegasusinfo pegasusinfo || preflight_rc=1
  capture rbudgetcheck rbudgetcheck || preflight_rc=1
  capture check_quota check_quota || preflight_rc=1
  [[ "$preflight_rc" -eq 0 ]] || { echo "preflight failed" >&2; exit 3; }
else
  for name in qstat_Q pegasusinfo rbudgetcheck check_quota; do
    printf '%s\n' "not run (--dry-run)" >"$SUBMISSION/$name.stdout"
    : >"$SUBMISSION/$name.stderr"
    printf '0\n' >"$SUBMISSION/$name.rc"
  done
fi

JOB_SHA=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
DRIVER_SHA=$(sha256sum "$DRIVER" | awk '{print $1}')
SUBMITTER_SHA=$(sha256sum "$REPO_ROOT/tools/pegasus/submit_silo_ladder_rung1.sh" | awk '{print $1}')
VERIFIER_SHA=$(sha256sum "$REPO_ROOT/orchestrator/verifier/report.py" | awk '{print $1}')
POLICY_SHA=$(sha256sum "$POLICY" | awk '{print $1}')
RUNTIME_MODULES_SHA=$(python3 -I -B - "$REPO_ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign.silo_ladder_rung1 import runtime_modules_sha256
print(runtime_modules_sha256(__import__("pathlib").Path(sys.argv[1])))
PY
)
PATCH_SHA=$(sha256sum "$REPO_ROOT/patches/silo_ladder_rung1.patch" | awk '{print $1}')
LEDGER_SHA=$(sha256sum "$REPO_ROOT/patches/ledger.json" | awk '{print $1}')
CORRECTNESS_SHA=$(sha256sum "$CORRECTNESS_JSON" | awk '{print $1}')
SCHEDULE_SHA=$(sha256sum "$SUBMISSION/schedule-receipt.json" | awk '{print $1}')
CAMPAIGN_ID=$(python3 -I -B - "$SOURCE_COMMIT" "$CORRECTNESS_SHA" "$JOB_SHA" \
  "$DRIVER_SHA" "$SUBMITTER_SHA" "$VERIFIER_SHA" "$POLICY_SHA" "$PATCH_SHA" \
  "$LEDGER_SHA" "$RUNTIME_MODULES_SHA" <<'PY'
import hashlib,sys
print(hashlib.sha256(("\0".join(sys.argv[1:])+"\0").encode()).hexdigest())
PY
)
CAMPAIGN_ROOT="$ATTEMPTS/$CAMPAIGN_ID"
if [[ "$ATTEMPT_NUMBER" -eq 1 ]]; then
  mkdir "$CAMPAIGN_ROOT"
else
  PRIOR_CAMPAIGN_ID=$(python3 -I -B - "$PRIOR_GAP_RESULT" <<'PY'
import json,sys
print(json.load(open(sys.argv[1],encoding="utf-8"))["campaign_id"])
PY
)
  [[ "$PRIOR_CAMPAIGN_ID" == "$CAMPAIGN_ID" ]] || {
    echo "prior attempt belongs to a different campaign root" >&2; exit 2;
  }
  [[ -d "$CAMPAIGN_ROOT" && ! -L "$CAMPAIGN_ROOT" ]] || {
    echo "attempt 2 campaign root receipt is absent" >&2; exit 2;
  }
  python3 -I -B - "$PRIOR_GAP_RESULT" "$CAMPAIGN_ROOT" "$REPO_ROOT" <<'PY'
import json,pathlib,sys
prior=json.load(open(sys.argv[1],encoding="utf-8"))
campaign=pathlib.Path(sys.argv[2]).resolve()
repo=pathlib.Path(sys.argv[3]).resolve()
expected=(campaign/"attempt-1/attempt-root-receipt.json").resolve()
actual=(repo/prior["campaign_attempt_root_receipt"]["path"]).resolve()
if actual != expected:
    raise SystemExit("prior attempt seal is outside this campaign root")
submit_path=repo/prior["raw_root"]/"submit-receipt.json"
from hashlib import sha256
if sha256(submit_path.read_bytes()).hexdigest() != prior["submit_receipt_sha256"]:
    raise SystemExit("prior sealed submit receipt hash mismatch")
submit=json.load(open(submit_path,encoding="utf-8"))
if not (
    submit["campaign_id"] == prior["campaign_id"]
    and submit["nonce"] == prior["submission_nonce"]
    and submit["campaign_root_receipt"]["path"]
    == str((campaign/"root-receipt.json").relative_to(repo))
):
    raise SystemExit("prior submit receipt is not rooted in this campaign")
PY
fi
mkdir "$CAMPAIGN_ROOT/attempt-$ATTEMPT_NUMBER"
python3 -I -B - "$CAMPAIGN_ROOT/root-receipt.json" "$REPO_ROOT" \
  "$CAMPAIGN_ID" "$SOURCE_COMMIT" "$SCHEDULE_SHA" "$CORRECTNESS_SHA" \
  "$JOB_SHA" "$DRIVER_SHA" "$SUBMITTER_SHA" "$VERIFIER_SHA" "$POLICY_SHA" \
  "$PATCH_SHA" "$LEDGER_SHA" "$RUNTIME_MODULES_SHA" "$ATTEMPT_NUMBER" \
  "$SUBMISSION/schedule-receipt.json" "$THIRD_PARTY_HEADS" <<'PY'
import json,pathlib,sys
from hashlib import sha256
path,repo,campaign,commit,schedule_sha,correctness_sha,job_sha,driver_sha,\
submitter_sha,verifier_sha,policy_sha,patch_sha,ledger_sha,runtime_modules_sha,\
attempt,schedule_path,third_party_heads_path=sys.argv[1:]
sys.path.insert(0,repo)
from orchestrator.campaign.silo_ladder_rung1 import (
    PIN, SOURCE_FILES, _expected_patched_source_hashes,
    publish_create_only_json,
)
root=pathlib.Path(repo)
def pinned_source_hash(relative):
    import subprocess
    raw=subprocess.run(
        ["git","-C",str(root/"external/ccbench"),"show",f"{PIN}:{relative}"],
        check=True,capture_output=True,
    ).stdout
    return sha256(raw).hexdigest()
doc={
 "schema_version":"silo_ladder_rung1-campaign-root/v1",
 "campaign_id":campaign,
 "source_commit":commit,
 "attempt_chain":[1,2],
 "first_attempt":int(attempt),
 "schedule_receipt":json.load(open(schedule_path,encoding="utf-8")),
 "bindings":{
   "schedule_sha256":schedule_sha,"correctness_sha256":correctness_sha,
   "job_script_sha256":job_sha,"driver_sha256":driver_sha,
   "submitter_sha256":submitter_sha,"verifier_module_sha256":verifier_sha,
   "policy_sha256":policy_sha,"patch_sha256":patch_sha,
   "ledger_sha256":ledger_sha,"runtime_modules_sha256":runtime_modules_sha,
   "third_party_heads":json.load(
      open(third_party_heads_path,encoding="utf-8")
   ),
   "ccbench_pin_full":PIN,
   "pinned_source_sha256":{
      relative:pinned_source_hash(relative) for relative in SOURCE_FILES
   },
   "expected_patched_source_sha256":_expected_patched_source_hashes(
      root/"external/ccbench",root/"patches/silo_ladder_rung1.patch"
   ),
 },
}
target=pathlib.Path(path)
if int(attempt)==1:
    publish_create_only_json(target,doc,staging_dir=target.parent)
else:
    existing=json.load(open(target,encoding="utf-8"))
    if existing != {**doc,"first_attempt":1}:
        raise SystemExit("campaign root receipt/input drift")
PY

if [[ "$DRY_RUN" -eq 1 ]]; then
  REQUEST_ID="dry-run-$NONCE"
  printf 'dry-run\n' >"$SUBMISSION/qsub.stdout"
  : >"$SUBMISSION/qsub.stderr"
  printf '0\n' >"$SUBMISSION/qsub.rc"
  printf 'dry-run\n' >"$SUBMISSION/qstat-after-qsub.stdout"
  : >"$SUBMISSION/qstat-after-qsub.stderr"
  printf '0\n' >"$SUBMISSION/qstat-after-qsub.rc"
else
  set +e
  (
    cd "$REPO_ROOT"
    qsub -v "IZANAGI_SUBMISSION_NONCE=$NONCE,IZANAGI_ATTEMPT_NUMBER=$ATTEMPT_NUMBER" \
      "$JOB_SCRIPT"
  ) >"$SUBMISSION/qsub.stdout" 2>"$SUBMISSION/qsub.stderr"
  qsub_rc=$?
  set -e
  printf '%s\n' "$qsub_rc" >"$SUBMISSION/qsub.rc"
  [[ "$qsub_rc" -eq 0 ]] || exit "$qsub_rc"
  REQUEST_ID=$(python3 -I -B - "$SUBMISSION/qsub.stdout" <<'PY'
import re,sys
text=open(sys.argv[1],encoding="utf-8",errors="replace").read()
m=re.search(r"Request\s+(\S+)\s+submitted",text)
if m: print(m.group(1).rstrip("."))
elif len(text.split()) == 1: print(text.split()[0])
else: raise SystemExit(2)
PY
)
  set +e
  qstat -f "${REQUEST_ID#0:}" >"$SUBMISSION/qstat-after-qsub.stdout" \
    2>"$SUBMISSION/qstat-after-qsub.stderr"
  qstat_rc=$?
  set -e
  printf '%s\n' "$qstat_rc" >"$SUBMISSION/qstat-after-qsub.rc"
  [[ "$qstat_rc" -eq 0 ]] || {
    echo "qsub succeeded but immediate qstat visibility failed" >&2; exit 4;
  }
fi

python3 -I -B - "$SUBMISSION" "$NONCE" "$REQUEST_ID" "$SOURCE_COMMIT" \
  "$PROJECT" "$QUEUE" "$NODES" "$WALLTIME_S" "$DRY_RUN" "$JOB_SHA" \
  "$DRIVER_SHA" "$PATCH_SHA" "$LEDGER_SHA" "$CORRECTNESS_SHA" "$SCHEDULE_SHA" \
  "$ATTEMPT_NUMBER" "$PRIOR_GAP_SHA" "$PRIOR_GAP_RESULT" "$PRIOR_GAP_REL" \
  "$SUBMITTER_SHA" "$VERIFIER_SHA" "$POLICY_SHA" "$CAMPAIGN_ID" \
  "$RUNTIME_MODULES_SHA" "$CAMPAIGN_ROOT/root-receipt.json" "$REPO_ROOT" \
  "$(pwd -P)" "$THIRD_PARTY_HEADS" <<'PY'
import json, pathlib, sys, time
(root,nonce,job,commit,project,queue,nodes,walltime,dry,job_sha,driver_sha,
 patch_sha,ledger_sha,correctness_sha,schedule_sha,attempt_number,
 prior_gap_sha,prior_gap_path,prior_gap_rel,submitter_sha,verifier_sha,
 policy_sha,campaign_id,runtime_modules_sha,campaign_receipt_path,repo_root,
 caller_cwd,third_party_heads_path)=sys.argv[1:]
root=pathlib.Path(root)
sys.path.insert(0,repo_root)
from orchestrator.campaign.silo_ladder_rung1 import publish_create_only_json
schedule=json.load(open(root/"schedule-receipt.json",encoding="utf-8"))
prior_attempt=None
if int(attempt_number) == 2:
    prior=json.load(open(prior_gap_path,encoding="utf-8"))
    prior_attempt={"attempt":1,"failure_class":"infra",
                   "reason_code":prior["reason_code"],
                   "raw_root":prior["raw_root"],
                   "attempt_receipt_sha256":prior["attempt_receipt_sha256"],
                   "job_id":prior["pbs_jobid"],
                   "nonce":prior["submission_nonce"],
                   "submit_receipt_sha256":prior["submit_receipt_sha256"],
                   "campaign_attempt_root_receipt":
                       prior["campaign_attempt_root_receipt"]}
def raw(name):
    return (root/name).read_text(encoding="utf-8",errors="replace")
preflight={}
for name in ("qstat_Q","pegasusinfo","rbudgetcheck","check_quota"):
    preflight[name]={"rc":int(raw(name+".rc").strip()),
                     "stdout_raw":raw(name+".stdout"),
                     "stderr_raw":raw(name+".stderr")}
doc={"schema_version":"silo_ladder_rung1-submit-receipt/v1",
     "nonce":nonce,"source_commit":commit,"whole_tree_clean":True,
     "campaign_id":campaign_id,
     "campaign_root_receipt":{"path":str(pathlib.Path(campaign_receipt_path).relative_to(repo_root)),
                              "sha256":__import__("hashlib").sha256(pathlib.Path(campaign_receipt_path).read_bytes()).hexdigest()},
     "submission_cwd":{"caller":caller_cwd,
                       "repo_root_realpath":str(pathlib.Path(repo_root).resolve()),
                       "qsub_cwd_realpath":str(pathlib.Path(repo_root).resolve())},
     "attempt_number":int(attempt_number),
     "prior_gap_result_sha256":prior_gap_sha or None,
     "prior_attempt":prior_attempt,
     "bindings":{"job_script_sha256":job_sha,"driver_sha256":driver_sha,
                 "patch_sha256":patch_sha,"ledger_sha256":ledger_sha,
                 "correctness_sha256":correctness_sha,
                 "schedule_sha256":schedule_sha,
                 "submitter_sha256":submitter_sha,
                 "verifier_module_sha256":verifier_sha,
                 "policy_sha256":policy_sha,
                 "runtime_modules_sha256":runtime_modules_sha,
                 "third_party_heads":json.load(
                     open(third_party_heads_path,encoding="utf-8")
                 )},
     "request":{"project":project,"queue":queue,"nodes":int(nodes),
                "elapstim_req_s":int(walltime)},
     "qsub":{"request_id":job,"rc":int(raw("qsub.rc").strip()),
             "stdout_raw":raw("qsub.stdout"),"stderr_raw":raw("qsub.stderr"),
             "qstat_rc":int(raw("qstat-after-qsub.rc").strip()),
             "qstat_stdout_raw":raw("qstat-after-qsub.stdout"),
             "qstat_stderr_raw":raw("qstat-after-qsub.stderr")},
     "preflight":preflight,"schedule_receipt":schedule,
     "submitted_epoch":int(time.time()),"dry_run":bool(int(dry))}
publish_create_only_json(root/"submit-receipt.json",doc,staging_dir=root)
PY
echo "submit receipt: $SUBMISSION/submit-receipt.json"
echo "request ID: $REQUEST_ID"
