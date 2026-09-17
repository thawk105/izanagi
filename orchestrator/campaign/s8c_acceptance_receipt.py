# -*- coding: utf-8 -*-
"""Strict verifier for tracked Phase 3 8c acceptance receipt bytes.

This module has no import-time dependency on ``trial_registry``,
``layer3_report``, or the autonomous-trial completeness verifier.  It verifies
the receipt artifact, every immutable byte hash it names, the recorded
lifecycle prefix, and that recorded arm execution can be rederived from the
ratified legacy freeze.  For current v5 receipts it lazily loads the
completeness verifier to rederive each cross-binding leaf.  Legacy v3/v4
receipts retain their aggregate-only check; they cannot reach downstream
capabilities because ``require_current_verified_receipt`` accepts only v5.
This verifier does not infer approval authority or certify an experimental
arm.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from . import attempt_registry_core as _attempt_core


LEGACY_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v1"
PREVIOUS_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v2"
CROSS_BINDING_V1_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v3"
CROSS_BINDING_V2_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v4"
SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v5"
LEGACY_CROSS_BINDING_RECEIPT_SCHEMA_VERSION = (
    "p3-8c-cross-binding-receipt/v1"
)
CROSS_BINDING_RECEIPT_SCHEMA_VERSION = "p3-8c-cross-binding-receipt/v2"
DEFAULT_RECEIPT_DIR = PurePosixPath("output/s8c-trial-registry/receipts")
DEFAULT_ATTEMPT_REGISTRY_PATH = PurePosixPath(
    "output/s8c-preregistration/attempt-registry.jsonl"
)
LEGACY_MANDATORY_NON_CERTIFYING_REASONS = frozenset({
    "c02-arm-binding-unproven",
    "t468-approval-authority-absent",
})
MANDATORY_NON_CERTIFYING_REASONS = frozenset({
    "t468-approval-authority-absent",
})
C02_ARM_BINDING_UNPROVEN = "c02-arm-binding-unproven"

_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_BASE_TOP_LEVEL_KEYS = frozenset({
    "schema_version",
    "manifest_path",
    "manifest_sha256",
    "prereg_commit",
    "activation_report_digest_sha256",
    "registry_path",
    "registry_blob_sha256",
    "registry_introduction_commit",
    "lifecycle_path",
    "lifecycle_prefix_bytes",
    "lifecycle_prefix_sha256",
    "certifying",
    "non_certifying_reason_codes",
    "trials",
})
_V1_TOP_LEVEL_KEYS = frozenset(_BASE_TOP_LEVEL_KEYS)
_V2_TOP_LEVEL_KEYS = frozenset(_BASE_TOP_LEVEL_KEYS)
_V3_TOP_LEVEL_KEYS = _BASE_TOP_LEVEL_KEYS | {
    "cross_binding_receipt_sha256",
}
_V4_TOP_LEVEL_KEYS = _V3_TOP_LEVEL_KEYS
_V5_TOP_LEVEL_KEYS = _V4_TOP_LEVEL_KEYS | {
    "prereg_content_commit",
    "prereg_effective_commit",
    "attempt_registry_path",
    "attempt_registry_prefix_bytes",
    "attempt_registry_prefix_sha256",
    "attempt_slot_projection",
}
_TOP_LEVEL_KEYS = _V5_TOP_LEVEL_KEYS
_V1_TRIAL_KEYS = frozenset({
    "trial_id",
    "arm",
    "holdout",
    "campaign_id",
    "status",
    "measurement_head",
    "report_path",
    "report_sha256",
    "attempt_journal_path",
    "attempt_journal_sha256",
})
_V2_TRIAL_KEYS = _V1_TRIAL_KEYS | {"arm_execution"}
_V2_TRIAL_KEYS_WITH_ORIGIN = _V2_TRIAL_KEYS | {"origin_terminal_projection"}
_V3_TRIAL_KEYS = _V2_TRIAL_KEYS | {"cross_binding_receipt_sha256"}
_V3_TRIAL_KEYS_WITH_ORIGIN = (
    _V3_TRIAL_KEYS | {"origin_terminal_projection"}
)
_V4_TRIAL_KEYS = _V3_TRIAL_KEYS
_V4_TRIAL_KEYS_WITH_ORIGIN = _V3_TRIAL_KEYS_WITH_ORIGIN
_V5_TRIAL_KEYS = _V4_TRIAL_KEYS
_V5_TRIAL_KEYS_WITH_ORIGIN = _V4_TRIAL_KEYS_WITH_ORIGIN
_ATTEMPT_SLOT_PROJECTION_KEYS = frozenset({
    "prereg_generation", "unit_count", "units",
})
_ATTEMPT_UNIT_KEYS = frozenset({
    "slot_id", "trial_id", "arm", "holdout", "campaign_id",
    "replicate_index",
})
_ATTEMPT_SCHEMA_VERSION = "p3-8c-attempt-registry/v3"
_ATTEMPT_SCHEMA_VERSIONS = frozenset({
    "p3-8c-attempt-registry/v1",
    "p3-8c-attempt-registry/v2",
    _ATTEMPT_SCHEMA_VERSION,
})
_ATTEMPT_CHAIN_KEYS = frozenset({
    "event_index", "previous_event_sha256", "event_sha256",
})
_ATTEMPT_GENESIS_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "manifest_path",
    "manifest_sha256", "root_path", "retryable_failure_reasons", "slots",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_SLOT_KEYS = frozenset({
    "slot_id", "trial_id", "arm", "holdout", "campaign_id",
    "prereg_generation", "replicate_index", "attempt_index",
    "schedule_row_sha256",
})
_ATTEMPT_START_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "run_start_receipt_sha256", "process_identity", "schedule_row_sha256",
    "started_at",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_PRE_OBSERVATION_SEAL_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "start_event_sha256", "run_start_receipt_sha256", "process_identity",
    "schedule_row_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_CLASSIFICATION_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "capability_digest_sha256",
    "authority_id", "authority_policy_sha256", "external_evidence_sha256",
    "classified_at", "pre_observation_failure_reason",
    "pre_observation_seal_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_OBSERVATION_START_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "classification_event_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_TERMINAL_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "terminal_status", "raw_output_sha256",
    "report_sha256", "observation_sha256", "primary_value", "failure_reason",
    "pre_observation_failure_reason_echo", "observation_start_event_sha256",
    "finished_at", "schedule_row_sha256", "process_identity",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_RECEIPT_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "capability_digest_sha256", "authority_id", "authority_policy_sha256",
    "external_evidence_sha256", "classified_at",
    "pre_observation_failure_reason", "pre_observation_seal_sha256",
})
_ATTEMPT_RETRYABLE_REASONS = frozenset({
    "preempted", "wall-timeout", "node-failure", "launcher-failure",
})
_ATTEMPT_STATUSES = (
    "observed", "retryable-failure", "terminal-failure", "not-consumed",
)
_PROCESS_IDENTITY_KEYS = frozenset({"pid", "starttime", "execution_uuid"})
_ARM_EXECUTION_KEYS = frozenset({
    "input_schema_version",
    "content_digest_sha256",
    "arm_binding_digest_sha256",
})
_ARM_BINDING_DOMAIN_SEPARATOR_V1 = b"izanagi-s8c-arm-binding/v1\0"
_VERIFIED_RECEIPT_SEAL = object()
_GIT_ENV_ALLOW = frozenset({
    "LANG", "LC_ALL", "LC_CTYPE", "PATH", "SYSTEMROOT", "TMPDIR",
})


class AcceptanceReceiptError(RuntimeError):
    """A receipt or one of its referenced byte streams was rejected."""


def _fail(gate: str, message: str) -> None:
    raise AcceptanceReceiptError(f"[{gate}] {message}")


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptArmExecution:
    input_schema_version: str
    content_digest_sha256: str
    arm_binding_digest_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptTrial:
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    status: str
    measurement_head: str
    report_path: str
    report_sha256: str
    attempt_journal_path: str
    attempt_journal_sha256: str
    arm_execution: AcceptanceReceiptArmExecution | None
    cross_binding_receipt_sha256: str | None
    origin_terminal_projection: dict[str, Any] | None


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptAttemptUnit:
    slot_id: str
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    replicate_index: int


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptAttemptSlotProjection:
    prereg_generation: int
    unit_count: int
    units: tuple[AcceptanceReceiptAttemptUnit, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceipt:
    schema_version: str
    manifest_path: str
    manifest_sha256: str
    prereg_commit: str
    prereg_content_commit: str | None
    prereg_effective_commit: str | None
    activation_report_digest_sha256: str
    registry_path: str
    registry_blob_sha256: str
    registry_introduction_commit: str
    lifecycle_path: str
    lifecycle_prefix_bytes: int
    lifecycle_prefix_sha256: str
    attempt_registry_path: str | None
    attempt_registry_prefix_bytes: int | None
    attempt_registry_prefix_sha256: str | None
    attempt_slot_projection: AcceptanceReceiptAttemptSlotProjection | None
    certifying: bool
    non_certifying_reason_codes: tuple[str, ...]
    cross_binding_receipt_sha256: str | None
    trials: tuple[AcceptanceReceiptTrial, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class VerifiedAcceptanceReceipt:
    """Sealed proof that tracked receipt and referenced working bytes matched."""

    repository_root: Path = dataclasses.field(repr=False, compare=False)
    path: Path
    relative_path: str
    raw_bytes: bytes = dataclasses.field(repr=False, compare=False)
    sha256: str
    receipt: AcceptanceReceipt
    _seal: object = dataclasses.field(repr=False, compare=False)

    @property
    def certifying(self) -> bool:
        return self.receipt.certifying

    @property
    def trials(self) -> tuple[AcceptanceReceiptTrial, ...]:
        return self.receipt.trials


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-json] value is not canonical JSON: {exc}"
        ) from exc


def _cross_binding_aggregate_sha256_for_schema(
    trials: Sequence[Mapping[str, Any]], *, cross_binding_schema_version: str,
) -> str:
    """Hash sorted leaves under one explicit cross-binding schema domain."""
    if cross_binding_schema_version not in {
        LEGACY_CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
        CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    }:
        _fail("receipt-cross-binding", "unsupported cross-binding schema domain")
    leaves: list[dict[str, str]] = []
    for index, trial in enumerate(trials):
        if not isinstance(trial, Mapping):
            _fail("receipt-cross-binding", f"leaf {index} is not an object")
        if set(trial) != {"trial_id", "receipt_sha256"}:
            _fail("receipt-cross-binding", f"leaf {index} exact keys differ")
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("receipt-cross-binding", f"leaf {index} trial_id is invalid")
        digest = _require_sha256(
            trial.get("receipt_sha256"),
            f"leaf {index}.receipt_sha256",
        )
        leaves.append({"trial_id": trial_id, "receipt_sha256": digest})
    if len({leaf["trial_id"] for leaf in leaves}) != len(leaves):
        _fail("receipt-cross-binding", "cross-binding leaves reuse a trial_id")
    payload = {
        "schema_version": cross_binding_schema_version,
        "trials": sorted(leaves, key=lambda leaf: leaf["trial_id"]),
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def cross_binding_aggregate_sha256(
    trials: Sequence[Mapping[str, Any]],
) -> str:
    """Hash cross-binding v2 leaves for newly issued outer receipt v5 bytes."""
    return _cross_binding_aggregate_sha256_for_schema(
        trials,
        cross_binding_schema_version=CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )


def _reject_constant(value: str) -> None:
    _fail("receipt-json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("receipt-json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except AcceptanceReceiptError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-json] receipt is not strict UTF-8 JSON: {exc}"
        ) from exc


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        _fail(
            "receipt-schema",
            f"{label} key set differs: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}",
        )


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("receipt-schema", f"{label} is not a SHA-256")
    return value


def _require_commit(value: Any, label: str) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        _fail("receipt-schema", f"{label} is not a full lowercase commit ID")
    return value


def _require_posix_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        _fail("receipt-path", f"{label} is not a repository-relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or value in {".", ".."}
        or any(part in {"", ".", ".."} for part in path.parts)
        or ".git" in path.parts
    ):
        _fail("receipt-path", f"{label} is not canonical: {value!r}")
    return value


def _attempt_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        _fail(
            "receipt-attempt-registry",
            f"{label} is not a bounded non-empty string",
        )
    return value


def _attempt_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("receipt-attempt-registry", f"{label} is not a SHA-256")
    return value


class _ReceiptAttemptSlotCodec:
    exact_keys = _ATTEMPT_SLOT_KEYS

    def parse(self, value: object, *, label: str) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            _fail("receipt-attempt-registry", f"{label} is not an object")
        if frozenset(value) != self.exact_keys:
            _fail("receipt-attempt-registry", f"{label} exact keys differ")
        slot_id = _attempt_text(value.get("slot_id"), label=f"{label}.slot_id")
        trial_id = value.get("trial_id")
        if (
            not isinstance(trial_id, str)
            or _TRIAL_ID_RE.fullmatch(trial_id) is None
        ):
            _fail("receipt-attempt-registry", f"{label}.trial_id is invalid")
        arm = value.get("arm")
        holdout = value.get("holdout")
        if arm not in {"on", "off", "swapped"}:
            _fail("receipt-attempt-registry", f"{label}.arm is invalid")
        if holdout not in {"H1", "H2"}:
            _fail("receipt-attempt-registry", f"{label}.holdout is invalid")
        campaign_id = _attempt_text(
            value.get("campaign_id"), label=f"{label}.campaign_id",
        )
        prereg_generation = value.get("prereg_generation")
        replicate_index = value.get("replicate_index")
        attempt_index = value.get("attempt_index")
        if type(prereg_generation) is not int or prereg_generation < 1:
            _fail(
                "receipt-attempt-registry",
                f"{label}.prereg_generation is invalid",
            )
        for field, raw in (
            ("replicate_index", replicate_index),
            ("attempt_index", attempt_index),
        ):
            if type(raw) is not int or raw < 0:
                _fail(
                    "receipt-attempt-registry", f"{label}.{field} is invalid",
                )
        schedule = _attempt_digest(
            value.get("schedule_row_sha256"),
            label=f"{label}.schedule_row_sha256",
        )
        return {
            "slot_id": slot_id,
            "trial_id": trial_id,
            "arm": arm,
            "holdout": holdout,
            "campaign_id": campaign_id,
            "prereg_generation": prereg_generation,
            "replicate_index": replicate_index,
            "attempt_index": attempt_index,
            "schedule_row_sha256": schedule,
        }

    def to_json(self, slot: Mapping[str, Any]) -> dict[str, Any]:
        return dict(slot)

    def slot_id(self, slot: Mapping[str, Any]) -> str:
        return slot["slot_id"]

    def series_key(self, slot: Mapping[str, Any]) -> tuple[object, ...]:
        return (
            slot["trial_id"], slot["arm"], slot["holdout"],
            slot["campaign_id"], slot["replicate_index"],
        )

    def attempt_ordinal(self, slot: Mapping[str, Any]) -> int:
        return slot["attempt_index"]

    def schedule_sha256(self, slot: Mapping[str, Any]) -> str:
        return slot["schedule_row_sha256"]


class _ReceiptAttemptBindingCodec:
    event_keys = frozenset({
        "prereg_content_commit", "prereg_effective_commit",
    })

    def parse(
        self, row: Mapping[str, object], *, label: str,
    ) -> tuple[str, str]:
        return (
            _require_commit(
                row.get("prereg_content_commit"),
                f"{label}.prereg_content_commit",
            ),
            _require_commit(
                row.get("prereg_effective_commit"),
                f"{label}.prereg_effective_commit",
            ),
        )

    def to_event_fields(self, binding: tuple[str, str]) -> dict[str, Any]:
        return {
            "prereg_content_commit": binding[0],
            "prereg_effective_commit": binding[1],
        }

    def identity(self, binding: tuple[str, str]) -> tuple[str, str]:
        return binding

    def capability_payload(
        self,
        *,
        slot: Mapping[str, Any],
        binding: tuple[str, str],
        freeze_id: str,
    ) -> dict[str, Any]:
        del freeze_id
        return {
            "slot_id": slot["slot_id"],
            "trial_id": slot["trial_id"],
            "arm": slot["arm"],
            "holdout": slot["holdout"],
            "campaign_id": slot["campaign_id"],
            "prereg_generation": slot["prereg_generation"],
            "replicate_index": slot["replicate_index"],
            "attempt_index": slot["attempt_index"],
            "schedule_row_sha256": slot["schedule_row_sha256"],
            "prereg_content_commit": binding[0],
            "prereg_effective_commit": binding[1],
        }


def _receipt_attempt_binding_mismatch(
    actual: tuple[str, str],
    expected: tuple[str | None, str | None],
) -> str | None:
    if expected[0] is not None and actual[0] != expected[0]:
        return (
            "attempt row content commit differs from receipt "
            "prereg_content_commit"
        )
    if expected[1] is not None and actual[1] != expected[1]:
        return (
            "attempt row effective commit differs from receipt "
            "prereg_effective_commit"
        )
    return None


_RECEIPT_ATTEMPT_PROFILE = _attempt_core.DomainProfile(
    schema=_attempt_core.SchemaProfile(
        current=_ATTEMPT_SCHEMA_VERSION,
        readable=frozenset({_ATTEMPT_SCHEMA_VERSION}),
        genesis_keys={_ATTEMPT_SCHEMA_VERSION: _ATTEMPT_GENESIS_KEYS},
        event_keys={
            _ATTEMPT_SCHEMA_VERSION: {
                "start": _ATTEMPT_START_KEYS,
                "pre-observation-seal": _ATTEMPT_PRE_OBSERVATION_SEAL_KEYS,
                "classification": _ATTEMPT_CLASSIFICATION_KEYS,
                "observation-start": _ATTEMPT_OBSERVATION_START_KEYS,
                "terminal": _ATTEMPT_TERMINAL_KEYS,
            },
        },
        receipt_keys={_ATTEMPT_SCHEMA_VERSION: _ATTEMPT_RECEIPT_KEYS},
    ),
    layout=_attempt_core.RegistryLayout(
        registry_path=DEFAULT_ATTEMPT_REGISTRY_PATH,
        classification_receipt_dir=PurePosixPath(
            "output/s8c-trial-registry/classification-receipts"
        ),
    ),
    statuses=_ATTEMPT_STATUSES,
    retryable_reasons=_ATTEMPT_RETRYABLE_REASONS,
    slot_codec=_ReceiptAttemptSlotCodec(),
    binding_codec=_ReceiptAttemptBindingCodec(),
    transition_policy=_attempt_core.TransitionPolicy(
        require_previous_terminal=True,
        forbid_retry_after_observation=True,
        allow_recovered_abandonment=False,
        max_series_attempts=None,
        require_terminal_reason_equals_classification=True,
        budget_key=None,
        max_consumptions_per_budget_key=None,
    ),
    process_identity_keys=_PROCESS_IDENTITY_KEYS,
    build_genesis_fields=lambda freeze_id, manifest_path, manifest_sha256: {
        "freeze_id": freeze_id,
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": manifest_sha256,
    },
    freeze_id_from_genesis=lambda genesis: str(genesis["freeze_id"]),
    binding_conflict_message="attempt rows do not share one P/C pair",
    binding_mismatch=_receipt_attempt_binding_mismatch,
)


def _parse_attempt_slot_projection(
    value: object,
) -> AcceptanceReceiptAttemptSlotProjection:
    if not isinstance(value, Mapping):
        _fail("receipt-schema", "attempt_slot_projection is not an object")
    _exact_keys(
        value, _ATTEMPT_SLOT_PROJECTION_KEYS, "attempt_slot_projection",
    )
    prereg_generation = value["prereg_generation"]
    unit_count = value["unit_count"]
    if type(prereg_generation) is not int or prereg_generation < 1:
        _fail(
            "receipt-schema",
            "attempt_slot_projection.prereg_generation is not a positive int",
        )
    if type(unit_count) is not int or unit_count < 1:
        _fail(
            "receipt-schema",
            "attempt_slot_projection.unit_count is not a positive int",
        )
    raw_units = value["units"]
    if not isinstance(raw_units, list) or len(raw_units) != unit_count:
        _fail(
            "receipt-schema",
            "attempt_slot_projection units differ from unit_count",
        )
    units: list[AcceptanceReceiptAttemptUnit] = []
    for index, raw in enumerate(raw_units):
        if not isinstance(raw, Mapping):
            _fail("receipt-schema", f"attempt units[{index}] is not an object")
        _exact_keys(raw, _ATTEMPT_UNIT_KEYS, f"attempt units[{index}]")
        slot_id = _attempt_text(
            raw.get("slot_id"), label=f"attempt units[{index}].slot_id",
        )
        trial_id = raw.get("trial_id")
        if (
            not isinstance(trial_id, str)
            or _TRIAL_ID_RE.fullmatch(trial_id) is None
        ):
            _fail("receipt-schema", f"attempt units[{index}].trial_id is invalid")
        arm = raw.get("arm")
        holdout = raw.get("holdout")
        campaign_id = raw.get("campaign_id")
        replicate_index = raw.get("replicate_index")
        if arm not in {"on", "off", "swapped"}:
            _fail("receipt-schema", f"attempt units[{index}].arm is invalid")
        if holdout not in {"H1", "H2"}:
            _fail("receipt-schema", f"attempt units[{index}].holdout is invalid")
        if not isinstance(campaign_id, str) or not campaign_id:
            _fail(
                "receipt-schema", f"attempt units[{index}].campaign_id is invalid",
            )
        if type(replicate_index) is not int or replicate_index != 0:
            _fail(
                "receipt-attempt-projection",
                "attempt unit replicate_index must remain zero",
            )
        units.append(AcceptanceReceiptAttemptUnit(
            slot_id=slot_id,
            trial_id=trial_id,
            arm=arm,
            holdout=holdout,
            campaign_id=campaign_id,
            replicate_index=replicate_index,
        ))
    if [unit.slot_id for unit in units] != sorted(unit.slot_id for unit in units):
        _fail("receipt-schema", "attempt units are not sorted by slot_id")
    if len({unit.slot_id for unit in units}) != len(units):
        _fail("receipt-schema", "attempt units reuse a slot_id")
    return AcceptanceReceiptAttemptSlotProjection(
        prereg_generation=prereg_generation,
        unit_count=unit_count,
        units=tuple(units),
    )


def _require_nonempty_reason_codes(value: Any) -> tuple[str, ...]:
    """Validate only the non-empty, sorted, unique reason-list shape."""
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(reason, str) or not reason for reason in value)
        or value != sorted(set(value))
    ):
        _fail(
            "receipt-reason-list",
            "reason codes must be a non-empty sorted unique string list",
        )
    return tuple(value)


def _require_mandatory_reason_codes(
    reasons: Sequence[str],
    required: frozenset[str] = MANDATORY_NON_CERTIFYING_REASONS,
) -> None:
    """Validate one schema generation's unresolved-authority reasons."""
    if not required.issubset(reasons):
        _fail(
            "receipt-mandatory-reasons",
            "mandatory unresolved-authority reason codes are absent",
        )


