"""Fail-closed formal consumption of reflux result evidence.

This module cannot produce a non-aborted origin terminal.  The P6 contract
``derive_p6_cut`` does not exist anywhere in the codebase: D138 declined an
implementation because there were no firing artifacts, and D156 assigns the
mechanical boundary tests and cap-lift receipt design to a future P6
implementation wave.  That wave has not happened, so condition 8 is
unjudgeable and failing closed is the only honest implementation.

The prohibition on an all-tombstone batch is deliberately inside the formal
consumer / typed-client boundary only.  It does not change the ledger rule
fixed by D198, under which a batch with zero execution candidates is outside
the ledger's lower-bound gate.

This wiring also assumes that callers do not invoke the ledger's private
seams directly.  Python code in the same process can otherwise bypass this
consumer; closing that route would require a ledger acceptance change outside
this unit's scope.

The physical-layout checks below establish artifact consistency only beneath
the canonical leaves of the base selected by the caller through
``campaign_output_root``.  They neither identify a unique deployment root,
prove physical execution, nor authenticate a trusted harness.  D1674 assumes
operationally that only the trusted harness can write the evidence root;
coherent locks and WAL evidence placed under those leaves after execution
cannot be rejected here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import threading
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence, TypeAlias

from . import campaign_lock
from . import ident
from . import reflux_origin_ledger as ledger
from . import reflux_result_evidence as result_evidence
from . import trigger_gate_binding
from .layout import exploration_campaign_layout
from .model import CampaignConfig, STAGE_ABORT, STAGE_COMMIT
from .reflux_origin_artifacts import (
    ArtifactError,
    canonical_json_bytes,
    strict_json_loads,
)
from .reflux_origin_binding import (
    OriginBindingCapability,
    OriginBindingError,
    assert_issued_origin_binding_capability,
    origin_binding_capability_record,
)
from .reflux_origin_topology import (
    RecoveryEnvelope,
    SOURCE_AND_VALIDATION_MEMBER_COUNT,
    VALIDATION_MASK_COUNT,
    canonical_recovery_envelope_bytes,
)
from .reflux_ir import TriggerGateIR, encode_wire
from .reflux_result_evidence import (
    ResolvedResultEvidence,
    ResultEvidenceError,
    assert_non_overlapping_wal_ranges,
    parse_result_evidence_bytes,
    resolve_result_evidence,
)
from .reflux_source_closure import (
    SourceClosureError,
    ValidatedSourceClosure,
    assert_issued_validated_source_closure,
)
from .wal import TRIGGER_BINDING_COMMITMENT_KEY, TRIGGER_BINDING_PAYLOAD_KEY


__all__ = [
    "FORMAL_CONSUMER_RECEIPT_SCHEMA_VERSION",
    "ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION",
    "AbortedOriginDecision",
    "FormalContractRejected",
    "FormalConsumerReceipt",
    "FormalConsumerResult",
    "FormalReasonCode",
    "FormalReceiptError",
    "FormalReceiptReason",
    "OriginTerminalProjection",
    "P6Unavailable",
    "aborted_origin_payload_sha256",
    "canonical_aborted_origin_payload_bytes",
    "canonical_formal_consumer_receipt_bytes",
    "consume_formal_consumer_receipt",
    "evaluate_formal_origin",
    "formal_consumer_receipt_record",
    "formal_consumer_receipt_sha256",
    "origin_terminal_projection_record",
]


FORMAL_CONSUMER_RECEIPT_SCHEMA_VERSION = "formal-consumer-receipt/v1"
ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION = "OriginTerminalProjection/v1"
_RECEIPT_ISSUER = "izanagi-formal-consumer/v1"
_PROJECTION_KEY = "origin_terminal_projection"
_RECOVERY_ENVELOPE_RELATIVE_PATH = Path("origin/recovery-envelope.json")
_ORIGIN_CAMPAIGN_RUN_KEYS = frozenset({
    "attempt_capability_sha256",
    "query_ordinal",
})
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_CANDIDATE_ATTRIBUTABLE_ABORT_REASON = "non-serializable"
_ANOMALY_KEYS = result_evidence._ANOMALY_KEYS
_EDGE_KEYS = result_evidence._EDGE_KEYS
_REASON_REQUIRED_KEYS = result_evidence._REASON_REQUIRED_KEYS
_REASON_OPTIONAL_KEYS = result_evidence._REASON_OPTIONAL_KEYS
_REASON_TYPES = result_evidence._REASON_TYPES
_REASON_VERSION_KEYS = result_evidence._REASON_VERSION_KEYS
_PHENOMENA = result_evidence._PHENOMENA
_VERIFY_KEYS = result_evidence._VERIFY_KEYS
_VERIFY_STATS_KEYS = result_evidence._VERIFY_STATS_KEYS
_VERIFY_INTEGRITY_KEYS = result_evidence._VERIFY_INTEGRITY_KEYS
_PERMUTATION_VIOLATION_DETAILS_KEYS = (
    result_evidence._PERMUTATION_VIOLATION_DETAILS_KEYS
)
_PERMUTATION_VIOLATION_COUNT_KEYS = (
    result_evidence._PERMUTATION_VIOLATION_COUNT_KEYS
)
_CLEAN_WIRE_COUNTER_KEYS = result_evidence._CLEAN_WIRE_COUNTER_KEYS


class FormalReasonCode(Enum):
    """Closed terminal reason set; values are the stable wire codes."""

    FC01 = "FC01"
    FC02 = "FC02"
    FC03 = "FC03"
    FC04 = "FC04"
    FC05A = "FC05a"
    FC05B = "FC05b"
    FC05C = "FC05c"
    FC06 = "FC06"
    FC07 = "FC07"
    FC09 = "FC09"
    FC10 = "FC10"
    P6_UNAVAILABLE = "P6Unavailable"


class FormalReceiptReason(Enum):
    ISSUER = "issuer-mismatch"
    OPERATION = "operation-mismatch"
    STATE = "state-commitment-mismatch"
    PAYLOAD = "terminal-payload-mismatch"
    REPLAY = "operation-replay-payload-mismatch"


class FormalReceiptError(ValueError):
    def __init__(self, reason_code: FormalReceiptReason, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class AbortedOriginDecision:
    """Counters for the only terminal payload this consumer can authorize."""

    batch_count: int
    tombstone_count: int
    sealed_queries: int
    tombstoned_queries: int
    forfeited_iterations: int
    forfeited_queries: int
    terminal_payload_sha256: str


@dataclass(frozen=True, slots=True)
class OriginTerminalProjection:
    schema_version: str
    reason_code: FormalReasonCode
    formal_receipt_sha256: str | None
    evidence_root_sha256: str | None
    authority_blob_sha256: str
    origin_id: str
    cell_key: str
    terminal_payload_sha256: str
    arm_binding_digest_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION:
            raise ValueError("unsupported origin terminal projection")
        if type(self.reason_code) is not FormalReasonCode:
            raise TypeError("projection reason_code must be FormalReasonCode")
        required = self.reason_code is FormalReasonCode.P6_UNAVAILABLE
        if required != (self.formal_receipt_sha256 is not None):
            raise ValueError("formal receipt nullability differs from result kind")
        if required != (self.evidence_root_sha256 is not None):
            raise ValueError("evidence root nullability differs from result kind")
        for value in (
            self.authority_blob_sha256,
            self.terminal_payload_sha256,
            self.arm_binding_digest_sha256,
            *(() if self.formal_receipt_sha256 is None else (self.formal_receipt_sha256,)),
            *(() if self.evidence_root_sha256 is None else (self.evidence_root_sha256,)),
        ):
            _sha256(value, label="projection digest")
        _token(self.origin_id, label="projection origin_id")
        _token(self.cell_key, label="projection cell_key")


@dataclass(frozen=True, slots=True)
class FormalContractRejected:
    reason_code: FormalReasonCode
    decision: AbortedOriginDecision
    projection: OriginTerminalProjection

    def __post_init__(self) -> None:
        if self.reason_code is FormalReasonCode.P6_UNAVAILABLE:
            raise ValueError("rejected result cannot use the unavailable code")


@dataclass(frozen=True, slots=True, init=False)
class FormalConsumerReceipt:
    """Issuer-bound, canonical receipt without a self-digest field."""

    operation_id: str
    authority_blob_sha256: str
    source_closure_sha256: str
    run_plan_sha256: str
    origin_id: str
    input_state_commitment: str
    origin_sealed_payload_sha256: str
    evidence_sha256s: tuple[str, ...]
    evidence_root_sha256: str
    enforcement_arm: str
    arm_binding_digest_sha256: str
    generator_closure: Mapping[str, object]
    reason_code: FormalReasonCode
    issuer_seal: str
    _seal: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        operation_id: str,
        authority_blob_sha256: str,
        source_closure_sha256: str,
        run_plan_sha256: str,
        origin_id: str,
        input_state_commitment: str,
        origin_sealed_payload_sha256: str,
        evidence_sha256s: tuple[str, ...],
        evidence_root_sha256: str,
        enforcement_arm: str,
        arm_binding_digest_sha256: str,
        generator_closure: Mapping[str, object],
        reason_code: FormalReasonCode,
        _issuer: object,
    ) -> None:
        if _issuer is not _RECEIPT_CONSTRUCTOR:
            raise TypeError("FormalConsumerReceipt values are issuer-only")
        seal = object()
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(self, "authority_blob_sha256", authority_blob_sha256)
        object.__setattr__(self, "source_closure_sha256", source_closure_sha256)
        object.__setattr__(self, "run_plan_sha256", run_plan_sha256)
        object.__setattr__(self, "origin_id", origin_id)
        object.__setattr__(self, "input_state_commitment", input_state_commitment)
        object.__setattr__(
            self, "origin_sealed_payload_sha256", origin_sealed_payload_sha256
        )
        object.__setattr__(self, "evidence_sha256s", evidence_sha256s)
        object.__setattr__(self, "evidence_root_sha256", evidence_root_sha256)
        object.__setattr__(self, "enforcement_arm", enforcement_arm)
        object.__setattr__(
            self, "arm_binding_digest_sha256", arm_binding_digest_sha256
        )
        object.__setattr__(
            self, "generator_closure", MappingProxyType(dict(generator_closure))
        )
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "issuer_seal", _RECEIPT_ISSUER)
        object.__setattr__(self, "_seal", seal)


@dataclass(frozen=True, slots=True)
class P6Unavailable:
    reason_code: FormalReasonCode
    receipt: FormalConsumerReceipt
    decision: AbortedOriginDecision
    projection: OriginTerminalProjection

    def __post_init__(self) -> None:
        if self.reason_code is not FormalReasonCode.P6_UNAVAILABLE:
            raise ValueError("P6Unavailable has the wrong reason code")


FormalConsumerResult: TypeAlias = FormalContractRejected | P6Unavailable


@dataclass(frozen=True, slots=True)
class _ContractFailure(Exception):
    reason_code: FormalReasonCode


@dataclass(frozen=True, slots=True)
class _MemberRecord:
    batch: ledger.SealedBatch
    member: ledger.SealedBatchMember
    record: dict
    raw_bytes: bytes
    raw_sha256: str


@dataclass(frozen=True, slots=True)
class _ReplayEntry:
    request_bytes: bytes
    decision: AbortedOriginDecision


_RECEIPT_CONSTRUCTOR = object()
_ISSUED_RECEIPTS: dict[object, bytes] = {}
_OPERATION_REPLAY_CACHE: dict[str, _ReplayEntry] = {}
_REPLAY_LOCK = threading.Lock()


def _sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _token(value: object, *, label: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise ValueError(f"{label} must be a non-empty token")
    return value


def _require(reason_code: FormalReasonCode, condition: bool) -> None:
    if type(condition) is not bool or not condition:
        raise _ContractFailure(reason_code)


def _read_regular_file_no_follow(
    path: Path, *, reason_code: FormalReasonCode
) -> bytes:
    """Read one fixed-path artifact without following a symlink component."""

    target = Path(os.path.abspath(os.fspath(path)))
    current = Path(target.anchor)
    try:
        for component in target.parts[1:]:
            current /= component
            info = os.lstat(current)
            _require(reason_code, not stat.S_ISLNK(info.st_mode))
    except OSError as exc:
        raise _ContractFailure(reason_code) from exc

    nofollow = getattr(os, "O_NOFOLLOW", None)
    _require(reason_code, nofollow is not None)
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise _ContractFailure(reason_code) from exc
    try:
        info = os.fstat(fd)
        _require(reason_code, stat.S_ISREG(info.st_mode))
        identity = (info.st_dev, info.st_ino)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError as exc:
        raise _ContractFailure(reason_code) from exc
    finally:
        os.close(fd)

    try:
        final_info = os.lstat(target)
    except OSError as exc:
        raise _ContractFailure(reason_code) from exc
    _require(reason_code, not stat.S_ISLNK(final_info.st_mode))
    _require(reason_code, (final_info.st_dev, final_info.st_ino) == identity)
    return b"".join(chunks)


def _validate_bound_recovery_envelope(
    *,
    evidence_root: Path,
    run_plan: RecoveryEnvelope,
    origin_run_plan_sha256: str,
) -> None:
    """Re-read the one fixed envelope and match its lifecycle-bound digest."""

    try:
        bound_digest = _sha256(
            origin_run_plan_sha256, label="origin_run_plan_sha256"
        )
    except ValueError as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc
    path = Path(evidence_root) / _RECOVERY_ENVELOPE_RELATIVE_PATH
    raw = _read_regular_file_no_follow(path, reason_code=FormalReasonCode.FC03)
    _require(
        FormalReasonCode.FC03,
        hashlib.sha256(raw).hexdigest() == bound_digest,
    )
    _require(
        FormalReasonCode.FC03,
        raw == canonical_recovery_envelope_bytes(run_plan),
    )


def _campaign_config_from_lock(
    decoded: campaign_lock.DecodedCampaignLock,
    *,
    expected_campaign_run_identity: str,
) -> CampaignConfig:
    """Reconstruct a config whose identity must equal the planned run ID."""

    identity = decoded.identity
    search_tag = identity["search_tag"]
    config = CampaignConfig(
        spec_slug="",
        search_tag=search_tag,
        spec_content=identity["spec_content"],
        ccbench_commit=identity["ccbench_commit"],
        search_config=dict(identity["search_config"]),
        trial=identity["trial"],
    )
    try:
        reconstructed_preimage = ident.canonical_preimage(config)
    except (TypeError, ValueError) as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc
    # The v2 decoder already enforces this equality.  The v1 decoder preserves
    # its original text, so the comparison is meaningful only for v1.
    if decoded.schema_version == "campaign-lock/v1":
        _require(
            FormalReasonCode.FC03,
            reconstructed_preimage == decoded.identity_preimage,
        )
    cfg_hash8 = hashlib.sha256(
        reconstructed_preimage.encode("utf-8")
    ).hexdigest()[:8]
    suffix = f"-{search_tag}-{cfg_hash8}"
    slug = (
        expected_campaign_run_identity[: -len(suffix)]
        if expected_campaign_run_identity.endswith(suffix)
        else ""
    )
    _require(FormalReasonCode.FC03, bool(slug))
    config = replace(config, spec_slug=slug)
    try:
        reconstructed_identity = str(ident.campaign_id(config))
    except (TypeError, ValueError) as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc
    _require(
        FormalReasonCode.FC03,
        reconstructed_identity == expected_campaign_run_identity,
    )
    return config


def _decision(snapshot: ledger.OriginSnapshot) -> AbortedOriginDecision:
    counters = {
        "batch_count": snapshot.batch_count,
        "tombstone_count": snapshot.tombstone_count,
        "sealed_queries": snapshot.sealed_queries,
        "tombstoned_queries": snapshot.tombstoned_queries,
        "forfeited_iterations": snapshot.forfeited_iterations,
        "forfeited_queries": snapshot.forfeited_queries,
    }
    provisional = AbortedOriginDecision(**counters, terminal_payload_sha256="0" * 64)
    return AbortedOriginDecision(
        **counters,
        terminal_payload_sha256=aborted_origin_payload_sha256(provisional),
    )


def _aborted_origin_payload(decision: AbortedOriginDecision) -> dict[str, object]:
    if type(decision) is not AbortedOriginDecision:
        raise TypeError("decision must be AbortedOriginDecision")
    counters = (
        decision.batch_count,
        decision.tombstone_count,
        decision.sealed_queries,
        decision.tombstoned_queries,
        decision.forfeited_iterations,
        decision.forfeited_queries,
    )
    if any(type(value) is not int or value < 0 for value in counters):
        raise ValueError("terminal counters must be non-negative integers")
    return {
        "seal_kind": "aborted",
        "constraint_class_sha256s": [],
        "batch_count": decision.batch_count,
        "tombstone_count": decision.tombstone_count,
        "sealed_queries": decision.sealed_queries,
        "tombstoned_queries": decision.tombstoned_queries,
        "forfeited_iterations": decision.forfeited_iterations,
        "forfeited_queries": decision.forfeited_queries,
    }


def canonical_aborted_origin_payload_bytes(decision: AbortedOriginDecision) -> bytes:
    """Return the ledger's exact aborted ``origin-sealed`` payload bytes."""

    return canonical_json_bytes(_aborted_origin_payload(decision))


