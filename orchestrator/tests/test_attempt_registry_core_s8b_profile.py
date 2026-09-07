"""Drive the domain-independent attempt-registry core with the 8b profile."""
from __future__ import annotations

import ast
import hashlib
import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import fields, replace
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
_ACCOUNTING_RECORD = "d" * 64
_CONTENT = "b" * 40
_EFFECTIVE = "c" * 40
_RECOVERY_AUTHORITY = "s8b-profile-test-scheduler-authority"
_RECOVERER = {
    "pid": 5678,
    "starttime": "s8b-profile-test-recoverer-start",
    "execution_uuid": "s8b-profile-test-recoverer-execution",
}
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
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )


def _genesis(
    profile: core.DomainProfile[Any, Any],
    slots: Sequence[s8b.S8BAttemptSlot],
) -> core.RegistryRows:
    return core.create_attempt_registry_genesis(
        profile=profile,
        slots=slots,
        binding=_BINDING,
    )


def _reserve(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot: s8b.S8BAttemptSlot,
    process_identity: Mapping[str, Any] | None = None,
) -> core.RegistryRows:
    return core.reserve_attempt_slot(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=_BINDING,
        run_start_receipt_sha256=_RUN_START,
        process_identity=(
            _PROCESS if process_identity is None else process_identity
        ),
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
    measurement_retry_reason: str | None = None,
    terminal_evidence_sha256: str | None = None,
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
        measurement_retry_reason=measurement_retry_reason,
        terminal_evidence_sha256=terminal_evidence_sha256,
        finished_at="2026-08-23T00:00:02+00:00",
    )


def _start_for_slot(
    rows: Sequence[Mapping[str, Any]],
    *,
    slot: s8b.S8BAttemptSlot,
) -> Mapping[str, Any]:
    starts = [
        row for row in rows
        if row.get("event") == "start"
        and row.get("freeze_holdout_key") == slot.freeze_holdout_key
        and row.get("configuration_id") == slot.configuration_id
        and row.get("repetition") == slot.repetition
        and row.get("attempt_ordinal") == slot.attempt_ordinal
    ]
    assert len(starts) == 1
    return starts[0]


def _recovery_receipt(
    rows: Sequence[Mapping[str, Any]],
    *,
    slot: s8b.S8BAttemptSlot,
    reason: str,
) -> dict[str, Any]:
    start = _start_for_slot(rows, slot=slot)
    return {
        "schema_version": s8b.S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
        "event": s8b.S8B_RECOVERY_RECEIPT_EVENT,
        "source": s8b.S8B_RECOVERY_RECEIPT_SOURCE,
        "scheduler_request_id": "nqsv-request-1234",
        "target_start_event_sha256": start["event_sha256"],
        "raw_scheduler_accounting_record_sha256": _ACCOUNTING_RECORD,
        "authority_id": _RECOVERY_AUTHORITY,
        "authority_policy_sha256": _POLICY,
        "failure_reason": reason,
        "collected_at": "2026-08-23T00:00:03+00:00",
    }


def _recover(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot: s8b.S8BAttemptSlot,
    reason: str = "scheduler_external_interruption",
    receipt: Mapping[str, Any] | None = None,
    recoverer_process_identity: Mapping[str, Any] | None = None,
) -> core.RegistryRows:
    scheduler_receipt = (
        _recovery_receipt(rows, slot=slot, reason=reason)
        if receipt is None else receipt
    )
    return core.record_attempt_recovery(
        rows,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=_BINDING,
        scheduler_accounting_receipt=scheduler_receipt,
        recoverer_process_identity=(
            _RECOVERER
            if recoverer_process_identity is None
            else recoverer_process_identity
        ),
        recovered_at="2026-08-23T00:00:04+00:00",
    )


def _receipt_sha256(receipt: Mapping[str, Any]) -> str:
    return hashlib.sha256(core.canonical_json_bytes(receipt) + b"\n").hexdigest()


def _assert_core_rejection(
    expected: str,
    operation: Callable[[], object],
) -> None:
    with pytest.raises(core.AttemptRegistryCoreError) as caught:
        operation()
    assert str(caught.value) == expected


def _registry_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(core.canonical_json_bytes(row) + b"\n" for row in rows)


def _rechain_after(
    rows: Sequence[Mapping[str, Any]], row: Mapping[str, Any],
) -> core.RegistryRows:
    payload = {
        key: value
        for key, value in row.items()
        if key not in {
            "event_index", "previous_event_sha256", "event_sha256",
        }
    }
    rechained = core.chained_event_row(
        payload,
        event_index=len(rows),
        previous_event_sha256=rows[-1]["event_sha256"],
    )
    return tuple(dict(existing) for existing in rows) + (rechained,)


def _expected_recovery_policy_sha256(
    profile: core.DomainProfile[Any, Any],
) -> str:
    policy = profile.recovery_policy
    assert policy is not None
    payload = {
        "receipt_schema_version": policy.receipt_schema_version,
        "receipt_event": policy.receipt_event,
        "receipt_source": policy.receipt_source,
        "authority_id": policy.authority_id,
        "authority_policy_sha256": policy.authority_policy_sha256,
        "failure_reasons": sorted(policy.failure_reasons),
        "enabled": profile.transition_policy.allow_recovered_abandonment,
    }
    return hashlib.sha256(core.canonical_json_bytes(payload)).hexdigest()


def test_s8b_profile_closes_slot_binding_budget_and_reason_policy() -> None:
    profile = _profile(budget=2)
    first = _slot(0, 0)
    other_repetition = _slot(1, 0)

    assert profile.retryable_reasons == frozenset()
    assert s8b.S8B_RETRYABLE_FAILURE_REASONS == frozenset()
    assert s8b.S8B_RECOVERY_FAILURE_REASONS == frozenset({
        "node_failure", "scheduler_external_interruption",
    })
    assert profile.recovery_policy is not None
    assert (
        profile.recovery_policy.failure_reasons
        == s8b.S8B_RECOVERY_FAILURE_REASONS
    )
    assert profile.transition_policy.require_previous_terminal
    assert profile.transition_policy.forbid_retry_after_observation
    assert profile.transition_policy.allow_recovered_abandonment
    assert profile.transition_policy.require_terminal_reason_equals_classification
    event_keys = profile.schema.event_keys[profile.schema.current]
    assert event_keys["start"].isdisjoint({
        "generation",
        "fence_generation",
        "predecessor_outcome_event_sha256",
        "registry_head_sha256",
    })
    assert event_keys["recovery"].isdisjoint({
        "raw_output_sha256",
        "report_sha256",
        "observation_sha256",
        "primary_value",
        "terminal_status",
    })
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
    assert rows[0]["recovery_policy_sha256"] == (
        _expected_recovery_policy_sha256(profile)
    )
    assert core.load_attempt_registry(
        _registry_bytes(rows), profile=profile,
    ) == rows

    invalid = {**profile.slot_codec.to_json(first), "campaign_run_id": "forbidden"}
    _assert_core_rejection(
        "[attempt-registry-schema] slot exact keys differ",
        lambda: profile.slot_codec.parse(invalid, label="slot"),
    )
    _assert_core_rejection(
        "[attempt-registry-profile] 8b cell consumption budget is invalid",
        lambda: s8b.make_s8b_domain_profile(
            max_consumptions_per_budget_key=-1,
            recovery_authority_id=_RECOVERY_AUTHORITY,
            recovery_authority_policy_sha256=_POLICY,
        ),
    )


