#!/usr/bin/env python3
"""Verify the frozen T-1434/T-1222 retrospective science slice."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


FAMILY_ID = "T-1222-population-closure"
ARTIFACT_KIND = "t1434-t1222-task-output-science-slice"
SCHEMA_VERSION = "t1434-t1222-task-output-science-slice/v1"
RECEIPT_KIND = "t1434-t1222-task-output-science-slice-verification"
MAX_ARTIFACT_BYTES = 1 << 20
MAX_CATALOG_BYTES = 2 << 20
MAX_DEPENDENCY_BYTES = 8 << 20

CATALOG_BASE_COMMIT = "66fdf68c84991b50c2b56dad8d90bdad6e43750a"
IMPLEMENTATION_COMMIT = "6e707b6134dd0e8b8d4328faf19b4af97a31b783"
TESTED_TIP = "3f2fb1f7506faea6f20beb9c83efd87b91b35ce3"
WORKLOG_PATH = "docs/archive/worklog-phase3-0821-778.md"
WORKLOG_SHA256 = "9f4dee506f073666f66090ad7cd8058edcdb8a2fa027acbc934431541c71d5a9"
LEDGER_PATH = "dev-wave-t1434-science-slice/oracle-ledger-freeze-v1.json"
LEDGER_SHA256 = "e80571c0aebbd98e5ce3cb7f1cfaed9042cc39653917a834d13dcccb7f8b7304"
SOURCE_BUNDLE_PATH = (
    "dev-wave-t1434-science-slice/projections/oracle-source-bundle.md"
)
SOURCE_BUNDLE_SHA256 = (
    "8016b6337b74bd832c0a8ff416085433f314e1e695e84914e30e18e67f1e5585"
)

EXPECTED_SCOPE = {
    "claim": "availability-selected-retrospective-task-output-diagnostic",
    "family_id": FAMILY_ID,
    "held_out_selected": False,
    "organizational_independence": "not-established",
    "section8_complete": False,
    "stages": ["plan", "author"],
    "task_acceptance_is_replayer_status": False,
    "task_type": "bug-fix",
}

STAGES = ("plan", "author")
FINDING_NORMS = (
    ("T1222-O1-FRESH-CHILD-IMPORT-ISOLATION", "CRITICAL", "T1222-C1"),
    ("T1222-O2-SOCKET-CONTRACT-PRESERVATION", "HIGH", "T1222-C2"),
    ("T1222-O3-D452-REGRESSION", "HIGH", "T1222-C3"),
    ("T1222-O4-GROWTH-HOLD-IMMUTABILITY", "HIGH", "T1222-C4"),
    ("T1222-O5-SELF-LOAD-CONTROL", "HIGH", "T1222-C5"),
    ("T1222-O6-AUTHOR-SCOPE-BOUNDARY", "HIGH", "T1222-C6"),
)
FINDING_IDS = tuple(row[0] for row in FINDING_NORMS)
FINDINGS_SHA256 = "9999ea8a067211ba6bed7976cbeeb1eaadd58bd941b8bc8090d4cbb00c780f44"
_FINDING_FIELDS = frozenset({
    "applicable_stages", "canonical_identity", "detection_condition", "must_fix",
    "oracle_finding_id", "severity", "source_criterion_id",
})

CONTENT_REVIEW_PINS = {
    "oracle-content-A": {
        "prompt_path": "dev-wave-t1434-science-slice/stage3-lensA-prompt.md",
        "prompt_sha256": "3e50badbdb212305b546fae345579cd7e6b467a903147c3c3723384633883962",
        "output_path": "dev-wave-t1434-science-slice/stage3-lensA.md",
        "output_sha256": "9545f07fde7da61b75240dbc9f85bc84489713fb1317991a683f6f9a023d6e63",
        "receipt_path": (
            "dev-wave-t1434-science-slice/codex-artifacts/"
            "dev-wave-t1434-science-slice/t1434-science-stage3-lensA/receipt.json"
        ),
        "receipt_sha256": "976da9a89f8c52d34159c60be9a79b2c12d297e87e68cc6561bbd9e17f36b52d",
    },
    "oracle-content-B": {
        "prompt_path": "dev-wave-t1434-science-slice/stage3-lensB-prompt.md",
        "prompt_sha256": "3601d3c6a0896b37196e4c5d1e503a7a996e15446bcddc5ecf0423659ff30ed2",
        "output_path": "dev-wave-t1434-science-slice/stage3-lensB.md",
        "output_sha256": "0969375d68240b8699bcfbadcc47c54401b3b7cc39e7ea2413b470cd715c5a72",
        "receipt_path": (
            "dev-wave-t1434-science-slice/codex-artifacts/"
            "dev-wave-t1434-science-slice/t1434-science-stage3-lensB/receipt.json"
        ),
        "receipt_sha256": "c2180eab268de8e585a127b4931d85cab8cc89aff758002654d4f80986d02f3d",
    },
}

TARGET_PATHS = {
    "plan": {
        "prompt": f"{FAMILY_ID}/stage2-plan-prompt.md",
        "output": f"{FAMILY_ID}/stage2-plan.md",
        "receipt": (
            f"{FAMILY_ID}/{FAMILY_ID}-plan-"
            "c7d8a2085d4bacb773d2a1a240801409d1c754541d424fffe87fbf21e1305ff3/"
            "receipt.json"
        ),
    },
    "author": {
        "prompt": f"{FAMILY_ID}/stage5-author-prompt.md",
        "output": f"{FAMILY_ID}/stage5-author.md",
        "receipt": (
            f"{FAMILY_ID}/{FAMILY_ID}-author-"
            "6e91e61393fd97a4ea7ea5ef8783eb93cdc131692dc10259c99d97c42c444863/"
            "receipt.json"
        ),
    },
}

READER_PATHS = {
    "reader-A": {
        "prompt": "dev-wave-t1434-science-slice/readerA-prompt.md",
        "output": "dev-wave-t1434-science-slice/readerA.md",
        "receipt": (
            "dev-wave-t1434-science-slice/codex-artifacts/"
            "dev-wave-t1434-science-slice/t1434-science-readerA/receipt.json"
        ),
    },
    "reader-B": {
        "prompt": "dev-wave-t1434-science-slice/readerB-prompt.md",
        "output": "dev-wave-t1434-science-slice/readerB.md",
        "receipt": (
            "dev-wave-t1434-science-slice/codex-artifacts/"
            "dev-wave-t1434-science-slice/t1434-science-readerB/receipt.json"
        ),
    },
}

_TOP_FIELDS = frozenset({
    "artifact_kind", "content_review", "evidence", "oracle_ledger",
    "reader_reviews", "results", "schema_version", "scope",
})
_PATH_DIGEST_FIELDS = frozenset({"jobs_relative_path", "sha256"})
_CATALOG_TARGET_FIELDS = frozenset({
    "base_commit", "base_commit_resolvable", "dev_wave_stage", "evidence",
    "model_slug_contamination", "oracle_finding_count",
    "primary_acceptance_receipt", "prompt", "rationale", "receipt",
    "receipt_ordinal", "receipt_schema_version", "replay_artifact_sufficiency",
    "rule_id", "t189_design_work_markers", "t189_stage_boundary", "task_type",
    "task_type_reason", "task_type_status", "tie_break_applied", "wave_id",
    "wave_stage_receipt_count",
})


class ScienceSliceError(ValueError):
    """The slice or a frozen dependency failed validation."""


def _fail(label: str, reason: str) -> Any:
    raise ScienceSliceError(f"{label}: {reason}")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScienceSliceError(f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def _no_float(value: str) -> Any:
    raise ScienceSliceError(f"JSON: float is forbidden ({value})")


def _no_constant(value: str) -> Any:
    raise ScienceSliceError(f"JSON: non-finite number is forbidden ({value})")


def _strict_json(raw: bytes, *, label: str, forbid_floats: bool) -> Any:
    if not raw:
        return _fail(label, "file is empty")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScienceSliceError(f"{label}: not strict UTF-8") from exc
    if "\x00" in text:
        return _fail(label, "NUL is forbidden")
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=_no_float if forbid_floats else Decimal,
            parse_constant=_no_constant,
        )
    except ScienceSliceError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ScienceSliceError(f"{label}: invalid JSON") from exc


def _json_value(value: object, *, label: str, depth: int = 0) -> Any:
    if depth > 32:
        return _fail(label, "nesting depth exceeded")
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if abs(value) > (1 << 63) - 1:
            return _fail(label, "integer is out of range")
        return value
    if isinstance(value, str):
        if "\x00" in value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            return _fail(label, "invalid string")
        return value
    if isinstance(value, (float, Decimal)):
        return _fail(label, "float is forbidden")
    if isinstance(value, list):
        return [
            _json_value(item, label=f"{label}[{index}]", depth=depth + 1)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or "\x00" in key:
                return _fail(label, "object keys must be NUL-free strings")
            result[key] = _json_value(
                item, label=f"{label}.{key}", depth=depth + 1,
            )
        return result
    return _fail(label, "unsupported JSON value")


def _exact_json_equal(actual: object, expected: object) -> bool:
    """Compare JSON values without Python's bool/int equality aliasing."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return (
            set(actual) == set(expected)
            and all(
                _exact_json_equal(actual[key], value)
                for key, value in expected.items()
            )
        )
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return (
            len(actual) == len(expected)
            and all(
                _exact_json_equal(actual_item, expected_item)
                for actual_item, expected_item in zip(
                    actual, expected, strict=True,
                )
            )
        )
    return actual == expected


