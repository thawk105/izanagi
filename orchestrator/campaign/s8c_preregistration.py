# -*- coding: utf-8 -*-
"""Phase 3 段 8c 事前登録の静的発効判定と条件契約 ledger。

第一級の読取 API は指定 commit の blob を評価する :func:`activation_report_at` と
:func:`effective_at` である。worktree 読取は revision record の準備と parser の補助 API
だけに限定する。

保護対象は §1, §2, §3, §4, §6, §7 の本文全体（配下の H3 を含む）、§5 の
欄名集合、evidence contract である。§0 は表記上の補助規約なので意図的に保護 hash
から除外する。§5 の値は記入によって変化するため保護せず、発効時に別途検査する。

この module は approval、active pointer、revocation を持たない。発効は commit C の
tree から毎回導出される値である。
"""
from __future__ import annotations

import argparse
import dataclasses
import enum
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence


SOURCE_PATH = "docs/phase3-8c-preregistration.md"
FREEZE_DIR = "output/s8c-preregistration/condition-freeze"
FREEZE_BASENAME = "condition-freeze.v1"
EVIDENCE_CONTRACT_PATH = (
    "orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json"
)
EVALUATOR_MODULE_PATH = "orchestrator/campaign/s8c_preregistration_evidence.py"
CORE_MODULE_PATH = "orchestrator/campaign/s8c_preregistration.py"
SCHEMA_VERSION = "s8c-prereg-condition-freeze/v1"
NORMALIZATION_VERSION = "s8c-prereg-markdown/v2"
PREDICATE_IDS = tuple(f"C{number:02d}" for number in range(1, 13))

_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_OBJECT_ID_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_GENERATION_RE = re.compile(
    rf"{re.escape(FREEZE_DIR)}/{re.escape(FREEZE_BASENAME)}\.g([1-9][0-9]*)\.json\Z"
)
_RULING_RE = re.compile(r"D[1-9][0-9]*\Z")
_ATX_RE = re.compile(r"^( {0,3})(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_TOP_ITEM_RE = re.compile(r"^ {0,3}([0-9]+)[.)][ \t]+(.*)$")
_UNORDERED_ITEM_RE = re.compile(r"^ {0,3}[-+*][ \t]+(.*)$")
_LIST_CONTAINER_RE = re.compile(
    r"^ {0,3}(?:[0-9]+[.)]|[-+*])[ \t]+(?P<content>.*)$"
)
_NESTED_ITEM_RE = re.compile(r"^ {4,}([0-9]+)[.)][ \t]+")
_FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)$")
_REFERENCE_DEF_RE = re.compile(r"^ {0,3}\[[^\]\r\n]+\]:[ \t]*\S+")
_RAW_HTML_RE = re.compile(
    r"<!--|<![A-Z][^>]*>|<\?[^>]*\?>|<!\[CDATA\[|"
    r"</?[A-Za-z][A-Za-z0-9-]*(?:[ \t][^<>]*|[ \t]*/|/)?>"
)
_PLACEHOLDER_RE = re.compile(
    r"^(?:未記入(?:[ \t]*(?:\([^)]*\)|（[^）]*）|\[[^]]*\]|【[^】]*】))?"
    r"|\(未記入\)|（未記入）|\[未記入\]|【未記入】)$"
)
_FREEZE_KEYS = frozenset(
    {
        "schema_version",
        "normalization_version",
        "generation_number",
        "supersedes_sha256",
        "source_path",
        "section5_field_names_sha256",
        "section6_conditions_sha256",
        "section6_condition_hashes",
        "normative_body_sha256",
        "evidence_contract_sha256",
        "protected_sha256",
        "revision_reason",
        "ruling_reference",
    }
)
_GIT_HARDEN = ("-c", "core.useReplaceRefs=false")
GIT_TIMEOUT_SECONDS = 15.0
MAX_GENERATIONS = 1024
MAX_COMMITS = 10_000
MAX_BLOB_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BLOB_BYTES = 64 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = MAX_TOTAL_BLOB_BYTES + 4 * 1024 * 1024
MAX_GIT_INPUT_BYTES = 16 * 1024 * 1024
MAX_BATCH_REQUESTS = 50_000
# RATE が採用する実測は during phase 全体の最大 0.588973 秒 / 7,044 要求
# = 8.3613e-5 秒/要求。この最大サンプルは worker 0 であり、worker 実在に限った最大は
# 0.445290 秒（6.3216e-5 秒/要求）。大きい方を採るのは予算を保守側に出す意図的な選択で、
# 15 秒での打ち切り観測から逆算した 25.6 倍と安全係数 4 を掛け、0.0086 へ上向きに丸めた。
GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST = 0.0086
# CAP は RATE から独立した絶対値。受入全走 1 走の 1055〜1408 秒に対して 1/4 未満、
# 計算ノード既定 walltime 30 分に対して 1/6 以下とする。凍結された生実測は
# output/insights/2026-08-09_t553-git-budget/。commit 数が約 4,700（実測時の 2 倍）を
# 超える、generation が g2 以上になる、または同じ nodeid で再発した場合に再較正する。
GIT_TIMEOUT_CAP_SECONDS = 300.0
_DOMAIN_FIELD_NAMES = b"izanagi:s8c:section5-field-names:v1\0"
_DOMAIN_CONDITIONS = b"izanagi:s8c:section6-conditions:v1\0"
_DOMAIN_CONDITION = b"izanagi:s8c:section6-condition:v1\0"
_DOMAIN_NORMATIVE = b"izanagi:s8c:normative-body:v1\0"
_DOMAIN_EVIDENCE = b"izanagi:s8c:evidence-contract:v1\0"
_DOMAIN_PROTECTED = b"izanagi:s8c:protected-contract:v1\0"
_DOMAIN_ACTIVATION_REPORT = b"izanagi:s8c:activation-report:v1\0"


class PreregistrationError(RuntimeError):
    """fail-closed 拒否。機械判定用の ``reason`` を持つ。"""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(f"[{reason}] {detail}" if detail else reason)


class FieldStatus(str, enum.Enum):
    FILLED = "FILLED"
    UNFILLED = "UNFILLED"
    INVALID = "INVALID"


class PredicateStatus(str, enum.Enum):
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    EVIDENCE_UNDEFINED = "EVIDENCE_UNDEFINED"
    ERROR = "ERROR"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True)
class EvidenceRef:
    path: str
    blob_sha256: str


@dataclass(frozen=True)
class PredicateResult:
    id: str
    status: PredicateStatus
    reason_code: str
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))


class PredicateRegistry(Protocol):
    """単位 B が実装する registry の最小 protocol。"""

    def evaluate_all(
        self, commit: str, *, repo_root: Path
    ) -> Sequence[PredicateResult]: ...


@dataclass(frozen=True)
class Section5Finding:
    name: str
    status: FieldStatus
    reason_code: str


@dataclass(frozen=True)
class MarkdownContract:
    section5_field_names: frozenset[str]
    section5_findings: tuple[Section5Finding, ...]
    section6_conditions: tuple[tuple[int, str], ...]
    normative_body: str
    section5_field_names_sha256: str
    section6_conditions_sha256: str
    section6_condition_hashes: tuple[tuple[int, str], ...]
    normative_body_sha256: str

    def protected_sha256(self, evidence_contract_sha256: str) -> str:
        _require_hash(evidence_contract_sha256, "evidence_contract_sha256")
        preimage = {
            "evidence_contract_sha256": evidence_contract_sha256,
            "normative_body_sha256": self.normative_body_sha256,
            "section5_field_names_sha256": self.section5_field_names_sha256,
            "section6_conditions_sha256": self.section6_conditions_sha256,
        }
        return _sha256(_DOMAIN_PROTECTED + _canonical_bytes(preimage))


@dataclass(frozen=True)
class FreezeRecord:
    generation_number: int
    supersedes_sha256: Optional[str]
    section5_field_names_sha256: str
    section6_conditions_sha256: str
    section6_condition_hashes: tuple[tuple[int, str], ...]
    normative_body_sha256: str
    evidence_contract_sha256: str
    protected_sha256: str
    revision_reason: str
    ruling_reference: Optional[str]
    raw_sha256: str
    raw: bytes


