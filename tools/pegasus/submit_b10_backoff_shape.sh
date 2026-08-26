#!/bin/bash
# Login-side create-only submitter for one registered B10 phase.
set -Eeuo pipefail
umask 077
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP

usage() {
  cat >&2 <<'EOF'
usage: submit_b10_backoff_shape.sh --prereg-commit COMMIT
       --phase {build|verify|perf} [--workload {write-heavy|balanced|read-heavy}]
       [--dry-run] [--durable-root PATH]
EOF
}

PREREG_COMMIT=""
PHASE=""
WORKLOAD=""
DRY_RUN=0
DURABLE_ROOT_OVERRIDE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prereg-commit)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      PREREG_COMMIT=$2
      shift 2
      ;;
    --phase)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      PHASE=$2
      shift 2
      ;;
    --workload)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      WORKLOAD=$2
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --durable-root)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      DURABLE_ROOT_OVERRIDE=$2
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

[[ "$PREREG_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
  echo "--prereg-commit must be a full lowercase commit ID" >&2
  exit 2
}
[[ "$PHASE" =~ ^(build|verify|perf)$ ]] || {
  echo "--phase must be build, verify, or perf" >&2
  exit 2
}
if [[ "$PHASE" == build ]]; then
  [[ -z "$WORKLOAD" ]] || { echo "build phase must not select a workload" >&2; exit 2; }
else
  [[ "$WORKLOAD" =~ ^(write-heavy|balanced|read-heavy)$ ]] || {
    echo "verify/perf phase requires one registered workload" >&2
    exit 2
  }
fi
if [[ -n "$DURABLE_ROOT_OVERRIDE" && "$DRY_RUN" -ne 1 ]]; then
  echo "--durable-root override is test-only and requires --dry-run" >&2
  exit 2
fi

SCRIPT_SOURCE=${BASH_SOURCE[0]}
SCRIPT_PATH=$(realpath -e -- "$SCRIPT_SOURCE") || exit 2
[[ -f "$SCRIPT_PATH" && ! -L "$SCRIPT_SOURCE" && ! -L "$SCRIPT_PATH" ]] || exit 2
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..") || exit 2
JOB_SCRIPT="$SCRIPT_DIR/b10_backoff_shape_campaign.sh"
[[ -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]] || exit 2
[[ "$SCRIPT_PATH" == "$REPO_ROOT/tools/pegasus/submit_b10_backoff_shape.sh" ]] || exit 2

# Source identity and cleanliness are established before any durable write.
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit}) || exit 2
[[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || exit 2
git -C "$REPO_ROOT" merge-base --is-ancestor "$PREREG_COMMIT" "$SOURCE_COMMIT"
for required in \
  docs/b10-backoff-shape-preregistration.md \
  patches/silo-backoff-fixed.patch \
  orchestrator/campaign/b10_backoff_shape_sweep.py \
  tools/pegasus/b10_backoff_shape_campaign.sh; do
  git -C "$REPO_ROOT" cat-file -e "$SOURCE_COMMIT:$required"
done
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] || {
  echo "repository working tree must be clean" >&2
  exit 2
}
JOB_SCRIPT_SHA256=$(
  git -C "$REPO_ROOT" cat-file blob \
    "$SOURCE_COMMIT:tools/pegasus/b10_backoff_shape_campaign.sh" | sha256sum | awk '{print $1}'
)
[[ "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 2
[[ "$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')" == "$JOB_SCRIPT_SHA256" ]] || {
  echo "job script differs from committed source blob" >&2
  exit 2
}

GIT_COMMON_DIR=$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir) || exit 2
[[ "$GIT_COMMON_DIR" == /* ]] || { echo "git common dir is not absolute" >&2; exit 2; }
GIT_COMMON_REPO=${GIT_COMMON_DIR%/.git}
DEFAULT_DURABLE_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/b10-backoff-shape/submissions"
DURABLE_ROOT=${DURABLE_ROOT_OVERRIDE:-$DEFAULT_DURABLE_ROOT}

provision_durable_root() {
  local root=$1 current="/" component resolved
  local -a components
  [[ "$root" == /* && "$root" =~ ^[A-Za-z0-9_./:-]+$ ]] || return 1
  [[ "$root" != "$REPO_ROOT" && "$root" != "$REPO_ROOT/"* \
      && "$root" != "$GIT_COMMON_REPO" && "$root" != "$GIT_COMMON_REPO/"* ]] || return 1
  IFS='/' read -r -a components <<<"${root#/}"
  for component in "${components[@]}"; do
    [[ -n "$component" && "$component" != . && "$component" != .. ]] || return 1
    current="${current%/}/$component"
    [[ ! -L "$current" ]] || return 1
  done
  mkdir -p -m 0700 -- "$root" || return 1
  resolved=$(realpath -e -- "$root") || return 1
  [[ "$resolved" == "$root" ]] || return 1
  current="/"
  for component in "${components[@]}"; do
    current="${current%/}/$component"
    [[ -d "$current" && ! -L "$current" ]] || return 1
  done
}
provision_durable_root "$DURABLE_ROOT" || {
  echo "durable submission root is unsafe or unavailable" >&2
  exit 2
}

NONCE=$(python3 -I -B -c 'import secrets; print(secrets.token_hex(16))')
[[ "$NONCE" =~ ^[0-9a-f]{32}$ ]] || exit 2
SUBMISSION_DIR="$DURABLE_ROOT/$NONCE"
mkdir -m 0700 -- "$SUBMISSION_DIR" || {
  echo "submission staging already exists or cannot be created (create-only)" >&2
  exit 2
}
set -o noclobber

capture_required() {
  local name=$1 rc=0
  shift
  "$@" >"$SUBMISSION_DIR/${name}.stdout" 2>"$SUBMISSION_DIR/${name}.stderr" || rc=$?
  printf '%s\n' "$rc" >"$SUBMISSION_DIR/${name}.rc"
  return "$rc"
}

preflight_rc=0
if [[ "$DRY_RUN" -eq 1 ]]; then
  for name in qstat_Q pegasusinfo rbudgetcheck check_quota; do
    printf '%s\n' "not run (--dry-run)" >"$SUBMISSION_DIR/${name}.stdout"
    : >"$SUBMISSION_DIR/${name}.stderr"
    printf '0\n' >"$SUBMISSION_DIR/${name}.rc"
  done
else
  capture_required qstat_Q qstat -Q || preflight_rc=1
  capture_required pegasusinfo pegasusinfo || preflight_rc=1
  capture_required rbudgetcheck rbudgetcheck || preflight_rc=1
  capture_required check_quota check_quota || preflight_rc=1
fi
[[ "$preflight_rc" -eq 0 ]] || {
  echo "one or more scheduler preflight captures failed; qsub not executed" >&2
  exit 3
}

PREPARED_AT=$(date +%s)
python3 -I -B - "$SUBMISSION_DIR/pre-submit.json" "$SOURCE_COMMIT" \
  "$PREREG_COMMIT" "$NONCE" "$JOB_SCRIPT_SHA256" "$PHASE" "$WORKLOAD" \
  "$PREPARED_AT" "$DRY_RUN" <<'PY'
import json
import sys

(target, source, prereg, nonce, script_sha, phase, workload,
 prepared_at, dry_run) = sys.argv[1:]
payload = {
    "schema_version": "pegasus-b10-pre-submit/v2",
    "source_commit": source,
    "prereg_commit": prereg,
    "nonce": nonce,
    "job_script_path": "tools/pegasus/b10_backoff_shape_campaign.sh",
    "job_script_sha256": script_sha,
    "phase": phase,
    "workload": workload or None,
    "prepared_epoch": int(prepared_at),
    "dry_run": dry_run == "1",
    "request": {"project": "SFC", "queue": "gen_S", "nodes": 1,
                "elapstim_req_s": 21600},
}
with open(target, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
    stream.write("\n")
PY

export_spec="IZANAGI_B10_NONCE=$NONCE,IZANAGI_B10_SOURCE_COMMIT=$SOURCE_COMMIT,IZANAGI_B10_PREREG_COMMIT=$PREREG_COMMIT,IZANAGI_B10_PHASE=$PHASE"
if [[ -n "$WORKLOAD" ]]; then
  export_spec+=",IZANAGI_B10_WORKLOAD=$WORKLOAD"
fi
SCHEDULER_STDOUT="$SUBMISSION_DIR/scheduler.stdout"
SCHEDULER_STDERR="$SUBMISSION_DIR/scheduler.stderr"
qsub_cmd=(qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR" -v "$export_spec" "$JOB_SCRIPT")
printf 'qsub command:'
printf ' %q' "${qsub_cmd[@]}"
printf '\n'

SUBMITTED_AT=$(date +%s)
if [[ "$DRY_RUN" -eq 1 ]]; then
  REQUEST_ID="dry-run-$NONCE"
  printf '%s\n' "dry-run: qsub was not executed" >"$SUBMISSION_DIR/qsub.stdout"
  : >"$SUBMISSION_DIR/qsub.stderr"
else
  qsub_rc=0
  (cd "$REPO_ROOT" && "${qsub_cmd[@]}") \
    >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr" || qsub_rc=$?
  [[ "$qsub_rc" -eq 0 ]] || exit "$qsub_rc"
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
    if [[ "$qstat_rc" -eq 0 ]] && python3 -I -B - \
      "$SUBMISSION_DIR/qstat-$attempt.stdout" "$REQUEST_ID" <<'PY'
import re
import sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
expected = sys.argv[2].removeprefix("0:").rstrip(".")
observed = [item.removeprefix("0:").rstrip(".") for item in
            re.findall(r"(?im)^\s*Request ID\s*[:=]\s*(\S+)\s*$", text)]
raise SystemExit(0 if observed == [expected] else 1)
PY
    then
      request_visible=1
      break
    fi
    sleep 2
  done
  [[ "$request_visible" -eq 1 ]] || {
    echo "qsub succeeded but exact request ID is not visible via qstat" >&2
    exit 4
  }
fi

python3 -I -B - "$SUBMISSION_DIR/pre-submit.json" \
  "$SUBMISSION_DIR/submit-receipt.json" "$REQUEST_ID" "$SUBMITTED_AT" <<'PY'
import json
import sys
source, target, request_id, submitted_at = sys.argv[1:]
pre = json.load(open(source, encoding="utf-8"))
payload = {
    "schema_version": "pegasus-b10-submit-receipt/v2",
    "source_commit": pre["source_commit"],
    "prereg_commit": pre["prereg_commit"],
    "nonce": pre["nonce"],
    "request_id": request_id,
    "dry_run": pre["dry_run"],
    "submitted_epoch": int(submitted_at),
    "job_script_path": pre["job_script_path"],
    "job_script_sha256": pre["job_script_sha256"],
    "phase": pre["phase"],
    "workload": pre["workload"],
    "request": pre["request"],
}
with open(target, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
    stream.write("\n")
PY

echo "submission receipt: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
