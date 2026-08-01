#!/bin/bash
# Login-side create-only submitter for the T-126 qualification job.
set -Eeuo pipefail
umask 077

usage() {
  echo "usage: submit_t126_qualification.sh [--dry-run] [--retry-from FAILURE-RECEIPT]" >&2
}

DRY_RUN=0
RETRY_FROM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --retry-from)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      RETRY_FROM=$2
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}") || exit 2
[[ -f "$SCRIPT_PATH" && ! -L "$SCRIPT_PATH" ]] || exit 2
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..") || exit 2
OUTPUT_ROOT="$REPO_ROOT/output"
QUAL_ROOT="$OUTPUT_ROOT/env/pegasus/qualification/t126"
POLICY="$SCRIPT_DIR/policy.json"
JOB_SCRIPT="$SCRIPT_DIR/t126_qualification.sh"
PROTOCOL="$REPO_ROOT/orchestrator/qualification/t126_control_v1.json"
# T-126 owns its own PBS reservation policy.  The shared Pegasus policy keeps
# only shared values (project/queue/nodes/...); it must stay byte-stable for
# the other campaigns that pin it in committed evidence.
RESERVATION_POLICY="$REPO_ROOT/orchestrator/qualification/t126_reservation_policy_v1.json"
COLLECTOR="$SCRIPT_DIR/collect_t126_qualification.py"
SUBMISSION_HELPER="$REPO_ROOT/orchestrator/qualification/submission.py"

OUTPUT_ROOT_REAL=$(realpath -e -- "$OUTPUT_ROOT") || exit 2
assert_safe_submit_path() {
  local target=$1 relative current component resolved
  local -a components
  [[ "$target" == "$OUTPUT_ROOT" || "$target" == "$OUTPUT_ROOT/"* ]] || return 1
  relative=${target#"$REPO_ROOT"/}
  current="$REPO_ROOT"
  IFS='/' read -r -a components <<<"$relative"
  for component in "${components[@]}"; do
    [[ -n "$component" && "$component" != "." && "$component" != ".." ]] || return 1
    current="$current/$component"
    [[ ! -L "$current" ]] || return 1
  done
  resolved=$(realpath -m -- "$target") || return 1
  [[ "$resolved" == "$OUTPUT_ROOT_REAL" || "$resolved" == "$OUTPUT_ROOT_REAL/"* ]]
}

[[ -d "$OUTPUT_ROOT" && ! -L "$OUTPUT_ROOT" ]] || {
  echo "output root must be a non-symlink directory" >&2
  exit 2
}
[[ -f "$POLICY" && ! -L "$POLICY" && -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]] || {
  echo "policy/job script missing or symlinked" >&2
  exit 2
}
[[ -f "$PROTOCOL" && ! -L "$PROTOCOL" && -f "$COLLECTOR" && ! -L "$COLLECTOR" ]] || {
  echo "protocol/collector missing or symlinked" >&2
  exit 2
}
[[ -f "$RESERVATION_POLICY" && ! -L "$RESERVATION_POLICY" ]] || {
  echo "T-126 reservation policy missing or symlinked" >&2
  exit 2
}
[[ -f "$SUBMISSION_HELPER" && ! -L "$SUBMISSION_HELPER" ]] || exit 2

SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD)
SOURCE_TREE=$(git -C "$REPO_ROOT" rev-parse --verify 'HEAD^{tree}')
CCBENCH_GITLINK=$(git -C "$REPO_ROOT" rev-parse --verify HEAD:external/ccbench)
[[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ && "$SOURCE_TREE" =~ ^[0-9a-f]{40}$ \
  && "$CCBENCH_GITLINK" =~ ^[0-9a-f]{40}$ ]] || {
  echo "full source/tree/gitlink identity unavailable" >&2
  exit 2
}
git -C "$REPO_ROOT" diff --quiet HEAD -- || {
  echo "tracked worktree is dirty" >&2
  exit 2
}
git -C "$REPO_ROOT" diff --cached --quiet HEAD -- || {
  echo "index is dirty" >&2
  exit 2
}
if [[ "$(git -C "$REPO_ROOT/external/ccbench" rev-parse HEAD)" != "$CCBENCH_GITLINK" ]] \
    || [[ -n "$(git -C "$REPO_ROOT/external/ccbench" status --porcelain --untracked-files=all)" ]]; then
  echo "CCBench gitlink is uninitialized or not pinned-clean" >&2
  exit 2
fi
UNTRACKED_LIST=$(mktemp "${TMPDIR:-/tmp}/izanagi-t126-untracked.XXXXXX") || exit 2
untracked_rc=0
git -C "$REPO_ROOT" ls-files --others --exclude-standard -z \
  >"$UNTRACKED_LIST" || untracked_rc=$?