@dataclass(frozen=True)
class FreezeValidation:
    commit: str
    generation_number: int
    protected_sha256: str
    tip_record_sha256: str
    contract: MarkdownContract


@dataclass(frozen=True)
class ActivationReport:
    commit: str
    condition_freeze_valid: bool
    freeze_generation: Optional[int]
    protected_sha256: Optional[str]
    freeze_reason_code: str
    section5_findings: tuple[Section5Finding, ...]
    predicates: tuple[PredicateResult, ...]
    core_module_blob_sha256: Optional[str]
    evaluator_module_blob_sha256: Optional[str]
    effective: bool


def _define_effective_type():
    seal = object()

    @dataclass(frozen=True, slots=True, init=False)
    class EffectivePreregistration:
        """発効成功時だけ private factory が生成する immutable capability。

        Python の型は信頼境界ではなく、完全な偽造不能性を主張しない。consumer は
        authority としてこの object 単独を信用せず、利用のたびに ``commit`` C から
        :func:`activation_report_at` を再計算し、C と ``report_digest_sha256`` の双方を
        照合しなければならない。
        """

        _report: ActivationReport
        _report_digest_sha256: str

        def __init__(
            self,
            report: ActivationReport,
            report_digest_sha256: str,
            *,
            _seal: object = None,
        ) -> None:
            if (
                _seal is not seal
                or not isinstance(report, ActivationReport)
                or not report.effective
            ):
                raise TypeError("EffectivePreregistration は effective_at() だけが生成できる")
            _require_hash(report_digest_sha256, "report_digest_sha256")
            object.__setattr__(self, "_report", report)
            object.__setattr__(self, "_report_digest_sha256", report_digest_sha256)

        @property
        def report(self) -> ActivationReport:
            return self._report

        @property
        def commit(self) -> str:
            return self._report.commit

        @property
        def report_digest_sha256(self) -> str:
            return self._report_digest_sha256

        def __repr__(self) -> str:
            return f"EffectivePreregistration(commit={self.commit!r})"

    def construct(report: ActivationReport):
        return EffectivePreregistration(
            report,
            _activation_report_digest(report),
            _seal=seal,
        )

    return EffectivePreregistration, construct


EffectivePreregistration, _construct_effective = _define_effective_type()
EffectivePreregistration.__name__ = "EffectivePreregistration"
EffectivePreregistration.__qualname__ = "EffectivePreregistration"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise PreregistrationError("schema-hash", f"{label} が lowercase SHA-256 でない")
    return value


def _reject_constant(token: str):
    raise PreregistrationError("json-nan", f"非有限 JSON 数値: {token}")


def _no_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreregistrationError("json-duplicate-key", f"duplicate key: {key!r}")
        result[key] = value
    return result


def _strict_json(raw: bytes, *, what: str) -> Any:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise PreregistrationError("bad-utf8", f"{what} が UTF-8 でない") from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        raise PreregistrationError("bad-json", f"{what}: {exc}") from exc


def evidence_contract_sha256(raw: bytes) -> str:
    """evidence contract の JSON 意味内容を canonical 化して hash する。"""
    value = _strict_json(raw, what=EVIDENCE_CONTRACT_PATH)
    try:
        canonical = _canonical_bytes(value)
    except (TypeError, ValueError) as exc:
        raise PreregistrationError("evidence-contract-json", str(exc)) from exc
    return _sha256(_DOMAIN_EVIDENCE + canonical)


def _normalize_newlines(raw: bytes, *, what: str) -> str:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise PreregistrationError("bad-utf8", f"{what} が UTF-8 でない") from exc
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


@dataclass(frozen=True)
class _FenceSpec:
    marker: str
    width: int
    indent: int
    info: str


def _fence_opener(line: str) -> Optional[_FenceSpec]:
    """CommonMark の opening code fence なら走査に必要な属性を返す。"""
    match = _FENCE_RE.fullmatch(line)
    if match is None:
        return None
    run = match.group(2)
    info = match.group(3)
    # backtick fence の info string は backtick を含められない。tilde には同制約が無い。
    if run[0] == "`" and "`" in info:
        return None
    return _FenceSpec(
        marker=run[0],
        width=len(run),
        indent=len(match.group(1)),
        info=info.strip(" \t"),
    )


def _is_fence_closer(line: str, opener: _FenceSpec) -> bool:
    """``opener`` と marker が同じで幅以上の CommonMark closing fence か。"""
    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    if indent > 3:
        return False
    run = len(stripped) - len(stripped.lstrip(opener.marker))
    return run >= opener.width and not stripped[run:].strip(" \t")


def _fence_map(
    lines: Sequence[str], *, reject_container_fences: bool = True
) -> tuple[bool, ...]:
    opener: Optional[_FenceSpec] = None
    container_indents: list[int] = []
    result: list[bool] = []
    for number, line in enumerate(lines, 1):
        if opener is None:
            result.append(False)

            if reject_container_fences and line.strip():
                leading = len(line) - len(line.lstrip(" "))
                while container_indents and leading < container_indents[-1]:
                    container_indents.pop()

                bases = [0, *container_indents]
                matched_container: Optional[tuple[int, re.Match[str]]] = None
                for base in reversed(bases):
                    if base > leading:
                        continue
                    match = _LIST_CONTAINER_RE.fullmatch(line[base:])
                    if match is not None:
                        matched_container = (base, match)
                        break
                    if base and _fence_opener(line[base:]) is not None:
                        raise PreregistrationError(
                            "container-fence",
                            f"list continuation 内の fenced code (line {number})",
                        )
                if matched_container is not None:
                    base, match = matched_container
                    content = match.group("content")
                    if _fence_opener(content) is not None:
                        raise PreregistrationError(
                            "container-fence",
                            f"list item 内の fenced code (line {number})",
                        )
                    content_indent = base + match.start("content")
                    container_indents = [
                        indent for indent in container_indents if indent <= base
                    ]
                    container_indents.append(content_indent)

            opener = _fence_opener(line)
            continue
        result.append(True)
        if _is_fence_closer(line, opener):
            opener = None
    if opener is not None:
        raise PreregistrationError("unclosed-fence", "fenced code block が閉じていない")
    return tuple(result)


def _reject_hidden_markup(lines: Sequence[str], fenced: Sequence[bool]) -> None:
    code_delimiter: Optional[str] = None
    for number, (line, in_fence) in enumerate(zip(lines, fenced), 1):
        if in_fence or _fence_opener(line) is not None:
            continue
        masked: list[str] = []
        index = 0
        while index < len(line):
            if code_delimiter is not None:
                close = line.find(code_delimiter, index)
                if close < 0:
                    masked.append(" " * (len(line) - index))
                    index = len(line)
                    continue
                masked.append(" " * (close + len(code_delimiter) - index))
                index = close + len(code_delimiter)
                code_delimiter = None
                continue
            if line[index] == "\\" and index + 1 < len(line):
                masked.append(line[index : index + 2])
                index += 2
                continue
            if line[index] != "`":
                masked.append(line[index])
                index += 1
                continue
            end = index
            while end < len(line) and line[end] == "`":
                end += 1
            code_delimiter = line[index:end]
            masked.append(" " * len(code_delimiter))
            index = end
        visible = "".join(masked)
        if _REFERENCE_DEF_RE.match(visible):
            raise PreregistrationError(
                "reference-link-definition", f"reference link definition (line {number})"
            )
        if _RAW_HTML_RE.search(visible):
            raise PreregistrationError("raw-html", f"raw HTML (line {number})")


def _strip_code_spans(text: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            if text[index] == "\\" and index + 1 < len(text):
                next_char = text[index + 1]
                if next_char in r"\\`*_{}[]()#+-.!|>":
                    output.append(next_char)
                    index += 2
                    continue
            output.append(text[index])
            index += 1
            continue
        end_run = index
        while end_run < len(text) and text[end_run] == "`":
            end_run += 1
        delimiter = text[index:end_run]
        close = text.find(delimiter, end_run)
        if close < 0:
            raise PreregistrationError("unclosed-code-span", "inline code span が閉じていない")
        content = text[end_run:close].replace("\n", " ")
        if content.startswith(" ") and content.endswith(" ") and content.strip(" "):
            content = content[1:-1]
        output.append(content.replace("*", "\ue000").replace("_", "\ue001"))
        index = close + len(delimiter)
    return "".join(output)


def _strip_balanced_emphasis(text: str) -> str:
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"(?<!\\)(\*\*)(?=\S)(.+?\S)\1", r"\2", text)
        text = re.sub(r"(?<![\\\w])(__)(?=\S)(.+?\S)\1(?!\w)", r"\2", text)
        text = re.sub(
            r"(?<![\\\w])([*_])(?=\S)(.+?\S)\1(?!\w)", r"\2", text
        )
    return text


