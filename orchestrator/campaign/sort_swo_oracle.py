#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finite, independent strict-weak-order oracle for synthesized sort holes.

The candidate's materialized ``sort(...)`` statement is compiled unchanged in
a hardened worker translation unit using the real CCBench
``WriteElement<Tuple>``.  The worker can emit only comparator booleans to a
fixed broker process.  Only that broker, after fully reaping the worker, owns
and writes the final protocol pipe.  Python checks the four strict-weak-order
axioms.

This is a counterexample finder over finite, versioned corpora.  It is not a
proof that arbitrary C++ is a strict weak ordering on every possible input.
It makes corpus mutation and candidate protocol writes impossible under the
sandbox boundary; it does not prove that candidate-controlled relation cells
represent the comparator's true return values.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import resource
import shlex
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
from array import array
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, Optional, Sequence

if __package__:
    from .evolve_block import extract_materialized_evolve_block
else:  # Direct broker subprocess executes this file by absolute path.
    from evolve_block import extract_materialized_evolve_block


CORPUS_VERSION = 2
PROTOCOL_VERSION = 3
AXIOM_CHECKER_VERSION = 3
GRAMMAR_VERSION = 1
CONTRACT_VERSION = 4

_MAGIC = b"IZSWO3\0\0"
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
# SHA-256 of the canonical CS-1 fixture's SHA256SUMS bytes.  The contract
# binds the dependency file-set declaration itself; receipts carry that pinned
# component alongside the machine-local dependency root and config hash.
DEPENDENCY_MANIFEST_SHA256 = (
    "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
)
SORT_SWO_GUARANTEE_BOUNDARY = (
    "guarantees[candidate-corpus-mutation-is-impossible,"
    "candidate-protocol-frame-write-is-impossible];"
    "does-not-guarantee[reported-relation-matrix-is-comparator-true-relation]"
)
_DEPENDENCY_MANIFEST_NAME = "SHA256SUMS"
_DEPENDENCY_MANIFEST_LINE = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)")
_MIN_DEPENDENCY_MANIFEST_CLOSURE = 31
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
    "-DFORCE_ENABLE_ASSERTIONS=1",
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
    dependency_manifest_sha256: str = DEPENDENCY_MANIFEST_SHA256
    guarantee_boundary: str = SORT_SWO_GUARANTEE_BOUNDARY

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
            "dependency_manifest_sha256": self.dependency_manifest_sha256,
            "guarantee_boundary": self.guarantee_boundary,
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
class _VerifiedDependencyRoot:
    root: Path
    manifest_sha256: str
    manifest_bytes: bytes
    files: tuple[tuple[str, str], ...]
    config_sha256: str


class _DependencyVerificationError(RuntimeError):
    def __init__(self, detail_code: str):
        super().__init__(detail_code)
        self.detail_code = detail_code


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
                or self.receipt.tu_template_sha256 != TU_TEMPLATE_SHA256
                or self.receipt.dependency_manifest_sha256
                != DEPENDENCY_MANIFEST_SHA256
                or self.receipt.guarantee_boundary
                != SORT_SWO_GUARANTEE_BOUNDARY):
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
    """Compatibility wrapper returning the former exact hole bytes."""
    return extract_materialized_evolve_block(materialized_source, marker_id).hole


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


