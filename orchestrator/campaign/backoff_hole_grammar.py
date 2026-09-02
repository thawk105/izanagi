# -*- coding: utf-8 -*-
"""Tier 1 grammar for coder-supplied backoff EVOLVE-BLOCK text.

The validator requires one ``double now_backoff = <literal>;`` statement whose
initializer is exactly one suffix-free strict C++ numeric literal.  It also
enforces the explicitly frozen straight-line/storage rules and the scalar
``coder.value`` contract.

Decision order is part of the public contract:

``input-type -> raw-size -> empty -> tokenize/resource -> storage ->
control-flow/label -> reference -> declaration-type -> single-declarator ->
declaration-count -> rebinding -> initializer-literal -> statement-count``.

The full validator runs ahead of attribution in ``run_one_iteration`` and is
rechecked by quarantine after the pre-existing structural and host-effect
gates.  Every public rejection contains fixed rule/reason bytes; candidate
identifiers, literals, statements, and internal exception text are never
projected.
"""
from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass

from .coder_effect_gate import MAX_HOLE_TOKENS

__all__ = [
    "BackoffGrammarDecision",
    "BackoffGrammarViolation",
    "BACKOFF_GRAMMAR_VERSION",
    "BACKOFF_GRAMMAR_VERSION_KEY",
    "BACKOFF_GRAMMAR_RULE_IDS",
    "MAX_BACKOFF_HOLE_BYTES",
    "MAX_BACKOFF_HOLE_NESTING",
    "MAX_BACKOFF_HOLE_TOKENS",
    "attribution_numeric_literals",
    "canonicalize_backoff_implementation",
    "validate_backoff_implementation",
    "validate_backoff_preflight",
    "validate_backoff_value",
]


BACKOFF_GRAMMAR_VERSION = 1
BACKOFF_GRAMMAR_VERSION_KEY = "backoff_grammar_version"
MAX_BACKOFF_HOLE_BYTES = 4096
MAX_BACKOFF_HOLE_TOKENS = MAX_HOLE_TOKENS
MAX_BACKOFF_HOLE_NESTING = 256


@dataclass(frozen=True)
class BackoffGrammarDecision:
    """Disclosure-free admission result."""

    accepted: bool
    stage: str | None = None
    rule_id: str | None = None
    reason: str | None = None


class BackoffGrammarViolation(ValueError):
    """Fixed projection used before attribution can safely inspect a proposal."""

    def __init__(self, decision: BackoffGrammarDecision) -> None:
        if (
            decision.accepted
            or decision.rule_id is None
            or decision.reason is None
        ):
            raise ValueError("backoff grammar violation requires a fixed rejection")
        self.stage = decision.stage
        self.rule_id = decision.rule_id
        self.reason = decision.reason
        super().__init__(decision.reason)


_ACCEPT = BackoffGrammarDecision(True)
_REJECTIONS = {
    "input-type": (
        "backoff-grammar.input-type.v1",
        "backoff hole input type is outside the Tier 1 contract",
    ),
    "raw-size": (
        "backoff-grammar.raw-size.v1",
        "backoff hole raw size is outside the Tier 1 resource cap",
    ),
    "empty": (
        "backoff-grammar.empty.v1",
        "backoff hole is empty",
    ),
    "tokenize": (
        "backoff-grammar.tokenize.v1",
        "backoff hole token structure is outside the Tier 1 resource contract",
    ),
    "storage": (
        "backoff-grammar.storage-duration.v1",
        "backoff hole uses forbidden persistent storage duration",
    ),
    "control-flow": (
        "backoff-grammar.control-flow.v1",
        "backoff hole violates the Tier 1 straight-line contract",
    ),
    "reference": (
        "backoff-grammar.reference-binding.v1",
        "backoff hole binds now_backoff as a reference",
    ),
    "declaration-type": (
        "backoff-grammar.declaration-type.v1",
        "backoff hole does not declare exact double now_backoff",
    ),
    "single-declarator": (
        "backoff-grammar.single-declarator.v1",
        "backoff hole declaration has more than one declarator",
    ),
    "declaration-count": (
        "backoff-grammar.declaration-count.v1",
        "backoff hole must declare now_backoff exactly once",
    ),
    "rebinding": (
        "backoff-grammar.rebinding.v1",
        "backoff hole rebinds now_backoff",
    ),
    "initializer-literal": (
        "backoff-grammar.initializer-literal.v1",
        "backoff hole initializer must be exactly one suffix-free strict C++ numeric literal",
    ),
    "statement-count": (
        "backoff-grammar.statement-count.v1",
        "backoff hole must contain exactly one statement",
    ),
    "value-integer": (
        "backoff-grammar.value-integer.v1",
        "backoff coder value is not a lossless finite integer",
    ),
    "value-range": (
        "backoff-grammar.value-range.v1",
        "backoff coder value is outside the closed range",
    ),
}
BACKOFF_GRAMMAR_RULE_IDS = frozenset(
    rule_id for rule_id, _reason in _REJECTIONS.values()
)


