# probe / launcher / 集計器 / 差分 probe の逐語 (job dir `probe/`、Codex author + fix 4 本。repo の実装面には入れない)

## run-measure.sh (sha256 `5fd1f27a1bf2ceb11479cb902534802ba091bcc6a48d977689b688c6cc1df83f`, 10155 byte)

```bash
#!/bin/bash
# T-2802 sequential, pinned-tree acceptance measurement.
set -uo pipefail
JOBDIR=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery
SLUG=dev-wave-t2802-floor-attempt-recovery
if [ "$#" -ne 3 ] || [[ ! "$1" =~ ^[0-9]{2}$ ]] || [[ ! "$2" =~ ^[AB]$ ]] || [[ ! "$3" =~ ^[123]$ ]]; then
  echo 'usage: run-measure.sh <NN> <A|B> <pair-slot>' >&2
  exit 2
fi
NN=$1 COND=$2 SLOT=$3
# Validate both pins before making any output, including runs/ or aborts/.
CONFIG=$(python3 - "$JOBDIR/measurement-tips.json" "$COND" <<'CONFIGPY'
import json, pathlib, re, sys
try:
    tips = json.loads(pathlib.Path(sys.argv[1]).read_text())
    for c in ('A', 'B'):
        t = tips[c]
        assert pathlib.Path(t['worktree']).is_absolute()
        assert not any(x in t['worktree'] for x in ('\n', '\r', '\t'))
        assert re.fullmatch('[0-9a-f]{40}', t['sha'])
    t = tips[sys.argv[2]]
    print(t['worktree'], t['sha'], tips['A']['sha'], tips['B']['sha'], sep='\t')
except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
    print('invalid measurement-tips.json: ' + str(exc), file=sys.stderr)
    sys.exit(2)
CONFIGPY
) || exit 2
IFS=$'\t' read -r WT MEASUREMENT_TIP A_SHA B_SHA <<< "$CONFIG"
TAG="$NN-$COND"
RUN="$JOBDIR/runs/$TAG"
LEADERS_MAX=1
L1_MAX=30
GATE_MAX_ROUNDS=90
mkdir -p "$JOBDIR/aborts" || exit 2
STAMP=$(date '+%Y%m%dT%H%M%S')
ABORT="$JOBDIR/aborts/$TAG-$STAMP.log"
abort() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $2" >> "$ABORT"; exit "$1"; }
if [ "$COND" != "A" ] && [ "$COND" != "B" ]; then abort 2 "bad condition: $COND"; fi

# 直列化: 最初に flock (fd 9)。取れなければ何も作らない。
exec 9> "$JOBDIR/measure.lock" || abort 94 "cannot open lock"
if ! flock -n 9; then abort 94 "another measurement holds the lock"; fi
# Count every run directory while holding the launch lock, before gate/output.
RUN_COUNT=$(python3 - "$JOBDIR/runs" <<'COUNTPY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
print(sum(p.is_dir() for p in root.iterdir()) if root.exists() else 0)
COUNTPY
) || abort 92 "cannot count runs"
if [ "$RUN_COUNT" -ge 12 ]; then abort 92 "12-run submission cap reached"; fi
if [ "$RUN_COUNT" -ge 6 ]; then
  # Direct launcher calls also respect the preregistered fixed stop.
  SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  python3 - "$JOBDIR" "$SCRIPT_DIR" <<'STOPPY'
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2802_ab_analyze import analyze, frozen_sets
job = Path(sys.argv[1])
paths = [p for p in (job / 'runs').iterdir() if p.is_dir()]
result = analyze(paths, frozen_sets(job / 'floor-subset-frozen.json'),
                 json.loads((job / 'measurement-tips.json').read_bytes()), warm_root=job)
sys.exit(92 if result['valid_pairs'] == 3 else 0)
STOPPY
  check_rc=$?
  if [ "$check_rc" -ne 0 ]; then abort 92 "fixed stop reached or cannot verify existing series"; fi
fi
if compgen -G "$JOBDIR/runs/$NN-*" > /dev/null; then abort 2 "run number exists (attempt reuse refused): $NN"; fi

export IZANAGI_ACCEPTANCE_SHARDS=3
unset PYTHONDONTWRITEBYTECODE
cd "$WT" || abort 90 "cd failed"

count_leaders() { ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG"; }
load1() { read -r l1 _ < /proc/loadavg; echo "$l1"; }
dirty_lines() {
  git -C "$WT" status --porcelain --untracked-files=all --ignore-submodules=none |
    python3 -c 'import sys; print(sum(not line.startswith("?? output/pegasus-dispatch/") for line in sys.stdin))'
}
glog() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$JOBDIR/aborts/$TAG-$STAMP.gate.log"; }

gate_open() {
  l1=$(load1)
  leaders=$(count_leaders)
  glog "gate: load1=$l1 leaders=$leaders (max $LEADERS_MAX, l1 < $L1_MAX)"
  python3 - "$l1" "$leaders" "$LEADERS_MAX" "$L1_MAX" <<'PY'
import sys
l1, leaders, lmax, l1max = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
sys.exit(0 if (leaders <= lmax and l1 < l1max) else 1)
PY
}

round=0; stable=0; opened=0
while [ "$round" -lt "$GATE_MAX_ROUNDS" ]; do
  round=$((round + 1))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  stable=$((stable + 1))
  if [ "$stable" -lt 2 ]; then sleep $((100 + RANDOM % 41)); continue; fi
  sleep $((RANDOM % 46))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  # 投入直前の照合: 門番へ戻った場合も HEAD / clean / diff を取り直す。
  TIP=$(git -C "$WT" rev-parse HEAD)
  DIRTY_BEFORE=$(dirty_lines) || abort 91 "status failed"
  if [ "$TIP" != "$MEASUREMENT_TIP" ]; then abort 95 "HEAD $TIP != measurement tip"; fi
  if [ "$DIRTY_BEFORE" -ne 0 ]; then abort 91 "worktree dirty before launch ($DIRTY_BEFORE lines)"; fi

  if ! git -C "$WT" diff --stat "$A_SHA" "$B_SHA" > "$JOBDIR/aborts/$TAG-$STAMP.diff.stat"; then
    abort 95 "cannot calculate tracked diff"
  fi
  DIFF_SHA=$(sha256sum "$JOBDIR/aborts/$TAG-$STAMP.diff.stat" | cut -d' ' -f1)

  # 照合中に門番が閉じたら、走番号を消費せず同じ round 上限で待ち直す。
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  LEADERS=$leaders
  L1=$l1
  opened=1
  break
done
if [ "$opened" -ne 1 ]; then abort 93 "gate never opened"; fi

# ここで初めて RUN dir を作る (既存なら mkdir が失敗 = 再利用拒否)。
mkdir -p "$JOBDIR/runs" || abort 2 "cannot create runs parent"
if ! mkdir "$RUN"; then abort 2 "mkdir failed (exists?): $RUN"; fi
CHAIN="$RUN/chain.log"
mv "$JOBDIR/aborts/$TAG-$STAMP.diff.stat" "$RUN/tracked-diff.stat" || abort 95 "diff evidence move failed"
echo $$ > "$RUN/measure.pid"
mv "$JOBDIR/aborts/$TAG-$STAMP.gate.log" "$RUN/gate.log" 2>/dev/null
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$CHAIN"; }
MAIN=$(git -C "$WT" rev-parse refs/heads/main)
START=$(date '+%Y-%m-%dT%H:%M:%S%z')
log "launch: cond=$COND slot=$SLOT tip=$TIP main=$MAIN leaders=$LEADERS load1=$L1"
env | grep '^IZANAGI_\|^PYTHONDONTWRITEBYTECODE' > "$RUN/env.txt"
echo "PYTHONDONTWRITEBYTECODE_SET=$( [ -n "${PYTHONDONTWRITEBYTECODE+x}" ] && echo yes || echo no )" >> "$RUN/env.txt"
python3 tools/run_tests.py > "$RUN/child.log" 2>&1
rc=$?
END=$(date '+%Y-%m-%dT%H:%M:%S%z')
ROOT=$(grep -o '"session_root":"[^"]*"' "$RUN/child.log" | head -1 | cut -d'"' -f4)
DIRTY_AFTER=$(dirty_lines) || DIRTY_AFTER=-1
TIP_AFTER=$(git -C "$WT" rev-parse HEAD) || TIP_AFTER=unavailable
log "finished: child_rc=$rc session_root=$ROOT dirty_after=$DIRTY_AFTER tip_after=$TIP_AFTER"

# 複製: shard-0/1/2 の junit.xml と report.json (+ dispatch/receipt.json があれば) を session/ へ。sha256 で検算。
COPY_OK=0
if [ -n "$ROOT" ] && [ -d "$ROOT" ]; then
  mkdir -p "$RUN/session"
  COPY_OK=1
  for s in 0 1 2; do
    mkdir -p "$RUN/session/shard-$s"
    for f in junit.xml report.json; do
      if [ -f "$ROOT/shard-$s/$f" ]; then
        cp "$ROOT/shard-$s/$f" "$RUN/session/shard-$s/$f" || COPY_OK=0
        a=$(sha256sum "$ROOT/shard-$s/$f" | cut -d' ' -f1); b=$(sha256sum "$RUN/session/shard-$s/$f" | cut -d' ' -f1)
        if [ "$a" != "$b" ]; then COPY_OK=0; log "sha mismatch shard-$s/$f"; fi
        echo "$b  shard-$s/$f" >> "$RUN/session/SHA256SUMS"
      else
        COPY_OK=0; log "missing $ROOT/shard-$s/$f"
      fi
    done
    if [ -f "$ROOT/shard-$s/dispatch/receipt.json" ]; then
      mkdir -p "$RUN/session/shard-$s/dispatch"
      cp "$ROOT/shard-$s/dispatch/receipt.json" "$RUN/session/shard-$s/dispatch/receipt.json" || { COPY_OK=0; log "receipt copy failed shard-$s"; }
    fi
  done
  if [ -f "$ROOT/junit.xml" ]; then cp "$ROOT/junit.xml" "$RUN/session/junit.xml" || { COPY_OK=0; log "top junit copy failed"; }; fi
fi
# Optional artifacts are also hashed when present; shard evidence stays mandatory.
if [ "$COPY_OK" -eq 1 ]; then
  for rel in junit.xml shard-0/dispatch/receipt.json shard-1/dispatch/receipt.json shard-2/dispatch/receipt.json; do
    if [ -f "$ROOT/$rel" ]; then
      a=$(sha256sum "$ROOT/$rel" | cut -d' ' -f1)
      b=$(sha256sum "$RUN/session/$rel" | cut -d' ' -f1)
      if [ "$a" != "$b" ]; then COPY_OK=0; fi
      echo "$b  $rel" >> "$RUN/session/SHA256SUMS" || COPY_OK=0
    fi
  done
  (cd "$RUN/session" && sha256sum --check SHA256SUMS) >> "$CHAIN" 2>&1 || COPY_OK=0
fi
log "copy_ok=$COPY_OK"
python3 - "$RUN/run.json" "$COND" "$TIP" "$MAIN" "$START" "$END" "$ROOT" "$LEADERS" "$L1" "$rc" "$DIRTY_BEFORE" "$DIRTY_AFTER" "$TIP_AFTER" "$NN" "$SLOT" "$COPY_OK" "$MEASUREMENT_TIP" "$LEADERS_MAX" "$L1_MAX" "$WT" "$DIFF_SHA" <<'PY'
import json, sys
(path, cond, tip, main, start, end, root, leaders, l1, rc, dirty_before, dirty_after, tip_after, nn, slot, copy_ok, mtip, lmax, l1max, wt, diff_sha) = sys.argv[1:]
env = {}
for line in open(path.replace("run.json", "env.txt")):
    k, _, v = line.rstrip("\n").partition("=")
    env[k] = v
json.dump({
    "run": nn, "condition": cond, "pair_slot": int(slot),
    "condition_worktree": wt, "expected_sha": mtip,
    "tracked_diff_stat_sha256": diff_sha,
    "valid_tree": tip == tip_after == mtip and dirty_before == dirty_after == "0",
    "measurement_tip": mtip, "tip_sha": tip, "tip_sha_after": tip_after,
    "main_sha_at_launch": main,
    "submitted_at": start, "finished_at": end,
    "session_dir": "session" if copy_ok == "1" else None,
    "session_dir_origin": root or None, "copy_ok": copy_ok == "1",
    "env": env, "other_leaders": int(leaders), "load1": float(l1), "rc": int(rc),
    "dirty_lines_before": int(dirty_before), "dirty_lines_after": int(dirty_after),
    "gate": {"leaders_max": int(lmax), "load1_max_exclusive": float(l1max),
             "leader_query": "ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc <slug>"},
}, open(path, "w"), indent=2, ensure_ascii=True)
PY
json_rc=$?
final=$rc
if [ "$json_rc" -ne 0 ]; then final=97; log "run.json generation failed rc=$json_rc"; fi
if [ "$COPY_OK" -ne 1 ] && [ "$final" -eq 0 ]; then final=96; log "copy failed with child rc=0"; fi
if { [ "$TIP_AFTER" != "$MEASUREMENT_TIP" ] || [ "$DIRTY_AFTER" -ne 0 ]; } && [ "$final" -eq 0 ]; then final=95; fi
echo "$final" > "$RUN/measure.done"
exit "$final"
```

