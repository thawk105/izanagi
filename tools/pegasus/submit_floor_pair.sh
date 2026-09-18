#!/bin/bash
set -Eeuo pipefail
umask 077

fail() {
  printf '{"gate":"%s","reason":"%s"}\n' "$2" "$3" >&2
  exit "$1"
}

select_python() {
  local candidate resolved
  PY=
  for candidate in python3.10 python3.11 python3.12 python3; do
    resolved=$(command -v -- "$candidate" 2>/dev/null) || continue
    resolved=$(realpath -e -- "$resolved" 2>/dev/null) || continue
    [[ -x "$resolved" ]] || continue
    if "$resolved" -I -B -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
      PY=$resolved
      return 0
    fi
  done
  fail 2 interpreter python_unavailable
}

clean_environment() {
  export PATH=/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin
  unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH || fail 2 environment cleanup_failed
  local name
  for name in ${!GIT_@}; do
    unset "$name" || fail 2 environment cleanup_failed
  done
}

walltime_seconds() {
  local value=$1
  [[ "$value" =~ ^[0-9]{2}:[0-5][0-9]:[0-5][0-9]$ ]] || fail 2 bootstrap invalid_walltime
  DURATION=$((10#${value:0:2} * 3600 + 10#${value:3:2} * 60 + 10#${value:6:2}))
  (( DURATION > 0 )) || fail 2 bootstrap invalid_walltime
}

window_gate() {
  local now=$1 not_before=$2 not_after=$3 duration=$4
  (( now >= not_before )) || fail 4 window before_window
  (( now + duration <= not_after )) || fail 4 window insufficient_remaining_time
}

read_window_bounds() {
  local bounds
  bounds=$("$PY" -I -B -c '
import datetime, json, sys
spec = json.load(open(sys.argv[1]))
window, = [w for w in spec["windows"] if w["window_id"] == sys.argv[2]]
print(*(int(datetime.datetime.fromisoformat(window[k].replace("Z", "+00:00")).timestamp()) for k in ("not_before", "not_after")))
' "$1" "$2" 2>/dev/null) || fail 4 window invalid_window
  read -r NOT_BEFORE NOT_AFTER <<<"$bounds"
  [[ "$NOT_BEFORE" =~ ^[0-9]+$ && "$NOT_AFTER" =~ ^[0-9]+$ ]] || fail 4 window invalid_window
}

check_binaries() {
  "$PY" -I -B -c '
import hashlib, json, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
for artifact in json.load(open(root / sys.argv[2]))["artifacts"]:
    binary = root / artifact["binary_relpath"]
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise SystemExit(1)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != artifact["binary_sha256"]:
        raise SystemExit(1)
' "$1" "$2" 2>/dev/null || fail 4 binary missing_or_mismatch
}

parse_args() {
  WORKLOAD= MODE= WINDOW= DRY_RUN=0
  while (( $# )); do
    case "$1" in
      --workload)
        [[ -z "$WORKLOAD" && $# -ge 2 ]] || fail 2 arguments invalid_arguments
        WORKLOAD=$2; shift 2 ;;
      --window)
        [[ -z "$MODE" && $# -ge 2 ]] || fail 2 arguments invalid_arguments
        MODE=window WINDOW=$2; shift 2 ;;
      --finalize)
        [[ -z "$MODE" ]] || fail 2 arguments invalid_arguments
        MODE=finalize WINDOW=fin; shift ;;
      --dry-run)
        (( DRY_RUN == 0 )) || fail 2 arguments invalid_arguments
        DRY_RUN=1; shift ;;
      -h|--help)
        printf '%s\n' 'Usage: submit_floor_pair.sh --workload {rr95,rr50,rr5} (--window {w1,w2}|--finalize) [--dry-run]'
        exit 0 ;;
      *) fail 2 arguments invalid_arguments ;;
    esac
  done
  case "$WORKLOAD" in rr95|rr50|rr5) ;; *) fail 2 arguments invalid_workload ;; esac
  case "$MODE:$WINDOW" in window:w1|window:w2|finalize:fin) ;; *) fail 2 arguments invalid_mode ;; esac
}

select_pin() {
  case "$WORKLOAD" in
    rr95)
      SPEC_RELPATH=output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json
      SPEC_SHA256=990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619 ;;
    rr50)
      SPEC_RELPATH=output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json
      SPEC_SHA256=b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37 ;;
    rr5)
      SPEC_RELPATH=output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json
      SPEC_SHA256=d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4 ;;
  esac
}

select_walltime() {
  case "$MODE" in
    window) ELAPSTIM_REQ=24:00:00 ;;
    finalize) ELAPSTIM_REQ=00:30:00 ;;
  esac
  walltime_seconds "$ELAPSTIM_REQ"
}

