# -*- coding: utf-8 -*-
"""critic digest の単体テスト (machine 非依存・mock WAL)。

pytest でも 素の `python orchestrator/tests/test_critic.py` でも走る。
"""
from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import wal                                          # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_START,  # noqa: E402
                            STAGE_COMMIT)
from critic.digest import build_digest, render_text               # noqa: E402


def _tmp_layout():
    d = tempfile.mkdtemp(prefix="izanagi_critic_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    return CampaignLayout(root=d).ensure()


def _write(lay, genome, committed=True, **li):
    wal.log(lay, genome, STAGE_BUILD_START, "test", {"genome": genome})
    wal.log(lay, genome, STAGE_BENCH_DONE, "test", {"leading_indicators": li})
    if committed:                                  # digest は committed のみ拾う
        wal.log(lay, genome, STAGE_COMMIT, "test", {"fitness_tps": li.get("throughput_tps")})


_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def test_load_sorts_by_throughput_and_marginal_back_off():
    lay = _tmp_layout()
    # BACK_OFF 0→1: throughput 半減・latency 倍・abort 不変 (= backoff は latency コスト)
    _write(lay, _G.format(b=0, l=1, t=0, w=0),
           throughput_tps=8_000_000, abort_rate=0.05, latency_ns=1000,
           llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0),
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("balanced", {"ycsb_rratio": "50"}, lay)
    assert len(d.genomes) == 2
    assert d.fastest.flags["BACK_OFF"] == 0           # throughput 降順
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"] == {"0": 8_000_000, "1": 4_000_000}
    assert abs(bo.rel_throughput - (-0.5)) < 1e-9     # 0→1 で -50%
    assert bo.means["abort_rate"]["0"] == bo.means["abort_rate"]["1"]  # abort 不変
    assert bo.means["latency_ns"] == {"0": 1000, "1": 2000}            # latency 倍


def test_no_wait_axis_is_categorical_LT():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0),         # L = 即abort
           throughput_tps=2_700_000, abort_rate=0.40, latency_ns=500,
           llc_miss_rate=0.3, ipc=1.0)
    _write(lay, _G.format(b=0, l=0, t=1, w=0),         # T = retry
           throughput_tps=1_900_000, abort_rate=0.50, latency_ns=700,
           llc_miss_rate=0.3, ipc=0.9)
    d = build_digest("balanced", {}, lay)
    nw = next(e for e in d.axes if e.axis == "no_wait")
    assert set(nw.levels) == {"L", "T"}                # NWL=1→L / NWT=1→T に畳む
    assert nw.means["throughput_tps"]["L"] == 2_700_000
    assert nw.means["throughput_tps"]["T"] == 1_900_000
    assert nw.means["latency_ns"]["L"] == 500 and nw.means["latency_ns"]["T"] == 700


def test_marginal_averages_over_other_flags():
    """限界効果は他フラグで周辺化する: WAL=0/1 各 2 genome の平均で軸効果を出す。"""
    lay = _tmp_layout()
    # BACK_OFF=0 を 2 genome (WAL 0/1)、BACK_OFF=1 を 2 genome (WAL 0/1)
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=0, l=1, t=0, w=1), throughput_tps=7_000_000,
           abort_rate=0.05, latency_ns=1100, llc_miss_rate=0.2, ipc=1.4)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), throughput_tps=4_000_000,
           abort_rate=0.05, latency_ns=2000, llc_miss_rate=0.2, ipc=1.0)
    _write(lay, _G.format(b=1, l=1, t=0, w=1), throughput_tps=3_000_000,
           abort_rate=0.05, latency_ns=2100, llc_miss_rate=0.2, ipc=0.9)
    d = build_digest("x", {}, lay)
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"]["0"] == 7_500_000     # (8M+7M)/2
    assert bo.means["throughput_tps"]["1"] == 3_500_000     # (4M+3M)/2
    wal_eff = next(e for e in d.axes if e.axis == "WAL")
    assert wal_eff.means["throughput_tps"]["0"] == 6_000_000  # (8M+4M)/2
    assert wal_eff.means["throughput_tps"]["1"] == 5_000_000  # (7M+3M)/2


def test_uncommitted_genome_excluded():
    """A (atomicity): bench_done はあるが COMMIT 前にクラッシュした genome は digest から除外。"""
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), committed=False,  # half-evaluated
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("x", {}, lay)
    assert len(d.genomes) == 1                   # 非 committed は不採用
    assert d.genomes[0].flags["BACK_OFF"] == 0


def test_render_text_has_axes_and_indicators():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    txt = render_text([build_digest("read-heavy", {"ycsb_rratio": "95"}, lay)])
    assert "read-heavy" in txt
    assert "BACK_OFF" in txt and "no_wait" in txt and "WAL" in txt
    assert "throughput_tps" in txt and "abort_rate" in txt
    assert "限界効果" in txt


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
