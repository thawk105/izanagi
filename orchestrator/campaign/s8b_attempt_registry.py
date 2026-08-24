# -*- coding: utf-8 -*-
"""File-backed, currently unconnected 8b attempt-registry adapter.

This adapter does not close D510 decision 4.  A caller can bypass it and read
an output file directly, and can import :mod:`attempt_registry_core` directly.
True ordering enforcement requires a trusted launcher which owns the output
surface.  This module is also not a "safe recovery mechanism": no scheduler
accounting collector exists here, and recovery evidence remains caller input.

The adapter supplies guarded file publication, directory fsyncs, and typed API
ordering only for callers which choose this API.  It is deliberately not
imported by the production 8b floor campaign.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
import hashlib
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
from typing import Any, TypeVar, cast
import weakref

from . import attempt_registry_core as core
from . import s8b_attempt_profile as profile8b
from . import s8b_holdout_admission as admission


class S8BAttemptRegistryError(RuntimeError):
    """The durable 8b adapter rejected an operation."""


_ISSUED_HANDLE_TOKENS: dict[
    object,
    tuple[
        weakref.ReferenceType[object],
        type[object],
        tuple[object, ...],
        tuple[object, ...],
    ],
] = {}
_STAGING_COUNTER = itertools.count()
_MAX_DURABLE_BYTES = 16 * 1024 * 1024
_CLASSIFICATION_CLAIM_SCHEMA = "s8b-attempt-classification-claim/v2"
_CLASSIFICATION_CLAIM_EVENT = "classification-claim"
_CLASSIFICATION_CLAIM_DIR = "classification-claims"
_FLOOR_CONSUMED_MARKER_KEYS = frozenset({
    "schema_version",
    "event",
    "claim_digest",
    "attempt_id",
    "campaign_run_id",
    "manifest_sha256",
    "run_relpath",
    "cell_id",
    "freeze_holdout_key",
    "configuration_id",
    "observation_role",
})
_FLOOR_CONSUMED_MARKER_SCHEMA = "s8b-holdout-attempt-consumption/v1"
_ZERO_OUTPUT_SHA256 = hashlib.sha256(b"").hexdigest()

# Tests enumerate this exact set and prove that every point fires.  A raised
# hook models process loss at the boundary; the authoritative path must still
# name either the old complete bytes or the new complete bytes.
ATOMIC_UPDATE_FAULT_POINTS = (
    "after-authoritative-read",
    "after-replay",
    "after-transition",
    "after-candidate-validation",
    "after-staging-fsync",
    "after-replace",
    "after-parent-fsync",
)
CLASSIFICATION_PUBLISH_FAULT_POINTS = (
    "after-classification-claim",
    "after-classification-receipt",
)
_FAULT_HOOK: Callable[[str], None] | None = None
_PRELOCK_SNAPSHOT_HOOK: Callable[[bytes], None] | None = None


def _fail(gate: str, message: str) -> None:
    raise S8BAttemptRegistryError(f"[{gate}] {message}")


def _sha256(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail("s8b-attempt-registry-schema", f"{label} is not a SHA-256 digest")
    return value


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        _fail(
            "s8b-attempt-registry-schema",
            f"{label} is not a bounded non-empty string",
        )
    return value


def _consumption_identity(
    *,
    campaign_run_id: object,
    manifest_sha256: object,
    run_relpath: object,
    cell_id: object,
    attempt_id: object,
    slot: profile8b.S8BAttemptSlot | None = None,
) -> tuple[str, str, str, str, str]:
    campaign = _text(campaign_run_id, label="campaign_run_id")
    manifest = _sha256(manifest_sha256, label="manifest_sha256")
    run = _text(run_relpath, label="run_relpath")
    cell = _text(cell_id, label="cell_id")
    attempt = _text(attempt_id, label="attempt_id")
    portable_run = PurePosixPath(run)
    if (
        portable_run.is_absolute()
        or ".." in portable_run.parts
        or portable_run.as_posix() != run
        or portable_run.name != campaign
    ):
        _fail(
            "s8b-attempt-registry-consume",
            "campaign/run identity is not canonical",
        )
    if slot is not None:
        expected_cell = (
            f"{slot.freeze_holdout_key}::{slot.configuration_id}"
        )
        if cell != expected_cell or not attempt.startswith(f"{cell}::"):
            _fail(
                "s8b-attempt-registry-consume",
                "attempt/cell identity differs from the registry slot",
            )
    return campaign, manifest, run, cell, attempt


def _fault(point: str) -> None:
    if point not in (
        *ATOMIC_UPDATE_FAULT_POINTS,
        *CLASSIFICATION_PUBLISH_FAULT_POINTS,
    ):
        _fail("s8b-attempt-registry-fault", f"unknown fault point: {point}")
    hook = _FAULT_HOOK
    if hook is not None:
        hook(point)


@dataclass(frozen=True, slots=True)
class _AttemptState:
    repo_root: Path
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
    ]
    binding: profile8b.S8BAttemptBinding
    freeze_id: str
    slot_id: profile8b.S8BSlotIdentity
    registry_path: Path
    admission_claim_digest: str
    attempt_id: str
    campaign_run_id: str
    manifest_sha256: str
    run_relpath: str
    cell_id: str
    deferred_output_reader: Callable[[], bytes]
    classification_receipt_bytes: bytes | None = None
    classification_receipt_sha256: str | None = None
    classification_event_sha256: str | None = None
    observation_event_sha256: str | None = None
    raw_output_sha256: str | None = None


@dataclass(frozen=True)
class ReservedAttempt:
    """A reserved slot whose pre-observation classification is not complete."""

    _state: _AttemptState
    _seal: object


@dataclass(frozen=True)
class ClassifiedAttempt:
    """A no-failure classification whose claim and receipt were published."""

    _state: _AttemptState
    _seal: object


@dataclass(frozen=True)
class ClassifiedFailure:
    """A pre-observation failure, intentionally distinct from an observation."""

    _state: _AttemptState
    _seal: object


@dataclass(frozen=True)
class CapturedObservation:
    """An observation-start whose deferred output bytes have been digested."""

    _state: _AttemptState
    _seal: object


HandleT = TypeVar(
    "HandleT",
    ReservedAttempt,
    ClassifiedAttempt,
    ClassifiedFailure,
    CapturedObservation,
)


def _state_fingerprint(state: _AttemptState) -> tuple[object, ...]:
    return (
        state.repo_root,
        id(state.profile),
        (
            state.binding.freeze_sha256,
            state.binding.protocol_sha256,
            state.binding.schedule_sha256,
        ),
        state.freeze_id,
        state.slot_id,
        state.registry_path,
        state.admission_claim_digest,
        state.attempt_id,
        state.campaign_run_id,
        state.manifest_sha256,
        state.run_relpath,
        state.cell_id,
        id(state.deferred_output_reader),
        state.classification_receipt_bytes,
        state.classification_receipt_sha256,
        state.classification_event_sha256,
        state.observation_event_sha256,
        state.raw_output_sha256,
    )


def _new_handle(handle_type: type[HandleT], state: _AttemptState) -> HandleT:
    token = object()
    handle = handle_type(state, token)
    attempt_key = (
        state.registry_path,
        state.freeze_id,
        state.slot_id,
        handle_type,
    )

    def discard(_reference: weakref.ReferenceType[object]) -> None:
        _ISSUED_HANDLE_TOKENS.pop(token, None)

    _ISSUED_HANDLE_TOKENS[token] = (
        weakref.ref(handle, discard),
        handle_type,
        attempt_key,
        _state_fingerprint(state),
    )
    return handle


def _require_handle(value: object, expected: type[HandleT]) -> _AttemptState:
    if type(value) is not expected:
        _fail(
            "s8b-attempt-registry-handle",
            f"operation requires exact {expected.__name__}",
        )
    token = value._seal  # type: ignore[union-attr]
    issued = _ISSUED_HANDLE_TOKENS.get(token)
    if issued is None:
        _fail("s8b-attempt-registry-handle", "handle private seal differs")
    issued_reference, issued_type, attempt_key, state_fingerprint = issued
    if issued_reference() is not value or issued_type is not expected:
        _fail(
            "s8b-attempt-registry-handle",
            "handle was not issued for this attempt phase",
        )
    state = value._state  # type: ignore[union-attr]
    if type(state) is not _AttemptState:
        _fail("s8b-attempt-registry-handle", "issued handle state type differs")
    if _state_fingerprint(state) != state_fingerprint:
        _fail(
            "s8b-attempt-registry-handle",
            "issued handle state differs from its phase token",
        )
    _assert_state_path(state)
    expected_key = (
        state.registry_path,
        state.freeze_id,
        state.slot_id,
        expected,
    )
    if attempt_key != expected_key:
        _fail(
            "s8b-attempt-registry-handle",
            "handle attempt-phase token differs",
        )
    return state


def _assert_profile(
    profile: core.DomainProfile[Any, Any],
) -> core.DomainProfile[
    profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
]:
    if type(profile) is not core.DomainProfile:
        _fail(
            "s8b-attempt-registry-profile",
            "domain profile type differs from the frozen 8b profile",
        )
    recovery = profile.recovery_policy
    transition = profile.transition_policy
    if (
        type(recovery) is not core.RecoveryPolicy
        or type(transition) is not core.TransitionPolicy
        or type(transition.max_consumptions_per_budget_key) is not int
        or type(recovery.authority_id) is not str
        or type(recovery.authority_policy_sha256) is not str
    ):
        _fail(
            "s8b-attempt-registry-profile",
            "domain profile policy shape differs from frozen 8b",
        )
    try:
        expected = profile8b.make_s8b_domain_profile(
            max_consumptions_per_budget_key=(
                transition.max_consumptions_per_budget_key
            ),
            recovery_authority_id=recovery.authority_id,
            recovery_authority_policy_sha256=(
                recovery.authority_policy_sha256
            ),
        )
    except core.AttemptRegistryCoreError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-profile] variable profile values are invalid"
        ) from exc
    expected_transition = expected.transition_policy
    expected_recovery = expected.recovery_policy
    assert expected_recovery is not None
    layout = profile.layout
    expected_layout = expected.layout

    def exact_string_tuple(value: object, known: tuple[str, ...]) -> bool:
        if type(value) is not tuple:
            return False
        items = cast(tuple[object, ...], value)
        return len(items) == len(known) and all(
            type(item) is str and item == expected_item
            for item, expected_item in zip(items, known)
        )

    def exact_string_frozenset(
        value: object,
        known: frozenset[str],
    ) -> bool:
        if type(value) is not frozenset:
            return False
        items = cast(frozenset[object], value)
        if len(items) != len(known):
            return False
        if any(type(item) is not str for item in items):
            return False
        return all(item in known for item in items)

    def exact_path(value: object, known: PurePosixPath) -> bool:
        if type(value) is not PurePosixPath:
            return False
        path = cast(PurePosixPath, value)
        return exact_string_tuple(path.parts, known.parts)

    if (
        type(profile.schema) is not core.SchemaProfile
        or profile.schema is not expected.schema
        or type(layout) is not core.RegistryLayout
        or layout is not expected_layout
        or not exact_path(layout.registry_path, expected_layout.registry_path)
        or not exact_path(
            layout.classification_receipt_dir,
            expected_layout.classification_receipt_dir,
        )
        or not exact_string_tuple(profile.statuses, expected.statuses)
        or not exact_string_frozenset(
            profile.retryable_reasons, expected.retryable_reasons,
        )
        or not exact_string_frozenset(
            profile.process_identity_keys, expected.process_identity_keys,
        )
        or type(profile.slot_codec) is not type(expected.slot_codec)
        or profile.slot_codec is not expected.slot_codec
        or type(profile.binding_codec) is not type(expected.binding_codec)
        or profile.binding_codec is not expected.binding_codec
        or type(transition.require_previous_terminal) is not bool
        or transition.require_previous_terminal
        is not expected_transition.require_previous_terminal
        or type(transition.forbid_retry_after_observation) is not bool
        or transition.forbid_retry_after_observation
        is not expected_transition.forbid_retry_after_observation
        or type(transition.allow_recovered_abandonment) is not bool
        or transition.allow_recovered_abandonment
        is not expected_transition.allow_recovered_abandonment
        or transition.max_series_attempts is not expected_transition.max_series_attempts
        or type(transition.require_terminal_reason_equals_classification) is not bool
        or transition.require_terminal_reason_equals_classification
        is not expected_transition.require_terminal_reason_equals_classification
        or type(transition.budget_key) is not type(expected_transition.budget_key)
        or transition.budget_key is not expected_transition.budget_key
        or transition.max_consumptions_per_budget_key
        != expected_transition.max_consumptions_per_budget_key
        or type(recovery.receipt_schema_version) is not str
        or recovery.receipt_schema_version != expected_recovery.receipt_schema_version
        or type(recovery.receipt_event) is not str
        or recovery.receipt_event != expected_recovery.receipt_event
        or type(recovery.receipt_source) is not str
        or recovery.receipt_source != expected_recovery.receipt_source
        or recovery.authority_id != expected_recovery.authority_id
        or recovery.authority_policy_sha256
        != expected_recovery.authority_policy_sha256
        or not exact_string_frozenset(
            recovery.failure_reasons, expected_recovery.failure_reasons,
        )
        or profile.build_genesis_fields is not expected.build_genesis_fields
        or type(profile.freeze_id_from_genesis)
        is not type(expected.freeze_id_from_genesis)
        or profile.freeze_id_from_genesis is not expected.freeze_id_from_genesis
        or type(profile.binding_conflict_message) is not str
        or profile.binding_conflict_message != expected.binding_conflict_message
        or profile.binding_mismatch is not expected.binding_mismatch
    ):
        _fail(
            "s8b-attempt-registry-profile",
            "domain profile differs from frozen 8b semantics",
        )
    return profile


def _relative_registry_path(freeze_sha256: str) -> PurePosixPath:
    freeze_sha256 = _sha256(freeze_sha256, label="freeze_sha256")
    template = profile8b.S8B_REGISTRY_LAYOUT.registry_path
    rendered = PurePosixPath(
        template.as_posix().format(freeze_sha256=freeze_sha256)
    )
    if rendered.is_absolute() or ".." in rendered.parts:
        _fail("s8b-attempt-registry-path", "registry layout is not relative")
    return rendered


def _entry_paths(
    repo_root: Path,
    *,
    freeze_sha256: str,
    requested_registry_path: Path | None = None,
) -> tuple[Path, Path]:
    # Provisioning is part of every adapter entry.  In particular, it creates
    # the lock inode before the private shared lock is opened.
    root = admission.provision_shared_admission_root(Path(repo_root))
    _fsync_shared_root_chain(root)
    relative = _relative_registry_path(freeze_sha256)
    registry = root.joinpath(*relative.parts)
    if requested_registry_path is not None:
        requested = Path(os.path.abspath(os.fspath(requested_registry_path)))
        canonical = Path(os.path.abspath(os.fspath(registry)))
        if requested != canonical:
            _fail(
                "s8b-attempt-registry-path",
                "alternate registry path is forbidden",
            )
    return root, registry


def registry_path(repo_root: Path, *, freeze_sha256: str) -> Path:
    """Return the only accepted path for one freeze-wide 8b registry."""

    _root, path = _entry_paths(
        Path(repo_root), freeze_sha256=freeze_sha256,
    )
    return path


def _assert_state_path(state: _AttemptState) -> None:
    if type(state.binding) is not profile8b.S8BAttemptBinding:
        _fail("s8b-attempt-registry-handle", "handle binding type differs")
    _assert_profile(state.profile)
    if not state.repo_root.is_absolute() or state.repo_root != state.repo_root.resolve():
        _fail("s8b-attempt-registry-handle", "handle repo root is not canonical")
    _root, canonical = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )
    if state.registry_path != canonical:
        _fail("s8b-attempt-registry-handle", "handle registry path differs")
    if state.binding.freeze_sha256 != state.freeze_id:
        _fail("s8b-attempt-registry-handle", "handle freeze binding differs")


def _read_regular_bytes(path: Path, *, missing_ok: bool = False) -> bytes | None:
    admission._assert_no_symlink_components(path.parent)
    try:
        before = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        _fail("s8b-attempt-registry-storage", f"durable file is absent: {path.name}")
    except OSError as exc:
        raise S8BAttemptRegistryError(
            f"[s8b-attempt-registry-storage] cannot lstat {path.name}"
        ) from exc
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        _fail(
            "s8b-attempt-registry-storage",
            f"durable path is not a regular file: {path.name}",
        )
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        _fail("s8b-attempt-registry-storage", "O_NOFOLLOW is unavailable")
    try:
        fd = os.open(path, os.O_RDONLY | nofollow)
    except OSError as exc:
        raise S8BAttemptRegistryError(
            f"[s8b-attempt-registry-storage] cannot open {path.name}"
        ) from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            _fail(
                "s8b-attempt-registry-storage",
                f"durable inode changed while opening: {path.name}",
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > _MAX_DURABLE_BYTES:
                _fail(
                    "s8b-attempt-registry-storage",
                    f"durable file exceeds byte bound: {path.name}",
                )
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _canonical_line_bytes(value: Mapping[str, Any]) -> bytes:
    return core.canonical_json_bytes(dict(value)) + b"\n"


def _registry_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_line_bytes(row) for row in rows)


def _canonical_document(data: bytes, *, label: str) -> dict[str, Any]:
    if type(data) is not bytes or not data.endswith(b"\n") or data.count(b"\n") != 1:
        _fail(
            "s8b-attempt-registry-canonical",
            f"{label} is not one canonical JSON line",
        )
    try:
        value = json.loads(data[:-1].decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise S8BAttemptRegistryError(
            f"[s8b-attempt-registry-canonical] {label} is not strict JSON"
        ) from exc
    if type(value) is not dict or _canonical_line_bytes(value) != data:
        _fail(
            "s8b-attempt-registry-canonical",
            f"{label} is not a canonical object",
        )
    return value


def _fsync_directory(path: Path) -> None:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, os.O_RDONLY | nofollow)
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            _fail("s8b-attempt-registry-storage", "fsync parent is not a directory")
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_shared_root_chain(root: Path) -> None:
    """Fsync the common-dir chain after admission recursively provisions it."""

    relative_parts = admission._ROOT_REL.parts
    common = root
    for _part in relative_parts:
        common = common.parent
    cursor = common
    chain = [common]
    for part in relative_parts:
        cursor = cursor / part
        chain.append(cursor)
    if cursor != root:
        _fail(
            "s8b-attempt-registry-storage",
            "shared admission root differs from its common-dir layout",
        )
    for directory in chain:
        _fsync_directory(directory)


def _staging_path(destination: Path) -> Path:
    return destination.parent / (
        f".{destination.name}.staging-{os.getpid()}-"
        f"{next(_STAGING_COUNTER)}-{secrets.token_hex(8)}"
    )


def _ensure_durable_directory(path: Path) -> None:
    """Create missing directory levels and fsync every new parent entry."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    admission._assert_no_symlink_components(absolute)
    missing: list[Path] = []
    cursor = absolute
    while True:
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            missing.append(cursor)
            parent = cursor.parent
            if parent == cursor:
                _fail(
                    "s8b-attempt-registry-storage",
                    "cannot find an existing directory ancestor",
                )
            cursor = parent
            continue
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot inspect directory parent"
            ) from exc
        if not stat.S_ISDIR(mode) or cursor.is_symlink():
            _fail(
                "s8b-attempt-registry-storage",
                "durable directory ancestor is not a real directory",
            )
        break
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot create durable directory"
            ) from exc
        admission._assert_no_symlink_components(directory)
        try:
            mode = directory.lstat().st_mode
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot inspect durable directory"
            ) from exc
        if not stat.S_ISDIR(mode) or directory.is_symlink():
            _fail(
                "s8b-attempt-registry-storage",
                "new durable path is not a real directory",
            )
        _fsync_directory(directory)
        _fsync_directory(directory.parent)


