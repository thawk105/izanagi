#!/bin/bash
set -uo pipefail
umask 077

: "${T362_RUN_ROOT:?T362_RUN_ROOT is required}"
: "${T362_DRIVER_ROOT:?T362_DRIVER_ROOT is required}"
: "${T362_MODE:?T362_MODE is required}"
: "${T362_RUN_NONCE:?T362_RUN_NONCE is required}"
: "${T362_ATTEMPT_ID:?T362_ATTEMPT_ID is required}"
[[ "$T362_RUN_NONCE" == "$T362_ATTEMPT_ID" ]] || exit 16
[[ "$T362_MODE" == "split-warning" ]] || { printf '%s\n' 'diagnostic body requires split-warning mode' >&2; exit 16; }
[[ "$T362_RUN_ROOT" == /* && -d "$T362_RUN_ROOT" && ! -L "$T362_RUN_ROOT" ]] || exit 16
[[ "$T362_DRIVER_ROOT" == /* && -d "$T362_DRIVER_ROOT" && ! -L "$T362_DRIVER_ROOT" ]] || exit 16

PROBE="$T362_DRIVER_ROOT/signal_interpreter_probe.py"
SIGNAL_PROBE="$T362_DRIVER_ROOT/signal_probe.py"
[[ -f "$PROBE" && ! -L "$PROBE" && -f "$SIGNAL_PROBE" && ! -L "$SIGNAL_PROBE" ]] || exit 16

selected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
if [[ -z "$selected" ]]; then
    exit 16
fi

export PATH="$(dirname "$selected"):$PATH"
export PYTHONDONTWRITEBYTECODE=1

CONTROL_LOG="$T362_RUN_ROOT/control-bash.jsonl"
MAIN_LOG="$T362_RUN_ROOT/events-bash.jsonl"
HEARTBEAT_LOG="$T362_RUN_ROOT/heartbeats-bash.jsonl"
ACTIVE_SIGNAL_LOG="$MAIN_LOG"
SIGNAL_WRITER_FAILURE_LOG="$T362_RUN_ROOT/signal-writer-failures.raw"
signal_writer_failed=0

record_bash_signal() {
    local signal_name=$1
    local writer_rc
    "$selected" "$SIGNAL_PROBE" append --path "$ACTIVE_SIGNAL_LOG" \
        --layer bash --event signal --signal "$signal_name"
    writer_rc=$?
    if [[ "$writer_rc" -ne 0 ]]; then
        if ! printf 'signal=%s writer_rc=%s time=%(%s)T\n' \
            "$signal_name" "$writer_rc" -1 >>"$SIGNAL_WRITER_FAILURE_LOG"; then
            printf '%s\n' 'signal writer and durable failure marker both failed' >&2
            exit 97
        fi
        if ! sync -f "$SIGNAL_WRITER_FAILURE_LOG"; then
            printf '%s\n' 'signal writer failure marker fsync failed' >&2
            exit 97
        fi
        signal_writer_failed=1
    fi
}

trap 'record_bash_signal SIGHUP' HUP
trap 'record_bash_signal SIGINT' INT
trap 'record_bash_signal SIGQUIT' QUIT
trap 'record_bash_signal SIGTERM' TERM
trap 'record_bash_signal SIGUSR1' USR1
trap 'record_bash_signal SIGUSR2' USR2

"$selected" "$SIGNAL_PROBE" bootstrap --layer bash

# D4 control: exercise the real Bash trap writer, but keep it out of the main log.
ACTIVE_SIGNAL_LOG="$CONTROL_LOG"
"$selected" "$SIGNAL_PROBE" append --path "$CONTROL_LOG" --layer bash --event control_start
kill -USR2 "$$"
"$selected" "$SIGNAL_PROBE" append --path "$CONTROL_LOG" --layer bash --event control_normal_exit
ACTIVE_SIGNAL_LOG="$MAIN_LOG"

"$selected" "$SIGNAL_PROBE" parent &
parent_pid=$!
"$selected" "$SIGNAL_PROBE" append --path "$MAIN_LOG" --layer bash \
    --event parent_spawned --detail "$parent_pid"

# No internal total deadline: exceeding walltime is the measurement.
while true; do
    if [[ "$signal_writer_failed" -ne 0 ]]; then
        printf '%s\n' 'durable signal writer failed; aborting diagnostic leg' >&2
        exit 97
    fi
    if kill -0 "$parent_pid" 2>/dev/null; then
        parent_state=alive
    else
        parent_state=exited
    fi
    "$selected" "$SIGNAL_PROBE" append --path "$HEARTBEAT_LOG" --layer bash \
        --event heartbeat --detail "$parent_state"
    sleep 1
done
