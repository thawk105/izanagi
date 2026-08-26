# -*- coding: utf-8 -*-
"""Production materialization for the pinned sort SWO dependency root.

The oracle owns the canonical manifest parser, exact inventory verifier, and
manifest pin.  This module only projects a live Masstree checkout into that
existing contract and proves that the live build root still has equivalent
tracked/config bytes.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

from . import sort_swo_oracle


_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_LEASE_PREFIX = ".sort-swo-dependency-"
_MANIFEST_NAME = "SHA256SUMS"
_MANIFEST_SEPARATOR = b"  "
_RESERVED_TRACKED_PATHS = frozenset({_MANIFEST_NAME, "PIN"})
_READ_CHUNK_SIZE = 64 * 1024


class CanonicalDependencyMaterialError(RuntimeError):
    """Fail-closed canonical materialization or two-root verification error."""

    def __init__(
            self, detail_code: str, *, path: Optional[Path] = None,
            generated_manifest_sha256: Optional[str] = None,
            expected_manifest_sha256: Optional[str] = None):
        parts = [detail_code]
        if generated_manifest_sha256 is not None:
            parts.append(
                f"generated_manifest_sha256={generated_manifest_sha256}"
            )
        if expected_manifest_sha256 is not None:
            parts.append(
                f"expected_manifest_sha256={expected_manifest_sha256}"
            )
        super().__init__(": ".join(parts))
        self.detail_code = detail_code
        self.path = path
        self.generated_manifest_sha256 = generated_manifest_sha256
        self.expected_manifest_sha256 = expected_manifest_sha256


@dataclass(frozen=True)
class CanonicalDependencyMaterial:
    root: Path
    lease_root: Path
    manifest_sha256: str
    config_sha256: str
    files: tuple[str, ...]
    source_root: Path
    head: str


@dataclass(frozen=True)
class CanonicalDependencyVerification:
    source_root: Path
    canonical_root: Path
    head: str
    tracked_paths: tuple[str, ...]
    manifest_sha256: str
    config_sha256: str


@dataclass(frozen=True)
class _GitSourceState:
    root: Path
    head: str
    tracked_paths: tuple[str, ...]


class _SourceDriftError(RuntimeError):
    pass


def _git_environment() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _run_git(root: Path, arguments: list[str], *, detail_code: str) -> bytes:
    try:
        completed = subprocess.run(
            [
                "git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
                "-c", "core.useReplaceRefs=false", "-C", str(root),
                *arguments,
            ],
            env=_git_environment(), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CanonicalDependencyMaterialError(
            detail_code, path=root,
        ) from exc
    if completed.returncode != 0:
        raise CanonicalDependencyMaterialError(detail_code, path=root)
    if completed.stderr:
        raise CanonicalDependencyMaterialError(
            "canonical-tracked-list-invalid", path=root,
        )
    return completed.stdout


def _canonical_source_root(source_root: Path) -> Path:
    try:
        unresolved = Path(source_root)
        metadata = unresolved.lstat()
        resolved = unresolved.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-source-unavailable", path=Path(source_root),
        ) from exc
    if (stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode)
            or resolved != unresolved.absolute()):
        raise CanonicalDependencyMaterialError(
            "canonical-source-invalid", path=unresolved,
        )
    return resolved


def _normalize_tracked_path(raw: bytes, *, root: Path) -> str:
    try:
        relative = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-tracked-list-invalid", path=root,
        ) from exc
    path = PurePosixPath(relative)
    if (
        not relative
        or relative in _RESERVED_TRACKED_PATHS
        or path.is_absolute()
        or "\\" in relative
        or "\r" in relative
        or "\n" in relative
        or str(path) != relative
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CanonicalDependencyMaterialError(
            "canonical-tracked-list-invalid", path=root,
        )
    return relative


def _probe_git_source(source_root: Path) -> _GitSourceState:
    root = _canonical_source_root(source_root)
    identity = _run_git(
        root, ["rev-parse", "--show-toplevel", "--verify", "HEAD"],
        detail_code="canonical-head-unavailable",
    )
    try:
        identity_text = identity.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-head-invalid", path=root,
        ) from exc
    lines = identity_text.splitlines()
    if len(lines) != 2 or _HEAD_RE.fullmatch(lines[1]) is None:
        raise CanonicalDependencyMaterialError(
            "canonical-head-invalid", path=root,
        )
    try:
        top_level = Path(lines[0]).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-head-invalid", path=root,
        ) from exc
    if top_level != root:
        raise CanonicalDependencyMaterialError(
            "canonical-git-root-mismatch", path=root,
        )

    tracked_raw = _run_git(
        root, ["ls-files", "--cached", "-z", "--"],
        detail_code="canonical-tracked-list-unavailable",
    )
    if not tracked_raw or not tracked_raw.endswith(b"\0"):
        raise CanonicalDependencyMaterialError(
            "canonical-tracked-list-invalid", path=root,
        )
    raw_entries = tracked_raw[:-1].split(b"\0")
    tracked = tuple(_normalize_tracked_path(raw, root=root) for raw in raw_entries)
    if not tracked or len(tracked) != len(set(tracked)):
        raise CanonicalDependencyMaterialError(
            "canonical-tracked-list-invalid", path=root,
        )
    return _GitSourceState(
        root=root, head=lines[1], tracked_paths=tuple(sorted(tracked)),
    )


def _file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode),
        metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns,
    )


def _read_root_file_with_identity(
        root: Path, relative: str,
) -> tuple[bytes, tuple[int, ...]]:
    parts = PurePosixPath(relative).parts
    directory_fds: list[int] = []
    file_fd = -1
    try:
        root_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        root_flags |= getattr(os, "O_CLOEXEC", 0)
        root_flags |= getattr(os, "O_NOFOLLOW", 0)
        root_fd = os.open(root, root_flags)
        directory_fds.append(root_fd)
        current_fd = root_fd
        for component in parts[:-1]:
            directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            directory_flags |= getattr(os, "O_CLOEXEC", 0)
            directory_flags |= getattr(os, "O_NOFOLLOW", 0)
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            directory_fds.append(current_fd)
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        file_flags |= getattr(os, "O_NOFOLLOW", 0)
        entry = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
        file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        before = os.fstat(file_fd)
        if (
            stat.S_ISLNK(entry.st_mode)
            or not stat.S_ISREG(entry.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or _file_identity(entry) != _file_identity(before)
        ):
            raise _SourceDriftError(relative)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, _READ_CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        if _file_identity(before) != _file_identity(after):
            raise _SourceDriftError(relative)
        return b"".join(chunks), _file_identity(after)
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def _read_root_file(root: Path, relative: str) -> bytes:
    payload, _identity = _read_root_file_with_identity(root, relative)
    return payload


def _read_source_file_with_identity(
        root: Path, relative: str,
) -> tuple[bytes, tuple[int, ...]]:
    try:
        return _read_root_file_with_identity(root, relative)
    except _SourceDriftError as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=root / relative,
        ) from exc
    except OSError as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-copy-failed", path=root / relative,
        ) from exc


def _read_source_file(root: Path, relative: str) -> bytes:
    payload, _identity = _read_source_file_with_identity(root, relative)
    return payload


def _source_file_identity(root: Path, relative: str) -> tuple[int, ...]:
    parts = PurePosixPath(relative).parts
    directory_fds: list[int] = []
    file_fd = -1
    try:
        root_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        root_flags |= getattr(os, "O_CLOEXEC", 0)
        root_flags |= getattr(os, "O_NOFOLLOW", 0)
        root_fd = os.open(root, root_flags)
        directory_fds.append(root_fd)
        current_fd = root_fd
        for component in parts[:-1]:
            directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            directory_flags |= getattr(os, "O_CLOEXEC", 0)
            directory_flags |= getattr(os, "O_NOFOLLOW", 0)
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            directory_fds.append(current_fd)
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        file_flags |= getattr(os, "O_NOFOLLOW", 0)
        entry = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
        file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        opened = os.fstat(file_fd)
        if (
            stat.S_ISLNK(entry.st_mode)
            or not stat.S_ISREG(entry.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or _file_identity(entry) != _file_identity(opened)
        ):
            raise _SourceDriftError(relative)
        return _file_identity(opened)
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def _assert_source_file_identity(
        root: Path, relative: str, expected: tuple[int, ...],
) -> None:
    try:
        observed = _source_file_identity(root, relative)
    except (OSError, _SourceDriftError) as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=root / relative,
        ) from exc
    if observed != expected:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=root / relative,
        )


def _write_private_file(root: Path, relative: str, payload: bytes) -> None:
    destination = root.joinpath(*PurePosixPath(relative).parts)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
    finally:
        os.close(descriptor)


def _validated_lease_parent(parent: Path) -> Path:
    try:
        unresolved = Path(parent)
        metadata = unresolved.lstat()
        resolved = unresolved.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-root-create-failed", path=Path(parent),
        ) from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or resolved != unresolved.absolute()
        or metadata.st_uid != os.geteuid()
    ):
        raise CanonicalDependencyMaterialError(
            "canonical-root-create-failed", path=unresolved,
        )
    return resolved


def _same_git_state(left: _GitSourceState, right: _GitSourceState) -> bool:
    return (
        left.root == right.root
        and left.head == right.head
        and left.tracked_paths == right.tracked_paths
    )


def _canonical_payloads(
        source_payloads: dict[str, bytes], head: str,
) -> dict[str, bytes]:
    payloads = dict(source_payloads)
    payloads["PIN"] = f"{head}\n".encode("ascii")
    return payloads


def _manifest_paths(payloads: dict[str, bytes]) -> tuple[str, ...]:
    return tuple(sorted(payloads))


def _render_manifest(payloads: dict[str, bytes]) -> bytes:
    return b"".join(
        hashlib.sha256(payloads[relative]).hexdigest().encode("ascii")
        + _MANIFEST_SEPARATOR + relative.encode("utf-8") + b"\n"
        for relative in _manifest_paths(payloads)
    )


def assert_source_matches_canonical(
        source_root: Path, canonical_root: Path, *, expected_head: str,
        expected_manifest_sha256: Optional[str] = None,
) -> CanonicalDependencyVerification:
    """Verify canonical exactness and live source bytes as two distinct roots."""
    if type(expected_head) is not str or _HEAD_RE.fullmatch(expected_head) is None:
        raise CanonicalDependencyMaterialError(
            "canonical-head-invalid", path=Path(source_root),
        )
    try:
        verified = sort_swo_oracle._verify_dependency_root(Path(canonical_root))
    except sort_swo_oracle._DependencyVerificationError as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-verification-failed", path=Path(canonical_root),
        ) from exc
    if (
        expected_manifest_sha256 is not None
        and verified.manifest_sha256 != expected_manifest_sha256
    ):
        raise CanonicalDependencyMaterialError(
            "canonical-manifest-mismatch", path=verified.root,
            generated_manifest_sha256=verified.manifest_sha256,
            expected_manifest_sha256=expected_manifest_sha256,
        )

    before = _probe_git_source(Path(source_root))
    if before.head != expected_head:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=before.root,
        )
    canonical_hashes = dict(verified.files)
    declared_without_pin = set(canonical_hashes) - {"PIN"}
    expected_declared = set(before.tracked_paths) | {"config.h"}
    if declared_without_pin != expected_declared:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=before.root,
        )
    try:
        pin_bytes = sort_swo_oracle._read_verified_dependency_file(
            verified.root, "PIN", canonical_hashes["PIN"],
        )
    except (KeyError, sort_swo_oracle._DependencyVerificationError) as exc:
        raise CanonicalDependencyMaterialError(
            "canonical-verification-failed", path=verified.root,
        ) from exc
    if pin_bytes != f"{before.head}\n".encode("ascii"):
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=before.root,
        )
    source_identities: dict[str, tuple[int, ...]] = {}
    for relative in sorted(declared_without_pin):
        source_bytes, source_identity = _read_source_file_with_identity(
            before.root, relative,
        )
        source_identities[relative] = source_identity
        if hashlib.sha256(source_bytes).hexdigest() != canonical_hashes[relative]:
            raise CanonicalDependencyMaterialError(
                "canonical-source-drift", path=before.root / relative,
            )
    after = _probe_git_source(before.root)
    if not _same_git_state(before, after):
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=before.root,
        )
    for relative in sorted(source_identities):
        _assert_source_file_identity(
            before.root, relative, source_identities[relative],
        )
    return CanonicalDependencyVerification(
        source_root=before.root,
        canonical_root=verified.root,
        head=before.head,
        tracked_paths=before.tracked_paths,
        manifest_sha256=verified.manifest_sha256,
        config_sha256=verified.config_sha256,
    )


def materialize_canonical_dependency(
        source_root: Path, *, lease_parent: Path, expected_head: str,
) -> CanonicalDependencyMaterial:
    """Project tracked files, config.h, and generated PIN into a pinned root."""
    initial = _probe_git_source(Path(source_root))
    if type(expected_head) is not str or initial.head != expected_head:
        raise CanonicalDependencyMaterialError(
            "canonical-source-drift", path=initial.root,
        )
    parent = _validated_lease_parent(Path(lease_parent))
    lease_root: Optional[Path] = None
    manifest_sha256: Optional[str] = None
    try:
        try:
            lease_root = Path(tempfile.mkdtemp(prefix=_LEASE_PREFIX, dir=parent))
            lease_root.chmod(0o700)
            generated = lease_root / "generated"
            generated.mkdir(mode=0o700)
        except OSError as exc:
            raise CanonicalDependencyMaterialError(
                "canonical-root-create-failed", path=parent,
            ) from exc

        source_payloads = {
            relative: _read_source_file(initial.root, relative)
            for relative in initial.tracked_paths
        }
        source_payloads["config.h"] = _read_source_file(
            initial.root, "config.h",
        )
        payloads = _canonical_payloads(source_payloads, initial.head)
        manifest = _render_manifest(payloads)
        manifest_sha256 = hashlib.sha256(manifest).hexdigest()
        try:
            for relative in sorted(payloads):
                _write_private_file(generated, relative, payloads[relative])
            _write_private_file(generated, _MANIFEST_NAME, manifest)
        except OSError as exc:
            raise CanonicalDependencyMaterialError(
                "canonical-root-create-failed", path=generated,
            ) from exc

        canonical = lease_root / "canonical"
        try:
            verified = sort_swo_oracle._prepare_verified_dependency(
                generated, canonical,
            )
        except sort_swo_oracle._DependencyVerificationError as exc:
            if exc.detail_code == "dependency-manifest-not-canonical":
                raise CanonicalDependencyMaterialError(
                    "canonical-manifest-mismatch", path=generated,
                    generated_manifest_sha256=manifest_sha256,
                    expected_manifest_sha256=(
                        sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
                    ),
                ) from exc
            raise CanonicalDependencyMaterialError(
                "canonical-verification-failed", path=generated,
            ) from exc

        verification = assert_source_matches_canonical(
            initial.root, verified.root, expected_head=initial.head,
            expected_manifest_sha256=verified.manifest_sha256,
        )
        try:
            shutil.rmtree(generated)
        except OSError as exc:
            raise CanonicalDependencyMaterialError(
                "canonical-root-create-failed", path=generated,
            ) from exc
        return CanonicalDependencyMaterial(
            root=verified.root,
            lease_root=lease_root,
            manifest_sha256=verification.manifest_sha256,
            config_sha256=verification.config_sha256,
            files=tuple(relative for relative, _digest in verified.files),
            source_root=initial.root,
            head=initial.head,
        )
    except BaseException:
        if lease_root is not None:
            shutil.rmtree(lease_root, ignore_errors=True)
        raise


def cleanup_canonical_dependency(material: CanonicalDependencyMaterial) -> None:
    """Remove only the exact random lease returned by this materializer."""
    if not isinstance(material, CanonicalDependencyMaterial):
        raise TypeError("material must be CanonicalDependencyMaterial")
    lease = material.lease_root
    if (
        lease.name.startswith(_LEASE_PREFIX)
        and material.root == lease / "canonical"
        and lease.exists()
        and not lease.is_symlink()
    ):
        shutil.rmtree(lease, ignore_errors=True)


__all__ = [
    "CanonicalDependencyMaterial",
    "CanonicalDependencyMaterialError",
    "CanonicalDependencyVerification",
    "assert_source_matches_canonical",
    "cleanup_canonical_dependency",
    "materialize_canonical_dependency",
]
