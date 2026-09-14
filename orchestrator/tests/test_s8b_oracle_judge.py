# -*- coding: utf-8 -*-
"""8b oracle judge の三値・argmax・入力順独立性を検査する。"""
from __future__ import annotations

import copy
import inspect
import json
import math
import random
import sys
from pathlib import Path
from unittest import mock

import pytest

ORCH = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ORCH.parent))
sys.path.insert(0, str(TESTS))

from orchestrator.campaign import s8b_oracle_judge as judge  # noqa: E402
from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze as holdout_freeze  # noqa: E402
from orchestrator.campaign import s8b_oracle_manifest as oracle_manifest  # noqa: E402
from orchestrator.campaign import s8b_oracle_spec as oracle_spec  # noqa: E402
from orchestrator.calibrator import perf_preflight  # noqa: E402
import test_s8b_oracle_report as report_fixtures  # noqa: E402
import test_s8b_ratified_freeze as ratified_fixture  # noqa: E402


# 注意: holdout の三軸 conjunction は JSON 形の静止リテラルにしない。
# judge fixture は workload 値を持たず、opaque な holdout_id だけを使う。
CONFIGURATIONS = tuple(f"c{i}" for i in range(6))
MANIFEST_SHA256 = "a" * 64
SPEC_SHA256 = "b" * 64
CAMPAIGN_ID = "oracle-b0"


def _store_reverification(expected_cells) -> dict:
    logical_cell_ids = sorted({
        f"{entry['holdout_id']}::{entry['configuration_id']}"
        for entry in expected_cells
    })
    return {
        "state": "verified",
        "cells": [{
            "cell_id": cell_id,
            "store_path": f"fixture-store/{cell_id.replace('::', '--')}",
            "expected_sha256": "c" * 64,
            "actual_sha256": "c" * 64,
            "state": "match",
        } for cell_id in logical_cell_ids],
    }


def _e1_evidence() -> list[dict]:
    return [{
        "campaign_id": CAMPAIGN_ID,
        "campaign_verifier_epoch": f"E1:{'e' * 64}",
        "state": "E1",
        "reason_code": "recorded-closure",
        "identity_scope": "fixture enforcement closure",
        "excluded_scope": "fixture excluded verifier implementation",
        "certified_eligible": True,
        "rejection": None,
    }]


def _observations(
    *, n: int = 2, holdouts: tuple[str, ...] = ("rr80",),
) -> artifacts.OfficialObservations:
    rows = []
    index = 0
    for holdout_id in holdouts:
        for config_index, configuration_id in enumerate(CONFIGURATIONS):
            for replicate in range(n):
                value = float(config_index * 10 + replicate)
                rows.append({
                    "schedule_index": index,
                    "campaign_id": CAMPAIGN_ID,
                    "block_id": "b0",
                    "holdout_id": holdout_id,
                    "configuration_id": configuration_id,
                    "attempt": 1,
                    "status": "completed",
                    "outcome": "committed",
                    "binding_ok": True,
                    "legacy_verify": "pass",
                    "s2_verify": "pass",
                    "bench_values": [
                        value, value + 1.0, value + 2.0, value + 3.0, value + 4.0,
                    ],
                    "excluded_reason": None,
                    "screen_outcome": "not_enabled",
                    "reason": None,
                })
                index += 1
    expected_cells = [{
        "schedule_index": row["schedule_index"],
        "holdout_id": row["holdout_id"],
        "configuration_id": row["configuration_id"],
    } for row in rows]
    return artifacts.OfficialObservations({
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": MANIFEST_SHA256,
        "spec_sha256": SPEC_SHA256,
        "n_per_cell": n,
        "campaign_verifier_epochs": _e1_evidence(),
        "expected_cells": expected_cells,
        "store_reverification": _store_reverification(expected_cells),
        "rows": rows,
    })


def _holdout(verdict: dict) -> dict:
    return verdict["holdouts"]["rr80"]


def _judge(
        observations, *, manifest_sha256=MANIFEST_SHA256,
        spec_sha256=SPEC_SHA256, schedule_projection=None):
    if schedule_projection is None:
        schedule_projection = judge.ManifestScheduleProjection(
            n_per_cell=observations.get("n_per_cell", 1),
            expected_cells=frozenset(
                (
                    entry["schedule_index"],
                    entry["holdout_id"],
                    entry["configuration_id"],
                )
                for entry in observations.get("expected_cells", [])
                if isinstance(entry, dict)
                and set(entry) == judge._EXPECTED_CELL_KEYS
            ),
            expected_campaign_ids=frozenset({CAMPAIGN_ID}),
        )
    return judge.judge_oracle(
        observations,
        schedule_projection=schedule_projection,
        verified_manifest_sha256=manifest_sha256,
        approved_spec_sha256=spec_sha256,
    )


