#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GNU ar 内の Masstree ELF object を非 debug 射影へ正規化する。

射影 ID は ``gnu-ar-elf-nondebug/v1``。

この gate が検出するのは、承認 policy と実行時 archive の非 debug 射影の差、および
`tool_version_body(--version)` の差である。同じ射影を出す道具の置換、debug 情報だけの差、
同じ version body を保った compiler binary の置換、gcc と g++ の role 混成は検出しない。
適用範囲は S8b `sort_best` の masstree prebuild と mocc trace pilot の compiler であり、
全 CCBench consumer を覆うものではない。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import struct
import sys
from typing import Iterable


PROJECTION_ID = "gnu-ar-elf-nondebug/v1"
MASSTREE_MEMBERS = (
    "json.o",
    "string.o",
    "straccum.o",
    "str.o",
    "msgpack.o",
    "clp.o",
    "kvrandom.o",
    "compiler.o",
    "memdebug.o",
    "kvthread.o",
    "misc.o",
)

_AR_MAGIC = b"!<arch>\n"
_AR_HEADER_SIZE = 60
_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_ELF_SECTION = struct.Struct("<IIQQQQIIQQ")
_SHT_NULL = 0
_SHT_PROGBITS = 1
_SHT_STRTAB = 3
_SHT_RELA = 4
_SHT_NOBITS = 8
_SHT_REL = 9
_SHF_ALLOC = 0x2
_SHF_EXECINSTR = 0x4
_DEBUG_SECTION_TYPES = frozenset({
    _SHT_PROGBITS, _SHT_STRTAB, _SHT_RELA, _SHT_REL,
})
_MAX_ARCHIVE_BYTES = 512 * 1024 * 1024


class MasstreeArchiveProjectionError(ValueError):
    """Archive が射影規約に一意に従わず、fail-closed にすべきである。"""


@dataclass(frozen=True)
class MasstreeArchiveDigests:
    """同じ no-follow capture から得た raw SHA と canonical 射影 SHA。"""

    raw_sha256: str
    archive_nondebug_sha256: str


@dataclass(frozen=True)
class _ArMember:
    name: str
    header_offset: int
    payload: bytes


@dataclass(frozen=True)
class _ElfSection:
    index: int
    name: bytes
    section_type: int
    flags: int
    address: int
    offset: int
    size: int
    link: int
    info: int
    alignment: int
    entry_size: int
    content: bytes


class _CanonicalHash:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self.record(b"projection", PROJECTION_ID.encode("ascii"))

    def record(self, tag: bytes, *parts: bytes) -> None:
        self._digest.update(struct.pack(">I", len(tag)))
        self._digest.update(tag)
        self._digest.update(struct.pack(">I", len(parts)))
        for part in parts:
            self._digest.update(struct.pack(">Q", len(part)))
            self._digest.update(part)

    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def _u64(value: int) -> bytes:
    if value < 0 or value > 0xFFFF_FFFF_FFFF_FFFF:
        raise MasstreeArchiveProjectionError("canonical integer is out of range")
    return struct.pack(">Q", value)


def _parse_decimal(field: bytes, *, label: str, allow_empty: bool = False) -> int:
    stripped = field.strip(b" ")
    if not stripped:
        if allow_empty:
            return 0
        raise MasstreeArchiveProjectionError(f"ar {label} is empty")
    if any(byte < ord("0") or byte > ord("9") for byte in stripped):
        raise MasstreeArchiveProjectionError(f"ar {label} is not decimal")
    return int(stripped, 10)


def _validate_ar_metadata(header: bytes) -> None:
    _parse_decimal(header[16:28], label="timestamp", allow_empty=True)
    _parse_decimal(header[28:34], label="uid", allow_empty=True)
    _parse_decimal(header[34:40], label="gid", allow_empty=True)
    mode = header[40:48].strip(b" ")
    if not mode or any(byte < ord("0") or byte > ord("7") for byte in mode):
        raise MasstreeArchiveProjectionError("ar mode is not octal")


def _gnu_long_name(table: bytes, offset: int) -> str:
    if offset < 0 or offset >= len(table):
        raise MasstreeArchiveProjectionError("GNU ar long-name offset is invalid")
    end = table.find(b"/\n", offset)
    if end < 0 or end == offset:
        raise MasstreeArchiveProjectionError("GNU ar long-name entry is invalid")
    raw = table[offset:end]
    try:
        name = raw.decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise MasstreeArchiveProjectionError(
            "GNU ar long-name entry is not ASCII"
        ) from exc
    if "/" in name or "\x00" in name:
        raise MasstreeArchiveProjectionError("GNU ar member name is invalid")
    return name