def _normalize_inline(text: str) -> str:
    text = _strip_code_spans(text)
    text = _strip_balanced_emphasis(text)
    return " ".join(text.split()).replace("\ue000", "*").replace("\ue001", "_")


def _normalize_fragment(lines: Sequence[str]) -> str:
    """layout を潰しつつ Markdown block の node kind と heading 文言を残す。"""
    fenced = _fence_map(lines)
    nodes: list[dict[str, Any]] = []
    paragraph: list[str] = []
    list_kind: Optional[str] = None
    list_ordinal: Optional[int] = None
    list_parts: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = _normalize_inline(" ".join(paragraph))
            if text:
                nodes.append({"kind": "paragraph", "text": text})
            paragraph.clear()

    def flush_list_item() -> None:
        nonlocal list_kind, list_ordinal
        if list_kind is not None:
            node: dict[str, Any] = {
                "kind": "list_item",
                "list_kind": list_kind,
                "text": _normalize_inline(" ".join(list_parts)),
            }
            if list_ordinal is not None:
                node["ordinal"] = list_ordinal
            nodes.append(node)
            list_kind = None
            list_ordinal = None
            list_parts.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        fence_opener = _fence_opener(line)
        if fence_opener is not None and not fenced[index]:
            flush_paragraph()
            flush_list_item()
            content: list[str] = []
            cursor = index + 1
            while cursor < len(lines):
                if fenced[cursor] and _is_fence_closer(lines[cursor], fence_opener):
                    break
                content_line = lines[cursor]
                leading = len(content_line) - len(content_line.lstrip(" "))
                content.append(content_line[min(leading, fence_opener.indent) :])
                cursor += 1
            nodes.append(
                {
                    "kind": "fenced_code",
                    "info": " ".join(fence_opener.info.split()),
                    "text": "\n".join(content),
                }
            )
            index = cursor + 1
            continue
        if fenced[index]:
            raise PreregistrationError("fence-structure", f"unexpected fenced line {index + 1}")
        heading = _ATX_RE.match(line)
        if heading:
            flush_paragraph()
            flush_list_item()
            nodes.append(
                {
                    "kind": "heading",
                    "level": len(heading.group(2)),
                    "text": _normalize_inline(heading.group(3)),
                }
            )
            index += 1
            continue
        ordered = _TOP_ITEM_RE.match(line)
        unordered = _UNORDERED_ITEM_RE.match(line)
        if ordered or unordered:
            flush_paragraph()
            flush_list_item()
            list_kind = "ordered" if ordered else "unordered"
            list_ordinal = int(ordered.group(1)) if ordered else None
            list_parts.append((ordered or unordered).group(2 if ordered else 1))
            index += 1
            continue
        if list_kind is not None and line[:1].isspace() and line.strip():
            list_parts.append(line.strip())
            index += 1
            continue
        if not line.strip():
            index += 1
            continue
        flush_list_item()
        paragraph.append(line.strip())
        index += 1
    flush_paragraph()
    flush_list_item()
    return _canonical_bytes(nodes).decode("utf-8")


def _section_bounds(lines: Sequence[str], fenced: Sequence[bool]) -> dict[int, tuple[int, int]]:
    found: dict[int, list[tuple[int, int]]] = {number: [] for number in range(1, 8)}
    for index, (line, in_fence) in enumerate(zip(lines, fenced)):
        if in_fence:
            continue
        match = _ATX_RE.match(line)
        if not match:
            continue
        title = match.group(3).strip()
        section_match = re.match(r"([0-7])(?:[.．][ \t]+|[ \t]+)", title)
        if not section_match:
            continue
        number = int(section_match.group(1))
        if number == 0:
            if len(match.group(2)) != 2:
                raise PreregistrationError("heading-level", "§0 heading は H2 でなければならない")
            continue
        found[number].append((index, len(match.group(2))))
    positions: list[int] = []
    for number in range(1, 8):
        occurrences = found[number]
        if not occurrences:
            raise PreregistrationError("section-missing", f"§{number} が無い")
        if len(occurrences) != 1:
            raise PreregistrationError("section-duplicate", f"§{number} が重複している")
        position, level = occurrences[0]
        if level != 2:
            raise PreregistrationError("heading-level", f"§{number} heading は H2 でない")
        positions.append(position)
    if positions != sorted(positions):
        raise PreregistrationError("section-order", "§1..§7 の順序が逆転している")
    return {
        number: (positions[number - 1] + 1, positions[number] if number < 7 else len(lines))
        for number in range(1, 8)
    }


def split_markdown_table_row(row: str) -> list[str]:
    """GFM table row を escape と code span を意識して分割する公開 lexer。"""
    cells: list[str] = []
    current: list[str] = []
    separators: list[int] = []
    index = 0
    while index < len(row):
        char = row[index]
        if char == "`":
            end_run = index
            while end_run < len(row) and row[end_run] == "`":
                end_run += 1
            delimiter = row[index:end_run]
            close = row.find(delimiter, end_run)
            if close < 0:
                raise PreregistrationError("unclosed-code-span", "table code span が閉じていない")
            current.append(row[index : close + len(delimiter)])
            index = close + len(delimiter)
            continue
        if char == "\\" and index + 1 < len(row) and row[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(current))
            current = []
            separators.append(index)
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current))
    first_nonspace = len(row) - len(row.lstrip())
    last_nonspace = len(row.rstrip()) - 1
    if separators and separators[0] == first_nonspace and cells and not cells[0].strip():
        cells.pop(0)
    if separators and separators[-1] == last_nonspace and cells and not cells[-1].strip():
        cells.pop()
    return [cell.strip() for cell in cells]


def _parse_section5(
    lines: Sequence[str], fenced: Sequence[bool]
) -> tuple[frozenset[str], tuple[Section5Finding, ...]]:
    tables: list[tuple[int, list[str]]] = []
    for index in range(len(lines) - 1):
        if fenced[index] or fenced[index + 1]:
            continue
        try:
            header = split_markdown_table_row(lines[index])
            delimiter = split_markdown_table_row(lines[index + 1])
        except PreregistrationError:
            raise
        if [_normalize_inline(cell) for cell in header] != ["欄", "値"]:
            continue
        if len(delimiter) != 2 or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in delimiter):
            raise PreregistrationError("table-delimiter", "§5 table delimiter が不正")
        tables.append((index, header))
    if not tables:
        raise PreregistrationError("table-missing", "§5 の 欄/値 table が無い")
    if len(tables) != 1:
        raise PreregistrationError("table-duplicate", "§5 の 欄/値 table が複数ある")
    start = tables[0][0] + 2
    findings: list[Section5Finding] = []
    names: set[str] = set()
    for line, in_fence in zip(lines[start:], fenced[start:]):
        if in_fence:
            raise PreregistrationError("table-fence", "§5 table 内に fenced code がある")
        if not line.strip():
            break
        if "|" not in line:
            break
        cells = split_markdown_table_row(line)
        if len(cells) != 2:
            raise PreregistrationError("table-columns", "§5 data row が exact 2 列でない")
        name = _normalize_inline(cells[0])
        if not name:
            raise PreregistrationError("field-empty", "§5 欄名が空")
        if name in names:
            raise PreregistrationError("field-duplicate", f"§5 欄名が重複: {name!r}")
        names.add(name)
        status, reason = _classify_section5_value(cells[1])
        findings.append(Section5Finding(name, status, reason))
    if not findings:
        raise PreregistrationError("table-empty", "§5 table に data row が無い")
    return frozenset(names), tuple(findings)


