# -*- coding: utf-8 -*-
"""Closed Layer-3 admission diagnosis and fail-closed publication tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import autonomous_trial_completeness as C  # noqa: E402
from orchestrator.campaign import layer3_report as L3                 # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as A   # noqa: E402


_DIAGNOSIS_KEYS = {
    "schema_version",
    "status",
    "validator",
    "validator_value",
    "absolute_instance_path",
    "absolute_schema_path",
    "offending_property",
    "degradation_reason",
}


def _raise_screening_type_failure(*_args, **_kwargs):
    schema = {
        "type": "object",
        "properties": {"screening": {"type": "boolean"}},
        "additionalProperties": False,
    }
    try:
        Draft7Validator(schema).validate({"screening": "enabled"})
    except ValidationError as cause:
        raise L3.Layer3ReportError("layer3 schema 検証に失敗") from cause
    raise AssertionError("fixture schema unexpectedly accepted invalid screening")


def _raise_surrogate_validator_failure(*_args, **_kwargs):
    cause = ValidationError(
        "fixture validation error with a non-UTF-8 validator value",
        validator="const",
        validator_value="\udcff",
        path=["screening"],
        schema_path=["properties", "screening", "const"],
    )
    raise L3.Layer3ReportError("layer3 schema 検証に失敗") from cause


def _required_failure(required: list[str], instance: dict):
    def raise_failure(*_args, **_kwargs):
        schema = {
            "type": "object",
            "required": required,
            "properties": {
                key: {} for key in required
            },
            "additionalProperties": False,
        }
        try:
            Draft7Validator(schema).validate(instance)
        except ValidationError as cause:
            raise L3.Layer3ReportError("layer3 schema 検証に失敗") from cause
        raise AssertionError("fixture schema unexpectedly accepted missing fields")

    return raise_failure


def _screening_diagnosis() -> dict:
    try:
        _raise_screening_type_failure()
    except L3.Layer3ReportError as error:
        return A._layer3_admission_diagnosis(error)
    raise AssertionError("fixture Layer3ReportError was not raised")


def _failure_decision() -> dict:
    return {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": (
                "build cell campaign admission/Layer-3 validation failed: "
                "layer3 schema 検証に失敗"
            ),
        },
    }


def _install_layer3_failure_trial(
    tmp_path, monkeypatch, *, render_failure,
) -> None:
    output_root = tmp_path / "output"
    campaign_id = "fixture-layer3-admission-failure"
    campaign = output_root / "campaigns" / campaign_id
    (campaign / "reports").mkdir(parents=True)
    entry = A.resolve_workload_entry("ycsb-a")

    monkeypatch.setattr(
        A, "_assert_build_site_opted_in", lambda *_a, **_k: None,
    )
    monkeypatch.setattr(A, "_assert_reservation_preflight", lambda **_k: None)
    monkeypatch.setattr(
        A, "_assert_build_transport_admitted", lambda *_a, **_k: None,
    )
    monkeypatch.setattr(A, "build_run_context", lambda **_k: object())
    monkeypatch.setattr(A.layer3_report, "render", render_failure)
    monkeypatch.setattr(
        C, "require_admitted_campaign", lambda *_a, **_k: object(),
    )

    def fixture_workload(**kwargs):
        kwargs["_partial"]["cell"] = {
            "workload": "ycsb-a",
            "campaign_id": campaign_id,
            "campaign_root": str(campaign),
            "workload_flags": dict(entry["ycsb"]),
            "generations": [],
            "stop_reason": "converged",
            "_pending_critics": [],
        }
        raise RuntimeError("fixture supervisor failure before admission")

    monkeypatch.setattr(A, "_run_workload", fixture_workload)


def test_validation_error_projection_is_closed_and_names_screening() -> None:
    diagnosis = _screening_diagnosis()

    assert set(diagnosis) == _DIAGNOSIS_KEYS
    assert diagnosis == {
        "schema_version": (
            "p3-autonomous-workload-trial-layer3-admission-diagnosis/v1"
        ),
        "status": "validation-error",
        "validator": "type",
        "validator_value": "boolean",
        "absolute_instance_path": ["screening"],
        "absolute_schema_path": ["properties", "screening", "type"],
        "offending_property": "screening",
        "degradation_reason": None,
    }


def test_additional_property_failure_names_unpathed_property() -> None:
    try:
        Draft7Validator({
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }).validate({"screening": True})
    except ValidationError as cause:
        error = L3.Layer3ReportError("layer3 schema 検証に失敗")
        error.__cause__ = cause
    else:
        raise AssertionError("fixture schema unexpectedly accepted screening")

    diagnosis = A._layer3_admission_diagnosis(error)
    assert diagnosis["validator"] == "additionalProperties"
    assert diagnosis["absolute_instance_path"] == []
    assert diagnosis["offending_property"] == "screening"


@pytest.mark.parametrize("cause_kind", ["missing", "wrong", "unprojectable"])
def test_diagnosis_extraction_is_total_and_degrades(cause_kind) -> None:
    error = L3.Layer3ReportError("fixture layer3 failure")
    if cause_kind == "wrong":
        error.__cause__ = RuntimeError("not a validation error")
    elif cause_kind == "unprojectable":
        error.__cause__ = ValidationError(
            "fixture validation error",
            validator="type",
            validator_value=object(),
            path=["screening"],
            schema_path=["properties", "screening", "type"],
        )

    diagnosis = A._layer3_admission_diagnosis(error)
    assert set(diagnosis) == _DIAGNOSIS_KEYS
    assert diagnosis["status"] == "degraded"
    assert diagnosis["validator"] is None
    assert diagnosis["offending_property"] is None
    assert diagnosis["degradation_reason"] == (
        "validation-error-projection-failed"
        if cause_kind == "unprojectable"
        else "validation-error-cause-not-found"
    )
    assert C.is_exact_layer3_admission_diagnosis(diagnosis) is True


def test_diagnosis_degrades_for_non_string_validator() -> None:
    error = L3.Layer3ReportError("fixture layer3 failure")
    error.__cause__ = ValidationError(
        "fixture validation error",
        validator=123,
        validator_value="v",
        path=[],
        schema_path=[],
    )

    diagnosis = A._layer3_admission_diagnosis(error)

    assert diagnosis["status"] == "degraded"
    assert diagnosis["degradation_reason"] == (
        "validation-error-projection-failed"
    )


def test_diagnosis_degrades_for_non_json_path_component_and_stays_canonical(
) -> None:
    for path_component in (object(), {"not": "a path scalar"}):
        error = L3.Layer3ReportError("fixture layer3 failure")
        error.__cause__ = ValidationError(
            "fixture validation error",
            validator="const",
            validator_value="v",
            path=[path_component],
            schema_path=[],
        )

        diagnosis = A._layer3_admission_diagnosis(error)

        assert diagnosis["status"] == "degraded"
        assert diagnosis["degradation_reason"] == (
            "validation-error-projection-failed"
        )
        assert json.loads(
            A._canonical_json_bytes(diagnosis).decode("utf-8")
        ) == diagnosis


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param("extra-key", id="extra-key"),
        pytest.param("schema-version", id="schema-version"),
        pytest.param("status", id="status"),
        pytest.param("validator", id="validator"),
        pytest.param("degradation-reason", id="degradation-reason"),
        pytest.param("path-container", id="path-container"),
        pytest.param("path-component", id="path-component"),
        pytest.param("surrogate", id="non-utf8-validator-value"),
    ],
)
def test_layer3_admission_diagnosis_exact_predicate_rejects_mutations(
    mutation,
) -> None:
    diagnosis = _screening_diagnosis()
    assert C.is_exact_layer3_admission_diagnosis(diagnosis) is True

    if mutation == "extra-key":
        diagnosis["extra"] = True
    elif mutation == "schema-version":
        diagnosis["schema_version"] = "wrong/v1"
    elif mutation == "status":
        diagnosis["status"] = "unknown"
    elif mutation == "validator":
        diagnosis["validator"] = None
    elif mutation == "degradation-reason":
        diagnosis["degradation_reason"] = "unexpected"
    elif mutation == "path-container":
        diagnosis["absolute_instance_path"] = ("screening",)
    elif mutation == "path-component":
        diagnosis["absolute_schema_path"] = [-1]
    elif mutation == "surrogate":
        diagnosis["validator_value"] = "\udcff"
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(f"unknown mutation: {mutation}")

    assert C.is_exact_layer3_admission_diagnosis(diagnosis) is False


def test_failure_projection_rejects_present_nonmapping_diagnosis() -> None:
    cell = {
        "workload": "ycsb-a",
        "admission_decision": _failure_decision(),
        "layer3_admission_diagnosis": "not-a-mapping",
    }

    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"Layer-3 admission diagnosis is not exact$",
    ):
        C.cell_admission_failure_projection([cell])


def test_failure_decision_stays_exact_while_projection_carries_diagnosis() -> None:
    decision = _failure_decision()
    diagnosis = _screening_diagnosis()
    cell = {
        "workload": "ycsb-a",
        "admission_decision": decision,
        C.LAYER3_ADMISSION_DIAGNOSIS_KEY: diagnosis,
    }

    projection = C.cell_admission_failure_projection([cell])

    assert set(decision) == {"schema_version", "admission_status", "error"}
    assert set(decision["error"]) == {"type", "message"}
    assert C.is_exact_cell_admission_failure_decision(decision) is True
    assert projection == [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": decision,
        C.LAYER3_ADMISSION_DIAGNOSIS_KEY: diagnosis,
    }]


def test_campaignless_fallback_producer_does_not_gain_diagnosis(
    tmp_path,
) -> None:
    cell = {
        "workload": "ycsb-a",
        "generations": [],
        "stop_reason": "supervisor-error",
        "error": {"type": "RuntimeError", "message": "fixture failure"},
        "_pending_critics": [],
    }

    admitted = A._finalize_cell_admission(
        cell,
        do_build=True,
        launch_admission=object(),
        journal=A.AttemptJournal(tmp_path / "attempts.jsonl"),
    )

    assert admitted is False
    assert set(cell) == {
        "workload", "generations", "stop_reason", "error",
        "admission_decision", "pending_critic_disposition",
    }
    assert C.is_exact_campaignless_failure_fallback_cell(cell) is True
    assert C.LAYER3_ADMISSION_DIAGNOSIS_KEY not in cell
    projection = C.cell_admission_failure_projection([cell])
    assert C.LAYER3_ADMISSION_DIAGNOSIS_KEY not in projection[0]


def test_attempt_journal_append_orders_write_fsync_close(
    tmp_path, monkeypatch,
) -> None:
    calls = []
    real_write = A.os.write
    real_fsync = A.os.fsync
    real_close = A.os.close

    def write(fd, data):
        calls.append(("write", fd))
        return real_write(fd, data)

    def fsync(fd):
        calls.append(("fsync", fd))
        return real_fsync(fd)

    def close(fd):
        calls.append(("close", fd))
        return real_close(fd)

    monkeypatch.setattr(A.os, "write", write)
    monkeypatch.setattr(A.os, "fsync", fsync)
    monkeypatch.setattr(A.os, "close", close)

    A.AttemptJournal(tmp_path / "attempts.jsonl").append({
        "event": "run-finish",
        "status": "partial",
    })

    assert [name for name, _fd in calls] == ["write", "fsync", "close"]
    assert len({fd for _name, fd in calls}) == 1


@pytest.mark.parametrize(
    ("render_failure", "expected_status", "expected_property"),
    [
        pytest.param(
            _raise_screening_type_failure,
            "validation-error",
            "screening",
            id="ordinary-validation-error",
        ),
        pytest.param(
            _raise_surrogate_validator_failure,
            "degraded",
            None,
            id="surrogate-validator-value",
        ),
    ],
)
def test_run_trial_preserves_chain_exception_identity_and_runs_completeness(
    tmp_path, monkeypatch, render_failure, expected_status, expected_property,
) -> None:
    _install_layer3_failure_trial(
        tmp_path, monkeypatch, render_failure=render_failure,
    )
    completeness_calls = []

    def real_completeness(**kwargs):
        C.assert_autonomous_trial_completeness(**kwargs)
        completeness_calls.append(kwargs)

    monkeypatch.setattr(A, "assert_autonomous_trial_completeness", real_completeness)
    chain_message = (
        "cells[0] failure campaign remains independently admitted"
    )
    sentinel = C.AutonomousTrialCompletenessError(
        f"[campaign-chain] {chain_message}"
    )
    original_fail = C._fail

    def identity_pinned_fail(gate, message):
        if (
            gate == "campaign-chain"
            and message == chain_message
        ):
            raise sentinel
        original_fail(gate, message)

    monkeypatch.setattr(C, "_fail", identity_pinned_fail)
    run = tmp_path / "run"

    with pytest.raises(C.AutonomousTrialCompletenessError) as caught:
        A.run_trial(
            trial_id="layer3-admission-diagnosis",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            providers={},
            run_root=run,
            sub="/unused",
            do_build=True,
            coder_authority=object(),
            allow_unregistered_exploratory=True,
        )

    assert caught.value is sentinel
    assert type(caught.value) is C.AutonomousTrialCompletenessError
    assert not isinstance(caught.value, TypeError)
    assert not (run / "report.json").exists()
    assert not (run / "admission_failure.json").exists()
    events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert events[-1]["event"] == "run-finish"
    failures = events[-1]["cell_admission_failures"]
    diagnosis = failures[0][C.LAYER3_ADMISSION_DIAGNOSIS_KEY]
    assert diagnosis["status"] == expected_status
    assert diagnosis["offending_property"] == expected_property
    assert C.is_exact_layer3_admission_diagnosis(diagnosis) is True
    assert C.is_exact_cell_admission_failure_decision(
        failures[0]["admission_decision"]
    ) is True
    assert len(completeness_calls) == 1
    verified = completeness_calls[0]
    assert verified["attempt_journal"] == run / "attempts.jsonl"
    assert verified["report"]["cells"][0][
        C.LAYER3_ADMISSION_DIAGNOSIS_KEY
    ] == diagnosis


@pytest.mark.parametrize(
    ("required", "instance", "expected_property"),
    [
        pytest.param(
            ["present", "missing"],
            {"present": True},
            "missing",
            id="single-missing",
        ),
        pytest.param(
            ["present", "first-missing", "second-missing"],
            {"present": True},
            "first-missing",
            id="multiple-missing-required-order",
        ),
    ],
)
def test_required_failure_names_first_missing_property_in_journal(
    tmp_path, monkeypatch, required, instance, expected_property,
) -> None:
    _install_layer3_failure_trial(
        tmp_path,
        monkeypatch,
        render_failure=_required_failure(required, instance),
    )
    sentinel = C.AutonomousTrialCompletenessError(
        "fixture chain stop after real completeness"
    )

    def stop_at_chain(**_kwargs):
        raise sentinel

    monkeypatch.setattr(A, "assert_campaign_layer3_chain", stop_at_chain)
    run = tmp_path / "run"

    with pytest.raises(C.AutonomousTrialCompletenessError) as caught:
        A.run_trial(
            trial_id="layer3-required-diagnosis",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            providers={},
            run_root=run,
            sub="/unused",
            do_build=True,
            coder_authority=object(),
            allow_unregistered_exploratory=True,
        )

    assert caught.value is sentinel
    events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert events[-1]["event"] == "run-finish"
    diagnosis = events[-1]["cell_admission_failures"][0][
        "layer3_admission_diagnosis"
    ]
    assert diagnosis["validator"] == "required"
    assert diagnosis["validator_value"] == required
    assert diagnosis["offending_property"] == expected_property
    assert C.is_exact_layer3_admission_diagnosis(diagnosis) is True


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
