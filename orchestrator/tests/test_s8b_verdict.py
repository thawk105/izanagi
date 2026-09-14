# -*- coding: utf-8 -*-
"""8b 結合 judge (§6 判定表 v3) の三値・holdout 束縛・型分離。"""
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
from orchestrator.campaign import s8b_holdout_freeze as holdout_freeze  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze as ratified_freeze  # noqa: E402
from orchestrator.calibrator import perf_preflight  # noqa: E402
from orchestrator.campaign.s8b_selector_input import (  # noqa: E402
    CHOICE_TO_BINDING,
    STATIC_DEFAULT_CHOICE_ID,
)
import test_s8b_oracle_report as report_fixtures  # noqa: E402
import test_s8b_ratified_freeze as ratified_fixture  # noqa: E402

STOCK = verdict.STOCK_CONFIGURATION  # "stock_common"

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
            row = {
                "target_holdout": holdout_id,
                "arm": arm,
                "choice_id": choice,
                "status": "valid" if choice is not None else "invalid",
            }
            # off arm の decision_method/binding_key は型検査の入力になる。
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


def run(prediction: dict, oracle: artifacts.OfficialVerdict, *,
        expected=EXPECTED, floor_source=None) -> dict:
    """三値判定本体だけを対象に、検証済み token 形へ包んで呼ぶ薄いラッパ。"""
    return verdict.judge_combined(
        prediction=verdict.VerifiedPrediction(document=prediction),
        oracle=_unsafe_verified_oracle_for_judge_unit_test(oracle),
        expected_holdouts=expected,
        floor_source=({} if floor_source is None else floor_source))


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
    result = run(prediction, oracle)
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert result["status"] == verdict.HOLDS


