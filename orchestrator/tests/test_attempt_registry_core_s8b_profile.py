"""Drive the domain-independent attempt-registry core with the 8b profile."""
from __future__ import annotations

import ast
import hashlib
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from orchestrator.campaign import attempt_registry_core as core
from orchestrator.campaign import s8b_attempt_profile as s8b
from orchestrator.campaign import trial_registry as R


_FREEZE = "1" * 64
_PROTOCOL = "2" * 64
_SCHEDULE = "3" * 64
_MANIFEST = "4" * 64
_RUN_START = "5" * 64
_POLICY = "6" * 64
_EXTERNAL = "7" * 64
_RAW = "8" * 64
_REPORT = "9" * 64
_OBSERVATION = "a" * 64
_CONTENT = "b" * 40
_EFFECTIVE = "c" * 40
_PROCESS = {
    "pid": 1234,
    "starttime": "s8b-profile-test-start",
    "execution_uuid": "s8b-profile-test-execution",
}
_BINDING = s8b.S8BAttemptBinding(
    freeze_sha256=_FREEZE,
    protocol_sha256=_PROTOCOL,
    schedule_sha256=_SCHEDULE,
)

_FACADE_NAMES = frozenset({
    "create_attempt_registry_genesis",
    "load_attempt_registry",
    "reserve_attempt_slot",
    "classify_attempt",
    "begin_attempt_observation",
    "record_attempt_terminal",
})


def _slot(
    repetition: int,
    attempt_ordinal: int,
    *,
    freeze_holdout_key: str = "holdout-a",
    configuration_id: str = "configuration-a",
) -> s8b.S8BAttemptSlot:
    identity = {
        "freeze_holdout_key": freeze_holdout_key,
        "configuration_id": configuration_id,
        "repetition": repetition,
        "attempt_ordinal": attempt_ordinal,
    }
    return s8b.S8BAttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )


def _profile(*, budget: int = 32) -> core.DomainProfile[Any, Any]:
    return s8b.make_s8b_domain_profile(
        max_consumptions_per_budget_key=budget,
    )


def _genesis(
    profile: core.DomainProfile[Any, Any],
    slots: Sequence[s8b.S8BAttemptSlot],
) -> core.RegistryRows:
    return core.create_attempt_registry_genesis(
        profile=profile,
        freeze_id=_FREEZE,
        manifest_path=PurePosixPath("output/s8b-freeze/holdout_freeze.json"),
        manifest_sha256=_MANIFEST,
        slots=slots,
        binding=_BINDING,
    )


def _reserve(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot: s8b.S8BAttemptSlot,
) -> core.RegistryRows:
    return core.reserve_attempt_slot(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=_BINDING,
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-23T00:00:00+00:00",
    )


def _classify(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot: s8b.S8BAttemptSlot,
    reason: str | None,
) -> core.RegistryRows:
    digest = core.capability_digest(
        profile=profile,
        schema_version=profile.schema.current,
        freeze_id=_FREEZE,
        slot=slot,
        binding=_BINDING,
    )
    candidate, _receipt = core.classify_attempt(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=_BINDING,
        capability_digest_sha256=digest,
        pre_observation_failure_reason=reason,
        authority_id="s8b-profile-test-authority",
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=_EXTERNAL,
        classified_at="2026-08-23T00:00:01+00:00",
    )
    return candidate


def _terminal(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot: s8b.S8BAttemptSlot,
    status: str,
    failure_reason: str | None,
    report_sha256: str | None = None,
    observation_sha256: str | None = None,
    primary_value: object = None,
) -> core.RegistryRows:
    return core.record_attempt_terminal(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=_BINDING,
        terminal_status=status,
        raw_output_sha256=_RAW,
        report_sha256=report_sha256,
        observation_sha256=observation_sha256,
        primary_value=primary_value,
        failure_reason=failure_reason,
        finished_at="2026-08-23T00:00:02+00:00",
    )


