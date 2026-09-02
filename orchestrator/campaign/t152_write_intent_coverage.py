#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-152 write-intent shadow characterization (correctness-only, not integrated).

The target CCBench commit is deliberately not coupled to orchestrator.campaign.pin: this
driver characterizes the staged T-152 commit before a separately approved pin
bump.  Every build uses patchharness.checkout() and a fresh build directory, so
the external/ccbench working tree and HEAD are never changed.

Seven trace-enabled runs form the gate:
  1. stock, single-thread update-only YCSB;
  2. stock, contended YCSB that must exercise abort cleanup;
  3. stock BOMB smoke covering update/insert/delete;
  4-7. erase, forge, op-swap, and pointer-swap positive controls.

This is correctness characterization only.  It intentionally records no
throughput or latency values and performs no single-tenant assertion.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import condition_meaning_gate  # noqa: E402
from .layout import repo_output_root  # noqa: E402
from .patchharness import applied, checkout  # noqa: E402
from .materializer_admission import non_admissible_materializer  # noqa: E402



CONFIGURE_TIMEOUT_S = 120.0
BUILD_TIMEOUT_S = 600.0
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 300.0
DEFAULT_CC = "gcc-12"
DEFAULT_CXX = "g++-12"
DEFAULT_JOBS = 8
MAX_JOBS = 8
CLK = 2100

MISSING_REASON = "intent-missing-from-write-set"
UNEXPECTED_REASON = "write-set-entry-without-intent"

_BASE_DEFINES = (
    "-DCCBENCH_BACK_OFF=1",
    "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
    "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
    "-DCCBENCH_WAL=0",
    "-DCCBENCH_TRACE=1",
)

_PATCHES = {
    "erase": (
        "broken-silo-write-intent-erase.patch",
        "IZANAGI_BREAK_WRITE_INTENT_ERASE",
    ),
    "forge": (
        "broken-silo-write-intent-forge.patch",
        "IZANAGI_BREAK_WRITE_INTENT_FORGE",
    ),
    "opswap": (
        "broken-silo-write-intent-opswap.patch",
        "IZANAGI_BREAK_WRITE_INTENT_OPSWAP",
    ),
    "ptrswap": (
        "broken-silo-write-intent-ptrswap.patch",
        "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
    ),
}

_YCSB_SINGLE_FLAGS = {
    "ycsb_tuple_num": "200",
    "ycsb_zipf_skew": "0.9",
    "ycsb_rmw": "false",
    "ycsb_rratio": "0",
    "ycsb_max_ope": "10",
    "thread_num": "1",
    "extime": "1",
}

_YCSB_ABORT_FLAGS = {
    "ycsb_tuple_num": "200",
    "ycsb_zipf_skew": "0.9",
    "ycsb_rmw": "true",
    "ycsb_rratio": "50",
    "ycsb_max_ope": "10",
    "thread_num": "2",
    "extime": "1",
}

# Use only S1's updates and S3's delete-then-add path.  Their two workers cover
# U and D/I without racing L1's fatal empty-target check.  The loader always
# partitions work over 64 threads, so bomb_work_size=64 is the smallest
# non-overlapping scale.
_BOMB_FLAGS = {
    "thread_num": "2",
    "extime": "1",
    "bomb_l1_thread_num": "0",
    "bomb_s1_thread_num": "1",
    "bomb_s2_thread_num": "0",
    "bomb_s3_thread_num": "1",
    "bomb_s4_thread_num": "0",
    "bomb_factory_size": "1",
    "bomb_product_size": "8",
    "bomb_work_size": "64",
    "bomb_material_size": "8",
    "bomb_tree_num_per_product": "1",
    "bomb_base_tree_size": "2",
    "bomb_material_per_wip": "1",
    "bomb_base_product_size_per_factory": "4",
    "bomb_mc_update_size": "1",
}

_ABORT_RE = re.compile(r"(?m)^abort_counts_:\s*(\d+)\s*$")
_CMAKE_LIBRARY_KEYS = {
    "gflags": "gflags_LIBRARY_FILE",
    "glog": "glog_LIBRARY_FILE",
}

_PERFORMANCE_SEMANTICS = (
    "none (trace-enabled correctness run; counts must not be compared as throughput)"
)