def test_s8b_genesis_accepts_omitted_manifest_fields_and_rejects_undeclared_value(
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = core.create_attempt_registry_genesis(
        profile=profile,
        slots=[slot],
        binding=_BINDING,
    )

    assert {"freeze_id", "manifest_path", "manifest_sha256"}.isdisjoint(rows[0])
    assert core.load_attempt_registry(
        _registry_bytes(rows), profile=profile, expected_binding=_BINDING,
    ) == rows
    _assert_core_rejection(
        "[attempt-registry-genesis] manifest_sha256 is not declared by the "
        "domain profile",
        lambda: core.create_attempt_registry_genesis(
            profile=profile,
            manifest_sha256=_MANIFEST,
            slots=[slot],
            binding=_BINDING,
        ),
    )


@pytest.mark.parametrize(
    "declared_manifest_keys",
    (
        frozenset({"freeze_id"}),
        frozenset({"manifest_path", "manifest_sha256"}),
    ),
    ids=("one-of-three", "two-of-three"),
)
def test_genesis_rejects_partial_manifest_key_profiles_early(
    declared_manifest_keys: frozenset[str],
) -> None:
    base = _profile()
    version = base.schema.current
    partial = replace(
        base,
        schema=core.SchemaProfile(
            current=version,
            readable=base.schema.readable,
            genesis_keys={
                version: (
                    base.schema.genesis_keys[version]
                    | declared_manifest_keys
                ),
            },
            event_keys=base.schema.event_keys,
            receipt_keys=base.schema.receipt_keys,
        ),
    )

    _assert_core_rejection(
        "[attempt-registry-profile] genesis must declare either all or none "
        "of the manifest keys",
        lambda: core.create_attempt_registry_genesis(
            profile=partial,
            slots=[_slot(0, 0)],
            binding=_BINDING,
        ),
    )


def test_genesis_rejects_binding_codec_overlap_with_manifest_keys() -> None:
    base = R._S8C_ATTEMPT_PROFILE

    class OverlappingBindingCodec:
        event_keys = frozenset({"manifest_sha256"})

        def parse(self, row: Mapping[str, object], *, label: str) -> str:
            del label
            return str(row["manifest_sha256"])

        def to_event_fields(self, binding: str) -> dict[str, object]:
            return {"manifest_sha256": binding}

        def identity(self, binding: str) -> str:
            return binding

        def capability_payload(
            self, *, slot: object, binding: str, freeze_id: str,
        ) -> dict[str, object]:
            del slot, freeze_id
            return {"manifest_sha256": binding}

    overlapping = replace(base, binding_codec=OverlappingBindingCodec())
    _assert_core_rejection(
        "[attempt-registry-profile] binding codec overlaps manifest genesis keys",
        lambda: core.create_attempt_registry_genesis(
            profile=overlapping,
            freeze_id="s8b-policy-control-freeze",
            manifest_path=PurePosixPath("manifest.json"),
            manifest_sha256=_MANIFEST,
            slots=[_s8c_slot()],
            binding="e" * 64,
        ),
    )


def test_zero_and_three_manifest_key_profiles_remain_accepted() -> None:
    rows_8b = core.create_attempt_registry_genesis(
        profile=_profile(), slots=[_slot(0, 0)], binding=_BINDING,
    )
    assert "manifest_sha256" not in rows_8b[0]

    rows_8c = core.create_attempt_registry_genesis(
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id="s8b-policy-control-freeze",
        manifest_path=PurePosixPath("manifest.json"),
        manifest_sha256=_MANIFEST,
        slots=[_s8c_slot()],
    )
    assert rows_8c[0]["manifest_sha256"] == _MANIFEST


@pytest.mark.parametrize(
    ("omitted", "expected_rejection"),
    (
        (
            "freeze_id",
            "[attempt-registry-schema] freeze_id is not a bounded non-empty string",
        ),
        (
            "manifest_sha256",
            "[attempt-registry-schema] manifest_sha256 is not a SHA-256 digest",
        ),
        (
            "manifest_path",
            "[attempt-registry-genesis] manifest_path is required by the domain "
            "profile",
        ),
    ),
    ids=("freeze_id", "manifest_sha256", "manifest_path"),
)
def test_s8c_genesis_requires_manifest_contract_and_preserves_exact_row(
    omitted: str,
    expected_rejection: str,
) -> None:
    slot = _s8c_slot()
    arguments: dict[str, Any] = {
        "profile": R._S8C_ATTEMPT_PROFILE,
        "freeze_id": "s8b-policy-control-freeze",
        "manifest_path": PurePosixPath("manifest.json"),
        "manifest_sha256": _MANIFEST,
        "slots": [slot],
    }
    rows = core.create_attempt_registry_genesis(**arguments)

    assert rows[0] == {
        "schema_version": "p3-8c-attempt-registry/v3",
        "event": "freeze",
        "freeze_id": "s8b-policy-control-freeze",
        "manifest_path": "manifest.json",
        "manifest_sha256": "4" * 64,
        "root_path": "output/s8c-preregistration/attempt-registry.jsonl",
        "retryable_failure_reasons": [
            "launcher-failure", "node-failure", "preempted", "wall-timeout",
        ],
        "slots": [{
            "slot_id": "s8b-policy-control-r0-a0",
            "trial_id": "s8b-policy-control",
            "arm": "on",
            "holdout": "H1",
            "campaign_id": "s8b-policy-control-campaign",
            "prereg_generation": 13,
            "replicate_index": 0,
            "attempt_index": 0,
            "schedule_row_sha256": (
                "a33fa332404f536be10eef669ff091ffa8acbc229dd32d1ce181d9aee04a5e12"
            ),
        }],
        "event_index": 0,
        "previous_event_sha256": "0" * 64,
        "event_sha256": (
            "83e0db2035a3bce02b209fdaed365a49f487dda5dce24c1f9289dcd764321cb7"
        ),
    }
    assert core.load_attempt_registry(
        _registry_bytes(rows), profile=R._S8C_ATTEMPT_PROFILE,
    ) == rows

    incomplete = {key: value for key, value in arguments.items() if key != omitted}
    _assert_core_rejection(
        expected_rejection,
        lambda: core.create_attempt_registry_genesis(**incomplete),
    )


def test_genesis_rejects_freeze_id_that_differs_from_8b_binding() -> None:
    base = _profile()
    version = base.schema.current
    profile = replace(
        base,
        schema=core.SchemaProfile(
            current=version,
            readable=base.schema.readable,
            genesis_keys={
                version: base.schema.genesis_keys[version] | frozenset({
                    "freeze_id", "manifest_path", "manifest_sha256",
                }),
            },
            event_keys=base.schema.event_keys,
            receipt_keys=base.schema.receipt_keys,
        ),
        build_genesis_fields=lambda freeze_id, manifest_path, manifest_sha256: {
            "freeze_id": freeze_id,
            "manifest_path": manifest_path.as_posix(),
            "manifest_sha256": manifest_sha256,
        },
    )
    mismatched_binding = replace(_BINDING, freeze_sha256="d" * 64)

    _assert_core_rejection(
        "[attempt-binding] genesis freeze_id differs from requested freeze_id",
        lambda: core.create_attempt_registry_genesis(
            profile=profile,
            freeze_id=_FREEZE,
            manifest_path=PurePosixPath(
                "output/s8b-freeze/holdout_freeze.json"
            ),
            manifest_sha256=_MANIFEST,
            slots=[_slot(0, 0)],
            binding=mismatched_binding,
        ),
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("receipt_schema_version", "scheduler-accounting-receipt/v2"),
        ("receipt_event", "different-scheduler-event"),
        ("receipt_source", "different-accounting-source"),
        ("authority_id", "different-recovery-authority"),
        ("authority_policy_sha256", "e" * 64),
        (
            "failure_reasons",
            frozenset({
                "node_failure",
                "scheduler_external_interruption",
                "wall_timeout",
            }),
        ),
    ),
)
def test_genesis_rejects_recovery_history_under_a_different_policy_profile(
    field: str, replacement: object,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    policy = profile.recovery_policy
    assert policy is not None
    changed_profile = replace(
        profile,
        recovery_policy=replace(policy, **{field: replacement}),
    )

    _assert_core_rejection(
        "[attempt-registry-genesis] attempt registry genesis."
        "recovery_policy_sha256 differs from the current profile",
        lambda: core.load_attempt_registry(
            _registry_bytes(rows), profile=changed_profile,
        ),
    )


def test_genesis_rejects_recovery_history_when_enable_flag_changes() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    disabled_profile = replace(
        profile,
        transition_policy=replace(
            profile.transition_policy,
            allow_recovered_abandonment=False,
        ),
    )

    _assert_core_rejection(
        "[attempt-registry-genesis] attempt registry genesis."
        "recovery_policy_sha256 differs from the current profile",
        lambda: core.load_attempt_registry(
            _registry_bytes(rows), profile=disabled_profile,
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
        started, profile=profile, slot=first, reason="node_failure",
    )
    terminal = _terminal(
        classified,
        profile=profile,
        slot=first,
        status="terminal-failure",
        failure_reason="node_failure",
    )
    assert terminal[-1]["terminal_status"] == "terminal-failure"
    _assert_core_rejection(
        "[attempt-slot-order] a slot after a non-retryable outcome cannot be consumed",
        lambda: _reserve(terminal, profile=profile, slot=next_slot),
    )


def test_recovery_reason_does_not_bypass_ordinary_terminal_retryable_set() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    classified = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="node_failure",
    )

    _assert_core_rejection(
        "[attempt-null-matrix] attempt registry line 5 "
        "retryable-failure null matrix differs",
        lambda: _terminal(
            classified,
            profile=profile,
            slot=slot,
            status="retryable-failure",
            failure_reason="node_failure",
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


def test_retryable_terminal_after_observation_hits_only_observation_guard() -> None:
    official_profile = _profile()
    profile = replace(
        official_profile,
        retryable_reasons=frozenset({"scheduler-timeout"}),
    )
    first = _slot(0, 0)
    next_slot = _slot(0, 1)

    assert official_profile.retryable_reasons == frozenset()
    assert s8b.S8B_RETRYABLE_FAILURE_REASONS == frozenset()
    rows = _reserve(
        _genesis(profile, [first, next_slot]), profile=profile, slot=first,
    )
    rows = _classify(
        rows, profile=profile, slot=first, reason="scheduler-timeout",
    )
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
        status="retryable-failure",
        failure_reason="scheduler-timeout",
        report_sha256=_REPORT,
    )
    assert rows[-1]["terminal_status"] == "retryable-failure"
    assert rows[-1]["observation_start_event_sha256"] is not None

    _assert_core_rejection(
        "[attempt-slot-order] a retryable failure after observation cannot "
        "authorize a retry",
        lambda: _reserve(rows, profile=profile, slot=next_slot),
    )
    guard_disabled = replace(
        profile,
        transition_policy=replace(
            profile.transition_policy,
            forbid_retry_after_observation=False,
        ),
    )
    accepted = _reserve(rows, profile=guard_disabled, slot=next_slot)
    assert accepted[-2]["event"] == "start"
    assert accepted[-2]["attempt_ordinal"] == 1


@pytest.mark.parametrize(
    ("reason", "after_observation"),
    (
        pytest.param("node_failure", False, id="node-before-observation"),
        pytest.param(
            "scheduler_external_interruption",
            True,
            id="scheduler-interruption-after-observation",
        ),
    ),
)
def test_verified_recovery_closes_slot_and_opens_exact_next_ordinal(
    reason: str, after_observation: bool,
) -> None:
    profile = _profile()
    first = _slot(0, 0)
    next_slot = _slot(0, 1)
    rows = _reserve(
        _genesis(profile, [first, next_slot]), profile=profile, slot=first,
    )
    if after_observation:
        rows = _classify(rows, profile=profile, slot=first, reason=None)
        rows = core.begin_attempt_observation(
            rows,
            profile=profile,
            freeze_id=_FREEZE,
            slot_id=profile.slot_codec.slot_id(first),
        )

    rows = _recover(rows, profile=profile, slot=first, reason=reason)
    recovery = rows[-1]
    start = _start_for_slot(rows, slot=first)
    assert rows[0]["recovery_policy_sha256"] == (
        _expected_recovery_policy_sha256(profile)
    )
    assert recovery["event"] == "recovery"
    assert recovery["start_event_sha256"] == start["event_sha256"]
    assert recovery["recoverer_process_identity"] != start["process_identity"]
    assert recovery["failure_reason"] == reason
    assert recovery["scheduler_accounting_receipt"]["failure_reason"] == reason
    assert recovery["scheduler_accounting_receipt_sha256"] == _receipt_sha256(
        recovery["scheduler_accounting_receipt"]
    )
    assert frozenset(recovery).isdisjoint({
        "raw_output_sha256",
        "report_sha256",
        "observation_sha256",
        "primary_value",
        "terminal_status",
    })

    accepted = _reserve(rows, profile=profile, slot=next_slot)
    assert accepted[-2]["event"] == "start"
    assert accepted[-2]["attempt_ordinal"] == 1


@pytest.mark.parametrize(
    "reason",
    (
        "wall_timeout",
        "process_disappearance",
        "sigkill",
        "user_cancellation",
        "unregistered_scheduler_reason",
    ),
)
def test_recovery_receipt_rejects_every_reason_outside_exact_closed_set(
    reason: str,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    receipt = _recovery_receipt(rows, slot=slot, reason="node_failure")
    receipt["failure_reason"] = reason

    _assert_core_rejection(
        "[attempt-recovery-evidence] scheduler_accounting_receipt."
        "failure_reason is outside the exact closed set",
        lambda: _recover(
            rows, profile=profile, slot=slot, receipt=receipt,
        ),
    )


@pytest.mark.parametrize(
    "reason",
    (
        pytest.param([], id="array"),
        pytest.param({}, id="object"),
    ),
)
def test_recovery_receipt_rejects_non_string_reason_at_evidence_gate(
    reason: object,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = dict(rows[-1])
    receipt = dict(recovery["scheduler_accounting_receipt"])
    receipt["failure_reason"] = reason
    recovery["scheduler_accounting_receipt"] = receipt
    recovery["scheduler_accounting_receipt_sha256"] = _receipt_sha256(receipt)
    recovery["failure_reason"] = reason
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[attempt-recovery-evidence] attempt registry line 4."
        "scheduler_accounting_receipt."
        "failure_reason is outside the exact closed set",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("schema_version", "scheduler-accounting-receipt/v2"),
        ("event", "scheduler-finished"),
        ("source", "untrusted-accounting-source"),
        ("authority_id", "different-authority"),
        ("authority_policy_sha256", "e" * 64),
    ),
)
def test_recovery_receipt_rejects_pinned_authority_substitution(
    field: str, replacement: str,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    receipt = _recovery_receipt(rows, slot=slot, reason="node_failure")
    receipt[field] = replacement

    _assert_core_rejection(
        "[attempt-recovery-evidence] scheduler_accounting_receipt."
        f"{field} differs from the pinned authority policy",
        lambda: _recover(
            rows, profile=profile, slot=slot, receipt=receipt,
        ),
    )


@pytest.mark.parametrize("mode", ("missing", "extra"))
def test_recovery_receipt_rejects_non_exact_nested_keys(mode: str) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    receipt = _recovery_receipt(rows, slot=slot, reason="node_failure")
    if mode == "missing":
        del receipt["scheduler_request_id"]
        detail = "missing=['scheduler_request_id'], unknown=[]"
    else:
        receipt["performance_output_read"] = False
        detail = "missing=[], unknown=['performance_output_read']"

    _assert_core_rejection(
        "[attempt-recovery-evidence] scheduler_accounting_receipt key set "
        f"differs: {detail}",
        lambda: _recover(
            rows, profile=profile, slot=slot, receipt=receipt,
        ),
    )


def test_recovery_receipt_rejects_empty_scheduler_request_identity() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    receipt = _recovery_receipt(rows, slot=slot, reason="node_failure")
    receipt["scheduler_request_id"] = ""

    _assert_core_rejection(
        "[attempt-recovery-evidence] scheduler_accounting_receipt."
        "scheduler_request_id is invalid",
        lambda: _recover(
            rows, profile=profile, slot=slot, receipt=receipt,
        ),
    )


def test_recovery_rejects_nested_receipt_change_with_stale_digest() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = dict(rows[-1])
    receipt = dict(recovery["scheduler_accounting_receipt"])
    receipt["raw_scheduler_accounting_record_sha256"] = "e" * 64
    recovery["scheduler_accounting_receipt"] = receipt
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[attempt-recovery-evidence] attempt registry line 4."
        "scheduler_accounting_receipt_sha256 differs from the nested receipt",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


def test_recovery_rejects_receipt_targeting_a_different_start() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = dict(rows[-1])
    receipt = dict(recovery["scheduler_accounting_receipt"])
    receipt["target_start_event_sha256"] = "e" * 64
    recovery["scheduler_accounting_receipt"] = receipt
    recovery["scheduler_accounting_receipt_sha256"] = _receipt_sha256(receipt)
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[attempt-recovery-evidence] scheduler receipt targets a different "
        "start event",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


def test_recovery_rejects_replaced_row_start_fence() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = {**rows[-1], "start_event_sha256": "e" * 64}
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[attempt-recovery-fence] recovery start-event hash differs from the "
        "slot start",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


def test_recovery_rejects_reason_echo_substitution() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = {
        **rows[-1],
        "failure_reason": "node_failure",
    }
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[attempt-recovery-evidence] attempt registry line 4.failure_reason "
        "differs from the nested receipt",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


def test_recovery_rejects_same_process_identity_as_start_owner() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)

    _assert_core_rejection(
        "[attempt-recovery-fence] recoverer process identity matches the "
        "start owner",
        lambda: _recover(
            rows,
            profile=profile,
            slot=slot,
            recoverer_process_identity=_PROCESS,
        ),
    )


@pytest.mark.parametrize(
    ("owner_starttime", "recoverer_starttime"),
    (
        pytest.param(123, "123", id="integer-and-decimal-string"),
        pytest.param(123, "00123", id="integer-and-zero-padded-string"),
        pytest.param("123", "00123", id="decimal-and-zero-padded-string"),
    ),
)
def test_recovery_rejects_same_owner_with_equivalent_starttime_encoding(
    owner_starttime: int | str,
    recoverer_starttime: int | str,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    owner = {**_PROCESS, "starttime": owner_starttime}
    recoverer = {**_PROCESS, "starttime": recoverer_starttime}
    rows = _reserve(
        _genesis(profile, [slot]),
        profile=profile,
        slot=slot,
        process_identity=owner,
    )

    _assert_core_rejection(
        "[attempt-recovery-fence] recoverer process identity matches the "
        "start owner",
        lambda: _recover(
            rows,
            profile=profile,
            slot=slot,
            recoverer_process_identity=recoverer,
        ),
    )


def test_terminal_then_recovery_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="ordinary-terminal-reason",
    )
    rows = _terminal(
        rows,
        profile=profile,
        slot=slot,
        status="terminal-failure",
        failure_reason="ordinary-terminal-reason",
    )

    _assert_core_rejection(
        "[attempt-recovery-order] recovery follows terminal",
        lambda: _recover(rows, profile=profile, slot=slot),
    )


def test_recovery_then_terminal_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="ordinary-terminal-reason",
    )
    rows = _recover(rows, profile=profile, slot=slot)

    _assert_core_rejection(
        "[attempt-recovery-order] terminal follows verified recovery",
        lambda: _terminal(
            rows,
            profile=profile,
            slot=slot,
            status="terminal-failure",
            failure_reason="ordinary-terminal-reason",
        ),
    )


def test_recovery_then_classification_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )

    _assert_core_rejection(
        "[attempt-recovery-order] classification follows verified recovery",
        lambda: _classify(
            rows, profile=profile, slot=slot, reason=None,
        ),
    )


