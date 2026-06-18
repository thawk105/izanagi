# -*- coding: utf-8 -*-
"""校正の判定ロジック (純関数。machine に触れない=モックでテストできる)。

3 つ:
- `find_saturation` — 倍々スイープの miss 率系列から「採用すべき最小レコード数」。
- `scale_sensitivity` — small/medium 2 点でのスケール効率 (頭打ち検出の枠組み)。
- `noise_floor` — 反復 throughput のばらつき (信用してよい差の下限)。

roadmap §4 / §3.6 と calibrator.md の規律に対応。
"""
from __future__ import annotations

import statistics
from typing import List, Optional

from .model import NoiseFloor, ScalePoint, ScaleSensitivity, SaturationResult


# 既定の閾値。査読で「なぜこの値?」に答えられるよう全て名前付き・上書き可能。
DEFAULT_SATURATION_DELTA = 0.01     # miss 率 (0..1) の絶対変化。1 ポイント未満で飽和
DEFAULT_CACHE_FLOOR = 0.005         # 採用点 miss 率がこれ未満=working set が cache に乗る疑い
DEFAULT_NOISE_CV = 0.05             # CV がこれを超えたら「騒がしい」(roadmap §3.6(2))
DEFAULT_SCALE_EFF = 0.70            # per-thread 効率比がこれ未満で scale-suspect


def find_saturation(points: List[ScalePoint],
                    threshold: float = DEFAULT_SATURATION_DELTA,
                    cache_floor: float = DEFAULT_CACHE_FLOOR) -> SaturationResult:
    """倍々スイープから飽和レコード数を決める。

    判定: 「ここから先、どれだけ倍にしても miss 率が threshold 未満しか動かない」
    最小レコード数を採る (roadmap §4)。単なる「次の 1 ステップが平ら」では
    途中の noise dip に騙されるので、**採用点から末尾までの全ステップが平ら**
    であることを要求する (= 非単調系列への頑健化)。

    範囲内で飽和しなければ saturated=False とし、測定した最大点を安全側として
    返す (スイープを延ばす必要があるという notes 付き)。
    """
    usable = [p for p in points if p.miss_rate is not None]
    res = SaturationResult(records=0, saturated=False, threshold=threshold)

    if len(points) != len(usable):
        res.notes.append(
            f"{len(points) - len(usable)} 点で miss 率が欠損 (perf カウンタ取得失敗) → 除外")
    if not usable:
        res.notes.append("有効な測定点が無い。飽和判定不能")
        return res

    usable = sorted(usable, key=lambda p: p.records)
    res.series = [
        {"records": float(p.records), "miss_rate": float(p.miss_rate)}
        for p in usable
    ]
    # 隣接デルタを series に添える (provenance)
    for i in range(1, len(usable)):
        res.series[i]["delta"] = usable[i].miss_rate - usable[i - 1].miss_rate

    if len(usable) == 1:
        p = usable[0]
        res.records = p.records
        res.saturated = False
        res.miss_rate_at = p.miss_rate
        res.notes.append("測定点が 1 つのみ。飽和は確認できない (最低 2 点必要)")
        _flag_cache_floor(res, p.miss_rate, cache_floor)
        return res

    # 採用点 i: i→末尾の全ステップ |Δ| < threshold を満たす最小の i。
    # 最終点 (n-1) は後続が無く「平ら」を確認できないので候補から外す
    # (空の tail を平らと誤認すると、飽和していなくても最大点を saturated に
    # してしまう)。よって i は range(n-1) まで。
    n = len(usable)
    chosen: Optional[int] = None
    for i in range(n - 1):
        flat = True
        for j in range(i + 1, n):
            if abs(usable[j].miss_rate - usable[j - 1].miss_rate) >= threshold:
                flat = False
                break
        if flat:
            chosen = i
            break

    if chosen is None:
        # 末尾まで平らにならなかった = 範囲内で飽和せず。
        p = usable[-1]
        res.records = p.records
        res.saturated = False
        res.miss_rate_at = p.miss_rate
        res.notes.append(
            "測定範囲内で miss 率が飽和しなかった。スイープを上に延ばすべき "
            "(採用値は暫定の最大点)")
        _flag_cache_floor(res, p.miss_rate, cache_floor)
        return res

    p = usable[chosen]
    res.records = p.records
    res.saturated = True
    res.miss_rate_at = p.miss_rate
    if chosen == 0:
        res.notes.append(
            "最小点で既に飽和。下限 (cache 競合再現) の確認のため "
            "cache_floor 警告も参照のこと")
    _flag_cache_floor(res, p.miss_rate, cache_floor)
    return res


