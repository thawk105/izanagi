#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mocc lock-coverage and permutation positive-control driver.

This is a correctness-only diagnostic.  Every source variant is built in a
fresh checkout of the trace-hook commit, and every mutation build is explicitly
non-admissible for campaign selection.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from itertools import zip_longest
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import condition_meaning_gate, site_policy  # noqa: E402
from .materializer_admission import non_admissible_materializer  # noqa: E402
from .model import Genome  # noqa: E402
from .p2_2 import _assert_single_tenant  # noqa: E402
from .patchharness import (  # noqa: E402
    apply_patch,
    assert_pinned_clean,
    checkout,
    patch_files,
)
from .toolchain_binding import tool_version_body  # noqa: E402


PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
SOURCE_REL = "cc/mocc/transaction.cc"
ENV_TAG = "pegasus"
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 300.0
CLK = 2100

STOCK_G = Genome(
    "mocc", {"BACK_OFF": 1, "KEY_SORT": 0, "TEMPERATURE_RESET_OPT": 1},
)
SINGLE_FLAGS = {
    "ycsb_tuple_num": "200",
    "ycsb_zipf_skew": "0.9",
    "ycsb_rratio": "0",
    "ycsb_rmw": "true",
    "ycsb_max_ope": "5",
    "thread_num": "1",
    "extime": "1",
}
HIGH_FLAGS = {**SINGLE_FLAGS, "thread_num": "4"}

INSTRUMENTATION_PATCH = "patches/instr-mocc-lock-coverage.patch"
LOCKSKIP_PATCH = "patches/broken-mocc-lockskip-validation.patch"
PERMUTATION_PATCH = "patches/broken-mocc-permutation-erase.patch"
EARLY_UNLOCK_PATCH = "patches/broken-mocc-early-unlock.patch"
LOCKSKIP_DEFINE = "IZANAGI_BREAK_MOCC_LOCK_COVERAGE"
PERMUTATION_DEFINE = "IZANAGI_BREAK_MOCC_PERMUTATION"
EARLY_UNLOCK_DEFINE = "IZANAGI_BREAK_MOCC_EARLY_UNLOCK"

