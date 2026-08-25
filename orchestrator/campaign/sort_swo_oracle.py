#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finite, independent strict-weak-order oracle for synthesized sort holes.

The candidate's materialized ``sort(...)`` statement is compiled unchanged in
a small translation unit which uses the real CCBench ``WriteElement<Tuple>``.
The executable returns only a fixed-size relation matrix over a dedicated pipe;
stdout and stderr are discarded.  Python, not candidate-controlled C++, checks
the four strict-weak-order axioms.

This is a counterexample finder over finite, versioned corpora.  It is not a
proof that arbitrary C++ is a strict weak ordering on every possible input.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import resource
import shutil
import signal
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence


CORPUS_VERSION = 1
PROTOCOL_VERSION = 2
AXIOM_CHECKER_VERSION = 2
GRAMMAR_VERSION = 1
CONTRACT_VERSION = 3

_MAGIC = b"IZSWO2\0\0"
_N = 18
_WITNESS_NONE = 0xFFFFFFFF
_HEADER = struct.Struct("=8sIIIIIIIII")
_RECORD_SIZE = _HEADER.size + _N * _N
_COMPILE_TIMEOUT_S = 8.0
_RUN_TIMEOUT_S = 2.0
_TOOL_IDENTITY_TIMEOUT_S = 2.0
_MAX_SOURCE_BYTES = 64 * 1024
_MAX_DIAGNOSTIC_BYTES = 16 * 1024
_MAX_ENVIRONMENT_CANDIDATES = 16
_MAX_ENVIRONMENT_BASENAME_CHARS = 255
_ENVIRONMENT_CANDIDATE_OUTCOMES = frozenset({
    "not-configured",
    "not-found",
    "selected",
    "not-executable",
    "not-regular-file",
    "missing",
    "config-h-not-regular-file",
    "config-h-missing",
    "invalid-path",
})
_ORDERS = (0, 1, 2)
_CORPORA = (0, 1)
# Public producer-domain aliases for consumers of the finding schema.
N = _N
ORDERS = _ORDERS
CORPORA = _CORPORA
CORPUS_ID = f"sort-swo-corpus-v{CORPUS_VERSION}"
INFRASTRUCTURE_REASON_CODE = "sort-swo-oracle-infrastructure-unavailable"
_TRUSTED_CONTROL_STATEMENT = (
    "sort(write_set_.begin(), write_set_.end(), "
    "[](const auto& lhs, const auto& rhs) { return lhs.key_ < rhs.key_; });"
)
_TRUSTED_POSTFLIGHT_COMPILE_DETAIL_CODE = (
    "trusted-positive-tu-postflight-compile-failed"
)
_TRUSTED_POSTFLIGHT_COMPILE_WITH_CANDIDATE_CLEANUP_DETAIL_CODE = (
    "trusted-positive-tu-postflight-compile-failed-after-candidate-cleanup-failed"
)

_COMPILE_FLAGS = (
    "-std=c++17", "-O1",
    "-DGLOBAL=extern", "-DCACHE_LINE_SIZE=64", "-DVAL_SIZE=4",
    "-DKEY_SIZE=8", "-DMASSTREE_USE=0", "-DCLOCKS_PER_US=2100",
    "-DBACK_OFF=1", "-DWAL=0", "-DNO_WAIT_LOCKING_IN_VALIDATION=1",
    "-DTRACE=0", "-DSORT_VARIANT=0", "-DKEY_SORT=0",
    "-DPARTITION_TABLE=0",
)
COMPILE_FLAGS_SHA256 = hashlib.sha256(
    json.dumps(_COMPILE_FLAGS, separators=(",", ":")).encode("utf-8")
).hexdigest()


class OracleStatus(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"
    UNAVAILABLE = "UNAVAILABLE"


class OracleRejectKind(str, Enum):
    STRUCTURE = "structure"
    COMPILE = "compile"
    TIMEOUT = "timeout"
    EXECUTION = "execution"
    PROTOCOL = "protocol"
    NONDETERMINISTIC = "nondeterministic"
    MUTATION = "mutation"
    AXIOM = "axiom"


class SwoAxiom(str, Enum):
    IRREFLEXIVE = "irreflexive"
    ASYMMETRIC = "asymmetric"
    TRANSITIVE = "transitive"
    TRANSITIVE_EQUIVALENCE = "transitive-equivalence"


@dataclass(frozen=True)
class SwoCounterexample:
    axiom: SwoAxiom
    input_pairs: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "axiom": self.axiom.value,
            "input_pairs": [
                {"lhs_index": lhs, "rhs_index": rhs}
                for lhs, rhs in self.input_pairs
            ],
        }


@dataclass(frozen=True)
class CompilerDiagnostic:
    """Bounded compiler diagnostic retained for operators, never for verdicts."""

    text: str
    captured_bytes: int
    total_bytes: int
    sha256: str
    truncated: bool

    def metadata_dict(self) -> dict[str, object]:
        # Candidate source can be quoted in ``text``.  WAL/critic get metadata
        # only; the bounded body remains on the in-process result for diagnosis.
        return {
            "captured_bytes": self.captured_bytes,
            "total_bytes": self.total_bytes,
            "sha256": self.sha256,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class SortSwoFinding:
    kind: OracleRejectKind
    reason_code: str
    counterexample: Optional[SwoCounterexample] = None
    input_pairs: tuple[tuple[int, int], ...] = ()
    corpus_id: str = CORPUS_ID
    order_id: Optional[int] = None
    observations: tuple[Mapping[str, object], ...] = ()
    compiler_diagnostic: Optional[CompilerDiagnostic] = None

    def as_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "kind": self.kind.value,
            "reason_code": self.reason_code,
            "corpus_id": self.corpus_id,
        }
        if self.order_id is not None:
            out["order_id"] = self.order_id
        if self.counterexample is not None:
            out["counterexample"] = self.counterexample.as_dict()
        if self.input_pairs:
            out["input_pairs"] = [
                {"lhs_index": lhs, "rhs_index": rhs}
                for lhs, rhs in self.input_pairs
            ]
        if self.observations:
            out["observations"] = [dict(item) for item in self.observations]
        if self.compiler_diagnostic is not None:
            out["compiler_diagnostic"] = self.compiler_diagnostic.metadata_dict()
        return out


@dataclass(frozen=True)
class OracleReceipt:
    contract_id: str
    materialized_hole_sha256: str
    proposal_sha256: str
    corpus_id: str
    corpus_version: int
    compiler_realpath: str
    compiler_version: str
    compile_flags_sha256: str
    tu_sha256: str
    tu_template_sha256: str
    dependency_root_realpath: str
    dependency_config_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "materialized_hole_sha256": self.materialized_hole_sha256,
            "proposal_sha256": self.proposal_sha256,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "compiler_realpath": self.compiler_realpath,
            "compiler_version": self.compiler_version,
            "compile_flags_sha256": self.compile_flags_sha256,
            "tu_sha256": self.tu_sha256,
            "tu_template_sha256": self.tu_template_sha256,
            "dependency_root_realpath": self.dependency_root_realpath,
            "dependency_config_sha256": self.dependency_config_sha256,
        }


@dataclass(frozen=True)
class OracleEnvironmentCandidate:
    """resolver が実際に検査した bounded な候補 1 件。"""

    origin: str
    path: Optional[Path]
    outcome: str

    def __post_init__(self) -> None:
        if type(self.origin) is not str or not self.origin or len(self.origin) > 128:
            raise ValueError("oracle environment candidate origin is invalid")
        if self.outcome not in _ENVIRONMENT_CANDIDATE_OUTCOMES:
            raise ValueError("oracle environment candidate outcome is invalid")
        if self.path is not None and not isinstance(self.path, Path):
            raise TypeError("oracle environment candidate path must be Path or None")

    def private_dict(self) -> dict[str, object]:
        return {
            "origin": self.origin,
            "outcome": self.outcome,
            "path": None if self.path is None else os.fspath(self.path),
        }

    def durable_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "origin": self.origin,
            "outcome": self.outcome,
        }
        if self.path is not None:
            path_text = os.fspath(self.path)
            basename = self.path.name
            out["path_basename"] = basename[:_MAX_ENVIRONMENT_BASENAME_CHARS]
            out["path_sha256"] = hashlib.sha256(
                path_text.encode("utf-8", errors="surrogatepass")
            ).hexdigest()
        return out


