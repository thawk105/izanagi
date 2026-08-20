#!/bin/bash
# Login-node wrapper: provision repo-external output/cache and bind scheduler logs.
set -Eeuo pipefail
umask 077

usage() {
  cat <<'EOF'
usage: submit_oracle_n_pilot.sh [--dry-run] --mode reserve|consume
       --protocol PATH --output-root PATH --campaign-run-id ID
       --admission-manifest PATH [--allocation-index 0|1|2]
       [--cache-root PATH] --confirm-irreversible-pilot-holdout
       [--job-script PATH] [--repo-root PATH]

legacy diagnostic compatibility:
       submit_oracle_n_pilot.sh [--dry-run] --protocol PATH
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
CAMPAIGN_RUN_ID=""
ALLOCATION_INDEX=""
ADMISSION_MANIFEST_RAW=""
ATTEMPT=""
MODE=""
ROUNDS=""
BUILD_ONLY=0
CONFIRM=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --mode)
      [[ $# -ge 2 ]] || fail "--mode requires reserve or consume"
      MODE=$2
      shift 2
      ;;
    --protocol)
      [[ $# -ge 2 ]] || fail "--protocol requires PATH"
      PROTOCOL_RAW=$2
      shift 2
      ;;
    --output-root)
      [[ $# -ge 2 ]] || fail "--output-root requires PATH"
      OUTPUT_ROOT_RAW=$2
      shift 2
      ;;
    --cache-root)
      [[ $# -ge 2 ]] || fail "--cache-root requires PATH"
      [[ -z "$CACHE_ROOT_RAW" ]] || fail "--cache-root may be specified once"
      CACHE_ROOT_RAW=$2
      shift 2
      ;;
    --campaign-run-id)
      [[ $# -ge 2 ]] || fail "--campaign-run-id requires ID"
      CAMPAIGN_RUN_ID=$2
      shift 2
      ;;
    --allocation-index)
      [[ $# -ge 2 ]] || fail "--allocation-index requires 0, 1, or 2"
      [[ -z "$ALLOCATION_INDEX" ]] || fail "--allocation-index may be specified once"
      ALLOCATION_INDEX=$2
      shift 2
      ;;
    --admission-manifest)
      [[ $# -ge 2 ]] || fail "--admission-manifest requires PATH"
      [[ -z "$ADMISSION_MANIFEST_RAW" ]] \
        || fail "--admission-manifest may be specified once"
      ADMISSION_MANIFEST_RAW=$2
      shift 2
      ;;
    --attempt)
      [[ $# -ge 2 ]] || fail "--attempt requires ID"
      ATTEMPT=$2
      shift 2
      ;;
    --rounds)
      [[ $# -ge 2 ]] || fail "--rounds requires N"
      ROUNDS=$2
      shift 2
      ;;
    --build-only)
      BUILD_ONLY=1
      shift
      ;;
    --confirm-irreversible-pilot-holdout)
      CONFIRM=1
      shift
      ;;
    --job-script)
      [[ $# -ge 2 ]] || fail "--job-script requires PATH"
      JOB_SCRIPT_RAW=$2
      JOB_SCRIPT_OVERRIDDEN=1
      shift 2
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || fail "--repo-root requires PATH"
      REPO_ROOT_RAW=$2
      REPO_ROOT_OVERRIDDEN=1
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$PROTOCOL_RAW" && -n "$OUTPUT_ROOT_RAW" ]] \
  || { usage >&2; fail "required option missing"; }
if [[ "$DRY_RUN" == 0 ]] && ((REPO_ROOT_OVERRIDDEN || JOB_SCRIPT_OVERRIDDEN)); then
  fail "--repo-root/--job-script overrides require --dry-run"
fi

if [[ -n "$MODE" ]]; then
  [[ "$MODE" == reserve || "$MODE" == consume ]] \
    || fail "--mode must be reserve or consume"
  [[ -z "$ATTEMPT" ]] || fail "--attempt is legacy-only"
  [[ "$BUILD_ONLY" == 0 ]] || fail "--build-only is legacy-only"
  [[ "$CAMPAIGN_RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || fail "unsafe campaign run id"
  [[ -n "$ADMISSION_MANIFEST_RAW" ]] \
    || fail "--admission-manifest is required for reserve/consume"
  [[ -z "$ADMISSION_MANIFEST_RAW" || "$ADMISSION_MANIFEST_RAW" != *','* ]] \
    || fail "admission manifest contains qsub delimiter"
  [[ -z "$ADMISSION_MANIFEST_RAW" || "$ADMISSION_MANIFEST_RAW" != *$'\n'* ]] \
    || fail "admission manifest contains newline"
  [[ "$CONFIRM" == 1 ]] \
    || fail "reserve/consume requires --confirm-irreversible-pilot-holdout"
  if [[ "$MODE" == reserve ]]; then
    [[ -z "$CACHE_ROOT_RAW" ]] || fail "reserve must not receive --cache-root"
    [[ -z "$ALLOCATION_INDEX" ]] || fail "reserve must not receive --allocation-index"
    [[ -z "$ROUNDS" ]] || fail "reserve must not receive --rounds"
  else
    [[ "$ALLOCATION_INDEX" =~ ^[012]$ ]] \
      || fail "consume allocation index must be 0, 1, or 2"
    [[ -n "$CACHE_ROOT_RAW" ]] || fail "consume requires --cache-root"
    if [[ -n "$ROUNDS" ]]; then
      [[ "$ROUNDS" == 11 ]] || fail "consume rounds must be 11"
    else
      ROUNDS=11
    fi
  fi
else
  [[ -z "$CAMPAIGN_RUN_ID" && -z "$ALLOCATION_INDEX" \
      && -z "$ADMISSION_MANIFEST_RAW" ]] \
    || fail "campaign/allocation/manifest require --mode"
  [[ -z "$ATTEMPT" ]] || true
  [[ "$ATTEMPT" =~ ^[A-Za-z0-9._-]+$ ]] || fail "unsafe attempt id"
  [[ -n "$CACHE_ROOT_RAW" ]] || fail "legacy mode requires --cache-root"
  [[ -z "$ROUNDS" || "$ROUNDS" =~ ^[1-9][0-9]*$ ]] \
    || fail "--rounds must be positive"
  [[ "$BUILD_ONLY" == 0 || -z "$ROUNDS" ]] \
    || fail "--build-only and --rounds are exclusive"
fi

for raw in "$REPO_ROOT_RAW" "$OUTPUT_ROOT_RAW"; do
  [[ -d "$raw" && ! -L "$raw" ]] || fail "directory missing or symlink: $raw"
done
if [[ -z "$MODE" ]]; then
  [[ -d "$CACHE_ROOT_RAW" && ! -L "$CACHE_ROOT_RAW" ]] \
    || fail "legacy cache root missing or symlink: $CACHE_ROOT_RAW"
fi
REPO_ROOT=$(cd "$REPO_ROOT_RAW" && pwd -P) || fail "cannot resolve repo root"
if [[ "$DRY_RUN" == 0 && "$SCRIPT_PATH" != "$REPO_ROOT/tools/pegasus/submit_oracle_n_pilot.sh" ]]; then
  fail "real submission requires the repo tools/pegasus/submit_oracle_n_pilot.sh"
fi
OUTPUT_ROOT=$(cd "$OUTPUT_ROOT_RAW" && pwd -P) || fail "cannot resolve output root"
[[ "$OUTPUT_ROOT" != "$REPO_ROOT" && "$OUTPUT_ROOT" != "$REPO_ROOT/"* ]] \
  || fail "output root must be outside repo"

PROTOCOL=$(realpath -e -- "$PROTOCOL_RAW") || fail "cannot resolve protocol"
[[ -f "$PROTOCOL" && ! -L "$PROTOCOL_RAW" ]] \
  || fail "protocol must be a non-symlink file"
if [[ "$JOB_SCRIPT_RAW" != /* ]]; then
  JOB_SCRIPT_RAW="$REPO_ROOT/$JOB_SCRIPT_RAW"
fi
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

if [[ -z "$MODE" ]]; then
  CACHE_ROOT=$(cd "$CACHE_ROOT_RAW" && pwd -P) || fail "cannot resolve cache root"
  [[ "$CACHE_ROOT" != "$REPO_ROOT" && "$CACHE_ROOT" != "$REPO_ROOT/"* ]] \
    || fail "cache root must be outside repo"
else
  if [[ "$MODE" == consume ]]; then
    CACHE_ROOT_PARENT_RAW=${CACHE_ROOT_RAW%/*}
    [[ "$CACHE_ROOT_PARENT_RAW" != "$CACHE_ROOT_RAW" ]] \
      || CACHE_ROOT_PARENT_RAW="."
    CACHE_ROOT_PARENT=$(realpath -e -- "$CACHE_ROOT_PARENT_RAW") \
      || fail "consume cache root parent does not exist"
    CACHE_ROOT="$CACHE_ROOT_PARENT/${CACHE_ROOT_RAW##*/}"
    [[ "$CACHE_ROOT" != "$CACHE_ROOT_PARENT" && "$CACHE_ROOT" != "$CACHE_ROOT_PARENT/" ]] \
      || fail "consume cache root leaf is invalid"
    [[ "$CACHE_ROOT" != "$REPO_ROOT" && "$CACHE_ROOT" != "$REPO_ROOT/"* ]] \
      || fail "cache root must be outside repo"
    [[ ! -e "$CACHE_ROOT" && ! -L "$CACHE_ROOT" ]] \
      || fail "consume cache root must be create-only"
    mkdir -m 0700 "$CACHE_ROOT" || fail "cannot provision allocation cache root"
  else
    CACHE_ROOT=""
  fi
fi

if [[ -z "$MODE" ]]; then
  RUN_DIR="$OUTPUT_ROOT/$ATTEMPT"
  mkdir -m 0700 "$RUN_DIR" || fail "attempt directory must be create-only"
else
  CAMPAIGN_DIR="$OUTPUT_ROOT/$CAMPAIGN_RUN_ID"
  if [[ "$MODE" == reserve ]]; then
    if [[ -e "$CAMPAIGN_DIR" || -L "$CAMPAIGN_DIR" ]]; then
      [[ -d "$CAMPAIGN_DIR" && ! -L "$CAMPAIGN_DIR" ]] \
        || fail "campaign directory is not a regular directory"
    else
      mkdir -m 0700 "$CAMPAIGN_DIR" || fail "cannot provision campaign directory"
    fi
  else
    [[ -d "$CAMPAIGN_DIR" && ! -L "$CAMPAIGN_DIR" ]] \
      || fail "consume requires the reserved campaign directory"
  fi
  if [[ "$MODE" == reserve ]]; then
    RUN_DIR="$CAMPAIGN_DIR/reserve"
  else
    RUN_DIR="$CAMPAIGN_DIR/allocation-$ALLOCATION_INDEX"
  fi
  mkdir -m 0700 "$RUN_DIR" || fail "mode directory must be create-only"
fi

if [[ -n "$MODE" ]]; then
  MANIFEST_PARENT_RAW=${ADMISSION_MANIFEST_RAW%/*}
  [[ "$MANIFEST_PARENT_RAW" != "$ADMISSION_MANIFEST_RAW" ]] \
    || MANIFEST_PARENT_RAW="."
  if [[ "$MODE" == reserve ]]; then
    MANIFEST_PARENT=$(realpath -e -- "$MANIFEST_PARENT_RAW") \
      || fail "cannot resolve admission manifest parent"
    MANIFEST="$MANIFEST_PARENT/${ADMISSION_MANIFEST_RAW##*/}"
    [[ "$MANIFEST" != "$REPO_ROOT" && "$MANIFEST" != "$REPO_ROOT/"* ]] \
      || fail "admission manifest must be outside repo"
    [[ ! -e "$MANIFEST" && ! -L "$MANIFEST" ]] \
      || fail "admission manifest output must be create-only"
  else
    MANIFEST=$(realpath -e -- "$ADMISSION_MANIFEST_RAW") \
      || fail "cannot resolve admission manifest"
    [[ -f "$MANIFEST" && ! -L "$ADMISSION_MANIFEST_RAW" ]] \
      || fail "admission manifest must be a non-symlink regular file"
  fi
else
  MANIFEST=""
fi

SCHEDULER_STDOUT="$RUN_DIR/scheduler.stdout"
SCHEDULER_STDERR="$RUN_DIR/scheduler.stderr"

if [[ "$DRY_RUN" == 0 ]]; then
  qstat -Q >/dev/null
  pegasusinfo >/dev/null
  rbudgetcheck >/dev/null
  check_quota >/dev/null
  (cd "$REPO_ROOT" && python3 -B -m orchestrator.campaign.queue_state) >/dev/null
fi

if [[ -z "$MODE" ]]; then
  for value in "$PROTOCOL" "$OUTPUT_ROOT" "$CACHE_ROOT" "$ATTEMPT"; do
    [[ "$value" != *','* && "$value" != *$'\n'* ]] \
      || fail "qsub -v value contains delimiter"
  done
  export_spec="IZANAGI_PILOT_PROTOCOL=$PROTOCOL,IZANAGI_PILOT_OUTPUT_ROOT=$OUTPUT_ROOT,IZANAGI_PILOT_CACHE_ROOT=$CACHE_ROOT,IZANAGI_PILOT_ATTEMPT=$ATTEMPT,IZANAGI_PILOT_BUILD_ONLY=$BUILD_ONLY,IZANAGI_PILOT_ROUNDS=$ROUNDS"
else
  for value in "$MODE" "$PROTOCOL" "$OUTPUT_ROOT" "$CAMPAIGN_RUN_ID" "$MANIFEST"; do
    [[ "$value" != *','* && "$value" != *$'\n'* ]] \
      || fail "qsub -v value contains delimiter"
  done
  export_spec="IZANAGI_PILOT_MODE=$MODE,IZANAGI_PILOT_PROTOCOL=$PROTOCOL,IZANAGI_PILOT_OUTPUT_ROOT=$OUTPUT_ROOT,IZANAGI_PILOT_CAMPAIGN_RUN_ID=$CAMPAIGN_RUN_ID,IZANAGI_PILOT_ADMISSION_MANIFEST=$MANIFEST,IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT=1"
  if [[ "$MODE" == consume ]]; then
    for value in "$CACHE_ROOT" "$ALLOCATION_INDEX" "$ROUNDS"; do
      [[ "$value" != *','* && "$value" != *$'\n'* ]] \
        || fail "qsub -v value contains delimiter"
    done
    export_spec+="${export_spec:+,}IZANAGI_PILOT_CACHE_ROOT=$CACHE_ROOT,IZANAGI_PILOT_ALLOCATION_INDEX=$ALLOCATION_INDEX,IZANAGI_PILOT_ROUNDS=$ROUNDS"
  fi
fi

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
  >"$RUN_DIR/qsub.stdout" 2>"$RUN_DIR/qsub.stderr"