def aborted_origin_payload_sha256(decision: AbortedOriginDecision) -> str:
    return hashlib.sha256(canonical_aborted_origin_payload_bytes(decision)).hexdigest()


def origin_terminal_projection_record(
    projection: OriginTerminalProjection,
) -> dict[str, object]:
    if type(projection) is not OriginTerminalProjection:
        raise TypeError("expected exact OriginTerminalProjection")
    return {
        _PROJECTION_KEY: {
            "schema_version": projection.schema_version,
            "reason_code": projection.reason_code.value,
            "formal_receipt_sha256": projection.formal_receipt_sha256,
            "evidence_root_sha256": projection.evidence_root_sha256,
            "authority_blob_sha256": projection.authority_blob_sha256,
            "origin_id": projection.origin_id,
            "cell_key": projection.cell_key,
            "terminal_payload_sha256": projection.terminal_payload_sha256,
            "arm_binding_digest_sha256": projection.arm_binding_digest_sha256,
        }
    }


def formal_consumer_receipt_record(
    receipt: FormalConsumerReceipt,
) -> dict[str, object]:
    if type(receipt) is not FormalConsumerReceipt:
        raise TypeError("expected exact FormalConsumerReceipt")
    return {
        "schema_version": FORMAL_CONSUMER_RECEIPT_SCHEMA_VERSION,
        "operation_id": receipt.operation_id,
        "authority_blob_sha256": receipt.authority_blob_sha256,
        "source_closure_sha256": receipt.source_closure_sha256,
        "run_plan_sha256": receipt.run_plan_sha256,
        "origin_id": receipt.origin_id,
        "input_state_commitment": receipt.input_state_commitment,
        "origin_sealed_payload_sha256": receipt.origin_sealed_payload_sha256,
        "evidence_sha256s": list(receipt.evidence_sha256s),
        "evidence_root_sha256": receipt.evidence_root_sha256,
        "enforcement_arm": receipt.enforcement_arm,
        "arm_binding_digest_sha256": receipt.arm_binding_digest_sha256,
        "generator_closure": dict(receipt.generator_closure),
        "reason_code": receipt.reason_code.value,
        "issuer_seal": receipt.issuer_seal,
    }


