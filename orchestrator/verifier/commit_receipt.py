# -*- coding: utf-8 -*-
"""Verifier-issued, process-bound capabilities for terminal COMMIT records."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from types import MappingProxyType
from typing import Any, Mapping, Sequence


RECEIPT_PAYLOAD_KEY = "commit_verification_receipt"
RECEIPT_SCHEMA = "campaign-commit-verification-receipt/v1"
REMOTE_VERIFICATION_RECEIPT_SCHEMA = "remote-verification-receipt/v1"
CAMPAIGN_WAL_SINK = "campaign-wal"
QUALIFICATION_SINK = "qualification-evaluation"
_SINK_KINDS = frozenset({CAMPAIGN_WAL_SINK, QUALIFICATION_SINK})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_TOKEN = object()
_PROCESS_SEAL = secrets.token_bytes(32)
_PROCESS_SEAL_SHA256 = hashlib.sha256(_PROCESS_SEAL).hexdigest()
_REMOTE_ADMISSION_LOCK = threading.Lock()
_REMOTE_ADMISSION_PID = os.getpid()
_ADMITTED_REMOTE_RECEIPTS: set[tuple[str, str]] = set()
CAMPAIGN_LOCK_ABSENT_SHA256 = hashlib.sha256(
    b"izanagi-campaign-lock-absent-snapshot-v1"
).hexdigest()


class CommitReceiptError(ValueError):
    """A verifier receipt is absent, forged, stale, or bound elsewhere."""


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise CommitReceiptError("receipt value is not canonical JSON") from exc


def _domain_digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical_bytes(value)).hexdigest()


def _freeze_json(value):
    if type(value) is dict:
        return MappingProxyType({
            key: _freeze_json(item) for key, item in value.items()
        })
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value):
    if type(value) is MappingProxyType:
        return {key: _thaw_json(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_thaw_json(item) for item in value]
    return value


def terminal_payload_sha256(payload: Mapping[str, Any]) -> str:
    if type(payload) is not dict:
        raise CommitReceiptError("terminal payload must be an exact dict")
    if RECEIPT_PAYLOAD_KEY in payload:
        raise CommitReceiptError("terminal payload already contains a receipt")
    return _domain_digest(b"izanagi-commit-terminal-payload-v1", payload)


def campaign_lock_bytes_sha256(raw: object) -> str:
    """Hash one caller-owned, non-empty campaign.lock byte snapshot."""
    if type(raw) is not bytes or not raw:
        raise CommitReceiptError("campaign.lock byte snapshot is empty or invalid")
    return hashlib.sha256(raw).hexdigest()


def campaign_lock_sha256(layout: object) -> str:
    path = getattr(layout, "lock_file", None)
    if type(path) is not str or not path:
        raise CommitReceiptError("campaign layout has no exact lock path")
    try:
        with open(path, "rb") as stream:
            raw = stream.read()
    except OSError as exc:
        raise CommitReceiptError("campaign.lock is unavailable") from exc
    if not raw:
        raise CommitReceiptError("campaign.lock is empty")
    return campaign_lock_bytes_sha256(raw)


def campaign_lock_sha256_or_absent(layout: object) -> str:
    """Hash one observed lock, or bind an explicitly absent snapshot."""
    path = getattr(layout, "lock_file", None)
    if type(path) is not str or not path:
        raise CommitReceiptError("campaign layout has no exact lock path")
    if not os.path.lexists(path):
        return CAMPAIGN_LOCK_ABSENT_SHA256
    return campaign_lock_sha256(layout)


class CommitReceipt:
    """Opaque live capability; sinks persist only its validated projection."""

    __slots__ = ("_record", "_pid", "_process_seal", "_token", "_sealed")

    def __init__(self, record: dict[str, Any], token: object):
        if token is not _RECEIPT_TOKEN:
            raise TypeError("CommitReceipt is verifier-issued")
        object.__setattr__(self, "_record", _freeze_json(record))
        object.__setattr__(self, "_pid", os.getpid())
        object.__setattr__(self, "_process_seal", _PROCESS_SEAL)
        object.__setattr__(self, "_token", token)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("CommitReceipt is immutable")
        object.__setattr__(self, name, value)


def _bind_replay_verification_evidence():
    issuer_token = object()
    issued: dict[object, tuple[object, ...]] = {}

    class _ReplayVerificationEvidence:
        """Opaque evidence admitted from an exact certified campaign view."""

        __slots__ = ("_nonce",)

        def __init__(
                self, *, receipt: Mapping[str, Any],
                source_campaign_lock_sha256: str,
                source_wal_sha256: str, source_variant: str,
                _token: object = None,
        ) -> None:
            if _token is not issuer_token:
                raise TypeError(
                    "ReplayVerificationEvidence is admission-issued"
                )
            nonce = object()
            issued[nonce] = (
                _freeze_json(dict(receipt)),
                source_campaign_lock_sha256,
                source_wal_sha256,
                source_variant,
                os.getpid(),
            )
            object.__setattr__(self, "_nonce", nonce)

        def _projection(self) -> tuple[object, ...]:
            try:
                projection = issued[self._nonce]
            except (AttributeError, KeyError, TypeError) as exc:
                raise CommitReceiptError(
                    "replay evidence has no admission authority"
                ) from exc
            if (type(self) is not _ReplayVerificationEvidence
                    or projection[4] != os.getpid()):
                raise CommitReceiptError(
                    "exact replay verification evidence required"
                )
            return projection

    def issue(**fields):
        return _ReplayVerificationEvidence(**fields, _token=issuer_token)

    return _ReplayVerificationEvidence, issue


(
    ReplayVerificationEvidence,
    _issue_replay_verification_evidence,
) = _bind_replay_verification_evidence()
del _bind_replay_verification_evidence


def _bind_remote_verification_evidence():
    issuer_token = object()
    issued: dict[object, tuple[object, ...]] = {}
    consumed: set[object] = set()

    class _RemoteVerificationEvidence:
        """Main-process capability admitted from one task-bound worker receipt."""

        __slots__ = ("_nonce", "_sealed")

        def __init__(self, projection: tuple[object, ...], *, _token=None) -> None:
            if _token is not issuer_token:
                raise TypeError("RemoteVerificationEvidence is admission-issued")
            nonce = object()
            issued[nonce] = (*projection, os.getpid())
            object.__setattr__(self, "_nonce", nonce)
            object.__setattr__(self, "_sealed", True)

        def __setattr__(self, name, value) -> None:
            if getattr(self, "_sealed", False):
                raise AttributeError("RemoteVerificationEvidence is immutable")
            object.__setattr__(self, name, value)

        def _assert_matches(
                self, *, sink_kind: str, lock_identity_sha256: str,
                variant: str, operation_identity: str, workload_tag: str,
        ) -> None:
            try:
                authority = issued.get(self._nonce)
            except (AttributeError, TypeError):
                authority = None
            if authority is None or type(self) is not _RemoteVerificationEvidence:
                raise CommitReceiptError("remote verification evidence has no authority")
            (
                _task_sha256, verdict, certified, _result_sha256,
                bound_sink, bound_lock, bound_variant, bound_operation,
                bound_tag, issuer_pid,
            ) = authority
            if (issuer_pid != os.getpid()
                    or verdict != "serializable" or certified is not True):
                raise CommitReceiptError(
                    "remote verification evidence is not certified in this process"
                )
            if self._nonce in consumed:
                raise CommitReceiptError(
                    "remote verification evidence was already consumed"
                )
            if (bound_sink != sink_kind
                    or bound_lock != lock_identity_sha256
                    or bound_variant != variant
                    or bound_operation != operation_identity
                    or bound_tag != workload_tag):
                raise CommitReceiptError(
                    "remote verification evidence is bound to a different operation"
                )

        def _receipt_evidence(self) -> tuple[str, bool, str]:
            try:
                authority = issued[self._nonce]
            except (AttributeError, KeyError, TypeError) as exc:
                raise CommitReceiptError(
                    "remote verification evidence has no authority"
                ) from exc
            return authority[1], authority[2], authority[3]

        def _remote_task_sha256(self) -> str:
            try:
                return str(issued[self._nonce][0])
            except (AttributeError, KeyError, TypeError) as exc:
                raise CommitReceiptError(
                    "remote verification evidence has no authority"
                ) from exc

        def _consume(self) -> None:
            try:
                valid = self._nonce in issued and self._nonce not in consumed
            except (AttributeError, TypeError):
                valid = False
            if not valid:
                raise CommitReceiptError(
                    "remote verification evidence was already consumed"
                )
            consumed.add(self._nonce)

    def issue(projection: tuple[object, ...]):
        return _RemoteVerificationEvidence(projection, _token=issuer_token)

    return _RemoteVerificationEvidence, issue


(
    RemoteVerificationEvidence,
    _issue_remote_verification_evidence,
) = _bind_remote_verification_evidence()
del _bind_remote_verification_evidence


def _validate_hex(value: object, label: str) -> str:
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        raise CommitReceiptError(f"{label} must be lowercase sha256")
    return value


def serialize_remote_verification_receipt(
        capability: object, *, task_sha256: str,
        verify_payload_sha256: str,
) -> dict[str, Any]:
    """Consume one live worker capability into a task-bound wire receipt."""
    from .core import VerificationCapability

    _validate_hex(task_sha256, "task sha256")
    _validate_hex(verify_payload_sha256, "verify payload sha256")
    if type(capability) is not VerificationCapability:
        raise CommitReceiptError("exact VerificationCapability is required")
    if capability._sink_kind != CAMPAIGN_WAL_SINK:
        raise CommitReceiptError(
            "remote verification receipts are campaign-wal only"
        )
    capability._assert_matches(
        sink_kind=capability._sink_kind,
        lock_identity_sha256=capability._lock_identity_sha256,
        variant=capability._variant,
        operation_identity=capability._operation_identity,
        workload_tag=capability._workload_tag,
    )
    verdict, certified, result_sha256 = capability._receipt_evidence()
    core = {
        "schema": REMOTE_VERIFICATION_RECEIPT_SCHEMA,
        "task_sha256": task_sha256,
        "verdict": verdict,
        "certified": certified,
        "verifier_result_sha256": result_sha256,
        "verify_payload_sha256": verify_payload_sha256,
        "sink_kind": capability._sink_kind,
        "lock_identity_sha256": capability._lock_identity_sha256,
        "variant": capability._variant,
        "operation_identity": capability._operation_identity,
        "workload_tag": capability._workload_tag,
    }
    receipt = {
        **core,
        "receipt_sha256": _domain_digest(
            b"izanagi-remote-verification-receipt-v1", core,
        ),
    }
    capability._consume()
    return json.loads(_canonical_bytes(receipt))


def admit_remote_verification_receipt(
        payload: object, *, expected_task_sha256: str,
        lock_identity_sha256: str, variant: str,
        operation_identity: str, workload_tag: str,
        authenticated_result: object = None,
        result_secret: object = None,
) -> RemoteVerificationEvidence:
    """Admit an exact worker receipt into one main-PID, one-shot capability."""
    required = {
        "schema", "task_sha256", "verdict", "certified",
        "verifier_result_sha256", "verify_payload_sha256", "sink_kind",
        "lock_identity_sha256", "variant", "operation_identity",
        "workload_tag", "receipt_sha256",
    }
    if type(payload) is not dict or set(payload) != required:
        raise CommitReceiptError("remote verification receipt key set mismatch")
    if type(result_secret) is not bytes or len(result_secret) != 32:
        raise CommitReceiptError(
            "remote verification receipt requires a one-task transport secret"
        )
    result_keys = {
        "schema", "task_sha256", "build_attempt_id", "tag", "rep",
        "trace_bin_sha256", "outcome", "result_mac",
    }
    if type(authenticated_result) is not dict or set(authenticated_result) != result_keys:
        raise CommitReceiptError("authenticated remote result is absent or malformed")
    unsigned_result = dict(authenticated_result)
    result_mac = unsigned_result.pop("result_mac")
    if type(result_mac) is not str or _HEX64.fullmatch(result_mac) is None:
        raise CommitReceiptError("authenticated remote result MAC is malformed")
    expected_result_mac = hmac.new(
        result_secret, _canonical_bytes(unsigned_result), hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(result_mac, expected_result_mac):
        raise CommitReceiptError("authenticated remote result MAC mismatch")
    outcome = authenticated_result["outcome"]
    if (authenticated_result["task_sha256"] != expected_task_sha256
            or type(outcome) is not dict
            or outcome.get("kind") != "success"
            or outcome.get("remote_verification_receipt") != payload
            or type(outcome.get("verify_payload")) is not dict):
        raise CommitReceiptError("authenticated remote result binding mismatch")
    actual_verify_payload_sha256 = hashlib.sha256(
        _canonical_bytes(outcome["verify_payload"])
    ).hexdigest()
    _validate_hex(expected_task_sha256, "expected task sha256")
    _validate_hex(payload["task_sha256"], "remote task sha256")
    _validate_hex(payload["verifier_result_sha256"], "verifier result digest")
    _validate_hex(payload["verify_payload_sha256"], "verify payload digest")
    _validate_hex(payload["lock_identity_sha256"], "lock identity")
    core = dict(payload)
    receipt_sha256 = core.pop("receipt_sha256")
    expected_receipt_sha256 = _domain_digest(
        b"izanagi-remote-verification-receipt-v1", core,
    )
    if (payload["schema"] != REMOTE_VERIFICATION_RECEIPT_SCHEMA
            or payload["task_sha256"] != expected_task_sha256
            or payload["verdict"] != "serializable"
            or payload["certified"] is not True
            or payload["verify_payload_sha256"]
            != actual_verify_payload_sha256
            or payload["sink_kind"] != CAMPAIGN_WAL_SINK
            or payload["lock_identity_sha256"] != lock_identity_sha256
            or payload["variant"] != variant
            or payload["operation_identity"] != operation_identity
            or payload["workload_tag"] != workload_tag
            or receipt_sha256 != expected_receipt_sha256):
        raise CommitReceiptError("remote verification receipt binding mismatch")
    global _REMOTE_ADMISSION_PID
    with _REMOTE_ADMISSION_LOCK:
        if _REMOTE_ADMISSION_PID != os.getpid():
            _REMOTE_ADMISSION_PID = os.getpid()
            _ADMITTED_REMOTE_RECEIPTS.clear()
        admission_identity = (
            payload["task_sha256"], payload["receipt_sha256"],
        )
        if admission_identity in _ADMITTED_REMOTE_RECEIPTS:
            raise CommitReceiptError(
                "remote verification receipt was already admitted"
            )
        _ADMITTED_REMOTE_RECEIPTS.add(admission_identity)
    return _issue_remote_verification_evidence((
        payload["task_sha256"], payload["verdict"], payload["certified"],
        payload["verifier_result_sha256"], payload["sink_kind"],
        payload["lock_identity_sha256"], payload["variant"],
        payload["operation_identity"], payload["workload_tag"],
    ))


def _receipt_core(record: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "sink_kind", "lock_identity_sha256", "variant",
        "operation_identity", "verifier_evidence", "terminal_payload_sha256",
        "replay_provenance", "issuer_pid", "issuer_process_seal_sha256",
        "receipt_id",
    }
    if type(record) is not dict or set(record) != required:
        raise CommitReceiptError("commit receipt key set mismatch")
    core = dict(record)
    core.pop("receipt_id")
    return core


def validate_serialized_receipt(
        record: Mapping[str, Any], *, sink_kind: str,
        lock_identity_sha256: str, variant: str,
        terminal_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the durable projection; this does not authorize a new append."""
    core = _receipt_core(record)
    if (core["schema"] != RECEIPT_SCHEMA
            or core["sink_kind"] != sink_kind
            or sink_kind not in _SINK_KINDS
            or core["lock_identity_sha256"] != lock_identity_sha256
            or core["variant"] != variant
            or type(core["operation_identity"]) is not str
            or not core["operation_identity"]
            or core["terminal_payload_sha256"]
            != terminal_payload_sha256(terminal_payload)
            or type(core["issuer_pid"]) is not int
            or core["issuer_pid"] <= 0):
        raise CommitReceiptError("commit receipt binding mismatch")
    _validate_hex(core["lock_identity_sha256"], "lock identity")
    _validate_hex(
        core["issuer_process_seal_sha256"], "issuer process seal digest")
    evidence = core["verifier_evidence"]
    if type(evidence) is not list or not evidence:
        raise CommitReceiptError("commit receipt verifier evidence is empty")
    for row in evidence:
        if (type(row) is not dict
                or set(row) != {
                    "workload_tag", "verdict", "certified",
                    "verifier_result_sha256",
                }
                or type(row["workload_tag"]) is not str
                or not row["workload_tag"]
                or row["verdict"] != "serializable"
                or row["certified"] is not True):
            raise CommitReceiptError("commit receipt has uncertified verifier evidence")
        _validate_hex(row["verifier_result_sha256"], "verifier result digest")
    replay = core["replay_provenance"]
    if replay is not None:
        if (type(replay) is not dict
                or set(replay) != {
                    "source_campaign_lock_sha256", "source_wal_sha256",
                    "source_commit_receipt_id", "source_variant",
                }
                or type(replay["source_variant"]) is not str
                or not replay["source_variant"]):
            raise CommitReceiptError("commit receipt replay provenance mismatch")
        for key in (
                "source_campaign_lock_sha256", "source_wal_sha256",
                "source_commit_receipt_id"):
            _validate_hex(replay[key], key)
    expected_id = _domain_digest(b"izanagi-commit-receipt-v1", core)
    if record["receipt_id"] != expected_id:
        raise CommitReceiptError("commit receipt id mismatch")
    return json.loads(_canonical_bytes(dict(record)))


