# -*- coding: utf-8 -*-
"""P2-2 材料レポート射影器 — campaign WAL → genome 別 fitness ランキング + 分布比較 + グラフ。

silo 全探索 (p2_2.py) の WAL を読み、workload ごとに:
  - genome 別 median tps / CV / unstable を表に
  - 最速 genome を特定し、compare (§3.6(4): noise floor 以下は差なし + Mann-Whitney U) で
    他 genome との差が「信用できる差」かを判定 (unstable は最速判定から除外)
  - gnuplot 棒グラフ (.dat/.plt/.png) + report.md を campaigns/<id>/reports/ に射影
  - WAL に残る実ビルド/実行コマンドを .dat/report.md に埋める (forensic binding, D12)
そして全 workload 横断の summary (最速構成一覧) を campaigns/p2-2-summary.md に出す。

  python orchestrator/campaign/p2_2_report.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrator.stability import compare                        # noqa: E402
from campaign import ident, wal                                 # noqa: E402
from campaign.layout import campaign_layout, repo_output_root   # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_DONE,  # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT)
from campaign.p2_2 import (CLK, EXTIME, RECORDS, THREADS,        # noqa: E402
                           WORKLOADS, config_for)
from reports.plot import DatFile, PlotSpec, Series, make_plot    # noqa: E402

# 確定 calibration の noise floor (skew0.9, worklog 2026-06-18) = 信用してよい差の下限。
NOISE_CV_SKEW09 = 0.0228


def _parse_flags(canonical: str) -> dict:
    return dict(kv.split("=") for kv in canonical.split("|", 1)[1].split(","))


def _short_label(canonical: str) -> str:
    """genome を棒グラフ用の短ラベルに。no-wait は L=即abort(locking) / T=retry(tictoc)。"""
    f = _parse_flags(canonical)
    nw = "L" if f.get("NO_WAIT_LOCKING_IN_VALIDATION") == "1" else "T"
    return f"B{f.get('BACK_OFF','?')}-{nw}-W{f.get('WAL','?')}"


class GRow:
    def __init__(self, variant: str):
        self.variant = variant
        self.genome = ""
        self.tps_list: list = []
        self.median = None
        self.cv = None
        self.unstable = False
        self.committed = False
        self.run_cmd = ""
        self.build_cmd = ""
        self.configure_cmd = ""

    @property
    def label(self) -> str:
        return _short_label(self.genome) if self.genome else self.variant[:8]


def _collect(layout) -> dict:
    rows: dict = {}
    for r in wal.read_records(layout):
        g = rows.setdefault(r.variant, GRow(r.variant))
        p = r.payload
        if r.stage == STAGE_BUILD_START:
            g.genome = p.get("genome", g.genome)
        elif r.stage == STAGE_BUILD_DONE:
            g.build_cmd = p.get("perf_build_cmd", g.build_cmd)
            g.configure_cmd = p.get("perf_configure_cmd", g.configure_cmd)
        elif r.stage == STAGE_BENCH_DONE:
            g.tps_list = p.get("tps", g.tps_list)
            g.median = p.get("median_tps", g.median)
            g.cv = p.get("cv", g.cv)
            g.unstable = p.get("unstable", g.unstable)
            g.run_cmd = p.get("run_cmd", g.run_cmd)
        elif r.stage == STAGE_COMMIT:
            g.committed = True
            if p.get("fitness_tps") is not None:
                g.median = p.get("fitness_tps")
    return rows


def _ranked(rows: dict) -> list:
    """committed かつ median を持つ genome を median 降順で。"""
    rs = [g for g in rows.values() if g.committed and g.median is not None]
    rs.sort(key=lambda g: g.median, reverse=True)
    return rs


def _winner(ranked: list):
    """最速 = median 最大の **stable** な genome (unstable は信用しないので除外)。"""
    for g in ranked:
        if not g.unstable:
            return g
    return ranked[0] if ranked else None


def report_workload(tag: str, workload: dict, log=print) -> dict:
    cfg = config_for(tag, workload)
    cid = ident.campaign_id(cfg)
    layout = campaign_layout(str(cid))
    if not os.path.exists(layout.wal_file):
        log(f"[{tag}] WAL 無し ({layout.root}) — campaign 未実行 → skip")
        return {}
    rows = _collect(layout)
    ranked = _ranked(rows)
    if not ranked:
        log(f"[{tag}] committed genome 無し → skip")
        return {}
    win = _winner(ranked)

    # --- 棒グラフ (.dat/.plt/.png): genome 別 median tps (降順) ---
    dat_rows = [[g.label, round(g.median), round((g.cv or 0) * 100, 2)] for g in ranked]
    wl_str = ", ".join(f"{k}={v}" for k, v in sorted(workload.items()))
    prov = {
        "env": "linux-baremetal", "campaign": str(cid),
        "workload": f"{tag} ({wl_str})",
        "calibration": f"records={RECORDS:,} threads={THREADS} clocks_per_us={CLK} "
                       f"extime={EXTIME}",
        "noise_floor_cv": f"{NOISE_CV_SKEW09 * 100:.2f}% (skew0.9)",
        "genome_label": "B<BACK_OFF>-<L=no-wait-locking/即abort | T=tictoc-no-wait/retry>-W<WAL>",
    }
    dat = DatFile(
        title=f"P2-2 silo fitness: {tag} ({wl_str})",
        columns=["genome", "median_tps", "cv_pct"], rows=dat_rows,
        provenance=prov,
        build_command=f"# 最速 {win.label} のビルド:\n{win.configure_cmd}\n{win.build_cmd}",
        repro_command=f"# 最速 {win.label} の計測 (reps={EXTIME}…は run_cmd 参照):\n{win.run_cmd}")
    spec = PlotSpec(
        title=f"P2-2 silo fitness — {tag} (skew0.9, {THREADS}t, {RECORDS:,} rec)",
        xlabel="genome (B=BACK_OFF, L/T=no-wait policy, W=WAL)",
        ylabel="median throughput (tps)",
        series=[Series("2:xtic(1)", "median tps", style="boxes")],
        extra_setup=["set style fill solid 0.6", "set boxwidth 0.6 relative",
                     "set yrange [0:*]", "set xtics rotate by -30", "unset key"])
    stem = os.path.join(layout.reports_dir, f"p2-2-fitness-{tag}")
    os.makedirs(layout.reports_dir, exist_ok=True)
    paths = make_plot(dat, spec, stem)

    # --- compare: 最速 vs 各 genome (信用できる差か) ---
    verdicts = {}
    for g in ranked:
        if g.variant == win.variant:
            continue
        c = compare(baseline=g.tps_list, variant=win.tps_list, noise_cv=NOISE_CV_SKEW09)
        verdicts[g.variant] = c

    md_path = os.path.join(layout.reports_dir, f"p2-2-fitness-{tag}_report.md")
    _write_md(md_path, tag, wl_str, str(cid), ranked, win, verdicts, prov,
              os.path.basename(paths["png"]), os.path.basename(paths["dat"]),
              os.path.basename(paths["plt"]))
    log(f"[{tag}] 最速={win.label} {win.median:,.0f} tps → {md_path}")
    return {"tag": tag, "cid": str(cid), "winner": win, "ranked": ranked,
            "verdicts": verdicts, "report": md_path, "png": paths["png"]}


def _verdict_str(c) -> str:
    """compare(baseline=この genome, variant=最速) の結果を「最速はこの genome より…」で。"""
    if c.verdict == "faster":
        return f"最速が **+{c.rel_median * 100:.1f}%** 速い (有意, p={c.p:.3f})"
    if c.verdict == "slower":   # 起こらない想定 (最速が baseline より遅い) だが念のため
        return f"最速が {c.rel_median * 100:.1f}% 遅い (有意, p={c.p:.3f})"
    if c.verdict == "no-difference":
        return f"差 {c.rel_median * 100:+.1f}% は信用できる差でない (noise内/非有意)"
    return c.reason or c.verdict


def _write_md(path, tag, wl_str, cid, ranked, win, verdicts, prov, png, dat, plt):
    L = [f"# P2-2 材料レポート — silo fitness ({tag})", "",
         "> 自動生成 (orchestrator/campaign/p2_2_report)。計測は trace-disabled build "
         "(規律1)・単一テナント直列 (規律4)。グラフ/.dat/.plt は手で再生成できる。", "",
         f"![{tag} fitness]({png})", "", "## provenance"]
    for k, v in prov.items():
        L.append(f"- **{k}**: {v}")
    L += ["",
          f"## 最速構成: `{win.genome}`  ({win.label})",
          "",
          f"**{win.median:,.0f} tps** (CV {win.cv * 100:.2f}%)。差の判定は noise floor "
          f"{prov['noise_floor_cv']} 以下を「差なし」に丸め、超える差にだけ Mann-Whitney U "
          "(α=0.05) を当てる (§3.6(4))。", "",
          "## fitness ランキング (median 降順)", "",
          "| rank | genome | median tps | CV | 最速との差 |",
          "|---:|---|---:|---:|---|"]
    for i, g in enumerate(ranked, 1):
        if g.variant == win.variant:
            diff = "**(最速)**"
        else:
            diff = _verdict_str(verdicts[g.variant])
        un = " ⚠UNSTABLE" if g.unstable else ""
        L.append(f"| {i} | `{g.label}`{un} | {g.median:,.0f} | "
                 f"{(g.cv or 0) * 100:.2f}% | {diff} |")
    L += ["",
          "## 実験の再現 (最速構成)", "",
          "**ビルド (perf = trace-disabled, 規律1):**", "", "```bash",
          win.configure_cmd, win.build_cmd, "```", "",
          "**計測 (1 rep 相当; 実計測は reps 回反復し median+CV を採る):**", "",
          "```bash", win.run_cmd, "```", "",
          f"グラフは `gnuplot {plt}` で再生成 (データ = `{dat}`、同一 provenance)。", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def write_summary(results: list, path: str) -> None:
    L = ["# P2-2 サマリ — silo 全探索 (workload 別の最速構成)", "",
         "> 自動生成。各 workload campaign の最速 genome を横断比較 "
         "(genome 列挙=no-wait XOR で 8、空間訂正は "
         "insight 2026-06-22_silo-both-no-wait-zero-livelock.md)。", "",
         f"- calibration: records={RECORDS:,} / threads={THREADS} / "
         f"clocks_per_us={CLK} / skew0.9 / noise floor CV {NOISE_CV_SKEW09 * 100:.2f}%",
         "",
         "| workload | 最速 genome | median tps | CV | 2位との差 |",
         "|---|---|---:|---:|---|"]
    for r in results:
        if not r:
            continue
        win = r["winner"]
        ranked = r["ranked"]
        second = next((g for g in ranked if g.variant != win.variant), None)
        gap = "—"
        if second is not None:
            c = r["verdicts"].get(second.variant)
            gap = _verdict_str(c) if c else "—"
        L.append(f"| {r['tag']} | `{win.label}` ({win.genome.split('|',1)[1]}) | "
                 f"{win.median:,.0f} | {win.cv * 100:.2f}% | {gap} |")
    L += ["", "## 各 workload の詳細レポート", ""]
    for r in results:
        if r:
            rel = os.path.relpath(r["report"], os.path.dirname(path))
            L.append(f"- **{r['tag']}**: [{rel}]({rel})")
    L.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main() -> int:
    results = []
    for tag, workload in WORKLOADS:
        results.append(report_workload(tag, workload))
    have = [r for r in results if r]
    if not have:
        print("レポート対象の campaign が無い (p2_2.py を先に実行)。")
        return 1
    summary = os.path.join(repo_output_root(), "campaigns", "p2-2-summary.md")
    write_summary(results, summary)
    print(f"\nサマリ → {summary}")
    for r in have:
        print(f"  {r['tag']}: 最速 {r['winner'].label} "
              f"{r['winner'].median:,.0f} tps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
