# -*- coding: utf-8 -*-
"""P2-5 誘導アーム + ベースラインの単体テスト (machine 非依存・mock WAL)。

リーク制御 (online digest が評価済みしか含まない) と到達判定・ベースライン期待値の回帰固定。
pytest でも 素の `python orchestrator/tests/test_guided.py` でも走る。
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

from campaign import replay, wal                                  # noqa: E402
from campaign.genome import SILO_SPACE                            # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_START,  # noqa: E402
                            STAGE_COMMIT)
from campaign.search_baselines import (expectation, oracle_ceiling,  # noqa: E402
                                       random_reach_distribution, reached_cost)
from critic.online_digest import LeakageError, online_digest      # noqa: E402

_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def _tmp_layout():
    d = tempfile.mkdtemp(prefix="izanagi_guided_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    return CampaignLayout(root=d).ensure()


def _gr(canon, med):
    return replay.GenomeResult(genome=canon, flags=replay.parse_flags(canon),
                               fitness_tps=med, tps=[med] * 5,
                               leading_indicators={}, certified=True)


# ---- label ↔ genome 逆写像 (誘導の次手翻訳) ----

def test_genome_label_roundtrip():
    """全 8 genome で genome_label → genome_from_label が canonical に戻る。"""
    for g in SILO_SPACE.enumerate():
        lab = replay.genome_label(g.flags)
        back = replay.genome_from_label(lab)
        assert back.canonical() == g.canonical(), (lab, g.canonical(), back.canonical())


def test_genome_from_label_rejects_invalid():
    """不正/空間外ラベルは ValueError (空間外を黙って評価しない、規律6)。"""
    for bad in ["B0-X-W0", "B2-L-W0", "garbage", "B0-L", "B0-L-W2", "B0-L-W0-extra"]:
        try:
            replay.genome_from_label(bad)
            raise AssertionError(f"{bad!r} を弾けなかった")
        except ValueError:
            pass


# ---- リーク制御: online digest は評価済みしか含まない ----

def test_online_digest_leakage_assert():
    """digest の genome 数 > 評価回数 なら LeakageError (未評価リークの機械検知)。"""
    lay = _tmp_layout()
    for g in (_G.format(b=0, l=1, t=0, w=0), _G.format(b=1, l=1, t=0, w=0)):
        wal.log(lay, g, STAGE_BUILD_START, "test", {"genome": g})
        wal.log(lay, g, STAGE_BENCH_DONE, "test", {"leading_indicators": {"throughput_tps": 1.0}})
        wal.log(lay, g, STAGE_COMMIT, "test", {"fitness_tps": 1.0})
    # committed 2 genome。評価回数 1 と主張したら未評価が漏れている。
    try:
        online_digest(lay, "x", {}, iterations=1)
        raise AssertionError("LeakageError が出なかった (リーク検知が壊れている)")
    except LeakageError:
        pass
    d = online_digest(lay, "x", {}, iterations=2)        # ちょうど → OK
    assert len(d.genomes) == 2


# ---- 到達コスト (全戦略共通定義) ----

def test_reached_cost():
    assert reached_cost(["a", "b", "c"], {"c"}) == 3
    assert reached_cost(["x"], {"x"}) == 1
    assert reached_cost(["a", "b", "c"], {"a"}) == 1
    assert reached_cost(["a", "b"], {"z"}) == 2          # 未到達 → 予算上限 (= len)


# ---- ベースライン期待値 (1.4 でなく 1.80 を回帰固定、批判2-#5) ----

def test_random_distribution_sums_and_expectation():
    for n, k, exp in [(8, 1, 4.5), (8, 4, 1.8), (8, 2, 3.0)]:
        d = random_reach_distribution(n, k)
        assert abs(sum(d.values()) - 1.0) < 1e-9, (n, k, sum(d.values()))
        assert abs(expectation(d) - exp) < 1e-9, (n, k, expectation(d))


def test_oracle_ceiling():
    assert abs(oracle_ceiling(8, 4) - 1.5) < 1e-9
    assert abs(oracle_ceiling(8, 1) - 1.875) < 1e-9


# ---- winner-tied set = no-difference 連結成分 (winner pivot 非依存) ----

def test_winner_tied_set_basic():
    win = _G.format(b=0, l=1, t=0, w=0)
    near = _G.format(b=0, l=1, t=0, w=1)      # 1% 差 < floor → tied
    far = _G.format(b=1, l=1, t=0, w=0)       # 50% 差 → not tied
    land = {win: _gr(win, 100.0), near: _gr(near, 99.0), far: _gr(far, 50.0)}
    tied = replay.winner_tied_set(land, between_run_cv=0.03)
    assert tied == {win, near}, tied


def test_winner_tied_set_transitive_chain():
    """a-b・b-c が floor 内なら a-c が floor 超でも連結成分で全て tied。"""
    a = _G.format(b=0, l=1, t=0, w=0)         # 100
    b = _G.format(b=0, l=1, t=0, w=1)         # 98  (a と 2%)
    c = _G.format(b=0, l=0, t=1, w=0)         # 96  (b と ~2%、a と ~4%)
    d = _G.format(b=1, l=1, t=0, w=0)         # 50  (far)
    land = {a: _gr(a, 100.0), b: _gr(b, 98.0), c: _gr(c, 96.0), d: _gr(d, 50.0)}
    tied = replay.winner_tied_set(land, between_run_cv=0.03)
    assert tied == {a, b, c}, tied            # 連結で 3 つ、far は除外


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
