# -*- coding: utf-8 -*-
"""P2-5 ベースライン: ランダム探索 (解析+経験) / critic 無し貪欲 / オラクル天井。

LLM を一切呼ばず、replay (P2-2 WAL の記録値) の上で「最適到達までの評価本数」を測る。
P2-5 の negative result の主柱: silo 8 のような 1 ビットで割れる小空間では、逐次帰属に
到達速度の優位はほぼ無いことを、LLM の揺れを挟まずに確定させる。

系列:
- **random** — 8 genome をランダム順に 1 本ずつ。winner-tied set 初到達位置の分布。
  解析分布 P(初到達=j)=C(N-j,k-1)/C(N,k)、期待値 (N+1)/(k+1)。経験分布 (K seed) は sanity。
- **critic-free greedy** (規律5 ablation の核心) — LLM を呼ばず digest.axis_effects の
  限界効果だけで未評価候補から最良勾配方向を貪欲選択。「この空間は LLM critic を要するか」を
  測る対照。greedy が random を大きく上回れば優位は digest 整形由来 (LLM 不要)、上回らねば
  そもそも空間に優位の余地が無い。seed 依存なので K trial の分布。
- **oracle 天井** — 強制ランダム初手 (誘導も初手は critic 信号なし) の後、2 手目で必ず
  tied に当てる完全知 = E[到達]=2-k/N。「どんなに賢い critic でも初手ランダム制約下で
  これ以上速くならない」上限。実 critic/greedy がこの天井のどこに落ちるかで over-claim を防ぐ。

主指標は生の到達本数でなく **確率優越** P(戦略 < random) + 効果量 (本数差)。
"""
from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass, field
from math import comb
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import replay                                       # noqa: E402
from campaign.genome import SILO_SPACE                            # noqa: E402
from campaign.model import Genome                                 # noqa: E402
from campaign.p2_2 import BETWEEN_RUN_CV, WORKLOADS               # noqa: E402
from critic import digest                                        # noqa: E402

_AXES = ["BACK_OFF", "no_wait", "WAL"]


# ============================================================
# 到達コスト (全戦略で共通定義 = winner-tied set 初到達位置)
# ============================================================

def reached_cost(order: List[str], tied: set) -> int:
    """評価順 order (canonical のリスト) で tied set に初到達した 1-based 位置。

    全戦略 (random/greedy/guided/enumerate) でこの 1 つの定義に統一する (二重定義を作らない)。
    order を最後まで見ても当たらなければ len(order) (= 予算上限 N、最悪値) を返す。"""
    for i, g in enumerate(order, start=1):
        if g in tied:
            return i
    return len(order)


# ============================================================
# random (解析分布 + 経験分布)
# ============================================================

def random_reach_distribution(n: int, k: int) -> Dict[int, float]:
    """ランダム順での winner-tied set 初到達位置の厳密分布。

    N 個中 k 個が tied (成功)。P(初到達=j) = C(N-j, k-1) / C(N, k) (j=1..N-k+1)。"""
    if k <= 0 or k > n:
        raise ValueError(f"k={k} は 1..N={n} の範囲外")
    return {j: comb(n - j, k - 1) / comb(n, k) for j in range(1, n - k + 2)}


def expectation(dist: Dict[int, float]) -> float:
    return sum(j * p for j, p in dist.items())


def random_reach_empirical(genomes: List[str], tied: set, k_trials: int,
                           seed0: int = 0) -> List[int]:
    """K 個の seed でランダム順をシャッフルし到達本数の経験分布 (解析の sanity 用)。"""
    out = []
    for s in range(k_trials):
        rng = random.Random(seed0 * 100003 + s)
        order = list(genomes)
        rng.shuffle(order)
        out.append(reached_cost(order, tied))
    return out


# ============================================================
# critic-free greedy (digest 限界効果のみ、LLM なし)
# ============================================================

def _axis_prefs(evaluated: List[replay.GenomeResult]) -> Dict[str, Tuple[str, float]]:
    """評価済み部分集合から各軸の選好水準 (throughput 高い方) と重み (|相対差|) を出す。

    digest.axis_effects (他フラグで周辺化した水準別平均) をそのまま使う = この greedy は
    『digest が機械的に提示する勾配』そのもの。2 水準揃った軸だけ選好を持つ。"""
    lis = [digest.GenomeLI(genome=r.genome, flags=r.flags, li=r.leading_indicators)
           for r in evaluated]
    prefs: Dict[str, Tuple[str, float]] = {}
    for a in _AXES:
        eff = digest.axis_effects(lis, a)
        tp = eff.means.get("throughput_tps", {})
        if len(tp) >= 2:
            best = max(tp, key=lambda lv: tp[lv])
            w = abs(eff.rel_throughput) if eff.rel_throughput is not None else 0.0
            prefs[a] = (best, w)
    return prefs


def _greedy_next(evaluated: List[replay.GenomeResult], candidates: List[Genome],
                 rng: random.Random) -> Genome:
    """評価済みから勾配を読み、未評価候補の中で選好に最も適合する genome を選ぶ。

    選好がまだ無い (軸が 1 水準しか観測されていない初期) なら探索としてランダム選択。"""
    prefs = _axis_prefs(evaluated)
    if not prefs:
        return rng.choice(candidates)

    def score(g: Genome) -> float:
        gli = digest.GenomeLI(genome=g.canonical(), flags=g.flags, li={})
        return sum(w for a, (lvl, w) in prefs.items() if gli.axis_value(a) == lvl)

    best = max(score(g) for g in candidates)
    top = [g for g in candidates if score(g) == best]
    return rng.choice(top)


