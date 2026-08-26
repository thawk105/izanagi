#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=04:00:00
#PBS -b 1

set -Eeuo pipefail
umask 077

# 9000 + 3000 + 300 + 300 = 12600 seconds, leaving 1800 seconds of walltime.
SWEEP_CAP_S=9000
AA_CAP_S=3000
REPORT_CAP_S=300
FINALIZE_CAP_S=300
EXPECTED_FREEZE_TREES_SHA256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3
CURRENT_STAGE=bootstrap
PY=""
OUTPUT_ROOT=""

write_failure_receipt() {
  local rc=$1
  local line=$2
  [[ -n "$PY" && -n "$OUTPUT_ROOT" ]] || return 0
  "$PY" -I -B - "$OUTPUT_ROOT" "$rc" "$CURRENT_STAGE" "$line" "${PBS_JOBID:-}" <<'PY' || true
import hashlib, json, os, pathlib, sys
root, rc, stage, line, job = sys.argv[1:]
path = pathlib.Path(root + ".failure.json")
last = None
record_hash = None
for candidate in sorted(pathlib.Path(root).glob("campaigns/*/reports/b10-backoff-overthrottle-*.jsonl")):
    raw = candidate.read_bytes()
    record_hash = hashlib.sha256(raw).hexdigest()
    rows = [row for row in raw.splitlines() if row]
    if rows:
        parsed = json.loads(rows[-1])
        last = {
            "workload": parsed.get("workload"),
            "label": parsed.get("label"),
            "rep": parsed.get("rep"),
            "reference_variant_id": parsed.get("reference_variant_id"),
        }
document = {
    "schema_version": "b10-backoff-grid-job-failure/v1",
    "returncode": int(rc),
    "stage": stage,
    "line": int(line),
    "pbs_jobid": job,
    "last_persisted": last,
    "aa_jsonl_sha256": record_hash,
}
try:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write("\n")
except FileExistsError:
    pass
PY
}

on_error() {
  local rc=$?
  local line=${BASH_LINENO[0]:-0}
  trap - ERR
  write_failure_receipt "$rc" "$line"
  exit "$rc"
}
trap on_error ERR

[[ -n "${PBS_JOBID:-}" && -n "${PBS_O_WORKDIR:-}" ]] || {
  echo "PBS_JOBID and PBS_O_WORKDIR are required" >&2
  exit 2
}

WORKLOAD=${1:-${B10_WORKLOAD:-}}
case "$WORKLOAD" in
  write-heavy|balanced|read-heavy) ;;
  *) echo "workload must be write-heavy, balanced, or read-heavy" >&2; exit 2 ;;
esac

for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" && -x "$resolved" ]] || continue
  if "$resolved" -I -B -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 10))'; then
    PY=$("$resolved" -I -B -c 'import os,sys; print(os.path.realpath(sys.executable))')
    break
  fi
done
[[ -n "$PY" ]] || { echo "Python 3.10 is required" >&2; exit 2; }

export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"
for command_name in git cmake cc c++ make timeout gnuplot; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required command is unavailable: $command_name" >&2
    exit 2
  }
done

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LD_PRELOAD LD_LIBRARY_PATH
unset CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH COMPILER_PATH GCC_EXEC_PREFIX
unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
OUTPUT_ROOT=${B10_OUTPUT_ROOT:-}
[[ -n "$OUTPUT_ROOT" && "$OUTPUT_ROOT" == /* && ! -e "$OUTPUT_ROOT" ]] || {
  echo "B10_OUTPUT_ROOT must be an absolute, job-unique, uncreated path" >&2
  exit 2
}
"$PY" -I -B - "$REPO_ROOT" "$OUTPUT_ROOT" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=False)
if target == repo or repo in target.parents or target in repo.parents:
    raise SystemExit("official output root must be outside the repository")
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    raise SystemExit("official output root has a repository ancestor")
PY

export TMPDIR="/scr/${PBS_JOBID//:/_}-b10-backoff-grid-${WORKLOAD}"
mkdir -m 0700 "$TMPDIR"
export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
mkdir -m 0700 "$OUTPUT_ROOT"
mkdir -m 0700 "$OUTPUT_ROOT/campaigns" "$OUTPUT_ROOT/campaign-locks" "$OUTPUT_ROOT/env"

ENV_TAG=$("$PY" -I -B - "$REPO_ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign import p2_2
print(p2_2.resolve_site_runtime()[1].env_tag)
PY
)
mkdir -m 0700 "$OUTPUT_ROOT/env/$ENV_TAG" "$OUTPUT_ROOT/env/$ENV_TAG/claims"
export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"

freeze_digest() {
  "$PY" -I -B - "$REPO_ROOT" <<'PY'
import hashlib, pathlib, sys
repo = pathlib.Path(sys.argv[1])
digest = hashlib.sha256()
for relative in ("output/s1-freeze", "output/s8b-freeze"):
    root = repo / relative
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(repo).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
print(digest.hexdigest())
PY
}

FREEZE_BEFORE=$(freeze_digest)
[[ "$FREEZE_BEFORE" == "$EXPECTED_FREEZE_TREES_SHA256" ]] || {
  echo "freeze trees do not match the B-10 preregistered bytes" >&2
  exit 2
}
CURRENT_STAGE=extended_sweep
timeout "$SWEEP_CAP_S" "$PY" -I -B \
  "$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep.py" \
  "$WORKLOAD" --output-root "$OUTPUT_ROOT"

CURRENT_STAGE=add_analysis
timeout "$AA_CAP_S" "$PY" -I -B \
  "$REPO_ROOT/orchestrator/campaign/backoff_overthrottle.py" \
  "$WORKLOAD" --output-root "$OUTPUT_ROOT"

CURRENT_STAGE=report
timeout "$REPORT_CAP_S" "$PY" -I -B \
  "$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep_report.py" \
  "$WORKLOAD" --output-root "$OUTPUT_ROOT"

CURRENT_STAGE=finalize
FREEZE_AFTER=$(freeze_digest)
[[ "$FREEZE_AFTER" == "$EXPECTED_FREEZE_TREES_SHA256" ]] || {
  echo "freeze trees changed during the job" >&2
  exit 2
}
timeout "$FINALIZE_CAP_S" "$PY" -I -B - \
  "$OUTPUT_ROOT" "$WORKLOAD" "$PBS_JOBID" "$FREEZE_AFTER" <<'PY'
import hashlib, json, pathlib, sys
root, workload, job, freeze_hash = sys.argv[1:]
base = pathlib.Path(root)
campaigns = [path for path in (base / "campaigns").iterdir() if path.is_dir()]
if len(campaigns) != 1:
    raise SystemExit(f"expected exactly one campaign, found {len(campaigns)}")
artifacts = {}
for path in sorted(item for item in campaigns[0].rglob("*") if item.is_file()):
    artifacts[path.relative_to(base).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
document = {
    "schema_version": "b10-backoff-grid-job-complete/v1",
    "status": "complete",
    "workload": workload,
    "pbs_jobid": job,
    "campaign_id": campaigns[0].name,
    "freeze_trees_sha256": freeze_hash,
    "artifacts": artifacts,
}
with (base / "completion.json").open("x", encoding="utf-8") as handle:
    json.dump(document, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY
