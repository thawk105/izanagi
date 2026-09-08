# -*- coding: utf-8 -*-
"""s8b floor 統計の純関数モジュール (formula v2 の実装正本)。

段 8b oracle の **採否丸め閾値 (floor)** を、holdout×構成のセル計測から算出する記述的
統計を、I/O・環境参照を一切持たない純関数として実装する。実機ドライバ・レポータは本モジュール
を通してのみ floor を得る (自前で式を持たない)。生成側と検証側が同一関数を通るので、
`verify_floor_artifact` は自己申告値を厳密 (==) 比較で照合できる。

**この floor は単一 campaign 内で観測された session dispersion に基づく記述的な下限であり、
α・検定力を保証する検定ではない。** 「有意」とは呼ばない。u_noise は 2 群の session-median
標準偏差の RSS で、「差がその大きさ未満なら単一 campaign 内の session 間ノイズと区別できない」
という下限を与える。**時間ドリフト・cold-boot・温度など別 run 間で生じる変動は本 floor に
含まれない下限であり、報告側でその限界を明記する** (formula v1 の 2-block delta_c 対比は
ユーザー裁定 F1 で廃止された。§9 承認状態 2026-07-18)。

算出式 (formula_id = FORMULA_ID) はセルの有効性契約・floor 合成・scalar 代替・診断まで含めて
本モジュールが正本である。**式を変えるときは FORMULA_ID を改版する。式の正本記述は
docs/phase3-8b-descriptor-design.md §9 承認状態 (2026-07-18) を参照する。凍結済み裁定資料
(output/insights/2026-07-16_*.md) は不変であり本モジュールから編集を指示しない。**

fail-closed 契約 (絶対規律): 縮退・欠測・不正入力はすべて null/判定不能へ倒す。
- 無効 session は median を作らない (fallback 値を代入しない)。
- stock セルが無効/machine_anomaly なら当該 holdout の floor は未確定 = 全 pair null +
  scalar_alt null + scale_ref null (holdout ごと丸ごと落とす)。
- stock 以外のセル c が無効/machine_anomaly なら当該 pair のみ null。他 pair に veto しない。
- scalar 代替はいずれかの pair が null なら null (max を欠測で盛らない)。
- protocol config (n_sessions / reps / stock / wired_min_rel_floor / session_cv_max /
  cell_cv_max) はすべて呼び出し側からの入力必須。本モジュールは未凍結数値のデフォルトを内蔵
  しない (F14 対策)。

閾値の厳密算術 (α-9): session 内 CV / セル間 CV の判定はすべて Fraction 厳密算術で行う。
CV > T ⟺ 標本分散(n-1) > T²·mean² を全て Fraction で比較する。閾値は decimal 文字列で受け
Fraction(str) で解釈し、標本値は Fraction(float) で厳密変換する。float 直接比較 (0.1 の 2 進
非正確表現) による境界の非決定を排除する。表示用 cv は float で別に持ち、判定 Fraction と混同
しない。
"""
from __future__ import annotations

import hashlib
import math
import statistics
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Optional, Sequence

from ..calibrator import perf_preflight as _perf_preflight
from . import s8b_binary_admission as _binary_admission
from . import s8b_floor_contract as _floor_contract

FORMULA_ID = "s8b-floor-stats/v2"

# 閉じた除外理由表 (F2 承認 + F1 で 4 行目 performance_anomaly 追加)。並び順も正本。
ALLOWED_EXCLUDED_REASONS = (
    "competing_process",
    "launch_failure",
    "nonfinite_or_partial_output",
    "performance_anomaly",
)
_REASON_PARTIAL = "nonfinite_or_partial_output"
_REASON_PERFORMANCE = "performance_anomaly"
REP_INTEGRITY_EXCLUSION_CLASS = "rep_integrity_failure"
PERF_EVENTS = ("LLC-load-misses", "LLC-loads", "instructions", "cycles")
_REP_OBSERVATION_KEYS = frozenset({
    "rep_index", "returncode", "counter_status", "missing_perf_events",
    "perf_raw", "throughput", "execution_failure",
})
_COUNTER_STATUSES = frozenset({"complete", "incomplete", "not_required", "unknown"})

# throughput から再導出できる (＝ verifier が生値照合できる) 理由。probe/launch 起因の
# competing_process / launch_failure は throughput から導出不能で、その真正性は F7 wave
# (journal 突合) の責務。
_THROUGHPUT_DERIVABLE_REASONS = frozenset({_REASON_PARTIAL, _REASON_PERFORMANCE})


class FloorStatsError(ValueError):
    """protocol 縮退・型違反・内部不変条件破れの構造化エラー (fail-closed)。"""


# ---------------------------------------------------------------------------
# session 評価 (単一純関数 — 生成側・verifier・cell_stats 全経路が共有)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SessionAssessment:
    """raw throughputs 単体からの評価結果 (α-8: 検証の運用非依存化)。

    median          : 有効 (required_reason is None) なら session_median、無効なら None。
    cv              : 完全・有限・正の計測なら表示用 CV (float)、部分計測なら None。
    required_reason : この throughputs が必然的に負う理由 (閉表 4 理由のうち throughput 導出可能な
                      performance_anomaly / nonfinite_or_partial_output のみ)。有効なら None。
    """
    median: Optional[float]
    cv: Optional[float]
    required_reason: Optional[str]


def _threshold_fraction(name: str, value) -> Fraction:
    """decimal 文字列閾値を Fraction へ厳密変換 (0 < T <= 1 を要求)。"""
    if isinstance(value, bool) or not isinstance(value, str):
        raise FloorStatsError(f"{name} は decimal 文字列であること (受領 {value!r})")
    try:
        frac = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise FloorStatsError(f"{name} を Fraction 化できない: {value!r}") from exc
    if not (0 < frac <= 1):
        raise FloorStatsError(f"{name} は (0, 1] 域であること (受領 {value!r})")
    return frac


def _cv_exceeds(values: Sequence[float], threshold: Fraction) -> bool:
    """CV > threshold を Fraction 厳密算術で判定する。

    CV = s/mean (s = 標本標準偏差 n-1)。CV > T ⟺ var(n-1) > T²·mean² (mean > 0 前提)。
    全て Fraction。標本値は Fraction(float) で厳密変換 (IEEE-754 の 2 進表現をそのまま採用)
    するので、同じ入力に対し機械・run をまたいで決定的。
    """
    fr = [Fraction(v) for v in values]
    n = len(fr)
    mean = sum(fr, Fraction(0)) / n
    if mean <= 0:
        # 完全・有限・正値を通過した後にここへ来るのは内部不変条件破れ (β-8)。
        raise FloorStatsError("CV 判定: 有限正値なのに mean <= 0 (内部不変条件破れ)")
    var = sum((x - mean) ** 2 for x in fr) / (n - 1)
    return var > (threshold * threshold) * (mean * mean)


