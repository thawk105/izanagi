# -*- coding: utf-8 -*-
"""calibrator 純ロジックの単体テスト (machine 非依存・モックデータ)。

pytest でも素の `python orchestrator/tests/test_calibrator.py` でも走る
(末尾に pytest 非依存 runner)。モック文字列は実 perf/ccbench 出力に合わせてある
(perf CSV: `value,,event,...` / ccbench: `label:\\tvalue`)。
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from skiputil import Skip, skip                                                   # noqa: E402
from orchestrator.calibrator.analyze import (find_saturation, noise_floor,        # noqa: E402
                                scale_sensitivity)
from orchestrator.calibrator.benchparse import (actual_extime, parse_bench_stdout,  # noqa: E402
                                    throughput_tps)
from orchestrator.calibrator.model import PerfCounters, ScalePoint                # noqa: E402
from orchestrator.calibrator.perfparse import parse_perf_stat                     # noqa: E402


def _pt(records, miss_rate, threads=8, tps=None, maxrss_mb=None):
    """miss_rate (0..1) を持つ ScalePoint をモック。loads=1e6 固定で逆算。"""
    loads = 1_000_000
    c = PerfCounters(llc_load_misses=int(round(miss_rate * loads)),
                     llc_loads=loads)
    p = ScalePoint(records=records, threads=threads, counters=c)
    if tps is not None:
        p.throughputs = [tps]
    if maxrss_mb is not None:
        p.maxrss_kb = int(maxrss_mb * 1024)
    return p


_L3 = 90 * 1024 * 1024   # 本ホストの L3 総量 (90MB) を模した値


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
    from orchestrator.calibrator.benchparse import _num
    assert _num(m["batch_abort_rate"]) is None


# ===== leading indicators (P2-3, §3.5) =====

def test_benchparse_abort_rate_and_latency():
    from orchestrator.calibrator.benchparse import abort_rate, latency_ns
    # abort_rate ラベルがあればそれを優先 (生カウントより)
    m = parse_bench_stdout("abort_rate:\t0.0260\nabort_counts_:\t999\ncommit_counts_:\t1\n")
    assert abort_rate(m) == 0.0260
    # _BENCH は abort_rate ラベル無し → 生カウントから再計算 (fallback)
    m2 = parse_bench_stdout(_BENCH)
    assert abs(abort_rate(m2) - 253 / (253 + 791069)) < 1e-12
    assert latency_ns(m2) == 5056.4489


def test_benchparse_abort_rate_nan_falls_back_to_counts():
    from orchestrator.calibrator.benchparse import abort_rate
    m = parse_bench_stdout("abort_rate:\t-nan\nabort_counts_:\t10\ncommit_counts_:\t90\n")
    assert abort_rate(m) == 0.1                    # -nan ラベルは無効 → 10/(10+90)


def test_perfcounters_ipc():
    assert PerfCounters(instructions=300, cycles=200).ipc == 1.5
    assert PerfCounters(instructions=300, cycles=0).ipc is None     # 0 除算回避
    assert PerfCounters(instructions=None, cycles=200).ipc is None


def test_scalepoint_leading_indicators():
    pt = ScalePoint(records=1000, threads=4,
                    counters=PerfCounters(llc_load_misses=20, llc_loads=100,
                                          instructions=300, cycles=200),
                    throughputs=[1000.0, 1000.0, 1000.0],
                    abort_rate=0.05, latency_ns=1234.0)
    li = pt.leading_indicators()
    assert li == {"throughput_tps": 1000.0, "abort_rate": 0.05,
                  "latency_ns": 1234.0, "llc_miss_rate": 0.2, "ipc": 1.5}


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
    assert not r.lower_bound_selected
    assert not any("候補から選択" in n for n in r.notes)


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


# ===== find_saturation: 膝なし → 下限基準 (D15) =====

def test_lower_bound_when_no_plateau():
    # miss 率が単調上昇で飽和せず + maxrss + L3 → working set≥L3×4 の最小 N を採用。
    # L3=90MB, K=4 → need 360MB。maxrss: 1m=300MB(<360), 2m=520MB(≥360) → 2m。
    pts = [_pt(1_000_000, 0.198, maxrss_mb=300), _pt(2_000_000, 0.231, maxrss_mb=520),
           _pt(4_000_000, 0.287, maxrss_mb=960), _pt(8_000_000, 0.331, maxrss_mb=1840)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert not r.saturated
    assert r.lower_bound_selected
    assert r.records == 2_000_000
    assert r.working_set_ratio is not None and r.working_set_ratio > 4.0
    assert not r.cache_floor_warning
    assert not any("候補から選択" in n for n in r.notes)


def test_lower_bound_unavailable_without_l3_or_maxrss():
    # 膝なしだが L3/maxrss が無い → 従来通り最大点を暫定返し (下限基準は不発)
    pts = [_pt(1_000_000, 0.198), _pt(2_000_000, 0.231),
           _pt(4_000_000, 0.287), _pt(8_000_000, 0.331)]
    r = find_saturation(pts, l3_bytes=None)
    assert not r.saturated
    assert not r.lower_bound_selected
    assert r.records == 8_000_000        # 最大点 (暫定)
    assert any("適用不能" in n for n in r.notes)


def test_lower_bound_even_max_too_small():
    # 全点で working set が L3×4 に届かない → 最大点 + もっと大きくせよの note
    pts = [_pt(1_000_000, 0.05, maxrss_mb=120), _pt(2_000_000, 0.08, maxrss_mb=180),
           _pt(4_000_000, 0.11, maxrss_mb=300)]   # 300MB < 360MB(=L3×4)
    r = find_saturation(pts, l3_bytes=_L3)
    assert not r.saturated
    assert not r.lower_bound_selected
    assert r.records == 4_000_000
    assert any("上げる必要" in n for n in r.notes)


def test_plateau_preferred_over_lower_bound():
    # 飽和点があれば下限基準より優先 (第一基準)。早期に平らなら膝を採る。
    pts = [_pt(1_000_000, 0.002, maxrss_mb=300), _pt(2_000_000, 0.015, maxrss_mb=520),
           _pt(4_000_000, 0.018, maxrss_mb=960), _pt(8_000_000, 0.0185, maxrss_mb=1840)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert r.saturated
    assert not r.lower_bound_selected
    assert r.records == 2_000_000
    assert not r.cache_floor_warning
    assert not any("候補から選択" in n for n in r.notes)


# ===== find_saturation: 下限割れ (cache に乗る) =====

def test_saturation_cache_floor_warning():
    # 低 miss 率で平ら → 採用はするが working set が cache に乗る警告
    pts = [_pt(1_000_000, 0.001), _pt(2_000_000, 0.0015),
           _pt(4_000_000, 0.0016), _pt(8_000_000, 0.0016)]
    r = find_saturation(pts)
    assert r.saturated
    assert r.records == 1_000_000
    assert r.cache_floor_warning
    assert not r.lower_bound_selected
    assert not any("候補から選択" in n for n in r.notes)


def test_lower_bound_cache_floor_rr5():
    pts = [_pt(1_000_000, .00364, maxrss_mb=517),
           _pt(2_000_000, .01392, maxrss_mb=1023),
           _pt(4_000_000, .04762, maxrss_mb=1958)]
    r = find_saturation(pts, l3_bytes=110_100_480)
    assert r.records == 2_000_000
    assert not r.saturated and r.lower_bound_selected
    assert not r.cache_floor_warning
    assert r.miss_rate_at == .01392
    assert r.working_set_ratio == 1023 * 1024 * 1024 / 110_100_480
    note = ("cache_floor 下限 0.50% を満たす最小 N を同じ下限基準候補から選択: "
            "N=1,000,000 (LLC miss 0.364%) → N=2,000,000 (LLC miss 1.392%)。")
    assert note in r.notes
    assert any("かつ LLC miss 率 ≥ 0.50%" in n for n in r.notes)
    from orchestrator.calibrator.model import CalibrationResult
    from orchestrator.calibrator.report import render_text, result_to_dict
    result = CalibrationResult(env_tag="test", threads=8, saturation=r)
    assert note in result_to_dict(result)["saturation"]["notes"]
    assert note in render_text(result)


def test_saturation_cache_floor_minimum_records():
    pts = [_pt(4_000_000, .005), _pt(8_000_000, .006),
           _pt(1_000_000, .001), _pt(2_000_000, .006)]
    r = find_saturation(pts)
    assert r.records == 2_000_000
    assert r.saturated and not r.lower_bound_selected
    assert not r.cache_floor_warning and r.miss_rate_at == .006
    note = ("cache_floor 下限 0.50% を満たす最小 N を同じ飽和候補から選択: "
            "N=1,000,000 (LLC miss 0.100%) → N=2,000,000 (LLC miss 0.600%)。")
    assert note in r.notes
    from orchestrator.calibrator.model import CalibrationResult
    from orchestrator.calibrator.report import render_text, result_to_dict
    result = CalibrationResult(env_tag="test", threads=8, saturation=r)
    assert note in result_to_dict(result)["saturation"]["notes"]
    assert note in render_text(result)


def test_lower_bound_cache_floor_no_match():
    pts = [_pt(1_000_000, .001, maxrss_mb=400),
           _pt(2_000_000, .002, maxrss_mb=500),
           _pt(4_000_000, .003, maxrss_mb=600)]
    r = find_saturation(pts, threshold=.0005, l3_bytes=_L3)
    assert r.records == 1_000_000
    assert not r.saturated and r.lower_bound_selected
    assert r.cache_floor_warning and r.miss_rate_at == .001
    assert not any("候補から選択" in n for n in r.notes)
    assert any("保持 (miss 率下限を満たす候補なし)" in n for n in r.notes)


def test_saturation_cache_floor_final_point_excluded():
    pts = [_pt(1_000_000, .001, maxrss_mb=400),
           _pt(2_000_000, .002, maxrss_mb=500),
           _pt(4_000_000, .006, maxrss_mb=600)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert r.records == 1_000_000
    assert r.saturated and not r.lower_bound_selected
    assert r.cache_floor_warning
    assert not any("候補から選択" in n for n in r.notes)


def test_lower_bound_cache_floor_final_point_included():
    pts = [_pt(1_000_000, .001, maxrss_mb=400),
           _pt(2_000_000, .002, maxrss_mb=500),
           _pt(4_000_000, .020, maxrss_mb=600)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert r.records == 4_000_000
    assert not r.saturated and r.lower_bound_selected
    assert not r.cache_floor_warning


def test_lower_bound_cache_floor_and_rss_same_point():
    pts = [_pt(1_000_000, .020, maxrss_mb=300),
           _pt(2_000_000, .001, maxrss_mb=400),
           _pt(4_000_000, .030, maxrss_mb=500)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert r.records == 4_000_000
    assert not r.saturated and r.lower_bound_selected
    assert not r.cache_floor_warning


def test_saturation_cache_floor_boundary_and_override():
    for floor, rates in ((.005, (.001, .005, .006)),
                         (.020, (.019, .020, .021))):
        pts = [_pt(n, rate) for n, rate in
               zip((1_000_000, 2_000_000, 4_000_000), rates)]
        r = find_saturation(pts, cache_floor=floor)
        assert r.records == 2_000_000
        assert r.saturated and not r.lower_bound_selected
        assert not r.cache_floor_warning and r.miss_rate_at == floor
        assert any(f"cache_floor 下限 {floor*100:.2f}%" in n for n in r.notes)


def test_lower_bound_cache_floor_boundary():
    pts = [_pt(1_000_000, .001, maxrss_mb=400),
           _pt(2_000_000, .005, maxrss_mb=500),
           _pt(4_000_000, .020, maxrss_mb=600)]
    r = find_saturation(pts, l3_bytes=_L3)
    assert r.records == 2_000_000
    assert not r.saturated and r.lower_bound_selected
    assert not r.cache_floor_warning and r.miss_rate_at == .005


def test_saturation_cache_floor_warning_inside_margin():
    # v2-1: .0045 は [floor*.8, floor) の内側。この値は動かさない。
    pts = [_pt(1_000_000, .0045), _pt(2_000_000, .0046),
           _pt(4_000_000, .0047)]
    r = find_saturation(pts)
    assert r.records == 1_000_000
    assert r.saturated and not r.lower_bound_selected
    assert r.miss_rate_at == .0045 and r.cache_floor_warning
    assert not any("候補から選択" in n for n in r.notes)


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


# ===== measure_point: rep 失敗の握り (規律3) =====

def _completed_process(returncode, stdout=_BENCH):
    return type("Completed", (), {
        "returncode": returncode,
        "stdout": stdout,
        "stderr": "injected stderr",
    })()


def test_runner_default_perf_commands_are_unchanged():
    from orchestrator.calibrator import runner

    assert runner._build_cmd("/bench", ["-x=1"], "/tmp/perf.csv", ("numactl",)) == [
        "numactl", "perf", "stat", "-x,", "-o", "/tmp/perf.csv", "-e",
        "LLC-load-misses,LLC-loads,instructions,cycles", "--", "/bench", "-x=1",
    ]
    assert runner.repro_command("/bench", ["-x=1"], ("numactl",)) == (
        "numactl perf stat -e LLC-load-misses,LLC-loads,instructions,cycles "
        "-- /bench -x=1"
    )


def test_run_once_without_perf_executes_binary_and_keeps_counters_missing():
    from orchestrator.calibrator import runner
    seen = []

    def fake_run(argv, **_kwargs):
        seen.append(list(argv))
        return _completed_process(0)

    _metrics, counters, _wall = runner.run_once(
        "/bench", ["-x=1"], numactl=("numactl", "--interleave=all"),
        subprocess_runner=fake_run, use_perf=False,
    )
    assert seen == [["numactl", "--interleave=all", "/bench", "-x=1"]]
    assert counters.llc_load_misses is None
    assert counters.llc_loads is None
    assert counters.instructions is None
    assert counters.cycles is None


def test_measure_point_without_perf_records_matching_direct_repro_command():
    from orchestrator.calibrator import runner
    seen = []

    def fake_run_once(binary, gflags, **kwargs):
        seen.append((binary, list(gflags), dict(kwargs)))
        return ({"throughput[tps]": "1000", "maxrss": "100 kB"},
                PerfCounters(), 0.5)

    original = runner.run_once
    runner.run_once = fake_run_once
    try:
        point = runner.measure_point(
            "/bench", records=1000, threads=4, clocks_per_us=1800,
            reps=1, numactl=("numactl",), use_perf=False,
        )
    finally:
        runner.run_once = original
    assert seen[0][2]["use_perf"] is False
    assert point.run_cmd.startswith("numactl /bench ")
    assert "perf" not in point.run_cmd


def test_run_once_records_rc_and_keeps_three_tuple_when_not_strict():
    """M-P1a: rc 収集を opt-in しても既存 3-tuple 契約は変えない。"""
    from orchestrator.calibrator import runner
    returncodes = []

    result = runner.run_once(
        "dummy", [], strict_returncode=False,
        subprocess_runner=lambda *args, **kwargs: _completed_process(7),
        rep_returncodes=returncodes,
    )

    assert len(result) == 3
    assert returncodes == [7]


def test_run_once_records_rc_before_strict_failure():
    """M-P1b: strict nonzero が例外になっても、発生済み rc は失わない。"""
    from orchestrator.calibrator import runner
    returncodes = []

    try:
        runner.run_once(
            "dummy", [], strict_returncode=True,
            subprocess_runner=lambda *args, **kwargs: _completed_process(9),
            rep_returncodes=returncodes,
        )
    except RuntimeError as exc:
        assert "ccbench failed. rc=9" in str(exc)
    else:
        raise AssertionError("strict nonzero return code が拒否されなかった")
    assert returncodes == [9]


def test_run_once_records_rc_before_metrics_parse_failure():
    """M-P1c: stdout metrics が空でも、完了した subprocess の rc は失わない。"""
    from orchestrator.calibrator import runner
    returncodes = []

    try:
        runner.run_once(
            "dummy", [],
            subprocess_runner=lambda *args, **kwargs: _completed_process(0, stdout=""),
            rep_returncodes=returncodes,
        )
    except RuntimeError as exc:
        assert "produced no metrics" in str(exc)
    else:
        raise AssertionError("空 metrics が拒否されなかった")
    assert returncodes == [0]


def test_measure_point_survives_partial_rep_failure():
    """一部 rep が run_once 例外でも、残り rep で median を取り notes に構造化記録する。

    倍々スイープ末尾で 1 rep がコケても測定点全体を捨てない (reps>=2 の冗長性を活かす)。
    握り潰さず notes に残す (規律3: 沈黙させない)。"""
    from orchestrator.calibrator import runner
    calls = {"n": 0}
    good = ({"throughput[tps]": "1000", "maxrss": "100 kB"},
            PerfCounters(llc_load_misses=10, llc_loads=100), 0.5)

    def fake_run_once(binary, gflags, numactl=None, timeout_s=120.0, extra_env=None):
        calls["n"] += 1
        if calls["n"] == 2:                    # 2 回目 (rep1) だけ失敗
            raise RuntimeError("ccbench produced no metrics (injected)")
        return good

    orig = runner.run_once
    runner.run_once = fake_run_once
    try:
        pt = runner.measure_point("dummy", records=1000, threads=4,
                                  clocks_per_us=1800, reps=3)
    finally:
        runner.run_once = orig
    assert len(pt.throughputs) == 2            # 3 rep 中 1 失敗 → 2 成功で median
    assert pt.throughput == 1000.0
    assert any("rep1 failed" in n for n in pt.notes)
    assert any("1/3 reps failed" in n for n in pt.notes)
    assert pt.rep_observations is None  # P5: opt-in しない既存 caller は無影響


def test_measure_point_require_all_reps_rejects_partial_rep_failure():
    """Balanced caller's strict mode aborts at the first missing rep."""
    from orchestrator.calibrator import runner
    calls = {"n": 0}
    observations = []
    good = (
        {"throughput[tps]": "1000", "maxrss": "100 kB"},
        PerfCounters(llc_load_misses=10, llc_loads=100),
        0.5,
    )

    def fake_run_once(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("injected missing rep")
        return good

    original = runner.run_once
    runner.run_once = fake_run_once
    try:
        try:
            runner.measure_point(
                "dummy", records=1000, threads=4, clocks_per_us=1800,
                reps=3, rep_observations=observations,
                require_all_reps=True,
            )
        except RuntimeError as exc:
            assert "rep1/3 fatal" in str(exc)
        else:
            raise AssertionError("strict partial rep failure was accepted")
    finally:
        runner.run_once = original
    assert calls["n"] == 2


def test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc():
    """M3: timeout/例外/非 0/success が logical rep index からずれず全件残る。"""
    from orchestrator.calibrator import runner
    calls = {"n": 0}
    observations = []
    returncodes = []
    perf_text = (
        "11,,LLC-load-misses,0,100.00,,\n"
        "22,,LLC-loads,0,100.00,,\n"
        "33,,instructions,0,100.00,,\n"
        "44,,cycles,0,100.00,,\n"
    )

    def fake_run(argv, **_kwargs):
        index = calls["n"]
        calls["n"] += 1
        if index == 0:
            raise subprocess.TimeoutExpired(argv, 1.0)
        if index == 1:
            raise OSError("synthetic spawn failure")
        perf_path = Path(argv[argv.index("-o") + 1])
        perf_path.write_text(perf_text, encoding="utf-8")
        return _completed_process(7 if index == 2 else 0)

    point = runner.measure_point(
        "dummy", records=1000, threads=4, clocks_per_us=1800, reps=4,
        subprocess_runner=fake_run, rep_returncodes=returncodes,
        rep_observations=observations,
    )

    assert [row["rep_index"] for row in observations] == [0, 1, 2, 3]
    assert [row["returncode"] for row in observations] == [None, None, 7, 0]
    assert returncodes == [7, 0]
    assert observations[0]["counter_status"] == "incomplete"
    assert observations[1]["counter_status"] == "incomplete"
    assert observations[2]["perf_raw"] == {
        "LLC-load-misses": 11, "LLC-loads": 22,
        "instructions": 33, "cycles": 44,
    }
    assert observations[3]["missing_perf_events"] == []
    assert point.rep_observations == observations


def test_measure_point_execution_failure_is_exact_bool_for_all_outcomes():
    """The direct public surface distinguishes caught exceptions from rc alone."""
    from orchestrator.calibrator import runner

    def observe(*, failure=None, returncode=0):
        observations = []
        calls = {"n": 0}

        def fake_run(argv, **_kwargs):
            index = calls["n"]
            calls["n"] += 1
            if index == 0 and failure is not None:
                raise failure
            return _completed_process(returncode if index == 0 else 0)

        point = runner.measure_point(
            "/bench", records=1000, threads=4, clocks_per_us=1800,
            reps=2 if failure is not None else 1,
            subprocess_runner=fake_run, rep_observations=observations,
            use_perf=False,
        )
        assert point.rep_observations == observations
        assert all(type(row["execution_failure"]) is bool
                   for row in observations)
        return observations

    success = observe()
    nonzero = observe(returncode=7)
    runtime = observe(failure=RuntimeError("injected runtime failure"))
    timeout = observe(failure=subprocess.TimeoutExpired(["/bench"], 1.0))
    generic = observe(failure=Exception("injected generic failure"))

    assert success[0]["execution_failure"] is False
    assert nonzero[0]["returncode"] == 7
    assert nonzero[0]["execution_failure"] is False
    for observations in (runtime, timeout, generic):
        assert observations[0]["execution_failure"] is True
        assert observations[1]["execution_failure"] is False


def test_measure_point_rep_timestamps_are_generated_around_each_runner_call():
    """Balanced receipt timestamps come from the runner's exact rep boundary."""
    from orchestrator.calibrator import runner
    timestamps = []
    ticks = iter((101, 109, 201, 215))
    good = (
        {"throughput[tps]": "1000", "maxrss": "100 kB"},
        PerfCounters(llc_load_misses=10, llc_loads=100),
        0.5,
    )
    original_run_once = runner.run_once
    original_time_ns = runner.time.time_ns
    runner.run_once = lambda *_args, **_kwargs: good
    runner.time.time_ns = lambda: next(ticks)
    try:
        runner.measure_point(
            "dummy", records=1000, threads=4, clocks_per_us=1800,
            reps=2, rep_timestamps=timestamps,
        )
    finally:
        runner.run_once = original_run_once
        runner.time.time_ns = original_time_ns
    assert timestamps == [
        {"rep_index": 0, "started_at_ns": 101, "finished_at_ns": 109},
        {"rep_index": 1, "started_at_ns": 201, "finished_at_ns": 215},
    ]


def test_measure_point_rep_observations_no_perf_are_not_required():
    """P1/P5: no-perf は rc 0 を保ち counter だけを not_required にする。"""
    from orchestrator.calibrator import runner
    observations = []
    point = runner.measure_point(
        "dummy", records=1000, threads=4, clocks_per_us=1800, reps=2,
        subprocess_runner=lambda *args, **kwargs: _completed_process(0),
        rep_observations=observations, use_perf=False,
    )
    assert [row["returncode"] for row in observations] == [0, 0]
    assert [row["counter_status"] for row in observations] == [
        "not_required", "not_required",
    ]
    assert [row["missing_perf_events"] for row in observations] == [[], []]
    assert point.rep_observations == observations


def test_perf_raw_evidence_rejects_duplicate_and_infinite_values():
    """B3/A7: parser 集約値が残っても raw 証跡は曖昧値・inf を欠損へ倒す。"""
    from orchestrator.calibrator import runner
    text = (
        "11,,LLC-load-misses,0,100.00,,\n"
        "22,,LLC-loads,0,100.00,,\n"
        "33,,instructions,0,100.00,,\n"
        "44,,cycles,0,100.00,,\n"
        "<not counted>,,cycles,0,0.00,,\n"
    )
    assert runner._perf_raw_values(text) == {
        "LLC-load-misses": 11, "LLC-loads": 22,
        "instructions": 33, "cycles": None,
    }
    assert runner._perf_raw_values(
        text.replace("33,,instructions", "inf,,instructions")
    )["instructions"] is None
    assert runner._perf_raw_values(
        text.replace("33,,instructions", "33.5,,instructions")
    )["instructions"] is None


def test_measure_point_all_reps_fail_raises():
    """全 rep が run_once 例外なら集約 RuntimeError (測定不能を沈黙で None 化しない)。"""
    from orchestrator.calibrator import runner

    def fake_run_once(binary, gflags, numactl=None, timeout_s=120.0, extra_env=None):
        raise RuntimeError("ccbench produced no metrics (injected)")

    orig = runner.run_once
    runner.run_once = fake_run_once
    try:
        raised = False
        try:
            runner.measure_point("dummy", records=1000, threads=4,
                                 clocks_per_us=1800, reps=3)
        except RuntimeError as e:
            raised = True
            assert "all 3 reps failed" in str(e)
        assert raised, "全 rep 失敗で RuntimeError が出るべき"
    finally:
        runner.run_once = orig


# ===== calibrate: clocks_per_us フォールバックの成果物記録 =====

def test_clocks_fallback_recorded_in_result():
    """TSC 実測失敗時のフォールバック 2100 が result.clocks_per_us (成果物 JSON/MD)
    にも記録される (notes だけの semi-silent を解消、audit §2)。"""
    from orchestrator.calibrator import sweep
    from orchestrator.calibrator.model import CalibrationResult
    res = CalibrationResult(env_tag="t", threads=1, clocks_per_us=None)
    assert sweep._apply_clocks_fallback(res, None) == 2100
    assert res.clocks_per_us == 2100
    assert any("フォールバック" in n for n in res.notes)
    # 実測できた場合は素通り (result は不変)
    res2 = CalibrationResult(env_tag="t", threads=1, clocks_per_us=1800)
    assert sweep._apply_clocks_fallback(res2, 1800) == 1800
    assert res2.clocks_per_us == 1800 and res2.notes == []


# ===== competing_bench_pids (F3 admission 強化、付録3) =====
# 8b oracle は build cache を <output_root>/s8b-build-cache に置く
# (orchestrator/campaign/s8b_oracle_driver.py) ため、`build-variants/` に固定された旧
# パターンでは孤児 bench を素通りさせていた (docs/failures.md F3)。新パターンは path
# 非依存 (`ycsb_.*\.exe` のみ) にする代わり、自プロセス自身 (os.getpid()) だけを除外する
# (B-2: 子孫まで除外していた旧実装からの縮小 — 自分の子でも競合として検出する)。

def test_competing_bench_pids_pattern_is_path_independent():
    """pgrep へ渡すパターンが `build-variants/` 接頭辞を要求しないことを固定する
    (退行防止: 旧パターンへの巻き戻しを検知するテスト)。"""
    from orchestrator.calibrator import runner
    calls = []

    def fake_run(cmd, capture_output=True, text=True):
        calls.append(cmd)
        class _R:
            returncode = 1          # 無競合の確定信号 (rc==1 かつ出力空)
            stdout = ""
            stderr = ""
        return _R()

    orig = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        runner.competing_bench_pids()
    finally:
        runner.subprocess.run = orig
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[:2] == ["pgrep", "-af"]
    pattern = cmd[2]
    assert pattern == r"ycsb_.*\.exe"
    assert "build-variants" not in pattern


def test_competing_bench_pids_excludes_own_pid_only():
    """B-2: 除外されるのは自プロセス自身 (os.getpid()) の行**だけ**。自 PID 以外の
    行 (他者・孤児・自分の子を含む) はすべて競合として残る (子孫まで除外していた旧実装
    からの縮小 — この振る舞いへの逆戻りを検知する回帰テスト)。"""
    from orchestrator.calibrator import runner
    own = os.getpid()
    fake_stdout = (
        f"{own} /out/s8b-build-cache/gen0/ycsb_self.exe\n"
        "9999 /out/s8b-build-cache/gen0/ycsb_other.exe\n"
    )

    def fake_run(cmd, capture_output=True, text=True):
        class _R:
            returncode = 0          # 一致あり (PID 行を返す)
            stdout = fake_stdout
            stderr = ""
        return _R()

    orig_run = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        lines = runner.competing_bench_pids()
    finally:
        runner.subprocess.run = orig_run
    assert len(lines) == 1
    assert "9999" in lines[0]
    assert all(int(line.split(None, 1)[0]) != own for line in lines)  # 自 PID 行だけ除外


def test_competing_bench_pids_non_self_descendant_pid_is_competing():
    """B-2: 自 PID 以外の PID は「自分の子孫かどうか」に関係なく競合として残る。
    仮に子孫集合による除外へ逆戻りすると、直前 run 残骸/自分の子が黙って落ちる
    (孤児 livelock 汚染の再来) — その回帰を固定する。"""
    from orchestrator.calibrator import runner
    own = os.getpid()
    # own+1 は「自 PID ではない」ことだけが本質 (子孫かどうかを問わず残るべき)。
    other_pid = own + 1
    fake_stdout = f"{other_pid} /out/s8b-build-cache/gen0/ycsb_x.exe\n"

    def fake_run(cmd, capture_output=True, text=True):
        class _R:
            returncode = 0
            stdout = fake_stdout
            stderr = ""
        return _R()

    orig_run = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        lines = runner.competing_bench_pids()
    finally:
        runner.subprocess.run = orig_run
    assert len(lines) == 1 and str(other_pid) in lines[0]


def test_competing_bench_pids_unparseable_pid_kept_fails_closed():
    """pgrep 行の先頭 token が PID としてパースできない (想定外の出力形) 場合は
    素性不明として競合側に残す (規律4: 検知を弱める方向に倒さない)。"""
    from orchestrator.calibrator import runner
    fake_stdout = "not-a-pid some garbage ycsb_x.exe\n"

    def fake_run(cmd, capture_output=True, text=True):
        class _R:
            returncode = 0          # 一致あり (行はあるが先頭が PID 形でない)
            stdout = fake_stdout
            stderr = ""
        return _R()

    orig = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        lines = runner.competing_bench_pids()
    finally:
        runner.subprocess.run = orig
    assert len(lines) == 1
    assert "garbage" in lines[0]


class _FakeProc:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _probe_result(*, returncode=0, stdout="", stderr="", exc=None):
    """固定 rc/stdout/stderr (または例外) の pgrep 下で competing_bench_pids を呼び、
    戻り値 or 送出された CompetingBenchProbeError を返す。素の runner でも動くよう
    monkeypatch fixture でなく手動 save/restore を使う (このファイルの既存様式)。"""
    from orchestrator.calibrator import runner

    def fake_run(cmd, capture_output=True, text=True):
        if exc is not None:
            raise exc
        return _FakeProc(returncode, stdout, stderr)

    orig = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        return runner.competing_bench_pids()
    finally:
        runner.subprocess.run = orig


def _expect_probe_error(**kw):
    """_probe_result が CompetingBenchProbeError を送出することを固定し、例外を返す。"""
    from orchestrator.calibrator import runner
    try:
        _probe_result(**kw)
    except runner.CompetingBenchProbeError as e:
        return e
    raise AssertionError("CompetingBenchProbeError が送出されなかった")


def test_competing_bench_pids_rc1_clean_is_no_competition():
    """rc==1 かつ stdout・stderr とも空だけが「無競合の確定信号」= 空リスト (B-1)。"""
    assert _probe_result(returncode=1, stdout="", stderr="") == []


def test_recorded_competing_bench_probes_pass_admission():
    """tracked isolation.txt 6 件の production 観測が無競合に分類されることを固定する。"""
    from orchestrator.calibrator import runner
    recorded_probes = [
        ("0_873732.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
        ("0_873737.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
        ("0_873759.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
        ("0_873846.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
        ("0_873855.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
        ("0_873859.nqsv", 1, "", "", ("pgrep", "-af", r"ycsb_.*\.exe")),
    ]
    for artifact, rc, stdout, stderr, argv in recorded_probes:
        classified = runner.classify_competing_probe(
            rc, stdout, stderr, argv, own_pid=4242)
        assert classified == [], artifact


def test_competing_bench_pids_rc1_with_stderr_is_probe_error():
    """rc==1 でも stderr 非空 (BusyBox 等の option 構文エラーの罠) は fail-closed で例外
    にする — 空 stdout を「無競合」と誤認して汚染計測を採用しない (B-1)。"""
    e = _expect_probe_error(returncode=1, stdout="",
                            stderr="pgrep: unrecognized option '-a'")
    assert e.kind == "unexpected-rc"
    assert e.returncode == 1
    assert "unrecognized" in e.stderr_excerpt


def test_competing_bench_pids_rc1_with_stdout_is_probe_error():
    """rc==1 なのに stdout に PID 行が付随する矛盾出力も fail-closed で例外にする —
    「一致なし」の rc を信じて競合行を黙って捨てない (B-1, レビュー L2-N1)。"""
    e = _expect_probe_error(returncode=1, stdout="1234 ycsb_x.exe", stderr="")
    assert e.kind == "unexpected-rc"
    assert e.returncode == 1
    assert "ycsb_x.exe" in e.stdout_excerpt


def test_competing_bench_pids_rc0_empty_stdout_is_inconsistent():
    """rc==0 (一致あり) なのに stdout が空という内部矛盾は inconsistent-output で例外
    (B-1: rc==0 は非空 stdout 必須)。"""
    e = _expect_probe_error(returncode=0, stdout="", stderr="")
    assert e.kind == "inconsistent-output"
    assert e.returncode == 0


def test_competing_bench_pids_rc2_is_probe_error():
    """rc>1 (pgrep エラー) は fail-closed で例外 (旧: rc 未検査で空扱いの fail-open)。"""
    e = _expect_probe_error(returncode=2, stdout="", stderr="pgrep error")
    assert e.kind == "unexpected-rc" and e.returncode == 2


def test_competing_bench_pids_rc3_is_probe_error():
    """rc==3 (pgrep usage error 等) も fail-closed で例外。"""
    e = _expect_probe_error(returncode=3, stdout="", stderr="usage")
    assert e.kind == "unexpected-rc" and e.returncode == 3


def test_competing_bench_pids_negative_rc_is_probe_error():
    """負の returncode (シグナル終了) も rc>1 と同じく fail-closed で例外 (B-1: 負値網羅)。"""
    e = _expect_probe_error(returncode=-9, stdout="", stderr="")
    assert e.kind == "unexpected-rc" and e.returncode == -9


def test_competing_bench_pids_oserror_is_probe_error():
    """pgrep 起動自体が OSError で失敗したら fail-closed で例外 (旧契約 = 空リスト返しの
    fail-open を反転)。errno を保持する (B-6)。"""
    e = _expect_probe_error(exc=OSError(2, "pgrep not found"))
    assert e.kind == "exec-failure"
    assert e.errno == 2


def test_competing_bench_pids_subprocess_error_is_probe_error():
    """subprocess.SubprocessError も fail-closed で例外 (握りつぶさない, 規律3)。"""
    e = _expect_probe_error(exc=subprocess.SubprocessError("boom"))
    assert e.kind == "exec-failure"


def test_competing_bench_probe_error_as_dict_carries_structured_fields():
    """CompetingBenchProbeError.as_dict が WAL payload 用の全キーを持つ (B-6)。"""
    from orchestrator.calibrator import runner
    e = runner.CompetingBenchProbeError(
        "unexpected-rc", ["pgrep", "-af", "x"], returncode=2, errno=None,
        stdout="o" * 5000, stderr="e" * 5000)
    d = e.as_dict()
    assert set(d) == {"kind", "argv", "returncode", "errno",
                      "stdout_excerpt", "stderr_excerpt"}
    assert d["kind"] == "unexpected-rc" and d["returncode"] == 2
    # 抜粋は上限で切り詰められる (payload 肥大防止)。
    assert len(d["stdout_excerpt"]) == runner._PROBE_EXCERPT_LIMIT
    assert len(d["stderr_excerpt"]) == runner._PROBE_EXCERPT_LIMIT


def _spawn_fake_bench_child(fake_argv0):
    """自プロセスの直接子として、cmdline が `fake_argv0` になるプロセスを 1 つ起こす
    (execv で `/bin/sleep` に argv0 だけ差し替える)。呼び出し元が Popen を kill/wait する。"""
    return subprocess.Popen(
        [sys.executable, "-c",
         f"import os; os.execv('/bin/sleep', [{fake_argv0!r}, '20'])"])


def _spawn_fake_bench_orphan(fake_argv0, pid_file):
    """二重 fork で自プロセスの子孫から外れた「孤児」プロセスを 1 つ起こす
    (cmdline は `fake_argv0`)。孤児の PID を `pid_file` に書かせ、確認できるまで待つ。
    戻り値は (orphan_pid, middle_popen) — 呼び出し元が orphan を kill、middle を wait 済み。"""
    try:
        os.remove(pid_file)
    except OSError:
        pass
    script = (
        "import os, sys\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    os.setsid()\n"
        f"    with open({pid_file!r}, 'w') as f:\n"
        "        f.write(str(os.getpid()))\n"
        f"    os.execv('/bin/sleep', [{fake_argv0!r}, '20'])\n"
        "else:\n"
        "    sys.exit(0)\n"
    )
    middle = subprocess.Popen([sys.executable, "-c", script])
    middle.wait(timeout=5)
    deadline = time.monotonic() + 5
    orphan_pid = None
    while time.monotonic() < deadline:
        if os.path.exists(pid_file):
            content = open(pid_file, encoding="utf-8").read().strip()
            if content:
                orphan_pid = int(content)
                break
        time.sleep(0.05)
    return orphan_pid


def test_competing_bench_pids_real_orphan_under_s8b_build_cache_detected():
    """実プロセスで検証: `build-variants/` を経路に含まない孤児 bench
    (8b の `s8b-build-cache` 配下相当の cmdline) が実 pgrep 越しに検知される
    (F3 admission 強化の本題 — path 非依存化がなければ旧パターンは無反応だった)。"""
    if shutil.which("pgrep") is None or not os.path.isdir("/proc"):
        skip("pgrep コマンドまたは /proc が利用できない")
    from orchestrator.calibrator import runner
    pid_file = os.path.join(tempfile.gettempdir(),
                            f"_izanagi_test_orphan_{os.getpid()}.pid")
    fake_argv0 = "/tmp/out/s8b-build-cache/gen0/ycsb_orphan_admission_test.exe"
    orphan_pid = _spawn_fake_bench_orphan(fake_argv0, pid_file)
    try:
        assert orphan_pid is not None, "孤児プロセスの起動を確認できなかった"
        lines = runner.competing_bench_pids()
        assert any(str(orphan_pid) in ln for ln in lines), (
            f"s8b-build-cache 配下の孤児 bench (pid={orphan_pid}) が検知されなかった: "
            f"{lines}")
    finally:
        if orphan_pid is not None:
            try:
                os.kill(orphan_pid, signal.SIGKILL)
            except OSError:
                pass
        try:
            os.remove(pid_file)
        except OSError:
            pass


def test_competing_bench_pids_real_own_child_detected():
    """B-2 反転: 実プロセスで検証。自分が起こした直接の子プロセス (bench 相当の
    cmdline) は子孫であっても除外されず、競合として検出される (own-PID-only 縮小の
    本題 — 子孫除外へ逆戻りするとこの子が黙って落ちる)。"""
    if shutil.which("pgrep") is None or not os.path.isdir("/proc"):
        skip("pgrep コマンドまたは /proc が利用できない")
    from orchestrator.calibrator import runner
    fake_argv0 = f"/tmp/out/s8b-build-cache/gen0/ycsb_child_admission_test_{os.getpid()}.exe"
    child = _spawn_fake_bench_child(fake_argv0)
    try:
        time.sleep(0.3)          # execv 完了を待つ
        lines = runner.competing_bench_pids()
        assert any(str(child.pid) in ln for ln in lines), (
            f"自分の直接子 (pid={child.pid}) が競合として検出されなかった "
            f"(子孫除外への逆戻り疑い): {lines}")
    finally:
        child.kill()
        child.wait(timeout=5)


def _skip_exception_types():
    """skiputil.skip が実行環境に応じて投げうる例外型を集める。"""
    types = [Skip]
    try:
        import pytest
    except ImportError:
        return tuple(types)
    skipped = getattr(pytest.skip, "Exception", None)
    if isinstance(skipped, type) and issubclass(skipped, BaseException):
        types.append(skipped)
    return tuple(types)


def test_competing_bench_pids_missing_dependency_is_visible_skip():
    """README「依存物不在時の skip (可視化)」への疑似 return 回帰を撃つ。
    pgrep 不在時に実プロセス検査 2 本が PASS せず、skip 例外を送出することを固定する。
    """
    skip_exceptions = _skip_exception_types()
    original_which = shutil.which
    shutil.which = lambda _name: None
    try:
        for test_fn in (
            test_competing_bench_pids_real_orphan_under_s8b_build_cache_detected,
            test_competing_bench_pids_real_own_child_detected,
        ):
            try:
                test_fn()
            except skip_exceptions:
                continue
            raise AssertionError(
                f"{test_fn.__name__} が依存物不在を PASS に化かした"
            )
    finally:
        shutil.which = original_which


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
