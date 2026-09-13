# -*- coding: utf-8 -*-
"""Declaration-derived reference materialization for S8b source snapshots.

The producer materializes the pinned CCBench commit, template patch, canonical
predicate or comparator, and configuration in a separate disposable worktree.
Only an exact digest match admits the caller's materialized worktree.  The
admitted worktree is then made non-writable and becomes the snapshot from which
later source evidence is derived.

The production replay authority is the repository's own ``external/ccbench``
checkout, not Git metadata reachable through the candidate snapshot.  Git
replacement objects are disabled while the disposable reference is created.

Protection also removes write bits from the snapshot's parent directory and
checks the snapshot root's device/inode identity before and after the consumer
body.  That closes pathname replacement by an ordinary writer which honors the
protected modes.  It is not a sandbox boundary: the directory owner can restore
write permission, and a privileged actor can rename entries despite these mode
bits.  Those actors remain outside the guarantee made here.

This mechanism does not prove that the materializer itself is correct.  The
reference materialization passes through the same implementation, so a planted
behavior in that implementation can be reproduced on both sides.  It closes
only the path where the tree after materialization differs from the tree
derived from the declaration.  It does not claim dynamic predicate reachability
or any guarantee that is not exercised by these functions.

The additional sealed_build_session closes D966's build-time source replacement
(A->B->A) path with a private copy and a recursive read-only mount. It does not
close contaminated cache binary reuse. Its process-local capability is within
the trusted producer boundary, not kernel attestation or a digital signature;
it is not a security boundary against modification of Python process memory.
The clone3 ENOSYS fallback was measured on glibc 2.35, not on other libcs.
"""
from __future__ import annotations

import contextlib
import ctypes
import enum
import errno
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import time
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Mapping, Optional

from . import patchharness, source_digest


TREE_DIGEST_SCHEMA = b"s8b-materialized-tree/v1\x00"
# Entry names are explicit.  There is no gitignore, generic hidden-file, or
# suffix filter in snapshot_tree_digest().
TREE_DIGEST_EXCLUSIONS: frozenset[str] = frozenset({".git"})
_LOWER_HEX = frozenset("0123456789abcdef")


class ExpectedMaterializationError(RuntimeError):
    """The expected tree or immutable-snapshot contract could not be proven."""


@dataclass(frozen=True, slots=True, init=False)
class ExpectedMaterializationDescriptor:
    """Immutable declaration handed to the binary-producing build boundary.

    The descriptor carries the pin, selected configuration, exact freeze entry,
    and the template patch path derived from that entry.  The declaration is
    stored as canonical JSON rather than retaining a caller-owned mutable
    mapping.  It contains no observed tree digest: the build implementation
    must derive that value by replaying the declaration.
    """

    ccbench_commit: str
    configuration: str
    template_patch_path: Optional[str]
    declaration_sha256: str
    _declaration_json: str

    def __init__(
            self, *, ccbench_commit: str, configuration: str,
            declaration: Mapping[str, object],
            template_patch_path: Optional[os.PathLike[str] | str]) -> None:
        if type(ccbench_commit) is not str or not ccbench_commit:
            raise ExpectedMaterializationError(
                "build declaration is invalid (reason=commit count=1)"
            )
        if type(configuration) is not str or not configuration:
            raise ExpectedMaterializationError(
                "build declaration is invalid (reason=configuration count=1)"
            )
        if not isinstance(declaration, Mapping):
            raise ExpectedMaterializationError(
                "build declaration is invalid (reason=entry-type count=1)"
            )
        try:
            declaration_json = json.dumps(
                declaration, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            )
            patch = (
                os.fspath(template_patch_path)
                if template_patch_path is not None else None
            )
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ExpectedMaterializationError(
                "build declaration is not canonical JSON "
                "(reason=entry-json count=1)"
            ) from exc
        if patch is not None and (type(patch) is not str or not patch):
            raise ExpectedMaterializationError(
                "build declaration patch path is invalid "
                "(reason=template-patch-path count=1)"
            )
        object.__setattr__(self, "ccbench_commit", ccbench_commit)
        object.__setattr__(self, "configuration", configuration)
        object.__setattr__(self, "template_patch_path", patch)
        object.__setattr__(
            self, "declaration_sha256",
            hashlib.sha256(declaration_json.encode("utf-8")).hexdigest(),
        )
        object.__setattr__(self, "_declaration_json", declaration_json)

    @property
    def declaration(self) -> Mapping[str, object]:
        """Return a fresh JSON tree so callers cannot mutate the descriptor."""
        value = json.loads(self._declaration_json)
        if type(value) is not dict:  # pragma: no cover - constructor invariant
            raise ExpectedMaterializationError(
                "build declaration is invalid (reason=entry-type count=1)"
            )
        return value


@dataclass(frozen=True, slots=True)
class SnapshotPermissionState:
    """Original modes needed to dismantle one protected disposable snapshot."""

    root: str
    modes: tuple[tuple[str, int], ...]
    tree_digest: str
    parent: str = ""
    root_fd: int = -1
    parent_fd: int = -1


@dataclass(frozen=True, slots=True)
class AdmittedBuildSnapshot:
    """One declaration-matched, protected snapshot and its rederived evidence."""

    source_snapshot_sha256: str
    expected_materialization_sha256: str
    source_evidence: source_digest.SourceEvidence
    evolve_block_sources: tuple[tuple[str, str], ...] = ()


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _LOWER_HEX for character in value)
    )


def _root_path(root: os.PathLike[str] | str) -> Path:
    try:
        path = Path(root)
        info = path.lstat()
    except (TypeError, ValueError, OSError) as exc:
        raise ExpectedMaterializationError(
            "snapshot root is unavailable (reason=root-invalid count=1)"
        ) from exc
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink():
        raise ExpectedMaterializationError(
            "snapshot root is not a directory (reason=root-type count=1)"
        )
    return path


