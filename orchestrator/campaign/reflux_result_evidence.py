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
import os
import posixpath
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

from . import reflux_origin_ledger as ledger
from . import wal as wal_codec
from .layout import validate_campaign_id
from .reflux_origin_artifacts import (
    ArtifactError,
    canonical_json_bytes,
    strict_json_loads,
    write_json_create_only,
)


__all__ = [
    "RESULT_EVIDENCE_SCHEMA_VERSION",
    "RECORD_RAW_SHA256_LAYER",
    "LEDGER_EVIDENCE_DIGEST_LAYER",
    "LEDGER_OUTER_COMMITMENT_LAYER",
    "ResultEvidenceError",
    "ResolvedEvidenceBytes",
    "ResolvedOrderedWal",
    "ResolvedResultEvidence",
    "validate_result_evidence",
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


class ResultEvidenceError(ValueError):
    """Fail-closed rejection of result evidence or one of its referents."""


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
