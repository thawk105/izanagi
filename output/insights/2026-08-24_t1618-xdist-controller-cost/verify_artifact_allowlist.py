#!/usr/bin/env python3
"""Regenerate or verify the T-1618 durable artifact allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


DIRECTORY = Path(__file__).resolve().parent
ALLOWLIST = DIRECTORY / "artifact-allowlist.json"
SCHEMA_VERSION = "t1618-artifact-allowlist/v3"
ALLOWLIST_NAME = ALLOWLIST.name
HASH_CHUNK_BYTES = 1024 * 1024


class AllowlistError(RuntimeError):
    """A fail-closed allowlist error."""


def _repository_root() -> Path:
    completed = subprocess.run(
        ["git", "-C", str(DIRECTORY), "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git rev-parse failed"
        raise AllowlistError(detail)
    return Path(completed.stdout.strip()).resolve()


def _tracked_root(repository_root: Path) -> str:
    try:
        return DIRECTORY.relative_to(repository_root).as_posix()
    except ValueError as exc:
        raise AllowlistError(f"artifact directory is outside repository: {DIRECTORY}") from exc


def _candidate_files(repository_root: Path, tracked_root: str) -> dict[str, Path]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            tracked_root,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise AllowlistError(detail or "git ls-files failed")

    candidates: dict[str, Path] = {}
    prefix = tracked_root + "/"
    for encoded_path in completed.stdout.split(b"\0"):
        if not encoded_path:
            continue
        repository_relative = encoded_path.decode("utf-8")
        if not repository_relative.startswith(prefix):
            raise AllowlistError(f"candidate escaped tracked root: {repository_relative}")
        relative = repository_relative[len(prefix) :]
        path = repository_root / repository_relative
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            # A deleted tracked path remains a candidate so verification reports it.
            candidates[relative] = path
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise AllowlistError(f"candidate is not a regular file: {relative}")
        candidates[relative] = path
    return candidates


def _file_identity(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(HASH_CHUNK_BYTES):
                digest.update(chunk)
                byte_count += len(chunk)
    except OSError as exc:
        raise AllowlistError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest(), byte_count


def _load_allowlist() -> dict[str, Any]:
    try:
        value = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AllowlistError(f"cannot load {ALLOWLIST}: {exc}") from exc
    if not isinstance(value, dict):
        raise AllowlistError("allowlist root must be an object")
    return value


def _string_map(manifest: dict[str, Any], key: str) -> dict[str, str]:
    value = manifest.get(key)
    if not isinstance(value, dict):
        raise AllowlistError(f"{key} must be an object")
    if not all(isinstance(name, str) and isinstance(item, str) for name, item in value.items()):
        raise AllowlistError(f"{key} must map strings to strings")
    return value


def _byte_map(manifest: dict[str, Any]) -> dict[str, int]:
    value = manifest.get("tracked_file_bytes")
    if not isinstance(value, dict):
        raise AllowlistError("tracked_file_bytes must be an object")
    if not all(
        isinstance(name, str)
        and isinstance(item, int)
        and not isinstance(item, bool)
        and item >= 0
        for name, item in value.items()
    ):
        raise AllowlistError("tracked_file_bytes must map strings to non-negative integers")
    return value


def _validate_manifest_shape(
    manifest: dict[str, Any], tracked_root: str
) -> tuple[dict[str, str], dict[str, int], dict[str, str]]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise AllowlistError(
            f"schema_version must be {SCHEMA_VERSION!r}; regenerate the allowlist"
        )
    if manifest.get("tracked_root") != tracked_root:
        raise AllowlistError(
            f"tracked_root mismatch: expected {tracked_root!r}, got {manifest.get('tracked_root')!r}"
        )

    hashes = _string_map(manifest, "tracked_files")
    byte_counts = _byte_map(manifest)
    classes = _string_map(manifest, "tracked_file_classes")
    if set(hashes) != set(byte_counts) or set(hashes) != set(classes):
        raise AllowlistError(
            "tracked_files, tracked_file_bytes, and tracked_file_classes must have identical keys"
        )
    for name, digest in hashes.items():
        if (
            not name
            or name.startswith("/")
            or ".." in Path(name).parts
            or name == ALLOWLIST_NAME
        ):
            raise AllowlistError(f"invalid tracked file name: {name!r}")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise AllowlistError(f"invalid SHA-256 for {name}: {digest!r}")
        if not classes[name]:
            raise AllowlistError(f"empty class for {name}")
    return hashes, byte_counts, classes


def _integer_field(manifest: dict[str, Any], key: str) -> int:
    value = manifest.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AllowlistError(f"{key} must be a non-negative integer")
    return value


def verify() -> None:
    repository_root = _repository_root()
    tracked_root = _tracked_root(repository_root)
    manifest = _load_allowlist()
    hashes, byte_counts, _classes = _validate_manifest_shape(manifest, tracked_root)
    candidates = _candidate_files(repository_root, tracked_root)

    errors: list[str] = []
    if ALLOWLIST_NAME not in candidates:
        errors.append(f"missing allowlist candidate: {ALLOWLIST_NAME}")
    candidate_entries = set(candidates) - {ALLOWLIST_NAME}
    expected_entries = set(hashes)
    for name in sorted(expected_entries - candidate_entries):
        errors.append(f"missing tracked file: {name}")
    for name in sorted(candidate_entries - expected_entries):
        errors.append(f"unreviewed candidate file: {name}")

    for name in sorted(expected_entries & candidate_entries):
        try:
            actual_hash, actual_bytes = _file_identity(candidates[name])
        except AllowlistError as exc:
            errors.append(str(exc))
            continue
        if actual_hash != hashes[name]:
            errors.append(
                f"SHA-256 mismatch for {name}: expected {hashes[name]}, got {actual_hash}"
            )
        if actual_bytes != byte_counts[name]:
            errors.append(
                f"byte count mismatch for {name}: expected {byte_counts[name]}, got {actual_bytes}"
            )

    expected_count = _integer_field(manifest, "tracked_file_count_including_allowlist")
    actual_count = len(candidates)
    if actual_count != expected_count:
        errors.append(f"file count mismatch: expected {expected_count}, got {actual_count}")

    expected_total_bytes = _integer_field(
        manifest, "tracked_directory_bytes_including_allowlist"
    )
    actual_total_bytes = 0
    for name, path in candidates.items():
        try:
            actual_total_bytes += path.stat().st_size
        except OSError as exc:
            errors.append(f"cannot stat {name}: {exc}")
    if actual_total_bytes != expected_total_bytes:
        errors.append(
            f"directory byte count mismatch: expected {expected_total_bytes}, got {actual_total_bytes}"
        )

    if errors:
        raise AllowlistError("verification failed:\n- " + "\n- ".join(errors))
    print(
        f"verified {len(expected_entries)} entries; "
        f"{actual_count} files and {actual_total_bytes} bytes including allowlist"
    )


def _class_for(name: str, existing_classes: dict[str, str]) -> str:
    if name in existing_classes and existing_classes[name]:
        return existing_classes[name]
    if name.endswith(".py"):
        return "harness-implementation"
    if name.endswith(".md"):
        return "docs"
    raise AllowlistError(
        f"no class is defined for new candidate {name!r}; add an explicit class before regeneration"
    )


def _render(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def regenerate() -> None:
    repository_root = _repository_root()
    tracked_root = _tracked_root(repository_root)
    old_manifest = _load_allowlist()
    old_classes_value = old_manifest.get("tracked_file_classes", {})
    old_classes = old_classes_value if isinstance(old_classes_value, dict) else {}
    if not all(isinstance(name, str) and isinstance(item, str) for name, item in old_classes.items()):
        raise AllowlistError("existing tracked_file_classes must map strings to strings")

    candidates = _candidate_files(repository_root, tracked_root)
    if ALLOWLIST_NAME not in candidates:
        raise AllowlistError(f"missing allowlist candidate: {ALLOWLIST_NAME}")
    entry_names = sorted(set(candidates) - {ALLOWLIST_NAME})
    identities = {name: _file_identity(candidates[name]) for name in entry_names}
    hashes = {name: identities[name][0] for name in entry_names}
    byte_counts = {name: identities[name][1] for name in entry_names}
    classes = {name: _class_for(name, old_classes) for name in entry_names}

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tracked_root": tracked_root,
        "tracked_files": hashes,
        "tracked_file_bytes": byte_counts,
        "tracked_file_classes": classes,
        "tracked_file_count_including_allowlist": len(candidates),
        "tracked_directory_bytes_including_allowlist": 0,
        "self_hash": None,
        "self_hash_reason": "A manifest cannot contain its own stable content hash.",
        "optional_tracked_after_compute": old_manifest.get(
            "optional_tracked_after_compute", []
        ),
        "ignored_runtime_root": old_manifest.get(
            "ignored_runtime_root", "output/runs/t1618-xdist-controller-cost"
        ),
        "ignored_runtime_allowlist": old_manifest.get("ignored_runtime_allowlist", []),
    }

    non_manifest_bytes = sum(byte_counts.values())
    total_bytes = non_manifest_bytes
    for _attempt in range(100):
        manifest["tracked_directory_bytes_including_allowlist"] = total_bytes
        rendered = _render(manifest)
        updated_total = non_manifest_bytes + len(rendered)
        if updated_total == total_bytes:
            break
        total_bytes = updated_total
    else:
        raise AllowlistError("manifest byte count did not reach a fixed point")

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=DIRECTORY, prefix=f".{ALLOWLIST_NAME}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, ALLOWLIST)
    except OSError as exc:
        try:
            temporary.unlink()
        except (NameError, OSError):
            pass
        raise AllowlistError(f"cannot replace {ALLOWLIST}: {exc}") from exc

    print(
        f"regenerated {len(entry_names)} entries; "
        f"{len(candidates)} files and {total_bytes} bytes including allowlist"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true", help="verify every allowlisted file")
    mode.add_argument(
        "--regenerate", action="store_true", help="rewrite the allowlist from current files"
    )
    arguments = parser.parse_args()
    try:
        if arguments.verify:
            verify()
        else:
            regenerate()
    except AllowlistError as exc:
        print(f"artifact allowlist error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
