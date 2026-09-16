#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=10:00:00
#PBS -b 1
set -Eeuo pipefail
umask 077

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" \
  && -n "${IZANAGI_SUBMISSION_NONCE:-}" ]] || exit 2
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ \
  && "$IZANAGI_SUBMISSION_NONCE" =~ ^[0-9a-f]{32}$ ]] || exit 2
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP
PY=""
for candidate in python3 python3.10 python3.11 python3.12; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -S -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,10) else 1)' \
      >/dev/null 2>&1; then
    PY=$(realpath -e -- "$resolved")
    break
  fi
done
[[ -n "$PY" ]] || exit 2
PROLOGUE_STARTED_EPOCH=$(date +%s)
JOB_STARTED_MONOTONIC_NS=$("$PY" -I -S -B -c \
  'import time; print(time.monotonic_ns())')
WMAX_FIXED_S=29100
JOB_DEADLINE_MONOTONIC_NS=$((JOB_STARTED_MONOTONIC_NS + WMAX_FIXED_S * 1000000000))
export IZANAGI_T126_JOB_STARTED_MONOTONIC_NS="$JOB_STARTED_MONOTONIC_NS"
export IZANAGI_T126_JOB_DEADLINE_MONOTONIC_NS="$JOB_DEADLINE_MONOTONIC_NS"
remaining_job_s() {
  "$PY" -I -S -B - "$JOB_DEADLINE_MONOTONIC_NS" <<'PY'
import sys,time
remaining=(int(sys.argv[1])-time.monotonic_ns())//1_000_000_000
if remaining <= 0:
    raise SystemExit(2)
print(remaining)
PY
}
check_job_deadline() {
  remaining_job_s >/dev/null
}
run_with_budget() {
  local cap=$1 remaining
  shift
  remaining=$(remaining_job_s)
  if [[ "$cap" -gt "$remaining" ]]; then
    cap=$remaining
  fi
  [[ "$cap" -gt 0 ]] || return 124
  timeout --signal=TERM --kill-after=10 "$cap" "$@"
}

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
ARTIFACT_REPO_ROOT="$REPO_ROOT"
QUAL_ROOT="$REPO_ROOT/output/env/pegasus/qualification/t126"
SUBMISSION_RECEIPT="$QUAL_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE/submit-receipt.json"
CANONICAL_JOB_ID=${PBS_JOBID#0:}
JOB_STAGING="$QUAL_ROOT/job-staging/$CANONICAL_JOB_ID.$IZANAGI_SUBMISSION_NONCE"

# The submitter publishes the receipt after qsub returns.  Waiting and static
# admission are read-only and therefore precede job-staging creation and traps.
for _ in $(seq 1 600); do
  [[ -f "$SUBMISSION_RECEIPT" && ! -L "$SUBMISSION_RECEIPT" ]] && break
  sleep 0.1
done
if [[ ! -f "$SUBMISSION_RECEIPT" || -L "$SUBMISSION_RECEIPT" ]]; then
  echo '{"gate":"bootstrap","reason":"T126 submission receipt is unavailable"}' >&2
  exit 4
fi
PREFLIGHT_SOURCE_COMMIT=$(
  "$PY" -I -S -B - "$SUBMISSION_RECEIPT" <<'PY'
import json
import re
import sys

def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        document = json.load(handle, object_pairs_hook=no_duplicates)
    source_commit = document["source_commit"]
except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError):
    raise SystemExit(4)
if type(source_commit) is not str or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
    raise SystemExit(4)
print(source_commit)
PY
) || {
  echo '{"gate":"bootstrap","reason":"cannot read a unique source_commit from T126 receipt"}' >&2
  exit 4
}
PREFLIGHT_HELPER_PATH="orchestrator/campaign/certified_writer_preflight.py"
PREFLIGHT_HELPER_SPEC="$PREFLIGHT_SOURCE_COMMIT:$PREFLIGHT_HELPER_PATH"
if ! git -C "$REPO_ROOT" cat-file -e "$PREFLIGHT_HELPER_SPEC" 2>/dev/null; then
  echo '{"gate":"bootstrap","reason":"static admission helper blob is unavailable"}' >&2
  exit 4
fi
preflight_rc=0
git -C "$REPO_ROOT" cat-file blob "$PREFLIGHT_HELPER_SPEC" \
  | "$PY" -I -B - t126 --repo-root "$REPO_ROOT" \
      --receipt "$SUBMISSION_RECEIPT" || preflight_rc=$?
if [[ "$preflight_rc" -ne 0 ]]; then
  exit "$preflight_rc"
fi

safe_namespace() {
  local target=$1 current="$REPO_ROOT" part
  local -a components
  [[ "$target" == "$REPO_ROOT/output/"* ]] || return 1
  IFS='/' read -r -a components <<<"${target#"$REPO_ROOT"/}"
  for part in "${components[@]}"; do
    [[ -n "$part" && "$part" != "." && "$part" != ".." ]] || return 1
    current="$current/$part"
    [[ ! -L "$current" ]] || return 1
  done
  [[ "$(realpath -m -- "$target")" == "$REPO_ROOT/output/"* ]]
}
safe_namespace "$QUAL_ROOT/job-staging" || exit 2
mkdir -p "$QUAL_ROOT/job-staging"
safe_namespace "$QUAL_ROOT/job-staging" || exit 2
mkdir "$JOB_STAGING"
safe_namespace "$JOB_STAGING" || exit 2
if [[ -n "${IZANAGI_T126_TEST_POINTER_SYMLINK_TARGET:-}" ]]; then
  ln -s -- "$IZANAGI_T126_TEST_POINTER_SYMLINK_TARGET" \
    "$JOB_STAGING/attempt-pointer.json"
