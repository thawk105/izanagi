#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=10:00:00
#PBS -b 1
# 出典: certify_calibration.sh:1-5 @ e9b6f69

# driver required_s                    = 12 * (900 + (8+2) * (5*5 + 120)) = 28200
# driver finalize reserve              =   600
# driver が要求する capacity           = 28800
# job prologue (gflags/glog build・qstat・git・hash) 見積          ≈  900
# driver 定数が hard cap でないことへの余裕 (B-02)                 ≈ 6300
# PBS request                          = 36000  (= 10:00:00, gen_S 上限 86400 の範囲内)
set -Eeuo pipefail
umask 077

# 出典: certify_calibration.sh:15-31 @ e9b6f69
if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

# 出典: certify_calibration.sh:33-44 @ e9b6f69
REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
TOOLS="$REPO_ROOT/tools/pegasus"
POLICY="$TOOLS/policy.json"
OUTPUT_ROOT="$REPO_ROOT/output"
ATTEMPTS_ROOT="$OUTPUT_ROOT/env/pegasus/floor/attempts"
JOB_STAGING_ROOT="$OUTPUT_ROOT/env/pegasus/floor/job-staging"

if [[ ! -d "$OUTPUT_ROOT" || -L "$OUTPUT_ROOT" ]]; then
  echo "repo output root is missing, not a directory, or a symlink" >&2
  exit 2
fi
OUTPUT_ROOT_REAL=$(realpath -e -- "$OUTPUT_ROOT") || exit 2
if [[ "$OUTPUT_ROOT_REAL" != "$OUTPUT_ROOT" ]]; then
  echo "repo output root does not resolve to the fixed output path" >&2
  exit 2
fi

assert_safe_output_path() {
  local target=$1
  local relative
  local current
  local component
  local resolved
  local -a components

  if [[ "$target" != "$OUTPUT_ROOT" && "$target" != "$OUTPUT_ROOT/"* ]]; then
    return 1
  fi
  relative=${target#"$REPO_ROOT"/}
  current="$REPO_ROOT"
  IFS='/' read -r -a components <<<"$relative"
  for component in "${components[@]}"; do
    [[ -n "$component" && "$component" != "." && "$component" != ".." ]] || return 1
    current="$current/$component"
    [[ ! -L "$current" ]] || return 1
  done
  resolved=$(realpath -m -- "$target") || return 1
  [[ "$resolved" == "$OUTPUT_ROOT_REAL" || "$resolved" == "$OUTPUT_ROOT_REAL/"* ]] \
    || return 1
  [[ "$resolved" != "$OUTPUT_ROOT_REAL/s8b-freeze" \
      && "$resolved" != "$OUTPUT_ROOT_REAL/s8b-freeze/"* ]] || return 1
  [[ "$resolved" != "$OUTPUT_ROOT_REAL/campaigns" \
      && "$resolved" != "$OUTPUT_ROOT_REAL/campaigns/"* ]]
}

for staging_path in "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"; do
  if ! assert_safe_output_path "$staging_path"; then
    echo "unsafe output path component or containment: $staging_path" >&2
    exit 2
  fi
done
mkdir -p "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"
for staging_path in "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"; do
  if ! assert_safe_output_path "$staging_path"; then
    echo "unsafe output path after creation: $staging_path" >&2
    exit 2
  fi
done

ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"
if ! assert_safe_output_path "$ATTEMPT_DIR"; then
  echo "unsafe attempt path component or containment: $ATTEMPT_DIR" >&2
  exit 2
fi
if ! mkdir "$ATTEMPT_DIR"; then
  echo "attempt already exists or cannot be created (create-only): $ATTEMPT_DIR" >&2
  exit 2
fi
if ! assert_safe_output_path "$ATTEMPT_DIR"; then
  echo "unsafe attempt path after creation: $ATTEMPT_DIR" >&2
  exit 2
fi
# shell redirections must not truncate a concurrently created record.
set -o noclobber

# 出典: certify_calibration.sh:46-93 @ e9b6f69
failure_written=0
write_failure() {
  local rc=$1
  local stage=$2
  local message=$3
  local writer_rc=0
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    "$PY" -I -B - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" "$message" <<'PY' \
      || writer_rc=$?
import json
import sys
import time

path, job_id, rc, stage, message = sys.argv[1:]
payload = {
    "schema_version": "pegasus-job-failure/v1",
    "pbs_jobid": job_id,
    "rc": int(rc),
    "stage": stage,
    "message": message,
    "recorded_epoch": int(time.time()),
}
try:
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
except FileExistsError:
    pass
PY
    if [[ "$writer_rc" -ne 0 ]]; then
      echo "failure writer failed with rc=$writer_rc (original rc=$rc stage=$stage)" >&2
    fi
  fi
  return 0
}
write_interpreter_failure() {
  local message=$1
  if ! printf 'stage=interpreter\nrc=2\nmessage=%s\n' "$message" \
      >"$ATTEMPT_DIR/failure-interpreter.txt"; then
    echo "cannot write interpreter failure marker: $message" >&2
  fi
}

# 計算ノードは intelpython 既定ロードで python3 が 3.9 に解決され、driver の import 前提
# (dataclass kw_only = Python 3.10+) を満たさない (実測: job 0:873200.nqsv, rc=1)。
# 版数 gate を通る最初の候補だけを採用する。authorization gate ではなく実行前提の束縛。
PY=""
py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if "$py_resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY="$py_resolved"
    break
  fi
  py_rejected+="${py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$PY" ]]; then
  write_interpreter_failure "no python3 >= 3.10 (rejected: ${py_rejected:-none})"
  echo "no python3 >= 3.10 (rejected: ${py_rejected:-none})" >&2
  exit 2
