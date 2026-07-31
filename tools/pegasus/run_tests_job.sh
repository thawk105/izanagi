#!/usr/bin/env bash
set -euo pipefail

for name in \
  IZANAGI_TEST_DISPATCH_ID \
  IZANAGI_TEST_DISPATCH_DIR \
  IZANAGI_TEST_SNAPSHOT_ROOT \
  IZANAGI_TEST_WORKER_AUTH \
  IZANAGI_TEST_RUNNER_RESULT \
  PBS_JOBID
do
  if [[ -z "${!name:-}" ]]; then
    printf 'required worker variable is missing: %s\n' "$name" >&2
    exit 125
  fi
done

if [[ ! "$IZANAGI_TEST_DISPATCH_ID" =~ ^[0-9]{14}-[0-9a-f]{16}$ ]]; then
  printf 'unsafe dispatch ID\n' >&2
  exit 125
fi

SAFE_PATH=/usr/local/bin:/usr/bin:/bin
PYTHON=
for candidate in \
  /usr/local/bin/python3.10 \
  /usr/bin/python3.10 \
  /usr/local/bin/python3 \
  /usr/bin/python3 \
  /bin/python3
do
  if [[ ! -x "$candidate" ]]; then
    continue
  fi
  if env -i \
      PATH="$SAFE_PATH" \
      LANG=C \
      LC_ALL=C \
      TZ=UTC \
      PYTHONNOUSERSITE=1 \
      PYTHONDONTWRITEBYTECODE=1 \
      "$candidate" -B -s -c \
      'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 125)'
  then
    PYTHON=$candidate
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  printf 'Python >= 3.10 with same-interpreter pytest/xdist is unavailable\n' >&2
  exit 125
fi

SUBMITTER="$IZANAGI_TEST_SNAPSHOT_ROOT/tools/pegasus/submit_tests.py"
if [[ ! -f "$SUBMITTER" || -L "$SUBMITTER" ]]; then
  printf 'snapshot submitter is unavailable\n' >&2
  exit 125
fi

exec env -i \
  PATH="$SAFE_PATH" \
  LANG=C \
  LC_ALL=C \
  TZ=UTC \
  PYTHONNOUSERSITE=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PIP_NO_INDEX=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PBS_JOBID="$PBS_JOBID" \
  IZANAGI_TEST_DISPATCH_ID="$IZANAGI_TEST_DISPATCH_ID" \
  IZANAGI_TEST_DISPATCH_DIR="$IZANAGI_TEST_DISPATCH_DIR" \
  IZANAGI_TEST_SNAPSHOT_ROOT="$IZANAGI_TEST_SNAPSHOT_ROOT" \
  IZANAGI_TEST_WORKER_AUTH="$IZANAGI_TEST_WORKER_AUTH" \
  IZANAGI_TEST_RUNNER_RESULT="$IZANAGI_TEST_RUNNER_RESULT" \
  "$PYTHON" -B -s "$SUBMITTER" worker \
    --dispatch-id "$IZANAGI_TEST_DISPATCH_ID" \
    --dispatch-dir "$IZANAGI_TEST_DISPATCH_DIR" \
    --snapshot-root "$IZANAGI_TEST_SNAPSHOT_ROOT" \
    --marker "$IZANAGI_TEST_WORKER_AUTH"
