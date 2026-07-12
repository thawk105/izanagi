#!/usr/bin/env python3
"""s6_proposal_rounds_power — D52 提案ラウンド束 (S-2/C4/C5) の n 確定用の厳密検定力計算。

Fisher 正確検定 (片側、本アーム適格率 > 対照) の検定力を、依存ライブラリなしで
全数総和により厳密計算する (scipy 非依存 — math.comb のみ)。
正本 = docs/phase3-main-experiment.md 2026-07-12 追記の「n = 20/アーム基準」の
着手時確定 (2026-07-13 追記)。

用法: python3 s6_proposal_rounds_power.py
"""

from math import comb


def fisher_one_sided_p(x1: int, x2: int, n1: int, n2: int) -> float:
    """片側 (group1 > group2) の Fisher 正確 p 値。
    条件付き超幾何: P(X1 >= x1 | X1 + X2 = k)。"""
    k = x1 + x2
    denom = comb(n1 + n2, k)
    hi = min(k, n1)
    return sum(comb(n1, i) * comb(n2, k - i) for i in range(x1, hi + 1)) / denom


def binom_pmf(n: int, p: float, x: int) -> float:
    return comb(n, x) * p**x * (1 - p) ** (n - x)


def power(
    n: int, p1: float, p2: float, alpha: float, floor_count: "int | None" = None
) -> float:
    """真の率 (p1, p2) の下で成功条件を満たす確率 (厳密・全数総和)。
    成功条件 = 片側 Fisher p <= alpha、floor_count 指定時はさらに x1 >= floor_count
    (適格率の絶対下限、2026-07-13 着手時確定の連言) との連言。"""
    pm1 = [binom_pmf(n, p1, x) for x in range(n + 1)]
    pm2 = [binom_pmf(n, p2, x) for x in range(n + 1)]
    total = 0.0
    for x1 in range(n + 1):
        if floor_count is not None and x1 < floor_count:
            continue
        for x2 in range(n + 1):
            if fisher_one_sided_p(x1, x2, n, n) <= alpha:
                total += pm1[x1] * pm2[x2]
    return total


def main() -> None:
    alpha = 0.0125  # Holm 初段 (族 4: S-1a / S-1b / S-2 / S-3) = 0.05 / 4
    print("== n グリッド: p1=0.6 vs p2=0.1, alpha=0.0125 片側 (Fisher 単独) ==")
    for n in (10, 12, 14, 15, 16, 18, 19, 20, 22, 25, 30, 40):
        print(f"n={n:3d}/arm  power={power(n, 0.6, 0.1, alpha):.4f}")
    print()
    print("== 成功条件の連言 (Fisher かつ 本アーム >= 10/20 = 適格率下限 0.5), n=20 ==")
    print(f"連言 power = {power(20, 0.6, 0.1, alpha, floor_count=10):.4f}"
          f" (Fisher 単独 {power(20, 0.6, 0.1, alpha):.4f})")
    print()
    print("== 感度 (n=20, 連言): 効果量仮定が外れた場合 ==")
    for p1, p2 in ((0.5, 0.1), (0.6, 0.2), (0.5, 0.2), (0.4, 0.1), (0.6, 0.3)):
        print(f"p1={p1} p2={p2}  power={power(20, p1, p2, alpha, floor_count=10):.4f}")
    print()
    print("== 参考: C4 が強対照 (0.6 vs 0.3) のとき n を倍にしても ==")
    print(f"n=40 連言 (floor 20/40) = {power(40, 0.6, 0.3, alpha, floor_count=20):.4f}")


if __name__ == "__main__":
    main()
