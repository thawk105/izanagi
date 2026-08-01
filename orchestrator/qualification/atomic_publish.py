# -*- coding: utf-8 -*-
"""Crash-atomic create-only publication shared by T-126 shell entry points."""
from __future__ import annotations

import os
import re
import secrets
import stat
from pathlib import Path


class AtomicPublishError(RuntimeError):
    """A canonical target or abandoned staging entry is unsafe or contradictory."""


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish_bytes(
        path: Path, data: bytes, *, crash_boundary: str = "") -> Path:
    """Publish exact bytes via sibling staging, hard link, and directory fsync."""
    if type(data) is not bytes:
        raise TypeError("published data must be exact bytes")
    if path.is_symlink() or path.parent.is_symlink() or not path.parent.is_dir():
        raise AtomicPublishError("atomic publish namespace is unsafe")
    prefix = f".{path.name}.create-"
    pattern = re.compile(
        re.escape(prefix) + r"[1-9][0-9]*-[0-9a-f]{16}")
    abandoned = [
        entry for entry in path.parent.iterdir()
        if entry.name.startswith(prefix)]
    if (len(abandoned) > 1
            or any(pattern.fullmatch(entry.name) is None
                   for entry in abandoned)):
        raise AtomicPublishError("ambiguous abandoned create staging entries")
    stage = abandoned[0] if abandoned else None
    target_present = path.exists() or path.is_symlink()
    target_stat = path.lstat() if target_present else None
    stage_stat = stage.lstat() if stage is not None else None
    for current, expected_nlink in (
            (target_stat, 2 if stage is not None else 1),
            (stage_stat, 2 if target_present else 1)):
        if current is None:
            continue
        if (stat.S_ISLNK(current.st_mode)
                or not stat.S_ISREG(current.st_mode)
                or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o600
                or current.st_nlink != expected_nlink):
            raise AtomicPublishError(
                "publisher staging owner/mode/nlink mismatch")
    if stage is not None and target_present:
        if ((stage_stat.st_dev, stage_stat.st_ino)
                != (target_stat.st_dev, target_stat.st_ino)
                or stage.read_bytes() != path.read_bytes()):
            raise AtomicPublishError(
                "publisher staging target inode/bytes mismatch")
    if target_present and path.read_bytes() != data:
        raise AtomicPublishError(
            "existing canonical target differs or is partial")
    if stage is not None:
        if target_present:
            _fsync_directory(path.parent)
        stage.unlink()
        _fsync_directory(path.parent)
    if target_present:
        return path
    _fsync_directory(path.parent)
    staging = path.parent / (
        f"{prefix}{os.getpid()}-{secrets.token_hex(8)}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(staging, flags, 0o600)
    if crash_boundary == "after-open":
        os._exit(91)
    try:
        offset = 0
        while offset < len(data):
            limit = (
                1 if crash_boundary == "after-short-write" and offset == 0
                else len(data) - offset)
            written = os.write(fd, data[offset:offset + limit])
            if written <= 0:
                raise AtomicPublishError("atomic write made no progress")
            offset += written
            if crash_boundary == "after-short-write" and offset == 1:
                os._exit(92)
        os.fsync(fd)
        if crash_boundary == "after-fsync":
            os._exit(93)
    finally:
        os.close(fd)
    try:
        os.link(staging, path, follow_symlinks=False)
    except FileExistsError:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        existing = os.open(path, flags)
        try:
            chunks = []
            while True:
                block = os.read(existing, 1024 * 1024)
                if not block:
                    break
                chunks.append(block)
        finally:
            os.close(existing)
        if b"".join(chunks) != data:
            raise AtomicPublishError(
                "existing canonical target differs or is partial")
    if crash_boundary == "after-publish":
        os._exit(94)
    _fsync_directory(path.parent)
    staging.unlink()
    _fsync_directory(path.parent)
    return path
