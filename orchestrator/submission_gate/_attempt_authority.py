"""Private a13 reservation and durable attempt-event authorities.

The alpha reservation literals in this module are quoted from
``docs/decisions.md:12941-12958`` (D282), with the append-only validator
requirements from ``output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:439-467``.
The ledger is therefore not selected by receipt input: ``family_root`` and
the path are fixed module-owned literals and a receipt declaration can only
reject a candidate.  Every inspection re-walks the complete bounded Git
history and re-reads the working-tree bytes; no history or reservation cache
is used.

This unit supplies an alpha-reservation authority and an event-chain
authority bound to that reservation.  It does not claim the producer-external
durable intent authority, PBS/qsub coverage, absence of attempts outside the
canonical ledger, or the stronger provenance guarantees outside the
canonical-main/common-directory boundary stated by D282 and §6.7.  The
``_AttemptAuthority`` deliberately stores frozen event snapshots, never raw
``ChainEvent`` instances: ``ChainEvent.payload`` only has a shallow mapping
proxy and would otherwise leave nested lists and dictionaries mutable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from . import _event_chain, _git
from ._receipt_io import ReceiptParseError, parse_receipt_bytes
from ._safe_io import (
    SafeIOError,
    create_only_relative_bytes,
    read_relative_regular_bytes,
)


ALPHA_LEDGER_PATH: Final = "output/registry/t139-alpha-reservations.jsonl"
ALPHA_FAMILY_ROOT: Final = "dce4ae4fed6f4fb33747165c5b92c16d01822850"
ALPHA_LEDGER_KIND: Final = "alpha_reservation"
ALPHA_SCHEMA_VERSION: Final = "t139-alpha-reservation/v1"

_ALPHA_ROW_KEYS: Final = frozenset(
    {"family_root", "kind", "ordinal", "schema_version"}
)
_LEDGER_EVIDENCE_KEYS: Final = frozenset(
    {
        "ledger_path",
        "family_root",
        "ordinal",
        "reservation_entry_sha256",
        "reservation_commit",
    }
)
_COMMIT_RE: Final = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_EVENT_NAME_RE: Final = re.compile(r"[0-9]+\.json\Z")
_MAX_EVENT_BYTES: Final = 4 * 1024 * 1024
_ALPHA_CAPABILITY_TOKEN: Final = object()
_ATTEMPT_CAPABILITY_TOKEN: Final = object()

# Named aliases make the two sealing domains explicit without making either
# token part of a public package surface.
_ALPHA_RESERVATION_CAPABILITY_TOKEN: Final = _ALPHA_CAPABILITY_TOKEN
_ATTEMPT_AUTHORITY_CAPABILITY_TOKEN: Final = _ATTEMPT_CAPABILITY_TOKEN


class AttemptAuthorityError(RuntimeError):
    """A reservation or durable attempt authority cannot be accepted."""


class AlphaReservationError(AttemptAuthorityError):
    """The fixed a13 alpha reservation cannot be accepted."""


class EventSinkError(AttemptAuthorityError):
    """The durable event directory cannot be loaded or appended safely."""


def _commit(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise AlphaReservationError(
            f"{label} must be a 40-character lowercase hexadecimal commit"
        )
    return value


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise AlphaReservationError(
            f"{label} must be a 64-character lowercase hexadecimal digest"
        )
    return value


def _root_identity(root: Path) -> tuple[int, int]:
    try:
        result = root.stat()
    except OSError as exc:
        raise AttemptAuthorityError("repository root identity cannot be read") from exc
    return result.st_dev, result.st_ino


def _freeze_json_value(value: object) -> Any:
    """Deeply freeze JSON-shaped values without importing receipt internals."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_json_value(child) for key, child in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(child) for child in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_json_value(child) for child in value)
    if isinstance(value, bytearray):
        return bytes(value)
    return value


def _thaw_json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(child) for child in value]
    if isinstance(value, frozenset):
        return [_thaw_json_value(child) for child in value]
    return value


