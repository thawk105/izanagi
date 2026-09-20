# [T-2700] 測定 launcher・集計器・見積り script の逐語と sha256

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab` の実行時版。sha256 は file bytes。集計器 2 本は Codex author (段 5) + fix2 (段 6)、launcher / 系列 / warm / run.json / gate は親、見積り script は親 (brief 前の前提実測、`verbatim/`)。repo には入れない。

| file | bytes | sha256 |
|---|---|---|
| `probe/t2700_ab_analyze.py` | 60081 | `cfbbc3e87ba1251889a4596744861157fc71d79b32ddd9f4dd9f6492e4a7c42b` |
| `probe/t2700_history_estimate.py` | 8638 | `3aa4909d301a008b51178eab6000845ab167cfe1cbfbd4bb48b877a5b6a5db02` |
| `run-measure.sh` | 8746 | `8937a44d4839567a9acf3420123c37553133fcf05643904d9326f0ea6e95100d` |
| `run-series.sh` | 3062 | `70be741a1e8392821b463a2c1aec53ea4f9307d55f0ef700f76c7daf15c4e09b` |
| `run-warm.sh` | 1245 | `345217002605826cf0299307d4d14da906581d095f7c7ab447cc33a78fa928e4` |
| `write_run_json.py` | 1814 | `88921438f231b891cfad5f3ece8412809277cfd1eb8d1a3b5b817cbc9057780f` |
| `gate_check.py` | 310 | `4a671af2f387b31a242799427c51e6662585cdae1885f62123307735bc308ac3` |
| `run-mutation.sh` | 1240 | `850d5088b7f5e69eb55b553074ca0e7009ca50fbd7e648c1699f7af813d66988` |
| `verbatim/power_rule.py` | 2921 | `fb25bd155c206747d67104778c9599ac55798fee5c7fda9e0dabdc9d10c1fe96` |
| `verbatim/power.py` | 1970 | `de8d7ff8c9e42836da349814732a965c6556750016f35a950da67d01f6c0b036` |
| `verbatim/head_stats.py` | 4518 | `6235f6e168476ee425a4ce1195d245abf0043a1a84dad03a533c268d993f8863` |
| `verbatim/dist_start.py` | 2766 | `7285ce9991956cfc971d70c054b15551b245c084e700a90cb14397f0344fa1f2` |
| `verbatim/prewarm_stats.py` | 1628 | `f58177d37a2431a08f4dfc92071ce3a3395e876bf1f73b3c7063f2c1320e1f13` |

## `probe/t2700_ab_analyze.py` (sha256 `cfbbc3e87ba1…`)

```python
"""T-2700 preregistered, successful-run-conditional paired analysis (stdlib)."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics as st
import tempfile
import subprocess
import sys
import xml.etree.ElementTree as ET

ENV = 'IZANAGI_T2700_EARLY_MEMO_OFF_V1'
TOKEN = 't2700-early-memo-off'
PREFIX = 'IZANAGI_MEMO_PREWARM_V1 '
T_CRIT = dict(enumerate((12.706, 4.303, 3.182, 2.776, 2.571, 2.447,
                        2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160,
                        2.145, 2.131, 2.120, 2.110, 2.101, 2.093), 1))
VERDICTS = {
    'support': '成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上)',
    'direction-only': '方向は支持、大きさは探索閾値未満',
    'not-established': 'n の範囲で効果未確立',
    'indeterminate': '判定不能',
}


def timestamp(value):
    value = re.sub(r'([+-][0-9]{2})([0-9]{2})\Z', r'\1:\2', value)
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('timestamp requires offset')
    return result.timestamp()


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('missing/nonfinite numeric field')
    return value


def read_json(path):
    return json.loads(Path(path).read_text())


def witnesses(text):
    return [json.loads(line[len(PREFIX):]) for line in text.splitlines() if line.startswith(PREFIX)]


def normalize(node):
    parts = node.split('::')
    return Path(parts[0]).name + '::' + parts[1].split('[', 1)[0].split('@', 1)[0] if len(parts) >= 2 else ''


def dump_consumers(path):
    names = {'RECEIPT_MEMO_CONSUMER_NODES', 'ORACLE_ENVIRONMENT_CONSUMER_NODES'}
    result = {}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    call = node.value
                    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != 'frozenset':
                        raise ValueError('consumer registry is not a frozenset literal')
                    result[target.id] = sorted(ast.literal_eval(call.args[0]))
    if set(result) != names:
        raise ValueError('missing consumer registry')
    result['source_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return result


def consumer_set(registries):
    return {normalize(node) for key in ('RECEIPT_MEMO_CONSUMER_NODES', 'ORACLE_ENVIRONMENT_CONSUMER_NODES')
            for node in registries.get(key, [])}


def shard_metrics(directory):
    directory = Path(directory)
    report = read_json(directory / 'report.json')
    with (directory / 'junit.xml').open('rb') as source:
        suite = next(element for _, element in ET.iterparse(source, events=('start',)) if element.tag == 'testsuite')
    start = timestamp(suite.attrib['timestamp'])
    wall = finite(float(suite.attrib['time']))
    if wall <= 0:
        raise ValueError('JUnit wall must be positive')
    timeline = report['session_timeline']
    workers = timeline['workers']
    occupancy = report['worker_occupancy']
    busiest = max(occupancy, key=lambda worker: finite(occupancy[worker]['duration_s']))
    occupied = finite(occupancy[busiest]['duration_s'])
    first = min(finite(worker['first_test_started_epoch_s']) for worker in workers.values())
    last = max(finite(worker['last_test_finished_epoch_s']) for worker in workers.values())
    selected = report['selected']
    if not isinstance(selected, list) or not all(isinstance(node, str) for node in selected):
        raise ValueError('selected must be nodeid list')
    digest = hashlib.sha256(json.dumps(sorted(selected), separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    return dict(W=wall, timestamp=suite.attrib['timestamp'], epoch=start,
                hostname=suite.attrib['hostname'], O=occupied, busiest=busiest,
                items=occupancy[busiest]['items'], F=wall-occupied,
                H=finite(timeline['collection_finished_epoch_s'])-start, D=first-start,
                tail=wall-(last-start), selected_digest=digest,
                **{key: report[key] for key in ('terminal_counts', 'pytest_rc', 'shard_count',
                                               'shard_index', 'effective_scheduler')}), selected


def check_hashes(session):
    entries = {}
    for line in (session / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(None, 1)
        name = name.lstrip('* ')
        path = session / name
        if Path(name).is_absolute() or '..' in Path(name).parts or name in entries:
            raise ValueError('invalid hash manifest path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('SHA256SUMS mismatch: ' + name)
        entries[name] = digest
    return entries


def inspect_run(directory, tip, consumers):
    row = dict(directory=str(directory), run=directory.name.split('-')[0], condition=directory.name[-1],
               valid=False, classification='artifact', shards=[], reasons=[])
    try:
        run = read_json(directory / 'run.json')
        row.update(run)
        row.update(valid=False, classification='artifact', shards=[], reasons=[], directory=str(directory))
        row['start'] = timestamp(run['submitted_at'])
        row['end'] = timestamp(run['finished_at'])
        if (int(run['run']) < 1 or int(run['run']) != int(directory.name.split('-')[0])
                or run['condition'] != directory.name[-1]):
            raise ValueError('run sequence/directory mismatch')
        if row['end'] < row['start']:
            raise ValueError('negative run interval')
        artifacts = run.get('artifacts', {})
        bad = {name: entry['status'] for name, entry in artifacts.items()
               if entry.get('requirement') == 'required' and entry.get('status') != 'ok'}
        row['artifact_issues'] = bad
        row['reasons'].extend(f'{name}: {status}' for name, status in bad.items())
        diagnostic_paths = sorted(directory.glob('session/shard-*/dispatch/izdw-shard-*.[eo]*'))
        if (directory / 'child.log').is_file():
            diagnostic_paths.append(directory / 'child.log')
        evidence = []
        for path in diagnostic_paths:
            for line in path.read_text(errors='replace').splitlines():
                if (any(marker in line for marker in ('memo publication timeout', 'publication-timeout',
                        'IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1', 'IZANAGI_ORACLE_ENVIRONMENT_MEMO_FAIL_CLOSED_V1'))
                        or ('TimeoutError' in line and 'memo' in line.lower())):
                    evidence.append(dict(path=str(path.relative_to(directory)), line=line))
        row['failure_evidence'] = evidence
        if run['condition'] == 'E' and evidence:
            row['classification'] = 'treatment-failure'
            row['reasons'].append('memo failure diagnostic')
            return row
        receipt_copy_failed = any(name.endswith('/receipt.json') and status in ('copy-failed', 'hash-mismatch')
                                  for name, status in bad.items())
        if receipt_copy_failed:
            return row  # artifact: failed copy is not receipt non-publication
        if any(name.endswith('/receipt.json') and status == 'missing-at-origin' for name, status in bad.items()):
            row['classification'] = 'infrastructure'
            row['reasons'].append('receipt not published at origin')
            return row
        missing_diagnostics = any(re.search(r'izdw-shard-\d+\.[eo]', name) for name in bad)
        if missing_diagnostics and run['rc'] != 0 and not evidence:
            row['classification'] = 'unknown'
            row['reasons'].append('diagnostics unavailable; child.log has no memo failure evidence')
            return row
        if any(status in ('copy-failed', 'hash-mismatch') for status in bad.values()):
            return row
        if run['rc'] == 16:
            row['classification'] = 'infrastructure'
            row['reasons'].append('dispatch rc=16')
            return row
        # Red status takes precedence over secondary missing artifacts.
        for path in directory.glob('session/shard-*/report.json'):
            report = read_json(path)
            if report.get('pytest_rc') == 1 or any(report.get('terminal_counts', {}).get(k, 0) for k in ('failed', 'error')):
                row['classification'] = 'red'
                row['reasons'].append('pytest/report failures')
                return row
        if run['rc'] != 0:
            row['classification'] = 'unknown'
            row['reasons'].append('unexplained nonzero run rc')
            return row
        if bad:
            raise ValueError('required artifacts not ok')
        if run.get('schema') != 't2700-run/v2':
            raise ValueError('run schema must be t2700-run/v2')
        if not isinstance(run.get('worktree_realpath'), str) or not Path(run['worktree_realpath']).is_absolute():
            raise ValueError('worktree_realpath missing/not absolute')
        if run.get('warm_tip') != tip or run.get('warm_rc') != 0:
            raise ValueError('warm-up tip/rc mismatch')
        if not (run['measurement_tip'] == run['tip_sha'] == run['tip_sha_after'] == tip):
            raise ValueError('measurement SHA mismatch')
        if run['dirty_lines_before'] != 0 or run['dirty_lines_after'] != 0:
            raise ValueError('dirty worktree')
        if run['copy_ok'] is not True or run['session_dir'] != 'session':
            raise ValueError('session copy incomplete')
        if run['condition'] not in ('E', 'L'):
            raise ValueError('invalid arm')
        if type(run['pair_slot']) is not int or run['pair_slot'] < 1:
            raise ValueError('invalid pair slot')
        expected_env = (None, '') if run['condition'] == 'E' else (TOKEN,)
        if run['env'].get(ENV) not in expected_env:
            raise ValueError('env arm mismatch')
        env_file = dict(line.split('=', 1) for line in (directory / 'env.txt').read_text().splitlines() if '=' in line)
        if env_file != run['env']:
            raise ValueError('env.txt mismatch')
        manifest = check_hashes(directory / 'session')
        if any(name not in manifest for name, entry in artifacts.items() if entry.get('status') == 'ok'):
            raise ValueError('copied artifact absent from hash manifest')
        for s in range(3):
            shard = directory / f'session/shard-{s}'
            metrics, selected = shard_metrics(shard)
            row['shards'].append(metrics)
            if (metrics['pytest_rc'] != 0 or metrics['shard_count'] != 3 or metrics['shard_index'] != s
                    or metrics['effective_scheduler'] != 'loadgroup'):
                raise ValueError('report configuration mismatch')
            if any(metrics['terminal_counts'][key] != 0 for key in ('failed', 'error')):
                row['classification'] = 'red'
                row['reasons'].append('pytest/report failures')
                return row
            if not row['start'] - 300 <= metrics['epoch'] <= row['end'] + 300:
                raise ValueError('JUnit timestamp outside run interval tolerance')
            receipt = read_json(shard / 'dispatch/receipt.json')
            request_bytes = (shard / 'dispatch/request.json').read_bytes()
            request = json.loads(request_bytes)
            result = read_json(shard / 'dispatch/result.json')
            request_sha256 = hashlib.sha256(request_bytes).hexdigest()
            if (receipt['request'].get('sha256') != request_sha256
                    or result.get('request_sha256') != request_sha256):
                raise ValueError('request binding hash mismatch')
            if receipt['result'] != result:
                raise ValueError('receipt/result mismatch')
            if (result['child_rc'] != 0 or receipt['outcome'].get('kind') != 'child'
                    or receipt['outcome'].get('rc') != 0
                    or receipt['outcome'].get('accounting_verified') is not True
                    or receipt['terminal_reason'] != 'scheduler-end-state'):
                raise ValueError('receipt not successful')
            if receipt['request']['args'] != request['args']:
                raise ValueError('receipt/request args mismatch')
            for binding in (receipt['request'], request):
                args = binding['args']
                if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
                    raise ValueError('request args must be a string list')
                for flag, expected in (('index', str(metrics['shard_index'])),
                                       ('count', str(metrics['shard_count'])),
                                       ('session', run['session_dir_origin'])):
                    key = '--izanagi-acceptance-shard-' + flag
                    values = []
                    for i, arg in enumerate(args):
                        if arg == key:
                            values.append(args[i+1] if i+1 < len(args) else None)
                        elif arg.startswith(key+'='):
                            values.append(arg[len(key)+1:])
                    if len(values) != 1 or values[0] != expected or not values[0]:
                        raise ValueError('request shard ' + flag + ' missing/duplicate/mismatch')
            if request.get('repo_root') != run['worktree_realpath']:
                raise ValueError('request worktree missing/mismatch')
            job = re.fullmatch(r'(?:\d+:)?(\d+)\.[\w.-]+', receipt['result']['pbs_jobid'])
            logs = list((shard / 'dispatch').glob(f'izdw-shard-{s}.e*'))
            if job is None or len(logs) != 1 or logs[0].name != f'izdw-shard-{s}.e{job[1]}':
                raise ValueError('witness job mismatch/multiple/missing')
            stdout = shard / f'dispatch/izdw-shard-{s}.o{job[1]}'
            if not stdout.is_file() or len(list((shard / 'dispatch').glob(f'izdw-shard-{s}.o*'))) != 1:
                raise ValueError('stdout missing')
            required = [shard / 'junit.xml', shard / 'report.json', logs[0], stdout] + [shard / ('dispatch/'+name+'.json') for name in ('receipt', 'request', 'result')]
            if any(str(path.relative_to(directory / 'session')) not in manifest for path in required):
                raise ValueError('mandatory artifact absent from hash manifest')
            if any(artifacts.get(str(path.relative_to(directory / 'session'))) != {'status': 'ok', 'requirement': 'required'} for path in required):
                raise ValueError('mandatory artifact status missing/not ok')
            witness = witnesses(logs[0].read_text())
            for entry in witness:
                finite(entry['barrier_s'])
                for key in ('receipt_memo_s', 'oracle_environment_memo_s'):
                    if entry[key] is not None:
                        finite(entry[key])
            has_consumer = bool({normalize(node) for node in selected} & consumers)
            hooks = (['configure_node'] if run['condition'] == 'E' else
                     ['xdist_node_collection_finished'] if s == 0 or has_consumer else [])
            if [w['hook'] for w in witness] != hooks:
                raise ValueError('witness arm mismatch')
            metrics.update(witness=witness, job=job[1], has_consumer=has_consumer)
        row.update(valid=True, classification='success', W_max=max(s['W'] for s in row['shards']))
    except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError) as exc:
        row['reasons'].append(str(exc))
    return row


@lru_cache(maxsize=64)
def signed_sums(ranks):
    # Enumerates every sign assignment, retaining multiplicities for ties.
    sums = [0]
    for rank in ranks:
        sums += [value + rank for value in sums]
    return tuple(sorted(sums))


def wilcoxon(deltas):
    import bisect
    nz = [x for x in deltas if x != 0]
    m = len(nz)
    if not m:
        return dict(m=0, one_sided=None, two_sided=None, method='indeterminate')
    ordered = sorted(abs(x) for x in nz)
    rank = {x: (ordered.index(x)+1 + m-ordered[::-1].index(x))/2 for x in ordered}
    ranks = tuple(sorted(int(2*rank[abs(x)]) for x in nz))
    observed = sum(int(2*rank[abs(x)]) for x in nz if x > 0)
    if m > 20:
        raise ValueError('Wilcoxon exact supports at most 20 nonzero differences')
    sums = signed_sums(ranks)
    upper = (len(sums)-bisect.bisect_left(sums, observed))/len(sums)
    lower = bisect.bisect_right(sums, observed)/len(sums)
    method = 'exact sign enumeration, average ranks, zeros removed'
    return dict(m=m, W_plus=observed/2, one_sided=upper, two_sided=min(1, 2*min(upper, lower)), method=method)


def rule(deltas):
    p = wilcoxon(deltas)['one_sided']
    if p is None:
        return 'indeterminate'
    return ('support' if st.median(deltas) >= 15 else 'direction-only') if p <= .05 else 'not-established'


def sensitivity(sd, n):
    if sd is None or sd == 0 or not n:
        return []
    rng = random.Random(20260920)
    rows = []
    for tail in (False, True):
        for delta in (15, 20, 27):
            hits = 0
            for _ in range(2000):
                sample = []
                for _ in range(n):
                    value = delta + rng.gauss(0, sd)
                    if tail:
                        if rng.random() < .15:
                            value += rng.uniform(30, 90)
                        if rng.random() < .15:
                            value -= rng.uniform(30, 90)
                    sample.append(value)
                hits += rule(sample) == 'support'
            rows.append(dict(model='normal + independent 15%/15% tails' if tail else 'normal',
                             delta=delta, sigma_d=sd, n=n, R=2000, seed=20260920, power=hits/2000))
    return rows


def inspect_series(root, tip, consumers, target=8, maximum=20):
    root = Path(root)
    if (root / 'runs').is_dir():
        root = root / 'runs'
    if not 1 <= target <= 20 or maximum < 1:
        raise ValueError('target-pairs must be 1..20; max-runs must be positive')
    rows = [inspect_run(p, tip, consumers) for p in root.iterdir()
            if p.is_dir() and re.fullmatch(r'\d+-[EL]', p.name)]
    rows.sort(key=lambda r: (int(Path(r['directory']).name.split('-')[0]), r['directory']))
    baseline, worktree, previous_end, previous_number = None, None, None, 0
    pairs, pending, slot, cutoff = [], None, 1, None
    invalid_attempts, stopped = 0, None
    state_slot, state_pending, state_pairs = 1, False, 0
    for index, row in enumerate(rows):
        number = int(Path(row['directory']).name.split('-')[0])
        row.update(used_in_pair=False, post_cutoff=cutoff is not None, over_budget=index >= maximum,
                   run_classification=row['classification'], sequence_violation=False)
        problems = []
        directory = Path(row['directory'])
        if number != previous_number + 1 or str(row.get('run')) not in (str(number), f'{number:02}') or row.get('condition') != directory.name[-1]:
            problems.append('run sequence/directory mismatch')
        if previous_end is not None and row.get('start', -math.inf) < previous_end:
            problems.append('nonmonotonic/overlapping attempts')
        previous_number = number
        previous_end = max(previous_end or -math.inf, row.get('end', -math.inf))
        if worktree is None:
            worktree = row.get('worktree_realpath')
        elif row.get('worktree_realpath') != worktree:
            problems.append('worktree_realpath mismatch')
        if row['valid']:
            digests = [shard['selected_digest'] for shard in row['shards']]
            if baseline is not None and baseline != digests:
                problems.append('selected digest mismatch')
            if not problems and baseline is None:
                baseline = digests
        if problems:
            row['reasons'].extend(problems)
            row.update(valid=False, classification='artifact')
        if row['post_cutoff']:
            continue
        expected = ('E', 'L') if slot % 2 else ('L', 'E')
        expected_arm = expected[0 if pending is None else 1]
        if (row.get('pair_slot') != slot or row.get('condition') != expected_arm
                or number != index+1 or 'run sequence/directory mismatch' in problems):
            row['reasons'].append(f'sequence-violation: expected slot {slot} arm {expected_arm}')
            row.update(valid=False, classification='sequence-violation', sequence_violation=True)
            pending = None
        elif not row['valid']:
            # An invalid attempt restarts both arms of this slot.
            pending = None
            invalid_attempts += 1
        elif pending is None:
            pending = row
        else:
            a, b = pending, row
            e, l = (a, b) if a['condition'] == 'E' else (b, a)
            delta = l['W_max']-e['W_max']
            pair = dict(slot=slot, E=e['run'], L=l['run'], W_E=e['W_max'], W_L=l['W_max'],
                        delta_W=delta, r=delta/e['W_max'],
                        shard_delta_W=[ls['W']-es['W'] for es, ls in zip(e['shards'], l['shards'])])
            pair.update({f'delta_{k}_0': l['shards'][0][k]-e['shards'][0][k] for k in ('D', 'H', 'O', 'tail')})
            pairs.append(pair)
            a['used_in_pair'] = b['used_in_pair'] = True
            pending, slot = None, slot+1
            invalid_attempts = 0
        # Operational stops do not redefine the preregistered analysis window.
        # Freeze launcher progress at the first stop, retaining later audit rows.
        if stopped is None:
            state_slot, state_pending, state_pairs = slot, pending is not None, len(pairs)
            if row['sequence_violation']:
                stopped = 'sequence-violation'
            elif invalid_attempts >= 3:
                stopped = 'series-invalid'
            elif len(pairs) >= target:
                stopped = 'target-pairs'
            elif index+1 >= maximum:
                stopped = 'max-runs'
        if len(pairs) == target or index+1 == maximum:
            cutoff = number
    expected = ('E', 'L') if state_slot % 2 else ('L', 'E')
    state = dict(runs_seen=len(rows), valid_pairs=state_pairs,
                 cutoff_reached=stopped is not None, stop_reason=stopped,
                 next_run_number=len(rows)+1, next_slot=state_slot,
                 next_arm=expected[1 if state_pending else 0], pending_first_arm=state_pending,
                 last_run=rows[-1] if rows else {})
    return rows, pairs, cutoff, state


def analyze(root, tip, consumers, target=8, maximum=20, mc=True):
    rows, pairs, cutoff, _ = inspect_series(root, tip, consumers, target, maximum)
    analysis_rows = [r for r in rows if not r['post_cutoff']]
    post_rows = [r for r in rows if r['post_cutoff']]
    def counts(selected):
        return {arm: dict(attempts=sum(r.get('condition') == arm for r in selected),
                          counts=dict(Counter(r['classification'] for r in selected if r.get('condition') == arm)))
                for arm in ('E', 'L')}
    deltas = [p['delta_W'] for p in pairs]
    sd = st.stdev(deltas) if len(deltas) > 1 else None
    failures = counts(analysis_rows)
    wins = sum(x > 0 for x in deltas)
    losses = sum(x < 0 for x in deltas)
    # In-window failures only; paired speed samples contain only successes.
    wins += sum(r.get('condition') == 'L' and not r['valid'] for r in analysis_rows)
    losses += sum(r.get('condition') == 'E' and not r['valid'] for r in analysis_rows)
    nsign = wins+losses
    sign_p = sum(math.comb(nsign, k) for k in range(wins, nsign+1))/2**nsign if nsign else None
    verdict = rule(deltas)
    return dict(analysis_cutoff=cutoff, post_cutoff=counts(post_rows), measurement_tip=tip, consumer_nodes=sorted(consumers), runs=rows, pairs=pairs, target_pairs=target, max_runs=maximum,
                status='complete' if len(pairs) >= target else '未達', cap_reached=len(rows) >= maximum,
                wilcoxon=wilcoxon(deltas), sigma_d=sd,
                t=dict(statistic=st.mean(deltas)/(sd/math.sqrt(len(deltas))) if sd else None,
                       df=len(deltas)-1 if deltas else None, critical_5pct_two_sided=T_CRIT.get(len(deltas)-1),
                       note='SD=0: descriptive only; critical table available for df 1..19'),
                medians=dict(paired_difference=st.median(deltas) if deltas else None,
                             paired_ratio=st.median(p['r'] for p in pairs) if pairs else None,
                             difference_of_condition_medians=st.median(p['W_L'] for p in pairs)-st.median(p['W_E'] for p in pairs) if pairs else None),
                verdict=verdict, conclusion=VERDICTS[verdict] + ' + 腕別失敗件数 ' + ', '.join(f'{arm}={sum(v for k,v in failures[arm]["counts"].items() if k != "success")}' for arm in ('E', 'L')),
                failures=failures, failure_sign_sensitivity=dict(wins=wins, losses=losses, one_sided_p=sign_p,
                    note='Each failed attempt is an arm loss; unknown/both-arm failures retained in counts. Not a paired speed estimate.'),
                sensitivity=sensitivity(sd, len(pairs)) if mc else [],
                sensitivity_note='正規成分 SD σ + 両腕独立の遅延 (各 15 %、+30〜90 秒 / −30〜90 秒) の対称 model。σ は対差全体の SD ではない。')


def descriptive(root, window, excluded):
    rows, errors = [], []
    for directory in sorted(Path(root).glob('*/shard-0')):
        if str(directory.parent) in excluded:
            continue
        try:
            metrics, _ = shard_metrics(directory)
            if window[0] <= metrics['epoch'] <= window[1]:
                logs = list((directory / 'dispatch').glob('shard-0/izdw-shard-0.e*'))
                hooks = [w['hook'] for p in logs for w in witnesses(p.read_text(errors='replace'))]
                rows.append(dict(session=str(directory.parent), W=metrics['W'], D=metrics['D'],
                                 timestamp=metrics['timestamp'], hooks=hooks))
        except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError) as exc:
            errors.append(dict(session=str(directory.parent), error=str(exc)))
    return dict(rows=rows, exclusions=errors, note='Descriptive only: other tips; never a stopping criterion.')


def table(rows, keys):
    def cell(value):
        return json.dumps(value, ensure_ascii=False).replace('|', '\\|') if isinstance(value, (dict, list)) else str(value)
    return '\n'.join(['| ' + ' | '.join(keys) + ' |', '| ' + ' | '.join('---' for _ in keys) + ' |'] +
                     ['| ' + ' | '.join(cell(r.get(k, '')) for k in keys) + ' |' for r in rows])


def write_analysis(data, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'analysis.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    lines = ['## 判定', data['conclusion'], data['status'],
             '成功走に条件付き。15 秒は便宜的探索閾値であり母効果 ≥15 秒の証明ではない。',
             'H は worker collection-finish 最大時刻（E の待ち込み）、D は最初の test 開始。D−H は純解決所要ではない。',
             '必要対数は効果・分散・裾の仮定に依存し確定できない。', '## 走表',
             table(data['runs'], ['run', 'condition', 'pair_slot', 'classification', 'W_max', 'used_in_pair', 'over_budget', 'post_cutoff', 'sequence_violation', 'reasons'])]
    for row in data['runs']:
        lines += [f'## Run {row.get("run", row["directory"])}', table(row['shards'],
                  ['shard_index', 'W', 'timestamp', 'hostname', 'O', 'busiest', 'items', 'F', 'H', 'D', 'tail',
                   'terminal_counts', 'pytest_rc', 'shard_count', 'effective_scheduler', 'selected_digest', 'job', 'witness'])]
    lines += ['## 対表', table(data['pairs'], ['slot', 'E', 'L', 'delta_W', 'r', 'delta_D_0', 'delta_H_0', 'delta_O_0', 'delta_tail_0', 'shard_delta_W'])]
    for title, keys in [('中央値・検定', ['medians', 'wilcoxon', 't', 'sigma_d']), ('失敗集計', ['analysis_cutoff', 'failures', 'post_cutoff', 'failure_sign_sensitivity'])]:
        lines += ['## '+title, json.dumps({k:data[k] for k in keys}, ensure_ascii=False, indent=2)]
    lines += ['## 感度', data['sensitivity_note'], table(data['sensitivity'], ['model', 'delta', 'sigma_d', 'n', 'R', 'seed', 'power']),
              '## 記述的対照', json.dumps(data.get('descriptive_control', {}), ensure_ascii=False, indent=2)]
    (out / 'analysis.md').write_text('\n\n'.join(lines)+'\n')


def selftest():
    assert timestamp('2026-09-20T10:14:38+0900') == timestamp('2026-09-20T10:14:38+09:00')
    assert timestamp('2026-09-20T10:14:38-0930') == timestamp('2026-09-20T10:14:38-09:30')
    cases = [([40]*5+[-45], 17/64, 'not-established'), ([10,20,30,40,50,-60], 14/64, 'not-established'),
             ([5,6,7,8,9,10], 1/64, 'direction-only'), ([0,0,12,20,30,40], 1/16, 'not-established'),
             ([30,25,40,20,35,28], 1/64, 'support')]
    for sample, p, verdict in cases:
        assert wilcoxon(sample)['one_sided'] == p
        assert rule(sample) == verdict
    assert rule([0, 0]) == 'indeterminate'
    assert st.median(cases[-1][0]) == 29
    with tempfile.TemporaryDirectory(prefix='t2700-selftest-') as tmp:
        root = Path(tmp)
        def make(number, arm, slot=1, change=None):
            directory = root / f'{number:02}-{arm}'
            directory.mkdir()
            start = 1700000000 + number*1000
            iso = lambda seconds: datetime.fromtimestamp(seconds, timezone.utc).isoformat()
            env = {ENV: TOKEN if arm == 'L' else ''}
            run = dict(schema='t2700-run/v2', worktree_realpath='/synthetic/worktree', warm_tip='tip', warm_rc=0, artifacts={}, run=f'{number:02}', condition=arm, pair_slot=slot, measurement_tip='tip', tip_sha='tip', tip_sha_after='tip',
                       submitted_at=iso(start), finished_at=iso(start+500), session_dir='session', session_dir_origin='original',
                       copy_ok=True, env=env, other_leaders=0, load1=1, rc=0, dirty_lines_before=0, dirty_lines_after=0)
            (directory/'env.txt').write_text(f'{ENV}={env[ENV]}\n')
            for s in range(3):
                shard = directory/f'session/shard-{s}'
                (shard/'dispatch').mkdir(parents=True)
                (shard/'junit.xml').write_text(f'<testsuites><testsuite time="{330 if arm == "L" else 300}" timestamp="{iso(start)}" hostname="node"/></testsuites>')
                report = dict(pytest_rc=0, shard_count=3, shard_index=s, effective_scheduler='loadgroup', selected=['test_a.py::test_a'] if s == 0 else [],
                              terminal_counts=dict(failed=0, error=0), worker_occupancy={'gw0':dict(duration_s=200, items=1)},
                              session_timeline=dict(collection_finished_epoch_s=start+50, workers={'gw0':dict(first_test_started_epoch_s=start+60, last_test_finished_epoch_s=start+280)}))
                (shard/'report.json').write_text(json.dumps(report))
                request = dict(args=[f'--izanagi-acceptance-shard-index={s}', '--izanagi-acceptance-shard-count=3',
                                     '--izanagi-acceptance-shard-session=original'], repo_root='/synthetic/worktree',
                               environment=env, request_binding='sha256-job-script/v1',
                               runner_binding=dict(nonce='synthetic', shard_count=3, shard_index=s, tested_main='tip'),
                               schema_version='pegasus-dispatch-request/v2', task='tests')
                request_sha256 = hashlib.sha256(json.dumps(request).encode()).hexdigest()
                result = dict(pbs_jobid='0:123.nqsv', child_rc=0, request_sha256=request_sha256)
                receipt_request = dict(args=request['args'], job_name=f'izdw-shard-{s}', nodes=1,
                                       project='SFC', queue='gen_S', sha256=request_sha256,
                                       task='tests', walltime='01:00:00')
                receipt = dict(request=receipt_request, result=result, outcome=dict(kind='child', rc=0, accounting_verified=True),
                               terminal_reason='scheduler-end-state')
                for name, value in (('receipt', receipt), ('request', request), ('result', result)):
                    (shard/f'dispatch/{name}.json').write_text(json.dumps(value))
                witness = [dict(hook='configure_node' if arm == 'E' else 'xdist_node_collection_finished', receipt_memo_s=30, oracle_environment_memo_s=.1, barrier_s=30)] if arm == 'E' or s == 0 else []
                (shard/f'dispatch/izdw-shard-{s}.e123').write_text(''.join(PREFIX+json.dumps(w)+'\n' for w in witness))
                (shard/f'dispatch/izdw-shard-{s}.o123').write_text('ok')
            run['artifacts'] = {str(p.relative_to(directory/'session')): dict(status='ok', requirement='required')
                                for p in (directory/'session').rglob('*') if p.is_file()}
            if change:
                change(directory, run)
            (directory/'run.json').write_text(json.dumps(run))
            session = directory/'session'
            (session/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(session))+'\n' for p in sorted(session.rglob('*')) if p.is_file()))
            return directory
        registry = Path(tmp)/'consumers.json'
        registry.write_text(json.dumps(dict(RECEIPT_MEMO_CONSUMER_NODES=['test_a.py::test_a'],
                                            ORACLE_ENVIRONMENT_CONSUMER_NODES=[], source_sha256='source-hash')))
        def cli(directory, kind, reason=None):
            completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--check-run', str(directory),
                                        '--measurement-tip', 'tip', '--consumer-nodes', str(registry)],
                                       capture_output=True, text=True)
            assert completed.returncode == (0 if kind == 'success' else 1), completed.stderr
            assert json.loads(completed.stdout)['classification'] == kind, completed.stdout
            if reason is not None:
                assert reason in json.loads(completed.stdout)['reasons'], completed.stdout
        a = make(1, 'E')
        assert 'repo_root' not in read_json(a/'session/shard-0/dispatch/receipt.json')['request']
        cli(a, 'success')
        make(2, 'L')
        assert len(analyze(root, 'tip', {'test_a.py::test_a'}, target=1, mc=False)['pairs']) == 1
        tests = [
            ('artifact', lambda p,r: r['env'].update({ENV:TOKEN})),
            ('unknown', lambda p,r: r.update(rc=3)),
            ('infrastructure', lambda p,r: r.update(rc=16)),
            ('treatment-failure', lambda p,r: (p/'session/shard-0/dispatch/izdw-shard-0.e123').write_text('INTERNALERROR> TimeoutError: [Errno 110] memo publication timeout\n')),
            ('artifact', lambda p,r: (p/'session/shard-0/junit.xml').write_text('<testsuite time="1" timestamp="2026-09-20T01:00:00" hostname="n"/>')),
            ('artifact', lambda p,r: (p/'session/shard-0/dispatch/receipt.json').write_text('{"result":{"pbs_jobid":"0:999.nqsv"}}')),
            ('red', lambda p,r: (p/'session/shard-0/report.json').write_text('{"pytest_rc":1}')),
            ('artifact', lambda p,r: (p/'session/shard-0/junit.xml').unlink()),
        ]
        for number, (kind, change) in enumerate(tests, 3):
            directory = make(number, 'E', change=change)
            assert inspect_run(directory, 'tip', {'test_a.py::test_a'})['classification'] == kind, kind
            cli(directory, kind)
        # Invalid intervening attempt cannot be skipped to manufacture adjacency.
        make(11, 'E', 1)
        make(12, 'L', 1)
        make(13, 'L', 2)
        make(14, 'E', 2)
        result = analyze(root, 'tip', {'test_a.py::test_a'}, target=1, mc=False)
        assert len(result['pairs']) == 1 and len(result['runs']) == 14
        result = analyze(root, 'tip', {'test_a.py::test_a'}, target=8, maximum=14, mc=False)
        assert result['status'] == '未達' and result['cap_reached']
        assert len(result['pairs']) == 2
        report_path = a/'session/shard-0/report.json'
        report = read_json(report_path)
        report['selected'].append('different.py::test_b')
        report_path.write_text(json.dumps(report))
        session = a/'session'
        (session/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(session))+'\n' for p in sorted(session.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
        result = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
        assert 'selected digest mismatch' in result['runs'][1]['reasons']
        report_path.write_text(report_path.read_text()+' ')
        assert 'SHA256SUMS mismatch' in inspect_run(a, 'tip', {'test_a.py::test_a'})['reasons'][0]
        root = root / 'retakes'
        root.mkdir()
        make(1, 'E')
        make(2, 'L', change=lambda p,r:r.update(rc=16))
        make(3, 'E')
        make(4, 'L')
        make(5, 'L', 2)
        make(6, 'E', 2)
        make(7, 'E', 3)
        make(8, 'L', 3)
        result = analyze(root, 'tip', {'test_a.py::test_a'}, target=2, maximum=8, mc=False)
        assert [(p['E'], p['L']) for p in result['pairs']] == [('03','04'), ('06','05')]
        assert not result['runs'][7]['used_in_pair']
        result = analyze(root, 'tip', {'test_a.py::test_a'}, target=8, maximum=5, mc=False)
        assert len(result['pairs']) == 1 and result['cap_reached'] and result['status'] == '未達'
        assert result['runs'][5]['over_budget']
        completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--runs-root', str(root),
                                    '--measurement-tip', 'tip', '--consumer-nodes', str(registry),
                                    '--max-runs', '5', '--out', str(root/'cli-analysis')], capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr
        assert read_json(root/'cli-analysis/analysis.json')['source_sha256'] == 'source-hash'
        # Separate series: no adopted slot can conceal a nonadjacent pairing bug.
        root = Path(tmp)/'nonadjacent'
        root.mkdir()
        make(1, 'E')
        make(2, 'L')
        make(3, 'L', 2)
        make(4, 'E', 2, lambda p,r: r.update(rc=16))
        make(5, 'E', 2)
        result = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
        assert len(result['pairs']) == 1
        assert result['runs'][4]['classification'] == 'sequence-violation'
        make(6, 'E', 3)  # skipped unfinished slot 2
        make(7, 'E', 1)  # backtracking to completed slot 1
        result = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
        assert all(r['sequence_violation'] for r in result['runs'][4:])
        root = Path(tmp)/'first-arm-retry'
        root.mkdir()
        make(1, 'E', change=lambda p,r: r.update(rc=16))
        make(2, 'E')
        make(3, 'L')
        assert analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)['pairs'][0]['E'] == '02'
        # Both target and budget cutoffs freeze all inferential outputs.
        for budget_cutoff in (False, True):
            root = Path(tmp)/('cutoff-'+str(budget_cutoff))
            root.mkdir()
            make(1, 'E')
            make(2, 'L')
            kwargs = dict(target=8 if budget_cutoff else 1, maximum=2 if budget_cutoff else 20, mc=False)
            before = analyze(root, 'tip', {'test_a.py::test_a'}, **kwargs)
            make(3, 'E', 2, lambda p,r: r.update(rc=16))
            make(4, 'L', 2, lambda p,r: r.update(rc=3))
            after = analyze(root, 'tip', {'test_a.py::test_a'}, **kwargs)
            assert after['analysis_cutoff'] == 2
            for key in ('pairs', 'wilcoxon', 'conclusion', 'failures', 'failure_sign_sensitivity', 'sensitivity'):
                assert before[key] == after[key], key
            assert after['post_cutoff']['E']['attempts'] == after['post_cutoff']['L']['attempts'] == 1
        root = Path(tmp)/'validation'
        root.mkdir()
        def edit_json(path, update):
            value = read_json(path)
            update(value)
            path.write_text(json.dumps(value))
        def rebind_request(dispatch):
            digest = hashlib.sha256((dispatch/'request.json').read_bytes()).hexdigest()
            edit_json(dispatch/'result.json', lambda d:d.update(request_sha256=digest))
            edit_json(dispatch/'receipt.json', lambda d:(d['request'].update(sha256=digest),
                      d.update(result=read_json(dispatch/'result.json'))))
        def consumers_in_all(p, r):
            for shard in (1, 2):
                edit_json(p/f'session/shard-{shard}/report.json',
                          lambda report: report.update(selected=['orchestrator/tests/test_a.py::test_a[param]@group']))
                (p/f'session/shard-{shard}/dispatch/izdw-shard-{shard}.e123').write_text(
                    (p/'session/shard-0/dispatch/izdw-shard-0.e123').read_text())
        good = make(1, 'L', change=consumers_in_all)
        cli(good, 'success')
        assert normalize('orchestrator/tests/test_a.py::test_a[param]@group') == 'test_a.py::test_a'
        assert normalize('test_a.py::test_a@group') == 'test_a.py::test_a'
        for number, change in enumerate((
                lambda p,r: (p/'session/shard-0/dispatch/izdw-shard-0.e123').write_text(''),
                lambda p,r: (p/'session/shard-0/dispatch/izdw-shard-0.e123').write_text(
                    (p/'session/shard-0/dispatch/izdw-shard-0.e123').read_text()*2),
                lambda p,r: (p/'session/shard-0/dispatch/izdw-shard-0.e123').write_text(
                    (p/'session/shard-0/dispatch/izdw-shard-0.e123').read_text().replace('xdist_node_collection_finished', 'configure_node')),
                lambda p,r: r.update(warm_rc=1),
                lambda p,r: r.update(warm_tip='other'),
                lambda p,r: r['artifacts']['shard-0/dispatch/receipt.json'].update(status='copy-failed'),
                lambda p,r: r['artifacts']['shard-0/dispatch/receipt.json'].update(status='hash-mismatch'),
                lambda p,r: edit_json(p/'session/shard-0/dispatch/receipt.json', lambda d: d.update(terminal_reason='bad')),
                lambda p,r: edit_json(p/'session/shard-0/dispatch/request.json', lambda d: d.update(args=[])),
                lambda p,r: (p/'session/shard-0/junit.xml').write_text('<testsuite time="300" timestamp="2000-01-01T00:00:00+00:00" hostname="n"/>'),
                ), 2):
            cli(make(number, 'L', change=change), 'artifact')
        missing = make(12, 'E', change=lambda p,r:r['artifacts']['shard-0/dispatch/receipt.json'].update(status='missing-at-origin'))
        cli(missing, 'infrastructure')
        def lost_log(p, r):
            r.update(rc=16, copy_ok=False, session_dir=None)
            r['artifacts']['shard-0/dispatch/izdw-shard-0.o123']['status'] = 'copy-failed'
            (p/'session/shard-0/dispatch/izdw-shard-0.o123').unlink()
        cli(make(13, 'E', change=lost_log), 'unknown')
        # Exception lines use the actual memo constructors' canonical JSON format.
        diagnostics = [
            'INTERNALERROR> TimeoutError: [Errno 110] memo publication timeout',
            'INTERNALERROR> ReceiptMemoError: IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1 {"cache_path":null,"head":null,"prewarm":false,"process_prewarmed":false,"reason":"publication-timeout","run_id":null}',
            'INTERNALERROR> OracleEnvironmentMemoError: IZANAGI_ORACLE_ENVIRONMENT_MEMO_FAIL_CLOSED_V1 {"cache_path":null,"head":null,"prewarm":false,"process_prewarmed":false,"reason":"publication-timeout","run_id":null}',
        ]
        for number, diagnostic in enumerate(diagnostics, 14):
            for location in ('stdout', 'stderr', 'child'):
                # One run directory per fixture, while preserving its numeric name.
                root = Path(tmp)/f'diagnostic-{number}-{location}'
                root.mkdir()
                def failure(p, r):
                    r['rc'] = 16
                    if location == 'child':
                        lost_log(p, r)
                    path = p/'child.log' if location == 'child' else p/f'session/shard-0/dispatch/izdw-shard-0.{"o" if location == "stdout" else "e"}123'
                    path.write_text(diagnostic+'\n')
                cli(make(1, 'E', change=failure), 'treatment-failure')
        root = Path(tmp)/'extra-bindings'
        root.mkdir()
        def bad_child(p, r):
            for name in ('receipt', 'result'):
                edit_json(p/f'session/shard-0/dispatch/{name}.json',
                          lambda d: (d['result'] if name == 'receipt' else d).update(child_rc=3))
        def bad_job(p, r):
            for name in ('receipt', 'result'):
                edit_json(p/f'session/shard-0/dispatch/{name}.json',
                          lambda d: (d['result'] if name == 'receipt' else d).update(pbs_jobid='0:999.nqsv'))
        def bad_shard(p, r):
            for name in ('receipt', 'request'):
                edit_json(p/f'session/shard-0/dispatch/{name}.json',
                          lambda d: (d['request'] if name == 'receipt' else d).update(args=['--izanagi-acceptance-shard-index=2']))
        def missing_consumer_witness(p, r):
            consumers_in_all(p, r)
            (p/'session/shard-1/dispatch/izdw-shard-1.e123').write_text('')
        for n, change in enumerate((bad_child, bad_job, bad_shard, missing_consumer_witness,
                lambda p,r:(p/'session/shard-0/dispatch/izdw-shard-0.o999').write_text('extra'),
                lambda p,r:r.update(dirty_lines_after=1),
                lambda p,r:r.update(tip_sha_after='other'),
                lambda p,r:edit_json(p/'session/shard-0/report.json', lambda d:d.update(session_timeline={}))), 1):
            cli(make(n, 'L', change=change), 'artifact')
        # Both copies carry each shard argument; only request.json carries repo_root.
        for flag in ('index', 'count', 'session', 'repo_root'):
            for mode in ('missing', 'duplicate', 'wrong') if flag != 'repo_root' else ('missing', 'wrong'):
                root = Path(tmp)/f'binding-{flag}-{mode}'
                root.mkdir()
                def broken_binding(p, r):
                    def update(binding):
                        if flag == 'repo_root':
                            if mode == 'missing':
                                binding.pop('repo_root')
                            else:
                                binding['repo_root'] = '/wrong'
                            return
                        key = '--izanagi-acceptance-shard-' + flag + '='
                        original = next(arg for arg in binding['args'] if arg.startswith(key))
                        if mode == 'duplicate':
                            binding['args'].append(original)
                        else:
                            binding['args'].remove(original)
                            if mode == 'wrong':
                                binding['args'].append(key+'wrong')
                    for name in (('request',) if flag == 'repo_root' else ('request', 'receipt')):
                        edit_json(p/f'session/shard-0/dispatch/{name}.json',
                                  lambda d:update(d['request'] if name == 'receipt' else d))
                    rebind_request(p/'session/shard-0/dispatch')
                reason = ('request worktree missing/mismatch' if flag == 'repo_root' else
                          'request shard ' + flag + ' missing/duplicate/mismatch')
                cli(make(1, 'E', change=broken_binding), 'artifact', reason)

        for source in ('receipt', 'result'):
            root = Path(tmp)/('binding-hash-'+source)
            root.mkdir()
            def broken_hash(p, r):
                dispatch = p/'session/shard-0/dispatch'
                if source == 'receipt':
                    edit_json(dispatch/'receipt.json', lambda d:d['request'].update(sha256='0'*64))
                else:
                    edit_json(dispatch/'result.json', lambda d:d.update(request_sha256='0'*64))
                    edit_json(dispatch/'receipt.json', lambda d:d.update(result=read_json(dispatch/'result.json')))
            cli(make(1, 'E', change=broken_hash), 'artifact', 'request binding hash mismatch')

        def state_cli(label, expected, extra=()):
            completed = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                '--series-state', str(root), '--measurement-tip', 'tip',
                '--consumer-nodes', str(registry), *extra], capture_output=True, text=True)
            assert completed.returncode == 0, completed.stderr
            assert len(completed.stdout.splitlines()) == 1
            state = json.loads(completed.stdout)
            for key, value in expected.items():
                assert state[key] == value, (label, key, state)
            shared = inspect_series(root, 'tip', {'test_a.py::test_a'},
                                    maximum=20)[3]
            if not extra:
                assert state == shared
            # Print the actual CLI state compactly; last_run retains its full row in the CLI.
            print('series-state '+label+': '+json.dumps({k:v for k,v in state.items() if k != 'last_run'}))
            assert bool(state['last_run']) == bool(state['runs_seen'])
            analysis = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
            assert state['valid_pairs'] == len(analysis['pairs'])
            assert state['last_run'] == (analysis['runs'][-1] if analysis['runs'] else {})
            return state

        root = Path(tmp)/'state-abc'
        root.mkdir()
        state_cli('a', dict(runs_seen=0, valid_pairs=0, next_run_number=1,
                           next_slot=1, next_arm='E', pending_first_arm=False, cutoff_reached=False, stop_reason=None))
        make(1, 'E')
        state_cli('b', dict(runs_seen=1, valid_pairs=0, next_run_number=2,
                           next_slot=1, next_arm='L', pending_first_arm=True, cutoff_reached=False, stop_reason=None))
        make(2, 'L')
        state_cli('c', dict(runs_seen=2, valid_pairs=1, next_run_number=3,
                           next_slot=2, next_arm='L', pending_first_arm=False, cutoff_reached=False, stop_reason=None))
        def different_digest(p, r):
            edit_json(p/'session/shard-0/report.json', lambda d:d.update(selected=['different.py::test_b']))
        for label, change in (('d', lambda p,r:r.update(rc=16)), ('e', different_digest)):
            root = Path(tmp)/('state-'+label)
            root.mkdir()
            make(1, 'E')
            second = make(2, 'L', change=change)
            if label == 'e':
                cli(second, 'success')
            state_cli(label, dict(runs_seen=2, valid_pairs=0, next_run_number=3,
                                 next_slot=1, next_arm='E', pending_first_arm=False, cutoff_reached=False, stop_reason=None))
            make(3, 'E')
            make(4, 'L')
            assert inspect_series(root, 'tip', {'test_a.py::test_a'})[3]['valid_pairs'] == 1
        root = Path(tmp)/'state-f'
        root.mkdir()
        for slot in range(1, 9):
            for arm in (('E', 'L') if slot % 2 else ('L', 'E')):
                make(len(list(root.iterdir()))+1, arm, slot)
        state_cli('f', dict(runs_seen=16, valid_pairs=8, next_run_number=17,
                           cutoff_reached=True, stop_reason='target-pairs', next_slot=9, next_arm='E', pending_first_arm=False))
        root = Path(tmp)/'state-g'
        root.mkdir()
        # Seven pairs plus isolated failures and one final failed pair use 20 runs.
        number = 0
        for slot in range(1, 8):
            arms = ('E', 'L') if slot % 2 else ('L', 'E')
            if slot <= 4:
                number += 1
                make(number, arms[0], slot, lambda p,r:r.update(rc=16))
            for arm in arms:
                number += 1
                make(number, arm, slot)
        make(19, 'L', 8)
        make(20, 'E', 8, lambda p,r:r.update(rc=16))
        state_cli('g', dict(runs_seen=20, valid_pairs=7, next_run_number=21,
                           cutoff_reached=True, stop_reason='max-runs', next_slot=8, next_arm='L', pending_first_arm=False))
        root = Path(tmp)/'state-h'
        root.mkdir()
        make(1, 'E')
        make(2, 'L', change=different_digest)
        make(3, 'E', change=different_digest)
        make(4, 'E', change=different_digest)
        state_cli('h', dict(runs_seen=4, valid_pairs=0, next_run_number=5,
                           cutoff_reached=True, stop_reason='series-invalid', next_slot=1, next_arm='E', pending_first_arm=False))
        root = Path(tmp)/'state-i'
        root.mkdir()
        make(2, 'E')
        state_cli('i', dict(runs_seen=1, valid_pairs=0, next_run_number=2,
                           cutoff_reached=True, stop_reason='sequence-violation', next_slot=1, next_arm='E', pending_first_arm=False))
        root = Path(tmp)/'state-duplicate'
        root.mkdir()
        make(1, 'E')
        make(1, 'L')
        state_cli('duplicate', dict(cutoff_reached=True, stop_reason='sequence-violation'))
        for bad_root, bad_registry, options in ((Path(tmp)/'absent', registry, ()),
                (root, registry, ('--max-runs', '0')), (root, root, ())):
            completed = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                '--series-state', str(bad_root), '--measurement-tip', 'tip',
                '--consumer-nodes', str(bad_registry), *options], capture_output=True, text=True)
            assert completed.returncode == 2 and not completed.stdout
        # Series-only checks: each standalone run is valid but cannot join a pair.
        root = Path(tmp)/'worktree-binding'
        root.mkdir()
        make(1, 'E')
        def other_tree(p, r):
            r['worktree_realpath'] = '/other/worktree'
            for shard in range(3):
                dispatch = p/f'session/shard-{shard}/dispatch'
                edit_json(dispatch/'request.json', lambda d:d.update(repo_root='/other/worktree'))
                rebind_request(dispatch)
        cli(make(2, 'L', change=other_tree), 'success')
        checked = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
        assert not checked['pairs'] and 'worktree_realpath mismatch' in checked['runs'][1]['reasons']
        state_cli('worktree', dict(valid_pairs=0, next_slot=1, next_arm='E',
                                  pending_first_arm=False, cutoff_reached=False))
        root = Path(tmp)/'time-overlap'
        root.mkdir()
        make(1, 'E')
        cli(make(2, 'L', change=lambda p,r:r.update(submitted_at='2023-11-14T22:30:00+00:00')), 'success')
        checked = analyze(root, 'tip', {'test_a.py::test_a'}, mc=False)
        assert not checked['pairs'] and 'nonmonotonic/overlapping attempts' in checked['runs'][1]['reasons']
        state_cli('overlap', dict(valid_pairs=0, next_slot=1, next_arm='E',
                                 pending_first_arm=False, cutoff_reached=False))
        # Equal instants in different UTC offsets preserve all elapsed metrics.
        root = Path(tmp)/'offset'
        root.mkdir()
        good = make(1, 'E')
        before, _ = shard_metrics(good/'session/shard-0')
        xml = good/'session/shard-0/junit.xml'
        from datetime import timedelta
        shifted = datetime.fromtimestamp(before['epoch'], timezone(timedelta(hours=9))).isoformat()
        xml.write_text(xml.read_text().replace(before['timestamp'], shifted))
        after, _ = shard_metrics(good/'session/shard-0')
        assert all(before[key] == after[key] for key in ('H', 'D', 'tail'))
        try:
            wilcoxon([1]*21)
        except ValueError:
            pass
        else:
            raise AssertionError('m > 20 must be rejected')
        power = sensitivity(st.stdev(cases[-1][0]), 6)
        assert len(power) == 6 and all(0 <= row['power'] <= 1 and row['R'] == 2000 for row in power)
        result['sensitivity'] = power
        write_analysis(result, root/'analysis-output')
        assert read_json(root/'analysis-output/analysis.json')['status'] == '未達'
        assert '## 感度' in (root/'analysis-output/analysis.md').read_text()
    print('selftest: PASS (5 statistical counterexamples, v2 artifacts, sequence/cutoff, diagnostic, check-run and series-state CLI cases)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runs-root', 'measurement-tip', 'out', 'consumer-nodes', 'other-sessions-root', 'window', 'dump-consumers', 'check-run', 'series-state'):
        parser.add_argument('--'+name)
    parser.add_argument('--target-pairs', type=int, default=8)
    parser.add_argument('--max-runs', type=int, default=20)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if args.dump_consumers:
        print(json.dumps(dump_consumers(args.dump_consumers), indent=2))
        return
    if not args.measurement_tip or not args.consumer_nodes:
        parser.error('measurement-tip and consumer-nodes required')
    try:
        registries = read_json(args.consumer_nodes)
        if not isinstance(registries, dict) or any(
                not isinstance(registries.get(key), list)
                or not all(isinstance(node, str) for node in registries[key])
                for key in ('RECEIPT_MEMO_CONSUMER_NODES', 'ORACLE_ENVIRONMENT_CONSUMER_NODES')):
            raise ValueError('consumer-nodes requires both nodeid registries')
        consumers = consumer_set(registries)
        if args.series_state:
            state = inspect_series(args.series_state, args.measurement_tip, consumers,
                                   args.target_pairs, args.max_runs)[3]
            print(json.dumps(state, ensure_ascii=False, allow_nan=False))
            return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.error(str(exc))
    if args.check_run:
        row = inspect_run(Path(args.check_run), args.measurement_tip, consumers)
        print(json.dumps(row, ensure_ascii=False, allow_nan=False))
        return 0 if row['valid'] else 1
    if not args.runs_root or not args.out or not 1 <= args.target_pairs <= 20 or args.max_runs < 1:
        parser.error('runs-root and out required; target-pairs must be 1..20; max-runs must be positive')
    data = analyze(args.runs_root, args.measurement_tip, consumers, args.target_pairs, args.max_runs)
    if 'source_sha256' in registries:
        data['source_sha256'] = registries['source_sha256']
    if args.other_sessions_root:
        if args.window:
            window = [timestamp(v) for v in args.window.split(',')]
            if len(window) != 2 or window[1] < window[0]:
                parser.error('window must be START,END with offsets')
        else:
            bounds = [r for r in data['runs'] if 'start' in r and 'end' in r]
            window = [min(r['start'] for r in bounds), max(r['end'] for r in bounds)] if bounds else [0, 0]
        data['descriptive_control'] = descriptive(args.other_sessions_root, window, {r.get('session_dir_origin') for r in data['runs']})
    write_analysis(data, Path(args.out))


if __name__ == '__main__':
    sys.exit(main())

```

## `probe/t2700_history_estimate.py` (sha256 `3aa4909d301a…`)

```python
"""Descriptive historical memo-prewarm distributions; hypothesis formation only."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
import statistics as st
import xml.etree.ElementTree as ET

