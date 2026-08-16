#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=06:00:00
#PBS -b 1
set -Eeuo pipefail
umask 077

fail() {
  echo "oracle n pilot job refused: $*" >&2
  exit 2
}

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" ]] \
  || fail "PBS_JOBID and PBS_O_WORKDIR are required"
[[ "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]] || fail "unsafe PBS_JOBID"

for variable in IZANAGI_PILOT_PROTOCOL IZANAGI_PILOT_OUTPUT_ROOT \
                IZANAGI_PILOT_CACHE_ROOT IZANAGI_PILOT_ATTEMPT; do
  [[ -n "${!variable:-}" ]] || fail "$variable is required"
done
[[ "$IZANAGI_PILOT_ATTEMPT" =~ ^[A-Za-z0-9._-]+$ ]] || fail "unsafe attempt id"
[[ "${IZANAGI_PILOT_BUILD_ONLY:-0}" =~ ^[01]$ ]] || fail "unsafe build-only flag"
if [[ -n "${IZANAGI_PILOT_ROUNDS:-}" ]]; then
  [[ "$IZANAGI_PILOT_ROUNDS" =~ ^[1-9][0-9]*$ ]] || fail "unsafe rounds"
fi

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP
REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || fail "cannot resolve repo root"
[[ ! -L "$PBS_O_WORKDIR" ]] || fail "repo root must not be a symlink"
git -C "$REPO_ROOT" diff-index --quiet HEAD -- || fail "repo has tracked changes"
[[ -z "$(git -C "$REPO_ROOT" ls-files --others --exclude-standard)" ]] \
  || fail "repo has untracked files"

PY=""
for candidate in python3 python3.10 python3.11 python3.12; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  resolved=$(realpath -e -- "$resolved" 2>/dev/null || true)
  [[ -n "$resolved" && -x "$resolved" ]] || continue
  if "$resolved" -I -B -c \
      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    PY="$resolved"
    break
  fi
done
[[ -n "$PY" ]] || fail "python 3.10 or newer is required"

PROTOCOL=$(realpath -e -- "$IZANAGI_PILOT_PROTOCOL") \
  || fail "cannot resolve protocol"
[[ -f "$PROTOCOL" && ! -L "$IZANAGI_PILOT_PROTOCOL" ]] \
  || fail "protocol must be a non-symlink regular file"
OUTPUT_ROOT=$(realpath -e -- "$IZANAGI_PILOT_OUTPUT_ROOT") \
  || fail "cannot resolve output root"
CACHE_ROOT=$(realpath -e -- "$IZANAGI_PILOT_CACHE_ROOT") \
  || fail "cannot resolve persistent cache root"
for external_root in "$OUTPUT_ROOT" "$CACHE_ROOT"; do
  [[ -d "$external_root" && ! -L "$external_root" ]] \
    || fail "external root must be a non-symlink directory"
  [[ "$external_root" != "$REPO_ROOT" && "$external_root" != "$REPO_ROOT/"* ]] \
    || fail "external root must be outside the repo"
done

export TMPDIR="/scr/${PBS_JOBID//:/_}-oracle-n-pilot"
mkdir -m 0700 "$TMPDIR" || fail "scratch directory must be create-only"
mkdir -m 0700 "$TMPDIR/worktrees" "$TMPDIR/dummy-trace"
mkdir -m 0700 "$TMPDIR/python-bin"
ln -s "$PY" "$TMPDIR/python-bin/python3"
export PATH="$TMPDIR/python-bin:$PATH"

ATTEMPT_DIR="$OUTPUT_ROOT/$IZANAGI_PILOT_ATTEMPT"
[[ -d "$ATTEMPT_DIR" && ! -L "$ATTEMPT_DIR" ]] \
  || fail "submit wrapper must provision the attempt directory"
RESULT="$ATTEMPT_DIR/result.json"
[[ ! -e "$RESULT" && ! -L "$RESULT" ]] || fail "result already exists"

driver=(
  "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_oracle_n_pilot.py"
  --protocol "$PROTOCOL"
  --output "$RESULT"
  --attempt-id "$IZANAGI_PILOT_ATTEMPT"
  --cache-root "$CACHE_ROOT"
)
if [[ "$IZANAGI_PILOT_BUILD_ONLY" == 1 ]]; then
  driver+=(--build-only)
fi
if [[ -n "${IZANAGI_PILOT_ROUNDS:-}" ]]; then
  driver+=(--rounds "$IZANAGI_PILOT_ROUNDS")
fi

cd "$REPO_ROOT"
"${driver[@]}"
[[ -f "$RESULT" && ! -L "$RESULT" ]] || fail "driver did not create a regular result"
"$PY" -I -B - "$RESULT" "$REPO_ROOT" <<'PY'
import hashlib
import pathlib
import sys

sys.path.insert(0, sys.argv[2])
from orchestrator.campaign.s8b_oracle_n_pilot import assert_holdout_safe_bytes

path = pathlib.Path(sys.argv[1])
payload = path.read_bytes()
assert_holdout_safe_bytes(path.name, payload)
print(hashlib.sha256(payload).hexdigest())
PY
