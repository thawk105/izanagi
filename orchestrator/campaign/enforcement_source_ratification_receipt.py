# -*- coding: utf-8 -*-
"""Validate committed Ed25519 enforcement-source ratification receipts.

This module compares a requested closure digest with signed receipts verified
by the key in the current committed trust root.  The trust root, ledger, Git
history, receipt chain, and receipt source bindings must all be internally
consistent.  ``closure_paths_sha256`` and ``trust_root_sha256`` are diagnostic
schema redundancies, not independent defenses.
"""
from __future__ import annotations

import base64
import binascii
from types import FunctionType
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Mapping, cast

from .campaign_lock import CONTRACT_LOADER_RELATIVE_PATHS
from .ed25519_verify import Ed25519VerifyError, verify
from .enforcement_source_ratification import (
    EnforcementSourceRatificationError,
    _FORBIDDEN_AMBIENT_GIT_ENV,
    _GIT_ENV_ALLOWLIST,
    _GIT_EXECUTABLE,
    _GIT_HARDEN,
    _assert_full_history_repository,
    _git as _v1_git,
    _git_env,
    _ledger_blob_oids,
    _reachable_commit_parents,
    closure_digest_sha256,
)

# These test-visible aliases are not separate hardening barriers; _git delegates
# every command to the imported v1 Git kernel.

RECEIPT_LEDGER_RELATIVE_PATH = (
    "hooks/enforcement-source-ratification-receipts.v2.jsonl"
)
TRUST_ROOT_RELATIVE_PATH = (
    "hooks/enforcement-source-ratification-trust-root.v1.json"
)
RECEIPT_SCHEMA_VERSION = "enforcement-source-ratification-receipt/v2"
_TRUST_ROOT_SCHEMA_VERSION = "enforcement-source-ratification-trust-root/v1"
_DOMAIN_PREFIX = b"izanagi/enforcement-source-ratification-receipt/v2\x00"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROW_KEYS = frozenset({
    "closure_digest_sha256",
    "closure_paths",
    "closure_paths_sha256",
    "decision",
    "previous_receipt_sha256",
    "ratification_serial",
    "schema_version",
    "signature_ed25519_base64",
    "source_commit",
    "trust_root_sha256",
})
_SIGNED_KEYS = _ROW_KEYS - {"signature_ed25519_base64"}
_TRUST_ROOT_KEYS = frozenset({
    "public_key_ed25519_base64",
    "schema_version",
})
_ED25519_FIELD_PRIME = (1 << 255) - 19

# Each scalar cap is at least 8x a 100-row, 3 KiB-row, depth-2 ledger.
_MAX_LEDGER_BYTES = 4 * 1024 * 1024
_MAX_LEDGER_LINE_BYTES = 32 * 1024
_MAX_LEDGER_ROWS = 2048
_MAX_JSON_NESTING = 16
# Aggregate caps are 8x+ a realistic 20-receipt history (3 KiB rows, 1 MiB closure).
_MAX_HISTORY_COMMITS = 2048
_MAX_HISTORY_LEDGER_BYTES = 128 * 1024 * 1024
_MAX_SOURCE_BATCH_BYTES = 256 * 1024 * 1024
_REGULAR_SOURCE_MODES = frozenset({b"100644", b"100755"})


class EnforcementSourceRatificationReceiptError(ValueError):
    """The trust root, receipt ledger, or requested closure is inadmissible."""


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt value is not canonical JSON"
        ) from exc


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt has duplicate key: {key!r}"
            )
        value[key] = item
    return value


def _decode_canonical_base64(value: object, *, label: str) -> bytes:
    if type(value) is not str:
        raise EnforcementSourceRatificationReceiptError(
            f"{label} is not canonical base64"
        )
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
        raise EnforcementSourceRatificationReceiptError(
            f"{label} is not canonical base64"
        ) from exc
    if base64.b64encode(decoded) != encoded:
        raise EnforcementSourceRatificationReceiptError(
            f"{label} is not canonical base64"
        )
    return decoded


def _git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
):
    try:
        return _v1_git(root, *args, input_bytes=input_bytes)
    except EnforcementSourceRatificationError as exc:
        raise EnforcementSourceRatificationReceiptError(str(exc)) from exc


