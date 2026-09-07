# -*- coding: utf-8 -*-
"""Domain profile for the 8b floor attempt registry."""
from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
import json
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, ClassVar, TypeAlias

from .attempt_registry_core import (
    AttemptRegistryCoreError,
    DomainProfile,
    RecoveryPolicy,
    RegistryLayout,
    SchemaProfile,
    SeriesKey,
    TransitionPolicy,
)
from .s8b_terminal_evidence import (
    ValidatedTerminalEvidence,
    require_sealed_terminal_evidence,
)


S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION = "s8b-floor-attempt-registry/v1"
S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION = "s8b-floor-attempt-registry/v2"
S8B_RECOVERY_RECEIPT_SCHEMA_VERSION = "scheduler-accounting-receipt/v1"
S8B_RECOVERY_RECEIPT_EVENT = "scheduler-termination"
S8B_RECOVERY_RECEIPT_SOURCE = "nqsv-qstat-accounting"

S8BSlotIdentity: TypeAlias = tuple[str, str, int, int]
S8BSeriesKey: TypeAlias = tuple[str, str, int]
S8BBudgetKey: TypeAlias = tuple[str, str]
S8BV2SlotIdentity: TypeAlias = tuple[str, str, int, int, int]
S8BV2SeriesKey: TypeAlias = tuple[str, str, int, int]


@dataclass(frozen=True, slots=True)
class S8BAttemptSlot:
    """One freeze-wide 8b slot; campaign_run_id is intentionally absent."""

    freeze_holdout_key: str
    configuration_id: str
    repetition: int
    attempt_ordinal: int
    schedule_row_sha256: str


@dataclass(frozen=True, slots=True)
class S8BAttemptBinding:
    """Immutable freeze/protocol/schedule binding shared by registry rows."""

    freeze_sha256: str
    protocol_sha256: str
    schedule_sha256: str


@dataclass(frozen=True, slots=True)
class S8BSlotCodec:
    """Parse and serialize the frozen 8b slot identity."""

    exact_keys: ClassVar[frozenset[str]] = frozenset({
        "freeze_holdout_key",
        "configuration_id",
        "repetition",
        "attempt_ordinal",
        "schedule_row_sha256",
    })

    def parse(self, value: object, *, label: str) -> S8BAttemptSlot:
        """Parse one serialized 8b slot."""

        if not isinstance(value, Mapping) or frozenset(value) != self.exact_keys:
            raise AttemptRegistryCoreError(
                f"[attempt-registry-schema] {label} exact keys differ"
            )
        freeze_holdout_key = _bounded_text(
            value.get("freeze_holdout_key"),
            label=f"{label}.freeze_holdout_key",
        )
        configuration_id = _bounded_text(
            value.get("configuration_id"),
            label=f"{label}.configuration_id",
        )
        repetition = _nonnegative_int(
            value.get("repetition"), label=f"{label}.repetition",
        )
        attempt_ordinal = _nonnegative_int(
            value.get("attempt_ordinal"),
            label=f"{label}.attempt_ordinal",
        )
        schedule_row_sha256 = _sha256(
            value.get("schedule_row_sha256"),
            label=f"{label}.schedule_row_sha256",
        )
        return S8BAttemptSlot(
            freeze_holdout_key=freeze_holdout_key,
            configuration_id=configuration_id,
            repetition=repetition,
            attempt_ordinal=attempt_ordinal,
            schedule_row_sha256=schedule_row_sha256,
        )

    def to_json(self, slot: S8BAttemptSlot) -> dict[str, Any]:
        """Project an 8b slot to canonical JSON fields."""

        if type(slot) is not S8BAttemptSlot:
            raise AttemptRegistryCoreError(
                "[attempt-registry-schema] 8b slot has an invalid type"
            )
        value = {
            "freeze_holdout_key": slot.freeze_holdout_key,
            "configuration_id": slot.configuration_id,
            "repetition": slot.repetition,
            "attempt_ordinal": slot.attempt_ordinal,
            "schedule_row_sha256": slot.schedule_row_sha256,
        }
        parsed = self.parse(value, label="8b slot")
        return {
            "freeze_holdout_key": parsed.freeze_holdout_key,
            "configuration_id": parsed.configuration_id,
            "repetition": parsed.repetition,
            "attempt_ordinal": parsed.attempt_ordinal,
            "schedule_row_sha256": parsed.schedule_row_sha256,
        }

    def slot_id(self, slot: S8BAttemptSlot) -> S8BSlotIdentity:
        """Identify a slot without campaign_run_id or any campaign identifier."""

        return (
            slot.freeze_holdout_key,
            slot.configuration_id,
            slot.repetition,
            slot.attempt_ordinal,
        )

    def series_key(self, slot: S8BAttemptSlot) -> SeriesKey:
        """Group attempts within one repetition."""

        return (
            slot.freeze_holdout_key,
            slot.configuration_id,
            slot.repetition,
        )

    def attempt_ordinal(self, slot: S8BAttemptSlot) -> int:
        """Return the zero-based rescue ordinal."""

        return slot.attempt_ordinal

    def schedule_sha256(self, slot: S8BAttemptSlot) -> str:
        """Return the frozen schedule-row digest."""

        return slot.schedule_row_sha256


