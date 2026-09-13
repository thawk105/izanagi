#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=02:00:00
#PBS -b 1

# C3-7 予約式 (秒):
# TSC(10) + cooldown_max(1200) + points(5)*sweep_reps(3)*120
# + noise_reps(10)*120 + 2*sweep_reps(3)*120
# + build_cap(CCBench=900 + gflags=60 + glog=120)(1080)
# + finalize_reserve(600) = 6610。要求 7200 秒はこれを上回る。
set -Eeuo pipefail
umask 077

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi

# (i) helper・使い捨て build 専用。永続成果物の唯一コピーは repo output に置く。
# CMake の PATH 型 cache 値は ':' を ';' に正規化するため、cmake 経路の job dir だけを無害化する。
# repo 側 job-staging と receipt の PBS_JOBID は raw 値を維持する。
export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || exit 2
TOOLS="$REPO_ROOT/tools/pegasus"
POLICY="$TOOLS/policy.json"
CALIBRATION_POLICY="$TOOLS/policies/calibration_v1.json"
ATTEMPTS_ROOT="$REPO_ROOT/output/env/pegasus/calibration/attempts"
JOB_STAGING_ROOT="$REPO_ROOT/output/env/pegasus/calibration/job-staging"
mkdir -p "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"
# calibrator は attempts/<job-id> を自分で create-only 作成する。wrapper は別 namespace。
ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"
if ! mkdir "$ATTEMPT_DIR"; then
  echo "attempt already exists (create-only): $ATTEMPT_DIR" >&2
  exit 2
fi

