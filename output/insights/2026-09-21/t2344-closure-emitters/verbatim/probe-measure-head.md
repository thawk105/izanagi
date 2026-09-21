# 親が repo 外で実行した script の逐語 (`measure_head.py`)

```python
"""着手 commit で閉包寸法を実測する (T-2344 一次資料の probe 原本を書き直さずに import して使う)。

出力: closure-head.json (tuple 起点 / 発行器起点 / 和 / 発行器起点にだけ居る集合 / 提案 tuple を seed にした閉包)。
"""
import json
import subprocess
import sys

sys.path.insert(0, "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability")
from probe_closure_v2 import Tree, enrolled_tuple, expand, imports_of, package_inits  # noqa: E402

J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
W = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters"
C = subprocess.run(["git", "rev-parse", "HEAD"], cwd=W, capture_output=True, text=True, check=True).stdout.strip()

PRODUCER_SEEDS = (
    "orchestrator/campaign/s8b_oracle_report.py",
    "orchestrator/campaign/autonomous_trial_completeness.py",
    "orchestrator/campaign/b10_backoff_shape_sweep.py",
    "orchestrator/campaign/backoff_extended_sweep.py",
    "orchestrator/campaign/backoff_extended_sweep_report.py",
    "orchestrator/campaign/backoff_overthrottle.py",
)

tree = Tree(W, C)
enrolled = enrolled_tuple(tree, "CONTRACT_LOADER_RELATIVE_PATHS")
tuple_full = expand(tree, list(enrolled), depth=None)
tuple_rooted = set(tuple_full["members"])
tuple_l1 = set(expand(tree, list(enrolled), depth=1)["members"])
missing = [p for p in PRODUCER_SEEDS if not tree.isfile(p)]
prod = expand(tree, [p for p in PRODUCER_SEEDS if tree.isfile(p)], depth=None)
producer_rooted = set(prod["members"])
union = tuple_rooted | producer_rooted
producer_only = sorted(producer_rooted - tuple_rooted)

emitters_status = {p: {"enrolled": p in enrolled, "in_tuple_universe": p in tuple_rooted,
                       "in_producer_only": p in producer_only} for p in PRODUCER_SEEDS}
new_members = sorted((set(PRODUCER_SEEDS) | set(producer_only)) - set(enrolled))
proposed = list(enrolled) + new_members  # 末尾へ sorted 順 (D2193 の前例)
prop_full = expand(tree, proposed, depth=None)
prop_rooted = set(prop_full["members"])

# 2 段目 (現行 85 起点の 1 段目の未収載) — 参考: 本 wave は含めない
layer2_unenrolled = sorted(tuple_l1 - set(enrolled))

# 新規 member の直接 import 元 (edges) — 何が何を import して居るか
new_edges = {}
for p in new_members:
    tg, _ = imports_of(tree, p)
    inits = set(package_inits(tree, p))
    for t in tg:
        inits.update(package_inits(tree, t))
    new_edges[p] = sorted(tg | inits)
importers = {p: sorted(src for src, outs in {**tuple_full["edges"], **prod["edges"]}.items() if p in outs)
             for p in new_members}

result = {
    "commit": C,
    "enrolled_count": len(enrolled),
    "tuple_rooted_universe": len(tuple_rooted),
    "tuple_unenrolled": len(tuple_rooted - set(enrolled)),
    "tuple_layer1_unenrolled_count": len(layer2_unenrolled),
    "tuple_layer1_unenrolled": layer2_unenrolled,
    "seeds_missing": missing,
    "producer_rooted_universe": len(producer_rooted),
    "union_universe": len(union),
    "union_unenrolled": len(union - set(enrolled)),
    "producer_only_count": len(producer_only),
    "producer_only_not_in_tuple_universe": producer_only,
    "emitters_status": emitters_status,
    "new_members_count": len(new_members),
    "new_members_sorted": new_members,
    "proposed_count": len(proposed),
    "proposed_rooted_universe": len(prop_rooted),
    "proposed_rooted_equals_union": prop_rooted == union,
    "proposed_unenrolled": len(prop_rooted - set(proposed)),
    "proposed_unenrolled_list": sorted(prop_rooted - set(proposed)),
    "unresolved_references_tuple": tuple_full["unresolved"],
    "unresolved_references_proposed": prop_full["unresolved"],
    "new_member_edges": new_edges,
    "new_member_importers": importers,
    "enrolled": list(enrolled),
    "proposed": proposed,
}
json.dump(result, open(J + "/closure-head.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in result.items()
                  if k not in ("enrolled", "proposed", "new_member_edges", "new_member_importers",
                               "proposed_unenrolled_list", "tuple_layer1_unenrolled")},
                 indent=2, ensure_ascii=False))
```
