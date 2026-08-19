"""File-descriptor-relative I/O for submission-gate artifacts.

The repository root is the only path resolved by the caller.  A relative
artifact path is split without normalization, and every component is opened
from the directory descriptor that preceded it.  This keeps ``..`` and
symlink traversal out of the resolution path instead of trying to repair a
path after the operating system has resolved it.
"""

from __future__ import annotations

from contextlib import contextmanager
import errno
import os
import re
import secrets
import stat
from collections.abc import Iterator
from os import PathLike
from typing import Any


class SafeIOError(OSError):
    """A safe relative-I/O operation could not be completed."""


class UnsafeRelativePathError(ValueError):
    """The supplied artifact path is not a strict relative component list."""


_READ_CHUNK_BYTES = 1024 * 1024


def _relative_components(relative_path: str) -> tuple[str, ...]:
    """Validate and split a POSIX-style relative path without normalizing it."""

    if type(relative_path) is not str:
        raise TypeError("relative_path must be a built-in str")
    # Keep this check before splitting: an absolute path must never reach an
    # open call, even on a platform where a later dir_fd argument is ignored.
    if os.path.isabs(relative_path):
        raise UnsafeRelativePathError("relative_path must not be absolute")
    if "\x00" in relative_path:
        raise UnsafeRelativePathError("relative_path must not contain NUL")
    components = tuple(relative_path.split("/"))
    if any(component in {"", ".", ".."} for component in components):
        raise UnsafeRelativePathError(
            "relative_path components must not be empty, '.' or '..'"
        )
    return components