def _write_staging(destination: Path, payload: bytes, *, logical_name: str) -> Path:
    # The random suffix makes stale files from a reused pid harmless.  O_EXCL
    # remains the final arbiter.
    admission.assert_holdout_safe_bytes(logical_name, payload)
    _ensure_durable_directory(destination.parent)
    for _attempt in range(8):
        staging = _staging_path(destination)
        try:
            admission.write_guarded_create_bytes(
                staging, payload, logical_name=logical_name,
            )
        except FileExistsError:
            continue
        except BaseException:
            try:
                staging.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                raise S8BAttemptRegistryError(
                    "[s8b-attempt-registry-storage] cannot remove failed staging file"
                ) from cleanup_error
            _fsync_directory(staging.parent)
            raise
        return staging
    _fail("s8b-attempt-registry-storage", "cannot allocate unique staging name")


def _unlink_staging(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-storage] cannot remove staging file"
        ) from exc
    _fsync_directory(path.parent)


def _publish_create_only(
    destination: Path,
    payload: bytes,
    *,
    logical_name: str,
    allow_exact_retry: bool,
) -> None:
    prior = _read_regular_bytes(destination, missing_ok=True)
    if prior is not None:
        if allow_exact_retry and prior == payload:
            return
        _fail(
            "s8b-attempt-registry-create-only",
            f"durable destination already exists: {destination.name}",
        )
    staging: Path | None = None
    try:
        staging = _write_staging(
            destination, payload, logical_name=logical_name,
        )
        try:
            os.link(staging, destination, follow_symlinks=False)
        except FileExistsError:
            prior = _read_regular_bytes(destination)
            if not allow_exact_retry or prior != payload:
                _fail(
                    "s8b-attempt-registry-create-only",
                    f"durable destination raced: {destination.name}",
                )
        except OSError as exc:
            raise S8BAttemptRegistryError(
                f"[s8b-attempt-registry-storage] cannot publish {destination.name}"
            ) from exc
        _fsync_directory(destination.parent)
    finally:
        _unlink_staging(staging)


