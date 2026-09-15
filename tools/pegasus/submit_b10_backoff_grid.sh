#!/bin/bash
# Login-side fan-out: submit one independent job for each B-10 workload.
set -Eeuo pipefail
umask 077

usage() {
  echo "usage: submit_b10_backoff_grid.sh --output-parent ABSOLUTE_PATH" \
    "[--run-kind extended|t2266-tail|t2418-explore|t2500-tail-formal]" \
    "[--preregistration-commit SHA40 --explore-campaign ABSOLUTE_PATH]" >&2
  echo "The two new flags are required and valid only for t2500-tail-formal." >&2
}

OUTPUT_PARENT=""
B10_RUN_KIND=extended
B10_PREREGISTRATION_COMMIT=""
B10_EXPLORE_CAMPAIGN=""
PREREGISTRATION_COMMIT_SPECIFIED=0
EXPLORE_CAMPAIGN_SPECIFIED=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-parent)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      OUTPUT_PARENT=$2
      shift 2
      ;;
    --run-kind)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      B10_RUN_KIND=$2
      shift 2
      ;;
    --preregistration-commit)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      B10_PREREGISTRATION_COMMIT=$2
      PREREGISTRATION_COMMIT_SPECIFIED=1
      shift 2
      ;;
    --explore-campaign)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      B10_EXPLORE_CAMPAIGN=$2
      EXPLORE_CAMPAIGN_SPECIFIED=1
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

case "$B10_RUN_KIND" in
  extended|t2266-tail|t2418-explore|t2500-tail-formal) ;;
  *) usage; exit 2 ;;
esac
export B10_RUN_KIND