def canonical_formal_consumer_receipt_bytes(receipt: FormalConsumerReceipt) -> bytes:
    raw = canonical_json_bytes(formal_consumer_receipt_record(receipt))
    expected = _ISSUED_RECEIPTS.get(receipt._seal)
    if expected != raw:
        raise FormalReceiptError(
            FormalReceiptReason.ISSUER, "receipt differs from issuer snapshot"
        )
    return raw


def formal_consumer_receipt_sha256(receipt: FormalConsumerReceipt) -> str:
    return hashlib.sha256(canonical_formal_consumer_receipt_bytes(receipt)).hexdigest()


def _projection(
    *,
    reason_code: FormalReasonCode,
    decision: AbortedOriginDecision,
    capability: OriginBindingCapability,
    receipt: FormalConsumerReceipt | None,
    arm_binding_digest_sha256: str,
) -> OriginTerminalProjection:
    return OriginTerminalProjection(
        schema_version=ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION,
        reason_code=reason_code,
        formal_receipt_sha256=(
            None if receipt is None else formal_consumer_receipt_sha256(receipt)
        ),
        evidence_root_sha256=(
            None if receipt is None else receipt.evidence_root_sha256
        ),
        authority_blob_sha256=capability.authority_blob_sha256,
        origin_id=capability.origin_id,
        cell_key=capability.cell_key,
        terminal_payload_sha256=decision.terminal_payload_sha256,
        arm_binding_digest_sha256=arm_binding_digest_sha256,
    )


