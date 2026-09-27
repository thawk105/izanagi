# 集計・計算 script の逐語 (repo 外 job dir の原本の写し、.py を repo に置かないため .md に貼る)

## job_costs.py

```python
"""試走 v2 の 18 job の Elapse と queue 待ちを job.stderr の NQSV 終了票から抜き出す (repo 外の集計用)。"""
import json, re, sys
from datetime import datetime
from pathlib import Path

EVID = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/evidence/t2850-trial-v2")
FMT = "%a %b %d %H:%M:%S %Y"
out = {}
for d in sorted(EVID.iterdir()):
    text = (d / "job.stderr").read_text(errors="replace")
    rid = re.findall(r"Request ID:\s+(\S+)", text)
    el = re.findall(r"(?m)^\s+Elapse:\s+(\d+)S", text)
    cr = re.findall(r"Created Request Time:\s+(.+)", text)
    st = re.findall(r"Started Request Time:\s+(.+)", text)
    en = re.findall(r"Ended Request Time:\s+(.+)", text)
    if len(rid) != 1 or len(el) != 1:
        print("NG", d.name, rid, el, file=sys.stderr)
        continue
    c, s, e = (datetime.strptime(x[0].strip(), FMT) for x in (cr, st, en))
    out["0:" + rid[0]] = {"job": d.name, "elapse_s": int(el[0]), "queue_wait_s": int((s - c).total_seconds()),
                          "started": s.isoformat(), "ended": e.isoformat(),
                          "source": str(d / "job.stderr")}
json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
```

## run_aggregate.sh

```bash
#!/bin/bash
# 試走 v2 の固定 commit (299aa022e) の checkout tree-01 の harness で集計する (読むだけ、出力は job dir)。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup
T=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2
cd "$T/trees/tree-01" || exit 2
python3 -m orchestrator.campaign.t2849_comparison_harness aggregate \
  --cohort-root "$T/cohort-trial" --job-costs "$J/job-costs.json" --out "$J/aggregate.json"
echo "rc=$?"
```

## failures.py

```python
"""試走 v2 の台帳 event から、欠測・拒否・retry・静定・検査の内訳を系列ごとに数える (repo 外の集計用、読むだけ)。"""
import collections, json, sys
from pathlib import Path

ROOT = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/cohort-trial/write-heavy")
mode = sys.argv[1] if len(sys.argv) > 1 else "summary"


def events(series_dir):
    return [json.loads(p.read_text()) for p in sorted((series_dir / "events").glob("*.json"))]


if mode == "keys":
    ev = events(ROOT / "llm" / "series-2")
    print(collections.Counter(e["kind"] for e in ev))
    for e in ev:
        if e["kind"] in ("proposal-rejected", "evaluation-result", "series-end"):
            print(e["kind"], sorted(e.keys()))
            break
    for e in ev:
        if e["kind"] == "proposal-rejected":
            print(json.dumps({k: e.get(k) for k in ("a", "b", "reject_class", "note")}, ensure_ascii=False)[:500])
    sys.exit(0)

rows = []
for series_dir in sorted(ROOT.glob("*/*")):
    ev = events(series_dir)
    kinds = collections.Counter(e["kind"] for e in ev)
    outcomes = collections.Counter((e.get("kind"), e.get("slot_kind"), e.get("outcome"), e.get("quality"))
                                   for e in ev if e.get("outcome") is not None)
    rejects = collections.Counter(e.get("reject_class") for e in ev if e["kind"] == "proposal-rejected")
    notes = [e.get("note") for e in ev if e["kind"] == "proposal-rejected"]
    text = json.dumps(ev, ensure_ascii=False)
    rows.append({"series": f"{series_dir.parent.name}/{series_dir.name}", "kinds": dict(kinds),
                 "outcomes": {"|".join(map(str, k)): v for k, v in outcomes.items()},
                 "rejects": dict(rejects), "reject_notes": notes,
                 "verify_local_unavailable": text.count("verify-local-unavailable"),
                 "http_429": text.count("429"), "quality_missing": text.count("quality-missing"),
                 "end": ev[-1] if ev and ev[-1]["kind"] == "series-end" else None})
json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
```

