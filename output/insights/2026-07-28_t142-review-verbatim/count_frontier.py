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
