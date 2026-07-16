# -*- coding: utf-8 -*-
"""plot_backoff._ci95 の 95% CI が t 分布規約 (FIGURE_CONVENTIONS.md §2) に従う回帰。

正本規約: 点推定 = 標本平均、CI 半幅 = 小 n では t_{0.975,n-1}·s/√n、n>=30 で
1.96·s/√n の正規近似。既知入力の期待値で t 分布使用 (1.96 固定でないこと) を固定する。
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, _HERE)

from skiputil import Skip, skip                                  # noqa: E402


def _load_plot_module(need_numpy=True):
    path = os.path.join(_REPO, "tools", "plotting", "plot_backoff.py")
    spec = importlib.util.spec_from_file_location("plot_backoff_ci_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)   # module top-level は numpy 非依存 (遅延 import)。
    if need_numpy:
        # _ci95 は np のみ使う。matplotlib (作図専用) を要求せず np だけ注入する。
        try:
            import numpy as _np
        except ImportError as exc:
            skip(f"numpy 不在で _ci95 を検証できない: {exc}")
        module.np = _np
    return module


def test_t975_table_matches_known_critical_values():
    """内蔵 t 表が代表的自由度の t_{0.975,df} と一致し、n>=30 は 1.96 に落ちる。"""
    plot = _load_plot_module(need_numpy=False)   # 純粋な表引き、numpy 不要。
    assert plot._t975(1) == 12.706          # n=2
    assert plot._t975(4) == 2.776           # n=5 (実 campaign)
    assert plot._t975(28) == 2.048          # n=29 (t 表の下端)
    assert plot._t975(29) == 1.96           # n=30: 正規近似に切替
    assert plot._t975(100) == 1.96          # 大 n も 1.96


def test_ci95_small_n_uses_t_distribution():
    """n=5, reps=[1..5] → mean=3.0, 半幅 = t4·s/√n = 2.776·sqrt(0.5)。

    std(ddof=1) = sqrt(2.5), s/√n = sqrt(2.5)/sqrt(5) = sqrt(0.5)。旧実装 (1.96 固定)
    なら半幅 = 1.96·sqrt(0.5) ≈ 1.386 で、t4 期待値 ≈ 1.963 とは一致しない。
    """
    plot = _load_plot_module()
    center, half = plot._ci95([1.0, 2.0, 3.0, 4.0, 5.0])
    expected_half = 2.776 * math.sqrt(0.5)   # ≈ 1.96293
    assert abs(center - 3.0) < 1e-9, center
    assert abs(half - expected_half) < 1e-9, (half, expected_half)
    # 1.96 固定の旧挙動と明確に乖離していること (退行検知)。
    assert abs(half - 1.96 * math.sqrt(0.5)) > 0.5


def test_ci95_center_is_mean_not_median():
    """CI 半幅は平均 SE ベースなので中心も標本平均 (median との差で確認)。"""
    plot = _load_plot_module()
    # 歪んだ標本: median=2.0 だが mean=4.0。
    center, _ = plot._ci95([1.0, 2.0, 9.0])
    assert abs(center - 4.0) < 1e-9, center


def test_ci95_single_sample_ci_incalculable():
    """n<2 は分散を推定できず CI 計算不能 → 半幅は None (幅ゼロの誤差棒を描かない)。

    旧契約は半幅 0.0 を返し、図に幅ゼロの誤差棒が「95% CI」として描かれていた
    (分散未知なのに不確かさゼロと誤読させる)。None を返して描画側が誤差棒を抑止する。
    """
    plot = _load_plot_module()
    center, half = plot._ci95([123456.0])
    assert center == 123456.0
    assert half is None


def test_ci95_half_M_suppresses_errorbar_when_incalculable():
    """描画ヘルパ: n<2 は NaN (errorbar が誤差棒を描かない)、n>=2 は半幅/1e6。"""
    plot = _load_plot_module()
    assert math.isnan(plot._ci95_half_M([123456.0]))     # n=1 → 誤差棒抑止
    half_M = plot._ci95_half_M([1.0e6, 2.0e6, 3.0e6, 4.0e6, 5.0e6])
    expected_half_M = 2.776 * math.sqrt(0.5)             # n=5, 単位 1e6 tps
    assert not math.isnan(half_M)
    assert abs(half_M - expected_half_M) < 1e-9, (half_M, expected_half_M)


def test_ci95_large_n_uses_normal_approx():
    """n>=30 は 1.96·s/√n の正規近似 (t 表を引かない)。"""
    plot = _load_plot_module()
    reps = [float(i) for i in range(1, 31)]   # n=30
    np = plot.np
    a = np.asarray(reps, dtype=float)
    expected_half = 1.96 * a.std(ddof=1) / math.sqrt(30)
    _, half = plot._ci95(reps)
    assert abs(half - expected_half) < 1e-9, (half, expected_half)


# ---- 素の runner (pytest 無しでも) ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