def _require_open_flags(*, directory: bool) -> int:
    """Return flags that include the mandatory no-follow protection."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    if type(nofollow) is not int or nofollow == 0:
        raise SafeIOError(
            errno.ENOTSUP,
            "O_NOFOLLOW is unavailable; refusing relative artifact I/O",
        )
    flags = os.O_RDONLY | nofollow
    if directory:
        directory_flag = getattr(os, "O_DIRECTORY", None)
        if type(directory_flag) is not int or directory_flag == 0:
            raise SafeIOError(
                errno.ENOTSUP,
                "O_DIRECTORY is unavailable; refusing relative artifact I/O",
            )
        flags |= directory_flag
    return flags


def _open_root(repository_root: str | PathLike[str]) -> int:
    flags = _require_open_flags(directory=True)
    try:
        root_fd = os.open(os.fspath(repository_root), flags)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"repository_root cannot be opened as a no-follow directory: {exc}",
        ) from exc
    try:
        root_stat = os.fstat(root_fd)
    except OSError as exc:
        os.close(root_fd)
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"repository_root descriptor cannot be stated: {exc}",
        ) from exc
    if not stat.S_ISDIR(root_stat.st_mode):
        os.close(root_fd)
        raise SafeIOError(errno.ENOTDIR, "repository_root is not a directory")
    return root_fd


def _open_directory_component(component: str, parent_fd: int) -> int:
    flags = _require_open_flags(directory=True)
    try:
        child_fd = os.open(component, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"relative directory component cannot be opened safely: {component!r}",
        ) from exc
    try:
        child_stat = os.fstat(child_fd)
    except OSError as exc:
        os.close(child_fd)
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"relative directory component cannot be stated: {component!r}",
        ) from exc
    if not stat.S_ISDIR(child_stat.st_mode):
        os.close(child_fd)
        raise SafeIOError(
            errno.ENOTDIR,
            f"relative path component is not a directory: {component!r}",
        )
    return child_fd


@contextmanager
def _open_parent_directory(
    repository_root: str | PathLike[str],
    components: tuple[str, ...],
) -> Iterator[tuple[int, str]]:
    """Open the root and all parent components, returning parent fd and leaf."""

    root_fd = _open_root(repository_root)
    opened = [root_fd]
    try:
        parent_fd = root_fd
        for component in components[:-1]:
            child_fd = _open_directory_component(component, parent_fd)
            opened.append(child_fd)
            parent_fd = child_fd
        yield parent_fd, components[-1]
    finally:
        for descriptor in reversed(opened):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _open_regular_target(parent_fd: int, leaf: str, flags: int) -> int:
    nonblock = getattr(os, "O_NONBLOCK", None)
    if type(nonblock) is not int or nonblock == 0:
        raise SafeIOError(
            errno.ENOTSUP,
            "O_NONBLOCK is unavailable; refusing relative target I/O",
        )
    flags |= nonblock
    try:
        descriptor = os.open(leaf, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"relative target cannot be opened safely: {leaf!r}",
        ) from exc
    try:
        target_stat = os.fstat(descriptor)
    except OSError as exc:
        os.close(descriptor)
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"relative target descriptor cannot be stated: {leaf!r}",
        ) from exc
    if not stat.S_ISREG(target_stat.st_mode):
        os.close(descriptor)
        raise SafeIOError(
            errno.EINVAL,
            f"relative target is not a regular file: {leaf!r}",
        )
    return descriptor


def _snapshot(stat_result: Any) -> tuple[int, int, int, int, int, int]:
    """Return metadata unaffected by the normal atime update caused by read."""

    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_mode,
        stat_result.st_size,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )


def _staging_prefix(leaf: str) -> str:
    return f".{leaf}.create-"


def _staging_candidates(parent_fd: int, leaf: str) -> list[str]:
    prefix = _staging_prefix(leaf)
    pattern = re.compile(re.escape(prefix) + r"[1-9][0-9]*-[0-9a-f]{16}")
    try:
        entries = os.listdir(parent_fd)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"relative parent directory cannot be listed safely: {leaf!r}",
        ) from exc
    candidates = [entry for entry in entries if entry.startswith(prefix)]
    if len(candidates) > 1 or any(
        pattern.fullmatch(entry) is None for entry in candidates
    ):
        raise SafeIOError(
            errno.EINVAL,
            f"ambiguous create-only staging entries for {leaf!r}",
        )
    return candidates


def _open_stage(parent_fd: int, stage_name: str, *, create: bool) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if type(nofollow) is not int or nofollow == 0:
        raise SafeIOError(
            errno.ENOTSUP,
            "O_NOFOLLOW is unavailable; refusing create-only staging I/O",
        )
    flags = os.O_RDWR | nofollow
    if create:
        flags |= os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(stage_name, flags, 0o600, dir_fd=parent_fd)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"create-only staging entry cannot be opened safely: {stage_name!r}",
        ) from exc
    try:
        stage_stat = os.fstat(descriptor)
    except OSError as exc:
        os.close(descriptor)
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"create-only staging entry cannot be stated: {stage_name!r}",
        ) from exc
    if (
        not stat.S_ISREG(stage_stat.st_mode)
        or stage_stat.st_uid != os.getuid()
        or stat.S_IMODE(stage_stat.st_mode) != 0o600
        or stage_stat.st_nlink != 1
    ):
        os.close(descriptor)
        raise SafeIOError(
            errno.EINVAL,
            f"create-only staging entry metadata is unsafe: {stage_name!r}",
        )
    return descriptor


def _read_stage_bytes(descriptor: int, expected: bytes, stage_name: str) -> None:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        total = 0
        while total <= len(expected):
            chunk = os.read(
                descriptor,
                min(_READ_CHUNK_BYTES, len(expected) + 1 - total),
            )
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        if b"".join(chunks) != expected:
            raise SafeIOError(
                errno.EINVAL,
                f"create-only staging bytes mismatch: {stage_name!r}",
            )
    except SafeIOError:
        raise
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"create-only staging read failed: {stage_name!r}",
        ) from exc


def _unlink_stage_if_same(
    parent_fd: int,
    stage_name: str,
    expected_identity: tuple[int, int],
) -> None:
    try:
        current = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"create-only staging entry cannot be restated: {stage_name!r}",
        ) from exc
    if (current.st_dev, current.st_ino) != expected_identity:
        raise SafeIOError(
            errno.EAGAIN,
            f"create-only staging entry changed: {stage_name!r}",
        )
    try:
        os.unlink(stage_name, dir_fd=parent_fd)
    except OSError as exc:
        raise SafeIOError(
            exc.errno or errno.EIO,
            f"create-only staging cleanup failed: {stage_name!r}",
        ) from exc


def read_relative_regular_bytes(
    repository_root: str | PathLike[str],
    relative_path: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read a regular file through a no-follow, directory-fd-relative path.

    No component is normalized.  Absolute paths, empty components, ``.`` and
    ``..`` are rejected before any repository-relative open is attempted.
    The descriptor is checked before and after the bounded read so a changing
    regular file is not silently accepted.
    """

    components = _relative_components(relative_path)
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError("max_bytes must be a non-negative built-in int")
    final_flags = _require_open_flags(directory=False)
    with _open_parent_directory(repository_root, components) as (parent_fd, leaf):
        descriptor = _open_regular_target(parent_fd, leaf, final_flags)
        try:
            try:
                before_stat = os.fstat(descriptor)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"relative target cannot be stated before read: {leaf!r}",
                ) from exc
            if before_stat.st_size > max_bytes:
                raise SafeIOError(
                    errno.EFBIG,
                    f"relative target exceeds the read limit: {leaf!r}",
                )

            result = bytearray()
            while True:
                remaining = max_bytes - len(result)
                try:
                    chunk = os.read(
                        descriptor,
                        min(_READ_CHUNK_BYTES, remaining + 1),
                    )
                except OSError as exc:
                    raise SafeIOError(
                        exc.errno or errno.EIO,
                        f"relative target read failed: {leaf!r}",
                    ) from exc
                if not chunk:
                    break
                result.extend(chunk)
                if len(result) > max_bytes:
                    raise SafeIOError(
                        errno.EFBIG,
                        f"relative target exceeds the read limit: {leaf!r}",
                    )

            try:
                after_stat = os.fstat(descriptor)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"relative target cannot be stated after read: {leaf!r}",
                ) from exc
            if not stat.S_ISREG(after_stat.st_mode):
                raise SafeIOError(
                    errno.EINVAL,
                    f"relative target changed away from a regular file: {leaf!r}",
                )
            if _snapshot(before_stat) != _snapshot(after_stat):
                raise SafeIOError(
                    errno.EAGAIN,
                    f"relative target changed while reading: {leaf!r}",
                )
            if len(result) != after_stat.st_size:
                raise SafeIOError(
                    errno.EIO,
                    f"relative target read size mismatch: {leaf!r}",
                )
            return bytes(result)
        finally:
            try:
                os.close(descriptor)
            except OSError:
                pass