def _slot_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot_id: profile8b.S8BSlotIdentity,
) -> profile8b.S8BAttemptSlot:
    slots = rows[0].get("slots")
    if type(slots) is not list:
        _fail("s8b-attempt-registry-schema", "genesis slots are unavailable")
    matches = []
    for index, value in enumerate(slots):
        slot = profile.slot_codec.parse(value, label=f"genesis slot {index}")
        if profile.slot_codec.slot_id(slot) == slot_id:
            matches.append(slot)
    if len(matches) != 1:
        _fail("s8b-attempt-registry-slot", "slot identity is not unique in genesis")
    return matches[0]


def _row_is_for_slot(
    row: Mapping[str, Any], slot: profile8b.S8BAttemptSlot,
) -> bool:
    return all(
        row.get(field) == value
        for field, value in {
            "freeze_holdout_key": slot.freeze_holdout_key,
            "configuration_id": slot.configuration_id,
            "repetition": slot.repetition,
            "attempt_ordinal": slot.attempt_ordinal,
        }.items()
    )


def _rows_for_event(
    rows: Sequence[Mapping[str, Any]],
    *,
    slot: profile8b.S8BAttemptSlot,
    event: str,
) -> list[Mapping[str, Any]]:
    return [
        row for row in rows
        if row.get("event") == event and _row_is_for_slot(row, slot)
    ]


