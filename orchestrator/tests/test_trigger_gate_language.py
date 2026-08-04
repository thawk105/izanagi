# -*- coding: utf-8 -*-
"""Pure tests for the frozen trigger-gate language recognizer."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest import mock


_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO))

from orchestrator.campaign.trigger_gate_language import (  # noqa: E402
    TRIGGER_GATE_LANGUAGE,
    GateLanguageRejectCode,
    GateLanguageResult,
    _evaluate,
    _parse,
    _tokenize,
    check_trigger_gate_implementation,
)


_MEMBERS = (
    "kUnset",
    "kLockConflict",
    "kUpdateAbsent",
    "kReadValiTid",
    "kReadValiLocked",
    "kNodeVali",
    "kInsertNode",
    "kScanNode",
)
_PREFIX = "izanagi_gate_pass = "
_REASON = "izanagi_abort_reason_"
_ENUM = "IzanagiAbortReason::"


def _implementation(expression: str) -> str:
    return f"{_PREFIX}{expression};"


def _comparison(operator: str, member: str) -> str:
    return f"{_REASON} {operator} {_ENUM}{member}"


def _ast(implementation: str):
    return _parse(_tokenize(implementation))


def _assert_rejected(source: object, reason: GateLanguageRejectCode) -> None:
    result = check_trigger_gate_implementation(source)  # type: ignore[arg-type]
    assert result == GateLanguageResult(passed=False, reason_code=reason)


def test_public_contract_is_closed_and_versioned():
    assert TRIGGER_GATE_LANGUAGE == "trigger-gate-language/v1"
    assert [(item.name, item.value) for item in GateLanguageRejectCode] == [
        ("INVALID_TYPE", "invalid-type"),
        ("RESOURCE_LIMIT", "resource-limit"),
        ("INVALID_CHARACTER", "invalid-character"),
        ("INVALID_TOKEN", "invalid-token"),
        ("INVALID_GRAMMAR", "invalid-grammar"),
        ("UNSET_NOT_TRUE", "unset-not-true"),
    ]
    assert check_trigger_gate_implementation(
        _implementation("true")
    ) == GateLanguageResult(passed=True, reason_code=None)


def test_a2_5_whitespace_and_punctuator_failures_have_exact_codes():
    cases = (
        (
            _implementation(
                f"{_REASON} == IzanagiAbortReason : : kUnset"
            ),
            GateLanguageRejectCode.INVALID_TOKEN,
        ),
        ("izanagi_gate_pass = = true;", GateLanguageRejectCode.INVALID_GRAMMAR),
        (_implementation("! = true"), GateLanguageRejectCode.INVALID_TOKEN),
        (_implementation("true & & true"), GateLanguageRejectCode.INVALID_TOKEN),
        (_implementation("true &&& true"), GateLanguageRejectCode.INVALID_TOKEN),
        ("izanagi_gate_pass === true;", GateLanguageRejectCode.INVALID_GRAMMAR),
        (_implementation("true || | true"), GateLanguageRejectCode.INVALID_TOKEN),
    )
    for source, expected in cases:
        _assert_rejected(source, expected)


def test_longest_match_accepts_every_multi_character_punctuator():
    source = _implementation(
        f"{_REASON}=={_ENUM}kUnset"
        f"&&{_REASON}!={_ENUM}kLockConflict"
        f"||({_REASON}=={_ENUM}kNodeVali)"
    )
    tokens = _tokenize(source)
    for punctuator in ("::", "==", "!=", "&&", "||"):
        assert punctuator in tokens
    assert check_trigger_gate_implementation(source).passed


def test_raw_code_point_size_boundaries_4095_4096_4097():
    base = _implementation("true")
    for size in (4095, 4096):
        source = base + (" " * (size - len(base)))
        assert len(source) == size
        assert check_trigger_gate_implementation(source).passed

    oversized = base + (" " * (4097 - len(base)))
    assert len(oversized) == 4097
    _assert_rejected(oversized, GateLanguageRejectCode.RESOURCE_LIMIT)


def test_raw_size_stage_does_not_encode_input():
    class EncodeBomb(str):
        def encode(self, *args, **kwargs):
            raise AssertionError("SECRET_CANARY")

    source = EncodeBomb(_implementation("true"))
    assert check_trigger_gate_implementation(source).passed


def test_token_count_boundaries_511_512_513():
    accepted_512 = _implementation(" || ".join(["true"] * 255))
    tokens_512 = _tokenize(accepted_512)
    assert len(tokens_512) == 512
    assert check_trigger_gate_implementation(accepted_512).passed

    invalid_511 = accepted_512[:-1]
    assert len(_tokenize(invalid_511)) == 511
    _assert_rejected(invalid_511, GateLanguageRejectCode.INVALID_GRAMMAR)

    excessive_513 = accepted_512 + ";"
    assert len(_tokenize(excessive_513)) == 513
    _assert_rejected(excessive_513, GateLanguageRejectCode.RESOURCE_LIMIT)


def test_parenthesis_depth_boundaries_63_64_65():
    for depth in (63, 64):
        source = _implementation("(" * depth + "true" + ")" * depth)
        assert check_trigger_gate_implementation(source).passed

    source_65 = _implementation("(" * 65 + "true" + ")" * 65)
    _assert_rejected(source_65, GateLanguageRejectCode.INVALID_GRAMMAR)


def test_failure_order_size_precedes_character():
    source = _implementation("true") + "#"
    source += " " * (4097 - len(source))
    assert len(source) == 4097
    _assert_rejected(source, GateLanguageRejectCode.RESOURCE_LIMIT)


def test_failure_order_character_precedes_excessive_token_count():
    source = _PREFIX + ("true " * 513) + "#;"
    assert len(source) <= 4096
    _assert_rejected(source, GateLanguageRejectCode.INVALID_CHARACTER)


def test_semantic_rejections_are_unset_not_true():
    cases = (
        _implementation("false"),
        _implementation(_comparison("==", "kLockConflict")),
        _implementation(_comparison("!=", "kUnset")),
    )
    for source in cases:
        _assert_rejected(source, GateLanguageRejectCode.UNSET_NOT_TRUE)


def test_all_128_unset_preserving_subsets_pass_and_evaluate_as_membership():
    optional_members = _MEMBERS[1:]
    for mask in range(1 << len(optional_members)):
        selected = {"kUnset"}
        selected.update(
            member
            for bit, member in enumerate(optional_members)
            if mask & (1 << bit)
        )
        source = _implementation(
            " || ".join(_comparison("==", member) for member in _MEMBERS if member in selected)
        )
        assert check_trigger_gate_implementation(source).passed, mask
        ast = _ast(source)
        for member in _MEMBERS:
            assert _evaluate(ast, member) is (member in selected), (mask, member)


# These expectations are handwritten truth-table literals.  They are intentionally not
# derived from the recognizer or from a set-expression helper.
_MIXED_PRECEDENCE_FIXTURES = (
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict && "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;",
        (True, False, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) && "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;",
        (False, False, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent);",
        (True, False, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset && "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;",
        (False, False, True, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent);",
        (False, False, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict);",
        (False, True, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid);",
        (True, False, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict);",
        (True, True, False, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset && "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) || "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent && "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid) || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;",
        (False, False, False, False, True, False, False, False),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent) && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid);",
        (False, True, True, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali)) || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kScanNode;",
        (True, False, False, False, False, False, False, True),
    ),
    (
        "izanagi_gate_pass = (izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict) && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent) || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;",
        (True, False, False, False, False, True, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset && "
        "izanagi_abort_reason_ != IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;",
        (True, False, True, False, False, False, False, False),
    ),
    (
        "izanagi_gate_pass = izanagi_abort_reason_ != IzanagiAbortReason::kUnset && "
        "(izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent);",
        (False, True, True, False, False, False, False, False),
    ),
)


def test_handwritten_mixed_precedence_truth_tables():
    assert len(_MIXED_PRECEDENCE_FIXTURES) >= 10
    for source, expected in _MIXED_PRECEDENCE_FIXTURES:
        ast = _ast(source)
        actual = tuple(_evaluate(ast, member) for member in _MEMBERS)
        assert actual == expected, source


def test_positive_control_trigger_expressions_and_rendered_indent_pass():
    path = (
        _REPO
        / "output"
        / "insights"
        / "2026-08-04_t409-evolve-hole-allowlist"
        / "positive-controls.txt"
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    selected_lines = (1, 3, 5, 41, 43, 45, 47, 49, 51)
    expressions = []
    for line_number in selected_lines:
        quoted = lines[line_number - 1]
        assert quoted.startswith("'") and quoted.endswith("'")
        expressions.append(quoted[1:-1])

    assert len(expressions) == 9
    for source in expressions:
        assert check_trigger_gate_implementation(source).passed
        assert check_trigger_gate_implementation("  " + source).passed


def test_reject_corpus_is_fail_closed():
    cases = (
        (
            "izanagi_gate_pass = 1;",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = true; pro_set_.pop_back();",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = (izanagi_gate_pass = true);",
            GateLanguageRejectCode.INVALID_GRAMMAR,
        ),
        (
            "izanagi_gate_pass = true; // comment",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = true;\n",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = true;\r",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = trué;",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
        (
            "izanagi_gate_pass = true;\ud800",
            GateLanguageRejectCode.INVALID_CHARACTER,
        ),
    )
    for source, expected in cases:
        _assert_rejected(source, expected)


def test_non_string_inputs_are_invalid_type_without_exception():
    for source in (b"izanagi_gate_pass = true;", None, 1):
        _assert_rejected(source, GateLanguageRejectCode.INVALID_TYPE)


def test_rejections_and_logging_do_not_leak_input_canary():
    canary = "SECRET_CANARY"
    calls: list[tuple[object, ...]] = []

    def capture_log(*args, **kwargs):
        calls.append(args + tuple(kwargs.items()))

    with mock.patch.object(logging.Logger, "_log", capture_log):
        result = check_trigger_gate_implementation(
            _implementation(canary)
        )

    assert result.reason_code is GateLanguageRejectCode.INVALID_GRAMMAR
    rendered = repr(result) + str(result) + repr(calls) + str(calls)
    assert canary not in rendered
    assert calls == []


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
