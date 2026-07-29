#!/usr/bin/env python3
"""Codex の ``-o`` 成果物に対する最小限の機械検収。"""
from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path
from typing import Pattern, Sequence

_DEFAULT_MIN_BYTES = 500
_DEFAULT_HEADING = r"^## 総括"
_MAX_READ_BYTES = 10 * 1024 * 1024
_FENCE_OPEN = re.compile(r"^[ \t]*(`{3,})([^`]*)$")


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("整数を指定すること") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("1 以上を指定すること")
    return parsed


def _heading_regex(parser: argparse.ArgumentParser, value: str) -> Pattern[str]:
    try:
        return re.compile(value, re.MULTILINE)
    except re.error as exc:
        parser.error(f"--require-heading の regex が不正: {exc}")
        raise AssertionError("argparse.ArgumentParser.error must exit")


def _without_fenced_code(text: str) -> str:
    """backtick 3 個以上の fenced code block と fence 行を本文から除く。"""
    kept: list[str] = []
    fence_width: int | None = None
    for line in text.splitlines(keepends=True):
        logical = line.rstrip("\r\n")
        if fence_width is None:
            opening = _FENCE_OPEN.fullmatch(logical)
            if opening:
                fence_width = len(opening.group(1))
                continue
            kept.append(line)
            continue
        if re.fullmatch(rf"[ \t]*`{{{fence_width},}}[ \t]*", logical):
            fence_width = None
    return "".join(kept)


def _read_at_most(fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    remaining = limit
    while remaining:
        chunk = os.read(fd, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def check_file(path: Path, *, min_bytes: int, heading: Pattern[str]) -> list[str]:
    """検査可能な違反をすべて返す。特殊ファイルは読み取らない。"""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        return ["O_NOFOLLOW 非対応環境のため安全に対象を開けない"]
    flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        return [f"対象を symlink 非追跡で開けない ({exc})"]

    try:
        try:
            metadata = os.fstat(fd)
        except OSError as exc:
            return [f"open 済み対象を fstat できない ({exc})"]
        if not stat.S_ISREG(metadata.st_mode):
            return ["対象は regular file ではない (non-regular file)"]

        failures: list[str] = []
        if metadata.st_size > _MAX_READ_BYTES:
            failures.append(
                f"read 上限 10MB を超過 ({metadata.st_size} > {_MAX_READ_BYTES})"
            )
            return failures
        try:
            raw = _read_at_most(fd, _MAX_READ_BYTES + 1)
        except OSError as exc:
            failures.append(f"open 済み対象を読み取れない ({exc})")
            return failures
    finally:
        os.close(fd)

    if len(raw) < min_bytes:
        failures.append(f"raw byte 数が不足 ({len(raw)} < {min_bytes})")
    if len(raw) > _MAX_READ_BYTES:
        failures.append(
            f"read 上限 10MB を超過 (読込中に {_MAX_READ_BYTES} bytes を超過)"
        )
        return failures
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"非 UTF-8 成果物 ({exc})")
        return failures
    body = _without_fenced_code(text)
    if heading.search(body) is None:
        failures.append(f"fenced code block 外に必須見出しが無い ({heading.pattern})")
    return failures


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Codex -o 成果物の file/size/見出しを検査する。"
            "総括と本文の意味・件数の整合は scope 外で、親が内容を検収する。"
        )
    )
    parser.add_argument("file", type=Path, help="検査対象 file")
    parser.add_argument(
        "--min-bytes",
        type=_positive_int,
        default=_DEFAULT_MIN_BYTES,
        metavar="N",
        help=f"必要な raw byte 数 (既定: {_DEFAULT_MIN_BYTES}, N >= 1)",
    )
    parser.add_argument(
        "--require-heading",
        default=_DEFAULT_HEADING,
        metavar="REGEX",
        help=f"fence 外で必要な heading regex (既定: {_DEFAULT_HEADING!r})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    heading = _heading_regex(parser, args.require_heading)
    failures = check_file(args.file, min_bytes=args.min_bytes, heading=heading)
    if failures:
        for failure in failures:
            print(f"NG: {failure}", file=sys.stderr)
        return 1
    print(f"OK: Codex output passed ({os.fspath(args.file)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
