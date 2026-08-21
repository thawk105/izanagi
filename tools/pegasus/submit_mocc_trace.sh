#!/bin/bash
# ログインノード専用: Mocc trace pilot の source binding と投入前 receipt を固定して qsub する。
set -Eeuo pipefail

usage() {
  cat <<'EOF'
usage: submit_mocc_trace.sh [--dry-run] [--repo-root PATH] [--attempts-root PATH]
                            [--job-script PATH] [--trace-mode {1,0}]
EOF
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)
JOB_SCRIPT="$SCRIPT_DIR/mocc_trace_pilot.sh"
ATTEMPTS_ROOT=""
DRY_RUN=0
TRACE_MODE=1

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
    --trace-mode)
      TRACE_MODE=${2:?}
      [[ "$TRACE_MODE" == 0 || "$TRACE_MODE" == 1 ]] || {
        echo "--trace-mode must be 0 or 1" >&2
        exit 2
      }
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -f "$JOB_SCRIPT" ]]; then
  echo "job script not found: $JOB_SCRIPT" >&2
  exit 2
fi

POLICY="$REPO_ROOT/tools/pegasus/mocc_trace_v1_policy.json"
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  echo "Mocc trace policy not found or is a symlink: $POLICY" >&2
  exit 2
fi

# The workload tuple is parent-selected pilot data; it is not a reproduction of
# any historical T-816 measurement.  Keep that distinction in every receipt.
readarray -t policy_values < <(python3 - "$POLICY" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    policy = json.load(handle)
trace = policy["mocc_trace"]
workload = trace["workload"]
required_workload = {
    "records", "threads", "zipf_skew", "ycsb_rratio", "ycsb_rmw", "extime_s"
}
if set(workload) != required_workload:
    raise SystemExit("mocc_trace.workload keys differ")
if trace["cmake_target"] != "ycsb_mocc.exe":
    raise SystemExit("mocc_trace cmake target differs")
if trace["trace1_defines"] != {"CCBENCH_TRACE": "1"}:
    raise SystemExit("trace1 define differs")
if trace["trace0_defines"] != {"CCBENCH_TRACE": "0"}:
    raise SystemExit("trace0 define differs")
for key in ("base_oid", "new_oid"):
    value = trace[key]
    if type(value) is not str or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise SystemExit(f"{key} is not a full lowercase OID")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(policy["pilot_walltime_s"])
print(policy["finalize_reserve_s"])
print(policy["expected_cpu_model"])
print(policy["expected_physical_cores"])
print(trace["base_oid"])
print(trace["new_oid"])
print(trace["cmake_target"])
print(json.dumps(workload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
print(policy["third_party_cache_env"])
print(policy["pilot_walltime"])
PY
)
if [[ ${#policy_values[@]} -ne 13 ]]; then
  echo "Mocc trace policy parse failed" >&2
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
WALLTIME_S=${policy_values[3]}
FINALIZE_RESERVE_S=${policy_values[4]}
EXPECTED_CPU=${policy_values[5]}
EXPECTED_CORES=${policy_values[6]}
BASE_OID=${policy_values[7]}
NEW_OID=${policy_values[8]}
CMAKE_TARGET=${policy_values[9]}
WORKLOAD_JSON=${policy_values[10]}
THIRD_PARTY_CACHE_ENV=${policy_values[11]}
PILOT_WALLTIME=${policy_values[12]}
if [[ ! "$THIRD_PARTY_CACHE_ENV" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "third_party_cache_env is not a valid environment variable name" >&2
  exit 2
fi

if [[ ! -d "$REPO_ROOT/external/ccbench" ]]; then
  echo "Mocc trace submodule is missing: $REPO_ROOT/external/ccbench" >&2
  exit 2
fi
# Only prove that the user-created commit exists.  Do not checkout, reset, clean,
# stash, move, or otherwise mutate the submodule working tree on the login node.
CCBENCH_RESOLVED=$(git -C "$REPO_ROOT/external/ccbench" rev-parse "$NEW_OID^{commit}") || {
  echo "required Mocc trace commit is absent from external/ccbench: $NEW_OID" >&2
  exit 2
}
if [[ "$CCBENCH_RESOLVED" != "$NEW_OID" ]]; then
  echo "required Mocc trace commit resolved unexpectedly: $CCBENCH_RESOLVED" >&2
  exit 2
fi

# Outer source identity is frozen before any submission staging is created.
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD) || exit 2
if [[ ! "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "cannot resolve a full outer source commit" >&2
  exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]]; then
  echo "working tree is dirty; Mocc trace submission aborted" >&2
  exit 2
fi
JOB_SCRIPT_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
SUBMIT_EPOCH=$(date +%s)
NONCE=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)

if [[ -z "$ATTEMPTS_ROOT" ]]; then
  ATTEMPTS_ROOT="$REPO_ROOT/output/env/pegasus/mocc-trace/attempts"
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
  capture_required qstat_Q qstat -Q || preflight_rc=1
  capture_required pegasusinfo pegasinfo || preflight_rc=1
  capture_required rbudgetcheck rbudgetcheck || preflight_rc=1
  capture_required check_quota check_quota || preflight_rc=1
fi

THIRD_PARTY_CACHE_VALUE="${!THIRD_PARTY_CACHE_ENV:-}"
if [[ "$DRY_RUN" -eq 0 && -z "$THIRD_PARTY_CACHE_VALUE" ]]; then
  echo "$THIRD_PARTY_CACHE_ENV is required for compute-side third-party hydrate" >&2
  exit 2
fi
EXPORT_SPEC="IZANAGI_SUBMISSION_NONCE=$NONCE,IZANAGI_MOCC_TRACE_MODE=$TRACE_MODE"
if [[ -n "$THIRD_PARTY_CACHE_VALUE" ]]; then
  EXPORT_SPEC+=",$THIRD_PARTY_CACHE_ENV=$THIRD_PARTY_CACHE_VALUE"
fi
qsub_cmd=(qsub -v "$EXPORT_SPEC" "$JOB_SCRIPT")

python3 - "$SUBMISSION_DIR" "$SOURCE_COMMIT" "$JOB_SCRIPT" "$JOB_SCRIPT_SHA256" \
  "$SUBMIT_EPOCH" "$NONCE" "$PROJECT" "$QUEUE" "$NODES" "$WALLTIME_S" \
  "$FINALIZE_RESERVE_S" "$EXPECTED_CPU" "$EXPECTED_CORES" "$BASE_OID" "$NEW_OID" \
  "$CMAKE_TARGET" "$WORKLOAD_JSON" "$POLICY" "$TRACE_MODE" "$DRY_RUN" \
  "${qsub_cmd[@]}" <<'PY'
import json
import os
import sys

(root, source_commit, script, script_sha, submit_epoch, nonce, project, queue,
 nodes, walltime_s, reserve_s, expected_cpu, expected_cores, base_oid, new_oid,
 cmake_target, workload_json, policy_path, trace_mode, dry_run, *qsub_argv) = sys.argv[1:]
with open(policy_path, encoding="utf-8") as handle:
    policy = json.load(handle)
mocc_trace = dict(policy["mocc_trace"])
mocc_trace["trace_mode"] = int(trace_mode)
mocc_trace["workload"] = json.loads(workload_json)
mocc_trace["workload_note"] = (
    "parent-selected pilot workload; not a reproduction of historical T-816 measurements"
)
mocc_trace["source_binding"] = {
    "base_oid": base_oid,
    "new_oid": new_oid,
    "cmake_target": cmake_target,
}
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
        "project": project,
        "queue": queue,
        "nodes": int(nodes),
        "elapstim_req_s": int(walltime_s),
        "finalize_reserve_s": int(reserve_s),
        "qsub_argv": qsub_argv,
    },
    "policy": {
        "path": os.path.relpath(policy_path, os.path.dirname(os.path.dirname(os.path.dirname(root)))),
        "pilot_walltime": policy["pilot_walltime"],
        "pilot_walltime_s": int(policy["pilot_walltime_s"]),
        "expected_cpu_model": expected_cpu,
        "expected_physical_cores": int(expected_cores),
    },
    "mocc_trace": mocc_trace,
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
  "${qsub_cmd[@]}" >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"
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
        "finalize_reserve_s": request["finalize_reserve_s"],
        "argv": request["qsub_argv"],
    },
    "preflight": pre["preflight"],
    "policy": pre["policy"],
    "mocc_trace": pre["mocc_trace"],
    "dry_run": pre["dry_run"],
}
with open(target, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY

echo "submit receipt: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