check_checkout() {
  REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../.." 2>/dev/null) || fail 4 checkout root_unavailable
  local canonical status symbolic_rc
  canonical=$(git -C "$REPO_ROOT" rev-parse --show-toplevel 2>/dev/null) || fail 4 checkout root_unavailable
  canonical=$(realpath -e -- "$canonical" 2>/dev/null) || fail 4 checkout root_unavailable
  [[ "$REPO_ROOT" == "$canonical" ]] || fail 4 checkout root_mismatch
  symbolic_rc=0
  git -C "$REPO_ROOT" symbolic-ref -q HEAD >/dev/null 2>&1 || symbolic_rc=$?
  case "$symbolic_rc" in
    1) ;;
    0) fail 4 checkout detached_required ;;
    *) fail 4 checkout head_observation_failed ;;
  esac
  status=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=no 2>/dev/null) || fail 4 checkout status_failed
  [[ -z "$status" ]] || fail 4 checkout tracked_dirty
  HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit} 2>/dev/null) || fail 4 checkout head_observation_failed
  [[ "$HEAD" =~ ^[0-9a-f]{40}$ ]] || fail 4 checkout head_observation_failed
}

check_spec_binding() {
  local file_hash blob_hash
  file_hash=$(sha256sum -- "$REPO_ROOT/$SPEC_RELPATH" 2>/dev/null) || fail 4 spec file_unavailable
  [[ "${file_hash%% *}" == "$SPEC_SHA256" ]] || fail 4 spec file_hash_mismatch
  blob_hash=$(git -C "$REPO_ROOT" show "HEAD:$SPEC_RELPATH" 2>/dev/null | sha256sum 2>/dev/null) || fail 4 spec blob_unavailable
  [[ "${blob_hash%% *}" == "$SPEC_SHA256" ]] || fail 4 spec blob_hash_mismatch
}

check_outputs() {
  # Only header/terminal readiness: full artifact validation belongs to the driver.
  "$PY" -I -B -c '
import json, os, pathlib, sys
root, relpath, mode, selected, head = sys.argv[1:]
root = pathlib.Path(root)
def refuse(reason):
    print(json.dumps(dict(gate="outputs", reason=reason), separators=(",", ":")), file=sys.stderr)
    raise SystemExit(4)
try:
    spec = json.load(open(root / relpath))
    if mode == "finalize" and os.path.lexists(root / spec["outputs"]["summary_relpath"]):
        refuse("summary_exists")
    for window in spec["windows"]:
        path = root / window["artifact_relpath"]
        exists = os.path.lexists(path)
        if mode == "window" and window["window_id"] == selected:
            if exists:
                refuse("window_exists")
            continue
        if not exists:
            if mode == "finalize":
                refuse("window_missing")
            continue
        with open(path) as stream:
            header = json.loads(stream.readline())
            if header.get("loaded_head") != head: refuse("loaded_head_mismatch")
            if mode == "finalize":
                last = ""
                for line in stream:
                    last = line
                if not last or json.loads(last).get("event") != "terminal":
                    refuse("terminal_missing")
except (OSError, ValueError, KeyError, TypeError, AttributeError):
    refuse("unreadable_artifact")
' "$REPO_ROOT" "$SPEC_RELPATH" "$MODE" "$WINDOW_ID" "$HEAD"
}

build_qsub_argv() {
  EXPORT_SPEC="FP_NONCE=$NONCE,FP_EXPECTED_HEAD=$HEAD,FP_SPEC_RELPATH=$SPEC_RELPATH,FP_SPEC_SHA256=$SPEC_SHA256,FP_MODE=$MODE,FP_WINDOW_ID=$WINDOW_ID,FP_EVIDENCE_DIR=$EVIDENCE_DIR,FP_ELAPSTIM_REQ=$ELAPSTIM_REQ"
  qsub_cmd=(qsub -l "elapstim_req=$ELAPSTIM_REQ" -N "fp-$WORKLOAD-$WINDOW"
    -v "$EXPORT_SPEC" -o "$EVIDENCE_DIR/scheduler.stdout" -e "$EVIDENCE_DIR/scheduler.stderr"
    tools/pegasus/floor_pair_campaign.sh)
}

write_pre_submit() {
  "$PY" -I -B -c '
import json, pathlib, sys
(directory, nonce, head, root, spec, sha, mode, window, walltime, duration,
 dry_run, prepared, *argv) = sys.argv[1:]
payload = dict(schema_version="pegasus-floor-pair-submit-receipt/v1", nonce=nonce,
 expected_head=head, repo_root=root, spec_relpath=spec, spec_sha256=sha, mode=mode,
 window_id=None if mode == "finalize" else window, evidence_dir=directory,
 request=dict(project="SFC", queue="gen_S", nodes=1, elapstim_req=walltime, elapstim_req_s=int(duration)),
 qsub_argv=argv, dry_run=bool(int(dry_run)), qsub_rc=None, pbs_jobid=None,
 status="prepared", prepared_epoch=int(prepared), completed_epoch=None)
with open(pathlib.Path(directory) / "pre-submit.json", "x") as stream:
    json.dump(payload, stream, sort_keys=True)
    stream.write("\n")
' "$EVIDENCE_DIR" "$NONCE" "$HEAD" "$REPO_ROOT" "$SPEC_RELPATH" "$SPEC_SHA256" "$MODE" \
    "$WINDOW_ID" "$ELAPSTIM_REQ" "$DURATION" "$DRY_RUN" "$PREPARED_EPOCH" "${qsub_cmd[@]}" 2>/dev/null || fail 4 evidence pre_submit_failed
}