def test_recovery_then_observation_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason=None,
    )
    rows = _recover(rows, profile=profile, slot=slot)

    _assert_core_rejection(
        "[attempt-recovery-order] observation-start follows verified recovery",
        lambda: core.begin_attempt_observation(
            rows,
            profile=profile,
            freeze_id=_FREEZE,
            slot_id=profile.slot_codec.slot_id(slot),
        ),
    )


def test_second_recovery_is_rejected() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )

    _assert_core_rejection(
        "[attempt-recovery-order] slot has more than one recovery row",
        lambda: _recover(rows, profile=profile, slot=slot),
    )


def test_replay_rejects_rechained_terminal_then_recovery() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    classified = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="ordinary-terminal-reason",
    )
    terminal = _terminal(
        classified,
        profile=profile,
        slot=slot,
        status="terminal-failure",
        failure_reason="ordinary-terminal-reason",
    )
    recovery = _recover(classified, profile=profile, slot=slot)
    invalid = _rechain_after(terminal, recovery[-1])

    _assert_core_rejection(
        "[attempt-recovery-order] recovery follows terminal",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
    )


def test_replay_rejects_rechained_recovery_then_terminal() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    classified = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="ordinary-terminal-reason",
    )
    recovery = _recover(classified, profile=profile, slot=slot)
    terminal = _terminal(
        classified,
        profile=profile,
        slot=slot,
        status="terminal-failure",
        failure_reason="ordinary-terminal-reason",
    )
    invalid = _rechain_after(recovery, terminal[-1])

    _assert_core_rejection(
        "[attempt-recovery-order] terminal follows verified recovery",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
    )


