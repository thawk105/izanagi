#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=06:00:00
#PBS -b 1
#
# Compute-only job body for the D95 paper-story A-1 exploratory study.
# Submission is intentionally outside this file: the parent uses direct qsub
# with -v plus repo-external -o/-e files.
set -Eeuo pipefail
umask 077

EXPECTED_STUDY_ID="paper-story-a1-20260824-exploratory-v1"
DRIVER_RELATIVE="orchestrator/campaign/paper_story_a1_paired.py"

refuse() {
  printf 'paper-story A-1 job refused: %s\n' "$1" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" ]] || refuse "PBS_JOBID is required"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || refuse "unsafe PBS_JOBID"
[[ -n "${PBS_O_WORKDIR:-}" ]] || refuse "PBS_O_WORKDIR is required"
[[ "${IZANAGI_A1_STUDY_ID:-}" == "$EXPECTED_STUDY_ID" ]] || refuse "study ID differs"
[[ "${IZANAGI_EXPECTED_HEAD:-}" =~ ^[0-9a-f]{40}$ ]] || refuse "expected HEAD is invalid"
[[ -n "${IZANAGI_A1_RAW_ROOT:-}" ]] || refuse "raw root is required"
[[ -n "${IZANAGI_A1_CACHE_ROOT:-}" ]] || refuse "cache root is required"
[[ "$IZANAGI_A1_RAW_ROOT" = /* ]] || refuse "raw root must be absolute"
[[ "$IZANAGI_A1_CACHE_ROOT" = /* ]] || refuse "cache root must be absolute"

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -f "$REPO_ROOT/$DRIVER_RELATIVE" ]] || refuse "tracked driver is missing"
CURRENT_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD) || refuse "cannot resolve HEAD"
[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]] || refuse "HEAD mismatch"
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] || \
  refuse "working tree is dirty"

PYTHON_BIN=""
for candidate in python3.10 python3.11 python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && \
      "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v "$candidate")
    break
  fi
done
[[ -n "$PYTHON_BIN" ]] || refuse "Python 3.10 or newer is required"

"$PYTHON_BIN" - "$REPO_ROOT" <<'PY' || refuse "Pegasus compute site check failed"
import sys

repo = sys.argv[1]
sys.path.insert(0, repo)
from orchestrator.campaign import site_policy

if site_policy.current_site() != site_policy.PEGASUS_COMPUTE:
    raise SystemExit("not Pegasus compute")
PY

"$PYTHON_BIN" - "$REPO_ROOT" "$IZANAGI_A1_RAW_ROOT" "$IZANAGI_A1_CACHE_ROOT" <<'PY' \
  || refuse "root preflight failed"
import os
import pathlib
import sys

repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
roots = [pathlib.Path(value) for value in sys.argv[2:]]
resolved = []
for root in roots:
    if not root.is_absolute():
        raise SystemExit("root is not absolute")
    item = root.resolve(strict=False)
    try:
        item.relative_to(repo)
    except ValueError:
        pass
    else:
        raise SystemExit("root is inside repository")
    if os.path.lexists(root) or os.path.lexists(item):
        raise SystemExit("root already exists")
    resolved.append(item)
if len(set(resolved)) != len(resolved):
    raise SystemExit("roots are not distinct")
PY

if ! mkdir -- "$IZANAGI_A1_RAW_ROOT"; then
  refuse "raw attempt root cannot be exclusive-created"
fi
ATTEMPT_CREATED=1
OUTPUT_ROOT="$IZANAGI_A1_RAW_ROOT/campaign-output"
RESULT_ROOT="$IZANAGI_A1_RAW_ROOT/results"
TMP_ROOT="$IZANAGI_A1_RAW_ROOT/tmp"
if ! mkdir -- "$TMP_ROOT"; then
  refuse "temporary root cannot be exclusive-created"
fi
export TMPDIR="$TMP_ROOT"
export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"
DRIVER_RC="not-run"
TERMINAL_PATH="$IZANAGI_A1_RAW_ROOT/job-terminal.json"

write_terminal() {
  local shell_rc=$1
  [[ "$ATTEMPT_CREATED" -eq 1 ]] || return 0
  [[ ! -e "$TERMINAL_PATH" ]] || return 0
  "$PYTHON_BIN" - "$TERMINAL_PATH" "$EXPECTED_STUDY_ID" "$PBS_JOBID" \
    "$IZANAGI_EXPECTED_HEAD" "$DRIVER_RC" "$shell_rc" "$RESULT_ROOT" <<'PY'
import hashlib
import json
import os
import sys
import time

(
    path, study_id, pbs_jobid, expected_head, driver_rc_raw, shell_rc_raw,
    result_root,
) = sys.argv[1:]
try:
    driver_rc = int(driver_rc_raw)
except ValueError:
    driver_rc = int(shell_rc_raw)
result_path = os.path.join(result_root, "result.json")
receipt_path = os.path.join(result_root, "receipt.json")

def digest(candidate):
    if not os.path.isfile(candidate):
        return None
    value = hashlib.sha256()
    with open(candidate, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

result_sha = digest(result_path)
receipt_sha = digest(receipt_path)
document = {
    "schema_version": "paper-story-a1-paired-job-terminal/v1",
    "study_id": study_id,
    "pbs_jobid": pbs_jobid,
    "expected_head": expected_head,
    "driver_rc": driver_rc,
    "shell_rc": int(shell_rc_raw),
    "status": (
        "finished"
        if driver_rc == 0 and result_sha is not None and receipt_sha is not None
        else "failed"
    ),
    "result_sha256": result_sha,
    "receipt_sha256": receipt_sha,
    "recorded_epoch": int(time.time()),
}
with open(path, "x", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
PY
}

on_exit() {
  local shell_rc=$?
  trap - EXIT
  write_terminal "$shell_rc" || true
  exit "$shell_rc"
}
trap on_exit EXIT

set +e
"$PYTHON_BIN" "$REPO_ROOT/$DRIVER_RELATIVE" measure \
  --study-id "$EXPECTED_STUDY_ID" \
  --expected-head "$IZANAGI_EXPECTED_HEAD" \
  --pbs-jobid "$PBS_JOBID" \
  --output-root "$OUTPUT_ROOT" \
  --cache-root "$IZANAGI_A1_CACHE_ROOT" \
  --result-root "$RESULT_ROOT"
DRIVER_RC=$?
set -e
exit "$DRIVER_RC"