PREFIX = 'IZANAGI_MEMO_PREWARM_V1 '
HOOKS = ('xdist_node_collection_finished', 'configure_node')


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('missing/nonfinite metric')
    return value


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(n=0)
    def quantile(p):
        position = (len(values)-1)*p
        lo, hi = math.floor(position), math.ceil(position)
        return values[lo] + (values[hi]-values[lo])*(position-lo)
    return dict(n=len(values), median=st.median(values), mean=st.mean(values),
                sd=st.stdev(values) if len(values)>1 else None,
                p10=quantile(.1), p90=quantile(.9), min=min(values), max=max(values))


def extract(path, witness):
    shard = path.parents[2]
    with (shard/'report.json').open() as source:
        report = json.load(source)
    if report.get('shard_count') != 3:
        raise ValueError('shard_count != 3')
    if report.get('pytest_rc') != 0:
        raise ValueError('pytest_rc != 0')
    with (shard/'junit.xml').open('rb') as source:
        suite = next(element for _, element in ET.iterparse(source, events=('start',)) if element.tag == 'testsuite')
    stamp = datetime.fromisoformat(suite.attrib['timestamp'])
    if stamp.utcoffset() is None:
        raise ValueError('timestamp missing offset')
    start = stamp.timestamp()
    wall = number(float(suite.attrib['time']))
    timeline = report.get('session_timeline')
    if not timeline or not timeline.get('workers'):
        raise ValueError('timeline missing')
    workers = timeline['workers'].values()
    first = min(number(w['first_test_started_epoch_s']) for w in workers)
    last = max(number(w['last_test_finished_epoch_s']) for w in workers)
    occupancy = report['worker_occupancy']
    occupied = max(number(w['duration_s']) for w in occupancy.values())
    repo_sha = None
    try:
        request = json.loads((path.parent/'receipt.json').read_text()).get('request', {})
        # request.sha256 is the request payload hash, NOT the repository SHA.
        for key in ('repo_sha', 'tip_sha', 'measurement_tip', 'head_sha', 'git_sha'):
            if isinstance(request.get(key), str) and len(request[key]) == 40:
                repo_sha = request[key]
                break
        if repo_sha is None:
            repo_sha = request.get('runner_binding', {}).get('tested_main')
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return dict(effective_scheduler=report.get('effective_scheduler', '取得不能'), repo_sha=repo_sha or '取得不能', session=str(shard.parent), shard=report['shard_index'], hook=witness['hook'],
                timestamp=suite.attrib['timestamp'], epoch=start, hostname=suite.attrib['hostname'],
                W=wall, O=occupied, F=wall-occupied, H=number(timeline['collection_finished_epoch_s'])-start,
                D=first-start, tail=wall-(last-start), rm=number(witness['receipt_memo_s']))


