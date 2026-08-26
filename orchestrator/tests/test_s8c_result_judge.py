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
from types import MappingProxyType, SimpleNamespace

import pytest

from orchestrator.campaign import s8c_result_judge as M


_TEST_GENERATION_AXIS = "silo-backoff-trigger-gating"


def _test_canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


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
    "generation marker selects only the generation schema",
    "generation results bind exact cell identities",
    "generation proposal digests are unique across cells",
    "generation proposal bytes and canonical JSON are verified",
    "generation proposal arm binding is verified",
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
    "generation sequence is exact ordered G1 G2",
    "generation final outcome is certified only",
    "generation on off difference requires variant and normal form difference",
    "generation swapped follows exact nonconstant wire normal forms",
    "generation paired same prediction uses variant or normal form identity",
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


def _generation_manifest(*, n: int = 2) -> dict:
    manifest = _manifest(n=n)
    manifest["experiment_kind"] = "generation_search"
    for cell in manifest["cells"]:
        cell.pop("configuration_id")
        cell["workload"] = "rr80" if cell["holdout_id"] == "H1" else "rr20"
    return manifest


def _generation_case(
    tmp_path: Path,
    *,
    wires: dict[str, str] | None = None,
    variants: dict[str, str] | None = None,
) -> tuple[dict, list[dict], dict]:
    manifest = _generation_manifest()
    wire_by_cell = {
        "H1-on": "10000",
        "H1-off": "00100",
        "H1-swapped": "01000",
        "H2-on": "01000",
        "H2-off": "00010",
        "H2-swapped": "10000",
    }
    if wires:
        wire_by_cell.update(wires)
    variant_by_cell = {
        cell["cell_id"]: f"{index + 1:012x}"
        for index, cell in enumerate(manifest["cells"])
    }
    if variants:
        variant_by_cell.update(variants)
    generation_results: dict[str, dict] = {}
    for cell in manifest["cells"]:
        cell_id = cell["cell_id"]
        proposals: dict[int, dict[str, str]] = {}
        for generation_number in (1, 2):
            binding_label = (
                f"binding:{cell_id}:g1"
                if generation_number == 1
                else f"binding:{cell_id}"
            )
            digest = hashlib.sha256(binding_label.encode("ascii")).hexdigest()
            proposal_value = {
                "arm_binding_digest_sha256": digest,
                "coder": {
                    "axis": _TEST_GENERATION_AXIS,
                    "wire": wire_by_cell[cell_id],
                },
            }
            proposal_bytes = _test_canonical_json_bytes(proposal_value)
            proposal_path = tmp_path / f"{cell_id}.g{generation_number}.json"
            proposal_path.write_bytes(proposal_bytes)
            proposals[generation_number] = {
                "path": str(proposal_path),
                "sha256": hashlib.sha256(proposal_bytes).hexdigest(),
                "digest": digest,
            }
        harness = {
            "outcome": "certified",
            "variant": variant_by_cell[cell_id],
        }
        generation_results[cell_id] = {
            "workload": cell["workload"],
            "holdout": cell["holdout_id"],
            "arm": cell["arm"],
            "stop_reason": "fixed-generation-budget",
            "generations": [
                {"generation": 1, "proposal": proposals[1]},
                {
                    "generation": 2,
                    "proposal": proposals[2],
                    "harness": harness,
                    "outcome": "certified",
                },
            ],
        }
    prediction = {
        "experiment_kind": "generation_search",
        "conditions": list(M._CONDITION_IDS),
        "generation_results": generation_results,
    }
    return manifest, _observations(manifest), prediction


def _generation_record(prediction: dict, cell_id: str) -> dict:
    return prediction["generation_results"][cell_id]


def _generation_two(prediction: dict, cell_id: str) -> dict:
    return _generation_by_number(prediction, cell_id, 2)


def _generation_by_number(
    prediction: dict, cell_id: str, generation_number: int,
) -> dict:
    matches = [
        generation
        for generation in _generation_record(prediction, cell_id)["generations"]
        if generation["generation"] == generation_number
    ]
    assert len(matches) == 1
    return matches[0]


