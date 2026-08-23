#!/usr/bin/env python3
"""Build the deterministic T-189 pre-screen candidate catalog.

The generator reads physical dev-wave receipts at exactly
``<jobs-root>/<wave>/<job-id>/receipt.json``.  It does not fetch, mutate the
jobs tree, infer a T-189 stage, or classify a task.  Task types come only from
the caller-supplied classification artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.dev_waves.schema import (  # noqa: E402
    DEFAULT_MAX_JSON_BYTES,
    DevWavesError,
    canonical_bytes,
    strict_loads,
)


SCHEMA_VERSION = "t189-task-catalog/v1"
CLASSIFICATION_SCHEMA_VERSION = 1
CLASSIFICATION_KIND = "t189-task-type-classification"
SUPPORTED_RECEIPT_SCHEMAS = frozenset({3, 4})
DEV_WAVE_STAGES = ("plan", "author")
TASK_TYPES = ("new-mechanism", "bug-fix", "check-or-test", "docs")
MODEL_LITERALS = ("gpt-5.6-sol", "gpt-5.6-luna", "reasoning=max")
DESIGN_MARKERS = (
    "codex_reasoning_ab", "T-189", "T-181", "T-182", "model-routing",
    "routing_evidence_status",
)
EXCLUSION_REASONS = (
    "unsupported-receipt-schema",
    "unsupported-dev-wave-stage",
    "invalid-receipt-field",
    "missing-paired-stage",
    "prompt-body-unrecoverable",
    "base-commit-unresolvable",
)

_CLASSIFICATION_TOP_FIELDS = frozenset({
    "artifact_kind", "classifications", "classifier", "criteria_document",
    "criteria_version", "independent_classifiers", "schema_version",
    "signatures",
})
_CLASSIFICATION_FIELDS = frozenset({
    "evidence", "rationale", "rule_id", "task_type", "task_type_status",
    "tie_break_applied", "wave_id",
})
_CATALOG_FIELDS = frozenset({"schema_version", "counts", "candidates", "excluded"})
_COUNT_FIELDS = frozenset({
    "paired_stage_wave_count", "prompt_recoverable_wave_count",
    "candidate_receipt_count", "excluded_receipt_count",
    "candidate_receipts_by_task_type",
})
_CANDIDATE_FIELDS = frozenset({
    "wave_id", "dev_wave_stage", "receipt_schema_version", "receipt",
    "prompt", "base_commit", "base_commit_resolvable",
    "model_slug_contamination", "t189_design_work_markers",
    "primary_acceptance_receipt", "wave_stage_receipt_count",
    "receipt_ordinal", "task_type", "task_type_status", "task_type_reason",
    "rule_id", "tie_break_applied", "evidence", "rationale",
    "oracle_finding_count", "t189_stage_boundary",
    "replay_artifact_sufficiency",
})
_EXCLUDED_FIELDS = frozenset({
    "wave_id", "receipt", "receipt_schema_version", "dev_wave_stage",
    "reason_codes",
})
_PATH_DIGEST_FIELDS = frozenset({"jobs_relative_path", "sha256"})
_NOT_ESTABLISHED_FIELDS = frozenset({"evidence_status", "blocked_on"})

CommitResolver = Callable[[Path, str], bool]


class TaskCatalogError(ValueError):
    """An input or generated catalog violates the T-189 contract."""


@dataclass
class _Receipt:
    path: Path
    relative_path: str
    wave_id: str
    raw_sha256: str
    schema_version: object
    stage: object
    prompt_sha256: object
    base_commit: object
    prompt_path: Path | None = None
    prompt_text: str | None = None
    ordinal: int | None = None
    stage_receipt_count: int | None = None


def _fail(label: str, kind: str) -> "Any":
    raise TaskCatalogError(f"{label}: {kind}")


def _object(value: object, fields: frozenset[str], *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        return _fail(label, "must be an object")
    if set(value) != fields:
        return _fail(label, "field set mismatch")
    return value


def _copy_json_value(value: object, *, label: str, depth: int = 1) -> object:
    """Copy canonical JSON data while rejecting float and Decimal values."""
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
        return _fail(label, "float and Decimal values are forbidden")
    if isinstance(value, list):
        return [
            _copy_json_value(item, label=f"{label}[{index}]", depth=depth + 1)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or "\x00" in key:
                return _fail(label, "object key must be a NUL-free string")
            result[key] = _copy_json_value(
                item, label=f"{label}.{key}", depth=depth + 1,
            )
        return result
    return _fail(label, "unsupported JSON value")


def _string(value: object, *, label: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or "\x00" in value:
        return _fail(label, "must be a string")
    return value


def _bool(value: object, *, label: str) -> bool:
    if not isinstance(value, bool):
        return _fail(label, "must be a boolean")
    return value


def _int(value: object, *, label: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        return _fail(label, "must be an integer in range")
    return value


def _relative_path(value: object, *, label: str) -> str:
    text = _string(value, label=label)
    if "\\" in text:
        return _fail(label, "must use POSIX separators")
    path = PurePosixPath(text)
    if path.is_absolute() or text != path.as_posix() or text == "." or ".." in path.parts:
        return _fail(label, "must be a normalized jobs-root relative path")
    return text


def _digest(value: object, *, label: str) -> str:
    text = _string(value, label=label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        return _fail(label, "must be a lowercase sha256")
    return text


def _is_regular_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def _read_strict_json(path: Path, *, label: str) -> object:
    try:
        raw = path.read_bytes()
        return strict_loads(
            raw, label=label, max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    except (OSError, DevWavesError) as exc:
        raise TaskCatalogError(f"{label}: unreadable or not strict JSON") from exc


def _validate_classification_evidence(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        return _fail(label, "must be an object")
    kind = value.get("kind")
    if kind == "worklog-entry":
        item = _object(value, frozenset({"kind", "path", "line"}), label=label)
        return {
            "kind": "worklog-entry",
            "path": _relative_path(item["path"], label=f"{label}.path"),
            "line": _int(item["line"], label=f"{label}.line", minimum=1),
        }
    if kind == "plan-prompt":
        item = _object(
            value, frozenset({"kind", "jobs_relative_path", "sha256"}),
            label=label,
        )
        return {
            "kind": "plan-prompt",
            "jobs_relative_path": _relative_path(
                item["jobs_relative_path"], label=f"{label}.jobs_relative_path",
            ),
            "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
        }
    return _fail(label, "unsupported evidence kind")


def _load_classifications(path: Path) -> dict[str, dict[str, object]]:
    raw_value = _read_strict_json(path, label="classification-artifact")
    copied = _copy_json_value(raw_value, label="classification-artifact")
    top = _object(copied, _CLASSIFICATION_TOP_FIELDS, label="classification-artifact")
    if top["artifact_kind"] != CLASSIFICATION_KIND:
        return _fail("classification-artifact.artifact_kind", "unsupported kind")
    if top["schema_version"] != CLASSIFICATION_SCHEMA_VERSION:
        return _fail("classification-artifact.schema_version", "unsupported version")
    _string(top["classifier"], label="classification-artifact.classifier")
    _relative_path(
        top["criteria_document"], label="classification-artifact.criteria_document",
    )
    _string(top["criteria_version"], label="classification-artifact.criteria_version")
    if _int(
        top["independent_classifiers"],
        label="classification-artifact.independent_classifiers",
    ) != 0:
        return _fail(
            "classification-artifact.independent_classifiers",
            "must be zero for this generation",
        )
    if top["signatures"] is not None:
        return _fail("classification-artifact.signatures", "must be null")
    entries = top["classifications"]
    if not isinstance(entries, list):
        return _fail("classification-artifact.classifications", "must be a list")

    result: dict[str, dict[str, object]] = {}
    for index, raw_entry in enumerate(entries):
        label = f"classification-artifact.classifications[{index}]"
        entry = _object(raw_entry, _CLASSIFICATION_FIELDS, label=label)
        wave_id = _string(entry["wave_id"], label=f"{label}.wave_id")
        if wave_id in result:
            return _fail(f"{label}.wave_id", "duplicate wave classification")
        status = entry["task_type_status"]
        task_type = entry["task_type"]
        if status == "classified":
            if task_type not in TASK_TYPES:
                return _fail(f"{label}.task_type", "unknown classified task type")
        elif status == "unclassified":
            if task_type is not None:
                return _fail(f"{label}.task_type", "must be null when unclassified")
        else:
            return _fail(f"{label}.task_type_status", "unknown status")
        result[wave_id] = {
            "task_type": task_type,
            "task_type_status": status,
            "rule_id": _string(entry["rule_id"], label=f"{label}.rule_id"),
            "tie_break_applied": _bool(
                entry["tie_break_applied"], label=f"{label}.tie_break_applied",
            ),
            "evidence": _validate_classification_evidence(
                entry["evidence"], label=f"{label}.evidence",
            ),
            "rationale": _string(entry["rationale"], label=f"{label}.rationale"),
        }
    return result


def _scan_receipts(jobs_root: Path) -> list[_Receipt]:
    paths = sorted(
        path for path in jobs_root.glob("*/*/receipt.json")
        if _is_regular_file(path)
    )
    receipts: list[_Receipt] = []
    for path in paths:
        relative = path.relative_to(jobs_root).as_posix()
        try:
            raw = path.read_bytes()
            value = strict_loads(
                raw, label=f"receipt:{relative}", max_bytes=DEFAULT_MAX_JSON_BYTES,
            )
        except (OSError, DevWavesError) as exc:
            raise TaskCatalogError(f"receipt:{relative}: unreadable or not strict JSON") from exc
        if not isinstance(value, dict):
            return _fail(f"receipt:{relative}", "top level must be an object")
        receipts.append(_Receipt(
            path=path,
            relative_path=relative,
            wave_id=path.parents[1].name,
            raw_sha256=hashlib.sha256(raw).hexdigest(),
            schema_version=value.get("schema_version"),
            stage=value.get("stage"),
            prompt_sha256=value.get("prompt_sha256"),
            base_commit=value.get("base_commit"),
        ))
    return receipts


def _wave_files_by_digest(jobs_root: Path, wave_id: str) -> dict[str, Path]:
    wave_root = jobs_root / wave_id
    result: dict[str, Path] = {}
    try:
        paths = sorted(
            (path for path in wave_root.iterdir() if _is_regular_file(path)),
            key=lambda path: path.name,
        )
    except OSError:
        return result
    for path in paths:
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha256(raw).hexdigest()
        result.setdefault(digest, path)
    return result


def _recover_prompts(jobs_root: Path, receipts: list[_Receipt]) -> None:
    by_wave: dict[str, list[_Receipt]] = defaultdict(list)
    for receipt in receipts:
        if (receipt.schema_version in SUPPORTED_RECEIPT_SCHEMAS and
                receipt.stage in DEV_WAVE_STAGES):
            by_wave[receipt.wave_id].append(receipt)
    for wave_id, wave_receipts in by_wave.items():
        files = _wave_files_by_digest(jobs_root, wave_id)
        for receipt in wave_receipts:
            if not isinstance(receipt.prompt_sha256, str):
                continue
            path = files.get(receipt.prompt_sha256)
            if path is None:
                continue
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8", errors="strict")
            except (OSError, UnicodeDecodeError):
                continue
            if "\x00" in text:
                continue
            receipt.prompt_path = path
            receipt.prompt_text = text


def _default_commit_resolver(repo_root: Path, base_commit: str) -> bool:
    try:
        completed = subprocess.run(
            [
                "git", "-C", str(repo_root), "rev-parse", "--verify", "--quiet",
                "--end-of-options", f"{base_commit}^{{commit}}",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def _primary_acceptance_receipt(jobs_root: Path, wave_id: str) -> dict[str, object]:
    wave_root = jobs_root / wave_id
    paths = sorted(
        (
            path for path in wave_root.glob("acceptance-receipt*.json")
            if (_is_regular_file(path) and
                not path.name.endswith(".acceptance-red-check.json"))
        ),
        key=lambda path: path.name,
    )
    records: list[dict[str, object]] = []
    for path in paths:
        relative = path.relative_to(jobs_root).as_posix()
        try:
            raw = path.read_bytes()
            value = strict_loads(
                raw, label=f"primary-acceptance:{relative}",
                max_bytes=DEFAULT_MAX_JSON_BYTES,
            )
        except (OSError, DevWavesError) as exc:
            raise TaskCatalogError(
                f"primary-acceptance:{relative}: unreadable or not strict JSON"
            ) from exc
        if not isinstance(value, dict) or not isinstance(value.get("verdict"), str):
            return _fail(f"primary-acceptance:{relative}.verdict", "must be a string")
        records.append({
            "jobs_relative_path": relative,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "verdict": value["verdict"],
        })
    return {"present": bool(records), "records": records}


def _not_established(blocked_on: str) -> dict[str, str]:
    return {"evidence_status": "not-established", "blocked_on": blocked_on}


def _classification_fields(
    wave_id: str, classifications: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    item = classifications.get(wave_id)
    if item is None:
        return {
            "task_type": None,
            "task_type_status": "unclassified",
            "task_type_reason": "not-classified-in-this-generation",
            "rule_id": None,
            "tie_break_applied": None,
            "evidence": None,
            "rationale": None,
        }
    return {
        "task_type": item["task_type"],
        "task_type_status": item["task_type_status"],
        "task_type_reason": None,
        "rule_id": item["rule_id"],
        "tie_break_applied": item["tie_break_applied"],
        "evidence": item["evidence"],
        "rationale": item["rationale"],
    }


def _candidate_row(
    receipt: _Receipt,
    *,
    jobs_root: Path,
    base_commit_resolvable: bool,
    classifications: Mapping[str, dict[str, object]],
    acceptance: dict[str, object],
) -> dict[str, object]:
    assert receipt.schema_version in SUPPORTED_RECEIPT_SCHEMAS
    assert receipt.stage in DEV_WAVE_STAGES
    assert isinstance(receipt.prompt_sha256, str)
    assert isinstance(receipt.base_commit, str)
    assert receipt.prompt_path is not None and receipt.prompt_text is not None
    assert receipt.ordinal is not None and receipt.stage_receipt_count is not None
    prompt_relative = receipt.prompt_path.relative_to(jobs_root).as_posix()
    model_matches = [literal for literal in MODEL_LITERALS if literal in receipt.prompt_text]
    design_markers = [marker for marker in DESIGN_MARKERS if marker in receipt.prompt_text]
    row: dict[str, object] = {
        "wave_id": receipt.wave_id,
        "dev_wave_stage": receipt.stage,
        "receipt_schema_version": receipt.schema_version,
        "receipt": {
            "jobs_relative_path": receipt.relative_path,
            "sha256": receipt.raw_sha256,
        },
        "prompt": {
            "jobs_relative_path": prompt_relative,
            "sha256": receipt.prompt_sha256,
        },
        "base_commit": receipt.base_commit,
        "base_commit_resolvable": base_commit_resolvable,
        "model_slug_contamination": {
            "detected": bool(model_matches),
            "scanned_surfaces": [{
                "surface": "prompt-body",
                "jobs_relative_path": prompt_relative,
                "matches": model_matches,
            }],
        },
        "t189_design_work_markers": design_markers,
        "primary_acceptance_receipt": acceptance,
        "wave_stage_receipt_count": receipt.stage_receipt_count,
        "receipt_ordinal": receipt.ordinal,
        "oracle_finding_count": _not_established("§8 oracle ledger (未実装)"),
        "t189_stage_boundary": _not_established(
            "§5.3 stage2/stage5 replayer 契約 (未登録)"
        ),
        "replay_artifact_sufficiency": _not_established(
            "§5.3 replayer 契約 (未登録)"
        ),
    }
    row.update(_classification_fields(receipt.wave_id, classifications))
    return row


def _display_schema_version(value: object) -> object:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def build_task_catalog(
    jobs_root: Path | str,
    repo_root: Path | str,
    classification_artifact: Path | str,
    *,
    commit_resolver: CommitResolver | None = None,
) -> dict[str, object]:
    """Build a catalog from immutable inputs without writing any file.

    Tests can inject ``commit_resolver``; when supplied, this function never
    invokes git.
    """
    jobs_path = Path(jobs_root)
    repo_path = Path(repo_root)
    classification_path = Path(classification_artifact)
    if not jobs_path.is_dir():
        return _fail("jobs_root", "must be a directory")
    if not repo_path.is_dir():
        return _fail("repo_root", "must be a directory")
    resolver = _default_commit_resolver if commit_resolver is None else commit_resolver
    classifications = _load_classifications(classification_path)
    receipts = _scan_receipts(jobs_path)
    _recover_prompts(jobs_path, receipts)

    stage_receipts: dict[tuple[str, str], list[_Receipt]] = defaultdict(list)
    stages_by_wave: dict[str, set[str]] = defaultdict(set)
    for receipt in receipts:
        if (receipt.schema_version in SUPPORTED_RECEIPT_SCHEMAS and
                receipt.stage in DEV_WAVE_STAGES):
            assert isinstance(receipt.stage, str)
            stage_receipts[(receipt.wave_id, receipt.stage)].append(receipt)
            stages_by_wave[receipt.wave_id].add(receipt.stage)
    for group in stage_receipts.values():
        group.sort(key=lambda item: item.relative_path)
        for ordinal, receipt in enumerate(group):
            receipt.ordinal = ordinal
            receipt.stage_receipt_count = len(group)

    paired_waves = {
        wave_id for wave_id, stages in stages_by_wave.items()
        if stages == set(DEV_WAVE_STAGES)
    }
    prompt_recoverable_waves = {
        wave_id for wave_id in paired_waves
        if all(
            any(
                receipt.prompt_path is not None
                for receipt in stage_receipts[(wave_id, stage)]
            )
            for stage in DEV_WAVE_STAGES
        )
    }

    commit_cache: dict[str, bool] = {}
    acceptance_cache: dict[str, dict[str, object]] = {}
    candidates: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    reason_order = {reason: index for index, reason in enumerate(EXCLUSION_REASONS)}

    for receipt in receipts:
        reasons: list[str] = []
        supported = receipt.schema_version in SUPPORTED_RECEIPT_SCHEMAS
        if not supported:
            reasons.append("unsupported-receipt-schema")
        elif not isinstance(receipt.stage, str):
            reasons.append("invalid-receipt-field")
        elif receipt.stage not in DEV_WAVE_STAGES:
            reasons.append("unsupported-dev-wave-stage")
        else:
            if not isinstance(receipt.prompt_sha256, str) or not isinstance(
                receipt.base_commit, str
            ):
                reasons.append("invalid-receipt-field")
            if receipt.wave_id not in paired_waves:
                reasons.append("missing-paired-stage")
            if (receipt.wave_id not in prompt_recoverable_waves or
                    receipt.prompt_path is None):
                reasons.append("prompt-body-unrecoverable")
            resolvable = False
            if isinstance(receipt.base_commit, str):
                if receipt.base_commit not in commit_cache:
                    try:
                        commit_cache[receipt.base_commit] = bool(
                            resolver(repo_path, receipt.base_commit)
                        )
                    except Exception as exc:
                        raise TaskCatalogError(
                            f"base_commit resolver failed for {receipt.base_commit!r}"
                        ) from exc
                resolvable = commit_cache[receipt.base_commit]
                if not resolvable:
                    reasons.append("base-commit-unresolvable")

            if not reasons:
                if receipt.wave_id not in acceptance_cache:
                    acceptance_cache[receipt.wave_id] = _primary_acceptance_receipt(
                        jobs_path, receipt.wave_id,
                    )
                candidates.append(_candidate_row(
                    receipt,
                    jobs_root=jobs_path,
                    base_commit_resolvable=resolvable,
                    classifications=classifications,
                    acceptance=acceptance_cache[receipt.wave_id],
                ))

        if reasons:
            excluded.append({
                "wave_id": receipt.wave_id,
                "receipt": {
                    "jobs_relative_path": receipt.relative_path,
                    "sha256": receipt.raw_sha256,
                },
                "receipt_schema_version": _display_schema_version(
                    receipt.schema_version,
                ),
                "dev_wave_stage": receipt.stage if isinstance(receipt.stage, str) else None,
                "reason_codes": sorted(set(reasons), key=reason_order.__getitem__),
            })

    stage_order = {stage: index for index, stage in enumerate(DEV_WAVE_STAGES)}
    candidates.sort(key=lambda row: (
        row["wave_id"], stage_order[row["dev_wave_stage"]],
        row["receipt_ordinal"], row["receipt"]["jobs_relative_path"],
    ))
    excluded.sort(key=lambda row: row["receipt"]["jobs_relative_path"])
    type_counts = Counter(
        "unclassified" if row["task_type"] is None else row["task_type"]
        for row in candidates
    )
    artifact: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "counts": {
            "paired_stage_wave_count": len(paired_waves),
            "prompt_recoverable_wave_count": len(prompt_recoverable_waves),
            "candidate_receipt_count": len(candidates),
            "excluded_receipt_count": len(excluded),
            "candidate_receipts_by_task_type": {
                task_type: type_counts[task_type]
                for task_type in (*TASK_TYPES, "unclassified")
            },
        },
        "candidates": candidates,
        "excluded": excluded,
    }
    return validate_task_catalog(artifact)


def _validate_path_digest(value: object, *, label: str) -> dict[str, str]:
    item = _object(value, _PATH_DIGEST_FIELDS, label=label)
    return {
        "jobs_relative_path": _relative_path(
            item["jobs_relative_path"], label=f"{label}.jobs_relative_path",
        ),
        "sha256": _digest(item["sha256"], label=f"{label}.sha256"),
    }


def _validate_not_established(
    value: object, *, label: str, blocked_on: str,
) -> dict[str, str]:
    item = _object(value, _NOT_ESTABLISHED_FIELDS, label=label)
    if item["evidence_status"] != "not-established":
        return _fail(f"{label}.evidence_status", "must be not-established")
    if item["blocked_on"] != blocked_on:
        return _fail(f"{label}.blocked_on", "dependency mismatch")
    return _not_established(blocked_on)


def _validate_contamination(value: object, *, label: str) -> dict[str, object]:
    item = _object(
        value, frozenset({"detected", "scanned_surfaces"}), label=label,
    )
    detected = _bool(item["detected"], label=f"{label}.detected")
    surfaces = item["scanned_surfaces"]
    if not isinstance(surfaces, list) or len(surfaces) != 1:
        return _fail(f"{label}.scanned_surfaces", "must contain prompt-body once")
    surface = _object(
        surfaces[0],
        frozenset({"surface", "jobs_relative_path", "matches"}),
        label=f"{label}.scanned_surfaces[0]",
    )
    if surface["surface"] != "prompt-body":
        return _fail(f"{label}.scanned_surfaces[0].surface", "unsupported surface")
    matches = surface["matches"]
    if (not isinstance(matches, list) or
            matches != [literal for literal in MODEL_LITERALS if literal in matches]):
        return _fail(f"{label}.scanned_surfaces[0].matches", "invalid literal list")
    if detected != bool(matches):
        return _fail(f"{label}.detected", "does not match literal results")
    return {
        "detected": detected,
        "scanned_surfaces": [{
            "surface": "prompt-body",
            "jobs_relative_path": _relative_path(
                surface["jobs_relative_path"],
                label=f"{label}.scanned_surfaces[0].jobs_relative_path",
            ),
            "matches": list(matches),
        }],
    }


def _validate_acceptance(value: object, *, label: str) -> dict[str, object]:
    item = _object(value, frozenset({"present", "records"}), label=label)
    present = _bool(item["present"], label=f"{label}.present")
    records = item["records"]
    if not isinstance(records, list):
        return _fail(f"{label}.records", "must be a list")
    normalized: list[dict[str, object]] = []
    previous_path: str | None = None
    for index, raw_record in enumerate(records):
        record_label = f"{label}.records[{index}]"
        record = _object(
            raw_record,
            frozenset({"jobs_relative_path", "sha256", "verdict"}),
            label=record_label,
        )
        path = _relative_path(
            record["jobs_relative_path"], label=f"{record_label}.jobs_relative_path",
        )
        if previous_path is not None and path <= previous_path:
            return _fail(f"{label}.records", "must be strictly path-sorted")
        previous_path = path
        normalized.append({
            "jobs_relative_path": path,
            "sha256": _digest(record["sha256"], label=f"{record_label}.sha256"),
            "verdict": _string(record["verdict"], label=f"{record_label}.verdict"),
        })
    if present != bool(normalized):
        return _fail(f"{label}.present", "does not match records")
    return {"present": present, "records": normalized}


def _validate_candidate(value: object, *, label: str) -> dict[str, object]:
    item = _object(value, _CANDIDATE_FIELDS, label=label)
    wave_id = _string(item["wave_id"], label=f"{label}.wave_id")
    stage = item["dev_wave_stage"]
    if stage not in DEV_WAVE_STAGES:
        return _fail(f"{label}.dev_wave_stage", "must be plan or author")
    schema_version = item["receipt_schema_version"]
    if schema_version not in SUPPORTED_RECEIPT_SCHEMAS or isinstance(schema_version, bool):
        return _fail(f"{label}.receipt_schema_version", "unsupported version")
    receipt = _validate_path_digest(item["receipt"], label=f"{label}.receipt")
    prompt = _validate_path_digest(item["prompt"], label=f"{label}.prompt")
    base_commit = _string(item["base_commit"], label=f"{label}.base_commit", allow_empty=True)
    resolvable = _bool(
        item["base_commit_resolvable"], label=f"{label}.base_commit_resolvable",
    )
    if not resolvable:
        return _fail(f"{label}.base_commit_resolvable", "candidate commit must resolve")
    count = _int(
        item["wave_stage_receipt_count"],
        label=f"{label}.wave_stage_receipt_count", minimum=1,
    )
    ordinal = _int(item["receipt_ordinal"], label=f"{label}.receipt_ordinal")
    if ordinal >= count:
        return _fail(f"{label}.receipt_ordinal", "outside stage receipt count")
    markers = item["t189_design_work_markers"]
    if (not isinstance(markers, list) or
            markers != [marker for marker in DESIGN_MARKERS if marker in markers]):
        return _fail(f"{label}.t189_design_work_markers", "invalid marker list")
    task_type = item["task_type"]
    status = item["task_type_status"]
    if status == "classified":
        if task_type not in TASK_TYPES:
            return _fail(f"{label}.task_type", "unknown classified task type")
    elif status == "unclassified":
        if task_type is not None:
            return _fail(f"{label}.task_type", "must be null when unclassified")
    else:
        return _fail(f"{label}.task_type_status", "unknown status")
    reason = item["task_type_reason"]
    rule_id = item["rule_id"]
    tie_break = item["tie_break_applied"]
    evidence = item["evidence"]
    rationale = item["rationale"]
    if reason is None:
        normalized_reason = None
        normalized_rule = _string(rule_id, label=f"{label}.rule_id")
        normalized_tie = _bool(tie_break, label=f"{label}.tie_break_applied")
        normalized_evidence = _validate_classification_evidence(
            evidence, label=f"{label}.evidence",
        )
        normalized_rationale = _string(rationale, label=f"{label}.rationale")
    else:
        if (reason != "not-classified-in-this-generation" or task_type is not None or
                status != "unclassified" or rule_id is not None or
                tie_break is not None or evidence is not None or rationale is not None):
            return _fail(f"{label}.task_type_reason", "invalid missing-classification record")
        normalized_reason = reason
        normalized_rule = None
        normalized_tie = None
        normalized_evidence = None
        normalized_rationale = None
    return {
        "wave_id": wave_id,
        "dev_wave_stage": stage,
        "receipt_schema_version": schema_version,
        "receipt": receipt,
        "prompt": prompt,
        "base_commit": base_commit,
        "base_commit_resolvable": True,
        "model_slug_contamination": _validate_contamination(
            item["model_slug_contamination"],
            label=f"{label}.model_slug_contamination",
        ),
        "t189_design_work_markers": list(markers),
        "primary_acceptance_receipt": _validate_acceptance(
            item["primary_acceptance_receipt"],
            label=f"{label}.primary_acceptance_receipt",
        ),
        "wave_stage_receipt_count": count,
        "receipt_ordinal": ordinal,
        "task_type": task_type,
        "task_type_status": status,
        "task_type_reason": normalized_reason,
        "rule_id": normalized_rule,
        "tie_break_applied": normalized_tie,
        "evidence": normalized_evidence,
        "rationale": normalized_rationale,
        "oracle_finding_count": _validate_not_established(
            item["oracle_finding_count"], label=f"{label}.oracle_finding_count",
            blocked_on="§8 oracle ledger (未実装)",
        ),
        "t189_stage_boundary": _validate_not_established(
            item["t189_stage_boundary"], label=f"{label}.t189_stage_boundary",
            blocked_on="§5.3 stage2/stage5 replayer 契約 (未登録)",
        ),
        "replay_artifact_sufficiency": _validate_not_established(
            item["replay_artifact_sufficiency"],
            label=f"{label}.replay_artifact_sufficiency",
            blocked_on="§5.3 replayer 契約 (未登録)",
        ),
    }


def _validate_excluded(value: object, *, label: str) -> dict[str, object]:
    item = _object(value, _EXCLUDED_FIELDS, label=label)
    reasons = item["reason_codes"]
    if (not isinstance(reasons, list) or not reasons or
            reasons != [reason for reason in EXCLUSION_REASONS if reason in reasons]):
        return _fail(f"{label}.reason_codes", "invalid reason list")
    schema_version = item["receipt_schema_version"]
    if not (schema_version is None or isinstance(schema_version, str) or
            (isinstance(schema_version, int) and not isinstance(schema_version, bool))):
        return _fail(f"{label}.receipt_schema_version", "invalid display value")
    stage = item["dev_wave_stage"]
    if stage is not None and not isinstance(stage, str):
        return _fail(f"{label}.dev_wave_stage", "must be a string or null")
    return {
        "wave_id": _string(item["wave_id"], label=f"{label}.wave_id"),
        "receipt": _validate_path_digest(item["receipt"], label=f"{label}.receipt"),
        "receipt_schema_version": schema_version,
        "dev_wave_stage": stage,
        "reason_codes": list(reasons),
    }


def validate_task_catalog(value: object) -> dict[str, object]:
    """Validate the closed catalog schema and return a fresh JSON tree."""
    copied = _copy_json_value(value, label="task_catalog")
    top = _object(copied, _CATALOG_FIELDS, label="task_catalog")
    if top["schema_version"] != SCHEMA_VERSION:
        return _fail("task_catalog.schema_version", "unsupported version")
    counts = _object(top["counts"], _COUNT_FIELDS, label="task_catalog.counts")
    candidates_raw = top["candidates"]
    excluded_raw = top["excluded"]
    if not isinstance(candidates_raw, list) or not isinstance(excluded_raw, list):
        return _fail("task_catalog", "candidates and excluded must be lists")
    candidates = [
        _validate_candidate(item, label=f"task_catalog.candidates[{index}]")
        for index, item in enumerate(candidates_raw)
    ]
    excluded = [
        _validate_excluded(item, label=f"task_catalog.excluded[{index}]")
        for index, item in enumerate(excluded_raw)
    ]
    if counts["candidate_receipt_count"] != len(candidates):
        return _fail("task_catalog.counts.candidate_receipt_count", "count mismatch")
    if counts["excluded_receipt_count"] != len(excluded):
        return _fail("task_catalog.counts.excluded_receipt_count", "count mismatch")
    paired_count = _int(
        counts["paired_stage_wave_count"],
        label="task_catalog.counts.paired_stage_wave_count",
    )
    prompt_count = _int(
        counts["prompt_recoverable_wave_count"],
        label="task_catalog.counts.prompt_recoverable_wave_count",
    )
    if prompt_count > paired_count:
        return _fail("task_catalog.counts", "prompt wave count exceeds paired wave count")
    by_type = _object(
        counts["candidate_receipts_by_task_type"],
        frozenset((*TASK_TYPES, "unclassified")),
        label="task_catalog.counts.candidate_receipts_by_task_type",
    )
    normalized_counts: dict[str, int] = {}
    observed = Counter(
        "unclassified" if row["task_type"] is None else row["task_type"]
        for row in candidates
    )
    for task_type in (*TASK_TYPES, "unclassified"):
        count = _int(
            by_type[task_type],
            label=f"task_catalog.counts.candidate_receipts_by_task_type.{task_type}",
        )
        if count != observed[task_type]:
            return _fail(
                f"task_catalog.counts.candidate_receipts_by_task_type.{task_type}",
                "count mismatch",
            )
        normalized_counts[task_type] = count
    if sum(normalized_counts.values()) != len(candidates):
        return _fail("task_catalog.counts.candidate_receipts_by_task_type", "sum mismatch")

    candidate_paths = [row["receipt"]["jobs_relative_path"] for row in candidates]
    excluded_paths = [row["receipt"]["jobs_relative_path"] for row in excluded]
    if len(candidate_paths + excluded_paths) != len(set(candidate_paths + excluded_paths)):
        return _fail("task_catalog", "duplicate physical receipt path")
    try:
        canonical_bytes({
            "schema_version": SCHEMA_VERSION,
            "counts": {}, "candidates": candidates, "excluded": excluded,
        })
    except (TypeError, ValueError):
        return _fail("task_catalog", "is not canonical JSON data")
    return {
        "schema_version": SCHEMA_VERSION,
        "counts": {
            "paired_stage_wave_count": paired_count,
            "prompt_recoverable_wave_count": prompt_count,
            "candidate_receipt_count": len(candidates),
            "excluded_receipt_count": len(excluded),
            "candidate_receipts_by_task_type": normalized_counts,
        },
        "candidates": candidates,
        "excluded": excluded,
    }


def task_catalog_bytes(value: object) -> bytes:
    """Return canonical UTF-8 JSON with exactly one trailing LF."""
    return canonical_bytes(validate_task_catalog(value)) + b"\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="build the read-only T-189 pre-screen candidate catalog",
    )
    parser.add_argument("jobs_root", type=Path)
    parser.add_argument("repo_root", type=Path)
    parser.add_argument("classification_artifact", type=Path)
    args = parser.parse_args(argv)
    try:
        output = task_catalog_bytes(build_task_catalog(
            args.jobs_root, args.repo_root, args.classification_artifact,
        ))
    except (OSError, TaskCatalogError, TypeError, ValueError) as exc:
        print(f"t189_task_catalog: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "TaskCatalogError", "build_task_catalog", "main", "task_catalog_bytes",
    "validate_task_catalog",
]
