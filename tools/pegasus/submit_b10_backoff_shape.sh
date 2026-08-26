#!/bin/bash
# Login-side submitter for the registered B10 performance campaign.
set -Eeuo pipefail
umask 077

usage() {
  echo "usage: submit_b10_backoff_shape.sh --prereg-commit COMMIT [--dry-run]" >&2
}

PREREG_COMMIT=""
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prereg-commit)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      PREREG_COMMIT=$2
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
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

[[ "$PREREG_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
  echo "--prereg-commit must be a full lowercase commit ID" >&2
  exit 2
}

SCRIPT_SOURCE=${BASH_SOURCE[0]}
SCRIPT_PATH=$(realpath -e -- "$SCRIPT_SOURCE")
[[ -f "$SCRIPT_PATH" && ! -L "$SCRIPT_SOURCE" && ! -L "$SCRIPT_PATH" ]]
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
JOB_SCRIPT="$SCRIPT_DIR/b10_backoff_shape_campaign.sh"
[[ -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]]
[[ "$SCRIPT_PATH" == "$REPO_ROOT/tools/pegasus/submit_b10_backoff_shape.sh" ]]

SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})
[[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]
git -C "$REPO_ROOT" merge-base --is-ancestor "$PREREG_COMMIT" "$SOURCE_COMMIT"
git -C "$REPO_ROOT" cat-file -e \
  "$PREREG_COMMIT:docs/b10-backoff-shape-preregistration.md"
git -C "$REPO_ROOT" cat-file -e "$PREREG_COMMIT:patches/silo-backoff-fixed.patch"
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] || {
  echo "repository working tree must be clean" >&2
  exit 2
}

NONCE=$(python3 -I -B -c 'import secrets; print(secrets.token_hex(16))')
SUBMISSION_ROOT="$REPO_ROOT/output/env/pegasus/b10-backoff-shape/submissions"
SUBMISSION_DIR="$SUBMISSION_ROOT/$NONCE"
mkdir -p "$SUBMISSION_ROOT"
mkdir "$SUBMISSION_DIR"
SCHEDULER_STDOUT="$SUBMISSION_DIR/scheduler.stdout"
SCHEDULER_STDERR="$SUBMISSION_DIR/scheduler.stderr"

python3 -I -B - "$SUBMISSION_DIR/pre-submit.json" "$SOURCE_COMMIT" \
  "$PREREG_COMMIT" "$NONCE" "$JOB_SCRIPT" <<'PY'
import hashlib
import json
import pathlib
import sys

target, source, prereg, nonce, job = sys.argv[1:]
job_path = pathlib.Path(job)
payload = {
    "schema_version": "pegasus-b10-submit-preflight/v1",
    "source_commit": source,
    "prereg_commit": prereg,
    "nonce": nonce,
    "job_script_path": "tools/pegasus/b10_backoff_shape_campaign.sh",
    "job_script_sha256": hashlib.sha256(job_path.read_bytes()).hexdigest(),
}
with open(target, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
PY

export_spec="IZANAGI_B10_NONCE=$NONCE,IZANAGI_B10_SOURCE_COMMIT=$SOURCE_COMMIT,IZANAGI_B10_PREREG_COMMIT=$PREREG_COMMIT"
qsub_cmd=(
  qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR"
  -v "$export_spec" "$JOB_SCRIPT"
)
printf 'qsub command:'
printf ' %q' "${qsub_cmd[@]}"
printf '\n'

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' dry-run >"$SUBMISSION_DIR/qsub.stdout"
  : >"$SUBMISSION_DIR/qsub.stderr"
  REQUEST_ID="dry-run-$NONCE"
else
  (
    cd "$REPO_ROOT"
    "${qsub_cmd[@]}"
  ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"
  REQUEST_ID=$(python3 -I -B - "$SUBMISSION_DIR/qsub.stdout" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
match = re.search(r"Request\s+(\S+)\s+submitted", text)
tokens = text.split()
if match:
    print(match.group(1).rstrip("."))
elif len(tokens) == 1:
    print(tokens[0].rstrip("."))
else:
    raise SystemExit(2)
PY
  )
  request_visible=0
  for attempt in 1 2 3; do
    qstat_rc=0
    timeout 20 qstat -f "${REQUEST_ID#0:}" \
      >"$SUBMISSION_DIR/qstat-$attempt.stdout" \
      2>"$SUBMISSION_DIR/qstat-$attempt.stderr" || qstat_rc=$?
    printf '%s\n' "$qstat_rc" >"$SUBMISSION_DIR/qstat-$attempt.rc"
    qstat_visible=1
    if [[ "$qstat_rc" -eq 0 ]]; then
      python3 -I -B - "$SUBMISSION_DIR/qstat-$attempt.stdout" "$REQUEST_ID" <<'PY' \
        || qstat_visible=0
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
expected = sys.argv[2].removeprefix("0:").rstrip(".")
observed = [value.removeprefix("0:").rstrip(".") for value in
            re.findall(r"(?im)^\s*Request ID\s*[:=]\s*(\S+)\s*$", text)]
raise SystemExit(0 if observed == [expected] else 1)
PY
    else
      qstat_visible=0
    fi
    if [[ "$qstat_visible" -eq 1 ]]; then
      request_visible=1
      break
    fi
    sleep 2
  done
  [[ "$request_visible" -eq 1 ]] || {
    echo "qsub succeeded but the exact request is not visible via qstat; submission is not certified" >&2
    exit 4
  }
fi

python3 -I -B - "$SUBMISSION_DIR/submit-receipt.json" "$SOURCE_COMMIT" \
  "$PREREG_COMMIT" "$NONCE" "$REQUEST_ID" "$DRY_RUN" <<'PY'
import json
import sys
import time

target, source, prereg, nonce, request_id, dry_run = sys.argv[1:]
payload = {
    "schema_version": "pegasus-b10-submit-receipt/v1",
    "source_commit": source,
    "prereg_commit": prereg,
    "nonce": nonce,
    "request_id": request_id,
    "dry_run": dry_run == "1",
    "submitted_epoch": int(time.time()),
}
with open(target, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
PY

echo "submission receipt: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