def test_replay_rejects_rechained_recovery_then_classification() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    started = _reserve(
        _genesis(profile, [slot]), profile=profile, slot=slot,
    )
    recovery = _recover(started, profile=profile, slot=slot)
    classification = _classify(
        started, profile=profile, slot=slot, reason=None,
    )
    invalid = _rechain_after(recovery, classification[-1])

    _assert_core_rejection(
        "[attempt-recovery-order] classification follows verified recovery",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
    )


def test_replay_rejects_rechained_recovery_then_observation() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    classified = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason=None,
    )
    recovery = _recover(classified, profile=profile, slot=slot)
    observation = core.begin_attempt_observation(
        classified,
        profile=profile,
        freeze_id=_FREEZE,
        slot_id=profile.slot_codec.slot_id(slot),
    )
    invalid = _rechain_after(recovery, observation[-1])

    _assert_core_rejection(
        "[attempt-recovery-order] observation-start follows verified recovery",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
    )


def test_replay_rejects_rechained_second_recovery() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    recovery = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    invalid = _rechain_after(recovery, recovery[-1])

    _assert_core_rejection(
        "[attempt-recovery-order] slot has more than one recovery row",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
    )


@pytest.mark.parametrize(
    "forbidden_key",
    (
        "raw_output_sha256",
        "report_sha256",
        "observation_sha256",
        "terminal_status",
    ),
)
def test_recovery_row_rejects_terminal_or_value_field_injection(
    forbidden_key: str,
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _recover(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
    )
    recovery = {**rows[-1], forbidden_key: None}
    recovery["event_sha256"] = core.event_sha256(recovery)

    _assert_core_rejection(
        "[schema] attempt registry line 4 key set differs: missing=[], "
        f"unknown=['{forbidden_key}']",
        lambda: core.load_attempt_registry(
            _registry_bytes((*rows[:-1], recovery)), profile=profile,
        ),
    )


def test_recovery_row_rejects_primary_value_injection_at_exact_schema_gate() -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    start = _start_for_slot(rows, slot=slot)
    receipt = _recovery_receipt(rows, slot=slot, reason="node_failure")
    injected_recovery = {
        "schema_version": profile.schema.current,
        "event": "recovery",
        "freeze_holdout_key": start["freeze_holdout_key"],
        "configuration_id": start["configuration_id"],
        "repetition": start["repetition"],
        "attempt_ordinal": start["attempt_ordinal"],
        "freeze_sha256": start["freeze_sha256"],
        "protocol_sha256": start["protocol_sha256"],
        "schedule_sha256": start["schedule_sha256"],
        "start_event_sha256": start["event_sha256"],
        "scheduler_accounting_receipt": receipt,
        "scheduler_accounting_receipt_sha256": _receipt_sha256(receipt),
        "failure_reason": receipt["failure_reason"],
        "recoverer_process_identity": _RECOVERER,
        "recovered_at": "2026-08-23T00:00:04+00:00",
        "primary_value": None,
    }
    invalid = _rechain_after(rows, injected_recovery)

    _assert_core_rejection(
        "[schema] attempt registry line 4 key set differs: missing=[], "
        "unknown=['primary_value']",
        lambda: core.load_attempt_registry(
            _registry_bytes(invalid), profile=profile,
        ),
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
            "event": "unknown-lifecycle-event",
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


def test_profile_only_event_cannot_acquire_terminal_semantics() -> None:
    base = _profile()
    version = base.schema.current
    profile = replace(
        base,
        schema=core.SchemaProfile(
            current=version,
            readable=base.schema.readable,
            genesis_keys=base.schema.genesis_keys,
            event_keys={
                version: {
                    **base.schema.event_keys[version],
                    "profile-only-event": (
                        base.schema.event_keys[version]["terminal"]
                    ),
                },
            },
            receipt_keys=base.schema.receipt_keys,
        ),
    )
    slot = _slot(0, 0)
    terminal = _terminal(
        _classify(
            _reserve(
                _genesis(profile, [slot]), profile=profile, slot=slot,
            ),
            profile=profile,
            slot=slot,
            reason="terminal-reason",
        ),
        profile=profile,
        slot=slot,
        status="terminal-failure",
        failure_reason="terminal-reason",
    )

    assert core.load_attempt_registry(
        _registry_bytes(terminal), profile=profile,
    ) == terminal
    profile_only = {**terminal[-1], "event": "profile-only-event"}
    profile_only["event_sha256"] = core.event_sha256(profile_only)
    _assert_core_rejection(
        "[attempt-registry-semantic] attempt registry line 5.event has no "
        "core semantic handler",
        lambda: core.load_attempt_registry(
            _registry_bytes((*terminal[:-1], profile_only)), profile=profile,
        ),
    )


def test_schema_profile_mappings_are_deeply_immutable() -> None:
    for profile in (R._S8C_ATTEMPT_PROFILE, _profile()):
        version = profile.schema.current
        with pytest.raises(TypeError):
            profile.schema.event_keys[version]["recovery"] = frozenset()
        with pytest.raises(TypeError):
            profile.schema.event_keys[version] = {}
        with pytest.raises(TypeError):
            profile.schema.genesis_keys[version] = frozenset()
        if profile.schema.receipt_keys is not None:
            with pytest.raises(TypeError):
                profile.schema.receipt_keys[version] = frozenset()
    recovery_policy = _profile().recovery_policy
    assert recovery_policy is not None
    with pytest.raises(AttributeError):
        recovery_policy.failure_reasons = frozenset()


def _s8c_slot() -> dict[str, object]:
    identity = {
        "trial_id": "s8b-policy-control",
        "arm": "on",
        "holdout": "H1",
        "campaign_id": "s8b-policy-control-campaign",
        "prereg_generation": 13,
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


def _s8c_classified_rows(
    reason: str | None,
) -> tuple[core.RegistryRows, dict[str, object], tuple[str, str], str]:
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
        pre_observation_failure_reason=reason,
        authority_id="s8b-policy-control-authority",
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=_EXTERNAL,
        classified_at="2026-08-23T00:00:01+00:00",
    )
    return rows, slot, binding, freeze_id


def _s8c_terminal(
    rows: core.RegistryRows,
    *,
    profile: core.DomainProfile[Any, Any],
    slot: Mapping[str, object],
    binding: tuple[str, str],
    freeze_id: str,
    status: str,
    reason: str | None,
    begin_observation: bool = False,
) -> core.RegistryRows:
    if begin_observation:
        rows = core.begin_attempt_observation(
            rows,
            profile=profile,
            freeze_id=freeze_id,
            slot_id=slot["slot_id"],
        )
    return core.record_attempt_terminal(
        rows,
        profile=profile,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        terminal_status=status,
        raw_output_sha256=_RAW,
        report_sha256=(
            _REPORT
            if status in {"observed", "retryable-failure"}
            else None
        ),
        observation_sha256=_OBSERVATION if status == "observed" else None,
        primary_value=1.0 if status == "observed" else None,
        failure_reason=reason,
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


def test_s8c_formal_profile_differs_only_by_reason_equality_policy() -> None:
    compat = R._S8C_ATTEMPT_PROFILE
    formal = R._S8C_FORMAL_ATTEMPT_PROFILE

    assert formal is not compat
    for field in fields(core.DomainProfile):
        if field.name == "transition_policy":
            assert getattr(formal, field.name) is not getattr(compat, field.name)
        else:
            assert getattr(formal, field.name) is getattr(compat, field.name)
    changed_policy_fields = {
        field.name
        for field in fields(core.TransitionPolicy)
        if getattr(formal.transition_policy, field.name)
        != getattr(compat.transition_policy, field.name)
    }
    assert changed_policy_fields == {
        "require_terminal_reason_equals_classification"
    }
    assert (
        compat.transition_policy.require_terminal_reason_equals_classification
        is False
    )
    assert (
        formal.transition_policy.require_terminal_reason_equals_classification
        is True
    )


@pytest.mark.parametrize(
    ("classification_reason", "terminal_reason", "status", "observation"),
    [
        pytest.param("preempted", "preempted", "retryable-failure", False,
                     id="matching-retryable"),
        pytest.param(None, None, "observed", True, id="observed-none"),
        pytest.param(None, None, "not-consumed", False, id="not-consumed-none"),
    ],
)
def test_s8c_formal_profile_matching_terminals_keep_compat_bytes(
    classification_reason: str | None,
    terminal_reason: str | None,
    status: str,
    observation: bool,
) -> None:
    rows, slot, binding, freeze_id = _s8c_classified_rows(
        classification_reason
    )
    compat = _s8c_terminal(
        rows,
        profile=R._S8C_ATTEMPT_PROFILE,
        slot=slot,
        binding=binding,
        freeze_id=freeze_id,
        status=status,
        reason=terminal_reason,
        begin_observation=observation,
    )
    formal = _s8c_terminal(
        rows,
        profile=R._S8C_FORMAL_ATTEMPT_PROFILE,
        slot=slot,
        binding=binding,
        freeze_id=freeze_id,
        status=status,
        reason=terminal_reason,
        begin_observation=observation,
    )
    assert _registry_bytes(formal) == _registry_bytes(compat)


@pytest.mark.parametrize(
    ("classification_reason", "terminal_reason", "status"),
    [
        pytest.param(None, "preempted", "retryable-failure", id="none-to-preempted"),
        pytest.param(
            "preempted", "wall-timeout", "retryable-failure",
            id="preempted-to-wall-timeout",
        ),
        pytest.param(
            "classified-terminal-failure",
            "different-terminal-failure",
            "terminal-failure",
            id="terminal-failure-mismatch",
        ),
    ],
)
def test_s8c_formal_profile_rejects_reason_replacement_before_null_matrix(
    classification_reason: str | None,
    terminal_reason: str,
    status: str,
) -> None:
    rows, slot, binding, freeze_id = _s8c_classified_rows(
        classification_reason
    )
    _assert_core_rejection(
        "[attempt-classification] terminal failure reason differs from classification",
        lambda: _s8c_terminal(
            rows,
            profile=R._S8C_FORMAL_ATTEMPT_PROFILE,
            slot=slot,
            binding=binding,
            freeze_id=freeze_id,
            status=status,
            reason=terminal_reason,
        ),
    )


def test_s8c_formal_profile_rejects_mismatch_that_compat_replays() -> None:
    rows, slot, binding, freeze_id = _s8c_classified_rows(None)
    mismatching = _s8c_terminal(
        rows,
        profile=R._S8C_ATTEMPT_PROFILE,
        slot=slot,
        binding=binding,
        freeze_id=freeze_id,
        status="retryable-failure",
        reason="preempted",
    )
    payload = _registry_bytes(mismatching)

    assert core.load_attempt_registry(
        payload, profile=R._S8C_ATTEMPT_PROFILE,
    ) == mismatching
    _assert_core_rejection(
        "[attempt-classification] terminal failure reason differs from classification",
        lambda: core.load_attempt_registry(
            payload, profile=R._S8C_FORMAL_ATTEMPT_PROFILE,
        ),
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


def _called_names(node: ast.AST) -> set[str]:
    return {
        call.func.id if isinstance(call.func, ast.Name) else call.func.attr
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, (ast.Name, ast.Attribute))
    }


def _profile_name_for_call(function: ast.FunctionDef, target: str) -> str | None:
    matches = [
        call
        for call in ast.walk(function)
        if isinstance(call, ast.Call)
        and (
            (isinstance(call.func, ast.Name) and call.func.id == target)
            or (isinstance(call.func, ast.Attribute) and call.func.attr == target)
        )
    ]
    assert len(matches) == 1
    profile = next(
        (keyword.value for keyword in matches[0].keywords if keyword.arg == "profile"),
        None,
    )
    assert isinstance(profile, ast.Name)
    return profile.id


def test_s8c_formal_entrypoints_and_producers_are_strictly_routed() -> None:
    registry_tree = ast.parse(Path(R.__file__).read_text(encoding="utf-8"))
    registry_functions = {
        node.name: node
        for node in registry_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    expected_profiles = {
        "reserve_attempt_slot": ("_reserve_attempt_slot", "_S8C_ATTEMPT_PROFILE"),
        "reserve_formal_attempt_slot": (
            "_reserve_attempt_slot", "_S8C_FORMAL_ATTEMPT_PROFILE",
        ),
        "record_attempt_terminal": (
            "_record_attempt_terminal", "_S8C_ATTEMPT_PROFILE",
        ),
        "record_formal_attempt_terminal": (
            "_record_attempt_terminal", "_S8C_FORMAL_ATTEMPT_PROFILE",
        ),
        "assert_attempt_registry_acceptance": (
            "_assert_attempt_registry_acceptance", "_S8C_ATTEMPT_PROFILE",
        ),
        "assert_formal_attempt_registry_acceptance": (
            "_assert_attempt_registry_acceptance", "_S8C_FORMAL_ATTEMPT_PROFILE",
        ),
    }
    for name, (target, profile) in expected_profiles.items():
        assert _profile_name_for_call(registry_functions[name], target) == profile

    assert inspect.signature(R.reserve_formal_attempt_slot) == inspect.signature(
        R.reserve_attempt_slot
    )
    assert inspect.signature(R.record_formal_attempt_terminal) == inspect.signature(
        R.record_attempt_terminal
    )
    assert inspect.signature(
        R.assert_formal_attempt_registry_acceptance
    ) == inspect.signature(R.assert_attempt_registry_acceptance)

    producer_source = Path(
        R.__file__
    ).with_name("p3_autonomous_workload_trial.py").read_text(encoding="utf-8")
    producer_tree = ast.parse(producer_source)
    producer_functions = {
        node.name: node
        for node in producer_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    reserve_calls = _called_names(
        producer_functions["_reserve_registered_attempt_slot"]
    )
    terminal_calls = _called_names(
        producer_functions["_record_attempt_terminal_for_run"]
    )
    acceptance_calls = _called_names(
        registry_functions["assert_trial_registry_acceptance"]
    )
    assert "reserve_formal_attempt_slot" in reserve_calls
    assert "reserve_attempt_slot" not in reserve_calls
    assert "record_formal_attempt_terminal" in terminal_calls
    assert "record_attempt_terminal" not in terminal_calls
    assert "assert_formal_attempt_registry_acceptance" in acceptance_calls
    assert "assert_attempt_registry_acceptance" not in acceptance_calls


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
    assert "record_attempt_recovery" not in vars(R)


def test_facade_rebinding_guard_rejects_c03_blind_synthetic_source() -> None:
    definitions = "\n".join(
        f"def {name}():\n    pass" for name in sorted(_FACADE_NAMES)
    )
    source = (
        f"{definitions}\n"
        "create_attempt_registry_genesis = malicious_replacement\n"
    )
    with pytest.raises(AssertionError) as caught:
        _assert_six_facades_are_unrebound(source)
    assert str(caught.value) == (
        "top-level facade rebinding is forbidden: "
        "create_attempt_registry_genesis"
    )


@pytest.mark.parametrize("invalid_count", [True, -1, 1.5])
def test_seeded_budget_replay_rejects_invalid_counts_and_accepts_exact_limit(
    invalid_count: object,
) -> None:
    profile = _profile(budget=10)
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    payload = _registry_bytes(rows)
    budget_key = (slot.freeze_holdout_key, slot.configuration_id)

    _assert_core_rejection(
        "[attempt-slot-order] initial started budget count is invalid",
        lambda: core.load_attempt_registry_with_budget_counts(
            payload,
            profile=profile,
            expected_binding=_BINDING,
            initial_started_budget_counts={budget_key: invalid_count},
        ),
    )

    seed = {budget_key: 9}
    replayed, counts = core.load_attempt_registry_with_budget_counts(
        payload,
        profile=profile,
        expected_binding=_BINDING,
        initial_started_budget_counts=seed,
    )
    assert replayed == rows
    assert counts == {budget_key: 10}
    assert seed == {budget_key: 9}


def test_seeded_budget_replay_rejects_eleventh_start_and_old_apis_are_unchanged(
) -> None:
    profile = _profile(budget=10)
    slot = _slot(0, 0)
    rows = _reserve(_genesis(profile, [slot]), profile=profile, slot=slot)
    payload = _registry_bytes(rows)
    budget_key = (slot.freeze_holdout_key, slot.configuration_id)

    _assert_core_rejection(
        "[attempt-slot-order] attempt consumption exceeds the profile budget",
        lambda: core.load_attempt_registry_with_budget_counts(
            payload,
            profile=profile,
            initial_started_budget_counts={budget_key: 10},
        ),
    )
    assert core.assert_registry_rows(rows, profile=profile) == rows
    assert core.load_attempt_registry(payload, profile=profile) == rows
    assert "initial_started_budget_counts" not in inspect.signature(
        core.assert_registry_rows
    ).parameters
    assert "initial_started_budget_counts" not in inspect.signature(
        core.load_attempt_registry
    ).parameters

    _assert_core_rejection(
        "[attempt-slot-order] initial started budget counts are not a mapping",
        lambda: core.load_attempt_registry_with_budget_counts(
            payload,
            profile=profile,
            initial_started_budget_counts=[],  # type: ignore[arg-type]
        ),
    )
    empty_replay, empty_counts = core.load_attempt_registry_with_budget_counts(
        _registry_bytes(_genesis(profile, [slot])),
        profile=profile,
        initial_started_budget_counts={},
    )
    assert empty_replay[0]["event"] == "freeze"
    assert empty_counts == {}


@pytest.mark.parametrize(
    ("field", "invalid"),
    [("measurement_ordinal", True), ("attempt_ordinal", -1)],
)
def test_v2_slot_codec_rejects_invalid_ordinals_and_accepts_five_axis_identity(
    field: str,
    invalid: object,
) -> None:
    value = {
        "freeze_holdout_key": "holdout-a",
        "configuration_id": "configuration-a",
        "repetition": 2,
        "measurement_ordinal": 3,
        "attempt_ordinal": 4,
        "schedule_row_sha256": _SCHEDULE,
    }
    rejected = {**value, field: invalid}
    _assert_core_rejection(
        f"[attempt-registry-schema] v2 slot.{field} is not a nonnegative integer",
        lambda: s8b.S8B_V2_SLOT_CODEC.parse(rejected, label="v2 slot"),
    )

    slot = s8b.S8B_V2_SLOT_CODEC.parse(value, label="v2 slot")
    assert s8b.S8B_V2_SLOT_CODEC.to_json(slot) == value
    assert s8b.S8B_V2_SLOT_CODEC.slot_id(slot) == (
        "holdout-a", "configuration-a", 2, 3, 4,
    )
    assert s8b.S8B_V2_SLOT_CODEC.series_key(slot) == (
        "holdout-a", "configuration-a", 2, 3,
    )


def test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell() -> None:
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[attempt-registry-profile\] "
            r"8b cell consumption budget is invalid$"
        ),
    ):
        s8b.make_s8b_v2_domain_profile(
            max_consumptions_per_budget_key=-1,
            recovery_authority_id=_RECOVERY_AUTHORITY,
            recovery_authority_policy_sha256=_POLICY,
        )
    profile = s8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=10,
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )
    slot = s8b.S8BV2AttemptSlot(
        freeze_holdout_key="holdout-a",
        configuration_id="configuration-a",
        repetition=2,
        measurement_ordinal=3,
        attempt_ordinal=4,
        schedule_row_sha256=_SCHEDULE,
    )
    assert profile.schema is s8b.S8B_V2_SCHEMA_PROFILE
    assert profile.schema.current == "s8b-floor-attempt-registry/v2"
    assert profile.layout is s8b.S8B_V2_REGISTRY_LAYOUT
    assert profile.layout.registry_path.as_posix() == (
        "floor-attempt-registries/{freeze_sha256}/"
        "{protocol_sha256}/registry.jsonl"
    )
    expected_reasons = frozenset({
        "measurement_environment_conflict",
        "measurement_execution_unavailable",
        "measurement_sample_incomplete",
        "measurement_dispersion_exceeded",
    })
    assert profile.retryable_reasons == expected_reasons
    assert s8b.S8B_V2_RETRYABLE_FAILURE_REASONS == expected_reasons
    assert profile.retryable_reason_field == "measurement_retry_reason"
    assert profile.transition_policy.budget_key is not None
    assert profile.transition_policy.budget_key(slot) == (
        "holdout-a", "configuration-a",
    )
    event_keys = profile.schema.event_keys[profile.schema.current]
    assert all("measurement_ordinal" in keys for keys in event_keys.values())
    v1_event_keys = s8b.S8B_SCHEMA_PROFILE.event_keys[
        s8b.S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION
    ]
    assert event_keys["terminal"] - v1_event_keys["terminal"] == {
        "measurement_ordinal",
        "measurement_retry_reason",
        "terminal_evidence_sha256",
    }
    assert all(
        event_keys[event] - v1_event_keys[event] == {"measurement_ordinal"}
        for event in event_keys if event != "terminal"
    )
    assert s8b.S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION == (
        "s8b-floor-attempt-registry/v1"
    )
    assert s8b.S8B_RETRYABLE_FAILURE_REASONS == frozenset()


def test_profile_extension_fields_are_keyword_only_and_preserve_legacy_defaults(
) -> None:
    domain_field = next(
        field for field in fields(core.DomainProfile)
        if field.name == "terminal_row_validator"
    )
    reason_field = next(
        field for field in fields(core.DomainProfile)
        if field.name == "retryable_reason_field"
    )
    transition_field = next(
        field for field in fields(core.TransitionPolicy)
        if field.name == "retryable_terminal_opens_next_attempt"
    )
    assert domain_field.kw_only is True
    assert domain_field.default is None
    assert reason_field.kw_only is True
    assert reason_field.default == "failure_reason"
    assert transition_field.kw_only is True
    assert transition_field.default is True
    legacy = _profile()
    assert legacy.terminal_row_validator is None
    assert legacy.retryable_reason_field == "failure_reason"
    assert legacy.transition_policy.retryable_terminal_opens_next_attempt is True
    assert R._S8C_ATTEMPT_PROFILE.terminal_row_validator is None
    assert (
        R._S8C_ATTEMPT_PROFILE.transition_policy
        .retryable_terminal_opens_next_attempt
        is True
    )
    v2 = s8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=10,
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )
    assert v2.terminal_row_validator is not None
    assert v2.transition_policy.retryable_terminal_opens_next_attempt is False


def test_v2_terminal_failure_null_matrix_reads_measurement_reason_directly(
) -> None:
    """D1522/S1: name the lower branch hidden by the sealed E1 surface."""

    row = {
        "terminal_status": "terminal-failure",
        "raw_output_sha256": _RAW,
        "classification_receipt_sha256": _REPORT,
        "report_sha256": None,
        "observation_sha256": None,
        "primary_value": None,
        "failure_reason": "classification-echo",
        "measurement_retry_reason": "non-retryable-measurement-failure",
    }
    core._assert_null_matrix(
        row,
        retryable_reasons=s8b.S8B_V2_RETRYABLE_FAILURE_REASONS,
        retryable_reason_field="measurement_retry_reason",
        label="direct v2 terminal-failure",
    )
    mutated = {
        **row,
        "measurement_retry_reason": "measurement_execution_unavailable",
    }
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=r"^\[attempt-null-matrix\].*terminal-failure null matrix differs$",
    ):
        core._assert_null_matrix(
            mutated,
            retryable_reasons=s8b.S8B_V2_RETRYABLE_FAILURE_REASONS,
            retryable_reason_field="measurement_retry_reason",
            label="direct v2 terminal-failure",
        )