fi

on_err() {
  local rc=$?
  local line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "shell" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR
on_signal() {
  local signal_name=$1
  local signal_number=$2
  local rc=$((128 + signal_number))
  trap - ERR INT TERM HUP
  write_failure "$rc" signal "received $signal_name"
  exit "$rc"
}
trap 'on_signal INT 2' INT
trap 'on_signal TERM 15' TERM
trap 'on_signal HUP 1' HUP

printf '%s\n' "$PY" >"$ATTEMPT_DIR/python3.realpath"
"$PY" -I -B --version >"$ATTEMPT_DIR/python3.version" 2>&1

# 出典: certify_calibration.sh:105-141 @ e9b6f69
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  write_failure 2 policy "policy file missing, not regular, or a symlink"
  exit 2
fi
policy_output=""
policy_rc=0
policy_output=$("$PY" -I -B - "$POLICY" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
text_fields = (
    "project",
    "queue",
    "gflags_source_path",
    "gflags_expected_head",
    "glog_source_path",
    "glog_expected_head",
)
for key in text_fields:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("nodes", "floor_walltime_s"):
    if type(policy.get(key)) is not int or policy[key] <= 0:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(policy["floor_walltime_s"])
print(policy["gflags_source_path"])
print(policy["gflags_expected_head"])
print(policy["glog_source_path"])
print(policy["glog_expected_head"])
PY
) || policy_rc=$?
if [[ "$policy_rc" -ne 0 ]]; then
  write_failure 2 policy "cannot parse required floor policy"
  exit 2
fi
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 8 ]]; then
  write_failure 2 policy "floor policy yielded an unexpected field count"
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
FLOOR_WALLTIME_S=${policy_values[3]}
GFLAGS_SOURCE_PATH=${policy_values[4]}
GFLAGS_EXPECTED_HEAD=${policy_values[5]}
GLOG_SOURCE_PATH=${policy_values[6]}
GLOG_EXPECTED_HEAD=${policy_values[7]}
REQUESTED_S_POLICY=36000
if [[ "$PROJECT" != SFC || "$QUEUE" != gen_S || "$NODES" != 1 \
    || "$FLOOR_WALLTIME_S" != "$REQUESTED_S_POLICY" ]]; then
  write_failure 2 policy "floor policy does not match the fixed PBS request"
  exit 2