def _assert_core_rejection(
    expected: str,
    operation: Callable[[], object],
) -> None:
    with pytest.raises(core.AttemptRegistryCoreError) as caught:
        operation()
    assert str(caught.value) == expected


def _registry_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(core.canonical_json_bytes(row) + b"\n" for row in rows)


def test_s8b_profile_closes_slot_binding_budget_and_reason_policy() -> None:
    profile = _profile(budget=2)
    first = _slot(0, 0)
    other_repetition = _slot(1, 0)

    assert profile.retryable_reasons == frozenset()
    assert s8b.S8B_RETRYABLE_FAILURE_REASONS == frozenset()
    assert profile.transition_policy.require_previous_terminal
    assert profile.transition_policy.forbid_retry_after_observation
    assert profile.transition_policy.require_terminal_reason_equals_classification
    assert profile.slot_codec.slot_id(first) == (
        "holdout-a", "configuration-a", 0, 0,
    )
    assert profile.slot_codec.series_key(first) == (
        "holdout-a", "configuration-a", 0,
    )
    budget_key = profile.transition_policy.budget_key
    assert budget_key is not None
    assert budget_key(first) == budget_key(other_repetition) == (
        "holdout-a", "configuration-a",
    )
    assert profile.slot_codec.parse(
        profile.slot_codec.to_json(first), label="slot",
    ) == first
    assert profile.binding_codec.parse(
        profile.binding_codec.to_event_fields(_BINDING), label="binding",
    ) == _BINDING

    rows = _genesis(profile, [first, other_repetition])
    assert rows[0]["root_path"] == (
        f"floor-attempt-registries/{_FREEZE}/registry.jsonl"
    )
    assert rows[0]["max_consumptions_per_budget_key"] == 2

    invalid = {**profile.slot_codec.to_json(first), "campaign_run_id": "forbidden"}
    _assert_core_rejection(
        "[attempt-registry-schema] slot exact keys differ",
        lambda: profile.slot_codec.parse(invalid, label="slot"),
    )
    _assert_core_rejection(
        "[attempt-registry-profile] 8b cell consumption budget is invalid",
        lambda: s8b.make_s8b_domain_profile(
            max_consumptions_per_budget_key=-1,
        ),
    )


def test_preallocation_accepts_a_genesis_slot_and_rejects_an_absent_slot() -> None:
    profile = _profile()
    declared = _slot(0, 0)
    rows = _genesis(profile, [declared])

    accepted = _reserve(rows, profile=profile, slot=declared)
    assert [row["event"] for row in accepted] == [
        "freeze", "start", "pre-observation-seal",
    ]

    absent = _slot(1, 0)
    _assert_core_rejection(
        "[attempt-slot] slot_id was not declared by genesis",
        lambda: _reserve(rows, profile=profile, slot=absent),
    )


def test_series_order_accepts_first_slot_and_rejects_skip_and_empty_retry_set() -> None:
    profile = _profile()
    first = _slot(0, 0)
    next_slot = _slot(0, 1)
    rows = _genesis(profile, [first, next_slot])

    started = _reserve(rows, profile=profile, slot=first)
    assert started[-2]["attempt_ordinal"] == 0
    _assert_core_rejection(
        "[attempt-slot-order] only the next slot after a completed "
        "retryable failure may start",
        lambda: _reserve(rows, profile=profile, slot=next_slot),
    )

    classified = _classify(
        started, profile=profile, slot=first, reason="scheduler-timeout",
    )
    terminal = _terminal(
        classified,
        profile=profile,
        slot=first,
        status="terminal-failure",
        failure_reason="scheduler-timeout",
    )
    assert terminal[-1]["terminal_status"] == "terminal-failure"
    _assert_core_rejection(
        "[attempt-slot-order] a slot after a non-retryable outcome cannot be consumed",
        lambda: _reserve(terminal, profile=profile, slot=next_slot),
    )

    # R-c is unresolved: claiming retryability must fail against the exact
    # empty closed set, rather than silently inventing an 8b retry reason.
    _assert_core_rejection(
        "[attempt-null-matrix] attempt registry line 5 "
        "retryable-failure null matrix differs",
        lambda: _terminal(
            classified,
            profile=profile,
            slot=first,
            status="retryable-failure",
            failure_reason="scheduler-timeout",
            report_sha256=_REPORT,
        ),
    )


