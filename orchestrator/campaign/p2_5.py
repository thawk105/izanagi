# -*- coding: utf-8 -*-
"""P2-5 主ドライバ: 誘導 (LLM critic) / ランダム / critic 無し貪欲 / オラクル天井 を集計。

Phase 2 主実験の集計層。各 workload で「winner-tied set 初到達までの評価本数」を 4 系列で比べる:
- random — 解析期待 (N+1)/(k+1) (LLM なし、search_baselines)
- critic 無し貪欲 — digest 勾配のみ (LLM なし、search_baselines)
- オラクル天井 — 初手ランダム制約下の理論下限 2-k/N (LLM なし)
- **誘導** — 中立 critic-experiment エージェントの K 試行 (guided.py で記録した WAL を集計)

主指標は確率優越 a = P(戦略<random) + 0.5·P(=) (tie 半加算、同分布で厳密 0.500。D29 —
旧主指標 p_lt は同分布でも 0.5 を下回る系統バイアスがあり下限 bracket に格下げ) + 効果量
(本数差)。silo 8 では誘導が機械的勾配 (貪欲) で達成できる水準を超えず (直接 A で有意差
なし)、deceptive 構造では貪欲より有意に有害 (= negative result) であることを、誘導の知能を
貪欲と分離して示す。a の 0.5 からの分離を t 検定で主張しない (分散縮小で過大評価しうる、
D29 — 有意主張は exact / permutation で)。

新規直列計測ゼロ (全系列 replay)。誘導試行は p2-5-guided-<wl>-s<seed> 各 WAL に永続化済み。
事前登録: winner-tied set (equivalence class + floor 0.030) と perfect-critic 天井は実験前に凍結。

  python orchestrator/campaign/p2_5.py            # 全 workload 集計 + JSON 出力
"""
from __future__ import annotations

import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import guided                                       # noqa: E402
from campaign import search_baselines as sb                       # noqa: E402
from campaign.layout import repo_output_root                      # noqa: E402
from campaign.p2_2 import BETWEEN_RUN_CV, WORKLOADS               # noqa: E402

GUIDED_PREFIX = "p2-5-guided-"


def guided_trials(wl: str, budget: int, root: str = ""):
    """p2-5-guided-<wl>-s* の試行 WAL から到達本数 + 詳細を集める。

    **未到達 (critic が tied set を踏まずに早期停止) は到達本数 = 予算上限 budget (=N, 最悪) に
    算入する** (落とさない、批判3-#9)。早期の誤収束を低コストの成功と誤計上すると誘導に有利な
    偏りになる。到達本数 (reached_cost) は trajectory に tied member が出る位置だが、出ないまま
    critic が done した試行は「見つけられなかった」= 全探索 N 本に縮退とみなすのが honest。"""
    base = root or repo_output_root()
    pat = os.path.join(base, "campaigns", f"{GUIDED_PREFIX}{wl}-s*")
    costs, details, failures = [], [], 0
    for d in sorted(glob.glob(pat)):
        if not os.path.exists(os.path.join(d, "runs", "wal.jsonl")):
            continue
        trial = os.path.basename(d)[len(GUIDED_PREFIX):]
        r = guided.trial_result(trial, root)
        if r["reached"]:
            costs.append(r["reached_cost"])
        else:
            costs.append(budget)        # 未到達 = 予算上限 N (最悪) に算入
            failures += 1
        details.append(r)
    return costs, details, failures


