"""Exact ``result-evidence/v1`` records and content-addressed resolution.

Content-addressed resolution proves only that the retrieved bytes are the
bytes claimed by the record.  It does not prove that those bytes correspond to
a physical execution.  This resolver must not be described as proof of
physical execution.

Likewise, create-only storage does not authenticate the first writer.  The
record path is sound only under the operational assumption that the trusted
physical harness is the sole writer to the evidence root.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import posixpath
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, Mapping, Sequence

from orchestrator.verifier.model import RW, WR, WW, VerifyResult
from orchestrator.verifier.report import result_to_dict

from . import execution_guard
from . import reflux_origin_ledger as ledger
from . import reflux_origin_binding
from . import trigger_gate_binding
from . import wal as wal_codec
from .env_contract import ExecutionEnvironmentContract
from .layout import CampaignLayout, ExplorationCampaignLayout, validate_campaign_id
from .model import STAGE_ABORT, STAGE_COMMIT
from .reflux_ir import TriggerGateIR, encode_wire
from .reflux_origin_artifacts import (
    ArtifactError,
    canonical_json_bytes,
    strict_json_loads,
    write_create_only,
    write_json_create_only,
)


__all__ = [
    "RESULT_EVIDENCE_SCHEMA_VERSION",
    "RECORD_RAW_SHA256_LAYER",
    "LEDGER_EVIDENCE_DIGEST_LAYER",
    "LEDGER_OUTER_COMMITMENT_LAYER",
    "ResultEvidenceError",
    "ResultEvidenceIssuanceRefused",
    "ResultEvidenceIssuanceContext",
    "DerivedPhysicalResult",
    "ResolvedEvidenceBytes",
    "ResolvedOrderedWal",
    "ResolvedResultEvidence",
    "validate_result_evidence",
    "validate_witness_anomaly",
    "witness_class_sha256",
    "derive_physical_result",
    "produce_ordered_wal_projection",
    "assemble_result_evidence_record",
    "issue_campaign_result_evidence",
    "issue_result_evidence_record",
    "canonical_result_evidence_bytes",
    "parse_result_evidence_bytes",
    "result_evidence_record_raw_sha256",
    "ledger_evidence_digest_sha256",
    "ledger_result_evidence_outer_commitment",
    "result_evidence_relative_path",
    "write_result_evidence_record",
    "resolve_content_addressed_ref",
    "resolve_result_evidence",
    "resolve_result_evidence_batch",
    "assert_non_overlapping_wal_ranges",
    "map_result_evidence_to_opened_member",
    "map_result_evidence_to_sealed_member",
    "map_absent_result_to_opened_tombstone",
    "map_absent_result_to_sealed_tombstone",
]


RESULT_EVIDENCE_SCHEMA_VERSION = "result-evidence/v1"
RESULT_EVIDENCE_ISSUER_KIND = "trusted-physical-harness"

# These labels deliberately identify three different hash/commitment layers.
# The first two have equal values by contract, but are computed by independent
# helpers.  The third delegates to the ledger's existing domain-separated
# salted commitment implementation.
RECORD_RAW_SHA256_LAYER = "result-evidence-record/raw-sha256/v1"
LEDGER_EVIDENCE_DIGEST_LAYER = "ledger-evidence-digest/raw-sha256/v1"
LEDGER_OUTER_COMMITMENT_LAYER = "ledger-result-evidence/salted-domain/v1"

_RECORD_RAW_SHA256_ALGORITHM = "sha256"
_LEDGER_EVIDENCE_DIGEST_ALGORITHM = "sha256"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_CAMPAIGN_ID_RE = re.compile(r".+-.+-[0-9a-f]{8}\Z")
_TOP_LEVEL_KEYS = frozenset({
    "schema_version",
    "issuer",
    "origin_binding",
    "trial_binding",
    "ledger_member",
    "p6_plan",
    "trigger_binding",
    "physical_result",
    "evidence",
})
_ORIGIN_BINDING_KEYS = frozenset({
    "authority_blob_sha256",
    "source_closure_sha256",
    "origin_id",
    "cell_key",
    "workload",
    "axis_semantics_sha256",
    "verifier_policy_sha256",
    "environment_contract_sha256",
})
_TRIAL_BINDING_KEYS = frozenset({
    "launch_admission_record_sha256", "campaign_id", "workload",
})
_LEDGER_MEMBER_KEYS = frozenset({
    "batch_id", "iteration_index", "query_ordinal", "replicate_ordinal",
})
_P6_PLAN_KEYS = frozenset({
    "purpose", "hypothesis_sha256", "validation_plan_sha256",
})
_TRIGGER_BINDING_KEYS = frozenset({
    "mask", "candidate_wire", "trigger_gate_binding_commitment",
})
_PHYSICAL_RESULT_KEYS = frozenset({
    "build_attempt_id", "outcome", "constraint_sha256",
})
_EVIDENCE_KEYS = frozenset({
    "ordered_wal_ref", "execution_provenance_ref",
})
_REFERENCE_KEYS = frozenset({"path", "sha256"})
_ORDERED_WAL_KEYS = frozenset({
    "schema_version",
    "source_wal_ref",
    "byte_start",
    "byte_end",
    "build_attempt_id",
    "records",
})
_PRODUCTION_WAL_RECORD_KEYS = frozenset({
    "variant", "stage", "env_tag", "ts", "payload",
})
_EXECUTION_PROVENANCE_V2_KEYS = frozenset({
    "schema_version",
    "build_attempt_id",
    "campaign_id",
    "workload",
    "contract_sha256",
    "trigger_binding",
    "execution_receipt_sha256",
    "campaign_run_identity",
})
_ANOMALY_KEYS = frozenset({"phenomenon", "length", "cycle", "edges"})
_EDGE_KEYS = frozenset({"from", "to", "types", "reasons"})
_REASON_REQUIRED_KEYS = frozenset({"type", "key"})
_REASON_OPTIONAL_KEYS = frozenset({"u_ver", "v_ver"})
_REASON_TYPES = frozenset({WW, WR, RW})
_REASON_VERSION_KEYS = {
    WW: frozenset({"u_ver", "v_ver"}),
    WR: frozenset({"u_ver"}),
    RW: frozenset({"u_ver", "v_ver"}),
}
_PHENOMENA = frozenset({"G0", "G1c", "G2"})
_VERIFY_KEYS = frozenset({
    "verdict",
    "certified",
    "serializable",
    "stats",
    "integrity",
    "anomaly_count",
    "total_cycles",
    "anomalies",
})
_VERIFY_STATS_KEYS = frozenset({
    "txns",
    "reads",
    "writes",
    "keys",
    "edges",
    "abort_reasons",
})
_VERIFY_INTEGRITY_KEYS = frozenset({
    "clean",
    "orphan_reads",
    "version_dups",
    "dup_txids",
    "genesis_commits",
    "missing_txids",
    "write_version_mismatch",
    "malformed_keys",
    "framing_violations",
    "framing_violation_details",
    "lock_coverage_violations",
    "write_intent_violations",
    "permutation_violations",
    "permutation_violation_details",
    "notes",
})
_PERMUTATION_VIOLATION_DETAILS_KEYS = frozenset({
    "counts",
    "sample",
    "unknown_reason_sample",
})
_PERMUTATION_VIOLATION_COUNT_KEYS = frozenset({
    "size-changed",
    "rcdptr-set-changed",
    "unknown",
})
_CLEAN_WIRE_COUNTER_KEYS = frozenset({
    "orphan_reads",
    "version_dups",
    "dup_txids",
    "genesis_commits",
    "missing_txids",
    "write_version_mismatch",
    "malformed_keys",
    "framing_violations",
    "lock_coverage_violations",
    "write_intent_violations",
    "permutation_violations",
})


class ResultEvidenceError(ValueError):
    """Fail-closed rejection of result evidence or one of its referents."""


class ResultEvidenceIssuanceRefused(ResultEvidenceError):
    """Refuse issuance when no unique trustworthy physical result is derivable."""


@dataclass(frozen=True, slots=True)
class ResultEvidenceIssuanceContext:
    origin_capability: object
    evidence_root: Path
    batch_id: str
    query_ordinal: int
    iteration_index: int
    replicate_ordinal: int
    p6_plan: Mapping[str, object]
    trial_binding: Mapping[str, object]
    origin_binding: Mapping[str, object]
    ordered_verifiers: tuple[str, ...]
    expected_record_path: str
    env_tag: str
    attestation_mode: str
    verified_calibration: object | None


@dataclass(frozen=True, slots=True)
class DerivedPhysicalResult:
    """Physical result derived from one terminal WAL interval."""

    build_attempt_id: str
    outcome: Literal["accepted", "rejected"]
    constraint_sha256: str | None
    ordered_wal_sha256: str


@dataclass(frozen=True, slots=True)
class ResolvedEvidenceBytes:
    """Bytes retrieved from one confined, digest-matching reference."""

    claimed_path: str
    normalized_path: Path
    identity: tuple[int, int]
    sha256: str
    raw_bytes: bytes


@dataclass(frozen=True, slots=True)
class ResolvedOrderedWal:
    """A projection and the physical source-WAL interval it binds."""

    projection_ref: ResolvedEvidenceBytes
    source_wal_ref: ResolvedEvidenceBytes
    byte_start: int
    byte_end: int
    build_attempt_id: str
    records: tuple[dict, ...]

    @property
    def range_identity(self) -> tuple[tuple[int, int], int, int]:
        return self.source_wal_ref.identity, self.byte_start, self.byte_end


@dataclass(frozen=True, slots=True)
class ResolvedResultEvidence:
    """Validated record plus digest-checked WAL and provenance bytes."""

    record: dict
    record_bytes: bytes
    ordered_wal: ResolvedOrderedWal
    execution_provenance_ref: ResolvedEvidenceBytes
    execution_provenance: dict


def _fail(message: str) -> None:
    raise ResultEvidenceError(message)


def _exact_object(value: object, keys: frozenset[str], *, label: str) -> dict:
    if type(value) is not dict:
        _fail(f"{label} must be an object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        _fail(f"{label} keys are not exact (missing={missing}, unknown={unknown})")
    return value


def _text(value: object, *, label: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        _fail(f"{label} must be a non-empty string")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ResultEvidenceError(f"{label} is not valid UTF-8 text") from exc
    return value


def _sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be a lowercase sha256")
    return value


def _campaign_identity(value: object, *, label: str) -> str:
    identity = _text(value, label=label)
    if _CAMPAIGN_ID_RE.fullmatch(identity) is None:
        _fail(f"{label} is not an ident campaign identity")
    try:
        return validate_campaign_id(identity)
    except ValueError as exc:
        raise ResultEvidenceError(f"{label} is not a campaign identity") from exc


def _ordinal(value: object, *, label: str) -> int:
    if type(value) is not int or value < 0:
        _fail(f"{label} must be a non-negative integer")
    return value


def validate_witness_anomaly(anomaly: object) -> bool:
    if type(anomaly) is not dict or set(anomaly) != _ANOMALY_KEYS:
        return False
    phenomenon = anomaly["phenomenon"]
    if type(phenomenon) is not str or phenomenon not in _PHENOMENA:
        return False
    cycle = anomaly["cycle"]
    if (
        type(cycle) is not list
        or len(cycle) < 2
        or any(type(txid) is not int for txid in cycle)
        or len(set(cycle)) != len(cycle)
        or type(anomaly["length"]) is not int
        or anomaly["length"] != len(cycle)
    ):
        return False
    edges = anomaly["edges"]
    if type(edges) is not list or len(edges) != len(cycle):
        return False
    all_types: set[str] = set()
    for index, edge in enumerate(edges):
        if type(edge) is not dict or set(edge) != _EDGE_KEYS:
            return False
        if (
            type(edge["from"]) is not int
            or type(edge["to"]) is not int
            or edge["from"] != cycle[index]
            or edge["to"] != cycle[(index + 1) % len(cycle)]
        ):
            return False
        types = edge["types"]
        reasons = edge["reasons"]
        if (
            type(types) is not list
            or not types
            or any(type(edge_type) is not str for edge_type in types)
            or type(reasons) is not list
            or not reasons
        ):
            return False
        derived_types: list[str] = []
        seen_types: set[str] = set()
        for reason in reasons:
            if type(reason) is not dict:
                return False
            keys = set(reason)
            if not _REASON_REQUIRED_KEYS <= keys <= (
                _REASON_REQUIRED_KEYS | _REASON_OPTIONAL_KEYS
            ):
                return False
            reason_type = reason["type"]
            if (
                type(reason_type) is not str
                or reason_type not in _REASON_TYPES
                or type(reason["key"]) is not str
            ):
                return False
            expected_version_keys = _REASON_VERSION_KEYS.get(reason_type)
            if (
                expected_version_keys is not None
                and keys & _REASON_OPTIONAL_KEYS != expected_version_keys
            ):
                return False
            for optional in _REASON_OPTIONAL_KEYS:
                if optional in reason and (
                    type(reason[optional]) is not list
                    or len(reason[optional]) != 2
                    or any(type(item) is not int for item in reason[optional])
                ):
                    return False
            if reason_type not in seen_types:
                seen_types.add(reason_type)
                derived_types.append(reason_type)
        if types != derived_types:
            return False
        all_types.update(types)
    derived_phenomenon = (
        "G2" if RW in all_types else "G1c" if WR in all_types else "G0"
    )
    return phenomenon == derived_phenomenon


def witness_class_sha256(anomaly: object) -> str:
    return hashlib.sha256(canonical_json_bytes(anomaly)).hexdigest()


def _issuance_refused(message: str) -> None:
    raise ResultEvidenceIssuanceRefused(
        "result evidence issuance refused: " + message
    )


def _ordered_attempt_materials(
    *, layout: object, build_attempt_id: str,
) -> tuple[tuple[wal_codec.OrderedAttemptFrame, ...], bytes]:
    if (
        type(layout) is not CampaignLayout
        and type(layout) is not ExplorationCampaignLayout
    ):
        raise ResultEvidenceError(
            "layout must be an exact CampaignLayout or ExplorationCampaignLayout"
        )
    if type(build_attempt_id) is not str or not build_attempt_id:
        _issuance_refused("build attempt identity is absent or invalid")
    try:
        frames = wal_codec.ordered_attempt_frames(layout, build_attempt_id)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ResultEvidenceIssuanceRefused(
            "result evidence issuance refused: WAL frames are not complete and valid"
        ) from exc
    if not frames:
        _issuance_refused("the build attempt has no WAL frames")

    # The WAL API owns physical framing and offsets.  This check uses those
    # offsets only to reject another attempt interleaved inside this interval.
    if any(
        previous.byte_end != current.byte_start
        for previous, current in zip(frames, frames[1:])
    ):
        _issuance_refused("the build attempt WAL frames are not physically contiguous")

    terminal_byte_end = frames[-1].byte_end
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ResultEvidenceError("O_NOFOLLOW is required for source WAL capture")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(layout.wal_file, flags)
    except OSError as exc:
        raise ResultEvidenceError("source WAL cannot be opened safely") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ResultEvidenceError("source WAL must be a regular file")
        chunks: list[bytes] = []
        offset = 0
        while offset < terminal_byte_end:
            chunk = os.pread(fd, min(1024 * 1024, terminal_byte_end - offset), offset)
            if not chunk:
                raise ResultEvidenceError(
                    "source WAL ended before the terminal frame boundary"
                )
            chunks.append(chunk)
            offset += len(chunk)
    except OSError as exc:
        raise ResultEvidenceError("source WAL prefix snapshot read failed") from exc
    finally:
        os.close(fd)

    # This is an immutable snapshot of wal.jsonl[0:terminal_byte_end], not a
    # reference to the live WAL.  The projection keeps the original offsets.
    terminal_prefix_snapshot = b"".join(chunks)
    if any(
        terminal_prefix_snapshot[frame.byte_start:frame.byte_end] != frame.raw_bytes
        for frame in frames
    ):
        raise ResultEvidenceError("source WAL changed during prefix snapshot capture")
    return frames, terminal_prefix_snapshot


def _project_ordered_attempt_records(
    frames: Sequence[wal_codec.OrderedAttemptFrame],
) -> list[dict]:
    return [
        {
            "variant": frame.record.variant,
            "stage": frame.record.stage,
            "env_tag": frame.record.env_tag,
            "ts": frame.record.ts,
            "payload": frame.record.payload,
        }
        for frame in frames
    ]


def produce_ordered_wal_projection(
    *,
    layout: object,
    build_attempt_id: str,
    source_wal_ref: Mapping[str, object],
) -> bytes:
    """Produce canonical bytes for one physically ordered attempt interval.

    ``source_wal_ref`` must name the immutable terminal-prefix snapshot whose
    digest equals ``wal.jsonl[0:byte_end]``.  A live WAL path is not suitable.
    """

    frames, terminal_prefix_snapshot = _ordered_attempt_materials(
        layout=layout, build_attempt_id=build_attempt_id
    )
    source_ref = _reference(
        source_wal_ref, label="ordered WAL projection.source_wal_ref"
    )
    if source_ref["sha256"] != _content_addressed_referent_sha256(
        terminal_prefix_snapshot
    ):
        raise ResultEvidenceError(
            "source WAL reference does not match the terminal prefix snapshot"
        )
    projection = {
        "schema_version": "ordered-wal-projection/v1",
        "source_wal_ref": dict(source_ref),
        "byte_start": frames[0].byte_start,
        "byte_end": frames[-1].byte_end,
        "build_attempt_id": build_attempt_id,
        "records": _project_ordered_attempt_records(frames),
    }
    return canonical_json_bytes(projection)


def _valid_rejected_verify_snapshot(snapshot: object) -> bool:
    if type(snapshot) is not dict or set(snapshot) != _VERIFY_KEYS:
        return False
    stats = snapshot.get("stats")
    if type(stats) is not dict or set(stats) != _VERIFY_STATS_KEYS:
        return False
    if not all(
        type(stats[key]) is int and stats[key] >= 0
        for key in ("txns", "reads", "writes", "keys", "edges")
    ):
        return False
    abort_reasons = stats["abort_reasons"]
    if type(abort_reasons) is not dict or not all(
        type(reason) is str and type(count) is int and count >= 0
        for reason, count in abort_reasons.items()
    ):
        return False
    integrity = snapshot.get("integrity")
    if type(integrity) is not dict or set(integrity) != _VERIFY_INTEGRITY_KEYS:
        return False
    permutation_details = integrity.get("permutation_violation_details")
    if (
        type(permutation_details) is not dict
        or set(permutation_details) != _PERMUTATION_VIOLATION_DETAILS_KEYS
    ):
        return False
    if snapshot.get("verdict") != "non-serializable":
        return False
    if snapshot.get("serializable") is not False:
        return False
    if snapshot.get("certified") is not False:
        return False
    if integrity.get("clean") is not True:
        return False
    if not all(
        type(integrity[key]) is int and integrity[key] == 0
        for key in _CLEAN_WIRE_COUNTER_KEYS
    ):
        return False
    if type(integrity["framing_violation_details"]) is not list or not (
        integrity["framing_violations"] != 0
        or not integrity["framing_violation_details"]
    ):
        return False
    if type(integrity["notes"]) is not list or not all(
        type(note) is str for note in integrity["notes"]
    ):
        return False
    permutation_counts = permutation_details.get("counts")
    if not (
        type(permutation_counts) is dict
        and set(permutation_counts) == _PERMUTATION_VIOLATION_COUNT_KEYS
        and all(
            type(count) is int and count >= 0
            for count in permutation_counts.values()
        )
        and sum(permutation_counts.values()) == integrity["permutation_violations"]
    ):
        return False
    if type(permutation_details["sample"]) is not list:
        return False
    if type(permutation_details["unknown_reason_sample"]) is not list:
        return False
    anomalies = snapshot.get("anomalies")
    if type(anomalies) is not list or len(anomalies) != 1:
        return False
    total_cycles = snapshot.get("total_cycles")
    anomaly_count = snapshot.get("anomaly_count")
    if type(total_cycles) is not int or type(anomaly_count) is not int:
        return False
    # Exact keys, anomaly_count equality, and derived booleans are drift assertions.
    # total_cycles equality blocks truncation; one anomaly enforces one class.
    if anomaly_count != len(anomalies) or total_cycles != anomaly_count:
        return False
    return validate_witness_anomaly(anomalies[0])


def derive_physical_result(
    *,
    ordered_wal_projection_bytes: bytes,
    build_attempt_id: str,
    ordered_verifiers: Sequence[str],
    verify_result: VerifyResult | None = None,
) -> DerivedPhysicalResult:
    """Derive one issuable result bound to canonical ordered-WAL bytes."""

    if type(build_attempt_id) is not str or not build_attempt_id:
        _issuance_refused("build attempt identity is absent or invalid")
    if type(ordered_wal_projection_bytes) is not bytes:
        _issuance_refused("ordered WAL projection is not raw bytes")
    try:
        projection = _parse_canonical_object(
            ordered_wal_projection_bytes, label="ordered WAL projection"
        )
        projection = _exact_object(
            projection, _ORDERED_WAL_KEYS, label="ordered WAL projection"
        )
    except ResultEvidenceError:
        _issuance_refused("ordered WAL projection is not a canonical exact object")
    if projection["schema_version"] != "ordered-wal-projection/v1":
        _issuance_refused("ordered WAL projection schema is unsupported")
    if projection["build_attempt_id"] != build_attempt_id:
        _issuance_refused("ordered WAL projection belongs to a different build attempt")
    records = projection["records"]
    if type(records) is not list or not records:
        _issuance_refused("ordered WAL projection has no terminal record")
    if any(type(item) is not dict for item in records):
        _issuance_refused("ordered WAL projection records are not objects")
    if any(_projection_attempt_id(item) != build_attempt_id for item in records):
        _issuance_refused("ordered WAL projection mixes build attempts")
    terminal = records[-1]
    if set(terminal) != _PRODUCTION_WAL_RECORD_KEYS:
        _issuance_refused("terminal WAL record does not have the production envelope")
    payload = terminal.get("payload")
    if type(payload) is not dict:
        _issuance_refused("terminal WAL payload is not a production object")
    if payload.get("build_attempt_id") != build_attempt_id:
        _issuance_refused("terminal WAL belongs to a different build attempt")

    if isinstance(ordered_verifiers, (str, bytes)):
        _issuance_refused("ordered verifier policy is not a sequence of names")
    try:
        verifier_order = tuple(ordered_verifiers)
    except TypeError:
        _issuance_refused("ordered verifier policy is not iterable")
    if not verifier_order or any(
        type(item) is not str or not item for item in verifier_order
    ):
        _issuance_refused("ordered verifier policy is empty or invalid")
    ordered_wal_sha256 = _content_addressed_referent_sha256(
        ordered_wal_projection_bytes
    )

    if terminal.get("stage") == STAGE_COMMIT:
        verify_configs = payload.get("verify_configs")
        if type(verify_configs) is not list or tuple(verify_configs) != verifier_order:
            _issuance_refused("commit verifier order does not match the policy")
        if verify_result is not None:
            if type(verify_result) is not VerifyResult:
                _issuance_refused("accepted verifier result is not exact VerifyResult")
            try:
                accepted = (
                    verify_result.certified is True
                    and verify_result.verdict == "serializable"
                )
            except Exception:
                accepted = False
            if not accepted:
                _issuance_refused("commit contradicts the supplied verifier result")
        return DerivedPhysicalResult(
            build_attempt_id, "accepted", None, ordered_wal_sha256
        )

    if terminal.get("stage") != STAGE_ABORT:
        _issuance_refused("terminal WAL stage is neither commit nor abort")
    if type(verify_result) is not VerifyResult:
        _issuance_refused("rejected result requires an exact VerifyResult")
    try:
        rejected = (
            verify_result.verdict == "non-serializable"
            and verify_result.serializable is False
            and verify_result.certified is False
            and verify_result.integrity.clean() is True
        )
    except Exception:
        rejected = False
    if not rejected:
        _issuance_refused("verifier result is not a clean non-serializable result")
    if (
        type(verify_result.anomalies) is not list
        or type(verify_result.total_cycles) is not int
        or verify_result.total_cycles != len(verify_result.anomalies)
        or len(verify_result.anomalies) != 1
    ):
        _issuance_refused("verifier result does not contain exactly one full witness class")
    try:
        snapshot = result_to_dict(verify_result)
    except Exception:
        _issuance_refused("verifier result cannot be projected to the production wire shape")
    snapshot.pop("trace_dir", None)
    if not _valid_rejected_verify_snapshot(snapshot):
        _issuance_refused("verifier result does not satisfy the formal-consumer contract")
    if payload.get("reason") != verify_result.verdict:
        _issuance_refused("abort reason does not match the verifier verdict")
    try:
        snapshot_matches_terminal = (
            canonical_json_bytes(payload.get("verify"))
            == canonical_json_bytes(snapshot)
        )
    except ArtifactError:
        _issuance_refused("terminal verifier snapshot is not canonical JSON")
    if not snapshot_matches_terminal:
        _issuance_refused("terminal verifier snapshot differs from the typed result")
    return DerivedPhysicalResult(
        build_attempt_id,
        "rejected",
        witness_class_sha256(snapshot["anomalies"][0]),
        ordered_wal_sha256,
    )


def _reference(value: object, *, label: str) -> dict:
    ref = _exact_object(value, _REFERENCE_KEYS, label=label)
    path = _text(ref["path"], label=f"{label}.path")
    if "\\" in path:
        _fail(f"{label}.path must use POSIX separators")
    _sha256(ref["sha256"], label=f"{label}.sha256")
    return ref


def validate_result_evidence(record: object) -> dict:
    """Validate the exact nine-key ``result-evidence/v1`` schema."""

    root = _exact_object(record, _TOP_LEVEL_KEYS, label="result evidence")
    if root["schema_version"] != RESULT_EVIDENCE_SCHEMA_VERSION:
        _fail("unsupported result evidence schema_version")

    issuer = _exact_object(root["issuer"], frozenset({"kind"}), label="issuer")
    if issuer["kind"] != RESULT_EVIDENCE_ISSUER_KIND:
        _fail("unknown result evidence issuer kind")

    origin = _exact_object(
        root["origin_binding"], _ORIGIN_BINDING_KEYS, label="origin_binding"
    )
    for name in (
        "authority_blob_sha256",
        "source_closure_sha256",
        "axis_semantics_sha256",
        "verifier_policy_sha256",
        "environment_contract_sha256",
    ):
        _sha256(origin[name], label=f"origin_binding.{name}")
    for name in ("origin_id", "cell_key", "workload"):
        _text(origin[name], label=f"origin_binding.{name}")

    trial = _exact_object(
        root["trial_binding"], _TRIAL_BINDING_KEYS, label="trial_binding"
    )
    _sha256(
        trial["launch_admission_record_sha256"],
        label="trial_binding.launch_admission_record_sha256",
    )
    _text(trial["campaign_id"], label="trial_binding.campaign_id")
    _text(trial["workload"], label="trial_binding.workload")

    member = _exact_object(
        root["ledger_member"], _LEDGER_MEMBER_KEYS, label="ledger_member"
    )
    _text(member["batch_id"], label="ledger_member.batch_id")
    for name in ("iteration_index", "query_ordinal", "replicate_ordinal"):
        _ordinal(member[name], label=f"ledger_member.{name}")

    plan = _exact_object(root["p6_plan"], _P6_PLAN_KEYS, label="p6_plan")
    if plan["purpose"] not in ("source", "p6-validation"):
        _fail("p6_plan.purpose must be source or p6-validation")
    _sha256(plan["hypothesis_sha256"], label="p6_plan.hypothesis_sha256")
    _sha256(
        plan["validation_plan_sha256"], label="p6_plan.validation_plan_sha256"
    )

    trigger = _exact_object(
        root["trigger_binding"], _TRIGGER_BINDING_KEYS, label="trigger_binding"
    )
    mask = trigger["mask"]
    if type(mask) is not int or not 0 <= mask < 32:
        _fail("trigger_binding.mask must be an integer in [0, 31]")
    wire = _text(trigger["candidate_wire"], label="trigger_binding.candidate_wire")
    try:
        wire.encode("ascii")
    except UnicodeError as exc:
        raise ResultEvidenceError(
            "trigger_binding.candidate_wire must be ASCII"
        ) from exc
    _sha256(
        trigger["trigger_gate_binding_commitment"],
        label="trigger_binding.trigger_gate_binding_commitment",
    )

    physical = _exact_object(
        root["physical_result"], _PHYSICAL_RESULT_KEYS, label="physical_result"
    )
    _text(physical["build_attempt_id"], label="physical_result.build_attempt_id")
    outcome = physical["outcome"]
    if outcome not in ("accepted", "rejected"):
        _fail("physical_result.outcome must be accepted or rejected")
    constraint = physical["constraint_sha256"]
    if outcome == "accepted":
        if constraint is not None:
            _fail("accepted physical_result must not have a constraint_sha256")
    else:
        _sha256(constraint, label="physical_result.constraint_sha256")

    evidence = _exact_object(root["evidence"], _EVIDENCE_KEYS, label="evidence")
    _reference(evidence["ordered_wal_ref"], label="evidence.ordered_wal_ref")
    _reference(
        evidence["execution_provenance_ref"],
        label="evidence.execution_provenance_ref",
    )

    # Return a detached JSON value so later caller mutation cannot alter a
    # value already accepted by this validator.
    return json.loads(canonical_json_bytes(root).decode("utf-8"))


def assemble_result_evidence_record(
    *,
    origin_binding: Mapping,
    trial_binding: Mapping,
    ledger_member: Mapping,
    p6_plan: Mapping,
    trigger_binding: Mapping,
    derived: DerivedPhysicalResult,
    ordered_wal_ref: Mapping,
    execution_provenance_ref: Mapping,
) -> dict:
    """Assemble and validate the exact record around one derived result."""

    if type(derived) is not DerivedPhysicalResult:
        raise ResultEvidenceError("derived must be an exact DerivedPhysicalResult")
    ordered_ref = _reference(
        ordered_wal_ref, label="evidence.ordered_wal_ref"
    )
    if ordered_ref["sha256"] != derived.ordered_wal_sha256:
        raise ResultEvidenceError(
            "ordered WAL reference sha256 does not match the derived projection"
        )
    record = {
        "schema_version": RESULT_EVIDENCE_SCHEMA_VERSION,
        "issuer": {"kind": RESULT_EVIDENCE_ISSUER_KIND},
        "origin_binding": dict(origin_binding),
        "trial_binding": dict(trial_binding),
        "ledger_member": dict(ledger_member),
        "p6_plan": dict(p6_plan),
        "trigger_binding": dict(trigger_binding),
        "physical_result": {
            "build_attempt_id": derived.build_attempt_id,
            "outcome": derived.outcome,
            "constraint_sha256": derived.constraint_sha256,
        },
        "evidence": {
            "ordered_wal_ref": dict(ordered_ref),
            "execution_provenance_ref": dict(execution_provenance_ref),
        },
    }
    return validate_result_evidence(record)


def canonical_result_evidence_bytes(record: object) -> bytes:
    """Return sorted compact UTF-8 record bytes with no trailing LF."""

    return canonical_json_bytes(validate_result_evidence(record))


def parse_result_evidence_bytes(raw_bytes: bytes) -> dict:
    """Parse canonical bytes and validate the exact result-evidence schema."""

    try:
        value = strict_json_loads(raw_bytes)
    except ArtifactError as exc:
        raise ResultEvidenceError("result evidence bytes are not canonical JSON") from exc
    return validate_result_evidence(value)


def result_evidence_record_raw_sha256(raw_bytes: bytes) -> str:
    """Layer 1: sha256 of the complete canonical nine-key record bytes."""

    if type(raw_bytes) is not bytes:
        raise TypeError("record raw bytes must be bytes")
    parse_result_evidence_bytes(raw_bytes)
    record_raw_hasher = hashlib.new(_RECORD_RAW_SHA256_ALGORITHM)
    record_raw_hasher.update(raw_bytes)
    return record_raw_hasher.hexdigest()


def ledger_evidence_digest_sha256(raw_bytes: bytes) -> str:
    """Layer 2: independently compute ``EvidenceDigest.sha256``."""

    if type(raw_bytes) is not bytes:
        raise TypeError("ledger evidence bytes must be bytes")
    parse_result_evidence_bytes(raw_bytes)
    return hashlib.new(_LEDGER_EVIDENCE_DIGEST_ALGORITHM, raw_bytes).hexdigest()


def ledger_result_evidence_outer_commitment(
    *, result_evidence_salt: str, outcome: str, evidence_digest: ledger.EvidenceDigest
) -> str:
    """Layer 3: call the ledger's existing domain-separated salted mechanism."""

    normalized_salt = ledger._salt(
        result_evidence_salt, label="result evidence salt"
    )
    preimage = ledger._result_evidence_preimage(outcome, evidence_digest)
    return ledger._salted_commitment(normalized_salt, preimage)