def assess_session(throughputs, *, reps: int, session_cv_max) -> SessionAssessment:
    """raw throughputs から session の median / CV / 必然理由を返す単一純関数 (α-7/α-8)。

    事前検査 (不変条件破れ = 構造化エラー FloorStatsError):
      - reps は非 bool int かつ >= 2 (標本標準偏差の定義に 2 点以上必要)。
      - session_cv_max は (0,1] の decimal 文字列。
      - throughputs 各値は非 bool の実数型 (bool / 非数値は型違反 = エラー)。

    完全性判定 (fail-closed に無効化する = required_reason を付す):
      - len(throughputs) != reps、または非有限・0 以下を含む → required_reason =
        "nonfinite_or_partial_output"、median/cv は None。
      - 完全・有限・正値で CV > session_cv_max (Fraction 厳密) → required_reason =
        "performance_anomaly"、median は None、cv は表示値。
      - 完全・有限・正値で CV <= session_cv_max → required_reason None、median と cv を返す。
    """
    if isinstance(reps, bool) or not isinstance(reps, int):
        raise FloorStatsError(f"reps は int であること (受領 {reps!r})")
    if reps < 2:
        raise FloorStatsError(f"reps は 2 以上であること (CV の定義に必要, 受領 {reps})")
    threshold = _threshold_fraction("session_cv_max", session_cv_max)

    tps = tuple(throughputs)
    # 型違反は理由でなくエラー (bool は int のサブクラスなので先に弾く)。
    for v in tps:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise FloorStatsError(f"throughputs に非数値/bool が混入: {v!r}")

    # 完全性 (本数一致 ∧ 全値有限正)。いずれか崩れれば部分/非有限として無効化。
    complete = len(tps) == reps and all(math.isfinite(v) and v > 0 for v in tps)
    if not complete:
        return SessionAssessment(median=None, cv=None, required_reason=_REASON_PARTIAL)

    median = statistics.median(tps)
    mean_f = statistics.fmean(tps)
    cv_display = statistics.stdev(tps) / mean_f  # mean_f > 0 (完全・有限・正値)
    if _cv_exceeds(tps, threshold):
        return SessionAssessment(median=None, cv=cv_display,
                                 required_reason=_REASON_PERFORMANCE)
    return SessionAssessment(median=median, cv=cv_display, required_reason=None)


# ---------------------------------------------------------------------------
# 入力レコード
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SessionRecord:
    """1 セッション (= 実 campaign の 1 measure_point と同形) の生計測。

    throughputs は「rc/counter が完備した rep の tps」列であり、reps_expected 本揃って初めて有効。
    exec_failures / excluded_reason / 非有限・非正値・CV 超過はいずれも session を無効にする。
    formula v2 で block field は廃止 (2-block delta_c 対比は F1 裁定で削除, α-12)。
    """
    cell_id: str
    holdout_id: str
    configuration_id: str
    seq: int                         # holdout×構成内のセッション連番 (順序の決定性用)
    throughputs: tuple                # tuple[float, ...] — 成功 rep の tps
    reps_expected: int
    exec_failures: int
    excluded_reason: Optional[str]
    retry: bool
    rep_observations: tuple = ()
    rep_integrity_failures: Optional[int] = None


def session_median(rec: SessionRecord, *, reps: int, session_cv_max) -> Optional[float]:
    """有効 session の session_median。無効なら None。判定は assess_session に一元化 (α-8)。

    有効性 ⇔ excluded_reason is None ∧ exec_failures == 0 ∧
    assess_session(throughputs, reps, session_cv_max).required_reason is None。
    driver が付した probe/launch 起因の excluded_reason (competing_process/launch_failure) は
    throughput から導出できないため、ここでは self-report を尊重して無効化する (真正性の突合は
    verifier + F7 wave)。
    """
    if rec.excluded_reason is not None:
        return None
    if rec.exec_failures != 0:
        return None
    return assess_session(rec.throughputs, reps=reps,
                          session_cv_max=session_cv_max).median


# ---------------------------------------------------------------------------
# セル統計
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CellStats:
    """セル c (holdout×構成) の記述統計 (formula v2 — block_medians 廃止)。

    valid=False のとき m/s/cv が None でも部分診断値は保持しうるが、holdout_floors は
    valid=True のセルしか floor 合成に使わない (無効は null へ倒す)。
    machine_anomaly はセル間 CV と閾値の関数なので CellStats 自体は持たず holdout_floors が判定
    する。ただし判定は本モジュールの cell_cv_exceeds が正本で、生成側・verifier が共有する
    (β-9: cell 出力に再計算可能な machine_anomaly 状態を持たせる)。
    """
    cell_id: str
    holdout_id: str
    configuration_id: str
    n_valid: int
    medians: tuple                        # 有効 session medians (seq 昇順)
    m: Optional[float]                    # statistics.median(medians)
    s: Optional[float]                    # statistics.stdev(medians) — n-1、要 2 点以上
    valid: bool
    cv: Optional[float]                  # s / statistics.fmean(medians) — 表示用診断 (float)
    notes: tuple = ()                     # 無効理由等 (人間可読)


def cell_cv_exceeds(medians: Sequence[float], cell_cv_max) -> bool:
    """セル間 CV > cell_cv_max を Fraction 厳密算術で判定する (machine_anomaly の正本)。

    要 2 点以上。判定は _cv_exceeds と同一意味論 (表示 float と混同しない厳密経路)。
    """
    if len(medians) < 2:
        raise FloorStatsError("cell_cv_exceeds: medians が 2 点未満 (CV 判定不能)")
    threshold = _threshold_fraction("cell_cv_max", cell_cv_max)
    return _cv_exceeds(medians, threshold)


def cell_stats(records: Sequence[SessionRecord], *, n_sessions: int, reps: int,
               session_cv_max) -> CellStats:
    """1 セルの有効 session medians から CellStats を組む (formula v2)。

    セル有効 ⇔ 有効 session 数 == n_sessions ∧ 全レコードの (cell_id, holdout_id,
    configuration_id) が一致。有効性判定は assess_session 経由 (α-8)。s は statistics.stdev
    (n-1、要 2 点以上)。cv は表示用 float 診断で machine_anomaly 判定には使わない
    (判定は cell_cv_exceeds が Fraction 厳密で行う)。
    """
    notes: list = []
    cell_id = records[0].cell_id if records else ""
    holdout_id = records[0].holdout_id if records else ""
    configuration_id = records[0].configuration_id if records else ""
    if not records:
        notes.append("レコードが空")

    # 座標の一貫性 (混入検知、fail-closed)。
    mixed_cell = sorted({r.cell_id for r in records})
    mixed_holdout = sorted({r.holdout_id for r in records})
    mixed_cfg = sorted({r.configuration_id for r in records})
    coord_consistent = (len(mixed_cell) <= 1 and len(mixed_holdout) <= 1
                        and len(mixed_cfg) <= 1)
    if len(mixed_cell) > 1:
        notes.append(f"cell_id 不一致: {mixed_cell}")
    if len(mixed_holdout) > 1:
        notes.append(f"holdout_id 不一致: {mixed_holdout}")
    if len(mixed_cfg) > 1:
        notes.append(f"configuration_id 不一致: {mixed_cfg}")

    # 有効 session を seq 昇順に。順序の決定性は verify の == 照合に効く。
    valid_recs = [r for r in records
                  if session_median(r, reps=reps, session_cv_max=session_cv_max) is not None]
    valid_recs.sort(key=lambda r: r.seq)
    medians = tuple(session_median(r, reps=reps, session_cv_max=session_cv_max)
                    for r in valid_recs)  # 全て非 None
    n_valid = len(medians)

    m = statistics.median(medians) if n_valid >= 1 else None
    s = statistics.stdev(medians) if n_valid >= 2 else None
    cv: Optional[float] = None
    if s is not None:
        mean = statistics.fmean(medians)
        cv = s / mean if mean > 0 else None

    valid = coord_consistent and n_valid == n_sessions
    if n_valid != n_sessions:
        notes.append(f"有効 session 数 {n_valid} != n_sessions {n_sessions}")

    return CellStats(cell_id=cell_id, holdout_id=holdout_id,
                     configuration_id=configuration_id, n_valid=n_valid,
                     medians=medians, m=m, s=s, valid=valid, cv=cv,
                     notes=tuple(notes))


