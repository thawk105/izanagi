#!/bin/bash
# Login-node wrapper: provision repo-external output and bind scheduler logs.
set -Eeuo pipefail
umask 077

usage() {
  cat <<'EOF'
usage: submit_oracle_n_pilot.sh [--dry-run] --protocol PATH
       --output-root PATH --cache-root PATH --attempt ID
       [--build-only | --rounds 1] [--job-script PATH] [--repo-root PATH]
EOF
}

fail() {
  echo "oracle n pilot submission refused: $*" >&2
  exit 2
}

SCRIPT_PATH=$(realpath -e -- "${BASH_SOURCE[0]}") || fail "cannot resolve script"
[[ -f "$SCRIPT_PATH" && ! -L "$SCRIPT_PATH" && ! -L "${BASH_SOURCE[0]}" ]] \
  || fail "submit script must be a non-symlink regular file"
SCRIPT_DIR=${SCRIPT_PATH%/*}
REPO_ROOT_RAW="$SCRIPT_DIR/../.."
JOB_SCRIPT_RAW="$SCRIPT_DIR/oracle_n_pilot.sh"
REPO_ROOT_OVERRIDDEN=0
JOB_SCRIPT_OVERRIDDEN=0
PROTOCOL_RAW=""
OUTPUT_ROOT_RAW=""
CACHE_ROOT_RAW=""
ATTEMPT=""
ROUNDS=""
BUILD_ONLY=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --protocol) [[ $# -ge 2 ]] || fail "--protocol requires PATH"; PROTOCOL_RAW=$2; shift 2 ;;
    --output-root) [[ $# -ge 2 ]] || fail "--output-root requires PATH"; OUTPUT_ROOT_RAW=$2; shift 2 ;;
    --cache-root) [[ $# -ge 2 ]] || fail "--cache-root requires PATH"; CACHE_ROOT_RAW=$2; shift 2 ;;
    --attempt) [[ $# -ge 2 ]] || fail "--attempt requires ID"; ATTEMPT=$2; shift 2 ;;
    --rounds) [[ $# -ge 2 ]] || fail "--rounds requires N"; ROUNDS=$2; shift 2 ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --job-script) [[ $# -ge 2 ]] || fail "--job-script requires PATH"; JOB_SCRIPT_RAW=$2; JOB_SCRIPT_OVERRIDDEN=1; shift 2 ;;
    --repo-root) [[ $# -ge 2 ]] || fail "--repo-root requires PATH"; REPO_ROOT_RAW=$2; REPO_ROOT_OVERRIDDEN=1; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
done

[[ -n "$PROTOCOL_RAW" && -n "$OUTPUT_ROOT_RAW" && -n "$CACHE_ROOT_RAW" \
    && -n "$ATTEMPT" ]] || { usage >&2; fail "required option missing"; }
if [[ "$DRY_RUN" == 0 ]] && ((REPO_ROOT_OVERRIDDEN || JOB_SCRIPT_OVERRIDDEN)); then
  fail "--repo-root/--job-script overrides require --dry-run"
fi
[[ "$ATTEMPT" =~ ^[A-Za-z0-9._-]+$ ]] || fail "unsafe attempt id"
[[ -z "$ROUNDS" || "$ROUNDS" =~ ^[1-9][0-9]*$ ]] || fail "--rounds must be positive"
[[ "$BUILD_ONLY" == 0 || -z "$ROUNDS" ]] || fail "--build-only and --rounds are exclusive"
for raw in "$REPO_ROOT_RAW" "$OUTPUT_ROOT_RAW" "$CACHE_ROOT_RAW"; do
  [[ -d "$raw" && ! -L "$raw" ]] || fail "directory missing or symlink: $raw"
done
REPO_ROOT=$(cd "$REPO_ROOT_RAW" && pwd -P) || fail "cannot resolve repo root"
if [[ "$DRY_RUN" == 0 && "$SCRIPT_PATH" != "$REPO_ROOT/tools/pegasus/submit_oracle_n_pilot.sh" ]]; then
  fail "real submission requires the repo tools/pegasus/submit_oracle_n_pilot.sh"
fi
OUTPUT_ROOT=$(cd "$OUTPUT_ROOT_RAW" && pwd -P) || fail "cannot resolve output root"
CACHE_ROOT=$(cd "$CACHE_ROOT_RAW" && pwd -P) || fail "cannot resolve cache root"
for external_root in "$OUTPUT_ROOT" "$CACHE_ROOT"; do
  [[ "$external_root" != "$REPO_ROOT" && "$external_root" != "$REPO_ROOT/"* ]] \
    || fail "output/cache root must be outside repo"
done
PROTOCOL=$(realpath -e -- "$PROTOCOL_RAW") || fail "cannot resolve protocol"
[[ -f "$PROTOCOL" && ! -L "$PROTOCOL_RAW" ]] || fail "protocol must be a non-symlink file"
if [[ "$JOB_SCRIPT_RAW" != /* ]]; then JOB_SCRIPT_RAW="$REPO_ROOT/$JOB_SCRIPT_RAW"; fi
JOB_SCRIPT=$(realpath -e -- "$JOB_SCRIPT_RAW") || fail "cannot resolve job script"
[[ -f "$JOB_SCRIPT" && -x "$JOB_SCRIPT" && ! -L "$JOB_SCRIPT_RAW" ]] \
  || fail "job script must be a non-symlink executable"
if [[ "$DRY_RUN" == 0 ]]; then
  [[ "$JOB_SCRIPT" == "$REPO_ROOT/"* ]] || fail "job script must be inside repo root"
  JOB_SCRIPT_RELATIVE=${JOB_SCRIPT#"$REPO_ROOT/"}
  SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD) \
    || fail "cannot resolve source commit"
  [[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "source commit is not full lowercase hex"
  git -C "$REPO_ROOT" diff --quiet HEAD -- \
    || fail "tracked working tree bytes are dirty"
  git -C "$REPO_ROOT" diff --cached --quiet HEAD -- \
    || fail "tracked index bytes are dirty"
  [[ -z "$(git -C "$REPO_ROOT" ls-files --others --exclude-standard)" ]] \
    || fail "repo has untracked files"
  git -C "$REPO_ROOT" ls-files --error-unmatch -- "$JOB_SCRIPT_RELATIVE" >/dev/null \
    || fail "job script is not tracked: $JOB_SCRIPT_RELATIVE"
  COMMITTED_JOB_SHA256=$(
    git -C "$REPO_ROOT" cat-file blob "$SOURCE_COMMIT:$JOB_SCRIPT_RELATIVE" \
      | sha256sum | awk '{print $1}'
  ) || fail "cannot hash committed job script blob"
  WORKTREE_JOB_SHA256=$(sha256sum "$JOB_SCRIPT" | awk '{print $1}') \
    || fail "cannot hash working-tree job script"
  [[ "$COMMITTED_JOB_SHA256" =~ ^[0-9a-f]{64}$ \
      && "$WORKTREE_JOB_SHA256" =~ ^[0-9a-f]{64}$ ]] \
    || fail "job script sha256 is invalid"
  [[ "$WORKTREE_JOB_SHA256" == "$COMMITTED_JOB_SHA256" ]] \
    || fail "working-tree job script differs from HEAD blob"
fi
for value in "$PROTOCOL" "$OUTPUT_ROOT" "$CACHE_ROOT" "$ATTEMPT"; do
  [[ "$value" != *','* && "$value" != *$'\n'* ]] || fail "qsub -v value contains delimiter"
done

ATTEMPT_DIR="$OUTPUT_ROOT/$ATTEMPT"
mkdir -m 0700 "$ATTEMPT_DIR" || fail "attempt directory must be create-only"
SCHEDULER_STDOUT="$ATTEMPT_DIR/scheduler.stdout"
SCHEDULER_STDERR="$ATTEMPT_DIR/scheduler.stderr"

if [[ "$DRY_RUN" == 0 ]]; then
  qstat -Q >/dev/null
  pegasusinfo >/dev/null
  rbudgetcheck >/dev/null
  check_quota >/dev/null
  (cd "$REPO_ROOT" && python3 -B -m orchestrator.campaign.queue_state) >/dev/null
fi

export_spec="IZANAGI_PILOT_PROTOCOL=$PROTOCOL,IZANAGI_PILOT_OUTPUT_ROOT=$OUTPUT_ROOT,IZANAGI_PILOT_CACHE_ROOT=$CACHE_ROOT,IZANAGI_PILOT_ATTEMPT=$ATTEMPT,IZANAGI_PILOT_BUILD_ONLY=$BUILD_ONLY,IZANAGI_PILOT_ROUNDS=$ROUNDS"
qsub_cmd=(
  qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR"
  -v "$export_spec" "$JOB_SCRIPT"
)
printf 'qsub command:'
printf ' %q' "${qsub_cmd[@]}"
printf '\n'

if [[ "$DRY_RUN" == 1 ]]; then
  exit 0
fi
(cd "$REPO_ROOT" && "${qsub_cmd[@]}") \
  >"$ATTEMPT_DIR/qsub.stdout" 2>"$ATTEMPT_DIR/qsub.stderr"
