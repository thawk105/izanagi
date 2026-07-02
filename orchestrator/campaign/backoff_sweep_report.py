# -*- coding: utf-8 -*-
"""backoff sweep の材料レポート — throughput を backoff 量の関数として射影。

backoff_sweep.py の WAL を読み、workload ごとに:
  - 静的 backoff の量 (us) に対する throughput / abort_rate / ipc の曲線 (.dat/.plt/.png)
  - 無 backoff (BACK_OFF=0) と stock 適応 (BACKOFF_FIXED=-1) の参照線
  - 「適応が逃した sweet spot」があるか (静的最良 vs 無 vs 適応) を report.md に
を campaigns/<id>/reports/ に出す。critic の帰属 (P2-3) を実 sweep で検証する材料。

  python orchestrator/campaign/backoff_sweep_report.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.backoff_sweep import WORKLOADS, config_for         # noqa: E402
from campaign.p2_2 import BETWEEN_RUN_CV                          # noqa: E402
from campaign.replay import discover_campaign_dir                 # noqa: E402
from critic.digest import load_workload                          # noqa: E402
from reports.plot import DatFile, PlotSpec, Series, make_plot     # noqa: E402


def _classify(g):
    """genome を (種別, 量) に。種別 = none / adaptive / static。"""
    if g.flags.get("BACK_OFF") == 0:
        return ("none", None)
    if g.flags.get("BACKOFF_FIXED", -1) < 0:
        return ("adaptive", None)
    return ("static", g.flags.get("BACKOFF_FIXED"))


def report_workload(tag: str, workload: dict, log=print) -> dict:
    cfg = config_for(tag, workload)
    # C1 回避: campaign-id 再計算 (宣言 ccbench_commit 依存) でなく dir 名 prefix で
    # discover する (+38%/+11% の根拠 sweep が pin 前進で沈黙 skip されていた)。
    try:
        layout = discover_campaign_dir(cfg.spec_slug, cfg.search_tag)
    except FileNotFoundError as e:
        log(f"[{tag}] campaign dir を discover できない → skip: {e}")
        return {}
    genomes = load_workload(layout)
    none_g = adaptive_g = None
    static = []
    for g in genomes:
        kind, amt = _classify(g)
        if kind == "none":
            none_g = g
        elif kind == "adaptive":
            adaptive_g = g
        else:
            static.append((amt, g))
    static.sort(key=lambda t: t[0])
    if not static:
        log(f"[{tag}] 静的点が無い → skip")
        return {}

    def tp(g):
        return g.li.get("throughput_tps") if g else None

    # 静的曲線の .dat
    rows = [[amt, round(tp(g) or 0), round((g.li.get("abort_rate") or 0) * 100, 2),
             round(g.li.get("ipc") or 0, 3)] for amt, g in static]
    none_tp, adap_tp = tp(none_g), tp(adaptive_g)
    best_amt, best_g = max(static, key=lambda t: tp(t[1]) or 0)
    wl_str = ", ".join(f"{k}={v}" for k, v in sorted(workload.items()))
    prov = {
        # on-disk の実 campaign id (dir 名)。再計算 id は C1 drift で実体とずれうる
        "env": "linux-baremetal", "campaign": os.path.basename(layout.root),
        "workload": f"{tag} ({wl_str})", "base": "L-W0 (no-wait-locking, WAL 無)",
        "no_backoff_tps(BACK_OFF=0)": f"{none_tp:,.0f}" if none_tp else "—",
        "adaptive_tps(stock Cicada)": f"{adap_tp:,.0f}" if adap_tp else "—",
        "best_static": f"{best_amt}us = {tp(best_g):,.0f} tps",
        "noise_floor_cv": f"between-run {BETWEEN_RUN_CV * 100:.1f}% (skew0.9, A2)",
    }
    dat = DatFile(
        title=f"backoff sweep: {tag} ({wl_str})",
        columns=["backoff_us", "throughput_tps", "abort_pct", "ipc"],
        rows=rows, provenance=prov,
        build_command="# patches/silo-backoff-fixed.patch を ccbench に適用 (D18)。"
                      "genome に BACKOFF_FIXED=<us> + BACK_OFF=1",
        repro_command="# orchestrator/campaign/backoff_sweep.py (各点の run_cmd は WAL 参照)")
    spec = PlotSpec(
        title=f"backoff sweep — {tag} (skew0.9, static vs none={none_tp:,.0f} / "
              f"adaptive={adap_tp:,.0f})" if none_tp and adap_tp else f"backoff sweep — {tag}",
        xlabel="static backoff magnitude (us)", ylabel="throughput (tps)",
        y2label="abort rate (%)",
        series=[Series("1:2", "throughput (static)", "x1y1", style="linespoints"),
                Series("1:3", "abort rate (static)", "x1y2", style="linespoints")],
        extra_setup=["set yrange [0:*]", "set y2range [0:*]"]
        + ([f'set label "none={none_tp:,.0f}" at graph 0.02,0.95'] if none_tp else []))
    stem = os.path.join(layout.reports_dir, f"backoff-sweep-{tag}")
    os.makedirs(layout.reports_dir, exist_ok=True)
    paths = make_plot(dat, spec, stem)

    md = _md(tag, wl_str, os.path.basename(layout.root), static, none_tp, adap_tp, best_amt, best_g, tp,
             os.path.basename(paths["png"]), os.path.basename(paths["dat"]))
    md_path = os.path.join(layout.reports_dir, f"backoff-sweep-{tag}_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    verdict = _verdict(none_tp, adap_tp, tp(best_g))
    log(f"[{tag}] best static={best_amt}us {tp(best_g):,.0f} tps / none={none_tp:,.0f} / "
        f"adaptive={adap_tp:,.0f} → {verdict}")
    return {"tag": tag, "cid": os.path.basename(layout.root), "none": none_tp, "adaptive": adap_tp,
            "best_amt": best_amt, "best_tps": tp(best_g), "verdict": verdict,
            "report": md_path}


def _verdict(none_tp, adap_tp, best_static) -> str:
    """sweet spot 判定 (between-run noise floor を超えるかで, A2)。"""
    nf = BETWEEN_RUN_CV
    if none_tp is None or best_static is None:
        return "判定不能 (データ欠損)"
    rel_vs_none = best_static / none_tp - 1
    if rel_vs_none > nf:
        return f"静的 backoff が無 backoff を +{rel_vs_none*100:.1f}% 上回る (sweet spot あり)"
    if abs(rel_vs_none) <= nf:
        return f"静的最良も無 backoff と差なし ({rel_vs_none*100:+.1f}%, noise内) = backoff は不要"
    return f"静的最良でも無 backoff に届かず ({rel_vs_none*100:+.1f}%) = backoff は純損"


def _md(tag, wl_str, cid, static, none_tp, adap_tp, best_amt, best_g, tp, png, dat) -> str:
    L = [f"# backoff sweep 材料レポート — {tag}", "",
         "> 自動生成。silo の backoff *量* を単一軸として sweep (patches/silo-backoff-fixed.patch, "
         "D18)。trace-disabled build (規律1)・単一テナント直列 (規律4)・各 genome は verifier 通過。", "",
         f"![backoff sweep {tag}]({png})", "",
         "## 参照", "",
         f"- **無 backoff** (BACK_OFF=0): {none_tp:,.0f} tps" if none_tp else "- 無 backoff: —",
         f"- **stock 適応 backoff** (Cicada hill-climb): {adap_tp:,.0f} tps" if adap_tp else "- 適応: —",
         f"- **静的最良**: {best_amt}us = {tp(best_g):,.0f} tps",
         f"- **判定**: {_verdict(none_tp, adap_tp, tp(best_g))}", "",
         "## 静的 backoff 量に対する曲線", "",
         "| backoff us | throughput tps | abort % | ipc | vs 無 backoff |",
         "|---:|---:|---:|---:|---|"]
    for amt, g in static:
        t = tp(g)
        rel = f"{(t/none_tp-1)*100:+.1f}%" if (none_tp and t) else "—"
        L.append(f"| {amt} | {t:,.0f} | {(g.li.get('abort_rate') or 0)*100:.1f}% | "
                 f"{g.li.get('ipc') or 0:.2f} | {rel} |")
    L += ["",
          "## 読み (critic 帰属の検証)", "",
          "stock 適応 backoff が静的最良に対してどこに居るか = Cicada の hill-climbing が "
          "sweet spot を捉えているか/逃しているかの直接証拠。abort% と ipc の列で「backoff を増やすと "
          "abort は下がるが ipc が落ちる」trade-off が量の関数として見える。", ""]
    return "\n".join(L)


def main() -> int:
    results = [report_workload(tag, wl) for tag, wl in WORKLOADS]
    have = [r for r in results if r]
    if not have:
        print("backoff sweep campaign が無い (backoff_sweep.py を先に実行)。")
        return 1
    print("\n=== backoff sweep サマリ ===")
    for r in have:
        print(f"  {r['tag']}: best static {r['best_amt']}us {r['best_tps']:,.0f} / "
              f"none {r['none']:,.0f} / adaptive {r['adaptive']:,.0f} → {r['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