# ---------------------------------------------------------------------------
# holdout の floor 合成
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HoldoutFloors:
    """1 holdout の pair 別 floor と scalar 代替 (formula v2)。

    pairs のキーは configuration_id (freeze 向き出力, δ-10)。diagnostics のキーは cell_id
    (raw 向き)。
    stock 無効/machine_anomaly → 全 pair None + scalar_alt None + scale_ref None (holdout 未確定)。
    非 stock c 無効/machine_anomaly → 当該 pair のみ None (他 pair に veto しない)。
    scalar_alt: 全 pair floor の max。いずれかが None なら None。
    scale_ref: m_stock (oracle 実走時の scale-adequacy gate 用)。
    """
    pairs: dict                          # {configuration_id: floor_pair (float) | None}
    scalar_alt: Optional[float]
    scale_ref: Optional[float]
    diagnostics: dict                    # {cell_id: {...}} + machine_anomaly_cells 一覧


def _cell_machine_anomaly(c: CellStats, cell_cv_max) -> bool:
    """有効セルが machine_anomaly (セル間 CV 超過) か。無効セルは False (無効理由が優先)。"""
    if not c.valid or c.n_valid < 2:
        return False
    return cell_cv_exceeds(c.medians, cell_cv_max)


def holdout_floors(cells: Mapping[str, CellStats], *, stock_id: str,
                   wired_min_rel_floor: float, cell_cv_max) -> HoldoutFloors:
    """FORMULA v2 逐語 (§9 承認状態 2026-07-18):

        u_noise(c)   = sqrt(s_c^2 + s_stock^2)
        floor_pair(c)= max(u_noise(c), wired_min_rel_floor × m_stock)

    machine_anomaly (fail-closed 専用): 有効セル c のセル間 CV > cell_cv_max のとき、
    非 stock なら当該 pair null、stock なら holdout 全体 (全 pair / scalar_alt / scale_ref) null。
    stock (= stock_common セル) が無効/不在/machine_anomaly なら当該 holdout の全 pair は null、
    scale_ref も null (holdout 未確定)。非 stock c 無効/anomaly → その pair のみ null。
    pairs のキーは configuration_id (δ-10)。
    """
    diagnostics: dict = {"stock_id": stock_id,
                         "wired_min_rel_floor": wired_min_rel_floor,
                         "cell_cv_max": cell_cv_max,
                         "cells": {}, "machine_anomaly_cells": []}
    stock = cells.get(stock_id)
    stock_valid = stock is not None and stock.valid
    stock_anomaly = bool(stock_valid and _cell_machine_anomaly(stock, cell_cv_max))
    diagnostics["stock_valid"] = bool(stock_valid)
    diagnostics["stock_machine_anomaly"] = stock_anomaly

    # 非 stock セルの configuration_id → pair キー。既定は判定不能 (null)。
    pairs: dict = {}
    machine_anomaly_cells: list = []
    for cid, c in cells.items():
        if cid == stock_id:
            continue
        pairs[c.configuration_id] = None

    if stock_anomaly:
        machine_anomaly_cells.append(stock_id)
        diagnostics["cells"][stock_id] = {"machine_anomaly": True,
                                          "floor": None, "reason": "stock machine_anomaly"}
    if not stock_valid or stock_anomaly:
        reason = "stock セル無効/不在" if not stock_valid else "stock machine_anomaly"
        diagnostics["reason"] = reason
        diagnostics["machine_anomaly_cells"] = sorted(machine_anomaly_cells)
        return HoldoutFloors(pairs=pairs, scalar_alt=None, scale_ref=None,
                             diagnostics=diagnostics)

    m_stock = stock.m
    s_stock = stock.s
    scale_ref = m_stock
    rel_floor = wired_min_rel_floor * m_stock
    diagnostics["cells"][stock_id] = {"machine_anomaly": False, "m": m_stock,
                                      "s": s_stock, "cv": stock.cv}

    for cid, c in cells.items():
        if cid == stock_id:
            continue
        cfg = c.configuration_id
        if not c.valid:
            diagnostics["cells"][cid] = {"machine_anomaly": False, "floor": None,
                                         "reason": "セル無効", "cv": c.cv}
            continue
        anomaly = _cell_machine_anomaly(c, cell_cv_max)
        if anomaly:
            machine_anomaly_cells.append(cid)
            pairs[cfg] = None
            diagnostics["cells"][cid] = {"machine_anomaly": True, "floor": None,
                                         "reason": "machine_anomaly", "cv": c.cv}
            continue
        u_noise = math.sqrt(c.s ** 2 + s_stock ** 2)
        floor_pair = max(u_noise, rel_floor)
        pairs[cfg] = floor_pair
        diagnostics["cells"][cid] = {"machine_anomaly": False, "u_noise": u_noise,
                                     "rel_floor": rel_floor, "floor": floor_pair,
                                     "cv": c.cv}

    diagnostics["machine_anomaly_cells"] = sorted(machine_anomaly_cells)

    # scalar 代替: 全 pair の max。空 or いずれか null → null (欠測で盛らない)。
    vals = list(pairs.values())
    if not vals or any(v is None for v in vals):
        scalar_alt: Optional[float] = None
    else:
        scalar_alt = max(vals)

    return HoldoutFloors(pairs=pairs, scalar_alt=scalar_alt, scale_ref=scale_ref,
                         diagnostics=diagnostics)


# ---------------------------------------------------------------------------
# 自己申告値の検証 (生データからの再計算と厳密照合 + 外部 protocol 照合)
# ---------------------------------------------------------------------------
# 保証境界 (docstring 正本): verify_floor_artifact は「raw session からの内部整合再計算 +
# expected_protocol (外部凍結値) との照合」を保証する。raw session 自体の真正性 (append-only
# journal / attempt registry / schedule との突合) は本関数の責務ではなく F7 wave の責務である
# (α-1)。したがって「全 throughput を都合よく書き換え derived を再生成した」改竄は本関数単体
# では捕まらない — journal 突合が別レイヤで必要。
_EXPECTED_PROTOCOL_KEYS = ("formula", "n_sessions", "reps", "stock_configuration",
                           "wired_min_rel_floor", "session_cv_max", "cell_cv_max",
                           "expected_cells")
_REQUIRED_SESSION = ("cell_id", "holdout_id", "configuration_id", "seq",
                     "throughputs", "reps_expected", "exec_failures",
                     "excluded_reason", "retry", "rep_observations",
                     "rep_integrity_failures", "exclusion_class")
# artifact.config に self-report される protocol 値 (expected と完全一致すべき)。
_CONFIG_SCALARS = ("formula", "n_sessions", "reps", "stock_configuration",
                   "wired_min_rel_floor", "session_cv_max", "cell_cv_max")


def _record_from_mapping(d: Mapping) -> SessionRecord:
    """session 生データ dict を SessionRecord に厳密変換 (欠損キーは KeyError)。"""
    for field in ("seq", "reps_expected", "exec_failures"):
        value = d[field]
        if type(value) is not int or value < 0:
            raise ValueError(f"{field} が非負 exact int でない: {value!r}")
    if type(d["retry"]) is not bool:
        raise ValueError(f"retry が exact bool でない: {d['retry']!r}")
    return SessionRecord(
        cell_id=d["cell_id"],
        holdout_id=d["holdout_id"],
        configuration_id=d["configuration_id"],
        seq=d["seq"],
        throughputs=tuple(d["throughputs"]),
        reps_expected=d["reps_expected"],
        exec_failures=d["exec_failures"],
        excluded_reason=d["excluded_reason"],
        retry=d["retry"],
        rep_observations=tuple(d["rep_observations"]),
        rep_integrity_failures=d["rep_integrity_failures"],
    )