def _require_legacy_mandatory_reason_codes(reasons: Sequence[str]) -> None:
    _require_mandatory_reason_codes(
        reasons, LEGACY_MANDATORY_NON_CERTIFYING_REASONS,
    )


def _parse_arm_execution(
    value: Any, *, label: str,
) -> AcceptanceReceiptArmExecution:
    if not isinstance(value, Mapping):
        _fail("receipt-schema", f"{label} is not an object")
    _exact_keys(value, _ARM_EXECUTION_KEYS, label)
    input_schema_version = value["input_schema_version"]
    if input_schema_version != "8b-v1":
        _fail("receipt-arm-binding", f"{label}.input_schema_version differs")
    return AcceptanceReceiptArmExecution(
        input_schema_version=input_schema_version,
        content_digest_sha256=_require_sha256(
            value["content_digest_sha256"],
            f"{label}.content_digest_sha256",
        ),
        arm_binding_digest_sha256=_require_sha256(
            value["arm_binding_digest_sha256"],
            f"{label}.arm_binding_digest_sha256",
        ),
    )


def _parse_origin_terminal_projection(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("receipt-schema", f"{label} is not an object")
    return dict(value)


def parse_acceptance_receipt_bytes(data: bytes) -> AcceptanceReceipt:
    """Strictly parse one canonical receipt line terminated by LF."""
    if not isinstance(data, bytes) or not data.endswith(b"\n"):
        _fail("receipt-canonical", "receipt must be one newline-terminated JSON line")
    if data.count(b"\n") != 1:
        _fail("receipt-canonical", "receipt must contain exactly one JSON line")
    value = _decode_json(data[:-1])
    if not isinstance(value, Mapping):
        _fail("receipt-schema", "receipt root is not an object")
    if _canonical_bytes(value) + b"\n" != data:
        _fail("receipt-canonical", "receipt bytes are not canonical JSON plus LF")
    if "schema_version" not in value:
        _fail("receipt-schema", "receipt.schema_version is missing")
    schema_version = value["schema_version"]
    if schema_version not in {
        LEGACY_SCHEMA_VERSION,
        PREVIOUS_SCHEMA_VERSION,
        CROSS_BINDING_V1_SCHEMA_VERSION,
        CROSS_BINDING_V2_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }:
        _fail("receipt-schema", "unsupported schema_version")
    expected_top_keys = {
        LEGACY_SCHEMA_VERSION: _V1_TOP_LEVEL_KEYS,
        PREVIOUS_SCHEMA_VERSION: _V2_TOP_LEVEL_KEYS,
        CROSS_BINDING_V1_SCHEMA_VERSION: _V3_TOP_LEVEL_KEYS,
        CROSS_BINDING_V2_SCHEMA_VERSION: _V4_TOP_LEVEL_KEYS,
        SCHEMA_VERSION: _V5_TOP_LEVEL_KEYS,
    }[schema_version]
    _exact_keys(value, expected_top_keys, "receipt")

    manifest_path = _require_posix_path(value["manifest_path"], "manifest_path")
    manifest_sha256 = _require_sha256(value["manifest_sha256"], "manifest_sha256")
    prereg_commit = _require_commit(value["prereg_commit"], "prereg_commit")
    activation_digest = _require_sha256(
        value["activation_report_digest_sha256"],
        "activation_report_digest_sha256",
    )
    registry_path = _require_posix_path(value["registry_path"], "registry_path")
    registry_digest = _require_sha256(
        value["registry_blob_sha256"], "registry_blob_sha256"
    )
    introduction = _require_commit(
        value["registry_introduction_commit"], "registry_introduction_commit"
    )
    lifecycle_path = _require_posix_path(value["lifecycle_path"], "lifecycle_path")
    lifecycle_prefix_bytes = value["lifecycle_prefix_bytes"]
    if (
        isinstance(lifecycle_prefix_bytes, bool)
        or not isinstance(lifecycle_prefix_bytes, int)
        or lifecycle_prefix_bytes < 1
    ):
        _fail("receipt-schema", "lifecycle_prefix_bytes is not a positive int")
    lifecycle_prefix_digest = _require_sha256(
        value["lifecycle_prefix_sha256"], "lifecycle_prefix_sha256"
    )
    cross_binding_digest = (
        None
        if schema_version not in {
            CROSS_BINDING_V1_SCHEMA_VERSION,
            CROSS_BINDING_V2_SCHEMA_VERSION,
            SCHEMA_VERSION,
        }
        else _require_sha256(
            value["cross_binding_receipt_sha256"],
            "cross_binding_receipt_sha256",
        )
    )
    if schema_version == SCHEMA_VERSION:
        prereg_content_commit = _require_commit(
            value["prereg_content_commit"], "prereg_content_commit",
        )
        prereg_effective_commit = _require_commit(
            value["prereg_effective_commit"], "prereg_effective_commit",
        )
        attempt_registry_path = _require_posix_path(
            value["attempt_registry_path"], "attempt_registry_path",
        )
        if attempt_registry_path != DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix():
            _fail(
                "receipt-attempt-registry",
                "attempt_registry_path is not canonical",
            )
        attempt_registry_prefix_bytes = value["attempt_registry_prefix_bytes"]
        if (
            type(attempt_registry_prefix_bytes) is not int
            or attempt_registry_prefix_bytes < 1
        ):
            _fail(
                "receipt-schema",
                "attempt_registry_prefix_bytes is not a positive int",
            )
        attempt_registry_prefix_sha256 = _require_sha256(
            value["attempt_registry_prefix_sha256"],
            "attempt_registry_prefix_sha256",
        )
        attempt_slot_projection = _parse_attempt_slot_projection(
            value["attempt_slot_projection"]
        )
    else:
        prereg_content_commit = None
        prereg_effective_commit = None
        attempt_registry_path = None
        attempt_registry_prefix_bytes = None
        attempt_registry_prefix_sha256 = None
        attempt_slot_projection = None

    # Every schema generation structurally records unresolved approval authority.
    # No accepted bytes can turn any generation into a certifying receipt.
    if value["certifying"] is not False:
        _fail("receipt-certifying", "receipts are structurally non-certifying")
    reasons = _require_nonempty_reason_codes(value["non_certifying_reason_codes"])
    if schema_version == LEGACY_SCHEMA_VERSION:
        _require_legacy_mandatory_reason_codes(reasons)
    else:
        _require_mandatory_reason_codes(reasons)

    trials_value = value["trials"]
    if not isinstance(trials_value, list) or len(trials_value) != 6:
        _fail("receipt-schema", "trials must contain exactly six rows")
    trials: list[AcceptanceReceiptTrial] = []
    for index, raw in enumerate(trials_value):
        if not isinstance(raw, Mapping):
            _fail("receipt-schema", f"trials[{index}] is not an object")
        expected_trial_keys = (
            _V1_TRIAL_KEYS
            if schema_version == LEGACY_SCHEMA_VERSION
            else (
                (
                    _V5_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V5_TRIAL_KEYS
                )
                if schema_version == SCHEMA_VERSION
                else (
                    _V4_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V4_TRIAL_KEYS
                )
                if schema_version == CROSS_BINDING_V2_SCHEMA_VERSION
                else (
                    _V3_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V3_TRIAL_KEYS
                )
                if schema_version == CROSS_BINDING_V1_SCHEMA_VERSION
                else (
                    _V2_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V2_TRIAL_KEYS
                )
            )
        )
        _exact_keys(raw, expected_trial_keys, f"trials[{index}]")
        trial_id = raw["trial_id"]
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("receipt-schema", f"trials[{index}].trial_id is invalid")
        arm = raw["arm"]
        holdout = raw["holdout"]
        campaign_id = raw["campaign_id"]
        status = raw["status"]
        if not isinstance(arm, str) or arm not in {"on", "off", "swapped"}:
            _fail("receipt-schema", f"trials[{index}].arm is invalid")
        if not isinstance(holdout, str) or holdout not in {"H1", "H2"}:
            _fail("receipt-schema", f"trials[{index}].holdout is invalid")
        if not isinstance(campaign_id, str) or not campaign_id:
            _fail("receipt-schema", f"trials[{index}].campaign_id is invalid")
        if not isinstance(status, str) or not status:
            _fail("receipt-schema", f"trials[{index}].status is invalid")
        trials.append(AcceptanceReceiptTrial(
            trial_id=trial_id,
            arm=arm,
            holdout=holdout,
            campaign_id=campaign_id,
            status=status,
            measurement_head=_require_commit(
                raw["measurement_head"], f"trials[{index}].measurement_head"
            ),
            report_path=_require_posix_path(
                raw["report_path"], f"trials[{index}].report_path"
            ),
            report_sha256=_require_sha256(
                raw["report_sha256"], f"trials[{index}].report_sha256"
            ),
            attempt_journal_path=_require_posix_path(
                raw["attempt_journal_path"],
                f"trials[{index}].attempt_journal_path",
            ),
            attempt_journal_sha256=_require_sha256(
                raw["attempt_journal_sha256"],
                f"trials[{index}].attempt_journal_sha256",
            ),
            arm_execution=(
                None
                if schema_version == LEGACY_SCHEMA_VERSION
                else _parse_arm_execution(
                    raw["arm_execution"], label=f"trials[{index}].arm_execution",
                )
            ),
            cross_binding_receipt_sha256=(
                None
                if schema_version not in {
                    CROSS_BINDING_V1_SCHEMA_VERSION,
                    CROSS_BINDING_V2_SCHEMA_VERSION,
                    SCHEMA_VERSION,
                }
                else _require_sha256(
                    raw["cross_binding_receipt_sha256"],
                    f"trials[{index}].cross_binding_receipt_sha256",
                )
            ),
            origin_terminal_projection=(
                None
                if "origin_terminal_projection" not in raw
                else _parse_origin_terminal_projection(
                    raw["origin_terminal_projection"],
                    label=f"trials[{index}].origin_terminal_projection",
                )
            ),
        ))
    if [trial.trial_id for trial in trials] != sorted(
        trial.trial_id for trial in trials
    ):
        _fail("receipt-schema", "trials are not sorted by trial_id")
    if len({trial.trial_id for trial in trials}) != 6:
        _fail("receipt-schema", "receipt reuses a trial_id")
    if len({trial.campaign_id for trial in trials}) != 6:
        _fail("receipt-schema", "receipt reuses a campaign_id")
    if len({trial.measurement_head for trial in trials}) != 1:
        _fail(
            "receipt-measurement-head-coherence",
            "trials do not share one measurement_head",
        )
    if schema_version in {
        PREVIOUS_SCHEMA_VERSION,
        CROSS_BINDING_V1_SCHEMA_VERSION,
        CROSS_BINDING_V2_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }:
        expected_cells = {
            (holdout, arm)
            for holdout in ("H1", "H2")
            for arm in ("on", "off", "swapped")
        }
        actual_cells = {(trial.holdout, trial.arm) for trial in trials}
        if actual_cells != expected_cells:
            _fail("receipt-arm-binding", "current trials are not the closed six arm cells")
        for holdout in ("H1", "H2"):
            digests = [
                trial.arm_execution.content_digest_sha256
                for trial in trials
                if trial.holdout == holdout and trial.arm_execution is not None
            ]
            if len(set(digests)) != 3:
                _fail(
                    "receipt-arm-binding",
                    f"{holdout} content digests are not pairwise distinct",
                )

    return AcceptanceReceipt(
        schema_version=schema_version,
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        prereg_commit=prereg_commit,
        prereg_content_commit=prereg_content_commit,
        prereg_effective_commit=prereg_effective_commit,
        activation_report_digest_sha256=activation_digest,
        registry_path=registry_path,
        registry_blob_sha256=registry_digest,
        registry_introduction_commit=introduction,
        lifecycle_path=lifecycle_path,
        lifecycle_prefix_bytes=lifecycle_prefix_bytes,
        lifecycle_prefix_sha256=lifecycle_prefix_digest,
        attempt_registry_path=attempt_registry_path,
        attempt_registry_prefix_bytes=attempt_registry_prefix_bytes,
        attempt_registry_prefix_sha256=attempt_registry_prefix_sha256,
        attempt_slot_projection=attempt_slot_projection,
        certifying=False,
        non_certifying_reason_codes=reasons,
        cross_binding_receipt_sha256=cross_binding_digest,
        trials=tuple(trials),
    )


def _git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in _GIT_ENV_ALLOW}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _git(
    root: Path, args: Sequence[str], *, input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", os.fspath(root), *args],
        env=_git_env(),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repository_root(path: Path) -> Path:
    try:
        root = Path(path).resolve(strict=True)
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-repo] repository root cannot be resolved: {path}"
        ) from exc
    result = _git(root, ("rev-parse", "--show-toplevel"))
    if result.returncode != 0:
        _fail("receipt-repo", "repository root is not a Git work tree")
    try:
        actual = Path(result.stdout.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise AcceptanceReceiptError("[receipt-repo] Git returned a bad root") from exc
    if actual != root:
        _fail("receipt-repo", "repository_root is not the Git top level")
    return root


def _read_regular_bytes(path: Path, *, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} cannot be stated: {path}"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail("receipt-reference", f"{label} is not a regular non-symlink file")
    flags = os.O_RDONLY | (getattr(os, "O_NOFOLLOW", 0))
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} cannot be read: {path}"
        ) from exc
    if not stat.S_ISREG(opened.st_mode) or (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
    ) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        _fail("receipt-reference", f"{label} changed while it was read")
    return b"".join(chunks)


