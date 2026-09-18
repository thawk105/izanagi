#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS --accept-sigterm=yes
set -Eeuo pipefail
umask 077

# Early refusals do not replace the frozen driver's authoritative gates.
GATE=bootstrap REASON=unhandled_failure
DRIVER_RC= HOST_OBSERVED= SIGNAL_RC=0
printf -v STARTED_EPOCH '%(%s)T' -1

fail() {
  printf '{"gate":"%s","reason":"%s"}\n' "$2" "$3" >&2
  GATE=$2 REASON=$3
  exit "$1"
}

select_python() {
  local candidate resolved
  PY=
  for candidate in python3.10 python3.11 python3.12 python3; do
    resolved=$(command -v -- "$candidate" 2>/dev/null) || continue
    resolved=$(realpath -e -- "$resolved" 2>/dev/null) || continue
    [[ -x "$resolved" ]] || continue
    if "$resolved" -I -B -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
      PY=$resolved
      return 0
    fi
  done
  fail 2 interpreter python_unavailable
}

clean_environment() {
  export PATH=/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin
  unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH || fail 2 environment cleanup_failed
  local name
  for name in ${!GIT_@}; do
    unset "$name" || fail 2 environment cleanup_failed
  done
}

walltime_seconds() {
  local value=$1
  [[ "$value" =~ ^[0-9]{2}:[0-5][0-9]:[0-5][0-9]$ ]] || fail 2 bootstrap invalid_walltime
  DURATION=$((10#${value:0:2} * 3600 + 10#${value:3:2} * 60 + 10#${value:6:2}))
  (( DURATION > 0 )) || fail 2 bootstrap invalid_walltime
}

window_gate() {
  local now=$1 not_before=$2 not_after=$3 duration=$4
  (( now >= not_before )) || fail 4 window before_window
  (( now + duration <= not_after )) || fail 4 window insufficient_remaining_time
}

read_window_bounds() {
  local bounds
  bounds=$("$PY" -I -B -c '
import datetime, json, sys
spec = json.load(open(sys.argv[1]))
window, = [w for w in spec["windows"] if w["window_id"] == sys.argv[2]]
print(*(int(datetime.datetime.fromisoformat(window[k].replace("Z", "+00:00")).timestamp()) for k in ("not_before", "not_after")))
' "$1" "$2" 2>/dev/null) || fail 4 window invalid_window
  read -r NOT_BEFORE NOT_AFTER <<<"$bounds"
  [[ "$NOT_BEFORE" =~ ^[0-9]+$ && "$NOT_AFTER" =~ ^[0-9]+$ ]] || fail 4 window invalid_window
}

check_binaries() {
  "$PY" -I -B -c '
import hashlib, json, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
for artifact in json.load(open(root / sys.argv[2]))["artifacts"]:
    binary = root / artifact["binary_relpath"]
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise SystemExit(1)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != artifact["binary_sha256"]:
        raise SystemExit(1)
' "$1" "$2" 2>/dev/null || fail 4 binary missing_or_mismatch
}

bootstrap() {
  local name
  for name in PBS_JOBID PBS_O_WORKDIR FP_NONCE FP_EXPECTED_HEAD FP_SPEC_RELPATH FP_SPEC_SHA256 FP_MODE FP_WINDOW_ID FP_EVIDENCE_DIR FP_ELAPSTIM_REQ; do
    [[ -n "${!name:-}" ]] || fail 2 bootstrap missing_binding
  done
  [[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || fail 2 bootstrap invalid_jobid
  [[ "$FP_NONCE" =~ ^[0-9a-f]{32}$ ]] || fail 2 bootstrap invalid_nonce
  [[ "$FP_EXPECTED_HEAD" =~ ^[0-9a-fA-F]{40}$ ]] || fail 2 bootstrap invalid_head
  [[ "$FP_SPEC_SHA256" =~ ^[0-9a-fA-F]{64}$ ]] || fail 2 bootstrap invalid_sha256
  case "$FP_SPEC_RELPATH" in
    output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json) WORKLOAD=rr95 ;;
    output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json) WORKLOAD=rr50 ;;
    output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json) WORKLOAD=rr5 ;;
    *) fail 2 bootstrap invalid_spec ;;
  esac
  case "$FP_MODE" in
    window) [[ "$FP_WINDOW_ID" == "$WORKLOAD-w1" || "$FP_WINDOW_ID" == "$WORKLOAD-w2" ]] || fail 2 bootstrap invalid_window ;;
    finalize) [[ "$FP_WINDOW_ID" == none ]] || fail 2 bootstrap invalid_window ;;
    *) fail 2 bootstrap invalid_mode ;;
  esac
  [[ "$FP_EVIDENCE_DIR" == /* && -d "$FP_EVIDENCE_DIR" ]] || fail 2 bootstrap invalid_evidence
  walltime_seconds "$FP_ELAPSTIM_REQ"
}

write_result() {
  "$PY" -I -B -c '
import hashlib, json, pathlib, sys, time
(directory, jobid, host, nonce, head, spec, sha, mode, window, driver_rc,
 started, job_rc, gate, reason) = sys.argv[1:]
stdout = pathlib.Path(directory) / "driver.stdout"
payload = dict(schema_version="pegasus-floor-pair-job-result/v1",
 pbs_jobid=jobid, hostname=host, nonce=nonce, expected_head=head,
 spec_relpath=spec, spec_sha256=sha, mode=mode,
 window_id=None if mode == "finalize" else window,
 driver_rc=int(driver_rc) if driver_rc else None,
 driver_stdout_sha256=hashlib.sha256(stdout.read_bytes()).hexdigest() if driver_rc else None,
 started_epoch=int(started), completed_epoch=int(time.time()),
 job_rc=int(job_rc), gate=gate, reason=reason)
with open(pathlib.Path(directory) / "job-result.json", "x") as stream:
    json.dump(payload, stream, sort_keys=True)
    stream.write("\n")
' "$FP_EVIDENCE_DIR" "$PBS_JOBID" "$HOST_OBSERVED" "$FP_NONCE" "$FP_EXPECTED_HEAD" \
    "$FP_SPEC_RELPATH" "$FP_SPEC_SHA256" "$FP_MODE" "$FP_WINDOW_ID" "$DRIVER_RC" \
    "$STARTED_EPOCH" "$1" "$GATE" "$REASON" 2>/dev/null
}

finish_job() {
  local rc=$?
  trap - EXIT ERR
  if ! write_result "$rc"; then
    printf '{"gate":"result","reason":"receipt_failed"}\n' >&2
    if [[ -z "$DRIVER_RC" || "$DRIVER_RC" == 0 ]]; then rc=5; fi
  fi
  exit "$rc"
}

require_compute_hostname() {
  local label=${1%%.*}
  label=${label,,}
  [[ "$label" =~ ^bnode[0-9]+$ ]] || fail 4 site compute_node_required
}

check_time() {
  if [[ "$FP_MODE" == window ]]; then
    local now
    now=$(date -u +%s 2>/dev/null) || fail 4 window clock_unavailable
    window_gate "$now" "$NOT_BEFORE" "$NOT_AFTER" "$DURATION"
  fi
}

prepare_scratch() {
  export TMPDIR=/scr/${PBS_JOBID//:/_}
  mkdir -m 0700 -- "$TMPDIR" 2>/dev/null || fail 4 scratch create_failed
}

build_driver_argv() {
  DRIVER_BOOTSTRAP='import sys; sys.path.insert(0, sys.argv.pop(1)); from orchestrator.campaign.floor_pair_driver import main; raise SystemExit(main())'
  driver_argv=("$PY" -I -B -c "$DRIVER_BOOTSTRAP" "$REPO_ROOT"
    --repo-root "$REPO_ROOT" --spec "$FP_SPEC_RELPATH" --expected-sha256 "$FP_SPEC_SHA256")
  case "$FP_MODE" in
    window) driver_argv+=(--execute-window "$FP_WINDOW_ID") ;;
    finalize) driver_argv+=(--finalize) ;;
  esac
}

record_signal() {
  SIGNAL_RC=$1 WAIT_INTERRUPTED=1
}

run_driver() {
  # Open both streams before starting a child; collisions cannot launch the driver.
  set -o noclobber
  { exec {DRIVER_OUT}>"$FP_EVIDENCE_DIR/driver.stdout"; } 2>/dev/null || fail 4 driver stdout_exists_or_unwritable
  { exec {DRIVER_ERR}>"$FP_EVIDENCE_DIR/driver.stderr"; } 2>/dev/null || fail 4 driver stderr_exists_or_unwritable
  trap 'record_signal 143' TERM
  trap 'record_signal 129' HUP
  trap 'record_signal 130' INT
  (trap - ERR; exec "${driver_argv[@]}") >&"$DRIVER_OUT" 2>&"$DRIVER_ERR" &
  DRIVER_PID=$!
  while :; do
    WAIT_INTERRUPTED=0
    if wait "$DRIVER_PID"; then DRIVER_RC=0; else DRIVER_RC=$?; fi
    (( WAIT_INTERRUPTED )) || break
  done
  exec {DRIVER_OUT}>&- {DRIVER_ERR}>&-
  GATE=driver REASON=completed
  if (( SIGNAL_RC )); then REASON=signal_observed; fi
  JOB_RC=$DRIVER_RC
  if (( JOB_RC == 0 && SIGNAL_RC != 0 )); then JOB_RC=$SIGNAL_RC; fi
}

admit_and_run() {
  GATE=site
  require_compute_hostname "$HOST_OBSERVED"
  GATE=window
  if [[ "$FP_MODE" == window ]]; then
    read_window_bounds "$FP_SPEC_RELPATH" "$FP_WINDOW_ID"
  fi
  check_time
  GATE=scratch
  prepare_scratch
  # Window admission is checked again after scratch preparation.
  GATE=window
  check_time
  GATE=driver
  run_driver
}

bootstrap
clean_environment
select_python
trap finish_job EXIT
trap 'fail 4 "$GATE" unhandled_failure' ERR
GATE=commands
for command_name in git nm pgrep sha256sum hostname date realpath mkdir env; do
  command -v -- "$command_name" >/dev/null 2>&1 || fail 2 commands required_command_missing
done
GATE=checkout
REPO_ROOT=$(realpath -e -- "$PBS_O_WORKDIR" 2>/dev/null) || fail 4 checkout root_unavailable
CANONICAL_ROOT=$(git -C "$REPO_ROOT" rev-parse --show-toplevel 2>/dev/null) || fail 4 checkout root_unavailable
CANONICAL_ROOT=$(realpath -e -- "$CANONICAL_ROOT" 2>/dev/null) || fail 4 checkout root_unavailable
[[ "$REPO_ROOT" == "$CANONICAL_ROOT" ]] || fail 4 checkout root_mismatch
HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit} 2>/dev/null) || fail 4 checkout head_unavailable
[[ "$HEAD" == "$FP_EXPECTED_HEAD" ]] || fail 4 checkout head_mismatch
cd -P -- "$REPO_ROOT" 2>/dev/null || fail 4 checkout root_unavailable
SPEC_HASH=$(sha256sum -- "$FP_SPEC_RELPATH" 2>/dev/null) || fail 4 spec hash_unavailable
[[ "${SPEC_HASH%% *}" == "$FP_SPEC_SHA256" ]] || fail 4 spec hash_mismatch
check_binaries "$REPO_ROOT" "$FP_SPEC_RELPATH"
HOST_OBSERVED=$(hostname 2>/dev/null) || fail 4 site hostname_unavailable
build_driver_argv
admit_and_run
exit "$JOB_RC"
