# -*- coding: utf-8 -*-
"""Izanagi calibrator — データモデル。

calibrator の役割は「測定の妥当性を保つ最小コストの実験条件」を決めること
(roadmap §4)。ここには校正に必要な中間表現だけを置く:
1 点の測定 (`ScalePoint`)、飽和判定 (`SaturationResult`)、スケール感度
(`ScaleSensitivity`)、noise floor (`NoiseFloor`)、確定した校正結果
(`CalibrationResult`)。

**workload binding (D15):** calibration は (env, thread数, 代表 workload) ごとに決まる。
だから出力は campaign スコープでなく env スコープ
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

    @property
    def ipc(self) -> Optional[float]:
        """instructions per cycle。命令効率の leading indicator (spin/stall で下がる)。"""
        if self.instructions is None or self.cycles in (None, 0):
            return None
        return self.instructions / self.cycles


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
    run_cmd: str = ""                     # この測定点を再現する実行コマンド (forensic binding)
    # counters / walltime_s / maxrss_kb は代表 rep 由来 (throughput の中央値に
    # 最も近い rep、偶数有効 reps では上側中央。同値なら実行順で最初)。
    # CC-native な leading indicator (roadmap §3.5) は throughput と同じ中央値演算:
    # 奇数有効 reps は代表の中央 rep の値、偶数は throughput 順の中央 2 rep の
    # 算術平均 (一方でも欠損なら None)。
    abort_rate: Optional[float] = None    # abort/(commit+abort)。競合の捌き方が直接出る
    latency_ns: Optional[float] = None    # 平均トランザクションレイテンシ [ns]
    notes: List[str] = field(default_factory=list)   # rep 失敗等の構造化記録 (規律3)
    # floor campaign が opt-in したときだけ持つ rep 単位の実行・counter 証跡。
    # None は「呼び手が証跡収集を要求しなかった」を表し、空列を成功の既定値にしない。
    rep_observations: Optional[List[Dict[str, object]]] = None

    @property
    def miss_rate(self) -> Optional[float]:
        return self.counters.llc_miss_rate

    @property
    def throughput(self) -> Optional[float]:
        """反復 run の中央値 tps。0 run なら None。"""
        if not self.throughputs:
            return None
        return _median(self.throughputs)

    def leading_indicators(self) -> Dict[str, Optional[float]]:
        """fitness を説明する先行指標 (roadmap §3.5)。critic が設計選択に帰属させる材料。

        throughput スカラーだけでは探索が停滞する (Jitskit) ので、abort 率
        (CC が競合をどう捌くか)・latency・cache miss 率・IPC を一緒に残す。
        latency_ns は WAL に残す CC 本来のデータだが、CCBench の通常出力では
        throughput 由来の量なので critic digest は列に出さない。
        """
        return {
            "throughput_tps": self.throughput,
            "abort_rate": self.abort_rate,
            "latency_ns": self.latency_ns,
            "llc_miss_rate": self.counters.llc_miss_rate,
            "ipc": self.counters.ipc,
        }


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
class BetweenRunNoiseFloor:
    """独立な測定セッション間 (= 別 run) の throughput ばらつき (roadmap §3.6(3)(4))。

    `NoiseFloor` (within-run) が 1 セッション内 N rep の散らばり = **その 1 測定の品質**
    を見る (再測定/unstable の品質ゲート) のに対し、これは N 個の**独立セッション**
    (各 = 1 つの measure_point = rep を内包し median を返す) の session-median の散らばり
    = **差が信用できるかの下限**を見る。variant と baseline は決して同一セッションで
    測らない (別ビルド・campaign の別時点) ので、§3.6(4) の分布比較が『差なし』に丸める
    閾値 (compare の noise_cv) は within-run でなく between-run であるべき。

    **限界 (正直に):** fresh な back-to-back セッションは warmup/cwd のリセットは挟むが
    settle は admission (他テナント検出) であって独立性ではない (runner.settle の docstring:
    連続 run 間 settle は load EMA 残像でほぼ即 return)。よって cold-boot/温度/数時間
    ドリフトは捉えない = workload-agnostic な**下限**。high-abort genome は run 間ドリフトが
    大きい (worklog 2026-06-28: no-backoff abort 82% が最大の run 間分散源)。wired する floor は
    cross-campaign の genuine な between データと突き合わせ保守側 (最大) に採る。
    """
    session_throughputs: List[float] = field(default_factory=list)  # 各セッションの代表 tps (=median)
    sessions: int = 0                # 有効セッション数 (測定不能を除いた数)
    cv: Optional[float] = None       # between-run CV = session 列の stdev/mean (信用できる差の下限)
    mean: Optional[float] = None
    median: Optional[float] = None
    stdev: Optional[float] = None
    high_variance: bool = False      # cv が cv_threshold を超えた (既定は汎用 5%。between 固有でなく
                                     # 診断専用。採否 floor の確定は driver が cross-campaign と突き合わせ)
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


@dataclass
class CertificationMeasurement:
    """certification で probe に挟まれた 1 measurement point の完備証拠。"""

    kind: str
    expected_reps: int
    point: ScalePoint


@dataclass
class CertificationEvidence:
    """C3-1 の 8 条件を独立に判定するための run-scoped 証拠。"""

    tsc_measured: bool = False
    cooldown_settled: bool = False
    measurements: List[CertificationMeasurement] = field(default_factory=list)
    all_subprocesses_succeeded: bool = False
    all_windows_isolated: bool = False
    post_static_matches: bool = False


# ---- 小道具 ----

def _median(xs: List[float]) -> float:
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0