def test_complete_data_has_unique_best():
    result = _judge(_observations())

    assert type(result) is artifacts.OfficialVerdict
    assert _holdout(result)["verdict"] == "unique-best"
    assert _holdout(result)["winner_configuration_id"] == CONFIGURATIONS[-1]
    assert result["status"] == "determinate"


def test_official_store_reverification_absence_is_indeterminate():
    observations = _observations()
    assert _judge(observations)["status"] == "determinate"

    observations.pop("store_reverification")
    result = _judge(observations)

    assert result["status"] == "indeterminate"
    assert {reason["code"] for reason in result["reasons"]} == {
        "store-reverification-absent",
    }
    assert all(
        cell["status"] == "unknown"
        for holdout in result["holdouts"].values()
        for cell in holdout["configurations"].values()
    )


@pytest.mark.parametrize(
    ("damage", "reason_code"),
    [
        ("empty-mapping", "store-reverification-schema"),
        ("empty-cells", "store-reverification-cells"),
        ("missing-cell", "store-reverification-cell-coverage"),
        ("duplicate-cell", "store-reverification-duplicate"),
        ("verified-with-mismatch", "store-reverification-state"),
        ("unverified-with-all-match", "store-reverification-state"),
        ("mismatch-with-equal-sha", "store-reverification-cell-state"),
        ("missing-with-actual-sha", "store-reverification-cell-state"),
    ],
)
def test_store_reverification_rejects_non_tautological_receipts(
        damage, reason_code):
    observations = _observations()
    assert _judge(observations)["status"] == "determinate"
    receipt = observations["store_reverification"]
    if damage == "empty-mapping":
        observations["store_reverification"] = {}
    elif damage == "empty-cells":
        receipt["cells"] = []
    elif damage == "missing-cell":
        receipt["cells"].pop()
    elif damage == "duplicate-cell":
        receipt["cells"].append(copy.deepcopy(receipt["cells"][0]))
    elif damage == "verified-with-mismatch":
        receipt["cells"][0]["actual_sha256"] = "d" * 64
        receipt["cells"][0]["state"] = "mismatch"
    elif damage == "unverified-with-all-match":
        receipt["state"] = "unverified"
    elif damage == "mismatch-with-equal-sha":
        receipt["state"] = "unverified"
        receipt["cells"][0]["state"] = "mismatch"
    elif damage == "missing-with-actual-sha":
        receipt["state"] = "unverified"
        receipt["cells"][0]["state"] = "missing"
    else:  # pragma: no cover - parameter table is closed above
        raise AssertionError(damage)

    result = _judge(observations)
    assert result["status"] == "indeterminate"
    assert reason_code in {reason["code"] for reason in result["reasons"]}


@pytest.mark.parametrize("level", ["outer-extra", "cell-extra"])
def test_store_reverification_requires_exact_keys(level):
    observations = _observations()
    assert _judge(observations)["status"] == "determinate"
    if level == "outer-extra":
        observations["store_reverification"]["extra"] = None
        expected = "store-reverification-schema"
    else:
        observations["store_reverification"]["cells"][0]["extra"] = None
        expected = "store-reverification-cell-schema"

    result = _judge(observations)
    assert result["status"] == "indeterminate"
    assert expected in {reason["code"] for reason in result["reasons"]}


def test_store_reverification_rejects_receipt_cell_outside_schedule():
    observations = _observations()
    assert _judge(observations)["status"] == "determinate"
    observations["store_reverification"]["cells"].append({
        "cell_id": "outside::schedule",
        "store_path": "fixture-store/outside--schedule",
        "expected_sha256": "d" * 64,
        "actual_sha256": "d" * 64,
        "state": "match",
    })

    result = _judge(observations)
    assert result["status"] == "indeterminate"
    assert "store-reverification-cell-coverage" in {
        reason["code"] for reason in result["reasons"]
    }