## run-series.sh (sha256 `686a8bc79b8765cd5a8afe09d7d7323b9f19a5aab2ab069a0fd3c197e4ed393d`, 2593 byte)

```bash
#!/bin/bash
# usage: run-series.sh <spec...>; spec is "NN X slot".
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [ "$#" -eq 0 ]; then
  set -- "01 A 1" "02 B 1" "03 B 2" "04 A 2" "05 A 3" "06 B 3"
fi
for spec in "$@"; do
  if [[ ! "$spec" =~ ^[0-9]{2}\ [AB]\ [123]$ ]]; then
    echo 'usage: run-series.sh <"NN X slot"...>' >&2; exit 2
  fi
done
preflight() {
  python3 - "$J" "$SCRIPT_DIR" <<'PREFLIGHT'
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2802_ab_analyze import classification, warm_errors, analyze, frozen_sets
job = Path(sys.argv[1])
try:
    tips = json.loads((job / 'measurement-tips.json').read_bytes())
    errors = warm_errors(job, tips)
    if errors:
        raise ValueError('; '.join(errors))
except (OSError, ValueError, KeyError, TypeError) as exc:
    print('warm precondition: ' + str(exc), file=sys.stderr)
    sys.exit(94)
paths = [p for p in (job / 'runs').iterdir() if p.is_dir()] if (job / 'runs').exists() else []
for path in paths:
    try:
        red = int((path / 'measure.done').read_text()) != 0
        metadata = json.loads((path / 'run.json').read_bytes())
        red = red or metadata['rc'] != 0
    except (OSError, ValueError, KeyError, TypeError):
        red = True
    if red:
        try:
            classification(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f'{path.name}: {exc}', file=sys.stderr)
            sys.exit(93)
if len(paths) >= 12:
    sys.exit(92)
if paths:
    result = analyze(paths, frozen_sets(job / 'floor-subset-frozen.json'), tips, warm_root=job)
    if result['series_invalid']:
        print(result['series_invalid'], file=sys.stderr)
        sys.exit(93)
    if result['valid_pairs'] == 3:
        print('fixed stop: three valid pairs', file=sys.stderr)
        sys.exit(92)
PREFLIGHT
}
preflight || exit $?
echo $$ > "$J/series.pid" || exit 2
rm -f "$J/series.done"
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$J/series.log"; }
log 'series start'
for spec in "$@"; do
  preflight || { rc=$?; echo "$rc" > "$J/series.done"; exit "$rc"; }
  read -r nn cond slot <<< "$spec"
  log "launch $nn-$cond slot $slot"
  bash "$SCRIPT_DIR/run-measure.sh" "$nn" "$cond" "$slot"
  rc=$?
  log "$nn-$cond rc=$rc"
  if [ "$rc" -ne 0 ]; then
    echo "$rc" > "$J/series.done"
    log "series stopped rc=$rc; parent classification required"
    exit "$rc"
  fi
done
echo 0 > "$J/series.done"
log 'series end'
```

## run-warm.sh (sha256 `970f118cc6fe2d923817f246a30f2abcb36fd499abda475742d2d4fad5321c2a`, 3432 byte)

```bash
#!/bin/bash
# usage: run-warm.sh <A|B>
set -uo pipefail
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery
if [ "$#" -ne 1 ] || [[ ! "$1" =~ ^[AB]$ ]]; then
  echo 'usage: run-warm.sh <A|B>' >&2; exit 2
fi
COND=$1
# Keep all before/after evidence in one record even when the child fails.
python3 - "$J" "$COND" <<'PYWARM'
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import os

job, condition = Path(sys.argv[1]), sys.argv[2]
try:
    tip = json.loads((job / 'measurement-tips.json').read_bytes())[condition]
    worktree, sha = tip['worktree'], tip['sha']
    assert Path(worktree).is_absolute() and re.fullmatch('[0-9a-f]{40}', sha)
except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
    print('invalid measurement-tips.json: ' + str(exc), file=sys.stderr)
    sys.exit(2)
prefix = job / ('warm-' + condition)
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def tree():
    head = subprocess.check_output(['git', '-C', worktree, 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', worktree, 'status', '--porcelain',
                                     '--untracked-files=all', '--ignore-submodules=none'], text=True)
    clean = not any(not line.startswith('?? output/pegasus-dispatch/') for line in status.splitlines())
    return head, clean
def pycs():
    directory = Path(worktree) / 'orchestrator/tests/__pycache__'
    return sum(1 for p in directory.rglob('*.pyc')) if directory.exists() else 0
record = dict(condition=condition, worktree=worktree, sha=sha,
              head_before=None, head_after=None, clean_before=False, clean_after=False,
              pyc_before=pycs(), pyc_after=None, dispatch_request=None,
              PYTHONDONTWRITEBYTECODE='', started_at=now(), finished_at=None, rc=95)
Path(str(prefix) + '.pid').write_text(str(os.getpid()) + '\n')
Path(str(prefix) + '.done').unlink(missing_ok=True)
try:
    record['head_before'], record['clean_before'] = tree()
    if record['head_before'] == sha and record['clean_before']:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='')
        with Path(str(prefix) + '.log').open('w') as log:
            record['rc'] = subprocess.run(
                ['python3', 'tools/run_tests.py', '--force-dispatch', '--collect-only', '-q', '-p', 'no:cacheprovider'],
                cwd=worktree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        lines = Path(str(prefix) + '.log').read_text().splitlines()
        requests = [line for line in lines if '[Pegasus dispatch] request ID ' in line]
        record['dispatch_request'] = '\n'.join(requests) or None
    record['head_after'], record['clean_after'] = tree()
except (OSError, subprocess.SubprocessError) as exc:
    record['error'] = str(exc)
    record['rc'] = 95
record['pyc_after'] = pycs()
record['finished_at'] = now()
if (record['dispatch_request'] is None or record['head_after'] != sha
        or not record['clean_after']):
    record['rc'] = 95
Path(str(prefix) + '.json').write_text(json.dumps(record, indent=2) + '\n')
for suffix, value in [('started.txt', record['started_at']), ('finished.txt', record['finished_at']),
                      ('pyc-count.txt', record['pyc_after']), ('done', record['rc'])]:
    Path(str(prefix) + '.' + suffix).write_text(str(value) + '\n')
sys.exit(record['rc'])
PYWARM
exit $?
```

## t2802_ab_analyze.py (sha256 `d64b96137fbe73d3f72e5eb81b5024ad8e0dce709053d0a9bfa9f4f7ef95ad4a`, 30463 byte)