def _reject(stage: str) -> BackoffGrammarDecision:
    rule_id, reason = _REJECTIONS[stage]
    return BackoffGrammarDecision(False, stage, rule_id, reason)


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    ordinal: int


class _Malformed(Exception):
    """Internal fixed stop.  Its detail is intentionally never projected."""


_RAW_PREFIXES = ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"")
_QUOTED_PREFIXES = (
    "u8\"", "u\"", "U\"", "L\"", "\"",
    "u8'", "u'", "U'", "L'", "'",
)
_PUNCTUATORS = tuple(sorted((
    "%:%:", "<<=", ">>=", "<=>", "->*", "...", "##", "::", ".*", "->",
    "++", "--", "<<", ">>", "<=", ">=", "==", "!=", "&&", "||", "*=",
    "/=", "%=", "+=", "-=", "&=", "^=", "|=", "<:", ":>", "<%", "%>",
    "%:", "{", "}", "[", "]", "(", ")", ";", ":", "?", ".", "~", "!",
    "+", "-", "*", "/", "%", "^", "&", "|", "=", "<", ">", ",", "#",
), key=len, reverse=True))
_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = frozenset(_OPEN_TO_CLOSE.values())
_CONTROL_FLOW = frozenset({
    "goto", "return", "throw", "break", "continue",
    "if", "else", "switch", "case", "default", "for", "while", "do",
    "try", "catch",
})
_STORAGE = frozenset({"static", "thread_local"})


def validate_backoff_preflight(implementation: object) -> BackoffGrammarDecision:
    """Run the only checks allowed ahead of attribution/materialization."""

    if type(implementation) is not str:
        return _reject("input-type")
    try:
        encoded = implementation.encode("utf-8")
    except UnicodeError:
        return _reject("raw-size")
    if len(encoded) > MAX_BACKOFF_HOLE_BYTES:
        return _reject("raw-size")
    return _ACCEPT


def _scan_quoted(source: str, offset: int, prefix: str) -> int:
    quote = prefix[-1]
    cursor = offset + len(prefix)
    while cursor < len(source):
        character = source[cursor]
        if character == quote:
            return cursor + 1
        if character in "\r\n\x00":
            raise _Malformed
        if character == "\\":
            cursor += 1
            if cursor >= len(source) or source[cursor] in "\r\n\x00":
                raise _Malformed
        cursor += 1
    raise _Malformed


def _scan_raw(source: str, offset: int, prefix: str) -> int:
    delimiter_start = offset + len(prefix)
    open_paren = source.find("(", delimiter_start)
    if open_paren < 0:
        raise _Malformed
    delimiter = source[delimiter_start:open_paren]
    if (
        len(delimiter) > 16
        or any(
            character.isspace() or character in "()\\"
            for character in delimiter
        )
    ):
        raise _Malformed
    terminator = ")" + delimiter + "\""
    close = source.find(terminator, open_paren + 1)
    if close < 0 or "\x00" in source[open_paren + 1:close]:
        raise _Malformed
    return close + len(terminator)


def _scan_number(source: str, offset: int) -> int:
    cursor = offset + 1
    previous = source[offset]
    while cursor < len(source):
        character = source[cursor]
        if character.isalnum() or character in "_.'":
            previous = character
            cursor += 1
            continue
        if character in "+-" and previous in "eEpP":
            previous = character
            cursor += 1
            continue
        break
    return cursor


