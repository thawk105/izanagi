# -*- coding: utf-8 -*-
"""測定安定性 (roadmap §3.6 の (2)(4))。純関数 + callable 注入 = machine に触れずモックでテスト可能。

Phase 1 で配線済みの (1)(3) (noise floor + 反復中央値・CV、`analyze.noise_floor`) の上に積む:

- **(2) 外れ値 → 自動再測定** (`remeasure_until_stable`): 反復内 CV が閾値を超えたら静定して
  測り直す。規定ラウンドで収束しなければ `unstable`。`measure_fn`/`settle_fn` を注入する
  ので、実ベンチを回さずにモックでテストできる (実走は pipeline が bench_lock 下=直列で行う、
  絶対規律4)。
- **(4) 採否は分布比較** (`compare`): noise floor 以下の差は「差なし」に丸め、超える差だけ
  Mann-Whitney U で有意性を判定する。scipy 等の重い統計機構は使わない (正規近似 + tie/連続補正)。
  **unstable な variant は呼び手が比較から除外する** (沈黙して 1 点を採用しない)。
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

from .analyze import DEFAULT_NOISE_CV, noise_floor
from .model import NoiseFloor


# 既定の閾値 (全て名前付き・上書き可能 = 査読で「なぜこの値?」に答えられる)。
DEFAULT_REMEASURE_ROUNDS = 3        # 収束しなければ unstable とするまでの最大測定回数 (§3.6(2))
DEFAULT_ALPHA = 0.05               # 分布比較の有意水準 (§3.6(4))


# ============================================================
# (2) 外れ値 → 自動再測定
# ============================================================

@dataclass
class RemeasureResult:
    """自動再測定の結果。`point` は採用した測定 (= 最も CV が低いラウンド)。"""
    point: object = None                  # 採用した測定点 (.throughputs を持つ ScalePoint 等)
    nf: Optional[NoiseFloor] = None       # 採用測定の noise_floor
    rounds: int = 0                       # 実際に測定した回数
    stable: bool = False                  # あるラウンドで CV <= 閾値 を達成した
    unstable: bool = False                # 規定ラウンドで収束しなかった (= not stable)
    cv_history: List[Optional[float]] = field(default_factory=list)   # 各ラウンドの CV


def _cv_is_better(new: Optional[float], cur: Optional[float]) -> bool:
    """より信用できる CV か。実数 CV は None (算出不能) に勝ち、低いほど勝つ。"""
    if new is None:
        return False
    return cur is None or new < cur


def remeasure_until_stable(
        measure_fn: Callable[[], object],
        settle_fn: Optional[Callable[[], None]] = None,
        cv_threshold: float = DEFAULT_NOISE_CV,
        max_rounds: int = DEFAULT_REMEASURE_ROUNDS) -> RemeasureResult:
    """反復内 CV が閾値を超えたら静定して測り直す (§3.6(2))。

    各ラウンドは `measure_fn()` を 1 回呼ぶ (= reps 反復を内包した 1 測定点)。その CV が
    `cv_threshold` 以下なら収束として打ち切る。収束しないまま `max_rounds` を使い切ったら
    `unstable=True`。採用する測定点は **最も CV が低かったラウンド** (収束したならその点)。

    2 ラウンド目以降は再測定の前に `settle_fn()` を呼ぶ (騒がしかったので静定し直す)。
    1 ラウンド目の静定は呼び手 (campaign 冒頭) が済ませている前提なので呼ばない。
    """
    history: List[Optional[float]] = []
    best_pt = None
    best_nf: Optional[NoiseFloor] = None
    rounds = 0
    while rounds < max_rounds:
        if rounds > 0 and settle_fn is not None:
            settle_fn()                              # 騒がしかった → 静定してから測り直す
        pt = measure_fn()
        rounds += 1
        nf = noise_floor(pt.throughputs, cv_threshold)
        history.append(nf.cv)
        if best_nf is None or _cv_is_better(nf.cv, best_nf.cv):
            best_pt, best_nf = pt, nf
        if nf.cv is not None and nf.cv <= cv_threshold:
            break                                    # 収束 = これ以上測り直さない
    stable = (best_nf is not None and best_nf.cv is not None
              and best_nf.cv <= cv_threshold)
    return RemeasureResult(point=best_pt, nf=best_nf, rounds=rounds,
                           stable=stable, unstable=not stable, cv_history=history)


# ============================================================
# (4) 採否は分布比較 (Mann-Whitney U, 正規近似)
# ============================================================

def _average_ranks(values: Sequence[float]) -> List[float]:
    """tie には平均順位を与える (1 始まり)。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0                    # ranks[i..j] の平均 (1 始まり)
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def mann_whitney_u(a: Sequence[float],
                   b: Sequence[float]) -> Tuple[Optional[float], float]:
    """両側 Mann-Whitney U 検定 (正規近似 + tie 補正 + 連続補正)。`(U, p)` を返す。

    重い統計機構を避けるための軽量実装 (roadmap §3.6(4)「重い統計機構は不要」)。reps が小さい
    (5 程度) と正規近似の p は粗いので、第一ゲートの noise-floor 丸め (`compare`) を主役にし、
    本検定は noise floor を超えた差にだけ二次的に当てる。サンプルが空なら `(None, 1.0)`。
    """
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return None, 1.0
    n = n1 + n2
    ranks = _average_ranks(list(a) + list(b))
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    u_min = min(u1, u2)
    mu = n1 * n2 / 2.0

    # tie 補正項: Σ(t^3 - t) を全 tie group で。
    tie_term = 0.0
    sv = sorted(list(a) + list(b))
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    var_u = (n1 * n2 / 12.0) * ((n + 1) - tie_term / (n * (n - 1)))
    if var_u <= 0:                                   # 全点同値など → 差なし
        return u_min, 1.0
    sigma = math.sqrt(var_u)
    z = (abs(u1 - mu) - 0.5) / sigma                 # 連続補正
    if z < 0:
        z = 0.0
    p = 1.0 - math.erf(z / math.sqrt(2.0))           # = 2*(1 - Φ(z)), 両側
    return u_min, max(0.0, min(1.0, p))