_KNOWN_LIMITATIONS = (
    "delete_record cancel-previous-write mirroring is not exercised by this "
    "characterization: BOMB does not execute update->delete for the same key "
    "in the same transaction; detection-coverage claims exclude it.",
    "patchharness internal git subprocesses have no timeout (existing shared "
    "infrastructure behavior).",
)


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_process(argv: list[str], *, timeout: float, cwd: str | None = None,
                 env: dict[str, str] | None = None,
                 label: str) -> subprocess.CompletedProcess[str]:
    """Run one bounded subprocess and turn every nonzero status into a hard error."""
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"{label} failed to run: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"{label} failed (rc={proc.returncode}): "
            f"{(proc.stderr or proc.stdout).strip()[-500:]}"
        )
    return proc


def _require_condition_gate(
    source_root: str,
    *,
    macro: str,
    cmake: str,
    cxx: str,
    configure_args: Iterable[str],
) -> dict[str, Any]:
    captured = condition_meaning_gate.capture_define_inputs(
        source_root, configure_args=tuple(configure_args),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.t152_write_intent_coverage",
        macro=macro,
        requested_value=1,
        default_value=0,
    )
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake=cmake,
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=condition_meaning_gate.declare_define_runtime_meaning(request),
        cxx=cxx,
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    if not admission.admitted:
        raise RuntimeError(
            f"condition gate rejected {macro}: "
            f"supply={supply.terminal_status}/{supply.reason_code}, "
            f"meaning={meaning.terminal_status}/{meaning.reason_code}"
        )
    return {
        "supply": json.loads(supply.canonical_json()),
        "meaning": json.loads(meaning.canonical_json()),
        "admission": json.loads(admission.canonical_json()),
    }


def _preflight_condition_gates(
    *,
    sha: str,
    ccbench_base: str,
    root: str,
    cmake: str,
    cc: str,
    cxx: str,
    cmake_prefix_path: str,
) -> list[dict[str, Any]]:
    configure_args = (
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={cc}",
        f"-DCMAKE_PREFIX_PATH={cmake_prefix_path}",
        *_BASE_DEFINES,
    )
    records = []
    for patch_name, macro in _PATCHES.values():
        with checkout(sha, base_dir=ccbench_base) as source_root:
            with applied(os.path.join(root, "patches", patch_name), sha, source_root):
                records.append(_require_condition_gate(
                    source_root,
                    macro=macro,
                    cmake=cmake,
                    cxx=cxx,
                    configure_args=configure_args,
                ))
    return records


def _resolve_executable(command: str, role: str) -> str:
    candidate = shutil.which(command)
    if candidate is None:
        raise RuntimeError(f"{role} executable not found: {command}")
    realpath = os.path.realpath(candidate)
    if not os.path.isfile(realpath) or not os.access(realpath, os.X_OK):
        raise RuntimeError(f"{role} executable is not an executable file: {realpath}")
    return realpath


def _tool_record(command: str, role: str) -> dict[str, str]:
    realpath = _resolve_executable(command, role)
    proc = _run_process(
        [realpath, "--version"],
        timeout=CONFIGURE_TIMEOUT_S,
        label=f"{role} --version",
    )
    lines = [line.strip() for line in (proc.stdout or proc.stderr).splitlines()
             if line.strip()]
    if not lines:
        raise RuntimeError(f"{role} --version returned no version line")
    return {"realpath": realpath, "version": lines[0]}


def _dependency_contract(raw: str | None) -> tuple[dict[str, Any], str]:
    """Validate dependency headers/libraries and return realpath provenance."""
    if raw is None or not raw.strip():
        raise RuntimeError("CMAKE_PREFIX_PATH is required")
    pieces: list[str] = []
    for cmake_piece in raw.split(";"):
        pieces.extend(part for part in cmake_piece.split(os.pathsep) if part)
    if not pieces:
        raise RuntimeError("CMAKE_PREFIX_PATH contains no install prefix")

    prefixes: list[str] = []
    for piece in pieces:
        realpath = os.path.realpath(piece)
        if not os.path.isdir(realpath):
            raise RuntimeError(f"CMAKE_PREFIX_PATH prefix does not exist: {piece}")
        if realpath not in prefixes:
            prefixes.append(realpath)

    def dependency_record(
        header: str,
        library_stem: str,
        dependency: str,
    ) -> dict[str, list[str]]:
        headers: list[str] = []
        libraries: list[str] = []
        for prefix in prefixes:
            header_path = os.path.join(prefix, header)
            if os.path.isfile(header_path):
                headers.append(os.path.realpath(header_path))
            for suffix in (".so", ".a"):
                library_path = os.path.join(
                    prefix, "lib", f"lib{library_stem}{suffix}"
                )
                if os.path.isfile(library_path):
                    libraries.append(os.path.realpath(library_path))
        if not headers or not libraries:
            raise RuntimeError(
                f"{dependency} header/library not found under CMAKE_PREFIX_PATH: "
                f"{header} / lib/lib{library_stem}.so or "
                f"lib/lib{library_stem}.a"
            )
        return {"headers": headers, "libraries": libraries}

    record = {
        "cmake_prefix_path": prefixes,
        "gflags": dependency_record(
            "include/gflags/gflags.h",
            "gflags",
            "gflags",
        ),
        "glog": dependency_record(
            "include/glog/logging.h",
            "glog",
            "glog",
        ),
    }
    return record, ";".join(prefixes)


