# -*- coding: utf-8 -*-
"""Strict CMake/Unix-Makefiles compiler-input manifests for S8b.

The collector accepts only the measured CMake ``Unix Makefiles`` shape: one
``CMakeFiles/<target>.dir`` directory, its CXX ``flags.make`` and ``link.txt``,
and one or more compiler-generated ``*.o.d`` dependency files.  Unknown
generators, incomplete metadata, make variables, response files, symlinked
metadata, and ambiguous target directories are rejected rather than treated as
an empty or partial manifest.

Version 2 persists every compiler input as a tagged root plus a root-relative
POSIX path.  The only portable FetchContent root admitted by the measured S8b
surface is masstree.  Snapshot and filesystem inputs retain their established
bytes checks, while masstree inputs are rebound to a caller-supplied current
canonical root at every live validation boundary.  Version 1 remains a strict
read-only compatibility format; its absolute external paths are never migrated
or softened.

Descriptor-bound S8b collection also carries an independently captured
pre-build EVOLVE-BLOCK source entry and requires its post-build snapshot bytes
to match.  That check does not depend on the source merely appearing in the
target dependency list.  The manifest does not prove dynamic predicate
reachability.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


LEGACY_MANIFEST_SCHEMA = "s8b-compiler-input/v1"
MANIFEST_SCHEMA = "s8b-compiler-input/v2"
_METADATA_SCHEMA = "cmake-unix-makefiles-cxx-depfile/v1"
_EXTERNAL_INPUT_POLICY = "snapshot-and-external-hashes/v1"
_V2_ROOTS = frozenset({"snapshot", "fetchcontent-masstree", "filesystem"})
_LOWER_HEX = frozenset("0123456789abcdef")
_TARGET_RE = re.compile(r"[A-Za-z0-9_.+-]+\Z")
_FLAGS_KEYS = ("CXX_DEFINES", "CXX_INCLUDES", "CXX_FLAGS")


class CompilerInputError(RuntimeError):
    """The compiler dependency metadata or snapshot binding is not admissible."""


@dataclass(frozen=True, slots=True)
class CompilerInputManifest:
    """Canonical manifest body and its exact SHA-256 digest."""

    manifest: dict[str, Any]
    manifest_sha256: str


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _LOWER_HEX for character in value)
    )


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CompilerInputError("compiler input manifest is not canonical JSON") from exc


def manifest_sha256(manifest: object) -> str:
    """Return the root-independent canonical digest for one manifest body."""
    return hashlib.sha256(_canonical_bytes(manifest)).hexdigest()


def _directory(
        value: os.PathLike[str] | str, *, label: str,
        allow_symlink_root: bool = False) -> Path:
    try:
        raw = os.fspath(value)
        path = Path(raw)
        info = path.lstat()
    except (TypeError, ValueError, OSError) as exc:
        raise CompilerInputError(f"{label} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode):
        if not allow_symlink_root or not path.is_dir():
            raise CompilerInputError(f"{label} is not a directory")
    elif not stat.S_ISDIR(info.st_mode):
        raise CompilerInputError(f"{label} is not a directory")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise CompilerInputError(f"{label} cannot be resolved") from exc


def _target_name(value: object) -> str:
    if type(value) is not str or _TARGET_RE.fullmatch(value) is None:
        raise CompilerInputError("compiler target name is unsupported")
    return value


def _read_regular_text(path: Path, *, label: str) -> str:
    descriptor = -1
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
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
            raise CompilerInputError(f"{label} is not a non-symlink regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CompilerInputError(f"{label} changed while being read")
        raw = b"".join(chunks)
        if b"\0" in raw:
            raise CompilerInputError(f"{label} contains NUL")
        return raw.decode("utf-8", errors="strict")
    except CompilerInputError:
        raise
    except (OSError, UnicodeError) as exc:
        raise CompilerInputError(f"{label} cannot be read strictly") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _require_unix_makefiles(build_root: Path) -> None:
    text = _read_regular_text(build_root / "CMakeCache.txt", label="CMakeCache.txt")
    values = []
    for line in text.splitlines():
        match = re.fullmatch(r"CMAKE_GENERATOR(?::[^=\r\n]*)?=([^\r\n]*)", line)
        if match is not None:
            values.append(match.group(1))
    if values != ["Unix Makefiles"]:
        raise CompilerInputError(
            "CMAKE_GENERATOR is not one exact Unix Makefiles value"
        )


def _target_directory(build_root: Path, target: str) -> Path:
    matches: list[Path] = []
    expected_leaf = f"{target}.dir"
    try:
        for directory, names, _files in os.walk(build_root, followlinks=False):
            parent = Path(directory)
            retained = []
            for name in names:
                child = parent / name
                info = child.lstat()
                if stat.S_ISLNK(info.st_mode):
                    continue
                retained.append(name)
                if (
                    name == expected_leaf
                    and parent.name == "CMakeFiles"
                    and stat.S_ISDIR(info.st_mode)
                ):
                    matches.append(child)
            names[:] = retained
    except OSError as exc:
        raise CompilerInputError("build tree cannot be enumerated") from exc
    if len(matches) != 1:
        raise CompilerInputError(
            "target metadata directory is missing or ambiguous"
        )
    return matches[0]


def _strict_shell_words(value: str, *, label: str) -> list[str]:
    if "$" in value or "`" in value:
        raise CompilerInputError(f"{label} contains unsupported shell expansion")
    try:
        words = shlex.split(value, posix=True)
    except ValueError as exc:
        raise CompilerInputError(f"{label} has unsupported shell quoting") from exc
    if any("\0" in word for word in words):
        raise CompilerInputError(f"{label} contains NUL")
    return words


def _parse_flags_make(target_dir: Path) -> str:
    text = _read_regular_text(target_dir / "flags.make", label="flags.make")
    assignments: dict[str, str] = {}
    compiler_values: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        compiler_match = re.fullmatch(r"# compile CXX with (.+)", line)
        if compiler_match is not None:
            words = _strict_shell_words(
                compiler_match.group(1), label="flags.make compiler",
            )
            if len(words) != 1 or not os.path.isabs(words[0]):
                raise CompilerInputError("flags.make compiler is unsupported")
            compiler_values.append(words[0])
            continue
        if line.startswith("#"):
            continue
        assignment = re.fullmatch(r"([A-Z][A-Z0-9_]*) =([^\r\n]*)", line)
        if assignment is None or assignment.group(1) not in _FLAGS_KEYS:
            raise CompilerInputError("flags.make metadata shape is unsupported")
        key, value = assignment.groups()
        if key in assignments:
            raise CompilerInputError("flags.make contains a duplicate assignment")
        _strict_shell_words(value, label=f"flags.make {key}")
        assignments[key] = value
    if set(assignments) != set(_FLAGS_KEYS) or len(compiler_values) != 1:
        raise CompilerInputError("flags.make is incomplete or ambiguous")
    return compiler_values[0]


def _parse_link_txt(
    build_root: Path, target_dir: Path, target: str, compiler: str,
) -> frozenset[str]:
    text = _read_regular_text(target_dir / "link.txt", label="link.txt")
    lines = text.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        raise CompilerInputError("link.txt must contain one non-empty command")
    words = _strict_shell_words(lines[0], label="link.txt")
    if len(words) < 3 or words[0] != compiler or any(word.startswith("@") for word in words):
        raise CompilerInputError("link.txt command shape is unsupported")
    outputs: list[str] = []
    for index, word in enumerate(words):
        if word == "-o":
            if index + 1 >= len(words):
                raise CompilerInputError("link.txt has an incomplete -o option")
            outputs.append(words[index + 1])
        elif word.startswith("-o") and word != "-o":
            outputs.append(word[2:])
    if len(outputs) != 1 or not outputs[0]:
        raise CompilerInputError("link.txt output is missing or ambiguous")
    output = Path(outputs[0])
    expected = target_dir.parent.parent / target
    working_directories = (build_root, target_dir.parent.parent)
    expected_output = os.path.normpath(os.path.abspath(expected))
    matching_working_directories = [
        working for working in working_directories
        if os.path.normpath(os.path.abspath(
            output if output.is_absolute() else working / output
        )) == expected_output
    ]
    if not matching_working_directories:
        raise CompilerInputError("link.txt output does not match the selected target")
    object_words = [
        word for word in words[1:]
        if word.endswith(".o") and not word.startswith("-")
    ]
    if not object_words:
        raise CompilerInputError("link.txt has no direct object inputs")
    object_sets = {
        frozenset(
            os.path.normpath(os.path.abspath(
                Path(word) if Path(word).is_absolute() else working / word
            ))
            for word in object_words
        )
        for working in matching_working_directories
    }
    if len(object_sets) != 1:
        raise CompilerInputError("link.txt object working directory is ambiguous")
    return object_sets.pop()


def _logical_depfile(text: str) -> str:
    if "\r" in text.replace("\r\n", ""):
        raise CompilerInputError("depfile contains unsupported carriage returns")
    logical = text.replace("\\\r\n", " ").replace("\\\n", " ")
    if "\n" in logical.rstrip("\n"):
        raise CompilerInputError("depfile contains multiple logical rules")
    return logical.strip()


def _rule_separator(rule: str) -> int:
    escaped = False
    for index, character in enumerate(rule):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == ":":
            return index
    raise CompilerInputError("depfile rule separator is missing")


def _make_words(value: str) -> list[str]:
    if "$" in value:
        raise CompilerInputError("depfile make variables are unsupported")
    words: list[str] = []
    current: list[str] = []
    escaped = False
    for character in value:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character.isspace():
            if current:
                words.append("".join(current))
                current = []
        elif character == "#":
            raise CompilerInputError("depfile comments are unsupported")
        else:
            current.append(character)
    if escaped:
        raise CompilerInputError("depfile ends with an incomplete escape")
    if current:
        words.append("".join(current))
    return words


def _parse_depfile(
        build_root: Path, target_dir: Path, depfile: Path,
) -> tuple[list[str], Path]:
    rule = _logical_depfile(_read_regular_text(depfile, label="compiler depfile"))
    separator = _rule_separator(rule)
    targets = _make_words(rule[:separator])
    inputs = _make_words(rule[separator + 1:])
    if len(targets) != 1 or not inputs:
        raise CompilerInputError("depfile target/input cardinality is unsupported")
    target_path = Path(targets[0])
    expected_object = Path(str(depfile)[:-2])
    working_directories = tuple(dict.fromkeys((
        build_root, target_dir.parent.parent,
    )))
    matching = [
        working for working in working_directories
        if os.path.normpath(os.path.abspath(
            target_path if target_path.is_absolute() else working / target_path
        )) == os.path.normpath(os.path.abspath(expected_object))
    ]
    if not matching:
        raise CompilerInputError("depfile target does not match its .o.d path")
    if target_path.is_absolute() and any(
            not Path(raw_input).is_absolute() for raw_input in inputs):
        raise CompilerInputError(
            "absolute depfile target with relative inputs is ambiguous"
        )
    return inputs, matching[0]


def _compiler_depfiles(target_dir: Path) -> list[Path]:
    depfiles: list[Path] = []
    try:
        for directory, names, files in os.walk(target_dir, followlinks=False):
            parent = Path(directory)
            retained = []
            for name in names:
                child = parent / name
                if child.is_symlink():
                    raise CompilerInputError(
                        "target metadata contains a symlinked directory"
                    )
                retained.append(name)
            names[:] = retained
            for name in files:
                child = parent / name
                if name.endswith(".d") and not name.endswith(".o.d"):
                    raise CompilerInputError(
                        "target metadata contains an unsupported depfile suffix"
                    )
                if child.is_symlink():
                    if name.endswith(".o.d"):
                        raise CompilerInputError("compiler depfile is a symlink")
                    continue
                if name.endswith(".o.d"):
                    if not child.is_file():
                        raise CompilerInputError(
                            "compiler depfile is not a regular file"
                        )
                    depfiles.append(child)
    except CompilerInputError:
        raise
    except OSError as exc:
        raise CompilerInputError("compiler depfiles cannot be enumerated") from exc
    depfiles.sort()
    if not depfiles:
        raise CompilerInputError("compiler depfile set is empty")
    return depfiles


def _snapshot_entry(
    raw_path: str, *, build_root: Path, snapshot_root: Path,
) -> tuple[str, Path]:
    path = Path(raw_path)
    if not path.is_absolute():
        path = build_root / path
    normalized = Path(os.path.normpath(os.path.abspath(path)))
    try:
        relative = normalized.relative_to(snapshot_root)
    except ValueError as exc:
        raise CompilerInputError("compiler input is outside the source snapshot") from exc
    if not relative.parts:
        raise CompilerInputError("compiler input names the snapshot directory")
    current = snapshot_root
    try:
        for part in relative.parts:
            current = current / part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise CompilerInputError("compiler input traverses a snapshot symlink")
        if not stat.S_ISREG(info.st_mode):
            raise CompilerInputError("compiler input is not a regular snapshot entry")
    except FileNotFoundError as exc:
        raise CompilerInputError("compiler input is absent from the source snapshot") from exc
    except OSError as exc:
        raise CompilerInputError("compiler input snapshot entry cannot be inspected") from exc
    return relative.as_posix(), current


def _external_entry(raw_path: str, *, snapshot_root: Path) -> tuple[str, Path]:
    path = Path(raw_path)
    if not path.is_absolute():
        raise CompilerInputError("external compiler input path is not absolute")
    normalized = Path(os.path.normpath(os.path.abspath(path)))
    if normalized.as_posix() != raw_path:
        raise CompilerInputError("external compiler input path is not normalized")
    try:
        resolved = normalized.resolve(strict=True)
        info = resolved.lstat()
    except FileNotFoundError as exc:
        raise CompilerInputError("external compiler input is unavailable") from exc
    except OSError as exc:
        raise CompilerInputError(
            "external compiler input cannot be inspected"
        ) from exc
    try:
        resolved.relative_to(snapshot_root)
    except ValueError:
        pass
    else:
        return _snapshot_entry(
            resolved.as_posix(), build_root=snapshot_root,
            snapshot_root=snapshot_root,
        )
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise CompilerInputError(
            "external compiler input is not a non-symlink regular file"
        )
    return resolved.as_posix(), resolved


def _compiler_input_entry(
        raw_path: str, *, build_root: Path, snapshot_root: Path,
        allow_external_inputs: bool,
) -> tuple[str, Path]:
    path = Path(raw_path)
    if not path.is_absolute():
        path = build_root / path
    normalized = Path(os.path.normpath(os.path.abspath(path)))
    try:
        normalized.relative_to(snapshot_root)
    except ValueError:
        if not allow_external_inputs:
            raise CompilerInputError(
                "compiler input is outside the source snapshot"
            )
        return _external_entry(
            normalized.as_posix(), snapshot_root=snapshot_root,
        )
    return _snapshot_entry(
        normalized.as_posix(), build_root=build_root,
        snapshot_root=snapshot_root,
    )


def _file_sha256(path: Path) -> str:
    descriptor = -1
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CompilerInputError("compiler input is not a regular file")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        if total != before.st_size or (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CompilerInputError("compiler input changed while hashing")
        return digest.hexdigest()
    except CompilerInputError:
        raise
    except OSError as exc:
        raise CompilerInputError("compiler input cannot be hashed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _strict_root(
        value: os.PathLike[str] | str, *, label: str,
) -> Path:
    """Return one canonical absolute directory after no-follow traversal."""
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise CompilerInputError(f"{label} is unavailable") from exc
    if (type(raw) is not str or not raw or "\0" in raw
            or not os.path.isabs(raw)):
        raise CompilerInputError(f"{label} is not a canonical absolute directory")
    absolute = os.path.abspath(raw)
    if absolute != raw or os.path.realpath(raw) != absolute:
        raise CompilerInputError(f"{label} is not a canonical absolute directory")
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required):
        raise CompilerInputError(f"{label} cannot be inspected without symlink following")
    flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = -1
    try:
        descriptor = os.open(os.sep, flags)
        for part in Path(absolute).parts[1:]:
            before = os.stat(part, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise CompilerInputError(
                    f"{label} traverses a symlink or non-directory component"
                )
            child = os.open(part, flags, dir_fd=descriptor)
            after = os.fstat(child)
            if (
                not stat.S_ISDIR(after.st_mode)
                or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            ):
                os.close(child)
                raise CompilerInputError(f"{label} changed during traversal")
            os.close(descriptor)
            descriptor = child
        return Path(absolute)
    except CompilerInputError:
        raise
    except OSError as exc:
        raise CompilerInputError(f"{label} is unavailable") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _normalized_relative_posix(value: object, *, label: str) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise CompilerInputError(f"{label} path is invalid")
    pure = PurePosixPath(value)
    if (pure.is_absolute() or pure.as_posix() != value
            or any(part in {"", ".", ".."} for part in pure.parts)):
        raise CompilerInputError(f"{label} path is not normalized relative POSIX")
    return value


def _hash_relative_nofollow(
        root: Path, relative: str, *, label: str,
) -> str:
    """Hash a regular leaf reached from a held root fd without following links."""
    parts = PurePosixPath(
        _normalized_relative_posix(relative, label=label)
    ).parts
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    root_fd = current_fd = leaf_fd = -1
    try:
        root_fd = os.open(root, directory_flags)
        current_fd = root_fd
        for part in parts[:-1]:
            before = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise CompilerInputError(f"{label} traverses a symlink component")
            child_fd = os.open(part, directory_flags, dir_fd=current_fd)
            after = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(after.st_mode)
                or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            ):
                os.close(child_fd)
                raise CompilerInputError(f"{label} changed during traversal")
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = child_fd
        entry = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
        if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
            raise CompilerInputError(f"{label} is not a non-symlink regular file")
        leaf_fd = os.open(parts[-1], leaf_flags, dir_fd=current_fd)
        before = os.fstat(leaf_fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or (entry.st_dev, entry.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise CompilerInputError(f"{label} changed during open")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(leaf_fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
        after = os.fstat(leaf_fd)
        stable_before = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns,
        )
        stable_after = (
            after.st_dev, after.st_ino, after.st_size,
            after.st_mtime_ns, after.st_ctime_ns,
        )
        if total != before.st_size or stable_before != stable_after:
            raise CompilerInputError(f"{label} changed while hashing")
        return digest.hexdigest()
    except CompilerInputError:
        raise
    except OSError as exc:
        raise CompilerInputError(f"{label} is unavailable or cannot be hashed") from exc
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
        if current_fd >= 0 and current_fd != root_fd:
            os.close(current_fd)
        if root_fd >= 0:
            os.close(root_fd)


def _roots_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _normalized_hashed_entries(
        value: object, *, label: str, allow_absolute: bool,
) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise CompilerInputError(f"{label} is empty")
    normalized: list[dict[str, str]] = []
    previous = ""
    for entry in value:
        if type(entry) is not dict or set(entry) != {"path", "sha256"}:
            raise CompilerInputError(f"{label} entry field set is invalid")
        path = entry["path"]
        digest = entry["sha256"]
        if type(path) is not str or not path or "\0" in path:
            raise CompilerInputError(f"{label} path is invalid")
        pure = PurePosixPath(path)
        if pure.is_absolute():
            if (
                not allow_absolute
                or pure.as_posix() != path
                or os.path.normpath(path) != path
            ):
                raise CompilerInputError(
                    f"{label} path is not normalized POSIX"
                )
        elif pure.as_posix() != path or any(
                part in {"", ".", ".."} for part in pure.parts):
            raise CompilerInputError(
                f"{label} path is not normalized relative POSIX"
            )
        if path <= previous:
            raise CompilerInputError(f"{label} entries are not unique and sorted")
        if not _is_sha256(digest):
            raise CompilerInputError(f"{label} bytes hash is invalid")
        normalized.append({"path": path, "sha256": digest})
        previous = path
    return normalized


def _normalized_expected_evolve_sources(
        value: Mapping[str, str] | None,
) -> list[dict[str, str]] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or not value:
        raise CompilerInputError(
            "expected EVOLVE-BLOCK source entries are invalid"
        )
    raw = [
        {"path": path, "sha256": value[path]}
        for path in sorted(value)
    ]
    return _normalized_hashed_entries(
        raw, label="EVOLVE-BLOCK source", allow_absolute=False,
    )


def _normalized_v1_manifest(
        manifest: object, *, target: str | None,
) -> dict[str, Any]:
    base_keys = {
        "schema_version", "metadata_schema", "target", "depfile_count", "inputs",
    }
    descriptor_keys = base_keys | {"input_policy"}
    if type(manifest) is not dict or set(manifest) not in (
        base_keys,
        descriptor_keys,
        descriptor_keys | {"evolve_block_sources"},
    ):
        raise CompilerInputError("compiler input manifest field set is invalid")
    if manifest["schema_version"] != LEGACY_MANIFEST_SCHEMA:
        raise CompilerInputError("compiler input manifest schema is invalid")
    if manifest["metadata_schema"] != _METADATA_SCHEMA:
        raise CompilerInputError("compiler input metadata schema is invalid")
    selected_target = _target_name(manifest["target"])
    if target is not None and selected_target != _target_name(target):
        raise CompilerInputError("compiler input manifest target is inconsistent")
    if type(manifest["depfile_count"]) is not int or manifest["depfile_count"] <= 0:
        raise CompilerInputError("compiler input depfile count is invalid")
    input_policy = manifest.get("input_policy")
    if input_policy is not None and input_policy != _EXTERNAL_INPUT_POLICY:
        raise CompilerInputError("compiler input policy is invalid")
    inputs = _normalized_hashed_entries(
        manifest["inputs"], label="compiler input",
        allow_absolute=input_policy == _EXTERNAL_INPUT_POLICY,
    )
    normalized = {
        "schema_version": LEGACY_MANIFEST_SCHEMA,
        "metadata_schema": _METADATA_SCHEMA,
        "target": selected_target,
        "depfile_count": manifest["depfile_count"],
        "inputs": inputs,
    }
    if input_policy is not None:
        normalized["input_policy"] = input_policy
    if "evolve_block_sources" in manifest:
        normalized["evolve_block_sources"] = _normalized_hashed_entries(
            manifest["evolve_block_sources"],
            label="EVOLVE-BLOCK source", allow_absolute=False,
        )
    return normalized


def _normalized_v2_inputs(value: object) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise CompilerInputError("compiler input is empty")
    normalized: list[dict[str, str]] = []
    previous: tuple[str, str] | None = None
    for entry in value:
        if type(entry) is not dict or set(entry) != {"root", "path", "sha256"}:
            raise CompilerInputError("compiler input entry field set is invalid")
        root = entry["root"]
        if type(root) is not str or root not in _V2_ROOTS:
            raise CompilerInputError("compiler input root is invalid")
        path = _normalized_relative_posix(
            entry["path"], label="compiler input",
        )
        digest = entry["sha256"]
        if not _is_sha256(digest):
            raise CompilerInputError("compiler input bytes hash is invalid")
        key = (root, path)
        if previous is not None and key <= previous:
            raise CompilerInputError(
                "compiler input entries are not unique and sorted"
            )
        normalized.append({"root": root, "path": path, "sha256": digest})
        previous = key
    return normalized


def _normalized_v2_manifest(
        manifest: object, *, target: str | None,
) -> dict[str, Any]:
    base_keys = {
        "schema_version", "metadata_schema", "target", "depfile_count", "inputs",
    }
    descriptor_keys = base_keys | {"input_policy"}
    if type(manifest) is not dict or set(manifest) not in (
        base_keys,
        descriptor_keys,
        descriptor_keys | {"evolve_block_sources"},
    ):
        raise CompilerInputError("compiler input manifest field set is invalid")
    if manifest["schema_version"] != MANIFEST_SCHEMA:
        raise CompilerInputError("compiler input manifest schema is invalid")
    if manifest["metadata_schema"] != _METADATA_SCHEMA:
        raise CompilerInputError("compiler input metadata schema is invalid")
    selected_target = _target_name(manifest["target"])
    if target is not None and selected_target != _target_name(target):
        raise CompilerInputError("compiler input manifest target is inconsistent")
    if type(manifest["depfile_count"]) is not int or manifest["depfile_count"] <= 0:
        raise CompilerInputError("compiler input depfile count is invalid")
    input_policy = manifest.get("input_policy")
    if input_policy is not None and input_policy != _EXTERNAL_INPUT_POLICY:
        raise CompilerInputError("compiler input policy is invalid")
    inputs = _normalized_v2_inputs(manifest["inputs"])
    if input_policy is None and any(entry["root"] != "snapshot" for entry in inputs):
        raise CompilerInputError(
            "external compiler input root requires descriptor input policy"
        )
    normalized: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "metadata_schema": _METADATA_SCHEMA,
        "target": selected_target,
        "depfile_count": manifest["depfile_count"],
        "inputs": inputs,
    }
    if input_policy is not None:
        normalized["input_policy"] = input_policy
    if "evolve_block_sources" in manifest:
        normalized["evolve_block_sources"] = _normalized_hashed_entries(
            manifest["evolve_block_sources"],
            label="EVOLVE-BLOCK source", allow_absolute=False,
        )
    return normalized


def _normalized_manifest(manifest: object, *, target: str | None) -> dict[str, Any]:
    if type(manifest) is not dict:
        raise CompilerInputError("compiler input manifest field set is invalid")
    schema = manifest.get("schema_version")
    if schema == LEGACY_MANIFEST_SCHEMA:
        return _normalized_v1_manifest(manifest, target=target)
    if schema == MANIFEST_SCHEMA:
        return _normalized_v2_manifest(manifest, target=target)
    raise CompilerInputError("compiler input manifest schema is invalid")


def validate_compiler_input_manifest(
    manifest: object, expected_sha256: object, *,
    snapshot_root: os.PathLike[str] | str, target: str | None = None,
    expected_evolve_block_sources: Mapping[str, str] | None = None,
    current_fetchcontent_masstree_root: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    """Validate all input bytes and any independent EVOLVE-BLOCK source proof."""
    normalized = _normalized_manifest(manifest, target=target)
    if not _is_sha256(expected_sha256):
        raise CompilerInputError("compiler input manifest sha256 is invalid")
    if manifest_sha256(normalized) != expected_sha256:
        raise CompilerInputError("compiler input manifest sha256 mismatch")
    if normalized["schema_version"] == LEGACY_MANIFEST_SCHEMA:
        snapshot = _directory(
            snapshot_root, label="source snapshot", allow_symlink_root=True,
        )
        for entry in normalized["inputs"]:
            recorded, path = _compiler_input_entry(
                entry["path"], build_root=snapshot, snapshot_root=snapshot,
                allow_external_inputs=True,
            )
            if recorded != entry["path"]:
                raise CompilerInputError("compiler input path changed during validation")
            if _file_sha256(path) != entry["sha256"]:
                if Path(entry["path"]).is_absolute():
                    raise CompilerInputError(
                        "external compiler input bytes differ from the manifest"
                    )
                raise CompilerInputError(
                    "compiler input bytes differ from the snapshot entry"
                )
    else:
        snapshot = _strict_root(snapshot_root, label="source snapshot")
        needs_current_context = any(
            entry["root"] != "snapshot" for entry in normalized["inputs"]
        )
        current_masstree = (
            _strict_root(
                current_fetchcontent_masstree_root,
                label="current FetchContent masstree root",
            )
            if (
                current_fetchcontent_masstree_root is not None
                and needs_current_context
            ) else None
        )
        if current_masstree is not None and _roots_overlap(snapshot, current_masstree):
            raise CompilerInputError(
                "source snapshot and current FetchContent masstree roots overlap"
            )
        for entry in normalized["inputs"]:
            root = entry["root"]
            if root == "snapshot":
                selected_root = snapshot
                difference = "compiler input bytes differ from the snapshot entry"
            elif root == "fetchcontent-masstree":
                if current_masstree is None:
                    raise CompilerInputError(
                        "current FetchContent masstree root is required"
                    )
                selected_root = current_masstree
                difference = (
                    "current FetchContent masstree input bytes differ from the manifest"
                )
            else:
                selected_root = Path(os.sep)
                absolute = selected_root.joinpath(*PurePosixPath(entry["path"]).parts)
                special_roots = [snapshot]
                if current_masstree is not None:
                    special_roots.extend((current_masstree, current_masstree.parent))
                if any(
                    absolute == special or special in absolute.parents
                    for special in special_roots
                ):
                    raise CompilerInputError(
                        "compiler input root tag is not canonical for its live path"
                    )
                difference = "external compiler input bytes differ from the manifest"
            if _hash_relative_nofollow(
                    selected_root, entry["path"], label="compiler input") != entry["sha256"]:
                raise CompilerInputError(difference)
    expected_sources = _normalized_expected_evolve_sources(
        expected_evolve_block_sources,
    )
    recorded_sources = normalized.get("evolve_block_sources")
    if expected_sources is not None and recorded_sources != expected_sources:
        raise CompilerInputError(
            "EVOLVE-BLOCK source proof differs from the admitted snapshot entry"
        )
    for entry in recorded_sources or ():
        if normalized["schema_version"] == LEGACY_MANIFEST_SCHEMA:
            relative, path = _snapshot_entry(
                entry["path"], build_root=snapshot, snapshot_root=snapshot,
            )
            matches = relative == entry["path"] and _file_sha256(path) == entry["sha256"]
        else:
            matches = _hash_relative_nofollow(
                snapshot, entry["path"], label="EVOLVE-BLOCK source",
            ) == entry["sha256"]
        if not matches:
            raise CompilerInputError(
                "EVOLVE-BLOCK source bytes differ from the admitted snapshot entry"
            )
    return normalized


def collect_compiler_input_manifest(
    build_dir: os.PathLike[str] | str,
    snapshot_root: os.PathLike[str] | str,
    *, target: str, allow_external_inputs: bool = False,
    expected_evolve_block_sources: Mapping[str, str] | None = None,
    origin_fetchcontent_masstree_root: os.PathLike[str] | str | None = None,
    current_fetchcontent_masstree_root: os.PathLike[str] | str | None = None,
) -> CompilerInputManifest:
    """Collect one strict manifest, optionally admitting hashed external inputs."""
    if type(allow_external_inputs) is not bool:
        raise TypeError("allow_external_inputs must be exact bool")
    if expected_evolve_block_sources is not None and not allow_external_inputs:
        raise CompilerInputError(
            "EVOLVE-BLOCK source proof requires descriptor input policy"
        )
    build = _directory(build_dir, label="CMake build directory")
    snapshot = _strict_root(snapshot_root, label="source snapshot")
    origin_masstree = (
        _strict_root(
            origin_fetchcontent_masstree_root,
            label="origin FetchContent masstree root",
        )
        if origin_fetchcontent_masstree_root is not None else None
    )
    current_masstree = (
        _strict_root(
            current_fetchcontent_masstree_root,
            label="current FetchContent masstree root",
        )
        if current_fetchcontent_masstree_root is not None else None
    )
    if current_masstree is not None and origin_masstree is None:
        raise CompilerInputError(
            "current FetchContent masstree root requires an origin root"
        )
    for root in (origin_masstree, current_masstree):
        if root is not None and _roots_overlap(snapshot, root):
            raise CompilerInputError(
                "source snapshot and FetchContent masstree roots overlap"
            )
    selected_target = _target_name(target)
    _require_unix_makefiles(build)
    target_dir = _target_directory(build, selected_target)
    compiler = _parse_flags_make(target_dir)
    linked_objects = _parse_link_txt(
        build, target_dir, selected_target, compiler,
    )
    depfiles = _compiler_depfiles(target_dir)
    depfile_objects = frozenset(
        os.path.normpath(os.path.abspath(Path(str(depfile)[:-2])))
        for depfile in depfiles
    )
    if depfile_objects != linked_objects:
        raise CompilerInputError(
            "link.txt objects and compiler depfiles are not an exact set"
        )
    entries: dict[tuple[str, str], str] = {}
    for depfile in depfiles:
        raw_inputs, compiler_working_directory = _parse_depfile(
            build, target_dir, depfile,
        )
        for raw_input in raw_inputs:
            raw_path = Path(raw_input)
            if not raw_path.is_absolute():
                raw_path = compiler_working_directory / raw_path
            absolute = Path(os.path.normpath(os.path.abspath(raw_path)))
            try:
                relative = absolute.relative_to(snapshot)
                root = "snapshot"
                selected_root = snapshot
            except ValueError:
                if not allow_external_inputs:
                    raise CompilerInputError(
                        "compiler input is outside the source snapshot"
                    )
                if origin_masstree is not None:
                    try:
                        relative = absolute.relative_to(origin_masstree)
                        root = "fetchcontent-masstree"
                        selected_root = origin_masstree
                    except ValueError:
                        try:
                            absolute.relative_to(origin_masstree.parent)
                        except ValueError:
                            pass
                        else:
                            raise CompilerInputError(
                                "unsupported FetchContent compiler input root"
                            )
                        root = "filesystem"
                        selected_root = Path(os.sep)
                        relative = absolute.relative_to(selected_root)
                else:
                    root = "filesystem"
                    selected_root = Path(os.sep)
                    relative = absolute.relative_to(selected_root)
            relative_text = relative.as_posix()
            digest = _hash_relative_nofollow(
                selected_root, relative_text, label="compiler input",
            )
            key = (root, relative_text)
            previous = entries.setdefault(key, digest)
            if previous != digest:
                raise CompilerInputError("compiler input hash is inconsistent")
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "metadata_schema": _METADATA_SCHEMA,
        "target": selected_target,
        "depfile_count": len(depfiles),
        "inputs": [
            {"root": root, "path": relative, "sha256": entries[(root, relative)]}
            for root, relative in sorted(entries)
        ],
    }
    if allow_external_inputs:
        manifest["input_policy"] = _EXTERNAL_INPUT_POLICY
    expected_sources = _normalized_expected_evolve_sources(
        expected_evolve_block_sources,
    )
    if expected_sources is not None:
        manifest["evolve_block_sources"] = expected_sources
    digest = manifest_sha256(manifest)
    normalized = validate_compiler_input_manifest(
        manifest, digest, snapshot_root=snapshot, target=selected_target,
        expected_evolve_block_sources=expected_evolve_block_sources,
        current_fetchcontent_masstree_root=(
            current_masstree if current_masstree is not None else origin_masstree
        ),
    )
    return CompilerInputManifest(normalized, digest)