def _slot_address_payload(
    *,
    freeze_sha256: str,
    slot: profile8b.S8BAttemptSlot,
) -> dict[str, Any]:
    return {
        "freeze_sha256": freeze_sha256,
        "freeze_holdout_key": slot.freeze_holdout_key,
        "configuration_id": slot.configuration_id,
        "repetition": slot.repetition,
        "attempt_ordinal": slot.attempt_ordinal,
    }


def _classification_claim_path(
    root: Path,
    *,
    freeze_sha256: str,
    slot: profile8b.S8BAttemptSlot,
) -> Path:
    address = hashlib.sha256(
        core.canonical_json_bytes(
            _slot_address_payload(freeze_sha256=freeze_sha256, slot=slot)
        )
    ).hexdigest()
    receipt_root = root.joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts
    )
    return receipt_root / _CLASSIFICATION_CLAIM_DIR / f"{address}.json"


def _receipt_path(root: Path, receipt_sha256: str) -> Path:
    receipt_sha256 = _sha256(
        receipt_sha256, label="classification_receipt_sha256",
    )
    return root.joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts,
        f"{receipt_sha256}.json",
    )


def _claim_document(
    *,
    freeze_sha256: str,
    slot: profile8b.S8BAttemptSlot,
    classification_receipt: Mapping[str, Any],
    classification_receipt_sha256: str,
    classification_event_sha256: str,
    admission_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": _CLASSIFICATION_CLAIM_SCHEMA,
        "event": _CLASSIFICATION_CLAIM_EVENT,
        **_slot_address_payload(freeze_sha256=freeze_sha256, slot=slot),
        "schedule_row_sha256": slot.schedule_row_sha256,
        "classification_receipt": dict(classification_receipt),
        "classification_receipt_sha256": classification_receipt_sha256,
        "classification_event_sha256": classification_event_sha256,
        "admission_claim_digest": admission_claim_digest,
        "attempt_id": attempt_id,
        "campaign_run_id": campaign_run_id,
        "manifest_sha256": manifest_sha256,
        "run_relpath": run_relpath,
        "cell_id": cell_id,
    }


_CLAIM_KEYS = frozenset({
    "schema_version",
    "event",
    "freeze_sha256",
    "freeze_holdout_key",
    "configuration_id",
    "repetition",
    "attempt_ordinal",
    "schedule_row_sha256",
    "classification_receipt",
    "classification_receipt_sha256",
    "classification_event_sha256",
    "admission_claim_digest",
    "attempt_id",
    "campaign_run_id",
    "manifest_sha256",
    "run_relpath",
    "cell_id",
})


def _classification_claim(
    *,
    root: Path,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BAttemptSlot,
    missing_ok: bool = False,
) -> tuple[Mapping[str, Any], bytes] | None:
    claim_path = _classification_claim_path(
        root, freeze_sha256=binding.freeze_sha256, slot=slot,
    )
    claim_bytes = _read_regular_bytes(claim_path, missing_ok=missing_ok)
    if claim_bytes is None:
        return None
    claim = _canonical_document(claim_bytes, label="classification claim")
    if frozenset(claim) != _CLAIM_KEYS:
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim exact keys differ",
        )
    expected_identity = {
        "schema_version": _CLASSIFICATION_CLAIM_SCHEMA,
        "event": _CLASSIFICATION_CLAIM_EVENT,
        **_slot_address_payload(freeze_sha256=binding.freeze_sha256, slot=slot),
        "schedule_row_sha256": slot.schedule_row_sha256,
    }
    for field, expected in expected_identity.items():
        if claim.get(field) != expected:
            _fail(
                "s8b-attempt-registry-classification",
                f"classification claim differs: {field}",
            )
    receipt_value = claim.get("classification_receipt")
    if type(receipt_value) is not dict:
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim receipt is not an exact object",
        )
    receipt_bytes = _canonical_line_bytes(receipt_value)
    receipt_sha256 = _sha256(
        claim.get("classification_receipt_sha256"),
        label="classification claim.classification_receipt_sha256",
    )
    if hashlib.sha256(receipt_bytes).hexdigest() != receipt_sha256:
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim cannot reconstruct its receipt digest",
        )
    _sha256(
        claim.get("classification_event_sha256"),
        label="classification claim.classification_event_sha256",
    )
    _sha256(
        claim.get("admission_claim_digest"),
        label="classification claim.admission_claim_digest",
    )
    _consumption_identity(
        campaign_run_id=claim.get("campaign_run_id"),
        manifest_sha256=claim.get("manifest_sha256"),
        run_relpath=claim.get("run_relpath"),
        cell_id=claim.get("cell_id"),
        attempt_id=claim.get("attempt_id"),
        slot=slot,
    )
    return claim, receipt_bytes


@dataclass(frozen=True, slots=True)
class _ClassificationResult:
    slot: profile8b.S8BAttemptSlot
    receipt_bytes: bytes
    receipt_sha256: str
    event_sha256: str
    reason: str | None
    claim: Mapping[str, Any]
    publish: bool


TransitionResultT = TypeVar("TransitionResultT")


def _atomic_update(
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    transition: Callable[
        [core.RegistryRows], tuple[core.RegistryRows, TransitionResultT]
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]:
    # This read is a concurrency-test rendezvous only.  The authoritative read
    # is repeated under the root lock below.
    snapshot = _read_regular_bytes(path)
    assert snapshot is not None
    snapshot_hook = _PRELOCK_SNAPSHOT_HOOK
    if snapshot_hook is not None:
        snapshot_hook(snapshot)

    with admission._locked(root):
        old_bytes = _read_regular_bytes(path)
        assert old_bytes is not None
        _fault("after-authoritative-read")
        rows = core.load_attempt_registry(
            old_bytes, profile=profile, expected_binding=binding,
        )
        _fault("after-replay")
        candidate, result = transition(rows)
        _fault("after-transition")
        candidate_bytes = _registry_bytes(candidate)
        validated = core.load_attempt_registry(
            candidate_bytes, profile=profile, expected_binding=binding,
        )
        _fault("after-candidate-validation")
        if candidate_bytes == old_bytes:
            return validated, result
        if not candidate_bytes.startswith(old_bytes):
            _fail(
                "s8b-attempt-registry-append-only",
                "candidate registry is not a strict extension",
            )
        if prepare is not None:
            prepare(result, candidate_bytes)

        staging: Path | None = None
        try:
            logical_name = PurePosixPath(*path.relative_to(root).parts).as_posix()
            staging = _write_staging(
                path, candidate_bytes, logical_name=logical_name,
            )
            _fault("after-staging-fsync")
            current = _read_regular_bytes(path)
            if current != old_bytes:
                _fail(
                    "s8b-attempt-registry-concurrency",
                    "authoritative registry changed under the root lock",
                )
            os.replace(staging, path)
            staging = None
            _fault("after-replace")
            _fsync_directory(path.parent)
            _fault("after-parent-fsync")
        finally:
            _unlink_staging(staging)
        return validated, result


def create_attempt_registry(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
    ],
    slots: Sequence[profile8b.S8BAttemptSlot],
    binding: profile8b.S8BAttemptBinding,
    requested_registry_path: Path | None = None,
) -> Path:
    """Create exactly one genesis at the canonical shared-root path."""

    profile = _assert_profile(profile)
    if type(binding) is not profile8b.S8BAttemptBinding:
        _fail("s8b-attempt-registry-profile", "8b binding type differs")
    root, path = _entry_paths(
        Path(repo_root),
        freeze_sha256=binding.freeze_sha256,
        requested_registry_path=requested_registry_path,
    )
    rows = core.create_attempt_registry_genesis(
        profile=profile, slots=slots, binding=binding,
    )
    payload = _registry_bytes(rows)
    core.load_attempt_registry(
        payload, profile=profile, expected_binding=binding,
    )
    logical_name = _relative_registry_path(binding.freeze_sha256).as_posix()
    with admission._locked(root):
        _publish_create_only(
            path, payload, logical_name=logical_name, allow_exact_retry=False,
        )
    return path


