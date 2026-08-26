# -*- coding: utf-8 -*-
"""Read-only comparison against committed enforcement-closure ratifications.

The ledger is deliberately outside the closure whose digest it records.  This
module only reads and verifies it; it provides no append, update, or CLI path.
The resulting claim is limited to comparison with a set that AI implementers
cannot write through the repository hooks, not proof of who added a row.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping

from .campaign_lock import CONTRACT_LOADER_RELATIVE_PATHS


RATIFICATION_LEDGER_RELATIVE_PATH = (
    "hooks/enforcement-source-closure-ratifications.v1.jsonl"
)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROW_KEYS = frozenset({"schema_version", "closure_digest_sha256"})
_GIT_TIMEOUT_SECONDS = 10
_GIT_EXECUTABLE = Path("/usr/bin/git")
_GIT_HARDEN = (
    "--no-pager",
    "-c",
    "core.useReplaceRefs=false",
    "-c",
    "core.commitGraph=false",
    "-c",
    "core.fsmonitor=false",
)
_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)
_FORBIDDEN_AMBIENT_GIT_ENV = frozenset({
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
})


class EnforcementSourceRatificationError(ValueError):
    """The read-only ledger or requested exact closure is not admissible."""


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
        raise EnforcementSourceRatificationError(
            "ratification value is not canonical JSON"
        ) from exc


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise EnforcementSourceRatificationError(
                f"ratification row has duplicate key: {key!r}"
            )
        value[key] = item
    return value


def closure_digest_sha256(blob_sha256s: Mapping[str, str]) -> str:
    """Hash the exact path-to-blob-SHA-256 map, excluding any Git commit ID."""
    if (type(blob_sha256s) is not dict
            or set(blob_sha256s) != set(CONTRACT_LOADER_RELATIVE_PATHS)):
        raise EnforcementSourceRatificationError(
            "closure digest requires the exact enforcement path map"
        )
    canonical_map: dict[str, str] = {}
    for relative in CONTRACT_LOADER_RELATIVE_PATHS:
        digest = blob_sha256s[relative]
        if type(digest) is not str or _HEX64_RE.fullmatch(digest) is None:
            raise EnforcementSourceRatificationError(
                f"closure blob digest is invalid: {relative}"
            )
        canonical_map[relative] = digest
    return hashlib.sha256(_canonical_json_bytes(canonical_map)).hexdigest()


def _load_rows(raw: bytes) -> tuple[str, ...]:
    if not raw:
        return ()
    if not raw.endswith(b"\n"):
        raise EnforcementSourceRatificationError(
            "ratification ledger is not newline terminated"
        )
    digests: list[str] = []
    for line_number, line in enumerate(raw.split(b"\n")[:-1], start=1):
        if not line:
            raise EnforcementSourceRatificationError(
                f"ratification ledger has an empty row: {line_number}"
            )
        try:
            text = line.decode("ascii")
            value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
        except UnicodeDecodeError as exc:
            raise EnforcementSourceRatificationError(
                f"ratification row is not ASCII: {line_number}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise EnforcementSourceRatificationError(
                f"ratification row is not JSON: {line_number}"
            ) from exc
        if type(value) is not dict or set(value) != _ROW_KEYS:
            raise EnforcementSourceRatificationError(
                f"ratification row has a non-exact schema: {line_number}"
            )
        if (type(value["schema_version"]) is not int
                or value["schema_version"] != 1):
            raise EnforcementSourceRatificationError(
                f"ratification row schema version is invalid: {line_number}"
            )
        digest = value["closure_digest_sha256"]
        if type(digest) is not str or _HEX64_RE.fullmatch(digest) is None:
            raise EnforcementSourceRatificationError(
                f"ratification row digest is invalid: {line_number}"
            )
        if line != _canonical_json_bytes(value):
            raise EnforcementSourceRatificationError(
                f"ratification row is not canonical JSON: {line_number}"
            )
        if digest in digests:
            raise EnforcementSourceRatificationError(
                f"ratification ledger repeats a closure digest: {line_number}"
            )
        digests.append(digest)
    return tuple(digests)


def _git_env() -> dict[str, str]:
    contaminated = sorted(
        key for key in _FORBIDDEN_AMBIENT_GIT_ENV if key in os.environ
    )
    if contaminated:
        raise EnforcementSourceRatificationError(
            "ratification git environment has repository/object overrides: "
            f"{contaminated!r}"
        )
    result = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    result.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return result


def _git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    if not _GIT_EXECUTABLE.is_absolute():
        raise EnforcementSourceRatificationError(
            "ratification git executable is not an absolute path"
        )
    try:
        present = _GIT_EXECUTABLE.is_file()
    except OSError as exc:
        raise EnforcementSourceRatificationError(
            "ratification git executable cannot be resolved"
        ) from exc
    if not present:
        raise EnforcementSourceRatificationError(
            "ratification git executable is unavailable"
        )
    executable = os.fspath(_GIT_EXECUTABLE)
    try:
        return subprocess.run(
            [
                executable,
                *_GIT_HARDEN,
                "--no-replace-objects",
                "-C", str(root),
                *args,
            ],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=_git_env(),
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise EnforcementSourceRatificationError(
            "ratification git command timed out"
        ) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise EnforcementSourceRatificationError(
            "ratification git command could not run"
        ) from exc


def _require_git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> bytes:
    result = _git(root, *args, input_bytes=input_bytes)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise EnforcementSourceRatificationError(
            "ratification git command failed: "
            f"args={args!r} rc={result.returncode} stderr={stderr!r}"
        )
    return result.stdout


def _validated_root() -> Path:
    if not isinstance(_REPO_ROOT, Path):
        raise EnforcementSourceRatificationError(
            "ratification repository root must be pathlib.Path"
        )
    try:
        root = _REPO_ROOT.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise EnforcementSourceRatificationError(
            "ratification repository root cannot be resolved"
        ) from exc
    if not root.is_dir():
        raise EnforcementSourceRatificationError(
            "ratification repository root is not a directory"
        )
    raw = _require_git(root, "rev-parse", "--show-toplevel")
    try:
        toplevel = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationError(
            "ratification Git top-level is not UTF-8"
        ) from exc
    if not toplevel.endswith("\n") or "\n" in toplevel[:-1]:
        raise EnforcementSourceRatificationError(
            "ratification Git top-level output is not exact"
        )
    if toplevel[:-1] != str(root):
        raise EnforcementSourceRatificationError(
            "ratification Git top-level differs from the expected checkout"
        )
    return root


def _assert_full_history_repository(root: Path) -> None:
    shallow = _require_git(root, "rev-parse", "--is-shallow-repository")
    if shallow != b"false\n":
        raise EnforcementSourceRatificationError(
            "ratification history requires a non-shallow repository"
        )

    raw_grafts_path = _require_git(
        root, "rev-parse", "--git-path", "info/grafts",
    )
    try:
        grafts_text = raw_grafts_path.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationError(
            "ratification history cannot use Git grafts"
        ) from exc
    if (not grafts_text.endswith("\n")
            or "\n" in grafts_text[:-1]
            or not grafts_text[:-1]):
        raise EnforcementSourceRatificationError(
            "ratification history cannot use Git grafts"
        )

    grafts_path = Path(grafts_text[:-1])
    if not grafts_path.is_absolute():
        grafts_path = root / grafts_path
    try:
        if grafts_path.exists():
            grafts = grafts_path.read_bytes()
            if any(
                line and not line.startswith(b"#")
                for line in grafts.split(b"\n")
            ):
                raise EnforcementSourceRatificationError(
                    "ratification history cannot use Git grafts"
                )
    except EnforcementSourceRatificationError:
        raise
    except OSError as exc:
        raise EnforcementSourceRatificationError(
            "ratification history cannot use Git grafts"
        ) from exc


def _head_commit(root: Path) -> str:
    raw = _require_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationError(
            "ratification HEAD is not ASCII"
        ) from exc
    if (not text.endswith("\n")
            or "\n" in text[:-1]
            or _HEX40_RE.fullmatch(text[:-1]) is None):
        raise EnforcementSourceRatificationError(
            "ratification HEAD is not an exact commit ID"
        )
    return text[:-1]


def _reachable_commit_parents(
    root: Path, head: str,
) -> dict[str, tuple[str, ...]]:
    raw = _require_git(
        root,
        "log",
        "--format=%H %P",
        head,
    )
    if not raw.endswith(b"\n"):
        raise EnforcementSourceRatificationError(
            "ratification history returned an invalid commit ID"
        )
    parents_by_commit: dict[str, tuple[str, ...]] = {}
    for raw_line in raw.split(b"\n")[:-1]:
        try:
            line = raw_line.decode("ascii")
        except UnicodeDecodeError as exc:
            raise EnforcementSourceRatificationError(
                "ratification history returned a non-ASCII commit"
            ) from exc
        root_line = line.endswith(" ")
        if root_line:
            fields = [line[:-1]]
        else:
            fields = line.split(" ")
        if (not fields
                or any(_HEX40_RE.fullmatch(field) is None for field in fields)):
            raise EnforcementSourceRatificationError(
                "ratification history returned an invalid commit ID"
            )
        commit, *parents = fields
        if commit in parents_by_commit:
            raise EnforcementSourceRatificationError(
                "ratification history returned an invalid commit ID"
            )
        parents_by_commit[commit] = tuple(parents)
    if (not parents_by_commit
            or next(iter(parents_by_commit)) != head
            or any(
                parent not in parents_by_commit
                for parents in parents_by_commit.values()
                for parent in parents
            )):
        raise EnforcementSourceRatificationError(
            "ratification history returned an invalid commit ID"
        )
    return parents_by_commit


def _ledger_blob_oids(
    root: Path, commits: tuple[str, ...],
) -> dict[str, str | None]:
    ledger_name = RATIFICATION_LEDGER_RELATIVE_PATH.rsplit("/", 1)[1]
    ledger_directory = RATIFICATION_LEDGER_RELATIVE_PATH.rsplit("/", 1)[0]
    queries = tuple(
        query
        for commit in commits
        for query in (
            f"{commit}:{RATIFICATION_LEDGER_RELATIVE_PATH}",
            f"{commit}:{ledger_directory}",
        )
    )
    raw = _require_git(
        root,
        "cat-file",
        "--batch-check",
        input_bytes=b"".join(query.encode("ascii") + b"\n" for query in queries),
    )
    if not raw.endswith(b"\n"):
        raise EnforcementSourceRatificationError(
            "ratification ledger is not a blob in committed history"
        )
    lines = raw.split(b"\n")[:-1]
    if len(lines) != len(queries):
        raise EnforcementSourceRatificationError(
            "ratification ledger is not a blob in committed history"
        )

    def batch_object(
        query: str, raw_line: bytes,
    ) -> tuple[str, bytes] | None:
        missing = query.encode("ascii") + b" missing"
        if raw_line == missing:
            return None
        fields = raw_line.split(b" ")
        if len(fields) != 3:
            raise EnforcementSourceRatificationError(
                "ratification ledger is not a blob in committed history"
            )
        raw_oid, object_type, raw_size = fields
        try:
            oid = raw_oid.decode("ascii")
            size_text = raw_size.decode("ascii")
        except UnicodeDecodeError as exc:
            raise EnforcementSourceRatificationError(
                "ratification ledger is not a blob in committed history"
            ) from exc
        if (_HEX40_RE.fullmatch(oid) is None
                or not size_text.isdecimal()
                or (len(size_text) > 1 and size_text.startswith("0"))):
            raise EnforcementSourceRatificationError(
                "ratification ledger is not a blob in committed history"
            )
        return oid, object_type

    result: dict[str, str | None] = {}
    directory_trees: dict[str, str] = {}
    for index, commit in enumerate(commits):
        ledger_query = queries[index * 2]
        directory_query = queries[index * 2 + 1]
        ledger_object = batch_object(ledger_query, lines[index * 2])
        directory_object = batch_object(
            directory_query, lines[index * 2 + 1],
        )
        if ledger_object is None:
            result[commit] = None
            continue
        if (ledger_object[1] != b"blob"
                or directory_object is None
                or directory_object[1] != b"tree"):
            raise EnforcementSourceRatificationError(
                "ratification ledger is not a blob in committed history"
            )
        result[commit] = ledger_object[0]
        directory_trees[commit] = directory_object[0]

    tree_entry_cache: dict[str, tuple[tuple[bytes, str], ...]] = {}
    for commit, tree_oid in directory_trees.items():
        if tree_oid not in tree_entry_cache:
            raw_tree = _require_git(
                root, "cat-file", "tree", tree_oid,
            )
            offset = 0
            matching_entries: list[tuple[bytes, str]] = []
            while offset < len(raw_tree):
                mode_end = raw_tree.find(b" ", offset)
                name_end = raw_tree.find(b"\0", mode_end + 1)
                oid_end = name_end + 21
                if (mode_end <= offset
                        or name_end <= mode_end + 1
                        or oid_end > len(raw_tree)):
                    raise EnforcementSourceRatificationError(
                        "ratification ledger is not a blob in committed history"
                    )
                mode = raw_tree[offset:mode_end]
                name = raw_tree[mode_end + 1:name_end]
                raw_oid = raw_tree[name_end + 1:oid_end]
                if name == ledger_name.encode("ascii"):
                    matching_entries.append((mode, raw_oid.hex()))
                offset = oid_end
            tree_entry_cache[tree_oid] = tuple(matching_entries)
        matching_entry = tree_entry_cache[tree_oid]
        if (matching_entry != ((b"100644", result[commit]),)
                and matching_entry != ((b"100755", result[commit]),)):
            raise EnforcementSourceRatificationError(
                "ratification ledger is not a blob in committed history"
            )
    return result


def _rows_by_blob_oid(
    root: Path, entries: Mapping[str, str | None],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for oid in dict.fromkeys(
        oid for oid in entries.values() if oid is not None
    ):
        result[oid] = _load_rows(_require_git(root, "cat-file", "blob", oid))
    return result


def _is_subsequence(
    earlier: tuple[str, ...], later: tuple[str, ...],
) -> bool:
    later_iterator = iter(later)
    return all(
        any(earlier_digest == later_digest for later_digest in later_iterator)
        for earlier_digest in earlier
    )


def _committed_ratification_digests() -> frozenset[str]:
    root = _validated_root()
    _assert_full_history_repository(root)
    head = _head_commit(root)
    parents_by_commit = _reachable_commit_parents(root, head)
    commits = tuple(parents_by_commit)
    entries = _ledger_blob_oids(root, commits)
    rows_by_oid = _rows_by_blob_oid(root, entries)

    def rows_at(commit: str) -> tuple[str, ...]:
        oid = entries[commit]
        if oid is None:
            raise EnforcementSourceRatificationError(
                "ratification ledger was deleted in committed history"
            )
        return rows_by_oid[oid]

    introductions: list[str] = []
    for commit, parents in parents_by_commit.items():
        bearing_parents = tuple(
            parent for parent in parents if entries[parent] is not None
        )
        if entries[commit] is None:
            if bearing_parents:
                raise EnforcementSourceRatificationError(
                    "ratification ledger was deleted in committed history"
                )
            continue

        rows = rows_at(commit)
        if not bearing_parents:
            introductions.append(commit)
            if len(rows) > 1:
                raise EnforcementSourceRatificationError(
                    "ratification history introduced more than one row"
                )
            continue

        parent_union = frozenset(
            digest
            for parent in bearing_parents
            for digest in rows_at(parent)
        )
        row_set = frozenset(rows)
        if not parent_union.issubset(row_set):
            raise EnforcementSourceRatificationError(
                "ratification history is not a strict prefix extension"
            )
        if len(row_set - parent_union) > 1:
            raise EnforcementSourceRatificationError(
                "ratification history added more than one row"
            )
        if (len(parents) == 1
                and not _is_subsequence(rows_at(bearing_parents[0]), rows)):
            raise EnforcementSourceRatificationError(
                "ratification history is not a strict prefix extension"
            )

    if len(introductions) > 1:
        raise EnforcementSourceRatificationError(
            "ratification history has more than one ledger introduction"
        )
    head_oid = entries[head]
    if head_oid is None:
        return frozenset()
    return frozenset(rows_by_oid[head_oid])


def require_ratified_closure(blob_sha256s: Mapping[str, str]) -> str:
    """Return the closure digest only when committed ledger history contains it."""
    digest = closure_digest_sha256(blob_sha256s)
    if digest not in _committed_ratification_digests():
        raise EnforcementSourceRatificationError(
            "enforcement-source-closure-unratified: closure digest is absent "
            "from the read-only ledger"
        )
    return digest
