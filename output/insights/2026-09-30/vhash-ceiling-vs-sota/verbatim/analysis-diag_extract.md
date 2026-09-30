# 親の診断値の要約 script の逐語 (analysis/diag_extract.py、repo 外で実行)

sha256: ed6d1f8e88155254a7aabd89add6cd3e1efe4bb539b9adb095e8bfdd01482bea、2393 bytes

```python
#!/usr/bin/env python3
"""診断 run (各 1 走、extime 1 s、計数入り build) の要約 (repo 外、親の集計)。
S・R は md_29 の VLIFE parser (`vhash_cicada_vlife.parse_vlife_line` / `summarize`)、機構の腕は各計数行の JSON をそのまま読む。
driver の aggregate_diagnostics は前進 C の parser が CICADA_LONGTX_V1 行を必須にしていて止まったため使わない。
import は vceil-m2 (3dcdbbe4e) から、PYTHONDONTWRITEBYTECODE=1 で行う (変異本走中の vceil-m1 に触れない)。
引数: <raw dir> <出力 json>
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, "/work/1/SFC/tanab/izanagi/.claude/worktrees/vceil-m2")
from orchestrator.campaign import vhash_cicada_vlife as VL  # noqa: E402


def line_json(stdout, prefix):
    lines = [l[len(prefix):] for l in stdout.splitlines() if l.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f"{prefix!r}: {len(lines)} lines")
    return json.loads(lines[0])


out = {}
raw = Path(sys.argv[1])
for point in ("P1", "P2", "P3", "P4"):
    for row in (json.loads(l) for l in open(raw / f"diag-{point}.jsonl") if l.strip()):
        arm, s = row["arm"], row["stdout"]
        wl = line_json(s, "IZANAGI_CICADA_CEILING_WORKLOAD_V1 ")
        item = {"gc_inter_us": row["gc_inter_us"], "normal_commits": wl["normal_commits"],
                "batch_commits": wl["batch_commits"]}
        if arm in ("S", "R"):
            summ = VL.summarize(VL.parse_vlife_line(s))
            item["vlife_summary"] = summ
        if arm == "R":
            item["ro_gcflag_count"] = line_json(s, "IZANAGI_CICADA_RO_GCFLAG_COUNT_V1 ")
        if arm == "fwd":
            item["fwd"] = line_json(s, "CICADA_FWD_V1 ")
        if arm.startswith("hot"):
            item["hot"] = line_json(s, "CICADA_VHASH_COUNT_JSON ")
            item["hot_post"] = line_json(s, "CICADA_VHASH_POST_COUNT_JSON ")
        if arm.startswith("igc"):
            item["igc"] = line_json(s, "CICADA_INTERVAL_V1 ")
        out.setdefault(point, {})[arm] = item
Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
for point, arms in out.items():
    for arm, item in arms.items():
        keys = {k: v for k, v in item.items() if k in ("normal_commits", "batch_commits", "gc_inter_us")}
        print(point, arm, keys, sorted(item.get("vlife_summary", {}).keys())[:12])
```
