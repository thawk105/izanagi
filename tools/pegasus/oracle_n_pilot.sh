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

# The unset mode is retained only for the pre-R33 build/round diagnostic path.
# New R33 submissions must use reserve or consume and never carry an attempt id.
IZANAGI_PILOT_MODE=${IZANAGI_PILOT_MODE:-legacy}
case "$IZANAGI_PILOT_MODE" in
  reserve|consume|legacy) ;;
  *) fail "IZANAGI_PILOT_MODE must be reserve or consume" ;;
esac

if [[ "$IZANAGI_PILOT_MODE" == legacy ]]; then
  for variable in IZANAGI_PILOT_PROTOCOL IZANAGI_PILOT_OUTPUT_ROOT \
                  IZANAGI_PILOT_CACHE_ROOT IZANAGI_PILOT_ATTEMPT; do
    [[ -n "${!variable:-}" ]] || fail "$variable is required"
  done
  [[ "$IZANAGI_PILOT_ATTEMPT" =~ ^[A-Za-z0-9._-]+$ ]] \
    || fail "unsafe attempt id"
  IZANAGI_PILOT_CAMPAIGN_RUN_ID=$IZANAGI_PILOT_ATTEMPT
  IZANAGI_PILOT_ADMISSION_MANIFEST=""
else
  for variable in IZANAGI_PILOT_PROTOCOL IZANAGI_PILOT_OUTPUT_ROOT \
                  IZANAGI_PILOT_CAMPAIGN_RUN_ID IZANAGI_PILOT_ADMISSION_MANIFEST; do
    [[ -n "${!variable:-}" ]] || fail "$variable is required"
  done
  [[ "$IZANAGI_PILOT_CAMPAIGN_RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || fail "unsafe campaign run id"
  [[ "$IZANAGI_PILOT_ADMISSION_MANIFEST" != *','* \
      && "$IZANAGI_PILOT_ADMISSION_MANIFEST" != *$'\n'* ]] \
    || fail "admission manifest path contains qsub delimiter"
  if [[ "$IZANAGI_PILOT_MODE" == consume ]]; then
    for variable in IZANAGI_PILOT_CACHE_ROOT IZANAGI_PILOT_ALLOCATION_INDEX; do
      [[ -n "${!variable:-}" ]] || fail "$variable is required for consume"
    done
    [[ "$IZANAGI_PILOT_ALLOCATION_INDEX" =~ ^[012]$ ]] \
      || fail "allocation index must be 0, 1, or 2"
  else
    [[ -z "${IZANAGI_PILOT_CACHE_ROOT:-}" ]] \
      || fail "reserve must not receive a cache root"
    [[ -z "${IZANAGI_PILOT_ALLOCATION_INDEX:-}" ]] \
      || fail "reserve must not receive an allocation index"
  fi
fi

[[ "${IZANAGI_PILOT_BUILD_ONLY:-0}" =~ ^[01]$ ]] \
  || fail "unsafe build-only flag"
IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT=${IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT:-0}
[[ "$IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT" =~ ^[01]$ ]] \
  || fail "unsafe irreversible holdout confirmation"
if [[ "$IZANAGI_PILOT_MODE" != legacy ]]; then
  [[ "$IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT" == 1 ]] \
    || fail "reserve/consume requires irreversible holdout confirmation"
  [[ "${IZANAGI_PILOT_BUILD_ONLY:-0}" == 0 ]] \
    || fail "R33 mode cannot use build-only"
fi
if [[ -n "${IZANAGI_PILOT_ROUNDS:-}" ]]; then
  [[ "$IZANAGI_PILOT_ROUNDS" =~ ^[1-9][0-9]*$ ]] || fail "unsafe rounds"
fi
if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
  [[ -z "${IZANAGI_PILOT_ROUNDS:-}" ]] || fail "reserve must not receive rounds"
elif [[ "$IZANAGI_PILOT_MODE" == consume ]]; then
  [[ "${IZANAGI_PILOT_ROUNDS:-11}" == 11 ]] \
    || fail "consume rounds must be 11"
fi

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP
REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P) || fail "cannot resolve repo root"
[[ ! -L "$PBS_O_WORKDIR" ]] || fail "repo root must not be a symlink"
git -C "$REPO_ROOT" diff-index --quiet HEAD -- || fail "repo has tracked changes"
[[ -z "$(git -C "$REPO_ROOT" ls-files --others --exclude-standard)" ]] \
  || fail "repo has untracked files"
REPO_HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD) \
  || fail "cannot resolve repo HEAD"