def _blob_at_head(root: Path, relative_path: str) -> bytes | None:
    listing = _git(root, (
        "ls-tree", "-z", "--full-name", "HEAD", "--", relative_path,
    ))
    if listing.returncode != 0:
        _fail("receipt-tracked", "HEAD tree lookup failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("receipt-tracked", "receipt path is not a single HEAD entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        _fail("receipt-tracked", "HEAD tree entry is malformed")
    mode, object_type, object_id = fields
    if (
        entry_path != os.fsencode(relative_path)
        or object_type != b"blob"
        or mode not in {b"100644", b"100755"}
    ):
        _fail("receipt-tracked", "receipt HEAD entry is not the literal regular file")
    blob = _git(root, ("cat-file", "blob", object_id.decode("ascii")))
    if blob.returncode != 0:
        _fail("receipt-tracked", "receipt HEAD blob cannot be read")
    return blob.stdout


def _resolved_reference(root: Path, relative_path: str, label: str) -> Path:
    lexical = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} escapes or is absent from repository"
        ) from exc
    if resolved != lexical:
        _fail("receipt-reference", f"{label} traverses a symlink component")
    return resolved


def _assert_digest(
    root: Path, relative_path: str, expected: str, label: str,
) -> bytes:
    data = _read_regular_bytes(
        _resolved_reference(root, relative_path, label), label=label,
    )
    if hashlib.sha256(data).hexdigest() != expected:
        _fail("receipt-reference-hash", f"{label} bytes differ from receipt")
    return data