```python
#!/usr/bin/env python3
"""T-2802 preregistered floor worker-seconds analysis; no test launches."""
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import median
import sys
import xml.etree.ElementTree as ET

JOB = Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery')
OLD = JOB.parent / 'dev-wave-t2766-pairing-ab/runs'
FROZEN_SHA = '2bc360b9b1e524506cfa152ec53f2b720df726a6b1a6e9b2f245314e1df4e5d4'
FLOOR = 'orchestrator/tests/test_s8b_floor_campaign.py::'
CLASS = 'orchestrator.tests.test_s8b_floor_campaign'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def finite(value):
    value = float(value)
    require(math.isfinite(value) and value >= 0, 'nonfinite/negative time')
    return value


def frozen_sets(path):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == FROZEN_SHA, 'frozen sha256 mismatch')
    data = json.loads(raw)
    for key, count in [('S_all', 523), ('S_mid', 65), ('S_long', 22)]:
        require(len(data[key]) == len(set(data[key])) == count, key + ' size/duplicates')
        require(set(data[key]) <= set(data['S_all']), key + ' not subset')
    return data


def parse_junit(raw):
    require(b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw, 'unexpected XML declaration')
    root = ET.fromstring(raw)
    suites = [root] if root.tag == 'testsuite' else list(root)
    require(root.tag in ('testsuite', 'testsuites') and len(suites) == 1
            and suites[0].tag == 'testsuite', 'expected one pytest testsuite')
    suite = suites[0]
    counts = {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
    require(all(v >= 0 for v in counts.values()), 'negative suite count')
    cases = list(suite.iter('testcase'))
    require(counts['tests'] == len(cases), 'tests count mismatch')
    require(counts['failures'] == counts['errors'] == 0, 'red shard')
    require(not any(c.find('failure') is not None or c.find('error') is not None for c in cases), 'red testcase')
    times, skipped_nodes = {}, []
    for c in cases:
        if c.get('classname') != CLASS:
            continue
        node = FLOOR + c.attrib['name']
        require(node not in times, 'duplicate floor node: ' + node)
        if c.find('skipped') is not None:
            skipped_nodes.append(node)
        finite(c.attrib['time'])
        times[node] = Decimal(c.attrib['time'])
    return {'W': finite(suite.attrib['time']), 'skipped_floor': sorted(skipped_nodes), **counts}, times


def verify_hashes(session):
    required = {f'shard-{s}/{f}' for s in range(3) for f in ('junit.xml', 'report.json')}
    entries = {}
    for line in (session / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        require(name not in entries and not Path(name).is_absolute() and '..' not in Path(name).parts,
                'unsafe/duplicate hash path')
        require(re.fullmatch('[0-9a-f]{64}', digest), 'invalid hash')
        require(hashlib.sha256((session / name).read_bytes()).hexdigest() == digest, 'hash mismatch: ' + name)
        entries[name] = digest
    require(required <= entries.keys(), 'missing shard hashes')


def parse_session(session, frozen):
    verify_hashes(session)
    shards, times = [], {}
    for s in range(3):
        shard = session / f'shard-{s}'
        summary, nodes = parse_junit((shard / 'junit.xml').read_bytes())
        report = json.loads((shard / 'report.json').read_bytes())
        require(report['shard_index'] == s and report['shard_count'] == 3, 'report shard mismatch')
        require(report['pytest_rc'] == 0, 'report red')
        # S_all intentionally uses exact module classname, excluding class methods.
        selected = Counter(n for n in report['selected']
                           if n.startswith(FLOOR) and '::' not in n[len(FLOOR):].split('[', 1)[0])
        require(selected == Counter(nodes.keys()), 'selected/JUnit floor mismatch')
        require(not (times.keys() & nodes.keys()), 'cross-shard duplicate floor node')
        times.update(nodes)
        occupancy = report.get('worker_occupancy')
        summary['worker_occupancy'] = occupancy
        summary['busiest_worker'] = None
        if occupancy:
            for v in occupancy.values():
                finite(v['duration_s'])
                require(type(v['items']) is int and v['items'] >= 0, 'invalid occupancy items')
            name = max(occupancy, key=lambda n: occupancy[n]['duration_s'])
            summary['busiest_worker'] = {'worker': name, **occupancy[name]}
        shards.append(summary)
    require(set(times) == set(frozen['S_all']), 'floor nodeid set mismatch')
    return {'shards': shards, 'node_times': times,
            'skipped_floor': sorted(n for shard in shards for n in shard['skipped_floor']),
            'F': sum((times[n] for n in frozen['S_all']), Decimal(0)),
            'F_mid': sum((times[n] for n in frozen['S_mid']), Decimal(0)),
            'F_long': sum((times[n] for n in frozen['S_long']), Decimal(0)),
            'W_max': max(s['W'] for s in shards), 'W_0': shards[0]['W']}


def timestamp(value):
    t = datetime.fromisoformat(re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', value))
    require(t.tzinfo is not None, 'timezone missing')
    return t


def read_run(path, frozen, tips, selftest=False):
    run = {'tag': path.name, 'valid': False, 'errors': [], 'skipped_floor': []}
    try:
        m = json.loads((path / 'run.json').read_bytes())
        run['metadata'] = m
        require(path.name == f"{m['run']}-{m['condition']}", 'run tag mismatch')
        require(m['condition'] in ('A', 'B') and type(m['pair_slot']) is int and m['pair_slot'] in (1, 2, 3), 'condition/slot')
        require(type(m['rc']) is int and m['rc'] == 0 and m['copy_ok'] is True, 'rc/copy_ok')
        require(type(m['dirty_lines_before']) is int and type(m['dirty_lines_after']) is int
                and m['dirty_lines_before'] == m['dirty_lines_after'] == 0, 'dirty tree')
        require(timestamp(m['submitted_at']) < timestamp(m['finished_at']), 'invalid run interval')
        if not selftest:
            require(int((path / 'measure.done').read_text()) == 0, 'launcher final rc')
            tip = tips[m['condition']]
            require(m['expected_sha'] == m['tip_sha'] == m['tip_sha_after'] == tip['sha'], 'tip mismatch')
            require(m['condition_worktree'] == tip['worktree'], 'worktree mismatch')
            require(m['valid_tree'] is True, 'valid_tree false')
            require(re.fullmatch('[0-9a-f]{64}', m['tracked_diff_stat_sha256']), 'diff hash missing/invalid')
            require(hashlib.sha256((path / 'tracked-diff.stat').read_bytes()).hexdigest()
                    == m['tracked_diff_stat_sha256'], 'tracked diff file hash mismatch')
            require(m['env']['IZANAGI_ACCEPTANCE_SHARDS'] == '3'
                    and m['env']['PYTHONDONTWRITEBYTECODE_SET'] == 'no'
                    and 'PYTHONDONTWRITEBYTECODE' not in m['env'], 'environment mismatch')
            env = dict(line.split('=', 1) for line in (path / 'env.txt').read_text().splitlines())
            require(env == m['env'], 'env.txt mismatch')
            require(type(m['other_leaders']) is int and 0 <= m['other_leaders'] <= 1
                    and finite(m['load1']) < 30, 'gate metadata')
        else:
            run['checks_skipped'] = 'selftest では検算省略: condition_worktree, expected_sha, valid_tree, tracked_diff_stat_sha256, environment equality (T-2766 schema)'
        run.update(parse_session(path / 'session', frozen))
        run['valid'] = True
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        run['errors'].append(str(exc))
    return run


def invalidate(run, reason):
    run['valid'] = False
    run['errors'].append(reason)


def pair_metrics(a, b):
    delta = {n: a['node_times'][n] - b['node_times'][n] for n in a['node_times']}
    large = [v for v in delta.values() if v >= 3]
    return {'delta_F': a['F'] - b['F'], 'r': (a['F'] - b['F']) / a['F'] if a['F'] else None,
            'delta_F_mid': a['F_mid'] - b['F_mid'], 'delta_F_long': a['F_long'] - b['F_long'],
            'delta_W_max': a['W_max'] - b['W_max'], 'delta_W_0': a['W_0'] - b['W_0'],
            'node_deltas': delta, 'node_delta_median': median(delta.values()),
            'nodes_ge_3': len(large), 'sum_ge_3': sum(large, Decimal(0)),
            'top10': [{'nodeid': n, 'delta': v} for n, v in sorted(delta.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]}


def decision(deltas, total_runs):
    """Frozen rule: exactly three valid pairs; 200 worker seconds; 12-run cap."""
    if len(deltas) < 3:
        return 'insufficient-valid-pairs'
    if len(deltas) != 3 or total_runs > 12 or not all(d > 0 for d in deltas):
        return 'effect-not-established'
    return ('direction-consistent-above-threshold' if median(deltas) >= 200
            else 'direction-consistent-below-threshold')


def classification(path):
    try:
        c = json.loads((path / 'classification.json').read_bytes())
    except FileNotFoundError:
        raise ValueError('missing classification')
    require(c['kind'] in ('infra', 'impl', 'unclassified'), 'invalid classification kind')
    require(all(isinstance(c[k], str) and c[k].strip() for k in ('by', 'evidence', 'at')),
            'invalid classification evidence')
    timestamp(c['at'])
    require(c['kind'] == 'infra', 'classification: ' + c['kind'])
    return c


def warm_errors(root, tips):
    errors = []
    for condition in ('A', 'B'):
        try:
            w = json.loads((root / f'warm-{condition}.json').read_bytes())
            tip = tips[condition]
            require(w['condition'] == condition and w['worktree'] == tip['worktree']
                    and w['sha'] == w['head_before'] == w['head_after'] == tip['sha'],
                    'warm tip mismatch')
            require(type(w['rc']) is int and w['rc'] == 0
                    and w['clean_before'] is True and w['clean_after'] is True,
                    'warm failed or dirty')
            require(isinstance(w['dispatch_request'], str)
                    and '[Pegasus dispatch] request ID ' in w['dispatch_request'],
                    'warm missing dispatch')
            require(w['PYTHONDONTWRITEBYTECODE'] == '', 'warm bytecode environment')
            require(all(type(w[k]) is int and w[k] >= 0 for k in ('pyc_before', 'pyc_after')),
                    'warm pyc counts')
            require(timestamp(w['started_at']) <= timestamp(w['finished_at']), 'warm interval')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'warm-{condition}: {exc}')
    return errors


def analyze(paths, frozen, tips, selftest=False, warm_root=None):
    paths = sorted(paths, key=lambda p: int(p.name.split("-")[0]))
    series_errors = warm_errors(warm_root or JOB, tips)
    runs = [read_run(p, frozen, tips, selftest) for p in paths]
    # Check all intervals, not only successful runs; never skip a bad observation.
    prior = None
    seen_numbers = set()
    for r in runs:
        m = r.get('metadata', {})
        try:
            number = int(r['tag'].split('-')[0])
            require(number not in seen_numbers, 'duplicate run number')
            seen_numbers.add(number)
            start, end = timestamp(m['submitted_at']), timestamp(m['finished_at'])
            if prior and start <= prior[0]:
                invalidate(r, 'nonsequential submission')
                invalidate(prior[1], 'overlapping/following submission')
            if prior is None or end > prior[0]:
                prior = (end, r)
        except (ValueError, KeyError, TypeError) as exc:
            invalidate(r, 'interval: ' + str(exc))
    if not selftest:
        hashes = {r.get('metadata', {}).get('tracked_diff_stat_sha256') for r in runs}
        envs = {json.dumps(r.get('metadata', {}).get('env'), sort_keys=True) for r in runs}
        if len(hashes) > 1 or len(envs) > 1:
            for r in runs:
                invalidate(r, 'series diff hash/environment mismatch')
    # Never regroup by slot or reuse a half: consume adjacent observations once.
    pairs, slot, cursor = [], 1, 0
    attempts = Counter()
    while cursor < len(runs):
        if slot == 4:
            series_errors.append('runs after fixed stop')
            break
        expected = ('B', 'A') if slot == 2 else ('A', 'B')
        group = [runs[cursor]]
        cursor += 1
        # A stopped red first half may restart the whole pair. A healthy
        # abandoned half is a grammar violation, not a retry opportunity.
        next_is_restart = (cursor < len(runs) and
            runs[cursor].get('metadata', {}).get('pair_slot') == slot and
            runs[cursor].get('metadata', {}).get('condition') == expected[0])
        if cursor < len(runs) and not next_is_restart:
            group.append(runs[cursor])
            cursor += 1
        grammar_errors = []
        for index, r in enumerate(group):
            m = r.get('metadata', {})
            if m.get('pair_slot') != slot or m.get('condition') != expected[index]:
                grammar_errors.append(
                    f"series grammar: {r['tag']} expected slot {slot} condition {expected[index]}")
        if len(group) == 1 and next_is_restart and group[0]['valid']:
            grammar_errors.append(
                f"series grammar: {group[0]['tag']} healthy first half abandoned before retry")
        # A matching trailing first half is an in-progress pair. A red
        # singleton retry still requires infra classification below.
        series_errors.extend(grammar_errors)
        attempts[slot] += 1
        order_ok = (len(group) == 2 and
                    all(r.get('metadata', {}).get('pair_slot') == slot for r in group) and
                    tuple(r.get('metadata', {}).get('condition') for r in group) == expected)
        skipped_match = (len(group) == 2 and
                         set(group[0]['skipped_floor']) == set(group[1]['skipped_floor']))
        valid = order_ok and all(r['valid'] for r in group) and skipped_match
        p = {'pair_slot': slot, 'attempt': attempts[slot], 'runs': [r['tag'] for r in group],
             'valid': valid, 'skipped_match': skipped_match}
        if valid:
            a, b = sorted(group, key=lambda r: r['metadata']['condition'])
            p.update(pair_metrics(a, b))
            slot += 1
        elif not order_ok:
            p['reason'] = 'incomplete/nonadjacent pair, wrong slot/order, or half reuse'
        elif not all(r['valid'] for r in group):
            p['reason'] = 'invalid run in adjacent pair'
        else:
            p['reason'] = 'skipped set differs within pair'
        pairs.append(p)
        if grammar_errors:
            break
    for path, run in zip(paths, runs):
        if not run['valid'] or (path / 'classification.json').exists():
            try:
                run['classification'] = classification(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                series_errors.append(str(exc))
    if len(runs) > 12:
        series_errors.append('total runs exceeds 12')
    valid = [p for p in pairs if p['valid']]
    deltas = [p['delta_F'] for p in valid]
    return {'runs': runs, 'pairs': pairs, 'total_runs': len(runs), 'over_12_runs': len(runs) > 12,
            'valid_pairs': len(valid), 'delta_F_median': median(deltas) if deltas else None,
            'series_invalid': list(dict.fromkeys(series_errors)),
            'decision': 'series-invalid' if series_errors else decision(deltas, len(runs)), 'frozen_sha256': FROZEN_SHA}


def markdown(result):
    lines = ['## Run table', '', '|run|valid|F|F_mid|W_max|W_0|busiest worker by shard|',
             '|---|---|---|---|---|---|---|']
    fmt = lambda value: f'{value:.3f}' if isinstance(value, (float, int, Decimal)) else '—'
    for r in result['runs']:
        occupancy = json.dumps([s.get('busiest_worker') for s in r.get('shards', [])], ensure_ascii=False)
        lines.append('|' + '|'.join([r['tag'], str(r['valid'])] +
                     [fmt(r.get(k)) for k in ('F', 'F_mid', 'W_max', 'W_0')] + [occupancy]) + '|')
        if r['errors']:
            lines.append('\n' + r['tag'] + ': ' + '; '.join(r['errors']) + '\n')
    lines += ['', '## Pair table', '', '|slot/attempt|runs|valid|ΔF|ΔF_mid|ΔW_max|ΔW_0|median Δ_n|n ≥ 3|sum ≥ 3|',
              '|---|---|---|---|---|---|---|---|---|---|']
    for p in result['pairs']:
        lines.append('|' + '|'.join([f"{p['pair_slot']}/{p['attempt']}", ', '.join(p['runs']), str(p['valid'])] +
                     [fmt(p.get(k)) for k in ('delta_F', 'delta_F_mid', 'delta_W_max', 'delta_W_0',
                                              'node_delta_median', 'nodes_ge_3', 'sum_ge_3')]) + '|')
        if 'reason' in p:
            lines.append('\n' + p['reason'] + '\n')
    lines += ['', *('series_invalid: ' + e for e in result['series_invalid']), '']
    lines += ['## Decision', '', result['decision'], '',
              f"valid_pairs={result['valid_pairs']}; total_runs={result['total_runs']}; over_12_runs={result['over_12_runs']}; median ΔF={fmt(result['delta_F_median'])}", '',
              'JSON retains calculation precision; tables display three decimal places. Floor excludes added admission tests; shared scheduling and fixture effects remain.']
    return '\n'.join(lines) + '\n'


def selftest():
    from unittest.mock import patch
    import copy
    warm_root = Path('/synthetic-warm')
    tips = {c: {'sha': c.lower() * 40, 'worktree': '/synthetic-' + c} for c in ('A', 'B')}
    warms = {warm_root / f'warm-{c}.json': json.dumps(dict(
        condition=c, worktree=t['worktree'], sha=t['sha'], head_before=t['sha'], head_after=t['sha'],
        clean_before=True, clean_after=True, rc=0, dispatch_request='[Pegasus dispatch] request ID fixture node fixture',
        PYTHONDONTWRITEBYTECODE='', pyc_before=0, pyc_after=3,
        started_at='2026-09-19T00:00:00+00:00', finished_at='2026-09-19T00:01:00+00:00')).encode()
        for c, t in tips.items()}
    def analyze(paths, frozen, _tips, selftest=True):
        reader = Path.read_bytes
        with patch.object(Path, 'read_bytes', lambda p: warms[p] if p in warms else reader(p)):
            return globals()['analyze'](paths, frozen, tips, selftest, warm_root)
    frozen = frozen_sets(JOB / 'floor-subset-frozen.json')
    result = analyze([OLD / s for s in ('03-A', '04-B', '05-B', '06-A', '07-A', '08-B')], frozen, {}, True)
    require(all(r['valid'] for r in result['runs']), str([(r['tag'], r['errors']) for r in result['runs']]))
    require(result['valid_pairs'] == 3, 'historical pairing')
    print(result['runs'][0]['checks_skipped'])
    for r in result['runs']:
        skipped = r['skipped_floor']
        require(len(skipped) == 3 and skipped == result['runs'][0]['skipped_floor'],
                'unexpected historical skipped set')
        print(r['tag'] + ': skipped_floor: ' + json.dumps(skipped))
    require(all(p['skipped_match'] for p in result['pairs']), 'historical skipped pairing')
    # Tiny XML still exercises the same testcase parser before applying the rule.
    def metric(t):
        raw = f'<testsuite time="1" tests="1" failures="0" errors="0" skipped="0"><testcase classname="{CLASS}" name="synthetic[x]" time="{t}"/></testsuite>'
        _, nodes = parse_junit(raw.encode())
        return sum(nodes.values(), Decimal(0))
    for ds, expected in [([200, 210, 220], 'direction-consistent-above-threshold'),
                         ([1, 2, 3], 'direction-consistent-below-threshold'),
                         ([210, -1, 220], 'effect-not-established')]:
        require(decision([metric(500) - metric(500 - d) for d in ds], 6) == expected, expected)
    require(decision([300, 300], 4) == 'insufficient-valid-pairs', 'insufficient branch')
    require(decision([300] * 3, 13) == 'effect-not-established', 'cap branch')
    # Exercise the actual parser, hash checks and pair assembly without writing files.
    from unittest.mock import patch

    paths = [Path('/synthetic/01-A'), Path('/synthetic/02-B')]
    payloads = {}

    def synthetic_run(path, skipped, index):
        metadata = {'run': path.name[:2], 'condition': path.name[-1], 'pair_slot': 1,
                    'rc': 0, 'copy_ok': True, 'dirty_lines_before': 0, 'dirty_lines_after': 0,
                    'submitted_at': f'2026-09-20T0{index}:00:00+09:00',
                    'finished_at': f'2026-09-20T0{index}:01:00+09:00'}
        payloads[path / 'run.json'] = json.dumps(metadata).encode()
        hashes = []
        for shard in range(3):
            selected = frozen['S_all'][shard::3]
            suite = ET.Element('testsuite', time='1', tests=str(len(selected)),
                               failures='0', errors='0', skipped=str(len(set(selected) & skipped)))
            for node in selected:
                case = ET.SubElement(suite, 'testcase', classname=CLASS,
                                     name=node[len(FLOOR):], time='0.125' if node in skipped else '1')
                if node in skipped:
                    ET.SubElement(case, 'skipped')
            report = {'shard_index': shard, 'shard_count': 3, 'pytest_rc': 0, 'selected': selected}
            for name, raw in [('junit.xml', ET.tostring(suite)),
                              ('report.json', json.dumps(report).encode())]:
                relative = f'shard-{shard}/{name}'
                payloads[path / 'session' / relative] = raw
                hashes.append(hashlib.sha256(raw).hexdigest() + '  ' + relative)
        payloads[path / 'session/SHA256SUMS'] = ('\n'.join(hashes) + '\n').encode()

    skipped = set(frozen['S_all'][:3])
    synthetic_run(paths[0], skipped, 1)
    synthetic_run(paths[1], skipped, 2)
    with patch.object(Path, 'read_bytes', lambda p: payloads[p] if p in payloads else (_ for _ in ()).throw(FileNotFoundError(str(p)))), \
            patch.object(Path, 'read_text', lambda p: payloads[p].decode() if p in payloads else (_ for _ in ()).throw(FileNotFoundError(str(p)))):
        positive = analyze(paths, frozen, {}, True)
        require(positive['valid_pairs'] == 1 and positive['pairs'][0]['skipped_match'],
                'same three skipped nodes must yield a valid pair')
        require(all(r['valid'] and r['skipped_floor'] == sorted(skipped)
                    and r['F'] == Decimal('520.375') for r in positive['runs']),
                'skipped nodes must retain recorded time in F')
        require(positive['pairs'][0]['delta_F'] == 0, 'same skipped times must cancel')
        synthetic_run(paths[1], set(frozen['S_all'][1:4]), 2)
        negative = analyze(paths, frozen, {}, True)
        require(all(r['valid'] for r in negative['runs']) and negative['valid_pairs'] == 0
                and not negative['pairs'][0]['skipped_match']
                and negative['pairs'][0]['reason'] == 'skipped set differs within pair'
                and 'delta_F' not in negative['pairs'][0], 'different skipped sets must invalidate pair')
        synthetic_run(paths[1], skipped, 2)
        payloads[paths[1] / 'session/shard-0/junit.xml'] += b' '
        tampered = analyze(paths, frozen, {}, True)
        require(not tampered['runs'][1]['valid'] and tampered['valid_pairs'] == 0
                and any('hash mismatch' in e for e in tampered['runs'][1]['errors']),
                'hash tampering must invalidate run and pair')
    # Whole-series state machine, including restart after a stopped first half.
    template = copy.deepcopy(result['runs'][0])
    def series(specs, red=(), classified=False):
        rs, ps, records = [], [], {}
        for i, (condition, slot) in enumerate(specs, 1):
            r = copy.deepcopy(template)
            r.update(tag=f'{i:02d}-{condition}', valid=i not in red, errors=[])
            r['metadata'].update(condition=condition, pair_slot=slot,
                submitted_at=f'2026-09-20T00:{i*2:02d}:00+00:00',
                finished_at=f'2026-09-20T00:{i*2+1:02d}:00+00:00')
            rs.append(r)
            path = Path('/synthetic') / r['tag']
            ps.append(path)
            if i in red and classified:
                records[path / 'classification.json'] = json.dumps(dict(
                    kind=classified if isinstance(classified, str) else 'infra', by='parent',
                    evidence='review.md', at='2026-09-20T01:00:00+00:00')).encode()
        def read(p):
            if p in records:
                return records[p]
            raise FileNotFoundError(str(p))
        with patch.dict(globals(), read_run=lambda p, *args: rs[ps.index(p)]), \
                patch.object(Path, 'read_bytes', read):
            return analyze(ps, frozen, {}, True)
    normal = [('A', 1), ('B', 1), ('B', 2), ('A', 2), ('A', 3), ('B', 3)]
    require(series([('A',1), ('B',2), ('B',1), ('A',2), ('A',3), ('B',3)])['valid_pairs'] == 0,
            'nonadjacent regrouping must never produce a pair')
    for count in range(7):
        prefix = series(normal[:count])
        require(not prefix['series_invalid'] and prefix['valid_pairs'] == count // 2
                and (count == 6 or prefix['decision'] == 'insufficient-valid-pairs'),
                'normal series prefix including in-progress first half')
    counterexample = series([('A', 1), ('B', 2)] + normal)
    require(counterexample['decision'] == 'series-invalid'
            and any(e.startswith('series grammar: 02-B ') for e in counterexample['series_invalid']),
            'slot violation before three valid pairs must invalidate series')
    for specs in [normal[:2] + normal, [('B', 1), ('A', 1)] + normal,
                  normal[:2] + [('A', 2), ('B', 2)] + normal[2:],
                  normal[:2] + [('A', 1)], normal[:2] + [('A', 2)],
                  normal[:1] + normal]:
        bad = series(specs)
        require(bad['decision'] == 'series-invalid'
                and any(e.startswith('series grammar: ') for e in bad['series_invalid']),
                'slot rollback, wrong order, or abandoned healthy half')
    missing = series(normal[:2] + normal, red=(2,))
    require(missing['decision'] == 'series-invalid' and 'missing classification' in missing['series_invalid'],
            'unclassified red series')
    require(series(normal[:2] + normal, red=(2,), classified=True)['valid_pairs'] == 3
            and series(normal[:2] + normal, red=(2,), classified=True)['decision'] != 'series-invalid',
            'infra red whole-pair retry')
    for kind in ('impl', 'unclassified'):
        require(series(normal[:2] + normal, red=(2,), classified=kind)['decision'] == 'series-invalid', kind)
    for specs in (normal[:2] + normal, normal[:1] + normal):
        retry = series(specs, red=(1,), classified=True)
        require(retry['valid_pairs'] == 3 and not retry['series_invalid']
                and retry['decision'] != 'insufficient-valid-pairs',
                'infra red first run permits whole-pair or stopped-first-half retry')
        for kind in (False, 'impl', 'unclassified'):
            require(series(specs, red=(1,), classified=kind)['decision'] == 'series-invalid',
                    'first-run retry requires infra classification')
    require('runs after fixed stop' in series(normal + [('A',3)])['series_invalid'], 'fixed stop')
    require(series(normal + normal + [('A',3)])['decision'] == 'series-invalid', 'series cap')
    with patch.object(Path, 'read_bytes', lambda p: warms[p]):
        require(not warm_errors(warm_root, tips), 'synthetic warm evidence')
        bad_tips = copy.deepcopy(tips)
        bad_tips['A']['sha'] = '0' * 40
        require(warm_errors(warm_root, bad_tips), 'warm SHA mismatch')
    warm_a = warm_root / 'warm-A.json'
    original_warm = warms[warm_a]
    del warms[warm_a]
    require(series(normal)['decision'] == 'series-invalid', 'missing warm invalidates series')
    warms[warm_a] = original_warm
    for key, value in [('sha', '0' * 40), ('dispatch_request', None), ('rc', 95), ('clean_after', False)]:
        bad = json.loads(original_warm)
        bad[key] = value
        warms[warm_a] = json.dumps(bad).encode()
        require(series(normal)['decision'] == 'series-invalid', 'invalid warm: ' + key)
    warms[warm_a] = original_warm
    md = markdown(result)
    require('F_long' not in md and 'ΔF_long' not in md and '|r|' not in md
            and '## Node deltas' not in md and 'busiest worker' in md,
            'markdown must retain only preregistered metrics')
    print('PASS: series grammar/counterexample; infra whole-pair/first-half retry; in-progress prefixes')
    print('PASS: chronological adjacency/retry; classification; fixed stop; cap; warm evidence')
    print('PASS: 6 historical runs; exact 523 floor nodes/run; 18 shard W; '
          '3 decision branches + insufficient/cap; skipped match/mismatch; hash tampering')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selftest', action='store_true')
    for name in ('runs-root', 'frozen', 'tips', 'out'):
        p.add_argument('--' + name, type=Path)
    args = p.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not all((args.runs_root, args.frozen, args.tips, args.out)):
        p.error('--runs-root, --frozen, --tips, --out are required')
    tips = json.loads(args.tips.read_bytes())
    for c in ('A', 'B'):
        require(re.fullmatch('[0-9a-f]{40}', tips[c]['sha']) and Path(tips[c]['worktree']).is_absolute(), 'invalid tips')
    paths = sorted((d for d in args.runs_root.iterdir() if d.is_dir() ), key=lambda d: int(d.name.split('-')[0]))
    result = analyze(paths, frozen_sets(args.frozen), tips, warm_root=args.tips.parent)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'analysis.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False, default=float) + '\n')
    (args.out / 'analysis.md').write_text(markdown(result))
    print(result['decision'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(2)
```

