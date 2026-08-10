"""追補 A の ``fields`` envelope grammar。

本 module は投入 gate (admission gate) ではない。
``resolve_effective_preregistration`` / ``PreregBinding`` / ``submit_pilot`` /
``verify_receipt`` は本 wave では実装しない。
"""

from __future__ import annotations

import re


T139_EXACT_FIELDS = frozenset(
    {
        "a01",
        "a02",
        "a03",
        "a04",
        "a05",
        "a06",
        "a07",
        "a08",
        "a09",
        "a10",
        "a11",
        "a12",
        "a13",
    }
)

_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


class AddendumEnvelopeError(Exception):
    """追補 A envelope の parse または exact-fields 検査に失敗した。"""


class FieldsSectionNotFoundError(AddendumEnvelopeError):
    """``## fields`` 節が一意に存在しない。"""


class MissingFieldsError(AddendumEnvelopeError):
    """必要な field key が欠落している。"""

    reason_code = "missing_fields"

    def __init__(self, missing: frozenset[str]) -> None:
        self.missing = missing
        super().__init__(f"field key が欠落: {sorted(missing)}")


class ExtraFieldsError(AddendumEnvelopeError):
    """許可されていない field key が余剰である。"""

    reason_code = "extra_fields"

    def __init__(self, extra: frozenset[str]) -> None:
        self.extra = extra
        super().__init__(f"field key が余剰: {sorted(extra)}")


class MissingAndExtraFieldsError(AddendumEnvelopeError):
    """field key に欠落と余剰が同時にある。"""

    reason_code = "missing_and_extra_fields"

    def __init__(self, missing: frozenset[str], extra: frozenset[str]) -> None:
        self.missing = missing
        self.extra = extra
        super().__init__(f"field key に欠落と余剰: missing={sorted(missing)}, extra={sorted(extra)}")


class DuplicateFieldsError(AddendumEnvelopeError):
    """同じ field key の heading が複数回現れる。"""

    reason_code = "duplicate_fields"

    def __init__(self, duplicates: frozenset[str]) -> None:
        self.duplicates = duplicates
        super().__init__(f"field key heading が重複: {sorted(duplicates)}")


def _outside_fences(lines: list[str]) -> tuple[bool, ...]:
    """各 Markdown 行が fenced code の外側にあるかを返す。"""

    visible: list[bool] = []
    fence_character: str | None = None
    fence_width = 0
    for line in lines:
        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_width},}}[ \t]*",
                line,
            )
            visible.append(False)
            if closing is not None:
                fence_character = None
                fence_width = 0
            continue
        opening = _FENCE_OPEN_RE.fullmatch(line)
        if opening is not None:
            marker, info = opening.groups()
            if marker[0] == "`" and "`" in info:
                visible.append(True)
                continue
            fence_character = marker[0]
            fence_width = len(marker)
            visible.append(False)
            continue
        visible.append(True)
    return tuple(visible)


def parse_addendum_fields(blob: bytes) -> tuple[str, ...]:
    """``## fields`` 節内だけの ``### `` heading から key 列を返す。"""

    try:
        text = blob.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FieldsSectionNotFoundError("追補 blob が UTF-8 でない") from exc
    lines = text.splitlines()
    outside_fences = _outside_fences(lines)
    starts = [
        i
        for i, line in enumerate(lines)
        if outside_fences[i] and line == "## fields"
    ]
    if len(starts) != 1:
        raise FieldsSectionNotFoundError("## fields heading が一意に存在しない")
    start = starts[0] + 1
    end = next(
        (
            i
            for i in range(start, len(lines))
            if outside_fences[i] and lines[i].startswith("## ")
        ),
        len(lines),
    )
    keys: list[str] = []
    for index, line in enumerate(lines[start:end], start=start):
        if not outside_fences[index]:
            continue
        if not line.startswith("### "):
            continue
        remainder = line[4:]
        if not remainder or remainder[0].isspace():
            raise AddendumEnvelopeError("### heading の key token が空または先頭空白である")
        keys.append(remainder.split(maxsplit=1)[0])
    return tuple(keys)


def require_exact_fields(
    blob: bytes, expected: frozenset[str] = T139_EXACT_FIELDS
) -> None:
    """Envelope の key が ``expected`` と過不足なく一度ずつ一致することを課す。

    汎用 utility であり、T-139 の承認済み追補 A の検査には caller が集合を
    選べない :func:`require_approved_addendum_a_fields` を使うこと。
    """

    if not isinstance(expected, frozenset) or not all(isinstance(key, str) for key in expected):
        raise TypeError("expected は str の frozenset でなければならない")
    fields = parse_addendum_fields(blob)
    seen: set[str] = set()
    duplicates: set[str] = set()
    for field in fields:
        if field in seen:
            duplicates.add(field)
        seen.add(field)
    if duplicates:
        raise DuplicateFieldsError(frozenset(duplicates))
    actual = frozenset(fields)
    missing = expected - actual
    extra = actual - expected
    if missing and extra:
        raise MissingAndExtraFieldsError(missing, extra)
    if missing:
        raise MissingFieldsError(missing)
    if extra:
        raise ExtraFieldsError(extra)


def require_approved_addendum_a_fields(blob: bytes) -> None:
    """承認済み追補 A の閉集合 (a01〜a13) だけを課す。"""

    require_exact_fields(blob, T139_EXACT_FIELDS)
