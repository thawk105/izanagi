#!/bin/bash
# Login-side T-1998 submitter: submit the balanced stock-inline producer once.
set -Eeuo pipefail
umask 077

usage() {
  echo "usage: submit_t1998_balanced_stock_inline.sh --output-parent ABSOLUTE_PATH" >&2
}

OUTPUT_PARENT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-parent)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      OUTPUT_PARENT=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[[ -n "$OUTPUT_PARENT" && "$OUTPUT_PARENT" == /* && -d "$OUTPUT_PARENT" \
    && ! -L "$OUTPUT_PARENT" ]] || {
  echo "--output-parent must name an existing absolute directory" >&2
  exit 2
}
[[ "$OUTPUT_PARENT" =~ ^[A-Za-z0-9._/-]+$ ]] || {
  echo "output parent contains characters unsafe for qsub -v" >&2
  exit 2
}
OUTPUT_PARENT=$(realpath -e -- "$OUTPUT_PARENT")

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
SUBMITTER_PATH="tools/pegasus/submit_t1998_balanced_stock_inline.sh"
JOB_SCRIPT="$SCRIPT_DIR/a5_second_boot_backoff_sweep.sh"
JOB_SCRIPT_PATH="tools/pegasus/a5_second_boot_backoff_sweep.sh"
[[ -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]] || {
  echo "A-5 job script is missing or a symlink" >&2
  exit 2
}
"${PYTHON:-python3}" -I -B - "$REPO_ROOT" "$OUTPUT_PARENT" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=True)
if target == repo or repo in target.parents or target in repo.parents:
    raise SystemExit("output parent must be outside the repository")
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    raise SystemExit("output parent has a repository ancestor")
PY

for command_name in git qstat qsub pegasusinfo check_quota sha256sum python3.10; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required submission command is unavailable: $command_name" >&2
    exit 2
  }
done
python3.10 -I -B -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 10))'
check_quota >/dev/null
QUEUE_STATE=$(qstat -Q)
printf '%s\n' "$QUEUE_STATE" | python3.10 -I -B -c '
import re, sys
text = sys.stdin.read()
raise SystemExit(0 if "gen_S" in text
                 and re.search(r"(?i)\b(ENA|ENABLE(?:D)?)\b", text)
                 and re.search(r"(?i)\b(ACT|ACTIVE)\b", text) else 1)
' || {
  echo "gen_S is not ENA/ACT" >&2
  exit 2
}
PEGASUS_INFO=$(pegasusinfo)
[[ -n "$PEGASUS_INFO" ]] || { echo "pegasusinfo returned no data" >&2; exit 2; }

EXPECTED_HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})
[[ "$EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || {
  echo "repository HEAD is not a full commit id" >&2
  exit 2
}
GROUP_ID="t1998-balanced-stock-inline-$(date -u +%Y%m%dT%H%M%SZ)-$$"
SUBMISSION_NONCE=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')
SUBMITTER_SHA256=$(sha256sum -- "$SCRIPT_PATH")
SUBMITTER_SHA256=${SUBMITTER_SHA256%% *}
JOB_SCRIPT_SHA256=$(sha256sum -- "$JOB_SCRIPT")
JOB_SCRIPT_SHA256=${JOB_SCRIPT_SHA256%% *}
RECEIPT="$OUTPUT_PARENT/$GROUP_ID.submit.jsonl"
[[ ! -e "$RECEIPT" ]] || { echo "submission receipt already exists" >&2; exit 2; }

WORKLOAD=balanced
root="$OUTPUT_PARENT/$GROUP_ID-$WORKLOAD"
stdout="$OUTPUT_PARENT/$GROUP_ID-$WORKLOAD.stdout"
stderr="$OUTPUT_PARENT/$GROUP_ID-$WORKLOAD.stderr"
[[ ! -e "$root" && ! -e "$stdout" && ! -e "$stderr" ]] || {
  echo "job-unique output already exists for $WORKLOAD" >&2
  exit 2
}

append_submission_event() {
  python3.10 -I -B - "$RECEIPT" "$@" <<'PY'
import json, os, pathlib, stat, sys
path = pathlib.Path(sys.argv[1])
kind = sys.argv[2]
values = sys.argv[3:]
if kind == "manifest":
    (group, nonce, submitter_path, submitter_hash, job_script_path,
     job_script_hash, expected_head, workload) = values
    event = {
        "schema_version": "t1998-balanced-stock-inline-submit-event/v1",
        "event": "manifest",
        "group_id": group,
        "submission_nonce": nonce,
        "submitter_path": submitter_path,
        "submitter_sha256": submitter_hash,
        "job_script_path": job_script_path,
        "job_script_sha256": job_script_hash,
        "repository_commit": expected_head,
        "workloads": [workload],
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
elif kind == "submitted":
    workload, job_id, root, stdout, stderr = values
    event = {
        "schema_version": "t1998-balanced-stock-inline-submit-event/v1",
        "event": "submitted",
        "workload": workload,
        "job_id": job_id,
        "output_root": root,
        "stdout": stdout,
        "stderr": stderr,
    }
    flags = os.O_WRONLY | os.O_APPEND
elif kind == "failed":
    workload, returncode, reason = values
    event = {
        "schema_version": "t1998-balanced-stock-inline-submit-event/v1",
        "event": "failed",
        "workload": workload,
        "returncode": int(returncode),
        "reason": reason,
    }
    flags = os.O_WRONLY | os.O_APPEND
else:
    raise SystemExit("unknown submission event")
flags |= getattr(os, "O_NOFOLLOW", 0)
if kind != "manifest":
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SystemExit("submission receipt is not a unique regular file")
payload = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
fd = os.open(path, flags, 0o600)
try:
    if os.write(fd, payload) != len(payload):
        raise OSError("short submission receipt append")
    os.fsync(fd)
finally:
    os.close(fd)
parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
try:
    os.fsync(parent_fd)
finally:
    os.close(parent_fd)
PY
}

append_submission_event manifest "$GROUP_ID" "$SUBMISSION_NONCE" \
  "$SUBMITTER_PATH" "$SUBMITTER_SHA256" "$JOB_SCRIPT_PATH" \
  "$JOB_SCRIPT_SHA256" "$EXPECTED_HEAD" "$WORKLOAD"

cd -- "$REPO_ROOT"
qsub_rc=0
job_id=$(qsub \
  -v "A5_WORKLOAD=$WORKLOAD,A5_OUTPUT_ROOT=$root,A5_SUBMISSION_NONCE=$SUBMISSION_NONCE,A5_EXPECTED_HEAD=$EXPECTED_HEAD,JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256" \
  -o "$stdout" -e "$stderr" "$JOB_SCRIPT") || qsub_rc=$?
if [[ "$qsub_rc" -ne 0 ]]; then
  append_submission_event failed "$WORKLOAD" "$qsub_rc" "qsub_failed"
  exit "$qsub_rc"
fi
if [[ -z "$job_id" ]]; then
  append_submission_event failed "$WORKLOAD" 2 "qsub_returned_empty_job_id"
  echo "qsub returned no job id for $WORKLOAD" >&2
  exit 2
fi
append_submission_event submitted \
  "$WORKLOAD" "$job_id" "$root" "$stdout" "$stderr"
printf '%s\n' "$job_id"
