"""Issue one local, pre-run B-4 registry and manifest publication.

The publication binds the complete caller-supplied scheduled batch, one planned
result path for every scheduled attempt, one locally generated seed, the sealed
registry, and the 201-row analysis manifest.  It does not claim to close the
file-drawer risk end to end.

Explicit non-guarantees remain: the formal launcher is not wired to require this
receipt; paths below an unknown or not-yet-created result root cannot be fully
pre-inspected; a coordinated issuer can publish again under a different root;
the local CSPRNG call has no external uniformity proof or attestation; caller
schedule inputs are not bound to an external authoritative population; caller
result paths are not proven to be the formal producer's paths; the commitment
hash is not an identity, signature, or external pin; coordinated rewrites are
not detected; and bind-mount, external rename, or concurrent result-writer races
are not excluded.

Planned result-path inspection is a point-in-time absence check only; it does
not exclude an uncoordinated writer after either inspection.

Registry and manifest bytes are produced and loaded only through the existing
B-4 ledger public API.  This module does not reproduce their private serializers
or wire shapes.  ``issuer_commitment_sha256`` is a commitment digest, not an
issuer identity.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import NoReturn, Sequence

from .attempt_registry_core import canonical_json_bytes
from . import p3_b4_analysis_ledgers as ledgers


B4_PRERUN_RECEIPT_SCHEMA_VERSION = "p3-b4-prerun-issuer-receipt/v1"
B4_ISSUER_COMMITMENT_SCHEMA_VERSION = "p3-b4-issuer-commitment/v1"
B4_SEED_SOURCE_SCHEMA_VERSION = "p3-b4-seed-source/v1"
B4_ARTIFACT_DESCRIPTOR_SCHEMA_VERSION = "p3-b4-artifact-descriptor/v1"
B4_RAW_RECORD_REJECTIONS_NAME = "raw-record-rejections.jsonl"

_REGISTRY_NAME = "scheduled-attempt-registry.jsonl"
_MANIFEST_NAME = "analysis-manifest.json"
_RECEIPT_NAME = "prerun-issuer-receipt.json"
_RECEIPT_TEMP_NAME = ".prerun-issuer-receipt.tmp"
_SEED_SOURCE_KIND = "python-secrets-token-bytes"
_SEED_BYTE_COUNT = 32
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PREREGISTRATION_PATH = "docs/phase3-b4-reflux-ablation-preregistration.md"
_PUBLICATION_ROOT_KEY = "B-4 prerun publication root"

B4_PRERUN_NON_GUARANTEES = (
    "formal_launcher_not_wired_to_require_this_receipt",
    "unknown_or_missing_result_root_cannot_be_fully_preinspected",
    "publication_under_a_different_root_is_not_prevented",
    "csprng_uniformity_and_external_attestation_are_not_proven",
    "caller_schedule_is_not_bound_to_an_external_authoritative_population",
    "caller_result_paths_are_not_proven_formal_producer_paths",
    "issuer_commitment_hash_is_not_identity_signature_or_external_pin",
    "coordinated_rewrite_is_not_detected",
    "bind_mount_and_external_rename_races_are_not_excluded",
    "concurrent_result_writer_race_is_not_excluded",
    "file_drawer_risk_is_not_closed_end_to_end",
)


class B4PrerunRejectionReason(str, Enum):
    """Closed reason codes for a rejected B-4 issuer operation."""

    SCHEDULED_INPUTS_INVALID = "scheduled_inputs_invalid"
    PLANNED_RESULT_MAPPING_MISMATCH = "planned_result_mapping_mismatch"
    PLANNED_RESULT_PATH_INVALID = "planned_result_path_invalid"
    PLANNED_RESULT_PATH_DUPLICATE = "planned_result_path_duplicate"
    RESULT_PATH_SYMLINK_COMPONENT = "result_path_symlink_component"
    RESULT_PATH_COMPONENT_NOT_DIRECTORY = "result_path_component_not_directory"
    RESULT_PATH_INSPECTION_FAILED = "result_path_inspection_failed"
    RESULT_ARTIFACT_ALREADY_EXISTS = "result_artifact_already_exists"
    PUBLICATION_ROOT_INVALID = "publication_root_invalid"
    PUBLICATION_ROOT_NOT_PREREGISTERED = "publication_root_not_preregistered"
    PUBLICATION_ROOT_EXISTS = "publication_root_exists"
    PUBLICATION_ROOT_CHANGED = "publication_root_changed"
    DESIGN_NOT_FEASIBLE = "design_not_feasible"
    CSPRNG_FAILURE = "csprng_failure"
    LEDGER_CONTRACT_VIOLATION = "ledger_contract_violation"
    PUBLICATION_IO_ERROR = "publication_io_error"
    PUBLICATION_COMMIT_UNCERTAIN = "publication_commit_uncertain"
    RECEIPT_SCHEMA_MISMATCH = "receipt_schema_mismatch"
    ARTIFACT_MISMATCH = "artifact_mismatch"
    ISSUER_COMMITMENT_MISMATCH = "issuer_commitment_mismatch"
    SEED_SOURCE_MISMATCH = "seed_source_mismatch"
    COMPLETENESS_MISMATCH = "completeness_mismatch"


class B4PrerunIssuerError(ValueError):
    """A B-4 pre-run publication was rejected with one typed reason."""

    def __init__(self, reason: B4PrerunRejectionReason, detail: str) -> None:
        self.reason = reason
        super().__init__(f"{reason.value}: {detail}")


@dataclass(frozen=True, slots=True)
class B4PlannedResultArtifact:
    """The exact planned result leaf for one scheduled attempt."""

    attempt_id: str
    artifact_path: str


@dataclass(frozen=True, slots=True)
class B4PrerunPublication:
    """A loaded B-4 publication and its existing-ledger objects.

    ``non_guarantees`` records that the formal launcher is not wired, unknown
    roots cannot be fully pre-inspected, separate-root reissuance is possible,
    the caller schedule has no external authoritative-population binding, the
    commitment is not an identity/signature/external pin, coordinated rewrites
    and concurrent result-writer races are not detected, and the CSPRNG has no
    external proof.  The publication therefore does not assert that the full
    file-drawer risk is closed.
    """

    publication_root: str
    registry_path: str
    manifest_path: str
    receipt_path: str
    issuer_commitment_sha256: str
    planned_result_artifacts: tuple[B4PlannedResultArtifact, ...]
    schedule_receipt: ledgers.B4ScheduleReceipt
    registry: ledgers.B4ScheduledAttemptRegistry
    seed_receipt: ledgers.B4RandomizationSeedRecord
    manifest: ledgers.B4AnalysisManifest
    completeness: ledgers.B4ManifestCompletenessReceipt
    receipt_canonical_bytes: bytes
    receipt_sha256: str
    non_guarantees: tuple[str, ...]


def _reject(
    reason: B4PrerunRejectionReason,
    detail: str,
    *,
    cause: BaseException | None = None,
) -> NoReturn:
    error = B4PrerunIssuerError(reason, detail)
    if cause is None:
        raise error
    raise error from cause


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_exact_typed_mapping(value: object, expected: dict[str, object]) -> bool:
    return (
        type(value) is dict
        and set(value) == set(expected)
        and all(
            type(value[key]) is type(expected_item) and value[key] == expected_item
            for key, expected_item in expected.items()
        )
    )


def _canonical_absolute_path(
    value: object,
    *,
    reason: B4PrerunRejectionReason,
    label: str,
) -> str:
    if type(value) is not str or not value or "\x00" in value:
        _reject(reason, f"{label} must be a non-empty path string")
    if not os.path.isabs(value) or value.startswith("//"):
        _reject(reason, f"{label} must be an absolute POSIX path")
    components = value.split("/")[1:]
    if not components or any(component in ("", ".", "..") for component in components):
        _reject(reason, f"{label} must not contain empty, dot, or dot-dot components")
    if os.path.normpath(value) != value:
        _reject(reason, f"{label} is not canonical")
    return value


def _preregistered_publication_root() -> str:
    reason = B4PrerunRejectionReason.PUBLICATION_ROOT_NOT_PREREGISTERED
    try:
        document = (_REPOSITORY_ROOT / _PREREGISTRATION_PATH).read_bytes().decode("utf-8")
    except OSError as exc:
        _reject(reason, "cannot read publication root preregistration", cause=exc)
    except UnicodeDecodeError as exc:
        _reject(reason, "publication root preregistration is not UTF-8", cause=exc)
    lines = [line for line in document.splitlines() if _PUBLICATION_ROOT_KEY in line]
    if len(lines) != 1:
        _reject(reason, f"expected exactly one publication root declaration, found {len(lines)}")
    match = re.fullmatch(
        r"B-4 prerun publication root \(repo 相対\): `(?P<root>output/[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)*)`",
        lines[0],
    )
    if match is None:
        _reject(reason, "malformed publication root declaration")
    return _canonical_absolute_path(
        str(_REPOSITORY_ROOT / match.group("root")),
        reason=reason,
        label="preregistered publication root",
    )


def _require_preregistered_publication_root(root: str) -> None:
    if root != _preregistered_publication_root():
        _reject(
            B4PrerunRejectionReason.PUBLICATION_ROOT_NOT_PREREGISTERED,
            "publication_root does not match the preregistered root",
        )


def _inspect_result_leaf_absent(path: str) -> None:
    current = "/"
    components = path.split("/")[1:]
    for index, component in enumerate(components):
        current = os.path.join(current, component)
        is_leaf = index == len(components) - 1
        try:
            status = os.lstat(current)
        except FileNotFoundError:
            return
        except OSError as exc:
            _reject(
                B4PrerunRejectionReason.RESULT_PATH_INSPECTION_FAILED,
                f"cannot inspect planned result path component: {current}",
                cause=exc,
            )
        if is_leaf:
            _reject(
                B4PrerunRejectionReason.RESULT_ARTIFACT_ALREADY_EXISTS,
                f"planned result leaf already exists: {path}",
            )
        if stat.S_ISLNK(status.st_mode):
            _reject(
                B4PrerunRejectionReason.RESULT_PATH_SYMLINK_COMPONENT,
                f"planned result path has a symlink component: {current}",
            )
        if not stat.S_ISDIR(status.st_mode):
            _reject(
                B4PrerunRejectionReason.RESULT_PATH_COMPONENT_NOT_DIRECTORY,
                f"planned result path component is not a directory: {current}",
            )


def _ensure_new_publication_root(path: str) -> None:
    current = "/"
    components = path.split("/")[1:]
    for index, component in enumerate(components):
        current = os.path.join(current, component)
        is_leaf = index == len(components) - 1
        try:
            status = os.lstat(current)
        except FileNotFoundError as exc:
            if is_leaf:
                return
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
                f"publication root parent does not exist: {current}",
                cause=exc,
            )
        except OSError as exc:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
                f"cannot inspect publication root component: {current}",
                cause=exc,
            )
        if is_leaf:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_EXISTS,
                f"publication root already exists: {path}",
            )
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
                f"publication root parent is not a real directory: {current}",
            )


def _open_validated_publication_parent(path: str) -> tuple[int, str]:
    """Open and retain the already validated parent of one absent root."""

    _ensure_new_publication_root(path)
    parent_path, root_name = os.path.split(path)
    parent_fd = -1
    try:
        parent_fd = os.open(
            parent_path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        path_status = os.lstat(parent_path)
        held_status = os.fstat(parent_fd)
        if (
            stat.S_ISLNK(path_status.st_mode)
            or not stat.S_ISDIR(path_status.st_mode)
            or (path_status.st_dev, path_status.st_ino)
            != (held_status.st_dev, held_status.st_ino)
        ):
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_CHANGED,
                "publication root parent changed while it was opened",
            )
        try:
            os.stat(root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_EXISTS,
                f"publication root was concurrently created: {path}",
            )
        return parent_fd, root_name
    except B4PrerunIssuerError:
        if parent_fd >= 0:
            try:
                os.close(parent_fd)
            except OSError:
                pass
        raise
    except OSError as exc:
        if parent_fd >= 0:
            try:
                os.close(parent_fd)
            except OSError:
                pass
        _reject(
            B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
            "cannot retain the validated publication root parent",
            cause=exc,
        )


def _inspect_existing_publication_root(path: str) -> os.stat_result:
    current = "/"
    final_status: os.stat_result | None = None
    for component in path.split("/")[1:]:
        current = os.path.join(current, component)
        try:
            final_status = os.lstat(current)
        except OSError as exc:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
                f"cannot inspect publication root component: {current}",
                cause=exc,
            )
        if stat.S_ISLNK(final_status.st_mode) or not stat.S_ISDIR(
            final_status.st_mode
        ):
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
                f"publication root component is not a real directory: {current}",
            )
    if final_status is None:
        _reject(
            B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
            "publication root has no path components",
        )
    return final_status


def _normalize_planned_results(
    *,
    scheduled_inputs: Sequence[ledgers.B4ScheduledAttemptInput],
    planned_result_artifacts: Sequence[B4PlannedResultArtifact],
    inspect_absence: bool,
) -> tuple[B4PlannedResultArtifact, ...]:
    if type(planned_result_artifacts) not in (list, tuple):
        _reject(
            B4PrerunRejectionReason.PLANNED_RESULT_MAPPING_MISMATCH,
            "planned result artifacts must be one complete list or tuple",
        )
    normalized: list[B4PlannedResultArtifact] = []
    for item in planned_result_artifacts:
        if not isinstance(item, B4PlannedResultArtifact):
            _reject(
                B4PrerunRejectionReason.PLANNED_RESULT_MAPPING_MISMATCH,
                "planned result mapping contains a value of the wrong type",
            )
        if (
            type(item.attempt_id) is not str
            or not item.attempt_id
            or item.attempt_id.strip() != item.attempt_id
        ):
            _reject(
                B4PrerunRejectionReason.PLANNED_RESULT_MAPPING_MISMATCH,
                "planned result attempt_id is invalid",
            )
        path = _canonical_absolute_path(
            item.artifact_path,
            reason=B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
            label="planned result artifact_path",
        )
        normalized.append(B4PlannedResultArtifact(item.attempt_id, path))

    scheduled_ids = [item.attempt_id for item in scheduled_inputs]
    mapped_ids = [item.attempt_id for item in normalized]
    if (
        len(mapped_ids) != len(scheduled_ids)
        or len(set(mapped_ids)) != len(mapped_ids)
        or set(mapped_ids) != set(scheduled_ids)
    ):
        _reject(
            B4PrerunRejectionReason.PLANNED_RESULT_MAPPING_MISMATCH,
            "planned result attempt ids do not exactly match the scheduled batch",
        )
    paths = [item.artifact_path for item in normalized]
    if len(set(paths)) != len(paths):
        _reject(
            B4PrerunRejectionReason.PLANNED_RESULT_PATH_DUPLICATE,
            "planned result artifact paths are not unique",
        )
    paths_by_component = sorted(
        (tuple(path.split("/")[1:]), path) for path in paths
    )
    for (ancestor_components, ancestor), (
        descendant_components,
        descendant,
    ) in zip(paths_by_component, paths_by_component[1:]):
        if descendant_components[: len(ancestor_components)] == ancestor_components:
            _reject(
                B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
                "planned result artifact paths have a strict ancestor conflict: "
                f"{ancestor} and {descendant}",
            )
    result = tuple(sorted(normalized, key=lambda item: item.attempt_id))
    if inspect_absence:
        for item in result:
            _inspect_result_leaf_absent(item.artifact_path)
    return result


def _planned_result_payload(
    planned: Sequence[B4PlannedResultArtifact],
) -> list[dict[str, str]]:
    return [
        {
            "attempt_id": item.attempt_id,
            "result_artifact_path": item.artifact_path,
        }
        for item in planned
    ]


def _reject_fixed_artifact_conflicts(
    *,
    publication_root: str,
    planned: Sequence[B4PlannedResultArtifact],
) -> None:
    fixed_artifact_paths = tuple(
        os.path.join(publication_root, name)
        for name in (
            _REGISTRY_NAME,
            _MANIFEST_NAME,
            _RECEIPT_NAME,
            _RECEIPT_TEMP_NAME,
            B4_RAW_RECORD_REJECTIONS_NAME,
        )
    )
    for item in planned:
        path = item.artifact_path
        if path == publication_root or any(
            path == fixed_path or path.startswith(fixed_path + "/")
            for fixed_path in fixed_artifact_paths
        ):
            _reject(
                B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
                "a planned result path conflicts with an issuer publication path",
            )


def _issuer_commitment_payload(
    *,
    publication_root: str,
    registry_path: str,
    manifest_path: str,
    receipt_path: str,
    scheduled_inputs_sha256: str,
    scheduled_attempt_count: int,
    planned: Sequence[B4PlannedResultArtifact],
    seed_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": B4_ISSUER_COMMITMENT_SCHEMA_VERSION,
        "publication_root": publication_root,
        "registry_path": registry_path,
        "manifest_path": manifest_path,
        "receipt_path": receipt_path,
        "scheduled_inputs_sha256": scheduled_inputs_sha256,
        "scheduled_attempt_count": scheduled_attempt_count,
        "planned_result_artifacts": _planned_result_payload(planned),
        "seed_sha256": seed_sha256,
        "seed_source_kind": _SEED_SOURCE_KIND,
        "seed_byte_count": _SEED_BYTE_COUNT,
    }


def _seed_source_payload(
    *,
    seed_sha256: str,
    issuer_commitment_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": B4_SEED_SOURCE_SCHEMA_VERSION,
        "seed_sha256": seed_sha256,
        "issuer_commitment_sha256": issuer_commitment_sha256,
        "seed_source_kind": _SEED_SOURCE_KIND,
        "seed_byte_count": _SEED_BYTE_COUNT,
    }


def _artifact_descriptor(
    *,
    artifact_path: str,
    data: bytes,
    row_count: int,
) -> dict[str, object]:
    return {
        "schema_version": B4_ARTIFACT_DESCRIPTOR_SCHEMA_VERSION,
        "artifact_path": artifact_path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_count": len(data),
        "row_count": row_count,
    }


def _completeness_payload(
    value: ledgers.B4ManifestCompletenessReceipt,
) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "manifest_sha256": value.manifest_sha256,
        "registry_sha256": value.registry_sha256,
        "registry_prefix_sha256": value.registry_prefix_sha256,
        "schedule_issuer_sha256": value.schedule_issuer_sha256,
        "seed_issuer_sha256": value.seed_issuer_sha256,
        "row_count": value.row_count,
        "registry_violation_count": value.registry_violation_count,
    }


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write while publishing B-4 artifact")
        view = view[written:]


def _write_exclusive(root_fd: int, name: str, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(name, flags, 0o600, dir_fd=root_fd)
    try:
        _write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_all(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _read_relative(root_fd: int, name: str) -> bytes:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    fd = os.open(name, flags, dir_fd=root_fd)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(f"B-4 artifact is not a regular file: {name}")
        return _read_all(fd)
    finally:
        os.close(fd)


def _assert_root_identity(
    publication_root: str,
    parent_fd: int,
    root_name: str,
    root_fd: int,
    original_status: os.stat_result,
) -> None:
    try:
        path_status = os.lstat(publication_root)
        parent_entry_status = os.stat(
            root_name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        held_status = os.fstat(root_fd)
    except OSError as exc:
        _reject(
            B4PrerunRejectionReason.PUBLICATION_ROOT_CHANGED,
            "publication root cannot be re-inspected before receipt publication",
            cause=exc,
        )
    expected = (original_status.st_dev, original_status.st_ino)
    if (
        stat.S_ISLNK(path_status.st_mode)
        or not stat.S_ISDIR(path_status.st_mode)
        or (path_status.st_dev, path_status.st_ino) != expected
        or stat.S_ISLNK(parent_entry_status.st_mode)
        or not stat.S_ISDIR(parent_entry_status.st_mode)
        or (parent_entry_status.st_dev, parent_entry_status.st_ino) != expected
        or (held_status.st_dev, held_status.st_ino) != expected
    ):
        _reject(
            B4PrerunRejectionReason.PUBLICATION_ROOT_CHANGED,
            "publication root path or inode changed before receipt publication",
        )


def _publish_bundle(
    *,
    publication_root: str,
    registry_bytes: bytes,
    manifest_bytes: bytes,
    receipt_bytes: bytes,
    planned: Sequence[B4PlannedResultArtifact],
) -> None:
    parent_fd = -1
    root_fd = -1
    root_name = ""
    final_receipt_linked = False
    operation_error: B4PrerunIssuerError | OSError | None = None
    try:
        parent_fd, root_name = _open_validated_publication_parent(
            publication_root
        )
        try:
            os.mkdir(root_name, 0o700, dir_fd=parent_fd)
        except FileExistsError as exc:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_EXISTS,
                f"publication root was concurrently created: {publication_root}",
                cause=exc,
            )
        root_fd = os.open(
            root_name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        original_status = os.fstat(root_fd)
        _write_exclusive(root_fd, _REGISTRY_NAME, registry_bytes)
        _write_exclusive(root_fd, _MANIFEST_NAME, manifest_bytes)
        _write_exclusive(root_fd, _RECEIPT_TEMP_NAME, receipt_bytes)

        for item in planned:
            _inspect_result_leaf_absent(item.artifact_path)
        _assert_root_identity(
            publication_root,
            parent_fd,
            root_name,
            root_fd,
            original_status,
        )
        if _read_relative(root_fd, _REGISTRY_NAME) != registry_bytes:
            _reject(
                B4PrerunRejectionReason.ARTIFACT_MISMATCH,
                "registry bytes changed before final receipt publication",
            )
        if _read_relative(root_fd, _MANIFEST_NAME) != manifest_bytes:
            _reject(
                B4PrerunRejectionReason.ARTIFACT_MISMATCH,
                "manifest bytes changed before final receipt publication",
            )
        if _read_relative(root_fd, _RECEIPT_TEMP_NAME) != receipt_bytes:
            _reject(
                B4PrerunRejectionReason.ARTIFACT_MISMATCH,
                "receipt temp bytes changed before final publication",
            )

        os.link(
            _RECEIPT_TEMP_NAME,
            _RECEIPT_NAME,
            src_dir_fd=root_fd,
            dst_dir_fd=root_fd,
            follow_symlinks=False,
        )
        final_receipt_linked = True
    except (B4PrerunIssuerError, OSError) as exc:
        operation_error = exc

    if not final_receipt_linked:
        for fd in (root_fd, parent_fd):
            if fd < 0:
                continue
            try:
                os.close(fd)
            except OSError:
                pass
        if isinstance(operation_error, B4PrerunIssuerError):
            raise operation_error
        if operation_error is None:
            _reject(
                B4PrerunRejectionReason.PUBLICATION_IO_ERROR,
                "final receipt was not linked",
            )
        _reject(
            B4PrerunRejectionReason.PUBLICATION_IO_ERROR,
            "exclusive B-4 artifact publication failed before final commit",
            cause=operation_error,
        )

    postcommit_errors: list[OSError] = []
    try:
        os.unlink(_RECEIPT_TEMP_NAME, dir_fd=root_fd)
    except OSError as exc:
        postcommit_errors.append(exc)
    for fd in (root_fd, parent_fd):
        try:
            os.fsync(fd)
        except OSError as exc:
            postcommit_errors.append(exc)
    for fd in (root_fd, parent_fd):
        try:
            os.close(fd)
        except OSError as exc:
            postcommit_errors.append(exc)

    if postcommit_errors:
        _reject(
            B4PrerunRejectionReason.PUBLICATION_COMMIT_UNCERTAIN,
            "final receipt is visible but cleanup or durability confirmation failed; "
            "reload the publication root to determine its visible state",
            cause=postcommit_errors[0],
        )


def issue_b4_prerun_publication(
    *,
    scheduled_inputs: Sequence[ledgers.B4ScheduledAttemptInput],
    planned_result_artifacts: Sequence[B4PlannedResultArtifact],
    publication_root: str,
) -> B4PrerunPublication:
    """Issue exactly one B-4 pre-run publication under a new absolute root."""

    root = _canonical_absolute_path(
        publication_root,
        reason=B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
        label="publication_root",
    )
    _require_preregistered_publication_root(root)
    registry_path = os.path.join(root, _REGISTRY_NAME)
    manifest_path = os.path.join(root, _MANIFEST_NAME)
    receipt_path = os.path.join(root, _RECEIPT_NAME)

    try:
        scheduled_inputs_sha256 = ledgers.scheduled_attempts_sha256(scheduled_inputs)
    except (TypeError, ValueError, ledgers.B4LedgerError) as exc:
        _reject(
            B4PrerunRejectionReason.SCHEDULED_INPUTS_INVALID,
            "scheduled batch does not satisfy the B-4 ledger contract",
            cause=exc,
        )
    planned = _normalize_planned_results(
        scheduled_inputs=scheduled_inputs,
        planned_result_artifacts=planned_result_artifacts,
        inspect_absence=True,
    )
    _reject_fixed_artifact_conflicts(
        publication_root=root,
        planned=planned,
    )
    _ensure_new_publication_root(root)

    try:
        seed_bytes = secrets.token_bytes(32)
    except Exception as exc:
        _reject(
            B4PrerunRejectionReason.CSPRNG_FAILURE,
            "secrets.token_bytes failed",
            cause=exc,
        )
    if type(seed_bytes) is not bytes or len(seed_bytes) != _SEED_BYTE_COUNT:
        _reject(
            B4PrerunRejectionReason.CSPRNG_FAILURE,
            "secrets.token_bytes did not return exactly 32 bytes",
        )
    seed_sha256 = hashlib.sha256(seed_bytes).hexdigest()
    commitment = _issuer_commitment_payload(
        publication_root=root,
        registry_path=registry_path,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        scheduled_inputs_sha256=scheduled_inputs_sha256,
        scheduled_attempt_count=len(scheduled_inputs),
        planned=planned,
        seed_sha256=seed_sha256,
    )
    issuer_commitment_sha256 = hashlib.sha256(
        canonical_json_bytes(commitment)
    ).hexdigest()
    schedule_receipt = ledgers.B4ScheduleReceipt(
        schema_version=ledgers.B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
        issuer_sha256=issuer_commitment_sha256,
        scheduled_inputs_sha256=scheduled_inputs_sha256,
        scheduled_attempt_count=len(scheduled_inputs),
    )
    try:
        registry = ledgers.seal_scheduled_attempt_registry(
            scheduled_inputs=scheduled_inputs,
            schedule_receipt=schedule_receipt,
        )
        seed_source = _seed_source_payload(
            seed_sha256=seed_sha256,
            issuer_commitment_sha256=issuer_commitment_sha256,
        )
        seed_receipt = ledgers.B4RandomizationSeedRecord(
            schema_version=ledgers.B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
            seed_hex=seed_bytes.hex(),
            registry_prefix_sha256=registry.sealed_prefix_sha256,
            issuer_sha256=issuer_commitment_sha256,
            source_receipt_sha256=hashlib.sha256(
                canonical_json_bytes(seed_source)
            ).hexdigest(),
        )
        manifest_result = ledgers.generate_analysis_manifest(
            registry=registry,
            schedule_receipt=schedule_receipt,
            seed_receipt=seed_receipt,
        )
        if isinstance(manifest_result, ledgers.B4DesignNotFeasible):
            _reject(
                B4PrerunRejectionReason.DESIGN_NOT_FEASIBLE,
                "fewer than 201 eligible scheduled attempts",
            )
        manifest = manifest_result
        completeness = ledgers.assert_analysis_manifest_complete(
            registry=registry,
            manifest=manifest,
            schedule_receipt=schedule_receipt,
            seed_receipt=seed_receipt,
        )
    except B4PrerunIssuerError:
        raise
    except (TypeError, ValueError, ledgers.B4LedgerError) as exc:
        _reject(
            B4PrerunRejectionReason.LEDGER_CONTRACT_VIOLATION,
            "existing B-4 ledger rejected issuer-generated objects",
            cause=exc,
        )

    registry_bytes = registry.canonical_bytes
    manifest_bytes = manifest.canonical_bytes
    receipt = {
        "schema_version": B4_PRERUN_RECEIPT_SCHEMA_VERSION,
        "issuer_commitment": commitment,
        "issuer_commitment_sha256": issuer_commitment_sha256,
        "registry_artifact": _artifact_descriptor(
            artifact_path=registry_path,
            data=registry_bytes,
            row_count=len(registry_bytes.splitlines()),
        ),
        "manifest_artifact": _artifact_descriptor(
            artifact_path=manifest_path,
            data=manifest_bytes,
            row_count=len(manifest.rows),
        ),
        "seed_source": seed_source,
        "completeness": _completeness_payload(completeness),
        "non_guarantees": list(B4_PRERUN_NON_GUARANTEES),
    }
    receipt_bytes = canonical_json_bytes(receipt)
    _publish_bundle(
        publication_root=root,
        registry_bytes=registry_bytes,
        manifest_bytes=manifest_bytes,
        receipt_bytes=receipt_bytes,
        planned=planned,
    )
    return B4PrerunPublication(
        publication_root=root,
        registry_path=registry_path,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        issuer_commitment_sha256=issuer_commitment_sha256,
        planned_result_artifacts=planned,
        schedule_receipt=schedule_receipt,
        registry=registry,
        seed_receipt=seed_receipt,
        manifest=manifest,
        completeness=completeness,
        receipt_canonical_bytes=receipt_bytes,
        receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        non_guarantees=B4_PRERUN_NON_GUARANTEES,
    )


def _strict_receipt(data: bytes) -> dict[str, object]:
    if type(data) is not bytes or not data:
        _reject(
            B4PrerunRejectionReason.RECEIPT_SCHEMA_MISMATCH,
            "receipt must be non-empty bytes",
        )
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _reject(
            B4PrerunRejectionReason.RECEIPT_SCHEMA_MISMATCH,
            "receipt is not strict UTF-8 JSON",
            cause=exc,
        )
    expected = {
        "schema_version",
        "issuer_commitment",
        "issuer_commitment_sha256",
        "registry_artifact",
        "manifest_artifact",
        "seed_source",
        "completeness",
        "non_guarantees",
    }
    if (
        type(value) is not dict
        or set(value) != expected
        or value.get("schema_version") != B4_PRERUN_RECEIPT_SCHEMA_VERSION
        or canonical_json_bytes(value) != data
    ):
        _reject(
            B4PrerunRejectionReason.RECEIPT_SCHEMA_MISMATCH,
            "receipt key set, schema version, or canonical bytes mismatch",
        )
    if value["non_guarantees"] != list(B4_PRERUN_NON_GUARANTEES):
        _reject(
            B4PrerunRejectionReason.RECEIPT_SCHEMA_MISMATCH,
            "receipt non-guarantees are not the fixed B-4 set",
        )
    return value


def _validate_descriptor(
    value: object,
    *,
    expected_path: str,
    data: bytes,
    row_count: int,
) -> None:
    expected_keys = {
        "schema_version",
        "artifact_path",
        "sha256",
        "byte_count",
        "row_count",
    }
    if type(value) is not dict or set(value) != expected_keys:
        _reject(
            B4PrerunRejectionReason.ARTIFACT_MISMATCH,
            "artifact descriptor key set mismatch",
        )
    expected = _artifact_descriptor(
        artifact_path=expected_path,
        data=data,
        row_count=row_count,
    )
    if not _is_exact_typed_mapping(value, expected):
        _reject(
            B4PrerunRejectionReason.ARTIFACT_MISMATCH,
            f"artifact descriptor does not match bytes at {expected_path}",
        )


def _planned_from_commitment(value: object) -> tuple[B4PlannedResultArtifact, ...]:
    if type(value) is not list:
        _reject(
            B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
            "commitment planned results are not a list",
        )
    planned: list[B4PlannedResultArtifact] = []
    for item in value:
        if type(item) is not dict or set(item) != {
            "attempt_id",
            "result_artifact_path",
        }:
            _reject(
                B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
                "commitment planned result key set mismatch",
            )
        planned.append(
            B4PlannedResultArtifact(
                attempt_id=item["attempt_id"],
                artifact_path=item["result_artifact_path"],
            )
        )
    return tuple(planned)


def _validate_seed_source(
    value: object,
    *,
    seed_receipt: ledgers.B4RandomizationSeedRecord,
    issuer_commitment_sha256: object,
) -> None:
    if type(value) is not dict or set(value) != {
        "schema_version",
        "seed_sha256",
        "issuer_commitment_sha256",
        "seed_source_kind",
        "seed_byte_count",
    }:
        _reject(
            B4PrerunRejectionReason.SEED_SOURCE_MISMATCH,
            "seed source key set mismatch",
        )
    try:
        seed_bytes = bytes.fromhex(seed_receipt.seed_hex)
    except (TypeError, ValueError) as exc:
        _reject(
            B4PrerunRejectionReason.SEED_SOURCE_MISMATCH,
            "manifest seed is not valid hex",
            cause=exc,
        )
    expected = _seed_source_payload(
        seed_sha256=hashlib.sha256(seed_bytes).hexdigest(),
        issuer_commitment_sha256=issuer_commitment_sha256,
    )
    if not _is_exact_typed_mapping(value, expected):
        _reject(
            B4PrerunRejectionReason.SEED_SOURCE_MISMATCH,
            "seed source does not bind the manifest seed",
        )
    if seed_receipt.source_receipt_sha256 != hashlib.sha256(
        canonical_json_bytes(value)
    ).hexdigest():
        _reject(
            B4PrerunRejectionReason.SEED_SOURCE_MISMATCH,
            "manifest seed receipt does not bind the seed source payload",
        )


def load_b4_prerun_publication(publication_root: str) -> B4PrerunPublication:
    """Strictly reload and regenerate one B-4 issuer publication."""

    root = _canonical_absolute_path(
        publication_root,
        reason=B4PrerunRejectionReason.PUBLICATION_ROOT_INVALID,
        label="publication_root",
    )
    registry_path = os.path.join(root, _REGISTRY_NAME)
    manifest_path = os.path.join(root, _MANIFEST_NAME)
    receipt_path = os.path.join(root, _RECEIPT_NAME)
    root_fd = -1
    try:
        path_status = _inspect_existing_publication_root(root)
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        held_status = os.fstat(root_fd)
        if (path_status.st_dev, path_status.st_ino) != (
            held_status.st_dev,
            held_status.st_ino,
        ):
            _reject(
                B4PrerunRejectionReason.PUBLICATION_ROOT_CHANGED,
                "publication root changed while it was opened",
            )
        receipt_bytes = _read_relative(root_fd, _RECEIPT_NAME)
        registry_bytes = _read_relative(root_fd, _REGISTRY_NAME)
        manifest_bytes = _read_relative(root_fd, _MANIFEST_NAME)
    except B4PrerunIssuerError:
        raise
    except OSError as exc:
        _reject(
            B4PrerunRejectionReason.ARTIFACT_MISMATCH,
            "publication root is missing a required regular artifact",
            cause=exc,
        )
    finally:
        if root_fd >= 0:
            os.close(root_fd)

    receipt = _strict_receipt(receipt_bytes)
    try:
        registry = ledgers.load_scheduled_attempt_registry(registry_bytes)
        manifest = ledgers.load_analysis_manifest(manifest_bytes)
    except (TypeError, ValueError, ledgers.B4LedgerError) as exc:
        _reject(
            B4PrerunRejectionReason.ARTIFACT_MISMATCH,
            "registry or manifest is not accepted by its existing public loader",
            cause=exc,
        )
    _validate_descriptor(
        receipt["registry_artifact"],
        expected_path=registry_path,
        data=registry_bytes,
        row_count=len(registry_bytes.splitlines()),
    )
    _validate_descriptor(
        receipt["manifest_artifact"],
        expected_path=manifest_path,
        data=manifest_bytes,
        row_count=len(manifest.rows),
    )

    issuer_commitment_sha256 = receipt["issuer_commitment_sha256"]
    if not _is_sha256(issuer_commitment_sha256):
        _reject(
            B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
            "issuer commitment hash is invalid",
        )
    _validate_seed_source(
        receipt["seed_source"],
        seed_receipt=manifest.seed_receipt,
        issuer_commitment_sha256=issuer_commitment_sha256,
    )

    commitment = receipt["issuer_commitment"]
    expected_commitment_keys = {
        "schema_version",
        "publication_root",
        "registry_path",
        "manifest_path",
        "receipt_path",
        "scheduled_inputs_sha256",
        "scheduled_attempt_count",
        "planned_result_artifacts",
        "seed_sha256",
        "seed_source_kind",
        "seed_byte_count",
    }
    if type(commitment) is not dict or set(commitment) != expected_commitment_keys:
        _reject(
            B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
            "issuer commitment key set mismatch",
        )
    raw_planned = _planned_from_commitment(commitment["planned_result_artifacts"])
    planned = _normalize_planned_results(
        scheduled_inputs=registry.scheduled_attempts,
        planned_result_artifacts=raw_planned,
        inspect_absence=False,
    )
    _reject_fixed_artifact_conflicts(
        publication_root=root,
        planned=planned,
    )
    seed_bytes = bytes.fromhex(manifest.seed_receipt.seed_hex)
    expected_commitment = _issuer_commitment_payload(
        publication_root=root,
        registry_path=registry_path,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        scheduled_inputs_sha256=registry.schedule_receipt.scheduled_inputs_sha256,
        scheduled_attempt_count=len(registry.scheduled_attempts),
        planned=planned,
        seed_sha256=hashlib.sha256(seed_bytes).hexdigest(),
    )
    calculated_commitment_sha256 = hashlib.sha256(
        canonical_json_bytes(commitment)
    ).hexdigest()
    if (
        not _is_exact_typed_mapping(commitment, expected_commitment)
        or canonical_json_bytes(commitment) != canonical_json_bytes(
            expected_commitment
        )
        or calculated_commitment_sha256 != issuer_commitment_sha256
        or registry.schedule_receipt.issuer_sha256 != issuer_commitment_sha256
        or manifest.seed_receipt.issuer_sha256 != issuer_commitment_sha256
    ):
        _reject(
            B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
            "registry, manifest seed, paths, or planned results changed commitment",
        )

    try:
        completeness = ledgers.assert_analysis_manifest_complete(
            registry=registry,
            manifest=manifest,
            schedule_receipt=registry.schedule_receipt,
            seed_receipt=manifest.seed_receipt,
        )
    except (TypeError, ValueError, ledgers.B4LedgerError) as exc:
        _reject(
            B4PrerunRejectionReason.COMPLETENESS_MISMATCH,
            "manifest does not exactly regenerate from registry and seed",
            cause=exc,
        )
    if not _is_exact_typed_mapping(
        receipt["completeness"],
        _completeness_payload(completeness),
    ):
        _reject(
            B4PrerunRejectionReason.COMPLETENESS_MISMATCH,
            "receipt completeness fields do not match regeneration",
        )

    return B4PrerunPublication(
        publication_root=root,
        registry_path=registry_path,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        issuer_commitment_sha256=issuer_commitment_sha256,
        planned_result_artifacts=planned,
        schedule_receipt=registry.schedule_receipt,
        registry=registry,
        seed_receipt=manifest.seed_receipt,
        manifest=manifest,
        completeness=completeness,
        receipt_canonical_bytes=receipt_bytes,
        receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        non_guarantees=B4_PRERUN_NON_GUARANTEES,
    )


__all__ = [
    "B4_ARTIFACT_DESCRIPTOR_SCHEMA_VERSION",
    "B4_ISSUER_COMMITMENT_SCHEMA_VERSION",
    "B4_PRERUN_NON_GUARANTEES",
    "B4_PRERUN_RECEIPT_SCHEMA_VERSION",
    "B4_RAW_RECORD_REJECTIONS_NAME",
    "B4_SEED_SOURCE_SCHEMA_VERSION",
    "B4PlannedResultArtifact",
    "B4PrerunIssuerError",
    "B4PrerunPublication",
    "B4PrerunRejectionReason",
    "issue_b4_prerun_publication",
    "load_b4_prerun_publication",
]