fi

# 出典: certify_calibration.sh:143-172 @ e9b6f69
if [[ -z "${IZANAGI_SUBMISSION_NONCE:-}" \
    || ! "$IZANAGI_SUBMISSION_NONCE" =~ ^[0-9a-f]{32}$ ]]; then
  write_failure 2 submit_binding "IZANAGI_SUBMISSION_NONCE must be 32 lowercase hex"
  exit 2
fi
SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE"
SUBMIT_SOURCE="$SUBMISSION_DIR/submit-receipt.json"
for ((receipt_wait=0; receipt_wait<60; receipt_wait++)); do
  if [[ -e "$SUBMISSION_DIR" || -L "$SUBMISSION_DIR" ]]; then
    if ! assert_safe_output_path "$SUBMISSION_DIR"; then
      write_failure 2 submit_binding "unsafe submission path component or containment"
      exit 2
    fi
  fi
  if [[ -L "$SUBMIT_SOURCE" ]]; then
    write_failure 2 submit_binding "submit receipt must not be a symlink"
    exit 2
  fi
  if [[ -e "$SUBMIT_SOURCE" && ! -f "$SUBMIT_SOURCE" ]]; then
    write_failure 2 submit_binding "submit receipt must be a regular file"
    exit 2
  fi
  [[ -f "$SUBMIT_SOURCE" ]] && break
  sleep 1
done
if [[ ! -f "$SUBMIT_SOURCE" || -L "$SUBMIT_SOURCE" ]]; then
  write_failure 2 submit_binding "submit receipt did not appear as a regular file within 60 seconds"
  exit 2
fi
if ! assert_safe_output_path "$SUBMIT_SOURCE"; then
  write_failure 2 submit_binding "unsafe submit receipt path component or containment"
  exit 2
fi
copy_rc=0
"$PY" -I -B - "$SUBMIT_SOURCE" "$ATTEMPT_DIR/submit-receipt.json" <<'PY' || copy_rc=$?
import os
import shutil
import stat
import sys

source, destination = sys.argv[1:]
flags = os.O_RDONLY
if hasattr(os, "O_NOFOLLOW"):
    flags |= os.O_NOFOLLOW
fd = os.open(source, flags)
try:
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        raise SystemExit("submit receipt is not a regular file")
    with os.fdopen(fd, "rb", closefd=False) as source_handle:
        with open(destination, "xb") as destination_handle:
            shutil.copyfileobj(source_handle, destination_handle)
finally:
    os.close(fd)
PY
if [[ "$copy_rc" -ne 0 ]]; then
  write_failure 2 submit_binding "cannot copy submit receipt create-only"
  exit 2
fi

receipt_rc=0
"$PY" -I -B - "$ATTEMPT_DIR/submit-receipt.json" "$IZANAGI_SUBMISSION_NONCE" \
  "$PBS_JOBID" "$PROJECT" "$QUEUE" "$NODES" "$REQUESTED_S_POLICY" "$REPO_ROOT" <<'PY' \
  || receipt_rc=$?
import json
import re
import sys

(path, nonce, job_id, project, queue, nodes, requested_s, repo_root) = sys.argv[1:]
sys.path.insert(0, repo_root + "/orchestrator")
from calibrator.schema_v2 import normalize_request_id

def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

with open(path, encoding="utf-8") as handle:
    document = json.load(handle, object_pairs_hook=reject_duplicates)

top_keys = {
    "schema_version",
    "source_commit",
    "job_script_path",
    "job_script_sha256",
    "job_id",
    "nonce",
    "submitted_at",
    "request",
    "preflight",
    "dry_run",
}
if type(document) is not dict or set(document) != top_keys:
    raise SystemExit("submit receipt top-level key set mismatch")