def _write_cmake_dependency_probe(build_dir: str) -> str:
    """Defer actual imported-target paths into CMakeCache for later auditing."""
    probe_path = os.path.join(build_dir, "izanagi_t152_dependency_probe.cmake")
    os.makedirs(build_dir, exist_ok=True)
    with open(probe_path, "w", encoding="utf-8") as probe:
        probe.write(
            "function(_izanagi_t152_record_dependency_links)\n"
            "  foreach(_dep IN ITEMS gflags glog)\n"
            "    if(NOT TARGET \"${_dep}::${_dep}\")\n"
            "      message(FATAL_ERROR \"missing imported target ${_dep}::${_dep}\")\n"
            "    endif()\n"
            "    get_target_property(_location \"${_dep}::${_dep}\" IMPORTED_LOCATION)\n"
            "    if(NOT _location OR _location MATCHES \"-NOTFOUND$\")\n"
            "      message(FATAL_ERROR \"missing imported location for ${_dep}::${_dep}\")\n"
            "    endif()\n"
            "    set(\"${_dep}_LIBRARY_FILE\" \"${_location}\" CACHE FILEPATH\n"
            "        \"Izanagi T-152 actual imported library\" FORCE)\n"
            "  endforeach()\n"
            "endfunction()\n"
            "cmake_language(DEFER CALL _izanagi_t152_record_dependency_links)\n"
        )
    return probe_path


def _linked_dependency_contract(
    build_dir: str,
    deps_record: dict[str, Any],
) -> dict[str, str]:
    """Read actual linked libraries from CMakeCache and match recorded prefixes."""
    cache_path = os.path.join(build_dir, "CMakeCache.txt")
    try:
        with open(cache_path, encoding="utf-8") as cache_file:
            lines = cache_file.readlines()
    except OSError as exc:
        raise RuntimeError(f"stock CMakeCache.txt is not readable: {cache_path}") from exc

    cache_values: dict[str, str] = {}
    for dependency, key in _CMAKE_LIBRARY_KEYS.items():
        prefix = f"{key}:FILEPATH="
        matches = [line.rstrip("\n")[len(prefix):]
                   for line in lines if line.startswith(prefix)]
        if len(matches) != 1 or not matches[0]:
            raise RuntimeError(
                f"stock CMakeCache.txt must contain exactly one {key}:FILEPATH"
            )
        realpath = os.path.realpath(matches[0])
        if not os.path.isfile(realpath):
            raise RuntimeError(f"{key} is not an existing file: {realpath}")
        under_recorded_prefix = False
        for recorded_prefix in deps_record["cmake_prefix_path"]:
            try:
                if (
                    os.path.commonpath([realpath, recorded_prefix])
                    == recorded_prefix
                ):
                    under_recorded_prefix = True
                    break
            except ValueError:
                continue
        if not under_recorded_prefix:
            raise RuntimeError(
                f"{key} resolved outside recorded CMAKE_PREFIX_PATH: {realpath}"
            )
        cache_values[key] = realpath
    return cache_values


def _resolve_ccbench_sha(raw_sha: str, ccbench_base: str) -> str:
    proc = _run_process(
        ["git", "-C", ccbench_base, "rev-parse", "--verify", f"{raw_sha}^{{commit}}"],
        timeout=CONFIGURE_TIMEOUT_S,
        label="resolve IZANAGI_T152_CCBENCH_SHA",
    )
    resolved = proc.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", resolved):
        raise RuntimeError(f"resolved CCBench SHA is not a full commit id: {resolved!r}")
    return resolved


