#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=06:00:00
#PBS -N izanagi-b10-shape
#PBS --accept-sigterm=yes
set -Eeuo pipefail
umask 077

fail() {
  echo "B10 job preflight failed: $*" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" ]] || fail "PBS envelope missing"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || fail "unsafe PBS_JOBID"
[[ "${IZANAGI_B10_NONCE:-}" =~ ^[0-9a-f]{32}$ ]] || fail "submission nonce missing"
[[ "${IZANAGI_B10_SOURCE_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || fail "source commit missing"
[[ "${IZANAGI_B10_PREREG_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || fail "prereg commit missing"

HOSTNAME_SHORT=$(hostname -s)
HOSTNAME_FQDN=$(hostname -f)
[[ "$HOSTNAME_SHORT" =~ ^bnode[0-9]+$ ]] || fail "measurement job is not on a compute node"
REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
[[ -d "$REPO_ROOT/.git" || -f "$REPO_ROOT/.git" ]] || fail "PBS_O_WORKDIR is not a repository"
[[ "$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})" == "$IZANAGI_B10_SOURCE_COMMIT" ]] \
  || fail "queued job source HEAD drifted"
[[ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]] \
  || fail "repository working tree is dirty"
git -C "$REPO_ROOT" merge-base --is-ancestor \
  "$IZANAGI_B10_PREREG_COMMIT" "$IZANAGI_B10_SOURCE_COMMIT" \
  || fail "prereg commit is not an ancestor"

PY=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10 python3; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY=$(realpath -e -- "$resolved")
    break
  fi
done
[[ -n "$PY" ]] || fail "Python >=3.10 unavailable"

QSTAT_JOBID=${PBS_JOBID#0:}
QSTAT_FILE=$(mktemp /tmp/izanagi-b10-qstat.XXXXXXXX)
timeout 30 qstat -f "$QSTAT_JOBID" >"$QSTAT_FILE"
readarray -t QSTAT_VALUES < <("$PY" -I -B - "$QSTAT_FILE" "$HOSTNAME_SHORT" "$HOSTNAME_FQDN" <<'PY'
import re
import subprocess
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
short, fqdn = sys.argv[2:]
assigned = None
for key in ("Execution Host", "exec_host", "Assigned Host"):
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*[:=]\s*(\S+)", text)
    if match:
        assigned = match.group(1).split("/")[0]
        break
if assigned not in {short, fqdn}:
    raise SystemExit("assigned host mismatch")
matches = re.findall(r"(?im)^\s*Started Request Time\s*=\s*(.+?)\s*$", text)
if len(matches) != 1:
    raise SystemExit("scheduler start time missing")
parsed = subprocess.run(["date", "-d", matches[0], "+%s"], capture_output=True, text=True)
if parsed.returncode != 0 or not parsed.stdout.strip().isdigit():
    raise SystemExit("scheduler start time unparsable")
print(assigned)
print(parsed.stdout.strip())
PY
)
find "$QSTAT_FILE" -delete
[[ ${#QSTAT_VALUES[@]} -eq 2 ]] || fail "qstat binding unavailable"

REQUESTED_S=21600
SCHEDULER_STARTED_EPOCH=${QSTAT_VALUES[1]}
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
BOOT_ID=$(< /proc/sys/kernel/random/boot_id)
SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
SCRIPT_SHA256=$(sha256sum "$SCRIPT_PATH" | awk '{print $1}')
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="${QSTAT_VALUES[0]}"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$SCRIPT_SHA256"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_B10_NONCE"

export TMPDIR="/scr/${PBS_JOBID//:/_}-b10"
mkdir "$TMPDIR"
cleanup() {
  find "$TMPDIR" -depth -delete 2>/dev/null || true
}
trap cleanup EXIT

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
[[ ${#DEPENDENCY_VALUES[@]} -eq 4 ]] || fail "dependency policy invalid"
GFLAGS_SOURCE=${DEPENDENCY_VALUES[0]}
GFLAGS_HEAD=${DEPENDENCY_VALUES[1]}
GLOG_SOURCE=${DEPENDENCY_VALUES[2]}
GLOG_HEAD=${DEPENDENCY_VALUES[3]}
[[ "$(git -C "$GFLAGS_SOURCE" rev-parse HEAD)" == "$GFLAGS_HEAD" ]]
[[ "$(git -C "$GLOG_SOURCE" rev-parse HEAD)" == "$GLOG_HEAD" ]]
[[ -z "$(git -C "$GFLAGS_SOURCE" status --porcelain --untracked-files=all)" ]]
[[ -z "$(git -C "$GLOG_SOURCE" status --porcelain --untracked-files=all)" ]]

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

mkdir -p "$REPO_ROOT/output/env/pegasus/claims"
cd "$REPO_ROOT"
exec "$PY" -I -B -m orchestrator.campaign.b10_backoff_shape_sweep \
  --prereg-commit "$IZANAGI_B10_PREREG_COMMIT"
