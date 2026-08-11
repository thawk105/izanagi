"""凍結 core に対する構造化 erratum の合成。

本 module は投入 gate (admission gate) ではない。
``resolve_effective_preregistration`` / ``PreregBinding`` / ``submit_pilot`` /
``verify_prereg_receipt`` は本 wave では実装しない。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Callable, Literal, NoReturn, TypeAlias, cast

from .blobref import BlobRef, read_pinned_blob


_LOWER_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_OLD_RANGE = "`a01`〜`a12`"
_S7_OLD_TEXT = "較正"
_S7_EXPECTED_COMPOSED_SHA256 = (
    "e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c"
)
_S7_OPERATION_BINDINGS = {
    1: (
        "7",
        "帰無仮説の段落の最終行",
        221,
        "225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89",
        "92fd71754c81b45b6cc01fb14600bfdc140af8e464c50484b45e1bb8caaa01a4",
    ),
    2: (
        "14",
        "追補 A field 表の a12 行",
        333,
        "a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952",
        "b8741cc99c5c45acee8e9c78a9e72a34f9ab9c2a0e27bdfd5ee71e9ec54b37fe",
    ),
}

RegisteredErratumId: TypeAlias = Literal[
    "t139-core-s15-exactkey-v1",
    "t139-core-s7-stresscheck-v1",
]
ApprovedErratumId: TypeAlias = Literal[
    "t139-core-s15-exactkey-v1",
    "t139-core-s7-stresscheck-v1",
]
DraftErratumId: TypeAlias = NoReturn

APPROVED_ERRATA: frozenset[ApprovedErratumId] = frozenset(
    {
        "t139-core-s15-exactkey-v1",
        "t139-core-s7-stresscheck-v1",
    }
)
DRAFT_ERRATA: frozenset[DraftErratumId] = frozenset()

_TOP_LEVEL_KEYS: dict[RegisteredErratumId, frozenset[str]] = {
    "t139-core-s15-exactkey-v1": frozenset({"operations"}),
    "t139-core-s7-stresscheck-v1": frozenset(
        {"operations", "expected_composed_sha256"}
    ),
}
_OPERATION_KEYS: dict[RegisteredErratumId, frozenset[str]] = {
    "t139-core-s15-exactkey-v1": frozenset(
        {"index", "locator", "old_sha256", "old_text", "new_text"}
    ),
    "t139-core-s7-stresscheck-v1": frozenset(
        {
            "index",
            "locator",
            "old_sha256",
            "new_sha256",
            "old_text",
            "new_text",
        }
    ),
}
_LOCATOR_KEYS = frozenset(
    {"section", "anchor", "line_number_at_target_commit"}
)


class ErratumError(Exception):
    """Erratum の parse、検査、または合成に失敗した。"""


class ErratumParseError(ErratumError):
    """§3 の YAML fence を一意に構造化できない。"""


class OperationCountError(ErratumError):
    """operations の要素数が erratum 固有の件数ではない。"""


class UnknownErratumError(ErratumError):
    """erratum_id に対応する fail-closed validator が登録されていない。"""


class EmptyErratumSetError(ErratumError):
    """合成対象の erratum 集合が空である。"""


class OldDigestMismatchError(ErratumError):
    """old_sha256 が locator の対象行 bytes と一致しない。"""


class OccurrenceCountError(ErratumError):
    """対象語句の出現が erratum 固有の operation と一致しない。"""


class OperationDeltaError(ErratumError):
    """operation の差分が a12 から a13 への 1 token 置換ではない。"""


class LineCountMismatchError(ErratumError):
    """operation の old_text と new_text が同じ 1 行ではない。"""


class ReplacementTextMismatchError(ErratumError):
    """operation の new_text が erratum 固有の承認予定 bytes と一致しない。"""


class ErratumRegistryError(ErratumError):
    """validator registry と承認・draft 集合の状態が整合しない。"""


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
    new_sha256: str | None
    old_text: str
    new_text: str


@dataclass(frozen=True)
class ErratumDocument:
    erratum_id: RegisteredErratumId
    operations: tuple[ErratumOperation, ...]
    expected_composed_sha256: str | None


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


def _top_level_values(
    yaml_text: str, erratum_id: RegisteredErratumId
) -> dict[str, str]:
    values: dict[str, str] = {}
    names: list[str] = []
    in_operations = False
    for line in yaml_text.splitlines():
        if not line:
            continue
        if line[0].isspace():
            if not in_operations:
                _fail("top-level scalar の下に indented content を許さない")
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_]*):(?: *(.*))?", line)
        if match is None:
            _fail("erratum §3 の top-level key 形式が不正")
        name = match.group(1)
        names.append(name)
        values[name] = match.group(2) or ""
        in_operations = name == "operations"
    expected = _TOP_LEVEL_KEYS[erratum_id]
    if len(names) != len(expected) or frozenset(names) != expected:
        _fail(f"{erratum_id} の top-level key 集合が exact でない")
    if values["operations"]:
        _fail("operations は block sequence でなければならない")
    return values


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


def _validate_operation_keys(
    block: list[str], erratum_id: RegisteredErratumId
) -> None:
    if not block:
        _fail("operation が空")
    first = re.fullmatch(
        r"  - ([a-z][a-z0-9_]*):.*", block[0].rstrip("\r\n")
    )
    if first is None:
        _fail("operation の先頭 key 形式が不正")
    positions = [(0, first.group(1))]
    for index, line in enumerate(block[1:], start=1):
        raw = line.rstrip("\r\n")
        match = re.match(r"^    ([a-z][a-z0-9_]*):", raw)
        if match is not None:
            positions.append((index, match.group(1)))
    names = [name for _position, name in positions]
    expected = _OPERATION_KEYS[erratum_id]
    if len(names) != len(expected) or frozenset(names) != expected:
        _fail(f"{erratum_id} の operation key 集合が exact でない")

    locator_names: list[str] = []
    for position_index, (position, name) in enumerate(positions):
        end = (
            positions[position_index + 1][0]
            if position_index + 1 < len(positions)
            else len(block)
        )
        children = block[position + 1 : end]
        if name == "locator":
            for line in children:
                match = re.fullmatch(
                    r"      ([a-z][a-z0-9_]*):.*", line.rstrip("\r\n")
                )
                if match is None:
                    _fail("locator の indentation または key 形式が不正")
                locator_names.append(match.group(1))
        elif name in {"old_text", "new_text"}:
            if not children or any(
                not line.startswith("      ") for line in children
            ):
                _fail(f"operation の {name} block scalar が不正")
        elif children:
            _fail(f"operation の scalar key {name} に nested content を許さない")
    if (
        len(locator_names) != len(_LOCATOR_KEYS)
        or frozenset(locator_names) != _LOCATOR_KEYS
    ):
        _fail("locator key 集合が exact でない")


def _parse_operation(
    block: list[str], erratum_id: RegisteredErratumId
) -> ErratumOperation:
    _validate_operation_keys(block, erratum_id)
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
    new_sha256 = None
    if "new_sha256" in _OPERATION_KEYS[erratum_id]:
        new_sha256 = _scalar(
            block, r"    new_sha256:\s*(\S+)\s*", "new_sha256"
        )
        if _LOWER_SHA256_RE.fullmatch(new_sha256) is None:
            _fail("new_sha256 は 64 桁 lowercase hex でなければならない")
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
        new_sha256=new_sha256,
        old_text=_block_scalar(block, "old_text"),
        new_text=_block_scalar(block, "new_text"),
    )


def _validate_delta(operation: ErratumOperation) -> None:
    if operation.old_text.count("a12") != 1:
        raise OperationDeltaError("old_text は a12 token をちょうど 1 個持たなければならない")
    expected = operation.old_text.replace("a12", "a13", 1)
    if operation.new_text != expected:
        raise OperationDeltaError("new_text の差分は a12 から a13 への 1 token だけでなければならない")


def _registered_erratum_id(value: str) -> RegisteredErratumId:
    if value not in _ERRATUM_VALIDATORS:
        raise UnknownErratumError(f"未知の erratum_id を拒否: {value}")
    return cast(RegisteredErratumId, value)


def parse_erratum(blob: bytes) -> ErratumDocument:
    """Erratum ID と §3 の ``operations`` 直下 sequence を構造化する。"""

    erratum_id = _registered_erratum_id(_metadata_erratum_id(blob))
    yaml_text = _section_three_yaml(blob)
    top_level = _top_level_values(yaml_text, erratum_id)
    operation_lines = _operations_sequence_lines(yaml_text)
    starts = [
        index
        for index, line in enumerate(operation_lines)
        if line.startswith("  - ")
    ]
    prefix_end = starts[0] if starts else len(operation_lines)
    if any(line.strip() for line in operation_lines[:prefix_end]):
        _fail("operations の先頭 list item より前に content を許さない")
    operations = tuple(
        _parse_operation(
            operation_lines[
                start : starts[position + 1]
                if position + 1 < len(starts)
                else len(operation_lines)
            ],
            erratum_id,
        )
        for position, start in enumerate(starts)
    )
    expected_composed_sha256 = top_level.get("expected_composed_sha256")
    if (
        expected_composed_sha256 is not None
        and _LOWER_SHA256_RE.fullmatch(expected_composed_sha256) is None
    ):
        _fail("expected_composed_sha256 は 64 桁 lowercase hex でなければならない")
    return ErratumDocument(
        erratum_id=erratum_id,
        operations=operations,
        expected_composed_sha256=expected_composed_sha256,
    )


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
        _validate_operation_binding(core_lines, operation)


def _validate_operation_binding(
    core_lines: list[bytes], operation: ErratumOperation
) -> None:
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


def _validate_t139_core_s7_stresscheck_v1(
    core_lines: list[bytes], document: ErratumDocument
) -> None:
    if len(document.operations) != 2:
        raise OperationCountError(
            f"operations の要素数は 2 必須: actual={len(document.operations)}"
        )
    by_index = {operation.index: operation for operation in document.operations}
    if set(by_index) != {1, 2}:
        raise OperationCountError("operation index 集合は exact {1, 2} でなければならない")

    token = _S7_OLD_TEXT.encode("utf-8")
    occurrence_lines: list[int] = []
    for line_number, line in enumerate(core_lines, start=1):
        occurrence_lines.extend([line_number] * line.count(token))
    operation_lines = {
        operation.locator.line_number_at_target_commit
        for operation in document.operations
    }
    if len(occurrence_lines) != 2:
        raise OccurrenceCountError(
            "core 全体の `較正` 出現は exact 2 件でなければならない"
        )
    if set(occurrence_lines) != operation_lines:
        raise OccurrenceCountError(
            "core 全体の `較正` 出現行は 2 operation の対象行と一致しなければならない"
        )

    for index, operation in by_index.items():
        section, anchor, line_number, old_sha256, new_sha256 = (
            _S7_OPERATION_BINDINGS[index]
        )
        if operation.locator != Locator(section, anchor, line_number):
            raise OldDigestMismatchError(
                f"operation {index} の locator が承認値と一致しない"
            )
        if operation.old_sha256 != old_sha256:
            raise OldDigestMismatchError(
                f"operation {index} の old_sha256 が承認値と一致しない"
            )
        _validate_operation_binding(core_lines, operation)
        old_lines = operation.old_text.splitlines(keepends=True)
        new_lines = operation.new_text.splitlines(keepends=True)
        if len(old_lines) != 1 or len(new_lines) != 1:
            raise LineCountMismatchError(
                "old_text と new_text は同じ 1 行でなければならない"
            )
        try:
            new_bytes = operation.new_text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ErratumParseError("operation text を UTF-8 bytes にできない") from exc
        if (
            operation.new_sha256 != new_sha256
            or hashlib.sha256(new_bytes).hexdigest() != new_sha256
        ):
            raise ReplacementTextMismatchError(
                f"operation {index} の new_text/new_sha256 が承認値と一致しない"
            )

    table_operation = by_index[2]
    if (
        not table_operation.new_text.startswith("| a12 |")
        or table_operation.new_text.count("|")
        != table_operation.old_text.count("|")
    ):
        raise ReplacementTextMismatchError(
            "operation 2 は a12 表行の形と列数を維持しなければならない"
        )

    replaced_lines = list(core_lines)
    for operation in document.operations:
        replaced_lines[operation.locator.line_number_at_target_commit - 1] = (
            operation.new_text.encode("utf-8")
        )
    if b"".join(replaced_lines).count(token) != 0:
        raise ReplacementTextMismatchError("適用後 core の `較正` 出現は 0 件でなければならない")
    if document.expected_composed_sha256 != _S7_EXPECTED_COMPOSED_SHA256:
        raise ComposedDigestMismatchError(
            "文書内 expected_composed_sha256 が承認値と一致しない"
        )


_ERRATUM_VALIDATORS: dict[
    RegisteredErratumId, Callable[[list[bytes], ErratumDocument], None]
] = {
    "t139-core-s15-exactkey-v1": _validate_t139_core_s15_exactkey_v1,
    "t139-core-s7-stresscheck-v1": _validate_t139_core_s7_stresscheck_v1,
}


def _validate_erratum_registry() -> None:
    approved = frozenset(APPROVED_ERRATA)
    draft = frozenset(DRAFT_ERRATA)
    registered = frozenset(_ERRATUM_VALIDATORS)
    if not approved.isdisjoint(draft):
        raise ErratumRegistryError("approved と draft の erratum_id が重複している")
    if approved | draft != registered:
        raise ErratumRegistryError(
            "registered erratum_id は approved または draft に一意に分類しなければならない"
        )


def approved_erratum_ids() -> frozenset[ApprovedErratumId]:
    """明示的に承認済みの ID だけを返す。validator 登録だけでは承認しない。"""

    _validate_erratum_registry()
    return APPROVED_ERRATA


def compose_core(
    repository_root: str,
    *,
    core_ref: BlobRef,
    erratum_refs: Sequence[BlobRef],
    expected_composed_sha256: str,
) -> ComposedCore:
    """固定 core blob へ、固定 erratum blob 群を順序どおり累積適用する。"""

    _validate_erratum_registry()
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
        _ERRATUM_VALIDATORS[document.erratum_id](core_lines, document)
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
    for document in documents:
        if document.expected_composed_sha256 is not None:
            result.require_sha256(document.expected_composed_sha256)
    return result
