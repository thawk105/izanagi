# -*- coding: utf-8 -*-
"""Small create-only byte store with no-follow reads.

This module is deliberately domain independent.  Callers choose an identity,
derive a claim path, and validate the returned bytes themselves.
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import secrets
import stat
from typing import Sequence


_NAMESPACE_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?")


class CreateOnlyStoreError(RuntimeError):
    """A create-only storage invariant failed."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


@dataclass(frozen=True, slots=True)
class CreateOnlyClaimResult:
    """The durable bytes at a claim path and whether this call created them."""

    data: bytes
    created: bool


def identity_claim_path(
    root: Path, *, namespace: str, identity: Sequence[str],
) -> Path:
    """Derive one flat claim path from an ordered identity tuple."""

    if type(namespace) is not str or _NAMESPACE_RE.fullmatch(namespace) is None:
        raise CreateOnlyStoreError("claim-namespace", "namespace is invalid")
    if type(identity) not in {tuple, list} or not identity:
        raise CreateOnlyStoreError(
            "claim-identity", "identity must be a non-empty string sequence",
        )
    checked: list[str] = []
    for index, value in enumerate(identity):
        if type(value) is not str or not value:
            raise CreateOnlyStoreError(
                "claim-identity", f"identity[{index}] is not a non-empty string",
            )
        checked.append(value)
    preimage = json.dumps(
        checked, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(preimage).hexdigest()
    return Path(root) / f"{namespace}-{digest}.json"


def _open_parent(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise CreateOnlyStoreError(
            "claim-platform-no-follow",
            "O_NOFOLLOW and O_DIRECTORY are required",
        )
    try:
        descriptor = os.open(os.fspath(path.parent), flags | nofollow | directory)
    except OSError as exc:
        code = "claim-root-no-follow" if exc.errno == errno.ELOOP else "claim-root-open"
        raise CreateOnlyStoreError(code, f"cannot open claim root: {exc}") from exc
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise CreateOnlyStoreError(
                "claim-root-not-directory", "claim root is not a directory",
            )
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _read_at(
    directory_descriptor: int, name: str, *, max_bytes: int,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as exc:
        code = "claim-no-follow" if exc.errno == errno.ELOOP else "claim-open"
        raise CreateOnlyStoreError(code, f"cannot open claim: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CreateOnlyStoreError(
                "claim-not-regular", "claim is not a regular file",
            )
        if metadata.st_size > max_bytes:
            raise CreateOnlyStoreError(
                "claim-too-large", f"claim exceeds {max_bytes} bytes",
            )
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            try:
                chunk = os.read(descriptor, min(65536, remaining))
            except OSError as exc:
                raise CreateOnlyStoreError(
                    "claim-read", f"cannot read claim: {exc}",
                ) from exc
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            raise CreateOnlyStoreError(
                "claim-too-large", f"claim exceeds {max_bytes} bytes",
            )
        return data
    finally:
        os.close(descriptor)


def read_claim_bytes(path: Path, *, max_bytes: int) -> bytes | None:
    """Read an existing regular claim without following the final path."""

    if type(max_bytes) is not int or max_bytes < 1:
        raise CreateOnlyStoreError("claim-read-limit", "max_bytes is invalid")
    checked = Path(path)
    directory_descriptor = _open_parent(checked)
    try:
        try:
            return _read_at(
                directory_descriptor, checked.name, max_bytes=max_bytes,
            )
        except CreateOnlyStoreError as exc:
            if exc.code == "claim-open" and isinstance(exc.__cause__, OSError):
                if exc.__cause__.errno == errno.ENOENT:
                    return None
            raise
    finally:
        os.close(directory_descriptor)


def claim_bytes(
    path: Path, payload: bytes, *, max_bytes: int,
) -> CreateOnlyClaimResult:
    """Atomically establish bytes at ``path`` without replacing an existing claim."""

    if type(payload) is not bytes:
        raise CreateOnlyStoreError("claim-payload", "payload must be exact bytes")
    if type(max_bytes) is not int or max_bytes < 1 or len(payload) > max_bytes:
        raise CreateOnlyStoreError(
            "claim-write-limit", f"payload exceeds the {max_bytes!r} byte limit",
        )
    checked = Path(path)
    directory_descriptor = _open_parent(checked)
    temporary_name = f".{checked.name}.tmp-{secrets.token_hex(16)}"
    temporary_created = False
    try:
        flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
        )
        try:
            temporary_descriptor = os.open(
                temporary_name, flags, 0o600, dir_fd=directory_descriptor,
            )
            temporary_created = True
        except OSError as exc:
            raise CreateOnlyStoreError(
                "claim-temp-create", f"cannot create temporary claim: {exc}",
            ) from exc
        try:
            offset = 0
            while offset < len(payload):
                try:
                    written = os.write(temporary_descriptor, payload[offset:])
                except OSError as exc:
                    raise CreateOnlyStoreError(
                        "claim-write", f"cannot write temporary claim: {exc}",
                    ) from exc
                if written <= 0:
                    raise CreateOnlyStoreError(
                        "claim-write", "temporary claim write made no progress",
                    )
                offset += written
            try:
                os.fsync(temporary_descriptor)
            except OSError as exc:
                raise CreateOnlyStoreError(
                    "claim-fsync", f"cannot fsync temporary claim: {exc}",
                ) from exc
        finally:
            os.close(temporary_descriptor)

        try:
            os.link(
                temporary_name,
                checked.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            existing = _read_at(
                directory_descriptor, checked.name, max_bytes=max_bytes,
            )
            return CreateOnlyClaimResult(data=existing, created=False)
        except OSError as exc:
            raise CreateOnlyStoreError(
                "claim-publish", f"cannot publish create-only claim: {exc}",
            ) from exc
        try:
            os.fsync(directory_descriptor)
        except OSError as exc:
            raise CreateOnlyStoreError(
                "claim-directory-fsync", f"cannot fsync claim root: {exc}",
            ) from exc
        return CreateOnlyClaimResult(data=payload, created=True)
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass
        os.close(directory_descriptor)
