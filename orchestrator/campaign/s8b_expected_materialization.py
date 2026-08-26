# -*- coding: utf-8 -*-
"""Declaration-derived reference materialization for S8b source snapshots.

The producer materializes the pinned CCBench commit, template patch, canonical
predicate or comparator, and configuration in a separate disposable worktree.
Only an exact digest match admits the caller's materialized worktree.  The
admitted worktree is then made non-writable and becomes the snapshot from which
later source evidence is derived.

This mechanism does not prove that the materializer itself is correct.  The
reference materialization passes through the same implementation, so a planted
behavior in that implementation can be reproduced on both sides.  It closes
only the path where the tree after materialization differs from the tree
derived from the declaration.  It does not claim dynamic predicate reachability
or any guarantee that is not exercised by these functions.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
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


@dataclass(frozen=True, slots=True)
class AdmittedBuildSnapshot:
    """One declaration-matched, protected snapshot and its rederived evidence."""

    source_snapshot_sha256: str
    expected_materialization_sha256: str
    source_evidence: source_digest.SourceEvidence


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


def restore_snapshot_permissions(state: SnapshotPermissionState) -> None:
    """Restore modes before the disposable worktree is reverted and removed."""
    if type(state) is not SnapshotPermissionState:
        raise TypeError("state must be exact SnapshotPermissionState")
    failures = 0
    for raw_path, mode in sorted(state.modes, key=lambda item: item[0].count(os.sep)):
        try:
            os.chmod(raw_path, mode, follow_symlinks=False)
        except OSError:
            failures += 1
    if failures:
        raise ExpectedMaterializationError(
            "snapshot permissions could not be restored "
            f"(reason=permission-restore count={failures})"
        )


def make_snapshot_non_writable(
        snapshot_root: os.PathLike[str] | str,
) -> SnapshotPermissionState:
    """Remove write bits throughout a snapshot and prove its tree digest is unchanged."""
    root = _root_path(snapshot_root)
    before = snapshot_tree_digest(root)
    nodes = _all_permission_nodes(root)
    modes = tuple((os.fspath(path), mode) for path, mode in nodes)
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
        failures = 0
        for raw_path, mode in sorted(changed, key=lambda item: item[0].count(os.sep)):
            try:
                os.chmod(raw_path, mode, follow_symlinks=False)
            except OSError:
                failures += 1
        if failures:
            raise ExpectedMaterializationError(
                "snapshot protection failed and modes could not be restored "
                f"(reason=permission-rollback count={failures})"
            )
        raise
    return SnapshotPermissionState(
        root=os.fspath(root), modes=modes, tree_digest=before,
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

    with patchharness.checkout(ccbench_commit, base_dir=base) as reference_root:
        with contextlib.ExitStack() as stack:
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
        template_patch = root / sort_axis.TEMPLATE_PATCH
        quarantine_fn = loop_axis.quarantine
    elif configuration == "backoff_fixed_best":
        template_patch = root / loop_axis.TEMPLATE_PATCH
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
    until the caller leaves the context after consuming the build result.
    """
    expected_digest = produce_expected_materialization_from_declaration(
        ccbench_commit=ccbench_commit,
        configuration=configuration,
        declaration=declaration,
        base_dir=snapshot_root,
    )
    actual_digest = assert_expected_materialization(
        snapshot_root, expected_digest,
    )
    permission_state = make_snapshot_non_writable(snapshot_root)
    try:
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
        yield AdmittedBuildSnapshot(
            source_snapshot_sha256=actual_digest,
            expected_materialization_sha256=expected_digest,
            source_evidence=evidence,
        )
    finally:
        restore_snapshot_permissions(permission_state)