def _new_commit_receipt(
        evidence: list[dict[str, Any]], *, sink_kind: str,
        lock_identity_sha256: str, variant: str, operation_identity: str,
        terminal_payload: Mapping[str, Any], replay_provenance: object,
) -> CommitReceipt:
    if sink_kind not in _SINK_KINDS:
        raise CommitReceiptError("unknown receipt sink kind")
    _validate_hex(lock_identity_sha256, "lock identity")
    if type(variant) is not str or not variant:
        raise CommitReceiptError("receipt variant must be non-empty str")
    if type(operation_identity) is not str or not operation_identity:
        raise CommitReceiptError("receipt operation identity must be non-empty str")
    core = {
        "schema": RECEIPT_SCHEMA,
        "sink_kind": sink_kind,
        "lock_identity_sha256": lock_identity_sha256,
        "variant": variant,
        "operation_identity": operation_identity,
        "verifier_evidence": evidence,
        "terminal_payload_sha256": terminal_payload_sha256(terminal_payload),
        "replay_provenance": replay_provenance,
        "issuer_pid": os.getpid(),
        "issuer_process_seal_sha256": _PROCESS_SEAL_SHA256,
    }
    record = {
        **core,
        "receipt_id": _domain_digest(b"izanagi-commit-receipt-v1", core),
    }
    validate_serialized_receipt(
        record,
        sink_kind=sink_kind,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        terminal_payload=terminal_payload,
    )
    return CommitReceipt(record, _RECEIPT_TOKEN)