@dataclass
class Comparison:
    """variant と baseline の throughput 分布の比較結果。"""
    verdict: str = "indeterminate"        # faster / slower / no-difference / indeterminate
    rel_median: Optional[float] = None    # (med_variant - med_base) / med_base (符号付き)
    u: Optional[float] = None             # Mann-Whitney U (noise floor を超えた時のみ算出)
    p: Optional[float] = None             # 両側 p 値
    median_base: Optional[float] = None
    median_variant: Optional[float] = None
    reason: str = ""


def compare(baseline: Sequence[Optional[float]],
            variant: Sequence[Optional[float]],
            noise_cv: float = DEFAULT_NOISE_CV,
            alpha: float = DEFAULT_ALPHA) -> Comparison:
    """variant の throughput 分布を baseline と比較し採否判定の材料を返す (§3.6(4))。

    手順: (1) noise floor 以下の中央値差は「差なし」に丸める (信用してよい差の下限、§3.6(3))。
    (2) 超える差にだけ Mann-Whitney U を当て、有意なら faster/slower、有意でなければ no-difference。

    **unstable な variant はこの比較に渡す前に呼び手が除外すること** (沈黙して 1 点を採用しない、
    §3.6(4))。サンプルが空なら indeterminate。
    """
    xb = [x for x in baseline if x is not None]
    xv = [x for x in variant if x is not None]
    if not xb or not xv:
        return Comparison(verdict="indeterminate", reason="throughput サンプルが不足")

    med_b = statistics.median(xb)
    med_v = statistics.median(xv)
    rel = (med_v - med_b) / med_b if med_b else None
    c = Comparison(rel_median=rel, median_base=med_b, median_variant=med_v)

    # (1) noise floor 以下 → 差なしに丸める。
    if rel is not None and abs(rel) <= noise_cv:
        c.verdict = "no-difference"
        c.reason = (f"中央値差 {rel * 100:+.2f}% が noise floor {noise_cv * 100:.1f}% 以下 "
                    "→ 信用できる差ではない")
        return c

    # (2) noise floor 超 → Mann-Whitney U で有意性判定。
    u, p = mann_whitney_u(xv, xb)
    c.u, c.p = u, p
    if p < alpha:
        c.verdict = "faster" if (rel or 0) > 0 else "slower"
        c.reason = (f"中央値差 {rel * 100:+.2f}% (noise floor 超) かつ "
                    f"Mann-Whitney p={p:.3f} < {alpha} で有意")
    else:
        c.verdict = "no-difference"
        c.reason = (f"中央値差 {rel * 100:+.2f}% は noise floor 超だが "
                    f"Mann-Whitney p={p:.3f} >= {alpha} で有意でない")
    return c
