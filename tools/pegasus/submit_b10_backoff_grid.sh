#!/bin/bash
# Login-side fan-out: submit one independent job for each B-10 workload.
set -Eeuo pipefail
umask 077

usage() {
  echo "usage: submit_b10_backoff_grid.sh --output-parent ABSOLUTE_PATH" >&2
}

OUTPUT_PARENT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-parent)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      OUTPUT_PARENT=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[[ -n "$OUTPUT_PARENT" && "$OUTPUT_PARENT" == /* && -d "$OUTPUT_PARENT" \
    && ! -L "$OUTPUT_PARENT" ]] || {
  echo "--output-parent must name an existing absolute directory" >&2
  exit 2
}
[[ "$OUTPUT_PARENT" =~ ^[A-Za-z0-9._/-]+$ ]] || {
  echo "output parent contains characters unsafe for qsub -v" >&2
  exit 2
}
OUTPUT_PARENT=$(realpath -e -- "$OUTPUT_PARENT")

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}")
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..")
JOB_SCRIPT="$SCRIPT_DIR/b10_backoff_grid.sh"
[[ -f "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT" ]] || {
  echo "B-10 job script is missing or a symlink" >&2
  exit 2
}
"${PYTHON:-python3}" -I -B - "$REPO_ROOT" "$OUTPUT_PARENT" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1]).resolve(strict=True)
target = pathlib.Path(sys.argv[2]).resolve(strict=True)
if target == repo or repo in target.parents or target in repo.parents:
    raise SystemExit("output parent must be outside the repository")
if any((parent / ".git").exists() for parent in (target, *target.parents)):
    raise SystemExit("output parent has a repository ancestor")
PY

for command_name in qstat qsub pegasusinfo quota; do
  command -v -- "$command_name" >/dev/null 2>&1 || {
    echo "required submission command is unavailable: $command_name" >&2
    exit 2
  }
done
python3.10 -I -B -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 10))'
quota -s >/dev/null
QUEUE_STATE=$(qstat -Q)
printf '%s\n' "$QUEUE_STATE" | python3.10 -I -B -c '
import re, sys
text = sys.stdin.read()
raise SystemExit(0 if "gen_S" in text
                 and re.search(r"(?i)\b(ENA|ENABLE(?:D)?)\b", text)
                 and re.search(r"(?i)\b(ACT|ACTIVE)\b", text) else 1)
' || {
  echo "gen_S is not ENA/ACT" >&2
  exit 2
}
PEGASUS_INFO=$(pegasusinfo)
[[ -n "$PEGASUS_INFO" ]] || { echo "pegasusinfo returned no data" >&2; exit 2; }

GROUP_ID="b10-backoff-grid-$(date -u +%Y%m%dT%H%M%SZ)-$$"
RECEIPT="$OUTPUT_PARENT/$GROUP_ID.submit.json"
[[ ! -e "$RECEIPT" ]] || { echo "submission receipt already exists" >&2; exit 2; }

WORKLOADS=(write-heavy balanced read-heavy)
JOB_IDS=()
ROOTS=()
for workload in "${WORKLOADS[@]}"; do
  root="$OUTPUT_PARENT/$GROUP_ID-$workload"
  stdout="$OUTPUT_PARENT/$GROUP_ID-$workload.stdout"
  stderr="$OUTPUT_PARENT/$GROUP_ID-$workload.stderr"
  [[ ! -e "$root" && ! -e "$stdout" && ! -e "$stderr" ]] || {
    echo "job-unique output already exists for $workload" >&2
    exit 2
  }
  job_id=$(qsub \
    -v "B10_WORKLOAD=$workload,B10_OUTPUT_ROOT=$root" \
    -o "$stdout" -e "$stderr" "$JOB_SCRIPT")
  [[ -n "$job_id" ]] || { echo "qsub returned no job id for $workload" >&2; exit 2; }
  JOB_IDS+=("$job_id")
  ROOTS+=("$root")
done

python3.10 -I -B - "$RECEIPT" "$GROUP_ID" \
  "${WORKLOADS[0]}" "${JOB_IDS[0]}" "${ROOTS[0]}" \
  "${WORKLOADS[1]}" "${JOB_IDS[1]}" "${ROOTS[1]}" \
  "${WORKLOADS[2]}" "${JOB_IDS[2]}" "${ROOTS[2]}" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
group = sys.argv[2]
values = sys.argv[3:]
jobs = [
    {"workload": values[index], "job_id": values[index + 1], "output_root": values[index + 2]}
    for index in range(0, len(values), 3)
]
with path.open("x", encoding="utf-8") as handle:
    json.dump({
        "schema_version": "b10-backoff-grid-submit/v1",
        "group_id": group,
        "jobs": jobs,
    }, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

printf '%s\n' "${JOB_IDS[@]}"