def _require_git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> bytes:
    result = _git(root, *args, input_bytes=input_bytes)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt git command failed: "
            f"args={args!r} rc={result.returncode} stderr={stderr!r}"
        )
    return result.stdout


def _validated_root() -> Path:
    if not isinstance(_REPO_ROOT, Path):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt repository root must be pathlib.Path"
        )
    try:
        root = _REPO_ROOT.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt repository root cannot be resolved"
        ) from exc
    if not root.is_dir():
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt repository root is not a directory"
        )
    raw = _require_git(root, "rev-parse", "--show-toplevel")
    try:
        toplevel = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt Git top-level is not UTF-8"
        ) from exc
    if not toplevel.endswith("\n") or "\n" in toplevel[:-1]:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt Git top-level output is not exact"
        )
    if toplevel[:-1] != str(root):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt Git top-level differs from expected checkout"
        )
    return root


def _head_commit(root: Path) -> str:
    raw = _require_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt HEAD is not ASCII"
        ) from exc
    if (
        not text.endswith("\n")
        or "\n" in text[:-1]
        or _HEX40_RE.fullmatch(text[:-1]) is None
    ):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt HEAD is not an exact commit ID"
        )
    return text[:-1]


def _full_history(root: Path, head: str) -> dict[str, tuple[str, ...]]:
    try:
        _assert_full_history_repository(root)
    except EnforcementSourceRatificationError as exc:
        raise EnforcementSourceRatificationReceiptError(str(exc)) from exc
    raw = _require_git(
        root,
        "rev-list",
        f"--max-count={_MAX_HISTORY_COMMITS + 1}",
        head,
    )
    if not raw.endswith(b"\n"):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt history returned an invalid commit ID"
        )
    commits = raw.split(b"\n")[:-1]
    if len(commits) > _MAX_HISTORY_COMMITS:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt history exceeds the commit limit"
        )
    try:
        return _reachable_commit_parents(root, head)
    except EnforcementSourceRatificationError as exc:
        raise EnforcementSourceRatificationReceiptError(str(exc)) from exc


def _blob_oids_for_path(
    root: Path,
    commits: tuple[str, ...],
    relative_path: str,
    *,
    label: str,
) -> tuple[dict[str, str | None], dict[str, int]]:
    """Run the v1 DAG tree/object kernel for an explicit committed path."""
    kernel_globals = dict(_ledger_blob_oids.__globals__)
    kernel_globals["RATIFICATION_LEDGER_RELATIVE_PATH"] = relative_path
    kernel = FunctionType(
        _ledger_blob_oids.__code__,
        kernel_globals,
        _ledger_blob_oids.__name__,
        _ledger_blob_oids.__defaults__,
        _ledger_blob_oids.__closure__,
    )
    try:
        return kernel(root, commits)
    except EnforcementSourceRatificationError as exc:
        raise EnforcementSourceRatificationReceiptError(
            f"ratification receipt {label} is not a regular file in "
            "committed history"
        ) from exc


def _load_blob_exact(root: Path, oid: str, expected_size: int, label: str) -> bytes:
    raw = _require_git(root, "cat-file", "blob", oid)
    if len(raw) != expected_size:
        raise EnforcementSourceRatificationReceiptError(
            f"ratification receipt {label} blob size disagrees with Git"
        )
    return raw


def _assert_immutable_trust_root_history(
    parents_by_commit: Mapping[str, tuple[str, ...]],
    entries: Mapping[str, str | None],
) -> str:
    introductions: list[str] = []
    for commit, parents in parents_by_commit.items():
        oid = entries[commit]
        parent_oids = tuple(
            entries[parent] for parent in parents if entries[parent] is not None
        )
        if oid is None:
            if parent_oids:
                raise EnforcementSourceRatificationReceiptError(
                    "ratification receipt trust root was deleted across "
                    "reachable history"
                )
            continue
        if not parent_oids:
            introductions.append(commit)
            continue
        if any(parent_oid != oid for parent_oid in parent_oids):
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt trust root changed across reachable "
                "history"
            )
    if len(introductions) != 1:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root must be introduced exactly once"
        )
    head = next(iter(parents_by_commit))
    # Exact-one introduction plus the live deletion check imply HEAD presence.
    return cast(str, entries[head])


