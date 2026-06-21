# -*- coding: utf-8 -*-
"""測定安定性 (§3.6 (2)(4)) の単体テスト。純ロジック (machine 非依存・モック注入)。

pytest でも 素の `python orchestrator/tests/test_stability.py` でも走る。
"""
from __future__ import annotations

import os
import sys
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from calibrator.stability import (                              # noqa: E402
    compare, mann_whitney_u, remeasure_until_stable)


def _measure_seq(seqs):
    """canned な throughput 列を順に返す measure_fn (末尾を繰り返す)。最後の呼び出し回数も持つ。"""
    box = {"i": 0}

    def fn():
        i = min(box["i"], len(seqs) - 1)
        box["i"] += 1
        return types.SimpleNamespace(throughputs=list(seqs[i]))
    fn.calls = lambda: box["i"]
    return fn


# ===== (2) 自動再測定 =====

def test_remeasure_converges_first_round_no_resettle():
    """反復内 CV が閾値以下なら 1 ラウンドで打ち切り、静定し直さない。"""
    settles = {"n": 0}
    m = _measure_seq([[100, 100, 100]])              # CV=0 → 即収束
    rem = remeasure_until_stable(m, settle_fn=lambda: settles.__setitem__("n", settles["n"] + 1))
    assert rem.rounds == 1 and rem.stable and not rem.unstable
    assert settles["n"] == 0                         # 収束したので測り直し=静定なし
    assert rem.nf.cv == 0.0 and m.calls() == 1


def test_remeasure_converges_later_round_resettles_before_remeasure():
    """1 回目が騒がしく 2 回目で収束 → 2 ラウンド、再測定前に 1 回だけ静定。"""
    settles = {"n": 0}
    m = _measure_seq([[100, 200, 50], [100, 100, 100]])
    rem = remeasure_until_stable(m, settle_fn=lambda: settles.__setitem__("n", settles["n"] + 1),
                                 cv_threshold=0.05, max_rounds=3)
    assert rem.rounds == 2 and rem.stable and not rem.unstable
    assert settles["n"] == 1                         # 2 回目の前に静定
    assert rem.nf.cv == 0.0                          # 採用は収束した 2 回目


def test_remeasure_unstable_keeps_lowest_cv_round():
    """規定ラウンドで収束しなければ unstable。採用は最も CV が低かったラウンド。"""
    settles = {"n": 0}
    # CV: round1=0.40, round2=0.08, round3=0.50 (全て >0.05) → 採用は round2
    m = _measure_seq([[100, 140, 60], [100, 108, 92], [100, 150, 50]])
    rem = remeasure_until_stable(m, settle_fn=lambda: settles.__setitem__("n", settles["n"] + 1),
                                 cv_threshold=0.05, max_rounds=3)
    assert rem.rounds == 3 and rem.unstable and not rem.stable
    assert settles["n"] == 2                         # round2,3 の前に静定
    assert rem.point.throughputs == [100, 108, 92]   # 最小 CV のラウンドを採用
    assert abs(rem.nf.cv - 0.08) < 1e-9
    assert rem.cv_history[1] < rem.cv_history[0]


def test_remeasure_single_sample_is_unstable():
    """1 反復しか取れない (CV 算出不能) なら収束扱いにせず unstable (沈黙して 1 点採用しない)。"""
    m = _measure_seq([[100]])
    rem = remeasure_until_stable(m, settle_fn=None, max_rounds=3)
    assert rem.rounds == 3 and rem.unstable and not rem.stable
    assert rem.nf.cv is None and rem.nf.median == 100   # median はあるが CV 不能


# ===== (4) 分布比較: Mann-Whitney U =====

def test_mwu_identical_distributions_not_significant():
    u, p = mann_whitney_u([100, 100, 100, 100, 100], [100, 100, 100, 100, 100])
    assert p == 1.0                                  # 全 tie → 分散 0 → 差なし


def test_mwu_fully_separated_is_significant():
    u, p = mann_whitney_u([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
    assert u == 0.0 and p < 0.05                     # 完全分離 → U=0, 有意


def test_mwu_empty_sample_is_indeterminate():
    u, p = mann_whitney_u([], [1, 2, 3])
    assert u is None and p == 1.0


# ===== (4) 分布比較: compare =====

def test_compare_below_noise_floor_is_no_difference():
    """noise floor 以下の中央値差は『差なし』に丸める (MWU を当てない)。"""
    c = compare([1000] * 5, [1015] * 5, noise_cv=0.05)
    assert c.verdict == "no-difference"
    assert c.p is None                               # 第一ゲートで止まり MWU 未実施
    assert abs(c.rel_median - 0.015) < 1e-9


def test_compare_significant_faster():
    base = [1000, 1010, 990, 1005, 995]              # median 1000
    var = [1200, 1210, 1190, 1205, 1195]             # median 1200, 完全分離
    c = compare(base, var, noise_cv=0.05)
    assert c.verdict == "faster" and c.p < 0.05 and c.rel_median > 0


def test_compare_significant_slower():
    base = [1200, 1210, 1190, 1205, 1195]
    var = [1000, 1010, 990, 1005, 995]
    c = compare(base, var, noise_cv=0.05)
    assert c.verdict == "slower" and c.p < 0.05 and c.rel_median < 0


def test_compare_above_floor_but_not_significant_is_no_difference():
    """noise floor は超えるが分布が重なり MWU 有意でない → 差なし (1 点比較に倒さない)。"""
    base = [100, 101, 99, 103, 98]                   # median 100
    var = [102, 104, 100, 105, 101]                  # median 102, rel 2% > floor 1%
    c = compare(base, var, noise_cv=0.01)
    assert c.verdict == "no-difference"
    assert c.p is not None and c.p >= 0.05           # MWU は当てたが有意でない


def test_compare_empty_is_indeterminate():
    assert compare([], [1, 2, 3]).verdict == "indeterminate"


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