def _jobs(raw: str | None) -> int:
    if raw is None:
        return DEFAULT_JOBS
    try:
        requested = int(raw)
    except ValueError as exc:
        raise RuntimeError("IZANAGI_T152_JOBS must be an integer") from exc
    if requested <= 0:
        raise RuntimeError("IZANAGI_T152_JOBS must be positive")
    return min(requested, MAX_JOBS)


def _build(
    *,
    sha: str,
    ccbench_base: str,
    build_dir: str,
    cmake: str,
    cc: str,
    cxx: str,
    cmake_prefix_path: str,
    jobs: int,
    targets: Iterable[str],
    patch_path: str | None = None,
    macro: str | None = None,
    record_dependency_links: bool = False,
) -> dict[str, str]:
    """Fresh direct-CMake build in a disposable checkout (never buildcache)."""
    target_list = list(targets)
    with contextlib.ExitStack() as stack:
        ccbench_dir = stack.enter_context(checkout(sha, base_dir=ccbench_base))
        if patch_path is not None:
            stack.enter_context(applied(patch_path, sha, ccbench_dir))
        configure = [
            cmake,
            "-S", ccbench_dir,
            "-B", build_dir,
            "-DCMAKE_BUILD_TYPE=Release",
            "-DENABLE_SANITIZER=OFF",
            f"-DCMAKE_C_COMPILER={cc}",
            f"-DCMAKE_CXX_COMPILER={cxx}",
            f"-DCMAKE_PREFIX_PATH={cmake_prefix_path}",
            *_BASE_DEFINES,
        ]
        if record_dependency_links:
            dependency_probe = _write_cmake_dependency_probe(build_dir)
            configure.append(f"-DCMAKE_PROJECT_INCLUDE={dependency_probe}")
        if macro is not None:
            configure.append(f"-DCMAKE_CXX_FLAGS=-D{macro}=1")
            _require_condition_gate(
                ccbench_dir,
                macro=macro,
                cmake=cmake,
                cxx=cxx,
                configure_args=(
                    argument for argument in configure[5:]
                    if not argument.startswith("-DCMAKE_CXX_FLAGS=")
                ),
            )
        _run_process(
            configure,
            timeout=CONFIGURE_TIMEOUT_S,
            label=f"configure {macro or 'stock'}",
        )
        _run_process(
            [cmake, "--build", build_dir, "--target", *target_list,
             "-j", str(jobs)],
            timeout=BUILD_TIMEOUT_S,
            label=f"build {macro or 'stock'}",
        )

    binaries: dict[str, str] = {}
    for target in target_list:
        binary = os.path.join(build_dir, "cc", "silo", target)
        if not os.path.isfile(binary) or not os.access(binary, os.X_OK):
            raise RuntimeError(f"built binary missing or not executable: {binary}")
        binaries[target] = binary
    return binaries


def _trace_summary(trace_dir: str) -> dict[str, Any]:
    reasons: dict[str, int] = {}
    write_ops: set[str] = set()
    lock_violations = 0
    permutation_violations = 0
    files = 0
    for name in sorted(os.listdir(trace_dir)):
        if not (name.startswith("trace_") and name.endswith(".log")):
            continue
        files += 1
        with open(os.path.join(trace_dir, name), encoding="utf-8",
                  errors="replace") as trace_file:
            for lineno, line in enumerate(trace_file, 1):
                fields = line.split()
                if not fields:
                    continue
                if fields[0] == "I":
                    if len(fields) != 4:
                        raise RuntimeError(f"{name}:{lineno}: malformed I line")
                    reason = fields[3]
                    reasons[reason] = reasons.get(reason, 0) + 1
                elif fields[0] == "X":
                    lock_violations += 1
                elif fields[0] == "P":
                    permutation_violations += 1
                elif fields[0] == "W":
                    if len(fields) != 6:
                        raise RuntimeError(f"{name}:{lineno}: malformed W line")
                    write_ops.add(fields[3])
    if files == 0:
        raise RuntimeError(f"no trace_*.log files produced in {trace_dir}")
    return {
        "files": files,
        "write_intent_total": sum(reasons.values()),
        "write_intent_reasons": dict(sorted(reasons.items())),
        "lock_coverage_violations": lock_violations,
        "permutation_violations": permutation_violations,
        "write_ops": sorted(write_ops),
    }


