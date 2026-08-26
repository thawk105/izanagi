# -*- coding: utf-8 -*-
"""Fail-closed collector for saved login-side ``qstat -J -f`` output.

The collector never launches qstat.  Its request ID comes from a registry
start event loaded by :func:`bind_scheduler_request_from_registry_start`, not
from an independently selectable string argument.  The current S8B start
schema has no ``scheduler_request_id`` field, so that production binding path
is intentionally inert until a separately adjudicated schema change exists.
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re
import stat
from types import MappingProxyType
from typing import Any, Mapping

from ..scheduler_nqsv import QSTAT_REQUEST_ID_RE
from . import attempt_registry_core as _registry_core
from .create_only_store import (
    CreateOnlyStoreError,
    claim_bytes,
    identity_claim_path,
    read_claim_bytes,
)
from .s8b_attempt_profile import (
    S8B_RECOVERY_FAILURE_REASONS,
    S8B_RECOVERY_RECEIPT_EVENT,
    S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
    S8B_RECOVERY_RECEIPT_SOURCE,
)


AUTHORITY_ID = "izanagi-s8b-nqsv-qstat-j-f/v1"
RAW_SCHEDULER_ACCOUNTING_MAX_BYTES = 1024 * 1024
RECEIPT_MAX_BYTES = 64 * 1024
REGISTRY_MAX_BYTES = 16 * 1024 * 1024
FAILURE_REASONS = frozenset({
    "node_failure",
    "scheduler_external_interruption",
})
assert FAILURE_REASONS == S8B_RECOVERY_FAILURE_REASONS

# This is an observed value range, not a value-to-meaning correspondence table.
OBSERVED_EXIT_CODE_COUNTS = MappingProxyType({
    "(none)": 263,
    "1100": 4,
    "F": 3,
    "9": 2,
    "A": 1,
})

# No observed Exit Code has an established meaning for either closed reason.
# In particular, the presence of a value in OBSERVED_EXIT_CODE_COUNTS is not a
# classification rule.
FAILURE_REASON_RULES: Mapping[str, str] = MappingProxyType({})


def authority_policy_document() -> dict[str, Any]:
    """Return a fresh JSON policy object whose canonical hash is authoritative."""

    return {
        "schema_version": "s8b-scheduler-accounting-authority-policy/v1",
        "authority_id": AUTHORITY_ID,
        "evidence": {
            "command_argv": [
                "qstat", "-J", "-f", "<bound-scheduler-request-id>",
            ],
            "capture_side": "login",
            "raw_record_max_bytes": RAW_SCHEDULER_ACCOUNTING_MAX_BYTES,
            "required_fields": [
                "Request ID", "Execution Host", "Exit Code",
            ],
            "time_fields": [
                "Created Request Time",
                "Started Request Time",
                "Ended Request Time",
            ],
        },
        "receipt": {
            "schema_version": S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
            "event": S8B_RECOVERY_RECEIPT_EVENT,
            "source": S8B_RECOVERY_RECEIPT_SOURCE,
            "failure_reason_closed_set": sorted(FAILURE_REASONS),
        },
        "failure_reason_rules": [],
        "observed_exit_code_counts": [
            [value, count] for value, count in OBSERVED_EXIT_CODE_COUNTS.items()
        ],
    }


AUTHORITY_POLICY_BYTES = _registry_core.canonical_json_bytes(
    authority_policy_document()
)
AUTHORITY_POLICY_SHA256 = hashlib.sha256(AUTHORITY_POLICY_BYTES).hexdigest()


class SchedulerAccountingCollectorError(RuntimeError):
    """A collector gate rejected the input, with a stable distinguishing code."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


class SchedulerAccountingUnclassifiable(SchedulerAccountingCollectorError):
    """Well-formed evidence does not name a reason in the closed policy."""