def test_condition1_refuted_when_all_holdouts_identical():
    prediction = make_prediction({
        H1: {"on": "c06", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = run(prediction, oracle)
    assert _cond(result, "on_off_prediction_difference") == verdict.REFUTED
    assert result["status"] == verdict.REFUTED


def test_condition1_indeterminate_when_missing_and_no_difference():
    prediction = make_prediction({
        H1: {"on": None, "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 10.0}},
    })
    result = run(prediction, oracle)
    assert _cond(result, "on_off_prediction_difference") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


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
    result = run(prediction, oracle)
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    assert result["status"] == verdict.HOLDS


def test_condition2_refuted_when_one_holdout_does_not_follow():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c03"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    result = run(prediction, oracle)
    assert _cond(result, "swapped_follow") == verdict.REFUTED
    assert result["status"] == verdict.REFUTED


def test_condition2_indeterminate_when_a_swapped_cell_is_missing():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": None},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 10.0, "c06": 10.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 10.0, "c06": 10.0}},
    })
    result = run(prediction, oracle)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


# ---- oracle 状態は診断専用 --------------------------------------------------

@pytest.mark.parametrize("oracle_verdict", ["tie", "indeterminate"])
def test_oracle_verdict_is_diagnostic_only(oracle_verdict):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": oracle_verdict, "tied": ["c01", "c06"],
             "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    oracle["status"] = "indeterminate" if oracle_verdict == "indeterminate" else "determinate"

    result = run(prediction, oracle)

    assert result["status"] == verdict.HOLDS
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
    assert result["holdouts"][H1]["oracle_verdict"] == oracle_verdict
    assert result["evidence"]["oracle_status"] == oracle["status"]
    assert "oracle_floor_exceeded" not in result["conditions"]
    assert "same_holdout_coupled_verdict" not in result
    assert "protocol_violations" not in result


@pytest.mark.parametrize("oracle_verdict", ["tie", "indeterminate"])
def test_oracle_verdict_does_not_mask_refuted_prediction_difference(oracle_verdict):
    prediction = make_prediction({
        H1: {"on": "c06", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c06"},
    })
    oracle = make_oracle({
        H1: {"verdict": oracle_verdict, "tied": ["c01", "c06"],
             "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c06": 100.0}},
    })
    oracle["status"] = "indeterminate" if oracle_verdict == "indeterminate" else "determinate"

    result = run(prediction, oracle)

    assert result["status"] == verdict.REFUTED
    assert _cond(result, "on_off_prediction_difference") == verdict.REFUTED


@pytest.mark.parametrize("oracle_verdict", ["tie", "indeterminate"])
def test_oracle_verdict_does_not_mask_refuted_swapped_follow(oracle_verdict):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c03"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": oracle_verdict, "tied": ["c01", "c06"],
             "configs": {"c01": 100.0, "c06": 100.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    oracle["status"] = "indeterminate" if oracle_verdict == "indeterminate" else "determinate"

    result = run(prediction, oracle)

    assert result["status"] == verdict.REFUTED
    assert _cond(result, "swapped_follow") == verdict.REFUTED


# ---- 結論の連言 (成立の代表) ----------------------------------------------

def test_conclusion_holds_when_both_conditions_hold():
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    result = run(prediction, oracle)
    assert _cond(result, "on_off_prediction_difference") == verdict.HOLDS
    assert _cond(result, "swapped_follow") == verdict.HOLDS
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
    result = run(prediction, oracle)
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert result["status"] == verdict.INDETERMINATE


# ---- 構造破綻の fail-closed --------------------------------------------------

def test_malformed_prediction_is_fully_indeterminate():
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    result = run({"schema_version": "wrong", "rows": "not-a-list"}, oracle)
    assert result["status"] == verdict.INDETERMINATE
    for name in ("on_off_prediction_difference", "swapped_follow"):
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
    result = run(prediction, oracle)
    assert result["evidence"]["prediction_body_sha256"] == "a" * 64
    assert result["evidence"]["oracle_manifest_sha256"] == "manifest-sha"
    assert result["evidence"]["oracle_status"] == "determinate"
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
    with pytest.raises(verdict.VerdictError, match="VerifiedPrediction"):
        verdict.judge_combined(
            prediction=prediction, oracle=oracle,
            expected_holdouts=EXPECTED, floor_source={})


def test_judge_combined_rejects_unverified_official_oracle_verdict():
    prediction = verdict.VerifiedPrediction(document=make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c02"},
        H2: {"on": "c02", "off": "c06", "swapped": "c01"},
    }))
    official = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
        H2: {"verdict": "unique-best", "configs": {"c02": 100.0, "c06": 50.0}},
    })
    for unverified in (
            official, dict(official), artifacts.ExplorationArtifact(official)):
        with pytest.raises(verdict.VerdictError, match="VerifiedOracleVerdict"):
            verdict.judge_combined(
                prediction=prediction, oracle=unverified,
                expected_holdouts=EXPECTED, floor_source={},
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
    with pytest.raises(verdict.VerdictError, match="VerifiedOracleVerdict"):
        verdict.judge_combined(
            prediction=prediction,
            oracle=SimpleNamespace(document=official),
            expected_holdouts=EXPECTED,
            floor_source={},
        )


def test_verified_oracle_verdict_rejects_direct_construction():
    official = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c06": 1.0}},
    })
    with pytest.raises(verdict.VerdictError, match="検証結果からのみ"):
        verdict.VerifiedOracleVerdict(document=official)


def test_judge_combined_rejects_post_issuance_oracle_document_tampering(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_combined_rejects_post_issuance_oracle_document_tampering"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_combined_rejects_post_issuance_oracle_document_tampering(tmp_path):
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
            expected_holdouts=EXPECTED,
            floor_source={},
        )