def _parse_ar(raw: bytes) -> tuple[tuple[_ArMember, ...], bytes, bool]:
    if not raw.startswith(_AR_MAGIC):
        raise MasstreeArchiveProjectionError("archive is not a GNU ar file")
    offset = len(_AR_MAGIC)
    members: list[_ArMember] = []
    symbol_table: bytes | None = None
    symbol_table_64 = False
    long_names: bytes | None = None
    pending_long_members: list[tuple[int, int, bytes]] = []
    while offset < len(raw):
        header_offset = offset
        if len(raw) - offset < _AR_HEADER_SIZE:
            raise MasstreeArchiveProjectionError("ar member header is truncated")
        header = raw[offset:offset + _AR_HEADER_SIZE]
        offset += _AR_HEADER_SIZE
        if header[58:60] != b"`\n":
            raise MasstreeArchiveProjectionError("ar member trailer is invalid")
        _validate_ar_metadata(header)
        size = _parse_decimal(header[48:58], label="member size")
        end = offset + size
        if end < offset or end > len(raw):
            raise MasstreeArchiveProjectionError("ar member payload is truncated")
        payload = raw[offset:end]
        offset = end
        if size & 1:
            if offset >= len(raw) or raw[offset:offset + 1] != b"\n":
                raise MasstreeArchiveProjectionError("ar member padding is invalid")
            offset += 1

        name_field = header[:16].rstrip(b" ")
        if name_field == b"/":
            if symbol_table is not None:
                raise MasstreeArchiveProjectionError("ar has duplicate symbol indexes")
            symbol_table = payload
            continue
        if name_field == b"/SYM64/":
            if symbol_table is not None:
                raise MasstreeArchiveProjectionError("ar has duplicate symbol indexes")
            symbol_table = payload
            symbol_table_64 = True
            continue
        if name_field == b"//":
            if long_names is not None:
                raise MasstreeArchiveProjectionError("ar has duplicate name tables")
            long_names = payload
            continue
        if name_field.startswith(b"#1/"):
            raise MasstreeArchiveProjectionError("BSD ar member names are unsupported")
        if name_field.startswith(b"/"):
            reference = name_field[1:]
            if not reference or not reference.isdigit():
                raise MasstreeArchiveProjectionError("unknown GNU ar index format")
            pending_long_members.append((header_offset, int(reference), payload))
            continue
        if not name_field.endswith(b"/"):
            raise MasstreeArchiveProjectionError("GNU ar member name lacks terminator")
        raw_name = name_field[:-1]
        try:
            name = raw_name.decode("ascii", "strict")
        except UnicodeDecodeError as exc:
            raise MasstreeArchiveProjectionError("ar member name is not ASCII") from exc
        if not name or "/" in name or "\x00" in name:
            raise MasstreeArchiveProjectionError("ar member name is invalid")
        members.append(_ArMember(name, header_offset, payload))

    if offset != len(raw):
        raise MasstreeArchiveProjectionError("archive has trailing bytes")
    if pending_long_members:
        if long_names is None:
            raise MasstreeArchiveProjectionError("ar long-name table is missing")
        members.extend(
            _ArMember(_gnu_long_name(long_names, name_offset), header_offset, payload)
            for header_offset, name_offset, payload in pending_long_members
        )
        members.sort(key=lambda member: member.header_offset)
    if symbol_table is None:
        raise MasstreeArchiveProjectionError("GNU ar symbol index is missing")
    if tuple(member.name for member in members) != MASSTREE_MEMBERS:
        raise MasstreeArchiveProjectionError(
            "masstree archive member names/order differ from the exact recipe"
        )
    return tuple(members), symbol_table, symbol_table_64


def _cstring(table: bytes, offset: int, *, label: str) -> bytes:
    if offset < 0 or offset >= len(table):
        raise MasstreeArchiveProjectionError(f"{label} offset is invalid")
    end = table.find(b"\x00", offset)
    if end < 0:
        raise MasstreeArchiveProjectionError(f"{label} is not NUL terminated")
    return table[offset:end]


def _direct_debug_name(name: bytes) -> bool:
    return (
        name.startswith(b".debug")
        or name.startswith(b".zdebug")
        or name == b".gdb_index"
        or name.startswith(b".stab")
    )