@dataclass(frozen=True, slots=True)
class S8BV2AttemptSlot:
    """One protocol-generation slot with distinct measurement and retry axes."""

    freeze_holdout_key: str
    configuration_id: str
    repetition: int
    measurement_ordinal: int
    attempt_ordinal: int
    schedule_row_sha256: str


@dataclass(frozen=True, slots=True)
class S8BV2SlotCodec:
    """Parse and serialize the five-axis v2 slot identity."""

    exact_keys: ClassVar[frozenset[str]] = frozenset({
        "freeze_holdout_key",
        "configuration_id",
        "repetition",
        "measurement_ordinal",
        "attempt_ordinal",
        "schedule_row_sha256",
    })

    def parse(self, value: object, *, label: str) -> S8BV2AttemptSlot:
        if not isinstance(value, Mapping) or frozenset(value) != self.exact_keys:
            raise AttemptRegistryCoreError(
                f"[attempt-registry-schema] {label} exact keys differ"
            )
        return S8BV2AttemptSlot(
            freeze_holdout_key=_bounded_text(
                value.get("freeze_holdout_key"),
                label=f"{label}.freeze_holdout_key",
            ),
            configuration_id=_bounded_text(
                value.get("configuration_id"),
                label=f"{label}.configuration_id",
            ),
            repetition=_nonnegative_int(
                value.get("repetition"), label=f"{label}.repetition",
            ),
            measurement_ordinal=_nonnegative_int(
                value.get("measurement_ordinal"),
                label=f"{label}.measurement_ordinal",
            ),
            attempt_ordinal=_nonnegative_int(
                value.get("attempt_ordinal"),
                label=f"{label}.attempt_ordinal",
            ),
            schedule_row_sha256=_sha256(
                value.get("schedule_row_sha256"),
                label=f"{label}.schedule_row_sha256",
            ),
        )

    def to_json(self, slot: S8BV2AttemptSlot) -> dict[str, Any]:
        if type(slot) is not S8BV2AttemptSlot:
            raise AttemptRegistryCoreError(
                "[attempt-registry-schema] 8b v2 slot has an invalid type"
            )
        value = {
            "freeze_holdout_key": slot.freeze_holdout_key,
            "configuration_id": slot.configuration_id,
            "repetition": slot.repetition,
            "measurement_ordinal": slot.measurement_ordinal,
            "attempt_ordinal": slot.attempt_ordinal,
            "schedule_row_sha256": slot.schedule_row_sha256,
        }
        parsed = self.parse(value, label="8b v2 slot")
        return {
            "freeze_holdout_key": parsed.freeze_holdout_key,
            "configuration_id": parsed.configuration_id,
            "repetition": parsed.repetition,
            "measurement_ordinal": parsed.measurement_ordinal,
            "attempt_ordinal": parsed.attempt_ordinal,
            "schedule_row_sha256": parsed.schedule_row_sha256,
        }

    def slot_id(self, slot: S8BV2AttemptSlot) -> S8BV2SlotIdentity:
        return (
            slot.freeze_holdout_key,
            slot.configuration_id,
            slot.repetition,
            slot.measurement_ordinal,
            slot.attempt_ordinal,
        )

    def series_key(self, slot: S8BV2AttemptSlot) -> SeriesKey:
        return (
            slot.freeze_holdout_key,
            slot.configuration_id,
            slot.repetition,
            slot.measurement_ordinal,
        )

    def attempt_ordinal(self, slot: S8BV2AttemptSlot) -> int:
        return slot.attempt_ordinal

    def schedule_sha256(self, slot: S8BV2AttemptSlot) -> str:
        return slot.schedule_row_sha256


