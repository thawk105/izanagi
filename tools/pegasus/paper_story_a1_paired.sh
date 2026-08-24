#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=06:00:00
#PBS -b 1
#
# Compute-only job body for the D95 paper-story A-1 exploratory study.
# A parent performs direct qsub and then create-only writes the acquisition
# receipt consumed here. This file is not a submitter.
set -Eeuo pipefail
umask 077

EXPECTED_STUDY_ID="paper-story-a1-20260824-exploratory-v1"
EXPECTED_QUEUE="gen_S"
SUBMISSION_SCHEMA="paper-story-a1-paired-submission/v1"
DRIVER_RELATIVE="orchestrator/campaign/paper_story_a1_paired.py"
POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v1.json"
PIPELINE_RELATIVE="orchestrator/campaign/pipeline.py"
JOB_RELATIVE="tools/pegasus/paper_story_a1_paired.sh"

refuse() {
  printf 'paper-story A-1 job refused: %s\n' "$1" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" ]] || refuse "PBS_JOBID is required"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || refuse "unsafe PBS_JOBID"
[[ -n "${PBS_O_HOST:-}" ]] || refuse "PBS_O_HOST is required"
[[ -n "${PBS_O_WORKDIR:-}" ]] || refuse "PBS_O_WORKDIR is required"
[[ -n "${PBS_O_QUEUE:-}" ]] || refuse "PBS_O_QUEUE is required"
[[ "${IZANAGI_A1_STUDY_ID:-}" == "$EXPECTED_STUDY_ID" ]] || refuse "study ID differs"
[[ "${IZANAGI_EXPECTED_HEAD:-}" =~ ^[0-9a-f]{40}$ ]] || refuse "expected HEAD is invalid"
[[ -n "${IZANAGI_A1_ATTEMPT_ROOT:-}" ]] || refuse "attempt root is required"
[[ -n "${IZANAGI_A1_ACQUISITION_RECEIPT:-}" ]] || refuse "acquisition receipt is required"
[[ -n "${IZANAGI_A1_COMPLETION_RECEIPT:-}" ]] || refuse "completion receipt is required"
[[ "$IZANAGI_A1_ATTEMPT_ROOT" = /* ]] || refuse "attempt root must be absolute"
[[ "$IZANAGI_A1_ACQUISITION_RECEIPT" = /* ]] || refuse "acquisition receipt must be absolute"
[[ "$IZANAGI_A1_COMPLETION_RECEIPT" = /* ]] || refuse "completion receipt must be absolute"

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -f "$REPO_ROOT/$DRIVER_RELATIVE" ]] || refuse "tracked driver is missing"
[[ -f "$REPO_ROOT/$POLICY_RELATIVE" ]] || refuse "tracked policy is missing"
[[ -f "$REPO_ROOT/$JOB_RELATIVE" ]] || refuse "tracked job body is missing"
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

PBS_STDOUT_PATH=$("$PYTHON_BIN" -c \
  'import os, sys; print(os.readlink(f"/proc/{sys.argv[1]}/fd/1"))' "$$") || \
  refuse "cannot observe PBS stdout path"
PBS_STDERR_PATH=$("$PYTHON_BIN" -c \
  'import os, sys; print(os.readlink(f"/proc/{sys.argv[1]}/fd/2"))' "$$") || \
  refuse "cannot observe PBS stderr path"
[[ "$PBS_STDOUT_PATH" = /* ]] || refuse "PBS stdout path is not absolute"
[[ "$PBS_STDERR_PATH" = /* ]] || refuse "PBS stderr path is not absolute"

"$PYTHON_BIN" - "$REPO_ROOT" <<'PY' || refuse "Pegasus compute site check failed"
import sys

repo = sys.argv[1]
sys.path.insert(0, repo)
from orchestrator.campaign import site_policy

if site_policy.current_site() != site_policy.PEGASUS_COMPUTE:
    raise SystemExit("not Pegasus compute")
PY

for ((WAITED=0; WAITED<60; WAITED++)); do
  [[ -e "$IZANAGI_A1_ACQUISITION_RECEIPT" ]] && break
  sleep 1
done
[[ -e "$IZANAGI_A1_ACQUISITION_RECEIPT" ]] || refuse "acquisition receipt did not appear within 60 seconds"

ACQUISITION_SHA=$("$PYTHON_BIN" - \
  "$IZANAGI_A1_ACQUISITION_RECEIPT" "$REPO_ROOT" "$SUBMISSION_SCHEMA" \
  "$EXPECTED_STUDY_ID" "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" \
  "$IZANAGI_A1_ATTEMPT_ROOT" "$IZANAGI_A1_COMPLETION_RECEIPT" \
  "$POLICY_RELATIVE" "$JOB_RELATIVE" "$PBS_O_HOST" "$PBS_O_WORKDIR" \
  "$PBS_O_QUEUE" "$PBS_STDOUT_PATH" "$PBS_STDERR_PATH" "$EXPECTED_QUEUE" <<'PY'
import hashlib
import json
import os
import pathlib
import re
import stat
import sys

(
    path, repo_raw, schema, study, source, request_id, attempt_raw,
    completion_raw, policy_relative, job_relative, pbs_o_host, pbs_o_workdir,
    pbs_o_queue, pbs_stdout_path, pbs_stderr_path, expected_queue,
) = sys.argv[1:]
receipt_path = pathlib.Path(path)
if not receipt_path.is_absolute() or receipt_path.resolve(strict=True) != receipt_path:
    raise SystemExit("acquisition receipt path is not canonical absolute")
flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(path, flags)
try:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit("acquisition receipt is not regular")
    raw = b""
    while len(raw) < info.st_size:
        block = os.read(fd, info.st_size - len(raw))
        if not block:
            raise SystemExit("acquisition receipt shortened")
        raw += block
    if os.fstat(fd).st_size != info.st_size:
        raise SystemExit("acquisition receipt changed")
finally:
    os.close(fd)

def reject_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value

document = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
if type(document) is not dict or set(document) != {
    "schema_version", "route", "study_id", "source_commit",
    "attempt_root", "request_id", "submission_receipt_path",
    "completion_receipt_path", "qsub_argv", "qsub_options",
    "submit_observation",
}:
    raise SystemExit("submission receipt shape differs")
for key, expected in {
    "schema_version": schema,
    "route": "direct-qsub",
    "study_id": study,
    "source_commit": source,
    "attempt_root": attempt_raw,
    "request_id": request_id,
}.items():
    if document.get(key) != expected:
        raise SystemExit(f"submission receipt identity differs: {key}")
repo = pathlib.Path(repo_raw).resolve(strict=True)
attempt = pathlib.Path(attempt_raw)
if not attempt.is_absolute() or attempt.resolve(strict=False) != attempt:
    raise SystemExit("attempt root is not canonical absolute")
with open(repo / policy_relative, encoding="utf-8") as stream:
    policy = json.load(stream, object_pairs_hook=reject_duplicates)
base_raw = policy.get("execution", {}).get("durable_measurement_base")
if type(base_raw) is not str:
    raise SystemExit("durable measurement base is missing")
base = pathlib.Path(base_raw)
if not base.is_absolute() or base.resolve(strict=False) != base:
    raise SystemExit("durable measurement base is not canonical absolute")
if attempt.parent != base or attempt == base:
    raise SystemExit("attempt root is not one direct durable-base child")
if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", attempt.name) is None:
    raise SystemExit("attempt child name is unsafe")
if os.path.lexists(attempt):
    raise SystemExit("attempt root already exists")
stem = attempt.name
submission = base / f"{stem}.submission.json"
completion = base / f"{stem}.completion.json"
stdout_path = base / f"{stem}.stdout"
stderr_path = base / f"{stem}.stderr"
if receipt_path != submission or pathlib.Path(completion_raw) != completion:
    raise SystemExit("durable receipt topology differs")
variables = {
    "IZANAGI_EXPECTED_HEAD": source,
    "IZANAGI_A1_STUDY_ID": study,
    "IZANAGI_A1_ATTEMPT_ROOT": str(attempt),
    "IZANAGI_A1_ACQUISITION_RECEIPT": str(submission),
    "IZANAGI_A1_COMPLETION_RECEIPT": str(completion),
}
variable_text = ",".join(f"{key}={value}" for key, value in variables.items())
options = {
    "v": variable_text,
    "variables": variables,
    "o": str(stdout_path),
    "e": str(stderr_path),
}
argv = [
    "qsub", "-v", variable_text, "-o", str(stdout_path),
    "-e", str(stderr_path), str((repo / job_relative).resolve(strict=True)),
]
if document.get("submission_receipt_path") != str(submission):
    raise SystemExit("submission receipt path differs")
if document.get("completion_receipt_path") != str(completion):
    raise SystemExit("completion receipt path differs")
if document.get("qsub_argv") != argv or document.get("qsub_options") != options:
    raise SystemExit("canonical qsub request differs")
observation = document.get("submit_observation")
if type(observation) is not dict or set(observation) != {
    "submit_host", "qsub_stdout", "qsub_stdout_sha256", "qsub_stderr",
    "qsub_stderr_sha256", "qstat_visibility",
}:
    raise SystemExit("submit observation shape differs")
if (
    type(observation["submit_host"]) is not str
    or not observation["submit_host"]
    or any(ord(character) < 0x20 for character in observation["submit_host"])
):
    raise SystemExit("submit host observation differs")
if observation["submit_host"] != pbs_o_host:
    raise SystemExit("submit host does not match PBS_O_HOST")
if pbs_o_workdir != str(repo):
    raise SystemExit("PBS_O_WORKDIR does not match repository")
if pbs_o_queue != expected_queue:
    raise SystemExit("PBS_O_QUEUE differs")
if pbs_stdout_path != options["o"] or pbs_stderr_path != options["e"]:
    raise SystemExit("PBS stdout/stderr paths differ from qsub options")
qsub_stdout = f"{request_id}\n"
if observation["qsub_stdout"] != qsub_stdout or observation["qsub_stderr"] != "":
    raise SystemExit("qsub stdout/stderr observation differs")
if observation["qsub_stdout_sha256"] != hashlib.sha256(qsub_stdout.encode()).hexdigest():
    raise SystemExit("qsub stdout hash differs")
if observation["qsub_stderr_sha256"] != hashlib.sha256(b"").hexdigest():
    raise SystemExit("qsub stderr hash differs")
visibility = observation["qstat_visibility"]
if type(visibility) is not dict or set(visibility) != {
    "request_id", "visible", "state", "observed_epoch",
}:
    raise SystemExit("qstat visibility shape differs")
if (
    visibility["request_id"] != request_id
    or visibility["visible"] is not True
    or type(visibility["state"]) is not str
    or re.fullmatch(r"[A-Z]", visibility["state"]) is None
    or type(visibility["observed_epoch"]) is not int
    or visibility["observed_epoch"] <= 0
):
    raise SystemExit("qstat visibility observation differs")
print(hashlib.sha256(raw).hexdigest())
PY
) || refuse "acquisition receipt validation failed"
[[ "$ACQUISITION_SHA" =~ ^[0-9a-f]{64}$ ]] || refuse "acquisition receipt SHA is invalid"

ATTEMPT_ROOT="$IZANAGI_A1_ATTEMPT_ROOT"
RAW_ROOT="$ATTEMPT_ROOT/raw"
CACHE_ROOT="$ATTEMPT_ROOT/cache"
OUTPUT_ROOT="$RAW_ROOT/campaign-output"
RESULT_ROOT="$RAW_ROOT/results"
TMP_ROOT="$RAW_ROOT/tmp"
if ! mkdir -- "$ATTEMPT_ROOT"; then
  refuse "attempt root cannot be exclusive-created"
fi
if ! mkdir -- "$RAW_ROOT"; then
  refuse "raw root cannot be exclusive-created"
fi
if ! mkdir -- "$TMP_ROOT"; then
  refuse "temporary root cannot be exclusive-created"
fi
export TMPDIR="$TMP_ROOT"
export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"
DRIVER_RC=125
TERMINAL_PATH="$RAW_ROOT/job-terminal.json"

write_terminal() {
  local shell_rc=$1
  [[ ! -e "$TERMINAL_PATH" ]] || return 66
  "$PYTHON_BIN" - "$TERMINAL_PATH" "$REPO_ROOT" "$EXPECTED_STUDY_ID" \
  "$PBS_JOBID" "$IZANAGI_EXPECTED_HEAD" "$DRIVER_RC" "$shell_rc" \
    "$RESULT_ROOT" "$IZANAGI_A1_ACQUISITION_RECEIPT" "$ACQUISITION_SHA" \
    "$IZANAGI_A1_COMPLETION_RECEIPT" "$ATTEMPT_ROOT" \
    "$PBS_O_HOST" "$PBS_O_WORKDIR" "$PBS_O_QUEUE" \
    "$PBS_STDOUT_PATH" "$PBS_STDERR_PATH" \
    "$DRIVER_RELATIVE" "$POLICY_RELATIVE" "$PIPELINE_RELATIVE" "$JOB_RELATIVE" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
import time

(
    path, repo, study_id, pbs_jobid, expected_head, driver_rc_raw,
    shell_rc_raw, result_root, acquisition_path, acquisition_sha,
    completion_path, attempt_root, pbs_o_host, pbs_o_workdir, pbs_o_queue,
    pbs_stdout_path, pbs_stderr_path, *source_paths,
) = sys.argv[1:]
driver_rc = int(driver_rc_raw)
shell_rc = int(shell_rc_raw)

def digest(candidate):
    if not os.path.isfile(candidate):
        return None
    value = hashlib.sha256()
    with open(candidate, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def git(*args):
    proc = subprocess.run(
        ["git", "-C", repo, *args], text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise SystemExit(f"terminal git check failed: {' '.join(args)}")
    return proc.stdout.strip()

observed_head = git("rev-parse", "HEAD")
porcelain = git("status", "--porcelain", "--untracked-files=all")
files = {}
for relative in source_paths:
    files[relative] = {
        "git_blob_oid": git("rev-parse", f"{expected_head}:{relative}"),
        "working_sha256": digest(os.path.join(repo, relative)),
    }
source_binding = {
    "measurement_source_commit": expected_head,
    "files": files,
    "evidence_level": "source-routed-trace0",
    "artifact_standalone_proof": False,
}
result_path = os.path.join(result_root, "result.json")
receipt_path = os.path.join(result_root, "receipt.json")
result_sha = digest(result_path)
receipt_sha = digest(receipt_path)
terminal_acquisition_sha = digest(acquisition_path)
attempt_info = os.stat(attempt_root, follow_symlinks=False)
if not stat.S_ISDIR(attempt_info.st_mode):
    raise SystemExit("terminal attempt root is not a real directory")
source_ok = observed_head == expected_head and porcelain == ""
success = all((
    driver_rc == 0,
    shell_rc == 0,
    result_sha is not None,
    receipt_sha is not None,
    terminal_acquisition_sha == acquisition_sha,
    source_ok,
))
document = {
    "schema_version": "paper-story-a1-paired-job-terminal/v2",
    "study_id": study_id,
    "pbs_jobid": pbs_jobid,
    "expected_head": expected_head,
    "observed_head": observed_head,
    "porcelain": porcelain,
    "driver_rc": driver_rc,
    "shell_rc": shell_rc,
    "status": "finished" if success else "failed",
    "result_sha256": result_sha,
    "receipt_sha256": receipt_sha,
    "submission_receipt_sha256": terminal_acquisition_sha,
    "completion_receipt_path": completion_path,
    "pbs_observation": {
        "pbs_jobid": pbs_jobid,
        "pbs_o_host": pbs_o_host,
        "pbs_o_workdir": pbs_o_workdir,
        "pbs_o_queue": pbs_o_queue,
        "stdout_path": pbs_stdout_path,
        "stderr_path": pbs_stderr_path,
    },
    "attempt_identity": {
        "st_dev": attempt_info.st_dev,
        "st_ino": attempt_info.st_ino,
    },
    "terminal_source_binding": source_binding,
    "recorded_epoch": int(time.time()),
}
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(path, flags, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
raise SystemExit(0 if success or driver_rc != 0 or shell_rc != 0 else 3)
PY
}

on_exit() {
  local shell_rc=$?
  local writer_rc
  trap - EXIT
  set +e
  write_terminal "$shell_rc"
  writer_rc=$?
  set -e
  if [[ "$writer_rc" -ne 0 ]]; then
    exit 70
  fi
  exit "$shell_rc"
}
trap on_exit EXIT

set +e
"$PYTHON_BIN" "$REPO_ROOT/$DRIVER_RELATIVE" measure \
  --study-id "$EXPECTED_STUDY_ID" \
  --expected-head "$IZANAGI_EXPECTED_HEAD" \
  --pbs-jobid "$PBS_JOBID" \
  --acquisition-receipt "$IZANAGI_A1_ACQUISITION_RECEIPT" \
  --acquisition-receipt-sha256 "$ACQUISITION_SHA" \
  --output-root "$OUTPUT_ROOT" \
  --cache-root "$CACHE_ROOT" \
  --result-root "$RESULT_ROOT"
DRIVER_RC=$?
set -e
exit "$DRIVER_RC"
