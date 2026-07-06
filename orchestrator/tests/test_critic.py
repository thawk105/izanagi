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
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT)
from critic.digest import (build_digest, load_liveness_rejections,  # noqa: E402
                           load_rejections, render_text)


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


def test_load_rejections_surfaces_structured_anomaly():
    """S4 (規律3 配線): load_rejections が verify-red の構造化 anomaly を次手入力として拾い、
    verify を持たない abort (build-error 等) は除外する。`load_workload` (緑) と対をなす。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    builderr = _G.format(b=0, l=1, t=0, w=0)
    # verify-red の variant (pipeline が書く形 = abort payload に verify 構造)
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red, "src_token": "codediff1"})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable",
             "verify": {"verdict": "non-serializable", "anomaly_count": 1,
                        "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                                       "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                                  "reasons": [{"type": "rw", "key": "aa"}]}]}],
                        "integrity": {"clean": True}}})
    # verify を持たない abort (build-error) は規律3 の次手入力ではない → 除外
    wal.log(lay, builderr, STAGE_BUILD_START, "test", {"genome": builderr})
    wal.log(lay, builderr, STAGE_ABORT, "test", {"reason": "build-error"})

    rej = load_rejections(lay)
    assert len(rej) == 1                          # build-error は除外
    assert rej[0].genome == red
    assert rej[0].flags["BACK_OFF"] == 1          # genome flags まで復元
    assert rej[0].verdict == "non-serializable"
    assert rej[0].anomalies[0]["phenomenon"] == "G2"
    assert rej[0].anomalies[0]["edges"][0]["reasons"][0]["key"] == "aa"
    assert rej[0].integrity == {"clean": True}
    # コード軸の識別 (D23): 同 canonical 別コードの RED variant が alias しないよう
    # WAL キーと src_token も次手入力に載る
    assert rej[0].variant == red
    assert rej[0].src_token == "codediff1"


def test_load_liveness_rejections_surfaces_reason_and_extra():
    """S4 consumer (規律3): liveness-red (verify 前に死んだ) が構造化されて次手入力に
    届き、infra 系 (build-error/eval-exception 等) は詳細でなく正規化 reason の件数に
    集約される (詳細は返さないが沈黙もさせない)。verify-red は混ざらない。"""
    lay = _tmp_layout()
    to = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, to, STAGE_BUILD_START, "test", {"genome": to, "src_token": "codediff9"})
    wal.log(lay, to, STAGE_ABORT, "test", {"reason": "trace-timeout", "timeout_s": 120.0})
    te = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, te, STAGE_BUILD_START, "test", {"genome": te})
    wal.log(lay, te, STAGE_ABORT, "test",
            {"reason": "trace-empty", "commits": 0, "aborts": 4321})
    b1 = _G.format(b=0, l=0, t=1, w=0)
    wal.log(lay, b1, STAGE_BUILD_START, "test", {"genome": b1})
    wal.log(lay, b1, STAGE_ABORT, "test", {"reason": "build-error"})
    b2 = _G.format(b=1, l=0, t=1, w=0)
    wal.log(lay, b2, STAGE_BUILD_START, "test", {"genome": b2})
    wal.log(lay, b2, STAGE_ABORT, "test",
            {"reason": "eval-exception: TypeError: boom"})   # 動的部は正規化で畳む
    vr = _G.format(b=1, l=1, t=0, w=1)
    wal.log(lay, vr, STAGE_BUILD_START, "test", {"genome": vr})
    wal.log(lay, vr, STAGE_ABORT, "test",
            {"reason": "non-serializable",
             "verify": {"verdict": "non-serializable"}})

    lrs, other = load_liveness_rejections(lay)
    assert {l.reason for l in lrs} == {"trace-timeout", "trace-empty"}
    lto = next(l for l in lrs if l.reason == "trace-timeout")
    assert lto.extra.get("timeout_s") == 120.0
    assert lto.variant == to and lto.src_token == "codediff9"
    assert lto.flags["BACK_OFF"] == 1
    lte = next(l for l in lrs if l.reason == "trace-empty")
    assert lte.extra.get("commits") == 0 and lte.extra.get("aborts") == 4321
    assert other == {"build-error": 1, "eval-exception": 1}


def test_rejection_types_keep_forward_workload_tag():
    """D36 決定 4 (段 5 配線予定) への前方寛容: abort payload に workload タグが来たら
    verify-red / liveness-red の両型が生値で保持する (形の確定は D36 実装時)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    wal.log(lay, red, STAGE_BUILD_START, "test", {"genome": red})
    wal.log(lay, red, STAGE_ABORT, "test",
            {"reason": "non-serializable", "workload": {"tag": "s2"},
             "verify": {"verdict": "non-serializable", "anomalies": [],
                        "integrity": {}}})
    lv = _G.format(b=0, l=1, t=0, w=0)
    wal.log(lay, lv, STAGE_BUILD_START, "test", {"genome": lv})
    wal.log(lay, lv, STAGE_ABORT, "test",
            {"reason": "trace-timeout", "workload": {"tag": "s2"}})
    rej = load_rejections(lay)
    lrs, _ = load_liveness_rejections(lay)
    assert rej[0].workload == {"tag": "s2"}
    assert lrs[0].workload == {"tag": "s2"}
    assert "workload" not in lrs[0].extra      # 別フィールドに分離 (extra と二重化しない)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}"); failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