def _arm_execution_record(
    arm_execution: AcceptanceReceiptArmExecution,
) -> dict[str, str]:
    return {
        "input_schema_version": arm_execution.input_schema_version,
        "content_digest_sha256": arm_execution.content_digest_sha256,
        "arm_binding_digest_sha256": arm_execution.arm_binding_digest_sha256,
    }


def _arm_binding_digest(
    *, holdout: str, arm: str, content_digest: str,
) -> str:
    return hashlib.sha256(
        _ARM_BINDING_DOMAIN_SEPARATOR_V1
        + holdout.encode("utf-8")
        + arm.encode("utf-8")
        + content_digest.encode("ascii")
    ).hexdigest()


def _require_ratified_legacy_arm_authority() -> None:
    """Require exact agreement between fixed legacy and in-source authority.

    This gate rejects v2/v3/v4 arm records that cannot be rederived from the
    verifier checkout's ratified legacy freeze.  It does not reject a receipt
    because the subject repository lacks a copy of that legacy freeze.
    """
    try:
        from . import s8b_holdout_freeze
        from . import s8b_ratified_freeze

        legacy = s8b_ratified_freeze.load_legacy_freeze()
    except AcceptanceReceiptError:
        raise
    except Exception as exc:
        raise AcceptanceReceiptError(
            "[receipt-freeze-arm-binding] ratified legacy freeze cannot be loaded"
        ) from exc

    document = legacy.document
    legacy_holdouts = (
        document.get("holdouts") if isinstance(document, Mapping) else None
    )
    source_holdouts = s8b_holdout_freeze.HOLDOUTS
    if (
        not isinstance(legacy_holdouts, Mapping)
        or not isinstance(source_holdouts, Mapping)
        or set(legacy_holdouts) != set(source_holdouts)
    ):
        _fail(
            "receipt-freeze-arm-binding",
            "ratified legacy holdout names differ from in-source authority",
        )

    legacy_entry_keys = {
        "candidate_id",
        "ycsb",
        "records",
        "threads",
        "unknownness_check",
        "variant_binding",
    }
    for name, source_entry in source_holdouts.items():
        legacy_entry = legacy_holdouts.get(name)
        if (
            not isinstance(legacy_entry, Mapping)
            or set(legacy_entry) != legacy_entry_keys
        ):
            _fail(
                "receipt-freeze-arm-binding",
                f"ratified legacy holdout entry key set differs: {name}",
            )
        legacy_ycsb = legacy_entry.get("ycsb")
        source_ycsb = (
            source_entry.get("ycsb")
            if isinstance(source_entry, Mapping)
            else None
        )
        if not isinstance(legacy_ycsb, Mapping) or not isinstance(
            source_ycsb, Mapping
        ):
            _fail(
                "receipt-freeze-arm-binding",
                f"ratified legacy holdout projection is malformed: {name}",
            )
        legacy_projection = {
            "candidate_id": legacy_entry.get("candidate_id"),
            "ycsb": dict(legacy_ycsb),
            "records": legacy_entry.get("records"),
            "threads": legacy_entry.get("threads"),
        }
        source_projection = {
            "candidate_id": source_entry.get("candidate_id"),
            "ycsb": dict(source_ycsb),
            "records": source_entry.get("records"),
            "threads": source_entry.get("threads"),
        }
        try:
            legacy_projection_bytes = _canonical_bytes(legacy_projection)
            source_projection_bytes = _canonical_bytes(source_projection)
        except AcceptanceReceiptError as exc:
            raise AcceptanceReceiptError(
                "[receipt-freeze-arm-binding] holdout projection is not canonical JSON"
            ) from exc
        if legacy_projection_bytes != source_projection_bytes:
            _fail(
                "receipt-freeze-arm-binding",
                f"ratified legacy holdout differs from in-source authority: {name}",
            )

    legacy_derangement = (
        document.get("derangement") if isinstance(document, Mapping) else None
    )
    try:
        derangement_differs = (
            not isinstance(legacy_derangement, Mapping)
            or _canonical_bytes(dict(legacy_derangement))
            != _canonical_bytes(s8b_holdout_freeze.DERANGEMENT)
        )
    except AcceptanceReceiptError as exc:
        raise AcceptanceReceiptError(
            "[receipt-freeze-arm-binding] derangement is not canonical JSON"
        ) from exc
    if derangement_differs:
        _fail(
            "receipt-freeze-arm-binding",
            "ratified legacy derangement differs from in-source authority",
        )


