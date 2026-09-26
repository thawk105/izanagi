# 計測 probe の逐語 (repo 外で実行、repo へは land しない)

Codex author (子 branch author-t2273lc-probe の 57e3e1c96、集計器だけ fix 子 branch author-t2273lc-probe-fix1 の d16f13781)。job dir /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ で実行した bytes と同一 (git blob 照合済み)。改作元は T-2825 の probe。

## t2273lc_run_series.sh

````text
#!/bin/bash
# usage: t2273lc_run_series.sh <spec...>; spec is "NN X slot".
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [ "$#" -eq 0 ]; then
  set -- "01 A 1" "02 B 1" "03 B 2" "04 A 2" "05 A 3" "06 B 3"
fi
for spec in "$@"; do
  if [[ ! "$spec" =~ ^[0-9]{2}\ [AB]\ [123]$ ]]; then
    echo 'usage: t2273lc_run_series.sh <"NN X slot"...>' >&2; exit 2
  fi
done
preflight() {
  python3 - "$J" "$SCRIPT_DIR" "$1" "$2" "$3" <<'PREFLIGHT'
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2273lc_ab_analyze import classification, warm_errors, analyze, check_request, read_submissions, check_number
job = Path(sys.argv[1])
try:
    tips = json.loads((job / 'measurement-tips.json').read_bytes())
    errors = warm_errors(job, tips)
    if errors:
        raise ValueError('; '.join(errors))
except (OSError, ValueError, KeyError, TypeError) as exc:
    print('warm precondition: ' + str(exc), file=sys.stderr)
    sys.exit(94)
try:
    entries = read_submissions(job)
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(98)
try:
    check_number(entries, sys.argv[5])
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(99)
paths = [job / 'runs' / e['tag'] for e in entries]
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
result = analyze(paths, job / 'input/login-collection.log', tips, warm_root=job)
try:
    check_request(result, sys.argv[3], int(sys.argv[4]))
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(92)

PREFLIGHT
}
read -r nn cond slot <<< "$1"
preflight "$cond" "$slot" "$nn" || exit $?
echo $$ > "$J/series.pid" || exit 2
rm -f "$J/series.done"
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$J/series.log"; }
log 'series start'
for spec in "$@"; do
  read -r nn cond slot <<< "$spec"
  preflight "$cond" "$slot" "$nn" || { rc=$?; echo "$rc" > "$J/series.done"; exit "$rc"; }
  log "launch $nn-$cond slot $slot"
  bash "$SCRIPT_DIR/t2273lc_run_measure.sh" "$nn" "$cond" "$slot"
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
````

## t2273lc_run_measure.sh

````text
#!/bin/bash
# T-2273 sequential, pinned-tree acceptance measurement.
set -uo pipefail
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy
JOBDIR=$J
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SLUG=dev-wave-t2273-shard0-local-copy
if [ "$#" -ne 3 ] || [[ ! "$1" =~ ^[0-9]{2}$ ]] || [[ ! "$2" =~ ^[AB]$ ]] || [[ ! "$3" =~ ^[123]$ ]]; then
  echo 'usage: t2273lc_run_measure.sh <NN> <A|B> <pair-slot>' >&2
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
source "$SCRIPT_DIR/t2273lc_gate.conf" || exit 2
mkdir -p "$JOBDIR/aborts" || exit 2
STAMP=$(date '+%Y%m%dT%H%M%S')
ABORT="$JOBDIR/aborts/$TAG-$STAMP.log"
abort() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $2" >> "$ABORT"; exit "$1"; }
if [ "$COND" != "A" ] && [ "$COND" != "B" ]; then abort 2 "bad condition: $COND"; fi

# 直列化: 最初に flock (fd 9)。取れなければ何も作らない。
exec 9> "$JOBDIR/measure.lock" || abort 94 "cannot open lock"
if ! flock -n 9; then abort 94 "another measurement holds the lock"; fi
# Shared history validation under flock; refusal does not append or create RUN.
python3 - "$JOBDIR" "$SCRIPT_DIR" "$COND" "$SLOT" "$NN" <<'STOPPY'
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2273lc_ab_analyze import analyze, check_request, read_submissions, check_number
job = Path(sys.argv[1])
try:
    entries = read_submissions(job)
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(98)
try:
    check_number(entries, sys.argv[5])
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(99)
paths = [job / 'runs' / e['tag'] for e in entries]
result = analyze(paths, job / 'input/login-collection.log',
                 json.loads((job / 'measurement-tips.json').read_bytes()), warm_root=job)
try:
    check_request(result, sys.argv[3], int(sys.argv[4]))
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(92)
STOPPY
check_rc=$?
if [ "$check_rc" -ne 0 ]; then abort "$check_rc" "request refused before submission"; fi

export IZANAGI_ACCEPTANCE_SHARDS=3
unset PYTHONDONTWRITEBYTECODE
cd "$WT" || abort 90 "cd failed"