@dataclass(frozen=True)
class OracleEnvironmentResolutionFailure:
    """成功値と排他的な resolver failure union member。"""

    detail_code: str
    compiler_candidates: tuple[OracleEnvironmentCandidate, ...]
    dependency_candidates: tuple[OracleEnvironmentCandidate, ...]

    def __post_init__(self) -> None:
        if self.detail_code not in {
            "oracle-environment-compiler-unresolved",
            "oracle-environment-dependency-unresolved",
            "oracle-environment-compiler-and-dependency-unresolved",
        }:
            raise ValueError("unknown oracle environment resolution detail_code")
        for candidates in (self.compiler_candidates, self.dependency_candidates):
            if not candidates or len(candidates) > _MAX_ENVIRONMENT_CANDIDATES:
                raise ValueError("oracle environment candidate count is out of bounds")
            if any(type(item) is not OracleEnvironmentCandidate for item in candidates):
                raise TypeError("oracle environment candidates must use the exact type")

    @property
    def failed_legs(self) -> tuple[str, ...]:
        if self.detail_code == "oracle-environment-compiler-unresolved":
            return ("compiler",)
        if self.detail_code == "oracle-environment-dependency-unresolved":
            return ("dependency",)
        return ("compiler", "dependency")

    def private_dict(self) -> dict[str, object]:
        return {
            "detail_code": self.detail_code,
            "failed_legs": list(self.failed_legs),
            "compiler_candidates": [
                item.private_dict() for item in self.compiler_candidates
            ],
            "dependency_candidates": [
                item.private_dict() for item in self.dependency_candidates
            ],
        }

    def durable_dict(self) -> dict[str, object]:
        return {
            "detail_code": self.detail_code,
            "failed_legs": list(self.failed_legs),
            "compiler_candidates": [
                item.durable_dict() for item in self.compiler_candidates
            ],
            "dependency_candidates": [
                item.durable_dict() for item in self.dependency_candidates
            ],
        }


@dataclass(frozen=True)
class OracleInfrastructureFailure:
    reason_code: str
    phase: str
    detail_code: str
    compiler_diagnostic: Optional[CompilerDiagnostic] = None
    environment_resolution: Optional[OracleEnvironmentResolutionFailure] = None
    dependency_config_sha256: Optional[str] = None

    def as_dict(self) -> dict[str, object]:
        """durable/WAL 専用の機体非依存射影。"""
        out: dict[str, object] = {
            "reason_code": self.reason_code,
            "phase": self.phase,
            "detail_code": self.detail_code,
        }
        if self.compiler_diagnostic is not None:
            out["compiler_diagnostic"] = self.compiler_diagnostic.metadata_dict()
        if self.environment_resolution is not None:
            out["environment_resolution"] = (
                self.environment_resolution.durable_dict()
            )
        if self.dependency_config_sha256 is not None:
            out["dependency_config_sha256"] = self.dependency_config_sha256
        return out

    def private_dict(self) -> dict[str, object]:
        """mode 0700 の job staging だけへ出す operator 射影。"""
        out: dict[str, object] = {
            "reason_code": self.reason_code,
            "phase": self.phase,
            "detail_code": self.detail_code,
        }
        if self.compiler_diagnostic is not None:
            out["compiler_diagnostic"] = self.compiler_diagnostic.metadata_dict()
        if self.environment_resolution is not None:
            out["environment_resolution"] = (
                self.environment_resolution.private_dict()
            )
        if self.dependency_config_sha256 is not None:
            out["dependency_config_sha256"] = self.dependency_config_sha256
        return out


@dataclass(frozen=True)
class OracleEnvironment:
    compiler: Path
    ccbench_dir: Path
    dependency_root: Path


@dataclass(frozen=True)
class SortSwoOracleResult:
    status: OracleStatus
    materialized_hole_sha256: str
    proposal_sha256: str
    finding: Optional[SortSwoFinding] = None
    contract_id: str = ""
    receipt: Optional[OracleReceipt] = None
    infrastructure: Optional[OracleInfrastructureFailure] = None
    candidate_compile_finding: Optional[SortSwoFinding] = None

    def __post_init__(self) -> None:
        if self.contract_id == "":
            object.__setattr__(self, "contract_id", ORACLE_CONTRACT_ID)
        if self.contract_id != ORACLE_CONTRACT_ID:
            raise ValueError("oracle result contract_id mismatch")
        if self.receipt is not None and (
                self.receipt.contract_id != self.contract_id
                or self.receipt.materialized_hole_sha256
                != self.materialized_hole_sha256
                or self.receipt.proposal_sha256 != self.proposal_sha256
                or self.receipt.corpus_id != CORPUS_ID
                or self.receipt.corpus_version != CORPUS_VERSION
                or self.receipt.compile_flags_sha256 != COMPILE_FLAGS_SHA256
                or self.receipt.tu_template_sha256 != TU_TEMPLATE_SHA256):
            raise ValueError("oracle receipt/result binding mismatch")
        if self.status is OracleStatus.PASS and (
                self.finding is not None or self.receipt is None
                or self.infrastructure is not None):
            raise ValueError("PASS requires a receipt and no finding/infrastructure")
        if self.status is OracleStatus.REJECT and self.finding is None:
            raise ValueError("REJECT must carry a rejection finding")
        if self.status is OracleStatus.REJECT and self.infrastructure is not None:
            raise ValueError("REJECT must not carry infrastructure attribution")
        if self.status is OracleStatus.UNAVAILABLE and (
                self.finding is not None or self.infrastructure is None):
            raise ValueError("UNAVAILABLE requires separate infrastructure attribution")
        if self.candidate_compile_finding is not None and (
                self.status is not OracleStatus.UNAVAILABLE
                or self.infrastructure is None
                or self.infrastructure.phase != "trusted-postflight-compile"):
            raise ValueError(
                "candidate compile finding requires postflight UNAVAILABLE",
            )

    def as_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "status": self.status.value,
            "contract_id": self.contract_id,
            "materialized_hole_sha256": self.materialized_hole_sha256,
            "proposal_sha256": self.proposal_sha256,
        }
        if self.finding is not None:
            out["finding"] = self.finding.as_dict()
        if self.receipt is not None:
            out["receipt"] = self.receipt.as_dict()
        if self.infrastructure is not None:
            out["infrastructure"] = self.infrastructure.as_dict()
        if self.candidate_compile_finding is not None:
            out["candidate_compile_finding"] = (
                self.candidate_compile_finding.as_dict()
            )
        return out


class SortSwoOracleUnavailable(RuntimeError):
    """The trusted oracle infrastructure is unavailable; stop the attempt."""

    def __init__(self, result: Optional[SortSwoOracleResult] = None):
        super().__init__(INFRASTRUCTURE_REASON_CODE)
        self.result = result


class _EvaluationUnavailable(RuntimeError):
    def __init__(self, phase: str, detail_code: str):
        super().__init__(detail_code)
        self.phase = phase
        self.detail_code = detail_code


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_materialized_hole(materialized_source: str, marker_id: str) -> str:
    """Return exact post-materialization bytes between the marker's #if/#else."""
    lines = materialized_source.splitlines(keepends=True)
    begin = re.compile(r"EVOLVE-BLOCK-BEGIN\s+" + re.escape(marker_id) + r"\b")
    end = re.compile(r"EVOLVE-BLOCK-END\s+" + re.escape(marker_id) + r"\b")
    begins = [i for i, line in enumerate(lines) if begin.search(line)]
    ends = [i for i, line in enumerate(lines) if end.search(line)]
    if len(begins) != 1 or len(ends) != 1 or not begins[0] < ends[0]:
        raise ValueError("materialized marker boundary is not unique")
    body_range = range(begins[0] + 1, ends[0])
    if_lines = [i for i in body_range if re.match(r"^\s*#\s*if(?:def|ndef)?\b", lines[i])]
    else_lines = [i for i in body_range if re.match(r"^\s*#\s*else\b", lines[i])]
    endif_lines = [i for i in body_range if re.match(r"^\s*#\s*endif\b", lines[i])]
    if not (len(if_lines) == len(else_lines) == len(endif_lines) == 1):
        raise ValueError("materialized marker does not contain one #if/#else/#endif")
    if not if_lines[0] < else_lines[0] < endif_lines[0]:
        raise ValueError("materialized marker branch ordering is invalid")
    return "".join(lines[if_lines[0] + 1:else_lines[0]])


