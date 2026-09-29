# 集計 script の写し (repo 外で実行、2026-09-29)

`analysis/summary.{json,md}` の生成器 `summarize.py` (sha256 `c60ed40cbd8dc615aa8f4750a77e467e8b86f59ae3cd3df464c33540ef35f906`) と、本文の範囲を検算した `ranges.py` (sha256 `54aacfee1196efd5b092b6fa6e994788ba0c7953da8c1657cf83b1bf190aad98`、出力 `analysis/ranges.txt`)。
実行: `python3 summarize.py <wave worktree> <out dir> measure-m0.json … measure-m3.json` (展開後の raw)、`python3 ranges.py`。定義は driver (`orchestrator/campaign/vhash_cicada_vlife.py`) の `summarize` と `df_interaction` を import して使う。

## summarize.py

```python
#!/usr/bin/env python3
"""md_15 本計測 raw の集計 (repo 外で実行、定義は driver の summarize と同じ)。
argv: <wave worktree> <out dir> <raw.json>...
出力: summary.json (条件ごとの反復値・平均・最小・最大、D-F)、summary.md (抜粋表)。"""
import json
import statistics
import sys
from pathlib import Path

WT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
RAWS = [Path(p) for p in sys.argv[3:]]
sys.path.insert(0, str(WT))
from orchestrator.campaign import vhash_cicada_vlife as V  # noqa: E402

KI = {1: 0, 4: 3, 8: 4}
runs = {}
meta = []
for path in RAWS:
    raw = json.loads(path.read_text())
    meta.append({"path": str(path), "patch_sha256": raw["patch_sha256"], "records": raw["records"],
                 "conditions": len(raw["runs"])})
    for cid, reps in raw["runs"].items():
        assert cid not in runs
        runs[cid] = reps


def extime(argv):
    vals = [a for a in argv if a.startswith("-extime=")]
    assert len(vals) == 1
    return int(vals[0].split("=")[1])


def metrics(rep):
    p = rep["parsed"]
    s = V.summarize(p)
    w = p["workers"]
    w0 = w[0]
    t = extime(rep["argv"])
    ro_reads = s["readonly_reads"]
    upd_reads = sum(sum(x["hops"][0]) for x in w)
    deep_all = [s["readonly_deep"][i] + s["deep"][i] for i in range(5)]
    out = {
        "realized_ro_attempt": s["realized_readonly_attempt_rate"],
        "realized_ro_commit": s["realized_readonly_commit_rate"],
        "abort_rate": s["abort_rate"],
        "update_commits_per_s": s["update_commits"] / t,
        "install_per_s": s["install"] / t,
        "boundary_mean_us": s["gc_boundary_mean_us"],
        "boundary_p50_bucket_us": s["gc_boundary_p50_bucket_us"],
        "publish_mean_us": s["gc_publish_mean_us"],
        "publications_per_s": s["gc_publications"] / t,
        "ro_snapshot_age_mean_us": s["ro_snapshot_age_mean_us"],
        "dc_cf_wait_mean_us": s["dc_cf_wait_mean_us"],
        "dc_ro_gap_mean_us": s["dc_ro_gap_mean_us"],
        "dc_leader_wait_mean_us": s["dc_leader_wait_mean_us"],
        "local_flag_opportunity": s["local_flag_opportunity"],
        "dc_count": w0["dc_count"], "dc_first": w0["dc_first"], "dc_generation": w0["dc_generation"],
        "dc_missing": w0["dc_missing"], "dc_negative": w0["dc_negative"],
        "dc_late_epoch": w0["dc_late_epoch"], "dc_epoch_mismatch": w0["dc_epoch_mismatch"],
        "publish_count": w0["gc_publish_count"],
        "cf_kind_share": [c / w0["dc_count"] if w0["dc_count"] else None for c in w0["dc_cf_kind_count"]],
        "cf_kind_wait_share": [c / w0["dc_cf_wait_sum_us"] if w0["dc_cf_wait_sum_us"] else None
                               for c in w0["dc_cf_kind_sum_us"]],
        "holder_fraction": s["holder_fraction"],
        "holder_unresolved": s["holder_unresolved"],
        "same_boundary_publications": s["same_boundary_publications"],
        "logical_live_versions": 1000000 + s["logical_version_delta"],
        "ro_reads": ro_reads, "update_reads": upd_reads,
    }
    for k, i in KI.items():
        out[f"ro_deep_rate_k{k}"] = s["readonly_deep_rate"][i]
        out[f"ro_share_of_deep_k{k}"] = s["readonly_share_of_deep"][i]
        out[f"ro_eligible_rate_k{k}"] = s["readonly_candidate_rate"][i]
        out[f"update_deep_rate_k{k}"] = s["deep"][i] / upd_reads if upd_reads else None
        out[f"all_deep_rate_k{k}"] = deep_all[i] / (ro_reads + upd_reads) if (ro_reads + upd_reads) else None
        out[f"ro_deep_count_k{k}"] = s["readonly_deep"][i]
        out[f"update_deep_count_k{k}"] = s["deep"][i]
    return out


def agg(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {"mean": statistics.fmean(vals), "min": min(vals), "max": max(vals), "n": len(vals)}


table = {}
for cid in sorted(runs):
    reps = [metrics(r) for r in runs[cid]]
    row = {"condition": V.CONDITIONS[cid], "reps": reps, "agg": {}}
    for key in reps[0]:
        if isinstance(reps[0][key], list):
            row["agg"][key] = [agg([r[key][i] for r in reps]) for i in range(len(reps[0][key]))]
        else:
            row["agg"][key] = agg([r[key] for r in reps])
    table[cid] = row


def mean(cid, key):
    return table[cid]["agg"][key]["mean"]


def sd(cid, key):
    vals = [r[key] for r in table[cid]["reps"] if r[key] is not None]
    return statistics.stdev(vals) if len(vals) > 1 else None


df = []
for prefix, rates, longs, gcs in (("R", (25, 50, 75, 95), ("wait1msU", "wait10msU", "wait10msR"), (10, 1000, 100000)),
                                  ("S", (50, 95), ("wait10msU",), (10, 100000)),
                                  ("T", (50, 95), ("wait10msU",), (10, 100000))):
    for gc in gcs:
        base = f"{prefix}0-none-gc{gc}"
        for key in ("boundary_mean_us", "publications_per_s"):
            for r in rates:
                ro = f"{prefix}{r}-none-gc{gc}"
                entry = {"prefix": prefix, "gc": gc, "metric": key, "r": r, "long": None,
                         "ro_total_diff": None if mean(ro, key) is None or mean(base, key) is None
                         else mean(ro, key) - mean(base, key)}
                df.append(entry)
                for L in longs:
                    lg0 = f"{prefix}0-{L}-gc{gc}"
                    lgr = f"{prefix}{r}-{L}-gc{gc}"
                    vals = [mean(c, key) for c in (lgr, ro, lg0, base)]
                    df.append({"prefix": prefix, "gc": gc, "metric": key, "r": r, "long": L,
                               "long_total_diff": None if vals[2] is None or vals[3] is None else vals[2] - vals[3],
                               "interaction": None if None in vals else V.df_interaction(*vals)})

summary = {"inputs": meta, "conditions": table, "df": df}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")


def f(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float):
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        return f"{x:.{nd}g}"
    return str(x)


lines = ["# md_15 集計 (3 反復の平均、`summary.json` に反復ごとの値と最小・最大)", "",
         "| 条件 | 実現 ro 試行率 | ro 深部率 K=1/4/8 | 深部に占める ro K=1/4/8 | update 深部率 K=1 | 境界年齢 平均 µs | p50 bucket | 公開/s | ro snapshot 年齢 µs | Δ_ro 平均 µs | 機会量 (b) | ro 適格率 K=1/4/8 | 保持: 通常U/長U/ro/長ro | 除外 (世代/遅延公開) | update commit/s | abort 率 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for cid in sorted(table, key=lambda c: (c[0], c.split("-")[1], int(c.split("gc")[1]), int(c.split("-")[0][1:]) if c[0] in "RST" else 0)):
    a = table[cid]["agg"]
    m = lambda k: a[k]["mean"]
    hf = [x["mean"] for x in a["holder_fraction"]]
    lines.append(
        f"| {cid} | {f(m('realized_ro_attempt'))} | {f(m('ro_deep_rate_k1'))} / {f(m('ro_deep_rate_k4'))} / {f(m('ro_deep_rate_k8'))} | "
        f"{f(m('ro_share_of_deep_k1'))} / {f(m('ro_share_of_deep_k4'))} / {f(m('ro_share_of_deep_k8'))} | {f(m('update_deep_rate_k1'))} | "
        f"{f(m('boundary_mean_us'))} | {f(m('boundary_p50_bucket_us'))} | {f(m('publications_per_s'))} | {f(m('ro_snapshot_age_mean_us'))} | "
        f"{f(m('dc_ro_gap_mean_us'))} | {f(m('local_flag_opportunity'))} | {f(m('ro_eligible_rate_k1'))} / {f(m('ro_eligible_rate_k4'))} / {f(m('ro_eligible_rate_k8'))} | "
        f"{f(hf[0])} / {f(hf[1])} / {f(hf[3])} / {f(hf[4])} | {f(m('dc_generation'))} / {f(m('dc_late_epoch'))} | {f(m('update_commits_per_s'))} | {f(m('abort_rate'))} |")
lines += ["", "## D-F (境界年齢の平均 µs と公開/s の、条件間の総差と交互作用。3 反復平均どうしの差)", "",
          "| 系列 | gc µs | 指標 | r | 長い tx | ro の総差 | 長い tx の総差 | 交互作用 |", "|---|---|---|---|---|---|---|---|"]
for e in df:
    lines.append(f"| {e['prefix']} | {e['gc']} | {e['metric']} | {e['r']} | {e['long'] or '—'} | {f(e.get('ro_total_diff'))} | {f(e.get('long_total_diff'))} | {f(e.get('interaction'))} |")
(OUT / "summary.md").write_text("\n".join(lines) + "\n")
print("conditions", len(table), "df rows", len(df))
```