def _load_trust_root(root: Path, oid: str, expected_size: int) -> bytes:
    raw = _load_blob_exact(root, oid, expected_size, "trust-root")
    if not raw:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root is empty"
        )
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root is not ASCII"
        ) from exc
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except json.JSONDecodeError as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root is not JSON"
        ) from exc
    if type(value) is not dict or set(value) != _TRUST_ROOT_KEYS:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root has a non-exact schema"
        )
    if value["schema_version"] != _TRUST_ROOT_SCHEMA_VERSION:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root schema version is invalid"
        )
    if raw != _canonical_json_bytes(value) + b"\n":
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust root is not canonical JSON with "
            "exactly one trailing LF"
        )
    public_key = _decode_canonical_base64(
        value["public_key_ed25519_base64"], label="trust-root public key"
    )
    if len(public_key) != 32:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust-root public key is not 32 bytes"
        )
    encoded_y = int.from_bytes(public_key, "little") & ((1 << 255) - 1)
    if encoded_y >= _ED25519_FIELD_PRIME:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt trust-root public key is not canonical"
        )
    return public_key


def _validate_json_nesting(raw: bytes) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == ord("\\"):
                escaped = True
            elif byte == ord('"'):
                in_string = False
            continue
        if byte == ord('"'):
            in_string = True
        elif byte in (ord("{"), ord("[")):
            depth += 1
            if depth > _MAX_JSON_NESTING:
                raise EnforcementSourceRatificationReceiptError(
                    "ratification receipt JSON nesting exceeds the limit"
                )
        elif byte in (ord("}"), ord("]")) and depth:
            depth -= 1


def _validate_ledger_blob_bounds(raw: bytes) -> None:
    if not raw:
        return
    lines = raw.split(b"\n")[:-1]
    if len(lines) > _MAX_LEDGER_ROWS:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt ledger exceeds the row limit"
        )
    for line in lines:
        if len(line) > _MAX_LEDGER_LINE_BYTES:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt row exceeds the byte limit"
            )
        _validate_json_nesting(line)


def _load_ledger_blobs(
    root: Path,
    entries: Mapping[str, str | None],
    sizes_by_oid: Mapping[str, int],
) -> dict[str, bytes]:
    """Load each historical ledger blob OID once without parsing its rows."""
    memo: dict[str, bytes] = {}
    total_size = 0
    for oid in dict.fromkeys(
        entry for entry in entries.values() if entry is not None
    ):
        size = sizes_by_oid[oid]
        if size > _MAX_LEDGER_BYTES:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt ledger exceeds the byte limit"
            )
        total_size += size
        if total_size > _MAX_HISTORY_LEDGER_BYTES:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt historical ledger blobs exceed the "
                "aggregate byte limit"
            )
        raw = _load_blob_exact(root, oid, size, "ledger")
        if raw and not raw.endswith(b"\n"):
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt ledger is not newline terminated"
            )
        memo[oid] = raw
    return memo


def _assert_linear_ledger_history(
    parents_by_commit: Mapping[str, tuple[str, ...]],
    entries: Mapping[str, str | None],
    blobs_by_oid: Mapping[str, bytes],
) -> bytes:
    introductions: list[str] = []
    row_counts_by_oid = {
        oid: raw.count(b"\n") for oid, raw in blobs_by_oid.items()
    }

    def raw_at(commit: str) -> bytes:
        oid = entries[commit]
        if oid is None:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt ledger was deleted in committed history"
            )
        return blobs_by_oid[oid]

    def row_count_at(commit: str) -> int:
        oid = entries[commit]
        if oid is None:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt ledger was deleted in committed history"
            )
        return row_counts_by_oid[oid]

    for commit, parents in parents_by_commit.items():
        oid = entries[commit]
        bearing_parents = tuple(
            parent for parent in parents if entries[parent] is not None
        )
        if oid is None:
            if bearing_parents:
                raise EnforcementSourceRatificationReceiptError(
                    "ratification receipt ledger was deleted in committed "
                    "history"
                )
            continue

        current = blobs_by_oid[oid]
        if not bearing_parents:
            introductions.append(commit)
            if row_counts_by_oid[oid] > 1:
                raise EnforcementSourceRatificationReceiptError(
                    "ratification receipt history introduced more than one row"
                )
            continue

        parent_blobs = tuple(raw_at(parent) for parent in bearing_parents)
        longest_parent_commit = max(
            bearing_parents, key=lambda parent: len(raw_at(parent))
        )
        longest_parent = raw_at(longest_parent_commit)
        if any(not longest_parent.startswith(parent) for parent in parent_blobs):
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt history has divergent signed chains; "
                "serialize ledger appends through a single writer before "
                "merging"
            )
        if not current.startswith(longest_parent):
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt history is not a strict prefix extension"
            )
        added_rows = row_counts_by_oid[oid] - row_count_at(
            longest_parent_commit
        )
        if added_rows > 1:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt history added more than one row"
            )

    if len(introductions) != 1:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt history must introduce the ledger exactly once"
        )
    head = next(iter(parents_by_commit))
    # Exact-one introduction plus the live deletion check imply HEAD presence.
    return raw_at(head)


