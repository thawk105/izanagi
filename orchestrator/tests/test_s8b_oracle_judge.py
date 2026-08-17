# -*- coding: utf-8 -*-
"""8b oracle judge の三値・argmax・入力順独立性を検査する。"""
from __future__ import annotations

import copy
import inspect
import json
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
from orchestrator.campaign import s8b_oracle_manifest as oracle_manifest  # noqa: E402
from orchestrator.campaign import s8b_oracle_spec as oracle_spec  # noqa: E402
from orchestrator.calibrator import perf_preflight  # noqa: E402
import test_s8b_oracle_report as report_fixtures  # noqa: E402


# 注意: holdout の三軸 conjunction は JSON 形の静止リテラルにしない。
# judge fixture は workload 値を持たず、opaque な holdout_id だけを使う。
CONFIGURATIONS = tuple(f"c{i}" for i in range(6))
MANIFEST_SHA256 = "a" * 64
SPEC_SHA256 = "b" * 64
CAMPAIGN_ID = "oracle-b0"


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
    return artifacts.OfficialObservations({
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": MANIFEST_SHA256,
        "spec_sha256": SPEC_SHA256,
        "n_per_cell": n,
        "campaign_verifier_epochs": _e1_evidence(),
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
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
    return artifacts.OfficialObservations({
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": MANIFEST_SHA256,
        "spec_sha256": SPEC_SHA256,
        "n_per_cell": 3,
        "campaign_verifier_epochs": _e1_evidence(),
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
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
    return {
        "schema_version": judge.INPUT_SCHEMA,
        "manifest_kind": "official",
        "manifest_sha256": oracle_manifest._canonical_sha256(document),
        "spec_sha256": approved_sha256,
        "n_per_cell": document["schedule"]["n"],
        "campaign_verifier_epochs": [{
            **_e1_evidence()[0], "campaign_id": campaign_id,
        }],
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
        "rows": rows,
    }


@pytest.mark.parametrize("schema", [
    None,
    "unknown/v1",
    artifacts.OFFICIAL_VERDICT_SCHEMA,
    artifacts.EXPLORATION_ARTIFACT_SCHEMA,
])
def test_judge_cli_rejects_non_observations_schema_without_output(tmp_path, schema):
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
