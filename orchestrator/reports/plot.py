# -*- coding: utf-8 -*-
"""gnuplot ベースのグラフ生成。**再現性が一級市民** (roadmap §3.6(4)/§7 forensic binding)。

各図は3点セットで残す:
  <stem>.dat  データ + ヘッダに provenance と **手打ち再現コマンド** を # コメントで埋める
  <stem>.plt  gnuplot スクリプト (人間が手で `gnuplot x.plt` して再生成できる)
  <stem>.png  描画結果 (材料レポート report.md に埋め込む、人間可読)

.dat 単体で「どの実行コマンドからこの数値が出たか」を辿れる → 後で手打ち実行でも近似結果を
再現できる (ユーザー要件)。これは throughput 等の生値を WAL に残すのと同じ anti-fabrication
の思想 (claim→code→evidence の proof chain)。
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Sequence


def _fmt(x) -> str:
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, float):
        return f"{x:.6g}"
    return str(x)


@dataclass
class DatFile:
    """gnuplot 用データファイル。ヘッダに provenance + 手打ち再現コマンドを埋める。"""
    title: str
    columns: List[str]                                  # 列名 (順序 = rows の並び)
    rows: List[Sequence]                                # データ行
    provenance: Dict[str, str] = field(default_factory=dict)   # env/commit/clk 等
    repro_command: str = ""                             # 手打ちで近似再現するコマンド

    def render(self) -> str:
        out = [f"# {self.title}"]
        for k, v in self.provenance.items():
            out.append(f"# {k}: {v}")
        if self.repro_command:
            out.append("#")
            out.append("# 手打ち再現コマンド (この .dat の各点を生成する; <...> は置換):")
            for line in self.repro_command.splitlines():
                out.append(f"#   {line}")
        out.append("#")
        out.append("# " + "\t".join(self.columns))      # 列ヘッダ (gnuplot は # を無視)
        for row in self.rows:
            out.append("\t".join(_fmt(x) for x in row))
        return "\n".join(out) + "\n"


@dataclass
class Series:
    using: str                  # gnuplot using 指定 (例 "1:2")
    title: str
    axis: str = "x1y1"          # 第2軸に載せるなら "x1y2"
    style: str = "linespoints"


@dataclass
class PlotSpec:
    title: str
    xlabel: str
    ylabel: str
    series: List[Series]
    y2label: str = ""
    logscale_x: int = 0         # 0=線形、2 なら `set logscale x 2`
    size: str = "900,540"


def render_plt(dat_name: str, png_name: str, spec: PlotSpec) -> str:
    """gnuplot スクリプト文字列を生成 (dat_name/png_name は .plt と同じ dir の相対名)。"""
    lines = [
        # noenhanced: ラベル中の _ を下付き文字でなくリテラルで出す (ycsb_tuple_num 等)。
        f'set terminal pngcairo size {spec.size} noenhanced font "sans,11"',
        f'set output "{png_name}"',
        f'set title "{_q(spec.title)}"',
        f'set xlabel "{_q(spec.xlabel)}"',
        f'set ylabel "{_q(spec.ylabel)}"',
        'set grid',
        'set key outside right top',
    ]
    if spec.logscale_x:
        lines.append(f'set logscale x {spec.logscale_x}')
    if spec.y2label:
        lines += [f'set y2label "{_q(spec.y2label)}"', 'set y2tics', 'set ytics nomirror']
    parts = [f'"{dat_name}" using {s.using} with {s.style} axes {s.axis} '
             f'title "{_q(s.title)}"' for s in spec.series]
    lines.append("plot " + ", \\\n     ".join(parts))
    return "\n".join(lines) + "\n"


def _q(s: str) -> str:
    return s.replace('"', '\\"')


def make_plot(dat: DatFile, spec: PlotSpec, stem: str) -> Dict[str, str]:
    """<stem>.{dat,plt,png} を書き出し gnuplot で描画。生成パスの辞書を返す。

    gnuplot は .plt のあるディレクトリで実行する (相対名参照のため、出力 png も同 dir)。"""
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    dat_path, plt_path, png_path = stem + ".dat", stem + ".plt", stem + ".png"
    with open(dat_path, "w", encoding="utf-8") as f:
        f.write(dat.render())
    plt_text = render_plt(os.path.basename(dat_path), os.path.basename(png_path), spec)
    with open(plt_path, "w", encoding="utf-8") as f:
        f.write(plt_text)
    work = os.path.dirname(stem) or "."
    r = subprocess.run(["gnuplot", os.path.basename(plt_path)], cwd=work,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gnuplot failed (rc={r.returncode}): {r.stderr[-500:]}")
    return {"dat": dat_path, "plt": plt_path, "png": png_path}