def _validate_paths(value: object, *, line_number: int) -> list[str]:
    if type(value) is not list or not value:
        raise EnforcementSourceRatificationReceiptError(
            f"ratification receipt closure paths are invalid: {line_number}"
        )
    paths: list[str] = []
    for relative in value:
        if type(relative) is not str or not relative or not relative.isascii():
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt closure path is invalid: {line_number}"
            )
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or path.as_posix() != relative
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt closure path is invalid: {line_number}"
            )
        paths.append(relative)
    if paths != sorted(set(paths)):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt closure paths are not exact sorted paths: "
            f"{line_number}"
        )
    return paths


def _require_hex64(value: object, *, label: str, line_number: int) -> str:
    if type(value) is not str or _HEX64_RE.fullmatch(value) is None:
        raise EnforcementSourceRatificationReceiptError(
            f"ratification receipt {label} is invalid: {line_number}"
        )
    return value


def _source_commit(value: object, line_number: int) -> str:
    if type(value) is not str or _HEX40_RE.fullmatch(value) is None:
        raise EnforcementSourceRatificationReceiptError(
            f"ratification receipt source commit is invalid: {line_number}"
        )
    return value


def _load_rows(
    raw: bytes,
    public_key: bytes,
) -> tuple[dict[str, object], ...]:
    if not raw:
        return ()
    rows: list[dict[str, object]] = []
    previous_canonical: bytes | None = None
    trust_root_sha256 = hashlib.sha256(public_key).hexdigest()
    # R11 is linear only in scalar multiplications: one signature check per row.
    # Historical prefix bytes are separately bounded, not claimed to be linear.
    for line_number, line in enumerate(raw.split(b"\n")[:-1], start=1):
        if not line:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt ledger has an empty row: {line_number}"
            )
        try:
            text = line.decode("ascii")
        except UnicodeDecodeError as exc:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt row is not ASCII: {line_number}"
            ) from exc
        try:
            value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
        except json.JSONDecodeError as exc:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt row is not JSON: {line_number}"
            ) from exc
        if type(value) is not dict or set(value) != _ROW_KEYS:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt row has a non-exact schema: {line_number}"
            )
        canonical = _canonical_json_bytes(value)
        if line != canonical:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt row is not canonical JSON: {line_number}"
            )
        if value["schema_version"] != RECEIPT_SCHEMA_VERSION:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt schema version is invalid: {line_number}"
            )
        signature = _decode_canonical_base64(
            value["signature_ed25519_base64"],
            label=f"ratification receipt signature at line {line_number}",
        )
        if len(signature) != 64:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt signature is not 64 bytes: {line_number}"
            )
        signed = {key: value[key] for key in _SIGNED_KEYS}
        try:
            verify(
                public_key,
                _DOMAIN_PREFIX + _canonical_json_bytes(signed),
                signature,
            )
        except Ed25519VerifyError as exc:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt signature is invalid: {line_number}"
            ) from exc
        serial = value["ratification_serial"]
        if type(serial) is not int or serial != line_number:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt serial is not contiguous: {line_number}"
            )
        previous = value["previous_receipt_sha256"]
        expected_previous = (
            None
            if previous_canonical is None
            else hashlib.sha256(previous_canonical).hexdigest()
        )
        if previous != expected_previous:
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt previous hash is invalid: {line_number}"
            )
        _require_hex64(
            value["closure_digest_sha256"],
            label="closure digest",
            line_number=line_number,
        )
        paths = _validate_paths(value["closure_paths"], line_number=line_number)
        paths_sha256 = _require_hex64(
            value["closure_paths_sha256"],
            label="closure paths digest",
            line_number=line_number,
        )
        if paths_sha256 != hashlib.sha256(
            _canonical_json_bytes(paths)
        ).hexdigest():
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt closure paths digest disagrees: "
                f"{line_number}"
            )
        if value["decision"] != "ratify":
            raise EnforcementSourceRatificationReceiptError(
                f"ratification receipt decision is not ratify: {line_number}"
            )
        _source_commit(value["source_commit"], line_number)
        recorded_root_sha256 = _require_hex64(
            value["trust_root_sha256"],
            label="trust-root digest",
            line_number=line_number,
        )
        if recorded_root_sha256 != trust_root_sha256:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt trust-root digest disagrees: "
                f"{line_number}"
            )
        rows.append(value)
        previous_canonical = canonical
    return tuple(rows)