## section8.py

```python
"""[T-2850] 試走 v2 (cohort t2850-trial-v2) から事前登録 §8.1 の入力と §8.2 の規模を計算する (repo 外、読むだけ)。

入力: harness の aggregate 出力 (aggregate.json、固定 commit 299aa022e の木で作成)、job-costs.json (NQSV 終了票の Elapse)、台帳 event。
手法間の差 (どの手法が勝ったか) と曲線は出力しない (§8.1)。score は cell ごとの ln score の標本 SD にだけ使う。
"""
import json, math, statistics
from datetime import datetime
from pathlib import Path

J = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup")
ROOT = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/cohort-trial/write-heavy")
ARMS = ["random", "sweep", "bo", "evolution", "llm"]
NONLLM = ARMS[:4]
agg = json.loads((J / "aggregate.json").read_text())
costs = json.loads((J / "job-costs.json").read_text())


def utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def events(d):
    return [json.loads(p.read_text()) for p in sorted((d / "events").glob("*.json"))]


out = {"cohort": agg["cohort"], "mismatches": agg["mismatches"]}

# --- job Elapse (node 時間) ---
elapse = {v["job"]: v["elapse_s"] for v in costs.values()}
cell_elapse = {m: [elapse[f"S1-wh_{m}_s{b}"] for b in (1, 2, 3)] for m in ARMS}
block_elapse = [elapse[f"S1-wh_block_s{b}"] for b in (1, 2, 3)]
out["job_elapse_total_s"] = sum(elapse.values())
out["job_elapse_total_h"] = sum(elapse.values()) / 3600
out["cell_elapse_s"] = cell_elapse
out["block_elapse_s"] = block_elapse
out["queue_wait_s"] = {v["job"]: v["queue_wait_s"] for v in costs.values()}

# --- s_{t,m}: E_B の score が得られた系列の ln score の標本 SD ---
rows = {(r["arm"], r["series"]): r for r in agg["series"]}
status = {m: [rows[(m, b)]["status"] for b in (1, 2, 3)] for m in ARMS}
lnscore = {m: [math.log(rows[(m, b)]["score"]) for b in (1, 2, 3) if rows[(m, b)]["score"] is not None] for m in ARMS}
s_cell = {m: statistics.stdev(v) if len(v) >= 2 else None for m, v in lnscore.items()}
out["status"] = status
out["n_scores"] = {m: len(v) for m, v in lnscore.items()}
out["n_fallback"] = {m: sum(s.startswith("fallback") for s in status[m]) for m in ARMS}
out["s_cell"] = s_cell
pairs = [(ARMS[i], ARMS[j]) for i in range(5) for j in range(i + 1, 5)]
pair_sd = {f"{a}-{b}": math.sqrt(s_cell[a] ** 2 + s_cell[b] ** 2) for a, b in pairs}
out["pair_sd"] = pair_sd
s_plan = max(pair_sd.values())
out["s_plan"] = s_plan
out["s_plan_pair"] = max(pair_sd, key=pair_sd.get)
out["not_computed_conditions"] = {
    "a_cell_with_lt2_scores": [m for m in ARMS if len(lnscore[m]) < 2],
    "b_cell_with_zero_sd": [m for m in ARMS if s_cell[m] == 0],
    # (c) 費用上限 (§9.2) で試走が未完に終わった: 予定 18 job がすべて投入・終了し、全系列が series-end で終端したかで判定する。
    # 総費用は別欄 (job_elapse_total_h) に置く。
    "c_trial_unfinished_by_cap": not (len(elapse) == 18 and all(
        rows[(m, b)]["status"] is not None and rows[(m, b)]["a"] is not None for m in ARMS for b in (1, 2, 3)))}
out["series_end_reasons"] = sorted({json.loads(sorted((ROOT / m / f"series-{b}" / "events").glob("*series-end*"))[-1].read_text())["reason"]
                                    for m in ARMS for b in (1, 2, 3)} | {
    json.loads(sorted((ROOT / "controls" / f"block-{b}" / "events").glob("*series-end*"))[-1].read_text())["reason"] for b in (1, 2, 3)})

# --- T_c(wh): 非 LLM 4 手法で B に達した系列の (B 番目の探索評価の available − t0) の中央値、秒へ切り上げ ---
tc, reached, not_reached = {}, [], []
session_walls, score_walls = [], []
llm_wait = {}
for d in sorted(ROOT.glob("*/*")):
    ev = events(d)
    seen = {}
    for e in ev:
        t = e.get("timing") or {}
        if e.get("slot_key") and t.get("subprocess_wall_s") is not None:
            seen[e["slot_key"]] = e
    for e in seen.values():
        session_walls.append(e["timing"]["subprocess_wall_s"])
        if e.get("slot_kind") == "score":
            score_walls.append(e["timing"]["subprocess_wall_s"])
    arm = d.parent.name
    if arm == "controls":
        continue
    start = next(e for e in ev if e["kind"] == "stock-start")
    t0 = utc(start["timing"]["started_utc"])
    bth = [e for e in ev if e["kind"] == "evaluation-result" and e.get("slot_kind") == "search" and e.get("b") == 10]
    key = f"{arm}/{d.name}"
    if bth:
        tc[key] = (utc(bth[0]["timing"]["available_utc"]) - t0).total_seconds()
    if arm in NONLLM:
        (reached if bth else not_reached).append(key)
    if arm == "llm":
        opp = {}
        for e in ev:
            if e.get("a") and (e["kind"] in {"evaluation-result", "proposal-rejected"}):
                opp[e["a"]] = (e.get("timing") or {}).get("proposal_wait_wall_s", 0)
        llm_wait[key] = {"sum_s": sum(opp.values()), "opportunities": len(opp)}
out["elapsed_to_B_s"] = tc
out["T_c_s"] = math.ceil(statistics.median([tc[k] for k in reached])) if reached else None
out["T_c_reached"] = len(reached)
out["T_c_not_reached"] = not_reached
out["session_wall_median_s"] = statistics.median(session_walls)
out["session_wall_n"] = len(session_walls)
out["score_session_wall_median_s"] = statistics.median(score_walls)
out["llm_serial_s"] = llm_wait
ell = statistics.median(v["sum_s"] for v in llm_wait.values())
out["ell_wh_s"] = ell

# --- c(wh, m) = cell の job Elapse の中央値 + block job Elapse の中央値 / 5 + 5 × session 所要の中央値 ---
c = {m: statistics.median(cell_elapse[m]) + statistics.median(block_elapse) / 5 + 5 * out["session_wall_median_s"] for m in ARMS}
out["c_wh_s"] = c
out["c_wh_block_s"] = sum(c.values())
out["series_duration_median_s"] = {m: statistics.median(cell_elapse[m]) for m in ARMS}


# --- §8.2 ---
def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    cc, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > FPMIN else FPMIN); h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        cc = 1 + aa / cc; cc = cc if abs(cc) > FPMIN else FPMIN; h *= d * cc
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        cc = 1 + aa / cc; cc = cc if abs(cc) > FPMIN else FPMIN
        de = d * cc; h *= de
        if abs(de - 1) < EPS: break
    return h


def betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    return bt * betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t); p = 0.5 * betai(df / 2, 0.5, x)
    return 1 - p if t > 0 else p


def t_q(p, df):
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


assert abs(t_q(0.975, 7) - 2.3646) < 1e-3
DELTA, H2 = math.log(1.03), math.log(1.05)


def h(n, s, M):
    return t_q(1 - 0.025 / M, n - 1) * s / math.sqrt(n)


def nmin(target, s, M):
    n = 5
    while h(n, s, M) > target:
        n += 1
    return n


plans = {}
for q in (1, 2, 3):
    M = 10 * q
    n1, n2 = nmin(DELTA / 2, s_plan, M), nmin(H2, s_plan, M)
    plans[f"|Q|={q}"] = {"M": M, "n1": n1, "h_n1": h(n1, s_plan, M), "n2": n2, "h_n2": h(n2, s_plan, M),
                         "h5": h(5, s_plan, M), "t_q_n1": t_q(1 - 0.025 / M, n1 - 1)}
out["plans"] = plans
out["delta"] = DELTA
out["ln105"] = H2
print(json.dumps(out, ensure_ascii=False, indent=1))
```

