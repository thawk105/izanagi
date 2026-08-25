# -*- coding: utf-8 -*-
"""Tier 1 grammar for coder-supplied backoff EVOLVE-BLOCK text.

The validator deliberately leaves the initializer expression opaque.  Calls,
arithmetic, conditionals, comma expressions, and lambdas belong to the Tier 2
policy decision and are not rejected here.  Tier 1 only enforces the declared
``double now_backoff = <expression>;`` binding, the explicitly frozen
straight-line/storage rules, and the scalar ``coder.value`` contract.

Decision order is part of the public contract:

``input-type -> raw-size -> empty -> tokenize/resource -> storage ->
control-flow/label -> reference -> declaration-type -> single-declarator ->
declaration-count -> rebinding``.

Only the input-type and raw-size preflight runs ahead of attribution and
materialization.  Consequently the pre-existing structural and host-effect
reasons are preserved only for inputs within the new raw-size cap.  Every
public rejection contains fixed rule/reason bytes; candidate identifiers,
literals, statements, and internal exception text are never projected.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "BackoffGrammarDecision",
    "BackoffGrammarViolation",
    "MAX_BACKOFF_HOLE_BYTES",
    "MAX_BACKOFF_HOLE_CODEPOINTS",
    "MAX_BACKOFF_HOLE_NESTING",
    "MAX_BACKOFF_HOLE_TOKENS",
    "validate_backoff_implementation",
    "validate_backoff_preflight",
    "validate_backoff_value",
]


MAX_BACKOFF_HOLE_CODEPOINTS = 4096
MAX_BACKOFF_HOLE_BYTES = 4096
MAX_BACKOFF_HOLE_TOKENS = 1024
MAX_BACKOFF_HOLE_NESTING = 64


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
    "value-integer": (
        "backoff-grammar.value-integer.v1",
        "backoff coder value is not a lossless finite integer",
    ),
    "value-range": (
        "backoff-grammar.value-range.v1",
        "backoff coder value is outside the closed range",
    ),
}


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
_ASSIGNMENTS = frozenset({
    "=", "*=", "/=", "%=", "+=", "-=", "<<=", ">>=", "&=", "^=", "|=",
})
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
    if len(implementation) > MAX_BACKOFF_HOLE_CODEPOINTS:
        return _reject("raw-size")
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


def _tokens(source: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    stack: list[str] = []
    offset = 0
    while offset < len(source):
        character = source[offset]
        if character.isspace():
            offset += 1
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
                token = _Token("number", "", len(tokens))
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
            if tokens[start:index]:
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
            while cursor < len(tokens) and tokens[cursor].text in {"*", "&", "&&"}:
                cursor += 1
            if cursor >= len(tokens) or tokens[cursor].kind != "identifier":
                continue
            cursor += 1
            if cursor == len(tokens) or tokens[cursor].text in {
                "=", "(", "{", "[", ",",
            }:
                return True
    return False


def _has_label(tokens: tuple[_Token, ...]) -> bool:
    for index, token in enumerate(tokens[:-1]):
        if token.kind != "identifier" or tokens[index + 1].text != ":":
            continue
        previous = None if index == 0 else tokens[index - 1].text
        if previous is None or previous in {";", "{", "}"}:
            return True
    return False


def validate_backoff_implementation(implementation: object) -> BackoffGrammarDecision:
    """Validate the frozen Tier 1 implementation rules in deterministic order."""

    preflight = validate_backoff_preflight(implementation)
    if not preflight.accepted:
        return preflight
    assert type(implementation) is str
    if not implementation.strip():
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
    if len(exact_declarations) != 1:
        return _reject("declaration-count")

    for statement, _terminated in statements:
        for index, token in enumerate(statement):
            if (
                token.kind != "identifier"
                or token.text != "now_backoff"
                or token.ordinal in declaration_ordinals
                or not _unqualified(statement, index)
            ):
                continue
            left = index - 1
            while left >= 0 and statement[left].text == "(":
                left -= 1
            right = index + 1
            while right < len(statement) and statement[right].text == ")":
                right += 1
            previous = None if left < 0 else statement[left].text
            following = None if right == len(statement) else statement[right].text
            if (
                previous in {"++", "--"}
                or following in _ASSIGNMENTS | {"++", "--"}
            ):
                return _reject("rebinding")
    return _ACCEPT


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
