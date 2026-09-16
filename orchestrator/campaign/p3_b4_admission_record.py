# -*- coding: utf-8 -*-
"""Verify one repository-local P3 B-4 pre-run admission record.

This verifier proves only repository-local ordering: before the provider query
of this invocation, the exact verified record bytes existed in a Git commit
tree.  It does not prove that another route, including a test-only factory, a
direct Python API call, or an earlier similar experiment, did not reveal a
result before the record was committed.  Git author and committer timestamps
are not an absolute chronology relative to activity outside the repository.

The required-path gate proves only that the resolved repository-relative
record path equals the path selected by ``driver_kind``.  It does not prove
that the record at the required path has correct contents.  It does not prove
that the mapping in this module is a preregistered source of truth.  It does
not prove that there is a single path across drivers.  It does not prevent a
commit from changing the mapping or the record at the required path.  It does
not block a route that learns a result outside Git before committing the
record at the required path.

The expected model can be checked only after the critic query and provider
envelope, including modelUsage, have been saved and validated.  The verifier
therefore cannot prevent an operator from seeing output, changing the model
field, committing a new record, and starting a new invocation.  Rebuilding a
record after such a mismatch and continuing the same experiment is a protocol
change, not maintenance.

Complete admission Section 5 validation checks the fixed raw table shape, nonempty source cells,
a closed reserved-sentinel list, and fixed model, prompt, and driver-tagged
projection declarations.  It does not check cell types, meanings, or rendered
non-emptiness for the remaining cells.
Floor reading shares the fixed-table parser and owner-cell predicate, but does
not validate other cells' sentinels or expectation declarations.
HTML comment detection is a line-oriented simple search: ``<!--`` inside an
inline code span, an indented code block, or a backslash escape is also treated
as a comment opener.  Thus otherwise valid documents containing those forms
before Section 5 are intentionally rejected fail-closed; this over-rejection
does not admit a document that must be rejected.  Raw HTML blocks other than
HTML comments are not checked.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Literal


SCHEMA_VERSION = "p3-b4-prerun-admission/v1"
PREREGISTRATION_REPOSITORY_PATH = (
    "docs/phase3-b4-reflux-ablation-preregistration.md"
)

_RECORD_UNAVAILABLE = "[admission-record] record is unavailable"
_RECORD_NOT_AT_HEAD = (
    "[admission-record] record is not committed at execution HEAD"
)
_RECORD_REPOSITORY_PATH_NOT_REQUIRED_FOR_DRIVER_KIND = (
    "[admission-record] record repository path is not the path required for "
    "driver_kind"
)
_DOCUMENT_NOT_VERIFIABLE = (
    "[admission-preregistration] document binding is not verifiable"
)
_SECTION5_SOURCE_CELL_CONTRACT_FAILED = (
    "[admission-preregistration] section 5 fixed table requires nonempty "
    "source cells and no reserved sentinel; types, meanings, and rendered "
    "non-emptiness are not checked"
)

_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_SECTION5_LABELS = (
    "対象 driver と軸",
    "赤 precursor の母集合 (workload・赤形状・初期 proposal)",
    "アームあたり block 数 n と検定単位",
    "primary outcome の演算定義 (純関数)",
    "floor (対象動作点で再実測した between-run floor) の artifact パスと hash",
    "校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash",
    "総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限",
    "env_tag (実測環境)",
    "model snapshot / prompt hash / projection hash",
    "実行責任者・開始時刻",
)
_EXPECTATION_ROW_LABEL = "model snapshot / prompt hash / projection hash"
B4ProjectionDriverKind = Literal["base", "sort", "trigger"]
B4_PROJECTION_DRIVER_KINDS: Final[tuple[B4ProjectionDriverKind, ...]] = (
    "base",
    "sort",
    "trigger",
)
_REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER: Final[
    MappingProxyType[B4ProjectionDriverKind, str]
] = MappingProxyType({
    "base": "docs/phase3-b4-reflux-ablation-admission-record-base.json",
    "sort": "docs/phase3-b4-reflux-ablation-admission-record-sort.json",
    "trigger": "docs/phase3-b4-reflux-ablation-admission-record-trigger.json",
})
_EXPECTATION_ROW_RE = re.compile(
    r"expected_claude_model_snapshot="
    r"(?P<model>claude-opus-[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*); "
    r"expected_effective_critic_prompt_sha256=(?P<prompt>[0-9a-f]{64}); "
    r"expected_closed_critic_projection_closure_sha256\[base\]="
    r"(?P<projection_base>[0-9a-f]{64}); "
    r"expected_closed_critic_projection_closure_sha256\[sort\]="
    r"(?P<projection_sort>[0-9a-f]{64}); "
    r"expected_closed_critic_projection_closure_sha256\[trigger\]="
    r"(?P<projection_trigger>[0-9a-f]{64})"
)
_RESERVED_SENTINEL_RE = re.compile(
    r"(?:未記入|要記入|(?<!\w)"
    r"(?:TBD|TODO|FIXME|PLACEHOLDER|N/?A)(?!\w))",
    re.IGNORECASE,
)
_RESERVED_SENTINEL_WHOLE_VALUES = frozenset(
    {"x", "-", "--", "---", "—", "…", "..."}
)
_DEFAULT_IGNORABLE_RANGES = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)
_FENCE_OPEN_RE = re.compile(
    r" {0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)"
)


class B4AdmissionRecordError(RuntimeError):
    """The admission record or one of its declared expectations is invalid."""


@dataclass(frozen=True)
class VerifiedB4AdmissionRecord:
    """Immutable values obtained from exact committed record and document bytes."""

    admission_record_repository_path: str
    admission_record_sha256: str
    admission_record_commit: str
    preregistration_repository_path: str
    preregistration_content_commit: str
    preregistration_content_sha256: str
    expected_claude_model_snapshot: str
    expected_effective_critic_prompt_sha256: str
    expected_closed_critic_projection_closure_sha256: str
    expected_closed_critic_projection_closure_sha256_by_driver: (
        MappingProxyType[B4ProjectionDriverKind, str]
    )


@dataclass(frozen=True)
class _Section5ClosedCriticExpectationRow:
    expected_claude_model_snapshot: str
    expected_effective_critic_prompt_sha256: str
    expected_closed_critic_projection_closure_sha256_by_driver: (
        MappingProxyType[B4ProjectionDriverKind, str]
    )


@dataclass(frozen=True)
class _DeclaredAdmissionRecord:
    preregistration_repository_path: str
    preregistration_content_commit: str
    preregistration_content_sha256: str
    expected_claude_model_snapshot: str
    expected_effective_critic_prompt_sha256: str
    expected_closed_critic_projection_closure_sha256: str


class _GitVerificationFailure(RuntimeError):
    pass


class _RecordSchemaFailure(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _RecordSchemaFailure("duplicate key")
        value[key] = item
    return value


def _parse_canonical_record(raw: bytes) -> _DeclaredAdmissionRecord:
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
        canonical = _canonical_json_bytes(value)
    except (
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        _RecordSchemaFailure,
    ) as exc:
        raise _RecordSchemaFailure("record is not canonical JSON") from exc
    if raw != canonical or type(value) is not dict:
        raise _RecordSchemaFailure("record bytes are not canonical")
    if set(value) != {
        "schema_version",
        "preregistration_binding",
        "closed_critic_expectations",
    }:
        raise _RecordSchemaFailure("record root keys differ")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise _RecordSchemaFailure("record schema version differs")
    binding = value.get("preregistration_binding")
    expectations = value.get("closed_critic_expectations")
    if type(binding) is not dict or set(binding) != {
        "repository_path",
        "content_commit",
        "content_sha256",
    }:
        raise _RecordSchemaFailure("binding keys differ")
    if type(expectations) is not dict or set(expectations) != {
        "expected_claude_model_snapshot",
        "expected_effective_critic_prompt_sha256",
        "expected_closed_critic_projection_closure_sha256",
    }:
        raise _RecordSchemaFailure("expectation keys differ")

    repository_path = binding.get("repository_path")
    content_commit = binding.get("content_commit")
    content_sha256 = binding.get("content_sha256")
    model = expectations.get("expected_claude_model_snapshot")
    prompt = expectations.get("expected_effective_critic_prompt_sha256")
    projection = expectations.get(
        "expected_closed_critic_projection_closure_sha256"
    )
    if (
        type(repository_path) is not str
        or repository_path != PREREGISTRATION_REPOSITORY_PATH
        or type(content_commit) is not str
        or _SHA1_RE.fullmatch(content_commit) is None
        or type(content_sha256) is not str
        or _SHA256_RE.fullmatch(content_sha256) is None
        or type(model) is not str
        or not model.startswith("claude-opus-")
        or type(prompt) is not str
        or _SHA256_RE.fullmatch(prompt) is None
        or type(projection) is not str
        or _SHA256_RE.fullmatch(projection) is None
    ):
        raise _RecordSchemaFailure("record field value is invalid")
    return _DeclaredAdmissionRecord(
        preregistration_repository_path=repository_path,
        preregistration_content_commit=content_commit,
        preregistration_content_sha256=content_sha256,
        expected_claude_model_snapshot=model,
        expected_effective_critic_prompt_sha256=prompt,
        expected_closed_critic_projection_closure_sha256=projection,
    )


def _fixed_git_executable() -> Path:
    for candidate in (Path("/usr/bin/git"), Path("/bin/git")):
        try:
            resolved = candidate.resolve(strict=True)
            mode = resolved.stat().st_mode
        except OSError:
            continue
        if stat.S_ISREG(mode) and os.access(resolved, os.X_OK):
            return resolved
    raise _GitVerificationFailure("fixed Git executable is unavailable")


def _git_environment() -> dict[str, str]:
    return {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


def _git_call(
    repository_root: Path,
    *args: str,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> bytes:
    """Run fixed Git with a fixed allow-list environment; internal use only."""
    try:
        completed = subprocess.run(
            [str(_fixed_git_executable()), "-C", str(repository_root), *args],
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise _GitVerificationFailure("Git process could not start") from exc
    if completed.returncode not in allowed_returncodes:
        raise _GitVerificationFailure("Git command rejected the object graph")
    return completed.stdout


def _decoded_git_path(raw: bytes) -> Path:
    try:
        value = os.fsdecode(raw.rstrip(b"\n"))
        return Path(value).resolve(strict=True)
    except (OSError, UnicodeError) as exc:
        raise _GitVerificationFailure("Git returned an invalid repository path") from exc


def _expected_git_directories(repository_root: Path) -> tuple[Path, Path]:
    marker = repository_root / ".git"
    try:
        marker_stat = marker.lstat()
    except OSError as exc:
        raise _GitVerificationFailure("repository has no Git control path") from exc
    if stat.S_ISLNK(marker_stat.st_mode):
        raise _GitVerificationFailure("Git control path is a symlink")
    if stat.S_ISDIR(marker_stat.st_mode):
        resolved = marker.resolve(strict=True)
        return resolved, resolved
    if not stat.S_ISREG(marker_stat.st_mode):
        raise _GitVerificationFailure("Git control path is not regular")
    try:
        marker_text = marker.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise _GitVerificationFailure("Git control file is unreadable") from exc
    if not marker_text.startswith("gitdir: ") or "\n" in marker_text:
        raise _GitVerificationFailure("Git control file is malformed")
    git_dir_value = Path(marker_text.removeprefix("gitdir: "))
    if not git_dir_value.is_absolute():
        git_dir_value = marker.parent / git_dir_value
    try:
        git_dir = git_dir_value.resolve(strict=True)
    except OSError as exc:
        raise _GitVerificationFailure("linked worktree Git dir is unavailable") from exc
    common_marker = git_dir / "commondir"
    try:
        common_stat = common_marker.lstat()
    except OSError as exc:
        raise _GitVerificationFailure("linked worktree common dir is unavailable") from exc
    if not stat.S_ISREG(common_stat.st_mode) or stat.S_ISLNK(common_stat.st_mode):
        raise _GitVerificationFailure("linked worktree common marker is unsafe")
    try:
        common_value = Path(common_marker.read_text(encoding="utf-8").strip())
        if not common_value.is_absolute():
            common_value = git_dir / common_value
        common_dir = common_value.resolve(strict=True)
        git_dir.relative_to(common_dir / "worktrees")
        repository_root.relative_to(common_dir.parent)
    except (OSError, UnicodeError, ValueError) as exc:
        raise _GitVerificationFailure("linked worktree is outside the repository") from exc
    return git_dir, common_dir


def _assert_git_repository_layout(repository_root: Path) -> None:
    expected_git_dir, expected_common_dir = _expected_git_directories(
        repository_root
    )
    worktree = _decoded_git_path(
        _git_call(repository_root, "rev-parse", "--show-toplevel")
    )
    git_dir = _decoded_git_path(
        _git_call(
            repository_root,
            "rev-parse",
            "--path-format=absolute",
            "--git-dir",
        )
    )
    common_dir = _decoded_git_path(
        _git_call(
            repository_root,
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        )
    )
    object_dir = _decoded_git_path(
        _git_call(
            repository_root,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "objects",
        )
    )
    if (
        worktree != repository_root
        or git_dir != expected_git_dir
        or common_dir != expected_common_dir
        or object_dir != expected_common_dir / "objects"
    ):
        raise _GitVerificationFailure("Git repository layout differs")
    if _git_call(repository_root, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        raise _GitVerificationFailure("Git command is not in the expected worktree")
    for path in (
        expected_common_dir / "objects" / "info" / "alternates",
        expected_common_dir / "info" / "grafts",
    ):
        try:
            if path.is_file() and path.read_bytes().strip():
                raise _GitVerificationFailure("alternate object history is configured")
        except OSError as exc:
            raise _GitVerificationFailure("Git object controls are unreadable") from exc


def _repository_relative_regular_file(
    repository_root: Path,
    record_path: str | os.PathLike[str],
) -> tuple[Path, Path]:
    try:
        supplied = Path(record_path)
    except TypeError as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc
    candidate = supplied if supplied.is_absolute() else repository_root / supplied
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(repository_root)
    except ValueError as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc
    if not relative.parts or ".git" in relative.parts:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE)
    current = repository_root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise B4AdmissionRecordError(_RECORD_UNAVAILABLE)
        if not stat.S_ISREG(mode):
            raise B4AdmissionRecordError(_RECORD_UNAVAILABLE)
    except OSError as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc
    return candidate, relative


def _tree_blob(
    repository_root: Path,
    commit: str,
    relative_path: str,
) -> bytes:
    pathspec = f":(top,literal){relative_path}"
    listing = _git_call(
        repository_root,
        "ls-tree",
        "-z",
        "--full-tree",
        commit,
        "--",
        pathspec,
    )
    records = [item for item in listing.split(b"\0") if item]
    if len(records) != 1 or b"\t" not in records[0]:
        raise _GitVerificationFailure("tree path is absent or ambiguous")
    header, returned_path = records[0].split(b"\t", 1)
    parts = header.split(b" ")
    if (
        len(parts) != 3
        or parts[0] not in {b"100644", b"100755"}
        or parts[1] != b"blob"
        or returned_path != os.fsencode(relative_path)
    ):
        raise _GitVerificationFailure("tree path is not one regular blob")
    return _git_call(repository_root, "cat-file", "blob", os.fsdecode(parts[2]))


def assert_admission_expectation(
    field_name: str,
    *,
    expected: str,
    actual: str,
) -> None:
    """Raise the fixed mismatch signature for one exact expectation field."""
    if actual != expected:
        raise B4AdmissionRecordError(f"[admission-mismatch] {field_name}")


def _parse_closed_critic_expectation_row(
    value: str,
) -> _Section5ClosedCriticExpectationRow:
    match = _EXPECTATION_ROW_RE.fullmatch(value)
    if match is None:
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    projection_by_driver = MappingProxyType(
        {
            kind: match.group(f"projection_{kind}")
            for kind in B4_PROJECTION_DRIVER_KINDS
        }
    )
    return _Section5ClosedCriticExpectationRow(
        expected_claude_model_snapshot=match.group("model"),
        expected_effective_critic_prompt_sha256=match.group("prompt"),
        expected_closed_critic_projection_closure_sha256_by_driver=(
            projection_by_driver
        ),
    )


def _contains_default_ignorable_or_format(value: str) -> bool:
    for character in value:
        codepoint = ord(character)
        if unicodedata.category(character) == "Cf" or any(
            lower <= codepoint <= upper
            for lower, upper in _DEFAULT_IGNORABLE_RANGES
        ):
            return True
    return False


def _normalized_source_cell(value: str) -> str:
    if _contains_default_ignorable_or_format(value):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    normalized = unicodedata.normalize("NFKC", value)
    if _contains_default_ignorable_or_format(normalized):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    return normalized


def _markdown_block_context(
    lines: list[str],
) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    fenced = [False] * len(lines)
    html_commented = [False] * len(lines)
    marker_character: str | None = None
    marker_length = 0
    in_html_comment = False
    for index, line in enumerate(lines):
        if marker_character is not None:
            fenced[index] = True
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(marker_character)}"
                rf"{{{marker_length},}}[ \t]*",
                line,
            )
            if closing is not None:
                marker_character = None
                marker_length = 0
            continue
        if in_html_comment:
            html_commented[index] = True
            search_from = 0
            closing_comment = line.find("-->", search_from)
            if closing_comment < 0:
                continue
            in_html_comment = False
            search_from = closing_comment + 3
        else:
            search_from = 0
        opening = _FENCE_OPEN_RE.fullmatch(line)
        if opening is not None:
            marker = opening.group("marker")
            info = opening.group("info")
            if marker[0] == "`" and "`" in info:
                opening = None
        if opening is not None:
            marker_character = marker[0]
            marker_length = len(marker)
            fenced[index] = True
            continue
        while True:
            opening_comment = line.find("<!--", search_from)
            if opening_comment < 0:
                break
            if not line[:opening_comment].strip():
                html_commented[index] = True
            closing_comment = line.find("-->", opening_comment + 4)
            if closing_comment < 0:
                in_html_comment = True
                break
            search_from = closing_comment + 3
    return tuple(fenced), tuple(html_commented)


def _parse_section5_fixed_table_source_cells(
    document_blob: bytes,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return normalized values, stripped raw values, and verbatim labels."""
    try:
        text = document_blob.decode("utf-8-sig")
    except UnicodeError as exc:
        raise B4AdmissionRecordError(
            _SECTION5_SOURCE_CELL_CONTRACT_FAILED
        ) from exc
    lines = text.splitlines()
    fenced_lines, html_commented_lines = _markdown_block_context(lines)
    starts = [
        index
        for index, line in enumerate(lines)
        if not fenced_lines[index]
        and not html_commented_lines[index]
        and re.fullmatch(r"## 5\.(?:\s.*)?", line) is not None
    ]
    ends = [
        index
        for index, line in enumerate(lines)
        if not fenced_lines[index]
        and not html_commented_lines[index]
        and re.fullmatch(r"### 5\.1(?:\s.*)?", line) is not None
    ]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    if any(fenced_lines[starts[0] : ends[0] + 1]) or any(
        html_commented_lines[starts[0] : ends[0] + 1]
    ):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    table = [line for line in lines[starts[0] + 1 : ends[0]] if line.strip()]
    if len(table) != len(_SECTION5_LABELS) + 2:
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    if table[:2] != ["|欄|値|", "|---|---|"]:
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    values: dict[str, str] = {}
    raw_values: dict[str, str] = {}
    verbatim_labels: dict[str, str] = {}
    for line in table[2:]:
        if not line.startswith("|") or not line.endswith("|"):
            raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
        cells = line[1:-1].split("|")
        if len(cells) != 2:
            raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
        raw_label, raw_value = (cell.strip() for cell in cells)
        label = _normalized_source_cell(raw_label)
        value = _normalized_source_cell(raw_value)
        if label in values:
            raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
        values[label] = value
        raw_values[label] = raw_value
        verbatim_labels[label] = cells[0]
    if set(values) != set(_SECTION5_LABELS):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)
    return values, raw_values, verbatim_labels


