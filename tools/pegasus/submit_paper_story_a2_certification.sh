#!/bin/bash
# Login-side exact two-job fan-out and create-only group finisher for A-2.
set -Eeuo pipefail
umask 077

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
PYTHON_BIN=${PYTHON:-python3.10}
cd "$REPO_ROOT"

usage() {
  echo "usage: submit_paper_story_a2_certification.sh [finish-group] --attempt-id ID [--ccbench-root ABS --dependency-prefix-source ABS]" >&2
}

MODE=submit
if [[ ${1:-} == finish-group ]]; then
  MODE=finish-group
  shift
fi
ATTEMPT_ID=""
CCBENCH_ROOT=""
DEPENDENCY_PREFIX_SOURCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --attempt-id)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      ATTEMPT_ID=$2
      shift 2
      ;;
    --ccbench-root)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      CCBENCH_ROOT=$2
      shift 2
      ;;
    --dependency-prefix-source)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      DEPENDENCY_PREFIX_SOURCE=$2
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
[[ "$ATTEMPT_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]] || {
  echo "--attempt-id is not a canonical leaf" >&2
  exit 2
}

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^pegasus0[0-9]+([.].*)?$ ]]; then
  echo "A-2 submitter is login-side only" >&2
  exit 2
fi
command -v -- qstat >/dev/null 2>&1 || {
  echo "required completion command is unavailable: qstat" >&2
  exit 2
}

if [[ "$MODE" == finish-group ]]; then
  ATTEMPT_ROOT=$("$PYTHON_BIN" -B - "$ATTEMPT_ID" <<'PY'
import json, pathlib, sys
from orchestrator.campaign import paper_story_a2_certification as a2
root = a2.load_policy().durable_base / sys.argv[1]
value = json.loads((root / "preregistration.json").read_text(encoding="utf-8"))
if value.get("attempt_root") != str(root):
    raise SystemExit("preregistration attempt root differs")
print(root)
print(value.get("current_pin", ""))
PY
  )
  readarray -t FINISH_VALUES <<<"$ATTEMPT_ROOT"
  [[ ${#FINISH_VALUES[@]} -eq 2 && -n ${FINISH_VALUES[1]} ]] || {
    echo "preregistration identity is incomplete" >&2
    exit 2
  }
  "$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
    finish-group --attempt-root "${FINISH_VALUES[0]}" \
    --current-pin "${FINISH_VALUES[1]}"
  exit 0
fi

for command_name in git qsub check_quota sha256sum realpath; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required submission command is unavailable: $command_name" >&2
    exit 2
  }
done
check_quota >/dev/null
QUEUE_STATE=$(qstat -Q)
printf '%s\n' "$QUEUE_STATE" | "$PYTHON_BIN" -I -B -c '
import re, sys
text = sys.stdin.read()
raise SystemExit(0 if "gen_S" in text
                 and re.search(r"(?i)\b(ENA|ENABLE(?:D)?)\b", text)
                 and re.search(r"(?i)\b(ACT|ACTIVE)\b", text) else 1)
' || {
  echo "gen_S is not ENA/ACT" >&2
  exit 2
}