_BOUND_SEAL = object()
_RECEIPT_IDENTITY_SEAL = object()
_RECEIPT_ROOT_SEAL = object()
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_EXECUTION_HOST_RE = re.compile(
    r"(?m)^[ \t]*Execution Host[ \t]*=[ \t]*(\S+)[ \t]*\r?$"
)
_EXIT_CODE_RE = re.compile(
    r"(?m)^[ \t]*Exit Code[ \t]*=[ \t]*(\S+)[ \t]*\r?$"
)
_TIME_LABELS = (
    "Created Request Time",
    "Started Request Time",
    "Ended Request Time",
)
_TIME_RES = {
    label: re.compile(
        rf"(?m)^[ \t]*{re.escape(label)}[ \t]*[:=][ \t]*"
        r"(\S(?:[^\r\n]*\S)?)[ \t]*\r?$"
    )
    for label in _TIME_LABELS
}
_NQSV_TIME_RE = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) "
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"([0-3]?\d) ([0-2]\d):([0-5]\d):([0-5]\d) (\d{4})"
)
_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_COLLECTED_AT_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)


@dataclass(frozen=True, slots=True, init=False)
class BoundSchedulerRequest:
    """A request ID and target hash loaded together from one registry start.

    S8B start rows do not currently declare ``scheduler_request_id``.  No
    production instance can therefore be issued by the current schema; this
    type exists so the collector remains fail-closed and ready for a separately
    adjudicated binding field rather than trusting a synthetic mapping.
    """

    scheduler_request_id: str
    target_start_event_sha256: str
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True, init=False)
class SchedulerAccountingReceiptIdentity:
    """Untrusted public fields sufficient only to locate a receipt claim."""

    scheduler_request_id: str
    target_start_event_sha256: str
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True, init=False)
class SchedulerAccountingReceiptRoot:
    """Typed issuance root derived from the shared admission root."""

    path: Path
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SchedulerAccountingReceipt:
    """Canonical standalone receipt bytes and their digest."""

    canonical_bytes: bytes
    sha256: str
    failure_reason: str


@dataclass(frozen=True, slots=True)
class _ParsedAccountingRecord:
    scheduler_request_id: str
    execution_host: str
    exit_code: str
    times: tuple[datetime, datetime, datetime] | None


def _raise(code: str, detail: str) -> None:
    raise SchedulerAccountingCollectorError(code, detail)


def _checked_request_id(value: object, *, code: str) -> str:
    if type(value) is not str or not value or len(value) > 256:
        _raise(code, "scheduler request ID is invalid")
    if any(character.isspace() for character in value):
        _raise(code, "scheduler request ID contains whitespace")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        _raise(code, "scheduler request ID normalizes to empty")
    return normalized