failure_written=0
CCBENCH_BASE=""
BUILD_SOURCE=""
write_failure() {
  local rc=$1
  local stage=$2
  local message=$3
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    python3 - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" "$message" <<'PY' || true
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
  fi
}
on_err() {
  local rc=$?
  local line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "shell" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR
on_signal() {
  local signal=$1
  trap - ERR INT TERM HUP
  write_failure 128 signal "received $signal"
  exit 128
}
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap 'on_signal HUP' HUP
cleanup_worktree() {
  local original_rc=$?
  trap - EXIT
  if [[ -n "$CCBENCH_BASE" && -n "$BUILD_SOURCE" ]]; then
    git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
      >>"$ATTEMPT_DIR/worktree-cleanup.stdout" 2>>"$ATTEMPT_DIR/worktree-cleanup.stderr" || true
  fi
  exit "$original_rc"
}
trap cleanup_worktree EXIT

if [[ ! -f "$POLICY" ]]; then
  write_failure 2 policy "policy file missing"
  exit 2
fi
if [[ ! -f "$CALIBRATION_POLICY" || -L "$CALIBRATION_POLICY" ]]; then
  write_failure 2 policy "calibration policy file missing"
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
print(calibration["finalize_reserve_s"])
print(p["expected_cpu_model"])
print(p["expected_physical_cores"])
print(p["gflags_source_path"])
print(p["gflags_expected_head"])
print(p["glog_source_path"])
print(p["glog_expected_head"])
for candidate in p["perf_candidates"]:
    print(candidate)
PY
)
[[ ${#policy_values[@]} -ge 12 ]]
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
REQUESTED_S=${policy_values[3]}
FINALIZE_RESERVE_S=${policy_values[4]}
EXPECTED_CPU=${policy_values[5]}
EXPECTED_CORES=${policy_values[6]}
GFLAGS_SOURCE_PATH=${policy_values[7]}
GFLAGS_EXPECTED_HEAD=${policy_values[8]}
GLOG_SOURCE_PATH=${policy_values[9]}
GLOG_EXPECTED_HEAD=${policy_values[10]}
PERF_CANDIDATES=("${policy_values[@]:11}")

if [[ -z "${IZANAGI_SUBMISSION_NONCE:-}" || ! "$IZANAGI_SUBMISSION_NONCE" =~ ^[A-Za-z0-9._-]+$ ]]; then
  write_failure 2 submit_binding "IZANAGI_SUBMISSION_NONCE is missing or unsafe"
  exit 2
fi
if [[ -z "${IZANAGI_CALIBRATION_RRATIO:-}" \
      || "$IZANAGI_CALIBRATION_RRATIO" != "5" \
      && "$IZANAGI_CALIBRATION_RRATIO" != "20" \
      && "$IZANAGI_CALIBRATION_RRATIO" != "50" \
      && "$IZANAGI_CALIBRATION_RRATIO" != "80" \
      && "$IZANAGI_CALIBRATION_RRATIO" != "95" ]]; then
  write_failure 2 submit_binding \
    "IZANAGI_CALIBRATION_RRATIO must be exactly 5, 20, 50, 80, or 95"
  exit 2
fi
CALIBRATION_RRATIO="$IZANAGI_CALIBRATION_RRATIO"
CALIBRATION_PROTOCOL=${IZANAGI_CALIBRATION_PROTOCOL-silo}
if [[ "$CALIBRATION_PROTOCOL" != "silo" \
      && "$CALIBRATION_PROTOCOL" != "mocc" \
      && "$CALIBRATION_PROTOCOL" != "tictoc" ]]; then
  write_failure 2 submit_binding \
    "IZANAGI_CALIBRATION_PROTOCOL must be exactly silo, mocc, or tictoc"
  exit 2
fi
THIRD_PARTY_SOURCE_ROOT="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
if [[ "$THIRD_PARTY_SOURCE_ROOT" != /* \
      || ! -d "$THIRD_PARTY_SOURCE_ROOT" \
      || -L "$THIRD_PARTY_SOURCE_ROOT" ]]; then
  write_failure 2 third_party_source \
    "pinned third-party staging root is unavailable"
  exit 2
fi
for third_party_name in masstree mimalloc googletest; do
  third_party_source="$THIRD_PARTY_SOURCE_ROOT/$third_party_name"
  if [[ ! -d "$third_party_source" || -L "$third_party_source" ]]; then
    write_failure 2 third_party_source \
      "pinned third-party staging source is unavailable: $third_party_name"
    exit 2
  fi
done
if [[ -n "${PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT+x}" ]]; then
  write_failure 2 submit_binding "legacy effective clock tolerance input is forbidden"
  exit 2
fi

# submit receipt は qsub 応答後に同 nonce staging へ追加される。開始競合は 60 秒で打ち切る。
SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE"
SUBMIT_SOURCE="$SUBMISSION_DIR/submit-receipt.json"
for _ in $(seq 1 60); do
  [[ -f "$SUBMIT_SOURCE" ]] && break
  sleep 1
done
if [[ ! -f "$SUBMIT_SOURCE" ]]; then
  write_failure 2 submit_binding "submit receipt did not appear within 60 seconds"
  exit 2
fi
cp "$SUBMIT_SOURCE" "$ATTEMPT_DIR/submit-receipt.json"

# qsub 前の source commit と job script bytes を job 冒頭で再照合する。
CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)
# submit/job receipt 自身は output に増えるため、source 面だけを再照合する。
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all -- . ':(exclude)output')" ]]; then
  write_failure 2 source_identity "working tree became dirty before job start"
  exit 2
fi
CURRENT_SCRIPT_SHA=$(sha256sum "$TOOLS/certify_calibration.sh" | awk '{print $1}')
python3 - "$ATTEMPT_DIR/submit-receipt.json" "$CURRENT_COMMIT" "$CURRENT_SCRIPT_SHA" \
  "$PBS_JOBID" "$PROJECT" "$QUEUE" "$NODES" "$REQUESTED_S" \
  "$CALIBRATION_RRATIO" "$CALIBRATION_PROTOCOL" "$REPO_ROOT" <<'PY'
import json
import sys
(path, commit, script_sha, job_id, project, queue, nodes, requested_s,
 rratio, protocol, repo_root) = sys.argv[1:]
sys.path.insert(0, repo_root)
from orchestrator.calibrator.schema_v2 import normalize_request_id
with open(path, encoding="utf-8") as handle:
    doc = json.load(handle)
qsub = doc["qsub"]
checks = {
    "dry_run": doc.get("dry_run") is False,
    "source_commit": doc.get("source_commit") == commit,
    "job_script_sha256": doc.get("job_script_sha256") == script_sha,
    "request_id": (
        isinstance(qsub.get("request_id"), str)
        and normalize_request_id(qsub["request_id"]) == normalize_request_id(job_id)
    ),
    "project": qsub.get("project") == project,
    "queue": qsub.get("queue") == queue,
    "nodes": qsub.get("nodes") == int(nodes),
    "walltime": qsub.get("elapstim_req_s") == int(requested_s),
    "calibration_rratio": (
        doc.get("calibration", {}).get("workload", {}).get("ycsb_rratio")
        == str(rratio)
    ),
    "calibration_protocol": doc.get("calibration", {}).get("protocol") == protocol,
}
if not all(checks.values()):
    raise SystemExit("submit binding mismatch: " + repr(checks))
PY

# (ii) allocation receipt 素材。qstat 不可/host 不明も raw と unavailable を残して停止する。
qstat_rc=0
QSTAT_JOBID=${PBS_JOBID#0:}
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-f.stdout" 2>"$ATTEMPT_DIR/qstat-f.stderr" \
  || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$ATTEMPT_DIR/qstat-f.rc"
HOSTNAME_SHORT=$(hostname)
HOSTNAME_FQDN=$(hostname -f)
printf '%s\n' "$HOSTNAME_SHORT" >"$ATTEMPT_DIR/hostname.stdout"
printf '%s\n' "$HOSTNAME_FQDN" >"$ATTEMPT_DIR/hostname-f.stdout"
HOSTNAME_OBSERVED="$HOSTNAME_SHORT"
python3 - "$ATTEMPT_DIR/topology.json" <<'PY'
import json
import os
import sys
import pathlib

visible = sorted(os.sched_getaffinity(0))
pairs = set()
for cpu in visible:
    root = pathlib.Path("/sys/devices/system/cpu") / f"cpu{cpu}" / "topology"
    try:
        package = int((root / "physical_package_id").read_text().strip())
        core = int((root / "core_id").read_text().strip())
    except (OSError, ValueError):
        raise SystemExit("cannot derive physical core topology")
    pairs.add((package, core))
payload = {
    "affinity_cpus": visible,
    "cpuset_size": len(visible),
    "physical_visible": len(pairs),
    "ht_off": len(visible) == len(pairs),
}
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

readarray -t qstat_values < <(python3 - "$ATTEMPT_DIR/qstat-f.stdout" "$HOSTNAME_OBSERVED" "$qstat_rc" <<'PY'
import re
import subprocess
import sys
path, observed, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
if rc == "0":
    for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
        m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
        if m:
            raw = m.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    if assigned == "unavailable":
        # NQSV reports the allocation as a section, not an inline key=value field.
        m = re.search(
            r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
            text,
        )
        if m and m.group(1).lower() != "none":
            assigned = m.group(1)
    if assigned == "unavailable" and observed.split(".")[0] in text:
        assigned = observed.split(".")[0]
    for key in ("stime", "start_time", "start", "Started Request Time"):
        m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not m:
            continue
        raw = m.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = raw
            break
        proc = subprocess.run(["date", "-d", raw, "+%s"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip().isdigit():
            started = proc.stdout.strip()
            break
print(assigned)
print(started)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable || "$SCHEDULER_STARTED_EPOCH" == unavailable ]]; then
  python3 - "$ATTEMPT_DIR/allocation-unavailable.json" "$PBS_JOBID" "$qstat_rc" \
    "$ASSIGNED_HOST" "$HOSTNAME_OBSERVED" "$SCHEDULER_STARTED_EPOCH" <<'PY'
import json, sys, time
path, job, rc, assigned, host, started = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump({"pbs_jobid": job, "qstat_rc": int(rc), "assigned_host_qstat": assigned,
               "hostname_observed": host, "scheduler_started_epoch": started,
               "recorded_epoch": int(time.time())}, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY
  write_failure 2 allocation "qstat allocation/start binding unavailable"
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

BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$HOSTNAME_OBSERVED"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$CURRENT_SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"
python3 - "$ATTEMPT_DIR/reservation.json" <<'PY'
import json, os, sys, time
keys = ("JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
        "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE")
payload = {key.lower(): os.environ["IZANAGI_RESERVATION_" + key] for key in keys}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    payload[key] = int(payload[key])
payload["recorded_epoch"] = int(time.time())
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

# C3-3 step 1: build の熱状態に汚される前の静的 profile を保存する。
timeout 120 python3 "$TOOLS/run_probe.py" --output "$ATTEMPT_DIR/attestation-static.json" \
  >"$ATTEMPT_DIR/attestation-static.stdout" 2>"$ATTEMPT_DIR/attestation-static.stderr"

# (iii) Pegasus 実測: gcc/cmake module は存在しない。既定 module 環境を変更せず記録し、
# PATH 上の system gcc/g++/cmake を実体・version とともに固定する。
module -t list >"$ATTEMPT_DIR/module-list.stdout" 2>"$ATTEMPT_DIR/module-list.stderr"

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)
CMAKE_PATH=$(realpath "$(command -v cmake)")
if ! NM_PATH=$(realpath /usr/bin/nm); then
  write_failure 2 toolchain "fixed nm path cannot be resolved"
  exit 2
fi
if [[ ! -f "$NM_PATH" || ! -x "$NM_PATH" ]]; then
  write_failure 2 toolchain "fixed nm path is not a regular executable"
  exit 2
fi
realpath "$CC_PATH" >"$ATTEMPT_DIR/compiler.path"
"$CC_PATH" --version >"$ATTEMPT_DIR/compiler.version" 2>&1
"$CXX_PATH" --version >"$ATTEMPT_DIR/cxx.version" 2>&1
"$CMAKE_PATH" --version >"$ATTEMPT_DIR/cmake.version" 2>&1
realpath "$NM_PATH" >"$ATTEMPT_DIR/nm.path"
"$NM_PATH" --version >"$ATTEMPT_DIR/nm.version" 2>&1

# calibrator は Python 3.10 構文を使う。候補自身で版数 smoke check を通し、
# 選んだ interpreter を argv に固定する。PATH shim は calibrator の子 process が
# python3 を拾う場合にも同じ interpreter のディレクトリを優先させる。
CALIBRATE_PYTHON=""
calibrate_python_rejected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    CALIBRATE_PYTHON="$resolved"
    break
  fi
  calibrate_python_rejected+="${calibrate_python_rejected:+ }$candidate=$resolved"
done
if [[ -z "$CALIBRATE_PYTHON" ]]; then
  write_failure 2 interpreter \
    "no python3.10 interpreter passed smoke check (rejected: ${calibrate_python_rejected:-none})"
  exit 2
fi

# (iv-a) pinned-clean gflags を /scr で static build/install。build cache は一切参照しない。
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
gflags_configure_argv=("$CMAKE_PATH" -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=("$CMAKE_PATH" --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=("$CMAKE_PATH" --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-configure.stdout" 2>"$ATTEMPT_DIR/gflags-configure.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags configure failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_build_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-build.stdout" 2>"$ATTEMPT_DIR/gflags-build.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags build failed"
  exit "$gflags_rc"
fi
timeout 60 "${gflags_install_argv[@]}" \
  >"$ATTEMPT_DIR/gflags-install.stdout" 2>"$ATTEMPT_DIR/gflags-install.stderr" || gflags_rc=$?
if [[ "$gflags_rc" -ne 0 ]]; then
  write_failure "$gflags_rc" gflags "gflags install failed"
  exit "$gflags_rc"
fi

# (iv-b) pinned-clean glog を /scr で static/PIC build/install。gflags の install のみを参照。
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
glog_configure_argv=("$CMAKE_PATH" -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=("$CMAKE_PATH" --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=("$CMAKE_PATH" --install "$GLOG_BUILD_DIR")
timeout 120 "${glog_configure_argv[@]}" \
  >"$ATTEMPT_DIR/glog-configure.stdout" 2>"$ATTEMPT_DIR/glog-configure.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog configure failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_build_argv[@]}" \
  >"$ATTEMPT_DIR/glog-build.stdout" 2>"$ATTEMPT_DIR/glog-build.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog build failed"
  exit "$glog_rc"
fi
timeout 120 "${glog_install_argv[@]}" \
  >"$ATTEMPT_DIR/glog-install.stdout" 2>"$ATTEMPT_DIR/glog-install.stderr" || glog_rc=$?
if [[ "$glog_rc" -ne 0 ]]; then
  write_failure "$glog_rc" glog "glog install failed"
  exit "$glog_rc"
fi

# (iv-c) pinned-clean CCBench + /scr の fresh worktree/build。
FETCHCONTENT_SOURCE_ROOT="$TMPDIR/fetchcontent-src"
FETCHCONTENT_BASE_DIR="$TMPDIR/fetchcontent-base"
mkdir -p "$FETCHCONTENT_SOURCE_ROOT" "$FETCHCONTENT_BASE_DIR"

# The pristine-source verifier imports Python 3.10-only runtime APIs. Resolve
# its interpreter independently from the calibrator interpreter selected above.
THIRD_PARTY_VERIFY_PYTHON=""
third_party_verify_python_rejected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    THIRD_PARTY_VERIFY_PYTHON="$resolved"
    break
  fi
  third_party_verify_python_rejected+="${third_party_verify_python_rejected:+ }$candidate=$resolved"
done
if [[ -z "$THIRD_PARTY_VERIFY_PYTHON" ]]; then
  write_failure 2 interpreter \
    "no python3.10 interpreter passed smoke check (rejected: ${third_party_verify_python_rejected:-none})"
  exit 2
fi

for third_party_name in masstree mimalloc googletest; do
  third_party_copy_rc=0
  timeout 120 cp -a \
    "$THIRD_PARTY_SOURCE_ROOT/$third_party_name" \
    "$FETCHCONTENT_SOURCE_ROOT/${third_party_name}-src" \
    || third_party_copy_rc=$?
  if [[ "$third_party_copy_rc" -ne 0 ]]; then
    write_failure 2 third_party_source \
      "cannot copy pinned third-party staging source: $third_party_name"
    exit 2
  fi
done
third_party_verify_rc=0
(cd "$REPO_ROOT" && timeout 120 "$THIRD_PARTY_VERIFY_PYTHON" - \
  "$FETCHCONTENT_SOURCE_ROOT" "$REPO_ROOT" <<'PY'
import sys
from pathlib import Path

from orchestrator.campaign.s8b_floor_campaign import (
    _verify_pristine_floor_dependency_sources,
)

_verify_pristine_floor_dependency_sources(
    Path(sys.argv[1]), repo_root=Path(sys.argv[2]),
)
PY
) >"$ATTEMPT_DIR/third-party-source-verify.stdout" \
  2>"$ATTEMPT_DIR/third-party-source-verify.stderr" \
  || third_party_verify_rc=$?
if [[ "$third_party_verify_rc" -ne 0 ]]; then
  write_failure 2 third_party_source \
    "job-private FetchContent sources are not pinned-pristine"
  exit 2
fi
CCBENCH_BASE="$REPO_ROOT/external/ccbench"
CCBENCH_HEAD=$(git -C "$CCBENCH_BASE" rev-parse HEAD)
GITLINK=$(git -C "$REPO_ROOT" ls-tree HEAD external/ccbench | awk '{print $3}')
[[ "$CCBENCH_HEAD" == "$GITLINK" ]]
[[ -z "$(git -C "$CCBENCH_BASE" status --porcelain --untracked-files=no)" ]]
BUILD_SOURCE="$TMPDIR/ccbench-source"
BUILD_DIR="$TMPDIR/ccbench-build"
git -C "$CCBENCH_BASE" worktree add --detach "$BUILD_SOURCE" "$CCBENCH_HEAD" \
  >"$ATTEMPT_DIR/worktree-add.stdout" 2>"$ATTEMPT_DIR/worktree-add.stderr"
mkdir "$BUILD_DIR"
case "$CALIBRATION_PROTOCOL" in
  silo)
    ccbench_define_argv=(
      -DCCBENCH_TRACE=0
      -DCCBENCH_BACK_OFF=0
      -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
      -DCCBENCH_NO_WAIT_OF_TICTOC=0
      -DCCBENCH_WAL=0
    )
    ;;
  mocc)
    ccbench_define_argv=(
      -DCCBENCH_TRACE=0
      -DCCBENCH_BACK_OFF=1
      -DCCBENCH_KEY_SORT=0
      -DCCBENCH_TEMPERATURE_RESET_OPT=1
    )
    ;;
  tictoc)
    ccbench_define_argv=(
      -DCCBENCH_TRACE=0
      -DCCBENCH_BACK_OFF=1
      -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
      -DCCBENCH_NO_WAIT_OF_TICTOC=0
      -DCCBENCH_PREEMPTIVE_ABORTS=1
      -DCCBENCH_TIMESTAMP_HISTORY=1
    )
    ;;
esac
configure_argv=("$CMAKE_PATH" -S "$BUILD_SOURCE" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
  -DENABLE_SANITIZER=OFF
  "-DFETCHCONTENT_BASE_DIR=$FETCHCONTENT_BASE_DIR"
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON
  "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$FETCHCONTENT_SOURCE_ROOT/masstree-src"
  "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$FETCHCONTENT_SOURCE_ROOT/mimalloc-src"
  "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$FETCHCONTENT_SOURCE_ROOT/googletest-src"
  "${ccbench_define_argv[@]}"
  "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"
  "-DIZANAGI_GFLAGS_SRC_HEAD=$GFLAGS_SOURCE_HEAD"
  "-DIZANAGI_GLOG_SRC_HEAD=$GLOG_SOURCE_HEAD"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")" "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
case "$CALIBRATION_PROTOCOL" in
  silo)
    build_argv=("$CMAKE_PATH" --build "$BUILD_DIR" --target ycsb_silo.exe -j 48)
    ;;
  mocc)
    build_argv=("$CMAKE_PATH" --build "$BUILD_DIR" --target ycsb_mocc.exe -j 48)
    ;;
  tictoc)
    build_argv=("$CMAKE_PATH" --build "$BUILD_DIR" --target ycsb_tictoc.exe -j 48)
    ;;
esac
timeout 900 "${configure_argv[@]}" >"$ATTEMPT_DIR/configure.stdout" 2>"$ATTEMPT_DIR/configure.stderr"
timeout 900 "${build_argv[@]}" >"$ATTEMPT_DIR/build.stdout" 2>"$ATTEMPT_DIR/build.stderr"
BINARY="$BUILD_DIR/cc/$CALIBRATION_PROTOCOL/${build_argv[4]}"
[[ -x "$BINARY" ]]
timeout 60 sha256sum "$BINARY" >"$ATTEMPT_DIR/binary.sha256"
BINARY_SHA=$(awk '{print $1}' "$ATTEMPT_DIR/binary.sha256")
timeout 60 "$NM_PATH" -C "$BINARY" >"$ATTEMPT_DIR/binary.symbols" 2>"$ATTEMPT_DIR/nm.stderr"
if [[ ! -s "$ATTEMPT_DIR/binary.symbols" ]]; then
  write_failure 2 trace_separation "calibration binary symbol table is empty"
  exit 2
fi
if grep -qi 'izanagi_trace' "$ATTEMPT_DIR/binary.symbols"; then
  write_failure 2 trace_separation "trace symbol detected in calibration binary"
  exit 2
fi

# (v) synchronous build return + /proc descendant scan の両方で build 子孫終了を確認する。
python3 - "$$" <<'PY' >"$ATTEMPT_DIR/build-descendants.json"
import json, os, pathlib, sys
root = int(sys.argv[1])
self_pid = os.getpid()
parents = {}
for entry in pathlib.Path("/proc").iterdir():
    if not entry.name.isdigit():
        continue
    try:
        stat = (entry / "stat").read_text()
        tail = stat[stat.rfind(")") + 2:].split()
        parents[int(entry.name)] = int(tail[1])
    except (OSError, ValueError, IndexError):
        continue
def descends(pid):
    seen = set()
    while pid in parents and pid not in seen:
        if pid == self_pid:
            return False
        if parents[pid] == root:
            return True
        seen.add(pid)
        pid = parents[pid]
    return False
remaining = sorted(pid for pid in parents if descends(pid))
print(json.dumps({"shell_pid": root, "remaining_descendants": remaining}, sort_keys=True))
raise SystemExit(1 if remaining else 0)
PY

# (vi 前半) build 後 profile。calibrator certification がこの後、凍結 cooldown
# (load1<=1.0、30 秒間隔 3 回、最大 20 分) と dynamic pre-receipt を fatal gate として実行する。
timeout 120 python3 "$TOOLS/run_probe.py" --output "$ATTEMPT_DIR/attestation-pre.json" \
  >"$ATTEMPT_DIR/attestation-pre.stdout" 2>"$ATTEMPT_DIR/attestation-pre.stderr"

# exact AcquisitionReceipt candidate を組み立て、W0 dataclass 自身で検証する。
python3 - "$ATTEMPT_DIR" "$CCBENCH_HEAD" "$BINARY_SHA" "$CURRENT_SCRIPT_SHA" \
  "$ASSIGNED_HOST" "$HOSTNAME_OBSERVED" "$EXPECTED_CPU" "$EXPECTED_CORES" \
  "$REQUESTED_S" "$FINALIZE_RESERVE_S" "${configure_argv[*]}" "${build_argv[*]}" \
  "$REPO_ROOT" <<'PY'
import json, os, shlex, sys
from pathlib import Path
(root, cc_head, binary_sha, script_sha, assigned, hostname, expected_cpu,
 expected_cores, requested_s, reserve_s, configure_text, build_text,
 repo_root) = sys.argv[1:]
sys.path.insert(0, repo_root)
from orchestrator.campaign.env_attestation import (
    PEGASUS_PROBE_OUTPUT_V2,
    observed_profile_to_dict,
    parse_probe_output,
)
submit = json.load(open(os.path.join(root, "submit-receipt.json"), encoding="utf-8"))
topology = json.load(open(os.path.join(root, "topology.json"), encoding="utf-8"))
attestation = parse_probe_output(Path(root, "attestation-pre.json").read_bytes())
if attestation.schema_version != PEGASUS_PROBE_OUTPUT_V2 or not attestation.ok:
    raise SystemExit("pre attestation failed")
if attestation.profile is None:
    raise SystemExit("pre attestation profile missing")
profile = observed_profile_to_dict(attestation.profile)
combined_modules = []
for filename in ("module-list.stdout", "module-list.stderr"):
    for line in open(os.path.join(root, filename), encoding="utf-8", errors="replace"):
        line = line.strip()
        if line and "currently loaded" not in line.lower() and not line.endswith(":"):
            combined_modules.append(line)
if not combined_modules:
    raise SystemExit("module -t list produced no exact module names")
compiler_path = open(os.path.join(root, "compiler.path"), encoding="utf-8").read().strip()
compiler_version = open(os.path.join(root, "compiler.version"), encoding="utf-8").read().strip()
cmake_version = open(os.path.join(root, "cmake.version"), encoding="utf-8").read().strip()
model = profile["cpu"]["model_name_normalized"]
known_passed = (expected_cpu == model and profile["cores"]["physical"] == int(expected_cores)
                and topology["cpuset_size"] == int(expected_cores) and topology["ht_off"] is True)
frozen_required_s = 10 + 1200 + 5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 1080 + int(reserve_s)
walltime_formula = (
    "TSC(10)+cooldown_max(1200)+points(5)*sweep_reps(3)*120+"
    "noise_reps(10)*120+2*sweep_reps(3)*120+"
    "build_cap(CCBench=900+gflags=60+glog=120)(1080)+finalize_reserve(600)=6610"
)
candidate = {
    "qsub": submit["qsub"],
    "allocation": {
        "pbs_jobid": os.environ["PBS_JOBID"],
        "assigned_host_qstat": assigned,
        "hostname_observed": hostname,
        "cpuset_size": topology["cpuset_size"],
        "ht_off": topology["ht_off"],
    },
    "toolchain": {
        "module_list": combined_modules,
        "compiler_path": compiler_path,
        "compiler_version": compiler_version,
        "cmake_version": cmake_version,
    },
    "ccbench": {
        "head_sha": cc_head,
        "pinned_clean": True,
        "build_argv": shlex.split(configure_text) + ["&&"] + shlex.split(build_text),
        "binary_sha256": binary_sha,
    },
    "job_script_sha256": script_sha,
    "walltime": {
        "formula": walltime_formula,
        "required_s": frozen_required_s,
        "reserve_s": int(reserve_s),
    },
    "known_values_check": {
        "expected_cpu_model": expected_cpu,
        "expected_cores": int(expected_cores),
        "source": "pegasus-runbook §1",
        "passed": known_passed,
    },
}
with open(os.path.join(root, "acquisition-candidate.json"), "x", encoding="utf-8") as handle:
    json.dump(candidate, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
python3 "$TOOLS/make_acquisition_receipt.py" \
  --input "$ATTEMPT_DIR/acquisition-candidate.json" \
  --output "$ATTEMPT_DIR/acquisition-receipt.json"

now=$(date +%s)
remaining=$((DEADLINE_EPOCH - now - FINALIZE_RESERVE_S))
if [[ "$remaining" -le 0 ]]; then
  write_failure 2 reservation "no measured window remains before finalize reserve"
  exit 2
fi

# (vii) policy-pinned perf dispatcher bypass. The calibrator's exact event set is
# read from its source of truth so this smoke cannot silently drift from measurement.
PERF_EVENTS=$(python3 - "$REPO_ROOT/orchestrator/calibrator/runner.py" <<'PY'
import ast
import sys

tree = ast.parse(open(sys.argv[1], encoding="utf-8").read(), filename=sys.argv[1])
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == "PERF_EVENTS" for target in targets):
            events = ast.literal_eval(node.value)
            if (not isinstance(events, list) or not events
                    or any(not isinstance(event, str) or not event for event in events)):
                raise SystemExit("PERF_EVENTS must be a non-empty list of strings")
            print(",".join(events))
            break
else:
    raise SystemExit("PERF_EVENTS assignment not found")
PY
)
PERF_SELECTED=""
PERF_SELECTED_REAL=""
PERF_SELECTED_VERSION=""
PERF_SELECTED_SMOKE=""
for perf_index in "${!PERF_CANDIDATES[@]}"; do
  perf_candidate=${PERF_CANDIDATES[$perf_index]}
  perf_version_file="$ATTEMPT_DIR/perf-candidate-${perf_index}.version"
  perf_smoke_file="$ATTEMPT_DIR/perf-candidate-${perf_index}.smoke"
  if [[ ! -x "$perf_candidate" ]]; then
    continue
  fi
  perf_version_rc=0
  timeout 10 "$perf_candidate" --version >"$perf_version_file" 2>&1 || perf_version_rc=$?
  if [[ "$perf_version_rc" -ne 0 ]]; then
    continue
  fi
  perf_smoke_rc=0
  timeout 10 "$perf_candidate" stat -e "$PERF_EVENTS" -- sleep 0.1 \
    >"$perf_smoke_file" 2>&1 || perf_smoke_rc=$?
  if [[ "$perf_smoke_rc" -ne 0 ]] \
      || grep -Eqi '<not (supported|counted)>' "$perf_smoke_file"; then
    continue
  fi
  PERF_SELECTED=$perf_candidate
  PERF_SELECTED_REAL=$(realpath -e "$perf_candidate")
  PERF_SELECTED_VERSION=$(cat "$perf_version_file")
  PERF_SELECTED_SMOKE=$(cat "$perf_smoke_file")
  break
done
if [[ -z "$PERF_SELECTED" ]]; then
  write_failure 2 perf "no policy perf candidate passed version and event smoke"
  exit 2
fi
python3 - "$ATTEMPT_DIR/perf-selection.json" "$PERF_SELECTED_REAL" \
  "$PERF_SELECTED_VERSION" "$PERF_EVENTS" "$PERF_SELECTED_SMOKE" <<'PY'
import json
import sys

path, selected, version, events, smoke = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump({
        "schema_version": "pegasus-perf-selection/v1",
        "path": selected,
        "version": version,
        "events": events.split(","),
        "smoke_output": smoke,
    }, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
mkdir "$TMPDIR/bin"
ln -s "$PERF_SELECTED_REAL" "$TMPDIR/bin/perf"
CALIBRATE_PATH="$TMPDIR/bin:$PATH"

CALIBRATE_PATH="$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH"

# CLI 名は L4 と凍結共有。override/fallback 用 --clocks-per-us は渡さない。
CALIBRATE_ARGV_JSON="$ATTEMPT_DIR/calibrate-argv.json"
calibrate_argv=(
  env "PATH=$CALIBRATE_PATH"
  "$CALIBRATE_PYTHON" "$REPO_ROOT/orchestrator/calibrate.py"
  --certify
  --env-tag pegasus
  --threads 48
  --workload "ycsb_zipf_skew=0.9,ycsb_rratio=$CALIBRATION_RRATIO,ycsb_rmw=0"
  --binary "$BINARY"
  --binary-sha256 "$BINARY_SHA"
  --receipt-json "$ATTEMPT_DIR/acquisition-receipt.json"
)
python3 - "$CALIBRATE_ARGV_JSON" "${calibrate_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

calibrate_rc=0
timeout --signal=TERM "$remaining" python3 "$TOOLS/exec_calibrate.py" "$CALIBRATE_ARGV_JSON" \
  >"$ATTEMPT_DIR/calibrate.stdout" 2>"$ATTEMPT_DIR/calibrate.stderr" \
  || calibrate_rc=$?

if [[ "$calibrate_rc" -eq 0 ]]; then
  timeout 120 python3 "$TOOLS/run_probe.py" --output "$ATTEMPT_DIR/attestation-post.json" \
    >"$ATTEMPT_DIR/attestation-post.stdout" 2>"$ATTEMPT_DIR/attestation-post.stderr"
fi

python3 - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$calibrate_rc" "$BINARY_SHA" \
  "$CURRENT_SCRIPT_SHA" "$CALIBRATION_RRATIO" "$CALIBRATION_PROTOCOL" <<'PY'
import json, sys, time
path, job_id, rc, binary_sha, job_script_sha, rratio, protocol = sys.argv[1:]
payload = {
    "schema_version": "pegasus-job-result/v1",
    "pbs_jobid": job_id,
    "calibrate_rc": int(rc),
    "binary_sha256": binary_sha,
    "job_script_sha256": job_script_sha,
    "calibration": {
        "protocol": protocol,
        "workload": {"ycsb_rratio": rratio},
    },
    "completed_epoch": int(time.time()),
}
with open(path, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

if [[ "$calibrate_rc" -ne 0 ]]; then
  write_failure "$calibrate_rc" calibrate "certification calibrator rejected the attempt"
  exit "$calibrate_rc"
fi

# worktree metadata を clean に戻す。/scr 本体は scheduler の job cleanup に委ねる。
git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
  >"$ATTEMPT_DIR/worktree-remove.stdout" 2>"$ATTEMPT_DIR/worktree-remove.stderr"
BUILD_SOURCE=""
exit 0