def _rep_evidence_exemption_kind(raw: Mapping) -> Optional[str]:
    """構造的に測定されなかった session の固定分類を返す。"""
    if (raw.get("run_cmd") is not None
            or raw.get("throughputs") != []
            or raw.get("session_median") is not None
            or raw.get("valid") is not False):
        return None
    probe_before = raw.get("probe_before")
    probe_after = raw.get("probe_after")
    if (isinstance(probe_before, Mapping)
            and probe_before.get("competing") is True
            and probe_after is None):
        return "pre_probe_competing"
    if raw.get("exec_failures") == raw.get("reps_expected"):
        return "measure_exception"
    return None


def _derive_rep_integrity(observations, *, reps: int,
                          expected_use_perf: bool) -> tuple[list, int, int, tuple]:
    """rep 証跡から integrity/実行例外本数と qualified tps を独立再導出する。"""
    errors: list = []
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        return ["rep_observations が配列でない"], reps, 0, ()
    if len(observations) != reps:
        errors.append(f"rep_observations 件数 {len(observations)} != reps {reps}")

    by_index: dict[int, Mapping] = {}
    structurally_bad: set[int] = set()
    for position, observation in enumerate(observations):
        ctx = f"rep_observations[{position}]"
        if not isinstance(observation, Mapping):
            errors.append(f"{ctx}: object でない")
            continue
        if set(observation) != _REP_OBSERVATION_KEYS:
            errors.append(
                f"{ctx}: exact key 不一致 (受領 {sorted(map(repr, observation))})"
            )
        index = observation.get("rep_index")
        if type(index) is not int or not 0 <= index < reps:
            errors.append(f"{ctx}: rep_index が範囲内 exact int でない: {index!r}")
            continue
        if index in by_index:
            errors.append(f"{ctx}: rep_index {index} が重複")
            structurally_bad.add(index)
            continue
        by_index[index] = observation

    missing_indices = sorted(set(range(reps)) - set(by_index))
    if missing_indices:
        errors.append(f"rep_observations: rep_index 欠損 {missing_indices}")

    failures = len(missing_indices)
    exec_failures = 0
    qualified: list = []
    for index in range(reps):
        observation = by_index.get(index)
        if observation is None:
            continue
        ctx = f"rep_observations[{index}]"
        bad = index in structurally_bad

        execution_failure = observation.get("execution_failure")
        if type(execution_failure) is not bool:
            errors.append(
                f"{ctx}: execution_failure が exact bool でない: "
                f"{execution_failure!r}"
            )
            bad = True
        elif execution_failure:
            exec_failures += 1

        returncode = observation.get("returncode")
        returncode_is_exact_int = type(returncode) is int
        if returncode is not None and not returncode_is_exact_int:
            errors.append(f"{ctx}: returncode が exact int/null でない: {returncode!r}")
            bad = True

        perf_raw = observation.get("perf_raw")
        if not isinstance(perf_raw, Mapping) or set(perf_raw) != set(PERF_EVENTS):
            errors.append(f"{ctx}: perf_raw の exact event 集合が不一致")
            perf_raw = {}
            bad = True
        raw_missing: list[str] = []
        for event in PERF_EVENTS:
            value = perf_raw.get(event)
            if value is not None and type(value) is not int:
                errors.append(f"{ctx}: perf_raw[{event!r}] が exact int/null でない")
                bad = True
            if type(value) is not int or value < 0:
                raw_missing.append(event)

        reported_missing = observation.get("missing_perf_events")
        if (not isinstance(reported_missing, Sequence)
                or isinstance(reported_missing, (str, bytes))):
            errors.append(f"{ctx}: missing_perf_events が配列でない")
            reported_missing = []
            bad = True
        else:
            reported_missing = list(reported_missing)
            strings_only = all(isinstance(event, str) for event in reported_missing)
            expected_order = (
                [event for event in PERF_EVENTS if event in reported_missing]
                if strings_only else []
            )
            if (not strings_only or reported_missing != expected_order
                    or len(set(reported_missing)) != len(reported_missing)):
                errors.append(f"{ctx}: missing_perf_events が固定順 subset でない")
                bad = True

        derived_missing = raw_missing if expected_use_perf else []
        if reported_missing != derived_missing:
            errors.append(
                f"{ctx}: missing_perf_events 齟齬 "
                f"(申告 {reported_missing!r} != raw 再導出 {derived_missing!r})"
            )
            bad = True
        derived_status = (
            "not_required" if not expected_use_perf
            else "complete" if not derived_missing else "incomplete"
        )
        status = observation.get("counter_status")
        if not isinstance(status, str) or status not in _COUNTER_STATUSES:
            errors.append(f"{ctx}: counter_status が未知: {status!r}")
            bad = True
        if status != derived_status:
            errors.append(
                f"{ctx}: counter_status 齟齬 "
                f"(申告 {status!r} != 再導出 {derived_status!r})"
            )
            bad = True

        throughput = observation.get("throughput")
        if throughput is not None and (
                isinstance(throughput, bool) or not isinstance(throughput, (int, float))):
            errors.append(f"{ctx}: throughput が数値/null でない: {throughput!r}")
        if execution_failure is True and throughput is not None:
            errors.append(
                f"{ctx}: execution_failure=True なのに throughput が非 null"
            )
            bad = True

        complete = (
            not bad
            and returncode is not None and returncode == 0
            and status == derived_status
            and derived_status in {"complete", "not_required"}
            and execution_failure is False
        )
        if not complete:
            failures += 1
        elif throughput is not None:
            qualified.append(throughput)
    return errors, failures, exec_failures, tuple(qualified)


def _cmp(ctx: str, name: str, reported, computed, out: list) -> None:
    if reported != computed:
        out.append(f"{ctx}: {name} 齟齬 (申告 {reported!r} != 再計算 {computed!r})")


def floor_perf_validation_contexts(
        artifact: Mapping) -> tuple[tuple[object, Mapping[str, object]], ...]:
    """result 内の全 session を observation validator 用 context へ射影する。"""

    contexts: list[tuple[object, Mapping[str, object]]] = []
    sessions = artifact.get("sessions") if isinstance(artifact, Mapping) else None
    binaries = artifact.get("binaries") if isinstance(artifact, Mapping) else None

    def binary_run_cmd(cell_id: object | None = None) -> tuple[str, ...] | None:
        if not isinstance(binaries, Mapping):
            return None
        candidates = (
            (binaries.get(cell_id),) if cell_id is not None
            else tuple(binaries[key] for key in sorted(binaries, key=str))
        )
        for binary in candidates:
            if isinstance(binary, Mapping) and isinstance(binary.get("binary"), str):
                return (binary["binary"],)
        return None

    if isinstance(sessions, Sequence) and not isinstance(sessions, (str, bytes)):
        for session in sessions:
            if not isinstance(session, Mapping):
                continue
            run_cmd = session.get("run_cmd")
            if run_cmd is None:
                run_cmd = binary_run_cmd(session.get("cell_id"))
            if run_cmd is None:
                raise _perf_preflight.PerfPreflightError(
                    "floor session の run_cmd を同じ result から導出できない"
                )
            contexts.append((run_cmd, {
                "ipc": session.get("ipc"),
                "llc_miss_rate": session.get("llc_miss_rate"),
                "session": session,
            }))
    if not contexts:
        run_cmd = binary_run_cmd()
        if run_cmd is None:
            raise _perf_preflight.PerfPreflightError(
                "floor result の run_cmd を同じ result から導出できない"
            )
        contexts.append((run_cmd, {
            "ipc": artifact.get("ipc"),
            "llc_miss_rate": artifact.get("llc_miss_rate"),
            "artifact": artifact,
        }))
    return tuple(contexts)


