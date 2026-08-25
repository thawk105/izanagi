# -*- coding: utf-8 -*-
"""Fail-closed integrity verification for the canonical Masstree fixture."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
from typing import Optional


FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "sort_swo_masstree"
)
MANIFEST_NAME = "SHA256SUMS"
PIN = "b3c5d054b66b08374d7a6ff5a0faeaf28b041a38"
_MANIFEST_LINE = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)")


@dataclass(frozen=True)
class FixtureHashMismatch:
    path: str
    expected_sha256: str
    actual_sha256: str


@dataclass(frozen=True)
class FixtureVerificationFailure:
    detail_code: str
    paths: tuple[str, ...] = ()
    missing_files: tuple[str, ...] = ()
    unregistered_files: tuple[str, ...] = ()
    hash_mismatches: tuple[FixtureHashMismatch, ...] = ()


@dataclass(frozen=True)
class VerifiedFixture:
    root: Path
    manifest_sha256: str
    files: tuple[tuple[str, str], ...]


def _fixture_inventory(root: Path) -> tuple[set[str], set[str]]:
    regular_files: set[str] = set()
    symlinks: set[str] = set()
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in (*directory_names, *file_names):
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks.add(relative)
            elif path.is_file():
                regular_files.add(relative)
    return regular_files, symlinks


def _parse_manifest(raw: bytes) -> Optional[tuple[tuple[str, str], ...]]:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return None
    if not text.endswith("\n"):
        return None
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _MANIFEST_LINE.fullmatch(line)
        if match is None:
            return None
        digest, relative = match.groups()
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or relative == MANIFEST_NAME
            or str(path) != relative
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            return None
        entries.append((relative, digest))
    paths = [path for path, _digest in entries]
    if not entries or paths != sorted(paths) or len(paths) != len(set(paths)):
        return None
    return tuple(entries)


def verify_sort_swo_masstree_fixture(
    root: os.PathLike[str] | str = FIXTURE_ROOT,
) -> VerifiedFixture | FixtureVerificationFailure:
    """Verify names, containment, file types, and SHA-256 without fallback."""
    fixture_root = Path(root)
    if fixture_root.is_symlink():
        return FixtureVerificationFailure("fixture-root-symlink")
    if not fixture_root.is_dir():
        return FixtureVerificationFailure("fixture-root-not-directory")
    try:
        root_realpath = fixture_root.resolve(strict=True)
        regular_files, symlinks = _fixture_inventory(fixture_root)
    except OSError:
        return FixtureVerificationFailure("fixture-filesystem-error")
    if symlinks:
        return FixtureVerificationFailure(
            "fixture-symlink-present", paths=tuple(sorted(symlinks)),
        )

    manifest_path = fixture_root / MANIFEST_NAME
    if MANIFEST_NAME not in regular_files:
        return FixtureVerificationFailure("fixture-manifest-not-regular-file")
    try:
        manifest_raw = manifest_path.read_bytes()
    except OSError:
        return FixtureVerificationFailure("fixture-filesystem-error")
    entries = _parse_manifest(manifest_raw)
    if entries is None:
        return FixtureVerificationFailure("fixture-manifest-invalid")

    declared = {path for path, _digest in entries}
    actual = regular_files - {MANIFEST_NAME}
    missing = tuple(sorted(declared - actual))
    unregistered = tuple(sorted(actual - declared))
    if missing or unregistered:
        return FixtureVerificationFailure(
            "fixture-file-set-mismatch",
            missing_files=missing,
            unregistered_files=unregistered,
        )

    mismatches: list[FixtureHashMismatch] = []
    for relative, expected in entries:
        candidate = fixture_root.joinpath(*PurePosixPath(relative).parts)
        try:
            candidate_realpath = candidate.resolve(strict=True)
            if not candidate_realpath.is_relative_to(root_realpath):
                return FixtureVerificationFailure(
                    "fixture-path-escapes-root", paths=(relative,),
                )
            actual_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError:
            return FixtureVerificationFailure(
                "fixture-filesystem-error", paths=(relative,),
            )
        if actual_digest != expected:
            mismatches.append(FixtureHashMismatch(
                relative, expected, actual_digest,
            ))
    if mismatches:
        return FixtureVerificationFailure(
            "fixture-sha256-mismatch", hash_mismatches=tuple(mismatches),
        )
    return VerifiedFixture(
        root=root_realpath,
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        files=entries,
    )


__all__ = [
    "FIXTURE_ROOT", "MANIFEST_NAME", "PIN", "FixtureHashMismatch",
    "FixtureVerificationFailure", "VerifiedFixture",
    "verify_sort_swo_masstree_fixture",
]