count_leaders() { ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc "$SLUG" || true; }
load1() { read -r l1 _ < /proc/loadavg; echo "$l1"; }
dirty_lines() {
  git -C "$WT" status --porcelain --untracked-files=all --ignore-submodules=none |
    python3 -c 'import sys; print(sum(not line.startswith("?? output/pegasus-dispatch/") for line in sys.stdin))'
}
glog() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$JOBDIR/aborts/$TAG-$STAMP.gate.log"; }

gate_open() {
  source "$SCRIPT_DIR/t2273lc_gate.conf" || abort 2 "t2273lc_gate.conf unavailable"
  l1=$(load1)
  leaders=$(count_leaders)
  glog "gate: load1=$l1 leaders=$leaders (max $LEADERS_MAX, l1 <= $L1_MAX)"
  python3 - "$l1" "$leaders" "$LEADERS_MAX" "$L1_MAX" <<'PY'
import sys
l1, leaders, lmax, l1max = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
sys.exit(0 if (leaders <= lmax and l1 <= l1max) else 1)
PY
}

round=0; stable=0; opened=0
while [ "$round" -lt "$GATE_MAX_ROUNDS" ]; do
  round=$((round + 1))
  if ! gate_open; then stable=0; sleep $((PERIOD_MIN + RANDOM % PERIOD_WIDTH)); continue; fi
  stable=$((stable + 1))
  if [ "$stable" -lt 2 ]; then sleep $((PERIOD_MIN + RANDOM % PERIOD_WIDTH)); continue; fi
  sleep $((RANDOM % JITTER_WIDTH))
  if ! gate_open; then stable=0; sleep $((PERIOD_MIN + RANDOM % PERIOD_WIDTH)); continue; fi
  # 投入直前の照合: 門番へ戻った場合も HEAD / clean / diff を取り直す。
  TIP=$(git -C "$WT" rev-parse HEAD)
  DIRTY_BEFORE=$(dirty_lines) || abort 91 "status failed"
  if [ "$TIP" != "$MEASUREMENT_TIP" ]; then abort 95 "HEAD $TIP != measurement tip"; fi
  if [ "$DIRTY_BEFORE" -ne 0 ]; then abort 91 "worktree dirty before launch ($DIRTY_BEFORE lines)"; fi

  if ! git -C "$WT" diff --name-only "$A_SHA" "$B_SHA" > "$JOBDIR/aborts/$TAG-$STAMP.diff.stat"; then
    abort 95 "cannot calculate tracked diff"
  fi
  if [ ! -s "$JOBDIR/aborts/$TAG-$STAMP.diff.stat" ]; then abort 95 "A and B have no tracked diff"; fi
  DIFF_SHA=$(sha256sum "$JOBDIR/aborts/$TAG-$STAMP.diff.stat" | cut -d' ' -f1)

  # 照合中に門番が閉じたら、走番号を消費せず同じ round 上限で待ち直す。
  if ! gate_open; then stable=0; sleep $((PERIOD_MIN + RANDOM % PERIOD_WIDTH)); continue; fi
  LEADERS=$leaders
  L1=$l1
  opened=1
  break
done
if [ "$opened" -ne 1 ]; then abort 93 "gate never opened"; fi

# ここで初めて RUN dir を作る (既存なら mkdir が失敗 = 再利用拒否)。
mkdir -p "$JOBDIR/runs" || abort 2 "cannot create runs parent"
# Durable append immediately before RUN creation. A crash here fails closed;
# the ordinary log cannot protect against tampering with the log itself.
python3 - "$JOBDIR" "$SCRIPT_DIR" "$NN" "$COND" "$SLOT" <<'APPENDPY'
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2273lc_ab_analyze import append_submission
append_submission(Path(sys.argv[1]), sys.argv[3], sys.argv[4], int(sys.argv[5]))
APPENDPY
if [ "$?" -ne 0 ]; then abort 98 "submission ledger append failed; inspect history"; fi
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

# Copy all mandatory artifacts and actual nested dispatch request/receipt, hashing source and copy.
COPY_OK=0
if [ -n "$ROOT" ] && [ -d "$ROOT" ]; then
  python3 - "$ROOT" "$RUN/session" <<'COPYPY'
from pathlib import Path
import hashlib, shutil, sys
src, dst = map(Path, sys.argv[1:])
dst.mkdir(parents=True, exist_ok=True)
required = ['login-collection.log', 'junit.xml'] + [f'shard-{s}/{f}' for s in range(3) for f in ('junit.xml','report.json')]
optional = [f'shard-{s}/dispatch/{prefix}{f}' for s in range(3) for prefix in ('',f'shard-{s}/') for f in ('request.json','receipt.json')]
errors = []
with (dst/'SHA256SUMS').open('w') as hashes:
    for rel in required + [r for r in optional if (src/r).is_file()]:
        try:
            data = (src/rel).read_bytes()
            (dst/rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src/rel,dst/rel)
            sha = hashlib.sha256(data).hexdigest()
            assert sha == hashlib.sha256((dst/rel).read_bytes()).hexdigest()
            hashes.write(f'{sha}  {rel}\n')
        except (OSError, AssertionError) as exc:
            errors.append(f'{rel}: {exc}')
