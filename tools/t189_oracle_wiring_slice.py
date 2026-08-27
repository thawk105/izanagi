#!/usr/bin/env python3
"""Verify the pinned T-189 task-oracle wiring slice without creating artifacts."""
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import sys
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.dev_waves.schema import (  # noqa: E402
    DEFAULT_MAX_JSON_BYTES,
    DevWavesError,
    canonical_bytes,
    strict_loads,
)
from tools import t189_task_catalog as task_catalog  # noqa: E402


SLICE_KIND = "t189-task-oracle-wiring-slice"
SLICE_SCHEMA_VERSION = "t189-task-oracle-wiring-slice/v1"
SLICE_SHA256 = "96a39ee259f985525df0a1206665dd331eb23b24e365b84e4558bfe115e75767"
SUPPORTED_COMMANDS = frozenset({
    "aggregate",
    "append-verdicts",
    "freeze-verdicts",
    "make-packets",
    "reveal-mapping",
    "verify",
})

_TOP_FIELDS = frozenset({
    "acceptance_contract",
    "artifact_kind",
    "catalog",
    "classification",
    "held_out_selected",
    "manifest_kind",
    "oracle_content_review_status",
    "purpose",
    "routing_evidence_status",
    "schema_version",
    "section8_complete",
    "slice_schema_version",
    "supported_commands",
    "task_universe_locked",
    "tasks",
})
_ACCEPTANCE_FIELDS = frozenset({
    "fix_gate_eligible", "routing_evidence_eligible", "task_acceptance_status",
})
_ARTIFACT_FIELDS = frozenset({"path", "relative_to", "sha256"})
_TASK_FIELDS = frozenset({
    "benchmark_task_id",
    "fix_gate_eligible",
    "known_finding_ids",
    "legacy_case",
    "oracle_findings",
    "oracle_kind",
    "provenance",
    "replay_artifact_sufficiency",
    "routing_evidence_eligible",
    "snapshot",
    "stage",
    "t189_stage_boundary",
    "task_acceptance_status",
    "task_type",
})
_PROVENANCE_FIELDS = frozenset({
    "catalog_join", "evidence", "oracle_content_review_status",
})
_CATALOG_JOIN_FIELDS = frozenset({
    "base_commit",
    "dev_wave_stage",
    "prompt",
    "receipt",
    "receipt_ordinal",
    "task_type",
    "wave_id",
    "wave_stage_receipt_count",
})
_PATH_DIGEST_FIELDS = frozenset({
    "jobs_relative_path", "relative_to", "sha256",
})
_FILE_EVIDENCE_FIELDS = frozenset({
    "evidence_id",
    "kind",
    "line_end",
    "line_start",
    "path",
    "relative_to",
    "sha256",
})
_COMMIT_EVIDENCE_FIELDS = frozenset({
    "evidence_id", "kind", "oid", "relative_to",
})
_FINDING_FIELDS = frozenset({
    "canonical_identity",
    "detection_condition",
    "evidence",
    "must_fix",
    "oracle_finding_id",
    "severity",
    "status",
})
_SNAPSHOT_FIELDS = frozenset({
    "base_commit", "base_commit_resolvable", "snapshot_manifest_status",
})
_NOT_ESTABLISHED_FIELDS = frozenset({"blocked_on", "evidence_status"})
_CLASSIFICATION_TOP_FIELDS = frozenset({
    "artifact_kind",
    "classifications",
    "criteria_document",
    "criteria_version",
    "schema_version",
})
_CLASSIFICATION_FIELDS = frozenset({
    "evidence",
    "rationale",
    "rule_id",
    "task_type",
    "task_type_status",
    "tie_break_applied",
    "wave_id",
})


class WiringSliceError(ValueError):
    """The wiring slice or one of its frozen dependencies is invalid."""


def _fail(label: str, reason: str) -> Any:
    raise WiringSliceError(f"{label}: {reason}")


