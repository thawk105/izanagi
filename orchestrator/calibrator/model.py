# -*- coding: utf-8 -*-
"""Izanagi calibrator — データモデル。

calibrator の役割は「測定の妥当性を保つ最小コストの実験条件」を決めること
(roadmap §4)。ここには校正に必要な中間表現だけを置く:
1 点の測定 (`ScalePoint`)、飽和判定 (`SaturationResult`)、スケール感度
(`ScaleSensitivity`)、noise floor (`NoiseFloor`)、確定した校正結果
(`CalibrationResult`)。

**入力非依存性 (D13):** calibration は (env, thread数) ごとに決まり、入力
ワークロードに依存しない。だから出力は campaign スコープでなく env スコープ
(`output/env/<env-tag>/`) に置く。ここに置く数値は「測定の物差し」であって
variant の fitness ではない (fitness は verifier/性能ベンチが別途出す)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PerfCounters:
    """1 run の perf stat HW カウンタ (生値)。欠損は None。

    cache miss 率の母数は `LLC-loads` (= L3 への load アクセス数)、分子は
    `LLC-load-misses` (= そのうち DRAM へ溢れた数)。比 = working set が L3 を
    超えて DRAM を叩く割合。これが飽和シグナル (roadmap §4: 見るべきは
    throughput でなく cache 利用率)。
    """
    llc_load_misses: Optional[int] = None
    llc_loads: Optional[int] = None
    instructions: Optional[int] = None
    cycles: Optional[int] = None
    # 親が拾った生イベント名→値 (上記以外も保持して provenance にする)
    raw: Dict[str, int] = field(default_factory=dict)

    @property
    def llc_miss_rate(self) -> Optional[float]:
        """LLC load のうち miss した割合 (0..1)。母数 0 / 欠損なら None。"""
        if self.llc_loads is None or self.llc_load_misses is None:
            return None
        if self.llc_loads == 0:
            return None
        return self.llc_load_misses / self.llc_loads


@dataclass
class ScalePoint:
    """倍々スイープの 1 点 = (records, threads) 固定での 1 measurement。

    校正は単一 run でなく反復測定の分布として扱う (roadmap §3.6)。
    `throughputs` に反復 run の生 tps を全部残し、後から分布を再構成できる
    ようにする。`throughput` は中央値 (代表値)。
    """
    records: int                # ycsb_tuple_num
    threads: int                # thread_num
    counters: PerfCounters = field(default_factory=PerfCounters)
    throughputs: List[float] = field(default_factory=list)   # 反復 run の tps
    walltime_s: Optional[float] = None    # 1 run の実時間 (コスト指標)
    maxrss_kb: Optional[int] = None       # 常駐メモリ (working set の実測代理。
                                          # 下限判定 = working set vs L3 に使う)

    @property
    def miss_rate(self) -> Optional[float]:
        return self.counters.llc_miss_rate

    @property
    def throughput(self) -> Optional[float]:
        """反復 run の中央値 tps。0 run なら None。"""
        if not self.throughputs:
            return None
        return _median(self.throughputs)


@dataclass
class SaturationResult:
    """飽和判定の結果。

    `records` = 採用すべき最小レコード数。`saturated` が False なら測定範囲
    内で飽和しなかった (スイープを延ばす必要がある) ことを意味し、その場合
    `records` は測定した最大点 (= 暫定の安全側)。
    """
    records: int                    # 採用レコード数
    saturated: bool                 # 測定範囲内で飽和に達したか
    threshold: float                # 飽和判定の Δ (miss率の絶対変化, 0..1)
    miss_rate_at: Optional[float] = None     # 採用点の miss 率
    cache_floor_warning: bool = False        # 採用点が低 miss=working set が
                                             # cache に乗る疑い (下限割れ)
    # 膝が無い (単調上昇) workload 向けの下限基準 (decisions D15)。飽和点が
    # 範囲内に無いとき、上限を採る (=最も遅い run) のは規律4 と逆なので、
    # 代わりに「working set が L3 を l3_multiple 倍超える最小 N」を採る。
    lower_bound_selected: bool = False       # 飽和でなく下限基準で採用したか
    l3_bytes: Optional[int] = None           # 検出した L3 総量
    l3_multiple: Optional[float] = None       # 下限の安全係数 K
    working_set_ratio: Optional[float] = None  # 採用点 maxrss / L3 総量
    series: List[Dict[str, float]] = field(default_factory=list)  # 各点の (records, miss_rate, delta, maxrss)
    notes: List[str] = field(default_factory=list)


@dataclass
class ScaleSensitivity:
    """small / medium 2 点でのスケールの伸び方 (calibrator.md / roadmap §4)。

    variant 評価を単一スケールでやらないための特徴量。small で良いのに medium
    で頭打ちの variant に「スケールしない疑い」フラグを立てる材料。Phase 1 では
    枠組みだけ作り、実 variant 比較は Phase 2 で使う。
    """
    small: ScalePoint
    medium: ScalePoint
    # per-thread throughput = tps / threads。many-core での効率の代理。
    small_per_thread: Optional[float] = None
    medium_per_thread: Optional[float] = None
    # medium_per_thread / small_per_thread。1.0 近傍=線形に近い、<1=頭打ち。
    efficiency_ratio: Optional[float] = None
    scale_suspect: bool = False     # efficiency_ratio が閾値を下回る
    notes: List[str] = field(default_factory=list)


@dataclass
class NoiseFloor:
    """確定条件で baseline を連続 N 回測った throughput のばらつき。

    CV (変動係数 = stdev/mean) が「この差以下は信用するな」の下限 (roadmap
    §3.6(3))。環境タグごとに持ち、§3.6(4) の分布比較が『差なし』に丸める閾値
    の根拠になる。
    """
    throughputs: List[float] = field(default_factory=list)
    mean: Optional[float] = None
    median: Optional[float] = None
    stdev: Optional[float] = None
    cv: Optional[float] = None       # stdev / mean (0..)
    high_variance: bool = False      # cv が許容上限を超えた (環境が騒がしい)
    notes: List[str] = field(default_factory=list)


@dataclass
class CalibrationResult:
    """env スコープに書き出す確定校正。

    「なぜそのレコード数か」を査読に先回りで答えるため、判定だけでなく根拠
    (スイープの全点・飽和の推移・noise floor の生値) を全部持つ (roadmap §4)。
    """
    env_tag: str                    # linux-baremetal / mac-devcontainer ...
    threads: int                    # 飽和点は thread 数依存 → 必ず併記
    clocks_per_us: Optional[int] = None      # calibrator が実測した TSC MHz
    saturation: Optional[SaturationResult] = None
    noise_floor: Optional[NoiseFloor] = None
    scale: Optional[ScaleSensitivity] = None
    sweep: List[ScalePoint] = field(default_factory=list)    # 全測定点 (provenance)
    workload: Dict[str, str] = field(default_factory=dict)   # 固定した workload param
    host: Dict[str, str] = field(default_factory=dict)       # ホスト識別 (provenance)
    notes: List[str] = field(default_factory=list)


# ---- 小道具 ----

def _median(xs: List[float]) -> float:
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0