write_submit_receipt() {
  "$PY" -I -B -c '
import json, pathlib, sys, time
directory, status, rc, jobid = sys.argv[1:]
directory = pathlib.Path(directory)
payload = json.load(open(directory / "pre-submit.json"))
payload.update(status=status, qsub_rc=int(rc) if rc else None,
 pbs_jobid=jobid or None, completed_epoch=int(time.time()))
with open(directory / "submit-receipt.json", "x") as stream:
    json.dump(payload, stream, sort_keys=True)
    stream.write("\n")
' "$EVIDENCE_DIR" "$STATUS" "$QSUB_RC" "$PBS_REQUEST_ID" 2>/dev/null || fail 4 evidence submit_receipt_failed
}

submit_or_dry_run() {
  QSUB_RC= PBS_REQUEST_ID=
  if (( DRY_RUN )); then
    STATUS=dry_run
    write_submit_receipt
    return 0
  fi
  cd -P -- "$REPO_ROOT" 2>/dev/null || fail 4 checkout root_unavailable
  set -o noclobber
  { exec {QSUB_OUT}>"$EVIDENCE_DIR/qsub.stdout"; } 2>/dev/null || fail 4 evidence qsub_stdout_unwritable
  { exec {QSUB_ERR}>"$EVIDENCE_DIR/qsub.stderr"; } 2>/dev/null || fail 4 evidence qsub_stderr_unwritable
  QSUB_RC=0
  "${qsub_cmd[@]}" >&"$QSUB_OUT" 2>&"$QSUB_ERR" || QSUB_RC=$?
  exec {QSUB_OUT}>&- {QSUB_ERR}>&-
  { printf '%s\n' "$QSUB_RC" >"$EVIDENCE_DIR/qsub.rc"; } 2>/dev/null || fail 4 evidence qsub_rc_unwritable
  STATUS=failed
  if (( QSUB_RC == 0 )); then
    STATUS=indeterminate
    if PBS_REQUEST_ID=$("$PY" -I -B -c '
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
match = re.search(r"Request\s+(\S+)\s+submitted", text)
tokens = text.split()
request = match.group(1).rstrip(".") if match else tokens[0] if len(tokens) == 1 else ""
if not re.fullmatch(r"([0-9]+:)?[A-Za-z0-9._-]+", request):
    raise SystemExit(2)
print(request)
' "$EVIDENCE_DIR/qsub.stdout" 2>/dev/null); then STATUS=submitted; fi
  fi
  write_submit_receipt
  [[ "$STATUS" == submitted ]] || fail 4 submission "$STATUS"
}

parse_args "$@"
clean_environment
select_python
trap 'fail 4 submission unhandled_failure' ERR
select_pin
select_walltime
WINDOW_ID=none
if [[ "$MODE" == window ]]; then WINDOW_ID=$WORKLOAD-$WINDOW; fi
SCRIPT_DIR=$(cd -- "${BASH_SOURCE[0]%/*}" && pwd -P) || fail 4 checkout script_root_unavailable
check_checkout
check_spec_binding
check_binaries "$REPO_ROOT" "$SPEC_RELPATH"
if [[ "$MODE" == window ]]; then
  read_window_bounds "$REPO_ROOT/$SPEC_RELPATH" "$WINDOW_ID"
  NOW=$(date -u +%s 2>/dev/null) || fail 4 window clock_unavailable
  window_gate "$NOW" "$NOT_BEFORE" "$NOT_AFTER" "$DURATION"
fi
check_outputs || exit $?
BASE=/work/1/SFC/tanab/izanagi-job-evidence/floor-pair
NONCE=$("$PY" -I -B -c 'import secrets; print(secrets.token_hex(16))' 2>/dev/null) || fail 4 evidence nonce_failed
EVIDENCE_DIR=$BASE/$NONCE
mkdir -p -- "$BASE" 2>/dev/null || fail 4 evidence base_create_failed
mkdir -m 0700 -- "$EVIDENCE_DIR" 2>/dev/null || fail 4 evidence leaf_create_failed
PREPARED_EPOCH=$(date -u +%s 2>/dev/null) || fail 4 evidence clock_unavailable
build_qsub_argv
write_pre_submit
submit_or_dry_run
