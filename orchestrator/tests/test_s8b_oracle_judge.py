# -*- coding: utf-8 -*-
"""8b oracle judge の三値・argmax・入力順独立性を検査する。"""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCH.parent))

from orchestrator.campaign import s8b_oracle_judge as judge  # noqa: E402
from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402


# 注意: holdout の三軸 conjunction は JSON 形の静止リテラルにしない。
# judge fixture は workload 値を持たず、opaque な holdout_id だけを使う。
CONFIGURATIONS = tuple(f"c{i}" for i in range(6))


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
        "manifest_sha256": "manifest-sha",
        "n_per_cell": n,
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
        "rows": rows,
    })


def _holdout(verdict: dict) -> dict:
    return verdict["holdouts"]["rr80"]


def test_complete_data_has_unique_best():
    result = judge.judge_oracle(_observations())

    assert type(result) is artifacts.OfficialVerdict
    assert _holdout(result)["verdict"] == "unique-best"
    assert _holdout(result)["winner_configuration_id"] == CONFIGURATIONS[-1]
    assert result["status"] == "determinate"


def test_exact_maximum_tie_is_not_broken_by_a_floor():
    observations = _observations()
    for row in observations["rows"]:
        if row["configuration_id"] == CONFIGURATIONS[-2]:
            offset = float(row["schedule_index"] % 2)
            row["bench_values"] = [
                50.0 + offset, 51.0 + offset, 52.0 + offset,
                53.0 + offset, 54.0 + offset,
            ]

    result = judge.judge_oracle(observations)

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

    result = judge.judge_oracle(observations)

    assert _holdout(result)["verdict"] == "indeterminate"
    assert any(cell["status"] == "unknown"
               for cell in _holdout(result)["configurations"].values())


def test_huge_integer_bench_value_is_indeterminate():
    observations = _observations()
    observations["rows"][0]["bench_values"] = [10**400]

    result = judge.judge_oracle(observations)
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

    result = judge.judge_oracle(observations)
    holdout = _holdout(result)

    assert holdout["configurations"][red_config]["status"] == "disqualified"
    assert holdout["configurations"][red_config]["median_of_medians"] is None
    assert holdout["verdict"] == "unique-best"
    assert holdout["winner_configuration_id"] == CONFIGURATIONS[-2]


def test_non_string_excluded_reason_is_unknown():
    observations = _observations()
    observations["rows"][0]["excluded_reason"] = 123

    result = judge.judge_oracle(observations)
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

    result = judge.judge_oracle(observations)
    cell = _holdout(result)["configurations"][target]

    assert cell["status"] == "unknown"
    assert any(reason["code"] == "red-excluded" for reason in cell["reasons"])
    assert result["status"] == "indeterminate"


def test_committed_row_with_excluded_reason_is_not_eligible():
    observations = _observations()
    observations["rows"][0]["excluded_reason"] = "machine-fault"

    result = judge.judge_oracle(observations)
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

    result = judge.judge_oracle(observations)
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

    result = judge.judge_oracle(observations)
    cell = _holdout(result)["configurations"][target]

    assert cell["status"] == "unknown"
    assert result["status"] == "indeterminate"
    assert any(reason["code"] == "binary-mismatch" for reason in cell["reasons"])


def test_row_shuffle_does_not_change_verdict_json():
    observations = _observations()
    expected = judge.judge_oracle(observations)
    shuffled = copy.deepcopy(observations)
    random.Random(827).shuffle(shuffled["rows"])

    assert judge.judge_oracle(shuffled) == expected


def test_deleting_every_row_for_one_expected_holdout_is_indeterminate():
    observations = _observations(holdouts=("rr80", "h-second"))
    assert judge.judge_oracle(observations)["status"] == "determinate"
    observations["rows"] = [
        row for row in observations["rows"] if row["holdout_id"] != "h-second"
    ]

    result = judge.judge_oracle(observations)

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
        "manifest_sha256": "manifest-sha",
        "n_per_cell": 3,
        "expected_cells": [{
            "schedule_index": row["schedule_index"],
            "holdout_id": row["holdout_id"],
            "configuration_id": row["configuration_id"],
        } for row in rows],
        "rows": rows,
    })


def test_v9_asymmetric_fixture_pins_median_aggregation():
    observations = _asymmetric_observations()

    result = judge.judge_oracle(observations)
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
    baseline = judge.judge_oracle(observations)

    # statistics.median を mean へ差し替えると集約が変わり winner が反転する。
    # この差が出ることが、上の数値 assert が median 依存 (恒真でない) である証拠。
    monkeypatch.setattr(judge.statistics, "median", judge.statistics.mean)
    mutated = judge.judge_oracle(observations)
    mutated_holdout = mutated["holdouts"]["rr80"]

    assert mutated_holdout["configurations"]["c-low"]["median_of_medians"] == 20.0
    assert mutated_holdout["winner_configuration_id"] == "c-low"
    assert mutated != baseline


def test_judge_rejects_valid_raw_and_exploration_observation_types():
    official = _observations()
    for untyped in (dict(official), artifacts.ExplorationArtifact(official)):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
            judge.judge_oracle(untyped)


@pytest.mark.parametrize("schema", [
    None,
    "unknown/v1",
    artifacts.OFFICIAL_VERDICT_SCHEMA,
    artifacts.EXPLORATION_ARTIFACT_SCHEMA,
])
def test_judge_cli_rejects_non_observations_schema_without_output(tmp_path, schema):
    source = tmp_path / "observations.invalid.json"
    source.write_text(json.dumps({"schema_version": schema}), encoding="utf-8")
    output = tmp_path / "must-not-exist.json"

    rc = judge.main(["judge", "--input", str(source), "--out", str(output)])

    assert rc == 2
    assert not output.exists()