[[ "$REPO_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail "repo HEAD is not a full lowercase commit"

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
[[ -d "$OUTPUT_ROOT" && ! -L "$IZANAGI_PILOT_OUTPUT_ROOT" ]] \
  || fail "output root must be a non-symlink directory"
[[ "$OUTPUT_ROOT" != "$REPO_ROOT" && "$OUTPUT_ROOT" != "$REPO_ROOT/"* ]] \
  || fail "output root must be outside the repo"

if [[ "$IZANAGI_PILOT_MODE" == consume ]]; then
  CACHE_ROOT=$(realpath -e -- "$IZANAGI_PILOT_CACHE_ROOT") \
    || fail "cannot resolve persistent cache root"
  [[ -d "$CACHE_ROOT" && ! -L "$IZANAGI_PILOT_CACHE_ROOT" ]] \
    || fail "cache root must be a non-symlink directory"
  [[ "$CACHE_ROOT" != "$REPO_ROOT" && "$CACHE_ROOT" != "$REPO_ROOT/"* ]] \
    || fail "cache root must be outside the repo"
elif [[ "$IZANAGI_PILOT_MODE" == legacy ]]; then
  CACHE_ROOT=$(realpath -e -- "$IZANAGI_PILOT_CACHE_ROOT") \
    || fail "cannot resolve persistent cache root"
  [[ -d "$CACHE_ROOT" && ! -L "$IZANAGI_PILOT_CACHE_ROOT" ]] \
    || fail "cache root must be a non-symlink directory"
  [[ "$CACHE_ROOT" != "$REPO_ROOT" && "$CACHE_ROOT" != "$REPO_ROOT/"* ]] \
    || fail "cache root must be outside the repo"
else
  CACHE_ROOT=""
fi

if [[ "$IZANAGI_PILOT_MODE" == legacy ]]; then
  RUN_DIR="$OUTPUT_ROOT/$IZANAGI_PILOT_ATTEMPT"
  [[ -d "$RUN_DIR" && ! -L "$RUN_DIR" ]] \
    || fail "submit wrapper must provision the attempt directory"
else
  CAMPAIGN_DIR="$OUTPUT_ROOT/$IZANAGI_PILOT_CAMPAIGN_RUN_ID"
  [[ -d "$CAMPAIGN_DIR" && ! -L "$CAMPAIGN_DIR" ]] \
    || fail "submit wrapper must provision the campaign directory"
  if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
    RUN_DIR="$CAMPAIGN_DIR/reserve"
  else
    RUN_DIR="$CAMPAIGN_DIR/allocation-$IZANAGI_PILOT_ALLOCATION_INDEX"
  fi
  [[ -d "$RUN_DIR" && ! -L "$RUN_DIR" ]] \
    || fail "submit wrapper must provision the mode directory"
fi

if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
  MANIFEST_PARENT_RAW=${IZANAGI_PILOT_ADMISSION_MANIFEST%/*}
  [[ "$MANIFEST_PARENT_RAW" != "$IZANAGI_PILOT_ADMISSION_MANIFEST" ]] \
    || MANIFEST_PARENT_RAW="."
  MANIFEST_PARENT=$(realpath -e -- "$MANIFEST_PARENT_RAW") \
    || fail "cannot resolve admission manifest parent"
  MANIFEST="$MANIFEST_PARENT/${IZANAGI_PILOT_ADMISSION_MANIFEST##*/}"
  [[ ! -e "$MANIFEST" && ! -L "$MANIFEST" ]] \
    || fail "admission manifest output already exists"
elif [[ "$IZANAGI_PILOT_MODE" == consume ]]; then
  MANIFEST=$(realpath -e -- "$IZANAGI_PILOT_ADMISSION_MANIFEST") \
    || fail "cannot resolve admission manifest"
  [[ -f "$MANIFEST" && ! -L "$IZANAGI_PILOT_ADMISSION_MANIFEST" ]] \
    || fail "admission manifest must be a non-symlink regular file"
else
  MANIFEST=""
fi

if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
  RESULT="$RUN_DIR/reserve-driver-output.json"
else
  RESULT="$RUN_DIR/result.json"
fi
[[ ! -e "$RESULT" && ! -L "$RESULT" ]] || fail "result already exists"

export TMPDIR="/scr/${PBS_JOBID//:/_}-oracle-n-pilot"
mkdir -m 0700 "$TMPDIR" || fail "scratch directory must be create-only"
mkdir -m 0700 "$TMPDIR/worktrees" "$TMPDIR/dummy-trace"
mkdir -m 0700 "$TMPDIR/python-bin"
ln -s "$PY" "$TMPDIR/python-bin/python3"
export PATH="$TMPDIR/python-bin:$PATH"

POLICY="$REPO_ROOT/tools/pegasus/policy.json"
[[ -f "$POLICY" && ! -L "$POLICY" ]] \
  || fail "third-party policy must be a non-symlink regular file"
policy_rc=0
"$PY" -I -B - "$POLICY" \
  >"$RUN_DIR/third-party-policy.stdout" \
  2>"$RUN_DIR/third-party-policy.stderr" <<'PY' || policy_rc=$?
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
text_fields = (
    "gflags_expected_head",
    "glog_expected_head",
)
for key in text_fields:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
for key in text_fields:
    print(policy[key])
PY
if [[ "$policy_rc" -ne 0 ]]; then
  fail "cannot load third-party policy"
fi
mapfile -t third_party_policy <"$RUN_DIR/third-party-policy.stdout"
[[ "${#third_party_policy[@]}" -eq 2 ]] \
  || fail "third-party policy produced an unexpected field count"
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"
GFLAGS_EXPECTED_HEAD=${third_party_policy[0]}
GLOG_EXPECTED_HEAD=${third_party_policy[1]}

if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  fail "gflags source path missing"
fi
gflags_head_rc=0
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD \
  2>"$RUN_DIR/gflags-source-head.stderr") || gflags_head_rc=$?
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$RUN_DIR/gflags-source-head.stdout"
if [[ "$gflags_head_rc" -ne 0 ]]; then
  fail "cannot resolve gflags source HEAD"
fi
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  fail "gflags source HEAD mismatch"
fi
gflags_status_rc=0
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$RUN_DIR/gflags-source-status.stderr") || gflags_status_rc=$?
printf '%s' "$GFLAGS_STATUS" >"$RUN_DIR/gflags-source-status.stdout"
if [[ "$gflags_status_rc" -ne 0 ]]; then
  fail "cannot inspect gflags working tree"
fi
if [[ -n "$GFLAGS_STATUS" ]]; then
  fail "gflags working tree is dirty"
fi

if [[ "$IZANAGI_PILOT_MODE" == consume || "$IZANAGI_PILOT_MODE" == legacy ]]; then
  GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
  GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
  mkdir "$GFLAGS_BUILD_DIR" \
    >"$RUN_DIR/gflags-build-dir.stdout" \
    2>"$RUN_DIR/gflags-build-dir.stderr" \
    || fail "cannot create gflags build directory"
  gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
    "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR")
  gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
  gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
  timeout 60 "${gflags_configure_argv[@]}" \
    >"$RUN_DIR/gflags-configure.stdout" \
    2>"$RUN_DIR/gflags-configure.stderr" \
    || fail "gflags configure failed"
  timeout 60 "${gflags_build_argv[@]}" \
    >"$RUN_DIR/gflags-build.stdout" \
    2>"$RUN_DIR/gflags-build.stderr" \
    || fail "gflags build failed"
  timeout 60 "${gflags_install_argv[@]}" \
    >"$RUN_DIR/gflags-install.stdout" \
    2>"$RUN_DIR/gflags-install.stderr" \
    || fail "gflags install failed"