@dataclass(frozen=True, slots=True)
class S8BBindingCodec:
    """Parse and serialize the immutable freeze/protocol/schedule binding."""

    event_keys: ClassVar[frozenset[str]] = frozenset({
        "freeze_sha256",
        "protocol_sha256",
        "schedule_sha256",
    })

    def parse(
        self,
        row: Mapping[str, object],
        *,
        label: str,
    ) -> S8BAttemptBinding:
        """Parse the 8b binding fields of one row."""

        missing = self.event_keys - frozenset(row)
        if missing:
            raise AttemptRegistryCoreError(
                f"[attempt-registry-schema] {label} binding keys are missing: "
                f"{sorted(missing)}"
            )
        return S8BAttemptBinding(
            freeze_sha256=_sha256(
                row.get("freeze_sha256"), label=f"{label}.freeze_sha256",
            ),
            protocol_sha256=_sha256(
                row.get("protocol_sha256"), label=f"{label}.protocol_sha256",
            ),
            schedule_sha256=_sha256(
                row.get("schedule_sha256"), label=f"{label}.schedule_sha256",
            ),
        )

    def to_event_fields(self, binding: S8BAttemptBinding) -> dict[str, Any]:
        """Project the immutable 8b binding into an event."""

        if type(binding) is not S8BAttemptBinding:
            raise AttemptRegistryCoreError(
                "[attempt-registry-schema] 8b binding has an invalid type"
            )
        parsed = self.parse(
            {
                "freeze_sha256": binding.freeze_sha256,
                "protocol_sha256": binding.protocol_sha256,
                "schedule_sha256": binding.schedule_sha256,
            },
            label="8b binding",
        )
        return {
            "freeze_sha256": parsed.freeze_sha256,
            "protocol_sha256": parsed.protocol_sha256,
            "schedule_sha256": parsed.schedule_sha256,
        }

    def identity(self, binding: S8BAttemptBinding) -> Hashable:
        """Return the freeze-wide binding identity."""

        return (
            binding.freeze_sha256,
            binding.protocol_sha256,
            binding.schedule_sha256,
        )

    def capability_payload(
        self,
        *,
        slot: S8BAttemptSlot | S8BV2AttemptSlot,
        binding: S8BAttemptBinding,
        freeze_id: str,
    ) -> dict[str, Any]:
        """Build the 8b portion of a capability payload."""

        # freeze_id is part of the common capability envelope.  Requiring the
        # same digest here prevents a caller from presenting a second alias for
        # the freeze-wide registry identity.
        if freeze_id != binding.freeze_sha256:
            raise AttemptRegistryCoreError(
                "[attempt-binding] capability freeze_id differs from 8b binding"
            )
        if type(slot) is S8BAttemptSlot:
            slot_fields = S8B_SLOT_CODEC.to_json(slot)
        elif type(slot) is S8BV2AttemptSlot:
            slot_fields = S8B_V2_SLOT_CODEC.to_json(slot)
        else:
            raise AttemptRegistryCoreError(
                "[attempt-registry-schema] 8b capability slot type differs"
            )
        return {**slot_fields, **self.to_event_fields(binding)}


def _bounded_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise AttemptRegistryCoreError(
            f"[attempt-registry-schema] {label} is not a bounded non-empty string"
        )
    return value


