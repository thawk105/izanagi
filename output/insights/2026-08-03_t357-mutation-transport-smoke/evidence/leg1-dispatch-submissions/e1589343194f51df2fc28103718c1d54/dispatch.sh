#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=00:30:00
#PBS -N izdw-e158934319
set -u

RESULT=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree/output/pegasus-dispatch/e1589343194f51df2fc28103718c1d54/result.json
PROBE=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree/output/pegasus-dispatch/e1589343194f51df2fc28103718c1d54/interpreter_probe.py
REQUEST=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree/output/pegasus-dispatch/e1589343194f51df2fc28103718c1d54/request.json
REPO=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree
DISPATCHER=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree/tools/pegasus/dispatch_compute.py
MARKER=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree/output/pegasus-dispatch/e1589343194f51df2fc28103718c1d54/compute-visible.json

write_failure() {
    local stage=$1
    local tmp="${RESULT}.tmp.$$"
    printf '{"schema_version":"pegasus-dispatch-result/v1","stage":"%s","child_rc":16,"pbs_jobid":"%s"}\n'         "$stage" "${PBS_JOBID:-unknown}" >"$tmp"
    mv "$tmp" "$RESULT"
}

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
    write_failure hostname
    exit 16
fi
marker_tmp="${MARKER}.tmp.$$"
printf '{"schema_version":"pegasus-compute-visible/v1","pbs_jobid":"%s","hostname":"%s"}\n'     "${PBS_JOBID:-unknown}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
if [[ -z "$selected" ]]; then
    write_failure interpreter
    exit 16
fi

if ! cd "$REPO"; then
    write_failure cwd
    exit 16
fi

export PATH="$(dirname "$selected"):$PATH"
unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT IZANAGI_TASK_RUN_SIDECAR
exec "$selected" "$DISPATCHER" --job-run "$REQUEST"
