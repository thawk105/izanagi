# junit_scan_survey.py (逐語)

Codex author 作の受入 shard junit 集計器 (job dir で実行、repo には入れない)。出力は survey-final.md。

```python
"""Stratify t1259 JUnit scan proxies by regime and overlapping sessions."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


def percentile(values: list[float], percent: int) -> str:
    if not values:
        return '-'
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return f'{ordered[low] + (ordered[high] - ordered[low]) * (position - low):.3f}'


def union(windows: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[tuple[float, float]] = []
    for start, end in sorted(windows):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def cell(value: object) -> str:
    return str(value).replace('|', '\\|').replace('\n', ' ')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shards-root', type=Path, required=True)
    parser.add_argument('--since', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.shards_root.is_absolute():
        parser.error('--shards-root must be absolute')
    since = datetime.strptime(args.since, '%Y-%m-%d %H:%M').timestamp()
    sessions = []
    for directory in sorted(args.shards_root.iterdir()):
        if not directory.is_dir() or directory.stat().st_mtime < since:
            continue
        session = {'name': directory.name, 'windows': [], 'suites': [], 'cases': []}
        for xml in sorted(directory.glob('shard-*/junit.xml')):
            root = ET.parse(xml).getroot()
            suites = [root] if root.tag == 'testsuite' else list(root.iter('testsuite'))
            for suite in suites:
                timestamp = suite.attrib['timestamp']
                duration = float(suite.attrib['time'])
                start = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
                if xml.parent.name in {'shard-0', 'shard-1', 'shard-2'}:
                    session['windows'].append((start, start + duration))
                session['suites'].append((xml.parent.name, timestamp, duration,
                                          suite.get('hostname', '')))
                for case in suite.findall('testcase'):
                    if 'test_t1259_qsub_env_delivery_probe' not in case.get('classname', ''):
                        continue
                    nodeid = case.get('nodeid', case.get('name', ''))
                    session['cases'].append({
                        'nodeid': nodeid,
                        'regime': 'real-repo' if nodeid.endswith('@real-repo') else 'ungrouped',
                        'time': float(case.get('time', '0')),
                        'error': case.find('error') is not None,
                        'hostname': suite.get('hostname', ''),
                    })
        session['windows'] = union(session['windows'])
        sessions.append(session)
    groups = defaultdict(lambda: {'times': [], 'errors': 0, 'proxies': 0, 'hosts': set()})
    lines = [
        '# t1259 scan survey', '',
        'Time is the testcase setup/call/teardown proxy, not an individual Git duration. '
        'n/percentiles use non-error cases with time >= 2 s; errors are reported separately '
        'as 30 s right-censored Git observations (their testcase time is not replaced).', '',
        'Overlap = number of distinct other retained sessions whose shard-0..2 window union '
        'intersects this session; this is not peak simultaneous concurrency. '
        'Naive timestamps and --since use the local timezone. Sessions are filtered by directory mtime.', '',
        '| regime | other sessions | scan proxies | n | p50 | p90 | p95 | p99 | max | errors | hostname |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for session in sessions:
        session['overlap'] = sum(
            other is not session and any(a < d and c < b
                for a, b in session['windows'] for c, d in other['windows'])
            for other in sessions
        )
        for case in session['cases']:
            group = groups[(case['regime'], session['overlap'])]
            group['hosts'].add(case['hostname'])
            group['errors'] += int(case['error'])
            group['proxies'] += int(case['time'] >= 2.0)
            if case['time'] >= 2.0 and not case['error']:
                group['times'].append(case['time'])
    for (regime, overlap), group in sorted(groups.items()):
        values = group['times']
        row = [regime, overlap, group['proxies'], len(values),
               *(percentile(values, p) for p in (50, 90, 95, 99, 100)),
               group['errors'], ', '.join(sorted(group['hosts']))]
        lines.append('| ' + ' | '.join(map(cell, row)) + ' |')
    lines += ['', '## Session suite windows', '',
              '| session | overlap | shard | timestamp | time | hostname |',
              '|---|---:|---|---|---:|---|']
    for session in sessions:
        for shard, timestamp, duration, host in session['suites']:
            lines.append('| ' + ' | '.join(map(cell, (
                session['name'], session['overlap'], shard, timestamp, duration, host
            ))) + ' |')
    lines += ['', '## Individual scan proxies and errors', '',
              '| session | regime | overlap | nodeid | time | error (30 s censored) | hostname |',
              '|---|---|---:|---|---:|---|---|']
    for session in sessions:
        for case in session['cases']:
            if case['time'] >= 2.0 or case['error']:
                lines.append('| ' + ' | '.join(map(cell, (
                    session['name'], case['regime'], session['overlap'], case['nodeid'],
                    case['time'], case['error'], case['hostname'],
                ))) + ' |')
    args.out.write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

```
