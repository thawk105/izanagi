#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を検査する。

この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである。
この検査だけで trace の完全除去を証明したと解釈してはならない。
この保証は使用した compiler と選定した macro context に依存し、admission toolchain と同一であるとは主張しない。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign.genome import SILO_SPACE  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EVOLVE_BLOCK_SOURCE_PROTOCOLS,
    _INCLUDE_RE,
    _assert_conditional_macros_covered,
    _assert_proven_repo_absent_macros,
    _context_overlays,
    _cpp_normalize,
    _git_show,
    _head_defines,
    _include_lines,
    _lex_normalize,
    _splice_c_line_continuations,
    _strip_utf8_bom,
)


GUARANTEE = (
    "選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、"
    "および include 活性の同一性"
)
SCHEMA = "izanagi-trace0-preprocess-identity/v2"
_FULL_OID_RE = re.compile(r"[0-9a-f]{40}\Z")
_SOURCE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cxx"})
_HEADER_SUFFIXES = frozenset({
    ".h", ".h++", ".hh", ".hp", ".hpp", ".hxx", ".inl", ".ipp", ".tcc",
})
HEADER_GUARANTEE = (
    "選定 configure 集合の compile database に載る変更 header consumer entry における、"
    "TRACE=0 完全展開と include 活性の同一性"
)
HEADER_SCOPE = "この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである"
_GENERATED_TARGETS = ("masstree_build",)
_MARKER_PREFIX = "IZANAGI_TRACE0_INCLUDE_MARKER_"
_MOCC_TRANSACTION_PATH = "cc/mocc/transaction.cc"
_MOCC_TRACE_INCLUDE_LINE = '#include "../../include/trace.hh"'
_CONDITIONAL_DIRECTIVE_RE = re.compile(
    r"^[ \t]*#[ \t]*(if|ifdef|ifndef|elif|elifdef|elifndef|else|endif)\b(.*)$"
)
_TRACE_IF_EXPRESSION_RE = re.compile(r"^[ \t]*TRACE[ \t]*$")
_HASH_DIRECTIVE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*([A-Za-z_]\w*)\b(.*)$")
_DIGRAPH_DIRECTIVE_RE = re.compile(r"(?m)^[ \t]*%:")
_LOGICAL_LITERAL_INCLUDE_RE = re.compile(
    r'^[ \t]*#[ \t]*include\b[ \t]*(?:""|<[^>\r\n]+>)[ \t]*$'
)


class CheckError(RuntimeError):
    """選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を確認できない。"""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        super().error(f"{GUARANTEE}を確認できない: {message}")


def _full_oid(value: str) -> str:
    if not _FULL_OID_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"{GUARANTEE}の検査には 40 桁 lowercase hex commit OID が必要"
        )
    return value


def _run_git(repo: Path, args: Sequence[str], *, binary: bool = False) -> str | bytes:
    command = ["git", "-C", os.fspath(repo), *args]
    try:
        result = subprocess.run(command, capture_output=True, text=not binary)
    except (OSError, subprocess.SubprocessError) as exc:
        raise CheckError(f"git を起動できない ({exc})") from exc
    if result.returncode != 0:
        stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode(
            "utf-8", errors="replace"
        )
        raise CheckError(
            f"git {' '.join(args)} が失敗 (rc={result.returncode}): {stderr.strip()[-500:]}"
        )
    return result.stdout


def _resolve_commit(repo: Path, requested: str) -> str:
    output = _run_git(repo, ["rev-parse", "--verify", f"{requested}^{{commit}}"])
    assert isinstance(output, str)
    resolved = output.strip()
    if not _FULL_OID_RE.fullmatch(resolved):
        raise CheckError(f"commit 解決結果が 40 桁 lowercase hex でない: {resolved!r}")
    return resolved


def _is_ancestor(repo: Path, old_oid: str, new_oid: str) -> bool:
    command = ["git", "-C", os.fspath(repo), "merge-base", "--is-ancestor", old_oid, new_oid]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise CheckError(f"祖先関係を照合できない ({exc})") from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise CheckError(
        f"祖先関係の照合が失敗 (rc={result.returncode}): {result.stderr.strip()[-500:]}"
    )