def test_v2_not_consumed_null_matrix_has_direct_positive_and_negative_pair(
) -> None:
    """D1522: E1 cannot produce this branch, so exercise it below E1."""

    accepted = {
        "terminal_status": "not-consumed",
        "raw_output_sha256": _RAW,
        "classification_receipt_sha256": _REPORT,
        "report_sha256": None,
        "observation_sha256": None,
        "primary_value": None,
        "failure_reason": None,
        "measurement_retry_reason": None,
    }
    core._assert_null_matrix(
        accepted,
        retryable_reasons=s8b.S8B_V2_RETRYABLE_FAILURE_REASONS,
        retryable_reason_field="measurement_retry_reason",
        label="direct v2 not-consumed",
    )
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=r"^\[attempt-null-matrix\].*not-consumed null matrix differs$",
    ):
        core._assert_null_matrix(
            {
                **accepted,
                "measurement_retry_reason": "measurement_sample_incomplete",
            },
            retryable_reasons=s8b.S8B_V2_RETRYABLE_FAILURE_REASONS,
            retryable_reason_field="measurement_retry_reason",
            label="direct v2 not-consumed",
        )


def test_v1_terminal_rejects_non_null_v2_only_fields_without_emitting_them(
) -> None:
    profile = _profile()
    slot = _slot(0, 0)
    rows = _classify(
        _reserve(_genesis(profile, [slot]), profile=profile, slot=slot),
        profile=profile,
        slot=slot,
        reason="legacy-failure",
    )
    for field_name, value in (
        ("measurement_retry_reason", "measurement_execution_unavailable"),
        ("terminal_evidence_sha256", "e" * 64),
    ):
        arguments = {
            "measurement_retry_reason": None,
            "terminal_evidence_sha256": None,
        }
        arguments[field_name] = value
        with pytest.raises(
            core.AttemptRegistryCoreError,
            match=rf"^\[attempt-terminal\] {field_name} is not accepted",
        ):
            core.record_attempt_terminal(
                rows,
                profile=profile,
                freeze_id=_FREEZE,
                slot_id=profile.slot_codec.slot_id(slot),
                binding=_BINDING,
                terminal_status="terminal-failure",
                raw_output_sha256=_RAW,
                report_sha256=None,
                observation_sha256=None,
                primary_value=None,
                failure_reason="legacy-failure",
                finished_at="2026-08-23T00:00:02+00:00",
                **arguments,
            )