def read_attempt_registry(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
    ],
    binding: profile8b.S8BAttemptBinding,
) -> core.RegistryRows:
    """Read and replay one authoritative registry without changing its rows."""

    profile = _assert_profile(profile)
    canonical_repo_root = Path(repo_root).resolve()
    root, path = _entry_paths(
        canonical_repo_root, freeze_sha256=binding.freeze_sha256,
    )
    with admission._locked(root):
        payload = _read_regular_bytes(path)
        assert payload is not None
        return core.load_attempt_registry(
            payload, profile=profile, expected_binding=binding,
        )


def reserve_attempt_slot(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
    ],
    binding: profile8b.S8BAttemptBinding,
    slot_id: profile8b.S8BSlotIdentity,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    admission_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    deferred_output_reader: Callable[[], bytes],
) -> ReservedAttempt:
    """Persist reservation and return the only handle accepted by classify."""

    profile = _assert_profile(profile)
    _sha256(admission_claim_digest, label="admission_claim_digest")
    (
        campaign_run_id,
        manifest_sha256,
        run_relpath,
        cell_id,
        attempt_id,
    ) = _consumption_identity(
        campaign_run_id=campaign_run_id,
        manifest_sha256=manifest_sha256,
        run_relpath=run_relpath,
        cell_id=cell_id,
        attempt_id=attempt_id,
    )
    if not callable(deferred_output_reader):
        _fail("s8b-attempt-registry-handle", "deferred output reader is not callable")
    canonical_repo_root = Path(repo_root).resolve()
    root, path = _entry_paths(
        canonical_repo_root, freeze_sha256=binding.freeze_sha256,
    )

    def transition(
        rows: core.RegistryRows,
    ) -> tuple[core.RegistryRows, tuple[profile8b.S8BAttemptSlot, str]]:
        slot = _slot_from_rows(rows, profile=profile, slot_id=slot_id)
        _consumption_identity(
            campaign_run_id=campaign_run_id,
            manifest_sha256=manifest_sha256,
            run_relpath=run_relpath,
            cell_id=cell_id,
            attempt_id=attempt_id,
            slot=slot,
        )
        capability = core.capability_digest(
            profile=profile,
            schema_version=profile.schema.current,
            freeze_id=binding.freeze_sha256,
            slot=slot,
            binding=binding,
        )
        candidate = core.reserve_attempt_slot(
            rows,
            profile=profile,
            freeze_id=binding.freeze_sha256,
            slot_id=slot_id,
            binding=binding,
            run_start_receipt_sha256=run_start_receipt_sha256,
            process_identity=process_identity,
            started_at=started_at,
        )
        return candidate, (slot, capability)

    _rows, (_slot, _capability) = _atomic_update(
        root=root,
        path=path,
        profile=profile,
        binding=binding,
        transition=transition,
    )
    state = _AttemptState(
        repo_root=canonical_repo_root,
        profile=profile,
        binding=binding,
        freeze_id=binding.freeze_sha256,
        slot_id=slot_id,
        registry_path=path,
        admission_claim_digest=admission_claim_digest,
        attempt_id=attempt_id,
        campaign_run_id=campaign_run_id,
        manifest_sha256=manifest_sha256,
        run_relpath=run_relpath,
        cell_id=cell_id,
        deferred_output_reader=deferred_output_reader,
    )
    return _new_handle(ReservedAttempt, state)


def _assert_classification_artifacts(
    *,
    root: Path,
    rows: Sequence[Mapping[str, Any]],
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    slot_id: profile8b.S8BSlotIdentity,
    admission_claim_digest: str | None = None,
    attempt_id: str | None = None,
    expected_receipt_bytes: bytes | None = None,
    desired_fields: Mapping[str, Any] | None = None,
) -> tuple[profile8b.S8BAttemptSlot, Mapping[str, Any], bytes, Mapping[str, Any]]:
    slot = _slot_from_rows(rows, profile=profile, slot_id=slot_id)
    classifications = _rows_for_event(rows, slot=slot, event="classification")
    if len(classifications) != 1:
        _fail(
            "s8b-attempt-registry-classification",
            "slot does not have exactly one classification row",
        )
    classification = classifications[0]
    claim_result = _classification_claim(
        root=root, binding=binding, slot=slot,
    )
    assert claim_result is not None
    claim, claim_receipt_bytes = claim_result
    expected_claim_identity = {
        "classification_receipt_sha256": classification[
            "classification_receipt_sha256"
        ],
        "classification_event_sha256": classification["event_sha256"],
    }
    for field, expected in expected_claim_identity.items():
        if claim.get(field) != expected:
            _fail(
                "s8b-attempt-registry-classification",
                f"classification claim differs: {field}",
            )
    if (
        admission_claim_digest is not None
        and claim.get("admission_claim_digest") != admission_claim_digest
    ):
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim admission identity differs",
        )
    if attempt_id is not None and claim.get("attempt_id") != attempt_id:
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim attempt identity differs",
        )
    receipt_path = _receipt_path(
        root, str(classification["classification_receipt_sha256"]),
    )
    receipt_bytes = _read_regular_bytes(receipt_path)
    assert receipt_bytes is not None
    if hashlib.sha256(receipt_bytes).hexdigest() != receipt_path.stem:
        _fail(
            "s8b-attempt-registry-classification",
            "stored classification receipt digest differs",
        )
    if receipt_bytes != claim_receipt_bytes:
        _fail(
            "s8b-attempt-registry-classification",
            "stored classification receipt differs from slot claim",
        )
    if expected_receipt_bytes is not None and receipt_bytes != expected_receipt_bytes:
        _fail(
            "s8b-attempt-registry-classification",
            "stored classification receipt bytes differ from handle",
        )
    receipt = _canonical_document(receipt_bytes, label="classification receipt")
    if desired_fields is not None:
        for field, expected in desired_fields.items():
            if receipt.get(field) != expected:
                _fail(
                    "s8b-attempt-registry-classification",
                    f"classification exact retry differs: {field}",
                )
    return slot, classification, receipt_bytes, claim