def _rejected(
    reason_code: FormalReasonCode,
    *,
    snapshot: ledger.OriginSnapshot,
    capability: OriginBindingCapability,
    arm_binding_digest_sha256: str,
) -> FormalContractRejected:
    decision = _decision(snapshot)
    projection = _projection(
        reason_code=reason_code,
        decision=decision,
        capability=capability,
        receipt=None,
        arm_binding_digest_sha256=arm_binding_digest_sha256,
    )
    return FormalContractRejected(reason_code, decision, projection)


def _member_rows(
    sealed_batches: Sequence[ledger.SealedBatch],
) -> tuple[tuple[ledger.SealedBatch, ledger.SealedBatchMember], ...]:
    batches = tuple(sealed_batches)
    if any(type(batch) is not ledger.SealedBatch for batch in batches):
        raise TypeError("sealed_batches must contain exact SealedBatch values")
    return tuple((batch, member) for batch in batches for member in batch.members)


def _pair_records(
    *,
    sealed_batches: Sequence[ledger.SealedBatch],
    result_record_bytes: Sequence[bytes],
) -> tuple[_MemberRecord, ...]:
    rows = _member_rows(sealed_batches)
    parsed: list[tuple[dict, bytes, str]] = []
    try:
        for raw in result_record_bytes:
            if type(raw) is not bytes:
                raise ResultEvidenceError("result record input is not raw bytes")
            record = parse_result_evidence_bytes(raw)
            parsed.append((record, raw, hashlib.sha256(raw).hexdigest()))
    except ResultEvidenceError as exc:
        raise _ContractFailure(FormalReasonCode.FC01) from exc

    keyed_rows = {
        (batch.batch_id, member.query_ordinal): member for batch, member in rows
    }
    for record, _raw, _digest in parsed:
        key = (
            record["ledger_member"]["batch_id"],
            record["ledger_member"]["query_ordinal"],
        )
        keyed = keyed_rows.get(key)
        if keyed is not None and keyed.outcome == "tombstoned":
            raise _ContractFailure(FormalReasonCode.FC02)

    digest_records: dict[str, list[tuple[dict, bytes]]] = {}
    for record, raw, digest in parsed:
        digest_records.setdefault(digest, []).append((record, raw))

    paired: list[_MemberRecord] = []
    referenced: set[int] = set()
    for batch, member in rows:
        if member.outcome == "tombstoned":
            _require(FormalReasonCode.FC02, member.evidence_digest is None)
            continue
        _require(FormalReasonCode.FC01, member.evidence_digest is not None)
        matches = digest_records.get(member.evidence_digest.sha256, [])
        _require(FormalReasonCode.FC01, len(matches) == 1)
        record, raw = matches[0]
        referenced.add(id(raw))
        paired.append(
            _MemberRecord(
                batch=batch,
                member=member,
                record=record,
                raw_bytes=raw,
                raw_sha256=member.evidence_digest.sha256,
            )
        )
    _require(FormalReasonCode.FC01, len(referenced) == len(parsed))
    return tuple(paired)


def _authority_manifest(
    raw_bytes: bytes, capability: OriginBindingCapability
) -> ledger.AuthorityManifest:
    try:
        authority = ledger._authority_from_bytes(raw_bytes)
    except (TypeError, ValueError, ledger.RefluxOriginLedgerError) as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc
    _require(
        FormalReasonCode.FC03,
        authority.blob_sha256 == capability.authority_blob_sha256,
    )
    entry = authority.entries.get(capability.origin_id)
    _require(FormalReasonCode.FC03, entry is not None)
    _require(FormalReasonCode.FC03, entry.cell_key == capability.cell_key)
    return entry.manifest


def _validate_bindings(
    *,
    capability: OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    manifest: ledger.AuthorityManifest,
    run_plan: RecoveryEnvelope,
    launch_admission_record_sha256: str,
    snapshot: ledger.OriginSnapshot,
    sealed_batches: Sequence[ledger.SealedBatch],
    paired: Sequence[_MemberRecord],
) -> None:
    try:
        assert_issued_origin_binding_capability(capability)
        assert_issued_validated_source_closure(source_closure)
        launch_digest = _sha256(
            launch_admission_record_sha256, label="launch admission digest"
        )
    except (OriginBindingError, SourceClosureError, ValueError) as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc

    _require(FormalReasonCode.FC03, snapshot.origin_id == capability.origin_id)
    _require(
        FormalReasonCode.FC03,
        source_closure.source_closure_sha256 == capability.source_closure_sha256,
    )
    _require(FormalReasonCode.FC03, source_closure.origin_id == capability.origin_id)
    _require(FormalReasonCode.FC03, source_closure.cell_key == capability.cell_key)
    _require(
        FormalReasonCode.FC03,
        run_plan.source_closure_sha256 == capability.source_closure_sha256,
    )
    capability_sha256 = hashlib.sha256(
        canonical_json_bytes(origin_binding_capability_record(capability))
    ).hexdigest()
    _require(
        FormalReasonCode.FC03,
        run_plan.origin_binding_capability_sha256 == capability_sha256,
    )
    _require(
        FormalReasonCode.FC03,
        manifest.workload["descriptor_sha256"]
        == capability.authority_workload.descriptor_sha256
        == source_closure.referent_sha256s[
            "authority.workload.descriptor_sha256"
        ],
    )
    _require(
        FormalReasonCode.FC03,
        manifest.axis_semantics_sha256 == capability.axis_semantics_sha256,
    )
    _require(
        FormalReasonCode.FC03,
        manifest.verifier_policy_sha256 == capability.verifier_policy_sha256,
    )
    _require(
        FormalReasonCode.FC03,
        manifest.environment_contract_sha256
        == capability.environment_contract_sha256,
    )
    for batch in sealed_batches:
        _require(FormalReasonCode.FC03, batch.origin_id == capability.origin_id)
    for item in paired:
        record = item.record
        origin = record["origin_binding"]
        trial = record["trial_binding"]
        _require(FormalReasonCode.FC03, origin["origin_id"] == capability.origin_id)
        _require(FormalReasonCode.FC03, origin["cell_key"] == capability.cell_key)
        _require(
            FormalReasonCode.FC03,
            origin["authority_blob_sha256"] == capability.authority_blob_sha256,
        )
        _require(
            FormalReasonCode.FC03,
            origin["source_closure_sha256"] == capability.source_closure_sha256,
        )
        _require(FormalReasonCode.FC03, trial["campaign_id"] == capability.campaign_id)
        _require(
            FormalReasonCode.FC03,
            origin["workload"] == capability.trial_workload
            and trial["workload"] == capability.trial_workload,
        )
        _require(
            FormalReasonCode.FC03,
            origin["axis_semantics_sha256"] == capability.axis_semantics_sha256,
        )
        _require(
            FormalReasonCode.FC03,
            origin["verifier_policy_sha256"] == capability.verifier_policy_sha256,
        )
        _require(
            FormalReasonCode.FC03,
            origin["environment_contract_sha256"]
            == capability.environment_contract_sha256,
        )
        _require(
            FormalReasonCode.FC03,
            trial["launch_admission_record_sha256"] == launch_digest,
        )


