# -*- coding: utf-8 -*-
"""段 8b selector の単一 JSON 出力を fallback なしで厳格に解釈する。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


ALLOWED_CHOICE_IDS = ("c01", "c02", "c03", "c04", "c05", "c06")
_REQUIRED_KEYS = {"schema_version", "choice_id", "rationale"}
_MAX_RATIONALE_LENGTH = 2000
_RATIONALE_LITERAL_PLACEHOLDERS = (
    "<反映>",
    "<受入結果を反映>",
    "<受入全走結果を反映>",
)


@dataclass(frozen=True)
class SelectorDecision:
    choice_id: str
    rationale: str
    raw_sha256: str


class SelectorOutputError(RuntimeError):
    """selector 出力違反。``code`` は collector が記録する機械可読値。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _DuplicateKey(ValueError):
    pass


class _NonFiniteNumber(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _NonFiniteNumber(value)


def _decode_exact_json(raw: str) -> Any:
    stripped = raw.strip()
    if not stripped:
        raise SelectorOutputError("invalid_json", "selector 出力が空")
    if stripped.startswith("```") or stripped.endswith("```"):
        raise SelectorOutputError("markdown_fence", "Markdown fence を許可しない")

    decoder = json.JSONDecoder(
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    try:
        value, end = decoder.raw_decode(stripped)
    except _DuplicateKey as exc:
        raise SelectorOutputError("duplicate_key", "duplicate key: %s" % exc) from exc
    except _NonFiniteNumber as exc:
        raise SelectorOutputError("non_finite_number", "非有限数を許可しない: %s" % exc) from exc
    except json.JSONDecodeError as exc:
        if "{" in stripped[1:]:
            raise SelectorOutputError(
                "leading_content", "JSON object 前の説明文を許可しない"
            ) from exc
        raise SelectorOutputError("invalid_json", "JSON として不正") from exc

    if stripped[end:].strip():
        raise SelectorOutputError(
            "trailing_content", "先頭 JSON value 後の非空白を許可しない"
        )
    return value


def parse_selector_output(raw: str) -> SelectorDecision:
    """raw 出力を厳格検証し、不正時は既定選択へ fallback せず例外を投げる。"""
    if not isinstance(raw, str):
        raise SelectorOutputError("raw_type", "selector raw output は str でなければならない")

    value = _decode_exact_json(raw)
    if not isinstance(value, dict):
        raise SelectorOutputError("top_level_type", "top-level は object でなければならない")

    missing = sorted(_REQUIRED_KEYS - set(value))
    if missing:
        raise SelectorOutputError("missing_required", "必須キー欠落: %r" % missing)
    unknown = sorted(set(value) - _REQUIRED_KEYS)
    if unknown:
        raise SelectorOutputError("unknown_key", "未知キー: %r" % unknown)

    if value["schema_version"] != "8b-selector-output/v1":
        raise SelectorOutputError("schema_version_mismatch", "schema_version が不一致")

    choice_id = value["choice_id"]
    if isinstance(choice_id, list):
        raise SelectorOutputError("multiple_choice", "choice_id の配列を許可しない")
    if not isinstance(choice_id, str):
        raise SelectorOutputError("choice_id_type", "choice_id は string でなければならない")
    if choice_id not in ALLOWED_CHOICE_IDS:
        raise SelectorOutputError("unknown_choice_id", "choice_id が enum 外: %r" % choice_id)

    rationale = value["rationale"]
    if not isinstance(rationale, str):
        raise SelectorOutputError("rationale_type", "rationale は string でなければならない")
    if not rationale.strip():
        raise SelectorOutputError("rationale_blank", "rationale は空白のみであってはならない")
    if len(rationale) > _MAX_RATIONALE_LENGTH:
        raise SelectorOutputError("rationale_too_long", "rationale が最大長を超過")
    if any(
        placeholder in rationale
        for placeholder in _RATIONALE_LITERAL_PLACEHOLDERS
    ):
        raise SelectorOutputError(
            "rationale_placeholder",
            "rationale に literal placeholder を含めてはならない",
        )

    return SelectorDecision(
        choice_id=choice_id,
        rationale=rationale,
        raw_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )
