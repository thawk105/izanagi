# -*- coding: utf-8 -*-
"""s8b_floor_stats (formula v2) の mutation-killing golden テスト。

**独立 oracle 契約 (β-12/δ-16):** 式の golden は production を import しない stdlib-only の
reference calculator と手導出 literal で固定する (`_ref_*`)。production を走らせて出力を貼る
堕落を避ける。各テストがどの mutant を殺すかはコメントに明記する:
  median↔mean / stdev(n-1)↔pstdev(n) / CV 判定 >↔>= / 異常ゲート除去 / null skip /
  stock anomaly 全 pair 伝播 / pairs キー (configuration_id↔cell_id) 混同。

**閾値の厳密算術 (α-9):** [90,90,100,110,110] は CV ちょうど 10% で異常でない (厳密超過)、
[89,89,100,111,111] は超過。尺度同値 [0.9,0.9,1.0,1.1,1.1] は IEEE-754 の 2 進表現が
名目 10% を僅かに超えるため Fraction 意味論で決定的に異常となる (float 直接比較の非決定ではなく
再現可能な確定値である点を固定する)。

**テストデータは synthetic 軸のみ (δ-15):** holdout 実軸 literal を新規に書かない。
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import asdict
from fractions import Fraction

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign.s8b_floor_stats import (  # noqa: E402
    ALLOWED_EXCLUDED_REASONS,
    FORMULA_ID,
    CellStats,
    FloorStatsError,
    SessionRecord,
    assess_session,
    cell_cv_exceeds,
    cell_stats,
    holdout_floors,
    session_median,
    verify_floor_artifact,
)


# ---------------------------------------------------------------------------
# stdlib-only 独立 reference calculator (production を import しない, β-12)
# ---------------------------------------------------------------------------
def _ref_mean(xs):
    return sum(xs) / len(xs)


def _ref_median(xs):
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _ref_var_n1(xs):
    m = _ref_mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def _ref_stdev_n1(xs):
    return math.sqrt(_ref_var_n1(xs))


def _ref_cv_exceeds(xs, tstr):
    """CV > T を Fraction 厳密で独立判定 (production の _cv_exceeds とは別実装)。"""
    fr = [Fraction(v) for v in xs]
    n = len(fr)
    mean = sum(fr, Fraction(0)) / n
    var = sum((x - mean) ** 2 for x in fr) / (n - 1)
    T = Fraction(tstr)
    return var > T * T * mean * mean


def _ref_u_noise(s_c, s_stock):
    return math.sqrt(s_c ** 2 + s_stock ** 2)


# ---------------------------------------------------------------------------
# テストヘルパ
# ---------------------------------------------------------------------------
def _sess(cell_id, seq, throughputs, *, reps_expected=5, holdout_id="H",
          configuration_id="cfg", exec_failures=0, excluded_reason=None, retry=False):
    return SessionRecord(
        cell_id=cell_id, holdout_id=holdout_id, configuration_id=configuration_id,
        seq=seq, throughputs=tuple(throughputs), reps_expected=reps_expected,
        exec_failures=exec_failures, excluded_reason=excluded_reason, retry=retry)


def _flat(cell_id, seq, median_value, **kw):
    """median==median_value・CV=0 の完全 5-rep session (定数列)。"""
    return _sess(cell_id, seq, [median_value] * 5, **kw)


def _cell(cell_id, *, medians, valid=True, holdout_id="H", configuration_id="cfg"):
    """指定 medians から CellStats を組む (m/s/cv は reference calculator で導出)。"""
    medians = tuple(medians)
    n = len(medians)
    m = _ref_median(medians) if n >= 1 else None
    s = _ref_stdev_n1(medians) if n >= 2 else None
    cv = (s / _ref_mean(medians)) if (s is not None and _ref_mean(medians) > 0) else None
    return CellStats(cell_id=cell_id, holdout_id=holdout_id,
                     configuration_id=configuration_id, n_valid=n, medians=medians,
                     m=m, s=s, valid=valid, cv=cv, notes=())


# ---------------------------------------------------------------------------
# FORMULA_ID / 閉表
# ---------------------------------------------------------------------------
def test_formula_id_is_v2():
    # 式の版は v2 (block/delta_c 廃止, F1 裁定)。
    assert FORMULA_ID == "s8b-floor-stats/v2"


def test_allowed_reasons_closed_table_order():
    # 閉じた 4 理由 + 固定順 (performance_anomaly は 4 行目)。
    assert ALLOWED_EXCLUDED_REASONS == (
        "competing_process", "launch_failure",
        "nonfinite_or_partial_output", "performance_anomaly")


# ---------------------------------------------------------------------------
# assess_session — Fraction 厳密境界・完全性・構造化エラー
# ---------------------------------------------------------------------------
def test_assess_cv_boundary_exactly_ten_percent_not_anomaly():
    # [90,90,100,110,110]: mean=100, var(n-1)=100, T^2*mean^2=0.01*10000=100。
    # 100 > 100 は偽 → 異常でない。>= mutant はここで赤 (>↔>= を殺す)。
    a = assess_session([90, 90, 100, 110, 110], reps=5, session_cv_max="0.10")
    assert a.required_reason is None
    assert a.median == 100
    assert _ref_cv_exceeds([90, 90, 100, 110, 110], "0.10") is False


def test_assess_cv_just_over_ten_percent_is_anomaly():
    # [89,89,100,111,111]: var(n-1)=121 > 100 → performance_anomaly。ゲート除去 mutant を殺す。
    a = assess_session([89, 89, 100, 111, 111], reps=5, session_cv_max="0.10")
    assert a.required_reason == "performance_anomaly"
    assert a.median is None                      # 異常 session は median を作らない
    assert _ref_cv_exceeds([89, 89, 100, 111, 111], "0.10") is True


def test_assess_scale_equivalent_vector_is_deterministic():
    # 尺度同値 [0.9,0.9,1.0,1.1,1.1] は IEEE-754 表現が名目 10% を僅かに超えるため
    # Fraction 意味論で確定的に異常。float 直接比較の非決定ではなく再現可能な確定値。
    v = [0.9, 0.9, 1.0, 1.1, 1.1]
    a1 = assess_session(v, reps=5, session_cv_max="0.10")
    a2 = assess_session(list(v), reps=5, session_cv_max="0.10")
    assert a1.required_reason == "performance_anomaly"   # 決定的
    assert a2.required_reason == a1.required_reason       # 再現的
    assert _ref_cv_exceeds(v, "0.10") is True


def test_assess_valid_returns_median_and_cv():
    # 完全・低 CV だが右に歪んだ列 [100,100,100,100,105]: median=100, mean=101 (cv≈0.022<10%)。
    a = assess_session([100, 100, 100, 100, 105], reps=5, session_cv_max="0.10")
    assert a.median == 100                         # median (mean=101) — median↔mean を殺す
    assert a.required_reason is None
    assert a.cv is not None and a.cv < 0.10


def test_assess_partial_reps_is_nonfinite_or_partial():
    # 4/5 rep → 完全性欠如 → nonfinite_or_partial_output (CV より優先)。
    a = assess_session([1, 2, 3, 4], reps=5, session_cv_max="0.10")
    assert a.required_reason == "nonfinite_or_partial_output"
    assert a.median is None and a.cv is None


def test_assess_nonfinite_and_nonpositive_are_partial():
    for bad in ([1, 2, 3, 4, math.inf], [1, 2, 3, 4, math.nan],
                [1, 2, 3, 4, 0.0], [1, 2, 3, 4, -5.0]):
        a = assess_session(bad, reps=5, session_cv_max="0.10")
        assert a.required_reason == "nonfinite_or_partial_output"


def test_assess_rejects_bool_and_nonnumeric_as_structured_error():
    # bool は int サブクラスだが型違反 = 構造化エラー (α-7)。
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, True], reps=5, session_cv_max="0.10")
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, "5"], reps=5, session_cv_max="0.10")


def test_assess_rejects_bad_reps_and_threshold():
    with pytest.raises(FloorStatsError):
        assess_session([1, 2], reps=1, session_cv_max="0.10")      # reps<2
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=True, session_cv_max="0.10")  # bool reps
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max=0.10)  # 非文字列閾値
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max="0")   # (0,1] 外
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max="1.5")  # >1


# ---------------------------------------------------------------------------
# session_median — assess_session への一元化 (α-8)
# ---------------------------------------------------------------------------
def test_session_median_valid_and_invalidations():
    good = _flat("c", 0, 100)
    assert session_median(good, reps=5, session_cv_max="0.10") == 100
    # excluded_reason / exec_failures / CV 異常はいずれも None。
    assert session_median(_flat("c", 0, 100, excluded_reason="competing_process"),
                          reps=5, session_cv_max="0.10") is None
    assert session_median(_flat("c", 0, 100, exec_failures=1),
                          reps=5, session_cv_max="0.10") is None
    anomaly = _sess("c", 0, [89, 89, 100, 111, 111])  # CV>10%
    assert session_median(anomaly, reps=5, session_cv_max="0.10") is None


# ---------------------------------------------------------------------------
# cell_stats — median/stdev golden・有効性・座標一貫性
# ---------------------------------------------------------------------------
def test_cell_stats_golden_median_and_stdev():
    # 4 session medians = [100,100,100,200] (定数列で CV=0)。
    #   m = median = 100  (mean=125; median↔mean を殺す)
    #   s = stdev(n-1): mean=125, dev=[-25,-25,-25,75], Σsq=7500, /3=2500, sqrt=50
    #       (pstdev(n) なら sqrt(7500/4)=43.30…; stdev(n-1)↔pstdev(n) を殺す)
    #   cv = 50/125 = 0.4
    recs = [_flat("c", 0, 100), _flat("c", 1, 100),
            _flat("c", 2, 100), _flat("c", 3, 200)]
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is True and cs.n_valid == 4
    assert cs.m == _ref_median([100, 100, 100, 200]) == 100
    assert math.isclose(cs.s, _ref_stdev_n1([100, 100, 100, 200])) and math.isclose(cs.s, 50.0)
    assert math.isclose(cs.cv, 0.4)
    assert cs.medians == (100, 100, 100, 200)
    assert cs.holdout_id == "H" and cs.configuration_id == "cfg"


def test_cell_stats_invalid_when_valid_count_short():
    # anomaly session を 1 本混ぜ有効数を減らす → n_valid(3) != n_sessions(4) → 無効。
    recs = [_flat("c", 0, 100), _flat("c", 1, 100), _flat("c", 2, 100),
            _sess("c", 3, [89, 89, 100, 111, 111])]  # CV 異常 → 除外
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is False
    assert cs.n_valid == 3
    # 異常 session の median 101 は母集団に入らない (fail-closed)。
    assert 101 not in cs.medians


def test_cell_stats_invalid_when_configuration_mixed():
    # 同一 cell_id に別 configuration_id が混入 → 座標不一致 → 無効 (混入検知)。
    recs = [_flat("c", 0, 100, configuration_id="cfgA"),
            _flat("c", 1, 100, configuration_id="cfgB"),
            _flat("c", 2, 100, configuration_id="cfgA"),
            _flat("c", 3, 100, configuration_id="cfgA")]
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is False


# ---------------------------------------------------------------------------
# cell_cv_exceeds — machine_anomaly 判定の Fraction 厳密境界
# ---------------------------------------------------------------------------
def test_cell_cv_boundary_exactly_fifteen_percent_not_anomaly():
    # [85,100,115]: var(n-1)=225, T^2*mean^2=0.0225*10000=225 → 225>225 偽 → 非異常。
    assert cell_cv_exceeds([85, 100, 115], "0.15") is False
    assert _ref_cv_exceeds([85, 100, 115], "0.15") is False


def test_cell_cv_just_over_fifteen_percent_is_anomaly():
    # [84,100,116]: var(n-1)=256 > 225 → 異常。
    assert cell_cv_exceeds([84, 100, 116], "0.15") is True
    assert _ref_cv_exceeds([84, 100, 116], "0.15") is True


# ---------------------------------------------------------------------------
# holdout_floors — formula v2 支配関係・fail-closed・machine_anomaly
# ---------------------------------------------------------------------------
def test_floor_u_noise_dominates():
    # stock medians [97,100,103] → s=3, m=100 (cv=0.03<15%)。
    # c medians [96,100,104] → s=4 (cv=0.04)。u_noise=sqrt(16+9)=5, rel=0.01*100=1 → floor=5。
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], _ref_u_noise(4.0, 3.0)) and math.isclose(
        hf.pairs["variant_A"], 5.0)
    # pairs のキーは configuration_id であって cell_id ではない (key 混同 mutant を殺す)。
    assert "variant_A" in hf.pairs and "c" not in hf.pairs
    assert math.isclose(hf.scalar_alt, 5.0)
    assert hf.scale_ref == 100


def test_floor_wired_min_dominates():
    # u_noise 小・rel 大: stock/c medians [99,100,101] → s=1。u_noise=sqrt(2)=1.414。
    # wired=0.05, m_stock=100 → rel=5 → floor=max(1.414,5)=5。
    stock = _cell("stock", medians=[99, 100, 101], configuration_id="stock_common")
    c = _cell("c", medians=[99, 100, 101], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.05, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], 5.0)


def test_floor_stock_invalid_nulls_whole_holdout():
    stock = _cell("stock", medians=[97, 100, 103], valid=False,
                  configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.scalar_alt is None and hf.scale_ref is None


def test_floor_cell_invalid_nulls_only_its_pair():
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c1 = _cell("c1", medians=[96, 100, 104], configuration_id="variant_A")   # floor 5
    c2 = _cell("c2", medians=[96, 100, 104], valid=False, configuration_id="variant_B")
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], 5.0)
    assert hf.pairs["variant_B"] is None
    # scalar_alt は c2 の null で veto (null skip mutant を殺す)。
    assert hf.scalar_alt is None
    assert hf.scale_ref == 100


def test_floor_scalar_alt_is_max_when_all_valid():
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c1 = _cell("c1", medians=[92, 100, 108], configuration_id="variant_A")  # s=8 u_noise=sqrt(64+9)
    c2 = _cell("c2", medians=[96, 100, 104], configuration_id="variant_B")  # s=4 u_noise=5
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], _ref_u_noise(8.0, 3.0))
    assert math.isclose(hf.pairs["variant_B"], 5.0)
    assert math.isclose(hf.scalar_alt, _ref_u_noise(8.0, 3.0))   # max


def test_floor_machine_anomaly_nulls_nonstock_pair():
    # c のセル間 CV>15% → 当該 pair null + diagnostics.machine_anomaly_cells に載る。
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    anom = _cell("c", medians=[70, 100, 130], configuration_id="variant_A")  # cv=0.3
    hf = holdout_floors({"stock": stock, "c": anom}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.diagnostics["machine_anomaly_cells"] == ["c"]
    assert hf.diagnostics["cells"]["c"]["machine_anomaly"] is True


def test_floor_stock_machine_anomaly_nulls_whole_holdout():
    # stock のセル間 CV>15% → 全 pair / scalar_alt / scale_ref すべて null (α-11, stock 伝播)。
    stock = _cell("stock", medians=[70, 100, 130], configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.scalar_alt is None
    assert hf.scale_ref is None                        # scale_ref も消える (異常 stock 値を消費させない)
    assert "stock" in hf.diagnostics["machine_anomaly_cells"]


# ---------------------------------------------------------------------------
# verify_floor_artifact — 内部整合再計算 + expected_protocol 照合 + 改竄検出
# ---------------------------------------------------------------------------
def _honest_artifact():
    """honest な生成器を模した整合 artifact と対応する expected_protocol を組む (synthetic 軸)。"""
    holdout = "H1"
    stock_cfg = "stock_common"
    va, vb = "variant_A", "variant_B"
    stock_cell = f"{holdout}::{stock_cfg}"
    va_cell = f"{holdout}::{va}"
    vb_cell = f"{holdout}::{vb}"
    n_sessions, reps = 4, 5

    def mk(cell, cfg, seq, median):
        return _sess(cell, seq, [median] * reps, holdout_id=holdout,
                     configuration_id=cfg, reps_expected=reps)

    records = []
    for seq, mval in enumerate([98, 100, 100, 102]):        # stock medians, s>0, cv 低
        records.append(mk(stock_cell, stock_cfg, seq, mval))
    for seq, mval in enumerate([148, 150, 150, 152]):        # variant_A
        records.append(mk(va_cell, va, seq, mval))
    for seq, mval in enumerate([118, 120, 120, 122]):        # variant_B
        records.append(mk(vb_cell, vb, seq, mval))

    by_cell = {}
    for r in records:
        by_cell.setdefault(r.cell_id, []).append(r)
    cells = {cid: asdict(cell_stats(recs, n_sessions=n_sessions, reps=reps,
                                    session_cv_max="0.10"))
             for cid, recs in by_cell.items()}

    cell_objs = {cid: cell_stats(recs, n_sessions=n_sessions, reps=reps,
                                 session_cv_max="0.10")
                 for cid, recs in by_cell.items()}
    hf = holdout_floors(cell_objs, stock_id=stock_cell, wired_min_rel_floor=0.01,
                        cell_cv_max="0.15")
    floors = {holdout: asdict(hf)}

    config = {"formula": FORMULA_ID, "n_sessions": n_sessions, "reps": reps,
              "stock_configuration": stock_cfg, "wired_min_rel_floor": 0.01,
              "session_cv_max": "0.10", "cell_cv_max": "0.15"}
    artifact = {"config": config,
                "sessions": [asdict(r) for r in records],
                "cells": cells, "floors": floors}
    expected = {"formula": FORMULA_ID, "n_sessions": n_sessions, "reps": reps,
                "stock_configuration": stock_cfg, "wired_min_rel_floor": 0.01,
                "session_cv_max": "0.10", "cell_cv_max": "0.15",
                "expected_cells": {holdout: [stock_cfg, va, vb]}}
    return artifact, expected, holdout, stock_cell, va_cell, va


def test_verify_accepts_consistent_artifact():
    artifact, expected, *_ = _honest_artifact()
    assert verify_floor_artifact(artifact, expected) == []


def test_verify_detects_tampered_floor_pair():
    # freeze 向き pair (configuration_id キー) を +1 改竄 → 再計算不一致。
    artifact, expected, holdout, _, _, va = _honest_artifact()
    artifact["floors"][holdout]["pairs"][va] += 1.0
    errs = verify_floor_artifact(artifact, expected)
    assert any("pairs" in e for e in errs)


def test_verify_rejects_ghost_holdout_floor():
    # sessions に現れない幽霊 holdout の floors 注入を拒否 (fail-closed 対称性、
    # レビュー所見: 以前は素通りしていた)。
    artifact, expected, *_ = _honest_artifact()
    artifact["floors"]["ghost-holdout"] = {
        "pairs": {"variant_a": 0.0001}, "scalar_alt": 0.0001, "scale_ref": 1.0,
        "diagnostics": {"machine_anomaly_cells": []},
    }
    errs = verify_floor_artifact(artifact, expected)
    assert any("期待にない holdout" in e for e in errs)


def test_verify_detects_diagnostics_cells_tamper_and_injected_key():
    # diagnostics の cells 内訳改竄・任意キー注入を拒否 (レビュー所見: machine_anomaly_cells
    # だけの照合では素通りしていた)。
    artifact, expected, holdout, *_ = _honest_artifact()
    tampered = dict(artifact["floors"][holdout]["diagnostics"])
    tampered["injected"] = "malicious note"
    artifact["floors"][holdout]["diagnostics"] = tampered
    errs = verify_floor_artifact(artifact, expected)
    assert any("diagnostics" in e for e in errs)


def test_verify_rejects_extra_key_in_floors_entry():
    # floors[h] 直下への余分キー注入を拒否。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["floors"][holdout]["bonus"] = 1
    errs = verify_floor_artifact(artifact, expected)
    assert any("期待にないキー" in e for e in errs)


def test_verify_detects_swapped_throughputs():
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["throughputs"] = [999999.0] * 5
    assert verify_floor_artifact(artifact, expected) != []


# --- 改竄 positive control 群 (verifier mutant を殺す) ---
def test_verify_rejects_empty_artifact():
    # 空 sessions/cells/floors + config だけ → expected_cells 不一致で恒真化を拒否 (α-2)。
    _, expected, *_ = _honest_artifact()
    empty = {"config": {"formula": FORMULA_ID, "n_sessions": 4, "reps": 5,
                        "stock_configuration": "stock_common", "wired_min_rel_floor": 0.01,
                        "session_cv_max": "0.10", "cell_cv_max": "0.15"},
             "sessions": [], "cells": {}, "floors": {}}
    errs = verify_floor_artifact(empty, expected)
    assert any("expected_cells" in e for e in errs)


def test_verify_rejects_missing_holdout_cell():
    # variant_B のセッションを丸ごと削除 → expected_cells 欠落で拒否。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["sessions"] = [s for s in artifact["sessions"]
                            if s["configuration_id"] != "variant_B"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("expected_cells" in e for e in errs)


def test_verify_rejects_threshold_selfreport_mismatch():
    # config の閾値を緩めても expected_protocol (凍結値) と不一致で拒否 (α-3)。
    artifact, expected, *_ = _honest_artifact()
    artifact["config"]["cell_cv_max"] = "1.0"
    errs = verify_floor_artifact(artifact, expected)
    assert any("cell_cv_max" in e for e in errs)


def test_verify_rejects_reps_selfreport_downgrade():
    # 4/5 rep の session を reps_expected=4 と自己申告しても expected.reps=5 と不一致で拒否 (α-4)。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["throughputs"] = [100.0, 100.0, 100.0, 100.0]
    artifact["sessions"][0]["reps_expected"] = 4
    errs = verify_floor_artifact(artifact, expected)
    assert any("reps_expected" in e for e in errs)


def test_verify_detects_false_exclusion():
    # 良い session (CV 0) を performance_anomaly と偽ラベル → 生値と理由が食い違う (偽除外, α-5)。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["excluded_reason"] = "performance_anomaly"
    errs = verify_floor_artifact(artifact, expected)
    assert any("理由すり替え" in e for e in errs)


def test_verify_detects_anomaly_hiding():
    # CV 異常な生値を持つ session を有効 (excluded_reason=None) と主張 → 異常隠蔽 (α-5)。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    for s in artifact["sessions"]:
        if s["seq"] == 0 and s["cell_id"] == stock_cell:
            s["throughputs"] = [89.0, 89.0, 100.0, 111.0, 111.0]  # CV>10%
            s["excluded_reason"] = None
    errs = verify_floor_artifact(artifact, expected)
    assert any("異常隠蔽" in e for e in errs)


def test_verify_detects_reason_swap_to_partial():
    # CV 異常 (完全 5-rep) を nonfinite_or_partial_output と誤ラベル → throughput 導出理由と不一致。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    for s in artifact["sessions"]:
        if s["seq"] == 0 and s["cell_id"] == stock_cell:
            s["throughputs"] = [89.0, 89.0, 100.0, 111.0, 111.0]
            s["excluded_reason"] = "nonfinite_or_partial_output"
    errs = verify_floor_artifact(artifact, expected)
    assert any("理由すり替え" in e for e in errs)


def test_verify_rejects_unknown_reason():
    # 閉表外の理由は拒否。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["excluded_reason"] = "orphan_detected"
    errs = verify_floor_artifact(artifact, expected)
    assert any("閉表" in e for e in errs)


def test_verify_detects_diagnostics_machine_anomaly_tamper():
    # diagnostics の machine_anomaly_cells を捏造 → 再計算と不一致 (α-11 改竄 positive control)。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["floors"][holdout]["diagnostics"]["machine_anomaly_cells"] = ["H1::variant_A"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("machine_anomaly_cells" in e for e in errs)


def test_verify_detects_cell_stat_tamper():
    # 申告 cell の m を書き換え → 再計算と不一致。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    artifact["cells"][stock_cell]["m"] += 7.0
    errs = verify_floor_artifact(artifact, expected)
    assert any(stock_cell in e and "m" in e for e in errs)


def test_verify_rejects_cellid_collision_across_coords():
    # 同一 cell_id を別 (holdout, configuration) に再利用 → global 衝突拒否 (α-10)。
    artifact, expected, holdout, stock_cell, va_cell, va = _honest_artifact()
    # variant_A の 1 セッションの座標だけ別 holdout に変え cell_id は据え置き。
    for s in artifact["sessions"]:
        if s["cell_id"] == va_cell:
            s["holdout_id"] = "H2"
            break
    errs = verify_floor_artifact(artifact, expected)
    assert any("衝突" in e or "不一致" in e for e in errs)


def test_verify_rejects_missing_expected_protocol_key():
    artifact, expected, *_ = _honest_artifact()
    del expected["cell_cv_max"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("expected_protocol" in e for e in errs)


def test_verify_rejects_missing_config():
    artifact, expected, *_ = _honest_artifact()
    del artifact["config"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("config" in e for e in errs)
