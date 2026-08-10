# -*- coding: utf-8 -*-
"""Finite lexical defense-in-depth for coder-supplied C++ hole text.

This gate shrinks the accepted set against the four measured injection forms
(``std::system``, ``execl``, ``std::ofstream``, and ``while (true) {}``).  It is
not a host-security boundary and is not a semantically complete account of C++
effects.  In particular, residuals include unlisted identifiers such as
``close`` and ``fsync``; indirect effects through types such as ``File(...)``
whose constructor calls ``open()``; non-terminating loop headers that require
constant folding, such as ``2 - 1``; macro token-pasting; a function pointer
obtained before the scanned text; and compiler extensions outside the deny
table.  The lexical loop rule also conservatively rejects
``while (true) { break; }`` without attempting reachability analysis.

Findings deliberately contain no identifier, string literal, statement,
command, path, URL, or other candidate-derived bytes.  Malformed tokens and
strings fail closed under one fixed rule ID.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterator, Sequence

__all__ = [
    "DENY_TABLE",
    "DenyRule",
    "EffectFinding",
    "MALFORMED_RULE_ID",
    "scan_host_effects",
]


@dataclass(frozen=True)
class DenyRule:
    """One fixed lexical category in the public deny table."""

    rule_id: str
    category: str
    identifiers: tuple[str, ...]


DENY_TABLE: tuple[DenyRule, ...] = (
    DenyRule(
        "host-effect.process-shell.v1",
        "process-shell",
        (
            "system", "popen", "pclose", "fork", "vfork", "clone", "clone3",
            "execl", "execle", "execlp", "execv", "execve", "execvp",
            "execvpe", "fexecve", "posix_spawn", "posix_spawnp", "wordexp",
        ),
    ),
    DenyRule(
        "host-effect.file-stdio.v1",
        "file-stdio",
        (
            "ifstream", "ofstream", "fstream", "filebuf", "basic_ifstream",
            "basic_ofstream", "basic_fstream", "basic_filebuf", "fopen",
            "freopen", "fdopen", "tmpfile", "open", "openat", "creat", "read",
            "write", "pread", "pwrite", "readv", "writev", "fread", "fwrite",
            "remove", "rename", "unlink", "unlinkat", "mkdir", "mkdirat",
            "rmdir", "truncate", "ftruncate", "mmap", "shm_open", "filesystem",
        ),
    ),
    DenyRule(
        "host-effect.network.v1",
        "network",
        (
            "socket", "socketpair", "connect", "bind", "listen", "accept",
            "accept4", "send", "sendto", "sendmsg", "recv", "recvfrom",
            "recvmsg", "shutdown", "getaddrinfo", "getnameinfo",
            "curl_easy_init", "curl_easy_perform",
        ),
    ),
    DenyRule(
        "host-effect.sleep-block-thread.v1",
        "sleep-block-thread",
        (
            "sleep", "usleep", "nanosleep", "clock_nanosleep", "sleep_for",
            "sleep_until", "pause", "sigsuspend", "select", "pselect", "poll",
            "ppoll", "epoll_wait", "pthread_create", "thrd_create", "async",
            "thread", "jthread",
        ),
    ),
    DenyRule(
        "host-effect.escape-hatch.v1",
        "escape-hatch",
        ("syscall", "dlopen", "dlsym", "dlvsym", "asm", "__asm", "__asm__"),
    ),
)

MALFORMED_RULE_ID = "host-effect.lexer-malformed.v1"
_LOOP_RULE_ID = "host-effect.unconditional-loop.v1"
_MALFORMED_CATEGORY = "malformed-token"
_LOOP_CATEGORY = "unconditional-loop"

_ALL_RULE_IDS = tuple(rule.rule_id for rule in DENY_TABLE) + (
    MALFORMED_RULE_ID,
    _LOOP_RULE_ID,
)
assert len(_ALL_RULE_IDS) == len(set(_ALL_RULE_IDS)), "effect rule IDs must be unique"
assert len(DENY_TABLE) == len({rule.category for rule in DENY_TABLE}), (
    "effect categories must be unique"
)

_IDENTIFIER_RULE = {
    identifier: rule
    for rule in DENY_TABLE
    for identifier in rule.identifiers
}
assert sum(len(rule.identifiers) for rule in DENY_TABLE) == len(_IDENTIFIER_RULE), (
    "effect identifiers must belong to exactly one category"
)


@dataclass(frozen=True)
class EffectFinding:
    """Disclosure-free result projected from an untrusted candidate."""

    rule_id: str
    category: str
    token_ordinal: int
    line_number: int
    byte_length: int
    finding_count: int


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    ordinal: int
    line: int
    byte_length: int


class _Malformed(Exception):
    """Internal lexer stop whose message is fixed and disclosure-free."""

    def __init__(self, ordinal: int, line: int, byte_length: int) -> None:
        super().__init__("malformed-token")
        self.ordinal = ordinal
        self.line = line
        self.byte_length = byte_length


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


def _byte_length(text: str) -> int:
    return len(text.encode("utf-8", errors="surrogatepass"))


def _line_delta(text: str) -> int:
    return text.count("\n") + sum(
        character == "\r" and (index + 1 == len(text) or text[index + 1] != "\n")
        for index, character in enumerate(text)
    )


def _is_identifier_start(character: str) -> bool:
    return character == "_" or character.isidentifier()


def _is_identifier_continue(character: str) -> bool:
    return ("_" + character).isidentifier()


def _string_prefix_at(source: str, offset: int) -> tuple[str, bool] | None:
    for prefix in _RAW_PREFIXES:
        if source.startswith(prefix, offset):
            return prefix, True
    for prefix in _QUOTED_PREFIXES:
        if source.startswith(prefix, offset):
            return prefix, False
    return None


def _line_splice_length(source: str, offset: int) -> int:
    if source.startswith("\\\r\n", offset):
        return 3
    if source.startswith("\\\n", offset) or source.startswith("\\\r", offset):
        return 2
    return 0


def _scan_quoted(source: str, offset: int, prefix: str, ordinal: int, line: int) -> int:
    quote = prefix[-1]
    cursor = offset + len(prefix)
    while cursor < len(source):
        character = source[cursor]
        if character == quote:
            return cursor + 1
        if character in "\r\n" or character == "\x00" or 0xD800 <= ord(character) <= 0xDFFF:
            raise _Malformed(ordinal, line, _byte_length(source[offset:cursor + 1]))
        if character == "\\":
            splice_length = _line_splice_length(source, cursor)
            if splice_length:
                cursor += splice_length
                continue
            cursor += 1
            if cursor >= len(source):
                raise _Malformed(ordinal, line, _byte_length(source[offset:cursor]))
            escaped = source[cursor]
            if escaped == "\x00" or 0xD800 <= ord(escaped) <= 0xDFFF:
                raise _Malformed(
                    ordinal, line, _byte_length(source[offset:cursor + 1]),
                )
        cursor += 1
    raise _Malformed(ordinal, line, _byte_length(source[offset:]))


def _scan_raw(source: str, offset: int, prefix: str, ordinal: int, line: int) -> int:
    delimiter_start = offset + len(prefix)
    open_paren = source.find("(", delimiter_start)
    if open_paren < 0:
        raise _Malformed(ordinal, line, _byte_length(source[offset:]))
    delimiter = source[delimiter_start:open_paren]
    if (
        len(delimiter) > 16
        or any(character.isspace() or character in "()\\" or ord(character) < 0x20
               or 0xD800 <= ord(character) <= 0xDFFF
               for character in delimiter)
    ):
        raise _Malformed(ordinal, line, _byte_length(source[offset:open_paren + 1]))
    terminator = ")" + delimiter + "\""
    close = source.find(terminator, open_paren + 1)
    if close < 0:
        raise _Malformed(ordinal, line, _byte_length(source[offset:]))
    body = source[open_paren + 1:close]
    if "\x00" in body or any(0xD800 <= ord(character) <= 0xDFFF for character in body):
        raise _Malformed(ordinal, line, _byte_length(source[offset:close]))
    return close + len(terminator)


def _scan_number(source: str, offset: int) -> tuple[int, str]:
    """Consume a C++ preprocessing-number without swallowing binary operators."""
    characters = [source[offset]]
    cursor = offset + 1
    while cursor < len(source):
        splice_length = _line_splice_length(source, cursor)
        if splice_length:
            cursor += splice_length
            continue
        character = source[cursor]
        previous = characters[-1]
        if character.isalnum() or character in "_.'":
            characters.append(character)
            cursor += 1
            continue
        if character in "+-" and previous in "eEpP":
            characters.append(character)
            cursor += 1
            continue
        break
    return cursor, "".join(characters)


def _tokens(source: str) -> Iterator[_Token]:
    offset = 0
    line = 1
    ordinal = 1
    while offset < len(source):
        character = source[offset]
        splice_length = _line_splice_length(source, offset)
        if splice_length:
            line += 1
            offset += splice_length
            continue
        if character.isspace():
            end = offset + 1
            while end < len(source) and source[end].isspace():
                end += 1
            line += _line_delta(source[offset:end])
            offset = end
            continue
        if source.startswith("//", offset):
            end = offset + 2
            while end < len(source):
                splice_length = _line_splice_length(source, end)
                if splice_length:
                    end += splice_length
                    continue
                if source[end] in "\r\n":
                    break
                end += 1
            line += _line_delta(source[offset:end])
            offset = end
            continue
        if source.startswith("/*", offset):
            end = source.find("*/", offset + 2)
            if end < 0:
                raise _Malformed(ordinal, line, _byte_length(source[offset:]))
            end += 2
            line += _line_delta(source[offset:end])
            offset = end
            continue

        string_prefix = _string_prefix_at(source, offset)
        if string_prefix is not None:
            prefix, raw = string_prefix
            end = (_scan_raw if raw else _scan_quoted)(
                source, offset, prefix, ordinal, line,
            )
            text = source[offset:end]
            yield _Token("string", "", ordinal, line, _byte_length(text))
            line += _line_delta(text)
            ordinal += 1
            offset = end
            continue

        if _is_identifier_start(character):
            characters = [character]
            end = offset + 1
            while end < len(source):
                splice_length = _line_splice_length(source, end)
                if splice_length:
                    end += splice_length
                    continue
                if not _is_identifier_continue(source[end]):
                    break
                characters.append(source[end])
                end += 1
            source_span = source[offset:end]
            yield _Token(
                "identifier", "".join(characters), ordinal, line,
                _byte_length(source_span),
            )
            line += _line_delta(source_span)
            ordinal += 1
            offset = end
            continue

        if character.isdigit() or (
            character == "." and offset + 1 < len(source) and source[offset + 1].isdigit()
        ):
            end, text = _scan_number(source, offset)
            source_span = source[offset:end]
            yield _Token("number", text, ordinal, line, _byte_length(source_span))
            line += _line_delta(source_span)
            ordinal += 1
            offset = end
            continue

        punctuator = next(
            (item for item in _PUNCTUATORS if source.startswith(item, offset)),
            None,
        )
        if punctuator is None or character == "\x00" or 0xD800 <= ord(character) <= 0xDFFF:
            raise _Malformed(ordinal, line, _byte_length(character))
        yield _Token("punctuator", punctuator, ordinal, line, _byte_length(punctuator))
        ordinal += 1
        offset += len(punctuator)


def _strip_parentheses(tokens: Sequence[_Token]) -> Sequence[_Token]:
    while len(tokens) >= 2 and tokens[0].text == "(" and tokens[-1].text == ")":
        depth = 0
        encloses_all = True
        for index, token in enumerate(tokens):
            if token.text == "(":
                depth += 1
            elif token.text == ")":
                depth -= 1
                if depth == 0 and index != len(tokens) - 1:
                    encloses_all = False
                    break
        if not encloses_all or depth != 0:
            break
        tokens = tokens[1:-1]
    return tokens


def _is_nonzero_integer_literal(text: str) -> bool:
    compact = text.replace("'", "")
    cursor = len(compact)
    while cursor and compact[cursor - 1] in "uUlLzZ":
        cursor -= 1
    digits = compact[:cursor]
    if not digits:
        return False
    try:
        if digits.lower().startswith("0x"):
            if "." in digits or "p" in digits.lower():
                return False
            value = int(digits[2:], 16)
        elif digits.lower().startswith("0b"):
            if any(character in digits for character in ".eEpP"):
                return False
            value = int(digits[2:], 2)
        elif len(digits) > 1 and digits.startswith("0"):
            if any(character in digits for character in ".eEpP"):
                return False
            value = int(digits[1:], 8)
        else:
            if any(character in digits for character in ".eEpP"):
                return False
            value = int(digits, 10)
        return value != 0
    except ValueError:
        return False


def _is_true_condition(tokens: Sequence[_Token]) -> bool:
    tokens = _strip_parentheses(tokens)
    if len(tokens) != 1:
        return False
    token = tokens[0]
    return (
        token.kind == "identifier" and token.text == "true"
    ) or (
        token.kind == "number" and _is_nonzero_integer_literal(token.text)
    )


def _matching_paren(tokens: Sequence[_Token], open_index: int) -> int | None:
    depth = 0
    for index in range(open_index, len(tokens)):
        if tokens[index].text == "(":
            depth += 1
        elif tokens[index].text == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _loop_findings(tokens: Sequence[_Token]) -> Iterator[EffectFinding]:
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.text not in {"while", "for"}:
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].text != "(":
            continue
        close_index = _matching_paren(tokens, index + 1)
        if close_index is None:
            continue
        header = tokens[index + 2:close_index]
        unconditional = False
        if token.text == "while":
            unconditional = _is_true_condition(header)
        else:
            depth = 0
            semicolons: list[int] = []
            for header_index, header_token in enumerate(header):
                if header_token.text in {"(", "[", "{"}:
                    depth += 1
                elif header_token.text in {")", "]", "}"}:
                    depth -= 1
                elif header_token.text == ";" and depth == 0:
                    semicolons.append(header_index)
            if len(semicolons) == 2:
                condition = header[semicolons[0] + 1:semicolons[1]]
                unconditional = not condition or _is_true_condition(condition)
        if unconditional:
            yield EffectFinding(
                _LOOP_RULE_ID,
                _LOOP_CATEGORY,
                token.ordinal,
                token.line,
                token.byte_length,
                0,
            )


def _malformed_finding(error: _Malformed) -> tuple[EffectFinding, ...]:
    return (EffectFinding(
        MALFORMED_RULE_ID,
        _MALFORMED_CATEGORY,
        error.ordinal,
        error.line,
        error.byte_length,
        1,
    ),)


def scan_host_effects(implementation: str) -> tuple[EffectFinding, ...]:
    """Return disclosure-free findings; malformed input is a fixed fail-closed hit."""
    if type(implementation) is not str:
        return _malformed_finding(_Malformed(0, 0, 0))
    try:
        tokens = tuple(_tokens(implementation))
        findings: list[EffectFinding] = []
        for token in tokens:
            if token.kind != "identifier":
                continue
            rule = _IDENTIFIER_RULE.get(token.text)
            if rule is not None:
                findings.append(EffectFinding(
                    rule.rule_id,
                    rule.category,
                    token.ordinal,
                    token.line,
                    token.byte_length,
                    0,
                ))
        findings.extend(_loop_findings(tokens))
        findings.sort(key=lambda finding: (finding.token_ordinal, finding.rule_id))
        count = len(findings)
        return tuple(replace(finding, finding_count=count) for finding in findings)
    except _Malformed as error:
        return _malformed_finding(error)
    except Exception:
        # Candidate-triggered implementation errors must neither pass nor reflect
        # exception details to callers such as WAL/provenance projectors.
        return _malformed_finding(_Malformed(0, 0, 0))