def _validate_member_mapping(paired: Sequence[_MemberRecord]) -> None:
    for item in paired:
        record = item.record
        member = item.member
        ledger_member = record["ledger_member"]
        physical = record["physical_result"]
        _require(
            FormalReasonCode.FC04,
            ledger_member["query_ordinal"] == member.query_ordinal,
        )
        _require(
            FormalReasonCode.FC04,
            ledger_member["replicate_ordinal"] == member.replicate_ordinal,
        )
        _require(
            FormalReasonCode.FC04,
            record["trigger_binding"]["candidate_wire"].encode("ascii")
            == member.candidate_bytes,
        )
        _require(FormalReasonCode.FC04, physical["outcome"] == member.outcome)
        _require(
            FormalReasonCode.FC04,
            physical["constraint_sha256"] == member.constraint_sha256,
        )


def _resolved_records(
    paired: Sequence[_MemberRecord], *, evidence_root: Path
) -> tuple[ResolvedResultEvidence, ...]:
    try:
        resolved = tuple(
            resolve_result_evidence(item.record, evidence_root=evidence_root)
            for item in paired
        )
    except ResultEvidenceError as exc:
        raise _ContractFailure(FormalReasonCode.FC05B) from exc
    try:
        assert_non_overlapping_wal_ranges(resolved)
    except ResultEvidenceError as exc:
        raise _ContractFailure(FormalReasonCode.FC05B) from exc
    return resolved


def _validate_execution_provenance_bindings(
    capability: OriginBindingCapability,
    paired: Sequence[_MemberRecord],
    resolved: Sequence[ResolvedResultEvidence],
) -> None:
    for item, resolved_item in zip(paired, resolved, strict=True):
        record = item.record
        provenance = resolved_item.execution_provenance
        origin = record["origin_binding"]
        trial = record["trial_binding"]
        physical = record["physical_result"]
        _require(
            FormalReasonCode.FC03,
            provenance["build_attempt_id"] == physical["build_attempt_id"],
        )
        _require(
            FormalReasonCode.FC03,
            provenance["campaign_id"]
            == trial["campaign_id"]
            == capability.campaign_id,
        )
        _require(
            FormalReasonCode.FC03,
            provenance["workload"]
            == origin["workload"]
            == trial["workload"]
            == capability.trial_workload,
        )
        _require(
            FormalReasonCode.FC03,
            provenance["contract_sha256"]
            == origin["environment_contract_sha256"]
            == capability.environment_contract_sha256,
        )
        _require(
            FormalReasonCode.FC03,
            provenance["trigger_binding"] == record["trigger_binding"],
        )


def _validate_physical_campaign_bindings(
    *,
    capability: OriginBindingCapability,
    attempt_capability_sha256: str,
    campaign_output_root: str,
    run_plan: RecoveryEnvelope,
    paired: Sequence[_MemberRecord],
    resolved: Sequence[ResolvedResultEvidence],
) -> None:
    """Bind records below canonical leaves of the caller-selected base.

    ``campaign_output_root`` is not authenticated as a deployment-wide root.
    The checks here establish path and identity consistency under the base the
    caller supplied, subject to the trusted-writer assumption stated above.
    """

    try:
        expected_attempt = _sha256(
            attempt_capability_sha256,
            label="attempt_capability_sha256",
        )
    except ValueError as exc:
        raise _ContractFailure(FormalReasonCode.FC03) from exc
    planned_by_query = {
        member.query_ordinal: member for member in run_plan.members
    }
    for item, resolved_item in zip(paired, resolved, strict=True):
        query_ordinal = item.record["ledger_member"]["query_ordinal"]
        planned = planned_by_query.get(query_ordinal)
        _require(FormalReasonCode.FC03, planned is not None)
        planned_identity = planned.planned_campaign_run_identity
        try:
            computed_root = Path(os.path.abspath(
                exploration_campaign_layout(
                    planned_identity, campaign_output_root
                ).root
            ))
        except (TypeError, ValueError, OSError) as exc:
            raise _ContractFailure(FormalReasonCode.FC03) from exc

        lock_raw = _read_regular_file_no_follow(
            computed_root / "campaign.lock",
            reason_code=FormalReasonCode.FC03,
        )
        try:
            decoded = campaign_lock.decode_campaign_lock_bytes(lock_raw)
        except campaign_lock.CampaignLockCodecError as exc:
            raise _ContractFailure(FormalReasonCode.FC03) from exc
        physical_config = _campaign_config_from_lock(
            decoded,
            expected_campaign_run_identity=planned_identity,
        )
        run_binding = physical_config.search_config.get("origin_campaign_run")
        _require(FormalReasonCode.FC03, type(run_binding) is dict)
        _require(
            FormalReasonCode.FC03,
            set(run_binding) == _ORIGIN_CAMPAIGN_RUN_KEYS,
        )
        _require(
            FormalReasonCode.FC03,
            run_binding["attempt_capability_sha256"] == expected_attempt,
        )
        _require(
            FormalReasonCode.FC03,
            type(run_binding["query_ordinal"]) is int
            and run_binding["query_ordinal"] == query_ordinal,
        )
        _require(
            FormalReasonCode.FC03,
            resolved_item.execution_provenance.get("campaign_run_identity")
            == planned_identity,
        )

        logical_search_config = dict(physical_config.search_config)
        del logical_search_config["origin_campaign_run"]
        logical_config = replace(
            physical_config,
            search_config=logical_search_config,
        )
        try:
            logical_identity = str(ident.campaign_id(logical_config))
        except (TypeError, ValueError) as exc:
            raise _ContractFailure(FormalReasonCode.FC03) from exc
        _require(
            FormalReasonCode.FC03,
            logical_identity == capability.campaign_id,
        )

        projection_path = resolved_item.ordered_wal.projection_ref.normalized_path
        source_wal_path = resolved_item.ordered_wal.source_wal_ref.normalized_path
        _require(
            FormalReasonCode.FC03,
            all(
                path.is_relative_to(computed_root)
                for path in (projection_path, source_wal_path)
            ),
        )


