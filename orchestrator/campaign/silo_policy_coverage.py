#!/usr/bin/env python3
"""Compute-node diagnostics for the Silo function-policy skeleton (NON_ADMISSIBLE).

No campaign admission or candidate selection occurs here. All mutation builds
are isolated, and no-limit is explicitly a surviving, non-detection control.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
from dataclasses import asdict
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import axis_silo_function_policy as axis
from .backoff_extended_sweep import _assert_backoff_fixed_materialized
from . import condition_meaning_gate as condition
from . import site_policy, source_digest
from . import s2_verify_calibration as calibration
from . import s3_lock_coverage as locks
from . import s3_mocc_lock_coverage as compute
from .materializer_admission import non_admissible_materializer
from .model import Genome
from .p2_2 import _assert_single_tenant
from .p3_s4_loop import quarantine
from .patchharness import applied, apply_patch, checkout
from .pipeline import (CorrectnessWorkload, PerfConfig,
                       performance_correctness_workload, _parse_commit_witness)
from orchestrator.calibrator.benchparse import parse_bench_stdout, throughput_tps

ROOT = Path(__file__).resolve().parents[2]
DRIVER_ID = "orchestrator.campaign.silo_policy_coverage"
MATERIALIZER = DRIVER_ID + "._build_variant"
ENV_TAG = compute.ENV_TAG
PIN = axis.PIN
PROBE_PATCH = "instr-silo-function-policy-probe.patch"
PROBE_DEFINE = "IZANAGI_SILO_POLICY_PROBE"
BREAK_DEFINE = "IZANAGI_BREAK_SILO_POLICY"
GENOME = Genome("silo", {**locks._BASE, axis.FLAG: 1})
LEGACY = CorrectnessWorkload().flags
PERF = PerfConfig(1000000, 48, {
    "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
    "ycsb_rmw": "false", "ycsb_max_ope": "10",
}, extime=3, reps=1)
NEGATIVES = {
    "norw": ("broken-silo-policy-norw-validation.patch", calibration.NORW_DEFINE),
    "lockskip": ("broken-silo-policy-lockskip-validation.patch", locks.LOCKSKIP_DEFINE),
    "early-unlock": (locks.EARLY_UNLOCK_PATCH, locks.EARLY_UNLOCK_DEFINE),
}
# (policy, enable probe, first observable layer). The probe patch is the common
# application base of mechanism patches, but is compiled out in the legacy cases.
MUTATIONS = {
    "no-clamp": ("huge", False, "trace-timeout"),
    "no-reload": ("retry", True, "retry_success"),
    "no-limit": ("retry", False, "NON_DETECTION_CONTROL"),
    "no-prefix-unlock-conflict": ("abort0", False, "trace-timeout"),
    "no-prefix-unlock-limit": ("retry", False, "trace-timeout"),
    "no-abort-hook": ("focus", True, "abort"),
    "no-lock-hook": ("focus", True, "lock"),
    "no-commit-hook": ("focus", True, "commit"),
    "wrong-reason": ("focus", True, "reason"),
}
MUTATION_PATCHES = {
    name: "broken-silo-policy-" + ("no-prefix-unlock" if name == "no-prefix-unlock-conflict" else name) + ".patch"
    for name in MUTATIONS
}
PREFIX_EXITS = {"no-prefix-unlock-conflict": "action-abort",
                "no-prefix-unlock-limit": "attempt-limit"}
CONTROL_OBSERVATIONS = {
    "control/" + name: "focus/" + policy
    for name, (policy, probe, _) in MUTATIONS.items() if probe
}
FLAG_BOUNDARIES = {
    "backoff0": ("BACK_OFF", "0"), "backoff2": ("BACK_OFF", "2"),
    "tictoc1": ("NO_WAIT_OF_TICTOC", "1"),
    "nowait0": ("NO_WAIT_LOCKING_IN_VALIDATION", "0"),
}
REASONS = axis.REASON_NAMES
PROBE_KEYS = frozenset((
    "aborts", "locks", "commits", "retry_success", "limit_aborts",
    "prefix_held_limit_aborts", "prefix_held_action_aborts",
    "limit_reason_mismatch", "clamps", "post_commit_match", "post_commit_mismatch",
    *(h + "_" + outcome for h in ("abort", "lock", "commit", "reason")
      for outcome in ("match", "mismatch")),
    *("site_" + r for r in REASONS[1:]), *("reason_" + r for r in REASONS),
))
NEGATIVE_CASES = tuple(f"{n}/{p}" for n in NEGATIVES for p in ("abort0", "maxwait"))
FOCUS_CASES = ("focus/focus", "focus/retry", "focus/huge", "focus/abort0")
CONTROL_CASES = tuple("control/" + m for m in MUTATIONS)
MUTATION_CASES = tuple("mutation/" + m for m in MUTATIONS)
COVERAGE_CASES = frozenset((*NEGATIVE_CASES, *FOCUS_CASES, *CONTROL_CASES,
                            *MUTATION_CASES, *("flag/" + f for f in FLAG_BOUNDARIES),
                            "trace0"))
SMOKE_CASES = frozenset(("stock", "abort0", "static5", "static10", "retry"))
FOCUS_CHECKS = ("certified", "commits", "aborts", "locks", "conservation",
                "reason", "abort", "lock", "commit")
CASE_CHECKS = {
    **{n: ("detected", "preprocess") for n in NEGATIVE_CASES},
    "focus/focus": FOCUS_CHECKS,
    "focus/abort0": ("certified", "commits", "aborts", "locks", "conservation", "prefix_action"),
    "focus/retry": ("certified", "commits", "retry_success", "limit", "reason", "conservation"),
    "focus/huge": ("certified", "commits", "clamp", "reason", "conservation"),
    **{n: ("expected",) for n in (*CONTROL_CASES, *MUTATION_CASES)},
    **{"flag/" + n: ("rejected",) for n in FLAG_BOUNDARIES},
    "trace0": ("clean",),
}
COVERAGE_CHECKS = frozenset(c + ":" + k for c, keys in CASE_CHECKS.items() for k in keys)
SMOKE_CHECKS = frozenset(
    c + ":" + k for c in SMOKE_CASES
    for k in ("contract", "digest", "legacy", "performance", "throughput", "identity")
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_probe(text: str, *, workers: int) -> dict:
    """Strict worker records; unrelated CCBench stdout lines are ignored."""
    records = {}
    for line in text.splitlines():
        if not line.startswith(PROBE_DEFINE):
            continue
        parts = line.split()
        if parts[0] != PROBE_DEFINE:
            raise ValueError("invalid probe prefix")
        row = {}
        for item in parts[1:]:
            match = re.fullmatch(r"([a-z_]+)=([0-9]+)", item)
            if match is None or match[1] in row:
                raise ValueError("malformed or duplicate probe field")
            row[match[1]] = int(match[2])
        if set(row) != PROBE_KEYS | {"worker"}:
            raise ValueError("missing or unknown probe field")
        worker = row.pop("worker")
        if worker in records:
            raise ValueError("duplicate worker")
        records[worker] = row
    if type(workers) is not int or workers <= 0 or set(records) != set(range(workers)):
        raise ValueError("missing or unexpected worker")
    totals = {key: sum(row[key] for row in records.values()) for key in PROBE_KEYS}
    return {"workers": records, "totals": totals,
            "reasons": {r: ("measured" if totals["site_" + r] > 0 else "unmeasured")
                        for r in REASONS[1:]}}


def _positive(value) -> bool:
    return type(value) is int and value > 0


def _certified(r: dict) -> bool:
    return (r.get("certified") is True and r.get("verdict") == "serializable"
            and type(r.get("exit_code")) is int and r["exit_code"] == 0
            and _positive(r.get("commits")))


def judge_norw(r: dict) -> bool:
    return (r.get("verdict") == "non-serializable"
            and _positive(r.get("total_cycles"))
            and type(r.get("exit_code")) is int and r["exit_code"] == 1)


def _encoding(p: dict, hook: str) -> bool:
    denominator = p.get("locks" if hook == "abort" else "aborts")
    return (_positive(p.get(hook + "_match")) and p.get(hook + "_mismatch") == 0
            and p[hook + "_match"] == denominator)


def _focus_checks(r: dict) -> dict[str, bool]:
    p = r.get("probe", {}).get("totals", {})
    return {
        "certified": _certified(r), "commits": _positive(p.get("commits")),
        "aborts": _positive(p.get("aborts")), "locks": _positive(p.get("locks")),
        "conservation": (_positive(p.get("aborts")) and
                         sum(p.get("reason_" + n, -1) for n in REASONS) == p.get("aborts")
                         and p.get("aborts") == r.get("aborts")
                         and p.get("commits") == r.get("commits")),
        **{h: _encoding(p, h) for h in ("abort", "lock", "commit", "reason")},
        "retry_success": _positive(p.get("retry_success")),
        "limit": (_positive(p.get("limit_aborts")) and p.get("limit_reason_mismatch") == 0
                  and _positive(p.get("reason_lock_conflict"))),
        "clamp": _positive(p.get("clamps")),
        "prefix_action": _positive(p.get("prefix_held_action_aborts")),
    }


def check_case(case: str, r: dict) -> dict[str, bool]:
    if case in NEGATIVE_CASES:
        kind = case.split("/")[0]
        if kind == "norw":
            ok = judge_norw(r)
        else:
            reasons = r.get("x_reasons", {})
            ok = (r.get("total_cycles") == 0 and _positive(r.get("lock_coverage_violations"))
                  and r.get("verdict") == "indeterminate"
                  and _positive(reasons.get("lock-lost-before-write")))
            ok = ok and (_positive(reasons.get("not-locked-at-entry")) if kind == "lockskip"
                         else set(reasons) == {"lock-lost-before-write"})
        return {"detected": ok and _positive(r.get("commits")),
                "preprocess": r.get("break_evidence", {}).get("target_difference") is True}
    if case in FOCUS_CASES:
        checks = _focus_checks(r)
        if case == "focus/focus":
            p = r.get("probe", {}).get("totals", {})
            checks["commit"] = (checks["commit"] and _positive(p.get("post_commit_match"))
                                and p.get("post_commit_mismatch") == 0)
        return {k: checks[k] for k in CASE_CHECKS[case]}
    if case.startswith(("control/", "mutation/")):
        control, name = case.split("/")
        _, _, layer = MUTATIONS[name]
        p = r.get("probe", {}).get("totals", {})
        if control == "control":
            expected = _certified(r)
            if layer == "retry_success":
                expected = expected and _positive(p.get("retry_success"))
            elif layer in ("abort", "lock", "commit", "reason"):
                expected = expected and all(_focus_checks(r)[k] for k in FOCUS_CHECKS)
        elif layer == "trace-timeout":
            expected = r.get("reason") == "trace-timeout"
        elif layer == "NON_DETECTION_CONTROL":
            expected = _certified(r)  # Never report this as KILLED.
        elif layer == "retry_success":
            expected = (_certified(r) and _positive(p.get("locks"))
                        and p.get("retry_success") == 0)
        else:
            red = {"no-abort-hook": {"abort", "lock", "commit"},
                   "no-lock-hook": {"abort", "lock"},
                   "no-commit-hook": {"commit"}, "wrong-reason": {"reason"}}[name]
            expected = (_certified(r)
                        and all(_positive(p.get(hook + "_mismatch")) if hook in red
                                else _encoding(p, hook)
                                for hook in ("abort", "lock", "commit", "reason"))
                        and _focus_checks(r)["conservation"])
        return {"expected": expected}
    if case.startswith("flag/"):
        return {"rejected": r.get("returncode") == 1 and
                "Silo function policy requires BACK_OFF=1 and no-wait flags 1/0" in r.get("stderr", "")}
    if case == "trace0":
        return {"clean": r.get("clean") is True}
    raise ValueError("unknown case: " + case)


def judge(runs: dict, checks: dict, *, mode: str = "coverage") -> dict:
    """Exact sets and exact booleans precede aggregation (M-CHK-EMPTY)."""
    if mode not in ("coverage", "smoke"):
        raise ValueError("unknown diagnostic mode")
    cases, keys = ((COVERAGE_CASES, COVERAGE_CHECKS) if mode == "coverage"
                   else (SMOKE_CASES, SMOKE_CHECKS))
    complete = set(runs) == cases and set(checks) == keys
    actual_bools = all(type(v) is bool for v in checks.values())
    reached = complete and all(
        _positive(runs[c].get("commits"))
        for c in cases if not c.startswith("flag/") and c != "trace0"
        and c not in {"mutation/no-clamp", *("mutation/" + name for name in PREFIX_EXITS)}
    )
    derived = {}
    if complete:
        try:
            derived = (coverage_checks(runs)
                       if mode == "coverage" else smoke_checks(runs))
        except (KeyError, TypeError, ValueError):
            complete = False
    return {"checks": checks, "all_pass": bool(complete and actual_bools and reached
                                               and checks == derived and all(checks.values()))}


def prepare_policy(path: Path, body: str, *, compiler: str, scratch_dir: str) -> tuple[str, dict]:
    """Four real gates before writing source or calling a build sink.

    Exceptions intentionally propagate: no fallback can proceed to a build.
    The exact same body string is rendered and checked, without normalization.
    """
    from .silo_policy_compile import check_policy_body
    sub = path.parents[len(Path(axis.SOURCE_REL).parts) - 1]
    result, _base, rendered, _diff = quarantine(
        str(sub), body, marker_id=axis.MARKER_ID, source_rel=axis.SOURCE_REL, write=False,
    )
    if not result.passed:
        raise ValueError("DiffQuarantine/effect gate: " + str(result.reason))
    grammar, compiled = check_policy_body(body, compiler=compiler, scratch_dir=scratch_dir)
    if (grammar.accepted is not True or compiled is None or compiled.accepted is not True
            or compiled.timed_out or compiled.unavailable or compiled.returncode != 0):
        raise ValueError("policy grammar/compile rejected: " + repr((grammar, compiled)))
    # render_hole preserves this body's exact bytes (including a trailing newline).
    start = rendered.index("#if SILO_POLICY_VARIANT\n", rendered.index("// EVOLVE-BLOCK-BEGIN"))
    start += len("#if SILO_POLICY_VARIANT\n")
    materialized = rendered[start:rendered.index("#else\n#endif\n// EVOLVE-BLOCK-END", start)]
    # render_hole adds one newline separating the body's last split element.
    if materialized != body + "\n":
        raise RuntimeError("checked/materialized body differs")
    return rendered, {"accepted": True, "stages": ("quarantine", "effects", "grammar", "compile"),
                      "checked_sha256": sha(body), "materialized_sha256": sha(materialized[:-1]),
                      "grammar": asdict(grammar), "compile": asdict(compiled)}


def _condition_gate(source: Path, macro: str, configure_args: list[str], cxx: str) -> dict:
    captured = condition.capture_define_inputs(source, configure_args=tuple(configure_args))
    request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                            requested_value=1, default_value=0)
    with condition._configured_define_compile_commands(
        captured, request=request, cxx=cxx, cmake="cmake",
    ) as commands:
        supply = condition.evaluate_define_supply_effectuation(
            captured, request=request, cxx=cxx, cmake="cmake", configured_commands=commands)
        meaning = condition.evaluate_define_runtime_meaning(
            captured, request=request, declaration=condition.declare_define_runtime_meaning(request),
            cxx=cxx, cmake="cmake", configured_commands=commands)
    admission = condition.require_condition_gate_family([supply], [meaning], use_class="raw-measurement")
    if not admission.admitted:
        rejection = RuntimeError(
            f"condition gate rejected {macro}: "
            f"supply={supply.terminal_status}/{supply.reason_code}, "
            f"meaning={meaning.terminal_status}/{meaning.reason_code}"
        )
        rejection.condition_gate_evidence = {
            "macro": macro, "supply": json.loads(supply.canonical_json()),
            "meaning": json.loads(meaning.canonical_json()),
            "admission": json.loads(admission.canonical_json()),
        }
        raise rejection
    return {"macro": macro, "supply": json.loads(supply.canonical_json()),
            "meaning": json.loads(meaning.canonical_json()),
            "admission": json.loads(admission.canonical_json())}


def _condition_gates(source: Path, macros: tuple[str, ...], args: list[str],
                     cxx: str, *, stock: bool) -> list[dict]:
    if stock and macros:
        raise ValueError("stock build cannot supply diagnostic macros")
    gates = []
    # A mechanism mutation's one declared site is witnessed on its own actual
    # source. Controls separately witness axis/probe sites. Enclosing mutations
    # duplicate those sites in their inactive #else; a fixed site-count receipt
    # for the unmutated probe must not be misrepresented as a mutation receipt.
    gate_macros = ((BREAK_DEFINE,) if BREAK_DEFINE in macros else
                   (() if stock else (axis.FLAG,)) + macros)
    if not stock and not gate_macros:
        raise RuntimeError("missing policy condition requests")
    for macro in gate_macros:
        # One receipt tests one macro. The norw break hides an axis site when
        # enabled; probe/break sites need only the axis cache flag already in
        # args. No declared break site is nested under the probe flag, so no
        # diagnostic CXX companion is needed, even for probe-enabled builds.
        gates.append(_condition_gate(source, macro, args, cxx))
    if len(gates) != len(gate_macros) or any(
            r["admission"]["admitted"] is not True for r in gates):
        raise RuntimeError("incomplete or rejected condition gates")
    return gates


def _build_variant(source: Path, build: Path, *, trace: int, toolchain: dict,
                   dependencies: dict, macros: tuple[str, ...] = (), stock: bool = False,
                   stock_backoff: int = 1, stock_backoff_fixed: int | None = None) -> tuple[Path, dict]:
    if stock_backoff not in (0, 1) or (not stock and stock_backoff != 1):
        raise ValueError("stock_backoff is only available for stock builds")
    if stock_backoff_fixed is not None and (not stock or stock_backoff != 1):
        raise ValueError("stock_backoff_fixed requires stock with BACK_OFF=1")
    admission = non_admissible_materializer(MATERIALIZER)
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, "Silo policy diagnostic build"))
    # Reuse dependency/CMake arguments, replacing only MOCC's protocol flags.
    args = [a for a in compute._common_configure_args(
        trace=trace, toolchain=toolchain, dependencies=dependencies)
        if a not in compute.STOCK_G.cmake_defines()]
    stock_flags = {**locks._BASE, "BACK_OFF": stock_backoff}
    if stock_backoff_fixed is not None:
        stock_flags["BACKOFF_FIXED"] = stock_backoff_fixed
    stock_genome = Genome("silo", stock_flags)
    args += (stock_genome if stock else GENOME).cmake_defines()
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    gates = _condition_gates(source, macros, args, toolchain["cxx_path"], stock=stock)
    if (not stock and not gates) or any(r["admission"]["admitted"] is not True for r in gates):
        raise RuntimeError("condition gates rejected before build")
    if macros:
        args.append("-DCMAKE_CXX_FLAGS=" + " ".join("-D" + m + "=1" for m in macros))
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    compute._run_checked(configure)
    locks._run_cmake_build(["cmake", "--build", str(build), "--target", "ycsb_silo.exe"], site=site)
    binary = build / "cc/silo/ycsb_silo.exe"
    if not binary.is_file():
        raise RuntimeError("missing Silo binary")
    return binary, {"admission": admission, "condition_gates": gates, "configure": configure,
                    "binary_sha256": compute._sha256_file(binary)}


def _owner_command(build: Path, source: Path) -> dict:
    rows = json.loads((build / "compile_commands.json").read_text())
    owner = (source / axis.SOURCE_REL).resolve()
    def target_output(row):
        if "output" in row:
            return row["output"]
        args = _command_arguments(row)
        outputs = [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == "-o"]
        outputs += [arg[2:] for arg in args if arg.startswith("-o") and arg != "-o"]
        return outputs[0] if len(outputs) == 1 else ""

    rows = [r for r in rows if (Path(r["directory"]) / r["file"]).resolve() == owner
            and isinstance(target_output(r), str)
            and "CMakeFiles/ycsb_silo.exe.dir/" in target_output(r)]
    if len(rows) != 1:
        raise RuntimeError("owner TU compile command is not unique")
    return rows[0]


def _preprocess(command: dict, overrides: dict[str, str] | None = None):
    args = _command_arguments(command)
    overrides = overrides or {}
    out = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-o", "-MF", "-MT", "-MQ"):
            i += 2
            continue
        if any(arg.startswith(prefix) and arg != prefix for prefix in ("-o", "-MF", "-MT", "-MQ")):
            i += 1
            continue
        if arg in ("-c", "-MD", "-MMD", "-MP"):
            i += 1
            continue
        if arg == "-D" and i + 1 < len(args) and args[i + 1].split("=", 1)[0] in overrides:
            i += 2
            continue
        if arg.startswith("-D") and arg[2:].split("=", 1)[0] in overrides:
            i += 1
            continue
        out.append(arg)
        i += 1
    out += ["-E", "-P", *("-D" + k + "=" + v for k, v in overrides.items())]
    return compute._run_checked(out, cwd=Path(command["directory"]),
                                allowed_returncodes=frozenset({0, 1}))


def _command_arguments(command: dict) -> list[str]:
    # Presence, not truthiness: an arguments row need not have a command key.
    return list(command["arguments"]) if "arguments" in command else shlex.split(command["command"])


def _break_evidence(case: str, command: dict, source: Path, patch: Path, macro: str) -> dict:
    off = _preprocess(command, {axis.FLAG: "1", macro: "0"})
    on = _preprocess(command, {axis.FLAG: "1", macro: "1"})
    if off.returncode or on.returncode:
        raise RuntimeError("owner TU preprocessing failed")
    kind = case.split("/")[0]
    function = {"norw": "validationPhase", "lockskip": "lockWriteSet",
                "early-unlock": "writePhase"}[kind]
    def body(text):
        match = re.search(r"(?:bool|void) TxExecutor::" + function + r"\([^)]*\)\s*\{", text)
        if match is None:
            raise RuntimeError("owner function absent in preprocessed TU")
        depth, end = 1, match.end()
        while depth and end < len(text):
            depth += (text[end] == "{") - (text[end] == "}")
            end += 1
        if depth:
            raise RuntimeError("unbalanced preprocessed function")
        return text[match.start():end]
    a, b = body(off.stdout), body(on.stdout)
    if kind == "norw":
        target = "AbortReason::read_tid" in a and "AbortReason::read_tid" not in b
    elif kind == "lockskip":
        # Preprocessors may normalize indentation; retain the exact token
        # sequence and adjacency, not the source file's whitespace spelling.
        needle = r"max_wset_\s*=\s*std::max\(max_wset_,\s*expected\);\s*continue;"
        target = re.search(needle, b) is not None and re.search(needle, a) is None
    else:
        needle = "storeRelease((*itr).rcdptr_->tidword_.obj_, maxtid.obj_);"
        target = b.count(needle) == a.count(needle) + 1
    return {"case_sha256": sha(case), "patch_sha256": compute._sha256_file(patch),
            "source_sha256": compute._sha256_file(source / axis.SOURCE_REL),
            "off_sha256": sha(off.stdout), "on_sha256": sha(on.stdout),
            "owner_compile_command": command,
            "target_difference": bool(target and a != b),
            "target_diff": "\n".join(difflib.unified_diff(a.splitlines(), b.splitlines(), n=3))}


def _verify(trace_dir: str, source: Path, commits: int) -> dict:
    # The S2/S3 helpers hard-code the shared checkout. Isolated builds need the
    # actual materialized root for proof-surface inspection; retain their CLI
    # and projection through the existing checked-process helper.
    completed = compute._run_checked([
        sys.executable, "-m", "verifier", trace_dir, "--json", "--quiet",
        "--protocol", "silo", "--ccbench-root", str(source),
        "--expected-commits", str(commits),
    ], cwd=ROOT / "orchestrator", timeout=calibration.GATE2_VERIFIER_WALL_S,
        allowed_returncodes=frozenset({0, 1, 2, 3}))
    record = json.loads(completed.stdout)["results"][0]
    return {"exit_code": completed.returncode, "verdict": record["verdict"],
            "certified": record["certified"], "total_cycles": record["total_cycles"],
            "txns": record["stats"]["txns"],
            "lock_coverage_violations": record["integrity"]["lock_coverage_violations"]}


def _run(binary: Path, flags: dict, *, source: Path, trace: bool, probe: bool = False,
         numa: bool = False) -> dict:
    """One new run site: retain stdout for probe and bench, always clean timeouts."""
    _assert_single_tenant()
    with tempfile.TemporaryDirectory(prefix="silo-policy-run-") as tmp:
        (Path(tmp) / "log").mkdir()
        env = dict(os.environ)
        env.pop("IZANAGI_TRACE_DIR", None)
        if trace:
            env["IZANAGI_TRACE_DIR"] = tmp
        command = (calibration.NUMA if numa else []) + [str(binary)]
        command += [f"-{k}={v}" for k, v in flags.items()] + [f"-clocks_per_us={locks.CLK}"]
        try:
            completed = subprocess.run(command, cwd=tmp, env=env, capture_output=True,
                                       text=True, timeout=locks.RUN_TIMEOUT_S, check=False)
        except subprocess.TimeoutExpired as exc:
            # TimeoutExpired can carry bytes even with text=True. Preserve
            # emitted diagnostics; killed workers cannot emit TLS destructors.
            def output_text(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
            return {"reason": "trace-timeout" if trace else "bench-no-throughput", "command": command,
                    "timeout_s": locks.RUN_TIMEOUT_S,
                    "stdout": output_text(exc.stdout), "stderr": output_text(exc.stderr)}
        if completed.returncode != 0:
            return {"reason": "trace-run-nonzero-exit", "returncode": completed.returncode,
                    "stderr": completed.stderr[-2000:], "command": command}
        commits, batches = _parse_commit_witness(completed.stdout)
        if commits is None or batches != 0:
            raise RuntimeError("missing or unattributable commit witness")
        r = {"commits": commits, "aborts": calibration._parse_abort_counts(completed.stdout),
             "command": command, "stdout_sha256": sha(completed.stdout)}
        if probe:
            r["probe"] = parse_probe(completed.stdout, workers=int(flags["thread_num"]))
        if trace:
            r["x_reasons"] = locks._count_x_reasons(tmp)
            try:
                r.update(_verify(tmp, source, commits))
            except RuntimeError as exc:
                if not isinstance(exc.__cause__, subprocess.TimeoutExpired):
                    raise
                r.update(reason="verifier-timeout", timeout_s=calibration.GATE2_VERIFIER_WALL_S)
        else:
            r["throughput"] = throughput_tps(parse_bench_stdout(completed.stdout))
            r["preliminary_same_job_stock_control"] = True
        return r


@contextmanager
def _source(policy: str, *, probe_patch: bool = False, patch: str | None = None,
            compiler: str, scratch: Path, body: str | None = None,
            backoff_fixed_patch: bool = False):
    if body is not None and policy == "stock":
        raise ValueError("stock and body cannot be specified together")
    if backoff_fixed_patch and policy != "stock":
        raise ValueError("backoff_fixed_patch requires stock")
    with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as value:
        source = Path(value)
        stock = policy == "stock"
        ctx = (applied(str(ROOT / "patches/silo-backoff-fixed.patch"), PIN, value)
               if backoff_fixed_patch else nullcontext() if stock else
               applied(str(ROOT / "patches" / axis.TEMPLATE_PATCH), PIN, value))
        with ctx:
            contract = {"accepted": True, "stock": True}
            if backoff_fixed_patch:
                _assert_backoff_fixed_materialized(value)
                contract["backoff_fixed_patch"] = True
            if not stock:
                if probe_patch:
                    apply_patch(str(ROOT / "patches" / PROBE_PATCH), value)
                if patch:
                    apply_patch(str(ROOT / "patches" / patch), value)
                if body is None:
                    body = (ROOT / axis.HAND_POLICY_DIR / (policy + ".cpp")).read_text()
                path = source / axis.SOURCE_REL
                rendered, contract = prepare_policy(path, body, compiler=compiler, scratch_dir=str(scratch))
                path.write_text(rendered)
                if path.read_text() != rendered:
                    raise RuntimeError("materialized source differs from the checked rendering")
            yield source, contract


def run_coverage(scratch: Path, toolchain: dict, dependencies: dict, *, runs: dict | None = None) -> dict:
    runs = {} if runs is None else runs
    cases = [(c, c.split("/")[1], False, False, NEGATIVES[c.split("/")[0]][0],
              (NEGATIVES[c.split("/")[0]][1],)) for c in NEGATIVE_CASES]
    cases += [(c, c.split("/")[1], True, True, None, (PROBE_DEFINE,)) for c in FOCUS_CASES]
    for name, (policy, probe, _) in MUTATIONS.items():
        if "control/" + name not in CONTROL_OBSERVATIONS:
            cases.append(("control/" + name, policy, True, probe, None, (PROBE_DEFINE,) if probe else ()))
        cases.append(("mutation/" + name, policy, True, probe,
                      MUTATION_PATCHES[name],
                      ((PROBE_DEFINE,) if probe else ()) + (BREAK_DEFINE,)))
    for case, policy, probe_patch, probe, patch, macros in cases:
        print("case=" + case, flush=True)
        work = scratch / case.replace("/", "-")
        work.mkdir()
        with _source(policy, probe_patch=probe_patch, patch=patch,
                     compiler=toolchain["cxx_path"], scratch=work) as (source, contract):
            binary, build = _build_variant(source, work / "build", trace=1,
                                           toolchain=toolchain, dependencies=dependencies, macros=macros)
            negative = case.split("/")[0]
            flags = (locks.SINGLE_FLAGS if negative in ("lockskip", "early-unlock") else
                     {**calibration.S2_FLAGS, "extime": str(calibration.EXTIME_CANDIDATES[0])}
                     if negative == "norw" else LEGACY)
            definition = {"case": case, "policy": policy, "probe": probe,
                          "probe_patch": probe_patch, "patch": patch,
                          "macros": macros, "workload": flags, "trace": 1}
            if case.split("/")[-1] in PREFIX_EXITS:
                definition["target_exit"] = PREFIX_EXITS[case.split("/")[-1]]
            case_sha256 = sha(json.dumps(definition, sort_keys=True, separators=(",", ":")))
            evidence = (_break_evidence(case, _owner_command(work / "build", source), source,
                                        ROOT / "patches" / patch, macros[0])
                        if case in NEGATIVE_CASES else None)
            r = _run(binary, flags, source=source, trace=True, probe=probe, numa=negative == "norw")
            r.update(build=build, contract=contract, workload=flags,
                     source_sha256=compute._sha256_file(source / axis.SOURCE_REL),
                     case_sha256=case_sha256, case_definition=definition,
                     patches={p: compute._sha256_file(ROOT / "patches" / p)
                              for p in (axis.TEMPLATE_PATCH, PROBE_PATCH if probe_patch else None, patch) if p})
            if evidence is not None:
                evidence["case_sha256"] = case_sha256
                r["break_evidence"] = evidence
            if case == "mutation/no-limit":
                r["classification"] = "NON_DETECTION_CONTROL"
            runs[case] = r
    for control, observation in CONTROL_OBSERVATIONS.items():
        runs[control] = {**runs[observation], "observation_case": observation}
    # One real ordinary TRACE=0 build supplies all four flag boundary preprocess
    # attempts and the local absence check, without creating four redundant binaries.
    work = scratch / "trace0"
    work.mkdir()
    with _source("abort0", compiler=toolchain["cxx_path"], scratch=work) as (source, contract):
        _, build = _build_variant(source, work / "build", trace=0,
                                  toolchain=toolchain, dependencies=dependencies)
        command = _owner_command(work / "build", source)
        result = _preprocess(command)
        args = _command_arguments(command)
        clean = (result.returncode == 0 and not any("IZANAGI_" in a for a in args)
                 and not any(t in result.stdout for t in
                             (PROBE_DEFINE, BREAK_DEFINE, "izanagi_silo_probe", "DELIBERATELY BROKEN")))
        runs["trace0"] = {"clean": clean, "command": command, "build": build,
                          "preprocess_sha256": sha(result.stdout), "contract": contract,
                          "source_sha256": compute._sha256_file(source / axis.SOURCE_REL)}
        for name, (macro, value) in FLAG_BOUNDARIES.items():
            failed = _preprocess(command, {macro: value})
            runs["flag/" + name] = {"returncode": failed.returncode, "stderr": failed.stderr,
                                    "owner_command": command, "overrides": {macro: value}}
    checks = coverage_checks(runs)
    return {"runs": runs,
            "prefix_reach_evidence": {
                "scope": "Separate probe run with the same policy and workload; "
                         "not reach observed in the mutation run itself.",
                "mutation/no-prefix-unlock-limit": {
                    "observation_case": "focus/retry", "counter": "prefix_held_limit_aborts"},
                "mutation/no-prefix-unlock-conflict": {
                    "observation_case": "focus/abort0", "counter": "prefix_held_action_aborts"},
            }, **judge(runs, checks)}


def coverage_checks(runs: dict) -> dict[str, bool]:
    checks = {c + ":" + k: v for c, r in runs.items() for k, v in check_case(c, r).items()}
    for name, policy, counter in (
            ("no-prefix-unlock-limit", "retry", "prefix_held_limit_aborts"),
            ("no-prefix-unlock-conflict", "abort0", "prefix_held_action_aborts")):
        case = "mutation/" + name
        if case not in runs:
            continue
        mutation = runs[case].get("case_definition", {})
        focus = runs.get("focus/" + policy, {})
        observation = focus.get("case_definition", {})
        # Separate probe run: evidence of reach under the same configuration,
        # not evidence that the mutation run itself reached the target exit.
        reached = (mutation.get("policy") == observation.get("policy") == policy
                   and isinstance(mutation.get("workload"), dict)
                   and bool(mutation["workload"])
                   and mutation["workload"] == observation.get("workload")
                   and _positive(focus.get("probe", {}).get("totals", {}).get(counter)))
        if policy == "retry":
            reached = reached and _positive(focus.get("probe", {}).get("totals", {}).get("limit_aborts"))
        checks[case + ":expected"] = checks[case + ":expected"] and reached
    return checks


def run_smoke(scratch: Path, toolchain: dict, dependencies: dict, *, runs: dict | None = None) -> dict:
    runs = {} if runs is None else runs
    for policy in ("stock", "abort0", "static5", "static10", "retry"):
        print("smoke=" + policy, flush=True)
        work = scratch / policy
        work.mkdir()
        with _source(policy, compiler=toolchain["cxx_path"], scratch=work) as (source, contract):
            genome = locks.STOCK_G if policy == "stock" else GENOME
            evidence = source_digest.resolve_evidence(genome, PIN, ccbench_dir=str(source), cxx=toolchain["cxx_path"])
            trace, trace_build = _build_variant(source, work / "trace", trace=1, toolchain=toolchain,
                                                dependencies=dependencies, stock=policy == "stock")
            legacy = _run(trace, LEGACY, source=source, trace=True)
            performance_flags = performance_correctness_workload(PERF).flags
            performance = _run(trace, performance_flags, source=source, trace=True, numa=True)
            binary, perf_build = _build_variant(source, work / "perf", trace=0, toolchain=toolchain,
                                                dependencies=dependencies, stock=policy == "stock")
            bench = _run(binary, performance_flags, source=source, trace=False, numa=True)
            # Source identity must remain unchanged across the two actual builds.
            after = source_digest.resolve_evidence(genome, PIN, ccbench_dir=str(source), cxx=toolchain["cxx_path"])
            if after != evidence:
                raise RuntimeError("source identity changed during smoke")
            runs[policy] = {"commits": legacy.get("commits"), "contract": contract,
                            "legacy": legacy, "performance": performance, "bench": bench,
                            "src_token": evidence.src_token, "source_evidence": evidence.as_receipt(),
                            "builds": (trace_build, perf_build)}
    checks = smoke_checks(runs)
    return {"runs": runs, "throughput_interpretation": "preliminary; same-job stock; no comparison judgement",
            **judge(runs, checks, mode="smoke")}


def smoke_checks(runs: dict) -> dict[str, bool]:
    checks = {}
    tokens = [r["src_token"] for r in runs.values()]
    for policy, r in runs.items():
        contract = r["contract"]
        values = {
            "contract": contract.get("accepted") is True,
            "digest": (contract.get("stock") is True if policy == "stock" else
                       contract["checked_sha256"] == contract["materialized_sha256"]),
            "legacy": _certified(r["legacy"]), "performance": _certified(r["performance"]),
            "throughput": isinstance(r["bench"].get("throughput"), (int, float))
                          and r["bench"]["throughput"] > 0,
            "identity": (len(set(tokens)) == len(SMOKE_CASES) and
                         ((r["src_token"] == source_digest.STOCK) == (policy == "stock"))),
        }
        checks.update({policy + ":" + k: v for k, v in values.items()})
    return checks


def _prepare_build_dependencies(scratch: Path, toolchain: dict, dependencies: dict) -> dict:
    # Hydration supplies fresh per-job sources, not masstree's generated config.h.
    # Complete one ungated stock build before either mode can enter a case gate.
    work = scratch / "dependency-stock"
    work.mkdir()
    with _source("stock", compiler=toolchain["cxx_path"], scratch=work) as (source, _):
        _, receipt = _build_variant(source, work / "build", trace=1,
                                    toolchain=toolchain, dependencies=dependencies, stock=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("coverage", "smoke"))
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        print(site_policy.heavy_work_refusal(site, "Silo policy diagnostics"), file=sys.stderr)
        return 2
    _assert_single_tenant()
    if not args.third_party_cache.is_absolute():
        raise ValueError("--third-party-cache must be absolute")
    policy = compute._load_policy(args.policy.resolve(strict=True))
    toolchain = compute._resolve_toolchain(policy)
    result = {"schema_version": "silo-function-policy-" + args.command + "/v1",
              "env_tag": ENV_TAG, "site": site, "ccbench_commit": PIN,
              "toolchain": toolchain, "all_pass": False, "runs": {}, "checks": {},
              "diagnostic_build_admission": non_admissible_materializer(MATERIALIZER)}
    try:
        with tempfile.TemporaryDirectory(prefix="silo-policy-") as temporary:
            scratch = Path(temporary)
            dependencies = compute._prepare_dependencies(ROOT, policy, args.third_party_cache, scratch, toolchain)
            result["dependency_preparation"] = _prepare_build_dependencies(scratch, toolchain, dependencies)
            result.update((run_coverage if args.command == "coverage" else run_smoke)(
                scratch, toolchain, dependencies, runs=result["runs"]))
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        if hasattr(exc, "condition_gate_evidence"):
            result["condition_gate_evidence"] = exc.condition_gate_evidence
    out = args.out or ROOT / "output/env" / ENV_TAG / "calibration" / ("silo_function_policy_" + args.command + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"all_pass={result['all_pass']} -> {out}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
