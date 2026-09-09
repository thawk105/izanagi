# -*- coding: utf-8 -*-
"""File-backed 8b attempt-registry adapter for the trusted floor launcher.

The sole connection owner is :mod:`s8b_floor_attempt_launcher`, which keeps the
captured output token away from the floor campaign and opens it only after this
adapter has durably published the classification claim, receipt, and row.  The
floor campaign and holdout admission deliberately do not import this adapter
directly.  A scheduler-accounting collector now exists, while recovery still
requires the adapter's pinned receipt checks and currently configured policy.

The existing adapter-disconnection meta-test only inspects direct AST imports
in the campaign and admission modules.  It therefore still passes with the
launcher indirection and is not proof that production cannot reach this
adapter.  Ordering assurance comes from the launcher's capability ownership
together with the guarded publication and typed phase handles implemented
here.
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
from . import s8b_scheduler_accounting as scheduler_accounting
from . import s8b_terminal_evidence as terminal_evidence


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
_CLASSIFICATION_CLAIM_V3_SCHEMA = "s8b-attempt-classification-claim/v3"
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
_TERMINAL_EVIDENCE_ISSUER_TOKEN = object()
_LAUNCHER_ORIGIN_ISSUER_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class _LauncherOriginCapability:
    """Private proof that a reservation came from the certified wrapper."""

    _seal: object


def _new_launcher_origin_capability() -> _LauncherOriginCapability:
    capability = object.__new__(_LauncherOriginCapability)
    object.__setattr__(
        capability, "_seal", _LAUNCHER_ORIGIN_ISSUER_TOKEN,
    )
    return capability


def _require_launcher_origin_capability(
    value: object,
) -> _LauncherOriginCapability:
    if (
        type(value) is not _LauncherOriginCapability
        or value._seal is not _LAUNCHER_ORIGIN_ISSUER_TOKEN
    ):
        _fail(
            "s8b-launcher-origin",
            "sealed terminal requires a certified launcher origin",
        )
    return value

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
    profile: core.DomainProfile[Any, profile8b.S8BAttemptBinding]
    binding: profile8b.S8BAttemptBinding
    freeze_id: str
    slot_id: Hashable
    registry_path: Path
    admission_claim_digest: str
    attempt_id: str
    campaign_run_id: str
    manifest_sha256: str
    run_relpath: str
    cell_id: str
    deferred_output_reader: Callable[[], bytes]
    launcher_origin_capability: _LauncherOriginCapability | None = None
    consumption_marker: admission.FloorAttemptConsumptionMarker | None = None
    measurement_generation_claim_digest: str | None = None
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
        id(state.launcher_origin_capability),
        id(state.consumption_marker),
        state.measurement_generation_claim_digest,
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


def _assert_exact_profile(
    profile: core.DomainProfile[Any, Any],
    expected: core.DomainProfile[Any, Any],
) -> None:
    """Apply the legacy exact comparator to one schema-selected profile."""

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
        or type(profile.retryable_reason_field) is not str
        or profile.retryable_reason_field != expected.retryable_reason_field
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
        or type(transition.retryable_terminal_opens_next_attempt) is not bool
        or transition.retryable_terminal_opens_next_attempt
        is not expected_transition.retryable_terminal_opens_next_attempt
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
        or profile.terminal_row_validator is not expected.terminal_row_validator
    ):
        _fail(
            "s8b-attempt-registry-profile",
            "domain profile differs from frozen 8b semantics",
        )


def _assert_profile(
    profile: core.DomainProfile[Any, Any],
) -> core.DomainProfile[Any, profile8b.S8BAttemptBinding]:
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
    factory: Callable[..., core.DomainProfile[Any, Any]]
    if profile.schema is profile8b.S8B_SCHEMA_PROFILE:
        factory = profile8b.make_s8b_domain_profile
    elif profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
        factory = profile8b.make_s8b_v2_domain_profile
    else:
        _fail(
            "s8b-attempt-registry-profile",
            "domain profile schema is not a frozen 8b schema",
        )
    try:
        expected = factory(
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
    _assert_exact_profile(profile, expected)
    return profile


def _profile_protocol_sha256(
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
) -> str | None:
    if profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
        return binding.protocol_sha256
    return None


def _relative_registry_path(
    freeze_sha256: str,
    protocol_sha256: str | None = None,
) -> PurePosixPath:
    freeze_sha256 = _sha256(freeze_sha256, label="freeze_sha256")
    context = {"freeze_sha256": freeze_sha256}
    if protocol_sha256 is None:
        template = profile8b.S8B_REGISTRY_LAYOUT.registry_path
    else:
        protocol_sha256 = _sha256(
            protocol_sha256, label="protocol_sha256",
        )
        context["protocol_sha256"] = protocol_sha256
        template = profile8b.S8B_V2_REGISTRY_LAYOUT.registry_path
    rendered = PurePosixPath(
        template.as_posix().format_map(context)
    )
    if rendered.is_absolute() or ".." in rendered.parts:
        _fail("s8b-attempt-registry-path", "registry layout is not relative")
    return rendered


def _entry_paths(
    repo_root: Path,
    *,
    freeze_sha256: str,
    protocol_sha256: str | None = None,
    requested_registry_path: Path | None = None,
) -> tuple[Path, Path]:
    # Provisioning is part of every adapter entry.  In particular, it creates
    # the lock inode before the private shared lock is opened.
    root = admission.provision_shared_admission_root(Path(repo_root))
    _fsync_shared_root_chain(root)
    relative = _relative_registry_path(
        freeze_sha256, protocol_sha256=protocol_sha256,
    )
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


def registry_path(
    repo_root: Path,
    *,
    freeze_sha256: str,
    protocol_sha256: str | None = None,
) -> Path:
    """Return the canonical path for one freeze and optional generation."""

    _root, path = _entry_paths(
        Path(repo_root),
        freeze_sha256=freeze_sha256,
        protocol_sha256=protocol_sha256,
    )
    return path


def _assert_state_path(state: _AttemptState) -> None:
    if type(state.binding) is not profile8b.S8BAttemptBinding:
        _fail("s8b-attempt-registry-handle", "handle binding type differs")
    _assert_profile(state.profile)
    if not state.repo_root.is_absolute() or state.repo_root != state.repo_root.resolve():
        _fail("s8b-attempt-registry-handle", "handle repo root is not canonical")
    _root, canonical = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
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


def _peek_registry_genesis(data: bytes) -> Mapping[str, Any]:
    first_line, separator, _remainder = data.partition(b"\n")
    if not separator or not first_line:
        _fail(
            "s8b-attempt-registry-canonical",
            "attempt registry genesis is not newline terminated",
        )
    return _canonical_document(
        first_line + b"\n", label="attempt registry genesis",
    )


def _registry_generation_paths_locked(
    root: Path,
    freeze_sha256: str,
) -> tuple[Path, ...]:
    freeze_sha256 = _sha256(freeze_sha256, label="freeze_sha256")
    freeze_directory = root / "floor-attempt-registries" / freeze_sha256
    admission._assert_no_symlink_components(freeze_directory.parent)
    try:
        freeze_stat = freeze_directory.lstat()
    except FileNotFoundError:
        _fail(
            "s8b-attempt-registry-storage",
            "freeze generation directory is absent",
        )
    except OSError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-storage] cannot inspect freeze generation directory"
        ) from exc
    if freeze_directory.is_symlink() or not stat.S_ISDIR(freeze_stat.st_mode):
        _fail(
            "s8b-attempt-registry-storage",
            "freeze generation directory is unsafe",
        )

    generations: list[Path] = []
    canonical = freeze_directory / "registry.jsonl"
    try:
        canonical.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-storage] cannot inspect registry.jsonl"
        ) from exc
    else:
        _read_regular_bytes(canonical)
        generations.append(canonical)

    try:
        siblings = sorted(freeze_directory.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-storage] cannot enumerate registry generations"
        ) from exc
    for sibling in siblings:
        name = sibling.name
        if len(name) != 64 or any(
            character not in "0123456789abcdef" for character in name
        ):
            continue
        try:
            sibling_stat = sibling.lstat()
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot inspect generation directory"
            ) from exc
        if sibling.is_symlink() or not stat.S_ISDIR(sibling_stat.st_mode):
            _fail(
                "s8b-attempt-registry-storage",
                "generation directory is unsafe or incomplete",
            )
        registry = sibling / "registry.jsonl"
        try:
            registry.lstat()
        except FileNotFoundError:
            _fail(
                "s8b-attempt-registry-storage",
                "generation directory is unsafe or incomplete",
            )
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot inspect generation registry"
            ) from exc
        _read_regular_bytes(registry)
        generations.append(registry)
    return tuple(generations)


def _profile_and_binding_for_generation(
    *,
    path: Path,
    genesis: Mapping[str, Any],
) -> tuple[
    core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    profile8b.S8BAttemptBinding,
]:
    try:
        binding = profile8b.S8B_BINDING_CODEC.parse(
            genesis, label="attempt registry genesis",
        )
        budget = genesis.get("max_consumptions_per_budget_key")
        schema_version = genesis.get("schema_version")
        canonical_relative = _relative_registry_path(binding.freeze_sha256)
        generation_relative = _relative_registry_path(
            binding.freeze_sha256,
            protocol_sha256=binding.protocol_sha256,
        )
        root_path = genesis.get("root_path")
        if schema_version == profile8b.S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION:
            candidate = profile8b.make_s8b_domain_profile(
                max_consumptions_per_budget_key=budget,
                recovery_authority_id=scheduler_accounting.AUTHORITY_ID,
                recovery_authority_policy_sha256=(
                    scheduler_accounting.AUTHORITY_POLICY_SHA256
                ),
            )
            if root_path == canonical_relative.as_posix():
                relative = canonical_relative
            elif root_path == generation_relative.as_posix():
                relative = generation_relative
                candidate = replace(
                    candidate, layout=profile8b.S8B_V2_REGISTRY_LAYOUT,
                )
            else:
                _fail(
                    "s8b-attempt-registry-profile",
                    "generation profile is not reconstructible",
                )
        elif schema_version == profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION:
            candidate = profile8b.make_s8b_v2_domain_profile(
                max_consumptions_per_budget_key=budget,
                recovery_authority_id=scheduler_accounting.AUTHORITY_ID,
                recovery_authority_policy_sha256=(
                    scheduler_accounting.AUTHORITY_POLICY_SHA256
                ),
            )
            relative = generation_relative
            if root_path != relative.as_posix():
                _fail(
                    "s8b-attempt-registry-profile",
                    "generation profile is not reconstructible",
                )
        else:
            _fail(
                "s8b-attempt-registry-profile",
                "generation profile is not reconstructible",
            )
    except S8BAttemptRegistryError:
        raise
    except core.AttemptRegistryCoreError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-profile] generation profile is not reconstructible"
        ) from exc

    if tuple(path.parts[-len(relative.parts):]) != relative.parts:
        if relative == generation_relative:
            _fail(
                "s8b-attempt-registry-path",
                "generation protocol differs from genesis",
            )
        _fail(
            "s8b-attempt-registry-path",
            "canonical generation path differs from genesis",
        )
    expected_recovery_digest = core._recovery_policy_sha256(candidate)
    if genesis.get("recovery_policy_sha256") != expected_recovery_digest:
        _fail(
            "s8b-attempt-registry-profile",
            "generation recovery policy differs from current authority",
        )
    try:
        core.assert_registry_rows(
            (genesis,), profile=candidate, expected_binding=binding,
        )
    except core.AttemptRegistryCoreError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-profile] generation profile is not reconstructible"
        ) from exc
    return candidate, binding


def _attempt_registry_prefix_proof(
    *,
    binding: profile8b.S8BAttemptBinding,
    row_count: int,
    chain_head_sha256: str,
) -> dict[str, object]:
    try:
        if type(binding) is not profile8b.S8BAttemptBinding:
            _fail(
                "s8b-attempt-registry-prefix",
                "expected binding type differs",
            )
        if (
            profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION
            != core.ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA
        ):
            _fail(
                "s8b-attempt-registry-prefix",
                "proof and profile registry schemas differ",
            )
        return core.validate_attempt_registry_prefix_proof({
            "schema": core.ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA,
            "registry_schema": (
                core.ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA
            ),
            "freeze_sha256": binding.freeze_sha256,
            "protocol_sha256": binding.protocol_sha256,
            "schedule_sha256": binding.schedule_sha256,
            "row_count": row_count,
            "chain_head_sha256": chain_head_sha256,
        })
    except (core.AttemptRegistryCoreError, S8BAttemptRegistryError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc


def _replay_current_v2_attempt_registry(
    repo_root: Path,
    *,
    expected_binding: profile8b.S8BAttemptBinding,
) -> core.RegistryRows:
    """Read and replay only the expected v2 generation without mutation.

    Other generations' budget excess is not inspected here; that remains a
    writer barrier.  Deletion followed by recreation of the same ledger bytes
    is not detected (D1533).
    """

    try:
        if type(expected_binding) is not profile8b.S8BAttemptBinding:
            _fail(
                "s8b-attempt-registry-prefix",
                "expected binding type differs",
            )
        relative = _relative_registry_path(
            expected_binding.freeze_sha256,
            protocol_sha256=expected_binding.protocol_sha256,
        )
        _sha256(
            expected_binding.schedule_sha256,
            label="expected_binding.schedule_sha256",
        )
    except S8BAttemptRegistryError as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc

    try:
        root = admission.shared_admission_root(Path(repo_root))
        root_stat = root.lstat()
        if root.is_symlink() or not stat.S_ISDIR(root_stat.st_mode):
            raise admission.HoldoutAdmissionError(
                "attempt registry root is not a real directory"
            )
    except (admission.HoldoutAdmissionError, OSError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="unverifiable",
            reason="attempt-registry-root-unavailable",
        ) from exc

    path = root.joinpath(*relative.parts)
    try:
        with admission._locked_readonly(root):
            try:
                admission._assert_no_symlink_components(path)
                path_stat = path.lstat()
                if path.is_symlink() or not stat.S_ISREG(path_stat.st_mode):
                    raise admission.HoldoutAdmissionError(
                        "attempt registry path is not a regular file"
                    )
                payload = _read_regular_bytes(path)
                assert payload is not None
            except (
                admission.HoldoutAdmissionError,
                S8BAttemptRegistryError,
                OSError,
            ) as exc:
                raise admission.FloorHoldoutEvidenceError(
                    category="unverifiable",
                    reason="attempt-registry-read-unavailable",
                ) from exc
    except admission.FloorHoldoutEvidenceError as exc:
        if exc.reason == "attempt-registry-read-unavailable":
            raise
        raise admission.FloorHoldoutEvidenceError(
            category="unverifiable",
            reason="attempt-registry-root-unavailable",
        ) from exc
    except OSError as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="unverifiable",
            reason="attempt-registry-root-unavailable",
        ) from exc

    try:
        genesis = _peek_registry_genesis(payload)
    except S8BAttemptRegistryError as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc
    if (
        genesis.get("schema_version")
        != profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION
    ):
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch",
            reason="attempt-registry-generation-unsupported",
        )
    try:
        genesis_binding = profile8b.S8B_BINDING_CODEC.parse(
            genesis, label="attempt registry genesis",
        )
    except core.AttemptRegistryCoreError as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc
    if genesis_binding != expected_binding:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-binding-mismatch",
        )
    try:
        generation_profile, generation_binding = (
            _profile_and_binding_for_generation(path=path, genesis=genesis)
        )
    except (core.AttemptRegistryCoreError, S8BAttemptRegistryError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc
    if generation_binding != genesis_binding:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        )
    try:
        rows, _counts, _evidence = _load_attempt_registry_with_evidence_locked(
            root=root,
            data=payload,
            profile=generation_profile,
            expected_binding=expected_binding,
        )
        return rows
    except (core.AttemptRegistryCoreError, S8BAttemptRegistryError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc


def capture_attempt_registry_prefix(
    repo_root: Path,
    *,
    expected_binding: profile8b.S8BAttemptBinding,
) -> dict[str, object]:
    """Capture the current prefix identity after a full read-only replay.

    This does not inspect other generations for freeze-wide budget excess;
    that is a writer barrier.  It also does not detect ledger deletion followed
    by recreation of the same bytes (D1533).
    """

    try:
        rows = _replay_current_v2_attempt_registry(
            Path(repo_root), expected_binding=expected_binding,
        )
    except (core.AttemptRegistryCoreError, S8BAttemptRegistryError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc
    return _attempt_registry_prefix_proof(
        binding=expected_binding,
        row_count=len(rows),
        chain_head_sha256=rows[-1]["event_sha256"],
    )


def inspect_attempt_registry_prefix(
    repo_root: Path,
    *,
    expected_binding: profile8b.S8BAttemptBinding,
    row_count: int,
    chain_head_sha256: str,
) -> dict[str, object]:
    """Verify a reported prefix against a fully replayed live generation.

    This does not inspect other generations for freeze-wide budget excess;
    that is a writer barrier.  It also does not detect ledger deletion followed
    by recreation of the same bytes (D1533).
    """

    proof = _attempt_registry_prefix_proof(
        binding=expected_binding,
        row_count=row_count,
        chain_head_sha256=chain_head_sha256,
    )
    try:
        rows = _replay_current_v2_attempt_registry(
            Path(repo_root), expected_binding=expected_binding,
        )
    except (core.AttemptRegistryCoreError, S8BAttemptRegistryError) as exc:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-replay-invalid",
        ) from exc
    if len(rows) < row_count:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch", reason="attempt-registry-prefix-too-short",
        )
    if rows[row_count - 1]["event_sha256"] != chain_head_sha256:
        raise admission.FloorHoldoutEvidenceError(
            category="mismatch",
            reason="attempt-registry-prefix-head-mismatch",
        )
    return proof


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


def _strict_canonical_json_object(data: bytes, *, label: str) -> dict[str, Any]:
    """Decode one LF-free canonical object while rejecting duplicate keys."""

    if type(data) is not bytes or not data or data.endswith(b"\n"):
        _fail(
            "s8b-terminal-evidence",
            f"{label} is not LF-free canonical JSON bytes",
        )

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail(
                    "s8b-terminal-evidence",
                    f"{label} contains duplicate key: {key}",
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_constant=lambda token: _fail(
                "s8b-terminal-evidence",
                f"{label} contains nonfinite token: {token}",
            ),
        )
    except S8BAttemptRegistryError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise S8BAttemptRegistryError(
            f"[s8b-terminal-evidence] {label} is not strict JSON"
        ) from exc
    if type(value) is not dict or core.canonical_json_bytes(value) != data:
        _fail(
            "s8b-terminal-evidence",
            f"{label} is not one canonical object",
        )
    return value


def _terminal_evidence_path(root: Path, digest: str) -> Path:
    digest = _sha256(digest, label="terminal_evidence_sha256")
    return root.joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts,
        "terminal-evidence",
        f"{digest}.json",
    )


def _external_evidence_path(root: Path, digest: str) -> Path:
    digest = _sha256(digest, label="external_evidence_sha256")
    return root.joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts,
        "external-evidence",
        f"{digest}.json",
    )


def _validated_external_evidence_bytes(
    data: bytes,
    *,
    expected_digest: str,
    evidence: terminal_evidence.ValidatedTerminalEvidence | None = None,
) -> bytes:
    """Validate one digest-named pre-output source and optional terminal."""

    digest = _sha256(expected_digest, label="external_evidence_sha256")
    if type(data) is not bytes or hashlib.sha256(data).hexdigest() != digest:
        _fail("s8b-terminal-evidence", "external evidence bytes digest differs")
    try:
        if evidence is None:
            terminal_evidence._pre_output_evidence_document(data)
        else:
            terminal_evidence._assert_external_evidence_matches_terminal(
                data,
                expected_digest=digest,
                terminal_document=evidence.document,
            )
    except terminal_evidence.TerminalEvidenceError as exc:
        raise S8BAttemptRegistryError(str(exc)) from exc
    return data


def _promote_draft_to_validated(
    draft: terminal_evidence.SealedTerminalEvidenceDraft,
    *,
    classification_receipt_sha256: str,
    classification_event_sha256: str,
    observation_event_sha256: str,
    issuer_token: object,
) -> terminal_evidence.ValidatedTerminalEvidence:
    """Rebuild draft bytes with the three durable phase digests."""

    if type(draft) is not terminal_evidence.SealedTerminalEvidenceDraft:
        _fail("s8b-terminal-evidence", "terminal evidence draft type differs")
    if issuer_token is not _TERMINAL_EVIDENCE_ISSUER_TOKEN:
        _fail("s8b-terminal-evidence", "terminal evidence issuer differs")
    phase_digests = {
        "classification_receipt_sha256": _sha256(
            classification_receipt_sha256,
            label="classification_receipt_sha256",
        ),
        "classification_event_sha256": _sha256(
            classification_event_sha256,
            label="classification_event_sha256",
        ),
        "observation_event_sha256": _sha256(
            observation_event_sha256,
            label="observation_event_sha256",
        ),
    }
    source_bytes = draft.canonical_bytes
    document = _strict_canonical_json_object(
        source_bytes, label="terminal evidence draft",
    )
    binding = document.get("attempt_binding")
    if type(binding) is not dict or len(binding) != 9:
        _fail("s8b-terminal-evidence", "draft attempt binding differs")
    document["attempt_binding"] = {**binding, **phase_digests}
    promoted_bytes = core.canonical_json_bytes(document)
    if promoted_bytes == source_bytes:
        _fail("s8b-terminal-evidence", "draft bytes were not rebuilt")
    validated = object.__new__(terminal_evidence.ValidatedTerminalEvidence)
    object.__setattr__(validated, "_canonical_bytes", promoted_bytes)
    object.__setattr__(validated, "_issuer_token", issuer_token)
    try:
        terminal_evidence.require_sealed_terminal_evidence(validated)
    except terminal_evidence.TerminalEvidenceError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-terminal-evidence] promoted evidence is invalid"
        ) from exc
    return validated


def _validated_terminal_evidence_from_bytes(
    data: bytes,
    *,
    expected_digest: str,
    expected_binding: Mapping[str, object],
) -> terminal_evidence.ValidatedTerminalEvidence:
    """Issue a capability only after durable bytes pass every file check."""

    digest = _sha256(expected_digest, label="terminal evidence filename")
    if hashlib.sha256(data).hexdigest() != digest:
        _fail("s8b-terminal-evidence", "terminal evidence bytes digest differs")
    document = _strict_canonical_json_object(data, label="terminal evidence file")
    validated = object.__new__(terminal_evidence.ValidatedTerminalEvidence)
    object.__setattr__(validated, "_canonical_bytes", core.canonical_json_bytes(document))
    object.__setattr__(
        validated, "_issuer_token", _TERMINAL_EVIDENCE_ISSUER_TOKEN,
    )
    try:
        terminal_evidence.require_sealed_terminal_evidence(validated)
    except terminal_evidence.TerminalEvidenceError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-terminal-evidence] durable evidence is invalid"
        ) from exc
    if validated.sha256 != digest:
        _fail("s8b-terminal-evidence", "terminal evidence filename differs")
    actual_binding = validated.document.get("attempt_binding")
    if (
        type(actual_binding) is not dict
        or type(expected_binding) is not dict
        or core.canonical_json_bytes(actual_binding)
        != core.canonical_json_bytes(expected_binding)
    ):
        _fail("s8b-terminal-evidence", "terminal evidence binding differs")
    return validated


def _registry_documents_for_evidence(data: bytes) -> core.RegistryRows:
    if type(data) is not bytes or not data or not data.endswith(b"\n"):
        _fail("s8b-terminal-evidence", "registry bytes are not line complete")
    lines = data.splitlines(keepends=True)
    if b"".join(lines) != data:
        _fail("s8b-terminal-evidence", "registry line framing differs")
    return tuple(
        _canonical_document(line, label=f"attempt registry line {index}")
        for index, line in enumerate(lines, start=1)
    )


def _terminal_slot_from_documents(
    rows: core.RegistryRows,
    *,
    row: Mapping[str, Any],
    profile: core.DomainProfile[Any, Any],
) -> profile8b.S8BV2AttemptSlot:
    slots_value = rows[0].get("slots")
    if type(slots_value) is not list:
        _fail("s8b-terminal-evidence", "registry genesis slots differ")
    matches: list[profile8b.S8BV2AttemptSlot] = []
    for index, value in enumerate(slots_value):
        slot = profile.slot_codec.parse(value, label=f"genesis slot {index}")
        if _row_is_for_slot(row, slot, profile=profile):
            if type(slot) is not profile8b.S8BV2AttemptSlot:
                _fail("s8b-terminal-evidence", "terminal slot type differs")
            matches.append(slot)
    if len(matches) != 1:
        _fail("s8b-terminal-evidence", "terminal slot identity is not unique")
    return matches[0]


def _expected_terminal_binding(
    *,
    root: Path,
    rows: core.RegistryRows,
    row: Mapping[str, Any],
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
) -> tuple[
    dict[str, object],
    Mapping[str, Any],
    profile8b.S8BV2AttemptSlot,
    str,
]:
    slot = _terminal_slot_from_documents(rows, row=row, profile=profile)
    classifications = _rows_for_event(
        rows, slot=slot, event="classification", profile=profile,
    )
    observations = _rows_for_event(
        rows, slot=slot, event="observation-start", profile=profile,
    )
    if len(classifications) != 1 or len(observations) != 1:
        _fail(
            "s8b-terminal-evidence",
            "terminal evidence requires one classification and observation",
        )
    claim_result = _classification_claim(
        root=root, binding=binding, slot=slot,
    )
    assert claim_result is not None
    claim, claim_receipt_bytes = claim_result
    receipt_sha256 = _sha256(
        classifications[0]["classification_receipt_sha256"],
        label="classification row.classification_receipt_sha256",
    )
    receipt_path = _receipt_path(root, receipt_sha256)
    receipt_bytes = _read_regular_bytes(receipt_path)
    assert receipt_bytes is not None
    if (
        hashlib.sha256(receipt_bytes).hexdigest() != receipt_sha256
        or receipt_bytes != claim_receipt_bytes
    ):
        _fail(
            "s8b-terminal-evidence",
            "classification receipt differs during terminal replay",
        )
    receipt = _canonical_document(
        receipt_bytes, label="classification receipt",
    )
    external_evidence_sha256 = _sha256(
        receipt.get("external_evidence_sha256"),
        label="classification receipt.external_evidence_sha256",
    )
    expected = {
        "admission_claim_digest": claim["admission_claim_digest"],
        "attempt_id": claim["attempt_id"],
        "campaign_run_id": claim["campaign_run_id"],
        "freeze_sha256": binding.freeze_sha256,
        "manifest_sha256": claim["manifest_sha256"],
        "protocol_sha256": binding.protocol_sha256,
        "run_relpath": claim["run_relpath"],
        "schedule_row_sha256": slot.schedule_row_sha256,
        "schedule_sha256": binding.schedule_sha256,
        "classification_receipt_sha256": classifications[0][
            "classification_receipt_sha256"
        ],
        "classification_event_sha256": classifications[0]["event_sha256"],
        "observation_event_sha256": observations[0]["event_sha256"],
    }
    return expected, claim, slot, external_evidence_sha256


def _assert_terminal_durable_identity(
    *,
    root: Path,
    evidence: terminal_evidence.ValidatedTerminalEvidence,
    claim: Mapping[str, Any],
    slot: profile8b.S8BV2AttemptSlot,
    binding: profile8b.S8BAttemptBinding,
) -> None:
    claim_digest = _sha256(
        claim.get("admission_claim_digest"),
        label="classification claim.admission_claim_digest",
    )
    try:
        durable_claim = admission._read_canonical_document(
            admission._measurement_generation_claim_path(root, claim_digest)
        )
        derived = admission._measurement_generation_claim_identity(durable_claim)
    except admission.HoldoutAdmissionError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-terminal-evidence] durable measurement claim is invalid"
        ) from exc
    if derived != claim_digest:
        _fail("s8b-terminal-evidence", "durable claim path differs")
    document = evidence.document
    campaign_record = document["campaign_record"]
    expected_retry_ordinal = (
        None if slot.measurement_ordinal == 0 else slot.measurement_ordinal
    )
    slot_identity = {
        "holdout_id": slot.freeze_holdout_key,
        "configuration_id": slot.configuration_id,
        "retry_ordinal": expected_retry_ordinal,
    }
    for field_name, expected_value in slot_identity.items():
        if campaign_record.get(field_name) != expected_value:
            _fail(
                "s8b-terminal-evidence",
                f"campaign record differs from slot: {field_name}",
            )
    key = durable_claim.get("key")
    attempt_ids = durable_claim.get("attempt_ids")
    expected_values = {
        "protocol_sha256": binding.protocol_sha256,
        "manifest_sha256": claim["manifest_sha256"],
        "campaign_run_id": claim["campaign_run_id"],
        "run_relpath": claim["run_relpath"],
        "cell_id": campaign_record["cell_id"],
        "records": campaign_record["records"],
        "threads": campaign_record["threads"],
        "mode": document["mode"],
    }
    if not isinstance(key, Mapping):
        _fail("s8b-terminal-evidence", "durable claim key differs")
    key_expected = {
        "freeze_sha256": binding.freeze_sha256,
        "freeze_holdout_key": slot.freeze_holdout_key,
        "configuration_id": slot.configuration_id,
    }
    for field_name, expected_value in key_expected.items():
        if key.get(field_name) != expected_value:
            _fail(
                "s8b-terminal-evidence",
                f"durable claim differs: key.{field_name}",
            )
    for field_name, expected_value in expected_values.items():
        if durable_claim.get(field_name) != expected_value:
            _fail(
                "s8b-terminal-evidence",
                f"durable claim differs: {field_name}",
            )
    attempt_id = campaign_record["attempt_id"]
    if (
        type(attempt_ids) is not list
        or attempt_id != claim.get("attempt_id")
        or attempt_id not in attempt_ids
    ):
        _fail("s8b-terminal-evidence", "durable claim attempt identity differs")
    workload_sha256 = hashlib.sha256(
        core.canonical_json_bytes(durable_claim.get("workload"))
    ).hexdigest()
    if document.get("workload_sha256") != workload_sha256:
        _fail("s8b-terminal-evidence", "durable claim workload differs")


def _terminal_validating_profile(
    profile: core.DomainProfile[Any, Any],
    evidence_by_digest: Mapping[
        str, terminal_evidence.ValidatedTerminalEvidence
    ],
) -> core.DomainProfile[Any, Any]:
    """Build the private v2 profile reachable only after evidence validation."""

    if profile.schema is not profile8b.S8B_V2_SCHEMA_PROFILE:
        return profile

    def validate(row: Mapping[str, Any]) -> None:
        digest = row.get("terminal_evidence_sha256")
        evidence = evidence_by_digest.get(digest) if isinstance(digest, str) else None
        if evidence is None:
            _fail("s8b-terminal-evidence", "terminal evidence capability is absent")
        if evidence._issuer_token is not _TERMINAL_EVIDENCE_ISSUER_TOKEN:
            _fail("s8b-terminal-evidence", "terminal evidence issuer differs")
        profile8b._require_sealed_s8b_v2_terminal(row, evidence)

    return replace(profile, terminal_row_validator=validate)


def _load_terminal_evidence_locked(
    root: Path,
    registry_bytes: bytes,
    *,
    profile: core.DomainProfile[Any, Any],
    expected_binding: profile8b.S8BAttemptBinding,
    evidence_overrides: Mapping[
        str, terminal_evidence.ValidatedTerminalEvidence
    ] | None = None,
) -> dict[str, terminal_evidence.ValidatedTerminalEvidence]:
    """Load every terminal file named by one v2 registry snapshot."""

    if profile.schema is not profile8b.S8B_V2_SCHEMA_PROFILE:
        return {}
    rows = _registry_documents_for_evidence(registry_bytes)
    overrides = {} if evidence_overrides is None else dict(evidence_overrides)
    result: dict[str, terminal_evidence.ValidatedTerminalEvidence] = {}
    for row in rows:
        if row.get("event") != "terminal":
            continue
        digest = _sha256(
            row.get("terminal_evidence_sha256"),
            label="terminal row.terminal_evidence_sha256",
        )
        expected, claim, slot, external_evidence_sha256 = (
            _expected_terminal_binding(
                root=root,
                rows=rows,
                row=row,
                profile=profile,
                binding=expected_binding,
            )
        )
        supplied = overrides.pop(digest, None)
        if supplied is None:
            path = _terminal_evidence_path(root, digest)
            if path.name != f"{digest}.json":
                _fail("s8b-terminal-evidence", "terminal evidence filename differs")
            data = _read_regular_bytes(path)
            assert data is not None
            supplied = _validated_terminal_evidence_from_bytes(
                data,
                expected_digest=digest,
                expected_binding=expected,
            )
        else:
            if (
                type(supplied) is not terminal_evidence.ValidatedTerminalEvidence
                or supplied._issuer_token is not _TERMINAL_EVIDENCE_ISSUER_TOKEN
            ):
                _fail("s8b-terminal-evidence", "terminal evidence override differs")
            supplied = _validated_terminal_evidence_from_bytes(
                supplied.canonical_bytes,
                expected_digest=digest,
                expected_binding=expected,
            )
        _assert_terminal_durable_identity(
            root=root,
            evidence=supplied,
            claim=claim,
            slot=slot,
            binding=expected_binding,
        )
        external_path = _external_evidence_path(
            root, external_evidence_sha256,
        )
        if external_path.name != f"{external_evidence_sha256}.json":
            _fail("s8b-terminal-evidence", "external evidence filename differs")
        external_data = _read_regular_bytes(external_path)
        assert external_data is not None
        _validated_external_evidence_bytes(
            external_data,
            expected_digest=external_evidence_sha256,
            evidence=supplied,
        )
        result[digest] = supplied
    if overrides:
        _fail("s8b-terminal-evidence", "unused terminal evidence override")
    return result


def _load_attempt_registry_with_evidence_locked(
    *,
    root: Path,
    data: bytes,
    profile: core.DomainProfile[Any, Any],
    expected_binding: profile8b.S8BAttemptBinding,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
    evidence_overrides: Mapping[
        str, terminal_evidence.ValidatedTerminalEvidence
    ] | None = None,
) -> tuple[
    core.RegistryRows,
    core.BudgetCounts,
    Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
]:
    evidence_by_digest = _load_terminal_evidence_locked(
        root,
        data,
        profile=profile,
        expected_binding=expected_binding,
        evidence_overrides=evidence_overrides,
    )
    validating_profile = _terminal_validating_profile(
        profile, evidence_by_digest,
    )
    rows, counts = core.load_attempt_registry_with_budget_counts(
        data,
        profile=validating_profile,
        expected_binding=expected_binding,
        initial_started_budget_counts=initial_started_budget_counts,
    )
    return rows, counts, evidence_by_digest


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


def _publish_registry_generation_create_only(
    *,
    root: Path,
    path: Path,
    payload: bytes,
) -> None:
    """Publish a new protocol generation without completing stale debris."""

    try:
        relative = PurePosixPath(*path.relative_to(root).parts)
    except ValueError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-path] generation path escapes the shared root"
        ) from exc
    parts = relative.parts
    freeze = parts[1] if len(parts) == 4 else ""
    protocol = path.parent.name
    if (
        len(parts) != 4
        or parts[0] != "floor-attempt-registries"
        or parts[-1] != "registry.jsonl"
        or len(freeze) != 64
        or any(character not in "0123456789abcdef" for character in freeze)
        or len(protocol) != 64
        or any(character not in "0123456789abcdef" for character in protocol)
    ):
        _fail(
            "s8b-attempt-registry-path",
            "generation publish path is not canonical",
        )
    generation = path.parent
    freeze_directory = generation.parent
    _ensure_durable_directory(freeze_directory)
    admission._assert_no_symlink_components(freeze_directory)
    try:
        generation.mkdir(mode=0o700)
    except FileExistsError:
        try:
            mode = generation.lstat().st_mode
        except OSError as exc:
            raise S8BAttemptRegistryError(
                "[s8b-attempt-registry-storage] cannot inspect generation destination"
            ) from exc
        if generation.is_symlink() or not stat.S_ISDIR(mode):
            _fail(
                "s8b-attempt-registry-storage",
                "generation directory is unsafe or incomplete",
            )
        if not path.is_file() or path.is_symlink():
            _fail(
                "s8b-attempt-registry-storage",
                "generation directory is unsafe or incomplete",
            )
        _fail(
            "s8b-attempt-registry-create-only",
            "durable registry generation already exists",
        )
    except OSError as exc:
        raise S8BAttemptRegistryError(
            "[s8b-attempt-registry-storage] cannot create registry generation"
        ) from exc
    admission._assert_no_symlink_components(generation)
    _fsync_directory(generation)
    _fsync_directory(freeze_directory)
    logical_name = relative.as_posix()
    _publish_create_only(
        path,
        payload,
        logical_name=logical_name,
        allow_exact_retry=False,
    )


def _slot_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: core.DomainProfile[Any, Any],
    slot_id: Hashable,
) -> profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot:
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
    row: Mapping[str, Any],
    slot: Any,
    *,
    profile: core.DomainProfile[Any, Any],
) -> bool:
    return core._row_is_for_slot(
        row,
        slot=slot,
        profile=profile,
    )


def _rows_for_event(
    rows: Sequence[Mapping[str, Any]],
    *,
    slot: Any,
    event: str,
    profile: core.DomainProfile[Any, Any],
) -> list[Mapping[str, Any]]:
    return [
        row for row in rows
        if row.get("event") == event
        and _row_is_for_slot(row, slot, profile=profile)
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


def _slot_address_payload_v3(
    *,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
) -> dict[str, Any]:
    """Bind a v2 claim address to the generation and all five slot axes."""

    return {
        **profile8b.S8B_BINDING_CODEC.to_event_fields(binding),
        **profile8b.S8B_V2_SLOT_CODEC.to_json(slot),
    }


def _claim_address_payload(
    *,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
) -> dict[str, Any]:
    if type(slot) is profile8b.S8BAttemptSlot:
        return _slot_address_payload(
            freeze_sha256=binding.freeze_sha256, slot=slot,
        )
    if type(slot) is profile8b.S8BV2AttemptSlot:
        return _slot_address_payload_v3(binding=binding, slot=slot)
    _fail("s8b-attempt-registry-slot", "classification claim slot type differs")


def _classification_claim_path(
    root: Path,
    *,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
) -> Path:
    address = hashlib.sha256(
        core.canonical_json_bytes(
            _claim_address_payload(binding=binding, slot=slot)
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
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
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
    schema = (
        _CLASSIFICATION_CLAIM_V3_SCHEMA
        if type(slot) is profile8b.S8BV2AttemptSlot
        else _CLASSIFICATION_CLAIM_SCHEMA
    )
    return {
        "schema_version": schema,
        "event": _CLASSIFICATION_CLAIM_EVENT,
        **_claim_address_payload(binding=binding, slot=slot),
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

_CLAIM_V3_KEYS = _CLAIM_KEYS | frozenset({
    "protocol_sha256",
    "schedule_sha256",
    "measurement_ordinal",
})


def _classification_claim(
    *,
    root: Path,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
    missing_ok: bool = False,
) -> tuple[Mapping[str, Any], bytes] | None:
    claim_path = _classification_claim_path(
        root, binding=binding, slot=slot,
    )
    claim_bytes = _read_regular_bytes(claim_path, missing_ok=missing_ok)
    if claim_bytes is None:
        return None
    claim = _canonical_document(claim_bytes, label="classification claim")
    is_v3 = type(slot) is profile8b.S8BV2AttemptSlot
    expected_keys = _CLAIM_V3_KEYS if is_v3 else _CLAIM_KEYS
    if frozenset(claim) != expected_keys:
        _fail(
            "s8b-attempt-registry-classification",
            "classification claim exact keys differ",
        )
    expected_identity = {
        "schema_version": (
            _CLASSIFICATION_CLAIM_V3_SCHEMA
            if is_v3
            else _CLASSIFICATION_CLAIM_SCHEMA
        ),
        "event": _CLASSIFICATION_CLAIM_EVENT,
        **_claim_address_payload(binding=binding, slot=slot),
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


def _measurement_generation_claim_digest_from_v2_payload(
    root: Path,
    *,
    claim_address: str,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
) -> str:
    """Derive marker authority from the durable v2 admission claim payload."""

    address = _sha256(claim_address, label="admission_claim_digest")
    claim = admission._read_canonical_document(
        admission._measurement_generation_claim_path(root, address)
    )
    derived = admission._measurement_generation_claim_identity(claim)
    if derived != address:
        _fail(
            "s8b-attempt-registry-consume",
            "v2 admission claim path differs from its payload",
        )
    key = claim.get("key")
    if (
        not isinstance(key, Mapping)
        or key.get("freeze_sha256") != binding.freeze_sha256
        or claim.get("protocol_sha256") != binding.protocol_sha256
        or key.get("freeze_holdout_key") != slot.freeze_holdout_key
        or key.get("configuration_id") != slot.configuration_id
    ):
        _fail(
            "s8b-attempt-registry-consume",
            "v2 admission claim differs from the registry generation or slot",
        )
    return derived


@dataclass(frozen=True, slots=True)
class _ClassificationResult:
    slot: profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot
    receipt_bytes: bytes
    receipt_sha256: str
    event_sha256: str
    reason: str | None
    claim: Mapping[str, Any]
    publish: bool


TransitionResultT = TypeVar("TransitionResultT")


def _load_other_generation_budget_counts_locked(
    *,
    root: Path,
    current_path: Path,
    freeze_sha256: str,
) -> core.BudgetCounts:
    generations = _registry_generation_paths_locked(root, freeze_sha256)
    if current_path not in generations:
        _fail(
            "s8b-attempt-registry-storage",
            "current registry is not an enumerated generation",
        )
    counts: core.BudgetCounts = {}
    for generation_path in generations:
        if generation_path == current_path:
            continue
        data = _read_regular_bytes(generation_path)
        assert data is not None
        genesis = _peek_registry_genesis(data)
        generation_profile, generation_binding = (
            _profile_and_binding_for_generation(
                path=generation_path, genesis=genesis,
            )
        )
        _rows, counts, _evidence = (
            _load_attempt_registry_with_evidence_locked(
                root=root,
                data=data,
                profile=generation_profile,
                expected_binding=generation_binding,
                initial_started_budget_counts=counts,
            )
        )
    return counts


def _run_prelock_snapshot_hook(path: Path) -> None:
    # This read is a concurrency-test rendezvous only.  The authoritative read
    # is repeated under the root lock by _atomic_update_locked.
    snapshot = _read_regular_bytes(path)
    assert snapshot is not None
    snapshot_hook = _PRELOCK_SNAPSHOT_HOOK
    if snapshot_hook is not None:
        snapshot_hook(snapshot)


def _atomic_update_locked(
    lock: admission._AdmissionRootLock,
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    transition: Callable[
        [
            core.RegistryRows,
            Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
        ],
        tuple[core.RegistryRows, TransitionResultT],
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
    candidate_evidence: Callable[
        [TransitionResultT],
        Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
    ] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]:
    admission._assert_active_admission_root_lock(lock, root=root)
    other_counts = _load_other_generation_budget_counts_locked(
        root=root,
        current_path=path,
        freeze_sha256=binding.freeze_sha256,
    )
    old_bytes = _read_regular_bytes(path)
    assert old_bytes is not None
    _fault("after-authoritative-read")
    rows, _old_counts, old_evidence = (
        _load_attempt_registry_with_evidence_locked(
            root=root,
            data=old_bytes,
            profile=profile,
            expected_binding=binding,
            initial_started_budget_counts=other_counts,
        )
    )
    _fault("after-replay")
    candidate, result = transition(rows, old_evidence)
    _fault("after-transition")
    candidate_bytes = _registry_bytes(candidate)
    overrides = (
        None if candidate_evidence is None else candidate_evidence(result)
    )
    validated, _candidate_counts, _candidate_terminal_evidence = (
        _load_attempt_registry_with_evidence_locked(
            root=root,
            data=candidate_bytes,
            profile=profile,
            expected_binding=binding,
            initial_started_budget_counts=other_counts,
            evidence_overrides=overrides,
        )
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


def _atomic_update(
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    transition: Callable[
        [
            core.RegistryRows,
            Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
        ],
        tuple[core.RegistryRows, TransitionResultT],
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
    candidate_evidence: Callable[
        [TransitionResultT],
        Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
    ] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]:
    _run_prelock_snapshot_hook(path)
    with admission._locked(root) as lock:
        return _atomic_update_locked(
            lock,
            root=root,
            path=path,
            profile=profile,
            binding=binding,
            transition=transition,
            prepare=prepare,
            candidate_evidence=candidate_evidence,
        )


def _atomic_update_with_consumption_marker(
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
    marker: admission.FloorAttemptConsumptionMarker,
    measurement_generation_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    transition: Callable[
        [
            core.RegistryRows,
            Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
        ],
        tuple[core.RegistryRows, TransitionResultT],
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
    candidate_evidence: Callable[
        [TransitionResultT],
        Mapping[str, terminal_evidence.ValidatedTerminalEvidence],
    ] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]:
    """Update a v2 generation inside one marker-owned lock interval."""

    _run_prelock_snapshot_hook(path)
    with admission._locked(root) as lock:
        return marker.use(
            lock=lock,
            root=root,
            measurement_generation_claim_digest=(
                measurement_generation_claim_digest
            ),
            attempt_id=attempt_id,
            campaign_run_id=campaign_run_id,
            manifest_sha256=manifest_sha256,
            run_relpath=run_relpath,
            cell_id=cell_id,
            freeze_holdout_key=slot.freeze_holdout_key,
            configuration_id=slot.configuration_id,
            repetition=slot.repetition,
            attempt_ordinal=slot.measurement_ordinal,
            action=lambda active_lock: _atomic_update_locked(
                active_lock,
                root=root,
                path=path,
                profile=profile,
                binding=binding,
                transition=transition,
                prepare=prepare,
                candidate_evidence=candidate_evidence,
            ),
        )


def create_attempt_registry(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
        profile8b.S8BAttemptBinding,
    ],
    slots: Sequence[
        profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot
    ],
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
        protocol_sha256=_profile_protocol_sha256(profile, binding),
        requested_registry_path=requested_registry_path,
    )
    rows = core.create_attempt_registry_genesis(
        profile=profile, slots=slots, binding=binding,
    )
    payload = _registry_bytes(rows)
    core.load_attempt_registry(
        payload, profile=profile, expected_binding=binding,
    )
    with admission._locked(root):
        if profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
            _publish_registry_generation_create_only(
                root=root, path=path, payload=payload,
            )
        else:
            logical_name = _relative_registry_path(
                binding.freeze_sha256,
            ).as_posix()
            _publish_create_only(
                path,
                payload,
                logical_name=logical_name,
                allow_exact_retry=False,
            )
    return path


def read_attempt_registry(
    repo_root: Path,
    *,
    profile: core.DomainProfile[
        profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
        profile8b.S8BAttemptBinding,
    ],
    binding: profile8b.S8BAttemptBinding,
) -> core.RegistryRows:
    """Read and replay one authoritative registry without changing its rows."""

    profile = _assert_profile(profile)
    canonical_repo_root = Path(repo_root).resolve()
    root, path = _entry_paths(
        canonical_repo_root,
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=_profile_protocol_sha256(profile, binding),
    )
    with admission._locked(root):
        payload = _read_regular_bytes(path)
        assert payload is not None
        rows, _counts, _evidence = _load_attempt_registry_with_evidence_locked(
            root=root,
            data=payload,
            profile=profile,
            expected_binding=binding,
        )
        return rows


def reserve_attempt_slot(
    repo_root: Path,
    *,
    profile: core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    binding: profile8b.S8BAttemptBinding,
    slot_id: Hashable,
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
    launcher_origin_capability: _LauncherOriginCapability | None = None,
    consumption_marker: admission.FloorAttemptConsumptionMarker | None = None,
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
    if launcher_origin_capability is not None:
        _require_launcher_origin_capability(launcher_origin_capability)
    canonical_repo_root = Path(repo_root).resolve()
    root, path = _entry_paths(
        canonical_repo_root,
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=_profile_protocol_sha256(profile, binding),
    )

    v2_slot: profile8b.S8BV2AttemptSlot | None = None
    measurement_generation_claim_digest: str | None = None
    if profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
        if consumption_marker is None:
            _fail(
                "s8b-attempt-registry-consume",
                "v2 reservation requires a consumption marker",
            )
        with admission._locked(root):
            snapshot = _read_regular_bytes(path)
            assert snapshot is not None
            snapshot_rows, _counts, _evidence = (
                _load_attempt_registry_with_evidence_locked(
                    root=root,
                    data=snapshot,
                    profile=profile,
                    expected_binding=binding,
                )
            )
        candidate_slot = _slot_from_rows(
            snapshot_rows, profile=profile, slot_id=slot_id,
        )
        if type(candidate_slot) is not profile8b.S8BV2AttemptSlot:
            _fail("s8b-attempt-registry-slot", "v2 reservation slot type differs")
        if candidate_slot.attempt_ordinal != 0:
            _fail(
                "s8b-attempt-registry-consume",
                "v2 reservation recovery ordinal is not capability-backed",
            )
        v2_slot = candidate_slot
        measurement_generation_claim_digest = (
            _measurement_generation_claim_digest_from_v2_payload(
                root,
                claim_address=admission_claim_digest,
                binding=binding,
                slot=candidate_slot,
            )
        )
    elif consumption_marker is not None:
        _fail(
            "s8b-attempt-registry-consume",
            "legacy reservation does not accept a v2 consumption marker",
        )

    def transition(
        rows: core.RegistryRows,
        evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, tuple[profile8b.S8BAttemptSlot, str]]:
        validating_profile = _terminal_validating_profile(
            profile, evidence_by_digest,
        )
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
            profile=validating_profile,
            freeze_id=binding.freeze_sha256,
            slot_id=slot_id,
            binding=binding,
            run_start_receipt_sha256=run_start_receipt_sha256,
            process_identity=process_identity,
            started_at=started_at,
        )
        return candidate, (slot, capability)

    if v2_slot is not None:
        if (
            consumption_marker is None
            or measurement_generation_claim_digest is None
        ):
            _fail(
                "s8b-attempt-registry-consume",
                "v2 reservation requires a consumption marker",
            )
        _rows, (_slot, _capability) = (
            _atomic_update_with_consumption_marker(
                root=root,
                path=path,
                profile=profile,
                binding=binding,
                slot=v2_slot,
                marker=consumption_marker,
                measurement_generation_claim_digest=(
                    measurement_generation_claim_digest
                ),
                attempt_id=attempt_id,
                campaign_run_id=campaign_run_id,
                manifest_sha256=manifest_sha256,
                run_relpath=run_relpath,
                cell_id=cell_id,
                transition=transition,
            )
        )
    else:
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
        launcher_origin_capability=launcher_origin_capability,
        consumption_marker=consumption_marker,
        measurement_generation_claim_digest=(
            measurement_generation_claim_digest
        ),
    )
    return _new_handle(ReservedAttempt, state)


def _assert_classification_artifacts(
    *,
    root: Path,
    rows: Sequence[Mapping[str, Any]],
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    slot_id: Hashable,
    admission_claim_digest: str | None = None,
    attempt_id: str | None = None,
    expected_receipt_bytes: bytes | None = None,
    desired_fields: Mapping[str, Any] | None = None,
) -> tuple[
    profile8b.S8BAttemptSlot | profile8b.S8BV2AttemptSlot,
    Mapping[str, Any],
    bytes,
    Mapping[str, Any],
]:
    slot = _slot_from_rows(rows, profile=profile, slot_id=slot_id)
    classifications = _rows_for_event(
        rows, slot=slot, event="classification", profile=profile,
    )
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
    external_evidence_bytes: bytes | None = None,
) -> ClassifiedAttempt | ClassifiedFailure:
    """Publish slot claim, receipt, and row before issuing a classified handle."""

    state = _require_handle(reserved, ReservedAttempt)
    root, path = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )
    durable_external_bytes: bytes | None = None
    if external_evidence_bytes is not None:
        if state.profile.schema is not profile8b.S8B_V2_SCHEMA_PROFILE:
            _fail(
                "s8b-terminal-evidence",
                "external evidence bytes require the canonical v2 profile",
            )
        durable_external_bytes = _validated_external_evidence_bytes(
            external_evidence_bytes,
            expected_digest=external_evidence_sha256,
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
        evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, _ClassificationResult]:
        validating_profile = _terminal_validating_profile(
            state.profile, evidence_by_digest,
        )
        slot = _slot_from_rows(rows, profile=state.profile, slot_id=state.slot_id)
        capability = core.capability_digest(
            profile=state.profile,
            schema_version=state.profile.schema.current,
            freeze_id=state.freeze_id,
            slot=slot,
            binding=state.binding,
        )
        desired_fields["capability_digest_sha256"] = capability
        existing = _rows_for_event(
            rows, slot=slot, event="classification", profile=state.profile,
        )
        if existing:
            if any(
                _rows_for_event(
                    rows, slot=slot, event=event, profile=state.profile,
                )
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
            profile=validating_profile,
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
            binding=state.binding,
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
            root, binding=state.binding, slot=result.slot,
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
        preflight_payloads = [
            (claim_name, claim_bytes),
            (receipt_name, result.receipt_bytes),
        ]
        external_path: Path | None = None
        external_name: str | None = None
        if durable_external_bytes is not None:
            external_path = _external_evidence_path(
                root, external_evidence_sha256,
            )
            external_name = PurePosixPath(
                *external_path.relative_to(root).parts
            ).as_posix()
            preflight_payloads.append(
                (external_name, durable_external_bytes)
            )
        preflight_payloads.append((registry_name, candidate_bytes))
        for logical_name, payload in preflight_payloads:
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
        if (
            external_path is not None
            and external_name is not None
            and durable_external_bytes is not None
        ):
            _publish_create_only(
                external_path,
                durable_external_bytes,
                logical_name=external_name,
                allow_exact_retry=True,
            )

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


def _assert_legacy_consumed_marker(
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


def _begin_attempt_observation(state: _AttemptState) -> CapturedObservation:
    root, path = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )

    def transition(
        rows: core.RegistryRows,
        evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, str]:
        validating_profile = _terminal_validating_profile(
            state.profile, evidence_by_digest,
        )
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
        if state.profile.schema is profile8b.S8B_SCHEMA_PROFILE:
            if type(slot) is not profile8b.S8BAttemptSlot:
                _fail(
                    "s8b-attempt-registry-slot",
                    "legacy observation slot type differs",
                )
            _assert_legacy_consumed_marker(root, state=state, slot=slot)
        candidate = core.begin_attempt_observation(
            rows,
            profile=validating_profile,
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

    if state.profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
        marker = state.consumption_marker
        generation_claim = state.measurement_generation_claim_digest
        with admission._locked(root):
            snapshot = _read_regular_bytes(path)
            assert snapshot is not None
            snapshot_rows, _counts, _evidence = (
                _load_attempt_registry_with_evidence_locked(
                    root=root,
                    data=snapshot,
                    profile=state.profile,
                    expected_binding=state.binding,
                )
            )
        slot = _slot_from_rows(
            snapshot_rows, profile=state.profile, slot_id=state.slot_id,
        )
        if (
            marker is None
            or generation_claim is None
            or type(slot) is not profile8b.S8BV2AttemptSlot
        ):
            _fail(
                "s8b-attempt-registry-consume",
                "v2 observation requires a consumption marker",
            )
        _rows, observation_sha256 = _atomic_update_with_consumption_marker(
            root=root,
            path=path,
            profile=state.profile,
            binding=state.binding,
            slot=slot,
            marker=marker,
            measurement_generation_claim_digest=generation_claim,
            attempt_id=state.attempt_id,
            campaign_run_id=state.campaign_run_id,
            manifest_sha256=state.manifest_sha256,
            run_relpath=state.run_relpath,
            cell_id=state.cell_id,
            transition=transition,
        )
    else:
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


def begin_attempt_observation(
    classified: ClassifiedAttempt,
) -> CapturedObservation:
    """Begin observation for a classification with no pre-output reason."""

    state = _require_handle(classified, ClassifiedAttempt)
    return _begin_attempt_observation(state)


def begin_classified_failure_observation(
    failure: ClassifiedFailure,
) -> CapturedObservation:
    """Begin observation after a durably classified pre-output reason.

    This is intentionally separate from :func:`begin_attempt_observation` so
    the existing no-reason handle contract does not widen implicitly.  The
    resulting terminal uses the deferred reader's actual bytes and never the
    unopened-failure zero-output sentinel.
    """

    state = _require_handle(failure, ClassifiedFailure)
    return _begin_attempt_observation(state)


def _assert_observation_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    state: _AttemptState,
    slot: profile8b.S8BAttemptSlot,
) -> Mapping[str, Any]:
    observations = _rows_for_event(
        rows, slot=slot, event="observation-start", profile=state.profile,
    )
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


def _reject_legacy_v2_terminal(state: _AttemptState) -> None:
    if state.profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
        _fail(
            "s8b-v2-terminal",
            "v2 terminal requires the sealed evidence API",
        )


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
    _reject_legacy_v2_terminal(state)
    if state.raw_output_sha256 is None:
        _fail("s8b-attempt-registry-handle", "captured output digest is absent")
    root, path = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )

    def transition(
        rows: core.RegistryRows,
        _evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, None]:
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


def record_sealed_attempt_terminal(
    observation: CapturedObservation,
    evidence: terminal_evidence.SealedTerminalEvidenceDraft,
) -> None:
    """Promote and publish one v2 terminal under the authoritative root lock."""

    state = _require_handle(observation, CapturedObservation)
    if state.profile.schema is not profile8b.S8B_V2_SCHEMA_PROFILE:
        _fail(
            "s8b-v2-terminal",
            "sealed terminal API requires the canonical v2 profile",
        )
    if type(evidence) is not terminal_evidence.SealedTerminalEvidenceDraft:
        _fail("s8b-terminal-evidence", "terminal evidence draft type differs")
    launcher_origin = _require_launcher_origin_capability(
        state.launcher_origin_capability,
    )
    if evidence._launcher_origin_capability is not launcher_origin:
        _fail(
            "s8b-launcher-origin",
            "terminal evidence launcher origin differs from reservation",
        )
    receipt_bytes = state.classification_receipt_bytes
    if type(receipt_bytes) is not bytes:
        _fail("s8b-terminal-evidence", "classification receipt is absent")
    receipt = _canonical_document(
        receipt_bytes, label="classification receipt",
    )
    external_evidence_sha256 = _sha256(
        receipt.get("external_evidence_sha256"),
        label="classification receipt.external_evidence_sha256",
    )
    if receipt.get("external_evidence_sha256") != (
        evidence._external_evidence_sha256
    ):
        _fail(
            "s8b-terminal-evidence",
            "classification external evidence differs from terminal sources",
        )
    if state.raw_output_sha256 is None:
        _fail("s8b-attempt-registry-handle", "captured output digest is absent")
    phase_digests = (
        state.classification_receipt_sha256,
        state.classification_event_sha256,
        state.observation_event_sha256,
    )
    if any(type(value) is not str for value in phase_digests):
        _fail("s8b-terminal-evidence", "handle phase digests are incomplete")
    root, path = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )

    def transition(
        rows: core.RegistryRows,
        evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[
        core.RegistryRows, terminal_evidence.ValidatedTerminalEvidence,
    ]:
        slot, classification, _receipt, claim = _assert_classification_artifacts(
            root=root,
            rows=rows,
            profile=state.profile,
            binding=state.binding,
            slot_id=state.slot_id,
            admission_claim_digest=state.admission_claim_digest,
            attempt_id=state.attempt_id,
            expected_receipt_bytes=state.classification_receipt_bytes,
        )
        if type(slot) is not profile8b.S8BV2AttemptSlot:
            _fail("s8b-terminal-evidence", "sealed terminal slot type differs")
        observation_row = _assert_observation_row(
            rows, state=state, slot=slot,
        )
        classification_receipt_sha256 = str(
            state.classification_receipt_sha256
        )
        classification_event_sha256 = str(state.classification_event_sha256)
        observation_event_sha256 = str(state.observation_event_sha256)
        validated = _promote_draft_to_validated(
            evidence,
            classification_receipt_sha256=classification_receipt_sha256,
            classification_event_sha256=classification_event_sha256,
            observation_event_sha256=observation_event_sha256,
            issuer_token=_TERMINAL_EVIDENCE_ISSUER_TOKEN,
        )
        expected_binding = {
            "admission_claim_digest": state.admission_claim_digest,
            "attempt_id": state.attempt_id,
            "campaign_run_id": state.campaign_run_id,
            "freeze_sha256": state.binding.freeze_sha256,
            "manifest_sha256": state.manifest_sha256,
            "protocol_sha256": state.binding.protocol_sha256,
            "run_relpath": state.run_relpath,
            "schedule_row_sha256": slot.schedule_row_sha256,
            "schedule_sha256": state.binding.schedule_sha256,
            "classification_receipt_sha256": classification[
                "classification_receipt_sha256"
            ],
            "classification_event_sha256": classification["event_sha256"],
            "observation_event_sha256": observation_row["event_sha256"],
        }
        validated = _validated_terminal_evidence_from_bytes(
            validated.canonical_bytes,
            expected_digest=validated.sha256,
            expected_binding=expected_binding,
        )
        _assert_terminal_durable_identity(
            root=root,
            evidence=validated,
            claim=claim,
            slot=slot,
            binding=state.binding,
        )
        external_data = _read_regular_bytes(
            _external_evidence_path(root, external_evidence_sha256)
        )
        assert external_data is not None
        _validated_external_evidence_bytes(
            external_data,
            expected_digest=external_evidence_sha256,
            evidence=validated,
        )
        projection = validated.projection
        if projection.raw_output_sha256 != state.raw_output_sha256:
            _fail(
                "s8b-terminal-evidence",
                "sealed raw output differs from captured handle",
            )
        validating_profile = _terminal_validating_profile(
            state.profile,
            {**evidence_by_digest, validated.sha256: validated},
        )
        candidate = core.record_attempt_terminal(
            rows,
            profile=validating_profile,
            freeze_id=state.freeze_id,
            slot_id=state.slot_id,
            binding=state.binding,
            terminal_status=projection.terminal_status,
            raw_output_sha256=projection.raw_output_sha256,
            report_sha256=projection.report_sha256,
            observation_sha256=projection.observation_sha256,
            primary_value=projection.primary_value,
            finished_at=projection.finished_at,
            failure_reason=projection.failure_reason,
            measurement_retry_reason=projection.measurement_retry_reason,
            terminal_evidence_sha256=validated.sha256,
        )
        return candidate, validated

    def prepare(
        validated: terminal_evidence.ValidatedTerminalEvidence,
        candidate_bytes: bytes,
    ) -> None:
        evidence_path = _terminal_evidence_path(root, validated.sha256)
        evidence_name = PurePosixPath(
            *evidence_path.relative_to(root).parts
        ).as_posix()
        registry_name = PurePosixPath(*path.relative_to(root).parts).as_posix()
        evidence_bytes = validated.canonical_bytes
        admission.assert_holdout_safe_bytes(evidence_name, evidence_bytes)
        admission.assert_holdout_safe_bytes(registry_name, candidate_bytes)
        _publish_create_only(
            evidence_path,
            evidence_bytes,
            logical_name=evidence_name,
            allow_exact_retry=True,
        )

    _atomic_update(
        root=root,
        path=path,
        profile=state.profile,
        binding=state.binding,
        transition=transition,
        prepare=prepare,
        candidate_evidence=lambda validated: {
            validated.sha256: validated,
        },
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
    _reject_legacy_v2_terminal(state)
    root, path = _entry_paths(
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )

    def transition(
        rows: core.RegistryRows,
        _evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, None]:
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
        state.repo_root,
        freeze_sha256=state.freeze_id,
        protocol_sha256=_profile_protocol_sha256(
            state.profile, state.binding,
        ),
        requested_registry_path=state.registry_path,
    )

    def transition(
        rows: core.RegistryRows,
        _evidence_by_digest: Mapping[
            str, terminal_evidence.ValidatedTerminalEvidence
        ],
    ) -> tuple[core.RegistryRows, None]:
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
    profile: core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    binding: profile8b.S8BAttemptBinding,
    slot_id: Hashable,
    deferred_output_reader: Callable[[], bytes],
    admission_claim_digest: str | None = None,
    attempt_id: str | None = None,
    campaign_run_id: str | None = None,
    manifest_sha256: str | None = None,
    run_relpath: str | None = None,
    cell_id: str | None = None,
    consumption_marker: admission.FloorAttemptConsumptionMarker | None = None,
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
    is_v2 = profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE
    if is_v2 and consumption_marker is None:
        _fail(
            "s8b-attempt-registry-consume",
            "v2 resume requires a consumption marker",
        )
    if not is_v2 and consumption_marker is not None:
        _fail(
            "s8b-attempt-registry-consume",
            "legacy resume does not accept a v2 consumption marker",
        )
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
        canonical_repo_root,
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=_profile_protocol_sha256(profile, binding),
    )
    pending_observation: _AttemptState | None = None
    pending_classification: tuple[ReservedAttempt, Mapping[str, Any]] | None = None
    resumed_handle: (
        ReservedAttempt | ClassifiedAttempt | ClassifiedFailure | None
    ) = None
    with admission._locked(root) as lock:
        payload = _read_regular_bytes(path)
        assert payload is not None
        rows, _counts, _evidence = _load_attempt_registry_with_evidence_locked(
            root=root,
            data=payload,
            profile=profile,
            expected_binding=binding,
        )
        slot = _slot_from_rows(rows, profile=profile, slot_id=slot_id)
        if _rows_for_event(
            rows, slot=slot, event="terminal", profile=profile,
        ):
            _fail("s8b-attempt-registry-resume", "terminal slot cannot resume")
        if _rows_for_event(
            rows, slot=slot, event="recovery", profile=profile,
        ):
            _fail("s8b-attempt-registry-resume", "recovered slot cannot resume")
        starts = _rows_for_event(
            rows, slot=slot, event="start", profile=profile,
        )
        seals = _rows_for_event(
            rows, slot=slot, event="pre-observation-seal", profile=profile,
        )
        if len(starts) != 1 or len(seals) != 1:
            _fail(
                "s8b-attempt-registry-resume",
                "slot does not have exactly one durable start and seal",
            )
        classifications = _rows_for_event(
            rows, slot=slot, event="classification", profile=profile,
        )
        if len(classifications) > 1:
            _fail(
                "s8b-attempt-registry-resume",
                "slot has multiple classification rows",
            )
        claim_result = _classification_claim(
            root=root, binding=binding, slot=slot, missing_ok=True,
        )
        marker_generation_claim: str | None = None
        if is_v2:
            if type(slot) is not profile8b.S8BV2AttemptSlot:
                _fail("s8b-attempt-registry-slot", "v2 resume slot type differs")
            if slot.attempt_ordinal != 0:
                _fail(
                    "s8b-attempt-registry-consume",
                    "v2 resume recovery ordinal is not capability-backed",
                )
            if not classifications:
                _fail(
                    "s8b-attempt-registry-resume",
                    "v2 start-only resume is not marker-atomic",
                )
            if claim_result is not None:
                marker_claim = claim_result[0]
                marker_claim_address = _sha256(
                    marker_claim.get("admission_claim_digest"),
                    label="classification claim.admission_claim_digest",
                )
                marker_identity = _consumption_identity(
                    campaign_run_id=marker_claim.get("campaign_run_id"),
                    manifest_sha256=marker_claim.get("manifest_sha256"),
                    run_relpath=marker_claim.get("run_relpath"),
                    cell_id=marker_claim.get("cell_id"),
                    attempt_id=marker_claim.get("attempt_id"),
                    slot=slot,
                )
            else:
                if (
                    admission_claim_digest is None
                    or requested_consumption_identity is None
                ):
                    _fail(
                        "s8b-attempt-registry-resume",
                        "v2 start-only resume requires complete marker identities",
                    )
                marker_claim_address = admission_claim_digest
                marker_identity = _consumption_identity(
                    campaign_run_id=requested_consumption_identity[0],
                    manifest_sha256=requested_consumption_identity[1],
                    run_relpath=requested_consumption_identity[2],
                    cell_id=requested_consumption_identity[3],
                    attempt_id=requested_consumption_identity[4],
                    slot=slot,
                )
            marker_generation_claim = (
                _measurement_generation_claim_digest_from_v2_payload(
                    root,
                    claim_address=marker_claim_address,
                    binding=binding,
                    slot=slot,
                )
            )
            assert consumption_marker is not None
            consumption_marker.use(
                lock=lock,
                root=root,
                measurement_generation_claim_digest=marker_generation_claim,
                attempt_id=marker_identity[4],
                campaign_run_id=marker_identity[0],
                manifest_sha256=marker_identity[1],
                run_relpath=marker_identity[2],
                cell_id=marker_identity[3],
                freeze_holdout_key=slot.freeze_holdout_key,
                configuration_id=slot.configuration_id,
                repetition=slot.repetition,
                attempt_ordinal=slot.measurement_ordinal,
                action=lambda active_lock: admission._assert_active_admission_root_lock(
                    active_lock, root=root,
                ),
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
                    consumption_marker=consumption_marker,
                    measurement_generation_claim_digest=(
                        marker_generation_claim
                    ),
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
                    consumption_marker=consumption_marker,
                    measurement_generation_claim_digest=(
                        marker_generation_claim
                    ),
                )
                pending_classification = (
                    _new_handle(ReservedAttempt, state), receipt,
                )
            observations = _rows_for_event(
                rows, slot=slot, event="observation-start", profile=profile,
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
                consumption_marker=consumption_marker,
                measurement_generation_claim_digest=marker_generation_claim,
                classification_receipt_bytes=receipt_bytes,
                classification_receipt_sha256=str(
                    classification["classification_receipt_sha256"]
                ),
                classification_event_sha256=str(
                    classification["event_sha256"]
                ),
            )
            observations = _rows_for_event(
                rows, slot=slot, event="observation-start", profile=profile,
            )
            if len(observations) > 1:
                _fail(
                    "s8b-attempt-registry-resume",
                    "slot has multiple observation-start rows",
                )
            if observations:
                if profile.schema is profile8b.S8B_SCHEMA_PROFILE:
                    if type(slot) is not profile8b.S8BAttemptSlot:
                        _fail(
                            "s8b-attempt-registry-slot",
                            "legacy resume slot type differs",
                        )
                    _assert_legacy_consumed_marker(
                        root, state=state, slot=slot,
                    )
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
