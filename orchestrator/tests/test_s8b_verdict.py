# -*- coding: utf-8 -*-
"""8b 結合 judge (§6 判定表 v2) の三値・同一 holdout 束縛・per-pair floor・scale gate・型分離。

fixture は workload 値を持たず opaque な holdout ID (h1/h2) と choice_id (c01..c06) を使う。
oracle の configurations と floor の pairs は「構成名 (binding_key)」を key とし、prediction の
choice (c01..c06) とは名前空間が異なる (C3-1)。テストは choice→binding を明示的に翻訳して両者を
構成し、verdict が trusted projector で解決することを検証する。
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

_HERE = Path(__file__).resolve().parent
ORCH = _HERE.parent
REPO_ROOT = ORCH.parent
for _p in (str(REPO_ROOT), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from orchestrator.campaign import s8b_verdict as verdict  # noqa: E402
from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402
from orchestrator.campaign import s8b_oracle_judge as oracle_judge  # noqa: E402
from orchestrator.campaign import s8b_oracle_manifest as oracle_manifest  # noqa: E402
from orchestrator.campaign import s8b_oracle_spec as oracle_spec  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze as ratified_freeze  # noqa: E402
from orchestrator.campaign.s8b_selector_input import (  # noqa: E402
    CHOICE_TO_BINDING,
    STATIC_DEFAULT_CHOICE_ID,
)
import test_s8b_oracle_report as report_fixtures  # noqa: E402

STOCK = verdict.STOCK_CONFIGURATION  # "stock_common"

H1, H2 = "h1", "h2"
DERANGEMENT = {H1: H2, H2: H1}
# 凍結 holdout 集合 (裁定 5 項 1 の全称量化の領域)。judge_combined に必ず渡す。
EXPECTED = frozenset({H1, H2})
TOL = "0.10"  # protocol 由来の scale tolerance (十進文字列で厳密 Fraction 化)


def make_prediction(holdouts: dict) -> dict:
    """holdouts = {h: {"on":c|None, "off":c|None, "swapped":c|None}} から予測文書を作る。"""
    rows = []
    for holdout_id, arms in holdouts.items():
        for arm in ("on", "off", "swapped"):
            choice = arms.get(arm)
            row = {
                "target_holdout": holdout_id,
                "arm": arm,
                "choice_id": choice,
                "status": "valid" if choice is not None else "invalid",
            }
            # off arm の decision_method/binding_key は projector/型検査の入力になる。
            if arm == "off":
                row["decision_method"] = "static_default"
                row["binding_key"] = (CHOICE_TO_BINDING.get(choice)
                                      if choice is not None else None)
            rows.append(row)
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


def make_oracle(holdouts: dict) -> artifacts.OfficialVerdict:
    """holdouts = {h: {"verdict":..., "configs": {choice_id: median|dict}}} から oracle verdict を作る。

    configs の key は choice_id で書くが、oracle 文書へは binding_key (構成名) へ翻訳して格納する
    (実 oracle は configuration_id = binding_key で keying する。C3-1)。
    """
    out_holdouts = {}
    for holdout_id, spec in holdouts.items():
        configurations = {}
        for choice_id, cell in spec.get("configs", {}).items():
            binding = CHOICE_TO_BINDING[choice_id]
            if isinstance(cell, dict):
                configurations[binding] = dict(cell)
            else:
                configurations[binding] = {
                    "status": "eligible",
                    "median_of_medians": float(cell),
                    "trial_medians": [float(cell)],
                    "reasons": [],
                }
        out_holdouts[holdout_id] = {
            "verdict": spec["verdict"],
            "winner_configuration_id": (CHOICE_TO_BINDING.get(spec["winner"])
                                        if spec.get("winner") else None),
            "tied_configuration_ids": [CHOICE_TO_BINDING[c] for c in spec.get("tied", [])],
            "configurations": configurations,
            "reasons": [],
        }
    return artifacts.OfficialVerdict({
        "schema_version": verdict.ORACLE_SCHEMA,
        "manifest_sha256": "manifest-sha",
        "n_per_cell": 2,
        "status": "determinate",
        "reasons": [],
        "holdouts": out_holdouts,
    })


def make_floor(pairs: dict, scale_ref) -> dict:
    """pairs = {h: {choice_id: floor|None}} (非 stock) と scale_ref から by_holdout 表を作る。

    pairs の key は choice_id で書くが、by_holdout.pairs へは binding_key (構成名) へ翻訳する。
    scalar_alt は judge_combined が参照しないため None (per-pair 相関検査は manifest validator の責務)。
    """
    by = {}
    for holdout_id, cells in pairs.items():
        by[holdout_id] = {
            "pairs": {CHOICE_TO_BINDING[c]: val for c, val in cells.items()},
            "scale_ref": (scale_ref.get(holdout_id) if isinstance(scale_ref, dict)
                          else scale_ref),
            "scalar_alt": None,
        }
    return by


def _unsafe_verified_oracle_for_judge_unit_test(
        document: artifacts.OfficialVerdict,
) -> verdict.VerifiedOracleVerdict:
    """判定本体の単体テスト専用に、明記済みの信頼境界外操作で token を作る。"""
    token = object.__new__(verdict.VerifiedOracleVerdict)
    object.__setattr__(token, "document", document)
    object.__setattr__(
        token,
        "document_sha256",
        hashlib.sha256(verdict._canonical_json_text(document).encode("utf-8")).hexdigest(),
    )
    return token


def run(prediction: dict, oracle: artifacts.OfficialVerdict, floor_by_holdout: dict, *,
        expected=EXPECTED, tol=TOL) -> dict:
    """三値判定本体だけを対象に、検証済み token 形へ包んで呼ぶ薄いラッパ。"""
    return verdict.judge_combined(
        prediction=verdict.VerifiedPrediction(document=prediction),
        oracle=_unsafe_verified_oracle_for_judge_unit_test(oracle),
        floor_by_holdout=floor_by_holdout,
        expected_holdouts=expected, scale_tolerance=tol)


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
    floor = make_floor({H1: {"c01": 5.0}, H2: {}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
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
    floor = make_floor({H1: {}, H2: {}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "on_off_prediction_difference") == verdict.REFUTED


def test_condition1_indeterminate_when_missing_and_no_difference():
    prediction = make_prediction({
        H1: {"on": None, "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {}, H2: {}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "on_off_prediction_difference") == verdict.INDETERMINATE


# ---- 条件 2: swapped 追従 (両 holdout 必須) --------------------------------

def test_condition2_holds_when_both_holdouts_follow():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 5.0}, H2: {"c02": 5.0}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "swapped_follow") == verdict.HOLDS


def test_condition2_refuted_when_one_holdout_does_not_follow():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c03"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 5.0}, H2: {"c02": 5.0}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "swapped_follow") == verdict.REFUTED


def test_condition2_indeterminate_when_a_swapped_cell_is_missing():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": None},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 5.0}, H2: {"c02": 5.0}}, {H1: 10.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE


# ---- 条件 3: oracle per-pair floor 超 (方向付き) ---------------------------

def test_condition3_holds_when_directional_diff_exceeds_floor():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    # scale_ref = stock(c06) median なので scale adequate。pair floor c01=10。
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    # oracle(on=c01)=100 − oracle(off=stock)=50 = 50 > floor 10。
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    # h1: 55 − 50 = 5 ≤ 10、h2: on==off → 不成立側 (floor 照会なし)。両者確定不成立。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED


def test_condition3_refuted_directionally_when_off_beats_on():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 100.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    # h1: 10 − 100 = −90 は floor 10 を超えない (方向付き)。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED


def test_condition3_indeterminate_when_pair_floor_null():
    # per-pair floor が null (機械異常の伝播) → 判定不能。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": None}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


@pytest.mark.parametrize("bad_floor", [0.0, -5.0, float("inf"), True])
def test_condition3_indeterminate_when_pair_floor_is_not_positive_finite(bad_floor):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": bad_floor}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


# ---- on == off の短絡 (floor 照会なしで不成立側。§5-iii) ---------------------

def test_on_equals_off_is_refuted_without_floor_query():
    # h2: on==off==c06 (stock)。floor 表に stock pair は存在しないが、projector は照会せず不成立側。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "indeterminate", "configs": {}},  # oracle 判定不能でも on==off は refuted
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H2]["oracle_floor_exceeded"] == verdict.REFUTED
    assert result["holdouts"][H2]["floor"] is None  # floor 照会なし


# ---- projector の名前空間解決 (choice_id を floor key に使わない。C3-1) -------

def test_projector_query_resolves_choice_to_binding():
    floor_by_holdout = make_floor({H1: {"c01": 10.0}}, {H1: 50.0})
    projected = verdict.project_pair_floor(
        floor_by_holdout, CHOICE_TO_BINDING, H1, "c01", "c06")
    assert projected.resolution == verdict._PROJECT_QUERY
    assert projected.floor == 10.0
    assert projected.on_binding_key == CHOICE_TO_BINDING["c01"]
    assert projected.off_binding_key == STOCK


def test_projector_rejects_choice_id_keyed_floor_table():
    # 攻撃: floor pairs を choice_id ("c01") で keying する (名前空間混同)。projector は
    # on_binding = p2_2_flag_opt を引くため見つからず判定不能 + floor-pair-missing。
    poisoned = {H1: {"pairs": {"c01": 10.0}, "scale_ref": 50.0, "scalar_alt": None}}
    projected = verdict.project_pair_floor(
        poisoned, CHOICE_TO_BINDING, H1, "c01", "c06")
    assert projected.resolution == verdict._PROJECT_INDETERMINATE
    assert any(v["code"] == "floor-pair-missing" for v in projected.violations)


def test_projector_off_not_stock_records_violation():
    floor_by_holdout = make_floor({H1: {"c01": 10.0}}, {H1: 50.0})
    projected = verdict.project_pair_floor(
        floor_by_holdout, CHOICE_TO_BINDING, H1, "c01", "c02")  # off=c02 は非 stock
    assert projected.resolution == verdict._PROJECT_INDETERMINATE
    assert any(v["code"] == "off-not-stock" for v in projected.violations)


def test_projector_on_equals_off_short_circuits_before_floor_lookup():
    # pairs を空にしても on==off は floor 照会なしで refuted (照会されたら missing になる)。
    empty = {H1: {"pairs": {}, "scale_ref": 50.0, "scalar_alt": None}}
    projected = verdict.project_pair_floor(empty, CHOICE_TO_BINDING, H1, "c06", "c06")
    assert projected.resolution == verdict._PROJECT_REFUTED
    assert projected.violations == ()


def test_judge_records_off_not_stock_protocol_violation():
    # off を非 stock (c02) に改竄した prediction → 当該 holdout の条件 3 判定不能 + violation 記録。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c02", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    # off=c02 の binding_key を整合させる (型検査は verify_prediction 側。ここは judge の projector)。
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c02": 50.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE
    assert any(v["code"] == "off-not-stock" and v["holdout"] == H1
               for v in result["protocol_violations"])


# ---- scale gate (C3-8、§5-iv) ---------------------------------------------

def _scale_case(stock_median: float, scale_ref: float, on_median: float = 100.0):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best",
             "configs": {"c01": on_median, "c06": stock_median}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: scale_ref, H2: 10.0})
    return prediction, oracle, floor


def test_scale_gate_boundary_exactly_tolerance_is_adequate():
    # observed 110 / scale_ref 100 → 相対差 1/10 == tolerance 0.10 → adequate。条件 3 は通常判定。
    prediction, oracle, floor = _scale_case(stock_median=110.0, scale_ref=100.0, on_median=200.0)
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["scale"]["state"] == verdict.SCALE_ADEQUATE
    # on(200) − stock(110) = 90 > floor 10 → HOLDS (scale gate に潰されていない)。
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.HOLDS


def test_scale_gate_over_tolerance_is_inadequate_and_condition3_indeterminate():
    # observed 111 / scale_ref 100 → 11/100 > 0.10 → inadequate → 条件 3 のみ判定不能。
    prediction, oracle, floor = _scale_case(stock_median=111.0, scale_ref=100.0, on_median=200.0)
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["scale"]["state"] == verdict.SCALE_INADEQUATE
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE
    # 他条件 (1) は不変: on(c01)≠off(c06) → 予測差は成立のまま。
    assert result["holdouts"][H1]["on_off_prediction_difference"] == verdict.HOLDS


def test_scale_gate_stock_ineligible_makes_condition3_indeterminate():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {
            "c01": 200.0,
            "c06": {"status": "disqualified", "median_of_medians": None,
                    "trial_medians": [], "reasons": []}}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 100.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["scale"]["state"] == verdict.SCALE_STOCK_INELIGIBLE
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


def test_scale_gate_scale_ref_null_makes_condition3_indeterminate():
    prediction, oracle, _floor = _scale_case(stock_median=100.0, scale_ref=100.0, on_median=200.0)
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: None, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["scale"]["state"] == verdict.SCALE_REF_NULL
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


def test_invalid_scale_tolerance_is_rejected():
    prediction, oracle, floor = _scale_case(stock_median=100.0, scale_ref=100.0)
    for bad in (None, -1, "abc", float("inf"), True):
        with pytest.raises(verdict.VerdictError):
            run(prediction, oracle, floor, tol=bad)


# ---- tie 写像: oracle exact tie → oracle 非一意 → 判定不能 ------------------

def test_oracle_exact_tie_maps_to_indeterminate():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "tie", "tied": ["c01", "c06"],
             "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 100.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE
    assert _cond(result, "oracle_floor_exceeded") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


def test_oracle_indeterminate_holdout_maps_to_indeterminate():
    # scale adequate (stock eligible) を保ち、oracle verdict=indeterminate 経由の判定不能を切り分ける。
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "indeterminate", "configs": {"c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["scale"]["state"] == verdict.SCALE_ADEQUATE
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


def test_disqualified_predicted_config_is_indeterminate():
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    assert result["holdouts"][H1]["oracle_floor_exceeded"] == verdict.INDETERMINATE


# ---- 同一 holdout 束縛の反例 ----------------------------------------------

def test_same_holdout_binding_refutes_cross_holdout_evidence():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best",
             "winner": "c01", "configs": {"c01": 500.0, "c06": 100.0}},
    })
    floor = make_floor({H1: {"c01": 5.0}, H2: {}}, {H1: 100.0, H2: 100.0})
    result = run(prediction, oracle, floor)

    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    # 条件 3 は on/off 予測構成の差なので h2 の勝者 c01 を使わず、両 holdout で不成立。
    assert _cond(result, "oracle_floor_exceeded") == verdict.REFUTED
    assert result["holdouts"][H2]["oracle_floor_exceeded"] == verdict.REFUTED
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    assert _cond(result, "oracle_floor_exceeded") == verdict.HOLDS
    assert result["same_holdout_coupled_verdict"] == verdict.HOLDS
    assert result["status"] == verdict.HOLDS


def test_conclusion_indeterminate_propagates_from_a_condition():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": None},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0})
    result = run(prediction, oracle, floor)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


# ---- 構造破綻の fail-closed --------------------------------------------------

def test_malformed_prediction_is_fully_indeterminate():
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}}, {H1: 50.0})
    result = run({"schema_version": "wrong", "rows": "not-a-list"}, oracle, floor)
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {}}, {H1: 50.0, H2: 10.0})
    result = run(prediction, oracle, floor)
    floor_ev = result["conditions"]["oracle_floor_exceeded"]["evidence"]
    assert floor_ev["prediction_body_sha256"] == "a" * 64
    assert floor_ev["oracle_manifest_sha256"] == "manifest-sha"
    # per-pair 化: h1 は投影された pair floor、h2 は on==off 短絡で None。
    assert floor_ev["floors"] == {H1: 10.0, H2: None}
    assert floor_ev["scale_tolerance"] == TOL
    assert floor_ev["scale_states"][H1] == verdict.SCALE_ADEQUATE
    pred_ev = result["conditions"]["on_off_prediction_difference"]["evidence"]
    assert pred_ev["selector_basis_sha256"] == "b" * 64


# ---- 型分離 (C3-2): 未検証 object を verdict に渡せない -----------------------

def test_judge_combined_rejects_unverified_raw_dict():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0})
    with pytest.raises(verdict.VerdictError, match="VerifiedPrediction"):
        verdict.judge_combined(
            prediction=prediction, oracle=oracle, floor_by_holdout=floor,
            expected_holdouts=EXPECTED, scale_tolerance=TOL)


def test_judge_combined_rejects_unverified_official_oracle_verdict():
    prediction = verdict.VerifiedPrediction(document=make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    }))
    official = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    floor = make_floor(
        {H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0},
    )
    for unverified in (
            official, dict(official), artifacts.ExplorationArtifact(official)):
        with pytest.raises(verdict.VerdictError, match="VerifiedOracleVerdict"):
            verdict.judge_combined(
                prediction=prediction, oracle=unverified, floor_by_holdout=floor,
                expected_holdouts=EXPECTED, scale_tolerance=TOL,
            )


def test_judge_combined_rejects_duck_typed_oracle_wrapper():
    prediction = verdict.VerifiedPrediction(document=make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    }))
    official = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    floor = make_floor(
        {H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0},
    )

    with pytest.raises(verdict.VerdictError, match="VerifiedOracleVerdict"):
        verdict.judge_combined(
            prediction=prediction,
            oracle=SimpleNamespace(document=official),
            floor_by_holdout=floor,
            expected_holdouts=EXPECTED,
            scale_tolerance=TOL,
        )


def test_verified_oracle_verdict_rejects_direct_construction():
    official = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 1.0}},
    })
    with pytest.raises(verdict.VerdictError, match="検証結果からのみ"):
        verdict.VerifiedOracleVerdict(document=official)


def test_judge_combined_rejects_post_issuance_oracle_document_tampering(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    verified_oracle = verdict.verify_oracle_verdict(
        case.oracle_path,
        observations_source=case.observations_path,
        verified_manifest=case.verified_manifest,
        approved_spec=case.approved,
    )
    original_status = verified_oracle.document["status"]
    verified_oracle.document["status"] = (
        "indeterminate" if original_status != "indeterminate" else "determinate"
    )
    prediction = verdict.VerifiedPrediction(document=make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    }))

    with pytest.raises(verdict.VerdictError, match="canonical hash.*事後改竄"):
        verdict.judge_combined(
            prediction=prediction,
            oracle=verified_oracle,
            floor_by_holdout={},
            expected_holdouts=EXPECTED,
            scale_tolerance=TOL,
        )


def test_judge_combined_rejects_nested_semantic_subclass_in_sealed_document(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    verified_oracle = verdict.verify_oracle_verdict(
        case.oracle_path,
        observations_source=case.observations_path,
        verified_manifest=case.verified_manifest,
        approved_spec=case.approved,
    )
    first_holdout = next(iter(verified_oracle.document["holdouts"].values()))
    configurations = first_holdout["configurations"]
    original_cell = configurations[STOCK]
    floor_by_holdout = {
        holdout_id: {
            "pairs": {},
            "scale_ref": holdout["configurations"][STOCK]["median_of_medians"],
            "scalar_alt": None,
        }
        for holdout_id, holdout in verified_oracle.document["holdouts"].items()
    }

    class MisleadingMedianCell(dict):
        def __getitem__(self, key):
            value = dict.__getitem__(self, key)
            if key == "median_of_medians":
                return value + 1.0
            return value

        def get(self, key, default=None):
            if key == "median_of_medians" and key in self:
                return self[key]
            return dict.get(self, key, default)

    configurations[STOCK] = MisleadingMedianCell(original_cell)
    assert list(configurations[STOCK]) == list(original_cell)
    assert list(configurations[STOCK].items()) == list(original_cell.items())
    assert configurations[STOCK].get("median_of_medians") != original_cell.get(
        "median_of_medians"
    )
    canonical_sha256 = hashlib.sha256(
        verdict._canonical_json_text(verified_oracle.document).encode("utf-8")
    ).hexdigest()
    assert canonical_sha256 == verified_oracle.document_sha256
    # この fixture は canonical hash を保つため、plain 型検査を外すと受理される。
    prediction = verdict.VerifiedPrediction(document=make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    }))

    with pytest.raises(verdict.VerdictError, match="nested 値.*plain JSON 型"):
        verdict.judge_combined(
            prediction=prediction,
            oracle=verified_oracle,
            floor_by_holdout=floor_by_holdout,
            expected_holdouts=set(verified_oracle.document["holdouts"]),
            scale_tolerance=TOL,
        )


# ---- VerifiedPrediction: off=stock / catalog 合法性の機械検査 ------------------

def _valid_off_stock_rows() -> list[dict]:
    return [
        {"target_holdout": H1, "arm": "on", "choice_id": "c01",
         "decision_method": "selector_agent", "binding_key": CHOICE_TO_BINDING["c01"]},
        {"target_holdout": H1, "arm": "off", "choice_id": STATIC_DEFAULT_CHOICE_ID,
         "decision_method": "static_default", "binding_key": STOCK},
        {"target_holdout": H1, "arm": "swapped", "choice_id": "c02",
         "decision_method": "selector_agent", "binding_key": CHOICE_TO_BINDING["c02"]},
    ]


def test_off_stock_check_accepts_valid_static_default():
    verdict._assert_off_stock_and_catalog({"rows": _valid_off_stock_rows()})


def test_off_stock_check_rejects_non_static_default_decision_method():
    rows = deepcopy(_valid_off_stock_rows())
    off = next(r for r in rows if r["arm"] == "off")
    off["decision_method"] = "selector_agent"
    with pytest.raises(verdict.VerdictError, match="static_default"):
        verdict._assert_off_stock_and_catalog({"rows": rows})


def test_off_stock_check_rejects_non_stock_off():
    rows = _valid_off_stock_rows()
    off = next(r for r in rows if r["arm"] == "off")
    off["choice_id"] = "c01"  # 非 stock choice を off に注入
    off["binding_key"] = CHOICE_TO_BINDING["c01"]
    with pytest.raises(verdict.VerdictError, match="静的既定 ID でない"):
        verdict._assert_off_stock_and_catalog({"rows": rows})


def test_off_stock_check_rejects_off_binding_not_stock():
    rows = _valid_off_stock_rows()
    off = next(r for r in rows if r["arm"] == "off")
    off["binding_key"] = "p2_2_flag_opt"  # choice は c06 のまま binding だけ改竄
    with pytest.raises(verdict.VerdictError, match="binding が stock"):
        verdict._assert_off_stock_and_catalog({"rows": rows})


def test_off_stock_check_rejects_illegal_choice_id():
    rows = _valid_off_stock_rows()
    rows[0]["choice_id"] = "c99"  # catalog 外
    with pytest.raises(verdict.VerdictError, match="catalog 外"):
        verdict._assert_off_stock_and_catalog({"rows": rows})


def test_verify_prediction_happy_path_returns_verified(tmp_path):
    # 実 selector 機構で valid prediction を組み、verify_prediction が VerifiedPrediction を返す。
    import test_s8b_selector_freeze as SF
    freeze = SF._freeze()
    head = SF._fixture_head(tmp_path)
    document = SF._document(freeze, root=tmp_path, pre_oracle_head=head)
    verified = verdict.verify_prediction(document, freeze=freeze, root=tmp_path)
    assert isinstance(verified, verdict.VerifiedPrediction)
    assert verified.document is document


# ---- VerifiedOracleVerdict: authority 束縛 + observations 再導出 ------------

def _oracle_verifier_case(tmp_path: Path) -> SimpleNamespace:
    """実 manifest/spec verifier を通した oracle 再導出 fixture を作る。"""
    root, manifest_path, manifest_document, approved_fixture = (
        report_fixtures._ratified_cli_manifest(tmp_path)
    )
    ratified = ratified_freeze.load_ratified_freeze(root)
    reverified = ratified_freeze.reverify_published_freeze(ratified, root)
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved_fixture.sha256):
        approved = oracle_spec.load_approved_spec(root)
        verified_manifest = oracle_manifest.verify_manifest(
            manifest_path,
            root=root,
            freeze_document=reverified.ratified.document,
            freeze_sha256=reverified.ratified.sha256,
            approved_spec=approved,
        )

    rows = []
    for ordinal, schedule_row in enumerate(manifest_document["schedule"]["rows"], start=1):
        rows.append({
            "schedule_index": schedule_row["schedule_index"],
            "block_id": schedule_row["block_id"],
            "holdout_id": schedule_row["holdout_id"],
            "configuration_id": schedule_row["configuration_id"],
            "attempt": 1,
            "status": "completed",
            "outcome": "committed",
            "binding_ok": True,
            "legacy_verify": "pass",
            "s2_verify": "pass",
            "bench_values": [float(ordinal)],
            "excluded_reason": None,
            "screen_outcome": "not_enabled",
            "reason": None,
        })
    observations = artifacts.OfficialObservations({
        "schema_version": artifacts.OFFICIAL_OBSERVATIONS_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": verified_manifest.sha256,
        "spec_sha256": approved.sha256,
        "n_per_cell": manifest_document["schedule"]["n"],
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
        "rows": rows,
    })
    schedule_projection = oracle_judge.project_verified_manifest_schedule(
        verified_manifest,
    )
    oracle = oracle_judge.judge_oracle(
        observations,
        schedule_projection=schedule_projection,
        verified_manifest_sha256=verified_manifest.sha256,
        approved_spec_sha256=approved.sha256,
    )
    observations_path = tmp_path / "verifier-observations.json"
    oracle_path = tmp_path / "verifier-oracle.json"
    observations_path.write_text(
        json.dumps(observations, ensure_ascii=False), encoding="utf-8",
    )
    oracle_path.write_text(
        json.dumps(oracle, ensure_ascii=False), encoding="utf-8",
    )
    return SimpleNamespace(
        root=root,
        manifest_path=manifest_path,
        manifest_document=manifest_document,
        approved=approved,
        verified_manifest=verified_manifest,
        observations=observations,
        observations_path=observations_path,
        oracle=oracle,
        oracle_path=oracle_path,
        schedule_projection=schedule_projection,
        reverified=reverified,
    )


def _write_oracle_variant(path: Path, document) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def test_verify_oracle_verdict_accepts_rederived_exact_match(tmp_path):
    case = _oracle_verifier_case(tmp_path)

    verified = verdict.verify_oracle_verdict(
        case.oracle_path,
        observations_source=case.observations_path,
        verified_manifest=case.verified_manifest,
        approved_spec=case.approved,
    )

    assert type(verified) is verdict.VerifiedOracleVerdict
    assert type(verified.document) is artifacts.OfficialVerdict
    assert verified.document == case.oracle


def test_verify_oracle_verdict_rejects_boolean_median_type_confusion(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    forged = deepcopy(case.oracle)
    target = next(
        cell
        for holdout in forged["holdouts"].values()
        for cell in holdout["configurations"].values()
        if cell["median_of_medians"] == 1.0
    )
    target["median_of_medians"] = True
    # Python の dict 等値では True == 1.0 のため差が消える。canonical JSON だけが型差を残す。
    assert forged == case.oracle
    forged_path = tmp_path / "oracle-boolean-median.json"
    _write_oracle_variant(forged_path, forged)

    with pytest.raises(verdict.VerdictError, match="再導出結果"):
        verdict.verify_oracle_verdict(
            forged_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


def test_verify_oracle_verdict_rejects_wrong_authority_observations(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    wrong_observations = artifacts.OfficialObservations(deepcopy(case.observations))
    wrong_observations["manifest_sha256"] = "f" * 64
    self_consistent = oracle_judge.judge_oracle(
        wrong_observations,
        schedule_projection=case.schedule_projection,
        verified_manifest_sha256=case.verified_manifest.sha256,
        approved_spec_sha256=case.approved.sha256,
    )
    assert self_consistent["manifest_sha256"] is None
    observations_path = tmp_path / "wrong-authority-observations.json"
    oracle_path = tmp_path / "wrong-authority-oracle.json"
    observations_path.write_text(
        json.dumps(wrong_observations, ensure_ascii=False), encoding="utf-8",
    )
    _write_oracle_variant(oracle_path, self_consistent)

    with pytest.raises(verdict.VerdictError, match="manifest_sha256"):
        verdict.verify_oracle_verdict(
            oracle_path,
            observations_source=observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


def test_verify_oracle_verdict_rejects_extra_top_level_key(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    forged = deepcopy(case.oracle)
    forged["extra"] = "not-authoritative"
    forged_path = tmp_path / "oracle-extra-key.json"
    _write_oracle_variant(forged_path, forged)

    with pytest.raises(verdict.VerdictError, match="再導出結果"):
        verdict.verify_oracle_verdict(
            forged_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


def test_verify_oracle_verdict_requires_exact_authority_types(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    # project_verified_manifest_schedule の TypeError も CLI main が捕捉し、rc=2 に保つ。
    with pytest.raises(TypeError, match="VerifiedManifest exact type"):
        verdict.verify_oracle_verdict(
            case.oracle_path,
            observations_source=case.observations_path,
            verified_manifest=object(),
            approved_spec=case.approved,
        )
    with pytest.raises(verdict.VerdictError, match="ReviewedSpec exact type"):
        verdict.verify_oracle_verdict(
            case.oracle_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=SimpleNamespace(sha256=case.approved.sha256),
        )


def test_verify_oracle_verdict_rejects_approved_spec_from_other_manifest(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    foreign_sha256 = "f" * 64
    foreign_spec = replace(case.approved, sha256=foreign_sha256)
    assert foreign_spec.sha256 != case.approved.sha256
    foreign_observations = artifacts.OfficialObservations(deepcopy(case.observations))
    foreign_observations["spec_sha256"] = foreign_sha256
    self_consistent = oracle_judge.judge_oracle(
        foreign_observations,
        schedule_projection=case.schedule_projection,
        verified_manifest_sha256=case.verified_manifest.sha256,
        approved_spec_sha256=foreign_sha256,
    )
    observations_path = tmp_path / "foreign-spec-observations.json"
    oracle_path = tmp_path / "foreign-spec-oracle.json"
    observations_path.write_text(
        json.dumps(foreign_observations, ensure_ascii=False), encoding="utf-8",
    )
    _write_oracle_variant(oracle_path, self_consistent)
    # spec 束縛の独立効果を測る fixture。observations・引数・oracle は B で自己整合し、
    # canonical 比較は一致するため、manifest が束縛する A との照合だけが拒否理由になる。

    with pytest.raises(
            verdict.VerdictError,
            match="approved_spec.*manifest の spec_sha256"):
        verdict.verify_oracle_verdict(
            oracle_path,
            observations_source=observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=foreign_spec,
        )


def test_verify_oracle_verdict_rejects_post_issuance_manifest_tampering(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    case.verified_manifest.document["schedule"]["n"] += 1
    tampered_n = case.verified_manifest.document["schedule"]["n"]
    tampered_observations = artifacts.OfficialObservations(deepcopy(case.observations))
    tampered_observations["n_per_cell"] = tampered_n
    tampered_rows = []
    for row in case.observations["rows"]:
        for attempt in range(1, tampered_n + 1):
            copied = deepcopy(row)
            copied["attempt"] = attempt
            tampered_rows.append(copied)
    tampered_observations["rows"] = tampered_rows
    tampered_projection = oracle_judge.project_verified_manifest_schedule(
        case.verified_manifest,
    )
    self_consistent = oracle_judge.judge_oracle(
        tampered_observations,
        schedule_projection=tampered_projection,
        verified_manifest_sha256=case.verified_manifest.sha256,
        approved_spec_sha256=case.approved.sha256,
    )
    observations_path = tmp_path / "tampered-manifest-observations.json"
    oracle_path = tmp_path / "tampered-manifest-oracle.json"
    observations_path.write_text(
        json.dumps(tampered_observations, ensure_ascii=False), encoding="utf-8",
    )
    _write_oracle_variant(oracle_path, self_consistent)
    # manifest hash 再照合の独立効果を測る fixture。改竄 schedule・observations・oracle は
    # 自己整合し canonical 比較は一致するため、発行時 document hash との照合だけが拒否する。

    with pytest.raises(verdict.VerdictError, match="事後改竄"):
        verdict.verify_oracle_verdict(
            oracle_path,
            observations_source=observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


def test_verify_oracle_verdict_rejects_semantic_sha256_subclass(tmp_path):
    case = _oracle_verifier_case(tmp_path)

    class AlwaysEqualSha256(str):
        def __eq__(self, other):
            return True

    semantic_sha256 = AlwaysEqualSha256("f" * 64)
    forged_spec = replace(case.approved, sha256=semantic_sha256)
    assert type(forged_spec) is oracle_spec.ReviewedSpec

    with pytest.raises(verdict.VerdictError, match="ReviewedSpec.sha256.*plain str"):
        verdict.verify_oracle_verdict(
            case.oracle_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=forged_spec,
        )


def test_verify_oracle_verdict_rejects_nested_semantic_dict_subclass(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    original_schedule = case.verified_manifest.document["schedule"]

    class MisleadingSchedule(dict):
        def __getitem__(self, key):
            if key == "n":
                return dict.__getitem__(self, key) + 1
            if key == "rows":
                return []
            return dict.__getitem__(self, key)

    canonical_before = oracle_manifest._canonical_sha256(
        case.verified_manifest.document,
    )
    assert canonical_before == case.verified_manifest.sha256
    case.verified_manifest.document["schedule"] = MisleadingSchedule(original_schedule)
    # json.dumps は items() を読むので canonical hash は保存される。したがって hash gate ではなく、
    # projector が偽の __getitem__ 値を読む前の plain-type gate が独立に攻撃を拒否する。
    assert oracle_manifest._canonical_sha256(
        case.verified_manifest.document,
    ) == case.verified_manifest.sha256

    with pytest.raises(verdict.VerdictError, match="nested 値.*plain JSON 型"):
        verdict.verify_oracle_verdict(
            case.oracle_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


# ---- 裁定 5 項 1: 両 holdout 必須の基数下限 (所見 1 の回帰) --------------------

def _single_holdout_self_consistent() -> dict:
    return {
        "schema_version": verdict.PREDICTION_SCHEMA,
        "body_sha256": "a" * 64,
        "selector_basis_sha256": "b" * 64,
        "derangement": {H1: H2, H2: H1},
        "rows": [
            {"target_holdout": H1, "arm": "on", "choice_id": "c01", "status": "valid"},
            {"target_holdout": H1, "arm": "off", "choice_id": "c06", "status": "valid",
             "decision_method": "static_default", "binding_key": STOCK},
            {"target_holdout": H1, "arm": "swapped", "choice_id": "c02", "status": "valid"},
        ],
        "swapped_follow_expectations": [
            {"target_holdout": H1, "source_on_holdout": H2, "expected_choice_id": "c02"},
        ],
    }


def test_single_holdout_prediction_cannot_conclude_holds():
    prediction = _single_holdout_self_consistent()
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}}, {H1: 50.0})
    result = run(prediction, oracle, floor)
    assert result["status"] != verdict.HOLDS
    assert result["status"] == verdict.INDETERMINATE
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert any(reason["code"] == "missing-holdout" for reason in result["reasons"])


def test_single_holdout_would_hold_without_cardinality_guard():
    prediction = _single_holdout_self_consistent()
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    floor = make_floor({H1: {"c01": 10.0}}, {H1: 50.0})
    degenerate = run(prediction, oracle, floor, expected=frozenset({H1}))
    assert degenerate["status"] == verdict.HOLDS


def test_unexpected_holdout_in_prediction_is_structural_indeterminate():
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0})
    result = run(prediction, oracle, floor)
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
    floor = make_floor({H1: {"c01": 10.0}, H2: {"c02": 10.0}}, {H1: 50.0, H2: 50.0})
    result = run(prediction, oracle, floor, expected=bad_expected)
    assert result["status"] == verdict.INDETERMINATE
    for name in ("on_off_prediction_difference", "swapped_follow",
                 "oracle_floor_exceeded"):
        assert _cond(result, name) == verdict.INDETERMINATE


# ---- CLI (C2-7): floors/holdouts 廃止 + freeze 導出 --------------------------

def _v2_freeze_document() -> dict:
    """_validate_execution_snapshot を通す最小の v2 per-pair freeze を組む。"""
    non_stock = [b for b in CHOICE_TO_BINDING.values() if b != STOCK]
    entries = {name: {} for name in list(CHOICE_TO_BINDING.values())}
    holdouts = {
        H1: {"variant_binding": {"entries": dict(entries)}},
        H2: {"variant_binding": {"entries": dict(entries)}},
    }
    pairs_h1 = {name: 10.0 for name in non_stock}
    pairs_h2 = {name: 20.0 for name in non_stock}
    floor = {"by_holdout": {
        H1: {"pairs": pairs_h1, "scale_ref": 50.0, "scalar_alt": max(pairs_h1.values())},
        H2: {"pairs": pairs_h2, "scale_ref": 60.0, "scalar_alt": max(pairs_h2.values())},
    }}
    budget = {"total_bench_s": 100.0,
              "per_holdout_bench_s": {H1: 50.0, H2: 50.0},
              "oracle_shared": True}
    return {"holdouts": holdouts, "floor": floor, "budget": budget}


def _write_json(path: Path, document) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_cli_rejects_removed_floors_and_holdouts_args(tmp_path, capsys):
    # 後方非互換: 旧 --floors / --holdouts は argparse が unrecognized で拒否する。
    args = ["judge", "--prediction", "p.json", "--oracle", "o.json",
            "--manifest", "m.json", "--observations", "obs.json",
            "--freeze", "f.json", "--freeze-sha256", "0" * 64, "--out", "out.json",
            "--floors", "x.json"]
    with pytest.raises(SystemExit) as ei:
        verdict.main(args)
    assert ei.value.code != 0
    args2 = ["judge", "--prediction", "p.json", "--oracle", "o.json",
             "--manifest", "m.json", "--observations", "obs.json",
             "--freeze", "f.json", "--freeze-sha256", "0" * 64, "--out", "out.json",
             "--holdouts", "h.json"]
    with pytest.raises(SystemExit):
        verdict.main(args2)


def test_cli_derives_floor_and_tolerance_from_freeze(tmp_path, monkeypatch):
    # 外部 authority I/O は個別 E2E で覆うため、ここは CLI の順序・freeze 導出・wiring を検証する。
    freeze_doc = _v2_freeze_document()
    protocol_path = tmp_path / "protocol.json"
    protocol_sha = _write_json(protocol_path, {"scale_adequacy_rel_tolerance": "0.10"})
    freeze_doc["floor_protocol"] = {"path": "protocol.json", "sha256": protocol_sha}
    freeze_path = tmp_path / "freeze.json"
    freeze_sha = _write_json(freeze_path, freeze_doc)

    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 60.0}},
    })
    pred_path = tmp_path / "prediction.json"
    pred_path.write_text(json.dumps(prediction), encoding="utf-8")
    oracle_path = tmp_path / "oracle.json"
    oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
    out_path = tmp_path / "verdict.json"

    calls = []
    ratified = object()
    reverified = SimpleNamespace(ratified=SimpleNamespace(
        document=freeze_doc, sha256=freeze_sha,
    ))
    approved = object()
    verified_manifest = object()

    def load_freeze(path, expected_sha=None):
        calls.append("freeze")
        return SimpleNamespace(document=freeze_doc, sha256=freeze_sha)

    def load_ratified(root):
        calls.append("ratified")
        return ratified

    def reverify(value, root):
        calls.append("reverify")
        assert value is ratified
        return reverified

    def load_approved(root):
        calls.append("approved")
        return approved

    def verify_manifest(path, **kwargs):
        calls.append("manifest")
        assert kwargs["approved_spec"] is approved
        return verified_manifest

    def verify_prediction(document, *, freeze, root):
        calls.append("prediction")
        return verdict.VerifiedPrediction(document=document)

    def verify_oracle(path, **kwargs):
        calls.append("oracle")
        assert kwargs["verified_manifest"] is verified_manifest
        assert kwargs["approved_spec"] is approved
        return _unsafe_verified_oracle_for_judge_unit_test(oracle)

    monkeypatch.setattr(verdict, "load_verified_freeze", load_freeze)
    monkeypatch.setattr(verdict.s8b_ratified_freeze, "load_ratified_freeze", load_ratified)
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "reverify_published_freeze", reverify,
    )
    monkeypatch.setattr(verdict.s8b_oracle_spec, "load_approved_spec", load_approved)
    monkeypatch.setattr(verdict.s8b_oracle_manifest, "verify_manifest", verify_manifest)
    monkeypatch.setattr(verdict, "_resolve_scale_tolerance", lambda document, *, root: TOL)
    monkeypatch.setattr(verdict, "verify_prediction", verify_prediction)
    monkeypatch.setattr(verdict, "verify_oracle_verdict", verify_oracle)

    rc = verdict.main([
        "judge", "--prediction", str(pred_path), "--oracle", str(oracle_path),
        "--manifest", str(tmp_path / "manifest.json"),
        "--observations", str(tmp_path / "observations.json"),
        "--freeze", str(freeze_path), "--freeze-sha256", freeze_sha,
        "--root", str(tmp_path), "--out", str(out_path)])
    assert rc == 0
    assert calls == [
        "freeze", "ratified", "reverify", "approved", "manifest",
        "prediction", "oracle",
    ]
    out = json.loads(out_path.read_text(encoding="utf-8"))
    floor_ev = out["conditions"]["oracle_floor_exceeded"]["evidence"]
    # freeze 由来の pair floor (c01→p2_2_flag_opt = 10.0) が投影される。
    assert floor_ev["floors"][H1] == 10.0
    assert floor_ev["scale_tolerance"] == "0.10"
    # scale_ref 50 と stock median 50 が一致 → adequate、100−50=50>10 → HOLDS。
    assert out["holdouts"][H1]["oracle_floor_exceeded"] == verdict.HOLDS
    assert out["schema_version"] == "8b-combined-verdict/v2"


@pytest.mark.parametrize("schema", [
    None,
    "unknown/v1",
    artifacts.OFFICIAL_OBSERVATIONS_SCHEMA,
    artifacts.EXPLORATION_ARTIFACT_SCHEMA,
])
def test_cli_rejects_non_verdict_oracle_schema_without_output(
    tmp_path, monkeypatch, schema,
):
    freeze_doc = _v2_freeze_document()
    protocol_path = tmp_path / "protocol.json"
    protocol_sha = _write_json(protocol_path, {"scale_adequacy_rel_tolerance": "0.10"})
    freeze_doc["floor_protocol"] = {"path": "protocol.json", "sha256": protocol_sha}
    freeze_path = tmp_path / "freeze.json"
    freeze_sha = _write_json(freeze_path, freeze_doc)
    prediction_path = tmp_path / "prediction.json"
    prediction_path.write_text(json.dumps(make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })), encoding="utf-8")
    oracle_path = tmp_path / "oracle.invalid.json"
    oracle_path.write_text(json.dumps({"schema_version": schema}), encoding="utf-8")
    output = tmp_path / "must-not-exist.json"
    authority = SimpleNamespace(document=freeze_doc, sha256=freeze_sha)
    reverified = SimpleNamespace(ratified=authority)
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "load_ratified_freeze", lambda root: object(),
    )
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "reverify_published_freeze",
        lambda ratified, root: reverified,
    )
    monkeypatch.setattr(verdict.s8b_oracle_spec, "load_approved_spec", lambda root: object())
    monkeypatch.setattr(
        verdict.s8b_oracle_manifest, "verify_manifest", lambda path, **kwargs: object(),
    )
    monkeypatch.setattr(
        verdict, "verify_prediction",
        lambda document, *, freeze, root: verdict.VerifiedPrediction(document=document),
    )

    def load_oracle_only(path, **kwargs):
        loaded = artifacts.load_official_verdict(path)
        return _unsafe_verified_oracle_for_judge_unit_test(loaded)

    monkeypatch.setattr(verdict, "verify_oracle_verdict", load_oracle_only)

    rc = verdict.main([
        "judge", "--prediction", str(prediction_path), "--oracle", str(oracle_path),
        "--manifest", str(tmp_path / "manifest.json"),
        "--observations", str(tmp_path / "observations.json"),
        "--freeze", str(freeze_path), "--freeze-sha256", freeze_sha,
        "--root", str(tmp_path), "--out", str(output),
    ])

    assert rc == 2
    assert not output.exists()


def test_cli_rejects_freeze_sha_mismatch(tmp_path, monkeypatch):
    freeze_doc = _v2_freeze_document()
    freeze_doc["floor_protocol"] = {"path": "protocol.json", "sha256": "0" * 64}
    freeze_path = tmp_path / "freeze.json"
    _write_json(freeze_path, freeze_doc)
    rc = verdict.main([
        "judge", "--prediction", str(tmp_path / "p.json"),
        "--oracle", str(tmp_path / "o.json"),
        "--manifest", str(tmp_path / "m.json"),
        "--observations", str(tmp_path / "obs.json"),
        "--freeze", str(freeze_path), "--freeze-sha256", "1" * 64,
        "--root", str(tmp_path), "--out", str(tmp_path / "out.json")])
    assert rc == 2  # freeze byte sha256 不一致 → fail-closed


def test_cli_rejects_freeze_identity_mismatch_before_consumers(tmp_path, monkeypatch):
    freeze_doc = _v2_freeze_document()
    freeze_path = tmp_path / "freeze.json"
    freeze_sha = _write_json(freeze_path, freeze_doc)
    published = SimpleNamespace(
        ratified=SimpleNamespace(document=freeze_doc, sha256="f" * 64),
    )
    calls = []
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "load_ratified_freeze", lambda root: object(),
    )
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "reverify_published_freeze",
        lambda ratified, root: published,
    )
    monkeypatch.setattr(verdict.s8b_oracle_spec, "load_approved_spec", lambda root: object())
    monkeypatch.setattr(
        verdict.s8b_oracle_manifest, "verify_manifest", lambda path, **kwargs: object(),
    )
    monkeypatch.setattr(
        verdict, "verify_prediction", lambda *args, **kwargs: calls.append("prediction"),
    )
    monkeypatch.setattr(
        verdict, "verify_oracle_verdict", lambda *args, **kwargs: calls.append("oracle"),
    )
    output = tmp_path / "must-not-exist.json"

    rc = verdict.main([
        "judge", "--prediction", str(tmp_path / "p.json"),
        "--oracle", str(tmp_path / "o.json"),
        "--manifest", str(tmp_path / "m.json"),
        "--observations", str(tmp_path / "obs.json"),
        "--freeze", str(freeze_path), "--freeze-sha256", freeze_sha,
        "--root", str(tmp_path), "--out", str(output),
    ])

    assert rc == 2
    assert calls == []
    assert not output.exists()
