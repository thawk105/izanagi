# -*- coding: utf-8 -*-
"""reports 射影器の単体テスト。

純ロジック (.dat/.plt 文字列生成) は機械非依存。gnuplot 実行を伴うテストは gnuplot が
無ければ skip。pytest でも 素の `python orchestrator/tests/test_reports.py` でも走る。
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from reports.plot import (DatFile, PlotSpec, Series,            # noqa: E402
                          make_plot, render_plt)

_HAS_GNUPLOT = shutil.which("gnuplot") is not None


# ===== .dat: 再現コマンド埋め込み (ユーザー要件の核) =====

def test_datfile_embeds_repro_command_and_provenance():
    dat = DatFile(
        title="cal", columns=["records", "miss"], rows=[[1000, 0.2], [2000, 0.3]],
        provenance={"env": "linux-baremetal", "clocks_per_us": "1800"},
        repro_command="numactl --interleave=all perf stat -- ./ycsb_silo -thread_num=48")
    s = dat.render()
    assert "# cal" in s
    assert "# env: linux-baremetal" in s
    assert "# clocks_per_us: 1800" in s
    assert "手打ち再現コマンド" in s
    assert "numactl --interleave=all perf stat" in s   # 生成コマンドが # コメントに埋まる
    assert "# records\tmiss" in s                      # 列ヘッダも # コメント
    assert "1000\t0.2" in s                            # データ行は素のまま (gnuplot が読む)


def test_datfile_repro_command_lines_are_all_commented():
    """複数行コマンドの全行が # で始まる (gnuplot がデータと誤読しない)。"""
    dat = DatFile(title="t", columns=["a"], rows=[[1]],
                  repro_command="line1 \\\nline2 \\\nline3")
    for line in dat.render().splitlines():
        # データ行は "1" のみ。コマンド行は全て # 始まり。
        if "line" in line:
            assert line.lstrip().startswith("#")


def test_datfile_float_format_6g():
    dat = DatFile(title="t", columns=["a"], rows=[[0.123456789]])
    assert "0.123457" in dat.render()                  # %.6g


# ===== .plt: gnuplot スクリプト生成 =====

def test_render_plt_series_axes_logscale_noenhanced():
    spec = PlotSpec(title="cal", xlabel="records", ylabel="miss", y2label="rss",
                    logscale_x=2, series=[Series("1:2", "miss", "x1y1"),
                                          Series("1:3", "rss", "x1y2")])
    plt = render_plt("d.dat", "d.png", spec)
    assert 'set output "d.png"' in plt
    assert "set logscale x 2" in plt
    assert "set y2tics" in plt
    assert "using 1:2 with linespoints axes x1y1" in plt
    assert "using 1:3 with linespoints axes x1y2" in plt
    assert "noenhanced" in plt                         # ラベルの _ をリテラル表示


def test_render_plt_no_y2_when_absent():
    spec = PlotSpec(title="t", xlabel="x", ylabel="y", series=[Series("1:2", "s")])
    assert "y2tics" not in render_plt("d.dat", "d.png", spec)


# ===== gnuplot 実行 (実機、無ければ skip) =====

def test_make_plot_generates_valid_png():
    if not _HAS_GNUPLOT:
        print("(gnuplot 無し → skip)")
        return
    tmp = tempfile.mkdtemp(prefix="izanagi_plot_")
    try:
        dat = DatFile(title="t", columns=["x", "y"], rows=[[1, 1], [2, 4], [3, 9]])
        spec = PlotSpec(title="t", xlabel="x", ylabel="y", series=[Series("1:2", "y")])
        paths = make_plot(dat, spec, os.path.join(tmp, "g"))
        assert os.path.exists(paths["png"]) and os.path.getsize(paths["png"]) > 100
        with open(paths["png"], "rb") as f:
            assert f.read(8) == b"\x89PNG\r\n\x1a\n"    # PNG マジックバイト
        # .dat と .plt も残る (手で再生成できる)
        assert os.path.exists(paths["dat"]) and os.path.exists(paths["plt"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- 素の runner ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