CHECK_KEYS = (
    "stock_single_certified_and_silent",
    "stock_single_non_insert_writes_positive",
    "stock_high_xp_silent",
    "stock_high_non_insert_writes_positive",
    "lockskip_single_cycles_zero_x_positive",
    "lockskip_single_both_entry_and_retention_reasons",
    "lockskip_high_x_positive",
    "perm_single_only_size_changed",
    "early_unlock_single_retention_reasons_without_entry",
    "trace0_nm_izanagi_zero",
    "trace0_strings_izanagi_trace_zero",
    "trace0_text_identical",
    "all_patch_touch_sets_are_transaction_only",
    "toolchain_matches_policy",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_checked(
    argv: Sequence[str], *, cwd: Path | None = None, timeout: float = 300.0,
    allowed_returncodes: frozenset[int] = frozenset({0}),
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(argv), cwd=os.fspath(cwd) if cwd is not None else None,
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"command could not be executed: {list(argv)!r}") from exc
    if completed.returncode not in allowed_returncodes:
        raise RuntimeError(
            f"command rc={completed.returncode}: {list(argv)!r}; "
            f"stderr={completed.stderr[-500:]!r}"
        )
    return completed


def _load_policy(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs):
        document = {}
        for key, value in pairs:
            if key in document:
                raise ValueError(f"duplicate policy key: {key}")
            document[key] = value
        return document

    with path.open(encoding="utf-8") as handle:
        policy = json.load(handle, object_pairs_hook=reject_duplicates)
    expected = policy.get("expected_compiler_version_body_sha256")
    if type(expected) is not dict or set(expected) != {"gcc", "g++"}:
        raise RuntimeError("policy compiler digest mapping differs")
    if any(
        type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in expected.values()
    ):
        raise RuntimeError("policy compiler digest is invalid")
    trace = policy.get("mocc_trace")
    if type(trace) is not dict or trace.get("new_oid") != PIN:
        raise RuntimeError("policy mocc trace commit differs")
    if trace.get("cmake_target") != "ycsb_mocc.exe":
        raise RuntimeError("policy mocc target differs")
    return policy


def _resolve_toolchain(policy: Mapping[str, Any]) -> dict[str, Any]:
    expected = policy["expected_compiler_version_body_sha256"]
    result: dict[str, Any] = {"version_body_sha256": {}}
    for role, output_key in (("gcc", "cc_path"), ("g++", "cxx_path")):
        candidate = shutil.which(role)
        if candidate is None:
            raise RuntimeError(f"compiler is unavailable: {role}")
        path = Path(candidate).resolve(strict=True)
        version = _run_checked([os.fspath(path), "--version"]).stdout
        observed = hashlib.sha256(
            tool_version_body(version).encode("utf-8")
        ).hexdigest()
        if observed != expected[role]:
            raise RuntimeError(
                f"{role} version body mismatch: expected={expected[role]} "
                f"observed={observed}"
            )
        result[output_key] = os.fspath(path)
        result["version_body_sha256"][role] = observed
    return result


def _assert_dependency_source(
    path_value: object, expected_head: object, name: str,
) -> Path:
    if type(path_value) is not str or type(expected_head) is not str:
        raise RuntimeError(f"policy {name} source binding is invalid")
    path = Path(path_value).resolve(strict=True)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is unavailable")
    head = _run_checked([git, "-C", os.fspath(path), "rev-parse", "HEAD"]).stdout.strip()
    if head != expected_head:
        raise RuntimeError(f"{name} source HEAD mismatch")
    status = _run_checked([
        git, "-C", os.fspath(path), "status", "--porcelain",
        "--untracked-files=all",
    ]).stdout
    if status:
        raise RuntimeError(f"{name} source is dirty")
    return path


def _install_dependency(
    name: str, source: Path, scratch: Path, toolchain: Mapping[str, Any],
    *, gflags_prefix: Path | None = None,
) -> Path:
    build = scratch / f"{name}-build"
    install = scratch / f"{name}-install"
    configure = [
        "cmake", "-S", os.fspath(source), "-B", os.fspath(build),
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        f"-DCMAKE_INSTALL_PREFIX={install}",
        f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=",
    ]
    if name == "gflags":
        configure.append("-DREGISTER_INSTALL_PREFIX=OFF")
    elif name == "glog":
        if gflags_prefix is None:
            raise RuntimeError("glog requires the gflags install prefix")
        configure.extend([
            "-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF", "-DWITH_UNWIND=OFF",
            f"-DCMAKE_PREFIX_PATH={gflags_prefix}",
        ])
    else:
        raise RuntimeError(f"unsupported dependency: {name}")
    _run_checked(configure)
    jobs = site_policy.default_build_jobs(site_policy.current_site())
    _run_checked(["cmake", "--build", os.fspath(build), "-j", str(jobs)])
    _run_checked(["cmake", "--install", os.fspath(build)])
    return install


def _prepare_dependencies(
    root: Path, policy: Mapping[str, Any], cache_root: Path, scratch: Path,
    toolchain: Mapping[str, Any],
) -> dict[str, Path]:
    staging = scratch / "thirdparty-src"
    hydrate = _run_checked([
        sys.executable, os.fspath(root / "tools" / "pegasus" / "fetch_third_party.py"),
        "hydrate", "--repo-root", os.fspath(root), "--cache-root",
        os.fspath(cache_root), "--staging-root", os.fspath(staging),
    ], timeout=120.0)
    payload = json.loads(hydrate.stdout)
    source_root_value = payload.get("source_root")
    if type(source_root_value) is not str or not os.path.isabs(source_root_value):
        raise RuntimeError("hydrate source_root is not absolute")
    source_root = Path(source_root_value).resolve(strict=True)
    gflags_source = _assert_dependency_source(
        os.fspath(source_root / "gflags"), policy.get("gflags_expected_head"), "gflags",
    )
    glog_source = _assert_dependency_source(
        os.fspath(source_root / "glog"), policy.get("glog_expected_head"), "glog",
    )
    gflags = _install_dependency("gflags", gflags_source, scratch, toolchain)
    glog = _install_dependency(
        "glog", glog_source, scratch, toolchain, gflags_prefix=gflags,
    )
    dependencies = {name: source_root / name for name in (
        "masstree", "mimalloc", "googletest",
    )}
    if any(not path.is_dir() for path in dependencies.values()):
        raise RuntimeError("hydrated dependency source set is incomplete")
    return {**dependencies, "gflags": gflags, "glog": glog}


def _common_configure_args(
    *, trace: int, toolchain: Mapping[str, Any], dependencies: Mapping[str, Path],
) -> list[str]:
    return [
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        "-DCCBENCH_CCACHE=OFF", f"-DCCBENCH_TRACE={trace}",
        *STOCK_G.cmake_defines(),
        f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DCMAKE_TOOLCHAIN_FILE=",
        f"-DCMAKE_PREFIX_PATH={dependencies['gflags']};{dependencies['glog']}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={dependencies['masstree']}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={dependencies['mimalloc']}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={dependencies['googletest']}",
    ]


def _require_condition_gate(
    source_root: Path, macro: str | None, configure_args: Sequence[str], cxx: str,
) -> dict[str, Any] | None:
    if macro is None:
        return None
    captured = condition_meaning_gate.capture_define_inputs(
        source_root, configure_args=tuple(configure_args),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.s3_mocc_lock_coverage",
        macro=macro, requested_value=1, default_value=0,
    )
    with condition_meaning_gate._configured_define_compile_commands(
        captured, request=request, cxx=cxx, cmake="cmake",
    ) as configured_commands:
        supply = condition_meaning_gate.evaluate_define_supply_effectuation(
            captured, request=request, cxx=cxx, cmake="cmake",
            configured_commands=configured_commands,
        )
        meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
            captured, request=request,
            declaration=condition_meaning_gate.declare_define_runtime_meaning(request),
            cxx=cxx, cmake="cmake", configured_commands=configured_commands,
        )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    if not admission.admitted:
        raise RuntimeError(
            f"condition gate rejected {macro}: "
            f"{supply.terminal_status}/{meaning.terminal_status}"
        )
    return {
        "macro": macro,
        "supply": json.loads(supply.canonical_json()),
        "meaning": json.loads(meaning.canonical_json()),
        "admission": json.loads(admission.canonical_json()),
    }