## t2802_diff_probe.py (sha256 `57a4b34667f93b0467f5658eda276afb38ebe92e2f1cd4ad2a5b4d4edf3fc945`, 23472 byte)

```python
#!/usr/bin/env python3
"""Compare the pinned base candidate and wave candidate on stable fixture roots."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

# Prevent import caches outside our owned directory, including imported tests.
sys.dont_write_bytecode = True
BASE_SHA = 'de03d2536bbe69df9138273c8911d75cebbec8b5d72e3435715903102b88c48c'
NAME = 'orchestrator.campaign._t2802_base_admission'
CANDIDATE = '_floor_attempt_recovery_candidate_locked'
IMPORT_NOTES = (
    'Test module imports campaign/calibrator/evidence modules and evaluates pytest '
    'parametrize decorators; its guarded pytest.main is not invoked. Admission import '
    'checks scheduler authority, creates separate state registries and RLock; no '
    'admission-root write occurs at module top level. Fixture helpers create and commit '
    'a disposable git repository only below this script directory. Dependencies are '
    'shared from repo-root, so their equivalence to base remains a parent integration precondition.'
)


IMPORT_AUDIT = {'active': False, 'writes': [], 'processes': []}


def import_audit(event, args):
    if not IMPORT_AUDIT['active']:
        return
    if event == 'open':
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                isinstance(flags, int) and flags & (1 | 2 | 64 | 512 | 1024)):
            IMPORT_AUDIT['writes'].append(str(args[0]))
    elif event in ('subprocess.Popen', 'os.system', 'os.posix_spawn'):
        IMPORT_AUDIT['processes'].append(event)


def load_modules(repo, base_path):
    if hashlib.sha256(base_path.read_bytes()).hexdigest() != BASE_SHA:
        raise ValueError('base module SHA256 mismatch')
    sys.addaudithook(import_audit)
    IMPORT_AUDIT['active'] = True
    sys.path.insert(0, str(repo))
    current = importlib.import_module('orchestrator.campaign.s8b_holdout_admission')
    if Path(current.__file__).resolve() != repo / 'orchestrator/campaign/s8b_holdout_admission.py':
        raise ValueError('current module imported from wrong repo')
    spec = importlib.util.spec_from_file_location(NAME, base_path)
    base = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = base  # Required before dataclass evaluation in exec_module.
    spec.loader.exec_module(base)
    helpers = importlib.import_module('orchestrator.tests.test_s8b_holdout_admission')
    IMPORT_AUDIT['active'] = False
    return current, base, helpers


def exception_map(module):
    # Only corresponding module-owned exception types lose the module prefix.
    # Shared dependency and builtin exceptions retain their full identity.
    return {v: k for k, v in vars(module).items()
            if isinstance(v, type) and issubclass(v, Exception) and v.__module__ == module.__name__}


def outcome(module, shared, expected, completed):
    try:
        value = getattr(module, CANDIDATE)(shared, expected_marker=expected, completed_attempt=completed)
        return {'kind': 'return', 'value': value}
    except Exception as exc:
        name = exception_map(module).get(type(exc), f'{type(exc).__module__}.{type(exc).__qualname__}')
        return {'kind': 'exception', 'type': name, 'message': str(exc)}


def snapshot(root):
    # Exclude only the advisory lock contents; do not follow unsafe symlinks.
    result = {}
    for p in sorted(root.rglob('*')):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            result[rel] = ('symlink', str(p.readlink()))
        elif p.is_file() and p.name != 'ledger.lock':
            result[rel] = ('file', hashlib.sha256(p.read_bytes()).hexdigest())
        elif p.is_dir():
            result[rel] = ('directory',)
    return result


def compare(current, base, shared, expected, completed, label):
    orders = []
    with current._locked(shared):
        before = snapshot(shared)
        for sequence in (('current', 'base'), ('base', 'current')):
            values = {}
            unchanged = True
            for side in sequence:
                values[side] = outcome(current if side == 'current' else base, shared, expected, completed)
                unchanged = unchanged and snapshot(shared) == before
            orders.append({'order': list(sequence), **values,
                           'root_unchanged': unchanged,
                           'match': values['current'] == values['base'] and unchanged})
    return {'state': label, 'expected_marker': expected, 'completed_attempt': completed,
            'orders': orders, 'match': all(o['match'] for o in orders)}


@contextmanager
def changed_files(*paths):
    old = {p: p.read_bytes() if p.exists() else None for p in paths}
    try:
        yield
    finally:
        for p, raw in old.items():
            if p.is_symlink() or p.exists():
                p.unlink()
            if raw is not None:
                p.write_bytes(raw)


def exercise(current, base, h, parent, selftest):
    import pytest
    results = []
    positive = None
    with tempfile.TemporaryDirectory(prefix='.diff-fixture-', dir=parent) as tmp:
        root, protocol, cell, admitted, first_id, _ = h._issued_cell(Path(tmp))
        shared = current.shared_admission_root(root)
        state = current._cell_state(admitted)
        ledger = shared / 'attempt-ledger.jsonl'
        consumed = shared / 'measurement-generation-consumed'
        first = h._floor_expected_marker(admitted, first_id)
        def check(label, marker=first, completed=False):
            r = compare(current, base, shared, marker, completed, label)
            results.append(r)
            return r
        def write_rows(path, rows):
            path.write_bytes(b''.join(h._canonical(row) + b'\n' for row in rows))
        check('a-marker-absent')
        with pytest.MonkeyPatch.context() as mp:
            h._crash_floor_after_marker(mp, admitted, first_id)
        check('b-single-claim-M+A-')
        current.consume_attempt_ticket(admitted, attempt_id=first_id)
        check('c-single-claim-M+A+')
        markers = [first]
        schedule = [r for r in state.schedule if r['cell_id'] == cell['cell_id']][:3]
        for row in schedule:
            aid = f"{cell['cell_id']}::seq{row['seq']}"
            if aid == first_id:
                continue
            h._append_journal_rows(admitted, {
                'event': 'session-start', 'seq': row['seq'], 'round': row['round'],
                'kind': 'planned', 'cell_id': cell['cell_id'], 'attempt_id': aid, 'trigger': None,
            })
            with pytest.MonkeyPatch.context() as mp:
                h._crash_floor_after_marker(mp, admitted, aid)
            marker = h._floor_expected_marker(admitted, aid)
            check(f'd-sequence-{len(markers)+1}-M+A-', marker)
            current.consume_attempt_ticket(admitted, attempt_id=aid)
            markers.append(marker)
            check(f'd-sequence-{len(markers)}-M+A+', marker)
        if len(markers) != 3:
            raise ValueError('fixture lacks three planned attempts')
        all_rows = current._read_ledger(ledger)
        for i, target in enumerate(markers):
            with changed_files(ledger):
                write_rows(ledger, [r for r in all_rows if r['attempt_id'] != target['attempt_id']])
                check(f'd-three-consumed-target-{i}-M+A-', target)
        ordered = sorted(markers, key=lambda m: current._floor_canonical_marker_path(shared, m).name)
        target, later = ordered[0], ordered[-1]
        later_path = current._floor_canonical_marker_path(shared, later)
        # Later marker has no A row: equality regression is isolated to marker validation.
        for tamper in ('campaign_run_id', 'extra-key', 'rename', 'unregistered-attempt'):
            mutated = dict(later)
            destination = later_path
            if tamper == 'campaign_run_id':
                mutated['campaign_run_id'] = 'different-run'
            elif tamper == 'extra-key':
                mutated['extra'] = 'forbidden'
            elif tamper == 'rename':
                destination = consumed / ('zz-renamed-' + later_path.name)
            else:
                # Keep the altered marker after the target in filename order.
                for i in range(10000):
                    mutated['attempt_id'] = f"{later['cell_id']}::unregistered-{i}"
                    destination = current._floor_canonical_marker_path(shared, mutated)
                    if destination.name > current._floor_canonical_marker_path(shared, target).name:
                        break
                else:
                    raise ValueError('could not construct later unregistered marker')
            paths = tuple(dict.fromkeys((ledger, later_path, destination)))
            with changed_files(*paths):
                write_rows(ledger, [r for r in all_rows if r['attempt_id'] not in (target['attempt_id'], later['attempt_id'])])
                later_path.unlink()
                destination.write_bytes(h._canonical(mutated) + b'\n')
                check('e-later-nontarget-marker-' + tamper, target)
                if selftest and tamper == 'campaign_run_id':
                    # Intentional loose candidate: skips non-target verification.
                    def loose(_root, *, expected_marker, completed_attempt):
                        return dict(expected_marker)
                    with pytest.MonkeyPatch.context() as mp:
                        mp.setattr(current, CANDIDATE, loose)
                        positive = compare(current, base, shared, target, False, 'positive-loose-current-stub')
                        positive['rc'] = 0 if positive['match'] else 1
        for tamper in ('campaign_run_id', 'canonical-duplicate', 'missing-marker'):
            with changed_files(ledger, later_path):
                rows = [dict(r) for r in all_rows]
                # Make sure the changed row is second or later in ledger order.
                victim = rows[-1]
                victim_path = current._floor_canonical_marker_path(shared, victim)
                with changed_files(victim_path):
                    if tamper == 'campaign_run_id':
                        victim['campaign_run_id'] = 'different-run'
                    elif tamper == 'canonical-duplicate':
                        rows.append(dict(victim))
                    else:
                        victim_path.unlink()
                    write_rows(ledger, rows)
                    check('f-later-A-' + tamper, target)
        journal = state.run_dir / 'journal.jsonl'
        with changed_files(ledger, journal):
            write_rows(ledger, [r for r in all_rows if r['attempt_id'] != first_id])
            row = schedule[0]
            h._append_journal_rows(admitted, {
                'event': 'session', 'seq': row['seq'], 'round': row['round'],
                'kind': 'planned', 'cell_id': cell['cell_id'], 'attempt_id': first_id, 'valid': True,
            })
            completed = any(r.get('event') == 'session' and r.get('attempt_id') == first_id
                            for r in current._read_run_journal(journal))
            check('g-completed-journal-session', first, completed)
        main = shared / 'ledger.jsonl'
        with changed_files(main):
            rows = current._read_ledger(main)
            matching = next(r for r in rows if r.get('measurement_generation_claim_digest') == first['measurement_generation_claim_digest'])
            matching['records'] += 1
            write_rows(main, rows)
            check('h-main-ledger-records')
        claim = current._measurement_generation_claim_path(shared, first['measurement_generation_claim_digest'])
        with changed_files(claim):
            claim.write_text(json.dumps(json.loads(claim.read_bytes()), sort_keys=True) + '\n')
            check('i-noncanonical-claim-bytes')
        unsafe = consumed / 'zz-unsafe.json'
        with changed_files(unsafe):
            unsafe.symlink_to(later_path)
            check('j-consumed-symlink')
        # Extra: a different generation on the same physical root, with distinct claim.
        _, freeze = h._fixture_documents()
        reservation = h._reserve(root, protocol, freeze, run_id='run-b')
        other = current.finalize_floor_holdout_admissions(reservation)[cell['cell_id']]
        row = schedule[0]
        h._append_journal_rows(other, {
            'event': 'session-start', 'seq': row['seq'], 'round': row['round'],
            'kind': 'planned', 'cell_id': cell['cell_id'], 'attempt_id': first_id, 'trigger': None,
        })
        other_marker = h._floor_expected_marker(other, first_id)
        check('extra-multiple-claims-marker-absent', other_marker)
        with pytest.MonkeyPatch.context() as mp:
            h._crash_floor_after_marker(mp, other, first_id)
        check('extra-multiple-claims-M+A-', other_marker)
        current.consume_attempt_ticket(other, attempt_id=first_id)
        check('extra-multiple-claims-M+A+', other_marker)
        # Exact 2 claims x 2 attempts: every target has marker and ledger hits
        # from both claims, while only its own A row is absent.
        row = schedule[1]
        other_id = f"{cell['cell_id']}::seq{row['seq']}"
        h._append_journal_rows(other, {
            'event': 'session-start', 'seq': row['seq'], 'round': row['round'],
            'kind': 'planned', 'cell_id': cell['cell_id'], 'attempt_id': other_id, 'trigger': None,
        })
        current.consume_attempt_ticket(other, attempt_id=other_id)
        four = markers[:2] + [other_marker, h._floor_expected_marker(other, other_id)]
        third_path = current._floor_canonical_marker_path(shared, markers[2])
        with changed_files(ledger, third_path):
            third_path.unlink()
            for index, target in enumerate(four):
                write_rows(ledger, [m for m in four if m != target])
                check(f'multiclaim-2x2-target-{index}-M+A-', target)
            target = four[0]
            write_rows(ledger, [m for m in four if m != target])
            # Force the invalid non-target marker after its claim's valid hit.
            other_pair = sorted(four[2:], key=lambda m: current._floor_canonical_marker_path(shared, m).name)
            victim = other_pair[-1]
            victim_path = current._floor_canonical_marker_path(shared, victim)
            bad = dict(victim)
            for index in range(10000):
                bad['attempt_id'] = f"{victim['cell_id']}::unregistered-{index}"
                bad_path = current._floor_canonical_marker_path(shared, bad)
                if bad_path.name > current._floor_canonical_marker_path(shared, other_pair[0]).name:
                    break
            else:
                raise ValueError('cannot order multiclaim coverage marker')
            with changed_files(victim_path, bad_path, ledger):
                victim_path.unlink()
                bad_path.write_bytes(h._canonical(bad) + b'\n')
                write_rows(ledger, [m for m in four if m not in (target, victim)])
                check('e-multiclaim-2x2-nontarget-marker-coverage', target)
            with changed_files(ledger):
                write_rows(ledger, [m for m in four if m not in (target, victim)] + [bad])
                check('e-multiclaim-2x2-nontarget-A-coverage', target)
            # Each sequence starts from healthy bytes in the same process/root.
            for source in ('claim', 'main'):
                path = claim if source == 'claim' else main
                with changed_files(path):
                    check(f'recall-{source}-before-M+A-', target)
                    if source == 'claim':
                        doc = json.loads(path.read_bytes())
                        doc['records'] += 1
                        path.write_bytes(h._canonical(doc) + b'\n')
                    else:
                        rows = current._read_ledger(path)
                        next(r for r in rows if r.get('measurement_generation_claim_digest') ==
                             target['measurement_generation_claim_digest'])['records'] += 1
                        write_rows(path, rows)
                    check(f'e-recall-{source}-after-tamper', target)
        # The base test file has no cut-6 legacy fixture. Build the small stable
        # input here; production constructors are input generators, not an oracle.
        generation_claim = json.loads(claim.read_bytes())
        for version in ('v1', 'v2'):
            legacy_root = Path(tmp) / ('legacy-' + version)
            (legacy_root / 'claims').mkdir(parents=True)
            (legacy_root / 'consumed').mkdir()
            (legacy_root / 'ledger.lock').touch(mode=0o600)
            key = {k: state.row[k] for k in ('freeze_sha256', 'freeze_holdout_key',
                'configuration_id', 'ccbench_pin', 'env_tag', 'observation_role')}
            digest = current._claim_digest(key)
            legacy_claim = {k: generation_claim[k] for k in current._FLOOR_CLAIM_KEYS_V1
                            if k not in ('schema_version', 'event', 'key', 'irreversible_pilot_approved')}
            legacy_claim.update(schema_version='s8b-holdout-cell-claim/' + version,
                                event='claim', key=key, irreversible_pilot_approved=True)
            if version == 'v2':
                legacy_claim.update(entry_kind='fresh', nondefault_seams=[])
            legacy_claim_path = legacy_root / 'claims' / (digest + '.claim')
            legacy_claim_path.write_bytes(h._canonical(legacy_claim) + b'\n')
            main_row = {**key, **{k: legacy_claim[k] for k in current._FLOOR_LEDGER_KEYS
                       if k in legacy_claim and k not in ('schema_version', 'event')}}
            main_row.update(schema_version=current._LEDGER_SCHEMA, event='admit',
                            manifest_sha256=state.row['manifest_sha256'],
                            attempt_count=len(legacy_claim['attempt_ids']))
            legacy_main = legacy_root / 'ledger.jsonl'
            write_rows(legacy_main, [main_row])
            legacy_markers = [current._canonical_floor_attempt_document(
                claim_digest=digest, attempt_id=m['attempt_id'],
                **{k: m[k] for k in ('campaign_run_id', 'manifest_sha256', 'run_relpath',
                                    'cell_id', 'freeze_holdout_key', 'configuration_id')}) for m in markers[:2]]
            legacy_markers.sort(key=lambda m: current._floor_canonical_marker_path(legacy_root, m).name)
            for m in legacy_markers:
                current._floor_canonical_marker_path(legacy_root, m).write_bytes(h._canonical(m) + b'\n')
            write_rows(legacy_root / 'attempt-ledger.jsonl', [legacy_markers[0]])
            target = legacy_markers[1]
            def legacy_check(label):
                results.append(compare(current, base, legacy_root, target, False, label))
            legacy_check(f'legacy-{version}-second-marker-M+A-')
            victim = legacy_markers[1]
            victim_path = current._floor_canonical_marker_path(legacy_root, victim)
            bad = dict(victim)
            for index in range(10000):
                bad['attempt_id'] = f"{victim['cell_id']}::unregistered-{index}"
                bad_path = current._floor_canonical_marker_path(legacy_root, bad)
                if bad_path.name > current._floor_canonical_marker_path(legacy_root, legacy_markers[0]).name:
                    break
            else:
                raise ValueError('cannot order legacy coverage marker')
            with changed_files(victim_path, bad_path):
                victim_path.unlink()
                bad_path.write_bytes(h._canonical(bad) + b'\n')
                target = legacy_markers[0]
                legacy_check(f'e-legacy-{version}-membership')
            target = legacy_markers[1]
            with changed_files(legacy_main):
                unrelated = dict(main_row, configuration_id='unrelated')
                unrelated.pop('records')
                write_rows(legacy_main, [main_row, unrelated])
                legacy_check(f'e-legacy-{version}-unrelated-floor-shape')
    return results, positive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root', type=Path, required=True)
    p.add_argument('--base-module', type=Path, required=True)
    p.add_argument('--out', type=Path)
    p.add_argument('--selftest', action='store_true')
    args = p.parse_args()
    if not args.selftest and args.out is None:
        p.error('--out is required except with --selftest')
    if not args.repo_root.is_absolute() or not args.base_module.is_absolute():
        p.error('repo-root and base-module must be absolute')
    current, base, helpers = load_modules(args.repo_root.resolve(), args.base_module)
    if args.selftest and Path(current.__file__).read_bytes() != args.base_module.read_bytes():
        raise ValueError('--selftest requires current == pinned base; use regular mode after integration')
    results, positive = exercise(current, base, helpers, Path(__file__).resolve().parent, args.selftest)
    if args.selftest:
        # Avoid a vacuous agreement where both sides fail during fixture setup.
        for r in results:
            observed = r['orders'][0]['base']
            label = r['state']
            if label.startswith(('e-', 'f-', 'g-', 'h-', 'i-', 'j-')):
                if observed.get('type') != 'HoldoutAdmissionError':
                    raise ValueError('negative state did not reach admission rejection: ' + label)
            else:
                if observed['kind'] != 'return':
                    raise ValueError('positive state unexpectedly rejected: ' + label)
                expects_marker = label.endswith('M+A-')
                if (observed['value'] is not None) != expects_marker:
                    raise ValueError('wrong baseline candidate result: ' + label)
        if IMPORT_AUDIT['writes'] or IMPORT_AUDIT['processes']:
            raise ValueError('unexpected import write/process: ' + str(IMPORT_AUDIT))
    mismatches = [r['state'] for r in results if not r['match']]
    positive_ok = not args.selftest or (positive is not None and positive['rc'] == 1)
    rc = int(bool(mismatches) or not positive_ok)
    report = {'repo_root': str(args.repo_root), 'base_module': str(args.base_module),
              'base_sha256': BASE_SHA, 'import_side_effects': IMPORT_NOTES,
              'import_audit': IMPORT_AUDIT,
              'exception_correspondence': {m.__name__: list(exception_map(m).values()) for m in (current, base)},
              'states': results, 'state_count': len(results), 'matched': len(results) - len(mismatches),
              'mismatches': mismatches, 'positive_control': positive, 'rc': rc}
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"{'PASS' if rc == 0 else 'FAIL'} states={len(results)} matched={len(results)-len(mismatches)} mismatches={json.dumps(mismatches)} positive_control_rc={positive['rc'] if positive else 'not-run'} import_writes={len(IMPORT_AUDIT['writes'])} import_processes={len(IMPORT_AUDIT['processes'])} rc={rc}")
    return rc


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL setup: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(2)
```

