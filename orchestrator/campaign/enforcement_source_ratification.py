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
import shutil
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
_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
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
    for line_number, line in enumerate(raw.splitlines(), start=1):
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


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    executable = shutil.which("git")
    if executable is None:
        raise EnforcementSourceRatificationError(
            "ratification git executable is unavailable"
        )
    try:
        return subprocess.run(
            [executable, "-C", str(root), *args],
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


def _require_git(root: Path, *args: str) -> bytes:
    result = _git(root, *args)
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


def _committed_ratification_digests() -> frozenset[str]:
    root = _validated_root()
    head = _require_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        head_text = head.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise EnforcementSourceRatificationError(
            "ratification HEAD is not ASCII"
        ) from exc
    if _HEX40_RE.fullmatch(head_text) is None:
        raise EnforcementSourceRatificationError(
            "ratification HEAD is not an exact commit ID"
        )
    history = _require_git(
        root,
        "log",
        "--format=%H",
        "--reverse",
        "--full-history",
        head_text,
        "--",
        RATIFICATION_LEDGER_RELATIVE_PATH,
    )
    previous_raw = b""
    previous_rows: tuple[str, ...] = ()
    saw_version = False
    for raw_commit in history.splitlines():
        try:
            commit = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise EnforcementSourceRatificationError(
                "ratification history returned a non-ASCII commit"
            ) from exc
        if _HEX40_RE.fullmatch(commit) is None:
            raise EnforcementSourceRatificationError(
                "ratification history returned an invalid commit ID"
            )
        blob = _git(
            root, "cat-file", "blob",
            f"{commit}:{RATIFICATION_LEDGER_RELATIVE_PATH}",
        )
        if blob.returncode != 0:
            raise EnforcementSourceRatificationError(
                "ratification ledger was deleted in committed history"
            )
        rows = _load_rows(blob.stdout)
        if saw_version:
            if (not blob.stdout.startswith(previous_raw)
                    or len(blob.stdout) <= len(previous_raw)):
                raise EnforcementSourceRatificationError(
                    "ratification history is not a strict prefix extension"
                )
            if len(rows) != len(previous_rows) + 1:
                raise EnforcementSourceRatificationError(
                    "ratification history added more than one row"
                )
        elif len(rows) > 1:
            raise EnforcementSourceRatificationError(
                "ratification history introduced more than one row"
            )
        previous_raw = blob.stdout
        previous_rows = rows
        saw_version = True
    return frozenset(previous_rows)


def require_ratified_closure(blob_sha256s: Mapping[str, str]) -> str:
    """Return the closure digest only when committed ledger history contains it."""
    digest = closure_digest_sha256(blob_sha256s)
    if digest not in _committed_ratification_digests():
        raise EnforcementSourceRatificationError(
            "enforcement-source-closure-unratified: closure digest is absent "
            "from the read-only ledger"
        )
    return digest
