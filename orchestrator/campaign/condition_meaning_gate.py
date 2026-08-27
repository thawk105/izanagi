# -*- coding: utf-8 -*-
"""Call-scoped BACKOFF_FIXED supply and decoder-meaning gates.

The two public assertion functions are independent. The supply arm rederives
the source-owner-specific CMake cache-to-TU mapping. The meaning arm compiles
captured materialized hole bytes in a standalone TU and compares a finite set
of declared pointwise witnesses. Neither arm is wired into a campaign driver.

Claim boundary: this module does not prove dynamic branch reachability, the
actual target TU, or exact post-configure build input. ``driver_integration``
is always ``"none"``. Compiler path snapshots narrow identity drift around
version and compile invocations, but do not attest a same-UID adversarial
process, delegated compiler processes, the network, or a sandbox. In
particular, a process that changes and restores an executable wholly between
the portable pre/post snapshots remains outside this proof, and the recorded
version line remains the executable's self-report rather than an attestation.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import stat
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from . import source_digest
from .evolve_block import extract_materialized_evolve_block
from .model import Genome


RELATED_DEFINE_DECODE_MACROS = frozenset({
    "BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACKOFF_TRIGGER_GATING",
    "SORT_VARIANT", "SS2PL_LOCK_IMPL", "SS2PL_LOCK_KIND", "SS2PL_DLR",
    "SS2PL_WFG_DIAG",
})
SUPPORTED_MACROS = frozenset({"BACKOFF_FIXED"})
SOURCE_REL = "include/backoff.hh"
OPTIONS_REL = "cmake/Options.cmake"
PROTOCOL = "silo"
PROTOCOL_CMAKE_REL = "cc/silo/CMakeLists.txt"
MARKER_ID = "silo-backoff-magnitude"
MACRO = "BACKOFF_FIXED"
RESULT_IDENTIFIER = "now_backoff"
CONTEXT_STARTS = (1, 2)
PROCESS_TIMEOUT_SECONDS = 120.0
DRIVER_INTEGRATION = "none"
SUPPLY_PROOF_KIND = "cmake-source-owner-resolved-cache-to-tu-define"
MEANING_PROOF_KIND = (
    "compiler-evaluated-captured-applied-source-decoder-standalone-tu-"
    "finite-pointwise-witness"
)
_BITS_RE = re.compile(r"[0-9a-f]{16}\Z")
_ROW_RE = re.compile(rb"([0-9]+) ([0-9]+) ([0-9a-f]{16})\Z")


class ConditionMeaningGateError(RuntimeError):
    """Structured fail-closed rejection from exactly one arm."""

    def __init__(
        self,
        reason_code: str,
        detail: str,
        *,
        define_value: int | None = None,
        context_index: int | None = None,
        expected: str | None = None,
        observed: str | None = None,
    ) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail
        self.define_value = define_value
        self.context_index = context_index
        self.expected = expected
        self.observed = observed


@dataclass(frozen=True, slots=True)
class RegularFileIdentity:
    """Portable regular-file identity fields used by capture evidence."""

    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True, slots=True)
class CapturedFileEvidence:
    """Identity and content hash of one input held open during capture."""

    relative_path: str
    before: RegularFileIdentity
    after: RegularFileIdentity
    path_after: RegularFileIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class CapturedBackoffFixedInputs:
    """One dirfd-anchored read of the three code-owned inputs."""

    root: str
    source_bytes: bytes
    options_text: str
    protocol_cmake_text: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    input_files: tuple[CapturedFileEvidence, ...]


@dataclass(frozen=True, slots=True)
class SupplyObservation:
    define_value: int
    cache_name: str
    effective_value: str


@dataclass(frozen=True, slots=True)
class SupplyEvidence:
    proof_kind: str
    driver_integration: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    source_rel: str
    owner_protocol: str
    input_files: tuple[CapturedFileEvidence, ...]
    observations: tuple[SupplyObservation, ...]


@dataclass(frozen=True, slots=True)
class MeaningCase:
    """One non-negative define value and bits expected for start=1, then 2."""

    define_value: int
    expected_float64_bits_by_context: tuple[str, str]

    def __post_init__(self) -> None:
        _validate_define_value(self.define_value)
        if type(self.expected_float64_bits_by_context) is not tuple \
                or len(self.expected_float64_bits_by_context) != len(CONTEXT_STARTS):
            raise ValueError("expected bits must be an exact two-item tuple")
        for bits in self.expected_float64_bits_by_context:
            if type(bits) is not str or _BITS_RE.fullmatch(bits) is None:
                raise ValueError("expected float64 bits must be 16 lowercase hex digits")
            if not math.isfinite(_float_from_bits(bits)):
                raise ValueError("expected float64 bits must encode a finite value")


@dataclass(frozen=True, slots=True)
class MeaningObservation:
    define_value: int
    context_index: int
    start: int
    expected_bits: str
    observed_bits: str


@dataclass(frozen=True, slots=True)
class MeaningEvidence:
    """Finite witness evidence with bounded, portable compiler snapshots."""

    proof_kind: str
    driver_integration: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    hole_sha256: str
    compiler_path: str
    compiler_version: str
    compiler_argv: tuple[str, ...]
    run_argv: tuple[str, ...]
    input_files: tuple[CapturedFileEvidence, ...]
    compiler_identities: tuple["CompilerFileEvidence", ...]
    observations: tuple[MeaningObservation, ...]


@dataclass(frozen=True, slots=True)
class CompilerFileEvidence:
    """One compiler path identity/hash snapshot at a declared phase."""

    phase: str
    identity: RegularFileIdentity
    sha256: str


def canonical_float64_bits(value: float) -> str:
    """Return canonical lowercase bits for one finite binary64 value."""
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("value must be an exact finite float")
    return struct.pack(">d", value).hex()


def _float_from_bits(bits: str) -> float:
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def _validate_define_value(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("BACKOFF_FIXED must be a non-negative exact integer")
    return value


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_identity(value: os.stat_result) -> RegularFileIdentity:
    return RegularFileIdentity(
        device=value.st_dev,
        inode=value.st_ino,
        size=value.st_size,
        mtime_ns=value.st_mtime_ns,
        ctime_ns=value.st_ctime_ns,
    )


def _nofollow_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ConditionMeaningGateError(
            "input-capture-failed",
            "this Python platform cannot enforce dirfd no-symlink capture",
        )
    return getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW


def _open_relative_nofollow(root_descriptor: int, relative: str) -> int:
    """Open a code-owned relative file via no-symlink component traversal."""
    parts = Path(relative).parts
    invalid_component = any(part in {"", ".", ".."} for part in parts)
    if not parts or Path(relative).is_absolute() or invalid_component:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"captured input path is invalid: {relative!r}",
        )
    nofollow = _nofollow_flags()
    current = os.dup(root_descriptor)
    try:
        for component in parts[:-1]:
            following = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | nofollow, dir_fd=current,
            )
            try:
                opened = os.fstat(following)
            except OSError:
                os.close(following)
                raise
            if not stat.S_ISDIR(opened.st_mode):
                os.close(following)
                raise OSError(f"non-directory path component {component!r}")
            os.close(current)
            current = following
        descriptor = os.open(parts[-1], os.O_RDONLY | nofollow, dir_fd=current)
        try:
            opened = os.fstat(descriptor)
        except OSError:
            os.close(descriptor)
            raise
        if not stat.S_ISREG(opened.st_mode):
            os.close(descriptor)
            raise OSError(f"non-regular captured input {relative!r}")
        return descriptor
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed",
            f"cannot open captured input without symlinks: {relative!r}",
        ) from exc
    finally:
        os.close(current)


def _read_descriptor(
    descriptor: int,
    relative: str,
) -> tuple[bytes, RegularFileIdentity, RegularFileIdentity]:
    try:
        before = _file_identity(os.fstat(descriptor))
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = _file_identity(os.fstat(descriptor))
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"cannot read captured input {relative!r}",
        ) from exc
    value = b"".join(chunks)
    if before != after or len(value) != after.size:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"captured input changed while reading: {relative!r}",
        )
    return value, before, after


def capture_backoff_fixed_inputs(
    ccbench_root: str | os.PathLike[str],
) -> CapturedBackoffFixedInputs:
    """Open all three inputs first, then read them from a no-symlink dirfd walk."""
    root_descriptor: int | None = None
    try:
        root = Path(ccbench_root).resolve(strict=True)
        nofollow = _nofollow_flags()
        root_path_identity = _file_identity(os.stat(root, follow_symlinks=False))
        root_descriptor = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | nofollow,
        )
        root_fd_identity = _file_identity(os.fstat(root_descriptor))
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if root_descriptor is not None:
            os.close(root_descriptor)
        raise ConditionMeaningGateError(
            "input-capture-failed", "ccbench root cannot be resolved",
        ) from exc
    if root_path_identity != root_fd_identity:
        os.close(root_descriptor)
        raise ConditionMeaningGateError(
            "input-capture-failed", "ccbench root changed while opening",
        )
    relatives = (SOURCE_REL, OPTIONS_REL, PROTOCOL_CMAKE_REL)
    descriptors: dict[str, int] = {}
    try:
        for relative in relatives:
            descriptors[relative] = _open_relative_nofollow(root_descriptor, relative)
        values: dict[str, bytes] = {}
        files: list[CapturedFileEvidence] = []
        pending: list[tuple[str, bytes, RegularFileIdentity, RegularFileIdentity]] = []
        for relative in relatives:
            value, before, after = _read_descriptor(descriptors[relative], relative)
            pending.append((relative, value, before, after))
        for relative, value, before, after in pending:
            path_descriptor = _open_relative_nofollow(root_descriptor, relative)
            try:
                path_after = _file_identity(os.fstat(path_descriptor))
            finally:
                os.close(path_descriptor)
            if path_after != after:
                raise ConditionMeaningGateError(
                    "input-capture-failed",
                    f"captured input path changed during capture: {relative!r}",
                )
            values[relative] = value
            files.append(CapturedFileEvidence(
                relative_path=relative,
                before=before,
                after=after,
                path_after=path_after,
                sha256=_sha256(value),
            ))
        if _file_identity(os.stat(root, follow_symlinks=False)) != root_fd_identity:
            raise ConditionMeaningGateError(
                "input-capture-failed", "ccbench root path changed during capture",
            )
    except ConditionMeaningGateError:
        raise
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input namespace changed during capture",
        ) from exc
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(root_descriptor)

    source_bytes = values[SOURCE_REL]
    options_bytes = values[OPTIONS_REL]
    protocol_bytes = values[PROTOCOL_CMAKE_REL]
    try:
        options_text = options_bytes.decode("utf-8")
        protocol_text = protocol_bytes.decode("utf-8")
        source_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured inputs must be UTF-8",
        ) from exc
    return CapturedBackoffFixedInputs(
        root=os.fspath(root),
        source_bytes=source_bytes,
        options_text=options_text,
        protocol_cmake_text=protocol_text,
        source_sha256=_sha256(source_bytes),
        options_sha256=_sha256(options_bytes),
        protocol_cmake_sha256=_sha256(protocol_bytes),
        input_files=tuple(files),
    )


def _requested_values(values: Iterable[int]) -> tuple[int, ...]:
    try:
        requested = tuple(values)
    except TypeError as exc:
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "requested values are not iterable",
        ) from exc
    if not requested:
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "at least one requested value is required",
        )
    try:
        checked = tuple(_validate_define_value(value) for value in requested)
    except ValueError as exc:
        raise ConditionMeaningGateError("supply-contract-invalid", str(exc)) from exc
    if len(set(checked)) != len(checked):
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "requested values must be unique",
        )
    return checked


def _validate_captured(captured: CapturedBackoffFixedInputs) -> None:
    if type(captured) is not CapturedBackoffFixedInputs:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input has the wrong exact type",
        )
    hashes = (
        (captured.source_bytes, captured.source_sha256),
        (captured.options_text.encode("utf-8"), captured.options_sha256),
        (captured.protocol_cmake_text.encode("utf-8"), captured.protocol_cmake_sha256),
    )
    if any(_sha256(value) != expected for value, expected in hashes):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input hashes are inconsistent",
        )
    expected_files = {
        SOURCE_REL: captured.source_sha256,
        OPTIONS_REL: captured.options_sha256,
        PROTOCOL_CMAKE_REL: captured.protocol_cmake_sha256,
    }
    if len(captured.input_files) != len(expected_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input evidence is incomplete",
        )
    if any(type(entry) is not CapturedFileEvidence for entry in captured.input_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input evidence has the wrong type",
        )
    observed_files = {entry.relative_path: entry for entry in captured.input_files}
    if set(observed_files) != set(expected_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input paths are inconsistent",
        )
    for relative, expected_sha256 in expected_files.items():
        entry = observed_files[relative]
        if (entry.before != entry.after
                or entry.after != entry.path_after
                or entry.sha256 != expected_sha256):
            raise ConditionMeaningGateError(
                "input-capture-failed",
                f"captured input identity evidence is inconsistent: {relative!r}",
            )


def assert_backoff_fixed_supply(
    captured: CapturedBackoffFixedInputs,
    requested_values: Iterable[int],
) -> SupplyEvidence:
    """Independently require exact cache-to-TU supply for every value."""
    _validate_captured(captured)
    values = _requested_values(requested_values)
    observations: list[SupplyObservation] = []
    for value in values:
        try:
            resolution = source_digest.resolve_effective_defines_from_cmake_sources(
                SOURCE_REL,
                Genome(PROTOCOL, {MACRO: value}),
                options_text=captured.options_text,
                protocol_cmake_text=captured.protocol_cmake_text,
            )
        except (RuntimeError, TypeError, ValueError) as exc:
            raise ConditionMeaningGateError(
                "supply-set-unavailable", "effective CMake supply cannot be rederived",
                define_value=value,
            ) from exc
        cache_name = resolution.cache_name(MACRO)
        if MACRO not in resolution.supplied_macros:
            raise ConditionMeaningGateError(
                "macro-not-supplied", "BACKOFF_FIXED cache-to-TU mapping is absent",
                define_value=value,
            )
        effective = resolution.effective_value(MACRO)
        if cache_name != MACRO or effective != str(value):
            route = "bare define without a cache mapping" if cache_name is None \
                else f"CCBENCH_{cache_name}"
            if cache_name != MACRO:
                route += f", not CCBENCH_{MACRO}"
            raise ConditionMeaningGateError(
                "supply-value-mismatch",
                f"BACKOFF_FIXED maps through {route}, to {effective!r}",
                define_value=value,
                expected=str(value),
                observed=effective,
            )
        observations.append(SupplyObservation(value, cache_name, effective))
    return SupplyEvidence(
        proof_kind=SUPPLY_PROOF_KIND,
        driver_integration=DRIVER_INTEGRATION,
        source_sha256=captured.source_sha256,
        options_sha256=captured.options_sha256,
        protocol_cmake_sha256=captured.protocol_cmake_sha256,
        source_rel=SOURCE_REL,
        owner_protocol=resolution.owner_protocol,
        input_files=captured.input_files,
        observations=tuple(observations),
    )


def _validated_cases(cases: Sequence[MeaningCase]) -> tuple[MeaningCase, ...]:
    if type(cases) not in {tuple, list} or not cases:
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "cases must be a non-empty tuple or list",
        )
    values = tuple(case.define_value for case in cases if type(case) is MeaningCase)
    if len(values) != len(cases):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "every case must be an exact MeaningCase",
        )
    if len(set(values)) != len(values):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "define values must be unique",
        )
    return tuple(cases)


def _render_evaluation_tu(hole: str, cases: Sequence[MeaningCase]) -> str:
    rows: list[str] = []
    for case_index, case in enumerate(cases):
        for context_index, start in enumerate(CONTEXT_STARTS):
            rows.extend([
                "  {",
                f"#define {MACRO} {case.define_value}",
                f"    [[maybe_unused]] std::uint64_t start = {start}ULL;",
                hole,
                f"#undef {MACRO}",
                "    std::uint64_t observed_bits = 0;",
                f"    static_assert(std::is_same_v<decltype({RESULT_IDENTIFIER}), double>);",
                f"    static_assert(sizeof({RESULT_IDENTIFIER}) == sizeof(observed_bits));",
                f"    std::memcpy(&observed_bits, &{RESULT_IDENTIFIER}, sizeof(observed_bits));",
                f'    std::printf("{case_index} {context_index} %016llx\\n",',
                "                static_cast<unsigned long long>(observed_bits));",
                "  }",
            ])
    return "\n".join([
        "#include <cstdint>",
        "#include <cstdio>",
        "#include <cstring>",
        "#include <type_traits>",
        "int main() {",
        *rows,
        "  return 0;",
        "}",
        "",
    ])


def _resolve_compiler(cxx: str) -> Path:
    if type(cxx) is not str or not cxx:
        raise ConditionMeaningGateError("compiler-failed", "compiler name is invalid")
    candidate = shutil.which(cxx) if os.sep not in cxx else cxx
    if candidate is None:
        raise ConditionMeaningGateError("compiler-failed", "compiler was not found")
    try:
        compiler = Path(candidate).resolve(strict=True)
        mode = compiler.stat().st_mode
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError("compiler-failed", "compiler cannot be resolved") from exc
    if not stat.S_ISREG(mode) or not os.access(compiler, os.X_OK):
        raise ConditionMeaningGateError("compiler-failed", "compiler is not executable")
    return compiler


def _capture_compiler_identity(compiler: Path, phase: str) -> CompilerFileEvidence:
    """Capture one regular compiler path before or after an invocation.

    This is a deliberate injection seam for deterministic drift tests. It is a
    path snapshot, not proof of which executable image a hostile process ran.
    """
    reason = "compiler-failed" if phase == "before-version" else "compiler-identity-drift"
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(compiler, flags)
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler path is unavailable at {phase}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ConditionMeaningGateError(reason, f"compiler is not regular at {phase}")
        if not os.access(compiler, os.X_OK):
            raise ConditionMeaningGateError(reason, f"compiler is not executable at {phase}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler cannot be read at {phase}") from exc
    finally:
        os.close(descriptor)
    content = b"".join(chunks)
    before_identity = _file_identity(before)
    after_identity = _file_identity(after)
    try:
        path_identity = _file_identity(os.stat(compiler, follow_symlinks=False))
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler path disappeared at {phase}") from exc
    if (before_identity != after_identity
            or after_identity != path_identity
            or len(content) != after_identity.size):
        raise ConditionMeaningGateError(reason, f"compiler changed during {phase} capture")
    return CompilerFileEvidence(
        phase=phase,
        identity=after_identity,
        sha256=_sha256(content),
    )


def _require_same_compiler(
    baseline: CompilerFileEvidence,
    observed: CompilerFileEvidence,
) -> None:
    if baseline.identity != observed.identity or baseline.sha256 != observed.sha256:
        raise ConditionMeaningGateError(
            "compiler-identity-drift",
            f"compiler path identity/content changed by {observed.phase}",
        )


def _run_process(
    argv: Sequence[str],
    *,
    timeout_reason: str,
    failure_reason: str,
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            list(argv), capture_output=True, timeout=PROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConditionMeaningGateError(timeout_reason, "process exceeded 120 seconds") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise ConditionMeaningGateError(failure_reason, "process could not be executed") from exc
    if completed.returncode != 0:
        raise ConditionMeaningGateError(
            failure_reason,
            f"process returned rc={completed.returncode}; stderr={completed.stderr[-500:]!r}",
        )
    if completed.stderr:
        raise ConditionMeaningGateError(
            failure_reason, f"successful process wrote stderr={completed.stderr[-500:]!r}",
        )
    return completed


def _parse_observed_rows(
    stdout: bytes,
    cases: Sequence[MeaningCase],
) -> dict[tuple[int, int], str]:
    expected_rows = {
        (case_index, context_index)
        for case_index in range(len(cases))
        for context_index in range(len(CONTEXT_STARTS))
    }
    observed: dict[tuple[int, int], str] = {}
    for raw_line in stdout.splitlines():
        match = _ROW_RE.fullmatch(raw_line)
        if match is None:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", f"malformed output row {raw_line!r}",
            )
        try:
            identity = (int(match.group(1)), int(match.group(2)))
        except ValueError as exc:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", "output row index is not a bounded Python integer",
            ) from exc
        if identity not in expected_rows or identity in observed:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", f"unknown or duplicate output row {identity!r}",
            )
        bits = match.group(3).decode("ascii")
        if not math.isfinite(_float_from_bits(bits)):
            raise ConditionMeaningGateError(
                "decoded-output-nonfinite", f"non-finite output at row {identity!r}",
                define_value=(cases[identity[0]].define_value
                              if identity[0] < len(cases) else None),
                context_index=identity[1],
                observed=bits,
            )
        observed[identity] = bits
    if set(observed) != expected_rows:
        missing = sorted(expected_rows - set(observed))
        raise ConditionMeaningGateError(
            "compiler-output-invalid", f"missing output rows {missing!r}",
        )
    return observed


def assert_backoff_fixed_meaning(
    captured: CapturedBackoffFixedInputs,
    cases: Sequence[MeaningCase],
    *,
    cxx: str,
) -> MeaningEvidence:
    """Compile captured decoder bytes and require pointwise binary64 meaning."""
    _validate_captured(captured)
    checked_cases = _validated_cases(cases)
    try:
        source_text = captured.source_bytes.decode("utf-8")
        block = extract_materialized_evolve_block(source_text, MARKER_ID)
    except (UnicodeError, ValueError) as exc:
        raise ConditionMeaningGateError(
            "materialized-decoder-invalid", "unique BACKOFF_FIXED decoder hole is unavailable",
        ) from exc
    if not block.hole.strip():
        raise ConditionMeaningGateError(
            "materialized-decoder-invalid", "captured decoder hole is empty",
        )
    hole_sha256 = _sha256(block.hole.encode("utf-8"))
    tu = _render_evaluation_tu(block.hole, checked_cases)
    compiler = _resolve_compiler(cxx)
    compiler_identities = [
        _capture_compiler_identity(compiler, "before-version"),
    ]

    version_argv = (os.fspath(compiler), "--version")
    version_result = _run_process(
        version_argv, timeout_reason="compiler-timeout", failure_reason="compiler-failed",
    )
    compiler_identities.append(_capture_compiler_identity(compiler, "after-version"))
    _require_same_compiler(compiler_identities[0], compiler_identities[-1])
    try:
        version_lines = version_result.stdout.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "compiler-failed", "compiler identity is not UTF-8",
        ) from exc
    if not version_lines or not version_lines[0]:
        raise ConditionMeaningGateError("compiler-failed", "compiler identity is empty")

    with tempfile.TemporaryDirectory(prefix="izanagi_condition_meaning_") as temporary:
        source_path = Path(temporary) / "decoder.cc"
        binary_path = Path(temporary) / "decoder"
        source_path.write_text(tu, encoding="utf-8")
        compiler_argv = (
            os.fspath(compiler), *source_digest.BUILD_FLAGS,
            "-Wall", "-Wextra", "-Werror", "-x", "c++",
            os.fspath(source_path), "-o", os.fspath(binary_path),
        )
        _run_process(
            compiler_argv,
            timeout_reason="compiler-timeout",
            failure_reason="compiler-failed",
        )
        compiler_identities.append(_capture_compiler_identity(compiler, "after-compile"))
        _require_same_compiler(compiler_identities[0], compiler_identities[-1])
        run_argv = (os.fspath(binary_path),)
        run_result = _run_process(
            run_argv,
            timeout_reason="decoder-run-timeout",
            failure_reason="decoder-run-failed",
        )
        observed = _parse_observed_rows(run_result.stdout, checked_cases)

    observations: list[MeaningObservation] = []
    for case_index, case in enumerate(checked_cases):
        for context_index, start in enumerate(CONTEXT_STARTS):
            expected_bits = case.expected_float64_bits_by_context[context_index]
            observed_bits = observed[(case_index, context_index)]
            if observed_bits != expected_bits:
                raise ConditionMeaningGateError(
                    "decoded-meaning-mismatch",
                    "captured decoder result differs from declared pointwise meaning",
                    define_value=case.define_value,
                    context_index=context_index,
                    expected=expected_bits,
                    observed=observed_bits,
                )
            observations.append(MeaningObservation(
                define_value=case.define_value,
                context_index=context_index,
                start=start,
                expected_bits=expected_bits,
                observed_bits=observed_bits,
            ))
    return MeaningEvidence(
        proof_kind=MEANING_PROOF_KIND,
        driver_integration=DRIVER_INTEGRATION,
        source_sha256=captured.source_sha256,
        options_sha256=captured.options_sha256,
        protocol_cmake_sha256=captured.protocol_cmake_sha256,
        hole_sha256=hole_sha256,
        compiler_path=os.fspath(compiler),
        compiler_version=version_lines[0],
        compiler_argv=compiler_argv,
        run_argv=run_argv,
        input_files=captured.input_files,
        compiler_identities=tuple(compiler_identities),
        observations=tuple(observations),
    )


__all__ = [
    "CONTEXT_STARTS", "DRIVER_INTEGRATION", "MEANING_PROOF_KIND",
    "PROCESS_TIMEOUT_SECONDS", "RELATED_DEFINE_DECODE_MACROS", "SUPPORTED_MACROS",
    "SUPPLY_PROOF_KIND",
    "CapturedBackoffFixedInputs", "CapturedFileEvidence", "CompilerFileEvidence",
    "ConditionMeaningGateError", "MeaningCase", "MeaningEvidence", "MeaningObservation",
    "RegularFileIdentity", "SupplyEvidence", "SupplyObservation",
    "assert_backoff_fixed_meaning", "assert_backoff_fixed_supply",
    "canonical_float64_bits", "capture_backoff_fixed_inputs",
]
