# -*- coding: utf-8 -*-
"""段 8b selector 出力 parser の strict rejection と no-fallback を検査する。"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import jsonschema
import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))
sys.path.insert(0, str(_HERE.parents[1] / "tools"))

from orchestrator.campaign import s8b_selector_output  # noqa: E402
import check_docs  # noqa: E402


SCHEMA_PATH = _HERE.parent / "campaign/s8b_selector_output_schema.json"
CHECK_DOCS_PATH = _HERE.parents[1] / "tools/check_docs.py"
_EXPECTED_LITERAL_PLACEHOLDERS = (
    "<反映>",
    "<受入結果を反映>",
    "<受入全走結果を反映>",
)
_LP_IDS = tuple(
    f"lp-{index}"
    for index in range(1, len(_EXPECTED_LITERAL_PLACEHOLDERS) + 1)
)


def _extract_single_top_level_literal_tuple(path: Path, name: str) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    stores = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == name
        )
    ]
    assignments = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        )
    ]
    assert len(stores) == 1, f"{name} Store はちょうど1個でなければならない"
    assert len(assignments) == 1, f"{name} はトップレベル ast.Assign ちょうど1個でなければならない"
    value = ast.literal_eval(assignments[0].value)
    assert isinstance(value, tuple)
    assert value
    assert all(isinstance(item, str) and item for item in value)
    return value


def _raw(choice_id="c01", rationale="descriptor-based reason", **extra) -> str:
    value = {
        "schema_version": "8b-selector-output/v1",
        "choice_id": choice_id,
        "rationale": rationale,
    }
    value.update(extra)
    return json.dumps(value, ensure_ascii=False)


def _assert_code(raw: str, code: str) -> s8b_selector_output.SelectorOutputError:
    with pytest.raises(s8b_selector_output.SelectorOutputError) as caught:
        s8b_selector_output.parse_selector_output(raw)
    assert caught.value.code == code
    return caught.value


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


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_literal_placeholder_rationale_is_rejected(placeholder):
    error = _assert_code(
        _raw(rationale=placeholder),
        "rationale_placeholder",
    )
    assert str(error) == "rationale に literal placeholder を含めてはならない"


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_embedded_literal_placeholder_rationale_is_rejected(placeholder):
    rationale = "x" * 1000 + placeholder + "y" * (1000 - len(placeholder))
    assert len(rationale) == 2000
    _assert_code(_raw(rationale=rationale), "rationale_placeholder")


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_trailing_literal_placeholder_rationale_is_rejected(placeholder):
    rationale = "x" * (2000 - len(placeholder)) + placeholder
    assert len(rationale) == 2000
    _assert_code(_raw(rationale=rationale), "rationale_placeholder")


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_json_angle_escaped_literal_placeholder_is_rejected(placeholder):
    raw = _raw(rationale=placeholder).replace("<", "\\u003c").replace(">", "\\u003e")
    assert placeholder not in raw
    assert json.loads(raw)["rationale"] == placeholder
    _assert_code(raw, "rationale_placeholder")


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_json_body_escaped_literal_placeholder_is_rejected(placeholder):
    escaped_body = "".join(f"\\u{ord(character):04X}" for character in placeholder[1:-1])
    assert any(character in "ABCDEF" for character in escaped_body)
    raw = _raw(rationale=placeholder).replace(
        placeholder,
        f"<{escaped_body}>",
    )
    assert placeholder not in raw
    assert json.loads(raw)["rationale"] == placeholder
    _assert_code(raw, "rationale_placeholder")


@pytest.mark.parametrize(
    "placeholders",
    tuple(combinations(_EXPECTED_LITERAL_PLACEHOLDERS, 2))
    + (_EXPECTED_LITERAL_PLACEHOLDERS,),
    ids=("lp-1+lp-2", "lp-1+lp-3", "lp-2+lp-3", "all-lps"),
)
def test_multiple_literal_placeholders_are_rejected(placeholders):
    rationale = " / ".join(placeholders)
    _assert_code(_raw(rationale=rationale), "rationale_placeholder")


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_literal_placeholder_after_unrelated_angle_token_is_rejected(placeholder):
    rationale = f"<無関係> / {placeholder}"
    _assert_code(_raw(rationale=rationale), "rationale_placeholder")


@pytest.mark.parametrize(
    ("prefix", "suffix"),
    [(" ", " "), ("`", "`")],
    ids=("spaces", "backticks"),
)
@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_wrapped_literal_placeholder_is_rejected(placeholder, prefix, suffix):
    _assert_code(
        _raw(rationale=f"{prefix}{placeholder}{suffix}"),
        "rationale_placeholder",
    )


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_placeholder_body_without_delimiters_is_accepted(placeholder):
    rationale = placeholder[1:-1]
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


@pytest.mark.parametrize(
    "rationale",
    ("<結果を反映>", "<反映済み>"),
    ids=("unapproved-result", "unapproved-completed"),
)
def test_unapproved_ascii_angle_rationale_is_accepted(rationale):
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


@pytest.mark.parametrize(
    "transform",
    (
        lambda placeholder: placeholder[:-1],
        lambda placeholder: placeholder[1:],
    ),
    ids=("missing-closing", "missing-opening"),
)
@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_placeholder_with_one_missing_delimiter_is_accepted(
    placeholder,
    transform,
):
    rationale = transform(placeholder)
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_fullwidth_angle_placeholder_is_accepted(placeholder):
    # 全角山括弧まで拒否する一般化は T-100 の射程であり、本変更では受理を固定する。
    rationale = f"＜{placeholder[1:-1]}＞"
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_html_entity_placeholder_is_accepted(placeholder):
    rationale = f"&lt;{placeholder[1:-1]}&gt;"
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


@pytest.mark.parametrize(
    "insertion",
    (" ", "\u200b"),
    ids=("space", "zero-width-space"),
)
@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_placeholder_with_internal_space_is_accepted(placeholder, insertion):
    rationale = f"{placeholder[:2]}{insertion}{placeholder[2:]}"
    decision = s8b_selector_output.parse_selector_output(_raw(rationale=rationale))
    assert decision.rationale == rationale


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


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_rationale_too_long_takes_precedence_over_placeholder(placeholder):
    rationale = placeholder + "x" * (2001 - len(placeholder))
    assert len(rationale) == 2001
    _assert_code(_raw(rationale=rationale), "rationale_too_long")


@pytest.mark.parametrize(
    "placeholder",
    _EXPECTED_LITERAL_PLACEHOLDERS,
    ids=_LP_IDS,
)
def test_unknown_choice_id_takes_precedence_over_placeholder(placeholder):
    _assert_code(
        _raw(choice_id="c99", rationale=placeholder),
        "unknown_choice_id",
    )


def test_placeholder_vocabulary_matches_check_docs_and_parser():
    docs_placeholders = _extract_single_top_level_literal_tuple(
        CHECK_DOCS_PATH,
        "LITERAL_PLACEHOLDERS",
    )
    assert docs_placeholders == _EXPECTED_LITERAL_PLACEHOLDERS
    assert check_docs.LITERAL_PLACEHOLDERS == _EXPECTED_LITERAL_PLACEHOLDERS
    assert (
        s8b_selector_output._RATIONALE_LITERAL_PLACEHOLDERS
        == _EXPECTED_LITERAL_PLACEHOLDERS
    )


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