# 親が書いた補助 script (job dir 直下、読取だけ)

## freeze_floor_subset.py (sha256 `220a9251554a9ecfbde4ddbadfb1ea3faa31d9f33934cfe947dce105667bf9a1`)

```python
#!/usr/bin/env python3
"""親専用 (読取だけ): T-2766 の 6 走 (03-A..08-B) の shard junit から floor file の nodeid ごとの中央値を取り、
補助指標の部分集合 S_mid = {nodeid : median ∈ [4, 12] s} と完全集合 S_all を測定前に凍結する。"""
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RUNS = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/runs")
OUT = Path(sys.argv[1])
FILE = "orchestrator/tests/test_s8b_floor_campaign.py"
CLASS = "orchestrator.tests.test_s8b_floor_campaign"
runs = ["03-A", "04-B", "05-B", "06-A", "07-A", "08-B"]
times: dict[str, list[float]] = {}
per_run_sets: dict[str, set[str]] = {}
for r in runs:
    seen: set[str] = set()
    for s in (0, 1, 2):
        root = ET.parse(RUNS / r / "session" / f"shard-{s}" / "junit.xml").getroot()
        for tc in root.iter("testcase"):
            if tc.get("classname") != CLASS:
                continue
            nodeid = f"{FILE}::{tc.get('name')}"
            if nodeid in seen:
                raise SystemExit(f"duplicate nodeid in {r}: {nodeid}")
            seen.add(nodeid)
            times.setdefault(nodeid, []).append(float(tc.get("time")))
    per_run_sets[r] = seen
sets = list(per_run_sets.values())
if any(s != sets[0] for s in sets):
    raise SystemExit("floor nodeid sets differ across the 6 runs")
all_ids = sorted(sets[0])
med = {n: statistics.median(times[n]) for n in all_ids}
s_mid = sorted(n for n in all_ids if 4.0 <= med[n] <= 12.0)
s_long = sorted(n for n in all_ids if med[n] > 12.0)
payload = {
    "source_runs": runs,
    "source_dir": str(RUNS),
    "file": FILE,
    "rule": "median over the 6 T-2766 runs (3 shard junit, each node once) in [4.0, 12.0] s",
    "n_all": len(all_ids),
    "n_mid": len(s_mid),
    "n_long": len(s_long),
    "sum_mid_median": round(sum(med[n] for n in s_mid), 3),
    "sum_long_median": round(sum(med[n] for n in s_long), 3),
    "sum_all_median": round(sum(med.values()), 3),
    "S_all": all_ids,
    "S_mid": s_mid,
    "S_long": s_long,
    "median_by_nodeid": {n: round(med[n], 3) for n in all_ids},
}
OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
print(f"n_all={len(all_ids)} n_mid={len(s_mid)} n_long={len(s_long)} sum_mid={payload['sum_mid_median']} sum_long={payload['sum_long_median']} sum_all={payload['sum_all_median']}")
```

