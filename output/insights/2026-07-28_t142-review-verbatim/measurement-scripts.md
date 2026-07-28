# [T-142] 親の独立実測スクリプト (逐語凍結)

wave branch (worktree-dev-wave-t088-python-gate、333605d) では `count_abort_reasons.py` /
`count_frontier.py` の 2 ファイルとして凍結した。main への統合時、D95 の実装面契約
(check_ai_provenance は所在を問わず `*.py` を実装面と分類し Codex author を要求する) と
衝突しない形へ、内容を変えずに本 Markdown のコードブロックとして凍結し直した。
これは分析の再現手順の記録であり production code ではない。実行する場合は repo root で
それぞれをファイルへ書き出して `python3 <file>` する (読取のみ・WAL へ書かない)。

## count_abort_reasons.py

```python
"""全 campaign WAL の abort reason 分布と、S2/bench の段別コスト分布を読むだけの集計。"""
import json, glob, collections, os

os.chdir("/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate")
reasons = collections.Counter()
stages = collections.Counter()
per_campaign = collections.defaultdict(collections.Counter)
s2_durations = []
n_files = 0
for path in glob.glob("output/campaigns/*/runs/wal.jsonl"):
    n_files += 1
    camp = path.split("/")[2]
    last_ts = {}
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        stages[r.get("stage")] += 1
        v = r.get("variant")
        ts = r.get("ts")
        p = r.get("payload", {})
        if r.get("stage") == "verify_done" and p.get("workload", {}).get("tag") == "s2":
            prev = last_ts.get(v)
            if prev is not None and ts is not None:
                s2_durations.append(ts - prev)
        if ts is not None and v is not None:
            last_ts[v] = ts
        if r.get("stage") == "abort":
            reason = p.get("reason", "?").split(":")[0]
            reasons[reason] += 1
            per_campaign[camp][reason] += 1
print("files:", n_files)
print("stages:", dict(stages))
print("abort reasons (all campaigns):")
for k, v in reasons.most_common():
    print(f"  {k}: {v}")
print("\nper-campaign (p3 loop 系のみ):")
for c, cnt in sorted(per_campaign.items()):
    if "loop" in c:
        print(f"  {c}: {dict(cnt)}")
if s2_durations:
    s2_durations.sort()
    n = len(s2_durations)
    print(f"\nS2 verify duration (直前 record からの差分, n={n}): "
          f"min={s2_durations[0]:.1f}s median={s2_durations[n//2]:.1f}s max={s2_durations[-1]:.1f}s")
```

## count_frontier.py

```python
"""読むだけの集計: commit 済み variant のうち「その時点の new-best (fitness 最大更新)」の比率。
S2 を new-best だけに走らせる二層化が過去 campaign でどれだけ S2 を省けたかの見積もり。"""
import json, glob, collections, os

os.chdir("/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate")
total_commits = 0
total_newbest = 0
rows = []
for path in sorted(glob.glob("output/campaigns/*/runs/wal.jsonl")):
    camp = path.split("/")[2]
    commits = []
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("stage") == "commit":
            tps = r.get("payload", {}).get("fitness_tps")
            if isinstance(tps, (int, float)):
                commits.append((r.get("ts", 0), tps))
    if not commits:
        continue
    commits.sort()
    best = float("-inf")
    newbest = 0
    for _, tps in commits:
        if tps > best:
            best = tps
            newbest += 1
    total_commits += len(commits)
    total_newbest += newbest
    rows.append((camp, len(commits), newbest))
for camp, n, nb in rows:
    print(f"  {camp}: commits={n} new-best={nb} ({nb/n:.0%})")
print(f"\ntotal: commits={total_commits} new-best={total_newbest} "
      f"({total_newbest/total_commits:.0%}) → S2 を new-best 限定にした場合の省略率 = "
      f"{1 - total_newbest/total_commits:.0%}")
```