@pytest.mark.parametrize(
    "store_path",
    ["/absolute/store", "../parent/store", "control\x01store", "back\\slash"],
    ids=["absolute", "parent", "control", "backslash"],
)
def test_store_reverification_rejects_noncanonical_path(store_path):
    observations = _observations()
    assert _judge(observations)["status"] == "determinate"
    observations["store_reverification"]["cells"][0]["store_path"] = store_path

    result = _judge(observations)
    assert result["status"] == "indeterminate"
    assert "store-reverification-store-path" in {
        reason["code"] for reason in result["reasons"]
    }


@pytest.mark.parametrize(
    ("state", "epoch", "reason_code"),
    [
        ("E0", "E0", "v1-authority-absent"),
        (
            "E1-stale", f"E1:{'d' * 64}",
            "recorded-current-closure-mismatch",
        ),
    ],
)
def test_non_e1_campaign_epoch_is_never_eligible(
        state, epoch, reason_code):
    observations = _observations()
    observations["campaign_verifier_epochs"] = [{
        "campaign_id": CAMPAIGN_ID,
        "campaign_verifier_epoch": epoch,
        "state": state,
        "reason_code": reason_code,
        "identity_scope": "fixture enforcement closure",
        "excluded_scope": "fixture excluded verifier implementation",
        "certified_eligible": False,
        "rejection": {
            "code": "campaign-verifier-epoch-rejected",
            "message": f"fixture rejected {state}",
        },
    }]

    result = _judge(observations)

    assert result["status"] == "indeterminate"
    assert _holdout(result)["verdict"] == "indeterminate"
    assert all(
        cell["status"] == "unknown"
        for cell in _holdout(result)["configurations"].values()
    )
    assert [reason["code"] for reason in result["reasons"]] == [
        "campaign-verifier-epoch-rejected"
    ]


@pytest.mark.parametrize("damage", ["missing", "eligible-e0", "campaign-set"])
def test_epoch_evidence_schema_or_campaign_binding_failure_is_indeterminate(
        damage):
    observations = _observations()
    if damage == "missing":
        observations.pop("campaign_verifier_epochs")
    elif damage == "eligible-e0":
        observations["campaign_verifier_epochs"][0].update(
            campaign_verifier_epoch="E0",
            state="E0",
            reason_code="v1-authority-absent",
        )
    else:
        observations["campaign_verifier_epochs"][0]["campaign_id"] = "other"

    result = _judge(observations)

    assert result["status"] == "indeterminate"
    assert _holdout(result)["verdict"] == "indeterminate"


def test_exact_maximum_tie_is_not_broken_by_a_floor():
    observations = _observations()
    for row in observations["rows"]:
        if row["configuration_id"] == CONFIGURATIONS[-2]:
            offset = float(row["schedule_index"] % 2)
            row["bench_values"] = [
                50.0 + offset, 51.0 + offset, 52.0 + offset,
                53.0 + offset, 54.0 + offset,
            ]

    result = _judge(observations)

    assert _holdout(result)["verdict"] == "tie"
    assert _holdout(result)["tied_configuration_ids"] == list(CONFIGURATIONS[-2:])
    assert _holdout(result)["winner_configuration_id"] is None


def test_exact_maximum_boundary_distinguishes_one_ulp_in_both_directions():
    observations = _observations()
    lower_configuration_id, upper_configuration_id = CONFIGURATIONS[-2:]
    for row in observations["rows"]:
        if row["configuration_id"] in {
            lower_configuration_id, upper_configuration_id,
        }:
            row["bench_values"] = [100.0]

    exact_tie = _holdout(_judge(observations))
    assert exact_tie["verdict"] == "tie"
    assert exact_tie["tied_configuration_ids"] == [
        lower_configuration_id, upper_configuration_id,
    ]
    assert exact_tie["winner_configuration_id"] is None

    for direction, adjusted_configuration_id, winner_configuration_id in (
        (math.inf, lower_configuration_id, lower_configuration_id),
        (-math.inf, upper_configuration_id, lower_configuration_id),
    ):
        one_ulp_apart = copy.deepcopy(observations)
        adjusted_value = math.nextafter(100.0, direction)
        for row in one_ulp_apart["rows"]:
            if row["configuration_id"] == adjusted_configuration_id:
                row["bench_values"] = [adjusted_value]

        result = _holdout(_judge(one_ulp_apart))
        assert result["verdict"] == "unique-best"
        assert result["tied_configuration_ids"] == []
        assert result["winner_configuration_id"] == winner_configuration_id