def _raw_string_end(source: str, start: int) -> Optional[int]:
    prefix = next(
        (value for value in ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"")
         if source.startswith(value, start)),
        None,
    )
    if prefix is None:
        return None
    delimiter_start = start + len(prefix)
    open_paren = source.find("(", delimiter_start, delimiter_start + 17)
    if open_paren < 0:
        return None
    delimiter = source[delimiter_start:open_paren]
    if any(ch.isspace() or ch in "()\\" for ch in delimiter):
        return None
    terminator = ")" + delimiter + '"'
    close = source.find(terminator, open_paren + 1)
    return None if close < 0 else close + len(terminator)


def _validate_single_sort_statement(statement: str) -> Optional[str]:
    """Check only the outer single unqualified ``sort(...)`` statement shape."""
    if len(statement.encode("utf-8")) > _MAX_SOURCE_BYTES:
        return "statement-too-large"
    pos = 0
    while pos < len(statement) and statement[pos].isspace():
        pos += 1
    match = re.match(r"sort\b", statement[pos:])
    if match is None:
        return "qualified-or-non-sort-callee"
    pos += match.end()
    while pos < len(statement) and statement[pos].isspace():
        pos += 1
    if pos >= len(statement) or statement[pos] != "(":
        return "sort-call-missing-open-paren"
    depth = 0
    i = pos
    close = -1
    while i < len(statement):
        ch = statement[i]
        if statement.startswith("//", i):
            newline = statement.find("\n", i + 2)
            i = len(statement) if newline < 0 else newline + 1
            continue
        if statement.startswith("/*", i):
            block_end = statement.find("*/", i + 2)
            if block_end < 0:
                return "unterminated-comment"
            i = block_end + 2
            continue
        raw_end = _raw_string_end(statement, i)
        if raw_end is not None:
            i = raw_end
            continue
        if ch in "'\"":
            quote = ch
            i += 1
            while i < len(statement):
                if statement[i] == "\\":
                    i += 2
                    continue
                if statement[i] == quote:
                    i += 1
                    break
                i += 1
            else:
                return "unterminated-literal"
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                close = i
                break
            if depth < 0:
                return "unbalanced-sort-call"
        i += 1
    if close < 0:
        return "unbalanced-sort-call"
    if statement[close + 1:].strip() != ";":
        return "not-a-single-sort-statement"
    return None


def check_relation_matrix(matrix: Sequence[bool], n: int) -> Optional[SwoCounterexample]:
    """Return the first deterministic SWO counterexample, or ``None``."""
    if type(n) is not int or n < 1 or len(matrix) != n * n:
        raise ValueError("relation matrix dimensions are invalid")

    def rel(lhs: int, rhs: int) -> bool:
        return bool(matrix[lhs * n + rhs])

    for i in range(n):
        if rel(i, i):
            return SwoCounterexample(SwoAxiom.IRREFLEXIVE, ((i, i),))
    for i in range(n):
        for j in range(n):
            if i != j and rel(i, j) and rel(j, i):
                return SwoCounterexample(SwoAxiom.ASYMMETRIC, ((i, j), (j, i)))
    for i in range(n):
        for j in range(n):
            if not rel(i, j):
                continue
            for k in range(n):
                if rel(j, k) and not rel(i, k):
                    return SwoCounterexample(
                        SwoAxiom.TRANSITIVE, ((i, j), (j, k), (i, k)),
                    )

    def equivalent(lhs: int, rhs: int) -> bool:
        return not rel(lhs, rhs) and not rel(rhs, lhs)

    for i in range(n):
        for j in range(n):
            if not equivalent(i, j):
                continue
            for k in range(n):
                if equivalent(j, k) and not equivalent(i, k):
                    return SwoCounterexample(
                        SwoAxiom.TRANSITIVE_EQUIVALENCE,
                        ((i, j), (j, k), (i, k), (k, i)),
                    )
    return None


_CORPUS_MANIFEST = (
    (
        (0, b"", 1, 0), (0, b"", 1, 0), (0, b"", 1, 0),
        (1, b"a", 0, 0), (2, b"aa", 1, 1), (0x7FFFFFFF, b"b", 2, 0),
        (0x80000000, b"\0", 2, 1), (0xFFFFFFFE, b"a\0", 1, 2),
        (0xFFFFFFFF, b"\x7f", 2, 2), (0, b"\x80", 1, 3),
        (1, b"aa", 2, 3), (2, b"b", 0, 0), (0x7FFFFFFF, b"a", 1, 0),
        (0x80000000, b"", 2, 4), (0xFFFFFFFE, b"\x80", 1, 2),
        (0xFFFFFFFF, b"a\0", 2, 5), (1, b"\0", 1, 3), (2, b"\x7f", 0, 0),
    ),
    (
        (0, b"", 1, 0), (0, b"", 1, 0), (0, b"", 1, 0),
        (1, b"\x80", 2, 5), (2, b"\x7f", 1, 3), (0x7FFFFFFF, b"a\0", 0, 0),
        (0x80000000, b"aa", 2, 4), (0xFFFFFFFE, b"", 1, 2),
        (0xFFFFFFFF, b"b", 2, 3), (0, b"\0", 1, 1),
        (1, b"b", 0, 0), (2, b"a", 2, 2), (0x7FFFFFFF, b"\x80", 1, 0),
        (0x80000000, b"a", 2, 1), (0xFFFFFFFE, b"aa", 1, 3),
        (0xFFFFFFFF, b"\0", 2, 0), (1, b"a\0", 1, 2), (2, b"", 0, 0),
    ),
)


def _canonical_corpus_serialization() -> bytes:
    value = [
        [
            {
                "storage": storage,
                "key_hex": key.hex(),
                "pointer_kind": pointer_kind,
                "pointer_slot": pointer_slot,
            }
            for storage, key, pointer_kind, pointer_slot in corpus
        ]
        for corpus in _CORPUS_MANIFEST
    ]
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")


CORPUS_SHA256 = hashlib.sha256(_canonical_corpus_serialization()).hexdigest()


def _cpp_byte_literal(value: bytes) -> str:
    return '"' + "".join(f"\\{byte:03o}" for byte in value) + '"'


def _render_corpus_cpp() -> str:
    lines = [
        "struct ElementSpec {",
        "  std::uint32_t storage;",
        "  const char* key;",
        "  std::size_t key_size;",
        "  int pointer_kind;",
        "  int pointer_slot;",
        "};",
    ]
    for corpus_id, corpus in enumerate(_CORPUS_MANIFEST):
        lines.append(f"static constexpr ElementSpec CORPUS{corpus_id}[18] = {{")
        for storage, key, pointer_kind, pointer_slot in corpus:
            lines.append(
                f"  {{{storage}u,{_cpp_byte_literal(key)},{len(key)}u,"
                f"{pointer_kind},{pointer_slot}}},"
            )
        lines.append("};")
    return "\n".join(lines) + "\n"


_CORPUS_CPP = _render_corpus_cpp()

