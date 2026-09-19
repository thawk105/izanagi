# sampler_summary.py (逐語)

親の読取り補助 (権威にしない): sampler jsonl の要約。

```python
"""sampler jsonl の要約 (親の読取り専用補助)。引数: <jsonl> [threshold_seconds]"""
import json
import sys

path = sys.argv[1]
rows = [json.loads(line) for line in open(path, encoding='utf-8') if line.strip()]
print('samples', len(rows))
for s in rows:
    git = {n: round(g['wall_seconds'], 2) for n, g in s['git'].items()}
    errs = [n for n, g in s['git'].items() if g['error']]
    print(s['timestamp'][11:19], 'load', s['loadavg'], 'leaders', s['leaders'], 'workers', s['workers'],
          'git_total', round(s['git_total_seconds'], 2), git, 'sha', round(s['sha256_total_seconds'], 2), 'ERR' if errs else '')


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 2)


if rows:
    totals = [s['git_total_seconds'] for s in rows]
    percall = {n: [s['git'][n]['wall_seconds'] for s in rows] for n in rows[0]['git']}
    print('git_total: p50', pct(totals, .5), 'p90', pct(totals, .9), 'p99', pct(totals, .99), 'max', round(max(totals), 2))
    for n, xs in percall.items():
        print('  %-9s p50 %s p90 %s p99 %s max %s' % (n, pct(xs, .5), pct(xs, .9), pct(xs, .99), round(max(xs), 2)))
    by_leaders = {}
    for s in rows:
        by_leaders.setdefault(s['leaders'], []).append(s['git_total_seconds'])
    for k in sorted(by_leaders):
        xs = by_leaders[k]
        print('  leaders=%d n=%d p50 %s p90 %s max %s' % (k, len(xs), pct(xs, .5), pct(xs, .9), round(max(xs), 2)))

```