def test_budget_is_cell_wide_and_does_not_reset_for_each_repetition() -> None:
    profile = _profile(budget=2)
    repetitions = [_slot(index, 0) for index in range(3)]
    rows = _genesis(profile, repetitions)

    rows = _reserve(rows, profile=profile, slot=repetitions[0])
    rows = _reserve(rows, profile=profile, slot=repetitions[1])
    assert [
        row["repetition"] for row in rows if row["event"] == "start"
    ] == [0, 1]

    _assert_core_rejection(
        "[attempt-slot-order] attempt consumption exceeds the profile budget",
        lambda: _reserve(rows, profile=profile, slot=repetitions[2]),
    )


def test_observation_lifecycle_is_accepted_but_cannot_open_a_later_slot() -> None:
    profile = _profile()
    first = _slot(0, 0)
    next_slot = _slot(0, 1)
    rows = _genesis(profile, [first, next_slot])
    rows = _reserve(rows, profile=profile, slot=first)
    rows = _classify(rows, profile=profile, slot=first, reason=None)
    rows = core.begin_attempt_observation(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(first),
    )
    rows = _terminal(
        rows,
        profile=profile,
        slot=first,
        status="observed",
        failure_reason=None,
        report_sha256=_REPORT,
        observation_sha256=_OBSERVATION,
        primary_value={"throughput": 1.0},
    )
    assert rows[-1]["observation_start_event_sha256"] == rows[-2]["event_sha256"]

    _assert_core_rejection(
        "[attempt-slot-order] a slot after a non-retryable outcome cannot be consumed",
        lambda: _reserve(rows, profile=profile, slot=next_slot),
    )


def test_known_event_round_trip_passes_and_unknown_event_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _genesis(profile, [slot])
    assert core.load_attempt_registry(
        _registry_bytes(rows), profile=profile,
    ) == rows

    unknown = core.chained_event_row(
        {
            "schema_version": profile.schema.current,
            "event": "recovery",
        },
        event_index=1,
        previous_event_sha256=rows[0]["event_sha256"],
    )
    _assert_core_rejection(
        "[attempt-registry-schema] attempt registry line 2.event is unknown",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows, unknown)), profile=profile,
        ),
    )


def _s8c_slot() -> dict[str, object]:
    identity = {
        "trial_id": "s8b-policy-control",
        "arm": "on",
        "holdout": "H1",
        "campaign_id": "s8b-policy-control-campaign",
        "replicate_index": 0,
        "attempt_index": 0,
    }
    return {
        "slot_id": "s8b-policy-control-r0-a0",
        **identity,
        "schedule_row_sha256": hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    }


def _s8c_terminal_with_reason_mismatch(
    *, classification_reason: str, terminal_reason: str,
) -> core.RegistryRows:
    profile = R._S8C_ATTEMPT_PROFILE
    freeze_id = "s8b-policy-control-freeze"
    slot = _s8c_slot()
    binding = (_CONTENT, _EFFECTIVE)
    rows = core.create_attempt_registry_genesis(
        profile=profile,
        freeze_id=freeze_id,
        manifest_path=PurePosixPath("manifest.json"),
        manifest_sha256=_MANIFEST,
        slots=[slot],
    )
    rows = core.reserve_attempt_slot(
        rows,
        profile=profile,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-23T00:00:00+00:00",
    )
    digest = core.capability_digest(
        profile=profile,
        schema_version=profile.schema.current,
        freeze_id=freeze_id,
        slot=profile.slot_codec.parse(slot, label="slot"),
        binding=binding,
    )
    rows, _receipt = core.classify_attempt(
        rows,
        profile=profile,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        capability_digest_sha256=digest,
        pre_observation_failure_reason=classification_reason,
        authority_id="s8b-policy-control-authority",
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=_EXTERNAL,
        classified_at="2026-08-23T00:00:01+00:00",
    )
    return core.record_attempt_terminal(
        rows,
        profile=profile,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        terminal_status="terminal-failure",
        raw_output_sha256=_RAW,
        report_sha256=None,
        observation_sha256=None,
        primary_value=None,
        failure_reason=terminal_reason,
        finished_at="2026-08-23T00:00:02+00:00",
    )


