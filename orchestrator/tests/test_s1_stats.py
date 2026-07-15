# -*- coding: utf-8 -*-
"""S-1 層別統計の手計算突合・独立全列挙・凍結回帰。"""
from __future__ import annotations

import math
import os
import statistics
import sys
from itertools import combinations

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_stats  # noqa: E402


def _reference_ranks2(values):
    """テスト専用の平均順位実装。製品コードと独立に 2 倍整数を直接作る。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks2 = [0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank2 = i + j + 2
        for k in range(i, j + 1):
            ranks2[order[k]] = rank2
        i = j + 1
    return ranks2


def _reference(target, control, alternative):
    """各層 70 割付を独立に作り、素朴な 4,900 直積を全列挙する。"""
    observed = 0
    layer_distributions = []
    for target_layer, control_layer in zip(target, control):
        ranks2 = _reference_ranks2(list(target_layer) + list(control_layer))
        observed += sum(ranks2[:4])
        layer_distributions.append(tuple(
            sum(ranks2[i] for i in selected)
            for selected in combinations(range(8), 4)))
    distribution = tuple(left + right
                         for left in layer_distributions[0]
                         for right in layer_distributions[1])
    if alternative == "greater":
        hit = sum(statistic >= observed for statistic in distribution)
    else:
        hit = sum(statistic <= observed for statistic in distribution)
    return observed, distribution, hit / 4900


def _assert_value_error(fn, *args):
    try:
        fn(*args)
        raise AssertionError("ValueError が発生しなかった")
    except ValueError:
        pass


def test_complete_separation_hand_calculated():
    """各層の最大 rank-sum は一意なので greater tail は 1/4,900。"""
    target = [[5, 6, 7, 8], [15, 16, 17, 18]]
    control = [[1, 2, 3, 4], [11, 12, 13, 14]]
    result = s1_stats.stratified_test(target, control, "greater")
    assert result.statistic == 104
    assert result.n_permutations == math.comb(8, 4) ** 2 == 4900
    assert abs(result.p_perm - 1 / 4900) < 1e-12
    assert s1_stats.stratified_test(target, control, "less").p_perm == 1.0

    reverse = s1_stats.stratified_test(control, target, "greater")
    assert reverse.statistic == 40
    assert reverse.p_perm == 1.0


def test_rank_crossings_reference_and_frozen_literals():
    """完全分離から 1 点が交差する例と、両層で交差する例を凍結する。"""
    cases = [
        ([[0, 5, 6, 7], [14, 15, 16, 17]],
         [[1, 2, 3, 4], [10, 11, 12, 13]], 0.007755102040816327),
        ([[3, 6, 7, 8], [11, 12, 17, 18]],
         [[1, 2, 4, 5], [13, 14, 15, 16]], 0.13489795918367348),
    ]
    for target, control, frozen_p in cases:
        observed, distribution, reference_p = _reference(target, control, "greater")
        result = s1_stats.stratified_test(target, control, "greater")
        assert result.statistic == observed
        assert result.distribution == distribution
        assert abs(result.p_perm - reference_p) < 1e-12
        assert abs(result.p_perm - frozen_p) < 1e-12


def test_all_ties_are_conservative_and_effects_are_neutral():
    target = [[7, 7, 7, 7], [7, 7, 7, 7]]
    control = [[7, 7, 7, 7], [7, 7, 7, 7]]
    result = s1_stats.stratified_test(target, control, "greater")
    assert result.statistic == 72
    assert set(result.distribution) == {72}
    assert result.p_perm == 1.0
    assert result.effects.probability_superiority_stratified == 0.5
    assert result.effects.probability_superiority_pooled == 0.5
    assert result.effects.median_difference == 0.0
    assert result.effects.target_cv == 0.0
    assert result.effects.control_cv == 0.0


def test_partial_ties_reference_and_frozen_literal():
    target = [[2, 2, 5, 7], [10, 12, 12, 15]]
    control = [[1, 2, 4, 6], [9, 12, 13, 14]]
    observed, distribution, reference_p = _reference(target, control, "greater")
    result = s1_stats.stratified_test(target, control, "greater")
    assert result.statistic == observed == 76
    assert result.distribution == distribution
    assert abs(result.p_perm - reference_p) < 1e-12
    assert abs(result.p_perm - 0.37979591836734694) < 1e-12


def test_three_fixed_distributions_match_independent_enumeration():
    """tie なし 2 例 + 部分 tie 1 例で分布列と両方向 p を完全突合する。"""
    cases = [
        ([[0, 5, 6, 7], [14, 15, 16, 17]],
         [[1, 2, 3, 4], [10, 11, 12, 13]]),
        ([[3, 6, 7, 8], [11, 12, 17, 18]],
         [[1, 2, 4, 5], [13, 14, 15, 16]]),
        ([[1, 4, 4, 8], [10, 11, 15, 16]],
         [[2, 3, 6, 7], [9, 12, 13, 14]]),
    ]
    for target, control in cases:
        for alternative in ("greater", "less"):
            observed, distribution, p_value = _reference(target, control, alternative)
            result = s1_stats.stratified_test(target, control, alternative)
            assert (result.statistic, result.distribution) == (observed, distribution)
            assert result.p_perm == p_value


def test_effect_sizes_use_registered_definitions():
    target = [[5, 6, 7, 8], [15, 16, 17, 18]]
    control = [[1, 2, 3, 4], [11, 12, 13, 14]]
    effects = s1_stats.stratified_test(target, control, "greater").effects
    target_all = [value for layer in target for value in layer]
    control_all = [value for layer in control for value in layer]
    expected_median_difference = statistics.median(target_all) - statistics.median(control_all)
    assert effects.median_difference == expected_median_difference
    assert effects.probability_superiority_stratified == 1.0
    # pooled は campaign 間の位置差も含むため、この例では層別 A と異なる。
    assert effects.probability_superiority_pooled == 0.75
    expected_target_cv = statistics.stdev(target_all) / statistics.fmean(target_all)
    expected_control_cv = statistics.stdev(control_all) / statistics.fmean(control_all)
    assert abs(effects.target_cv - expected_target_cv) < 1e-12
    assert abs(effects.control_cv - expected_control_cv) < 1e-12


def test_input_validation_fails_closed():
    valid = [[1, 2, 3, 4], [5, 6, 7, 8]]
    _assert_value_error(s1_stats.stratified_test,
                        [[1, 2, 3], [5, 6, 7, 8]], valid, "greater")
    _assert_value_error(s1_stats.stratified_test,
                        [[1, 2, 3, 4]], [[5, 6, 7, 8]], "greater")
    for nonfinite in (math.nan, math.inf, -math.inf):
        _assert_value_error(s1_stats.stratified_test,
                            [[1, 2, 3, nonfinite], [5, 6, 7, 8]], valid, "greater")
    _assert_value_error(s1_stats.stratified_test, valid, valid, "two-sided")


def test_p_star_and_family_p():
    assert s1_stats.p_star(0.0125, True) == 0.0125
    assert s1_stats.p_star(0.0125, False) == 1.0
    assert s1_stats.family_p([0.01, 0.2, 0.03]) == 0.2
    _assert_value_error(s1_stats.family_p, [])


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {fn.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