def classify_attempt(
    reserved: ReservedAttempt,
    *,
    pre_observation_failure_reason: str | None,
    authority_id: str,
    authority_policy_sha256: str,
    external_evidence_sha256: str,
    classified_at: str,
) -> ClassifiedAttempt | ClassifiedFailure:
    """Publish slot claim, receipt, and row before issuing a classified handle."""

    state = _require_handle(reserved, ReservedAttempt)
    root, path = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )
    desired_fields = {
        "capability_digest_sha256": None,
        "pre_observation_failure_reason": pre_observation_failure_reason,
        "authority_id": authority_id,
        "authority_policy_sha256": authority_policy_sha256,
        "external_evidence_sha256": external_evidence_sha256,
        "classified_at": classified_at,
    }

    def transition(
        rows: core.RegistryRows,
    ) -> tuple[core.RegistryRows, _ClassificationResult]:
        slot = _slot_from_rows(rows, profile=state.profile, slot_id=state.slot_id)
        capability = core.capability_digest(
            profile=state.profile,
            schema_version=state.profile.schema.current,
            freeze_id=state.freeze_id,
            slot=slot,
            binding=state.binding,
        )
        desired_fields["capability_digest_sha256"] = capability
        existing = _rows_for_event(rows, slot=slot, event="classification")
        if existing:
            if any(
                _rows_for_event(rows, slot=slot, event=event)
                for event in ("observation-start", "terminal", "recovery")
            ):
                _fail(
                    "s8b-attempt-registry-classification",
                    "classification exact retry is no longer the durable phase",
                )
            (
                _slot,
                classification,
                receipt_bytes,
                claim,
            ) = _assert_classification_artifacts(
                root=root,
                rows=rows,
                profile=state.profile,
                binding=state.binding,
                slot_id=state.slot_id,
                admission_claim_digest=state.admission_claim_digest,
                attempt_id=state.attempt_id,
                desired_fields=desired_fields,
            )
            receipt = _canonical_document(
                receipt_bytes, label="classification receipt",
            )
            return rows, _ClassificationResult(
                slot=slot,
                receipt_bytes=receipt_bytes,
                receipt_sha256=str(classification["classification_receipt_sha256"]),
                event_sha256=str(classification["event_sha256"]),
                reason=receipt.get("pre_observation_failure_reason"),
                claim=claim,
                publish=False,
            )
        candidate, receipt = core.classify_attempt(
            rows,
            profile=state.profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
            binding=state.binding,
            capability_digest_sha256=capability,
            pre_observation_failure_reason=pre_observation_failure_reason,
            authority_id=authority_id,
            authority_policy_sha256=authority_policy_sha256,
            external_evidence_sha256=external_evidence_sha256,
            classified_at=classified_at,
        )
        receipt_bytes = _canonical_line_bytes(receipt)
        receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
        classification = candidate[-1]
        claim = _claim_document(
            freeze_sha256=state.freeze_id,
            slot=slot,
            classification_receipt=receipt,
            classification_receipt_sha256=receipt_sha256,
            classification_event_sha256=str(classification["event_sha256"]),
            admission_claim_digest=state.admission_claim_digest,
            attempt_id=state.attempt_id,
            campaign_run_id=state.campaign_run_id,
            manifest_sha256=state.manifest_sha256,
            run_relpath=state.run_relpath,
            cell_id=state.cell_id,
        )
        return candidate, _ClassificationResult(
            slot=slot,
            receipt_bytes=receipt_bytes,
            receipt_sha256=receipt_sha256,
            event_sha256=str(classification["event_sha256"]),
            reason=pre_observation_failure_reason,
            claim=claim,
            publish=True,
        )

    def prepare(result: _ClassificationResult, candidate_bytes: bytes) -> None:
        if not result.publish:
            return
        claim_path = _classification_claim_path(
            root, freeze_sha256=state.freeze_id, slot=result.slot,
        )
        claim_bytes = _canonical_line_bytes(result.claim)
        receipt_path = _receipt_path(root, result.receipt_sha256)
        claim_name = PurePosixPath(
            *claim_path.relative_to(root).parts
        ).as_posix()
        receipt_name = PurePosixPath(
            *receipt_path.relative_to(root).parts
        ).as_posix()
        registry_name = PurePosixPath(
            *path.relative_to(root).parts
        ).as_posix()
        for logical_name, payload in (
            (claim_name, claim_bytes),
            (receipt_name, result.receipt_bytes),
            (registry_name, candidate_bytes),
        ):
            admission.assert_holdout_safe_bytes(logical_name, payload)
        _publish_create_only(
            claim_path,
            claim_bytes,
            logical_name=claim_name,
            allow_exact_retry=True,
        )
        _fault("after-classification-claim")
        _publish_create_only(
            receipt_path,
            result.receipt_bytes,
            logical_name=receipt_name,
            allow_exact_retry=True,
        )
        _fault("after-classification-receipt")

    _rows, result = _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
        prepare=prepare,
    )
    classified_state = replace(
        state,
        classification_receipt_bytes=result.receipt_bytes,
        classification_receipt_sha256=result.receipt_sha256,
        classification_event_sha256=result.event_sha256,
    )
    if result.reason is None:
        return _new_handle(ClassifiedAttempt, classified_state)
    return _new_handle(ClassifiedFailure, classified_state)


def _marker_path(root: Path, *, claim_digest: str, attempt_id: str) -> Path:
    marker_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
    return root / "consumed" / f"{claim_digest}-{marker_digest}.json"


def _assert_consumed_marker(
    root: Path,
    *,
    state: _AttemptState,
    slot: profile8b.S8BAttemptSlot,
) -> Mapping[str, Any]:
    path = _marker_path(
        root,
        claim_digest=state.admission_claim_digest,
        attempt_id=state.attempt_id,
    )
    raw = _read_regular_bytes(path)
    assert raw is not None
    marker = _canonical_document(raw, label="consumed marker")
    if frozenset(marker) != _FLOOR_CONSUMED_MARKER_KEYS:
        _fail(
            "s8b-attempt-registry-consume",
            "consumed marker exact keys differ",
        )
    expected = {
        "schema_version": _FLOOR_CONSUMED_MARKER_SCHEMA,
        "event": "consume",
        "claim_digest": state.admission_claim_digest,
        "attempt_id": state.attempt_id,
        "campaign_run_id": state.campaign_run_id,
        "manifest_sha256": state.manifest_sha256,
        "run_relpath": state.run_relpath,
        "cell_id": state.cell_id,
        "freeze_holdout_key": slot.freeze_holdout_key,
        "configuration_id": slot.configuration_id,
        "observation_role": admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }
    for field, value in expected.items():
        if marker.get(field) != value:
            _fail(
                "s8b-attempt-registry-consume",
                f"consumed marker differs: {field}",
            )
    _consumption_identity(
        campaign_run_id=state.campaign_run_id,
        manifest_sha256=state.manifest_sha256,
        run_relpath=state.run_relpath,
        cell_id=state.cell_id,
        attempt_id=state.attempt_id,
        slot=slot,
    )
    return marker


def _captured_state(state: _AttemptState, raw_output: object) -> _AttemptState:
    if type(raw_output) is not bytes:
        _fail("s8b-attempt-registry-output", "deferred reader did not return bytes")
    return replace(
        state,
        raw_output_sha256=hashlib.sha256(raw_output).hexdigest(),
    )