if document["schema_version"] != "pegasus-floor-submit-receipt/v1":
    raise SystemExit("submit receipt schema mismatch")
if document["dry_run"] is not False:
    raise SystemExit("dry-run receipt is not valid for a PBS job")
if document["nonce"] != nonce or re.fullmatch(r"[0-9a-f]{32}", document["nonce"]) is None:
    raise SystemExit("submit receipt nonce mismatch")
if type(document["submitted_at"]) is not int or document["submitted_at"] <= 0:
    raise SystemExit("submit receipt submitted_at is invalid")
if type(document["job_id"]) is not str or not document["job_id"]:
    raise SystemExit("submit receipt job_id is invalid")
if normalize_request_id(document["job_id"]) != normalize_request_id(job_id):
    raise SystemExit("submit receipt job_id does not match PBS_JOBID")
if document["job_script_path"] != "tools/pegasus/floor_campaign.sh":
    raise SystemExit("submit receipt job script path mismatch")
if type(document["source_commit"]) is not str or re.fullmatch(
    r"[0-9a-f]{40}", document["source_commit"]
) is None:
    raise SystemExit("submit receipt source commit is invalid")
if type(document["job_script_sha256"]) is not str or re.fullmatch(
    r"[0-9a-f]{64}", document["job_script_sha256"]
) is None:
    raise SystemExit("submit receipt script hash is invalid")

request = document["request"]
if type(request) is not dict or set(request) != {
    "project", "queue", "nodes", "elapstim_req_s"
}:
    raise SystemExit("submit receipt request key set mismatch")
if type(request["project"]) is not str or request["project"] != project:
    raise SystemExit("submit receipt project mismatch")
if type(request["queue"]) is not str or request["queue"] != queue:
    raise SystemExit("submit receipt queue mismatch")
if type(request["nodes"]) is not int or request["nodes"] != int(nodes):
    raise SystemExit("submit receipt nodes mismatch")
if type(request["elapstim_req_s"]) is not int or request["elapstim_req_s"] != int(requested_s):
    raise SystemExit("submit receipt walltime mismatch")

preflight = document["preflight"]
preflight_keys = {"qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"}
if type(preflight) is not dict or set(preflight) != preflight_keys:
    raise SystemExit("submit receipt preflight key set mismatch")
for name, capture in preflight.items():
    if type(capture) is not dict or set(capture) != {"rc", "stdout_raw", "stderr_raw"}:
        raise SystemExit(f"submit receipt preflight capture mismatch: {name}")
    if type(capture["rc"]) is not int:
        raise SystemExit(f"submit receipt preflight rc is invalid: {name}")
    if type(capture["stdout_raw"]) is not str or type(capture["stderr_raw"]) is not str:
        raise SystemExit(f"submit receipt preflight raw capture is invalid: {name}")
PY
if [[ "$receipt_rc" -ne 0 ]]; then
  write_failure 2 submit_binding "submit receipt failed strict validation"
  exit 2
fi

# 出典: certify_calibration.sh:174-208 @ e9b6f69
SCRIPT_RELATIVE_PATH="tools/pegasus/floor_campaign.sh"
REPO_SCRIPT="$REPO_ROOT/$SCRIPT_RELATIVE_PATH"
if [[ ! -f "$REPO_SCRIPT" || -L "$REPO_SCRIPT" ]]; then
  write_failure 2 source_identity "repo job script is not a non-symlink regular file"
  exit 2
fi
if ! git -C "$REPO_ROOT" ls-files --error-unmatch -- "$SCRIPT_RELATIVE_PATH" >/dev/null; then
  write_failure 2 source_identity "repo job script is not tracked"
  exit 2
fi