## make_mutation_spec.py (sha256 `45726c99446d19a35ecb5a8f58a74866fa8e6fc971ef52f85fc061d892fa6be9`)

```python
#!/usr/bin/env python3
"""親専用: 段 4 §5 の変異 (M1/M3/M4/M5/M6g/M6v/M7/M8 + P0) の spec を、実装 tip の現物から old 文字列の一意性を検算して書く。
usage: make_mutation_spec.py <worktree> <mode: probe|final> <out.json> [expected-nodes.json]
probe: 全件 SURVIVED 期待 (node 空) で観測 node を集める。final: expected-nodes.json (mutation id → sorted nodeid list) を KILLED 期待に載せ、P0 は SURVIVED。"""
import hashlib
import json
import sys
from pathlib import Path

wt = Path(sys.argv[1])
mode = sys.argv[2]
out = Path(sys.argv[3])
expected = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
FILE = "orchestrator/campaign/s8b_holdout_admission.py"
src = (wt / FILE).read_text(encoding="utf-8")

M = []

def add(mid, category, replacements, note_status):
    for r in replacements:
        n = src.count(r["old"])
        if n != 1:
            raise SystemExit(f"{mid}: old は file 内で {n} 回 (1 回でない): {r['old'][:60]!r}")
    M.append((mid, category, replacements, note_status))

# M1: hit のときだけ marker の campaign_run_id を信用して期待文書を組む (generation 経路)
add("M1-hit-trusts-marker-campaign-run-id", "negative", [{
    "file": FILE,
    "old": "    expected = _canonical_measurement_generation_floor_attempt_document(\n        attempt_id=attempt_id, **projection.document_fields,\n    )\n",
    "new": "    _hit = context is not None and memo_key in context.projections\n    expected = _canonical_measurement_generation_floor_attempt_document(\n        attempt_id=attempt_id, **{**projection.document_fields, **({\"campaign_run_id\": marker.get(\"campaign_run_id\")} if _hit else {})},\n    )\n",
}], "KILLED")
# M3: hit 時の attempt coverage 検査を省く (generation 経路)
add("M3-hit-skips-coverage", "negative", [{
    "file": FILE,
    "old": "    elif attempt_id not in projection.attempt_ids:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation claim attempt coverage is invalid\"\n        )\n",
    "new": "    elif False and attempt_id not in projection.attempt_ids:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation claim attempt coverage is invalid\"\n        )\n",
}], "KILLED")
# M4: canonical filename 比較を省く
add("M4-skip-canonical-filename", "negative", [{
    "file": FILE,
    "old": "        if path != _floor_canonical_marker_path(root, canonical):\n            raise HoldoutAdmissionError(\"floor consume marker filename is not canonical\")\n",
    "new": "        if False and path != _floor_canonical_marker_path(root, canonical):\n            raise HoldoutAdmissionError(\"floor consume marker filename is not canonical\")\n",
}], "KILLED")
# M5: A identity 重複検査を省く
add("M5-skip-attempt-ledger-duplicate-identity", "negative", [{
    "file": FILE,
    "old": "        if identity in ledger_by_identity:\n            raise HoldoutAdmissionError(\"floor attempt ledger has a duplicate identity\")\n",
    "new": "        if False and identity in ledger_by_identity:\n            raise HoldoutAdmissionError(\"floor attempt ledger has a duplicate identity\")\n",
}], "KILLED")
# M6g: generation 経路の main != expected_main を省く
add("M6g-skip-main-equality-generation", "negative", [{
    "file": FILE,
    "old": "    if main != expected_main:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation ledger differs from its claim\"\n        )\n",
    "new": "    if False and main != expected_main:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation ledger differs from its claim\"\n        )\n",
}], "KILLED")
# M6v: v1 経路の main != expected_main を省く
add("M6v-skip-main-equality-v1", "negative", [{
    "file": FILE,
    "old": "    if main != expected_main:\n        raise HoldoutAdmissionError(\"floor consume main ledger differs from its claim\")\n",
    "new": "    if False and main != expected_main:\n        raise HoldoutAdmissionError(\"floor consume main ledger differs from its claim\")\n",
}], "KILLED")
# M7: completed 拒否 (MUT-A6) を省く
add("M7-skip-completed-rejection", "negative", [{
    "file": FILE,
    "old": "    if completed_attempt:\n        # MUT-A6: completed session evidence forbids a second measurement.\n",
    "new": "    if False and completed_attempt:\n        # MUT-A6: completed session evidence forbids a second measurement.\n",
}], "KILLED")
# M8: memo を root を key にした module 変数へ昇格 (呼び出しを跨いで保持)
add("M8-memo-survives-across-calls", "negative", [{
    "file": FILE,
    "old": "class _FloorAttemptRecoveryContext:\n",
    "new": "_T2802_CTX: dict = {}\n\n\nclass _FloorAttemptRecoveryContext:\n",
}, {
    "file": FILE,
    "old": "    context = _FloorAttemptRecoveryContext()\n",
    "new": "    context = _T2802_CTX.setdefault(root, _FloorAttemptRecoveryContext())\n",
}], "KILLED")
# P0: 等価変異 (A 行 identity の str(...) を外す)
add("P0-equivalent-identity-str", "positive", [{
    "file": FILE,
    "old": "        identity = (\n            str(canonical[identity_field]), str(canonical[\"attempt_id\"]),\n        )\n        if identity in ledger_by_identity:\n",
    "new": "        identity = (\n            canonical[identity_field], canonical[\"attempt_id\"],\n        )\n        if identity in ledger_by_identity:\n",
}], "SURVIVED")

mutations = []
for mid, category, replacements, status in M:
    if mode == "probe":
        st, nodes = "SURVIVED", []
    else:
        st = status
        nodes = sorted(expected.get(mid, [])) if status == "KILLED" else []
        if st == "KILLED" and not nodes:
            raise SystemExit(f"{mid}: final で expected nodes が空")
    mutations.append({
        "id": mid, "category": category, "replacements": replacements,
        "expected_nodes": nodes, "expected_status": st, "hang_risk": False,
    })
spec = {
    "schema": "izanagi-dev-wave-mutation-spec/v1",
    "estimated_run_seconds": 120,
    "timeout_seconds": 4500,
    "hang_timeout_seconds": 900,
    "mutations": mutations,
}
raw = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
out.write_text(raw, encoding="utf-8")
print(out, hashlib.sha256(raw.encode("utf-8")).hexdigest(), len(mutations), "mutations", mode)
```

