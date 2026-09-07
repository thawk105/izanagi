#!/bin/bash
# Login-side submitter for the three fixed T-1259 diagnostic requests.
set -Eeuo pipefail
umask 077
export GIT_OPTIONAL_LOCKS=0

usage() {
  cat <<'EOF'
usage: t1259_qsub_env_delivery_submit.sh --attempt-root ABSOLUTE_NEW_PATH

Run this from a clean detached submit-tree at the commit to be measured.
The script records queue preflight evidence, writes each request's create-only
submission manifest, and submits exactly R1, R2, and R3. It does not wait for
terminal scheduler states; the group manifest therefore remains indeterminate
until the parent records all three terminal states and result hashes.
EOF
}

ATTEMPT_ROOT_RAW=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --attempt-root)
      [[ $# -ge 2 ]] || { echo "--attempt-root requires a path" >&2; exit 2; }
      ATTEMPT_ROOT_RAW=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done
if [[ -z "$ATTEMPT_ROOT_RAW" || "$ATTEMPT_ROOT_RAW" != /* ]]; then
  echo "--attempt-root must be an absolute new path" >&2
  exit 2
fi

SCRIPT_SOURCE=${BASH_SOURCE[0]}
SCRIPT_PATH=$(realpath -e -- "$SCRIPT_SOURCE") || {
  echo "cannot resolve submitter path" >&2
  exit 2
}
if [[ ! -f "$SCRIPT_PATH" || -L "$SCRIPT_PATH" || -L "$SCRIPT_SOURCE" ]]; then
  echo "submitter must be a non-symlink regular file" >&2
  exit 2
fi
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../../..") || {
  echo "cannot resolve repository root" >&2
  exit 2
}
if [[ "$SCRIPT_PATH" != "$REPO_ROOT/tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh" ]]; then
  echo "submitter must run from its canonical repository path" >&2
  exit 2
fi

PBS_SCRIPT="$REPO_ROOT/tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs"
PROBE_SCRIPT="$REPO_ROOT/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py"
for source in "$SCRIPT_PATH" "$PBS_SCRIPT" "$PROBE_SCRIPT"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    echo "required regular source is unavailable: $source" >&2
    exit 2
  fi
done

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
unset GIT_CEILING_DIRECTORIES
REPO_HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD)
if [[ ! "$REPO_HEAD" =~ ^[0-9a-f]{40}$ ]]; then
  echo "repository HEAD must be an exact lowercase 40-hex commit" >&2
  exit 2
fi
if git -C "$REPO_ROOT" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "T-1259 submission requires a detached submit-tree" >&2
  exit 2
fi
REPO_STATUS=$(git -C "$REPO_ROOT" status --porcelain=v1 \
  --untracked-files=all --ignore-submodules=none)
if [[ -n "$REPO_STATUS" ]]; then
  echo "T-1259 submission requires a clean detached submit-tree" >&2
  exit 2
fi
for relative in \
    tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh \
    tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs \
    tools/pegasus/probes/t1259_qsub_env_delivery_probe.py \
    orchestrator/campaign/s8b_floor_campaign.py; do
  git -C "$REPO_ROOT" ls-files --error-unmatch -- "$relative" >/dev/null || {
    echo "required source is not tracked at submit-tree HEAD: $relative" >&2
    exit 2
  }
done

ATTEMPT_PARENT_RAW=${ATTEMPT_ROOT_RAW%/*}
ATTEMPT_LEAF=${ATTEMPT_ROOT_RAW##*/}
if [[ -z "$ATTEMPT_PARENT_RAW" || -z "$ATTEMPT_LEAF" \
    || "$ATTEMPT_LEAF" == . || "$ATTEMPT_LEAF" == .. ]]; then
  echo "invalid attempt root" >&2
  exit 2
fi
ATTEMPT_PARENT=$(realpath -e -- "$ATTEMPT_PARENT_RAW") || {
  echo "attempt root parent must already exist" >&2
  exit 2
}
ATTEMPT_ROOT="$ATTEMPT_PARENT/$ATTEMPT_LEAF"
if [[ "$ATTEMPT_ROOT" != "$ATTEMPT_ROOT_RAW" || -e "$ATTEMPT_ROOT" || -L "$ATTEMPT_ROOT" ]]; then
  echo "attempt root must be canonical and absent" >&2
  exit 2
fi
case "$ATTEMPT_ROOT/" in
  "$REPO_ROOT/"*)
    echo "attempt root must be outside the repository" >&2
    exit 2
    ;;
esac

PY=""
for candidate in python3.10 python3.11 python3.12 python3; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -S -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY=$(realpath -e -- "$resolved")
    break
  fi
done
if [[ -z "$PY" ]]; then
  echo "Python 3.10 or newer is required" >&2
  exit 2
fi

mkdir -m 700 -- "$ATTEMPT_ROOT"
PREFLIGHT_DIR="$ATTEMPT_ROOT/preflight"
R1_DIR="$ATTEMPT_ROOT/r1-with-explicit-approval"
R2_DIR="$ATTEMPT_ROOT/r2-without-approval"
R3_DIR="$ATTEMPT_ROOT/r3-ambient-approval-only"
mkdir -m 700 -- "$PREFLIGHT_DIR" "$R1_DIR" "$R2_DIR" "$R3_DIR"

capture_preflight() {
  local name=$1
  shift
  local rc=0
  "$@" >"$PREFLIGHT_DIR/$name.stdout" 2>"$PREFLIGHT_DIR/$name.stderr" || rc=$?
  ( set -o noclobber; printf '%s\n' "$rc" >"$PREFLIGHT_DIR/$name.rc" )
  return "$rc"
}

preflight_failed=0
capture_preflight qstat-queues qstat -Q || preflight_failed=1
capture_preflight pegasusinfo pegasusinfo || preflight_failed=1
capture_preflight own-requests qstat || preflight_failed=1

"$PY" -I -B - "$PREFLIGHT_DIR" "$REPO_HEAD" <<'PY'
import datetime as dt
import hashlib
import json
import os
import socket
import sys
from pathlib import Path

root = Path(sys.argv[1])
commands = []
for name, argv in (
    ("qstat-queues", ["qstat", "-Q"]),
    ("pegasusinfo", ["pegasusinfo"]),
    ("own-requests", ["qstat"]),
):
    stdout = root / f"{name}.stdout"
    stderr = root / f"{name}.stderr"
    rc_path = root / f"{name}.rc"
    commands.append({
        "name": name,
        "argv": argv,
        "returncode": int(rc_path.read_text(encoding="ascii").strip()),
        "stdout_path": stdout.name,
        "stdout_sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
        "stderr_path": stderr.name,
        "stderr_sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
    })
document = {
    "schema_version": "izanagi-t1259-qsub-preflight/v1",
    "authority": "diagnostic-only",
    "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "hostname": socket.gethostname(),
    "repo_head": sys.argv[2],
    "commands": commands,
}
target = root / "preflight.json"
with target.open("x", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
if [[ "$preflight_failed" -ne 0 ]]; then
  echo "queue/non-interference preflight command failed; no qsub was executed" >&2
  exit 2
fi

readarray -t RANDOM_VALUES < <("$PY" -I -S -B - <<'PY'
import secrets
values = set()
while len(values) < 6:
    values.add(secrets.token_hex(16))
for value in sorted(values):
    print(value)
PY
)
if [[ ${#RANDOM_VALUES[@]} -ne 6 ]]; then
  echo "failed to generate six distinct random 32-hex values" >&2
  exit 2
fi
R1_NONCE=${RANDOM_VALUES[0]}
R2_NONCE=${RANDOM_VALUES[1]}
R2_EXPLICIT_SECOND=${RANDOM_VALUES[2]}
R2_AMBIENT_SECOND=${RANDOM_VALUES[3]}
R3_NONCE=${RANDOM_VALUES[4]}
AMBIENT_SENTINEL_VALUE=${RANDOM_VALUES[5]}
AMBIENT_APPROVAL_LITERAL=t1259-ambient-approval-must-not-match
PROBE_SHA256=$(sha256sum -- "$PROBE_SCRIPT" | awk '{print $1}')
SUBMITTER_SHA256=$(sha256sum -- "$SCRIPT_PATH" | awk '{print $1}')

write_submission_manifest() {
  local request_id=$1 request_label=$2 evidence_dir=$3 export_spec=$4
  shift 4
  "$PY" -I -B - \
    "$evidence_dir/submission-manifest.json" \
    "$request_id" "$request_label" "$REPO_HEAD" "$PROBE_SHA256" \
    "$export_spec" "$@" <<'PY'
import datetime as dt
import json
import os
import socket
import sys
from pathlib import Path

(
    target_text,
    request_id,
    request_label,
    repo_head,
    probe_sha256,
    export_spec,
    *pair_tokens,
) = sys.argv[1:]
if len(pair_tokens) % 2:
    raise SystemExit("ordered name/value argv is not paired")
rows = []
for index in range(0, len(pair_tokens), 2):
    name, value = pair_tokens[index:index + 2]
    rows.append({
        "name": name,
        "value": value,
        "value_byte_length": len(value.encode("utf-8")),
    })
reconstructed = ",".join(f"{row['name']}={row['value']}" for row in rows)
if reconstructed != export_spec:
    raise SystemExit("qsub -v string is not derived from the ordered pair argv")
target_names = (
    "IZANAGI_SUBMISSION_NONCE",
    "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN",
    "IZANAGI_FLOOR_JOB_EVIDENCE_ROOT",
    "T1259_QSUB_SECOND_HEX",
    "T1259_NQSV_AMBIENT_SENTINEL",
)
caller_environment = {}
for name in target_names:
    present = name in os.environ
    value = os.environ.get(name) if present else None
    caller_environment[name] = {
        "present": present,
        "value": value,
        "value_byte_length": len(value.encode("utf-8")) if value is not None else None,
    }
document = {
    "schema_version": "izanagi-t1259-qsub-submission-manifest/v1",
    "authority": "diagnostic-only",
    "request_id": request_id,
    "request_label": request_label,
    "repo_head": repo_head,
    "probe_script_path": "tools/pegasus/probes/t1259_qsub_env_delivery_probe.py",
    "probe_script_sha256": probe_sha256,
    "ordered_explicit_env": rows,
    "qsub_v_exact": export_spec,
    "qsub_v_byte_length": len(export_spec.encode("utf-8")),
    "qsub_caller_environment": caller_environment,
    "qsub_caller_pid": os.getppid(),
    "qsub_caller_observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "qsub_hostname": socket.gethostname(),
}
target = Path(target_text)
with target.open("x", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

write_request_receipt() {
  local evidence_dir=$1 request_id=$2 scheduler_request_id=$3 submitted_utc=$4
  "$PY" -I -B - \
    "$evidence_dir/submission-manifest.json" \
    "$evidence_dir/qsub-request.json" \
    "$request_id" "$scheduler_request_id" "$submitted_utc" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

manifest_path, target_text, logical_id, scheduler_id, submitted_utc = sys.argv[1:]
manifest = Path(manifest_path)
document = {
    "schema_version": "izanagi-t1259-qsub-request/v1",
    "authority": "diagnostic-only",
    "request_id": logical_id,
    "scheduler_request_id": scheduler_id,
    "submitted_utc": submitted_utc,
    "submission_manifest_path": manifest.name,
    "submission_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
}
target = Path(target_text)
with target.open("x", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

submit_request() (
  local request_id=$1 request_label=$2 ambient_mode=$3 evidence_dir=$4
  shift 4
  local -a pair_tokens=("$@")
  local export_spec="" name value index

  unset IZANAGI_SUBMISSION_NONCE
  unset IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN
  unset IZANAGI_FLOOR_JOB_EVIDENCE_ROOT
  unset T1259_QSUB_SECOND_HEX
  unset T1259_NQSV_AMBIENT_SENTINEL
  export T1259_NQSV_AMBIENT_SENTINEL="$AMBIENT_SENTINEL_VALUE"
  case "$ambient_mode" in
    sentinel-only)
      ;;
    duplicate-second)
      export T1259_QSUB_SECOND_HEX="$R2_AMBIENT_SECOND"
      ;;
    ambient-approval)
      export IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN="$AMBIENT_APPROVAL_LITERAL"
      ;;
    *)
      echo "invalid ambient mode: $ambient_mode" >&2
      exit 2
      ;;
  esac

  if (( ${#pair_tokens[@]} % 2 != 0 )); then
    echo "request pair list is not even" >&2
    exit 2
  fi
  for ((index=0; index<${#pair_tokens[@]}; index+=2)); do
    name=${pair_tokens[index]}
    value=${pair_tokens[index+1]}
    if [[ "$value" == *','* || "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
      echo "qsub -v value contains a forbidden delimiter" >&2
      exit 2
    fi
    if [[ -n "$export_spec" ]]; then
      export_spec+=,
    fi
    export_spec+="$name=$value"
  done

  write_submission_manifest \
    "$request_id" "$request_label" "$evidence_dir" "$export_spec" \
    "${pair_tokens[@]}"

  local submitted_utc qsub_rc=0 scheduler_request_id
  submitted_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  cd "$REPO_ROOT"
  qsub \
    -o "$evidence_dir/pbs.stdout" \
    -e "$evidence_dir/pbs.stderr" \
    -v "$export_spec" \
    "$PBS_SCRIPT" \
    >"$evidence_dir/qsub.stdout" 2>"$evidence_dir/qsub.stderr" || qsub_rc=$?
  ( set -o noclobber; printf '%s\n' "$qsub_rc" >"$evidence_dir/qsub.rc" )
  if [[ "$qsub_rc" -ne 0 ]]; then
    echo "$request_id qsub failed; evidence=$evidence_dir" >&2
    exit "$qsub_rc"
  fi
  scheduler_request_id=$("$PY" -I -B - "$evidence_dir/qsub.stdout" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
match = re.search(r"Request\s+(\S+)\s+submitted", text)
if match:
    print(match.group(1).rstrip("."))
elif len(text.split()) == 1:
    print(text.split()[0])
else:
    raise SystemExit(2)
PY
  ) || {
    echo "$request_id qsub succeeded but request ID could not be parsed" >&2
    exit 4
  }
  write_request_receipt \
    "$evidence_dir" "$request_id" "$scheduler_request_id" "$submitted_utc"
)

submit_request \
  R1 with-explicit-approval sentinel-only "$R1_DIR" \
  IZANAGI_SUBMISSION_NONCE "$R1_NONCE" \
  IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN "$R1_NONCE" \
  IZANAGI_FLOOR_JOB_EVIDENCE_ROOT "$R1_DIR"

submit_request \
  R2 without-approval-with-duplicate-second-name duplicate-second "$R2_DIR" \
  IZANAGI_SUBMISSION_NONCE "$R2_NONCE" \
  T1259_QSUB_SECOND_HEX "$R2_EXPLICIT_SECOND" \
  IZANAGI_FLOOR_JOB_EVIDENCE_ROOT "$R2_DIR"

submit_request \
  R3 ambient-approval-name-only ambient-approval "$R3_DIR" \
  IZANAGI_SUBMISSION_NONCE "$R3_NONCE" \
  IZANAGI_FLOOR_JOB_EVIDENCE_ROOT "$R3_DIR"

"$PY" -I -B - \
  "$ATTEMPT_ROOT" "$REPO_HEAD" "$SUBMITTER_SHA256" <<'PY'
import datetime as dt
import hashlib
import json
import os
import socket
import sys
from pathlib import Path

root = Path(sys.argv[1])
requests = []
for order, directory_name in enumerate((
    "r1-with-explicit-approval",
    "r2-without-approval",
    "r3-ambient-approval-only",
), start=1):
    directory = root / directory_name
    receipt_path = directory / "qsub-request.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    result_path = directory / "result.json"
    requests.append({
        "submission_order": order,
        "request_id": receipt["request_id"],
        "scheduler_request_id": receipt["scheduler_request_id"],
        "submitted_utc": receipt["submitted_utc"],
        "evidence_directory": directory_name,
        "submission_manifest_sha256": receipt["submission_manifest_sha256"],
        "terminal_state": "not-observed-by-submitter",
        "result_sha256": (
            hashlib.sha256(result_path.read_bytes()).hexdigest()
            if result_path.is_file() and not result_path.is_symlink() else None
        ),
    })
preflight = root / "preflight" / "preflight.json"
document = {
    "schema_version": "izanagi-t1259-qsub-submission-group/v1",
    "authority": "diagnostic-only",
    "status": "indeterminate-until-three-terminal-results-are-collected",
    "repo_head": sys.argv[2],
    "submitter_script_path": "tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh",
    "submitter_script_sha256": sys.argv[3],
    "submitted_hostname": socket.gethostname(),
    "group_manifest_created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "preflight_path": "preflight/preflight.json",
    "preflight_sha256": hashlib.sha256(preflight.read_bytes()).hexdigest(),
    "requests": requests,
    "completion_rule": (
        "the group remains indeterminate until all three scheduler terminal states "
        "and all three prefixed stdout results and result hashes are collected"
    ),
}
target = root / "submission-group-manifest.json"
with target.open("x", encoding="utf-8") as stream:
    json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
print(json.dumps({
    "status": document["status"],
    "attempt_root": str(root),
    "requests": [row["scheduler_request_id"] for row in requests],
}, ensure_ascii=False, sort_keys=True))
PY
