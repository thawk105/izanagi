# -*- coding: utf-8 -*-
"""T-080 legacy freeze 移行 receipt の生成・検証 core。

この module は一回限りの移行専用である。過去 snapshot の Python は実行せず、draft
生成時だけ clean な移行基準 worktree 上の現行 builder/verifier を実走する。発効後の
gate は receipt の byte pin、移行基準 commit の blob closure、live ccbench pin、live
unknownness scan だけを検査する。
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RECEIPT_REL = "output/t080-migration/legacy-freeze-repin.receipt.json"
DRAFT_REL = "output/t080-migration/legacy-freeze-repin.receipt.draft.json"
KNOWN_AXES_REL = "output/s1-freeze/known_axes_freeze.json"
HOLDOUT_REL = "output/s8b-freeze/holdout_freeze.json"
CCBENCH_REL = "external/ccbench"

SCHEMA_VERSION = "izanagi-t080-legacy-freeze-repin/v1"
OBSERVATION_SCHEMA_VERSION = "izanagi-t080-freeze-migration-observation/v1"
MIGRATION_ID = "T-080"

KNOWN_AXES_RAW_SHA256 = "354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516"
HOLDOUT_RAW_SHA256 = "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"
KNOWN_AXES_RECORDED_HEAD = "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1"
HOLDOUT_RECORDED_HEAD = "2e20d441aaf7ae267e941ecda09e4b53050943cf"

# T-078 の production literal。fixture 本体は別単位が所有する。
POSITIVE_CONTROL_PATH = "orchestrator/tests/data/freeze_holdout_positive_control_v1.txt"
POSITIVE_CONTROL_ROOT_KEY = "positive-control/rr50/v1"
POSITIVE_CONTROL_SHA256 = "caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7"

RECEIPT_PREFIX = "migration-receipt-verify"
KNOWN_PREFIX = "known-axes-freeze-verify"
HOLDOUT_PREFIX = "holdout-freeze-verify"

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CONFIRMED_BY_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

_TOP_KEYS = frozenset({
    "schema_version", "migration_id", "migration_basis_commit", "artifacts",
    "source_repins", "metadata_fields", "reconstruction", "repin_report",
    "confirmed_by", "confirmed_at",
})
_ARTIFACT_KEYS = frozenset({"path", "raw_sha256", "recorded_frozen_at_head"})
_REPIN_KEYS = frozenset({
    "artifact", "json_pointer", "path", "recorded_sha256", "migration_blob_sha256",
})
_METADATA_KEYS = _REPIN_KEYS | {"disposition"}
_REPORT_KEYS = frozenset({
    "artifact", "json_pointer", "path", "recorded_sha256", "migration_blob_sha256",
    "provenance", "diff_summary",
})


@dataclasses.dataclass(frozen=True)
class RepinSpec:
    artifact: str
    json_pointer: str
    path: str
    recorded_sha256: str


_KNOWN_REPIN_ROWS = (
    ("/entries/balanced/ident_all/sources/3/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("/entries/balanced/sort_best/sources/5/sha256", "orchestrator/campaign/s6_sort_sweep.py", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("/entries/balanced/sort_best/sources/6/sha256", "orchestrator/campaign/p3_s4_loop_sort.py", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("/entries/balanced/system_gate/sources/4/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("/entries/read-heavy/ident_all/sources/3/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("/entries/read-heavy/sort_best/sources/2/sha256", "orchestrator/campaign/s6_sort_sweep.py", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("/entries/read-heavy/sort_best/sources/3/sha256", "orchestrator/campaign/p3_s4_loop_sort.py", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("/entries/read-heavy/system_gate/sources/4/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("/entries/write-heavy/ident_all/sources/3/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("/entries/write-heavy/sort_best/sources/5/sha256", "orchestrator/campaign/s6_sort_sweep.py", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("/entries/write-heavy/sort_best/sources/6/sha256", "orchestrator/campaign/p3_s4_loop_sort.py", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("/entries/write-heavy/system_gate/sources/4/sha256", "orchestrator/campaign/s8a_trigger_sweep.py", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
)
SOURCE_REPIN_SPECS: Tuple[RepinSpec, ...] = tuple(
    RepinSpec("known_axes", pointer, path, digest)
    for pointer, path, digest in _KNOWN_REPIN_ROWS
) + (
    RepinSpec(
        "holdout", "/design_source/sha256", "docs/phase3-8b-descriptor-design.md",
        "1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d",
    ),
)
METADATA_SPECS: Tuple[RepinSpec, ...] = (
    RepinSpec(
        "known_axes", "/generator/sha256",
        "orchestrator/campaign/s1_known_axes_freeze.py",
        "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0",
    ),
    RepinSpec(
        "holdout", "/generator/sha256",
        "orchestrator/campaign/s8b_holdout_freeze.py",
        "1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f",
    ),
)


class MigrationError(RuntimeError):
    """予期された fail-closed 拒否。``reason`` は一ドット grammar。"""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"[{reason}] {detail}" if detail else f"[{reason}]")


@dataclasses.dataclass(frozen=True)
class CommitGraph:
    commits: Tuple[str, ...]
    parents: Mapping[str, Tuple[str, ...]]


@dataclasses.dataclass(frozen=True)
class AncestryResult:
    status: str
    recorded: str
    observed: Optional[str]
    refusal_reason: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class ReceiptResolution:
    state: str
    refusals: Tuple[str, ...]
    t080_freeze_migration_observation: Optional[Mapping[str, object]]
    validation_head: str
    introduction_commit: Optional[str] = None
    receipt: Optional[Mapping[str, object]] = None


@dataclasses.dataclass(frozen=True)
class AdapterResult:
    refusals: Tuple[str, ...]
    t080_freeze_migration_observation: Optional[Mapping[str, object]]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reject_constant(token: str):
    raise MigrationError("receipt.schema_invalid", f"非数値定数を含む: {token}")


def _no_duplicate_keys(pairs):
    out: Dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise MigrationError("receipt.schema_invalid", f"duplicate key: {key!r}")
        out[key] = value
    return out


def _strict_load(raw: bytes, *, what: str = "JSON") -> dict:
    """UTF-8、duplicate key、非有限数、top-level object を厳格検査する。"""
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise MigrationError("receipt.schema_invalid", f"{what} が UTF-8 でない") from exc
    try:
        value = json.loads(
            text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_keys,
        )
    except MigrationError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise MigrationError("receipt.schema_invalid", f"{what} を strict parse できない") from exc
    if not isinstance(value, dict):
        raise MigrationError("receipt.schema_invalid", f"{what} top-level が object でない")
    return value


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MigrationError("receipt.schema_invalid", "canonical JSON に変換できない") from exc


def _load_canonical(raw: bytes, *, what: str = "receipt") -> dict:
    doc = _strict_load(raw, what=what)
    if _canonical_bytes(doc) != raw:
        raise MigrationError("receipt.canonical_mismatch", f"{what} が canonical bytes でない")
    return doc


def _pointer_tokens(pointer: str) -> Tuple[str, ...]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise MigrationError("receipt.repin_invalid", "json_pointer は / で始まらなければならない")
    tokens: List[str] = []
    for raw in pointer[1:].split("/"):
        index = 0
        while index < len(raw):
            if raw[index] == "~":
                if index + 1 >= len(raw) or raw[index + 1] not in "01":
                    raise MigrationError("receipt.repin_invalid", f"RFC 6901 escape が不正: {pointer}")
                index += 2
            else:
                index += 1
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tuple(tokens)


def _encode_pointer(tokens: Sequence[str]) -> str:
    return "/" + "/".join(token.replace("~", "~0").replace("/", "~1") for token in tokens)


def _resolve_pointer(value, pointer: str):
    tokens = _pointer_tokens(pointer)
    if _encode_pointer(tokens) != pointer:
        raise MigrationError("receipt.repin_invalid", f"json_pointer が canonical でない: {pointer}")
    current = value
    for token in tokens:
        if isinstance(current, Mapping):
            if token not in current:
                raise MigrationError("receipt.repin_invalid", f"json_pointer が存在しない: {pointer}")
            current = current[token]
        elif isinstance(current, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise MigrationError("receipt.repin_invalid", f"array index が不正: {pointer}")
            index = int(token)
            if index >= len(current):
                raise MigrationError("receipt.repin_invalid", f"array index が範囲外: {pointer}")
            current = current[index]
        else:
            raise MigrationError("receipt.repin_invalid", f"scalar の配下を参照した: {pointer}")
    return current


def _set_pointer(value, pointer: str, replacement: object) -> None:
    tokens = _pointer_tokens(pointer)
    if not tokens or _encode_pointer(tokens) != pointer:
        raise MigrationError("receipt.repin_invalid", f"置換 pointer が不正: {pointer}")
    parent = value
    for token in tokens[:-1]:
        if isinstance(parent, MutableMapping):
            parent = parent[token]
        elif isinstance(parent, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            parent = parent[int(token)]
        else:
            raise MigrationError("receipt.repin_invalid", f"置換 pointer が到達不能: {pointer}")
    last = tokens[-1]
    if isinstance(parent, MutableMapping) and last in parent:
        parent[last] = replacement
    elif isinstance(parent, list) and re.fullmatch(r"0|[1-9][0-9]*", last) and int(last) < len(parent):
        parent[int(last)] = replacement
    else:
        raise MigrationError("receipt.repin_invalid", f"置換 pointer が到達不能: {pointer}")


def _exact_keys(value: object, keys: frozenset, reason: str, label: str) -> Mapping:
    if not isinstance(value, Mapping) or frozenset(value) != keys:
        raise MigrationError(reason, f"{label} の keys が不一致")
    return value


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _require_hex(value: object, regex: re.Pattern, reason: str, label: str) -> str:
    if not isinstance(value, str) or regex.fullmatch(value) is None:
        raise MigrationError(reason, f"{label} の形式が不正")
    return value


def _require_utc(value: object) -> str:
    if not isinstance(value, str) or _UTC_RE.fullmatch(value) is None:
        raise MigrationError("receipt.confirmation_invalid", "confirmed_at が UTC 秒精度でない")
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise MigrationError("receipt.confirmation_invalid", "confirmed_at が実在日時でない") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise MigrationError("receipt.confirmation_invalid", "confirmed_at roundtrip に失敗")
    return value


def validate_receipt_structure(doc: Mapping[str, object]) -> None:
    """自由文を持たない閉じた構造だけを検査する。

    固定 path/hash の意味照合は ``validate_receipt_schema`` が続けて行う。J8 の scan
    二重負例はこの境界を通過した後、固定値照合と live scan の双方で拒否できる。
    """
    _exact_keys(doc, _TOP_KEYS, "receipt.schema_invalid", "top-level")
    if doc.get("schema_version") != SCHEMA_VERSION or doc.get("migration_id") != MIGRATION_ID:
        raise MigrationError("receipt.schema_invalid", "schema literal が不正")
    _require_hex(doc.get("migration_basis_commit"), _SHA1_RE, "receipt.basis_invalid", "basis")
    artifacts = _exact_keys(
        doc.get("artifacts"), frozenset({"known_axes", "holdout"}),
        "receipt.schema_invalid", "artifacts",
    )
    for name in ("known_axes", "holdout"):
        record = _exact_keys(artifacts.get(name), _ARTIFACT_KEYS, "receipt.schema_invalid", name)
        if not _canonical_relative(record.get("path")):
            raise MigrationError("receipt.schema_invalid", f"artifacts.{name}.path が不正")
        _require_hex(record.get("raw_sha256"), _SHA256_RE, "receipt.schema_invalid", "artifact raw")
        _require_hex(record.get("recorded_frozen_at_head"), _SHA1_RE, "receipt.schema_invalid", "recorded head")
    for field, count, keys in (
        ("source_repins", 13, _REPIN_KEYS), ("metadata_fields", 2, _METADATA_KEYS),
    ):
        records = doc.get(field)
        if not isinstance(records, list) or len(records) != count:
            raise MigrationError("receipt.schema_invalid", f"{field} の件数が不正")
        for index, record in enumerate(records):
            record = _exact_keys(record, keys, "receipt.schema_invalid", f"{field}[{index}]")
            if record.get("artifact") not in {"known_axes", "holdout"}:
                raise MigrationError("receipt.schema_invalid", f"{field}.artifact が不正")
            _pointer_tokens(record.get("json_pointer"))
            if not _canonical_relative(record.get("path")):
                raise MigrationError("receipt.schema_invalid", f"{field}.path が不正")
            _require_hex(record.get("recorded_sha256"), _SHA256_RE, "receipt.schema_invalid", "recorded hash")
            _require_hex(record.get("migration_blob_sha256"), _SHA256_RE, "receipt.schema_invalid", "migration hash")
            if field == "metadata_fields" and record.get("disposition") != "metadata-only":
                raise MigrationError("receipt.schema_invalid", "metadata disposition が不正")
    reconstruction = _exact_keys(
        doc.get("reconstruction"), frozenset({"known_axes", "holdout"}),
        "receipt.schema_invalid", "reconstruction",
    )
    for name, keys in (
        ("known_axes", frozenset({"status", "projected_document_sha256", "rebuilt_document_sha256"})),
        ("holdout", frozenset({"status", "projected_document_sha256", "live_scan_sha256"})),
    ):
        record = _exact_keys(reconstruction.get(name), keys, "receipt.schema_invalid", f"reconstruction.{name}")
        if record.get("status") != "pass":
            raise MigrationError("receipt.schema_invalid", "reconstruction status が不正")
        for key, value in record.items():
            if key != "status":
                _require_hex(value, _SHA256_RE, "receipt.schema_invalid", f"reconstruction.{name}.{key}")
    report = doc.get("repin_report")
    if not isinstance(report, list) or len(report) != 13:
        raise MigrationError("receipt.schema_invalid", "repin_report の件数が不正")
    for index, entry in enumerate(report):
        entry = _exact_keys(entry, _REPORT_KEYS, "receipt.schema_invalid", f"repin_report[{index}]")
        if entry.get("artifact") not in {"known_axes", "holdout"}:
            raise MigrationError("receipt.schema_invalid", "repin_report.artifact が不正")
        _pointer_tokens(entry.get("json_pointer"))
        if not _canonical_relative(entry.get("path")):
            raise MigrationError("receipt.schema_invalid", "repin_report.path が不正")
        _require_hex(entry.get("recorded_sha256"), _SHA256_RE, "receipt.schema_invalid", "report recorded")
        _require_hex(entry.get("migration_blob_sha256"), _SHA256_RE, "receipt.schema_invalid", "report migration")
        provenance = _exact_keys(
            entry.get("provenance"), frozenset({"status", "commit", "distance_from_basis"}),
            "receipt.schema_invalid", "provenance",
        )
        if provenance.get("status") == "provenance_resolved":
            _require_hex(provenance.get("commit"), _SHA1_RE, "receipt.schema_invalid", "provenance commit")
            if not _is_nonnegative_int(provenance.get("distance_from_basis")):
                raise MigrationError("receipt.schema_invalid", "provenance distance が不正")
        elif provenance.get("status") == "provenance_unverified":
            if provenance.get("commit") is not None or provenance.get("distance_from_basis") is not None:
                raise MigrationError("receipt.schema_invalid", "unverified provenance が不正")
        else:
            raise MigrationError("receipt.schema_invalid", "provenance status が不正")
        summary = _exact_keys(
            entry.get("diff_summary"),
            frozenset({"status", "path", "old_line_count", "new_line_count", "added_lines", "deleted_lines"}),
            "receipt.schema_invalid", "diff_summary",
        )
        if not _canonical_relative(summary.get("path")):
            raise MigrationError("receipt.schema_invalid", "diff_summary.path が不正")
        if summary.get("status") == "diff_resolved":
            if any(not _is_nonnegative_int(summary.get(key)) for key in (
                "old_line_count", "new_line_count", "added_lines", "deleted_lines",
            )):
                raise MigrationError("receipt.schema_invalid", "diff_resolved 数値が不正")
        elif summary.get("status") == "diff_unverified":
            if not _is_nonnegative_int(summary.get("new_line_count")) or any(
                summary.get(key) is not None for key in ("old_line_count", "added_lines", "deleted_lines")
            ):
                raise MigrationError("receipt.schema_invalid", "diff_unverified 数値が不正")
        else:
            raise MigrationError("receipt.schema_invalid", "diff_summary status が不正")
    confirmed_by, confirmed_at = doc.get("confirmed_by"), doc.get("confirmed_at")
    if (confirmed_by is None) != (confirmed_at is None):
        raise MigrationError("receipt.confirmation_invalid", "confirmation の null が混在")
    if confirmed_by is not None:
        if not isinstance(confirmed_by, str) or _CONFIRMED_BY_RE.fullmatch(confirmed_by) is None:
            raise MigrationError("receipt.confirmation_invalid", "confirmed_by の形式が不正")
        _require_utc(confirmed_at)


def validate_receipt_schema(doc: Mapping[str, object], *, confirmation: str = "either") -> None:
    """receipt の閉じた構造 schema と固定値・cross-field を検査する。"""
    validate_receipt_structure(doc)
    if doc.get("schema_version") != SCHEMA_VERSION or doc.get("migration_id") != MIGRATION_ID:
        raise MigrationError("receipt.schema_invalid", "schema_version/migration_id 不一致")
    _require_hex(doc.get("migration_basis_commit"), _SHA1_RE, "receipt.basis_invalid", "basis")

    artifacts = _exact_keys(
        doc.get("artifacts"), frozenset({"known_axes", "holdout"}),
        "receipt.schema_invalid", "artifacts",
    )
    expected_artifacts = {
        "known_axes": (KNOWN_AXES_REL, KNOWN_AXES_RAW_SHA256, KNOWN_AXES_RECORDED_HEAD),
        "holdout": (HOLDOUT_REL, HOLDOUT_RAW_SHA256, HOLDOUT_RECORDED_HEAD),
    }
    for name, expected in expected_artifacts.items():
        record = _exact_keys(
            artifacts.get(name), _ARTIFACT_KEYS, "receipt.schema_invalid", f"artifacts.{name}",
        )
        if tuple(record.get(key) for key in ("path", "raw_sha256", "recorded_frozen_at_head")) != expected:
            raise MigrationError("receipt.schema_invalid", f"artifacts.{name} 固定値不一致")

    repins = doc.get("source_repins")
    if not isinstance(repins, list) or len(repins) != len(SOURCE_REPIN_SPECS):
        raise MigrationError("receipt.repin_invalid", "source_repins は exact 13 件でなければならない")
    for index, (record, spec) in enumerate(zip(repins, SOURCE_REPIN_SPECS)):
        record = _exact_keys(record, _REPIN_KEYS, "receipt.repin_invalid", f"source_repins[{index}]")
        fixed = (record.get("artifact"), record.get("json_pointer"), record.get("path"), record.get("recorded_sha256"))
        if fixed != (spec.artifact, spec.json_pointer, spec.path, spec.recorded_sha256):
            raise MigrationError("receipt.repin_invalid", f"source_repins[{index}] 固定値不一致")
        _require_hex(record.get("migration_blob_sha256"), _SHA256_RE, "receipt.repin_invalid", "migration blob")
        _pointer_tokens(spec.json_pointer)

    metadata = doc.get("metadata_fields")
    if not isinstance(metadata, list) or len(metadata) != len(METADATA_SPECS):
        raise MigrationError("receipt.repin_invalid", "metadata_fields は exact 2 件でなければならない")
    for index, (record, spec) in enumerate(zip(metadata, METADATA_SPECS)):
        record = _exact_keys(record, _METADATA_KEYS, "receipt.repin_invalid", f"metadata_fields[{index}]")
        fixed = (record.get("artifact"), record.get("json_pointer"), record.get("path"), record.get("recorded_sha256"))
        if fixed != (spec.artifact, spec.json_pointer, spec.path, spec.recorded_sha256):
            raise MigrationError("receipt.repin_invalid", f"metadata_fields[{index}] 固定値不一致")
        if record.get("disposition") != "metadata-only":
            raise MigrationError("receipt.repin_invalid", "metadata disposition 不一致")
        _require_hex(record.get("migration_blob_sha256"), _SHA256_RE, "receipt.repin_invalid", "metadata blob")

    reconstruction = _exact_keys(
        doc.get("reconstruction"), frozenset({"known_axes", "holdout"}),
        "receipt.reconstruction_invalid", "reconstruction",
    )
    known = _exact_keys(
        reconstruction.get("known_axes"),
        frozenset({"status", "projected_document_sha256", "rebuilt_document_sha256"}),
        "receipt.reconstruction_invalid", "reconstruction.known_axes",
    )
    holdout = _exact_keys(
        reconstruction.get("holdout"),
        frozenset({"status", "projected_document_sha256", "live_scan_sha256"}),
        "receipt.reconstruction_invalid", "reconstruction.holdout",
    )
    if known.get("status") != "pass" or holdout.get("status") != "pass":
        raise MigrationError("receipt.reconstruction_invalid", "reconstruction status が pass でない")
    for label, value in (
        ("known projected", known.get("projected_document_sha256")),
        ("known rebuilt", known.get("rebuilt_document_sha256")),
        ("holdout projected", holdout.get("projected_document_sha256")),
        ("holdout scan", holdout.get("live_scan_sha256")),
    ):
        _require_hex(value, _SHA256_RE, "receipt.reconstruction_invalid", label)
    if known.get("projected_document_sha256") != known.get("rebuilt_document_sha256"):
        raise MigrationError("receipt.reconstruction_invalid", "known projected/rebuilt hash 不一致")

    report = doc.get("repin_report")
    if not isinstance(report, list) or len(report) != len(SOURCE_REPIN_SPECS):
        raise MigrationError("receipt.repin_invalid", "repin_report は exact 13 件でなければならない")
    for index, (entry, repin) in enumerate(zip(report, repins)):
        entry = _exact_keys(entry, _REPORT_KEYS, "receipt.repin_invalid", f"repin_report[{index}]")
        for key in ("artifact", "json_pointer", "path", "recorded_sha256", "migration_blob_sha256"):
            if entry.get(key) != repin.get(key):
                raise MigrationError("receipt.repin_invalid", f"repin_report[{index}].{key} cross-field 不一致")
        provenance = _exact_keys(
            entry.get("provenance"), frozenset({"status", "commit", "distance_from_basis"}),
            "receipt.repin_invalid", "provenance",
        )
        pstatus = provenance.get("status")
        if pstatus == "provenance_resolved":
            _require_hex(provenance.get("commit"), _SHA1_RE, "receipt.repin_invalid", "provenance commit")
            if not _is_nonnegative_int(provenance.get("distance_from_basis")):
                raise MigrationError("receipt.repin_invalid", "provenance distance が不正")
        elif pstatus == "provenance_unverified":
            if provenance.get("commit") is not None or provenance.get("distance_from_basis") is not None:
                raise MigrationError("receipt.repin_invalid", "unverified provenance に値がある")
        else:
            raise MigrationError("receipt.repin_invalid", "provenance status が不正")
        summary = _exact_keys(
            entry.get("diff_summary"),
            frozenset({"status", "path", "old_line_count", "new_line_count", "added_lines", "deleted_lines"}),
            "receipt.repin_invalid", "diff_summary",
        )
        if summary.get("path") != repin.get("path"):
            raise MigrationError("receipt.repin_invalid", "diff_summary.path cross-field 不一致")
        if summary.get("status") == "diff_resolved":
            for key in ("old_line_count", "new_line_count", "added_lines", "deleted_lines"):
                if not _is_nonnegative_int(summary.get(key)):
                    raise MigrationError("receipt.repin_invalid", f"diff_summary.{key} が不正")
        elif summary.get("status") == "diff_unverified":
            if summary.get("new_line_count") is None or not _is_nonnegative_int(summary.get("new_line_count")):
                raise MigrationError("receipt.repin_invalid", "diff_unverified new_line_count が不正")
            for key in ("old_line_count", "added_lines", "deleted_lines"):
                if summary.get(key) is not None:
                    raise MigrationError("receipt.repin_invalid", f"diff_unverified {key} は null でない")
        else:
            raise MigrationError("receipt.repin_invalid", "diff_summary status が不正")
        if (pstatus == "provenance_resolved") != (summary.get("status") == "diff_resolved"):
            raise MigrationError("receipt.repin_invalid", "provenance/diff status が不整合")

    confirmed_by, confirmed_at = doc.get("confirmed_by"), doc.get("confirmed_at")
    if (confirmed_by is None) != (confirmed_at is None):
        raise MigrationError("receipt.confirmation_invalid", "confirmation の null が混在")
    if confirmed_by is None:
        if confirmation == "active":
            raise MigrationError("receipt.confirmation_invalid", "active receipt の confirmation が null")
    else:
        if confirmation == "draft":
            raise MigrationError("receipt.confirmation_invalid", "draft の confirmation が non-null")
        if not isinstance(confirmed_by, str) or _CONFIRMED_BY_RE.fullmatch(confirmed_by) is None:
            raise MigrationError("receipt.confirmation_invalid", "confirmed_by の形式が不正")
        _require_utc(confirmed_at)


def _git_env() -> Dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


_GIT_HARDEN = ("-c", "core.useReplaceRefs=false")


def _git(args: Sequence[str], root: Path, *, stdin: Optional[bytes] = None) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *_GIT_HARDEN, *args], cwd=root, env=_git_env(), input=stdin,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raw = getattr(exc, "stderr", b"") or str(exc).encode("utf-8", "replace")
        detail = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        raise MigrationError("receipt.git_error", f"git {' '.join(args)}: {detail.strip()}") from exc
    return completed.stdout


def _git_text(args: Sequence[str], root: Path, *, stdin: Optional[bytes] = None) -> str:
    try:
        return _git(args, root, stdin=stdin).decode("utf-8", "strict").strip()
    except UnicodeError as exc:
        raise MigrationError("receipt.git_error", "git 出力が UTF-8 でない") from exc


def _git_rc(args: Sequence[str], root: Path) -> subprocess.CompletedProcess:
    """merge-base 用。rc=1 を潰さず、起動不能だけを例外にする。"""
    try:
        return subprocess.run(
            ["git", *_GIT_HARDEN, *args], cwd=root, env=_git_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError as exc:
        raise MigrationError("receipt.git_error", f"git {' '.join(args)} を起動できない") from exc


def _git_path(root: Path, name: str) -> Path:
    raw = _git_text(["rev-parse", "--git-path", name], root)
    path = Path(raw)
    return path if path.is_absolute() else root / path


def _capture_head(root: Path) -> str:
    root = Path(root)
    if _git_text(["rev-parse", "--is-shallow-repository"], root) == "true":
        raise MigrationError("receipt.git_error", "shallow repository は拒否する")
    if _git_text(["for-each-ref", "--format=%(refname)", "refs/replace/"], root):
        raise MigrationError("receipt.git_error", "replace refs は拒否する")
    for name in ("info/grafts", "objects/info/alternates"):
        path = _git_path(root, name)
        try:
            exists = path.exists() or path.is_symlink()
        except OSError as exc:
            raise MigrationError("receipt.git_error", f"{name} を検査できない") from exc
        if exists:
            raise MigrationError("receipt.git_error", f"{name} は拒否する")
    head = _git_text(["rev-parse", "HEAD"], root)
    _require_hex(head, _SHA1_RE, "receipt.git_error", "HEAD")
    if _object_type(head, root) != "commit":
        raise MigrationError("receipt.git_error", "HEAD が commit でない")
    return head


def _object_type(oid: str, root: Path) -> Optional[str]:
    out = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"], root,
        stdin=(oid + "\n").encode("ascii", "strict"),
    ).decode("utf-8", "strict").strip()
    tokens = out.split()
    if tokens and tokens[-1] == "missing":
        return None
    if len(tokens) == 2 and _SHA1_RE.fullmatch(tokens[0]):
        return tokens[1]
    raise MigrationError("receipt.git_error", f"object type 応答が不正: {out!r}")


def _commit_graph(head: str, root: Path) -> CommitGraph:
    out = _git_text(["rev-list", "--parents", head], root)
    commits: List[str] = []
    parents: Dict[str, Tuple[str, ...]] = {}
    for line in out.splitlines():
        parts = line.split()
        if not parts or any(_SHA1_RE.fullmatch(value) is None for value in parts):
            raise MigrationError("receipt.git_error", "rev-list 出力が不正")
        commits.append(parts[0])
        parents[parts[0]] = tuple(parts[1:])
    if not commits or commits[0] != head:
        raise MigrationError("receipt.git_error", "reachable graph が HEAD から始まらない")
    return CommitGraph(tuple(commits), parents)


def _blob_oid_by_commit(graph: CommitGraph, path: str, root: Path) -> Dict[str, Optional[str]]:
    if not graph.commits:
        return {}
    stdin = "".join(f"{commit}:{path}\n" for commit in graph.commits).encode("utf-8")
    lines = _git(["cat-file", "--batch-check"], root, stdin=stdin).decode("utf-8", "strict").splitlines()
    if len(lines) != len(graph.commits):
        raise MigrationError("receipt.git_error", "batch-check の件数が不一致")
    result: Dict[str, Optional[str]] = {}
    for commit, line in zip(graph.commits, lines):
        tokens = line.split()
        if tokens and tokens[-1] == "missing":
            result[commit] = None
        elif len(tokens) >= 2 and _SHA1_RE.fullmatch(tokens[0]) and tokens[1] == "blob":
            result[commit] = tokens[0]
        else:
            raise MigrationError("receipt.history_mutated", f"{path} が blob でない: {commit}")
    return result


def _blob_oid_at(commit: str, path: str, root: Path) -> Optional[str]:
    graph = CommitGraph((commit,), {commit: ()})
    return _blob_oid_by_commit(graph, path, root)[commit]


def _blob_bytes_at(commit: str, path: str, root: Path) -> bytes:
    oid = _blob_oid_at(commit, path, root)
    if oid is None:
        raise MigrationError("receipt.basis_invalid", f"{commit}:{path} が存在しない")
    return _git(["cat-file", "blob", oid], root)


def _tree_entry(commit: str, path: str, root: Path) -> Tuple[str, str, str]:
    out = _git(["ls-tree", "-z", commit, "--", path], root)
    records = [record for record in out.split(b"\0") if record]
    if len(records) != 1:
        raise MigrationError("receipt.basis_invalid", f"{commit}:{path} tree entry が一意でない")
    try:
        header, found = records[0].split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        found_text = found.decode("utf-8", "strict")
    except (ValueError, UnicodeError) as exc:
        raise MigrationError("receipt.git_error", "ls-tree 出力が不正") from exc
    if found_text != path or _SHA1_RE.fullmatch(oid) is None:
        raise MigrationError("receipt.basis_invalid", f"{path} tree entry が不正")
    return mode, kind, oid


def _basis_blob(commit: str, path: str, root: Path, *, ccbench_pin: Optional[str] = None) -> bytes:
    prefix = CCBENCH_REL + "/"
    if path.startswith(prefix):
        if ccbench_pin is None:
            raise MigrationError("known_axes.ccbench_gitlink", "ccbench pin がない")
        return _git(["cat-file", "blob", f"{ccbench_pin}:{path[len(prefix):]}"], root / CCBENCH_REL)
    return _blob_bytes_at(commit, path, root)


def _classify_ancestry(recorded: str, validation_head: str, root: Path, *, artifact: str) -> AncestryResult:
    prefix = "known_axes" if artifact == "known_axes" else "holdout"
    try:
        kind = _object_type(recorded, root)
    except MigrationError:
        return AncestryResult("git-error", recorded, None, f"{prefix}.ancestry_git_error")
    if kind is None:
        return AncestryResult("missing-commit", recorded, None)
    if kind != "commit":
        return AncestryResult("object-type-error", recorded, kind, f"{prefix}.ancestry_object_type")
    try:
        completed = _git_rc(["merge-base", "--is-ancestor", recorded, validation_head], root)
    except MigrationError:
        return AncestryResult("git-error", recorded, None, f"{prefix}.ancestry_git_error")
    if completed.returncode == 0:
        return AncestryResult("ancestor", recorded, validation_head)
    if completed.returncode == 1:
        return AncestryResult("not-ancestor", recorded, validation_head)
    return AncestryResult("git-error", recorded, None, f"{prefix}.ancestry_git_error")


def _read_nofollow(root: Path, rel: str) -> bytes:
    path = root / rel
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        before = path.lstat()
        fd = os.open(path, flags)
        try:
            after = os.fstat(fd)
            if not stat.S_ISREG(after.st_mode) or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                raise MigrationError("receipt.invalid", f"{rel} が同一 regular file でない")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)
    except MigrationError:
        raise
    except OSError as exc:
        raise MigrationError("receipt.invalid", f"{rel} を nofollow で読めない") from exc


def _worktree_presence(root: Path, rel: str) -> str:
    try:
        st = (root / rel).lstat()
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "error"
    return "regular" if stat.S_ISREG(st.st_mode) else "nonregular"


def _introduction_candidates(graph: CommitGraph, oids: Mapping[str, Optional[str]]) -> Tuple[str, ...]:
    return tuple(
        commit for commit in graph.commits
        if oids.get(commit) is not None
        and all(oids.get(parent) is None for parent in graph.parents.get(commit, ()))
    )


def _descendants_of(graph: CommitGraph, ancestor: str) -> frozenset[str]:
    children: Dict[str, List[str]] = {commit: [] for commit in graph.commits}
    for commit, parents in graph.parents.items():
        for parent in parents:
            if parent in children:
                children[parent].append(commit)
    seen = {ancestor}
    queue = deque([ancestor])
    while queue:
        current = queue.popleft()
        for child in children.get(current, ()):
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return frozenset(seen)


def _history_touches_path(commit: str, path: str, root: Path) -> bool:
    out = _git_text(
        [
            "diff-tree", "--root", "--no-commit-id", "--name-status", "-r",
            "-M", "-C", "--find-copies-harder", commit,
        ], root,
    )
    for line in out.splitlines():
        fields = line.split("\t")
        if not fields:
            continue
        status_code = fields[0][:1]
        if status_code in {"M", "D", "R", "C", "T"} and path in fields[1:]:
            return True
    return False


def _raw_ai_agent_lines(message: str) -> List[str]:
    return [
        line for line in message.split("\n")
        if ":" in line and line.split(":", 1)[0].strip().lower() == "ai-agent"
    ]


def _is_none_commit(commit: str, root: Path) -> bool:
    message = _git(["show", "-s", "--format=%B", commit], root).decode("utf-8", "strict")
    raw_lines = _raw_ai_agent_lines(message)
    if raw_lines != ["AI-Agent: none"]:
        return False
    parsed = _git_text(
        ["-c", "trailer.separators=:", "interpret-trailers", "--parse"], root,
        stdin=message.encode("utf-8"),
    )
    values = []
    for line in parsed.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "ai-agent":
            values.append(value.strip())
    return values == ["none"]


def _assert_introduction_topology(
    commit: str, receipt: Mapping[str, object], graph: CommitGraph, root: Path,
) -> None:
    parents = graph.parents.get(commit, ())
    if len(parents) != 1 or parents[0] != receipt.get("migration_basis_commit"):
        raise MigrationError("receipt.basis_invalid", "R の唯一 parent が H_mig でない")
    out = _git_text(
        ["diff-tree", "--no-commit-id", "--name-status", "-r", "-M", "-C", commit], root,
    )
    if out.splitlines() != [f"A\t{RECEIPT_REL}"]:
        raise MigrationError("receipt.introduction_diff", "R が receipt 1 file の A だけでない")
    if not _is_none_commit(commit, root):
        raise MigrationError("receipt.user_commit_trailer", "R に AI-Agent: none が逐語でない")


def _format_refusal(prefix: str, reason: str, detail: str = "") -> str:
    suffix = f" {detail}" if detail else ""
    return f"{prefix}: [{reason}]{suffix}"


def _append_refusal(refusals: List[str], prefix: str, reason: str, detail: str = "") -> None:
    value = _format_refusal(prefix, reason, detail)
    if value not in refusals:
        refusals.append(value)


def _canonical_relative(path: str) -> bool:
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    pure = PurePosixPath(path)
    return not pure.is_absolute() and ".." not in pure.parts and str(pure) == path


def _iter_known_sources(value, pointer: str = "") -> Iterable[Tuple[str, Mapping[str, object]]]:
    if isinstance(value, Mapping):
        if {"path", "sha256"}.issubset(value) and isinstance(value.get("path"), str):
            yield pointer + "/sha256", value
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            yield from _iter_known_sources(child, pointer + "/" + token)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_known_sources(child, pointer + "/" + str(index))


def _classify_source_closure(
    known_doc: Mapping[str, object],
    basis_sha256: Callable[[str], str],
) -> Tuple[frozenset[str], frozenset[str]]:
    """S-1 closure の 63/12/51 と pointer 集合を純粋に分類する。"""
    sources = [
        (pointer, record) for pointer, record in _iter_known_sources(known_doc)
        if "/sources/" in pointer
    ]
    if len(sources) != 63:
        raise MigrationError("known_axes.source_closure", f"source record が 63 件でない: {len(sources)}")
    pointers = [pointer for pointer, _ in sources]
    if len(set(pointers)) != 63:
        raise MigrationError("known_axes.source_closure", "source pointer が重複")
    changed: set[str] = set()
    unchanged: set[str] = set()
    for pointer, record in sources:
        path, recorded = record.get("path"), record.get("sha256")
        if not _canonical_relative(path) or not isinstance(recorded, str) or _SHA256_RE.fullmatch(recorded) is None:
            raise MigrationError("known_axes.source_closure", f"source record が不正: {pointer}")
        (changed if basis_sha256(path) != recorded else unchanged).add(pointer)
    expected = {spec.json_pointer for spec in SOURCE_REPIN_SPECS if spec.artifact == "known_axes"}
    if changed != expected or len(unchanged) != 51:
        raise MigrationError("known_axes.source_closure", "changed 12 / unchanged 51 が成立しない")
    return frozenset(changed), frozenset(unchanged)


def _verify_ccbench_basis(basis: str, expected_pin: str, root: Path) -> None:
    mode, kind, oid = _tree_entry(basis, CCBENCH_REL, root)
    if (mode, kind, oid) != ("160000", "commit", expected_pin):
        raise MigrationError("known_axes.ccbench_gitlink", "H_mig ccbench gitlink が legacy pin と不一致")


def _current_ccbench_head(root: Path) -> str:
    path = root / CCBENCH_REL
    if not path.is_dir():
        raise MigrationError("known_axes.ccbench_current", "ccbench submodule が存在しない")
    try:
        head = _capture_head(path)
    except MigrationError as exc:
        raise MigrationError("known_axes.ccbench_current", exc.detail or str(exc)) from exc
    return head


def _verify_closure(
    receipt: Mapping[str, object], known_doc: Mapping[str, object], holdout_doc: Mapping[str, object],
    root: Path,
) -> None:
    basis = str(receipt["migration_basis_commit"])
    if _object_type(basis, root) != "commit":
        raise MigrationError("receipt.basis_invalid", "H_mig が commit でない")
    ccbench_pin = known_doc.get("ccbench_pin")
    _require_hex(ccbench_pin, _SHA1_RE, "known_axes.schema", "ccbench_pin")
    _verify_ccbench_basis(basis, ccbench_pin, root)

    _classify_source_closure(
        known_doc,
        lambda path: _sha256(_basis_blob(basis, path, root, ccbench_pin=ccbench_pin)),
    )
    repins = receipt["source_repins"]
    for record in repins:
        target = known_doc if record["artifact"] == "known_axes" else holdout_doc
        if _resolve_pointer(target, record["json_pointer"]) != record["recorded_sha256"]:
            raise MigrationError("receipt.repin_invalid", "recorded_sha256 が artifact pointer と不一致")
        actual = _sha256(_basis_blob(basis, record["path"], root, ccbench_pin=ccbench_pin))
        if actual != record["migration_blob_sha256"]:
            reason = "known_axes.source_closure" if record["artifact"] == "known_axes" else "holdout.design_closure"
            raise MigrationError(reason, "migration blob hash が H_mig blob と不一致")
    for record in receipt["metadata_fields"]:
        target = known_doc if record["artifact"] == "known_axes" else holdout_doc
        if _resolve_pointer(target, record["json_pointer"]) != record["recorded_sha256"]:
            raise MigrationError("receipt.repin_invalid", "metadata recorded hash が artifact と不一致")
        actual = _sha256(_basis_blob(basis, record["path"], root, ccbench_pin=ccbench_pin))
        if actual != record["migration_blob_sha256"]:
            raise MigrationError("receipt.repin_invalid", "metadata hash が H_mig blob と不一致")


def _project_documents(
    receipt: Mapping[str, object], known_doc: Mapping[str, object], holdout_doc: Mapping[str, object],
) -> Tuple[dict, dict]:
    known = copy.deepcopy(known_doc)
    holdout = copy.deepcopy(holdout_doc)
    for record in receipt["source_repins"]:
        target = known if record["artifact"] == "known_axes" else holdout
        _set_pointer(target, record["json_pointer"], record["migration_blob_sha256"])
    for record in receipt["metadata_fields"]:
        if record["artifact"] == "holdout":
            _set_pointer(holdout, record["json_pointer"], record["migration_blob_sha256"])
    return known, holdout


def _verify_reconstruction_static(
    receipt: Mapping[str, object], known_doc: Mapping[str, object], holdout_doc: Mapping[str, object],
) -> None:
    projected_known, projected_holdout = _project_documents(receipt, known_doc, holdout_doc)
    known_view = copy.deepcopy(projected_known)
    _set_pointer(known_view, "/generator/sha256", None)
    # 比較時は cell 自体を除外する。None を残さず親から削除する。
    del known_view["generator"]["sha256"]
    known_sha = _sha256(_canonical_bytes(known_view))
    holdout_sha = _sha256(_canonical_bytes(projected_holdout))
    reconstruction = receipt["reconstruction"]
    if reconstruction["known_axes"]["projected_document_sha256"] != known_sha:
        raise MigrationError("receipt.reconstruction_invalid", "known projected hash が静的再計算と不一致")
    if reconstruction["known_axes"]["rebuilt_document_sha256"] != known_sha:
        raise MigrationError("receipt.reconstruction_invalid", "known rebuilt hash が静的再計算と不一致")
    if reconstruction["holdout"]["projected_document_sha256"] != holdout_sha:
        raise MigrationError("receipt.reconstruction_invalid", "holdout projected hash が静的再計算と不一致")


def _distances(graph: CommitGraph, basis: str) -> Mapping[str, int]:
    distances = {basis: 0}
    queue = deque([basis])
    while queue:
        current = queue.popleft()
        for parent in graph.parents.get(current, ()):
            if parent not in distances:
                distances[parent] = distances[current] + 1
                queue.append(parent)
    return distances


def _line_summary(old: bytes, new: bytes, path: str) -> Mapping[str, object]:
    try:
        old_lines = old.decode("utf-8", "strict").splitlines(keepends=True)
        new_lines = new.decode("utf-8", "strict").splitlines(keepends=True)
    except UnicodeError as exc:
        raise MigrationError("receipt.repin_invalid", f"diff 対象が UTF-8 でない: {path}") from exc
    added = deleted = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, old_lines, new_lines, autojunk=False,
    ).get_opcodes():
        if tag in {"replace", "delete"}:
            deleted += i2 - i1
        if tag in {"replace", "insert"}:
            added += j2 - j1
    return {
        "status": "diff_resolved", "path": path,
        "old_line_count": len(old_lines), "new_line_count": len(new_lines),
        "added_lines": added, "deleted_lines": deleted,
    }


def _build_repin_report(
    basis: str, repins: Sequence[Mapping[str, object]], root: Path,
) -> List[Mapping[str, object]]:
    graph = _commit_graph(basis, root)
    distances = _distances(graph, basis)
    cache: Dict[Tuple[str, str], Tuple[Mapping[str, object], Mapping[str, object]]] = {}
    report: List[Mapping[str, object]] = []
    for repin in repins:
        key = (str(repin["path"]), str(repin["recorded_sha256"]))
        if key not in cache:
            oids = _blob_oid_by_commit(graph, key[0], root)
            candidates: List[Tuple[int, str, str]] = []
            for commit, oid in oids.items():
                if oid is None or commit not in distances:
                    continue
                raw = _git(["cat-file", "blob", oid], root)
                if _sha256(raw) == key[1]:
                    candidates.append((distances[commit], commit, oid))
            new = _blob_bytes_at(basis, key[0], root)
            if candidates:
                distance, commit, oid = min(candidates, key=lambda value: (value[0], value[1]))
                old = _git(["cat-file", "blob", oid], root)
                provenance = {
                    "status": "provenance_resolved", "commit": commit,
                    "distance_from_basis": distance,
                }
                summary = _line_summary(old, new, key[0])
            else:
                try:
                    new_count = len(new.decode("utf-8", "strict").splitlines(keepends=True))
                except UnicodeError as exc:
                    raise MigrationError("receipt.repin_invalid", f"新 blob が UTF-8 でない: {key[0]}") from exc
                provenance = {
                    "status": "provenance_unverified", "commit": None,
                    "distance_from_basis": None,
                }
                summary = {
                    "status": "diff_unverified", "path": key[0],
                    "old_line_count": None, "new_line_count": new_count,
                    "added_lines": None, "deleted_lines": None,
                }
            cache[key] = (provenance, summary)
        provenance, summary = cache[key]
        report.append({
            **{name: repin[name] for name in (
                "artifact", "json_pointer", "path", "recorded_sha256", "migration_blob_sha256",
            )},
            "provenance": dict(provenance), "diff_summary": dict(summary),
        })
    return report


def _derive_repins_and_metadata(
    basis: str, known_doc: Mapping[str, object], holdout_doc: Mapping[str, object], root: Path,
) -> Tuple[List[Mapping[str, object]], List[Mapping[str, object]]]:
    ccbench_pin = str(known_doc.get("ccbench_pin"))
    repins = []
    for spec in SOURCE_REPIN_SPECS:
        target = known_doc if spec.artifact == "known_axes" else holdout_doc
        if _resolve_pointer(target, spec.json_pointer) != spec.recorded_sha256:
            raise MigrationError("receipt.repin_invalid", f"recorded cell 不一致: {spec.json_pointer}")
        repins.append({
            "artifact": spec.artifact, "json_pointer": spec.json_pointer,
            "path": spec.path, "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": _sha256(_basis_blob(basis, spec.path, root, ccbench_pin=ccbench_pin)),
        })
    metadata = []
    for spec in METADATA_SPECS:
        target = known_doc if spec.artifact == "known_axes" else holdout_doc
        if _resolve_pointer(target, spec.json_pointer) != spec.recorded_sha256:
            raise MigrationError("receipt.repin_invalid", f"metadata cell 不一致: {spec.json_pointer}")
        metadata.append({
            "artifact": spec.artifact, "json_pointer": spec.json_pointer,
            "path": spec.path, "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": _sha256(_basis_blob(basis, spec.path, root, ccbench_pin=ccbench_pin)),
            "disposition": "metadata-only",
        })
    return repins, metadata


def _without_generator_sha(document: Mapping[str, object]) -> dict:
    result = copy.deepcopy(document)
    generator = result.get("generator")
    if not isinstance(generator, MutableMapping) or "sha256" not in generator:
        raise MigrationError("known_axes.reconstruction_equality", "generator.sha256 がない")
    del generator["sha256"]
    return result


def _draft_reconstruct_known_axes(
    legacy: Mapping[str, object], repins: Sequence[Mapping[str, object]], *,
    builder: Optional[Callable[..., Mapping[str, object]]] = None,
    pairing: Optional[Callable[[Mapping[str, object]], None]] = None,
) -> Mapping[str, object]:
    if builder is None or pairing is None:
        from orchestrator.campaign import s1_known_axes_freeze as known_module
        builder = builder or known_module.build_document
        pairing = pairing or known_module.assert_s1b_pairing
    projected = copy.deepcopy(legacy)
    for record in repins:
        if record["artifact"] == "known_axes":
            _set_pointer(projected, record["json_pointer"], record["migration_blob_sha256"])
    rebuilt = builder(
        frozen_at_head=legacy["frozen_at_head"], ccbench_pin=legacy["ccbench_pin"],
        python_version=legacy["python_version"], generator_sha=legacy["generator"]["sha256"],
    )
    pairing(projected)
    projected_view = _without_generator_sha(projected)
    rebuilt_view = _without_generator_sha(rebuilt)
    if projected_view != rebuilt_view:
        raise MigrationError("known_axes.reconstruction_equality", "projected document と rebuilt document が不一致")
    projected_sha = _sha256(_canonical_bytes(projected_view))
    rebuilt_sha = _sha256(_canonical_bytes(rebuilt_view))
    if projected_sha != rebuilt_sha:
        raise MigrationError("known_axes.reconstruction_equality", "reconstruction hash が不一致")
    return {
        "status": "pass", "projected_document_sha256": projected_sha,
        "rebuilt_document_sha256": rebuilt_sha,
    }


_HOLDOUT_VERIFY_LOCK = threading.Lock()


def _draft_reconstruct_holdout(
    legacy: Mapping[str, object], repins: Sequence[Mapping[str, object]],
    metadata: Sequence[Mapping[str, object]], *, root: Path,
    verifier: Optional[Callable[..., None]] = None,
    searcher: Optional[Callable[..., Mapping[str, object]]] = None,
    search_assertion: Optional[Callable[[Mapping[str, object]], None]] = None,
) -> Mapping[str, object]:
    from orchestrator.campaign import s8b_holdout_freeze as holdout_module
    verifier = verifier or holdout_module.verify_document
    searcher = searcher or holdout_module.search_repository
    search_assertion = search_assertion or holdout_module._assert_search_pass
    projected = copy.deepcopy(legacy)
    for record in repins:
        if record["artifact"] == "holdout":
            _set_pointer(projected, record["json_pointer"], record["migration_blob_sha256"])
    for record in metadata:
        if record["artifact"] == "holdout":
            _set_pointer(projected, record["json_pointer"], record["migration_blob_sha256"])
    report = searcher(root)
    search_assertion(report)
    # 現行 verifier を実走しつつ、同じ repository scan を二度発火させない。
    if verifier is holdout_module.verify_document:
        with _HOLDOUT_VERIFY_LOCK:
            original = holdout_module.search_repository
            holdout_module.search_repository = lambda *_args, **_kwargs: report
            try:
                verifier(projected, root=root, current_head=legacy["frozen_at_head"])
            finally:
                holdout_module.search_repository = original
    else:
        verifier(projected, root=root, current_head=legacy["frozen_at_head"])
    return {
        "status": "pass",
        "projected_document_sha256": _sha256(_canonical_bytes(projected)),
        "live_scan_sha256": _sha256(_canonical_bytes(report)),
    }


def _parse_status_z(raw: bytes) -> Tuple[Tuple[str, str], ...]:
    parts = raw.split(b"\0")
    out: List[Tuple[str, str]] = []
    index = 0
    while index < len(parts) and parts[index]:
        record = parts[index]
        if len(record) < 4 or record[2:3] != b" ":
            raise MigrationError("receipt.basis_invalid", "git status porcelain が不正")
        try:
            status_code = record[:2].decode("ascii")
            path = record[3:].decode("utf-8", "strict")
        except UnicodeError as exc:
            raise MigrationError("receipt.basis_invalid", "dirty path が UTF-8 でない") from exc
        out.append((status_code, path))
        if status_code[0] in "RC" or status_code[1] in "RC":
            index += 1
            if index >= len(parts) or not parts[index]:
                raise MigrationError("receipt.basis_invalid", "rename status が不完全")
            out.append(("->", parts[index].decode("utf-8", "strict")))
        index += 1
    return tuple(out)


def _worktree_status(root: Path) -> Tuple[Tuple[str, str], ...]:
    raw = _git(
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"], root,
    )
    return _parse_status_z(raw)


def _capture_draft_basis(basis: str, root: Path) -> str:
    _require_hex(basis, _SHA1_RE, "receipt.basis_invalid", "--basis")
    head = _capture_head(root)
    if head != basis:
        raise MigrationError("receipt.basis_invalid", "HEAD と --basis が不一致")
    if _worktree_status(root):
        raise MigrationError("receipt.basis_invalid", "worktree/submodule が clean でない")
    state = inspect_receipt_history(root=root, validation_head=head)
    if state.state != "never-issued":
        raise MigrationError("receipt.invalid", f"draft は never-issued でのみ許可: {state.state}")
    known = _strict_load(_read_nofollow(root, KNOWN_AXES_REL), what="known_axes")
    pin = _require_hex(known.get("ccbench_pin"), _SHA1_RE, "known_axes.schema", "ccbench_pin")
    _verify_ccbench_basis(basis, pin, root)
    if _current_ccbench_head(root) != pin:
        raise MigrationError("known_axes.ccbench_current", "current ccbench HEAD が legacy pin と不一致")
    return head


def _artifact_documents(root: Path) -> Tuple[bytes, dict, bytes, dict]:
    known_raw, known = _load_artifact(
        root, KNOWN_AXES_REL, KNOWN_AXES_RAW_SHA256, "known_axes.artifact_bytes", "known_axes",
    )
    holdout_raw, holdout = _load_artifact(
        root, HOLDOUT_REL, HOLDOUT_RAW_SHA256, "holdout.artifact_bytes", "holdout",
    )
    return (
        known_raw, known, holdout_raw, holdout,
    )


def _load_artifact(
    root: Path, rel: str, expected_sha256: str, reason: str, what: str,
) -> Tuple[bytes, dict]:
    try:
        raw = _read_nofollow(root, rel)
    except MigrationError as exc:
        raise MigrationError(reason, f"{what} artifact を読めない") from exc
    if _sha256(raw) != expected_sha256:
        raise MigrationError(reason, f"{what} artifact raw bytes 不一致")
    try:
        document = _strict_load(raw, what=what)
    except MigrationError as exc:
        schema_reason = "known_axes.schema" if what == "known_axes" else "holdout.schema"
        raise MigrationError(schema_reason, exc.detail or str(exc)) from exc
    return raw, document


def _assert_receipt_does_not_pollute_scan(root: Path) -> Mapping[str, object]:
    from orchestrator.campaign import s8b_holdout_freeze as holdout_module
    report = holdout_module.search_repository(root)
    holdout_module._assert_search_pass(report)
    return report


def _create_only(path: Path, raw: bytes) -> Tuple[int, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o644)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("write が進行しない")
            view = view[written:]
        os.fsync(fd)
        st = os.fstat(fd)
        return st.st_dev, st.st_ino
    finally:
        os.close(fd)


def _remove_same_inode(path: Path, identity: Tuple[int, int]) -> None:
    try:
        st = path.lstat()
        if (st.st_dev, st.st_ino) == identity and stat.S_ISREG(st.st_mode):
            path.unlink()
    except OSError:
        pass


def _repo_relative(path: Path, root: Path) -> str:
    absolute = path if path.is_absolute() else root / path
    try:
        rel = absolute.resolve(strict=False).relative_to(root.resolve(strict=True)).as_posix()
    except (OSError, ValueError) as exc:
        raise MigrationError("receipt.invalid", "出力 path が repository 外") from exc
    if not _canonical_relative(rel):
        raise MigrationError("receipt.invalid", "出力 path が canonical relative でない")
    return rel


def draft_receipt(
    *, basis: str, out: Path | str = DRAFT_REL, root: Path = ROOT,
    known_builder: Optional[Callable[..., Mapping[str, object]]] = None,
    known_pairing: Optional[Callable[[Mapping[str, object]], None]] = None,
    holdout_verifier: Optional[Callable[..., None]] = None,
    holdout_searcher: Optional[Callable[..., Mapping[str, object]]] = None,
    holdout_search_assertion: Optional[Callable[[Mapping[str, object]], None]] = None,
) -> Mapping[str, object]:
    root = Path(root)
    _capture_draft_basis(basis, root)
    _, known, _, holdout = _artifact_documents(root)
    repins, metadata = _derive_repins_and_metadata(basis, known, holdout, root)
    # 63/12/51 と basis closure を再構成前に確定する。
    skeleton = {
        "migration_basis_commit": basis, "source_repins": repins,
        "metadata_fields": metadata,
    }
    _verify_closure(skeleton, known, holdout, root)
    report = _build_repin_report(basis, repins, root)
    reconstruction = {
        "known_axes": _draft_reconstruct_known_axes(
            known, repins, builder=known_builder, pairing=known_pairing,
        ),
        "holdout": _draft_reconstruct_holdout(
            holdout, repins, metadata, root=root, verifier=holdout_verifier,
            searcher=holdout_searcher, search_assertion=holdout_search_assertion,
        ),
    }
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "migration_id": MIGRATION_ID,
        "migration_basis_commit": basis,
        "artifacts": {
            "known_axes": {
                "path": KNOWN_AXES_REL, "raw_sha256": KNOWN_AXES_RAW_SHA256,
                "recorded_frozen_at_head": KNOWN_AXES_RECORDED_HEAD,
            },
            "holdout": {
                "path": HOLDOUT_REL, "raw_sha256": HOLDOUT_RAW_SHA256,
                "recorded_frozen_at_head": HOLDOUT_RECORDED_HEAD,
            },
        },
        "source_repins": repins,
        "metadata_fields": metadata,
        "reconstruction": reconstruction,
        "repin_report": report,
        "confirmed_by": None,
        "confirmed_at": None,
    }
    validate_receipt_schema(receipt, confirmation="draft")
    _verify_reconstruction_static(receipt, known, holdout)
    raw = _canonical_bytes(receipt)
    out_path = root / _repo_relative(Path(out), root)
    try:
        identity = _create_only(out_path, raw)
    except FileExistsError as exc:
        raise MigrationError("receipt.invalid", "draft 出力が既に存在する") from exc
    try:
        _assert_receipt_does_not_pollute_scan(root)
    except Exception:
        _remove_same_inode(out_path, identity)
        raise
    return receipt


def _validate_repin_report_git(receipt: Mapping[str, object], root: Path) -> None:
    expected = _build_repin_report(
        str(receipt["migration_basis_commit"]), receipt["source_repins"], root,
    )
    if expected != receipt["repin_report"]:
        raise MigrationError("receipt.repin_invalid", "repin_report が Git 導出値と不一致")


def validate_draft(*, path: Path | str = DRAFT_REL, root: Path = ROOT) -> Mapping[str, object]:
    root = Path(root)
    rel = _repo_relative(Path(path), root)
    head = _capture_head(root)
    raw = _read_nofollow(root, rel)
    receipt = _load_canonical(raw, what="draft")
    validate_receipt_schema(receipt, confirmation="draft")
    if receipt["migration_basis_commit"] != head:
        raise MigrationError("receipt.basis_invalid", "draft H_mig と current HEAD が不一致")
    status = _worktree_status(root)
    if status != (("??", rel),):
        raise MigrationError("receipt.basis_invalid", "dirty は指定 draft 1 file だけでなければならない")
    history = inspect_receipt_history(root=root, validation_head=head)
    if history.state != "never-issued":
        raise MigrationError("receipt.invalid", "active receipt が発行済み")
    _, known, _, holdout = _artifact_documents(root)
    _verify_closure(receipt, known, holdout, root)
    _verify_repin_report_git(receipt, root)
    _verify_reconstruction_static(receipt, known, holdout)
    _assert_receipt_does_not_pollute_scan(root)
    return receipt


def finalize_receipt(
    *, draft: Path | str = DRAFT_REL, confirmed_by: str, confirmed_at: str,
    out: Path | str = RECEIPT_REL, root: Path = ROOT,
) -> Mapping[str, object]:
    root = Path(root)
    if _repo_relative(Path(out), root) != RECEIPT_REL:
        raise MigrationError("receipt.invalid", "finalize 出力は active path 固定")
    receipt = copy.deepcopy(validate_draft(path=draft, root=root))
    receipt["confirmed_by"] = confirmed_by
    receipt["confirmed_at"] = confirmed_at
    validate_receipt_schema(receipt, confirmation="active")
    raw = _canonical_bytes(receipt)
    out_path = root / RECEIPT_REL
    try:
        identity = _create_only(out_path, raw)
    except FileExistsError as exc:
        raise MigrationError("receipt.invalid", "active receipt が既に存在する") from exc
    try:
        _assert_receipt_does_not_pollute_scan(root)
    except Exception:
        _remove_same_inode(out_path, identity)
        raise
    return receipt


def inspect_receipt_history(
    *, root: Path = ROOT, validation_head: Optional[str] = None,
) -> ReceiptResolution:
    """schema/gate 検査前までの 4 状態機械を実行する。"""
    root = Path(root)
    head = validation_head or _capture_head(root)
    graph = _commit_graph(head, root)
    oids = _blob_oid_by_commit(graph, RECEIPT_REL, root)
    introductions = _introduction_candidates(graph, oids)
    presence = _worktree_presence(root, RECEIPT_REL)
    if not introductions:
        if oids.get(head) is None and presence == "absent":
            return ReceiptResolution("never-issued", (), None, head)
        return ReceiptResolution(
            "invalid", (_format_refusal(RECEIPT_PREFIX, "receipt.invalid"),), None, head,
        )
    if len(introductions) != 1:
        return ReceiptResolution(
            "issued-but-missing",
            (_format_refusal(RECEIPT_PREFIX, "receipt.multiple_introduction"),),
            None, head,
        )
    introduction = introductions[0]
    expected_oid = oids[introduction]
    descendants = _descendants_of(graph, introduction)
    if any(oids.get(commit) != expected_oid for commit in descendants):
        return ReceiptResolution(
            "issued-but-missing", (_format_refusal(RECEIPT_PREFIX, "receipt.history_mutated"),),
            None, head, introduction,
        )
    if any(
        commit != introduction and _history_touches_path(commit, RECEIPT_REL, root)
        for commit in descendants
    ):
        return ReceiptResolution(
            "issued-but-missing", (_format_refusal(RECEIPT_PREFIX, "receipt.history_mutated"),),
            None, head, introduction,
        )
    if oids.get(head) != expected_oid or presence != "regular":
        return ReceiptResolution(
            "issued-but-missing", (_format_refusal(RECEIPT_PREFIX, "receipt.issued_but_missing"),),
            None, head, introduction,
        )
    try:
        r_raw = _git(["cat-file", "blob", str(expected_oid)], root)
        worktree_raw = _read_nofollow(root, RECEIPT_REL)
    except MigrationError:
        return ReceiptResolution(
            "issued-but-missing", (_format_refusal(RECEIPT_PREFIX, "receipt.issued_but_missing"),),
            None, head, introduction,
        )
    if worktree_raw != r_raw:
        return ReceiptResolution(
            "issued-but-missing", (_format_refusal(RECEIPT_PREFIX, "receipt.issued_but_missing"),),
            None, head, introduction,
        )
    try:
        receipt = _load_canonical(r_raw)
        validate_receipt_schema(receipt, confirmation="active")
    except MigrationError as exc:
        return ReceiptResolution(
            "invalid", (_format_refusal(RECEIPT_PREFIX, exc.reason, exc.detail),),
            None, head, introduction,
        )
    try:
        _assert_introduction_topology(introduction, receipt, graph, root)
    except MigrationError as exc:
        # schema が読める限り、anchor topology 拒否後も closure 等を継続できるよう保持する。
        return ReceiptResolution(
            "invalid", (_format_refusal(RECEIPT_PREFIX, exc.reason, exc.detail),),
            None, head, introduction, receipt,
        )
    return ReceiptResolution("invalid", (), None, head, introduction, receipt)


def _validate_positive_control(root: Path) -> None:
    try:
        raw = _read_nofollow(root, POSITIVE_CONTROL_PATH)
    except MigrationError as exc:
        raise MigrationError("holdout.positive_control", "positive fixture を読めない") from exc
    if _sha256(raw) != POSITIVE_CONTROL_SHA256:
        raise MigrationError("holdout.positive_control", "positive fixture raw root 不一致")


def _verify_live_and_static_documents(
    receipt: Mapping[str, object], known: Mapping[str, object], holdout: Mapping[str, object], root: Path,
) -> Mapping[str, object]:
    from orchestrator.campaign import s1_known_axes_freeze as known_module
    from orchestrator.campaign import s8b_holdout_freeze as holdout_module
    projected_known, projected_holdout = _project_documents(receipt, known, holdout)
    try:
        known_module._validate_schema(projected_known)
    except Exception as exc:
        raise MigrationError("known_axes.schema", str(exc)) from exc
    try:
        known_module.assert_s1b_pairing(projected_known)
    except Exception as exc:
        raise MigrationError("known_axes.pairing", str(exc)) from exc
    report = holdout_module.search_repository(root)
    try:
        holdout_module._assert_search_pass(report)
    except Exception as exc:
        raise MigrationError("holdout.unknownness_layer2", str(exc)) from exc
    # source/head は H_mig blob classifier の責務。static schema/binding/層1は現行 verifier を使う。
    with _HOLDOUT_VERIFY_LOCK:
        original_source = holdout_module._verify_source
        original_head = holdout_module._verify_head
        original_search = holdout_module.search_repository
        holdout_module._verify_source = lambda *_args, **_kwargs: None
        holdout_module._verify_head = lambda *_args, **_kwargs: None
        holdout_module.search_repository = lambda *_args, **_kwargs: report
        try:
            holdout_module.verify_document(
                projected_holdout, root=root, current_head=holdout["frozen_at_head"],
            )
        except Exception as exc:
            text = str(exc)
            reason = "holdout.binding" if "binding" in text else (
                "holdout.unknownness_layer1" if "unknownness" in text or "zero_hit" in text else "holdout.schema"
            )
            raise MigrationError(reason, text) from exc
        finally:
            holdout_module._verify_source = original_source
            holdout_module._verify_head = original_head
            holdout_module.search_repository = original_search
    return report


def _make_observation(
    receipt: Mapping[str, object], receipt_raw: bytes, validation_head: str,
    ancestries: Sequence[AncestryResult],
) -> Mapping[str, object]:
    items: List[Mapping[str, object]] = []
    for record in receipt["source_repins"]:
        items.append({
            "artifact": record["artifact"], "kind": "source-repin",
            "subject": record["json_pointer"], "recorded": record["recorded_sha256"],
            "observed": record["migration_blob_sha256"], "status": "repinned-to-basis-blob",
        })
    for record in receipt["metadata_fields"]:
        items.append({
            "artifact": record["artifact"], "kind": "generator-metadata",
            "subject": record["json_pointer"], "recorded": record["recorded_sha256"],
            "observed": record["migration_blob_sha256"], "status": "metadata-only",
        })
    for artifact, ancestry in zip(("known_axes", "holdout"), ancestries):
        items.append({
            "artifact": artifact, "kind": "ancestry", "subject": "/frozen_at_head",
            "recorded": ancestry.recorded, "observed": ancestry.observed,
            "status": ancestry.status,
        })
    if len(items) != 17:
        raise MigrationError("receipt.invalid", "observation items が 17 件でない")
    return {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "migration_id": MIGRATION_ID,
        "receipt": {"path": RECEIPT_REL, "raw_sha256": _sha256(receipt_raw)},
        "migration_basis_commit": receipt["migration_basis_commit"],
        "validation_head": validation_head,
        "items": items,
    }


def verify_receipt(*, root: Path = ROOT, path: Path | str = RECEIPT_REL) -> ReceiptResolution:
    root = Path(root)
    if _repo_relative(Path(path), root) != RECEIPT_REL:
        raise MigrationError("receipt.invalid", "verify path は active path 固定")
    head = _capture_head(root)
    history = inspect_receipt_history(root=root, validation_head=head)
    if history.state in {"never-issued", "issued-but-missing"}:
        return history
    if history.receipt is None:
        return history
    receipt = history.receipt
    refusals: List[str] = list(history.refusals)
    known = holdout = None
    try:
        _known_raw, known = _load_artifact(
            root, KNOWN_AXES_REL, KNOWN_AXES_RAW_SHA256,
            "known_axes.artifact_bytes", "known_axes",
        )
    except MigrationError as exc:
        _append_refusal(refusals, KNOWN_PREFIX, exc.reason, exc.detail)
    try:
        _holdout_raw, holdout = _load_artifact(
            root, HOLDOUT_REL, HOLDOUT_RAW_SHA256,
            "holdout.artifact_bytes", "holdout",
        )
    except MigrationError as exc:
        _append_refusal(refusals, HOLDOUT_PREFIX, exc.reason, exc.detail)
    ancestries = (
        _classify_ancestry(KNOWN_AXES_RECORDED_HEAD, head, root, artifact="known_axes"),
        _classify_ancestry(HOLDOUT_RECORDED_HEAD, head, root, artifact="holdout"),
    )
    for ancestry, prefix in zip(ancestries, (KNOWN_PREFIX, HOLDOUT_PREFIX)):
        if ancestry.refusal_reason:
            _append_refusal(refusals, prefix, ancestry.refusal_reason)
    checks: List[Callable[[], object]] = [
        lambda: _validate_repin_report_git(receipt, root),
        lambda: _validate_positive_control(root),
    ]
    if known is not None:
        checks.append(lambda: _verify_ccbench_live(receipt, known, root))
    if known is not None and holdout is not None:
        checks.extend((
            lambda: _verify_closure(receipt, known, holdout, root),
            lambda: _verify_reconstruction_static(receipt, known, holdout),
            lambda: _verify_live_and_static_documents(receipt, known, holdout, root),
        ))
    for check in checks:
        try:
            check()
        except MigrationError as exc:
            prefix = RECEIPT_PREFIX
            if exc.reason.startswith("known_axes."):
                prefix = KNOWN_PREFIX
            elif exc.reason.startswith("holdout."):
                prefix = HOLDOUT_PREFIX
            _append_refusal(refusals, prefix, exc.reason, exc.detail)
    try:
        receipt_raw = _read_nofollow(root, RECEIPT_REL)
        observation = _make_observation(receipt, receipt_raw, head, ancestries)
    except MigrationError as exc:
        _append_refusal(refusals, RECEIPT_PREFIX, exc.reason, exc.detail)
        observation = None
    state = "active-valid" if not refusals else "invalid"
    if state == "invalid" and not refusals:
        _append_refusal(refusals, RECEIPT_PREFIX, "receipt.invalid")
    return ReceiptResolution(
        state, tuple(refusals), observation, head, history.introduction_commit, receipt,
    )


def _verify_ccbench_live(receipt: Mapping[str, object], known: Mapping[str, object], root: Path) -> None:
    pin = str(known.get("ccbench_pin"))
    if _current_ccbench_head(root) != pin:
        raise MigrationError("known_axes.ccbench_current", "current ccbench HEAD が legacy pin と不一致")
    _verify_ccbench_basis(str(receipt["migration_basis_commit"]), pin, root)


def static_gate_adapter(
    *, resolution: ReceiptResolution, known_raw: bytes, holdout_raw: bytes, root: Path = ROOT,
) -> AdapterResult:
    """official gate 用の fail-fast しない静的 adapter。

    U1 は receipt 解決を最外層で一度だけ行い、active-valid のときだけこの関数へ raw
    artifact を渡す。発火条件外では refusal を増やさず legacy verifier へ委譲する。
    """
    if resolution.state != "active-valid" or resolution.receipt is None:
        return AdapterResult(resolution.refusals, resolution.t080_freeze_migration_observation)
    receipt = resolution.receipt
    known_doc = _strict_load(known_raw, what="known_axes")
    holdout_doc = _strict_load(holdout_raw, what="holdout")
    known_record = holdout_doc.get("known_axes_freeze")
    fires = (
        _sha256(holdout_raw) == receipt["artifacts"]["holdout"]["raw_sha256"]
        and isinstance(known_record, Mapping)
        and known_record.get("path") == KNOWN_AXES_REL
        and known_record.get("sha256") == KNOWN_AXES_RAW_SHA256
    )
    if not fires:
        return AdapterResult(resolution.refusals, resolution.t080_freeze_migration_observation)
    refusals = list(resolution.refusals)
    checks = (
        (KNOWN_PREFIX, "known_axes.artifact_bytes", _sha256(known_raw) == KNOWN_AXES_RAW_SHA256),
        (HOLDOUT_PREFIX, "holdout.artifact_bytes", _sha256(holdout_raw) == HOLDOUT_RAW_SHA256),
    )
    for prefix, reason, passed in checks:
        if not passed:
            _append_refusal(refusals, prefix, reason)
    # resolution 時にも全検査済みだが、caller が別 raw を渡した場合の closure を再確認する。
    independent = (
        lambda: _verify_closure(receipt, known_doc, holdout_doc, Path(root)),
        lambda: _verify_reconstruction_static(receipt, known_doc, holdout_doc),
        lambda: _verify_ccbench_live(receipt, known_doc, Path(root)),
        lambda: _validate_positive_control(Path(root)),
        lambda: _verify_live_and_static_documents(receipt, known_doc, holdout_doc, Path(root)),
    )
    for check in independent:
        try:
            check()
        except MigrationError as exc:
            prefix = RECEIPT_PREFIX
            if exc.reason.startswith("known_axes."):
                prefix = KNOWN_PREFIX
            elif exc.reason.startswith("holdout."):
                prefix = HOLDOUT_PREFIX
            _append_refusal(refusals, prefix, exc.reason, exc.detail)
    return AdapterResult(tuple(refusals), resolution.t080_freeze_migration_observation)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="T-080 legacy freeze migration receipt")
    commands = parser.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("draft")
    draft.add_argument("--basis", required=True)
    draft.add_argument("--out", type=Path, required=True)
    validate = commands.add_parser("validate-draft")
    validate.add_argument("--path", type=Path, required=True)
    finalize = commands.add_parser("finalize")
    finalize.add_argument("--draft", type=Path, required=True)
    finalize.add_argument("--confirmed-by", required=True)
    finalize.add_argument("--confirmed-at", required=True)
    finalize.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--path", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None, *, root: Path = ROOT) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "draft":
            draft_receipt(basis=args.basis, out=args.out, root=root)
            return 0
        if args.command == "validate-draft":
            validate_draft(path=args.path, root=root)
            return 0
        if args.command == "finalize":
            finalize_receipt(
                draft=args.draft, confirmed_by=args.confirmed_by,
                confirmed_at=args.confirmed_at, out=args.out, root=root,
            )
            return 0
        resolution = verify_receipt(root=root, path=args.path)
        print(json.dumps({
            "state": resolution.state,
            "refusals": list(resolution.refusals),
            "t080_freeze_migration_observation": resolution.t080_freeze_migration_observation,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if resolution.state == "active-valid" else 2
    except MigrationError as exc:
        print(json.dumps({
            "state": "invalid", "refusals": [_format_refusal(RECEIPT_PREFIX, exc.reason, exc.detail)],
            "t080_freeze_migration_observation": None,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 2
    except Exception as exc:  # pragma: no cover - 内部異常の最終境界
        print(f"T-080 internal error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