_TU_PREFIX = r'''#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <limits>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <unistd.h>
#include <vector>
#include "include/masstree_wrapper.hh"
#include "include/tuple_body.hh"
#include "cc/silo/include/tuple.hh"
#include "cc/silo/include/silo_op_element.hh"
''' + _CORPUS_CPP + r'''
static constexpr std::size_t N = 18;
static constexpr unsigned NO_WITNESS = std::numeric_limits<unsigned>::max();
class OracleWriteSet;
struct OracleIterator {
  OracleWriteSet* owner;
  std::size_t position;
  friend bool operator==(OracleIterator lhs, OracleIterator rhs) {
    return lhs.owner == rhs.owner && lhs.position == rhs.position;
  }
  friend bool operator!=(OracleIterator lhs, OracleIterator rhs) { return !(lhs == rhs); }
};
class OracleWriteSet {
 public:
  std::vector<WriteElement<Tuple>> elements;
  void reserve(std::size_t count) { elements.reserve(count); }
  template <class... Args> void emplace_back(Args&&... args) {
    elements.emplace_back(std::forward<Args>(args)...);
  }
  OracleIterator begin() { return OracleIterator{this, 0}; }
  OracleIterator end() { return OracleIterator{this, elements.size()}; }
  WriteElement<Tuple>& operator[](std::size_t index) { return elements[index]; }
};
static OracleWriteSet* active_write_set = nullptr;
static std::array<unsigned, N> active_order{};
static std::array<unsigned char, N * N> relation{};
static bool sort_called = false;
static int oracle_test_mode = 0;
static std::vector<unsigned char> trusted_snapshot;
static unsigned mutation_lhs = NO_WITNESS;
static unsigned mutation_rhs = NO_WITNESS;
static unsigned repeat_lhs = NO_WITNESS;
static unsigned repeat_rhs = NO_WITNESS;
static unsigned repeat_values = 0;

static void append_snapshot_bytes(std::vector<unsigned char>& out,
                                  const void* data, std::size_t size) {
  if (size == 0) return;
  const auto* bytes = static_cast<const unsigned char*>(data);
  out.insert(out.end(), bytes, bytes + size);
}

static std::vector<unsigned char> snapshot_corpus() {
  std::vector<unsigned char> out;
  if (active_write_set == nullptr) return out;
  for (auto& element : active_write_set->elements) {
    append_snapshot_bytes(out, &element, sizeof(element));
    const std::size_t key_size = element.key_.size();
    append_snapshot_bytes(out, &key_size, sizeof(key_size));
    append_snapshot_bytes(out, element.key_.data(), key_size);
    const auto body_key = element.body_.get_key();
    const HeapObject& body_object = element.body_.get_value();
    const void* body_value_data = body_object.data();
    const std::size_t body_key_size = body_key.size();
    const std::size_t body_value_size = body_object.size();
    const unsigned char body_value_present =
        body_value_data == nullptr ? 0u : 1u;
    append_snapshot_bytes(out, &body_key_size, sizeof(body_key_size));
    append_snapshot_bytes(out, body_key.data(), body_key_size);
    append_snapshot_bytes(out, &body_value_present, sizeof(body_value_present));
    append_snapshot_bytes(out, &body_value_size, sizeof(body_value_size));
    append_snapshot_bytes(out, body_value_data, body_value_size);
    const std::size_t value_size = element.get_val_length();
    append_snapshot_bytes(out, &value_size, sizeof(value_size));
    append_snapshot_bytes(out, element.get_val_ptr(), value_size);
    if (element.rcdptr_ != nullptr) {
      append_snapshot_bytes(out, element.rcdptr_, sizeof(Tuple));
    }
  }
  return out;
}

static bool snapshot_unchanged(unsigned lhs, unsigned rhs) {
  if (snapshot_corpus() == trusted_snapshot) return true;
  if (mutation_lhs == NO_WITNESS) {
    mutation_lhs = lhs;
    mutation_rhs = rhs;
  }
  return false;
}

static bool write_all(int fd, const void* data, std::size_t size) {
  const auto* bytes = static_cast<const unsigned char*>(data);
  while (size != 0) {
    const ssize_t count = ::write(fd, bytes, size);
    if (count <= 0) return false;
    bytes += count;
    size -= static_cast<std::size_t>(count);
  }
  return true;
}

template <class Compare>
void sort(OracleIterator first, OracleIterator last, Compare comparator) {
  if (sort_called || active_write_set == nullptr || first != active_write_set->begin()
      || last != active_write_set->end()) std::_Exit(71);
  sort_called = true;
  for (std::size_t lhs_position = 0; lhs_position < N; ++lhs_position) {
    for (std::size_t rhs_position = 0; rhs_position < N; ++rhs_position) {
      const unsigned lhs = active_order[lhs_position];
      const unsigned rhs = active_order[rhs_position];
      try {
        const WriteElement<Tuple>& lhs_element = (*active_write_set)[lhs_position];
        const WriteElement<Tuple>& rhs_element = (*active_write_set)[rhs_position];
        relation[lhs * N + rhs] = comparator(lhs_element, rhs_element) ? 1 : 0;
      } catch (...) { std::_Exit(72); }
      if (!snapshot_unchanged(lhs, rhs)) return;
    }
  }
  for (std::size_t flat = N * N; flat-- > 0;) {
    const std::size_t lhs_position = flat / N;
    const std::size_t rhs_position = flat % N;
    const unsigned lhs = active_order[lhs_position];
    const unsigned rhs = active_order[rhs_position];
    bool observed = false;
    try {
      const WriteElement<Tuple>& lhs_element = (*active_write_set)[lhs_position];
      const WriteElement<Tuple>& rhs_element = (*active_write_set)[rhs_position];
      observed = comparator(lhs_element, rhs_element);
    } catch (...) { std::_Exit(72); }
    if (!snapshot_unchanged(lhs, rhs)) return;
    const unsigned char first_value = relation[lhs * N + rhs];
    if (repeat_lhs == NO_WITNESS && observed != (first_value != 0)) {
      repeat_lhs = lhs;
      repeat_rhs = rhs;
      repeat_values = static_cast<unsigned>(first_value)
                    | (static_cast<unsigned>(observed) << 1u);
    }
  }
}

static std::array<unsigned, N> order_for(int order_id) {
  std::array<unsigned, N> order{};
  for (unsigned i = 0; i < N; ++i) order[i] = i;
  if (order_id == 1) {
    for (unsigned i = 0; i < N / 2; ++i) {
      const unsigned tmp = order[i]; order[i] = order[N - 1 - i]; order[N - 1 - i] = tmp;
    }
  } else if (order_id == 2) {
    std::uint32_t state = 0x3165a17u;
    for (unsigned i = N - 1; i > 0; --i) {
      state = state * 1664525u + 1013904223u;
      const unsigned j = state % (i + 1);
      const unsigned tmp = order[i]; order[i] = order[j]; order[j] = tmp;
    }
  }
  return order;
}

int main(int argc, char** argv) {
  if (argc != 4 && argc != 5) return 64;
  const int corpus_id = std::atoi(argv[1]);
  const int order_id = std::atoi(argv[2]);
  const int output_fd = std::atoi(argv[3]);
  if (corpus_id < 0 || corpus_id > 1 || order_id < 0 || order_id > 2 || output_fd < 0) return 65;
  if (argc == 5) oracle_test_mode = std::atoi(argv[4]);
  const ElementSpec* specs = corpus_id == 0 ? CORPUS0 : CORPUS1;
  std::array<Tuple, 4> aliases{};
  std::array<std::unique_ptr<Tuple>, 6> separate{};
  for (auto& item : separate) item = std::make_unique<Tuple>();
  active_order = order_for(order_id);
  OracleWriteSet write_set_;
  write_set_.reserve(N);
  for (unsigned position = 0; position < N; ++position) {
    const ElementSpec& spec = specs[active_order[position]];
    Tuple* pointer = nullptr;
    if (spec.pointer_kind == 1) pointer = &aliases[spec.pointer_slot];
    if (spec.pointer_kind == 2) pointer = separate[spec.pointer_slot].get();
    write_set_.emplace_back(static_cast<Storage>(spec.storage),
        std::string_view(spec.key, spec.key_size), pointer, OpType::UPDATE);
  }
  active_write_set = &write_set_;
  trusted_snapshot = snapshot_corpus();
'''

_TU_SUFFIX = r'''
  snapshot_unchanged(NO_WITNESS, NO_WITNESS);
  if (!sort_called) return 73;
  struct Header { char magic[8]; std::uint32_t version; std::uint32_t corpus;
                  std::uint32_t order; std::uint32_t n;
                  std::uint32_t mutation_lhs; std::uint32_t mutation_rhs;
                  std::uint32_t repeat_lhs; std::uint32_t repeat_rhs;
                  std::uint32_t repeat_values; };
  const Header header{{'I','Z','S','W','O','2','\0','\0'}, 2u,
                      static_cast<std::uint32_t>(corpus_id),
                      static_cast<std::uint32_t>(order_id), static_cast<std::uint32_t>(N),
                      mutation_lhs, mutation_rhs, repeat_lhs, repeat_rhs, repeat_values};
  const bool wrote = write_all(output_fd, &header, sizeof(header))
                     && write_all(output_fd, relation.data(), relation.size());
  std::_Exit(wrote ? 0 : 74);
}
'''