def validate_floor_perf_evidence(
        artifact: Mapping, observation: object, *, claim: str | None = None) -> dict:
    """全 session の argv/raw counter と artifact-level observation を束縛する。"""

    contexts = floor_perf_validation_contexts(artifact)
    first_run_cmd, first_indicators = contexts[0]
    if claim is None:
        normalized = _perf_preflight.validate_perf_observation(
            observation, run_cmd=first_run_cmd,
            leading_indicators=first_indicators,
        )
    else:
        allowed = _perf_preflight.perf_claim_allowed(
            observation, claim, run_cmd=first_run_cmd,
            leading_indicators=first_indicators,
        )
        if not allowed:
            raise _perf_preflight.PerfPreflightError(
                f"floor artifact は {claim!r} claim を許可しない"
            )
        normalized = _perf_preflight.validate_perf_observation(
            observation, run_cmd=first_run_cmd,
            leading_indicators=first_indicators,
        )
    for run_cmd, leading_indicators in contexts[1:]:
        candidate = _perf_preflight.validate_perf_observation(
            observation, run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )
        if candidate != normalized:
            raise _perf_preflight.PerfPreflightError(
                "floor session 間で perf observation の正規化結果が不一致"
            )
    return normalized


def verify_floor_artifact(artifact: Mapping, expected_protocol: Mapping,
                          expected_binaries: Optional[Mapping] = None, *,
                          expected_holdout_admission: Mapping,
                          expected_use_perf: bool,
                          expected_attempt_registry: Mapping[str, object] | None = None) -> list:
    """artifact の生 session を再計算し、自己申告値 + 外部 expected_protocol と厳密照合する。

    **保証境界 (α-1):** この関数は live admission を保証しない。caller が渡す
    expected_holdout_admission は live inspector 由来でなければならない。本関数が保証するのは
    (1) raw session からの cells/floors/理由の内部整合
    再計算一致と、(2) artifact.config の自己申告 protocol 値が外部 expected_protocol (凍結値) と
    完全一致すること、および (3) 出現するセル集合が expected_protocol.expected_cells と完全一致
    すること、である。**raw session 自体の真正性 (append-only journal・attempt registry・
    schedule 突合) は保証しない — それは F7 wave の責務。v5 の
    attempt registry prefix は caller が独立 replay した proof と照合する。

    binary admission は receipt の実在、exact key、canonical outer SHA、subject と
    record の一致、artifact 内 cross-cell 整合を無条件に検査する。per-cell freeze
    entry の権威は ratified/holdout verifier が持ち、本 standalone verifier は持たない。

    expected_protocol の想定形 (外部入力、既定値なし):
        {formula, n_sessions, reps, stock_configuration, wired_min_rel_floor,
         session_cv_max, cell_cv_max,
         expected_cells: {holdout_id: [configuration_id, ...]}}

    artifact の想定形:
        {
          "config": {formula, n_sessions, reps, stock_configuration,
                     wired_min_rel_floor, session_cv_max, cell_cv_max},
          "sessions": [ {SessionRecord と同じ key の dict}, ... ],
          "cells":  { cell_id: {holdout_id, configuration_id, n_valid, medians, m, s,
                                valid, cv} },
          "floors": { holdout_id: {pairs, scalar_alt, scale_ref, diagnostics} },
        }

    返り値は人間可読の齟齬文字列のリスト。**空リスト = 完全一致。** 欠損・不正形は fail-closed
    で齟齬として列挙する (黙認しない)。
    """
    errors: list = []
    if type(expected_use_perf) is not bool:
        return [f"expected_use_perf が bool でない: {expected_use_perf!r}"]
    if not isinstance(artifact, Mapping):
        return ["artifact が Mapping でない"]
    receipt = artifact.get("perf_preflight")
    try:
        derived_use_perf = _perf_preflight.use_perf_from_receipt(receipt)
    except _perf_preflight.PerfPreflightError as exc:
        return [f"artifact perf_preflight が不正: {exc}"]
    if expected_use_perf is not derived_use_perf:
        return [
            "expected_use_perf が artifact receipt の再導出値と不一致 "
            f"(caller={expected_use_perf!r}, artifact={derived_use_perf!r})"
        ]
    artifact_schema = artifact.get("schema")
    key_schema = (
        _floor_contract.RESULT_SCHEMA_V5
        if artifact_schema == _floor_contract.RESULT_SCHEMA_V5
        else _floor_contract.LEGACY_RESULT_SCHEMA
    )
    try:
        expected_result_keys = _floor_contract.result_keys_for_mode(
            artifact.get("mode"), schema=key_schema, perf_preflight=receipt,
        )
    except _floor_contract.FloorContractError as exc:
        return [f"artifact result key 契約が不正: {exc}"]
    if set(artifact) != set(expected_result_keys):
        missing = sorted(set(expected_result_keys) - set(artifact))
        extra = sorted(set(artifact) - set(expected_result_keys))
        return [
            f"artifact result {'v5' if key_schema == _floor_contract.RESULT_SCHEMA_V5 else 'v4'} "
            f"exact key 集合が不一致 (欠落={missing} 余分={extra})"
        ]
    if (
        artifact_schema != _floor_contract.LEGACY_RESULT_SCHEMA
        and artifact_schema != _floor_contract.RESULT_SCHEMA_V5
    ):
        return [
            f"artifact.schema が {_floor_contract.RESULT_SCHEMA!r} でない"
        ]
    if artifact_schema == _floor_contract.LEGACY_RESULT_SCHEMA:
        if expected_attempt_registry is not None:
            return ["v4 artifact に expected_attempt_registry を指定できない"]
    else:
        from .attempt_registry_core import (
            AttemptRegistryCoreError,
            validate_attempt_registry_prefix_proof,
        )

        try:
            reported_attempt_registry = validate_attempt_registry_prefix_proof(
                artifact.get("attempt_registry")
            )
        except AttemptRegistryCoreError as exc:
            return [f"artifact.attempt_registry が不正: {exc}"]
        if (
            reported_attempt_registry["freeze_sha256"]
            != artifact["freeze_sha256"]
        ):
            return [
                "attempt_registry.freeze_sha256 が "
                "artifact.freeze_sha256 と不一致"
            ]
        if (
            reported_attempt_registry["protocol_sha256"]
            != artifact["protocol_sha256"]
        ):
            return [
                "attempt_registry.protocol_sha256 が "
                "artifact.protocol_sha256 と不一致"
            ]
        if expected_attempt_registry is None:
            return ["v5 artifact の expected_attempt_registry が必須"]
        try:
            independent_attempt_registry = validate_attempt_registry_prefix_proof(
                expected_attempt_registry
            )
        except AttemptRegistryCoreError as exc:
            return [f"expected_attempt_registry が不正: {exc}"]
        if reported_attempt_registry != independent_attempt_registry:
            return ["attempt_registry が独立 inspector の期待値と不一致"]
    if artifact.get("mode") == "official" and not derived_use_perf:
        try:
            normalized_observation = validate_floor_perf_evidence(
                artifact, artifact.get("perf_observation"), claim="throughput",
            )
        except _perf_preflight.PerfPreflightError as exc:
            return [f"artifact perf_observation が不正: {exc}"]
        if normalized_observation["preflight"] != receipt:
            return ["artifact perf_observation.preflight が perf_preflight と不一致"]
    try:
        reported_admission = _floor_contract.validate_floor_holdout_admission_receipt(
            artifact.get("holdout_admission")
        )
        live_admission = _floor_contract.validate_floor_holdout_admission_receipt(
            expected_holdout_admission
        )
    except _floor_contract.FloorContractError as exc:
        return [f"holdout_admission が不正: {exc}"]
    if reported_admission != live_admission:
        return ["holdout_admission が live inspector の期待値と不一致"]

    # --- expected_protocol のキー集合検査 (外部入力自体の完全性) ---
    if not isinstance(expected_protocol, Mapping):
        return ["expected_protocol が Mapping でない (凍結 protocol 値は入力必須)"]
    exp_missing = [k for k in _EXPECTED_PROTOCOL_KEYS if k not in expected_protocol]
    exp_extra = sorted(set(expected_protocol) - set(_EXPECTED_PROTOCOL_KEYS))
    if exp_missing:
        errors.append(f"expected_protocol: 必須キー欠損 {exp_missing}")
    if exp_extra:
        errors.append(f"expected_protocol: 余分なキー {exp_extra}")
    if errors:
        return errors
    expected_cells = expected_protocol["expected_cells"]
    if not isinstance(expected_cells, Mapping) or not expected_cells:
        return ["expected_protocol.expected_cells が空/Mapping でない (空 artifact 恒真化拒否)"]
    for holdout, configurations in expected_cells.items():
        if (not isinstance(configurations, Sequence)
                or isinstance(configurations, (str, bytes))):
            return [f"expected_cells[{holdout!r}] が配列でない"]
        sort_count = sum(configuration == "sort_best" for configuration in configurations)
        if sort_count != 1:
            return [
                f"expected_cells[{holdout!r}] の sort_best が {sort_count} 個 "
                "(ちょうど 1 個であるべき)"
            ]

    n_sessions = expected_protocol["n_sessions"]
    reps = expected_protocol["reps"]
    stock_cfg = expected_protocol["stock_configuration"]
    wired = expected_protocol["wired_min_rel_floor"]
    session_cv_max = expected_protocol["session_cv_max"]
    cell_cv_max = expected_protocol["cell_cv_max"]

    # --- artifact.config vs expected_protocol の完全一致 (α-3: 自己申告を信頼根にしない) ---
    config = artifact.get("config")
    if not isinstance(config, Mapping):
        return errors + ["artifact に config が無い (protocol 値は自己申告 + 外部照合が必須)"]
    cfg_extra = sorted(set(config) - set(_CONFIG_SCALARS))
    if cfg_extra:
        errors.append(f"config: 余分なキー {cfg_extra} (閉じた schema からの逸脱)")
    for k in _CONFIG_SCALARS:
        if k not in config:
            errors.append(f"config: 必須キー {k} が欠損")
        else:
            _cmp("config", k, config[k], expected_protocol[k], errors)
    if errors:
        return errors

    # --- sessions のパース ---
    raw_sessions = artifact.get("sessions")
    if not isinstance(raw_sessions, Sequence) or isinstance(raw_sessions, (str, bytes)):
        return ["artifact に sessions 列が無い"]
    records: list = []
    for i, d in enumerate(raw_sessions):
        if not isinstance(d, Mapping):
            errors.append(f"sessions[{i}]: dict でない")
            continue
        missing = [k for k in _REQUIRED_SESSION if k not in d]
        if missing:
            errors.append(f"sessions[{i}]: 必須キー欠損 {missing}")
            continue
        try:
            records.append((i, _record_from_mapping(d)))
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"sessions[{i}]: SessionRecord へ変換不能 ({exc})")
    if errors:
        return errors

    # --- rep 証跡 + reps 一様性 + 理由 + CV↔reason 双方向一致 ---
    for i, r in records:
        ctx = f"sessions[{i}]"
        if r.reps_expected != reps:
            errors.append(f"{ctx}: reps_expected {r.reps_expected} != expected.reps {reps}")
        raw = raw_sessions[i]
        exempt_without_measure = _rep_evidence_exemption_kind(raw) is not None
        derived_failures: Optional[int] = None
        if not exempt_without_measure:
            evidence_errors, derived_failures, derived_exec_failures, qualified = _derive_rep_integrity(
                r.rep_observations, reps=reps, expected_use_perf=expected_use_perf,
            )
            errors.extend(f"{ctx}: {error}" for error in evidence_errors)
            if r.exec_failures != derived_exec_failures:
                errors.append(
                    f"{ctx}: exec_failures 齟齬 "
                    f"(申告 {r.exec_failures} != 再導出 {derived_exec_failures})"
                )
            if (type(r.rep_integrity_failures) is not int
                    or r.rep_integrity_failures < 0):
                errors.append(
                    f"{ctx}: rep_integrity_failures が非負 exact int でない: "
                    f"{r.rep_integrity_failures!r}"
                )
            elif r.rep_integrity_failures != derived_failures:
                errors.append(
                    f"{ctx}: rep_integrity_failures 齟齬 "
                    f"(申告 {r.rep_integrity_failures} != 再導出 {derived_failures})"
                )
            if tuple(r.throughputs) != qualified:
                errors.append(
                    f"{ctx}: integrity-qualified throughputs 齟齬 "
                    f"(申告 {tuple(r.throughputs)!r} != 再導出 {qualified!r})"
                )
            if derived_failures > 0 and r.excluded_reason not in {
                    "competing_process", "launch_failure", _REASON_PARTIAL}:
                errors.append(f"{ctx}: rep integrity 違反なのに partial へ閉じていない")
            if derived_failures == 0 and raw.get("exclusion_class") == \
                    REP_INTEGRITY_EXCLUSION_CLASS:
                errors.append(f"{ctx}: 完備な証跡を rep_integrity_failure と偽除外")
            if derived_failures > 0:
                if raw.get("valid") is True:
                    errors.append(f"{ctx}: rep integrity 違反なのに valid=true")
                if raw.get("session_median") is not None:
                    errors.append(f"{ctx}: rep integrity 違反なのに session_median が非 null")
        expected_class = (
            r.excluded_reason
            if r.excluded_reason in {"competing_process", "launch_failure"}
            else REP_INTEGRITY_EXCLUSION_CLASS
            if derived_failures is not None and derived_failures > 0
            else r.excluded_reason
        )
        if raw["exclusion_class"] != expected_class:
            errors.append(
                f"{ctx}: exclusion_class 齟齬 "
                f"(申告 {raw['exclusion_class']!r} != 再導出 {expected_class!r})"
            )
        reason = r.excluded_reason
        if reason is not None and reason not in ALLOWED_EXCLUDED_REASONS:
            errors.append(f"{ctx}: excluded_reason {reason!r} が閉表 4 理由に無い")
            continue
        # 生値から必然理由を再導出 (throughput 導出可能な範囲のみ)。
        try:
            derived = assess_session(r.throughputs, reps=reps,
                                     session_cv_max=session_cv_max).required_reason
        except FloorStatsError as exc:
            errors.append(f"{ctx}: throughputs が assess 不能 ({exc})")
            continue
        if reason is None:
            # 有効主張。生値も完全・有限・CV 以下でなければ異常隠蔽/偽有効。
            if derived is not None:
                errors.append(f"{ctx}: 有効主張だが生値の必然理由は {derived!r} "
                              "(異常隠蔽/偽有効の疑い)")
        elif reason in _THROUGHPUT_DERIVABLE_REASONS:
            # throughput 導出可能理由は生値と完全一致すべき (理由すり替えの検出)。
            if derived != reason:
                errors.append(f"{ctx}: excluded_reason {reason!r} だが生値の必然理由は "
                              f"{derived!r} (理由すり替えの疑い)")
        # competing_process / launch_failure は probe/launch 起因で throughput 導出不能
        # (真正性は F7 wave の journal 突合)。ここでは検査しない。

    # --- (holdout_id, configuration_id) キーでの cell grouping + 衝突検査 (α-10) ---
    by_key: dict = {}          # (holdout, cfg) -> list[SessionRecord]
    cellid_of_key: dict = {}   # (holdout, cfg) -> cell_id
    key_of_cellid: dict = {}   # cell_id -> (holdout, cfg)
    for _, r in records:
        key = (r.holdout_id, r.configuration_id)
        by_key.setdefault(key, []).append(r)
        # 同一キー内の cell_id 一貫性。
        prev = cellid_of_key.get(key)
        if prev is None:
            cellid_of_key[key] = r.cell_id
        elif prev != r.cell_id:
            errors.append(f"cell {key}: cell_id 不一致 ({prev!r} vs {r.cell_id!r})")
        # cell_id が別 (holdout, cfg) と衝突していないか (global 再利用の拒否)。
        prevk = key_of_cellid.get(r.cell_id)
        if prevk is None:
            key_of_cellid[r.cell_id] = key
        elif prevk != key:
            errors.append(f"cell_id {r.cell_id!r} が複数座標に衝突 ({prevk} vs {key})")
    if errors:
        return errors

    # --- expected_cells との完全一致 (空 artifact / holdout 欠落 / cell 欠落の拒否, α-2) ---
    exp_key_set = set()
    for h, cfgs in expected_cells.items():
        for cfg in cfgs:
            exp_key_set.add((h, cfg))
    got_key_set = set(by_key)
    for missing in sorted(exp_key_set - got_key_set):
        errors.append(f"expected_cells: セル {missing} が artifact に無い")
    for extra in sorted(got_key_set - exp_key_set):
        errors.append(f"expected_cells: セル {extra} が expected に無い (余分)")
    if errors:
        return errors

    # --- cells の再計算と照合 ---
    reported_cells = artifact.get("cells", {})
    if not isinstance(reported_cells, Mapping):
        return ["artifact.cells が Mapping でない"]

    recomputed_cells: dict = {}   # cell_id -> CellStats
    for key, recs in by_key.items():
        cs = cell_stats(recs, n_sessions=n_sessions, reps=reps,
                        session_cv_max=session_cv_max)
        recomputed_cells[cellid_of_key[key]] = cs

    calc_ids = set(recomputed_cells)
    rep_ids = set(reported_cells)
    for extra in sorted(rep_ids - calc_ids):
        errors.append(f"cells: 申告に余分な cell_id {extra} (生データに対応セッション無し)")
    for miss in sorted(calc_ids - rep_ids):
        errors.append(f"cells: 申告に cell_id {miss} が欠損")

    for cid in sorted(calc_ids & rep_ids):
        cs = recomputed_cells[cid]
        rep = reported_cells[cid]
        ctx = f"cell {cid}"
        if not isinstance(rep, Mapping):
            errors.append(f"{ctx}: 申告が Mapping でない")
            continue
        _cmp(ctx, "holdout_id", rep.get("holdout_id"), cs.holdout_id, errors)
        _cmp(ctx, "configuration_id", rep.get("configuration_id"),
             cs.configuration_id, errors)
        _cmp(ctx, "n_valid", rep.get("n_valid"), cs.n_valid, errors)
        _cmp(ctx, "medians", _as_tuple(rep.get("medians")), cs.medians, errors)
        _cmp(ctx, "m", rep.get("m"), cs.m, errors)
        _cmp(ctx, "s", rep.get("s"), cs.s, errors)
        _cmp(ctx, "valid", rep.get("valid"), cs.valid, errors)
        _cmp(ctx, "cv", rep.get("cv"), cs.cv, errors)

    # --- floors の再計算と照合 (pairs / scalar_alt / scale_ref / machine_anomaly) ---
    reported_floors = artifact.get("floors", {})
    if not isinstance(reported_floors, Mapping):
        return errors + ["artifact.floors が Mapping でない"]

    holdouts = sorted({h for (h, _cfg) in by_key})
    extra_floors = sorted(set(reported_floors) - set(holdouts))
    if extra_floors:
        # fail-closed 対称性: 他 schema と同様、余分な holdout キーの捏造を拒否する
        # (レビュー所見: 幽霊 holdout floor の注入が素通りしていた)。
        errors.append(f"floors: 期待にない holdout キー {extra_floors}")
    for holdout_id in holdouts:
        holdout_cells = {cellid_of_key[key]: recomputed_cells[cellid_of_key[key]]
                         for key in by_key if key[0] == holdout_id}
        stock_ids = sorted({cid for cid, cs in holdout_cells.items()
                            if cs.configuration_id == stock_cfg})
        ctx = f"holdout {holdout_id}"
        if len(stock_ids) != 1:
            errors.append(f"{ctx}: stock 構成 {stock_cfg!r} のセルが {len(stock_ids)} 個 "
                          "(1 個であるべき)")
            continue
        hf = holdout_floors(holdout_cells, stock_id=stock_ids[0],
                            wired_min_rel_floor=wired, cell_cv_max=cell_cv_max)
        rep = reported_floors.get(holdout_id)
        if not isinstance(rep, Mapping):
            errors.append(f"{ctx}: floors 申告が無い/Mapping でない")
            continue
        _cmp(ctx, "pairs", _as_plain_dict(rep.get("pairs")), hf.pairs, errors)
        _cmp(ctx, "scalar_alt", rep.get("scalar_alt"), hf.scalar_alt, errors)
        _cmp(ctx, "scale_ref", rep.get("scale_ref"), hf.scale_ref, errors)
        # machine_anomaly 状態の再計算一致 (α-11: 改竄 positive control 対象)。
        rep_diag = rep.get("diagnostics")
        if not isinstance(rep_diag, Mapping):
            errors.append(f"{ctx}: diagnostics 申告が無い/Mapping でない")
        else:
            _cmp(ctx, "machine_anomaly_cells",
                 _as_list(rep_diag.get("machine_anomaly_cells")),
                 hf.diagnostics["machine_anomaly_cells"], errors)
            # diagnostics 全構造の再計算一致 (レビュー所見: cells 内訳の改竄・
            # 任意キー注入が素通りしていた)。上の個別照合は pinpoint な error 文言用。
            _cmp(ctx, "diagnostics", _norm_json(rep_diag),
                 _norm_json(hf.diagnostics), errors)
        # floors[h] 自体への余分キー注入も拒否する。
        extra_keys = sorted(set(rep) - {"pairs", "scalar_alt", "scale_ref", "diagnostics"})
        if extra_keys:
            errors.append(f"{ctx}: floors 申告に期待にないキー {extra_keys}")

    # --- binaries section の検査 (C3-6: 計測 bytes の識別と journal receipt 突合) ---
    errors.extend(_verify_binaries_section(artifact, expected_cells, expected_binaries))

    return errors


