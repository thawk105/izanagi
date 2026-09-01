"""Canonical GNU ar/ELF projection contract for the Masstree archive."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys

import pytest

from orchestrator.campaign import masstree_archive_projection as projection


_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_ELF_SECTION = struct.Struct("<IIQQQQIIQQ")
GOLDEN_CANONICAL_DIGEST = (
    "3e8a7b80de77a9685a92af1b02c159541ead35fa42f25ae19b512836ba118e58"
)


def _elf_object(
        *, text: bytes = b"fixture text", debug: bytes = b"/build/a/source.cc",
        debug_flags: int = 0, debug_type: int = 1, debug_info: int = 0,
) -> bytes:
    names = b"\x00.text\x00.debug_info\x00.rela.debug_info\x00.shstrtab\x00"
    name_offsets = {
        name: names.index(name)
        for name in (b".text", b".debug_info", b".rela.debug_info", b".shstrtab")
    }
    ident = b"\x7fELF" + bytes((2, 1, 1, 0, 0)) + b"\x00" * 7
    content = bytearray(b"\x00" * _ELF_HEADER.size)

    def append(payload: bytes, alignment: int = 1) -> int:
        while len(content) % alignment:
            content.append(0)
        offset = len(content)
        content.extend(payload)
        return offset

    text_offset = append(text, 16)
    debug_offset = append(debug)
    relocation = b"\x00" * 24
    relocation_offset = append(relocation, 8)
    names_offset = append(names)
    while len(content) % 8:
        content.append(0)
    section_offset = len(content)
    sections = (
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (name_offsets[b".text"], 1, 0x6, 0, text_offset, len(text), 0, 0, 16, 0),
        (
            name_offsets[b".debug_info"], debug_type, debug_flags, 0,
            debug_offset, len(debug), 0, debug_info, 1, 0,
        ),
        (
            name_offsets[b".rela.debug_info"], 4, 0, 0,
            relocation_offset, len(relocation), 0, 2, 8, 24,
        ),
        (
            name_offsets[b".shstrtab"], 3, 0, 0,
            names_offset, len(names), 0, 0, 1, 0,
        ),
    )
    for section in sections:
        content.extend(_ELF_SECTION.pack(*section))
    content[:_ELF_HEADER.size] = _ELF_HEADER.pack(
        ident, 1, 62, 1, 0, 0, section_offset, 0,
        _ELF_HEADER.size, 0, 0, _ELF_SECTION.size, len(sections), 4,
    )
    return bytes(content)


def _ar_header(name: str, size: int, *, timestamp: int = 0) -> bytes:
    fields = (
        name.encode("ascii").ljust(16),
        str(timestamp).encode("ascii").ljust(12),
        b"0".ljust(6),
        b"0".ljust(6),
        b"644".ljust(8),
        str(size).encode("ascii").ljust(10),
        b"`\n",
    )
    header = b"".join(fields)
    assert len(header) == 60
    return header


def masstree_archive_bytes(
        *, text: bytes = b"fixture text", debug: bytes = b"/build/a/source.cc",
        debug_flags: int = 0, debug_type: int = 1, debug_info: int = 0,
        timestamp: int = 0,
) -> bytes:
    payloads = [
        _elf_object(
            text=text + bytes((index,)),
            debug=debug,
            debug_flags=debug_flags,
            debug_type=debug_type,
            debug_info=debug_info,
        )
        for index, _name in enumerate(projection.MASSTREE_MEMBERS)
    ]
    symbol_names = [f"fixture_symbol_{index}".encode("ascii") for index in range(11)]
    index_size = 4 + 4 * len(payloads) + sum(len(name) + 1 for name in symbol_names)
    cursor = len(b"!<arch>\n") + 60 + index_size + (index_size & 1)
    offsets = []
    for payload in payloads:
        offsets.append(cursor)
        cursor += 60 + len(payload) + (len(payload) & 1)
    index = bytearray(len(payloads).to_bytes(4, "big"))
    for offset in offsets:
        index.extend(offset.to_bytes(4, "big"))
    for name in symbol_names:
        index.extend(name + b"\x00")

    archive = bytearray(b"!<arch>\n")
    archive.extend(_ar_header("/", len(index), timestamp=timestamp))
    archive.extend(index)
    if len(index) & 1:
        archive.extend(b"\n")
    for name, payload in zip(projection.MASSTREE_MEMBERS, payloads, strict=True):
        archive.extend(_ar_header(f"{name}/", len(payload), timestamp=timestamp))
        archive.extend(payload)
        if len(payload) & 1:
            archive.extend(b"\n")
    return bytes(archive)


def write_masstree_archive(path: Path, **kwargs: object) -> bytes:
    raw = masstree_archive_bytes(**kwargs)
    path.write_bytes(raw)
    return raw


def test_masstree_archive_projection_matches_fixed_golden(tmp_path: Path) -> None:
    archive = tmp_path / "libkohler_masstree_json.a"
    raw = write_masstree_archive(archive)
    observed = projection.masstree_archive_digests(archive)
    assert observed.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert observed.archive_nondebug_sha256 == GOLDEN_CANONICAL_DIGEST


def test_masstree_archive_projection_single_file_cli(tmp_path: Path) -> None:
    archive = tmp_path / "libkohler_masstree_json.a"
    write_masstree_archive(archive)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(Path(projection.__file__).resolve()), str(archive)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == GOLDEN_CANONICAL_DIGEST


def test_debug_only_and_ar_metadata_differences_keep_projection(
        tmp_path: Path,
) -> None:
    first = tmp_path / "first.a"
    second = tmp_path / "second.a"
    write_masstree_archive(first, debug=b"/clone/a/source.cc", timestamp=1)
    write_masstree_archive(second, debug=b"/different/root/source.cc", timestamp=2)
    first_digest = projection.masstree_archive_digests(first)
    second_digest = projection.masstree_archive_digests(second)
    assert first_digest.raw_sha256 != second_digest.raw_sha256
    assert (
        first_digest.archive_nondebug_sha256
        == second_digest.archive_nondebug_sha256
        == GOLDEN_CANONICAL_DIGEST
    )


def test_loadable_or_disallowed_debug_named_section_fails_closed(
        tmp_path: Path,
) -> None:
    for name, kwargs in (
        ("loadable", {"debug_flags": 0x2}),
        ("disallowed-type", {"debug_type": 2}),
    ):
        archive = tmp_path / f"{name}.a"
        write_masstree_archive(archive, **kwargs)
        with pytest.raises(
                projection.MasstreeArchiveProjectionError,
                match="loadable or executable|disallowed type"):
            projection.masstree_archive_digests(archive)


def test_debug_named_relocation_targeting_retained_text_fails_closed(
        tmp_path: Path,
) -> None:
    archive = tmp_path / "debug-relocation-targets-text.a"
    write_masstree_archive(
        archive,
        debug_type=4,
        debug_info=1,
    )
    with pytest.raises(
            projection.MasstreeArchiveProjectionError,
            match="relocation targets a retained section"):
        projection.masstree_archive_digests(archive)


def test_capture_keeps_raw_and_projection_on_the_same_single_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "libkohler_masstree_json.a"
    original = write_masstree_archive(archive, text=b"approved")
    replacement = masstree_archive_bytes(text=b"replacement")
    real_projection = projection._canonical_projection
    open_calls = []
    pathname_reads = []
    real_open = projection.os.open

    def reject_pathname_read(self: Path) -> bytes:
        pathname_reads.append(self)
        raise AssertionError("capture performed a second pathname read")

    def counted_open(*args: object, **kwargs: object) -> int:
        open_calls.append(args[0])
        return real_open(*args, **kwargs)

    def replace_before_projection(captured: bytes) -> str:
        archive.write_bytes(replacement)
        return real_projection(captured)

    monkeypatch.setattr(projection.os, "open", counted_open)
    monkeypatch.setattr(Path, "read_bytes", reject_pathname_read)
    monkeypatch.setattr(projection, "_canonical_projection", replace_before_projection)
    observed = projection.masstree_archive_digests(archive)
    assert open_calls == [archive]
    assert pathname_reads == []
    assert observed.raw_sha256 == hashlib.sha256(original).hexdigest()
    assert observed.archive_nondebug_sha256 == real_projection(original)
    assert hashlib.sha256(replacement).hexdigest() != observed.raw_sha256


def test_capture_stops_at_cumulative_limit_during_concurrent_append(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "growing.a"
    raw = write_masstree_archive(archive)
    real_read = projection.os.read
    appended = False

    def append_after_first_read(descriptor: int, size: int) -> bytes:
        nonlocal appended
        chunk = real_read(descriptor, size)
        if chunk and not appended:
            appended = True
            with archive.open("ab") as handle:
                handle.write(b"x")
        return chunk

    monkeypatch.setattr(projection, "_MAX_ARCHIVE_BYTES", len(raw))
    monkeypatch.setattr(projection.os, "read", append_after_first_read)
    with pytest.raises(
            projection.MasstreeArchiveProjectionError,
            match="exceeded the bounded capture size"):
        projection.masstree_archive_digests(archive)
    assert appended is True


def test_malformed_member_set_section_range_and_symlink_fail_closed(
        tmp_path: Path,
) -> None:
    archive = tmp_path / "archive.a"
    raw = write_masstree_archive(archive)
    archive.write_bytes(raw[:-1])
    with pytest.raises(projection.MasstreeArchiveProjectionError):
        projection.masstree_archive_digests(archive)

    raw = bytearray(masstree_archive_bytes())
    first_elf = raw.find(b"\x7fELF")
    assert first_elf > 0
    # e_shoff points beyond the member payload.
    struct.pack_into("<Q", raw, first_elf + 40, len(raw) + 4096)
    archive.write_bytes(raw)
    with pytest.raises(
            projection.MasstreeArchiveProjectionError,
            match="section table is out of range"):
        projection.masstree_archive_digests(archive)

    target = tmp_path / "target.a"
    write_masstree_archive(target)
    link = tmp_path / "link.a"
    link.symlink_to(target)
    with pytest.raises(
            projection.MasstreeArchiveProjectionError,
            match="non-symlink regular file"):
        projection.masstree_archive_digests(link)