if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
  [[ "$PREREGISTRATION_COMMIT_SPECIFIED" == 1 && "$EXPLORE_CAMPAIGN_SPECIFIED" == 1 \
      && "$B10_PREREGISTRATION_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
    echo "t2500-tail-formal requires both inputs and a lowercase 40-digit commit" >&2
    exit 2
  }
  [[ -n "$B10_EXPLORE_CAMPAIGN" && "$B10_EXPLORE_CAMPAIGN" == /* \
      && -d "$B10_EXPLORE_CAMPAIGN" && ! -L "$B10_EXPLORE_CAMPAIGN" \
      && "$B10_EXPLORE_CAMPAIGN" =~ ^[A-Za-z0-9._/-]+$ ]] || {
    echo "explore campaign must be an existing safe absolute directory, not a symlink" >&2
    exit 2
  }
  # Preserve path newlines until validation; remove only realpath's terminator.
  resolved=$(realpath -e -- "$B10_EXPLORE_CAMPAIGN" && printf 'x') || exit 2
  resolved=${resolved%x}
  B10_EXPLORE_CAMPAIGN=${resolved%$'\n'}
  [[ "$B10_EXPLORE_CAMPAIGN" =~ ^[A-Za-z0-9._/-]+$ ]] || {
    echo "resolved explore campaign contains characters unsafe for qsub -v" >&2
    exit 2
  }
elif [[ "$PREREGISTRATION_COMMIT_SPECIFIED" == 1 || "$EXPLORE_CAMPAIGN_SPECIFIED" == 1 ]]; then
  echo "preregistration commit and explore campaign are only valid for t2500-tail-formal" >&2
  exit 2
fi

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
JOB_SCRIPT="$SCRIPT_DIR/b10_backoff_grid.sh"
[[ -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]] || {
  echo "B-10 job script is missing or a symlink" >&2
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

if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
  "${PYTHON:-python3}" -I -B - "$REPO_ROOT" "$B10_EXPLORE_CAMPAIGN" <<'PY_EXPLORE'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=True)
if (target == repo or repo in target.parents or target in repo.parents
        or any((parent / ".git").exists() for parent in (target, *target.parents))):
    print("explore campaign must be outside repositories and their ancestors", file=sys.stderr)
    raise SystemExit(2)
PY_EXPLORE
fi

for command_name in qstat qsub pegasusinfo check_quota sha256sum; do
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

GROUP_ID="b10-backoff-grid-$(date -u +%Y%m%dT%H%M%SZ)-$$"
SUBMISSION_NONCE=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')
JOB_SCRIPT_SHA256=$(sha256sum -- "$JOB_SCRIPT")
JOB_SCRIPT_SHA256=${JOB_SCRIPT_SHA256%% *}
RECEIPT="$OUTPUT_PARENT/$GROUP_ID.submit.jsonl"
[[ ! -e "$RECEIPT" ]] || { echo "submission receipt already exists" >&2; exit 2; }

WORKLOADS=(write-heavy balanced read-heavy)
for workload in "${WORKLOADS[@]}"; do
  root="$OUTPUT_PARENT/$GROUP_ID-$workload"
  stdout="$OUTPUT_PARENT/$GROUP_ID-$workload.stdout"
  stderr="$OUTPUT_PARENT/$GROUP_ID-$workload.stderr"
  [[ ! -e "$root" && ! -e "$stdout" && ! -e "$stderr" ]] || {
    echo "job-unique output already exists for $workload" >&2
    exit 2
  }
done

append_submission_event() {
  python3.10 -I -B - "$RECEIPT" "$@" <<'PY'
import json, os, pathlib, stat, sys
path = pathlib.Path(sys.argv[1])
kind = sys.argv[2]
values = sys.argv[3:]
run_kind = os.environ["B10_RUN_KIND"]
if kind == "manifest":
    group, nonce, script_hash, *workloads = values
    event = {
        "schema_version": "b10-backoff-grid-submit-event/v1",
        "event": "manifest",
        "run_kind": run_kind,
        "group_id": group,
        "submission_nonce": nonce,
        "job_script_sha256": script_hash,
        "workloads": workloads,
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
elif kind == "submitted":
    workload, job_id, root, stdout, stderr = values
    event = {
        "schema_version": "b10-backoff-grid-submit-event/v1",
        "event": "submitted",
        "run_kind": run_kind,
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
        "schema_version": "b10-backoff-grid-submit-event/v1",
        "event": "failed",
        "run_kind": run_kind,
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
  "$JOB_SCRIPT_SHA256" "${WORKLOADS[@]}"

for workload in "${WORKLOADS[@]}"; do
  root="$OUTPUT_PARENT/$GROUP_ID-$workload"
  stdout="$OUTPUT_PARENT/$GROUP_ID-$workload.stdout"
  stderr="$OUTPUT_PARENT/$GROUP_ID-$workload.stderr"
  QSUB_ENV="B10_WORKLOAD=$workload,B10_OUTPUT_ROOT=$root,B10_SUBMISSION_NONCE=$SUBMISSION_NONCE,JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256"
  if [[ "$B10_RUN_KIND" == "t2266-tail" \
      || "$B10_RUN_KIND" == "t2418-explore" ]]; then
    QSUB_ENV="$QSUB_ENV,B10_RUN_KIND=$B10_RUN_KIND"
  fi
  if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
    QSUB_ENV="$QSUB_ENV,B10_RUN_KIND=$B10_RUN_KIND"
    QSUB_ENV="$QSUB_ENV,B10_PREREGISTRATION_COMMIT=$B10_PREREGISTRATION_COMMIT"
    QSUB_ENV="$QSUB_ENV,B10_EXPLORE_CAMPAIGN=$B10_EXPLORE_CAMPAIGN"
  fi
  qsub_rc=0
  job_id=$(qsub \
    -v "$QSUB_ENV" \
    -o "$stdout" -e "$stderr" "$JOB_SCRIPT") || qsub_rc=$?
  if [[ "$qsub_rc" -ne 0 ]]; then
    append_submission_event failed "$workload" "$qsub_rc" "qsub_failed"
    exit "$qsub_rc"
  fi
  if [[ -z "$job_id" ]]; then
    append_submission_event failed "$workload" 2 "qsub_returned_empty_job_id"
    echo "qsub returned no job id for $workload" >&2
    exit 2
  fi
  append_submission_event submitted \
    "$workload" "$job_id" "$root" "$stdout" "$stderr"
  printf '%s\n' "$job_id"
done