_DECIMAL_DIGITS = r"[0-9](?:'?[0-9])*"
_HEX_DIGITS = r"[0-9a-fA-F](?:'?[0-9a-fA-F])*"
_BINARY_DIGITS = r"[01](?:'?[01])*"
_OCTAL_DIGITS = r"[0-7](?:'?[0-7])*"
_INTEGER_SUFFIX = (
    r"(?:[uU](?:(?:ll|LL)|[lL])?|(?:(?:ll|LL)|[lL])[uU]?)?"
)
_DECIMAL_FLOAT_RE = re.compile(
    rf"(?P<body>(?:(?:{_DECIMAL_DIGITS})\.(?:{_DECIMAL_DIGITS})?"
    rf"|\.(?:{_DECIMAL_DIGITS}))"
    rf"(?:[eE][+-]?(?:{_DECIMAL_DIGITS}))?"
    rf"|(?:{_DECIMAL_DIGITS})[eE][+-]?(?:{_DECIMAL_DIGITS}))"
    r"(?P<suffix>[fFlL]?)\Z"
)
_HEX_FLOAT_RE = re.compile(
    rf"(?P<body>0[xX](?:(?:{_HEX_DIGITS})\.(?:{_HEX_DIGITS})?"
    rf"|\.(?:{_HEX_DIGITS})|(?:{_HEX_DIGITS}))"
    rf"[pP][+-]?(?:{_DECIMAL_DIGITS}))"
    r"(?P<suffix>[fFlL]?)\Z"
)
_BINARY_INTEGER_RE = re.compile(
    rf"0[bB](?P<body>{_BINARY_DIGITS})(?P<suffix>{_INTEGER_SUFFIX})\Z"
)
_HEX_INTEGER_RE = re.compile(
    rf"0[xX](?P<body>{_HEX_DIGITS})(?P<suffix>{_INTEGER_SUFFIX})\Z"
)
_OCTAL_INTEGER_RE = re.compile(
    rf"0(?P<body>(?:{_OCTAL_DIGITS})?)(?P<suffix>{_INTEGER_SUFFIX})\Z"
)
_DECIMAL_INTEGER_RE = re.compile(
    rf"(?P<body>[1-9](?:'?[0-9])*)(?P<suffix>{_INTEGER_SUFFIX})\Z"
)


def _rounded_float(value: float, suffix: str) -> float:
    if suffix in {"f", "F"}:
        return struct.unpack("!f", struct.pack("!f", value))[0]
    return value


def _cpp_number_value(token: str) -> int | float:
    """Interpret one complete C++ numeric-literal preprocessing token.

    User-defined suffixes and malformed preprocessing numbers are deliberately
    rejected: their runtime value cannot be established from the token alone.
    """

    match = _HEX_FLOAT_RE.fullmatch(token)
    if match is not None:
        try:
            value = float.fromhex(match.group("body").replace("'", ""))
            value = _rounded_float(value, match.group("suffix"))
        except (OverflowError, ValueError):
            raise _Malformed from None
        if not math.isfinite(value):
            raise _Malformed
        return value

    match = _DECIMAL_FLOAT_RE.fullmatch(token)
    if match is not None:
        try:
            value = float(match.group("body").replace("'", ""))
            value = _rounded_float(value, match.group("suffix"))
        except (OverflowError, ValueError):
            raise _Malformed from None
        if not math.isfinite(value):
            raise _Malformed
        return value

    for pattern, base in (
        (_BINARY_INTEGER_RE, 2),
        (_HEX_INTEGER_RE, 16),
        (_OCTAL_INTEGER_RE, 8),
        (_DECIMAL_INTEGER_RE, 10),
    ):
        match = pattern.fullmatch(token)
        if match is None:
            continue
        body = match.group("body").replace("'", "")
        if pattern is _OCTAL_INTEGER_RE and not body:
            body = "0"
        try:
            return int(body, base)
        except ValueError:
            raise _Malformed from None
    raise _Malformed


