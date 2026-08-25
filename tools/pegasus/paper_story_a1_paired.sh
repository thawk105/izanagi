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

EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"
EXPECTED_QUEUE="gen_S"
SUBMISSION_SCHEMA="paper-story-a1-paired-submission/v1"
DRIVER_RELATIVE="orchestrator/campaign/paper_story_a1_paired.py"
POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v2.json"
PIPELINE_RELATIVE="orchestrator/campaign/pipeline.py"
JOB_RELATIVE="tools/pegasus/paper_story_a1_paired.sh"
PEGASUS_POLICY_RELATIVE="tools/pegasus/policy.json"

refuse() {
  printf 'paper-story A-1 job refused: %s\n' "$1" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" ]] || refuse "PBS_JOBID is required"
[[ "$PBS_JOBID" =~ ^(0:)?[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || refuse "unsafe PBS_JOBID"
[[ -n "${PBS_O_HOST:-}" ]] || refuse "PBS_O_HOST is required"
[[ -n "${PBS_O_WORKDIR:-}" ]] || refuse "PBS_O_WORKDIR is required"
[[ "${IZANAGI_A1_STUDY_ID:-}" == "$EXPECTED_STUDY_ID" ]] || refuse "study ID differs"
[[ "${IZANAGI_EXPECTED_HEAD:-}" =~ ^[0-9a-f]{40}$ ]] || refuse "expected HEAD is invalid"
[[ -n "${IZANAGI_A1_ATTEMPT_ROOT:-}" ]] || refuse "attempt root is required"
[[ -n "${IZANAGI_A1_ACQUISITION_RECEIPT:-}" ]] || refuse "acquisition receipt is required"
[[ -n "${IZANAGI_A1_COMPLETION_RECEIPT:-}" ]] || refuse "completion receipt is required"
[[ -n "${IZANAGI_SUBMISSION_NONCE:-}" ]] || refuse "submission nonce is required"
[[ "$IZANAGI_SUBMISSION_NONCE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || \
  refuse "submission nonce is unsafe"
# The calibration job's dependency staging uses /scr. Preserve that compute
# path, and retain the incoming TMPDIR only as the fallback when /scr is absent.
DEPENDENCY_SCRATCH_PARENT=/scr
if [[ ! -d "$DEPENDENCY_SCRATCH_PARENT" ]]; then
  DEPENDENCY_SCRATCH_PARENT=${TMPDIR:-}
fi
[[ "$IZANAGI_A1_ATTEMPT_ROOT" = /* ]] || refuse "attempt root must be absolute"
[[ "$IZANAGI_A1_ACQUISITION_RECEIPT" = /* ]] || refuse "acquisition receipt must be absolute"
[[ "$IZANAGI_A1_COMPLETION_RECEIPT" = /* ]] || refuse "completion receipt must be absolute"

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -f "$REPO_ROOT/$DRIVER_RELATIVE" ]] || refuse "tracked driver is missing"
[[ -f "$REPO_ROOT/$POLICY_RELATIVE" ]] || refuse "tracked policy is missing"
[[ -f "$REPO_ROOT/$JOB_RELATIVE" ]] || refuse "tracked job body is missing"
[[ -f "$REPO_ROOT/$PEGASUS_POLICY_RELATIVE" ]] || refuse "Pegasus policy is missing"
CURRENT_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD) || refuse "cannot resolve HEAD"
[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]] || refuse "HEAD mismatch"
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] || \
  refuse "working tree is dirty"
CURRENT_SCRIPT_SHA=$(sha256sum "$REPO_ROOT/$JOB_RELATIVE" | awk '{print $1}') || \
  refuse "cannot hash tracked job body"
[[ "$CURRENT_SCRIPT_SHA" =~ ^[0-9a-f]{64}$ ]] || refuse "tracked job body SHA is invalid"
ATTEMPT_CHILD=${IZANAGI_A1_ATTEMPT_ROOT##*/}
[[ "$IZANAGI_SUBMISSION_NONCE" == "$ATTEMPT_CHILD" ]] || \
  refuse "submission nonce differs from attempt child"

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
  "$EXPECTED_QUEUE" <<'PY'
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
    expected_queue,
) = sys.argv[1:]
repo = pathlib.Path(repo_raw).resolve(strict=True)
sys.path.insert(0, os.fspath(repo))
from orchestrator.campaign.paper_story_a1_paired import NQSV_QSTAT_STATES

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

request_pattern = re.compile(r"Request\s+(\S+)\s+submitted")
normalized_pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

def normalize_request_id(value):
    if type(value) is not str:
        raise SystemExit("request ID is not a string")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise SystemExit("request ID is empty")
    if normalized_pattern.fullmatch(normalized) is None:
        raise SystemExit("request ID is unsafe")
    return normalized

def parse_request_id(stdout):
    if type(stdout) is not str:
        raise SystemExit("qsub stdout is not a string")
    match = request_pattern.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise SystemExit("qsub stdout does not contain one request ID")

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
}.items():
    if document.get(key) != expected:
        raise SystemExit(f"submission receipt identity differs: {key}")
receipt_request_id = document.get("request_id")
if normalize_request_id(receipt_request_id) != normalize_request_id(request_id):
    raise SystemExit("submission receipt request ID differs from PBS_JOBID")
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
    "IZANAGI_SUBMISSION_NONCE": attempt.name,
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
qsub_stdout = observation["qsub_stdout"]
if observation["qsub_stderr"] != "":
    raise SystemExit("qsub stdout/stderr observation differs")
if normalize_request_id(parse_request_id(qsub_stdout)) != normalize_request_id(
    receipt_request_id
):
    raise SystemExit("qsub stdout request ID differs")
if observation["qsub_stdout_sha256"] != hashlib.sha256(qsub_stdout.encode()).hexdigest():
    raise SystemExit("qsub stdout hash differs")
if observation["qsub_stderr_sha256"] != hashlib.sha256(b"").hexdigest():
    raise SystemExit("qsub stderr hash differs")
visibility = observation["qstat_visibility"]
if type(visibility) is not dict or set(visibility) != {
    "request_id", "visible", "state", "queue", "observed_epoch",
}:
    raise SystemExit("qstat visibility shape differs")
if (
    visibility["visible"] is not True
    or type(visibility["state"]) is not str
    or visibility["state"] not in NQSV_QSTAT_STATES
    or visibility["queue"] != expected_queue
    or type(visibility["observed_epoch"]) is not int
    or visibility["observed_epoch"] <= 0
):
    raise SystemExit("qstat visibility observation differs")
if normalize_request_id(visibility["request_id"]) != normalize_request_id(
    receipt_request_id
):
    raise SystemExit("qstat visibility request ID differs")
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

readarray -t REQUESTED_WALLTIMES < <(
  sed -n -E \
    's/^#PBS[[:space:]]+-l[[:space:]]+elapstim_req=([0-9]{2}:[0-9]{2}:[0-9]{2})[[:space:]]*$/\1/p' \
    "$REPO_ROOT/$JOB_RELATIVE"
)
[[ ${#REQUESTED_WALLTIMES[@]} -eq 1 ]] || \
  refuse "job body must declare exactly one HH:MM:SS elapstim_req"
IFS=: read -r REQUESTED_HOURS REQUESTED_MINUTES REQUESTED_SECONDS \
  <<< "${REQUESTED_WALLTIMES[0]}"
((10#$REQUESTED_MINUTES < 60 && 10#$REQUESTED_SECONDS < 60)) || \
  refuse "job body elapstim_req minute/second is invalid"
REQUESTED_S=$((
  10#$REQUESTED_HOURS * 3600
  + 10#$REQUESTED_MINUTES * 60
  + 10#$REQUESTED_SECONDS
))
((REQUESTED_S > 0)) || refuse "job body elapstim_req must be positive"

qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$RAW_ROOT/qstat-f.stdout" \
  2>"$RAW_ROOT/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$RAW_ROOT/qstat-f.rc"
HOSTNAME_SHORT=$(hostname) || refuse "cannot observe hostname"
HOSTNAME_FQDN=$(hostname -f) || refuse "cannot observe hostname -f"
readarray -t qstat_values < <("$PYTHON_BIN" - \
  "$RAW_ROOT/qstat-f.stdout" "$HOSTNAME_SHORT" "$qstat_rc" <<'PY'
import re
import subprocess
import sys

path, observed, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
if rc == "0":
    for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
        if match:
            raw = match.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    if assigned == "unavailable":
        match = re.search(
            r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
            text,
        )
        if match and match.group(1).lower() != "none":
            assigned = match.group(1)
    if assigned == "unavailable" and observed.split(".")[0] in text:
        assigned = observed.split(".")[0]
    for key in ("stime", "start_time", "start", "Started Request Time"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = raw
            break
        parsed = subprocess.run(
            ["date", "-d", raw, "+%s"], capture_output=True, text=True
        )
        if parsed.returncode == 0 and parsed.stdout.strip().isdigit():
            started = parsed.stdout.strip()
            break
print(assigned)
print(started)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable \
      || "$SCHEDULER_STARTED_EPOCH" == unavailable ]]; then
  refuse "qstat allocation/start binding unavailable"
fi
if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]; then
  RESERVATION_HOST="$HOSTNAME_SHORT"
elif [[ "$ASSIGNED_HOST" == "$HOSTNAME_FQDN" ]]; then
  RESERVATION_HOST="$HOSTNAME_FQDN"
else
  refuse "qstat assigned host has no exact hostname/hostname-f observation"
fi
BOOT_ID=$(< /proc/sys/kernel/random/boot_id) || refuse "cannot read boot ID"
[[ -n "$BOOT_ID" ]] || refuse "boot ID is empty"
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$RESERVATION_HOST"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$CURRENT_SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"

DRIVER_RC=125
TERMINAL_PATH="$RAW_ROOT/job-terminal.json"
DEPENDENCY_ROOT=""
DEPENDENCY_ROOT_OWNED=0

write_terminal() {
  local shell_rc=$1
  [[ ! -e "$TERMINAL_PATH" ]] || return 66
  IZANAGI_A1_TERMINAL_DRIVER_RELATIVE="$DRIVER_RELATIVE" \
  IZANAGI_A1_TERMINAL_POLICY_RELATIVE="$POLICY_RELATIVE" \
  IZANAGI_A1_TERMINAL_PIPELINE_RELATIVE="$PIPELINE_RELATIVE" \
  IZANAGI_A1_TERMINAL_JOB_RELATIVE="$JOB_RELATIVE" \
  "$PYTHON_BIN" - "$TERMINAL_PATH" "$REPO_ROOT" "$EXPECTED_STUDY_ID" \
  "$PBS_JOBID" "$IZANAGI_EXPECTED_HEAD" "$DRIVER_RC" "$shell_rc" \
    "$RESULT_ROOT" "$IZANAGI_A1_ACQUISITION_RECEIPT" "$ACQUISITION_SHA" \
    "$IZANAGI_A1_COMPLETION_RECEIPT" "$ATTEMPT_ROOT" \
    "$PBS_O_HOST" "$PBS_O_WORKDIR" <<'PY'
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
    completion_path, attempt_root, pbs_o_host, pbs_o_workdir,
) = sys.argv[1:]
source_paths = tuple(
    os.environ[key]
    for key in (
        "IZANAGI_A1_TERMINAL_DRIVER_RELATIVE",
        "IZANAGI_A1_TERMINAL_POLICY_RELATIVE",
        "IZANAGI_A1_TERMINAL_PIPELINE_RELATIVE",
        "IZANAGI_A1_TERMINAL_JOB_RELATIVE",
    )
)
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
reservation_keys = (
    "JOB_ID",
    "REQUESTED_S",
    "SCHEDULER_STARTED_EPOCH",
    "DEADLINE_EPOCH",
    "HOST",
    "BOOT_ID",
    "SCRIPT_SHA256",
    "NONCE",
)
reservation_binding = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key]
    for key in reservation_keys
}
reservation_binding["requested_s"] = int(reservation_binding["requested_s"])
for key in ("scheduler_started_epoch", "deadline_epoch"):
    reservation_binding[key] = float(reservation_binding[key])
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
    "schema_version": "paper-story-a1-paired-job-terminal/v3",
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
    },
    "reservation_binding": reservation_binding,
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

cleanup_dependency_root() {
  if [[ "$DEPENDENCY_ROOT_OWNED" -eq 1 ]]; then
    [[ -n "$DEPENDENCY_ROOT" ]] || return 70
    /bin/rm -rf -- "$DEPENDENCY_ROOT"
  fi
}

on_exit() {
  local shell_rc=$?
  local cleanup_rc
  local writer_rc
  trap - EXIT
  set +e
  cleanup_dependency_root
  cleanup_rc=$?
  if [[ "$cleanup_rc" -ne 0 ]]; then
    shell_rc=70
  fi
  write_terminal "$shell_rc"
  writer_rc=$?
  set -e
  if [[ "$writer_rc" -ne 0 ]]; then
    exit 70
  fi
  exit "$shell_rc"
}
trap on_exit EXIT

# The dependency build is disposable node-local staging. The attempt root and
# all evidence remain in the durable base validated above.
DEPENDENCY_EVIDENCE_ROOT="$RAW_ROOT/dependency-staging"
if ! mkdir -- "$DEPENDENCY_EVIDENCE_ROOT"; then
  refuse "dependency evidence root cannot be exclusive-created"
fi
readarray -t DEPENDENCY_POLICY_VALUES < <(
  "$PYTHON_BIN" - "$REPO_ROOT/$PEGASUS_POLICY_RELATIVE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    policy = json.load(stream)
for key in (
    "gflags_source_path",
    "gflags_expected_head",
    "glog_source_path",
    "glog_expected_head",
):
    value = policy[key]
    if type(value) is not str or not value:
        raise SystemExit(f"Pegasus dependency pin is invalid: {key}")
    print(value)
PY
)
[[ ${#DEPENDENCY_POLICY_VALUES[@]} -eq 4 ]] || \
  refuse "Pegasus dependency pins are incomplete"
GFLAGS_SOURCE_PATH=${DEPENDENCY_POLICY_VALUES[0]}
GFLAGS_EXPECTED_HEAD=${DEPENDENCY_POLICY_VALUES[1]}
GLOG_SOURCE_PATH=${DEPENDENCY_POLICY_VALUES[2]}
GLOG_EXPECTED_HEAD=${DEPENDENCY_POLICY_VALUES[3]}
[[ "$GFLAGS_SOURCE_PATH" = /* && "$GLOG_SOURCE_PATH" = /* ]] || \
  refuse "dependency source paths must be absolute"
[[ "$GFLAGS_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  refuse "gflags expected HEAD is invalid"
[[ "$GLOG_EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
  refuse "glog expected HEAD is invalid"

if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  refuse "gflags source path is missing"
fi
gflags_head_rc=0
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-head.stderr") || gflags_head_rc=$?
if [[ "$gflags_head_rc" -ne 0 ]]; then
  refuse "cannot resolve gflags source HEAD"
fi
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  refuse "gflags source HEAD mismatch"
fi
gflags_status_rc=0
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-status.stderr") || gflags_status_rc=$?
if [[ "$gflags_status_rc" -ne 0 ]]; then
  refuse "cannot inspect gflags working tree"
fi
printf '%s' "$GFLAGS_STATUS" >"$DEPENDENCY_EVIDENCE_ROOT/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  refuse "gflags working tree is dirty"
fi

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  refuse "glog source path is missing"
fi
glog_head_rc=0
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-source-head.stderr") || glog_head_rc=$?
if [[ "$glog_head_rc" -ne 0 ]]; then
  refuse "cannot resolve glog source HEAD"
fi
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$DEPENDENCY_EVIDENCE_ROOT/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  refuse "glog source HEAD mismatch"
fi
glog_status_rc=0
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-source-status.stderr") || glog_status_rc=$?
if [[ "$glog_status_rc" -ne 0 ]]; then
  refuse "cannot inspect glog working tree"
fi
printf '%s' "$GLOG_STATUS" >"$DEPENDENCY_EVIDENCE_ROOT/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  refuse "glog working tree is dirty"
fi

[[ -n "$DEPENDENCY_SCRATCH_PARENT" ]] || \
  refuse "dependency scratch parent is unavailable"
[[ "$DEPENDENCY_SCRATCH_PARENT" = /* ]] || \
  refuse "dependency scratch parent must be absolute"
[[ -d "$DEPENDENCY_SCRATCH_PARENT" ]] || \
  refuse "dependency scratch parent is unavailable"
if ! DEPENDENCY_ROOT=$(mktemp -d -- \
  "$DEPENDENCY_SCRATCH_PARENT/${PBS_JOBID//:/_}.${IZANAGI_SUBMISSION_NONCE}.XXXXXXXX"); then
  refuse "dependency scratch root cannot be exclusive-created"
fi
DEPENDENCY_ROOT_OWNED=1
readonly DEPENDENCY_ROOT DEPENDENCY_ROOT_OWNED
CC_PATH=$(command -v gcc) || refuse "gcc is unavailable"
CXX_PATH=$(command -v g++) || refuse "g++ is unavailable"
command -v cmake >/dev/null 2>&1 || refuse "cmake is unavailable"

GFLAGS_BUILD_DIR="$DEPENDENCY_ROOT/gflags-build"
GFLAGS_INSTALL_DIR="$DEPENDENCY_ROOT/gflags-install"
if ! mkdir -- "$GFLAGS_BUILD_DIR"; then
  refuse "cannot create gflags build directory"
fi
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
gflags_rc=0
timeout 60 "${gflags_configure_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-configure.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-configure.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags configure failed"
fi
timeout 60 "${gflags_build_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-build.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-build.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags build failed"
fi
timeout 60 "${gflags_install_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/gflags-install.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/gflags-install.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  refuse "gflags install failed"
fi

GLOG_BUILD_DIR="$DEPENDENCY_ROOT/glog-build"
GLOG_INSTALL_DIR="$DEPENDENCY_ROOT/glog-install"
if ! mkdir -- "$GLOG_BUILD_DIR"; then
  refuse "cannot create glog build directory"
fi
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
glog_rc=0
timeout 120 "${glog_configure_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-configure.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-configure.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog configure failed"
fi
timeout 120 "${glog_build_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-build.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-build.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog build failed"
fi
timeout 120 "${glog_install_argv[@]}" \
  >"$DEPENDENCY_EVIDENCE_ROOT/glog-install.stdout" \
  2>"$DEPENDENCY_EVIDENCE_ROOT/glog-install.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  refuse "glog install failed"
fi
DEPENDENCY_PREFIX="$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"

set +e
"$PYTHON_BIN" "$REPO_ROOT/$DRIVER_RELATIVE" measure \
  --study-id "$EXPECTED_STUDY_ID" \
  --expected-head "$IZANAGI_EXPECTED_HEAD" \
  --pbs-jobid "$PBS_JOBID" \
  --acquisition-receipt "$IZANAGI_A1_ACQUISITION_RECEIPT" \
  --acquisition-receipt-sha256 "$ACQUISITION_SHA" \
  --output-root "$OUTPUT_ROOT" \
  --cache-root "$CACHE_ROOT" \
  --result-root "$RESULT_ROOT" \
  --dependency-prefix "$DEPENDENCY_PREFIX"
DRIVER_RC=$?
set -e
exit "$DRIVER_RC"