## run-diag-t080.sh (sha256 `074b8707934b54bae177a9480aa82067cb103914fd51bda06afbfe942be93f6a`)

```bash
#!/bin/bash
# 親専用: 事前登録外の診断走。t080 shared base 構築 test 1 本を A/B 両 tree から交互 (A,B,A,B) に計算ノードで走らせ、
# run_tests の "N passed in Xs" 行と dispatch の node 名を採る。判定には使わない (README に「診断」と明記)。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery
A=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-base-a
B=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery
D="$J/diag-t080"
mkdir -p "$D"
echo $$ > "$D/diag.pid"
rm -f "$D/diag.done"
NODE="orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes"
i=0
for cond in A B A B; do
  i=$((i + 1))
  if [ "$cond" = "A" ]; then W="$A"; else W="$B"; fi
  tag="$(printf '%02d' "$i")-$cond"
  cd "$W" || { echo 90 > "$D/diag.done"; exit 90; }
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') launch $tag head=$(git rev-parse HEAD)" >> "$D/diag.log"
  python3 tools/run_tests.py --force-dispatch "$NODE" -q -rf -p no:cacheprovider > "$D/$tag.log" 2>&1
  rc=$?
  summary=$(grep -a -o "[0-9]* passed in [0-9.]*s" "$D/$tag.log" | tail -1)
  node=$(grep -a -o "bnode[0-9]*" "$D/$tag.log" | head -1)
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $tag rc=$rc $summary node=$node" >> "$D/diag.log"
done
echo 0 > "$D/diag.done"
```