def begin_attempt_observation(
    classified: ClassifiedAttempt,
) -> CapturedObservation:
    """Persist observation-start, then and only then invoke the deferred reader."""

    state = _require_handle(classified, ClassifiedAttempt)
    root, path = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )

    def transition(
        rows: core.RegistryRows,
    ) -> tuple[core.RegistryRows, str]:
        slot, classification, _receipt, _claim = _assert_classification_artifacts(
            root=root,
            rows=rows,
            profile=state.profile,
            binding=state.binding,
            slot_id=state.slot_id,
            admission_claim_digest=state.admission_claim_digest,
            attempt_id=state.attempt_id,
            expected_receipt_bytes=state.classification_receipt_bytes,
        )
        _assert_consumed_marker(root, state=state, slot=slot)
        candidate = core.begin_attempt_observation(
            rows,
            profile=state.profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
        )
        observation = candidate[-1]
        if observation.get("classification_event_sha256") != classification.get(
            "event_sha256"
        ):
            _fail(
                "s8b-attempt-registry-observation",
                "observation classification binding differs",
            )
        return candidate, str(observation["event_sha256"])

    _rows, observation_sha256 = _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
    )
    observed_state = replace(
        state, observation_event_sha256=observation_sha256,
    )
    captured = _captured_state(
        observed_state, state.deferred_output_reader(),
    )
    return _new_handle(CapturedObservation, captured)


def _assert_observation_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    state: _AttemptState,
    slot: profile8b.S8BAttemptSlot,
) -> Mapping[str, Any]:
    observations = _rows_for_event(rows, slot=slot, event="observation-start")
    if len(observations) != 1:
        _fail(
            "s8b-attempt-registry-observation",
            "slot does not have exactly one observation-start row",
        )
    observation = observations[0]
    if (
        state.observation_event_sha256 is not None
        and observation.get("event_sha256") != state.observation_event_sha256
    ):
        _fail(
            "s8b-attempt-registry-observation",
            "observation-start differs from handle",
        )
    return observation


def record_attempt_terminal(
    observation: CapturedObservation,
    *,
    terminal_status: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
) -> None:
    """Record a terminal row; the raw-output digest comes only from the handle."""

    state = _require_handle(observation, CapturedObservation)
    if state.raw_output_sha256 is None:
        _fail("s8b-attempt-registry-handle", "captured output digest is absent")
    root, path = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )

    def transition(rows: core.RegistryRows) -> tuple[core.RegistryRows, None]:
        slot, _classification, _receipt, _claim = _assert_classification_artifacts(
            root=root,
            rows=rows,
            profile=state.profile,
            binding=state.binding,
            slot_id=state.slot_id,
            admission_claim_digest=state.admission_claim_digest,
            attempt_id=state.attempt_id,
            expected_receipt_bytes=state.classification_receipt_bytes,
        )
        _assert_observation_row(rows, state=state, slot=slot)
        candidate = core.record_attempt_terminal(
            rows,
            profile=state.profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
            binding=state.binding,
            terminal_status=terminal_status,
            raw_output_sha256=state.raw_output_sha256,
            report_sha256=report_sha256,
            observation_sha256=observation_sha256,
            primary_value=primary_value,
            finished_at=finished_at,
            failure_reason=None,
        )
        return candidate, None

    _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
    )


def record_classified_failure_terminal(
    failure: ClassifiedFailure,
    *,
    terminal_status: str,
    report_sha256: str | None,
    finished_at: str,
) -> None:
    """Close a classified pre-observation failure without an observation union."""

    state = _require_handle(failure, ClassifiedFailure)
    root, path = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )

    def transition(rows: core.RegistryRows) -> tuple[core.RegistryRows, None]:
        _assert_classification_artifacts(
            root=root,
            rows=rows,
            profile=state.profile,
            binding=state.binding,
            slot_id=state.slot_id,
            admission_claim_digest=state.admission_claim_digest,
            attempt_id=state.attempt_id,
            expected_receipt_bytes=state.classification_receipt_bytes,
        )
        candidate = core.record_attempt_terminal(
            rows,
            profile=state.profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
            binding=state.binding,
            terminal_status=terminal_status,
            raw_output_sha256=_ZERO_OUTPUT_SHA256,
            report_sha256=report_sha256,
            observation_sha256=None,
            primary_value=None,
            finished_at=finished_at,
            failure_reason=None,
        )
        return candidate, None

    _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
    )


def record_attempt_recovery(
    reserved: ReservedAttempt,
    *,
    scheduler_accounting_receipt: bytes,
    recoverer_process_identity: Mapping[str, Any],
    recovered_at: str,
) -> None:
    """Persist recovery from canonical receipt bytes without reinterpreting reason."""

    state = _require_handle(reserved, ReservedAttempt)
    receipt = _canonical_document(
        scheduler_accounting_receipt,
        label="scheduler accounting receipt",
    )
    root, path = _entry_paths(
        state.repo_root, freeze_sha256=state.freeze_id,
    )

    def transition(rows: core.RegistryRows) -> tuple[core.RegistryRows, None]:
        candidate = core.record_attempt_recovery(
            rows,
            profile=state.profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
            binding=state.binding,
            scheduler_accounting_receipt=receipt,
            recoverer_process_identity=recoverer_process_identity,
            recovered_at=recovered_at,
        )
        return candidate, None

    _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
    )