@pytest.mark.parametrize("damage", ["missing", "duplicate", "non-finite", "n-short", "binding"])
def test_quality_rule_violations_are_indeterminate(damage):
    observations = _observations()
    if damage == "missing":
        observations["rows"][0]["status"] = "not-started"
        observations["rows"][0]["outcome"] = None
    elif damage == "duplicate":
        observations["rows"].append(copy.deepcopy(observations["rows"][0]))
    elif damage == "non-finite":
        observations["rows"][0]["bench_values"] = [float("nan")]
    elif damage == "n-short":
        observations["n_per_cell"] = 3
    elif damage == "binding":
        observations["rows"][0]["binding_ok"] = False

    result = _judge(observations)

    assert _holdout(result)["verdict"] == "indeterminate"
    assert any(cell["status"] == "unknown"
               for cell in _holdout(result)["configurations"].values())


def test_huge_integer_bench_value_is_indeterminate():
    observations = _observations()
    observations["rows"][0]["bench_values"] = [10**400]

    result = _judge(observations)
    cell = _holdout(result)["configurations"][CONFIGURATIONS[0]]

    assert result["status"] == "indeterminate"
    assert cell["status"] == "unknown"
    assert any(reason["code"] == "non-finite" for reason in cell["reasons"])


def test_correctness_red_disqualifies_and_high_score_cannot_win():
    observations = _observations()
    red_config = CONFIGURATIONS[-1]
    for row in observations["rows"]:
        if row["configuration_id"] == red_config:
            row["outcome"] = "correctness-red"
            row["legacy_verify"] = "red"
            row["s2_verify"] = "missing"
            row["bench_values"] = [1_000_000.0]

    result = _judge(observations)
    holdout = _holdout(result)

    assert holdout["configurations"][red_config]["status"] == "disqualified"
    assert holdout["configurations"][red_config]["median_of_medians"] is None
    assert holdout["verdict"] == "unique-best"
    assert holdout["winner_configuration_id"] == CONFIGURATIONS[-2]


def test_non_string_excluded_reason_is_unknown():
    observations = _observations()
    observations["rows"][0]["excluded_reason"] = 123

    result = _judge(observations)
    cell = _holdout(result)["configurations"][CONFIGURATIONS[0]]

    assert cell["status"] == "unknown"
    assert any(reason["code"] == "excluded" and "文字列でない" in reason["message"]
               for reason in cell["reasons"])
    assert _holdout(result)["verdict"] == "indeterminate"


def test_correctness_red_with_excluded_reason_is_unknown_not_disqualified():
    observations = _observations()
    target = CONFIGURATIONS[-1]
    for row in observations["rows"]:
        if row["configuration_id"] == target:
            row["outcome"] = "correctness-red"
            row["legacy_verify"] = "red"
            row["s2_verify"] = "missing"
            row["excluded_reason"] = "machine-fault"

    result = _judge(observations)
    cell = _holdout(result)["configurations"][target]

    assert cell["status"] == "unknown"
    assert any(reason["code"] == "red-excluded" for reason in cell["reasons"])
    assert result["status"] == "indeterminate"


def test_committed_row_with_excluded_reason_is_not_eligible():
    observations = _observations()
    observations["rows"][0]["excluded_reason"] = "machine-fault"

    result = _judge(observations)
    cell = _holdout(result)["configurations"][CONFIGURATIONS[0]]

    assert cell["status"] == "unknown"
    assert any(reason["code"] == "excluded" and "null でない" in reason["message"]
               for reason in cell["reasons"])
    assert _holdout(result)["verdict"] == "indeterminate"


def test_verify_inconclusive_is_unknown_not_disqualified():
    observations = _observations()
    target = CONFIGURATIONS[-1]
    for row in observations["rows"]:
        if row["configuration_id"] == target:
            row["outcome"] = "verify-inconclusive"
            row["s2_verify"] = "missing"
            row["bench_values"] = []

    result = _judge(observations)
    cell = _holdout(result)["configurations"][target]

    assert cell["status"] == "unknown"
    assert result["status"] == "indeterminate"
    assert any(reason["code"] == "verify-inconclusive" for reason in cell["reasons"])