def _safe_path_token(value: object, *, label: str) -> str:
    token = _text(value, label=label)
    if token in (".", "..") or "/" in token or "\\" in token:
        _fail(f"{label} is not a safe path token")
    return token


def result_evidence_relative_path(record: object) -> Path:
    """Return the deterministic §3.3 path for a validated record."""

    value = validate_result_evidence(record)
    origin = _safe_path_token(value["origin_binding"]["origin_id"], label="origin_id")
    batch = _safe_path_token(value["ledger_member"]["batch_id"], label="batch_id")
    query = value["ledger_member"]["query_ordinal"]
    return Path(
        "reports", "reflux-result-evidence", origin, batch, f"{query}.json"
    )


def _open_root_directory(root: Path) -> tuple[Path, int]:
    absolute = Path(os.path.abspath(Path(root)))
    _reject_symlink_components(absolute)
    try:
        info = os.lstat(absolute)
    except OSError as exc:
        raise ResultEvidenceError("evidence root cannot be inspected") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _fail("evidence root must be a real directory")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        return absolute, os.open(absolute, flags)
    except OSError as exc:
        raise ResultEvidenceError("evidence root cannot be opened safely") from exc


def _ensure_parent_directories(root: Path, relative_parent: Path) -> None:
    _absolute, current_fd = _open_root_directory(root)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        for component in relative_parent.parts:
            try:
                os.mkdir(component, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            try:
                next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            except OSError as exc:
                raise ResultEvidenceError(
                    "result evidence parent is not a real directory"
                ) from exc
            os.close(current_fd)
            current_fd = next_fd
    finally:
        os.close(current_fd)


def write_result_evidence_record(*, evidence_root: Path, record: object) -> Path:
    """Create the canonical record once at its deterministic confined path."""

    value = validate_result_evidence(record)
    relative = result_evidence_relative_path(value)
    _ensure_parent_directories(Path(evidence_root), relative.parent)
    try:
        return write_json_create_only(
            root=Path(evidence_root), relative_path=relative, value=value
        )
    except ArtifactError as exc:
        raise ResultEvidenceError("result evidence create-only write failed") from exc


def issue_result_evidence_record(
    *, evidence_root: Path, record: Mapping
) -> Path:
    """Resolve both claimed referents before the create-only record write."""

    value = validate_result_evidence(record)
    refs = value["evidence"]
    resolve_content_addressed_ref(
        evidence_root=Path(evidence_root), reference=refs["ordered_wal_ref"]
    )
    resolve_content_addressed_ref(
        evidence_root=Path(evidence_root),
        reference=refs["execution_provenance_ref"],
    )
    return write_result_evidence_record(evidence_root=Path(evidence_root), record=value)


def _context_mapping(value: object, *, label: str) -> dict:
    if not isinstance(value, Mapping):
        raise ResultEvidenceError(f"{label} must be a mapping")
    try:
        return dict(value)
    except (TypeError, ValueError) as exc:
        raise ResultEvidenceError(f"{label} cannot be copied") from exc


def _issued_context_capability(
    context: ResultEvidenceIssuanceContext,
) -> reflux_origin_binding.OriginBindingCapability:
    try:
        capability = reflux_origin_binding.assert_issued_origin_binding_capability(
            context.origin_capability
        )
    except reflux_origin_binding.OriginBindingError as exc:
        raise ResultEvidenceError(
            "result evidence context lacks an issued origin capability"
        ) from exc

    expected_origin_binding = {
        "authority_blob_sha256": capability.authority_blob_sha256,
        "source_closure_sha256": capability.source_closure_sha256,
        "origin_id": capability.origin_id,
        "cell_key": capability.cell_key,
        "workload": capability.trial_workload,
        "axis_semantics_sha256": capability.axis_semantics_sha256,
        "verifier_policy_sha256": capability.verifier_policy_sha256,
        "environment_contract_sha256": capability.environment_contract_sha256,
    }
    if _context_mapping(
        context.origin_binding, label="context.origin_binding"
    ) != expected_origin_binding:
        raise ResultEvidenceError(
            "context origin binding differs from the issued capability"
        )
    return capability


def _context_roots(
    *, layout: CampaignLayout | ExplorationCampaignLayout,
    context: ResultEvidenceIssuanceContext,
) -> tuple[Path, Path]:
    try:
        evidence_root = Path(os.path.abspath(context.evidence_root))
        physical_campaign_root = Path(os.path.abspath(layout.root))
    except (TypeError, ValueError) as exc:
        raise ResultEvidenceError("result evidence roots are not path-like") from exc

    evidence_fd = None
    campaign_fd = None
    try:
        _evidence_absolute, evidence_fd = _open_root_directory(evidence_root)
        _campaign_absolute, campaign_fd = _open_root_directory(
            physical_campaign_root
        )
    finally:
        if evidence_fd is not None:
            os.close(evidence_fd)
        if campaign_fd is not None:
            os.close(campaign_fd)
    if not physical_campaign_root.is_relative_to(evidence_root):
        raise ResultEvidenceError(
            "physical campaign root is outside the result evidence root"
        )
    return evidence_root, physical_campaign_root


def _trigger_binding_from_records(records: Sequence[dict]) -> dict:
    candidates = [
        record
        for record in records
        if record.get("stage") == trigger_gate_binding.WAL_RECORD_STAGE
    ]
    if len(candidates) != 1:
        _issuance_refused("ordered WAL does not contain one trigger binding")
    record = candidates[0]
    if set(record) != _PRODUCTION_WAL_RECORD_KEYS:
        _issuance_refused("trigger WAL record lacks the production envelope")
    if type(record["variant"]) is not str or type(record["env_tag"]) is not str:
        _issuance_refused("trigger WAL record identity fields are invalid")
    timestamp = record["ts"]
    if type(timestamp) not in (int, float) or (
        type(timestamp) is float and not math.isfinite(timestamp)
    ):
        _issuance_refused("trigger WAL record timestamp is invalid")
    payload = record["payload"]
    if type(payload) is not dict or set(payload) != {
        "build_attempt_id",
        wal_codec.TRIGGER_BINDING_PAYLOAD_KEY,
    }:
        _issuance_refused("trigger WAL payload is not exact")
    try:
        binding = trigger_gate_binding.validate_record(
            payload[wal_codec.TRIGGER_BINDING_PAYLOAD_KEY],
            require_source=False,
        )
    except trigger_gate_binding.TriggerGateBindingError:
        _issuance_refused("trigger WAL binding is invalid")
    return {
        "mask": binding.mask,
        "candidate_wire": encode_wire(TriggerGateIR(binding.mask)),
        wal_codec.TRIGGER_BINDING_COMMITMENT_KEY: (
            trigger_gate_binding.commitment(binding)
        ),
    }


def _content_relative_path(
    *,
    evidence_root: Path,
    physical_campaign_root: Path,
    category: str,
    digest: str,
    suffix: str,
) -> Path:
    absolute = physical_campaign_root.joinpath(
        "reports",
        "reflux-result-evidence-content",
        "v1",
        category,
        digest + suffix,
    )
    try:
        return absolute.relative_to(evidence_root)
    except ValueError as exc:
        raise ResultEvidenceError(
            "result evidence content path is outside the evidence root"
        ) from exc


def _write_result_evidence_content(
    *, evidence_root: Path, relative_path: Path, raw_bytes: bytes,
) -> Path:
    _ensure_parent_directories(evidence_root, relative_path.parent)
    try:
        return write_create_only(
            root=evidence_root,
            relative_path=relative_path,
            raw=raw_bytes,
        )
    except ArtifactError as exc:
        raise ResultEvidenceError(
            "result evidence content create-only write failed"
        ) from exc


def issue_campaign_result_evidence(
    *,
    layout: object,
    context: ResultEvidenceIssuanceContext,
    build_attempt_id: str,
    verify_result: object | None,
    campaign_run_identity: str,
    campaign_id: str,
    environment_contract: ExecutionEnvironmentContract,
    execution_receipt: object | None,
) -> Path:
    """Issue source, projection, provenance, and then the record create-only."""

    if type(context) is not ResultEvidenceIssuanceContext:
        raise ResultEvidenceError(
            "context must be an exact ResultEvidenceIssuanceContext"
        )
    if (
        type(layout) is not CampaignLayout
        and type(layout) is not ExplorationCampaignLayout
    ):
        raise ResultEvidenceError(
            "layout must be an exact CampaignLayout or ExplorationCampaignLayout"
        )
    if type(environment_contract) is not ExecutionEnvironmentContract:
        raise ResultEvidenceError(
            "environment_contract must be an exact "
            "ExecutionEnvironmentContract"
        )
    capability = _issued_context_capability(context)
    if campaign_id != capability.campaign_id:
        raise ResultEvidenceError("campaign id differs from the origin capability")
    contract_sha256 = environment_contract.contract_sha256
    if contract_sha256 != capability.environment_contract_sha256:
        _issuance_refused(
            "environment contract differs from the origin capability"
        )
    _campaign_identity(campaign_run_identity, label="campaign_run_identity")
    _sha256(contract_sha256, label="contract_sha256")
    if (
        context.env_tag != environment_contract.env_tag
        or context.attestation_mode != environment_contract.attestation_mode
    ):
        _issuance_refused(
            "issuance context environment fields differ from the "
            "environment contract"
        )
    if (
        environment_contract.attestation_mode == "required"
        and context.verified_calibration is None
    ):
        _issuance_refused(
            "required environment contract lacks verified calibration"
        )
    if not execution_guard.receipt_matches_contract(
        execution_receipt,
        env_tag=environment_contract.env_tag,
        contract_sha256=contract_sha256,
        attestation_mode=environment_contract.attestation_mode,
        verified_calibration=context.verified_calibration,
    ):
        _issuance_refused(
            "execution receipt is absent or does not match the environment contract"
        )
    if type(context.ordered_verifiers) is not tuple:
        raise ResultEvidenceError("context.ordered_verifiers must be an exact tuple")

    trial_binding = _context_mapping(
        context.trial_binding, label="context.trial_binding"
    )
    if (
        trial_binding.get("campaign_id") != campaign_id
        or trial_binding.get("workload") != capability.trial_workload
    ):
        raise ResultEvidenceError(
            "context trial binding differs from the issued capability"
        )
    origin_binding = _context_mapping(
        context.origin_binding, label="context.origin_binding"
    )
    p6_plan = _context_mapping(context.p6_plan, label="context.p6_plan")
    ledger_member = {
        "batch_id": context.batch_id,
        "iteration_index": context.iteration_index,
        "query_ordinal": context.query_ordinal,
        "replicate_ordinal": context.replicate_ordinal,
    }
    evidence_root, physical_campaign_root = _context_roots(
        layout=layout, context=context
    )

    # Obtain the terminal prefix once to determine its content address.  The
    # public projection producer independently confirms that the same prefix
    # still has this digest before any durable result-evidence write occurs.
    _frames, terminal_prefix_snapshot = _ordered_attempt_materials(
        layout=layout, build_attempt_id=build_attempt_id
    )
    source_sha256 = _content_addressed_referent_sha256(
        terminal_prefix_snapshot
    )
    source_relative = _content_relative_path(
        evidence_root=evidence_root,
        physical_campaign_root=physical_campaign_root,
        category="source-wal",
        digest=source_sha256,
        suffix=".jsonl",
    )
    source_ref = {
        "path": source_relative.as_posix(),
        "sha256": source_sha256,
    }
    projection_bytes = produce_ordered_wal_projection(
        layout=layout,
        build_attempt_id=build_attempt_id,
        source_wal_ref=source_ref,
    )
    projection_sha256 = _content_addressed_referent_sha256(projection_bytes)
    projection_relative = _content_relative_path(
        evidence_root=evidence_root,
        physical_campaign_root=physical_campaign_root,
        category="ordered-wal",
        digest=projection_sha256,
        suffix=".json",
    )
    projection_ref = {
        "path": projection_relative.as_posix(),
        "sha256": projection_sha256,
    }

    records = _parse_canonical_object(
        projection_bytes, label="ordered WAL projection"
    )["records"]
    trigger_binding = _trigger_binding_from_records(records)
    derived = derive_physical_result(
        ordered_wal_projection_bytes=projection_bytes,
        build_attempt_id=build_attempt_id,
        ordered_verifiers=context.ordered_verifiers,
        verify_result=verify_result,
    )

    if type(execution_receipt) is not dict:
        raise ResultEvidenceError("execution receipt must be an exact object")
    if execution_receipt.get("contract_sha256") != contract_sha256:
        raise ResultEvidenceError(
            "execution receipt does not bind the environment contract"
        )
    try:
        execution_receipt_bytes = canonical_json_bytes(execution_receipt)
    except ArtifactError as exc:
        raise ResultEvidenceError("execution receipt is not canonical JSON") from exc
    provenance = _validate_execution_provenance({
        "schema_version": "execution-provenance/v2",
        "build_attempt_id": build_attempt_id,
        "campaign_id": campaign_id,
        "workload": capability.trial_workload,
        "contract_sha256": contract_sha256,
        "trigger_binding": trigger_binding,
        "execution_receipt_sha256": _content_addressed_referent_sha256(
            execution_receipt_bytes
        ),
        "campaign_run_identity": campaign_run_identity,
    })
    provenance_bytes = canonical_json_bytes(provenance)
    provenance_sha256 = _content_addressed_referent_sha256(provenance_bytes)
    provenance_relative = _content_relative_path(
        evidence_root=evidence_root,
        physical_campaign_root=physical_campaign_root,
        category="execution-provenance",
        digest=provenance_sha256,
        suffix=".json",
    )
    provenance_ref = {
        "path": provenance_relative.as_posix(),
        "sha256": provenance_sha256,
    }

    # Derivation and complete record assembly are memory-only gates.  No
    # result-evidence directory or file exists before both have succeeded.
    record = assemble_result_evidence_record(
        origin_binding=origin_binding,
        trial_binding=trial_binding,
        ledger_member=ledger_member,
        p6_plan=p6_plan,
        trigger_binding=trigger_binding,
        derived=derived,
        ordered_wal_ref=projection_ref,
        execution_provenance_ref=provenance_ref,
    )
    expected_record_path = _text(
        context.expected_record_path, label="context.expected_record_path"
    )
    actual_record_relative = result_evidence_relative_path(record)
    if expected_record_path != actual_record_relative.as_posix():
        raise ResultEvidenceError(
            "result evidence record path differs from the issuance context"
        )

    _write_result_evidence_content(
        evidence_root=evidence_root,
        relative_path=source_relative,
        raw_bytes=terminal_prefix_snapshot,
    )
    _write_result_evidence_content(
        evidence_root=evidence_root,
        relative_path=projection_relative,
        raw_bytes=projection_bytes,
    )
    _write_result_evidence_content(
        evidence_root=evidence_root,
        relative_path=provenance_relative,
        raw_bytes=provenance_bytes,
    )
    return issue_result_evidence_record(
        evidence_root=evidence_root,
        record=record,
    )


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise ResultEvidenceError("evidence path component does not exist") from exc
        if stat.S_ISLNK(info.st_mode):
            _fail("evidence path has a symlink component")


def _normalized_reference_target(root: Path, claimed_path: str) -> tuple[Path, Path]:
    if PurePosixPath(claimed_path).is_absolute():
        _fail("evidence reference must be relative to the evidence root")
    normalized_text = posixpath.normpath(claimed_path)
    if normalized_text in ("", ".", "..") or normalized_text.startswith("../"):
        _fail("evidence reference escapes the evidence root")
    normalized = PurePosixPath(normalized_text)

    absolute_root = Path(os.path.abspath(Path(root)))
    _reject_symlink_components(absolute_root)
    target = absolute_root.joinpath(*normalized.parts)
    if not target.is_relative_to(absolute_root) or target == absolute_root:
        _fail("evidence reference escapes the evidence root")
    _reject_symlink_components(target)
    return absolute_root, target


def _read_regular_file_no_follow(path: Path) -> tuple[bytes, tuple[int, int]]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        _fail("O_NOFOLLOW is required for evidence resolution")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ResultEvidenceError("evidence referent cannot be opened safely") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            _fail("evidence referent must be a regular file")
        identity = (info.st_dev, info.st_ino)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError as exc:
        raise ResultEvidenceError("evidence referent read failed") from exc
    finally:
        os.close(fd)
    try:
        final_info = os.lstat(path)
    except OSError as exc:
        raise ResultEvidenceError("evidence referent changed during resolution") from exc
    if stat.S_ISLNK(final_info.st_mode) or (
        final_info.st_dev, final_info.st_ino
    ) != identity:
        _fail("evidence referent identity changed during resolution")
    return b"".join(chunks), identity


def _content_addressed_referent_sha256(raw_bytes: bytes) -> str:
    content_hasher = hashlib.sha256()
    content_hasher.update(raw_bytes)
    return content_hasher.hexdigest()


def resolve_content_addressed_ref(
    *, evidence_root: Path, reference: object
) -> ResolvedEvidenceBytes:
    """Resolve only the claimed confined path and reject a digest mismatch.

    This establishes byte equality with the record's claim, not correspondence
    with a physical execution.
    """

    ref = _reference(reference, label="evidence reference")
    _root, target = _normalized_reference_target(
        Path(evidence_root), ref["path"]
    )
    raw_bytes, identity = _read_regular_file_no_follow(target)
    observed = _content_addressed_referent_sha256(raw_bytes)
    if observed != ref["sha256"]:
        _fail("evidence referent sha256 mismatch")
    return ResolvedEvidenceBytes(
        claimed_path=ref["path"],
        normalized_path=target,
        identity=identity,
        sha256=observed,
        raw_bytes=raw_bytes,
    )


def _parse_canonical_object(raw_bytes: bytes, *, label: str) -> dict:
    try:
        value = strict_json_loads(raw_bytes)
    except ArtifactError as exc:
        raise ResultEvidenceError(f"{label} is not canonical JSON") from exc
    if type(value) is not dict:
        _fail(f"{label} must be an object")
    return value


def _validate_execution_provenance(value: object) -> dict:
    provenance = _exact_object(
        value, _EXECUTION_PROVENANCE_V2_KEYS, label="execution provenance"
    )
    if provenance["schema_version"] != "execution-provenance/v2":
        _fail("unsupported execution provenance schema_version")
    for name in ("build_attempt_id", "campaign_id", "workload"):
        _text(provenance[name], label=f"execution provenance.{name}")
    _campaign_identity(
        provenance["campaign_run_identity"],
        label="execution provenance.campaign_run_identity",
    )
    _sha256(
        provenance["contract_sha256"],
        label="execution provenance.contract_sha256",
    )
    trigger = _exact_object(
        provenance["trigger_binding"],
        _TRIGGER_BINDING_KEYS,
        label="execution provenance.trigger_binding",
    )
    mask = trigger["mask"]
    if type(mask) is not int or not 0 <= mask < 32:
        _fail(
            "execution provenance.trigger_binding.mask must be an integer in [0, 31]"
        )
    wire = _text(
        trigger["candidate_wire"],
        label="execution provenance.trigger_binding.candidate_wire",
    )
    try:
        wire.encode("ascii")
    except UnicodeError as exc:
        raise ResultEvidenceError(
            "execution provenance.trigger_binding.candidate_wire must be ASCII"
        ) from exc
    _sha256(
        trigger["trigger_gate_binding_commitment"],
        label="execution provenance.trigger_binding.trigger_gate_binding_commitment",
    )
    _sha256(
        provenance["execution_receipt_sha256"],
        label="execution provenance.execution_receipt_sha256",
    )
    return json.loads(canonical_json_bytes(provenance).decode("utf-8"))


def _projection_attempt_id(record: dict) -> object:
    if "build_attempt_id" in record:
        return record["build_attempt_id"]
    payload = record.get("payload")
    return payload.get("build_attempt_id") if type(payload) is dict else None


def _canonical_wal_interval(raw_interval: bytes) -> bytes:
    try:
        value = strict_json_loads(raw_interval)
    except ArtifactError:
        value = None
    if type(value) is list:
        return canonical_json_bytes(value)

    if not raw_interval or not raw_interval.endswith(b"\n"):
        _fail("source WAL interval is neither a canonical list nor complete frames")
    projected: list[dict] = []
    for frame in raw_interval.splitlines(keepends=True):
        if not frame.endswith(b"\n"):
            _fail("source WAL interval contains an incomplete frame")
        try:
            record = wal_codec.parse_line(frame.decode("utf-8"))
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ResultEvidenceError("source WAL interval has an invalid frame") from exc
        projected.append({
            "variant": record.variant,
            "stage": record.stage,
            "env_tag": record.env_tag,
            "ts": record.ts,
            "payload": record.payload,
        })
    return canonical_json_bytes(projected)


def _resolve_ordered_wal(
    *, evidence_root: Path, projection_ref: ResolvedEvidenceBytes
) -> ResolvedOrderedWal:
    projection = _parse_canonical_object(
        projection_ref.raw_bytes, label="ordered WAL projection"
    )
    projection = _exact_object(
        projection, _ORDERED_WAL_KEYS, label="ordered WAL projection"
    )
    if projection["schema_version"] != "ordered-wal-projection/v1":
        _fail("unsupported ordered WAL projection schema_version")
    source_ref = resolve_content_addressed_ref(
        evidence_root=evidence_root,
        reference=_reference(
            projection["source_wal_ref"],
            label="ordered WAL projection.source_wal_ref",
        ),
    )
    byte_start = _ordinal(projection["byte_start"], label="byte_start")
    byte_end = _ordinal(projection["byte_end"], label="byte_end")
    if byte_end <= byte_start or byte_end > len(source_ref.raw_bytes):
        _fail("ordered WAL projection byte range is invalid")
    attempt = _text(projection["build_attempt_id"], label="build_attempt_id")
    records = projection["records"]
    if type(records) is not list or not records:
        _fail("ordered WAL projection.records must be a non-empty list")
    if any(type(item) is not dict for item in records):
        _fail("ordered WAL projection.records must contain objects")
    if any(_projection_attempt_id(item) != attempt for item in records):
        _fail("ordered WAL projection mixes build attempts")

    source_interval = source_ref.raw_bytes[byte_start:byte_end]
    if _canonical_wal_interval(source_interval) != canonical_json_bytes(records):
        _fail("ordered WAL projection records do not match source WAL bytes")
    return ResolvedOrderedWal(
        projection_ref=projection_ref,
        source_wal_ref=source_ref,
        byte_start=byte_start,
        byte_end=byte_end,
        build_attempt_id=attempt,
        records=tuple(records),
    )


def resolve_result_evidence(
    record: object, *, evidence_root: Path
) -> ResolvedResultEvidence:
    """Resolve one record and pass downstream only digest-matching bytes."""

    value = validate_result_evidence(record)
    raw_record = canonical_result_evidence_bytes(value)
    evidence = value["evidence"]
    projection_ref = resolve_content_addressed_ref(
        evidence_root=evidence_root, reference=evidence["ordered_wal_ref"]
    )
    ordered_wal = _resolve_ordered_wal(
        evidence_root=Path(evidence_root), projection_ref=projection_ref
    )
    if ordered_wal.build_attempt_id != value["physical_result"]["build_attempt_id"]:
        _fail("ordered WAL attempt does not match physical_result")
    provenance_ref = resolve_content_addressed_ref(
        evidence_root=evidence_root,
        reference=evidence["execution_provenance_ref"],
    )
    provenance = _validate_execution_provenance(
        _parse_canonical_object(
            provenance_ref.raw_bytes, label="execution provenance"
        )
    )
    return ResolvedResultEvidence(
        record=value,
        record_bytes=raw_record,
        ordered_wal=ordered_wal,
        execution_provenance_ref=provenance_ref,
        execution_provenance=provenance,
    )


def assert_non_overlapping_wal_ranges(
    resolved_records: Sequence[ResolvedResultEvidence],
) -> None:
    """Reject overlap after path aliases have collapsed to file identity."""

    intervals: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for item in resolved_records:
        if type(item) is not ResolvedResultEvidence:
            raise TypeError("resolved_records must contain exact resolved evidence")
        wal = item.ordered_wal
        intervals.setdefault(wal.source_wal_ref.identity, []).append(
            (wal.byte_start, wal.byte_end)
        )
    for ranges in intervals.values():
        ranges.sort()
        for previous, current in zip(ranges, ranges[1:]):
            if current[0] < previous[1]:
                _fail("ordered WAL byte ranges overlap")


def resolve_result_evidence_batch(
    records: Sequence[object], *, evidence_root: Path
) -> tuple[ResolvedResultEvidence, ...]:
    """Resolve a batch and enforce source-WAL range non-overlap."""

    resolved = tuple(
        resolve_result_evidence(record, evidence_root=evidence_root)
        for record in records
    )
    assert_non_overlapping_wal_ranges(resolved)
    return resolved


def _member_inputs(record: object, raw_bytes: bytes | None) -> tuple[dict, bytes]:
    value = validate_result_evidence(record)
    canonical = canonical_result_evidence_bytes(value)
    if raw_bytes is not None:
        if type(raw_bytes) is not bytes or raw_bytes != canonical:
            _fail("member mapping raw bytes do not equal the canonical record")
        raw = raw_bytes
    else:
        raw = canonical
    return value, raw


def map_result_evidence_to_opened_member(
    record: object,
    *,
    candidate_salt: str,
    result_evidence_salt: str,
    constraint_salt: str,
    raw_bytes: bytes | None = None,
) -> ledger.OpenedBatchMember:
    """Map exactly the §3.5 fields present on ``OpenedBatchMember``."""

    value, raw = _member_inputs(record, raw_bytes)
    member = value["ledger_member"]
    physical = value["physical_result"]
    candidate = value["trigger_binding"]["candidate_wire"].encode("ascii")
    return ledger.OpenedBatchMember(
        query_ordinal=member["query_ordinal"],
        replicate_ordinal=member["replicate_ordinal"],
        candidate_salt=ledger._salt(candidate_salt, label="candidate salt"),
        candidate_bytes=candidate,
        result_evidence_salt=ledger._salt(
            result_evidence_salt, label="result evidence salt"
        ),
        outcome=physical["outcome"],
        evidence_digest=ledger.EvidenceDigest(
            ledger_evidence_digest_sha256(raw)
        ),
        constraint_salt=ledger._salt(constraint_salt, label="constraint salt"),
        constraint_sha256=physical["constraint_sha256"],
    )


def map_result_evidence_to_sealed_member(
    record: object, *, raw_bytes: bytes | None = None
) -> ledger.SealedBatchMember:
    """Map exactly the §3.5 fields present on ``SealedBatchMember``."""

    value, raw = _member_inputs(record, raw_bytes)
    member = value["ledger_member"]
    physical = value["physical_result"]
    return ledger.SealedBatchMember(
        query_ordinal=member["query_ordinal"],
        replicate_ordinal=member["replicate_ordinal"],
        candidate_bytes=value["trigger_binding"]["candidate_wire"].encode("ascii"),
        outcome=physical["outcome"],
        evidence_digest=ledger.EvidenceDigest(
            ledger_evidence_digest_sha256(raw)
        ),
        constraint_sha256=physical["constraint_sha256"],
    )


def map_absent_result_to_opened_tombstone(
    *,
    query_ordinal: int,
    replicate_ordinal: int,
    candidate_bytes: bytes,
    candidate_salt: str,
    result_evidence_salt: str,
    constraint_salt: str,
) -> ledger.OpenedBatchMember:
    """Represent record absence without inventing evidence fields."""

    if type(candidate_bytes) is not bytes:
        raise TypeError("candidate_bytes must be exact bytes")
    return ledger.OpenedBatchMember(
        query_ordinal=_ordinal(query_ordinal, label="query_ordinal"),
        replicate_ordinal=_ordinal(replicate_ordinal, label="replicate_ordinal"),
        candidate_salt=ledger._salt(candidate_salt, label="candidate salt"),
        candidate_bytes=candidate_bytes,
        result_evidence_salt=ledger._salt(
            result_evidence_salt, label="result evidence salt"
        ),
        outcome="tombstoned",
        evidence_digest=None,
        constraint_salt=ledger._salt(constraint_salt, label="constraint salt"),
        constraint_sha256=None,
    )


def map_absent_result_to_sealed_tombstone(
    *, query_ordinal: int, replicate_ordinal: int, candidate_bytes: bytes
) -> ledger.SealedBatchMember:
    """Map record absence to the sealed tombstone row from §3.5."""

    if type(candidate_bytes) is not bytes:
        raise TypeError("candidate_bytes must be exact bytes")
    return ledger.SealedBatchMember(
        query_ordinal=_ordinal(query_ordinal, label="query_ordinal"),
        replicate_ordinal=_ordinal(replicate_ordinal, label="replicate_ordinal"),
        candidate_bytes=candidate_bytes,
        outcome="tombstoned",
        evidence_digest=None,
        constraint_sha256=None,
    )
