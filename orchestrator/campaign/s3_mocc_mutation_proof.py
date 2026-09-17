#!/usr/bin/env python3
"""Fixed-producer MOCC mutation proof: 36 correctness runs, no performance use."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import s3_mocc_lock_coverage as legacy
from . import condition_meaning_gate, site_policy
from .materializer_admission import non_admissible_materializer
from .p2_2 import _assert_single_tenant
from .patchharness import assert_pinned_clean, checkout

PIN = legacy.PIN
SOURCE_REL = legacy.SOURCE_REL
STOCK_G = legacy.STOCK_G
SINGLE_FLAGS = dict(legacy.SINGLE_FLAGS)
HIGH_FLAGS = dict(legacy.HIGH_FLAGS)
U_SINGLE_FLAGS = {**SINGLE_FLAGS, "ycsb_rmw": "false", "ycsb_max_ope": "1"}
U_HIGH_FLAGS = {**HIGH_FLAGS, "ycsb_rmw": "false", "ycsb_max_ope": "1"}
INSTRUMENTATION_PATCH = legacy.INSTRUMENTATION_PATCH
LOCKSKIP_PATCH = legacy.LOCKSKIP_PATCH
PERMUTATION_PATCH = legacy.PERMUTATION_PATCH
EARLY_UNLOCK_PATCH = legacy.EARLY_UNLOCK_PATCH
LOCKSKIP_DEFINE = legacy.LOCKSKIP_DEFINE
PERMUTATION_DEFINE = legacy.PERMUTATION_DEFINE
EARLY_UNLOCK_DEFINE = legacy.EARLY_UNLOCK_DEFINE
HOT_UPDATE_PATCH = "patches/broken-mocc-hot-update-unlock.patch"
HOT_UPDATE_DEFINE = "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK"
REGIMES = {"hot": "0", "cold": "21", "default": "10"}
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 900.0
CLK = legacy.CLK
ENV_TAG = legacy.ENV_TAG
LEGACY_PROOF = "output/env/pegasus/calibration/s3_mocc_lock_coverage.json"
HOT_PATH_EVIDENCE = {
    "method": "negative-control",
    "guarantee": "stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出",
}
PATCHES = {
    "instrumentation": INSTRUMENTATION_PATCH,
    "lockskip": LOCKSKIP_PATCH,
    "permutation_erase": PERMUTATION_PATCH,
    "early_unlock": EARLY_UNLOCK_PATCH,
    "hot_update_unlock": HOT_UPDATE_PATCH,
}
BROKEN_PATCHES = (LOCKSKIP_PATCH, PERMUTATION_PATCH, EARLY_UNLOCK_PATCH, HOT_UPDATE_PATCH)
_sha256_file = legacy._sha256_file
_run_checked = legacy._run_checked
_load_policy = legacy._load_policy
_resolve_toolchain = legacy._resolve_toolchain
_prepare_dependencies = legacy._prepare_dependencies
_common_configure_args = legacy._common_configure_args
_apply_owned_patch = legacy._apply_owned_patch
_trace0_record = legacy._trace0_record
_repo_root = legacy._repo_root

# Stock W and U share build S; the remaining controls each have one build.
MATRIX = tuple(
    {"run_name": f"{label}_{regime}_t{thread}", "build": build,
     "workload": workload, "regime": regime, "thread": thread,
     "acceptance": "required" if (
         build == "S"
         or (build == "L" and regime != "hot")
         or (build in {"P", "E"} and regime != "default" and thread == 1)
         or (build == "H" and (regime != "hot" or thread == 1))
     ) else "observe"}
    for label, build, workload in (
        ("stock", "S", "W"), ("stock_u", "S", "U"),
        ("lockskip", "L", "W"), ("perm", "P", "W"),
        ("early_unlock", "E", "W"), ("hot_update_unlock", "H", "U"),
    )
    for regime in REGIMES for thread in (1, 4)
)
CHECK_KEYS = (
    *(f"{label}_{regime}_t{thread}_certified_and_silent"
      for label in ("stock", "stock_u") for regime in REGIMES for thread in (1, 4)),
    *(f"{regime}_lockskip_t{thread}_{suffix}"
      for regime in ("cold", "default")
      for thread, suffix in ((1, "three_reasons_cycles_zero"), (4, "x_positive"))),
    *(f"perm_{regime}_t1_only_size_changed" for regime in ("hot", "cold")),
    *(f"early_unlock_{regime}_t1_retention_without_entry" for regime in ("hot", "cold")),
    "hot_update_unlock_hot_t1_three_reasons_cycles_zero",
    *(f"hot_update_unlock_{regime}_t{thread}_silent"
      for regime in ("cold", "default") for thread in (1, 4)),
    "matrix_runs_complete_and_terminated",
    "hot_path_evidence_method_is_negative_control",
    "trace0_nm_izanagi_zero",
    "trace0_strings_izanagi_trace_zero",
    "trace0_logical_rows_identical",
    "toolchain_matches_policy",
    "all_broken_patch_touch_sets_are_transaction_only",
)
SUMMARY_KEYS = (
    "verdict", "certified", "total_cycles", "txns",
    "lock_coverage_violations", "permutation_violations",
)
OTHER_INTEGRITY_KEYS = (
    "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
    "missing_txids", "write_version_mismatch", "malformed_keys",
    "framing_violations", "framing_violation_details", "write_intent_violations",
)
X_REASONS = ("not-locked-at-entry", "lock-lost-before-write", "lock-lost-before-publish")


def _cell_flags(cell: Mapping[str, Any]) -> dict[str, str]:
    flags = dict(SINGLE_FLAGS if cell["workload"] == "W" else U_SINGLE_FLAGS)
    flags.update(thread_num=str(cell["thread"]), temp_threshold=REGIMES[cell["regime"]])
    return flags


def _require_condition_gate(
    source_root: Path, macro: str | None, configure_args: Sequence[str], cxx: str,
) -> dict[str, Any] | None:
    if macro is None:
        return None
    captured = condition_meaning_gate.capture_define_inputs(
        source_root, configure_args=tuple(configure_args),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.s3_mocc_mutation_proof",
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


def _empty_process(argv: Sequence[str]) -> dict[str, Any]:
    return {"argv": list(argv), "terminated": False, "returncode": None,
            "timed_out": False, "error": None}


def _run_trace(binary: Path, flags: Mapping[str, str]) -> tuple[Path, dict[str, Any]]:
    trace_dir = Path(tempfile.mkdtemp(prefix="izanagi_mocc_mutation_trace_"))
    argv = [os.fspath(binary), *(f"-{k}={v}" for k, v in flags.items()),
            f"-clocks_per_us={CLK}"]
    record = _empty_process(argv)
    try:
        completed = subprocess.run(
            argv, cwd=os.fspath(trace_dir),
            env=dict(os.environ, IZANAGI_TRACE_DIR=os.fspath(trace_dir)),
            capture_output=True, text=True, timeout=RUN_TIMEOUT_S, check=False,
        )
        record.update(terminated=True, returncode=completed.returncode)
        if completed.returncode != 0:
            record["error"] = f"benchmark rc={completed.returncode}: {completed.stderr[-500:]!r}"
    except subprocess.TimeoutExpired as exc:
        record.update(timed_out=True, error=str(exc))
    except (OSError, subprocess.SubprocessError) as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    return trace_dir, record


def _verify(trace_dir: Path, ccbench_root: Path) -> dict[str, Any]:
    argv = [sys.executable, "-m", "verifier", os.fspath(trace_dir), "--json", "--quiet",
            "--protocol", "mocc", "--ccbench-root", os.fspath(ccbench_root)]
    result = {**_empty_process(argv), "record": None}
    try:
        completed = _run_checked(
            argv, cwd=_repo_root() / "orchestrator", timeout=VERIFIER_TIMEOUT_S,
            allowed_returncodes=frozenset({0, 1, 3}),
        )
        result.update(terminated=True, returncode=completed.returncode)
        record = json.loads(completed.stdout)["results"][0]
        if not isinstance(record, dict):
            raise ValueError("verifier result is not a record")
        result["record"] = record
    except RuntimeError as exc:
        result.update(timed_out=isinstance(exc.__cause__, subprocess.TimeoutExpired),
                      error=str(exc))
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        result["error"] = f"invalid verifier result: {exc}"
    return result


def _summary(record: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = record or {}
    integrity = raw.get("integrity")
    stats = raw.get("stats")
    integrity = integrity if isinstance(integrity, Mapping) else {}
    stats = stats if isinstance(stats, Mapping) else {}
    return {
        "verdict": raw.get("verdict"), "certified": raw.get("certified"),
        "total_cycles": raw.get("total_cycles"), "txns": stats.get("txns"),
        "lock_coverage_violations": integrity.get("lock_coverage_violations"),
        "permutation_violations": integrity.get("permutation_violations"),
    }


def _trace_counts(trace_dir: Path) -> dict[str, Any]:
    counts = legacy._trace_counts(trace_dir)
    read_rows = 0
    for path in sorted(trace_dir.glob("trace_*.log")):
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.split(maxsplit=1)[:1] == ["R"]:
                    read_rows += 1
    return {**counts, "read_rows": read_rows}


def _logical_nonempty_rows(preprocessed: str) -> tuple[tuple[int, str], ...]:
    logical = None
    rows = []
    for raw in preprocessed.splitlines():
        marker = re.fullmatch(r'#\s+([0-9]+)\s+"[^"\r\n]+"(?:\s+[0-9]+)*\s*', raw)
        if marker:
            logical = int(marker[1])
        elif logical is None:
            if raw.strip():
                raise ValueError("body appeared before a line marker")
        else:
            if raw.strip():
                rows.append((logical, raw))
            logical += 1
    return tuple(rows)


def _preprocess_trace_zero(source: str, cxx: str) -> tuple[tuple[int, str], ...]:
    # Preserve physical newlines while removing dependency includes (D1687).
    stripped = re.sub(r"(?m)^[ \t]*#[ \t]*include\b.*$", "", source)
    with tempfile.TemporaryDirectory(prefix="mocc-logical-rows-") as raw:
        directory = Path(raw)
        (directory / "source.cc").write_text(stripped, encoding="utf-8")
        output = _run_checked([
            cxx, "-E", "-nostdinc", "-Werror=undef", "-DTRACE=0", "-DRWLOCK",
            "-DADD_ANALYSIS=0", "-DBACK_OFF=0", "-DKEY_SORT=0",
            "-DTEMPERATURE_RESET_OPT=1", "-DMASSTREE_USE=1", "-DLinux",
            "-DKEY_SIZE=8", "-DVAL_SIZE=4", "-x", "c++", "source.cc",
        ], cwd=directory).stdout
    return _logical_nonempty_rows(output)


def _logical_rows_record(base, instrumented) -> dict[str, Any]:
    def digest(rows):
        return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "logical_rows_identical": base == instrumented,
        "base_logical_rows_count": len(base),
        "patched_logical_rows_count": len(instrumented),
        "base_logical_rows_sha256": digest(base),
        "patched_logical_rows_sha256": digest(instrumented),
    }


def _variant_run(binary: Path, cell: Mapping[str, Any], source_root: Path,
                 runs: dict[str, Any], save) -> None:
    _assert_single_tenant()
    flags = _cell_flags(cell)
    trace_dir, process = _run_trace(binary, flags)
    record = {key: cell[key] for key in ("build", "workload", "regime", "thread", "acceptance")}
    record.update(flags=flags, **process, verifier={**_empty_process([]), "record": None},
                  **_summary(None), x_reasons=None, p_reasons=None,
                  non_insert_writes=None, read_rows=None)
    runs[cell["run_name"]] = record
    try:
        save()
        if process["terminated"] and process["returncode"] == 0 and not process["timed_out"]:
            record.update(_trace_counts(trace_dir))
            record["verifier"] = _verify(trace_dir, source_root)
            record.update(_summary(record["verifier"]["record"]))
        save()
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def _positive(value: Any) -> bool:
    return type(value) is int and value > 0


def _other_integrity_clean(run) -> bool:
    integrity = run["verifier"]["record"]["integrity"]
    return all(key in integrity and integrity[key] in (0, [], {}) for key in OTHER_INTEGRITY_KEYS)


def _productive(run) -> bool:
    return _positive(run["txns"]) and _positive(run["non_insert_writes"])


def _u(run) -> bool:
    return run["read_rows"] == 0 and run["non_insert_writes"] == run["txns"]


def _silent(run, *, update=False) -> bool:
    return (run["certified"] is True and run["verdict"] == "serializable"
            and run["total_cycles"] == 0 and run["lock_coverage_violations"] == 0
            and run["permutation_violations"] == 0 and _productive(run)
            and _other_integrity_clean(run) and (not update or _u(run)))


def _negative_single(run) -> bool:
    return (run["certified"] is False and run["verdict"] == "indeterminate"
            and run["total_cycles"] == 0 and _productive(run) and _other_integrity_clean(run))


def _three_reasons(run, *, update=False) -> bool:
    return (_negative_single(run) and _positive(run["lock_coverage_violations"])
            and run["permutation_violations"] == 0
            and all(_positive(run["x_reasons"].get(reason)) for reason in X_REASONS)
            and (not update or _u(run)))


def _lockskip_four(run) -> bool:
    # R1: these two required runs retain raw integrity without a clean check.
    return (run["certified"] is False and _positive(run["lock_coverage_violations"])
            and run["permutation_violations"] == 0 and _productive(run)
            and type(run["total_cycles"]) is int and run["total_cycles"] >= 0
            and run["verdict"] == ("non-serializable" if run["total_cycles"] else "indeterminate"))


def _matrix_complete(runs) -> bool:
    if set(runs) != {cell["run_name"] for cell in MATRIX}:
        return False
    for cell in MATRIX:
        run = runs[cell["run_name"]]
        if any(run[key] != cell[key] for key in ("build", "workload", "regime", "thread", "acceptance")):
            return False
        flags = _cell_flags(cell)
        argv = run["argv"]
        if (run["flags"] != flags or not isinstance(argv, list) or not argv
                or not all(isinstance(arg, str) for arg in argv)
                or Path(argv[0]).name != "ycsb_mocc.exe"
                or argv[1:] != [*(f"-{k}={v}" for k, v in flags.items()), f"-clocks_per_us={CLK}"]):
            return False
        verifier = run["verifier"]
        verifier_argv = verifier["argv"]
        if (not isinstance(verifier_argv, list) or len(verifier_argv) != 10
                or not all(isinstance(arg, str) and arg for arg in verifier_argv)
                or verifier_argv[1:3] != ["-m", "verifier"]
                or verifier_argv[4:9] != ["--json", "--quiet", "--protocol", "mocc", "--ccbench-root"]
                or not Path(verifier_argv[3]).is_absolute()
                or not Path(verifier_argv[9]).is_absolute()):
            return False
        if (run["terminated"] is not True or run["returncode"] != 0
                or run["timed_out"] is not False or verifier["terminated"] is not True
                or verifier["timed_out"] is not False or verifier["returncode"] not in {0, 1, 3}
                or not isinstance(verifier["record"], Mapping)):
            return False
        if any(value is None for value in _summary(verifier["record"]).values()):
            return False
    return True


def compute_checks(runs, trace0, touch_sets, patch_relatives, toolchain, policy, *, hot_path_evidence):
    """Missing observations fail their checks; observation-only cells require completion."""
    checks = {}

    def check(key, predicate):
        try:
            checks[key] = bool(predicate())
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            checks[key] = False

    for label in ("stock", "stock_u"):
        for regime in REGIMES:
            for thread in (1, 4):
                name = f"{label}_{regime}_t{thread}"
                check(f"{name}_certified_and_silent", lambda: _silent(runs[name], update=label == "stock_u"))
    for regime in ("cold", "default"):
        check(f"{regime}_lockskip_t1_three_reasons_cycles_zero",
              lambda: _three_reasons(runs[f"lockskip_{regime}_t1"]))
        check(f"{regime}_lockskip_t4_x_positive",
              lambda: _lockskip_four(runs[f"lockskip_{regime}_t4"]))
    for regime in ("hot", "cold"):
        def permutation():
            run = runs[f"perm_{regime}_t1"]
            return (_negative_single(run) and run["lock_coverage_violations"] == 0
                    and _positive(run["permutation_violations"])
                    and run["p_reasons"] == {"size-changed": run["permutation_violations"]})
        check(f"perm_{regime}_t1_only_size_changed", permutation)
    for regime in ("hot", "cold"):
        def early():
            run = runs[f"early_unlock_{regime}_t1"]
            return (_negative_single(run) and run["permutation_violations"] == 0
                    and _positive(run["lock_coverage_violations"])
                    and run["x_reasons"].get(X_REASONS[0], 0) == 0
                    and all(_positive(run["x_reasons"].get(reason)) for reason in X_REASONS[1:]))
        check(f"early_unlock_{regime}_t1_retention_without_entry", early)
    check("hot_update_unlock_hot_t1_three_reasons_cycles_zero",
          lambda: _three_reasons(runs["hot_update_unlock_hot_t1"], update=True))
    for regime in ("cold", "default"):
        for thread in (1, 4):
            check(f"hot_update_unlock_{regime}_t{thread}_silent",
                  lambda: _silent(runs[f"hot_update_unlock_{regime}_t{thread}"], update=True))
    check("matrix_runs_complete_and_terminated", lambda: _matrix_complete(runs))
    check("hot_path_evidence_method_is_negative_control", lambda: all(
        hot_path_evidence[key] == value for key, value in HOT_PATH_EVIDENCE.items()))
    check("trace0_nm_izanagi_zero", lambda: trace0["nm_izanagi_count"] == 0)
    check("trace0_strings_izanagi_trace_zero", lambda: trace0["strings_izanagi_trace_count"] == 0
          and trace0["strings_izanagi_macro_count"] == 0)
    check("trace0_logical_rows_identical", lambda: trace0["logical_rows_identical"] is True
          and _positive(trace0["base_logical_rows_count"])
          and trace0["base_logical_rows_count"] == trace0["patched_logical_rows_count"]
          and isinstance(trace0["base_logical_rows_sha256"], str)
          and re.fullmatch(r"[0-9a-f]{64}", trace0["base_logical_rows_sha256"]) is not None
          and trace0["base_logical_rows_sha256"] == trace0["patched_logical_rows_sha256"])
    check("toolchain_matches_policy", lambda:
          set(toolchain["version_body_sha256"]) == set(policy["expected_compiler_version_body_sha256"]) == {"gcc", "g++"}
          and all(isinstance(toolchain["version_body_sha256"][role], str)
                  and re.fullmatch(r"[0-9a-f]{64}", toolchain["version_body_sha256"][role])
                  and toolchain["version_body_sha256"][role] == policy["expected_compiler_version_body_sha256"][role]
                  for role in ("gcc", "g++")))
    check("all_broken_patch_touch_sets_are_transaction_only", lambda:
          set(patch_relatives) == {INSTRUMENTATION_PATCH, *BROKEN_PATCHES}
          and set(touch_sets) - {INSTRUMENTATION_PATCH} == set(BROKEN_PATCHES)
          and all(touch_sets[path] == [SOURCE_REL] for path in BROKEN_PATCHES))
    if tuple(checks) != CHECK_KEYS:
        raise RuntimeError("check order/set differs from CHECK_KEYS")
    return checks


def _save_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        print(site_policy.heavy_work_refusal(site, "mocc mutation proof driver"), file=sys.stderr)
        return 2
    _assert_single_tenant()
    root = _repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=root / "tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--out", type=Path, default=root / "output/env/pegasus/calibration/s3_mocc_mutation_proof.json")
    args = parser.parse_args(argv)
    if not args.third_party_cache.is_absolute():
        raise RuntimeError("--third-party-cache must be absolute")
    policy = _load_policy(args.policy.resolve(strict=True))
    toolchain = _resolve_toolchain(policy)
    result = {
        "schema_version": "s3-mocc-mutation-proof/v1", "env_tag": ENV_TAG, "site": site,
        "ccbench_commit": PIN, "genome": STOCK_G.canonical(), "clocks_per_us": CLK,
        "toolchain": toolchain,
        "patches": {key: {"path": path, "sha256": _sha256_file(root / path)} for key, path in PATCHES.items()},
        "workloads": {"W": {"single": SINGLE_FLAGS, "high": HIGH_FLAGS},
                      "U": {"single": U_SINGLE_FLAGS, "high": U_HIGH_FLAGS}},
        "regimes": dict(REGIMES), "trace0": {},
        "legacy_proof": {"path": LEGACY_PROOF, "sha256": _sha256_file(root / LEGACY_PROOF)},
        "condition_gates": [],
        "diagnostic_build_admission": non_admissible_materializer(
            "orchestrator.campaign.s3_mocc_mutation_proof._build_variant"),
        "hot_path_evidence": dict(HOT_PATH_EVIDENCE), "touch_sets": {}, "runs": {},
    }

    def save():
        result["checks"] = compute_checks(
            result["runs"], result["trace0"], result["touch_sets"], tuple(PATCHES.values()),
            toolchain, policy, hot_path_evidence=result["hot_path_evidence"],
        )
        result["all_pass"] = all(result["checks"].values()) and len(result["runs"]) == len(MATRIX)
        _save_json(args.out, result)

    save()
    with tempfile.TemporaryDirectory(prefix="izanagi_mocc_mutation_") as raw:
        scratch = Path(raw)
        dependencies = _prepare_dependencies(root, policy, args.third_party_cache, scratch, toolchain)
        base_repo = root / "external/ccbench"
        for build, patch, macro in (
            ("S", None, None), ("L", LOCKSKIP_PATCH, LOCKSKIP_DEFINE),
            ("P", PERMUTATION_PATCH, PERMUTATION_DEFINE),
            ("E", EARLY_UNLOCK_PATCH, EARLY_UNLOCK_DEFINE),
            ("H", HOT_UPDATE_PATCH, HOT_UPDATE_DEFINE),
        ):
            with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
                source = Path(source_value)
                assert_pinned_clean(source_value, PIN)
                result["touch_sets"][INSTRUMENTATION_PATCH] = _apply_owned_patch(root, source, INSTRUMENTATION_PATCH)
                if patch is not None:
                    result["touch_sets"][patch] = _apply_owned_patch(root, source, patch)
                binary, gate = _build_variant(source, scratch / f"{build}-trace1", trace=1,
                                              toolchain=toolchain, dependencies=dependencies, macro=macro)
                if gate is not None:
                    result["condition_gates"].append(gate)
                for cell in MATRIX:
                    if cell["build"] == build:
                        _variant_run(binary, cell, source, result["runs"], save)
        binaries, logical = [], []
        for label, instrumented in (("base", False), ("inst", True)):
            with checkout(PIN, base_dir=os.fspath(base_repo)) as source_value:
                source = Path(source_value)
                assert_pinned_clean(source_value, PIN)
                if instrumented:
                    _apply_owned_patch(root, source, INSTRUMENTATION_PATCH)
                logical.append(_preprocess_trace_zero((source / SOURCE_REL).read_text(), str(toolchain["cxx_path"])))
                binary, _gate = _build_variant(source, scratch / f"trace0-{label}", trace=0,
                                               toolchain=toolchain, dependencies=dependencies)
                binaries.append(binary)
        result["trace0"] = {**_trace0_record(*binaries), **_logical_rows_record(*logical),
                            "comparison": "unpatched-vs-instrumentation-only"}
        save()
    print(f"all_pass={result['all_pass']} -> {args.out}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