def estimate(root, e_limit):
    candidates, scan_excluded = [], Counter()
    paths = sorted(root.glob('*/shard-*/dispatch/shard-*/izdw-shard-*.e*'))
    for path in paths:
        try:
            witnesses = [json.loads(line[len(PREFIX):]) for line in path.read_text(errors='replace').splitlines() if line.startswith(PREFIX)]
            if len(witnesses) != 1:
                scan_excluded['witness missing/multiple'] += 1
                continue
            if witnesses[0].get('hook') not in HOOKS:
                scan_excluded['other hook'] += 1
                continue
            candidates.append((path, witnesses[0], path.stat().st_mtime))
        except (OSError, ValueError) as exc:
            scan_excluded[type(exc).__name__] += 1
    e = sorted((x for x in candidates if x[1]['hook'] == 'configure_node'), key=lambda x:(x[2], str(x[0])))
    selected = [x for x in candidates if x[1]['hook'] == HOOKS[0]] + (e[-e_limit:] if e_limit else [])
    exclusions, rows = [], []
    for path, witness, _ in selected:
        try:
            rows.append(extract(path, witness))
        except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError) as exc:
            exclusions.append(dict(path=str(path), hook=witness['hook'], reason=str(exc), type=type(exc).__name__))
    groups = defaultdict(list)
    for row in rows:
        groups[(row['hook'], row['shard'])].append(row)
    summaries = []
    for hook in HOOKS:
        for shard in range(3):
            group = groups[(hook, shard)]
            summaries.append(dict(hook=hook, shard=shard, n=len(group), sessions=len({r['session'] for r in group}),
                                  hostname_types=len({r['hostname'] for r in group}),
                                  effective_scheduler=dict(Counter(r['effective_scheduler'] for r in group)),
                                  repo_sha=dict(Counter(r['repo_sha'] for r in group)),
                                  date_range=[min(group, key=lambda r:r['epoch'])['timestamp'], max(group, key=lambda r:r['epoch'])['timestamp']] if group else [],
                                  metrics={key:distribution([r[key] for r in group]) for key in ('H','D','W','O','F','tail','rm')}))
    return dict(root=str(root), e_limit=e_limit, stderr_scanned=len(paths), scan_exclusions=dict(scan_excluded),
                candidates_by_hook=dict(Counter(w['hook'] for _,w,_ in candidates)),
                selected=len(selected), e_older_excluded=max(0,len(e)-e_limit), included=len(rows),
                excluded=len(exclusions), exclusion_reasons=dict(Counter(r['reason'] for r in exclusions)),
                effective_scheduler=dict(Counter(r['effective_scheduler'] for r in rows)),
                repo_sha=dict(Counter(r['repo_sha'] for r in rows)),
                sessions=len({r['session'] for r in rows}), hostname_types=len({r['hostname'] for r in rows}),
                date_range=[min(rows,key=lambda r:r['epoch'])['timestamp'],max(rows,key=lambda r:r['epoch'])['timestamp']] if rows else [],
                summaries=summaries, rows=rows, exclusions=exclusions,
                note='Hypothesis formation only; E は適合前 N 件: stderr mtime の直近 N 件を選んでから適合判定する (適合後 N 件へ補充しない)。 SD is sample SD; quantiles use linear interpolation. H includes E waiting; D-H is not pure resolution time.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/work/1/SFC/tanab/.izanagi-acceptance-shards'))
    parser.add_argument('--e-limit', type=int, default=60)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.e_limit < 0 or not args.root.is_dir():
        parser.error('root must exist and e-limit must be nonnegative')
    result = estimate(args.root, args.e_limit)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'history.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    lines = ['## 抽出', result['note'], json.dumps({k:v for k,v in result.items() if k not in ('rows','summaries','exclusions')}, ensure_ascii=False, indent=2)]
    for summary in result['summaries']:
        lines += [f'## {summary["hook"]} / shard-{summary["shard"]}',
                  json.dumps({k:v for k,v in summary.items() if k not in ('metrics', 'effective_scheduler', 'repo_sha')}, ensure_ascii=False), '']
        for field in ('effective_scheduler', 'repo_sha'):
            lines += ['| '+field+' | 件数 |', '| --- | --- |']
            lines += ['| '+str(value)+' | '+str(count)+' |' for value, count in summary[field].items()]
            lines.append('')
        lines += ['| metric | n | median | mean | sd | p10 | p90 | min | max |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for key, values in summary['metrics'].items():
            lines.append('| '+key+' | '+' | '.join(str(values.get(k,'')) for k in ('n','median','mean','sd','p10','p90','min','max'))+' |')
    (args.out/'history.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:result[k] for k in ('stderr_scanned','selected','included','excluded','sessions')}))


if __name__ == '__main__':
    main()

```

## `run-measure.sh` (sha256 `8937a44d4839…`)

```bash
#!/bin/bash
# dev-wave-t2700-prewarm-ab 測定走 (門番 + 直接投入) v2 (段 6 レビュー B3/B4/B6 を反映)。codex/detach.sh または run-series.sh 経由で呼ぶ。
#  usage: run-measure.sh <NN> <E|L> <pair-slot>
#  形: 同一 SHA (MEASUREMENT_TIP) の wave worktree から IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py
#      を直接投入 (D2164 決定 1。待ち手 dev_wave_wait.py acceptance は claim 直後に main を取り込み tip が変わるので測定には使わない)。
#  E = 早期起動あり (現行、env は空文字を明示 export)。L = 早期起動なし (IZANAGI_T2700_EARLY_MEMO_OFF_V1=t2700-early-memo-off を export)。
#  PYTHONDONTWRITEBYTECODE は明示 unset (計算ノード既定の "1" に委ねる。warm-up だけが空文字を渡した)。
#  直列化: job dir の flock を最初に取り、門番待ち → 投入 → 成果物保存 → run.json まで保持する。取れなければ rc=94 (何も作らない)。
#  RUN dir: 門番が開き投入直前照合を通った時点で mkdir (既存なら失敗 = 同一 NN の再利用拒否)。それ以前の停止は aborts/ に記録。
#  門番: 他 session の受入待ち手 (dev_wave_wait.py … acceptance、自 slug 除外) <= LEADERS_MAX (v2 は 1、10:13 に投入前・結果を見る前に 2 へ緩和: 他 wave 2 本の受入がほぼ常時で 63 分開かず) かつ 1 分 load < L1_MAX を
#        100〜140 秒乱数周期で判定し、2 回連続で開いていたら 0〜45 秒乱数待ち → 再判定 → 投入。
#  複製 (必須): 3 shard の junit.xml / report.json / dispatch/{receipt,request,result}.json / dispatch/izdw-shard-N.{e,o}<job> を
#        session/shard-N/ と session/shard-N/dispatch/ へ平坦化して複製し、file ごとに ok / missing-at-origin / copy-failed / hash-mismatch を
#        artifacts.txt に記録、複製できた file は SHA256SUMS に載せる。任意: shard-N/dispatcher.log、session root の login-collection.log / junit.xml。
#  終了 rc: 子 rc が 0 でも必須複製・sha・run.json 生成に失敗したら 96/97 (子 rc は run.json の rc に別記)。失敗走 (rc=16 等) でも run.json と log を残す。
set -u
JOBDIR=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab
WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2700-prewarm-ab
SLUG=dev-wave-t2700-prewarm-ab
MEASUREMENT_TIP=$(cat "$JOBDIR/measurement-tip.txt" 2>/dev/null)
OPT_OUT_ENV=IZANAGI_T2700_EARLY_MEMO_OFF_V1
OPT_OUT_TOKEN=t2700-early-memo-off
NN=${1:?run number (2 digits)}
COND=${2:?E or L}
SLOT=${3:?pair slot}
TAG="$NN-$COND"
RUN="$JOBDIR/runs/$TAG"
LEADERS_MAX=2
L1_MAX=30
GATE_MAX_ROUNDS=90
mkdir -p "$JOBDIR/runs" "$JOBDIR/aborts"
STAMP=$(date '+%Y%m%dT%H%M%S')
ABORT="$JOBDIR/aborts/$TAG-$STAMP.log"
abort() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $2" >> "$ABORT"; exit "$1"; }
if [ "$COND" != "E" ] && [ "$COND" != "L" ]; then abort 2 "bad condition: $COND"; fi
if [ -z "$MEASUREMENT_TIP" ]; then abort 2 "measurement-tip.txt missing"; fi

exec 9> "$JOBDIR/measure.lock"
if ! flock -n 9; then abort 94 "another measurement holds the lock"; fi
if [ -e "$RUN" ]; then abort 2 "run dir exists (attempt reuse refused): $RUN"; fi

export IZANAGI_ACCEPTANCE_SHARDS=3
unset PYTHONDONTWRITEBYTECODE
# E は空文字を明示 export (allowlist 経由で request に載り、compute 側の残留を空で上書きする。段 3 相談 B2)。L は exact token。
if [ "$COND" = "L" ]; then export "$OPT_OUT_ENV=$OPT_OUT_TOKEN"; else export "$OPT_OUT_ENV="; fi
cd "$WT" || abort 90 "cd failed"
WT_REAL=$(realpath "$WT")

count_leaders() { ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG"; }
load1() { read -r l1 _ < /proc/loadavg; echo "$l1"; }
dirty_lines() { git status --porcelain --untracked-files=all --ignore-submodules=none | wc -l; }
glog() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$JOBDIR/aborts/$TAG-$STAMP.gate.log"; }

gate_open() {
  l1=$(load1)
  leaders=$(count_leaders)
  glog "gate: load1=$l1 leaders=$leaders (max $LEADERS_MAX, l1 < $L1_MAX)"
  python3 "$JOBDIR/gate_check.py" "$l1" "$leaders" "$LEADERS_MAX" "$L1_MAX"
}

round=0; stable=0; opened=0
while [ "$round" -lt "$GATE_MAX_ROUNDS" ]; do
  round=$((round + 1))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  stable=$((stable + 1))
  if [ "$stable" -lt 2 ]; then sleep $((100 + RANDOM % 41)); continue; fi
  sleep $((RANDOM % 46))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  opened=1
  break
done
if [ "$opened" -ne 1 ]; then abort 93 "gate never opened"; fi

TIP=$(git rev-parse HEAD)
DIRTY_BEFORE=$(dirty_lines)
if [ "$TIP" != "$MEASUREMENT_TIP" ]; then abort 95 "HEAD $TIP != measurement tip $MEASUREMENT_TIP"; fi
if [ "$DIRTY_BEFORE" -ne 0 ]; then abort 91 "worktree dirty before launch ($DIRTY_BEFORE lines)"; fi

if ! mkdir "$RUN"; then abort 2 "mkdir failed (exists?): $RUN"; fi
CHAIN="$RUN/chain.log"
echo $$ > "$RUN/measure.pid"
mv "$JOBDIR/aborts/$TAG-$STAMP.gate.log" "$RUN/gate.log" 2>/dev/null
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$CHAIN"; }
MAIN=$(git rev-parse refs/heads/main)
LEADERS=$(count_leaders)
L1=$(load1)
WARM_TIP=$(cat "$JOBDIR/warm.tip.txt" 2>/dev/null)
WARM_RC=$(cat "$JOBDIR/warm.done" 2>/dev/null)
START=$(date '+%Y-%m-%dT%H:%M:%S%z')
log "launch: cond=$COND slot=$SLOT tip=$TIP main=$MAIN leaders=$LEADERS load1=$L1 worktree=$WT_REAL warm_tip=$WARM_TIP warm_rc=$WARM_RC"
env | grep '^IZANAGI_\|^PYTHONDONTWRITEBYTECODE' > "$RUN/env.txt"
echo "PYTHONDONTWRITEBYTECODE_SET=$( [ -n "${PYTHONDONTWRITEBYTECODE+x}" ] && echo yes || echo no )" >> "$RUN/env.txt"
python3 tools/run_tests.py > "$RUN/child.log" 2>&1
rc=$?
END=$(date '+%Y-%m-%dT%H:%M:%S%z')
ROOT=$(grep -o '"session_root":"[^"]*"' "$RUN/child.log" | head -1 | cut -d'"' -f4)
DIRTY_AFTER=$(dirty_lines)
TIP_AFTER=$(git rev-parse HEAD)
log "finished: child_rc=$rc session_root=$ROOT dirty_after=$DIRTY_AFTER tip_after=$TIP_AFTER"

# 複製: file ごとに状態を artifacts.txt へ (<相対 path> <ok|missing-at-origin|copy-failed|hash-mismatch> <required|optional>)。
ART="$RUN/artifacts.txt"
: > "$ART"
COPY_OK=1
copy_one() {
  # usage: copy_one <origin abs> <dest rel (under session/)> <required|optional>
  local src=$1 rel=$2 req=$3 dst a b
  dst="$RUN/session/$rel"
  if [ ! -f "$src" ]; then
    echo "$rel missing-at-origin $req" >> "$ART"
    if [ "$req" = required ]; then COPY_OK=0; fi
    return
  fi
  mkdir -p "$(dirname "$dst")"
  if ! cp "$src" "$dst"; then
    echo "$rel copy-failed $req" >> "$ART"
    if [ "$req" = required ]; then COPY_OK=0; fi
    return
  fi
  a=$(sha256sum "$src" | cut -d' ' -f1); b=$(sha256sum "$dst" | cut -d' ' -f1)
  if [ "$a" != "$b" ]; then
    echo "$rel hash-mismatch $req" >> "$ART"
    if [ "$req" = required ]; then COPY_OK=0; fi
    return
  fi
  echo "$b  $rel" >> "$RUN/session/SHA256SUMS"
  echo "$rel ok $req" >> "$ART"
}
if [ -n "$ROOT" ] && [ -d "$ROOT" ]; then
  mkdir -p "$RUN/session"
  for s in 0 1 2; do
    for f in junit.xml report.json; do copy_one "$ROOT/shard-$s/$f" "shard-$s/$f" required; done
    for f in receipt.json request.json result.json; do copy_one "$ROOT/shard-$s/dispatch/shard-$s/$f" "shard-$s/dispatch/$f" required; done
    n_e=0; n_o=0
    for f in "$ROOT/shard-$s/dispatch/shard-$s"/izdw-shard-$s.e*; do
      if [ -f "$f" ]; then copy_one "$f" "shard-$s/dispatch/$(basename "$f")" required; n_e=$((n_e + 1)); fi
    done
    for f in "$ROOT/shard-$s/dispatch/shard-$s"/izdw-shard-$s.o*; do
      if [ -f "$f" ]; then copy_one "$f" "shard-$s/dispatch/$(basename "$f")" required; n_o=$((n_o + 1)); fi
    done
    if [ "$n_e" -ne 1 ]; then echo "shard-$s/dispatch/izdw-shard-$s.e* count=$n_e required" >> "$ART"; COPY_OK=0; fi
    if [ "$n_o" -ne 1 ]; then echo "shard-$s/dispatch/izdw-shard-$s.o* count=$n_o required" >> "$ART"; COPY_OK=0; fi
    copy_one "$ROOT/shard-$s/dispatcher.log" "shard-$s/dispatcher.log" optional
  done
  copy_one "$ROOT/junit.xml" "junit.xml" optional
  copy_one "$ROOT/login-collection.log" "login-collection.log" optional
else
  echo "session-root missing-at-origin required" >> "$ART"
  COPY_OK=0
fi
log "copy_ok=$COPY_OK"
python3 "$JOBDIR/write_run_json.py" "$RUN/run.json" "$COND" "$TIP" "$MAIN" "$START" "$END" "$ROOT" "$LEADERS" "$L1" "$rc" "$DIRTY_BEFORE" "$DIRTY_AFTER" "$TIP_AFTER" "$NN" "$SLOT" "$COPY_OK" "$MEASUREMENT_TIP" "$LEADERS_MAX" "$L1_MAX" "$WT_REAL" "$WARM_TIP" "$WARM_RC"
json_rc=$?
final=$rc
if [ "$json_rc" -ne 0 ]; then final=97; log "run.json generation failed rc=$json_rc"; fi
if [ "$COPY_OK" -ne 1 ] && [ "$final" -eq 0 ]; then final=96; log "copy failed with child rc=0"; fi
echo "$final" > "$RUN/measure.done"
exit "$final"

```

## `run-series.sh` (sha256 `70be741a1e83…`)

```bash
#!/bin/bash
# 親専用: 測定走の連結 v3 (焦点再レビュー B1 を反映)。detach.sh 経由で呼ぶ。usage: run-series.sh <series-tag>
# 規則 (結果を見る前に固定、集計器 `--series-state` が唯一の判定主体):
#  - 各走の前に `t2700_ab_analyze.py --series-state runs` を呼び、次に投入する走番号・slot・腕を受け取る。
#    (slot k の順序は k が奇数なら E,L、偶数なら L,E。slot 内のどちらかが無効 (単走検算・系列検算とも) なら同 slot を同順序で取り直す。
#     有効 8 対 or 20 走で cutoff。同 slot の取り直しが 3 回連続で無効なら series-invalid で停止 = 親が介入。)
#  - run-measure.sh が RUN dir を作らずに終わった (投入前 abort: lock / 門番 / tip / dirty) 場合は走番号を消費せず、系列を rc=93 で止める
#    (親が原因を見て同 tag で再起動する。状態は runs/ の実体だけから再計算されるので file 状態は持たない)。
#  - 投入前条件: warm.done == 0 かつ warm.tip.txt == measurement-tip.txt (B6)。不成立なら投入せず rc=92。
set -u
TAG=${1:?series tag}
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab
TARGET_PAIRS=8
MAX_RUNS=20
echo $$ > "$J/$TAG.pid"
rm -f "$J/$TAG.done"
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$J/$TAG.log"; }
MTIP=$(cat "$J/measurement-tip.txt")
WTIP=$(cat "$J/warm.tip.txt" 2>/dev/null)
WRC=$(cat "$J/warm.done" 2>/dev/null)
if [ "$WRC" != "0" ] || [ "$WTIP" != "$MTIP" ]; then log "precondition failed: warm_rc=$WRC warm_tip=$WTIP measurement_tip=$MTIP"; echo 92 > "$J/$TAG.done"; exit 92; fi
mkdir -p "$J/runs"
log "$TAG start: target=$TARGET_PAIRS max_runs=$MAX_RUNS tip=$MTIP"
state_file="$J/$TAG.state.json"
series_state() {
  python3 "$J/probe/t2700_ab_analyze.py" --series-state "$J/runs" --measurement-tip "$MTIP" --consumer-nodes "$J/consumer-nodes.json" --target-pairs "$TARGET_PAIRS" --max-runs "$MAX_RUNS" > "$state_file" 2>> "$J/$TAG.state.err"
}
field() { python3 "$J/json_field.py" "$state_file" "$1"; }
while true; do
  if ! series_state; then log "series-state failed (rc=$?), stopping"; echo 95 > "$J/$TAG.done"; exit 95; fi
  cp "$state_file" "$J/$TAG.state.$(date '+%H%M%S').json"
  cutoff=$(field cutoff_reached); reason=$(field stop_reason); pairs=$(field valid_pairs); seen=$(field runs_seen)
  nn=$(field next_run_number); slot=$(field next_slot); arm=$(field next_arm)
  log "state: runs_seen=$seen valid_pairs=$pairs cutoff=$cutoff reason=$reason next=$nn-$arm slot=$slot"
  if [ "$cutoff" = "True" ] || [ "$cutoff" = "true" ]; then log "cutoff reached ($reason)"; break; fi
  NN=$(printf '%02d' "$nn")
  log "launch $NN-$arm slot $slot"
  bash "$J/run-measure.sh" "$NN" "$arm" "$slot"
  rc=$?
  log "$NN-$arm rc=$rc"
  if [ ! -d "$J/runs/$NN-$arm" ]; then log "pre-launch abort (no run dir) rc=$rc — stopping without consuming a run number"; echo 93 > "$J/$TAG.done"; exit 93; fi
done
log "$TAG end: valid_pairs=$pairs runs_seen=$seen"
echo 0 > "$J/$TAG.done"
exit 0

```

## `run-warm.sh` (sha256 `345217002605…`)

```bash
#!/bin/bash
# 親専用: collect-only を 1 回走らせ orchestrator/tests/__pycache__ を温める (T-2710 §4、T-2766 §4)。
# login の admission が headroom 0 で dispatch へ倒れるため、PYTHONDONTWRITEBYTECODE を空 (= 「書かない」指定を外す) で
# allowlist 経由で計算ノードへ渡し、共有 FS の __pycache__ へ pytest の書換 pyc を書かせる。測定走にはこの env を渡さない。
# v2: 実行時の HEAD を warm.tip.txt に記録し、run-series.sh が測定 tip と一致し rc=0 であることを投入前条件にする (段 6 レビュー B6)。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab
W=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2700-prewarm-ab
echo $$ > "$J/warm.pid"
rm -f "$J/warm.done"
cd "$W" || { echo 90 > "$J/warm.done"; exit 90; }
git rev-parse HEAD > "$J/warm.tip.txt"
export PYTHONDONTWRITEBYTECODE=
date '+%Y-%m-%dT%H:%M:%S%z' > "$J/warm.started.txt"
python3 tools/run_tests.py --collect-only -q -p no:cacheprovider > "$J/warm.log" 2>&1
rc=$?
date '+%Y-%m-%dT%H:%M:%S%z' > "$J/warm.finished.txt"
find orchestrator/tests/__pycache__ -name '*.pyc' 2>/dev/null | wc -l > "$J/warm.pyc-count.txt"
echo "$rc" > "$J/warm.done"
exit "$rc"

```

## `write_run_json.py` (sha256 `88921438f231…`)

```python
"""run-measure.sh が走ごとに書く run.json v2 (heredoc を避けて file に置く)。artifacts.txt を dict に畳む。"""
import json, os, sys
(path, cond, tip, main, start, end, root, leaders, l1, rc, dirty_before, dirty_after, tip_after, nn, slot, copy_ok,
 mtip, lmax, l1max, wt_real, warm_tip, warm_rc) = sys.argv[1:]
run_dir = os.path.dirname(path)
env = {}
for line in open(os.path.join(run_dir, "env.txt")):
    k, _, v = line.rstrip("\n").partition("=")
    env[k] = v
artifacts = {}
art_path = os.path.join(run_dir, "artifacts.txt")
if os.path.exists(art_path):
    for line in open(art_path):
        parts = line.rstrip("\n").split(" ")
        if len(parts) >= 3:
            artifacts[parts[0]] = {"status": parts[1], "requirement": parts[2]}
json.dump({
    "schema": "t2700-run/v2",
    "run": nn, "condition": cond, "pair_slot": int(slot),
    "measurement_tip": mtip, "tip_sha": tip, "tip_sha_after": tip_after,
    "main_sha_at_launch": main,
    "worktree_realpath": wt_real,
    "warm_tip": warm_tip or None, "warm_rc": (int(warm_rc) if warm_rc.strip().lstrip("-").isdigit() else None),
    "submitted_at": start, "finished_at": end,
    "session_dir": "session" if copy_ok == "1" else None,
    "session_dir_origin": root or None, "copy_ok": copy_ok == "1",
    "artifacts": artifacts,
    "env": env, "other_leaders": int(leaders), "load1": float(l1), "rc": int(rc),
    "dirty_lines_before": int(dirty_before), "dirty_lines_after": int(dirty_after),
    "gate": {"leaders_max": int(lmax), "load1_max_exclusive": float(l1max),
             "leader_query": "ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc <slug>"},
    "opt_out_env": "IZANAGI_T2700_EARLY_MEMO_OFF_V1", "opt_out_token": "t2700-early-memo-off",
}, open(path, "w"), indent=2, ensure_ascii=True)

```

## `gate_check.py` (sha256 `4a671af2f387…`)

```python
"""run-measure.sh の門番判定 (heredoc を避けて file に置く)。argv: l1 leaders leaders_max l1_max。開いていれば rc=0。"""
import sys
l1, leaders, lmax, l1max = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
sys.exit(0 if (leaders <= lmax and l1 < l1max) else 1)

```

## `run-mutation.sh` (sha256 `850d5088b7f5…`)

```bash
#!/bin/bash
# 親専用: 変異 harness を独立 clone (D1009) の固定 commit で走らせる。detach.sh 経由で呼ぶ。
# usage: run-mutation.sh <tag> <spec> <spec-sha256> <wrapper-attempt>
set -u
TAG=${1:?tag}
SPEC=${2:?spec}
SHA=${3:?spec sha256}
ATT=${4:?wrapper attempt}
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab
SRC="$J/mutation-source"
COMMIT=$(cat "$J/measurement-tip.txt")
mkdir -p "$J/mutation-scratch"
echo $$ > "$J/mutation-$TAG.pid"
rm -f "$J/mutation-$TAG.done"
cd "$SRC" || { echo 90 > "$J/mutation-$TAG.done"; exit 90; }
export IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600
export IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600
python3 tools/mutation_worktree.py --source-repo "$SRC" --commit "$COMMIT" \
  --scratch-root "$J/mutation-scratch" \
  --spec "$SPEC" --expected-spec-sha256 "$SHA" \
  --out "$J/mutation-$TAG-results.json" \
  --attempt-out "$J/mutation-$TAG-attempts.json" --wrapper-attempt "$ATT" \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_real_repo_serialization.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf \
  > "$J/mutation-$TAG.log" 2>&1
rc=$?
echo "$rc" > "$J/mutation-$TAG.done"
exit "$rc"

```

## `verbatim/power_rule.py` (sha256 `fb25bd155c20…`)

```python
"""判定規則そのもの (Wilcoxon 符号順位 exact 片側 p <= 0.05 かつ 標本中央値 >= 15 秒) の検出力を MC で出す。
対差 = δ + 誤差。誤差は (a) 正規 N(0, σ_d)、(b) 右裾: 正規 + 確率 0.15 で L 側に +30〜+90 秒の遅延 (load の裾) を混ぜた非対称。
同順位は平均順位、0 差は除外 (m = 非 0 の数)、m == 0 は判定不能。"""
import itertools, math, random, statistics as st
random.seed(20260920)
R = 4000

def wilcoxon_one_sided_exact(d):
    nz = [x for x in d if x != 0]
    m = len(nz)
    if m == 0:
        return None
    absd = sorted(abs(x) for x in nz)
    # 平均順位
    ranks = {}
    i = 0
    while i < m:
        j = i
        while j + 1 < m and absd[j + 1] == absd[i]:
            j += 1
        r = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            ranks.setdefault(absd[k], []).append(r)
        i = j + 1
    rk = {}
    for v, rs in ranks.items():
        rk[v] = rs[0]
    wplus = sum(rk[abs(x)] for x in nz if x > 0)
    # 帰無: 各符号が独立に ±、W+ の分布を全列挙 (m <= 12)
    rlist = [rk[abs(x)] for x in nz]
    count = 0; total = 0
    for signs in itertools.product((0, 1), repeat=m):
        w = sum(r for r, s in zip(rlist, signs) if s)
        total += 1
        if w >= wplus - 1e-9:
            count += 1
    return count / total

def rule(d, thr=15.0):
    p = wilcoxon_one_sided_exact(d)
    if p is None:
        return 'indeterminate'
    med = st.median(d)
    if p <= 0.05 and med >= thr:
        return 'support'
    if p <= 0.05:
        return 'direction-only'
    return 'not-established'

def sample(delta, sd, n, skew):
    out = []
    for _ in range(n):
        x = delta + random.gauss(0, sd)
        if skew and random.random() < 0.15:
            x += random.uniform(30, 90)   # L の走が load の裾を踏む
        if skew and random.random() < 0.15:
            x -= random.uniform(30, 90)   # E の走が裾を踏む
        out.append(x)
    return out

print('rule = Wilcoxon one-sided exact p<=0.05 AND median>=15 ; R=%d' % R)
for skew in (False, True):
    print('--- error model:', 'normal' if not skew else 'normal + 15%/15% tail (+/-30..90s)')
    for delta in (0, 15, 20, 27):
        for sd in (17, 22, 25, 30):
            row = []
            for n in (6, 8, 10):
                hits = sum(1 for _ in range(R) if rule(sample(delta, sd, n, skew)) == 'support')
                row.append('n=%d:%.2f' % (n, hits / R))
            print('delta=%2d sd=%2d  ' % (delta, sd) + '  '.join(row))
# 相談の反例表
cases = {
    '+40x5, -45x1': [40, 40, 40, 40, 40, -45],
    'distinct positives 5 + largest negative': [10, 20, 30, 40, 50, -60],
    'all +5..+10': [5, 6, 7, 8, 9, 10],
    'zeros': [0, 0, 12, 20, 30, 40],
}
for name, d in cases.items():
    print(name, 'p=%s' % wilcoxon_one_sided_exact(d), 'median=%.1f' % st.median(d), rule(d))

```

## `verbatim/power.py` (sha256 `de8d7ff8c9e4…`)

```python
"""必要対数の見積り (依存なし、Monte Carlo)。
対差 ΔW ~ N(δ, σ_d²) を仮定し、対応のある t 検定 (両側 α=0.05、臨界値は H0 の MC 分位) の検出力と、
Wilcoxon 符号順位検定 (片側、exact) で「全対同符号」が与える p を n 別に出す。"""
import math, random, statistics as st
random.seed(20260920)
R = 20000
def tstat(xs):
    n = len(xs); m = st.mean(xs); s = st.stdev(xs)
    return m / (s / math.sqrt(n)) if s > 0 else float('inf')
crit = {}
for n in (3, 4, 5, 6, 7, 8, 10):
    ts = sorted(abs(tstat([random.gauss(0, 1) for _ in range(n)])) for _ in range(200000))
    crit[n] = ts[int(0.95 * len(ts))]
print('MC two-sided 5% critical |t| by n:', {n: round(c, 2) for n, c in crit.items()})
print('(reference: t(0.975, df) = 4.30, 3.18, 2.78, 2.57, 2.45, 2.36, 2.26)')
for delta in (20, 27, 35):
    for sd in (12, 17, 20, 25):
        row = []
        for n in (3, 4, 5, 6, 7, 8, 10):
            hits = 0
            for _ in range(R):
                xs = [random.gauss(delta, sd) for _ in range(n)]
                t = tstat(xs)
                if t > crit[n]:
                    hits += 1
            row.append('n=%d:%.2f' % (n, hits / R))
        print('delta=%2d sd=%2d d=%.2f  ' % (delta, sd, delta / sd) + '  '.join(row))
print('all n pairs same sign, one-sided exact p = 1/2^n:', {n: round(0.5 ** n, 4) for n in (3, 4, 5, 6, 7, 8)})
print('Wilcoxon signed-rank one-sided exact p, n=6: all positive 1/64=0.0156; one negative of smallest rank 2/64=0.0312;'
      ' one negative of rank 2 -> 3/64=0.0469; n=7: all positive 1/128=0.0078, one negative rank<=3 -> <=0.031')
# 期待される対差の観測確率 (δ=27, σ=17): 対差が負になる確率
for delta, sd in ((27, 17), (27, 20), (20, 20)):
    p_neg = 0.5 * (1 + math.erf((0 - delta) / (sd * math.sqrt(2))))
    print('P(pair negative | delta=%d, sd=%d) = %.3f ; P(all 6 positive) = %.2f' % (delta, sd, p_neg, (1 - p_neg) ** 6))

```

## `verbatim/head_stats.py` (sha256 `6235f6e16847…`)

```python
"""過去の受入 session の shard ごとに、session 開始から配布開始までの head H と prewarm hook を対応づける。
report.json は 5.8 MB 級なので、まず stderr file (安い) で hook を引き、L 経路の全 session と、
E 経路は mtime 順で直近 N session だけ report.json を読む。"""
import glob, json, os, re, statistics as st, sys, time
from collections import defaultdict
from datetime import datetime
root = '/work/1/SFC/tanab/.izanagi-acceptance-shards'
N_E = int(sys.argv[1]) if len(sys.argv) > 1 else 40
hooks = {}  # (sess, shard) -> (hook, receipt_memo_s, mtime)
for f in glob.glob(root + '/*/shard-*/dispatch/shard-*/izdw-shard-*.e*'):
    parts = f.split('/')
    sess, shard = parts[-5], parts[-4]
    hook = None; rm = None
    for line in open(f, errors='replace'):
        if 'IZANAGI_MEMO_PREWARM_V1' in line:
            j = json.loads(line.split('IZANAGI_MEMO_PREWARM_V1', 1)[1].strip())
            hook = j['hook']; rm = j.get('receipt_memo_s')
    hooks[(sess, shard)] = (hook, rm, os.path.getmtime(f))
L = sorted({k for k, v in hooks.items() if v[0] == 'xdist_node_collection_finished'}, key=lambda k: hooks[k][2])
E = sorted({k for k, v in hooks.items() if v[0] == 'configure_node'}, key=lambda k: hooks[k][2])
print('L shards', len(L), 'E shards', len(E))
def days(keys):
    return sorted({time.strftime('%m-%d', time.localtime(hooks[k][2])) for k in keys})
print('L days', days(L)); print('E days', days(E))
# E: 直近 N_E shard + L の各日と同日の E を少し (前後の比較用)
E_sel = E[-N_E:]
rows = []
def read(k):
    sess, shard = k
    shard_dir = f'{root}/{sess}/{shard}/'
    junit = shard_dir + 'junit.xml'; report = shard_dir + 'report.json'
    if not (os.path.exists(junit) and os.path.exists(report)):
        return None
    head = open(junit, errors='replace').read(600)
    m = re.search(r'<testsuite [^>]*time="([0-9.]+)" timestamp="([^"]+)" hostname="([^"]+)"', head)
    if not m:
        return None
    W = float(m.group(1)); t0 = datetime.fromisoformat(m.group(2)).timestamp(); host = m.group(3)
    try:
        d = json.load(open(report))
    except Exception:
        return None
    tl = d.get('session_timeline') or {}
    cf = tl.get('collection_finished_epoch_s')
    if cf is None:
        return None
    workers = tl.get('workers') or {}
    last = max((w.get('last_test_finished_epoch_s') or 0) for w in workers.values()) if workers else None
    occ = d.get('worker_occupancy') or {}
    O = max((v.get('duration_s') or 0) for v in occ.values()) if occ else None
    hook, rm, mt = hooks[k]
    return dict(sess=sess, shard=shard, day=time.strftime('%m-%d %H:%M', time.localtime(t0)), host=host, W=W, H=cf - t0,
                tail=(t0 + W - last) if last else None, O=O, hook=hook, rm=rm, nworkers=len(workers),
                shard_count=d.get('shard_count'), rc=d.get('pytest_rc'), sched=d.get('effective_scheduler'))
for k in L + E_sel:
    r = read(k)
    if r:
        rows.append(r)
print('rows', len(rows))
def summ(name, xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return
    q = st.quantiles(xs, n=10) if len(xs) >= 10 else [min(xs), max(xs)]
    print('  %-5s n=%3d median=%6.1f mean=%6.1f sd=%5.1f p10=%6.1f p90=%6.1f min=%6.1f max=%6.1f' % (
        name, len(xs), st.median(xs), st.mean(xs), st.pstdev(xs) if len(xs) > 1 else 0, q[0], q[-1], min(xs), max(xs)))
for hook in ('xdist_node_collection_finished', 'configure_node'):
    sel = [r for r in rows if r['hook'] == hook and r['shard_count'] == 3]
    print('hook', hook, 'shards', len(sel), 'sessions', len({r['sess'] for r in sel}), 'days', sorted({r['day'][:5] for r in sel}))
    for shard in ('shard-0', 'shard-1', 'shard-2'):
        s2 = [r for r in sel if r['shard'] == shard]
        print(' ', shard, len(s2))
        summ('H', [r['H'] for r in s2]); summ('W', [r['W'] for r in s2]); summ('O', [r['O'] for r in s2])
        summ('F', [r['W'] - r['O'] for r in s2 if r['O'] is not None]); summ('tail', [r['tail'] for r in s2]); summ('rm', [r['rm'] for r in s2])
json.dump(rows, open('/home/SFC/tanab/.claude/jobs/20f923f9/tmp/head_rows.json', 'w'), indent=0)
print('L rows detail (day, shard, host, W, H, O, rm):')
for r in sorted([r for r in rows if r['hook'] == 'xdist_node_collection_finished'], key=lambda r: r['day']):
    print('  ', r['day'], r['shard'], r['host'], '%.1f %.1f %s %.1f' % (r['W'], r['H'], ('%.1f' % r['O']) if r['O'] else '-', r['rm'] or -1), r['shard_count'], r['sched'])

```

## `verbatim/dist_start.py` (sha256 `7285ce999195…`)

```python
"""head_rows.json の session/shard について、配布開始 D = min(worker first_test_started) − session start と、
最忙 worker の (first, last) を出し、L (xdist_node_collection_finished) と E (configure_node) で比べる。"""
import json, os, re, statistics as st
from datetime import datetime
root = '/work/1/SFC/tanab/.izanagi-acceptance-shards'
rows = json.load(open('/home/SFC/tanab/.claude/jobs/20f923f9/tmp/head_rows.json'))
out = []
for r in rows:
    shard_dir = f"{root}/{r['sess']}/{r['shard']}/"
    head = open(shard_dir + 'junit.xml', errors='replace').read(600)
    m = re.search(r'timestamp="([^"]+)"', head)
    t0 = datetime.fromisoformat(m.group(1)).timestamp()
    d = json.load(open(shard_dir + 'report.json'))
    tl = d['session_timeline']; workers = tl['workers']
    firsts = [w['first_test_started_epoch_s'] - t0 for w in workers.values() if w.get('first_test_started_epoch_s')]
    lasts = [w['last_test_finished_epoch_s'] - t0 for w in workers.values() if w.get('last_test_finished_epoch_s')]
    occ = d['worker_occupancy']
    busiest = max(occ, key=lambda k: occ[k]['duration_s'])
    bw = workers.get(busiest, {})
    out.append(dict(r, D=min(firsts), Dmax=max(firsts), Lmax=max(lasts), H=tl['collection_finished_epoch_s'] - t0,
                    busiest=busiest, b_first=(bw.get('first_test_started_epoch_s') or 0) - t0,
                    b_last=(bw.get('last_test_finished_epoch_s') or 0) - t0, b_occ=occ[busiest]['duration_s'],
                    b_items=occ[busiest]['items']))
def summ(name, xs):
    xs = [x for x in xs if x is not None]
    q = st.quantiles(xs, n=10) if len(xs) >= 10 else [min(xs), max(xs)]
    print('  %-8s n=%3d median=%6.1f mean=%6.1f sd=%5.1f p10=%6.1f p90=%6.1f min=%6.1f max=%6.1f' % (
        name, len(xs), st.median(xs), st.mean(xs), st.pstdev(xs) if len(xs) > 1 else 0, q[0], q[-1], min(xs), max(xs)))
for hook in ('xdist_node_collection_finished', 'configure_node'):
    for shard in ('shard-0', 'shard-1', 'shard-2'):
        sel = [r for r in out if r['hook'] == hook and r['shard'] == shard]
        if not sel:
            continue
        print(hook, shard, len(sel))
        summ('H', [r['H'] for r in sel]); summ('D', [r['D'] for r in sel]); summ('Dmax', [r['Dmax'] for r in sel])
        summ('D-H', [r['D'] - r['H'] for r in sel]); summ('rm', [r['rm'] for r in sel])
        summ('W-Lmax', [r['W'] - r['Lmax'] for r in sel])
        summ('b_first', [r['b_first'] for r in sel]); summ('b_slack', [r['b_last'] - r['b_first'] - r['b_occ'] for r in sel])
        summ('W', [r['W'] for r in sel]); summ('O', [r['O'] for r in sel]); summ('F', [r['W'] - r['O'] for r in sel])
json.dump(out, open('/home/SFC/tanab/.claude/jobs/20f923f9/tmp/dist_rows.json', 'w'), indent=0)

```

## `verbatim/prewarm_stats.py` (sha256 `f58177d37a24…`)

```python
import glob, json, os, statistics as st, sys, time
from collections import Counter, defaultdict
root = '/work/1/SFC/tanab/.izanagi-acceptance-shards'
rows = []
for f in sorted(glob.glob(root + '/*/shard-*/dispatch/shard-*/izdw-shard-*.e*')):
    parts = f.split('/')
    sess, shard = parts[-5], parts[-4]
    mtime = os.path.getmtime(f)
    for line in open(f, errors='replace'):
        if 'IZANAGI_MEMO_PREWARM_V1' in line:
            j = json.loads(line.split('IZANAGI_MEMO_PREWARM_V1', 1)[1].strip())
            rows.append((sess, shard, mtime, j))
print('lines', len(rows), 'sessions', len({r[0] for r in rows}))
print(Counter(j['hook'] for *_, j in rows))
for hook in ('configure_node', 'collection_finish', 'xdist_node_collection_finished'):
    for key in ('barrier_s', 'receipt_memo_s', 'oracle_environment_memo_s'):
        xs = [j[key] for *_, j in rows if j['hook'] == hook and j.get(key) is not None]
        if xs:
            q = st.quantiles(xs, n=10) if len(xs) >= 10 else []
            print(hook, key, 'n=%d median=%.1f mean=%.1f sd=%.1f min=%.1f max=%.1f' % (
                len(xs), st.median(xs), st.mean(xs), st.pstdev(xs) if len(xs) > 1 else 0, min(xs), max(xs)),
                'p10=%.1f p90=%.1f' % (q[0], q[-1]) if q else '')
# by day
byday = defaultdict(list)
for sess, shard, mt, j in rows:
    if j['hook'] == 'configure_node' and j.get('receipt_memo_s') is not None:
        byday[time.strftime('%m-%d', time.localtime(mt))].append(j['receipt_memo_s'])
for d in sorted(byday):
    xs = byday[d]
    print(d, 'n=%d median=%.1f min=%.1f max=%.1f' % (len(xs), st.median(xs), min(xs), max(xs)))

```