def resume_attempt(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot, profile8b.S8BAttemptBinding
    ],
    binding: profile8b.S8BAttemptBinding,
    slot_id: profile8b.S8BSlotIdentity,
    deferred_output_reader: Callable[[], bytes],
    admission_claim_digest: str | None = None,
    attempt_id: str | None = None,
    campaign_run_id: str | None = None,
    manifest_sha256: str | None = None,
    run_relpath: str | None = None,
    cell_id: str | None = None,
) -> (
    ReservedAttempt
    | ClassifiedAttempt
    | ClassifiedFailure
    | CapturedObservation
):
    """Rehydrate or finish the exact durable phase after process loss.

    A start-only phase needs the complete admission and campaign identity
    because the core start/seal rows deliberately do not claim consumption. Once a
    slot claim exists, its self-contained receipt is authoritative and the
    exact classification row may be completed from it.
    """

    profile = _assert_profile(profile)
    if not callable(deferred_output_reader):
        _fail("s8b-attempt-registry-handle", "deferred output reader is not callable")
    if admission_claim_digest is not None:
        _sha256(admission_claim_digest, label="admission_claim_digest")
    if attempt_id is not None:
        _text(attempt_id, label="attempt_id")
    supplied_consumption_identity = (
        campaign_run_id,
        manifest_sha256,
        run_relpath,
        cell_id,
    )
    requested_consumption_identity: (
        tuple[str, str, str, str, str] | None
    ) = None
    if any(value is not None for value in supplied_consumption_identity):
        if (
            any(value is None for value in supplied_consumption_identity)
            or attempt_id is None
        ):
            _fail(
                "s8b-attempt-registry-resume",
                "resume consumption identity is incomplete",
            )
        requested_consumption_identity = _consumption_identity(
            campaign_run_id=campaign_run_id,
            manifest_sha256=manifest_sha256,
            run_relpath=run_relpath,
            cell_id=cell_id,
            attempt_id=attempt_id,
        )
    canonical_repo_root = Path(repo_root).resolve()
    root, path = _entry_paths(
        canonical_repo_root, freeze_sha256=binding.freeze_sha256,
    )
    pending_observation: _AttemptState | None = None
    pending_classification: tuple[ReservedAttempt, Mapping[str, Any]] | None = None
    resumed_handle: (
        ReservedAttempt | ClassifiedAttempt | ClassifiedFailure | None
    ) = None
    with admission._locked(root):
        payload = _read_regular_bytes(path)
        assert payload is not None
        rows = core.load_attempt_registry(
            payload, profile=profile, expected_binding=binding,
        )
        slot = _slot_from_rows(rows, profile=profile, slot_id=slot_id)
        if _rows_for_event(rows, slot=slot, event="terminal"):
            _fail("s8b-attempt-registry-resume", "terminal slot cannot resume")
        if _rows_for_event(rows, slot=slot, event="recovery"):
            _fail("s8b-attempt-registry-resume", "recovered slot cannot resume")
        starts = _rows_for_event(rows, slot=slot, event="start")
        seals = _rows_for_event(rows, slot=slot, event="pre-observation-seal")
        if len(starts) != 1 or len(seals) != 1:
            _fail(
                "s8b-attempt-registry-resume",
                "slot does not have exactly one durable start and seal",
            )
        classifications = _rows_for_event(
            rows, slot=slot, event="classification",
        )
        if len(classifications) > 1:
            _fail(
                "s8b-attempt-registry-resume",
                "slot has multiple classification rows",
            )
        claim_result = _classification_claim(
            root=root, binding=binding, slot=slot, missing_ok=True,
        )
        if not classifications:
            if claim_result is None:
                if (
                    admission_claim_digest is None
                    or requested_consumption_identity is None
                ):
                    _fail(
                        "s8b-attempt-registry-resume",
                        "start-only resume requires complete admission identities",
                    )
                (
                    resumed_campaign_run_id,
                    resumed_manifest_sha256,
                    resumed_run_relpath,
                    resumed_cell_id,
                    resumed_attempt_id,
                ) = _consumption_identity(
                    campaign_run_id=requested_consumption_identity[0],
                    manifest_sha256=requested_consumption_identity[1],
                    run_relpath=requested_consumption_identity[2],
                    cell_id=requested_consumption_identity[3],
                    attempt_id=requested_consumption_identity[4],
                    slot=slot,
                )
                state = _AttemptState(
                    repo_root=canonical_repo_root,
                    profile=profile,
                    binding=binding,
                    freeze_id=binding.freeze_sha256,
                    slot_id=slot_id,
                    registry_path=path,
                    admission_claim_digest=admission_claim_digest,
                    attempt_id=resumed_attempt_id,
                    campaign_run_id=resumed_campaign_run_id,
                    manifest_sha256=resumed_manifest_sha256,
                    run_relpath=resumed_run_relpath,
                    cell_id=resumed_cell_id,
                    deferred_output_reader=deferred_output_reader,
                )
                resumed_handle = _new_handle(ReservedAttempt, state)
            else:
                claim, receipt_bytes = claim_result
                claim_admission_digest = _sha256(
                    claim.get("admission_claim_digest"),
                    label="classification claim.admission_claim_digest",
                )
                claim_attempt_id = _text(
                    claim.get("attempt_id"),
                    label="classification claim.attempt_id",
                )
                claim_consumption_identity = _consumption_identity(
                    campaign_run_id=claim.get("campaign_run_id"),
                    manifest_sha256=claim.get("manifest_sha256"),
                    run_relpath=claim.get("run_relpath"),
                    cell_id=claim.get("cell_id"),
                    attempt_id=claim_attempt_id,
                    slot=slot,
                )
                if (
                    admission_claim_digest is not None
                    and admission_claim_digest != claim_admission_digest
                ):
                    _fail(
                        "s8b-attempt-registry-resume",
                        "resume admission claim differs from slot claim",
                    )
                if attempt_id is not None and attempt_id != claim_attempt_id:
                    _fail(
                        "s8b-attempt-registry-resume",
                        "resume attempt identity differs from slot claim",
                    )
                if (
                    requested_consumption_identity is not None
                    and requested_consumption_identity
                    != claim_consumption_identity
                ):
                    _fail(
                        "s8b-attempt-registry-resume",
                        "resume campaign/run/cell identity differs from slot claim",
                    )
                receipt = _canonical_document(
                    receipt_bytes, label="classification receipt",
                )
                state = _AttemptState(
                    repo_root=canonical_repo_root,
                    profile=profile,
                    binding=binding,
                    freeze_id=binding.freeze_sha256,
                    slot_id=slot_id,
                    registry_path=path,
                    admission_claim_digest=claim_admission_digest,
                    attempt_id=claim_attempt_id,
                    campaign_run_id=claim_consumption_identity[0],
                    manifest_sha256=claim_consumption_identity[1],
                    run_relpath=claim_consumption_identity[2],
                    cell_id=claim_consumption_identity[3],
                    deferred_output_reader=deferred_output_reader,
                )
                pending_classification = (
                    _new_handle(ReservedAttempt, state), receipt,
                )
            observations = _rows_for_event(
                rows, slot=slot, event="observation-start",
            )
            if observations:
                _fail(
                    "s8b-attempt-registry-resume",
                    "observation exists without classification",
                )
        else:
            slot, classification, receipt_bytes, claim = (
                _assert_classification_artifacts(
                    root=root,
                    rows=rows,
                    profile=profile,
                    binding=binding,
                    slot_id=slot_id,
                    admission_claim_digest=admission_claim_digest,
                    attempt_id=attempt_id,
                )
            )
            receipt = _canonical_document(
                receipt_bytes, label="classification receipt",
            )
            claim_consumption_identity = _consumption_identity(
                campaign_run_id=claim.get("campaign_run_id"),
                manifest_sha256=claim.get("manifest_sha256"),
                run_relpath=claim.get("run_relpath"),
                cell_id=claim.get("cell_id"),
                attempt_id=claim.get("attempt_id"),
                slot=slot,
            )
            if (
                requested_consumption_identity is not None
                and requested_consumption_identity
                != claim_consumption_identity
            ):
                _fail(
                    "s8b-attempt-registry-resume",
                    "resume campaign/run/cell identity differs from slot claim",
                )
            state = _AttemptState(
                repo_root=canonical_repo_root,
                profile=profile,
                binding=binding,
                freeze_id=binding.freeze_sha256,
                slot_id=slot_id,
                registry_path=path,
                admission_claim_digest=_sha256(
                    claim.get("admission_claim_digest"),
                    label="classification claim.admission_claim_digest",
                ),
                attempt_id=_text(
                    claim.get("attempt_id"),
                    label="classification claim.attempt_id",
                ),
                campaign_run_id=claim_consumption_identity[0],
                manifest_sha256=claim_consumption_identity[1],
                run_relpath=claim_consumption_identity[2],
                cell_id=claim_consumption_identity[3],
                deferred_output_reader=deferred_output_reader,
                classification_receipt_bytes=receipt_bytes,
                classification_receipt_sha256=str(
                    classification["classification_receipt_sha256"]
                ),
                classification_event_sha256=str(
                    classification["event_sha256"]
                ),
            )
            observations = _rows_for_event(
                rows, slot=slot, event="observation-start",
            )
            if len(observations) > 1:
                _fail(
                    "s8b-attempt-registry-resume",
                    "slot has multiple observation-start rows",
                )
            if observations:
                _assert_consumed_marker(root, state=state, slot=slot)
                pending_observation = replace(
                    state,
                    observation_event_sha256=str(
                        observations[0]["event_sha256"]
                    ),
                )
            elif receipt.get("pre_observation_failure_reason") is None:
                resumed_handle = _new_handle(ClassifiedAttempt, state)
            else:
                resumed_handle = _new_handle(ClassifiedFailure, state)
    if pending_classification is not None:
        reserved, receipt = pending_classification
        return classify_attempt(
            reserved,
            pre_observation_failure_reason=receipt.get(
                "pre_observation_failure_reason"
            ),
            authority_id=receipt.get("authority_id"),
            authority_policy_sha256=receipt.get("authority_policy_sha256"),
            external_evidence_sha256=receipt.get("external_evidence_sha256"),
            classified_at=receipt.get("classified_at"),
        )
    if pending_observation is not None:
        captured = _captured_state(
            pending_observation, deferred_output_reader(),
        )
        return _new_handle(CapturedObservation, captured)
    assert resumed_handle is not None
    return resumed_handle