_CORPUS_TOPOLOGY = (
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


def _element_payload(corpus_id: int, element_id: int) -> tuple[bytes, bytes, bytes]:
    return (
        f"element-body-key-c{corpus_id}-i{element_id:02d}".encode("ascii"),
        f"body-value-c{corpus_id}-i{element_id:02d}".encode("ascii"),
        f"write-value-c{corpus_id}-i{element_id:02d}".encode("ascii"),
    )


_CORPUS_MANIFEST = tuple(
    tuple(
        topology + _element_payload(corpus_id, element_id)
        for element_id, topology in enumerate(corpus)
    )
    for corpus_id, corpus in enumerate(_CORPUS_TOPOLOGY)
)

_TUPLE_BODY_MANIFEST = tuple(
    tuple(
        (
            f"tuple-body-key-c{corpus_id}-s{slot:02d}".encode("ascii"),
            f"tuple-body-value-c{corpus_id}-s{slot:02d}".encode("ascii"),
        )
        for slot in range(10)
    )
    for corpus_id in range(len(_CORPUS_TOPOLOGY))
)


def _canonical_corpus_serialization() -> bytes:
    value = [
        [
            {
                "storage": storage,
                "key_hex": key.hex(),
                "pointer_kind": pointer_kind,
                "pointer_slot": pointer_slot,
                "body_key_hex": body_key.hex(),
                "body_value_hex": body_value.hex(),
                "write_value_hex": write_value.hex(),
            }
            for (storage, key, pointer_kind, pointer_slot, body_key,
                 body_value, write_value) in corpus
        ]
        for corpus in _CORPUS_MANIFEST
    ]
    tuple_bodies = [
        [
            {"key_hex": key.hex(), "value_hex": body_value.hex()}
            for key, body_value in corpus
        ]
        for corpus in _TUPLE_BODY_MANIFEST
    ]
    return json.dumps(
        {"elements": value, "tuple_bodies": tuple_bodies},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
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
        "  const char* body_key;",
        "  std::size_t body_key_size;",
        "  const char* body_value;",
        "  std::size_t body_value_size;",
        "  const char* write_value;",
        "  std::size_t write_value_size;",
        "};",
        "struct TupleBodySpec {",
        "  const char* key;",
        "  std::size_t key_size;",
        "  const char* value;",
        "  std::size_t value_size;",
        "};",
    ]
    for corpus_id, corpus in enumerate(_CORPUS_MANIFEST):
        lines.append(f"static constexpr ElementSpec CORPUS{corpus_id}[18] = {{")
        for (storage, key, pointer_kind, pointer_slot, body_key, body_value,
             write_value) in corpus:
            lines.append(
                f"  {{{storage}u,{_cpp_byte_literal(key)},{len(key)}u,"
                f"{pointer_kind},{pointer_slot},"
                f"{_cpp_byte_literal(body_key)},{len(body_key)}u,"
                f"{_cpp_byte_literal(body_value)},{len(body_value)}u,"
                f"{_cpp_byte_literal(write_value)},{len(write_value)}u}},"
            )
        lines.append("};")
        lines.append(
            f"static constexpr TupleBodySpec TUPLE_BODIES{corpus_id}[10] = {{"
        )
        for key, body_value in _TUPLE_BODY_MANIFEST[corpus_id]:
            lines.append(
                f"  {{{_cpp_byte_literal(key)},{len(key)}u,"
                f"{_cpp_byte_literal(body_value)},{len(body_value)}u}},"
            )
        lines.append("};")
    return "\n".join(lines) + "\n"


_CORPUS_CPP = _render_corpus_cpp()

_TU_PREFIX = r'''#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <csignal>
#include <functional>
#include <limits>
#include <memory>
#include <new>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
#include "include/masstree_wrapper.hh"
#include "include/tuple_body.hh"
#include "cc/silo/include/tuple.hh"
#include "cc/silo/include/silo_op_element.hh"

#ifdef NDEBUG
#error "sort SWO oracle requires live assertions"
#endif

#if !defined(__x86_64__) || !defined(AUDIT_ARCH_X86_64)
#error "sort SWO oracle sandbox requires the x86-64 Linux audit ABI"
#endif

static constexpr std::size_t ORACLE_ARENA_SIZE = 4u * 1024u * 1024u;
static unsigned char* oracle_arena_begin = nullptr;
static std::size_t oracle_arena_cursor = 0;
static bool oracle_arena_active = false;

static bool oracle_arena_contains(const void* pointer, std::size_t size,
                                  std::size_t alignment = 1) noexcept {
  if (pointer == nullptr || size == 0 || oracle_arena_begin == nullptr) return false;
  const std::uintptr_t begin = reinterpret_cast<std::uintptr_t>(oracle_arena_begin);
  const std::uintptr_t address = reinterpret_cast<std::uintptr_t>(pointer);
  const std::uintptr_t end = begin + ORACLE_ARENA_SIZE;
  return address >= begin && address < end && size <= end - address
         && alignment != 0 && address % alignment == 0;
}

static void* oracle_arena_allocate(std::size_t size, std::size_t alignment) {
  if (size == 0) size = 1;
  if (alignment < alignof(void*)) alignment = alignof(void*);
  const std::size_t aligned =
      (oracle_arena_cursor + alignment - 1u) & ~(alignment - 1u);
  if (aligned > ORACLE_ARENA_SIZE || size > ORACLE_ARENA_SIZE - aligned) {
    throw std::bad_alloc();
  }
  void* result = oracle_arena_begin + aligned;
  oracle_arena_cursor = aligned + size;
  return result;
}

static void* oracle_fallback_allocate(std::size_t size, std::size_t alignment) {
  if (size == 0) size = 1;
  void* result = nullptr;
  if (alignment <= alignof(std::max_align_t)) {
    result = std::malloc(size);
  } else if (::posix_memalign(&result, alignment, size) != 0) {
    result = nullptr;
  }
  if (result == nullptr) throw std::bad_alloc();
  return result;
}

void* operator new(std::size_t size) {
  return oracle_arena_active
      ? oracle_arena_allocate(size, alignof(std::max_align_t))
      : oracle_fallback_allocate(size, alignof(std::max_align_t));
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void* operator new(std::size_t size, std::align_val_t alignment) {
  const std::size_t value = static_cast<std::size_t>(alignment);
  return oracle_arena_active ? oracle_arena_allocate(size, value)
                             : oracle_fallback_allocate(size, value);
}
void* operator new[](std::size_t size, std::align_val_t alignment) {
  return ::operator new(size, alignment);
}
void* operator new(std::size_t size, const std::nothrow_t&) noexcept {
  try { return ::operator new(size); } catch (...) { return nullptr; }
}
void* operator new[](std::size_t size, const std::nothrow_t&) noexcept {
  try { return ::operator new[](size); } catch (...) { return nullptr; }
}
void* operator new(std::size_t size, std::align_val_t alignment,
                   const std::nothrow_t&) noexcept {
  try { return ::operator new(size, alignment); } catch (...) { return nullptr; }
}
void* operator new[](std::size_t size, std::align_val_t alignment,
                     const std::nothrow_t&) noexcept {
  try { return ::operator new[](size, alignment); } catch (...) { return nullptr; }
}
static void oracle_deallocate(void* pointer) noexcept {
  if (pointer != nullptr && !oracle_arena_contains(pointer, 1)) std::free(pointer);
}
void operator delete(void* pointer) noexcept { oracle_deallocate(pointer); }
void operator delete[](void* pointer) noexcept { oracle_deallocate(pointer); }
void operator delete(void* pointer, std::size_t) noexcept { oracle_deallocate(pointer); }
void operator delete[](void* pointer, std::size_t) noexcept { oracle_deallocate(pointer); }
void operator delete(void* pointer, std::align_val_t) noexcept { oracle_deallocate(pointer); }
void operator delete[](void* pointer, std::align_val_t) noexcept { oracle_deallocate(pointer); }
void operator delete(void* pointer, std::size_t, std::align_val_t) noexcept {
  oracle_deallocate(pointer);
}
void operator delete[](void* pointer, std::size_t, std::align_val_t) noexcept {
  oracle_deallocate(pointer);
}

extern "C" [[noreturn]] void __assert_fail(const char*, const char*, unsigned,
                                            const char*) noexcept {
  ::syscall(SYS_exit_group, 75);
  __builtin_unreachable();
}
''' + _CORPUS_CPP + r'''
static constexpr std::size_t N = 18;
static constexpr std::size_t OBSERVATION_COUNT = 2u * N * N;
static constexpr unsigned EXPECTED_ALLOCATION_CLASS_COUNT = 8;
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

// Known residual, deliberately not claimed closed in this wave: these control
// and relation-provenance cells remain writable outside the corpus arena.
static OracleWriteSet* active_write_set = nullptr;
static std::array<unsigned, N> active_order{};
static std::array<unsigned char, N * N> relation{};
static bool sort_called = false;
static int oracle_test_mode = 0;
static int observation_fd = -1;
static std::size_t observation_count = 0;

static bool emit_bool(bool value) {
  const unsigned char byte = value ? 1u : 0u;
  const ssize_t count = ::write(observation_fd, &byte, 1);
  if (count != 1) std::_Exit(77);
  ++observation_count;
  return value;
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
        relation[lhs * N + rhs] = emit_bool(comparator(lhs_element, rhs_element)) ? 1u : 0u;
      } catch (...) { std::_Exit(72); }
    }
  }
  for (std::size_t flat = N * N; flat-- > 0;) {
    const std::size_t lhs_position = flat / N;
    const std::size_t rhs_position = flat % N;
    try {
      const WriteElement<Tuple>& lhs_element = (*active_write_set)[lhs_position];
      const WriteElement<Tuple>& rhs_element = (*active_write_set)[rhs_position];
      emit_bool(comparator(lhs_element, rhs_element));
    } catch (...) { std::_Exit(72); }
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

struct InventoryCounts {
  unsigned elements = 0;
  unsigned element_keys = 0;
  unsigned element_body_keys = 0;
  unsigned element_body_values = 0;
  unsigned write_values = 0;
  unsigned tuples = 0;
  unsigned tuple_body_keys = 0;
  unsigned tuple_body_values = 0;
};

static bool inventory_range(const void* pointer, std::size_t size,
                            std::size_t alignment, unsigned& count) {
  if (size == 0) return true;
  if (!oracle_arena_contains(pointer, size, alignment)) return false;
  ++count;
  return true;
}

static bool inventory_corpus(OracleWriteSet* write_set, Tuple* aliases,
                             const std::array<Tuple*, 6>& separate,
                             int corpus_id) {
  if (!oracle_arena_contains(write_set, sizeof(*write_set), alignof(OracleWriteSet))
      || write_set->elements.size() != N || write_set->elements.capacity() < N
      || !oracle_arena_contains(write_set->elements.data(),
             write_set->elements.capacity() * sizeof(WriteElement<Tuple>),
             alignof(WriteElement<Tuple>))) return false;
  InventoryCounts counts{};
  for (auto& element : write_set->elements) {
    if (!inventory_range(&element, sizeof(element), alignof(WriteElement<Tuple>),
                         counts.elements)) return false;
    if (!inventory_range(element.key_.data(), element.key_.size(), 1,
                         counts.element_keys)) return false;
    const auto body_key = element.body_.get_key();
    const HeapObject& body_value = element.body_.get_value();
    if (!inventory_range(body_key.data(), body_key.size(), 1,
                         counts.element_body_keys)
        || !inventory_range(body_value.data(), body_value.size(), 64,
                            counts.element_body_values)
        || !inventory_range(element.get_val_ptr(), element.get_val_length(), 1,
                            counts.write_values)) return false;
  }
  std::array<Tuple*, 10> tuples{};
  for (unsigned i = 0; i < 4; ++i) tuples[i] = &aliases[i];
  for (unsigned i = 0; i < 6; ++i) tuples[4 + i] = separate[i];
  for (Tuple* tuple : tuples) {
    const auto body_key = tuple->body_.get_key();
    const HeapObject& body_value = tuple->body_.get_value();
    if (!inventory_range(tuple, sizeof(*tuple), alignof(Tuple), counts.tuples)
        || !inventory_range(body_key.data(), body_key.size(), 1,
                            counts.tuple_body_keys)
        || !inventory_range(body_value.data(), body_value.size(), 64,
                            counts.tuple_body_values)) return false;
  }
  const unsigned expected_keys = corpus_id == 0 ? 14u : 13u;
  const unsigned populated_classes =
      (counts.elements != 0) + (counts.element_keys != 0)
      + (counts.element_body_keys != 0) + (counts.element_body_values != 0)
      + (counts.write_values != 0) + (counts.tuples != 0)
      + (counts.tuple_body_keys != 0) + (counts.tuple_body_values != 0);
  return counts.elements == 18 && counts.element_keys == expected_keys
      && counts.element_body_keys == 18 && counts.element_body_values == 18
      && counts.write_values == 18 && counts.tuples == 10
      && counts.tuple_body_keys == 10 && counts.tuple_body_values == 10
      && populated_classes == EXPECTED_ALLOCATION_CLASS_COUNT;
}

static sock_filter oracle_stmt(unsigned short code, unsigned value) {
  return sock_filter{code, 0, 0, value};
}
static sock_filter oracle_jump(unsigned short code, unsigned value,
                               unsigned char yes, unsigned char no) {
  return sock_filter{code, yes, no, value};
}
static void allow_syscall(std::vector<sock_filter>& filter, unsigned number) {
  filter.push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, number, 0, 1));
  filter.push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_ALLOW));
}

static bool install_oracle_seccomp(int fd, int mode, int pid, int tid) {
  auto* filter = new std::vector<sock_filter>();
  filter->reserve(64);
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, arch)));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K,
      AUDIT_ARCH_X86_64, 1, 0));
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, nr)));
  allow_syscall(*filter, SYS_exit);
  allow_syscall(*filter, SYS_exit_group);

  bool allow_any_write = false;
#ifdef IZANAGI_ORACLE_FAULT_INJECTION
  allow_any_write = mode == 1301;
#endif
  if (allow_any_write) {
    allow_syscall(*filter, SYS_write);
  } else {
    filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, SYS_write, 0, 4));
    filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
        offsetof(struct seccomp_data, args[0])));
    filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K,
        static_cast<unsigned>(fd), 0, 1));
    filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_ALLOW));
    filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS));
    filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
        offsetof(struct seccomp_data, nr)));
  }

  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, SYS_prctl, 0, 6));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, args[0])));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K,
      PR_SET_DUMPABLE, 0, 3));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, args[1])));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, 0, 0, 1));
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_ALLOW));
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, nr)));

  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, SYS_tgkill, 0, 8));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, args[0])));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K,
      static_cast<unsigned>(pid), 0, 5));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, args[1])));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K,
      static_cast<unsigned>(tid), 0, 3));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, args[2])));
  filter->push_back(oracle_jump(BPF_JMP | BPF_JEQ | BPF_K, SIGSTOP, 0, 1));
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_ALLOW));
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS));
  filter->push_back(oracle_stmt(BPF_LD | BPF_W | BPF_ABS,
      offsetof(struct seccomp_data, nr)));

#ifdef IZANAGI_ORACLE_FAULT_INJECTION
  if (mode == 1300) {
    allow_syscall(*filter, SYS_openat);
    allow_syscall(*filter, SYS_getdents64);
    allow_syscall(*filter, SYS_close);
  } else if (mode == 1302) {
    allow_syscall(*filter, SYS_mprotect);
  } else if (mode == 1303) {
    allow_syscall(*filter, SYS_mmap);
    allow_syscall(*filter, SYS_munmap);
  } else if (mode == 1304) {
    allow_syscall(*filter, SYS_rt_sigaction);
  }
#endif
  filter->push_back(oracle_stmt(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS));
  sock_fprog program{static_cast<unsigned short>(filter->size()), filter->data()};
  return ::prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program) == 0;
}

static void close_worker_fds_except(int keep) {
  rlimit limit{};
  unsigned long maximum = 65536;
  if (::getrlimit(RLIMIT_NOFILE, &limit) == 0 && limit.rlim_cur < maximum) {
    maximum = limit.rlim_cur;
  }
  for (unsigned long candidate = 0; candidate < maximum; ++candidate) {
    if (static_cast<int>(candidate) != keep) ::close(static_cast<int>(candidate));
  }
}

int main(int argc, char** argv) {
  if (argc != 7 && argc != 8) return 64;
  const int corpus_id = std::atoi(argv[1]);
  const int order_id = std::atoi(argv[2]);
  observation_fd = std::atoi(argv[3]);
  const unsigned long long expected_observation_dev = std::strtoull(argv[4], nullptr, 10);
  const unsigned long long expected_observation_ino = std::strtoull(argv[5], nullptr, 10);
  const unsigned long long expected_observation_type = std::strtoull(argv[6], nullptr, 10);
  if (corpus_id < 0 || corpus_id > 1 || order_id < 0 || order_id > 2
      || observation_fd < 0) return 65;
  struct stat observation_stat{};
  if (::fstat(observation_fd, &observation_stat) != 0
      || static_cast<unsigned long long>(observation_stat.st_dev)
             != expected_observation_dev
      || static_cast<unsigned long long>(observation_stat.st_ino)
             != expected_observation_ino
      || static_cast<unsigned long long>(observation_stat.st_mode & S_IFMT)
             != expected_observation_type) {
    std::_Exit(76);
  }
  if (argc == 8) oracle_test_mode = std::atoi(argv[7]);
  oracle_arena_begin = static_cast<unsigned char*>(::mmap(
      nullptr, ORACLE_ARENA_SIZE, PROT_READ | PROT_WRITE,
      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
  if (oracle_arena_begin == MAP_FAILED) std::_Exit(76);
  const ElementSpec* specs = corpus_id == 0 ? CORPUS0 : CORPUS1;
  const TupleBodySpec* tuple_specs =
      corpus_id == 0 ? TUPLE_BODIES0 : TUPLE_BODIES1;
  Tuple* aliases = nullptr;
  std::array<Tuple*, 6> separate{};
  OracleWriteSet* write_set_storage = nullptr;
  try {
    oracle_arena_active = true;
    aliases = new Tuple[4];
    for (auto& item : separate) item = new Tuple();
    for (unsigned slot = 0; slot < 10; ++slot) {
      Tuple* tuple = slot < 4 ? &aliases[slot] : separate[slot - 4];
      const TupleBodySpec& spec = tuple_specs[slot];
      tuple->body_ = TupleBody(
          std::string_view(spec.key, spec.key_size),
          std::string_view(spec.value, spec.value_size), std::align_val_t(64));
    }
    active_order = order_for(order_id);
    write_set_storage = new OracleWriteSet();
    write_set_storage->reserve(N);
    for (unsigned position = 0; position < N; ++position) {
      const ElementSpec& spec = specs[active_order[position]];
      Tuple* pointer = nullptr;
      if (spec.pointer_kind == 1) pointer = &aliases[spec.pointer_slot];
      if (spec.pointer_kind == 2) pointer = separate[spec.pointer_slot];
      write_set_storage->emplace_back(
          static_cast<Storage>(spec.storage),
          std::string_view(spec.key, spec.key_size), pointer,
          std::string_view(spec.write_value, spec.write_value_size), OpType::UPDATE);
      write_set_storage->elements.back().body_ = TupleBody(
          std::string_view(spec.body_key, spec.body_key_size),
          std::string_view(spec.body_value, spec.body_value_size),
          std::align_val_t(64));
    }
    active_write_set = write_set_storage;
    oracle_arena_active = false;
  } catch (...) {
    oracle_arena_active = false;
    std::_Exit(76);
  }
  OracleWriteSet& write_set_ = *write_set_storage;
  if (!inventory_corpus(&write_set_, aliases, separate, corpus_id)) std::_Exit(76);
  bool skip_read_only = false;
#ifdef IZANAGI_ORACLE_FAULT_INJECTION
  skip_read_only = oracle_test_mode >= 1000 && oracle_test_mode < 1100;
#endif
  if (!skip_read_only
      && ::mprotect(oracle_arena_begin, ORACLE_ARENA_SIZE, PROT_READ) != 0) {
    std::_Exit(76);
  }
  const int worker_pid = static_cast<int>(::getpid());
  const int worker_tid = static_cast<int>(::syscall(SYS_gettid));
  close_worker_fds_except(observation_fd);
  if (::prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0
      || !install_oracle_seccomp(
          observation_fd, oracle_test_mode, worker_pid, worker_tid)) {
    std::_Exit(76);
  }
  if (::syscall(SYS_tgkill, worker_pid, worker_tid, SIGSTOP) != 0) std::_Exit(76);
  if (::prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0) std::_Exit(76);
  if (::syscall(SYS_tgkill, worker_pid, worker_tid, SIGSTOP) != 0) std::_Exit(76);
'''

_TU_SUFFIX = r'''
  if (!sort_called || observation_count != OBSERVATION_COUNT) std::_Exit(73);
  std::_Exit(0);
}
'''

_STATEMENT_PLACEHOLDER = "/*__IZANAGI_SORT_STATEMENT__*/"


def _translation_unit(statement: str) -> str:
    return _TU_PREFIX + statement + _TU_SUFFIX


_BROKER_OUTCOME_OK = 0
_BROKER_OUTCOME_REJECT = 1
_BROKER_OUTCOME_INFRASTRUCTURE = 2
_BROKER_DETAIL_OK = 0
_BROKER_DETAIL_SORT_CONTRACT = 1
_BROKER_DETAIL_COMPARATOR_THREW = 2
_BROKER_DETAIL_CALL_COUNT = 3
_BROKER_DETAIL_ABORTED = 4
_BROKER_DETAIL_SANDBOX = 5
_BROKER_DETAIL_EXECUTION_FAULT = 6
_BROKER_DETAIL_SIGNAL = 7
_BROKER_DETAIL_OBSERVATION_SIZE = 8
_BROKER_DETAIL_OBSERVATION_VALUE = 9
_BROKER_DETAIL_OBSERVATION_WRITE = 10
_BROKER_DETAIL_FD_BOUNDARY = 11
_BROKER_DETAIL_REPEAT = 12
_BROKER_DETAIL_CPU = 13


def _broker_fd_identity(fd: int) -> tuple[int, int, int]:
    metadata = os.fstat(fd)
    return (metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode))