def _wal_trigger_shape_family(record: Mapping[str, object]) -> str | None:
    if record.get("stage") == trigger_gate_binding.WAL_RECORD_STAGE:
        return "native-stage-payload"
    if record.get("kind") == "TriggerGateBinding":
        return "legacy-root"
    return None


def _wal_trigger(records: Sequence[dict]) -> object:
    families = {
        family
        for record in records
        if (family := _wal_trigger_shape_family(record)) is not None
    }
    if families != {"native-stage-payload"}:
        return None
    stage_records = [
        record
        for record in records
        if record.get("stage") == trigger_gate_binding.WAL_RECORD_STAGE
    ]
    if len(stage_records) != 1:
        return None

    record = stage_records[0]
    if set(record) != {"variant", "stage", "env_tag", "ts", "payload"}:
        return None
    if type(record["variant"]) is not str or type(record["env_tag"]) is not str:
        return None
    ts = record["ts"]
    if type(ts) not in (int, float) or (
        type(ts) is float and not math.isfinite(ts)
    ):
        return None
    payload = record["payload"]
    if type(payload) is not dict or set(payload) != {
        "build_attempt_id",
        TRIGGER_BINDING_PAYLOAD_KEY,
    }:
        return None

    try:
        binding = trigger_gate_binding.validate_record(
            payload[TRIGGER_BINDING_PAYLOAD_KEY],
            require_source=False,
        )
    except trigger_gate_binding.TriggerGateBindingError:
        return None

    return {
        "mask": binding.mask,
        "candidate_wire": encode_wire(TriggerGateIR(binding.mask)),
        TRIGGER_BINDING_COMMITMENT_KEY: trigger_gate_binding.commitment(binding),
    }


def _validate_bijection(
    paired: Sequence[_MemberRecord],
    resolved: Sequence[ResolvedResultEvidence],
) -> None:
    attempts = [item.record["physical_result"]["build_attempt_id"] for item in paired]
    _require(FormalReasonCode.FC05A, len(attempts) == len(set(attempts)))
    for item, resolved_item in zip(paired, resolved, strict=True):
        _require(
            FormalReasonCode.FC05C,
            _wal_trigger(resolved_item.ordered_wal.records)
            == item.record["trigger_binding"],
        )


def _validate_topology(
    paired: Sequence[_MemberRecord], run_plan: RecoveryEnvelope
) -> None:
    _require(
        FormalReasonCode.FC06,
        len(paired) == SOURCE_AND_VALIDATION_MEMBER_COUNT,
    )
    records = [item.record for item in paired]
    source = records[0]
    _require(FormalReasonCode.FC06, source["p6_plan"]["purpose"] == "source")
    source_mask = source["trigger_binding"]["mask"]
    for index, record in enumerate(records):
        plan = record["p6_plan"]
        _require(
            FormalReasonCode.FC06,
            plan["hypothesis_sha256"] == run_plan.hypothesis_sha256
            and plan["validation_plan_sha256"] == run_plan.validation_plan_sha256,
        )
        planned = run_plan.members[index]
        _require(
            FormalReasonCode.FC06,
            record["ledger_member"]["iteration_index"] == planned.iteration_index
            and record["ledger_member"]["query_ordinal"] == planned.query_ordinal
            and record["ledger_member"]["replicate_ordinal"]
            == planned.replicate_ordinal
            and record["trigger_binding"]["candidate_wire"]
            == planned.candidate_wire,
        )
    masks = [record["trigger_binding"]["mask"] for record in records[1:]]
    _require(FormalReasonCode.FC06, masks == list(range(VALIDATION_MASK_COUNT)))
    _require(
        FormalReasonCode.FC06,
        all(record["p6_plan"]["purpose"] == "p6-validation" for record in records[1:]),
    )
    _require(
        FormalReasonCode.FC06,
        records[1 + source_mask]["ledger_member"]["replicate_ordinal"] == 1,
    )


def _wal_field(record: Mapping[str, object], name: str) -> object:
    if name in record:
        return record[name]
    payload = record.get("payload")
    return payload.get(name) if type(payload) is dict else None


def _valid_witness_anomaly(anomaly: object) -> bool:
    return result_evidence.validate_witness_anomaly(anomaly)


def _witness_class_sha256(anomaly: object) -> str:
    try:
        return result_evidence.witness_class_sha256(anomaly)
    except ArtifactError as exc:
        raise _ContractFailure(FormalReasonCode.FC07) from exc


def _verifier_policy(raw_bytes: bytes, expected_sha256: str) -> tuple[str, ...]:
    try:
        policy = strict_json_loads(raw_bytes)
    except ArtifactError as exc:
        raise _ContractFailure(FormalReasonCode.FC07) from exc
    _require(FormalReasonCode.FC07, type(policy) is dict)
    _require(
        FormalReasonCode.FC07,
        hashlib.sha256(raw_bytes).hexdigest() == expected_sha256,
    )
    ordered = policy.get("ordered_passes")
    _require(
        FormalReasonCode.FC07,
        type(ordered) is list
        and ordered
        and all(type(item) is str and item for item in ordered),
    )
    return tuple(ordered)


def _wal_terminal_shape_valid(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):
        return False
    if type(terminal["variant"]) is not str:
        return False
    if type(terminal["env_tag"]) is not str:
        return False
    terminal_ts = terminal["ts"]
    if type(terminal_ts) not in (int, float):
        return False
    if type(terminal_ts) is float and not math.isfinite(terminal_ts):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    terminal_count = sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
        for record in records
    )
    return terminal_count == 1


