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
from campaign.search_baselines import (exact_perm_pvalue_A,       # noqa: E402
                                       expectation, oracle_ceiling,
                                       prob_superiority,
                                       prob_superiority_two_sample,
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
    """digest の genome 数 > iterations なら LeakageError (配線 sanity: iterations 誤計算検知)。

    注: この assert は独立な第二防壁ではない — genome 数も iterations も同一誘導 WAL の
    STAGE_COMMIT 由来ゆえ同一 layout 経路では恒真化する (D26)。中立性の真の担保は WAL 分離
    + load_p2_2 非 import。ここで固定するのは「iterations を誤って渡した配線ミスを捕える」挙動。"""
    lay = _tmp_layout()
    for g in (_G.format(b=0, l=1, t=0, w=0), _G.format(b=1, l=1, t=0, w=0)):
        wal.log(lay, g, STAGE_BUILD_START, "test", {"genome": g})
        wal.log(lay, g, STAGE_BENCH_DONE, "test", {"leading_indicators": {"throughput_tps": 1.0}})
        wal.log(lay, g, STAGE_COMMIT, "test", {"fitness_tps": 1.0})
    # committed 2 genome。iterations=1 と誤計算したら sanity が発火する。
    try:
        online_digest(lay, "x", {}, iterations=1)
        raise AssertionError("LeakageError が出なかった (配線 sanity が壊れている)")
    except LeakageError:
        pass
    d = online_digest(lay, "x", {}, iterations=2)        # 整合 → OK
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


# ---- 確率優越 a の校正 (D29: 同分布で厳密 0.500、p_lt は系統バイアス) ----

def test_prob_superiority_a_calibrated_at_null():
    """戦略が random と完全同分布なら a = 0.500 (厳密)。p_lt は 0.5 を下回る
    系統バイアスを持つ (k=1 で 0.4375、k=4 で <0.4) ことも回帰固定する —
    p_lt を 0.5 基準で読むと negative result を実態より強く見せる (D29)。"""
    for n, k in [(8, 1), (8, 4), (8, 2)]:
        d = random_reach_distribution(n, k)
        # 「戦略のコスト標本 = random 分布そのもの」を重み付きで再現
        # (各コスト j を確率質量ぶんだけ並べる代わりに、期待値として直接計算)
        ps = prob_superiority(list(d.keys()), d)
        a_null = sum(p * (sum(q for j, q in d.items() if j > c) +
                          0.5 * sum(q for j, q in d.items() if j == c))
                     for c, p in d.items())
        assert abs(a_null - 0.5) < 1e-9, (n, k, a_null)          # a は厳密に校正
        p_lt_null = sum(p * sum(q for j, q in d.items() if j > c)
                        for c, p in d.items())
        assert p_lt_null < 0.5 - 1e-9, (n, k, p_lt_null)          # p_lt は系統的に下方
        assert ps["a"] == (ps["p_lt"] + ps["p_le"]) / 2           # 定義の整合


def test_prob_superiority_two_sample_null_and_direction():
    """二標本 A: 同一標本同士は 0.5、一様に速い/遅い標本は 1.0/0.0。"""
    xs = [1, 2, 3, 4]
    assert abs(prob_superiority_two_sample(xs, xs) - 0.5) < 1e-9
    assert prob_superiority_two_sample([1, 1], [5, 6]) == 1.0
    assert prob_superiority_two_sample([7, 8], [1, 2]) == 0.0


def test_exact_perm_pvalue_hand_calculated():
    """厳密 permutation の校正: 分割を手で列挙できる小ケースと突合。

    xs=[1,2] vs ys=[1,3]: pooled {1:2,2:1,3:1} から 2 本選ぶ C(4,2)=6 分割は
    構成 (A値, 重み) = (1.0,1)/(0.625,2)/(0.375,2)/(0.0,1)。観測 A=0.625 なので
    less: P(A≤0.625)=5/6、greater: P(A≥0.625)=3/6。"""
    res = exact_perm_pvalue_A([1, 2], [1, 3], "less")
    assert abs(res["p"] - 5 / 6) < 1e-12
    assert abs(res["A"] - 0.625) < 1e-12
    assert res["A"] == prob_superiority_two_sample([1, 2], [1, 3])  # A の定義一致
    assert abs(exact_perm_pvalue_A([1, 2], [1, 3], "greater")["p"] - 0.5) < 1e-12
    # 2 標本 1 本ずつ: 選抜 2 通りのみ
    assert exact_perm_pvalue_A([1], [2], "less")["p"] == 1.0
    assert exact_perm_pvalue_A([2], [1], "less")["p"] == 0.5
    # 同一多重集合同士は対称: A=0.5 で less/greater とも中央値を含み ≥0.5
    sym = exact_perm_pvalue_A([1, 2, 3], [1, 2, 3], "less")
    assert abs(sym["A"] - 0.5) < 1e-12 and sym["p"] >= 0.5
    try:
        exact_perm_pvalue_A([1], [2], "two-sided")
        raise AssertionError("alternative='two-sided' が ValueError にならなかった")
    except ValueError:
        pass


def test_exact_perm_pvalue_frozen_write_heavy():
    """P2-5 write-heavy 誘導 vs 貪欲の p の凍結回帰 (correction_2026_07_03)。

    guided_costs は p2-5-summary.json 凍結値、greedy 500 本は
    run_workload('write-heavy', k_trials=500, seed0=0) の決定論 replay の度数分布
    (凍結 greedy_p_lt=0.45475 と byte 一致することは summary.json provenance で確認済み)。
    旧記録「permutation p<1e-4」は方式未記録の Monte Carlo による過大表示で、
    厳密値は 2.52×10⁻⁴ (Holm ×6 でも <0.05 なので「有意に有害」の結論は不変)。"""
    guided = [1, 3, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8]
    greedy_hist = {1: 62, 2: 66, 3: 67, 4: 35, 5: 31, 6: 182, 7: 57}
    greedy = [v for v, c in greedy_hist.items() for _ in range(c)]
    assert len(greedy) == 500
    res = exact_perm_pvalue_A(guided, greedy, "less")
    assert abs(res["p"] - 2.521080185096e-04) < 1e-12
    assert abs(res["A"] - 0.230416666667) < 1e-9   # 凍結 guided_vs_greedy_A=0.2304
    assert res["n_configs"] == 50268
    assert 1e-4 < res["p"] < 3e-4                  # 「p<1e-4」が過大表示だったことの固定
    assert res["p"] * 6 < 0.05                     # Holm ×6 でも有意 = 結論不変


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
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