def greedy_reach(landscape: Dict[str, replay.GenomeResult], tied: set,
                 k_trials: int, seed0: int = 0) -> List[int]:
    """critic-free greedy を K seed で回し到達本数の経験分布を返す。

    各 trial: seed でランダム初手 → 以降 digest 勾配で貪欲選択 → tied 到達で停止。
    初手は critic 信号なしなのでランダム (誘導も初手はランダム = 公平)。"""
    all_genomes = SILO_SPACE.enumerate()
    out = []
    for s in range(k_trials):
        rng = random.Random(seed0 * 100019 + s)
        evaluated: List[replay.GenomeResult] = []
        order: List[str] = []
        remaining = list(all_genomes)
        # 初手 = ランダム
        first = rng.choice(remaining)
        while True:
            g = first if not order else _greedy_next(evaluated, remaining, rng)
            remaining = [x for x in remaining if x.canonical() != g.canonical()]
            res = replay.replay_evaluate(landscape, g)
            evaluated.append(res)
            order.append(g.canonical())
            if g.canonical() in tied or not remaining:
                break
        out.append(reached_cost(order, tied))
    return out


# ============================================================
# oracle 天井 (強制ランダム初手 + 完全知で 2 手目到達)
# ============================================================

def oracle_ceiling(n: int, k: int) -> float:
    """初手ランダム制約下で到達本数の理論下限 = E = 2 - k/N。

    初手が tied (確率 k/N) なら 1 本、外せば完全知で 2 本目に必ず当てる。
    『どんな critic も初手ランダムならこれ以上速くできない』天井。"""
    return 2.0 - k / n


# ============================================================
# 確率優越 (主指標)
# ============================================================

def prob_superiority(strategy_costs: List[int],
                     random_dist: Dict[int, float]) -> Dict[str, float]:
    """P(戦略 < random) と P(戦略 <= random) を解析 random 分布に対して計算。

    戦略の各 trial コスト c に対し P(random > c) と P(random >= c) を解析分布から取り平均。
    0.5 が『差なし』。0.5 を有意に超えて初めて『戦略が速い』と言える。"""
    if not strategy_costs:
        return {"p_lt": float("nan"), "p_le": float("nan")}
    p_gt = lambda c: sum(p for j, p in random_dist.items() if j > c)   # noqa: E731
    p_ge = lambda c: sum(p for j, p in random_dist.items() if j >= c)  # noqa: E731
    lt = sum(p_gt(c) for c in strategy_costs) / len(strategy_costs)
    le = sum(p_ge(c) for c in strategy_costs) / len(strategy_costs)
    return {"p_lt": lt, "p_le": le}


def _summ(costs: List[int]) -> Dict[str, float]:
    import statistics
    cs = sorted(costs)
    n = len(cs)
    q1 = cs[n // 4]
    q3 = cs[min(n - 1, (3 * n) // 4)]
    return {"mean": statistics.mean(cs), "median": statistics.median(cs),
            "min": cs[0], "max": cs[-1], "iqr_lo": q1, "iqr_hi": q3}


@dataclass
class WorkloadBaselines:
    tag: str
    n: int
    k: int
    tied_labels: List[str]
    random_dist: Dict[int, float]
    random_E: float
    random_emp_E: float
    greedy_costs: List[int] = field(default_factory=list)
    oracle_E: float = 0.0


def run_workload(tag: str, k_trials: int = 200, seed0: int = 0) -> WorkloadBaselines:
    lscape = replay.load_landscape(tag)
    replay.assert_complete(lscape, tag)
    tied = replay.winner_tied_set(lscape, BETWEEN_RUN_CV)
    genomes = [g.canonical() for g in SILO_SPACE.enumerate()]
    n, k = len(genomes), len(tied)
    dist = random_reach_distribution(n, k)
    emp = random_reach_empirical(genomes, tied, k_trials, seed0)
    greedy = greedy_reach(lscape, tied, k_trials, seed0)
    return WorkloadBaselines(
        tag=tag, n=n, k=k,
        tied_labels=sorted(replay.genome_label(lscape[g].flags) for g in tied),
        random_dist=dist, random_E=expectation(dist),
        random_emp_E=sum(emp) / len(emp),
        greedy_costs=greedy, oracle_E=oracle_ceiling(n, k))


def main(argv) -> int:
    import statistics
    k_trials = int(argv[1]) if len(argv) > 1 else 200
    print(f"# P2-5 search baselines (replay, LLM なし, K={k_trials} trial, "
          f"floor {BETWEEN_RUN_CV*100:.1f}%)\n")
    for tag, _wl in WORKLOADS:
        b = run_workload(tag, k_trials)
        gs = _summ(b.greedy_costs)
        ps = prob_superiority(b.greedy_costs, b.random_dist)
        print(f"== {tag}  (N={b.n}, winner-tied k={b.k} {b.tied_labels}) ==")
        print(f"  random      : E={b.random_E:.2f} 本 (解析)  / 経験 E={b.random_emp_E:.2f}")
        print(f"  oracle 天井 : E={b.oracle_E:.2f} 本 (初手ランダム制約下の理論下限)")
        print(f"  greedy      : 中央値={gs['median']:.0f} 平均={gs['mean']:.2f} "
              f"IQR=[{gs['iqr_lo']:.0f},{gs['iqr_hi']:.0f}] min={gs['min']} max={gs['max']}")
        print(f"  P(greedy<random)={ps['p_lt']:.3f}  P(greedy<=random)={ps['p_le']:.3f}  "
              f"(0.5=差なし)")
        adv = b.random_E - gs['mean']
        print(f"  → greedy の平均削減 = {adv:+.2f} 本 / oracle 天井の削減 = "
              f"{b.random_E - b.oracle_E:+.2f} 本\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