def _verify(trace_dir: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "verifier", trace_dir, "--json", "--quiet"],
        cwd=os.path.join(_repo_root(), "orchestrator"),
        capture_output=True,
        text=True,
        timeout=VERIFIER_TIMEOUT_S,
    )
    try:
        payload = json.loads(proc.stdout)
        result = payload["results"][0]
        integrity = result["integrity"]
        stats = result["stats"]
        return {
            "exit_code": proc.returncode,
            "verdict": result["verdict"],
            "certified": result["certified"],
            "serializable": result["serializable"],
            "total_cycles": result["total_cycles"],
            "txns": stats["txns"],
            "reads": stats["reads"],
            "writes": stats["writes"],
            "integrity": dict(integrity),
        }
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"verifier output is not usable (rc={proc.returncode}): "
            f"{proc.stdout[:300]} / {proc.stderr[-300:]}"
        ) from exc


def _stdout_count(pattern: re.Pattern[str], stdout: str, name: str) -> int:
    match = pattern.search(stdout or "")
    if match is None:
        raise RuntimeError(f"stdout does not contain {name} (fail-closed)")
    return int(match.group(1))


def _run_one(
    *,
    label: str,
    workload: str,
    binary: str,
    flags: dict[str, str],
    resources: contextlib.ExitStack,
) -> dict[str, Any]:
    trace_dir = resources.enter_context(
        tempfile.TemporaryDirectory(prefix=f"izanagi_t152_{label}_")
    )
    os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True)
    argv = [binary, *(f"-{key}={value}" for key, value in flags.items()),
            f"-clocks_per_us={CLK}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=trace_dir)
    proc = _run_process(
        argv,
        cwd=trace_dir,
        env=env,
        timeout=RUN_TIMEOUT_S,
        label=f"run {label}",
    )
    trace = _trace_summary(trace_dir)
    verifier = _verify(trace_dir)
    return {
        "workload": workload,
        "flags": dict(flags),
        "abort_exercised": (
            _stdout_count(_ABORT_RE, proc.stdout, "abort_counts_") > 0
        ),
        "trace": trace,
        "verifier": verifier,
    }


def _intent_reconciled(run: dict[str, Any]) -> bool:
    raw_count = run["trace"]["write_intent_total"]
    verifier = run["verifier"]
    expected_exit = 0 if raw_count == 0 else 3
    return (
        raw_count == verifier["integrity"]["write_intent_violations"]
        and verifier["exit_code"] == expected_exit
    )


def _integrity_counters_zero(
    integrity: dict[str, Any],
    *,
    except_write_intent: bool = False,
) -> bool:
    """Require every current/future integer integrity counter to be zero."""
    counters = {
        name: value for name, value in integrity.items()
        if name not in {
            "clean", "notes", "framing_violation_details",
            "permutation_violation_details",
        }
        and not (except_write_intent and name == "write_intent_violations")
    }
    return (
        "write_intent_violations" in integrity
        and bool(counters)
        and all(type(value) is int and value == 0 for value in counters.values())
    )


def _evaluate_checks(results: dict[str, dict[str, Any]]) -> dict[str, bool]:
    """Pure characterization predicates; no I/O, environment, or mutation."""
    stock = results["stock_single"]
    abort = results["stock_abort"]
    bomb = results["bomb_smoke"]
    erase = results["erase"]
    forge = results["forge"]
    opswap = results["opswap"]
    ptrswap = results["ptrswap"]

    st, sv = stock["trace"], stock["verifier"]
    at, av = abort["trace"], abort["verifier"]
    bt, bv = bomb["trace"], bomb["verifier"]
    et, ev = erase["trace"], erase["verifier"]
    ft, fv = forge["trace"], forge["verifier"]
    ot, ov = opswap["trace"], opswap["verifier"]
    pt, pv = ptrswap["trace"], ptrswap["verifier"]

    checks = {
        "stock_silent": (
            st["write_intent_total"] == 0
            and st["lock_coverage_violations"] == 0
            and st["permutation_violations"] == 0
            and _integrity_counters_zero(sv["integrity"])
            and sv["total_cycles"] == 0
            and sv["certified"]
            and sv["verdict"] == "serializable"
            and sv["txns"] > 0
            and sv["writes"] > 0
        ),
        "abort_exercised": (
            abort["abort_exercised"]
            and at["write_intent_total"] == 0
            and _integrity_counters_zero(av["integrity"])
            and av["certified"]
        ),
        "bomb_ops": (
            {"U", "I", "D"}.issubset(set(bt["write_ops"]))
            and bt["write_intent_total"] == 0
            and _integrity_counters_zero(bv["integrity"])
            and bv["certified"]
        ),
        "producer_union": (
            {"U", "I", "D"}.issubset(
                set(st["write_ops"])
                | set(at["write_ops"])
                | set(bt["write_ops"])
            )
        ),
        "erase": (
            et["write_intent_total"] > 0
            and set(et["write_intent_reasons"]) == {MISSING_REASON}
            and et["lock_coverage_violations"] == 0
            and et["permutation_violations"] == 0
            and _integrity_counters_zero(
                ev["integrity"], except_write_intent=True
            )
            and ev["total_cycles"] == 0
            and ev["verdict"] == "indeterminate"
            and not ev["certified"]
            and ev["exit_code"] == 3
        ),
        "forge": (
            ft["write_intent_total"] > 0
            and set(ft["write_intent_reasons"]) == {UNEXPECTED_REASON}
            and ft["lock_coverage_violations"] == 0
            and ft["permutation_violations"] == 0
            and _integrity_counters_zero(
                fv["integrity"], except_write_intent=True
            )
            and fv["total_cycles"] == 0
            and fv["verdict"] == "indeterminate"
            and not fv["certified"]
            and fv["exit_code"] == 3
        ),
        "opswap": (
            ot["write_intent_total"] >= 2
            and ot["write_intent_reasons"].get(MISSING_REASON, 0) > 0
            and ot["write_intent_reasons"].get(UNEXPECTED_REASON, 0) > 0
            and ot["lock_coverage_violations"] == 0
            and ot["permutation_violations"] == 0
            and _integrity_counters_zero(
                ov["integrity"], except_write_intent=True
            )
            and ov["total_cycles"] == 0
            and ov["verdict"] == "indeterminate"
            and not ov["certified"]
            and ov["exit_code"] == 3
        ),
        "ptrswap": (
            pt["write_intent_total"] >= 4
            and pt["write_intent_reasons"].get(MISSING_REASON, 0) >= 2
            and pt["write_intent_reasons"].get(UNEXPECTED_REASON, 0) >= 2
            and pt["lock_coverage_violations"] == 0
            and pt["permutation_violations"] == 0
            and _integrity_counters_zero(
                pv["integrity"], except_write_intent=True
            )
            and pv["total_cycles"] == 0
            and pv["verdict"] == "indeterminate"
            and not pv["certified"]
            and pv["exit_code"] == 3
        ),
        "three_way_reconciliation": all(
            _intent_reconciled(run) for run in results.values()
        ),
    }
    checks["all_pass"] = all(checks.values())
    return checks


def _publish_json(payload: dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(output_path),
            prefix=".t152_write_intent_coverage.",
            suffix=".tmp",
            delete=False,
        ) as output_file:
            temporary_path = output_file.name
            json.dump(payload, output_file, ensure_ascii=False, indent=2,
                      sort_keys=True)
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def _exit_code(all_pass: bool) -> int:
    """Map the final gate result to the process contract."""
    return 0 if all_pass else 1


def _make_payload(
    *,
    sha: str,
    cc_record: dict[str, str],
    cxx_record: dict[str, str],
    deps_record: dict[str, Any],
    linked_dependencies: dict[str, str],
    jobs: int,
    runs: dict[str, dict[str, Any]],
    condition_gates: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    evaluated = _evaluate_checks(runs)
    return {
        "schema_version": "t152-write-intent-coverage/v1",
        "platform": "pegasus",
        "host_role": "login-node",
        "fitness_eligible": False,
        "env_contract_applicable": False,
        "correctness_only": True,
        "not_integrated": True,
        "build_admission": non_admissible_materializer(
            "orchestrator.campaign.t152_write_intent_coverage._build"
        ),
        "ccbench_sha": sha,
        "toolchain": {"cc": cc_record, "cxx": cxx_record},
        "deps_prefix": deps_record,
        "build_jobs": jobs,
        "condition_gates": list(condition_gates),
        "runs_meta": {
            "cmake_cache_linked_dependencies": linked_dependencies,
            "performance_semantics": _PERFORMANCE_SEMANTICS,
        },
        "runs": runs,
        "checks": {
            name: passed for name, passed in evaluated.items()
            if name != "all_pass"
        },
        "all_pass": evaluated["all_pass"],
        "known_limitations": list(_KNOWN_LIMITATIONS),
    }


def _collect_payload() -> tuple[dict[str, Any], str]:
    raw_sha = os.environ.get("IZANAGI_T152_CCBENCH_SHA")
    if raw_sha is None or not raw_sha.strip():
        raise RuntimeError("IZANAGI_T152_CCBENCH_SHA is required (no default)")

    root = _repo_root()
    ccbench_base = os.path.join(root, "external", "ccbench")
    deps_record, cmake_prefix_path = _dependency_contract(
        os.environ.get("CMAKE_PREFIX_PATH")
    )
    cc_record = _tool_record(os.environ.get("IZANAGI_T152_CC", DEFAULT_CC), "cc")
    cxx_record = _tool_record(os.environ.get("IZANAGI_T152_CXX", DEFAULT_CXX), "cxx")
    cmake = _resolve_executable("cmake", "cmake")
    jobs = _jobs(os.environ.get("IZANAGI_T152_JOBS"))
    sha = _resolve_ccbench_sha(raw_sha.strip(), ccbench_base)

    with contextlib.ExitStack() as resources:
        temporary_root = resources.enter_context(
            tempfile.TemporaryDirectory(prefix="izanagi_t152_builds_")
        )
        condition_gates = _preflight_condition_gates(
            sha=sha,
            ccbench_base=ccbench_base,
            root=root,
            cmake=cmake,
            cc=cc_record["realpath"],
            cxx=cxx_record["realpath"],
            cmake_prefix_path=cmake_prefix_path,
        )
        stock_build_dir = os.path.join(temporary_root, "stock")
        stock_binaries = _build(
            sha=sha,
            ccbench_base=ccbench_base,
            build_dir=stock_build_dir,
            cmake=cmake,
            cc=cc_record["realpath"],
            cxx=cxx_record["realpath"],
            cmake_prefix_path=cmake_prefix_path,
            jobs=jobs,
            targets=("ycsb_silo.exe", "bomb_silo.exe"),
            record_dependency_links=True,
        )
        linked_dependencies = _linked_dependency_contract(
            stock_build_dir, deps_record
        )

        broken_binaries: dict[str, str] = {}
        for name, (patch_name, macro) in _PATCHES.items():
            built = _build(
                sha=sha,
                ccbench_base=ccbench_base,
                build_dir=os.path.join(temporary_root, name),
                cmake=cmake,
                cc=cc_record["realpath"],
                cxx=cxx_record["realpath"],
                cmake_prefix_path=cmake_prefix_path,
                jobs=jobs,
                targets=("ycsb_silo.exe",),
                patch_path=os.path.join(root, "patches", patch_name),
                macro=macro,
            )
            broken_binaries[name] = built["ycsb_silo.exe"]

        runs = {
            "stock_single": _run_one(
                label="stock_single",
                workload="ycsb",
                binary=stock_binaries["ycsb_silo.exe"],
                flags=_YCSB_SINGLE_FLAGS,
                resources=resources,
            ),
            "stock_abort": _run_one(
                label="stock_abort",
                workload="ycsb",
                binary=stock_binaries["ycsb_silo.exe"],
                flags=_YCSB_ABORT_FLAGS,
                resources=resources,
            ),
            "bomb_smoke": _run_one(
                label="bomb_smoke",
                workload="bomb",
                binary=stock_binaries["bomb_silo.exe"],
                flags=_BOMB_FLAGS,
                resources=resources,
            ),
        }
        for name in ("erase", "forge", "opswap", "ptrswap"):
            runs[name] = _run_one(
                label=name,
                workload="ycsb",
                binary=broken_binaries[name],
                flags=_YCSB_SINGLE_FLAGS,
                resources=resources,
            )

        payload = _make_payload(
            sha=sha,
            cc_record=cc_record,
            cxx_record=cxx_record,
            deps_record=deps_record,
            linked_dependencies=linked_dependencies,
            jobs=jobs,
            runs=runs,
            condition_gates=condition_gates,
        )
        output_path = os.path.join(
            repo_output_root(),
            "env", "pegasus", "characterization",
            "t152_write_intent_coverage.json",
        )

    return payload, output_path


def main() -> int:
    payload, output_path = _collect_payload()
    _publish_json(payload, output_path)

    for name, passed in payload["checks"].items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"all_pass={payload['all_pass']} -> {output_path}")
    return _exit_code(payload["all_pass"])


def _entrypoint() -> int:
    try:
        return main()
    except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(_entrypoint())
