# -*- coding: utf-8 -*-
"""calibrator 純ロジックの単体テスト (machine 非依存・モックデータ)。

pytest でも素の `python orchestrator/tests/test_calibrator.py` でも走る
(末尾に pytest 非依存 runner)。モック文字列は実 perf/ccbench 出力に合わせてある
(perf CSV: `value,,event,...` / ccbench: `label:\\tvalue`)。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from calibrator.analyze import (find_saturation, noise_floor,        # noqa: E402
                                scale_sensitivity)
from calibrator.benchparse import (actual_extime, parse_bench_stdout,  # noqa: E402
                                    throughput_tps)
from calibrator.model import PerfCounters, ScalePoint                # noqa: E402
from calibrator.perfparse import parse_perf_stat                     # noqa: E402


def _pt(records, miss_rate, threads=8, tps=None):
    """miss_rate (0..1) を持つ ScalePoint をモック。loads=1e6 固定で逆算。"""
    loads = 1_000_000
    c = PerfCounters(llc_load_misses=int(round(miss_rate * loads)),
                     llc_loads=loads)
    p = ScalePoint(records=records, threads=threads, counters=c)
    if tps is not None:
        p.throughputs = [tps]
    return p


# ===== perfparse (実 perf CSV / 人間可読 / 欠損) =====

def test_perfparse_csv():
    # 実 `perf stat -x,` の形 (value,,event,run-time,pct,metric,metric-unit)
    text = (
        "655445,,LLC-load-misses,14214727114,100.00,4.14,of all LL-cache accesses\n"
        "15824577,,LLC-loads,14214727114,100.00,,\n"
        "21552364949,,instructions,14214727114,100.00,0.59,insn per cycle\n"
        "36757636619,,cycles,14214727114,100.00,,\n"
    )
    c = parse_perf_stat(text)
    assert c.llc_load_misses == 655445
    assert c.llc_loads == 15824577
    assert c.instructions == 21552364949
    assert c.cycles == 36757636619
    # 4.14% に一致 (perf の報告値)
    assert abs(c.llc_miss_rate - 0.0414) < 0.001


def test_perfparse_human_readable():
    text = (
        "       123,456,789      LLC-load-misses\n"
        "     1,000,000,000      LLC-loads\n"
        "       5.123456789 seconds time elapsed\n"
    )
    c = parse_perf_stat(text)
    assert c.llc_load_misses == 123456789
    assert c.llc_loads == 1_000_000_000
    assert abs(c.llc_miss_rate - 0.123456789) < 1e-9


def test_perfparse_missing_counter():
    # カウンタが取れないと perf は <not counted> を出す → 欠損 (None)
    text = (
        "<not counted>,,LLC-load-misses,0,0.00,,\n"
        "<not counted>,,LLC-loads,0,0.00,,\n"
    )
    c = parse_perf_stat(text)
    assert c.llc_load_misses is None
    assert c.llc_loads is None
    assert c.llc_miss_rate is None


def test_perfparse_zero_loads_no_div0():
    c = PerfCounters(llc_load_misses=5, llc_loads=0)
    assert c.llc_miss_rate is None


# ===== benchparse (実 ccbench stdout) =====

_BENCH = (
    "#FLAGS_clocks_per_us:\t2600\n"
    "#FLAGS_extime:\t\t1\n"
    "#FLAGS_thread_num:\t4\n"
    "#ShowOptParameters(): ADD_ANALYSIS 0: WAL 0\n"
    "actual_extime:\t1\n"
    "abort_counts_:\t253\n"
    "commit_counts_:\t791069\n"
    "maxrss:\t216208 kB\n"
    "batch_abort_rate:\t-nan\n"
    "latency[ns]:\t5056.4489\n"
    "throughput[tps]:\t791069\n"
)


def test_benchparse_metrics():
    m = parse_bench_stdout(_BENCH)
    assert m["throughput[tps]"] == "791069"
    assert m["commit_counts_"] == "791069"
    assert m["maxrss"] == "216208 kB"        # 単位は文字列のまま保持
    # 二重タブの #FLAGS_extime も value だけ取れる
    assert m["#FLAGS_extime"] == "1"


def test_benchparse_throughput_and_extime():
    m = parse_bench_stdout(_BENCH)
    assert throughput_tps(m) == 791069.0
    assert actual_extime(m) == 1.0


def test_benchparse_throughput_fallback():
    # throughput[tps] が無くても commit_counts_/actual_extime で代替
    m = parse_bench_stdout("commit_counts_:\t1000\nactual_extime:\t2.0\n")
    assert throughput_tps(m) == 500.0


def test_benchparse_nan_is_none():
    m = parse_bench_stdout("batch_abort_rate:\t-nan\n")
    from calibrator.benchparse import _num
    assert _num(m["batch_abort_rate"]) is None


# ===== find_saturation: 早い飽和 =====

def test_saturation_fast():
    # miss 率が rise→2m で平らに。閾値 1pp。
    pts = [_pt(1_000_000, 0.002), _pt(2_000_000, 0.015),
           _pt(4_000_000, 0.018), _pt(8_000_000, 0.0185),
           _pt(16_000_000, 0.0186)]
    r = find_saturation(pts)              # 既定 Δ=0.01
    assert r.saturated
    assert r.records == 2_000_000
    assert not r.cache_floor_warning      # 1.5% は floor 0.5% 超


# ===== find_saturation: 飽和しない (遅い) =====

def test_saturation_never():
    # 毎ステップ >1pp 上昇し続ける → 範囲内で飽和せず、最大点を暫定採用
    pts = [_pt(1_000_000, 0.005), _pt(2_000_000, 0.016),
           _pt(4_000_000, 0.028), _pt(8_000_000, 0.040),
           _pt(16_000_000, 0.053)]
    r = find_saturation(pts)
    assert not r.saturated
    assert r.records == 16_000_000        # 最大点 (安全側)
    assert any("延ばす" in n for n in r.notes)


# ===== find_saturation: 非単調 (途中の noise dip に騙されない) =====

def test_saturation_non_monotonic():
    # 2m-8m で一旦平ら (noise の谷) → だが 8m→16m で再上昇 → 真の飽和は 16m。
    # 素朴な「最初に平らなステップ」だと 2m を誤採用する。tail-flat 要求で回避。
    pts = [_pt(1_000_000, 0.010), _pt(2_000_000, 0.020),
           _pt(4_000_000, 0.021), _pt(8_000_000, 0.0195),
           _pt(16_000_000, 0.035), _pt(32_000_000, 0.0355)]
    r = find_saturation(pts)
    assert r.saturated
    assert r.records != 2_000_000         # 早すぎる plateau を採らない
    assert r.records == 16_000_000        # 後段の真の飽和点


# ===== find_saturation: 下限割れ (cache に乗る) =====

def test_saturation_cache_floor_warning():
    # 低 miss 率で平ら → 採用はするが working set が cache に乗る警告
    pts = [_pt(1_000_000, 0.001), _pt(2_000_000, 0.0015),
           _pt(4_000_000, 0.0016), _pt(8_000_000, 0.0016)]
    r = find_saturation(pts)
    assert r.saturated
    assert r.records == 1_000_000
    assert r.cache_floor_warning


# ===== find_saturation: 退化ケース =====

def test_saturation_single_point():
    r = find_saturation([_pt(4_000_000, 0.02)])
    assert not r.saturated
    assert r.records == 4_000_000
    assert any("2 点" in n for n in r.notes)


def test_saturation_drops_missing_miss_rate():
    pts = [_pt(1_000_000, 0.015), _pt(2_000_000, 0.018)]
    bad = ScalePoint(records=4_000_000, threads=8,
                     counters=PerfCounters(llc_load_misses=5, llc_loads=None))
    r = find_saturation(pts + [bad])
    assert any("欠損" in n for n in r.notes)


# ===== scale_sensitivity =====

def test_scale_linear_not_suspect():
    small = _pt(1_000_000, 0.02, threads=4, tps=4_000_000)
    medium = _pt(10_000_000, 0.02, threads=10, tps=10_000_000)
    s = scale_sensitivity(small, medium)
    assert abs(s.efficiency_ratio - 1.0) < 1e-9
    assert not s.scale_suspect


def test_scale_sublinear_suspect():
    small = _pt(1_000_000, 0.02, threads=4, tps=4_000_000)    # per-thread 1.0M
    medium = _pt(10_000_000, 0.02, threads=10, tps=5_000_000)  # per-thread 0.5M
    s = scale_sensitivity(small, medium)
    assert abs(s.efficiency_ratio - 0.5) < 1e-9
    assert s.scale_suspect


# ===== noise_floor =====

def test_noise_floor_low_cv():
    n = noise_floor([100_000, 101_000, 99_000, 100_500, 99_500])
    assert n.cv is not None and n.cv < 0.05
    assert not n.high_variance


def test_noise_floor_high_cv():
    n = noise_floor([100_000, 130_000, 80_000, 120_000])
    assert n.cv is not None and n.cv > 0.05
    assert n.high_variance


def test_noise_floor_single_sample():
    n = noise_floor([100_000])
    assert n.cv is None
    assert any("1 点" in note for note in n.notes)


# ---- 素の runner (pytest 無しでも) ----

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