def test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive(
) -> None:
    v2 = s8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=10,
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )
    identity = {
        "freeze_holdout_key": "holdout-a",
        "configuration_id": "configuration-a",
        "repetition": 0,
        "measurement_ordinal": 0,
        "attempt_ordinal": 0,
    }
    v2_slot = s8b.S8BV2AttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )
    rows = _reserve(_genesis(v2, [v2_slot]), profile=v2, slot=v2_slot)
    rows = _classify(rows, profile=v2, slot=v2_slot, reason="sealed-later")
    unsealed = replace(v2, terminal_row_validator=None)
    historical = _terminal(
        rows,
        profile=unsealed,
        slot=v2_slot,
        status="terminal-failure",
        failure_reason="sealed-later",
        measurement_retry_reason="sealed-later",
        terminal_evidence_sha256="e" * 64,
    )
    assert v2.terminal_row_validator is not None
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[s8b-v2-terminal\] v2 terminal requires "
            r"the sealed evidence API$"
        ),
    ):
        v2.terminal_row_validator(historical[-1])
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[s8b-v2-terminal\] v2 terminal requires "
            r"the sealed evidence API$"
        ),
    ):
        core.load_attempt_registry(_registry_bytes(historical), profile=v2)

    legacy = _profile()
    legacy_slot = _slot(0, 0)
    legacy_rows = _classify(
        _reserve(
            _genesis(legacy, [legacy_slot]),
            profile=legacy,
            slot=legacy_slot,
        ),
        profile=legacy,
        slot=legacy_slot,
        reason="legacy-failure",
    )
    accepted = _terminal(
        legacy_rows,
        profile=legacy,
        slot=legacy_slot,
        status="terminal-failure",
        failure_reason="legacy-failure",
    )
    assert accepted[-1]["terminal_status"] == "terminal-failure"

    ordered_calls: list[Mapping[str, Any]] = []
    tracking = replace(
        legacy, terminal_row_validator=ordered_calls.append,
    )
    _assert_core_rejection(
        "[attempt-classification] terminal failure reason differs from classification",
        lambda: _terminal(
            legacy_rows,
            profile=tracking,
            slot=legacy_slot,
            status="terminal-failure",
            failure_reason="different-failure",
        ),
    )
    assert ordered_calls == []
    _assert_core_rejection(
        "[attempt-null-matrix] attempt registry line 5 "
        "retryable-failure null matrix differs",
        lambda: _terminal(
            legacy_rows,
            profile=tracking,
            slot=legacy_slot,
            status="retryable-failure",
            failure_reason="legacy-failure",
            report_sha256=_REPORT,
        ),
    )
    assert ordered_calls == []
    tracked = _terminal(
        legacy_rows,
        profile=tracking,
        slot=legacy_slot,
        status="terminal-failure",
        failure_reason="legacy-failure",
    )
    assert ordered_calls == [tracked[-1]]

    calls: list[Mapping[str, Any]] = []

    def reject(row: Mapping[str, Any]) -> None:
        calls.append(row)
        raise core.AttemptRegistryCoreError(
            "[test-terminal-validator] rejected by lower validator"
        )

    rejecting = replace(legacy, terminal_row_validator=reject)
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[test-terminal-validator\] rejected by lower validator$"
        ),
    ):
        _terminal(
            legacy_rows,
            profile=rejecting,
            slot=legacy_slot,
            status="terminal-failure",
            failure_reason="legacy-failure",
        )
    assert len(calls) == 1
    assert calls[0]["event"] == "terminal"


