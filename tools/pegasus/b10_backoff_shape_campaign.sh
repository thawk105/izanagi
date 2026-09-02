#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=12:00:00
#PBS -N izanagi-b10-shape
#PBS --accept-sigterm=yes
set -Eeuo pipefail
umask 077
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP
unset IZANAGI_OFFICIAL_OUTPUT_ROOT
export IZANAGI_B10_BINARY_PATH_POLICY="b10-macro-prefix-map-no-rpath/v1"

bootstrap_fail() {
  echo "B10 job bootstrap failed: $*" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" ]] || bootstrap_fail "PBS envelope missing"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || bootstrap_fail "unsafe PBS_JOBID"
[[ "${IZANAGI_B10_NONCE:-}" =~ ^[0-9a-f]{32}$ ]] || bootstrap_fail "submission nonce missing"
[[ "${IZANAGI_B10_SOURCE_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || bootstrap_fail "source commit missing"
[[ "${IZANAGI_B10_PREREG_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || bootstrap_fail "prereg commit missing"
[[ "${IZANAGI_B10_PHASE:-}" =~ ^(build|verify|perf|probe|verify-perf)$ ]] || bootstrap_fail "phase missing"
if [[ "$IZANAGI_B10_PHASE" == build || "$IZANAGI_B10_PHASE" == probe ]]; then
  [[ -z "${IZANAGI_B10_WORKLOAD:-}" ]] || bootstrap_fail "build/probe phase has workload"
else
  [[ "${IZANAGI_B10_WORKLOAD:-}" =~ ^(write-heavy|balanced|read-heavy)$ ]] \
    || bootstrap_fail "verify/perf/verify-perf workload missing"
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || bootstrap_fail "cannot resolve repository"
[[ -d "$REPO_ROOT/.git" || -f "$REPO_ROOT/.git" ]] || bootstrap_fail "PBS_O_WORKDIR is not a repository"
GIT_COMMON_DIR=$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir) \
  || bootstrap_fail "cannot resolve git common dir"
[[ "$GIT_COMMON_DIR" == /* ]] || bootstrap_fail "git common dir is not absolute"
GIT_COMMON_REPO=${GIT_COMMON_DIR%/.git}
DURABLE_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/b10-backoff-shape/submissions"
OUTPUT_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/b10-backoff-shape/official-output"
[[ "$DURABLE_ROOT" != "$REPO_ROOT" && "$DURABLE_ROOT" != "$REPO_ROOT/"* \
    && "$DURABLE_ROOT" != "$GIT_COMMON_REPO" && "$DURABLE_ROOT" != "$GIT_COMMON_REPO/"* ]] \
  || bootstrap_fail "durable root resolves inside a repository"
[[ "$OUTPUT_ROOT" != "$REPO_ROOT" && "$OUTPUT_ROOT" != "$REPO_ROOT/"* \
    && "$OUTPUT_ROOT" != "$GIT_COMMON_REPO" && "$OUTPUT_ROOT" != "$GIT_COMMON_REPO/"* ]] \
  || bootstrap_fail "official output root resolves inside a repository"
SUBMISSION_DIR="$DURABLE_ROOT/$IZANAGI_B10_NONCE"
SUBMIT_RECEIPT="$SUBMISSION_DIR/submit-receipt.json"

PY=""
for candidate in python3 python3.10 python3.11 python3.12 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY=$(realpath -e -- "$resolved")
    break
  fi
done
[[ -n "$PY" ]] || bootstrap_fail "Python >=3.10 unavailable"

ATTEMPTS_ROOT="$SUBMISSION_DIR/job-attempts"
mkdir -p -m 0700 -- "$ATTEMPTS_ROOT" || bootstrap_fail "cannot create attempt parent"
ATTEMPT_ID=${PBS_JOBID#0:}
ATTEMPT_DIR="$ATTEMPTS_ROOT/$ATTEMPT_ID"
mkdir -m 0700 -- "$ATTEMPT_DIR" || bootstrap_fail "attempt create-only failed"
set -o noclobber

CURRENT_STAGE=receipt
failure_written=0
write_failure() {
  local rc=$1 stage=$2 message=$3
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    "$PY" -I -B - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" \
      "$message" "$IZANAGI_B10_PHASE" "${IZANAGI_B10_WORKLOAD:-}" <<'PY' || true
import json
import sys
import time
path, job, rc, stage, message, phase, workload = sys.argv[1:]
payload = {
    "schema_version": "pegasus-b10-job-failure/v1",
    "pbs_jobid": job,
    "rc": int(rc),
    "stage": stage,
    "message": message,
    "phase": phase,
    "workload": workload or None,
    "recorded_epoch": int(time.time()),
}
try:
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
except FileExistsError:
    pass
PY
  fi
}
on_err() {
  local rc=$? line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "$CURRENT_STAGE" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR
on_signal() {
  local name=$1 number=$2
  local rc=$((128 + number))
  trap - ERR INT TERM HUP
  write_failure "$rc" signal "received $name"
  exit "$rc"
}
trap 'on_signal INT 2' INT
trap 'on_signal TERM 15' TERM
trap 'on_signal HUP 1' HUP

for ((receipt_wait=0; receipt_wait<60; receipt_wait++)); do
  [[ -f "$SUBMIT_RECEIPT" && ! -L "$SUBMIT_RECEIPT" ]] && break
  sleep 1
done
if [[ ! -f "$SUBMIT_RECEIPT" || -L "$SUBMIT_RECEIPT" ]]; then
  write_failure 2 receipt "submit receipt did not appear within 60 seconds"
  exit 2
fi

receipt_values=$(
  "$PY" -I -B - "$SUBMIT_RECEIPT" "$IZANAGI_B10_NONCE" "$PBS_JOBID" \
    "$IZANAGI_B10_SOURCE_COMMIT" "$IZANAGI_B10_PREREG_COMMIT" \
    "$IZANAGI_B10_PHASE" "${IZANAGI_B10_WORKLOAD:-}" <<'PY'
import json
import re
import sys

def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value

(path, nonce, pbs_jobid, source, prereg, phase, workload) = sys.argv[1:]
with open(path, encoding="utf-8") as stream:
    doc = json.load(stream, object_pairs_hook=no_duplicates)
expected_keys = {
    "schema_version", "source_commit", "prereg_commit", "nonce", "request_id",
    "dry_run", "submitted_epoch", "job_script_path", "job_script_sha256",
    "phase", "workload", "request",
}
if type(doc) is not dict or set(doc) != expected_keys:
    raise SystemExit("receipt key set mismatch")
if doc["schema_version"] != "pegasus-b10-submit-receipt/v2" or doc["dry_run"] is not False:
    raise SystemExit("real v2 receipt required")
expected_workload = workload or None
if (doc["nonce"] != nonce or doc["source_commit"] != source
        or doc["prereg_commit"] != prereg or doc["phase"] != phase
        or doc["workload"] != expected_workload):
    raise SystemExit("receipt environment binding mismatch")
if re.fullmatch(r"[0-9a-f]{32}", doc["nonce"]) is None:
    raise SystemExit("receipt nonce invalid")
if re.fullmatch(r"[0-9a-f]{64}", doc["job_script_sha256"]) is None:
    raise SystemExit("receipt script SHA invalid")
if doc["job_script_path"] != "tools/pegasus/b10_backoff_shape_campaign.sh":
    raise SystemExit("receipt script path mismatch")
if type(doc["submitted_epoch"]) is not int or doc["submitted_epoch"] <= 0:
    raise SystemExit("receipt timestamp invalid")
request = doc["request"]
if request != {"project": "SFC", "queue": "gen_S", "nodes": 1,
               "elapstim_req_s": 43200}:
    raise SystemExit("receipt PBS request mismatch")
def normalize(value):
    return value.removeprefix("0:").rstrip(".")
if type(doc["request_id"]) is not str or normalize(doc["request_id"]) != normalize(pbs_jobid):
    raise SystemExit("receipt request ID mismatch")
print(doc["request_id"])
print(doc["job_script_sha256"])
PY
) || { write_failure 2 receipt "submit receipt failed strict validation"; exit 2; }
readarray -t RECEIPT_VALUES <<<"$receipt_values"
[[ ${#RECEIPT_VALUES[@]} -eq 2 ]] || { write_failure 2 receipt "receipt output shape invalid"; exit 2; }
RECEIPT_REQUEST_ID=${RECEIPT_VALUES[0]}
RECEIPT_SCRIPT_SHA256=${RECEIPT_VALUES[1]}

CURRENT_STAGE=source-identity
CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})
[[ "$CURRENT_COMMIT" == "$IZANAGI_B10_SOURCE_COMMIT" ]] \
  || { write_failure 2 source-identity "queued source HEAD drifted"; exit 2; }
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] \
  || { write_failure 2 source-identity "repository working tree is dirty"; exit 2; }
git -C "$REPO_ROOT" merge-base --is-ancestor \
  "$IZANAGI_B10_PREREG_COMMIT" "$CURRENT_COMMIT" \
  || { write_failure 2 source-identity "prereg commit is not an ancestor"; exit 2; }
SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
EXECUTING_SCRIPT_SHA256=$(sha256sum "$SCRIPT_PATH" | awk '{print $1}')
COMMITTED_SCRIPT_SHA256=$(
  git -C "$REPO_ROOT" cat-file blob \
    "$CURRENT_COMMIT:tools/pegasus/b10_backoff_shape_campaign.sh" | sha256sum | awk '{print $1}'
)
[[ "$EXECUTING_SCRIPT_SHA256" == "$RECEIPT_SCRIPT_SHA256" \
    && "$COMMITTED_SCRIPT_SHA256" == "$RECEIPT_SCRIPT_SHA256" ]] \
  || { write_failure 2 source-identity "job script SHA binding mismatch"; exit 2; }

CURRENT_STAGE=allocation
QSTAT_JOBID=${PBS_JOBID#0:}
qstat_rc=0
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-f.stdout" \
  2>"$ATTEMPT_DIR/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$ATTEMPT_DIR/qstat-f.rc"
HOSTNAME_SHORT=$(hostname)
HOSTNAME_FQDN=$(hostname -f)
qstat_values=$(
  "$PY" -I -B - "$ATTEMPT_DIR/qstat-f.stdout" "$qstat_rc" \
    "$RECEIPT_REQUEST_ID" "$HOSTNAME_SHORT" "$HOSTNAME_FQDN" <<'PY'
import re
import subprocess
import sys
path, rc, request_id, short, fqdn = sys.argv[1:]
if rc != "0":
    raise SystemExit("qstat failed")
text = open(path, encoding="utf-8", errors="replace").read()
def normalize(value):
    return value.removeprefix("0:").rstrip(".")
requests = [normalize(item) for item in
            re.findall(r"(?im)^\s*Request ID\s*[:=]\s*(\S+)\s*$", text)]
if requests != [normalize(request_id)]:
    raise SystemExit("request ID mismatch")
assigned = None
section = re.search(r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)", text)
if section:
    assigned = section.group(1)
if assigned is None:
    for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
        match = re.search(rf"(?im)^\s*{key}\s*=\s*([^\n]+)", text)
        if match:
            assigned = re.split(r"[:+/,()\s]", match.group(1).strip().lstrip("("))[0]
            break
if assigned not in {short, fqdn}:
    raise SystemExit("assigned host mismatch")
starts = re.findall(r"(?im)^\s*Started Request Time\s*=\s*(.+?)\s*$", text)
if len(starts) != 1:
    raise SystemExit("scheduler start time missing")
parsed = subprocess.run(["date", "-d", starts[0], "+%s"], capture_output=True, text=True)
if parsed.returncode != 0 or not parsed.stdout.strip().isdigit():
    raise SystemExit("scheduler start time unparsable")
limits = re.findall(r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)", text)
remaining = re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$", text)
if len(limits) != 1 or len(remaining) != 1 or int(limits[0]) <= 0:
    raise SystemExit("scheduler Elapse fields unavailable")
print(assigned)
print(parsed.stdout.strip())
print(int(limits[0]))
print(int(remaining[0]))
PY
) || { write_failure 2 allocation "qstat request/host/start/elapse binding unavailable"; exit 2; }
readarray -t QSTAT_VALUES <<<"$qstat_values"
[[ ${#QSTAT_VALUES[@]} -eq 4 ]] || { write_failure 2 allocation "qstat output shape invalid"; exit 2; }
SCHEDULER_STARTED_EPOCH=${QSTAT_VALUES[1]}
SCHEDULER_ELAPSE_LIMIT_S=${QSTAT_VALUES[2]}
SCHEDULER_REMAINING_ELAPSE_S=${QSTAT_VALUES[3]}
[[ "$SCHEDULER_ELAPSE_LIMIT_S" -eq 43200 ]] \
  || { write_failure 2 allocation "actual scheduler Elapse limit differs from receipt"; exit 2; }

CURRENT_STAGE=reservation
REQUESTED_S=$SCHEDULER_ELAPSE_LIMIT_S
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
BOOT_ID=$(< /proc/sys/kernel/random/boot_id)
[[ -n "$BOOT_ID" ]] || { write_failure 2 reservation "boot ID unavailable"; exit 2; }
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="${QSTAT_VALUES[0]}"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$COMMITTED_SCRIPT_SHA256"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_B10_NONCE"

export TMPDIR="/scr/${PBS_JOBID//:/_}-b10"
mkdir "$TMPDIR" || { write_failure 2 scratch "scratch create-only failed"; exit 2; }
cleanup() {
  find "$TMPDIR" -depth -delete 2>/dev/null || true
}
trap cleanup EXIT

if [[ "$IZANAGI_B10_PHASE" != probe ]]; then
  CURRENT_STAGE=dependencies
  readarray -t DEPENDENCY_VALUES < <("$PY" -I -B - "$REPO_ROOT/tools/pegasus/policy.json" <<'PY'
import json
import re
import sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
for prefix in ("gflags", "glog"):
    path = policy[f"{prefix}_source_path"]
    head = policy[f"{prefix}_expected_head"]
    if not isinstance(path, str) or not path.startswith("/"):
        raise SystemExit(f"invalid {prefix} source path")
    if not isinstance(head, str) or re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise SystemExit(f"invalid {prefix} source head")
    print(path)
    print(head)
PY
  )
  [[ ${#DEPENDENCY_VALUES[@]} -eq 4 ]] || { write_failure 2 dependencies "dependency policy invalid"; exit 2; }
  GFLAGS_SOURCE=${DEPENDENCY_VALUES[0]}
  GFLAGS_HEAD=${DEPENDENCY_VALUES[1]}
  GLOG_SOURCE=${DEPENDENCY_VALUES[2]}
  GLOG_HEAD=${DEPENDENCY_VALUES[3]}
  [[ "$(git -C "$GFLAGS_SOURCE" rev-parse HEAD)" == "$GFLAGS_HEAD" \
      && -z "$(git -C "$GFLAGS_SOURCE" status --porcelain --untracked-files=all)" ]] \
    || { write_failure 2 dependencies "gflags source is not pinned-clean"; exit 2; }
  [[ "$(git -C "$GLOG_SOURCE" rev-parse HEAD)" == "$GLOG_HEAD" \
      && -z "$(git -C "$GLOG_SOURCE" status --porcelain --untracked-files=all)" ]] \
    || { write_failure 2 dependencies "glog source is not pinned-clean"; exit 2; }

  GFLAGS_INSTALL="$TMPDIR/gflags-install"
  GLOG_INSTALL="$TMPDIR/glog-install"
  cmake -S "$GFLAGS_SOURCE" -B "$TMPDIR/gflags-build" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF \
    -DCMAKE_INSTALL_PREFIX="$GFLAGS_INSTALL"
  cmake --build "$TMPDIR/gflags-build" -j 48
  cmake --install "$TMPDIR/gflags-build"
  cmake -S "$GLOG_SOURCE" -B "$TMPDIR/glog-build" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF \
    -DWITH_UNWIND=OFF -DCMAKE_PREFIX_PATH="$GFLAGS_INSTALL" \
    -DCMAKE_INSTALL_PREFIX="$GLOG_INSTALL"
  cmake --build "$TMPDIR/glog-build" -j 48
  cmake --install "$TMPDIR/glog-build"
  export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL:$GLOG_INSTALL"
fi

mkdir -p -m 0700 -- \
  "$OUTPUT_ROOT/campaigns" \
  "$OUTPUT_ROOT/campaign-locks" \
  "$OUTPUT_ROOT/env/pegasus/claims"
export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"
driver_argv=(
  "$PY" -B -m orchestrator.campaign.b10_backoff_shape_sweep
  --phase "$IZANAGI_B10_PHASE"
  --prereg-commit "$IZANAGI_B10_PREREG_COMMIT"
  --submission-receipt "$SUBMIT_RECEIPT"
)
if [[ -n "${IZANAGI_B10_WORKLOAD:-}" ]]; then
  driver_argv+=(--workload "$IZANAGI_B10_WORKLOAD")
fi
CURRENT_STAGE="driver-$IZANAGI_B10_PHASE"
driver_rc=0
(cd "$REPO_ROOT" && "${driver_argv[@]}") \
  >"$ATTEMPT_DIR/driver.stdout" 2>"$ATTEMPT_DIR/driver.stderr" || driver_rc=$?

CURRENT_STAGE=job-result
"$PY" -I -B - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$driver_rc" \
  "$IZANAGI_B10_PHASE" "${IZANAGI_B10_WORKLOAD:-}" "$CURRENT_COMMIT" \
  "$RECEIPT_REQUEST_ID" "$IZANAGI_B10_NONCE" "$SUBMIT_RECEIPT" \
  "$REQUESTED_S" "$SCHEDULER_REMAINING_ELAPSE_S" <<'PY'
import json
import sys
import time
(path, job, rc, phase, workload, source, request, nonce, receipt,
 requested_s, remaining_s) = sys.argv[1:]
payload = {
    "schema_version": "pegasus-b10-job-result/v1",
    "pbs_jobid": job,
    "driver_rc": int(rc),
    "phase": phase,
    "workload": workload or None,
    "source_commit": source,
    "request_id": request,
    "nonce": nonce,
    "submission_receipt": receipt,
    "scheduler_elapse_limit_s": int(requested_s),
    "scheduler_remaining_elapse_at_start_s": int(remaining_s),
    "completed_epoch": int(time.time()),
}
with open(path, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
    stream.write("\n")
PY
if [[ "$driver_rc" -ne 0 ]]; then
  write_failure "$driver_rc" "driver-$IZANAGI_B10_PHASE" "formal driver returned nonzero"
fi
exit "$driver_rc"