def issue_commit_receipt(
        capabilities: Sequence[object], *,
        workload_tags: Sequence[str], sink_kind: str,
        lock_identity_sha256: str, variant: str, operation_identity: str,
        terminal_payload: Mapping[str, Any]) -> CommitReceipt:
    """Bind verifier-issued capabilities to one prospective terminal payload."""
    if (type(capabilities) not in {tuple, list}
            or type(workload_tags) not in {tuple, list}
            or len(capabilities) != len(workload_tags)
            or not capabilities):
        raise CommitReceiptError("exact non-empty verifier capability/tag sequence required")
    from .core import VerificationCapability

    if len({id(capability) for capability in capabilities}) != len(capabilities):
        raise CommitReceiptError("verification capability sequence contains duplicates")
    evidence = []
    remote_task_sha256s: set[str] = set()
    for capability, tag in zip(capabilities, workload_tags):
        if type(capability) not in {
                VerificationCapability, RemoteVerificationEvidence}:
            raise CommitReceiptError("serialized verifier evidence is not a capability")
        if type(tag) is not str or not tag:
            raise CommitReceiptError("workload tag must be non-empty str")
        if type(capability) is RemoteVerificationEvidence:
            remote_task_sha256 = capability._remote_task_sha256()
            if remote_task_sha256 in remote_task_sha256s:
                raise CommitReceiptError(
                    "verification capability sequence contains duplicate remote tasks"
                )
            remote_task_sha256s.add(remote_task_sha256)
        capability._assert_matches(
            sink_kind=sink_kind,
            lock_identity_sha256=lock_identity_sha256,
            variant=variant,
            operation_identity=operation_identity,
            workload_tag=tag,
        )
        verdict, certified, result_sha256 = capability._receipt_evidence()
        evidence.append({
            "workload_tag": tag,
            "verdict": verdict,
            "certified": certified,
            "verifier_result_sha256": result_sha256,
        })
    for capability in capabilities:
        capability._consume()
    return _new_commit_receipt(
        evidence,
        sink_kind=sink_kind,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        operation_identity=operation_identity,
        terminal_payload=terminal_payload,
        replay_provenance=None,
    )


