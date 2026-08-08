#!/usr/bin/env python3
"""T-139 R4 environment probe contract, pure validators, and sampler.

The decision core deliberately accepts only counter/run/build witnesses.  Node
isolation diagnostics are recorded by the runtime, but are not arguments to
``derive_decision``.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence


PROBE_SERIES_ID = "t139-r4-env-probe"
PURPOSE = "non_study_environment_probe"
STUDY_ELIGIBLE = False
CONTRACT_PATH = "tools/pegasus/probes/t139_r4_env_probe_contract.json"
COUNTER_NAMES = (
    "user",
    "nice",
    "system",
    "idle",
    "iowait",
    "irq",
    "softirq",
    "steal",
)
WINDOW_TARGET_NS = 10_000_000_000
WINDOW_TOLERANCE_NS = 100_000_000
MAX_ADJACENCY_NS = 5_000_000_000
W1_ARGV = (
    "-ycsb_rmw=true",
    "-ycsb_zipf_skew=0.9",
    "-ycsb_tuple_num=10000",
    "-ycsb_max_ope=10",
    "-thread_num=48",
    "-extime=3",
)
W2_ARGV = (
    "-ycsb_rratio=50",
    "-ycsb_zipf_skew=0.5",
    "-ycsb_tuple_num=100000",
    "-ycsb_max_ope=10",
    "-thread_num=48",
    "-extime=3",
)

METADATA_KEYS = {"probe_series_id", "purpose", "study_eligible"}
TOP_LEVEL_KEYS = {
    "schema_version",
    "probe_series_id",
    "purpose",
    "study_eligible",
    "physical_cores",
    "counter_names",
    "window_duration_ns",
    "window_tolerance_ns",
    "max_run_adjacency_ns",
    "fixed_upper",
    "runs",
    "windows",
    "workloads",
    "terminal_attempt_policy",
    "phase_budget",
}
RUN_KEYS = METADATA_KEYS | {"run_id", "workload"}
WINDOW_KEYS = METADATA_KEYS | {
    "window_id",
    "stratum",
    "nominal_wait_s",
    "preceding_run_id",
    "following_run_id",
    "preceding_workload",
    "cell_rep",
}
WORKLOAD_KEYS = METADATA_KEYS | {"W1", "W2"}
ATTEMPT_POLICY_KEYS = METADATA_KEYS | {
    "attempt_with_any_observed_window_is_terminal",
    "resubmissions_after_observation",
    "resubmittable",
    "namespace_observed_attempt_gate_required",
    "scheduler_backed_pre_submit_ledger",
    "enforcement_scope",
}
PHASE_BUDGET_KEYS = METADATA_KEYS | {
    "pbs_setup_cap_s",
    "trace0_configure_cap_s",
    "trace0_build_cap_s",
    "trace1_configure_cap_s",
    "trace1_build_cap_s",
    "adjacency_budget_s",
    "sample_cap_s",
    "driver_cap_s",
    "termination_grace_s",
    "serial_noncontingency_s",
    "serial_sum_expression",
    "serial_with_termination_grace_s",
    "serial_with_grace_expression",
    "absolute_deadline_s",
    "walltime_s",
}


class ContractError(ValueError):
    """The committed contract is not the exact closed schema."""


class DuplicateKeyError(ContractError):
    """A JSON object repeated a key."""


class ProbeTerminated(RuntimeError):
    """The sampler received SIGTERM/SIGINT."""


@dataclass(frozen=True)
class LoadedContract:
    buffer: bytes
    sha256: str
    value: dict[str, Any]


@dataclass(frozen=True)
class ProcStatSnapshot:
    raw_line: str
    values: tuple[int, ...]

    @property
    def first_eight(self) -> tuple[int, ...]:
        return self.values[:8]


@dataclass(frozen=True)
class ProbeDecision:
    window_verdict: str
    window_verdict_reasons: tuple[str, ...]
    trace1_build_witness: str
    compiler_witness: str
    terminal_status: str


def metadata() -> dict[str, Any]:
    return {
        "probe_series_id": PROBE_SERIES_ID,
        "purpose": PURPOSE,
        "study_eligible": STUDY_ELIGIBLE,
    }


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ContractError(
            f"{label} keys differ: missing={sorted(expected - actual)!r}, "
            f"extra={sorted(actual - expected)!r}"
        )


def _require_type(value: Any, expected: type, label: str) -> None:
    if type(value) is not expected:
        raise ContractError(f"{label} must be {expected.__name__}")


def _require_metadata(value: Mapping[str, Any], label: str) -> None:
    if value.get("probe_series_id") != PROBE_SERIES_ID:
        raise ContractError(f"{label}.probe_series_id differs")
    if value.get("purpose") != PURPOSE:
        raise ContractError(f"{label}.purpose differs")
    if value.get("study_eligible") is not False:
        raise ContractError(f"{label}.study_eligible must be false")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_contract(contract: Any) -> dict[str, Any]:
    if type(contract) is not dict:
        raise ContractError("contract root must be an object")
    _require_exact_keys(contract, TOP_LEVEL_KEYS, "contract")
    _require_metadata(contract, "contract")
    if contract["schema_version"] != "t139-r4-env-probe-contract/v1":
        raise ContractError("schema_version differs")
    if contract["physical_cores"] != 48:
        raise ContractError("physical_cores must be 48")
    if contract["counter_names"] != list(COUNTER_NAMES):
        raise ContractError("counter_names differ")
    if contract["window_duration_ns"] != WINDOW_TARGET_NS:
        raise ContractError("window_duration_ns differs")
    if contract["window_tolerance_ns"] != WINDOW_TOLERANCE_NS:
        raise ContractError("window_tolerance_ns differs")
    if contract["max_run_adjacency_ns"] != MAX_ADJACENCY_NS:
        raise ContractError("max_run_adjacency_ns differs")
    if contract["fixed_upper"] != "1.0":
        raise ContractError("fixed_upper must be 1.0")

    runs = contract["runs"]
    _require_type(runs, list, "runs")
    if len(runs) != 13:
        raise ContractError("runs must contain exactly 13 objects")
    expected_workloads = ("W1", "W2", "W2", "W1") * 3 + ("W2",)
    for index, run in enumerate(runs, 1):
        _require_type(run, dict, f"runs[{index - 1}]")
        _require_exact_keys(run, RUN_KEYS, f"runs[{index - 1}]")
        _require_metadata(run, f"runs[{index - 1}]")
        if run["run_id"] != f"R{index:02d}":
            raise ContractError(f"run id {index} differs")
        if run["workload"] != expected_workloads[index - 1]:
            raise ContractError(f"run workload {index} differs")

    windows = contract["windows"]
    _require_type(windows, list, "windows")
    if len(windows) != 13:
        raise ContractError("windows must contain exactly 13 objects")
    for index, window in enumerate(windows):
        _require_type(window, dict, f"windows[{index}]")
        _require_exact_keys(window, WINDOW_KEYS, f"windows[{index}]")
        _require_metadata(window, f"windows[{index}]")
        expected_id = "preflight" if index == 0 else f"post-{index:02d}"
        if window["window_id"] != expected_id:
            raise ContractError(f"window id {index} differs")
        if window["following_run_id"] != f"R{index + 1:02d}":
            raise ContractError(f"following run {index} differs")
        if index == 0:
            if any(
                window[key] is not None
                for key in (
                    "nominal_wait_s",
                    "preceding_run_id",
                    "preceding_workload",
                    "cell_rep",
                )
            ) or window["stratum"] != "preflight":
                raise ContractError("preflight window fields differ")
        else:
            if window["preceding_run_id"] != f"R{index:02d}":
                raise ContractError(f"preceding run {index} differs")
            wait = 30 if index % 4 in (1, 3) else 60
            if window["nominal_wait_s"] != wait:
                raise ContractError(f"nominal wait {index} differs")
            if window["stratum"] != f"wait{wait}":
                raise ContractError(f"stratum {index} differs")
            if window["preceding_workload"] != runs[index - 1]["workload"]:
                raise ContractError(f"preceding workload {index} differs")
            if window["cell_rep"] != (index - 1) // 4 + 1:
                raise ContractError(f"cell rep {index} differs")
    strata = [window["stratum"] for window in windows]
    if strata.count("preflight") != 1 or strata.count("wait30") != 6 or strata.count("wait60") != 6:
        raise ContractError("window strata counts differ")

    workloads = contract["workloads"]
    _require_type(workloads, dict, "workloads")
    _require_exact_keys(workloads, WORKLOAD_KEYS, "workloads")
    _require_metadata(workloads, "workloads")
    if workloads["W1"] != list(W1_ARGV) or workloads["W2"] != list(W2_ARGV):
        raise ContractError("workload argv differs")

    policy = contract["terminal_attempt_policy"]
    _require_type(policy, dict, "terminal_attempt_policy")
    _require_exact_keys(policy, ATTEMPT_POLICY_KEYS, "terminal_attempt_policy")
    _require_metadata(policy, "terminal_attempt_policy")
    if policy["attempt_with_any_observed_window_is_terminal"] is not True:
        raise ContractError("an observed window must make the attempt terminal")
    if policy["resubmissions_after_observation"] != 0:
        raise ContractError("resubmissions_after_observation must be zero")
    if policy["resubmittable"] is not False:
        raise ContractError("resubmittable must be false")
    if policy["namespace_observed_attempt_gate_required"] is not True:
        raise ContractError("the namespace observed-attempt gate must be enabled")
    if policy["scheduler_backed_pre_submit_ledger"] is not False:
        raise ContractError("the probe must not claim a scheduler-backed pre-submit ledger")
    if policy["enforcement_scope"] != "existing_attempt_receipt_or_windows_tsv_observed_rows_only":
        raise ContractError("terminal attempt enforcement scope differs")

    budget = contract["phase_budget"]
    _require_type(budget, dict, "phase_budget")
    _require_exact_keys(budget, PHASE_BUDGET_KEYS, "phase_budget")
    _require_metadata(budget, "phase_budget")
    for key in PHASE_BUDGET_KEYS - METADATA_KEYS - {
        "serial_sum_expression",
        "serial_with_grace_expression",
    }:
        _require_type(budget[key], int, f"phase_budget.{key}")
    if budget["pbs_setup_cap_s"] != 903:
        raise ContractError("PBS setup cap differs")
    if budget["trace0_configure_cap_s"] != 60 or budget["trace0_build_cap_s"] != 180:
        raise ContractError("TRACE=0 caps differ")
    if budget["trace1_configure_cap_s"] != 90 or budget["trace1_build_cap_s"] != 420:
        raise ContractError("TRACE=1 caps differ")
    if budget["adjacency_budget_s"] != 12 * 5 + 5:
        raise ContractError("adjacency budget must be 12 * 5 + 5 = 65 seconds")
    if budget["sample_cap_s"] != 960:
        raise ContractError("sample cap differs")
    if budget["driver_cap_s"] != 2045:
        raise ContractError("driver cap differs")
    if budget["termination_grace_s"] != 120:
        raise ContractError("termination grace differs")
    if budget["serial_noncontingency_s"] != 2948:
        raise ContractError("serial non-contingency total differs")
    if budget["serial_sum_expression"] != "903 + 2045 = 2948 <= 3300 < 3600":
        raise ContractError("serial sum expression differs")
    if budget["serial_with_termination_grace_s"] != 3068:
        raise ContractError("serial total with termination grace differs")
    if (
        budget["serial_with_grace_expression"]
        != "903 + 2045 + 120 = 3068 <= 3300 < 3600"
    ):
        raise ContractError("serial sum with termination grace expression differs")
    if budget["absolute_deadline_s"] != 3300 or budget["walltime_s"] != 3600:
        raise ContractError("absolute deadline or walltime differs")
    if not budget["serial_noncontingency_s"] <= budget["absolute_deadline_s"] < budget["walltime_s"]:
        raise ContractError("phase budget does not fit deadline and walltime")
    return contract


def hash_then_parse_contract(buffer: bytes) -> LoadedContract:
    if type(buffer) is not bytes:
        raise ContractError("contract blob reader must return bytes")
    digest = hashlib.sha256(buffer).hexdigest()
    try:
        decoded = buffer.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"contract JSON is invalid: {exc}") from exc
    return LoadedContract(buffer=buffer, sha256=digest, value=validate_contract(value))


def load_contract_from_reader(reader: Callable[[], bytes]) -> LoadedContract:
    """Read once, then hash and parse the exact returned byte object."""
    buffer = reader()
    return hash_then_parse_contract(buffer)


def load_contract_from_git(repo: Path, commit: str, path: str = CONTRACT_PATH) -> LoadedContract:
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ContractError("expected commit must be 40 lowercase hex digits")

    def read_once() -> bytes:
        completed = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "-C",
                str(repo),
                "cat-file",
                "blob",
                f"{commit}:{path}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.stdout

    return load_contract_from_reader(read_once)


def parse_aggregate_cpu_line(text: str) -> ProcStatSnapshot:
    aggregate = []
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] == "cpu":
            aggregate.append((line, fields[1:]))
    if len(aggregate) != 1:
        raise ValueError(f"expected one aggregate cpu line, found {len(aggregate)}")
    raw_line, fields = aggregate[0]
    if len(fields) < 8:
        raise ValueError("aggregate cpu line has fewer than 8 counters")
    try:
        values = tuple(int(value, 10) for value in fields)
    except ValueError as exc:
        raise ValueError("aggregate cpu line contains a non-integer counter") from exc
    if any(value < 0 for value in values):
        raise ValueError("aggregate cpu line contains a negative raw counter")
    return ProcStatSnapshot(raw_line=raw_line, values=values)


def validate_window_duration(duration_ns: int) -> bool:
    return (
        type(duration_ns) is int
        and WINDOW_TARGET_NS - WINDOW_TOLERANCE_NS
        <= duration_ns
        <= WINDOW_TARGET_NS + WINDOW_TOLERANCE_NS
    )


def validate_run_adjacency(adjacency_ns: int) -> bool:
    return type(adjacency_ns) is int and 0 <= adjacency_ns <= MAX_ADJACENCY_NS


def analyze_window(
    start_text: str,
    end_text: str,
    duration_ns: int,
    adjacency_ns: int | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        **metadata(),
        "status": "malformed",
        "failure_reasons": [],
        "start_raw_line": None,
        "end_raw_line": None,
        "start_values": None,
        "end_values": None,
        "start_extra_values": None,
        "end_extra_values": None,
        "deltas": None,
        "total": None,
        "busy": None,
        "window_duration_ns": duration_ns,
        "window_to_next_exec_ns": adjacency_ns,
    }
    try:
        start = parse_aggregate_cpu_line(start_text)
        result["start_raw_line"] = start.raw_line
        result["start_values"] = list(start.first_eight)
        result["start_extra_values"] = list(start.values[8:])
    except ValueError as exc:
        result["failure_reasons"].append(f"start:{exc}")
        start = None
    try:
        end = parse_aggregate_cpu_line(end_text)
        result["end_raw_line"] = end.raw_line
        result["end_values"] = list(end.first_eight)
        result["end_extra_values"] = list(end.values[8:])
    except ValueError as exc:
        result["failure_reasons"].append(f"end:{exc}")
        end = None
    if not validate_window_duration(duration_ns):
        result["failure_reasons"].append("window_duration_out_of_tolerance")
    if adjacency_ns is None:
        result["failure_reasons"].append("run_adjacency_missing")
    elif not validate_run_adjacency(adjacency_ns):
        result["failure_reasons"].append("run_adjacency_out_of_range")
    if start is not None and end is not None:
        deltas = [after - before for before, after in zip(start.first_eight, end.first_eight)]
        result["deltas"] = deltas
        if any(delta < 0 for delta in deltas):
            result["failure_reasons"].append("counter_decreased")
        total = sum(deltas)
        result["total"] = total
        result["busy"] = total - deltas[3]
        if total <= 0:
            result["failure_reasons"].append("total_not_positive")
    if not result["failure_reasons"]:
        result["status"] = "valid"
    return result


def _exact_int_list(value: Any, expected: Sequence[int]) -> bool:
    return (
        type(value) is list
        and len(value) == len(expected)
        and all(type(item) is int for item in value)
        and value == list(expected)
    )


def _window_raw_counter_reason(window: Mapping[str, Any], window_id: str) -> str | None:
    start_raw = window.get("start_raw_line")
    end_raw = window.get("end_raw_line")
    if type(start_raw) is not str or type(end_raw) is not str:
        return f"window_raw_counter_missing:{window_id}"
    try:
        start = parse_aggregate_cpu_line(start_raw)
        end = parse_aggregate_cpu_line(end_raw)
    except ValueError:
        return f"window_raw_counter_invalid:{window_id}"
    deltas = tuple(after - before for before, after in zip(start.first_eight, end.first_eight))
    total = sum(deltas)
    busy = total - deltas[3]
    exact_fields = (
        _exact_int_list(window.get("start_values"), start.first_eight),
        _exact_int_list(window.get("end_values"), end.first_eight),
        _exact_int_list(window.get("start_extra_values"), start.values[8:]),
        _exact_int_list(window.get("end_extra_values"), end.values[8:]),
        _exact_int_list(window.get("deltas"), deltas),
        type(window.get("total")) is int and window.get("total") == total,
        type(window.get("busy")) is int and window.get("busy") == busy,
    )
    if not all(exact_fields):
        return f"window_raw_counter_mismatch:{window_id}"
    if any(delta < 0 for delta in deltas) or total <= 0 or busy < 0:
        return f"window_raw_counter_invalid:{window_id}"
    return None


def _derive_window_verdict(
    windows: Sequence[Mapping[str, Any]],
    expected_window_ids: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    if len(windows) != len(expected_window_ids):
        return "incomplete", ("window_count_mismatch",)
    by_id: dict[str, Mapping[str, Any]] = {}
    for window in windows:
        window_id = window.get("window_id")
        if type(window_id) is not str:
            return "incomplete", ("window_id_invalid",)
        if window_id in by_id:
            return "incomplete", (f"window_id_duplicate:{window_id}",)
        by_id[window_id] = window
    if set(by_id) != set(expected_window_ids):
        return "incomplete", ("window_id_set_mismatch",)
    ordered = [by_id[window_id] for window_id in expected_window_ids]
    status_reasons: list[str] = []
    for window_id, window in zip(expected_window_ids, ordered):
        if window.get("status") == "valid":
            continue
        reasons = window.get("failure_reasons")
        if (
            type(reasons) is list
            and reasons
            and all(type(reason) is str for reason in reasons)
        ):
            status_reasons.extend(f"{reason}:{window_id}" for reason in reasons)
        else:
            status_reasons.append(f"window_status_not_valid:{window_id}")
    if status_reasons:
        return "incomplete", tuple(status_reasons)
    pairs: list[tuple[int, int]] = []
    raw_reasons: list[str] = []
    for window_id, window in zip(expected_window_ids, ordered):
        raw_reason = _window_raw_counter_reason(window, window_id)
        if raw_reason is not None:
            raw_reasons.append(raw_reason)
            continue
        busy = window.get("busy")
        total = window.get("total")
        assert type(busy) is int and type(total) is int
        pairs.append((busy, total))
    if raw_reasons:
        return "incomplete", tuple(raw_reasons)
    if all(48 * busy <= total for busy, total in pairs):
        return "feasible", ()
    return "not_feasible", ()


def derive_decision(
    windows: Sequence[Mapping[str, Any]],
    expected_window_ids: Sequence[str],
    *,
    runs_ok: bool,
    trace0_build_ok: bool,
    trace1_build_witness: str,
    compiler_witness: str,
    driver_signaled: bool = False,
) -> ProbeDecision:
    """Derive the three independent measurement faces and overall terminal state."""
    witness_values = {"present", "failed", "not_attempted"}
    if trace1_build_witness not in witness_values:
        raise ValueError("trace1 build witness is outside the closed set")
    if compiler_witness not in witness_values:
        raise ValueError("compiler witness is outside the closed set")
    window_verdict, reasons = _derive_window_verdict(windows, expected_window_ids)
    if (
        driver_signaled
        or window_verdict == "incomplete"
        or not runs_ok
        or not trace0_build_ok
        or trace1_build_witness != "present"
        or compiler_witness != "present"
    ):
        terminal_status = "incomplete"
    else:
        terminal_status = window_verdict
    return ProbeDecision(
        window_verdict=window_verdict,
        window_verdict_reasons=reasons,
        trace1_build_witness=trace1_build_witness,
        compiler_witness=compiler_witness,
        terminal_status=terminal_status,
    )


def parse_cmake_cache_exact(text: str, expected: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, expected_value in expected.items():
        prefix = f"{key}:STRING="
        matches = [line for line in text.splitlines() if line.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"CMakeCache key {key} occurs {len(matches)} times")
        value = matches[0][len(prefix) :]
        if value != expected_value:
            raise ValueError(f"CMakeCache key {key} is {value!r}, expected {expected_value!r}")
        result[key] = value
    return result


def validate_compile_argv(argv: Sequence[str], *, trace: int, analysis: int) -> None:
    if trace not in (0, 1) or analysis not in (0, 1):
        raise ValueError("trace and analysis must be zero or one")
    checks = {
        "-DTRACE=": f"-DTRACE={trace}",
        "-DADD_ANALYSIS=": f"-DADD_ANALYSIS={analysis}",
    }
    for prefix, exact in checks.items():
        matches = [arg for arg in argv if arg.startswith(prefix)]
        if matches != [exact]:
            raise ValueError(f"compile argv {prefix} values differ: {matches!r}")
    for prefix in ("-DIZANAGI_T139_PC_MODE1=", "-DIZANAGI_T139_PC_MODEX="):
        if any(arg.startswith(prefix) for arg in argv):
            raise ValueError(f"stock compile argv contains {prefix}")


def select_compile_argvs(compile_commands: Any) -> dict[str, list[str]]:
    if type(compile_commands) is not list:
        raise ValueError("compile_commands root must be a list")
    targets = {
        "transaction": ("/cc/silo/transaction.cc", "/CMakeFiles/ycsb_silo.exe.dir/transaction.cc.o"),
        "result": ("/common/result.cc", None),
        "util": ("/common/util.cc", None),
    }
    matches: dict[str, list[list[str]]] = {name: [] for name in targets}
    for entry in compile_commands:
        if type(entry) is not dict:
            raise ValueError("compile command entry must be an object")
        if "arguments" in entry:
            argv = entry["arguments"]
            if type(argv) is not list or not all(type(arg) is str for arg in argv):
                raise ValueError("compile command must contain string arguments")
        else:
            command = entry.get("command")
            if type(command) is not str:
                raise ValueError(
                    "compile command must contain an arguments list or command string"
                )
            if not command:
                raise ValueError("compile command string must not be empty")
            try:
                argv = shlex.split(command)
            except ValueError as exc:
                raise ValueError("compile command string cannot be split") from exc
            if not argv:
                raise ValueError("compile command string must split to non-empty arguments")
        directory = entry.get("directory")
        source = entry.get("file")
        if type(directory) is not str or type(source) is not str:
            raise ValueError("compile command directory/file must be strings")
        source_path = os.path.realpath(os.path.join(directory, source))
        output = entry.get("output")
        if output is None:
            output_args = [argv[index + 1] for index, arg in enumerate(argv[:-1]) if arg == "-o"]
            if len(output_args) != 1:
                raise ValueError("compile command must have exactly one output")
            output = output_args[0]
        if type(output) is not str:
            raise ValueError("compile output must be a string")
        output_path = os.path.realpath(os.path.join(directory, output))
        for name, (source_suffix, output_suffix) in targets.items():
            if source_path.endswith(source_suffix) and (
                output_suffix is None or output_path.endswith(output_suffix)
            ):
                matches[name].append(list(argv))
    result: dict[str, list[str]] = {}
    for name, found in matches.items():
        if len(found) != 1:
            raise ValueError(f"{name} compile entries: {len(found)}")
        result[name] = found[0]
    return result


def validate_build_artifacts(
    cache_text: str,
    compile_commands: Any,
    *,
    trace: int,
    analysis: int,
) -> dict[str, Any]:
    cache = parse_cmake_cache_exact(
        cache_text,
        {
            "CCBENCH_TRACE": str(trace),
            "CCBENCH_ADD_ANALYSIS": str(analysis),
        },
    )
    selected = select_compile_argvs(compile_commands)
    for argv in selected.values():
        validate_compile_argv(argv, trace=trace, analysis=analysis)
    return {**metadata(), "cache": cache, "selected_compile_argv": selected}


def compare_compiler_identity(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> list[str]:
    fields = (
        "command_v",
        "command_v_raw_b64",
        "realpath",
        "version_stdout_b64",
        "version_stderr_b64",
        "version_stdout_sha256",
        "version_stderr_sha256",
        "executable_sha256",
        "size_bytes",
    )
    return [field for field in fields if expected.get(field) != observed.get(field)]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_compiler_identity(command: str) -> dict[str, Any]:
    located = subprocess.run(
        ["/bin/sh", "-c", 'command -v -- "$1"', "_", command],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    command_v_lines = located.stdout.decode("utf-8", "strict").splitlines()
    if located.returncode != 0 or len(command_v_lines) != 1 or not command_v_lines[0]:
        raise ValueError(f"command -v equivalent did not find {command}")
    command_v = command_v_lines[0]
    resolved = subprocess.run(
        ["realpath", "-e", "--", command_v],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    realpath_lines = resolved.stdout.decode("utf-8", "strict").splitlines()
    if resolved.returncode != 0 or len(realpath_lines) != 1 or not os.path.isabs(realpath_lines[0]):
        raise ValueError(f"realpath -e failed for {command}")
    realpath = Path(realpath_lines[0])
    completed = subprocess.run(
        [str(realpath), "--version"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(f"{command} --version returned {completed.returncode}")
    return {
        **metadata(),
        "command": command,
        "command_v": command_v,
        "command_v_raw_b64": base64.b64encode(located.stdout).decode("ascii"),
        "realpath": str(realpath),
        "version_stdout_b64": base64.b64encode(completed.stdout).decode("ascii"),
        "version_stderr_b64": base64.b64encode(completed.stderr).decode("ascii"),
        "version_stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "version_stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "executable_sha256": _sha256_file(realpath),
        "size_bytes": realpath.stat().st_size,
    }


def expected_configure_argv(
    *,
    source: str,
    build: str,
    prefix: str,
    third_party: str,
    gflags_pin: str,
    glog_pin: str,
    gcc_realpath: str,
    gxx_realpath: str,
    trace: int,
    analysis: int,
) -> list[str]:
    for value in (source, build, prefix, third_party, gcc_realpath, gxx_realpath):
        if not os.path.isabs(value):
            raise ValueError("configure paths must be absolute")
    return [
        "cmake",
        "-S",
        source,
        "-B",
        build,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCCBENCH_TRACE={trace}",
        "-DCCBENCH_BACK_OFF=0",
        "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0",
        "-DCCBENCH_CCACHE=OFF",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_C_COMPILER_LAUNCHER=",
        "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=",
        "-DCMAKE_TOOLCHAIN_FILE=",
        f"-DCMAKE_PREFIX_PATH={prefix}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={third_party}/masstree",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={third_party}/mimalloc",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={third_party}/googletest",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={gflags_pin}",
        f"-DIZANAGI_GLOG_SRC_HEAD={glog_pin}",
        f"-DCMAKE_C_COMPILER={gcc_realpath}",
        f"-DCMAKE_CXX_COMPILER={gxx_realpath}",
        f"-DCCBENCH_ADD_ANALYSIS={analysis}",
        "-DCMAKE_CXX_FLAGS=",
    ]


def _decorate_objects(value: Any) -> Any:
    if isinstance(value, dict):
        decorated = {key: _decorate_objects(item) for key, item in value.items()}
        for key, item in metadata().items():
            decorated.setdefault(key, item)
        return decorated
    if isinstance(value, list):
        return [_decorate_objects(item) for item in value]
    return value


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(_decorate_objects(value), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _artifact(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {**metadata(), "path": str(path), "exists": False, "size_bytes": None, "sha256": None}
    return {
        **metadata(),
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _safe_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def capture_environment_diagnostics() -> dict[str, Any]:
    nodefile = os.environ.get("PBS_NODEFILE")
    module_list = os.environ.get("IZANAGI_MODULE_LIST_PATH")
    source_witness = os.environ.get("IZANAGI_SOURCE_WITNESS_PATH")
    status = _safe_text(Path("/proc/self/status")) or ""
    cgroup = _safe_text(Path("/proc/self/cgroup"))
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    foreign: list[dict[str, Any]] = []
    proc = Path("/proc")
    own_pid = os.getpid()
    try:
        for child in sorted(proc.iterdir(), key=lambda item: item.name):
            if not child.name.isdigit() or int(child.name) == own_pid:
                continue
            comm = _safe_text(child / "comm")
            cmdline = None
            try:
                cmdline = (child / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
            except OSError:
                pass
            foreign.append(
                {
                    **metadata(),
                    "pid": int(child.name),
                    "comm": comm.rstrip("\n") if comm is not None else None,
                    "cmdline": cmdline,
                }
            )
            if len(foreign) >= 512:
                break
    except OSError:
        pass
    cpuset: dict[str, Any] = {}
    for path in (
        Path("/sys/fs/cgroup/cpuset.cpus.effective"),
        Path("/sys/fs/cgroup/cpu.max"),
        Path("/sys/fs/cgroup/cpuset/cpuset.cpus"),
    ):
        cpuset[str(path)] = _safe_text(path)
    return {
        **metadata(),
        "diagnostics_only": True,
        "hostname": socket.gethostname(),
        "pbs_nodefile_path": nodefile,
        "pbs_nodefile_text": _safe_text(Path(nodefile)) if nodefile else None,
        "module_list": _artifact(Path(module_list)) if module_list else None,
        "source_witness": _artifact(Path(source_witness)) if source_witness else None,
        "affinity": affinity,
        "cpus_allowed_list": re.findall(r"^Cpus_allowed_list:\s*(.+)$", status, re.MULTILINE),
        "cgroup_text": cgroup,
        "cgroup_files": cpuset,
        "pid_visibility_canary": {
            **metadata(),
            "self_pid": own_pid,
            "self_proc_visible": Path(f"/proc/{own_pid}").is_dir(),
            "pid1_visible": Path("/proc/1").is_dir(),
        },
        "foreign_process_count": len(foreign),
        "foreign_process_snapshot": foreign,
    }


def _placeholder_window(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **metadata(),
        **{key: spec[key] for key in WINDOW_KEYS - METADATA_KEYS},
        "observed": False,
        "status": "not_observed",
        "failure_reasons": ["not_observed"],
        "wait_start_monotonic_ns": None,
        "wait_end_monotonic_ns": None,
        "start_read_begin_ns": None,
        "start_read_end_ns": None,
        "start_sample_ns": None,
        "end_read_begin_ns": None,
        "end_read_end_ns": None,
        "end_sample_ns": None,
        "window_duration_ns": None,
        "wait_duration_ns": None,
        "wait_end_deviation_ns": None,
        "window_to_next_exec_ns": None,
        "start_raw_line": None,
        "end_raw_line": None,
        "start_values": None,
        "end_values": None,
        "start_extra_values": None,
        "end_extra_values": None,
        "deltas": None,
        "total": None,
        "busy": None,
        "load1_start": None,
        "load1_end": None,
        "foreign_process_count_start": None,
        "foreign_process_count_end": None,
    }


def _placeholder_run(spec: Mapping[str, Any], index: int) -> dict[str, Any]:
    return {
        **metadata(),
        "run_id": spec["run_id"],
        "role": "terminal_follower" if index == 12 else "measured_predecessor",
        "workload": spec["workload"],
        "argv": [],
        "binary_sha256": None,
        "started_monotonic_ns": None,
        "exec_monotonic_ns": None,
        "finished_monotonic_ns": None,
        "elapsed_ns": None,
        "returncode": None,
        "timed_out": False,
        "flags_match": False,
        "status": "not_observed",
        "log": None,
    }


def new_state(
    contract: LoadedContract,
    *,
    commit: str,
    jobid: str,
    expected_contract_sha256: str | None = None,
) -> dict[str, Any]:
    value = contract.value
    expected_digest = expected_contract_sha256 or contract.sha256
    try:
        environment = capture_environment_diagnostics()
    except BaseException as exc:
        environment = {
            **metadata(),
            "diagnostics_only": True,
            "capture_error": f"{type(exc).__name__}:{exc}",
        }
    return {
        **metadata(),
        "schema_version": "t139-r4-env-probe-state/v1",
        "contract_sha256": contract.sha256,
        "contract_digest_reads": {
            **metadata(),
            "contract_load_sha256": expected_digest,
            "init_state_sha256": contract.sha256,
            "exact_match": expected_digest == contract.sha256,
        },
        "contract": value,
        "run_commit": commit,
        "job": {
            **metadata(),
            "pbs_jobid": jobid,
            "hostname": socket.gethostname(),
            "queue": "gen_S",
            "walltime_s": value["phase_budget"]["walltime_s"],
            "absolute_deadline_s": value["phase_budget"]["absolute_deadline_s"],
            "started_epoch_ns": time.time_ns(),
            "started_monotonic_ns": time.monotonic_ns(),
            "finished_epoch_ns": None,
            "finished_monotonic_ns": None,
        },
        "environment": environment,
        "compilers": {**metadata(), "gcc": None, "gxx": None, "identity_rechecks": []},
        "builds": [
            {
                **metadata(),
                "kind": "trace0",
                "trace": 0,
                "add_analysis": 0,
                "status": "not_observed",
                "returncode": None,
                "configure_elapsed_ns": None,
                "build_elapsed_ns": None,
                "configure_argv": [],
                "validation": None,
                "configure_log": None,
                "build_log": None,
                "binary": None,
            },
            {
                **metadata(),
                "kind": "trace1",
                "trace": 1,
                "add_analysis": 1,
                "status": "not_observed",
                "returncode": None,
                "configure_elapsed_ns": None,
                "build_elapsed_ns": None,
                "configure_argv": [],
                "validation": None,
                "configure_log": None,
                "build_log": None,
                "binary": None,
            },
        ],
        "runs": [_placeholder_run(spec, index) for index, spec in enumerate(value["runs"])],
        "windows": [_placeholder_window(spec) for spec in value["windows"]],
        "failure_reasons": [],
    }


def initialize_state(
    contract_path: Path,
    state_path: Path,
    *,
    commit: str,
    jobid: str,
    expected_contract_sha256: str,
    contract_metadata_path: Path,
) -> bool:
    """Create a complete state even when the staged contract cannot be trusted."""
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ContractError("run commit must be 40 lowercase hex digits")
    if re.fullmatch(r"[0-9a-f]{64}", expected_contract_sha256) is None:
        raise ContractError("expected contract digest must be 64 lowercase hex digits")
    try:
        staged_buffer = contract_path.read_bytes()
        staged_digest = hashlib.sha256(staged_buffer).hexdigest()
        loaded = hash_then_parse_contract(staged_buffer)
        state = new_state(
            loaded,
            commit=commit,
            jobid=jobid,
            expected_contract_sha256=expected_contract_sha256,
        )
        if staged_digest != expected_contract_sha256:
            state["failure_reasons"].append("contract_digest_mismatch:contract-load:init-state")
            _write_json_atomic(state_path, state)
            return False
        _write_json_atomic(state_path, state)
        return True
    except BaseException as exc:
        staged_digest = None
        try:
            staged_digest = hashlib.sha256(contract_path.read_bytes()).hexdigest()
        except OSError:
            pass
        metadata_value = _read_json(contract_metadata_path)
        fallback_value = validate_contract(metadata_value["validated_contract"])
        fallback = LoadedContract(
            buffer=b"",
            sha256=staged_digest or "unreadable",
            value=fallback_value,
        )
        state = new_state(
            fallback,
            commit=commit,
            jobid=jobid,
            expected_contract_sha256=expected_contract_sha256,
        )
        state["contract_digest_reads"]["init_state_sha256"] = staged_digest
        state["contract_digest_reads"]["exact_match"] = False
        state["failure_reasons"].append(
            f"init_state_exception:{type(exc).__name__}:{exc}"
        )
        _write_json_atomic(state_path, state)
        return False


def _load_proc_endpoint() -> dict[str, Any]:
    load1 = Path("/proc/loadavg").read_text(encoding="utf-8").split()[0]
    foreign_count = max(
        0, sum(1 for item in Path("/proc").iterdir() if item.name.isdigit()) - 1
    )
    begin = time.monotonic_ns()
    text = Path("/proc/stat").read_text(encoding="utf-8")
    end = time.monotonic_ns()
    return {
        "begin_ns": begin,
        "end_ns": end,
        "sample_ns": (begin + end) // 2,
        "text": text,
        "load1": load1,
        "foreign_count": foreign_count,
    }


def _sleep_until(target_ns: int) -> None:
    while True:
        remaining = target_ns - time.monotonic_ns()
        if remaining <= 0:
            return
        time.sleep(remaining / 1_000_000_000)


def _sample_window_targets(start_target_ns: int, end_target_ns: int) -> tuple[dict[str, Any], dict[str, Any]]:
    _sleep_until(start_target_ns)
    start = _load_proc_endpoint()
    _sleep_until(end_target_ns)
    end = _load_proc_endpoint()
    return start, end


def _set_window_observed(
    state: dict[str, Any],
    index: int,
    start: Mapping[str, Any],
    end: Mapping[str, Any],
    *,
    wait_start_ns: int | None,
    wait_end_ns: int,
    adjacency_ns: int | None,
) -> None:
    analysis = analyze_window(
        str(start["text"]),
        str(end["text"]),
        int(end["sample_ns"]) - int(start["sample_ns"]),
        adjacency_ns,
    )
    wait_end_deviation_ns = int(end["sample_ns"]) - wait_end_ns
    if abs(wait_end_deviation_ns) > WINDOW_TOLERANCE_NS:
        analysis["failure_reasons"].append("wait_end_deviation_out_of_range")
        analysis["status"] = "malformed"
    spec_fields = {key: state["windows"][index][key] for key in WINDOW_KEYS - METADATA_KEYS}
    state["windows"][index] = {
        **metadata(),
        **spec_fields,
        **analysis,
        "observed": True,
        "wait_start_monotonic_ns": wait_start_ns,
        "wait_end_monotonic_ns": wait_end_ns,
        "wait_duration_ns": (
            None if wait_start_ns is None else int(end["sample_ns"]) - wait_start_ns
        ),
        "wait_end_deviation_ns": wait_end_deviation_ns,
        "start_read_begin_ns": start["begin_ns"],
        "start_read_end_ns": start["end_ns"],
        "start_sample_ns": start["sample_ns"],
        "end_read_begin_ns": end["begin_ns"],
        "end_read_end_ns": end["end_ns"],
        "end_sample_ns": end["sample_ns"],
        "load1_start": start["load1"],
        "load1_end": end["load1"],
        "foreign_process_count_start": start["foreign_count"],
        "foreign_process_count_end": end["foreign_count"],
    }


def _parse_flag_map(log_text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in log_text.splitlines():
        match = re.fullmatch(r"#FLAGS_([A-Za-z0-9_]+):\s*(\S+)\s*", line)
        if match:
            key = match.group(1)
            if key in result:
                raise ValueError(f"duplicate #FLAGS_{key}")
            result[key] = match.group(2)
    return result


def validate_run_log(log_text: str, workload: str) -> None:
    expected = {
        "clocks_per_us": "2100",
        "epoch_time": "40",
        "extime": "3",
        "thread_num": "48",
        "ycsb_max_ope": "10",
        "ycsb_rmw": "1" if workload == "W1" else "0",
        "ycsb_rratio": "50",
        "ycsb_tuple_num": "10000" if workload == "W1" else "100000",
        "ycsb_zipf_skew": "0.9" if workload == "W1" else "0.5",
    }
    actual = _parse_flag_map(log_text)
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ValueError("effective #FLAGS_ map differs")
    expected_options = (
        "#ShowOptParameters(): ADD_ANALYSIS 0: BACK_OFF 0: KEY_SIZE 8: "
        "MASSTREE_USE 1: NO_WAIT_LOCKING_IN_VALIDATION 1: PARTITION_TABLE 0: "
        "PROCEDURE_SORT 0: SLEEP_READ_PHASE 0: VAL_SIZE 4: WAL 0"
    )
    if log_text.splitlines().count(expected_options) != 1:
        raise ValueError("ShowOptParameters map differs")


def run_schedule(state_path: Path, binary: Path, output: Path) -> int:
    state = _read_json(state_path)
    contract = validate_contract(state["contract"])
    binary = binary.resolve(strict=True)
    binary_sha = _sha256_file(binary)
    terminated = False
    active_process: subprocess.Popen[bytes] | None = None
    active_run: dict[str, Any] | None = None
    pending_window_index: int | None = None
    pending_start: Mapping[str, Any] | None = None
    pending_end: Mapping[str, Any] | None = None
    pending_wait_start_ns: int | None = None
    pending_wait_end_ns: int | None = None
    pending_window_persisted = False

    def on_signal(signum: int, _frame: Any) -> None:
        nonlocal terminated
        terminated = True
        raise ProbeTerminated(f"signal:{signum}")

    old_handlers = {
        signum: signal.signal(signum, on_signal) for signum in (signal.SIGTERM, signal.SIGINT)
    }

    def persist_pending_window(adjacency_ns: int | None) -> None:
        nonlocal pending_window_persisted
        if pending_window_persisted or pending_window_index is None:
            return
        assert pending_start is not None and pending_end is not None
        assert pending_wait_end_ns is not None
        _set_window_observed(
            state,
            pending_window_index,
            pending_start,
            pending_end,
            wait_start_ns=pending_wait_start_ns,
            wait_end_ns=pending_wait_end_ns,
            adjacency_ns=adjacency_ns,
        )
        _write_json_atomic(state_path, state)
        pending_window_persisted = True

    try:
        preceding_finished: int | None = None
        for index, run_spec in enumerate(contract["runs"]):
            workload = run_spec["workload"]
            argv = list(contract["workloads"][workload])
            log_path = output / f"run-{run_spec['run_id']}.log"
            timed_out = False
            with log_path.open("wb") as log_handle:
                if index == 0:
                    start_target = time.monotonic_ns()
                    end_target = start_target + WINDOW_TARGET_NS
                    wait_start_ns = None
                else:
                    assert preceding_finished is not None
                    wait_s = int(contract["windows"][index]["nominal_wait_s"])
                    start_target = preceding_finished + (wait_s - 10) * 1_000_000_000
                    end_target = preceding_finished + wait_s * 1_000_000_000
                    wait_start_ns = preceding_finished
                pending_start, pending_end = _sample_window_targets(start_target, end_target)
                pending_window_index = index
                pending_wait_start_ns = wait_start_ns
                pending_wait_end_ns = end_target
                pending_window_persisted = False
                started = time.monotonic_ns()
                active_run = {
                    "index": index,
                    "run_id": run_spec["run_id"],
                    "workload": workload,
                    "argv": argv,
                    "started_monotonic_ns": started,
                    "exec_monotonic_ns": None,
                    "log_path": log_path,
                }
                try:
                    active_process = subprocess.Popen(
                        [str(binary), *argv],
                        stdout=log_handle,
                        stderr=subprocess.STDOUT,
                    )
                    exec_monotonic_ns = time.monotonic_ns()
                    active_run["exec_monotonic_ns"] = exec_monotonic_ns
                    persist_pending_window(
                        exec_monotonic_ns - int(pending_end["sample_ns"])
                    )
                    returncode = active_process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    active_process.terminate()
                    try:
                        active_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        active_process.kill()
                        active_process.wait()
                    returncode = 124
                    timed_out = True
                active_process = None
            finished = time.monotonic_ns()
            flags_match = False
            if returncode == 0:
                try:
                    validate_run_log(log_path.read_text(encoding="utf-8"), workload)
                    flags_match = True
                except (OSError, UnicodeError, ValueError):
                    flags_match = False
            state["runs"][index] = {
                **metadata(),
                "run_id": run_spec["run_id"],
                "role": "terminal_follower" if index == 12 else "measured_predecessor",
                "workload": workload,
                "argv": argv,
                "binary_sha256": binary_sha,
                "started_monotonic_ns": started,
                "exec_monotonic_ns": exec_monotonic_ns,
                "finished_monotonic_ns": finished,
                "elapsed_ns": finished - started,
                "returncode": returncode,
                "timed_out": timed_out,
                "flags_match": flags_match,
                "status": "success" if returncode == 0 and flags_match else "failed",
                "log": _artifact(log_path),
            }
            active_run = None
            _write_json_atomic(state_path, state)
            if returncode != 0 or not flags_match:
                state["failure_reasons"].append(f"first_run_failure:{run_spec['run_id']}")
                _write_json_atomic(state_path, state)
                return 12
            preceding_finished = finished
        return 0
    except ProbeTerminated as exc:
        if active_process is not None and active_process.poll() is None:
            active_process.terminate()
            try:
                active_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                active_process.kill()
                active_process.wait()
        persist_pending_window(None)
        if active_run is not None:
            finished = time.monotonic_ns()
            index = int(active_run["index"])
            state["runs"][index] = {
                **metadata(),
                "run_id": active_run["run_id"],
                "role": "terminal_follower" if index == 12 else "measured_predecessor",
                "workload": active_run["workload"],
                "argv": active_run["argv"],
                "binary_sha256": binary_sha,
                "started_monotonic_ns": active_run["started_monotonic_ns"],
                "exec_monotonic_ns": active_run["exec_monotonic_ns"],
                "finished_monotonic_ns": finished,
                "elapsed_ns": finished - int(active_run["started_monotonic_ns"]),
                "returncode": 143,
                "timed_out": False,
                "flags_match": False,
                "status": "failed",
                "log": _artifact(Path(active_run["log_path"])),
            }
            state["failure_reasons"].append(f"first_run_failure:{active_run['run_id']}")
        state["failure_reasons"].append(str(exc))
        _write_json_atomic(state_path, state)
        return 143 if terminated else 12
    except BaseException as exc:
        persist_pending_window(None)
        state["failure_reasons"].append(f"sampler_exception:{type(exc).__name__}:{exc}")
        _write_json_atomic(state_path, state)
        return 12
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)


def record_build(
    state_path: Path,
    *,
    kind: str,
    status: str,
    returncode: int,
    configure_elapsed_ns: int,
    build_elapsed_ns: int,
    configure_argv: list[str],
    configure_log: Path,
    build_log: Path,
    cache_path: Path | None,
    compile_commands_path: Path | None,
    binary_path: Path | None,
) -> None:
    state = _read_json(state_path)
    index = {"trace0": 0, "trace1": 1}[kind]
    trace = index
    analysis = index
    validation = None
    final_status = status
    reasons: list[str] = []
    if status == "success":
        try:
            if cache_path is None or compile_commands_path is None or binary_path is None:
                raise ValueError("successful build is missing artifacts")
            cache_text = cache_path.read_text(encoding="utf-8")
            compile_commands = _read_json(compile_commands_path)
            validation = validate_build_artifacts(
                cache_text, compile_commands, trace=trace, analysis=analysis
            )
            if not binary_path.is_file() or not os.access(binary_path, os.X_OK):
                raise ValueError("prebuilt binary is absent or not executable")
        except (OSError, UnicodeError, ValueError) as exc:
            final_status = "failed"
            reasons.append(f"artifact_validation:{exc}")
    state["builds"][index] = {
        **metadata(),
        "kind": kind,
        "trace": trace,
        "add_analysis": analysis,
        "status": final_status,
        "returncode": returncode,
        "failure_reasons": reasons,
        "configure_elapsed_ns": configure_elapsed_ns,
        "build_elapsed_ns": build_elapsed_ns,
        "configure_argv": configure_argv,
        "validation": validation,
        "configure_log": _artifact(configure_log),
        "build_log": _artifact(build_log),
        "cache": _artifact(cache_path) if cache_path is not None else None,
        "compile_commands": _artifact(compile_commands_path) if compile_commands_path is not None else None,
        "binary": _artifact(binary_path) if binary_path is not None else None,
        "source_witness": state["environment"].get("source_witness"),
    }
    if final_status != "success":
        state["failure_reasons"].append(f"build_failed:{kind}:rc={returncode}")
    _write_json_atomic(state_path, state)


def _tsv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _write_tsv_atomic(
    path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _tsv_value(row.get(field)) for field in fields})
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _create_completed_marker(path: Path, decision: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        os.write(descriptor, f"{decision}\n".encode("ascii"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _build_witness_status(build: Mapping[str, Any]) -> str:
    status = build.get("status")
    if status == "success":
        return "present"
    if status == "not_observed":
        return "not_attempted"
    return "failed"


def _compiler_witness_status(compilers: Mapping[str, Any]) -> str:
    checks = compilers.get("identity_rechecks")
    baseline_present = isinstance(compilers.get("gcc"), dict) and isinstance(
        compilers.get("gxx"), dict
    )
    if not baseline_present or type(checks) is not list or not checks:
        return "not_attempted"
    return "present" if compiler_rechecks_ok(compilers) else "failed"


def finalize(state_path: Path, output: Path, *, exit_rc: int = 0) -> str:
    state = _read_json(state_path)
    contract = validate_contract(state["contract"])
    termination_signal = {130: "INT", 143: "TERM"}.get(exit_rc)
    if termination_signal is not None:
        reason = f"driver_signal:{termination_signal}"
        if reason not in state["failure_reasons"]:
            state["failure_reasons"].append(reason)
    trace0_build_ok = (
        len(state["builds"]) == 2 and state["builds"][0].get("status") == "success"
    )
    trace1_build_witness = (
        _build_witness_status(state["builds"][1])
        if len(state["builds"]) == 2
        else "not_attempted"
    )
    compiler_witness = _compiler_witness_status(state["compilers"])
    for index, build in enumerate(state["builds"]):
        if build.get("status") != "not_observed":
            continue
        kind = ("trace0", "trace1")[index]
        configure_log = output / f"configure-{kind}.log"
        build_log = output / f"build-{kind}.log"
        configure_argv_path = output / f"configure-{kind}.argv.json"
        configure_argv: list[str] = []
        try:
            candidate_argv = _read_json(configure_argv_path)
            if type(candidate_argv) is list and all(type(item) is str for item in candidate_argv):
                configure_argv = candidate_argv
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        state["builds"][index] = {
            **build,
            "status": "failed",
            "returncode": exit_rc or 12,
            "failure_reasons": ["finalized_before_build_record"],
            "configure_argv": configure_argv,
            "configure_log": _artifact(configure_log),
            "build_log": _artifact(build_log),
        }
        state["failure_reasons"].append(f"build_failed:{kind}:rc={exit_rc or 12}")
    expected_ids = [item["window_id"] for item in contract["windows"]]
    runs_ok = len(state["runs"]) == 13 and all(
        run.get("status") == "success" and run.get("returncode") == 0 and run.get("flags_match") is True
        for run in state["runs"]
    )
    decision = derive_decision(
        state["windows"],
        expected_ids,
        runs_ok=runs_ok,
        trace0_build_ok=trace0_build_ok,
        trace1_build_witness=trace1_build_witness,
        compiler_witness=compiler_witness,
        driver_signaled=termination_signal is not None,
    )
    state["job"]["finished_epoch_ns"] = time.time_ns()
    state["job"]["finished_monotonic_ns"] = time.monotonic_ns()
    observed_count = sum(window.get("observed") is True for window in state["windows"])
    receipt_failure_reasons = list(state.get("failure_reasons", []))
    for reason in decision.window_verdict_reasons:
        if reason not in receipt_failure_reasons:
            receipt_failure_reasons.append(reason)
    receipt = {
        **metadata(),
        "schema_version": "t139-r4-env-probe-receipt/v1",
        "scope": "non_study_environment_probe",
        "window_verdict": decision.window_verdict,
        "window_verdict_reasons": list(decision.window_verdict_reasons),
        "trace1_build_witness": decision.trace1_build_witness,
        "compiler_witness": decision.compiler_witness,
        "terminal_status": decision.terminal_status,
        "failure_reasons": receipt_failure_reasons,
        "driver_exit": {
            **metadata(),
            "returncode": exit_rc,
            "signal": termination_signal,
            "signal_identity_best_effort": True,
            "signal_identity_limitation": (
                "group-TERM may be recorded as the current stage failure code"
            ),
        },
        "resubmittable": False,
        "attempt_terminal": observed_count > 0,
        "guarantee_scope": {
            **metadata(),
            "sigterm_finalization_attempted": True,
            "sigkill_excluded": True,
            "completion_requires_marker": "COMPLETED",
            "rerun_gate": "existing receipt/windows.tsv observed rows in this namespace",
            "scheduler_backed_pre_submit_ledger": False,
        },
        "provenance": {
            **metadata(),
            "run_commit": state["run_commit"],
            "contract": {
                **metadata(),
                "path": CONTRACT_PATH,
                "sha256": state["contract_sha256"],
                "digest_reads": state.get("contract_digest_reads"),
            },
        },
        "job": state["job"],
        "environment": state["environment"],
        "compilers": state["compilers"],
        "builds": state["builds"],
        "runs": state["runs"],
        "windows": state["windows"],
        "derivation": {
            **metadata(),
            "expected_window_ids": expected_ids,
            "valid_ids": [window["window_id"] for window in state["windows"] if window.get("status") == "valid"],
            "malformed_ids": [window["window_id"] for window in state["windows"] if window.get("status") == "malformed"],
            "not_observed_ids": [window["window_id"] for window in state["windows"] if window.get("status") == "not_observed"],
            "window_verdict": decision.window_verdict,
            "window_verdict_reasons": list(decision.window_verdict_reasons),
            "trace1_build_witness": decision.trace1_build_witness,
            "compiler_witness": decision.compiler_witness,
            "terminal_status": decision.terminal_status,
            "fixed_upper": "1.0",
            "integer_comparisons": ["48*busy<=total"],
            "tps_used": False,
        },
    }
    common = ["probe_series_id", "purpose", "study_eligible"]
    _write_tsv_atomic(
        output / "windows.tsv",
        common
        + [
            "window_id",
            "stratum",
            "nominal_wait_s",
            "preceding_run_id",
            "following_run_id",
            "preceding_workload",
            "cell_rep",
            "observed",
            "status",
            "failure_reasons",
            "wait_start_monotonic_ns",
            "wait_end_monotonic_ns",
            "start_read_begin_ns",
            "start_read_end_ns",
            "start_sample_ns",
            "end_read_begin_ns",
            "end_read_end_ns",
            "end_sample_ns",
            "window_duration_ns",
            "wait_duration_ns",
            "wait_end_deviation_ns",
            "window_to_next_exec_ns",
            "start_raw_line",
            "end_raw_line",
            "start_values",
            "end_values",
            "start_extra_values",
            "end_extra_values",
            "deltas",
            "total",
            "busy",
            "load1_start",
            "load1_end",
            "foreign_process_count_start",
            "foreign_process_count_end",
        ],
        state["windows"],
    )
    _write_tsv_atomic(
        output / "runs.tsv",
        common
        + [
            "run_id",
            "role",
            "workload",
            "argv",
            "binary_sha256",
            "started_monotonic_ns",
            "exec_monotonic_ns",
            "finished_monotonic_ns",
            "elapsed_ns",
            "returncode",
            "timed_out",
            "flags_match",
            "status",
            "log",
        ],
        state["runs"],
    )
    _write_tsv_atomic(
        output / "builds.tsv",
        common
        + [
            "kind",
            "trace",
            "add_analysis",
            "status",
            "returncode",
            "failure_reasons",
            "configure_elapsed_ns",
            "build_elapsed_ns",
            "configure_argv",
            "configure_log",
            "build_log",
            "cache",
            "compile_commands",
            "binary",
            "source_witness",
        ],
        state["builds"],
    )
    _write_json_atomic(output / "receipt.json", receipt)
    _create_completed_marker(output / "COMPLETED", decision.terminal_status)
    return decision.terminal_status


def _record_compilers(state_path: Path, output: Path) -> None:
    state = _read_json(state_path)
    for key, command in (("gcc", "gcc"), ("gxx", "g++")):
        identity = capture_compiler_identity(command)
        command_v_path = output / f"compiler-{key}-command-v.stdout"
        stdout_path = output / f"compiler-{key}-version.stdout"
        stderr_path = output / f"compiler-{key}-version.stderr"
        command_v_path.write_bytes(base64.b64decode(identity["command_v_raw_b64"]))
        stdout_path.write_bytes(base64.b64decode(identity["version_stdout_b64"]))
        stderr_path.write_bytes(base64.b64decode(identity["version_stderr_b64"]))
        identity["command_v_raw"] = _artifact(command_v_path)
        identity["version_stdout_raw"] = _artifact(stdout_path)
        identity["version_stderr_raw"] = _artifact(stderr_path)
        state["compilers"][key] = identity
    _write_json_atomic(state_path, state)


def _recheck_compilers(state_path: Path, label: str) -> bool:
    state = _read_json(state_path)
    matches = True
    for key, command in (("gcc", "gcc"), ("gxx", "g++")):
        observed = capture_compiler_identity(command)
        differences = compare_compiler_identity(state["compilers"][key], observed)
        state["compilers"]["identity_rechecks"].append(
            {
                **metadata(),
                "label": label,
                "compiler": key,
                "match": not differences,
                "differences": differences,
                "observed": observed,
                "monotonic_ns": time.monotonic_ns(),
            }
        )
        matches = matches and not differences
    if not matches:
        state["failure_reasons"].append(f"compiler_identity_drift:{label}")
    _write_json_atomic(state_path, state)
    return matches


def compiler_rechecks_ok(compilers: Mapping[str, Any]) -> bool:
    if not isinstance(compilers.get("gcc"), dict) or not isinstance(compilers.get("gxx"), dict):
        return False
    checks = compilers.get("identity_rechecks")
    if type(checks) is not list:
        return False
    expected = {
        (f"{position}-{kind}", compiler)
        for kind in ("trace0", "trace1")
        for position in ("before-configure", "before-build", "after-build")
        for compiler in ("gcc", "gxx")
    }
    observed: set[tuple[str, str]] = set()
    for check in checks:
        if type(check) is not dict or check.get("match") is not True:
            return False
        key = (check.get("label"), check.get("compiler"))
        if key in observed:
            return False
        observed.add(key)
    return observed == expected


def attempt_namespace_allows_start(namespace: Path) -> bool:
    """Reject a rerun after any prior receipt/TSV records an observed window.

    This is deliberately only an on-node namespace scan.  It is not a
    scheduler-backed pre-submit ledger and cannot exclude a concurrently
    starting job that has not published an observed row yet.
    """
    if not namespace.exists():
        return True
    if namespace.is_symlink() or not namespace.is_dir():
        raise ValueError("probe namespace must be a real directory")
    for attempt in sorted(namespace.iterdir(), key=lambda path: path.name):
        if attempt.is_symlink() or not attempt.is_dir():
            raise ValueError(f"unexpected namespace entry: {attempt}")
        receipt_path = attempt / "receipt.json"
        windows_path = attempt / "windows.tsv"
        if receipt_path.is_symlink() or windows_path.is_symlink():
            raise ValueError(f"attempt witness is a symlink: {attempt}")
        if receipt_path.exists():
            receipt = _read_json(receipt_path)
            windows = receipt.get("windows")
            if (
                type(windows) is not list
                or len(windows) != 13
                or any(type(row) is not dict or type(row.get("observed")) is not bool for row in windows)
            ):
                raise ValueError(f"receipt windows are malformed: {receipt_path}")
            if any(row["observed"] is True for row in windows):
                return False
        if windows_path.exists():
            with windows_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                if reader.fieldnames is None or "observed" not in reader.fieldnames:
                    raise ValueError(f"windows TSV is malformed: {windows_path}")
                rows = list(reader)
            if len(rows) != 13 or any(row.get("observed") not in {"true", "false"} for row in rows):
                raise ValueError(f"windows TSV rows are malformed: {windows_path}")
            if any(row["observed"] == "true" for row in rows):
                return False
    return True


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    load = subparsers.add_parser("contract-load")
    load.add_argument("--repo", type=Path, required=True)
    load.add_argument("--commit", required=True)
    load.add_argument("--path", default=CONTRACT_PATH)
    load.add_argument("--output", type=Path, required=True)
    load.add_argument("--metadata-output", type=Path, required=True)

    init = subparsers.add_parser("init-state")
    init.add_argument("--contract", type=Path, required=True)
    init.add_argument("--state", type=Path, required=True)
    init.add_argument("--commit", required=True)
    init.add_argument("--jobid", required=True)
    init.add_argument("--expected-contract-sha256", required=True)
    init.add_argument("--contract-metadata", type=Path, required=True)

    capture = subparsers.add_parser("capture-compilers")
    capture.add_argument("--state", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)

    recheck = subparsers.add_parser("recheck-compilers")
    recheck.add_argument("--state", type=Path, required=True)
    recheck.add_argument("--label", required=True)

    build = subparsers.add_parser("record-build")
    build.add_argument("--state", type=Path, required=True)
    build.add_argument("--kind", choices=("trace0", "trace1"), required=True)
    build.add_argument("--status", choices=("success", "failed"), required=True)
    build.add_argument("--returncode", type=int, required=True)
    build.add_argument("--configure-elapsed-ns", type=int, required=True)
    build.add_argument("--build-elapsed-ns", type=int, required=True)
    build.add_argument("--configure-argv-json", type=Path, required=True)
    build.add_argument("--configure-log", type=Path, required=True)
    build.add_argument("--build-log", type=Path, required=True)
    build.add_argument("--cache", type=Path)
    build.add_argument("--compile-commands", type=Path)
    build.add_argument("--binary", type=Path)

    sample = subparsers.add_parser("sample")
    sample.add_argument("--state", type=Path, required=True)
    sample.add_argument("--binary", type=Path, required=True)
    sample.add_argument("--output", type=Path, required=True)

    finish = subparsers.add_parser("finalize")
    finish.add_argument("--state", type=Path, required=True)
    finish.add_argument("--output", type=Path, required=True)
    finish.add_argument("--exit-rc", type=int, default=0)

    gate = subparsers.add_parser("attempt-gate")
    gate.add_argument("--namespace", type=Path, required=True)

    subparsers.add_parser("monotonic-ns")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "contract-load":
        loaded = load_contract_from_git(args.repo.resolve(strict=True), args.commit, args.path)
        args.output.write_bytes(loaded.buffer)
        _write_json_atomic(
            args.metadata_output,
            {
                **metadata(),
                "path": args.path,
                "sha256": loaded.sha256,
                "size_bytes": len(loaded.buffer),
                "validated_contract": loaded.value,
                "digest_stage": "contract-load",
            },
        )
        print(loaded.sha256)
        return 0
    if args.command == "init-state":
        return 0 if initialize_state(
            args.contract,
            args.state,
            commit=args.commit,
            jobid=args.jobid,
            expected_contract_sha256=args.expected_contract_sha256,
            contract_metadata_path=args.contract_metadata,
        ) else 14
    if args.command == "capture-compilers":
        _record_compilers(args.state, args.output)
        return 0
    if args.command == "recheck-compilers":
        return 0 if _recheck_compilers(args.state, args.label) else 13
    if args.command == "record-build":
        configure_argv = _read_json(args.configure_argv_json)
        if type(configure_argv) is not list or not all(type(item) is str for item in configure_argv):
            raise ValueError("configure argv JSON must be an array of strings")
        record_build(
            args.state,
            kind=args.kind,
            status=args.status,
            returncode=args.returncode,
            configure_elapsed_ns=args.configure_elapsed_ns,
            build_elapsed_ns=args.build_elapsed_ns,
            configure_argv=configure_argv,
            configure_log=args.configure_log,
            build_log=args.build_log,
            cache_path=args.cache,
            compile_commands_path=args.compile_commands,
            binary_path=args.binary,
        )
        return 0
    if args.command == "sample":
        return run_schedule(args.state, args.binary, args.output)
    if args.command == "finalize":
        decision = finalize(args.state, args.output, exit_rc=args.exit_rc)
        print(decision)
        return 12 if decision == "incomplete" else 0
    if args.command == "attempt-gate":
        return 0 if attempt_namespace_allows_start(args.namespace) else 14
    if args.command == "monotonic-ns":
        print(time.monotonic_ns())
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
