#!/usr/bin/env python3
"""RuleOps v1: HEAD-pinned inventory and human-review package validation.

This CLI is deliberately read-only.  It inventories two narrow artifact
families, emits review signals, and validates candidate package structure.  A
successful ``check`` is not deletion safety, eligibility, or human approval.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import posixpath
import re
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Collection, Iterable, Mapping, Sequence


INVENTORY_SCHEMA = "ruleops-inventory/v2"
INSPECTION_SCHEMA = "ruleops-inspection/v1"
LEDGER_SCHEMA = "ruleops-candidates/v1"
RECEIPT_SCHEMA = "ruleops-mutation-receipt/v1"
INSIGHT_MARKER_SCHEMA = "ruleops-insight/v1"
DEFAULT_LEDGER = "docs/ruleops-candidates.json"

MAX_LEDGER_BYTES = 1_048_576
MAX_RECEIPT_BYTES = 262_144
MAX_CANDIDATES = 2
MAX_PATH_BYTES = 4_096
MAX_RATIONALE_CHARS = 4_096
MAX_REVIEW_RATIONALE_CHARS = 2_048
MAX_QUERY_CHARS = 128
MAX_QUERY_COUNT = 1
MAX_SIGNAL_TOKENS = 6
MAX_EVIDENCE_ITEMS = 128
GIT_TIMEOUT_SECONDS = 20

_TEST_PATH_RE = re.compile(r"^orchestrator/tests/test_[^/]+\.py$")
_INSIGHT_PATH_RE = re.compile(r"^output/insights/.+")
_OID_RE = {
    "sha1": re.compile(r"^[0-9a-f]{40}$"),
    "sha256": re.compile(r"^[0-9a-f]{64}$"),
}
_REGULAR_MODES = frozenset({"100644", "100755"})
_GIT_SUBCOMMANDS = frozenset({
    "cat-file", "diff-tree", "for-each-ref", "grep", "log", "ls-tree",
    "merge-base", "rev-parse",
})
_ROOT_KEYS = frozenset({
    "schema_version", "authority", "default_effect", "candidates",
})
_CANDIDATE_KEYS = frozenset({
    "path", "kind", "target_blob", "rationale", "test_evidence",
})
_INSIGHT_CANDIDATE_KEYS = frozenset({
    "path", "kind", "target_blob", "rationale", "insight_evidence",
})
_TEST_EVIDENCE_KEYS = frozenset({
    "replacement_guards", "replacement_nodes", "semantic_queries",
    "observed_hits", "pickaxe_events", "mutation_receipts",
})
_INSIGHT_EVIDENCE_KEYS = frozenset({
    "artifact_class", "source_artifacts", "observed_hits", "pickaxe_events",
})
_BLOB_REF_KEYS = frozenset({"path", "blob"})
_NODE_REF_KEYS = frozenset({"nodeid", "blob"})
_OBSERVED_HIT_KEYS = frozenset({
    "query", "path", "blob", "line", "review", "rationale",
})
_PICKAXE_EVENT_KEYS = frozenset({
    "query", "commit", "review", "rationale",
})
_RECEIPT_KEYS = frozenset({
    "schema_version", "authority", "default_effect", "candidate_path",
    "candidate_blob", "head", "candidate_excluded", "baseline_rc",
    "restored_rc", "review_state", "mutants", "advisory_only",
    "human_review_required",
})
_MUTANT_KEYS = frozenset({"guard_path", "status", "failed_nodes"})
_REVIEWS = frozenset({"relevant", "not-relevant"})
_MUTANT_STATUSES = frozenset({"KILLED", "SURVIVED", "ERROR", "NOT_RUN"})
_INSIGHT_MARKER_KEYS = frozenset({
    "schema_version", "authority", "default_effect",
})
_INSIGHT_MARKER_PREFIX = b"<!-- ruleops-insight: "
_INSIGHT_MARKER_SUFFIX = b" -->\n"
_GIT_CONFIG_OVERRIDES = (
    ("core.useReplaceRefs", "false"),
    ("log.showSignature", "false"),
    ("diff.external", ""),
    ("diff.trustExitCode", "false"),
    ("submodule.recurse", "false"),
    ("grep.recurseSubmodules", "false"),
)


class RuleOpsError(RuntimeError):
    """Fail-closed validation error with a stable reason code."""

    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        super().__init__(detail)


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str
    oid: str
    size: int | None
    path: str


@dataclass(frozen=True)
class RepoSnapshot:
    repo: Path
    head: str
    object_format: str
    entries: Mapping[str, TreeEntry]
    blob_cache: dict[str, bytes] = field(default_factory=dict, compare=False)
    grep_cache: dict[str, tuple[str, ...]] = field(default_factory=dict, compare=False)
    pickaxe_cache: dict[
        str,
        tuple[tuple[str, tuple[str, ...]], ...],
    ] = field(default_factory=dict, compare=False)
    control_change_cache: dict[
        tuple[tuple[str, str], ...],
        dict[str, str],
    ] = field(default_factory=dict, compare=False)


def _fail(reason: str, detail: str) -> None:
    raise RuleOpsError(reason, detail)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise RuleOpsError("json-domain", f"canonical JSON 化不能: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate-key", f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _fail("non-finite-json", f"non-finite JSON value: {value}")


def _check_json_domain(value: Any, *, label: str) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if item is None or isinstance(item, (str, bool, int)):
            if isinstance(item, str) and unicodedata.normalize("NFC", item) != item:
                _fail("non-nfc", f"{label}: string は Unicode NFC でなければならない")
            continue
        if isinstance(item, list):
            stack.extend(item)
            continue
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    _fail("json-domain", f"{label}: object key が string でない")
                if unicodedata.normalize("NFC", key) != key:
                    _fail("non-nfc", f"{label}: key は Unicode NFC でなければならない")
                stack.append(child)
            continue
        _fail("json-domain", f"{label}: 禁止 JSON 型 {type(item).__name__}")


def _strict_json(raw: bytes, *, label: str, max_bytes: int) -> Any:
    if not raw:
        _fail("empty-json", f"{label}: 空ファイル")
    if len(raw) > max_bytes:
        _fail("oversize-json", f"{label}: {len(raw)} bytes > {max_bytes}")
    if raw.startswith(b"\xef\xbb\xbf"):
        _fail("bom-json", f"{label}: UTF-8 BOM は禁止")
    if b"\x00" in raw or b"\r" in raw:
        _fail("noncanonical-json", f"{label}: NUL/CR は禁止")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise RuleOpsError("non-utf8", f"{label}: UTF-8 不正") from exc
    if unicodedata.normalize("NFC", text) != text:
        _fail("non-nfc", f"{label}: Unicode NFC でなければならない")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except RuleOpsError:
        raise
    except (json.JSONDecodeError, ValueError, OverflowError, RecursionError) as exc:
        raise RuleOpsError("invalid-json", f"{label}: JSON parse 失敗: {exc}") from exc
    _check_json_domain(value, label=label)
    return value


def _exact_dict(value: Any, keys: frozenset[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("schema-type", f"{label}: object でなければならない")
    actual = frozenset(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        _fail("schema-keys", f"{label}: missing={missing}, unknown={extra}")
    return value


def _string(
    value: Any,
    *,
    label: str,
    minimum: int = 1,
    maximum: int,
    enum: frozenset[str] | None = None,
) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        _fail("schema-type", f"{label}: string length {minimum}..{maximum} が必要")
    if enum is not None and value not in enum:
        _fail("schema-enum", f"{label}: 許可外の値 {value!r}")
    return value


def _review_text(
    value: Any,
    *,
    label: str,
    minimum: int = 1,
    maximum: int,
) -> str:
    text = _string(value, label=label, minimum=minimum, maximum=maximum)
    if any(unicodedata.category(character) == "Cc" for character in text):
        _fail("control-character", f"{label}: control character は禁止")
    stripped = text.strip()
    if len(stripped) < minimum:
        _fail("empty-text", f"{label}: strip 後の nonempty string が必要")
    return stripped


def _integer(value: Any, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail("schema-type", f"{label}: integer >= {minimum} が必要")
    return value


def _array(
    value: Any,
    *,
    label: str,
    minimum: int = 0,
    maximum: int = MAX_EVIDENCE_ITEMS,
    overflow_reason: str = "evidence-overflow",
) -> list[Any]:
    if not isinstance(value, list):
        _fail("schema-type", f"{label}: array が必要")
    if len(value) > maximum:
        _fail(overflow_reason, f"{label}: {len(value)} items > {maximum}")
    if len(value) < minimum:
        _fail("schema-type", f"{label}: array length {minimum}..{maximum} が必要")
    return value


def _repo_path(value: Any, *, label: str) -> str:
    text = _string(value, label=label, maximum=MAX_PATH_BYTES)
    try:
        encoded = text.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise RuleOpsError("path-utf8", f"{label}: UTF-8 化不能") from exc
    if len(encoded) > MAX_PATH_BYTES:
        _fail("path-oversize", f"{label}: path bytes > {MAX_PATH_BYTES}")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or "\\" in text
        or text.startswith("./")
        or text.endswith("/")
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != text
    ):
        _fail("unsafe-path", f"{label}: repo-relative canonical path でない: {text!r}")
    return text


def _git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
        "LANG": "C",
    })
    return env


def _git_read(
    repo: Path,
    subcommand: str,
    *args: str,
    input_bytes: bytes | None = None,
    allowed_rc: frozenset[int] = frozenset({0}),
) -> bytes:
    """Run one command from the closed read-only Git set."""

    if subcommand not in _GIT_SUBCOMMANDS:
        _fail("git-subcommand", f"read-only closed set 外: {subcommand}")
    command = ["git", "--no-optional-locks"]
    for key, value in _GIT_CONFIG_OVERRIDES:
        command.extend(("-c", f"{key}={value}"))
    command.extend(("-C", str(repo), subcommand))
    if subcommand in {"diff-tree", "log"}:
        command.extend((
            "--no-show-signature",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=all",
        ))
    elif subcommand == "grep":
        command.append("--no-recurse-submodules")
    command.extend(args)
    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuleOpsError("git-timeout", f"git {subcommand} timeout") from exc
    except OSError as exc:
        raise RuleOpsError("git-unavailable", f"git {subcommand} 実行不能: {exc}") from exc
    if result.returncode not in allowed_rc:
        try:
            detail = result.stderr.decode("utf-8", "strict").strip()
        except UnicodeDecodeError as exc:
            raise RuleOpsError("git-non-utf8", f"git {subcommand} stderr が非 UTF-8") from exc
        _fail("git-failed", f"git {subcommand} rc={result.returncode}: {detail}")
    return result.stdout


def _git_text(repo: Path, subcommand: str, *args: str) -> str:
    raw = _git_read(repo, subcommand, *args)
    try:
        return raw.decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise RuleOpsError("git-non-utf8", f"git {subcommand} stdout が非 UTF-8") from exc


def _capture_snapshot(repo_value: Path | str) -> RepoSnapshot:
    repo = Path(repo_value).resolve()
    if not repo.is_dir():
        _fail("repo-missing", f"repo directory がない: {repo}")
    object_format = _git_text(repo, "rev-parse", "--show-object-format")
    if object_format not in _OID_RE:
        _fail("object-format", f"未対応 object format: {object_format!r}")
    head = _git_text(repo, "rev-parse", "HEAD")
    if _OID_RE[object_format].fullmatch(head) is None:
        _fail("bad-oid", f"HEAD OID が {object_format} 形式でない")
    _assert_history_boundary(repo)
    raw_tree = _git_read(repo, "ls-tree", "-r", "-l", "-z", head, "--")
    entries: dict[str, TreeEntry] = {}
    for chunk in raw_tree.split(b"\0"):
        if not chunk:
            continue
        try:
            meta_raw, path_raw = chunk.split(b"\t", 1)
            meta = meta_raw.decode("ascii", "strict").split()
            path = path_raw.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuleOpsError("bad-ls-tree", "ls-tree 出力を解釈できない") from exc
        if len(meta) != 4:
            _fail("bad-ls-tree", f"ls-tree metadata field 数不正: {meta!r}")
        mode, kind, oid, size_text = meta
        if _OID_RE[object_format].fullmatch(oid) is None:
            _fail("bad-oid", f"tree OID が不正: {path}")
        if path in entries:
            _fail("duplicate-tree-path", f"HEAD tree path 重複: {path}")
        size = None if size_text == "-" else _integer_text(size_text, label=f"{path}:size")
        entries[path] = TreeEntry(mode, kind, oid, size, path)
    return RepoSnapshot(repo, head, object_format, entries)


def _assert_history_boundary(repo: Path) -> None:
    shallow = _git_text(repo, "rev-parse", "--is-shallow-repository")
    if shallow != "false":
        _fail("shallow-repo", "non-shallow repository が必要")
    replacements = _git_text(
        repo, "for-each-ref", "--format=%(refname)", "refs/replace/",
    )
    if replacements:
        _fail("replace-refs", "refs/replace/* が存在する")
    graft_text = _git_text(repo, "rev-parse", "--git-path", "info/grafts")
    graft_path = Path(graft_text)
    if not graft_path.is_absolute():
        graft_path = repo / graft_path
    if graft_path.exists():
        _fail("grafts", f"grafts が存在する: {graft_path}")


def _assert_snapshot_current(snapshot: RepoSnapshot) -> None:
    current = _git_text(snapshot.repo, "rev-parse", "HEAD")
    if current != snapshot.head:
        _fail(
            "head-moved",
            f"HEAD moved during RuleOps query: {snapshot.head} -> {current}",
        )
    _assert_history_boundary(snapshot.repo)


def _integer_text(value: str, *, label: str) -> int:
    if not value.isascii() or not value.isdigit():
        _fail("bad-integer", f"{label}: non-negative integer でない")
    return int(value)


def _scoped_kind(path: str) -> str | None:
    if _TEST_PATH_RE.fullmatch(path):
        return "test"
    if _INSIGHT_PATH_RE.fullmatch(path):
        return "insight"
    return None


def _regular_blob(snapshot: RepoSnapshot, path: str, *, label: str) -> TreeEntry:
    entry = snapshot.entries.get(path)
    if entry is None:
        _fail("missing-path", f"{label}: HEAD に存在しない: {path}")
    if entry.kind != "blob" or entry.mode not in _REGULAR_MODES or entry.size is None:
        _fail("non-regular", f"{label}: tracked regular blob でない: {path}")
    return entry


def _blob(snapshot: RepoSnapshot, entry: TreeEntry) -> bytes:
    cached = snapshot.blob_cache.get(entry.oid)
    if cached is not None:
        return cached
    raw = _git_read(snapshot.repo, "cat-file", "blob", entry.oid)
    if entry.size is None or len(raw) != entry.size:
        _fail("blob-size-drift", f"{entry.path}: tree size と blob bytes が不一致")
    snapshot.blob_cache[entry.oid] = raw
    return raw


def _batch_blobs(
    snapshot: RepoSnapshot, entries: Sequence[TreeEntry],
) -> dict[str, bytes]:
    unique = {entry.oid: entry for entry in entries}
    if not unique:
        return {}
    cached = {
        oid: snapshot.blob_cache[oid]
        for oid in unique
        if oid in snapshot.blob_cache
    }
    unique = {oid: entry for oid, entry in unique.items() if oid not in cached}
    if not unique:
        return cached
    request = b"".join(oid.encode("ascii") + b"\n" for oid in unique)
    raw = _git_read(
        snapshot.repo,
        "cat-file",
        "--batch",
        input_bytes=request,
    )
    offset = 0
    result: dict[str, bytes] = dict(cached)
    for expected_oid, expected_entry in unique.items():
        newline = raw.find(b"\n", offset)
        if newline < 0:
            _fail("bad-cat-file", "cat-file --batch header が途中で終わった")
        try:
            header = raw[offset:newline].decode("ascii", "strict").split()
        except UnicodeDecodeError as exc:
            raise RuleOpsError("bad-cat-file", "cat-file header が非 ASCII") from exc
        if len(header) != 3:
            _fail("bad-cat-file", f"cat-file header 不正: {header!r}")
        oid, kind, size_text = header
        size = _integer_text(size_text, label=f"{expected_entry.path}:batch-size")
        start = newline + 1
        end = start + size
        if (
            oid != expected_oid
            or kind != "blob"
            or size != expected_entry.size
            or end >= len(raw)
            or raw[end:end + 1] != b"\n"
        ):
            _fail("bad-cat-file", f"cat-file batch response 不一致: {expected_entry.path}")
        result[oid] = raw[start:end]
        snapshot.blob_cache[oid] = raw[start:end]
        offset = end + 1
    if offset != len(raw):
        _fail("bad-cat-file", "cat-file batch response に余剰 bytes")
    return result


def _blob_text(snapshot: RepoSnapshot, entry: TreeEntry, *, label: str) -> str:
    try:
        return _blob(snapshot, entry).decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise RuleOpsError("non-utf8", f"{label}: blob が非 UTF-8: {entry.path}") from exc


def _last_changes(
    snapshot: RepoSnapshot, paths: Iterable[str],
) -> dict[str, tuple[str, str]]:
    wanted = frozenset(paths)
    if not wanted:
        return {}
    raw = _git_read(
        snapshot.repo,
        "log",
        "-z",
        "--diff-merges=first-parent",
        "--format=RULEOPS-COMMIT:%H%x09%cI",
        "--name-only",
        snapshot.head,
        "--",
        ":(top,literal)orchestrator/tests",
        ":(top,literal)output/insights",
    )
    current: tuple[str, str] | None = None
    result: dict[str, tuple[str, str]] = {}
    for raw_token in raw.split(b"\0"):
        if not raw_token:
            continue
        token = raw_token[1:] if raw_token.startswith(b"\n") else raw_token
        try:
            text = token.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise RuleOpsError("bad-history", "history token が非 UTF-8") from exc
        if text.startswith("RULEOPS-COMMIT:"):
            rendered = text[len("RULEOPS-COMMIT:"):]
            try:
                commit, timestamp = rendered.split("\t", 1)
            except ValueError as exc:
                raise RuleOpsError("bad-history", "history commit marker 不正") from exc
            if _OID_RE[snapshot.object_format].fullmatch(commit) is None or not timestamp:
                _fail("bad-history", f"history commit marker 不正: {rendered!r}")
            current = (commit, timestamp)
            continue
        if current is None:
            _fail("bad-history", f"commit marker 前に path: {text!r}")
        if text in wanted and text not in result:
            result[text] = current
    missing = sorted(wanted - set(result))
    if missing:
        _fail("bad-history", f"last change を取得できない: {missing[:3]}")
    return result


def _artifact_format(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    return {
        ".json": "json",
        ".md": "markdown",
        ".patch": "patch",
        ".py": "python",
        ".sh": "shell",
        ".txt": "text",
    }.get(suffix, "other")


def _typed_insight_marker(raw: bytes) -> bool:
    if not raw.startswith(_INSIGHT_MARKER_PREFIX):
        return False
    end = raw.find(_INSIGHT_MARKER_SUFFIX)
    if end < 0:
        return False
    marker_end = end + len(_INSIGHT_MARKER_SUFFIX)
    if _INSIGHT_MARKER_PREFIX in raw[marker_end:]:
        return False
    marker_raw = raw[len(_INSIGHT_MARKER_PREFIX):end]
    try:
        document = _exact_dict(
            _strict_json(
                marker_raw,
                label="typed insight marker",
                max_bytes=1_024,
            ),
            _INSIGHT_MARKER_KEYS,
            label="typed insight marker",
        )
    except RuleOpsError:
        return False
    if marker_raw + b"\n" != _canonical_json_bytes(document):
        return False
    return (
        document["schema_version"] == INSIGHT_MARKER_SCHEMA
        and document["authority"] == "none"
        and document["default_effect"] == "no-state-change"
    )


def _markers(raw: bytes, *, artifact_format: str) -> tuple[str | None, str | None]:
    if artifact_format == "markdown" and _typed_insight_marker(raw):
        return "none", "no-state-change"
    if artifact_format != "json":
        return None, None
    try:
        parsed = _strict_json(raw, label="inventory JSON", max_bytes=MAX_LEDGER_BYTES)
    except RuleOpsError:
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    authority = "none" if parsed.get("authority") == "none" else None
    default_effect = (
        "no-state-change"
        if parsed.get("default_effect") == "no-state-change"
        else None
    )
    return authority, default_effect


def build_inventory(
    repo: Path | str, *, kind: str = "all", snapshot: RepoSnapshot | None = None,
) -> dict[str, Any]:
    if kind not in {"all", "test", "insight"}:
        _fail("kind", f"inventory kind が不正: {kind!r}")
    snap = snapshot or _capture_snapshot(repo)
    selected: list[tuple[str, str, TreeEntry]] = []
    for path in sorted(snap.entries):
        scoped = _scoped_kind(path)
        if scoped is None or (kind != "all" and kind != scoped):
            continue
        entry = snap.entries[path]
        if (
            entry.kind == "blob"
            and entry.mode in _REGULAR_MODES
            and entry.size is not None
        ):
            selected.append((path, scoped, entry))
    blobs = _batch_blobs(snap, [entry for _, _, entry in selected])
    changes = _last_changes(snap, [path for path, _, _ in selected])
    items: list[dict[str, Any]] = []
    skipped_non_utf8 = 0
    for path, scoped, entry in selected:
        raw = blobs[entry.oid]
        try:
            raw.decode("utf-8", "strict")
        except UnicodeDecodeError:
            skipped_non_utf8 += 1
            continue
        last_commit, changed_at = changes[path]
        artifact_format = _artifact_format(path)
        authority, default_effect = _markers(raw, artifact_format=artifact_format)
        items.append({
            "artifact_format": artifact_format,
            "authority_marker": authority,
            "blob": entry.oid,
            "bytes": entry.size,
            "default_effect_marker": default_effect,
            "kind": scoped,
            "last_change_commit": last_commit,
            "last_changed_at": changed_at,
            "mode": entry.mode,
            "path": path,
        })
    output = {
        "head": snap.head,
        "items": items,
        "object_format": snap.object_format,
        "schema_version": INVENTORY_SCHEMA,
        "skipped_non_utf8": skipped_non_utf8,
    }
    _assert_snapshot_current(snap)
    return output


def _tree_path_map(snapshot: RepoSnapshot) -> dict[str, TreeEntry]:
    return {
        path: entry for path, entry in snapshot.entries.items()
        if entry.kind == "blob" and entry.mode in _REGULAR_MODES and entry.size is not None
    }


def _grep_names(snapshot: RepoSnapshot, token: str) -> tuple[str, ...]:
    cached = snapshot.grep_cache.get(token)
    if cached is not None:
        return cached
    raw = _git_read(
        snapshot.repo,
        "grep",
        "-I",
        "-F",
        "-l",
        "-z",
        "-e",
        token,
        snapshot.head,
        "--",
        allowed_rc=frozenset({0, 1}),
    )
    if not raw:
        return ()
    names: list[str] = []
    for chunk in raw.split(b"\0"):
        if not chunk:
            continue
        try:
            rendered = chunk.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise RuleOpsError("git-non-utf8", "git grep path が非 UTF-8") from exc
        prefix = f"{snapshot.head}:"
        if not rendered.startswith(prefix):
            _fail("bad-grep", f"git grep path を解釈できない: {rendered!r}")
        names.append(rendered[len(prefix):])
    result = tuple(sorted(set(names)))
    snapshot.grep_cache[token] = result
    return result


def _observed_hits(
    snapshot: RepoSnapshot,
    tokens: Sequence[str],
    controls: Mapping[str, str],
    *,
    link_target: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = _tree_path_map(snapshot)
    hits: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for token in sorted(set(tokens)):
        for path in _grep_names(snapshot, token):
            entry = entries.get(path)
            if entry is None:
                _fail("grep-drift", f"grep hit が regular HEAD blob でない: {path}")
            text = _blob_text(snapshot, entry, label="observed hit")
            for number, line in enumerate(text.splitlines(), 1):
                if token not in line:
                    continue
                item = {
                    "blob": entry.oid,
                    "line": number,
                    "path": path,
                    "query": token,
                }
                is_control = controls.get(path) == entry.oid
                (excluded if is_control else hits).append(item)
    basename = PurePosixPath(link_target).name
    markdown_link = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
    for path in _grep_names(snapshot, basename):
        if PurePosixPath(path).suffix.lower() != ".md":
            continue
        entry = entries.get(path)
        if entry is None:
            continue
        text = _blob_text(snapshot, entry, label="Markdown link hit")
        for number, line in enumerate(text.splitlines(), 1):
            for match in markdown_link.finditer(line):
                destination = match.group(1).split("#", 1)[0]
                if (
                    not destination
                    or destination.startswith("/")
                    or "://" in destination
                    or destination.startswith("mailto:")
                ):
                    continue
                resolved = posixpath.normpath(
                    posixpath.join(PurePosixPath(path).parent.as_posix(), destination),
                )
                if resolved != link_target:
                    continue
                item = {
                    "blob": entry.oid,
                    "line": number,
                    "path": path,
                    "query": link_target,
                }
                is_control = controls.get(path) == entry.oid
                (excluded if is_control else hits).append(item)
    hits = list({
        (x["query"], x["path"], x["line"], x["blob"]): x for x in hits
    }.values())
    excluded = list({
        (x["query"], x["path"], x["line"], x["blob"]): x for x in excluded
    }.values())
    key = lambda item: (
        item["query"], item["path"], item["line"], item["blob"],
    )
    return sorted(hits, key=key), sorted(excluded, key=key)


def _parse_pickaxe_paths(
    snapshot: RepoSnapshot,
    raw: bytes,
) -> dict[str, set[str]]:
    current: str | None = None
    result: dict[str, set[str]] = {}
    for raw_token in raw.split(b"\0"):
        if not raw_token:
            continue
        token = raw_token[1:] if raw_token.startswith(b"\n") else raw_token
        try:
            text = token.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise RuleOpsError("bad-history", "pickaxe path output が非 UTF-8") from exc
        if text.startswith("RULEOPS-COMMIT:"):
            commit = text[len("RULEOPS-COMMIT:"):]
            if _OID_RE[snapshot.object_format].fullmatch(commit) is None:
                _fail("bad-history", f"pickaxe OID 不正: {commit!r}")
            current = commit
            result.setdefault(commit, set())
            continue
        if current is None:
            _fail("bad-history", f"pickaxe commit marker 前に path: {text!r}")
        result[current].add(text)
    return result


def _control_last_changes(
    snapshot: RepoSnapshot,
    controls: Mapping[str, str],
) -> dict[str, str]:
    key = tuple(sorted(controls.items()))
    cached = snapshot.control_change_cache.get(key)
    if cached is not None:
        return cached
    if not key:
        return {}
    raw = _git_read(
        snapshot.repo,
        "log",
        "-z",
        "--diff-merges=first-parent",
        "--format=RULEOPS-COMMIT:%H",
        "--name-only",
        snapshot.head,
        "--",
        *(f":(top,literal){path}" for path, _ in key),
    )
    by_commit = _parse_pickaxe_paths(snapshot, raw)
    result: dict[str, str] = {}
    for commit, paths in by_commit.items():
        for path in paths:
            if path in controls and path not in result:
                result[path] = commit
    missing = sorted(set(controls) - set(result))
    if missing:
        _fail("bad-history", f"control last change を取得できない: {missing}")
    snapshot.control_change_cache[key] = result
    return result


def _pickaxe(
    snapshot: RepoSnapshot,
    tokens: Sequence[str],
    controls: Mapping[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    events: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    control_changes = _control_last_changes(snapshot, controls)
    for token in sorted(set(tokens)):
        cached = snapshot.pickaxe_cache.get(token)
        if cached is None:
            raw = _git_read(
                snapshot.repo,
                "log",
                "-z",
                "--diff-merges=first-parent",
                "--format=RULEOPS-COMMIT:%H",
                "--name-only",
                f"-S{token}",
                snapshot.head,
                "--",
                ":(top)",
            )
            by_commit = _parse_pickaxe_paths(snapshot, raw)
            cached = tuple(
                (commit, tuple(sorted(paths)))
                for commit, paths in by_commit.items()
            )
            snapshot.pickaxe_cache[token] = cached
        token_events: list[dict[str, str]] = []
        token_excluded: list[dict[str, str]] = []
        for commit, raw_paths in cached:
            paths = set(raw_paths)
            exact_controls: set[str] = set()
            for path in paths:
                entry = snapshot.entries.get(path)
                if (
                    entry is not None
                    and controls.get(path) == entry.oid
                    and control_changes.get(path) == commit
                    and token.encode("utf-8") in _blob(snapshot, entry)
                ):
                    exact_controls.add(path)
            if paths and paths == exact_controls:
                token_excluded.extend(
                    {"commit": commit, "path": path, "query": token}
                    for path in sorted(exact_controls)
                )
            else:
                token_events.append({"commit": commit, "query": token})
        token_events.sort(key=lambda item: item["commit"])
        token_excluded.sort(key=lambda item: (item["path"], item["commit"]))
        events.extend(token_events)
        excluded.extend(token_excluded)
    events = list({(x["query"], x["commit"]): x for x in events}.values())
    excluded = list({
        (x["query"], x["commit"], x["path"]): x for x in excluded
    }.values())
    return (
        sorted(events, key=lambda x: (x["query"], x["commit"])),
        sorted(excluded, key=lambda x: (x["query"], x["path"], x["commit"])),
    )


def _unique_basename(snapshot: RepoSnapshot, path: str) -> bool:
    basename = PurePosixPath(path).name
    return sum(
        1 for candidate, entry in snapshot.entries.items()
        if PurePosixPath(candidate).name == basename
        and entry.kind == "blob"
        and entry.mode in _REGULAR_MODES
    ) == 1


def _default_controls(
    snapshot: RepoSnapshot, target: str,
) -> dict[str, str]:
    controls: dict[str, str] = {}
    ledger_file = snapshot.repo / DEFAULT_LEDGER
    try:
        entry = snapshot.entries.get(DEFAULT_LEDGER)
        if (
            entry is not None
            and entry.kind == "blob"
            and entry.mode in _REGULAR_MODES
            and entry.size is not None
            and entry.size <= MAX_LEDGER_BYTES
            and ledger_file.is_file()
            and not ledger_file.is_symlink()
        ):
            raw = _read_regular_file_bounded(
                ledger_file,
                label=DEFAULT_LEDGER,
                max_bytes=MAX_LEDGER_BYTES,
            )
            head_raw = _blob(snapshot, entry)
            if raw != head_raw:
                return controls
            doc = _strict_ledger_control(head_raw, label=DEFAULT_LEDGER)
            controls[DEFAULT_LEDGER] = entry.oid
            if isinstance(doc, dict) and isinstance(doc.get("candidates"), list):
                for candidate in doc["candidates"]:
                    if not isinstance(candidate, dict) or candidate.get("path") != target:
                        continue
                    evidence = candidate.get("test_evidence")
                    if isinstance(evidence, dict):
                        receipts = evidence.get("mutation_receipts")
                        if isinstance(receipts, list):
                            for receipt in receipts:
                                if isinstance(receipt, dict) and isinstance(
                                    receipt.get("path"), str,
                                ):
                                    receipt_path = receipt["path"]
                                    receipt_entry = snapshot.entries.get(receipt_path)
                                    if (
                                        receipt_entry is not None
                                        and _strict_receipt_control(
                                            snapshot,
                                            receipt_entry,
                                        )
                                    ):
                                        controls[receipt_path] = receipt_entry.oid
    except (OSError, RuleOpsError):
        # Inspect remains a dry-run even while a human is drafting an invalid ledger.
        pass
    return controls


def _signal_tokens(
    snapshot: RepoSnapshot, target: str, queries: Sequence[str],
) -> tuple[str, ...]:
    tokens = [target, *queries]
    if _unique_basename(snapshot, target):
        tokens.append(PurePosixPath(target).name)
    return tuple(sorted(set(tokens)))


def _inventory_item(snapshot: RepoSnapshot, path: str, kind: str) -> dict[str, Any]:
    entry = _regular_blob(snapshot, path, label="inspect target")
    raw = _blob(snapshot, entry)
    try:
        raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise RuleOpsError("non-utf8", f"inspect target が非 UTF-8: {path}") from exc
    last_commit, changed_at = _last_changes(snapshot, (path,))[path]
    artifact_format = _artifact_format(path)
    authority, default_effect = _markers(raw, artifact_format=artifact_format)
    return {
        "artifact_format": artifact_format,
        "authority_marker": authority,
        "blob": entry.oid,
        "bytes": entry.size,
        "default_effect_marker": default_effect,
        "kind": kind,
        "last_change_commit": last_commit,
        "last_changed_at": changed_at,
        "mode": entry.mode,
        "path": path,
    }


def _check_signal_limit(
    observed: Sequence[Mapping[str, Any]],
    pickaxe: Sequence[Mapping[str, Any]],
    *,
    label: str,
) -> None:
    if len(observed) > MAX_EVIDENCE_ITEMS:
        _fail(
            "evidence-overflow",
            f"{label}: observed_hits {len(observed)} > {MAX_EVIDENCE_ITEMS}",
        )
    if len(pickaxe) > MAX_EVIDENCE_ITEMS:
        _fail(
            "evidence-overflow",
            f"{label}: pickaxe_events {len(pickaxe)} > {MAX_EVIDENCE_ITEMS}",
        )


def inspect_target(
    repo: Path | str,
    path: str,
    *,
    queries: Sequence[str] = (),
    draft: bool = False,
) -> dict[str, Any]:
    snapshot = _capture_snapshot(repo)
    target = _repo_path(path, label="inspect path")
    scoped = _scoped_kind(target)
    if scoped is None:
        _fail("out-of-scope", f"RuleOps scope 外: {target}")
    if len(queries) > MAX_QUERY_COUNT:
        _fail("query-limit", f"query は最大 {MAX_QUERY_COUNT} 件")
    normalized_queries: list[str] = []
    for index, query in enumerate(queries):
        text = _review_text(
            query,
            label=f"query[{index}]",
            minimum=2,
            maximum=MAX_QUERY_CHARS,
        )
        if text in normalized_queries:
            _fail("duplicate-query", f"query 重複: {text!r}")
        normalized_queries.append(text)
    item = _inventory_item(snapshot, target, scoped)
    controls = _default_controls(snapshot, target)
    tokens = _signal_tokens(snapshot, target, normalized_queries)
    observed, excluded_observed = _observed_hits(
        snapshot, tokens, controls, link_target=target,
    )
    pickaxe, excluded_pickaxe = _pickaxe(snapshot, tokens, controls)
    _check_signal_limit(observed, pickaxe, label=target)
    candidate = None
    receipt_draft = None
    if draft:
        common = {
            "kind": scoped,
            "path": target,
            "rationale": "",
            "target_blob": item["blob"],
        }
        if scoped == "test":
            receipt_draft = {
                "advisory_only": True,
                "authority": "none",
                "baseline_rc": 0,
                "candidate_blob": item["blob"],
                "candidate_excluded": True,
                "candidate_path": target,
                "default_effect": "no-state-change",
                "head": snapshot.head,
                "human_review_required": True,
                "mutants": [
                    {
                        "failed_nodes": [],
                        "guard_path": "",
                        "status": "NOT_RUN",
                    },
                ],
                "restored_rc": 0,
                "review_state": "pending",
                "schema_version": RECEIPT_SCHEMA,
            }
            common["test_evidence"] = {
                "mutation_receipts": [],
                "observed_hits": [
                    {**hit, "rationale": "", "review": "unresolved"}
                    for hit in observed
                ],
                "pickaxe_events": [
                    {**event, "rationale": "", "review": "unresolved"}
                    for event in pickaxe
                ],
                "replacement_guards": [],
                "replacement_nodes": [],
                "semantic_queries": normalized_queries,
            }
        else:
            common["insight_evidence"] = {
                "artifact_class": "derived-report",
                "observed_hits": [
                    {**hit, "rationale": "", "review": "unresolved"}
                    for hit in observed
                ],
                "pickaxe_events": [
                    {**event, "rationale": "", "review": "unresolved"}
                    for event in pickaxe
                ],
                "source_artifacts": [],
            }
        candidate = common
    output = {
        "candidate_draft": candidate,
        "excluded_hits": {
            "observed_hits": excluded_observed,
            "pickaxe_events": excluded_pickaxe,
        },
        "head": snapshot.head,
        "observed_hits": observed,
        "pickaxe_events": pickaxe,
        "schema_version": INSPECTION_SCHEMA,
        "target": item,
        "mutation_receipt_draft": receipt_draft,
    }
    _assert_snapshot_current(snapshot)
    return output


def _ledger_file(repo: Path, value: Path | str) -> tuple[Path, str]:
    raw_path = Path(value)
    if raw_path.is_absolute():
        try:
            lexical_rel = raw_path.relative_to(repo).as_posix()
        except ValueError as exc:
            raise RuleOpsError(
                "unsafe-ledger", f"ledger は repo 内実在 path が必要: {value}",
            ) from exc
    else:
        lexical_rel = raw_path.as_posix()
        _repo_path(lexical_rel, label="ledger path")
        raw_path = repo / raw_path
    _repo_path(lexical_rel, label="ledger path")
    current = repo
    for part in PurePosixPath(lexical_rel).parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise RuleOpsError("ledger-unreadable", f"ledger component を読めない: {current}") from exc
        if stat.S_ISLNK(mode):
            _fail("ledger-symlink", f"ledger symlink component: {current}")
    try:
        resolved = raw_path.resolve(strict=True)
        rel = resolved.relative_to(repo).as_posix()
    except (OSError, ValueError) as exc:
        raise RuleOpsError("unsafe-ledger", f"ledger は repo 内実在 path が必要: {value}") from exc
    _repo_path(rel, label="ledger path")
    if not stat.S_ISREG(resolved.stat().st_mode):
        _fail("ledger-nonregular", f"ledger は regular file でない: {resolved}")
    return resolved, rel


def _read_regular_file_bounded(
    path: Path,
    *,
    label: str,
    max_bytes: int,
) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuleOpsError("ledger-unreadable", f"{label}: open 失敗: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            _fail("ledger-nonregular", f"{label}: regular file でない")
        if metadata.st_size > max_bytes:
            _fail("oversize-json", f"{label}: {metadata.st_size} bytes > {max_bytes}")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > max_bytes:
            _fail("oversize-json", f"{label}: bytes > {max_bytes}")
        return raw
    except OSError as exc:
        raise RuleOpsError("ledger-unreadable", f"{label}: read 失敗: {exc}") from exc
    finally:
        os.close(descriptor)


def _strict_ledger_control(raw: bytes, *, label: str) -> dict[str, Any]:
    root = _exact_dict(
        _strict_json(raw, label=label, max_bytes=MAX_LEDGER_BYTES),
        _ROOT_KEYS,
        label=label,
    )
    if (
        root["schema_version"] != LEDGER_SCHEMA
        or root["authority"] != "none"
        or root["default_effect"] != "no-state-change"
    ):
        _fail("ledger-schema", f"{label}: strict RuleOps ledger marker 不正")
    candidates = _array(
        root["candidates"],
        label=f"{label}.candidates",
        maximum=MAX_CANDIDATES,
        overflow_reason="candidate-limit",
    )
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            _fail("schema-type", f"{label}.candidate[{index}]: object が必要")
        kind = raw_candidate.get("kind")
        keys = _CANDIDATE_KEYS if kind == "test" else _INSIGHT_CANDIDATE_KEYS
        candidate = _exact_dict(
            raw_candidate,
            keys,
            label=f"{label}.candidate[{index}]",
        )
        if kind == "test":
            evidence = _exact_dict(
                candidate["test_evidence"],
                _TEST_EVIDENCE_KEYS,
                label=f"{label}.candidate[{index}].test_evidence",
            )
            array_keys = (
                "replacement_guards",
                "replacement_nodes",
                "semantic_queries",
                "observed_hits",
                "pickaxe_events",
                "mutation_receipts",
            )
            nested_keys = {
                "replacement_guards": _BLOB_REF_KEYS,
                "replacement_nodes": _NODE_REF_KEYS,
                "observed_hits": _OBSERVED_HIT_KEYS,
                "pickaxe_events": _PICKAXE_EVENT_KEYS,
                "mutation_receipts": _BLOB_REF_KEYS,
            }
        elif kind == "insight":
            evidence = _exact_dict(
                candidate["insight_evidence"],
                _INSIGHT_EVIDENCE_KEYS,
                label=f"{label}.candidate[{index}].insight_evidence",
            )
            array_keys = ("source_artifacts", "observed_hits", "pickaxe_events")
            nested_keys = {
                "source_artifacts": _BLOB_REF_KEYS,
                "observed_hits": _OBSERVED_HIT_KEYS,
                "pickaxe_events": _PICKAXE_EVENT_KEYS,
            }
        else:
            _fail("kind-drift", f"{label}.candidate[{index}]: kind 不正")
        for key in array_keys:
            maximum = MAX_QUERY_COUNT if key == "semantic_queries" else MAX_EVIDENCE_ITEMS
            rows = _array(evidence[key], label=f"{label}.{key}", maximum=maximum)
            expected_keys = nested_keys.get(key)
            if expected_keys is not None:
                for row_index, row in enumerate(rows):
                    _exact_dict(
                        row,
                        expected_keys,
                        label=f"{label}.{key}[{row_index}]",
                    )
    return root


def _receipt_document(
    snapshot: RepoSnapshot,
    entry: TreeEntry,
) -> dict[str, Any]:
    if entry.size is None or entry.size > MAX_RECEIPT_BYTES:
        _fail(
            "oversize-json",
            f"{entry.path}: {entry.size} bytes > {MAX_RECEIPT_BYTES}",
        )
    return _exact_dict(
        _strict_json(
            _blob(snapshot, entry),
            label=entry.path,
            max_bytes=MAX_RECEIPT_BYTES,
        ),
        _RECEIPT_KEYS,
        label=entry.path,
    )


def _strict_receipt_control(
    snapshot: RepoSnapshot,
    entry: TreeEntry,
) -> bool:
    try:
        receipt = _receipt_document(snapshot, entry)
        if not (
            receipt["schema_version"] == RECEIPT_SCHEMA
            and receipt["authority"] == "none"
            and receipt["default_effect"] == "no-state-change"
            and receipt["advisory_only"] is True
            and receipt["human_review_required"] is True
        ):
            return False
        mutants = _array(
            receipt["mutants"],
            label=f"{entry.path}.mutants",
            maximum=MAX_EVIDENCE_ITEMS,
        )
        for index, raw_mutant in enumerate(mutants):
            mutant = _exact_dict(
                raw_mutant,
                _MUTANT_KEYS,
                label=f"{entry.path}.mutants[{index}]",
            )
            _array(
                mutant["failed_nodes"],
                label=f"{entry.path}.mutants[{index}].failed_nodes",
                maximum=MAX_EVIDENCE_ITEMS,
            )
        return True
    except RuleOpsError:
        return False


def _validate_oid(value: Any, snapshot: RepoSnapshot, *, label: str) -> str:
    oid = _string(value, label=label, maximum=64)
    if _OID_RE[snapshot.object_format].fullmatch(oid) is None:
        _fail("bad-oid", f"{label}: {snapshot.object_format} OID でない")
    return oid


def _validate_blob_ref(
    value: Any,
    snapshot: RepoSnapshot,
    *,
    label: str,
    candidate_paths: frozenset[str],
    controls: Collection[str],
    ledger_path: str,
) -> tuple[str, TreeEntry]:
    item = _exact_dict(value, _BLOB_REF_KEYS, label=label)
    path = _repo_path(item["path"], label=f"{label}.path")
    if path == ledger_path:
        _fail("ledger-evidence-alias", f"{label}: ledger path を evidence に使用: {path}")
    if path in candidate_paths:
        _fail("candidate-cycle", f"{label}: candidate を evidence/control に使用: {path}")
    if path in controls:
        _fail("control-cycle", f"{label}: control artifact を evidence に使用: {path}")
    entry = _regular_blob(snapshot, path, label=label)
    pinned = _validate_oid(item["blob"], snapshot, label=f"{label}.blob")
    if pinned != entry.oid:
        _fail("blob-drift", f"{label}: blob drift: {path}")
    return path, entry


def _node_symbol_exists(
    snapshot: RepoSnapshot,
    entry: TreeEntry,
    symbol: str,
    *,
    label: str,
) -> None:
    parts = symbol.split("::")
    if any(not part.isidentifier() for part in parts):
        _fail("nodeid-shape", f"{label}: static Python symbol が必要")
    try:
        module = ast.parse(_blob_text(snapshot, entry, label=label), filename=entry.path)
    except SyntaxError as exc:
        raise RuleOpsError("node-ast", f"{label}: Python AST parse 失敗") from exc
    body: Sequence[ast.stmt] = module.body
    for depth, part in enumerate(parts):
        found = next(
            (
                node
                for node in body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == part
            ),
            None,
        )
        if found is None:
            _fail("node-missing", f"{label}: advisory replacement symbol がない: {symbol}")
        if depth + 1 < len(parts):
            if not isinstance(found, ast.ClassDef):
                _fail("node-missing", f"{label}: nested symbol が class member でない")
            body = found.body


def _validate_reviewed_observed(
    value: Any,
    snapshot: RepoSnapshot,
    *,
    label: str,
) -> list[dict[str, Any]]:
    rows = _array(value, label=label, maximum=MAX_EVIDENCE_ITEMS)
    result: list[dict[str, Any]] = []
    identities: set[tuple[str, str, str, int]] = set()
    for index, row in enumerate(rows):
        item = _exact_dict(row, _OBSERVED_HIT_KEYS, label=f"{label}[{index}]")
        query = _review_text(
            item["query"], label=f"{label}[{index}].query", maximum=MAX_PATH_BYTES,
        )
        path = _repo_path(item["path"], label=f"{label}[{index}].path")
        blob = _validate_oid(
            item["blob"], snapshot, label=f"{label}[{index}].blob",
        )
        line = _integer(item["line"], label=f"{label}[{index}].line", minimum=1)
        review = _string(
            item["review"],
            label=f"{label}[{index}].review",
            maximum=32,
            enum=_REVIEWS,
        )
        rationale = _review_text(
            item["rationale"],
            label=f"{label}[{index}].rationale",
            maximum=MAX_REVIEW_RATIONALE_CHARS,
        )
        identity = (query, path, blob, line)
        if identity in identities:
            _fail("duplicate-hit", f"{label}: hit 重複: {identity}")
        identities.add(identity)
        result.append({
            "blob": blob,
            "line": line,
            "path": path,
            "query": query,
            "rationale": rationale,
            "review": review,
        })
    return result


def _validate_reviewed_pickaxe(
    value: Any,
    snapshot: RepoSnapshot,
    *,
    label: str,
) -> list[dict[str, str]]:
    rows = _array(value, label=label, maximum=MAX_EVIDENCE_ITEMS)
    result: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        item = _exact_dict(row, _PICKAXE_EVENT_KEYS, label=f"{label}[{index}]")
        query = _review_text(
            item["query"], label=f"{label}[{index}].query", maximum=MAX_PATH_BYTES,
        )
        commit = _validate_oid(
            item["commit"], snapshot, label=f"{label}[{index}].commit",
        )
        review = _string(
            item["review"],
            label=f"{label}[{index}].review",
            maximum=32,
            enum=_REVIEWS,
        )
        rationale = _review_text(
            item["rationale"],
            label=f"{label}[{index}].rationale",
            maximum=MAX_REVIEW_RATIONALE_CHARS,
        )
        identity = (query, commit)
        if identity in identities:
            _fail("duplicate-hit", f"{label}: event 重複: {identity}")
        identities.add(identity)
        result.append({
            "commit": commit,
            "query": query,
            "rationale": rationale,
            "review": review,
        })
    return result


def _compare_signals(
    computed_observed: Sequence[Mapping[str, Any]],
    reviewed_observed: Sequence[Mapping[str, Any]],
    computed_pickaxe: Sequence[Mapping[str, str]],
    reviewed_pickaxe: Sequence[Mapping[str, str]],
    *,
    label: str,
) -> None:
    observed_expected = {
        (x["query"], x["path"], x["blob"], x["line"])
        for x in computed_observed
    }
    observed_actual = {
        (x["query"], x["path"], x["blob"], x["line"])
        for x in reviewed_observed
    }
    if observed_expected != observed_actual:
        _fail(
            "unresolved-observed-hit",
            f"{label}: observed hit 未裁定/余剰 "
            f"missing={len(observed_expected - observed_actual)} "
            f"extra={len(observed_actual - observed_expected)}",
        )
    pickaxe_expected = {
        (x["query"], x["commit"]) for x in computed_pickaxe
    }
    pickaxe_actual = {
        (x["query"], x["commit"]) for x in reviewed_pickaxe
    }
    if pickaxe_expected != pickaxe_actual:
        _fail(
            "unresolved-pickaxe-event",
            f"{label}: pickaxe event 未裁定/余剰 "
            f"missing={len(pickaxe_expected - pickaxe_actual)} "
            f"extra={len(pickaxe_actual - pickaxe_expected)}",
        )


def _receipt_head_tree_blob(
    snapshot: RepoSnapshot,
    receipt_head: str,
    candidate_path: str,
) -> str:
    kind = _git_read(
        snapshot.repo,
        "cat-file",
        "-t",
        receipt_head,
        allowed_rc=frozenset({0, 128}),
    )
    if kind != b"commit\n":
        _fail("receipt-head-missing", f"receipt head commit が存在しない: {receipt_head}")
    raw_merge_base = _git_read(
        snapshot.repo,
        "merge-base",
        receipt_head,
        snapshot.head,
        allowed_rc=frozenset({0, 1}),
    )
    try:
        merge_base = raw_merge_base.decode("ascii", "strict").strip()
    except UnicodeDecodeError as exc:
        raise RuleOpsError("bad-history", "merge-base が非 ASCII") from exc
    if merge_base != receipt_head:
        _fail(
            "receipt-head-non-ancestor",
            f"receipt head が current snapshot の祖先でない: {receipt_head}",
        )
    raw_entry = _git_read(
        snapshot.repo,
        "ls-tree",
        "-l",
        "-z",
        receipt_head,
        "--",
        f":(top,literal){candidate_path}",
    )
    chunks = [chunk for chunk in raw_entry.split(b"\0") if chunk]
    if len(chunks) != 1:
        _fail(
            "receipt-candidate-blob",
            f"receipt head に candidate blob がない: {candidate_path}",
        )
    try:
        meta_raw, path_raw = chunks[0].split(b"\t", 1)
        mode, kind_name, oid, size_text = meta_raw.decode("ascii", "strict").split()
        rendered_path = path_raw.decode("utf-8", "strict")
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuleOpsError("bad-ls-tree", "receipt head ls-tree 出力不正") from exc
    if (
        rendered_path != candidate_path
        or mode not in _REGULAR_MODES
        or kind_name != "blob"
        or not size_text.isdigit()
        or _OID_RE[snapshot.object_format].fullmatch(oid) is None
    ):
        _fail(
            "receipt-candidate-blob",
            f"receipt head candidate entry 不正: {candidate_path}",
        )
    return oid


def _receipt_epoch_changed_paths(
    snapshot: RepoSnapshot,
    receipt_head: str,
) -> frozenset[str]:
    raw_commits = _git_read(
        snapshot.repo,
        "log",
        "--format=%H",
        "-z",
        f"{receipt_head}..{snapshot.head}",
        "--",
    )
    commits: list[str] = []
    for chunk in raw_commits.split(b"\0"):
        if not chunk:
            continue
        try:
            commit = chunk.decode("ascii", "strict")
        except UnicodeDecodeError as exc:
            raise RuleOpsError("bad-history", "receipt epoch commit が非 ASCII") from exc
        if _OID_RE[snapshot.object_format].fullmatch(commit) is None:
            _fail("bad-history", f"receipt epoch commit OID 不正: {commit!r}")
        commits.append(commit)
    if not commits:
        return frozenset()
    raw_paths = _git_read(
        snapshot.repo,
        "diff-tree",
        "--stdin",
        "-m",
        "--root",
        "--no-commit-id",
        "--name-only",
        "--no-renames",
        "-r",
        "-z",
        "--",
        input_bytes=("\n".join(commits) + "\n").encode("ascii"),
    )
    paths: set[str] = set()
    for chunk in raw_paths.split(b"\0"):
        if not chunk:
            continue
        try:
            path = chunk.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise RuleOpsError("bad-history", "receipt epoch path が非 UTF-8") from exc
        paths.add(path)
    return frozenset(paths)


def _validate_receipt(
    snapshot: RepoSnapshot,
    entry: TreeEntry,
    *,
    candidate_path: str,
    candidate_blob: str,
    replacement_guards: frozenset[str],
    replacement_nodes: frozenset[str],
    allowed_epoch_paths: frozenset[str],
) -> None:
    receipt = _receipt_document(snapshot, entry)
    if receipt["schema_version"] != RECEIPT_SCHEMA:
        _fail("receipt-schema", f"{entry.path}: schema_version 不正")
    if receipt["authority"] != "none" or receipt["default_effect"] != "no-state-change":
        _fail("receipt-authority", f"{entry.path}: non-authoritative marker 不正")
    if receipt["candidate_path"] != candidate_path:
        _fail("receipt-target", f"{entry.path}: candidate_path 不一致")
    if receipt["candidate_blob"] != candidate_blob:
        _fail("receipt-target", f"{entry.path}: candidate_blob 不一致")
    receipt_head = _validate_oid(
        receipt["head"], snapshot, label=f"{entry.path}.head",
    )
    head_candidate_blob = _receipt_head_tree_blob(
        snapshot,
        receipt_head,
        candidate_path,
    )
    if head_candidate_blob != candidate_blob:
        _fail(
            "receipt-candidate-blob",
            f"{entry.path}: receipt head candidate blob 不一致",
        )
    changed_paths = _receipt_epoch_changed_paths(snapshot, receipt_head)
    unrelated = sorted(changed_paths - allowed_epoch_paths)
    if unrelated:
        _fail(
            "receipt-epoch-path",
            f"{entry.path}: receipt epoch に許可外 path 変更: {unrelated}",
        )
    for key in ("candidate_excluded", "advisory_only", "human_review_required"):
        if not isinstance(receipt[key], bool):
            _fail("receipt-schema", f"{entry.path}.{key}: bool が必要")
    if not receipt["advisory_only"] or not receipt["human_review_required"]:
        _fail("receipt-overclaim", f"{entry.path}: advisory/human-review marker が必要")
    if not receipt["candidate_excluded"]:
        _fail("receipt-target", f"{entry.path}: candidate_excluded=true が必要")
    if receipt["review_state"] != "reviewed":
        _fail("receipt-review", f"{entry.path}: review_state=reviewed が必要")
    for key in ("baseline_rc", "restored_rc"):
        if _integer(receipt[key], label=f"{entry.path}.{key}") != 0:
            _fail("receipt-guard-result", f"{entry.path}.{key}: rc=0 が必要")
    mutants = _array(
        receipt["mutants"],
        label=f"{entry.path}.mutants",
        minimum=1,
        maximum=MAX_EVIDENCE_ITEMS,
    )
    receipt_guards: set[str] = set()
    receipt_nodes: set[str] = set()
    for index, raw_mutant in enumerate(mutants):
        mutant = _exact_dict(
            raw_mutant, _MUTANT_KEYS, label=f"{entry.path}.mutants[{index}]",
        )
        guard_path = _repo_path(
            mutant["guard_path"], label=f"{entry.path}.mutants[{index}].guard_path",
        )
        if guard_path in receipt_guards:
            _fail("duplicate-evidence", f"{entry.path}: guard_path 重複: {guard_path}")
        receipt_guards.add(guard_path)
        status = _string(
            mutant["status"],
            label=f"{entry.path}.mutants[{index}].status",
            maximum=16,
            enum=_MUTANT_STATUSES,
        )
        if status != "KILLED":
            _fail(
                "receipt-guard-result",
                f"{entry.path}.mutants[{index}]: KILLED が必要",
            )
        nodes = _array(
            mutant["failed_nodes"],
            label=f"{entry.path}.mutants[{index}].failed_nodes",
            minimum=1,
            maximum=MAX_EVIDENCE_ITEMS,
        )
        for node_index, node in enumerate(nodes):
            nodeid = _string(
                node,
                label=f"{entry.path}.mutants[{index}].failed_nodes[{node_index}]",
                maximum=MAX_PATH_BYTES,
            )
            if nodeid in receipt_nodes:
                _fail("duplicate-evidence", f"{entry.path}: failed node 重複: {nodeid}")
            receipt_nodes.add(nodeid)
    if receipt_guards != set(replacement_guards):
        _fail(
            "receipt-guard-mismatch",
            f"{entry.path}: receipt guards と replacement_guards が不一致",
        )
    if receipt_nodes != set(replacement_nodes):
        _fail(
            "receipt-node-mismatch",
            f"{entry.path}: failed_nodes と replacement_nodes が不一致",
        )


def _validated_semantic_queries(
    evidence: Mapping[str, Any],
    *,
    candidate_path: str,
) -> list[str]:
    queries = _array(
        evidence["semantic_queries"],
        label=f"{candidate_path}.semantic_queries",
        minimum=1,
        maximum=MAX_QUERY_COUNT,
    )
    normalized_queries: list[str] = []
    for index, raw_query in enumerate(queries):
        query = _review_text(
            raw_query,
            label=f"{candidate_path}.semantic_queries[{index}]",
            minimum=2,
            maximum=MAX_QUERY_CHARS,
        )
        if query in {candidate_path, PurePosixPath(candidate_path).name}:
            _fail(
                "semantic-query",
                f"{candidate_path}: path/basename は semantic query でない",
            )
        if query in normalized_queries:
            _fail("duplicate-query", f"{candidate_path}: semantic query 重複")
        normalized_queries.append(query)
    return normalized_queries


def _validate_test_evidence(
    candidate: Mapping[str, Any],
    snapshot: RepoSnapshot,
    *,
    candidate_paths: frozenset[str],
    ledger_path: str,
    ledger_controls: Mapping[str, str],
    ledger_receipt_paths: frozenset[str],
) -> None:
    path = candidate["path"]
    target_blob = candidate["target_blob"]
    evidence = _exact_dict(
        candidate["test_evidence"], _TEST_EVIDENCE_KEYS, label=f"{path}.test_evidence",
    )
    receipts_raw = _array(
        evidence["mutation_receipts"],
        label=f"{path}.mutation_receipts",
        minimum=1,
        maximum=MAX_EVIDENCE_ITEMS,
    )
    receipt_paths: set[str] = set()
    receipt_entries: dict[str, TreeEntry] = {}
    for index, raw_ref in enumerate(receipts_raw):
        item = _exact_dict(raw_ref, _BLOB_REF_KEYS, label=f"{path}.receipt[{index}]")
        receipt_path = _repo_path(item["path"], label=f"{path}.receipt[{index}].path")
        if receipt_path == ledger_path:
            _fail(
                "ledger-evidence-alias",
                f"{path}: ledger path を receipt に使用: {receipt_path}",
            )
        if receipt_path in candidate_paths:
            _fail("candidate-cycle", f"{path}: candidate を receipt に使用: {receipt_path}")
        if not _INSIGHT_PATH_RE.fullmatch(receipt_path):
            _fail("receipt-scope", f"{path}: receipt は output/insights/** が必要")
        if receipt_path in receipt_paths:
            _fail("duplicate-evidence", f"{path}: receipt 重複: {receipt_path}")
        receipt_entry = _regular_blob(snapshot, receipt_path, label=f"{path}.receipt")
        pinned = _validate_oid(
            item["blob"], snapshot, label=f"{path}.receipt[{index}].blob",
        )
        if pinned != receipt_entry.oid:
            _fail("blob-drift", f"{path}: receipt blob drift: {receipt_path}")
        receipt_paths.add(receipt_path)
        receipt_entries[receipt_path] = receipt_entry
    controls = dict(ledger_controls)
    for receipt_path, receipt_entry in receipt_entries.items():
        if _strict_receipt_control(snapshot, receipt_entry):
            controls[receipt_path] = receipt_entry.oid
    guards = _array(
        evidence["replacement_guards"],
        label=f"{path}.replacement_guards",
        minimum=1,
        maximum=MAX_EVIDENCE_ITEMS,
    )
    guard_paths: set[str] = set()
    for index, guard in enumerate(guards):
        guard_path, _ = _validate_blob_ref(
            guard,
            snapshot,
            label=f"{path}.replacement_guards[{index}]",
            candidate_paths=candidate_paths,
            controls=controls,
            ledger_path=ledger_path,
        )
        if guard_path in guard_paths:
            _fail("duplicate-evidence", f"{path}: replacement guard 重複: {guard_path}")
        guard_paths.add(guard_path)
    nodes = _array(
        evidence["replacement_nodes"],
        label=f"{path}.replacement_nodes",
        minimum=1,
        maximum=MAX_EVIDENCE_ITEMS,
    )
    nodeids: set[str] = set()
    for index, raw_node in enumerate(nodes):
        node = _exact_dict(raw_node, _NODE_REF_KEYS, label=f"{path}.replacement_nodes[{index}]")
        nodeid = _string(
            node["nodeid"],
            label=f"{path}.replacement_nodes[{index}].nodeid",
            maximum=MAX_PATH_BYTES,
        )
        module, separator, symbol = nodeid.partition("::")
        module = _repo_path(module, label=f"{path}.replacement_nodes[{index}].module")
        if not separator or not symbol:
            _fail("nodeid-shape", f"{path}: file::symbol nodeid が必要")
        if module == ledger_path:
            _fail(
                "ledger-evidence-alias",
                f"{path}: ledger path を replacement node に使用: {module}",
            )
        if module in candidate_paths:
            _fail("candidate-cycle", f"{path}: candidate を replacement node に使用: {module}")
        if module in controls:
            _fail("control-cycle", f"{path}: control を replacement node に使用: {module}")
        if not _TEST_PATH_RE.fullmatch(module):
            _fail("nodeid-scope", f"{path}: replacement node module は direct test が必要")
        module_entry = _regular_blob(snapshot, module, label=f"{path}.replacement_nodes[{index}]")
        pinned = _validate_oid(
            node["blob"], snapshot, label=f"{path}.replacement_nodes[{index}].blob",
        )
        if pinned != module_entry.oid:
            _fail("blob-drift", f"{path}: replacement node blob drift: {module}")
        _node_symbol_exists(
            snapshot,
            module_entry,
            symbol,
            label=f"{path}.replacement_nodes[{index}]",
        )
        if nodeid in nodeids:
            _fail("duplicate-evidence", f"{path}: replacement node 重複: {nodeid}")
        nodeids.add(nodeid)
    normalized_queries = _validated_semantic_queries(
        evidence,
        candidate_path=path,
    )
    reviewed_observed = _validate_reviewed_observed(
        evidence["observed_hits"], snapshot, label=f"{path}.observed_hits",
    )
    reviewed_pickaxe = _validate_reviewed_pickaxe(
        evidence["pickaxe_events"], snapshot, label=f"{path}.pickaxe_events",
    )
    for receipt_path in sorted(receipt_paths):
        _validate_receipt(
            snapshot,
            receipt_entries[receipt_path],
            candidate_path=path,
            candidate_blob=target_blob,
            replacement_guards=frozenset(guard_paths),
            replacement_nodes=frozenset(nodeids),
            allowed_epoch_paths=frozenset({ledger_path, *ledger_receipt_paths}),
        )
    tokens = _signal_tokens(snapshot, path, normalized_queries)
    observed, _ = _observed_hits(
        snapshot, tokens, controls, link_target=path,
    )
    pickaxe, _ = _pickaxe(snapshot, tokens, controls)
    _check_signal_limit(observed, pickaxe, label=path)
    _compare_signals(
        observed,
        reviewed_observed,
        pickaxe,
        reviewed_pickaxe,
        label=path,
    )


def _validate_insight_evidence(
    candidate: Mapping[str, Any],
    snapshot: RepoSnapshot,
    *,
    candidate_paths: frozenset[str],
    ledger_path: str,
    ledger_controls: Mapping[str, str],
) -> None:
    path = candidate["path"]
    evidence = _exact_dict(
        candidate["insight_evidence"],
        _INSIGHT_EVIDENCE_KEYS,
        label=f"{path}.insight_evidence",
    )
    if evidence["artifact_class"] != "derived-report":
        _fail("artifact-class", f"{path}: artifact_class は derived-report のみ")
    if PurePosixPath(path).suffix.lower() != ".md":
        _fail("legacy-insight", f"{path}: v1 candidate は typed Markdown のみ")
    target_entry = _regular_blob(snapshot, path, label=path)
    target_raw = _blob(snapshot, target_entry)
    try:
        target_text = target_raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise RuleOpsError("non-utf8", f"{path}: blob が非 UTF-8") from exc
    if not _typed_insight_marker(target_raw):
        _fail("authority-marker", f"{path}: byte-leading typed marker が必要")
    controls = dict(ledger_controls)
    sources = _array(
        evidence["source_artifacts"],
        label=f"{path}.source_artifacts",
        minimum=1,
        maximum=MAX_EVIDENCE_ITEMS,
    )
    source_paths: set[str] = set()
    for index, source in enumerate(sources):
        source_path, _ = _validate_blob_ref(
            source,
            snapshot,
            label=f"{path}.source_artifacts[{index}]",
            candidate_paths=candidate_paths,
            controls=controls,
            ledger_path=ledger_path,
        )
        if source_path == path:
            _fail("candidate-cycle", f"{path}: target 自身を source に使用")
        if source_path in source_paths:
            _fail("duplicate-evidence", f"{path}: source 重複: {source_path}")
        if source_path not in target_text:
            _fail("source-unquoted", f"{path}: source path が target に引用されていない")
        source_paths.add(source_path)
    reviewed_observed = _validate_reviewed_observed(
        evidence["observed_hits"], snapshot, label=f"{path}.observed_hits",
    )
    reviewed_pickaxe = _validate_reviewed_pickaxe(
        evidence["pickaxe_events"], snapshot, label=f"{path}.pickaxe_events",
    )
    tokens = _signal_tokens(snapshot, path, ())
    observed, _ = _observed_hits(
        snapshot, tokens, controls, link_target=path,
    )
    pickaxe, _ = _pickaxe(snapshot, tokens, controls)
    _check_signal_limit(observed, pickaxe, label=path)
    _compare_signals(
        observed,
        reviewed_observed,
        pickaxe,
        reviewed_pickaxe,
        label=path,
    )


def validate_candidate_ledger(
    repo: Path | str,
    ledger: Path | str = DEFAULT_LEDGER,
) -> dict[str, Any]:
    snapshot = _capture_snapshot(repo)
    ledger_file, ledger_rel = _ledger_file(snapshot.repo, ledger)
    raw = _read_regular_file_bounded(
        ledger_file,
        label=ledger_rel,
        max_bytes=MAX_LEDGER_BYTES,
    )
    root = _exact_dict(
        _strict_json(raw, label=ledger_rel, max_bytes=MAX_LEDGER_BYTES),
        _ROOT_KEYS,
        label="ledger",
    )
    if root["schema_version"] != LEDGER_SCHEMA:
        _fail("ledger-schema", "schema_version 不正")
    if root["authority"] != "none" or root["default_effect"] != "no-state-change":
        _fail("ledger-authority", "ledger は authority none / no-state-change が必要")
    candidates_raw = _array(
        root["candidates"],
        label="ledger.candidates",
        maximum=MAX_CANDIDATES,
        overflow_reason="candidate-limit",
    )
    paths: list[str] = []
    kinds: list[str] = []
    for index, raw_candidate in enumerate(candidates_raw):
        if not isinstance(raw_candidate, dict):
            _fail("schema-type", f"candidate[{index}]: object が必要")
        kind = raw_candidate.get("kind")
        keys = _CANDIDATE_KEYS if kind == "test" else _INSIGHT_CANDIDATE_KEYS
        candidate = _exact_dict(raw_candidate, keys, label=f"candidate[{index}]")
        path = _repo_path(candidate["path"], label=f"candidate[{index}].path")
        derived = _scoped_kind(path)
        if kind not in {"test", "insight"} or derived != kind:
            _fail("kind-drift", f"candidate[{index}]: kind/path 不一致")
        if path in paths:
            _fail("duplicate-candidate", f"candidate path 重複: {path}")
        entry = _regular_blob(snapshot, path, label=f"candidate[{index}]")
        pinned = _validate_oid(
            candidate["target_blob"], snapshot, label=f"candidate[{index}].target_blob",
        )
        if pinned != entry.oid:
            _fail("blob-drift", f"candidate[{index}]: target blob drift")
        _review_text(
            candidate["rationale"],
            label=f"candidate[{index}].rationale",
            maximum=MAX_RATIONALE_CHARS,
        )
        paths.append(path)
        kinds.append(kind)
    candidate_paths = frozenset(paths)
    if ledger_rel in candidate_paths:
        _fail(
            "ledger-candidate-alias",
            f"ledger path は candidate path と alias できない: {ledger_rel}",
        )
    ledger_receipt_paths: set[str] = set()
    signal_tokens: set[str] = set()
    for candidate, kind in zip(candidates_raw, kinds):
        path = candidate["path"]
        if kind == "test":
            evidence = _exact_dict(
                candidate["test_evidence"],
                _TEST_EVIDENCE_KEYS,
                label=f"{path}.test_evidence",
            )
            receipts = _array(
                evidence["mutation_receipts"],
                label=f"{path}.mutation_receipts",
                minimum=1,
                maximum=MAX_EVIDENCE_ITEMS,
            )
            for index, raw_ref in enumerate(receipts):
                item = _exact_dict(
                    raw_ref,
                    _BLOB_REF_KEYS,
                    label=f"{path}.receipt[{index}]",
                )
                receipt_path = _repo_path(
                    item["path"],
                    label=f"{path}.receipt[{index}].path",
                )
                if receipt_path == ledger_rel:
                    _fail(
                        "ledger-evidence-alias",
                        f"{path}: ledger path を receipt に使用: {receipt_path}",
                    )
                ledger_receipt_paths.add(receipt_path)
            queries = _validated_semantic_queries(
                evidence,
                candidate_path=path,
            )
        else:
            _exact_dict(
                candidate["insight_evidence"],
                _INSIGHT_EVIDENCE_KEYS,
                label=f"{path}.insight_evidence",
            )
            queries = []
        signal_tokens.update(_signal_tokens(snapshot, path, queries))
    if len(signal_tokens) > MAX_SIGNAL_TOKENS:
        _fail(
            "signal-token-limit",
            f"ledger signal token union {len(signal_tokens)} > {MAX_SIGNAL_TOKENS}",
        )
    ledger_controls: dict[str, str] = {}
    ledger_entry = snapshot.entries.get(ledger_rel)
    if (
        ledger_entry is not None
        and ledger_entry.kind == "blob"
        and ledger_entry.mode in _REGULAR_MODES
        and ledger_entry.size is not None
    ):
        if ledger_entry.size > MAX_LEDGER_BYTES:
            _fail(
                "oversize-json",
                f"{ledger_rel}: {ledger_entry.size} bytes > {MAX_LEDGER_BYTES}",
            )
        head_ledger = _blob(snapshot, ledger_entry)
        if raw == head_ledger:
            _strict_ledger_control(head_ledger, label=ledger_rel)
            ledger_controls[ledger_rel] = ledger_entry.oid
    for candidate, kind in zip(candidates_raw, kinds):
        if kind == "test":
            _validate_test_evidence(
                candidate,
                snapshot,
                candidate_paths=candidate_paths,
                ledger_path=ledger_rel,
                ledger_controls=ledger_controls,
                ledger_receipt_paths=frozenset(ledger_receipt_paths),
            )
        else:
            _validate_insight_evidence(
                candidate,
                snapshot,
                candidate_paths=candidate_paths,
                ledger_path=ledger_rel,
                ledger_controls=ledger_controls,
            )
    output = {
        "candidate_count": len(candidates_raw),
        "human_approved": False,
        "structurally_valid": True,
    }
    _assert_snapshot_current(snapshot)
    return output


class _RuleOpsArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise RuleOpsError("cli-args", message)


def _parser() -> argparse.ArgumentParser:
    parser = _RuleOpsArgumentParser(
        prog="ruleops.py",
        description="Read-only RuleOps inventory and candidate package validator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--kind", choices=("all", "test", "insight"), default="all")
    inventory.add_argument("--repo", default=".")

    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("path")
    inspect.add_argument("--query", action="append", default=[])
    inspect.add_argument("--draft", action="store_true")
    inspect.add_argument("--repo", default=".")

    check = subparsers.add_parser("check")
    check.add_argument("--ledger", default=DEFAULT_LEDGER)
    check.add_argument("--repo", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "inventory":
            output = build_inventory(args.repo, kind=args.kind)
        elif args.command == "inspect":
            output = inspect_target(
                args.repo,
                args.path,
                queries=args.query,
                draft=args.draft,
            )
        elif args.command == "check":
            output = validate_candidate_ledger(args.repo, args.ledger)
        else:  # argparse's required closed subparser makes this unreachable.
            _fail("command", f"unknown command: {args.command}")
        sys.stdout.buffer.write(_canonical_json_bytes(output))
        return 0
    except RuleOpsError as exc:
        print(f"ruleops: {exc.reason}: {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ruleops: internal-boundary: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # fail closed without exposing a traceback at the CLI boundary
        print(f"ruleops: internal-error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