def _checked_digest(value: object, *, code: str, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _raise(code, f"{label} is not a SHA-256 digest")
    return value


def bind_scheduler_request_from_start_event(
    start_event: Mapping[str, object],
) -> SchedulerAccountingReceiptIdentity:
    """Return an untrusted path identity, never a bound scheduler request.

    This legacy-named entry remains for admission's deterministic standalone
    receipt lookup.  A caller-assembled mapping can locate a public identity
    path, but the returned exact type is rejected by the collector and cannot
    authorize or issue a receipt.
    """

    if not isinstance(start_event, Mapping):
        _raise("bound-start-event-type", "start event must be a mapping")
    if start_event.get("event") != "start":
        _raise("bound-start-event-kind", "registry event is not a start event")
    request_id = _checked_request_id(
        start_event.get("scheduler_request_id"), code="bound-request-id",
    )
    target = _checked_digest(
        start_event.get("event_sha256"),
        code="bound-start-event-sha256",
        label="start_event.event_sha256",
    )
    identity = object.__new__(SchedulerAccountingReceiptIdentity)
    object.__setattr__(identity, "scheduler_request_id", request_id)
    object.__setattr__(identity, "target_start_event_sha256", target)
    object.__setattr__(identity, "_seal", _RECEIPT_IDENTITY_SEAL)
    return identity


def _new_bound_scheduler_request(
    scheduler_request_id: object,
    target_start_event_sha256: object,
) -> BoundSchedulerRequest:
    request_id = _checked_request_id(
        scheduler_request_id, code="bound-request-id",
    )
    target = _checked_digest(
        target_start_event_sha256,
        code="bound-start-event-sha256",
        label="start_event.event_sha256",
    )
    bound = object.__new__(BoundSchedulerRequest)
    object.__setattr__(bound, "scheduler_request_id", request_id)
    object.__setattr__(bound, "target_start_event_sha256", target)
    object.__setattr__(bound, "_seal", _BOUND_SEAL)
    return bound


def _read_registry_bytes(path: Path) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        _raise("bound-registry-platform-no-follow", "O_NOFOLLOW is required")
    try:
        descriptor = os.open(
            os.fspath(Path(path)),
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow,
        )
    except OSError as exc:
        code = (
            "bound-registry-no-follow"
            if exc.errno == errno.ELOOP else "bound-registry-open"
        )
        _raise(code, f"cannot open attempt registry: {exc}")
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            _raise(
                "bound-registry-not-regular",
                "attempt registry is not a regular file",
            )
        if metadata.st_size > REGISTRY_MAX_BYTES:
            _raise("bound-registry-too-large", "attempt registry is too large")
        chunks: list[bytes] = []
        remaining = REGISTRY_MAX_BYTES + 1
        while remaining:
            try:
                chunk = os.read(descriptor, min(65536, remaining))
            except OSError as exc:
                _raise("bound-registry-read", f"cannot read attempt registry: {exc}")
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > REGISTRY_MAX_BYTES:
            _raise("bound-registry-too-large", "attempt registry is too large")
        return raw
    finally:
        os.close(descriptor)


def bind_scheduler_request_from_registry_start(
    registry_path: Path,
    *,
    profile: object,
    binding: object,
    slot_id: tuple[str, str, int, int],
) -> BoundSchedulerRequest:
    """Load one exact registry start row and bind its scheduler request ID.

    The current S8B start schema does not contain ``scheduler_request_id``.
    Consequently a valid current registry reaches
    ``bound-request-id-unavailable`` and this production path is inert.  The
    function does not infer an ID from a caller argument or from qstat bytes.
    """
    raw = _read_registry_bytes(Path(registry_path))
    try:
        rows = _registry_core.load_attempt_registry(
            raw, profile=profile, expected_binding=binding,
        )
    except _registry_core.AttemptRegistryCoreError as exc:
        raise SchedulerAccountingCollectorError(
            "bound-registry-invalid", str(exc),
        ) from exc
    matches = [
        row for row in rows
        if row.get("event") == "start"
        and (
            row.get("freeze_holdout_key"),
            row.get("configuration_id"),
            row.get("repetition"),
            row.get("attempt_ordinal"),
        ) == slot_id
    ]
    if len(matches) != 1:
        _raise(
            "bound-registry-start-count",
            "registry must contain exactly one start row for the requested slot",
        )
    start = matches[0]
    if "scheduler_request_id" not in start:
        _raise(
            "bound-request-id-unavailable",
            "current S8B start schema has no scheduler_request_id field; "
            "registry binding is inert",
        )
    return _new_bound_scheduler_request(
        start.get("scheduler_request_id"), start.get("event_sha256"),
    )


def _bound_scheduler_request_for_test(
    scheduler_request_id: str,
    target_start_event_sha256: str,
) -> BoundSchedulerRequest:
    """Test-only constructor kept outside every certified collector entry."""
    return _new_bound_scheduler_request(
        scheduler_request_id, target_start_event_sha256,
    )


def _check_bound_request(value: object) -> BoundSchedulerRequest:
    if type(value) is not BoundSchedulerRequest:
        _raise(
            "bound-request-type",
            "collector requires a BoundSchedulerRequest from a start event",
        )
    try:
        sealed = value._seal is _BOUND_SEAL
    except AttributeError:
        sealed = False
    if not sealed:
        _raise("bound-request-seal", "bound scheduler request seal is invalid")
    _checked_request_id(value.scheduler_request_id, code="bound-request-id")
    _checked_digest(
        value.target_start_event_sha256,
        code="bound-start-event-sha256",
        label="target_start_event_sha256",
    )
    return value


def _check_receipt_identity(
    value: object,
) -> BoundSchedulerRequest | SchedulerAccountingReceiptIdentity:
    if type(value) is BoundSchedulerRequest:
        return _check_bound_request(value)
    if (
        type(value) is SchedulerAccountingReceiptIdentity
        and value._seal is _RECEIPT_IDENTITY_SEAL
    ):
        _checked_request_id(value.scheduler_request_id, code="bound-request-id")
        _checked_digest(
            value.target_start_event_sha256,
            code="bound-start-event-sha256",
            label="target_start_event_sha256",
        )
        return value
    _raise(
        "receipt-identity-type",
        "receipt path requires a bound request or public path identity",
    )


def assert_authority_policy_literal(literal: str) -> None:
    """Require an independently stored policy literal to equal our calculation."""

    _checked_digest(
        literal,
        code="authority-policy-literal-invalid",
        label="authority policy literal",
    )
    if literal != AUTHORITY_POLICY_SHA256:
        _raise(
            "authority-policy-literal-mismatch",
            "computed authority policy SHA-256 differs from the supplied literal",
        )


def scheduler_accounting_receipt_root(
    shared_admission_root: Path,
) -> SchedulerAccountingReceiptRoot:
    """Purely derive the typed issuance root from a shared admission root."""
    if not isinstance(shared_admission_root, Path):
        _raise(
            "receipt-root-source-type",
            "shared admission root must be a Path",
        )
    if not shared_admission_root.is_absolute():
        _raise(
            "receipt-root-source-absolute",
            "shared admission root must be absolute",
        )
    capability = object.__new__(SchedulerAccountingReceiptRoot)
    object.__setattr__(capability, "path", shared_admission_root)
    object.__setattr__(capability, "_seal", _RECEIPT_ROOT_SEAL)
    return capability


def _check_receipt_root(
    value: object,
) -> SchedulerAccountingReceiptRoot:
    if (
        type(value) is not SchedulerAccountingReceiptRoot
        or value._seal is not _RECEIPT_ROOT_SEAL
        or not isinstance(value.path, Path)
        or not value.path.is_absolute()
    ):
        _raise(
            "receipt-root-capability",
            "collector requires a typed shared-admission-root capability",
        )
    return value


def scheduler_accounting_receipt_claim_path(
    receipt_root: Path,
    bound_request: BoundSchedulerRequest | SchedulerAccountingReceiptIdentity,
    *,
    authority_policy_sha256_literal: str,
) -> Path:
    """Return the claim path for the exact three-part receipt identity."""

    bound = _check_receipt_identity(bound_request)
    assert_authority_policy_literal(authority_policy_sha256_literal)
    try:
        return identity_claim_path(
            Path(receipt_root),
            namespace="scheduler-accounting",
            identity=(
                AUTHORITY_ID,
                AUTHORITY_POLICY_SHA256,
                bound.target_start_event_sha256,
            ),
        )
    except CreateOnlyStoreError as exc:
        _raise(f"claim-store-{exc.code}", exc.detail)


def _read_raw_record(path: Path) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        _raise("raw-path-platform-no-follow", "O_NOFOLLOW is required")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    try:
        descriptor = os.open(os.fspath(Path(path)), flags)
    except OSError as exc:
        code = "raw-path-no-follow" if exc.errno == errno.ELOOP else "raw-path-open"
        _raise(code, f"cannot open saved qstat output: {exc}")
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            _raise("raw-path-not-regular", "saved qstat output is not a regular file")
        if metadata.st_size > RAW_SCHEDULER_ACCOUNTING_MAX_BYTES:
            _raise(
                "raw-record-too-large",
                f"saved qstat output exceeds {RAW_SCHEDULER_ACCOUNTING_MAX_BYTES} bytes",
            )
        chunks: list[bytes] = []
        remaining = RAW_SCHEDULER_ACCOUNTING_MAX_BYTES + 1
        while remaining:
            try:
                chunk = os.read(descriptor, min(65536, remaining))
            except OSError as exc:
                _raise("raw-record-read", f"cannot read saved qstat output: {exc}")
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > RAW_SCHEDULER_ACCOUNTING_MAX_BYTES:
            _raise(
                "raw-record-too-large",
                f"saved qstat output exceeds {RAW_SCHEDULER_ACCOUNTING_MAX_BYTES} bytes",
            )
        return raw
    finally:
        os.close(descriptor)


def _parse_nqsv_time(value: str, *, label: str) -> datetime:
    match = _NQSV_TIME_RE.fullmatch(value)
    if match is None:
        _raise("time-field-format", f"{label} has an unsupported timestamp")
    weekday, month, day, hour, minute, second, year = match.groups()
    try:
        parsed = datetime(
            int(year), _MONTHS[month], int(day), int(hour), int(minute), int(second),
        )
    except ValueError as exc:
        _raise("time-field-format", f"{label} is not a calendar timestamp: {exc}")
    if _WEEKDAYS[parsed.weekday()] != weekday:
        _raise("time-field-weekday", f"{label} weekday differs from its date")
    return parsed


def _parse_time_fields(text: str) -> tuple[datetime, datetime, datetime] | None:
    matches = {label: _TIME_RES[label].findall(text) for label in _TIME_LABELS}
    present = {label for label, values in matches.items() if values}
    if not present:
        return None
    if present != set(_TIME_LABELS):
        _raise(
            "time-field-partial",
            "scheduler time fields must be either absent or the exact complete trio",
        )
    if any(len(values) != 1 for values in matches.values()):
        _raise("time-field-count", "each scheduler time field must occur exactly once")
    parsed = tuple(
        _parse_nqsv_time(matches[label][0], label=label)
        for label in _TIME_LABELS
    )
    if not parsed[0] <= parsed[1] <= parsed[2]:
        _raise("time-field-order", "scheduler timestamps are not monotonic")
    return parsed


def _parse_raw_record(
    raw: bytes, *, bound_request: BoundSchedulerRequest,
) -> _ParsedAccountingRecord:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _raise("raw-record-utf8", f"saved qstat output is not strict UTF-8: {exc}")

    request_ids = QSTAT_REQUEST_ID_RE.findall(text)
    if len(request_ids) != 1:
        _raise("request-id-count", "saved qstat output needs exactly one Request ID")
    observed = request_ids[0]
    observed_normalized = _checked_request_id(observed, code="request-id-invalid")
    expected_normalized = _checked_request_id(
        bound_request.scheduler_request_id, code="bound-request-id",
    )
    if observed_normalized != expected_normalized:
        _raise(
            "request-id-mismatch",
            "saved qstat Request ID differs from the registry-bound request ID",
        )

    hosts = _EXECUTION_HOST_RE.findall(text)
    if len(hosts) != 1:
        _raise(
            "execution-host-count",
            "saved qstat output needs exactly one Execution Host",
        )
    execution_host = hosts[0]
    if len(execution_host) > 256:
        _raise("execution-host-invalid", "Execution Host is too long")

    exit_codes = _EXIT_CODE_RE.findall(text)
    if len(exit_codes) != 1:
        _raise("exit-code-count", "saved qstat output needs exactly one Exit Code")
    exit_code = exit_codes[0]
    if len(exit_code) > 64:
        _raise("exit-code-invalid", "Exit Code is too long")

    return _ParsedAccountingRecord(
        scheduler_request_id=observed,
        execution_host=execution_host,
        exit_code=exit_code,
        times=_parse_time_fields(text),
    )


def _failure_reason(record: _ParsedAccountingRecord) -> str:
    reason = FAILURE_REASON_RULES.get(record.exit_code)
    if reason is None:
        raise SchedulerAccountingUnclassifiable(
            "failure-reason-unclassifiable",
            "no measured Exit Code-to-failure-reason rule is established",
        )
    if reason not in FAILURE_REASONS:
        _raise("failure-reason-policy", "classification rule escaped the closed set")
    return reason


def _checked_collected_at(value: object, *, code: str) -> str:
    if type(value) is not str or _COLLECTED_AT_RE.fullmatch(value) is None:
        _raise(code, "collected_at is not an RFC 3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        _raise(code, f"collected_at is not a calendar timestamp: {exc}")
    if parsed.tzinfo != timezone.utc:
        _raise(code, "collected_at is not UTC")
    return value


def _collected_at_now() -> str:
    return datetime.now(timezone.utc).isoformat(
        timespec="microseconds",
    ).replace("+00:00", "Z")


def _assemble_receipt(
    *,
    bound_request: BoundSchedulerRequest,
    raw_sha256: str,
    failure_reason: str,
    collected_at: str,
) -> bytes:
    bound = _check_bound_request(bound_request)
    checked_raw_sha256 = _checked_digest(
        raw_sha256,
        code="receipt-raw-digest",
        label="raw scheduler accounting record SHA-256",
    )
    if failure_reason not in FAILURE_REASONS:
        _raise("receipt-failure-reason", "receipt reason escaped the closed set")
    checked_collected_at = _checked_collected_at(
        collected_at, code="receipt-collected-at",
    )
    document = {
        "schema_version": S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
        "event": S8B_RECOVERY_RECEIPT_EVENT,
        "source": S8B_RECOVERY_RECEIPT_SOURCE,
        "scheduler_request_id": bound.scheduler_request_id,
        "target_start_event_sha256": bound.target_start_event_sha256,
        "raw_scheduler_accounting_record_sha256": checked_raw_sha256,
        "authority_id": AUTHORITY_ID,
        "authority_policy_sha256": AUTHORITY_POLICY_SHA256,
        "failure_reason": failure_reason,
        "collected_at": checked_collected_at,
    }
    assert frozenset(document) == _registry_core._SCHEDULER_ACCOUNTING_RECEIPT_KEYS
    return _registry_core.canonical_json_bytes(document) + b"\n"


class _DuplicateReceiptKey(ValueError):
    pass


def _load_receipt_json(data: bytes) -> dict[str, Any]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _raise("existing-receipt-utf8", f"existing receipt is not strict UTF-8: {exc}")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateReceiptKey(key)
            result[key] = value
        return result

    try:
        document = json.loads(text, object_pairs_hook=no_duplicates)
    except _DuplicateReceiptKey as exc:
        _raise("existing-receipt-duplicate-key", f"duplicate JSON key: {exc}")
    except (json.JSONDecodeError, UnicodeError) as exc:
        _raise("existing-receipt-json", f"existing receipt is not JSON: {exc}")
    if type(document) is not dict:
        _raise("existing-receipt-object", "existing receipt is not a JSON object")
    return document


def _validated_existing_receipt(
    data: bytes,
    *,
    bound_request: BoundSchedulerRequest,
    raw_sha256: str,
    expected_failure_reason: str,
) -> SchedulerAccountingReceipt:
    document = _load_receipt_json(data)
    actual_keys = frozenset(document)
    if actual_keys != _registry_core._SCHEDULER_ACCOUNTING_RECEIPT_KEYS:
        _raise("existing-receipt-keys", "existing receipt key set is not exact")
    expected = {
        "schema_version": S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
        "event": S8B_RECOVERY_RECEIPT_EVENT,
        "source": S8B_RECOVERY_RECEIPT_SOURCE,
        "scheduler_request_id": bound_request.scheduler_request_id,
        "target_start_event_sha256": bound_request.target_start_event_sha256,
        "raw_scheduler_accounting_record_sha256": raw_sha256,
        "authority_id": AUTHORITY_ID,
        "authority_policy_sha256": AUTHORITY_POLICY_SHA256,
        "failure_reason": expected_failure_reason,
    }
    codes = {
        "schema_version": "existing-receipt-schema-version",
        "event": "existing-receipt-event",
        "source": "existing-receipt-source",
        "scheduler_request_id": "existing-receipt-request-id",
        "target_start_event_sha256": "existing-receipt-target",
        "raw_scheduler_accounting_record_sha256": "existing-receipt-raw-digest",
        "authority_id": "existing-receipt-authority-id",
        "authority_policy_sha256": "existing-receipt-authority-policy",
        "failure_reason": "existing-receipt-failure-reason",
    }
    for key, value in expected.items():
        if document.get(key) != value:
            _raise(codes[key], f"existing receipt {key} differs")
    _checked_collected_at(
        document.get("collected_at"), code="existing-receipt-collected-at",
    )
    canonical = _registry_core.canonical_json_bytes(document) + b"\n"
    if data != canonical:
        _raise("existing-receipt-canonical", "existing receipt bytes are not canonical")
    return SchedulerAccountingReceipt(
        canonical_bytes=data,
        sha256=hashlib.sha256(data).hexdigest(),
        failure_reason=expected_failure_reason,
    )


def collect_scheduler_accounting(
    bound_request: BoundSchedulerRequest,
    saved_qstat_output: Path,
    receipt_root: SchedulerAccountingReceiptRoot,
    *,
    authority_policy_sha256_literal: str,
) -> SchedulerAccountingReceipt:
    """Validate saved qstat bytes and create or replay one identity-bound receipt."""

    bound = _check_bound_request(bound_request)
    root = _check_receipt_root(receipt_root)
    assert_authority_policy_literal(authority_policy_sha256_literal)
    raw = _read_raw_record(Path(saved_qstat_output))
    parsed = _parse_raw_record(raw, bound_request=bound)
    raw_sha256 = hashlib.sha256(raw).hexdigest()

    # This raises for every current input because the measured rule table is empty.
    # No claim path is read or created before that fail-closed classification.
    failure_reason = _failure_reason(parsed)

    claim_path = scheduler_accounting_receipt_claim_path(
        root.path,
        bound,
        authority_policy_sha256_literal=authority_policy_sha256_literal,
    )
    try:
        existing = read_claim_bytes(claim_path, max_bytes=RECEIPT_MAX_BYTES)
    except CreateOnlyStoreError as exc:
        _raise(f"claim-store-{exc.code}", exc.detail)
    if existing is not None:
        return _validated_existing_receipt(
            existing,
            bound_request=bound,
            raw_sha256=raw_sha256,
            expected_failure_reason=failure_reason,
        )

    checked_collected_at = _checked_collected_at(
        _collected_at_now(), code="collected-at",
    )
    candidate = _assemble_receipt(
        bound_request=bound,
        raw_sha256=raw_sha256,
        failure_reason=failure_reason,
        collected_at=checked_collected_at,
    )
    try:
        claimed = claim_bytes(
            claim_path, candidate, max_bytes=RECEIPT_MAX_BYTES,
        )
    except CreateOnlyStoreError as exc:
        _raise(f"claim-store-{exc.code}", exc.detail)
    return _validated_existing_receipt(
        claimed.data,
        bound_request=bound,
        raw_sha256=raw_sha256,
        expected_failure_reason=failure_reason,
    )