def create_only_relative_bytes(
    repository_root: str | PathLike[str],
    relative_path: str,
    data: bytes,
) -> None:
    """Create and durably write exact bytes at a strict relative target.

    Creation is deliberately strict: an existing target is an error even if
    it contains identical bytes.  A receipt is unique to an attempt, so an
    idempotent-success rule would leave a mistaken retry path able to record
    the same receipt more than once.  Complete bytes are written to a
    no-follow ``O_EXCL`` staging file and published with a no-replace hard
    link from the already-open parent directory; the file and that directory
    are fsynced around publication.
    """

    components = _relative_components(relative_path)
    if type(data) is not bytes:
        raise TypeError("data must be a built-in bytes value")
    with _open_parent_directory(repository_root, components) as (parent_fd, leaf):
        # The no-replace link below is the sole target-existence decision.
        # Keeping it at the publication primitive makes the strict behavior
        # race-safe and ensures a mutation to idempotent success is observable
        # by the existing-target fixture.
        stages = _staging_candidates(parent_fd, leaf)

        stage_name = (
            stages[0]
            if stages
            else f"{_staging_prefix(leaf)}{os.getpid()}-{secrets.token_hex(8)}"
        )
        stage_descriptor = _open_stage(
            parent_fd,
            stage_name,
            create=not bool(stages),
        )
        try:
            if stages:
                _read_stage_bytes(stage_descriptor, data, stage_name)
            else:
                offset = 0
                while offset < len(data):
                    try:
                        written = os.write(stage_descriptor, data[offset:])
                    except OSError as exc:
                        raise SafeIOError(
                            exc.errno or errno.EIO,
                            f"create-only staging write failed: {stage_name!r}",
                        ) from exc
                    if written <= 0 or written > len(data) - offset:
                        raise SafeIOError(
                            errno.EIO,
                            "create-only staging made no valid write progress: "
                            f"{stage_name!r}",
                        )
                    offset += written

            try:
                after_write = os.fstat(stage_descriptor)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"create-only staging cannot be restated: {stage_name!r}",
                ) from exc
            if not stat.S_ISREG(after_write.st_mode) or after_write.st_size != len(data):
                raise SafeIOError(
                    errno.EIO,
                    f"create-only staging write size mismatch: {stage_name!r}",
                )
            stage_identity = (after_write.st_dev, after_write.st_ino)
            try:
                os.fsync(stage_descriptor)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"create-only staging fsync failed: {stage_name!r}",
                ) from exc

            try:
                os.link(
                    stage_name,
                    leaf,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    _unlink_stage_if_same(parent_fd, stage_name, stage_identity)
                    try:
                        os.fsync(parent_fd)
                    except OSError:
                        pass
                    raise SafeIOError(
                        errno.EEXIST,
                        f"create-only target already exists: {leaf!r}",
                    ) from exc
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"create-only target publication failed: {leaf!r}",
                ) from exc

            # Open the published final component again with O_NOFOLLOW and
            # fstat it.  This keeps the final-name contract explicit and
            # detects a namespace race before success.
            target_descriptor = _open_regular_target(
                parent_fd,
                leaf,
                _require_open_flags(directory=False),
            )
            try:
                target_stat = os.fstat(target_descriptor)
                if (target_stat.st_dev, target_stat.st_ino) != stage_identity:
                    raise SafeIOError(
                        errno.EAGAIN,
                        f"create-only target identity changed: {leaf!r}",
                    )
            finally:
                try:
                    os.close(target_descriptor)
                except OSError:
                    pass

            try:
                os.fsync(parent_fd)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    f"create-only parent directory fsync failed: {leaf!r}",
                ) from exc
            _unlink_stage_if_same(parent_fd, stage_name, stage_identity)
            try:
                os.fsync(parent_fd)
            except OSError as exc:
                raise SafeIOError(
                    exc.errno or errno.EIO,
                    "create-only parent directory fsync after publication "
                    f"failed: {leaf!r}",
                ) from exc
        finally:
            try:
                os.close(stage_descriptor)
            except OSError:
                pass
