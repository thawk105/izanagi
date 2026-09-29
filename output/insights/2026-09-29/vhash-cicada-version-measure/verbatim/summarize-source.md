# 解析 script の逐語 (repo 外で実行、sha256 6d8086f0c8890913b31d277faaa44d9338ff6cfcfaa0cfe759eec0cb5dea2e06)

```python
#!/usr/bin/env python3
"""vhash md_2: raw (final-j0..j3.json) から条件ごとの数値表を作る (repo 外の解析 script)。

定義は driver (orchestrator/campaign/vhash_cicada_vlife.py) と作図 (tools/plotting/plot_vhash_cicada_vlife.py) と同じ:
- update read の総数 = hops[site 0] の総和、read-only read の総数 = hops[site 1] の総和
- 深部割合 (K) = deep[K] / update read 総数、read-only 深部割合 = readonly_deep[K] / read-only read 総数
- 楽観的候補率 (K) = candidate[K] / deep[K] (分母 0 は欠測)
- 時間系の分位点 = 42 bucket (上界 2^0..2^40 µs + overflow) の累積が q に達した bucket の上界
値は 3 反復それぞれで計算し、平均と [min, max] を出す。throughput は性能値ではないので出さない。
usage: summarize.py <out.json> <out.md> <raw>...
"""
import json
import statistics
import sys
from pathlib import Path

K = (1, 2, 3, 4, 8)


def qbucket(hist, bounds, q):
    total = sum(hist)
    if total == 0:
        return None
    acc = 0
    for count, bound in zip(hist, bounds):
        acc += count
        if acc >= q * total:
            return bound
    return bounds[-1]


def per_run(p, records):
    ws = p["workers"]
    tb = p["time_bucket_bounds"]
    s = lambda f: sum(w[f] for w in ws)
    v = lambda f, i: sum(w[f][i] for w in ws)
    hist = lambda f: [sum(w[f][i] for w in ws) for i in range(len(tb))]
    upd = sum(sum(w["hops"][0]) for w in ws)
    ro = sum(sum(w["hops"][1]) for w in ws)
    out = {"update_reads": upd, "readonly_reads": ro,
           "readonly_attempt_share": s("readonly_attempt") / (v("attempts", 0) + v("attempts", 1)),
           "long_attempts": v("attempts", 1), "long_commits": v("commits", 1), "long_aborts": v("aborts", 1),
           "long_ops": v("operations", 1),
           "long_mean_us": (v("cycles", 1) / (v("commits", 1) + v("aborts", 1)) / p["clocks_per_us"])
           if (v("commits", 1) + v("aborts", 1)) else None,
           "short_commits": v("commits", 0), "short_aborts": v("aborts", 0),
           "install": s("install"), "detach": s("detach"),
           "logical_live_versions": records + s("install") - s("detach"),
           "gc_publications": sum(hist("gc_publish_us")) + 0,
           "gc_boundary_samples": sum(hist("gc_boundary_us")), "gc_negative": s("gc_negative")}
    for i, k in enumerate(K):
        d = v("deep", i)
        out[f"deep_share_K{k}"] = d / upd if upd else None
        out[f"deep_K{k}"] = d
        out[f"candidate_K{k}"] = v("candidate", i)
        out[f"candidate_rate_K{k}"] = v("candidate", i) / d if d else None
        out[f"deep_read_zero_K{k}"] = v("deep_read_zero", i)
        out[f"candidate_read_zero_K{k}"] = v("candidate_read_zero", i)
        out[f"readonly_deep_share_K{k}"] = v("readonly_deep", i) / ro if ro else None
    for f in ("gc_boundary_us", "gc_publish_us", "age_create_us", "age_overwrite_us"):
        h = hist(f)
        out[f + "_p50"] = qbucket(h, tb, 0.5)
        out[f + "_p90"] = qbucket(h, tb, 0.9)
        out[f + "_max"] = qbucket(h, tb, 1.0)
    return out


def agg(values):
    vals = [x for x in values if x is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {"mean": statistics.fmean(vals), "min": min(vals), "max": max(vals), "n": len(vals)}


def main():
    out_json, out_md = Path(sys.argv[1]), Path(sys.argv[2])
    runs, conds, records = {}, {}, None
    for raw in sys.argv[3:]:
        d = json.loads(Path(raw).read_text())
        records = d["records"]
        conds.update(d["conditions"])
        for cid, reps in d["runs"].items():
            assert cid not in runs, cid
            runs[cid] = [per_run(r["parsed"], d["records"]) for r in reps]
    table = {cid: {key: agg([r[key] for r in reps]) for key in reps[0]} for cid, reps in sorted(runs.items())}
    out_json.write_text(json.dumps({"records": records, "conditions": conds, "per_run": runs, "table": table},
                                   ensure_ascii=False, indent=1))
    f = lambda x, n=2: "—" if x is None else (f"{x:.{n}e}" if (abs(x) < 1e-2 and x != 0) else f"{x:.{n}f}")
    lines = ["| 条件 | update read 数 | 深部割合 K=1 / 2 / 4 / 8 | 候補率 K=1 / 2 / 4 / 8 (分母) | read-only 試行割合 | read-only 深部 K=1 / 4 / 8 | 境界年齢 p50 / p90 µs | 公開間隔 p50 / p90 µs | 回収時年齢(上書き) p50 / p90 µs | 論理生存版数 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for cid, t in table.items():
        m = lambda k: t[k]["mean"]
        den = lambda k: sum(r[f"deep_K{k}"] for r in runs[cid])
        lines.append(
            f"| {cid} | {m('update_reads'):.3g} | " + " / ".join(f(m(f'deep_share_K{k}')) for k in (1, 2, 4, 8)) + " | "
            + " / ".join(f"{f(m(f'candidate_rate_K{k}'))} ({den(k)})" for k in (1, 2, 4, 8)) + f" | {f(m('readonly_attempt_share'))} | "
            + " / ".join(f(m(f'readonly_deep_share_K{k}')) for k in (1, 4, 8)) + " | "
            + f"{m('gc_boundary_us_p50'):.0f} / {m('gc_boundary_us_p90'):.0f} | {m('gc_publish_us_p50'):.0f} / {m('gc_publish_us_p90'):.0f} | "
            + f"{m('age_overwrite_us_p50'):.0f} / {m('age_overwrite_us_p90'):.0f} | {m('logical_live_versions'):.3g} |")
    lines += ["", "| 条件 | 長い tx の試行 / commit / abort | 長い tx の平均継続 µs | 長い tx の実行操作数 | 短い tx の commit / abort | 公開回数 | 境界年齢の負値 |", "|---|---|---|---|---|---|---|"]
    for cid, t in table.items():
        m = lambda k: t[k]["mean"]
        lines.append(f"| {cid} | {m('long_attempts'):.0f} / {m('long_commits'):.0f} / {m('long_aborts'):.0f} | "
                     + ("—" if m('long_mean_us') is None else f"{m('long_mean_us'):.0f}")
                     + f" | {m('long_ops'):.0f} | {m('short_commits'):.3g} / {m('short_aborts'):.3g} | {m('gc_publications'):.0f} | {m('gc_negative'):.0f} |")
    out_md.write_text("\n".join(lines) + "\n")
    print("ok", len(table))


if __name__ == "__main__":
    main()
```