def _broker_worker_fd_numbers(directory_fd: int) -> tuple[int, ...]:
    os.lseek(directory_fd, 0, os.SEEK_SET)
    return tuple(sorted(
        int(entry.name) for entry in os.scandir(directory_fd)
        if entry.name.isdecimal()
    ))


def _broker_worker_fd_identities_from_snapshot(
    observed_numbers: Sequence[int], expected_numbers: Sequence[int],
    expected_identities: Sequence[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], ...]:
    # Default-deny seccomp permits no close/dup/fcntl/open operation between
    # snapshots, and the worker is stopped throughout authority receipt.  An
    # exact independent fd-number re-observation therefore preserves the
    # anchored object identities; any number change fails closed.
    if (
        tuple(observed_numbers) != tuple(expected_numbers)
        or len(expected_identities) != len(expected_numbers)
    ):
        return ()
    return tuple(expected_identities)


def _worker_fd_boundary_is_safe(
    before: Sequence[tuple[int, int, int]],
    after: Sequence[tuple[int, int, int]],
    final_identity: tuple[int, int, int],
    *,
    final_created_after_stop: bool,
) -> bool:
    return (
        final_created_after_stop
        and len(before) == 1
        and tuple(before) == tuple(after)
        and final_identity not in before
        and final_identity not in after
    )


