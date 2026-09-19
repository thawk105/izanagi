#!/bin/bash
# Login-side policy-sized fan-out and create-only group finisher for A-2/A-6.
set -Eeuo pipefail
umask 077

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
PYTHON_BIN=${PYTHON:-python3.10}
cd "$REPO_ROOT"

usage() {
  echo "usage: submit_paper_story_a2_certification.sh [finish-group] [--policy PATH] --attempt-id ID [--ccbench-root ABS --dependency-prefix-source ABS --third-party-source-root ABS]" >&2
}

MODE=submit
if [[ ${1:-} == finish-group ]]; then
  MODE=finish-group
  shift
fi
ATTEMPT_ID=""
CCBENCH_ROOT=""
DEPENDENCY_PREFIX_SOURCE=""
THIRD_PARTY_SOURCE_ROOT=""
POLICY_SELECTION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --policy)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      POLICY_SELECTION=$2
      shift 2
      ;;
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
    --third-party-source-root)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      THIRD_PARTY_SOURCE_ROOT=$2
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

readarray -t POLICY_VALUES < <(
  "$PYTHON_BIN" -B - "$POLICY_SELECTION" <<'PY'
import sys
from orchestrator.campaign import paper_story_a2_certification as a2

selected = sys.argv[1]
policy = (a2.load_policy(a2.canonical_policy_path(selected))
          if selected else a2.load_policy())
scheduler = policy.document["scheduler"]
print(policy.path)
print(policy.study)
print(a2._qsub_job_name(policy))
print(scheduler["project"])
print(scheduler["queue"])
print(scheduler["nodes"])
print(scheduler["walltime"])
print(scheduler["job_body"])
for workload in a2.workload_ids(policy):
    print(workload)
PY
)
[[ ${#POLICY_VALUES[@]} -ge 9 ]] || {
  echo "selected certification policy is incomplete" >&2
  exit 2
}
POLICY_PATH=${POLICY_VALUES[0]}
STUDY=${POLICY_VALUES[1]}
JOB_NAME=${POLICY_VALUES[2]}
SCHEDULER_PROJECT=${POLICY_VALUES[3]}
SCHEDULER_QUEUE=${POLICY_VALUES[4]}
SCHEDULER_NODES=${POLICY_VALUES[5]}
SCHEDULER_WALLTIME=${POLICY_VALUES[6]}
JOB_BODY_RELATIVE=${POLICY_VALUES[7]}
WORKLOADS=("${POLICY_VALUES[@]:8}")
POLICY_ARGS=()
if [[ -n "$POLICY_SELECTION" ]]; then
  POLICY_ARGS=(--policy "$POLICY_PATH")
fi

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
  ATTEMPT_ROOT=$("$PYTHON_BIN" -B - "$ATTEMPT_ID" "$POLICY_PATH" <<'PY'
import json, pathlib, sys
from orchestrator.campaign import paper_story_a2_certification as a2
policy = a2.load_policy(sys.argv[2])
root = policy.durable_base / sys.argv[1]
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
    "${POLICY_ARGS[@]}" finish-group --attempt-root "${FINISH_VALUES[0]}" \
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
import sys
queue = sys.argv[1]
for line in sys.stdin:
    fields = line.split()
    if not fields or fields[0] != queue:
        continue
    states = {field.upper() for field in fields[1:]}
    if states & {"ENA", "ENABLE", "ENABLED"} and states & {"ACT", "ACTIVE"}:
        raise SystemExit(0)
raise SystemExit(1)
' "$SCHEDULER_QUEUE" || {
  echo "$SCHEDULER_QUEUE is not ENA/ACT" >&2
  exit 2
}

SOURCE_COMMIT=$(git rev-parse HEAD)
[[ -n "$SOURCE_COMMIT" ]] || { echo "repository HEAD is unavailable" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || {
  echo "repository tracked worktree is not clean" >&2
  exit 2
}

[[ -n "$CCBENCH_ROOT" && -n "$DEPENDENCY_PREFIX_SOURCE" \
    && -n "$THIRD_PARTY_SOURCE_ROOT" ]] || {
  usage
  exit 2
}
for value in "$REPO_ROOT" "$CCBENCH_ROOT" "$DEPENDENCY_PREFIX_SOURCE" \
    "$THIRD_PARTY_SOURCE_ROOT"; do
  [[ "$value" == /* && "$value" != *","* && "$value" != *"="* \
      && "$value" != *$'\n'* ]] || {
    echo "qsub environment path is not a safe absolute value" >&2
    exit 2
  }
done
CCBENCH_ROOT=$(realpath -e -- "$CCBENCH_ROOT")
DEPENDENCY_PREFIX_SOURCE=$(realpath -e -- "$DEPENDENCY_PREFIX_SOURCE")
[[ ! -L "$THIRD_PARTY_SOURCE_ROOT" ]] || {
  echo "third-party source root must not be a symlink" >&2
  exit 2
}
THIRD_PARTY_SOURCE_ROOT=$(realpath -e -- "$THIRD_PARTY_SOURCE_ROOT")
for value in "$REPO_ROOT" "$CCBENCH_ROOT" "$DEPENDENCY_PREFIX_SOURCE" \
    "$THIRD_PARTY_SOURCE_ROOT"; do
  [[ "$value" == /* && "$value" != *","* && "$value" != *"="* \
      && "$value" != *$'\n'* ]] || {
    echo "qsub environment path is not a safe absolute value" >&2
    exit 2
  }
done
[[ -d "$CCBENCH_ROOT" && ! -L "$CCBENCH_ROOT" \
    && -d "$DEPENDENCY_PREFIX_SOURCE" && ! -L "$DEPENDENCY_PREFIX_SOURCE" \
    && -d "$THIRD_PARTY_SOURCE_ROOT" && ! -L "$THIRD_PARTY_SOURCE_ROOT" \
    && -d "$THIRD_PARTY_SOURCE_ROOT/masstree" \
    && ! -L "$THIRD_PARTY_SOURCE_ROOT/masstree" \
    && -d "$THIRD_PARTY_SOURCE_ROOT/mimalloc" \
    && ! -L "$THIRD_PARTY_SOURCE_ROOT/mimalloc" \
    && -d "$THIRD_PARTY_SOURCE_ROOT/googletest" \
    && ! -L "$THIRD_PARTY_SOURCE_ROOT/googletest" ]] || {
  echo "CCBench, dependency prefix, or third-party source is unavailable" >&2
  exit 2
}
CURRENT_PIN=$("$PYTHON_BIN" -B -c 'from orchestrator.campaign.pin import CURRENT_PIN; print(CURRENT_PIN)')
[[ "$CURRENT_PIN" =~ ^[0-9a-f]{7}$ ]] || {
  echo "repository canonical CCBench pin must be a short lowercase commit" >&2
  exit 2
}
if ! CCBENCH_FULL_HEAD=$(git -C "$CCBENCH_ROOT" rev-parse --verify 'HEAD^{commit}'); then
  echo "CCBench HEAD cannot be resolved" >&2
  exit 2
fi
if ! CANONICAL_FULL_HEAD=$(
  git -C "$CCBENCH_ROOT" rev-parse --verify "${CURRENT_PIN}^{commit}"
); then
  echo "repository canonical CCBench pin cannot be resolved" >&2
  exit 2
fi
[[ "$CCBENCH_FULL_HEAD" =~ ^[0-9a-f]{40}$ \
    && "$CANONICAL_FULL_HEAD" =~ ^[0-9a-f]{40}$ \
    && "$CCBENCH_FULL_HEAD" == "$CANONICAL_FULL_HEAD" \
    && "$CCBENCH_FULL_HEAD" == "$CURRENT_PIN"* \
    && -z "$(git -C "$CCBENCH_ROOT" status --porcelain --untracked-files=no)" ]] || {
  echo "CCBench must have a clean HEAD exactly resolving the canonical pin" >&2
  exit 2
}
TMP_ROOT=$(mktemp -d)
trap 'rm -rf -- "$TMP_ROOT"' EXIT
inventory_rc=0
qstat -f >"$TMP_ROOT/request-inventory.stdout" \
  2>"$TMP_ROOT/request-inventory.stderr" || inventory_rc=$?
if [[ "$inventory_rc" -ne 0 || -s "$TMP_ROOT/request-inventory.stderr" ]]; then
  echo "cannot inventory existing certification requests" >&2
  exit 2
fi
if "$PYTHON_BIN" -I -B - "$TMP_ROOT/request-inventory.stdout" "$JOB_NAME" <<'PY'
import pathlib
import sys

inventory_path, job_name = sys.argv[1:]
expected = f"    Request Name = {job_name}"
lines = pathlib.Path(inventory_path).read_text(
    encoding="utf-8", errors="replace").splitlines()
raise SystemExit(0 if expected in lines else 1)
PY
then
  echo "a same-study certification request is already visible" >&2
  exit 2
fi

ATTEMPT_ROOT=$("$PYTHON_BIN" -B -m \
  orchestrator.campaign.paper_story_a2_certification "${POLICY_ARGS[@]}" preregister \
  --attempt-id "$ATTEMPT_ID" --current-pin "$CURRENT_PIN")
JOB_BODY="$REPO_ROOT/$JOB_BODY_RELATIVE"
JOB_BODY_SHA256=$(sha256sum -- "$JOB_BODY")
JOB_BODY_SHA256=${JOB_BODY_SHA256%% *}

for workload in "${WORKLOADS[@]}"; do
  job_root="$ATTEMPT_ROOT/jobs/$workload"
  stdout_path="$job_root/scheduler/job.stdout"
  stderr_path="$job_root/scheduler/job.stderr"
  qsub_stdout_path="$job_root/scheduler/qsub.stdout"
  qsub_stderr_path="$job_root/scheduler/qsub.stderr"
  variable_arg="IZANAGI_A2_ATTEMPT_ROOT=$ATTEMPT_ROOT,IZANAGI_A2_WORKLOAD=$workload,IZANAGI_A2_EXPECTED_HEAD=$SOURCE_COMMIT,IZANAGI_A2_CURRENT_PIN=$CURRENT_PIN,IZANAGI_A2_CCBENCH_ROOT=$CCBENCH_ROOT,IZANAGI_A2_REPO_ROOT=$REPO_ROOT,IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE=$DEPENDENCY_PREFIX_SOURCE,IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT=$THIRD_PARTY_SOURCE_ROOT"
  if [[ "$STUDY" == paper-story-a6-certification || "$STUDY" == paper-story-b7-fixed5-regression ]]; then
    variable_arg+=",IZANAGI_A2_POLICY_PATH=$POLICY_PATH"
  fi
  [[ ! -e "$qsub_stdout_path" && ! -L "$qsub_stdout_path" \
      && ! -e "$qsub_stderr_path" && ! -L "$qsub_stderr_path" ]] || {
    echo "qsub diagnostics already exist for $workload" >&2
    exit 2
  }
  set -o noclobber
  exec {qsub_stdout_fd}>"$qsub_stdout_path"
  exec {qsub_stderr_fd}>"$qsub_stderr_path"
  set +o noclobber
  qsub_rc=0
  "$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
    "${POLICY_ARGS[@]}" exact-qsub -- qsub -A "$SCHEDULER_PROJECT" \
    -q "$SCHEDULER_QUEUE" -b "$SCHEDULER_NODES" \
    -l "elapstim_req=$SCHEDULER_WALLTIME" -N "$JOB_NAME" \
    -v "$variable_arg" -o "$stdout_path" -e "$stderr_path" \
    "$JOB_BODY" >&"$qsub_stdout_fd" 2>&"$qsub_stderr_fd" || qsub_rc=$?
  exec {qsub_stdout_fd}>&-
  exec {qsub_stderr_fd}>&-
  unset qsub_stdout_fd qsub_stderr_fd
  "$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
    "${POLICY_ARGS[@]}" durabilize-qsub-diagnostics --attempt-root "$ATTEMPT_ROOT" \
    --workload "$workload"
  if [[ "$qsub_rc" -ne 0 ]]; then
    echo "qsub failed for $workload; no group submission receipt was created" >&2
    exit "$qsub_rc"
  fi
  [[ ! -s "$qsub_stderr_path" ]] || {
    echo "qsub wrote stderr for $workload; no group submission receipt was created" >&2
    exit 2
  }
  request_id=$("$PYTHON_BIN" -I -B - "$qsub_stdout_path" <<'PY'
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
  "$PYTHON_BIN" -B -m orchestrator.campaign.paper_story_a2_certification \
    "${POLICY_ARGS[@]}" record-request-id --attempt-root "$ATTEMPT_ROOT" \
    --workload "$workload" --request-id "$request_id" >/dev/null
  printf '%s\n' "$request_id" >"$TMP_ROOT/$workload.request-id"
  qstat -f "$request_id" >"$TMP_ROOT/$workload.qstat.stdout" \
    2>"$TMP_ROOT/$workload.qstat.stderr"
  [[ ! -s "$TMP_ROOT/$workload.qstat.stderr" ]] || {
    echo "qstat visibility wrote stderr for $workload" >&2
    exit 2
  }
  date -u +%Y-%m-%dT%H:%M:%SZ >"$TMP_ROOT/$workload.observed-at"
done

"$PYTHON_BIN" -B - "$TMP_ROOT/submission.json" "$TMP_ROOT" \
  "$ATTEMPT_ROOT" "$SOURCE_COMMIT" "$CURRENT_PIN" "$host" \
  "$REPO_ROOT" "$CCBENCH_ROOT" "$DEPENDENCY_PREFIX_SOURCE" \
  "$THIRD_PARTY_SOURCE_ROOT" "$JOB_BODY" "$JOB_BODY_SHA256" \
  "$POLICY_PATH" <<'PY'
import json, pathlib, sys
from orchestrator.campaign import paper_story_a2_certification as a2

(destination, temporary, attempt, source, current, host, repo, ccbench,
 dependency, third_party, body, body_sha, policy_path) = sys.argv[1:]
temporary = pathlib.Path(temporary)
policy = a2.load_policy(policy_path)
scheduler_policy = policy.document["scheduler"]
jobs = []
for workload in a2.workload_ids(policy):
    request = (temporary / f"{workload}.request-id").read_text().strip()
    scheduler = pathlib.Path(attempt) / "jobs" / workload / "scheduler"
    qsub_stdout = (scheduler / "qsub.stdout").read_text()
    qsub_stderr = (scheduler / "qsub.stderr").read_text()
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
        "IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT": third_party,
    }
    if policy.study in {"paper-story-a6-certification", "paper-story-b7-fixed5-regression"}:
        environment["IZANAGI_A2_POLICY_PATH"] = str(policy.path)
    variable_arg = ",".join(f"{key}={value}" for key, value in environment.items())
    stdout_path = f"{attempt}/jobs/{workload}/scheduler/job.stdout"
    stderr_path = f"{attempt}/jobs/{workload}/scheduler/job.stderr"
    jobs.append({
        "workload": workload,
        "qsub_argv": [
            "qsub", "-A", scheduler_policy["project"],
            "-q", scheduler_policy["queue"],
            "-b", str(scheduler_policy["nodes"]), "-l",
            f"elapstim_req={scheduler_policy['walltime']}",
            "-N", a2._qsub_job_name(policy), "-v",
            variable_arg, "-o", stdout_path, "-e", stderr_path, body,
        ],
        "qsub_stdout": qsub_stdout,
        "qsub_stderr": qsub_stderr,
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
    "study": policy.study,
    "protocol_sha256": policy.protocol_sha256,
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
  "${POLICY_ARGS[@]}" record-submission --attempt-root "$ATTEMPT_ROOT" \
  --current-pin "$CURRENT_PIN" \
  --payload "$TMP_ROOT/submission.json"
for workload in "${WORKLOADS[@]}"; do
  cat "$TMP_ROOT/$workload.request-id"
done
