# 親の実測手順 (逐語)

3 本の script は job dir (`/home/SFC/tanab/.claude/jobs/385cc37e/tmp/`、repo 外) に親が直接書いた read-only の
probe で、repo へは `.py` として入れない (実装面の Codex author 規約。本書は逐語の `.md` 写し)。出力は同 dir の
`edge_probe.json` / `ao_probe.json` で、本 insight の `verbatim/parent-edge-probe.json` / `verbatim/parent-ao-probe.json` は
その bytes をそのまま複製したもの。実行は login node `pegasus02`、checkout は本 wave の worktree (HEAD `482f19b88`)。
`wal_summary.py` は先行の棚卸しで、出力 (`wal_summary.txt`) は本書に載せず、値は JSON 2 本から取った。

## edge_probe.py (`python3 edge_probe.py <repo root>`)

```python
#!/usr/bin/env python3
"""[T-2632] 対応の各辺 (proposal ↔ 走行 ↔ 参照点) を現存資料で結べるかの実測 (読み取りのみ)。

repo root を argv[1] に取る。出力は JSON 1 本 (stdout)。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))

from orchestrator.campaign import agent_outputs  # noqa: E402
from orchestrator.campaign import p3_s4_loop  # noqa: E402
from orchestrator.campaign import wal as walmod  # noqa: E402
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402

CAMPAIGNS = {
    "base": "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387",
    "sort": "output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
    "trigger": "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
}

RUN_CMD_RE = re.compile(r"-thread_num=(\d+) -ycsb_tuple_num=(\d+) -extime=(\d+) -clocks_per_us=(\d+) -ycsb_rratio=(\d+) -ycsb_zipf_skew=([0-9.]+) -ycsb_rmw=(\w+)")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def file_entry(p: Path) -> dict:
    return {"path": rel(p), "bytes": p.stat().st_size, "sha256": sha(p)}


def campaign_probe(kind: str, d: Path) -> dict:
    layout = CampaignLayout(root=str(d))
    out: dict = {"kind": kind, "dir": rel(d), "files": [file_entry(p) for p in sorted(d.rglob("*")) if p.is_file()]}
    lock = json.loads((d / "campaign.lock").read_text())
    state = json.loads((d / "loop_state.json").read_text())
    out["lock"] = lock
    out["whiteboard"] = state["whiteboard"]
    out["whiteboard_row_count"] = len(state["whiteboard"])
    out["whiteboard_keys_union"] = sorted({k for w in state["whiteboard"] for k in w})
    out["loop_state_keys"] = sorted(state.keys())
    records = walmod.read_records(layout)
    recs = []
    for r in records:
        entry = {
            "variant": r.variant, "stage": r.stage, "env_tag": r.env_tag, "ts": r.ts,
            "payload_keys": sorted(r.payload.keys()),
            "wal_ref": "wal:" + agent_outputs.canonical_sha256(vars(r)),
        }
        if r.stage == "build_start":
            entry["genome"] = r.payload.get("genome")
            entry["src_token"] = r.payload.get("src_token")
        if r.stage == "verify_done":
            entry["certified"] = r.payload.get("certified")
            entry["verdict"] = r.payload.get("verdict")
        if r.stage == "bench_done":
            m = RUN_CMD_RE.search(r.payload.get("run_cmd", ""))
            entry["median_tps"] = r.payload.get("median_tps")
            entry["run_cmd_perf"] = (
                {"threads": int(m[1]), "records": int(m[2]), "extime": int(m[3]), "clocks_per_us": int(m[4]),
                 "ycsb_rratio": int(m[5]), "ycsb_zipf_skew": m[6], "ycsb_rmw": m[7]} if m else None
            )
        if r.stage == "commit":
            entry["fitness_tps"] = r.payload.get("fitness_tps")
        if r.stage == "abort":
            entry["reason"] = r.payload.get("reason")
        recs.append(entry)
    out["wal_records"] = recs
    variants = []
    for v in dict.fromkeys(r.variant for r in records):
        stages = [r.stage for r in records if r.variant == v]
        variants.append({"variant": v, "stages": stages})
    out["wal_variants"] = variants
    out["wal_variant_count"] = len(variants)
    out["wal_record_count"] = len(records)
    # 記録間に iteration・proposal hash・lineage が現れるか (文字列検索)
    wal_text = (d / "runs/wal.jsonl").read_text()
    out["wal_mentions"] = {
        "iteration": "iteration" in wal_text,
        "proposal": "proposal" in wal_text,
        "attempt_id": "attempt_id" in wal_text,
        "parent": "parent" in wal_text,
        "ancestor": "ancestor" in wal_text,
        "snapshot": "snapshot" in wal_text,
        "receipt": "receipt" in wal_text,
    }
    out["whiteboard_has_variant_or_hash"] = any(
        k in ("variant", "sha256", "proposal_sha256", "attempt_id") for w in state["whiteboard"] for k in w
    )
    # 順序で結ぶ試み: whiteboard 行 i ↔ WAL variant i (build_start の ts 順)
    order_map = []
    for i, w in enumerate(state["whiteboard"]):
        v = variants[i]["variant"] if i < len(variants) else None
        order_map.append({"whiteboard_iteration": w["iteration"], "wal_variant_by_order": v})
    out["order_join_attempt"] = order_map
    out["order_join_is_bijective"] = len(state["whiteboard"]) == len(variants)
    # 参照点候補: certified variant の commit.fitness_tps と env_tag・run_cmd 由来 PerfConfig
    refs = []
    for v in variants:
        commit = next((r for r in records if r.variant == v["variant"] and r.stage == "commit"), None)
        bench = next((r for r in records if r.variant == v["variant"] and r.stage == "bench_done"), None)
        verify = [r for r in records if r.variant == v["variant"] and r.stage == "verify_done"]
        refs.append({
            "variant": v["variant"],
            "certified_all_verify": bool(verify) and all(r.payload.get("certified") is True for r in verify),
            "fitness_tps": commit.payload.get("fitness_tps") if commit else None,
            "commit_env_tag": commit.env_tag if commit else None,
            "commit_wal_ref": ("wal:" + agent_outputs.canonical_sha256(vars(commit))) if commit else None,
            "bench_wal_ref": ("wal:" + agent_outputs.canonical_sha256(vars(bench))) if bench else None,
            "lock_search_config_records_threads": [lock["search_config"].get("records"), lock["search_config"].get("threads")],
        })
    out["reference_candidates"] = refs
    return out


def main() -> int:
    result: dict = {"repo_root": str(ROOT), "campaigns": {}}
    for kind, c in CAMPAIGNS.items():
        result["campaigns"][kind] = campaign_probe(kind, ROOT / c)
    # trigger provenance report
    prov_path = ROOT / CAMPAIGNS["trigger"] / "reports/p3_s8a_trigger_loop_provenance.json"
    prov = json.loads(prov_path.read_text())
    trig_variants = {v["variant"] for v in result["campaigns"]["trigger"]["wal_variants"]}
    result["trigger_provenance"] = {
        "file": file_entry(prov_path),
        "entries": prov["entries"],
        "entry_variants_all_in_wal": all(e["variant"] in trig_variants for e in prov["entries"].values()),
        "proposal_paths_exist_now": {k: Path(e["proposal_path"]).exists() for k, e in prov["entries"].items()},
        "auditor_diff_digest_is_sha256": all(re.fullmatch(r"[0-9a-f]{64}", e["auditor_diff_digest"]) for e in prov["entries"].values()),
    }
    l3_path = ROOT / CAMPAIGNS["trigger"] / "reports/layer3_report.json"
    l3 = json.loads(l3_path.read_text())
    result["trigger_layer3"] = {
        "file": file_entry(l3_path),
        "runs": [{"variant": r["variant"], "source_ref": r.get("source_ref"), "median_tps": r.get("median_tps")} for r in l3.get("runs", [])],
        "artifact_refs": l3.get("artifact_refs"),
    }
    # layer3 の source_ref が WAL の bench_done ref と一致するか
    bench_refs = {r["wal_ref"] for r in result["campaigns"]["trigger"]["wal_records"] if r["stage"] == "bench_done"}
    result["trigger_layer3"]["source_refs_match_bench_wal_refs"] = all(r["source_ref"] in bench_refs for r in result["trigger_layer3"]["runs"])
    # K2 round 3 insight materials: proposal ↔ WAL ref 束縛の形
    k2 = ROOT / "output/insights/2026-09-19/k2-loop-round3"
    if k2.is_dir():
        prop = k2 / "materials/proposal-4.json"
        doc = json.loads(prop.read_text())
        k2out = {
            "files": [file_entry(p) for p in sorted((k2 / "materials").glob("*")) if p.is_file()],
            "proposal_raw_sha256": sha(prop),
            "proposal_top_keys": sorted(doc.keys()),
        }
        try:
            k2out["proposal_canonical_b4_sha256"] = p3_s4_loop.canonical_b4_proposal_sha256(doc)
        except Exception as exc:  # noqa: BLE001
            k2out["proposal_canonical_b4_sha256_error"] = f"{type(exc).__name__}: {exc}"
        rs = json.loads((k2 / "materials/run-summary.json").read_text())
        k2out["run_summary_variant"] = rs.get("variant")
        k2out["run_summary_wal_refs"] = rs.get("wal_refs")
        k2out["run_summary_whiteboard"] = rs.get("loop_state", {}).get("whiteboard")
        k2out["run_summary_keys"] = sorted(rs.keys())
        k2out["run_summary_has_proposal_hash"] = any("proposal" in k for k in rs.keys())
        result["k2_round3_insight"] = k2out
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## ao_probe.py (`python3 ao_probe.py <repo root>`)

```python
#!/usr/bin/env python3
"""K2 3 巡目 campaign (repo 外) の agent_outputs.jsonl が何を束縛するかを読む (読み取りのみ)。"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import agent_outputs  # noqa: E402
from orchestrator.campaign import p3_s4_loop  # noqa: E402

P = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8")
ao = P / "runs/agent_outputs.jsonl"
wal = P / "runs/wal.jsonl"
out = {"ao_path": str(ao), "ao_sha256": hashlib.sha256(ao.read_bytes()).hexdigest(),
       "wal_path": str(wal), "wal_sha256": hashlib.sha256(wal.read_bytes()).hexdigest()}
wal_recs = [json.loads(l) for l in wal.read_text().splitlines() if l.strip()]
wal_refs = {}
for r in wal_recs:
    ref = "wal:" + agent_outputs.canonical_sha256(r)
    wal_refs[ref] = (r["variant"], r["stage"])
out["wal_records"] = [{"variant": r["variant"], "stage": r["stage"], "env_tag": r["env_tag"], "ref": "wal:" + agent_outputs.canonical_sha256(r)} for r in wal_recs]
rows = []
for line in ao.read_text().splitlines():
    if not line.strip():
        continue
    e = json.loads(line)
    p = e["payload"]
    prov = p.get("provenance", {})
    row = {
        "stage": e["stage"], "variant": e.get("variant"), "env_tag": e.get("env_tag"), "ts": e.get("ts"),
        "payload_keys": sorted(p.keys()),
        "provenance_keys": sorted(prov.keys()),
        "provenance_mode": prov.get("mode"),
        "source_path": prov.get("source_path"),
        "source_sha256": prov.get("source_sha256"),
        "input_file_sha256": prov.get("input_file_sha256"),
        "input_sha256": p.get("input_sha256"),
        "refs": p.get("refs"),
        "refs_resolve_in_wal": [wal_refs.get(x) for x in (p.get("refs") or [])],
        "output_keys": sorted(p["output"].keys()) if isinstance(p.get("output"), dict) else type(p.get("output")).__name__,
        "digest_sha256": p.get("digest_sha256"),
    }
    rows.append(row)
out["agent_outputs"] = rows
# insight に写した proposal-4.json の raw sha256 と AO の source_sha256 の一致
prop = ROOT / "output/insights/2026-09-19/k2-loop-round3/materials/proposal-4.json"
out["insight_proposal_raw_sha256"] = hashlib.sha256(prop.read_bytes()).hexdigest()
out["insight_proposal_canonical_b4_sha256"] = p3_s4_loop.canonical_b4_proposal_sha256(json.loads(prop.read_text()))
out["ao_source_sha256_matches_insight_proposal"] = [r["source_sha256"] == out["insight_proposal_raw_sha256"] for r in rows if r["stage"] in ("planner_proposed", "coder_proposed")]
# loop_state / lock
st = json.loads((P / "loop_state.json").read_text())
out["loop_state"] = st
lock = json.loads((P / "campaign.lock").read_text())
out["lock_keys"] = sorted(lock.keys())
out["lock_search_config_keys"] = sorted(lock.get("search_config", {}).keys())
print(json.dumps(out, ensure_ascii=False, indent=1))
```

## wal_summary.py (`python3 wal_summary.py <repo root>`)

```python
#!/usr/bin/env python3
"""現物 3 campaign の WAL / lock / loop_state を要約する (読み取りのみ)。"""
import hashlib
import json
import sys
from pathlib import Path

CAMPAIGNS = [
    "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387",
    "output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
    "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    for c in CAMPAIGNS:
        d = root / c
        print("=" * 100)
        print(c)
        for name in ["campaign.lock", "loop_state.json", "runs/wal.jsonl"]:
            p = d / name
            print(f"  {name}: bytes={p.stat().st_size} sha256={sha(p)}")
        for extra in sorted(d.rglob("*")):
            if extra.is_file() and extra.relative_to(d).as_posix() not in {"campaign.lock", "loop_state.json", "runs/wal.jsonl"}:
                print(f"  extra {extra.relative_to(d)}: bytes={extra.stat().st_size} sha256={sha(extra)}")
        lock = json.loads((d / "campaign.lock").read_text())
        print("  lock keys:", sorted(lock.keys()))
        print("  lock:", json.dumps(lock, ensure_ascii=False)[:600])
        st = json.loads((d / "loop_state.json").read_text())
        print("  loop_state keys:", sorted(st.keys()))
        print("  iteration:", st.get("iteration"), "start_wall:", st.get("start_wall"))
        for w in st.get("whiteboard", []):
            print("   wb:", json.dumps(w, ensure_ascii=False))
        print("  WAL records:")
        for line in (d / "runs/wal.jsonl").read_text().splitlines():
            r = json.loads(line)
            p = r.get("payload", {})
            print(f"   variant={r.get('variant')} stage={r.get('stage')} env_tag={r.get('env_tag')} ts={r.get('ts')} payload_keys={sorted(p.keys())}")
            if r.get("stage") == "build_start":
                print(f"      genome={p.get('genome')} src_token={p.get('src_token')}")
            if r.get("stage") in ("commit", "verify_done"):
                print(f"      {json.dumps(p, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