print('\n'.join(errors))
sys.exit(bool(errors))
COPYPY
  [ "$?" -eq 0 ] && COPY_OK=1
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
    "tag": nn + "-" + cond, "run": nn, "condition": cond, "pair_slot": int(slot),
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
    "gate": {"leaders_max": int(lmax), "load1_max_inclusive": float(l1max),
             "leader_query": "argv-start python dev_wave_wait.py acceptance; exclude slug"},
}, open(path, "w"), indent=2, ensure_ascii=True)
PY
json_rc=$?
final=$rc
if [ "$json_rc" -ne 0 ]; then final=97; log "run.json generation failed rc=$json_rc"; fi
if [ "$COPY_OK" -ne 1 ] && [ "$final" -eq 0 ]; then final=96; log "copy failed with child rc=0"; fi
if { [ "$TIP_AFTER" != "$MEASUREMENT_TIP" ] || [ "$DIRTY_AFTER" -ne 0 ]; } && [ "$final" -eq 0 ]; then final=95; fi
echo "$final" > "$RUN/measure.done"
exit "$final"
````

## t2273lc_run_warm.sh

````text
#!/bin/bash
# usage: t2273lc_run_warm.sh <A|B>
set -uo pipefail
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy
if [ "$#" -ne 1 ] || [[ ! "$1" =~ ^[AB]$ ]]; then
  echo 'usage: t2273lc_run_warm.sh <A|B>' >&2; exit 2
fi
COND=$1
# Keep all before/after evidence in one record even when the child fails.
python3 - "$J" "$COND" <<'PYWARM'
import fcntl
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
lock = (job / 'measure.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
require_unused = not any((job / 'runs').glob('*/run.json'))
if not require_unused or (job / ('warm-' + condition + '.json')).exists():
    sys.exit('warm refuses overwrite or runs already submitted')
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
        env.pop('IZANAGI_ACCEPTANCE_SHARDS', None)
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
````

## t2273lc_gate.conf

````text
LEADERS_MAX=1
L1_MAX=60
GATE_MAX_ROUNDS=120
PERIOD_MIN=100
PERIOD_WIDTH=41
JITTER_WIDTH=46
````

## t2273lc_ab_analyze.py

````text
#!/usr/bin/env python3
"""T-2273 preregistered W_0 analysis; offline, standard library only."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
from statistics import median
import sys
import subprocess
import xml.etree.ElementTree as ET

JOB = Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy')
PREFIX = 'izanagi_acceptance_pairing_v1_'
E1_ADDED_NODE = 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_visible_output_uses_one_snapshot'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def split_group(node):
    return node.rsplit('@', 1) if node.rfind('@') > node.rfind(']') else (node, None)


def junit_key(node):
    head, bracket, parameter = node.partition('[')
    parts = head.split('::')
    parts[0] = parts[0].replace('/', '.').removesuffix('.py')
    return '.'.join(parts[:-1]), parts[-1] + bracket + parameter


def collection_nodes(path):
    nodes = [line.strip() for line in path.read_text().splitlines()
             if line.strip().startswith('orchestrator/tests/') and '.py::' in line]
    require(nodes, 'empty login collection')
    return Counter(nodes)


def verify_hashes(session):
    required = {'login-collection.log', 'junit.xml'} | {
        f'shard-{s}/{f}' for s in range(3) for f in ('junit.xml', 'report.json')}
    entries = {}
    for line in (session / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        require(name not in entries and not Path(name).is_absolute() and '..' not in Path(name).parts,
                'unsafe/duplicate hash path')
        require(re.fullmatch('[0-9a-f]{64}', digest), 'invalid hash')
        require(hashlib.sha256((session / name).read_bytes()).hexdigest() == digest, 'hash mismatch: ' + name)
        entries[name] = digest
    required.update(str(p.relative_to(session)) for p in session.glob('shard-*/dispatch/**/*.json'))
    require(required <= entries.keys(), 'missing artifact hashes')
    return entries


def red_evidence(path, metadata):
    bodies = []
    red = metadata.get('rc') != 0
    try:
        red |= int((path / 'measure.done').read_text()) != 0
    except (OSError, ValueError):
        red = True
    for xml in sorted((path / 'session').glob('shard-*/junit.xml')):
        try:
            root = ET.parse(xml).getroot()
            for case in root.iter('testcase'):
                for tag in ('failure', 'error'):
                    for failure in case.findall(tag):
                        red = True
                        bodies.append({'shard': xml.parent.name, 'classname': case.get('classname'),
                                       'name': case.get('name'), 'kind': tag,
                                       'message': failure.get('message'), 'body': failure.text or ''})
        except (OSError, ET.ParseError):
            pass
    result = {'red': red, 'red_testcases': bodies}
    if red:
        result['child_log'] = (path / 'child.log').read_text(errors='replace') if (path / 'child.log').exists() else None
    return result


def parse_session(session, collection):
    hashes = verify_hashes(session)
    baseline = collection_nodes(collection if collection.is_file() else session / 'login-collection.log')
    require(collection_nodes(session / 'login-collection.log') == baseline, 'login collection mismatch')
    all_nodes, skipped, shards = Counter(), [], []
    for j in range(3):
        shard = session / f'shard-{j}'
        report = json.loads((shard / 'report.json').read_bytes())
        require(report['shard_index'] == j and report['shard_count'] == 3, 'report shard mismatch')
        require(report['pytest_rc'] == 0 and not report['failures'], 'report red')
        selected = report['selected']
        require(Counter(report['finished']) == Counter(selected), 'shard incomplete')
        require(Counter(x['nodeid'] for x in report['observed_universe']) == baseline, 'observed universe mismatch')
        lookup = defaultdict(list)
        for node in selected:
            lookup[junit_key(split_group(node)[0])].append(node)
        raw = (shard / 'junit.xml').read_bytes()
        require(b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw, 'unexpected XML declaration')
        root = ET.fromstring(raw)
        suites = [root] if root.tag == 'testsuite' else list(root)
        require(len(suites) == 1 and suites[0].tag == 'testsuite', 'expected one pytest testsuite')
        suite = suites[0]
        cases = list(suite.iter('testcase'))
        counts = {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
        require(counts['tests'] == len(cases) and counts['failures'] == counts['errors'] == 0, 'red/count mismatch')
        timeline, occ = report['session_timeline'], report['worker_occupancy']
        require(occ, 'missing occupancy')
        for v in occ.values():
            finite(v['duration_s'])
            require(type(v['items']) is int and v['items'] >= 0, 'invalid occupancy items')
        rows, by_worker, sums, unmatched = [], defaultdict(list), defaultdict(float), []
        for order, case in enumerate(cases):
            name, group = split_group(case.attrib['name'])
            matches = lookup[(case.attrib['classname'], name)]
            if len(matches) != 1:
                unmatched.append(dict(case.attrib))
                continue
            node = matches[0]
            base, selected_group = split_group(node)
            require(selected_group is None or group == selected_group, 'selected/JUnit group mismatch')
            require(case.find('failure') is None and case.find('error') is None, 'red testcase')
            pairs = [(p.attrib['name'][len(PREFIX):], p.get('value'))
                     for p in case.findall('./properties/property') if p.get('name', '').startswith(PREFIX)]
            props = dict(pairs)
            require(len(props) == len(pairs) and set(props) == {'scope','rank','partner','worker'}, 'pairing property shape')
            worker = props['worker']
            require(worker in occ and worker in timeline['workers'], 'unknown worker')
            duration = finite(case.attrib['time'])
            rank, partner = int(props['rank']), int(props['partner'])
            require(rank >= 0 and partner in (0, 1), 'invalid pairing rank/partner')
            row = {'nodeid': node, 'runtime_group': group, 'scope': props['scope'], 'shard': j,
                   'worker': worker, 'rank': rank, 'partner': partner, 'time': duration,
                   'junit_order': order, 'worker_order': len(by_worker[worker]),
                   'estimated_start_offset_s': sums[worker],
                   'estimated_start_epoch_s': finite(timeline['workers'][worker]['first_test_started_epoch_s']) + sums[worker]}
            sums[worker] += duration
            rows.append(row)
            by_worker[worker].append(row)
            if case.find('skipped') is not None:
                skipped.append(node)
        require(not unmatched, 'JUnit mapping unresolved; login matched but item metrics unavailable: ' + str(unmatched[:3]))
        require(Counter(x['nodeid'] for x in rows) == Counter(selected), 'JUnit/selected collection mismatch')
        require(counts['skipped'] == sum(c.find('skipped') is not None for c in cases), 'skipped count mismatch')
        for worker, items in by_worker.items():
            require(occ[worker]['items'] == len(items), 'occupancy item count mismatch')
        all_nodes.update(x['nodeid'] for x in rows)
        W = finite(suite.attrib['time'])
        require(W > 0 and rows, 'empty/zero wall shard')
        busiest = max(occ, key=lambda w: occ[w]['duration_s'])
        longest = max(rows, key=lambda x: x['time'])
        O, L = finite(occ[busiest]['duration_s']), longest['time']
        t0 = timestamp(suite.attrib['timestamp']).timestamp()
        last = max(finite(w['last_test_finished_epoch_s']) for w in timeline['workers'].values()
                   if w.get('last_test_finished_epoch_s') is not None)
        dispatch = []
        for receipt in sorted(shard.glob('dispatch/**/receipt.json')):
            r = json.loads(receipt.read_bytes())
            marker = r.get('f49_compute_marker', {})
            dispatch.append({'path': str(receipt.relative_to(session)), 'node': marker.get('hostname'),
                             'job_id': marker.get('pbs_jobid'), 'receipt': r})
        requests = [{'path': str(p.relative_to(session)), 'request': json.loads(p.read_bytes())}
                    for p in sorted(shard.glob('dispatch/**/request.json'))]
        full_workers = {busiest, longest['worker']} if j == 0 else set()
        shards.append({'shard': j, **counts, 'W': W, 'O': O, 'L': L, 'O_minus_L': O-L, 'F': W-O,
                       'pre': finite(timeline['collection_finished_epoch_s'])-t0, 'post': t0+W-last,
                       'hostname': suite.get('hostname'), 'timestamp': suite.get('timestamp'),
                       'busiest_worker': busiest, 'longest': longest,
                       'O_L': occ[longest['worker']]['duration_s'], 'P_L': occ[longest['worker']]['duration_s']-L,
                       'L_worker_other_items': [x for x in by_worker[longest['worker']] if x is not longest] if j == 0 else [],
                       'selected_count': len(selected),
                       'selected_nodes': selected,
                       'selected_sha256': hashlib.sha256(('\n'.join(sorted(selected))+'\n').encode()).hexdigest(),
                       'worker_counts': {w: len(v) for w,v in by_worker.items()},
                       'worker_items': {w: by_worker[w] for w in sorted(full_workers)},
                       'dispatch': dispatch, 'requests': requests})
    require(all_nodes == baseline, 'global JUnit collection mismatch')
    maximum = max(s['W'] for s in shards)
    return {'shards': shards, 'skipped_nodes': sorted(skipped), 'W_0': shards[0]['W'], 'W_max': maximum,
            'collection_nodes': dict(baseline),
            'W_max_argmax': [s['shard'] for s in shards if s['W'] == maximum],
            'collection_sha256': hashlib.sha256(('\n'.join(sorted(baseline.elements()))+'\n').encode()).hexdigest(),
            'artifact_sha256': hashes,
            'collection_check': 'login and forward-projected JUnit multisets match input'}


def pair_metrics(a, b):
    delta = a['W_0'] - b['W_0']
    return {'W_0_A': a['W_0'], 'W_0_B': b['W_0'], 'delta_W_0': delta,
            'r': delta / a['W_0'], 'W_max_A': a['W_max'], 'W_max_B': b['W_max']}


def e1_pair_check(a, b, added_node=E1_ADDED_NODE):
    """Return E1 validity, reasons, and the shard containing B's added node."""
    a_nodes, b_nodes = Counter(a['collection_nodes']), Counter(b['collection_nodes'])
    expected = Counter([added_node]) if added_node else Counter()
    only_a, only_b = a_nodes - b_nodes, b_nodes - a_nodes
    reasons = []
    def brief(counter):
        return {'count': sum(counter.values()), 'sample': list(counter.items())[:3]}
    if only_a or only_b != expected:
        reasons.append(f'E1 collection difference: A only={brief(only_a)}, B only={brief(only_b)}, expected B only={dict(expected)}')
    common = a_nodes & b_nodes
    added_shards = []
    for j, (sa, sb) in enumerate(zip(a['shards'], b['shards'])):
        a_selected = Counter(sa['selected_nodes']) & common
        b_selected = Counter(sb['selected_nodes']) & common
        if a_selected != b_selected:
            reasons.append(f'E1 common node shard allocation differs: shard {j}, A only={brief(a_selected - b_selected)}, B only={brief(b_selected - a_selected)}')
        if added_node and Counter(sb['selected_nodes'])[added_node]:
            added_shards.append(j)
    return not reasons, reasons, added_shards


def aggregate(pairs):
    deltas = [p['delta_W_0'] for p in pairs]
    rates = [p['r'] for p in pairs]
    return {'median_delta_s': median(deltas) if deltas else None,
            'median_pair_rate': median(rates) if rates else None}


def finite(value):
    value = float(value)
    require(math.isfinite(value) and value >= 0, 'nonfinite/negative time')
    return value


def timestamp(value):
    t = datetime.fromisoformat(re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', value))
    require(t.tzinfo is not None, 'timezone missing')
    return t


def read_run(path, collection, tips):
    run = {'tag': path.name, 'valid': False, 'errors': [], 'skipped_nodes': []}
    try:
        m = json.loads((path / 'run.json').read_bytes())
        run['metadata'] = m
        run.update(red_evidence(path, m))
        require(path.name == f"{m['run']}-{m['condition']}", 'run tag mismatch')
        require(m['condition'] in ('A', 'B') and type(m['pair_slot']) is int and m['pair_slot'] in (1, 2, 3), 'condition/slot')
        require(type(m['rc']) is int and m['rc'] == 0 and m['copy_ok'] is True, 'rc/copy_ok')
        require(type(m['dirty_lines_before']) is int and type(m['dirty_lines_after']) is int
                and m['dirty_lines_before'] == m['dirty_lines_after'] == 0, 'dirty tree')
        require(timestamp(m['submitted_at']) < timestamp(m['finished_at']), 'invalid run interval')
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
                and finite(m['load1']) <= 60, 'gate metadata')
        gate_lines = (path / 'gate.log').read_text().splitlines()
        readings = []
        for line in gate_lines:
            match = re.search(r'gate: load1=([0-9.]+) leaders=([0-9]+)', line)
            require(match is not None, 'malformed gate record')
            readings.append({'load1': finite(match[1]), 'leaders': int(match[2]), 'raw': line})
        require(len(readings) >= 4 and all(x['leaders'] <= 1 and x['load1'] <= 60 for x in readings[-4:]), 'gate record violation')
        require(readings[-1]['leaders'] == m['other_leaders'] and readings[-1]['load1'] == m['load1'], 'gate log/metadata mismatch')
        require(m['gate']['leaders_max'] == 1 and m['gate']['load1_max_inclusive'] == 60, 'gate threshold mismatch')
        run['gate_readings'] = readings
        require((path / 'tracked-diff.stat').read_text().strip(), 'empty tracked diff')
        run.update(parse_session(path / 'session', collection))
        run['valid'] = True
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError, IndexError, subprocess.CalledProcessError) as exc:
        run['errors'].append(str(exc))
    return run