def _cpp_number_suffix(token: str) -> str:
    """Return the standard suffix of one syntactically strict numeric literal."""

    for pattern in (
        _HEX_FLOAT_RE,
        _DECIMAL_FLOAT_RE,
        _BINARY_INTEGER_RE,
        _HEX_INTEGER_RE,
        _OCTAL_INTEGER_RE,
        _DECIMAL_INTEGER_RE,
    ):
        match = pattern.fullmatch(token)
        if match is not None:
            return match.group("suffix")
    raise _Malformed


def _tokens(
    source: str, *, skip_comments: bool = False,
) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    stack: list[str] = []
    offset = 0
    while offset < len(source):
        character = source[offset]
        if character in " \t\r\n":
            offset += 1
            continue
        if character.isspace():
            raise _Malformed
        if skip_comments and source.startswith("//", offset):
            offset += 2
            while offset < len(source):
                if source[offset] == "\\" and offset + 1 < len(source):
                    if source[offset + 1] == "\n":
                        offset += 2
                        continue
                    if (
                        source[offset + 1] == "\r"
                        and offset + 2 < len(source)
                        and source[offset + 2] == "\n"
                    ):
                        offset += 3
                        continue
                if source[offset] in "\r\n":
                    break
                offset += 1
            continue
        if skip_comments and source.startswith("/*", offset):
            close = source.find("*/", offset + 2)
            if close < 0:
                raise _Malformed
            offset = close + 2
            continue

        prefix = next(
            (item for item in _RAW_PREFIXES if source.startswith(item, offset)),
            None,
        )
        if prefix is not None:
            offset = _scan_raw(source, offset, prefix)
            token = _Token("literal", "", len(tokens))
        else:
            prefix = next(
                (item for item in _QUOTED_PREFIXES if source.startswith(item, offset)),
                None,
            )
            if prefix is not None:
                offset = _scan_quoted(source, offset, prefix)
                token = _Token("literal", "", len(tokens))
            elif character == "_" or character.isalpha() or character.isidentifier():
                end = offset + 1
                while end < len(source):
                    candidate = source[end]
                    if not (
                        candidate == "_"
                        or candidate.isalnum()
                        or ("_" + candidate).isidentifier()
                    ):
                        break
                    end += 1
                token = _Token("identifier", source[offset:end], len(tokens))
                offset = end
            elif character.isdigit() or (
                character == "." and offset + 1 < len(source) and source[offset + 1].isdigit()
            ):
                end = _scan_number(source, offset)
                token = _Token("number", source[offset:end], len(tokens))
                offset = end
            else:
                punctuator = next(
                    (item for item in _PUNCTUATORS if source.startswith(item, offset)),
                    None,
                )
                if punctuator is None or character == "\x00":
                    raise _Malformed
                token = _Token("punctuator", punctuator, len(tokens))
                offset += len(punctuator)

        if len(tokens) >= MAX_BACKOFF_HOLE_TOKENS:
            raise _Malformed
        tokens.append(token)
        if token.text in _OPEN_TO_CLOSE:
            stack.append(_OPEN_TO_CLOSE[token.text])
            if len(stack) > MAX_BACKOFF_HOLE_NESTING:
                raise _Malformed
        elif token.text in _CLOSERS:
            if not stack or stack.pop() != token.text:
                raise _Malformed
    if stack:
        raise _Malformed
    return tuple(tokens)


def attribution_numeric_literals(
    implementation: str,
) -> tuple[bool, int | float | None, tuple[int | float, ...]]:
    """Return the direct binding literal and all complete numeric literals.

    The boolean distinguishes an absent direct literal from a literal whose
    value is otherwise falsey.  Any pp-number which is not a strict C++
    numeric literal makes the whole attribution scan fail closed.
    """

    tokens = _tokens(implementation, skip_comments=True)
    values: dict[int, int | float] = {}
    for token in tokens:
        if token.kind == "number":
            values[token.ordinal] = _cpp_number_value(token.text)

    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.text != "now_backoff":
            continue
        cursor = index + 1
        if cursor >= len(tokens) or tokens[cursor].text != "=":
            continue
        cursor += 1
        sign = 1
        if cursor < len(tokens) and tokens[cursor].text in {"+", "-"}:
            if tokens[cursor].text == "-":
                sign = -1
            cursor += 1
        if cursor < len(tokens) and tokens[cursor].kind == "number":
            return (
                True,
                sign * values[tokens[cursor].ordinal],
                tuple(values[token.ordinal] for token in tokens if token.kind == "number"),
            )
        break
    return (
        False,
        None,
        tuple(values[token.ordinal] for token in tokens if token.kind == "number"),
    )