## estimate_main.py

```python
"""[T-2850] 本比較の node 時間・LLM 直列時間・暦の見積り (repo 外、section8.json を入力に取る)。

出所の区別: 実測 = 試走 v2 の job Elapse・台帳。換算 = 別の実測 (B-5 v1 の直列検査の系列 Elapse) に構成差を当てた値。
規則どおりの値 (事前登録 §8.1: 試走していない課題は手法ごとに試走課題の最大値) と、換算値を分けて出す。
"""
import json, math, statistics
from pathlib import Path

J = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup")
s8 = json.loads((J / "section8.json").read_text())
ARMS = ["random", "sweep", "bo", "evolution", "llm"]
H = 3600.0
c_wh = s8["c_wh_s"]
block_wh = sum(c_wh.values())
cell = s8["cell_elapse_s"]
blk = s8["block_elapse_s"]
sess = s8["session_wall_median_s"]
ell = s8["ell_wh_s"]
out = {"c_wh_block_h": block_wh / H}

# 規則どおり (bal・rh は wh の値を流用、未検証の外挿。rh は追補 1 §4.3 で過小と分かっている)
rule = {"wh": block_wh, "bal": block_wh, "rh": block_wh}

# 換算 (B-5 v1 の直列検査、t2797-b5-cost-options §2): 非 LLM 系列 16 session の Elapse と 1 評価 session の平均。
# 本書の系列は 18 session (初期点 2 を足す)。E_T の再計測 5 session は score session の所要で足す。
b5 = {"bal": {"series16": (9149, 10076), "eval_mean": 5536 / 10, "score_mean": 3721 / 5, "stock": 305,
              "block10": None},
      "rh": {"series16": (26191, 26846), "eval_mean": 14607 / 10, "score_mean": 11157 / 5, "stock": 721,
             "block10": None}}
conv = {}
for t, v in b5.items():
    lo, hi = v["series16"]
    series18 = (lo + 2 * v["eval_mean"], hi + 2 * v["eval_mean"])
    # block job 10 session (stock 5 + 参照点 5)。参照点の直列所要は未測定なので stock 5 + 評価平均 5 で置く (換算)
    block10 = 5 * v["stock"] + 5 * v["eval_mean"]
    et = 5 * v["score_mean"]
    nonllm = tuple(s + block10 / 5 + et for s in series18)
    llm = tuple(x + ell for x in nonllm)  # ℓ(t') = 試走課題の ℓ の最大 (= wh)
    per_block = tuple(4 * a + b for a, b in zip(nonllm, llm))
    conv[t] = {"series18_s": series18, "block10_s": block10, "et5_s": et, "c_nonllm_s": nonllm, "c_llm_s": llm,
               "block_h": tuple(x / H for x in per_block)}
out["conversion"] = conv

plans = s8["plans"]
table = []
for q, name in ((("wh",), "wh"), (("wh", "bal"), "wh+bal"), (("wh", "rh"), "wh+rh"), (("wh", "bal", "rh"), "wh+bal+rh")):
    p = plans[f"|Q|={len(q)}"]
    rule_block = sum(rule[t] for t in q) / H
    conv_block = [block_wh / H + sum(conv[t]["block_h"][i] for t in q if t != "wh") for i in (0, 1)]
    for stage, n in (("n1", p["n1"]), ("n2", p["n2"])):
        table.append({"Q": name, "M": p["M"], "stage": stage, "n": n,
                      "C_rule_h": n * rule_block, "C_conv_h": (n * conv_block[0], n * conv_block[1])})
out["C_table"] = table

# wh だけ (n = n2) の幅: 下側 = E_T の再計測なし・中央値、上側 = 各 cell の最大 Elapse + E_T 全系列
n = plans["|Q|=1"]["n2"]
lower = n * (sum(statistics.median(cell[m]) for m in ARMS) + statistics.median(blk)) / H
upper = n * (sum(max(cell[m]) for m in ARMS) + max(blk) + 5 * 5 * sess) / H
out["wh_n2"] = {"n": n, "C_plan_h": n * block_wh / H, "lower_h": lower, "upper_h": upper,
                "jobs": n * 6, "llm_series": n}
# A = 30 を LLM 系列が使い切る場合の親の待ちの上乗せ (事前登録 §9.1 の 780 s / 機会の仮定)
out["wh_n2"]["llm_a30_extra_h"] = n * (30 - 10) * 780 / H

# LLM の直列時間 (§8.3)
llm = s8["llm_serial_s"]
vals = [v["sum_s"] for v in llm.values()]
out["llm_serial"] = {"ell_median_s": ell, "per_series_s": vals,
                     "total_h_median": n * ell / H, "total_h_range": (n * min(vals) / H, n * max(vals) / H),
                     "ideal_calendar_h_p4": n * ell / H / 4,
                     "opportunities_per_series": [v["opportunities"] for v in llm.values()],
                     "opportunities_total_est": n * statistics.median(v["opportunities"] for v in llm.values())}

# 案 (a): node 上の LLM 待ち (LLM 系列の Elapse - 非 LLM 系列の Elapse の中央値) と、待ちの和
nonllm_med = statistics.median(x for m in ARMS[:4] for x in cell[m])
llm_wait_node = [x - nonllm_med for x in cell["llm"]]
out["option_a"] = {"nonllm_series_median_s": nonllm_med, "llm_series_s": cell["llm"],
                   "llm_excess_over_nonllm_s": llm_wait_node,
                   "wh_n2_wait_node_h_by_excess": n * statistics.median(llm_wait_node) / H,
                   "wh_n2_wait_node_h_by_ell": n * ell / H}
print(json.dumps(out, ensure_ascii=False, indent=1))
```

