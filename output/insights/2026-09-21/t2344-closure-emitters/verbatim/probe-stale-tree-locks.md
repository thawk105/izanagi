# 親が repo 外で実行した script の逐語 (`stale_tree_locks.py`)

```python
"""tuple が main で前進した後に、前進前の木から旧 grammar で記録された lock がどれだけあるかを数える。

exact-85 は 2026-09-21 00:21 JST ごろ main に入った。それ以降に mtime を持つ 63-key lock は
「直前 grammar の lock が、tuple 前進後にも作られ続ける」ことの実測である。
出力: stale-tree-locks.json
"""
import json
import time

J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
LAND = "2026-09-21 00:21:07"  # 285477c00 (前段 T-2344 の fold、exact-85 が main の現行 grammar になった時刻)
d = json.load(open(J + "/recent-locks.json"))
rows = [r for r in d["locks"] if r.get("keys") == 63]
after = [r for r in rows if r["mtime"] >= LAND]
before = [r for r in rows if r["mtime"] < LAND]
commits = {}
for r in rows:
    doc = json.load(open(r["path"]))
    commits.setdefault(doc["authority"]["contract_loader_commit"], []).append(r["mtime"])
out = {
    "land_of_exact85_on_main": LAND + " JST (285477c00)",
    "recorded_63key_total_since_2155": len(rows),
    "recorded_63key_after_exact85_landed": len(after),
    "recorded_63key_before": len(before),
    "after_mtime_range": [min((r["mtime"] for r in after), default=None), max((r["mtime"] for r in after), default=None)],
    "record_commits": {c: {"count": len(v), "first": min(v), "last": max(v)} for c, v in commits.items()},
    "sample_after_paths": [r["path"] for r in after[:3]],
}
json.dump(out, open(J + "/stale-tree-locks.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
```