def validate_live_receipt(
        receipt: object, *, sink_kind: str, lock_identity_sha256: str,
        variant: str, terminal_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Require the opaque live object, then return its durable projection."""
    record = _live_receipt_record(receipt)
    return validate_serialized_receipt(
        record,
        sink_kind=sink_kind,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        terminal_payload=terminal_payload,
    )


def _live_receipt_record(receipt: object) -> dict[str, Any]:
    """Return an immutable capability's projection after process-seal checks."""
    if (type(receipt) is not CommitReceipt
            or receipt._token is not _RECEIPT_TOKEN
            or receipt._pid != os.getpid()
            or receipt._process_seal is not _PROCESS_SEAL):
        raise CommitReceiptError("exact live CommitReceipt capability required")
    return _thaw_json(receipt._record)


def validate_live_campaign_wal_receipt(
        receipt: object, *, lock_identity_sha256: str | None, variant: str,
        terminal_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate against the sink-observed lock or explicit absence binding."""
    record = _live_receipt_record(receipt)
    actual_lock_identity = (
        CAMPAIGN_LOCK_ABSENT_SHA256
        if lock_identity_sha256 is None
        else lock_identity_sha256
    )
    return validate_serialized_receipt(
        record,
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=actual_lock_identity,
        variant=variant,
        terminal_payload=terminal_payload,
    )


def _bind_admit_replay_evidence(evidence_issuer):
    def admit_replay_evidence(
            certified_view: object, source_record: object,
    ) -> ReplayVerificationEvidence:
        """Admit the exact COMMIT record capability held by a certified view."""
        from ..campaign.artifact_admission import (
            CertifiedCampaignView,
            ImmutableWalRecord,
            _assert_replay_admission_source,
        )

        if type(certified_view) is not CertifiedCampaignView:
            raise CommitReceiptError(
                "exact CertifiedCampaignView capability required"
            )
        if type(source_record) is not ImmutableWalRecord:
            raise CommitReceiptError(
                "exact COMMIT source record from the certified view is required"
            )
        try:
            _assert_replay_admission_source(
                certified_view,
                source_record,
            )
        except (AttributeError, TypeError) as exc:
            raise CommitReceiptError(
                "certified view lacks replay admission authority"
            ) from exc
        source_campaign_lock_sha256 = (
            certified_view.decision.campaign_lock_sha256
        )
        source_wal_sha256 = certified_view.decision.wal_sha256
        source_variant = source_record.variant
        source_terminal_payload = _thaw_json(source_record.payload)
        serialized_receipt = source_terminal_payload.pop(
            RECEIPT_PAYLOAD_KEY, None,
        )
        _validate_hex(source_campaign_lock_sha256, "source lock identity")
        _validate_hex(source_wal_sha256, "source WAL digest")
        record = validate_serialized_receipt(
            serialized_receipt,
            sink_kind=CAMPAIGN_WAL_SINK,
            lock_identity_sha256=source_campaign_lock_sha256,
            variant=source_variant,
            terminal_payload=source_terminal_payload,
        )
        return evidence_issuer(
            receipt=record,
            source_campaign_lock_sha256=source_campaign_lock_sha256,
            source_wal_sha256=source_wal_sha256,
            source_variant=source_variant,
        )

    return admit_replay_evidence


admit_replay_evidence = _bind_admit_replay_evidence(
    _issue_replay_verification_evidence,
)
del _bind_admit_replay_evidence
del _issue_replay_verification_evidence


def issue_replay_commit_receipt(
        evidence: ReplayVerificationEvidence, *, lock_identity_sha256: str,
        variant: str, terminal_payload: Mapping[str, Any]) -> CommitReceipt:
    """Rebind admitted immutable source evidence to a destination campaign lock."""
    if type(evidence) is not ReplayVerificationEvidence:
        raise CommitReceiptError("exact replay verification evidence required")
    (
        frozen_source,
        source_campaign_lock_sha256,
        source_wal_sha256,
        source_variant,
        _issuer_pid,
    ) = evidence._projection()
    source = _thaw_json(frozen_source)
    source_rows = source["verifier_evidence"]
    provenance = {
        "source_campaign_lock_sha256": source_campaign_lock_sha256,
        "source_wal_sha256": source_wal_sha256,
        "source_commit_receipt_id": source["receipt_id"],
        "source_variant": source_variant,
    }
    return _new_commit_receipt(
        [dict(row) for row in source_rows],
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        operation_identity=f"guided-replay:{source['receipt_id']}",
        terminal_payload=terminal_payload,
        replay_provenance=provenance,
    )