## breakdown.py

```python
"""試走 v2 の slot 所要の内訳 (build・検査・bench 周辺・その他) と bench round 数を集計する (読むだけ、性能値は出さない)。"""
import collections, json, statistics
from pathlib import Path

ROOT = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/cohort-trial/write-heavy")
agg = collections.defaultdict(list)
rounds = collections.Counter()
for d in sorted(ROOT.glob("*/*")):
    seen = {}
    for p in sorted((d / "events").glob("*.json")):
        e = json.loads(p.read_text())
        t = e.get("timing") or {}
        if e.get("slot_key") and t.get("subprocess_wall_s") is not None:
            seen[e["slot_key"]] = e
    for e in seen.values():
        t = e["timing"]
        kind = "control" if d.parent.name == "controls" else e.get("slot_kind")
        for k in ("subprocess_wall_s", "build_wall_s", "verify_total_wall_s", "bench_surrounding_wall_s", "bench_wall_s"):
            agg[(kind, k)].append(t.get(k) or 0.0)
        rounds[(e.get("bench_payload") or {}).get("rounds")] += 1
out = {}
for (kind, k), v in sorted(agg.items()):
    out.setdefault(kind, {"n": len(v)})[k] = {"sum": round(sum(v)), "median": round(statistics.median(v), 1),
                                                 "min": round(min(v), 1), "max": round(max(v), 1)}
tot = {k: sum(sum(agg[(kind, k)]) for kind in out) for k in ("subprocess_wall_s", "build_wall_s", "verify_total_wall_s",
                                                                "bench_surrounding_wall_s")}
out["total"] = {k: round(v) for k, v in tot.items()}
out["total"]["verify_share"] = tot["verify_total_wall_s"] / tot["subprocess_wall_s"]
out["bench_rounds"] = {str(k): v for k, v in rounds.items()}
print(json.dumps(out, ensure_ascii=False, indent=1))
```
