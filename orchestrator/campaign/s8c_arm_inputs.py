# -*- coding: utf-8 -*-
"""Canonical execution inputs and issued arm bindings for 8c trials.

This is deliberately a leaf module: it derives descriptors only from the 8b
descriptor and holdout-freeze authorities and never imports the autonomous
runner or its completeness consumer.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from . import s8b_descriptor
from . import s8b_holdout_freeze


OFF_DESCRIPTOR_RELATIVE_PATH = Path(
    "output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json"
)
OFF_FREEZE_RELATIVE_PATH = Path(
    "output/s8c-preregistration/arm-inputs/freeze.v1.json"
)
OFF_FREEZE_SCHEMA_VERSION = "s8c-arm-input-freeze/v1"
INPUT_SCHEMA_VERSION = "8b-v1"
ARMS = ("on", "off", "swapped")
ARM_BINDING_DOMAIN_SEPARATOR_V1 = b"izanagi-s8c-arm-binding/v1\0"

_EXPECTED_ENDPOINT_RATIOS = ("20", "80")
_OFF_RATIO = "50"
_OFF_SKEW = "0.9"
_OFF_RMW = "0"
_OFF_RECORDS = 1_000_000
_OFF_THREADS = 48
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
_RESOLVED_SEAL = object()
_FREEZE_KEYS = frozenset({
    "schema_version",
    "descriptor_path",
    "descriptor_sha256",
    "descriptor_size_bytes",
    "derivation",
})
_DERIVATION_KEYS = frozenset({
    "endpoint_ratios",
    "midpoint_ratio",
    "positive_control_ratio",
    "skew",
    "rmw",
    "records",
    "threads",
})


class ArmInputError(RuntimeError):
    """An arm input could not be derived or verified exactly."""


@dataclasses.dataclass(frozen=True, slots=True)
class VerifiedOffNeutralInput:
    descriptor: Mapping[str, Any]
    canonical_input_bytes: bytes = dataclasses.field(repr=False)
    content_digest_sha256: str
    freeze_bytes: bytes = dataclasses.field(repr=False)


@dataclasses.dataclass(frozen=True, slots=True)
class ResolvedArmInput:
    arm: str
    holdout: str
    selected_holdout: str | None
    descriptor: Mapping[str, Any]
    canonical_input_bytes: bytes = dataclasses.field(repr=False)
    input_schema_version: str
    content_digest_sha256: str
    arm_binding_digest_sha256: str
    _seal: object = dataclasses.field(repr=False, compare=False)


def canonical_execution_input_bytes(descriptor: Mapping[str, Any]) -> bytes:
    """Return the exact canonical JSON bytes used as execution authority."""
    if not isinstance(descriptor, Mapping):
        raise ArmInputError("[arm-input-canonical] descriptor must be an object")
    try:
        return json.dumps(
            _plain_json(descriptor),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ArmInputError(
            "[arm-input-canonical] descriptor is not finite canonical JSON"
        ) from exc


def validate_execution_input_descriptor(descriptor: Mapping[str, Any]) -> bytes:
    """Validate the closed 8b descriptor schema and return its canonical bytes."""
    try:
        s8b_descriptor.validate_descriptor(_plain_json(descriptor))
    except s8b_descriptor.DescriptorError as exc:
        raise ArmInputError("[arm-input-canonical] descriptor schema is invalid") from exc
    raw = canonical_execution_input_bytes(descriptor)
    if descriptor.get("schema_version") != INPUT_SCHEMA_VERSION:
        raise ArmInputError("[arm-input-canonical] descriptor schema version is invalid")
    return raw


def _plain_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_json(item) for item in value]
    if isinstance(value, list):
        return [_plain_json(item) for item in value]
    return value


def _immutable_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _immutable_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_immutable_json(item) for item in value)
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode_canonical_object(raw: bytes, *, label: str) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise ArmInputError(f"[arm-input-artifact] {label} is not bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ArmInputError(f"[arm-input-artifact] {label} has a UTF-8 BOM")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArmInputError(
            f"[arm-input-artifact] {label} is not strict UTF-8 JSON"
        ) from exc
    if type(value) is not dict:
        raise ArmInputError(f"[arm-input-artifact] {label} must be an object")
    if canonical_execution_input_bytes(value) != raw:
        raise ArmInputError(
            f"[arm-input-artifact] {label} is not exact canonical JSON"
        )
    return value


def _neutral_derivation_record() -> dict[str, Any]:
    _assert_neutral_authorities()
    return {
        "endpoint_ratios": list(_EXPECTED_ENDPOINT_RATIOS),
        "midpoint_ratio": _OFF_RATIO,
        "positive_control_ratio": _OFF_RATIO,
        "skew": _OFF_SKEW,
        "rmw": _OFF_RMW,
        "records": _OFF_RECORDS,
        "threads": _OFF_THREADS,
    }


def _holdout_entries_by_candidate() -> dict[str, tuple[str, Mapping[str, Any]]]:
    entries: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for name, entry in s8b_holdout_freeze.HOLDOUTS.items():
        if type(name) is not str or not isinstance(entry, Mapping):
            raise ArmInputError("[arm-input-resolution] invalid 8b holdout table")
        candidate_id = entry.get("candidate_id")
        if type(candidate_id) is not str or candidate_id in entries:
            raise ArmInputError("[arm-input-resolution] ambiguous 8b holdout candidate")
        entries[candidate_id] = (name, entry)
    return entries


def _assert_neutral_authorities() -> None:
    entries = _holdout_entries_by_candidate()
    if frozenset(entries) != frozenset({"H1", "H2"}):
        raise ArmInputError("[arm-input-neutral] holdout candidates are not exact H1/H2")
    ratios: list[str] = []
    for candidate in ("H1", "H2"):
        _name, entry = entries[candidate]
        ycsb = entry.get("ycsb")
        if not isinstance(ycsb, Mapping):
            raise ArmInputError("[arm-input-neutral] holdout ycsb entry is absent")
        ratio = ycsb.get(s8b_holdout_freeze.RRATIO_KEY)
        skew = ycsb.get(s8b_holdout_freeze.SKEW_KEY)
        rmw = ycsb.get(s8b_holdout_freeze.RMW_KEY)
        if skew != _OFF_SKEW or rmw != _OFF_RMW:
            raise ArmInputError("[arm-input-neutral] frozen skew/rmw differs from literal")
        if entry.get("records") != _OFF_RECORDS or entry.get("threads") != _OFF_THREADS:
            raise ArmInputError("[arm-input-neutral] frozen scale differs from literal")
        if type(ratio) is not str:
            raise ArmInputError("[arm-input-neutral] frozen endpoint ratio is not a string")
        ratios.append(ratio)
    try:
        endpoints = sorted(int(value) for value in ratios)
    except ValueError as exc:
        raise ArmInputError("[arm-input-neutral] endpoint ratio is not an integer") from exc
    if tuple(str(value) for value in endpoints) != _EXPECTED_ENDPOINT_RATIOS:
        raise ArmInputError("[arm-input-neutral] frozen endpoints differ from 20/80")
    if sum(endpoints) % 2 or str(sum(endpoints) // 2) != _OFF_RATIO:
        raise ArmInputError("[arm-input-neutral] endpoint midpoint differs from literal 50")
    if getattr(s8b_holdout_freeze, "_POSITIVE_RATIO", None) != _OFF_RATIO:
        raise ArmInputError("[arm-input-neutral] positive-control ratio differs from literal")
    if getattr(s8b_holdout_freeze, "_FIXED_SKEW", None) != _OFF_SKEW:
        raise ArmInputError("[arm-input-neutral] fixed skew differs from literal")
    if getattr(s8b_holdout_freeze, "_FIXED_RMW", None) != _OFF_RMW:
        raise ArmInputError("[arm-input-neutral] fixed rmw differs from literal")


def derive_off_neutral_descriptor() -> dict[str, Any]:
    """Derive the neutral descriptor from both frozen midpoint authorities."""
    _assert_neutral_authorities()
    try:
        descriptor = s8b_descriptor.project_from_search_config({
            "records": _OFF_RECORDS,
            "threads": _OFF_THREADS,
            "ycsb": {
                "ycsb_zipf_skew": _OFF_SKEW,
                "ycsb_rratio": _OFF_RATIO,
                "ycsb_rmw": _OFF_RMW,
            },
        })
        s8b_descriptor.validate_descriptor(descriptor)
    except s8b_descriptor.DescriptorError as exc:
        raise ArmInputError("[arm-input-neutral] neutral projection failed") from exc
    return descriptor


def _artifact_payloads() -> tuple[bytes, bytes]:
    descriptor_raw = canonical_execution_input_bytes(derive_off_neutral_descriptor())
    digest = hashlib.sha256(descriptor_raw).hexdigest()
    freeze = {
        "schema_version": OFF_FREEZE_SCHEMA_VERSION,
        "descriptor_path": OFF_DESCRIPTOR_RELATIVE_PATH.as_posix(),
        "descriptor_sha256": digest,
        "descriptor_size_bytes": len(descriptor_raw),
        "derivation": _neutral_derivation_record(),
    }
    return descriptor_raw, canonical_execution_input_bytes(freeze)


def _write_create_or_verify(path: Path, raw: bytes) -> None:
    try:
        before = path.lstat()
    except FileNotFoundError:
        before = None
    except OSError as exc:
        raise ArmInputError(f"[arm-input-generate] cannot state artifact: {path}") from exc
    if before is not None:
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ArmInputError(f"[arm-input-generate] artifact is not a regular file: {path}")
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise ArmInputError(f"[arm-input-generate] cannot read artifact: {path}") from exc
        if existing != raw:
            raise ArmInputError(f"[arm-input-generate] existing artifact differs: {path}")
        return
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o644)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("write did not advance")
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise ArmInputError(f"[arm-input-generate] cannot create artifact: {path}") from exc


def _ensure_artifact_parent(root: Path, relative_parent: Path) -> None:
    current = root
    for component in relative_parent.parts:
        current = current / component
        try:
            stated = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o755)
                stated = current.lstat()
            except OSError as exc:
                raise ArmInputError(
                    f"[arm-input-generate] cannot create artifact parent: {current}"
                ) from exc
        except OSError as exc:
            raise ArmInputError(
                f"[arm-input-generate] cannot state artifact parent: {current}"
            ) from exc
        if stat.S_ISLNK(stated.st_mode) or not stat.S_ISDIR(stated.st_mode):
            raise ArmInputError(
                f"[arm-input-generate] artifact parent is not a directory: {current}"
            )


def generate_off_neutral_artifacts(*, repository_root: Path) -> None:
    """Create the two immutable off artifacts, or verify identical existing bytes."""
    root = Path(repository_root).resolve(strict=True)
    descriptor_raw, freeze_raw = _artifact_payloads()
    _ensure_artifact_parent(root, OFF_DESCRIPTOR_RELATIVE_PATH.parent)
    _write_create_or_verify(root / OFF_DESCRIPTOR_RELATIVE_PATH, descriptor_raw)
    _ensure_artifact_parent(root, OFF_FREEZE_RELATIVE_PATH.parent)
    _write_create_or_verify(root / OFF_FREEZE_RELATIVE_PATH, freeze_raw)


def _committed_regular_blob(root: Path, *, commit: str, relative: Path) -> bytes:
    if type(commit) is not str or _COMMIT_RE.fullmatch(commit) is None:
        raise ArmInputError("[arm-input-artifact] commit is not a full lowercase OID")
    path = relative.as_posix()
    try:
        listed = s8b_holdout_freeze._run_git_z(
            ["ls-tree", "-z", commit, "--", path], root
        )
    except s8b_holdout_freeze.FreezeError as exc:
        raise ArmInputError(
            f"[arm-input-artifact] cannot inspect committed path: {path}"
        ) from exc
    if len(listed) != 1 or "\t" not in listed[0]:
        raise ArmInputError(f"[arm-input-artifact] committed path is absent or ambiguous: {path}")
    metadata, decoded_path = listed[0].split("\t", 1)
    try:
        mode, kind, _oid = metadata.split(" ", 2)
    except ValueError as exc:
        raise ArmInputError(f"[arm-input-artifact] invalid tree entry: {path}") from exc
    if decoded_path != path or kind != "blob" or mode not in {"100644", "100755"}:
        raise ArmInputError(f"[arm-input-artifact] path is not a regular committed file: {path}")
    try:
        shown = s8b_holdout_freeze._run_git_bytes(
            ["show", f"{commit}:{path}"], root
        )
    except s8b_holdout_freeze.FreezeError as exc:
        raise ArmInputError(
            f"[arm-input-artifact] cannot read committed blob: {path}"
        ) from exc
    return shown


def verify_off_neutral_artifacts(
    *, repository_root: Path, commit: str
) -> VerifiedOffNeutralInput:
    """Verify canonical descriptor and sidecar bytes at one historical commit."""
    root = Path(repository_root).resolve(strict=True)
    descriptor_raw = _committed_regular_blob(
        root, commit=commit, relative=OFF_DESCRIPTOR_RELATIVE_PATH
    )
    freeze_raw = _committed_regular_blob(
        root, commit=commit, relative=OFF_FREEZE_RELATIVE_PATH
    )
    descriptor = _decode_canonical_object(descriptor_raw, label="off descriptor")
    freeze = _decode_canonical_object(freeze_raw, label="off freeze")
    if frozenset(freeze) != _FREEZE_KEYS:
        raise ArmInputError("[arm-input-artifact] off freeze exact keys differ")
    derivation = freeze.get("derivation")
    if type(derivation) is not dict or frozenset(derivation) != _DERIVATION_KEYS:
        raise ArmInputError("[arm-input-artifact] off derivation exact keys differ")
    expected_descriptor, expected_freeze = _artifact_payloads()
    if descriptor_raw != expected_descriptor or freeze_raw != expected_freeze:
        raise ArmInputError("[arm-input-artifact] off artifact differs from frozen derivation")
    try:
        s8b_descriptor.validate_descriptor(descriptor)
    except s8b_descriptor.DescriptorError as exc:
        raise ArmInputError("[arm-input-artifact] off descriptor schema is invalid") from exc
    digest = hashlib.sha256(descriptor_raw).hexdigest()
    if (
        freeze.get("schema_version") != OFF_FREEZE_SCHEMA_VERSION
        or freeze.get("descriptor_path") != OFF_DESCRIPTOR_RELATIVE_PATH.as_posix()
        or freeze.get("descriptor_sha256") != digest
        or freeze.get("descriptor_size_bytes") != len(descriptor_raw)
    ):
        raise ArmInputError("[arm-input-artifact] off freeze binding differs")
    return VerifiedOffNeutralInput(
        descriptor=_immutable_json(descriptor),
        canonical_input_bytes=descriptor_raw,
        content_digest_sha256=digest,
        freeze_bytes=freeze_raw,
    )


def _descriptor_for_candidate(candidate_id: str) -> tuple[str, dict[str, Any]]:
    entries = _holdout_entries_by_candidate()
    try:
        selected_name, entry = entries[candidate_id]
    except KeyError as exc:
        raise ArmInputError(
            f"[arm-input-resolution] unknown holdout candidate: {candidate_id}"
        ) from exc
    try:
        descriptor = s8b_descriptor.descriptor_for_holdout(entry)
    except s8b_descriptor.DescriptorError as exc:
        raise ArmInputError("[arm-input-resolution] holdout descriptor is invalid") from exc
    return selected_name, descriptor


def _binding_digest(*, holdout: str, arm: str, content_digest: str) -> str:
    preimage = (
        ARM_BINDING_DOMAIN_SEPARATOR_V1
        + holdout.encode("utf-8")
        + arm.encode("utf-8")
        + content_digest.encode("ascii")
    )
    return hashlib.sha256(preimage).hexdigest()


def resolve_arm_input(
    *, arm: str, holdout: str, repository_root: Path, commit: str
) -> ResolvedArmInput:
    """Resolve one arm and reject any incomplete or pairwise-colliding mapping."""
    if type(arm) is not str or arm not in ARMS:
        raise ArmInputError("[arm-input-resolution] arm is outside the closed set")
    if type(holdout) is not str:
        raise ArmInputError("[arm-input-resolution] holdout is not a string")
    entries = _holdout_entries_by_candidate()
    if holdout not in entries:
        raise ArmInputError("[arm-input-resolution] holdout is outside the frozen set")
    own_name, on_descriptor = _descriptor_for_candidate(holdout)
    swapped_name = s8b_holdout_freeze.DERANGEMENT.get(own_name)
    if (
        type(swapped_name) is not str
        or swapped_name == own_name
        or s8b_holdout_freeze.DERANGEMENT.get(swapped_name) != own_name
    ):
        raise ArmInputError("[arm-input-resolution] derangement is absent or invalid")
    candidate_by_name = {name: candidate for candidate, (name, _entry) in entries.items()}
    try:
        swapped_candidate = candidate_by_name[swapped_name]
    except KeyError as exc:
        raise ArmInputError("[arm-input-resolution] derangement target is unknown") from exc
    _swapped_name, swapped_descriptor = _descriptor_for_candidate(swapped_candidate)
    off = verify_off_neutral_artifacts(repository_root=repository_root, commit=commit)
    descriptors = {
        "on": (own_name, on_descriptor),
        "off": (None, _plain_json(off.descriptor)),
        "swapped": (swapped_name, swapped_descriptor),
    }
    canonical = {
        name: canonical_execution_input_bytes(descriptor)
        for name, (_selected, descriptor) in descriptors.items()
    }
    digests = {
        name: hashlib.sha256(raw).hexdigest() for name, raw in canonical.items()
    }
    if len(set(digests.values())) != len(ARMS):
        raise ArmInputError(
            "[arm-input-resolution] on/off/swapped content digests are not pairwise distinct"
        )
    selected_holdout, selected_descriptor = descriptors[arm]
    raw = canonical[arm]
    content_digest = digests[arm]
    schema = selected_descriptor.get("schema_version")
    if schema != INPUT_SCHEMA_VERSION:
        raise ArmInputError("[arm-input-resolution] selected descriptor schema is invalid")
    return ResolvedArmInput(
        arm=arm,
        holdout=holdout,
        selected_holdout=selected_holdout,
        descriptor=_immutable_json(selected_descriptor),
        canonical_input_bytes=raw,
        input_schema_version=schema,
        content_digest_sha256=content_digest,
        arm_binding_digest_sha256=_binding_digest(
            holdout=holdout, arm=arm, content_digest=content_digest
        ),
        _seal=_RESOLVED_SEAL,
    )


def assert_issued_resolved_arm_input(value: object) -> ResolvedArmInput:
    if type(value) is not ResolvedArmInput or value._seal is not _RESOLVED_SEAL:
        raise ArmInputError("[arm-input-resolution] input was not issued by resolver")
    raw = canonical_execution_input_bytes(value.descriptor)
    if raw != value.canonical_input_bytes:
        raise ArmInputError("[arm-input-resolution] resolved descriptor bytes changed")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != value.content_digest_sha256:
        raise ArmInputError("[arm-input-resolution] resolved content digest changed")
    if _binding_digest(
        holdout=value.holdout, arm=value.arm, content_digest=digest
    ) != value.arm_binding_digest_sha256:
        raise ArmInputError("[arm-input-resolution] resolved arm binding digest changed")
    return value