def test_strict_8b_reason_match_rejects_input_that_8c_still_accepts() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    classification_reason = "classified-terminal-failure"
    terminal_reason = "different-terminal-failure"

    matching = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason=classification_reason,
    )
    matching = _terminal(
        matching,
        profile=profile,
        slot=slot,
        status="terminal-failure",
        failure_reason=classification_reason,
    )
    assert matching[-1]["failure_reason"] == classification_reason

    mismatching = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason=classification_reason,
    )
    _assert_core_rejection(
        "[attempt-classification] terminal failure reason differs from classification",
        lambda: _terminal(
            mismatching,
            profile=profile,
            slot=slot,
            status="terminal-failure",
            failure_reason=terminal_reason,
        ),
    )

    accepted_by_8c = _s8c_terminal_with_reason_mismatch(
        classification_reason=classification_reason,
        terminal_reason=terminal_reason,
    )
    assert (
        R._S8C_ATTEMPT_PROFILE.transition_policy
        .require_terminal_reason_equals_classification
        is False
    )
    assert accepted_by_8c[-1]["failure_reason"] == terminal_reason
    assert (
        accepted_by_8c[-1]["pre_observation_failure_reason_echo"]
        == classification_reason
    )


def _target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {
            name for element in target.elts for name in _target_names(element)
        }
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return set()


def _non_function_bindings(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Assign):
        return {
            name for target in statement.targets for name in _target_names(target)
        }
    if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        return _target_names(statement.target)
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        return {
            alias.asname or alias.name.split(".", 1)[0]
            for alias in statement.names
        }
    if isinstance(statement, ast.ClassDef):
        return {statement.name}
    return set()


def _assert_six_facades_are_unrebound(source: str) -> None:
    tree = ast.parse(source)
    definitions = [
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name in _FACADE_NAMES
    ]
    missing = sorted(_FACADE_NAMES - set(definitions))
    duplicates = sorted({name for name in definitions if definitions.count(name) != 1})
    rebound = sorted(
        _FACADE_NAMES.intersection(
            name
            for statement in tree.body
            for name in _non_function_bindings(statement)
        )
    )
    if missing:
        raise AssertionError(f"facade definitions are missing: {', '.join(missing)}")
    if duplicates:
        raise AssertionError(f"top-level facade definitions repeat: {', '.join(duplicates)}")
    if rebound:
        raise AssertionError(
            f"top-level facade rebinding is forbidden: {', '.join(rebound)}"
        )


def test_trial_registry_six_facades_have_no_top_level_rebinding() -> None:
    _assert_six_facades_are_unrebound(
        Path(R.__file__).read_text(encoding="utf-8")
    )


def test_facade_rebinding_guard_rejects_c03_blind_synthetic_source() -> None:
    definitions = "\n".join(
        f"def {name}():\n    pass" for name in sorted(_FACADE_NAMES)
    )
    source = (
        f"{definitions}\n"
        "create_attempt_registry_genesis = malicious_replacement\n"
    )
    assert any(
        isinstance(statement, ast.FunctionDef)
        and statement.name == "create_attempt_registry_genesis"
        for statement in ast.parse(source).body
    )
    with pytest.raises(AssertionError) as caught:
        _assert_six_facades_are_unrebound(source)
    assert str(caught.value) == (
        "top-level facade rebinding is forbidden: "
        "create_attempt_registry_genesis"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