fi

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  fail "glog source path missing"
fi
glog_head_rc=0
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD \
  2>"$RUN_DIR/glog-source-head.stderr") || glog_head_rc=$?
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$RUN_DIR/glog-source-head.stdout"
if [[ "$glog_head_rc" -ne 0 ]]; then
  fail "cannot resolve glog source HEAD"
fi
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  fail "glog source HEAD mismatch"
fi
glog_status_rc=0
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all \
  2>"$RUN_DIR/glog-source-status.stderr") || glog_status_rc=$?
printf '%s' "$GLOG_STATUS" >"$RUN_DIR/glog-source-status.stdout"
if [[ "$glog_status_rc" -ne 0 ]]; then
  fail "cannot inspect glog working tree"
fi
if [[ -n "$GLOG_STATUS" ]]; then
  fail "glog working tree is dirty"
fi

if [[ "$IZANAGI_PILOT_MODE" == consume || "$IZANAGI_PILOT_MODE" == legacy ]]; then
  GLOG_BUILD_DIR="$TMPDIR/glog-build"
  GLOG_INSTALL_DIR="$TMPDIR/glog-install"
  mkdir "$GLOG_BUILD_DIR" \
    >"$RUN_DIR/glog-build-dir.stdout" \
    2>"$RUN_DIR/glog-build-dir.stderr" \
    || fail "cannot create glog build directory"
  glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
    -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
    "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR")
  glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
  glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
  timeout 120 "${glog_configure_argv[@]}" \
    >"$RUN_DIR/glog-configure.stdout" \
    2>"$RUN_DIR/glog-configure.stderr" \
    || fail "glog configure failed"
  timeout 120 "${glog_build_argv[@]}" \
    >"$RUN_DIR/glog-build.stdout" \
    2>"$RUN_DIR/glog-build.stderr" \
    || fail "glog build failed"
  timeout 120 "${glog_install_argv[@]}" \
    >"$RUN_DIR/glog-install.stdout" \
    2>"$RUN_DIR/glog-install.stderr" \
    || fail "glog install failed"

  CMAKE_PREFIX_PATH_PREVIOUSLY_SET=false
  CMAKE_PREFIX_PATH_PREVIOUS_VALUE=""
  if [[ ${CMAKE_PREFIX_PATH+x} ]]; then
    CMAKE_PREFIX_PATH_PREVIOUSLY_SET=true
    CMAKE_PREFIX_PATH_PREVIOUS_VALUE=$CMAKE_PREFIX_PATH
  fi
  export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"
  printf 'previously_set=%s\nprevious_value=%s\ncurrent_value=%s\n' \
    "$CMAKE_PREFIX_PATH_PREVIOUSLY_SET" "$CMAKE_PREFIX_PATH_PREVIOUS_VALUE" \
    "$CMAKE_PREFIX_PATH" >"$RUN_DIR/cmake-prefix-path.stdout" \
    2>"$RUN_DIR/cmake-prefix-path.stderr"