def _build_variant(
    source_root: Path, build_root: Path, *, trace: int,
    toolchain: Mapping[str, Any], dependencies: Mapping[str, Path],
    macro: str | None = None,
) -> tuple[Path, dict[str, Any] | None]:
    configure_args = _common_configure_args(
        trace=trace, toolchain=toolchain, dependencies=dependencies,
    )
    gate = _require_condition_gate(
        source_root, macro, configure_args, str(toolchain["cxx_path"]),
    )
    if macro is not None:
        configure_args.append(f"-DCMAKE_CXX_FLAGS=-D{macro}=1")
    configure = [
        "cmake", "-S", os.fspath(source_root), "-B", os.fspath(build_root),
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}", *configure_args,
    ]
    _run_checked(configure)
    jobs = site_policy.default_build_jobs(site_policy.current_site())
    _run_checked([
        "cmake", "--build", os.fspath(build_root), "--target", "ycsb_mocc.exe",
        "-j", str(jobs),
    ], timeout=900.0)
    binary = build_root / "cc" / "mocc" / "ycsb_mocc.exe"
    if not binary.is_file():
        raise RuntimeError("mocc build did not produce ycsb_mocc.exe")
    return binary, gate


def _run_trace(binary: Path, flags: Mapping[str, str]) -> Path:
    trace_dir = Path(tempfile.mkdtemp(prefix="izanagi_s3_mocc_trace_"))
    args = [
        os.fspath(binary), *(f"-{key}={value}" for key, value in flags.items()),
        f"-clocks_per_us={CLK}",
    ]
    env = dict(os.environ, IZANAGI_TRACE_DIR=os.fspath(trace_dir))
    try:
        completed = subprocess.run(
            args, cwd=os.fspath(trace_dir), env=env, capture_output=True,
            text=True, timeout=RUN_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        shutil.rmtree(trace_dir, ignore_errors=True)
        raise
    if completed.returncode != 0:
        shutil.rmtree(trace_dir, ignore_errors=True)
        raise RuntimeError(
            f"mocc run rc={completed.returncode}: {completed.stderr[-500:]!r}"
        )
    return trace_dir


def _trace_counts(trace_dir: Path) -> dict[str, Any]:
    x_reasons: dict[str, int] = {}
    p_reasons: dict[str, int] = {}
    non_insert_writes = 0
    for path in sorted(trace_dir.glob("trace_*.log")):
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == "X":
                    x_reasons[parts[3]] = x_reasons.get(parts[3], 0) + 1
                elif len(parts) >= 2 and parts[0] == "P":
                    p_reasons[parts[1]] = p_reasons.get(parts[1], 0) + 1
                elif len(parts) >= 4 and parts[0] == "W" and parts[3] != "I":
                    non_insert_writes += 1
    return {
        "x_reasons": x_reasons,
        "p_reasons": p_reasons,
        "non_insert_writes": non_insert_writes,
    }


def _verify(trace_dir: Path, ccbench_root: Path) -> tuple[dict[str, Any], bool]:
    completed = _run_checked([
        sys.executable, "-m", "verifier", os.fspath(trace_dir), "--json", "--quiet",
        "--protocol", "mocc", "--ccbench-root", os.fspath(ccbench_root),
    ], cwd=_repo_root() / "orchestrator", timeout=VERIFIER_TIMEOUT_S,
        allowed_returncodes=frozenset({0, 1, 3}))
    try:
        record = json.loads(completed.stdout)["results"][0]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("verifier output is not a result record") from exc
    integrity = record["integrity"]
    other_integrity_clean = all(
        integrity.get(key) in (0, [], {})
        for key in (
            "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
            "missing_txids", "write_version_mismatch", "malformed_keys",
            "framing_violations", "framing_violation_details",
            "write_intent_violations",
        )
    )
    return {
        "verdict": record["verdict"],
        "certified": record["certified"],
        "total_cycles": record["total_cycles"],
        "lock_coverage_violations": integrity["lock_coverage_violations"],
        "permutation_violations": integrity["permutation_violations"],
        "txns": record["stats"]["txns"],
    }, other_integrity_clean


def _variant_run(binary: Path, flags: Mapping[str, str], source_root: Path) -> dict[str, Any]:
    _assert_single_tenant()
    trace_dir = _run_trace(binary, flags)
    try:
        verified, other_integrity_clean = _verify(trace_dir, source_root)
        return {
            **verified, **_trace_counts(trace_dir),
            "_other_integrity_clean": other_integrity_clean,
        }
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def _apply_owned_patch(root: Path, source_root: Path, relative: str) -> list[str]:
    patch = root / relative
    touched = patch_files(os.fspath(patch), os.fspath(source_root))
    if touched != [SOURCE_REL]:
        raise RuntimeError(f"patch touch set differs for {relative}: {touched!r}")
    apply_patch(os.fspath(patch), os.fspath(source_root))
    return touched


def _normalize_objdump(text: str) -> str:
    instructions = re.sub(r"(?m)^ *[0-9a-f]+:", "", text)
    return re.sub(r"(?m)^ *[0-9a-f]+(?= <.*>:$)", "", instructions)


def _trace0_record(base_binary: Path, patched_binary: Path) -> dict[str, Any]:
    base_nm = _run_checked(["nm", "-C", os.fspath(base_binary)]).stdout
    patched_nm = _run_checked(["nm", "-C", os.fspath(patched_binary)]).stdout
    base_strings = _run_checked(["strings", "-a", os.fspath(base_binary)]).stdout
    patched_strings = _run_checked([
        "strings", "-a", os.fspath(patched_binary),
    ]).stdout
    base_text = _normalize_objdump(_run_checked([
        "objdump", "-d", "--no-show-raw-insn", f"./{base_binary.name}",
    ], cwd=base_binary.parent).stdout)
    patched_text = _normalize_objdump(_run_checked([
        "objdump", "-d", "--no-show-raw-insn", f"./{patched_binary.name}",
    ], cwd=patched_binary.parent).stdout)
    text_diff_lines = sum(
        left != right
        for left, right in zip_longest(
            base_text.splitlines(), patched_text.splitlines(), fillvalue=None,
        )
    )
    return {
        "base_binary_sha256": _sha256_file(base_binary),
        "patched_binary_sha256": _sha256_file(patched_binary),
        "nm_izanagi_count": sum(
            "izanagi" in line
            for output in (base_nm, patched_nm)
            for line in output.splitlines()
        ),
        "strings_izanagi_trace_count": sum(
            "izanagi_trace" in line
            for output in (base_strings, patched_strings)
            for line in output.splitlines()
        ),
        "strings_izanagi_macro_count": sum(
            "IZANAGI_" in line
            for output in (base_strings, patched_strings)
            for line in output.splitlines()
        ),
        "text_identical": base_text == patched_text,
        "text_diff_lines": text_diff_lines,
        "text_diff_preview": list(difflib.unified_diff(
            base_text.splitlines(), patched_text.splitlines(), n=1,
        ))[:20],
    }


def _public_run_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def compute_checks(
    runs: Mapping[str, Mapping[str, Any]],
    trace0: Mapping[str, Any],
    touch_sets: Mapping[str, Sequence[str]],
    patch_relatives: Sequence[str],
    toolchain: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, bool]:
    """Derive the complete acceptance record from captured observations."""
    stock_single = runs["stock_single"]
    stock_high = runs["stock_high"]
    lockskip_single = runs["lockskip_single"]
    lockskip_high = runs["lockskip_high"]
    perm_single = runs["perm_erase_single"]
    early = runs["early_unlock_single"]
    observed_compilers = toolchain.get("version_body_sha256")
    expected_compilers = policy.get("expected_compiler_version_body_sha256")
    toolchain_matches_policy = (
        isinstance(observed_compilers, Mapping)
        and isinstance(expected_compilers, Mapping)
        and set(observed_compilers) == {"gcc", "g++"}
        and set(expected_compilers) == {"gcc", "g++"}
        and all(
            observed_compilers[role] == expected_compilers[role]
            for role in ("gcc", "g++")
        )
    )
    checks = {
        "stock_single_certified_and_silent": (
            stock_single["certified"]
            and stock_single["verdict"] == "serializable"
            and stock_single["total_cycles"] == 0
            and stock_single["lock_coverage_violations"] == 0
            and stock_single["permutation_violations"] == 0
            and stock_single["txns"] > 0
            and stock_single["_other_integrity_clean"]
        ),
        "stock_single_non_insert_writes_positive": (
            stock_single["non_insert_writes"] > 0
        ),
        "stock_high_xp_silent": (
            stock_high["lock_coverage_violations"] == 0
            and stock_high["permutation_violations"] == 0
            and stock_high["txns"] > 0
            and stock_high["_other_integrity_clean"]
        ),
        "stock_high_non_insert_writes_positive": (
            stock_high["non_insert_writes"] > 0
        ),
        "lockskip_single_cycles_zero_x_positive": (
            lockskip_single["total_cycles"] == 0
            and lockskip_single["lock_coverage_violations"] > 0
            and lockskip_single["txns"] > 0
            and lockskip_single["verdict"] == "indeterminate"
        ),
        "lockskip_single_both_entry_and_retention_reasons": all(
            lockskip_single["x_reasons"].get(reason, 0) > 0
            for reason in (
                "not-locked-at-entry", "lock-lost-before-write",
                "lock-lost-before-publish",
            )
        ),
        "lockskip_high_x_positive": (
            lockskip_high["lock_coverage_violations"] > 0
        ),
        "perm_single_only_size_changed": (
            perm_single["total_cycles"] == 0
            and perm_single["lock_coverage_violations"] == 0
            and perm_single["permutation_violations"] > 0
            and perm_single["p_reasons"] == {"size-changed": perm_single[
                "permutation_violations"
            ]}
            and perm_single["txns"] > 0
            and perm_single["verdict"] == "indeterminate"
        ),
        "early_unlock_single_retention_reasons_without_entry": (
            early["total_cycles"] == 0
            and early["lock_coverage_violations"] > 0
            and early["txns"] > 0
            and early["verdict"] == "indeterminate"
            and early["x_reasons"].get("not-locked-at-entry", 0) == 0
            and early["x_reasons"].get("lock-lost-before-write", 0) > 0
            and early["x_reasons"].get("lock-lost-before-publish", 0) > 0
        ),
        "trace0_nm_izanagi_zero": trace0["nm_izanagi_count"] == 0,
        "trace0_strings_izanagi_trace_zero": (
            trace0["strings_izanagi_trace_count"] == 0
            and trace0["strings_izanagi_macro_count"] == 0
        ),
        "trace0_text_identical": trace0["text_identical"],
        "all_patch_touch_sets_are_transaction_only": (
            set(touch_sets) == set(patch_relatives)
            and all(files == [SOURCE_REL] for files in touch_sets.values())
        ),
        "toolchain_matches_policy": toolchain_matches_policy,
    }
    if tuple(checks) != CHECK_KEYS:
        raise RuntimeError("driver check key order/set differs from CHECK_KEYS")
    return {key: bool(value) for key, value in checks.items()}


CANDIDATE_PATCH = "patches/instr-mocc-lock-coverage-pin-candidate.patch"
CANDIDATE_OUTPUT = "output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json"


def _candidate_oid(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise argparse.ArgumentTypeError("candidate OID must be 40 lowercase hex digits")
    return value


def _candidate_identity(
    oid: str, resolved: str, parent_line: str, raw_diff: str, tree: str,
    reconstructed_blob: str,
) -> dict[str, Any]:
    """Validate captured Git output without running Git or touching files."""
    _candidate_oid(oid)
    if resolved.strip() != oid:
        raise RuntimeError("candidate commit resolution differs")
    if parent_line.split() != [oid, PIN]:
        raise RuntimeError("candidate must have exactly the base parent")
    rows = raw_diff.splitlines()
    match = re.fullmatch(
        r":100644 100644 ([0-9a-f]{40}) ([0-9a-f]{40}) M\t"
        + re.escape(SOURCE_REL), rows[0] if len(rows) == 1 else "",
    )
    if match is None:
        raise RuntimeError("candidate raw diff must modify only transaction.cc without mode change")
    base_blob, candidate_blob = match.groups()
    if reconstructed_blob != candidate_blob:
        raise RuntimeError("candidate reconstructed blob differs")
    if re.fullmatch(r"[0-9a-f]{40}", tree.strip()) is None:
        raise RuntimeError("candidate tree is invalid")
    return {
        "oid": oid, "parents": [PIN], "tree": tree.strip(),
        "raw_diff": rows, "base_blob": base_blob,
        "candidate_blob": candidate_blob, "reconstructed_blob": reconstructed_blob,
    }


def _capture_candidate(root: Path, oid: str) -> tuple[dict[str, Any], list[str]]:
    _candidate_oid(oid)
    base_repo = root / "external" / "ccbench"

    def git(*arguments: str) -> str:
        return _run_checked(["git", "-C", os.fspath(base_repo), *arguments]).stdout

    resolved = git("rev-parse", "--verify", f"{oid}^{{commit}}")
    parents = git("rev-list", "--parents", "-n", "1", oid)
    raw_diff = git("diff-tree", "-r", "--raw", "--no-renames", "--no-abbrev", PIN, oid)
    tree = git("rev-parse", "--verify", f"{oid}^{{tree}}")
    with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
        assert_pinned_clean(source_value, PIN)
        source = Path(source_value)
        touched = _apply_owned_patch(root, source, CANDIDATE_PATCH)
        blob = _run_checked([
            "git", "-C", source_value, "hash-object", "--no-filters", SOURCE_REL,
        ]).stdout.strip()
        record = _candidate_identity(oid, resolved, parents, raw_diff, tree, blob)
        record["candidate_source_sha256"] = _sha256_file(source / SOURCE_REL)
    record["patch"] = {"path": CANDIDATE_PATCH, "sha256": _sha256_file(root / CANDIDATE_PATCH)}
    return record, touched


def _candidate_main(root: Path, args: argparse.Namespace, site: str) -> int:
    legacy_dir = root / "output/env/pegasus/calibration"
    for name in ("s3_mocc_lock_coverage.json", "s3_mocc_mutation_proof.json",
                 "s3_mocc_template_proof.json"):
        old = legacy_dir / name
        if args.out.resolve() == old.resolve() or (
            args.out.exists() and old.exists() and args.out.samefile(old)
        ):
            raise RuntimeError("candidate output must not overwrite legacy JSON")
    if not args.third_party_cache.is_absolute():
        raise RuntimeError("--third-party-cache must be absolute")
    candidate, touched = _capture_candidate(root, args.candidate_oid)
    policy_path = args.policy.resolve(strict=True)
    policy = _load_policy(policy_path)
    toolchain = _resolve_toolchain(policy)
    patch_relatives = (CANDIDATE_PATCH, LOCKSKIP_PATCH, PERMUTATION_PATCH, EARLY_UNLOCK_PATCH)
    patch_records = {
        name: {"path": relative, "sha256": _sha256_file(root / relative)}
        for name, relative in zip(
            ("instrumentation", "lockskip", "permutation_erase", "early_unlock"),
            patch_relatives,
        )
    }
    touch_sets = {CANDIDATE_PATCH: touched}
    runs: dict[str, dict[str, Any]] = {}
    condition_gates = []
    base_repo = root / "external" / "ccbench"
    with tempfile.TemporaryDirectory(prefix="izanagi_s3_mocc_candidate_") as temporary:
        scratch = Path(temporary)
        dependencies = _prepare_dependencies(root, policy, args.third_party_cache, scratch, toolchain)
        for label, broken_patch, macro, workloads in (
            ("stock", None, None, (("stock_single", SINGLE_FLAGS), ("stock_high", HIGH_FLAGS))),
            ("lockskip", LOCKSKIP_PATCH, LOCKSKIP_DEFINE, (
                ("lockskip_single", SINGLE_FLAGS), ("lockskip_high", HIGH_FLAGS))),
            ("perm", PERMUTATION_PATCH, PERMUTATION_DEFINE, (("perm_erase_single", SINGLE_FLAGS),)),
            ("early", EARLY_UNLOCK_PATCH, EARLY_UNLOCK_DEFINE, (("early_unlock_single", SINGLE_FLAGS),)),
        ):
            with checkout(args.candidate_oid, base_dir=os.fspath(base_repo)) as source_value:
                source = Path(source_value)
                assert_pinned_clean(source_value, args.candidate_oid)
                if broken_patch is not None:
                    touch_sets[broken_patch] = _apply_owned_patch(root, source, broken_patch)
                binary, gate = _build_variant(
                    source, scratch / f"{label}-trace1", trace=1,
                    toolchain=toolchain, dependencies=dependencies, macro=macro,
                )
                if macro is not None:
                    if gate is None:
                        raise RuntimeError(f"condition gate missing for {macro}")
                    condition_gates.append(gate)
                for run_name, flags in workloads:
                    runs[run_name] = _variant_run(binary, flags, source)
        binaries = []
        for oid, build_dir in ((PIN, scratch / "trace0-pin0"),
                               (args.candidate_oid, scratch / "trace0-cand")):
            with checkout(oid, base_dir=os.fspath(base_repo)) as source_value:
                assert_pinned_clean(source_value, oid)
                binary, _gate = _build_variant(
                    Path(source_value), build_dir, trace=0,
                    toolchain=toolchain, dependencies=dependencies,
                )
                binaries.append(binary)
        trace0 = _trace0_record(*binaries)
        checks = compute_checks(runs, trace0, touch_sets, patch_relatives, toolchain, policy)
        result = {
            "schema_version": "s3-mocc-xp-pin-candidate/v1",
            "env_tag": ENV_TAG, "site": site, "ccbench_commit": args.candidate_oid,
            "base_commit": PIN, "candidate": candidate,
            "genome": STOCK_G.canonical(), "clocks_per_us": CLK,
            "toolchain": toolchain,
            "policy": {"path": os.fspath(args.policy), "sha256": _sha256_file(policy_path)},
            "patches": patch_records,
            "workloads": {"single": SINGLE_FLAGS, "high": HIGH_FLAGS},
            "condition_gates": condition_gates,
            "diagnostic_build_admission": non_admissible_materializer(
                "orchestrator.campaign.s3_mocc_lock_coverage._build_variant"
            ),
            "trace0": trace0,
            "runs": {name: {**_public_run_record(record),
                            "other_integrity_clean": record["_other_integrity_clean"]}
                     for name, record in runs.items()},
            "checks": checks, "all_pass": all(checks.values()),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"all_pass={result['all_pass']} -> {args.out}")
    return 0 if result["all_pass"] else 1


def _parser(root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument(
        "--policy", type=Path,
        default=root / "tools" / "pegasus" / "mocc_trace_v1_policy.json",
    )
    parser.add_argument(
        "--out", type=Path,
        default=root / "output" / "env" / "pegasus" / "calibration"
        / "s3_mocc_lock_coverage.json",
    )
    parser.add_argument("--candidate-oid", type=_candidate_oid)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        print(site_policy.heavy_work_refusal(site, "mocc lock coverage driver"), file=sys.stderr)
        return 2
    _assert_single_tenant()
    root = _repo_root()
    args = _parser(root).parse_args(argv)
    if args.candidate_oid is not None:
        parser = _parser(root)
        parser.set_defaults(out=root / CANDIDATE_OUTPUT)
        return _candidate_main(root, parser.parse_args(argv), site)
    if not args.third_party_cache.is_absolute():
        raise RuntimeError("--third-party-cache must be absolute")
    policy = _load_policy(args.policy.resolve(strict=True))
    toolchain = _resolve_toolchain(policy)

    patch_relatives = (
        INSTRUMENTATION_PATCH, LOCKSKIP_PATCH, PERMUTATION_PATCH, EARLY_UNLOCK_PATCH,
    )
    patch_records = {
        name: {
            "path": relative,
            "sha256": _sha256_file(root / relative),
        }
        for name, relative in (
            ("instrumentation", INSTRUMENTATION_PATCH),
            ("lockskip", LOCKSKIP_PATCH),
            ("permutation_erase", PERMUTATION_PATCH),
            ("early_unlock", EARLY_UNLOCK_PATCH),
        )
    }
    touch_sets: dict[str, list[str]] = {}
    condition_gates: list[dict[str, Any]] = []
    runs: dict[str, dict[str, Any]] = {}

    with tempfile.TemporaryDirectory(prefix="izanagi_s3_mocc_") as temporary:
        scratch = Path(temporary)
        dependencies = _prepare_dependencies(
            root, policy, args.third_party_cache, scratch, toolchain,
        )
        base_repo = root / "external" / "ccbench"

        with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
            source = Path(source_value)
            assert_pinned_clean(source_value, PIN)
            touch_sets[INSTRUMENTATION_PATCH] = _apply_owned_patch(
                root, source, INSTRUMENTATION_PATCH,
            )
            binary, _gate = _build_variant(
                source, scratch / "stock-trace1", trace=1,
                toolchain=toolchain, dependencies=dependencies,
            )
            runs["stock_single"] = _variant_run(binary, SINGLE_FLAGS, source)
            runs["stock_high"] = _variant_run(binary, HIGH_FLAGS, source)

        for label, broken_patch, macro, workloads in (
            ("lockskip", LOCKSKIP_PATCH, LOCKSKIP_DEFINE, (
                ("lockskip_single", SINGLE_FLAGS), ("lockskip_high", HIGH_FLAGS),
            )),
            ("perm", PERMUTATION_PATCH, PERMUTATION_DEFINE, (
                ("perm_erase_single", SINGLE_FLAGS),
            )),
            ("early", EARLY_UNLOCK_PATCH, EARLY_UNLOCK_DEFINE, (
                ("early_unlock_single", SINGLE_FLAGS),
            )),
        ):
            with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
                source = Path(source_value)
                assert_pinned_clean(source_value, PIN)
                _apply_owned_patch(root, source, INSTRUMENTATION_PATCH)
                touch_sets[broken_patch] = _apply_owned_patch(root, source, broken_patch)
                binary, gate = _build_variant(
                    source, scratch / f"{label}-trace1", trace=1,
                    toolchain=toolchain, dependencies=dependencies, macro=macro,
                )
                if gate is None:
                    raise RuntimeError(f"condition gate missing for {macro}")
                condition_gates.append(gate)
                for run_name, flags in workloads:
                    runs[run_name] = _variant_run(binary, flags, source)

        # Equal-length build names avoid observed __FILE__ path drift in .text.
        with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
            assert_pinned_clean(source_value, PIN)
            trace0_base, _gate = _build_variant(
                Path(source_value), scratch / "trace0-base", trace=0,
                toolchain=toolchain, dependencies=dependencies,
            )
        with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
            source = Path(source_value)
            assert_pinned_clean(source_value, PIN)
            _apply_owned_patch(root, source, INSTRUMENTATION_PATCH)
            trace0_patched, _gate = _build_variant(
                source, scratch / "trace0-inst", trace=0,
                toolchain=toolchain, dependencies=dependencies,
            )
        trace0 = _trace0_record(trace0_base, trace0_patched)

        checks = compute_checks(
            runs, trace0, touch_sets, patch_relatives, toolchain, policy,
        )
        result = {
            "schema_version": "s3-mocc-lock-coverage/v1",
            "env_tag": ENV_TAG,
            "site": site,
            "ccbench_commit": PIN,
            "genome": STOCK_G.canonical(),
            "clocks_per_us": CLK,
            "toolchain": toolchain,
            "patches": patch_records,
            "workloads": {"single": SINGLE_FLAGS, "high": HIGH_FLAGS},
            "condition_gates": condition_gates,
            "diagnostic_build_admission": non_admissible_materializer(
                "orchestrator.campaign.s3_mocc_lock_coverage._build_variant"
            ),
            "trace0": trace0,
            "runs": {name: _public_run_record(record) for name, record in runs.items()},
            "checks": checks,
            "all_pass": all(checks.values()),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    print(f"all_pass={result['all_pass']} -> {args.out}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
