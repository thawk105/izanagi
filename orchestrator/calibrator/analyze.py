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
DEFAULT_L3_MULTIPLE = 4.0           # 下限基準: working set が L3 をこの倍超える最小 N


def find_saturation(points: List[ScalePoint],
                    threshold: float = DEFAULT_SATURATION_DELTA,
                    cache_floor: float = DEFAULT_CACHE_FLOOR,
                    l3_bytes: Optional[int] = None,
                    l3_multiple: float = DEFAULT_L3_MULTIPLE) -> SaturationResult:
    """倍々スイープから採用レコード数を決める。

    第一基準 = **飽和点** (roadmap §4): 「ここから先どれだけ倍にしても miss 率が
    threshold 未満しか動かない」最小 N。単なる「次の 1 ステップが平ら」では途中の
    noise dip に騙されるので、**採用点から末尾まで全ステップが平ら**を要求する
    (非単調系列への頑健化)。

    第二基準 = **下限** (decisions D15): masstree 系 workload では miss 率が木の
    深化で単調上昇し飽和しないことがある。その場合に上限 (=最も遅い run) を採るのは
    絶対規律4 と逆。代わりに l3_bytes が与えられていれば「working set (maxrss) が
    L3 の l3_multiple 倍以上になる最小 N」を候補として
    採る。l3_bytes が無ければ従来通り最大点を暫定返し (スイープ延長を促す)。

    両基準とも既存候補内で miss 率が cache_floor 以上の最小 N を優先する。
    適合候補が無ければ従来の最小候補と警告を保持する。
    """
    usable = [p for p in points if p.miss_rate is not None]
    res = SaturationResult(records=0, saturated=False, threshold=threshold,
                           l3_bytes=l3_bytes, l3_multiple=l3_multiple)

    if len(points) != len(usable):
        res.notes.append(
            f"{len(points) - len(usable)} 点で miss 率が欠損 (perf カウンタ取得失敗) → 除外")
    if not usable:
        res.notes.append("有効な測定点が無い。飽和判定不能")
        return res

    usable = sorted(usable, key=lambda p: p.records)
    res.series = []
    for i, p in enumerate(usable):
        row = {"records": float(p.records), "miss_rate": float(p.miss_rate)}
        if p.maxrss_kb is not None:
            row["maxrss_kb"] = float(p.maxrss_kb)
        if i > 0:
            row["delta"] = p.miss_rate - usable[i - 1].miss_rate
        res.series.append(row)

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
    original: Optional[int] = None
    for i in range(n - 1):
        flat = True
        for j in range(i + 1, n):
            if abs(usable[j].miss_rate - usable[j - 1].miss_rate) >= threshold:
                flat = False
                break
        if flat:
            if original is None:
                original = i
            if usable[i].miss_rate >= cache_floor:
                chosen = i
                break

    if chosen is None:
        chosen = original

    if chosen is None:
        # 末尾まで平らにならなかった = 範囲内で飽和せず (単調上昇 workload)。
        # 上限を採るのは規律4 と逆なので、下限基準にフォールバック。
        return _lower_bound(res, usable, l3_bytes, l3_multiple, cache_floor)

    p = usable[chosen]
    if chosen != original:
        old = usable[original]
        res.notes.append(
            f"cache_floor 下限 {cache_floor*100:.2f}% を満たす最小 N を同じ飽和候補から選択: "
            f"N={old.records:,} (LLC miss {old.miss_rate*100:.3f}%) → "
            f"N={p.records:,} (LLC miss {p.miss_rate*100:.3f}%)。")
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


def _lower_bound(res: SaturationResult, usable: List[ScalePoint],
                 l3_bytes: Optional[int], l3_multiple: float,
                 cache_floor: float) -> SaturationResult:
    """飽和点が無い (単調上昇) ときの下限基準 (decisions D15)。

    working set (= 実測 maxrss) が L3 の l3_multiple 倍以上の候補から、
    miss 率も cache_floor 以上の最小 N を採る。適合候補が無ければ従来の
    RSS 条件だけで最小の候補を保持する。l3_bytes / maxrss が無ければ
    判定できないので従来通り最大点を暫定返しし、スイープ延長を促す。
    """
    largest = usable[-1]
    have_maxrss = any(p.maxrss_kb is not None for p in usable)

    if l3_bytes is None or not have_maxrss:
        res.records = largest.records
        res.saturated = False
        res.miss_rate_at = largest.miss_rate
        miss = "" if l3_bytes is not None else "L3 総量未検出"
        rss = "" if have_maxrss else "maxrss 未取得"
        why = " / ".join(x for x in (miss, rss) if x)
        res.notes.append(
            f"測定範囲内で miss 率が飽和せず、下限基準も適用不能 ({why})。"
            "スイープを上に延ばすか L3/maxrss を供給すべき (採用値は暫定の最大点)")
        _flag_cache_floor(res, largest.miss_rate, cache_floor)
        return res

    need = l3_multiple * l3_bytes
    # RSS 候補の最小 N を退避し、miss 率下限も満たす最小 N を探す。
    chosen = None
    original = None
    for p in usable:
        if p.maxrss_kb is not None and p.maxrss_kb * 1024 >= need:
            if original is None:
                original = p
            if p.miss_rate >= cache_floor:
                chosen = p
                break

    if chosen is None:
        chosen = original

    if chosen is None:
        # 最大点でも L3×K に届かない = もっと大きい N が要る (稀)。
        res.records = largest.records
        res.saturated = False
        res.miss_rate_at = largest.miss_rate
        if largest.maxrss_kb is not None:
            res.working_set_ratio = (largest.maxrss_kb * 1024) / l3_bytes
        res.notes.append(
            f"測定範囲内で飽和せず、最大点の working set も L3 の {l3_multiple:g} 倍"
            "未満。レコード数を上げる必要がある (採用値は暫定の最大点)")
        _flag_cache_floor(res, largest.miss_rate, cache_floor)
        return res

    res.records = chosen.records
    res.saturated = False
    res.lower_bound_selected = True
    res.miss_rate_at = chosen.miss_rate
    res.working_set_ratio = (chosen.maxrss_kb * 1024) / l3_bytes
    if chosen is not original:
        res.notes.append(
            f"cache_floor 下限 {cache_floor*100:.2f}% を満たす最小 N を同じ下限基準候補から選択: "
            f"N={original.records:,} (LLC miss {original.miss_rate*100:.3f}%) → "
            f"N={chosen.records:,} (LLC miss {chosen.miss_rate*100:.3f}%)。")
    selection = (
        f"かつ LLC miss 率 ≥ {cache_floor*100:.2f}% を満たす最小 N={chosen.records:,} を採用。"
        if chosen.miss_rate >= cache_floor else
        f"の最小 N={chosen.records:,} を保持 (miss 率下限を満たす候補なし)。")
    res.notes.append(
        "測定範囲内で飽和点なし。下限基準を適用: "
        f"working set (maxrss {chosen.maxrss_kb/1024:.0f} MB) が L3 "
        f"({l3_bytes/1024/1024:.0f} MB) の {res.working_set_ratio:.1f} 倍 "
        f"(≥{l3_multiple:g}×) " + selection)
    _flag_cache_floor(res, chosen.miss_rate, cache_floor)
    return res


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