def _canonical_json_bytes(value: object) -> bytes:
    """Match ``_event_chain``'s canonical envelope serialization exactly."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AttemptAuthorityError("event value is not canonical JSON") from exc


def _canonical_alpha_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AlphaReservationError("alpha reservation row is not canonical JSON") from exc


def _strict_relative_components(relative_path: object) -> tuple[str, ...]:
    if type(relative_path) is not str:
        raise AttemptAuthorityError("relative path must be a built-in string")
    if not relative_path or os.path.isabs(relative_path):
        raise AttemptAuthorityError("relative path must be non-empty and relative")
    if "\x00" in relative_path or "\\" in relative_path:
        raise AttemptAuthorityError("relative path contains an unsafe character")
    components = tuple(relative_path.split("/"))
    if any(component in {"", ".", ".."} for component in components):
        raise AttemptAuthorityError("relative path has an unsafe component")
    if any("\n" in component or "\r" in component for component in components):
        raise AttemptAuthorityError("relative path contains a line break")
    return components


def _open_relative_directory(
    root: Path,
    relative_path: str,
) -> tuple[int, tuple[int, int]]:
    """Open a directory through no-follow directory fds and pin its inode."""

    components = _strict_relative_components(relative_path)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if type(nofollow) is not int or type(directory) is not int:
        raise EventSinkError("safe event-directory flags are unavailable")
    flags = os.O_RDONLY | nofollow | directory
    descriptor: int | None = None
    try:
        descriptor = os.open(os.fspath(root), flags)
        for component in components:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        result = os.fstat(descriptor)
        if not stat.S_ISDIR(result.st_mode):
            raise EventSinkError("event directory is not a directory")
        return descriptor, (result.st_dev, result.st_ino)
    except EventSinkError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise
    except OSError as exc:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise EventSinkError("event directory cannot be opened safely") from exc


def _directory_entries(root: Path, relative_path: str) -> tuple[tuple[str, ...], tuple[int, int]]:
    descriptor, identity = _open_relative_directory(root, relative_path)
    try:
        try:
            entries = tuple(os.listdir(descriptor))
        except OSError as exc:
            raise EventSinkError("event directory cannot be enumerated") from exc
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    return entries, identity


def _validate_evidence(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != _LEDGER_EVIDENCE_KEYS:
        raise AlphaReservationError(
            "ledger_evidence must have exactly the five fixed keys"
        )
    evidence = dict(value)
    if evidence["ledger_path"] != ALPHA_LEDGER_PATH:
        raise AlphaReservationError("ledger_path is not the fixed alpha ledger path")
    # This is deliberately reject-only.  The declaration never selects the
    # family root used for the history walk.
    if evidence["family_root"] != ALPHA_FAMILY_ROOT:
        raise AlphaReservationError("family_root is not the fixed D282 literal")
    ordinal = evidence["ordinal"]
    if type(ordinal) is not int or ordinal < 1:
        raise AlphaReservationError("ledger_evidence.ordinal must be positive")
    _sha256(evidence["reservation_entry_sha256"], "reservation_entry_sha256")
    _commit(evidence["reservation_commit"], "reservation_commit")
    return evidence


def _parse_alpha_line(line: bytes, *, label: str) -> dict[str, object]:
    try:
        document = parse_receipt_bytes(line, label=label)
    except ReceiptParseError as exc:
        raise AlphaReservationError(f"{label} is not strict JSON") from exc
    value = _thaw_json_value(document.value)
    if not isinstance(value, dict) or frozenset(value) != _ALPHA_ROW_KEYS:
        raise AlphaReservationError(f"{label} does not have the exact four-key row schema")
    if value["family_root"] != ALPHA_FAMILY_ROOT:
        raise AlphaReservationError(f"{label} family_root is not the fixed D282 literal")
    if value["kind"] != ALPHA_LEDGER_KIND:
        raise AlphaReservationError(f"{label} kind is not alpha_reservation")
    ordinal = value["ordinal"]
    if type(ordinal) is not int or ordinal < 1:
        raise AlphaReservationError(f"{label} ordinal must be positive")
    if value["schema_version"] != ALPHA_SCHEMA_VERSION:
        raise AlphaReservationError(f"{label} schema_version is not t139 v1")
    if _canonical_alpha_json_bytes(value) != line:
        raise AlphaReservationError(f"{label} is not canonical JSON")
    return value


def _parse_alpha_jsonl(data: bytes, *, label: str) -> tuple[tuple[dict[str, object], ...], tuple[bytes, ...]]:
    if type(data) is not bytes:
        raise AlphaReservationError("alpha ledger data must be bytes")
    if not data or not data.endswith(b"\n"):
        raise AlphaReservationError(f"{label} must be non-empty and final-LF terminated")
    lines = data[:-1].split(b"\n")
    if not lines or any(not line for line in lines):
        raise AlphaReservationError(f"{label} contains a blank JSONL line")
    rows: list[dict[str, object]] = []
    for lineno, line in enumerate(lines, 1):
        rows.append(_parse_alpha_line(line, label=f"{label} line {lineno}"))
    return tuple(rows), tuple(lines)


def _validate_introduction(revisions: Sequence[_git.GitPathRevision]) -> None:
    if not revisions:
        raise AlphaReservationError("alpha ledger has no regular-file introduction")
    for revision in revisions:
        if revision.mode != "100644" or revision.data is None or revision.blob_object is None:
            raise AlphaReservationError("alpha ledger has a non-regular history generation")


def _scan_alpha_history(
    revisions: Sequence[_git.GitPathRevision],
) -> tuple[dict[str, object], str, str]:
    _validate_introduction(revisions)
    seen: set[tuple[str, int]] = set()
    first_commits: dict[tuple[str, int], str] = {}
    previous_data: bytes | None = None
    previous_count = 0
    final_row: dict[str, object] | None = None
    final_entry_bytes: bytes | None = None

    for revision in revisions:
        data = revision.data
        if data is None:
            raise AlphaReservationError("alpha ledger revision has no blob data")
        rows, line_bytes = _parse_alpha_jsonl(
            data,
            label=f"alpha ledger at {revision.commit}",
        )
        if previous_data is not None:
            if not data.startswith(previous_data) or len(rows) < previous_count:
                raise AlphaReservationError("alpha ledger history is not append-only")
            new_rows = rows[previous_count:]
            new_lines = line_bytes[previous_count:]
        else:
            new_rows = rows
            new_lines = line_bytes
        for row, raw_line in zip(new_rows, new_lines):
            identity = (str(row["family_root"]), int(row["ordinal"]))
            if identity in seen:
                raise AlphaReservationError(
                    "alpha ledger repeats a (family_root, ordinal) reservation"
                )
            seen.add(identity)
            first_commits[identity] = revision.commit
            final_entry_bytes = raw_line
            final_row = row
        previous_data = data
        previous_count = len(rows)
        if rows:
            final_row = rows[-1]
            final_entry_bytes = line_bytes[-1]

    if final_row is None or final_entry_bytes is None:
        raise AlphaReservationError("alpha ledger has no reservation entry")
    if len(seen) != 1:
        raise AlphaReservationError("this study must have exactly one alpha reservation")
    identity = (str(final_row["family_root"]), int(final_row["ordinal"]))
    if identity != (ALPHA_FAMILY_ROOT, 1):
        raise AlphaReservationError("alpha reservation ordinal must be exactly one")
    reservation_commit = first_commits.get(identity)
    if reservation_commit is None:
        raise AlphaReservationError("alpha reservation introduction commit is missing")
    digest = hashlib.sha256(final_entry_bytes).hexdigest()
    return final_row, digest, reservation_commit


@dataclass(frozen=True, slots=True, init=False)
class _AlphaReservationAuthority:
    """Sealed, root-bound authority for the one fixed alpha reservation."""

    ledger_path: str
    family_root: str
    ordinal: int
    reservation_entry_sha256: str
    reservation_commit: str
    measurement_head: str
    _root_identity: tuple[int, int]
    _seal: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        ledger_path: str,
        family_root: str,
        ordinal: int,
        reservation_entry_sha256: str,
        reservation_commit: str,
        measurement_head: str,
        root_identity: tuple[int, int],
        token: object,
    ) -> None:
        if type(self) is not _AlphaReservationAuthority or token is not _ALPHA_CAPABILITY_TOKEN:
            raise TypeError("_AlphaReservationAuthority requires its capability token")
        if ledger_path != ALPHA_LEDGER_PATH or family_root != ALPHA_FAMILY_ROOT:
            raise TypeError("alpha reservation literals are not fixed")
        if type(ordinal) is not int or ordinal != 1:
            raise TypeError("alpha reservation ordinal must be exactly one")
        if type(root_identity) is not tuple or len(root_identity) != 2 or any(
            type(item) is not int or item < 0 for item in root_identity
        ):
            raise TypeError("root identity is invalid")
        _sha256(reservation_entry_sha256, "reservation_entry_sha256")
        _commit(reservation_commit, "reservation_commit")
        _commit(measurement_head, "measurement_head")
        object.__setattr__(self, "ledger_path", ledger_path)
        object.__setattr__(self, "family_root", family_root)
        object.__setattr__(self, "ordinal", ordinal)
        object.__setattr__(self, "reservation_entry_sha256", reservation_entry_sha256)
        object.__setattr__(self, "reservation_commit", reservation_commit)
        object.__setattr__(self, "measurement_head", measurement_head)
        object.__setattr__(self, "_root_identity", root_identity)
        object.__setattr__(self, "_seal", token)

    @classmethod
    def _issue(
        cls,
        *,
        ledger_path: str,
        family_root: str,
        ordinal: int,
        reservation_entry_sha256: str,
        reservation_commit: str,
        measurement_head: str,
        root_identity: tuple[int, int],
        token: object,
    ) -> _AlphaReservationAuthority:
        return cls(
            ledger_path=ledger_path,
            family_root=family_root,
            ordinal=ordinal,
            reservation_entry_sha256=reservation_entry_sha256,
            reservation_commit=reservation_commit,
            measurement_head=measurement_head,
            root_identity=root_identity,
            token=token,
        )

    def assert_intact(self, repository_root: str | os.PathLike[str]) -> None:
        if type(self) is not _AlphaReservationAuthority or self._seal is not _ALPHA_CAPABILITY_TOKEN:
            raise AlphaReservationError("alpha reservation capability seal is invalid")
        try:
            root = _git.require_git_repository(repository_root)
            if _root_identity(root) != self._root_identity:
                raise AlphaReservationError("repository root identity changed")
            current_head = _git.resolve_head(root)
            if current_head != self.measurement_head:
                raise AlphaReservationError("measurement head changed")
            evidence = {
                "ledger_path": self.ledger_path,
                "family_root": self.family_root,
                "ordinal": self.ordinal,
                "reservation_entry_sha256": self.reservation_entry_sha256,
                "reservation_commit": self.reservation_commit,
            }
            fresh = _inspect_alpha_reservation(
                root,
                ledger_evidence=evidence,
                measurement_head=self.measurement_head,
            )
            if fresh != self:
                raise AlphaReservationError("alpha reservation authority changed")
        except AlphaReservationError:
            raise
        except (AttemptAuthorityError, _git.GitSupportError, SafeIOError) as exc:
            raise AlphaReservationError("alpha reservation integrity check failed") from exc


def _inspect_alpha_reservation(
    repository_root: str | os.PathLike[str],
    *,
    ledger_evidence: Mapping[str, object],
    measurement_head: str,
) -> _AlphaReservationAuthority:
    """Reconstruct the fixed a13 authority from a complete history walk."""

    evidence = _validate_evidence(ledger_evidence)
    _commit(measurement_head, "measurement_head")
    try:
        root = _git.require_git_repository(repository_root)
        root_identity = _root_identity(root)
        current_head = _git.resolve_head(root)
        if current_head != measurement_head:
            raise AlphaReservationError("measurement_head is not the current checkout HEAD")
        _git.require_safe_history(root)
        _git.require_ancestor(
            root,
            ancestor=ALPHA_FAMILY_ROOT,
            descendant=measurement_head,
        )
        revisions = _git.read_full_history(
            root,
            start_commit=ALPHA_FAMILY_ROOT,
            end_commit=measurement_head,
            path=ALPHA_LEDGER_PATH,
        )
        final_row, derived_digest, derived_commit = _scan_alpha_history(revisions)
        raw = read_relative_regular_bytes(
            root,
            ALPHA_LEDGER_PATH,
            max_bytes=_git.MAX_BLOB_BYTES,
        )
        if raw != revisions[-1].data:
            raise AlphaReservationError(
                "working-tree alpha ledger is not the measurement-head blob"
            )
        # Recheck the current bytes independently so no declaration or
        # revision cache can become a positive authority.
        _parse_alpha_jsonl(raw, label="working-tree alpha ledger")
        if evidence["ordinal"] != final_row["ordinal"]:
            raise AlphaReservationError("declared reservation ordinal differs from history")
        if evidence["reservation_entry_sha256"] != derived_digest:
            raise AlphaReservationError("declared reservation digest differs from history")
        if evidence["reservation_commit"] != derived_commit:
            raise AlphaReservationError("declared reservation commit differs from history")
        return _AlphaReservationAuthority._issue(
            ledger_path=ALPHA_LEDGER_PATH,
            family_root=ALPHA_FAMILY_ROOT,
            ordinal=1,
            reservation_entry_sha256=derived_digest,
            reservation_commit=derived_commit,
            measurement_head=measurement_head,
            root_identity=root_identity,
            token=_ALPHA_CAPABILITY_TOKEN,
        )
    except AlphaReservationError:
        raise
    except (
        AttemptAuthorityError,
        ReceiptParseError,
        _git.GitSupportError,
        SafeIOError,
        _event_chain.EventChainError,
    ) as exc:
        raise AlphaReservationError("alpha reservation inspection failed") from exc
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AlphaReservationError("alpha reservation inspection failed") from exc


@dataclass(frozen=True, slots=True)
class _FrozenEvent:
    """Deep-frozen event snapshot; never a raw ``ChainEvent``."""

    event_index: int
    previous_event_sha256: str
    event_type: str
    payload: Mapping[str, Any]
    event_sha256: str


def _event_envelope(event: _FrozenEvent) -> dict[str, object]:
    return {
        "event_index": event.event_index,
        "previous_event_sha256": event.previous_event_sha256,
        "event_type": event.event_type,
        "payload": _thaw_json_value(event.payload),
        "event_sha256": event.event_sha256,
    }


def _frozen_events(
    events: Sequence[Mapping[str, Any]],
) -> tuple[_FrozenEvent, ...]:
    try:
        replayed = _event_chain.replay_event_chain(events)
    except _event_chain.EventChainError:
        raise
    return tuple(
        _FrozenEvent(
            event_index=event.event_index,
            previous_event_sha256=event.previous_event_sha256,
            event_type=event.event_type,
            payload=_freeze_json_value(_thaw_json_value(event.payload)),
            event_sha256=event.event_sha256,
        )
        for event in replayed
    )


def _load_event_files(
    root: Path,
    event_directory: str,
) -> tuple[tuple[_FrozenEvent, ...], tuple[int, int]]:
    entries, directory_identity = _directory_entries(root, event_directory)
    numbered: list[tuple[int, str]] = []
    for name in entries:
        if _EVENT_NAME_RE.fullmatch(name) is None:
            raise EventSinkError(f"unexpected event-directory entry: {name!r}")
        index_text = name[:-5]
        index = int(index_text)
        if name != f"{index:04d}.json":
            raise EventSinkError(f"event filename is not canonical: {name!r}")
        numbered.append((index, name))
    numbered.sort()
    envelopes: list[Mapping[str, Any]] = []
    for expected_index, (index, name) in enumerate(numbered):
        if index != expected_index:
            raise EventSinkError("event files are not a contiguous zero-based sequence")
        relative_path = f"{event_directory}/{name}"
        try:
            raw = read_relative_regular_bytes(
                root,
                relative_path,
                max_bytes=_MAX_EVENT_BYTES,
            )
        except SafeIOError:
            raise
        if not raw.endswith(b"\n") or raw[:-1].endswith(b"\n") or not raw[:-1]:
            raise EventSinkError(f"event {name!r} is not one canonical LF-terminated line")
        line = raw[:-1]
        try:
            document = parse_receipt_bytes(line, label=relative_path)
        except ReceiptParseError:
            raise
        value = _thaw_json_value(document.value)
        if not isinstance(value, dict):
            raise EventSinkError(f"event {name!r} is not an object")
        canonical = _canonical_json_bytes(value) + b"\n"
        # #11: compare the parsed/canonical bytes to the exact bytes read by
        # read_relative_regular_bytes.  A valid hash with noncanonical bytes
        # is still rejected.
        if canonical != raw:
            raise EventSinkError(f"event {name!r} is not stored canonically")
        if value.get("event_index") != index:
            raise EventSinkError(f"event {name!r} index does not match its filename")
        envelopes.append(value)
    final_entries, final_identity = _directory_entries(root, event_directory)
    if final_identity != directory_identity or set(final_entries) != set(entries):
        raise EventSinkError("event directory changed while being read")
    return _frozen_events(envelopes), directory_identity


@dataclass(frozen=True, slots=True, init=False)
class _AttemptAuthority:
    """Sealed reservation-bound authority for a durable event chain."""

    reservation: _AlphaReservationAuthority
    event_directory: str
    events: tuple[_FrozenEvent, ...]
    _root_identity: tuple[int, int]
    _event_directory_identity: tuple[int, int]
    _seal: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        reservation: _AlphaReservationAuthority,
        event_directory: str,
        events: tuple[_FrozenEvent, ...],
        root_identity: tuple[int, int],
        event_directory_identity: tuple[int, int],
        token: object,
    ) -> None:
        if type(self) is not _AttemptAuthority or token is not _ATTEMPT_CAPABILITY_TOKEN:
            raise TypeError("_AttemptAuthority requires its capability token")
        if type(reservation) is not _AlphaReservationAuthority:
            raise TypeError("attempt authority requires a sealed alpha reservation")
        _strict_relative_components(event_directory)
        if type(events) is not tuple or not all(type(item) is _FrozenEvent for item in events):
            raise TypeError("events must be frozen event snapshots")
        for identity, label in (
            (root_identity, "root identity"),
            (event_directory_identity, "event directory identity"),
        ):
            if type(identity) is not tuple or len(identity) != 2 or any(
                type(item) is not int or item < 0 for item in identity
            ):
                raise TypeError(f"{label} is invalid")
        object.__setattr__(self, "reservation", reservation)
        object.__setattr__(self, "event_directory", event_directory)
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "_root_identity", root_identity)
        object.__setattr__(self, "_event_directory_identity", event_directory_identity)
        object.__setattr__(self, "_seal", token)

    @classmethod
    def _issue(
        cls,
        *,
        reservation: _AlphaReservationAuthority,
        event_directory: str,
        events: tuple[_FrozenEvent, ...],
        root_identity: tuple[int, int],
        event_directory_identity: tuple[int, int],
        token: object,
    ) -> _AttemptAuthority:
        return cls(
            reservation=reservation,
            event_directory=event_directory,
            events=events,
            root_identity=root_identity,
            event_directory_identity=event_directory_identity,
            token=token,
        )

    def assert_intact(self, repository_root: str | os.PathLike[str]) -> None:
        if type(self) is not _AttemptAuthority or self._seal is not _ATTEMPT_CAPABILITY_TOKEN:
            raise AttemptAuthorityError("attempt authority capability seal is invalid")
        try:
            root = _git.require_git_repository(repository_root)
            if _root_identity(root) != self._root_identity:
                raise AttemptAuthorityError("repository root identity changed")
            self.reservation.assert_intact(root)
            fresh_events, directory_identity = _load_event_files(root, self.event_directory)
            if directory_identity != self._event_directory_identity:
                raise AttemptAuthorityError("event directory identity changed")
            if fresh_events != self.events:
                raise AttemptAuthorityError("durable event chain changed")
        except AttemptAuthorityError:
            raise
        except (
            ReceiptParseError,
            _event_chain.EventChainError,
            _git.GitSupportError,
            SafeIOError,
        ) as exc:
            raise AttemptAuthorityError("attempt authority integrity check failed") from exc
        except (OSError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
            raise AttemptAuthorityError("attempt authority integrity check failed") from exc


def _load_attempt_authority(
    repository_root: str | os.PathLike[str],
    *,
    reservation: _AlphaReservationAuthority,
    event_directory: str,
) -> _AttemptAuthority:
    """Load and replay a durable event sink bound to one alpha reservation."""

    if type(reservation) is not _AlphaReservationAuthority or getattr(
        reservation, "_seal", None
    ) is not _ALPHA_CAPABILITY_TOKEN:
        raise AttemptAuthorityError("reservation is not a sealed alpha authority")
    try:
        root = _git.require_git_repository(repository_root)
        if _root_identity(root) != reservation._root_identity:
            raise AttemptAuthorityError("reservation root identity does not match")
        reservation.assert_intact(root)
        _strict_relative_components(event_directory)
        events, directory_identity = _load_event_files(root, event_directory)
        return _AttemptAuthority._issue(
            reservation=reservation,
            event_directory=event_directory,
            events=events,
            root_identity=_root_identity(root),
            event_directory_identity=directory_identity,
            token=_ATTEMPT_CAPABILITY_TOKEN,
        )
    except AttemptAuthorityError:
        raise
    except (
        ReceiptParseError,
        _event_chain.EventChainError,
        _git.GitSupportError,
        SafeIOError,
    ) as exc:
        raise AttemptAuthorityError("attempt authority load failed") from exc
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AttemptAuthorityError("attempt authority load failed") from exc


def _append_attempt_event(
    repository_root: str | os.PathLike[str],
    authority: _AttemptAuthority,
    *,
    event_type: str,
    payload: Mapping[str, object],
) -> _AttemptAuthority:
    """Append one canonical event through the create-only safe-I/O sink."""

    if type(authority) is not _AttemptAuthority or getattr(authority, "_seal", None) is not _ATTEMPT_CAPABILITY_TOKEN:
        raise AttemptAuthorityError("authority is not a sealed attempt authority")
    if not isinstance(payload, Mapping):
        raise AttemptAuthorityError("event payload must be a mapping")
    try:
        root = _git.require_git_repository(repository_root)
        authority.assert_intact(root)
        payload_snapshot = _thaw_json_value(_freeze_json_value(payload))
        prior = [_event_envelope(event) for event in authority.events]

        def sink(name: str, data: bytes) -> None:
            if type(name) is not str or name != f"{len(prior):04d}.json":
                raise EventSinkError("event sink received a noncanonical filename")
            create_only_relative_bytes(
                root,
                f"{authority.event_directory}/{name}",
                data,
            )

        new_event = _event_chain.append_event(
            prior,
            event_type=event_type,
            payload=payload_snapshot,
            create_only=sink,
        )
        if _event_chain.hash_event(new_event) != new_event["event_sha256"]:
            raise EventSinkError("appended event hash did not rederive")
        _event_chain.replay_event_chain([*prior, new_event])
        fresh_events, directory_identity = _load_event_files(
            root,
            authority.event_directory,
        )
        expected = (*authority.events, fresh_events[-1]) if fresh_events else ()
        if fresh_events != expected:
            raise EventSinkError("appended event replay differs from authority")
        return _AttemptAuthority._issue(
            reservation=authority.reservation,
            event_directory=authority.event_directory,
            events=fresh_events,
            root_identity=_root_identity(root),
            event_directory_identity=directory_identity,
            token=_ATTEMPT_CAPABILITY_TOKEN,
        )
    except AttemptAuthorityError:
        raise
    except (
        ReceiptParseError,
        _event_chain.EventChainError,
        _git.GitSupportError,
        SafeIOError,
    ) as exc:
        raise AttemptAuthorityError("attempt event append failed") from exc
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AttemptAuthorityError("attempt event append failed") from exc


__all__ = ()