fi

if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
  driver=(
    "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_oracle_n_pilot.py"
    --protocol "$PROTOCOL"
    --output "$RESULT"
    --observed-repo-head "$REPO_HEAD"
    --reserve-only
    --campaign-run-id "$IZANAGI_PILOT_CAMPAIGN_RUN_ID"
    --admission-manifest "$MANIFEST"
    --confirm-irreversible-pilot-holdout
  )
elif [[ "$IZANAGI_PILOT_MODE" == consume ]]; then
  driver=(
    "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_oracle_n_pilot.py"
    --protocol "$PROTOCOL"
    --output "$RESULT"
    --observed-repo-head "$REPO_HEAD"
    --consume-only
    --campaign-run-id "$IZANAGI_PILOT_CAMPAIGN_RUN_ID"
    --allocation-index "$IZANAGI_PILOT_ALLOCATION_INDEX"
    --admission-manifest "$MANIFEST"
    --cache-root "$CACHE_ROOT"
    --rounds 11
    --confirm-irreversible-pilot-holdout
  )
else
  driver=(
    "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_oracle_n_pilot.py"
    --protocol "$PROTOCOL"
    --output "$RESULT"
    --attempt-id "$IZANAGI_PILOT_ATTEMPT"
    --observed-repo-head "$REPO_HEAD"
    --cache-root "$CACHE_ROOT"
  )
  if [[ "$IZANAGI_PILOT_BUILD_ONLY" == 1 ]]; then
    driver+=(--build-only)
  fi
  if [[ "$IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT" == 1 ]]; then
    driver+=(--confirm-irreversible-pilot-holdout)
  fi
  if [[ -n "${IZANAGI_PILOT_ROUNDS:-}" ]]; then
    driver+=(--rounds "$IZANAGI_PILOT_ROUNDS")
  fi
fi

cd "$REPO_ROOT"
"${driver[@]}"
if [[ "$IZANAGI_PILOT_MODE" == reserve ]]; then
  [[ -f "$MANIFEST" && ! -L "$MANIFEST" ]] \
    || fail "driver did not create a regular admission manifest"
  CHECKED_ARTIFACT="$MANIFEST"
else
  [[ -f "$RESULT" && ! -L "$RESULT" ]] || fail "driver did not create a regular result"
  CHECKED_ARTIFACT="$RESULT"
fi
"$PY" -I -B - "$CHECKED_ARTIFACT" "$REPO_ROOT" <<'PY'
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