def _require_reachable_source_commit(
    source_commit: str,
    line_number: int,
    parents_by_commit: Mapping[str, tuple[str, ...]],
) -> None:
    if source_commit not in parents_by_commit:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source commit is not reachable from HEAD: "
            f"{line_number}"
        )


def _parse_source_header(
    header: bytes,
    *,
    query: str,
    relative: str,
    expected_type: bytes,
    expected_rest: bytes,
) -> tuple[str, int]:
    if header == query.encode("ascii") + b" missing":
        if expected_type == b"blob":
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure path is absent: "
                f"{relative}"
            )
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure tree is incomplete"
        )
    fields = header.split(b" ")
    if len(fields) != 4:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure is not exact Git objects"
        )
    raw_oid, object_type, raw_size, rest = fields
    try:
        oid = raw_oid.decode("ascii")
        size_text = raw_size.decode("ascii")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure is not exact Git objects"
        ) from exc
    if (
        _HEX40_RE.fullmatch(oid) is None
        or object_type != expected_type
        or not size_text.isdecimal()
        or (len(size_text) > 1 and size_text.startswith("0"))
        or rest != expected_rest
    ):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure is not exact Git objects"
        )
    return oid, int(size_text)


def _source_tree_queries(
    source_commits: tuple[str, ...],
) -> tuple[tuple[str, str, str], ...]:
    directories = tuple(dict.fromkeys(
        PurePosixPath(relative).parent.as_posix()
        for relative in CONTRACT_LOADER_RELATIVE_PATHS
    ))
    return tuple(
        (
            commit,
            directory,
            (
                f"{commit}^{{tree}}"
                if directory == "."
                else f"{commit}:{directory}"
            ),
        )
        for commit in source_commits
        for directory in directories
    )


def _source_batch_specs(
    queries: tuple[tuple[str, str, str], ...],
    tree_queries: tuple[tuple[str, str, str], ...],
) -> tuple[tuple[bytes, str, str, str, bytes], ...]:
    return tuple(
        (b"blob", commit, relative, query, f"q{index}".encode("ascii"))
        for index, (commit, relative, query) in enumerate(queries)
    ) + tuple(
        (b"tree", commit, directory, query, f"t{index}".encode("ascii"))
        for index, (commit, directory, query) in enumerate(tree_queries)
    )


def _source_batch_metadata(
    root: Path,
    queries: tuple[tuple[str, str, str], ...],
    tree_queries: tuple[tuple[str, str, str], ...],
) -> tuple[
    dict[tuple[str, str], tuple[str, int]],
    dict[tuple[str, str], tuple[str, int]],
]:
    specs = _source_batch_specs(queries, tree_queries)
    raw = _require_git(
        root,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)",
        input_bytes=b"".join(
            query.encode("ascii") + b" " + rest + b"\n"
            for _kind, _commit, _relative, query, rest in specs
        ),
    )
    if not raw.endswith(b"\n"):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure batch is truncated"
        )
    headers = raw.split(b"\n")[:-1]
    if len(headers) != len(specs):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure batch is truncated"
        )
    blob_metadata: dict[tuple[str, str], tuple[str, int]] = {}
    tree_metadata: dict[tuple[str, str], tuple[str, int]] = {}
    predicted_batch_bytes = 0
    for ((kind, commit, relative, query, rest), header) in zip(
        specs, headers, strict=True
    ):
        oid, size = _parse_source_header(
            header,
            query=query,
            relative=relative,
            expected_type=kind,
            expected_rest=rest,
        )
        target = blob_metadata if kind == b"blob" else tree_metadata
        target[(commit, relative)] = (oid, size)
        predicted_batch_bytes += len(header) + 1 + size + 1
        if predicted_batch_bytes > _MAX_SOURCE_BATCH_BYTES:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure batch exceeds the "
                "aggregate byte limit"
            )
    return blob_metadata, tree_metadata


