# -*- coding: utf-8 -*-
"""Recognizer for the frozen trigger-gate implementation language.

The public result deliberately contains no source text or source location.  Callers may
therefore report a rejection without accidentally disclosing an untrusted proposal.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal


TRIGGER_GATE_LANGUAGE = "trigger-gate-language/v1"

_MAX_CODE_POINTS: Final = 4096
_MAX_TOKENS: Final = 512
_MAX_PAREN_DEPTH: Final = 64
_ASCII_WORD_CHARS: Final = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
)
_ALLOWED_CHARACTERS: Final = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_:=!&|(); \t"
)
_MULTI_PUNCTUATORS: Final = ("==", "!=", "&&", "||", "::")
_SINGLE_PUNCTUATORS: Final = frozenset("=();")
_MEMBERS: Final = frozenset({
    "kUnset",
    "kLockConflict",
    "kUpdateAbsent",
    "kReadValiTid",
    "kReadValiLocked",
    "kNodeVali",
    "kInsertNode",
    "kScanNode",
})


class GateLanguageRejectCode(str, Enum):
    """Closed rejection vocabulary for the trigger-gate recognizer."""

    INVALID_TYPE = "invalid-type"
    RESOURCE_LIMIT = "resource-limit"
    INVALID_CHARACTER = "invalid-character"
    INVALID_TOKEN = "invalid-token"
    INVALID_GRAMMAR = "invalid-grammar"
    UNSET_NOT_TRUE = "unset-not-true"


@dataclass(frozen=True)
class GateLanguageResult:
    passed: bool
    reason_code: GateLanguageRejectCode | None


_Token = str
_NodeKind = Literal["literal", "comparison", "and", "or"]


@dataclass(frozen=True, slots=True)
class _Node:
    kind: _NodeKind
    value: bool | tuple[str, str] | None = None
    left: _Node | None = None
    right: _Node | None = None


class _InvalidToken(Exception):
    """Internal sentinel.  It intentionally carries no diagnostic payload."""


class _InvalidGrammar(Exception):
    """Internal sentinel.  It intentionally carries no diagnostic payload."""


def _accepted() -> GateLanguageResult:
    return GateLanguageResult(passed=True, reason_code=None)


def _rejected(reason: GateLanguageRejectCode) -> GateLanguageResult:
    return GateLanguageResult(passed=False, reason_code=reason)


def _tokenize(implementation: str) -> tuple[_Token, ...]:
    """Tokenize using maximal munch, without retaining offsets in the result."""

    tokens: list[_Token] = []
    cursor = 0
    size = len(implementation)
    while cursor < size:
        character = implementation[cursor]
        if character == " " or character == "\t":
            cursor += 1
            continue

        if character in _ASCII_WORD_CHARS:
            end = cursor + 1
            while end < size and implementation[end] in _ASCII_WORD_CHARS:
                end += 1
            tokens.append(implementation[cursor:end])
            cursor = end
            continue

        matched = False
        for punctuator in _MULTI_PUNCTUATORS:
            if implementation.startswith(punctuator, cursor):
                tokens.append(punctuator)
                cursor += len(punctuator)
                matched = True
                break
        if matched:
            continue

        if character in _SINGLE_PUNCTUATORS:
            tokens.append(character)
            cursor += 1
            continue

        raise _InvalidToken

    return tuple(tokens)


class _Parser:
    def __init__(self, tokens: tuple[_Token, ...]) -> None:
        self._tokens = tokens
        self._cursor = 0

    def parse(self) -> _Node:
        self._expect("izanagi_gate_pass")
        self._expect("=")
        expression = self._parse_or(0)
        self._expect(";")
        if self._cursor != len(self._tokens):
            raise _InvalidGrammar
        return expression

    def _peek(self) -> _Token | None:
        if self._cursor == len(self._tokens):
            return None
        return self._tokens[self._cursor]

    def _expect(self, expected: _Token) -> None:
        if self._peek() != expected:
            raise _InvalidGrammar
        self._cursor += 1

    def _parse_or(self, depth: int) -> _Node:
        node = self._parse_and(depth)
        while self._peek() == "||":
            self._cursor += 1
            node = _Node(kind="or", left=node, right=self._parse_and(depth))
        return node

    def _parse_and(self, depth: int) -> _Node:
        node = self._parse_primary(depth)
        while self._peek() == "&&":
            self._cursor += 1
            node = _Node(kind="and", left=node, right=self._parse_primary(depth))
        return node

    def _parse_primary(self, depth: int) -> _Node:
        token = self._peek()
        if token == "true":
            self._cursor += 1
            return _Node(kind="literal", value=True)
        if token == "false":
            self._cursor += 1
            return _Node(kind="literal", value=False)
        if token == "(":
            nested_depth = depth + 1
            if nested_depth > _MAX_PAREN_DEPTH:
                raise _InvalidGrammar
            self._cursor += 1
            node = self._parse_or(nested_depth)
            self._expect(")")
            return node
        return self._parse_comparison()

    def _parse_comparison(self) -> _Node:
        self._expect("izanagi_abort_reason_")
        operator = self._peek()
        if operator not in ("==", "!="):
            raise _InvalidGrammar
        self._cursor += 1
        self._expect("IzanagiAbortReason")
        self._expect("::")
        member = self._peek()
        if member not in _MEMBERS:
            raise _InvalidGrammar
        self._cursor += 1
        return _Node(kind="comparison", value=(operator, member))


def _parse(tokens: tuple[_Token, ...]) -> _Node:
    """Parse one complete implementation and return its private expression AST."""

    return _Parser(tokens).parse()


def _evaluate(ast: _Node, member: str) -> bool:
    """Evaluate a parsed expression for one IzanagiAbortReason member."""

    if ast.kind == "literal":
        return ast.value is True
    if ast.kind == "comparison":
        if not isinstance(ast.value, tuple):
            raise _InvalidGrammar
        operator, expected_member = ast.value
        if operator == "==":
            return member == expected_member
        if operator == "!=":
            return member != expected_member
        raise _InvalidGrammar
    if ast.left is None or ast.right is None:
        raise _InvalidGrammar
    if ast.kind == "and":
        return _evaluate(ast.left, member) and _evaluate(ast.right, member)
    if ast.kind == "or":
        return _evaluate(ast.left, member) or _evaluate(ast.right, member)
    raise _InvalidGrammar


def check_trigger_gate_implementation(
    implementation: str,
) -> GateLanguageResult:
    """Recognize and semantically check one frozen trigger-gate implementation."""

    if not isinstance(implementation, str):
        return _rejected(GateLanguageRejectCode.INVALID_TYPE)

    # Bypass special-method overrides on a str subclass while preserving its code points.
    try:
        source = str.__str__(implementation)
        if len(source) > _MAX_CODE_POINTS:
            return _rejected(GateLanguageRejectCode.RESOURCE_LIMIT)
    except Exception:  # No exception text may cross the trust boundary.
        return _rejected(GateLanguageRejectCode.RESOURCE_LIMIT)

    try:
        if any(character not in _ALLOWED_CHARACTERS for character in source):
            return _rejected(GateLanguageRejectCode.INVALID_CHARACTER)
    except Exception:
        return _rejected(GateLanguageRejectCode.INVALID_CHARACTER)

    try:
        tokens = _tokenize(source)
    except Exception:
        return _rejected(GateLanguageRejectCode.INVALID_TOKEN)

    if len(tokens) > _MAX_TOKENS:
        return _rejected(GateLanguageRejectCode.RESOURCE_LIMIT)

    try:
        ast = _parse(tokens)
    except Exception:
        return _rejected(GateLanguageRejectCode.INVALID_GRAMMAR)

    try:
        if not _evaluate(ast, "kUnset"):
            return _rejected(GateLanguageRejectCode.UNSET_NOT_TRUE)
    except Exception:
        return _rejected(GateLanguageRejectCode.INVALID_GRAMMAR)
    return _accepted()