def _nonnegative_int(value: object, *, label: str) -> int:
    if type(value) is not int or value < 0:
        raise AttemptRegistryCoreError(
            f"[attempt-registry-schema] {label} is not a nonnegative integer"
        )
    return value


def _sha256(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AttemptRegistryCoreError(
            f"[attempt-registry-schema] {label} is not a SHA-256 digest"
        )
    return value


_CHAIN_KEYS = frozenset({
    "event_index",
    "previous_event_sha256",
    "event_sha256",
})
_SLOT_IDENTITY_KEYS = frozenset({
    "freeze_holdout_key",
    "configuration_id",
    "repetition",
    "attempt_ordinal",
})
_BINDING_KEYS = S8BBindingCodec.event_keys
_COMMON_EVENT_KEYS = frozenset({"schema_version", "event"}) | _CHAIN_KEYS

_S8B_GENESIS_KEYS = frozenset({
    "schema_version",
    "event",
    "root_path",
    "retryable_failure_reasons",
    "max_consumptions_per_budget_key",
    "recovery_policy_sha256",
    "slots",
}) | _BINDING_KEYS | _CHAIN_KEYS

_S8B_EVENT_KEYS = MappingProxyType({
    "start": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | _BINDING_KEYS
        | frozenset({
            "run_start_receipt_sha256",
            "process_identity",
            "schedule_row_sha256",
            "started_at",
        })
    ),
    "pre-observation-seal": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | frozenset({
            "start_event_sha256",
            "run_start_receipt_sha256",
            "process_identity",
            "schedule_row_sha256",
        })
    ),
    "classification": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | _BINDING_KEYS
        | frozenset({
            "classification_receipt_sha256",
            "capability_digest_sha256",
            "authority_id",
            "authority_policy_sha256",
            "external_evidence_sha256",
            "classified_at",
            "pre_observation_failure_reason",
            "pre_observation_seal_sha256",
        })
    ),
    "observation-start": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | frozenset({"classification_event_sha256"})
    ),
    "terminal": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | _BINDING_KEYS
        | frozenset({
            "classification_receipt_sha256",
            "terminal_status",
            "raw_output_sha256",
            "report_sha256",
            "observation_sha256",
            "primary_value",
            "failure_reason",
            "pre_observation_failure_reason_echo",
            "observation_start_event_sha256",
            "finished_at",
            "schedule_row_sha256",
            "process_identity",
        })
    ),
    "recovery": (
        _COMMON_EVENT_KEYS
        | _SLOT_IDENTITY_KEYS
        | _BINDING_KEYS
        | frozenset({
            "start_event_sha256",
            "scheduler_accounting_receipt",
            "scheduler_accounting_receipt_sha256",
            "failure_reason",
            "recoverer_process_identity",
            "recovered_at",
        })
    ),
})

S8B_SCHEMA_PROFILE = SchemaProfile(
    current=S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION,
    readable=frozenset({S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION}),
    genesis_keys=MappingProxyType({
        S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION: _S8B_GENESIS_KEYS,
    }),
    event_keys=MappingProxyType({
        S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION: _S8B_EVENT_KEYS,
    }),
)

_S8B_V2_EVENT_KEYS = MappingProxyType({
    event: (
        keys
        | frozenset({"measurement_ordinal"})
        | (
            frozenset({
                "measurement_retry_reason",
                "terminal_evidence_sha256",
            })
            if event == "terminal" else frozenset()
        )
    )
    for event, keys in _S8B_EVENT_KEYS.items()
})

S8B_V2_SCHEMA_PROFILE = SchemaProfile(
    current=S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION,
    readable=frozenset({S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION}),
    genesis_keys=MappingProxyType({
        S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION: _S8B_GENESIS_KEYS,
    }),
    event_keys=MappingProxyType({
        S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION: _S8B_V2_EVENT_KEYS,
    }),
)

S8B_REGISTRY_LAYOUT = RegistryLayout(
    # Both paths are relative to the existing shared 8b admission root.
    registry_path=PurePosixPath(
        "floor-attempt-registries/{freeze_sha256}/registry.jsonl"
    ),
    classification_receipt_dir=PurePosixPath(
        "floor-attempt-registry-receipts"
    ),
)

