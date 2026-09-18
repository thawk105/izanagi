#!/usr/bin/env python3
"""spool fragment を canonical 台帳へ決定的に畳む。

公開面は ``validate_spool_tree``、``plan_fold``、``apply_fold``、
``mark_fold_committed``、``finalize_fold`` と commit identity gate。
計画は canonical を一切書かず、適用は Git worktree 固有 admin path の state を
先に永続化してから before/after hash に従って resume 可能に進める。
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as _datetime
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Iterable, Mapping, Sequence


SCHEMA = "izanagi-spool-v1"
GLOBAL_ORDINAL_START_DATE = "2026-07-26"
LEDGERS = ("worklog", "decisions", "failures")
LEDGER_RANK = {name: rank for rank, name in enumerate(LEDGERS)}
STATE_NAME = "izanagi-spool-fold-state.json"
RECEIPT_REL = Path("docs/spool/FOLDED.md")
TASK_RE = re.compile(r"\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]")
TASK_HEAD_RE = re.compile(
    r"^(?:- |[1-9][0-9]*\. )(?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\])(?=$|[ \t])"
)
TASK_LIKE_HEAD_RE = re.compile(r"^(?:- |[1-9][0-9]*\. )\[T-[^\]\n]*\]")
PLACEHOLDER_RE = re.compile(
    r"\{\{(?P<namespace>[TDF]):(?P<slug>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)\}\}"
)
SLUG_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
WAVE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEQ_RE = re.compile(r"[1-9][0-9]*")
SHA_RE = re.compile(r"[0-9a-f]{64}")
OID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
REF_RE = re.compile(r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*")
ROTATION_PATH_RE = re.compile(
    r"docs/archive/worklog-phase3-[0-9]{4}-[1-9][0-9]*"
    r"(?:-(?:[1-9][0-9]*|[0-9]{4}-[1-9][0-9]*))?\.md"
)
STATE_VERSION = 3
STATE_PHASES = frozenset({"applied", "committed"})
STATE_FIELDS = frozenset({
    "version", "phase", "transaction_id", "origin",
    "input_closure_sha256", "fold_date", "fragments", "gc_paths",
    "projected_worklog_bytes", "rotation_path", "targets", "gate_receipt",
})
ORIGIN_FIELDS = frozenset({
    "kind", "base", "tested_tip", "wave_ref", "rollback_ref",
    "trusted_main_cutoff", "audited_digest",
})
FRAGMENT_STATE_FIELDS = frozenset({
    "path", "authored", "wave", "seq", "content_sha256", "allocations",
})
TARGET_STATE_FIELDS = frozenset({
    "path", "before_exists", "before_sha256", "after_sha256",
    "after_bytes_b64",
})
GATE_RECEIPT_FIELDS = frozenset({
    "transaction_id", "registry_digest", "nodeids", "target_raw_digests",
    "outcome", "uncovered_families",
})
LEGACY_RECEIPT_FIELDS = frozenset({
    "allocations", "authored", "content_sha256", "seq", "wave",
})
RECEIPT_V2_FIELDS = frozenset({
    "allocations", "authored", "base", "content_sha256", "seq",
    "tested_tip", "wave", "wave_ref",
})
_CLOSURE_FIXED_PATHS = (
    "docs/worklog.md",
    "docs/decisions.md",
    "docs/failures.md",
    "docs/phase3.md",
    "docs/archive/README.md",
    RECEIPT_REL.as_posix(),
    "tools/spool_fold.py",
    "tools/check_docs.py",
)
WORKLOG_ENTRY_RE = re.compile(
    r"^## (?P<date>\d{4}-\d{2}-\d{2}) \((?P<ordinal>[1-9][0-9]*)\) — .+$",
    re.MULTILINE,
)
ARCHIVE_ENTRY_RE = re.compile(
    r"^## (?P<date>\d{4}-\d{2}-\d{2})(?: \((?P<ordinal>[1-9][0-9]*)\))? — .+$",
    re.MULTILINE,
)
NEXT_ACTION_HEADING_RE = re.compile(r"^### 次の一手(?:[ \t].*)?$", re.MULTILINE)
DECISION_ID_RE = re.compile(r"^## D(?P<number>[1-9][0-9]*)\.", re.MULTILINE)
FAILURE_ID_RE = re.compile(r"^### F(?P<number>[1-9][0-9]*)\.", re.MULTILINE)
FAILURE_SUPERSEDE_ITEM_RE = re.compile(
    r"^- F(?P<number>[1-9][0-9]*) "
    r"(?P<body>\*\*supersede: (?P<date>\d{4}-\d{2}-\d{2})\*\* — "
    r"(?P<detail>[^\n]*\S[^\n]*))$"
)
FAILURE_RECURRENCE_SUPERSEDE_MISUSE_RE = re.compile(
    r"^ {0,3}-[ \t]+\*\*supersede:"
)
FAILURE_RECURRENCE_ZERO_WIDTH_TRANSLATION = str.maketrans(
    "", "", "\u200b\u200c\u200d\u2060\ufeff"
)
FAILURE_SUPERSEDE_FORBIDDEN_LINE_BREAKS = frozenset("\r\v\f\u0085\u2028\u2029")
DEFERRED_HEADING_RE = re.compile(r"^## 見送り台帳(?:[ \t].*)?$", re.MULTILINE)
COMPLETION_HEADING_RE = re.compile(r"^### 裁定・完了記録(?:[ \t].*)?$", re.MULTILINE)
H3_RE = re.compile(r"^### (?P<title>[^\n]+)$", re.MULTILINE)
H4_RE = re.compile(r"^#### (?P<title>[^\n]+)$", re.MULTILINE)
TOP_LEVEL_ITEM_RE = re.compile(
    r"^(?:[1-9][0-9]*\.|-)[ \t]+(?P<text>[^\n]*)$", re.MULTILINE
)
FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,}).*$")
MACHINE_FIELD_RE = re.compile(r"  (?P<name>[a-z][a-z0-9_-]*): .+")
FRAGMENT_FILE_RE = re.compile(
    r"(?P<authored>\d{4}-\d{2}-\d{2})-(?P<wave>[a-z0-9]+(?:-[a-z0-9]+)*)-"
    r"(?P<seq>[1-9][0-9]*)\.md"
)
_IMPORT_ROOT = Path(__file__).resolve().parents[1]


@dataclasses.dataclass(frozen=True, order=True)
class Issue:
    """schema/semantic 検査の決定的な finding。"""

    path: str
    line: int
    code: str
    message: str


@dataclasses.dataclass(frozen=True)
class Fragment:
    path: str
    ledger: str
    authored: str
    wave: str
    seq: int
    title: str | None
    body: str
    raw: bytes
    content_sha: str

    @property
    def key(self) -> tuple[str, int, int, str]:
        # authored は provenance 専用で、fold 順には使わない。
        return (self.wave, self.seq, LEDGER_RANK[self.ledger], self.path)


@dataclasses.dataclass(frozen=True)
class Symbol:
    wave: str
    namespace: str
    slug: str
    fragment_path: str
    offset: int

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.wave, self.namespace, self.slug)


@dataclasses.dataclass(frozen=True)
class TargetChange:
    path: str
    before_sha256: str
    after_sha256: str
    before_exists: bool
    after_bytes: bytes = dataclasses.field(repr=False)


@dataclasses.dataclass(frozen=True)
class FoldOrigin:
    kind: str
    base: str
    tested_tip: str
    wave_ref: str
    rollback_ref: str
    trusted_main_cutoff: str
    audited_digest: str


@dataclasses.dataclass(frozen=True)
class FragmentReceipt:
    path: str
    authored: str
    wave: str
    seq: int
    content_sha256: str
    allocations: tuple[tuple[str, str], ...]


@dataclasses.dataclass(frozen=True)
class FoldGateReceipt:
    transaction_id: str
    registry_digest: str
    nodeids: tuple[str, ...]
    target_raw_digests: tuple[tuple[str, str], ...]
    outcome: str
    uncovered_families: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class FoldPlan:
    status: str
    fold_date: str
    transaction_id: str
    origin: FoldOrigin
    input_closure_sha256: str
    phase: str
    allocations: tuple[tuple[str, str], ...]
    targets: tuple[TargetChange, ...]
    fragments: tuple[FragmentReceipt, ...]
    gc_paths: tuple[str, ...]
    projected_worklog_bytes: int
    rotation_path: str | None = None
    gate_receipt: FoldGateReceipt | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "allocations": dict(self.allocations),
            "fold_date": self.fold_date,
            "fragments": [
                {
                    "allocations": dict(fragment.allocations),
                    "authored": fragment.authored,
                    "content_sha256": fragment.content_sha256,
                    "path": fragment.path,
                    "seq": fragment.seq,
                    "wave": fragment.wave,
                }
                for fragment in self.fragments
            ],
            "gc_paths": list(self.gc_paths),
            "projected_worklog_bytes": self.projected_worklog_bytes,
            "rotation_path": self.rotation_path,
            "status": self.status,
            "targets": [
                {
                    "after_sha256": target.after_sha256,
                    "before_exists": target.before_exists,
                    "before_sha256": target.before_sha256,
                    "path": target.path,
                }
                for target in self.targets
            ],
            "transaction_id": self.transaction_id,
        }


@dataclasses.dataclass(frozen=True)
class FoldResult:
    status: str
    transaction_id: str
    written_paths: tuple[str, ...]
    resumed_paths: tuple[str, ...]
    gc_paths: tuple[str, ...]


class SpoolError(RuntimeError):
    """fold の基底例外。"""


class SpoolValidationError(SpoolError):
    def __init__(self, issues: Sequence[Issue]):
        self.issues = tuple(sorted(issues))
        super().__init__("; ".join(issue.message for issue in self.issues))


class TransactionError(SpoolError):
    """transaction の before/after 以外を検出した。"""


class FoldGateReceiptError(TransactionError):
    """land transaction の gate receipt が不在または不正。"""


class _DiffPreflightError(TransactionError):
    """show-diff の全照合中に、diff payload 出力前に検出した不一致。"""


@dataclasses.dataclass(frozen=True)
class _TaskItem:
    task_id: str
    block: str
    substantive_digest: str | None = None


@dataclasses.dataclass(frozen=True)
class _Operation:
    kind: str
    task_id: str | None
    output_block: str
    base: str | None
    category: str | None = None
    slug: str | None = None


@dataclasses.dataclass(frozen=True)
class _DeferredAppend:
    task_id: str
    suffix: str


@dataclasses.dataclass(frozen=True)
class _FailureSupersede:
    target_number: int
    line: str


@dataclasses.dataclass(frozen=True)
class _WorklogDelta:
    prose: str
    operations: tuple[_Operation, ...]
    deferred_appends: tuple[_DeferredAppend, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _git_text(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    try:
        return _git(repo, *args, input_bytes=input_bytes).decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise SpoolValidationError([
            Issue(".git", 1, "origin", "Git observation が ASCII でない")
        ]) from exc


def audited_commit_digest(commits: Sequence[str]) -> str:
    """順序付き audited commit 列の rev-list 互換 bytes を digest する。"""

    values: list[str] = []
    for commit in commits:
        if type(commit) is not str or OID_RE.fullmatch(commit) is None:
            raise ValueError("audited commit は exact Git OID でなければならない")
        values.append(commit)
    return _sha256(b"".join(value.encode("ascii") + b"\n" for value in values))


def _audited_commits(repo: Path, origin: FoldOrigin) -> tuple[str, ...]:
    raw = _git(
        repo,
        "rev-list",
        "--reverse",
        f"{origin.trusted_main_cutoff}..{origin.tested_tip}",
    )
    try:
        commits = tuple(line for line in raw.decode("ascii", errors="strict").splitlines() if line)
    except UnicodeDecodeError as exc:
        raise SpoolValidationError([
            Issue(".git", 1, "origin", "audited commit 列が ASCII でない")
        ]) from exc
    if any(OID_RE.fullmatch(commit) is None for commit in commits):
        raise SpoolValidationError([
            Issue(".git", 1, "origin", "audited commit 列の OID が不正")
        ])
    return commits


def _origin_dict(origin: FoldOrigin) -> dict[str, str]:
    return {
        "kind": origin.kind,
        "base": origin.base,
        "tested_tip": origin.tested_tip,
        "wave_ref": origin.wave_ref,
        "rollback_ref": origin.rollback_ref,
        "trusted_main_cutoff": origin.trusted_main_cutoff,
        "audited_digest": origin.audited_digest,
    }


def _observe_origin(repo: Path, origin: FoldOrigin | None) -> FoldOrigin:
    try:
        head = _git_text(repo, "rev-parse", "--verify", "HEAD^{commit}")
        wave_ref = _git_text(repo, "symbolic-ref", "--quiet", "HEAD")
        ref_head = _git_text(repo, "rev-parse", "--verify", f"{wave_ref}^{{commit}}")
    except (OSError, subprocess.SubprocessError, SpoolValidationError) as exc:
        if isinstance(exc, SpoolValidationError):
            raise
        raise SpoolValidationError([
            Issue(".git", 1, "origin", f"HEAD / symbolic HEAD を観測できない: {exc}")
        ]) from exc
    if OID_RE.fullmatch(head) is None or ref_head != head or REF_RE.fullmatch(wave_ref) is None:
        raise SpoolValidationError([
            Issue(".git", 1, "origin", "HEAD / symbolic HEAD / ref SHA が一致しない")
        ])
    if origin is None:
        origin = FoldOrigin(
            kind="standalone",
            base=head,
            tested_tip=head,
            wave_ref=wave_ref,
            rollback_ref=head,
            trusted_main_cutoff=head,
            audited_digest=audited_commit_digest(()),
        )
    if type(origin) is not FoldOrigin:
        raise SpoolValidationError([
            Issue("origin", 1, "origin", "origin は FoldOrigin exact object が必要")
        ])
    values = _origin_dict(origin)
    if (
        any(type(value) is not str for value in values.values())
        or origin.kind not in {"land", "standalone"}
        or OID_RE.fullmatch(origin.base) is None
        or OID_RE.fullmatch(origin.tested_tip) is None
        or OID_RE.fullmatch(origin.rollback_ref) is None
        or OID_RE.fullmatch(origin.trusted_main_cutoff) is None
        or REF_RE.fullmatch(origin.wave_ref) is None
        or SHA_RE.fullmatch(origin.audited_digest) is None
    ):
        raise SpoolValidationError([
            Issue("origin", 1, "origin", "FoldOrigin の値型/正規形が不正")
        ])
    if origin.tested_tip != head or origin.wave_ref != wave_ref or ref_head != origin.tested_tip:
        raise SpoolValidationError([
            Issue("origin", 1, "origin", "origin tested_tip / wave_ref が plan repo の観測値と不一致")
        ])
    try:
        for label, value in (
            ("base", origin.base),
            ("rollback_ref", origin.rollback_ref),
            ("trusted_main_cutoff", origin.trusted_main_cutoff),
        ):
            resolved = _git_text(repo, "rev-parse", "--verify", f"{value}^{{commit}}")
            if resolved != value:
                raise SpoolValidationError([
                    Issue("origin", 1, "origin", f"origin {label} が exact commit でない")
                ])
        audited = _audited_commits(repo, origin)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SpoolValidationError([
            Issue("origin", 1, "origin", f"origin commit を照合できない: {exc}")
        ]) from exc
    if audited_commit_digest(audited) != origin.audited_digest:
        raise SpoolValidationError([
            Issue("origin", 1, "origin", "origin audited_digest が観測した commit 列と不一致")
        ])
    return origin


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _issue(path: str, text: str, offset: int, code: str, message: str) -> Issue:
    return Issue(path, _line(text, offset), code, message)


def _parse_iso_date(value: object) -> _datetime.date | None:
    if not isinstance(value, str):
        return None
    try:
        return _datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _valid_date(value: str) -> bool:
    return _parse_iso_date(value) is not None


def _current_fold_date() -> str:
    """canonical 日付。fragment authored からは決して導出しない。"""

    return _datetime.datetime.now().astimezone().date().isoformat()


def _read_regular_utf8_lf(path: Path, rel: str) -> tuple[bytes | None, str | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        return None, None, [Issue(rel, 1, "read", f"{rel}: 読み取れない: {exc}")]
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        return None, None, [Issue(rel, 1, "regular-file", f"{rel}: symlink/非 regular file は不可")]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, None, [Issue(rel, 1, "read", f"{rel}: 読み取れない: {exc}")]
    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append(Issue(rel, 1, "bom", f"{rel}: UTF-8 BOM は不可"))
    if b"\r" in raw:
        issues.append(Issue(rel, 1, "line-ending", f"{rel}: CR/CRLF は不可"))
    if raw and not raw.endswith(b"\n"):
        issues.append(Issue(rel, 1, "final-newline", f"{rel}: 末尾 newline が必要"))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        issues.append(Issue(rel, exc.start + 1, "utf8", f"{rel}: UTF-8 として読めない"))
        return raw, None, issues
    return raw, text, issues


def _parse_frontmatter(rel: str, text: str) -> tuple[dict[str, str] | None, str, list[Issue]]:
    issues: list[Issue] = []
    if not text.startswith("---\n"):
        return None, "", [Issue(rel, 1, "frontmatter", f"{rel}: frontmatter 開始がない")]
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, "", [Issue(rel, 1, "frontmatter", f"{rel}: frontmatter 終端がない")]
    fields: dict[str, str] = {}
    cursor = 4
    for raw_line in text[4:end].splitlines(keepends=True):
        line = raw_line.rstrip("\n")
        match = re.fullmatch(r"([a-z]+): ([^\n]+)", line)
        if match is None:
            issues.append(_issue(rel, text, cursor, "frontmatter-line", f"{rel}: frontmatter は `key: value` 限定"))
        else:
            key, value = match.groups()
            if key in fields:
                issues.append(_issue(rel, text, cursor, "frontmatter-duplicate", f"{rel}: field {key!r} が重複"))
            elif not value:
                issues.append(_issue(rel, text, cursor, "frontmatter-empty", f"{rel}: field {key!r} が空"))
            else:
                fields[key] = value
        cursor += len(raw_line)
    return fields, text[end + 5 :], issues


def _split_top_items(body: str, base_offset: int = 0) -> list[tuple[str, int]]:
    starts = list(re.finditer(r"^(?:- |[1-9][0-9]*\. ).+$", body, re.MULTILINE))
    result: list[tuple[str, int]] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        block = body[match.start() : end].rstrip("\n") + "\n"
        result.append((block, base_offset + match.start()))
    return result


def _task_item_digest(block: str) -> str:
    """実質的に書かれた item bytes の digest（末尾 LF を 1 個に正規化）。"""

    return _sha256((block.rstrip("\n") + "\n").encode("utf-8"))


def _unconsumed_prefix(
    rel: str,
    whole: str,
    region: str,
    region_offset: int,
    consumed_starts: Sequence[int],
    code: str,
    message: str,
) -> list[Issue]:
    """構造化領域の最初の消費単位より前にある非空 bytes を拒否する。"""

    prefix_end = min(consumed_starts, default=len(region))
    prefix = region[:prefix_end]
    if not prefix.strip():
        return []
    first_nonspace = next(
        (index for index, character in enumerate(prefix) if not character.isspace()),
        0,
    )
    return [_issue(rel, whole, region_offset + first_nonspace, code, message)]


def _item_continuations_are_indented(block: str) -> bool:
    return all(not line or line.startswith("  ") for line in block.rstrip("\n").split("\n")[1:])


def _mask_html_comments(
    line: str,
    in_comment: bool,
    *,
    preserve_width: bool = True,
) -> tuple[str, bool]:
    """HTML comment を空白または空文字へ投影し、行をまたぐ状態を返す。"""

    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                if preserve_width:
                    visible.append(" " * (len(line) - cursor))
                cursor = len(line)
            else:
                end += len("-->")
                if preserve_width:
                    visible.append(" " * (end - cursor))
                cursor = end
                in_comment = False
            continue

        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            cursor = len(line)
        else:
            visible.append(line[cursor:start])
            cursor = start
            in_comment = True
    return "".join(visible), in_comment


def _visible_markdown_lines_in_container(
    text: str,
    *,
    list_container_width: int,
    collapse_html_comments: bool = False,
) -> list[tuple[str, int, str]]:
    """指定した list container 内で可視行と offset・改行を返す。"""

    lines: list[tuple[str, int, str]] = []
    in_comment = False
    fence: tuple[str, int] | None = None
    offset = 0

    def fence_view(line: str) -> str:
        prefix = " " * list_container_width
        if prefix and line.startswith(prefix):
            return line[list_container_width:]
        return line

    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        newline = raw_line[len(line):]
        if fence is not None:
            marker_char, marker_len = fence
            relative = fence_view(line)
            stripped = relative.lstrip(" \t")
            indent = len(relative) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        # fence opener の info string 内にある `<!--` は comment 開始ではない。
        if not in_comment:
            fence_match = FENCE_OPEN_RE.fullmatch(fence_view(line))
            if fence_match is not None:
                marker = fence_match.group("marker")
                fence = (marker[0], len(marker))
                lines.append(("", offset, newline))
                offset += len(raw_line)
                continue

        visible, in_comment = _mask_html_comments(
            line,
            in_comment,
            preserve_width=not collapse_html_comments,
        )
        fence_match = FENCE_OPEN_RE.fullmatch(fence_view(visible))
        if fence_match is not None:
            marker = fence_match.group("marker")
            fence = (marker[0], len(marker))
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        lines.append((visible, offset, newline))
        offset += len(raw_line)
    return lines


def _visible_markdown_lines(
    text: str,
    *,
    collapse_html_comments: bool = False,
) -> list[tuple[str, int, str]]:
    """top-level の code fence / HTML comment 外の可視行を返す。"""

    return _visible_markdown_lines_in_container(
        text,
        list_container_width=0,
        collapse_html_comments=collapse_html_comments,
    )


def _visible_item_markdown_lines(text: str) -> list[tuple[str, int, str]]:
    """`- ` item container 相対の code fence / comment 外の可視行を返す。"""

    return _visible_markdown_lines_in_container(text, list_container_width=2)


def _strip_base(rel: str, whole: str, block: str, offset: int) -> tuple[str, str | None, list[Issue]]:
    matches = list(re.finditer(r"^  base: (?P<digest>[0-9a-f]{64})$", block, re.MULTILINE))
    if len(matches) != 1:
        return block, None, [
            _issue(rel, whole, offset, "base", f"{rel}: 操作 item には `  base: <sha256>` が 1 件必要")
        ]
    match = matches[0]
    line_start = match.start()
    line_end = match.end()
    if line_end < len(block) and block[line_end] == "\n":
        line_end += 1
    output = block[:line_start] + block[line_end:]
    output = output.rstrip("\n") + "\n"
    return output, match.group("digest"), []


def _strip_completion_remaining(rel: str, whole: str, block: str, offset: int) -> tuple[str, list[Issue]]:
    """item 末尾の可視な機械 field 群から exact-one remaining を除く。"""

    trailer: list[tuple[str, int, int]] = []
    for visible, line_offset, newline in reversed(_visible_item_markdown_lines(block)):
        field = MACHINE_FIELD_RE.fullmatch(visible)
        if field is None:
            break
        trailer.append((field.group("name"), line_offset, line_offset + len(visible) + len(newline)))
    remaining = [entry for entry in trailer if entry[0] == "remaining"]
    if len(remaining) != 1:
        return block, [
            _issue(
                rel,
                whole,
                offset,
                "completion-remaining-field",
                f"{rel}: `完了` item 末尾には `  remaining: none` が 1 件必要",
            )
        ]
    _, line_start, line_end = remaining[0]
    if block[line_start:line_end].rstrip("\n") != "  remaining: none":
        return block, [
            _issue(
                rel,
                whole,
                offset,
                "completion-remaining-field",
                f"{rel}: `完了` item 末尾には `  remaining: none` が 1 件必要",
            )
        ]
    return block[:line_start] + block[line_end:], []


def _parse_worklog_delta(fragment: Fragment) -> tuple[_WorklogDelta | None, list[Issue]]:
    rel, body = fragment.path, fragment.body
    issues: list[Issue] = []
    headers = list(re.finditer(r"^## (?P<title>[^\n]+)$", body, re.MULTILINE))
    if [match.group("title") for match in headers] != ["本文", "次の一手差分"]:
        return None, [Issue(rel, 1, "worklog-sections", f"{rel}: H2 は `本文` → `次の一手差分` の 2 節が必要")]
    prose_start = headers[0].end()
    if prose_start < len(body) and body[prose_start] == "\n":
        prose_start += 1
    prose = body[prose_start : headers[1].start()].strip("\n")
    if NEXT_ACTION_HEADING_RE.search(prose):
        issues.append(_issue(rel, body, prose_start, "worklog-prose-heading", f"{rel}: `本文` に reserved `次の一手` heading を置けない"))
    delta_start = headers[1].end()
    if delta_start < len(body) and body[delta_start] == "\n":
        delta_start += 1
    delta_body = body[delta_start:]
    sections = list(re.finditer(r"^### (?P<title>[^\n]+)$", delta_body, re.MULTILINE))
    allowed = ("carry", "完了", "更新", "新規", "見送り", "見送り追記")
    names = [section.group("title") for section in sections]
    if len(names) != len(set(names)) or any(name not in allowed for name in names):
        issues.append(Issue(rel, _line(body, delta_start), "worklog-actions", f"{rel}: action 節が重複または未知"))
    ranks = [allowed.index(name) for name in names if name in allowed]
    if ranks != sorted(ranks):
        issues.append(Issue(rel, _line(body, delta_start), "worklog-action-order", f"{rel}: action 節の順序が不正"))
    prefix_end = sections[0].start() if sections else len(delta_body)
    if delta_body[:prefix_end].strip():
        issues.append(_issue(rel, body, delta_start, "worklog-action-content", f"{rel}: action H3 より前に未解釈 content がある"))
    operations: list[_Operation] = []
    deferred_appends: list[_DeferredAppend] = []
    for index, section in enumerate(sections):
        name = section.group("title")
        start = section.end()
        if start < len(delta_body) and delta_body[start] == "\n":
            start += 1
        end = sections[index + 1].start() if index + 1 < len(sections) else len(delta_body)
        section_body = delta_body[start:end]
        absolute = delta_start + start
        if name == "見送り追記":
            nonblank = False
            cursor = 0
            for raw_line in section_body.splitlines(keepends=True):
                line = raw_line.rstrip("\n")
                if not line.strip():
                    cursor += len(raw_line)
                    continue
                nonblank = True
                match = re.fullmatch(
                    r"- (?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\])"
                    r"(?P<suffix> (?=[^\n]*\S)[^\n]+)",
                    line,
                )
                if match is None:
                    issues.append(_issue(
                        rel,
                        body,
                        absolute + cursor,
                        "deferred-append-shape",
                        f"{rel}: 見送り追記は 1 行の `- [T-NNN] <suffix>` に限る",
                    ))
                else:
                    deferred_appends.append(_DeferredAppend(match.group("id"), match.group("suffix")))
                cursor += len(raw_line)
            if not nonblank:
                issues.append(_issue(
                    rel,
                    body,
                    absolute,
                    "deferred-append-empty",
                    f"{rel}: 見送り追記には item が 1 件以上必要",
                ))
            continue
        if name == "見送り":
            categories = list(H4_RE.finditer(section_body))
            if not categories:
                issues.append(_issue(rel, body, absolute, "defer-category", f"{rel}: 見送りには既存 H3 名の H4 が必要"))
            issues.extend(_unconsumed_prefix(
                rel,
                body,
                section_body,
                absolute,
                [category.start() for category in categories],
                "worklog-action-content",
                f"{rel}: 見送り category より前に未解釈 content がある",
            ))
            for cat_index, category in enumerate(categories):
                cat_start = category.end()
                if cat_start < len(section_body) and section_body[cat_start] == "\n":
                    cat_start += 1
                cat_end = categories[cat_index + 1].start() if cat_index + 1 < len(categories) else len(section_body)
                category_body = section_body[cat_start:cat_end]
                category_items = _split_top_items(category_body, absolute + cat_start)
                issues.extend(_unconsumed_prefix(
                    rel,
                    body,
                    category_body,
                    absolute + cat_start,
                    [item_offset - (absolute + cat_start) for _, item_offset in category_items],
                    "worklog-action-content",
                    f"{rel}: 見送り item より前に未解釈 content がある",
                ))
                for block, item_offset in category_items:
                    if not _item_continuations_are_indented(block):
                        issues.append(_issue(rel, body, item_offset, "item-continuation", f"{rel}: item 継続行は 2 spaces indent が必要"))
                    match = TASK_HEAD_RE.match(block)
                    if match is None:
                        issues.append(_issue(rel, body, item_offset, "task-id", f"{rel}: 見送り対象 ID が不正"))
                        continue
                    output, digest, base_issues = _strip_base(rel, body, block, item_offset)
                    issues.extend(base_issues)
                    if "理由:" not in output and "理由：" not in output:
                        issues.append(_issue(rel, body, item_offset, "defer-reason", f"{rel}: 見送りには `理由:` が必要"))
                    operations.append(_Operation("見送り", match.group("id"), output, digest, category.group("title")))
            continue
        section_items = _split_top_items(section_body, absolute)
        issues.extend(_unconsumed_prefix(
            rel,
            body,
            section_body,
            absolute,
            [item_offset - absolute for _, item_offset in section_items],
            "worklog-action-content",
            f"{rel}: {name} item より前に未解釈 content がある",
        ))
        for block, item_offset in section_items:
            if not _item_continuations_are_indented(block):
                issues.append(_issue(rel, body, item_offset, "item-continuation", f"{rel}: item 継続行は 2 spaces indent が必要"))
            if name == "新規":
                match = re.match(r"^- \{\{T:(?P<slug>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)\}\}(?=$|[ \t])", block)
                if match is None:
                    issues.append(_issue(rel, body, item_offset, "new-task", f"{rel}: 新規 T は item 先頭の placeholder で定義する"))
                    continue
                operations.append(_Operation("新規", None, block, None, slug=match.group("slug")))
                continue
            match = TASK_HEAD_RE.match(block)
            if match is None:
                issues.append(_issue(rel, body, item_offset, "task-id", f"{rel}: {name} 対象 ID が不正"))
                continue
            if name == "carry":
                if block != f"- {match.group('id')}\n":
                    issues.append(_issue(rel, body, item_offset, "carry-shape", f"{rel}: carry は ID だけを列挙する"))
                operations.append(_Operation("carry", match.group("id"), block, None))
                continue
            completion_issues: list[Issue] = []
            output = block
            if name == "完了":
                output, completion_issues = _strip_completion_remaining(rel, body, output, item_offset)
                issues.extend(completion_issues)
            output, digest, base_issues = _strip_base(rel, body, output, item_offset)
            issues.extend(base_issues)
            if name == "完了" and re.search(r"残件(?:[はが:]|：|[ \t])*あり|一部完了", output):
                issues.append(_issue(rel, body, item_offset, "completion-remaining", f"{rel}: 残件ありの item を `完了` にできない"))
            operations.append(_Operation(name, match.group("id"), output, digest))
    return _WorklogDelta(prose, tuple(operations), tuple(deferred_appends)), issues


def _decision_symbols(fragment: Fragment) -> tuple[list[Symbol], list[Issue]]:
    symbols: list[Symbol] = []
    issues: list[Issue] = []
    headings = list(re.finditer(r"^## \{\{D:(?P<slug>[^}\n]+)\}\}\. (?P<title>[^\n]+)$", fragment.body, re.MULTILINE))
    all_h2 = list(re.finditer(r"^## .+$", fragment.body, re.MULTILINE))
    if not headings or len(headings) != len(all_h2):
        issues.append(Issue(fragment.path, 1, "decision-shape", f"{fragment.path}: 全 H2 は `## {{{{D:slug}}}}. title` 形式が必要"))
    for heading in headings:
        slug = heading.group("slug")
        if SLUG_RE.fullmatch(slug) is None:
            issues.append(_issue(fragment.path, fragment.body, heading.start("slug"), "slug", f"{fragment.path}: D slug が不正"))
            continue
        if re.search(r"\(\d{4}-\d{2}-\d{2}\)$", heading.group("title")):
            issues.append(_issue(fragment.path, fragment.body, heading.start("title"), "authored-date-use", f"{fragment.path}: canonical 日付は fold が付与する"))
        symbols.append(Symbol(fragment.wave, "D", slug, fragment.path, heading.start()))
    return symbols, issues


def _failure_symbols(fragment: Fragment) -> tuple[list[Symbol], list[Issue]]:
    symbols: list[Symbol] = []
    issues: list[Issue] = []
    h2s = list(re.finditer(r"^## (?P<title>[^\n]+)$", fragment.body, re.MULTILINE))
    names = [match.group("title") for match in h2s]
    canonical_names = ("新規", "再発", "supersede 追記")
    if not names or names != [name for name in canonical_names if name in names]:
        issues.append(Issue(fragment.path, 1, "failure-sections", f"{fragment.path}: H2 は `新規`、`再発`、`supersede 追記` の順で一意に置く"))
    new_region = ""
    new_offset = 0
    if "新規" in names:
        index = names.index("新規")
        start = h2s[index].end() + 1
        end = h2s[index + 1].start() if index + 1 < len(h2s) else len(fragment.body)
        new_region, new_offset = fragment.body[start:end], start
        headings = list(re.finditer(r"^### \{\{F:(?P<slug>[^}\n]+)\}\}\. (?P<title>[^\n]+)$", new_region, re.MULTILINE))
        all_h3 = list(re.finditer(r"^### .+$", new_region, re.MULTILINE))
        if not headings:
            issues.append(_issue(fragment.path, fragment.body, new_offset, "failure-new-empty", f"{fragment.path}: 使用した `新規` 節には有効な F heading が 1 件以上必要"))
        issues.extend(_unconsumed_prefix(
            fragment.path,
            fragment.body,
            new_region,
            new_offset,
            [heading.start() for heading in all_h3],
            "failure-unconsumed",
            f"{fragment.path}: `新規` 節に未消費 content がある",
        ))
        if len(headings) != len(all_h3):
            issues.append(_issue(fragment.path, fragment.body, new_offset, "failure-new-shape", f"{fragment.path}: 新規 F heading が不正"))
        for heading in headings:
            slug = heading.group("slug")
            if SLUG_RE.fullmatch(slug) is None:
                issues.append(_issue(fragment.path, fragment.body, new_offset + heading.start("slug"), "slug", f"{fragment.path}: F slug が不正"))
                continue
            entry_end = next((other.start() for other in all_h3 if other.start() > heading.start()), len(new_region))
            entry = new_region[heading.start():entry_end]
            for required in ("事象:", "根本原因:", "恒久対応:", "再発検知:"):
                if required not in entry:
                    issues.append(_issue(fragment.path, fragment.body, new_offset + heading.start(), "failure-required", f"{fragment.path}: 新規 F に {required} がない"))
            symbols.append(Symbol(fragment.wave, "F", slug, fragment.path, new_offset + heading.start()))
    if "再発" in names:
        index = names.index("再発")
        start = h2s[index].end() + 1
        end = h2s[index + 1].start() if index + 1 < len(h2s) else len(fragment.body)
        region = fragment.body[start:end]
        headings = list(re.finditer(r"^### F[1-9][0-9]*$", region, re.MULTILINE))
        all_h3 = list(re.finditer(r"^### .+$", region, re.MULTILINE))
        if not headings:
            issues.append(_issue(fragment.path, fragment.body, start, "failure-recurrence-empty", f"{fragment.path}: 使用した `再発` 節には有効な F heading が 1 件以上必要"))
        issues.extend(_unconsumed_prefix(
            fragment.path,
            fragment.body,
            region,
            start,
            [heading.start() for heading in all_h3],
            "failure-unconsumed",
            f"{fragment.path}: `再発` 節に未消費 content がある",
        ))
        if len(headings) != len(all_h3):
            issues.append(_issue(fragment.path, fragment.body, start, "failure-recurrence-shape", f"{fragment.path}: 再発 target が不正"))
        for visible, line_offset, _ in _visible_markdown_lines(
            region,
            collapse_html_comments=True,
        ):
            normalized = visible.translate(FAILURE_RECURRENCE_ZERO_WIDTH_TRANSLATION)
            if FAILURE_RECURRENCE_SUPERSEDE_MISUSE_RE.match(normalized):
                issues.append(_issue(
                    fragment.path,
                    fragment.body,
                    start + line_offset,
                    "failure-recurrence-supersede-misuse",
                    f"{fragment.path}: supersede 追記を `再発` 節へ置けない",
                ))
    if "supersede 追記" in names:
        index = names.index("supersede 追記")
        start = h2s[index].end() + 1
        end = h2s[index + 1].start() if index + 1 < len(h2s) else len(fragment.body)
        region = fragment.body[start:end]
        items: list[tuple[str, int]] = []
        offset = 0
        for line in region.split("\n"):
            if line.strip():
                items.append((line, start + offset))
            offset += len(line) + 1
        if not items:
            issues.append(_issue(
                fragment.path,
                fragment.body,
                start,
                "failure-supersede-empty",
                f"{fragment.path}: 使用した `supersede 追記` 節には item が 1 件以上必要",
            ))
        for line, line_offset in items:
            item = FAILURE_SUPERSEDE_ITEM_RE.fullmatch(line)
            if (
                item is None
                or not _valid_date(item.group("date"))
                or any(character in line for character in FAILURE_SUPERSEDE_FORBIDDEN_LINE_BREAKS)
            ):
                issues.append(_issue(
                    fragment.path,
                    fragment.body,
                    line_offset,
                    "failure-supersede-shape",
                    f"{fragment.path}: supersede 追記 item の shape が不正",
                ))
    return symbols, issues


def _worklog_symbols(fragment: Fragment, delta: _WorklogDelta | None) -> list[Symbol]:
    if delta is None:
        return []
    symbols: list[Symbol] = []
    cursor = 0
    for operation in delta.operations:
        if operation.kind != "新規" or operation.slug is None:
            continue
        needle = f"{{{{T:{operation.slug}}}}}"
        offset = fragment.body.find(needle, cursor)
        symbols.append(Symbol(fragment.wave, "T", operation.slug, fragment.path, max(offset, 0)))
        cursor = max(offset, 0) + len(needle)
    return symbols


def _fragment_from_file(repo: Path, ledger: str, path: Path) -> tuple[Fragment | None, list[Issue]]:
    rel = path.relative_to(repo).as_posix()
    raw, text, issues = _read_regular_utf8_lf(path, rel)
    if raw is None or text is None:
        return None, issues
    fields, body, fm_issues = _parse_frontmatter(rel, text)
    issues.extend(fm_issues)
    if fields is None:
        return None, issues
    allowed = {"schema", "ledger", "authored", "wave", "seq"}
    if ledger == "worklog":
        allowed.add("title")
    unknown = sorted(set(fields) - allowed)
    missing = sorted(allowed - set(fields))
    for key in unknown:
        issues.append(Issue(rel, 1, "frontmatter-unknown", f"{rel}: 未知 field {key!r}"))
    for key in missing:
        issues.append(Issue(rel, 1, "frontmatter-missing", f"{rel}: 必須 field {key!r} がない"))
    if fields.get("schema") != SCHEMA:
        issues.append(
            Issue(
                rel,
                1,
                "schema",
                f"{rel}: schema が {SCHEMA!r} でない (実際: {fields.get('schema')!r})",
            )
        )
    if fields.get("ledger") != ledger:
        issues.append(Issue(rel, 1, "ledger", f"{rel}: ledger と directory が不一致"))
    authored = fields.get("authored", "")
    wave = fields.get("wave", "")
    seq_text = fields.get("seq", "")
    if not _valid_date(authored):
        issues.append(Issue(rel, 1, "authored", f"{rel}: authored が実在日でない"))
    if WAVE_RE.fullmatch(wave) is None:
        issues.append(Issue(rel, 1, "wave", f"{rel}: wave が filename-safe 形式でない"))
    if SEQ_RE.fullmatch(seq_text) is None:
        issues.append(Issue(rel, 1, "seq", f"{rel}: seq は正の canonical decimal が必要"))
    expected = f"{authored}-{wave}-{seq_text}.md"
    if path.name != expected:
        issues.append(Issue(rel, 1, "filename", f"{rel}: frontmatter から再構成した filename {expected!r} と不一致"))
    if ledger == "failures" and "\r" in body:
        h2s = list(re.finditer(r"^## (?P<title>[^\n]+)$", body, re.MULTILINE))
        for index, h2 in enumerate(h2s):
            if h2.group("title") != "supersede 追記":
                continue
            start = h2.end() + 1
            end = h2s[index + 1].start() if index + 1 < len(h2s) else len(body)
            region = body[start:end]
            if "\r" in region:
                issues.append(_issue(
                    rel,
                    body,
                    start + region.index("\r"),
                    "failure-supersede-shape",
                    f"{rel}: supersede 追記 item の shape が不正",
                ))
                break
    if issues:
        return None, issues
    fragment = Fragment(rel, ledger, authored, wave, int(seq_text), fields.get("title"), body, raw, _sha256(raw))
    return fragment, issues


def _state_path(repo: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-path", STATE_NAME],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    path = Path(completed.stdout.strip())
    return path if path.is_absolute() else repo / path


def _has_git_admin_marker(repo: Path) -> bool:
    """repo root 自身が Git worktree 候補なら True。

    `.git` が壊れている場合も候補として扱い、後続 `_state_path()` を fail-closed
    に発火させる。マーカー自体がない非 Git fixture だけを除外する。
    """

    try:
        (repo / ".git").lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _discover(
    repo: Path,
    *,
    state_gate: bool,
    expected_transaction_id: str | None = None,
) -> tuple[list[Fragment], list[Symbol], dict[str, _WorklogDelta], list[Issue]]:
    repo = repo.resolve()
    spool = repo / "docs" / "spool"
    issues: list[Issue] = []
    fragments: list[Fragment] = []
    symbols: list[Symbol] = []
    deltas: dict[str, _WorklogDelta] = {}
    if state_gate and _has_git_admin_marker(repo):
        try:
            state_path = _state_path(repo)
        except (OSError, subprocess.SubprocessError) as exc:
            issues.append(Issue(".git", 1, "transaction-state", f"Git admin path を解決できない: {exc}"))
        else:
            if state_path.exists() or state_path.is_symlink():
                state_rel = f"git-admin/{STATE_NAME}"
                if expected_transaction_id is None:
                    issues.append(Issue(
                        state_rel,
                        1,
                        "transaction-active",
                        "fold transaction が active — "
                        f"state={state_path.absolute()}; "
                        "引数なし CLI で resume が必要。standalone の lock-aware finalize command は未実装",
                    ))
                    return fragments, symbols, deltas, sorted(issues)
                try:
                    if (
                        type(expected_transaction_id) is not str
                        or SHA_RE.fullmatch(expected_transaction_id) is None
                    ):
                        raise TransactionError("expected transaction ID が不正")
                    active = _state_plan(_load_state(state_path))
                    if active.transaction_id != expected_transaction_id:
                        raise TransactionError("active transaction ID が明示 expected ID と不一致")
                    target_states, gc_states = _validate_closure(repo, active)
                    if (
                        any(state != "after" for state in target_states.values())
                        or any(state != "missing" for state in gc_states.values())
                    ):
                        raise TransactionError("active transaction が complete shape でない")
                except (OSError, subprocess.SubprocessError, TransactionError) as exc:
                    issues.append(Issue(state_rel, 1, "transaction-state", str(exc)))
                    return fragments, symbols, deltas, sorted(issues)
    if not spool.exists() or spool.is_symlink() or not spool.is_dir():
        return fragments, symbols, deltas, [Issue("docs/spool", 1, "spool-layout", "docs/spool が実 directory として存在しない")]
    expected_root = {"README.md", "FOLDED.md", *LEDGERS}
    try:
        root_members = {member.name: member for member in spool.iterdir()}
    except OSError as exc:
        return fragments, symbols, deltas, [Issue("docs/spool", 1, "spool-layout", f"docs/spool を列挙できない: {exc}")]
    for name in sorted(expected_root - set(root_members)):
        issues.append(Issue(f"docs/spool/{name}", 1, "spool-layout", f"docs/spool/{name} が不在"))
    for name in sorted(set(root_members) - expected_root):
        issues.append(Issue(f"docs/spool/{name}", 1, "spool-member", f"docs/spool の余分な member {name!r}"))
    for filename in ("README.md", "FOLDED.md"):
        path = spool / filename
        if path.exists() or path.is_symlink():
            _, root_text, file_issues = _read_regular_utf8_lf(path, f"docs/spool/{filename}")
            issues.extend(file_issues)
            if filename == "FOLDED.md" and root_text is not None and not file_issues:
                try:
                    _receipt_records(root_text)
                except SpoolValidationError as exc:
                    issues.extend(exc.issues)
    for ledger in LEDGERS:
        directory = spool / ledger
        rel_dir = f"docs/spool/{ledger}"
        if not directory.exists() or directory.is_symlink() or not directory.is_dir():
            issues.append(Issue(rel_dir, 1, "spool-layout", f"{rel_dir} が実 directory でない"))
            continue
        members = sorted(directory.iterdir(), key=lambda member: member.name)
        names = {member.name for member in members}
        if "README.md" not in names:
            issues.append(Issue(f"{rel_dir}/README.md", 1, "spool-layout", f"{rel_dir}/README.md が不在"))
        for member in members:
            rel = member.relative_to(repo).as_posix()
            if member.name == "README.md":
                _, _, file_issues = _read_regular_utf8_lf(member, rel)
                issues.extend(file_issues)
                continue
            if FRAGMENT_FILE_RE.fullmatch(member.name) is None:
                issues.append(Issue(rel, 1, "fragment-name", f"{rel}: fragment filename が不正"))
                continue
            fragment, file_issues = _fragment_from_file(repo, ledger, member)
            issues.extend(file_issues)
            if fragment is None:
                continue
            fragments.append(fragment)
            if ledger == "worklog":
                delta, body_issues = _parse_worklog_delta(fragment)
                issues.extend(body_issues)
                if delta is not None:
                    deltas[fragment.path] = delta
                symbols.extend(_worklog_symbols(fragment, delta))
            elif ledger == "decisions":
                found, body_issues = _decision_symbols(fragment)
                symbols.extend(found)
                issues.extend(body_issues)
            else:
                found, body_issues = _failure_symbols(fragment)
                symbols.extend(found)
                issues.extend(body_issues)
    fragments.sort(key=lambda fragment: fragment.key)
    symbols.sort(key=lambda symbol: (
        symbol.wave,
        symbol.namespace,
        next((fragment.seq for fragment in fragments if fragment.path == symbol.fragment_path), 0),
        symbol.offset,
        symbol.fragment_path,
    ))
    seen: dict[tuple[str, str, str], Symbol] = {}
    for symbol in symbols:
        if symbol.key in seen:
            issues.append(Issue(symbol.fragment_path, 1, "symbol-duplicate", f"{symbol.wave}/{symbol.namespace}:{symbol.slug} が重複定義"))
        else:
            seen[symbol.key] = symbol
    for fragment in fragments:
        surfaces = [(fragment.body, 1)]
        if fragment.title is not None:
            surfaces.append((fragment.title, 1))
        for surface, line_number in surfaces:
            for placeholder in PLACEHOLDER_RE.finditer(surface):
                key = (fragment.wave, placeholder.group("namespace"), placeholder.group("slug"))
                if key not in seen:
                    issues.append(Issue(fragment.path, line_number, "symbol-undefined", f"{fragment.path}: 未定義参照 {placeholder.group(0)}"))
            masked = PLACEHOLDER_RE.sub("", surface)
            brace = min((position for position in (masked.find("{{"), masked.find("}}")) if position >= 0), default=-1)
            if brace >= 0:
                issues.append(Issue(fragment.path, line_number, "placeholder-malformed", f"{fragment.path}: malformed placeholder または置換残り"))
    approval_issue = _approval_guard_issue(
        repo,
        (fragment.raw for fragment in fragments if fragment.ledger == "decisions"),
    )
    if approval_issue is not None:
        code, message = approval_issue
        issues.append(
            Issue(
                "docs/spool/decisions",
                1,
                code,
                message,
            )
        )
    return fragments, symbols, deltas, sorted(set(issues))


def _approval_guard_issue(
    repo: Path,
    decision_payloads: Iterable[bytes],
) -> tuple[str, str] | None:
    payloads = tuple(decision_payloads)
    if not any(b"approved_blobs:" in payload for payload in payloads):
        return None
    try:
        previous_sys_path = sys.path[:]
        try:
            sys.path.insert(0, str(_IMPORT_ROOT))
            from orchestrator.publication.approval_guard import (
                ApprovalGuardError,
                require_resolved_approval_markers,
            )
        finally:
            sys.path[:] = previous_sys_path
    except ImportError as exc:
        return "approval-guard-unavailable", f"approval guard を import できない: {exc}"
    try:
        require_resolved_approval_markers(repo, payloads)
    except ApprovalGuardError as exc:
        return exc.code, str(exc)
    return None


def _plan_decision_payloads(repo: Path, plan: FoldPlan) -> tuple[bytes, ...]:
    payloads: list[bytes] = []
    for fragment in plan.fragments:
        if not fragment.path.startswith("docs/spool/decisions/"):
            continue
        parts = fragment.path.split("/")
        if (
            len(parts) != 4
            or parts[:3] != ["docs", "spool", "decisions"]
            or FRAGMENT_FILE_RE.fullmatch(parts[3]) is None
        ):
            continue
        path = repo.joinpath(*parts)
        if path.is_symlink() or not path.is_file():
            continue
        raw = path.read_bytes()
        if _sha256(raw) != fragment.content_sha256:
            continue
        payloads.append(raw)
    target = next(
        (target for target in plan.targets if target.path == "docs/decisions.md"),
        None,
    )
    if target is not None:
        # fragment receipt は provenance の照合対象であって、実際に canonical へ
        # 書く bytes の代替ではない。direct plan / durable state のどちらでも
        # after_bytes 自体を必ず marker gate に通す。
        payloads.append(target.after_bytes)
    return tuple(payloads)


def validate_spool_tree(
    repo: str | os.PathLike[str] | Path,
    *,
    expected_transaction_id: str | None = None,
) -> list[Issue]:
    """spool tree を read-only で検査し、決定的順序の Issue を返す。"""

    _, _, _, issues = _discover(
        Path(repo),
        state_gate=True,
        expected_transaction_id=expected_transaction_id,
    )
    return issues


def validate_spool_layout(repo: str | os.PathLike[str] | Path) -> list[Issue]:
    """active transaction の before/after に依存せず layout と receipt 構造を検査する。"""

    repo = Path(repo).resolve()
    spool = repo / "docs" / "spool"
    if not spool.exists() or spool.is_symlink() or not spool.is_dir():
        return [Issue("docs/spool", 1, "spool-layout", "docs/spool が実 directory として存在しない")]
    expected_root = {"README.md", "FOLDED.md", *LEDGERS}
    try:
        members = {member.name: member for member in spool.iterdir()}
    except OSError as exc:
        return [Issue("docs/spool", 1, "spool-layout", f"docs/spool を列挙できない: {exc}")]
    issues: list[Issue] = []
    for name in sorted(expected_root - set(members)):
        issues.append(Issue(f"docs/spool/{name}", 1, "spool-layout", f"docs/spool/{name} が不在"))
    for name in sorted(set(members) - expected_root):
        issues.append(Issue(f"docs/spool/{name}", 1, "spool-member", f"docs/spool の余分な member {name!r}"))
    for filename in ("README.md", "FOLDED.md"):
        path = spool / filename
        if not path.exists() and not path.is_symlink():
            continue
        _, text, file_issues = _read_regular_utf8_lf(path, f"docs/spool/{filename}")
        issues.extend(file_issues)
        if filename == "FOLDED.md" and text is not None and not file_issues:
            try:
                _receipt_records(text)
            except SpoolValidationError as exc:
                issues.extend(exc.issues)
    for ledger in LEDGERS:
        directory = spool / ledger
        rel = f"docs/spool/{ledger}"
        if not directory.exists() or directory.is_symlink() or not directory.is_dir():
            issues.append(Issue(rel, 1, "spool-layout", f"{rel} が実 directory でない"))
            continue
        readme = directory / "README.md"
        if not readme.exists() and not readme.is_symlink():
            issues.append(Issue(f"{rel}/README.md", 1, "spool-layout", f"{rel}/README.md が不在"))
        else:
            _, _, file_issues = _read_regular_utf8_lf(readme, f"{rel}/README.md")
            issues.extend(file_issues)
    return sorted(set(issues))


def _read_required(repo: Path, rel: str) -> bytes:
    path = repo / rel
    if path.is_symlink() or not path.is_file():
        raise SpoolValidationError([Issue(rel, 1, "canonical", f"{rel}: canonical regular file が不在")])
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SpoolValidationError([Issue(rel, 1, "canonical", f"{rel}: 読み取れない: {exc}")]) from exc


def _decode_canonical(rel: str, raw: bytes) -> str:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SpoolValidationError([Issue(rel, 1, "canonical-utf8", f"{rel}: UTF-8 でない")]) from exc
    if b"\r" in raw or (raw and not raw.endswith(b"\n")):
        raise SpoolValidationError([Issue(rel, 1, "canonical-bytes", f"{rel}: LF/末尾 newline 契約違反")])
    return text


def _load_base_digest_sources(repo: Path) -> tuple[str, dict[str, str]]:
    """base-digest 用に worklog と worklog archive だけをロードする。"""

    worklog_raw = _read_required(repo, "docs/worklog.md")
    worklog = _decode_canonical("docs/worklog.md", worklog_raw)
    archives: dict[str, str] = {}
    archive_dir = repo / "docs/archive"
    if archive_dir.is_symlink() or not archive_dir.is_dir():
        raise SpoolValidationError([Issue("docs/archive", 1, "archive", "archive directory が不正")])
    for path in sorted(archive_dir.glob("worklog-*.md"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            raise SpoolValidationError([Issue(path.relative_to(repo).as_posix(), 1, "archive", "archive worklog が regular file でない")])
        rel = path.relative_to(repo).as_posix()
        archives[path.name] = _decode_canonical(rel, _read_required(repo, rel))
    return worklog, archives


def _entry_active_items(text: str, heading: re.Match[str], end: int, rel: str) -> list[_TaskItem]:
    body = text[heading.end():end]
    headings = list(NEXT_ACTION_HEADING_RE.finditer(body))
    if len(headings) != 1:
        raise SpoolValidationError([Issue(rel, _line(text, heading.end()), "next-action", "entry の `次の一手` が一意でない")])
    start = headings[0].end()
    if start < len(body) and body[start] == "\n":
        start += 1
    section = body[start:]
    next_heading = re.search(r"^#{2,3} ", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    items: list[_TaskItem] = []
    seen: set[str] = set()
    for block, _ in _split_top_items(section):
        match = TASK_HEAD_RE.match(block)
        if match is None:
            raise SpoolValidationError([Issue(rel, 1, "next-action-id", "次の一手に不正 ID item がある")])
        task_id = match.group("id")
        if task_id in seen:
            raise SpoolValidationError([Issue(rel, 1, "next-action-duplicate", f"次の一手で {task_id} が重複")])
        seen.add(task_id)
        items.append(_TaskItem(task_id, block))
    return items


def _global_ordinal_entries(
    worklog: str,
    archives: Mapping[str, str] | None = None,
) -> dict[int, tuple[str, str, re.Match[str], int]]:
    """見出し日付で global 世代だけを抽出し、境界 signature も検査する。"""

    parsed_boundary = _parse_iso_date(GLOBAL_ORDINAL_START_DATE)
    if parsed_boundary is None:
        raise SpoolValidationError([
            Issue(
                "tools/spool_fold.py",
                1,
                "global-ordinal-boundary",
                "GLOBAL_ORDINAL_START_DATE が実在する ISO date でない",
            )
        ])
    boundary = parsed_boundary or _datetime.date.min
    sources = [("docs/worklog.md", worklog)]
    sources.extend(
        (f"docs/archive/{name}", text)
        for name, text in sorted((archives or {}).items())
    )
    entries_by_ordinal: dict[int, tuple[str, str, re.Match[str], int]] = {}
    boundary_ordinals: list[int] = []
    current_dates: list[_datetime.date] = []
    for rel, text in sources:
        entries = list(ARCHIVE_ENTRY_RE.finditer(text))
        for index, heading in enumerate(entries):
            date_text = heading.group("date")
            parsed_entry_date = _parse_iso_date(date_text)
            if parsed_entry_date is None:
                raise SpoolValidationError([
                    Issue(
                        rel,
                        _line(text, heading.start()),
                        "worklog-date",
                        f"worklog 見出し日付 {date_text!r} が実在日でない",
                    )
                ])
            # invalid 時の唯一の拒否は直上の worklog-date gate。gate の変異を
            # raw date 例外や比較 TypeError が代替しないよう安全な値へ畳む。
            entry_date = parsed_entry_date or _datetime.date.min
            if rel == "docs/worklog.md":
                current_dates.append(entry_date)
            if entry_date < boundary:
                continue
            ordinal_text = heading.group("ordinal")
            if ordinal_text is None:
                raise SpoolValidationError([
                    Issue(
                        rel,
                        _line(text, heading.start()),
                        "worklog-ordinal",
                        "global 世代の worklog entry に ordinal がない",
                    )
                ])
            ordinal = int(ordinal_text)
            if entry_date == boundary:
                boundary_ordinals.append(ordinal)
            if ordinal in entries_by_ordinal:
                raise SpoolValidationError([
                    Issue(
                        rel,
                        _line(text, heading.start()),
                        "worklog-ordinal",
                        f"global worklog ordinal ({ordinal}) が重複",
                    )
                ])
            end = entries[index + 1].start() if index + 1 < len(entries) else len(text)
            entries_by_ordinal[ordinal] = (rel, text, heading, end)

    if current_dates and any(entry_date < boundary for entry_date in current_dates):
        raise SpoolValidationError([
            Issue(
                "docs/worklog.md",
                1,
                "global-ordinal-boundary",
                "現行 worklog に global ordinal 境界日前の entry がある",
            )
        ])
    # Phase 1/2 からの実履歴 corpus だけは境界 entry の存在も signature に含める。
    # 短い合成 fixture には歴史全体を要求しない。欠番・最大 ordinal・日付/ordinal
    # の単調性は固定しない。
    full_history_corpus = "worklog-phase1-2.md" in (archives or {})
    if (full_history_corpus and not boundary_ordinals) or (
        boundary_ordinals and 1 not in boundary_ordinals
    ):
        raise SpoolValidationError([
            Issue(
                "docs/archive",
                1,
                "global-ordinal-boundary",
                f"global ordinal 境界日 {GLOBAL_ORDINAL_START_DATE} の系列が (1) から始まらない",
            )
        ])
    return entries_by_ordinal


def _extract_latest_active(worklog: str, archives: Mapping[str, str] | None = None) -> tuple[int, list[_TaskItem]]:
    entries_by_ordinal = _global_ordinal_entries(worklog, archives)
    current_entries = list(ARCHIVE_ENTRY_RE.finditer(worklog))
    latest_ordinal = (
        int(current_entries[-1].group("ordinal"))
        if current_entries and current_entries[-1].group("ordinal") is not None
        else None
    )
    if latest_ordinal is None:
        raise SpoolValidationError([Issue("docs/worklog.md", 1, "worklog-entry", "現行 worklog entry がない")])
    item_maps: dict[int, dict[str, _TaskItem]] = {}

    def items_for(ordinal: int) -> dict[str, _TaskItem]:
        if ordinal not in item_maps:
            try:
                rel, text, heading, end = entries_by_ordinal[ordinal]
            except KeyError as exc:
                raise SpoolValidationError([Issue("docs/worklog.md", 1, "carry-reference", f"参照先 entry ({ordinal}) がない")]) from exc
            item_maps[ordinal] = {
                item.task_id: item
                for item in _entry_active_items(text, heading, end, rel)
            }
        return item_maps[ordinal]
    carry_re = re.compile(
        r"^- (?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]) "
        r"(?:変わらず \(\((?P<legacy_ordinal>[1-9][0-9]*)\) 参照\)"
        r"|\((?P<compact_ordinal>[1-9][0-9]*)\))\n"
    )

    def substantive_digest(task_id: str, ordinal: int, trail: frozenset[int]) -> str:
        current_ordinal = ordinal
        visited = set(trail)
        while True:
            if current_ordinal in visited:
                raise SpoolValidationError([Issue("docs/worklog.md", 1, "carry-cycle", f"{task_id} の carry 参照が循環")])
            item = items_for(current_ordinal).get(task_id)
            if item is None:
                raise SpoolValidationError([Issue("docs/worklog.md", 1, "carry-reference", f"{task_id} の参照先 entry ({current_ordinal}) に item がない")])
            carry = carry_re.fullmatch(item.block)
            if carry is None:
                return _task_item_digest(item.block)
            legacy_ordinal = carry.group("legacy_ordinal")
            compact_ordinal = carry.group("compact_ordinal")
            # 将来の regex 改変に対する構造 guard であり、現 regex では到達しない。
            if (legacy_ordinal is None) == (compact_ordinal is None):
                raise SpoolValidationError([
                    Issue(
                        "docs/worklog.md",
                        1,
                        "carry-reference",
                        f"{task_id} の carry 参照 ordinal を一意に抽出できない",
                    )
                ])
            referenced = int(
                legacy_ordinal if legacy_ordinal is not None else compact_ordinal
            )
            if referenced >= current_ordinal:
                raise SpoolValidationError([Issue("docs/worklog.md", 1, "carry-reference", f"{task_id} の carry 参照が過去 entry を指さない")])
            visited.add(current_ordinal)
            current_ordinal = referenced

    latest_items = list(items_for(latest_ordinal).values())
    return latest_ordinal, [
        _TaskItem(item.task_id, item.block, substantive_digest(item.task_id, latest_ordinal, frozenset()))
        for item in latest_items
    ]


def _resolve_base_digest(repo: Path, task_id: str) -> str:
    worklog, archives = _load_base_digest_sources(repo)
    _, active = _extract_latest_active(worklog, archives)
    item = next((item for item in active if item.task_id == task_id), None)
    if item is None:
        raise SpoolValidationError([
            Issue(
                "docs/worklog.md",
                1,
                "base-digest-not-active",
                f"{task_id}: 現行 active item に存在しない",
            )
        ])
    if item.substantive_digest is None:
        raise SpoolValidationError([
            Issue(
                "docs/worklog.md",
                1,
                "base-digest-unresolved",
                f"{task_id}: substantive digest を解決できない",
            )
        ])
    return item.substantive_digest


def _deferred_region(phase: str) -> tuple[int, int, dict[str, tuple[int, int]]]:
    ledgers = list(DEFERRED_HEADING_RE.finditer(phase))
    completions = list(COMPLETION_HEADING_RE.finditer(phase))
    if len(ledgers) != 1 or len(completions) != 1 or completions[0].start() <= ledgers[0].end():
        raise SpoolValidationError([Issue("docs/phase3.md", 1, "deferred-ledger", "見送り台帳/裁定・完了記録を一意抽出できない")])
    start, end = ledgers[0].end(), completions[0].start()
    headings = list(H3_RE.finditer(phase, start, end))
    regions: dict[str, tuple[int, int]] = {}
    for index, heading in enumerate(headings):
        title = heading.group("title")
        if title in regions:
            raise SpoolValidationError([Issue("docs/phase3.md", _line(phase, heading.start()), "deferred-category", f"見送り H3 {title!r} が重複")])
        region_end = headings[index + 1].start() if index + 1 < len(headings) else end
        regions[title] = (heading.end(), region_end)
    return start, end, regions


def _max_task_number(worklog: str, archives: Mapping[str, str], phase: str) -> int:
    rotations = list(re.finditer(r"^## ローテーション[^\n]*$", worklog, re.MULTILINE))
    if len(rotations) != 1:
        raise SpoolValidationError([Issue("docs/worklog.md", 1, "rotation", "`## ローテーション` が一意でない")])
    deferred_start, deferred_end, _ = _deferred_region(phase)
    texts = [worklog[rotations[0].end():], phase[deferred_start:deferred_end], *archives.values()]
    numbers = [int(match.group(0)[3:-1]) for text in texts for match in TASK_RE.finditer(text)]
    return max(numbers, default=0)


def _format_task(number: int) -> str:
    return f"[T-{number:03d}]" if number < 1000 else f"[T-{number}]"


def _receipt_records(text: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    v2_seen = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("- "):
            continue
        if not line.startswith("- {"):
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED receipt の bullet が JSON object でない")])
        try:
            record = json.loads(line[2:])
        except (json.JSONDecodeError, TypeError) as exc:
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED receipt JSON が不正")]) from exc
        if not isinstance(record, dict):
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED receipt が object でない")])
        fields = frozenset(record)
        if fields == RECEIPT_V2_FIELDS:
            v2_seen = True
        elif fields != LEGACY_RECEIPT_FIELDS or v2_seen:
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED receipt の field 集合が不正")])
        allocations = record["allocations"]
        authored = record["authored"]
        content_sha = record["content_sha256"]
        seq = record["seq"]
        wave = record["wave"]
        base = record.get("base")
        tested_tip = record.get("tested_tip")
        wave_ref = record.get("wave_ref")
        if (
            not isinstance(authored, str)
            or not _valid_date(authored)
            or not isinstance(wave, str)
            or WAVE_RE.fullmatch(wave) is None
            or type(seq) is not int
            or seq <= 0
            or not isinstance(content_sha, str)
            or SHA_RE.fullmatch(content_sha) is None
            or not isinstance(allocations, dict)
            or (
                fields == RECEIPT_V2_FIELDS
                and (
                    type(base) is not str
                    or OID_RE.fullmatch(base) is None
                    or type(tested_tip) is not str
                    or OID_RE.fullmatch(tested_tip) is None
                    or type(wave_ref) is not str
                    or REF_RE.fullmatch(wave_ref) is None
                )
            )
        ):
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED receipt の値型/正規形が不正")])
        for key, value in allocations.items():
            namespace = key.split(":", 1)[0] if isinstance(key, str) and ":" in key else ""
            if (
                not isinstance(key, str)
                or re.fullmatch(r"[TDF]:[a-z][a-z0-9]*(?:-[a-z0-9]+)*", key) is None
                or not isinstance(value, str)
                or (
                    (namespace == "T" and TASK_RE.fullmatch(value) is None)
                    or (namespace == "D" and re.fullmatch(r"D[1-9][0-9]*", value) is None)
                    or (namespace == "F" and re.fullmatch(r"F[1-9][0-9]*", value) is None)
                )
            ):
                raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), line_number, "receipt", "FOLDED allocation が不正")])
        records.append(record)
    return records


def _replace_placeholders(text: str, wave: str, allocations: Mapping[tuple[str, str, str], str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = (wave, match.group("namespace"), match.group("slug"))
        if key not in allocations:
            raise SpoolValidationError([Issue("docs/spool", 1, "symbol-undefined", f"未定義 symbol {key}")])
        return allocations[key]

    rendered = PLACEHOLDER_RE.sub(replace, text)
    if "{{" in rendered or "}}" in rendered:
        raise SpoolValidationError([Issue("docs/spool", 1, "placeholder-remains", "置換後に placeholder delimiter が残った")])
    return rendered


def _append_bytes(existing: bytes, addition: str) -> bytes:
    encoded = addition.strip("\n").encode("utf-8") + b"\n"
    if not existing:
        return encoded
    return existing + (b"\n" if existing.endswith(b"\n") else b"\n\n") + encoded


def _assert_active_conservation(
    input_active_ids: set[str],
    completed_ids: set[str],
    deferred_ids: set[str],
    new_ids: set[str],
    output_items: Sequence[_TaskItem],
) -> None:
    """fold 前後の active 集合保存則を、render 結果そのものに対して検査する。"""

    expected = (input_active_ids - completed_ids - deferred_ids) | new_ids
    actual = {item.task_id for item in output_items}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise SpoolValidationError([
            Issue(
                "docs/spool/worklog",
                1,
                "transition-conservation",
                "active 集合の保存則違反: "
                f"missing={missing}, extra={extra}",
            )
        ])


def _render_next_actions(
    active: Sequence[_TaskItem],
    operations: Sequence[_Operation],
    prior_ordinal: int,
    allocations: Mapping[tuple[str, str, str], str],
    wave: str,
) -> tuple[str, list[_TaskItem], list[str], dict[str, list[str]]]:
    action_by_id: dict[str, _Operation] = {}
    completions: list[str] = []
    deferred: dict[str, list[str]] = {}
    new_ops: list[_Operation] = []
    for operation in operations:
        if operation.kind == "新規":
            new_ops.append(operation)
            continue
        assert operation.task_id is not None
        if operation.task_id in action_by_id:
            raise SpoolValidationError([Issue("docs/spool/worklog", 1, "transition-duplicate", f"{operation.task_id} が複数操作に現れる")])
        action_by_id[operation.task_id] = operation
    active_by_id = {item.task_id: item for item in active}
    extra = sorted(set(action_by_id) - set(active_by_id))
    if extra:
        raise SpoolValidationError([Issue("docs/spool/worklog", 1, "transition-target", f"active でない操作対象: {', '.join(extra)}")])
    rendered_items: list[_TaskItem] = []
    for item in active:
        operation = action_by_id.get(item.task_id)
        rendered_output = (
            _replace_placeholders(operation.output_block, wave, allocations)
            if operation is not None
            else None
        )
        if operation is not None and operation.kind in {"完了", "更新", "見送り"}:
            expected_base = item.substantive_digest or _task_item_digest(item.block)
            if operation.base != expected_base:
                raise SpoolValidationError([Issue("docs/spool/worklog", 1, "base-mismatch", f"{item.task_id} の base digest が現本文と不一致")])
        if operation is None or operation.kind == "carry":
            block = f"- {item.task_id} ({prior_ordinal})\n"
            substantive = item.substantive_digest or _task_item_digest(item.block)
            rendered_items.append(_TaskItem(item.task_id, block, substantive))
        elif operation.kind == "更新":
            assert rendered_output is not None
            rendered_items.append(_TaskItem(item.task_id, rendered_output, _task_item_digest(rendered_output)))
        elif operation.kind == "完了":
            assert rendered_output is not None
            completions.append(rendered_output)
        elif operation.kind == "見送り":
            assert operation.category is not None
            assert rendered_output is not None
            deferred.setdefault(operation.category, []).append(rendered_output)
        else:
            raise SpoolValidationError([Issue("docs/spool/worklog", 1, "transition-kind", f"未知操作 {operation.kind}")])
    new_ids: set[str] = set()
    for operation in new_ops:
        assert operation.slug is not None
        block = _replace_placeholders(operation.output_block, wave, allocations)
        match = TASK_HEAD_RE.match(block)
        if match is None:
            raise SpoolValidationError([Issue("docs/spool/worklog", 1, "new-render", "新規 T の採番結果が item 先頭にない")])
        task_id = match.group("id")
        new_ids.add(task_id)
        rendered_items.append(_TaskItem(task_id, block, _task_item_digest(block)))
    _assert_active_conservation(
        set(active_by_id),
        {task_id for task_id, operation in action_by_id.items() if operation.kind == "完了"},
        {task_id for task_id, operation in action_by_id.items() if operation.kind == "見送り"},
        new_ids,
        rendered_items,
    )
    section = (
        "### 次の一手 — 「(番号)」だけの項は、その番号のエントリ "
        "(archive 含む) から変わらない持ち越し\n\n"
        + "".join(item.block for item in rendered_items)
    )
    return section, rendered_items, completions, deferred


def _render_worklog_entry(
    fragment: Fragment,
    delta: _WorklogDelta,
    fold_date: str,
    ordinal: int,
    prior_ordinal: int,
    active: Sequence[_TaskItem],
    allocations: Mapping[tuple[str, str, str], str],
) -> tuple[str, list[_TaskItem], dict[str, list[str]]]:
    section, next_active, completions, deferred = _render_next_actions(
        active, delta.operations, prior_ordinal, allocations, fragment.wave
    )
    title = _replace_placeholders(fragment.title or "", fragment.wave, allocations)
    prose = _replace_placeholders(delta.prose, fragment.wave, allocations).strip("\n")
    parts = [f"## {fold_date} ({ordinal}) — {title}"]
    if prose:
        parts.append(prose)
    parts.extend(block.rstrip("\n") for block in completions)
    parts.append(section.rstrip("\n"))
    return "\n\n".join(parts) + "\n", next_active, deferred


def _insert_deferred(phase: str, additions: Mapping[str, Sequence[str]]) -> str:
    if not additions:
        return phase
    _, _, regions = _deferred_region(phase)
    insertions: list[tuple[int, str]] = []
    for category in sorted(additions):
        if category not in regions:
            raise SpoolValidationError([Issue("docs/phase3.md", 1, "deferred-category", f"見送り先 H3 {category!r} が存在しない")])
        _, end = regions[category]
        payload = "".join(additions[category]).strip("\n") + "\n\n"
        insertions.append((end, payload))
    rendered = phase
    for offset, payload in sorted(insertions, reverse=True):
        prefix = "" if offset == 0 or rendered[offset - 1] == "\n" else "\n"
        rendered = rendered[:offset] + prefix + payload + rendered[offset:]
    return rendered


def _deferred_items(phase: str) -> dict[str, list[tuple[int, int, int]]]:
    """可視な見送り top-level item を ID -> (先頭, 行末, block末尾) で索引する。"""

    visible_lines = _visible_markdown_lines(phase)
    ledgers = [
        (offset, offset + len(visible))
        for visible, offset, _ in visible_lines
        if DEFERRED_HEADING_RE.fullmatch(visible) is not None
    ]
    completions = [
        offset
        for visible, offset, _ in visible_lines
        if COMPLETION_HEADING_RE.fullmatch(visible) is not None
    ]
    if len(ledgers) != 1 or len(completions) != 1 or completions[0] <= ledgers[0][1]:
        raise SpoolValidationError([
            Issue(
                "docs/phase3.md",
                1,
                "deferred-ledger",
                "見送り台帳/裁定・完了記録を一意抽出できない",
            )
        ])
    region_start, region_end = ledgers[0][1], completions[0]
    items: dict[str, list[tuple[int, int, int]]] = {}
    found: list[tuple[str, int, int]] = []
    boundaries: list[int] = []
    region = phase[region_start:region_end]
    for visible, line_offset, _ in _visible_markdown_lines(region):
        absolute = region_start + line_offset
        if H3_RE.fullmatch(visible) is not None:
            boundaries.append(absolute)
            continue
        item = TOP_LEVEL_ITEM_RE.fullmatch(visible)
        if item is None:
            continue
        boundaries.append(absolute)
        task = re.match(
            r"^(?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\])(?=$|[ \t])",
            item.group("text"),
        )
        if task is None:
            continue
        line_end = phase.find("\n", absolute, region_end)
        if line_end < 0:
            line_end = region_end
        found.append((task.group("id"), absolute, line_end))
    for task_id, item_start, line_end in found:
        block_end = next((boundary for boundary in boundaries if boundary > item_start), region_end)
        items.setdefault(task_id, []).append((item_start, line_end, block_end))
    return items


def _assert_deferred_ids_unique(rendered_phase: str) -> None:
    issues = [
        Issue(
            "docs/phase3.md",
            _line(rendered_phase, offset),
            "deferred-duplicate",
            f"見送り台帳の ID {task_id} が重複",
        )
        for task_id, items in _deferred_items(rendered_phase).items()
        for offset, _line_end, _block_end in items[1:]
    ]
    if issues:
        raise SpoolValidationError(issues)


def _insert_deferred_appends(phase: str, appends: Sequence[_DeferredAppend]) -> str:
    if not appends:
        return phase
    items = _deferred_items(phase)
    grouped: dict[str, list[str]] = {}
    positions: dict[str, int] = {}
    seen_suffixes: dict[str, list[str]] = {}
    for append in appends:
        targets = items.get(append.task_id, [])
        if not targets:
            raise SpoolValidationError([
                Issue(
                    "docs/phase3.md",
                    1,
                    "deferred-append-missing",
                    f"見送り追記 target {append.task_id} が不存在",
                )
            ])
        if len(targets) != 1:
            raise SpoolValidationError([
                Issue(
                    "docs/phase3.md",
                    _line(phase, targets[1][0]),
                    "deferred-append-duplicate",
                    f"見送り追記 target {append.task_id} が重複",
                )
            ])
        item_start, line_end, _ = targets[0]
        head_line = phase[item_start:line_end]
        seen = seen_suffixes.setdefault(append.task_id, [])
        if head_line.rstrip("\n").endswith(append.suffix) or append.suffix in seen:
            raise SpoolValidationError([
                Issue(
                    "docs/phase3.md",
                    _line(phase, item_start),
                    "deferred-append-duplicate-suffix",
                    f"見送り追記 target {append.task_id} に同一 suffix が存在",
                )
            ])
        grouped.setdefault(append.task_id, []).append(append.suffix)
        positions[append.task_id] = line_end
        seen.append(append.suffix)
    rendered = phase
    for task_id in sorted(grouped, key=lambda value: positions[value], reverse=True):
        offset = positions[task_id]
        payload = "".join(grouped[task_id])
        rendered = rendered[:offset] + payload + rendered[offset:]
    return rendered


def _render_decisions(fragment: Fragment, fold_date: str, allocations: Mapping[tuple[str, str, str], str]) -> str:
    rendered = _replace_placeholders(fragment.body, fragment.wave, allocations)
    lines: list[str] = []
    for line in rendered.splitlines():
        if re.match(r"^## D[1-9][0-9]*\. ", line):
            line += f" ({fold_date})"
        lines.append(line)
    return "\n".join(lines).strip("\n") + "\n"


def _failure_parts(
    fragment: Fragment,
    allocations: Mapping[tuple[str, str, str], str],
) -> tuple[list[str], list[tuple[int, str]], list[_FailureSupersede]]:
    body = _replace_placeholders(fragment.body, fragment.wave, allocations)
    h2s = list(re.finditer(r"^## (?P<title>新規|再発|supersede 追記)$", body, re.MULTILINE))
    new_entries: list[str] = []
    recurrences: list[tuple[int, str]] = []
    supersedes: list[_FailureSupersede] = []
    for index, h2 in enumerate(h2s):
        start = h2.end() + 1
        end = h2s[index + 1].start() if index + 1 < len(h2s) else len(body)
        region = body[start:end]
        if h2.group("title") == "supersede 追記":
            for line in region.split("\n"):
                if not line.strip():
                    continue
                item = FAILURE_SUPERSEDE_ITEM_RE.fullmatch(line)
                if item is None or any(
                    character in line
                    for character in FAILURE_SUPERSEDE_FORBIDDEN_LINE_BREAKS
                ):
                    raise SpoolValidationError([
                        Issue(fragment.path, 1, "failure-supersede-shape", "supersede 追記 item の shape が不正")
                    ])
                supersedes.append(_FailureSupersede(
                    int(item.group("number")),
                    item.group("body"),
                ))
            continue
        h3s = list(re.finditer(r"^### (?P<title>[^\n]+)$", region, re.MULTILINE))
        for h3_index, h3 in enumerate(h3s):
            entry_end = h3s[h3_index + 1].start() if h3_index + 1 < len(h3s) else len(region)
            entry = region[h3.start():entry_end].strip("\n") + "\n"
            if h2.group("title") == "新規":
                new_entries.append(entry)
            else:
                target = re.fullmatch(r"F(?P<number>[1-9][0-9]*)", h3.group("title"))
                if target is None:
                    raise SpoolValidationError([Issue(fragment.path, 1, "failure-recurrence", "再発 target が不正")])
                payload = entry[h3.end() - h3.start():].strip("\n") + "\n"
                recurrences.append((int(target.group("number")), payload))
    return new_entries, recurrences, supersedes


def _insert_failure_recurrences(failures: str, recurrences: Sequence[tuple[int, str]]) -> str:
    if not recurrences:
        return failures
    headings = list(FAILURE_ID_RE.finditer(failures))
    positions: dict[int, int] = {}
    for index, heading in enumerate(headings):
        number = int(heading.group("number"))
        if number in positions:
            raise SpoolValidationError([Issue("docs/failures.md", _line(failures, heading.start()), "failure-duplicate", f"F{number} が重複")])
        positions[number] = headings[index + 1].start() if index + 1 < len(headings) else len(failures)
    grouped: dict[int, list[str]] = {}
    for number, payload in recurrences:
        if number not in positions:
            raise SpoolValidationError([Issue("docs/failures.md", 1, "failure-missing", f"再発 target F{number} が不存在")])
        grouped.setdefault(number, []).append(payload)
    rendered = failures
    for number in sorted(grouped, key=lambda value: positions[value], reverse=True):
        offset = positions[number]
        payload = "\n" + "\n".join(item.strip("\n") for item in grouped[number]) + "\n"
        rendered = rendered[:offset] + payload + rendered[offset:]
    return rendered


def _insert_failure_supersedes(
    failures: str,
    supersedes: Sequence[_FailureSupersede],
) -> str:
    if not supersedes:
        return failures
    headings = list(FAILURE_ID_RE.finditer(failures))
    positions: dict[int, int] = {}
    starts: dict[int, int] = {}
    for index, heading in enumerate(headings):
        number = int(heading.group("number"))
        if number in positions:
            raise SpoolValidationError([
                Issue(
                    "docs/failures.md",
                    _line(failures, heading.start()),
                    "failure-duplicate",
                    f"F{number} が重複",
                )
            ])
        starts[number] = heading.start()
        entry_end = headings[index + 1].start() if index + 1 < len(headings) else len(failures)
        entry = failures[heading.start():entry_end]
        nonempty_lines = list(re.finditer(r"^[^\n]*\S[^\n]*(?:\n|$)", entry, re.MULTILINE))
        positions[number] = heading.start() + nonempty_lines[-1].end()
    grouped: dict[int, list[str]] = {}
    seen: set[tuple[int, str]] = set()
    for supersede in supersedes:
        number = supersede.target_number
        if number not in positions:
            raise SpoolValidationError([
                Issue(
                    "docs/failures.md",
                    1,
                    "failure-supersede-missing",
                    f"supersede 追記 target F{number} が不存在",
                )
            ])
        rendered_line = "- " + supersede.line
        identity = (number, rendered_line)
        existing_lines = failures[starts[number]:positions[number]].split("\n")
        if rendered_line in existing_lines or identity in seen:
            raise SpoolValidationError([
                Issue(
                    "docs/failures.md",
                    _line(failures, starts[number]),
                    "failure-supersede-duplicate-line",
                    f"supersede 追記 target F{number} に同一行が存在",
                )
            ])
        grouped.setdefault(number, []).append(rendered_line)
        seen.add(identity)
    rendered = failures
    for number in sorted(grouped, key=lambda value: positions[value], reverse=True):
        offset = positions[number]
        payload = "\n".join(grouped[number]) + "\n"
        rendered = rendered[:offset] + payload + rendered[offset:]
    return rendered


def _assert_failure_topology(
    before_numbers: Sequence[int],
    rendered_failures: str,
    appended_numbers: Sequence[int],
    allocated_numbers: Sequence[int],
) -> None:
    expected = [*before_numbers, *appended_numbers]
    actual = [int(match.group("number")) for match in FAILURE_ID_RE.finditer(rendered_failures)]
    if (
        sorted(appended_numbers) != sorted(allocated_numbers)
        or len(expected) != len(set(expected))
        or len(actual) != len(set(actual))
        or actual != expected
    ):
        raise SpoolValidationError([
            Issue(
                "docs/failures.md",
                1,
                "failure-topology",
                f"描画後の F heading 列が不正: expected={expected}, actual={actual}",
            )
        ])


def _load_rotate_limit(repo: Path) -> int:
    source = repo / "tools" / "check_docs.py"
    if source.is_symlink() or not source.is_file():
        raise SpoolValidationError([Issue("tools/check_docs.py", 1, "rotate-limit", "WORKLOG_ROTATE_BYTES の単一出所を import できない")])
    name = f"_izanagi_check_docs_{_sha256(str(source).encode())[:12]}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise SpoolValidationError([Issue("tools/check_docs.py", 1, "rotate-limit", "check_docs import spec を作れない")])
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.modules[name] = module
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
        value = module.WORKLOG_ROTATE_BYTES
    except BaseException as exc:  # SystemExit / KeyboardInterrupt も fail-closed。
        raise SpoolValidationError([Issue("tools/check_docs.py", 1, "rotate-limit", f"WORKLOG_ROTATE_BYTES を import できない: {exc}")]) from exc
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    if type(value) is not int or value <= 0:
        raise SpoolValidationError([Issue("tools/check_docs.py", 1, "rotate-limit", "WORKLOG_ROTATE_BYTES が正の int でない")])
    return value


def _rotation_name(entries: Sequence[re.Match[str]]) -> str:
    first, last = entries[0], entries[-1]
    first_date = first.group("date")
    last_date = last.group("date")
    first_mmdd = first_date[5:].replace("-", "")
    last_mmdd = last_date[5:].replace("-", "")
    first_ord, last_ord = first.group("ordinal"), last.group("ordinal")
    if first_date == last_date:
        suffix = first_ord if first_ord == last_ord else f"{first_ord}-{last_ord}"
        return f"worklog-phase3-{first_mmdd}-{suffix}.md"
    return f"worklog-phase3-{first_mmdd}-{first_ord}-{last_mmdd}-{last_ord}.md"


def _rotate_worklog(
    repo: Path,
    original: bytes,
    projected: bytes,
    archive_readme: bytes,
    limit: int,
) -> tuple[bytes, str, bytes, bytes]:
    original_text = _decode_canonical("docs/worklog.md", original)
    projected_text = _decode_canonical("docs/worklog.md", projected)
    original_entries = list(WORKLOG_ENTRY_RE.finditer(original_text))
    projected_entries = list(WORKLOG_ENTRY_RE.finditer(projected_text))
    has_new_entries = len(projected_entries) > len(original_entries)
    if not has_new_entries:
        if len(original_entries) < 2:
            raise SpoolValidationError([Issue("docs/worklog.md", 1, "rotation-capacity", "閾値超過だが seed を残して移動できる過去 entry がない")])
        move_start = len(original_text[: original_entries[0].start()].encode("utf-8"))
        keep_start = len(original_text[: original_entries[-1].start()].encode("utf-8"))
        moved = original[move_start:keep_start]
        rotated = original[:move_start] + projected[keep_start:]
        moved_entries = original_entries[:-1]
    else:
        move_start = len(projected_text[: projected_entries[0].start()].encode("utf-8"))
        rotated = b""
        keep_start = 0
        moved_entries: list[re.Match[str]] = []
        for split in range(1, len(projected_entries)):
            keep_start = len(
                projected_text[: projected_entries[split].start()].encode("utf-8")
            )
            candidate = projected[:move_start] + projected[keep_start:]
            if len(candidate) <= limit:
                rotated = candidate
                moved_entries = projected_entries[:split]
                break
        if not moved_entries:
            raise SpoolValidationError([Issue("docs/worklog.md", 1, "rotation-capacity", "過去 entry を移動しても閾値を超える")])
        moved = projected[move_start:keep_start]
    if len(rotated) > limit:
        raise SpoolValidationError([Issue("docs/worklog.md", 1, "rotation-capacity", "過去 entry を移動しても閾値を超える")])
    name = _rotation_name(moved_entries)
    rel = f"docs/archive/{name}"
    if (repo / rel).exists() or (repo / rel).is_symlink():
        raise SpoolValidationError([Issue(rel, 1, "rotation-collision", f"rotation target {rel} が既に存在")])
    readme_text = _decode_canonical("docs/archive/README.md", archive_readme)
    section = re.search(r"^## 現在の収容物(?:[ \t].*)?$", readme_text, re.MULTILINE)
    if section is None:
        raise SpoolValidationError([Issue("docs/archive/README.md", 1, "archive-index", "現在の収容物節がない")])
    first = moved_entries[0]
    last = moved_entries[-1]
    range_text = f"{first.group('date')} ({first.group('ordinal')})"
    if len(moved_entries) > 1:
        range_text += f"〜{last.group('date')} ({last.group('ordinal')})"
    index_line = f"- `{name}` — worklog の {range_text} 分\n  ローテーションアーカイブ (fold による閾値超過対応)\n"
    next_section = re.search(r"^## ", readme_text[section.end():], re.MULTILINE)
    if next_section is None:
        updated_readme = _append_bytes(archive_readme, index_line)
    else:
        char_offset = section.end() + next_section.start()
        byte_offset = len(readme_text[:char_offset].encode("utf-8"))
        payload = index_line.strip("\n").encode("utf-8") + b"\n\n"
        updated_readme = archive_readme[:byte_offset] + payload + archive_readme[byte_offset:]
    return rotated, rel, moved, updated_readme


def _target(repo: Path, rel: str, after: bytes) -> TargetChange:
    path = repo / rel
    before_exists = path.exists() and not path.is_symlink() and path.is_file()
    before = path.read_bytes() if before_exists else b""
    return TargetChange(rel, _sha256(before), _sha256(after), before_exists, after)


def _closure_digest(files: Mapping[str, str], worklog_rotate_bytes: int) -> str:
    payload = {
        "files": dict(sorted(files.items())),
        "worklog_rotate_bytes": worklog_rotate_bytes,
    }
    return _sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _plan_transaction_id(
    fold_date: str,
    origin: FoldOrigin,
    input_closure_sha256: str,
    fragments: Sequence[FragmentReceipt],
    gc_paths: Sequence[str],
    projected_worklog_bytes: int,
    rotation_path: str | None,
    targets: Sequence[TargetChange],
) -> str:
    payload = {
        "fold_date": fold_date,
        "origin": _origin_dict(origin),
        "input_closure_sha256": input_closure_sha256,
        "fragments": [
            {
                "path": fragment.path,
                "authored": fragment.authored,
                "wave": fragment.wave,
                "seq": fragment.seq,
                "content_sha256": fragment.content_sha256,
                "allocations": [list(pair) for pair in fragment.allocations],
            }
            for fragment in fragments
        ],
        "gc_paths": list(gc_paths),
        "projected_worklog_bytes": projected_worklog_bytes,
        "rotation_path": rotation_path,
        "targets": [
            {
                "path": target.path,
                "before_exists": target.before_exists,
                "before_sha256": target.before_sha256,
                "after_sha256": target.after_sha256,
            }
            for target in targets
        ],
    }
    return _sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def plan_fold(
    repo: str | os.PathLike[str] | Path,
    *,
    fold_date: str | None = None,
    origin: FoldOrigin | None = None,
) -> FoldPlan:
    """副作用なしに FoldPlan を構築する。

    ``fold_date`` を含む入力が同じなら、壁時計や timezone に関係なく同じ
    canonical bytes と transaction ID を返す。省略時だけ現在の local date を既定値にする。
    """

    repo = Path(repo).resolve()
    origin = _observe_origin(repo, origin)
    fragments, symbols, deltas, issues = _discover(repo, state_gate=True)
    if issues:
        raise SpoolValidationError(issues)
    if fold_date is None:
        fold_date = _current_fold_date()
    if not isinstance(fold_date, str) or not _valid_date(fold_date):
        raise SpoolValidationError([Issue("fold_date", 1, "fold-date", "fold_date は実在する ISO date が必要")])
    if not fragments:
        worklog_path = repo / "docs/worklog.md"
        projected_worklog_bytes = len(worklog_path.read_bytes()) if worklog_path.is_file() else 0
        return FoldPlan(
            "noop", fold_date, "", origin, "", "applied",
            (), (), (), (), projected_worklog_bytes, None,
        )
    worklog_raw = _read_required(repo, "docs/worklog.md")
    decisions_raw = _read_required(repo, "docs/decisions.md")
    failures_raw = _read_required(repo, "docs/failures.md")
    phase_raw = _read_required(repo, "docs/phase3.md")
    archive_readme_raw = _read_required(repo, "docs/archive/README.md")
    receipt_raw = _read_required(repo, RECEIPT_REL.as_posix())
    spool_fold_raw = _read_required(repo, "tools/spool_fold.py")
    check_docs_raw = _read_required(repo, "tools/check_docs.py")
    worklog = _decode_canonical("docs/worklog.md", worklog_raw)
    decisions = _decode_canonical("docs/decisions.md", decisions_raw)
    failures = _decode_canonical("docs/failures.md", failures_raw)
    phase = _decode_canonical("docs/phase3.md", phase_raw)
    receipt = _decode_canonical(RECEIPT_REL.as_posix(), receipt_raw)
    archives: dict[str, str] = {}
    archive_raws: dict[str, bytes] = {}
    archive_dir = repo / "docs/archive"
    if archive_dir.is_symlink() or not archive_dir.is_dir():
        raise SpoolValidationError([Issue("docs/archive", 1, "archive", "archive directory が不正")])
    for path in sorted(archive_dir.glob("worklog-*.md"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            raise SpoolValidationError([Issue(path.relative_to(repo).as_posix(), 1, "archive", "archive worklog が regular file でない")])
        rel = path.relative_to(repo).as_posix()
        raw = path.read_bytes()
        archive_raws[rel] = raw
        archives[path.name] = _decode_canonical(rel, raw)

    limit = _load_rotate_limit(repo)
    closure_files = {
        "docs/worklog.md": _sha256(worklog_raw),
        "docs/decisions.md": _sha256(decisions_raw),
        "docs/failures.md": _sha256(failures_raw),
        "docs/phase3.md": _sha256(phase_raw),
        "docs/archive/README.md": _sha256(archive_readme_raw),
        RECEIPT_REL.as_posix(): _sha256(receipt_raw),
        "tools/spool_fold.py": _sha256(spool_fold_raw),
        "tools/check_docs.py": _sha256(check_docs_raw),
        **{rel: _sha256(raw) for rel, raw in archive_raws.items()},
        **{fragment.path: fragment.content_sha for fragment in fragments},
    }
    input_closure_sha256 = _closure_digest(closure_files, limit)
    records = _receipt_records(receipt)
    seen_content: set[object] = set()
    seen_identity: set[tuple[str, str, str]] = set()
    for index, record in enumerate(records, 1):
        content_sha = record["content_sha256"]
        if content_sha in seen_content:
            raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), index, "receipt-duplicate", f"receipt content-sha {content_sha} が重複")])
        seen_content.add(content_sha)
        wave = record.get("wave")
        allocations_record = record.get("allocations", {})
        if isinstance(wave, str) and isinstance(allocations_record, dict):
            for name in allocations_record:
                if isinstance(name, str) and ":" in name:
                    namespace, slug = name.split(":", 1)
                    identity = (wave, namespace, slug)
                    if identity in seen_identity:
                        raise SpoolValidationError([Issue(RECEIPT_REL.as_posix(), index, "receipt-duplicate", f"receipt identity {identity} が重複")])
                    seen_identity.add(identity)
    replay_issues: list[Issue] = []
    for fragment in fragments:
        if fragment.content_sha in seen_content:
            replay_issues.append(Issue(fragment.path, 1, "receipt-replay", f"{fragment.path}: 同一内容は fold 済み"))
    for symbol in symbols:
        if symbol.key in seen_identity:
            replay_issues.append(Issue(symbol.fragment_path, 1, "symbol-replay", f"{symbol.key} は fold 済み identity"))
    if replay_issues:
        raise SpoolValidationError(replay_issues)

    decision_numbers = [int(match.group("number")) for match in DECISION_ID_RE.finditer(decisions)]
    failure_numbers = [int(match.group("number")) for match in FAILURE_ID_RE.finditer(failures)]
    if len(decision_numbers) != len(set(decision_numbers)):
        raise SpoolValidationError([Issue("docs/decisions.md", 1, "decision-duplicate", "canonical D ID が重複")])
    if len(failure_numbers) != len(set(failure_numbers)):
        raise SpoolValidationError([Issue("docs/failures.md", 1, "failure-duplicate", "canonical F ID が重複")])
    next_numbers = {
        "T": _max_task_number(worklog, archives, phase) + 1,
        "D": max(decision_numbers, default=0) + 1,
        "F": max(failure_numbers, default=0) + 1,
    }
    allocations: dict[tuple[str, str, str], str] = {}
    for symbol in symbols:
        number = next_numbers[symbol.namespace]
        next_numbers[symbol.namespace] += 1
        if symbol.namespace == "T":
            allocated = _format_task(number)
        else:
            allocated = f"{symbol.namespace}{number}"
        allocations[symbol.key] = allocated

    prior_ordinal, active = _extract_latest_active(worklog, archives)
    max_ordinal = max(_global_ordinal_entries(worklog, archives), default=prior_ordinal)
    rendered_worklog = worklog_raw
    rendered_phase = phase
    ordinal = max_ordinal + 1
    worklog_fragments = [fragment for fragment in fragments if fragment.ledger == "worklog"]
    for fragment in worklog_fragments:
        delta = deltas[fragment.path]
        entry, active, deferred = _render_worklog_entry(fragment, delta, fold_date, ordinal, prior_ordinal, active, allocations)
        rendered_worklog = _append_bytes(rendered_worklog, entry)
        rendered_phase = _insert_deferred(rendered_phase, deferred)
        rendered_appends = tuple(
            _DeferredAppend(
                append.task_id,
                _replace_placeholders(append.suffix, fragment.wave, allocations),
            )
            for append in delta.deferred_appends
        )
        rendered_phase = _insert_deferred_appends(rendered_phase, rendered_appends)
        prior_ordinal = ordinal
        ordinal += 1

    _assert_deferred_ids_unique(rendered_phase)

    rendered_decisions = decisions_raw
    for fragment in (item for item in fragments if item.ledger == "decisions"):
        rendered_decisions = _append_bytes(rendered_decisions, _render_decisions(fragment, fold_date, allocations))

    rendered_failures_text = failures
    new_failure_entries: list[str] = []
    recurrence_entries: list[tuple[int, str]] = []
    supersede_entries: list[_FailureSupersede] = []
    for fragment in (item for item in fragments if item.ledger == "failures"):
        new_entries, recurrences, supersedes = _failure_parts(fragment, allocations)
        new_failure_entries.extend(new_entries)
        recurrence_entries.extend(recurrences)
        supersede_entries.extend(supersedes)
    rendered_failures_text = _insert_failure_recurrences(rendered_failures_text, recurrence_entries)
    rendered_failures_text = _insert_failure_supersedes(rendered_failures_text, supersede_entries)
    rendered_failures = rendered_failures_text.encode("utf-8")
    appended_failure_numbers: list[int] = []
    for entry in new_failure_entries:
        first_line = entry.split("\n", 1)[0]
        heading = FAILURE_ID_RE.match(first_line)
        if heading is None:
            raise SpoolValidationError([
                Issue(
                    "docs/failures.md",
                    1,
                    "failure-topology",
                    f"追加 F entry の先頭行が不正: {first_line!r}",
                )
            ])
        appended_failure_numbers.append(int(heading.group("number")))
        rendered_failures = _append_bytes(rendered_failures, entry)
    rendered_failures_text = rendered_failures.decode("utf-8")
    allocated_failure_numbers = [
        int(allocations[symbol.key][1:])
        for symbol in symbols
        if symbol.namespace == "F"
    ]
    _assert_failure_topology(
        failure_numbers,
        rendered_failures_text,
        appended_failure_numbers,
        allocated_failure_numbers,
    )

    receipt_lines: list[str] = []
    fragment_receipts: list[FragmentReceipt] = []
    for fragment in fragments:
        owned = tuple(sorted(
            (f"{symbol.namespace}:{symbol.slug}", allocations[symbol.key])
            for symbol in symbols
            if symbol.fragment_path == fragment.path
        ))
        record = {
            "allocations": dict(owned),
            "authored": fragment.authored,
            "base": origin.base,
            "content_sha256": fragment.content_sha,
            "seq": fragment.seq,
            "tested_tip": origin.tested_tip,
            "wave": fragment.wave,
            "wave_ref": origin.wave_ref,
        }
        receipt_lines.append("- " + json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        fragment_receipts.append(FragmentReceipt(fragment.path, fragment.authored, fragment.wave, fragment.seq, fragment.content_sha, owned))
    fragment_receipts.sort(key=lambda fragment: fragment.path)
    rendered_receipt = _append_bytes(receipt_raw, "\n".join(receipt_lines))

    rotation_path: str | None = None
    rotation_archive: bytes | None = None
    rendered_archive_readme = archive_readme_raw
    if len(rendered_worklog) > limit:
        rendered_worklog, rotation_path, rotation_archive, rendered_archive_readme = _rotate_worklog(
            repo, worklog_raw, rendered_worklog, archive_readme_raw, limit
        )

    changes: dict[str, bytes] = {
        "docs/worklog.md": rendered_worklog,
        "docs/decisions.md": rendered_decisions,
        "docs/failures.md": rendered_failures,
        "docs/phase3.md": rendered_phase.encode("utf-8"),
        RECEIPT_REL.as_posix(): rendered_receipt,
    }
    if rotation_path is not None and rotation_archive is not None:
        changes[rotation_path] = rotation_archive
        changes["docs/archive/README.md"] = rendered_archive_readme
    targets: list[TargetChange] = []
    for rel in sorted(changes):
        path = repo / rel
        before = path.read_bytes() if path.exists() and path.is_file() and not path.is_symlink() else b""
        if before != changes[rel]:
            targets.append(_target(repo, rel, changes[rel]))
    gc_paths = tuple(fragment.path for fragment in fragment_receipts)
    transaction_id = _plan_transaction_id(
        fold_date,
        origin,
        input_closure_sha256,
        fragment_receipts,
        gc_paths,
        len(rendered_worklog),
        rotation_path,
        targets,
    )
    flat_allocations = tuple(sorted((f"{wave}/{namespace}:{slug}", value) for (wave, namespace, slug), value in allocations.items()))
    plan = FoldPlan(
        "planned",
        fold_date,
        transaction_id,
        origin,
        input_closure_sha256,
        "applied",
        flat_allocations,
        tuple(targets),
        tuple(fragment_receipts),
        gc_paths,
        len(rendered_worklog),
        rotation_path,
    )
    approval_issue = _approval_guard_issue(repo, _plan_decision_payloads(repo, plan))
    if approval_issue is not None:
        code, message = approval_issue
        raise SpoolValidationError(
            [Issue("docs/decisions.md", 1, code, message)]
        )
    return plan


def _atomic_replace(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _atomic_write(path: Path, data: bytes, *, mode: int | None = None) -> None:
    if mode is None:
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            mode = 0o600
        else:
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(
                metadata.st_mode
            ):
                raise TransactionError(
                    f"atomic write target が symlink/非 regular: {path}"
                )
            mode = stat.S_IMODE(metadata.st_mode)
    _atomic_replace(path, data, mode)


def _atomic_write_canonical_target(path: Path, data: bytes) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        pass
    else:
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(
            metadata.st_mode
        ):
            raise TransactionError(
                f"canonical write target が symlink/非 regular: {path}"
            )
    _atomic_replace(path, data, 0o644)


def _plan_state(plan: FoldPlan) -> dict[str, object]:
    return {
        "version": STATE_VERSION,
        "phase": plan.phase,
        "transaction_id": plan.transaction_id,
        "origin": _origin_dict(plan.origin),
        "input_closure_sha256": plan.input_closure_sha256,
        "fold_date": plan.fold_date,
        "fragments": [
            {
                "path": fragment.path,
                "authored": fragment.authored,
                "wave": fragment.wave,
                "seq": fragment.seq,
                "content_sha256": fragment.content_sha256,
                "allocations": [list(pair) for pair in fragment.allocations],
            }
            for fragment in plan.fragments
        ],
        "gc_paths": list(plan.gc_paths),
        "projected_worklog_bytes": plan.projected_worklog_bytes,
        "rotation_path": plan.rotation_path,
        "gate_receipt": (
            None
            if plan.gate_receipt is None
            else {
                "nodeids": list(plan.gate_receipt.nodeids),
                "outcome": plan.gate_receipt.outcome,
                "registry_digest": plan.gate_receipt.registry_digest,
                "target_raw_digests": [
                    list(pair) for pair in plan.gate_receipt.target_raw_digests
                ],
                "transaction_id": plan.gate_receipt.transaction_id,
                "uncovered_families": list(
                    plan.gate_receipt.uncovered_families
                ),
            }
        ),
        "targets": [
            {
                "after_bytes_b64": base64.b64encode(target.after_bytes).decode("ascii"),
                "after_sha256": target.after_sha256,
                "before_exists": target.before_exists,
                "before_sha256": target.before_sha256,
                "path": target.path,
            }
            for target in plan.targets
        ],
    }


def _safe_rel_path(value: object) -> bool:
    if type(value) is not str or not value or "\\" in value or value.startswith("/"):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def _fragment_rel_valid(value: object) -> bool:
    if not _safe_rel_path(value) or type(value) is not str:
        return False
    parts = value.split("/")
    return (
        len(parts) == 4
        and parts[:2] == ["docs", "spool"]
        and parts[2] in LEDGERS
        and FRAGMENT_FILE_RE.fullmatch(parts[3]) is not None
    )


def _target_rel_valid(value: object) -> bool:
    if not _safe_rel_path(value) or type(value) is not str:
        return False
    return value in {
        "docs/worklog.md",
        "docs/decisions.md",
        "docs/failures.md",
        "docs/phase3.md",
        "docs/spool/FOLDED.md",
        "docs/archive/README.md",
    } or ROTATION_PATH_RE.fullmatch(value) is not None


def _origin_from_state(value: object) -> FoldOrigin:
    if type(value) is not dict or frozenset(value) != ORIGIN_FIELDS:
        raise TransactionError("transaction state origin field 集合が不正")
    if any(type(item) is not str for item in value.values()):
        raise TransactionError("transaction state origin の値型が不正")
    origin = FoldOrigin(
        value["kind"],
        value["base"],
        value["tested_tip"],
        value["wave_ref"],
        value["rollback_ref"],
        value["trusted_main_cutoff"],
        value["audited_digest"],
    )
    if (
        origin.kind not in {"land", "standalone"}
        or any(
            OID_RE.fullmatch(oid) is None
            for oid in (
                origin.base,
                origin.tested_tip,
                origin.rollback_ref,
                origin.trusted_main_cutoff,
            )
        )
        or REF_RE.fullmatch(origin.wave_ref) is None
        or SHA_RE.fullmatch(origin.audited_digest) is None
    ):
        raise TransactionError("transaction state origin の正規形が不正")
    if origin.base != origin.rollback_ref:
        raise TransactionError("transaction state origin base/rollback_ref が不一致")
    if origin.kind == "standalone" and (
        origin.base != origin.tested_tip
        or origin.trusted_main_cutoff != origin.base
        or origin.audited_digest != audited_commit_digest(())
    ):
        raise TransactionError("standalone origin の値が観測既定形でない")
    return origin


def _gate_receipt_from_state(value: object) -> FoldGateReceipt | None:
    if value is None:
        return None
    if type(value) is not dict or frozenset(value) != GATE_RECEIPT_FIELDS:
        raise FoldGateReceiptError("fold gate receipt field 集合が不正")
    transaction_id = value["transaction_id"]
    registry_digest = value["registry_digest"]
    nodeids = value["nodeids"]
    raw_digests = value["target_raw_digests"]
    outcome = value["outcome"]
    uncovered = value["uncovered_families"]
    if (
        type(transaction_id) is not str
        or SHA_RE.fullmatch(transaction_id) is None
        or type(registry_digest) is not str
        or SHA_RE.fullmatch(registry_digest) is None
        or type(nodeids) is not list
        or any(type(nodeid) is not str or not nodeid for nodeid in nodeids)
        or tuple(nodeids) != tuple(sorted(set(nodeids)))
        or type(raw_digests) is not list
        or type(outcome) is not str
        or outcome != "covered-families-passed"
        or type(uncovered) is not list
        or any(type(family) is not str or not family for family in uncovered)
        or tuple(uncovered) != tuple(sorted(set(uncovered)))
    ):
        raise FoldGateReceiptError("fold gate receipt の値型/正規形が不正")
    pairs: list[tuple[str, str]] = []
    for pair in raw_digests:
        if (
            type(pair) is not list
            or len(pair) != 2
            or type(pair[0]) is not str
            or not _target_rel_valid(pair[0])
            or type(pair[1]) is not str
            or SHA_RE.fullmatch(pair[1]) is None
        ):
            raise FoldGateReceiptError("fold gate target raw digest が不正")
        pairs.append((pair[0], pair[1]))
    if tuple(pairs) != tuple(sorted(set(pairs))):
        raise FoldGateReceiptError(
            "fold gate target raw digest の順序/一意性が不正"
        )
    return FoldGateReceipt(
        transaction_id,
        registry_digest,
        tuple(nodeids),
        tuple(pairs),
        outcome,
        tuple(uncovered),
    )


def _state_plan(state: Mapping[str, object]) -> FoldPlan:
    if type(state) is not dict or frozenset(state) != STATE_FIELDS:
        raise TransactionError("transaction state top-level field 集合が不正")
    if type(state["version"]) is not int or state["version"] != STATE_VERSION:
        raise TransactionError("transaction state version/schema が不正")
    phase = state["phase"]
    transaction_id = state["transaction_id"]
    input_closure_sha256 = state["input_closure_sha256"]
    fold_date = state["fold_date"]
    projected = state["projected_worklog_bytes"]
    rotation_path = state["rotation_path"]
    if type(phase) is not str or phase not in STATE_PHASES:
        raise TransactionError("transaction state phase が不正")
    if type(transaction_id) is not str or SHA_RE.fullmatch(transaction_id) is None:
        raise TransactionError("transaction state の transaction_id が不正")
    if type(input_closure_sha256) is not str or SHA_RE.fullmatch(input_closure_sha256) is None:
        raise TransactionError("transaction state の input closure が不正")
    if type(fold_date) is not str or not _valid_date(fold_date):
        raise TransactionError("transaction state の fold_date が不正")
    if type(projected) is not int or projected < 0:
        raise TransactionError("transaction state の projected_worklog_bytes が不正")
    if rotation_path is not None and (
        type(rotation_path) is not str
        or ROTATION_PATH_RE.fullmatch(rotation_path) is None
    ):
        raise TransactionError("transaction state の rotation_path が不正")
    origin = _origin_from_state(state["origin"])
    gate_receipt = _gate_receipt_from_state(state["gate_receipt"])

    raw_targets = state["targets"]
    if type(raw_targets) is not list:
        raise TransactionError("transaction state targets が list でない")
    targets_list: list[TargetChange] = []
    for item in raw_targets:
        if type(item) is not dict or frozenset(item) != TARGET_STATE_FIELDS:
            raise TransactionError("transaction state target field 集合が不正")
        if (
            not _target_rel_valid(item["path"])
            or type(item["before_exists"]) is not bool
            or type(item["before_sha256"]) is not str
            or SHA_RE.fullmatch(item["before_sha256"]) is None
            or type(item["after_sha256"]) is not str
            or SHA_RE.fullmatch(item["after_sha256"]) is None
            or type(item["after_bytes_b64"]) is not str
        ):
            raise TransactionError("transaction state target の値型/正規形が不正")
        try:
            after_bytes = base64.b64decode(item["after_bytes_b64"], validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise TransactionError("transaction state target の base64 が不正") from exc
        if _sha256(after_bytes) != item["after_sha256"]:
            raise TransactionError(f"state payload hash が不一致: {item['path']}")
        targets_list.append(TargetChange(
            item["path"], item["before_sha256"], item["after_sha256"],
            item["before_exists"], after_bytes,
        ))
    targets = tuple(targets_list)
    if not targets:
        raise TransactionError("transaction state targets が空")
    target_paths = tuple(target.path for target in targets)
    if target_paths != tuple(sorted(set(target_paths))):
        raise TransactionError("transaction state target path の順序/一意性が不正")
    worklog_targets = [target for target in targets if target.path == "docs/worklog.md"]
    if worklog_targets and len(worklog_targets[0].after_bytes) != projected:
        raise TransactionError("projected_worklog_bytes が worklog after bytes と不一致")
    if rotation_path is not None and sum(target.path == rotation_path for target in targets) != 1:
        raise TransactionError("rotation_path が target と一意対応しない")
    if rotation_path is not None and next(
        target.before_exists for target in targets if target.path == rotation_path
    ):
        raise TransactionError("rotation target の before_exists が false でない")
    empty_sha = _sha256(b"")
    if any(
        not target.before_exists and target.before_sha256 != empty_sha
        for target in targets
    ):
        raise TransactionError("nonexistent target の before_sha256 が空 bytes hash でない")

    raw_fragments = state["fragments"]
    if type(raw_fragments) is not list:
        raise TransactionError("transaction state fragments が list でない")
    fragments_list: list[FragmentReceipt] = []
    for item in raw_fragments:
        if type(item) is not dict or frozenset(item) != FRAGMENT_STATE_FIELDS:
            raise TransactionError("transaction state fragment field 集合が不正")
        allocations_raw = item["allocations"]
        if type(allocations_raw) is not list:
            raise TransactionError("transaction state allocations が list でない")
        allocations: list[tuple[str, str]] = []
        for pair in allocations_raw:
            if (
                type(pair) is not list
                or len(pair) != 2
                or any(type(value) is not str for value in pair)
            ):
                raise TransactionError("transaction state allocation pair が不正")
            allocations.append((pair[0], pair[1]))
        if tuple(allocations) != tuple(sorted(set(allocations))):
            raise TransactionError("transaction state allocation の順序/一意性が不正")
        for key, value in allocations:
            namespace = key.split(":", 1)[0] if ":" in key else ""
            if (
                re.fullmatch(r"[TDF]:[a-z][a-z0-9]*(?:-[a-z0-9]+)*", key) is None
                or (
                    (namespace == "T" and TASK_RE.fullmatch(value) is None)
                    or (namespace == "D" and re.fullmatch(r"D[1-9][0-9]*", value) is None)
                    or (namespace == "F" and re.fullmatch(r"F[1-9][0-9]*", value) is None)
                )
            ):
                raise TransactionError("transaction state allocation の値が不正")
        fragment_name = FRAGMENT_FILE_RE.fullmatch(item["path"].rsplit("/", 1)[-1]) if type(item["path"]) is str else None
        if (
            not _fragment_rel_valid(item["path"])
            or type(item["authored"]) is not str
            or not _valid_date(item["authored"])
            or type(item["wave"]) is not str
            or WAVE_RE.fullmatch(item["wave"]) is None
            or type(item["seq"]) is not int
            or item["seq"] <= 0
            or type(item["content_sha256"]) is not str
            or SHA_RE.fullmatch(item["content_sha256"]) is None
            or fragment_name is None
            or fragment_name.group("authored") != item["authored"]
            or fragment_name.group("wave") != item["wave"]
            or int(fragment_name.group("seq")) != item["seq"]
        ):
            raise TransactionError("transaction state fragment の値型/正規形が不正")
        fragments_list.append(FragmentReceipt(
            item["path"], item["authored"], item["wave"], item["seq"],
            item["content_sha256"], tuple(allocations),
        ))
    fragments = tuple(fragments_list)
    if not fragments:
        raise TransactionError("transaction state fragments が空")
    fragment_paths = tuple(fragment.path for fragment in fragments)
    if fragment_paths != tuple(sorted(set(fragment_paths))):
        raise TransactionError("transaction state fragment path の順序/一意性が不正")

    raw_gc_paths = state["gc_paths"]
    if (
        type(raw_gc_paths) is not list
        or any(not _safe_rel_path(path) for path in raw_gc_paths)
        or tuple(raw_gc_paths) != fragment_paths
    ):
        raise TransactionError("transaction state gc_paths が fragments と不一致")
    plan = FoldPlan(
        "planned", fold_date, transaction_id, origin,
        input_closure_sha256, phase, (), targets, fragments,
        tuple(raw_gc_paths), projected, rotation_path, gate_receipt,
    )
    expected_id = _plan_transaction_id(
        plan.fold_date,
        plan.origin,
        plan.input_closure_sha256,
        plan.fragments,
        plan.gc_paths,
        plan.projected_worklog_bytes,
        plan.rotation_path,
        plan.targets,
    )
    if expected_id != plan.transaction_id:
        raise TransactionError("transaction_id が payload と不一致")
    if origin.kind == "land" and gate_receipt is not None:
        if gate_receipt.transaction_id != plan.transaction_id:
            raise FoldGateReceiptError(
                "fold gate receipt transaction_id が plan と不一致"
            )
        expected_raw_digests = tuple(
            (target.path, _sha256(target.after_bytes)) for target in plan.targets
        )
        if gate_receipt.target_raw_digests != expected_raw_digests:
            raise FoldGateReceiptError(
                "fold gate receipt target raw digest が plan と不一致"
            )
    elif gate_receipt is not None:
        raise FoldGateReceiptError(
            "standalone transaction が fold gate receipt を持つ"
        )
    return plan


def _load_state(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise TransactionError("transaction state が regular file でない")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransactionError(f"transaction state を読めない: {exc}") from exc
    if type(value) is not dict:
        raise TransactionError("transaction state version/schema が不正")
    if "gate_receipt" not in value:
        raise FoldGateReceiptError(
            "旧 transaction state に fold gate receipt がない"
        )
    if frozenset(value) != STATE_FIELDS:
        raise TransactionError("transaction state version/schema が不正")
    if type(value["version"]) is not int or value["version"] != STATE_VERSION:
        raise FoldGateReceiptError(
            "transaction state version が fold gate receipt schema と不一致"
        )
    canonical = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8") + b"\n"
    if raw != canonical:
        raise TransactionError("transaction state JSON が正準形でない")
    return value


def _transaction_shape(repo: Path, plan: FoldPlan) -> tuple[dict[str, str], dict[str, str]]:
    target_states: dict[str, str] = {}
    for target in plan.targets:
        path = repo / target.path
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise TransactionError(f"{target.path}: symlink/非 regular の第三状態")
        current_exists = path.exists() and path.is_file()
        current = path.read_bytes() if current_exists else b""
        current_sha = _sha256(current)
        if current_exists and current_sha == target.after_sha256:
            target_states[target.path] = "after"
        elif current_sha == target.before_sha256 and current_exists == target.before_exists:
            target_states[target.path] = "before"
        else:
            raise TransactionError(f"{target.path}: before/after 以外の第三状態")

    gc_states: dict[str, str] = {}
    receipt_by_path = {fragment.path: fragment for fragment in plan.fragments}
    for rel in plan.gc_paths:
        path = repo / rel
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise TransactionError(f"{rel}: GC target が symlink/非 regular")
        if not path.exists():
            gc_states[rel] = "missing"
            continue
        receipt = receipt_by_path[rel]
        if _sha256(path.read_bytes()) != receipt.content_sha256:
            raise TransactionError(f"{rel}: GC target content が transaction と不一致")
        gc_states[rel] = "present"
    if any(state == "missing" for state in gc_states.values()) and any(
        state == "before" for state in target_states.values()
    ):
        raise TransactionError("canonical が before の段階で GC target が欠落した第三状態")
    return target_states, gc_states


def _current_closure_digest(
    repo: Path,
    plan: FoldPlan,
    target_states: Mapping[str, str],
    gc_states: Mapping[str, str],
) -> str:
    files: dict[str, str] = {}
    targets = {target.path: target for target in plan.targets}
    for rel in _CLOSURE_FIXED_PATHS:
        target = targets.get(rel)
        if target is not None:
            files[rel] = target.before_sha256
        else:
            files[rel] = _sha256(_read_required(repo, rel))

    archive_dir = repo / "docs/archive"
    if archive_dir.is_symlink() or not archive_dir.is_dir():
        raise TransactionError("archive directory が不正")
    for path in sorted(archive_dir.glob("worklog-*.md"), key=lambda item: item.name):
        rel = path.relative_to(repo).as_posix()
        if rel == plan.rotation_path:
            continue
        if path.is_symlink() or not path.is_file():
            raise TransactionError(f"{rel}: archive worklog が regular file でない")
        files[rel] = _sha256(path.read_bytes())

    expected_fragments = {fragment.path: fragment for fragment in plan.fragments}
    all_targets_after = all(state == "after" for state in target_states.values())
    for rel, fragment in expected_fragments.items():
        state = gc_states[rel]
        if state == "present":
            files[rel] = fragment.content_sha256
        elif all_targets_after:
            files[rel] = fragment.content_sha256
        else:
            raise TransactionError("target が before のまま GC target が欠落した第三状態")
    for ledger in LEDGERS:
        directory = repo / "docs" / "spool" / ledger
        if directory.is_symlink() or not directory.is_dir():
            raise TransactionError(f"docs/spool/{ledger}: fragment directory が不正")
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.name == "README.md":
                continue
            rel = path.relative_to(repo).as_posix()
            if rel in expected_fragments:
                continue
            if path.is_symlink() or not path.is_file():
                raise TransactionError(f"{rel}: 新 fragment が regular file でない")
            files[rel] = _sha256(path.read_bytes())
    try:
        limit = _load_rotate_limit(repo)
    except SpoolValidationError as exc:
        raise TransactionError(str(exc)) from exc
    return _closure_digest(files, limit)


def _validate_closure(repo: Path, plan: FoldPlan) -> tuple[dict[str, str], dict[str, str]]:
    target_states, gc_states = _transaction_shape(repo, plan)
    try:
        current = _current_closure_digest(repo, plan, target_states, gc_states)
    except (OSError, subprocess.SubprocessError, SpoolValidationError) as exc:
        raise TransactionError(f"plan 入力 closure を観測できない: {exc}") from exc
    if current != plan.input_closure_sha256:
        raise TransactionError("plan 入力 closure が変化")
    return target_states, gc_states


def load_active_plan(repo: str | os.PathLike[str] | Path) -> FoldPlan | None:
    """当該 worktree の durable transaction plan を読み、なければ ``None``。"""

    repo = Path(repo).resolve()
    state_path = _state_path(repo)
    if not state_path.exists() and not state_path.is_symlink():
        return None
    plan = _state_plan(_load_state(state_path))
    _validate_closure(repo, plan)
    return plan


def _git_clean_preflight(repo: Path, plan: FoldPlan, *, resume: bool = False) -> None:
    # gc_paths は plan が content hash まで束縛した入力 fragment であり、通常は
    # untracked のまま apply される。canonical の既存 target だけについて、plan
    # 構築後の index/worktree 変更を Git 面でも拒否する。fragment 自体の第三状態は
    # apply 本体の receipt content_sha256 照合が fail-closed に検出する。
    paths = sorted({
        *(target.path for target in plan.targets if target.before_exists or resume),
        *(plan.gc_paths if resume else ()),
    })
    if not paths:
        return
    completed = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "--", *paths],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.stdout and not resume:
        raise TransactionError("actual fold 対象に未追跡または dirty path がある")
    if resume:
        for line in completed.stdout.splitlines():
            if len(line) < 2 or (line[0] not in {" ", "?"}):
                raise TransactionError("resume fold 対象に staged/不正な Git 状態がある")


def _verify_apply_head(repo: Path, plan: FoldPlan) -> None:
    try:
        head = _git_text(repo, "rev-parse", "--verify", "HEAD^{commit}")
    except (OSError, subprocess.SubprocessError, SpoolValidationError) as exc:
        raise TransactionError(f"apply HEAD を観測できない: {exc}") from exc
    if head != plan.origin.tested_tip:
        raise TransactionError("apply HEAD が origin.tested_tip と不一致")


def apply_fold(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    gate_receipt: FoldGateReceipt | None = None,
) -> FoldResult:
    """FoldPlan を transaction state、canonical、GC の順で適用する。"""

    repo = Path(repo).resolve()
    if plan.status == "noop":
        if (
            plan.transaction_id != ""
            or plan.input_closure_sha256 != ""
            or plan.targets
            or plan.fragments
            or plan.gc_paths
        ):
            raise TransactionError("noop plan が non-empty transaction payload を持つ")
        return FoldResult("noop", "", (), (), ())
    state_path = _state_path(repo)
    state_exists = state_path.exists() or state_path.is_symlink()
    if state_exists:
        stored_plan = _state_plan(_load_state(state_path))
        if stored_plan.transaction_id != plan.transaction_id:
            raise TransactionError("active transaction と渡された plan の ID が不一致")
        if (
            stored_plan.gate_receipt is not None
            and stored_plan.gate_receipt != gate_receipt
        ):
            raise FoldGateReceiptError(
                "active transaction と渡された fold gate receipt が不一致"
            )
        plan = stored_plan
        if plan.phase != "applied":
            raise TransactionError("committed transaction を apply へ戻せない")
        _verify_apply_head(repo, plan)
        _validate_closure(repo, plan)
        _git_clean_preflight(repo, plan, resume=True)
    else:
        if plan.phase != "applied":
            raise TransactionError("fresh plan の phase が applied でない")
        expected_id = _plan_transaction_id(
            plan.fold_date, plan.origin, plan.input_closure_sha256,
            plan.fragments, plan.gc_paths, plan.projected_worklog_bytes,
            plan.rotation_path, plan.targets,
        )
        if expected_id != plan.transaction_id:
            raise TransactionError("渡された plan の transaction_id が payload と不一致")
        if plan.origin.kind == "land" and gate_receipt is not None:
            expected_raw_digests = tuple(
                (target.path, _sha256(target.after_bytes))
                for target in plan.targets
            )
            if (
                gate_receipt.transaction_id != plan.transaction_id
                or gate_receipt.target_raw_digests != expected_raw_digests
            ):
                raise FoldGateReceiptError(
                    "fresh fold gate receipt が plan bytes と不一致"
                )
            plan = dataclasses.replace(plan, gate_receipt=gate_receipt)
        elif gate_receipt is not None:
            raise FoldGateReceiptError(
                "standalone transaction へ fold gate receipt を渡せない"
            )
        _verify_apply_head(repo, plan)
        _validate_closure(repo, plan)
    approval_issue = _approval_guard_issue(repo, _plan_decision_payloads(repo, plan))
    if approval_issue is not None:
        code, message = approval_issue
        raise TransactionError(f"[{code}] {message}")
    if not state_exists:
        _git_clean_preflight(repo, plan)
        state_data = json.dumps(_plan_state(plan), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
        _atomic_write(state_path, state_data)

    written: list[str] = []
    resumed: list[str] = []
    target_states, _gc_states = _transaction_shape(repo, plan)

    # 一つでも第三状態なら、別 target の before を先に書かない。全 target の状態を
    # 確定してから適用へ進むことで N16 を単一の fail-closed gate にする。
    for target in plan.targets:
        if target_states[target.path] == "after":
            resumed.append(target.path)
            continue
        path = repo / target.path
        _atomic_write_canonical_target(path, target.after_bytes)
        if _sha256(path.read_bytes()) != target.after_sha256:
            raise TransactionError(f"{target.path}: after write hash が不一致")
        written.append(target.path)

    for target in plan.targets:
        path = repo / target.path
        if path.is_symlink() or not path.is_file() or _sha256(path.read_bytes()) != target.after_sha256:
            raise TransactionError(f"{target.path}: GC 前 after 確認に失敗")

    removed: list[str] = []
    for rel in sorted(plan.gc_paths):
        path = repo / rel
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise TransactionError(f"{rel}: GC target が regular file でない")
        path.unlink()
        removed.append(rel)
    _fsync_directories({(repo / rel).parent for rel in plan.gc_paths})
    status = "resumed" if state_exists or resumed else "applied"
    return FoldResult(status, plan.transaction_id, tuple(written), tuple(resumed), tuple(removed))


def _fsync_directories(paths: Iterable[Path]) -> None:
    for path in sorted({item.resolve() for item in paths}, key=str):
        directory_fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def _complete_shape(repo: Path, plan: FoldPlan) -> None:
    target_states, gc_states = _validate_closure(repo, plan)
    if any(state != "after" for state in target_states.values()):
        raise TransactionError("fold target が全 after でない")
    if any(state != "missing" for state in gc_states.values()):
        raise TransactionError("fold GC path が残存する")


def _commit_diff_records(repo: Path, parent: str, commit: str) -> dict[str, tuple[str, str, str, str]]:
    raw = _git(
        repo, "diff-tree", "--no-commit-id", "--raw", "-r", "-z",
        "--no-renames", parent, commit,
    )
    chunks = raw.split(b"\0")
    if chunks and chunks[-1] == b"":
        chunks.pop()
    if len(chunks) % 2:
        raise TransactionError("fold commit diff record が不正")
    records: dict[str, tuple[str, str, str, str]] = {}
    for index in range(0, len(chunks), 2):
        metadata = chunks[index]
        path_raw = chunks[index + 1]
        if not metadata.startswith(b":"):
            raise TransactionError("fold commit diff metadata が不正")
        fields = metadata[1:].split(b" ")
        if len(fields) != 5:
            raise TransactionError("fold commit diff metadata field が不正")
        old_mode, new_mode, _old_oid, new_oid, status = fields
        try:
            path = path_raw.decode("utf-8", errors="strict")
            decoded = (
                status.decode("ascii", errors="strict"),
                old_mode.decode("ascii", errors="strict"),
                new_mode.decode("ascii", errors="strict"),
                new_oid.decode("ascii", errors="strict"),
            )
        except UnicodeDecodeError as exc:
            raise TransactionError("fold commit diff encoding が不正") from exc
        if path in records:
            raise TransactionError("fold commit diff path が重複")
        records[path] = decoded
    return records


def verify_fold_commit_identity(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    fold_commit: str,
) -> None:
    """state が宣言する exact fold commit identity を再利用可能に検査する。"""

    repo = Path(repo).resolve()
    if type(fold_commit) is not str or OID_RE.fullmatch(fold_commit) is None:
        raise TransactionError("fold_commit が exact Git OID でない")
    try:
        resolved = _git_text(repo, "rev-parse", "--verify", f"{fold_commit}^{{commit}}")
        raw_commit = _git(repo, "cat-file", "commit", fold_commit)
    except (OSError, subprocess.SubprocessError, SpoolValidationError) as exc:
        raise TransactionError(f"fold commit を観測できない: {exc}") from exc
    if resolved != fold_commit:
        raise TransactionError("fold_commit が exact commit として解決しない")
    header, separator, message = raw_commit.partition(b"\n\n")
    if not separator:
        raise TransactionError("fold commit object の header/message 境界がない")
    parents: list[str] = []
    authors: list[bytes] = []
    for line in header.splitlines():
        key, space, value = line.partition(b" ")
        if not space:
            raise TransactionError("fold commit header が不正")
        if key == b"parent":
            try:
                parents.append(value.decode("ascii", errors="strict"))
            except UnicodeDecodeError as exc:
                raise TransactionError("fold commit parent encoding が不正") from exc
        elif key == b"author":
            authors.append(value)
    try:
        from tools.dev_waves.git_state import (
            FOLD_AUTHOR_IDENTITY,
            FOLD_COMMIT_MESSAGE,
            verify_declared_fold_commit,
        )
        from tools.dev_waves.schema import DevWavesError
    except (ImportError, AttributeError) as exc:
        raise TransactionError(f"declared fold verifier を import できない: {exc}") from exc
    if parents != [plan.origin.tested_tip]:
        raise TransactionError("fold commit の単一 parent が origin.tested_tip と不一致")
    author_pattern = (
        re.escape(FOLD_AUTHOR_IDENTITY.encode("utf-8"))
        + rb" (?:0|[1-9][0-9]*) [+-](?:(?:0[0-9]|1[0-3])[0-5][0-9]|1400)"
    )
    if len(authors) != 1 or re.fullmatch(author_pattern, authors[0]) is None:
        raise TransactionError("fold commit author identity が不一致")
    if message != FOLD_COMMIT_MESSAGE:
        raise TransactionError("fold commit message bytes が不一致")

    try:
        actual = _commit_diff_records(repo, plan.origin.tested_tip, fold_commit)
        expected_paths = {target.path for target in plan.targets} | set(plan.gc_paths)
        if set(actual) != expected_paths:
            raise TransactionError("fold commit diff path 集合が state と不一致")
        for target in plan.targets:
            status, old_mode, new_mode, new_oid = actual[target.path]
            expected_status = "M" if target.before_exists else "A"
            expected_old_mode = "100644" if target.before_exists else "000000"
            expected_oid = _git_text(repo, "hash-object", "--stdin", input_bytes=target.after_bytes)
            if (
                status != expected_status
                or old_mode != expected_old_mode
                or new_mode != "100644"
                or new_oid != expected_oid
            ):
                raise TransactionError(f"fold commit target record が不一致: {target.path}")
        for rel in plan.gc_paths:
            status, _old_mode, new_mode, _new_oid = actual[rel]
            if status != "D" or new_mode != "000000":
                raise TransactionError(f"fold commit GC record が不一致: {rel}")
        audited = _audited_commits(repo, plan.origin)
    except (OSError, subprocess.SubprocessError, SpoolValidationError) as exc:
        raise TransactionError(f"fold commit diff/audit を観測できない: {exc}") from exc
    if audited_commit_digest(audited) != plan.origin.audited_digest:
        raise TransactionError("fold commit gate の audited closure が origin と不一致")
    landed_commits = audited if audited else (plan.origin.tested_tip,)
    try:
        declared = verify_declared_fold_commit(
            repo,
            fold_commit_sha=fold_commit,
            trusted_main_cutoff_sha=plan.origin.trusted_main_cutoff,
            landed_main_sha=fold_commit,
            landed_commits=landed_commits,
            wave_tip=plan.origin.tested_tip,
        )
    except BaseException as exc:
        if isinstance(exc, DevWavesError):
            raise TransactionError(
                f"declared fold verifier が失敗: {exc.code.value} "
                f"{json.dumps(exc.detail, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"
            ) from exc
        raise TransactionError(f"declared fold verifier が失敗: {exc}") from exc
    if not declared.ok:
        raise TransactionError(f"declared fold verifier が拒否: {declared.detail}")


def mark_fold_committed(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    fold_commit: str,
) -> FoldPlan:
    repo = Path(repo).resolve()
    if plan.origin.kind != "land":
        raise TransactionError("standalone transaction は mark/finalize できない")
    state_path = _state_path(repo)
    stored = _state_plan(_load_state(state_path))
    if stored.transaction_id != plan.transaction_id or stored.phase != "applied":
        raise TransactionError("mark_fold_committed の state ID/phase CAS が不一致")
    if _git_text(repo, "rev-parse", "--verify", "HEAD^{commit}") != fold_commit:
        raise TransactionError("mark_fold_committed の HEAD が fold_commit と不一致")
    _complete_shape(repo, stored)
    verify_fold_commit_identity(repo, stored, fold_commit=fold_commit)
    committed = dataclasses.replace(stored, phase="committed")
    data = json.dumps(
        _plan_state(committed), ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8") + b"\n"
    _atomic_write(state_path, data)
    return committed


def finalize_fold(
    repo: str | os.PathLike[str] | Path,
    plan: FoldPlan,
    *,
    fold_commit: str,
) -> None:
    repo = Path(repo).resolve()
    if plan.origin.kind != "land":
        raise TransactionError("standalone transaction は mark/finalize できない")
    state_path = _state_path(repo)
    stored = _state_plan(_load_state(state_path))
    if stored.transaction_id != plan.transaction_id or stored.phase != "committed":
        raise TransactionError("finalize_fold の state ID/phase が不一致")
    if _git_text(repo, "rev-parse", "--verify", "HEAD^{commit}") != fold_commit:
        raise TransactionError("finalize_fold の HEAD が fold_commit と不一致")
    _complete_shape(repo, stored)
    verify_fold_commit_identity(repo, stored, fold_commit=fold_commit)
    state_path.unlink()
    _fsync_directories({state_path.parent})


def _lf_lines(data: bytes) -> list[bytes]:
    """LF だけを行境界として、元 byte を保持した行列を返す。"""

    if not data:
        return []
    parts = data.split(b"\n")
    lines = [part + b"\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def _unsafe_terminal_byte(value: int) -> bool:
    return (value < 0x20 and value not in {0x09, 0x0A}) or value == 0x7F


def _escape_diff_payload(line: bytes) -> bytes:
    """先頭の diff marker を保ち、payload を可逆な C-style 表記へする。"""

    escaped = bytearray(line[:1])
    for value in line[1:]:
        if value == 0x5C:
            escaped.extend(b"\\\\")
        elif _unsafe_terminal_byte(value):
            escaped.extend(f"\\x{value:02x}".encode("ascii"))
        else:
            escaped.append(value)
    return bytes(escaped)


def _diff_lines(before: bytes, after: bytes, *, fromfile: bytes, tofile: bytes) -> Iterable[bytes]:
    raw_diff = difflib.diff_bytes(
        difflib.unified_diff,
        _lf_lines(before),
        _lf_lines(after),
        fromfile=fromfile,
        tofile=tofile,
    )
    diff: list[tuple[bytes, bool]] = []
    for index, line in enumerate(raw_diff):
        is_payload = index >= 2 and line[:1] in {b" ", b"+", b"-"}
        if is_payload and not line.endswith(b"\n"):
            diff.append((line + b"\n", True))
            diff.append((b"\\ No newline at end of file\n", False))
        else:
            diff.append((line, is_payload))

    escaped_mode = any(
        _unsafe_terminal_byte(value)
        for line, is_payload in diff
        if is_payload
        for value in line[1:]
    )
    if escaped_mode:
        yield b"# payload_control_bytes=escaped-c-v1\n"
    for line, is_payload in diff:
        yield _escape_diff_payload(line) if escaped_mode and is_payload else line


def _iter_plan_diff(repo: Path, plan: FoldPlan) -> Iterable[bytes]:
    """全 before を先に照合し、plan の byte-oriented unified diff を返す。"""

    target_before: dict[str, bytes] = {}
    for target in plan.targets:
        path = repo / target.path
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise TransactionError(f"{target.path}: diff 対象が symlink/非 regular")
        exists = path.exists()
        before = path.read_bytes() if exists else b""
        if exists != target.before_exists or _sha256(before) != target.before_sha256:
            raise _DiffPreflightError(f"{target.path}: diff before が plan と不一致")
        if _sha256(target.after_bytes) != target.after_sha256:
            raise _DiffPreflightError(f"{target.path}: diff after が plan と不一致")
        target_before[target.path] = before

    receipts = {fragment.path: fragment for fragment in plan.fragments}
    gc_before: dict[str, bytes] = {}
    for rel in sorted(plan.gc_paths):
        path = repo / rel
        if path.is_symlink() or not path.is_file():
            raise _DiffPreflightError(f"{rel}: diff GC target が存在しないか regular file でない")
        receipt = receipts.get(rel)
        before = path.read_bytes()
        if receipt is None or _sha256(before) != receipt.content_sha256:
            raise _DiffPreflightError(f"{rel}: diff GC target content が plan と不一致")
        gc_before[rel] = before

    for target in plan.targets:
        path = target.path.encode("utf-8")
        yield (
            f"# before_sha256={target.before_sha256} after_sha256={target.after_sha256}\n"
        ).encode("ascii")
        yield from _diff_lines(
            target_before[target.path],
            target.after_bytes,
            fromfile=b"a/" + path if target.before_exists else b"/dev/null",
            tofile=b"b/" + path,
        )

    empty_sha = _sha256(b"")
    for rel in sorted(plan.gc_paths):
        before = gc_before[rel]
        path = rel.encode("utf-8")
        yield f"# before_sha256={_sha256(before)} after_sha256={empty_sha}\n".encode("ascii")
        yield from _diff_lines(
            before,
            b"",
            fromfile=b"a/" + path,
            tofile=b"/dev/null",
        )


def _task_id_arg(value: str) -> str:
    if TASK_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError(
            "canonical task ID like '[T-001]' is required"
        )
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="spool fragment を canonical 台帳へ fold する")
    parser.add_argument("--dry-run", action="store_true", help="計画 JSON のみを出力し、変更しない")
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help=(
            "dry-run の unified diff を stderr へ出す（人間向け表示であり JSON channel ではない。"
            "端末制御 byte は可逆な \\xNN 表記へ escape する）"
        ),
    )
    parser.add_argument(
        "--fold-date",
        help="canonical に使う ISO date。dry-run と apply で同じ値を渡せば同じ plan になる",
    )
    parser.add_argument(
        "--base-digest",
        metavar="TASK_ID",
        type=_task_id_arg,
        help=(
            "worklog item 本文の carry 解決済み digest を1行出力する "
            "（FoldOrigin.base の git commit OID とは別概念）"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.base_digest is not None:
        if args.dry_run:
            parser.error("--base-digest cannot be combined with --dry-run")
        if args.show_diff:
            parser.error("--base-digest cannot be combined with --show-diff")
        if args.fold_date is not None:
            parser.error("--base-digest cannot be combined with --fold-date")
    if args.show_diff and not args.dry_run:
        parser.error("--show-diff requires --dry-run")
    repo = Path(__file__).resolve().parents[1]
    try:
        if args.base_digest is not None:
            print(_resolve_base_digest(repo, args.base_digest))
            return 0
        state_path = _state_path(repo)
        if not args.dry_run and state_path.exists():
            plan = _state_plan(_load_state(state_path))
        else:
            plan = plan_fold(repo, fold_date=args.fold_date)
        if args.dry_run:
            if args.show_diff:
                for chunk in _iter_plan_diff(repo, plan):
                    sys.stderr.buffer.write(chunk)
            print(json.dumps(plan.as_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True))
            return 0
        result = apply_fold(repo, plan)
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return 0
    except SpoolValidationError as exc:
        print(json.dumps({"issues": [dataclasses.asdict(issue) for issue in exc.issues], "status": "invalid"}, ensure_ascii=False, separators=(",", ":"), sort_keys=True), file=sys.stderr)
        return 1
    except (TransactionError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc), "status": "transaction-error"}, ensure_ascii=False, separators=(",", ":"), sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