def _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(
    label: str, value: str,
) -> None:
    """Apply the admission predicate to one already-normalized source cell."""
    if label == "実行責任者・開始時刻":
        match = re.fullmatch(
            r"実行責任者 = (?P<owner>[^、=\r\n]+)、開始時刻 = 未記入",
            value,
        )
        if match is not None:
            owner = match.group("owner").strip()
            if (
                owner
                and _RESERVED_SENTINEL_RE.search(owner) is None
                and owner.casefold() not in _RESERVED_SENTINEL_WHOLE_VALUES
            ):
                return
    if (
        not value
        or _RESERVED_SENTINEL_RE.search(value) is not None
        or value.casefold() in _RESERVED_SENTINEL_WHOLE_VALUES
    ):
        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)


def assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
    document_blob: bytes,
    *,
    expected_claude_model_snapshot: str,
    expected_effective_critic_prompt_sha256: str,
) -> MappingProxyType[B4ProjectionDriverKind, str]:
    """Check source cells, bind model and prompt, and return projections.

    HTML comment detection is a line-oriented simple search: ``<!--`` inside
    an inline code span, an indented code block, or a backslash escape is also
    treated as a comment opener.  Thus otherwise valid documents containing
    those forms before Section 5 are intentionally rejected fail-closed; this
    over-rejection does not admit a document that must be rejected.  Raw HTML
    blocks other than HTML comments are not checked.
    """
    values, raw_values, _ = _parse_section5_fixed_table_source_cells(document_blob)
    for label, value in values.items():
        _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(
            label, value
        )
    _parse_closed_critic_expectation_row(raw_values[_EXPECTATION_ROW_LABEL])
    expectation_row = _parse_closed_critic_expectation_row(
        values[_EXPECTATION_ROW_LABEL]
    )
    assert_admission_expectation(
        "expected_claude_model_snapshot",
        expected=expected_claude_model_snapshot,
        actual=expectation_row.expected_claude_model_snapshot,
    )
    assert_admission_expectation(
        "expected_effective_critic_prompt_sha256",
        expected=expected_effective_critic_prompt_sha256,
        actual=expectation_row.expected_effective_critic_prompt_sha256,
    )
    return expectation_row.expected_closed_critic_projection_closure_sha256_by_driver


