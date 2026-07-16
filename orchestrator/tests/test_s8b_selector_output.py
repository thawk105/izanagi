# -*- coding: utf-8 -*-
"""段 8b selector 出力 parser の strict rejection と no-fallback を検査する。"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import jsonschema
import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import s8b_selector_output  # noqa: E402


SCHEMA_PATH = _HERE.parent / "campaign/s8b_selector_output_schema.json"


def _raw(choice_id="c01", rationale="descriptor-based reason", **extra) -> str:
    value = {
        "schema_version": "8b-selector-output/v1",
        "choice_id": choice_id,
        "rationale": rationale,
    }
    value.update(extra)
    return json.dumps(value, ensure_ascii=False)


def _assert_code(raw: str, code: str) -> None:
    with pytest.raises(s8b_selector_output.SelectorOutputError) as caught:
        s8b_selector_output.parse_selector_output(raw)
    assert caught.value.code == code


@pytest.mark.parametrize("choice_id", ["c01", "c02", "c03", "c04", "c05", "c06"])
def test_all_choice_ids_are_accepted_with_rationale_and_raw_hash(choice_id):
    raw = _raw(choice_id=choice_id, rationale="理由")
    decision = s8b_selector_output.parse_selector_output(raw)
    assert decision == s8b_selector_output.SelectorDecision(
        choice_id=choice_id,
        rationale="理由",
        raw_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )


def test_output_schema_declares_draft_2020_12_and_accepts_all_valid_ids():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    # この repo の jsonschema は Draft202012Validator 未提供のため、使用している
    # 共通 keyword subset を既存 descriptor と同じ Draft7 validator で検査する。
    jsonschema.Draft7Validator.check_schema(schema)
    validator = jsonschema.Draft7Validator(schema)
    for choice_id in s8b_selector_output.ALLOWED_CHOICE_IDS:
        validator.validate(json.loads(_raw(choice_id=choice_id)))


def test_missing_required_is_rejected():
    value = json.loads(_raw())
    del value["rationale"]
    _assert_code(json.dumps(value), "missing_required")


def test_unknown_choice_id_is_rejected():
    _assert_code(_raw(choice_id="c07"), "unknown_choice_id")


@pytest.mark.parametrize("rationale", ["", " \t\n"])
def test_blank_rationale_is_rejected(rationale):
    _assert_code(_raw(rationale=rationale), "rationale_blank")


def test_additional_key_is_rejected():
    _assert_code(_raw(confidence=1), "unknown_key")


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"choice_id": 1}, "choice_id_type"),
        ({"choice_id": True}, "choice_id_type"),
        ({"rationale": 1}, "rationale_type"),
    ],
)
def test_type_coercion_is_not_performed(value, code):
    document = json.loads(_raw())
    document.update(value)
    _assert_code(json.dumps(document), code)


def test_choice_id_array_is_rejected_as_multiple_choice():
    _assert_code(_raw(choice_id=["c01", "c02"]), "multiple_choice")


def test_duplicate_key_is_rejected():
    raw = (
        '{"schema_version":"8b-selector-output/v1","choice_id":"c01",'
        '"choice_id":"c02","rationale":"reason"}'
    )
    _assert_code(raw, "duplicate_key")


def test_markdown_fence_is_rejected():
    _assert_code("```json\n" + _raw() + "\n```", "markdown_fence")


def test_leading_explanation_is_rejected():
    _assert_code("decision:\n" + _raw(), "leading_content")


def test_trailing_json_is_rejected():
    _assert_code(_raw() + "\n" + _raw(choice_id="c02"), "trailing_content")


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers_are_rejected(constant):
    raw = (
        '{"schema_version":"8b-selector-output/v1","choice_id":"c01",'
        '"rationale":' + constant + "}"
    )
    _assert_code(raw, "non_finite_number")


def test_rationale_over_maximum_length_is_rejected():
    _assert_code(_raw(rationale="x" * 2001), "rationale_too_long")


def test_schema_version_mismatch_is_rejected():
    value = json.loads(_raw())
    value["schema_version"] = "wrong"
    _assert_code(json.dumps(value), "schema_version_mismatch")


@pytest.mark.parametrize("raw", ["not-json", "[]", "null"])
def test_invalid_or_non_object_json_is_rejected(raw):
    expected = "invalid_json" if raw == "not-json" else "top_level_type"
    _assert_code(raw, expected)


def test_invalid_output_raises_instead_of_falling_back():
    with pytest.raises(s8b_selector_output.SelectorOutputError) as caught:
        s8b_selector_output.parse_selector_output(_raw(choice_id="invalid"))
    assert caught.value.code == "unknown_choice_id"
    assert not hasattr(caught.value, "choice_id")