def invalidate(run, reason):
    run['valid'] = False
    run['errors'].append(reason)


def classification(path):
    try:
        c = json.loads((path / 'classification.json').read_bytes())
    except FileNotFoundError:
        raise ValueError('missing classification')
    require(c['class'] in ('infra', 'impl', 'unclassified'), 'invalid classification class')
    require(isinstance(c['reason'], str) and c['reason'].strip(), 'invalid classification reason')
    require(c['class'] == 'infra', 'classification: ' + c['class'])
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


# Append-only by launcher convention, not tamper-proof storage. Never rebuild
# this log from surviving runs: that would erase evidence of missing submissions.
SUBMISSION_LIMIT = '投入台帳は launcher が追記専用で扱う通常ファイル。台帳自身の改竄・削除（RUN と同時の削除を含む）や外部の同時変更は防げない。追記後の異常終了は自動修復せず拒否する。'
MEDIAN_NOTE = '条件別・shard 別中央値は有効対の採用走が対象。偶数個のときは中央 2 値の算術平均、対象 0 件は欠測 (null)。'


def read_submissions(root, paths=None):
    log = root / 'submissions.log'
    entries = []
    try:
        actual = {p.name for p in (root / 'runs').iterdir()} if (root / 'runs').exists() else set()
        if log.exists():
            for line in log.read_text().splitlines():
                entry = json.loads(line)
                require(isinstance(entry, dict), 'entry must be an object')
                nn, cond, slot, tag = (entry[k] for k in ('run', 'condition', 'pair_slot', 'tag'))
                require(isinstance(nn, str) and re.fullmatch(r'[0-9]{2}', nn)
                        and cond in ('A', 'B') and type(slot) is int and slot in (1, 2, 3)
                        and tag == f'{nn}-{cond}', 'invalid submission identity')
                require(not entries or int(nn) > int(entries[-1]['run']), 'nonmonotonic submission numbers')
                path = root / 'runs' / tag
                require(path.is_dir(), 'missing run directory: ' + tag)
                metadata = json.loads((path / 'run.json').read_bytes())
                require(all(metadata[k] == entry[k] and type(metadata[k]) is type(entry[k])
                            for k in ('tag', 'run', 'condition', 'pair_slot')), 'run identity mismatch: ' + tag)
                entries.append(entry)
        require(actual == {e['tag'] for e in entries}, 'runs/log membership mismatch (missing ledger or unlogged run)')
        if paths is not None:
            require({p.resolve() for p in paths} == {(root/'runs'/e['tag']).resolve() for e in entries},
                    'analysis paths differ from submission ledger')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('submission history: ' + str(exc)) from exc
    return entries


