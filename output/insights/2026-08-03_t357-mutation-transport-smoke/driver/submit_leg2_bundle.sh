#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=00:45:00
#PBS -N izdw-g01-bundle
# 5 * 240s = 1200s measured, plus 1500s for startup/stop/restore; 20m had no safety margin.
set -u

ROOT=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01
WORKTREE=$ROOT/worktree
ANCHOR=ea6ca433eb83d666ec64f3629cc35c769a2b5c19
SPEC=$ROOT/spec.json
SPEC_SHA=1d13164c2830896656bdc3b12261756996decef018c9fd83dd4f7f495de2d70e
OUT=$ROOT/leg2-ledger.json
RCFILE=$ROOT/leg2.rc

finish() {
    local rc=$1
    local tmp="$RCFILE.tmp.$$"
    printf '%s\n' "$rc" >"$tmp"
    mv "$tmp" "$RCFILE"
    exit "$rc"
}

unset PYTHONHOME PYTHONPATH PYTEST_ADDOPTS PYTHONSTARTUP

host=$(hostname 2>/dev/null || true)
[[ "$host" =~ ^bnode[0-9]+ ]] || finish 16
selected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" -c 'import sys
if sys.version_info < (3, 10): raise SystemExit(1)
try:
 import pytest
 import xdist
 import packaging
except Exception: raise SystemExit(1)
raise SystemExit(0)' >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
[[ -n "$selected" ]] || finish 16
PY=$selected
PY_ABS=$(readlink -f -- "$PY") || finish 16
[[ -x "$PY" ]] || finish 16
cd "$WORKTREE" || finish 16
[[ "$(pwd -P)" == "$WORKTREE" ]] || finish 16
export PATH="$(dirname "$PY"):$PATH"
unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT IZANAGI_TASK_RUN_SIDECAR
[[ "$(git rev-parse --show-toplevel)" == "$WORKTREE" ]] || finish 16
[[ "$(git rev-parse HEAD)" == "$ANCHOR" ]] || finish 16
status=$(git status --porcelain=v1 --untracked-files=all --ignore-submodules=none) || finish 16
[[ -z "$status" ]] || finish 17
git diff --quiet "$ANCHOR" || finish 17
[[ ! -e "$OUT" ]] || finish 18
actual_sha=$(sha256sum "$SPEC" | awk '{print $1}') || finish 16
[[ "$actual_sha" == "$SPEC_SHA" ]] || finish 16

printf 'diagnostic command -v python3: %s\n' "$(command -v python3 2>/dev/null || true)"
python3 --version 2>&1 || true
printf 'diagnostic command -v python3.10: %s\n' "$(command -v python3.10 2>/dev/null || true)"
python3.10 --version 2>&1 || true
printf 'diagnostic selected interpreter: %s\n' "$PY_ABS"
"$PY" --version 2>&1 || true
printf 'diagnostic PATH: %s\n' "$PATH"
printf 'diagnostic hostname: %s\n' "$(hostname 2>/dev/null || true)"

harness_rc=0
"$PY" tools/mutation_harness.py \
    --repo "$WORKTREE" \
    --spec "$SPEC" \
    --expected-spec-sha256 "$SPEC_SHA" \
    --out "$OUT" \
    --runner-mode local \
    --detached \
    -- "$PY" tools/run_tests.py -rf -p no:cacheprovider || harness_rc=$?

status=$(git status --porcelain=v1 --untracked-files=all --ignore-submodules=none)
status_rc=$?
git diff --quiet "$ANCHOR"
diff_rc=$?
current_head=$(git rev-parse HEAD 2>/dev/null)
head_rc=$?

[[ $status_rc -eq 0 && $diff_rc -le 1 && $head_rc -eq 0 ]] || finish 94
[[ "$current_head" == "$ANCHOR" ]] || finish 93
status_dirty=0
diff_dirty=0
[[ -z "$status" ]] || status_dirty=1
[[ $diff_rc -eq 0 ]] || diff_dirty=1
[[ $status_dirty -eq 0 && $diff_dirty -eq 0 ]] || {
    [[ $status_dirty -eq 1 && $diff_dirty -eq 1 ]] && finish 92
    [[ $status_dirty -eq 1 ]] && finish 90
    finish 91
}
finish "$harness_rc"
