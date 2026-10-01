# 親の最終集計 script の逐語 (analysis/final_decision.py、repo 外で実行)

sha256: b9479755b65244c3d9a9d7038869d378c8d72d4dd3c8eea60dc46c9dc08cc472、3510 bytes

```python
#!/usr/bin/env python3
"""親の最終集計 (repo 外)。driver (vceil-m1、3dcdbbe4e) の関数をそのまま使い、30 秒比較の対だけを
事前記述 §4.2 どおり「点ごとに選んだ GC 間隔」で組む。driver の aggregate は両点を代表点の GC 間隔で
組むため、P2 (100 µs で走らせた) の対が作れず停止した (段 7 で記録)。
引数: <perf raw jsonl> <verify json> <出力 json>
"""
import json, statistics, sys
sys.path.insert(0, "/work/1/SFC/tanab/izanagi/.claude/worktrees/vceil-m1")
from orchestrator.campaign import vhash_ceiling_vs_sota as C  # noqa: E402

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
witnesses = {w["arm"]: w for w in json.load(open(sys.argv[2]))}
C._unique_runs(rows)
prelim_rows = [r for r in rows if r["mode"] == "prelim"]
compare_rows = [r for r in rows if r["mode"] == "compare"]
# 予備の集計は driver の aggregate を予備の raw だけに掛けたものと同じ
pre = C.aggregate(prelim_rows, witnesses)
gc, rep, arm, nb = pre["gc"], pre["representative"]["point"], pre["representative"]["arm"], pre["neighbor"]
compare = {}
for point in (rep, nb):
    interval = gc[point]
    compare[point] = {}
    for candidate in C.M_ARMS + ("S",):
        pairs = C.paired(compare_rows, candidate, point, interval, "compare")
        if not pairs:
            continue
        compare[point][candidate] = {
            "ratio": statistics.median(p["ratio"] for p in pairs),
            "ratio_min": min(p["ratio"] for p in pairs), "ratio_max": max(p["ratio"] for p in pairs),
            "completion_ratio": statistics.median(p["completion_ratio"] for p in pairs
                                                  if p["completion_ratio"] is not None),
            "rounds": sorted(p["round"] for p in pairs), "nodes": sorted({p["node"] for p in pairs}),
            "eligible": len(pairs) == 6 and {p["round"] for p in pairs} == set(range(1, 7))
                        and C.completion_ok(pairs, point)
                        and (candidate == "S" or C.accepted_witness(candidate, witnesses.get(candidate, {}))),
            "pairs": pairs}
residual = pre["prelim"].get(rep, {}).get("R-noLR", {})
residual_rounds = sorted(p["round"] for p in residual.get("pairs", []))
residual_ratio = residual.get("ratio") if residual_rounds == [1, 2, 3] else None  # FR2-1 を親が担保
decision = C.final_recommendation(compare, rep, nb, arm, {}, residual_ratio)
cont = C.continuation(compare, rep, nb, arm)
out = {"gc": gc, "representative": {"point": rep, "arm": arm}, "neighbor": nb,
       "comparison_arms": pre["comparison_arms"], "compare": compare,
       "continuation": cont, "research_decision": decision,
       "residual_cost": {"R_noLR_over_R_prelim_median": residual.get("ratio"),
                         "rounds": residual_rounds, "used_for_decision": residual_ratio},
       "prelim": pre["prelim"], "retune_R": pre["retune_R"], "add_P4_and_P4prime": pre["add_P4_and_P4prime"]}
open(sys.argv[3], "w").write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(json.dumps({k: out[k] for k in ("gc", "representative", "neighbor", "continuation",
                                      "research_decision", "residual_cost")}, ensure_ascii=False))
for p, arms in compare.items():
    for a, v in arms.items():
        print(p, a, round(v["ratio"], 3), round(v["ratio_min"], 3), round(v["ratio_max"], 3),
              "c", round(v["completion_ratio"], 3), v["rounds"], "eligible", v["eligible"])
```