EXECUTING_SCRIPT_SHA256=$(sha256sum "$0" | awk '{print $1}')
if [[ ! "$EXECUTING_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  write_failure 2 source_identity "cannot hash executing job script bytes"
  exit 2
fi
RECEIPT_SCRIPT_SHA256=$("$PY" -I -B - "$ATTEMPT_DIR/submit-receipt.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["job_script_sha256"])
PY
)
if [[ "$EXECUTING_SCRIPT_SHA256" != "$RECEIPT_SCRIPT_SHA256" ]]; then
  write_failure 2 source_identity "executing job script hash differs from submit receipt"
  exit 2
fi

CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD)
if [[ ! "$CURRENT_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  write_failure 2 source_identity "current source commit is not lowercase 40 hex"
  exit 2
fi
RECEIPT_SOURCE_COMMIT=$("$PY" -I -B - "$ATTEMPT_DIR/submit-receipt.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["source_commit"])
PY
)
if [[ "$CURRENT_COMMIT" != "$RECEIPT_SOURCE_COMMIT" ]]; then
  write_failure 2 source_identity "current source commit differs from submit receipt"
  exit 2
fi

REPO_BLOB_PATH="$TMPDIR/floor_campaign.commit-blob"
git_cat_file_rc=0
git -C "$REPO_ROOT" cat-file blob "$CURRENT_COMMIT:$SCRIPT_RELATIVE_PATH" \
  >"$REPO_BLOB_PATH" || git_cat_file_rc=$?
if [[ "$git_cat_file_rc" -ne 0 ]]; then
  write_failure "$git_cat_file_rc" source_identity "cannot read committed job script blob"
  exit "$git_cat_file_rc"
fi
JOB_SCRIPT_SHA256=$(sha256sum "$REPO_BLOB_PATH" | awk '{print $1}')
if [[ ! "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  write_failure 2 source_identity "cannot hash committed job script blob"
  exit 2
fi
if [[ "$JOB_SCRIPT_SHA256" != "$RECEIPT_SCRIPT_SHA256" ]]; then
  write_failure 2 source_identity "repo job script blob hash differs from submit receipt"
  exit 2
fi

repo_status_rc=0
REPO_STATUS=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all \
  -- . ':(exclude)output') || repo_status_rc=$?
if [[ "$repo_status_rc" -ne 0 ]]; then
  write_failure "$repo_status_rc" source_identity "cannot inspect repo working tree"
  exit "$repo_status_rc"
fi
if [[ -n "$REPO_STATUS" ]]; then
  write_failure 2 source_identity "tracked source or non-output untracked content is dirty"
  exit 2
fi

# 出典: certify_calibration.sh:210-318 @ e9b6f69
qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-f.stdout" \
  2>"$ATTEMPT_DIR/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$ATTEMPT_DIR/qstat-f.rc"
HOSTNAME_SHORT=$(hostname)
HOSTNAME_FQDN=$(hostname -f)
printf '%s\n' "$HOSTNAME_SHORT" >"$ATTEMPT_DIR/hostname.stdout"
printf '%s\n' "$HOSTNAME_FQDN" >"$ATTEMPT_DIR/hostname-f.stdout"

qstat_parse_rc=0
qstat_output=$("$PY" -I -B - "$ATTEMPT_DIR/qstat-f.stdout" "$qstat_rc" <<'PY'
import re
import subprocess
import sys

path, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
limit_s = "unavailable"
remaining_s = "unavailable"
if rc == "0":
    section = re.search(
        r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
        text,
    )
    if section and section.group(1).lower() != "none":
        assigned = section.group(1)
    if assigned == "unavailable":
        for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
            match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
            if not match:
                continue
            raw = match.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    for key in ("Started Request Time", "stime", "start_time", "start"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = str(int(raw))
            break
        process = subprocess.run(
            ["date", "-d", raw, "+%s"], capture_output=True, text=True
        )
        if process.returncode == 0 and process.stdout.strip().isdigit():
            started = str(int(process.stdout.strip()))
            break
    limits = re.findall(
        r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)",
        text,
    )
    if len(limits) == 1 and int(limits[0]) > 0:
        limit_s = str(int(limits[0]))
    remaining = re.findall(
        r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$",
        text,
    )
    if len(remaining) == 1:
        remaining_s = str(int(remaining[0]))
print(assigned)
print(started)
print(limit_s)
print(remaining_s)
PY
) || qstat_parse_rc=$?
if [[ "$qstat_parse_rc" -ne 0 ]]; then
  write_failure 2 allocation "qstat output parser failed"
  exit 2
fi
readarray -t qstat_values <<<"$qstat_output"
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
SCHEDULER_ELAPSE_LIMIT_S=${qstat_values[2]:-unavailable}
SCHEDULER_REMAINING_ELAPSE_S=${qstat_values[3]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable \
    || "$SCHEDULER_STARTED_EPOCH" == unavailable \
    || "$SCHEDULER_ELAPSE_LIMIT_S" == unavailable \
    || "$SCHEDULER_REMAINING_ELAPSE_S" == unavailable ]]; then
  "$PY" -I -B - "$ATTEMPT_DIR/allocation-unavailable.json" "$PBS_JOBID" "$qstat_rc" \
    "$ASSIGNED_HOST" "$SCHEDULER_STARTED_EPOCH" "$SCHEDULER_ELAPSE_LIMIT_S" \
    "$SCHEDULER_REMAINING_ELAPSE_S" <<'PY'
import json
import sys
import time

path, job, rc, assigned, started, limit_s, remaining_s = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "pbs_jobid": job,
            "qstat_rc": int(rc),
            "assigned_host_qstat": assigned,
            "scheduler_started_epoch": started,
            "scheduler_elapse_limit_s": limit_s,
            "scheduler_remaining_elapse_s": remaining_s,
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  write_failure 2 allocation "qstat allocation/start/elapse binding unavailable"
  exit 2
fi

"$PY" -I -B - "$ATTEMPT_DIR/scheduler-elapse.json" "$PBS_JOBID" \
  "$SCHEDULER_ELAPSE_LIMIT_S" "$SCHEDULER_REMAINING_ELAPSE_S" \
  "$REQUESTED_S_POLICY" <<'PY'
import json
import sys
import time

path, job, limit_s, remaining_s, policy_s = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "pbs_jobid": job,
            "scheduler_elapse_limit_s": int(limit_s),
            "scheduler_remaining_elapse_s": int(remaining_s),
            "policy_floor_walltime_s": int(policy_s),
            "policy_match": int(limit_s) == int(policy_s),
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
if [[ "$SCHEDULER_ELAPSE_LIMIT_S" -ne "$REQUESTED_S_POLICY" ]]; then
  write_failure 2 allocation "scheduler Elapse Time Limit differs from floor policy"
  exit 2
fi
if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]; then
  HOSTNAME_OBSERVED="$HOSTNAME_SHORT"
elif [[ "$ASSIGNED_HOST" == "$HOSTNAME_FQDN" ]]; then
  HOSTNAME_OBSERVED="$HOSTNAME_FQDN"
else
  write_failure 2 allocation "qstat assigned host has no exact hostname/hostname-f observation"
  exit 2
fi

# 出典: certify_calibration.sh:320-340 @ e9b6f69
REQUESTED_S="$SCHEDULER_ELAPSE_LIMIT_S"
BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
if [[ -z "$BOOT_ID" ]]; then
  write_failure 2 reservation "boot ID is unavailable"
  exit 2
fi
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$HOSTNAME_OBSERVED"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$JOB_SCRIPT_SHA256"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"
"$PY" -I -B - "$ATTEMPT_DIR/reservation.json" <<'PY'
import json
import os
import sys
import time

keys = (
    "JOB_ID",
    "REQUESTED_S",
    "SCHEDULER_STARTED_EPOCH",
    "DEADLINE_EPOCH",
    "HOST",
    "BOOT_ID",
    "SCRIPT_SHA256",
    "NONCE",
)
payload = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key]
    for key in keys
}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    payload[key] = int(payload[key])
payload["recorded_epoch"] = int(time.time())
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

