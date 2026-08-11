"""Canonical identity and read-only parser for the T-139 publication ledger.

This module deliberately has no reservation writer.  A writer cannot provide
cross-worktree uniqueness until reservation is integrated with canonical-main
landing under the shared Git-common-directory lock.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


PUBLICATION_FAMILY_ROOT = "88d68f9127b31df5aafc3d59607896626a1652e8"
PUBLICATION_LEDGER_KIND = "individual_publication"
PUBLICATION_LEDGER_SCHEMA_VERSION = "t139-publication-reservation/v1"

_PRIMARY_FAMILY_ROOT = "dce4ae4fed6f4fb33747165c5b92c16d01822850"
_PRIMARY_LEDGER_KIND = "alpha_reservation"
_ENTRY_KEYS = frozenset({"family_root", "kind", "ordinal", "schema_version"})
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
_CANONICAL_LEDGER_BY_IDENTITY = {
    (PUBLICATION_FAMILY_ROOT, PUBLICATION_LEDGER_KIND): PurePosixPath(
        "output/registry/t139-publication-reservations.jsonl"
    ),
}


class PublicationLedgerError(RuntimeError):
    """The canonical publication ledger cannot be accepted."""


@dataclass(frozen=True, slots=True)
class PublicationReservation:
    """One canonical publication reservation entry."""

    family_root: str
    kind: str
    ordinal: int
    schema_version: str


@dataclass(frozen=True, slots=True)
class PublicationLedger:
    """A present and validated publication ledger, possibly with zero entries."""

    entries: tuple[PublicationReservation, ...]


def _fail(gate: str, message: str) -> None:
    raise PublicationLedgerError(f"[{gate}] {message}")


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_relative_path() -> PurePosixPath:
    identity = (PUBLICATION_FAMILY_ROOT, PUBLICATION_LEDGER_KIND)
    try:
        return _CANONICAL_LEDGER_BY_IDENTITY[identity]
    except KeyError as exc:  # pragma: no cover - fixed module literals
        raise PublicationLedgerError(
            "[ledger-identity] canonical publication ledger identity is unbound"
        ) from exc


def canonical_publication_ledger_path() -> Path:
    """Return the sole ledger path derived from module-owned fixed literals."""

    return _repository_root().joinpath(*_canonical_relative_path().parts)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PublicationLedgerError(
            f"[json] value is not canonical JSON: {exc}"
        ) from exc


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except PublicationLedgerError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _read_regular_bytes(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise PublicationLedgerError(
            f"[ledger-read] canonical publication ledger is absent: {path}"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail("ledger-read", "canonical publication ledger must be a regular file")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                _fail("ledger-read", "canonical publication ledger is not regular")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
    except PublicationLedgerError:
        raise
    except OSError as exc:
        raise PublicationLedgerError(
            f"[ledger-read] canonical publication ledger cannot be read: {path}"
        ) from exc

    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity:
        _fail("ledger-read", "canonical publication ledger changed while being read")
    return b"".join(chunks)


def _require_exact_keys(value: Mapping[str, Any], *, label: str) -> None:
    actual = frozenset(value)
    if actual != _ENTRY_KEYS:
        missing = sorted(_ENTRY_KEYS - actual)
        unknown = sorted(actual - _ENTRY_KEYS)
        _fail(
            "entry-schema",
            f"{label} key set differs: missing={missing}, unknown={unknown}",
        )


def _require_primary_disjoint(value: Mapping[str, Any], *, label: str) -> None:
    if (
        value.get("family_root") == _PRIMARY_FAMILY_ROOT
        and value.get("kind") == _PRIMARY_LEDGER_KIND
    ):
        _fail(
            "entry-space",
            f"{label} occupies the primary (family_root, kind) entry space",
        )


def _parse_entry(value: Any, *, label: str) -> PublicationReservation:
    if not isinstance(value, Mapping):
        _fail("entry-schema", f"{label} must be an object")
    _require_exact_keys(value, label=label)
    _require_primary_disjoint(value, label=label)

    if value["kind"] != PUBLICATION_LEDGER_KIND:
        _fail(
            "ledger-kind",
            f"{label} kind is outside the closed publication ledger set",
        )
    if value["family_root"] != PUBLICATION_FAMILY_ROOT:
        _fail("family-root", f"{label} family_root is not the publication literal")
    if value["schema_version"] != PUBLICATION_LEDGER_SCHEMA_VERSION:
        _fail(
            "entry-schema",
            f"{label} schema_version is not publication-specific v1",
        )
    ordinal = value["ordinal"]
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
        _fail("entry-schema", f"{label} ordinal must be a positive integer")

    return PublicationReservation(
        family_root=PUBLICATION_FAMILY_ROOT,
        kind=PUBLICATION_LEDGER_KIND,
        ordinal=ordinal,
        schema_version=PUBLICATION_LEDGER_SCHEMA_VERSION,
    )


def _load_ledger_bytes(data: bytes, *, label: str) -> tuple[PublicationReservation, ...]:
    # Empty bytes are the sole representation of a present ledger with no
    # reservations.  Absence is rejected earlier by _read_regular_bytes.
    if data == b"":
        return ()
    if not data.endswith(b"\n"):
        _fail("ledger-framing", f"{label} must be newline terminated")

    entries: list[PublicationReservation] = []
    seen: set[tuple[str, str, int]] = set()
    for lineno, line in enumerate(data[:-1].split(b"\n"), 1):
        if not line:
            _fail("ledger-framing", f"{label} has a blank line at {lineno}")
        decoded = _decode_json(line, label=f"{label} line {lineno}")
        if not isinstance(decoded, Mapping):
            _fail("entry-schema", f"{label} line {lineno} must be an object")
        if _canonical_json_bytes(decoded) != line:
            _fail("ledger-canonical", f"{label} line {lineno} is not canonical JSON")
        entry = _parse_entry(decoded, label=f"{label} line {lineno}")
        identity = (entry.family_root, entry.kind, entry.ordinal)
        if identity in seen:
            _fail("entry-duplicate", f"{label} repeats reservation identity {identity!r}")
        seen.add(identity)
        entries.append(entry)
    return tuple(entries)


def _git(repository_root: Path, args: tuple[str, ...]) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
    }
    try:
        return subprocess.run(
            ("git", *args),
            cwd=repository_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublicationLedgerError(
            f"[git-operational] git command failed: {' '.join(args)}"
        ) from exc


def _current_head(repository_root: Path) -> str:
    result = _git(repository_root, ("rev-parse", "--verify", "HEAD^{commit}"))
    if result.returncode != 0:
        _fail("git-operational", "cannot resolve current HEAD")
    try:
        commit = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise PublicationLedgerError(
            "[git-operational] current HEAD is not ASCII"
        ) from exc
    if _COMMIT_RE.fullmatch(commit) is None:
        _fail("ledger-history", "current HEAD is not a full commit ID")
    return commit


def _blob_at_commit(
    repository_root: Path,
    *,
    commit: str,
    relative_path: PurePosixPath,
) -> bytes | None:
    result = _git(
        repository_root,
        ("cat-file", "blob", f"{commit}:{relative_path.as_posix()}"),
    )
    if result.returncode == 0:
        return result.stdout
    if result.returncode == 128:
        return None
    _fail("git-operational", f"cannot read ledger blob at {commit}")


def _ledger_history_tip(
    repository_root: Path,
    *,
    relative_path: PurePosixPath,
    current_head: str,
) -> bytes | None:
    """Reject deletion/recreation and non-prefix committed ledger history."""

    result = _git(
        repository_root,
        (
            "log",
            "--format=%H",
            "--reverse",
            "--full-history",
            current_head,
            "--",
            relative_path.as_posix(),
        ),
    )
    if result.returncode != 0:
        _fail("git-operational", "publication ledger history walk failed")

    previous: bytes | None = None
    for raw_commit in result.stdout.splitlines():
        try:
            commit = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise PublicationLedgerError(
                "[git-operational] publication ledger history is not ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit) is None:
            _fail("ledger-history", "history returned an invalid commit ID")
        blob = _blob_at_commit(
            repository_root,
            commit=commit,
            relative_path=relative_path,
        )
        if blob is None:
            _fail(
                "ledger-history",
                "publication ledger path was deleted in committed history",
            )
        _load_ledger_bytes(blob, label=f"publication ledger at {commit}")
        if previous is not None and not blob.startswith(previous):
            _fail(
                "ledger-history",
                "publication ledger history is not a prefix extension",
            )
        previous = blob
    return previous


def _read_publication_ledger_from_repository(
    repository_root: Path,
) -> PublicationLedger:
    root = Path(repository_root).resolve(strict=True)
    relative_path = _canonical_relative_path()
    ledger_path = root.joinpath(*relative_path.parts)
    current_bytes = _read_regular_bytes(ledger_path)
    entries = _load_ledger_bytes(current_bytes, label="publication ledger")
    history_tip = _ledger_history_tip(
        root,
        relative_path=relative_path,
        current_head=_current_head(root),
    )
    if history_tip is not None and current_bytes != history_tip:
        if not current_bytes.startswith(history_tip) or len(current_bytes) <= len(history_tip):
            _fail(
                "ledger-history",
                "working publication ledger is not a strict extension of committed history",
            )
    return PublicationLedger(entries=entries)


def read_publication_ledger() -> PublicationLedger:
    """Read the sole canonical ledger; absence and invalid history fail closed."""

    return _read_publication_ledger_from_repository(_repository_root())
