#!/usr/bin/env bash
# Login-node submitter for the one-shot T-1477 read-heavy Pegasus ablation.
# This file is intentionally kept in dev-wave-scratch; it is not a repo tool.
set -u -o pipefail

usage() {
  cat <<'EOF'
usage: submit_read_heavy_ablation.sh [options]

options:
  --repo-root PATH       repository/worktree root (default: inferred)
  --output-root PATH     persistent job output root
  --walltime HH:MM:SS    PBS walltime (default: 07:00:00)
  --job-script PATH      PBS body (default: sibling read_heavy_ablation.pbs)
  -h, --help             show this help

The same values can be supplied through IZANAGI_ABLATION_OUTPUT_ROOT and
IZANAGI_ABLATION_WALLTIME.
EOF
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd -P)
JOB_SCRIPT="$SCRIPT_DIR/read_heavy_ablation.pbs"
DEFAULT_OUTPUT_ROOT="/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1477-d58-ablation/pegasus-run/"
OUTPUT_ROOT="${IZANAGI_ABLATION_OUTPUT_ROOT:-$DEFAULT_OUTPUT_ROOT}"
WALLTIME="${IZANAGI_ABLATION_WALLTIME:-07:00:00}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      [[ $# -ge 2 ]] || { echo "--repo-root needs a value" >&2; exit 2; }
      REPO_ROOT=$2
      shift 2
      ;;
    --output-root)
      [[ $# -ge 2 ]] || { echo "--output-root needs a value" >&2; exit 2; }
      OUTPUT_ROOT=$2
      shift 2
      ;;
    --walltime)
      [[ $# -ge 2 ]] || { echo "--walltime needs a value" >&2; exit 2; }
      WALLTIME=$2
      shift 2
      ;;
    --job-script)
      [[ $# -ge 2 ]] || { echo "--job-script needs a value" >&2; exit 2; }
      JOB_SCRIPT=$2
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

if [[ ! -d "$REPO_ROOT" ]]; then
  echo "repo root is not a directory: $REPO_ROOT" >&2
  exit 2
fi
REPO_ROOT=$(cd "$REPO_ROOT" && pwd -P) || {
  echo "cannot resolve repo root: $REPO_ROOT" >&2
  exit 2
}
if [[ ! -f "$JOB_SCRIPT" ]]; then
  echo "job script not found: $JOB_SCRIPT" >&2
  exit 2
fi
JOB_SCRIPT_DIR=$(cd "$(dirname "$JOB_SCRIPT")" && pwd -P) || {
  echo "cannot resolve job script directory" >&2
  exit 2
}
JOB_SCRIPT="$JOB_SCRIPT_DIR/$(basename "$JOB_SCRIPT")"

if [[ "$REPO_ROOT" != /* || "$REPO_ROOT" == *$'\n'* || "$REPO_ROOT" == *,* ]]; then
  echo "repo root must be an absolute path without comma/newline: $REPO_ROOT" >&2
  exit 2
fi
if [[ "$JOB_SCRIPT" != /* || "$JOB_SCRIPT" == *$'\n'* || "$JOB_SCRIPT" == *,* ]]; then
  echo "job script must be an absolute path without comma/newline: $JOB_SCRIPT" >&2
  exit 2
fi

if [[ "$OUTPUT_ROOT" != /* || "$OUTPUT_ROOT" == *$'\n'* || "$OUTPUT_ROOT" == *,* ]]; then
  echo "output root must be an absolute path without comma/newline: $OUTPUT_ROOT" >&2
  exit 2
fi
if ! mkdir -p "$OUTPUT_ROOT"; then
  echo "cannot create output root: $OUTPUT_ROOT" >&2
  exit 2
fi
OUTPUT_ROOT=$(cd "$OUTPUT_ROOT" && pwd -P) || {
  echo "cannot resolve output root: $OUTPUT_ROOT" >&2
  exit 2
}
case "$OUTPUT_ROOT/" in
  "$REPO_ROOT/"*)
    echo "scheduler output must be outside the repository: $OUTPUT_ROOT" >&2
    exit 2
    ;;
esac
if git -C "$OUTPUT_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "scheduler output is inside another repository: $OUTPUT_ROOT" >&2
  exit 2
fi

walltime_seconds() {
  local value=$1
  if [[ ! "$value" =~ ^([0-9]+):([0-5][0-9]):([0-5][0-9])$ ]]; then
    return 2
  fi
  local hours=${BASH_REMATCH[1]}
  local minutes=${BASH_REMATCH[2]}
  local seconds=${BASH_REMATCH[3]}
  printf '%d\n' "$((10#$hours * 3600 + 10#$minutes * 60 + 10#$seconds))"
}

WALLTIME_S=$(walltime_seconds "$WALLTIME") || {
  echo "invalid walltime: $WALLTIME" >&2
  exit 2
}
if [[ "$WALLTIME_S" -le 0 ]]; then
  echo "walltime must be positive: $WALLTIME" >&2
  exit 2
fi

# Plan v2 §2c re-estimate after making both arms cold-cold:
# the existing plan range is 4,458--6,718 s for floor/campaign control work.
# buildcache's conservative CCBench cap is 900 s per build (the same cap documented
# in tools/pegasus/certify_calibration.sh:8-11).  Eight genomes × off/on means
# 16 cold builds = 14,400 s, so the combined estimate is 18,858--21,118 s;
# adding a 600 s final reserve gives 19,458--21,718 s (about 5 h 25 m--6 h 02 m).
# The task-mandated default is 07:00:00, leaving queue headroom for the
# cold-cold estimate.

SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)
rc=$?
if [[ "$rc" -ne 0 || ! "$SOURCE_COMMIT" =~ ^[0-9a-f]{7,64}$ ]]; then
  echo "cannot resolve source commit" >&2
  exit 2
fi

FULL_STATUS=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)
rc=$?
if [[ "$rc" -ne 0 ]]; then
  echo "cannot inspect worktree status" >&2
  exit 2
fi
SOURCE_STATUS=$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all -- \
  . ':(exclude)dev-wave-scratch')
rc=$?
if [[ "$rc" -ne 0 ]]; then
  echo "cannot inspect source worktree status" >&2
  exit 2
fi
FULL_CLEAN=false
SOURCE_CLEAN=false
[[ -z "$FULL_STATUS" ]] && FULL_CLEAN=true
[[ -z "$SOURCE_STATUS" ]] && SOURCE_CLEAN=true
# The source status is evidence, not a submission gate: this wave intentionally
# runs the stage-5 between_run_floor.py edits before they are committed.  The
# commit plus both status files make that fact explicit in the receipt.

JOB_SCRIPT_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
rc=$?
if [[ "$rc" -ne 0 || ! "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "cannot hash PBS job script" >&2
  exit 2
fi
NONCE="$(date +%s%N)-$$"
rc=$?
if [[ "$rc" -ne 0 || ! "$NONCE" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "cannot create a safe submission nonce" >&2
  exit 2
fi

SUBMISSION_DIR="$OUTPUT_ROOT/submissions/$NONCE"
if ! mkdir -p "$OUTPUT_ROOT/submissions"; then
  echo "cannot create submission parent" >&2
  exit 2
fi
if ! mkdir "$SUBMISSION_DIR"; then
  echo "submission directory already exists or cannot be created: $SUBMISSION_DIR" >&2
  exit 2
fi
if ! printf '%s' "$FULL_STATUS" >"$SUBMISSION_DIR/worktree-status.txt"; then
  echo "cannot record full worktree status" >&2
  exit 2
fi
if ! printf '%s' "$SOURCE_STATUS" >"$SUBMISSION_DIR/source-status-excluding-scratch.txt"; then
  echo "cannot record source worktree status" >&2
  exit 2
fi

# Capture preflight evidence.  qstat -Q is checked as a submission gate below;
# pegasusinfo remains evidence-only.
capture_preflight() {
  local name=$1
  shift
  "$@" >"$SUBMISSION_DIR/${name}.stdout" 2>"$SUBMISSION_DIR/${name}.stderr"
  local command_rc=$?
  printf '%s\n' "$command_rc" >"$SUBMISSION_DIR/${name}.rc"
  return 0
}
capture_preflight qstat_Q qstat -Q
capture_preflight pegasusinfo pegasusinfo

QSTAT_Q_RC=$(<"$SUBMISSION_DIR/qstat_Q.rc")
if [[ "$QSTAT_Q_RC" != 0 ]]; then
  echo "qstat -Q failed; refusing to submit" >&2
  exit 2
fi
if ! python3 - "$SUBMISSION_DIR/qstat_Q.stdout" <<'PY'
import sys

path = sys.argv[1]
found = False
for raw in open(path, encoding="utf-8", errors="replace"):
    fields = raw.split()
    if not fields or fields[0].rstrip(":") != "gen_S":
        continue
    found = True
    states = {field.upper() for field in fields[1:]}
    if "ENA" in states and "ACT" in states:
        raise SystemExit(0)
    raise SystemExit(
        "gen_S queue is not both ENA and ACT: " + repr(raw.rstrip("\n"))
    )
if not found:
    raise SystemExit("gen_S queue row is missing from qstat -Q output")
PY
then
  echo "gen_S queue is not enabled and active; refusing to submit" >&2
  exit 2
fi

python3 - "$SUBMISSION_DIR" "$SOURCE_COMMIT" "$JOB_SCRIPT" "$JOB_SCRIPT_SHA256" \
  "$REPO_ROOT" "$OUTPUT_ROOT" "$NONCE" "$WALLTIME" "$WALLTIME_S" \
  "$FULL_CLEAN" "$SOURCE_CLEAN" <<'PY'
import json
import os
import sys

(root, source_commit, job_script, script_sha, repo_root, output_root, nonce,
 walltime, walltime_s, full_clean, source_clean) = sys.argv[1:]

def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()

preflight = {}
for name in ("qstat_Q", "pegasusinfo"):
    preflight[name] = {
        "rc": int(read(os.path.join(root, name + ".rc")).strip()),
        "stdout_path": os.path.join(root, name + ".stdout"),
        "stderr_path": os.path.join(root, name + ".stderr"),
    }
payload = {
    "schema_version": "read-heavy-ablation-pre-submit/v1",
    "source_commit": source_commit,
    "repo_root": repo_root,
    "job_script": job_script,
    "job_script_sha256": script_sha,
    "worktree_clean": full_clean == "true",
    "source_worktree_clean_excluding_dev_wave_scratch": source_clean == "true",
    "worktree_status_path": os.path.join(root, "worktree-status.txt"),
    "source_status_excluding_scratch_path": os.path.join(
        root, "source-status-excluding-scratch.txt"
    ),
    "output_root": output_root,
    "submission_nonce": nonce,
    "walltime": walltime,
    "walltime_s": int(walltime_s),
    "preflight": preflight,
    "qsub": {"executed": False},
}
with open(os.path.join(root, "pre-submit.json"), "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
rc=$?
if [[ "$rc" -ne 0 ]]; then
  echo "cannot write pre-submit record" >&2
  exit "$rc"
fi

SCHEDULER_STDOUT="$OUTPUT_ROOT/scheduler-${NONCE}.stdout"
SCHEDULER_STDERR="$OUTPUT_ROOT/scheduler-${NONCE}.stderr"
EXPORT_SPEC="IZANAGI_REPO_ROOT=$REPO_ROOT,IZANAGI_OUT_ROOT=$OUTPUT_ROOT,"
EXPORT_SPEC+="IZANAGI_NONCE=$NONCE,IZANAGI_WALLTIME=$WALLTIME,"
EXPORT_SPEC+="IZANAGI_BETWEEN_RUN_ENV_TAG=pegasus,IZANAGI_SOURCE_COMMIT=$SOURCE_COMMIT,"
EXPORT_SPEC+="IZANAGI_JOB_SCRIPT=$JOB_SCRIPT,IZANAGI_JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256,"
# Short aliases make the qsub contract easy to inspect; the PBS body prefers the
# IZANAGI_* names so unrelated login-node variables cannot silently win.
EXPORT_SPEC+="REPO_ROOT=$REPO_ROOT,OUT_ROOT=$OUTPUT_ROOT,NONCE=$NONCE,WALLTIME=$WALLTIME"
QSUB_CMD=(qsub -l "elapstim_req=$WALLTIME" \
  -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR" -v "$EXPORT_SPEC" "$JOB_SCRIPT")
{
  printf '%q ' "${QSUB_CMD[@]}"
  printf '\n'
} >"$SUBMISSION_DIR/qsub-command.txt"

"${QSUB_CMD[@]}" >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"
qsub_rc=$?
printf '%s\n' "$qsub_rc" >"$SUBMISSION_DIR/qsub.rc"
if [[ "$qsub_rc" -ne 0 ]]; then
  echo "qsub failed; see $SUBMISSION_DIR" >&2
  exit "$qsub_rc"
fi

REQUEST_ID=$(python3 - "$SUBMISSION_DIR/qsub.stdout" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
match = re.search(r"Request\s+(\S+)\s+submitted", text)
if match:
    print(match.group(1).rstrip("."))
else:
    tokens = text.split()
    if len(tokens) == 1:
        print(tokens[0].rstrip("."))
    else:
        raise SystemExit("qsub succeeded but request ID could not be parsed")
PY
)
rc=$?
if [[ "$rc" -ne 0 || -z "$REQUEST_ID" ]]; then
  echo "qsub succeeded but request ID could not be parsed" >&2
  exit 4
fi
if ! printf '%s\n' "$REQUEST_ID" >"$SUBMISSION_DIR/request-id.txt"; then
  echo "cannot save request ID" >&2
  exit 2
fi

# Confirm visibility immediately; unlike congestion preflight, this is a submit
# integrity check and therefore stops if the scheduler cannot see the request.
qstat "$REQUEST_ID" >"$SUBMISSION_DIR/qstat.stdout" 2>"$SUBMISSION_DIR/qstat.stderr"
qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$SUBMISSION_DIR/qstat.rc"
if [[ "$qstat_rc" -ne 0 ]]; then
  echo "submitted request is not visible to qstat: $REQUEST_ID" >&2
  exit "$qstat_rc"
fi

python3 - "$SUBMISSION_DIR/pre-submit.json" "$SUBMISSION_DIR/submit-receipt.json" \
  "$REQUEST_ID" "$SCHEDULER_STDOUT" "$SCHEDULER_STDERR" <<'PY'
import json
import sys

pre_path, target, request_id, scheduler_stdout, scheduler_stderr = sys.argv[1:]
with open(pre_path, encoding="utf-8") as handle:
    pre = json.load(handle)
payload = dict(pre)
payload["schema_version"] = "read-heavy-ablation-submit-receipt/v1"
payload["qsub"] = {
    "executed": True,
    "request_id": request_id,
    "command_path": pre_path.replace("pre-submit.json", "qsub-command.txt"),
    "stdout_path": pre_path.replace("pre-submit.json", "qsub.stdout"),
    "stderr_path": pre_path.replace("pre-submit.json", "qsub.stderr"),
    "rc_path": pre_path.replace("pre-submit.json", "qsub.rc"),
    "scheduler_stdout": scheduler_stdout,
    "scheduler_stderr": scheduler_stderr,
    "visibility_stdout": pre_path.replace("pre-submit.json", "qstat.stdout"),
    "visibility_stderr": pre_path.replace("pre-submit.json", "qstat.stderr"),
    "visibility_rc": 0,
}
with open(target, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
rc=$?
if [[ "$rc" -ne 0 ]]; then
  echo "cannot write submit receipt" >&2
  exit "$rc"
fi

echo "submit receipt: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
echo "scheduler stdout: $SCHEDULER_STDOUT"
echo "scheduler stderr: $SCHEDULER_STDERR"