def _validate_wal_outcomes(
    paired: Sequence[_MemberRecord],
    resolved: Sequence[ResolvedResultEvidence],
    *,
    ordered_verifiers: tuple[str, ...],
) -> None:
    for item, resolved_item in zip(paired, resolved, strict=True):
        physical = item.record["physical_result"]
        wal_records = resolved_item.ordered_wal.records
        terminal = wal_records[-1]
        _require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))
        attempt = physical["build_attempt_id"]
        _require(FormalReasonCode.FC07, _wal_field(terminal, "build_attempt_id") == attempt)
        if physical["outcome"] == "accepted":
            _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_COMMIT)
            _require(
                FormalReasonCode.FC07,
                tuple(_wal_field(terminal, "verify_configs") or ()) == ordered_verifiers,
            )
        else:
            _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)
            _require(
                FormalReasonCode.FC07,
                _wal_field(terminal, "reason")
                == _CANDIDATE_ATTRIBUTABLE_ABORT_REASON,
            )
            verify = _wal_field(terminal, "verify")
            _require(FormalReasonCode.FC07, type(verify) is dict)
            _require(FormalReasonCode.FC07, set(verify) == _VERIFY_KEYS)
            stats = verify.get("stats")
            _require(
                FormalReasonCode.FC07,
                type(stats) is dict and set(stats) == _VERIFY_STATS_KEYS,
            )
            _require(
                FormalReasonCode.FC07,
                all(
                    type(stats[key]) is int and stats[key] >= 0
                    for key in ("txns", "reads", "writes", "keys", "edges")
                ),
            )
            abort_reasons = stats["abort_reasons"]
            _require(
                FormalReasonCode.FC07,
                type(abort_reasons) is dict
                and all(
                    type(reason) is str
                    and type(count) is int
                    and count >= 0
                    for reason, count in abort_reasons.items()
                ),
            )
            integrity = verify.get("integrity")
            _require(
                FormalReasonCode.FC07,
                type(integrity) is dict
                and set(integrity) == _VERIFY_INTEGRITY_KEYS,
            )
            permutation_details = integrity.get("permutation_violation_details")
            _require(
                FormalReasonCode.FC07,
                type(permutation_details) is dict
                and set(permutation_details)
                == _PERMUTATION_VIOLATION_DETAILS_KEYS,
            )
            _require(
                FormalReasonCode.FC07,
                verify.get("verdict") == _CANDIDATE_ATTRIBUTABLE_ABORT_REASON,
            )
            _require(FormalReasonCode.FC07, verify.get("serializable") is False)
            _require(FormalReasonCode.FC07, verify.get("certified") is False)
            _require(
                FormalReasonCode.FC07,
                integrity.get("clean") is True,
            )
            # These wire counters are necessary, not sufficient, evidence of clean integrity.
            _require(
                FormalReasonCode.FC07,
                all(
                    type(integrity[key]) is int and integrity[key] == 0
                    for key in _CLEAN_WIRE_COUNTER_KEYS
                ),
            )
            _require(
                FormalReasonCode.FC07,
                type(integrity["framing_violation_details"]) is list
                and (
                    integrity["framing_violations"] != 0
                    or not integrity["framing_violation_details"]
                ),
            )
            _require(
                FormalReasonCode.FC07,
                type(integrity["notes"]) is list
                and all(type(note) is str for note in integrity["notes"]),
            )
            permutation_counts = permutation_details.get("counts")
            _require(
                FormalReasonCode.FC07,
                type(permutation_counts) is dict
                and set(permutation_counts) == _PERMUTATION_VIOLATION_COUNT_KEYS
                and all(
                    type(count) is int and count >= 0
                    for count in permutation_counts.values()
                )
                and sum(permutation_counts.values())
                == integrity["permutation_violations"],
            )
            _require(
                FormalReasonCode.FC07,
                type(permutation_details["sample"]) is list,
            )
            _require(
                FormalReasonCode.FC07,
                type(permutation_details["unknown_reason_sample"]) is list,
            )
            anomalies = verify.get("anomalies")
            _require(
                FormalReasonCode.FC07,
                type(anomalies) is list and len(anomalies) == 1,
            )
            total_cycles = verify.get("total_cycles")
            anomaly_count = verify.get("anomaly_count")
            _require(FormalReasonCode.FC07, type(total_cycles) is int)
            _require(FormalReasonCode.FC07, type(anomaly_count) is int)
            _require(FormalReasonCode.FC07, anomaly_count == len(anomalies))
            _require(FormalReasonCode.FC07, total_cycles == anomaly_count)
            _require(FormalReasonCode.FC07, _valid_witness_anomaly(anomalies[0]))
            _require(
                FormalReasonCode.FC07,
                _witness_class_sha256(anomalies[0])
                == physical["constraint_sha256"],
            )


def _validate_exact_rejected_classes(paired: Sequence[_MemberRecord]) -> None:
    record_values = {
        item.record["physical_result"]["constraint_sha256"]
        for item in paired
        if item.record["physical_result"]["outcome"] == "rejected"
    }
    ledger_values = {
        item.member.constraint_sha256
        for item in paired
        if item.member.outcome == "rejected"
    }
    _require(
        FormalReasonCode.FC09,
        all(type(value) is str and _SHA256_RE.fullmatch(value) for value in ledger_values),
    )
    record_classes = tuple(sorted(record_values))
    ledger_classes = tuple(sorted(ledger_values))
    _require(FormalReasonCode.FC09, record_classes == ledger_classes)


def _validate_aggregate(
    *,
    paired: Sequence[_MemberRecord],
    manifest: ledger.AuthorityManifest,
    snapshot: ledger.OriginSnapshot,
) -> None:
    observed = tuple(sorted({
        item.record["physical_result"]["constraint_sha256"]
        for item in paired
        if item.record["physical_result"]["outcome"] == "rejected"
    }))
    _require(FormalReasonCode.FC09, len(observed) <= manifest.budget_policy.kmax)
    _require(
        FormalReasonCode.FC09,
        all(
            snapshot.sealed_queries >= floor.required_queries
            for floor in manifest.budget_policy.query_floor_constraints
        ),
    )


def _validate_no_all_tombstone_batch(
    sealed_batches: Sequence[ledger.SealedBatch],
) -> None:
    for batch in sealed_batches:
        _require(
            FormalReasonCode.FC10,
            not batch.members
            or any(member.outcome != "tombstoned" for member in batch.members),
        )


def _issue_receipt(
    *,
    operation_id: str,
    capability: OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    run_plan: RecoveryEnvelope,
    snapshot: ledger.OriginSnapshot,
    decision: AbortedOriginDecision,
    evidence_sha256s: tuple[str, ...],
    enforcement_arm: str,
    arm_binding_digest_sha256: str,
    generator_closure: Mapping[str, object],
) -> FormalConsumerReceipt:
    _token(operation_id, label="operation_id")
    _token(enforcement_arm, label="enforcement_arm")
    _sha256(arm_binding_digest_sha256, label="arm_binding_digest_sha256")
    if type(generator_closure) is not dict:
        raise TypeError("generator_closure must be an exact object")
    detached = json.loads(canonical_json_bytes(generator_closure).decode("utf-8"))
    evidence_root_sha256 = hashlib.sha256(
        canonical_json_bytes(list(evidence_sha256s))
    ).hexdigest()
    receipt = FormalConsumerReceipt(
        operation_id=operation_id,
        authority_blob_sha256=capability.authority_blob_sha256,
        source_closure_sha256=source_closure.source_closure_sha256,
        run_plan_sha256=hashlib.sha256(
            canonical_recovery_envelope_bytes(run_plan)
        ).hexdigest(),
        origin_id=capability.origin_id,
        input_state_commitment=snapshot.state_commitment,
        origin_sealed_payload_sha256=decision.terminal_payload_sha256,
        evidence_sha256s=evidence_sha256s,
        evidence_root_sha256=evidence_root_sha256,
        enforcement_arm=enforcement_arm,
        arm_binding_digest_sha256=arm_binding_digest_sha256,
        generator_closure=detached,
        reason_code=FormalReasonCode.P6_UNAVAILABLE,
        _issuer=_RECEIPT_CONSTRUCTOR,
    )
    raw = canonical_json_bytes(formal_consumer_receipt_record(receipt))
    _ISSUED_RECEIPTS[receipt._seal] = raw
    return receipt