def test_binary_mismatch_is_unknown_not_disqualified():
    """C3-5: binary-mismatch outcome の trial は cell を unknown に倒す (計測 binary の
    真正性が壊れているため disqualify でなく判定不能に伝播)。"""
    observations = _observations()
    target = CONFIGURATIONS[-1]
    for row in observations["rows"]:
        if row["configuration_id"] == target:
            row["outcome"] = "binary-mismatch"
            row["s2_verify"] = "missing"
            row["legacy_verify"] = "missing"
            row["bench_values"] = []

    result = _judge(observations)
    cell = _holdout(result)["configurations"][target]

    assert cell["status"] == "unknown"
    assert result["status"] == "indeterminate"
    assert any(reason["code"] == "binary-mismatch" for reason in cell["reasons"])


def test_row_shuffle_does_not_change_verdict_json():
    observations = _observations()
    expected = _judge(observations)
    shuffled = copy.deepcopy(observations)
    random.Random(827).shuffle(shuffled["rows"])

    assert _judge(shuffled) == expected


def test_deleting_every_row_for_one_expected_holdout_is_indeterminate():
    observations = _observations(holdouts=("rr80", "h-second"))
    assert _judge(observations)["status"] == "determinate"
    observations["rows"] = [
        row for row in observations["rows"] if row["holdout_id"] != "h-second"
    ]

    result = _judge(observations)

    assert result["status"] == "indeterminate"
    assert result["holdouts"]["h-second"]["verdict"] == "indeterminate"
    assert any(reason["code"] == "expected-cell-mismatch" for reason in result["reasons"])


def _asymmetric_observations() -> artifacts.OfficialObservations:
    """median と mean が乖離する非対称配置 (V9 — C-A #3 の変異 kill 恒久化)。

    - c-low: 各 trial [10, 10, 10, 10, 60] → median 10 / mean 20。
    - c-high: 各 trial [15, 15, 15, 15, 15] → median 15 / mean 15。
    median 集約なら winner=c-high、mean 置換なら c-low が 20 で勝つ (winner 反転)。
    """
    configs = {
        "c-low": [10.0, 10.0, 10.0, 10.0, 60.0],
        "c-high": [15.0, 15.0, 15.0, 15.0, 15.0],
    }
    rows = []
    index = 0
    for configuration_id, values in configs.items():
        for _ in range(3):
            rows.append({
                "schedule_index": index,
                "campaign_id": CAMPAIGN_ID,
                "block_id": "b0",
                "holdout_id": "rr80",
                "configuration_id": configuration_id,
                "attempt": 1,
                "status": "completed",
                "outcome": "committed",
                "binding_ok": True,
                "legacy_verify": "pass",
                "s2_verify": "pass",
                "bench_values": list(values),
                "excluded_reason": None,
                "screen_outcome": "not_enabled",
                "reason": None,
            })
            index += 1
    expected_cells = [{
        "schedule_index": row["schedule_index"],
        "holdout_id": row["holdout_id"],
        "configuration_id": row["configuration_id"],
    } for row in rows]
    return artifacts.OfficialObservations({
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": MANIFEST_SHA256,
        "spec_sha256": SPEC_SHA256,
        "n_per_cell": 3,
        "campaign_verifier_epochs": _e1_evidence(),
        "expected_cells": expected_cells,
        "store_reverification": _store_reverification(expected_cells),
        "rows": rows,
    })


def test_v9_asymmetric_fixture_pins_median_aggregation():
    observations = _asymmetric_observations()

    result = _judge(observations)
    holdout = result["holdouts"]["rr80"]

    # median 集約の数値を明示 assert する。対称 fixture では mean 置換でも通る
    # false-green を親が in-process 変異で再現済み (C-A #3)。
    assert holdout["configurations"]["c-low"]["trial_medians"] == [10.0, 10.0, 10.0]
    assert holdout["configurations"]["c-low"]["median_of_medians"] == 10.0
    assert holdout["configurations"]["c-high"]["median_of_medians"] == 15.0
    assert holdout["verdict"] == "unique-best"
    assert holdout["winner_configuration_id"] == "c-high"


def test_v9_median_to_mean_mutation_flips_winner(monkeypatch):
    observations = _asymmetric_observations()
    baseline = _judge(observations)

    # statistics.median を mean へ差し替えると集約が変わり winner が反転する。
    # この差が出ることが、上の数値 assert が median 依存 (恒真でない) である証拠。
    monkeypatch.setattr(judge.statistics, "median", judge.statistics.mean)
    mutated = _judge(observations)
    mutated_holdout = mutated["holdouts"]["rr80"]

    assert mutated_holdout["configurations"]["c-low"]["median_of_medians"] == 20.0
    assert mutated_holdout["winner_configuration_id"] == "c-low"
    assert mutated != baseline


