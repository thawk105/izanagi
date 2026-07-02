# -*- coding: utf-8 -*-
"""測定安定性 (roadmap §3.6 の (2)(4))。純関数 + callable 注入 = machine に触れずモックでテスト可能。

Phase 1 で配線済みの (1)(3) (noise floor + 反復中央値・CV、`analyze.noise_floor`) の上に積む:

- **(2) 外れ値 → 自動再測定** (`remeasure_until_stable`): 反復内 CV が閾値を超えたら静定して
  測り直す。規定ラウンドで収束しなければ `unstable`。`measure_fn`/`settle_fn` を注入する
  ので、実ベンチを回さずにモックでテストできる (実走は pipeline が bench_lock 下=直列で行う、
  絶対規律4)。
- **(3') between-run noise floor** (`between_run_noise_floor`): 独立セッション間の session-median
  の CV = **差が信用できるかの下限** (compare の丸め閾値)。within-run noise floor (= その 1 測定の
  品質) と用途が違う: variant と baseline は別 run で測るので採否の floor は between-run であるべき
  (within-run を流用すると偽 faster を出す。これが A2 で塞いだ穴)。callable 注入でテスト可。
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
from .model import BetweenRunNoiseFloor, NoiseFloor


# 既定の閾値 (全て名前付き・上書き可能 = 査読で「なぜこの値?」に答えられる)。
DEFAULT_REMEASURE_ROUNDS = 3        # 収束しなければ unstable とするまでの最大測定回数 (§3.6(2))
DEFAULT_ALPHA = 0.05               # 分布比較の有意水準 (§3.6(4))
DEFAULT_BETWEEN_RUN_SESSIONS = 8    # between-run CV の推定に使う独立セッション数 (§3.6(3))
DEFAULT_NEAR_FLOOR_MARGIN = 1.5    # 差がこの倍率×floor 以内なら floor 近傍とフラグ (§3.6(4))


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
# (3') between-run noise floor (差が信用できるかの下限)
# ============================================================

def between_run_noise_floor(
        measure_fn: Callable[[], Optional[float]],
        settle_fn: Optional[Callable[[], None]] = None,
        sessions: int = DEFAULT_BETWEEN_RUN_SESSIONS,
        cv_threshold: float = DEFAULT_NOISE_CV) -> BetweenRunNoiseFloor:
    """独立な測定セッションを sessions 回回し、各セッションの代表 throughput の CV を出す。

    within-run noise floor (`noise_floor`: 1 セッション内 N rep の散らばり=その測定の品質,
    `remeasure_until_stable` の品質ゲート) と用途が違う: これは N 個の**独立セッション**
    (各 = measure_fn() 1 回 = 完全な 1 測定点。reps を内包し median を返す) の session-median
    の散らばり = **差が信用できるかの下限** (compare の丸め閾値, roadmap §3.6(4))。variant と
    baseline は決して同一セッションで測らないので、この between-run CV が信用できる差の下限。

    2 回目以降は前に settle_fn() を呼ぶ — ただしこれは **admission** (他テナント混入の検出。
    driver は lag-free な競合検知 competing_bench_pids を注入する) であって between-run 独立性の
    確保ではない (settle = load EMA は連続 run 間で残像でほぼ即 return し独立性を足さない)。
    よって本関数が返すのは fresh な same-window の between-run CV = cold-boot/温度ドリフトを
    含まない **下限** であり、wired する floor は cross-campaign の genuine な between データと
    突き合わせ保守側に採ること (`BetweenRunNoiseFloor` の docstring・worklog 2026-06-28)。

    measure_fn/settle_fn を注入するので machine に触れずモックでテストできる (実走は driver が
    bench_lock 下=直列で行う, 絶対規律4)。measure_fn が None を返した (測定不能) セッションは除外。
    """
    series: List[float] = []
    for i in range(sessions):
        if i > 0 and settle_fn is not None:
            settle_fn()                              # admission (独立性ではない)
        tps = measure_fn()
        if tps is not None:
            series.append(tps)

    nf = noise_floor(series, cv_threshold)           # session 列の分布要約を再利用
    out = BetweenRunNoiseFloor(
        session_throughputs=series, sessions=len(series),
        cv=nf.cv, mean=nf.mean, median=nf.median, stdev=nf.stdev,
        high_variance=nf.high_variance)
    if len(series) < 2 or nf.cv is None:
        out.notes.append("独立セッションが 2 未満か CV 算出不能 (mean=0 等)。"
                         "between-run CV は使えない (最低 2 セッション + 非ゼロ tps)")
    else:
        out.notes.append(
            f"between-run CV {nf.cv*100:.2f}% = {len(series)} 独立セッションの session-median の"
            "散らばり。settle は admission (独立性でない) ため cold-boot/温度ドリフト未含 = 下限。"
            "high-abort genome はこれを上回りうる → cross-campaign データと突き合わせ保守側に採れ")
        if nf.high_variance:
            out.notes.append(
                f"between-run CV {nf.cv*100:.2f}% が許容上限 {cv_threshold*100:.1f}% 超。"
                "外乱混入か独立セッション間ドリフトが大きい (動作点/genome を疑え)")
    return out


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
    near_floor: bool = False              # faster/slower だが差が floor 近傍
                                          # (floor < |rel| <= margin*floor) → cross-run 再現で裏取り要
    reason: str = ""


def compare(baseline: Sequence[Optional[float]],
            variant: Sequence[Optional[float]],
            noise_cv: float = DEFAULT_NOISE_CV,
            alpha: float = DEFAULT_ALPHA,
            near_floor_margin: float = DEFAULT_NEAR_FLOOR_MARGIN) -> Comparison:
    """variant の throughput 分布を baseline と比較し採否判定の材料を返す (§3.6(4))。

    手順: (1) noise floor 以下の中央値差は「差なし」に丸める (信用してよい差の下限)。
    (2) 超える差にだけ Mann-Whitney U を当て、有意なら faster/slower、有意でなければ no-difference。

    **noise_cv は between-run noise floor を渡すこと** (`between_run_noise_floor`)。variant と
    baseline は別 run/別ビルドで測るので、信用できる差の下限は within-run でなく between-run
    (within-run を渡すと between-run ドリフト帯の差を『超』と誤判定し偽 faster を出す — これが
    A2 で塞いだ穴)。within-run noise floor は別関心 (1 測定の品質 = remeasure 品質ゲート)。

    **統計的な意味の注意 (洗練検査 2026-07-02):** CV は 1 測定 (session-median) の散らばりで
    あり、独立 2 測定の**差**の標準偏差は √2×CV。よって Gate1 の |rel| <= noise_cv は差分布の
    約 0.71σ でしか丸めておらず、「floor 超 = 信用できる差」は √2 分過小な謳い (真に差が
    なくても floor を超える確率が残る)。wired 3.0% は観測最悪 2.91% への保守丸めで write-heavy
    帯では偶然ほぼ 1σ_Δ 相当になっており、P2-2 の実データには √2 補正で verdict が変わる比較は
    存在しない (既存結論は不変)。Phase 3 で閾値意味論を √2 補正するかは設計判断として保留 —
    それまで near_floor 帯 (floor〜1.5×floor) の faster/slower を headline にしない運用を厳守。

    **Gate2 (Mann-Whitney) の弁別力は弱い**: reps が小さい (5 程度) と完全分離は常に p≈0.012 を
    返す (正規近似)。よって Gate2 は between-run 有意性検定でも fluky-rep 対策でもなく
    (median は外れ rep にロバスト)、within-run の分布重なり (partial overlap) を二次的に弾く
    弱い sanity にすぎない。**主防壁は Gate1 (between-run floor 丸め)**。Gate1 を僅かに超えた
    faster/slower は Gate2 が無力なので `near_floor` を立てる — headline にする前に cross-run
    再現 (backoff_repro 方式) で裏取りすること (現 repro は同一 boot・対象限定なので別 boot/
    rounds≥3 への拡張が将来必要)。

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

    # baseline median が 0/欠損 → 相対差を定義できない。Gate2 に落とすと faster/slower 分岐の
    # rel*100 が None で落ちるので、ここで indeterminate を返す (0 tps を WAL に書く crash genome 等)。
    if rel is None:
        c.verdict = "indeterminate"
        c.reason = "baseline median が 0 で相対差を定義できない"
        return c

    # (1) between-run noise floor 以下 → 差なしに丸める (主防壁)。
    if rel is not None and abs(rel) <= noise_cv:
        c.verdict = "no-difference"
        c.reason = (f"中央値差 {rel * 100:+.2f}% が between-run noise floor "
                    f"{noise_cv * 100:.1f}% 以下 → 信用できる差ではない")
        return c

    # (2) floor 超 → Mann-Whitney U (within-run 分布の弱い sanity)。
    u, p = mann_whitney_u(xv, xb)
    c.u, c.p = u, p
    if p < alpha:
        c.verdict = "faster" if (rel or 0) > 0 else "slower"
        c.reason = (f"中央値差 {rel * 100:+.2f}% (floor 超) かつ "
                    f"Mann-Whitney p={p:.3f} < {alpha} で有意")
        # floor 近傍 (Gate2 が無力な帯) → cross-run 再現で裏取り要のフラグを立てる。
        if rel is not None and abs(rel) <= near_floor_margin * noise_cv:
            c.near_floor = True
            c.reason += (f" — ただし差は floor の {near_floor_margin:g} 倍 "
                         f"({near_floor_margin * noise_cv * 100:.1f}%) 以内 (floor 近傍) "
                         "なので cross-run 再現で裏取り要")
    else:
        c.verdict = "no-difference"
        c.reason = (f"中央値差 {rel * 100:+.2f}% は floor 超だが "
                    f"Mann-Whitney p={p:.3f} >= {alpha} で有意でない")
    return c
