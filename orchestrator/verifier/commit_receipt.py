# -*- coding: utf-8 -*-
"""Verifier-issued, process-bound capabilities for terminal COMMIT records."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from types import MappingProxyType
from typing import Any, Mapping, Sequence


RECEIPT_PAYLOAD_KEY = "commit_verification_receipt"
RECEIPT_SCHEMA = "campaign-commit-verification-receipt/v1"
CAMPAIGN_WAL_SINK = "campaign-wal"
QUALIFICATION_SINK = "qualification-evaluation"
_SINK_KINDS = frozenset({CAMPAIGN_WAL_SINK, QUALIFICATION_SINK})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_TOKEN = object()
_PROCESS_SEAL = secrets.token_bytes(32)
_PROCESS_SEAL_SHA256 = hashlib.sha256(_PROCESS_SEAL).hexdigest()


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
    return hashlib.sha256(raw).hexdigest()


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


def _validate_hex(value: object, label: str) -> str:
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        raise CommitReceiptError(f"{label} must be lowercase sha256")
    return value


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
    for capability, tag in zip(capabilities, workload_tags):
        if type(capability) is not VerificationCapability:
            raise CommitReceiptError("serialized verifier evidence is not a capability")
        if type(tag) is not str or not tag:
            raise CommitReceiptError("workload tag must be non-empty str")
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
    """Validate against the sink-observed raw lock, or issuer binding if lockless."""
    record = _live_receipt_record(receipt)
    core = _receipt_core(record)
    actual_lock_identity = (
        core["lock_identity_sha256"]
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