def _expected_arm_content_digest(
    root: Path,
    holdout: str,
    arm: str,
    commit: str,
) -> str:
    """Rederive one content digest from the subject's historical arm input."""
    try:
        from . import s8c_arm_inputs

        resolved = s8c_arm_inputs.resolve_arm_input(
            arm=arm,
            holdout=holdout,
            repository_root=root,
            commit=commit,
        )
        return resolved.content_digest_sha256
    except AcceptanceReceiptError:
        raise
    except Exception as exc:
        raise AcceptanceReceiptError(
            "[receipt-freeze-arm-binding] trial arm input cannot be rederived"
        ) from exc


def _assert_rederived_trial_arm_execution(
    root: Path,
    trial: AcceptanceReceiptTrial,
) -> None:
    """Require the receipt content digest to equal independent rederivation."""
    arm_execution = trial.arm_execution
    if arm_execution is None:
        _fail("receipt-freeze-arm-binding", "v2 trial arm_execution is absent")
    expected_content_digest = _expected_arm_content_digest(
        root,
        trial.holdout,
        trial.arm,
        trial.measurement_head,
    )
    if arm_execution.content_digest_sha256 != expected_content_digest:
        _fail(
            "receipt-freeze-arm-binding",
            "content digest differs from ratified legacy freeze rederivation",
        )
    # Expected binding equality follows from this comparison and the existing binding gate.


def _reference_object(data: bytes, *, label: str) -> Mapping[str, Any]:
    value = _decode_json(data)
    if not isinstance(value, Mapping):
        _fail("receipt-arm-binding", f"{label} root is not an object")
    return value


def _journal_events(data: bytes) -> tuple[Mapping[str, Any], ...]:
    if not data or not data.endswith(b"\n"):
        _fail("receipt-arm-binding", "attempt journal is not newline terminated")
    events = []
    for index, line in enumerate(data.splitlines(), 1):
        value = _decode_json(line)
        if not isinstance(value, Mapping):
            _fail(
                "receipt-arm-binding",
                f"attempt journal line {index} is not an object",
            )
        events.append(value)
    return tuple(events)


def _rederive_cross_binding_receipt_sha256(
    root: Path,
    trial: AcceptanceReceiptTrial,
    *,
    report_bytes: bytes,
    journal_bytes: bytes,
) -> str:
    """Rederive one current cross-binding leaf from referenced evidence."""
    report = _reference_object(report_bytes, label="trial report")
    events = _journal_events(journal_bytes)
    run_root = _resolved_reference(
        root, trial.attempt_journal_path, "attempt journal",
    ).parent
    output_root = run_root.parent.parent if report.get("do_build") is True else None

    from . import autonomous_trial_completeness as completeness

    try:
        projection = completeness.verify_s8c_cross_binding(
            report=report,
            events=events,
            run_root=run_root,
            output_root=output_root,
        )
    except completeness.AutonomousTrialCompletenessError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-cross-binding] {exc}"
        ) from exc
    return projection["receipt_sha256"]


def _verify_v2_trial_arm_execution(
    trial: AcceptanceReceiptTrial,
    *,
    report_bytes: bytes,
    journal_bytes: bytes,
) -> bool:
    """Verify summary equality and rederive content from named report bytes.

    ``False`` means the report has no executed cell descriptor, so the legacy
    C02 reason cannot be dropped.  Any contradictory bytes fail closed.
    """
    arm_execution = trial.arm_execution
    if arm_execution is None:
        _fail("receipt-arm-binding", "v2 trial arm_execution is absent")
    expected_arm_execution = _arm_execution_record(arm_execution)
    report = _reference_object(report_bytes, label="trial report")

    if report.get("trial_id") != trial.trial_id:
        _fail("receipt-arm-binding", "trial report trial_id differs from receipt")
    if report.get("measurement_head") != trial.measurement_head:
        _fail(
            "receipt-arm-binding",
            "trial report measurement_head differs from receipt",
        )
    if report.get("status") != trial.status:
        _fail("receipt-arm-binding", "trial report status differs from receipt")
    report_has_origin = "origin_terminal_projection" in report
    receipt_has_origin = trial.origin_terminal_projection is not None
    if report_has_origin != receipt_has_origin:
        _fail(
            "receipt-origin-projection",
            "trial report origin_terminal_projection presence differs from receipt",
        )
    if receipt_has_origin:
        report_origin = report.get("origin_terminal_projection")
        if not isinstance(report_origin, Mapping):
            _fail(
                "receipt-origin-projection",
                "trial report origin_terminal_projection is not an object",
            )
        if _canonical_bytes(report_origin) != _canonical_bytes(
            trial.origin_terminal_projection
        ):
            _fail(
                "receipt-origin-projection",
                "trial report origin_terminal_projection differs from receipt",
            )
    launch = report.get("launch_admission")
    binding = launch.get("binding") if isinstance(launch, Mapping) else None
    if not isinstance(binding, Mapping) or any(
        binding.get(field) != expected
        for field, expected in (
            ("arm", trial.arm),
            ("holdout", trial.holdout),
            ("campaign_id", trial.campaign_id),
        )
    ):
        _fail("receipt-arm-binding", "trial report arm cell differs from receipt")
    if binding.get("measurement_head") != trial.measurement_head:
        _fail(
            "receipt-freeze-arm-binding",
            "trial report binding measurement_head differs from receipt",
        )

    cells = report.get("cells")
    if not isinstance(cells, list) or len(cells) > 1:
        _fail("receipt-arm-binding", "trial report cells are not a zero/one list")
    descriptor_proven = False
    if cells:
        cell = cells[0]
        descriptor = cell.get("descriptor") if isinstance(cell, Mapping) else None
        if not isinstance(descriptor, Mapping):
            _fail("receipt-arm-binding", "trial report cell descriptor is absent")
        workload = binding.get("workload")
        if cell.get("workload") != workload:
            _fail("receipt-arm-binding", "trial report descriptor cell is not bound")
        actual_content_digest = hashlib.sha256(
            _canonical_bytes(descriptor)
        ).hexdigest()
        if actual_content_digest != arm_execution.content_digest_sha256:
            _fail(
                "receipt-arm-binding",
                "cell descriptor content digest differs from receipt",
            )
        descriptor_proven = True

    if report.get("arm_execution") != expected_arm_execution:
        _fail(
            "receipt-arm-binding",
            "trial report arm_execution differs from receipt",
        )
    expected_binding_digest = _arm_binding_digest(
        holdout=trial.holdout,
        arm=trial.arm,
        content_digest=arm_execution.content_digest_sha256,
    )
    if arm_execution.arm_binding_digest_sha256 != expected_binding_digest:
        _fail("receipt-arm-binding", "arm binding digest differs from receipt inputs")

    starts = [
        event for event in _journal_events(journal_bytes)
        if event.get("event") == "run-start"
    ]
    if len(starts) != 1:
        _fail("receipt-arm-binding", "attempt journal run-start is not unique")
    if starts[0].get("arm_execution") != expected_arm_execution:
        _fail(
            "receipt-arm-binding",
            "run-start arm_execution differs from report and receipt",
        )
    return descriptor_proven