def test_judge_rejects_valid_raw_and_exploration_observation_types():
    official = _observations()
    for untyped in (dict(official), artifacts.ExplorationArtifact(official)):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
            _judge(untyped)


def test_manifest_and_spec_binding_match_then_one_field_mismatch_is_indeterminate():
    observations = _observations()

    accepted = _judge(observations)
    assert accepted["status"] == "determinate"
    assert accepted["reasons"] == []

    observations["spec_sha256"] = "c" * 64
    rejected = _judge(observations)
    assert rejected["status"] == "indeterminate"
    assert [reason["code"] for reason in rejected["reasons"]] == ["spec-sha256"]


def test_observations_schedule_body_must_match_verified_manifest_projection():
    observations = _observations(n=2)
    projection = judge.ManifestScheduleProjection(
        n_per_cell=2,
        expected_cells=frozenset(
            (
                entry["schedule_index"],
                entry["holdout_id"],
                entry["configuration_id"],
            )
            for entry in observations["expected_cells"]
        ),
        expected_campaign_ids=frozenset({CAMPAIGN_ID}),
    )
    baseline = _judge(observations, schedule_projection=projection)
    assert baseline["status"] == "determinate"
    assert baseline["reasons"] == []

    changed = copy.deepcopy(observations)
    changed["n_per_cell"] = 1
    changed["rows"] = [
        row for row in changed["rows"]
        if row["schedule_index"] % 2 == 0
    ]
    for schedule_index, row in enumerate(changed["rows"]):
        row["schedule_index"] = schedule_index
    changed["expected_cells"] = [
        {
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        }
        for row in changed["rows"]
    ]

    rejected = _judge(changed, schedule_projection=projection)
    assert rejected["status"] == "indeterminate"
    assert {
        reason["code"] for reason in rejected["reasons"]
    } >= {"n-per-cell-mismatch", "expected-cells-mismatch"}


def test_judge_binding_keywords_are_required_without_defaults():
    signature = inspect.signature(judge.judge_oracle)
    assert signature.parameters["schedule_projection"].default is inspect.Parameter.empty
    assert signature.parameters["verified_manifest_sha256"].default is inspect.Parameter.empty
    assert signature.parameters["approved_spec_sha256"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        judge.judge_oracle(_observations())


def _cli_observations(document, approved_sha256):
    campaign_id = next(iter(document["campaign_ids"].values()))
    if isinstance(campaign_id, dict):
        campaign_id = campaign_id["campaign_id"]
    rows = []
    for schedule_row in document["schedule"]["rows"]:
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
            "bench_values": [1.0],
            "excluded_reason": None,
            "screen_outcome": "not_enabled",
            "reason": None,
        })
    expected_cells = [{
        "schedule_index": row["schedule_index"],
        "holdout_id": row["holdout_id"],
        "configuration_id": row["configuration_id"],
    } for row in rows]
    return {
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": oracle_manifest._canonical_sha256(document),
        "spec_sha256": approved_sha256,
        "n_per_cell": document["schedule"]["n"],
        "campaign_verifier_epochs": [{
            **_e1_evidence()[0], "campaign_id": campaign_id,
        }],
        "expected_cells": expected_cells,
        "store_reverification": _store_reverification(expected_cells),
        "rows": rows,
    }


def _real_g1_judge_cli_fixture(tmp_path):
    root, manifest_path, document, approved = (
        report_fixtures._ratified_cli_manifest(tmp_path)
    )
    source = tmp_path / "observations.real-g1.json"
    source.write_text(
        json.dumps(_cli_observations(document, approved.sha256)),
        encoding="utf-8",
    )
    return root, manifest_path, source, approved