# 出典: certify_calibration.sh:347-357 @ e9b6f69
CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
CMAKE_PATH=$(command -v cmake)
realpath -e "$CC_PATH" >"$ATTEMPT_DIR/compiler.path"
realpath -e "$CXX_PATH" >"$ATTEMPT_DIR/cxx.path"
realpath -e "$CMAKE_PATH" >"$ATTEMPT_DIR/cmake.path"
"$CC_PATH" --version >"$ATTEMPT_DIR/compiler.version" 2>&1
"$CXX_PATH" --version >"$ATTEMPT_DIR/cxx.version" 2>&1
"$CMAKE_PATH" --version >"$ATTEMPT_DIR/cmake.version" 2>&1

# 出典: certify_calibration.sh:376-510 @ e9b6f69
if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  write_failure 2 gflags "gflags source path missing"
  exit 2
fi
gflags_head_rc=0
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD \
  2>"$ATTEMPT_DIR/gflags-source-head.stderr") || gflags_head_rc=$?
if [[ "$gflags_head_rc" -ne 0 ]]; then
  write_failure "$gflags_head_rc" gflags "cannot resolve gflags source HEAD"
  exit "$gflags_head_rc"
fi
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$ATTEMPT_DIR/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  write_failure 2 gflags "gflags source HEAD mismatch"
  exit 2
