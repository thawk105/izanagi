# -*- coding: utf-8 -*-
"""8b 結合 judge (§6 判定表) の三値・同一 holdout 束縛・tie 写像を検査する。

fixture は workload 値を持たず opaque な holdout ID (h1/h2) と choice_id (c01..c06) だけを
使う。判定表の 3 条件を静止 JSON リテラルにせず、成立/不成立/判定不能の各代表を構成する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCH))

from campaign import s8b_verdict as verdict  # noqa: E402


H1, H2 = "h1", "h2"
DERANGEMENT = {H1: H2, H2: H1}
# 凍結 holdout 集合 (裁定 5 項 1 の全称量化の領域)。judge_combined に必ず渡す。
EXPECTED = frozenset({H1, H2})


def make_prediction(holdouts: dict) -> dict:
    """holdouts = {h: {"on":c|None, "off":c|None, "swapped":c|None}} から予測文書を作る。"""
    rows = []
    for holdout_id, arms in holdouts.items():
        for arm in ("on", "off", "swapped"):
            choice = arms.get(arm)
            rows.append({
                "target_holdout": holdout_id,
                "arm": arm,
                "choice_id": choice,
                "status": "valid" if choice is not None else "invalid",
            })
    on_choice = {h: holdouts[h].get("on") for h in holdouts}
    expectations = [
        {"target_holdout": target,
         "source_on_holdout": DERANGEMENT[target],
         "expected_choice_id": on_choice.get(DERANGEMENT[target])}
        for target in holdouts
    ]
    return {
        "schema_version": verdict.PREDICTION_SCHEMA,
        "body_sha256": "a" * 64,
        "selector_basis_sha256": "b" * 64,
        "derangement": dict(DERANGEMENT),
        "rows": rows,
        "swapped_follow_expectations": expectations,
    }


def make_oracle(holdouts: dict) -> dict:
    """holdouts = {h: {"verdict":..., "configs": {c: median|dict}}} から oracle verdict を作る。"""
    out_holdouts = {}
    for holdout_id, spec in holdouts.items():
        configurations = {}
        for config_id, cell in spec.get("configs", {}).items():
            if isinstance(cell, dict):
                configurations[config_id] = dict(cell)
            else:
                configurations[config_id] = {
                    "status": "eligible",
                    "median_of_medians": float(cell),
                    "trial_medians": [float(cell)],
                    "reasons": [],
                }
        out_holdouts[holdout_id] = {
            "verdict": spec["verdict"],
            "winner_configuration_id": spec.get("winner"),
            "tied_configuration_ids": spec.get("tied", []),
            "configurations": configurations,
            "reasons": [],
        }
    return {
        "schema_version": verdict.ORACLE_SCHEMA,
        "manifest_sha256": "manifest-sha",
        "n_per_cell": 2,
        "status": "determinate",
        "reasons": [],
        "holdouts": out_holdouts,
    }


def _cond(result: dict, name: str) -> str:
    return result["conditions"][name]["verdict"]


# ---- 条件 1: on/off 予測差 ------------------------------------------------

def test_condition1_holds_when_a_holdout_differs():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS


def test_condition1_refuted_when_all_holdouts_identical():
    prediction = make_prediction({
        H1: {"on": "c06", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "on_off_prediction_difference") == verdict.REFUTED


def test_condition1_indeterminate_when_missing_and_no_difference():
    # h1 の on が invalid (null) で欠測、h2 は同一予測 → 全同一を確定できない。
    prediction = make_prediction({
        H1: {"on": None, "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "on_off_prediction_difference") == verdict.INDETERMINATE


# ---- 条件 2: swapped 追従 (両 holdout 必須) --------------------------------

def test_condition2_holds_when_both_holdouts_follow():
    # on[h1]=c01, on[h2]=c02。swap 追従: swapped[h1]=on[h2]=c02, swapped[h2]=on[h1]=c01。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "swapped_follow") == verdict.HOLDS


def test_condition2_refuted_when_one_holdout_does_not_follow():
    # h1 の swapped が期待 (c02) と不一致。データは完全 → 不成立。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c03"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "swapped_follow") == verdict.REFUTED


def test_condition2_indeterminate_when_a_swapped_cell_is_missing():
    # h1 の swapped が invalid (null)。両 holdout 必須なので判定不能へ倒す。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": None},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE


# ---- 条件 3: oracle floor 超 (方向付き) -----------------------------------

def test_condition3_holds_when_directional_diff_exceeds_floor():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    # oracle(on=c01)=100 − oracle(off=c06)=50 = 50 > floor 10。
    assert _cond(result, "oracle_floor_exceeded") == verdict.HOLDS


def test_condition3_refuted_when_diff_within_floor():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 55.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    # h1: 55 − 50 = 5 ≤ 10、h2: on==off → 0 ≤ floor。両者確定不成立。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED


def test_condition3_refuted_directionally_when_off_beats_on():
    # 絶対差なら成立するが、方向付きなので off が優る場合は不成立。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    # h1: 10 − 100 = −90 は floor 10 を超えない (方向付き)。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED


def test_condition3_indeterminate_when_floor_missing():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    # h1 の floor を渡さない → floor 未確定 → 判定不能へ。h2 は on==off で不成立。
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H2: 10.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "oracle_floor_exceeded") == verdict.INDETERMINATE


@pytest.mark.parametrize("bad_floor", [0.0, -5.0, float("inf"), True])
def test_condition3_indeterminate_when_floor_is_not_positive_finite(bad_floor):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: bad_floor, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


# ---- tie 写像: oracle exact tie → oracle 非一意 → 判定不能 ------------------

def test_oracle_exact_tie_maps_to_indeterminate():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    # h1 は determinate な exact tie。judge_oracle 側は status=determinate/verdict=tie。
    oracle = make_oracle({
        H1: {"verdict": "tie", "tied": ["c01", "c06"],
             "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE
    assert _cond(result, "oracle_floor_exceeded") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


def test_oracle_indeterminate_holdout_maps_to_indeterminate():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "indeterminate", "configs": {}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


def test_disqualified_predicted_config_is_indeterminate():
    # on 予測構成が correctness-red で disqualified → 比較不能 → 判定不能。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {
            "c01": {"status": "disqualified", "median_of_medians": None,
                    "trial_medians": [], "reasons": []},
            "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


# ---- 同一 holdout 束縛の反例 ----------------------------------------------

def test_same_holdout_binding_refutes_cross_holdout_evidence():
    """予測差 (h1) と大きな oracle 差 (h2) が別 holdout なら結論は成立しない。

    独立評価や winner ベースの (誤った) 実装なら成立にし得る反例。正しい結合 judge は
    「予測が異なる」holdout と「on/off 予測構成の floor 超」holdout が同一でない限り
    結論を成立にしない。
    """
    prediction = make_prediction({
        # h1: 予測が異なる (on!=off) が oracle 差は floor 未満。
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        # h2: 予測は同一 (on==off=c06)。
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        # h1: on(c01) と off(c06) は同値 → floor 超えない。
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 100.0}},
        # h2: 非予測構成 c01 が大差で勝つが、on/off 予測構成はどちらも c06。
        H2: {"verdict": "unique-best",
             "winner": "c01", "configs": {"c01": 500.0, "c06": 100.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 5.0, H2: 5.0},
        expected_holdouts=EXPECTED)

    # 条件 1 は成立 (h1 で予測差)、条件 2 は成立 (swap 追従) だが…
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    # …条件 3 は on/off 予測構成の差なので h2 の勝者 c01 を使わず、両 holdout で不成立。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED
    assert result["holdouts"][H2]["oracle_floor_exceeded"] == verdict.REFUTED
    # 同一 holdout で「予測差かつ floor 超」が成立しないため結論は不成立。
    assert result["same_holdout_coupled_verdict"] == verdict.REFUTED
    assert result["status"] == verdict.REFUTED


# ---- 結論の連言 (成立の代表) ----------------------------------------------

def test_conclusion_holds_when_all_conditions_hold_on_same_holdout():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    assert _cond(result, "oracle_floor_exceeded") == verdict.HOLDS
    assert result["same_holdout_coupled_verdict"] == verdict.HOLDS
    assert result["status"] == verdict.HOLDS


def test_conclusion_indeterminate_propagates_from_a_condition():
    # swapped 欠測 → 条件 2 判定不能 → 結論へ伝播。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": None},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


# ---- 構造破綻の fail-closed --------------------------------------------------

def test_malformed_prediction_is_fully_indeterminate():
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction={"schema_version": "wrong", "rows": "not-a-list"},
        oracle=oracle, floors={H1: 10.0}, expected_holdouts=EXPECTED)
    assert result["status"] == verdict.INDETERMINATE
    for name in ("on_off_prediction_difference", "swapped_follow",
                 "oracle_floor_exceeded"):
        assert _cond(result, name) == verdict.INDETERMINATE
    assert result["reasons"]


def test_evidence_pointers_are_recorded():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    floor_ev = result["conditions"]["oracle_floor_exceeded"]["evidence"]
    assert floor_ev["prediction_body_sha256"] == "a" * 64
    assert floor_ev["oracle_manifest_sha256"] == "manifest-sha"
    assert floor_ev["floors"] == {H1: 10.0, H2: 10.0}
    pred_ev = result["conditions"]["on_off_prediction_difference"]["evidence"]
    assert pred_ev["selector_basis_sha256"] == "b" * 64


# ---- 裁定 5 項 1: 両 holdout 必須の基数下限 (所見 1 の回帰) --------------------

def _single_holdout_self_consistent() -> dict:
    """凍結集合の片側 (h1) だけを含み、その holdout 内では全条件が自己整合に成立する予測。

    swapped_follow_expectations を swapped 予測へ一致させて condition2 を holdout 単位で成立に
    仕立ててある。基数下限がなければ全称量化が実質 1 標本へ退化し conclusion=HOLDS になる
    (裁定 5 項 1 が禁じた degenerate fail-open)。
    """
    return {
        "schema_version": verdict.PREDICTION_SCHEMA,
        "body_sha256": "a" * 64,
        "selector_basis_sha256": "b" * 64,
        "derangement": {H1: H2, H2: H1},
        "rows": [
            {"target_holdout": H1, "arm": "on", "choice_id": "c01", "status": "valid"},
            {"target_holdout": H1, "arm": "off", "choice_id": "c06", "status": "valid"},
            {"target_holdout": H1, "arm": "swapped", "choice_id": "c02", "status": "valid"},
        ],
        # swapped==expected に仕立てて追従を holdout 単位で成立させる (自己整合な改竄形)。
        "swapped_follow_expectations": [
            {"target_holdout": H1, "source_on_holdout": H2, "expected_choice_id": "c02"},
        ],
    }


def test_single_holdout_prediction_cannot_conclude_holds():
    # 片側 holdout だけで全条件成立でも、両 holdout 必須により結論は成立しない。
    prediction = _single_holdout_self_consistent()
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0},
        expected_holdouts=EXPECTED)

    # 全称量化の領域は凍結集合 {h1, h2}。h2 が欠けるため成立にはできない。
    assert result["status"] != verdict.HOLDS
    assert result["status"] == verdict.INDETERMINATE
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert any(reason["code"] == "missing-holdout" for reason in result["reasons"])


def test_single_holdout_would_hold_without_cardinality_guard():
    """基数下限が無い (領域 = present holdout) と仮定した場合は HOLDS になることの明示。

    expected_holdouts を実際に存在する片側 {h1} に縮めると領域退化が起き結論が成立する。
    これは所見 1 の degenerate fail-open が『領域を present holdout から採ること』に由来する
    ことの反例であり、上のテストが恒真でない (領域を凍結集合に固定して初めて塞げる) 証拠。
    """
    prediction = _single_holdout_self_consistent()
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    degenerate = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0},
        expected_holdouts=frozenset({H1}))
    assert degenerate["status"] == verdict.HOLDS


def test_unexpected_holdout_in_prediction_is_structural_indeterminate():
    # 凍結集合外の holdout を含む予測は構造破綻として全条件を判定不能へ倒す。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    prediction["rows"].append(
        {"target_holdout": "h-foreign", "arm": "on", "choice_id": "c01",
         "status": "valid"})
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=EXPECTED)
    assert result["status"] == verdict.INDETERMINATE
    assert any(reason["code"] == "unexpected-holdout" for reason in result["reasons"])


@pytest.mark.parametrize("bad_expected", [
    frozenset(), [], "h1", None, {H1: 1.0}, [H1, H1], [H1, ""],
])
def test_invalid_expected_holdouts_is_indeterminate(bad_expected):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    result = verdict.judge_combined(
        prediction=prediction, oracle=oracle, floors={H1: 10.0, H2: 10.0},
        expected_holdouts=bad_expected)
    assert result["status"] == verdict.INDETERMINATE
    for name in ("on_off_prediction_difference", "swapped_follow",
                 "oracle_floor_exceeded"):
        assert _cond(result, name) == verdict.INDETERMINATE