def _flag_cache_floor(res: SaturationResult, miss_rate: float, floor: float) -> None:
    """採用点の miss 率が低すぎる = working set が cache に乗り many-core の
    cache 競合が再現されない疑い (calibrator.md の下限の罠)。"""
    if miss_rate < floor:
        res.cache_floor_warning = True
        res.notes.append(
            f"採用点の LLC miss 率 {miss_rate*100:.3f}% が下限 {floor*100:.2f}% "
            "未満。working set が cache に収まり、many-core の cache 競合が "
            "再現されない恐れ (測定が楽観的に歪む)。レコード数の下げ過ぎを疑え")


def scale_sensitivity(small: ScalePoint, medium: ScalePoint,
                      eff_threshold: float = DEFAULT_SCALE_EFF) -> ScaleSensitivity:
    """small/medium 2 点の per-thread 効率からスケールの伸び方を特徴量化する。

    Phase 1 では枠組み。per-thread throughput (= tps/threads) の medium/small 比を
    効率比とし、閾値未満なら scale-suspect。これは後の Phase 2 で variant 比較に
    使う (small で良いのに medium で頭打ちの variant を最終選択から外す材料)。
    """
    out = ScaleSensitivity(small=small, medium=medium)
    st, mt = small.throughput, medium.throughput
    if st is not None and small.threads:
        out.small_per_thread = st / small.threads
    if mt is not None and medium.threads:
        out.medium_per_thread = mt / medium.threads

    if out.small_per_thread and out.medium_per_thread:
        out.efficiency_ratio = out.medium_per_thread / out.small_per_thread
        if out.efficiency_ratio < eff_threshold:
            out.scale_suspect = True
            out.notes.append(
                f"per-thread 効率が small→medium で {out.efficiency_ratio:.2f} 倍 "
                f"(<{eff_threshold}) に低下。スケール頭打ちの疑い")
    else:
        out.notes.append("throughput 欠損のため効率比を計算できない")
    return out


def noise_floor(throughputs: List[float],
                cv_threshold: float = DEFAULT_NOISE_CV) -> NoiseFloor:
    """確定条件での反復 throughput からばらつき (CV) を出す (roadmap §3.6(3))。

    CV = stdev/mean が「この差以下は信用するな」の下限。cv_threshold を超えたら
    high_variance (環境が騒がしい/再測定が要る)。
    """
    out = NoiseFloor(throughputs=list(throughputs))
    xs = [x for x in throughputs if x is not None]
    if not xs:
        out.notes.append("throughput サンプルが無い")
        return out
    out.mean = statistics.fmean(xs)
    out.median = statistics.median(xs)
    if len(xs) >= 2:
        out.stdev = statistics.stdev(xs)        # 標本標準偏差 (n-1)
        out.cv = (out.stdev / out.mean) if out.mean else None
    else:
        out.notes.append("サンプルが 1 点のみ。CV は算出不能 (最低 2 run 必要)")
    if out.cv is not None and out.cv > cv_threshold:
        out.high_variance = True
        out.notes.append(
            f"CV {out.cv*100:.2f}% が許容上限 {cv_threshold*100:.1f}% 超。"
            "測定が外乱で歪んでいる疑い (静定確認の上で再測定すべき)")
    return out