def verify_floor_artifact_with_live_admission(
        artifact: Mapping, expected_protocol: Mapping,
        expected_binaries: Optional[Mapping] = None, *, repo_root: Path,
        protocol: Mapping[str, object],
        verified_freeze_document: Mapping[str, object], freeze_sha256: str,
        manifest_sha256: str, campaign_run_id: str, run_relpath: str, mode: str,
        cells: Sequence[Mapping[str, object]],
        schedule: Sequence[Mapping[str, object]],
        sessions: Sequence[Mapping[str, object]], expected_use_perf: bool) -> list:
    """live admission を自ら検査してから pure projection verifier を実行する公開入口。

    **保証境界:** expected receipt を caller から受け取らず、共有 admission filesystem の
    現在状態を inspector で検査する。台帳を削除後に同一 bytes で再構成する攻撃への耐性は
    inspector の保証範囲外である。
    """

    from .s8b_holdout_admission import (
        FloorHoldoutEvidenceError,
        FloorHoldoutEvidenceInspection,
        inspect_floor_holdout_admission_evidence,
    )

    inspection = inspect_floor_holdout_admission_evidence(
        repo_root=Path(repo_root), protocol=protocol,
        verified_freeze_document=verified_freeze_document,
        freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
        campaign_run_id=campaign_run_id, run_relpath=run_relpath, mode=mode,
        cells=cells, schedule=schedule, sessions=sessions,
    )
    if not isinstance(inspection, FloorHoldoutEvidenceInspection):
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason="refreeze-inspection-contract-invalid",
        )
    reported_eligible_for_refreeze = artifact.get("eligible_for_refreeze")
    if (
        type(reported_eligible_for_refreeze) is bool
        and reported_eligible_for_refreeze
        != inspection.derived_eligible_for_refreeze
    ):
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason="refreeze-eligibility-mismatch",
        )

    expected_attempt_registry = None
    if (
        isinstance(artifact, Mapping)
        and artifact.get("schema") == _floor_contract.RESULT_SCHEMA_V5
    ):
        from . import attempt_registry_core as _attempt_registry_core
        from . import s8b_attempt_profile as _attempt_profile
        from . import s8b_attempt_registry as _attempt_registry

        try:
            reported_attempt_registry = (
                _attempt_registry_core.validate_attempt_registry_prefix_proof(
                    artifact.get("attempt_registry")
                )
            )
        except _attempt_registry_core.AttemptRegistryCoreError as exc:
            return [f"artifact.attempt_registry が不正: {exc}"]
        expected_binding = _attempt_profile.S8BAttemptBinding(
            freeze_sha256=freeze_sha256,
            protocol_sha256=_floor_contract.canonical_protocol_sha256(protocol),
            schedule_sha256=hashlib.sha256(
                _attempt_registry_core.canonical_json_bytes(list(schedule))
            ).hexdigest(),
        )
        expected_attempt_registry = (
            _attempt_registry.inspect_attempt_registry_prefix(
                Path(repo_root), expected_binding=expected_binding,
                row_count=reported_attempt_registry["row_count"],
                chain_head_sha256=(
                    reported_attempt_registry["chain_head_sha256"]
                ),
            )
        )
    return verify_floor_artifact(
        artifact, expected_protocol, expected_binaries=expected_binaries,
        expected_holdout_admission=inspection,
        expected_use_perf=expected_use_perf,
        expected_attempt_registry=expected_attempt_registry,
    )