def _validate_source_tree_modes(
    tree_blobs: Mapping[tuple[str, str], bytes],
    blob_metadata: Mapping[tuple[str, str], tuple[str, int]],
    tree_queries: tuple[tuple[str, str, str], ...],
) -> None:
    expected_by_directory: dict[str, dict[bytes, str]] = {}
    for relative in CONTRACT_LOADER_RELATIVE_PATHS:
        path = PurePosixPath(relative)
        expected_by_directory.setdefault(path.parent.as_posix(), {})[
            path.name.encode("ascii")
        ] = relative

    for commit, directory, _query in tree_queries:
        expected = expected_by_directory[directory]
        found: set[bytes] = set()
        raw = tree_blobs[(commit, directory)]
        offset = 0
        while offset < len(raw):
            mode_end = raw.find(b" ", offset)
            name_end = raw.find(b"\0", mode_end + 1)
            oid_end = name_end + 21
            if (
                mode_end <= offset
                or name_end <= mode_end + 1
                or oid_end > len(raw)
            ):
                raise EnforcementSourceRatificationReceiptError(
                    "ratification receipt source closure tree is not exact"
                )
            mode = raw[offset:mode_end]
            name = raw[mode_end + 1:name_end]
            raw_oid = raw[name_end + 1:oid_end]
            if name in expected:
                if name in found:
                    raise EnforcementSourceRatificationReceiptError(
                        "ratification receipt source closure tree is not exact"
                    )
                found.add(name)
                relative = expected[name]
                expected_oid, _size = blob_metadata[(commit, relative)]
                if mode not in _REGULAR_SOURCE_MODES:
                    raise EnforcementSourceRatificationReceiptError(
                        "ratification receipt source closure path is not a "
                        f"regular file: {relative}"
                    )
                if raw_oid.hex() != expected_oid:
                    raise EnforcementSourceRatificationReceiptError(
                        "ratification receipt source closure tree is not exact"
                    )
            offset = oid_end
        if found != set(expected):
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure tree is incomplete"
            )


def _parse_source_batch(
    raw: bytes,
    queries: tuple[tuple[str, str, str], ...],
    tree_queries: tuple[tuple[str, str, str], ...],
    blob_metadata: Mapping[tuple[str, str], tuple[str, int]],
    tree_metadata: Mapping[tuple[str, str], tuple[str, int]],
) -> dict[str, dict[str, str]]:
    specs = _source_batch_specs(queries, tree_queries)
    cursor = 0
    digests: dict[str, dict[str, str]] = {}
    tree_blobs: dict[tuple[str, str], bytes] = {}
    for kind, commit, relative, query, rest in specs:
        header_end = raw.find(b"\n", cursor)
        if header_end < 0:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure batch is truncated"
            )
        header = raw[cursor:header_end]
        oid, size = _parse_source_header(
            header,
            query=query,
            relative=relative,
            expected_type=kind,
            expected_rest=rest,
        )
        metadata = blob_metadata if kind == b"blob" else tree_metadata
        if (oid, size) != metadata[(commit, relative)]:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure batch changed after "
                "metadata validation"
            )
        content_start = header_end + 1
        content_end = content_start + size
        if content_end >= len(raw) or raw[content_end:content_end + 1] != b"\n":
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure batch is truncated"
            )
        content = raw[content_start:content_end]
        if kind == b"blob":
            digests.setdefault(commit, {})[relative] = hashlib.sha256(
                content
            ).hexdigest()
        else:
            tree_blobs[(commit, relative)] = content
        cursor = content_end + 1
    if cursor != len(raw):
        raise EnforcementSourceRatificationReceiptError(
            "ratification receipt source closure batch has trailing output"
        )
    _validate_source_tree_modes(tree_blobs, blob_metadata, tree_queries)
    return digests


