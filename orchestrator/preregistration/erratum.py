"""凍結 core に対する構造化 erratum の合成。

本 module は投入 gate (admission gate) ではない。
``resolve_effective_preregistration`` / ``PreregBinding`` / ``submit_pilot`` /
``verify_receipt`` は本 wave では実装しない。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Callable, NoReturn

from .blobref import BlobRef, read_pinned_blob


_LOWER_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_OLD_RANGE = "`a01`〜`a12`"


class ErratumError(Exception):
    """Erratum の parse、検査、または合成に失敗した。"""


class ErratumParseError(ErratumError):
    """§3 の YAML fence を一意に構造化できない。"""


class OperationCountError(ErratumError):
    """operations の要素数が 2 ではない。"""


class UnknownErratumError(ErratumError):
    """erratum_id に対応する fail-closed validator が登録されていない。"""


class EmptyErratumSetError(ErratumError):
    """合成対象の erratum 集合が空である。"""


class OldDigestMismatchError(ErratumError):
    """old_sha256 が locator の対象行 bytes と一致しない。"""


class OccurrenceCountError(ErratumError):
    """対象 core の a01〜a12 出現が exact 2 operation と一致しない。"""


class OperationDeltaError(ErratumError):
    """operation の差分が a12 から a13 への 1 token 置換ではない。"""


class LocatorOverlapError(ErratumError):
    """複数 operation の locator が重なる。"""


class ComposedDigestMismatchError(ErratumError):
    """合成後 core の digest が期待値と一致しない。"""


@dataclass(frozen=True)
class Locator:
    section: str
    anchor: str
    line_number_at_target_commit: int


@dataclass(frozen=True)
class ErratumOperation:
    index: int
    locator: Locator
    old_sha256: str
    old_text: str
    new_text: str


@dataclass(frozen=True)
class ErratumDocument:
    erratum_id: str
    operations: tuple[ErratumOperation, ...]


@dataclass(frozen=True)
class ComposedCore:
    composed_bytes: bytes
    composed_sha256: str

    def require_sha256(self, expected: str) -> None:
        """合成結果を、manifest 等が別途固定した digest と照合する。"""

        if not isinstance(expected, str) or _LOWER_SHA256_RE.fullmatch(expected) is None:
            raise ComposedDigestMismatchError("期待 digest は 64 桁 lowercase hex でなければならない")
        if self.composed_sha256 != expected:
            raise ComposedDigestMismatchError(
                "合成後 core の SHA-256 が期待値と一致しない: "
                f"expected_prefix={expected[:12]}"
            )


def _fail(message: str) -> NoReturn:
    raise ErratumParseError(message)


def _section_three_yaml(blob: bytes) -> str:
    try:
        text = blob.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ErratumParseError("erratum blob が UTF-8 でない") from exc
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith("## 3.")]
    if len(starts) != 1:
        _fail("erratum §3 が一意に存在しない")
    start = starts[0] + 1
    end = next(
        (i for i in range(start, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    fence_starts = [
        i for i in range(start, end) if lines[i].rstrip("\r\n") == "```yaml"
    ]
    if len(fence_starts) != 1:
        _fail("erratum §3 の YAML fence が一意に存在しない")
    fence_start = fence_starts[0]
    fence_end = next(
        (
            i
            for i in range(fence_start + 1, end)
            if lines[i].rstrip("\r\n") == "```"
        ),
        None,
    )
    if fence_end is None:
        _fail("erratum §3 の YAML fence が閉じていない")
    return "".join(lines[fence_start + 1 : fence_end])


def _metadata_erratum_id(blob: bytes) -> str:
    try:
        text = blob.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ErratumParseError("erratum blob が UTF-8 でない") from exc
    lines = text.splitlines()
    first_section = next(
        (index for index, line in enumerate(lines) if line.startswith("## ")),
        len(lines),
    )
    starts = [
        index for index, line in enumerate(lines[:first_section]) if line == "```text"
    ]
    if len(starts) != 1:
        _fail("erratum metadata の text fence が一意に存在しない")
    start = starts[0] + 1
    end = next(
        (index for index in range(start, first_section) if lines[index] == "```"),
        None,
    )
    if end is None:
        _fail("erratum metadata の text fence が閉じていない")
    matches = [
        match.group(1)
        for line in lines[start:end]
        if (match := re.fullmatch(r"erratum_id:\s*([a-z0-9][a-z0-9-]*)\s*", line))
    ]
    if len(matches) != 1:
        _fail("erratum_id が metadata に一意に存在しない")
    return matches[0]


def _operations_sequence_lines(yaml_text: str) -> list[str]:
    """YAML top-level ``operations`` の値である直下 sequence だけを返す。"""

    lines = yaml_text.splitlines(keepends=True)
    positions = [
        index
        for index, line in enumerate(lines)
        if line.rstrip("\r\n") == "operations:"
    ]
    if len(positions) != 1:
        _fail("operations key が一意な top-level key として存在しない")
    start = positions[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index].strip()
            and not lines[index].startswith((" ", "\t"))
        ),
        len(lines),
    )
    return lines[start:end]


def _scalar(lines: list[str], pattern: str, label: str) -> str:
    regex = re.compile(pattern)
    values = [match.group(1) for line in lines if (match := regex.fullmatch(line.rstrip("\r\n")))]
    if len(values) != 1:
        _fail(f"operation の {label} が一意に存在しない")
    return values[0]


def _string_scalar(raw: str, label: str) -> str:
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ErratumParseError(f"{label} の quoted scalar が不正") from exc
        if not isinstance(value, str):
            _fail(f"{label} が文字列でない")
        return value
    if not raw or raw[0] in "'[{":
        _fail(f"{label} の scalar 形式を解釈できない")
    return raw


def _block_scalar(lines: list[str], key: str) -> str:
    header = f"    {key}: |"
    positions = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == header]
    if len(positions) != 1:
        _fail(f"operation の {key} block scalar が一意に存在しない")
    start = positions[0] + 1
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("    ") and not line.startswith("      "):
            break
        if not line.startswith("      "):
            _fail(f"operation の {key} block scalar の indentation が不正")
        values.append(line[6:])
    if not values:
        _fail(f"operation の {key} block scalar が空")
    return "".join(values)


def _parse_operation(block: list[str]) -> ErratumOperation:
    index_raw = _scalar(block, r"  - index:\s*([0-9]+)\s*", "index")
    section_raw = _scalar(block, r"      section:\s*(.+?)\s*", "locator.section")
    anchor_raw = _scalar(block, r"      anchor:\s*(.+?)\s*", "locator.anchor")
    line_raw = _scalar(
        block,
        r"      line_number_at_target_commit:\s*([0-9]+)\s*",
        "locator.line_number_at_target_commit",
    )
    old_sha256 = _scalar(block, r"    old_sha256:\s*(\S+)\s*", "old_sha256")
    if _LOWER_SHA256_RE.fullmatch(old_sha256) is None:
        _fail("old_sha256 は 64 桁 lowercase hex でなければならない")
    line_number = int(line_raw)
    if line_number < 1:
        _fail("locator の line number は 1 以上でなければならない")
    return ErratumOperation(
        index=int(index_raw),
        locator=Locator(
            section=_string_scalar(section_raw, "locator.section"),
            anchor=_string_scalar(anchor_raw, "locator.anchor"),
            line_number_at_target_commit=line_number,
        ),
        old_sha256=old_sha256,
        old_text=_block_scalar(block, "old_text"),
        new_text=_block_scalar(block, "new_text"),
    )


def _validate_delta(operation: ErratumOperation) -> None:
    if operation.old_text.count("a12") != 1:
        raise OperationDeltaError("old_text は a12 token をちょうど 1 個持たなければならない")
    expected = operation.old_text.replace("a12", "a13", 1)
    if operation.new_text != expected:
        raise OperationDeltaError("new_text の差分は a12 から a13 への 1 token だけでなければならない")


def parse_erratum(blob: bytes) -> ErratumDocument:
    """Erratum ID と §3 の ``operations`` 直下 sequence を構造化する。"""

    erratum_id = _metadata_erratum_id(blob)
    if erratum_id not in _ERRATUM_VALIDATORS:
        raise UnknownErratumError(f"未知の erratum_id を拒否: {erratum_id}")
    yaml_text = _section_three_yaml(blob)
    operation_lines = _operations_sequence_lines(yaml_text)
    starts = [
        index
        for index, line in enumerate(operation_lines)
        if line.startswith("  - ")
    ]
    operations = tuple(
        _parse_operation(
            operation_lines[
                start : starts[position + 1]
                if position + 1 < len(starts)
                else len(operation_lines)
            ]
        )
        for position, start in enumerate(starts)
    )
    return ErratumDocument(erratum_id=erratum_id, operations=operations)


def _validate_non_overlapping(operations: Sequence[ErratumOperation]) -> None:
    lines: set[int] = set()
    logical: set[tuple[str, str]] = set()
    for operation in operations:
        line = operation.locator.line_number_at_target_commit
        key = (operation.locator.section, operation.locator.anchor)
        if line in lines or key in logical:
            raise LocatorOverlapError("複数 operation の locator が重なる")
        lines.add(line)
        logical.add(key)


def _validate_t139_core_s15_exactkey_v1(
    core_lines: list[bytes], document: ErratumDocument
) -> None:
    if len(document.operations) != 2:
        raise OperationCountError(
            f"operations の要素数は 2 必須: actual={len(document.operations)}"
        )
    for operation in document.operations:
        _validate_delta(operation)

    occurrence_lines: list[int] = []
    token = _OLD_RANGE.encode("utf-8")
    for line_number, line in enumerate(core_lines, start=1):
        occurrence_lines.extend([line_number] * line.count(token))
    operation_lines = sorted(
        operation.locator.line_number_at_target_commit for operation in document.operations
    )
    if len(occurrence_lines) != 2:
        raise OccurrenceCountError(
            "core 全体の `a01`〜`a12` 出現は exact 2 件でなければならない"
        )
    if len(occurrence_lines) == 2 and sorted(occurrence_lines) != operation_lines:
        raise OccurrenceCountError(
            "core 全体の `a01`〜`a12` 出現行は 2 operation の対象行と一致しなければならない"
        )

    for operation in document.operations:
        line_number = operation.locator.line_number_at_target_commit
        if line_number > len(core_lines):
            raise OldDigestMismatchError("locator の対象行が core に存在しない")
        target_line = core_lines[line_number - 1]
        actual = hashlib.sha256(target_line).hexdigest()
        if actual != operation.old_sha256:
            raise OldDigestMismatchError(
                f"locator 対象行の SHA-256 が不一致: line={line_number}"
            )
        try:
            old_bytes = operation.old_text.encode("utf-8", errors="strict")
            operation.new_text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ErratumParseError("operation text を UTF-8 bytes にできない") from exc
        if old_bytes != target_line:
            raise OldDigestMismatchError(
                f"old_text が locator の対象行 bytes と一致しない: line={line_number}"
            )


_ERRATUM_VALIDATORS: dict[
    str, Callable[[list[bytes], ErratumDocument], None]
] = {
    "t139-core-s15-exactkey-v1": _validate_t139_core_s15_exactkey_v1,
}


def compose_core(
    repository_root: str,
    *,
    core_ref: BlobRef,
    erratum_refs: Sequence[BlobRef],
    expected_composed_sha256: str,
) -> ComposedCore:
    """固定 core blob へ、固定 erratum blob 群を順序どおり累積適用する。"""

    references = tuple(erratum_refs)
    if not references:
        raise EmptyErratumSetError("erratum_refs は 1 件以上でなければならない")
    core = read_pinned_blob(repository_root, core_ref)
    core_lines = core.splitlines(keepends=True)
    documents = tuple(
        parse_erratum(read_pinned_blob(repository_root, ref)) for ref in references
    )
    operations = tuple(operation for document in documents for operation in document.operations)
    for document in documents:
        validator = _ERRATUM_VALIDATORS.get(document.erratum_id)
        if validator is None:
            raise UnknownErratumError(
                f"未知の erratum_id を拒否: {document.erratum_id}"
            )
        validator(core_lines, document)
    _validate_non_overlapping(operations)

    composed_lines = list(core_lines)
    for operation in operations:
        line_number = operation.locator.line_number_at_target_commit
        composed_lines[line_number - 1] = operation.new_text.encode("utf-8")
    composed = b"".join(composed_lines)
    result = ComposedCore(
        composed_bytes=composed,
        composed_sha256=hashlib.sha256(composed).hexdigest(),
    )
    result.require_sha256(expected_composed_sha256)
    return result