def _install_scan_neutral_earlier_result(root):
    loaded = judge.s8b_ratified_freeze.load_ratified_freeze(root)
    selected_rel = loaded.document["floor_source"]["path"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    earlier_run_id = f"20260718T115959Z-{proto8}"
    earlier_rel = selected_rel.replace(selected_run_id, earlier_run_id)
    assert earlier_rel != selected_rel
    earlier_path = root / earlier_rel
    earlier_path.parent.mkdir(parents=True, exist_ok=True)
    earlier_path.write_bytes(b"{}")
    ratified_fixture._commit_exact(
        root,
        [earlier_rel],
        subject="scan-neutral earlier official result",
        agent="fixture",
    )
    return earlier_rel


def test_judge_cli_real_g1_rule_mismatch_preserves_selection_reason(
        tmp_path, monkeypatch, capsys):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_cli_real_g1_rule_mismatch_preserves_selection_reason"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_cli_real_g1_rule_mismatch_preserves_selection_reason(tmp_path, monkeypatch):
    import contextlib
    import io
    from types import SimpleNamespace

    captured_stderr = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr):
        root, manifest_path, source, approved = _real_g1_judge_cli_fixture(tmp_path)
        earlier_rel = _install_scan_neutral_earlier_result(root)
        eligibility_calls = []

        def derive_eligibility(**kwargs):
            eligibility_calls.append(kwargs["result_rel"])
            return kwargs["result_rel"] == earlier_rel

        monkeypatch.setattr(
            holdout_freeze,
            "_derive_floor_selection_eligibility",
            derive_eligibility,
        )
        monkeypatch.setattr(oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256)
        output = tmp_path / "selection-mismatch-must-not-exist.json"

        rc = judge.main([
            "judge", "--input", str(source),
            "--manifest", str(manifest_path), "--out", str(output),
            "--repo-root", str(root),
        ])

        stderr = captured_stderr.getvalue()
        assert rc == 2
        assert "floor-selection-rule-mismatch" in stderr
        assert "earliest-eligible-official-run-id/v1" in stderr
        assert eligibility_calls == [earlier_rel]
        assert not output.exists()


def test_judge_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate(tmp_path):
    root, manifest_path, source, approved = _real_g1_judge_cli_fixture(tmp_path)
    output = tmp_path / "valid-real-g1-verdict.json"
    real_selection = (
        judge.s8b_ratified_freeze.assert_g1_floor_selection_identity
    )
    real_reverify = judge.s8b_ratified_freeze.reverify_published_freeze
    ordered_calls = mock.Mock()

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256,
    ), mock.patch.object(
            judge.s8b_ratified_freeze,
            "assert_g1_floor_selection_identity",
            wraps=real_selection,
    ) as selection_spy, mock.patch.object(
            judge.s8b_ratified_freeze,
            "reverify_published_freeze",
            wraps=real_reverify,
    ) as reverify_spy:
        ordered_calls.attach_mock(selection_spy, "selection")
        ordered_calls.attach_mock(reverify_spy, "reverify")
        rc = judge.main([
            "judge", "--input", str(source),
            "--manifest", str(manifest_path), "--out", str(output),
            "--repo-root", str(root),
        ])

    assert rc == 0
    assert output.exists()
    assert selection_spy.call_count == 1
    assert reverify_spy.call_count == 1
    assert [call[0] for call in ordered_calls.mock_calls[:2]] == [
        "selection", "reverify",
    ]


def test_judge_cli_selection_gate_receives_loaded_ratified_and_root(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_cli_selection_gate_receives_loaded_ratified_and_root"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_cli_selection_gate_receives_loaded_ratified_and_root(tmp_path):
    root, manifest_path, source, approved = _real_g1_judge_cli_fixture(tmp_path)
    output = tmp_path / "selection-arguments-verdict.json"
    real_load = judge.s8b_ratified_freeze.load_ratified_freeze
    real_selection = (
        judge.s8b_ratified_freeze.assert_g1_floor_selection_identity
    )
    loaded = []
    selection_calls = []

    def load_recording_wrapper(candidate_root):
        loaded_ratified = real_load(candidate_root)
        loaded.append(loaded_ratified)
        return loaded_ratified

    def selection_recording_wrapper(candidate, candidate_root):
        selection_calls.append((candidate, candidate_root))
        return real_selection(candidate, candidate_root)

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256,
    ), mock.patch.object(
            judge.s8b_ratified_freeze,
            "load_ratified_freeze",
            side_effect=load_recording_wrapper,
    ), mock.patch.object(
            judge.s8b_ratified_freeze,
            "assert_g1_floor_selection_identity",
            side_effect=selection_recording_wrapper,
    ):
        rc = judge.main([
            "judge", "--input", str(source),
            "--manifest", str(manifest_path), "--out", str(output),
            "--repo-root", str(root),
        ])

    assert rc == 0
    assert output.exists()
    assert len(loaded) == 1
    loaded_ratified = loaded[0]
    assert selection_calls == [(loaded_ratified, root)]
    assert selection_calls[0][0] is loaded_ratified
    assert type(selection_calls[0][1]) is type(root)
    assert selection_calls[0][1] == root