def _classify_section5_value(raw_value: str) -> tuple[FieldStatus, str]:
    normalized = _normalize_inline(raw_value)
    if _PLACEHOLDER_RE.fullmatch(normalized):
        return FieldStatus.UNFILLED, "placeholder"
    match = re.fullmatch(r"(`+)([\s\S]*)\1", raw_value.strip())
    if not match:
        return FieldStatus.INVALID, "canonical-json-code-span-required"
    delimiter = match.group(1)
    content = match.group(2)
    if delimiter in content:
        return FieldStatus.INVALID, "ambiguous-code-span"
    raw = content.encode("utf-8")
    try:
        value = _strict_json(raw, what="§5 value")
        canonical = _canonical_bytes(value)
    except (PreregistrationError, TypeError, ValueError):
        return FieldStatus.INVALID, "invalid-json"
    if canonical != raw:
        return FieldStatus.INVALID, "noncanonical-json"
    if value is None:
        return FieldStatus.UNFILLED, "json-null"
    if isinstance(value, str):
        candidate = " ".join(value.split())
        if not candidate:
            return FieldStatus.UNFILLED, "json-empty-string"
        if _PLACEHOLDER_RE.fullmatch(candidate):
            return FieldStatus.UNFILLED, "json-placeholder-string"
    if isinstance(value, (list, dict)) and not value:
        return FieldStatus.UNFILLED, "json-empty-container"
    return FieldStatus.FILLED, "canonical-json"


def _parse_section6(
    lines: Sequence[str], fenced: Sequence[bool]
) -> tuple[tuple[int, str], ...]:
    markers: list[tuple[int, int, str]] = []
    for index, (line, in_fence) in enumerate(zip(lines, fenced)):
        if in_fence:
            continue
        match = _TOP_ITEM_RE.match(line)
        if match:
            markers.append((index, int(match.group(1)), match.group(2)))
    numbers = [number for _, number, _ in markers]
    if numbers != list(range(1, 13)):
        nested = [
            int(match.group(1))
            for line, in_fence in zip(lines, fenced)
            if not in_fence and (match := _NESTED_ITEM_RE.match(line))
        ]
        reason = "condition-nested-replacement" if nested else "condition-numbering"
        raise PreregistrationError(reason, f"§6 top-level numbers={numbers!r}; exact 1..12 が必要")
    conditions: list[tuple[int, str]] = []
    for marker_index, (line_index, number, first) in enumerate(markers):
        limit = markers[marker_index + 1][0] if marker_index + 1 < len(markers) else len(lines)
        continuation: list[str] = [first]
        saw_blank = False
        for line, in_fence in zip(
            lines[line_index + 1 : limit], fenced[line_index + 1 : limit]
        ):
            if not line.strip():
                saw_blank = True
                continue
            if not in_fence and _ATX_RE.match(line):
                break
            if saw_blank and not line[:1].isspace():
                break
            continuation.append(line.strip())
            saw_blank = False
        text = _normalize_fragment(continuation)
        if not text:
            raise PreregistrationError("condition-empty", f"§6 condition {number} が空")
        conditions.append((number, text))
    return tuple(conditions)


def parse_preregistration_markdown(raw: bytes) -> MarkdownContract:
    """UTF-8 Markdown bytes から保護契約と §5 所見を抽出する。"""
    text = _normalize_newlines(raw, what=SOURCE_PATH)
    if any(marker in text for marker in ("\ue000", "\ue001", "\ue002")):
        raise PreregistrationError("normalization-sentinel", "reserved private-use character")
    lines = text.split("\n")
    fenced = _fence_map(lines)
    _reject_hidden_markup(lines, fenced)
    # §0 を hash には含めないが、未閉 code span による後続構造の隠蔽は文書全体で拒否する。
    _normalize_fragment(lines)
    bounds = _section_bounds(lines, fenced)
    section5_slice = slice(*bounds[5])
    section6_slice = slice(*bounds[6])
    section5_names, findings = _parse_section5(lines[section5_slice], fenced[section5_slice])
    conditions = _parse_section6(lines[section6_slice], fenced[section6_slice])
    normative_sections = [
        {
            "section": number,
            "text": _normalize_fragment(
                lines[bounds[number][0] - 1 : bounds[number][1]]
            ),
        }
        for number in (1, 2, 3, 4, 6, 7)
    ]
    normative_body = "\n".join(
        f"§{entry['section']} {entry['text']}" for entry in normative_sections
    )
    sorted_names = sorted(section5_names, key=lambda value: value.encode("utf-8"))
    field_hash = _sha256(_DOMAIN_FIELD_NAMES + _canonical_bytes(sorted_names))
    condition_docs = [{"number": number, "text": value} for number, value in conditions]
    conditions_hash = _sha256(_DOMAIN_CONDITIONS + _canonical_bytes(condition_docs))
    individual = tuple(
        (
            number,
            _sha256(
                _DOMAIN_CONDITION
                + _canonical_bytes({"number": number, "text": value})
            ),
        )
        for number, value in conditions
    )
    normative_hash = _sha256(_DOMAIN_NORMATIVE + _canonical_bytes(normative_sections))
    return MarkdownContract(
        section5_field_names=frozenset(section5_names),
        section5_findings=findings,
        section6_conditions=conditions,
        normative_body=normative_body,
        section5_field_names_sha256=field_hash,
        section6_conditions_sha256=conditions_hash,
        section6_condition_hashes=individual,
        normative_body_sha256=normative_hash,
    )


def parse_preregistration_worktree(repo_root: Path | str = Path(".")) -> MarkdownContract:
    """補助 API。commit 評価には使わず、revision 準備時の worktree を読む。"""
    return parse_preregistration_markdown(Path(repo_root, SOURCE_PATH).read_bytes())


def _git_timeout_budget_seconds(stdin: Optional[bytes]) -> float:
    requests = 0
    if stdin:
        requests = stdin.count(b"\n") + int(not stdin.endswith(b"\n"))
    requests = min(requests, MAX_BATCH_REQUESTS)
    return min(
        GIT_TIMEOUT_SECONDS + requests * GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST,
        GIT_TIMEOUT_CAP_SECONDS,
    )


def _git(root: Path, args: Sequence[str], *, stdin: Optional[bytes] = None) -> bytes:
    if stdin is not None and len(stdin) > MAX_GIT_INPUT_BYTES:
        raise PreregistrationError("git-input-limit", str(len(stdin)))
    timeout_seconds = _git_timeout_budget_seconds(stdin)
    try:
        with tempfile.TemporaryFile() as stdout:
            completed = subprocess.run(
                ["git", *_GIT_HARDEN, *args],
                cwd=root,
                input=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                check=True,
                timeout=timeout_seconds,
            )
            del completed
            size = stdout.tell()
            if size > MAX_GIT_OUTPUT_BYTES:
                raise PreregistrationError("git-output-limit", str(size))
            stdout.seek(0)
            return stdout.read()
    except subprocess.TimeoutExpired as exc:
        raise PreregistrationError("git-timeout") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"") or str(exc).encode("utf-8", "replace")
        raise PreregistrationError(
            "git-failed", detail.decode("utf-8", "replace").strip()
        ) from exc


def _git_text(root: Path, args: Sequence[str], *, stdin: Optional[bytes] = None) -> str:
    try:
        return _git(root, args, stdin=stdin).decode("utf-8", "strict").strip()
    except UnicodeError as exc:
        raise PreregistrationError("git-output-utf8", "git output が UTF-8 でない") from exc


def _assert_repository_safe(root: Path) -> None:
    if _git_text(root, ["rev-parse", "--is-shallow-repository"]) == "true":
        raise PreregistrationError("shallow-repository")
    if _git_text(root, ["for-each-ref", "--format=%(refname)", "refs/replace/"]):
        raise PreregistrationError("replace-refs")
    graft_path = _git_text(root, ["rev-parse", "--git-path", "info/grafts"])
    graft = Path(graft_path)
    if not graft.is_absolute():
        graft = root / graft
    if graft.exists():
        raise PreregistrationError("grafts")