def _arm_execution_authorizes_reason_drop(
    descriptor_proofs: Sequence[bool],
) -> bool:
    """The only v2 gate allowed to remove the legacy C02 reason."""
    return len(descriptor_proofs) == 6 and all(descriptor_proofs)


def _assert_prefix_digest(
    root: Path,
    relative_path: str,
    prefix_bytes: int,
    expected: str,
    label: str,
) -> bytes:
    data = _read_regular_bytes(
        _resolved_reference(root, relative_path, label), label=label,
    )
    if len(data) < prefix_bytes:
        _fail("receipt-reference-prefix", f"{label} is shorter than receipt prefix")
    prefix = data[:prefix_bytes]
    if hashlib.sha256(prefix).hexdigest() != expected:
        _fail("receipt-reference-prefix", f"{label} prefix bytes differ from receipt")
    return prefix


def _attempt_projection_from_rows(
    rows: Sequence[Mapping[str, Any]],
) -> AcceptanceReceiptAttemptSlotProjection:
    genesis = rows[0]
    initial_slots = [
        slot for slot in genesis["slots"] if slot["attempt_index"] == 0
    ]
    if not initial_slots:
        _fail(
            "receipt-attempt-consumption",
            "predeclared attempt unit set is empty",
        )
    generations = {slot["prereg_generation"] for slot in genesis["slots"]}
    if len(generations) != 1:
        _fail(
            "receipt-attempt-registry",
            "attempt registry does not have one prereg_generation",
        )
    units = tuple(sorted((
        AcceptanceReceiptAttemptUnit(
            slot_id=slot["slot_id"],
            trial_id=slot["trial_id"],
            arm=slot["arm"],
            holdout=slot["holdout"],
            campaign_id=slot["campaign_id"],
            replicate_index=slot["replicate_index"],
        )
        for slot in initial_slots
    ), key=lambda unit: unit.slot_id))
    if any(unit.replicate_index != 0 for unit in units):
        _fail(
            "receipt-attempt-projection",
            "attempt unit replicate_index must remain zero",
        )
    return AcceptanceReceiptAttemptSlotProjection(
        prereg_generation=next(iter(generations)),
        unit_count=len(units),
        units=units,
    )