def test_judge_combined_rejects_nested_semantic_subclass_in_sealed_document(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_combined_rejects_nested_semantic_subclass_in_sealed_document"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_combined_rejects_nested_semantic_subclass_in_sealed_document(tmp_path):
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
            expected_holdouts=set(verified_oracle.document["holdouts"]),
            floor_source={},
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

    campaign_id = next(iter(manifest_document["campaign_ids"].values()))
    if isinstance(campaign_id, dict):
        campaign_id = campaign_id["campaign_id"]
    rows = []
    for ordinal, schedule_row in enumerate(manifest_document["schedule"]["rows"], start=1):
        rows.append({
            "schedule_index": schedule_row["schedule_index"],
            "campaign_id": campaign_id,
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
    expected_cells = [{
        "schedule_index": row["schedule_index"],
        "holdout_id": row["holdout_id"],
        "configuration_id": row["configuration_id"],
    } for row in rows]
    observations = artifacts.OfficialObservations({
        "schema_version": artifacts.OFFICIAL_OBSERVATIONS_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": verified_manifest.sha256,
        "spec_sha256": approved.sha256,
        "n_per_cell": manifest_document["schedule"]["n"],
        "campaign_verifier_epochs": [{
            "campaign_id": campaign_id,
            "campaign_verifier_epoch": f"E1:{'e' * 64}",
            "state": "E1",
            "reason_code": "recorded-closure",
            "identity_scope": "fixture enforcement closure",
            "excluded_scope": "fixture excluded verifier implementation",
            "certified_eligible": True,
            "rejection": None,
        }],
        "expected_cells": expected_cells,
        "store_reverification": {
            "state": "verified",
            "cells": [{
                "cell_id": cell_id,
                "store_path": f"fixture-store/{cell_id.replace('::', '--')}",
                "expected_sha256": "c" * 64,
                "actual_sha256": "c" * 64,
                "state": "match",
            } for cell_id in sorted({
                f"{entry['holdout_id']}::{entry['configuration_id']}"
                for entry in expected_cells
            })],
        },
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_accepts_rederived_exact_match"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_accepts_rederived_exact_match(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_boolean_median_type_confusion"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_boolean_median_type_confusion(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_wrong_authority_observations"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_wrong_authority_observations(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_extra_top_level_key"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_extra_top_level_key(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_requires_exact_authority_types"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_requires_exact_authority_types(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_approved_spec_from_other_manifest"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_approved_spec_from_other_manifest(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_post_issuance_manifest_tampering"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_post_issuance_manifest_tampering(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_semantic_sha256_subclass"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_semantic_sha256_subclass(tmp_path):
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
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_nested_semantic_dict_subclass"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_nested_semantic_dict_subclass(tmp_path):
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
    result = run(prediction, oracle)
    assert result["status"] != verdict.HOLDS
    assert result["status"] == verdict.INDETERMINATE
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE
    assert any(reason["code"] == "missing-holdout" for reason in result["reasons"])


def test_single_holdout_would_hold_without_cardinality_guard():
    prediction = _single_holdout_self_consistent()
    oracle = make_oracle({
        H1: {"verdict": "unique-best", "configs": {"c01": 100.0, "c06": 50.0}},
    })
    degenerate = run(prediction, oracle, expected=frozenset({H1}))
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
    result = run(prediction, oracle)
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
    result = run(prediction, oracle, expected=bad_expected)
    assert result["status"] == verdict.INDETERMINATE
    for name in ("on_off_prediction_difference", "swapped_follow"):
        assert _cond(result, name) == verdict.INDETERMINATE


# ---- CLI (C2-7): floors/holdouts 廃止 + freeze / floor_source 検証 -----------

def _freeze_document() -> dict:
    """_validate_execution_snapshot を通す最小の freeze を組む。"""
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


def _real_g1_with_scan_neutral_earlier_result(
        tmp_path: Path,
) -> tuple[Path, str, str, str]:
    root, freeze_sha, freeze_rel, _g1, topology = (
        ratified_fixture.build_production_emitter_g1(tmp_path)
    )
    selected_rel = topology["paths"]["result"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    earlier_rel = selected_rel.replace(
        selected_run_id, f"20260718T115959Z-{proto8}",
    )
    assert earlier_rel != selected_rel
    earlier_path = root / earlier_rel
    earlier_path.parent.mkdir(parents=True, exist_ok=True)
    earlier_path.write_bytes(b"{}")
    assert earlier_path.read_bytes() != (root / selected_rel).read_bytes()
    ratified_fixture._commit_exact(
        root,
        [earlier_rel],
        subject="scan-neutral earlier official result",
        agent="fixture",
    )
    return root, freeze_sha, freeze_rel, earlier_rel


def test_verdict_cli_real_g1_rule_mismatch_preserves_selection_reason(
        tmp_path, monkeypatch, capsys):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verdict_cli_real_g1_rule_mismatch_preserves_selection_reason"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verdict_cli_real_g1_rule_mismatch_preserves_selection_reason(tmp_path, monkeypatch):
    import contextlib
    import io
    from types import SimpleNamespace

    captured_stderr = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr):
        root, freeze_sha, freeze_rel, earlier_rel = (
            _real_g1_with_scan_neutral_earlier_result(tmp_path)
        )
        eligibility_calls = []

        def derive_eligibility(**kwargs):
            eligibility_calls.append(kwargs["result_rel"])
            return kwargs["result_rel"] == earlier_rel

        monkeypatch.setattr(
            holdout_freeze,
            "_derive_floor_selection_eligibility",
            derive_eligibility,
        )
        # These seams begin after the real historical reverify.  With the selection
        # assertion removed, the same input must therefore reach rc=0 rather than a
        # different downstream rejection.
        monkeypatch.setattr(verdict.s8b_oracle_spec, "load_approved_spec", lambda root: object())
        monkeypatch.setattr(
            verdict.s8b_oracle_manifest, "verify_manifest", lambda path, **kwargs: object(),
        )
        monkeypatch.setattr(verdict, "_validate_execution_snapshot", lambda *args, **kwargs: None)
        monkeypatch.setattr(verdict, "verify_prediction", lambda *args, **kwargs: object())
        monkeypatch.setattr(verdict, "verify_oracle_verdict", lambda *args, **kwargs: object())
        monkeypatch.setattr(
            verdict, "judge_combined", lambda **kwargs: {"status": "selection-gate-passed"},
        )
        prediction_path = tmp_path / "prediction.json"
        prediction_path.write_text("{}", encoding="utf-8")
        output = tmp_path / "must-not-exist.json"

        rc = verdict.main([
            "judge", "--prediction", str(prediction_path),
            "--oracle", str(tmp_path / "oracle.json"),
            "--manifest", str(tmp_path / "manifest.json"),
            "--observations", str(tmp_path / "observations.json"),
            "--freeze", str(root / freeze_rel), "--freeze-sha256", freeze_sha,
            "--root", str(root), "--out", str(output),
        ])

        captured = SimpleNamespace(err=captured_stderr.getvalue())
        assert rc == 2
        assert "floor-selection-rule-mismatch" in captured.err
        assert "earliest-eligible-official-run-id/v1" in captured.err
        assert eligibility_calls == [earlier_rel]
        assert not output.exists()


def test_verdict_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate(
        tmp_path, monkeypatch, capsys):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verdict_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verdict_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate(tmp_path, monkeypatch):
    import contextlib
    import io
    from types import SimpleNamespace

    captured_stderr = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr):
        root, freeze_sha, freeze_rel, _g1, _topology = (
            ratified_fixture.build_production_emitter_g1(tmp_path)
        )
        cli_root = Path(root)
        events = []
        loaded = []
        selection_calls = []
        real_load = ratified_freeze.load_ratified_freeze
        real_selection = ratified_freeze.assert_g1_floor_selection_identity

        def load_ratified(candidate_root):
            candidate = real_load(candidate_root)
            loaded.append(candidate)
            return candidate

        def assert_selection(candidate, candidate_root):
            events.append("selection")
            selection_calls.append((candidate, candidate_root))
            return real_selection(candidate, candidate_root)

        def reached_reverify(candidate, candidate_root):
            events.append("reverify")
            raise ratified_freeze.RatifiedFreezeError(
                "test-reverify-sentinel", "actual selection gate completed",
            )

        monkeypatch.setattr(ratified_freeze, "load_ratified_freeze", load_ratified)
        monkeypatch.setattr(
            ratified_freeze, "assert_g1_floor_selection_identity", assert_selection,
        )
        monkeypatch.setattr(ratified_freeze, "reverify_published_freeze", reached_reverify)
        output = tmp_path / "must-not-exist.json"

        rc = verdict.main([
            "judge", "--prediction", str(tmp_path / "prediction.json"),
            "--oracle", str(tmp_path / "oracle.json"),
            "--manifest", str(tmp_path / "manifest.json"),
            "--observations", str(tmp_path / "observations.json"),
            "--freeze", str(root / freeze_rel), "--freeze-sha256", freeze_sha,
            "--root", str(root), "--out", str(output),
        ])

        captured = SimpleNamespace(err=captured_stderr.getvalue())
        assert rc == 2
        assert events == ["selection", "reverify"]
        assert len(loaded) == 1
        assert selection_calls == [(loaded[0], cli_root)]
        assert selection_calls[0][0] is loaded[0]
        assert type(selection_calls[0][1]) is type(cli_root)
        assert selection_calls[0][1] == cli_root
        assert "test-reverify-sentinel" in captured.err
        assert not output.exists()


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


def test_cli_preserves_freeze_and_floor_source_wiring(tmp_path, monkeypatch):
    # 外部 authority I/O は個別 E2E で覆うため、ここは CLI の順序・freeze 検証・floor_source wiring を検証する。
    freeze_doc = _freeze_document()
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
    selection_calls = []
    cli_root = Path(tmp_path)
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

    def assert_selection(value, root):
        calls.append("selection")
        selection_calls.append((value, root))

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

    def read_floor_source(value, root):
        calls.append("floor-source")
        assert value is reverified.ratified
        return b"{}"

    def verify_prediction(document, *, freeze, root):
        calls.append("prediction")
        return verdict.VerifiedPrediction(document=document)

    def verify_oracle(path, **kwargs):
        calls.append("oracle")
        assert kwargs["verified_manifest"] is verified_manifest
        assert kwargs["approved_spec"] is approved
        return _unsafe_verified_oracle_for_judge_unit_test(oracle)

    real_judge_combined = verdict.judge_combined

    def judge_combined(**kwargs):
        calls.append("judge")
        assert kwargs["expected_holdouts"] == EXPECTED
        assert kwargs["floor_source"] == {}
        assert "floor_by_holdout" not in kwargs
        assert "scale_tolerance" not in kwargs
        return real_judge_combined(**kwargs)

    monkeypatch.setattr(verdict, "load_verified_freeze", load_freeze)
    monkeypatch.setattr(verdict.s8b_ratified_freeze, "load_ratified_freeze", load_ratified)
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze,
        "assert_g1_floor_selection_identity",
        assert_selection,
    )
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "reverify_published_freeze", reverify,
    )
    monkeypatch.setattr(verdict.s8b_oracle_spec, "load_approved_spec", load_approved)
    monkeypatch.setattr(verdict.s8b_oracle_manifest, "verify_manifest", verify_manifest)
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze, "read_floor_source_blob", read_floor_source,
    )
    monkeypatch.setattr(verdict, "verify_prediction", verify_prediction)
    monkeypatch.setattr(verdict, "verify_oracle_verdict", verify_oracle)
    monkeypatch.setattr(verdict, "judge_combined", judge_combined)

    rc = verdict.main([
        "judge", "--prediction", str(pred_path), "--oracle", str(oracle_path),
        "--manifest", str(tmp_path / "manifest.json"),
        "--observations", str(tmp_path / "observations.json"),
        "--freeze", str(freeze_path), "--freeze-sha256", freeze_sha,
        "--root", str(tmp_path), "--out", str(out_path)])
    assert rc == 0
    assert calls == [
        "freeze", "ratified", "selection", "reverify", "approved", "manifest",
        "floor-source", "prediction", "oracle", "judge",
    ]
    assert selection_calls == [(ratified, cli_root)]
    assert selection_calls[0][0] is ratified
    assert type(selection_calls[0][1]) is type(cli_root)
    assert selection_calls[0][1] == cli_root
    out = json.loads(out_path.read_text(encoding="utf-8"))
    assert out["status"] == verdict.HOLDS
    assert out["holdouts"][H1]["oracle_verdict"] == "unique-best"
    assert out["schema_version"] == "8b-combined-verdict/v2"
    assert "oracle_floor_exceeded" not in out["conditions"]
    assert "same_holdout_coupled_verdict" not in out
    assert "protocol_violations" not in out


@pytest.mark.parametrize("schema", [
    None,
    "unknown/v1",
    artifacts.OFFICIAL_OBSERVATIONS_SCHEMA,
    artifacts.EXPLORATION_ARTIFACT_SCHEMA,
])
def test_cli_rejects_non_verdict_oracle_schema_without_output(
    tmp_path, monkeypatch, schema,
):
    freeze_doc = _freeze_document()
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
    loaded_ratified = object()
    cli_root = Path(tmp_path)
    selection_calls = []
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze,
        "load_ratified_freeze",
        lambda root: loaded_ratified,
    )
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
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
    assert selection_calls == [(loaded_ratified, cli_root)]
    assert selection_calls[0][0] is loaded_ratified
    assert type(selection_calls[0][1]) is type(cli_root)
    assert selection_calls[0][1] == cli_root
    assert not output.exists()


def test_cli_rejects_freeze_sha_mismatch(tmp_path, monkeypatch):
    freeze_doc = _freeze_document()
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
    freeze_doc = _freeze_document()
    freeze_path = tmp_path / "freeze.json"
    freeze_sha = _write_json(freeze_path, freeze_doc)
    published = SimpleNamespace(
        ratified=SimpleNamespace(document=freeze_doc, sha256="f" * 64),
    )
    calls = []
    loaded_ratified = object()
    cli_root = Path(tmp_path)
    selection_calls = []
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze,
        "load_ratified_freeze",
        lambda root: loaded_ratified,
    )
    monkeypatch.setattr(
        verdict.s8b_ratified_freeze,
        "assert_g1_floor_selection_identity",
        lambda candidate, candidate_root: selection_calls.append(
            (candidate, candidate_root)
        ),
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
    assert selection_calls == [(loaded_ratified, cli_root)]
    assert selection_calls[0][0] is loaded_ratified
    assert type(selection_calls[0][1]) is type(cli_root)
    assert selection_calls[0][1] == cli_root
    assert calls == []
    assert not output.exists()


def _degraded_observation() -> dict:
    receipt = {
        "schema": perf_preflight.SCHEMA,
        "status": "unavailable",
        "available": False,
        "probe_argv": list(perf_preflight._BASE_PROBE_ARGV),
        "rc": None,
        "parsed_events": [],
        "reason": "perf-not-found",
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }
    observation = perf_preflight.build_perf_observation(
        receipt,
        run_cmd=["ccbench"],
        leading_indicators={"ipc": None, "llc_miss_rate": None},
    )
    assert observation is not None
    return observation


def _measurement_condition(observation: dict) -> dict:
    return {
        "campaign_id": "oracle-b0",
        "measurement_manifest_sha256": "c" * 64,
        "perf_observation": observation,
    }


def _degraded_floor_source(observation: dict) -> dict:
    return {
        "perf_preflight": observation["preflight"],
        "perf_observation": observation,
        "sessions": [{
            "cell_id": "h1::stock_common",
            "run_cmd": ["ccbench"],
            "ipc": None,
            "llc_miss_rate": None,
        }],
        "binaries": {},
    }


def _combined_measurement_case(observation: dict):
    prediction = make_prediction({
        H1: {"on": "c01", "off": "c06", "swapped": "c06"},
        H2: {"on": "c06", "off": "c06", "swapped": "c01"},
    })
    oracle = make_oracle({
        H1: {
            "verdict": "unique-best",
            "winner": "c01",
            "configs": {"c01": 20.0, "c06": 10.0},
        },
        H2: {
            "verdict": "unique-best",
            "winner": "c06",
            "configs": {"c06": 10.0},
        },
    })
    oracle["measurement_conditions"] = [_measurement_condition(observation)]
    return prediction, oracle


def test_verify_oracle_verdict_rejects_handwritten_measurement_conditions(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_verify_oracle_verdict_rejects_handwritten_measurement_conditions"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_verify_oracle_verdict_rejects_handwritten_measurement_conditions(tmp_path):
    case = _oracle_verifier_case(tmp_path)
    observation = _degraded_observation()
    case.observations["measurement_conditions"] = [
        _measurement_condition(observation),
    ]
    oracle = oracle_judge.judge_oracle(
        case.observations,
        schedule_projection=case.schedule_projection,
        verified_manifest_sha256=case.verified_manifest.sha256,
        approved_spec_sha256=case.approved.sha256,
    )
    case.observations_path.write_text(
        json.dumps(case.observations, ensure_ascii=False), encoding="utf-8",
    )
    forged = deepcopy(oracle)
    forged["measurement_conditions"][0]["measurement_manifest_sha256"] = "d" * 64
    forged_path = tmp_path / "oracle-handwritten-measurement-condition.json"
    _write_oracle_variant(forged_path, forged)

    with pytest.raises(verdict.VerdictError, match="再導出結果"):
        verdict.verify_oracle_verdict(
            forged_path,
            observations_source=case.observations_path,
            verified_manifest=case.verified_manifest,
            approved_spec=case.approved,
        )


def test_combined_verdict_measurement_mismatch_is_indeterminate():
    observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(observation)

    result = run(prediction, oracle, floor_source={})

    assert result["status"] == verdict.INDETERMINATE
    assert {entry["code"] for entry in result["reasons"]} == {
        "measurement-conditions-mismatch",
    }
    assert _cond(result, "on_off_prediction_difference") == verdict.INDETERMINATE
    assert _cond(result, "swapped_follow") == verdict.INDETERMINATE


def test_combined_verdict_matching_degraded_conditions_propagate():
    observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(observation)

    result = run(
        prediction,
        oracle,
        floor_source=_degraded_floor_source(observation),
    )

    assert result["status"] == verdict.HOLDS
    assert result["measurement_conditions"] == {
        "floor_perf_observation": observation,
        "oracle": [_measurement_condition(observation)],
    }


def test_combined_verdict_different_floor_and_oracle_observations_indeterminate():
    floor_observation = _degraded_observation()
    oracle_observation = deepcopy(floor_observation)
    oracle_observation["preflight"]["stderr_sha256"] = "1" * 64
    prediction, oracle = _combined_measurement_case(oracle_observation)

    result = run(
        prediction,
        oracle,
        floor_source=_degraded_floor_source(floor_observation),
    )

    assert result["status"] == verdict.INDETERMINATE
    assert {entry["code"] for entry in result["reasons"]} == {
        "measurement-conditions-mismatch",
    }


def test_combined_verdict_empty_oracle_observations_with_floor_indeterminate():
    floor_observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(floor_observation)
    oracle["measurement_conditions"] = []

    result = run(
        prediction,
        oracle,
        floor_source=_degraded_floor_source(floor_observation),
    )

    assert result["status"] == verdict.INDETERMINATE
    assert "measurement-conditions-mismatch" in {
        entry["code"] for entry in result["reasons"]
    }


def test_combined_verdict_exact_floor_and_oracle_observations_not_indeterminate():
    observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(observation)

    result = run(
        prediction,
        oracle,
        floor_source=_degraded_floor_source(observation),
    )

    assert result["status"] == verdict.HOLDS
    assert "measurement-conditions-mismatch" not in {
        entry["code"] for entry in result["reasons"]
    }


def test_combined_verdict_calls_claim_gate_before_condition_comparison(monkeypatch):
    observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(observation)
    calls = []
    monkeypatch.setattr(
        verdict._perf_preflight,
        "perf_claim_allowed",
        lambda *args, **kwargs: calls.append((args, kwargs)) or False,
    )

    result = run(
        prediction,
        oracle,
        floor_source=_degraded_floor_source(observation),
    )

    assert calls
    assert result["status"] == verdict.INDETERMINATE
    assert {entry["code"] for entry in result["reasons"]} == {
        "floor-measurement-claim",
    }


def test_all_perf_combined_verdict_preserves_exact_keys():
    observation = _degraded_observation()
    prediction, oracle = _combined_measurement_case(observation)
    oracle.pop("measurement_conditions")

    result = run(prediction, oracle, floor_source={})

    assert set(result) == {
        "schema_version", "status", "conditions", "holdouts", "evidence", "reasons",
    }