def _object(value: object, fields: frozenset[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _fail(label, "must be an object")
    if set(value) != fields:
        return _fail(label, "field set mismatch")
    return value


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        return _fail(label, "must be a non-empty string")
    return value


def _digest(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        return _fail(label, "must be a lowercase SHA-256")
    return value


def _oid(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        return _fail(label, "must be a full lowercase commit object name")
    return value


def _relative(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    path = PurePosixPath(value)
    if (
        "\\" in value or path.is_absolute() or value != path.as_posix()
        or value == "." or ".." in path.parts
    ):
        return _fail(label, "must be a normalized POSIX relative path")
    return value


def _descriptor(value: object, *, label: str, expected_path: str | None = None) -> dict[str, str]:
    item = _object(value, _PATH_DIGEST_FIELDS, label=label)
    path = _relative(item["jobs_relative_path"], label=f"{label}.jobs_relative_path")
    if expected_path is not None and path != expected_path:
        return _fail(f"{label}.jobs_relative_path", "path mismatch")
    return {
        "jobs_relative_path": path,
        "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
    }


def _validate_findings(value: object) -> None:
    label = "artifact.oracle_ledger.findings"
    if not isinstance(value, list) or len(value) != len(FINDING_NORMS):
        return _fail(label, "exact six-finding ledger mismatch")
    for index, (raw, norm) in enumerate(zip(value, FINDING_NORMS, strict=True)):
        row = _object(raw, _FINDING_FIELDS, label=f"{label}[{index}]")
        identity = (
            row["oracle_finding_id"], row["severity"],
            row["source_criterion_id"],
        )
        if (
            identity != norm
            or row["must_fix"] is not True
            or row["applicable_stages"] != list(STAGES)
        ):
            return _fail(label, "exact six-finding ledger mismatch")
    digest = hashlib.sha256(canonical_bytes(value) + b"\n").hexdigest()
    if digest != FINDINGS_SHA256:
        return _fail(label, "exact six-finding ledger mismatch")


def _root(root: Path, *, label: str) -> Path:
    lexical = Path(os.path.abspath(os.fspath(root)))
    try:
        current = Path(lexical.anchor)
        for part in lexical.parts[1:]:
            current /= part
            if stat.S_ISLNK(current.lstat().st_mode):
                return _fail(label, "root ancestor must not be a symlink")
        if not stat.S_ISDIR(lexical.lstat().st_mode):
            return _fail(label, "root must be a directory")
    except OSError as exc:
        raise ScienceSliceError(f"{label}: root is unavailable") from exc
    return lexical


def _link_identity(value: os.stat_result) -> tuple[int, int, int]:
    return value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode)


def _full_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode), value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def _open_component(parent_fd: int, name: str, *, directory: bool, label: str) -> int:
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
            return _fail(label, "symlink path component is forbidden")
        raise ScienceSliceError(f"{label}: file is unavailable") from exc


def _rooted_regular_bytes(
    root: Path, relative: str, *, label: str, max_bytes: int,
) -> bytes:
    root = _root(root, label=f"{label}.root")
    relative = _relative(relative, label=f"{label}.path")
    descriptors: list[int] = []
    links: list[tuple[int, str, int, tuple[int, int, int]]] = []
    try:
        current_fd = os.open(
            root.anchor,
            os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        descriptors.append(current_fd)
        for part in root.parts[1:]:
            child = _open_component(current_fd, part, directory=True, label=label)
            descriptors.append(child)
            links.append((current_fd, part, child, _link_identity(os.fstat(child))))
            current_fd = child
        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            child = _open_component(current_fd, part, directory=True, label=label)
            descriptors.append(child)
            links.append((current_fd, part, child, _link_identity(os.fstat(child))))
            current_fd = child
        final_name = parts[-1]
        final_fd = _open_component(
            current_fd, final_name, directory=False, label=label,
        )
        descriptors.append(final_fd)
        before = os.fstat(final_fd)
        if not stat.S_ISREG(before.st_mode):
            return _fail(label, "must be a regular file")
        if before.st_size > max_bytes:
            return _fail(label, f"exceeds {max_bytes} byte limit")
        links.append((current_fd, final_name, final_fd, _link_identity(before)))
        with os.fdopen(os.dup(final_fd), "rb") as stream:
            raw = stream.read(max_bytes + 1)
        after = os.fstat(final_fd)
        if len(raw) > max_bytes:
            return _fail(label, f"exceeds {max_bytes} byte limit")
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
        raise ScienceSliceError(f"{label}: file is unavailable") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _absolute_regular_bytes(path: Path, *, label: str, max_bytes: int) -> bytes:
    lexical = Path(os.path.abspath(os.fspath(path)))
    relative = PurePosixPath(*lexical.parts[1:]).as_posix()
    return _rooted_regular_bytes(
        Path(lexical.anchor), relative, label=label, max_bytes=max_bytes,
    )


def _validate_content_review(value: object) -> None:
    item = _object(value, frozenset({
        "adjudication", "organizational_independence", "reviews", "status",
        "workflow_blind_distinct_dispatch",
    }), label="artifact.content_review")
    expected = {
        "adjudication": "six-source-criteria-one-to-one",
        "organizational_independence": "not-established",
        "status": "reviewed-with-parent-adjudication",
        "workflow_blind_distinct_dispatch": True,
    }
    for field, wanted in expected.items():
        if item[field] != wanted or type(item[field]) is not type(wanted):
            return _fail(f"artifact.content_review.{field}", "value mismatch")
    reviews = item["reviews"]
    if not isinstance(reviews, list) or len(reviews) != 2:
        return _fail("artifact.content_review.reviews", "must contain two reviews")
    seen: list[str] = []
    for index, raw in enumerate(reviews):
        label = f"artifact.content_review.reviews[{index}]"
        review = _object(raw, frozenset({
            "output", "prompt", "receipt", "review_id", "target_outputs_disclosed",
        }), label=label)
        review_id = _text(review["review_id"], label=f"{label}.review_id")
        if review_id not in CONTENT_REVIEW_PINS or review_id in seen:
            return _fail(f"{label}.review_id", "unexpected or duplicate review")
        pin = CONTENT_REVIEW_PINS[review_id]
        if review["target_outputs_disclosed"] is not False:
            return _fail(f"{label}.target_outputs_disclosed", "must be false")
        prompt = _descriptor(
            review["prompt"], label=f"{label}.prompt",
            expected_path=pin["prompt_path"],
        )
        output = _descriptor(
            review["output"], label=f"{label}.output",
            expected_path=pin["output_path"],
        )
        receipt = _descriptor(
            review["receipt"], label=f"{label}.receipt",
            expected_path=pin["receipt_path"],
        )
        for name, descriptor in (
            ("prompt", prompt), ("output", output), ("receipt", receipt),
        ):
            if descriptor["sha256"] != pin[f"{name}_sha256"]:
                return _fail(f"{label}.{name}.sha256", "frozen pin mismatch")
        seen.append(review_id)
    if seen != list(CONTENT_REVIEW_PINS):
        return _fail("artifact.content_review.reviews", "review order mismatch")


def _validate_results(value: object) -> None:
    item = _object(value, frozenset({
        "artifact_verification_status", "coverage", "reader_agreement_status",
        "retrospective_task_output_acceptance_status", "routing_evidence_eligible",
        "routing_evidence_status", "semantic_miss_finding_ids", "verdicts",
    }), label="artifact.results")
    if item["artifact_verification_status"] != "pending-validator":
        return _fail(
            "artifact.results.artifact_verification_status",
            "must preserve the freeze-time pending-validator fact",
        )
    if item["routing_evidence_eligible"] is not False:
        return _fail("artifact.results.routing_evidence_eligible", "must be false")
    if item["routing_evidence_status"] != "inconclusive":
        return _fail("artifact.results.routing_evidence_status", "must be inconclusive")
    if item["reader_agreement_status"] not in {
        "agreed-all-cells", "disagreed-cells",
    }:
        return _fail("artifact.results.reader_agreement_status", "unknown status")
    if item["retrospective_task_output_acceptance_status"] not in {
        "accepted", "not-accepted", "inconclusive",
    }:
        return _fail(
            "artifact.results.retrospective_task_output_acceptance_status",
            "unknown status",
        )
    coverage = _object(item["coverage"], frozenset({
        "agreed_detected", "canonical_rational", "oracle_finding_total",
    }), label="artifact.results.coverage")
    numerator = coverage["agreed_detected"]
    denominator = coverage["oracle_finding_total"]
    if (
        type(numerator) is not int or type(denominator) is not int
        or denominator != 6 or not 0 <= numerator <= denominator
    ):
        return _fail("artifact.results.coverage", "count is out of range")
    fraction = str(Fraction(numerator, denominator))
    if coverage["canonical_rational"] != fraction:
        return _fail("artifact.results.coverage.canonical_rational", "not canonical")
    verdicts = item["verdicts"]
    if not isinstance(verdicts, list) or len(verdicts) != 6:
        return _fail("artifact.results.verdicts", "must contain six verdict rows")
    for index, raw in enumerate(verdicts):
        label = f"artifact.results.verdicts[{index}]"
        row = _object(raw, frozenset({
            "author", "logical_detected", "oracle_finding_id", "plan",
        }), label=label)
        if row["oracle_finding_id"] != FINDING_IDS[index]:
            return _fail(f"{label}.oracle_finding_id", "identity or order mismatch")
        if row["plan"] not in {"detected", "not-detected"}:
            return _fail(f"{label}.plan", "unknown verdict")
        if row["author"] not in {"detected", "not-detected"}:
            return _fail(f"{label}.author", "unknown verdict")
        if type(row["logical_detected"]) is not bool:
            return _fail(f"{label}.logical_detected", "must be a bool")
    misses = item["semantic_miss_finding_ids"]
    if (
        not isinstance(misses, list) or len(misses) != len(set(misses))
        or any(finding_id not in FINDING_IDS for finding_id in misses)
    ):
        return _fail("artifact.results.semantic_miss_finding_ids", "invalid projection")


def validate_artifact(value: object) -> dict[str, Any]:
    value = _json_value(value, label="artifact")
    top = _object(value, _TOP_FIELDS, label="artifact")
    if top["artifact_kind"] != ARTIFACT_KIND:
        return _fail("artifact.artifact_kind", "unsupported kind")
    if top["schema_version"] != SCHEMA_VERSION:
        return _fail("artifact.schema_version", "unsupported version")
    if not _exact_json_equal(top["scope"], EXPECTED_SCOPE):
        return _fail("artifact.scope", "scope must match the T-1222 slice exactly")

    _validate_content_review(top["content_review"])
    ledger = _object(top["oracle_ledger"], frozenset({
        "findings", "freeze", "source_bundle",
    }), label="artifact.oracle_ledger")
    _validate_findings(ledger["findings"])
    freeze_value = _object(ledger["freeze"], frozenset({
        "frozen_before_target_output_review", "jobs_relative_path", "sha256",
    }), label="artifact.oracle_ledger.freeze")
    if freeze_value["frozen_before_target_output_review"] is not True:
        return _fail(
            "artifact.oracle_ledger.freeze.frozen_before_target_output_review",
            "must be true",
        )
    freeze_descriptor = _descriptor(
        {key: freeze_value[key] for key in _PATH_DIGEST_FIELDS},
        label="artifact.oracle_ledger.freeze", expected_path=LEDGER_PATH,
    )
    freeze = {
        "frozen_before_target_output_review": True, **freeze_descriptor,
    }
    if freeze["sha256"] != LEDGER_SHA256:
        return _fail("artifact.oracle_ledger.freeze.sha256", "frozen pin mismatch")
    source = _descriptor(
        ledger["source_bundle"], label="artifact.oracle_ledger.source_bundle",
        expected_path=SOURCE_BUNDLE_PATH,
    )
    if source["sha256"] != SOURCE_BUNDLE_SHA256:
        return _fail("artifact.oracle_ledger.source_bundle.sha256", "frozen pin mismatch")

    evidence = _object(top["evidence"], frozenset({
        "acceptance_receipt", "catalog", "fixed_state", "targets",
    }), label="artifact.evidence")
    catalog = _object(evidence["catalog"], frozenset({
        "path", "target_projection_sha256",
    }), label="artifact.evidence.catalog")
    if catalog["path"] != "output/t189-routing-preregistration/task-catalog-v1.json":
        return _fail("artifact.evidence.catalog.path", "catalog path mismatch")
    _digest(
        catalog["target_projection_sha256"],
        label="artifact.evidence.catalog.target_projection_sha256",
    )
    fixed = _object(evidence["fixed_state"], frozenset({
        "implementation_commit", "tested_tip", "worklog_path", "worklog_sha256",
    }), label="artifact.evidence.fixed_state")
    expected_fixed = {
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "tested_tip": TESTED_TIP,
        "worklog_path": WORKLOG_PATH,
        "worklog_sha256": WORKLOG_SHA256,
    }
    if not _exact_json_equal(fixed, expected_fixed):
        return _fail("artifact.evidence.fixed_state", "frozen state mismatch")

    acceptance = _object(evidence["acceptance_receipt"], frozenset({
        "expected_tested_tip", "expected_verdict", "jobs_relative_path", "sha256",
    }), label="artifact.evidence.acceptance_receipt")
    acceptance_path = _relative(
        acceptance["jobs_relative_path"],
        label="artifact.evidence.acceptance_receipt.jobs_relative_path",
    )
    if acceptance_path != f"{FAMILY_ID}/acceptance-receipt-2.json":
        return _fail("artifact.evidence.acceptance_receipt", "path mismatch")
    if acceptance["expected_tested_tip"] != TESTED_TIP:
        return _fail("artifact.evidence.acceptance_receipt.expected_tested_tip", "tip mismatch")
    if acceptance["expected_verdict"] != "child-green":
        return _fail(
            "artifact.evidence.acceptance_receipt.expected_verdict",
            "must be child-green",
        )
    _digest(acceptance["sha256"], label="artifact.evidence.acceptance_receipt.sha256")

    targets = evidence["targets"]
    if not isinstance(targets, list) or len(targets) != 2:
        return _fail("artifact.evidence.targets", "must contain plan and author")
    for index, raw in enumerate(targets):
        label = f"artifact.evidence.targets[{index}]"
        target = _object(raw, frozenset({
            "output", "prompt", "receipt", "stage",
        }), label=label)
        stage = STAGES[index]
        if target["stage"] != stage:
            return _fail(f"{label}.stage", "stage or order mismatch")
        paths = TARGET_PATHS[stage]
        for name in ("prompt", "output", "receipt"):
            _descriptor(
                target[name], label=f"{label}.{name}",
                expected_path=paths[name],
            )

    readers = top["reader_reviews"]
    if not isinstance(readers, list) or len(readers) != 2:
        return _fail("artifact.reader_reviews", "must contain two readers")
    for index, raw in enumerate(readers):
        label = f"artifact.reader_reviews[{index}]"
        reader = _object(raw, frozenset({
            "arm_counts_disclosed", "output", "peer_verdict_disclosed", "prompt",
            "reader_id", "receipt",
        }), label=label)
        reader_id = tuple(READER_PATHS)[index]
        if reader["reader_id"] != reader_id:
            return _fail(f"{label}.reader_id", "reader identity or order mismatch")
        if reader["peer_verdict_disclosed"] is not False or reader["arm_counts_disclosed"] is not False:
            return _fail(label, "reader disclosure flags must both be false")
        paths = READER_PATHS[reader_id]
        for name in ("prompt", "output", "receipt"):
            _descriptor(
                reader[name], label=f"{label}.{name}",
                expected_path=paths[name],
            )

    _validate_results(top["results"])
    return top


def _load_artifact_with_raw(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _absolute_regular_bytes(
        path, label="artifact", max_bytes=MAX_ARTIFACT_BYTES,
    )
    value = _strict_json(raw, label="artifact", forbid_floats=True)
    normalized = validate_artifact(value)
    if raw != canonical_bytes(normalized) + b"\n":
        return _fail(
            "artifact", "bytes must be sorted compact UTF-8 with exactly one LF",
        )
    return normalized, raw


def load_artifact(path: Path) -> dict[str, Any]:
    normalized, _ = _load_artifact_with_raw(path)
    return normalized


def _git(
    repo: Path, arguments: Sequence[str], *, label: str,
    capture_stdout: bool = False,
) -> bytes:
    clean_env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(repo), *arguments],
            env=clean_env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ScienceSliceError(f"{label}: git inspection failed") from exc
    if result.returncode != 0:
        return _fail(label, "git predicate failed")
    return result.stdout if capture_stdout else b""


def _verify_git_toplevel(repo: Path) -> None:
    raw = _git(
        repo, ["rev-parse", "--show-toplevel"],
        label="repository.git-toplevel", capture_stdout=True,
    )
    expected = os.fsencode(repo) + b"\n"
    if raw != expected:
        return _fail(
            "repository.git-toplevel",
            "specified repository root is not the git top-level",
        )


def _commit(repo: Path, oid: str, *, label: str) -> None:
    _oid(oid, label=label)
    _git(repo, ["cat-file", "-e", f"{oid}^{{commit}}"], label=label)


def _ancestor(repo: Path, older: str, newer: str, *, label: str) -> None:
    _git(repo, ["merge-base", "--is-ancestor", older, newer], label=label)


def _dependency_binding(
    *, relative_to: str, path: str, raw: bytes,
) -> dict[str, str]:
    return {
        "path": path,
        "relative_to": relative_to,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _portable_context(
    artifact_path: Path, repo_root: Path, *,
    provenance: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Path, dict[str, Mapping[str, Any]]]:
    artifact, artifact_raw = _load_artifact_with_raw(artifact_path)
    if provenance is not None:
        provenance["artifact_raw_sha256"] = hashlib.sha256(artifact_raw).hexdigest()
    repo = _root(repo_root, label="repository-root")
    _verify_git_toplevel(repo)
    catalog_path = artifact["evidence"]["catalog"]["path"]
    catalog_raw = _rooted_regular_bytes(
        repo, catalog_path, label="catalog", max_bytes=MAX_CATALOG_BYTES,
    )
    catalog = _strict_json(catalog_raw, label="catalog", forbid_floats=True)
    catalog = _json_value(catalog, label="catalog")
    if not isinstance(catalog, dict) or set(catalog) != {
        "candidates", "counts", "excluded", "schema_version",
    }:
        return _fail("catalog", "top-level field set mismatch")
    if catalog_raw != canonical_bytes(catalog) + b"\n":
        return _fail("catalog", "bytes are not canonical JSON")
    if provenance is not None:
        provenance["dependency_bytes"].append(_dependency_binding(
            relative_to="repository-root", path=catalog_path, raw=catalog_raw,
        ))
    candidates = catalog["candidates"]
    if not isinstance(candidates, list):
        return _fail("catalog.candidates", "must be an array")
    target_rows = [
        row for row in candidates
        if isinstance(row, dict) and row.get("wave_id") == FAMILY_ID
    ]
    if len(target_rows) != 2:
        return _fail("catalog.target_projection", "must contain exactly two rows")
    projection_sha = hashlib.sha256(canonical_bytes(target_rows) + b"\n").hexdigest()
    if projection_sha != artifact["evidence"]["catalog"]["target_projection_sha256"]:
        return _fail("catalog.target_projection", "SHA-256 mismatch")
    rows_by_stage: dict[str, Mapping[str, Any]] = {}
    targets_by_stage = {
        row["stage"]: row for row in artifact["evidence"]["targets"]
    }
    acceptance_descriptor = artifact["evidence"]["acceptance_receipt"]
    for index, row in enumerate(target_rows):
        label = f"catalog.target_projection[{index}]"
        if set(row) != _CATALOG_TARGET_FIELDS:
            return _fail(label, "closed target-row field set mismatch")
        stage = row["dev_wave_stage"]
        if stage not in STAGES or stage in rows_by_stage:
            return _fail(f"{label}.dev_wave_stage", "unexpected or duplicate stage")
        catalog_contract = {
            "base_commit": CATALOG_BASE_COMMIT,
            "base_commit_resolvable": True,
            "receipt_ordinal": 0,
            "wave_stage_receipt_count": 1,
            "receipt_schema_version": 3,
            "task_type": "bug-fix",
        }
        if any(
            not _exact_json_equal(row[field], expected)
            for field, expected in catalog_contract.items()
        ):
            return _fail(label, "catalog target contract mismatch")
        target = targets_by_stage[stage]
        for name in ("prompt", "receipt"):
            row_descriptor = row[name]
            if not isinstance(row_descriptor, dict) or row_descriptor.get("relative_to") != "jobs-root":
                return _fail(f"{label}.{name}", "must be jobs-root relative")
            if any(
                row_descriptor.get(field) != target[name][field]
                for field in ("jobs_relative_path", "sha256")
            ):
                return _fail(f"{label}.{name}", "artifact projection mismatch")
        primary = row["primary_acceptance_receipt"]
        expected_record = {
            "jobs_relative_path": acceptance_descriptor["jobs_relative_path"],
            "relative_to": "jobs-root",
            "sha256": acceptance_descriptor["sha256"],
            "verdict": acceptance_descriptor["expected_verdict"],
        }
        if not _exact_json_equal(
            primary, {"present": True, "records": [expected_record]},
        ):
            return _fail(f"{label}.primary_acceptance_receipt", "projection mismatch")
        evidence = row["evidence"]
        expected_evidence = {
            "kind": "worklog-entry", "line": 1, "path": WORKLOG_PATH,
            "relative_to": "repository-root",
        }
        if not isinstance(evidence, dict) or not _exact_json_equal(
            evidence, expected_evidence,
        ):
            return _fail(f"{label}.evidence", "worklog join mismatch")
        rows_by_stage[stage] = row
    if set(rows_by_stage) != set(STAGES):
        return _fail("catalog.target_projection", "plan/author projection mismatch")

    worklog = artifact["evidence"]["fixed_state"]
    worklog_raw = _rooted_regular_bytes(
        repo, worklog["worklog_path"], label="repository.worklog",
        max_bytes=MAX_DEPENDENCY_BYTES,
    )
    if hashlib.sha256(worklog_raw).hexdigest() != worklog["worklog_sha256"]:
        return _fail("repository.worklog", "SHA-256 mismatch")
    if provenance is not None:
        provenance["dependency_bytes"].append(_dependency_binding(
            relative_to="repository-root", path=worklog["worklog_path"],
            raw=worklog_raw,
        ))

    for label, oid in (
        ("catalog-base-commit", CATALOG_BASE_COMMIT),
        ("implementation-commit", IMPLEMENTATION_COMMIT),
        ("tested-tip", TESTED_TIP),
    ):
        _commit(repo, oid, label=label)
    _ancestor(
        repo, CATALOG_BASE_COMMIT, IMPLEMENTATION_COMMIT,
        label="ancestry.catalog-base-to-implementation",
    )
    _ancestor(
        repo, IMPLEMENTATION_COMMIT, TESTED_TIP,
        label="ancestry.implementation-to-tested-tip",
    )
    return artifact, repo, rows_by_stage


def _portable_receipt() -> dict[str, Any]:
    return {
        "artifact_kind": RECEIPT_KIND,
        "artifact_verification_status": "valid",
        "checked_family_id": FAMILY_ID,
        "integrity_status": "valid",
        "organizational_independence": "not-established",
        "retrospective_task_output_acceptance_status": "not-evaluated",
        "schema_version": 1,
        "section8_complete": False,
        "verification_mode": "portable",
        "workflow_blind_distinct_dispatch": True,
    }


def verify_portable(*, artifact_path: Path, repo_root: Path) -> dict[str, Any]:
    _portable_context(artifact_path, repo_root)
    return _portable_receipt()


def _audit_descriptor(jobs: Path, descriptor: Mapping[str, str], *, label: str) -> bytes:
    raw = _rooted_regular_bytes(
        jobs, descriptor["jobs_relative_path"], label=label,
        max_bytes=MAX_DEPENDENCY_BYTES,
    )
    if hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
        return _fail(label, "SHA-256 mismatch")
    return raw


def _absolute_under(root: Path, relative: str) -> str:
    return os.fspath(root / PurePosixPath(relative))


def _receipt_object(raw: bytes, *, label: str) -> dict[str, Any]:
    value = _strict_json(raw, label=label, forbid_floats=False)
    if not isinstance(value, dict):
        return _fail(label, "must be a JSON object")
    return value


def _dispatch_receipt(
    raw: bytes, *, label: str, jobs: Path, prompt: Mapping[str, str],
    output: Mapping[str, str], receipt: Mapping[str, str], stage: str,
    wave_id: str, expected_base: str | None,
) -> dict[str, Any]:
    value = _receipt_object(raw, label=label)
    exact = {
        "stage": stage,
        "outcome": "accepted",
        "prompt_sha256": prompt["sha256"],
        "output_sha256": output["sha256"],
        "output_path": _absolute_under(jobs, output["jobs_relative_path"]),
        "receipt_path": _absolute_under(jobs, receipt["jobs_relative_path"]),
        "manifest_wave_id": wave_id,
    }
    if expected_base is not None:
        exact["base_commit"] = expected_base
    for field, expected in exact.items():
        if value.get(field) != expected:
            return _fail(f"{label}.{field}", "receipt projection mismatch")
    recorded_model = _text(value.get("recorded_model"), label=f"{label}.recorded_model")
    recorded_effort = _text(value.get("recorded_effort"), label=f"{label}.recorded_effort")
    if value.get("requested_model") != recorded_model:
        return _fail(f"{label}.recorded_model", "requested/recorded mismatch")
    if value.get("requested_effort") != recorded_effort:
        return _fail(f"{label}.recorded_effort", "requested/recorded mismatch")
    attempts = value.get("attempts")
    if (
        not isinstance(attempts, list) or len(attempts) != 1
        or not isinstance(attempts[0], dict)
        or attempts[0].get("accepted") is not True
        or attempts[0].get("output_sha256") != output["sha256"]
    ):
        return _fail(f"{label}.attempts", "accepted output projection mismatch")
    return value


_TABLE_HEADER = ("finding_id", "stage", "verdict", "evidence_lines", "rationale")
_ATTESTATION_KEYS = (
    "reader_id", "peer_verdict_disclosed", "arm_counts_disclosed",
)
_ATX_H2_RE = re.compile(r" {0,3}##(?:[ \t]+(?P<body>.*)|[ \t]*)\Z")


def _markdown_h2_body(line: str) -> str | None:
    """Return a normalized CommonMark ATX H2 body, if *line* is an H2."""
    match = _ATX_H2_RE.fullmatch(line)
    if match is None:
        return None
    body = match.group("body") or ""
    body = re.sub(r"[ \t]+#+[ \t]*\Z", "", body)
    return body.strip(" \t")


def parse_reader_markdown(raw: bytes, *, expected_reader_id: str, label: str) -> dict[tuple[str, str], str]:
    if len(raw) > MAX_DEPENDENCY_BYTES:
        return _fail(label, "exceeds file size limit")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScienceSliceError(f"{label}: not strict UTF-8") from exc
    if "\x00" in text:
        return _fail(label, "NUL is forbidden")
    lines = text.splitlines()
    header_indices: list[int] = []
    for index, line in enumerate(lines):
        if line.startswith("|") and line.endswith("|"):
            cells = tuple(cell.strip() for cell in line[1:-1].split("|"))
            if cells == _TABLE_HEADER:
                header_indices.append(index)
    if len(header_indices) != 1:
        return _fail(label, "must contain exactly one verdict table")
    index = header_indices[0] + 1
    if index >= len(lines) or not re.fullmatch(
        r"\|(?:\s*:?-+:?\s*\|){5}", lines[index],
    ):
        return _fail(label, "verdict table separator is malformed")
    index += 1
    matrix: dict[tuple[str, str], str] = {}
    while index < len(lines) and lines[index].startswith("|") and lines[index].endswith("|"):
        cells = [cell.strip() for cell in lines[index][1:-1].split("|")]
        if len(cells) != 5 or any(not cell for cell in cells):
            return _fail(label, "verdict row must contain five non-empty cells")
        finding_id, stage, verdict = cells[:3]
        if finding_id not in FINDING_IDS or stage not in STAGES:
            return _fail(label, "verdict table contains an extra cell")
        if verdict not in {"detected", "not-detected"}:
            return _fail(label, "verdict must be detected or not-detected")
        key = (finding_id, stage)
        if key in matrix:
            return _fail(label, "verdict table contains a duplicate cell")
        matrix[key] = verdict
        index += 1
    expected_cells = {(finding_id, stage) for finding_id in FINDING_IDS for stage in STAGES}
    if set(matrix) != expected_cells:
        return _fail(label, "verdict table has missing or extra cells")

    attestation_headers = [
        index for index, line in enumerate(lines)
        if _markdown_h2_body(line) == "Blindness attestation"
    ]
    if len(attestation_headers) != 1:
        return _fail(label, "must contain exactly one blindness attestation")
    start = attestation_headers[0] + 1
    attestation_lines = []
    for line in lines[start:]:
        if _markdown_h2_body(line) is not None:
            break
        if line.strip():
            attestation_lines.append(line.strip())
    attestation: dict[str, str] = {}
    for line in attestation_lines:
        if "=" not in line:
            return _fail(label, "blindness attestation line is malformed")
        key, value = (part.strip() for part in line.split("=", 1))
        if key not in _ATTESTATION_KEYS or key in attestation:
            return _fail(label, "blindness attestation key mismatch")
        attestation[key] = value
    expected_attestation = {
        "reader_id": expected_reader_id,
        "peer_verdict_disclosed": "false",
        "arm_counts_disclosed": "false",
    }
    if attestation != expected_attestation:
        return _fail(label, "blindness attestation mismatch")
    return matrix


def _evaluate_reader_matrices(
    matrices: Mapping[str, Mapping[tuple[str, str], str]], *,
    primary_child_green: bool,
) -> dict[str, Any]:
    if set(matrices) != set(READER_PATHS):
        return _fail("reader evaluation", "must contain reader-A and reader-B")
    expected_cells = {(finding_id, stage) for finding_id in FINDING_IDS for stage in STAGES}
    if any(set(matrix) != expected_cells for matrix in matrices.values()):
        return _fail("reader evaluation", "matrix cell set mismatch")
    agreement = all(
        matrices["reader-A"][cell] == matrices["reader-B"][cell]
        for cell in expected_cells
    )
    verdicts = []
    for finding_id in FINDING_IDS:
        stage_verdicts = {
            stage: (
                "detected"
                if all(matrices[reader][(finding_id, stage)] == "detected" for reader in READER_PATHS)
                else "not-detected"
            )
            for stage in STAGES
        }
        logical = all(stage_verdicts[stage] == "detected" for stage in STAGES)
        verdicts.append({
            "author": stage_verdicts["author"],
            "logical_detected": logical,
            "oracle_finding_id": finding_id,
            "plan": stage_verdicts["plan"],
        })
    numerator = sum(row["logical_detected"] for row in verdicts)
    all_reader_consensus_detected = numerator == len(FINDING_IDS)
    return {
        "coverage": {
            "agreed_detected": numerator,
            "canonical_rational": str(Fraction(numerator, len(FINDING_IDS))),
            "oracle_finding_total": len(FINDING_IDS),
        },
        "reader_agreement_status": (
            "agreed-all-cells" if agreement else "disagreed-cells"
        ),
        "retrospective_task_output_acceptance_status": (
            "accepted"
            if all_reader_consensus_detected and primary_child_green
            else "not-accepted"
        ),
        "semantic_miss_finding_ids": [
            row["oracle_finding_id"] for row in verdicts
            if not row["logical_detected"]
        ],
        "verdicts": verdicts,
    }


def verify_physical(*, artifact_path: Path, repo_root: Path, jobs_root: Path) -> dict[str, Any]:
    provenance: dict[str, Any] = {"dependency_bytes": []}
    artifact, _, catalog_rows = _portable_context(
        artifact_path, repo_root, provenance=provenance,
    )
    jobs = _root(jobs_root, label="jobs-root")
    raw_by_label: dict[str, bytes] = {}

    def audit(descriptor: Mapping[str, str], label: str) -> bytes:
        raw = _audit_descriptor(jobs, descriptor, label=label)
        raw_by_label[label] = raw
        provenance["dependency_bytes"].append(_dependency_binding(
            relative_to="jobs-root",
            path=descriptor["jobs_relative_path"], raw=raw,
        ))
        return raw

    for review in artifact["content_review"]["reviews"]:
        prefix = f"jobs.content_review[{review['review_id']}]"
        for name in ("prompt", "output", "receipt"):
            audit(review[name], f"{prefix}.{name}")
    for target in artifact["evidence"]["targets"]:
        prefix = f"jobs.targets[{target['stage']}]"
        for name in ("prompt", "output", "receipt"):
            audit(target[name], f"{prefix}.{name}")
    acceptance_descriptor = artifact["evidence"]["acceptance_receipt"]
    acceptance_raw = audit(acceptance_descriptor, "jobs.acceptance_receipt")
    audit(artifact["oracle_ledger"]["freeze"], "jobs.oracle_ledger.freeze")
    audit(artifact["oracle_ledger"]["source_bundle"], "jobs.oracle_ledger.source_bundle")
    for reader in artifact["reader_reviews"]:
        prefix = f"jobs.reader_reviews[{reader['reader_id']}]"
        for name in ("prompt", "output", "receipt"):
            audit(reader[name], f"{prefix}.{name}")

    for review in artifact["content_review"]["reviews"]:
        prefix = f"jobs.content_review[{review['review_id']}]"
        _dispatch_receipt(
            raw_by_label[f"{prefix}.receipt"], label=f"{prefix}.receipt",
            jobs=jobs, prompt=review["prompt"], output=review["output"],
            receipt=review["receipt"], stage="consult",
            wave_id="dev-wave-t1434-science-slice", expected_base=None,
        )
    for target in artifact["evidence"]["targets"]:
        stage = target["stage"]
        prefix = f"jobs.targets[{stage}]"
        _dispatch_receipt(
            raw_by_label[f"{prefix}.receipt"], label=f"{prefix}.receipt",
            jobs=jobs, prompt=target["prompt"], output=target["output"],
            receipt=target["receipt"], stage=stage, wave_id=FAMILY_ID,
            expected_base=str(catalog_rows[stage]["base_commit"]),
        )
    matrices: dict[str, dict[tuple[str, str], str]] = {}
    for reader in artifact["reader_reviews"]:
        reader_id = reader["reader_id"]
        prefix = f"jobs.reader_reviews[{reader_id}]"
        _dispatch_receipt(
            raw_by_label[f"{prefix}.receipt"], label=f"{prefix}.receipt",
            jobs=jobs, prompt=reader["prompt"], output=reader["output"],
            receipt=reader["receipt"], stage="consult",
            wave_id="dev-wave-t1434-science-slice", expected_base=None,
        )
        matrices[reader_id] = parse_reader_markdown(
            raw_by_label[f"{prefix}.output"], expected_reader_id=reader_id,
            label=f"{prefix}.output",
        )

    acceptance = _receipt_object(acceptance_raw, label="jobs.acceptance_receipt")
    acceptance_expected = {
        "acceptance_wave": FAMILY_ID,
        "tested_tip": TESTED_TIP,
        "child_rc": 0,
        "red_nodeids": [],
        "flake_nodeids": [],
    }
    for field, expected in acceptance_expected.items():
        if acceptance.get(field) != expected or type(acceptance.get(field)) is not type(expected):
            return _fail(f"jobs.acceptance_receipt.{field}", "receipt value mismatch")
    expected_verdict = artifact["evidence"]["acceptance_receipt"]["expected_verdict"]
    if acceptance.get("verdict") != expected_verdict:
        return _fail("jobs.acceptance_receipt.verdict", "artifact projection mismatch")
    for fingerprint in ("pre_fingerprint", "post_fingerprint"):
        value = acceptance.get(fingerprint)
        if not isinstance(value, dict) or value.get("head_sha") != TESTED_TIP:
            return _fail(f"jobs.acceptance_receipt.{fingerprint}", "tested tip mismatch")
    primary_green = acceptance.get("verdict") == "child-green"

    computed = _evaluate_reader_matrices(
        matrices, primary_child_green=primary_green,
    )
    stored = artifact["results"]
    for field in (
        "coverage", "reader_agreement_status",
        "retrospective_task_output_acceptance_status",
        "semantic_miss_finding_ids", "verdicts",
    ):
        if stored[field] != computed[field]:
            return _fail(f"artifact.results.{field}", "physical recomputation mismatch")

    validator_raw = _absolute_regular_bytes(
        Path(__file__), label="validator", max_bytes=MAX_DEPENDENCY_BYTES,
    )
    dependency_bytes = sorted(
        provenance["dependency_bytes"],
        key=lambda item: (item["relative_to"], item["path"], item["sha256"]),
    )

    return {
        "artifact_raw_sha256": provenance["artifact_raw_sha256"],
        "artifact_kind": RECEIPT_KIND,
        "artifact_verification_status": "valid",
        "checked_family_id": FAMILY_ID,
        "coverage": computed["coverage"],
        "dependency_bytes": dependency_bytes,
        "integrity_status": "valid",
        "organizational_independence": "not-established",
        "reader_agreement_status": computed["reader_agreement_status"],
        "retrospective_task_output_acceptance_status": computed[
            "retrospective_task_output_acceptance_status"
        ],
        "schema_version": 1,
        "section8_complete": False,
        "verification_mode": "physical",
        "validator_bytes_sha256": hashlib.sha256(validator_raw).hexdigest(),
        "workflow_blind_distinct_dispatch": True,
    }


def _failure_receipt(reason: str, *, mode: str) -> dict[str, Any]:
    return {
        "artifact_kind": RECEIPT_KIND,
        "artifact_verification_status": "rejected",
        "failure_reasons": [reason],
        "integrity_status": "rejected",
        "retrospective_task_output_acceptance_status": "not-evaluated",
        "schema_version": 1,
        "verification_mode": mode,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    portable = subparsers.add_parser("verify-portable")
    portable.add_argument("artifact", type=Path)
    portable.add_argument("--repo-root", type=Path, default=Path.cwd())
    physical = subparsers.add_parser("verify-physical")
    physical.add_argument("artifact", type=Path)
    physical.add_argument("--repo-root", type=Path, required=True)
    physical.add_argument("--jobs-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    mode = "portable" if args.command == "verify-portable" else "physical"
    try:
        if mode == "portable":
            result = verify_portable(
                artifact_path=args.artifact, repo_root=args.repo_root,
            )
        else:
            result = verify_physical(
                artifact_path=args.artifact, repo_root=args.repo_root,
                jobs_root=args.jobs_root,
            )
        rc = 0
    except (OSError, TypeError, ValueError) as exc:
        result = _failure_receipt(str(exc), mode=mode)
        rc = 2
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARTIFACT_KIND", "FAMILY_ID", "FINDING_IDS", "ScienceSliceError",
    "canonical_bytes", "load_artifact", "main", "parse_reader_markdown",
    "validate_artifact", "verify_physical", "verify_portable",
]