def verify_b4_admission_record(
    admission_record_path: str | os.PathLike[str],
    *,
    repository_root: str | os.PathLike[str],
    driver_kind: B4ProjectionDriverKind,
) -> VerifiedB4AdmissionRecord:
    """Return declarations after exact record, document, and Git validation."""
    if (
        type(driver_kind) is not str
        or driver_kind not in B4_PROJECTION_DRIVER_KINDS
    ):
        raise B4AdmissionRecordError(
            "[admission-mismatch] "
            "expected_closed_critic_projection_closure_sha256"
        )
    try:
        root = Path(repository_root).resolve(strict=True)
    except (TypeError, OSError) as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc
    record_path, relative_record_path = _repository_relative_regular_file(
        root,
        admission_record_path,
    )
    if (
        relative_record_path.as_posix()
        != _REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER[driver_kind]
    ):
        raise B4AdmissionRecordError(
            _RECORD_REPOSITORY_PATH_NOT_REQUIRED_FOR_DRIVER_KIND
        )
    try:
        record_bytes = record_path.read_bytes()
    except OSError as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc

    try:
        _assert_git_repository_layout(root)
        head = _git_call(root, "rev-parse", "HEAD^{commit}").strip().decode("ascii")
        if _SHA1_RE.fullmatch(head) is None:
            raise _GitVerificationFailure("HEAD is not one SHA-1 commit")
        committed_record_bytes = _tree_blob(
            root,
            head,
            relative_record_path.as_posix(),
        )
    except (_GitVerificationFailure, UnicodeError) as exc:
        raise B4AdmissionRecordError(_RECORD_NOT_AT_HEAD) from exc
    if committed_record_bytes != record_bytes:
        raise B4AdmissionRecordError(_RECORD_NOT_AT_HEAD)

    try:
        declared = _parse_canonical_record(record_bytes)
    except _RecordSchemaFailure as exc:
        raise B4AdmissionRecordError(_RECORD_UNAVAILABLE) from exc

    try:
        object_type = _git_call(
            root,
            "cat-file",
            "-t",
            declared.preregistration_content_commit,
        ).strip()
        exact_commit = _git_call(
            root,
            "rev-parse",
            f"{declared.preregistration_content_commit}^{{commit}}",
        ).strip().decode("ascii")
        if (
            object_type != b"commit"
            or exact_commit != declared.preregistration_content_commit
        ):
            raise _GitVerificationFailure("declared object is not the exact commit")
        _git_call(
            root,
            "merge-base",
            "--is-ancestor",
            declared.preregistration_content_commit,
            head,
        )
        document_blob = _tree_blob(
            root,
            declared.preregistration_content_commit,
            declared.preregistration_repository_path,
        )
        if _sha256(document_blob) != declared.preregistration_content_sha256:
            raise _GitVerificationFailure("declared document hash differs")
        head_document_blob = _tree_blob(
            root,
            head,
            declared.preregistration_repository_path,
        )
        if head_document_blob != document_blob:
            raise _GitVerificationFailure("HEAD document differs from declared blob")
    except (_GitVerificationFailure, UnicodeError) as exc:
        raise B4AdmissionRecordError(_DOCUMENT_NOT_VERIFIABLE) from exc

    projection_closure_sha256_by_driver = (
        assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
            document_blob,
            expected_claude_model_snapshot=(
                declared.expected_claude_model_snapshot
            ),
            expected_effective_critic_prompt_sha256=(
                declared.expected_effective_critic_prompt_sha256
            ),
        )
    )
    assert_admission_expectation(
        "expected_closed_critic_projection_closure_sha256",
        expected=declared.expected_closed_critic_projection_closure_sha256,
        actual=projection_closure_sha256_by_driver[driver_kind],
    )
    return VerifiedB4AdmissionRecord(
        admission_record_repository_path=relative_record_path.as_posix(),
        admission_record_sha256=_sha256(record_bytes),
        admission_record_commit=head,
        preregistration_repository_path=(
            declared.preregistration_repository_path
        ),
        preregistration_content_commit=declared.preregistration_content_commit,
        preregistration_content_sha256=declared.preregistration_content_sha256,
        expected_claude_model_snapshot=(
            declared.expected_claude_model_snapshot
        ),
        expected_effective_critic_prompt_sha256=(
            declared.expected_effective_critic_prompt_sha256
        ),
        expected_closed_critic_projection_closure_sha256=(
            declared.expected_closed_critic_projection_closure_sha256
        ),
        expected_closed_critic_projection_closure_sha256_by_driver=(
            projection_closure_sha256_by_driver
        ),
    )