def _source_closure_digests(
    root: Path,
    source_commits: tuple[str, ...],
) -> dict[str, str]:
    unique_commits = tuple(dict.fromkeys(source_commits))
    if not unique_commits:
        return {}
    queries = tuple(
        (commit, relative, f"{commit}:{relative}")
        for commit in unique_commits
        for relative in CONTRACT_LOADER_RELATIVE_PATHS
    )
    tree_queries = _source_tree_queries(unique_commits)
    specs = _source_batch_specs(queries, tree_queries)
    request = b"".join(
        query.encode("ascii") + b" " + rest + b"\n"
        for _kind, _commit, _relative, query, rest in specs
    )
    blob_metadata, tree_metadata = _source_batch_metadata(
        root, queries, tree_queries
    )
    raw = _require_git(
        root,
        "cat-file",
        "--batch=%(objectname) %(objecttype) %(objectsize) %(rest)",
        input_bytes=request,
    )
    maps = _parse_source_batch(
        raw,
        queries,
        tree_queries,
        blob_metadata,
        tree_metadata,
    )
    result: dict[str, str] = {}
    for commit in unique_commits:
        try:
            result[commit] = closure_digest_sha256(maps[commit])
        except (KeyError, EnforcementSourceRatificationError) as exc:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source closure is incomplete"
            ) from exc
    return result


def _validate_source_bindings(
    root: Path,
    rows: tuple[dict[str, object], ...],
    parents_by_commit: Mapping[str, tuple[str, ...]],
) -> None:
    source_commits: list[str] = []
    for line_number, row in enumerate(rows, start=1):
        source_commit = cast(str, row["source_commit"])
        _require_reachable_source_commit(
            source_commit, line_number, parents_by_commit
        )
        source_commits.append(source_commit)
    digests = _source_closure_digests(root, tuple(source_commits))
    for line_number, row in enumerate(rows, start=1):
        source_commit = cast(str, row["source_commit"])
        if digests[source_commit] != row["closure_digest_sha256"]:
            raise EnforcementSourceRatificationReceiptError(
                "ratification receipt source commit closure digest disagrees: "
                f"{line_number}"
            )


def _committed_receipts(
    root: Path,
    head: str,
) -> tuple[dict[str, object], ...]:
    parents_by_commit = _full_history(root, head)
    commits = tuple(parents_by_commit)

    trust_entries, trust_sizes = _blob_oids_for_path(
        root,
        commits,
        TRUST_ROOT_RELATIVE_PATH,
        label="trust root",
    )
    trust_oid = _assert_immutable_trust_root_history(
        parents_by_commit, trust_entries
    )
    public_key = _load_trust_root(root, trust_oid, trust_sizes[trust_oid])

    ledger_entries, ledger_sizes = _blob_oids_for_path(
        root,
        commits,
        RECEIPT_LEDGER_RELATIVE_PATH,
        label="ledger",
    )
    ledger_blobs = _load_ledger_blobs(root, ledger_entries, ledger_sizes)
    head_ledger_oid = ledger_entries[head]
    if head_ledger_oid is not None:
        _validate_ledger_blob_bounds(ledger_blobs[head_ledger_oid])
    final_raw = _assert_linear_ledger_history(
        parents_by_commit, ledger_entries, ledger_blobs
    )
    rows = _load_rows(final_raw, public_key)
    _validate_source_bindings(root, rows, parents_by_commit)
    return rows


def require_signed_ratification(blob_sha256s: Mapping[str, str]) -> str:
    """Return the live closure digest only for a matching committed receipt."""
    try:
        digest = closure_digest_sha256(blob_sha256s)
    except EnforcementSourceRatificationError as exc:
        raise EnforcementSourceRatificationReceiptError(str(exc)) from exc
    root = _validated_root()
    head = _head_commit(root)
    rows = _committed_receipts(root, head)
    expected_paths = sorted(CONTRACT_LOADER_RELATIVE_PATHS)
    for row in rows:
        if (
            row["closure_digest_sha256"] == digest
            and row["closure_paths"] == expected_paths
        ):
            return digest
    raise EnforcementSourceRatificationReceiptError(
        "enforcement-source-closure-unratified: matching signed receipt is "
        "absent from committed history"
    )