def evaluate_formal_origin(
    *,
    capability: OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    run_plan: RecoveryEnvelope,
    campaign_output_root: str,
    origin_run_plan_sha256: str,
    attempt_capability_sha256: str,
    authority_blob_bytes: bytes,
    launch_admission_record_sha256: str,
    origin_snapshot: ledger.OriginSnapshot,
    sealed_batches: Sequence[ledger.SealedBatch],
    result_record_bytes: Sequence[bytes],
    evidence_root: Path,
    verifier_policy_bytes: bytes,
    enforcement_arm: str,
    arm_binding_digest_sha256: str,
    generator_closure: Mapping[str, object],
    operation_id: str,
) -> FormalConsumerResult:
    """Evaluate conditions 1--7, 9--10 and §4.2, then stop at P6.

    The physical-layout result is relative to the caller-selected
    ``campaign_output_root`` base.  It does not certify a unique deployment
    root, physical execution, or the identity of the evidence writer.
    """

    if type(capability) is not OriginBindingCapability:
        raise TypeError("capability must be an exact OriginBindingCapability")
    issued_capability = assert_issued_origin_binding_capability(capability)
    if type(origin_snapshot) is not ledger.OriginSnapshot:
        raise TypeError("origin_snapshot must be an exact OriginSnapshot")
    if type(run_plan) is not RecoveryEnvelope:
        raise TypeError("run_plan must be an exact RecoveryEnvelope")
    if type(campaign_output_root) is not str:
        raise TypeError("campaign_output_root must be an exact string")
    _sha256(arm_binding_digest_sha256, label="arm_binding_digest_sha256")
    if issued_capability.enforcement_arm != enforcement_arm:
        raise ValueError("enforcement_arm differs from issued arm binding")
    if (
        issued_capability.arm_binding_digest_sha256
        != arm_binding_digest_sha256
    ):
        raise ValueError(
            "arm_binding_digest_sha256 differs from issued arm binding"
        )
    try:
        paired = _pair_records(
            sealed_batches=sealed_batches,
            result_record_bytes=result_record_bytes,
        )
        manifest = _authority_manifest(authority_blob_bytes, capability)
        _validate_bindings(
            capability=capability,
            source_closure=source_closure,
            manifest=manifest,
            run_plan=run_plan,
            launch_admission_record_sha256=launch_admission_record_sha256,
            snapshot=origin_snapshot,
            sealed_batches=sealed_batches,
            paired=paired,
        )
        _validate_bound_recovery_envelope(
            evidence_root=Path(evidence_root),
            run_plan=run_plan,
            origin_run_plan_sha256=origin_run_plan_sha256,
        )
        _validate_exact_rejected_classes(paired)
        _validate_member_mapping(paired)
        resolved = _resolved_records(paired, evidence_root=Path(evidence_root))
        _validate_execution_provenance_bindings(capability, paired, resolved)
        _validate_physical_campaign_bindings(
            capability=capability,
            attempt_capability_sha256=attempt_capability_sha256,
            campaign_output_root=campaign_output_root,
            run_plan=run_plan,
            paired=paired,
            resolved=resolved,
        )
        _validate_bijection(paired, resolved)
        _validate_topology(paired, run_plan)
        ordered_verifiers = _verifier_policy(
            verifier_policy_bytes, capability.verifier_policy_sha256
        )
        _validate_wal_outcomes(
            paired, resolved, ordered_verifiers=ordered_verifiers
        )
        _validate_aggregate(
            paired=paired,
            manifest=manifest,
            snapshot=origin_snapshot,
        )
        _validate_no_all_tombstone_batch(sealed_batches)
    except _ContractFailure as failure:
        return _rejected(
            failure.reason_code,
            snapshot=origin_snapshot,
            capability=capability,
            arm_binding_digest_sha256=arm_binding_digest_sha256,
        )

    decision = _decision(origin_snapshot)
    evidence_sha256s = tuple(item.raw_sha256 for item in paired)
    receipt = _issue_receipt(
        operation_id=operation_id,
        capability=capability,
        source_closure=source_closure,
        run_plan=run_plan,
        snapshot=origin_snapshot,
        decision=decision,
        evidence_sha256s=evidence_sha256s,
        enforcement_arm=enforcement_arm,
        arm_binding_digest_sha256=arm_binding_digest_sha256,
        generator_closure=generator_closure,
    )
    reason = FormalReasonCode.P6_UNAVAILABLE
    return P6Unavailable(
        reason,
        receipt,
        decision,
        _projection(
            reason_code=reason,
            decision=decision,
            capability=capability,
            receipt=receipt,
            arm_binding_digest_sha256=arm_binding_digest_sha256,
        ),
    )


def _receipt_request_bytes(
    *, input_state_commitment: str, decision: AbortedOriginDecision
) -> bytes:
    return canonical_json_bytes({
        "input_state_commitment": input_state_commitment,
        "origin_sealed_payload": _aborted_origin_payload(decision),
    })


def consume_formal_consumer_receipt(
    receipt: FormalConsumerReceipt,
    *,
    operation_id: str,
    input_state_commitment: str,
    decision: AbortedOriginDecision,
) -> AbortedOriginDecision:
    """Consume once, while allowing byte-identical exact-operation replay."""

    canonical_formal_consumer_receipt_bytes(receipt)
    if operation_id != receipt.operation_id:
        raise FormalReceiptError(
            FormalReceiptReason.OPERATION, "receipt operation_id mismatch"
        )
    request_bytes = _receipt_request_bytes(
        input_state_commitment=input_state_commitment, decision=decision
    )
    with _REPLAY_LOCK:
        cached = _OPERATION_REPLAY_CACHE.get(operation_id)
        if cached is not None:
            if cached.request_bytes != request_bytes:
                raise FormalReceiptError(
                    FormalReceiptReason.REPLAY,
                    "operation_id was already used with different payload bytes",
                )
            return cached.decision
        if input_state_commitment != receipt.input_state_commitment:
            raise FormalReceiptError(
                FormalReceiptReason.STATE, "receipt input state commitment mismatch"
            )
        observed_payload_sha256 = aborted_origin_payload_sha256(decision)
        if (
            decision.terminal_payload_sha256 != observed_payload_sha256
            or observed_payload_sha256 != receipt.origin_sealed_payload_sha256
        ):
            raise FormalReceiptError(
                FormalReceiptReason.PAYLOAD, "receipt terminal payload digest mismatch"
            )
        _OPERATION_REPLAY_CACHE[operation_id] = _ReplayEntry(
            request_bytes=request_bytes, decision=decision
        )
        return decision