def test_retryable_terminal_policy_can_close_the_next_attempt_without_changing_v1(
) -> None:
    legacy = _profile()
    retryable = replace(
        legacy,
        retryable_reasons=frozenset({"retryable-test"}),
        transition_policy=replace(
            legacy.transition_policy,
            retryable_terminal_opens_next_attempt=False,
        ),
    )
    first = _slot(0, 0)
    second = _slot(0, 1)
    rows = _classify(
        _reserve(
            _genesis(retryable, [first, second]),
            profile=retryable,
            slot=first,
        ),
        profile=retryable,
        slot=first,
        reason="retryable-test",
    )
    rows = _terminal(
        rows,
        profile=retryable,
        slot=first,
        status="retryable-failure",
        failure_reason="retryable-test",
        report_sha256=_REPORT,
    )
    _assert_core_rejection(
        "[attempt-slot-order] a retryable terminal cannot authorize the next attempt",
        lambda: _reserve(rows, profile=retryable, slot=second),
    )
    legacy_open = replace(
        retryable,
        transition_policy=replace(
            retryable.transition_policy,
            retryable_terminal_opens_next_attempt=True,
        ),
    )
    accepted = _reserve(rows, profile=legacy_open, slot=second)
    assert accepted[-2]["event"] == "start"
    assert accepted[-2]["attempt_ordinal"] == 1