S8B_V2_REGISTRY_LAYOUT = RegistryLayout(
    registry_path=PurePosixPath(
        "floor-attempt-registries/{freeze_sha256}/{protocol_sha256}/registry.jsonl"
    ),
    classification_receipt_dir=PurePosixPath(
        "floor-attempt-registry-receipts"
    ),
)

S8B_ATTEMPT_STATUSES = (
    "observed",
    "retryable-failure",
    "terminal-failure",
    "not-consumed",
)

S8B_RETRYABLE_FAILURE_REASONS: frozenset[str] = frozenset()
S8B_V2_RETRYABLE_FAILURE_REASONS: frozenset[str] = frozenset({
    "measurement_environment_conflict",
    "measurement_execution_unavailable",
    "measurement_sample_incomplete",
    "measurement_dispersion_exceeded",
})
S8B_RECOVERY_FAILURE_REASONS: frozenset[str] = frozenset({
    "node_failure",
    "scheduler_external_interruption",
})

S8B_SLOT_CODEC = S8BSlotCodec()
S8B_V2_SLOT_CODEC = S8BV2SlotCodec()
S8B_BINDING_CODEC = S8BBindingCodec()


def _s8b_budget_key(slot: S8BAttemptSlot) -> S8BBudgetKey:
    """Aggregate a cell budget independently of repetition and attempt."""

    return slot.freeze_holdout_key, slot.configuration_id


def _s8b_v2_budget_key(slot: S8BV2AttemptSlot) -> S8BBudgetKey:
    """Aggregate a v2 cell budget across both ordinal axes."""

    return slot.freeze_holdout_key, slot.configuration_id


def _reject_unsealed_s8b_v2_terminal(
    _row: Mapping[str, Any],
) -> None:
    """Keep v2 terminal rows closed until the sealed evidence API exists."""

    raise AttemptRegistryCoreError(
        "[s8b-v2-terminal] v2 terminal requires the sealed evidence API"
    )


def _require_sealed_s8b_v2_terminal(
    row: Mapping[str, Any],
    evidence: ValidatedTerminalEvidence,
) -> None:
    """Require one adapter-issued capability to match all durable row facts."""

    if type(evidence) is not ValidatedTerminalEvidence:
        raise AttemptRegistryCoreError(
            "[s8b-v2-terminal] terminal evidence capability type differs"
        )
    try:
        validated = require_sealed_terminal_evidence(evidence)
        projection = validated.projection
        binding = validated.document["attempt_binding"]
    except (TypeError, ValueError, KeyError) as exc:
        raise AttemptRegistryCoreError(
            "[s8b-v2-terminal] terminal evidence capability is invalid"
        ) from exc
    expected = {
        "terminal_status": projection.terminal_status,
        "failure_reason": projection.failure_reason,
        "measurement_retry_reason": projection.measurement_retry_reason,
        "primary_value": projection.primary_value,
        "raw_output_sha256": projection.raw_output_sha256,
        "report_sha256": projection.report_sha256,
        "observation_sha256": projection.observation_sha256,
        "classification_receipt_sha256": binding[
            "classification_receipt_sha256"
        ],
        "observation_start_event_sha256": binding[
            "observation_event_sha256"
        ],
        "finished_at": projection.finished_at,
        "terminal_evidence_sha256": validated.sha256,
    }
    for field_name, expected_value in expected.items():
        if row.get(field_name) != expected_value:
            raise AttemptRegistryCoreError(
                "[s8b-v2-terminal] terminal row differs from sealed evidence: "
                f"{field_name}"
            )