def _top_level_statements(
    tokens: tuple[_Token, ...],
) -> tuple[tuple[tuple[_Token, ...], bool], ...]:
    statements: list[tuple[tuple[_Token, ...], bool]] = []
    start = 0
    depth = 0
    for index, token in enumerate(tokens):
        if token.text in _OPEN_TO_CLOSE:
            depth += 1
        elif token.text in _CLOSERS:
            depth -= 1
        elif token.text == ";" and depth == 0:
            statements.append((tokens[start:index], True))
            start = index + 1
    if start < len(tokens):
        statements.append((tokens[start:], False))
    return tuple(statements)


def _unqualified(statement: tuple[_Token, ...], index: int) -> bool:
    return index == 0 or statement[index - 1].text not in {".", "->", "::"}


def _has_additional_declarator(tokens: tuple[_Token, ...]) -> bool:
    depth = 0
    for index, token in enumerate(tokens):
        if token.text in _OPEN_TO_CLOSE:
            depth += 1
        elif token.text in _CLOSERS:
            depth -= 1
        elif token.text == "," and depth == 0:
            cursor = index + 1
            parenthesized = 0
            while cursor < len(tokens) and tokens[cursor].text == "(":
                parenthesized += 1
                cursor += 1
            while cursor < len(tokens) and tokens[cursor].text in {"*", "&", "&&"}:
                cursor += 1
            if cursor >= len(tokens) or tokens[cursor].kind != "identifier":
                continue
            cursor += 1
            while parenthesized and cursor < len(tokens) and tokens[cursor].text == ")":
                parenthesized -= 1
                cursor += 1
            if parenthesized:
                continue
            if cursor == len(tokens) or tokens[cursor].text in {
                "=", "(", "{", "[", ",",
            }:
                return True
    return False


def _has_label(tokens: tuple[_Token, ...]) -> bool:
    for index, token in enumerate(tokens[:-1]):
        if token.kind != "identifier" or tokens[index + 1].text != ":":
            continue
        cursor = index - 1
        while (
            cursor >= 1
            and tokens[cursor - 1].text == "]"
            and tokens[cursor].text == "]"
        ):
            attribute_start = next(
                (
                    candidate
                    for candidate in range(cursor - 2, -1, -1)
                    if candidate + 1 < len(tokens)
                    and tokens[candidate].text == "["
                    and tokens[candidate + 1].text == "["
                ),
                None,
            )
            if attribute_start is None:
                break
            cursor = attribute_start - 1
        previous = None if cursor < 0 else tokens[cursor].text
        if previous is None or previous in {";", "{", "}"}:
            return True
    return False