def test_serialize_session_line_uses_spaced_sorted_utf8_json_and_newline() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        s8b.serialize_session_line({"value": float("nan")})
    assert s8b.serialize_session_line({"z": "雪", "a": 1}) == (
        b'{"a": 1, "z": "\xe9\x9b\xaa"}\n'
    )


def _attempt_registry_prefix_proof() -> dict[str, object]:
    return {
        "schema": core.ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA,
        "registry_schema": core.ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA,
        "freeze_sha256": _FREEZE,
        "protocol_sha256": _PROTOCOL,
        "schedule_sha256": _SCHEDULE,
        "row_count": 3,
        "chain_head_sha256": _REPORT,
    }


def _assert_prefix_proof_rejection(value: object, message: str) -> None:
    with pytest.raises(core.AttemptRegistryCoreError, match=message):
        core.validate_attempt_registry_prefix_proof(value)


def test_attempt_registry_prefix_proof_accepts_exact_v2_shape() -> None:
    source = _attempt_registry_prefix_proof()
    validated = core.validate_attempt_registry_prefix_proof(source)
    assert type(validated) is dict
    assert validated == source
    assert validated is not source
    assert tuple(validated) == (
        "schema",
        "registry_schema",
        "freeze_sha256",
        "protocol_sha256",
        "schedule_sha256",
        "row_count",
        "chain_head_sha256",
    )
    assert frozenset(validated) == core.ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS


def test_attempt_registry_prefix_proof_rejects_missing_key() -> None:
    proof = _attempt_registry_prefix_proof()
    del proof["schedule_sha256"]
    _assert_prefix_proof_rejection(proof, "key set differs")


def test_attempt_registry_prefix_proof_rejects_extra_key() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["extra"] = "closed"
    _assert_prefix_proof_rejection(proof, "key set differs")


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("schema", None),
        ("registry_schema", None),
        ("freeze_sha256", 1),
        ("protocol_sha256", 1),
        ("schedule_sha256", 1),
        ("row_count", "3"),
        ("chain_head_sha256", 1),
    ),
    ids=(
        "literal-schema-none",
        "literal-registry-schema-none",
        "digest-freeze-sha256-int",
        "digest-protocol-sha256-int",
        "digest-schedule-sha256-int",
        "row-count-str",
        "digest-chain-head-sha256-int",
    ),
)
def test_attempt_registry_prefix_proof_rejects_each_field_type(
    field: str, invalid: object,
) -> None:
    proof = _attempt_registry_prefix_proof()
    proof[field] = invalid
    _assert_prefix_proof_rejection(proof, "prefix proof|SHA-256")


def test_attempt_registry_prefix_proof_rejects_zero_row_count() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["row_count"] = 0
    _assert_prefix_proof_rejection(proof, "positive integer")


def test_attempt_registry_prefix_proof_rejects_bool_row_count() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["row_count"] = True
    _assert_prefix_proof_rejection(proof, "positive integer")


@pytest.mark.parametrize(
    "field",
    (
        "freeze_sha256",
        "protocol_sha256",
        "schedule_sha256",
        "chain_head_sha256",
    ),
)
def test_attempt_registry_prefix_proof_rejects_invalid_digest(
    field: str,
) -> None:
    proof = _attempt_registry_prefix_proof()
    proof[field] = "A" * 64
    _assert_prefix_proof_rejection(proof, "SHA-256 digest")


def test_attempt_registry_prefix_proof_rejects_zero_head() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["chain_head_sha256"] = "0" * 64
    _assert_prefix_proof_rejection(proof, "chain head is zero")


def test_attempt_registry_prefix_proof_rejects_wrong_proof_schema() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["schema"] = "s8b-floor-attempt-registry-proof/v2"
    _assert_prefix_proof_rejection(proof, "proof schema is unsupported")


def test_attempt_registry_prefix_proof_rejects_wrong_registry_schema() -> None:
    proof = _attempt_registry_prefix_proof()
    proof["registry_schema"] = "s8b-floor-attempt-registry/v1"
    _assert_prefix_proof_rejection(proof, "registry_schema is unsupported")


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