def _debug_exclusion_reason(
    section: _ElfSection,
    sections: tuple[_ElfSection, ...],
    *,
    resolving: frozenset[int] = frozenset(),
) -> bool:
    if section.index in resolving:
        raise MasstreeArchiveProjectionError(
            "ELF debug relocation targets form a cycle"
        )
    direct = _direct_debug_name(section.name)
    relocation = False
    relocation_target: _ElfSection | None = None
    if section.section_type in {_SHT_REL, _SHT_RELA}:
        if section.info >= len(sections):
            raise MasstreeArchiveProjectionError(
                "ELF relocation target index is out of range"
            )
        relocation_target = sections[section.info]
        relocation = (
            section.name.startswith(b".rel")
            and _direct_debug_name(relocation_target.name)
        )
    exclude = direct or relocation
    if not exclude:
        return False
    if section.flags & (_SHF_ALLOC | _SHF_EXECINSTR):
        raise MasstreeArchiveProjectionError(
            "debug-named ELF section is loadable or executable"
        )
    if section.section_type not in _DEBUG_SECTION_TYPES:
        raise MasstreeArchiveProjectionError(
            "debug-named ELF section has a disallowed type"
        )
    if (relocation_target is not None
            and not _debug_exclusion_reason(
                relocation_target,
                sections,
                resolving=resolving | {section.index},
            )):
        raise MasstreeArchiveProjectionError(
            "debug-named ELF relocation targets a retained section"
        )
    return True


def _parse_elf(
    member: _ArMember,
) -> tuple[bytes, tuple[int, ...], tuple[_ElfSection, ...]]:
    raw = member.payload
    if len(raw) < _ELF_HEADER.size:
        raise MasstreeArchiveProjectionError(f"{member.name}: ELF header is truncated")
    (
        ident, elf_type, machine, version, entry, phoff, shoff, flags,
        ehsize, phentsize, phnum, shentsize, shnum, shstrndx,
    ) = _ELF_HEADER.unpack_from(raw)
    if (
        ident[:4] != b"\x7fELF"
        or ident[4] != 2
        or ident[5] != 1
        or ident[6] != 1
        or elf_type != 1
        or machine != 62
        or version != 1
        or ehsize != _ELF_HEADER.size
        or phnum != 0
        or phoff != 0
        or shentsize != _ELF_SECTION.size
        or shnum == 0
        or shstrndx >= shnum
    ):
        raise MasstreeArchiveProjectionError(
            f"{member.name}: ELF64 little-endian x86-64 ET_REL contract differs"
        )
    table_end = shoff + shnum * shentsize
    if shoff < ehsize or table_end < shoff or table_end > len(raw):
        raise MasstreeArchiveProjectionError(
            f"{member.name}: ELF section table is out of range"
        )
    headers = [
        _ELF_SECTION.unpack_from(raw, shoff + index * shentsize)
        for index in range(shnum)
    ]
    shstr = headers[shstrndx]
    if shstr[1] != _SHT_STRTAB or shstr[2] & (_SHF_ALLOC | _SHF_EXECINSTR):
        raise MasstreeArchiveProjectionError(
            f"{member.name}: ELF section-name table is invalid"
        )
    shstr_end = shstr[4] + shstr[5]
    if shstr_end < shstr[4] or shstr_end > len(raw):
        raise MasstreeArchiveProjectionError(
            f"{member.name}: ELF section-name table is out of range"
        )
    names = raw[shstr[4]:shstr_end]
    sections: list[_ElfSection] = []
    for index, values in enumerate(headers):
        (
            name_offset, section_type, section_flags, address, section_offset,
            section_size, link, info, alignment, entry_size,
        ) = values
        name = _cstring(names, name_offset, label="ELF section name")
        if link >= shnum and link != 0:
            raise MasstreeArchiveProjectionError(
                f"{member.name}: ELF section link is out of range"
            )
        if alignment and alignment & (alignment - 1):
            raise MasstreeArchiveProjectionError(
                f"{member.name}: ELF section alignment is not a power of two"
            )
        if section_type == _SHT_NOBITS:
            content = b""
        else:
            content_end = section_offset + section_size
            if content_end < section_offset or content_end > len(raw):
                raise MasstreeArchiveProjectionError(
                    f"{member.name}: ELF section content is out of range"
                )
            content = raw[section_offset:content_end]
        sections.append(_ElfSection(
            index=index,
            name=name,
            section_type=section_type,
            flags=section_flags,
            address=address,
            offset=section_offset,
            size=section_size,
            link=link,
            info=info,
            alignment=alignment,
            entry_size=entry_size,
            content=content,
        ))
    if headers[0] != (0, 0, 0, 0, 0, 0, 0, 0, 0, 0):
        raise MasstreeArchiveProjectionError(
            f"{member.name}: ELF null section is not canonical"
        )
    retained = tuple(
        section for section in sections
        if not _debug_exclusion_reason(section, tuple(sections))
    )
    header_identity = (
        elf_type, machine, version, entry, flags, ehsize, phentsize, phnum,
        shentsize,
    )
    return ident, header_identity, retained


