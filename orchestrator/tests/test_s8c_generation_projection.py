"""8c 世代間射影 leaf の閉包と変異検出。"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json

import pytest

from orchestrator.campaign import s8c_generation_projection as P


GATING_SPEC = "fixed gating spec bytes"
ALLOWLIST_SHA256 = "a" * 64


def _descriptor() -> dict:
    return {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "read_write": {"read_ratio_percent": 50, "rmw": 0},
        "contention": {"skew": 0.9, "label": "high"},
        "scale": {"records": 100_000, "threads": 4},
        "objective": "maximize_throughput_tps",
        "correctness": "serializable_legacy_and_s2",
    }


def _binding() -> dict:
    return {
        "projection_version": "8b-descriptor-projection/v1",
        "input_sha256": "a" * 64,
        "output_sha256": "b" * 64,
        "schema_sha256": "c" * 64,
    }


def _whiteboard() -> list[dict]:
    return [{
        "iteration": 1,
        "direction": "increase",
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }]


def _source_metrics() -> dict:
    return {
        "throughput_tps": 999_999.0,
        "abort_rate": 0.125,
        "latency_ns": 42.0,
        "llc_miss_rate": None,
        "ipc": 1.75,
    }


def _critic() -> dict:
    return {
        "attribution": "critic-claims abort_rate=0.999 latency_ns=999999",
        "recommend": "RECOMMEND_SENTINEL_8C_41F2",
        "avoid": "AVOID_SENTINEL_8C_A903",
        "uncertainty": "  uncertain free text  ",
        "reverse_recommended": True,
    }


def _common(*, workload: str = "ycsb-a", generation: int = 2) -> dict:
    return {
        "schema_version": P.ROLE_SCHEMA_VERSION,
        "pilot_scope": P.PILOT_SCOPE,
        "scientific_claim": False,
        "workload": workload,
        "generation": generation,
        "workload_descriptor": _descriptor(),
        "descriptor_binding": _binding(),
        "attempt_policy": dict(P.ATTEMPT_POLICY),
        "stop_policy": dict(P.STOP_POLICY),
    }


def _null_perf() -> dict:
    return {
        "throughput_tps": None,
        "abort_rate_pct": None,
        "latency_ns": None,
        "llc_miss_rate": None,
        "ipc": None,
    }


def _null_leading() -> dict:
    return {
        "contention_level": "high",
        "cache_miss_rate_pct": None,
        "IPC_overall": None,
    }


def _planner_payload(projection: dict) -> dict:
    return {
        **_common(),
        "current_perf": _null_perf(),
        "leading_indicators": _null_leading(),
        "whiteboard": _whiteboard(),
        "critic_feedback": copy.deepcopy(projection),
    }


def _coder_payload(*, workload: str = "ycsb-a") -> dict:
    return {
        **_common(workload=workload),
        "leakproof_context": P.LEAKPROOF_CONTEXT,
        "gating_spec": GATING_SPEC,
        "planner_direction": {
            "axis": P.PLANNER_AXIS,
            "direction": "increase",
            "magnitude": "small",
        },
        "baseline": _null_perf(),
        "whiteboard": _whiteboard(),
    }


def _validate_planner(
    payload: dict,
    projection: dict,
    *,
    expected_current_perf: dict | None = None,
    expected_leading_indicators: dict | None = None,
) -> P.PayloadValidationReceipt:
    return P.validate_planner_payload(
        payload,
        expected_workload="ycsb-a",
        expected_generation=2,
        expected_workload_descriptor=_descriptor(),
        expected_descriptor_binding=_binding(),
        expected_whiteboard_origin=_whiteboard(),
        expected_current_perf=(
            _null_perf()
            if expected_current_perf is None
            else expected_current_perf
        ),
        expected_leading_indicators=(
            _null_leading()
            if expected_leading_indicators is None
            else expected_leading_indicators
        ),
        expected_critic_feedback=projection,
        payload_allowlist_sha256=ALLOWLIST_SHA256,
    )


def _validate_coder(
    payload: dict, snapshot: P.GatingSpecSnapshot,
) -> P.PayloadValidationReceipt:
    return P.validate_coder_payload(
        payload,
        expected_workload=payload["workload"],
        expected_generation=2,
        expected_workload_descriptor=_descriptor(),
        expected_descriptor_binding=_binding(),
        expected_whiteboard_origin=_whiteboard(),
        expected_baseline=_null_perf(),
        gating_spec_snapshot=snapshot,
        payload_allowlist_sha256=ALLOWLIST_SHA256,
    )


def test_valid_two_generation_projection_and_payloads_are_accepted() -> None:
    applied = P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    )
    snapshot = P.snapshot_gating_spec(GATING_SPEC)

    assert dataclasses.is_dataclass(applied)
    assert [field.name for field in dataclasses.fields(applied)] == [
        "planner_projection", "prior_reverse",
    ]
    assert applied.prior_reverse is True
    assert applied.planner_projection == {
        "source_generation": 1,
        "diagnostics": [
            {"metric": "abort_rate", "value": 0.125},
            {"metric": "latency_ns", "value": 42.0},
            {"metric": "llc_miss_rate", "value": None},
            {"metric": "ipc", "value": 1.75},
        ],
        "uncertainty_present": True,
        "reverse_recommended": True,
    }
    _validate_planner(
        _planner_payload(dict(applied.planner_projection)),
        dict(applied.planner_projection),
    )
    _validate_coder(_coder_payload(), snapshot)
    assert snapshot.text == GATING_SPEC
    assert snapshot.utf8_bytes == GATING_SPEC.encode("utf-8")
    assert snapshot.sha256 == hashlib.sha256(GATING_SPEC.encode("utf-8")).hexdigest()


def test_validation_receipt_seals_payload_spec_and_safe_projection() -> None:
    applied = P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    )
    payload = _planner_payload(dict(applied.planner_projection))
    payload["current_perf"]["throughput_tps"] = 12345.0
    expected_perf = copy.deepcopy(payload["current_perf"])
    receipt = _validate_planner(
        payload,
        dict(applied.planner_projection),
        expected_current_perf=expected_perf,
    )
    stored = receipt.as_dict()

    assert stored["schema_version"] == P.VALIDATION_RECEIPT_SCHEMA_VERSION
    assert stored["payload_allowlist_sha256"] == ALLOWLIST_SHA256
    assert stored["safe_projection"]["current_perf_nullness"][
        "throughput_tps"
    ] is False
    diagnostics = stored["safe_projection"]["critic_feedback"]["diagnostics"]
    assert all(set(item) == {"metric", "value_is_null", "value_sha256"} for item in diagnostics)
    assert "12345.0" not in json.dumps(stored["safe_projection"], sort_keys=True)
    receipt.assert_bound_to(
        role="planner",
        payload=payload,
        payload_allowlist_sha256=ALLOWLIST_SHA256,
    )
    payload["generation"] = 3
    with pytest.raises(P.PayloadValidationError, match="payload digest"):
        receipt.assert_bound_to(
            role="planner",
            payload=payload,
            payload_allowlist_sha256=ALLOWLIST_SHA256,
        )


def test_critic_free_text_and_winning_metric_do_not_reach_second_layer() -> None:
    applied = P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    )
    encoded = json.dumps(applied.planner_projection, sort_keys=True)

    assert "RECOMMEND_SENTINEL_8C_41F2" not in encoded
    assert "AVOID_SENTINEL_8C_A903" not in encoded
    assert "critic-claims" not in encoded
    assert "uncertain free text" not in encoded
    assert "throughput_tps" not in encoded
    assert "999999.0" not in encoded


def test_diagnostics_are_from_source_not_critic_claims() -> None:
    applied = P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    )
    values = {
        item["metric"]: item["value"]
        for item in applied.planner_projection["diagnostics"]
    }
    assert values == {
        "abort_rate": 0.125,
        "latency_ns": 42.0,
        "llc_miss_rate": None,
        "ipc": 1.75,
    }
    assert 0.999 not in values.values()
    assert 999_999.0 not in values.values()


def test_uncertainty_is_reduced_to_presence_and_reverse_stays_bool() -> None:
    critic = _critic()
    critic["uncertainty"] = "  "
    critic["reverse_recommended"] = False
    applied = P.apply_critic_feedback(
        critic, source_metrics=_source_metrics(), source_generation=1,
    )
    assert applied.planner_projection["uncertainty_present"] is False
    assert applied.planner_projection["reverse_recommended"] is False
    assert applied.prior_reverse is False


@pytest.mark.parametrize(
    ("mutate",),
    [
        (lambda critic, metrics: critic.pop("avoid"),),
        (lambda critic, metrics: critic.__setitem__("extra", "x"),),
        (lambda critic, metrics: critic.__setitem__("recommend", 1),),
        (lambda critic, metrics: critic.__setitem__("reverse_recommended", 1),),
        (lambda critic, metrics: metrics.pop("throughput_tps"),),
        (lambda critic, metrics: metrics.__setitem__("extra", None),),
        (lambda critic, metrics: metrics.__setitem__("ipc", True),),
        (lambda critic, metrics: metrics.__setitem__("ipc", float("inf")),),
        (lambda critic, metrics: metrics.__setitem__("ipc", 1),),
    ],
)
def test_apply_critic_feedback_rejects_contract_drift(mutate) -> None:
    critic = _critic()
    metrics = _source_metrics()
    mutate(critic, metrics)
    with pytest.raises(P.CriticFeedbackError):
        P.apply_critic_feedback(
            critic, source_metrics=metrics, source_generation=1,
        )


@pytest.mark.parametrize("source_generation", [True, 1.0, 0])
def test_apply_critic_feedback_rejects_invalid_source_generation(
    source_generation,
) -> None:
    with pytest.raises(P.CriticFeedbackError):
        P.apply_critic_feedback(
            _critic(),
            source_metrics=_source_metrics(),
            source_generation=source_generation,
        )


def test_planner_rejects_unknown_top_level_and_nested_keys() -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    payload = _planner_payload(projection)
    payload["unknown"] = None
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)

    payload = _planner_payload(projection)
    payload["descriptor_binding"]["unknown"] = "x"
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.__setitem__("schema_version", "other"),
        lambda payload: payload.__setitem__("pilot_scope", "other"),
        lambda payload: payload.__setitem__("scientific_claim", 0),
        lambda payload: payload["attempt_policy"].__setitem__("retry", True),
        lambda payload: payload["stop_policy"].__setitem__(
            "performance_early_stop", True
        ),
    ],
)
def test_planner_rejects_fixed_literal_drift(mutation) -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    payload = _planner_payload(projection)
    mutation(payload)
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)


def test_planner_rejects_non_none_current_perf_metric() -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    payload = _planner_payload(projection)
    payload["current_perf"]["throughput_tps"] = 123.0
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)


def test_planner_rejects_non_none_leading_indicator_metric() -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    payload = _planner_payload(projection)
    payload["leading_indicators"]["IPC_overall"] = 1.5
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)


def test_payload_validators_accept_finite_external_metric_snapshots() -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    perf = {
        "throughput_tps": 12345.0,
        "abort_rate_pct": 7.9,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    leading = {
        "contention_level": "high",
        "cache_miss_rate_pct": 12.4,
        "IPC_overall": 2.5,
    }
    planner = _planner_payload(projection)
    planner["current_perf"] = dict(perf)
    planner["leading_indicators"] = dict(leading)
    _validate_planner(
        planner,
        projection,
        expected_current_perf=perf,
        expected_leading_indicators=leading,
    )

    coder = _coder_payload()
    coder["baseline"] = dict(perf)
    P.validate_coder_payload(
        coder,
        expected_workload="ycsb-a",
        expected_generation=2,
        expected_workload_descriptor=_descriptor(),
        expected_descriptor_binding=_binding(),
        expected_whiteboard_origin=_whiteboard(),
        expected_baseline=perf,
        gating_spec_snapshot=P.snapshot_gating_spec(GATING_SPEC),
        payload_allowlist_sha256=ALLOWLIST_SHA256,
    )


def test_coder_rejects_non_none_baseline_metric() -> None:
    payload = _coder_payload()
    payload["baseline"]["latency_ns"] = 88.0
    with pytest.raises(P.PayloadValidationError):
        _validate_coder(payload, P.snapshot_gating_spec(GATING_SPEC))


def test_coder_rejects_changed_leakproof_context_literal() -> None:
    payload = _coder_payload()
    payload["leakproof_context"] = "throughput=123"
    with pytest.raises(P.PayloadValidationError):
        _validate_coder(payload, P.snapshot_gating_spec(GATING_SPEC))


def test_whiteboard_rejects_integer_throughput_in_iteration() -> None:
    whiteboard = _whiteboard()
    whiteboard[0]["iteration"] = 999_999
    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(
            whiteboard,
            current_generation=2,
            expected_origin=whiteboard,
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda board: board[0].__setitem__("iteration", True),
        lambda board: board[0].__setitem__("delta_pct", 0.0),
        lambda board: board[0].__setitem__("direction", "sideways"),
        lambda board: board[0].__setitem__("magnitude", "huge"),
        lambda board: board[0].__setitem__("result", "winner"),
        lambda board: board[0].__setitem__("extra", None),
    ],
)
def test_whiteboard_rejects_type_value_and_key_drift(mutate) -> None:
    whiteboard = _whiteboard()
    mutate(whiteboard)
    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(whiteboard, current_generation=2)


def test_generation_two_accepts_empty_whiteboard() -> None:
    P.validate_whiteboard([], current_generation=2, expected_origin=[])


def test_generation_three_accepts_whiteboard_with_missing_iteration() -> None:
    P.validate_whiteboard(
        _whiteboard(), current_generation=3, expected_origin=_whiteboard(),
    )


def test_whiteboard_rejects_non_monotonic_iterations() -> None:
    whiteboard = _whiteboard() + [{
        "iteration": 1,
        "direction": "decrease",
        "magnitude": "medium",
        "result": "fail",
        "delta_pct": None,
    }]
    whiteboard[0]["iteration"] = 2
    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(whiteboard, current_generation=3)


def test_whiteboard_rejects_iteration_beyond_previous_generation() -> None:
    whiteboard = _whiteboard()
    whiteboard[0]["iteration"] = 3
    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(whiteboard, current_generation=3)


def test_whiteboard_rejects_excess_count_and_origin_drift() -> None:
    too_many = _whiteboard() + [
        {
            "iteration": iteration,
            "direction": "decrease",
            "magnitude": "medium",
            "result": "fail",
            "delta_pct": None,
        }
        for iteration in (2, 3)
    ]
    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(too_many, current_generation=3)

    with pytest.raises(P.PayloadValidationError):
        P.validate_whiteboard(
            _whiteboard(),
            current_generation=2,
            expected_origin=[{**_whiteboard()[0], "result": "fail"}],
        )


def test_planner_generation_one_preserves_existing_key_set() -> None:
    payload = {
        **_common(generation=1),
        "current_perf": _null_perf(),
        "leading_indicators": {
            "contention_level": "high",
            "cache_miss_rate_pct": None,
            "IPC_overall": None,
        },
        "whiteboard": [],
    }
    P.validate_planner_payload(
        payload,
        expected_workload="ycsb-a",
        expected_generation=1,
        expected_workload_descriptor=_descriptor(),
        expected_descriptor_binding=_binding(),
        expected_whiteboard_origin=[],
        expected_current_perf=_null_perf(),
        expected_leading_indicators=_null_leading(),
        expected_critic_feedback=None,
        payload_allowlist_sha256=ALLOWLIST_SHA256,
    )
    assert "critic_feedback" not in payload


def test_planner_rejects_critic_projection_identity_drift() -> None:
    projection = dict(P.apply_critic_feedback(
        _critic(), source_metrics=_source_metrics(), source_generation=1,
    ).planner_projection)
    payload = _planner_payload(projection)
    payload["critic_feedback"]["source_generation"] = 2
    with pytest.raises(P.PayloadValidationError):
        _validate_planner(payload, projection)


def test_coder_requires_exact_three_field_planner_direction() -> None:
    snapshot = P.snapshot_gating_spec(GATING_SPEC)
    payload = _coder_payload()
    payload["planner_direction"]["justification"] = "hidden mechanism"
    with pytest.raises(P.PayloadValidationError):
        _validate_coder(payload, snapshot)

    payload = _coder_payload()
    payload["planner_direction"]["axis"] = "other-axis"
    with pytest.raises(P.PayloadValidationError):
        _validate_coder(payload, snapshot)


def test_gating_spec_snapshot_is_frozen_and_reused_across_workloads() -> None:
    snapshot = P.snapshot_gating_spec(GATING_SPEC)
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.text = "changed"

    _validate_coder(_coder_payload(workload="ycsb-a"), snapshot)
    workload_b = _coder_payload(workload="ycsb-b")
    workload_b["gating_spec"] = GATING_SPEC + " throughput=123"
    with pytest.raises(P.GatingSpecError):
        _validate_coder(workload_b, snapshot)


@pytest.mark.parametrize("gating_spec", [b"bytes", 1, True, None])
def test_gating_spec_snapshot_requires_exact_str(gating_spec) -> None:
    with pytest.raises(P.GatingSpecError):
        P.snapshot_gating_spec(gating_spec)


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
