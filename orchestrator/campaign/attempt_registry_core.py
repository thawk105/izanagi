# -*- coding: utf-8 -*-
"""Domain-independent append-only attempt-registry state machine.

The core owns canonical lifecycle rows, hash-chain replay, and transition
authorization. A :class:`DomainProfile` supplies every domain binding. Git
history, locking, create-only storage, and capability ownership stay in each
domain facade.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType as _MappingProxyType
from typing import Any, Generic, Protocol, TypeAlias, TypeVar, runtime_checkable


SlotT = TypeVar("SlotT")
BindingT = TypeVar("BindingT")
RegistryRow: TypeAlias = dict[str, Any]
RegistryRows: TypeAlias = tuple[RegistryRow, ...]
BudgetCounts: TypeAlias = dict[Hashable, int]
SeriesKey: TypeAlias = tuple[Hashable, ...]

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_ZERO_SHA256 = "0" * 64
_CHAIN_KEYS = frozenset({
    "event_index", "previous_event_sha256", "event_sha256",
})
ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA = (
    "s8b-floor-attempt-registry-proof/v1"
)
ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA = (
    "s8b-floor-attempt-registry/v2"
)
ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS = frozenset({
    "schema",
    "registry_schema",
    "freeze_sha256",
    "protocol_sha256",
    "schedule_sha256",
    "row_count",
    "chain_head_sha256",
})
_DEFAULT_PROCESS_IDENTITY_KEYS = frozenset({
    "pid", "starttime", "execution_uuid",
})
_CORE_SEMANTIC_EVENTS = frozenset({
    "start",
    "pre-observation-seal",
    "classification",
    "observation-start",
    "terminal",
    "recovery",
})
_SCHEDULER_ACCOUNTING_RECEIPT_KEYS = frozenset({
    "schema_version",
    "event",
    "source",
    "scheduler_request_id",
    "target_start_event_sha256",
    "raw_scheduler_accounting_record_sha256",
    "authority_id",
    "authority_policy_sha256",
    "failure_reason",
    "collected_at",
})


class AttemptRegistryCoreError(RuntimeError):
    """A domain-independent registry check rejected its input."""


def _fail(gate: str, message: str) -> None:
    raise AttemptRegistryCoreError(f"[{gate}] {message}")


@runtime_checkable
class SlotCodec(Protocol[SlotT]):
    exact_keys: frozenset[str]

    def parse(self, value: object, *, label: str) -> SlotT: ...
    def to_json(self, slot: SlotT) -> dict[str, Any]: ...
    def slot_id(self, slot: SlotT) -> Hashable: ...
    def series_key(self, slot: SlotT) -> SeriesKey: ...
    def attempt_ordinal(self, slot: SlotT) -> int: ...
    def schedule_sha256(self, slot: SlotT) -> str: ...


@runtime_checkable
class BindingCodec(Protocol[SlotT, BindingT]):
    event_keys: frozenset[str]

    def parse(self, row: Mapping[str, object], *, label: str) -> BindingT: ...
    def to_event_fields(self, binding: BindingT) -> dict[str, Any]: ...
    def identity(self, binding: BindingT) -> Hashable: ...
    def capability_payload(
        self, *, slot: SlotT, binding: BindingT, freeze_id: str,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class SchemaProfile:
    current: str
    readable: frozenset[str]
    genesis_keys: Mapping[str, frozenset[str]]
    event_keys: Mapping[str, Mapping[str, frozenset[str]]]
    receipt_keys: Mapping[str, frozenset[str]] | None = None

    def __post_init__(self) -> None:
        """Freeze nested schema tables as deeply immutable profile data."""
        object.__setattr__(self, "readable", frozenset(self.readable))
        object.__setattr__(
            self,
            "genesis_keys",
            _MappingProxyType({
                version: frozenset(keys)
                for version, keys in self.genesis_keys.items()
            }),
        )
        object.__setattr__(
            self,
            "event_keys",
            _MappingProxyType({
                version: _MappingProxyType({
                    event: frozenset(keys)
                    for event, keys in events.items()
                })
                for version, events in self.event_keys.items()
            }),
        )
        if self.receipt_keys is not None:
            object.__setattr__(
                self,
                "receipt_keys",
                _MappingProxyType({
                    version: frozenset(keys)
                    for version, keys in self.receipt_keys.items()
                }),
            )


@dataclass(frozen=True, slots=True)
class RegistryLayout:
    registry_path: PurePosixPath
    classification_receipt_dir: PurePosixPath


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    """Pinned authority contract for the common recovery semantic."""

    receipt_schema_version: str
    receipt_event: str
    receipt_source: str
    authority_id: str
    authority_policy_sha256: str
    failure_reasons: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "failure_reasons", frozenset(self.failure_reasons))
        for field in (
            "receipt_schema_version", "receipt_event", "receipt_source",
            "authority_id",
        ):
            _text(getattr(self, field), label=f"recovery policy.{field}")
        _digest(
            self.authority_policy_sha256,
            label="recovery policy.authority_policy_sha256",
        )
        if not self.failure_reasons:
            _fail(
                "attempt-registry-profile",
                "recovery policy failure_reasons must be non-empty",
            )
        for reason in self.failure_reasons:
            _text(reason, label="recovery policy.failure_reason")


@dataclass(frozen=True, slots=True)
class TransitionPolicy(Generic[SlotT]):
    require_previous_terminal: bool
    forbid_retry_after_observation: bool
    allow_recovered_abandonment: bool
    max_series_attempts: int | None
    require_terminal_reason_equals_classification: bool
    budget_key: Callable[[SlotT], Hashable] | None
    max_consumptions_per_budget_key: int | None
    retryable_terminal_opens_next_attempt: bool = field(
        default=True, kw_only=True,
    )


@dataclass(frozen=True, slots=True)
class DomainProfile(Generic[SlotT, BindingT]):
    schema: SchemaProfile
    layout: RegistryLayout
    statuses: tuple[str, ...]
    retryable_reasons: frozenset[str]
    slot_codec: SlotCodec[SlotT]
    binding_codec: BindingCodec[SlotT, BindingT]
    transition_policy: TransitionPolicy[SlotT]
    recovery_policy: RecoveryPolicy | None = None
    process_identity_keys: frozenset[str] = _DEFAULT_PROCESS_IDENTITY_KEYS
    build_genesis_fields: Callable[
        [str, PurePosixPath, str], Mapping[str, Any]
    ] | None = None
    freeze_id_from_genesis: Callable[[Mapping[str, Any]], str] | None = None
    binding_conflict_message: str = "attempt rows do not share one binding"
    binding_mismatch: Callable[[BindingT, BindingT], str | None] | None = None
    terminal_row_validator: Callable[[Mapping[str, Any]], None] | None = field(
        default=None, kw_only=True,
    )
    retryable_reason_field: str = field(
        default="failure_reason", kw_only=True,
    )


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AttemptRegistryCoreError(
            f"[json] value is not canonical JSON: {exc}"
        ) from exc


def _recovery_policy_sha256(
    profile: DomainProfile[Any, Any],
) -> str | None:
    policy = profile.recovery_policy
    if policy is None:
        return None
    enabled = profile.transition_policy.allow_recovered_abandonment
    if type(enabled) is not bool:
        _fail(
            "attempt-registry-profile",
            "recovery policy enable flag is not boolean",
        )
    payload = {
        "receipt_schema_version": policy.receipt_schema_version,
        "receipt_event": policy.receipt_event,
        "receipt_source": policy.receipt_source,
        "authority_id": policy.authority_id,
        "authority_policy_sha256": policy.authority_policy_sha256,
        "failure_reasons": sorted(policy.failure_reasons),
        "enabled": enabled,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def event_sha256(row: Mapping[str, Any]) -> str:
    payload = dict(row)
    payload.pop("event_sha256", None)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def chained_event_row(
    row: Mapping[str, Any], *, event_index: int,
    previous_event_sha256: str,
) -> RegistryRow:
    if type(event_index) is not int or event_index < 0:
        _fail("attempt-event-chain", "event_index is invalid")
    _digest(previous_event_sha256, label="previous_event_sha256")
    result = dict(row)
    result["event_index"] = event_index
    result["previous_event_sha256"] = previous_event_sha256
    result["event_sha256"] = event_sha256(result)
    return result


def previous_event_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    for row in reversed(rows):
        if _CHAIN_KEYS <= frozenset(row):
            value = row.get("event_sha256")
            if isinstance(value, str):
                return value
    return _ZERO_SHA256


def validate_attempt_registry_prefix_proof(
    value: object,
) -> dict[str, object]:
    """Validate and normalize one exact v2 attempt-registry prefix proof."""

    if not isinstance(value, Mapping):
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof is not a mapping",
        )
    actual_keys = frozenset(value)
    if actual_keys != ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS:
        missing = sorted(ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS - actual_keys)
        unknown = sorted(actual_keys - ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS)
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof key set differs: "
            f"missing={missing}, unknown={unknown}",
        )
    schema = value.get("schema")
    if schema != ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA:
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof schema is unsupported",
        )
    registry_schema = value.get("registry_schema")
    if registry_schema != ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA:
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof registry_schema is unsupported",
        )
    freeze_sha256 = _digest(
        value.get("freeze_sha256"), label="prefix proof.freeze_sha256",
    )
    protocol_sha256 = _digest(
        value.get("protocol_sha256"), label="prefix proof.protocol_sha256",
    )
    schedule_sha256 = _digest(
        value.get("schedule_sha256"), label="prefix proof.schedule_sha256",
    )
    row_count = value.get("row_count")
    if type(row_count) is not int or row_count < 1:
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof row_count is not a positive integer",
        )
    chain_head_sha256 = _digest(
        value.get("chain_head_sha256"),
        label="prefix proof.chain_head_sha256",
    )
    if chain_head_sha256 == _ZERO_SHA256:
        _fail(
            "attempt-registry-prefix-proof",
            "attempt registry prefix proof chain head is zero",
        )
    return {
        "schema": schema,
        "registry_schema": registry_schema,
        "freeze_sha256": freeze_sha256,
        "protocol_sha256": protocol_sha256,
        "schedule_sha256": schedule_sha256,
        "row_count": row_count,
        "chain_head_sha256": chain_head_sha256,
    }


def capability_digest(
    *, profile: DomainProfile[SlotT, BindingT], schema_version: str,
    freeze_id: str, slot: SlotT, binding: BindingT,
) -> str:
    payload = {
        "schema_version": schema_version,
        "freeze_id": freeze_id,
        **profile.binding_codec.capability_payload(
            slot=slot, binding=binding, freeze_id=freeze_id,
        ),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _digest(value: object, *, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("attempt-registry-schema", f"{label} is not a SHA-256 digest")
    return value


def _text(value: object, *, label: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        _fail(
            "attempt-registry-schema",
            f"{label} is not a bounded non-empty string",
        )
    return value


def parse_process_identity(
    value: object, *, label: str,
    exact_keys: frozenset[str] = _DEFAULT_PROCESS_IDENTITY_KEYS,
) -> RegistryRow:
    if type(value) is not dict or frozenset(value) != exact_keys:
        _fail("attempt-registry-schema", f"{label} exact keys differ")
    pid = value.get("pid")
    if type(pid) is not int or pid < 1:
        _fail("attempt-registry-schema", f"{label}.pid is invalid")
    starttime = value.get("starttime")
    if type(starttime) is bool or not isinstance(starttime, (int, str)):
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    if isinstance(starttime, int) and starttime < 0:
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    if isinstance(starttime, str) and not starttime:
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    execution_uuid = _text(
        value.get("execution_uuid"), label=f"{label}.execution_uuid",
    )
    return {"pid": pid, "starttime": starttime, "execution_uuid": execution_uuid}


def _recovery_comparison_identity(
    identity: Mapping[str, Any],
) -> RegistryRow:
    starttime = identity["starttime"]
    if type(starttime) is int:
        comparison_starttime = str(starttime)
    elif starttime.isascii() and starttime.isdecimal():
        comparison_starttime = starttime.lstrip("0") or "0"
    else:
        comparison_starttime = starttime
    return {
        **dict(identity),
        "starttime": comparison_starttime,
    }


def _parse_recovery_receipt(
    value: object, *, profile: DomainProfile[Any, Any], label: str,
) -> RegistryRow:
    policy = profile.recovery_policy
    if (
        policy is None
        or not profile.transition_policy.allow_recovered_abandonment
    ):
        _fail(
            "attempt-recovery-evidence",
            f"{label} is not enabled by the domain profile",
        )
    if type(value) is not dict:
        _fail(
            "attempt-recovery-evidence",
            f"{label} is not a canonical object",
        )
    actual_keys = frozenset(value)
    if actual_keys != _SCHEDULER_ACCOUNTING_RECEIPT_KEYS:
        missing = sorted(_SCHEDULER_ACCOUNTING_RECEIPT_KEYS - actual_keys)
        unknown = sorted(actual_keys - _SCHEDULER_ACCOUNTING_RECEIPT_KEYS)
        _fail(
            "attempt-recovery-evidence",
            f"{label} key set differs: missing={missing}, unknown={unknown}",
        )
    exact_values = {
        "schema_version": policy.receipt_schema_version,
        "event": policy.receipt_event,
        "source": policy.receipt_source,
        "authority_id": policy.authority_id,
        "authority_policy_sha256": policy.authority_policy_sha256,
    }
    for field, expected in exact_values.items():
        if value.get(field) != expected:
            _fail(
                "attempt-recovery-evidence",
                f"{label}.{field} differs from the pinned authority policy",
            )
    scheduler_request_id = value.get("scheduler_request_id")
    if (
        not isinstance(scheduler_request_id, str)
        or not scheduler_request_id
        or len(scheduler_request_id) > 256
    ):
        _fail(
            "attempt-recovery-evidence",
            f"{label}.scheduler_request_id is invalid",
        )
    for field in (
        "target_start_event_sha256",
        "raw_scheduler_accounting_record_sha256",
        "authority_policy_sha256",
    ):
        field_value = value.get(field)
        if (
            not isinstance(field_value, str)
            or _SHA256_RE.fullmatch(field_value) is None
        ):
            _fail(
                "attempt-recovery-evidence",
                f"{label}.{field} is not a SHA-256 digest",
            )
    reason = value.get("failure_reason")
    if not isinstance(reason, str) or reason not in policy.failure_reasons:
        _fail(
            "attempt-recovery-evidence",
            f"{label}.failure_reason is outside the exact closed set",
        )
    collected_at = value.get("collected_at")
    if (
        not isinstance(collected_at, str)
        or not collected_at
        or len(collected_at) > 256
    ):
        _fail(
            "attempt-recovery-evidence",
            f"{label}.collected_at is invalid",
        )
    return dict(value)


def _recovery_receipt_sha256(receipt: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(receipt) + b"\n").hexdigest()


def _exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], *, label: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        _fail(
            "schema",
            f"{label} key set differs: missing={missing}, unknown={unknown}",
        )


def _schema_version(
    value: Mapping[str, Any], *, profile: DomainProfile[Any, Any], label: str,
) -> str:
    schema_version = value.get("schema_version")
    if not isinstance(schema_version, str) or schema_version not in profile.schema.readable:
        _fail("attempt-registry-schema", f"{label}.schema_version is unsupported")
    return schema_version


def _is_chained_keys(keys: frozenset[str]) -> bool:
    return _CHAIN_KEYS <= keys


def _assert_chain(
    value: Mapping[str, Any], *, label: str,
    expected_event_index: int | None = None,
    expected_previous_event_sha256: str | None = None,
) -> None:
    event_index = value.get("event_index")
    if type(event_index) is not int or event_index < 0:
        _fail("attempt-event-chain", f"{label}.event_index is invalid")
    if expected_event_index is not None and event_index != expected_event_index:
        _fail("attempt-event-chain", f"{label}.event_index is not monotonic")
    previous = _digest(
        value.get("previous_event_sha256"),
        label=f"{label}.previous_event_sha256",
    )
    if expected_previous_event_sha256 is not None and previous != expected_previous_event_sha256:
        _fail(
            "attempt-event-chain",
            f"{label}.previous_event_sha256 differs from the preceding event",
        )
    actual = _digest(value.get("event_sha256"), label=f"{label}.event_sha256")
    if actual != event_sha256(value):
        _fail("attempt-event-chain", f"{label}.event_sha256 differs from its payload")


def _safe_relative_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/"):
        _fail("effective-binding", f"{label} must be a relative repository path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        _fail("effective-binding", f"{label} is not a safe repository path")
    if ".git" in path.parts:
        _fail("effective-binding", f"{label} must not contain a .git component")
    return path.as_posix()


def _normalize_slot(
    profile: DomainProfile[SlotT, Any], value: object, *, label: str,
) -> SlotT:
    return profile.slot_codec.parse(value, label=label)


def _assert_slot_layout(
    slots: Sequence[SlotT], *, profile: DomainProfile[SlotT, Any],
) -> None:
    slot_ids: set[Hashable] = set()
    groups: dict[SeriesKey, list[int]] = {}
    for slot in slots:
        slot_id = profile.slot_codec.slot_id(slot)
        if slot_id in slot_ids:
            _fail("attempt-registry-genesis", "genesis reuses a slot_id")
        slot_ids.add(slot_id)
        groups.setdefault(profile.slot_codec.series_key(slot), []).append(
            profile.slot_codec.attempt_ordinal(slot)
        )
    if not slots:
        _fail("attempt-registry-genesis", "genesis must close a non-empty slot set")
    for indexes in groups.values():
        if sorted(indexes) != list(range(len(indexes))):
            _fail(
                "attempt-registry-genesis",
                "slot attempt_index values must be a contiguous zero-based set",
            )
        limit = profile.transition_policy.max_series_attempts
        if limit is not None and len(indexes) > limit:
            _fail(
                "attempt-registry-genesis",
                "slot attempt_index values exceed the profile series limit",
            )


def _genesis_freeze_id(
    genesis: Mapping[str, Any], *, profile: DomainProfile[Any, Any],
    required: bool,
) -> str | None:
    if profile.freeze_id_from_genesis is not None:
        value: object = profile.freeze_id_from_genesis(genesis)
    else:
        value = genesis.get("freeze_id")
    if value is None and not required:
        return None
    if value is None:
        _fail(
            "attempt-registry-profile",
            "profile cannot derive the capability freeze identifier from genesis",
        )
    return _text(value, label="attempt registry genesis.freeze_id")


def _event_keys(
    profile: DomainProfile[Any, Any], *, schema_version: str, event: str,
) -> frozenset[str]:
    keys = profile.schema.event_keys.get(schema_version, {}).get(event)
    if keys is None:
        _fail("attempt-registry-schema", f"event is unavailable in {schema_version}")
    return keys


def _slot_identity_fields(
    profile: DomainProfile[SlotT, Any], *, slot: SlotT,
    schema_version: str, event: str,
) -> RegistryRow:
    expected = _event_keys(
        profile, schema_version=schema_version, event=event,
    )
    serialized = profile.slot_codec.to_json(slot)
    # schedule_row_sha256 is checked independently against the frozen slot.  It
    # must not participate in slot lookup, or a tamper would be misreported as
    # an undeclared slot rather than a replaced schedule binding.
    keys = (profile.slot_codec.exact_keys & expected) - {
        "schedule_row_sha256",
    }
    return {key: serialized[key] for key in keys}


def _slot_for_row(
    row: Mapping[str, Any], *, slots: Sequence[SlotT],
    profile: DomainProfile[SlotT, Any],
) -> tuple[Hashable, SlotT]:
    matches: list[SlotT] = []
    for slot in slots:
        identity = _slot_identity_fields(
            profile,
            slot=slot,
            schema_version=str(row["schema_version"]),
            event=str(row["event"]),
        )
        if identity and all(row.get(key) == value for key, value in identity.items()):
            matches.append(slot)
    if len(matches) != 1:
        serialized_keys = (
            profile.slot_codec.exact_keys & frozenset(row)
        ) - {"schedule_row_sha256"}
        reference: object
        if "slot_id" in row:
            reference = row.get("slot_id")
        else:
            reference = tuple((key, row.get(key)) for key in sorted(serialized_keys))
        _fail(
            "attempt-slot",
            f"attempt registry references an undeclared slot: {reference}",
        )
    slot = matches[0]
    return profile.slot_codec.slot_id(slot), slot


def _row_is_for_slot(
    row: Mapping[str, Any], *, slot: SlotT,
    profile: DomainProfile[SlotT, Any],
) -> bool:
    identity = _slot_identity_fields(
        profile,
        slot=slot,
        schema_version=str(row["schema_version"]),
        event=str(row["event"]),
    )
    return bool(identity) and all(
        row.get(key) == value for key, value in identity.items()
    )


def _event_context_fields(
    genesis: Mapping[str, Any], *, expected: frozenset[str],
) -> RegistryRow:
    excluded = {"schema_version", "event"} | _CHAIN_KEYS
    return {
        key: genesis[key]
        for key in expected & frozenset(genesis)
        if key not in excluded
    }


def _registry_path(
    profile: DomainProfile[Any, Any], context: Mapping[str, Any],
) -> str:
    template = profile.layout.registry_path.as_posix()
    try:
        return template.format_map(context)
    except (KeyError, ValueError) as exc:
        _fail(
            "attempt-registry-profile",
            f"registry path template cannot be resolved: {exc}",
        )


def _event_payload(
    *, profile: DomainProfile[SlotT, BindingT],
    genesis: Mapping[str, Any], event: str, slot: SlotT,
    binding: BindingT | None = None,
    fields: Mapping[str, Any] | None = None,
) -> RegistryRow:
    schema_version = profile.schema.current
    expected = _event_keys(
        profile, schema_version=schema_version, event=event,
    )
    value: RegistryRow = {
        "schema_version": schema_version,
        "event": event,
        **_event_context_fields(genesis, expected=expected),
        **_slot_identity_fields(
            profile, slot=slot, schema_version=schema_version, event=event,
        ),
    }
    if binding is not None:
        value.update(profile.binding_codec.to_event_fields(binding))
    if fields is not None:
        value.update(fields)
    # The chain fields are appended after construction.  Exact-key validation
    # here catches a profile/codec mismatch before hashing an invalid row.
    _exact_keys(value, expected - _CHAIN_KEYS, label=f"{event} event")
    return value


def _parse_genesis(
    value: object, *, profile: DomainProfile[SlotT, BindingT], label: str,
) -> tuple[RegistryRow, tuple[SlotT, ...], BindingT | None]:
    if not isinstance(value, Mapping):
        _fail("attempt-registry-schema", f"{label} is not an object")
    schema_version = _schema_version(value, profile=profile, label=label)
    expected = profile.schema.genesis_keys.get(schema_version)
    if expected is None:
        _fail("attempt-registry-schema", f"{label}.schema_version is unsupported")
    _exact_keys(value, expected, label=label)
    if value.get("event") != "freeze":
        _fail("attempt-registry-genesis", f"{label}.event is not freeze")
    if _is_chained_keys(expected):
        _assert_chain(
            value, label=label, expected_event_index=0,
            expected_previous_event_sha256=_ZERO_SHA256,
        )
    result = dict(value)
    if "freeze_id" in expected:
        result["freeze_id"] = _text(
            value.get("freeze_id"), label=f"{label}.freeze_id",
        )
    if "manifest_path" in expected:
        result["manifest_path"] = _safe_relative_path(
            value.get("manifest_path"), label=f"{label}.manifest_path",
        )
    if "manifest_sha256" in expected:
        result["manifest_sha256"] = _digest(
            value.get("manifest_sha256"), label=f"{label}.manifest_sha256",
        )
    if (
        "root_path" in expected
        and value.get("root_path") != _registry_path(profile, value)
    ):
        _fail("attempt-registry-genesis", f"{label}.root_path is not canonical")
    if "retryable_failure_reasons" in expected:
        reasons = value.get("retryable_failure_reasons")
        if (
            not isinstance(reasons, list)
            or any(type(reason) is not str or not reason for reason in reasons)
            or len(reasons) != len(set(reasons))
            or reasons != sorted(reasons)
            or frozenset(reasons) != profile.retryable_reasons
        ):
            _fail(
                "attempt-registry-genesis",
                f"{label}.retryable_failure_reasons is not the exact closed set",
            )
        result["retryable_failure_reasons"] = list(reasons)
    if "max_consumptions_per_budget_key" in expected:
        maximum = value.get("max_consumptions_per_budget_key")
        if (
            type(maximum) is not int
            or maximum < 0
            or maximum
            != profile.transition_policy.max_consumptions_per_budget_key
        ):
            _fail(
                "attempt-registry-genesis",
                f"{label}.max_consumptions_per_budget_key differs from the profile",
            )
    if "recovery_policy_sha256" in expected:
        recovery_policy_sha256 = _digest(
            value.get("recovery_policy_sha256"),
            label=f"{label}.recovery_policy_sha256",
        )
        if recovery_policy_sha256 != _recovery_policy_sha256(profile):
            _fail(
                "attempt-registry-genesis",
                f"{label}.recovery_policy_sha256 differs from the current profile",
            )
        result["recovery_policy_sha256"] = recovery_policy_sha256
    raw_slots = value.get("slots")
    if not isinstance(raw_slots, list):
        _fail("attempt-registry-genesis", f"{label}.slots is not an array")
    slots = tuple(
        _normalize_slot(profile, slot, label=f"{label}.slots[{index}]")
        for index, slot in enumerate(raw_slots)
    )
    if schema_version == "p3-8c-attempt-registry/v3":
        # A v3 root is accepted only when every declared slot names one shared
        # positive preregistration generation.  A missing or mixed generation
        # is rejected without changing the domain-independent series key.
        generations = [
            slot.get("prereg_generation")
            if isinstance(slot, Mapping) else None
            for slot in slots
        ]
        if (
            any(type(generation) is not int or generation < 1
                for generation in generations)
            or len(set(generations)) != 1
        ):
            _fail(
                "attempt-prereg-generation",
                "v3 genesis slots do not share one positive prereg_generation",
            )
    elif schema_version in {
        "p3-8c-attempt-registry/v1",
        "p3-8c-attempt-registry/v2",
    } and any(
        isinstance(slot, Mapping) and "prereg_generation" in slot
        for slot in slots
    ):
        _fail(
            "attempt-registry-schema",
            "legacy 8c genesis slot carries prereg_generation",
        )
    _assert_slot_layout(slots, profile=profile)
    result["slots"] = [profile.slot_codec.to_json(slot) for slot in slots]
    genesis_binding: BindingT | None = None
    if profile.binding_codec.event_keys <= expected:
        genesis_binding = profile.binding_codec.parse(value, label=label)
    return result, slots, genesis_binding


def _parse_row(
    value: object, *, profile: DomainProfile[SlotT, BindingT],
    label: str, freeze_id: str | None,
) -> tuple[RegistryRow, BindingT | None]:
    if not isinstance(value, Mapping):
        _fail("attempt-registry-schema", f"{label} is not an object")
    schema_version = _schema_version(value, profile=profile, label=label)
    event = value.get("event")
    event_table = profile.schema.event_keys.get(schema_version, {})
    expected = event_table.get(event) if isinstance(event, str) else None
    if expected is None:
        _fail("attempt-registry-schema", f"{label}.event is unknown")
    if event not in _CORE_SEMANTIC_EVENTS:
        _fail(
            "attempt-registry-semantic",
            f"{label}.event has no core semantic handler",
        )
    _exact_keys(value, expected, label=label)
    if _is_chained_keys(expected):
        _assert_chain(value, label=label)
    if "freeze_id" in expected and value.get("freeze_id") != freeze_id:
        _fail("attempt-registry-binding", f"{label}.freeze_id differs from genesis")
    if event == "pre-observation-seal":
        if "slot_id" in expected:
            _text(value.get("slot_id"), label=f"{label}.slot_id")
        _digest(value.get("start_event_sha256"), label=f"{label}.start_event_sha256")
        _digest(
            value.get("run_start_receipt_sha256"),
            label=f"{label}.run_start_receipt_sha256",
        )
        parse_process_identity(
            value.get("process_identity"), label=f"{label}.process_identity",
            exact_keys=profile.process_identity_keys,
        )
        _digest(
            value.get("schedule_row_sha256"),
            label=f"{label}.schedule_row_sha256",
        )
        return dict(value), None
    if event == "observation-start":
        if "slot_id" in expected:
            _text(value.get("slot_id"), label=f"{label}.slot_id")
        _digest(
            value.get("classification_event_sha256"),
            label=f"{label}.classification_event_sha256",
        )
        return dict(value), None

    if event == "recovery":
        if "slot_id" in expected:
            _text(value.get("slot_id"), label=f"{label}.slot_id")
        binding = (
            profile.binding_codec.parse(value, label=label)
            if profile.binding_codec.event_keys <= expected else None
        )
        start_event_sha256 = _digest(
            value.get("start_event_sha256"),
            label=f"{label}.start_event_sha256",
        )
        receipt = _parse_recovery_receipt(
            value.get("scheduler_accounting_receipt"),
            profile=profile,
            label=f"{label}.scheduler_accounting_receipt",
        )
        receipt_sha256 = _digest(
            value.get("scheduler_accounting_receipt_sha256"),
            label=f"{label}.scheduler_accounting_receipt_sha256",
        )
        if receipt_sha256 != _recovery_receipt_sha256(receipt):
            _fail(
                "attempt-recovery-evidence",
                f"{label}.scheduler_accounting_receipt_sha256 differs "
                "from the nested receipt",
            )
        reason = value.get("failure_reason")
        if reason != receipt["failure_reason"]:
            _fail(
                "attempt-recovery-evidence",
                f"{label}.failure_reason differs from the nested receipt",
            )
        recoverer_process_identity = parse_process_identity(
            value.get("recoverer_process_identity"),
            label=f"{label}.recoverer_process_identity",
            exact_keys=profile.process_identity_keys,
        )
        recovered_at = _text(
            value.get("recovered_at"), label=f"{label}.recovered_at",
        )
        return {
            **dict(value),
            "start_event_sha256": start_event_sha256,
            "scheduler_accounting_receipt": receipt,
            "scheduler_accounting_receipt_sha256": receipt_sha256,
            "recoverer_process_identity": recoverer_process_identity,
            "recovered_at": recovered_at,
        }, binding

    if "slot_id" in expected:
        _text(value.get("slot_id"), label=f"{label}.slot_id")
    binding = (
        profile.binding_codec.parse(value, label=label)
        if profile.binding_codec.event_keys <= expected else None
    )
    if event == "start":
        _digest(
            value.get("run_start_receipt_sha256"),
            label=f"{label}.run_start_receipt_sha256",
        )
        process_identity = parse_process_identity(
            value.get("process_identity"), label=f"{label}.process_identity",
            exact_keys=profile.process_identity_keys,
        )
        schedule = _digest(
            value.get("schedule_row_sha256"),
            label=f"{label}.schedule_row_sha256",
        )
        started_at = _text(value.get("started_at"), label=f"{label}.started_at")
        return {
            **dict(value),
            "process_identity": process_identity,
            "schedule_row_sha256": schedule, "started_at": started_at,
        }, binding
    if event == "classification":
        digest_fields = (
            "classification_receipt_sha256", "capability_digest_sha256",
            "authority_policy_sha256", "external_evidence_sha256",
        )
        if "pre_observation_seal_sha256" in expected:
            digest_fields += ("pre_observation_seal_sha256",)
        for field in digest_fields:
            _digest(value.get(field), label=f"{label}.{field}")
        _text(value.get("authority_id"), label=f"{label}.authority_id")
        _text(value.get("classified_at"), label=f"{label}.classified_at")
        reason_field = (
            "pre_observation_failure_reason"
            if "pre_observation_failure_reason" in expected else "failure_reason"
        )
        reason = value.get(reason_field)
        if reason is not None:
            _text(reason, label=f"{label}.{reason_field}")
        if (
            "performance_output_read" in expected
            and value.get("performance_output_read") is not False
        ):
            _fail(
                "attempt-classification",
                f"{label}.performance_output_read must be false",
            )
        return dict(value), binding

    for field in (
        "classification_receipt_sha256", "raw_output_sha256",
        "report_sha256", "observation_sha256",
    ):
        _digest(value.get(field), label=f"{label}.{field}", nullable=True)
    if "observation_start_event_sha256" in expected:
        _digest(
            value.get("observation_start_event_sha256"),
            label=f"{label}.observation_start_event_sha256", nullable=True,
        )
    if "pre_observation_failure_reason_echo" in expected:
        echo = value.get("pre_observation_failure_reason_echo")
        if echo is not None:
            _text(echo, label=f"{label}.pre_observation_failure_reason_echo")
    if "terminal_evidence_sha256" in expected:
        _digest(
            value.get("terminal_evidence_sha256"),
            label=f"{label}.terminal_evidence_sha256",
        )
    if "measurement_retry_reason" in expected:
        measurement_reason = value.get("measurement_retry_reason")
        if measurement_reason is not None:
            _text(
                measurement_reason,
                label=f"{label}.measurement_retry_reason",
            )
    status = value.get("terminal_status")
    if status not in profile.statuses:
        _fail(
            "attempt-null-matrix",
            f"{label}.terminal_status is outside the closed set",
        )
    primary_value = value.get("primary_value")
    if primary_value is not None:
        try:
            canonical_json_bytes(primary_value)
        except AttemptRegistryCoreError as exc:
            raise AttemptRegistryCoreError(
                f"[attempt-null-matrix] {label}.primary_value is not JSON data"
            ) from exc
    reason = value.get("failure_reason")
    if reason is not None:
        _text(reason, label=f"{label}.failure_reason")
    _text(value.get("finished_at"), label=f"{label}.finished_at")
    _digest(
        value.get("schedule_row_sha256"), label=f"{label}.schedule_row_sha256",
    )
    parse_process_identity(
        value.get("process_identity"), label=f"{label}.process_identity",
        exact_keys=profile.process_identity_keys,
    )
    return dict(value), binding


def _assert_null_matrix(
    row: Mapping[str, Any], *, retryable_reasons: frozenset[str],
    retryable_reason_field: str = "failure_reason", label: str,
) -> None:
    status = row["terminal_status"]
    raw_output = row.get("raw_output_sha256")
    classification = row.get("classification_receipt_sha256")
    if raw_output is None or classification is None:
        _fail(
            "attempt-null-matrix",
            f"{label} requires non-null raw output and classification receipt digests",
        )
    if status == "observed":
        if (
            row.get("report_sha256") is None
            or row.get("observation_sha256") is None
            or row.get("primary_value") is None
            or row.get("failure_reason") is not None
            or row.get(retryable_reason_field) is not None
        ):
            _fail("attempt-null-matrix", f"{label} observed null matrix differs")
    elif status == "retryable-failure":
        reason = row.get(retryable_reason_field)
        if (
            row.get("report_sha256") is None
            or row.get("observation_sha256") is not None
            or row.get("primary_value") is not None
            or not isinstance(reason, str)
            or reason not in retryable_reasons
        ):
            _fail(
                "attempt-null-matrix",
                f"{label} retryable-failure null matrix differs",
            )
    elif status == "terminal-failure":
        reason = row.get(retryable_reason_field)
        if (
            row.get("observation_sha256") is not None
            or row.get("primary_value") is not None
            or not isinstance(reason, str)
            or reason in retryable_reasons
        ):
            _fail(
                "attempt-null-matrix",
                f"{label} terminal-failure null matrix differs",
            )
    elif (
        row.get("report_sha256") is not None
        or row.get("observation_sha256") is not None
        or row.get("primary_value") is not None
        or row.get("failure_reason") is not None
        or row.get(retryable_reason_field) is not None
    ):
        _fail("attempt-null-matrix", f"{label} not-consumed null matrix differs")


def _validated_budget_counts(
    initial_started_budget_counts: Mapping[Hashable, int] | None,
) -> BudgetCounts:
    if initial_started_budget_counts is None:
        return {}
    if not isinstance(initial_started_budget_counts, Mapping):
        _fail(
            "attempt-slot-order",
            "initial started budget counts are not a mapping",
        )
    counts: BudgetCounts = {}
    for budget_key, count in initial_started_budget_counts.items():
        if type(count) is not int or count < 0:
            _fail(
                "attempt-slot-order",
                "initial started budget count is invalid",
            )
        counts[budget_key] = count
    return counts


def _assert_registry_rows_with_budget_counts(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]:
    """Replay one genesis/lifecycle sequence under ``profile``."""
    started_budget_counts = _validated_budget_counts(
        initial_started_budget_counts
    )
    if not rows or rows[0].get("event") != "freeze":
        _fail(
            "attempt-registry-genesis",
            "attempt registry must begin with one freeze row",
        )
    genesis, parsed_slots, genesis_binding = _parse_genesis(
        rows[0], profile=profile, label="attempt registry genesis",
    )
    schema_version = genesis["schema_version"]
    genesis_keys = profile.schema.genesis_keys[schema_version]
    last_hash: str | None = (
        genesis["event_sha256"] if _is_chained_keys(genesis_keys) else None
    )
    starts: dict[Hashable, Mapping[str, Any]] = {}
    seals: dict[Hashable, Mapping[str, Any]] = {}
    classifications: dict[Hashable, Mapping[str, Any]] = {}
    observations: dict[Hashable, Mapping[str, Any]] = {}
    terminals: dict[Hashable, Mapping[str, Any]] = {}
    recoveries: dict[Hashable, Mapping[str, Any]] = {}
    binding_identity: Hashable | None = (
        profile.binding_codec.identity(genesis_binding)
        if genesis_binding is not None else None
    )
    expected_identity = (
        profile.binding_codec.identity(expected_binding)
        if expected_binding is not None else None
    )
    freeze_id = _genesis_freeze_id(genesis, profile=profile, required=False)

    def assert_expected_binding(parsed_binding: BindingT) -> None:
        if expected_binding is None:
            return
        if profile.binding_mismatch is not None:
            mismatch = profile.binding_mismatch(parsed_binding, expected_binding)
        else:
            mismatch = (
                None
                if profile.binding_codec.identity(parsed_binding) == expected_identity
                else "attempt row binding differs from expected"
            )
        if mismatch is not None:
            _fail("attempt-binding", mismatch)

    if genesis_binding is not None:
        assert_expected_binding(genesis_binding)

    for row_index, raw in enumerate(rows[1:], 1):
        line_number = row_index + 1
        row, parsed_binding = _parse_row(
            raw, profile=profile,
            label=f"attempt registry line {line_number}",
            freeze_id=freeze_id,
        )
        row_schema = row["schema_version"]
        if row_schema != schema_version:
            _fail(
                "attempt-registry-schema",
                "attempt registry row schema_version differs from genesis",
            )
        row_keys = profile.schema.event_keys[row_schema][row["event"]]
        if _is_chained_keys(row_keys):
            expected_previous = last_hash or _ZERO_SHA256
            _assert_chain(
                row, label=f"attempt registry line {line_number}",
                expected_event_index=row_index,
                expected_previous_event_sha256=expected_previous,
            )
            last_hash = row["event_sha256"]

        slot_id, slot = _slot_for_row(
            row, slots=parsed_slots, profile=profile,
        )
        if parsed_binding is not None:
            identity = profile.binding_codec.identity(parsed_binding)
            if binding_identity is None:
                binding_identity = identity
            elif identity != binding_identity:
                _fail("attempt-binding", profile.binding_conflict_message)
            assert_expected_binding(parsed_binding)

        event = row["event"]
        if event == "start":
            if slot_id in starts or slot_id in terminals or slot_id in recoveries:
                _fail("attempt-slot", "slot was reserved more than once")
            if row["schedule_row_sha256"] != profile.slot_codec.schedule_sha256(slot):
                _fail(
                    "attempt-slot", "start schedule row hash differs from genesis",
                )
            ordinal = profile.slot_codec.attempt_ordinal(slot)
            policy = profile.transition_policy
            if policy.max_series_attempts is not None and ordinal >= policy.max_series_attempts:
                _fail("attempt-slot-order", "attempt exceeds the profile series limit")
            if ordinal > 0 and policy.require_previous_terminal:
                previous_slots = [
                    candidate for candidate in parsed_slots
                    if profile.slot_codec.series_key(candidate)
                    == profile.slot_codec.series_key(slot)
                    and profile.slot_codec.attempt_ordinal(candidate) == ordinal - 1
                ]
                if len(previous_slots) != 1:
                    _fail(
                        "attempt-slot-order",
                        "only the next slot after a completed retryable failure may start",
                    )
                previous_slot_id = profile.slot_codec.slot_id(previous_slots[0])
                if previous_slot_id in terminals:
                    previous_terminal = terminals[previous_slot_id]
                    if previous_terminal["terminal_status"] != "retryable-failure":
                        _fail(
                            "attempt-slot-order",
                            "a slot after a non-retryable outcome cannot be consumed",
                        )
                    if not policy.retryable_terminal_opens_next_attempt:
                        _fail(
                            "attempt-slot-order",
                            "a retryable terminal cannot authorize the next attempt",
                        )
                    if (
                        policy.forbid_retry_after_observation
                        and previous_terminal.get(
                            "observation_start_event_sha256"
                        ) is not None
                    ):
                        _fail(
                            "attempt-slot-order",
                            "a retryable failure after observation cannot authorize a retry",
                        )
                elif previous_slot_id not in recoveries:
                    _fail(
                        "attempt-slot-order",
                        "only the next slot after a completed retryable failure may start",
                    )
            if policy.budget_key is not None:
                budget_key = policy.budget_key(slot)
                count = started_budget_counts.get(budget_key, 0)
                limit = policy.max_consumptions_per_budget_key
                if limit is not None and count >= limit:
                    _fail(
                        "attempt-slot-order",
                        "attempt consumption exceeds the profile budget",
                    )
                started_budget_counts[budget_key] = count + 1
            starts[slot_id] = row
        elif event == "pre-observation-seal":
            if slot_id in recoveries:
                _fail(
                    "attempt-recovery-order",
                    "pre-observation seal follows verified recovery",
                )
            if slot_id not in starts or slot_id in seals:
                _fail(
                    "attempt-phase-order",
                    "pre-observation seal does not follow exactly one start",
                )
            if slot_id in classifications or slot_id in terminals:
                _fail("attempt-phase-order", "pre-observation seal is out of phase")
            start = starts[slot_id]
            if row["start_event_sha256"] != start["event_sha256"]:
                _fail("attempt-slot", "pre-observation seal start binding differs")
            if row["run_start_receipt_sha256"] != start["run_start_receipt_sha256"]:
                _fail("attempt-slot", "pre-observation seal receipt binding differs")
            if row["schedule_row_sha256"] != start["schedule_row_sha256"]:
                _fail("attempt-slot", "pre-observation seal schedule binding differs")
            if canonical_json_bytes(row["process_identity"]) != canonical_json_bytes(
                start["process_identity"]
            ):
                _fail("attempt-slot", "pre-observation seal process binding differs")
            seals[slot_id] = row
        elif event == "classification":
            if slot_id in recoveries:
                _fail(
                    "attempt-recovery-order",
                    "classification follows verified recovery",
                )
            if slot_id not in starts or slot_id in classifications:
                _fail(
                    "attempt-phase-order",
                    "classification does not follow exactly one start",
                )
            if slot_id in terminals or slot_id in observations:
                _fail("attempt-phase-order", "classification is out of phase")
            assert parsed_binding is not None
            capability_freeze_id = _genesis_freeze_id(
                genesis, profile=profile, required=True,
            )
            expected_digest = capability_digest(
                profile=profile, schema_version=row_schema,
                freeze_id=capability_freeze_id, slot=slot,
                binding=parsed_binding,
            )
            if row["capability_digest_sha256"] != expected_digest:
                _fail(
                    "attempt-classification",
                    "classification capability digest differs",
                )
            if "pre_observation_seal_sha256" in row:
                if slot_id not in seals:
                    _fail(
                        "attempt-phase-order",
                        "classification requires a preceding pre-observation seal",
                    )
                if row["pre_observation_seal_sha256"] != seals[slot_id]["event_sha256"]:
                    _fail(
                        "attempt-slot",
                        "classification pre-observation seal binding differs",
                    )
            classifications[slot_id] = row
        elif event == "observation-start":
            if slot_id in recoveries:
                _fail(
                    "attempt-recovery-order",
                    "observation-start follows verified recovery",
                )
            if slot_id not in classifications or slot_id in observations:
                _fail(
                    "attempt-phase-order",
                    "observation-start does not follow exactly one classification",
                )
            if slot_id in terminals:
                _fail("attempt-phase-order", "observation-start follows terminal")
            classification = classifications[slot_id]
            if row["classification_event_sha256"] != classification["event_sha256"]:
                _fail(
                    "attempt-slot",
                    "observation-start classification binding differs",
                )
            observations[slot_id] = row
        elif event == "terminal":
            if slot_id in recoveries:
                _fail(
                    "attempt-recovery-order",
                    "terminal follows verified recovery",
                )
            if slot_id not in starts or slot_id not in classifications:
                _fail(
                    "attempt-phase-order",
                    "terminal does not follow start and classification",
                )
            if slot_id in terminals:
                _fail("attempt-terminal", "slot has more than one terminal row")
            start = starts[slot_id]
            classification = classifications[slot_id]
            if row["classification_receipt_sha256"] != classification[
                "classification_receipt_sha256"
            ]:
                _fail("attempt-slot", "terminal classification receipt was replaced")
            if row["schedule_row_sha256"] != start["schedule_row_sha256"]:
                _fail("attempt-slot", "terminal schedule row hash was replaced")
            if canonical_json_bytes(row["process_identity"]) != canonical_json_bytes(
                start["process_identity"]
            ):
                _fail("attempt-slot", "terminal process identity was replaced")
            if "observation_start_event_sha256" in row:
                expected_observation = (
                    observations[slot_id]["event_sha256"]
                    if slot_id in observations else None
                )
                if row["observation_start_event_sha256"] != expected_observation:
                    _fail(
                        "attempt-slot",
                        "terminal observation-start binding differs",
                    )
                if row["terminal_status"] == "observed" and expected_observation is None:
                    _fail(
                        "attempt-phase-order",
                        "observed terminal requires observation-start",
                    )
                if (
                    row["terminal_status"] == "terminal-failure"
                    and row["report_sha256"] is not None
                    and expected_observation is None
                ):
                    _fail(
                        "attempt-phase-order",
                        "terminal-failure with a report requires observation-start",
                    )
                classification_reason = classification[
                    "pre_observation_failure_reason"
                ]
                if row["pre_observation_failure_reason_echo"] != classification_reason:
                    _fail(
                        "attempt-classification",
                        "terminal pre-observation failure echo differs from classification",
                    )
                if (
                    profile.transition_policy.require_terminal_reason_equals_classification
                    and row["failure_reason"] != classification_reason
                ):
                    _fail(
                        "attempt-classification",
                        "terminal failure reason differs from classification",
                    )
            elif row["failure_reason"] != classification["failure_reason"]:
                _fail(
                    "attempt-classification",
                    "terminal failure reason differs from receipt",
                )
            _assert_null_matrix(
                row,
                retryable_reasons=frozenset(genesis["retryable_failure_reasons"]),
                retryable_reason_field=profile.retryable_reason_field,
                label=f"attempt registry line {line_number}",
            )
            if profile.terminal_row_validator is not None:
                profile.terminal_row_validator(row)
            terminals[slot_id] = row
        elif event == "recovery":
            if slot_id not in starts:
                _fail(
                    "attempt-recovery-order",
                    "recovery does not follow exactly one start",
                )
            if slot_id in terminals:
                _fail(
                    "attempt-recovery-order",
                    "recovery follows terminal",
                )
            if slot_id in recoveries:
                _fail(
                    "attempt-recovery-order",
                    "slot has more than one recovery row",
                )
            start = starts[slot_id]
            receipt = row["scheduler_accounting_receipt"]
            if row["start_event_sha256"] != start["event_sha256"]:
                _fail(
                    "attempt-recovery-fence",
                    "recovery start-event hash differs from the slot start",
                )
            if receipt["target_start_event_sha256"] != start["event_sha256"]:
                _fail(
                    "attempt-recovery-evidence",
                    "scheduler receipt targets a different start event",
                )
            if _recovery_comparison_identity(
                row["recoverer_process_identity"]
            ) == _recovery_comparison_identity(start["process_identity"]):
                _fail(
                    "attempt-recovery-fence",
                    "recoverer process identity matches the start owner",
                )
            recoveries[slot_id] = row
        else:
            _fail(
                "attempt-registry-semantic",
                f"attempt registry line {line_number}.event has no core "
                "semantic handler",
            )
    return tuple(dict(row) for row in rows), started_budget_counts


def assert_registry_rows(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
) -> RegistryRows:
    """Replay one genesis/lifecycle sequence under ``profile``."""
    validated, _counts = _assert_registry_rows_with_budget_counts(
        rows, profile=profile, expected_binding=expected_binding,
    )
    return validated


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"), object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except AttemptRegistryCoreError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _load_registry_bytes_with_budget_counts(
    data: bytes, *, profile: DomainProfile[SlotT, BindingT], label: str,
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]:
    if not data or not data.endswith(b"\n"):
        _fail(
            "attempt-registry-framing",
            f"{label} must be non-empty and newline terminated",
        )
    rows: list[RegistryRow] = []
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail(
                "attempt-registry-framing",
                f"{label} has a blank line at {lineno}",
            )
        value = _decode_json(line, label=f"{label} line {lineno}")
        if not isinstance(value, Mapping) or canonical_json_bytes(value) != line:
            _fail(
                "attempt-registry-canonical",
                f"{label} line {lineno} is not canonical JSON",
            )
        rows.append(dict(value))
    return _assert_registry_rows_with_budget_counts(
        rows, profile=profile, expected_binding=expected_binding,
        initial_started_budget_counts=initial_started_budget_counts,
    )


def _load_registry_bytes(
    data: bytes, *, profile: DomainProfile[SlotT, BindingT], label: str,
    expected_binding: BindingT | None = None,
) -> RegistryRows:
    rows, _counts = _load_registry_bytes_with_budget_counts(
        data, profile=profile, label=label,
        expected_binding=expected_binding,
    )
    return rows


def load_attempt_registry(
    data: bytes, *, profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
) -> RegistryRows:
    """Parse canonical JSONL and replay it under one domain profile."""
    return _load_registry_bytes(
        data, profile=profile, label="attempt registry",
        expected_binding=expected_binding,
    )


def load_attempt_registry_with_budget_counts(
    data: bytes, *, profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]:
    """Parse and replay JSONL, seeded by prior generation budget counts."""
    return _load_registry_bytes_with_budget_counts(
        data, profile=profile, label="attempt registry",
        expected_binding=expected_binding,
        initial_started_budget_counts=initial_started_budget_counts,
    )


def create_attempt_registry_genesis(
    *, profile: DomainProfile[SlotT, BindingT], freeze_id: str | None = None,
    manifest_path: PurePosixPath | None = None,
    manifest_sha256: str | None = None,
    slots: Sequence[SlotT],
    retryable_failure_reasons: Sequence[str] | None = None,
    binding: BindingT | None = None,
) -> RegistryRows:
    """Build the single canonical freeze row for a declared slot set."""
    keys = profile.schema.genesis_keys[profile.schema.current]
    manifest_keys = frozenset({
        "freeze_id", "manifest_path", "manifest_sha256",
    })
    declared_manifest_keys = keys & manifest_keys
    if declared_manifest_keys and declared_manifest_keys != manifest_keys:
        _fail(
            "attempt-registry-profile",
            "genesis must declare either all or none of the manifest keys",
        )
    binding_manifest_overlap = (
        frozenset(profile.binding_codec.event_keys) & manifest_keys
    )
    if binding_manifest_overlap:
        _fail(
            "attempt-registry-profile",
            "binding codec overlaps manifest genesis keys",
        )
    if "freeze_id" in keys:
        _text(freeze_id, label="freeze_id")
    elif freeze_id is not None:
        _fail(
            "attempt-registry-genesis",
            "freeze_id is not declared by the domain profile",
        )
    if "manifest_sha256" in keys:
        _digest(manifest_sha256, label="manifest_sha256")
    elif manifest_sha256 is not None:
        _fail(
            "attempt-registry-genesis",
            "manifest_sha256 is not declared by the domain profile",
        )
    manifest_relative: str | None = None
    if "manifest_path" in keys:
        if manifest_path is None:
            _fail(
                "attempt-registry-genesis",
                "manifest_path is required by the domain profile",
            )
        manifest_relative = _safe_relative_path(
            manifest_path.as_posix(), label="manifest_path",
        )
    elif manifest_path is not None:
        _fail(
            "attempt-registry-genesis",
            "manifest_path is not declared by the domain profile",
        )
    serialized_slots = [profile.slot_codec.to_json(slot) for slot in slots]
    reasons = list(
        profile.retryable_reasons
        if retryable_failure_reasons is None else retryable_failure_reasons
    )
    domain_fields = (
        {}
        if (
            profile.build_genesis_fields is None
            or not {
                "freeze_id", "manifest_path", "manifest_sha256",
            } <= keys
        )
        else dict(profile.build_genesis_fields(
            freeze_id, PurePosixPath(manifest_relative), manifest_sha256,
        ))
    )
    if binding is not None:
        domain_fields.update(profile.binding_codec.to_event_fields(binding))
    value: RegistryRow = {
        "schema_version": profile.schema.current,
        "event": "freeze",
        **domain_fields,
        "root_path": _registry_path(profile, domain_fields),
        "retryable_failure_reasons": sorted(reasons),
        "slots": serialized_slots,
    }
    if "max_consumptions_per_budget_key" in keys:
        value["max_consumptions_per_budget_key"] = (
            profile.transition_policy.max_consumptions_per_budget_key
        )
    if "recovery_policy_sha256" in keys:
        recovery_policy_sha256 = _recovery_policy_sha256(profile)
        if recovery_policy_sha256 is None:
            _fail(
                "attempt-registry-profile",
                "genesis requires a recovery policy",
            )
        value["recovery_policy_sha256"] = recovery_policy_sha256
    if _is_chained_keys(keys):
        value = chained_event_row(
            value, event_index=0, previous_event_sha256=_ZERO_SHA256,
        )
    parsed, _slots, _binding = _parse_genesis(
        value, profile=profile, label="attempt registry genesis",
    )
    genesis_freeze_id = _genesis_freeze_id(parsed, profile=profile, required=True)
    if freeze_id is not None and genesis_freeze_id != freeze_id:
        _fail(
            "attempt-binding",
            "genesis freeze_id differs from requested freeze_id",
        )
    return (parsed,)


def _slot_by_id(
    rows: Sequence[Mapping[str, Any]], *, profile: DomainProfile[SlotT, Any],
    slot_id: Hashable,
) -> SlotT:
    _genesis, slots, _binding = _parse_genesis(
        rows[0], profile=profile, label="attempt registry genesis",
    )
    matches = [slot for slot in slots if profile.slot_codec.slot_id(slot) == slot_id]
    if len(matches) != 1:
        _fail("attempt-slot", "slot_id was not declared by genesis")
    return matches[0]


def _append_event(
    rows: Sequence[Mapping[str, Any]], row: Mapping[str, Any], *,
    profile: DomainProfile[Any, Any],
) -> RegistryRow:
    keys = profile.schema.event_keys[profile.schema.current][str(row["event"])]
    if _is_chained_keys(keys):
        return chained_event_row(
            row, event_index=len(rows),
            previous_event_sha256=previous_event_sha256(rows),
        )
    return dict(row)


def reserve_attempt_slot(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT], freeze_id: str,
    slot_id: Hashable, binding: BindingT,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any], started_at: str,
) -> RegistryRows:
    """Return rows with one authorized start and pre-observation seal."""
    checked = assert_registry_rows(rows, profile=profile)
    genesis = checked[0]
    if _genesis_freeze_id(genesis, profile=profile, required=True) != freeze_id:
        _fail("attempt-binding", "slot reservation freeze_id differs from genesis")
    slot = _slot_by_id(checked, profile=profile, slot_id=slot_id)
    if any(
        row.get("event") == "start"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked[1:]
    ):
        _fail("attempt-slot", "slot was already reserved")
    _digest(run_start_receipt_sha256, label="run_start_receipt_sha256")
    checked_process = parse_process_identity(
        dict(process_identity), label="process_identity",
        exact_keys=profile.process_identity_keys,
    )
    _text(started_at, label="started_at")
    start = _append_event(
        checked,
        _event_payload(
            profile=profile, genesis=genesis, event="start", slot=slot,
            binding=binding, fields={
            "run_start_receipt_sha256": run_start_receipt_sha256,
            "process_identity": checked_process,
            "schedule_row_sha256": profile.slot_codec.schedule_sha256(slot),
            "started_at": started_at,
            },
        ),
        profile=profile,
    )
    candidate: RegistryRows = tuple(checked) + (start,)
    if "pre-observation-seal" in profile.schema.event_keys[profile.schema.current]:
        seal = _append_event(
            candidate,
            _event_payload(
                profile=profile, genesis=genesis,
                event="pre-observation-seal", slot=slot, fields={
                "start_event_sha256": start["event_sha256"],
                "run_start_receipt_sha256": start["run_start_receipt_sha256"],
                "process_identity": dict(start["process_identity"]),
                "schedule_row_sha256": start["schedule_row_sha256"],
                },
            ),
            profile=profile,
        )
        candidate += (seal,)
    return assert_registry_rows(candidate, profile=profile, expected_binding=binding)


def _classification_reason(row: Mapping[str, Any]) -> Any:
    return row.get("pre_observation_failure_reason", row.get("failure_reason"))


def _receipt_payload(
    *, profile: DomainProfile[Any, Any], schema_version: str,
    freeze_id: str, slot_id: Hashable, capability_digest_sha256: str,
    pre_observation_failure_reason: str | None, authority_id: str,
    authority_policy_sha256: str, external_evidence_sha256: str,
    classified_at: str, pre_observation_seal_sha256: str | None,
    slot: Any | None = None, genesis: Mapping[str, Any] | None = None,
) -> RegistryRow:
    expected = (
        profile.schema.receipt_keys.get(schema_version)
        if profile.schema.receipt_keys is not None else None
    )
    if expected is None:
        expected = (
            _event_keys(
                profile, schema_version=schema_version,
                event="classification",
            )
            - _CHAIN_KEYS
            - profile.binding_codec.event_keys
            - {"classification_receipt_sha256"}
        )
    candidate: RegistryRow = {
        "schema_version": schema_version, "event": "classification-receipt",
        "freeze_id": freeze_id, "slot_id": slot_id,
        "capability_digest_sha256": capability_digest_sha256,
        "authority_id": authority_id,
        "authority_policy_sha256": authority_policy_sha256,
        "external_evidence_sha256": external_evidence_sha256,
        "classified_at": classified_at,
    }
    if genesis is not None:
        candidate.update(_event_context_fields(genesis, expected=expected))
    if slot is not None:
        serialized = profile.slot_codec.to_json(slot)
        candidate.update({
            key: serialized[key]
            for key in profile.slot_codec.exact_keys & expected
            if key != "schedule_row_sha256"
        })
    if pre_observation_seal_sha256 is not None:
        candidate.update({
            "pre_observation_failure_reason": pre_observation_failure_reason,
            "pre_observation_seal_sha256": pre_observation_seal_sha256,
        })
    else:
        candidate.update({
            "failure_reason": pre_observation_failure_reason,
            "performance_output_read": False,
        })
    value = {key: candidate[key] for key in expected if key in candidate}
    _exact_keys(value, expected, label="classification receipt")
    return value


def classify_attempt(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT], freeze_id: str,
    slot_id: Hashable, binding: BindingT,
    capability_digest_sha256: str,
    pre_observation_failure_reason: str | None, authority_id: str,
    authority_policy_sha256: str, external_evidence_sha256: str,
    classified_at: str,
) -> tuple[RegistryRows, RegistryRow]:
    """Return candidate rows and the create-only receipt data."""
    checked = assert_registry_rows(rows, profile=profile, expected_binding=binding)
    if pre_observation_failure_reason is not None:
        _text(
            pre_observation_failure_reason,
            label="pre_observation_failure_reason",
        )
    authority_id = _text(authority_id, label="authority_id")
    _digest(authority_policy_sha256, label="authority_policy_sha256")
    _digest(external_evidence_sha256, label="external_evidence_sha256")
    classified_at = _text(classified_at, label="classified_at")
    genesis = checked[0]
    if _genesis_freeze_id(genesis, profile=profile, required=True) != freeze_id:
        _fail("attempt-binding", "classification freeze_id differs from genesis")
    slot = _slot_by_id(checked, profile=profile, slot_id=slot_id)
    expected_capability = capability_digest(
        profile=profile, schema_version=profile.schema.current,
        freeze_id=freeze_id, slot=slot, binding=binding,
    )
    if capability_digest_sha256 != expected_capability:
        _fail("attempt-capability", "slot capability digest was replaced")
    if any(
        row.get("event") == "recovery"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail(
            "attempt-recovery-order",
            "classification follows verified recovery",
        )
    if any(
        row.get("event") == "classification"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail("attempt-classification", "slot already has a classification receipt")
    seals = [
        row for row in checked
        if row.get("event") == "pre-observation-seal"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    seal_sha256 = seals[0]["event_sha256"] if len(seals) == 1 else None
    if "pre-observation-seal" in profile.schema.event_keys[profile.schema.current]:
        if len(seals) != 1:
            _fail(
                "attempt-phase-order",
                "classification requires exactly one pre-observation seal",
            )
    receipt = _receipt_payload(
        profile=profile, schema_version=profile.schema.current,
        freeze_id=freeze_id, slot_id=slot_id,
        capability_digest_sha256=capability_digest_sha256,
        pre_observation_failure_reason=pre_observation_failure_reason,
        authority_id=authority_id,
        authority_policy_sha256=authority_policy_sha256,
        external_evidence_sha256=external_evidence_sha256,
        classified_at=classified_at,
        pre_observation_seal_sha256=seal_sha256,
        slot=slot,
        genesis=genesis,
    )
    receipt_digest = hashlib.sha256(canonical_json_bytes(receipt) + b"\n").hexdigest()
    row_fields: RegistryRow = {
        "classification_receipt_sha256": receipt_digest,
        "capability_digest_sha256": capability_digest_sha256,
        "authority_id": authority_id,
        "authority_policy_sha256": authority_policy_sha256,
        "external_evidence_sha256": external_evidence_sha256,
        "classified_at": classified_at,
    }
    if seal_sha256 is not None:
        row_fields.update({
            "pre_observation_failure_reason": pre_observation_failure_reason,
            "pre_observation_seal_sha256": seal_sha256,
        })
    else:
        row_fields.update({
            "failure_reason": pre_observation_failure_reason,
            "performance_output_read": False,
        })
    row_payload = _event_payload(
        profile=profile, genesis=genesis, event="classification", slot=slot,
        binding=binding, fields=row_fields,
    )
    row = _append_event(checked, row_payload, profile=profile)
    candidate = tuple(checked) + (row,)
    return (
        assert_registry_rows(candidate, profile=profile, expected_binding=binding),
        receipt,
    )


def begin_attempt_observation(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT], freeze_id: str,
    slot_id: Hashable,
) -> RegistryRows:
    """Return rows with the observation boundary for one classified slot."""
    checked = assert_registry_rows(rows, profile=profile)
    genesis = checked[0]
    if _genesis_freeze_id(genesis, profile=profile, required=True) != freeze_id:
        _fail("attempt-binding", "observation freeze_id differs from genesis")
    slot = _slot_by_id(checked, profile=profile, slot_id=slot_id)
    if any(
        row.get("event") == "recovery"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail(
            "attempt-recovery-order",
            "observation-start follows verified recovery",
        )
    classifications = [
        row for row in checked
        if row.get("event") == "classification"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    observations = [
        row for row in checked
        if row.get("event") == "observation-start"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    terminals = [
        row for row in checked
        if row.get("event") == "terminal"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    if len(classifications) != 1:
        _fail(
            "attempt-phase-order",
            "observation-start requires exactly one classification",
        )
    if observations:
        _fail("attempt-phase-order", "slot already has observation-start")
    if terminals:
        _fail("attempt-phase-order", "observation-start follows terminal")
    classification = classifications[0]
    row = _append_event(
        checked,
        _event_payload(
            profile=profile, genesis=genesis, event="observation-start",
            slot=slot, fields={
            "classification_event_sha256": classification["event_sha256"],
            },
        ),
        profile=profile,
    )
    return assert_registry_rows(tuple(checked) + (row,), profile=profile)


def record_attempt_terminal(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT], freeze_id: str,
    slot_id: Hashable, binding: BindingT, terminal_status: str,
    raw_output_sha256: str, report_sha256: str | None,
    observation_sha256: str | None, primary_value: Any, finished_at: str,
    failure_reason: str | None = None,
    measurement_retry_reason: str | None = None,
    terminal_evidence_sha256: str | None = None,
) -> RegistryRows:
    """Return rows with one terminal event authorized by the profile."""
    checked = assert_registry_rows(rows, profile=profile, expected_binding=binding)
    genesis = checked[0]
    if _genesis_freeze_id(genesis, profile=profile, required=True) != freeze_id:
        _fail("attempt-binding", "terminal freeze_id differs from genesis")
    slot = _slot_by_id(checked, profile=profile, slot_id=slot_id)
    if any(
        row.get("event") == "recovery"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail(
            "attempt-recovery-order",
            "terminal follows verified recovery",
        )
    if terminal_status not in profile.statuses:
        _fail("attempt-terminal", "terminal_status is outside the closed set")
    _digest(raw_output_sha256, label="raw_output_sha256")
    _digest(report_sha256, label="report_sha256", nullable=True)
    _digest(observation_sha256, label="observation_sha256", nullable=True)
    _text(finished_at, label="finished_at")
    if failure_reason is not None:
        _text(failure_reason, label="failure_reason")
    if measurement_retry_reason is not None:
        _text(measurement_retry_reason, label="measurement_retry_reason")
    if terminal_evidence_sha256 is not None:
        _digest(
            terminal_evidence_sha256, label="terminal_evidence_sha256",
        )
    starts = [
        row for row in checked
        if row.get("event") == "start"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    classifications = [
        row for row in checked
        if row.get("event") == "classification"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    if len(starts) != 1 or len(classifications) != 1:
        _fail(
            "attempt-terminal", "terminal requires one start and one classification",
        )
    start = starts[0]
    classification = classifications[0]
    observations = [
        row for row in checked
        if row.get("event") == "observation-start"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    if len(observations) > 1:
        _fail("attempt-phase-order", "slot has more than one observation-start")
    observation_event = observations[0]["event_sha256"] if observations else None
    reason = _classification_reason(classification) if failure_reason is None else failure_reason
    row_fields: RegistryRow = {
        "classification_receipt_sha256": classification[
            "classification_receipt_sha256"
        ],
        "terminal_status": terminal_status,
        "raw_output_sha256": raw_output_sha256,
        "report_sha256": report_sha256,
        "observation_sha256": observation_sha256,
        "primary_value": primary_value,
        "failure_reason": reason,
        "finished_at": finished_at,
        "schedule_row_sha256": start["schedule_row_sha256"],
        "process_identity": dict(start["process_identity"]),
    }
    terminal_keys = profile.schema.event_keys[profile.schema.current]["terminal"]
    optional_terminal_fields = {
        "measurement_retry_reason": measurement_retry_reason,
        "terminal_evidence_sha256": terminal_evidence_sha256,
    }
    for field_name, field_value in optional_terminal_fields.items():
        if field_name in terminal_keys:
            if field_name == "terminal_evidence_sha256" and field_value is None:
                _fail(
                    "attempt-terminal",
                    "terminal_evidence_sha256 is required by the profile",
                )
            row_fields[field_name] = field_value
        elif field_value is not None:
            _fail(
                "attempt-terminal",
                f"{field_name} is not accepted by the profile",
            )
    if "pre_observation_failure_reason_echo" in terminal_keys:
        row_fields.update({
            "pre_observation_failure_reason_echo": _classification_reason(classification),
            "observation_start_event_sha256": observation_event,
        })
    row_payload = _event_payload(
        profile=profile, genesis=genesis, event="terminal", slot=slot,
        binding=binding, fields=row_fields,
    )
    terminal = _append_event(checked, row_payload, profile=profile)
    return assert_registry_rows(
        tuple(checked) + (terminal,), profile=profile, expected_binding=binding,
    )


def record_attempt_recovery(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT], freeze_id: str,
    slot_id: Hashable, binding: BindingT,
    scheduler_accounting_receipt: Mapping[str, Any],
    recoverer_process_identity: Mapping[str, Any], recovered_at: str,
) -> RegistryRows:
    """Close one abandoned slot with pinned scheduler-accounting evidence."""
    checked = assert_registry_rows(
        rows, profile=profile, expected_binding=binding,
    )
    genesis = checked[0]
    if _genesis_freeze_id(genesis, profile=profile, required=True) != freeze_id:
        _fail("attempt-binding", "recovery freeze_id differs from genesis")
    slot = _slot_by_id(checked, profile=profile, slot_id=slot_id)
    starts = [
        row for row in checked
        if row.get("event") == "start"
        and _row_is_for_slot(row, slot=slot, profile=profile)
    ]
    if len(starts) != 1:
        _fail(
            "attempt-recovery-order",
            "recovery requires exactly one start",
        )
    if any(
        row.get("event") == "terminal"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail("attempt-recovery-order", "recovery follows terminal")
    if any(
        row.get("event") == "recovery"
        and _row_is_for_slot(row, slot=slot, profile=profile)
        for row in checked
    ):
        _fail(
            "attempt-recovery-order",
            "slot has more than one recovery row",
        )
    receipt = _parse_recovery_receipt(
        dict(scheduler_accounting_receipt),
        profile=profile,
        label="scheduler_accounting_receipt",
    )
    checked_recoverer = parse_process_identity(
        dict(recoverer_process_identity),
        label="recoverer_process_identity",
        exact_keys=profile.process_identity_keys,
    )
    recovered_at = _text(recovered_at, label="recovered_at")
    start = starts[0]
    row_payload = _event_payload(
        profile=profile,
        genesis=genesis,
        event="recovery",
        slot=slot,
        binding=binding,
        fields={
            "start_event_sha256": start["event_sha256"],
            "scheduler_accounting_receipt": receipt,
            "scheduler_accounting_receipt_sha256": (
                _recovery_receipt_sha256(receipt)
            ),
            "failure_reason": receipt["failure_reason"],
            "recoverer_process_identity": checked_recoverer,
            "recovered_at": recovered_at,
        },
    )
    recovery = _append_event(checked, row_payload, profile=profile)
    return assert_registry_rows(
        tuple(checked) + (recovery,),
        profile=profile,
        expected_binding=binding,
    )
