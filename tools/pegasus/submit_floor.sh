#!/bin/bash
# ログインノード専用: floor job の submission record を create-only で作成する。
set -Eeuo pipefail
umask 077

# 出典: submit_certify.sh:5-30 @ e9b6f69
usage() {
  cat <<'EOF'
usage: submit_floor.sh [--dry-run] [--repo-root PATH]
                       [--attempts-root PATH] [--job-script PATH]
                       [--cache-root PATH]
EOF
}

SCRIPT_SOURCE=${BASH_SOURCE[0]}
SCRIPT_PATH=$(realpath -e -- "$SCRIPT_SOURCE") || {
  echo "cannot resolve submit script path" >&2
  exit 2
}
if [[ ! -f "$SCRIPT_PATH" || -L "$SCRIPT_PATH" || -L "$SCRIPT_SOURCE" ]]; then
  echo "submit script must be a non-symlink regular file" >&2
  exit 2
fi
SCRIPT_DIR=${SCRIPT_PATH%/*}
DEFAULT_REPO_ROOT=$(realpath -e -- "$SCRIPT_DIR/../..") || {
  echo "cannot resolve default repo root from submit script" >&2
  exit 2
}
REPO_ROOT_RAW="$DEFAULT_REPO_ROOT"
ATTEMPTS_ROOT_RAW=""
JOB_SCRIPT_RAW="$SCRIPT_DIR/floor_campaign.sh"
THIRD_PARTY_CACHE_ROOT_RAW=${IZANAGI_PEGASUS_THIRDPARTY_CACHE:-}
DRY_RUN=0
REPO_ROOT_OVERRIDDEN=0
ATTEMPTS_ROOT_OVERRIDDEN=0
JOB_SCRIPT_OVERRIDDEN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || { echo "--repo-root requires PATH" >&2; exit 2; }
      REPO_ROOT_RAW=$2
      REPO_ROOT_OVERRIDDEN=1
      shift 2
      ;;
    --attempts-root)
      [[ $# -ge 2 ]] || { echo "--attempts-root requires PATH" >&2; exit 2; }
      ATTEMPTS_ROOT_RAW=$2
      ATTEMPTS_ROOT_OVERRIDDEN=1
      shift 2
      ;;
    --job-script)
      [[ $# -ge 2 ]] || { echo "--job-script requires PATH" >&2; exit 2; }
      JOB_SCRIPT_RAW=$2
      JOB_SCRIPT_OVERRIDDEN=1
      shift 2
      ;;
    --cache-root)
      [[ $# -ge 2 ]] || { echo "--cache-root requires PATH" >&2; exit 2; }
      THIRD_PARTY_CACHE_ROOT_RAW=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$DRY_RUN" -eq 0 ]] \
    && ((REPO_ROOT_OVERRIDDEN || ATTEMPTS_ROOT_OVERRIDDEN || JOB_SCRIPT_OVERRIDDEN)); then
  echo "--repo-root/--attempts-root/--job-script overrides require --dry-run" >&2
  exit 2
fi

if [[ ! -d "$REPO_ROOT_RAW" || -L "$REPO_ROOT_RAW" ]]; then
  echo "repo root is missing, not a directory, or a symlink: $REPO_ROOT_RAW" >&2
  exit 2
fi
REPO_ROOT=$(cd "$REPO_ROOT_RAW" && pwd -P) || exit 2
if [[ "$DRY_RUN" -eq 0 \
    && "$SCRIPT_PATH" != "$REPO_ROOT/tools/pegasus/submit_floor.sh" ]]; then
  echo "real submission requires the repo tools/pegasus/submit_floor.sh" >&2
  exit 2
fi
if [[ -z "$THIRD_PARTY_CACHE_ROOT_RAW" \
    || "$THIRD_PARTY_CACHE_ROOT_RAW" != /* \
    || "$THIRD_PARTY_CACHE_ROOT_RAW" == *","* \
    || "$THIRD_PARTY_CACHE_ROOT_RAW" == *$'\n'* ]]; then
  echo "third-party cache root must be an explicit absolute path without comma/newline" >&2
  exit 2
fi
if [[ ! -d "$THIRD_PARTY_CACHE_ROOT_RAW" || -L "$THIRD_PARTY_CACHE_ROOT_RAW" ]]; then
  echo "third-party cache root is missing, not a directory, or a symlink" >&2
  exit 2
fi
THIRD_PARTY_CACHE_ROOT=$(realpath -e -- "$THIRD_PARTY_CACHE_ROOT_RAW") || exit 2
if [[ "$THIRD_PARTY_CACHE_ROOT" == "$REPO_ROOT" \
    || "$THIRD_PARTY_CACHE_ROOT" == "$REPO_ROOT/"* ]]; then
  echo "third-party cache root must be outside the repository" >&2
  exit 2
fi
OUTPUT_ROOT="$REPO_ROOT/output"
if [[ ! -d "$OUTPUT_ROOT" || -L "$OUTPUT_ROOT" ]]; then
  echo "repo output root is missing, not a directory, or a symlink" >&2
  exit 2
fi
OUTPUT_ROOT_REAL=$(realpath -e -- "$OUTPUT_ROOT") || exit 2
if [[ "$OUTPUT_ROOT_REAL" != "$OUTPUT_ROOT" ]]; then
  echo "repo output root does not resolve to the fixed output path" >&2
  exit 2
fi

assert_safe_output_path() {
  local target=$1
  local relative
  local current
  local component
  local resolved
  local -a components

  if [[ "$target" != "$OUTPUT_ROOT" && "$target" != "$OUTPUT_ROOT/"* ]]; then
    return 1
  fi
  relative=${target#"$REPO_ROOT"/}
  current="$REPO_ROOT"
  IFS='/' read -r -a components <<<"$relative"
  for component in "${components[@]}"; do
    [[ -n "$component" && "$component" != "." && "$component" != ".." ]] || return 1
    current="$current/$component"
    [[ ! -L "$current" ]] || return 1
  done
  resolved=$(realpath -m -- "$target") || return 1
  [[ "$resolved" == "$OUTPUT_ROOT_REAL" || "$resolved" == "$OUTPUT_ROOT_REAL/"* ]] \
    || return 1
  [[ "$resolved" != "$OUTPUT_ROOT_REAL/s8b-freeze" \
      && "$resolved" != "$OUTPUT_ROOT_REAL/s8b-freeze/"* ]] || return 1
  [[ "$resolved" != "$OUTPUT_ROOT_REAL/campaigns" \
      && "$resolved" != "$OUTPUT_ROOT_REAL/campaigns/"* ]]
}

# 出典: submit_certify.sh:50-73 @ e9b6f69
POLICY="$REPO_ROOT/tools/pegasus/policy.json"
FLOOR_POLICY="$REPO_ROOT/tools/pegasus/policies/floor_v1.json"
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  echo "policy file missing, not regular, or a symlink: $POLICY" >&2
  exit 2
fi
if [[ ! -f "$FLOOR_POLICY" || -L "$FLOOR_POLICY" ]]; then
  echo "floor policy file missing, not regular, or a symlink: $FLOOR_POLICY" >&2
  exit 2
fi
policy_output=""
policy_rc=0
policy_output=$(python3 -I -B - "$POLICY" "$FLOOR_POLICY" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    floor_policy = json.load(handle)
for key in ("project", "queue"):
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
if type(policy.get("nodes")) is not int or policy["nodes"] <= 0:
    raise SystemExit("invalid policy field: nodes")
if (
    type(floor_policy.get("floor_walltime_s")) is not int
    or floor_policy["floor_walltime_s"] <= 0
):
    raise SystemExit("invalid floor policy field: floor_walltime_s")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(floor_policy["floor_walltime_s"])
PY
) || policy_rc=$?
if [[ "$policy_rc" -ne 0 ]]; then
  echo "cannot parse required floor policy" >&2
  exit 2
fi
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 4 ]]; then
  echo "floor policy yielded an unexpected field count" >&2
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
WALLTIME_S=${policy_values[3]}

if [[ "$JOB_SCRIPT_RAW" != /* ]]; then
  JOB_SCRIPT_RAW="$REPO_ROOT/$JOB_SCRIPT_RAW"
fi
if [[ ! -f "$JOB_SCRIPT_RAW" || -L "$JOB_SCRIPT_RAW" ]]; then
  echo "job script is not a non-symlink regular file: $JOB_SCRIPT_RAW" >&2
  exit 2
fi
JOB_SCRIPT=$(realpath -e -- "$JOB_SCRIPT_RAW") || exit 2
if [[ "$JOB_SCRIPT" != "$REPO_ROOT/"* ]]; then
  echo "job script must be inside repo root" >&2
  exit 2
fi
JOB_SCRIPT_RELATIVE=${JOB_SCRIPT#"$REPO_ROOT/"}

# 出典: submit_certify.sh:75-91 @ e9b6f69
# source identity は staging/claims を作る前に確定する。
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD) || exit 2
if [[ ! "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "cannot resolve a full lowercase source commit" >&2
  exit 2
fi
if ! git -C "$REPO_ROOT" diff --quiet HEAD --; then
  echo "tracked working tree bytes are dirty; floor submission aborted" >&2
  exit 2
fi
if ! git -C "$REPO_ROOT" diff --cached --quiet HEAD --; then
  echo "tracked index bytes are dirty; floor submission aborted" >&2
  exit 2
fi
untracked_outside_output=0
untracked_list=$(mktemp "${TMPDIR:-/tmp}/izanagi-floor-untracked.XXXXXX") || {
  echo "cannot create temporary untracked-path record" >&2
  exit 2
}
untracked_git_rc=0
git -C "$REPO_ROOT" ls-files --others --exclude-standard -z \
  >"$untracked_list" || untracked_git_rc=$?
if [[ "$untracked_git_rc" -ne 0 ]]; then
  rm -f -- "$untracked_list"
  echo "cannot inspect untracked repository content" >&2
  exit "$untracked_git_rc"
fi
while IFS= read -r -d '' untracked; do
  if [[ "$untracked" != output/* ]]; then
    printf 'untracked path outside output/: %q\n' "$untracked" >&2
    untracked_outside_output=1
  fi
done <"$untracked_list"
rm -f -- "$untracked_list"
if [[ "$untracked_outside_output" -ne 0 ]]; then
  echo "untracked content outside output/; floor submission aborted" >&2
  exit 2
fi
if ! git -C "$REPO_ROOT" ls-files --error-unmatch -- "$JOB_SCRIPT_RELATIVE" >/dev/null; then
  echo "job script is not tracked: $JOB_SCRIPT_RELATIVE" >&2
  exit 2
fi
repo_blob_hash_rc=0
JOB_SCRIPT_SHA256=$(
  git -C "$REPO_ROOT" cat-file blob "$SOURCE_COMMIT:$JOB_SCRIPT_RELATIVE" \
    | sha256sum \
    | awk '{print $1}'
) || repo_blob_hash_rc=$?
if [[ "$repo_blob_hash_rc" -ne 0 ]]; then
  echo "cannot read committed job script blob" >&2
  exit "$repo_blob_hash_rc"
fi
if [[ ! "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "cannot hash committed job script blob" >&2
  exit 2
fi
WORKING_TREE_JOB_SCRIPT_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}')
if [[ ! "$WORKING_TREE_JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "cannot hash working-tree job script" >&2
  exit 2
fi
if [[ "$WORKING_TREE_JOB_SCRIPT_SHA256" != "$JOB_SCRIPT_SHA256" ]]; then
  echo "working-tree job script differs from committed blob" >&2
  exit 2
fi

# 出典: submit_certify.sh:93-101 @ e9b6f69
if [[ -z "$ATTEMPTS_ROOT_RAW" ]]; then
  ATTEMPTS_ROOT="$OUTPUT_ROOT/env/pegasus/floor/attempts"
elif [[ "$ATTEMPTS_ROOT_RAW" == /* ]]; then
  ATTEMPTS_ROOT=$ATTEMPTS_ROOT_RAW
else
  ATTEMPTS_ROOT="$REPO_ROOT/$ATTEMPTS_ROOT_RAW"
fi
SUBMISSIONS_ROOT="$ATTEMPTS_ROOT/submissions"
for staging_path in "$ATTEMPTS_ROOT" "$SUBMISSIONS_ROOT"; do
  if ! assert_safe_output_path "$staging_path"; then
    echo "unsafe submission path component or containment: $staging_path" >&2
    exit 2
  fi
done
mkdir -p "$SUBMISSIONS_ROOT"
for staging_path in "$ATTEMPTS_ROOT" "$SUBMISSIONS_ROOT"; do
  if ! assert_safe_output_path "$staging_path"; then
    echo "unsafe submission path after parent creation: $staging_path" >&2
    exit 2
  fi
done

NONCE=$(python3 -I -B - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)
if [[ ! "$NONCE" =~ ^[0-9a-f]{32}$ ]]; then
  echo "nonce generator returned an invalid value" >&2
  exit 2
fi
SUBMISSION_DIR="$SUBMISSIONS_ROOT/$NONCE"
if ! assert_safe_output_path "$SUBMISSION_DIR"; then
  echo "unsafe submission leaf component or containment" >&2
  exit 2
fi
if ! mkdir "$SUBMISSION_DIR"; then
  echo "submission staging already exists or cannot be created (create-only): $SUBMISSION_DIR" >&2
  exit 2
fi
if ! assert_safe_output_path "$SUBMISSION_DIR"; then
  echo "unsafe submission leaf after creation" >&2
  exit 2
fi
# raw capture redirections must not truncate a concurrently created record.
set -o noclobber

# 出典: submit_certify.sh:103-163 @ e9b6f69
capture_required() {
  local name=$1
  local rc=0
  shift
  "$@" >"$SUBMISSION_DIR/${name}.stdout" 2>"$SUBMISSION_DIR/${name}.stderr" || rc=$?
  printf '%s\n' "$rc" >"$SUBMISSION_DIR/${name}.rc"
  return "$rc"
}

preflight_rc=0
if [[ "$DRY_RUN" -eq 1 ]]; then
  for name in qstat_Q pegasusinfo rbudgetcheck check_quota; do
    printf '%s\n' "not run (--dry-run)" >"$SUBMISSION_DIR/${name}.stdout"
    : >"$SUBMISSION_DIR/${name}.stderr"
    printf '0\n' >"$SUBMISSION_DIR/${name}.rc"
  done
else
  capture_required qstat_Q qstat -Q || preflight_rc=1
  capture_required pegasusinfo pegasusinfo || preflight_rc=1
  capture_required rbudgetcheck rbudgetcheck || preflight_rc=1
  capture_required check_quota check_quota || preflight_rc=1
fi

PREPARED_AT=$(date +%s)
python3 -I -B - "$SUBMISSION_DIR" "$SOURCE_COMMIT" "$JOB_SCRIPT_RELATIVE" \
  "$JOB_SCRIPT_SHA256" "$NONCE" "$PREPARED_AT" "$PROJECT" "$QUEUE" "$NODES" \
  "$WALLTIME_S" "$DRY_RUN" <<'PY'
import json
import os
import sys

(root, source_commit, script_path, script_sha, nonce, prepared_at, project,
 queue, nodes, walltime_s, dry_run) = sys.argv[1:]
captures = {}
for name in ("qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"):
    def read(suffix):
        with open(
            os.path.join(root, name + suffix), encoding="utf-8", errors="replace"
        ) as handle:
            return handle.read()
    captures[name] = {
        "rc": int(read(".rc").strip()),
        "stdout_raw": read(".stdout"),
        "stderr_raw": read(".stderr"),
    }
payload = {
    "schema_version": "pegasus-floor-pre-submit/v1",
    "source_commit": source_commit,
    "job_script_path": script_path,
    "job_script_sha256": script_sha,
    "nonce": nonce,
    "prepared_at": int(prepared_at),
    "request": {
        "project": project,
        "queue": queue,
        "nodes": int(nodes),
        "elapstim_req_s": int(walltime_s),
    },
    "preflight": captures,
    "dry_run": bool(int(dry_run)),
}
with open(os.path.join(root, "pre-submit.json"), "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY

if [[ "$preflight_rc" -ne 0 ]]; then
  echo "one or more preflight captures failed; qsub not executed" >&2
  exit 3
fi

provision_claim_root() {
  local claim_root="$OUTPUT_ROOT/claims"
  local mode

  if ! assert_safe_output_path "$claim_root"; then
    echo "unsafe claims path component or containment" >&2
    return 2
  fi
  if [[ -e "$claim_root" ]]; then
    if [[ ! -d "$claim_root" ]]; then
      echo "claims root must be a directory" >&2
      return 2
    fi
    mode=$(stat -Lc '%a' -- "$claim_root") || return 2
    if [[ "$mode" != 700 ]]; then
      echo "existing claims root mode must be exactly 0700" >&2
      return 2
    fi
  else
    if ! mkdir -m 0700 "$claim_root"; then
      echo "cannot create claims root (create-only)" >&2
      return 2
    fi
  fi
  if ! assert_safe_output_path "$claim_root"; then
    echo "unsafe claims path after provisioning" >&2
    return 2
  fi
}
provision_claim_root || exit 2

# 出典: submit_certify.sh:170-237 @ e9b6f69
export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE,IZANAGI_PEGASUS_THIRDPARTY_CACHE=$THIRD_PARTY_CACHE_ROOT"
SCHEDULER_STDOUT="$SUBMISSION_DIR/scheduler.stdout"
SCHEDULER_STDERR="$SUBMISSION_DIR/scheduler.stderr"
for scheduler_path in "$SCHEDULER_STDOUT" "$SCHEDULER_STDERR"; do
  if ! assert_safe_output_path "$scheduler_path"; then
    echo "unsafe scheduler output path or containment: $scheduler_path" >&2
    exit 2
  fi
done
qsub_cmd=(
  qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR"
  -v "$export_spec" "$JOB_SCRIPT"
)
printf 'qsub command:'
printf ' %q' "${qsub_cmd[@]}"
printf '\n'

SUBMITTED_AT=$(date +%s)
if [[ "$DRY_RUN" -eq 1 ]]; then
  REQUEST_ID="dry-run-$NONCE"
  printf '%s\n' "dry-run: qsub was not executed" >"$SUBMISSION_DIR/qsub.stdout"
  : >"$SUBMISSION_DIR/qsub.stderr"
  printf '0\n' >"$SUBMISSION_DIR/qsub.rc"
else
  qsub_rc=0
  (
    cd "$REPO_ROOT"
    "${qsub_cmd[@]}"
  ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr" || qsub_rc=$?
  printf '%s\n' "$qsub_rc" >"$SUBMISSION_DIR/qsub.rc"
  if [[ "$qsub_rc" -ne 0 ]]; then
    echo "qsub failed; see submission record at $SUBMISSION_DIR" >&2
    exit "$qsub_rc"
  fi
  REQUEST_ID=$(python3 -I -B - "$SUBMISSION_DIR/qsub.stdout" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
match = re.search(r"Request\s+(\S+)\s+submitted", text)
if match:
    print(match.group(1).rstrip("."))
else:
    tokens = text.split()
    if len(tokens) == 1:
        print(tokens[0])
    else:
        raise SystemExit(2)
PY
  ) || {
    echo "qsub succeeded but request ID could not be parsed" >&2
    exit 4
  }
fi

python3 -I -B - "$SUBMISSION_DIR/pre-submit.json" \
  "$SUBMISSION_DIR/submit-receipt.json" "$REQUEST_ID" "$SUBMITTED_AT" <<'PY'
import json
import sys

source, target, request_id, submitted_at = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    pre = json.load(handle)
payload = {
    "schema_version": "pegasus-floor-submit-receipt/v1",
    "source_commit": pre["source_commit"],
    "job_script_path": pre["job_script_path"],
    "job_script_sha256": pre["job_script_sha256"],
    "job_id": request_id,
    "nonce": pre["nonce"],
    "submitted_at": int(submitted_at),
    "request": pre["request"],
    "preflight": pre["preflight"],
    "dry_run": pre["dry_run"],
}
with open(target, "x", encoding="utf-8") as handle:
    json.dump(
        payload,
        handle,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    handle.write("\n")
PY

echo "submission record: $SUBMISSION_DIR/submit-receipt.json"
echo "request ID: $REQUEST_ID"