if [[ "$untracked_rc" -ne 0 ]]; then
  rm -f -- "$UNTRACKED_LIST"
  echo "cannot inspect untracked repository content" >&2
  exit "$untracked_rc"
fi
while IFS= read -r -d '' untracked; do
  [[ "$untracked" == output/* ]] || {
    printf 'untracked path outside output/: %q\n' "$untracked" >&2
    rm -f -- "$UNTRACKED_LIST"
    exit 2
  }
done <"$UNTRACKED_LIST"
rm -f -- "$UNTRACKED_LIST"
if git -C "$REPO_ROOT" ls-files -v | grep -Eq '^[a-zS]'; then
  echo "assume-unchanged/skip-worktree source is forbidden" >&2
  exit 2
fi

for tracked in \
  tools/pegasus/t126_qualification.sh \
  tools/pegasus/collect_t126_qualification.py \
  orchestrator/qualification/t126_control_v1.json \
  orchestrator/qualification/t126_reservation_policy_v1.json \
  orchestrator/qualification/submission.py; do
  git -C "$REPO_ROOT" ls-files --error-unmatch -- "$tracked" >/dev/null || {
    echo "required execution input is not tracked: $tracked" >&2
    exit 2
  }
done

SUBMISSION_STAGE=$(mktemp -d "${TMPDIR:-/tmp}/izanagi-t126-submit-stage.XXXXXX") \
  || exit 2
cleanup_submission_stage() {
  rm -rf -- "$SUBMISSION_STAGE"
}
trap cleanup_submission_stage EXIT
git -C "$REPO_ROOT" archive --format=tar "$SOURCE_COMMIT" \
  orchestrator tools/pegasus/policy.json \
  | tar -xf - -C "$SUBMISSION_STAGE"
SUBMISSION_HELPER="$SUBMISSION_STAGE/orchestrator/qualification/submission.py"
STAGED_ORCHESTRATOR="$SUBMISSION_STAGE/orchestrator"
[[ -f "$SUBMISSION_HELPER" && ! -L "$SUBMISSION_HELPER" ]] || exit 2

for tracked in \
  tools/pegasus/submit_t126_qualification.sh \
  tools/pegasus/t126_qualification.sh \
  tools/pegasus/collect_t126_qualification.py \
  tools/pegasus/policy.json \
  orchestrator/qualification/t126_control_v1.json \
  orchestrator/qualification/t126_reservation_policy_v1.json \
  orchestrator/qualification/submission.py; do
  committed_sha=$(git -C "$REPO_ROOT" cat-file blob "$SOURCE_COMMIT:$tracked" \
    | sha256sum | awk '{print $1}') || exit 2
  current_sha=$(sha256sum "$REPO_ROOT/$tracked" | awk '{print $1}') || exit 2
  [[ "$committed_sha" == "$current_sha" ]] || {
    echo "hidden dirty execution input: $tracked" >&2
    exit 2
  }
done

# Shared values only: the shared Pegasus policy is not T-126 property.
readarray -t POLICY_VALUES < <(python3 -I -B - "$POLICY" <<'PY'
import json, sys
def no_dups(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise SystemExit("duplicate policy key")
        out[k] = v
    return out
p = json.load(open(sys.argv[1], encoding="utf-8"), object_pairs_hook=no_dups)
keys = ("project", "queue", "nodes")
for key in keys:
    if key not in p:
        raise SystemExit("missing policy key: " + key)
if p["nodes"] != 1:
    raise SystemExit("T-126 policy envelope mismatch")
for key in ("project", "queue", "nodes"):
    print(p[key])
PY
)
[[ ${#POLICY_VALUES[@]} -eq 3 ]] || exit 2
PROJECT=${POLICY_VALUES[0]}
QUEUE=${POLICY_VALUES[1]}
NODES=${POLICY_VALUES[2]}

# T-126-owned PBS reservation policy.  Same required keys, same walltime
# derivation, same rejection conditions as before; only the file moved.
readarray -t RESERVATION_VALUES < <(python3 -I -B - "$RESERVATION_POLICY" <<'PY'
import json, sys
def no_dups(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise SystemExit("duplicate reservation policy key")
        out[k] = v
    return out
p = json.load(open(sys.argv[1], encoding="utf-8"), object_pairs_hook=no_dups)
keys = (
    "t126_qualification_walltime",
    "t126_qualification_walltime_s", "t126_qualification_member_cap_s",
    "t126_qualification_round_gap_s", "t126_qualification_prologue_cap_s",
    "t126_qualification_attestation_cap_s",
    "t126_qualification_finalize_reserve_s", "t126_qualification_wmax_s",
)
for key in keys:
    if key not in p:
        raise SystemExit("missing reservation policy key: " + key)
calculated = (
    p["t126_qualification_prologue_cap_s"]
    + 16 * p["t126_qualification_member_cap_s"]
    + 7 * p["t126_qualification_round_gap_s"]
    + p["t126_qualification_attestation_cap_s"]
    + p["t126_qualification_finalize_reserve_s"]
)
if (p["t126_qualification_member_cap_s"] != 900
        or p["t126_qualification_round_gap_s"] != 1800
        or calculated != 29100 or p["t126_qualification_wmax_s"] != calculated
        or p["t126_qualification_walltime_s"] != 36000
        or calculated >= p["t126_qualification_walltime_s"]):
    raise SystemExit("T-126 reservation policy mismatch")
for key in ("t126_qualification_walltime",
            "t126_qualification_walltime_s", "t126_qualification_wmax_s"):
    print(p[key])
PY
)
[[ ${#RESERVATION_VALUES[@]} -eq 3 ]] || exit 2
WALLTIME=${RESERVATION_VALUES[0]}
WALLTIME_S=${RESERVATION_VALUES[1]}
WMAX_S=${RESERVATION_VALUES[2]}
[[ "$PROJECT" == SFC && "$QUEUE" == gen_S && "$NODES" == 1 \
  && "$WALLTIME" == 10:00:00 && "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 ]] || exit 2

RETRY_INDEX=0
RETRY_ATTEMPT_ID=""
RETRY_SERIES_ID=""
RETRY_RECEIPT_SHA256=""
if [[ -n "$RETRY_FROM" ]]; then
  [[ -f "$RETRY_FROM" && ! -L "$RETRY_FROM" ]] || {
    echo "retry receipt must be a non-symlink regular file" >&2
    exit 2
  }
  readarray -t RETRY_ID < <(python3 -I -B - "$RETRY_FROM" "$REPO_ROOT" \
    "$STAGED_ORCHESTRATOR" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from qualification.artifacts import validate_failure_receipt_for_retry
from qualification.contract import load_protocol
d=validate_failure_receipt_for_retry(
    Path(sys.argv[1]),Path(sys.argv[2]),load_protocol())
print(d["qualification_attempt_id"])
print(d["qualification_series_id"])
attempt=Path(sys.argv[1]).resolve().parent
identity=json.load(open(attempt/"series-identity.json",encoding="utf-8"))
print(identity["superproject_commit"])
PY
  )
  [[ ${#RETRY_ID[@]} -eq 3 && "${RETRY_ID[0]}" =~ ^[0-9a-f]{64}$ \
    && "${RETRY_ID[1]}" =~ ^[0-9a-f]{64}$ \
    && "${RETRY_ID[2]}" == "$SOURCE_COMMIT" ]] || exit 2
  RETRY_ATTEMPT_ID=${RETRY_ID[0]}
  RETRY_SERIES_ID=${RETRY_ID[1]}
  RETRY_RECEIPT_SHA256=$(sha256sum "$RETRY_FROM" | awk '{print $1}')
  [[ "$RETRY_RECEIPT_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 2
  RETRY_INDEX=1
fi

for namespace in "$QUAL_ROOT" "$QUAL_ROOT/submissions" "$QUAL_ROOT/series"; do
  assert_safe_submit_path "$namespace" || {
    echo "unsafe qualification namespace component" >&2
    exit 2
  }
done
mkdir -p "$QUAL_ROOT/submissions" "$QUAL_ROOT/series"
for namespace in "$QUAL_ROOT" "$QUAL_ROOT/submissions" "$QUAL_ROOT/series"; do
  assert_safe_submit_path "$namespace" || {
    echo "unsafe qualification namespace after creation" >&2
    exit 2
  }
done
[[ ! -L "$QUAL_ROOT" && ! -L "$QUAL_ROOT/submissions" && ! -L "$QUAL_ROOT/series" ]] || {
  echo "qualification namespace contains a symlink" >&2
  exit 2
}
NONCE=$(python3 -I -B -c 'import secrets; print(secrets.token_hex(16))')
SUBMISSION_DIR="$QUAL_ROOT/submissions/$NONCE"
mkdir "$SUBMISSION_DIR"
assert_safe_submit_path "$SUBMISSION_DIR" || {
  echo "unsafe submission namespace after creation" >&2
  exit 2
}

capture() {
  local name=$1
  shift
  local rc=0
  "$@" >"$SUBMISSION_DIR/$name.stdout" 2>"$SUBMISSION_DIR/$name.stderr" || rc=$?
  printf '%s\n' "$rc" >"$SUBMISSION_DIR/$name.rc"
  return "$rc"
}
if [[ "$DRY_RUN" -eq 1 ]]; then
  for name in qstat_Q pegasusinfo rbudgetcheck check_quota; do
    printf '%s\n' "not run (--dry-run)" >"$SUBMISSION_DIR/$name.stdout"
    : >"$SUBMISSION_DIR/$name.stderr"
    printf '0\n' >"$SUBMISSION_DIR/$name.rc"
  done
else
  capture qstat_Q qstat -Q
  capture pegasusinfo pegasusinfo
  capture rbudgetcheck rbudgetcheck
  capture check_quota check_quota
  python3 -I -B - "$SUBMISSION_DIR" "$QUEUE" "$WALLTIME_S" <<'PY'
import re, sys
from pathlib import Path
root, queue, requested = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
def read(name, suffix):
    return (root / f"{name}.{suffix}").read_text(encoding="utf-8", errors="replace")
for name in ("qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"):
    if int(read(name, "rc").strip()) != 0:
        raise SystemExit(f"{name} failed")
    if not read(name, "stdout").strip():
        raise SystemExit(f"{name} returned empty output")
q = read("qstat_Q", "stdout")
if queue not in q or not re.search(r"(?i)\b(ENA|ENABLE(?:D)?)\b", q) \
        or not re.search(r"(?i)\b(ACT|ACTIVE)\b", q):
    raise SystemExit("queue is not exact enabled/active")
limits = [int(v) for v in re.findall(r"(?i)(?:Max|Elapse[^=\n]*Limit)[^0-9]+([0-9]+)S", q)]
if not limits or max(limits) < requested:
    raise SystemExit("queue Max is below qualification walltime or unparseable")
budget = read("rbudgetcheck", "stdout")
remaining = re.findall(r"(?i)(?:remain(?:ing)?|balance|残)[^0-9-]*(-?[0-9]+(?:\.[0-9]+)?)", budget)
if not remaining or max(map(float, remaining)) <= 0:
    raise SystemExit("budget remaining is non-positive or unparseable")
quota = read("check_quota", "stdout")
percent = [int(v) for v in re.findall(r"([0-9]{1,3})%", quota)]
if percent and max(percent) >= 95:
    raise SystemExit("quota headroom is below 5%")
PY
fi

JOB_SCRIPT_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
COLLECTOR_SHA256=$(sha256sum "$COLLECTOR" | awk '{print $1}')
PROTOCOL_SHA256=$(sha256sum "$PROTOCOL" | awk '{print $1}')
for value in "$JOB_SCRIPT_SHA256" "$COLLECTOR_SHA256" "$PROTOCOL_SHA256"; do
  [[ "$value" =~ ^[0-9a-f]{64}$ ]] || exit 2
done

readarray -t SERIES_INFO < <(
  python3 -I -B "$SUBMISSION_HELPER" \
    --repo-root "$REPO_ROOT" --output-dir "$SUBMISSION_DIR"
)
[[ ${#SERIES_INFO[@]} -eq 3 && "${SERIES_INFO[0]}" =~ ^[0-9a-f]{64}$ ]] || exit 2
SERIES_ID=${SERIES_INFO[0]}
if [[ "$RETRY_INDEX" -eq 1 && "$RETRY_SERIES_ID" != "$SERIES_ID" ]]; then
  echo "retry source does not match the canonical series identity" >&2
  exit 2
fi

python3 -I -B - "$SUBMISSION_DIR/submission-intent.json" "$SERIES_ID" "$NONCE" \
  "$RETRY_INDEX" "$RETRY_ATTEMPT_ID" "$RETRY_RECEIPT_SHA256" <<'PY'
import json,os,sys,time
path,series_id,nonce,retry_index,retry_attempt,retry_receipt=sys.argv[1:]
p={"schema_version":"t126-qualification-submission-intent/v1",
   "qualification_lineage":"t126-only",
   "authority":"evidence-only/no-promotion","hold_enforced":False,
   "qualification_series_id":series_id,"nonce":nonce,
   "retry_index":int(retry_index),
   "retry_from_attempt_id":retry_attempt or None,
   "retry_from_receipt_sha256":retry_receipt or None,
   "prepared_epoch":int(time.time())}
data=(json.dumps(p,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
try:
    offset=0
    while offset<len(data):
        written=os.write(fd,data[offset:])
        if written<=0:
            raise RuntimeError("submission intent write made no progress")
        offset+=written
    os.fsync(fd)
finally:
    os.close(fd)
dfd=os.open(os.path.dirname(path),os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
try: os.fsync(dfd)
finally: os.close(dfd)
PY
INTENT_SHA256=$(sha256sum "$SUBMISSION_DIR/submission-intent.json" | awk '{print $1}')
[[ "$INTENT_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 2

reserve_series_attempt() {
  python3 -I -B - "$REPO_ROOT" "$STAGED_ORCHESTRATOR" "$SERIES_ID" "$NONCE" \
    "$INTENT_SHA256" "$RETRY_INDEX" "$RETRY_ATTEMPT_ID" \
    "$RETRY_RECEIPT_SHA256" <<'PY'
import sys
from pathlib import Path
repo=Path(sys.argv[1]); sys.path.insert(0,sys.argv[2])
series,nonce,intent,index,prior,prior_receipt=sys.argv[3:]
from qualification.artifacts import QualificationRoot
from qualification.attempt_ledger import SeriesAttemptLedger
from qualification.contract import load_protocol
protocol=load_protocol(Path(sys.argv[2])/"qualification/t126_control_v1.json")
ledger=SeriesAttemptLedger(
    QualificationRoot(repo).issue(),series,protocol["retry"]["eligible_reasons"])
index=int(index)
state=ledger.replay
expected_intent="initial_intent" if index==0 else "retry_intent"
expected_submitted="initial_submitted" if index==0 else "retry_submitted"
if state.state==expected_intent:
    print("resume-unbound",state.last_nonce,
          state.last_submission_intent_sha256,state.last_job_id or "",sep=":")
elif state.state==expected_submitted:
    receipt=(repo/"output/env/pegasus/qualification/t126/submissions"
             /state.last_nonce/"submit-receipt.json")
    abandoned=list(receipt.parent.glob(
        "."+receipt.name+".create-*"))
    if receipt.exists() and not abandoned:
        raise SystemExit("canonical series attempt already has a durable receipt")
    print("resume-bound",state.last_nonce,
          state.last_submission_intent_sha256,state.last_job_id or "",sep=":")
elif index==0:
    ledger.claim_initial(nonce=nonce,submission_intent_sha256=intent)
    print("reserved",nonce,intent,"",sep=":")
else:
    ledger.claim_retry(
        nonce=nonce,submission_intent_sha256=intent,
        retry_from_attempt_id=prior,retry_from_receipt_sha256=prior_receipt)
    print("reserved",nonce,intent,"",sep=":")
PY
}

create_qsub_invocation_claim() {
  python3 -I -S -B - "$SUBMISSION_DIR/qsub-invocation.json" "$NONCE" \
    "$INTENT_SHA256" "$RETRY_INDEX" <<'PY'
import json,os,sys
path,nonce,intent,index=sys.argv[1:]
value={"nonce":nonce,"retry_index":int(index),
       "submission_intent_sha256":intent}
data=(json.dumps(value,sort_keys=True,separators=(",",":"),
                 allow_nan=False)+"\n").encode("ascii")
flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)
try:
    fd=os.open(path,flags,0o600)
except FileExistsError:
    raise SystemExit(73)
try:
    offset=0
    while offset<len(data):
        requested=data[offset:]
        if (os.environ.get("IZANAGI_T126_TEST_INVOCATION_SHORT_WRITE")=="1"
                and offset==0):
            requested=requested[:1]
        written=os.write(fd,requested)
        if written<=0:
            raise RuntimeError("qsub invocation claim write made no progress")
        offset+=written
    os.fsync(fd)
finally:
    os.close(fd)
dfd=os.open(os.path.dirname(path),os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
try: os.fsync(dfd)
finally: os.close(dfd)
flags=os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)
fd=os.open(path,flags)
try:
    chunks=[]
    while True:
        block=os.read(fd,1024*1024)
        if not block: break
        chunks.append(block)
finally:
    os.close(fd)
actual=b"".join(chunks)
if actual!=data:
    raise RuntimeError("qsub invocation claim exact readback mismatch")
decoded=json.loads(actual.decode("ascii"))
if (type(decoded) is not dict or set(decoded)!=set(value)
        or decoded!=value
        or (json.dumps(decoded,sort_keys=True,separators=(",",":"),
                       allow_nan=False)+"\n").encode("ascii")!=actual):
    raise RuntimeError("qsub invocation claim is not exact canonical JSON")
import hashlib
print(hashlib.sha256(actual).hexdigest())
PY
}

load_qsub_invocation_claim() {
  python3 -I -S -B - "$SUBMISSION_DIR/qsub-invocation.json" "$NONCE" \
    "$INTENT_SHA256" "$RETRY_INDEX" <<'PY'
import hashlib,json,os,sys
path,nonce,intent,index=sys.argv[1:]
flags=os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)
fd=os.open(path,flags)
try:
    chunks=[]
    while True:
        block=os.read(fd,1024*1024)
        if not block: break
        chunks.append(block)
finally:
    os.close(fd)
raw=b"".join(chunks)
value=json.loads(raw.decode("ascii"))
expected={"nonce":nonce,"retry_index":int(index),
          "submission_intent_sha256":intent}
canonical=(json.dumps(value,sort_keys=True,separators=(",",":"),
                      allow_nan=False)+"\n").encode("ascii")
if (type(value) is not dict
        or type(value.get("retry_index")) is not int
        or value.get("retry_index") not in (0,1)
        or value!=expected or raw!=canonical):
    raise SystemExit("qsub invocation claim mismatch")
print(hashlib.sha256(raw).hexdigest())
PY
}

publish_qsub_binding() {
  python3 -I -S -B - "$SUBMISSION_DIR/qsub-binding.json" \
    "$SUBMISSION_DIR/qsub.stdout" "$NONCE" "$INTENT_SHA256" \
    "$INVOCATION_SHA256" "$RETRY_INDEX" "$STAGED_ORCHESTRATOR" <<'PY'
import json,sys
from pathlib import Path
path,stdout_path,nonce,intent,invocation,index,orchestrator=sys.argv[1:]
raw=Path(stdout_path).read_bytes()
try:
    stdout=raw.decode("utf-8",errors="strict")
except UnicodeDecodeError as exc:
    raise SystemExit("qsub stdout is not strict UTF-8") from exc
sys.path.insert(0,orchestrator)
from qualification.atomic_publish import publish_bytes
from qualification.qsub_binding import (
    job_id_from_qsub_stdout,validate_qsub_binding)
value={
    "schema_version":"t126-qsub-binding/v2",
    "job_id":job_id_from_qsub_stdout(stdout),
    "nonce":nonce,
    "submission_intent_sha256":intent,
    "qsub_invocation_sha256":invocation,
    "retry_index":int(index),
    "qsub_returncode":0,
    "qsub_stdout_raw":stdout,
}
validate_qsub_binding(value)
data=(json.dumps(value,sort_keys=True,separators=(",",":"),
                 allow_nan=False)+"\n").encode("ascii")
publish_bytes(Path(path),data)
print(value["job_id"])
PY
}

load_qsub_binding() {
  python3 -I -S -B - "$SUBMISSION_DIR/qsub-binding.json" \
    "$NONCE" "$INTENT_SHA256" "$INVOCATION_SHA256" "$RETRY_INDEX" \
    "$STAGED_ORCHESTRATOR" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[6])
from qualification.artifacts import load_json_strict
from qualification.qsub_binding import validate_qsub_binding
value=validate_qsub_binding(
    load_json_strict(Path(sys.argv[1])),
    expected_nonce=sys.argv[2],
    expected_intent_sha256=sys.argv[3],
    expected_invocation_sha256=sys.argv[4],
    expected_retry_index=int(sys.argv[5]))
print(value["job_id"])
PY
}

bind_qsub_attempt() {
  BINDING_SHA256=$(sha256sum "$SUBMISSION_DIR/qsub-binding.json" | awk '{print $1}')
  ATTEMPT_ID=$(python3 -I -B - "$STAGED_ORCHESTRATOR" "$SERIES_ID" "$JOB_ID" "$NONCE" \
    "$RETRY_INDEX" "$INTENT_SHA256" <<'PY'
import sys
sys.path.insert(0,sys.argv[1])
from qualification.contract import attempt_identity
_,series,job,nonce,index,intent=sys.argv[1:]
print(attempt_identity({
 "schema_version":"t126-qualification-attempt-identity/v1",
 "qualification_series_id":series,"pbs_job_id":job,"nonce":nonce,
 "retry_index":int(index),"submission_intent_sha256":intent}))
PY
  )
  python3 -I -B - "$REPO_ROOT" "$STAGED_ORCHESTRATOR" "$SERIES_ID" \
    "$RETRY_INDEX" "$NONCE" \
    "$JOB_ID" "$ATTEMPT_ID" "$INVOCATION_SHA256" "$BINDING_SHA256" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from qualification.artifacts import QualificationRoot
from qualification.attempt_ledger import SeriesAttemptLedger
from qualification.contract import load_protocol
repo=Path(sys.argv[1]); series,index,nonce,job,attempt,invocation,evidence=sys.argv[3:]
protocol=load_protocol(Path(sys.argv[2])/"qualification/t126_control_v1.json")
SeriesAttemptLedger(
    QualificationRoot(repo).issue(),series,
    protocol["retry"]["eligible_reasons"]).bind_submitted(
        retry_index=int(index),nonce=nonce,job_id=job,attempt_id=attempt,
        qsub_invocation_sha256=invocation,
        submission_evidence_sha256=evidence)
PY
}

recover_or_reject_unbound_invocation() {
  echo "qsub invocation has no durable v2 binding; automatic resubmit is forbidden" >&2
  return 1
}

if [[ "$DRY_RUN" -eq 1 ]]; then
  JOB_ID="dry-run-$NONCE"
  INVOCATION_SHA256=$(printf '%064d' 0)
  BINDING_SHA256=$(printf '%064d' 0)
  printf '%s\n' "dry-run: qsub was not executed" >"$SUBMISSION_DIR/qsub.stdout"
  : >"$SUBMISSION_DIR/qsub.stderr"
  printf '0\n' >"$SUBMISSION_DIR/qsub.rc"
else
  RESERVATION=$(reserve_series_attempt)
  IFS=: read -r RESERVATION_STATE RESERVED_NONCE RESERVED_INTENT RESERVED_JOB \
    <<<"$RESERVATION"
  [[ "$RESERVATION_STATE" =~ ^(reserved|resume-unbound|resume-bound)$ \
    && "$RESERVED_NONCE" =~ ^[0-9a-f]{32}$ \
    && "$RESERVED_INTENT" =~ ^[0-9a-f]{64}$ ]] || exit 2
  if [[ "$RESERVATION_STATE" != "reserved" ]]; then
    NONCE=$RESERVED_NONCE
    INTENT_SHA256=$RESERVED_INTENT
    SUBMISSION_DIR="$QUAL_ROOT/submissions/$NONCE"
    assert_safe_submit_path "$SUBMISSION_DIR" || exit 2
    [[ -d "$SUBMISSION_DIR" && ! -L "$SUBMISSION_DIR" \
      && "$(sha256sum "$SUBMISSION_DIR/submission-intent.json" | awk '{print $1}')" \
         == "$INTENT_SHA256" ]] || exit 2
    if [[ -e "$SUBMISSION_DIR/qsub-invocation.json" \
        || -L "$SUBMISSION_DIR/qsub-invocation.json" ]]; then
      INVOCATION_SHA256=$(load_qsub_invocation_claim) || exit 4
    else
      INVOCATION_SHA256=""
    fi
  fi
  if [[ "$RESERVATION_STATE" == "resume-bound" ]]; then
    JOB_ID=$(load_qsub_binding)
    [[ "$JOB_ID" == "$RESERVED_JOB" ]] || exit 2
    BINDING_SHA256=$(sha256sum "$SUBMISSION_DIR/qsub-binding.json" | awk '{print $1}')
  elif [[ "$RESERVATION_STATE" == "resume-unbound" ]]; then
    if [[ -f "$SUBMISSION_DIR/qsub-binding.json" \
        && ! -L "$SUBMISSION_DIR/qsub-binding.json" ]]; then
      JOB_ID=$(load_qsub_binding)
      bind_qsub_attempt
      RESERVATION_STATE="resume-bound"
    elif [[ -e "$SUBMISSION_DIR/qsub-invocation.json" \
        || -L "$SUBMISSION_DIR/qsub-invocation.json" ]]; then
      if ! recover_or_reject_unbound_invocation; then
        exit 4
      fi
    else
      # The series intent is durable, but no qsub invocation began.  The
      # create-only claim below remains the sole authority to cross that edge.
      RESERVATION_STATE="reserved"
    fi
  fi
  if [[ "$RESERVATION_STATE" == "resume-bound" ]]; then
    :
  else
  assert_safe_submit_path "$SUBMISSION_DIR" || exit 2
  if [[ -z "${INVOCATION_SHA256:-}" ]]; then
    if ! INVOCATION_SHA256=$(create_qsub_invocation_claim); then
      echo "qsub invocation claim already exists; automatic resubmit is forbidden" >&2
      exit 4
    fi
  fi
  qsub_rc=0
  (
    cd "$REPO_ROOT"
    qsub -v "IZANAGI_SUBMISSION_NONCE=$NONCE" "$JOB_SCRIPT"
  ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr" || qsub_rc=$?
  printf '%s\n' "$qsub_rc" >"$SUBMISSION_DIR/qsub.rc"
  if [[ "$qsub_rc" -ne 0 ]]; then
    exit "$qsub_rc"
  fi
  if [[ "${IZANAGI_T126_TEST_CRASH_AFTER_QSUB:-0}" == 1 ]]; then
    kill -KILL "$$"
  fi
  JOB_ID=$(publish_qsub_binding)
  if [[ "${IZANAGI_T126_TEST_CRASH_AFTER_BINDING:-0}" == 1 ]]; then
    kill -KILL "$$"
  fi
  bind_qsub_attempt
  fi
  assert_safe_submit_path "$SUBMISSION_DIR/qsub-binding.json" || exit 2
  qstat_rc=0
  qstat -f "$JOB_ID" >"$SUBMISSION_DIR/qstat-job.stdout" \
    2>"$SUBMISSION_DIR/qstat-job.stderr" || qstat_rc=$?
  printf '%s\n' "$qstat_rc" >"$SUBMISSION_DIR/qstat-job.rc"
  [[ "$qstat_rc" -eq 0 ]] || {
    echo "submitted job is not visible to exact qstat lookup" >&2
    exit 4
  }
  python3 -I -B - "$SUBMISSION_DIR/qstat-job.stdout" "$JOB_ID" <<'PY' || exit 4
import re,sys
s=open(sys.argv[1],encoding="utf-8",errors="strict").read()
job=sys.argv[2]
values=[]
for pattern in (
    r"(?im)^\s*Request\s+(?:ID|Name)\s*=\s*(\S+)\s*$",
    r"(?im)^\s*Job_Id\s*=\s*(\S+)\s*$",
):
    values += re.findall(pattern,s)
normalized=lambda value: value[2:] if value.startswith("0:") else value
if len(values)!=1 or normalized(values[0])!=normalized(job):
    raise SystemExit("qstat visibility job ID mismatch")
PY
fi

if [[ "${IZANAGI_T126_TEST_FAIL_RECEIPT_WRITE:-0}" == 1 ]]; then
  echo "injected submit receipt write failure after qsub binding" >&2
  exit 4
fi

assert_safe_submit_path "$SUBMISSION_DIR" || exit 2
python3 -I -B - "$SUBMISSION_DIR" "$JOB_ID" "$NONCE" "$SOURCE_COMMIT" \
  "$SOURCE_TREE" "$CCBENCH_GITLINK" "$JOB_SCRIPT_SHA256" "$COLLECTOR_SHA256" \
  "$PROTOCOL_SHA256" "$PROJECT" "$QUEUE" "$NODES" "$WALLTIME_S" \
  "$RETRY_INDEX" "$DRY_RUN" "$RETRY_ATTEMPT_ID" \
  "$RETRY_SERIES_ID" "$RETRY_RECEIPT_SHA256" "$SERIES_ID" "$INTENT_SHA256" \
  "$BINDING_SHA256" "$INVOCATION_SHA256" "$STAGED_ORCHESTRATOR" <<'PY'
import hashlib,json,os,sys
(root, job_id, nonce, commit, tree, gitlink, job_sha, collector_sha,
 protocol_sha, project, queue, nodes, walltime, retry_index, dry_run,
 retry_attempt_id,retry_series_id,retry_receipt_sha256,series_id,
 intent_sha256,qsub_binding_sha256,qsub_invocation_sha256,
 staged_orchestrator) = sys.argv[1:]
captures={}
for name in ("qstat_Q","pegasusinfo","rbudgetcheck","check_quota"):
    captures[name]={
        "rc":int(open(os.path.join(root,name+".rc")).read().strip()),
        "stdout_raw":open(os.path.join(root,name+".stdout"),encoding="utf-8",errors="replace").read(),
        "stderr_raw":open(os.path.join(root,name+".stderr"),encoding="utf-8",errors="replace").read(),
    }
p={
 "schema_version":"t126-qualification-submit-receipt/v1",
 "qualification_lineage":"t126-only",
 "authority":"evidence-only/no-promotion",
 "hold_enforced":False,
 "job_id":job_id,
 "qualification_series_id":series_id,
 "nonce":nonce,
 "source_commit":commit,
 "source_tree":tree,
 "ccbench_gitlink":gitlink,
 "job_script_sha256":job_sha,
 "collector_sha256":collector_sha,
 "protocol_sha256":protocol_sha,
 "request":{"project":project,"queue":queue,"nodes":int(nodes),"elapstim_req_s":int(walltime)},
 "preflight":captures,
 "retry_index":int(retry_index),
 "retry_from_attempt_id":retry_attempt_id or None,
 "retry_from_series_id":retry_series_id or None,
 "retry_receipt_sha256":retry_receipt_sha256 or None,
 "submission_intent_sha256":intent_sha256,
 "qsub_invocation_sha256":qsub_invocation_sha256,
 "qsub_binding_sha256":qsub_binding_sha256,
 "dry_run":bool(int(dry_run)),
 "submitted_epoch":int(json.load(open(
     os.path.join(root,"submission-intent.json"),encoding="utf-8"))[
         "prepared_epoch"]),
}
sys.path.insert(0,staged_orchestrator)
from qualification.contract import attempt_identity
attempt_preimage={
 "schema_version":"t126-qualification-attempt-identity/v1",
 "qualification_series_id":series_id,"pbs_job_id":job_id,"nonce":nonce,
 "retry_index":int(retry_index),"submission_intent_sha256":intent_sha256}
p["qualification_attempt_id"]=attempt_identity(attempt_preimage)
target=os.path.join(root,"submit-receipt.json")
data=(json.dumps(p,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
sys.path.insert(0,staged_orchestrator)
from qualification.atomic_publish import publish_bytes
publish_bytes(
    __import__("pathlib").Path(target),data,
    crash_boundary=os.environ.get("IZANAGI_T126_TEST_RECEIPT_CRASH",""))
print(p["qualification_attempt_id"])
PY
ATTEMPT_ID=$(python3 -I -B - "$SUBMISSION_DIR/submit-receipt.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1],encoding="utf-8"))["qualification_attempt_id"])
PY
)
echo "$SUBMISSION_DIR/submit-receipt.json"
echo "$JOB_ID"
