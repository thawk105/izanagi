# 集計 script (repo 外で実行、逐語)

- 置き場 (repo 外、永続を保証しない): `/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/summarize.py`
- sha256: `346c86393c5f315075b1e95abe7bce013b72c4032219c18d179c554c003bfe51`
- 実行: `python3 summarize.py analysis` (入力は作図器の出力 `analysis/all_points.csv`・`abort_reasons.csv`・`hot_chains.csv`、出力 `analysis/summary.md`)

```python
#!/usr/bin/env python3
"""集計 (repo 外): analysis/all_points.csv・abort_reasons.csv・hot_chains.csv → analysis/summary.md。
定義は作図器 (tools/plotting/plot_vhash_workload_space.py) の出力列をそのまま使い、新しい指標は作らない。"""
import csv, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

A = Path(sys.argv[1])
rows = list(csv.DictReader(open(A / "all_points.csv")))
ab = list(csv.DictReader(open(A / "abort_reasons.csv")))
hot = list(csv.DictReader(open(A / "hot_chains.csv")))
out = []
p = out.append


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def gclass(r):
    return "default" if r["genome"] == "default" else "best"


def lay(r):
    return "S" if r["layer"] == "S" else "O"


def med(vals):
    v = [x for x in vals if x is not None]
    return st.median(v) if v else None


def fmt(x, n=3):
    if x is None:
        return "—"
    if x == float("inf"):
        return "∞"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{n}g}"


p("# 集計 (生成: summarize.py、入力 analysis/all_points.csv ほか)\n")
p(f"点 × genome の行数: {len(rows)}\n")
p("## 1. 述語の状態の件数 (層 × genome)\n")
p("| H | 層 | genome | 通過 | 停止 | 境界 | 不通過 | 判定不能 |")
p("|---|---|---|---|---|---|---|---|")
for h in ("H1", "H2", "H4-lag", "H4-live", "H4"):
    for L in ("S", "O"):
        for g in ("default", "best"):
            c = Counter(r[h] for r in rows if lay(r) == L and gclass(r) == g)
            p(f"| {h} | {L} | {g} | {c['通過']} | {c['停止']} | {c['境界']} | {c['不通過']} | {c['判定不能']} |")
p("")

p("## 2. 層 S (中心: record 100 万・操作 10・ro 0%・値 4 B・thread 48・gc 100 µs)\n")
p("u1 = update read の位置 ≥ 1 の割合、h1 = 全 read の位置 ≥ 1、d8 = 位置 ≥ 8、h2 = 候補 (K=1) / update read、cK1 = 候補 / 位置 ≥ 1 の update read、"
  "abort = abort 率、lag = 境界年齢 p50 bucket 上界 µs、pub = 公開回数 / 3 s、live = 論理生存版数 / record 数、chain = 熱いキー 0〜7 の鎖長の最大 (2 反復平均)。\n")
p("| rr | 長い tx | skew | genome | u1 | h1 | d8 | h2 | cK1 | abort | lag | pub | live | chain |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
S = sorted((r for r in rows if lay(r) == "S"), key=lambda r: (int(r["rr"]), r["long"], float(r["skew"]), r["genome"]))
for r in S:
    p(f"| {r['rr']} | {r['long']} | {r['skew']} | {gclass(r)} | {fmt(f(r['u1_mean']))} | {fmt(f(r['h1_mean']))} | {fmt(f(r['depth8_mean']))} | "
      f"{fmt(f(r['h2_mean']))} | {fmt(f(r['candidate_k1_rate_mean']))} | {fmt(f(r['abort_rate_mean']))} | {fmt(f(r['lag_us_mean']))} | "
      f"{fmt(f(r['publications_mean']))} | {fmt(f(r['live_ratio_mean']))} | {fmt(f(r['hot_chain_max_mean']))} |")
p("")

p("## 3. 層 O の水準別の中央値 (O1+O2 の各 18 点、genome 別)\n")
factors = ["skew", "rr", "records", "ops", "long", "ro", "val", "threads", "gc"]
p("| 因子 | 水準 | genome | h1 | u1 | h2 | abort | lag | live | H1 通過 | H2 通過 | H4 通過 |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|")
O = [r for r in rows if lay(r) == "O"]
for fac in factors:
    levels = sorted({r[fac] for r in O}, key=lambda x: (f(x) is None, f(x) if f(x) is not None else x))
    for lv in levels:
        for g in ("default", "best"):
            sub = [r for r in O if r[fac] == lv and gclass(r) == g]
            lagv = [float("inf") if f(r["publications_mean"]) == 0 else f(r["lag_us_mean"]) for r in sub]
            ok = lambda h: sum(r[h] in ("通過", "停止") for r in sub)
            p(f"| {fac} | {lv} | {g} | {fmt(med(f(r['h1_mean']) for r in sub))} | {fmt(med(f(r['u1_mean']) for r in sub))} | "
              f"{fmt(med(f(r['h2_mean']) for r in sub))} | {fmt(med(f(r['abort_rate_mean']) for r in sub))} | {fmt(med(lagv))} | "
              f"{fmt(med(f(r['live_ratio_mean']) for r in sub))} | {ok('H1')}/{len(sub)} | {ok('H2')}/{len(sub)} | {ok('H4')}/{len(sub)} |")
p("")

p("## 4. abort 理由の内訳 (層 × genome、全反復の合計に対する割合)\n")
reasons = []
for r in ab:
    if r["reason"] not in reasons:
        reasons.append(r["reason"])
p("| 層 | genome | abort 合計 | " + " | ".join(reasons) + " |")
p("|---|---|---|" + "---|" * len(reasons))
for L in ("S", "O"):
    for g in ("default", "best"):
        tot = Counter()
        for r in ab:
            if ("S" if r["layer"] == "S" else "O") == L and ("default" if r["genome"] == "default" else "best") == g:
                tot[r["reason"]] += int(r["total"])
        s = sum(tot.values())
        p(f"| {L} | {g} | {s:,} | " + " | ".join(f"{tot[x]/s:.3f}" if s else "—" for x in reasons) + " |")
p("")

p("## 5. 熱いキーの鎖長 (層 S・長い tx なし、key 0 の鎖長の 2 反復平均; 熱いキー数は zipf の式による解析値)\n")
p("| skew | rr | genome | key 0 の鎖長 | 質量の半分を占める key 数 (解析) |")
p("|---|---|---|---|---|")
agg = defaultdict(list)
half = {}
for r in hot:
    if r["layer"] == "S" and r["long"] == "none" and r["key"] == "0" and r["chain_status"] == "ok":
        k = (float(r["skew"]), int(r["rr"]), "default" if r["genome"] == "default" else "best")
        agg[k].append(float(r["chain_length"]))
        half[k] = r["zipf_analytic_keys_for_half_mass"]
for k in sorted(agg):
    p(f"| {k[0]} | {k[1]} | {k[2]} | {fmt(st.mean(agg[k]))} | {half[k]} |")
status = Counter(r["chain_status"] for r in hot)
p(f"\n鎖長の状態の件数 (全行): {dict(status)}\n")
(A / "summary.md").write_text("\n".join(out).rstrip("\n") + "\n")
print("\n".join(out[:40]))
```