def check_number(entries, number):
    require(not entries or int(number) > max(int(e['run']) for e in entries),
            'run number must exceed every prior submission; not submitted')


def append_submission(root, number, condition, slot):
    # Caller must hold measure.lock through this append, mkdir and measurement.
    entries = read_submissions(root)
    check_number(entries, number)
    entry = dict(tag=f'{number}-{condition}', run=number, condition=condition, pair_slot=slot)
    with (root/'submissions.log').open('a') as stream:
        stream.write(json.dumps(entry, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def analyze(paths, collection, tips, warm_root=None, added_node=E1_ADDED_NODE):
    paths = list(paths)
    series_errors = warm_errors(warm_root or JOB, tips)
    try:
        read_submissions(warm_root or JOB, paths)
    except ValueError as exc:
        series_errors.append(str(exc))
    paths = sorted(paths, key=lambda p: p.name)
    runs = []
    for path in paths:
        condition = path.name.rsplit('-', 1)[-1]
        condition_collection = collection.parent / f'login-collection-{condition}.log'
        # A's original preflight collection may be shared by legacy series.
        # B has its own login collection because E1 adds one node.
        baseline = (condition_collection if condition_collection.is_file() else
                    collection if (condition == 'A' or not added_node) and collection.is_file() else
                    path / 'session/login-collection.log')
        runs.append(read_run(path, baseline, tips))
    for condition in 'AB':
        same_condition = [r for r in runs if r['valid'] and r['metadata']['condition'] == condition]
        if same_condition:
            reference = same_condition[0]
            for run in same_condition[1:]:
                if (Counter(run['collection_nodes']) != Counter(reference['collection_nodes']) or
                    any(Counter(x['selected_nodes']) != Counter(y['selected_nodes'])
                        for x, y in zip(run['shards'], reference['shards']))):
                    invalidate(run, f'E1 {condition} runs collection/selected differ from {reference["tag"]}')
                    series_errors.append(f'{run["tag"]}: {run["errors"][-1]}')
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
                         set(group[0]['skipped_nodes']) == set(group[1]['skipped_nodes']))
        e1_ok, e1_reasons, added_shards = False, [], []
        if len(group) == 2 and all(r['valid'] for r in group):
            a, b = sorted(group, key=lambda r: r['metadata']['condition'])
            e1_ok, e1_reasons, added_shards = e1_pair_check(a, b, added_node)
        valid = order_ok and all(r['valid'] for r in group) and skipped_match and e1_ok
        p = {'pair_slot': slot, 'attempt': attempts[slot], 'runs': [r['tag'] for r in group],
             'valid': valid, 'skipped_match': skipped_match,
             'e1_reasons': e1_reasons, 'B_added_node_shards': added_shards}
        if valid:
            a, b = sorted(group, key=lambda r: r['metadata']['condition'])
            p.update(pair_metrics(a, b))
            slot += 1
        elif not order_ok:
            p['reason'] = 'incomplete/nonadjacent pair, wrong slot/order, or half reuse'
        elif not all(r['valid'] for r in group):
            p['reason'] = 'invalid run in adjacent pair'
        else:
            p['reason'] = 'skipped nodes differ within pair' if not skipped_match else '; '.join(e1_reasons)
            series_errors.append(f"pair {slot}/{attempts[slot]}: {p['reason']}")
        pairs.append(p)
        if grammar_errors:
            break
    for path, run in zip(paths, runs):
        if not run['valid'] or run.get('red') or (path / 'classification.json').exists():
            try:
                if (path / 'classification.json').exists():
                    run['classification'] = json.loads((path / 'classification.json').read_bytes())
                run['classification'] = classification(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                series_errors.append(str(exc))
    if len(runs) > 12:
        series_errors.append('total runs exceeds 12')
    valid = [p for p in pairs if p['valid']]
    summary = aggregate(valid)
    if series_errors or len(valid) < 3:
        land = 'undetermined'
        reasons = list(dict.fromkeys(series_errors)) or [f'valid pairs {len(valid)}/3']
    else:
        reasons = []
        if not all(p['delta_W_0'] > 0 for p in valid):
            reasons.append('not all three pair deltas are positive')
        if summary['median_pair_rate'] < .10:
            reasons.append('median pair rate below 10%')
        land = 'not-met' if reasons else 'met'
    b_wmax = [p['W_max_B'] for p in valid]
    five = ('undetermined' if series_errors or len(valid) < 3 else
            'met' if median(b_wmax) <= 300 else 'not-met')
    return {'runs': runs, 'pairs': pairs, 'total_runs': len(runs),
            'valid_pairs': len(valid), 'series_invalid': list(dict.fromkeys(series_errors)),
            'W_0': summary, 'land_condition': land, 'land_reasons': reasons,
            'five_minute_goal': {'status': five,
                                 'median_B_W_max_s': median(b_wmax) if b_wmax else None,
                                 'threshold_s': 300},
            'submission_limitations': SUBMISSION_LIMIT,
            'condition_summaries': condition_summaries(runs, valid)}


def condition_summaries(runs, valid_pairs):
    adopted = {tag for pair in valid_pairs for tag in pair['runs']}
    result = {}
    for condition in 'AB':
        selected = [r for r in runs if r['tag'] in adopted and
                    r['metadata']['condition'] == condition]
        result[condition] = {
            'runs': [r['tag'] for r in selected],
            'run_numbers': [r['metadata']['run'] for r in selected],
            'valid_runs': len(selected),
            'shards': [{'shard': j, **{
                k: median(r['shards'][j][k] for r in selected) if selected else None
                for k in ('W', 'O', 'L', 'F', 'pre', 'post')}} for j in range(3)]}
    return result


def next_allowed(result):
    if result['series_invalid'] or result['valid_pairs'] == 3 or result['total_runs'] >= 12:
        return None
    slot = result['valid_pairs'] + 1
    order = ('B', 'A') if slot == 2 else ('A', 'B')
    if result['pairs']:
        last = result['pairs'][-1]
        if len(last['runs']) == 1 and result['runs'][-1]['valid']:
            return order[1], slot
    return order[0], slot


def check_request(result, condition, slot):
    expected = next_allowed(result)
    require(expected is not None, 'fixed stop, cap, or invalid series')
    require((condition, slot) == expected,
            f'request {(condition, slot)} != next allowed {expected}; not submitted')


def table(headers, rows):
    def cell(x):
        if isinstance(x, float):
            return f'{x:.3f}'
        return str(x if x is not None else '—').replace('|', '\\|').replace('\n', '<br>')
    return ['|'+'|'.join(headers)+'|', '|'+'|'.join(['---']*len(headers))+'|',
            *('|'+'|'.join(cell(x) for x in row)+'|' for row in rows), '']


def markdown(result):
    lines = ['# T-2273 A/B measurement', '',
             f"land_condition: {result['land_condition']}; reasons: {result['land_reasons']}",
             f"five_minute_goal: {result['five_minute_goal']}", '',
             f"有効対: {result['valid_pairs']}/3; series_invalid: {result['series_invalid']}", '',
             f"対差中央値: {result['W_0']['median_delta_s']} 秒; 対率中央値: {result['W_0']['median_pair_rate']}", '']
    lines += table(['slot/attempt', 'runs', 'valid', 'W_0 A', 'W_0 B', 'Δi', 'ri',
                    'B 追加 node shard', 'E1 理由'],
                   [[f"{p['pair_slot']}/{p['attempt']}", ', '.join(p['runs']), p['valid'],
                     p.get('W_0_A'), p.get('W_0_B'), p.get('delta_W_0'), p.get('r'),
                     p.get('B_added_node_shards'), p.get('e1_reasons')]
                    for p in result['pairs']])
    lines += table(['run','valid','W_0','W_1','W_2','W_max','argmax','O_max',
                    'O worker/items', 'L', 'L worker/nodeid','O_max−L','pre','post'],
                   [[r['tag'],r['valid'],
                     *([s['W'] for s in r['shards']] if r.get('shards') else [None]*3),
                     r.get('W_max'),r.get('W_max_argmax'),
                     r['shards'][0]['O'] if r.get('shards') else None,
                     (f"{r['shards'][0]['busiest_worker']}/{r['shards'][0]['worker_counts'].get(r['shards'][0]['busiest_worker'], 0)}"
                      if r.get('shards') else None),
                     r['shards'][0]['L'] if r.get('shards') else None,
                     (f"{r['shards'][0]['longest']['worker']}/{r['shards'][0]['longest']['nodeid']}"
                      if r.get('shards') else None),
                     r['shards'][0]['O_minus_L'] if r.get('shards') else None,
                     r['shards'][0]['pre'] if r.get('shards') else None,
                     r['shards'][0]['post'] if r.get('shards') else None]
                    for r in result['runs']])
    for r in result['runs']:
        lines += [f"## {r['tag']}", '', f"valid={r['valid']}; errors={r['errors']}", '']
        if r.get('shards'):
            s = r['shards'][0]
            lines += [f"O_max={s['O']}; L={s['L']}; O_max−L={s['O_minus_L']}", '',
                      f"最大占有 worker {s['busiest_worker']} の item 列", '']
            lines += table(['nodeid','time','rank','worker_order'],
                           [[x[k] for k in ('nodeid','time','rank','worker_order')]
                            for x in s['worker_items'][s['busiest_worker']]])
    lines += ['## 限界', '', '固定 2 tree は同一 node・同一 allocation ではない。同時刻性は隣接逐次投入による。',
              result['submission_limitations'], '']
    return '\n'.join(lines)


def write_analysis(result, out):
    out.mkdir(parents=True, exist_ok=True)
    (out/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    (out/'analysis.md').write_text(markdown(result))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job',type=Path,default=JOB)
    for option in ('runs-root','tips','collection','out'):
        p.add_argument('--'+option,type=Path)
    args=p.parse_args()
    tip_path=args.tips or args.job/'measurement-tips.json'
    tips=json.loads(tip_path.read_bytes())
    for c in 'AB':
        require(re.fullmatch('[0-9a-f]{40}',tips[c]['sha']) and Path(tips[c]['worktree']).is_absolute(),'invalid tips')
    root=args.runs_root or args.job/'runs'
    paths=[d for d in root.iterdir() if d.is_dir()] if root.exists() else []
    result=analyze(paths,args.collection or args.job/'input/login-collection.log',tips,warm_root=tip_path.parent)
    write_analysis(result,args.out or args.job/'analysis')
    print(result['land_condition'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        sys.exit(2)
````
