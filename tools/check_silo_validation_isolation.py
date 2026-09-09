#!/usr/bin/env python3
"""Check a patch against Silo's raw-config validation call closure.

This intentionally does not preprocess C++.  Every conditional-compilation
branch remains present while function regions and calls are inspected.  The
result is only a syntactic, downward-call-closure intersection result; the
machine-readable claim boundary below states the deliberately narrower claim.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional


SCHEMA = "izanagi.silo-validation-isolation/v1"
NO_INTERSECTION = "NO_STATIC_VALIDATION_CLOSURE_INTERSECTION"
INTERSECTION = "STATIC_VALIDATION_CLOSURE_INTERSECTION"
ERROR = "ERROR"
VALIDATION_ROOT = "TxExecutor::validationPhase/0"
OWNER_TUS = ["cc/silo/transaction.cc"]
CLAIM_BOUNDARY = {
    "analysis_kind": "raw-config-union-static-downward-call-closure",
    "closure_direction": "downward-callees-only",
    "thread_interleavings_proven": False,
    "validation_decision_sequence_proven": False,
    "abort_retry_lifecycle_proven": False,
    "commit_validation_result_consumption_covered": False,
    "write_phase_write_writeback_correctness_covered": False,
    "pure_timing_or_side_effect_freedom_proven": False,
    "other_protocols_covered": False,
    "other_groups_or_unexecuted_schedules_licensed": False,
    "runtime_anomaly_policy": (
        "REJECT_VARIANT_IMMEDIATELY_REGARDLESS_OF_THIS_RESULT"
    ),
    "runtime_anomaly_policy_enforced_by_this_checker": False,
    "external_runtime_anomaly_evidence_required": True,
    "implicit_constructor_destructor_edges_modeled": False,
    "error_policy": "ERROR_IS_NOT_NO_STATIC_VALIDATION_CLOSURE_INTERSECTION",
    "does_not_prove": [
        "thread_interleaving",
        "validation_decision_sequence",
        "abort_retry_lifecycle",
        "commit_validation_result_consumption",
        "write_phase_write_or_writeback_correctness",
        "pure_timing_or_side_effect_freedom",
        "serializability_or_dynamic_anomaly_absence",
        "implicit_constructor_or_destructor_call_edges",
        "other_protocol_correctness",
        "other_group_or_unexecuted_schedule_certification",
    ],
}

_CXX_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
_ROOT_TU = PurePosixPath("cc/silo/transaction.cc")
_OPTIONS = PurePosixPath("cmake/Options.cmake")
_ALLOWED_HEADER_ROOTS = (
    PurePosixPath("cc/silo/include"),
    PurePosixPath("include"),
)
_CONTROL_WORDS = {
    "alignas", "asm", "catch", "decltype", "defined", "for", "if",
    "noexcept", "requires", "sizeof", "static_assert", "switch", "while",
}


class AnalysisError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[tuple[str, str]]


@dataclass
class PatchFile:
    path: PurePosixPath
    hunks: list[Hunk] = field(default_factory=list)


@dataclass
class EditSpan:
    edit_id: str
    path: PurePosixPath
    hunk_index: int
    operation: str
    text: list[str]
    old_lines: list[int] = field(default_factory=list)
    new_lines: list[int] = field(default_factory=list)
    deletion_anchor: Optional[int] = None

    def evidence(self) -> dict:
        item = {
            "edit_id": self.edit_id,
            "path": self.path.as_posix(),
            "hunk": self.hunk_index,
            "operation": self.operation,
        }
        if self.old_lines:
            item["old_lines"] = [min(self.old_lines), max(self.old_lines)]
        if self.new_lines:
            item["new_lines"] = [min(self.new_lines), max(self.new_lines)]
        if self.deletion_anchor is not None:
            item["post_image_anchor"] = {
                "after_line": self.deletion_anchor,
                "before_line": self.deletion_anchor + 1,
            }
        return item


@dataclass
class FunctionRegion:
    symbol: str
    name: str
    owner: str
    arity: int
    min_arity: int
    variadic: bool
    path: PurePosixPath
    start_line: int
    signature_line: int
    end_line: int
    body_start: int
    body_end: int
    source: str
    syntax: str

    def accepts_arity(self, arity: int) -> bool:
        return self.min_arity <= arity and (self.variadic or arity <= self.arity)

    def closure_evidence(self, depth: int, edge: Optional["CallEdge"]) -> dict:
        return {
            "symbol": self.symbol,
            "path": self.path.as_posix(),
            "start_line": self.start_line,
            "signature_line": self.signature_line,
            "end_line": self.end_line,
            "depth": depth,
            "caller": None if edge is None else edge.caller,
            "callsite": None if edge is None else {
                "path": edge.path.as_posix(),
                "line": edge.line,
            },
            "edge_kind": "root" if edge is None else edge.kind,
        }


@dataclass(frozen=True)
class Call:
    name: str
    qualifier: str
    expression_receiver: bool
    arity: int
    line: int
    args: str


@dataclass(frozen=True)
class CallEdge:
    caller: str
    callee: str
    path: PurePosixPath
    line: int
    kind: str


def _base_result(patch: Path | str) -> dict:
    return {
        "schema": SCHEMA,
        "verdict": ERROR,
        "patch": str(patch),
        "validation_root": VALIDATION_ROOT,
        "owner_tus": list(OWNER_TUS),
        "claim_boundary": dict(CLAIM_BOUNDARY),
        "closure": [],
        "cmake_macros": [],
        "conditional_macros": [],
        "closure_expansion_errors": [],
        "intersections": [],
        "classified_edits": [],
        "unconsumed_edits": [],
    }


def _read_utf8(path: Path, code: str) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError as exc:
        raise AnalysisError(code, f"file does not exist: {path}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise AnalysisError(code, f"cannot read UTF-8 file {path}: {exc}") from exc


def _safe_patch_path(raw: str) -> PurePosixPath:
    if not raw or raw.startswith("/") or "\\" in raw:
        raise AnalysisError("UNSAFE_PATCH_PATH", f"unsafe patch path: {raw!r}")
    path = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise AnalysisError("UNSAFE_PATCH_PATH", f"unsafe patch path: {raw!r}")
    return path


_HUNK_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$"
)


def _parse_patch(text: str) -> list[PatchFile]:
    lines = text.splitlines()
    if not lines:
        raise AnalysisError("EMPTY_PATCH", "patch is empty")
    files: list[PatchFile] = []
    seen: set[PurePosixPath] = set()
    i = 0
    while i < len(lines):
        if not lines[i].startswith("diff --git "):
            raise AnalysisError(
                "INVALID_DIFF", f"expected diff --git header at patch line {i + 1}"
            )
        match = re.fullmatch(r"diff --git a/(\S+) b/(\S+)", lines[i])
        if not match or match.group(1) != match.group(2):
            raise AnalysisError("UNSUPPORTED_DIFF", "only same-path git diffs are supported")
        path = _safe_patch_path(match.group(1))
        if path in seen:
            raise AnalysisError("DUPLICATE_FILE_SECTION", f"duplicate file section: {path}")
        seen.add(path)
        item = PatchFile(path)
        files.append(item)
        i += 1

        saw_old = False
        saw_new = False
        while i < len(lines) and not lines[i].startswith("diff --git "):
            line = lines[i]
            if line.startswith((
                "Binary files ", "GIT binary patch", "new file mode ",
                "deleted file mode ", "rename from ", "rename to ",
                "copy from ", "copy to ", "old mode ", "new mode ",
                "similarity index ", "dissimilarity index ",
            )):
                raise AnalysisError("UNSUPPORTED_DIFF", f"unsupported diff metadata: {line}")
            if line.startswith("index "):
                i += 1
                continue
            if line == f"--- a/{path.as_posix()}":
                saw_old = True
                i += 1
                continue
            if line == f"+++ b/{path.as_posix()}":
                if not saw_old:
                    raise AnalysisError("INVALID_DIFF", "new header precedes old header")
                saw_new = True
                i += 1
                continue
            hmatch = _HUNK_RE.fullmatch(line)
            if hmatch:
                if not (saw_old and saw_new):
                    raise AnalysisError("INVALID_DIFF", "hunk precedes file headers")
                old_count = int(hmatch.group(2) or "1")
                new_count = int(hmatch.group(4) or "1")
                hunk_lines: list[tuple[str, str]] = []
                i += 1
                while i < len(lines):
                    body = lines[i]
                    if body.startswith("diff --git ") or _HUNK_RE.fullmatch(body):
                        break
                    if body.startswith("\\ No newline at end of file"):
                        raise AnalysisError(
                            "UNSUPPORTED_DIFF",
                            "no-newline markers are unsupported because line-ending edits "
                            "cannot be classified as source regions",
                        )
                    if not body or body[0] not in " +-":
                        raise AnalysisError(
                            "INVALID_HUNK", f"invalid hunk body at patch line {i + 1}"
                        )
                    hunk_lines.append((body[0], body[1:]))
                    i += 1
                actual_old = sum(kind != "+" for kind, _ in hunk_lines)
                actual_new = sum(kind != "-" for kind, _ in hunk_lines)
                if not any(kind in "+-" for kind, _ in hunk_lines):
                    raise AnalysisError("EMPTY_HUNK", f"hunk has no edits for {path}")
                if actual_old != old_count or actual_new != new_count:
                    raise AnalysisError(
                        "INVALID_HUNK_COUNT",
                        f"hunk count mismatch for {path}: "
                        f"header -{old_count}/+{new_count}, body -{actual_old}/+{actual_new}",
                    )
                item.hunks.append(Hunk(
                    int(hmatch.group(1)), old_count,
                    int(hmatch.group(3)), new_count, hunk_lines,
                ))
                continue
            if not line:
                i += 1
                continue
            raise AnalysisError("INVALID_DIFF", f"unexpected diff metadata: {line}")
        if not item.hunks:
            raise AnalysisError("EMPTY_FILE_DIFF", f"no hunks for {path}")
    return files


def _find_unique_block(lines: list[str], block: list[str], path: PurePosixPath) -> int:
    if not block:
        raise AnalysisError(
            "UNMAPPABLE_HUNK", f"context-free insertion cannot be uniquely mapped: {path}"
        )
    width = len(block)
    matches = [i for i in range(len(lines) - width + 1) if lines[i:i + width] == block]
    if len(matches) != 1:
        raise AnalysisError(
            "UNMAPPABLE_HUNK",
            f"hunk old image has {len(matches)} exact matches in {path}; expected exactly one",
        )
    return matches[0]


def _finish_span(
    spans: list[EditSpan], path: PurePosixPath, hunk_index: int,
    operation: str, text: list[str], old_lines: list[int],
    new_lines: list[int], anchor: Optional[int],
) -> None:
    if not text:
        return
    spans.append(EditSpan(
        edit_id=f"E{len(spans) + 1:04d}", path=path, hunk_index=hunk_index,
        operation=operation, text=list(text), old_lines=list(old_lines),
        new_lines=list(new_lines), deletion_anchor=anchor,
    ))


def _apply_patch(
    ccbench: Path, patch_files: list[PatchFile]
) -> tuple[dict[PurePosixPath, str], dict[PurePosixPath, str], list[EditSpan]]:
    pre_images: dict[PurePosixPath, str] = {}
    post_images: dict[PurePosixPath, str] = {}
    spans: list[EditSpan] = []
    ccbench_real = ccbench.resolve()
    for patch_file in patch_files:
        disk_path = ccbench / patch_file.path.as_posix()
        try:
            resolved = disk_path.resolve(strict=True)
        except (OSError, FileNotFoundError) as exc:
            raise AnalysisError(
                "PATCH_TARGET_MISSING", f"patch target does not exist: {patch_file.path}"
            ) from exc
        if ccbench_real not in resolved.parents or not resolved.is_file():
            raise AnalysisError("UNSAFE_PATCH_PATH", f"patch target escapes ccbench: {patch_file.path}")
        original = _read_utf8(resolved, "PATCH_TARGET_UNREADABLE")
        pre_images[patch_file.path] = original
        current = original.splitlines()
        previous_end = -1
        for hunk_index, hunk in enumerate(patch_file.hunks, start=1):
            old_block = [line for kind, line in hunk.lines if kind != "+"]
            match_at = _find_unique_block(current, old_block, patch_file.path)
            if match_at < previous_end:
                raise AnalysisError("OVERLAPPING_HUNKS", f"out-of-order hunk in {patch_file.path}")

            replacement = [line for kind, line in hunk.lines if kind != "-"]
            old_cursor = match_at
            new_cursor = match_at
            active_kind: Optional[str] = None
            active_text: list[str] = []
            active_old: list[int] = []
            active_new: list[int] = []
            active_anchor: Optional[int] = None

            def flush() -> None:
                nonlocal active_kind, active_text, active_old, active_new, active_anchor
                if active_kind is not None:
                    _finish_span(
                        spans, patch_file.path, hunk_index, active_kind,
                        active_text, active_old, active_new, active_anchor,
                    )
                active_kind = None
                active_text = []
                active_old = []
                active_new = []
                active_anchor = None

            for kind, line in hunk.lines:
                operation = "deletion" if kind == "-" else "addition" if kind == "+" else None
                if operation != active_kind:
                    flush()
                    active_kind = operation
                if kind == " ":
                    old_cursor += 1
                    new_cursor += 1
                elif kind == "-":
                    active_text.append(line)
                    active_old.append(old_cursor + 1)
                    if active_anchor is None:
                        active_anchor = new_cursor
                    old_cursor += 1
                else:
                    active_text.append(line)
                    active_new.append(new_cursor + 1)
                    new_cursor += 1
            flush()
            current[match_at:match_at + len(old_block)] = replacement
            previous_end = match_at + len(replacement)
        trailing_newline = original.endswith("\n")
        post_images[patch_file.path] = "\n".join(current) + ("\n" if trailing_newline else "")
    return pre_images, post_images, spans


def _strip_comments_and_literals(text: str) -> str:
    """Replace comments and literals with spaces while preserving offsets/newlines."""
    out = list(text)
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i + 2)
            if j < 0:
                j = n
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise AnalysisError("UNBALANCED_CPP", "unterminated block comment")
            for k in range(i, j + 2):
                if out[k] != "\n":
                    out[k] = " "
            i = j + 2
            continue
        raw_at = i if text.startswith('R"', i) else -1
        if raw_at >= 0:
            delim_end = text.find("(", raw_at + 2, min(n, raw_at + 20))
            if delim_end < 0:
                raise AnalysisError("UNBALANCED_CPP", "invalid raw string literal")
            delimiter = text[raw_at + 2:delim_end]
            marker = ")" + delimiter + '"'
            j = text.find(marker, delim_end + 1)
            if j < 0:
                raise AnalysisError("UNBALANCED_CPP", "unterminated raw string literal")
            end = j + len(marker)
            for k in range(raw_at, end):
                if out[k] != "\n":
                    out[k] = " "
            i = end
            continue
        if text[i] in {'"', "'"}:
            quote = text[i]
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == quote:
                    j += 1
                    break
                j += 1
            else:
                raise AnalysisError("UNBALANCED_CPP", "unterminated quoted literal")
            for k in range(i, min(j, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def _blank_directives(text: str) -> str:
    lines = text.splitlines(keepends=True)
    continuation = False
    out: list[str] = []
    for line in lines:
        is_directive = continuation or line.lstrip().startswith("#")
        if is_directive:
            out.append("".join("\n" if char == "\n" else " " for char in line))
            continuation = line.rstrip("\n").rstrip().endswith("\\")
        else:
            out.append(line)
            continuation = False
    return "".join(out)


def _brace_pairs(text: str) -> dict[int, int]:
    stack: list[int] = []
    pairs: dict[int, int] = {}
    parens = 0
    brackets = 0
    for i, char in enumerate(text):
        if char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
            if parens < 0:
                raise AnalysisError("UNBALANCED_CPP", "unbalanced parenthesis in raw source")
        elif char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
            if brackets < 0:
                raise AnalysisError("UNBALANCED_CPP", "unbalanced bracket in raw source")
        elif char == "{":
            stack.append(i)
        elif char == "}":
            if not stack:
                raise AnalysisError("UNBALANCED_CPP", "unbalanced brace in raw source")
            pairs[stack.pop()] = i
    if stack or parens or brackets:
        raise AnalysisError("UNBALANCED_CPP", "unbalanced raw source delimiters")
    return pairs


def _matching_open_paren(text: str, close: int) -> Optional[int]:
    depth = 0
    for i in range(close, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                return i
    return None


def _arity(arguments: str) -> int:
    if not arguments.strip() or arguments.strip() == "void":
        return 0
    paren = bracket = brace = angle = 0
    commas = 0
    for char in arguments:
        if char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "{":
            brace += 1
        elif char == "}":
            brace = max(0, brace - 1)
        elif char == "<":
            angle += 1
        elif char == ">" and angle:
            angle -= 1
        elif char == "," and not (paren or bracket or brace or angle):
            commas += 1
    return commas + 1


def _parameter_arity(arguments: str) -> tuple[int, int, bool]:
    """Return minimum, written maximum, and variadic status for parameters."""
    if not arguments.strip() or arguments.strip() == "void":
        return 0, 0, False
    parts: list[str] = []
    start = 0
    paren = bracket = brace = angle = 0
    for index, char in enumerate(arguments):
        if char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "{":
            brace += 1
        elif char == "}":
            brace = max(0, brace - 1)
        elif char == "<":
            angle += 1
        elif char == ">" and angle:
            angle -= 1
        elif char == "," and not (paren or bracket or brace or angle):
            parts.append(arguments[start:index])
            start = index + 1
    parts.append(arguments[start:])

    minimum = 0
    variadic = False
    for parameter in parts:
        if "..." in parameter:
            variadic = True
            continue
        paren = bracket = brace = angle = 0
        has_default = False
        for index, char in enumerate(parameter):
            if char == "(":
                paren += 1
            elif char == ")":
                paren = max(0, paren - 1)
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket = max(0, bracket - 1)
            elif char == "{":
                brace += 1
            elif char == "}":
                brace = max(0, brace - 1)
            elif char == "<":
                angle += 1
            elif char == ">" and angle:
                angle -= 1
            elif char == "=" and not (paren or bracket or brace or angle):
                before = parameter[index - 1] if index else ""
                after = parameter[index + 1] if index + 1 < len(parameter) else ""
                if before not in "!<=>" and after != "=":
                    has_default = True
                    break
        if not has_default:
            minimum += 1
    return minimum, len(parts), variadic


_FUNCTION_NAME_RE = re.compile(
    r"((?:(?:[A-Za-z_]\w*)(?:\s*<[^(){};\n]*>)?\s*::\s*)*"
    r"(?:~?[A-Za-z_]\w*|operator\s*(?:\(\)|\[\]|<=|>=|==|!=|<|>|"
    r"[+\-*/%=!&|^~]+)))\s*$"
)


def _canonical_owner(text: str) -> str:
    parts = []
    for part in text.split("::"):
        part = re.sub(r"\s*<.*>\s*$", "", part.strip())
        if part:
            parts.append(part)
    return "::".join(parts)


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _expanded_start_line(source: str, signature_line: int) -> int:
    lines = source.splitlines()
    line = signature_line
    in_block_comment = False
    while line > 1:
        prior = lines[line - 2].strip()
        if in_block_comment:
            line -= 1
            if "/*" in prior:
                in_block_comment = False
            continue
        if not prior or prior.startswith(("//", "#", "[[", "__attribute__", "template")):
            line -= 1
            continue
        if prior.endswith("*/") or prior.startswith("*"):
            in_block_comment = "/*" not in prior
            line -= 1
            continue
        break
    return line


def _scope_ranges(syntax: str, pairs: dict[int, int]) -> tuple[list[tuple[int, int, str]], list[tuple[int, int, str]]]:
    classes: list[tuple[int, int, str]] = []
    namespaces: list[tuple[int, int, str]] = []
    class_re = re.compile(r"\b(?:class|struct)\s+([A-Za-z_]\w*)[^;{}]*\{")
    ns_re = re.compile(r"\bnamespace\s+([A-Za-z_]\w*)\s*\{")
    for match in class_re.finditer(syntax):
        brace = syntax.rfind("{", match.start(), match.end())
        if brace in pairs:
            classes.append((brace, pairs[brace], match.group(1)))
    for match in ns_re.finditer(syntax):
        brace = syntax.rfind("{", match.start(), match.end())
        if brace in pairs:
            namespaces.append((brace, pairs[brace], match.group(1)))
    return classes, namespaces


def _innermost_scope(ranges: Iterable[tuple[int, int, str]], offset: int) -> str:
    containing = [item for item in ranges if item[0] < offset < item[1]]
    if not containing:
        return ""
    return min(containing, key=lambda item: item[1] - item[0])[2]


def _extract_functions(path: PurePosixPath, source: str) -> list[FunctionRegion]:
    lexical = _strip_comments_and_literals(source)
    syntax = _blank_directives(lexical)
    pairs = _brace_pairs(syntax)
    classes, namespaces = _scope_ranges(syntax, pairs)
    regions: list[FunctionRegion] = []
    accepted_ranges: list[tuple[int, int]] = []
    for brace in sorted(pairs):
        close_brace = pairs[brace]
        if any(start < brace < end for start, end in accepted_ranges):
            continue
        close_paren = brace - 1
        while close_paren >= 0 and syntax[close_paren].isspace():
            close_paren -= 1
        if close_paren < 0:
            continue
        if syntax[close_paren] != ")":
            candidates = [m.end() - 1 for m in re.finditer(r"\)", syntax[max(0, brace - 300):brace])]
            if not candidates:
                continue
            close_paren = max(0, brace - 300) + candidates[-1]
            suffix = syntax[close_paren + 1:brace].strip()
            if suffix and not re.fullmatch(
                r"(?:(?:const|noexcept|override|final)\b\s*|->\s*[A-Za-z_:<>*&\s]+|\[\[[^\]]+\]\]\s*)+",
                suffix,
            ):
                continue
        open_paren = _matching_open_paren(syntax, close_paren)
        if open_paren is None:
            continue
        prefix = syntax[max(0, open_paren - 240):open_paren]
        name_match = _FUNCTION_NAME_RE.search(prefix)
        if not name_match:
            continue
        raw_name = re.sub(r"\s+", "", name_match.group(1))
        simple_name = raw_name.split("::")[-1]
        if simple_name in _CONTROL_WORDS:
            continue
        name_pos = open_paren - (len(prefix) - name_match.start(1))
        explicit_owner = _canonical_owner("::".join(raw_name.split("::")[:-1]))
        class_owner = _innermost_scope(classes, brace)
        namespace_owner = _innermost_scope(namespaces, brace)
        owner = explicit_owner or class_owner or namespace_owner
        function_name = simple_name
        arguments = syntax[open_paren + 1:close_paren]
        min_arity, arity, variadic = _parameter_arity(arguments)
        symbol = f"{owner + '::' if owner else ''}{function_name}/{arity}"
        signature_line = _line_of(source, name_pos)
        start_line = _expanded_start_line(source, signature_line)
        end_line = _line_of(source, close_brace)
        regions.append(FunctionRegion(
            symbol=symbol, name=function_name, owner=owner,
            arity=arity, min_arity=min_arity, variadic=variadic, path=path,
            start_line=start_line, signature_line=signature_line, end_line=end_line,
            body_start=brace + 1, body_end=close_brace, source=source, syntax=syntax,
        ))
        accepted_ranges.append((brace, close_brace))
    return regions


def _is_allowed_header(path: PurePosixPath) -> bool:
    return any(path == root or root in path.parents for root in _ALLOWED_HEADER_ROOTS)


def _collect_sources(
    ccbench: Path, post_images: dict[PurePosixPath, str]
) -> dict[PurePosixPath, str]:
    pending = deque([_ROOT_TU])
    sources: dict[PurePosixPath, str] = {}
    include_re = re.compile(r"(?m)^\s*#\s*include\s*([<\"])([^>\"]+)[>\"]")
    computed_re = re.compile(r"(?m)^\s*#\s*include\s+(?![<\"])")
    while pending:
        path = pending.popleft()
        if path in sources:
            continue
        disk = ccbench / path.as_posix()
        source = post_images.get(path)
        if source is None:
            source = _read_utf8(disk, "SOURCE_UNREADABLE")
        sources[path] = source
        # Include spelling must remain visible here; preprocessing is never run.
        # Anchoring at the beginning of a physical line excludes ordinary comment
        # prose, and edited include directives are rejected separately.
        if computed_re.search(source):
            raise AnalysisError("COMPUTED_INCLUDE", f"computed include in {path}")
        for match in include_re.finditer(source):
            if match.group(1) == "<":
                continue
            target_text = match.group(2)
            if target_text.startswith(("gflags/", "glog/")):
                continue
            target = PurePosixPath(*((path.parent / target_text).parts))
            normalized_parts: list[str] = []
            for part in target.parts:
                if part == ".":
                    continue
                if part == "..":
                    if not normalized_parts:
                        raise AnalysisError("UNSAFE_INCLUDE", f"include escapes ccbench in {path}")
                    normalized_parts.pop()
                else:
                    normalized_parts.append(part)
            normalized = PurePosixPath(*normalized_parts)
            if not _is_allowed_header(normalized):
                continue
            target_disk = ccbench / normalized.as_posix()
            if normalized not in post_images and not target_disk.is_file():
                raise AnalysisError("INCLUDE_MISSING", f"first-party include missing: {normalized}")
            if normalized.suffix.lower() in _CXX_SUFFIXES:
                pending.append(normalized)
    return sources


def _parse_calls(region: FunctionRegion) -> list[Call]:
    body = region.syntax[region.body_start:region.body_end]
    base = region.body_start
    if re.search(r"\(\s*\*\s*[A-Za-z_]\w*\s*\)\s*\(", body):
        raise AnalysisError(
            "UNSUPPORTED_FUNCTION_POINTER",
            f"function-pointer call in closure region {region.symbol}",
        )
    if re.search(r"\[[^\]\n]*\]\s*\([^;{}]*\)\s*(?:mutable\s*)?\{", body):
        raise AnalysisError(
            "UNSUPPORTED_LAMBDA_CALL",
            f"lambda body in closure region {region.symbol}",
        )
    call_re = re.compile(
        r"(?P<full>(?:(?:[A-Za-z_]\w*)\s*(?:::|->|\.)\s*)*(?P<name>[A-Za-z_]\w*))\s*\("
    )
    calls: list[Call] = []
    for match in call_re.finditer(body):
        name = match.group("name")
        if name in _CONTROL_WORDS:
            continue
        open_paren = base + match.end() - 1
        depth = 0
        close_paren: Optional[int] = None
        for i in range(open_paren, region.body_end):
            if region.syntax[i] == "(":
                depth += 1
            elif region.syntax[i] == ")":
                depth -= 1
                if depth == 0:
                    close_paren = i
                    break
        if close_paren is None:
            raise AnalysisError("UNBALANCED_CALL", f"unbalanced call in {region.symbol}")
        full = re.sub(r"\s+", "", match.group("full"))
        qualifier = full[:-len(name)]
        prefix = body[:match.start()].rstrip()
        calls.append(Call(
            name=name, qualifier=qualifier,
            expression_receiver=not qualifier and prefix.endswith((".", "->")),
            arity=_arity(region.syntax[open_paren + 1:close_paren]),
            line=_line_of(region.source, base + match.start()),
            args=region.syntax[open_paren + 1:close_paren],
        ))
    return calls


def _unique_region(
    index: dict[str, list[FunctionRegion]], symbol: str, reason: str
) -> FunctionRegion:
    regions = index.get(symbol, [])
    if len(regions) != 1:
        raise AnalysisError(
            "AMBIGUOUS_CALLEE", f"{reason}: {symbol} has {len(regions)} definitions"
        )
    return regions[0]


def _resolve_direct_call(
    call: Call, caller: FunctionRegion,
    exact: dict[str, list[FunctionRegion]],
    by_name: dict[str, list[FunctionRegion]],
    edited_regions: set[str],
) -> Optional[FunctionRegion]:
    def select(candidates: list[FunctionRegion], reason: str) -> Optional[FunctionRegion]:
        matching = [region for region in candidates if region.accepts_arity(call.arity)]
        if len(matching) == 1:
            return matching[0]
        if len(matching) > 1:
            symbols = ", ".join(sorted(region.symbol for region in matching))
            raise AnalysisError(
                "AMBIGUOUS_CALLEE",
                f"{reason}: {call.name}/{call.arity} matches {symbols}",
            )
        if candidates:
            arities = ", ".join(sorted(region.symbol for region in candidates))
            raise AnalysisError(
                "FIRST_PARTY_ARITY_MISMATCH",
                f"{reason}: {call.name}/{call.arity} does not match {arities}",
            )
        return None

    qualifier = call.qualifier
    if qualifier.endswith("::"):
        owner = _canonical_owner(qualifier[:-2])
        if owner == "std":
            return None
        symbol = f"{owner}::{call.name}/{call.arity}"
        candidates = exact.get(symbol, [])
        if candidates:
            return _unique_region(exact, symbol, "explicitly qualified call")
        return select(
            [region for region in by_name.get(call.name, []) if region.owner == owner],
            "explicitly qualified first-party call",
        )
    if qualifier and qualifier != "this->":
        # Resolving object.member by name alone would invent edges between
        # unrelated classes (for example vector::begin -> TxExecutor::begin).
        # This limited checker only resolves such a call when its receiver is
        # the current object; other typed member calls remain external leaves.
        return None
    if not qualifier or qualifier == "this->":
        if caller.owner:
            local_symbol = f"{caller.owner}::{call.name}/{call.arity}"
            if local_symbol in exact:
                return _unique_region(exact, local_symbol, "same-owner call")
            local = [
                region for region in by_name.get(call.name, [])
                if region.owner == caller.owner
            ]
            if local:
                return select(local, "same-owner first-party call")
    if call.expression_receiver:
        candidates = by_name.get(call.name, [])
        matching = [
            region for region in candidates
            if region.accepts_arity(call.arity)
        ]
        if len(matching) == 1:
            return matching[0]
        if len(matching) > 1:
            return select(matching, f"expression member call in {caller.symbol}")
        if any(region.symbol in edited_regions for region in candidates):
            return select(candidates, f"edited expression member call in {caller.symbol}")
        return None
    return select(
        by_name.get(call.name, []),
        f"unqualified first-party call in {caller.symbol}",
    )


def _build_closure(
    regions: list[FunctionRegion], sources: dict[PurePosixPath, str],
    spans: list[EditSpan], edited_regions: set[str],
) -> tuple[
    list[FunctionRegion], dict[str, int], dict[str, Optional[CallEdge]], list[dict]
]:
    exact: dict[str, list[FunctionRegion]] = defaultdict(list)
    by_name: dict[str, list[FunctionRegion]] = defaultdict(list)
    for region in regions:
        exact[region.symbol].append(region)
        by_name[region.name].append(region)
    root = _unique_region(exact, VALIDATION_ROOT, "validation root")

    expansion_errors: list[dict] = []

    def record_expansion_error(
        exc: AnalysisError, caller: FunctionRegion, call: Optional[Call] = None,
    ) -> None:
        evidence = {
            "code": exc.code,
            "message": exc.message,
            "caller": caller.symbol,
            "path": caller.path.as_posix(),
        }
        if call is not None:
            evidence.update({
                "call": f"{call.name}/{call.arity}",
                "line": call.line,
            })
        expansion_errors.append(evidence)

    tx_header = sources.get(PurePosixPath("cc/silo/include/transaction.hh"), "")
    try:
        if not re.search(
            r"std\s*::\s*vector\s*<\s*WriteElement\s*<\s*Tuple\s*>\s*>\s*write_set_",
            _strip_comments_and_literals(tx_header),
        ):
            raise AnalysisError(
                "TYPE_PROOF_FAILED", "cannot derive write_set_ element type",
            )
        write_comparator = _unique_region(
            exact, "WriteElement::operator</1", "std::sort comparator",
        )
        write_comparator_error: Optional[AnalysisError] = None
    except AnalysisError as exc:
        write_comparator = None
        write_comparator_error = exc
    try:
        tidword_comparator = _unique_region(
            exact, "Tidword::operator</1", "std::max comparator",
        )
        tidword_comparator_error: Optional[AnalysisError] = None
    except AnalysisError as exc:
        tidword_comparator = None
        tidword_comparator_error = exc

    added_lines: dict[PurePosixPath, set[int]] = defaultdict(set)
    for span in spans:
        added_lines[span.path].update(span.new_lines)

    depth = {root.symbol: 0}
    incoming: dict[str, Optional[CallEdge]] = {root.symbol: None}
    chosen = {root.symbol: root}
    queue = deque([root])

    while queue:
        caller = queue.popleft()
        try:
            calls = _parse_calls(caller)
        except AnalysisError as exc:
            record_expansion_error(exc, caller)
            continue
        for call in calls:
            target: Optional[FunctionRegion] = None
            kind = "direct"
            try:
                normalized_args = re.sub(r"\s+", "", call.args)
                if call.name == "sort" and (
                    not call.qualifier or call.qualifier == "std::"
                ) and normalized_args == "write_set_.begin(),write_set_.end()":
                    if write_comparator is None:
                        raise write_comparator_error or AnalysisError(
                            "TYPE_PROOF_FAILED", "std::sort comparator is unavailable",
                        )
                    target = write_comparator
                    kind = "implicit-comparator"
                elif call.name == "max" and call.qualifier == "std::" and normalized_args in {
                    "max_rset_,check", "max_wset_,expected",
                }:
                    if tidword_comparator is None:
                        raise tidword_comparator_error or AnalysisError(
                            "AMBIGUOUS_CALLEE", "std::max comparator is unavailable",
                        )
                    target = tidword_comparator
                    kind = "implicit-comparator"
                else:
                    target = _resolve_direct_call(
                        call, caller, exact, by_name, edited_regions,
                    )
                if target is not None:
                    signature = "\n".join(
                        target.source.splitlines()[
                            target.start_line - 1:target.signature_line
                        ]
                    )
                    if re.search(r"\bvirtual\b", _strip_comments_and_literals(signature)):
                        raise AnalysisError(
                            "UNSUPPORTED_VIRTUAL_DISPATCH",
                            f"virtual callee {target.symbol} is not statically closed",
                        )
            except AnalysisError as exc:
                record_expansion_error(exc, caller, call)
                continue
            if target is None:
                if (
                    call.line in added_lines.get(caller.path, set())
                    and not call.qualifier.startswith(("std::", "__"))
                    and call.name not in {"static_cast", "const_cast", "reinterpret_cast", "dynamic_cast"}
                ):
                    record_expansion_error(AnalysisError(
                        "UNKNOWN_EDITED_CALLEE",
                        f"new call {call.name}/{call.arity} in {caller.symbol} cannot be resolved",
                    ), caller, call)
                continue
            edge = CallEdge(
                caller=caller.symbol, callee=target.symbol, path=caller.path,
                line=call.line, kind=kind,
            )
            if target.symbol not in depth:
                depth[target.symbol] = depth[caller.symbol] + 1
                incoming[target.symbol] = edge
                chosen[target.symbol] = target
                queue.append(target)
    ordered = sorted(chosen.values(), key=lambda item: (depth[item.symbol], item.symbol))
    return ordered, depth, incoming, expansion_errors


def _strip_cmake_comments(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        quote = False
        escaped = False
        chars = list(line)
        for i, char in enumerate(line):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                quote = not quote
            elif char == "#" and not quote:
                for j in range(i, len(chars)):
                    if chars[j] != "\n":
                        chars[j] = " "
                break
        out.append("".join(chars))
    return "".join(out)


def _balanced_invocations(text: str, name: str) -> list[str]:
    invocations: list[str] = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(", re.IGNORECASE)
    for match in pattern.finditer(text):
        open_paren = text.find("(", match.start(), match.end())
        depth = 0
        quote = False
        escaped = False
        for i in range(open_paren, len(text)):
            char = text[i]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                quote = not quote
                continue
            if quote:
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    invocations.append(text[open_paren + 1:i])
                    break
        else:
            raise AnalysisError("INVALID_CMAKE", f"unbalanced {name}(...) invocation")
    return invocations


def _cmake_model(text: str) -> tuple[dict[str, str], dict[str, str]]:
    clean = _strip_cmake_comments(text)
    defaults: dict[str, str] = {}
    for body in _balanced_invocations(clean, "set"):
        tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s]+', body)
        if len(tokens) >= 4 and re.fullmatch(r"CCBENCH_[A-Z0-9_]+", tokens[0]):
            upper = [token.upper() for token in tokens]
            if "CACHE" in upper:
                defaults[tokens[0]] = tokens[1].strip('"')

    function_match = re.search(
        r"\bfunction\s*\(\s*ccbench_universal_definitions\b.*?\)"
        r"(?P<body>.*?)\bendfunction\s*\(",
        clean, re.IGNORECASE | re.DOTALL,
    )
    if not function_match:
        raise AnalysisError("INVALID_CMAKE", "ccbench_universal_definitions not found")
    mappings = {
        macro: variable
        for macro, variable in re.findall(
            r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=\s*\$\{(CCBENCH_[A-Z0-9_]+)\}\s*$",
            function_match.group("body"),
        )
    }
    return defaults, mappings


def _changed_cmake_macros(before: str, after: str) -> tuple[set[str], dict[str, list[str]]]:
    before_defaults, before_mappings = _cmake_model(before)
    after_defaults, after_mappings = _cmake_model(after)
    macros: set[str] = set()
    reasons: dict[str, set[str]] = defaultdict(set)
    for macro in sorted(set(before_mappings) | set(after_mappings)):
        if before_mappings.get(macro) != after_mappings.get(macro):
            macros.add(macro)
            reasons[macro].add("universal-definition-mapping")
    variables = set(before_defaults) | set(after_defaults)
    for variable in sorted(variables):
        if before_defaults.get(variable) == after_defaults.get(variable):
            continue
        supplied = {
            macro for macro, mapped in before_mappings.items() if mapped == variable
        } | {
            macro for macro, mapped in after_mappings.items() if mapped == variable
        }
        for macro in supplied:
            macros.add(macro)
            reasons[macro].add("cache-default")
    return macros, {macro: sorted(values) for macro, values in reasons.items()}


def _conditional_macro_span(lines: Iterable[str]) -> tuple[bool, set[str]]:
    macros: set[str] = set()
    saw_conditional = False
    continuation = False
    for line in lines:
        if not line.strip():
            continue
        if continuation:
            match_body = line
        else:
            match = re.match(
                r"\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)$", line,
            )
            if not match:
                return False, macros
            saw_conditional = True
            match_body = match.group(2) if match.group(1) in {
                "if", "ifdef", "ifndef", "elif",
            } else ""
        for token in re.findall(r"\b[A-Z][A-Z0-9_]*\b", match_body):
            macros.add(token)
        continuation = line.rstrip().endswith("\\")
    return saw_conditional and not continuation and bool(macros), macros


def _required_macro_guard_span(lines: Iterable[str]) -> set[str]:
    nonempty = [line.strip() for line in lines if line.strip()]
    if len(nonempty) != 3:
        return set()
    opening = re.fullmatch(r"#\s*ifndef\s+([A-Z][A-Z0-9_]*)", nonempty[0])
    if not opening or not re.fullmatch(r"#\s*error\b.*", nonempty[1]):
        return set()
    if not re.fullmatch(r"#\s*endif\b.*", nonempty[2]):
        return set()
    return {opening.group(1)}


def _lexical_span_lines(
    span: EditSpan,
    pre_images: dict[PurePosixPath, str],
    post_images: dict[PurePosixPath, str],
) -> list[str]:
    if span.operation == "addition":
        source = post_images[span.path]
        line_numbers = span.new_lines
    else:
        source = pre_images[span.path]
        line_numbers = span.old_lines
    clean_lines = _strip_comments_and_literals(source).splitlines()
    return [clean_lines[number - 1] for number in line_numbers]


def _span_in_region(span: EditSpan, regions: list[FunctionRegion]) -> list[FunctionRegion]:
    candidates: list[FunctionRegion] = []
    if span.new_lines:
        low, high = min(span.new_lines), max(span.new_lines)
        candidates = [r for r in regions if r.start_line <= low and high <= r.end_line]
    elif span.deletion_anchor is not None:
        point = span.deletion_anchor + 1
        candidates = [r for r in regions if r.start_line <= point <= r.end_line]
    return candidates


def _validate_cmake_span(span: EditSpan, changed: set[str]) -> tuple[bool, set[str]]:
    text = "\n".join(span.text)
    clean = _strip_cmake_comments(text)
    nonempty = [line.strip() for line in clean.splitlines() if line.strip()]
    identifiers = set(re.findall(r"\b(?:CCBENCH_)?[A-Z][A-Z0-9_]*\b", clean))
    targets = {macro for macro in changed if macro in identifiers or f"CCBENCH_{macro}" in identifiers}
    if not nonempty:
        return True, targets
    for line in nonempty:
        if re.fullmatch(r"set\s*\(\s*CCBENCH_[A-Z0-9_]+\b.*\)", line):
            continue
        if re.fullmatch(r"[A-Z][A-Z0-9_]*\s*=\s*\$\{CCBENCH_[A-Z0-9_]+\}", line):
            continue
        return False, targets
    return bool(targets), targets


def _classify_edits(
    spans: list[EditSpan], regions: list[FunctionRegion],
    reachable: set[PurePosixPath], cmake_changed: set[str],
    pre_images: dict[PurePosixPath, str],
    post_images: dict[PurePosixPath, str],
) -> tuple[list[dict], list[dict], set[str], set[str]]:
    by_path: dict[PurePosixPath, list[FunctionRegion]] = defaultdict(list)
    for region in regions:
        by_path[region.path].append(region)
    classified: list[dict] = []
    unconsumed: list[dict] = []
    edited_regions: set[str] = set()
    conditional_macros: set[str] = set()
    for span in spans:
        evidence = span.evidence()
        if span.path == _OPTIONS:
            valid, targets = _validate_cmake_span(span, cmake_changed)
            if valid:
                evidence.update({
                    "classification": "macro-inspection",
                    "targets": sorted(targets),
                })
                classified.append(evidence)
            else:
                evidence["reason"] = "CMake edit is not explained by changed cache/supply mapping"
                unconsumed.append(evidence)
            continue
        if span.path.suffix.lower() not in _CXX_SUFFIXES or span.path not in reachable:
            evidence["reason"] = "edited file is outside the reachable Silo source set"
            unconsumed.append(evidence)
            continue
        lexical_lines = _lexical_span_lines(span, pre_images, post_images)
        edit_text = "\n".join(lexical_lines)
        if re.search(r"(?m)^\s*#\s*(?:define|undef|include)\b", edit_text) or "##" in edit_text:
            evidence["reason"] = "edited define/undef/include or token paste is unsupported"
            unconsumed.append(evidence)
            continue
        candidates = _span_in_region(span, by_path[span.path])
        if len(candidates) == 1:
            region = candidates[0]
            evidence.update({
                "classification": "function-region",
                "targets": [region.symbol],
            })
            classified.append(evidence)
            edited_regions.add(region.symbol)
            continue
        valid_macro_span, macros = _conditional_macro_span(lexical_lines)
        if not candidates and valid_macro_span:
            evidence.update({
                "classification": "macro-inspection",
                "targets": sorted(macros),
            })
            classified.append(evidence)
            conditional_macros.update(macros)
            continue
        required_macros = _required_macro_guard_span(lexical_lines)
        if not candidates and required_macros:
            evidence.update({
                "classification": "compile-time-requirement",
                "targets": sorted(required_macros),
            })
            classified.append(evidence)
            conditional_macros.update(required_macros)
            continue
        evidence["reason"] = (
            "edit maps to multiple function regions" if candidates
            else "edit maps to neither a function region nor a conditional macro inspection"
        )
        unconsumed.append(evidence)
    return classified, unconsumed, edited_regions, conditional_macros


def _macro_references(
    macros: set[str], closure: list[FunctionRegion]
) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {macro: [] for macro in sorted(macros)}
    for region in closure:
        # Macro influence includes the signature's contiguous decorators as well
        # as the body.  Unlike call extraction, directives stay visible here.
        source_lines = region.source.splitlines()
        raw_region = "\n".join(source_lines[region.start_line - 1:region.end_line])
        clean = _strip_comments_and_literals(raw_region)
        tokens = set(re.findall(r"\b[A-Za-z_]\w*\b", clean))
        for macro in sorted(macros & tokens):
            result[macro].append({
                "symbol": region.symbol,
                "path": region.path.as_posix(),
                "depth": None,
            })
    return result


def analyze(repo_root: Path | str, patch: Path | str) -> dict:
    """Return a JSON-serializable result; every inability to decide is ERROR."""
    root = Path(repo_root)
    patch_path = Path(patch)
    result = _base_result(patch_path)
    try:
        ccbench = root / "external" / "ccbench"
        required = [
            root / ".git", ccbench / ".git",
            ccbench / _ROOT_TU.as_posix(),
            ccbench / "cc/silo/include/transaction.hh",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise AnalysisError(
                "CCBENCH_ROOT_UNINITIALIZED",
                "repo/submodule root is missing required paths: " + ", ".join(missing),
            )
        patch_text = _read_utf8(patch_path, "PATCH_UNREADABLE")
        patch_files = _parse_patch(patch_text)
        pre_images, post_images, spans = _apply_patch(ccbench, patch_files)

        cmake_changed: set[str] = set()
        cmake_reasons: dict[str, list[str]] = {}
        if _OPTIONS in post_images:
            cmake_changed, cmake_reasons = _changed_cmake_macros(
                pre_images[_OPTIONS], post_images[_OPTIONS]
            )

        sources = _collect_sources(ccbench, post_images)
        regions: list[FunctionRegion] = []
        for path in sorted(sources, key=lambda item: item.as_posix()):
            regions.extend(_extract_functions(path, sources[path]))
        classified, unconsumed, edited_regions, conditional = _classify_edits(
            spans, regions, set(sources), cmake_changed,
            pre_images, post_images,
        )
        result["classified_edits"] = classified
        result["unconsumed_edits"] = unconsumed
        result["conditional_macros"] = sorted(conditional)

        closure, depths, incoming, expansion_errors = _build_closure(
            regions, sources, spans, edited_regions,
        )
        result["closure_expansion_errors"] = expansion_errors
        result["closure"] = [
            region.closure_evidence(depths[region.symbol], incoming[region.symbol])
            for region in closure
        ]
        all_macros = set(cmake_changed) | set(conditional)
        references = _macro_references(all_macros, closure)
        for macro_refs in references.values():
            for ref in macro_refs:
                ref["depth"] = depths[ref["symbol"]]
        result["cmake_macros"] = [
            {
                "macro": macro,
                "change_kinds": cmake_reasons.get(macro, []),
                "closure_references": references.get(macro, []),
            }
            for macro in sorted(cmake_changed)
        ]

        intersections: list[dict] = []
        closure_by_symbol = {region.symbol: region for region in closure}
        for item in classified:
            if item["classification"] != "function-region":
                continue
            for symbol in item["targets"]:
                if symbol in closure_by_symbol:
                    intersections.append({
                        "kind": "function-region",
                        "edit_id": item["edit_id"],
                        "symbol": symbol,
                        "path": closure_by_symbol[symbol].path.as_posix(),
                        "depth": depths[symbol],
                    })
        for macro in sorted(all_macros):
            for ref in references.get(macro, []):
                intersections.append({
                    "kind": "macro-reference",
                    "macro": macro,
                    "symbol": ref["symbol"],
                    "path": ref["path"],
                    "depth": ref["depth"],
                })
        intersections.sort(key=lambda item: (
            item["kind"], item.get("edit_id", ""), item.get("macro", ""),
            item["depth"], item["symbol"],
        ))
        result["intersections"] = intersections
        if intersections:
            result["verdict"] = INTERSECTION
            return result
        if unconsumed:
            result["error"] = {
                "code": "UNCONSUMED_EDITS",
                "message": f"{len(unconsumed)} edit span(s) were not classified",
            }
            return result
        if expansion_errors:
            result["error"] = {
                "code": "INCOMPLETE_CLOSURE_EXPANSION",
                "message": (
                    f"{len(expansion_errors)} closure expansion step(s) were incomplete"
                ),
            }
            return result
        result["verdict"] = NO_INTERSECTION
        return result
    except AnalysisError as exc:
        result["error"] = {"code": exc.code, "message": exc.message}
        return result
    except Exception as exc:  # Fail closed on parser defects as well as bad input.
        result["error"] = {
            "code": "INTERNAL_ANALYSIS_FAILURE",
            "message": f"unexpected analysis failure: {type(exc).__name__}: {exc}",
        }
        return result


def _exit_code(result: dict) -> int:
    if result["verdict"] == NO_INTERSECTION:
        return 0
    if result["verdict"] == INTERSECTION:
        return 1
    return 2


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        result = _base_result(args[0] if args else "<missing-patch-argument>")
        result["error"] = {
            "code": "USAGE",
            "message": "usage: check_silo_validation_isolation.py PATCH",
        }
    else:
        repo_root = Path(__file__).resolve().parents[1]
        result = analyze(repo_root, Path(args[0]))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
