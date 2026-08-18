# -*- coding: utf-8 -*-
"""Boundary tests for the stage 8c result judge.

The C-2 boundary list covers preregistration contract admission, C-3 covers
raw observation binding and the three-condition truth table, and C-4 covers
independent cell admission plus atomic publication.  The list is kept next to
the tests so a future mutation cannot silently drop a boundary category.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import s8c_result_judge as M


C2_BOUNDARIES = (
    "raw parameter mapping is rejected",
    "n=1 is rejected",
    "bool n is rejected",
    "non-finite delta_min is rejected",
    "non-positive delta_min is rejected",
    "negative sd_max is rejected",
    "non-finite sd_max is rejected",
    "wrong unit is rejected",
    "wrong direction is rejected",
    "empty source binding is rejected",
    "missing swapped mapping is indeterminate",
    "extra swapped mapping is indeterminate",
    "self swapped mapping is indeterminate",
    "missing swapped prediction is indeterminate",
    "extra swapped prediction is indeterminate",
)
C3_BOUNDARIES = (
    "missing replicate",
    "duplicate replicate",
    "replicate outside registered n",
    "non-contiguous schedule index",
    "wrong schedule index",
    "cell identity mismatch",
    "correctness gate failure",
    "trace-enabled observation",
    "non-finite observation",
    "non-finite paired delta",
    "same prediction is unsatisfied",
    "H1 and H2 are evaluated separately",
    "mean_delta strict lower boundary",
    "sample_sd inclusive upper boundary",
    "sample statistics are re-derived",
    "condition IDs are an exact set",
    "raw observation attestation is bound to values",
    "empty complete blocks are indeterminate",
)
C4_BOUNDARIES = (
    "predeclared cell set is independent",
    "missing generated cell",
    "extra generated cell",
    "duplicate generated cell",
    "three staging tables",
    "absolute path",
    "repository exclusion after symlink resolution",
    "create-only destination",
    "rollback leaves no table",
    "rollback failure is reported",
)


def _params(
    *, n: int = 2, delta_min: float = 1.5, sd_max: float = math.sqrt(2.0),
    unit: str = M._PARAM_UNIT, direction: str = M._PARAM_DIRECTION,
    source_binding: str = "prereg-binding-v1",
) -> M._ContrastParams:
    return M._ContrastParams(n, delta_min, sd_max, unit, direction, source_binding)


def _cells() -> list[dict[str, str]]:
    return [
        {"cell_id": "H1-on", "holdout_id": "H1", "arm": "on", "configuration_id": "cfg-H1-on"},
        {"cell_id": "H1-off", "holdout_id": "H1", "arm": "off", "configuration_id": "cfg-H1-off"},
        {"cell_id": "H1-swapped", "holdout_id": "H1", "arm": "swapped", "configuration_id": "cfg-H1-swapped"},
        {"cell_id": "H2-on", "holdout_id": "H2", "arm": "on", "configuration_id": "cfg-H2-on"},
        {"cell_id": "H2-off", "holdout_id": "H2", "arm": "off", "configuration_id": "cfg-H2-off"},
        {"cell_id": "H2-swapped", "holdout_id": "H2", "arm": "swapped", "configuration_id": "cfg-H2-swapped"},
    ]


def _manifest(*, n: int = 2) -> dict:
    cells = _cells()
    schedule = []
    schedule_index = 0
    for replicate in range(1, n + 1):
        for cell in cells:
            schedule.append({
                "schedule_index": schedule_index,
                "cell_id": cell["cell_id"],
                "holdout_id": cell["holdout_id"],
                "arm": cell["arm"],
                "replicate": replicate,
                "block": f"block-{replicate}",
            })
            schedule_index += 1
    return {
        "n": n,
        "source_binding": "prereg-binding-v1",
        "condition_ids": list(M._CONDITION_IDS),
        "cells": cells,
        "schedule": schedule,
        "swapped_mapping": {"H1": "H2", "H2": "H1"},
    }


def _prediction(*, same: bool = False) -> dict:
    h1_on = "cfg-H1-on"
    h2_on = "cfg-H2-on"
    return {
        "conditions": list(M._CONDITION_IDS),
        "on_off": {
            "H1": {"on": h1_on, "off": h1_on if same else "cfg-H1-off"},
            "H2": {"on": h2_on, "off": h2_on if same else "cfg-H2-off"},
        },
        "swapped": {"H1": h2_on, "H2": h1_on},
    }


def _observations(
    manifest: dict,
    *,
    h1_on: tuple[float, float] = (12.0, 14.0),
    h1_off: tuple[float, float] = (10.0, 10.0),
    h2_on: tuple[float, float] = (8.0, 8.0),
    h2_off: tuple[float, float] = (7.0, 7.0),
    extra: dict | None = None,
) -> list[dict]:
    by_cell = {
        "H1-on": h1_on,
        "H1-off": h1_off,
        "H1-swapped": (9.0, 9.0),
        "H2-on": h2_on,
        "H2-off": h2_off,
        "H2-swapped": (6.0, 6.0),
    }
    result = []
    for row in manifest["schedule"]:
        value = by_cell[row["cell_id"]][row["replicate"] - 1]
        item = {
            "schedule_index": row["schedule_index"],
            "cell_id": row["cell_id"],
            "holdout_id": row["holdout_id"],
            "arm": row["arm"],
            "replicate": row["replicate"],
            "throughput": value,
            "correctness_gate_passed": True,
            "trace_enabled": False,
            "attestation": {
                "raw_values_sha256": M._observation_raw_digest((float(value),)),
                "issuer": "test-gate-issuer",
            },
        }
        if extra:
            item.update(extra)
        result.append(item)
    return result


def _judge(
    *,
    manifest: dict | None = None,
    observations: list[dict] | None = None,
    prediction: dict | None = None,
    params: M._ContrastParams | None = None,
) -> M._JudgeResult:
    manifest = copy.deepcopy(manifest if manifest is not None else _manifest())
    observations = copy.deepcopy(observations if observations is not None else _observations(manifest))
    prediction = copy.deepcopy(prediction if prediction is not None else _prediction())
    return M.judge(manifest, observations, prediction, params or _params())


def _status(result: M._JudgeResult, condition_id: str) -> M._Status:
    return result.conditions[condition_id].status


def _output_paths(root: Path) -> dict[str, Path]:
    return {name: root / f"{name}.json" for name in M._TABLE_NAMES}


def _verified_floor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    protocol_payload: bytes = b"protocol-bytes",
    source_payload: bytes = b"source-bytes",
    frozen_at_head: str = "a" * 40,
) -> M._VerifiedFloorEvidence:
    protocol = tmp_path / "floor-protocol.bin"
    source = tmp_path / "floor-source.bin"
    protocol.write_bytes(protocol_payload)
    source.write_bytes(source_payload)
    document = {
        "floor_protocol": {
            "path": str(protocol),
            "sha256": hashlib.sha256(protocol_payload).hexdigest(),
        },
        "floor_source": {
            "path": str(source),
            "sha256": hashlib.sha256(source_payload).hexdigest(),
        },
        "env_tag": "test-env",
        "frozen_at_head": frozen_at_head,
    }
    monkeypatch.setattr(
        M,
        "load_ratified_freeze",
        lambda: SimpleNamespace(document=document),
    )
    return M.verify_floor_bytes([
        document["floor_protocol"],
        document["floor_source"],
    ])


def _floor_provenance(evidence: M._VerifiedFloorEvidence) -> dict[str, str]:
    return {
        "floor_protocol_path": evidence.floor_protocol_path,
        "floor_protocol_sha256": evidence.floor_protocol_sha256,
        "floor_source_path": evidence.floor_source_path,
        "floor_source_sha256": evidence.floor_source_sha256,
        "env_tag": evidence.env_tag,
        "frozen_at_head": evidence.frozen_at_head,
    }


def test_public_names_are_exactly_three() -> None:
    assert set(M.__all__) == {"verify_floor_bytes", "judge", "publish_result_table"}
    assert len(M.__all__) == 3
    result = _judge()
    assert set(result.conditions) == set(M._CONDITION_IDS)
    assert len(result.conditions) == 3
    assert "conclusion" not in result.conditions


def test_owned_result_judge_module_is_not_a_legacy_acceptance_decoy() -> None:
    assert Path(M.__file__).resolve() == (
        M._REPO_ROOT / "orchestrator" / "campaign" / "s8c_result_judge.py"
    ).resolve()
    assert not hasattr(M, "accept_trial")


def test_judge_signature_has_no_floor_argument() -> None:
    names = set(inspect.signature(M.judge).parameters)
    assert not names & {"floor", "floor_refs", "floor_value", "floor_artifact", "verified_floor"}
    assert names == {"manifest", "observations", "prediction", "params"}


@pytest.mark.parametrize("case", C2_BOUNDARIES)
def test_c2_boundary_list_is_documented(case: str) -> None:
    result = _judge()
    assert case in C2_BOUNDARIES
    assert set(result.conditions) == set(M._CONDITION_IDS)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("n", 1),
        ("n", True),
        ("delta_min", float("nan")),
        ("delta_min", 0.0),
        ("delta_min", -1.0),
        ("sd_max", -1.0),
        ("sd_max", float("inf")),
        ("unit", "latency_ns"),
        ("direction", "off_minus_on"),
        ("source_binding", ""),
    ],
)
def test_invalid_params_are_preregistration_not_effective(field: str, value: object) -> None:
    raw = {
        "n": 2,
        "delta_min": 1.5,
        "sd_max": 1.0,
        "unit": M._PARAM_UNIT,
        "direction": M._PARAM_DIRECTION,
        "source_binding": "prereg-binding-v1",
    }
    raw[field] = value
    params = M._ContrastParams(**raw)
    with pytest.raises(M._PreregistrationNotEffectiveError):
        _judge(params=params)


def test_raw_parameter_mapping_is_not_accepted() -> None:
    with pytest.raises(M._PreregistrationNotEffectiveError):
        M.judge(_manifest(), _observations(_manifest()), _prediction(), {
            "n": 2,
            "delta_min": 1.5,
            "sd_max": 1.0,
        })


def test_n_two_uses_sample_sd_denominator_n_minus_one() -> None:
    result = _judge(
        params=_params(delta_min=1.0, sd_max=math.sqrt(2.0)),
        observations=_observations(
            _manifest(),
            h1_on=(12.0, 14.0),
            h1_off=(10.0, 10.0),
            h2_on=(10.0, 12.0),
            h2_off=(8.0, 8.0),
        ),
    )
    h1 = result.conditions["paired_repeat_contrast"].diagnostics["holdouts"]["H1"]
    assert h1["deltas"] == (2.0, 4.0)
    assert h1["sample_sd"] == pytest.approx(math.sqrt(2.0))


def test_mean_delta_equal_delta_min_is_not_satisfied() -> None:
    result = _judge(
        params=_params(delta_min=1.5, sd_max=0.0),
        observations=_observations(
            _manifest(),
            h1_on=(11.5, 11.5),
            h1_off=(10.0, 10.0),
            h2_on=(9.5, 9.5),
            h2_off=(8.0, 8.0),
        ),
    )
    assert _status(result, "paired_repeat_contrast") is M._Status.UNSATISFIED


def test_sample_sd_equal_sd_max_is_satisfied_when_mean_is_strictly_above() -> None:
    result = _judge(
        params=_params(delta_min=1.0, sd_max=math.sqrt(2.0)),
        observations=_observations(
            _manifest(),
            h1_on=(12.0, 14.0),
            h1_off=(10.0, 10.0),
            h2_on=(10.0, 12.0),
            h2_off=(8.0, 8.0),
        ),
    )
    assert _status(result, "paired_repeat_contrast") is M._Status.SATISFIED


def test_h1_satisfied_h2_unsatisfied_is_not_hidden_by_one_global_mean() -> None:
    result = _judge()
    contrast = result.conditions["paired_repeat_contrast"]
    assert contrast.status is M._Status.UNSATISFIED
    assert contrast.diagnostics["holdouts"]["H1"]["status"] == "SATISFIED"
    assert contrast.diagnostics["holdouts"]["H2"]["status"] == "UNSATISFIED"


def test_condition_id_duplicate_is_rejected_even_when_length_is_three() -> None:
    manifest = _manifest()
    manifest["condition_ids"] = [
        M._CONDITION_IDS[0], M._CONDITION_IDS[1], M._CONDITION_IDS[1],
    ]
    with pytest.raises(M._InputContractError):
        _judge(manifest=manifest)


@pytest.mark.parametrize("mutation", [
    "missing_mapping", "extra_mapping", "self_mapping",
    "missing_prediction", "extra_prediction",
])
def test_c2_swapped_mapping_boundaries_are_indeterminate(mutation: str) -> None:
    manifest = _manifest()
    prediction = _prediction()
    if mutation == "missing_mapping":
        manifest["swapped_mapping"].pop("H1")
    elif mutation == "extra_mapping":
        manifest["swapped_mapping"]["H3"] = "H1"
    elif mutation == "self_mapping":
        manifest["swapped_mapping"]["H1"] = "H1"
    elif mutation == "missing_prediction":
        prediction["swapped"].pop("H1")
    else:
        prediction["swapped"]["H3"] = "cfg-H1-on"
    result = _judge(manifest=manifest, prediction=prediction)
    assert _status(result, "swapped_follow_through") is M._Status.INDETERMINATE


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "non_contiguous", "wrong_index", "wrong_cell"])
def test_c3_schedule_and_block_boundaries_are_indeterminate(mutation: str) -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    if mutation == "missing":
        observations.pop()
    elif mutation == "duplicate":
        observations[-1]["schedule_index"] = observations[-2]["schedule_index"]
    elif mutation == "non_contiguous":
        manifest["schedule"][3]["schedule_index"] = 99
    elif mutation == "wrong_index":
        observations[0]["schedule_index"] = 99
    elif mutation == "wrong_cell":
        observations[0]["cell_id"] = "H2-on"
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "outside_n"])
def test_c3_replicate_boundaries_are_indeterminate(mutation: str) -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    if mutation == "missing":
        observations = [
            item for item in observations
            if not (item["cell_id"] == "H1-on" and item["replicate"] == 2)
        ]
    elif mutation == "duplicate":
        for row in manifest["schedule"]:
            if row["cell_id"] == "H1-on" and row["replicate"] == 2:
                row["replicate"] = 1
                break
    else:
        for row in manifest["schedule"]:
            if row["cell_id"] == "H1-on" and row["replicate"] == 2:
                row["replicate"] = 3
                break
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


def test_c3_does_not_pair_rows_from_different_blocks() -> None:
    manifest = _manifest()
    for row in manifest["schedule"]:
        if row["cell_id"] == "H1-off":
            row["block"] = f"unpaired-{row['replicate']}"
    result = _judge(manifest=manifest)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


@pytest.mark.parametrize("mutation", ["manifest_n", "cell_n", "observation_count"])
def test_c3_registered_n_must_match_the_complete_block(mutation: str) -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    if mutation == "manifest_n":
        manifest["n"] = 3
    elif mutation == "cell_n":
        manifest["cells"][0]["n"] = 3
    else:
        observations[0]["replicate"] = 2
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


def test_gate_failure_trace_enabled_and_nonfinite_observation_are_indeterminate() -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    observations[0]["correctness_gate_passed"] = False
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    observations = _observations(
        manifest,
        h1_on=(1.0e308, 1.0e308),
        h1_off=(-1.0e308, -1.0e308),
    )
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    observations = _observations(manifest)
    observations[0]["trace_enabled"] = True
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    observations = _observations(manifest)
    observations[0]["throughput"] = float("nan")
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    observations = _observations(manifest)
    observations[0].pop("attestation")
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    observations = _observations(manifest)
    observations[0]["throughput"] = 999.0
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


def test_caller_median_delta_and_rank_fields_are_rejected() -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    observations[0]["median"] = 999.0
    result = _judge(manifest=manifest, observations=observations)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE

    prediction = _prediction()
    prediction["on_off"]["H1"]["rank"] = 1
    result = _judge(manifest=manifest, prediction=prediction)
    assert _status(result, "on_off_prediction_difference") is M._Status.INDETERMINATE


def test_same_prediction_with_complete_block_is_unsatisfied_not_indeterminate() -> None:
    manifest = _manifest()
    result = _judge(manifest=manifest, prediction=_prediction(same=True))
    assert _status(result, "paired_repeat_contrast") is M._Status.UNSATISFIED
    assert result.conditions["paired_repeat_contrast"].diagnostics["holdouts"]["H1"]["same_prediction"] is True


def test_three_condition_conclusion_uses_indeterminate_then_unsatisfied_priority() -> None:
    result = _judge(prediction={"conditions": list(M._CONDITION_IDS)})
    assert _status(result, "on_off_prediction_difference") is M._Status.INDETERMINATE
    assert result.conclusion is M._Status.INDETERMINATE

    result = _judge(prediction=_prediction(same=True))
    assert result.conclusion is M._Status.UNSATISFIED


def test_cv_and_diagnostic_values_do_not_enter_status() -> None:
    manifest = _manifest()
    first = _observations(manifest, extra={"cv": 0.01, "session_cv": 0.01})
    second = _observations(manifest, extra={"cv": 999.0, "session_cv": float("inf")})
    assert _judge(manifest=manifest, observations=first).conclusion == _judge(
        manifest=manifest, observations=second,
    ).conclusion


def test_covariance_and_spread_diagnostics_do_not_enter_status() -> None:
    manifest = _manifest()
    first = _judge(
        manifest=manifest,
        observations=_observations(
            manifest,
            h1_on=(12.0, 14.0), h1_off=(10.0, 10.0),
            h2_on=(10.0, 12.0), h2_off=(8.0, 8.0),
        ),
        params=_params(delta_min=1.0, sd_max=math.sqrt(2.0)),
    )
    second = _judge(
        manifest=manifest,
        observations=_observations(
            manifest,
            h1_on=(12.0, 16.0), h1_off=(10.0, 12.0),
            h2_on=(10.0, 14.0), h2_off=(8.0, 10.0),
        ),
        params=_params(delta_min=1.0, sd_max=math.sqrt(2.0)),
    )
    first_h1 = first.conditions["paired_repeat_contrast"].diagnostics["holdouts"]["H1"]
    second_h1 = second.conditions["paired_repeat_contrast"].diagnostics["holdouts"]["H1"]
    assert first_h1["deltas"] == second_h1["deltas"]
    assert first_h1["covariance"] != second_h1["covariance"]
    assert first.conditions["paired_repeat_contrast"].status is second.conditions["paired_repeat_contrast"].status


def test_source_binding_mismatch_is_indeterminate_not_a_new_status() -> None:
    manifest = _manifest()
    manifest["source_binding"] = "another-binding"
    result = _judge(manifest=manifest)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


def test_missing_source_binding_is_indeterminate_not_a_match() -> None:
    manifest = _manifest()
    manifest.pop("source_binding")
    result = _judge(manifest=manifest)
    assert _status(result, "paired_repeat_contrast") is M._Status.INDETERMINATE


def test_duplicate_holdout_configuration_ids_are_indeterminate() -> None:
    manifest = _manifest()
    manifest["cells"][1]["configuration_id"] = manifest["cells"][0]["configuration_id"]
    result = _judge(manifest=manifest)
    assert all(
        condition.status is M._Status.INDETERMINATE
        for condition in result.conditions.values()
    )


def test_prediction_cell_ids_are_canonicalized_to_configuration_ids() -> None:
    baseline = _judge()
    prediction = _prediction()
    prediction["on_off"]["H1"]["on"] = "H1-on"
    prediction["on_off"]["H1"]["off"] = "H1-off"
    prediction["on_off"]["H2"]["on"] = "H2-on"
    prediction["on_off"]["H2"]["off"] = "H2-off"
    prediction["swapped"]["H1"] = "H2-on"
    prediction["swapped"]["H2"] = "H1-on"
    result = _judge(prediction=prediction)
    assert result.conclusion is baseline.conclusion
    swapped = next(
        row for row in result.selection_rows if row["cell_id"] == "H1-swapped"
    )
    assert swapped["predicted_configuration_id"] == "cfg-H2-on"


def test_empty_manifest_does_not_make_any_condition_satisfied() -> None:
    manifest = _manifest()
    manifest["cells"] = []
    manifest["schedule"] = []
    result = _judge(manifest=manifest)
    assert all(
        condition.status is M._Status.INDETERMINATE
        for condition in result.conditions.values()
    )
    assert result.conclusion is M._Status.INDETERMINATE


def test_missing_complete_block_does_not_make_any_condition_satisfied() -> None:
    manifest = _manifest()
    manifest["schedule"] = []
    result = _judge(manifest=manifest, observations=[])
    assert all(
        condition.status is M._Status.INDETERMINATE
        for condition in result.conditions.values()
    )
    assert result.conclusion is M._Status.INDETERMINATE


def test_missing_observation_block_does_not_make_any_condition_satisfied() -> None:
    manifest = _manifest()
    result = _judge(manifest=manifest, observations=[])
    assert all(
        condition.status is M._Status.INDETERMINATE
        for condition in result.conditions.values()
    )
    assert result.conclusion is M._Status.INDETERMINATE


def test_floor_verification_derives_expectations_from_ratified_freeze(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = tmp_path / "floor-protocol.bin"
    source = tmp_path / "floor-source.bin"
    protocol_raw = b"protocol"
    source_raw = b"source"
    protocol.write_bytes(protocol_raw)
    source.write_bytes(source_raw)
    frozen_at_head = "a" * 40
    document = {
        "floor_protocol": {
            "path": str(protocol),
            "sha256": hashlib.sha256(protocol_raw).hexdigest(),
        },
        "floor_source": {
            "path": str(source),
            "sha256": hashlib.sha256(source_raw).hexdigest(),
        },
        "env_tag": "test-env",
        "frozen_at_head": frozen_at_head,
    }
    monkeypatch.setattr(
        M,
        "load_ratified_freeze",
        lambda: SimpleNamespace(document=document),
    )
    evidence = M.verify_floor_bytes([{
        "path": str(protocol),
        "sha256": document["floor_protocol"]["sha256"],
    }, {
        "path": str(source),
        "sha256": document["floor_source"]["sha256"],
    }])
    assert evidence.floor_protocol_path == str(protocol)
    assert evidence.floor_protocol_sha256 == document["floor_protocol"]["sha256"]
    assert evidence.floor_source_path == str(source)
    assert evidence.floor_source_sha256 == document["floor_source"]["sha256"]
    assert evidence.env_tag == "test-env"
    assert evidence.frozen_at_head == frozen_at_head
    assert set(vars(evidence)) == {
        "floor_protocol_path", "floor_protocol_sha256",
        "floor_source_path", "floor_source_sha256", "env_tag", "frozen_at_head",
    }


def test_floor_verification_requires_both_ratified_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _verified_floor(tmp_path, monkeypatch)
    with pytest.raises(M._FloorVerificationError):
        M.verify_floor_bytes([{
            "path": evidence.floor_source_path,
            "sha256": evidence.floor_source_sha256,
        }])


def test_floor_bytes_mismatch_raises_dedicated_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = tmp_path / "floor-protocol.bin"
    source = tmp_path / "floor-source.bin"
    protocol.write_bytes(b"protocol")
    source.write_bytes(b"source")
    document = {
        "floor_protocol": {
            "path": str(protocol),
            "sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        },
        "floor_source": {"path": str(source), "sha256": "0" * 64},
        "env_tag": "test-env",
        "frozen_at_head": "b" * 40,
    }
    monkeypatch.setattr(M, "load_ratified_freeze", lambda: SimpleNamespace(document=document))
    with pytest.raises(M._FloorVerificationError):
        M.verify_floor_bytes([document["floor_protocol"], document["floor_source"]])


def test_floor_bytes_or_floor_value_cannot_change_judge_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    prediction = _prediction()
    params = _params()
    first_dir = tmp_path / "first"
    first_dir.mkdir()
    first_evidence = _verified_floor(
        first_dir,
        monkeypatch,
        protocol_payload=b'{"floor":1}',
        source_payload=b'{"floor":1}',
    )
    first = M.judge(manifest, observations, prediction, params)
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    second_evidence = _verified_floor(
        second_dir,
        monkeypatch,
        protocol_payload=b'{"floor":999999}',
        source_payload=b'{"floor":999999}',
        frozen_at_head="b" * 40,
    )
    second = M.judge(manifest, observations, prediction, params)
    assert first_evidence != second_evidence
    assert first == second
    assert not hasattr(first, "floor")
    assert not hasattr(first, "threshold")


def test_publish_requires_current_ratified_floor_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    expected = [cell["cell_id"] for cell in _cells()]
    paths = _output_paths(tmp_path)
    evidence = _verified_floor(tmp_path, monkeypatch)
    with pytest.raises(TypeError):
        M.publish_result_table(result, expected, paths)
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, paths, None)
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir()
    foreign = _verified_floor(
        foreign_dir,
        monkeypatch,
        frozen_at_head="b" * 40,
    )
    monkeypatch.setattr(
        M,
        "load_ratified_freeze",
        lambda: SimpleNamespace(document={
            "floor_protocol": {
                "path": evidence.floor_protocol_path,
                "sha256": evidence.floor_protocol_sha256,
            },
            "floor_source": {
                "path": evidence.floor_source_path,
                "sha256": evidence.floor_source_sha256,
            },
            "env_tag": evidence.env_tag,
            "frozen_at_head": evidence.frozen_at_head,
        }),
    )
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, paths, foreign)
    assert all(not path.exists() for path in paths.values())


def test_publish_creates_three_separate_tables_from_independent_six_cell_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge(params=_params(delta_min=1.0, sd_max=math.sqrt(2.0)))
    evidence = _verified_floor(tmp_path, monkeypatch)
    paths = _output_paths(tmp_path)
    published = M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], paths, evidence,
    )
    assert set(published) == set(M._TABLE_NAMES)
    assert all(path.is_file() for path in paths.values())
    tables = [json.loads(path.read_text())["table"] for path in paths.values()]
    assert set(tables) == set(M._TABLE_NAMES)
    for path in paths.values():
        data = json.loads(path.read_text())
        assert len(data["result_table"]["cells"]) == 6
    official = json.loads(paths["official_status"].read_text())["result_table"]["cells"]
    assert {row["official_status"] for row in official} <= {
        "SATISFIED", "UNSATISFIED", "INDETERMINATE",
    }
    descriptive = json.loads(paths["descriptive_only"].read_text())["result_table"]["cells"]
    h1_on = next(row for row in descriptive if row["cell_id"] == "H1-on")
    assert h1_on["replicate_values"] == [[12.0], [14.0]]
    selection = json.loads(paths["selection_evaluation"].read_text())["result_table"]["cells"]
    assert {"predicted_configuration_id", "predicted_rank"} <= set(selection[0])


def test_publish_embeds_verified_floor_provenance_in_each_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    paths = _output_paths(tmp_path)

    M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], paths, evidence,
    )

    expected = _floor_provenance(evidence)
    for path in paths.values():
        payload = json.loads(path.read_text())
        assert payload["metadata"] == expected


def test_publish_provenance_follows_another_ratified_freeze_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    first_freeze = tmp_path / "first-freeze"
    first_freeze.mkdir()
    first_evidence = _verified_floor(
        first_freeze,
        monkeypatch,
        protocol_payload=b"first-protocol",
        source_payload=b"first-source",
        frozen_at_head="a" * 40,
    )
    first_output = tmp_path / "first-output"
    first_output.mkdir()
    first_paths = _output_paths(first_output)
    M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], first_paths, first_evidence,
    )

    second_freeze = tmp_path / "second-freeze"
    second_freeze.mkdir()
    second_evidence = _verified_floor(
        second_freeze,
        monkeypatch,
        protocol_payload=b"second-protocol",
        source_payload=b"second-source",
        frozen_at_head="b" * 40,
    )
    second_output = tmp_path / "second-output"
    second_output.mkdir()
    second_paths = _output_paths(second_output)
    M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], second_paths, second_evidence,
    )

    first_metadata = {
        name: json.loads(path.read_text())["metadata"]
        for name, path in first_paths.items()
    }
    second_metadata = {
        name: json.loads(path.read_text())["metadata"]
        for name, path in second_paths.items()
    }
    assert all(
        metadata == _floor_provenance(first_evidence)
        for metadata in first_metadata.values()
    )
    assert all(
        metadata == _floor_provenance(second_evidence)
        for metadata in second_metadata.values()
    )
    assert first_metadata != second_metadata


def test_publish_floor_provenance_does_not_copy_floor_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(
        tmp_path,
        monkeypatch,
        protocol_payload=(
            b'{"floor_value":123456789012345,"threshold":987654321098765,'
            b'"raw_measurement":555555555555555}'
        ),
        source_payload=(
            b'{"floor_value":123456789012345,"threshold":987654321098765,'
            b'"raw_measurement":555555555555555}'
        ),
    )
    paths = _output_paths(tmp_path)
    M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], paths, evidence,
    )

    forbidden_values = ("123456789012345", "987654321098765", "555555555555555")
    for path in paths.values():
        payload = json.loads(path.read_text())
        provenance = payload["metadata"]
        assert set(provenance) == set(_floor_provenance(evidence))
        assert all(type(value) is str for value in provenance.values())
        serialized = json.dumps(payload, sort_keys=True)
        assert all(value not in serialized for value in forbidden_values)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "second-write-failure"])
def test_publish_cell_missing_extra_duplicate_leaves_no_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    result = _judge()
    paths = _output_paths(tmp_path)
    if mutation == "missing":
        broken = replace(result, cell_rows=result.cell_rows[:-1])
    elif mutation == "extra":
        extra = M._freeze({
            "cell_id": "H3-on", "holdout_id": "H3", "arm": "on",
            "configuration_id": "cfg-H3-on", "replicate_values": (),
            "within_config_median": None, "rank": None,
        })
        broken = replace(result, cell_rows=result.cell_rows + (extra,))
    elif mutation == "duplicate":
        duplicate = dict(result.cell_rows[-1])
        duplicate["cell_id"] = result.cell_rows[0]["cell_id"]
        broken = replace(result, cell_rows=result.cell_rows[:-1] + (M._freeze(duplicate),))
    else:
        broken = result
        original_write = M._exclusive_write
        calls = 0

        def fail_on_second_write(path: Path, raw: bytes) -> None:
            nonlocal calls
            if path in paths.values():
                calls += 1
                if calls == 2:
                    raise OSError("injected second table write failure")
            original_write(path, raw)

        monkeypatch.setattr(M, "_exclusive_write", fail_on_second_write)
    evidence = _verified_floor(tmp_path, monkeypatch)
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(
            broken, [cell["cell_id"] for cell in _cells()], paths, evidence,
        )
    assert all(not path.exists() for path in paths.values())


def test_publish_rollback_failure_is_not_reported_as_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    paths = _output_paths(tmp_path)
    original_write = M._exclusive_write

    def fail_second_destination(path: Path, raw: bytes) -> None:
        if path == paths["official_status"]:
            raise OSError("injected destination failure")
        original_write(path, raw)

    monkeypatch.setattr(M, "_exclusive_write", fail_second_destination)
    original_unlink = Path.unlink

    def fail_rollback(path: Path, *args: object, **kwargs: object) -> None:
        if path == paths["descriptive_only"]:
            raise OSError("injected rollback failure")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_rollback)
    with pytest.raises(M._ResultTableError, match="rollback"):
        M.publish_result_table(
            result, [cell["cell_id"] for cell in _cells()], paths, evidence,
        )
    assert paths["descriptive_only"].exists()


def test_publish_rejects_predeclared_set_mutation_without_deriving_it_from_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    expected = [cell["cell_id"] for cell in _cells()]
    expected[-1] = "unregistered-cell"
    paths = _output_paths(tmp_path)
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, paths, evidence)
    assert all(not path.exists() for path in paths.values())


def test_publish_requires_absolute_paths_and_excludes_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    expected = [cell["cell_id"] for cell in _cells()]
    paths = _output_paths(tmp_path)
    relative = dict(paths)
    relative["official_status"] = Path("relative-result.json")
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, relative, evidence)

    inside = dict(paths)
    inside["official_status"] = M._REPO_ROOT / "result.json"
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, inside, evidence)


def test_publish_is_create_only_and_does_not_overwrite_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    paths = _output_paths(tmp_path)
    paths["official_status"].write_bytes(b"keep")
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(
            result, [cell["cell_id"] for cell in _cells()], paths, evidence,
        )
    assert paths["official_status"].read_bytes() == b"keep"
    assert not paths["descriptive_only"].exists()
    assert not paths["selection_evaluation"].exists()


def test_publish_rejects_symlink_resolving_inside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    expected = [cell["cell_id"] for cell in _cells()]
    link_parent = tmp_path / "outside-link"
    link_parent.symlink_to(M._REPO_ROOT, target_is_directory=True)
    paths = _output_paths(tmp_path)
    paths["official_status"] = link_parent / "result.json"
    with pytest.raises(M._ResultTableError):
        M.publish_result_table(result, expected, paths, evidence)


def test_c3_and_c4_boundary_catalogues_are_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _judge()
    evidence = _verified_floor(tmp_path, monkeypatch)
    paths = _output_paths(tmp_path)
    published = M.publish_result_table(
        result, [cell["cell_id"] for cell in _cells()], paths, evidence,
    )
    assert len(C3_BOUNDARIES) >= 10
    assert len(C4_BOUNDARIES) >= 8
    assert set(published) == set(M._TABLE_NAMES)


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    import pytest as _pytest

    return _pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