def _object(value: object, fields: frozenset[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _fail(label, "must be an object")
    if set(value) != fields:
        return _fail(label, "field set mismatch")
    return value


def _json_copy(value: object, *, label: str, depth: int = 0) -> Any:
    if depth > 32:
        return _fail(label, "nesting depth exceeded")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if "\x00" in value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            return _fail(label, "invalid string")
        return value
    if isinstance(value, int):
        if abs(value) > (1 << 63) - 1:
            return _fail(label, "integer out of range")
        return value
    if isinstance(value, (float, Decimal)):
        return _fail(label, "float is forbidden")
    if isinstance(value, list):
        return [
            _json_copy(item, label=f"{label}[{index}]", depth=depth + 1)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or "\x00" in key:
                return _fail(label, "object key must be a NUL-free string")
            copied[key] = _json_copy(
                item, label=f"{label}.{key}", depth=depth + 1,
            )
        return copied
    return _fail(label, "unsupported JSON value")


def _string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        return _fail(label, "must be a non-empty string")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        return _fail(label, "must be an integer in range")
    return value


def _digest(value: object, *, label: str) -> str:
    text = _string(value, label=label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        return _fail(label, "must be a lowercase sha256")
    return text


def _relative_path(value: object, *, label: str) -> str:
    text = _string(value, label=label)
    if "\\" in text:
        return _fail(label, "must use POSIX separators")
    path = PurePosixPath(text)
    if path.is_absolute() or text != path.as_posix() or text == "." or ".." in path.parts:
        return _fail(label, "must be a normalized relative path")
    return text


def _path_digest(value: object, *, label: str) -> dict[str, str]:
    item = _object(value, _PATH_DIGEST_FIELDS, label=label)
    if item["relative_to"] != "jobs-root":
        return _fail(f"{label}.relative_to", "must be jobs-root")
    return {
        "jobs_relative_path": _relative_path(
            item["jobs_relative_path"], label=f"{label}.jobs_relative_path",
        ),
        "relative_to": "jobs-root",
        "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
    }


def _artifact_descriptor(
    value: object, *, label: str, expected_path: str,
) -> dict[str, str]:
    item = _object(value, _ARTIFACT_FIELDS, label=label)
    path = _relative_path(item["path"], label=f"{label}.path")
    if path != expected_path:
        return _fail(f"{label}.path", "path mismatch")
    if item["relative_to"] != "repository-root":
        return _fail(f"{label}.relative_to", "must be repository-root")
    return {
        "path": path,
        "relative_to": "repository-root",
        "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
    }


def _not_established(value: object, *, label: str, blocked_on: str) -> dict[str, str]:
    item = _object(value, _NOT_ESTABLISHED_FIELDS, label=label)
    if item["evidence_status"] != "not-established":
        return _fail(f"{label}.evidence_status", "must be not-established")
    if item["blocked_on"] != blocked_on:
        return _fail(f"{label}.blocked_on", "dependency mismatch")
    return {"blocked_on": blocked_on, "evidence_status": "not-established"}


def _validate_file_evidence(value: object, *, label: str) -> dict[str, Any]:
    item = _object(value, _FILE_EVIDENCE_FIELDS, label=label)
    evidence_id = _string(item["evidence_id"], label=f"{label}.evidence_id")
    kind = item["kind"]
    if evidence_id == "task-prompt":
        if kind != "task-prompt" or item["relative_to"] != "jobs-root":
            return _fail(label, "task-prompt identity mismatch")
    elif evidence_id == "fixed-worklog":
        if (
            kind != "fixed-final-state-worklog"
            or item["relative_to"] != "repository-root"
        ):
            return _fail(label, "fixed-worklog identity mismatch")
    else:
        return _fail(f"{label}.evidence_id", "unsupported file evidence")
    line_start = _integer(item["line_start"], label=f"{label}.line_start", minimum=1)
    line_end = _integer(item["line_end"], label=f"{label}.line_end", minimum=1)
    if line_end < line_start:
        return _fail(f"{label}.line_end", "precedes line_start")
    return {
        "evidence_id": evidence_id,
        "kind": kind,
        "line_end": line_end,
        "line_start": line_start,
        "path": _relative_path(item["path"], label=f"{label}.path"),
        "relative_to": item["relative_to"],
        "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
    }


def _validate_commit_evidence(value: object, *, label: str) -> dict[str, str]:
    item = _object(value, _COMMIT_EVIDENCE_FIELDS, label=label)
    if (
        item["evidence_id"] != "fixed-commit"
        or item["kind"] != "fixed-final-state-commit"
        or item["relative_to"] != "git-object-database"
    ):
        return _fail(label, "fixed-commit identity mismatch")
    oid = _string(item["oid"], label=f"{label}.oid")
    if not 7 <= len(oid) <= 40 or any(ch not in "0123456789abcdef" for ch in oid):
        return _fail(f"{label}.oid", "must be a lowercase commit object name")
    return {
        "evidence_id": "fixed-commit",
        "kind": "fixed-final-state-commit",
        "oid": oid,
        "relative_to": "git-object-database",
    }


def _validate_finding(value: object, *, label: str) -> dict[str, Any]:
    item = _object(value, _FINDING_FIELDS, label=label)
    finding_id = _string(
        item["oracle_finding_id"], label=f"{label}.oracle_finding_id",
    )
    if item["canonical_identity"] != finding_id:
        return _fail(f"{label}.canonical_identity", "finding identity mismatch")
    if item["severity"] != "HIGH":
        return _fail(f"{label}.severity", "must be HIGH")
    if item["must_fix"] is not True:
        return _fail(f"{label}.must_fix", "must be true")
    if item["status"] != "provisional-wiring-only":
        return _fail(f"{label}.status", "must be provisional-wiring-only")
    evidence = item["evidence"]
    if evidence != ["task-prompt", "fixed-worklog", "fixed-commit"]:
        return _fail(f"{label}.evidence", "evidence projection mismatch")
    return {
        "canonical_identity": finding_id,
        "detection_condition": _string(
            item["detection_condition"], label=f"{label}.detection_condition",
        ),
        "evidence": list(evidence),
        "must_fix": True,
        "oracle_finding_id": finding_id,
        "severity": "HIGH",
        "status": "provisional-wiring-only",
    }


def _validate_task(value: object, *, key: str) -> dict[str, Any]:
    label = f"wiring_slice.tasks[{key}]"
    item = _object(value, _TASK_FIELDS, label=label)
    if item["benchmark_task_id"] != key or item["legacy_case"] != key:
        return _fail(label, "task key or legacy_case mismatch")
    if item["task_type"] not in task_catalog.TASK_TYPES:
        return _fail(f"{label}.task_type", "unsupported task type")
    if item["stage"] is not None:
        return _fail(f"{label}.stage", "must be null")
    if item["oracle_kind"] != "positive":
        return _fail(f"{label}.oracle_kind", "must be positive")
    if item["task_acceptance_status"] != "unbound":
        return _fail(f"{label}.task_acceptance_status", "must be unbound")
    if item["fix_gate_eligible"] is not False:
        return _fail(f"{label}.fix_gate_eligible", "must be false")
    if item["routing_evidence_eligible"] is not False:
        return _fail(f"{label}.routing_evidence_eligible", "must be false")

    provenance = _object(
        item["provenance"], _PROVENANCE_FIELDS, label=f"{label}.provenance",
    )
    if provenance["oracle_content_review_status"] != "not-established":
        return _fail(
            f"{label}.provenance.oracle_content_review_status",
            "must be not-established",
        )
    join = _object(
        provenance["catalog_join"],
        _CATALOG_JOIN_FIELDS,
        label=f"{label}.provenance.catalog_join",
    )
    wave_id = _string(join["wave_id"], label=f"{label}.provenance.catalog_join.wave_id")
    stage = join["dev_wave_stage"]
    if stage != "plan":
        return _fail(f"{label}.provenance.catalog_join.dev_wave_stage", "must be plan")
    ordinal = _integer(
        join["receipt_ordinal"],
        label=f"{label}.provenance.catalog_join.receipt_ordinal",
    )
    count = _integer(
        join["wave_stage_receipt_count"],
        label=f"{label}.provenance.catalog_join.wave_stage_receipt_count",
        minimum=1,
    )
    if ordinal >= count:
        return _fail(f"{label}.provenance.catalog_join.receipt_ordinal", "outside count")
    if key != f"{wave_id}:{stage}:{ordinal}":
        return _fail(label, "benchmark task id does not match catalog join")
    if join["task_type"] != item["task_type"]:
        return _fail(f"{label}.provenance.catalog_join.task_type", "task type mismatch")
    catalog_join = {
        "base_commit": _string(
            join["base_commit"], label=f"{label}.provenance.catalog_join.base_commit",
        ),
        "dev_wave_stage": "plan",
        "prompt": _path_digest(
            join["prompt"], label=f"{label}.provenance.catalog_join.prompt",
        ),
        "receipt": _path_digest(
            join["receipt"], label=f"{label}.provenance.catalog_join.receipt",
        ),
        "receipt_ordinal": ordinal,
        "task_type": item["task_type"],
        "wave_id": wave_id,
        "wave_stage_receipt_count": count,
    }

    raw_evidence = provenance["evidence"]
    if not isinstance(raw_evidence, list) or len(raw_evidence) != 3:
        return _fail(f"{label}.provenance.evidence", "must contain three rows")
    evidence: list[dict[str, Any]] = []
    for index, raw_row in enumerate(raw_evidence):
        row_label = f"{label}.provenance.evidence[{index}]"
        if isinstance(raw_row, dict) and raw_row.get("evidence_id") == "fixed-commit":
            evidence.append(_validate_commit_evidence(raw_row, label=row_label))
        else:
            evidence.append(_validate_file_evidence(raw_row, label=row_label))
    if [row["evidence_id"] for row in evidence] != [
        "task-prompt", "fixed-worklog", "fixed-commit",
    ]:
        return _fail(f"{label}.provenance.evidence", "evidence order mismatch")
    if (
        evidence[0]["path"] != catalog_join["prompt"]["jobs_relative_path"]
        or evidence[0]["sha256"] != catalog_join["prompt"]["sha256"]
    ):
        return _fail(f"{label}.provenance.evidence[0]", "prompt projection mismatch")

    raw_findings = item["oracle_findings"]
    if not isinstance(raw_findings, list) or not raw_findings:
        return _fail(f"{label}.oracle_findings", "must be a non-empty array")
    findings = [
        _validate_finding(row, label=f"{label}.oracle_findings[{index}]")
        for index, row in enumerate(raw_findings)
    ]
    projection = sorted(row["oracle_finding_id"] for row in findings)
    if item["known_finding_ids"] != projection:
        return _fail(f"{label}.known_finding_ids", "oracle finding projection mismatch")
    if len(projection) != len(set(projection)):
        return _fail(f"{label}.oracle_findings", "duplicate finding id")

    snapshot = _object(item["snapshot"], _SNAPSHOT_FIELDS, label=f"{label}.snapshot")
    if (
        snapshot["base_commit"] != catalog_join["base_commit"]
        or snapshot["base_commit_resolvable"] is not True
        or snapshot["snapshot_manifest_status"] != "not-established"
    ):
        return _fail(f"{label}.snapshot", "snapshot status mismatch")
    return {
        "benchmark_task_id": key,
        "fix_gate_eligible": False,
        "known_finding_ids": projection,
        "legacy_case": key,
        "oracle_findings": findings,
        "oracle_kind": "positive",
        "provenance": {
            "catalog_join": catalog_join,
            "evidence": evidence,
            "oracle_content_review_status": "not-established",
        },
        "replay_artifact_sufficiency": _not_established(
            item["replay_artifact_sufficiency"],
            label=f"{label}.replay_artifact_sufficiency",
            blocked_on="§5.3 replayer contract",
        ),
        "routing_evidence_eligible": False,
        "snapshot": {
            "base_commit": catalog_join["base_commit"],
            "base_commit_resolvable": True,
            "snapshot_manifest_status": "not-established",
        },
        "stage": None,
        "t189_stage_boundary": _not_established(
            item["t189_stage_boundary"],
            label=f"{label}.t189_stage_boundary",
            blocked_on="§5.3 stage2/stage5 replayer contract",
        ),
        "task_acceptance_status": "unbound",
        "task_type": item["task_type"],
    }


def validate_wiring_slice(value: object, *, require_pin: bool = True) -> dict[str, Any]:
    """Validate the closed slice schema and optionally its semantic SHA pin."""
    copied = _json_copy(value, label="wiring_slice")
    top = _object(copied, _TOP_FIELDS, label="wiring_slice")
    exact = {
        "artifact_kind": SLICE_KIND,
        "manifest_kind": SLICE_KIND,
        "schema_version": 3,
        "slice_schema_version": SLICE_SCHEMA_VERSION,
        "purpose": "catalog-backed-task-specific-adjudication-wiring-fire-proof",
        "oracle_content_review_status": "not-established",
        "routing_evidence_status": "inconclusive",
        "section8_complete": False,
        "held_out_selected": False,
        "task_universe_locked": False,
    }
    for field, expected in exact.items():
        if top[field] != expected or type(top[field]) is not type(expected):
            return _fail(f"wiring_slice.{field}", f"must be {expected!r}")
    acceptance = _object(
        top["acceptance_contract"], _ACCEPTANCE_FIELDS,
        label="wiring_slice.acceptance_contract",
    )
    if acceptance != {
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
        "task_acceptance_status": "unbound",
    }:
        return _fail("wiring_slice.acceptance_contract", "status mismatch")
    commands = top["supported_commands"]
    if commands != sorted(SUPPORTED_COMMANDS):
        return _fail("wiring_slice.supported_commands", "allowlist mismatch")
    catalog_descriptor = _artifact_descriptor(
        top["catalog"],
        label="wiring_slice.catalog",
        expected_path="output/t189-routing-preregistration/task-catalog-v1.json",
    )
    classification_descriptor = _artifact_descriptor(
        top["classification"],
        label="wiring_slice.classification",
        expected_path=(
            "output/t189-routing-preregistration/"
            "task-type-classification-v1.json"
        ),
    )
    raw_tasks = top["tasks"]
    if not isinstance(raw_tasks, dict) or not raw_tasks:
        return _fail("wiring_slice.tasks", "must be a non-empty object")
    tasks: dict[str, Any] = {}
    all_finding_ids: list[str] = []
    for key, raw_task in raw_tasks.items():
        task_key = _string(key, label="wiring_slice.tasks key")
        tasks[task_key] = _validate_task(raw_task, key=task_key)
        all_finding_ids.extend(tasks[task_key]["known_finding_ids"])
    if len(all_finding_ids) != len(set(all_finding_ids)):
        return _fail("wiring_slice.tasks", "finding ids must be disjoint by task")
    normalized = {
        "acceptance_contract": {
            "fix_gate_eligible": False,
            "routing_evidence_eligible": False,
            "task_acceptance_status": "unbound",
        },
        "artifact_kind": SLICE_KIND,
        "catalog": catalog_descriptor,
        "classification": classification_descriptor,
        "held_out_selected": False,
        "manifest_kind": SLICE_KIND,
        "oracle_content_review_status": "not-established",
        "purpose": exact["purpose"],
        "routing_evidence_status": "inconclusive",
        "schema_version": 3,
        "section8_complete": False,
        "slice_schema_version": SLICE_SCHEMA_VERSION,
        "supported_commands": sorted(SUPPORTED_COMMANDS),
        "task_universe_locked": False,
        "tasks": tasks,
    }
    semantic_sha256 = hashlib.sha256(
        canonical_bytes(normalized) + b"\n"
    ).hexdigest()
    if require_pin and semantic_sha256 != SLICE_SHA256:
        return _fail("wiring_slice", "semantic SHA-256 pin mismatch")
    return normalized


def load_wiring_slice(path: Path, *, require_pin: bool = True) -> dict[str, Any]:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        try:
            metadata = path.lstat()
        except OSError:
            metadata = None
        if metadata is not None and stat.S_ISLNK(metadata.st_mode):
            raise WiringSliceError(
                "wiring_slice: must be a non-symlink regular file"
            ) from exc
        raise WiringSliceError("wiring_slice: unreadable or not strict JSON") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise WiringSliceError(
                "wiring_slice: must be a non-symlink regular file"
            )
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
        if _full_identity(before) != _full_identity(after):
            raise WiringSliceError("wiring_slice: changed while reading")
    finally:
        os.close(descriptor)
    try:
        value = strict_loads(
            raw, label="wiring-slice", max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    except DevWavesError as exc:
        raise WiringSliceError("wiring_slice: unreadable or not strict JSON") from exc
    normalized = validate_wiring_slice(value, require_pin=require_pin)
    if raw != canonical_bytes(normalized) + b"\n":
        raise WiringSliceError(
            "wiring_slice: bytes must be sorted compact UTF-8 with exactly one LF"
        )
    return normalized


def _root(root: Path, *, label: str) -> Path:
    lexical = Path(os.path.abspath(os.fspath(root)))
    try:
        current = Path(lexical.anchor)
        for part in lexical.parts[1:]:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                return _fail(label, "root ancestor must not be a symlink")
        if not stat.S_ISDIR(lexical.lstat().st_mode):
            return _fail(label, "root must be a directory")
        return lexical
    except OSError as exc:
        raise WiringSliceError(f"{label}: root is unavailable") from exc


def _link_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _full_identity(
    metadata: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _open_component(
    parent_fd: int,
    name: str,
    *,
    directory: bool,
    label: str,
) -> int:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        try:
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError:
            metadata = None
        if metadata is not None and stat.S_ISLNK(metadata.st_mode):
            return _fail(label, "symlink path is forbidden")
        raise WiringSliceError(f"{label}: file is unavailable") from exc


def _rooted_regular_bytes(
    root: Path,
    relative: str,
    *,
    label: str,
    before_read: Callable[[], None] | None = None,
) -> bytes:
    relative = _relative_path(relative, label=f"{label}.path")
    root = _root(root, label=f"{label}.root")
    descriptors: list[int] = []
    links: list[tuple[int, str, int, tuple[int, int, int]]] = []
    try:
        current_fd = os.open(
            root.anchor,
            os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        descriptors.append(current_fd)
        for part in root.parts[1:]:
            child_fd = _open_component(
                current_fd, part, directory=True, label=label,
            )
            descriptors.append(child_fd)
            identity = _link_identity(os.fstat(child_fd))
            links.append((current_fd, part, child_fd, identity))
            current_fd = child_fd

        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            child_fd = _open_component(
                current_fd, part, directory=True, label=label,
            )
            descriptors.append(child_fd)
            identity = _link_identity(os.fstat(child_fd))
            links.append((current_fd, part, child_fd, identity))
            current_fd = child_fd
        final_name = parts[-1]
        final_fd = _open_component(
            current_fd, final_name, directory=False, label=label,
        )
        descriptors.append(final_fd)
        before = os.fstat(final_fd)
        if not stat.S_ISREG(before.st_mode):
            return _fail(label, "must be a regular file")
        links.append((current_fd, final_name, final_fd, _link_identity(before)))
        if before_read is not None:
            before_read()
        with os.fdopen(os.dup(final_fd), "rb") as stream:
            raw = stream.read()
        after = os.fstat(final_fd)
        for parent_fd, name, opened_fd, expected in links:
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if (
                _link_identity(current) != expected
                or _link_identity(os.fstat(opened_fd)) != expected
            ):
                return _fail(label, "path changed while reading")
        if _full_identity(before) != _full_identity(after):
            return _fail(label, "file changed while reading")
        return raw
    except OSError as exc:
        raise WiringSliceError(f"{label}: file is unavailable") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _strict_text(raw: bytes, *, label: str) -> str:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise WiringSliceError(f"{label}: file is not strict UTF-8") from exc
    if "\x00" in text:
        return _fail(label, "NUL is forbidden")
    return text


def _audit_file_evidence(root: Path, evidence: Mapping[str, Any], *, label: str) -> None:
    raw = _rooted_regular_bytes(root, str(evidence["path"]), label=label)
    if hashlib.sha256(raw).hexdigest() != evidence["sha256"]:
        return _fail(label, "SHA-256 mismatch")
    text = _strict_text(raw, label=label)
    lines = text.splitlines()
    if evidence["line_end"] > len(lines):
        return _fail(label, "line range exceeds file")


def _resolve_commit(repo_root: Path, oid: str, *, label: str) -> None:
    try:
        completed = subprocess.run(
            [
                "git", "-C", os.fspath(repo_root), "rev-parse", "--verify",
                "--quiet", "--end-of-options", f"{oid}^{{commit}}",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WiringSliceError(f"{label}: commit resolution failed") from exc
    if completed.returncode != 0:
        return _fail(label, "commit does not resolve")


def _catalog_row_for_task(
    catalog: Mapping[str, Any], task: Mapping[str, Any],
) -> Mapping[str, Any]:
    join = task["provenance"]["catalog_join"]
    rows = [
        row
        for row in catalog["candidates"]
        if row["wave_id"] == join["wave_id"]
        and row["dev_wave_stage"] == join["dev_wave_stage"]
        and row["receipt_ordinal"] == join["receipt_ordinal"]
    ]
    if len(rows) != 1:
        return _fail(
            f"catalog_join[{task['benchmark_task_id']}]",
            "must match exactly one candidate row",
        )
    row = rows[0]
    fields = (
        "wave_id",
        "dev_wave_stage",
        "receipt_ordinal",
        "receipt",
        "prompt",
        "base_commit",
        "task_type",
        "wave_stage_receipt_count",
    )
    if any(row[field] != join[field] for field in fields):
        return _fail(
            f"catalog_join[{task['benchmark_task_id']}]", "row projection mismatch",
        )
    if row["base_commit_resolvable"] is not True:
        return _fail(
            f"catalog_join[{task['benchmark_task_id']}].base_commit_resolvable",
            "must be true",
        )
    return row


def _classification_for_task(
    row: Mapping[str, Any],
    task: Mapping[str, Any],
    classifications: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    label = f"classification_join[{task['benchmark_task_id']}]"
    classification = classifications.get(str(row["wave_id"]))
    if classification is None or classification.get("task_type") != task["task_type"]:
        return _fail(label, "task type mismatch")
    classification_fields = (
        "task_type",
        "task_type_status",
        "rule_id",
        "tie_break_applied",
        "evidence",
        "rationale",
    )
    if any(
        row[field] != classification.get(field)
        for field in classification_fields
    ):
        return _fail(label, "catalog classification projection mismatch")
    worklog_evidence = task["provenance"]["evidence"][1]
    classification_evidence = classification.get("evidence")
    if (
        not isinstance(classification_evidence, Mapping)
        or classification_evidence.get("kind") != "worklog-entry"
        or classification_evidence.get("relative_to") != "repository-root"
        or classification_evidence.get("path") != worklog_evidence["path"]
        or classification_evidence.get("line") != worklog_evidence["line_start"]
    ):
        return _fail(f"{label}.evidence", "worklog projection mismatch")
    return classification


def _classifications_from_raw(raw: bytes) -> dict[str, dict[str, Any]]:
    try:
        value = strict_loads(
            raw,
            label="classification-artifact",
            max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    except DevWavesError as exc:
        raise WiringSliceError(
            "classification: strict schema validation failed"
        ) from exc
    top = _object(
        _json_copy(value, label="classification-artifact"),
        _CLASSIFICATION_TOP_FIELDS,
        label="classification-artifact",
    )
    if top["artifact_kind"] != task_catalog.CLASSIFICATION_KIND:
        return _fail("classification-artifact.artifact_kind", "unsupported kind")
    if top["schema_version"] != task_catalog.CLASSIFICATION_SCHEMA_VERSION:
        return _fail("classification-artifact.schema_version", "unsupported version")
    if top["criteria_document"] != task_catalog.CLASSIFICATION_CRITERIA_DOCUMENT:
        return _fail("classification-artifact.criteria_document", "criteria mismatch")
    if top["criteria_version"] != task_catalog.CLASSIFICATION_CRITERIA_VERSION:
        return _fail("classification-artifact.criteria_version", "criteria mismatch")
    entries = top["classifications"]
    if not isinstance(entries, list):
        return _fail("classification-artifact.classifications", "must be a list")

    result: dict[str, dict[str, Any]] = {}
    for index, raw_entry in enumerate(entries):
        label = f"classification-artifact.classifications[{index}]"
        entry = _object(raw_entry, _CLASSIFICATION_FIELDS, label=label)
        wave_id = _string(entry["wave_id"], label=f"{label}.wave_id")
        if wave_id in result:
            return _fail(f"{label}.wave_id", "duplicate wave classification")
        status = entry["task_type_status"]
        task_type = entry["task_type"]
        if status == "classified":
            if task_type not in task_catalog.TASK_TYPES:
                return _fail(f"{label}.task_type", "unknown classified task type")
        elif status == "unclassified":
            if task_type is not None:
                return _fail(f"{label}.task_type", "must be null when unclassified")
        else:
            return _fail(f"{label}.task_type_status", "unknown status")
        rule_id = _string(entry["rule_id"], label=f"{label}.rule_id")
        if rule_id not in task_catalog.RULE_TASK_TYPES:
            return _fail(f"{label}.rule_id", "unknown classification rule")
        if task_catalog.RULE_TASK_TYPES[rule_id] != task_type:
            return _fail(f"{label}.rule_id", "does not map to task_type")
        if type(entry["tie_break_applied"]) is not bool:
            return _fail(f"{label}.tie_break_applied", "must be a bool")
        try:
            evidence = task_catalog._validate_classification_evidence(
                entry["evidence"], label=f"{label}.evidence",
            )
        except task_catalog.TaskCatalogError as exc:
            raise WiringSliceError(
                "classification: strict schema validation failed"
            ) from exc
        result[wave_id] = {
            "task_type": task_type,
            "task_type_status": status,
            "rule_id": rule_id,
            "tie_break_applied": entry["tie_break_applied"],
            "evidence": evidence,
            "rationale": _string(entry["rationale"], label=f"{label}.rationale"),
        }
    return result


def _audit_jobs_task(task: Mapping[str, Any], jobs_root: Path) -> None:
    join = task["provenance"]["catalog_join"]
    descriptor = join["receipt"]
    label = f"jobs[{task['benchmark_task_id']}].receipt"
    raw = _rooted_regular_bytes(
        jobs_root, descriptor["jobs_relative_path"], label=label,
    )
    if hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
        return _fail(label, "SHA-256 mismatch")
    _strict_text(raw, label=label)
    prompt_evidence = task["provenance"]["evidence"][0]
    _audit_file_evidence(
        jobs_root, prompt_evidence,
        label=f"jobs[{task['benchmark_task_id']}].task-prompt",
    )


def verify_wiring_slice(
    *,
    slice_path: Path,
    catalog_path: Path,
    classification_path: Path,
    repo_root: Path,
    jobs_root: Path | None = None,
) -> dict[str, Any]:
    """Verify portable dependencies and optionally physical jobs-tree bytes."""
    value = load_wiring_slice(slice_path)
    repo = _root(repo_root, label="repository-root")
    artifact_paths = {
        "catalog": catalog_path,
        "classification": classification_path,
    }
    raw_artifacts: dict[str, bytes] = {}
    for kind, supplied in artifact_paths.items():
        descriptor = value[kind]
        expected_path = repo / descriptor["path"]
        supplied_path = Path(os.path.abspath(os.fspath(supplied)))
        if supplied_path != expected_path:
            return _fail(kind, "supplied path does not match slice path")
        raw = _rooted_regular_bytes(repo, descriptor["path"], label=kind)
        if hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
            return _fail(kind, "raw SHA-256 mismatch")
        raw_artifacts[kind] = raw

    try:
        catalog_value = strict_loads(
            raw_artifacts["catalog"],
            label="task-catalog",
            max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
        catalog = task_catalog.validate_task_catalog(catalog_value)
    except (DevWavesError, task_catalog.TaskCatalogError) as exc:
        raise WiringSliceError("catalog: strict schema validation failed") from exc
    if raw_artifacts["catalog"] != task_catalog.task_catalog_bytes(catalog):
        return _fail("catalog", "bytes are not canonical")
    classifications = _classifications_from_raw(raw_artifacts["classification"])

    for task in value["tasks"].values():
        row = _catalog_row_for_task(catalog, task)
        _classification_for_task(row, task, classifications)
        _resolve_commit(
            repo,
            task["snapshot"]["base_commit"],
            label=f"base_commit[{task['benchmark_task_id']}]",
        )
        for evidence in task["provenance"]["evidence"]:
            evidence_id = evidence["evidence_id"]
            if evidence_id == "fixed-worklog":
                _audit_file_evidence(
                    repo,
                    evidence,
                    label=f"repository[{task['benchmark_task_id']}].fixed-worklog",
                )
            elif evidence_id == "fixed-commit":
                _resolve_commit(
                    repo,
                    evidence["oid"],
                    label=f"fixed_commit[{task['benchmark_task_id']}]",
                )
        if jobs_root is not None:
            _audit_jobs_task(task, _root(jobs_root, label="jobs-root"))

    return {
        "artifact_kind": "t189-task-oracle-wiring-slice-verification",
        "schema_version": 1,
        "integrity_status": "verified",
        "physical_jobs_audit": "verified" if jobs_root is not None else "not-requested",
        "checked_task_count": len(value["tasks"]),
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
        "routing_evidence_status": "inconclusive",
        "oracle_content_review_status": "not-established",
        "section8_complete": False,
    }


def _failure_result(reason: str) -> dict[str, Any]:
    return {
        "artifact_kind": "t189-task-oracle-wiring-slice-verification",
        "schema_version": 1,
        "integrity_status": "rejected",
        "failure_reasons": [reason],
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
        "routing_evidence_status": "inconclusive",
        "oracle_content_review_status": "not-established",
        "section8_complete": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--slice", dest="slice_path", type=Path, required=True)
    verify.add_argument("--catalog", type=Path, required=True)
    verify.add_argument("--classification", type=Path, required=True)
    verify.add_argument("--repo-root", type=Path, required=True)
    verify.add_argument("--jobs-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = verify_wiring_slice(
            slice_path=args.slice_path,
            catalog_path=args.catalog,
            classification_path=args.classification,
            repo_root=args.repo_root,
            jobs_root=args.jobs_root,
        )
        rc = 0
    except (OSError, TypeError, ValueError) as exc:
        result = _failure_result(str(exc))
        rc = 2
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SLICE_KIND",
    "SLICE_SCHEMA_VERSION",
    "SLICE_SHA256",
    "SUPPORTED_COMMANDS",
    "WiringSliceError",
    "load_wiring_slice",
    "main",
    "validate_wiring_slice",
    "verify_wiring_slice",
]