def _decode_path(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CheckError("diff path が UTF-8 でなく JSON evidence に表現できない") from exc


def _raw_diff(repo: Path, old_oid: str, new_oid: str) -> list[dict[str, object]]:
    output = _run_git(
        repo,
        ["diff-tree", "--raw", "-r", "-z", "--no-renames", old_oid, new_oid],
        binary=True,
    )
    assert isinstance(output, bytes)
    fields = output.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()

    entries: list[dict[str, object]] = []
    index = 0
    while index < len(fields):
        header = fields[index]
        index += 1
        if not header.startswith(b":"):
            raise CheckError(f"git raw diff header が未対応形: {header[:120]!r}")
        parts = header[1:].split()
        if len(parts) != 5:
            raise CheckError(f"git raw diff header の field 数が未対応: {header[:120]!r}")
        old_mode_b, new_mode_b, old_blob_b, new_blob_b, status_b = parts
        try:
            old_mode = old_mode_b.decode("ascii")
            new_mode = new_mode_b.decode("ascii")
            old_blob = old_blob_b.decode("ascii")
            new_blob = new_blob_b.decode("ascii")
            status = status_b.decode("ascii")
        except UnicodeDecodeError as exc:
            raise CheckError("git raw diff metadata が ASCII でない") from exc
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(fields):
            raise CheckError("git raw diff の path field が欠落")
        paths = [_decode_path(value) for value in fields[index:index + path_count]]
        index += path_count
        entry: dict[str, object] = {
            "status": status,
            "path": paths[-1],
            "old_mode": old_mode,
            "new_mode": new_mode,
            "old_blob": old_blob,
            "new_blob": new_blob,
        }
        if len(paths) == 2:
            entry["old_path"] = paths[0]
        entries.append(entry)
    return entries


def _validate_diff(entries: list[dict[str, object]], *, header_enabled: bool = False) -> None:
    if not entries:
        raise CheckError("差分が空で対象 0 件")
    for entry in entries:
        status = entry["status"]
        path = entry["path"]
        if status != "M":
            raise CheckError(f"未対応の diff status {status!r}: {path!r} (A/D/R/C は拒否)")
        old_mode = entry["old_mode"]
        new_mode = entry["new_mode"]
        if old_mode != new_mode:
            raise CheckError(f"mode/type change は未対応: {path!r} ({old_mode} -> {new_mode})")
        if not isinstance(old_mode, str) or not old_mode.startswith("100"):
            raise CheckError(f"regular file でない C/C++ path は未対応: {path!r} mode={old_mode}")
        suffix = PurePosixPath(path).suffix.lower() if isinstance(path, str) else ""
        if suffix in _HEADER_SUFFIXES:
            if not header_enabled:
                raise CheckError(
                    "header の変更は consumer TU での解析が必要であり、この checker の保証範囲外なので "
                    f"fail-closed で拒否する: {path!r}"
                )
            continue
        if not isinstance(path, str) or suffix not in _SOURCE_SUFFIXES:
            raise CheckError(f"C/C++ regular source/header 以外の変更は未対応: {path!r}")


def _validate_expected_paths(
    entries: list[dict[str, object]], expect_paths: Sequence[str] | None
) -> list[str] | None:
    if expect_paths is None:
        return None
    expected = list(expect_paths)
    if not expected:
        raise CheckError("--expect-paths が指定されたが期待 path 集合が空")
    if len(expected) != len(set(expected)):
        raise CheckError(f"--expect-paths に重複 path がある: {expected!r}")
    actual = [entry["path"] for entry in entries]
    if any(not isinstance(path, str) for path in actual):
        raise CheckError("diff path 集合を文字列として確定できない")
    if len(actual) != len(set(actual)):
        raise CheckError(f"diff path 集合に重複がある未対応形: {actual!r}")
    if set(actual) != set(expected):
        raise CheckError(
            "diff path 集合が --expect-paths と厳密一致しない: "
            f"expected={sorted(expected)!r} actual={sorted(actual)!r}"
        )
    return sorted(expected)


def _compiler_identity(requested: str) -> tuple[str, str]:
    found = shutil.which(requested)
    if found is None:
        raise CheckError(f"compiler が存在しない、または実行不能: {requested!r}")
    compiler = os.path.realpath(found)
    try:
        result = subprocess.run([compiler, "--version"], capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise CheckError(f"compiler version を取得できない ({compiler}: {exc})") from exc
    lines = (result.stdout or result.stderr).splitlines()
    if result.returncode != 0 or not lines or not lines[0].strip():
        raise CheckError(
            f"compiler version を取得できない ({compiler}, rc={result.returncode})"
        )
    return compiler, lines[0].strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _independent_sha256_pair(old_value: bytes, new_value: bytes) -> tuple[str, str]:
    """旧側と新側を別々の digest 演算として evidence 化する。"""
    return _sha256(old_value), _sha256(new_value)


def _comparison_evidence(old_value: bytes, new_value: bytes) -> dict[str, object]:
    """元値と独立 digest の両方から同一性 evidence を作る。"""
    old_digest, new_digest = _independent_sha256_pair(old_value, new_value)
    value_identical = old_value == new_value
    digest_identical = old_digest == new_digest
    if value_identical != digest_identical:
        raise CheckError("値と digest の同一性が不整合")
    return {
        "old_sha256": old_digest,
        "new_sha256": new_digest,
        "identical": value_identical,
    }


def _context_tag(overlay: dict[str, str]) -> str:
    return ",".join(f"{key}={value}" for key, value in sorted(overlay.items())) or "base"


def _raw_include_operand_is_literal(line: str) -> bool:
    match = re.match(r"^[ \t]*#[ \t]*include\b", line)
    if match is None:
        return False
    rest = line[match.end():].lstrip(" \t")
    if rest.startswith('"'):
        end = rest.find('"', 1)
        if end <= 1:
            return False
    elif rest.startswith("<"):
        end = rest.find(">", 1)
        if end <= 1:
            return False
    else:
        return False
    trailing = rest[end + 1:].lstrip(" \t")
    return not trailing or trailing.startswith(("//", "/*"))


def _assert_literal_include_operands(source: str, path: str, side: str) -> None:
    """include/import directive の認識面を固定し、literal include だけを許す。"""
    try:
        logical = _lex_normalize(source, path)
    except RuntimeError as exc:
        raise CheckError(str(exc)) from exc
    spliced = _splice_c_line_continuations(source)
    if _DIGRAPH_DIRECTIVE_RE.search(source) or _DIGRAPH_DIRECTIVE_RE.search(spliced):
        raise CheckError(f"digraph directive (%:) は未対応: {side} {path}")

    logical_directives = list(_HASH_DIRECTIVE_RE.finditer(logical))
    if any(match.group(1).lower() == "import" for match in logical_directives):
        raise CheckError(f"#import directive は未対応: {side} {path}")

    raw_includes = [
        match for match in _HASH_DIRECTIVE_RE.finditer(source)
        if match.group(1).lower() == "include"
    ]
    logical_includes = [
        match for match in logical_directives
        if match.group(1).lower() == "include"
    ]
    marker_base = "IZANAGI_TRACE0_RAW_INCLUDE_ORIGIN_"
    while marker_base in source:
        marker_base += "X"
    pieces: list[str] = []
    previous = 0
    origin_markers: list[str] = []
    for index, raw_match in enumerate(raw_includes):
        marker = f"{marker_base}{index:08d}"
        origin_markers.append(marker)
        pieces.extend((source[previous:raw_match.start()], marker, "\n"))
        previous = raw_match.start()
    pieces.append(source[previous:])
    try:
        marked_logical = _lex_normalize("".join(pieces), path)
    except RuntimeError as exc:
        raise CheckError(str(exc)) from exc
    corresponding_logical: list[str] = []
    for marker in origin_markers:
        match = re.search(
            rf"(?m)^[ \t]*{re.escape(marker)}[ \t]*\n"
            rf"(?P<directive>[ \t]*#[ \t]*include\b.*)$",
            marked_logical,
        )
        if match is not None:
            corresponding_logical.append(match.group("directive"))
    logical_spellings = [match.group(0) for match in logical_includes]
    unsupported_reasons: list[str] = []
    if corresponding_logical != logical_spellings:
        unsupported_reasons.append(
            "splice 後・comment 除去後にだけ現れる include directive、または raw と logical "
            "で同じ位置・綴りに対応しない include directive は未対応: "
            f"{side} {path}"
        )
    if len(raw_includes) != len(logical_includes):
        unsupported_reasons.append(
            "raw と logical の include directive 件数が一致しない未対応形: "
            f"{side} {path}"
        )
    if unsupported_reasons:
        raise CheckError("; ".join(unsupported_reasons))
    for raw_match, logical_match in zip(raw_includes, logical_includes):
        raw_line = raw_match.group(0)
        if "\\\n" in raw_line or raw_line.rstrip(" \t").endswith("\\"):
            raise CheckError(f"line-spliced include directive は未対応: {side} {path}")
        if not _raw_include_operand_is_literal(raw_line):
            raise CheckError(
                f"#include operand が literal header token でない: {side} {path}"
            )
        if _LOGICAL_LITERAL_INCLUDE_RE.fullmatch(logical_match.group(0)) is None:
            raise CheckError(
                f"#include operand が literal header token でない: {side} {path}"
            )


def _mark_includes(source_text: str) -> tuple[str, list[str]]:
    if _MARKER_PREFIX in source_text:
        raise CheckError("include marker prefix が source に存在する未対応形")
    include_count = len(_INCLUDE_RE.findall(source_text))
    markers = [f"{_MARKER_PREFIX}{index:08d}" for index in range(include_count)]
    spliced_source = _splice_c_line_continuations(source_text)
    for marker in markers:
        if re.search(rf"\b{re.escape(marker)}\b", spliced_source):
            raise CheckError(f"include marker 識別子が source と衝突する未対応形: {marker}")
    marker_iter = iter(markers)
    body = _INCLUDE_RE.sub(lambda _match: next(marker_iter), source_text)
    preamble = "".join(f"#undef {marker}\n#define {marker} {marker}\n" for marker in markers)
    return preamble + body, markers


def _active_markers(normalized: str, markers: list[str]) -> list[str]:
    if not markers:
        return []
    alternatives = "|".join(re.escape(marker) for marker in markers)
    pattern = re.compile(rf"(?m)^[ \t]*({alternatives})[ \t]*$")
    return [match.group(1) for match in pattern.finditer(normalized)]


def _trace_guard_is_inactive_at_zero(source_text: str, include_start: int) -> bool:
    """追加 include が単純な ``#if TRACE`` の真枝内にあるかを保守的に確認する。"""
    # The parser intentionally recognizes only the unambiguous ``#if TRACE`` form.
    # The shared lexical pass removes comments/literals first; an unparseable
    # prefix, compound expression, #elif, or #else is not enough evidence for
    # this exception and therefore remains fail-closed.
    try:
        prefix = _lex_normalize(source_text[:include_start], _MOCC_TRANSACTION_PATH)
    except RuntimeError:
        return False
    stack: list[tuple[bool, bool]] = []
    for line in prefix.splitlines():
        match = _CONDITIONAL_DIRECTIVE_RE.match(line)
        if match is None:
            continue
        directive, expression = match.groups()
        if directive == "if":
            stack.append((bool(_TRACE_IF_EXPRESSION_RE.fullmatch(expression)), True))
        elif directive in {"ifdef", "ifndef"}:
            stack.append((False, True))
        elif directive in {"elif", "elifdef", "elifndef", "else"}:
            if not stack:
                return False
            is_trace_if, is_initial_branch = stack[-1]
            stack[-1] = (is_trace_if, False)
        elif directive == "endif":
            if not stack:
                return False
            stack.pop()
    return any(is_trace_if and is_initial_branch for is_trace_if, is_initial_branch in stack)


def _mocc_trace_include_addition_index(
    path: str, old_source: str, new_source: str
) -> int | None:
    """Return the sole permitted mocc trace include insertion index, if any.

    D297 still requires the normalized TRACE=0 preprocess output to match below,
    and this exception preserves exact matching for every other include and marker.
    It permits one mechanically verifiable addition only: the exact trace.hh line
    in ``cc/mocc/transaction.cc`` inside the initial branch of ``#if TRACE``.
    Arbitrary include additions are never accepted by this helper.
    """
    if path != _MOCC_TRANSACTION_PATH:
        return None

    old_matches = list(_INCLUDE_RE.finditer(old_source))
    new_matches = list(_INCLUDE_RE.finditer(new_source))
    old_lines = [match.group(0) for match in old_matches]
    new_lines = [match.group(0) for match in new_matches]
    if len(new_lines) != len(old_lines) + 1:
        return None

    candidates = [
        index
        for index, line in enumerate(new_lines)
        if line.strip() == _MOCC_TRACE_INCLUDE_LINE
        and new_lines[:index] == old_lines[:index]
        and new_lines[index + 1:] == old_lines[index:]
    ]
    if len(candidates) != 1:
        return None

    index = candidates[0]
    if not _trace_guard_is_inactive_at_zero(new_source, new_matches[index].start()):
        return None
    return index


def validate_remaining_markers_map_exactly(
    path: str,
    old_active: list[str],
    new_active: list[str],
    old_markers: list[str],
    new_markers: list[str],
    added_index: int,
) -> None:
    """許可追加を除いた marker の活性と順序が old 列へ厳密に写るか検査する。"""
    mapped_new_active = [
        old_markers[index if index < added_index else index - 1]
        for index, marker in enumerate(new_markers)
        if index != added_index and marker in new_active
    ]
    if old_active != mapped_new_active:
        raise CheckError(f"include 活性（順序込み）が不一致: path={path!r}")


def _compare_include_activity(
    path: str,
    old_active: list[str],
    new_active: list[str],
    old_markers: list[str],
    new_markers: list[str],
    added_index: int | None,
) -> dict[str, object]:
    if added_index is None:
        if old_active != new_active:
            raise CheckError(f"include 活性（順序込み）が不一致: path={path!r}")
        return {
            "accepted": True,
            "basis": "exact_identity",
            "permitted_addition": None,
        }

    if len(new_markers) != len(old_markers) + 1:
        raise CheckError(f"include marker 列を構成できない未対応形: {path}")
    added_marker = new_markers[added_index]
    if added_marker in new_active:
        raise CheckError(
            "許可した mocc の trace.hh include が TRACE=0 で活性化したため拒否: "
            f"path={path!r}"
        )

    validate_remaining_markers_map_exactly(
        path, old_active, new_active, old_markers, new_markers, added_index
    )
    return {
        "accepted": True,
        "basis": "permitted_mocc_trace_include_addition",
        "permitted_addition": {
            "new_include_index": added_index,
            "new_marker": added_marker,
            "active_at_trace0": False,
        },
    }


def _compare_file(
    repo: Path,
    old_oid: str,
    new_oid: str,
    path: str,
    compiler: str,
    old_known_absent: frozenset[str],
    new_known_absent: frozenset[str],
    genomes: Sequence[Any],
    overlays: Sequence[dict[str, str]],
    expected_context_count: int,
) -> dict[str, object]:
    old_source = _git_show(os.fspath(repo), old_oid, path)
    new_source = _git_show(os.fspath(repo), new_oid, path)
    old_has_bom = old_source.startswith("\ufeff")
    new_has_bom = new_source.startswith("\ufeff")
    if old_has_bom != new_has_bom:
        raise CheckError(f"old/new の先頭 UTF-8 BOM 有無が不一致: {path}")
    try:
        old_source = _strip_utf8_bom(old_source)
        new_source = _strip_utf8_bom(new_source)
    except RuntimeError as exc:
        raise CheckError(f"先頭 UTF-8 BOM を正規化できない: {path}: {exc}") from exc
    _assert_literal_include_operands(old_source, path, "old")
    _assert_literal_include_operands(new_source, path, "new")
    old_includes = _include_lines(old_source)
    new_includes = _include_lines(new_source)
    added_include_index: int | None = None
    # D297 の保証（選定 macro context の TRACE=0 正規化 preprocess 出力と include 活性の同一性）は
    # 以下で従来どおり比較する。特別扱いは mocc の trace.hh 1 行だけを機械的に検証可能な形で
    # 許すものであり、任意の include 追加を許すものではない。
    if old_includes != new_includes:
        added_include_index = _mocc_trace_include_addition_index(path, old_source, new_source)
        if added_include_index is None:
            raise CheckError(f"include 行文字列（順序込み）が不一致: {path}")

    marked_old, old_markers = _mark_includes(old_source)
    marked_new, new_markers = _mark_includes(new_source)
    if old_markers != new_markers:
        if added_include_index is None or len(new_markers) != len(old_markers) + 1:
            raise CheckError(f"include marker 列を構成できない未対応形: {path}")

    source_rel = path if path in EVOLVE_BLOCK_SOURCE_PROTOCOLS else None
    contexts: list[dict[str, object]] = []
    for genome in genomes:
        old_defines = dict(
            _head_defines(os.fspath(repo), genome, old_oid, source_rel)
        )
        new_defines = dict(
            _head_defines(os.fspath(repo), genome, new_oid, source_rel)
        )
        old_defines["TRACE"] = "0"
        new_defines["TRACE"] = "0"
        _assert_conditional_macros_covered(
            old_source, old_defines, compiler, path, old_known_absent
        )
        _assert_conditional_macros_covered(
            new_source, new_defines, compiler, path, new_known_absent
        )

        for overlay in overlays:
            old_context_defines = dict(old_defines, **overlay)
            new_context_defines = dict(new_defines, **overlay)
            # TRACE は genome 由来 defines と context overlay の双方より後に固定する。
            old_context_defines["TRACE"] = "0"
            new_context_defines["TRACE"] = "0"
            tag = _context_tag(overlay)
            old_normalized = _cpp_normalize(old_source, old_context_defines, compiler).encode("utf-8")
            new_normalized = _cpp_normalize(new_source, new_context_defines, compiler).encode("utf-8")
            normalized_evidence = _comparison_evidence(old_normalized, new_normalized)
            if not normalized_evidence["identical"]:
                raise CheckError(
                    f"TRACE=0 正規化 preprocess 出力が不一致: path={path!r} "
                    f"genome={genome.canonical()!r} context={tag!r}"
                )

            old_marked_output = _cpp_normalize(
                marked_old, old_context_defines, compiler
            )
            new_marked_output = _cpp_normalize(
                marked_new, new_context_defines, compiler
            )
            old_active = _active_markers(old_marked_output, old_markers)
            new_active = _active_markers(new_marked_output, new_markers)
            try:
                policy_decision = _compare_include_activity(
                    path,
                    old_active,
                    new_active,
                    old_markers,
                    new_markers,
                    added_include_index,
                )
            except CheckError as exc:
                raise CheckError(
                    f"{exc} genome={genome.canonical()!r} context={tag!r}"
                ) from exc

            old_activity_bytes = "\0".join(old_active).encode("ascii")
            new_activity_bytes = "\0".join(new_active).encode("ascii")
            activity_evidence = _comparison_evidence(
                old_activity_bytes, new_activity_bytes
            )
            contexts.append({
                "genome": genome.canonical(),
                "context": tag,
                "overlay": dict(sorted(overlay.items())),
                "defines": {
                    "old": dict(sorted(old_context_defines.items())),
                    "new": dict(sorted(new_context_defines.items())),
                },
                "normalized_preprocess": normalized_evidence,
                "include_activity": {
                    "old_active_markers": old_active,
                    "new_active_markers": new_active,
                    **activity_evidence,
                    "policy_comparison": policy_decision,
                },
            })

    if len(contexts) != expected_context_count:
        raise CheckError(
            "context 比較件数が列挙元から導出した期待数と一致しない: "
            f"path={path!r} expected={expected_context_count} actual={len(contexts)}"
        )

    return {
        "path": path,
        "include_line_count": len(old_markers),
        "include_lines_sha256": _sha256(old_includes.encode("utf-8")),
        "contexts": contexts,
        "result": "match",
    }


def _h_run(argv: Sequence[str], cwd: Path | None = None, timeout: int = 120) -> bytes:
    try:
        result = subprocess.run(list(map(os.fspath, argv)), cwd=cwd, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CheckError(f"header command を完了できない: {exc}") from exc
    if result.returncode:
        raise CheckError(f"header command 失敗 rc={result.returncode}: {result.stderr[-400:]!r}")
    return result.stdout


def _h_sources(repo: Path, old: str, new: str, root: Path) -> dict[str, Path]:
    bare = root / "objects.git"
    _h_run(["git", "clone", "--bare", "--no-local", repo, bare], timeout=300)
    (bare / "info" / "attributes").write_text("* -export-ignore\n* -export-subst\n")
    sources = {}
    for side, oid in (("old", old), ("new", new)):
        src = root / f"src-{side}"
        src.mkdir()
        expected = {}
        for row in _h_run(["git", "-C", bare, "ls-tree", "-r", "-z", oid]).split(b"\0"):
            if not row:
                continue
            meta, name = row.split(b"\t", 1)
            mode, kind, blob = meta.decode().split()
            if mode not in ("100644", "100755") or kind != "blob":
                raise CheckError(f"source tree に regular file 以外: {name!r}")
            expected[_decode_path(name)] = blob
        archive = root / f"{side}.tar"
        _h_run(["git", "-C", bare, "archive", "--format=tar", "-o", archive, oid], timeout=300)
        with tarfile.open(archive) as stream:
            for member in stream:
                dest = (src / member.name).resolve()
                if not dest.is_relative_to(src) or not (member.isdir() or member.isfile()):
                    raise CheckError(f"source archive member が未対応: {member.name}")
                if member.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with stream.extractfile(member) as reader, dest.open("wb") as writer:
                        shutil.copyfileobj(reader, writer)
                    dest.chmod(member.mode & 0o777)
        archive.unlink()
        actual = {p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file() and not p.is_symlink()}
        if actual != set(expected):
            raise CheckError(f"source tree file 集合が不一致: missing={sorted(set(expected)-actual)!r} extra={sorted(actual-set(expected))!r}")
        for name, blob in expected.items():
            data = (src / name).read_bytes()
            if hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() != blob:
                raise CheckError(f"source tree blob が不一致: {name}")
        sources[side] = src
    return sources


def _h_supply(genome: Any, src: Path, build: Path, toolchain: Mapping[str, Mapping[str, str]],
              prefix: Path, third: Mapping[str, Path]) -> tuple[list[str], list[str], str]:
    from orchestrator.campaign.buildcache import _v2_commands
    configure, build_argv = _v2_commands(
        genome, False, os.fspath(src), os.fspath(build), dict(toolchain), jobs=1,
        dependency_prefix=os.fspath(prefix), fetchcontent_base_dir=os.fspath(build / "_deps"),
        masstree_source_dir=third["masstree"], mimalloc_source_dir=third["mimalloc"],
        googletest_source_dir=third["googletest"],
    )
    if build_argv.count("--target") != 1:
        raise CheckError("production build argv の --target が不正")
    target = build_argv[build_argv.index("--target") + 1]
    return [*configure, "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCCBENCH_CCACHE=OFF"], list(_GENERATED_TARGETS), target


def _h_roots(src: Path, build: Path, generated: Path, third: Mapping[str, Path]) -> list[tuple[bytes, bytes]]:
    roots = [(os.fsencode(src), b"<SOURCE>"), (os.fsencode(build), b"<BUILD>"),
             (os.fsencode(generated), b"<GENERATED>")]
    roots += [(os.fsencode(path), f"<THIRD:{name}>".encode()) for name, path in third.items()]
    return sorted(dict(roots).items(), key=lambda item: -len(item[0]))


def _h_norm(value: bytes, roots: Sequence[tuple[bytes, bytes]]) -> bytes:
    for root, token in roots:
        value = value.replace(root, token)
    return value


def _h_entry(entry: dict[str, Any], roots: Sequence[tuple[bytes, bytes]]) -> tuple[tuple[str, str], list[str], tuple[str, str, tuple[str, ...]]]:
    argv = entry.get("arguments")
    if argv is None:
        argv = shlex.split(entry["command"])
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise CheckError("compile database argv が未対応形")
    file = Path(entry["file"])
    file = (file if file.is_absolute() else Path(entry["directory"]) / file).resolve()
    output = entry.get("output") or next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "-o"), "")
    if not output:
        output = next((a[2:] for a in argv if a.startswith("-o") and len(a) > 2), "")
    match = re.search(r"(?:^|/)CMakeFiles/([^/]+)\.dir(?:/|$)", output)
    if not match:
        raise CheckError(f"compile database target を特定できない: {output!r}")
    key = (_h_norm(os.fsencode(file), roots).decode(), match.group(1))
    signature = (key[0], key[1], tuple(_h_norm(os.fsencode(a), roots).decode() for a in argv))
    return key, argv, signature


def _h_args(argv: list[str], trace: int) -> list[str]:
    kept = []
    found = 0
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "-MG" or arg.startswith("@") or arg.startswith("-Wp,"):
            raise CheckError(f"opaque compiler argv: {arg!r}")
        if arg in ("-o", "-MF", "-MT", "-MQ"):
            if i + 1 == len(argv):
                raise CheckError(f"compiler argv の {arg} が欠落")
            i += 2
            continue
        if arg in ("-c", "-MD", "-MMD", "-MP") or any(arg.startswith(p) and arg != p for p in ("-o", "-MF", "-MT", "-MQ")):
            i += 1
            continue
        if arg.startswith("-DTRACE="):
            found += 1
            if arg != "-DTRACE=0":
                raise CheckError(f"TRACE argv が 0 でない: {arg!r}")
            arg = f"-DTRACE={trace}"
        kept.append(arg)
        i += 1
    if found > 1:
        raise CheckError("TRACE argv token が重複")
    if not found:
        kept.append(f"-DTRACE={trace}")
    return kept


def _h_dep(entry: dict[str, Any], argv: list[str], trace: int, depfile: Path) -> set[Path]:
    macros = _h_run([*_h_args(argv, trace), "-E", "-dM", "-MD", "-MF", depfile], Path(entry["directory"]))
    if not re.search(rb"(?m)^#define TRACE " + str(trace).encode() + rb"$", macros):
        raise CheckError(f"TRACE={trace} の実効値を確認できない: {entry['file']}")
    if not depfile.is_file():
        raise CheckError(f"dependency file が無い: {entry['file']}")
    raw = depfile.read_text().replace("\\\n", "")
    if ":" not in raw:
        raise CheckError("dependency file が未対応形")
    files = {(Path(entry["directory"]) / word).resolve() for word in shlex.split(raw.split(":", 1)[1])}
    if any(not path.is_file() for path in files):
        raise CheckError(f"dependency closure に存在しない file: {entry['file']}")
    return files


def _h_transitions(raw: bytes) -> bytes:
    lines = []
    for line in raw.splitlines(keepends=True):
        match = re.match(rb'^# [0-9]+ "([^"]+)"((?: [1-4])+)[\r]?\n$', line)
        if match:
            flags = [flag for flag in match[2].split() if flag in (b"1", b"2")]
            if flags:
                lines.append(b" ".join(flags) + b' "' + match[1] + b'"\n')
    return b"".join(lines)


def _h_compare(pair: dict[str, Any], key: tuple[str, str], label: str) -> dict[str, object]:
    modes = {}
    for side in ("old", "new"):
        row = pair[side]
        entry = row["entries"][key]
        # Compare two fixed expansions so live uses of volatile builtins cannot
        # accidentally compare equal just because both commands ran in one second.
        probes = []
        for marker in ("A", "B"):
            override = []
            for builtin in ("__DATE__", "__TIME__", "__TIMESTAMP__"):
                override.extend((f"-U{builtin}", f'-D{builtin}="IZANAGI_VOLATILE_{marker}"'))
            probes.append(_h_run(
                [*_h_args(entry["argv"], 0), *override, "-Wno-builtin-macro-redefined", "-E", "-P"],
                Path(entry["raw"]["directory"]),
            ))
        if probes[0] != probes[1]:
            raise CheckError(f"volatile builtin が完全展開に存在: {label} {key}")
    for mode, flags in (("expanded", ("-E", "-P", "-dD")), ("include_activity", ("-E",))):
        values = []
        for side in ("old", "new"):
            row = pair[side]
            entry = row["entries"][key]
            raw = _h_run([*_h_args(entry["argv"], 0), *flags], Path(entry["raw"]["directory"]))
            value = _h_transitions(raw) if mode == "include_activity" else raw
            values.append(_h_norm(value, row["roots"]))
        evidence = _comparison_evidence(*values)
        if not evidence["identical"]:
            raise CheckError(f"header {mode} 不一致: configure={label} entry={key}")
        modes[mode] = evidence
    return {"file": key[0], "target": key[1], "modes": modes}


def _h_check(
    repo: Path, old: str, new: str, headers: list[str], cc: str, cxx: str,
    cache: Path, prefix: Path, scratch_root: Path,
    supply: Callable[..., tuple[list[str], list[str], str]] | None,
    spaces: Mapping[str, Any] | None,
) -> dict[str, object]:
    from orchestrator.campaign.genome import SPACES
    from orchestrator.campaign.model import Genome
    space_map = SPACES if spaces is None else spaces
    if not space_map:
        raise CheckError("genome 空間が空")
    cc_path, cc_version = _compiler_identity(cc)
    cxx_path, cxx_version = _compiler_identity(cxx)
    cmake_path = shutil.which("cmake")
    if cmake_path is None:
        raise CheckError("cmake が存在しない")
    if not cache.is_dir() or not prefix.is_dir() or not scratch_root.is_dir():
        raise CheckError("header 用 cache/prefix/scratch root が directory でない")
    toolchain = {"cmake": {"realpath": os.path.realpath(cmake_path)},
                 "cc": {"realpath": cc_path}, "cxx": {"realpath": cxx_path}}
    provider = supply or _h_supply
    with tempfile.TemporaryDirectory(prefix="trace0-header-", dir=scratch_root) as temporary:
        root = Path(temporary)
        source = _h_sources(repo, old, new, root)
        if supply is None:
            payload = json.loads(_h_run([
                sys.executable, "-B", REPO_ROOT / "tools/pegasus/fetch_third_party.py",
                "hydrate", "--repo-root", REPO_ROOT, "--cache-root", cache,
                "--staging-root", root / "thirdparty-src",
            ], timeout=600))
            third = {name: Path(payload["source_root"]) / name for name in ("masstree", "mimalloc", "googletest")}
        else:
            third = {}
        changed = {side: {p: (source[side] / p).resolve() for p in headers} for side in ("old", "new")}
        counter = 0

        def provided(genome: Any, src: Path, build: Path, local_third: Mapping[str, Path]) -> tuple[list[str], list[str], str]:
            argv, targets, production = provider(genome, src, build, toolchain, prefix, local_third)
            if not isinstance(production, str) or not re.fullmatch(r"ycsb_[A-Za-z0-9_]+\.exe", production):
                raise CheckError(f"production target が未対応形: {production}")
            return argv, targets, production

        def configure(genome: Any, label: str, *, discovery: bool = False) -> dict[str, Any]:
            nonlocal counter
            pair: dict[str, Any] = {}
            for side in ("old", "new"):
                src = source[side]
                build = root / f"b{counter:04d}-{side}"
                counter += 1
                generated = root / f"g{counter:04d}-{side}"
                local_third = dict(third)
                if supply is None:
                    if discovery:
                        generated = stock[side]["generated"]
                    else:
                        shutil.copytree(third["masstree"], generated)
                    local_third["masstree"] = generated
                elif discovery:
                    local_third["generated"] = stock[side]["build"] / "generated"
                argv, targets, production = provided(genome, src, build, local_third)
                _h_run(argv, timeout=300)
                if not discovery:
                    for target in targets:
                        _h_run([toolchain["cmake"]["realpath"], "--build", build, "--target", target], timeout=600)
                    if supply is None and not (generated / "config.h").is_file():
                        raise CheckError(f"masstree config.h が無い: {label} {side}")
                database = json.loads((build / "compile_commands.json").read_text())
                if not isinstance(database, list) or not database:
                    raise CheckError(f"compile database が空: {label} {side}")
                roots = _h_roots(src, build, generated, local_third)
                entries = {}
                signatures = []
                for item in database:
                    key, command, signature = _h_entry(item, roots)
                    if key in entries:
                        raise CheckError(f"compile database 重複 entry: {key}")
                    entries[key] = {"raw": item, "argv": command}
                    signatures.append(signature)
                pair[side] = {"src": src, "build": build, "generated": generated,
                              "roots": roots, "entries": entries, "signatures": Counter(signatures),
                              "production": production}
            if pair["old"]["signatures"] != pair["new"]["signatures"]:
                raise CheckError(f"旧新 compile database が不一致: {label}")
            if pair["old"]["production"] != pair["new"]["production"]:
                raise CheckError(f"旧新 production target が不一致: {label}")
            return pair

        def dependencies(pair: dict[str, Any], label: str, target: str | None = None) -> tuple[dict[str, Any], set[tuple[str, str]]]:
            work = []
            for side in ("old", "new"):
                row = pair[side]
                for index, (key, entry) in enumerate(sorted(row["entries"].items())):
                    if target is not None and key[1] != target:
                        continue
                    for trace in (0, 1):
                        work.append((side, key, trace, entry, root / f"dep-{label}-{side}-{index}-{trace}.d"))
            def one(job: tuple[Any, ...]) -> tuple[str, tuple[str, str], int, set[Path]]:
                side, key, trace, entry, depfile = job
                return side, key, trace, _h_dep(entry["raw"], entry["argv"], trace, depfile)
            with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as pool:
                results = list(pool.map(one, work))
            deps: dict[str, Any] = {"old": {}, "new": {}}
            consumers = set()
            for side, key, trace, files in results:
                deps[side].setdefault(key, {})[trace] = files
                if any(path in files for path in changed[side].values()):
                    consumers.add(key)
            return deps, consumers

        first_protocol = next(iter(sorted(space_map)))
        stock = configure(Genome(first_protocol, {}), "stock")
        selected = {"stock": (stock, *dependencies(stock, "stock"))}
        skipped = {}
        targets = {}
        for protocol, space in sorted(space_map.items()):
            # The production target comes from the same provider as configure argv.
            sample = provided(Genome(protocol, {}), source["old"], root / f"target-{protocol}", third)
            target = sample[2]
            targets[protocol] = target
            stock_consumers = selected["stock"][2]
            choose = any(key[1] == target for key in stock_consumers)
            genomes = tuple(space.enumerate())
            if not genomes:
                raise CheckError(f"genome 空間が空: {protocol}")
            if not choose:
                for index, genome in enumerate(genomes):
                    label = f"discover-{protocol}-{index}"
                    pair = configure(genome, label, discovery=True)
                    _, consumers = dependencies(pair, label, target)
                    if any(key[1] == target for key in consumers):
                        choose = True
                        break
                if not choose:
                    skipped[protocol] = len(genomes)
            if choose:
                for index, genome in enumerate(genomes):
                    label = f"{protocol}-{index}"
                    pair = configure(genome, label)
                    selected[label] = (pair, *dependencies(pair, label))
        planned = []
        header_hits = {path: 0 for path in headers}
        for label, (pair, deps, consumers) in selected.items():
            for key in sorted(consumers):
                planned.append((label, key))
                for path in headers:
                    if any(changed[side][path] in deps[side][key][trace]
                           for side in ("old", "new") for trace in (0, 1)):
                        header_hits[path] += 1
        for path, count in header_hits.items():
            if not count:
                raise CheckError(f"変更 header の consumer が 0 件: {path}")
        planned_set = set(planned)
        aggregate = {}
        unique_jobs = []
        for label, key in planned:
            pair, deps, _ = selected[label]
            closure = []
            for side in ("old", "new"):
                row = pair[side]
                closure.append(tuple(sorted(
                    (_h_norm(os.fsencode(path), row["roots"]).decode(), _sha256(path.read_bytes()))
                    for path in deps[side][key][0]
                )))
            signature = next(sig for sig in pair["old"]["signatures"] if sig[:2] == key)
            aggregation_key = (key, signature, *closure)
            if aggregation_key in aggregate:
                aggregate[aggregation_key]["configures"].append(label)
            else:
                aggregate[aggregation_key] = {"configures": [label]}
                unique_jobs.append((aggregation_key, pair, key, label))
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as pool:
            evidence_rows = list(pool.map(
                lambda job: _h_compare(job[1], job[2], job[3]), unique_jobs))
        comparisons = []
        done = set()
        for job, evidence in zip(unique_jobs, evidence_rows):
            evidence["configures"] = aggregate[job[0]]["configures"]
            comparisons.append(evidence)
            done.update((label, (evidence["file"], evidence["target"])) for label in evidence["configures"])
        if done != planned_set:
            raise CheckError("比較の予定集合と実行済み集合が不一致")
        return {
            "guarantee": HEADER_GUARANTEE, "scope": HEADER_SCOPE,
            "compilers": {"cc": {"path": cc_path, "version": cc_version},
                          "cxx": {"path": cxx_path, "version": cxx_version}},
            "selected_configures": sorted(selected), "unselected_genomes_checked": skipped,
            "production_targets": targets, "consumers": [
                {"configure": label, "file": key[0], "target": key[1]} for label, key in planned],
            "planned_count": len(planned), "executed_count": len(done),
            "unique_comparison_count": len(comparisons), "comparisons": comparisons,
            "production_argv_difference": ["-DCCBENCH_CCACHE=OFF"],
        }


def check(
    repo: Path,
    old: str,
    new: str,
    cxx: str,
    expect_paths: Sequence[str] | None = None,
    *,
    header_cc: str | None = None,
    third_party_cache: Path | None = None,
    dependency_prefix: Path | None = None,
    scratch_root: Path | None = None,
    configure_supply: Callable[..., tuple[list[str], list[str], str]] | None = None,
    genome_spaces: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性の evidence を返す。"""
    repo = Path(os.path.realpath(repo))
    if not repo.is_dir():
        raise CheckError(f"--repo が directory でない: {repo}")
    old_oid = _resolve_commit(repo, old)
    new_oid = _resolve_commit(repo, new)
    header_inputs = (header_cc, third_party_cache, dependency_prefix, scratch_root)
    legacy_order = all(value is None for value in header_inputs)
    if legacy_order:
        old_known_absent = _assert_proven_repo_absent_macros(os.fspath(repo), commit=old_oid)
        new_known_absent = _assert_proven_repo_absent_macros(os.fspath(repo), commit=new_oid)
    ancestor = _is_ancestor(repo, old_oid, new_oid)
    if not ancestor:
        raise CheckError(f"old commit は new commit の祖先でない: {old_oid} !<= {new_oid}")
    diff = _raw_diff(repo, old_oid, new_oid)
    header_paths = [entry["path"] for entry in diff if isinstance(entry["path"], str)
                    and PurePosixPath(entry["path"]).suffix.lower() in _HEADER_SUFFIXES]
    _validate_diff(diff, header_enabled=bool(header_paths) and all(value is not None for value in header_inputs))
    if header_paths and any(value is None for value in header_inputs):
        raise CheckError("header 用の 4 引数はすべて必要")
    validated_expect_paths = _validate_expected_paths(diff, expect_paths)
    compiler, compiler_version = _compiler_identity(cxx)
    if not legacy_order:
        old_known_absent = _assert_proven_repo_absent_macros(os.fspath(repo), commit=old_oid) if len(header_paths) != len(diff) else frozenset()
        new_known_absent = _assert_proven_repo_absent_macros(os.fspath(repo), commit=new_oid) if len(header_paths) != len(diff) else frozenset()

    genomes = tuple(SILO_SPACE.enumerate())
    overlays = tuple(_context_overlays())
    expected_context_count = len(genomes) * len(overlays)
    if expected_context_count == 0:
        raise CheckError(
            "context 列挙が空で比較 0 件になるため fail-closed で拒否する: "
            f"genomes={len(genomes)} overlays={len(overlays)}"
        )

    files: list[dict[str, object]] = []
    for entry in diff:
        path = entry["path"]
        if not isinstance(path, str):
            raise CheckError("検証済み diff path が文字列でない未対応形")
        if path in header_paths:
            continue
        files.append(
            _compare_file(
                repo,
                old_oid,
                new_oid,
                path,
                compiler,
                old_known_absent,
                new_known_absent,
                genomes,
                overlays,
                expected_context_count,
            )
        )
    if not files and not header_paths:
        raise CheckError("比較対象が 0 件")
    report = {
        "schema": SCHEMA,
        "guarantee": GUARANTEE,
        "result": "pass",
        "repo": os.fspath(repo),
        "old_oid": old_oid,
        "new_oid": new_oid,
        "old_is_ancestor_of_new": ancestor,
        "expected_paths": validated_expect_paths,
        "diff": diff,
        "compiler": {"path": compiler, "version": compiler_version},
        "context_matrix": {
            "genome_count": len(genomes),
            "overlay_count": len(overlays),
            "expected_context_count_per_file": expected_context_count,
        },
        "files": files,
    }
    if header_paths:
        assert header_cc is not None and third_party_cache is not None
        assert dependency_prefix is not None and scratch_root is not None
        report["header_rule"] = _h_check(
            repo, old_oid, new_oid, header_paths, header_cc, cxx,
            Path(third_party_cache), Path(dependency_prefix), Path(scratch_root),
            configure_supply, genome_spaces,
        )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description=f"{GUARANTEE}を fail-closed に検査する。")
    parser.add_argument("--repo", required=True, type=Path, help="submodule の git worktree path")
    parser.add_argument("--old", required=True, type=_full_oid, help="旧 commit の 40 桁 lowercase hex OID")
    parser.add_argument("--new", required=True, type=_full_oid, help="新 commit の 40 桁 lowercase hex OID")
    parser.add_argument("--cxx", required=True, help="preprocess に使う compiler（既定値なし）")
    parser.add_argument("--header-cc")
    parser.add_argument("--third-party-cache", type=Path)
    parser.add_argument("--dependency-prefix", type=Path)
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument(
        "--expect-paths",
        nargs="+",
        metavar="PATH",
        help=(
            "任意の期待 diff path 集合。指定時は順不同で厳密一致が必須で、重複・過不足を "
            "fail-closed で拒否する"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = check(
            args.repo, args.old, args.new, args.cxx, args.expect_paths,
            header_cc=args.header_cc, third_party_cache=args.third_party_cache,
            dependency_prefix=args.dependency_prefix, scratch_root=args.scratch_root,
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary is deliberately fail-closed
        print(f"error: {GUARANTEE}を確認できない: {exc}", file=sys.stderr)
        return 1
    json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
