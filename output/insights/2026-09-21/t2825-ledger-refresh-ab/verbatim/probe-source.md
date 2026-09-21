# [T-2825] 測定 probe・変異 spec 生成器・台帳検算 script の逐語

job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/`) に置いて走らせた実物の逐語。repo には入れない (実装面、D95 決定 2)。
著者は各節の見出しのとおり (Codex role=author)。親が書いた運転 script (detach / launch / switch / run-mutation / make-mutation-source) は測定の意味に関わらないので載せない。

## run-measure.sh (sha256 `11fec2dc41c6195affd5d0457d92b7afc433563e0620e8f4786a56711ad94890`, 10369 byte、Codex author (単位 P) + fix1 + fix2)

````bash
#!/bin/bash
# T-2825 sequential, pinned-tree acceptance measurement.
set -uo pipefail
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab
JOBDIR=$J
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SLUG=dev-wave-t2825-ledger-refresh-ab
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
source "$SCRIPT_DIR/gate.conf" || exit 2
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
from t2825_ab_analyze import analyze, check_request, read_submissions, check_number
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
  source "$SCRIPT_DIR/gate.conf" || abort 2 "gate.conf unavailable"
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
  if [ "$(cat "$JOBDIR/aborts/$TAG-$STAMP.diff.stat")" != "orchestrator/tests/acceptance_duration_ledger.json" ]; then abort 95 "tracked diff is not exactly the ledger"; fi
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
from t2825_ab_analyze import append_submission
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

## run-series.sh (sha256 `87a2c1f05c08fd77041d6feb3b587e4cea85561a85d5be2c03c458248286a8fa`, 2799 byte、同上)

````bash
#!/bin/bash
# usage: run-series.sh <spec...>; spec is "NN X slot".
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab
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
  python3 - "$J" "$SCRIPT_DIR" "$1" "$2" "$3" <<'PREFLIGHT'
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
from t2825_ab_analyze import classification, warm_errors, analyze, check_request, read_submissions, check_number
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
````

## run-warm.sh (sha256 `b646f9f3d26054b7bcb315557fe44b4dad393e634d986238f554338a0a6af930`, 3780 byte、同上)

````bash
#!/bin/bash
# usage: run-warm.sh <A|B>
set -uo pipefail
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab
if [ "$#" -ne 1 ] || [[ ! "$1" =~ ^[AB]$ ]]; then
  echo 'usage: run-warm.sh <A|B>' >&2; exit 2
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

## gate.conf (sha256 `8478d7c6b941a2881ab5ee5736eba42dae8cc00ad8a75e53c4aadf6224a67116`, 91 byte、同上)

````bash
LEADERS_MAX=1
L1_MAX=60
GATE_MAX_ROUNDS=120
PERIOD_MIN=100
PERIOD_WIDTH=41
JITTER_WIDTH=46
````

## t2825_ab_analyze.py (sha256 `1491c5b54ea827528432d17c51e78792fd8b8d69f31376f0c2ec14e3ab0d0ace`, 58914 byte、同上)

````python
#!/usr/bin/env python3
"""T-2825 preregistered W_0 analysis; offline, standard library only."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
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

JOB = Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab')
LEDGER = 'orchestrator/tests/acceptance_duration_ledger.json'
PREFIX = 'izanagi_acceptance_pairing_v1_'
OLD_L = 'test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5'
ESTIMATE_NOTE = '推定開始は worker の first_test_started_epoch_s + 同 worker の JUnit 順先行 time 累積。item 間の空白は未観測。'


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


def measurement_ledger_bytes(tip):
    require(re.fullmatch('[0-9a-f]{40}', tip['sha']), 'invalid ledger SHA')
    return subprocess.check_output(['git', '-C', tip['worktree'], 'show',
                                    tip['sha'] + ':' + LEDGER])


def ledger_provenance(tip):
    raw = measurement_ledger_bytes(tip)
    ledger = json.loads(raw)['duration_seconds_by_nodeid']
    require(isinstance(ledger, dict), 'invalid ledger shape')
    measured = hashlib.sha256(raw).hexdigest()
    try:
        current = hashlib.sha256((Path(tip['worktree']) / LEDGER).read_bytes()).hexdigest()
        warning = 'measurement/worktree ledger hash mismatch' if current != measured else None
    except OSError as exc:
        current, warning = None, 'worktree ledger unavailable: ' + str(exc)
    return ledger, {'measurement_ledger_sha256': measured,
                    'worktree_ledger_sha256': current, 'ledger_warning': warning,
                    'measurement_ledger_source': tip['sha'] + ':' + LEDGER}


def ledger_cost(ledger, nodeid, group):
    duration = ledger.get(nodeid)
    if duration is None and group is not None:
        duration = ledger.get(f'{nodeid}@{group}')
    return (1.0, True) if duration is None else (finite(duration), False)


def parse_session(session, collection, ledger):
    hashes = verify_hashes(session)
    baseline = collection_nodes(collection)
    require(collection_nodes(session / 'login-collection.log') == baseline, 'login collection mismatch')
    all_nodes, skipped, shards, all_rows = Counter(), [], [], []
    for j in range(3):
        shard = session / f'shard-{j}'
        report = json.loads((shard / 'report.json').read_bytes())
        require(report['shard_index'] == j and report['shard_count'] == 3, 'report shard mismatch')
        require(report['pytest_rc'] == 0 and not report['failures'], 'report red')
        selected = report['selected']
        require(Counter(report['finished']) == Counter(selected), 'shard incomplete')
        require(Counter(x['nodeid'] for x in report['observed_universe']) == baseline, 'observed universe mismatch')
        groups = {x['nodeid']: x['group'] for x in report['observed_universe']}
        costs = [ledger_cost(ledger, node, groups[node]) for node in selected]
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
        all_rows.extend(rows)
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
                       'selected_sha256': hashlib.sha256(('\n'.join(sorted(selected))+'\n').encode()).hexdigest(),
                       'ledger_predicted_load': sum(cost for cost, missing in costs),
                       'ledger_missing_count': sum(missing for cost, missing in costs),
                       'worker_counts': {w: len(v) for w,v in by_worker.items()},
                       'worker_items': {w: by_worker[w] for w in sorted(full_workers)},
                       'dispatch': dispatch, 'requests': requests})
    require(all_nodes == baseline, 'global JUnit collection mismatch')
    maximum = max(s['W'] for s in shards)
    targets = [x for x in all_rows if 'test_s8b_oracle_driver.py::' in x['nodeid'] and
               any(t in x['nodeid'] for t in ('active_v2','v1_gate_does_not_delegate','failed_launch_preserves',
                                             'delegated_campaign_start','shared_base_separates'))]
    return {'shards': shards, 'skipped_nodes': sorted(skipped), 'W_0': shards[0]['W'], 'W_max': maximum,
            'W_max_argmax': [s['shard'] for s in shards if s['W'] == maximum],
            'T2724': targets, 'old_L_candidates': [x for x in all_rows if OLD_L in x['nodeid']],
            'node_times': {x['nodeid']: x['time'] for x in all_rows},
            'node_shards': {x['nodeid']: x['shard'] for x in all_rows}, 'artifact_sha256': hashes,
            'collection_check': 'login and forward-projected JUnit multisets match input'}


def pair_metrics(a, b):
    a0, b0 = a['shards'][0], b['shards'][0]
    delta = a['W_0'] - b['W_0']
    moves = defaultdict(list)
    for node, source in a['node_shards'].items():
        dest = b['node_shards'][node]
        if source != dest:
            moves[f'{source}->{dest}'].append({'nodeid': node, 'time_A': a['node_times'][node], 'time_B': b['node_times'][node]})
    dL, dgap = b0['L']-a0['L'], b0['O_minus_L']-a0['O_minus_L']
    return {'W_0_A': a['W_0'], 'W_0_B': b['W_0'], 'delta_W_0': delta, 'r': delta/a['W_0'],
            'D357': '1 走比較として変化なし' if abs(delta/a['W_0']) < .1 else '',
            'delta_O_0': b0['O']-a0['O'], 'delta_L_0': dL, 'delta_gap_0': dgap,
            'relative_L_growth': dL/a0['L'] if a0['L'] else 0,
            'L_nodeid_A': a0['longest']['nodeid'], 'L_nodeid_B': b0['longest']['nodeid'],
            'L_node_changed': a0['longest']['nodeid'] != b0['longest']['nodeid'],
            'gap_note': 'L 増大を伴う差の縮小' if dL > 0 and dgap < 0 else '',
            'old_L_A': a['old_L_candidates'], 'old_L_B': b['old_L_candidates'],
            'W_max_A': a['W_max'], 'W_max_B': b['W_max'], 'delta_W_max': a['W_max']-b['W_max'],
            'shard_moves': {d: {'count': len(v), 'time_A_sum': sum(x['time_A'] for x in v),
                                'time_B_sum': sum(x['time_B'] for x in v), 'nodes': v} for d,v in moves.items()}}


def aggregate(pairs, metric):
    ds = [p['delta_'+metric] for p in pairs]
    rs = [p['delta_'+metric]/p[metric+'_A'] for p in pairs]
    result = {'median_delta': median(ds) if ds else None, 'median_r': median(rs) if rs else None,
              'difference_of_condition_medians': (median(p[metric+'_A'] for p in pairs)-median(p[metric+'_B'] for p in pairs)) if pairs else None,
              'branch': None, 'subclassification': None, 'decision': '判定不能 (反復不足)'}
    if len(pairs) != 3:
        return result
    if all(d > 0 for d in ds):
        result.update(branch='(i)' if median(rs) >= .1 else '(ii)',
                      decision='方向一致・閾値以上' if median(rs) >= .1 else '方向一致・閾値未満')
    else:
        sub = '退行の観測' if all(d < 0 for d in ds) else '0 を含む' if any(d == 0 for d in ds) else '符号混在'
        result.update(branch='(iii)', decision='効果未確立', subclassification=sub)
    return result


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
        require((path / 'tracked-diff.stat').read_text().splitlines() == [LEDGER], 'tracked diff not exactly ledger')
        ledger, provenance = ledger_provenance(tip)
        run.update(provenance)
        run.update(parse_session(path / 'session', collection, ledger))
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


def analyze(paths, collection, tips, warm_root=None):
    paths = list(paths)
    series_errors = warm_errors(warm_root or JOB, tips)
    try:
        read_submissions(warm_root or JOB, paths)
    except ValueError as exc:
        series_errors.append(str(exc))
    paths = sorted(paths, key=lambda p: p.name)
    ledger_hashes = {}
    for condition in 'AB':
        try:
            _, ledger_hashes[condition] = ledger_provenance(tips[condition])
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            series_errors.append(f'ledger-{condition}: {exc}')
    runs = [read_run(p, collection, tips) for p in paths]
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
        if run.get('red') or (path / 'classification.json').exists():
            try:
                if (path / 'classification.json').exists():
                    run['classification'] = json.loads((path / 'classification.json').read_bytes())
                run['classification'] = classification(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                series_errors.append(str(exc))
    if len(runs) > 12:
        series_errors.append('total runs exceeds 12')
    valid = [p for p in pairs if p['valid']]
    primary = aggregate(valid, 'W_0')
    auxiliary = aggregate(valid, 'W_max')
    if series_errors:
        for summary in (primary, auxiliary):
            summary.update(branch=None, decision='series-invalid', subclassification=None)
    growth = (len(valid) == 3 and all(p['delta_L_0'] > 0 for p in valid)
              and median(p['relative_L_growth'] for p in valid) >= .1)
    notes = []
    if primary['branch'] == '(i)' and auxiliary['branch'] != '(i)':
        notes.append('shard-0 の短縮であって受入全体の短縮とは言わない')
    return {'runs': runs, 'pairs': pairs, 'total_runs': len(runs), 'over_12_runs': len(runs) > 12,
            'valid_pairs': len(valid), 'series_invalid': list(dict.fromkeys(series_errors)),
            'ledger_provenance_by_condition': ledger_hashes,
            'decision': 'series-invalid' if series_errors else primary['decision'],
            'W_0': primary, 'W_max_auxiliary': auxiliary,
            'L_observation': ('判定不能' if len(valid) != 3 or series_errors else
                              'L の伸長を観測' if growth else '事前登録した L 伸長の判定条件を満たさない'),
            'notes': notes, 'estimate_note': ESTIMATE_NOTE,
            'submission_limitations': SUBMISSION_LIMIT, 'median_definition': MEDIAN_NOTE,
            'reference_only': {'model_difference_s': 19.5, 'model_source': 'T-2817 §5 (a): 未収載333 node 全部更新の固定所要 model',
                               'observed_gap_median_s': 62.7, 'observed_source': 'T-2817: 21 session の O_max − L 中央値',
                               'job_B_gap_s': 65.0, 'job_B_source': 'T-2817 Job B',
                               'usage': '参考のみ。判定の閾値・上下限・期待値に使わない'},
            'red_counts_by_condition': {c: sum(r.get('red', False) and r.get('metadata', {}).get('condition') == c for r in runs) for c in 'AB'},
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
    lines = ['# T-2825 A/B measurement', '', result['decision'], '',
             'ΔW = A−B、ΔO / ΔL / Δ(O−L) = B−A。L の観測規則は shard-0 に適用。', '',
             result['estimate_note'], '',
             '10% は事前登録の保守基準で D357 からの導出ではない。3/3 一致は有意差ではない。', '']
    lines += table(['量','分岐','判定','副分類','med Δ','med r','条件別中央値差'],
                   [[name, result[k]['branch'], result[k]['decision'], result[k]['subclassification'],
                     result[k]['median_delta'], result[k]['median_r'], result[k]['difference_of_condition_medians']]
                    for name,k in [('W_0 一次','W_0'),('W_max 補助','W_max_auxiliary')]])
    lines += [result['L_observation'], '', *result['notes'], '',
              'series_invalid: ' + '; '.join(result['series_invalid']), '',
              f"有効対={result['valid_pairs']}; 投入={result['total_runs']}/12", '']
    lines += table(['条件', '測定台帳 hash', '集計時の worktree の台帳 hash', '警告'],
                   [[c, v['measurement_ledger_sha256'], v['worktree_ledger_sha256'], v['ledger_warning']]
                    for c, v in result['ledger_provenance_by_condition'].items()])
    lines += table(['条件', '対象走番号', 'shard', 'med W', 'med O', 'med L', 'med F', 'med pre', 'med post'],
                   [[c, ', '.join(v['run_numbers']), s['shard'],
                     *[s[k] for k in ('W','O','L','F','pre','post')]]
                    for c,v in result['condition_summaries'].items() for s in v['shards']])
    lines += ['脚注: ' + result['median_definition'], '']
    lines += table(['slot/attempt','runs','valid','W0 A','W0 B','ΔW','r','D357','ΔO0','ΔL0','Δ(O0−L0)','Wmax A','Wmax B'],
                   [[f"{p['pair_slot']}/{p['attempt']}", ', '.join(p['runs']), p['valid'],
                     *[p.get(k) for k in ('W_0_A','W_0_B','delta_W_0','r','D357','delta_O_0','delta_L_0','delta_gap_0','W_max_A','W_max_B')]]
                    for p in result['pairs']])
    for p in result['pairs']:
        lines += [f"対 {p['pair_slot']}/{p['attempt']}: {p.get('reason','')} {p.get('gap_note','')}", '']
        if p['valid']:
            lines += [f"L 交代={p['L_node_changed']}: {p['L_nodeid_A']} → {p['L_nodeid_B']}", '']
            lines += table(['移動 A→B','件数','time A 和','time B 和'],
                           [[d,v['count'],v['time_A_sum'],v['time_B_sum']] for d,v in p['shard_moves'].items()])
    item_fields = ['nodeid','shard','worker','rank','partner','time','junit_order','estimated_start_offset_s','estimated_start_epoch_s']
    for r in result['runs']:
        m = r.get('metadata', {})
        lines += [f"## {r['tag']} ({m.get('condition')})", '',
                  f"valid={r['valid']}; errors={r['errors']}; 測定台帳 hash={r.get('measurement_ledger_sha256')}; 集計時の worktree の台帳 hash={r.get('worktree_ledger_sha256')}; 警告={r.get('ledger_warning')}", '',
                  f"投入={m.get('submitted_at')}; 完了={m.get('finished_at')}; leader={m.get('other_leaders')}; load1={m.get('load1')}", '',
                  f"W_max={r.get('W_max')}; argmax={r.get('W_max_argmax')}" +
                  ('; shard-0 以外が argmax' if any(j != 0 for j in r.get('W_max_argmax',[])) else ''), '']
        lines += table(['shard','W','O','L','O−L','F','pre','post','O worker','L worker','P_L','node','job ID'],
                       [[s['shard'], *[s[k] for k in ('W','O','L','O_minus_L','F','pre','post','busiest_worker')],
                         s['longest']['worker'],s['P_L'],s['hostname'],','.join(str(d['job_id']) for d in s['dispatch'])] for s in r.get('shards',[])])
        lines += table(['shard','selected count','selected sha256','台帳予測負荷','未登録','worker/item 件数'],
                       [[s['shard'],s['selected_count'],s['selected_sha256'],s['ledger_predicted_load'],s['ledger_missing_count'],
                         ', '.join(f'{w}:{n}' for w,n in s['worker_counts'].items())] for s in r.get('shards',[])])
        lines += table(['shard','L nodeid','L rank','L partner','O_L'],
                       [[s['shard'],s['longest']['nodeid'],s['longest']['rank'],s['longest']['partner'],s['O_L']] for s in r.get('shards',[])])
        for s in r.get('shards',[]):
            for w, items in s['worker_items'].items():
                lines += [f"shard-{s['shard']} worker {w} 全 item (JUnit 順)", '']
                lines += table(item_fields, [[x[k] for k in item_fields] for x in items])
        for title,key in [('T-2724','T2724'),('固定した旧 L 候補 (全 parametrize)','old_L_candidates')]:
            lines += [title, ''] + table(item_fields, [[x[k] for k in item_fields] for x in r.get(key,[])])
    lines += ['## 赤', '', '条件別赤走数: '+str(result['red_counts_by_condition']), '',
              '全赤の testcase 本文・child log・分類は analysis.json の runs に保存。', '',
              '## 参考値 (判定に使わない)', '']
    lines += table(['量','秒','出所'], [['model 差',19.5,result['reference_only']['model_source']],
                 ['O_max−L 中央値',62.7,result['reference_only']['observed_source']],['Job B',65.0,result['reference_only']['job_B_source']]])
    lines += ['## 限界', '', result['submission_limitations'], '', '別 tree / node / page cache の差は残る。入力 1 走の190秒群・40秒群がBの順位を決める。',
              'copy 配置・builder/waiter の因果や役割は所要だけでは断定しない。', '']
    return '\n'.join(lines)


def write_analysis(result, out):
    out.mkdir(parents=True, exist_ok=True)
    # Full per-node maps are transient inputs to movement accounting, not repeated output.
    compact = dict(result, runs=[{k:v for k,v in r.items() if k not in ('node_times','node_shards')}
                                 for r in result['runs']])
    (out/'analysis.json').write_text(json.dumps(compact, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    (out/'analysis.md').write_text(markdown(result))


def fixture_job(root):
    tips = {c: {'sha': c.lower()*40, 'worktree': str(root/('tree-'+c))} for c in 'AB'}
    for c,t in tips.items():
        p = Path(t['worktree'])/LEDGER
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'duration_seconds_by_nodeid': {}}))
        (root/f'warm-{c}.json').write_text(json.dumps(dict(
            condition=c, worktree=t['worktree'], sha=t['sha'], head_before=t['sha'], head_after=t['sha'],
            clean_before=True, clean_after=True, rc=0, dispatch_request='[Pegasus dispatch] request ID fixture',
            PYTHONDONTWRITEBYTECODE='', pyc_before=0, pyc_after=3,
            started_at='2026-09-19T00:00:00+00:00', finished_at='2026-09-19T00:01:00+00:00')))
    (root/'measurement-tips.json').write_text(json.dumps(tips))
    return tips


def fixture_run(root, tips, number, condition, slot):
    path = root/'runs'/f'{number:02d}-{condition}'
    (root/'runs').mkdir(exist_ok=True)
    append_submission(root, f'{number:02d}', condition, slot)
    path.mkdir(parents=True)
    sha = tips[condition]['sha']
    diff = LEDGER+'\n'
    env = {'IZANAGI_ACCEPTANCE_SHARDS':'3', 'PYTHONDONTWRITEBYTECODE_SET':'no'}
    m = dict(tag=path.name, run=f'{number:02d}', condition=condition, pair_slot=slot, rc=0, copy_ok=True,
             dirty_lines_before=0, dirty_lines_after=0, valid_tree=True,
             expected_sha=sha, measurement_tip=sha, tip_sha=sha, tip_sha_after=sha,
             condition_worktree=tips[condition]['worktree'],
             submitted_at=f'2026-09-20T{number:02d}:00:00+00:00', finished_at=f'2026-09-20T{number:02d}:30:00+00:00',
             tracked_diff_stat_sha256=hashlib.sha256(diff.encode()).hexdigest(),
             env=env, other_leaders=1, load1=60, gate={'leaders_max':1,'load1_max_inclusive':60})
    (path/'run.json').write_text(json.dumps(m))
    (path/'tracked-diff.stat').write_text(diff)
    (path/'measure.done').write_text('0\n')
    (path/'env.txt').write_text(''.join(f'{k}={v}\n' for k,v in env.items()))
    (path/'gate.log').write_text('2026-09-20T00:00:00+0000 gate: load1=60 leaders=1 (max 1, l1 <= 60)\n'*4)
    return path


def rehash(session):
    (session/'SHA256SUMS').write_text(''.join(
        f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(session)}\n'
        for p in sorted(session.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))


def fixture_session(path, W=100, L=40, O=60, other_W=70):
    session = path/'session'
    session.mkdir()
    nodes = [f'orchestrator/tests/test_s8b_oracle_driver.py::{OLD_L}[a.b@x]',
             'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt',
             'orchestrator/tests/test_example.py::TestClass::test_method[param.a]',
             'orchestrator/tests/test_other.py::test_one']
    (session/'login-collection.log').write_text('\n'.join(nodes)+'\n')
    top = ET.Element('testsuites')
    for j,selected in enumerate([nodes[:2],nodes[2:3],nodes[3:]]):
        shard = session/f'shard-{j}'
        shard.mkdir()
        times = [L, O-L] if j == 0 else [10]
        wall = W if j == 0 else other_W
        suite = ET.Element('testsuite', name='pytest', tests=str(len(selected)), errors='0', failures='0', skipped='0',
                           time=str(wall), timestamp='2026-09-20T00:00:00+00:00', hostname='fixture-node')
        for i,(node,t) in enumerate(zip(selected,times)):
            cls,name = junit_key(node)
            case = ET.SubElement(suite,'testcase',classname=cls,name=name+'@real-repo',time=str(t))
            props = ET.SubElement(case,'properties')
            for k,v in dict(scope='real-repo',rank=456+i,partner=1-i if j==0 else 0,worker='gw33').items():
                ET.SubElement(props,'property',name=PREFIX+k,value=str(v))
        top.append(suite)
        wrapper = ET.Element('testsuites'); wrapper.append(suite)
        (shard/'junit.xml').write_bytes(ET.tostring(wrapper))
        t0 = timestamp(suite.get('timestamp')).timestamp()
        report = dict(schema_version='izanagi-acceptance-shard-report/v1', shard_index=j, shard_count=3,
                      pytest_rc=0, failures=[], selected=selected, finished=selected,
                      observed_universe=[{'nodeid':n,'file':n.split('::')[0],'group':None} for n in nodes],
                      worker_occupancy={'gw33':{'duration_s':sum(times),'items':len(times)}},
                      session_timeline={'collection_finished_epoch_s':t0+2, 'workers':{'gw33':{
                          'first_test_started_epoch_s':t0+3,'last_test_finished_epoch_s':t0+3+sum(times),'real_repo_lock_intervals':[]}}})
        (shard/'report.json').write_text(json.dumps(report))
        dispatch = shard/'dispatch'/f'shard-{j}'
        dispatch.mkdir(parents=True)
        (dispatch/'request.json').write_text(json.dumps({'schema_version':'pegasus-dispatch-request/v2','task':'tests','args':[], 'runner_binding':{'shard_count':3,'shard_index':j}}))
        (dispatch/'receipt.json').write_text(json.dumps({'f49_compute_marker':{'hostname':'fixture-node','pbs_jobid':'0:1.nqsv'}}))
    (session/'junit.xml').write_bytes(ET.tostring(top))
    rehash(session)
    collection = path.parents[1]/'input/login-collection.log'
    collection.parent.mkdir(exist_ok=True)
    if not collection.exists():
        collection.write_text('\n'.join(nodes)+'\n')
    return session


def selftest():
    import tempfile
    from unittest.mock import patch
    normal = [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]
    def scenario(specs=normal, B_W=80, B_L=40, B_O=60, other_W=70, mutate=None):
        with tempfile.TemporaryDirectory(prefix='t2825-selftest-') as temp:
            root = Path(temp)
            tips = fixture_job(root)
            pinned = {t['sha']: (Path(t['worktree'])/LEDGER).read_bytes() for t in tips.values()}
            paths = []
            for i,(c,slot) in enumerate(specs,1):
                p = fixture_run(root,tips,i,c,slot)
                fixture_session(p,W=100 if c=='A' else B_W,L=40 if c=='A' else B_L,
                                O=60 if c=='A' else B_O,other_W=other_W)
                paths.append(p)
            if mutate:
                mutate(root,paths)
            def git_show(command):
                tip = next(t for t in tips.values() if t['worktree'] == command[2])
                require(command == ['git', '-C', tip['worktree'], 'show', tip['sha']+':'+LEDGER],
                        'ledger read must use pinned SHA:path')
                return pinned[tip['sha']]
            with patch(__name__ + '.subprocess.check_output', side_effect=git_show):
                result = analyze(paths,root/'input/login-collection.log',tips,warm_root=root)
            write_analysis(result,root/'analysis')
            require((root/'analysis/analysis.json').is_file(), 'JSON output')
            return result
    for bw,branch in [(80,'(i)'),(95,'(ii)'),(110,'(iii)'),(100,'(iii)'),(90,'(i)')]:
        r = scenario(B_W=bw)
        require(r['valid_pairs']==3 and not r['series_invalid'] and r['W_0']['branch']==branch, str(r['series_invalid'])+str(r['runs'][0]['errors']))
    require(scenario(B_W=110)['W_0']['subclassification']=='退行の観測','regression subclass')
    require(scenario(B_W=100)['W_0']['subclassification']=='0 を含む','zero subclass')
    r = scenario()
    rows = r['runs'][0]['shards'][0]['worker_items']['gw33']
    require(rows[1]['estimated_start_offset_s']==40 and rows[1]['estimated_start_epoch_s']-rows[0]['estimated_start_epoch_s']==40,'cumulative estimate')
    require(len(r['runs'][0]['old_L_candidates'])==1 and r['pairs'][0]['old_L_A'],'old L')
    require(r['runs'][0]['T2724'][0]['rank']==457,'T2724 property')
    require(scenario(B_L=45)['L_observation']=='L の伸長を観測','L growth')
    require(scenario(B_L=43)['L_observation']=='事前登録した L 伸長の判定条件を満たさない','L below threshold')
    require(scenario(B_L=45)['pairs'][0]['gap_note']=='L 増大を伴う差の縮小','L growth gap shrink')
    require(scenario(other_W=99)['notes'],'W0 only shortening')
    def change_json(path,key,value):
        data=json.loads(path.read_bytes()); data[key]=value; path.write_text(json.dumps(data))
    def defect(kind):
        def mutate(root,paths):
            p=paths[1]
            if kind=='rc':
                change_json(p/'run.json','rc',1)
                (p/'classification.json').write_text(json.dumps({'class':'infra','reason':'synthetic child failure'}))
            elif kind=='sha':
                with (p/'session/shard-0/report.json').open('a') as f: f.write(' ')
            elif kind=='head': change_json(p/'run.json','tip_sha_after','0'*40)
            elif kind=='gate': (p/'gate.log').write_text((p/'gate.log').read_text().replace('load1=60','load1=61'))
            elif kind=='collection':
                (p/'session/login-collection.log').write_text('orchestrator/tests/test_bad.py::test_missing\n')
                rehash(p/'session')
        return mutate
    for kind in ('rc','sha','head','gate','collection'):
        r=scenario(normal[:2]+normal,mutate=defect(kind))
        require(not r['pairs'][0]['valid'] and r['valid_pairs']==3 and not r['series_invalid'], 'invalid whole-pair retry '+kind+str(r['series_invalid']))
    def classify(kind):
        def mutate(root,paths):
            change_json(paths[1]/'run.json','rc',1)
            if kind:
                (paths[1]/'classification.json').write_text(json.dumps({'class':kind,'reason':'fixture classification'}))
        return mutate
    for kind in ('impl','unclassified',None):
        require(scenario(mutate=classify(kind))['series_invalid'], 'classification '+str(kind))
    for n in range(1,7):
        r=scenario(normal[:n])
        require(not r['series_invalid'] and r['valid_pairs']==n//2,'prefix')
    require('runs after fixed stop' in scenario(normal+[('A',3)])['series_invalid'],'fixed stop')
    require(scenario(normal+normal+[('A',3)])['over_12_runs'],'12 cap exceeded')
    def invalidate_even(root,paths):
        for p in paths[1::2]: change_json(p/'run.json','tip_sha_after','0'*40)
    r=scenario(normal[:2]*6,mutate=invalidate_even)
    require(r['total_runs']==12 and r['valid_pairs']==0 and r['decision']=='判定不能 (反復不足)','12 cap insufficient')
    for specs in ([('B',1),('A',1)],normal[:1]+normal,normal[:2]+[('A',2),('B',2)]):
        require(scenario(specs)['series_invalid'],'wrong order/healthy half reuse')
    def skip(root,paths):
        p=paths[1]/'session/shard-0/junit.xml'
        tree=ET.parse(p); suite=tree.getroot()[0];suite.set('skipped','1')
        ET.SubElement(next(suite.iter('testcase')),'skipped',message='fixture')
        tree.write(p);rehash(paths[1]/'session')
    require(scenario(normal[:2]+normal,mutate=skip)['valid_pairs']==3,'skipped whole-pair retry')
    def mixed(root,paths):
        p=paths[1]/'session/shard-0/junit.xml';tree=ET.parse(p);tree.getroot()[0].set('time','110');tree.write(p);rehash(paths[1]/'session')
    require(scenario(mutate=mixed)['W_0']['subclassification']=='符号混在','mixed signs')
    def warm_bad(root,paths):
        change_json(root/'warm-A.json','sha','0'*40)
    require(scenario(mutate=warm_bad)['series_invalid'],'warm failure')
    # A-1: every prefix and whole-pair retry exposes exactly one next request.
    def accepts(result, condition, slot):
        try:
            check_request(result, condition, slot)
            return True
        except ValueError:
            return False
    for n in range(7):
        result = scenario(normal[:n])
        expected = normal[n] if n < 6 else None
        require(next_allowed(result) == expected, 'next request for prefix')
        for condition in 'AB':
            for slot in (1, 2, 3):
                require(accepts(result, condition, slot) == ((condition, slot) == expected),
                        'slot/condition request match')
    for mutation in (skip, defect('head'), defect('rc')):
        result = scenario(normal[:2], mutate=mutation)
        require(accepts(result, 'A', 1) and not accepts(result, 'B', 2), 'retry before next slot')
    result = scenario(normal[:4], mutate=lambda root, paths: defect('head')(root, paths[2:]))
    require(accepts(result, 'B', 2) and not accepts(result, 'A', 3), 'BA retry order')
    def first_invalid(root, paths):
        change_json(paths[0]/'run.json', 'tip_sha_after', '0'*40)
    require(next_allowed(scenario(normal[:1], mutate=first_invalid)) == ('A', 1), 'invalid first half restart')
    require(next_allowed(scenario(normal[:2]*6, mutate=invalidate_even)) is None, 'cap refuses request')
    require(next_allowed(scenario(mutate=classify('impl'))) is None, 'impl refuses request')
    # History loss must be visible even when discovery sees only surviving dirs.
    import shutil
    def lost_run(root, paths):
        shutil.rmtree(paths.pop())
    require(scenario(normal[:2], mutate=lost_run)['series_invalid'], 'deleted run invalidates series')
    require(scenario(normal[:1], mutate=lost_run)['series_invalid'], 'all runs deleted invalidates series')
    def changed_identity(root, paths):
        change_json(paths[-1]/'run.json', 'pair_slot', 2)
    require(scenario(normal[:2], mutate=changed_identity)['series_invalid'], 'ledger/metadata mismatch')
    def lost_log(root, paths):
        (root/'submissions.log').unlink()
    require(scenario(normal[:2], mutate=lost_log)['series_invalid'], 'missing log with runs')
    # Exercise both entry points without reaching a gate, runner or real job.
    with tempfile.TemporaryDirectory(prefix='t2825-launch-refusal-') as temp:
        root = Path(temp)
        tips = fixture_job(root)
        source = Path(__file__).resolve().parent
        for name in ('run-measure.sh', 'run-series.sh', 'gate.conf', 't2825_ab_analyze.py'):
            text = (source/name).read_text()
            if name.endswith('.sh'):
                text = text.replace('J=' + str(JOB), 'J=' + str(root))
            (root/name).write_text(text)
        path = fixture_run(root, tips, 5, 'A', 1)
        fixture_session(path)
        entries = read_submissions(root)
        check_number(entries, '06')  # A larger unused number is allowed.
        def refused(number, expected_rc):
            before = (root/'submissions.log').read_bytes()
            dirs = sorted(p.name for p in (root/'runs').iterdir())
            for script, args in [('run-measure.sh', [number, 'B', '1']),
                                 ('run-series.sh', [number + ' B 1'])]:
                completed = subprocess.run(['bash', str(root/script), *args],
                                           capture_output=True, text=True, timeout=15)
                require(completed.returncode == expected_rc,
                        script + ': ' + str(completed.returncode) + completed.stderr)
                require((root/'submissions.log').read_bytes() == before and
                        sorted(p.name for p in (root/'runs').iterdir()) == dirs,
                        'refusal must not consume submission or create RUN')
        refused('01', 99)
        refused('05', 99)
        shutil.rmtree(path)
        refused('06', 98)
    require(MEDIAN_NOTE in markdown(scenario(normal[:1])) and
            scenario()['median_definition'] == MEDIAN_NOTE, 'median definition in both outputs')
    # B-3: changing worktree bytes must only change comparison hash/warning.
    def ledger_changed(root, paths):
        (root/'tree-A'/LEDGER).write_text(json.dumps({'duration_seconds_by_nodeid': {
            'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt': 999}}))
    unchanged, changed = scenario(), scenario(mutate=ledger_changed)
    old = unchanged['ledger_provenance_by_condition']['A']
    new = changed['ledger_provenance_by_condition']['A']
    require(old['measurement_ledger_sha256'] == new['measurement_ledger_sha256'] and
            old['worktree_ledger_sha256'] != new['worktree_ledger_sha256'] and new['ledger_warning'],
            'measurement/worktree hashes separately bound')
    require(changed['valid_pairs'] == 3 and not changed['series_invalid'] and
            unchanged['runs'][0]['shards'][0]['ledger_predicted_load'] ==
            changed['runs'][0]['shards'][0]['ledger_predicted_load'], 'worktree drift does not alter load/validity')
    require('測定台帳 hash' in markdown(changed) and '集計時の worktree の台帳 hash' in markdown(changed), 'hash Markdown fields')
    # A-3: same base -> suffix -> 1.0 precedence and missing count as allocator.
    require(ledger_cost({'n': 2, 'n@g': .19}, 'n', 'g') == (2, False), 'base precedence')
    require(ledger_cost({'n@g': .19}, 'n', 'g') == (.19, False), 'suffix fallback')
    require(ledger_cost({'n': None, 'n@g': .19}, 'n', 'g') == (.19, False), 'null base fallback')
    require(ledger_cost({'n@g': .19}, 'n', None) == (1, True), 'no group default')
    require(ledger_cost({}, 'n', 'g') == (1, True), 'missing default')
    with tempfile.TemporaryDirectory(prefix='t2825-suffix-') as temp:
        root = Path(temp); tips = fixture_job(root)
        path = fixture_run(root, tips, 1, 'A', 1); session = fixture_session(path)
        node = 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt'
        for report_path in session.glob('shard-*/report.json'):
            report = json.loads(report_path.read_bytes())
            for record in report['observed_universe']:
                if record['nodeid'] == node: record['group'] = 'real-repo'
            report_path.write_text(json.dumps(report))
        rehash(session)
        parsed = parse_session(session, root/'input/login-collection.log', {node+'@real-repo': .19})
        require(abs(parsed['shards'][0]['ledger_predicted_load'] - 1.19) < 1e-9 and
                parsed['shards'][0]['ledger_missing_count'] == 1, 'report group load and missing count')
    # A-4: exclude the healthy half of an invalid pair from condition medians.
    def excluded_outlier(root, paths):
        skip(root, paths)
        xml = paths[0]/'session/shard-0/junit.xml'
        tree = ET.parse(xml); tree.getroot()[0].set('time', '999'); tree.write(xml)
        rehash(paths[0]/'session')
    result = scenario(normal[:2]+normal, mutate=excluded_outlier)
    require(result['condition_summaries']['A']['run_numbers'] == ['03','06','07'] and
            result['condition_summaries']['B']['run_numbers'] == ['04','05','08'], 'adopted pair population')
    require(result['condition_summaries']['A']['shards'][0] ==
            {'shard': 0, 'W': 100, 'O': 60, 'L': 40, 'F': 40, 'pre': 2, 'post': 37},
            'all condition/shard medians')
    require('対象走番号' in markdown(result) and 'med post' in markdown(result), 'condition Markdown')
    require(all(s['W'] is None for s in scenario(normal[:1])['condition_summaries']['A']['shards']),
            'healthy unpaired run excluded')
    print('PASS: real-shaped temporary fixtures; (i)/(ii)/(iii), 10% inclusive, subclasses; invalid rc/hash/HEAD/gate/collection + same-order retries; skipped, order, cap/fixed stop, impl/unclassified, warm; L rules, W_max note, cumulative start, old L; JSON/Markdown; next-slot matching/retries, pinned/worktree hash separation, suffix costs, adopted-pair medians; missing/mismatched submission history, launcher/series rc98 and rc99 without consumption, median definition')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--job',type=Path,default=JOB)
    for option in ('runs-root','tips','collection','out'):
        p.add_argument('--'+option,type=Path)
    args=p.parse_args()
    if args.selftest:
        selftest(); return 0
    tip_path=args.tips or args.job/'measurement-tips.json'
    tips=json.loads(tip_path.read_bytes())
    for c in 'AB':
        require(re.fullmatch('[0-9a-f]{40}',tips[c]['sha']) and Path(tips[c]['worktree']).is_absolute(),'invalid tips')
    root=args.runs_root or args.job/'runs'
    paths=[d for d in root.iterdir() if d.is_dir()] if root.exists() else []
    result=analyze(paths,args.collection or args.job/'input/login-collection.log',tips,warm_root=tip_path.parent)
    write_analysis(result,args.out or args.job/'analysis')
    print(result['decision'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        sys.exit(2)
````

## make_mutation_spec.py (sha256 `ed2a4caaeddab76fc6da2bae7c43adbe9e164fd2ca3eee1c0e6361e9d6738deb`, 9864 byte、Codex author (単位 M))

````python
#!/usr/bin/env python3
"""Generate T-2825 ledger mutation specs; never import repository modules.

The collection is the pinned main 21641fee7 capture. M3 keeps the G6
comparison key as well as frozen/real-repo keys: G6 also checks ordering.
Diagnostics belong on stdout because the harness rejects unknown fields.
"""

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path


FILE = "orchestrator/tests/acceptance_duration_ledger.json"
COLLECTION = Path(
    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/"
    "main-collect-21641fee7.txt"
)
FROZEN = tuple(
    f"orchestrator/tests/{suite}.py::" for suite in (
        "test_critic", "test_p3_exploration_namespace", "test_p3_s4_loop_sort",
        "test_real_repo_serialization", "test_s1_direct_comparison",
        "test_s8b_materialization", "test_s8b_sort_swo_receipt",
        "test_sort_swo_oracle",
    )
)
G6 = (
    "orchestrator/tests/test_acceptance_schedule_order.py::"
    "test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order"
)
M1_KEY = (
    "orchestrator/tests/test_sort_swo_oracle.py::"
    "test_masstree_manifest_rejects_one_byte_change"
)
M2_KEY = "orchestrator/tests/test_critic.py::test_t2825_mutation_stale"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(document):
    return (json.dumps(document, ensure_ascii=True, indent=2,
                       sort_keys=True, allow_nan=False) + "\n").encode("ascii")


def protected(key):
    return key.startswith(FROZEN) or "@real-repo" in key


def shortest_block(keys, collection, required_hits, keep_g6):
    """Sliding window: minimum length, then earliest canonical position."""
    best = None
    start = hits = 0
    for end, key in enumerate(keys):
        if protected(key) or (keep_g6 and key == G6):
            start, hits = end + 1, 0
            continue
        hits += key in collection
        while hits >= required_hits:
            candidate = (end - start + 1, start, end)
            if best is None or candidate < best:
                best = candidate
            hits -= keys[start] in collection
            start += 1
    require(best is not None, "no eligible contiguous M3 block reaches 87%")
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger_worktree", type=Path)
    parser.add_argument("mode", choices=("probe", "final"))
    parser.add_argument("out", type=Path)
    parser.add_argument("expected_nodes", type=Path, nargs="?")
    args = parser.parse_args()
    if (args.mode == "final") != (args.expected_nodes is not None):
        parser.error("final requires expected-nodes.json; probe takes no expected nodes")

    source = (args.ledger_worktree / FILE).read_bytes()
    document = json.loads(source)
    require(source == canonical(document), "ledger bytes are not canonical JSON")
    durations = document["duration_seconds_by_nodeid"]
    require(document["nodeid_count"] == len(durations), "ledger count mismatch")
    require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) and v >= 0 for v in durations.values()),
            "ledger durations must be nonnegative finite numbers")
    keys = sorted(durations)
    lines = source.splitlines(keepends=True)
    # Canonical layout is verified above; preserve actual source line bytes.
    entry_lines = dict(zip(keys, lines[2:2 + len(keys)]))
    collection_lines = [
        line for line in COLLECTION.read_text(encoding="utf-8").splitlines()
        if line.startswith("orchestrator/tests/") and "::" in line
    ]
    collection = set(collection_lines)
    require(len(collection_lines) == len(collection) == 26808,
            "pinned collection must contain 26808 distinct nodeid lines")
    covered = len(collection.intersection(durations))
    required_hits = covered - (len(collection) * 87 // 100)
    require(required_hits > 0, "unmutated coverage already at or below 87%")
    minimum = shortest_block(keys, collection, required_hits, False)
    size, start, end = shortest_block(keys, collection, required_hits, True)
    require(size == minimum[0], "preserving G6 would exceed global minimum M3 size")
    deleted = keys[start:end + 1]

    expected = {}
    if args.expected_nodes:
        expected = json.loads(args.expected_nodes.read_bytes())
        require(isinstance(expected, dict), "expected nodes must be an object")
        require(set(expected) in ({"M1", "M2", "M3"}, {"P0", "M1", "M2", "M3"}),
                "expected nodes must have M1/M2/M3 and optionally P0")
        require(expected.get("P0", []) == [], "P0 must have empty expected nodes")
        for mid in ("M1", "M2", "M3"):
            nodes = expected[mid]
            require(isinstance(nodes, list) and bool(nodes)
                    and all(isinstance(n, str) and n.strip() for n in nodes),
                    f"{mid}: expected nodes must be a nonempty string list")
            require(nodes == sorted(set(nodes)), f"{mid}: nodes must be sorted and unique")

    mutations = []
    counts = {}

    def add(mid, pairs, changed):
        current = source
        replacements = []
        counts[mid] = []
        for old, new in pairs:
            count = current.count(old)
            require(bool(old) and count == 1, f"{mid}: old count={count}, expected 1")
            require(old != new, f"{mid}: no-op replacement")
            counts[mid].append(count)
            current = current.replace(old, new, 1)
            replacements.append({"file": FILE, "old": old.decode("ascii"),
                                 "new": new.decode("ascii")})
        parsed = json.loads(current)
        require(parsed == changed and current == canonical(changed),
                f"{mid}: cumulative replacement differs from intended canonical JSON")
        require(parsed["nodeid_count"] == len(parsed["duration_seconds_by_nodeid"]),
                f"{mid}: count mismatch after cumulative replacements")
        killed = args.mode == "final" and mid != "P0"
        mutations.append({"id": mid, "category": "positive" if mid == "P0" else "negative",
                          "replacements": replacements,
                          "expected_nodes": expected[mid] if killed else [],
                          "expected_status": "KILLED" if killed else "SURVIVED",
                          "hang_risk": False})

    def changed_payload(values):
        return {**document, "duration_seconds_by_nodeid": values, "nodeid_count": len(values)}

    def value_mutation(mid, key, value):
        old = entry_lines[key]
        ending = b",\n" if old.endswith(b",\n") else b"\n"
        new = ("    " + json.dumps(key, ensure_ascii=True) + ": "
               + json.dumps(value, allow_nan=False)).encode("ascii") + ending
        add(mid, [(old, new)], changed_payload({**durations, key: value}))

    p0 = next(key for key in keys if not protected(key))
    value_mutation("P0", p0, 1.0 if durations[p0] == 0 else 0.0)
    require(durations[M1_KEY] == 0.12, "M1 requires original value 0.12")
    value_mutation("M1", M1_KEY, 0.13)
    require(M2_KEY not in durations, "M2 stale key already exists")
    successor = bisect.bisect_left(keys, M2_KEY)
    require(successor < len(keys), "M2 has no canonical successor")
    anchor = entry_lines[keys[successor]]
    inserted = ("    " + json.dumps(M2_KEY) + ": 1.0,\n").encode("ascii")
    old_count = f'  "nodeid_count": {len(keys)},\n'.encode("ascii")

    def count_pair(count):
        return old_count, f'  "nodeid_count": {count},\n'.encode("ascii")

    add("M2", [(anchor, inserted + anchor), count_pair(len(keys) + 1)],
        changed_payload({**durations, M2_KEY: 1.0}))
    old_block = b"".join(entry_lines[k] for k in deleted)
    new_block = b""
    if end == len(keys) - 1:
        # Include preceding line to remove its trailing comma as well.
        require(start > 0, "M3 cannot delete the entire ledger")
        preceding = entry_lines[keys[start - 1]]
        old_block = preceding + old_block
        new_block = preceding[:-2] + b"\n"
    deleted_set = set(deleted)
    remaining = {k: v for k, v in durations.items() if k not in deleted_set}
    add("M3", [(old_block, new_block), count_pair(len(keys) - size)],
        changed_payload(remaining))
    after_covered = len(collection.intersection(remaining))
    require(after_covered * 100 <= len(collection) * 87, "M3 coverage exceeds 87%")
    # T2236 used estimate=90, timeout=3900. Allow extra dispatch/queue margin;
    # harness dispatch mode additionally takes max(spec, P+Q+W+G+A+C).
    spec = {"schema": "izanagi-dev-wave-mutation-spec/v1",
            "estimated_run_seconds": 120, "timeout_seconds": 4500,
            "hang_timeout_seconds": 4500, "mutations": mutations}
    raw = (json.dumps(spec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.out.write_bytes(raw)
    print(json.dumps({"mode": args.mode, "spec_sha256": hashlib.sha256(raw).hexdigest(),
                      "ledger_sha256": hashlib.sha256(source).hexdigest(),
                      "old_counts": counts, "P0_key": p0,
                      "M3": {"deleted_count": size, "covered_before": covered,
                             "covered_after": after_covered, "collection_count": len(collection),
                             "coverage": after_covered / len(collection),
                             "first_key": deleted[0], "last_key": deleted[-1],
                             "global_minimum_size": minimum[0], "preserved_g6_key": G6}},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        raise SystemExit(f"make_mutation_spec: {exc}") from exc
````

## verify.py (sha256 `e290c6853226bb6d737eacda2a66724973001f8e767de7cb942b2a1f62c40b60`, 5307 byte、Codex author (単位 L) の台帳検算)

````python
from pathlib import Path
import ast, hashlib, json, math, subprocess
root=Path(__file__).resolve().parents[1]
a=root/'t2825-author-l'
job=Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab')
owned='orchestrator/tests/acceptance_duration_ledger.json'
source=ast.parse((root/'tools/update_acceptance_duration_ledger.py').read_text())
prefixes=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_ADD_ONLY_FROZEN_SUITE_PREFIXES' for t in n.targets))
oldbytes=(a/'ledger-before.json').read_bytes(); newbytes=(root/owned).read_bytes()
old=json.loads(oldbytes); new=json.loads(newbytes)
before=old['duration_seconds_by_nodeid']; after=new['duration_seconds_by_nodeid']
frozen=lambda d:{k:v for k,v in d.items() if k.startswith(prefixes)}
def frozen_lines(raw):
 result={}
 for line in raw.splitlines(keepends=True):
  if not line.startswith(b'    "'): continue
  key=json.JSONDecoder().raw_decode(line.decode().lstrip())[0]
  if key.startswith(prefixes): result[key]=line
 return result
checks={}
checks['a']={'pass':frozen(before)==frozen(after) and frozen_lines(oldbytes)==frozen_lines(newbytes),'before_count':len(frozen(before)),'after_count':len(frozen(after)),'line_bytes_equal':frozen_lines(oldbytes)==frozen_lines(newbytes)}
writer='orchestrator/tests/test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding'
checks['b']={'pass':after.get(writer+'@real-repo')==0.19,'value':after.get(writer+'@real-repo')}
checks['c']={'pass':set(new)=={'duration_seconds_by_nodeid','nodeid_count','schema_version','unit'} and type(new['schema_version']) is int and new['schema_version']==1 and new['unit']=='seconds' and type(new['nodeid_count']) is int and new['nodeid_count']==len(after) and all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in after.values()),'before_count':len(before),'after_count':len(after),'bytes':len(newbytes)}
tnodes=json.loads((job/'input/t2724-nodes-input.json').read_text())
values={row['name']:after.get('orchestrator/tests/test_s8b_oracle_driver.py::'+row['name']) for row in tnodes}
checks['d']={'pass':len(tnodes)==8 and all(values[r['name']]==r['ledger_new'] for r in tnodes),'values_seconds':values}
collection=(a/'main-nodeids.txt').read_text().splitlines(); nodes=set(collection)
cmd=['python3','tools/update_acceptance_duration_ledger.py','--refresh','--check',*[str(job/f'input/shard-{i}/junit.xml') for i in range(3)]]
def check_run(extra,log):
 r=subprocess.run(cmd+extra,cwd=root,capture_output=True,text=True)
 (a/log).write_text('stdout:\n'+r.stdout+'stderr:\n'+r.stderr+f'rc={r.returncode}\n')
 return r
r=check_run(['--coverage-against',str(a/'main-nodeids.txt')],'coverage.log')
covered=len(nodes & after.keys()); ratio=covered/len(nodes)
checks['e']={'pass':r.returncode==0 and len(collection)==len(nodes)==26808 and ratio>=0.9,'rc':r.returncode,'collection_count':len(collection),'covered':covered,'ratio':ratio,'generator_stdout':r.stdout}
r=check_run([],'determinism.log')
checks['f']={'pass':r.returncode==0 and (root/owned).read_bytes()==newbytes,'rc':r.returncode,'bytes_unchanged':(root/owned).read_bytes()==newbytes}
removed=sorted(before.keys()-after.keys()); added=after.keys()-before.keys()
(a/'removed.txt').write_text(f'count={len(removed)}\n'+'\n'.join(removed)+'\n')
checks['g']={'pass':len(removed)==140 and not nodes.intersection(removed) and not any(k.startswith(prefixes) for k in removed),'removed_count':len(removed),'in_main_count':len(nodes.intersection(removed)),'frozen_count':sum(k.startswith(prefixes) for k in removed)}
checks['h']={'pass':len(added)==2366 and not added-nodes,'added_count':len(added),'outside_main_count':len(added-nodes)}
# Create the final report paths before taking the status inventory.
for name in ('verify.md','verify.json','status.txt'):
 (a/name).touch()
r=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=root,capture_output=True,text=True,check=True)
(a/'status.txt').write_text(r.stdout)
lines=r.stdout.splitlines()
checks['i']={'pass':sum(line==' M '+owned for line in lines)==1 and all(line==' M '+owned or line.startswith('?? t2825-author-l/') for line in lines),'tracked_changed_count':sum(not line.startswith('?? ') for line in lines),'status':lines}
sha=lambda b:hashlib.sha256(b).hexdigest()
checks['j']={'pass':sha(newbytes)==sha((root/owned).read_bytes()),'before_sha256':sha(oldbytes),'after_sha256':sha(newbytes)}
slow='orchestrator/tests/test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order'
report={'checks':checks,'all_pass':all(c['pass'] for c in checks.values()),'static_support':{'writer_base_absent':writer not in after,'g6_known_slow_seconds':after.get(slow),'below_conftest_16MiB':len(newbytes)<16*1024*1024},'pytest_executed':False}
(a/'verify.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(a/'verify.md').write_text('# T-2825 author L verification\n\n'+ '\n'.join(f'- ({k}) {"PASS" if v["pass"] else "FAIL"}: `{json.dumps(v,ensure_ascii=False)}`' for k,v in checks.items())+'\n\npytest: 未実走。consumer / test の判断は静的確認のみ。\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['all_pass'] else 1)
````
