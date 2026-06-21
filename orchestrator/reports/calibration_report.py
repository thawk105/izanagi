# -*- coding: utf-8 -*-
"""calibration json → 材料レポート (.dat/.plt/.png + report.md)。

env スコープの calibration (records 掃引の miss 率 / maxrss) を gnuplot グラフ + 人間可読 md に
射影する最初の reports 射影器。.dat には手打ち再現コマンドを埋める (plot.DatFile)。
"""
from __future__ import annotations

import json
import os
from typing import Dict

from .plot import DatFile, PlotSpec, Series, make_plot

# runner.PERF_EVENTS と一致させる (再現コマンドが実際の計測と同じ events を指すように)。
PERF_EVENTS = "LLC-load-misses,LLC-loads,instructions,cycles"


def _repro_command(threads, clk, workload: Dict[str, str],
                   binary: str = "<build>/ycsb_silo.exe", extime: int = 3) -> str:
    wl = " ".join(f"-{k}={v}" for k, v in sorted(workload.items()))
    return (f"numactl --interleave=all perf stat -e {PERF_EVENTS} -- \\\n"
            f"  {binary} -thread_num={threads} -ycsb_tuple_num=<records> \\\n"
            f"  {wl} -extime={extime} -clocks_per_us={clk}")


def _build_command(ccbench_commit: str = "", cc: str = "g++-13") -> str:
    """calibration バイナリを作るビルドコマンド (silo 標準 Release、最適化フラグ default)。

    注: calibration は genome 非依存の baseline silo を使うので最適化 -D は付かない。
    探索 variant のビルドコマンドは buildcache が genome ごとに正確に記録する (WAL)。"""
    head = "# silo 標準 Release build (calibration は最適化フラグ default)"
    if ccbench_commit:
        head += f"; ccbench={ccbench_commit}"
    return (f"{head}\n"
            f"cmake -S external/ccbench -B build -DCMAKE_BUILD_TYPE=Release \\\n"
            f"  -DENABLE_SANITIZER=OFF -DCMAKE_CXX_COMPILER={cc}\n"
            f"cmake --build build --target ycsb_silo.exe -j")


def calibration_report(cal_json_path: str, out_dir: str,
                       ccbench_commit: str = "", extime: int = 3) -> Dict[str, str]:
    """calibration json を読み .dat/.plt/.png + report.md を out_dir に生成しパスを返す。"""
    with open(cal_json_path, encoding="utf-8") as f:
        cal = json.load(f)

    env = cal.get("env_tag", "?")
    threads = cal.get("threads", "?")
    clk = cal.get("clocks_per_us", "?")
    workload = cal.get("workload", {})
    host = cal.get("host", {})
    sat = cal.get("saturation", {})
    series = sat.get("series", [])
    nf = cal.get("noise_floor", {})

    prov = {
        "env": env,
        "host": f"{host.get('node','?')} / {host.get('machine','?')} / "
                f"{host.get('cpu_count','?')}cpu / L3={host.get('l3_total_bytes','?')}B",
        "ccbench-commit": ccbench_commit or "(calibration json に未記録)",
        "clocks_per_us": str(clk),
        "workload": ", ".join(f"{k}={v}" for k, v in sorted(workload.items())),
        "calibration": (f"lower-bound N={sat.get('records')} "
                        f"(working_set/L3={sat.get('working_set_ratio', 0):.1f}x)"
                        if sat.get("lower_bound_selected")
                        else f"saturated N={sat.get('records')}"),
    }
    repro = _repro_command(threads, clk, workload, extime=extime)
    build_cmd = _build_command(ccbench_commit)

    rows = [[int(s["records"]), s["miss_rate"], int(s.get("maxrss_kb", 0))]
            for s in series]
    dat = DatFile(
        title=f"calibration sweep: {env} t{threads} ({prov['workload']})",
        columns=["records", "miss_rate", "maxrss_kb"],
        rows=rows, provenance=prov, build_command=build_cmd, repro_command=repro)

    spec = PlotSpec(
        title=f"Calibration sweep ({env}, {threads} threads)",
        xlabel="records (ycsb_tuple_num, log2)",
        ylabel="LLC miss rate", y2label="maxrss (kB)", logscale_x=2,
        series=[Series("1:2", "miss rate", "x1y1"),
                Series("1:3", "maxrss (kB)", "x1y2")])

    # 出力名は入力 json 名ベース (workload 署名を含む → skew 違いで上書きしない)。
    base = os.path.splitext(os.path.basename(cal_json_path))[0]
    stem = os.path.join(out_dir, base + "_sweep")
    paths = make_plot(dat, spec, stem)

    md = _render_md(env, threads, prov, build_cmd, repro, rows, nf,
                    os.path.basename(paths["png"]), os.path.basename(paths["dat"]),
                    os.path.basename(paths["plt"]))
    md_path = os.path.join(out_dir, base + "_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    paths["md"] = md_path
    return paths


def _render_md(env, threads, prov, build_cmd, repro, rows, nf, png, dat, plt) -> str:
    L = [f"# Calibration 材料レポート — {env} / {threads} threads", "",
         "> 自動生成 (orchestrator/reports)。グラフ・`.dat`・`.plt` は全て手で再生成できる "
         "(.dat ヘッダに手打ち再現コマンドを埋めてある)。", "",
         f"![calibration sweep]({png})", "", "## provenance"]
    for k, v in prov.items():
        L.append(f"- **{k}**: {v}")
    L += ["", "## 数値", "", "| records | miss_rate | maxrss_kb |", "|---:|---:|---:|"]
    for r in rows:
        L.append(f"| {r[0]:,} | {r[1] * 100:.2f}% | {r[2]:,} |")
    L.append("")
    if nf:
        L.append(f"- **noise floor**: median {nf.get('median', 0):,.0f} tps / "
                 f"CV {nf.get('cv', 0) * 100:.2f}% / N={len(nf.get('throughputs', []))}")
        L.append("")
    L += ["## 実験の再現 (ビルド → 実行)", "",
          "**1. バイナリをビルド:**", "", "```bash", build_cmd, "```", "",
          "**2. 各 records 点を実行** (`<records>` / `<build>` を置換):", "",
          "```bash", repro, "```", "",
          f"グラフは `gnuplot {plt}` で再生成 (データ = `{dat}`、同一 provenance)。", ""]
    return "\n".join(L)