## lock_intervals.py (sha256 `2bd4ce0ddf79bf8d112078b4ea49201b3b5d4121edbc92a79e49213e05711338`)

```python
#!/usr/bin/env python3
"""親専用 (読取だけ): 各走の shard-0 report.json の real_repo_lock_intervals を集計する (本数・総保持秒・最長・lock 系列の span)。"""
import json
import sys
from pathlib import Path

root = Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/runs')
for tag in sys.argv[1:]:
    p = root / tag / 'session' / 'shard-0' / 'report.json'
    if not p.exists():
        print(tag, 'no report'); continue
    r = json.load(open(p))
    t0 = r['session_timeline']['collection_finished_epoch_s']
    ivs = []
    for w, rec in r['session_timeline']['workers'].items():
        for iv in rec.get('real_repo_lock_intervals') or []:
            if isinstance(iv, dict):
                s, e = iv.get("acquired_epoch_s"), iv.get("released_epoch_s")
            else:
                s, e = iv[0], iv[1]
            ivs.append((w, float(s) - t0, float(e) - t0))
    ivs.sort(key=lambda x: x[1])
    tot = sum(e - s for _, s, e in ivs)
    longest = max(((e - s, w) for w, s, e in ivs), default=(0, '-'))
    span = (ivs[0][1], ivs[-1][2]) if ivs else (0, 0)
    print(f"{tag}: intervals={len(ivs)} total_hold={tot:.1f}s longest={longest[0]:.1f}s({longest[1]}) span={span[0]:.0f}..{span[1]:.0f}s W={r['terminal_counts'] if 'terminal_counts' in r else ''}")
    for w, s, e in ivs[:40]:
        print(f"   {w:5s} {s:7.1f} -> {e:7.1f}  ({e - s:6.1f}s)")
```

## node_delta_breakdown.py (sha256 `edc50ca409765c72d5add507fc320c263433a5febdc644b35cf0d4cc8b300628`)

```python
#!/usr/bin/env python3
"""親専用 (読取だけ): analysis.json の有効対ごとに nodeid 単位の対差の内訳 (B が遅い node) を出す。"""
import json
import sys
from decimal import Decimal

d = json.load(open(sys.argv[1]))
pairs = [p for p in d['pairs'] if p.get('valid')]
for p in pairs:
    nd = {k: Decimal(str(v)) for k, v in p['node_deltas'].items()}
    neg = sorted(nd.items(), key=lambda kv: kv[1])[:14]
    print('== pair', p['pair_slot'], p['runs'], 'delta_F', p['delta_F'], 'delta_F_mid', p['delta_F_mid'], 'delta_F_long', p.get('delta_F_long'))
    tot_neg = sum(v for v in nd.values() if v < 0)
    tot_pos = sum(v for v in nd.values() if v > 0)
    print('  sum neg', round(tot_neg, 1), 'sum pos', round(tot_pos, 1),
          'n neg<-3', sum(1 for v in nd.values() if v < -3), 'n pos>3', sum(1 for v in nd.values() if v > 3))
    for k, v in neg:
        print('   ', round(v, 1), k.split('::')[1][:120])
```