def _root_identity(root: Path) -> tuple[int, int]:
    """Return one non-symlink directory identity for the named snapshot root."""
    try:
        info = root.lstat()
    except OSError as exc:
        raise ExpectedMaterializationError(
            "snapshot root identity is unavailable "
            "(reason=root-identity-lstat count=1)"
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ExpectedMaterializationError(
            "snapshot root identity is not a directory "
            "(reason=root-identity-type count=1)"
        )
    return info.st_dev, info.st_ino


def _assert_root_identity(root: Path, expected: tuple[int, int], *, stage: str) -> None:
    if _root_identity(root) != expected:
        raise ExpectedMaterializationError(
            "snapshot root identity changed "
            f"(reason=root-identity-{stage} count=1)"
        )


def _repository_ccbench_authority() -> Path:
    """Return the repository-owned Git authority used by production replay."""
    return Path(__file__).resolve().parents[2] / "external" / "ccbench"


@contextlib.contextmanager
def _git_replacements_disabled() -> Iterator[None]:
    """Set Git's process environment switch and restore its exact prior state."""
    key = "GIT_NO_REPLACE_OBJECTS"
    missing = object()
    previous: object = os.environ.get(key, missing)
    os.environ[key] = "1"
    try:
        yield
    finally:
        if previous is missing:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(previous)


def _relative_bytes(relative: str) -> bytes:
    try:
        return os.fsencode(relative)
    except (TypeError, UnicodeError) as exc:
        raise ExpectedMaterializationError(
            "snapshot path is not encodable (reason=path-encoding count=1)"
        ) from exc


def _tree_entries(
        root: Path, directory: Path, relative_directory: str = "",
) -> Iterator[tuple[str, Path, os.stat_result]]:
    try:
        with os.scandir(directory) as scan:
            entries = sorted(list(scan), key=lambda item: os.fsencode(item.name))
    except OSError as exc:
        raise ExpectedMaterializationError(
            "snapshot tree cannot be enumerated (reason=scandir-failed count=1)"
        ) from exc
    for entry in entries:
        relative = (
            f"{relative_directory}/{entry.name}"
            if relative_directory else entry.name
        )
        if entry.name in TREE_DIGEST_EXCLUSIONS:
            continue
        path = root / relative
        try:
            info = path.lstat()
        except OSError as exc:
            raise ExpectedMaterializationError(
                "snapshot entry cannot be inspected (reason=lstat-failed count=1)"
            ) from exc
        yield relative, path, info
        if stat.S_ISDIR(info.st_mode):
            yield from _tree_entries(root, path, relative)


def _digest_field(hasher, value: bytes) -> None:
    hasher.update(len(value).to_bytes(8, "big"))
    hasher.update(value)


def _digest_regular_file(hasher, path: Path, info: os.stat_result) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ExpectedMaterializationError(
            "snapshot file cannot be opened (reason=file-open-failed count=1)"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ExpectedMaterializationError(
                "snapshot entry changed type (reason=file-type-race count=1)"
            )
        hasher.update(before.st_size.to_bytes(8, "big"))
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            hasher.update(chunk)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev, before.st_ino, before.st_mode, before.st_size,
            before.st_mtime_ns,
        ) == (
            after.st_dev, after.st_ino, after.st_mode, after.st_size,
            after.st_mtime_ns,
        )
        if total != before.st_size or not stable or (
                info.st_dev, info.st_ino, info.st_mode, info.st_size,
                info.st_mtime_ns,
        ) != (
                before.st_dev, before.st_ino, before.st_mode, before.st_size,
                before.st_mtime_ns,
        ):
            raise ExpectedMaterializationError(
                "snapshot file changed while hashing (reason=file-race count=1)"
            )
    except OSError as exc:
        raise ExpectedMaterializationError(
            "snapshot file cannot be read (reason=file-read-failed count=1)"
        ) from exc
    finally:
        os.close(descriptor)


def _declared_source_path(root: Path, source_rel: str) -> Path:
    if type(source_rel) is not str or not source_rel:
        raise ExpectedMaterializationError(
            "reference source path is invalid (reason=source-path count=1)"
        )
    relative = Path(source_rel)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != source_rel
    ):
        raise ExpectedMaterializationError(
            "reference source path is invalid (reason=source-path count=1)"
        )
    path = root / relative
    try:
        info = path.lstat()
    except OSError as exc:
        raise ExpectedMaterializationError(
            "reference source is unavailable (reason=source-lstat count=1)"
        ) from exc
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise ExpectedMaterializationError(
            "reference source type is invalid (reason=source-type count=1)"
        )
    return path