@pytest.mark.parametrize("schema", [
    None,
    "unknown/v1",
    artifacts.OFFICIAL_VERDICT_SCHEMA,
    artifacts.EXPLORATION_ARTIFACT_SCHEMA,
])
def test_judge_cli_rejects_non_observations_schema_without_output(tmp_path, schema):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_cli_rejects_non_observations_schema_without_output"
    result = _run_sealed_case(
        __name__, case, tmp_path, schema=schema,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_cli_rejects_non_observations_schema_without_output(tmp_path, schema):
    root, manifest_path, document, approved = (
        report_fixtures._ratified_cli_manifest(tmp_path)
    )
    valid_source = tmp_path / "observations.valid.json"
    valid_source.write_text(
        json.dumps(_cli_observations(document, approved.sha256)),
        encoding="utf-8",
    )
    positive_output = tmp_path / "positive-verdict.json"
    source = tmp_path / "observations.invalid.json"
    source.write_text(json.dumps({"schema_version": schema}), encoding="utf-8")
    output = tmp_path / "must-not-exist.json"

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        positive_rc = judge.main([
            "judge", "--input", str(valid_source),
            "--manifest", str(manifest_path), "--out", str(positive_output),
            "--repo-root", str(root),
        ])
        rc = judge.main([
            "judge", "--input", str(source),
            "--manifest", str(manifest_path), "--out", str(output),
            "--repo-root", str(root),
        ])

    assert positive_rc == 0
    assert positive_output.exists()
    assert rc == 2
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


def _condition(campaign_id: str, observation: dict | None) -> dict:
    return {
        "campaign_id": campaign_id,
        "measurement_manifest_sha256": ("c" * 64 if observation is not None else None),
        "perf_observation": observation,
    }


def test_mixed_perf_conditions_are_indeterminate_before_cell_aggregation():
    observations = _observations()
    second_campaign = "oracle-b1"
    observations["campaign_verifier_epochs"].append({
        **_e1_evidence()[0],
        "campaign_id": second_campaign,
    })
    for row in observations["rows"][1::2]:
        row["campaign_id"] = second_campaign
    observations["measurement_conditions"] = [
        _condition(CAMPAIGN_ID, _degraded_observation()),
        _condition(second_campaign, None),
    ]
    projection = judge.ManifestScheduleProjection(
        n_per_cell=observations["n_per_cell"],
        expected_cells=frozenset(
            (entry["schedule_index"], entry["holdout_id"], entry["configuration_id"])
            for entry in observations["expected_cells"]
        ),
        expected_campaign_ids=frozenset({CAMPAIGN_ID, second_campaign}),
    )

    result = _judge(observations, schedule_projection=projection)

    assert result["status"] == "indeterminate"
    assert [reason["code"] for reason in result["reasons"]] == [
        "measurement-conditions-mixed",
    ]
    assert all(
        cell["median_of_medians"] is None
        for cell in _holdout(result)["configurations"].values()
    )


def test_all_degraded_claim_gate_precedes_configuration_median(monkeypatch):
    observations = _observations()
    observations["measurement_conditions"] = [
        _condition(CAMPAIGN_ID, _degraded_observation()),
    ]
    calls = []
    monkeypatch.setattr(
        judge._perf_preflight,
        "perf_claim_allowed",
        lambda *args, **kwargs: calls.append((args, kwargs)) or False,
    )

    result = _judge(observations)

    assert calls
    assert result["status"] == "indeterminate"
    assert [reason["code"] for reason in result["reasons"]] == [
        "measurement-condition-claim",
    ]
    assert all(
        cell["trial_medians"] == []
        for cell in _holdout(result)["configurations"].values()
    )


def test_all_degraded_conditions_propagate_to_oracle_verdict():
    observations = _observations()
    conditions = [_condition(CAMPAIGN_ID, _degraded_observation())]
    observations["measurement_conditions"] = conditions

    result = _judge(observations)

    assert result["status"] == "determinate"
    assert result["measurement_conditions"] == conditions


def test_all_perf_oracle_verdict_preserves_exact_keys():
    result = _judge(_observations())

    assert set(result) == {
        "schema_version", "manifest_sha256", "n_per_cell", "status",
        "reasons", "holdouts",
    }
