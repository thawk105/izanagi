# -*- coding: utf-8 -*-
"""S-1 の二層 exact permutation と効果量 (純関数、標準ライブラリのみ)。

層 ``h in {1, 2}`` ごとに対象群 4、対照群 4 を合併し、1 始まりの平均順位
``r_hi`` (tie は占有順位の平均) を与える。主統計量は層内 rank-sum の和を 2 倍した
整数 ``T = sum_h sum_{i in target_h} 2*r_hi`` とする。平均順位は 0.5 刻みなので、
この整数化により tail 境界で浮動小数の等値判定を行わずに済む。

帰無分布は各層の 8 観測から対象群 4 本を選ぶ全割付の直積であり、分割数は
``C(8, 4)^2 = 70^2 = 4,900``。片側 p 値は ``alternative='greater'`` なら
``p = P(T >= T_obs)``、``'less'`` なら ``p = P(T <= T_obs)`` とし、観測統計量と
同値の分割を tail に含める。Monte Carlo 近似は使わない。

効果量は判定に使わない。確率優越 A の主表示は campaign ブロックの位置ずれを混ぜない
``A_stratified`` (各層の ``P(target > control) + 0.5*P(tie)`` の平均) とし、全 8x8
ペアの ``A_pooled`` も副表示として返す。中央値差は対象群 minus 対照群、CV は各群 8
セッションをプールした標本標準偏差 (n-1) / mean である。
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from itertools import combinations
from typing import Optional, Sequence, Tuple

from ..calibrator.stability import _average_ranks
from .search_baselines import prob_superiority_two_sample


N_STRATA = 2
GROUP_SIZE = 4
PERMUTATIONS_PER_STRATUM = math.comb(2 * GROUP_SIZE, GROUP_SIZE)
N_PERMUTATIONS = PERMUTATIONS_PER_STRATUM ** N_STRATA

Strata = Tuple[Tuple[float, ...], Tuple[float, ...]]


@dataclass(frozen=True)
class EffectSizes:
    """検定判定に関与しない併記用の効果量。"""

    median_difference: float
    probability_superiority_stratified: float
    probability_superiority_pooled: float
    target_cv: Optional[float]
    control_cv: Optional[float]


@dataclass(frozen=True)
class StratifiedTestResult:
    """層別検定結果。``distribution`` は 4,900 分割の整数統計量列。"""

    statistic: int
    p_perm: float
    alternative: str
    distribution: Tuple[int, ...]
    n_permutations: int
    effects: EffectSizes


def _validate_inputs(target_strata: Sequence[Sequence[float]],
                     control_strata: Sequence[Sequence[float]]) -> Tuple[Strata, Strata]:
    """固定済みの 2 層・4/4 契約と有限性を検査し、黙った除外を防ぐ。"""
    try:
        target_layers = tuple(tuple(layer) for layer in target_strata)
        control_layers = tuple(tuple(layer) for layer in control_strata)
    except TypeError as exc:
        raise ValueError("target_strata / control_strata は層の列でなければならない") from exc
    if len(target_layers) != N_STRATA or len(control_layers) != N_STRATA:
        raise ValueError("層数は対象群・対照群ともに 2 でなければならない")
    for h, (target, control) in enumerate(zip(target_layers, control_layers), start=1):
        if len(target) != GROUP_SIZE or len(control) != GROUP_SIZE:
            raise ValueError(f"層 {h} の群サイズは 4/4 でなければならない")
        for value in target + control:
            try:
                finite = math.isfinite(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"層 {h} に有限な数値でない観測値がある: {value!r}") from exc
            if not finite:
                raise ValueError(f"層 {h} に非有限値がある: {value!r}")
    return target_layers, control_layers  # type: ignore[return-value]


def _integer_ranks(values: Sequence[float]) -> Tuple[int, ...]:
    """平均順位を 2 倍した整数へ変換する。順位実装は既存 calibrator と共有する。"""
    ranks = _average_ranks(values)
    doubled = tuple(int(round(2.0 * rank)) for rank in ranks)
    if any(not math.isclose(rank2 / 2.0, rank, rel_tol=0.0, abs_tol=0.0)
           for rank2, rank in zip(doubled, ranks)):
        raise AssertionError("平均順位が 0.5 刻みでない")
    return doubled


def _layer_statistics(target: Sequence[float],
                      control: Sequence[float]) -> Tuple[int, Tuple[int, ...]]:
    ranks2 = _integer_ranks(tuple(target) + tuple(control))
    observed = sum(ranks2[:GROUP_SIZE])
    distribution = tuple(sum(ranks2[i] for i in selected)
                         for selected in combinations(range(2 * GROUP_SIZE), GROUP_SIZE))
    if len(distribution) != PERMUTATIONS_PER_STRATUM:
        raise AssertionError("層内割付数が C(8,4) と一致しない")
    return observed, distribution


def _rank_sum_and_distribution(target: Strata, control: Strata) -> Tuple[int, Tuple[int, ...]]:
    layers = [_layer_statistics(t, c) for t, c in zip(target, control)]
    observed = sum(item[0] for item in layers)
    distribution = tuple(left + right
                         for left in layers[0][1]
                         for right in layers[1][1])
    if len(distribution) != N_PERMUTATIONS:
        raise AssertionError("層間直積の割付数が C(8,4)^2 と一致しない")
    return observed, distribution


def stratified_rank_sum(target_strata: Sequence[Sequence[float]],
                        control_strata: Sequence[Sequence[float]]) -> int:
    """観測された層別 rank-sum の和を、2 倍した整数で返す。"""
    target, control = _validate_inputs(target_strata, control_strata)
    return _rank_sum_and_distribution(target, control)[0]


def _cv(values: Sequence[float]) -> Optional[float]:
    """既存 noise_floor と同じ n-1 標準偏差 / mean。mean=0 は算出不能。"""
    mean = statistics.fmean(values)
    return statistics.stdev(values) / mean if mean else None


def _effect_sizes(target: Strata, control: Strata) -> EffectSizes:
    target_all = [value for layer in target for value in layer]
    control_all = [value for layer in control for value in layer]
    layer_as = [prob_superiority_two_sample(list(c), list(t))
                for t, c in zip(target, control)]
    return EffectSizes(
        median_difference=statistics.median(target_all) - statistics.median(control_all),
        probability_superiority_stratified=statistics.fmean(layer_as),
        probability_superiority_pooled=prob_superiority_two_sample(control_all, target_all),
        target_cv=_cv(target_all),
        control_cv=_cv(control_all),
    )


def stratified_test(target_strata: Sequence[Sequence[float]],
                    control_strata: Sequence[Sequence[float]],
                    alternative: str) -> StratifiedTestResult:
    """層別 rank-sum の exact 片側 permutation 検定と効果量を返す。"""
    if alternative not in ("greater", "less"):
        raise ValueError(f"alternative={alternative!r} は greater / less のみ")
    target, control = _validate_inputs(target_strata, control_strata)
    observed, distribution = _rank_sum_and_distribution(target, control)
    if alternative == "greater":
        hit = sum(statistic >= observed for statistic in distribution)
    else:
        hit = sum(statistic <= observed for statistic in distribution)
    return StratifiedTestResult(
        statistic=observed,
        p_perm=hit / N_PERMUTATIONS,
        alternative=alternative,
        distribution=distribution,
        n_permutations=N_PERMUTATIONS,
        effects=_effect_sizes(target, control),
    )


def p_star(p_perm: float, gates_passed: bool) -> float:
    """driver が判定した gate が全通過なら p、そうでなければ 1.0 を返す。"""
    if not isinstance(gates_passed, bool):
        raise ValueError("gates_passed は bool でなければならない")
    if not math.isfinite(p_perm) or not 0.0 <= p_perm <= 1.0:
        raise ValueError("p_perm は有限な [0, 1] の値でなければならない")
    return p_perm if gates_passed else 1.0


def family_p(p_stars: Sequence[float]) -> float:
    """intersection-union family の p 値として p* 列の max を返す。"""
    values = tuple(p_stars)
    if not values:
        raise ValueError("p_stars は空にできない")
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("p_stars は有限な [0, 1] の値でなければならない")
    return max(values)