def serialize_session_line(record: Mapping[str, Any]) -> bytes:
    """Serialize the durable floor-session JSON line exactly once."""

    return (
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _s8b_freeze_id_from_genesis(genesis: Mapping[str, Any]) -> str:
    """Use the frozen document digest as the registry-wide identity."""

    value = genesis.get("freeze_sha256")
    return _sha256(value, label="attempt registry genesis.freeze_sha256")


def make_s8b_domain_profile(
    *,
    max_consumptions_per_budget_key: int,
    recovery_authority_id: str,
    recovery_authority_policy_sha256: str,
) -> DomainProfile[S8BAttemptSlot, S8BAttemptBinding]:
    """Bind the 8b budget and pinned recovery authority to immutable data.

    The cap is required rather than guessed here because its value comes from
    the frozen protocol.  The authority inputs identify an already selected
    policy; this factory does not implement its collector or any production
    caller.
    """

    if (
        type(max_consumptions_per_budget_key) is not int
        or max_consumptions_per_budget_key < 0
    ):
        raise AttemptRegistryCoreError(
            "[attempt-registry-profile] 8b cell consumption budget is invalid"
        )

    return DomainProfile(
        schema=S8B_SCHEMA_PROFILE,
        layout=S8B_REGISTRY_LAYOUT,
        statuses=S8B_ATTEMPT_STATUSES,
        retryable_reasons=S8B_RETRYABLE_FAILURE_REASONS,
        slot_codec=S8B_SLOT_CODEC,
        binding_codec=S8B_BINDING_CODEC,
        transition_policy=TransitionPolicy(
            require_previous_terminal=True,
            forbid_retry_after_observation=True,
            allow_recovered_abandonment=True,
            max_series_attempts=None,
            require_terminal_reason_equals_classification=True,
            budget_key=_s8b_budget_key,
            max_consumptions_per_budget_key=(
                max_consumptions_per_budget_key
            ),
        ),
        recovery_policy=RecoveryPolicy(
            receipt_schema_version=S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
            receipt_event=S8B_RECOVERY_RECEIPT_EVENT,
            receipt_source=S8B_RECOVERY_RECEIPT_SOURCE,
            authority_id=recovery_authority_id,
            authority_policy_sha256=recovery_authority_policy_sha256,
            failure_reasons=S8B_RECOVERY_FAILURE_REASONS,
        ),
        freeze_id_from_genesis=_s8b_freeze_id_from_genesis,
    )


def make_s8b_v2_domain_profile(
    *,
    max_consumptions_per_budget_key: int,
    recovery_authority_id: str,
    recovery_authority_policy_sha256: str,
) -> DomainProfile[S8BV2AttemptSlot, S8BAttemptBinding]:
    """Build the additive five-axis profile for one protocol generation."""

    if (
        type(max_consumptions_per_budget_key) is not int
        or max_consumptions_per_budget_key < 0
    ):
        raise AttemptRegistryCoreError(
            "[attempt-registry-profile] 8b cell consumption budget is invalid"
        )

    return DomainProfile(
        schema=S8B_V2_SCHEMA_PROFILE,
        layout=S8B_V2_REGISTRY_LAYOUT,
        statuses=S8B_ATTEMPT_STATUSES,
        retryable_reasons=S8B_V2_RETRYABLE_FAILURE_REASONS,
        slot_codec=S8B_V2_SLOT_CODEC,
        binding_codec=S8B_BINDING_CODEC,
        transition_policy=TransitionPolicy(
            require_previous_terminal=True,
            forbid_retry_after_observation=True,
            allow_recovered_abandonment=True,
            max_series_attempts=None,
            require_terminal_reason_equals_classification=True,
            budget_key=_s8b_v2_budget_key,
            max_consumptions_per_budget_key=(
                max_consumptions_per_budget_key
            ),
            retryable_terminal_opens_next_attempt=False,
        ),
        recovery_policy=RecoveryPolicy(
            receipt_schema_version=S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
            receipt_event=S8B_RECOVERY_RECEIPT_EVENT,
            receipt_source=S8B_RECOVERY_RECEIPT_SOURCE,
            authority_id=recovery_authority_id,
            authority_policy_sha256=recovery_authority_policy_sha256,
            failure_reasons=S8B_RECOVERY_FAILURE_REASONS,
        ),
        freeze_id_from_genesis=_s8b_freeze_id_from_genesis,
        terminal_row_validator=_reject_unsealed_s8b_v2_terminal,
        retryable_reason_field="measurement_retry_reason",
    )