def _broker_send_control(authority: socket.socket, payload: bytes) -> None:
    authority.sendmsg(
        [payload],
        [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
          array("i", [authority.fileno()]))],
    )


def _broker_receive_control(authority: socket.socket) -> bytes:
    item_size = array("i").itemsize
    payload, ancillary, flags, _address = authority.recvmsg(
        4096, socket.CMSG_SPACE(item_size),
    )
    received = []
    for level, kind, data in ancillary:
        if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
            values = array("i")
            values.frombytes(data[:len(data) - len(data) % item_size])
            received.extend(values)
    expected_count = 1
    if (
        flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC)
        or len(received) != expected_count
    ):
        for fd in received:
            os.close(fd)
        raise RuntimeError("broker control marker fd mismatch")
    if received:
        os.close(received[0])
    return payload


def _broker_receive_fd(authority: socket.socket) -> int:
    item_size = array("i").itemsize
    payload, ancillary, flags, _address = authority.recvmsg(
        1, socket.CMSG_SPACE(item_size)
    )
    if payload != b"F" or flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC):
        raise RuntimeError("invalid protocol authority transfer")
    received = []
    for level, kind, data in ancillary:
        if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
            values = array("i")
            values.frombytes(data[:len(data) - len(data) % item_size])
            received.extend(values)
    if len(received) != 1:
        for fd in received:
            os.close(fd)
        raise RuntimeError("protocol authority fd count mismatch")
    return received[0]


def _broker_write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            raise OSError("broker protocol write failed")
        view = view[count:]


def _broker_order(order_id: int) -> tuple[int, ...]:
    order = list(range(_N))
    if order_id == 1:
        order.reverse()
    elif order_id == 2:
        state = 0x3165A17
        for index in range(_N - 1, 0, -1):
            state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
            target = state % (index + 1)
            order[index], order[target] = order[target], order[index]
    return tuple(order)


def _broker_frame(
    wait_result: os.waitid_result,
    observations: bytes,
    corpus: int,
    order_id: int,
    *,
    fd_boundary_safe: bool,
) -> bytes:
    outcome = _BROKER_OUTCOME_REJECT
    detail = _BROKER_DETAIL_SIGNAL
    witness_lhs = _WITNESS_NONE
    witness_rhs = _WITNESS_NONE
    detail_value = 0
    matrix = bytes(_N * _N)
    if not fd_boundary_safe:
        outcome = _BROKER_OUTCOME_INFRASTRUCTURE
        detail = _BROKER_DETAIL_FD_BOUNDARY
    elif wait_result.si_code == os.CLD_EXITED:
        exit_code = wait_result.si_status
        exit_details = {
            71: _BROKER_DETAIL_SORT_CONTRACT,
            72: _BROKER_DETAIL_COMPARATOR_THREW,
            73: _BROKER_DETAIL_CALL_COUNT,
            75: _BROKER_DETAIL_ABORTED,
            77: _BROKER_DETAIL_OBSERVATION_WRITE,
        }
        if exit_code != 0:
            detail = exit_details.get(exit_code, _BROKER_DETAIL_SIGNAL)
            detail_value = exit_code
        elif len(observations) != 2 * _N * _N:
            detail = _BROKER_DETAIL_OBSERVATION_SIZE
            detail_value = len(observations)
        elif any(value not in (0, 1) for value in observations):
            detail = _BROKER_DETAIL_OBSERVATION_VALUE
        else:
            first = observations[:_N * _N]
            second = observations[_N * _N:]
            active_order = _broker_order(order_id)
            canonical = bytearray(_N * _N)
            for lhs_position in range(_N):
                for rhs_position in range(_N):
                    flat = lhs_position * _N + rhs_position
                    lhs = active_order[lhs_position]
                    rhs = active_order[rhs_position]
                    canonical[lhs * _N + rhs] = first[flat]
            for second_index, value in enumerate(second):
                flat = _N * _N - 1 - second_index
                if value != first[flat]:
                    lhs_position, rhs_position = divmod(flat, _N)
                    witness_lhs = active_order[lhs_position]
                    witness_rhs = active_order[rhs_position]
                    detail_value = first[flat] | (value << 1)
                    detail = _BROKER_DETAIL_REPEAT
                    break
            else:
                outcome = _BROKER_OUTCOME_OK
                detail = _BROKER_DETAIL_OK
            matrix = bytes(canonical)
    elif wait_result.si_status == signal.SIGSYS:
        detail = _BROKER_DETAIL_SANDBOX
    elif wait_result.si_status in {signal.SIGSEGV, signal.SIGBUS}:
        # waitid identifies only the terminating signal.  It supplies neither
        # the fault address nor the access type, so this cannot be attributed
        # specifically to an attempted corpus write.
        detail = _BROKER_DETAIL_EXECUTION_FAULT
        detail_value = wait_result.si_status
    elif wait_result.si_status == signal.SIGABRT:
        detail = _BROKER_DETAIL_ABORTED
    elif wait_result.si_status == signal.SIGXCPU:
        detail = _BROKER_DETAIL_CPU
    else:
        detail_value = wait_result.si_status
    header = _HEADER.pack(
        _MAGIC, PROTOCOL_VERSION, corpus, order_id, _N, outcome, detail,
        witness_lhs, witness_rhs, detail_value,
    )
    return header + matrix