def resolve_commit(repo_root: Path | str, commit: str = "HEAD") -> str:
    root = Path(repo_root).resolve()
    _assert_repository_safe(root)
    resolved = _git_text(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"])
    if not _OBJECT_ID_RE.fullmatch(resolved):
        raise PreregistrationError("bad-commit", resolved)
    return resolved


def read_blob_at(
    repo_root: Path | str, commit: str, path: str, *, required: bool = True
) -> Optional[bytes]:
    rendered = path if isinstance(path, str) else str(path)
    text = "".join((rendered,))
    if "\r" in text or "\n" in text:
        raise PreregistrationError("path-control-char")
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    spec = f"{resolved}:{text}"
    result = _git_text(root, ["cat-file", "--batch-check"], stdin=f"{spec}\n".encode())
    tokens = result.split()
    if tokens and tokens[-1] == "missing":
        if required:
            raise PreregistrationError("blob-missing", spec)
        return None
    if len(tokens) < 2 or not _OBJECT_ID_RE.fullmatch(tokens[0]) or tokens[1] != "blob":
        raise PreregistrationError("path-not-blob", f"{spec}: {result!r}")
    if len(tokens) < 3 or not tokens[2].isdigit():
        raise PreregistrationError("cat-file-header", result)
    if int(tokens[2]) > MAX_BLOB_BYTES:
        raise PreregistrationError("blob-byte-limit", text)
    return _git(root, ["cat-file", "blob", tokens[0]])


def parse_preregistration_at(
    repo_root: Path | str, commit: str = "HEAD"
) -> MarkdownContract:
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    return parse_preregistration_markdown(
        read_blob_at(root, resolved, SOURCE_PATH, required=True) or b""
    )


def generation_path(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise PreregistrationError("generation-number", repr(number))
    if number > MAX_GENERATIONS:
        raise PreregistrationError("generation-limit", repr(number))
    return f"{FREEZE_DIR}/{FREEZE_BASENAME}.g{number}.json"


def _load_freeze_record(raw: bytes, *, expected_generation: int) -> FreezeRecord:
    value = _strict_json(raw, what=generation_path(expected_generation))
    if not isinstance(value, dict):
        raise PreregistrationError("record-not-object")
    if frozenset(value) != _FREEZE_KEYS:
        raise PreregistrationError(
            "record-schema-keys", repr(sorted(set(value) ^ set(_FREEZE_KEYS)))
        )
    if _canonical_bytes(value) != raw:
        raise PreregistrationError("record-not-canonical")
    if value["schema_version"] != SCHEMA_VERSION:
        raise PreregistrationError("record-schema-version")
    if value["normalization_version"] != NORMALIZATION_VERSION:
        raise PreregistrationError("record-normalization-version")
    number = value["generation_number"]
    if isinstance(number, bool) or not isinstance(number, int) or number != expected_generation:
        raise PreregistrationError("record-generation-number")
    if value["source_path"] != SOURCE_PATH:
        raise PreregistrationError("record-source-path")
    supersedes = value["supersedes_sha256"]
    if number == 1:
        if supersedes is not None:
            raise PreregistrationError("record-g1-supersedes")
    else:
        _require_hash(supersedes, "supersedes_sha256")
    hashes = value["section6_condition_hashes"]
    if not isinstance(hashes, list) or len(hashes) != 12:
        raise PreregistrationError("record-condition-hashes")
    parsed_hashes: list[tuple[int, str]] = []
    for expected, item in enumerate(hashes, 1):
        if not isinstance(item, dict) or set(item) != {"number", "sha256"}:
            raise PreregistrationError("record-condition-hash-schema")
        if (
            isinstance(item["number"], bool)
            or not isinstance(item["number"], int)
            or item["number"] != expected
        ):
            raise PreregistrationError("record-condition-hash-number")
        parsed_hashes.append((expected, _require_hash(item["sha256"], "condition sha256")))
    reason = value["revision_reason"]
    if not isinstance(reason, str) or not reason.strip() or reason != reason.strip():
        raise PreregistrationError("record-revision-reason")
    ruling = value["ruling_reference"]
    if number >= 2:
        if not isinstance(ruling, str) or not _RULING_RE.fullmatch(ruling):
            raise PreregistrationError("record-ruling-reference")
    elif ruling is not None and (not isinstance(ruling, str) or not _RULING_RE.fullmatch(ruling)):
        raise PreregistrationError("record-ruling-reference")
    return FreezeRecord(
        generation_number=number,
        supersedes_sha256=supersedes,
        section5_field_names_sha256=_require_hash(
            value["section5_field_names_sha256"], "section5_field_names_sha256"
        ),
        section6_conditions_sha256=_require_hash(
            value["section6_conditions_sha256"], "section6_conditions_sha256"
        ),
        section6_condition_hashes=tuple(parsed_hashes),
        normative_body_sha256=_require_hash(
            value["normative_body_sha256"], "normative_body_sha256"
        ),
        evidence_contract_sha256=_require_hash(
            value["evidence_contract_sha256"], "evidence_contract_sha256"
        ),
        protected_sha256=_require_hash(value["protected_sha256"], "protected_sha256"),
        revision_reason=reason,
        ruling_reference=ruling,
        raw_sha256=_sha256(raw),
        raw=raw,
    )


@dataclass(frozen=True)
class _CommitGraph:
    commits: tuple[str, ...]
    parents: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class _HistoryState:
    protected_sha256: Optional[str]
    tip_generation_number: int
    tip_record_sha256: Optional[str]
    record_oids: tuple[str, ...]


def _commit_graph(root: Path, commit: str) -> _CommitGraph:
    output = _git_text(
        root,
        [
            "rev-list",
            "--reverse",
            "--topo-order",
            "--parents",
            f"--max-count={MAX_COMMITS + 1}",
            commit,
        ],
    )
    commits: list[str] = []
    parents: dict[str, tuple[str, ...]] = {}
    for line in output.splitlines():
        tokens = line.split()
        if not tokens:
            continue
        commits.append(tokens[0])
        parents[tokens[0]] = tuple(tokens[1:])
    if len(commits) > MAX_COMMITS:
        raise PreregistrationError("commit-limit", str(len(commits)))
    return _CommitGraph(tuple(commits), parents)


def _history_namespace_paths(root: Path, commit: str) -> set[str]:
    output = _git_text(
        root,
        ["log", "--format=", "--name-only", "--diff-merges=separate", commit, "--", FREEZE_DIR],
    )
    paths = {line.strip() for line in output.splitlines() if line.strip()}
    current = _git_text(root, ["ls-tree", "-r", "--name-only", commit, "--", FREEZE_DIR])
    paths.update(line.strip() for line in current.splitlines() if line.strip())
    for path in paths:
        if not _GENERATION_RE.fullmatch(path):
            raise PreregistrationError("freeze-namespace-unknown", path)
    return paths


def _batch_oids(
    root: Path, commits: Sequence[str], paths: Sequence[str]
) -> dict[tuple[str, str], Optional[str]]:
    if len(commits) * len(paths) > MAX_BATCH_REQUESTS:
        raise PreregistrationError(
            "batch-request-limit", str(len(commits) * len(paths))
        )
    requests = [(commit, path) for commit in commits for path in paths]
    if not requests:
        return {}
    stdin = "".join(f"{commit}:{path}\n" for commit, path in requests).encode("utf-8")
    output = _git(root, ["cat-file", "--batch-check"], stdin=stdin).decode("utf-8", "strict")
    lines = output.splitlines()
    if len(lines) != len(requests):
        raise PreregistrationError("cat-file-count")
    result: dict[tuple[str, str], Optional[str]] = {}
    for request, line in zip(requests, lines):
        tokens = line.split()
        if tokens and tokens[-1] == "missing":
            result[request] = None
        elif len(tokens) >= 3 and _OBJECT_ID_RE.fullmatch(tokens[0]) and tokens[1] == "blob":
            if not tokens[2].isdigit():
                raise PreregistrationError("cat-file-header", line)
            if int(tokens[2]) > MAX_BLOB_BYTES:
                raise PreregistrationError("blob-byte-limit", request[1])
            result[request] = tokens[0]
        else:
            raise PreregistrationError("path-not-blob", f"{request}: {line!r}")
    return result


def _batch_blob_bytes(root: Path, oids: Iterable[str]) -> dict[str, bytes]:
    requested = tuple(dict.fromkeys(oids))
    if not requested:
        return {}
    size_output = _git_text(
        root,
        ["cat-file", "--batch-check"],
        stdin="".join(f"{oid}\n" for oid in requested).encode(),
    )
    sizes: list[int] = []
    for expected, line in zip(requested, size_output.splitlines()):
        tokens = line.split()
        if (
            len(tokens) != 3
            or tokens[0] != expected
            or tokens[1] != "blob"
            or not tokens[2].isdigit()
        ):
            raise PreregistrationError("cat-file-header", repr(tokens))
        size = int(tokens[2])
        if size > MAX_BLOB_BYTES:
            raise PreregistrationError("blob-byte-limit", expected)
        sizes.append(size)
    if len(sizes) != len(requested):
        raise PreregistrationError("cat-file-count")
    if sum(sizes) > MAX_TOTAL_BLOB_BYTES:
        raise PreregistrationError("blob-total-byte-limit", str(sum(sizes)))
    output = _git(root, ["cat-file", "--batch"], stdin="".join(f"{oid}\n" for oid in requested).encode())
    result: dict[str, bytes] = {}
    offset = 0
    for expected in requested:
        end = output.find(b"\n", offset)
        if end < 0:
            raise PreregistrationError("cat-file-truncated")
        header = output[offset:end].decode("ascii", "strict").split()
        if len(header) != 3 or header[0] != expected or header[1] != "blob":
            raise PreregistrationError("cat-file-header", repr(header))
        size = int(header[2])
        start = end + 1
        stop = start + size
        if stop >= len(output) or output[stop : stop + 1] != b"\n":
            raise PreregistrationError("cat-file-size")
        result[expected] = output[start:stop]
        offset = stop + 1
    if offset != len(output):
        raise PreregistrationError("cat-file-extra")
    return result


def _assert_record_matches_contract(
    record: FreezeRecord, contract: MarkdownContract, evidence_sha256: str
) -> None:
    expected = {
        "section5_field_names_sha256": contract.section5_field_names_sha256,
        "section6_conditions_sha256": contract.section6_conditions_sha256,
        "section6_condition_hashes": contract.section6_condition_hashes,
        "normative_body_sha256": contract.normative_body_sha256,
        "evidence_contract_sha256": evidence_sha256,
        "protected_sha256": contract.protected_sha256(evidence_sha256),
    }
    for name, value in expected.items():
        if getattr(record, name) != value:
            raise PreregistrationError("record-protected-mismatch", name)


def _is_successor(newer: _HistoryState, older: _HistoryState) -> bool:
    if newer.tip_generation_number <= older.tip_generation_number:
        return False
    return newer.record_oids[: older.tip_generation_number] == older.record_oids


def _assert_history_transition(
    commit: str,
    state: _HistoryState,
    parent_states: Sequence[_HistoryState],
) -> None:
    """単一 commit の generation state 遷移だけを検査する。"""
    if not parent_states:
        if state.tip_generation_number not in (0, 1):
            raise PreregistrationError("generation-jump", commit)
        return
    if len(parent_states) == 1:
        parent = parent_states[0]
        if parent.tip_generation_number == 0:
            if state.tip_generation_number not in (0, 1):
                raise PreregistrationError("generation-jump", commit)
        elif state.tip_generation_number == parent.tip_generation_number:
            if state != parent:
                raise PreregistrationError("unrecorded-protected-change", commit)
        elif state.tip_generation_number == parent.tip_generation_number + 1:
            if state.protected_sha256 == parent.protected_sha256:
                raise PreregistrationError("spurious-revision", commit)
        else:
            raise PreregistrationError("generation-transition", commit)
        return
    if len(parent_states) == 2:
        left, right = parent_states
        if left == right:
            if state != left:
                raise PreregistrationError("merge-state", commit)
            return
        successor = (
            left
            if _is_successor(left, right)
            else right
            if _is_successor(right, left)
            else None
        )
        if successor is None or state != successor:
            raise PreregistrationError("merge-divergent-revision", commit)
        return
    raise PreregistrationError("octopus-merge", commit)


def _mask_html_comments_outside_fences(lines: Sequence[str]) -> tuple[str, ...]:
    """fenced code 内の literal は保ち、HTML comment だけを空白へ置換する。"""
    in_comment = False
    opener: Optional[_FenceSpec] = None
    visible_lines: list[str] = []
    for line in lines:
        if opener is not None:
            visible_lines.append(line)
            if _is_fence_closer(line, opener):
                opener = None
            continue

        visible = list(line)
        cursor = 0
        while cursor < len(line):
            if in_comment:
                end = line.find("-->", cursor)
                stop = len(line) if end < 0 else end + 3
                visible[cursor:stop] = " " * (stop - cursor)
                cursor = stop
                if end >= 0:
                    in_comment = False
                continue
            start = line.find("<!--", cursor)
            if start < 0:
                break
            end = line.find("-->", start + 4)
            stop = len(line) if end < 0 else end + 3
            visible[start:stop] = " " * (stop - start)
            cursor = stop
            in_comment = end < 0
        visible_line = "".join(visible)
        visible_lines.append(visible_line)
        if not in_comment:
            opener = _fence_opener(visible_line)
    return tuple(visible_lines)


def _assert_rulings_exist(root: Path, checks: Sequence[tuple[str, str]]) -> None:
    """改訂 commit 時点の canonical decisions 見出しを構造照合する。"""
    commits = tuple(dict.fromkeys(commit for commit, _ in checks))
    ledger_path = "docs/decisions.md"
    oids = _batch_oids(root, commits, [ledger_path])
    blobs = _batch_blob_bytes(root, (oid for oid in oids.values() if oid is not None))
    for commit, ruling in checks:
        oid = oids[(commit, ledger_path)]
        if oid is None:
            raise PreregistrationError("ruling-not-found", f"{ruling} at {commit}")
        try:
            text = blobs[oid].decode("utf-8", "strict")
        except UnicodeError as exc:
            raise PreregistrationError("ledger-bad-utf8", ledger_path) from exc
        heading = re.compile(rf"^## {re.escape(ruling)}\.")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = _mask_html_comments_outside_fences(normalized.split("\n"))
        fenced = _fence_map(lines, reject_container_fences=False)
        if not any(
            not in_fence and heading.match(line)
            for line, in_fence in zip(lines, fenced)
        ):
            raise PreregistrationError("ruling-not-found", f"{ruling} at {commit}")


def validate_condition_freeze_at(
    repo_root: Path | str, commit: str = "HEAD"
) -> FreezeValidation:
    """C の全祖先を state transition として検証し、C の freeze tip を返す。"""
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    graph = _commit_graph(root, resolved)
    namespace_paths = _history_namespace_paths(root, resolved)
    generations = sorted(int(_GENERATION_RE.fullmatch(path).group(1)) for path in namespace_paths)
    if not generations:
        raise PreregistrationError("freeze-missing")
    max_generation = max(generations)
    if max_generation > MAX_GENERATIONS or len(generations) > MAX_GENERATIONS:
        raise PreregistrationError("generation-limit", str(max_generation))
    generation_paths = [generation_path(number) for number in range(1, max_generation + 1)]
    paths = [SOURCE_PATH, EVIDENCE_CONTRACT_PATH, *generation_paths]
    oids = _batch_oids(root, graph.commits, paths)
    blobs = _batch_blob_bytes(root, (oid for oid in oids.values() if oid is not None))

    introductions: dict[int, list[str]] = {number: [] for number in range(1, max_generation + 1)}
    for number, path in enumerate(generation_paths, 1):
        seen_oids = {oids[(item, path)] for item in graph.commits if oids[(item, path)] is not None}
        if len(seen_oids) > 1:
            raise PreregistrationError("generation-mutated", path)
        for item in graph.commits:
            oid = oids[(item, path)]
            for parent in graph.parents[item]:
                if oids.get((parent, path)) is not None and oid is None:
                    raise PreregistrationError("generation-deleted", path)
            if oid is None:
                continue
            parents = graph.parents[item]
            if all(oids.get((parent, path)) is None for parent in parents):
                introductions[number].append(item)
        if len(introductions[number]) > 1:
            raise PreregistrationError("generation-fork", path)

    record_cache: dict[tuple[int, str], FreezeRecord] = {}
    contract_cache: dict[tuple[str, str], tuple[MarkdownContract, str]] = {}
    states: dict[str, _HistoryState] = {}
    records_by_commit: dict[str, tuple[FreezeRecord, ...]] = {}
    for item in graph.commits:
        present = [
            number
            for number, path in enumerate(generation_paths, 1)
            if oids[(item, path)] is not None
        ]
        if present and present != list(range(1, present[-1] + 1)):
            raise PreregistrationError("generation-gap", f"commit {item}: {present}")
        record_oids = tuple(
            oids[(item, generation_path(number))] for number in present
        )
        records: list[FreezeRecord] = []
        for number, oid in zip(present, record_oids):
            assert oid is not None
            key = (number, oid)
            if key not in record_cache:
                record_cache[key] = _load_freeze_record(blobs[oid], expected_generation=number)
            record = record_cache[key]
            if number > 1 and record.supersedes_sha256 != records[-1].raw_sha256:
                raise PreregistrationError("generation-supersedes", generation_path(number))
            records.append(record)
        records_by_commit[item] = tuple(records)
        protected: Optional[str] = None
        contract: Optional[MarkdownContract] = None
        evidence_sha: Optional[str] = None
        if present:
            source_oid = oids[(item, SOURCE_PATH)]
            evidence_oid = oids[(item, EVIDENCE_CONTRACT_PATH)]
            if source_oid is None or evidence_oid is None:
                raise PreregistrationError("protected-source-missing", item)
            cache_key = (source_oid, evidence_oid)
            if cache_key not in contract_cache:
                parsed = parse_preregistration_markdown(blobs[source_oid])
                contract_cache[cache_key] = (
                    parsed,
                    evidence_contract_sha256(blobs[evidence_oid]),
                )
            contract, evidence_sha = contract_cache[cache_key]
            _assert_record_matches_contract(records[-1], contract, evidence_sha)
            protected = contract.protected_sha256(evidence_sha)
        state = _HistoryState(
            protected,
            present[-1] if present else 0,
            records[-1].raw_sha256 if records else None,
            tuple(oid for oid in record_oids if oid is not None),
        )
        parents = graph.parents[item]
        parent_states = [states[parent] for parent in parents]
        _assert_history_transition(item, state, parent_states)
        states[item] = state

    ruling_checks: list[tuple[str, str]] = []
    for number in range(2, max_generation + 1):
        intro = introductions[number]
        if len(intro) != 1:
            raise PreregistrationError("generation-introduction", generation_path(number))
        record = records_by_commit[intro[0]][number - 1]
        assert record.ruling_reference is not None
        ruling_checks.append((intro[0], record.ruling_reference))
    _assert_rulings_exist(root, ruling_checks)

    final_state = states[resolved]
    if final_state.tip_generation_number == 0:
        raise PreregistrationError("freeze-missing-at-commit")
    final_records = records_by_commit[resolved]
    source_oid = oids[(resolved, SOURCE_PATH)]
    evidence_oid = oids[(resolved, EVIDENCE_CONTRACT_PATH)]
    assert source_oid is not None and evidence_oid is not None
    contract, evidence_sha = contract_cache[(source_oid, evidence_oid)]
    return FreezeValidation(
        commit=resolved,
        generation_number=final_state.tip_generation_number,
        protected_sha256=contract.protected_sha256(evidence_sha),
        tip_record_sha256=final_records[-1].raw_sha256,
        contract=contract,
    )


def condition_freeze_valid_at(repo_root: Path | str, commit: str = "HEAD") -> bool:
    try:
        validate_condition_freeze_at(repo_root, commit)
    except PreregistrationError:
        return False
    return True


def _undefined_predicates(reason: str = "registry-unavailable") -> tuple[PredicateResult, ...]:
    return tuple(
        PredicateResult(identifier, PredicateStatus.EVIDENCE_UNDEFINED, reason, ())
        for identifier in PREDICATE_IDS
    )


def _normalize_predicate_results(results: Iterable[PredicateResult]) -> tuple[PredicateResult, ...]:
    values = tuple(results)
    if len(values) != 12 or not all(isinstance(value, PredicateResult) for value in values):
        raise PreregistrationError("predicate-result-type")
    if {value.id for value in values} != set(PREDICATE_IDS):
        raise PreregistrationError("predicate-id-set")
    ordered = tuple(sorted(values, key=lambda value: value.id))
    for value in ordered:
        if not isinstance(value.status, PredicateStatus):
            try:
                PredicateStatus(value.status)
            except ValueError as exc:
                raise PreregistrationError("predicate-status", repr(value.status)) from exc
        for evidence in value.evidence:
            if not isinstance(evidence, EvidenceRef):
                raise PreregistrationError("predicate-evidence-type")
            _require_hash(evidence.blob_sha256, "evidence blob hash")
    return ordered


def _module_blob(root: Path, commit: str, path: str) -> Optional[bytes]:
    return read_blob_at(root, commit, path, required=False)


def _uniform_predicates(status: PredicateStatus, reason: str) -> tuple[PredicateResult, ...]:
    return tuple(
        PredicateResult(identifier, status, reason, ()) for identifier in PREDICATE_IDS
    )


def _default_registry_results(root: Path, commit: str, module_blob: Optional[bytes]):
    if module_blob is None:
        return _undefined_predicates("evaluator-module-absent-at-commit")
    module = None
    for name in (
        "orchestrator.campaign.s8c_preregistration_evidence",
        "campaign.s8c_preregistration_evidence",
    ):
        try:
            module = importlib.import_module(name)
            break
        except ModuleNotFoundError as exc:
            if exc.name not in {name, name.split(".")[0]}:
                return tuple(
                    PredicateResult(identifier, PredicateStatus.ERROR, "evaluator-import-error", ())
                    for identifier in PREDICATE_IDS
                )
    if module is None:
        return _undefined_predicates("evaluator-module-unavailable")
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return tuple(
            PredicateResult(identifier, PredicateStatus.ERROR, "evaluator-file-unavailable", ())
            for identifier in PREDICATE_IDS
        )
    try:
        live = Path(module_file).read_bytes()
    except OSError:
        live = b""
    if live != module_blob:
        return tuple(
            PredicateResult(identifier, PredicateStatus.ERROR, "evaluator-blob-mismatch", ())
            for identifier in PREDICATE_IDS
        )
    registry: Any = module
    probe = getattr(module, "get_registry", None)
    if callable(probe):
        registry = probe()
    evaluator = getattr(registry, "evaluate_all", None)
    if not callable(evaluator):
        return _undefined_predicates("evaluator-capability-unavailable")
    try:
        return _normalize_predicate_results(evaluator(commit, repo_root=root))
    except Exception:
        return tuple(
            PredicateResult(identifier, PredicateStatus.ERROR, "evaluator-exception", ())
            for identifier in PREDICATE_IDS
        )


def _activation_report_at(
    repo_root: Path | str,
    commit: str,
    *,
    registry: Optional[PredicateRegistry] = None,
    allow_test_registry: bool = False,
) -> ActivationReport:
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    core_blob = _module_blob(root, resolved, CORE_MODULE_PATH)
    evaluator_blob = _module_blob(root, resolved, EVALUATOR_MODULE_PATH)
    core_hash = _sha256(core_blob) if core_blob is not None else None
    evaluator_hash = _sha256(evaluator_blob) if evaluator_blob is not None else None
    contract: Optional[MarkdownContract] = None
    try:
        source = read_blob_at(root, resolved, SOURCE_PATH, required=True)
        assert source is not None
        contract = parse_preregistration_markdown(source)
    except PreregistrationError:
        pass
    validation: Optional[FreezeValidation] = None
    freeze_reason = "valid"
    try:
        validation = validate_condition_freeze_at(root, resolved)
    except PreregistrationError as exc:
        freeze_reason = exc.reason
    if allow_test_registry and registry is not None:
        try:
            predicates = _normalize_predicate_results(
                registry.evaluate_all(resolved, repo_root=root)
            )
        except Exception:
            predicates = _uniform_predicates(PredicateStatus.ERROR, "registry-exception")
    else:
        try:
            live_core = Path(__file__).read_bytes()
        except OSError:
            live_core = b""
        if core_blob is None:
            predicates = _uniform_predicates(
                PredicateStatus.ERROR, "core-module-absent-at-commit"
            )
        elif live_core != core_blob:
            predicates = _uniform_predicates(PredicateStatus.ERROR, "core-blob-mismatch")
        else:
            predicates = _default_registry_results(root, resolved, evaluator_blob)
    findings = contract.section5_findings if contract is not None else ()
    all_filled = bool(findings) and all(item.status is FieldStatus.FILLED for item in findings)
    exact_ids = tuple(item.id for item in predicates) == PREDICATE_IDS
    all_satisfied = exact_ids and all(
        item.status is PredicateStatus.SATISFIED for item in predicates
    )
    effective = validation is not None and all_filled and all_satisfied
    return ActivationReport(
        commit=resolved,
        condition_freeze_valid=validation is not None,
        freeze_generation=validation.generation_number if validation else None,
        protected_sha256=validation.protected_sha256 if validation else None,
        freeze_reason_code=freeze_reason,
        section5_findings=findings,
        predicates=predicates,
        core_module_blob_sha256=core_hash,
        evaluator_module_blob_sha256=evaluator_hash,
        effective=effective,
    )


def activation_report_at(
    repo_root: Path | str,
    commit: str = "HEAD",
) -> ActivationReport:
    """production entrypoint: C と一致する core/evaluator bytes だけで再計算する。"""
    return _activation_report_at(repo_root, commit)


def _activation_report_at_for_test(
    repo_root: Path | str,
    commit: str,
    *,
    registry: PredicateRegistry,
) -> ActivationReport:
    """conjunction 単体テスト専用。capability を生成しない private 注入経路。"""
    return _activation_report_at(
        repo_root,
        commit,
        registry=registry,
        allow_test_registry=True,
    )


def effective_at(
    repo_root: Path | str,
    commit: str = "HEAD",
) -> Optional[EffectivePreregistration]:
    report = activation_report_at(repo_root, commit)
    return _construct_effective(report) if report.effective else None


def _record_document(
    generation: int,
    supersedes: Optional[str],
    contract: MarkdownContract,
    evidence_sha: str,
    revision_reason: str,
    ruling_reference: Optional[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "generation_number": generation,
        "supersedes_sha256": supersedes,
        "source_path": SOURCE_PATH,
        "section5_field_names_sha256": contract.section5_field_names_sha256,
        "section6_conditions_sha256": contract.section6_conditions_sha256,
        "section6_condition_hashes": [
            {"number": number, "sha256": sha}
            for number, sha in contract.section6_condition_hashes
        ],
        "normative_body_sha256": contract.normative_body_sha256,
        "evidence_contract_sha256": evidence_sha,
        "protected_sha256": contract.protected_sha256(evidence_sha),
        "revision_reason": revision_reason,
        "ruling_reference": ruling_reference,
    }


def prepare_revision(
    repo_root: Path | str,
    *,
    ruling_reference: Optional[str] = None,
    revision_reason: str,
    commit: str = "HEAD",
) -> Path:
    """worktree の次契約を canonical record として exclusive-create する。"""
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    if not revision_reason.strip() or revision_reason != revision_reason.strip():
        raise PreregistrationError("record-revision-reason")
    current_paths = _git_text(
        root, ["ls-tree", "-r", "--name-only", resolved, "--", FREEZE_DIR]
    ).splitlines()
    numbers: list[int] = []
    for path in current_paths:
        match = _GENERATION_RE.fullmatch(path)
        if not match:
            raise PreregistrationError("freeze-namespace-unknown", path)
        numbers.append(int(match.group(1)))
    numbers.sort()
    if numbers and (numbers[-1] > MAX_GENERATIONS or len(numbers) > MAX_GENERATIONS):
        raise PreregistrationError("generation-limit", str(numbers[-1]))
    if numbers and numbers != list(range(1, numbers[-1] + 1)):
        raise PreregistrationError("generation-gap")
    if numbers:
        if not isinstance(ruling_reference, str) or not _RULING_RE.fullmatch(
            ruling_reference
        ):
            raise PreregistrationError("record-ruling-reference")
    elif ruling_reference is not None and (
        not isinstance(ruling_reference, str)
        or not _RULING_RE.fullmatch(ruling_reference)
    ):
        raise PreregistrationError("record-ruling-reference")
    supersedes: Optional[str] = None
    if numbers:
        validation = validate_condition_freeze_at(root, resolved)
        next_generation = validation.generation_number + 1
        tip_raw = read_blob_at(root, resolved, generation_path(validation.generation_number))
        assert tip_raw is not None
        supersedes = _sha256(tip_raw)
    else:
        next_generation = 1
    source_file = root / SOURCE_PATH
    evidence_file = root / EVIDENCE_CONTRACT_PATH
    try:
        contract = parse_preregistration_markdown(source_file.read_bytes())
        evidence_sha = evidence_contract_sha256(evidence_file.read_bytes())
    except OSError as exc:
        raise PreregistrationError("worktree-input-missing", str(exc)) from exc
    if numbers and contract.protected_sha256(evidence_sha) == validation.protected_sha256:
        raise PreregistrationError("spurious-revision")
    document = _record_document(
        next_generation,
        supersedes,
        contract,
        evidence_sha,
        revision_reason,
        ruling_reference,
    )
    raw = _canonical_bytes(document)
    destination = root / generation_path(next_generation)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.parent.resolve() != destination.parent:
        raise PreregistrationError("revision-parent-symlink", str(destination.parent))
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise PreregistrationError("revision-exists", str(destination)) from exc
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        # A partially written exclusive destination is itself evidence of failure; do not
        # silently unlink and make a second create look like the first.
        raise
    return destination


def _jsonable(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if dataclasses.is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _activation_report_digest(report: ActivationReport) -> str:
    """consumer が C の再導出結果と照合する report digest。"""
    if not isinstance(report, ActivationReport):
        raise TypeError("ActivationReport が必要")
    return _sha256(_DOMAIN_ACTIVATION_REPORT + _canonical_bytes(_jsonable(report)))


def require_effective_preregistration(
    capability,
    *,
    repo_root: Path | str,
    commit: str,
) -> ActivationReport:
    """C から再計算した発効状態と一致する sealed capability だけを受理する。"""
    if not isinstance(capability, EffectivePreregistration):
        raise PreregistrationError(
            "effective-capability-type",
            "effective_at() が発行した EffectivePreregistration が必要",
        )
    if capability.commit != commit:
        raise PreregistrationError(
            "effective-capability-commit",
            "capability.commit が要求 commit と一致しない",
        )
    report = activation_report_at(repo_root, commit)
    if not report.effective:
        raise PreregistrationError(
            "preregistration-not-effective",
            "commit の事前登録は再計算時点で発効していない",
        )
    expected_digest = _activation_report_digest(report)
    if capability.report_digest_sha256 != expected_digest:
        raise PreregistrationError(
            "effective-capability-digest",
            "capability の report digest が再計算結果と一致しない",
        )
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="指定 commit の導出発効状態を表示")
    check.add_argument("--commit", default="HEAD")
    check.add_argument("--repo-root", type=Path, default=Path("."))
    check.add_argument("--json", action="store_true", dest="json_output")
    prepare = subparsers.add_parser("prepare-revision", help="次 generation を exclusive-create")
    prepare.add_argument("--commit", default="HEAD")
    prepare.add_argument("--repo-root", type=Path, default=Path("."))
    prepare.add_argument("--ruling-reference")
    prepare.add_argument("--revision-reason", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "check":
            report = activation_report_at(args.repo_root, args.commit)
            if args.json_output:
                print(json.dumps(_jsonable(report), ensure_ascii=False, sort_keys=True))
            else:
                state = "EFFECTIVE" if report.effective else "NOT_EFFECTIVE"
                print(f"{state} commit={report.commit} freeze={report.freeze_reason_code}")
                for finding in report.section5_findings:
                    print(f"section5 {finding.status.value} {finding.name}: {finding.reason_code}")
                for result in report.predicates:
                    print(f"{result.id} {result.status.value}: {result.reason_code}")
            return 0 if report.effective else 1
        path = prepare_revision(
            args.repo_root,
            commit=args.commit,
            ruling_reference=args.ruling_reference,
            revision_reason=args.revision_reason,
        )
        print(path)
        return 0
    except PreregistrationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