def validate_backoff_implementation(implementation: object) -> BackoffGrammarDecision:
    """Validate the frozen Tier 1 implementation rules in deterministic order."""

    preflight = validate_backoff_preflight(implementation)
    if not preflight.accepted:
        return preflight
    assert type(implementation) is str
    if not implementation.strip(" \t\r\n"):
        return _reject("empty")
    try:
        tokens = _tokens(implementation)
    except Exception:
        return _reject("tokenize")
    if not tokens:
        return _reject("empty")

    if any(
        token.kind == "identifier" and token.text in _STORAGE
        for token in tokens
    ):
        return _reject("storage")
    if (
        any(
            token.kind == "identifier" and token.text in _CONTROL_FLOW
            for token in tokens
        )
        or _has_label(tokens)
    ):
        return _reject("control-flow")

    statements = _top_level_statements(tokens)
    exact_declarations: list[tuple[_Token, ...]] = []
    declaration_ordinals: set[int] = set()
    saw_reference = False
    saw_wrong_type = False
    saw_multiple_declarator = False

    double_declaration_ordinals = set()
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.text != "now_backoff":
            continue
        cursor = index - 1
        while cursor >= 0 and tokens[cursor].text in {"&", "&&"}:
            cursor -= 1
        if cursor >= 0 and tokens[cursor].text == "double":
            double_declaration_ordinals.add(token.ordinal)

    for statement, terminated in statements:
        for index, token in enumerate(statement):
            if (
                token.kind != "identifier"
                or token.text != "now_backoff"
                or not _unqualified(statement, index)
            ):
                continue
            before = statement[:index]
            after = statement[index + 1:]
            normalized_before = tuple(
                item for item in before
                if not (item.kind == "identifier" and item.text in _STORAGE)
            )
            if before and before[0].text == "double" and any(
                item.text in {"&", "&&"} for item in before[1:]
            ):
                saw_reference = True
                normalized_before = tuple(
                    item for item in before if item.text not in {"&", "&&"}
                )
            if (
                len(normalized_before) == 1
                and normalized_before[0].text == "double"
            ):
                if (
                    not terminated
                    or not after
                    or after[0].text != "="
                    or len(after) == 1
                ):
                    saw_wrong_type = True
                    continue
                if _has_additional_declarator(after[1:]):
                    saw_multiple_declarator = True
                    continue
                exact_declarations.append(statement)
                declaration_ordinals.add(token.ordinal)
                continue
            next_text = after[0].text if after else None
            if (
                before
                and before[0].kind == "identifier"
                and next_text in {None, "=", "(", "{", "[", ","}
            ):
                saw_wrong_type = True

    if saw_reference:
        return _reject("reference")
    if saw_wrong_type:
        return _reject("declaration-type")
    if saw_multiple_declarator:
        return _reject("single-declarator")
    if (
        len(exact_declarations) != 1
        or len(double_declaration_ordinals) != 1
    ):
        return _reject("declaration-count")

    if any(
        token.kind == "identifier"
        and token.text == "now_backoff"
        and token.ordinal not in declaration_ordinals
        for token in tokens
    ):
        return _reject("rebinding")

    declaration = exact_declarations[0]
    binding_index = next(
        index
        for index, token in enumerate(declaration)
        if token.ordinal in declaration_ordinals
    )
    initializer = declaration[binding_index + 2:]
    if len(initializer) != 1 or initializer[0].kind != "number":
        return _reject("initializer-literal")
    try:
        _cpp_number_value(initializer[0].text)
        suffix = _cpp_number_suffix(initializer[0].text)
    except _Malformed:
        return _reject("initializer-literal")
    if suffix:
        return _reject("initializer-literal")

    if len(statements) != 1:
        return _reject("statement-count")
    return _ACCEPT


def canonicalize_backoff_implementation(implementation: object) -> str:
    """Canonicalize one fully accepted production-domain backoff hole.

    Rejected candidates retain the validator's fixed rejection.  Grammar-only
    inputs outside the production integer domain retain their accepted bytes;
    ``run_one_iteration`` rejects those values before materialization.
    """

    decision = validate_backoff_implementation(implementation)
    if not decision.accepted:
        raise BackoffGrammarViolation(decision)
    assert type(implementation) is str
    try:
        present, value, _all_values = attribution_numeric_literals(
            implementation
        )
        if not present or value is None:
            raise _Malformed
        converted = int(value)
    except (OverflowError, TypeError, ValueError, _Malformed):
        raise AssertionError(
            "accepted backoff implementation lost its numeric literal"
        ) from None
    if value != converted or not 1 <= converted <= 1000:
        return implementation
    return f"double now_backoff = {converted};"


def validate_backoff_value(value: object) -> BackoffGrammarDecision:
    """Require a finite mathematical integer whose ``int`` conversion is lossless."""

    if isinstance(value, bool) or type(value) not in {int, float}:
        return _reject("value-integer")
    if type(value) is float and not math.isfinite(value):
        return _reject("value-integer")
    try:
        converted = int(value)
    except (OverflowError, TypeError, ValueError):
        return _reject("value-integer")
    if value != converted:
        return _reject("value-integer")
    if not 1 <= converted <= 1000:
        return _reject("value-range")
    return _ACCEPT
