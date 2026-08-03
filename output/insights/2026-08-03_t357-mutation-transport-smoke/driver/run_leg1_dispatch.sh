#!/bin/bash
set -euo pipefail

ROOT=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01
WORKTREE=$ROOT/worktree
ANCHOR=ea6ca433eb83d666ec64f3629cc35c769a2b5c19
SPEC=$ROOT/spec.json
SPEC_SHA=1d13164c2830896656bdc3b12261756996decef018c9fd83dd4f7f495de2d70e
OUT=$ROOT/leg1-ledger.json
DONE=$ROOT/leg1.done
LOG=$ROOT/leg1.log
PIDFILE=$ROOT/leg1.pid
PY=/usr/bin/python3.10

die() {
    echo "leg1 preflight failed: $*" >&2
    exit 2
}

if [[ ${1:-} == --child ]]; then
    cd "$WORKTREE" || exit 2
    unset PYTHONHOME PYTHONPATH PYTEST_ADDOPTS PYTHONSTARTUP
    unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT IZANAGI_TASK_RUN_SIDECAR
    set +e
    "$PY" tools/mutation_harness.py \
        --repo "$WORKTREE" \
        --spec "$SPEC" \
        --expected-spec-sha256 "$SPEC_SHA" \
        --out "$OUT" \
        --runner-mode dispatch \
        --detached \
        -- "$PY" tools/run_tests.py -rf -p no:cacheprovider
    rc=$?
    tmp="$DONE.tmp.$$"
    printf '%s\n' "$rc" >"$tmp"
    mv "$tmp" "$DONE"
    exit "$rc"
fi

[[ -x "$PY" ]] || die "$PY is not executable"
[[ -f "$SPEC" && ! -L "$SPEC" ]] || die "spec is missing or a symlink"
[[ -d "$WORKTREE" ]] || die "worktree is missing: $WORKTREE"
[[ ! -e "$OUT" ]] || die "--out already exists: $OUT"
[[ ! -e "$DONE" && ! -e "$LOG" && ! -e "$PIDFILE" ]] || die "leg1 artifacts already exist"
[[ "$(git -C "$WORKTREE" rev-parse HEAD)" == "$ANCHOR" ]] || die "HEAD is not anchor"
[[ "$(git -C "$WORKTREE" rev-parse --show-toplevel)" == "$WORKTREE" ]] || die "path is not worktree root"
status=$(git -C "$WORKTREE" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)
[[ -z "$status" ]] || die "worktree is dirty: $status"
git -C "$WORKTREE" diff --quiet "$ANCHOR" || die "worktree differs from anchor"
actual_sha=$(sha256sum "$SPEC" | awk '{print $1}')
[[ "$actual_sha" == "$SPEC_SHA" ]] || die "spec sha256 mismatch: $actual_sha"
[[ "$("$PY" -c 'import os,sys; print(os.path.realpath(sys.executable))')" == "$PY" ]] || die "Python identity mismatch"

SELF=$(readlink -f "$0")
setsid nohup "$SELF" --child </dev/null >"$LOG" 2>&1 &
pid=$!
printf '%s\n' "$pid" >"$PIDFILE"
echo "leg1 detached: pid=$pid"
echo "completion rc: $DONE"
echo "log: $LOG"