def _regular_file_sha256(path: Path) -> str:
    """Hash one held regular-file inode and reject an in-read bytes race."""
    descriptor = -1
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
        os, "O_NOFOLLOW", 0,
    )
    try:
        entry = path.lstat()
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if (
            stat.S_ISLNK(entry.st_mode)
            or not stat.S_ISREG(entry.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or (entry.st_dev, entry.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise ExpectedMaterializationError(
                "EVOLVE-BLOCK source type is invalid "
                "(reason=evolve-source-type count=1)"
            )
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns,
        ) == (
            after.st_dev, after.st_ino, after.st_size,
            after.st_mtime_ns, after.st_ctime_ns,
        )
        if total != before.st_size or not stable:
            raise ExpectedMaterializationError(
                "EVOLVE-BLOCK source changed while hashing "
                "(reason=evolve-source-race count=1)"
            )
        return digest.hexdigest()
    except ExpectedMaterializationError:
        raise
    except OSError as exc:
        raise ExpectedMaterializationError(
            "EVOLVE-BLOCK source bytes cannot be read "
            "(reason=evolve-source-read count=1)"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def snapshot_tree_digest(root: os.PathLike[str] | str) -> str:
    """Hash every tree entry except names in the explicit exclusion set.

    The preimage includes relative path bytes, node type, regular-file bytes,
    symlink targets, and mode bits other than write bits.  Write bits are
    intentionally normalized away, so making the same snapshot non-writable
    cannot change its digest.  Unsupported filesystem node types are rejected
    rather than silently skipped.
    """
    path = _root_path(root)
    hasher = hashlib.sha256(TREE_DIGEST_SCHEMA)
    for relative, entry_path, info in _tree_entries(path, path):
        relative_bytes = _relative_bytes(relative)
        normalized_mode = (
            stat.S_IMODE(info.st_mode) & ~0o222
        ).to_bytes(2, "big")
        if stat.S_ISDIR(info.st_mode):
            hasher.update(b"D")
            _digest_field(hasher, relative_bytes)
            hasher.update(normalized_mode)
        elif stat.S_ISREG(info.st_mode):
            hasher.update(b"F")
            _digest_field(hasher, relative_bytes)
            hasher.update(normalized_mode)
            _digest_regular_file(hasher, entry_path, info)
        elif stat.S_ISLNK(info.st_mode):
            try:
                target = os.fsencode(os.readlink(entry_path))
            except (OSError, UnicodeError) as exc:
                raise ExpectedMaterializationError(
                    "snapshot symlink cannot be read (reason=readlink-failed count=1)"
                ) from exc
            hasher.update(b"L")
            _digest_field(hasher, relative_bytes)
            _digest_field(hasher, target)
        else:
            raise ExpectedMaterializationError(
                "snapshot node type is unsupported (reason=node-type count=1)"
            )
    return hasher.hexdigest()


def assert_expected_materialization(
        snapshot_root: os.PathLike[str] | str, expected_digest: str,
) -> str:
    """Require the snapshot tree to match one exact declaration-derived digest."""
    if not _is_sha256(expected_digest):
        raise ExpectedMaterializationError(
            "expected digest is invalid (reason=digest-schema count=1)"
        )
    actual = snapshot_tree_digest(snapshot_root)
    if actual != expected_digest:
        raise ExpectedMaterializationError(
            "materialized tree differs from declaration "
            "(reason=tree-digest-mismatch count=1)"
        )
    return actual


def _all_permission_nodes(root: Path) -> list[tuple[Path, int]]:
    nodes: list[tuple[Path, int]] = []

    def visit(directory: Path) -> None:
        try:
            with os.scandir(directory) as scan:
                entries = sorted(list(scan), key=lambda item: os.fsencode(item.name))
        except OSError as exc:
            raise ExpectedMaterializationError(
                "snapshot permissions cannot be enumerated "
                "(reason=permission-scandir count=1)"
            ) from exc
        for entry in entries:
            path = directory / entry.name
            try:
                info = path.lstat()
            except OSError as exc:
                raise ExpectedMaterializationError(
                    "snapshot permission entry cannot be inspected "
                    "(reason=permission-lstat count=1)"
                ) from exc
            if stat.S_ISDIR(info.st_mode):
                visit(path)
            if stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode):
                nodes.append((path, stat.S_IMODE(info.st_mode)))
            elif not stat.S_ISLNK(info.st_mode):
                raise ExpectedMaterializationError(
                    "snapshot permission node type is unsupported "
                    "(reason=permission-node-type count=1)"
                )

    visit(root)
    nodes.append((root, stat.S_IMODE(root.lstat().st_mode)))
    return nodes


def _restore_permission_modes(
        modes: tuple[tuple[str, int], ...], *, root: Path, parent: Path,
        root_fd: int, parent_fd: int,
) -> int:
    """Restore through held directory fds so root pathname replacement is harmless."""
    failures = 0
    # Keep the parent directory protected until every descendant mode is back.
    for raw_path, mode in sorted(
            modes, key=lambda item: item[0].count(os.sep), reverse=True):
        try:
            if root_fd >= 0 and raw_path == os.fspath(root):
                os.fchmod(root_fd, mode)
            elif parent_fd >= 0 and raw_path == os.fspath(parent):
                os.fchmod(parent_fd, mode)
            elif root_fd >= 0:
                relative = Path(raw_path).relative_to(root)
                os.chmod(
                    relative.as_posix(), mode, dir_fd=root_fd,
                    follow_symlinks=False,
                )
            else:
                os.chmod(raw_path, mode, follow_symlinks=False)
        except (OSError, ValueError):
            failures += 1
    return failures


def _close_permission_anchors(*fds: int) -> int:
    failures = 0
    for descriptor in fds:
        if descriptor < 0:
            continue
        try:
            os.close(descriptor)
        except OSError:
            failures += 1
    return failures


def restore_snapshot_permissions(state: SnapshotPermissionState) -> None:
    """Restore original modes through held fds, then release both anchors."""
    if type(state) is not SnapshotPermissionState:
        raise TypeError("state must be exact SnapshotPermissionState")
    root = Path(state.root)
    parent = Path(state.parent) if state.parent else root.parent
    failures = _restore_permission_modes(
        state.modes, root=root, parent=parent,
        root_fd=state.root_fd, parent_fd=state.parent_fd,
    )
    failures += _close_permission_anchors(state.root_fd, state.parent_fd)
    if failures:
        raise ExpectedMaterializationError(
            "snapshot permissions could not be restored "
            f"(reason=permission-restore count={failures})"
        )


def make_snapshot_non_writable(
        snapshot_root: os.PathLike[str] | str,
) -> SnapshotPermissionState:
    """Protect the snapshot and its parent, preserving modes for exact rollback."""
    root = _root_path(snapshot_root)
    parent = _root_path(root.parent)
    root_fd = parent_fd = -1
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
        os, "O_DIRECTORY", 0,
    ) | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_fd = os.open(parent, flags)
        root_fd = os.open(root, flags)
        if (
            _root_identity(parent)
            != (os.fstat(parent_fd).st_dev, os.fstat(parent_fd).st_ino)
            or _root_identity(root)
            != (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
        ):
            raise ExpectedMaterializationError(
                "snapshot permission anchor identity changed "
                "(reason=permission-anchor-race count=1)"
            )
    except Exception:
        _close_permission_anchors(root_fd, parent_fd)
        raise
    try:
        before = snapshot_tree_digest(root)
        nodes = _all_permission_nodes(root)
        nodes.append((parent, stat.S_IMODE(parent.lstat().st_mode)))
        modes = tuple((os.fspath(path), mode) for path, mode in nodes)
    except Exception:
        _close_permission_anchors(root_fd, parent_fd)
        raise
    changed: list[tuple[str, int]] = []
    try:
        for raw_path, mode in sorted(modes, key=lambda item: item[0].count(os.sep),
                                     reverse=True):
            os.chmod(raw_path, mode & ~0o222, follow_symlinks=False)
            changed.append((raw_path, mode))
        writable = sum(
            1 for raw_path, _mode in modes
            if stat.S_IMODE(os.lstat(raw_path).st_mode) & 0o222
        )
        if writable:
            raise ExpectedMaterializationError(
                "snapshot remains writable "
                f"(reason=write-bits-remain count={writable})"
            )
        after = snapshot_tree_digest(root)
        if after != before:
            raise ExpectedMaterializationError(
                "snapshot changed while becoming non-writable "
                "(reason=readonly-digest-mismatch count=1)"
            )
    except Exception:
        failures = _restore_permission_modes(
            tuple(changed), root=root, parent=parent,
            root_fd=root_fd, parent_fd=parent_fd,
        )
        failures += _close_permission_anchors(root_fd, parent_fd)
        if failures:
            raise ExpectedMaterializationError(
                "snapshot protection failed and modes could not be restored "
                f"(reason=permission-rollback count={failures})"
            )
        raise
    return SnapshotPermissionState(
        root=os.fspath(root), modes=modes, tree_digest=before,
        parent=os.fspath(parent), root_fd=root_fd, parent_fd=parent_fd,
    )


def produce_expected_materialization_sha256(
        *, ccbench_commit: str, configuration: str,
        base_dir: os.PathLike[str] | str,
        template_patch: Optional[os.PathLike[str] | str] = None,
        implementation: Optional[str] = None,
        marker_id: Optional[str] = None,
        source_rel: Optional[str] = None,
        quarantine_fn: Optional[Callable] = None,
) -> str:
    """Independently materialize one normalized declaration and hash its tree."""
    if type(ccbench_commit) is not str or not ccbench_commit:
        raise ExpectedMaterializationError(
            "reference declaration is invalid (reason=commit count=1)"
        )
    if type(configuration) is not str or not configuration:
        raise ExpectedMaterializationError(
            "reference declaration is invalid (reason=configuration count=1)"
        )
    has_implementation = implementation is not None
    implementation_fields = (marker_id, source_rel, quarantine_fn)
    if has_implementation != all(value is not None for value in implementation_fields):
        raise ExpectedMaterializationError(
            "reference declaration is incomplete "
            "(reason=implementation-fields count=1)"
        )
    if has_implementation and template_patch is None:
        raise ExpectedMaterializationError(
            "reference declaration is incomplete (reason=template-patch count=1)"
        )
    if not has_implementation and any(value is not None for value in implementation_fields):
        raise ExpectedMaterializationError(
            "reference declaration is inconsistent "
            "(reason=unused-implementation-fields count=1)"
        )
    if has_implementation and (
            type(implementation) is not str
            or not implementation
            or type(marker_id) is not str
            or not marker_id
            or type(source_rel) is not str
            or not callable(quarantine_fn)):
        raise ExpectedMaterializationError(
            "reference declaration implementation is invalid "
            "(reason=implementation-types count=1)"
        )

    try:
        base = os.fspath(base_dir)
        patch = os.fspath(template_patch) if template_patch is not None else None
    except TypeError as exc:
        raise ExpectedMaterializationError(
            "reference declaration path is invalid (reason=path-type count=1)"
        ) from exc

    with _git_replacements_disabled():
        checkout = patchharness.checkout(ccbench_commit, base_dir=base)
        with checkout as reference_root, contextlib.ExitStack() as stack:
            if patch is not None:
                stack.enter_context(patchharness.applied(
                    patch, ccbench_commit, ccbench_dir=reference_root,
                ))
            if has_implementation:
                assert quarantine_fn is not None
                assert source_rel is not None
                source_path = _declared_source_path(
                    Path(reference_root), source_rel,
                )
                result, _base, reference_edited, _diff = quarantine_fn(
                    reference_root,
                    implementation,
                    marker_id=marker_id,
                    source_rel=source_rel,
                    write=True,
                )
                if getattr(result, "passed", None) is not True:
                    raise ExpectedMaterializationError(
                        "reference materialization was rejected "
                        "(reason=reference-quarantine count=1)"
                    )
                if type(reference_edited) is not str:
                    raise ExpectedMaterializationError(
                        "reference materialization returned invalid source "
                        "(reason=edited-source-type count=1)"
                    )
                _declared_source_path(Path(reference_root), source_rel)
                try:
                    materialized_source = source_path.read_bytes()
                    rendered_source = reference_edited.encode("utf-8")
                except (OSError, UnicodeError) as exc:
                    raise ExpectedMaterializationError(
                        "reference source cannot be read "
                        "(reason=source-read count=1)"
                    ) from exc
                if materialized_source != rendered_source:
                    raise ExpectedMaterializationError(
                        "reference source was not materialized exactly "
                        "(reason=source-write-mismatch count=1)"
                    )
            return snapshot_tree_digest(reference_root)


def _declaration_recipe(
        *, configuration: str, declaration: Mapping[str, object],
) -> dict[str, object]:
    """Derive the authoritative replay recipe without observing a source tree."""
    from . import axis_trigger_gating as gate_axis
    from . import p3_s4_loop as loop_axis
    from . import p3_s4_loop_sort as sort_axis
    from . import trigger_gate_binding

    if not isinstance(declaration, Mapping):
        raise ExpectedMaterializationError(
            "reference declaration is invalid (reason=entry-type count=1)"
        )
    if (
        "configuration" in declaration
        and declaration["configuration"] != configuration
    ):
        raise ExpectedMaterializationError(
            "reference declaration is inconsistent "
            "(reason=configuration-mismatch count=1)"
        )

    root = Path(__file__).resolve().parents[2]
    template_patch: Optional[Path] = None
    implementation: Optional[str] = None
    marker_id: Optional[str] = None
    source_rel: Optional[str] = None
    evolve_block_source_rel: Optional[str] = None
    quarantine_fn: Optional[Callable] = None

    if configuration in {"system_gate", "ident_all"}:
        raw = declaration.get("gate_predicate")
        if type(raw) is not str or not raw.strip():
            raise ExpectedMaterializationError(
                "reference declaration is invalid (reason=gate-predicate count=1)"
            )
        if not trigger_gate_binding.is_canonical_predicate(raw):
            raise ExpectedMaterializationError(
                "reference declaration is invalid "
                "(reason=gate-predicate-canonical count=1)"
            )
        implementation = trigger_gate_binding.canonicalize_predicate(raw)
        marker_id = gate_axis.MARKER_ID
        source_rel = gate_axis.SOURCE_REL
        evolve_block_source_rel = source_rel
        template_patch = root / "patches" / gate_axis.TEMPLATE_PATCH
        quarantine_fn = loop_axis.quarantine
    elif configuration == "sort_best":
        raw = declaration.get("comparator")
        if type(raw) is not str or not raw.strip():
            raise ExpectedMaterializationError(
                "reference declaration is invalid (reason=comparator count=1)"
            )
        implementation = raw
        marker_id = sort_axis.MARKER_ID
        source_rel = sort_axis.SOURCE_REL
        evolve_block_source_rel = source_rel
        template_patch = root / sort_axis.TEMPLATE_PATCH
        quarantine_fn = loop_axis.quarantine
    elif configuration == "backoff_fixed_best":
        template_patch = root / loop_axis.TEMPLATE_PATCH
        evolve_block_source_rel = loop_axis.SOURCE_REL
    elif configuration not in {"p2_2_flag_opt", "stock", "stock_common"}:
        raise ExpectedMaterializationError(
            "reference declaration is invalid (reason=configuration-set count=1)"
        )

    return {
        "template_patch": template_patch,
        "implementation": implementation,
        "marker_id": marker_id,
        "source_rel": source_rel,
        "quarantine_fn": quarantine_fn,
        "evolve_block_source_rel": evolve_block_source_rel,
    }


def template_patch_path_from_declaration(
        *, configuration: str, declaration: Mapping[str, object],
) -> Optional[str]:
    """Return the exact template patch path carried by a build descriptor."""
    recipe = _declaration_recipe(
        configuration=configuration, declaration=declaration,
    )
    patch = recipe["template_patch"]
    return None if patch is None else os.fspath(patch)


def expected_materialization_descriptor(
        *, ccbench_commit: str, configuration: str,
        declaration: Mapping[str, object],
) -> ExpectedMaterializationDescriptor:
    """Freeze one declaration for transfer to :func:`buildcache.build_v2`."""
    return ExpectedMaterializationDescriptor(
        ccbench_commit=ccbench_commit,
        configuration=configuration,
        declaration=declaration,
        template_patch_path=template_patch_path_from_declaration(
            configuration=configuration, declaration=declaration,
        ),
    )


def produce_expected_materialization_from_declaration(
        *, ccbench_commit: str, configuration: str,
        declaration: Mapping[str, object],
        base_dir: os.PathLike[str] | str,
) -> str:
    """Replay one S8b freeze declaration in a separate disposable worktree.

    ``configuration`` is the authoritative key used by ``binding_entry`` to
    select this declaration from the freeze entry map.  Production entries do
    not repeat that key in their bodies.  If a non-production caller supplies
    the redundant field, retain a strict consistency check without requiring
    it from the freeze shape.
    """
    recipe = _declaration_recipe(
        configuration=configuration, declaration=declaration,
    )

    return produce_expected_materialization_sha256(
        ccbench_commit=ccbench_commit,
        configuration=configuration,
        base_dir=base_dir,
        template_patch=recipe["template_patch"],
        implementation=recipe["implementation"],
        marker_id=recipe["marker_id"],
        source_rel=recipe["source_rel"],
        quarantine_fn=recipe["quarantine_fn"],
    )


@contextlib.contextmanager
def admitted_build_snapshot(
        *, ccbench_commit: str, configuration: str,
        declaration: Mapping[str, object], snapshot_root: os.PathLike[str] | str,
        genome, prepared_src_token: str, cxx: str,
) -> Iterator[AdmittedBuildSnapshot]:
    """Admit and protect the source snapshot used by one S8b build.

    This is deliberately not part of ``prepared_binding``.  A caller enters it
    only at the build boundary.  There are no injected callables or bypass
    switches: declaration replay, exact comparison, protection, and evidence
    rederivation always run in this order.  The snapshot remains non-writable
    until the caller leaves the context after consuming the build result.  Its
    parent remains non-writable over the same interval, and the named root must
    retain its original device/inode identity.  This is a discretionary-mode
    boundary, not protection against the owner restoring permission or a
    privileged actor replacing the pathname.
    """
    root = _root_path(snapshot_root)
    root_identity = _root_identity(root)
    expected_digest = produce_expected_materialization_from_declaration(
        ccbench_commit=ccbench_commit,
        configuration=configuration,
        declaration=declaration,
        base_dir=_repository_ccbench_authority(),
    )
    actual_digest = assert_expected_materialization(
        snapshot_root, expected_digest,
    )
    permission_state = make_snapshot_non_writable(snapshot_root)
    try:
        _assert_root_identity(root, root_identity, stage="before-build")
        if permission_state.tree_digest != actual_digest:
            raise ExpectedMaterializationError(
                "snapshot changed before protection completed "
                "(reason=pre-readonly-digest-mismatch count=1)"
            )
        try:
            evidence = source_digest.resolve_evidence(
                genome,
                ccbench_commit,
                ccbench_dir=os.fspath(snapshot_root),
                cxx=cxx,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise ExpectedMaterializationError(
                "non-writable snapshot evidence cannot be derived "
                "(reason=evidence-derivation count=1)"
            ) from exc
        if type(evidence) is not source_digest.SourceEvidence:
            raise ExpectedMaterializationError(
                "non-writable snapshot evidence is invalid "
                "(reason=evidence-type count=1)"
            )
        if evidence.src_token != prepared_src_token:
            raise ExpectedMaterializationError(
                "non-writable snapshot src_token differs from prepared result "
                "(reason=src-token-mismatch count=1)"
            )
        recipe = _declaration_recipe(
            configuration=configuration, declaration=declaration,
        )
        evolve_block_sources: tuple[tuple[str, str], ...] = ()
        source_rel = recipe["evolve_block_source_rel"]
        if source_rel is not None:
            source_path = _declared_source_path(root, source_rel)
            source_sha256 = _regular_file_sha256(source_path)
            evolve_block_sources = ((source_rel, source_sha256),)
        yield AdmittedBuildSnapshot(
            source_snapshot_sha256=actual_digest,
            expected_materialization_sha256=expected_digest,
            source_evidence=evidence,
            evolve_block_sources=evolve_block_sources,
        )
    finally:
        identity_error: Optional[ExpectedMaterializationError] = None
        try:
            _assert_root_identity(root, root_identity, stage="after-build")
        except ExpectedMaterializationError as exc:
            identity_error = exc
        restore_snapshot_permissions(permission_state)
        if identity_error is not None:
            raise identity_error


class SealedSnapshotProtectionKind(enum.Enum):
    SEALED_BUILD = "sealed-build"
    SEALED_CACHE_HIT = "sealed-cache-hit"


_CAPABILITY_SEAL = object()
# Strong references prevent recycled ids from authenticating another object.
_ISSUED_SNAPSHOT_CAPABILITIES: dict[int, tuple[object, int]] = {}


@dataclass(frozen=True, init=False)
class SealedSnapshotCapability:
    """Execution-derived value within the trusted producer's process boundary.

    This is neither kernel attestation nor a digital signature. The identity
    registry is not a security boundary against process memory modification or
    an adversarial Python interpreter. Pickle/JSON reconstruction is not issue.
    """

    kind: SealedSnapshotProtectionKind
    source_snapshot_sha256: str
    expected_materialization_sha256: str
    binary_sha256: str
    compiler_input_manifest_sha256: str

    def __init__(self, *, kind, source_snapshot_sha256,
                 expected_materialization_sha256, binary_sha256,
                 compiler_input_manifest_sha256, _seal=None):
        if _seal is not _CAPABILITY_SEAL:
            raise ExpectedMaterializationError("snapshot capability requires issue")
        for name, value in (
            ("kind", kind), ("source_snapshot_sha256", source_snapshot_sha256),
            ("expected_materialization_sha256", expected_materialization_sha256),
            ("binary_sha256", binary_sha256),
            ("compiler_input_manifest_sha256", compiler_input_manifest_sha256),
        ):
            object.__setattr__(self, name, value)


def validate_sealed_snapshot_capability(
        value: object, *, source_snapshot_sha256: str,
        expected_materialization_sha256: str, binary_sha256: str,
        compiler_input_manifest_sha256: str,
) -> SealedSnapshotCapability:
    """Require the issued object itself and all four exact digest bindings."""
    record = _ISSUED_SNAPSHOT_CAPABILITIES.get(id(value))
    if (type(value) is not SealedSnapshotCapability or record is None
            or record[0] is not value or record[1] != os.getpid()):
        raise ExpectedMaterializationError("snapshot capability was not issued")
    for name, expected in (
        ("source_snapshot_sha256", source_snapshot_sha256),
        ("expected_materialization_sha256", expected_materialization_sha256),
        ("binary_sha256", binary_sha256),
        ("compiler_input_manifest_sha256", compiler_input_manifest_sha256),
    ):
        if not _is_sha256(expected) or getattr(value, name) != expected:
            raise ExpectedMaterializationError("snapshot capability binding mismatch: " + name)
    return value


def _linux_call(number: int, *args) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    result = libc.syscall(ctypes.c_long(number), *args)
    if result == -1:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))
    return result


def _enter_snapshot_namespace() -> None:
    if platform.machine() != "x86_64":
        raise ExpectedMaterializationError("sealed snapshot requires Linux x86_64")
    uid, gid = os.getuid(), os.getgid()
    _linux_call(272, 0x10000000 | 0x00020000)
    for name, data in (("setgroups", "deny"), ("uid_map", f"{uid} {uid} 1"),
                       ("gid_map", f"{gid} {gid} 1")):
        Path("/proc/self/" + name).write_text(data + "\n")
    _linux_call(165, None, b"/", None, ctypes.c_ulong(16384 | 262144), None)


def _drop_snapshot_capabilities() -> None:
    for cap in range(int(Path("/proc/sys/kernel/cap_last_cap").read_text()) + 1):
        _linux_call(157, 24, cap, 0, 0, 0)
    _linux_call(157, 47, 4, 0, 0, 0)
    libc = ctypes.CDLL(None, use_errno=True)
    header = (ctypes.c_uint32 * 2)(0x20080522, 0)
    data = (ctypes.c_uint32 * 6)()
    if libc.capset(ctypes.byref(header), ctypes.byref(data)) == -1:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))
    _linux_call(157, 38, 1, 0, 0, 0)
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines())
    if (any(int(status[name], 16) for name in
            ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"))
            or int(status["NoNewPrivs"]) != 1):
        raise ExpectedMaterializationError("snapshot capability drop incomplete")


def _install_snapshot_seccomp() -> None:
    """Block namespace/mount bypasses including i386 and x32.

    clone3 ENOSYS fallback was measured on glibc 2.35 only; this makes no
    portability claim for other libc implementations.
    """
    class Instruction(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                    ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]

    class Program(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Instruction))]

    deny = 0x50000 | errno.EPERM
    rows = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e), (6, 0, 0, deny),
            (0x20, 0, 0, 0), (0x45, 0, 1, 0x40000000), (6, 0, 0, deny)]
    for number, verdict in ((435, 0x50000 | errno.ENOSYS), (308, deny),
                            (165, deny), (166, deny), (442, deny), (429, deny)):
        rows.extend(((0x15, 0, 1, number), (6, 0, 0, verdict)))
    for number in (56, 272):
        rows.extend(((0x15, 0, 3, number), (0x20, 0, 0, 16),
                     (0x45, 0, 1, 0x10020000), (6, 0, 0, deny), (0x20, 0, 0, 0)))
    rows.append((6, 0, 0, 0x7fff0000))
    instructions = (Instruction * len(rows))(*(Instruction(*row) for row in rows))
    program = Program(len(rows), instructions)
    _linux_call(317, 1, 0, ctypes.byref(program))