def summarize(costs):
    if not costs:
        return None
    cs = sorted(costs)
    n = len(cs)
    return {"n": n, "mean": statistics.mean(cs), "median": statistics.median(cs),
            "min": cs[0], "max": cs[-1],
            "iqr_lo": cs[n // 4], "iqr_hi": cs[min(n - 1, (3 * n) // 4)]}


def run(k_baseline: int = 500, root: str = ""):
    rows = []
    for tag, _wl in WORKLOADS:
        b = sb.run_workload(tag, k_trials=k_baseline)
        gcosts, gdet, gfail = guided_trials(tag, b.n, root)
        gps = sb.prob_superiority(b.greedy_costs, b.random_dist)
        ups = sb.prob_superiority(gcosts, b.random_dist) if gcosts else None
        rows.append({
            "workload": tag, "n": b.n, "k": b.k, "tied_set": b.tied_labels,
            "random_E": b.random_E, "random_emp_E": b.random_emp_E,
            "oracle_E": b.oracle_E,
            "greedy": summarize(b.greedy_costs),
            "greedy_p_lt": gps["p_lt"],
            "greedy_a": gps["a"],                 # 主指標 (tie 半加算、null=0.500。D29)
            "guided": summarize(gcosts),
            "guided_p_lt": ups["p_lt"] if ups else None,
            "guided_a": ups["a"] if ups else None,
            # 誘導 vs 貪欲の直接確率優越 (どちらも経験標本)。有意主張は permutation で (D29)
            "guided_vs_greedy_A": (sb.prob_superiority_two_sample(gcosts, b.greedy_costs)
                                   if gcosts else None),
            "guided_costs": sorted(gcosts),
            "guided_failures": gfail,    # critic done で未到達 (誤収束) した試行数
            "guided_n": len(gcosts),
            "informative": b.k == 1,     # k=空間の半分の workload は到達判定が情報を持たない
            # per-trial 軌跡を保存し raw 試行 WAL を消せるようにする (証拠連鎖は P2-2 WAL +
            # この軌跡で保持。fitness は replay 元 = P2-2 にある)。
            "guided_trials": [{"seed": d["seed"], "trajectory": d["trajectory"],
                               "final_pick": d["final_pick"], "reached": d["reached"],
                               "n_evaluated": d["n_evaluated"]} for d in gdet],
        })
    return rows


def _fmt_summ(s):
    if not s:
        return "(試行なし)"
    return (f"中央値={s['median']:.0f} 平均={s['mean']:.2f} "
            f"IQR=[{s['iqr_lo']:.0f},{s['iqr_hi']:.0f}] n={s['n']}")


def main(argv) -> int:
    rows = run()
    print(f"# P2-5 集計 — 誘導 (LLM critic) vs random / 貪欲 / オラクル "
          f"(replay, floor {BETWEEN_RUN_CV*100:.1f}%)\n")
    for r in rows:
        tag_note = "" if r["informative"] else "  ※k=空間の半分=到達判定が情報を持たない (主張対象外)"
        print(f"== {r['workload']}  (N={r['n']}, winner-tied k={r['k']} {r['tied_set']}){tag_note} ==")
        print(f"  random  : E={r['random_E']:.2f} 本 (解析)")
        print(f"  オラクル天井: E={r['oracle_E']:.2f} 本")
        print(f"  貪欲(LLMなし): {_fmt_summ(r['greedy'])}  優越 a={r['greedy_a']:.3f} "
              f"(strict {r['greedy_p_lt']:.3f})")
        g = r["guided"]
        if g:
            print(f"  **誘導(LLM)** : {_fmt_summ(g)}  優越 a={r['guided_a']:.3f} "
                  f"(strict {r['guided_p_lt']:.3f})  vs貪欲 A={r['guided_vs_greedy_A']:.3f}  "
                  f"誤収束(未到達)={r['guided_failures']}/{r['guided_n']}")
            print(f"     到達本数 (未到達は N={r['n']} に算入) = {r['guided_costs']}")
            adv_r = r["random_E"] - g["mean"]
            adv_g = (r["greedy"]["mean"] - g["mean"]) if r["greedy"] else float("nan")
            print(f"     → 誘導の対 random 平均削減 = {adv_r:+.2f} 本 / 対 貪欲 = {adv_g:+.2f} 本 "
                  f"(オラクル天井までの余地 = {r['random_E']-r['oracle_E']:+.2f})")
        else:
            print("  **誘導(LLM)** : (試行 WAL がまだ無い — workflow 完了後に再実行)")
        print()

    # JSON 永続化 (report/insight 用)。**guided 試行が 1 件も無い時は上書きしない**
    # (raw 試行 WAL を消した後に再実行して凍結済み結果を空で潰す footgun を防ぐ)。
    out_path = os.path.join(repo_output_root(), "campaigns", "p2-5-summary.json")
    total_guided = sum(r["guided_n"] for r in rows)
    if total_guided == 0 and os.path.exists(out_path):
        print(f"guided 試行 WAL が見つからない → 既存 {out_path} を保護のため上書きしない "
              "(誘導アームを回すには workflow p2-5-guided-trials を再実行)")
        return 0
    payload = {"floor": BETWEEN_RUN_CV, "rows": rows}
    if os.path.exists(out_path):
        # 追記キー (recalibration 等の事後分析セクション) を再実行で消さない (D29 footgun)
        try:
            with open(out_path, encoding="utf-8") as f:
                for k, v in json.load(f).items():
                    payload.setdefault(k, v)
        except json.JSONDecodeError as e:
            print(f"既存 JSON が壊れているため追記キーを引き継げない: {e}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"集計 JSON: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