def _assert_attempt_registry_consumption(
    root: Path,
    receipt: AcceptanceReceipt,
) -> None:
    """Recheck the v5 registry projection and final consumption independently.

    A non-empty projection with exactly one observed or terminal-failure row
    per predeclared unit is accepted. A missing registry, divergent projection,
    retryable-only unit, missing final, duplicate final, or report mismatch is
    rejected.
    """
    if (
        receipt.attempt_registry_path is None
        or receipt.prereg_content_commit is None
        or receipt.prereg_effective_commit is None
        or receipt.attempt_registry_prefix_bytes is None
        or receipt.attempt_registry_prefix_sha256 is None
        or receipt.attempt_slot_projection is None
    ):
        _fail("receipt-attempt-registry", "v5 attempt binding is absent")
    if _blob_at_head(root, receipt.attempt_registry_path) is None:
        _fail(
            "receipt-attempt-registry",
            "attempt registry is not tracked at Git HEAD",
        )
    current_attempt_registry = _read_regular_bytes(
        _resolved_reference(
            root, receipt.attempt_registry_path, "attempt registry",
        ),
        label="attempt registry",
    )
    _assert_attempt_registry_history_append_only(
        root,
        receipt.attempt_registry_path,
        current_bytes=current_attempt_registry,
    )
    prefix = _assert_prefix_digest(
        root,
        receipt.attempt_registry_path,
        receipt.attempt_registry_prefix_bytes,
        receipt.attempt_registry_prefix_sha256,
        "attempt registry",
    )
    try:
        rows = _attempt_core.load_attempt_registry(
            prefix,
            profile=_RECEIPT_ATTEMPT_PROFILE,
            expected_binding=(
                receipt.prereg_content_commit,
                receipt.prereg_effective_commit,
            ),
        )
    except _attempt_core.AttemptRegistryCoreError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-attempt-registry] {exc}"
        ) from exc
    genesis = rows[0]
    if genesis["manifest_sha256"] != receipt.manifest_sha256:
        _fail(
            "receipt-attempt-binding",
            "attempt registry manifest_sha256 differs from receipt",
        )
    initial_blob = _blob_at_commit(
        root, receipt.prereg_content_commit, receipt.attempt_registry_path,
    )
    if initial_blob is None or not prefix.startswith(initial_blob):
        _fail(
            "receipt-attempt-binding",
            "attempt registry does not extend the genesis at "
            "prereg_content_commit",
        )
    try:
        initial_rows = _attempt_core.load_attempt_registry(
            initial_blob, profile=_RECEIPT_ATTEMPT_PROFILE,
        )
    except _attempt_core.AttemptRegistryCoreError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-attempt-registry] {exc}"
        ) from exc
    if len(initial_rows) != 1:
        _fail(
            "receipt-attempt-binding",
            "attempt registry at prereg_content_commit is not genesis-only",
        )
    derived_projection = _attempt_projection_from_rows(rows)
    if derived_projection != receipt.attempt_slot_projection:
        _fail(
            "receipt-attempt-projection",
            "attempt registry slot projection differs from receipt",
        )

    trials_by_id = {trial.trial_id: trial for trial in receipt.trials}
    projected_trials = {
        (
            unit.trial_id, unit.arm, unit.holdout, unit.campaign_id,
        )
        for unit in derived_projection.units
    }
    receipt_trials = {
        (trial.trial_id, trial.arm, trial.holdout, trial.campaign_id)
        for trial in receipt.trials
    }
    if projected_trials != receipt_trials:
        _fail(
            "receipt-attempt-projection",
            "attempt units differ from receipt trials",
        )

    slots_by_id = {
        slot["slot_id"]: slot for slot in rows[0]["slots"]
    }
    finals_by_unit: dict[tuple[object, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        if (
            row.get("event") != "terminal"
            or row.get("terminal_status")
            not in {"observed", "terminal-failure"}
        ):
            continue
        slot = slots_by_id[row["slot_id"]]
        unit_key = (
            slot["trial_id"], slot["arm"], slot["holdout"],
            slot["campaign_id"], slot["replicate_index"],
        )
        finals_by_unit.setdefault(unit_key, []).append(row)

    for unit in derived_projection.units:
        unit_key = (
            unit.trial_id, unit.arm, unit.holdout, unit.campaign_id,
            unit.replicate_index,
        )
        finals = finals_by_unit.pop(unit_key, [])
        if len(finals) != 1:
            _fail(
                "receipt-attempt-consumption",
                "predeclared unit does not have exactly one final terminal",
            )
        terminal = finals[0]
        trial = trials_by_id[unit.trial_id]
        expected_terminal_status = {
            "complete": "observed",
            "partial": "terminal-failure",
        }.get(trial.status)
        if expected_terminal_status != terminal["terminal_status"]:
            _fail(
                "receipt-attempt-consumption",
                "final terminal status differs from receipt trial status",
            )
        if terminal["report_sha256"] != trial.report_sha256:
            _fail(
                "receipt-attempt-consumption",
                "final terminal report hash differs from receipt trial",
            )
    if finals_by_unit:
        _fail(
            "receipt-attempt-consumption",
            "final terminal exists outside the predeclared unit projection",
        )


def _assert_git_history_append_only(
    root: Path,
    relative_path: str,
    *,
    label: str,
) -> None:
    """Reject deletion/recreation and non-prefix edits within this repository."""
    history = _git(root, (
        "log", "--format=%H", "--reverse", "--full-history", "HEAD", "--",
        relative_path,
    ))
    if history.returncode != 0:
        _fail("receipt-history", f"{label} history walk failed")
    previous: bytes | None = None
    for raw_commit in history.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise AcceptanceReceiptError(
                f"[receipt-history] {label} history returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("receipt-history", f"{label} history returned an invalid commit ID")
        blob = _blob_at_commit(root, commit_id, relative_path)
        if blob is None:
            _fail("receipt-history", f"{label} was deleted in committed history")
        if previous is not None and (
            not blob.startswith(previous) or len(blob) <= len(previous)
        ):
            _fail("receipt-history", f"{label} history is not a strict prefix extension")
        previous = blob
    if previous is not None:
        current = _read_regular_bytes(
            _resolved_reference(root, relative_path, label), label=label,
        )
        if not current.startswith(previous):
            _fail(
                "receipt-history",
                f"working {label} does not extend committed history",
            )


def _assert_not_shallow(root: Path) -> None:
    result = _git(root, ("rev-parse", "--is-shallow-repository"))
    if result.returncode != 0:
        _fail("receipt-history", "shallow-repository state cannot be determined")
    if result.stdout.strip() != b"false":
        _fail("receipt-history", "shallow repositories are not accepted")


def _assert_no_grafts_or_replace_refs(root: Path) -> None:
    graft = _git(root, ("rev-parse", "--git-path", "info/grafts"))
    if graft.returncode != 0:
        _fail("receipt-history", "Git graft path could not be resolved")
    try:
        graft_path = Path(graft.stdout.decode("utf-8").strip())
    except UnicodeDecodeError as exc:
        raise AcceptanceReceiptError(
            "[receipt-history] Git graft path was not UTF-8"
        ) from exc
    if not graft_path.is_absolute():
        graft_path = root / graft_path
    if graft_path.exists() or graft_path.is_symlink():
        _fail("receipt-history", "Git graft files are not accepted")
    replaces = _git(root, (
        "for-each-ref", "--format=%(refname)", "refs/replace",
    ))
    if replaces.returncode != 0:
        _fail("receipt-history", "replace-ref enumeration failed")
    if replaces.stdout.splitlines():
        _fail("receipt-history", "Git replace refs are not accepted")


_ATTEMPT_BATCH_MAX_BYTES = 256 * 1024 * 1024
_ATTEMPT_HISTORY_RAW_ARGS = (
    "log", "--stdin", "--root", "--diff-merges=separate", "--full-history",
    "--raw", "-z", "--no-renames", "--no-abbrev", "--no-show-signature",
    "--format=%H", "--diff-filter=AMT",
)


def _attempt_batch_check(root: Path, requests: Sequence[bytes]) -> list[list[bytes]]:
    if not requests:
        return []
    result = _git(root, ("cat-file", "--batch-check"), input_bytes=b"\n".join(requests) + b"\n")
    if result.returncode:
        _fail("receipt-history", "attempt tree blob cannot be read")
    return _attempt_parse_batch_check(result.stdout, requests)


def _attempt_parse_batch_check(data: bytes, requests: Sequence[bytes]) -> list[list[bytes]]:
    lines = data.splitlines()
    if len(lines) != len(requests):
        _fail("receipt-history", "attempt tree blob cannot be read")
    entries = []
    for request, line in zip(requests, lines):
        fields = line.split()
        if line == request + b" missing":
            entries.append([])
        elif (len(fields) == 3 and re.fullmatch(rb"[0-9a-f]{40}", fields[0])
              and fields[1] in {b"blob", b"tree", b"commit", b"tag"}
              and fields[2].isdigit()):
            entries.append(fields)
        else:
            _fail("receipt-history", "attempt tree blob cannot be read")
    return entries


def _attempt_parse_batch(data: bytes, entries: Sequence[list[bytes]], on_error=None):
    """Yield size-framed bodies; never treat body LF or NUL as separators."""
    offset = 0
    for entry in entries:
        header = b" ".join(entry) + b"\n"
        end = offset + len(header) + int(entry[2])
        if data[offset:offset + len(header)] != header or data[end:end + 1] != b"\n":
            if not data[offset:] or (end >= len(data) and entry is not entries[-1]) or on_error is None:
                _fail("receipt-history", "attempt tree blob cannot be read")
            on_error(entry[0])
            if end >= len(data):
                offset = len(data)
                break
        else:
            yield entry[0], data[offset + len(header):end]
        offset = end + 1
    if offset != len(data):
        _fail("receipt-history", "attempt tree blob cannot be read")


def _attempt_batch_chunks(entries: Sequence[list[bytes]], cap: int):
    chunk, total = [], 0
    for entry in entries:
        size = len(b" ".join(entry)) + 2 + int(entry[2])
        if chunk and total + size > cap:
            yield chunk
            chunk, total = [], 0
        chunk.append(entry)
        total += size
    if chunk:
        yield chunk


def _attempt_read_batch(root: Path, entries: Sequence[list[bytes]], on_error=None):
    result = _git(root, ("cat-file", "--batch"),
                  input_bytes=b"\n".join(entry[0] for entry in entries) + b"\n")
    if result.returncode:
        _fail("receipt-history", "attempt tree blob cannot be read")
    yield from _attempt_parse_batch(result.stdout, entries, on_error)


def _attempt_canonical_tree(data: bytes, component: bytes, *, leaf: bool) -> bytes | None:
    offset = 0
    while offset < len(data):
        end = data.find(b"\0", offset)
        if end < 0 or end + 21 > len(data):
            _fail("receipt-history", "attempt registry tree walk failed")
        mode, separator, name = data[offset:end].partition(b" ")
        if not separator:
            _fail("receipt-history", "attempt registry tree walk failed")
        if name == component:
            if not leaf and mode != b"40000":
                return None
            if leaf and mode not in {b"100644", b"100755", b"120000"}:
                return None
            return data[end + 1:end + 21].hex().encode("ascii")
        offset = end + 21
    return None


def _attempt_raw_entries(data: bytes, ranks: Mapping[bytes, int]):
    fields = iter(data.split(b"\0"))
    rank = None
    for field in fields:
        field = field.lstrip(b"\n")
        if not field:
            continue
        if re.fullmatch(rb"[0-9a-f]{40}", field):
            rank = ranks.get(field)
            continue
        metadata = field.split()
        if (len(metadata) != 5 or not re.fullmatch(rb":[0-7]{6}", metadata[0])
                or not re.fullmatch(rb"[0-7]{6}", metadata[1])
                or any(not re.fullmatch(rb"[0-9a-f]{40}", oid) for oid in metadata[2:4])
                or metadata[4] not in {b"A", b"M", b"T"}):
            _fail("receipt-history", "attempt registry tree walk failed")
        path = next(fields, None)
        if path is None:
            _fail("receipt-history", "attempt registry tree walk failed")
        if rank is not None and metadata[1] in {b"100644", b"100755", b"120000"}:
            yield rank, path, metadata[3]


def _looks_like_attempt_genesis(data: bytes) -> bool:
    if not data:
        return False
    first_line = data.splitlines()[0]
    if not any(
        schema.encode("ascii") in first_line
        for schema in _ATTEMPT_SCHEMA_VERSIONS
    ):
        return False
    try:
        value = _decode_json(first_line)
    except AcceptanceReceiptError:
        return False
    return (
        isinstance(value, Mapping)
        and value.get("schema_version") in _ATTEMPT_SCHEMA_VERSIONS
        and value.get("event") == "freeze"
    )


def _assert_attempt_registry_history_append_only(
    root: Path,
    relative_path: str,
    *,
    current_bytes: bytes,
    batch_max_bytes: int | None = None,
) -> None:
    """Apply the all-ref gate.

    Unattributable process/response anomalies have no ordering guarantee.
    """
    cap = _ATTEMPT_BATCH_MAX_BYTES if batch_max_bytes is None else batch_max_bytes
    if relative_path != DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix():
        _fail("receipt-history", "attempt registry path is not canonical")
    _assert_no_grafts_or_replace_refs(root)
    _assert_not_shallow(root)
    commits = _git(root, ("rev-list", "--all", "--topo-order", "--reverse"))
    if commits.returncode != 0:
        _fail("receipt-history", "attempt registry full history walk failed")
    commit_ids = []
    for raw_commit in commits.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise AcceptanceReceiptError(
                "[receipt-history] attempt history commit is not ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("receipt-history", "attempt history returned an invalid commit ID")
        commit_ids.append(raw_commit)
    ranks = {oid: rank for rank, oid in enumerate(commit_ids)}
    directories = _attempt_batch_check(root, [oid + b"^{tree}" for oid in commit_ids])
    canonical_ids = [entry[0] if entry and entry[1] == b"tree" else None for entry in directories]
    trees = {entry[0]: entry for entry in directories if entry and entry[1] == b"tree"}
    components = DEFAULT_ATTEMPT_REGISTRY_PATH.parts
    for depth, component in enumerate(components):
        leaf = depth == len(components) - 1
        canonical_trees = {}
        for chunk in _attempt_batch_chunks(list(trees.values()), cap):
            for oid, data in _attempt_read_batch(root, chunk):
                canonical_trees[oid] = _attempt_canonical_tree(data, component.encode(), leaf=leaf)
        canonical_ids = [canonical_trees.get(oid) for oid in canonical_ids]
        if not leaf:
            oids = list(dict.fromkeys(oid for oid in canonical_ids if oid is not None))
            trees = {entry[0]: entry for entry in _attempt_batch_check(root, oids)
                     if entry and entry[1] == b"tree"}
    first, alternate, errors = {}, {}, []
    for rank, oid in enumerate(canonical_ids):
        if oid is not None:
            first.setdefault(oid, rank)
    paths = {oid: (rank, relative_path.encode()) for oid, rank in first.items()}
    if commit_ids:
        raw = _git(root, _ATTEMPT_HISTORY_RAW_ARGS, input_bytes=commits.stdout)
        if raw.returncode:
            _fail("receipt-history", "attempt registry tree walk failed")
        for rank, path_bytes, oid in _attempt_raw_entries(raw.stdout, ranks):
            first[oid] = min(rank, first.get(oid, rank))
            paths[oid] = min(paths.get(oid, (rank, path_bytes)), (rank, path_bytes))
            try:
                path = path_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                try:
                    raise AcceptanceReceiptError(
                        "[receipt-history] attempt tree entry is not valid UTF-8") from exc
                except AcceptanceReceiptError as error:
                    errors.append((rank, 0, path_bytes, error))
                continue
            if path != relative_path:
                alternate[oid] = min(rank, alternate.get(oid, rank))
    canonical_set = set(canonical_ids) - {None}
    ordered = list(dict.fromkeys(oid for oid in canonical_ids if oid is not None))
    ordered.extend(sorted((oid for oid in first if oid not in canonical_set), key=first.get))
    entries = []
    for oid, entry in zip(ordered, _attempt_batch_check(root, ordered)):
        if not entry or entry[0] != oid or entry[1] != b"blob":
            errors.append((first[oid], 0, paths[oid][1], AcceptanceReceiptError(
                "[receipt-history] attempt tree blob cannot be read")))
        else:
            entries.append(entry)
    def body_error(oid):
        errors.append((first[oid], 0, paths[oid][1], AcceptanceReceiptError(
            "[receipt-history] attempt tree blob cannot be read")))

    bodies, genesis = {}, set()
    for chunk in _attempt_batch_chunks(entries, cap):
        for oid, data in _attempt_read_batch(root, chunk, body_error):
            if oid in canonical_set:
                bodies[oid] = data
            if oid in alternate and _looks_like_attempt_genesis(data):
                genesis.add(oid)
    previous: bytes | None = None
    validated = set()
    for rank, oid in enumerate(canonical_ids):
        try:
            if oid is None:
                if previous is not None:
                    _fail("receipt-history", "attempt registry was deleted")
                continue
            if oid not in bodies:
                break  # The ranked tree-read error already records this failure.
            canonical = bodies[oid]
            if oid not in validated:
                try:
                    _attempt_core.load_attempt_registry(
                        canonical, profile=_RECEIPT_ATTEMPT_PROFILE,
                    )
                except _attempt_core.AttemptRegistryCoreError as exc:
                    raise AcceptanceReceiptError(f"[receipt-attempt-registry] {exc}") from exc
                validated.add(oid)
            if previous is not None and canonical != previous and (
                not canonical.startswith(previous) or len(canonical) <= len(previous)
            ):
                _fail("receipt-history", "attempt registry history is not a strict prefix extension")
            previous = canonical
        except AcceptanceReceiptError as exc:
            errors.append((rank, 1, b"", exc))
            break
    for oid in genesis:
        errors.append((alternate[oid], 2, b"", AcceptanceReceiptError(
            "[receipt-history] alternate attempt registry genesis exists on a ref")))
    if errors:
        raise min(errors, key=lambda error: error[:3])[3]
    try:
        _attempt_core.load_attempt_registry(
            current_bytes, profile=_RECEIPT_ATTEMPT_PROFILE,
        )
    except _attempt_core.AttemptRegistryCoreError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-attempt-registry] {exc}"
        ) from exc
    if previous is not None and not current_bytes.startswith(previous):
        _fail("receipt-history", "working attempt registry does not extend committed history")


def _blob_at_commit(root: Path, commit_id: str, relative_path: str) -> bytes | None:
    listing = _git(root, (
        "ls-tree", "-z", "--full-name", commit_id, "--", relative_path,
    ))
    if listing.returncode != 0:
        _fail("receipt-history", "history tree lookup failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("receipt-history", "history path is not a single entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if (
        separator != b"\t"
        or len(fields) != 3
        or entry_path != os.fsencode(relative_path)
        or fields[1] != b"blob"
        or fields[0] not in {b"100644", b"100755"}
    ):
        _fail("receipt-history", "history entry is not a literal regular file")
    blob = _git(root, ("cat-file", "blob", fields[2].decode("ascii")))
    if blob.returncode != 0:
        _fail("receipt-history", "history blob cannot be read")
    return blob.stdout


def verify_acceptance_receipt(
    receipt_path: Path,
    *,
    repository_root: Path,
) -> VerifiedAcceptanceReceipt:
    """Freshly hash every immutable reference and the lifecycle prefix."""
    root = _repository_root(repository_root)
    supplied = Path(receipt_path)
    lexical = Path(os.path.abspath(os.fspath(
        supplied if supplied.is_absolute() else root / supplied
    )))
    try:
        relative = lexical.relative_to(root).as_posix()
        path = lexical.resolve(strict=True)
        path.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AcceptanceReceiptError(
            "[receipt-path] receipt is absent or outside repository"
        ) from exc
    if path != lexical:
        _fail("receipt-path", "receipt path traverses a symlink component")
    raw = _read_regular_bytes(path, label="receipt")
    receipt = parse_acceptance_receipt_bytes(raw)
    expected_relative = (
        DEFAULT_RECEIPT_DIR / f"{receipt.manifest_sha256}.json"
    ).as_posix()
    if relative != expected_relative:
        _fail("receipt-path", "receipt path does not match manifest_sha256")
    committed = _blob_at_head(root, relative)
    if committed is None:
        _fail("receipt-untracked", "receipt is not tracked at Git HEAD")
    if committed != raw:
        _fail("receipt-head-mismatch", "working receipt bytes differ from Git HEAD")

    _assert_digest(root, receipt.manifest_path, receipt.manifest_sha256, "manifest")
    _assert_digest(root, receipt.registry_path, receipt.registry_blob_sha256, "registry")
    _assert_git_history_append_only(root, receipt.lifecycle_path, label="lifecycle")
    _assert_prefix_digest(
        root,
        receipt.lifecycle_path,
        receipt.lifecycle_prefix_bytes,
        receipt.lifecycle_prefix_sha256,
        "lifecycle",
    )
    rederive_arm_execution = receipt.schema_version in {
        PREVIOUS_SCHEMA_VERSION,
        CROSS_BINDING_V1_SCHEMA_VERSION,
        CROSS_BINDING_V2_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }
    if rederive_arm_execution:
        _require_ratified_legacy_arm_authority()
    descriptor_proofs: list[bool] = []
    for trial in receipt.trials:
        report_bytes = _assert_digest(
            root, trial.report_path, trial.report_sha256, "trial report",
        )
        journal_bytes = _assert_digest(
            root,
            trial.attempt_journal_path,
            trial.attempt_journal_sha256,
            "attempt journal",
        )
        if rederive_arm_execution:
            descriptor_proven = _verify_v2_trial_arm_execution(
                trial,
                report_bytes=report_bytes,
                journal_bytes=journal_bytes,
            )
            _assert_rederived_trial_arm_execution(root, trial)
            descriptor_proofs.append(descriptor_proven)
        if receipt.schema_version == SCHEMA_VERSION:
            rederived_leaf = _rederive_cross_binding_receipt_sha256(
                root,
                trial,
                report_bytes=report_bytes,
                journal_bytes=journal_bytes,
            )
            if trial.cross_binding_receipt_sha256 != rederived_leaf:
                _fail(
                    "receipt-cross-binding",
                    f"trial_id={trial.trial_id} leaf differs from independently "
                    "rederived projection",
                )
    if (
        receipt.schema_version in {
            PREVIOUS_SCHEMA_VERSION,
            CROSS_BINDING_V1_SCHEMA_VERSION,
            CROSS_BINDING_V2_SCHEMA_VERSION,
            SCHEMA_VERSION,
        }
        and C02_ARM_BINDING_UNPROVEN not in receipt.non_certifying_reason_codes
        and not _arm_execution_authorizes_reason_drop(descriptor_proofs)
    ):
        _fail(
            "receipt-mandatory-reasons",
            "c02-arm-binding-unproven was dropped without descriptor proof",
        )
    if rederive_arm_execution and any(
        trial.status == "complete" and not descriptor_proven
        for trial, descriptor_proven in zip(receipt.trials, descriptor_proofs)
    ):
        _fail(
            "receipt-arm-binding",
            "complete trial lacks descriptor proof",
        )
    if receipt.schema_version in {
        CROSS_BINDING_V1_SCHEMA_VERSION,
        CROSS_BINDING_V2_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }:
        cross_binding_schema_version = (
            LEGACY_CROSS_BINDING_RECEIPT_SCHEMA_VERSION
            if receipt.schema_version == CROSS_BINDING_V1_SCHEMA_VERSION
            else CROSS_BINDING_RECEIPT_SCHEMA_VERSION
        )
        aggregate = _cross_binding_aggregate_sha256_for_schema([
            {
                "trial_id": trial.trial_id,
                "receipt_sha256": trial.cross_binding_receipt_sha256,
            }
            for trial in receipt.trials
        ], cross_binding_schema_version=cross_binding_schema_version)
        if receipt.cross_binding_receipt_sha256 != aggregate:
            _fail(
                "receipt-cross-binding",
                "top-level cross-binding aggregate differs from trial leaves",
            )
    if receipt.schema_version == SCHEMA_VERSION:
        _assert_attempt_registry_consumption(root, receipt)
    return VerifiedAcceptanceReceipt(
        repository_root=root,
        path=path,
        relative_path=relative,
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        receipt=receipt,
        _seal=_VERIFIED_RECEIPT_SEAL,
    )


def require_current_verified_receipt(
    verified: VerifiedAcceptanceReceipt,
) -> VerifiedAcceptanceReceipt:
    """Require v5 and reverify it so later byte changes cannot reuse it."""
    if (
        not isinstance(verified, VerifiedAcceptanceReceipt)
        or verified._seal is not _VERIFIED_RECEIPT_SEAL
    ):
        _fail("receipt-capability", "receipt was not issued by the verifier")
    if verified.receipt.schema_version != SCHEMA_VERSION:
        _fail(
            "receipt-capability",
            "downstream capability requires the current receipt schema",
        )
    current = verify_acceptance_receipt(
        verified.path, repository_root=verified.repository_root,
    )
    if current.sha256 != verified.sha256 or current.raw_bytes != verified.raw_bytes:
        _fail("receipt-capability", "receipt changed after capability issuance")
    return current