## ranges.py

```python
#!/usr/bin/env python3
"""一次資料に書く範囲 (最小・最大) を summary.json から検算する (読むだけ)。"""
import json

s = json.load(open("/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/analysis/out/summary.json"))
C = s["conditions"]


def m(c, k):
    return C[c]["agg"][k]["mean"]


def rng(cs, k):
    v = [(m(c, k), c) for c in cs if m(c, k) is not None]
    return (min(v), max(v)) if v else None


RST = [c for c in C if c[0] in "RST"]
ro_pos = [c for c in RST if not c[1:].split("-")[0] == "0"]
nolong_ro = [c for c in ro_pos if "-none-" in c]
print("anchor", {c: {k: m(c, k) for k in ("ro_deep_rate_k1", "ro_deep_rate_k8", "publications_per_s", "boundary_p50_bucket_us", "realized_ro_attempt")}
                 for c in ("B-none-gc10", "B-wait10ms-gc10")})
print("ro share of deep K1 (r>=25):", rng(ro_pos, "ro_share_of_deep_k1"))
print("ro share of deep K4 (r>=25):", rng(ro_pos, "ro_share_of_deep_k4"))
print("update deep K1 (all RST):", rng(RST, "update_deep_rate_k1"))
for pre in "RST":
    for gc in (10, 1000, 100000):
        cs = [c for c in nolong_ro if c[0] == pre and c.endswith(f"-gc{gc}")]
        if cs:
            print(pre, gc, "ro deep K1", rng(cs, "ro_deep_rate_k1"), "eligible K1", rng(cs, "ro_eligible_rate_k1"),
                  "(b)", rng(cs, "local_flag_opportunity"))
wr = [c for c in RST if "wait10msR" in c]
print("wait10msR ro deep K1", rng([c for c in wr if not c[1:].startswith("0-")], "ro_deep_rate_k1"), "eligible", rng(wr, "ro_eligible_rate_k1"),
      "pubs", rng(wr, "publications_per_s"), "snapshot age", rng(wr, "ro_snapshot_age_mean_us"))
for pre, gc in (("R", 10), ("R", 1000), ("R", 100000), ("S", 10), ("S", 100000), ("T", 10), ("T", 100000)):
    cs = [c for c in RST if c[0] == pre and c.endswith(f"-none-gc{gc}")]
    print(pre, gc, "boundary mean", rng(cs, "boundary_mean_us"), "p50", sorted({m(c, 'boundary_p50_bucket_us') for c in cs}))
excl = []
for c in C:
    for r in C[c]["reps"]:
        if r["publish_count"]:
            excl.append(((r["dc_generation"] + r["dc_missing"] + r["dc_negative"]) / r["publish_count"], c, r["publish_count"]))
print("max exclusion share", max(excl))
print("dc_epoch_mismatch total", sum(r["dc_epoch_mismatch"] for c in C for r in C[c]["reps"]))
holder_ro = [(m(c, "holder_fraction") if False else C[c]["agg"]["holder_fraction"][3]["mean"], c) for c in nolong_ro if C[c]["agg"]["holder_fraction"][3]["mean"] is not None]
print("holder ro share range", min(holder_ro), max(holder_ro))
```