def _rewrite_generation_proposal(
    prediction: dict,
    cell_id: str,
    value: object,
    *,
    generation_number: int = 2,
    raw: bytes | None = None,
    update_sha256: bool = True,
) -> None:
    generation = _generation_by_number(prediction, cell_id, generation_number)
    path = Path(generation["proposal"]["path"])
    proposal_bytes = _test_canonical_json_bytes(value) if raw is None else raw
    path.write_bytes(proposal_bytes)
    if update_sha256:
        generation["proposal"]["sha256"] = hashlib.sha256(proposal_bytes).hexdigest()


def _judge_generation_case(
    manifest: dict,
    observations: list[dict],
    prediction: dict,
    *,
    params: M._ContrastParams | None = None,
) -> M._JudgeResult:
    return M.judge(
        copy.deepcopy(manifest),
        copy.deepcopy(observations),
        copy.deepcopy(prediction),
        params or _params(delta_min=0.5),
    )


def _all_conditions_are_indeterminate(result: M._JudgeResult) -> bool:
    return all(
        condition.status is M._Status.INDETERMINATE
        for condition in result.conditions.values()
    )


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


def _selector_reference_result(
    manifest: dict,
    observations: list[dict],
    prediction: dict,
    params: M._ContrastParams,
) -> M._JudgeResult:
    params = M._validate_contrast_params(params)
    M._validate_condition_declarations(manifest, prediction)
    manifest_map = M._mapping(manifest, "manifest")
    try:
        cells, holdouts = M._normalise_cells(manifest_map)
    except M._InputContractError:
        cells = ()
        holdouts = ()
    complete_block = False
    context = None
    if cells:
        try:
            schedule, by_cell_replicate = M._validate_complete_block(
                manifest_map, cells, params.n,
            )
            context = M._build_observation_context(
                observations, schedule, by_cell_replicate,
            )
            complete_block = True
        except M._InputContractError:
            context = None
    if not cells or not holdouts or not complete_block:
        conditions = {
            condition_id: M._condition(
                condition_id,
                M._Status.INDETERMINATE,
                {"reason": "manifest-or-complete-block-missing"},
            )
            for condition_id in M._CONDITION_IDS
        }
        official_by_holdout = {}
    else:
        first, on_off = M._evaluate_prediction_difference(
            prediction, holdouts, cells,
        )
        second = M._evaluate_swapped(
            manifest_map, prediction, holdouts, on_off, cells,
        )
        third, official_by_holdout = M._evaluate_contrast(
            cells,
            holdouts,
            context,
            on_off,
            params,
            M._source_binding_matches(manifest_map, params),
        )
        conditions = {
            M._CONDITION_IDS[0]: first,
            M._CONDITION_IDS[1]: second,
            M._CONDITION_IDS[2]: third,
        }
    cell_rows, selection_rows = M._derived_cell_rows(cells, context, holdouts)
    frozen_conditions = MappingProxyType(conditions)
    selection_rows = M._selection_evaluation_rows(
        cells,
        selection_rows,
        manifest_map,
        prediction,
        holdouts,
        frozen_conditions,
    )
    return M._JudgeResult(
        conditions=frozen_conditions,
        conclusion=M._derive_conclusion(frozen_conditions),
        cell_rows=cell_rows,
        selection_rows=selection_rows,
        official_by_holdout=MappingProxyType(dict(official_by_holdout)),
    )


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


def test_generation_diagnostic_reason_enum_contains_required_closed_values() -> None:
    assert {
        "generation-results-missing",
        "generation-sequence-invalid",
        "final-generation-missing",
        "final-harness-missing",
        "generation-harness-outcome-mismatch",
        "final-outcome-not-admissible",
        "final-variant-missing-or-invalid",
        "terminal-stop-reason-invalid",
        "proposal-binding-missing-or-invalid",
        "proposal-bytes-unreadable",
        "proposal-sha256-mismatch",
        "proposal-not-canonical-json",
        "proposal-schema-invalid",
        "proposal-arm-binding-mismatch",
        "proposal-axis-invalid",
        "proposal-wire-invalid",
        "variant-normal-form-conflict",
    } <= M._GENERATION_DIAGNOSTIC_REASONS


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


