"""Fail-closed issuance validation for ``source-closure/v1`` records.

The four referent preimages are read from the captured Git commit.  Working-tree
bytes and live producer output are deliberately outside this trust boundary.
Axis and verifier artifacts have no production fallback: if either blob is
absent, validation stops.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping

from .axis_trigger_gating import GATEABLE_REASONS
from .env_contract import resolve_by_contract_sha256
from .reflux_ir import TriggerGateIR, emit_predicate, encode_wire
from .reflux_origin_artifacts import (
    ArtifactError,
    strict_json_loads,
)
from .reflux_origin_ledger import (
    AUTHORITY_RELATIVE_PATH,
    AuthorityManifest,
    _manifest_from_object,
    derive_cell_key,
    derive_origin_id,
)
from .s8b_descriptor import (
    DescriptorError,
    canonical_descriptor_bytes,
    validate_descriptor,
)


__all__ = [
    "SOURCE_CLOSURE_SCHEMA_ID",
    "SourceClosureError",
    "ValidatedSourceClosure",
    "assert_issued_validated_source_closure",
    "validate_source_closure",
]


SOURCE_CLOSURE_SCHEMA_ID = "source-closure/v1"

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_OID_RE = re.compile(r"[0-9a-f]{40}\Z")
_TOP_LEVEL_KEYS = frozenset({
    "schema_version",
    "captured_commit_oid",
    "authority_series_id",
    "origin_id",
    "cell_key",
    "referents",
})
_REFERENT_KEYS = (
    "authority.workload.descriptor_sha256",
    "axis_semantics_sha256",
    "verifier_policy_sha256",
    "environment_contract_sha256",
)
_REFERENT_VALUE_KEYS = frozenset({
    "preimage_ref", "digest_rule", "producer_field", "runtime_field_paths",
})
_PREIMAGE_REF_KEYS = frozenset({"path", "sha256"})
_DIGEST_RULE = "raw-git-blob-sha256"
_PRODUCER_FIELDS = {
    name: name for name in _REFERENT_KEYS
}
_RUNTIME_FIELD_PATHS = {
    "authority.workload.descriptor_sha256": (
        "report.cells[*].descriptor",
        "report.cells[*].descriptor_binding.output_sha256",
    ),
    "axis_semantics_sha256": (
        "wal.TriggerGateBinding.mask",
        "wal.TriggerGateBinding.predicate_sha256",
        "wal.TriggerGateBinding.source",
    ),
    "verifier_policy_sha256": (
        "wal.commit.payload.verify_configs",
        "wal.abort.payload.verify.anomalies",
    ),
    "environment_contract_sha256": (
        "execution_provenance.contract_sha256",
    ),
}
_EXPECTED_REASONS = (
    "lock-conflict",
    "update-absent",
    "readvali-tid",
    "readvali-locked",
    "node-vali",
)
_APPROVAL_KEYS = frozenset({
    "authority_blob_sha256", "origin_id", "cell_key", "source_closure_sha256",
})
_ISSUER_SEAL = object()


class SourceClosureError(ValueError):
    """A source closure could not be issued without weakening a gate."""


def _reject(message: str) -> None:
    raise SourceClosureError(message)


def _exact_mapping(value: object, keys: frozenset[str], *, label: str) -> Mapping:
    if type(value) is not dict or frozenset(value) != keys:
        _reject(f"[{label}] exact key set mismatch")
    return value


def _sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _reject(f"[{label}] expected lowercase SHA-256")
    return value


def _token(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        _reject(f"[{label}] expected non-empty string")
    return value


def _git(repo_root: Path, arguments: tuple[str, ...], *, absent: bool = False) -> bytes:
    try:
        completed = subprocess.run(
            ("git", "-C", str(repo_root), *arguments),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, ValueError) as exc:
        raise SourceClosureError("[git] cannot execute Git") from exc
    if completed.returncode != 0:
        if absent:
            # Mutation M-CLOSURE-ARTIFACT-ABSENT targets this fail-closed edge.
            raise SourceClosureError("[artifact-absent] referent blob is absent")
        _reject("[git] captured commit or authority blob is unavailable")
    return completed.stdout


def _resolve_commit_once(repo_root: Path, captured: object) -> str:
    if type(captured) is not str or _OID_RE.fullmatch(captured) is None:
        _reject("[captured-commit] expected a full lowercase commit OID")
    raw = _git(repo_root, ("rev-parse", "--verify", f"{captured}^{{commit}}"))
    try:
        resolved = raw.decode("ascii").rstrip("\n")
    except UnicodeDecodeError as exc:
        raise SourceClosureError("[captured-commit] Git returned a non-ASCII OID") from exc
    if _OID_RE.fullmatch(resolved) is None or resolved != captured:
        _reject("[captured-commit] OID did not resolve to that full commit")
    return resolved


def _git_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        _reject("[referent-schema] invalid Git path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.endswith("/")
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        _reject("[referent-schema] Git path is not confined")
    return value


def _check_pre_authority(repo_root: Path, commit_oid: str, record: Mapping) -> None:
    raw = _git(
        repo_root,
        ("cat-file", "blob", f"{commit_oid}:{AUTHORITY_RELATIVE_PATH}"),
    )
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        _reject("[self-reference] captured authority encoding is invalid")
    try:
        document = strict_json_loads(raw[:-1])
    except ArtifactError as exc:
        raise SourceClosureError("[self-reference] captured authority is invalid") from exc
    authority = _exact_mapping(
        document, frozenset({"authority_schema", "origins"}), label="self-reference"
    )
    if authority["authority_schema"] != "izanagi-reflux-origin-authority/v2":
        _reject("[self-reference] captured authority schema is unsupported")
    origins = authority["origins"]
    if type(origins) is not list:
        _reject("[self-reference] captured authority origins must be a list")
    for entry_value in origins:
        entry = _exact_mapping(
            entry_value,
            frozenset({"cell_key", "manifest", "origin_id"}),
            label="self-reference",
        )
        _sha256(entry["origin_id"], label="self-reference")
        _sha256(entry["cell_key"], label="self-reference")
        if type(entry["manifest"]) is not dict:
            _reject("[self-reference] captured authority manifest is invalid")
        if entry["origin_id"] == record["origin_id"] or entry["cell_key"] == record["cell_key"]:
            _reject("[self-reference] captured commit already contains the new authority entry")


def _parse_record(raw_record: bytes) -> Mapping:
    if type(raw_record) is not bytes:
        _reject("[record-schema] source closure must be immutable raw bytes")
    try:
        value = strict_json_loads(raw_record)
    except ArtifactError as exc:
        raise SourceClosureError("[record-schema] source closure is not canonical JSON") from exc
    record = _exact_mapping(value, _TOP_LEVEL_KEYS, label="record-schema")
    if record["schema_version"] != SOURCE_CLOSURE_SCHEMA_ID:
        _reject("[record-schema] unsupported source closure schema")
    _token(record["authority_series_id"], label="record-schema")
    _sha256(record["origin_id"], label="record-schema")
    _sha256(record["cell_key"], label="record-schema")
    referents = _exact_mapping(
        record["referents"], frozenset(_REFERENT_KEYS), label="referent-schema"
    )
    for name in _REFERENT_KEYS:
        item = _exact_mapping(referents[name], _REFERENT_VALUE_KEYS, label="referent-schema")
        reference = _exact_mapping(
            item["preimage_ref"], _PREIMAGE_REF_KEYS, label="referent-schema"
        )
        _git_path(reference["path"])
        _sha256(reference["sha256"], label="referent-schema")
        if item["digest_rule"] != _DIGEST_RULE:
            _reject("[referent-schema] unsupported digest rule")
        if item["producer_field"] != _PRODUCER_FIELDS[name]:
            _reject("[referent-schema] producer field mismatch")
        paths = item["runtime_field_paths"]
        if type(paths) is not list or tuple(paths) != _RUNTIME_FIELD_PATHS[name]:
            _reject("[referent-schema] runtime field paths mismatch")
    return record


def _typed_manifest(value: object) -> AuthorityManifest:
    if type(value) is AuthorityManifest:
        return value
    try:
        return _manifest_from_object(value)
    except Exception as exc:
        raise SourceClosureError("[manifest] authority manifest is invalid") from exc


def _manifest_digest(manifest: AuthorityManifest, referent: str) -> str:
    if referent == "authority.workload.descriptor_sha256":
        return str(manifest.workload["descriptor_sha256"])
    return str(getattr(manifest, referent))


def _load_referents(
    repo_root: Path,
    commit_oid: str,
    record: Mapping,
    manifest: AuthorityManifest,
) -> dict[str, bytes]:
    blobs: dict[str, bytes] = {}
    for name in _REFERENT_KEYS:
        reference = record["referents"][name]["preimage_ref"]
        raw = _git(
            repo_root,
            ("cat-file", "blob", f"{commit_oid}:{reference['path']}"),
            absent=True,
        )
        digest = hashlib.sha256(raw).hexdigest()
        if digest != reference["sha256"]:
            _reject("[referent-digest] raw Git blob differs from closure record")
        if digest != _manifest_digest(manifest, name):
            _reject("[referent-digest] raw Git blob differs from authority manifest")
        blobs[name] = raw
    return blobs


def _validate_workload(raw: bytes, report_cell: object, manifest: AuthorityManifest) -> None:
    try:
        descriptor = strict_json_loads(raw)
        canonical = canonical_descriptor_bytes(descriptor)
    except (ArtifactError, DescriptorError) as exc:
        raise SourceClosureError("[workload] descriptor is not strict canonical JSON") from exc
    if canonical != raw or type(descriptor) is not dict:
        _reject("[workload] canonical descriptor bytes differ from Git blob")

    schema = descriptor.get("schema_version")
    if schema == "8b-v1":
        try:
            validate_descriptor(descriptor)
        except DescriptorError as exc:
            raise SourceClosureError("[workload] 8b descriptor schema is invalid") from exc
        scale = descriptor["scale"]
        records, threads = scale["records"], scale["threads"]
    elif schema == "izanagi-workload-descriptor/v1":
        if frozenset(descriptor) != frozenset({
            "schema_version", "records", "threads", "workload", "ycsb_rratio",
        }):
            _reject("[workload] fixture projection has an open schema")
        records, threads = descriptor["records"], descriptor["threads"]
        if (
            type(records) is not int or records < 1
            or type(threads) is not int or threads < 1
            or type(descriptor["workload"]) is not str or not descriptor["workload"]
            or type(descriptor["ycsb_rratio"]) is not int
        ):
            _reject("[workload] fixture projection value is invalid")
    else:
        _reject("[workload] unsupported descriptor projection")

    cell = report_cell if type(report_cell) is dict else None
    binding = cell.get("descriptor_binding") if cell is not None else None
    if cell is None or type(binding) is not dict:
        _reject("[workload] report cell descriptor binding is absent")
    expected_digest = str(manifest.workload["descriptor_sha256"])
    if cell.get("descriptor") != descriptor:
        _reject("[workload] report cell descriptor differs from Git blob")
    if binding.get("output_sha256") != expected_digest:
        _reject("[workload] report descriptor digest differs from authority")
    if records != manifest.workload["records"] or threads != manifest.workload["threads"]:
        _reject("[workload] descriptor scale differs from authority")


def _validate_axis(raw: bytes) -> None:
    try:
        value = strict_json_loads(raw)
    except ArtifactError as exc:
        raise SourceClosureError("[axis] artifact is not strict canonical JSON") from exc
    axis = _exact_mapping(
        value,
        frozenset({"schema_version", "marker", "reasons", "wire", "sentinel"}),
        label="axis",
    )
    wire = _exact_mapping(
        axis["wire"], frozenset({"width", "bit_order", "masks"}), label="axis"
    )
    if (
        axis["schema_version"] != "izanagi-axis-semantics/v1"
        or axis["marker"] != "trigger-gating"
        or type(axis["reasons"]) is not list
        or tuple(axis["reasons"]) != _EXPECTED_REASONS
        or wire != {"width": 5, "bit_order": "lsb-first", "masks": [0, 31]}
        or axis["sentinel"] != "kUnset"
    ):
        _reject("[axis] artifact semantics mismatch")

    if tuple(GATEABLE_REASONS) != _EXPECTED_REASONS:
        _reject("[axis] implementation reason order does not conform")
    for mask in range(32):
        expected = "".join("1" if mask & (1 << bit) else "0" for bit in range(5))
        ir = TriggerGateIR(mask=mask)
        if encode_wire(ir) != expected:
            _reject("[axis] implementation wire does not conform")
        if "IzanagiAbortReason::kUnset" not in emit_predicate(ir):
            _reject("[axis] implementation sentinel does not conform")


def _validate_verifier(raw: bytes) -> None:
    try:
        value = strict_json_loads(raw)
    except ArtifactError as exc:
        raise SourceClosureError("[verifier] artifact is not strict canonical JSON") from exc
    policy = _exact_mapping(
        value,
        frozenset({
            "schema_version",
            "ordered_passes",
            "accepted",
            "candidate_attributable_rejected",
            "fail_closed",
            "witness_class_cardinality",
        }),
        label="verifier",
    )
    if (
        policy["schema_version"] != "izanagi-verifier-policy/v1"
        or type(policy["ordered_passes"]) is not list
        or policy["ordered_passes"] != ["legacy", "s2"]
        or policy["accepted"] != "all-passes-complete"
        or policy["candidate_attributable_rejected"]
        != "single-normalized-witness-class"
        or policy["fail_closed"] is not True
        or type(policy["witness_class_cardinality"]) is not int
        or policy["witness_class_cardinality"] != 1
    ):
        _reject("[verifier] artifact policy mismatch")


def _validate_approval(
    receipt: object,
    *,
    authority_blob_sha256: str,
    record: Mapping,
    source_closure_sha256: str,
) -> None:
    approval = _exact_mapping(receipt, _APPROVAL_KEYS, label="approval-receipt")
    expected = {
        "authority_blob_sha256": _sha256(
            authority_blob_sha256, label="approval-receipt"
        ),
        "origin_id": record["origin_id"],
        "cell_key": record["cell_key"],
        "source_closure_sha256": source_closure_sha256,
    }
    if approval != expected:
        _reject("[approval-receipt] receipt binding mismatch")


@dataclass(frozen=True, slots=True, init=False)
class ValidatedSourceClosure:
    """Issuer-bound result of all source-closure issuance checks."""

    source_closure_sha256: str
    captured_commit_oid: str
    authority_series_id: str
    origin_id: str
    cell_key: str
    referent_sha256s: Mapping[str, str]
    _record_bytes: bytes
    _seal: object

    def __init__(
        self,
        *,
        source_closure_sha256: str,
        captured_commit_oid: str,
        authority_series_id: str,
        origin_id: str,
        cell_key: str,
        referent_sha256s: Mapping[str, str],
        record_bytes: bytes,
        _issuer: object = None,
    ) -> None:
        if _issuer is not _ISSUER_SEAL:
            raise TypeError("ValidatedSourceClosure values are issuer-only")
        object.__setattr__(self, "source_closure_sha256", source_closure_sha256)
        object.__setattr__(self, "captured_commit_oid", captured_commit_oid)
        object.__setattr__(self, "authority_series_id", authority_series_id)
        object.__setattr__(self, "origin_id", origin_id)
        object.__setattr__(self, "cell_key", cell_key)
        object.__setattr__(self, "referent_sha256s", MappingProxyType(dict(referent_sha256s)))
        object.__setattr__(self, "_record_bytes", record_bytes)
        object.__setattr__(self, "_seal", _ISSUER_SEAL)


def assert_issued_validated_source_closure(value: object) -> ValidatedSourceClosure:
    """Reject forged or post-issuance modified closure values."""

    if type(value) is not ValidatedSourceClosure or value._seal is not _ISSUER_SEAL:
        _reject("[issued-value] source closure was not issued by this module")
    digest = hashlib.sha256(value._record_bytes).hexdigest()
    if digest != value.source_closure_sha256:
        _reject("[issued-value] source closure record digest changed")
    record = _parse_record(value._record_bytes)
    expected_referents = {
        name: record["referents"][name]["preimage_ref"]["sha256"]
        for name in _REFERENT_KEYS
    }
    if (
        value.captured_commit_oid != record["captured_commit_oid"]
        or value.authority_series_id != record["authority_series_id"]
        or value.origin_id != record["origin_id"]
        or value.cell_key != record["cell_key"]
        or dict(value.referent_sha256s) != expected_referents
    ):
        _reject("[issued-value] source closure fields changed")
    return value


def validate_source_closure(
    raw_record: bytes,
    *,
    repo_root: Path,
    authority_manifest: Mapping[str, object] | AuthorityManifest,
    report_cell: Mapping[str, object],
    candidate_authority_blob_sha256: str,
    human_approval_receipt: Mapping[str, object],
) -> ValidatedSourceClosure:
    """Validate issuance checks 1--7 and the step-8 receipt shape, in order."""

    record = _parse_record(raw_record)
    try:
        root = Path(repo_root)
    except (TypeError, ValueError) as exc:
        raise SourceClosureError("[git] repository root is invalid") from exc
    manifest = _typed_manifest(authority_manifest)

    commit_oid = _resolve_commit_once(root, record["captured_commit_oid"])
    _check_pre_authority(root, commit_oid, record)
    blobs = _load_referents(root, commit_oid, record, manifest)

    if record["authority_series_id"] != manifest.authority_series_id:
        _reject("[manifest] authority series mismatch")
    if record["origin_id"] != derive_origin_id(manifest):
        _reject("[manifest] origin ID mismatch")

    _validate_workload(
        blobs["authority.workload.descriptor_sha256"], report_cell, manifest
    )
    _validate_axis(blobs["axis_semantics_sha256"])
    _validate_verifier(blobs["verifier_policy_sha256"])
    try:
        resolve_by_contract_sha256(manifest.environment_contract_sha256)
    except Exception as exc:
        raise SourceClosureError(
            "[environment] contract digest did not resolve uniquely"
        ) from exc

    derived_cell_key = derive_cell_key(manifest)
    if record["cell_key"] != derived_cell_key:
        _reject("[cell-key] closure cell key differs from four-digest derivation")

    closure_digest = hashlib.sha256(raw_record).hexdigest()
    _validate_approval(
        human_approval_receipt,
        authority_blob_sha256=candidate_authority_blob_sha256,
        record=record,
        source_closure_sha256=closure_digest,
    )
    referent_sha256s = {
        name: record["referents"][name]["preimage_ref"]["sha256"]
        for name in _REFERENT_KEYS
    }
    issued = ValidatedSourceClosure(
        source_closure_sha256=closure_digest,
        captured_commit_oid=commit_oid,
        authority_series_id=record["authority_series_id"],
        origin_id=record["origin_id"],
        cell_key=record["cell_key"],
        referent_sha256s=referent_sha256s,
        record_bytes=raw_record,
        _issuer=_ISSUER_SEAL,
    )
    return assert_issued_validated_source_closure(issued)