fi
gflags_status_rc=0
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$ATTEMPT_DIR/gflags-source-status.stderr") || gflags_status_rc=$?
if [[ "$gflags_status_rc" -ne 0 ]]; then
  write_failure "$gflags_status_rc" gflags "cannot inspect gflags working tree"
  exit "$gflags_status_rc"
fi
printf '%s' "$GFLAGS_STATUS" >"$ATTEMPT_DIR/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  write_failure 2 gflags "gflags working tree is dirty"
  exit 2
fi

GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
gflags_rc=0
mkdir "$GFLAGS_BUILD_DIR" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "cannot create gflags build directory"
  exit "$gflags_rc"
fi
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-configure.stdout" \
  2>"$ATTEMPT_DIR/gflags-configure.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags configure failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_build_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-build.stdout" \
  2>"$ATTEMPT_DIR/gflags-build.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags build failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_install_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-install.stdout" \
  2>"$ATTEMPT_DIR/gflags-install.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags install failed"
  exit "$gflags_rc"
fi

# 出典: certify_calibration.sh:423-486 @ e9b6f69
if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  write_failure 2 glog "glog source path missing"
  exit 2
fi
glog_head_rc=0
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD \
  2>"$ATTEMPT_DIR/glog-source-head.stderr") || glog_head_rc=$?
if [[ "$glog_head_rc" -ne 0 ]]; then
  write_failure "$glog_head_rc" glog "cannot resolve glog source HEAD"
  exit "$glog_head_rc"
fi
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$ATTEMPT_DIR/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  write_failure 2 glog "glog source HEAD mismatch"
  exit 2
fi
glog_status_rc=0
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$ATTEMPT_DIR/glog-source-status.stderr") || glog_status_rc=$?
if [[ "$glog_status_rc" -ne 0 ]]; then
  write_failure "$glog_status_rc" glog "cannot inspect glog working tree"
  exit "$glog_status_rc"
fi
printf '%s' "$GLOG_STATUS" >"$ATTEMPT_DIR/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  write_failure 2 glog "glog working tree is dirty"
  exit 2
fi

GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
glog_rc=0
mkdir "$GLOG_BUILD_DIR" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "cannot create glog build directory"
  exit "$glog_rc"
fi
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
timeout 120 "${glog_configure_argv[@]}" \
  >"$ATTEMPT_DIR/glog-configure.stdout" \
  2>"$ATTEMPT_DIR/glog-configure.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog configure failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_build_argv[@]}" \
  >"$ATTEMPT_DIR/glog-build.stdout" \
  2>"$ATTEMPT_DIR/glog-build.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog build failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_install_argv[@]}" \
  >"$ATTEMPT_DIR/glog-install.stdout" \
  2>"$ATTEMPT_DIR/glog-install.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog install failed"
  exit "$glog_rc"
