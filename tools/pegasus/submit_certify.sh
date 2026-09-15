#!/bin/bash
# ログインノード専用: clean source と投入前 snapshot を固定して certification job を投入する。
set -Eeuo pipefail

usage() {
  cat <<'EOF'
usage: submit_certify.sh [--dry-run] [--repo-root PATH] [--attempts-root PATH]
                         [--job-script PATH] [--rratio 5|20|50|80|95]
                         [--protocol silo|mocc|tictoc]
EOF
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)
JOB_SCRIPT="$SCRIPT_DIR/certify_calibration.sh"
ATTEMPTS_ROOT=""
DRY_RUN=0
RRATIO=50
PROTOCOL=silo
PROTOCOL_EXPLICIT=0

if [[ -n "${PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT+x}" ]]; then
  echo "legacy PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT is forbidden" >&2
  exit 2
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --repo-root) REPO_ROOT=$(cd "${2:?}" && pwd -P); shift 2 ;;
    --attempts-root) ATTEMPTS_ROOT=${2:?}; shift 2 ;;
    --job-script) JOB_SCRIPT=${2:?}; shift 2 ;;
    --rratio) RRATIO=${2:?}; shift 2 ;;
    --protocol) PROTOCOL=${2:?}; PROTOCOL_EXPLICIT=1; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$RRATIO" != "5" && "$RRATIO" != "20" && "$RRATIO" != "50" \
      && "$RRATIO" != "80" && "$RRATIO" != "95" ]]; then
  echo "--rratio must be exactly 5, 20, 50, 80, or 95" >&2
  exit 2
fi
if [[ "$PROTOCOL" != "silo" \
      && "$PROTOCOL" != "mocc" \
      && "$PROTOCOL" != "tictoc" ]]; then
  echo "--protocol must be exactly silo, mocc, or tictoc" >&2
  exit 2
fi