def _parse_symbol_index(
    raw: bytes, *, wide: bool, offset_names: dict[int, str],
) -> tuple[tuple[bytes, str], ...]:
    width = 8 if wide else 4
    if len(raw) < width:
        raise MasstreeArchiveProjectionError("ar symbol index is truncated")
    count = int.from_bytes(raw[:width], "big")
    offsets_end = width + count * width
    if offsets_end < width or offsets_end > len(raw):
        raise MasstreeArchiveProjectionError("ar symbol offsets are truncated")
    offsets = [
        int.from_bytes(raw[width + index * width:width + (index + 1) * width], "big")
        for index in range(count)
    ]
    cursor = offsets_end
    symbols: list[bytes] = []
    for _index in range(count):
        end = raw.find(b"\x00", cursor)
        if end < 0:
            raise MasstreeArchiveProjectionError("ar symbol name is not terminated")
        symbol = raw[cursor:end]
        if not symbol:
            raise MasstreeArchiveProjectionError("ar symbol name is empty")
        symbols.append(symbol)
        cursor = end + 1
    trailing = raw[cursor:]
    if len(trailing) > 7 or any(trailing):
        raise MasstreeArchiveProjectionError("ar symbol index has trailing bytes")
    normalized: list[tuple[bytes, str]] = []
    for symbol, member_offset in zip(symbols, offsets, strict=True):
        member_name = offset_names.get(member_offset)
        if member_name is None:
            raise MasstreeArchiveProjectionError(
                "ar symbol index does not resolve to an object member"
            )
        normalized.append((symbol, member_name))
    return tuple(normalized)


def _canonical_projection(raw: bytes) -> str:
    members, index, wide_index = _parse_ar(raw)
    canonical = _CanonicalHash()
    canonical.record(b"member-count", _u64(len(members)))
    for member in members:
        canonical.record(b"member", member.name.encode("ascii"))
        ident, header_identity, sections = _parse_elf(member)
        canonical.record(b"elf-ident", ident)
        canonical.record(
            b"elf-header", *(_u64(value) for value in header_identity),
        )
        canonical.record(b"section-count", _u64(len(sections)))
        for section in sections:
            canonical.record(
                b"section",
                section.name,
                _u64(section.section_type),
                _u64(section.flags),
                _u64(section.address),
                _u64(section.size),
                _u64(section.link),
                _u64(section.info),
                _u64(section.alignment),
                _u64(section.entry_size),
                section.content,
            )
    symbols = _parse_symbol_index(
        index,
        wide=wide_index,
        offset_names={member.header_offset: member.name for member in members},
    )
    canonical.record(b"symbol-count", _u64(len(symbols)))
    for symbol, member_name in symbols:
        canonical.record(b"symbol", symbol, member_name.encode("ascii"))
    return canonical.hexdigest()


def masstree_archive_digests(path: Path) -> MasstreeArchiveDigests:
    """Path を no-follow で一度だけ読み、raw と非 debug digest を返す。"""
    candidate = Path(path)
    descriptor = -1
    try:
        entry = candidate.lstat()
        if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
            raise MasstreeArchiveProjectionError(
                "archive is not a non-symlink regular file"
            )
        if not hasattr(os, "O_NOFOLLOW"):
            raise MasstreeArchiveProjectionError("O_NOFOLLOW is unavailable")
        descriptor = os.open(
            candidate,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or (entry.st_dev, entry.st_ino) != (before.st_dev, before.st_ino)
            or before.st_size > _MAX_ARCHIVE_BYTES
        ):
            raise MasstreeArchiveProjectionError(
                "archive identity or bounded size is invalid"
            )
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        captured_bytes = 0
        while True:
            chunk = os.read(
                descriptor,
                min(1024 * 1024, _MAX_ARCHIVE_BYTES - captured_bytes + 1),
            )
            if not chunk:
                break
            captured_bytes += len(chunk)
            if captured_bytes > _MAX_ARCHIVE_BYTES:
                raise MasstreeArchiveProjectionError(
                    "archive exceeded the bounded capture size"
                )
            digest.update(chunk)
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise MasstreeArchiveProjectionError(f"cannot capture archive: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    stable_before = (
        before.st_dev, before.st_ino, before.st_size,
        before.st_mtime_ns, before.st_ctime_ns,
    )
    stable_after = (
        after.st_dev, after.st_ino, after.st_size,
        after.st_mtime_ns, after.st_ctime_ns,
    )
    raw = b"".join(chunks)
    if stable_before != stable_after or len(raw) != before.st_size:
        raise MasstreeArchiveProjectionError("archive changed while being captured")
    return MasstreeArchiveDigests(
        raw_sha256=digest.hexdigest(),
        archive_nondebug_sha256=_canonical_projection(raw),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="print gnu-ar-elf-nondebug/v1 digest for one masstree archive",
    )
    parser.add_argument("archive", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = masstree_archive_digests(args.archive)
    except MasstreeArchiveProjectionError as exc:
        print(f"masstree_archive_projection: {exc}", file=sys.stderr)
        return 2
    print(result.archive_nondebug_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