def _verify_binaries_section(artifact: Mapping, expected_cells: Mapping,
                             expected_binaries: Optional[Mapping]) -> list:
    """artifact.binaries を検査する (C3-6)。

    - (holdout_id, configuration_id) の完全集合が expected_cells と一致する。
    - 各 rec の bin_hash_short が binary_sha256 の 16 文字 prefix と一致する (identity 整合)。
    - admission receipt の exact/canonical/subject 対応を常に検査する。freeze entry の
      外部権威はこの関数の責務でない。
    - expected_binaries (journal receipt 由来) が与えられれば cell_id ごとの binary_sha256 を
      完全一致で突合する (実測直前 hash との reconcile フック)。

    binaries は expected_binaries の有無にかかわらず全 expected cell をちょうど 1 件ずつ持つ。"""
    binaries = artifact.get("binaries")
    out: list = []
    if not isinstance(binaries, Mapping) or not binaries:
        return ["binaries: section が無い/空"]

    expected_cell_ids = set()
    expected_cell_count = 0
    for holdout, cfgs in expected_cells.items():
        for cfg in cfgs:
            expected_cell_ids.add(f"{holdout}::{cfg}")
            expected_cell_count += 1
    if len(expected_cell_ids) != expected_cell_count:
        out.append("binaries: expected_cells の canonical cell_id が重複")
    binary_cell_ids = set(binaries)
    if len(binaries) != expected_cell_count or binary_cell_ids != expected_cell_ids:
        missing = sorted(expected_cell_ids - binary_cell_ids)
        extra = sorted(binary_cell_ids - expected_cell_ids)
        out.append(
            "binaries: canonical cell_id 集合/件数が expected cells と不一致 "
            f"(missing={missing}, extra={extra}, got_count={len(binaries)}, "
            f"expected_count={expected_cell_count})"
        )
    for cell_id, rec in binaries.items():
        if not isinstance(rec, Mapping):
            out.append(f"binaries[{cell_id}]: rec が Mapping でない")
            continue
        expected_keys = _binary_admission.portable_built_keys_for(
            rec.get("configuration_id")
        )
        if set(rec) != set(expected_keys):
            out.append(f"binaries[{cell_id}]: exact key 集合が不一致")
            continue
        expected_cell_id = f"{rec.get('holdout_id')}::{rec.get('configuration_id')}"
        if cell_id != expected_cell_id or rec.get("cell_id") != cell_id:
            out.append(
                f"binaries[{cell_id}]: canonical cell identity が record と不一致"
            )
        bin_sha = rec.get("binary_sha256")
        bin_short = rec.get("bin_hash_short")
        if not isinstance(bin_sha, str) or len(bin_sha) != 64:
            out.append(f"binaries[{cell_id}]: binary_sha256 が 64hex でない")
        elif bin_short != bin_sha[:16]:
            out.append(f"binaries[{cell_id}]: bin_hash_short {bin_short!r} != sha256[:16]")
        try:
            _binary_admission.validate_portable_binary_record(
                rec, expected_policy=None,
                expected_ccbench_pin=artifact.get("ccbench_pin"),
                expected_cell_id=cell_id,
                expected_holdout_id=rec.get("holdout_id"),
                expected_configuration_id=rec.get("configuration_id"),
            )
        except _binary_admission.BinaryAdmissionError as exc:
            out.append(f"binaries[{cell_id}]: admission receipt が不正: {exc}")
        if expected_binaries is not None:
            exp = expected_binaries.get(cell_id)
            if not isinstance(exp, str):
                out.append(f"binaries[{cell_id}]: expected_binaries に receipt が無い")
            elif exp != bin_sha:
                out.append(f"binaries[{cell_id}]: binary_sha256 が journal receipt と不一致")
    if expected_binaries is not None:
        missing_cells = sorted(set(expected_binaries) - set(binaries))
        for m in missing_cells:
            out.append(f"binaries: journal receipt のセル {m} が artifact.binaries に無い")
    return out


def _as_tuple(v):
    """medians 申告 (list/tuple/None) を tuple/None に正規化して == 照合可能にする。"""
    if v is None:
        return None
    return tuple(v)


def _as_list(v):
    if v is None:
        return None
    return list(v)


def _as_plain_dict(v):
    if v is None:
        return None
    return dict(v)


def _norm_json(v):
    """深い構造を == 照合可能な形に正規化する (tuple→list、Mapping→dict)。
    JSON round-trip 済み申告と Python 内再計算値の型差だけを吸収し、値は変えない。"""
    if isinstance(v, Mapping):
        return {str(k): _norm_json(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_norm_json(x) for x in v]
    return v