def _broker_main(arguments: Sequence[str]) -> int:
    if len(arguments) not in {4, 5, 6}:
        return 64
    worker_path, corpus_text, order_text, authority_text = arguments[:4]
    test_mode = None if len(arguments) == 4 else arguments[4]
    injected_final_fd = None if len(arguments) < 6 else int(arguments[5])
    if injected_final_fd is not None and test_mode not in {"1404", "1405"}:
        return 64
    corpus = int(corpus_text)
    order_id = int(order_text)
    authority = socket.socket(
        socket.AF_UNIX, socket.SOCK_SEQPACKET, 0,
        fileno=int(authority_text),
    )
    observation_read, observation_write = os.pipe()
    worker_observation_fd = observation_write
    worker_observation_identity = _broker_fd_identity(observation_write)
    worker_pid = os.fork()
    if worker_pid == 0:
        try:
            authority.close()
            os.close(observation_read)
            if injected_final_fd is not None:
                if test_mode == "1405":
                    if injected_final_fd != observation_write:
                        os.dup2(injected_final_fd, observation_write)
                        os.close(injected_final_fd)
                else:
                    # MUT-4: final authority was inherited at fork, then
                    # closed before the first worker stop.
                    os.close(injected_final_fd)
            os.set_inheritable(observation_write, True)
            worker_arguments = [
                worker_path, corpus_text, order_text, str(observation_write),
                *(str(field) for field in worker_observation_identity),
            ]
            if test_mode is not None:
                worker_arguments.append(test_mode)
            os.execv(worker_path, worker_arguments)
        finally:
            os._exit(76)
    os.close(observation_write)
    if injected_final_fd is not None:
        os.close(injected_final_fd)
    final_fd = None
    worker_fd_directory = None
    try:
        inspection_stop = os.waitid(
            os.P_PID, worker_pid, os.WSTOPPED | os.WEXITED
        )
        if (
            inspection_stop.si_pid != worker_pid
            or inspection_stop.si_code != os.CLD_STOPPED
            or inspection_stop.si_status != signal.SIGSTOP
        ):
            _broker_send_control(authority, b"F:worker-hardening-preflight-failed")
            return 76
        before_numbers = (worker_observation_fd,)
        before = (worker_observation_identity,)
        worker_fd_directory = os.open(
            f"/proc/{worker_pid}/fd",
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0),
        )
        os.kill(worker_pid, signal.SIGCONT)
        hardened_stop = os.waitid(
            os.P_PID, worker_pid, os.WSTOPPED | os.WEXITED
        )
        if (
            hardened_stop.si_pid != worker_pid
            or hardened_stop.si_code != os.CLD_STOPPED
            or hardened_stop.si_status != signal.SIGSTOP
        ):
            _broker_send_control(authority, b"F:worker-hardening-preflight-failed")
            return 76
        ready_payload = json.dumps(
            {"fd_identities": before, "pid": worker_pid},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        _broker_send_control(authority, b"R:" + ready_payload)
        final_fd = _broker_receive_fd(authority)
        final_identity = _broker_fd_identity(final_fd)
        acknowledged = _broker_receive_control(authority) == b"A"
        # The authority handshake is now complete, but the worker is still
        # stopped.  Re-enumerate only now; no authority write follows this
        # observation, which also works under the /proc information-flow guard.
        observed_numbers = _broker_worker_fd_numbers(worker_fd_directory)
        after = _broker_worker_fd_identities_from_snapshot(
            observed_numbers, before_numbers, before,
        )
        boundary_safe = _worker_fd_boundary_is_safe(
            before, after, final_identity,
            final_created_after_stop=injected_final_fd is None,
        )
        if boundary_safe and acknowledged:
            os.kill(worker_pid, signal.SIGCONT)
        else:
            boundary_safe = False
            os.kill(worker_pid, signal.SIGKILL)
        reaped = os.waitid(os.P_PID, worker_pid, os.WEXITED)
        observations = bytearray()
        while len(observations) <= 2 * _N * _N:
            chunk = os.read(
                observation_read, 2 * _N * _N + 1 - len(observations)
            )
            if not chunk:
                break
            observations.extend(chunk)
        frame = _broker_frame(
            reaped, bytes(observations), corpus, order_id,
            fd_boundary_safe=boundary_safe,
        )
        _broker_write_all(final_fd, frame)
        return 0
    except Exception as exc:
        try:
            _broker_send_control(
                authority,
                b"E:broker-" + type(exc).__name__.encode("ascii", errors="replace")
            )
        except OSError:
            pass
        try:
            os.kill(worker_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitid(os.P_PID, worker_pid, os.WEXITED)
        except ChildProcessError:
            pass
        return 76
    finally:
        os.close(observation_read)
        if final_fd is not None:
            os.close(final_fd)
        if worker_fd_directory is not None:
            os.close(worker_fd_directory)
        authority.close()


_BROKER_SOURCE_FUNCTIONS = (
    _broker_fd_identity,
    _broker_worker_fd_numbers,
    _broker_worker_fd_identities_from_snapshot,
    _worker_fd_boundary_is_safe,
    _broker_send_control,
    _broker_receive_control,
    _broker_receive_fd,
    _broker_write_all,
    _broker_order,
    _broker_frame,
    _broker_main,
)


def _translation_unit_bundle_sha256(worker_source: str) -> str:
    digest = hashlib.sha256()
    members = [("worker", worker_source)] + [
        (
            f"broker:{function.__module__}.{function.__qualname__}",
            inspect.getsource(function),
        )
        for function in _BROKER_SOURCE_FUNCTIONS
    ]
    semantics = json.dumps(
        {
            "broker_details": {
                "aborted": _BROKER_DETAIL_ABORTED,
                "call_count": _BROKER_DETAIL_CALL_COUNT,
                "comparator_threw": _BROKER_DETAIL_COMPARATOR_THREW,
                "cpu": _BROKER_DETAIL_CPU,
                "execution_fault": _BROKER_DETAIL_EXECUTION_FAULT,
                "fd_boundary": _BROKER_DETAIL_FD_BOUNDARY,
                "observation_size": _BROKER_DETAIL_OBSERVATION_SIZE,
                "observation_value": _BROKER_DETAIL_OBSERVATION_VALUE,
                "observation_write": _BROKER_DETAIL_OBSERVATION_WRITE,
                "ok": _BROKER_DETAIL_OK,
                "repeat": _BROKER_DETAIL_REPEAT,
                "sandbox": _BROKER_DETAIL_SANDBOX,
                "signal": _BROKER_DETAIL_SIGNAL,
                "sort_contract": _BROKER_DETAIL_SORT_CONTRACT,
            },
            "broker_outcomes": {
                "infrastructure": _BROKER_OUTCOME_INFRASTRUCTURE,
                "ok": _BROKER_OUTCOME_OK,
                "reject": _BROKER_OUTCOME_REJECT,
            },
            "header": _HEADER.format,
            "magic_hex": _MAGIC.hex(),
            "n": _N,
            "protocol_version": PROTOCOL_VERSION,
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    members.append(("broker-semantics", semantics))
    for label, source in members:
        for value in (label.encode("utf-8"), source.encode("utf-8")):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return digest.hexdigest()


TU_TEMPLATE_SHA256 = _translation_unit_bundle_sha256(
    _translation_unit(_STATEMENT_PLACEHOLDER)
)


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


def _parse_dependency_manifest(
    raw: bytes,
) -> tuple[tuple[str, str], ...]:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise _DependencyVerificationError(
            "dependency-manifest-invalid",
        ) from exc
    if not text.endswith("\n"):
        raise _DependencyVerificationError("dependency-manifest-invalid")
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _DEPENDENCY_MANIFEST_LINE.fullmatch(line)
        if match is None:
            raise _DependencyVerificationError("dependency-manifest-invalid")
        digest, relative = match.groups()
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or relative == _DEPENDENCY_MANIFEST_NAME
            or str(path) != relative
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise _DependencyVerificationError("dependency-manifest-invalid")
        entries.append((relative, digest))
    paths = [relative for relative, _digest in entries]
    if not entries or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise _DependencyVerificationError("dependency-manifest-invalid")
    return tuple(entries)


def _dependency_file_inventory(root: Path) -> tuple[set[str], set[str]]:
    regular_files: set[str] = set()
    forbidden_entries: set[str] = set()
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in (*directory_names, *file_names):
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise _DependencyVerificationError(
                    "dependency-filesystem-error",
                ) from exc
            if stat.S_ISLNK(metadata.st_mode):
                forbidden_entries.add(relative)
            elif stat.S_ISREG(metadata.st_mode):
                regular_files.add(relative)
            elif not stat.S_ISDIR(metadata.st_mode):
                forbidden_entries.add(relative)
    return regular_files, forbidden_entries


def _verify_dependency_root(root: Path) -> _VerifiedDependencyRoot:
    fixture_root = Path(root)
    try:
        root_metadata = fixture_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode):
            raise _DependencyVerificationError("dependency-root-symlink")
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise _DependencyVerificationError("dependency-root-not-directory")
        root_realpath = fixture_root.resolve(strict=True)
        regular_files, forbidden_entries = _dependency_file_inventory(
            fixture_root,
        )
    except _DependencyVerificationError:
        raise
    except OSError as exc:
        raise _DependencyVerificationError(
            "dependency-filesystem-error",
        ) from exc
    if forbidden_entries:
        raise _DependencyVerificationError("dependency-forbidden-entry")
    if _DEPENDENCY_MANIFEST_NAME not in regular_files:
        raise _DependencyVerificationError(
            "dependency-manifest-not-regular-file",
        )
    manifest_path = fixture_root / _DEPENDENCY_MANIFEST_NAME
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise _DependencyVerificationError(
            "dependency-filesystem-error",
        ) from exc
    entries = _parse_dependency_manifest(manifest_bytes)
    declared = {relative for relative, _digest in entries}
    actual = regular_files - {_DEPENDENCY_MANIFEST_NAME}
    if declared != actual:
        raise _DependencyVerificationError("dependency-file-set-mismatch")
    for relative, expected_sha256 in entries:
        path = fixture_root.joinpath(*PurePosixPath(relative).parts)
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root_realpath):
                raise _DependencyVerificationError(
                    "dependency-path-escapes-root",
                )
            actual_sha256 = _file_sha256(path)
        except _DependencyVerificationError:
            raise
        except OSError as exc:
            raise _DependencyVerificationError(
                "dependency-filesystem-error",
            ) from exc
        if actual_sha256 != expected_sha256:
            raise _DependencyVerificationError("dependency-sha256-mismatch")
    files = tuple(entries)
    hashes = dict(files)
    if "config.h" not in hashes:
        raise _DependencyVerificationError("dependency-config-not-declared")
    return _VerifiedDependencyRoot(
        root=root_realpath,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        manifest_bytes=manifest_bytes,
        files=files,
        config_sha256=hashes["config.h"],
    )


def _read_verified_dependency_file(
    root: Path, relative: str, expected_sha256: str,
) -> bytes:
    path = root.joinpath(*PurePosixPath(relative).parts)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise _DependencyVerificationError(
                    "dependency-copy-source-not-regular-file",
                )
            chunks = []
            while True:
                chunk = os.read(fd, 64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(fd)
    except _DependencyVerificationError:
        raise
    except OSError as exc:
        raise _DependencyVerificationError(
            "dependency-copy-source-unavailable",
        ) from exc
    raw = b"".join(chunks)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise _DependencyVerificationError("dependency-copy-source-changed")
    return raw


def _prepare_verified_dependency(
    source_root: Path, private_root: Path,
) -> _VerifiedDependencyRoot:
    source = _verify_dependency_root(source_root)
    if source.manifest_sha256 != DEPENDENCY_MANIFEST_SHA256:
        raise _DependencyVerificationError("dependency-manifest-not-canonical")
    try:
        private_root.mkdir(mode=0o700)
        manifest_path = private_root / _DEPENDENCY_MANIFEST_NAME
        manifest_path.write_bytes(source.manifest_bytes)
        for relative, expected_sha256 in source.files:
            raw = _read_verified_dependency_file(
                source.root, relative, expected_sha256,
            )
            destination = private_root.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination.write_bytes(raw)
    except _DependencyVerificationError:
        raise
    except OSError as exc:
        raise _DependencyVerificationError(
            "dependency-private-copy-failed",
        ) from exc
    copied = _verify_dependency_root(private_root)
    source_after = _verify_dependency_root(source.root)
    if (
        copied.manifest_sha256 != DEPENDENCY_MANIFEST_SHA256
        or copied.files != source.files
        or source_after.manifest_sha256 != source.manifest_sha256
        or source_after.files != source.files
    ):
        raise _DependencyVerificationError("dependency-private-copy-mismatch")
    return copied


def _assert_verified_dependency_unchanged(
    expected: _VerifiedDependencyRoot,
) -> None:
    actual = _verify_dependency_root(expected.root)
    if (
        actual.manifest_sha256 != expected.manifest_sha256
        or actual.manifest_bytes != expected.manifest_bytes
        or actual.files != expected.files
        or actual.config_sha256 != expected.config_sha256
    ):
        raise _DependencyVerificationError("dependency-private-copy-changed")


def _compile_command(
    source_path: Path, executable: Path, *, compiler: str,
    ccbench_dir: Path, masstree_dir: Path, fault_injection: bool = False,
) -> list[str]:
    flags = list(_COMPILE_FLAGS)
    if fault_injection:
        flags.insert(-1, "-DIZANAGI_ORACLE_FAULT_INJECTION=1")
    return [
        compiler, *flags[:2], "-o", str(executable), str(source_path),
        "-I", str(ccbench_dir), "-I", str(ccbench_dir / "include"),
        "-I", str(masstree_dir), *flags[2:],
    ]


def _dependency_command(
    source_path: Path, *, compiler: str, ccbench_dir: Path,
    dependency_root: Path, fault_injection: bool,
) -> list[str]:
    flags = list(_COMPILE_FLAGS)
    if fault_injection:
        flags.insert(-1, "-DIZANAGI_ORACLE_FAULT_INJECTION=1")
    return [
        compiler, *flags[:2], "-M", "-MT", "oracle-dependency-closure",
        str(source_path), "-I", str(ccbench_dir),
        "-I", str(ccbench_dir / "include"), "-I", str(dependency_root),
        *flags[2:],
    ]


def _dependency_manifest_closure(
    source_path: Path, *, compiler: str, ccbench_dir: Path,
    dependency: _VerifiedDependencyRoot, fault_injection: bool,
) -> tuple[str, ...]:
    command = _dependency_command(
        source_path, compiler=compiler, ccbench_dir=ccbench_dir,
        dependency_root=dependency.root, fault_injection=fault_injection,
    )
    try:
        completed = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=_COMPILE_TIMEOUT_S, check=False,
            start_new_session=True, preexec_fn=_limit_compile,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _DependencyVerificationError(
            "dependency-closure-scan-unavailable",
        ) from exc
    if completed.returncode != 0:
        raise _DependencyVerificationError("dependency-closure-scan-failed")
    try:
        text = completed.stdout.decode("utf-8", "strict").replace("\\\n", " ")
        target, separator, body = text.partition(":")
        if separator != ":" or target.strip() != "oracle-dependency-closure":
            raise ValueError("unexpected dependency target")
        tokens = shlex.split(body, comments=False, posix=True)
    except (UnicodeDecodeError, ValueError) as exc:
        raise _DependencyVerificationError(
            "dependency-closure-output-invalid",
        ) from exc
    declared = {relative for relative, _digest in dependency.files}
    used: set[str] = set()
    for token in tokens:
        candidate = Path(token)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise _DependencyVerificationError(
                "dependency-closure-path-unavailable",
            ) from exc
        if not resolved.is_relative_to(dependency.root):
            continue
        relative = resolved.relative_to(dependency.root).as_posix()
        if relative not in declared:
            raise _DependencyVerificationError(
                "dependency-closure-outside-manifest",
            )
        used.add(relative)
    if "config.h" not in used or len(used) < _MIN_DEPENDENCY_MANIFEST_CLOSURE:
        raise _DependencyVerificationError("dependency-closure-too-small")
    return tuple(sorted(used))


def _compile(
    source: str, source_path: Path, executable: Path, *, compiler: str,
    ccbench_dir: Path, masstree_dir: Path, fault_injection: bool = False,
) -> tuple[Optional[SortSwoFinding], bool]:
    source_path.write_text(source, encoding="utf-8")
    command = _compile_command(
        source_path, executable, compiler=compiler,
        ccbench_dir=ccbench_dir, masstree_dir=masstree_dir,
        fault_injection=fault_injection,
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


def _compile_verified(
    source: str, source_path: Path, executable: Path, *, compiler: str,
    ccbench_dir: Path, dependency: _VerifiedDependencyRoot,
    fault_injection: bool = False,
) -> tuple[Optional[SortSwoFinding], bool]:
    try:
        _assert_verified_dependency_unchanged(dependency)
        source_path.write_text(source, encoding="utf-8")
        _dependency_manifest_closure(
            source_path, compiler=compiler, ccbench_dir=ccbench_dir,
            dependency=dependency, fault_injection=fault_injection,
        )
        _assert_verified_dependency_unchanged(dependency)
    except _DependencyVerificationError as exc:
        return SortSwoFinding(
            OracleRejectKind.COMPILE, exc.detail_code,
        ), True
    finding, unavailable = _compile(
        source, source_path, executable, compiler=compiler,
        ccbench_dir=ccbench_dir, masstree_dir=dependency.root,
        fault_injection=fault_injection,
    )
    try:
        _assert_verified_dependency_unchanged(dependency)
    except _DependencyVerificationError as exc:
        return SortSwoFinding(
            OracleRejectKind.COMPILE, exc.detail_code,
        ), True
    return finding, unavailable


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
    fd_observer: Optional[
        Callable[
            [str, int, tuple[tuple[int, int, int], ...],
             Optional[tuple[int, int, int]]], None
        ]
    ] = None,
) -> tuple[Optional[bytes], Optional[SortSwoFinding]]:
    authority, broker_authority = socket.socketpair(
        socket.AF_UNIX, socket.SOCK_SEQPACKET
    )
    command = [
        sys.executable, os.fspath(Path(__file__).resolve()),
        "--sort-swo-broker", str(executable), str(corpus), str(order),
        str(broker_authority.fileno()),
    ]
    if test_mode is not None:
        command.append(str(test_mode))
    read_fd = None
    write_fd = None
    final_created_after_stop = test_mode not in {1404, 1405}
    if not final_created_after_stop:
        # MUT-4/MUT-5 deliberately create the final object before the broker
        # forks its worker.  Normal production never enters these test modes.
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        command.append(str(write_fd))
    inherited_fds = [broker_authority.fileno()]
    if write_fd is not None:
        inherited_fds.append(write_fd)
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, pass_fds=tuple(inherited_fds),
            start_new_session=True, preexec_fn=_limit_run,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        authority.close()
        broker_authority.close()
        if read_fd is not None:
            os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        raise _EvaluationUnavailable("run-launch", "loader-or-launch-failed") from exc
    broker_authority.close()
    authority.settimeout(_RUN_TIMEOUT_S)
    acknowledged = False
    try:
        ready = _broker_receive_control(authority)
        if ready.startswith(b"F:"):
            process.communicate(timeout=_RUN_TIMEOUT_S)
            raise _EvaluationUnavailable(
                "worker-hardening", ready[2:].decode("ascii", errors="replace")
            )
        if not ready.startswith(b"R:"):
            raise _EvaluationUnavailable("broker-handshake", "worker-stop-not-confirmed")
        ready_payload = json.loads(ready[2:].decode("ascii"))
        if set(ready_payload) != {"fd_identities", "pid"}:
            raise ValueError("broker ready payload shape mismatch")
        worker_pid = int(ready_payload["pid"])
        before = tuple(
            tuple(int(field) for field in identity)
            for identity in ready_payload["fd_identities"]
        )
        if fd_observer is not None:
            fd_observer("stopped", worker_pid, before, None)
        # Except in explicit MUT-4/MUT-5 fault injection, the final pipe is born
        # only after the exact hardened worker pid has been observed stopped.
        if final_created_after_stop:
            read_fd, write_fd = os.pipe()
            os.set_blocking(read_fd, False)
        assert write_fd is not None
        final_identity = _broker_fd_identity(write_fd)
        authority.sendmsg(
            [b"F"],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array("i", [write_fd]))],
        )
        os.close(write_fd)
        write_fd = None
        if fd_observer is not None:
            fd_observer("authority-sent", worker_pid, before, final_identity)
        # ACK completes the authority channel, but does not authorize worker
        # resume.  The broker independently observes the stopped worker after
        # this ACK and encodes failure only in the final protocol frame.
        _broker_send_control(authority, b"A")
        acknowledged = True
    except Exception as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        if read_fd is not None:
            os.close(read_fd)
            read_fd = None
        if isinstance(exc, _EvaluationUnavailable):
            raise
        if isinstance(exc, (OSError, ValueError, socket.timeout)):
            raise _EvaluationUnavailable(
                "broker-handshake", "protocol-authority-handshake-failed"
            ) from exc
        raise
    finally:
        authority.close()
        if write_fd is not None:
            os.close(write_fd)
    timed_out, returncode = _communicate_hard_timeout(process, _RUN_TIMEOUT_S)
    assert acknowledged
    record = b"" if read_fd is None else _read_all(read_fd, _RECORD_SIZE)
    if read_fd is not None:
        os.close(read_fd)
    if timed_out:
        return None, SortSwoFinding(
            OracleRejectKind.TIMEOUT, "candidate-run-wall-timeout",
            corpus_id=f"{CORPUS_ID}/corpus-{corpus}", order_id=order,
        )
    if returncode == -signal.SIGXCPU:
        return None, SortSwoFinding(
            OracleRejectKind.TIMEOUT, "candidate-run-cpu-limit-exceeded",
            corpus_id=f"{CORPUS_ID}/corpus-{corpus}", order_id=order,
        )
    if returncode < 0:
        raise _EvaluationUnavailable("broker-signal", f"broker-run-signal-{abs(returncode)}")
    if returncode != 0:
        raise _EvaluationUnavailable("broker-exit", f"broker-run-exit-{returncode}")
    if len(record) != _RECORD_SIZE:
        raise _EvaluationUnavailable("protocol", "record-size-mismatch")
    (magic, version, got_corpus, got_order, n, outcome, detail,
     witness_lhs, witness_rhs, detail_value) = _HEADER.unpack(
         record[:_HEADER.size]
     )
    if (magic != _MAGIC or version != PROTOCOL_VERSION or got_corpus != corpus
            or got_order != order or n != _N):
        raise _EvaluationUnavailable("protocol", "record-header-mismatch")
    matrix = record[_HEADER.size:]
    if any(value not in (0, 1) for value in matrix):
        raise _EvaluationUnavailable("protocol", "record-value-out-of-range")
    execution_corpus_id = f"{CORPUS_ID}/corpus-{corpus}"
    if outcome == _BROKER_OUTCOME_OK:
        if detail != _BROKER_DETAIL_OK:
            raise _EvaluationUnavailable("protocol", "success-detail-mismatch")
        return matrix, None
    if outcome == _BROKER_OUTCOME_INFRASTRUCTURE:
        if detail != _BROKER_DETAIL_FD_BOUNDARY:
            raise _EvaluationUnavailable("protocol", "infrastructure-detail-invalid")
        raise _EvaluationUnavailable(
            "protocol-authority", "worker-fd-boundary-verification-failed"
        )
    if outcome != _BROKER_OUTCOME_REJECT:
        raise _EvaluationUnavailable("protocol", "record-outcome-invalid")
    if detail == _BROKER_DETAIL_REPEAT:
        if (witness_lhs >= _N or witness_rhs >= _N
                or detail_value not in {1, 2}):
            raise _EvaluationUnavailable("protocol", "repeat-witness-invalid")
        pair = (witness_lhs, witness_rhs)
        return None, SortSwoFinding(
            OracleRejectKind.NONDETERMINISTIC,
            "relation-varies-within-process",
            input_pairs=(pair,), corpus_id=execution_corpus_id, order_id=order,
            observations=(
                {"point": "first-pass", "lhs_index": witness_lhs,
                 "rhs_index": witness_rhs, "value": bool(detail_value & 1)},
                {"point": "second-pass-after-other-pairs", "lhs_index": witness_lhs,
                 "rhs_index": witness_rhs, "value": bool(detail_value & 2)},
            ),
        )
    detail_map = {
        _BROKER_DETAIL_SORT_CONTRACT: (
            OracleRejectKind.EXECUTION, "candidate-sort-call-contract-violation"
        ),
        _BROKER_DETAIL_COMPARATOR_THREW: (
            OracleRejectKind.EXECUTION, "candidate-comparator-threw"
        ),
        _BROKER_DETAIL_CALL_COUNT: (
            OracleRejectKind.EXECUTION, "candidate-comparator-call-count-invalid"
        ),
        _BROKER_DETAIL_ABORTED: (
            OracleRejectKind.EXECUTION, "candidate-comparator-aborted"
        ),
        _BROKER_DETAIL_SANDBOX: (
            OracleRejectKind.EXECUTION, "candidate-sandbox-violation"
        ),
        _BROKER_DETAIL_EXECUTION_FAULT: (
            OracleRejectKind.EXECUTION, "candidate-execution-fault"
        ),
        _BROKER_DETAIL_SIGNAL: (
            OracleRejectKind.EXECUTION, "candidate-process-signalled"
        ),
        _BROKER_DETAIL_OBSERVATION_SIZE: (
            OracleRejectKind.PROTOCOL, "candidate-observation-size-invalid"
        ),
        _BROKER_DETAIL_OBSERVATION_VALUE: (
            OracleRejectKind.PROTOCOL, "candidate-observation-value-invalid"
        ),
        _BROKER_DETAIL_OBSERVATION_WRITE: (
            OracleRejectKind.EXECUTION, "candidate-observation-write-failed"
        ),
        _BROKER_DETAIL_CPU: (
            OracleRejectKind.TIMEOUT, "candidate-run-cpu-limit-exceeded"
        ),
    }
    if detail not in detail_map:
        raise _EvaluationUnavailable("protocol", "record-reject-detail-invalid")
    kind, reason_code = detail_map[detail]
    return None, SortSwoFinding(
        kind, reason_code, corpus_id=execution_corpus_id, order_id=order,
        observations=(
            {"point": "broker-waitid", "status": detail_value},
        ) if detail_value else (),
    )


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
    _parse_dependency_manifest,
    _dependency_file_inventory,
    _verify_dependency_root,
    _read_verified_dependency_file,
    _prepare_verified_dependency,
    _assert_verified_dependency_unchanged,
    _dependency_command,
    _dependency_manifest_closure,
    _compile_verified,
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
        {
            "_CORPORA": tuple(corpora),
            "_DEPENDENCY_MANIFEST_NAME": _DEPENDENCY_MANIFEST_NAME,
            "_MIN_DEPENDENCY_MANIFEST_CLOSURE": (
                _MIN_DEPENDENCY_MANIFEST_CLOSURE
            ),
            "_N": n,
            "_ORDERS": tuple(orders),
        },
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
_ORACLE_CONTRACT_COMPONENTS_SCHEMA = "sort-swo-contract-components-v2"
_ORACLE_CONTRACT_COMPONENTS = {
    "axiom_checker_implementation_sha256": AXIOM_CHECKER_IMPLEMENTATION_SHA256,
    "compile_flags_sha256": COMPILE_FLAGS_SHA256,
    "corpus_sha256": CORPUS_SHA256,
    "dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
    "guarantee_boundary_sha256": hashlib.sha256(
        SORT_SWO_GUARANTEE_BOUNDARY.encode("ascii")
    ).hexdigest(),
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
    dependency: _VerifiedDependencyRoot, materialized_hash: str,
    proposal_hash: str, source: str,
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
        tu_sha256=_translation_unit_bundle_sha256(source),
        tu_template_sha256=TU_TEMPLATE_SHA256,
        dependency_root_realpath=os.fspath(dependency.root),
        dependency_config_sha256=dependency.config_sha256,
        dependency_manifest_sha256=dependency.manifest_sha256,
        guarantee_boundary=SORT_SWO_GUARANTEE_BOUNDARY,
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
            try:
                dependency = _prepare_verified_dependency(
                    environment.dependency_root,
                    temp / "verified-masstree",
                )
            except _DependencyVerificationError as exc:
                return _unavailable_result(
                    materialized_hash, proposal_hash,
                    phase="dependency-verification",
                    detail_code=exc.detail_code,
                    environment=environment,
                )
            control_source = _translation_unit(_TRUSTED_CONTROL_STATEMENT)
            control_executable = temp / "trusted-control"
            control_finding, control_unavailable = _compile_verified(
                control_source, temp / "trusted-control.cpp", control_executable,
                compiler=os.fspath(environment.compiler), ccbench_dir=ccbench,
                dependency=dependency,
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
                dependency=dependency,
                materialized_hash=materialized_hash, proposal_hash=proposal_hash,
                source=candidate_source,
            )
            finding, unavailable = _compile_verified(
                candidate_source, temp / "oracle.cpp", executable,
                compiler=os.fspath(environment.compiler), ccbench_dir=ccbench,
                dependency=dependency,
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
                            postflight_finding, postflight_unavailable = _compile_verified(
                                control_source,
                                postflight_source_path,
                                postflight_executable,
                                compiler=os.fspath(environment.compiler),
                                ccbench_dir=ccbench,
                                dependency=dependency,
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
    "DEPENDENCY_MANIFEST_SHA256",
    "GRAMMAR_VERSION", "N", "ORDERS",
    "INFRASTRUCTURE_REASON_CODE", "ORACLE_COMPONENTS_SHA256",
    "ORACLE_CONTRACT_ID", "PROTOCOL_VERSION",
    "SORT_SWO_GUARANTEE_BOUNDARY",
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


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--sort-swo-broker":
        raise SystemExit(_broker_main(sys.argv[2:]))
    raise SystemExit("sort_swo_oracle.py is not a standalone command")