fi

CMAKE_PREFIX_PATH_PREVIOUSLY_SET=false
CMAKE_PREFIX_PATH_PREVIOUS_VALUE=""
if [[ ${CMAKE_PREFIX_PATH+x} ]]; then
  CMAKE_PREFIX_PATH_PREVIOUSLY_SET=true
  CMAKE_PREFIX_PATH_PREVIOUS_VALUE=$CMAKE_PREFIX_PATH
fi
export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"
"$PY" -I -B - "$ATTEMPT_DIR/cmake-prefix-path.json" "$CMAKE_PREFIX_PATH_PREVIOUSLY_SET" \
  "$CMAKE_PREFIX_PATH_PREVIOUS_VALUE" "$CMAKE_PREFIX_PATH" <<'PY'
import json
import sys
import time

path, previously_set, previous_value, effective_value = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "previously_set": previously_set == "true",
            "previous_value": previous_value,
            "effective_value": effective_value,
            "overwritten": previously_set == "true",
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"
driver_setup_rc=0
exec {DRIVER_STDOUT_FD}>"$ATTEMPT_DIR/floor-driver.stdout" || driver_setup_rc=$?
if [[ "$driver_setup_rc" -ne 0 ]]; then
  write_failure "$driver_setup_rc" floor_driver_setup "cannot create driver stdout"
  exit "$driver_setup_rc"
fi
exec {DRIVER_STDERR_FD}>"$ATTEMPT_DIR/floor-driver.stderr" || driver_setup_rc=$?
if [[ "$driver_setup_rc" -ne 0 ]]; then
  write_failure "$driver_setup_rc" floor_driver_setup "cannot create driver stderr"
  exit "$driver_setup_rc"
fi
printf '%s\n' "launch-attempted" >"$ATTEMPT_DIR/floor-driver.launch-attempted"
driver_rc=0
"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py" \
  --mode official \
  --protocol "$REPO_ROOT/$PROTOCOL_PATH" \
  >&"$DRIVER_STDOUT_FD" 2>&"$DRIVER_STDERR_FD" || driver_rc=$?
exec {DRIVER_STDOUT_FD}>&-
exec {DRIVER_STDERR_FD}>&-

# 出典: certify_calibration.sh:734-762 @ e9b6f69
job_result_writer_rc=0
"$PY" -I -B - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$driver_rc" \
  "$PROTOCOL_PATH" "$CURRENT_COMMIT" "$JOB_SCRIPT_SHA256" \
  "$EXECUTING_SCRIPT_SHA256" "$IZANAGI_SUBMISSION_NONCE" "$REQUESTED_S" <<'PY' \
  || job_result_writer_rc=$?
import json
import sys
import time

(
    path,
    job_id,
    driver_rc,
    protocol_path,
    source_commit,
    job_script_sha256,
    executing_script_sha256,
    nonce,
    reservation_requested_s,
) = sys.argv[1:]
payload = {
    "schema_version": "pegasus-floor-job-result/v1",
    "pbs_jobid": job_id,
    "driver_rc": int(driver_rc),
    "mode": "official",
    "protocol_path": protocol_path,
    "source_commit": source_commit,
    "job_script_sha256": job_script_sha256,
    "executing_script_sha256": executing_script_sha256,
    "nonce": nonce,
    "reservation_requested_s": int(reservation_requested_s),
    "completed_epoch": int(time.time()),
}
with open(path, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY
if [[ "$job_result_writer_rc" -ne 0 ]]; then
  write_failure "$job_result_writer_rc" job_result "cannot write floor job result create-only"
fi
if [[ "$driver_rc" -ne 0 ]]; then
  write_failure "$driver_rc" floor_driver "official floor driver returned nonzero"
fi
exit "$driver_rc"