def test_selector_path_remains_exact_without_marker() -> None:
    manifest = _manifest()
    observations = _observations(manifest)
    prediction = _prediction()
    params = _params()
    expected = _selector_reference_result(
        copy.deepcopy(manifest),
        copy.deepcopy(observations),
        copy.deepcopy(prediction),
        params,
    )
    actual = M.judge(manifest, observations, prediction, params)
    assert actual == expected
    result_snapshot = {
        "conditions": {
            condition_id: {
                "condition_id": condition.condition_id,
                "status": condition.status.value,
                "diagnostics": M._plain(condition.diagnostics),
            }
            for condition_id, condition in actual.conditions.items()
        },
        "conclusion": actual.conclusion.value,
        "cell_rows": M._plain(actual.cell_rows),
        "selection_rows": M._plain(actual.selection_rows),
        "official_by_holdout": {
            holdout_id: status.value
            for holdout_id, status in actual.official_by_holdout.items()
        },
    }
    snapshot_bytes = json.dumps(
        result_snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(snapshot_bytes).hexdigest() == (
        "7974acc6362f1ff6955e76143cf6c5472c708fc39b8a0035e85f50c8e573b92e"
    )

    provenance = {
        "floor_protocol_path": "/sealed/floor-protocol.json",
        "floor_protocol_sha256": "1" * 64,
        "floor_source_path": "/sealed/floor-source.cc",
        "floor_source_sha256": "2" * 64,
        "env_tag": "selector-golden",
        "frozen_at_head": "3" * 40,
    }
    actual_rows = {
        "descriptive_only": actual.cell_rows,
        "official_status": M._official_rows(actual.cell_rows, actual),
        "selection_evaluation": M._selection_rows(actual.cell_rows, actual),
    }
    expected_rows = {
        "descriptive_only": expected.cell_rows,
        "official_status": M._official_rows(expected.cell_rows, expected),
        "selection_evaluation": M._selection_rows(expected.cell_rows, expected),
    }
    for table_name in M._TABLE_NAMES:
        actual_bytes = M._table_bytes(
            table_name, actual_rows[table_name], actual, provenance,
        )
        assert actual_bytes == M._table_bytes(
            table_name, expected_rows[table_name], expected, provenance,
        )
        assert hashlib.sha256(actual_bytes).hexdigest() == {
            "descriptive_only": (
                "6319ab5d809edbb73518bf644d1774fa9e9e88ca02a5fbef472efd8aadb753dd"
            ),
            "official_status": (
                "b1769163d5c02ea805db5b315c348315926fd88e26f716f2a2ec744941de8895"
            ),
            "selection_evaluation": (
                "eb7a06012061f372ba4c7e64ac4c7123c1442874b2702fed0fcf60fc6edb890d"
            ),
        }[table_name]


def test_generation_marker_rejects_selector_shaped_mixed_input() -> None:
    manifest = _manifest()
    manifest["experiment_kind"] = "generation_search"
    prediction = _prediction()
    prediction["experiment_kind"] = "generation_search"
    result = M.judge(
        manifest, _observations(manifest), prediction, _params(),
    )
    assert _all_conditions_are_indeterminate(result)
    assert {
        condition.diagnostics["reason"]
        for condition in result.conditions.values()
    } == {"generation-schema-invalid"}


def test_generation_cell_configuration_id_is_an_independent_schema_error(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    manifest["cells"][0]["configuration_id"] = "selector-identity"
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics
    assert diagnostic["reason"] == "generation-schema-invalid"
    assert tuple(diagnostic["mismatches"]) == ({
        "path": "manifest.cells[0].configuration_id",
        "expected": "absent",
        "actual": "selector-identity",
    },)


def test_generation_selector_prediction_key_is_an_independent_schema_error(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    prediction["on_off"] = {"H1": {"on": "unused", "off": "unused"}}
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics
    assert diagnostic["reason"] == "generation-schema-invalid"
    assert tuple(diagnostic["mismatches"]) == ({
        "path": "prediction.on_off",
        "expected": "absent",
        "actual": {"H1": {"on": "unused", "off": "unused"}},
    },)


def test_generation_cell_workload_is_independently_required(tmp_path: Path) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    manifest["cells"][0].pop("workload")
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics
    assert diagnostic["reason"] == "generation-schema-invalid"
    assert diagnostic["mismatches"] == ()


@pytest.mark.parametrize("marker_owner", ["manifest", "prediction"])
def test_generation_marker_requires_exact_str_type(
    tmp_path: Path, marker_owner: str,
) -> None:
    class MarkerSubclass(str):
        pass

    manifest, observations, prediction = _generation_case(tmp_path)
    if marker_owner == "manifest":
        manifest["experiment_kind"] = MarkerSubclass("generation_search")
        expected_reason = "experiment-kind-invalid"
    else:
        prediction["experiment_kind"] = MarkerSubclass("generation_search")
        expected_reason = "generation-schema-invalid"
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    assert {
        condition.diagnostics["reason"]
        for condition in result.conditions.values()
    } == {expected_reason}


def test_unknown_experiment_kind_is_indeterminate() -> None:
    manifest = _manifest()
    manifest["experiment_kind"] = "selector"
    result = M.judge(
        manifest, _observations(manifest), _prediction(), _params(),
    )
    assert _all_conditions_are_indeterminate(result)
    assert {
        condition.diagnostics["reason"]
        for condition in result.conditions.values()
    } == {"experiment-kind-invalid"}


def test_prediction_marker_without_manifest_authority_is_indeterminate() -> None:
    prediction = _prediction()
    prediction["experiment_kind"] = "generation_search"
    manifest = _manifest()
    result = M.judge(
        manifest, _observations(manifest), prediction, _params(),
    )
    assert _all_conditions_are_indeterminate(result)


def test_generation_fixture_pins_literal_axis_and_canonical_json_bytes(
    tmp_path: Path,
) -> None:
    _, _, prediction = _generation_case(tmp_path)
    proposal_path = Path(_generation_two(prediction, "H1-on")["proposal"]["path"])
    assert proposal_path.read_bytes() == (
        b'{"arm_binding_digest_sha256":"'
        b'd400fed6f4b325fc51e8e78b43c42d737e6debb29ed5e8bcbfc0fdb22d177503'
        b'","coder":{"axis":"silo-backoff-trigger-gating","wire":"10000"}}'
    )


@pytest.mark.parametrize(
    ("case", "wire_override", "expected"),
    [
        pytest.param("wire-follow", {}, M._Status.SATISFIED, id="wire-follow"),
        pytest.param(
            "wire-mismatch",
            {"H1-swapped": "10000"},
            M._Status.UNSATISFIED,
            id="wire-mismatch",
        ),
    ],
)
def test_generation_swapped_follow_through_is_not_axis_tautology(
    tmp_path: Path,
    case: str,
    wire_override: dict[str, str],
    expected: M._Status,
) -> None:
    manifest, observations, prediction = _generation_case(
        tmp_path, wires=wire_override,
    )
    result = _judge_generation_case(manifest, observations, prediction)
    condition = result.conditions["swapped_follow_through"]
    assert condition.status is expected
    assert case in {"wire-follow", "wire-mismatch"}
    for diagnostic in condition.diagnostics["holdouts"].values():
        assert diagnostic["expected_normal_form"]["axis"] == _TEST_GENERATION_AXIS
        assert diagnostic["actual_normal_form"]["axis"] == _TEST_GENERATION_AXIS
    if case == "wire-mismatch":
        diagnostic = condition.diagnostics["holdouts"]["H1"]
        assert diagnostic["matched"] is False
        assert diagnostic["mismatch_components"] == ("parameters.wire",)
        assert diagnostic["expected_normal_form"]["axis"] == diagnostic[
            "actual_normal_form"
        ]["axis"]


def test_generation_swapped_constant_source_family_is_unsatisfied(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(
        tmp_path,
        wires={
            "H2-on": "10000",
            "H1-swapped": "10000",
            "H2-swapped": "10000",
        },
    )
    result = _judge_generation_case(manifest, observations, prediction)
    assert _status(result, "on_off_prediction_difference") is M._Status.SATISFIED
    swapped = result.conditions["swapped_follow_through"]
    assert swapped.status is M._Status.UNSATISFIED
    assert swapped.diagnostics["reason"] == "source-on-normal-forms-constant"
    assert swapped.diagnostics["source_on_normal_forms_constant"] is True
    assert _status(result, "paired_repeat_contrast") is M._Status.SATISFIED


def test_generation_converged_same_variant_and_normal_form_is_unsatisfied(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(
        tmp_path,
        wires={"H1-off": "10000", "H2-off": "01000"},
        variants={"H1-off": "000000000001", "H2-off": "000000000004"},
    )
    result = _judge_generation_case(manifest, observations, prediction)
    assert not _all_conditions_are_indeterminate(result)
    assert _status(result, "on_off_prediction_difference") is M._Status.UNSATISFIED
    contrast = result.conditions["paired_repeat_contrast"]
    assert contrast.status is M._Status.UNSATISFIED
    assert contrast.diagnostics["holdouts"]["H1"]["same_prediction"] is True


def test_generation_same_normal_form_different_variant_is_unsatisfied(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(
        tmp_path,
        wires={"H1-off": "10000", "H2-off": "01000"},
    )
    result = _judge_generation_case(manifest, observations, prediction)
    difference = result.conditions["on_off_prediction_difference"]
    assert difference.status is M._Status.UNSATISFIED
    assert difference.diagnostics["holdouts"]["H1"]["normal_form_equal"] is True
    contrast = result.conditions["paired_repeat_contrast"]
    assert contrast.status is M._Status.UNSATISFIED
    h1 = contrast.diagnostics["holdouts"]["H1"]
    assert h1["on_variant"] != h1["off_variant"]
    assert h1["same_prediction"] is True


def test_generation_duplicate_final_outcome_is_not_admissible(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    generation = _generation_two(prediction, "H1-on")
    generation["outcome"] = "duplicate"
    generation["harness"]["outcome"] = "duplicate"
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == "final-outcome-not-admissible"


@pytest.mark.parametrize(
    ("mutation", "numbers"),
    [
        pytest.param("reordered", [2, 1], id="reordered"),
        pytest.param("missing-g2", [1], id="missing-g2"),
        pytest.param("duplicate-g2", [1, 2, 2], id="duplicate-g2"),
        pytest.param("extra-g3", [1, 2, 3], id="extra-g3"),
    ],
)
def test_generation_outcome_requires_exact_generation_sequence(
    tmp_path: Path,
    mutation: str,
    numbers: list[int],
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    original = _generation_record(prediction, "H1-on")["generations"]
    by_number = {item["generation"]: item for item in original}
    replacements = []
    for number in numbers:
        if number in by_number:
            replacements.append(copy.deepcopy(by_number[number]))
        else:
            replacements.append({"generation": number})
    _generation_record(prediction, "H1-on")["generations"] = replacements
    result = _judge_generation_case(manifest, observations, prediction)
    assert mutation in {"reordered", "missing-g2", "duplicate-g2", "extra-g3"}
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == "generation-sequence-invalid"
    assert diagnostic["generation_numbers"] == tuple(numbers)


def test_generation_result_record_swap_is_indeterminate(tmp_path: Path) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    results = prediction["generation_results"]
    results["H1-on"], results["H1-off"] = results["H1-off"], results["H1-on"]
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    assert result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]["reason"] == "generation-cell-binding-invalid"


@pytest.mark.parametrize(
    ("field", "actual", "expected"),
    [
        pytest.param("workload", "rr20", "rr80", id="workload-only"),
        pytest.param("holdout", "H2", "H1", id="holdout-only"),
    ],
)
def test_generation_result_record_field_binding_is_independent(
    tmp_path: Path, field: str, actual: str, expected: str,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    _generation_record(prediction, "H1-on")[field] = actual
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == "generation-cell-binding-invalid"
    assert tuple(diagnostic["mismatches"]) == ({
        "path": field,
        "expected": expected,
        "actual": actual,
    },)


@pytest.mark.parametrize("mutation", ["missing", "extra"], ids=["missing", "extra"])
def test_generation_results_are_keyed_by_exact_manifest_cell_set(
    tmp_path: Path,
    mutation: str,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    if mutation == "missing":
        prediction["generation_results"].pop("H1-on")
    else:
        prediction["generation_results"]["H3-on"] = copy.deepcopy(
            prediction["generation_results"]["H1-on"]
        )
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    assert {
        condition.diagnostics["reason"]
        for condition in result.conditions.values()
    } == {"generation-results-missing"}


def test_generation_proposal_digests_are_unique_across_cells(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    source = _generation_two(prediction, "H1-on")["proposal"]["digest"]
    target = _generation_two(prediction, "H1-off")
    target["proposal"]["digest"] = source
    proposal_path = Path(target["proposal"]["path"])
    proposal_value = json.loads(proposal_path.read_text("utf-8"))
    proposal_value["arm_binding_digest_sha256"] = source
    _rewrite_generation_proposal(prediction, "H1-off", proposal_value)
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    assert result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["off"]["reason"] == "proposal-binding-missing-or-invalid"


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        pytest.param("hash-mismatch", "proposal-sha256-mismatch", id="hash-mismatch"),
        pytest.param(
            "noncanonical-json", "proposal-not-canonical-json", id="noncanonical-json",
        ),
        pytest.param("invalid-wire", "proposal-wire-invalid", id="invalid-wire"),
        pytest.param(
            "arm-binding-mismatch",
            "proposal-arm-binding-mismatch",
            id="arm-binding-mismatch",
        ),
    ],
)
def test_generation_proposal_validation_is_fail_closed(
    tmp_path: Path,
    mutation: str,
    expected_reason: str,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    generation = _generation_two(prediction, "H1-on")
    proposal_path = Path(generation["proposal"]["path"])
    proposal_value = json.loads(proposal_path.read_text("utf-8"))
    if mutation == "hash-mismatch":
        generation["proposal"]["sha256"] = "0" * 64
    elif mutation == "noncanonical-json":
        raw = json.dumps(proposal_value, indent=2, sort_keys=True).encode("utf-8")
        _rewrite_generation_proposal(prediction, "H1-on", proposal_value, raw=raw)
    elif mutation == "invalid-wire":
        proposal_value["coder"]["wire"] = "22222"
        _rewrite_generation_proposal(prediction, "H1-on", proposal_value)
    else:
        proposal_value["arm_binding_digest_sha256"] = "f" * 64
        _rewrite_generation_proposal(prediction, "H1-on", proposal_value)
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == expected_reason
    assert diagnostic["proposal_path"] is None
    if mutation == "invalid-wire":
        assert tuple(diagnostic["mismatches"]) == ({
            "path": "generations[1].proposal.json.coder.wire",
            "expected": "five-character-binary-string",
            "actual": "22222",
        },)


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        pytest.param(
            "missing-proposal",
            "proposal-binding-missing-or-invalid",
            id="missing-proposal",
        ),
        pytest.param(
            "missing-digest",
            "proposal-binding-missing-or-invalid",
            id="missing-digest",
        ),
        pytest.param(
            "unreadable-path", "proposal-bytes-unreadable", id="unreadable-path",
        ),
        pytest.param("hash-mismatch", "proposal-sha256-mismatch", id="hash-mismatch"),
        pytest.param(
            "noncanonical-json", "proposal-not-canonical-json", id="noncanonical-json",
        ),
        pytest.param(
            "arm-binding-mismatch",
            "proposal-arm-binding-mismatch",
            id="arm-binding-mismatch",
        ),
    ],
)
def test_generation_one_proposal_validation_is_fail_closed(
    tmp_path: Path, mutation: str, expected_reason: str,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    generation = _generation_by_number(prediction, "H1-on", 1)
    proposal = generation["proposal"]
    proposal_path = Path(proposal["path"])
    proposal_value = json.loads(proposal_path.read_text("utf-8"))
    if mutation == "missing-proposal":
        generation.pop("proposal")
    elif mutation == "missing-digest":
        proposal.pop("digest")
    elif mutation == "unreadable-path":
        proposal["path"] = str(tmp_path / "missing-g1-proposal.json")
    elif mutation == "hash-mismatch":
        proposal["sha256"] = "0" * 64
    elif mutation == "noncanonical-json":
        raw = json.dumps(proposal_value, indent=2, sort_keys=True).encode("utf-8")
        _rewrite_generation_proposal(
            prediction,
            "H1-on",
            proposal_value,
            generation_number=1,
            raw=raw,
        )
    else:
        proposal_value["arm_binding_digest_sha256"] = "f" * 64
        _rewrite_generation_proposal(
            prediction, "H1-on", proposal_value, generation_number=1,
        )
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == expected_reason
    assert diagnostic["proposal_generation"] == 1
    assert diagnostic["proposal_path"] is None


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        pytest.param("invalid-axis", "proposal-axis-invalid", id="invalid-axis"),
        pytest.param("symlink-path", "proposal-bytes-unreadable", id="symlink-path"),
        pytest.param(
            "unreadable-path", "proposal-bytes-unreadable", id="unreadable-path",
        ),
        pytest.param("coder-not-mapping", "proposal-schema-invalid", id="coder-not-mapping"),
    ],
)
def test_generation_proposal_shape_and_reference_are_fail_closed(
    tmp_path: Path, mutation: str, expected_reason: str,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    generation = _generation_two(prediction, "H1-on")
    proposal_path = Path(generation["proposal"]["path"])
    proposal_value = json.loads(proposal_path.read_text("utf-8"))
    if mutation == "invalid-axis":
        proposal_value["coder"]["axis"] = "wrong-axis"
        _rewrite_generation_proposal(prediction, "H1-on", proposal_value)
    elif mutation == "symlink-path":
        link_path = tmp_path / "H1-on.g2-link.json"
        link_path.symlink_to(proposal_path)
        generation["proposal"]["path"] = str(link_path)
    elif mutation == "unreadable-path":
        generation["proposal"]["path"] = str(tmp_path / "missing-g2-proposal.json")
    else:
        proposal_value["coder"] = ["not", "a", "mapping"]
        _rewrite_generation_proposal(prediction, "H1-on", proposal_value)
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    diagnostic = result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]
    assert diagnostic["reason"] == expected_reason
    assert diagnostic["proposal_generation"] == 2
    assert diagnostic["proposal_path"] is None
    if mutation == "invalid-axis":
        assert tuple(diagnostic["mismatches"]) == ({
            "path": "generations[1].proposal.json.coder.axis",
            "expected": _TEST_GENERATION_AXIS,
            "actual": "wrong-axis",
        },)


def test_proposal_diagnostic_path_is_repo_relative_or_omitted(tmp_path: Path) -> None:
    repo_path = M._REPO_ROOT / "orchestrator" / "campaign" / "proposal.json"
    assert M._repo_relative_proposal_path(str(repo_path)) == (
        "orchestrator/campaign/proposal.json"
    )
    assert M._repo_relative_proposal_path(str(tmp_path / "proposal.json")) is None


def test_generation_variant_normal_form_conflict_is_indeterminate(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(
        tmp_path, variants={"H1-off": "000000000001"},
    )
    result = _judge_generation_case(manifest, observations, prediction)
    assert _all_conditions_are_indeterminate(result)
    assert result.conditions[M._CONDITION_IDS[0]].diagnostics[
        "holdouts"
    ]["H1"]["on"]["reason"] == "variant-normal-form-conflict"


def test_generation_result_tables_use_actual_and_expected_g2_variants(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    result = _judge_generation_case(manifest, observations, prediction)
    variants = {
        cell_id: _generation_two(prediction, cell_id)["harness"]["variant"]
        for cell_id in prediction["generation_results"]
    }
    by_cell = {row["cell_id"]: row for row in result.selection_rows}
    assert by_cell["H1-on"]["configuration_id"] == variants["H1-on"]
    assert by_cell["H1-on"]["predicted_configuration_id"] == variants["H1-on"]
    assert by_cell["H1-off"]["predicted_configuration_id"] == variants["H1-off"]
    assert by_cell["H1-swapped"]["configuration_id"] == variants["H1-swapped"]
    assert by_cell["H1-swapped"]["predicted_configuration_id"] == variants["H2-on"]
    assert by_cell["H2-swapped"]["predicted_configuration_id"] == variants["H1-on"]


def test_generation_invalid_swap_mapping_does_not_invent_expected_variants(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    manifest["swapped_mapping"] = {"H1": "H1", "H2": "H2"}
    result = _judge_generation_case(manifest, observations, prediction)
    assert result.conditions["swapped_follow_through"].status is M._Status.INDETERMINATE
    by_cell = {row["cell_id"]: row for row in result.selection_rows}
    for cell_id in ("H1-swapped", "H2-swapped"):
        assert by_cell[cell_id]["predicted_configuration_id"] is None
        assert by_cell[cell_id]["predicted_rank"] is None
        assert by_cell[cell_id]["prediction_matches_rank"] is False


def test_generation_prediction_marker_is_optional_but_must_match_when_present(
    tmp_path: Path,
) -> None:
    manifest, observations, prediction = _generation_case(tmp_path)
    prediction.pop("experiment_kind")
    assert not _all_conditions_are_indeterminate(
        _judge_generation_case(manifest, observations, prediction)
    )
    prediction["experiment_kind"] = "selector"
    assert _all_conditions_are_indeterminate(
        _judge_generation_case(manifest, observations, prediction)
    )


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