elif [[ -n "${IZANAGI_T126_TEST_POINTER_SOURCE:-}" ]]; then
  cp -- "$IZANAGI_T126_TEST_POINTER_SOURCE" \
    "$JOB_STAGING/attempt-pointer.json"
fi
set -o noclobber

JOB_RESULT="$JOB_STAGING/job-result.json"
SUBMITTED_ATTEMPT_ID=""
SUBMITTED_SERIES_ID=""
driver_rc=2
terminal_written=0
SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
write_terminal_result() {
  local rc=$1
  local target_rejected=0
  [[ "$terminal_written" -eq 0 ]] || return 0
  terminal_written=1
  check_job_deadline || return 0
  if [[ "$SUBMITTED_ATTEMPT_ID" =~ ^[0-9a-f]{64}$ ]]; then
    local submitted_dir pointer_ok=1
    submitted_dir="$QUAL_ROOT/attempts/$SUBMITTED_ATTEMPT_ID"
    if [[ -e "$JOB_STAGING/attempt-pointer.json" \
        || -L "$JOB_STAGING/attempt-pointer.json" ]]; then
      if [[ -L "$JOB_STAGING/attempt-pointer.json" ]]; then
        pointer_ok=0
      else
        "$PY" -I -S -B - "$JOB_STAGING/attempt-pointer.json" \
        "$SUBMITTED_SERIES_ID" "$SUBMITTED_ATTEMPT_ID" \
        "$CANONICAL_JOB_ID" "$IZANAGI_SUBMISSION_NONCE" <<'PY' \
        || pointer_ok=0
import json,os,sys
path,series,attempt,job,nonce=sys.argv[1:]
fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
try:
    chunks=[]
    while True:
        block=os.read(fd,1024*1024)
        if not block: break
        chunks.append(block)
finally:
    os.close(fd)
raw=b"".join(chunks)
value=json.loads(raw.decode("utf-8",errors="strict"))
expected={
    "schema_version":"t126-qualification-attempt-pointer/v1",
    "qualification_series_id":series,
    "qualification_attempt_id":attempt,
    "pbs_job_id":job,
    "nonce":nonce,
}
canonical=(json.dumps(
    value,sort_keys=True,separators=(",",":"),allow_nan=False
)+"\n").encode("ascii")
if type(value) is not dict or value!=expected or raw!=canonical:
    raise SystemExit(2)
PY
      fi
    fi
    if [[ "$pointer_ok" -eq 1 && -d "$submitted_dir" \
        && ! -L "$submitted_dir" ]] && safe_namespace "$submitted_dir"; then
      JOB_RESULT="$submitted_dir/job-result.json"
    else
      target_rejected=1
    fi
  fi
  local completed_ns
  completed_ns=$("$PY" -I -S -B -c \
    'import time; print(time.monotonic_ns())') || return 0
  "$PY" -I -S -B - "$JOB_RESULT" "$PBS_JOBID" "$rc" \
    "${SCRIPT_SHA:-unknown}" "$IZANAGI_SUBMISSION_NONCE" \
    "$JOB_STARTED_MONOTONIC_NS" "$completed_ns" "$WMAX_FIXED_S" \
    "$target_rejected" "$SUBMITTED_SERIES_ID" \
    "$SUBMITTED_ATTEMPT_ID" <<'PY' || true
import json,os,re,secrets,stat,sys,time
path,job,rc,script,nonce,started,completed,wmax,rejected,series,attempt=sys.argv[1:]
rc=int(rc); started=int(started); completed=int(completed); wmax=int(wmax)
table={30:"member-rejected",31:"pre-attestation",32:"reservation-unavailable",
       33:"pre-member-infrastructure",34:"pre-member-infrastructure",
       124:"pre-member-infrastructure",129:"scheduler-terminated",
       137:"scheduler-hard-kill",
       143:"scheduler-terminated"}
failure="none" if rc in (0,20,21) else table.get(rc,"unregistered-scheduler-failure")
p={"schema_version":"t126-qualification-job-result/v1","pbs_jobid":job,
   "driver_rc":rc,"job_script_sha256":script,"nonce":nonce,
   "failure_class":failure,"completed_epoch":int(time.time()),
   "job_started_monotonic_ns":started,"completed_monotonic_ns":completed,
   "elapsed_ns":completed-started,"wmax_s":wmax}
data=(json.dumps(p,sort_keys=True,separators=(",",":"))+"\n").encode()
parent=os.path.dirname(path)
name=os.path.basename(path)
prefix="."+name+".create-"
pattern=re.compile(re.escape(prefix)+r"[1-9][0-9]*-[0-9a-f]{16}")
def fsync_dir():
    fd=os.open(parent,os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
    try: os.fsync(fd)
    finally: os.close(fd)
entries=[entry for entry in os.scandir(parent)
         if entry.name.startswith(prefix)]
if len(entries)>1 or any(pattern.fullmatch(entry.name) is None
                         for entry in entries):
    raise RuntimeError("ambiguous abandoned publisher staging")
stage=entries[0] if entries else None
target_exists=os.path.lexists(path)
target_stat=os.lstat(path) if target_exists else None
stage_stat=os.lstat(stage.path) if stage is not None else None
for current,expected_nlink in (
        (target_stat,2 if stage is not None else 1),
        (stage_stat,2 if target_exists else 1)):
    if current is None:
        continue
    if (stat.S_ISLNK(current.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or current.st_uid!=os.getuid()
            or stat.S_IMODE(current.st_mode)!=0o600
            or current.st_nlink!=expected_nlink):
        raise RuntimeError("publisher staging owner/mode/nlink mismatch")
if stage is not None and target_exists:
    if ((stage_stat.st_dev,stage_stat.st_ino)
            !=(target_stat.st_dev,target_stat.st_ino)
            or open(stage.path,"rb").read()!=open(path,"rb").read()):
        raise RuntimeError("publisher staging target inode/bytes mismatch")
if target_exists and open(path,"rb").read()!=data:
    raise RuntimeError("existing canonical result differs")
if rejected=="1":
    marker=os.path.join(parent,"target-rejection.json")
    marker_value={
        "schema_version":"t126-job-result-target-rejection/v1",
        "qualification_series_id":series,
        "qualification_attempt_id":attempt,
        "pbs_job_id":job,
        "nonce":nonce,
        "reason":"submitted-attempt-target-invalid",
    }
    marker_data=(json.dumps(
        marker_value,sort_keys=True,separators=(",",":"),
        allow_nan=False)+"\n").encode("ascii")
    marker_flags=(os.O_WRONLY|os.O_CREAT|os.O_EXCL
                  |getattr(os,"O_NOFOLLOW",0))
    try:
        marker_fd=os.open(marker,marker_flags,0o600)
    except FileExistsError:
        marker_fd=os.open(
            marker,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
        try:
            marker_chunks=[]
            while True:
                marker_block=os.read(marker_fd,1024*1024)
                if not marker_block: break
                marker_chunks.append(marker_block)
        finally:
            os.close(marker_fd)
        marker_actual=b"".join(marker_chunks)
        if marker_actual!=marker_data:
            raise RuntimeError("target rejection marker differs")
    else:
        try:
            marker_offset=0
            while marker_offset<len(marker_data):
                marker_written=os.write(
                    marker_fd,marker_data[marker_offset:])
                if marker_written<=0:
                    raise RuntimeError(
                        "target rejection marker write made no progress")
                marker_offset+=marker_written
            os.fsync(marker_fd)
        finally:
            os.close(marker_fd)
        fsync_dir()
if stage is not None:
    if target_exists:
        fsync_dir()
    os.unlink(stage.path)
    fsync_dir()
if target_exists:
    raise SystemExit(0)
fsync_dir()
staging=os.path.join(
    parent,prefix+str(os.getpid())+"-"+secrets.token_hex(8))
flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)
fd=os.open(staging,flags,0o600)
boundary=os.environ.get("IZANAGI_T126_TEST_JOB_RESULT_CRASH","")
if boundary=="after-open": os._exit(91)
try:
    offset=0
    while offset<len(data):
        limit=1 if boundary=="after-short-write" and offset==0 else len(data)-offset
        written=os.write(fd,data[offset:offset+limit])
        if written<=0: raise RuntimeError("publisher write made no progress")
        offset+=written
        if boundary=="after-short-write" and offset==1: os._exit(92)
    os.fsync(fd)
    if boundary=="after-fsync": os._exit(93)
finally:
    os.close(fd)
try:
    os.link(staging,path,follow_symlinks=False)
except FileExistsError:
    flags=os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)
    existing=os.open(path,flags)
    try:
        chunks=[]
        while True:
            block=os.read(existing,1024*1024)
            if not block: break
            chunks.append(block)
    finally:
        os.close(existing)
    if b"".join(chunks)!=data:
        raise RuntimeError("existing canonical result differs")
if boundary=="after-publish": os._exit(94)
fsync_dir()
os.unlink(staging)
fsync_dir()
PY
}
on_signal() {
  local sig=$1
  driver_rc=$((128 + sig))
  write_terminal_result "$driver_rc"
  exit "$driver_rc"
}
trap 'on_signal 15' TERM
trap 'on_signal 1' HUP
trap 'driver_rc=$?' ERR
trap 'rc=$?; if [[ "$terminal_written" -eq 0 ]]; then write_terminal_result "$rc"; fi' EXIT

for _ in $(seq 1 600); do
  [[ -f "$SUBMISSION_RECEIPT" && ! -L "$SUBMISSION_RECEIPT" ]] && break
  sleep 0.1
done
check_job_deadline
[[ -f "$SUBMISSION_RECEIPT" && ! -L "$SUBMISSION_RECEIPT" ]] || exit 2
safe_namespace "$SUBMISSION_RECEIPT" || exit 2
"$PY" -I -S -B - "$SUBMISSION_RECEIPT" "$QUAL_ROOT/series" <<'PY'
import hashlib,json,os,re,sys
receipt_path,series_root=sys.argv[1:]
def no_dups(pairs):
    value={}
    for key,item in pairs:
        if key in value: raise SystemExit("duplicate JSON key")
        value[key]=item
    return value
def load(path):
    with open(path,"rb") as stream: raw=stream.read()
    text=raw.decode("utf-8",errors="strict")
    value=json.loads(text,object_pairs_hook=no_dups)
    canonical=(json.dumps(
        value,sort_keys=True,separators=(",",":"),allow_nan=False
    )+"\n").encode("ascii")
    if canonical!=raw or type(value) is not dict:
        raise SystemExit("non-canonical JSON")
    return value,raw
receipt,_=load(receipt_path)
series=receipt.get("qualification_series_id","")
nonce=receipt.get("nonce","")
attempt=receipt.get("qualification_attempt_id","")
job=receipt.get("job_id","")
index=receipt.get("retry_index")
intent=receipt.get("submission_intent_sha256","")
invocation_hash=receipt.get("qsub_invocation_sha256","")
if (re.fullmatch(r"[0-9a-f]{64}",series) is None
        or re.fullmatch(r"[0-9a-f]{32}",nonce) is None
        or re.fullmatch(r"[0-9a-f]{64}",intent) is None
        or re.fullmatch(r"[0-9a-f]{64}",invocation_hash) is None
        or type(index) is not int or index not in (0,1)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",job) is None):
    raise SystemExit(2)
directory=os.path.join(series_root,series,"attempt-ledger")
names=sorted(os.listdir(directory))
if names != [f"{i:04d}.json" for i in range(len(names))]: raise SystemExit(2)
previous="0"*64
events=[]
for i,name in enumerate(names):
    value,raw=load(os.path.join(directory,name))
    unhashed={k:v for k,v in value.items() if k!="event_sha256"}
    actual=hashlib.sha256(json.dumps(
        unhashed,sort_keys=True,separators=(",",":"),allow_nan=False
    ).encode()).hexdigest()
    if value.get("event_index")!=i or value.get("previous_event_sha256")!=previous \
            or value.get("event_sha256")!=actual:
        raise SystemExit(2)
    previous=actual; events.append(value)
last=events[-1]
payload=last.get("payload",{})
expected="initial_submitted" if index==0 else "retry_submitted"
prior=events[-2] if len(events)>=2 else {}
prior_payload=prior.get("payload",{})
prior_expected="initial_intent" if index==0 else "retry_intent"
binding_path=os.path.join(os.path.dirname(receipt_path),"qsub-binding.json")
binding,binding_raw=load(binding_path)
invocation_path=os.path.join(
    os.path.dirname(receipt_path),"qsub-invocation.json")
invocation,invocation_raw=load(invocation_path)
binding_keys={"schema_version","job_id","nonce","submission_intent_sha256",
              "qsub_invocation_sha256","retry_index","qsub_returncode",
              "qsub_stdout_raw"}
invocation_expected={"nonce":nonce,"retry_index":index,
                     "submission_intent_sha256":intent}
if type(binding.get("qsub_stdout_raw")) is not str:
    raise SystemExit("qsub stdout type mismatch")
stdout_match=re.fullmatch(
    r"(?:Request (?P<request>[A-Za-z0-9][A-Za-z0-9._-]*) submitted\."
    r"|(?P<plain>[A-Za-z0-9][A-Za-z0-9._-]*))\n",
    binding["qsub_stdout_raw"])
derived=(stdout_match.group("request") or stdout_match.group("plain")
         if stdout_match else None)
if last.get("event_type")!=expected \
        or prior.get("event_type")!=prior_expected \
        or prior_payload.get("nonce")!=nonce \
        or type(prior_payload.get("retry_index")) is not int \
        or prior_payload.get("retry_index")!=index \
        or prior_payload.get("submission_intent_sha256")!=intent \
        or payload.get("qualification_attempt_id")!=attempt \
        or type(payload.get("retry_index")) is not int \
        or payload.get("retry_index")!=index \
        or payload.get("job_id")!=job or payload.get("nonce")!=nonce \
        or payload.get("qsub_invocation_sha256")!=invocation_hash \
        or receipt.get("qsub_binding_sha256")!=hashlib.sha256(binding_raw).hexdigest() \
        or payload.get("submission_evidence_sha256")!=hashlib.sha256(binding_raw).hexdigest() \
        or set(binding)!=binding_keys \
        or binding["schema_version"]!="t126-qsub-binding/v2" \
        or binding["job_id"]!=job or binding["nonce"]!=nonce \
        or binding["submission_intent_sha256"]!=intent \
        or binding["qsub_invocation_sha256"]!=invocation_hash \
        or hashlib.sha256(invocation_raw).hexdigest()!=invocation_hash \
        or type(invocation.get("retry_index")) is not int \
        or invocation!=invocation_expected \
        or binding["retry_index"]!=index or type(binding["retry_index"]) is not int \
        or binding["qsub_returncode"]!=0 \
        or type(binding["qsub_returncode"]) is not int \
        or derived!=job:
    print("durable qsub/ledger binding mismatch",file=sys.stderr)
    raise SystemExit(2)
PY
readarray -t EARLY_ID < <("$PY" -I -S -B - "$SUBMISSION_RECEIPT" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
for key in ("source_commit","source_tree","ccbench_gitlink",
            "qualification_attempt_id","qualification_series_id"):
    print(d[key])
PY
)
[[ ${#EARLY_ID[@]} -eq 5 && "${EARLY_ID[0]}" =~ ^[0-9a-f]{40}$ \
  && "${EARLY_ID[1]}" =~ ^[0-9a-f]{40}$ && "${EARLY_ID[2]}" =~ ^[0-9a-f]{40}$ \
  && "${EARLY_ID[3]}" =~ ^[0-9a-f]{64}$ \
  && "${EARLY_ID[4]}" =~ ^[0-9a-f]{64}$ ]] || exit 2
SOURCE_COMMIT=${EARLY_ID[0]}
SUBMITTED_ATTEMPT_ID=${EARLY_ID[3]}
SUBMITTED_SERIES_ID=${EARLY_ID[4]}
if [[ "${IZANAGI_T126_TEST_SIGNAL_AFTER_BINDING:-}" == "TERM" ]]; then
  kill -TERM "$$"
elif [[ -n "${IZANAGI_T126_TEST_EXIT_AFTER_BINDING:-}" ]]; then
  exit "$IZANAGI_T126_TEST_EXIT_AFTER_BINDING"
fi

SCR_ROOT="/scr/${PBS_JOBID//:/_}-t126"
mkdir "$SCR_ROOT"
SOURCE_STAGE="$SCR_ROOT/source"
mkdir "$SOURCE_STAGE"
STAGE_REMAINING=$(remaining_job_s)
timeout "$STAGE_REMAINING" git -C "$REPO_ROOT" archive --format=tar "$SOURCE_COMMIT" \
  | timeout "$STAGE_REMAINING" tar -xf - -C "$SOURCE_STAGE"
[[ "$(git -C "$REPO_ROOT" rev-parse "$SOURCE_COMMIT^{tree}")" == "${EARLY_ID[1]}" ]] \
  || exit 2
TOOLS="$SOURCE_STAGE/tools/pegasus"
POLICY="$TOOLS/policy.json"
# T-126-owned PBS reservation policy; the shared policy keeps only the
# shared values (dependency roots, perf candidates, project/queue/nodes).
RESERVATION_POLICY="$SOURCE_STAGE/orchestrator/qualification/t126_reservation_policy_v1.json"
REPO_SOURCE="$SOURCE_STAGE"

if ! RESERVATION_OUTPUT=$("$PY" -I -S -B - "$RESERVATION_POLICY" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding="utf-8"))
expected={
    "t126_qualification_walltime":"10:00:00",
    "t126_qualification_walltime_s":36000,
    "t126_qualification_member_cap_s":900,
    "t126_qualification_round_gap_s":1800,
    "t126_qualification_prologue_cap_s":900,
    "t126_qualification_attestation_cap_s":600,
    "t126_qualification_finalize_reserve_s":600,
    "t126_qualification_wmax_s":29100,
}
numeric_keys=(
    "t126_qualification_walltime_s",
    "t126_qualification_member_cap_s",
    "t126_qualification_round_gap_s",
    "t126_qualification_prologue_cap_s",
    "t126_qualification_attestation_cap_s",
    "t126_qualification_finalize_reserve_s",
    "t126_qualification_wmax_s",
)
if type(p.get("t126_qualification_walltime")) is not str:
    raise SystemExit("qualification envelope type mismatch")
for key in numeric_keys:
    if type(p.get(key)) is not int:
        raise SystemExit("qualification envelope type mismatch")
if any(p.get(key) != value for key,value in expected.items()):
    raise SystemExit("qualification envelope mismatch")
for key in ("t126_qualification_walltime_s","t126_qualification_wmax_s",
            "t126_qualification_prologue_cap_s"):
    print(p[key])
PY
); then
  exit 2
fi
readarray -t RESERVATION_VALUES <<<"$RESERVATION_OUTPUT"
unset RESERVATION_OUTPUT
[[ ${#RESERVATION_VALUES[@]} -eq 3 ]] || exit 2
WALLTIME_S=${RESERVATION_VALUES[0]}
WMAX_S=${RESERVATION_VALUES[1]}
PROLOGUE_CAP_S=${RESERVATION_VALUES[2]}
[[ "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 \
  && "$PROLOGUE_CAP_S" == 900 ]] || exit 2

readarray -t P < <("$PY" -I -S -B - "$POLICY" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding="utf-8"))
keys=("gflags_expected_head",
      "glog_expected_head")
for k in keys: print(p[k])
PY
)
[[ ${#P[@]} -eq 2 ]] || exit 2
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_HEAD=${P[0]}
GLOG_HEAD=${P[1]}

check_job_deadline
for source_pin in "$GFLAGS_SOURCE:$GFLAGS_HEAD" "$GLOG_SOURCE:$GLOG_HEAD"; do
  source=${source_pin%%:*}
  pin=${source_pin#*:}
  [[ -d "$source" && "$(git -C "$source" rev-parse HEAD)" == "$pin" \
    && -z "$(git -C "$source" status --porcelain --untracked-files=all)" ]] || {
    echo "dependency source is not pinned-clean: $source" >&2
    exit 2
  }
done
check_job_deadline

CCBENCH_STAGE="$SCR_ROOT/ccbench"
mkdir "$CCBENCH_STAGE"
STAGE_REMAINING=$(remaining_job_s)
timeout "$STAGE_REMAINING" git -C "$REPO_ROOT/external/ccbench" \
  archive --format=tar "${EARLY_ID[2]}" \
  | timeout "$STAGE_REMAINING" tar -xf - -C "$CCBENCH_STAGE"
[[ -f "$CCBENCH_STAGE/CMakeLists.txt" ]] || exit 2

CC_REAL=$(command -v -- gcc-13)
CXX_REAL=$(command -v -- g++-13)
CMAKE_REAL=$(command -v -- cmake)
CC_REAL=$(realpath -e -- "$CC_REAL")
CXX_REAL=$(realpath -e -- "$CXX_REAL")
CMAKE_REAL=$(realpath -e -- "$CMAKE_REAL")

GFLAGS_STAGE="$SCR_ROOT/dependencies/gflags"
GLOG_STAGE="$SCR_ROOT/dependencies/glog"
mkdir -p "$GFLAGS_STAGE" "$GLOG_STAGE"
STAGE_REMAINING=$(remaining_job_s)
timeout "$STAGE_REMAINING" git -C "$GFLAGS_SOURCE" archive --format=tar "$GFLAGS_HEAD" \
  | timeout "$STAGE_REMAINING" tar -xf - -C "$GFLAGS_STAGE"
STAGE_REMAINING=$(remaining_job_s)
timeout "$STAGE_REMAINING" git -C "$GLOG_SOURCE" archive --format=tar "$GLOG_HEAD" \
  | timeout "$STAGE_REMAINING" tar -xf - -C "$GLOG_STAGE"
GFLAGS_SOURCE="$GFLAGS_STAGE"
GLOG_SOURCE="$GLOG_STAGE"
chmod -R a-w "$SOURCE_STAGE" "$CCBENCH_STAGE" "$GFLAGS_STAGE" "$GLOG_STAGE"
if find "$SOURCE_STAGE" "$CCBENCH_STAGE" "$GFLAGS_STAGE" "$GLOG_STAGE" \
    -type l -print -quit | grep -q .; then
  echo "committed source staging contains a symlink" >&2
  exit 2
fi
check_job_deadline

GFLAGS_BUILD="$SCR_ROOT/gflags-build"
GFLAGS_INSTALL="$SCR_ROOT/gflags-install"
GLOG_BUILD="$SCR_ROOT/glog-build"
GLOG_INSTALL="$SCR_ROOT/glog-install"
run_with_budget 120 "$CMAKE_REAL" -S "$GFLAGS_SOURCE" -B "$GFLAGS_BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  "-DCMAKE_C_COMPILER=$CC_REAL" "-DCMAKE_CXX_COMPILER=$CXX_REAL" \
  -DREGISTER_INSTALL_PREFIX=OFF "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL"
run_with_budget 120 "$CMAKE_REAL" --build "$GFLAGS_BUILD" -j 48
run_with_budget 120 "$CMAKE_REAL" --install "$GFLAGS_BUILD"
run_with_budget 180 "$CMAKE_REAL" -S "$GLOG_SOURCE" -B "$GLOG_BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  "-DCMAKE_C_COMPILER=$CC_REAL" "-DCMAKE_CXX_COMPILER=$CXX_REAL" \
  -DWITH_GTEST=OFF -DBUILD_TESTING=OFF -DWITH_UNWIND=OFF \
  "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL" "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL"
run_with_budget 180 "$CMAKE_REAL" --build "$GLOG_BUILD" -j 48
run_with_budget 120 "$CMAKE_REAL" --install "$GLOG_BUILD"
export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL:$GLOG_INSTALL"

PERF_REAL=""
while IFS= read -r candidate; do
  [[ -x "$candidate" ]] || continue
  if run_with_budget 10 "$candidate" stat -x, \
      -e LLC-load-misses,LLC-loads,instructions,cycles \
      -- true >"$JOB_STAGING/perf-smoke.stdout" \
      2>"$JOB_STAGING/perf-smoke.stderr"; then
    if ! grep -Eqi '<not supported>|<not counted>' \
        "$JOB_STAGING/perf-smoke.stdout" "$JOB_STAGING/perf-smoke.stderr"; then
      PERF_REAL=$candidate
      break
    fi
  fi
done < <("$PY" -I -S -B - "$POLICY" <<'PY'
import json,sys
for p in json.load(open(sys.argv[1]))["perf_candidates"]: print(p)
PY
)
check_job_deadline
if [[ -n "$PERF_REAL" ]]; then
  PERF_BIN="$SCR_ROOT/perf-bin"
  mkdir "$PERF_BIN"
  ln -s "$PERF_REAL" "$PERF_BIN/perf"
  export PATH="$PERF_BIN:$PATH"
fi
PERF_PREFLIGHT_RECEIPT="$JOB_STAGING/perf-preflight.json"
USE_PERF=$("$PY" -I -S -B - "$SOURCE_STAGE" "$POLICY" \
  "$PERF_PREFLIGHT_RECEIPT" <<'PY'
import json,sys
sys.path.insert(0,sys.argv[1])
from orchestrator.calibrator import perf_preflight
policy=json.load(open(sys.argv[2],encoding="utf-8"))
receipt=perf_preflight.probe_perf_availability(
    perf_candidates=policy["perf_candidates"])
use_perf=perf_preflight.use_perf_from_receipt(receipt)
with open(sys.argv[3],"x",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,separators=(",",":")); f.write("\n")
print("1" if use_perf else "0")
PY
) || exit 2
[[ "$USE_PERF" == 0 || "$USE_PERF" == 1 ]] || exit 2

readarray -t SUBMIT_ID < <("$PY" -I -S -B - "$SUBMISSION_RECEIPT" <<'PY'
import json,sys
def no_dups(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise SystemExit(2)
        out[key]=value
    return out
d=json.load(open(sys.argv[1],encoding="utf-8"),object_pairs_hook=no_dups)
for key in ("nonce","source_commit","source_tree","ccbench_gitlink",
            "job_script_sha256","collector_sha256","protocol_sha256"):
    value=d.get(key)
    if not isinstance(value,str): raise SystemExit(2)
    print(value)
PY
)
[[ ${#SUBMIT_ID[@]} -eq 7 && "${SUBMIT_ID[0]}" == "$IZANAGI_SUBMISSION_NONCE" \
  && "$SOURCE_COMMIT" == "${SUBMIT_ID[1]}" \
  && "$(git -C "$REPO_ROOT" rev-parse --verify "$SOURCE_COMMIT^{tree}")" == "${SUBMIT_ID[2]}" \
  && "$(git -C "$REPO_ROOT" rev-parse --verify "$SOURCE_COMMIT:external/ccbench")" == "${SUBMIT_ID[3]}" \
  && "$(sha256sum "$0" | awk '{print $1}')" == "${SUBMIT_ID[4]}" \
  && "$(sha256sum "$SOURCE_STAGE/tools/pegasus/collect_t126_qualification.py" | awk '{print $1}')" == "${SUBMIT_ID[5]}" \
  && "$(sha256sum "$SOURCE_STAGE/orchestrator/qualification/t126_control_v1.json" \
       | awk '{print $1}')" == "${SUBMIT_ID[6]}" ]] || exit 2

QSTAT_JOBID=${PBS_JOBID#0:}
run_with_budget 30 qstat -f "$QSTAT_JOBID" >"$JOB_STAGING/qstat-f.stdout" \
  2>"$JOB_STAGING/qstat-f.stderr"
readarray -t SCHED < <("$PY" -I -S -B - "$JOB_STAGING/qstat-f.stdout" <<'PY'
import re,subprocess,sys,time
s=open(sys.argv[1],encoding="utf-8",errors="replace").read()
limits=re.findall(r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S",s)
remaining=re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S",s)
started=None
for key in ("Started Request Time","stime","start_time"):
    m=re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$",s)
    if m:
        raw=m.group(1).strip()
        if raw.isdigit(): started=int(raw)
        else:
            p=subprocess.run(["date","-d",raw,"+%s"],capture_output=True,text=True)
            if p.returncode==0 and p.stdout.strip().isdigit(): started=int(p.stdout)
        break
if len(limits)!=1 or len(remaining)!=1 or started is None: raise SystemExit(2)
print(started); print(limits[0]); print(remaining[0])
PY
)
[[ ${#SCHED[@]} -eq 3 && "${SCHED[1]}" -ge "$WALLTIME_S" \
  && "${SCHED[2]}" -ge "$WMAX_S" ]] || exit 2
BOOT_ID=$(< /proc/sys/kernel/random/boot_id)
HOST=$(hostname)
SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="${SCHED[1]}"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="${SCHED[0]}"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$((SCHED[0] + SCHED[1]))"
export IZANAGI_RESERVATION_HOST="$HOST"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"

check_job_deadline
safe_namespace "$JOB_STAGING" || exit 2
cp --no-clobber "$QUAL_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE/toolchain-manifest.json" \
  "$JOB_STAGING/toolchain-manifest.json"
"$PY" -I -S -B - "$JOB_STAGING/toolchain-manifest.json" "$PY" "$PERF_REAL" \
  "$CC_REAL" "$CXX_REAL" "$CMAKE_REAL" "$GFLAGS_HEAD" "$GLOG_HEAD" \
  "$PERF_PREFLIGHT_RECEIPT" "$SOURCE_STAGE" <<'PY'
import hashlib,json,os,sys
path,python,perf,cc,cxx,cmake,gflags,glog,compute_receipt,source=sys.argv[1:]
sys.path.insert(0,source)
from orchestrator.calibrator import perf_preflight
d=json.load(open(path,encoding="utf-8"))
compute=json.load(open(compute_receipt,encoding="utf-8"))
compute_use_perf=perf_preflight.use_perf_from_receipt(compute)
submission_receipt=d.get("perf_preflight")
submission_use_perf=perf_preflight.use_perf_from_receipt(submission_receipt)
if submission_receipt is not None and submission_use_perf:
    raise SystemExit("available submission receipt is forbidden")
expected_keys={"schema_version","executables","dependencies","build_argv"}
if not submission_use_perf: expected_keys.add("perf_preflight")
expected_executables={"python","cc","cxx","cmake"}
if submission_use_perf: expected_executables.add("perf")
if set(d)!=expected_keys or set(d.get("executables",{}))!=expected_executables \
        or d["schema_version"]!="t126-toolchain-manifest/v1":
    raise SystemExit("toolchain manifest shape mismatch")
if compute_use_perf and "perf" not in d["executables"]:
    raise SystemExit("compute perf requires submission perf identity")
actual={"python":python,"cc":cc,"cxx":cxx,"cmake":cmake}
if compute_use_perf: actual["perf"]=perf
for name,path_value in actual.items():
    row=d["executables"][name]
    if os.path.realpath(path_value)!=row["path"]:
        raise SystemExit("tool path mismatch: "+name)
    h=hashlib.sha256()
    with open(path_value,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    if h.hexdigest()!=row["sha256"]:
        raise SystemExit("tool hash mismatch: "+name)
if d["dependencies"]["gflags"]["commit"]!=gflags \
        or d["dependencies"]["glog"]["commit"]!=glog:
    raise SystemExit("dependency manifest mismatch")
PY
"$PY" -I -S -B - "$JOB_STAGING/source-stage-evidence.json" "$SOURCE_COMMIT" \
  "${EARLY_ID[1]}" "${EARLY_ID[2]}" "$SOURCE_STAGE" \
  "$JOB_STAGING/toolchain-manifest.json" "$JOB_STAGING/perf-smoke.stdout" \
  "$JOB_STAGING/perf-smoke.stderr" "$PERF_PREFLIGHT_RECEIPT" "$USE_PERF" <<'PY'
import hashlib,json,os,sys
(target,commit,tree,gitlink,source,toolchain,perf_out,perf_err,
 receipt_path,use_perf_raw)=sys.argv[1:]
sys.path.insert(0,source)
from orchestrator.calibrator import perf_preflight
def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
p={"schema_version":"t126-source-stage-evidence/v1",
   "source_commit":commit,"source_tree":tree,"ccbench_gitlink":gitlink,
   "tracked_only":True,"immutable_mode":True,
   "protocol_sha256":digest(os.path.join(
       source,"orchestrator/qualification/t126_control_v1.json")),
   "policy_sha256":digest(os.path.join(source,"tools/pegasus/policy.json")),
   "reservation_policy_sha256":digest(os.path.join(
       source,"orchestrator/qualification/t126_reservation_policy_v1.json")),
   "driver_sha256":digest(os.path.join(
       source,"orchestrator/qualification/t126_driver.py")),
   "job_script_sha256":digest(os.path.join(
       source,"tools/pegasus/t126_qualification.sh")),
   "toolchain_manifest_sha256":digest(toolchain)}
receipt=json.load(open(receipt_path,encoding="utf-8"))
use_perf=perf_preflight.use_perf_from_receipt(receipt)
if use_perf != (use_perf_raw=="1"): raise SystemExit(2)
if use_perf:
    p.update({
        "perf_smoke_returncode":0,
        "perf_smoke_stdout":open(
            perf_out,encoding="utf-8",errors="strict").read(),
        "perf_smoke_stderr":open(
            perf_err,encoding="utf-8",errors="strict").read(),
    })
else:
    p["perf_observation"]=perf_preflight.build_perf_observation(
        receipt,run_cmd=["true"],
        leading_indicators={"ipc":None,"llc_miss_rate":None})
with open(target,"x",encoding="utf-8") as f:
    json.dump(p,f,sort_keys=True,separators=(",",":")); f.write("\n")
PY
check_job_deadline

PROLOGUE_ELAPSED_S=$(($(date +%s) - PROLOGUE_STARTED_EPOCH))
[[ "$PROLOGUE_ELAPSED_S" -le "$PROLOGUE_CAP_S" ]] || {
  echo "qualification prologue exceeded fixed cap" >&2
  exit 2
}
check_job_deadline
driver_rc=0
CURRENT_MONOTONIC_NS=$("$PY" -I -S -B -c 'import time; print(time.monotonic_ns())')
REMAINING_S=$(( (JOB_DEADLINE_MONOTONIC_NS - CURRENT_MONOTONIC_NS) / 1000000000 ))
DRIVER_LIMIT_S=$((REMAINING_S - 600))
[[ "$DRIVER_LIMIT_S" -gt 0 ]] || exit 2
timeout --signal=TERM --kill-after=10 "$DRIVER_LIMIT_S" \
  "$PY" -I -B "$SOURCE_STAGE/orchestrator/qualification/t126_driver.py" run \
  --repo-root "$SOURCE_STAGE" \
  --artifact-repo-root "$ARTIFACT_REPO_ROOT" \
  --git-repo-root "$ARTIFACT_REPO_ROOT" \
  --toolchain-manifest "$JOB_STAGING/toolchain-manifest.json" \
  --prologue-evidence "$JOB_STAGING/source-stage-evidence.json" \
  --ccbench-dir "$CCBENCH_STAGE" \
  --cache-root "$SCR_ROOT/build-cache" \
  >"$JOB_STAGING/driver.stdout" 2>"$JOB_STAGING/driver.stderr" || driver_rc=$?
SERIES_RESULT=$(tail -n 1 "$JOB_STAGING/driver.stdout" || true)
# Driver stdout is diagnostic only.  The exact submitted attempt ID is the
# sole target authority after the durable submit/binding/ledger validation.
ATTEMPT_DIR="$QUAL_ROOT/attempts/$SUBMITTED_ATTEMPT_ID"
if [[ -d "$ATTEMPT_DIR" && ! -L "$ATTEMPT_DIR" ]] \
    && safe_namespace "$ATTEMPT_DIR"; then
  JOB_RESULT="$ATTEMPT_DIR/job-result.json"
else
  JOB_RESULT="$JOB_STAGING/job-result.json"
fi
if ! check_job_deadline; then
  driver_rc=124
fi
write_terminal_result "$driver_rc"
exit "$driver_rc"