_STATEMENT_PLACEHOLDER = "/*__IZANAGI_SORT_STATEMENT__*/"


def _translation_unit(statement: str) -> str:
    return _TU_PREFIX + statement + _TU_SUFFIX


TU_TEMPLATE_SHA256 = hashlib.sha256(
    _translation_unit(_STATEMENT_PLACEHOLDER).encode("utf-8")
).hexdigest()


def _limit_compile() -> None:
    # A distinct soft signal lets us attribute CPU exhaustion to the candidate;
    # a wall timeout or unrelated signal remains infrastructure-unavailable.
    resource.setrlimit(resource.RLIMIT_CPU, (8, 9))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _limit_run() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (1, 2))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _communicate_hard_timeout(
    process: subprocess.Popen[bytes], timeout_s: float,
) -> tuple[bool, int]:
    try:
        process.communicate(timeout=timeout_s)
        return False, int(process.returncode)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        return True, int(process.returncode)


def _bounded_diagnostic(path: Path) -> CompilerDiagnostic:
    digest = hashlib.sha256()
    captured = bytearray()
    total = 0
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                total += len(chunk)
                if len(captured) < _MAX_DIAGNOSTIC_BYTES:
                    captured.extend(chunk[:_MAX_DIAGNOSTIC_BYTES - len(captured)])
    except OSError:
        return CompilerDiagnostic("", 0, 0, hashlib.sha256(b"").hexdigest(), False)
    body = bytes(captured)
    return CompilerDiagnostic(
        text=body.decode("utf-8", errors="replace"),
        captured_bytes=len(body),
        total_bytes=total,
        sha256=digest.hexdigest(),
        truncated=total > len(body),
    )


def _compile_command(
    source_path: Path, executable: Path, *, compiler: str,
    ccbench_dir: Path, masstree_dir: Path,
) -> list[str]:
    return [
        compiler, *_COMPILE_FLAGS[:2], "-o", str(executable), str(source_path),
        "-I", str(ccbench_dir), "-I", str(ccbench_dir / "include"),
        "-I", str(masstree_dir), *_COMPILE_FLAGS[2:],
    ]