SOURCE_COMMIT=$(git rev-parse HEAD)
[[ -n "$SOURCE_COMMIT" ]] || { echo "repository HEAD is unavailable" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || {
  echo "repository tracked worktree is not clean" >&2
  exit 2
}

[[ -n "$CCBENCH_ROOT" && -n "$DEPENDENCY_PREFIX_SOURCE" ]] || {
  usage
  exit 2
}
for value in "$REPO_ROOT" "$CCBENCH_ROOT" "$DEPENDENCY_PREFIX_SOURCE"; do
  [[ "$value" == /* && "$value" != *","* && "$value" != *"="* \
      && "$value" != *$'\n'* ]] || {
    echo "qsub environment path is not a safe absolute value" >&2
    exit 2
  }
done
CCBENCH_ROOT=$(realpath -e -- "$CCBENCH_ROOT")
DEPENDENCY_PREFIX_SOURCE=$(realpath -e -- "$DEPENDENCY_PREFIX_SOURCE")
[[ -d "$CCBENCH_ROOT" && ! -L "$CCBENCH_ROOT" \
    && -d "$DEPENDENCY_PREFIX_SOURCE" && ! -L "$DEPENDENCY_PREFIX_SOURCE" ]] || {
  echo "CCBench or dependency prefix source is unavailable" >&2
  exit 2
}
CURRENT_PIN=$(git -C "$CCBENCH_ROOT" rev-parse HEAD)
[[ -n "$CURRENT_PIN" && -z "$(git -C "$CCBENCH_ROOT" status --porcelain --untracked-files=no)" ]] || {
  echo "CCBench must have a clean HEAD" >&2
  exit 2
}
if qstat | grep -F "paper-a2-cert" >/dev/null; then
  echo "an A-2 certification request is already visible" >&2
  exit 2
fi

ATTEMPT_ROOT=$("$PYTHON_BIN" -B -m \
  orchestrator.campaign.paper_story_a2_certification preregister \
  --attempt-id "$ATTEMPT_ID" --current-pin "$CURRENT_PIN")
JOB_BODY="$REPO_ROOT/tools/pegasus/paper_story_a2_certification.sh"
JOB_BODY_SHA256=$(sha256sum -- "$JOB_BODY")
JOB_BODY_SHA256=${JOB_BODY_SHA256%% *}
TMP_ROOT=$(mktemp -d)
trap 'rm -rf -- "$TMP_ROOT"' EXIT
WORKLOADS=(rr5 rr50)

for workload in "${WORKLOADS[@]}"; do
  job_root="$ATTEMPT_ROOT/jobs/$workload"
  stdout_path="$job_root/scheduler/job.stdout"
  stderr_path="$job_root/scheduler/job.stderr"
  variable_arg="IZANAGI_A2_ATTEMPT_ROOT=$ATTEMPT_ROOT,IZANAGI_A2_WORKLOAD=$workload,IZANAGI_A2_EXPECTED_HEAD=$SOURCE_COMMIT,IZANAGI_A2_CURRENT_PIN=$CURRENT_PIN,IZANAGI_A2_CCBENCH_ROOT=$CCBENCH_ROOT,IZANAGI_A2_REPO_ROOT=$REPO_ROOT,IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE=$DEPENDENCY_PREFIX_SOURCE"
  qsub_rc=0
  "$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
    exact-qsub -- qsub -A SFC -q gen_S -b 1 -l elapstim_req=06:00:00 \
    -N paper-a2-cert -v "$variable_arg" -o "$stdout_path" -e "$stderr_path" \
    "$JOB_BODY" >"$TMP_ROOT/$workload.qsub.stdout" \
    2>"$TMP_ROOT/$workload.qsub.stderr" || qsub_rc=$?
  if [[ "$qsub_rc" -ne 0 ]]; then
    echo "qsub failed for $workload; no group submission receipt was created" >&2
    exit "$qsub_rc"
  fi
  [[ ! -s "$TMP_ROOT/$workload.qsub.stderr" ]] || {
    echo "qsub wrote stderr for $workload; no group submission receipt was created" >&2
    exit 2
  }
  request_id=$("$PYTHON_BIN" -I -B - "$TMP_ROOT/$workload.qsub.stdout" <<'PY'
import pathlib, re, sys
raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
matches = re.findall(r"Request[ \t]+(\S+)[ \t]+submitted", raw)
value = matches[0] if len(matches) == 1 else raw.strip()
value = value.rstrip(".")
if value.startswith("0:"):
    value = value[2:]
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value):
    raise SystemExit("qsub returned a malformed request ID")
print(value)
PY
  )
  qstat -f "$request_id" >"$TMP_ROOT/$workload.qstat.stdout" \
    2>"$TMP_ROOT/$workload.qstat.stderr"
  [[ ! -s "$TMP_ROOT/$workload.qstat.stderr" ]] || {
    echo "qstat visibility wrote stderr for $workload" >&2
    exit 2
  }
  printf '%s\n' "$request_id" >"$TMP_ROOT/$workload.request-id"
  date -u +%Y-%m-%dT%H:%M:%SZ >"$TMP_ROOT/$workload.observed-at"
done

"$PYTHON_BIN" -B - "$TMP_ROOT/submission.json" "$TMP_ROOT" \
  "$ATTEMPT_ROOT" "$SOURCE_COMMIT" "$CURRENT_PIN" "$host" \
  "$REPO_ROOT" "$CCBENCH_ROOT" "$DEPENDENCY_PREFIX_SOURCE" \
  "$JOB_BODY" "$JOB_BODY_SHA256" <<'PY'
import json, pathlib, sys
from orchestrator.campaign import paper_story_a2_certification as a2

(destination, temporary, attempt, source, current, host, repo, ccbench,
 dependency, body, body_sha) = sys.argv[1:]
temporary = pathlib.Path(temporary)
jobs = []
for workload in ("rr5", "rr50"):
    request = (temporary / f"{workload}.request-id").read_text().strip()
    qsub_stdout = (temporary / f"{workload}.qsub.stdout").read_text()
    qstat_stdout = (temporary / f"{workload}.qstat.stdout").read_text()
    state = a2.target_bound_qstat_state_result(qstat_stdout, request).state
    if state not in a2._SUBMISSION_VISIBLE_STATES:
        raise SystemExit(f"qstat visibility is not QUE/RUN for {workload}")
    environment = {
        "IZANAGI_A2_ATTEMPT_ROOT": attempt,
        "IZANAGI_A2_WORKLOAD": workload,
        "IZANAGI_A2_EXPECTED_HEAD": source,
        "IZANAGI_A2_CURRENT_PIN": current,
        "IZANAGI_A2_CCBENCH_ROOT": ccbench,
        "IZANAGI_A2_REPO_ROOT": repo,
        "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE": dependency,
    }
    variable_arg = ",".join(f"{key}={value}" for key, value in environment.items())
    stdout_path = f"{attempt}/jobs/{workload}/scheduler/job.stdout"
    stderr_path = f"{attempt}/jobs/{workload}/scheduler/job.stderr"
    jobs.append({
        "workload": workload,
        "qsub_argv": [
            "qsub", "-A", "SFC", "-q", "gen_S", "-b", "1", "-l",
            "elapstim_req=06:00:00", "-N", "paper-a2-cert", "-v",
            variable_arg, "-o", stdout_path, "-e", stderr_path, body,
        ],
        "qsub_stdout": qsub_stdout,
        "qsub_stderr": "",
        "qsub_returncode": 0,
        "request_id": request,
        "qstat_visibility": {
            "observed": True,
            "observed_at_utc": (
                temporary / f"{workload}.observed-at").read_text().strip(),
            "request_id": request,
            "argv": ["qstat", "-f", request],
            "returncode": 0,
            "state": state,
            "stdout": qstat_stdout,
            "stderr": "",
        },
        "qsub_environment": environment,
    })
payload = {
    "schema_version": a2.SUBMISSION_SCHEMA,
    "route": "direct-qsub",
    "study": a2.load_policy().study,
    "protocol_sha256": a2.load_policy().protocol_sha256,
    "attempt_id": pathlib.Path(attempt).name,
    "attempt_root": attempt,
    "source_commit": source,
    "current_pin": current,
    "submit_host": host,
    "submission_cwd": repo,
    "job_body_sha256": body_sha,
    "jobs": jobs,
}
pathlib.Path(destination).write_text(
    json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
PY

"$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
  record-submission --attempt-root "$ATTEMPT_ROOT" --current-pin "$CURRENT_PIN" \
  --payload "$TMP_ROOT/submission.json"
for workload in "${WORKLOADS[@]}"; do
  cat "$TMP_ROOT/$workload.request-id"
done