THIRD_PARTY_SOURCE_ROOT="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
if [[ "$THIRD_PARTY_SOURCE_ROOT" != /* \
      || ! -d "$THIRD_PARTY_SOURCE_ROOT" \
      || -L "$THIRD_PARTY_SOURCE_ROOT" ]]; then
  echo "pinned third-party staging root is unavailable: $THIRD_PARTY_SOURCE_ROOT" >&2
  exit 2
fi
for third_party_name in masstree mimalloc googletest; do
  third_party_source="$THIRD_PARTY_SOURCE_ROOT/$third_party_name"
  if [[ ! -d "$third_party_source" || -L "$third_party_source" ]]; then
    echo "pinned third-party staging source is unavailable: $third_party_name" >&2
    exit 2
  fi
done

if [[ ! -f "$JOB_SCRIPT" ]]; then
  echo "job script not found: $JOB_SCRIPT" >&2
  exit 2
fi

POLICY="$REPO_ROOT/tools/pegasus/policy.json"
CALIBRATION_POLICY="$REPO_ROOT/tools/pegasus/policies/calibration_v1.json"
if [[ ! -f "$POLICY" ]]; then
  echo "policy not found: $POLICY" >&2
  exit 2
fi
if [[ ! -f "$CALIBRATION_POLICY" || -L "$CALIBRATION_POLICY" ]]; then
  echo "calibration policy not found: $CALIBRATION_POLICY" >&2
  exit 2
fi
readarray -t policy_values < <(python3 - "$POLICY" "$CALIBRATION_POLICY" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    p = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    calibration = json.load(handle)
print(p["project"])
print(p["queue"])
print(p["nodes"])
print(calibration["certify_walltime_s"])
PY
)
if [[ ${#policy_values[@]} -ne 4 ]]; then
  echo "policy parse failed" >&2
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
WALLTIME_S=${policy_values[3]}

# source identity は staging を作る前に確定する。
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD) || exit 2
if [[ ! "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "cannot resolve a full source commit" >&2
  exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all -- . ':(exclude)output')" ]]; then
  echo "working tree is dirty; certification submission aborted" >&2
  exit 2
fi
GIT_COMMON_DIR=$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir) || exit 2
SCHEDULER_OUTPUT_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/calibration-certify"
mkdir -p "$SCHEDULER_OUTPUT_ROOT"
JOB_SCRIPT_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
SUBMIT_EPOCH=$(date +%s)
NONCE=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)

if [[ -z "$ATTEMPTS_ROOT" ]]; then
  ATTEMPTS_ROOT="$REPO_ROOT/output/env/pegasus/calibration/attempts"
fi
SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$NONCE"
mkdir -p "$ATTEMPTS_ROOT/submissions"
if ! mkdir "$SUBMISSION_DIR"; then
  echo "submission staging already exists (create-only): $SUBMISSION_DIR" >&2
  exit 2
fi

capture_required() {
  local name=$1
  shift
  "$@" >"$SUBMISSION_DIR/${name}.stdout" 2>"$SUBMISSION_DIR/${name}.stderr"
  local rc=$?
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
  # 4 capture を 1 preflight stage として全て保存し、どれか失敗なら qsub へ進まない。
  capture_required qstat_Q qstat -Q || preflight_rc=1
  capture_required pegasusinfo pegasusinfo || preflight_rc=1
  capture_required rbudgetcheck rbudgetcheck || preflight_rc=1
  capture_required check_quota check_quota || preflight_rc=1
fi

python3 - "$SUBMISSION_DIR" "$SOURCE_COMMIT" "$JOB_SCRIPT" "$JOB_SCRIPT_SHA256" \
  "$SUBMIT_EPOCH" "$NONCE" "$PROJECT" "$QUEUE" "$NODES" "$WALLTIME_S" \
  "$RRATIO" "$PROTOCOL" "$DRY_RUN" <<'PY'
import hashlib
import json
import os
import sys

(root, source_commit, script, script_sha, submit_epoch, nonce, project, queue,
 nodes, walltime_s, rratio, protocol, dry_run) = sys.argv[1:]
captures = {}
for name in ("qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"):
    def read(suffix):
        with open(os.path.join(root, name + suffix), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    captures[name] = {
        "rc": int(read(".rc").strip()),
        "stdout_raw": read(".stdout"),
        "stderr_raw": read(".stderr"),
    }
payload = {
    "schema_version": "pegasus-pre-submit/v1",
    "source_commit": source_commit,
    "job_script_path": os.path.relpath(script, os.path.dirname(os.path.dirname(os.path.dirname(root)))),
    "job_script_sha256": script_sha,
    "submit_epoch": int(submit_epoch),
    "submission_nonce": nonce,
    "request": {
        "project": project, "queue": queue, "nodes": int(nodes),
        "elapstim_req_s": int(walltime_s),
        "calibration_rratio": int(rratio),
        "calibration_protocol": protocol,
    },
    "preflight": captures,
    "dry_run": bool(int(dry_run)),
}
with open(os.path.join(root, "pre-submit.json"), "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY

if [[ "$preflight_rc" -ne 0 ]]; then
  echo "one or more preflight captures failed; qsub not executed" >&2
  exit 3
fi

export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE,IZANAGI_CALIBRATION_RRATIO=$RRATIO"
if [[ "$PROTOCOL_EXPLICIT" -eq 1 ]]; then
  export_spec+=",IZANAGI_CALIBRATION_PROTOCOL=$PROTOCOL"
fi
SCHEDULER_STDOUT="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stdout"
SCHEDULER_STDERR="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stderr"
if [[ "$JOB_SCRIPT" != /* ]]; then
  # Keep directory-name newlines; remove only pwd's newline and the sentinel.
  CALLER_CWD=$(pwd -P && printf '.')
  CALLER_CWD=${CALLER_CWD%$'\n.'}
  JOB_SCRIPT="$CALLER_CWD/$JOB_SCRIPT"
fi
qsub_cmd=(qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR" -v "$export_spec" "$JOB_SCRIPT")
printf 'qsub command:'
printf ' %q' "${qsub_cmd[@]}"
printf '\n'

if [[ "$DRY_RUN" -eq 1 ]]; then
  REQUEST_ID="dry-run-$NONCE"
  printf '%s\n' "dry-run: qsub was not executed" >"$SUBMISSION_DIR/qsub.stdout"
  : >"$SUBMISSION_DIR/qsub.stderr"
  printf '0\n' >"$SUBMISSION_DIR/qsub.rc"
else
  set +e
  ( cd -- "$REPO_ROOT" && "${qsub_cmd[@]}" ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"
  qsub_rc=$?
  set -e
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
        print(tokens[0])
    else:
        raise SystemExit(2)
PY
  ) || { echo "qsub succeeded but request ID could not be parsed" >&2; exit 4; }
fi

python3 - "$SUBMISSION_DIR/pre-submit.json" "$SUBMISSION_DIR/submit-receipt.json" "$REQUEST_ID" <<'PY'
import json
import sys
source, target, request_id = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    pre = json.load(handle)
request = pre["request"]
payload = {
    "schema_version": "pegasus-submit-receipt/v1",
    "submission_nonce": pre["submission_nonce"],
    "source_commit": pre["source_commit"],
    "job_script_sha256": pre["job_script_sha256"],
    "qsub": {
        "request_id": request_id,
        "submit_epoch": pre["submit_epoch"],
        "queue": request["queue"],
        "project": request["project"],
        "nodes": request["nodes"],
        "elapstim_req_s": request["elapstim_req_s"],
    },
    "calibration": {
        "protocol": request["calibration_protocol"],
        "workload": {"ycsb_rratio": str(request["calibration_rratio"])},
    },
    "preflight": pre["preflight"],
    "dry_run": pre["dry_run"],
}
with open(target, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY

echo "submit receipt: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