def _compile(
    source: str, source_path: Path, executable: Path, *, compiler: str,
    ccbench_dir: Path, masstree_dir: Path,
) -> tuple[Optional[SortSwoFinding], bool]:
    source_path.write_text(source, encoding="utf-8")
    command = _compile_command(
        source_path, executable, compiler=compiler,
        ccbench_dir=ccbench_dir, masstree_dir=masstree_dir,
    )
    diagnostic_path = source_path.with_suffix(source_path.suffix + ".stderr")
    try:
        with diagnostic_path.open("wb") as diagnostic_stream:
            process = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=diagnostic_stream,
                start_new_session=True, preexec_fn=_limit_compile,
            )
            timed_out, returncode = _communicate_hard_timeout(
                process, _COMPILE_TIMEOUT_S,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        raw_error = str(exc).encode("utf-8", errors="replace")
        bounded_error = raw_error[:_MAX_DIAGNOSTIC_BYTES]
        diagnostic = CompilerDiagnostic(
            bounded_error.decode("utf-8", errors="replace"),
            len(bounded_error), len(raw_error),
            hashlib.sha256(raw_error).hexdigest(),
            len(raw_error) > _MAX_DIAGNOSTIC_BYTES,
        )
        return SortSwoFinding(
            OracleRejectKind.COMPILE, "compiler-launch-unavailable",
            compiler_diagnostic=diagnostic,
        ), True
    diagnostic = _bounded_diagnostic(diagnostic_path)
    if timed_out:
        return SortSwoFinding(
            OracleRejectKind.TIMEOUT, "compile-wall-timeout",
            compiler_diagnostic=diagnostic,
        ), True
    if returncode == -signal.SIGXCPU:
        return SortSwoFinding(
            OracleRejectKind.TIMEOUT, "candidate-compile-cpu-limit-exceeded",
            compiler_diagnostic=diagnostic,
        ), False
    if returncode < 0:
        return SortSwoFinding(
            OracleRejectKind.COMPILE, "compiler-signal-unavailable",
            compiler_diagnostic=diagnostic,
        ), True
    if returncode != 0 or not executable.is_file():
        return SortSwoFinding(
            OracleRejectKind.COMPILE, "candidate-compile-failed",
            compiler_diagnostic=diagnostic,
        ), False
    return None, False


def _read_all(fd: int, expected: int) -> bytes:
    chunks = []
    remaining = expected + 1
    while remaining:
        try:
            chunk = os.read(fd, remaining)
        except BlockingIOError:
            break
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _run_matrix(
    executable: Path, corpus: int, order: int, *, test_mode: Optional[int] = None,
) -> tuple[Optional[bytes], Optional[SortSwoFinding]]:
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    command = [str(executable), str(corpus), str(order), str(write_fd)]
    if test_mode is not None:
        command.append(str(test_mode))
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, pass_fds=(write_fd,),
            start_new_session=True, preexec_fn=_limit_run,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        os.close(read_fd)
        os.close(write_fd)
        raise _EvaluationUnavailable("run-launch", "loader-or-launch-failed") from exc
    os.close(write_fd)
    timed_out, returncode = _communicate_hard_timeout(process, _RUN_TIMEOUT_S)
    record = _read_all(read_fd, _RECORD_SIZE)
    os.close(read_fd)
    if timed_out:
        raise _EvaluationUnavailable("run-wall-timeout", "candidate-run-wall-timeout")
    if returncode == -signal.SIGXCPU:
        return None, SortSwoFinding(
            OracleRejectKind.TIMEOUT, "candidate-run-cpu-limit-exceeded",
            corpus_id=f"{CORPUS_ID}/corpus-{corpus}", order_id=order,
        )
    if returncode < 0:
        raise _EvaluationUnavailable("run-signal", f"candidate-run-signal-{abs(returncode)}")
    if returncode != 0:
        if returncode in {71, 72, 73}:
            return None, SortSwoFinding(
                OracleRejectKind.EXECUTION,
                {
                    71: "candidate-sort-call-contract-violation",
                    72: "candidate-comparator-threw",
                    73: "candidate-sort-not-called",
                }[returncode],
                corpus_id=f"{CORPUS_ID}/corpus-{corpus}", order_id=order,
            )
        raise _EvaluationUnavailable("run-exit", f"unattributed-run-exit-{returncode}")
    if len(record) != _RECORD_SIZE:
        raise _EvaluationUnavailable("protocol", "record-size-mismatch")
    (magic, version, got_corpus, got_order, n, mutation_lhs, mutation_rhs,
     repeat_lhs, repeat_rhs, repeat_values) = _HEADER.unpack(record[:_HEADER.size])
    if (magic != _MAGIC or version != PROTOCOL_VERSION or got_corpus != corpus
            or got_order != order or n != _N):
        raise _EvaluationUnavailable("protocol", "record-header-mismatch")
    matrix = record[_HEADER.size:]
    if any(value not in (0, 1) for value in matrix):
        raise _EvaluationUnavailable("protocol", "record-value-out-of-range")
    execution_corpus_id = f"{CORPUS_ID}/corpus-{corpus}"
    if mutation_lhs != _WITNESS_NONE:
        if mutation_lhs >= _N or mutation_rhs >= _N:
            raise _EvaluationUnavailable("protocol", "mutation-witness-out-of-range")
        return None, SortSwoFinding(
            OracleRejectKind.MUTATION, "corpus-mutated-by-comparator",
            input_pairs=((mutation_lhs, mutation_rhs),),
            corpus_id=execution_corpus_id, order_id=order,
            observations=({"point": "after-call", "changed": True},),
        )
    if repeat_lhs != _WITNESS_NONE:
        if (repeat_lhs >= _N or repeat_rhs >= _N
                or repeat_values not in {1, 2}):
            raise _EvaluationUnavailable("protocol", "repeat-witness-invalid")
        pair = (repeat_lhs, repeat_rhs)
        return None, SortSwoFinding(
            OracleRejectKind.NONDETERMINISTIC,
            "relation-varies-within-process",
            input_pairs=(pair,), corpus_id=execution_corpus_id, order_id=order,
            observations=(
                {"point": "first-pass", "lhs_index": repeat_lhs,
                 "rhs_index": repeat_rhs, "value": bool(repeat_values & 1)},
                {"point": "second-pass-after-other-pairs", "lhs_index": repeat_lhs,
                 "rhs_index": repeat_rhs, "value": bool(repeat_values & 2)},
            ),
        )
    return matrix, None


def resolve_oracle_environment(
    ccbench_dir: os.PathLike[str] | str,
    *,
    compiler: Optional[os.PathLike[str] | str] = None,
    dependency_root: Optional[os.PathLike[str] | str] = None,
) -> OracleEnvironment | OracleEnvironmentResolutionFailure:
    """Resolve bounded defaults into a success/failure closed union."""
    ccbench = Path(ccbench_dir).resolve()
    compiler_inputs: list[tuple[str, object | None, str]] = []
    if compiler is not None:
        compiler_inputs.append(("argument:compiler", compiler, "not-configured"))
    else:
        for env_name in ("IZANAGI_SORT_SWO_CXX", "CXX"):
            compiler_inputs.append((
                f"environment:{env_name}", os.environ.get(env_name),
                "not-configured",
            ))
        compiler_inputs.append((
            "path:g++", shutil.which("g++"), "not-found",
        ))

    dependency_inputs: list[tuple[str, object | None, str]] = []
    if dependency_root is not None:
        dependency_inputs.append((
            "argument:dependency-root", dependency_root, "not-configured",
        ))
    else:
        dependency_inputs.append((
            "environment:IZANAGI_SORT_SWO_MASSTREE_ROOT",
            os.environ.get("IZANAGI_SORT_SWO_MASSTREE_ROOT"),
            "not-configured",
        ))

    compiler_records: list[OracleEnvironmentCandidate] = []
    compiler_path: Optional[Path] = None
    for origin, raw_candidate, absent_outcome in compiler_inputs:
        if raw_candidate is None or raw_candidate == "":
            compiler_records.append(OracleEnvironmentCandidate(
                origin, None, absent_outcome,
            ))
            continue
        try:
            candidate = Path(raw_candidate)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                compiler_path = candidate.resolve()
                compiler_records.append(OracleEnvironmentCandidate(
                    origin, candidate, "selected",
                ))
                break
            outcome = (
                "not-executable" if candidate.is_file()
                else "not-regular-file"
                if candidate.exists() or candidate.is_symlink()
                else "missing"
            )
        except (OSError, TypeError, ValueError):
            candidate = None
            outcome = "invalid-path"
        compiler_records.append(OracleEnvironmentCandidate(
            origin, candidate, outcome,
        ))

    dependency_records: list[OracleEnvironmentCandidate] = []
    dependency_path: Optional[Path] = None
    for origin, raw_candidate, absent_outcome in dependency_inputs:
        if raw_candidate is None or raw_candidate == "":
            dependency_records.append(OracleEnvironmentCandidate(
                origin, None, absent_outcome,
            ))
            continue
        try:
            candidate = Path(raw_candidate)
            config = candidate / "config.h"
            if config.is_file():
                dependency_path = candidate.resolve()
                dependency_records.append(OracleEnvironmentCandidate(
                    origin, candidate, "selected",
                ))
                break
            outcome = (
                "config-h-not-regular-file"
                if config.exists() or config.is_symlink()
                else "config-h-missing"
            )
        except (OSError, TypeError, ValueError):
            candidate = None
            outcome = "invalid-path"
        dependency_records.append(OracleEnvironmentCandidate(
            origin, candidate, outcome,
        ))

    if compiler_path is None or dependency_path is None:
        detail_code = (
            "oracle-environment-compiler-and-dependency-unresolved"
            if compiler_path is None and dependency_path is None
            else "oracle-environment-compiler-unresolved"
            if compiler_path is None
            else "oracle-environment-dependency-unresolved"
        )
        return OracleEnvironmentResolutionFailure(
            detail_code,
            tuple(compiler_records),
            tuple(dependency_records),
        )
    return OracleEnvironment(compiler_path, ccbench, dependency_path)


def _evaluate_executable(
    executable: Path, *, test_mode: Optional[int] = None,
) -> Optional[SortSwoFinding]:
    for corpus in _CORPORA:
        matrices = []
        for order in _ORDERS:
            matrix, finding = _run_matrix(
                executable, corpus, order, test_mode=test_mode,
            )
            if finding is not None:
                return finding
            assert matrix is not None
            matrices.append(matrix)
        if matrices[1:] != matrices[:-1]:
            first = next(
                index for index, values in enumerate(zip(*matrices))
                if len(set(values)) != 1
            )
            pair = (first // _N, first % _N)
            return SortSwoFinding(
                OracleRejectKind.NONDETERMINISTIC,
                "relation-varies-across-process-order",
                input_pairs=(pair,),
                corpus_id=f"{CORPUS_ID}/corpus-{corpus}",
                order_id=_ORDERS[0],
                observations=tuple(
                    {"point": "fresh-process", "order_id": order,
                     "lhs_index": pair[0], "rhs_index": pair[1],
                     "value": bool(matrix[first])}
                    for order, matrix in zip(_ORDERS, matrices)
                ),
            )
        counterexample = check_relation_matrix(matrices[0], _N)
        if counterexample is not None:
            return SortSwoFinding(
                OracleRejectKind.AXIOM,
                f"swo-{counterexample.axiom.value}",
                counterexample,
                corpus_id=f"{CORPUS_ID}/corpus-{corpus}",
                order_id=_ORDERS[0],
            )
    return None


_AXIOM_CHECKER_SOURCE_FUNCTIONS = (
    check_relation_matrix,
    _evaluate_executable,
    _run_matrix,
    _compile_command,
)


def _source_bundle_sha256(
    functions: Sequence[Callable[..., object]], *, n: int,
    orders: Sequence[int], corpora: Sequence[int],
) -> str:
    """Hash the enumerated checker source and semantic constants.

    This binding is deliberately enumerated, not a closure: moving decision
    logic into a helper outside ``functions`` does not change the identity.
    ``inspect.getsource`` failures propagate so module initialization fails
    closed instead of substituting an empty digest.
    """
    digest = hashlib.sha256()
    for function in functions:
        identity = (
            f"{function.__module__}.{function.__qualname__}".encode("utf-8")
        )
        source = inspect.getsource(function).encode("utf-8")
        for value in (identity, source):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    semantic_constants = json.dumps(
        {"_CORPORA": tuple(corpora), "_N": n, "_ORDERS": tuple(orders)},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    digest.update(len(semantic_constants).to_bytes(8, "big"))
    digest.update(semantic_constants)
    return digest.hexdigest()


AXIOM_CHECKER_IMPLEMENTATION_SHA256 = _source_bundle_sha256(
    _AXIOM_CHECKER_SOURCE_FUNCTIONS,
    n=_N,
    orders=_ORDERS,
    corpora=_CORPORA,
)
_ORACLE_CONTRACT_COMPONENTS_SCHEMA = "sort-swo-contract-components-v1"
_ORACLE_CONTRACT_COMPONENTS = {
    "axiom_checker_implementation_sha256": AXIOM_CHECKER_IMPLEMENTATION_SHA256,
    "compile_flags_sha256": COMPILE_FLAGS_SHA256,
    "corpus_sha256": CORPUS_SHA256,
    "tu_template_sha256": TU_TEMPLATE_SHA256,
}


def _contract_components_sha256(components: Mapping[str, str]) -> str:
    canonical = json.dumps(
        {
            "components": dict(components),
            "schema": _ORACLE_CONTRACT_COMPONENTS_SCHEMA,
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


ORACLE_COMPONENTS_SHA256 = _contract_components_sha256(
    _ORACLE_CONTRACT_COMPONENTS,
)
# The full x digest is authoritative; c/tu/f/a are diagnostic prefixes only.
ORACLE_CONTRACT_ID = (
    f"sort-swo-v{CONTRACT_VERSION}-corpus{CORPUS_VERSION}-"
    f"protocol{PROTOCOL_VERSION}-checker{AXIOM_CHECKER_VERSION}-"
    f"grammar{GRAMMAR_VERSION}-x{ORACLE_COMPONENTS_SHA256}-"
    f"c{CORPUS_SHA256[:12]}-tu{TU_TEMPLATE_SHA256[:12]}-"
    f"f{COMPILE_FLAGS_SHA256[:12]}-"
    f"a{AXIOM_CHECKER_IMPLEMENTATION_SHA256[:12]}"
)


def _compiler_version(compiler: Path) -> str:
    try:
        completed = subprocess.run(
            [os.fspath(compiler), "--version"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=_TOOL_IDENTITY_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _EvaluationUnavailable("compiler-identity", "compiler-version-unavailable") from exc
    output = completed.stdout[:4096]
    if completed.returncode != 0 or not output:
        raise _EvaluationUnavailable("compiler-identity", "compiler-version-unavailable")
    return output.decode("utf-8", errors="replace").strip()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(64 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def _receipt(
    *, environment: OracleEnvironment, compiler_version: str,
    materialized_hash: str, proposal_hash: str, source: str,
) -> OracleReceipt:
    return OracleReceipt(
        contract_id=ORACLE_CONTRACT_ID,
        materialized_hole_sha256=materialized_hash,
        proposal_sha256=proposal_hash,
        corpus_id=CORPUS_ID,
        corpus_version=CORPUS_VERSION,
        compiler_realpath=os.fspath(environment.compiler),
        compiler_version=compiler_version,
        compile_flags_sha256=COMPILE_FLAGS_SHA256,
        tu_sha256=_sha256(source),
        tu_template_sha256=TU_TEMPLATE_SHA256,
        dependency_root_realpath=os.fspath(environment.dependency_root),
        dependency_config_sha256=_file_sha256(environment.dependency_root / "config.h"),
    )


def _unavailable_result(
    materialized_hash: str, proposal_hash: str, *, phase: str,
    detail_code: str, receipt: Optional[OracleReceipt] = None,
    diagnostic: Optional[CompilerDiagnostic] = None,
    candidate_compile_finding: Optional[SortSwoFinding] = None,
    environment_resolution: Optional[OracleEnvironmentResolutionFailure] = None,
    environment: Optional[OracleEnvironment] = None,
) -> SortSwoOracleResult:
    dependency_config_sha256 = None
    if type(environment) is OracleEnvironment:
        try:
            dependency_config_sha256 = _file_sha256(
                environment.dependency_root / "config.h"
            )
        except OSError:
            dependency_config_sha256 = None
    return SortSwoOracleResult(
        OracleStatus.UNAVAILABLE, materialized_hash, proposal_hash,
        receipt=receipt,
        infrastructure=OracleInfrastructureFailure(
            INFRASTRUCTURE_REASON_CODE,
            phase,
            detail_code,
            compiler_diagnostic=diagnostic,
            environment_resolution=environment_resolution,
            dependency_config_sha256=dependency_config_sha256,
        ),
        candidate_compile_finding=candidate_compile_finding,
    )


def check_materialized_sort_swo(
    materialized_source: str,
    *,
    marker_id: str,
    proposal_source: str,
    environment: Optional[
        OracleEnvironment | OracleEnvironmentResolutionFailure
    ],
    scratch_root: Optional[os.PathLike[str] | str] = None,
    phase_marker: Optional[Callable[[], None]] = None,
) -> SortSwoOracleResult:
    """Check the exact post-materialization sort hole with a closed result.

    A postflight failure establishes only that the trusted control also failed
    after the candidate compile.  Candidate compile artifact removal is
    attempted before postflight.  Cleanup failure does not skip postflight: it
    runs in a fresh temporary directory, and classification proceeds from the
    postflight and candidate compile results.  Filesystem quota, cgroup
    resources, and host state remain shared; this is correlation, not a
    candidate-independent environment diagnosis.
    """
    proposal_hash = _sha256(proposal_source)
    try:
        statement = extract_materialized_hole(materialized_source, marker_id)
    except (TypeError, ValueError):
        statement = ""
        return SortSwoOracleResult(
            OracleStatus.REJECT, _sha256(statement), proposal_hash,
            SortSwoFinding(OracleRejectKind.STRUCTURE, "materialized-marker-invalid"),
        )
    materialized_hash = _sha256(statement)
    structural_reason = _validate_single_sort_statement(statement)
    if structural_reason is not None:
        return SortSwoOracleResult(
            OracleStatus.REJECT, materialized_hash, proposal_hash,
            SortSwoFinding(OracleRejectKind.STRUCTURE, structural_reason),
        )

    if type(environment) is OracleEnvironmentResolutionFailure:
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase="environment-resolution",
            detail_code=environment.detail_code,
            environment_resolution=environment,
        )
    if environment is None:
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase="environment-resolution", detail_code="oracle-environment-unresolved",
        )
    if type(environment) is not OracleEnvironment:
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase="environment-resolution", detail_code="oracle-environment-invalid",
        )
    ccbench = environment.ccbench_dir
    required_headers = (
        ccbench / "include" / "masstree_wrapper.hh",
        ccbench / "include" / "tuple_body.hh",
        ccbench / "cc" / "silo" / "include" / "tuple.hh",
        ccbench / "cc" / "silo" / "include" / "silo_op_element.hh",
    )
    if not all(path.is_file() for path in required_headers):
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase="environment-resolution", detail_code="required-header-missing",
            environment=environment,
        )

    try:
        if phase_marker is not None:
            phase_marker()
        compiler_version = _compiler_version(environment.compiler)
        with tempfile.TemporaryDirectory(
            prefix="izanagi_sort_swo_",
            dir=None if scratch_root is None else os.fspath(scratch_root),
        ) as temporary:
            temp = Path(temporary)
            control_source = _translation_unit(_TRUSTED_CONTROL_STATEMENT)
            control_executable = temp / "trusted-control"
            control_finding, control_unavailable = _compile(
                control_source, temp / "trusted-control.cpp", control_executable,
                compiler=os.fspath(environment.compiler), ccbench_dir=ccbench,
                masstree_dir=environment.dependency_root,
            )
            if control_unavailable or control_finding is not None:
                return _unavailable_result(
                    materialized_hash, proposal_hash,
                    phase="trusted-preflight-compile",
                    detail_code="trusted-positive-tu-compile-failed",
                    diagnostic=(None if control_finding is None
                                else control_finding.compiler_diagnostic),
                    environment=environment,
                )
            try:
                control_evaluation = _evaluate_executable(control_executable)
            except _EvaluationUnavailable as exc:
                return _unavailable_result(
                    materialized_hash, proposal_hash,
                    phase="trusted-preflight-run", detail_code=exc.detail_code,
                    environment=environment,
                )
            if control_evaluation is not None:
                return _unavailable_result(
                    materialized_hash, proposal_hash,
                    phase="trusted-preflight-run",
                    detail_code="trusted-positive-tu-semantic-failure",
                    environment=environment,
                )

            executable = temp / "oracle"
            candidate_source = _translation_unit(statement)
            receipt = _receipt(
                environment=environment, compiler_version=compiler_version,
                materialized_hash=materialized_hash, proposal_hash=proposal_hash,
                source=candidate_source,
            )
            finding, unavailable = _compile(
                candidate_source, temp / "oracle.cpp", executable,
                compiler=os.fspath(environment.compiler), ccbench_dir=ccbench,
                masstree_dir=environment.dependency_root,
            )
            if finding is not None or unavailable:
                candidate_artifacts = (
                    temp / "oracle.cpp",
                    executable,
                    (temp / "oracle.cpp").with_suffix(".cpp.stderr"),
                )
                candidate_cleanup_failed = False
                for artifact in candidate_artifacts:
                    try:
                        artifact.unlink(missing_ok=True)
                    except OSError:
                        candidate_cleanup_failed = True
                postflight_finding = None
                postflight_unavailable = False
                postflight_io_failed = False
                postflight_artifacts: tuple[Path, ...] = ()
                try:
                    with tempfile.TemporaryDirectory(
                        prefix="izanagi_sort_swo_postflight_",
                        dir=(None if scratch_root is None
                             else os.fspath(scratch_root)),
                    ) as postflight_temporary:
                        postflight_temp = Path(postflight_temporary)
                        postflight_source_path = (
                            postflight_temp / "trusted-postflight.cpp"
                        )
                        postflight_executable = (
                            postflight_temp / "trusted-postflight"
                        )
                        postflight_artifacts = (
                            postflight_source_path,
                            postflight_executable,
                            postflight_source_path.with_suffix(
                                postflight_source_path.suffix + ".stderr",
                            ),
                        )
                        try:
                            postflight_finding, postflight_unavailable = _compile(
                                control_source,
                                postflight_source_path,
                                postflight_executable,
                                compiler=os.fspath(environment.compiler),
                                ccbench_dir=ccbench,
                                masstree_dir=environment.dependency_root,
                            )
                        finally:
                            for artifact in postflight_artifacts:
                                try:
                                    artifact.unlink(missing_ok=True)
                                except OSError:
                                    postflight_io_failed = True
                except OSError:
                    postflight_io_failed = True
                if (postflight_io_failed or postflight_unavailable
                        or postflight_finding is not None):
                    return _unavailable_result(
                        materialized_hash,
                        proposal_hash,
                        phase="trusted-postflight-compile",
                        detail_code=(
                            _TRUSTED_POSTFLIGHT_COMPILE_WITH_CANDIDATE_CLEANUP_DETAIL_CODE
                            if candidate_cleanup_failed
                            else _TRUSTED_POSTFLIGHT_COMPILE_DETAIL_CODE
                        ),
                        receipt=receipt,
                        diagnostic=(
                            None if postflight_finding is None
                            else postflight_finding.compiler_diagnostic
                        ),
                        candidate_compile_finding=finding,
                        environment=environment,
                    )
            if unavailable:
                return _unavailable_result(
                    materialized_hash, proposal_hash,
                    phase="candidate-compile", detail_code=(
                        "candidate-compile-infrastructure-unavailable"
                        if finding is None else finding.reason_code
                    ), receipt=receipt,
                    diagnostic=(None if finding is None
                                else finding.compiler_diagnostic),
                    environment=environment,
                )
            if finding is None:
                try:
                    finding = _evaluate_executable(executable)
                except _EvaluationUnavailable as exc:
                    return _unavailable_result(
                        materialized_hash, proposal_hash,
                        phase=exc.phase, detail_code=exc.detail_code,
                        receipt=receipt,
                        environment=environment,
                    )
    except _EvaluationUnavailable as exc:
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase=exc.phase, detail_code=exc.detail_code,
            environment=environment,
        )
    except OSError as exc:
        return _unavailable_result(
            materialized_hash, proposal_hash,
            phase="oracle-io", detail_code=type(exc).__name__,
            environment=environment,
        )
    if finding is not None:
        return SortSwoOracleResult(
            OracleStatus.REJECT, materialized_hash, proposal_hash, finding,
            receipt=receipt,
        )
    return SortSwoOracleResult(
        OracleStatus.PASS, materialized_hash, proposal_hash,
        receipt=receipt,
    )


def rejection_digest(result: SortSwoOracleResult, *, diff_region: str, marker_id: str) -> dict[str, object]:
    """Project one oracle REJECT into the existing WAL/critic reject envelope."""
    if type(result) is not SortSwoOracleResult or result.status is not OracleStatus.REJECT:
        raise TypeError("oracle rejection digest requires an exact REJECT result")
    assert result.finding is not None
    finding = result.finding.as_dict()
    evidence = json.dumps(finding, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    out: dict[str, object] = {
        "rejection_type": "diff-quarantine",
        "subtype": "sort-swo-oracle",
        "reason": result.finding.reason_code,
        "diff_region": diff_region,
        "template_diff_id": marker_id,
        "evidence": evidence,
        "oracle_finding": finding,
        "materialized_hole_sha256": result.materialized_hole_sha256,
        "proposal_sha256": result.proposal_sha256,
        "oracle_contract_id": result.contract_id,
    }
    if result.receipt is not None:
        out["oracle_receipt"] = result.receipt.as_dict()
    return out


def attempt_record(result: SortSwoOracleResult) -> dict[str, object]:
    """Return a PASS/UNAVAILABLE record that never represents candidate fitness."""
    if type(result) is not SortSwoOracleResult or result.status not in {
            OracleStatus.PASS, OracleStatus.UNAVAILABLE}:
        raise TypeError("oracle attempt record requires exact PASS or UNAVAILABLE")
    out: dict[str, object] = {
        "event": "sort-swo-oracle-attempt",
        "classification": (
            "pass" if result.status is OracleStatus.PASS else "attempt-infra"
        ),
        "reason_code": (
            "sort-swo-oracle-pass"
            if result.status is OracleStatus.PASS else INFRASTRUCTURE_REASON_CODE
        ),
        "oracle_contract_id": result.contract_id,
        "materialized_hole_sha256": result.materialized_hole_sha256,
        "proposal_sha256": result.proposal_sha256,
    }
    if result.receipt is not None:
        out["oracle_receipt"] = result.receipt.as_dict()
    if result.infrastructure is not None:
        out["infrastructure"] = result.infrastructure.as_dict()
    if result.candidate_compile_finding is not None:
        out["candidate_compile_finding"] = (
            result.candidate_compile_finding.as_dict()
        )
    return out


def private_attempt_record(result: SortSwoOracleResult) -> dict[str, object]:
    """private job artifact 用。resolver 候補の full path をここだけへ残す。"""
    if type(result) is not SortSwoOracleResult or result.status not in {
            OracleStatus.PASS, OracleStatus.UNAVAILABLE}:
        raise TypeError("oracle private attempt record requires exact PASS or UNAVAILABLE")
    out: dict[str, object] = {
        "event": "sort-swo-oracle-attempt",
        "classification": (
            "pass" if result.status is OracleStatus.PASS else "attempt-infra"
        ),
        "reason_code": (
            "sort-swo-oracle-pass"
            if result.status is OracleStatus.PASS else INFRASTRUCTURE_REASON_CODE
        ),
        "oracle_contract_id": result.contract_id,
        "materialized_hole_sha256": result.materialized_hole_sha256,
        "proposal_sha256": result.proposal_sha256,
    }
    if result.receipt is not None:
        out["oracle_receipt"] = result.receipt.as_dict()
    if result.infrastructure is not None:
        out["infrastructure"] = result.infrastructure.private_dict()
    if result.candidate_compile_finding is not None:
        out["candidate_compile_finding"] = (
            result.candidate_compile_finding.as_dict()
        )
    return out


__all__ = [
    "AXIOM_CHECKER_IMPLEMENTATION_SHA256", "AXIOM_CHECKER_VERSION",
    "COMPILE_FLAGS_SHA256", "CONTRACT_VERSION",
    "CORPORA", "CORPUS_ID", "CORPUS_SHA256", "CORPUS_VERSION",
    "GRAMMAR_VERSION", "N", "ORDERS",
    "INFRASTRUCTURE_REASON_CODE", "ORACLE_COMPONENTS_SHA256",
    "ORACLE_CONTRACT_ID", "PROTOCOL_VERSION",
    "TU_TEMPLATE_SHA256", "CompilerDiagnostic", "OracleEnvironment",
    "OracleEnvironmentCandidate", "OracleEnvironmentResolutionFailure",
    "OracleInfrastructureFailure", "OracleReceipt", "OracleRejectKind",
    "OracleStatus", "SortSwoFinding", "SortSwoOracleResult",
    "SortSwoOracleUnavailable", "SwoAxiom", "SwoCounterexample",
    "attempt_record", "private_attempt_record", "check_materialized_sort_swo",
    "check_relation_matrix",
    "extract_materialized_hole", "rejection_digest",
    "resolve_oracle_environment",
]