def _mount_snapshot(target: Path, mounts: list[Path], *, source=b"tmpfs",
                    filesystem=b"tmpfs", flags=0, data=None) -> None:
    _linux_call(165, source, os.fsencode(target), filesystem, ctypes.c_ulong(flags), data)
    mounts.append(target)


def _seal_snapshot_root(root: Path) -> None:
    attributes = (ctypes.c_uint64 * 4)(1, 0, 0, 0)
    _linux_call(442, -100, os.fsencode(root), 0x8000,
                ctypes.byref(attributes), ctypes.c_size_t(32))


def _snapshot_root_view(root: Path, expected: str, mounts: list[Path]) -> None:
    """Rebuild only the two-level source spine; bind its other branches by fd.

    Holding sibling directory inodes preserves late cache/staging creation.
    Only source bytes are copied; Git metadata is never copied or consulted.
    """
    ancestor = root.parent.parent
    if ancestor == Path("/"):
        raise ExpectedMaterializationError("snapshot needs a dedicated source ancestor")
    source_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    branches = []
    spine_modes = {p: stat.S_IMODE(p.stat().st_mode) for p in (ancestor, root.parent, root)}
    try:
        for directory, excluded in ((ancestor, root.parent), (root.parent, root)):
            for path in directory.iterdir():
                if path == excluded:
                    continue
                if path.is_symlink():
                    branches.append((path, -1, False, os.readlink(path)))
                else:
                    descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
                    branches.append((path, descriptor, path.is_dir(), None))
        # Size from the actual source enumeration, including per-node overhead.
        source = Path(f"/proc/self/fd/{source_fd}")
        size = 4 * 1024 * 1024 + sum(
            ((info.st_size + 4095) // 4096 + 2) * 4096
            for _, _, info in _tree_entries(source, source)
        )
        _mount_snapshot(ancestor, mounts, data=b"size=4m")
        root.parent.mkdir()
        root.mkdir()
        for path, descriptor, directory, link in branches:
            if link is not None:
                path.symlink_to(link)
                continue
            if directory:
                path.mkdir()
            else:
                path.touch()
            _mount_snapshot(path, mounts, source=os.fsencode(f"/proc/self/fd/{descriptor}"),
                            filesystem=None, flags=4096 | (16384 if directory else 0))
        _mount_snapshot(root, mounts, data=f"size={size}".encode())
        shutil.copytree(source, root, dirs_exist_ok=True, symlinks=True,
                        ignore=shutil.ignore_patterns(".git"))
        if snapshot_tree_digest(root) != expected:
            raise ExpectedMaterializationError("sealed snapshot copy digest mismatch")
        for path, mode in spine_modes.items():
            path.chmod(mode)
        _seal_snapshot_root(root)
    finally:
        os.close(source_fd)
        for _, descriptor, _, _ in branches:
            if descriptor >= 0:
                os.close(descriptor)


def _unmount_snapshot(mounts: list[Path]) -> None:
    # Never use MNT_DETACH: a busy mount is a failed session.
    failures = []
    for path in reversed(mounts):
        try:
            _linux_call(166, os.fsencode(path), 0)
        except OSError as exc:
            failures.append(exc)
    if failures:
        raise ExpectedMaterializationError("snapshot normal unmount failed") from failures[0]


def _send_snapshot_message(stream, message) -> None:
    stream.write(json.dumps(message, ensure_ascii=True) + "\n")
    stream.flush()


def _read_snapshot_message(stream):
    line = stream.readline()
    if not line:
        raise ExpectedMaterializationError("sealed snapshot child disconnected")
    message = json.loads(line)
    if "error" in message:
        raise ExpectedMaterializationError("sealed snapshot child: " + message["error"])
    return message


def _reap_snapshot_descendants() -> None:
    """The supervisor is a subreaper; ECHILD proves its descendant set empty.

    After the worker exits, orphaned grandchildren are adopted here, including
    processes which called setsid. Kill and reap them before ordinary unmount.
    """
    deadline = time.monotonic() + 10
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid:
            continue
        children = Path(f"/proc/self/task/{os.getpid()}/children").read_text().split()
        for child in children:
            try:
                os.kill(int(child), signal.SIGKILL)
            except ProcessLookupError:
                pass
        if time.monotonic() >= deadline:
            raise ExpectedMaterializationError("snapshot descendants did not terminate")
        time.sleep(0.01)


def _snapshot_worker(stream) -> None:
    _drop_snapshot_capabilities()
    _install_snapshot_seccomp()
    _send_snapshot_message(stream, {"ready": True})
    while True:
        request = _read_snapshot_message(stream)
        if request.get("finish"):
            return
        try:
            result = subprocess.run(request["argv"], cwd=request["cwd"], env=request["env"],
                                    timeout=request["timeout_s"], capture_output=True, text=True)
            _send_snapshot_message(stream, {"returncode": result.returncode,
                                           "stdout": result.stdout, "stderr": result.stderr})
        except subprocess.TimeoutExpired:
            # Exit the worker: the supervisor now owns and kills all descendants.
            raise ExpectedMaterializationError("snapshot command timed out")


def _snapshot_supervisor(connection, root: Path, expected: str) -> None:
    mounts: list[Path] = []
    stream = connection.makefile("rw")
    code = 1
    worker = None
    try:
        os.chdir("/")
        # No inherited directory/file anchors may keep mounts busy or leak into exec.
        for raw in os.listdir("/proc/self/fd"):
            descriptor = int(raw)
            if descriptor > 2 and descriptor != connection.fileno():
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        _enter_snapshot_namespace()
        _snapshot_root_view(root, expected, mounts)
        _linux_call(157, 36, 1, 0, 0, 0)  # PR_SET_CHILD_SUBREAPER
        worker = os.fork()
        if worker == 0:
            try:
                _snapshot_worker(stream)
                os._exit(0)
            except BaseException as exc:
                _send_snapshot_message(stream, {"error": str(exc)})
                os._exit(1)
        _, status = os.waitpid(worker, 0)
        worker = None
        _reap_snapshot_descendants()
        _unmount_snapshot(mounts)
        mounts.clear()
        if os.waitstatus_to_exitcode(status) != 0:
            raise ExpectedMaterializationError("snapshot worker exited abnormally")
        _send_snapshot_message(stream, {"finished": True, "unmounted": True,
                                       "descendants_reaped": True})
        code = 0
    except BaseException as exc:
        try:
            _send_snapshot_message(stream, {"error": str(exc)})
        except (OSError, ValueError):
            pass
    finally:
        if worker is not None:
            try:
                os.kill(worker, signal.SIGKILL)
                os.waitpid(worker, 0)
            except ProcessLookupError:
                pass
        try:
            _reap_snapshot_descendants()
            if mounts:
                _unmount_snapshot(mounts)
        except BaseException:
            code = 1
        os._exit(code)


class SealedBuildSession:
    """One sealed source session; issue is available only after context exit.

    Closes D966's build-time source replacement (A->B->A) path only, not
    contaminated cache binary reuse. Cache hits do not attest a historical
    protected build. Capability values live inside the trusted producer boundary,
    not a kernel attestation, signature, or Python memory security boundary.
    """

    def __init__(self, admitted: AdmittedBuildSnapshot):
        self.source_snapshot_sha256 = admitted.source_snapshot_sha256
        self.expected_materialization_sha256 = admitted.expected_materialization_sha256
        self.source_evidence = admitted.source_evidence
        self.evolve_block_sources = admitted.evolve_block_sources
        self._pid = None
        self._connection = None
        self._stream = None
        self._invalid = False
        self._finished = False
        self._completed = False
        self._defer_completion = False
        self._ran = False
        self._owner = os.getpid()
        self._permission_state = None
        self._root = None
        self._root_identity = None

    def _start(self, root: Path) -> None:
        if self._finished or self._invalid or self._root is not None:
            raise ExpectedMaterializationError("snapshot session cannot restart")
        self._root = root
        self._root_identity = _root_identity(root)
        self._permission_state = make_snapshot_non_writable(root)
        if self._permission_state.tree_digest != self.source_snapshot_sha256:
            raise ExpectedMaterializationError("snapshot changed before fork")
        _assert_root_identity(root, self._root_identity, stage="before-build")
        parent, child = socket.socketpair()
        try:
            # Check real OS tasks immediately before fork, not Python thread objects.
            if len(os.listdir("/proc/self/task")) != 1:
                raise ExpectedMaterializationError("snapshot fork requires exactly one OS thread")
            pid = os.fork()
        except BaseException:
            parent.close()
            child.close()
            raise
        if pid == 0:
            parent.close()
            _snapshot_supervisor(child, root, self.source_snapshot_sha256)
            os._exit(1)
        child.close()
        self._pid = pid
        self._connection = parent
        parent.settimeout(60)
        self._stream = parent.makefile("rw")
        if _read_snapshot_message(self._stream) != {"ready": True}:
            raise ExpectedMaterializationError("snapshot did not become ready")

    def run(self, argv, *, cwd, env, timeout_s) -> subprocess.CompletedProcess[str]:
        if (self._invalid or self._finished or self._stream is None
                or self._owner != os.getpid()):
            raise ExpectedMaterializationError("snapshot session cannot run")
        try:
            self._connection.settimeout(None if timeout_s is None else timeout_s + 15)
            args = [os.fspath(arg) for arg in argv]
            _send_snapshot_message(self._stream, {
                "argv": args,
                "cwd": os.getcwd() if cwd is None else os.path.abspath(os.fspath(cwd)),
                "env": dict(os.environ if env is None else env), "timeout_s": timeout_s,
            })
            result = _read_snapshot_message(self._stream)
            self._ran = True
            return subprocess.CompletedProcess(args, result["returncode"],
                                               result["stdout"], result["stderr"])
        except BaseException:
            self._invalid = True
            raise

    def _finish(self) -> None:
        if self._finished:
            return
        try:
            if self._stream is None:
                raise ExpectedMaterializationError("snapshot never started")
            self._connection.settimeout(30)
            if not self._invalid:
                _send_snapshot_message(self._stream, {"finish": True})
                result = _read_snapshot_message(self._stream)
                if result != {"finished": True, "unmounted": True, "descendants_reaped": True}:
                    raise ExpectedMaterializationError("snapshot cleanup incomplete")
            else:
                # EOF ends the worker and lets the supervisor reap/unmount normally.
                self._connection.shutdown(socket.SHUT_RDWR)
            _, status = os.waitpid(self._pid, 0)
            self._pid = None
            if self._invalid or os.waitstatus_to_exitcode(status) != 0:
                raise ExpectedMaterializationError("snapshot session failed")
        except BaseException:
            self._invalid = True
            raise
        finally:
            cleanup_error = None
            if self._connection is not None:
                try:
                    self._connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            for resource in (self._stream, self._connection):
                if resource is not None:
                    try:
                        resource.close()
                    except OSError as exc:
                        cleanup_error = exc
            if self._pid is not None:
                try:
                    os.waitpid(self._pid, 0)
                except OSError as exc:
                    cleanup_error = exc
                finally:
                    self._pid = None
            try:
                if self._root is not None:
                    _assert_root_identity(self._root, self._root_identity, stage="after-build")
            except BaseException:
                self._invalid = True
                raise
            finally:
                try:
                    if self._permission_state is not None:
                        restore_snapshot_permissions(self._permission_state)
                        self._permission_state = None
                except BaseException:
                    self._invalid = True
                    raise
                finally:
                    self._finished = True
            if cleanup_error is not None:
                self._invalid = True
                raise ExpectedMaterializationError("snapshot cleanup failed") from cleanup_error
        self._completed = not self._invalid and not self._defer_completion

    def issue(self, kind, *, binary_sha256,
              compiler_input_manifest_sha256) -> SealedSnapshotCapability:
        if (self._invalid or not self._completed or not self._finished
                or self._owner != os.getpid()):
            raise ExpectedMaterializationError("snapshot session is not complete")
        if type(kind) is not SealedSnapshotProtectionKind:
            raise ExpectedMaterializationError("snapshot protection kind must be exact enum")
        if ((kind is SealedSnapshotProtectionKind.SEALED_BUILD) != self._ran):
            raise ExpectedMaterializationError("snapshot protection kind differs from execution")
        if not _is_sha256(binary_sha256) or not _is_sha256(compiler_input_manifest_sha256):
            raise ExpectedMaterializationError("snapshot capability digest is invalid")
        value = SealedSnapshotCapability(
            kind=kind, source_snapshot_sha256=self.source_snapshot_sha256,
            expected_materialization_sha256=self.expected_materialization_sha256,
            binary_sha256=binary_sha256,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
            _seal=_CAPABILITY_SEAL,
        )
        _ISSUED_SNAPSHOT_CAPABILITIES[id(value)] = (value, os.getpid())
        return value


@contextlib.contextmanager
def sealed_build_session(
        *, ccbench_commit: str, configuration: str,
        declaration: Mapping[str, object], snapshot_root: os.PathLike[str] | str,
        genome, prepared_src_token: str, cxx: str,
) -> Iterator[SealedBuildSession]:
    """Add a private sealed view to the existing parent-side admission protocol.

    Evidence, chmod protection, root identity checks, and permission restoration
    all remain in the parent. The supervisor only mounts and cleans up; compiler
    execution occurs in its capability-free, seccomp-filtered child. No capability
    is issued until both this context and the nested admission context succeed.
    """
    session = None
    try:
        with admitted_build_snapshot(
            ccbench_commit=ccbench_commit, configuration=configuration,
            declaration=declaration, snapshot_root=snapshot_root, genome=genome,
            prepared_src_token=prepared_src_token, cxx=cxx,
        ) as admitted:
            session = SealedBuildSession(admitted)
            # The outer admission context still owns the original permissions.
            # Even an explicit early _finish cannot issue before it restores them.
            session._defer_completion = True
            try:
                session._start(Path(snapshot_root).absolute())
                yield session
            finally:
                session._finish()
                session._completed = False
        session._completed = True
    except BaseException:
        if session is not None:
            session._invalid = True
        raise
