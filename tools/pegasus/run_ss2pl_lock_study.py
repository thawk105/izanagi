#!/usr/bin/env python3
"""Run the descriptive SS2PL lock study on one Pegasus compute node.

The canonical CCBench submodule is read-only.  A network-free local clone is
patched and built below ``--scratch-root``.  Every published receipt describes
exactly one PBS occasion and one node; cross-node pooling is deliberately not
part of this schema.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Iterator, Mapping, Sequence
import uuid

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from orchestrator.campaign import condition_meaning_gate  # noqa: E402


SCHEMA_VERSION = "ss2pl-lock-study/v1"
PERFORMANCE_ARMS = ("S", "C", "A", "B", "D")
THREADS = (1, 2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48)
SWEEP_BLOCKS = 5
REPLICATION_BLOCKS = 3
ARM_CONFIG: dict[str, dict[str, int]] = {
    "S": {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0},
    "C": {"impl": 1, "kind": 1, "dlr": 1, "wfg": 0},
    "A": {"impl": 1, "kind": 0, "dlr": 1, "wfg": 0},
    "B": {"impl": 1, "kind": 0, "dlr": 2, "wfg": 0},
    "D": {"impl": 1, "kind": 1, "dlr": 2, "wfg": 0},
    "phase1": {"impl": 1, "kind": 0, "dlr": 0, "wfg": 1},
    "phase2": {"impl": 1, "kind": 0, "dlr": 1, "wfg": 1},
}
AXIS_CACHE_KEYS = {
    "impl": "CCBENCH_SS2PL_LOCK_IMPL",
    "kind": "CCBENCH_SS2PL_LOCK_KIND",
    "dlr": "CCBENCH_SS2PL_DLR",
    "wfg": "CCBENCH_SS2PL_WFG_DIAG",
}
AXIS_DEFAULTS = {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0}
CACHE_TO_DEFINE = {
    "CCBENCH_SS2PL_LOCK_IMPL": "SS2PL_LOCK_IMPL",
    "CCBENCH_SS2PL_LOCK_KIND": "SS2PL_LOCK_KIND",
    "CCBENCH_SS2PL_DLR": "SS2PL_DLR",
    "CCBENCH_SS2PL_WFG_DIAG": "SS2PL_WFG_DIAG",
    "CCBENCH_VAL_SIZE": "VAL_SIZE",
    "CCBENCH_BACK_OFF": "BACK_OFF",
    "CCBENCH_TRACE": "TRACE",
    "CCBENCH_KEY_SORT": "KEY_SORT",
}
WORKLOAD_DEFAULT = {
    "ycsb_tuple_num": 1_000_000,
    "ycsb_rratio": 50,
    "ycsb_rmw": 0,
    "ycsb_zipf_skew": 0.9,
    "ycsb_max_ope": 10,
}
WFG_DIAGNOSTIC_IDENTIFIERS = (
    "ss2pl_wfg_snapshot",
    "ss2pl_wfg_registry",
    "ss2pl_wfg_watchdog",
    "wait_for_graph",
    "WaitForGraph",
    "WfgRegistry",
    "WfgSnapshot",
    "WfgWatchdog",
)
WFG_AXIS_LITERAL = '": SS2PL_WFG_DIAG "'
WFG_AXIS_BINARY_STRING = ": SS2PL_WFG_DIAG "
STUDY_LOCK_AXIS_LITERAL = '": SS2PL_LOCK_IMPL "'
STUDY_LOCK_HEADER = "cc/ss2pl/include/ss2pl_study_lock.hh"
INERT_DECLARED_DIFFERENCES: dict[str, str] = {
    "cc/ss2pl/bomb_ss2pl.cc": (
        "common.hh no longer defines the legacy workload flags included by this TU; "
        "its direct changes remain inside #if SS2PL_WFG_DIAG"
    ),
    "cc/ss2pl/transaction.cc": (
        "removed TxExecutor::abort()'s duplicate local_abort_counts_ increment and "
        "one leading blank line"
    ),
    "cc/ss2pl/util.cc": (
        "removed legacy workload-flag output, made chkArg() use ycsb_rratio, and "
        "printed the four build axes required by ruling 3.11"
    ),
}
WORKLOAD_ABORT_INCREMENT_COUNT = 2
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ACTIVE_STAGE_DEADLINES: list["StageDeadline"] = []
REQUIRED_EXTERNAL_COMMANDS = (
    "git", "cmake", "cc", "c++", "make", "as", "ld", "ar", "ranlib", "nm", "strings",
)


class ContractError(RuntimeError):
    """The experiment no longer matches the preregistered acceptance set."""


def _uncollected_observation(exc: BaseException) -> dict[str, Any]:
    return {
        "collected": False,
        "failure": {"type": type(exc).__name__, "message": str(exc)},
    }


class StageDeadline:
    """A monotonic inner deadline for one preregistered harness stage."""

    def __init__(self, name: str, cap_s: float):
        if cap_s <= 0:
            raise ContractError(f"{name} stage cap must be positive")
        self.name = name
        self.cap_s = float(cap_s)
        self.started = time.monotonic()
        self.deadline = self.started + self.cap_s

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ContractError(f"{self.name} stage deadline exceeded ({self.cap_s:g}s)")
        return remaining

    def check(self) -> None:
        self.remaining()


@contextlib.contextmanager
def _stage_deadline(
    document: dict[str, Any], name: str, cap_s: float
) -> Iterator[StageDeadline]:
    deadline = StageDeadline(name, cap_s)
    _ACTIVE_STAGE_DEADLINES.append(deadline)
    try:
        yield deadline
        deadline.check()
    finally:
        ended = time.monotonic()
        document["stage_deadlines"][name] = {
            "cap_s": deadline.cap_s,
            "started_monotonic_s": deadline.started,
            "ended_monotonic_s": ended,
            "duration_s": ended - deadline.started,
            "within_deadline": ended <= deadline.deadline,
        }
        popped = _ACTIVE_STAGE_DEADLINES.pop()
        if popped is not deadline:
            raise RuntimeError("stage deadline stack corruption")


def _bounded_timeout(requested: float | None) -> tuple[float | None, StageDeadline | None]:
    if not _ACTIVE_STAGE_DEADLINES:
        return requested, None
    stage = _ACTIVE_STAGE_DEADLINES[-1]
    remaining = stage.remaining()
    if requested is None or remaining < requested:
        return remaining, stage
    return requested, None


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    text = str(value).strip()
    if text.upper() in {"ON", "TRUE", "YES"}:
        return "1"
    if text.upper() in {"OFF", "FALSE", "NO"}:
        return "0"
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return format(number, ".12g")


def validate_workload_binding(
    requested: Mapping[str, Any], observed: Mapping[str, Any]
) -> None:
    missing = sorted(set(requested) - set(observed))
    mismatches = {
        key: {"requested": requested[key], "observed": observed.get(key)}
        for key in requested
        if key in observed
        and _canonical_scalar(requested[key]) != _canonical_scalar(observed[key])
    }
    if missing or mismatches:
        raise ContractError(
            f"runtime workload binding mismatch: missing={missing}, mismatches={mismatches}"
        )


def validate_build_binding(
    expected_axes: Mapping[str, Any], observed_axes: Mapping[str, Any]
) -> None:
    missing = sorted(set(expected_axes) - set(observed_axes))
    mismatches = {
        key: {"expected": expected_axes[key], "observed": observed_axes.get(key)}
        for key in expected_axes
        if key in observed_axes
        and _canonical_scalar(expected_axes[key])
        != _canonical_scalar(observed_axes[key])
    }
    if missing or mismatches:
        raise ContractError(
            f"runtime build binding mismatch: missing={missing}, mismatches={mismatches}"
        )


def _wfg_text_hits(text: str) -> list[str]:
    hits = {
        token for token in WFG_DIAGNOSTIC_IDENTIFIERS
        if token.lower() in text.lower()
    }
    if re.search(r"(?i)(?:wfg|wait[_ -]?for[_ -]?graph)", text):
        hits.add("generic-wfg-identifier")
    return sorted(hits)


def _function_name_before_brace(tokens: Sequence[str], brace_index: int) -> str | None:
    if brace_index == 0 or tokens[brace_index - 1] != ")":
        return None
    depth = 0
    for index in range(brace_index - 1, -1, -1):
        if tokens[index] == ")":
            depth += 1
        elif tokens[index] == "(":
            depth -= 1
            if depth == 0:
                if index == 0 or not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", tokens[index - 1]):
                    return None
                return tokens[index - 1]
    return None


def _literal_function_locations(tokens: Sequence[str], literal: str) -> list[str | None]:
    contexts: list[str | None] = []
    locations: list[str | None] = []
    for index, token in enumerate(tokens):
        if token == "{":
            contexts.append(_function_name_before_brace(tokens, index))
        elif token == "}":
            if contexts:
                contexts.pop()
        elif token == literal:
            locations.append(next((name for name in reversed(contexts) if name), None))
    return locations


def _validated_preprocess_cost(row: Mapping[str, Any], context: str) -> dict[str, Any]:
    integer_fields = ("preprocessed_bytes", "token_count")
    duration_fields = (
        "preprocess_duration_s", "tokenize_duration_s", "request_duration_s",
    )
    missing = sorted(
        set(integer_fields + duration_fields + ("cache_hit",)) - set(row)
    )
    if missing:
        raise ContractError(f"preprocessing cost receipt is incomplete for {context}: {missing}")
    costs: dict[str, Any] = {}
    for field in integer_fields:
        value = row[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ContractError(
                f"preprocessing cost receipt has invalid {field} for {context}: {value}"
            )
        costs[field] = value
    for field in duration_fields:
        try:
            value = float(row[field])
        except (TypeError, ValueError) as exc:
            raise ContractError(
                f"preprocessing cost receipt has invalid {field} for {context}"
            ) from exc
        if not math.isfinite(value) or value < 0:
            raise ContractError(
                f"preprocessing cost receipt has invalid {field} for {context}: {value}"
            )
        costs[field] = value
    if not isinstance(row["cache_hit"], bool):
        raise ContractError(
            f"preprocessing cost receipt has invalid cache_hit for {context}"
        )
    costs["cache_hit"] = row["cache_hit"]
    for field in (
        "cache_key_sha256", "compile_argv_sha256", "directory_sha256",
        "source_path_sha256", "source_content_sha256", "source_state_sha256",
        "scan_config_sha256",
    ):
        if field in row:
            value = str(row[field])
            if not _HASH_RE.fullmatch(value):
                raise ContractError(
                    f"preprocessing cost receipt has invalid {field} for {context}"
                )
            costs[field] = value
    return costs


def validate_wfg_absence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact one-label exception and no other WFG material."""
    required = {
        "source_list", "symbols", "strings", "preprocessed",
        "checked_translation_units",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise ContractError(f"WFG absence gate failed: missing={missing}")

    sources = evidence["source_list"]
    preprocessed = evidence["preprocessed"]
    if not isinstance(sources, list) or not sources:
        raise ContractError("WFG absence gate failed: compile entry population is empty")
    source_names = [str(source) for source in sources]
    if len(source_names) != len(set(source_names)):
        raise ContractError("WFG absence gate failed: compile entry sources are not unique")
    if not isinstance(preprocessed, list) or not preprocessed:
        raise ContractError("WFG absence gate failed: preprocessed receipt population is empty")
    checked = int(evidence["checked_translation_units"])
    if checked != len(source_names) or len(preprocessed) != len(source_names):
        raise ContractError(
            "WFG absence gate failed: checked TU, preprocessed receipt, and source counts differ"
        )

    source_hits = {source: _wfg_text_hits(source) for source in source_names}
    source_hits = {source: hits for source, hits in source_hits.items() if hits}
    symbols_text = (
        "\n".join(str(item) for item in evidence["symbols"])
        if isinstance(evidence["symbols"], list) else str(evidence["symbols"])
    )
    symbol_hits = _wfg_text_hits(symbols_text)

    string_lines = (
        [str(item) for item in evidence["strings"]]
        if isinstance(evidence["strings"], list)
        else str(evidence["strings"]).splitlines()
    )
    allowed_binary_count = sum(line == WFG_AXIS_BINARY_STRING for line in string_lines)
    string_hits = [
        {"line": line, "hits": _wfg_text_hits(line)}
        for line in string_lines
        if line != WFG_AXIS_BINARY_STRING and _wfg_text_hits(line)
    ]

    preprocessed_by_source: dict[str, Mapping[str, Any]] = {}
    preprocessed_hits: list[dict[str, Any]] = []
    allowed_locations: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for row in preprocessed:
        if not isinstance(row, Mapping) or not isinstance(row.get("source"), str):
            raise ContractError("WFG absence gate failed: malformed preprocessed receipt")
        source = str(row["source"])
        text = row.get("text")
        token_scan = row.get("token_scan")
        if (
            source in preprocessed_by_source or source not in source_names
            or (not isinstance(text, str) and not isinstance(token_scan, Mapping))
        ):
            raise ContractError("WFG absence gate failed: preprocessed source identity mismatch")
        preprocessed_by_source[source] = row
        observed_sha = str(row.get("sha256", ""))
        if isinstance(text, str):
            encoded = text.encode("utf-8", "surrogateescape")
            expected_sha = _sha256_bytes(encoded)
        else:
            expected_sha = str(token_scan.get("preprocessed_sha256", ""))
        if observed_sha != expected_sha:
            raise ContractError("WFG absence gate failed: preprocessed SHA256 mismatch")
        if not isinstance(token_scan, Mapping):
            token_scan = _scan_cpp_tokens(encoded)
        if str(token_scan.get("preprocessed_sha256", "")) != expected_sha:
            raise ContractError("WFG absence gate failed: token scan source SHA256 mismatch")
        costs = _validated_preprocess_cost(row, source)
        if int(token_scan.get("token_count", -1)) != costs["token_count"]:
            raise ContractError("WFG absence gate failed: token count receipt mismatch")
        functions = token_scan.get("wfg_axis_literal_functions")
        identifier_hits = token_scan.get("wfg_identifier_hits")
        literal_hits = token_scan.get("wfg_literal_hits")
        if (
            not isinstance(functions, list)
            or not isinstance(identifier_hits, list)
            or not isinstance(literal_hits, list)
        ):
            raise ContractError("WFG absence gate failed: malformed token scan receipt")
        locations = list(functions)
        for function in locations:
            allowed_locations.append({"source": source, "function": function})
        if identifier_hits or literal_hits:
            preprocessed_hits.append({
                "source": source,
                "identifiers": sorted(str(item) for item in identifier_hits),
                "literals": sorted(str(item) for item in literal_hits),
            })
        receipts.append({"source": source, "sha256": expected_sha, **costs})

    expected_location = [{
        "source": next(
            (source for source in source_names if source.replace("\\", "/").endswith("cc/ss2pl/util.cc")),
            "",
        ),
        "function": "ShowOptParameters",
    }]
    population_ok = set(preprocessed_by_source) == set(source_names)
    if (
        source_hits or symbol_hits or string_hits or preprocessed_hits
        or allowed_binary_count != 1 or not population_ok
        or allowed_locations != expected_location or not expected_location[0]["source"]
    ):
        raise ContractError(
            "WFG absence gate failed: "
            f"source_hits={source_hits}, symbol_hits={symbol_hits}, "
            f"binary_label_count={allowed_binary_count}, string_hits={string_hits}, "
            f"preprocessed_hits={preprocessed_hits}, population_ok={population_ok}, "
            f"allowed_locations={allowed_locations}, expected_location={expected_location}"
        )
    return {
        "checked_translation_units": checked,
        "source_files": source_names,
        "preprocessed": receipts,
        "symbols_sha256": _sha256_bytes(symbols_text.encode()),
        "strings_sha256": _sha256_bytes("\n".join(string_lines).encode()),
        "allowed_axis_label": {
            "binary_string": WFG_AXIS_BINARY_STRING,
            "binary_count": allowed_binary_count,
            "source": expected_location[0]["source"],
            "function": "ShowOptParameters",
            "token_count": 1,
        },
    }


def canonical_abort_metrics(
    abort_count: int, commit_count: int, displayed_abort_rate: float | None
) -> dict[str, Any]:
    if abort_count < 0 or commit_count < 0 or abort_count + commit_count <= 0:
        raise ContractError("abort accounting counters must be nonnegative and nonempty")
    rate = abort_count / (abort_count + commit_count)
    if displayed_abort_rate is not None and not math.isclose(
        rate, displayed_abort_rate, rel_tol=5e-4, abs_tol=5e-5
    ):
        raise ContractError(
            "displayed abort rate does not match the single workload-owned abort counter"
        )
    return {
        "abort_count": abort_count,
        "commit_count": commit_count,
        "abort_rate": rate,
        "accounting": "single workload-owned abort count",
    }


def validate_matrix(
    runs: Sequence[Mapping[str, Any]],
    *,
    arms: Sequence[str],
    threads: Sequence[int],
    blocks: Sequence[int],
    experiment: str | None = None,
) -> None:
    selected = [run for run in runs if experiment is None or run.get("experiment") == experiment]
    actual = [(str(r["arm"]), int(r["thread_num"]), int(r["block_id"])) for r in selected]
    expected = [(arm, thread, block) for block in blocks for thread in threads for arm in arms]
    if len(actual) != len(set(actual)):
        raise ContractError("duplicate (arm, thread, block) performance cell")
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        raise ContractError(f"performance matrix mismatch: missing={missing}, extra={extra}")


def validate_control_matrices(runs: Sequence[Mapping[str, Any]]) -> None:
    experiments = {str(run.get("experiment")) for run in runs}
    if experiments != {"E1", "E2"}:
        raise ContractError(f"control performance experiments must be exactly E1/E2: {experiments}")
    e1_actual = []
    for run in runs:
        if run.get("experiment") != "E1":
            continue
        workload = run.get("workload", {})
        e1_actual.append((
            str(run["arm"]), int(run["thread_num"]), int(run["block_id"]),
            int(workload["ycsb_rratio"]), _canonical_scalar(workload["ycsb_zipf_skew"]),
        ))
    e1_expected = [
        (arm, thread, block, ratio, _canonical_scalar(skew))
        for block in range(3)
        for skew in (0, 0.9)
        for ratio in (0, 50, 100)
        for thread in (24, 48)
        for arm in PERFORMANCE_ARMS
    ]
    if len(e1_actual) != len(set(e1_actual)):
        raise ContractError("duplicate E1 control cell")
    if set(e1_actual) != set(e1_expected):
        missing = sorted(set(e1_expected) - set(e1_actual))
        extra = sorted(set(e1_actual) - set(e1_expected))
        raise ContractError(f"E1 control matrix mismatch: missing={missing}, extra={extra}")
    validate_matrix(
        runs, arms=("B", "D"), threads=(1, 24, 48), blocks=range(3), experiment="E2"
    )


def validate_phase_matrix(runs: Sequence[Mapping[str, Any]]) -> None:
    actual = [(str(run.get("phase")), str(run.get("point")), int(run.get("trial", -1))) for run in runs]
    expected = [
        (phase, point, trial)
        for phase in ("phase1", "phase2")
        for point in ("high-contention", "headline")
        for trial in range(3)
    ]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ContractError("phase1/phase2 trial matrix is incomplete or duplicated")
    for run in runs:
        if run["phase"] == "phase2":
            if run.get("timed_out") is not False or int(run.get("returncode", -1)) != 0:
                raise ContractError("phase2 trial did not complete normally within the hard timeout")
            if not isinstance(run.get("phase2_counters"), Mapping):
                raise ContractError("phase2 trial counters are missing")
            counters = run["phase2_counters"]
            if int(counters.get("conflict_count", 0)) <= 0:
                raise ContractError("phase2 trial has no observed lock conflict")
            if int(counters.get("no_wait_failure_count", 0)) <= 0:
                raise ContractError("phase2 trial has no observed No-Wait failure")
            paths = counters.get("acquisition_paths")
            if not isinstance(paths, Mapping) or not paths:
                raise ContractError("phase2 trial acquisition-path observations are empty")


def validate_single_occasion(document: Mapping[str, Any]) -> None:
    occasion = document.get("occasion")
    if not isinstance(occasion, Mapping):
        raise ContractError("occasion object is required")
    identity = (
        occasion.get("occasion_id"), occasion.get("pbs_jobid"), occasion.get("node")
    )
    if not all(isinstance(item, str) and item for item in identity):
        raise ContractError("occasion_id, pbs_jobid, and node must be nonempty strings")
    for collection in ("performance_runs", "phase_runs"):
        for run in document.get(collection, []):
            run_identity = (run.get("occasion_id"), run.get("pbs_jobid"), run.get("node"))
            if run_identity != identity:
                raise ContractError(
                    f"{collection} silently crosses occasion or node: {run_identity} != {identity}"
                )


def validate_positive_throughputs(runs: Sequence[Mapping[str, Any]]) -> None:
    for index, run in enumerate(runs):
        try:
            value = float(run["metrics"]["throughput_tps"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(f"performance run {index} lacks numeric throughput") from exc
        if not math.isfinite(value) or value <= 0:
            raise ContractError(
                f"performance run {index} throughput must be finite and positive: {value}"
            )


def validate_mode_document(document: Mapping[str, Any], expected_mode: str) -> None:
    """Run the final gates used by both collection and plotting admission."""
    mode = str(document.get("mode", ""))
    if mode != expected_mode:
        raise ContractError(f"receipt mode mismatch: {mode} != {expected_mode}")
    runs = document.get("performance_runs")
    if not isinstance(runs, list):
        raise ContractError("performance run collection is missing")
    validate_single_occasion(document)
    validate_isolation_records(document.get("isolation_observations", []))
    validate_positive_throughputs(runs)
    if expected_mode in {"sweep", "replication"}:
        experiments = {str(run.get("experiment")) for run in runs}
        if experiments != {expected_mode}:
            raise ContractError(f"performance receipt contains out-of-mode experiments: {experiments}")
        blocks = range(SWEEP_BLOCKS if expected_mode == "sweep" else REPLICATION_BLOCKS)
        validate_matrix(
            runs, arms=PERFORMANCE_ARMS, threads=THREADS,
            blocks=blocks, experiment=expected_mode,
        )
    elif expected_mode == "controls":
        validate_control_matrices(runs)
        phase_runs = document.get("phase_runs")
        if not isinstance(phase_runs, list):
            raise ContractError("phase run collection is missing")
        validate_phase_matrix(phase_runs)
    else:
        raise ContractError(f"unsupported study mode: {expected_mode}")


def validate_isolation_records(records: Sequence[Mapping[str, Any]]) -> None:
    scopes = [str(record.get("scope", "")) for record in records]
    if "job_before" not in scopes:
        raise ContractError("job-before isolation observation is missing")
    block_scopes: dict[str, set[str]] = {}
    for record in records:
        scope = str(record.get("scope", ""))
        block = record.get("block_attempt_id")
        if block is not None and scope in {"block_before", "block_after"}:
            block_scopes.setdefault(str(block), set()).add(scope)
        for field in ("uptime", "proc_loadavg", "other_user_cpu_processes"):
            if field not in record:
                raise ContractError(f"isolation observation lacks {field}")
    incomplete = sorted(key for key, value in block_scopes.items() if value != {"block_before", "block_after"})
    if incomplete:
        raise ContractError(f"isolation block observations are incomplete: {incomplete}")


def validate_patch_cleanup(cleanup: Mapping[str, Any]) -> None:
    if not cleanup.get("reverse_attempted") or not cleanup.get("reverse_succeeded"):
        raise ContractError("patch reverse was not completed")
    if cleanup.get("git_status_porcelain") != "":
        raise ContractError("scratch clone is dirty after patch reverse")


def validate_preprocessing_receipts(document: Mapping[str, Any]) -> None:
    witness = document.get("inert_witness")
    if not isinstance(witness, Mapping):
        raise ContractError("inert witness preprocessing receipt is missing")
    validate_inert_witness_receipt(witness)
    if witness["collected"]:
        units = witness.get("translation_units")
        if not isinstance(units, list) or not units:
            raise ContractError("inert witness preprocessing TU receipts are missing")
        for index, unit in enumerate(units):
            if not isinstance(unit, Mapping):
                raise ContractError(f"inert witness preprocessing TU {index} is malformed")
            for state in ("baseline", "patched"):
                cost = unit.get(f"{state}_preprocessing")
                if not isinstance(cost, Mapping):
                    raise ContractError(
                        f"inert witness {state} preprocessing cost is missing for TU {index}"
                    )
                _validated_preprocess_cost(cost, f"inert witness TU {index} {state}")

    builds = document.get("builds")
    if not isinstance(builds, list):
        raise ContractError("performance build preprocessing receipts are missing")
    performance = [
        build
        for build in builds
        if isinstance(build, Mapping) and str(build.get("arm")) in PERFORMANCE_ARMS
    ]
    if {str(build.get("arm")) for build in performance} != set(PERFORMANCE_ARMS):
        raise ContractError(
            "performance build preprocessing receipts do not cover all performance arms"
        )
    for build_index, build in enumerate(performance):
        arm = str(build.get("arm"))
        absence = build.get("wfg_absence")
        rows = absence.get("preprocessed") if isinstance(absence, Mapping) else None
        if not isinstance(rows, list) or not rows:
            raise ContractError(
                f"performance build {build_index}/{arm} preprocessing costs are missing"
            )
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ContractError(
                    f"performance build {build_index}/{arm} preprocessing cost row {index} "
                    "is malformed"
                )
            _validated_preprocess_cost(
                row, f"performance build {build_index}/{arm} TU {index}"
            )


def validate_completed_receipt(document: Mapping[str, Any], expected_mode: str) -> None:
    """Admission contract for a completed, cleaned receipt consumer."""
    validate_preprocessing_receipts(document)
    validate_patch_cleanup(document.get("cleanup", {}))
    validate_mode_document(document, expected_mode)


def _run_checked(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    effective_timeout, limiting_stage = _bounded_timeout(timeout)
    try:
        completed = subprocess.run(
            list(argv), cwd=cwd, env=None if env is None else dict(env),
            capture_output=True, text=text, timeout=effective_timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        if limiting_stage is not None:
            raise ContractError(
                f"{limiting_stage.name} stage deadline exceeded while running {shlex.join(argv)}"
            ) from exc
        raise ContractError(f"command timeout after {timeout}s: {shlex.join(argv)}") from exc
    if completed.returncode != 0:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", "replace")
        raise ContractError(
            f"command failed rc={completed.returncode}: {shlex.join(argv)}\n{stderr[-4000:]}"
        )
    return completed


def validate_required_commands(path: str | None = None) -> dict[str, str]:
    """Resolve every external command required for an admissible study run."""
    search_path = os.environ.get("PATH", "") if path is None else path
    resolved = {
        command: shutil.which(command, path=search_path)
        for command in REQUIRED_EXTERNAL_COMMANDS
    }
    missing = [command for command, executable in resolved.items() if executable is None]
    if missing:
        raise ContractError(
            f"required external commands are unavailable before study start: {missing}"
        )
    return {command: str(executable) for command, executable in resolved.items()}


def _optional_command_output(
    argv: Sequence[str], *, timeout: float
) -> tuple[str | None, dict[str, Any]]:
    """Run diagnostic-only telemetry without making its absence fatal."""
    recorded = time.monotonic()
    executable = shutil.which(argv[0])
    record: dict[str, Any] = {
        "collected": False,
        "recorded_monotonic_s": recorded,
        "command": list(argv),
        "executable": executable,
    }
    if executable is None:
        exc = FileNotFoundError(f"{argv[0]} is unavailable on PATH")
        record["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        return None, record
    try:
        output = _run_checked([executable, *argv[1:]], timeout=timeout).stdout
    except Exception as exc:
        record["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        return None, record
    record.update({
        "collected": True,
        "stdout_sha256": _sha256_bytes(output.encode()),
    })
    return output, record


def _git_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ALLOW_PROTOCOL": "file",
    })
    return env


def verify_canonical_submodule(repo_root: Path) -> dict[str, str]:
    canonical = repo_root / "external/ccbench"
    if not canonical.is_dir() or canonical.is_symlink():
        raise ContractError("canonical external/ccbench must be a real initialized directory")
    head = _run_checked(["git", "-C", str(canonical), "rev-parse", "HEAD"]).stdout.strip()
    status = _run_checked(
        ["git", "-C", str(canonical), "status", "--porcelain", "--untracked-files=all"]
    ).stdout
    tree_line = _run_checked(
        ["git", "-C", str(repo_root), "ls-tree", "HEAD", "external/ccbench"]
    ).stdout.strip()
    parts = tree_line.split()
    pinned = parts[2] if len(parts) >= 3 else ""
    if status or head != pinned or not re.fullmatch(r"[0-9a-f]{40}", pinned):
        raise ContractError(
            f"canonical submodule is not pinned-clean: head={head}, pinned={pinned}, status={status!r}"
        )
    return {"path": str(canonical), "head": head, "gitlink": pinned, "status_porcelain": status}


def clone_network_free(canonical: Path, destination: Path) -> None:
    if destination.exists():
        raise ContractError(f"scratch clone destination already exists: {destination}")
    _run_checked(
        [
            "git", "-c", "protocol.file.allow=always", "clone", "--local",
            "--no-hardlinks", "--no-recurse-submodules", str(canonical), str(destination),
        ],
        env=_git_env(), timeout=300,
    )


def _apply_patch(clone: Path, patch: Path, *, reverse: bool) -> None:
    flag = ["-R"] if reverse else []
    _run_checked(["git", "-C", str(clone), "apply", *flag, "--check", str(patch)])
    _run_checked(["git", "-C", str(clone), "apply", *flag, str(patch)])


def _cmake_cache(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith(("#", "//")) or "=" not in line or ":" not in line:
            continue
        left, value = line.split("=", 1)
        key = left.split(":", 1)[0]
        result[key] = value
    return result


def _expected_cache(arm: str, *, backoff: int) -> dict[str, str]:
    axes = ARM_CONFIG[arm]
    result = {
        AXIS_CACHE_KEYS[name]: str(axes[name]) for name in ("impl", "kind", "dlr", "wfg")
    }
    result.update({
        "CMAKE_BUILD_TYPE": "Release",
        "ENABLE_SANITIZER": "OFF",
        "CCBENCH_VAL_SIZE": "8",
        "CCBENCH_TRACE": "0",
        "CCBENCH_KEY_SORT": "0",
        "CCBENCH_BACK_OFF": str(backoff),
    })
    return result


def _validate_cache(expected: Mapping[str, str], observed: Mapping[str, str]) -> None:
    missing = sorted(set(expected) - set(observed))
    mismatches = {
        key: {"expected": value, "observed": observed.get(key)}
        for key, value in expected.items()
        if key in observed and _canonical_scalar(value) != _canonical_scalar(observed[key])
    }
    if missing or mismatches:
        raise ContractError(f"CMake cache binding mismatch: missing={missing}, mismatches={mismatches}")


def _entry_source(entry: Mapping[str, Any]) -> str:
    file_value = entry.get("file")
    directory = entry.get("directory")
    if not isinstance(file_value, str) or not file_value:
        raise ContractError("compile entry source path is missing")
    path = Path(file_value)
    if not path.is_absolute():
        if not isinstance(directory, str) or not directory:
            raise ContractError("relative compile entry source lacks a directory")
        path = Path(directory) / path
    return str(path.resolve())


def _target_compile_entries(build_dir: Path, target: str) -> list[dict[str, Any]]:
    path = build_dir / "compile_commands.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    marker = f"CMakeFiles/{target}.dir"
    selected = [row for row in rows if marker in str(row.get("output", "")) or marker in str(row.get("command", ""))]
    if not selected:
        raise ContractError(f"compile_commands has no entries for {target}")
    sources = [_entry_source(row) for row in selected]
    if len(sources) != len(set(sources)):
        raise ContractError(f"compile_commands sources for {target} are missing or duplicated")
    return selected


def _entry_argv(entry: Mapping[str, Any]) -> list[str]:
    if isinstance(entry.get("arguments"), list):
        return [str(item) for item in entry["arguments"]]
    command = entry.get("command")
    if not isinstance(command, str):
        raise ContractError("compile command lacks arguments and command")
    return shlex.split(command)


def _definitions(argv: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        definition: str | None = None
        if token == "-D" and index + 1 < len(argv):
            index += 1
            definition = argv[index]
        elif token.startswith("-D") and len(token) > 2:
            definition = token[2:]
        if definition:
            key, separator, value = definition.partition("=")
            result[key] = value if separator else "1"
        index += 1
    return result


def _validate_compile_definitions(
    entries: Sequence[Mapping[str, Any]], expected_cache: Mapping[str, str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    expected = [(key, CACHE_TO_DEFINE[key], value) for key, value in expected_cache.items() if key in CACHE_TO_DEFINE]
    for entry in entries:
        definitions = _definitions(_entry_argv(entry))
        missing = []
        mismatches = {}
        for cache_key, macro_key, value in expected:
            observed = [definitions[key] for key in (macro_key, cache_key) if key in definitions]
            if not observed:
                missing.append(f"{macro_key}|{cache_key}")
            elif any(_canonical_scalar(value) != _canonical_scalar(item) for item in observed):
                mismatches[macro_key] = {"expected": value, "observed": observed}
        if missing or mismatches:
            raise ContractError(
                f"compile definition binding mismatch for {entry.get('file')}: "
                f"missing={missing}, mismatches={mismatches}"
            )
        records.append({"file": str(entry.get("file")), "definitions": definitions})
    return records


def _validate_recorded_compile_definitions(
    records: Sequence[Mapping[str, Any]], expected_cache: Mapping[str, str]
) -> None:
    expected = [(key, CACHE_TO_DEFINE[key], value) for key, value in expected_cache.items() if key in CACHE_TO_DEFINE]
    if not records:
        raise ContractError("recorded compile definitions are missing")
    for record in records:
        definitions = record.get("definitions")
        if not isinstance(definitions, Mapping):
            raise ContractError("recorded compile definition row is malformed")
        missing = []
        mismatches = {}
        for cache_key, macro_key, value in expected:
            observed = [definitions[key] for key in (macro_key, cache_key) if key in definitions]
            if not observed:
                missing.append(f"{macro_key}|{cache_key}")
            elif any(_canonical_scalar(value) != _canonical_scalar(item) for item in observed):
                mismatches[macro_key] = {"expected": value, "observed": observed}
        if missing or mismatches:
            raise ContractError(
                f"recorded compile definition mismatch: missing={missing}, mismatches={mismatches}"
            )


def _preprocess_argv(entry: Mapping[str, Any]) -> list[str]:
    argv = _entry_argv(entry)
    result: list[str] = []
    skip_next = False
    consumes_value = {"-o", "-MF", "-MT", "-MQ", "--serialize-diagnostics"}
    discard = {"-c", "-MD", "-MMD", "-MP", "-MG"}
    for token in argv:
        if skip_next:
            skip_next = False
            continue
        if token in consumes_value:
            skip_next = True
            continue
        if token in discard:
            continue
        if any(token.startswith(prefix) for prefix in ("-MF", "-MT", "-MQ")):
            continue
        result.append(token)
    result.extend(["-E", "-P"])
    return result


_MULTI_OPS = tuple(sorted((
    "<=>", ">>=", "<<=", "->*", "...", "##", "::", ".*", "->", "++", "--",
    "<<", ">>", "<=", ">=", "==", "!=", "&&", "||", "*=", "/=", "%=", "+=",
    "-=", "&=", "^=", "|=", "##",
), key=len, reverse=True))

_CPP_TOKEN_RE = re.compile(
    r"(?P<whitespace>\s+)"
    r"|(?P<raw>(?:u8|u|U|L)?R\"(?P<raw_delimiter>[^ ()\\\t\r\n]{0,16})\("
    r"[\s\S]*?\)(?P=raw_delimiter)\")"
    r"|(?P<unterminated_raw>(?:u8|u|U|L)?R\"[^ ()\\\t\r\n]{0,16}\()"
    r'|(?P<string>(?:u8|u|U|L)?"(?:\\[\s\S]|[^"\\])*")'
    r"|(?P<character>(?:u8|u|U|L)?'(?:\\[\s\S]|[^'\\])*')"
    r"|(?P<unterminated_literal>(?:u8|u|U|L)?[\"'])"
    r"|(?P<identifier>[A-Za-z_$][A-Za-z0-9_$]*)"
    r"|(?P<number>(?:\d|\.\d)(?:[A-Za-z0-9_.']|(?<=[eEpP])[+-])*)"
    r"|(?P<operator>" + "|".join(re.escape(operator) for operator in _MULTI_OPS) + r")"
    r"|(?P<single>[\s\S])"
)
_CPP_BLANK_SPANS_RE = re.compile(
    r"//[^\n]*"
    r"|/\*(?:[^*]|\*(?!/))*(?:\*/|\Z)"
    r'|"(?:\\[\s\S]|[^"\\])*(?:"|\Z)'
    r"|'(?:\\[\s\S]|[^'\\])*(?:'|\Z)"
)
_NON_NEWLINE_RE = re.compile(r"[^\n]")


def _cpp_tokens(text: str) -> Iterator[str]:
    for match in _CPP_TOKEN_RE.finditer(text):
        if match.group("whitespace") is not None:
            continue
        if match.group("unterminated_raw") is not None:
            raise ContractError("unterminated raw C++ string in preprocessed source")
        if match.group("unterminated_literal") is not None:
            raise ContractError("unterminated C++ literal in preprocessed source")
        yield match.group(0)


def _strip_cpp_comments_and_literals(text: str) -> str:
    """Blank comments and literals while preserving braces and line positions."""
    return _CPP_BLANK_SPANS_RE.sub(
        lambda match: _NON_NEWLINE_RE.sub(" ", match.group(0)), text
    )


def _function_body(source: str, qualified_name: str) -> str:
    cleaned = _strip_cpp_comments_and_literals(source)
    pattern = re.compile(
        re.escape(qualified_name) + r"\s*\([^;{}]*\)\s*(?:noexcept\s*)?\{"
    )
    matches = list(pattern.finditer(cleaned))
    if len(matches) != 1:
        raise ContractError(
            f"expected exactly one definition of {qualified_name}, found {len(matches)}"
        )
    opening = cleaned.find("{", matches[0].start(), matches[0].end())
    depth = 0
    for index in range(opening, len(cleaned)):
        if cleaned[index] == "{":
            depth += 1
        elif cleaned[index] == "}":
            depth -= 1
            if depth == 0:
                return cleaned[opening + 1:index]
    raise ContractError(f"unterminated function body for {qualified_name}")


def _abort_counter_increments(source: str) -> int:
    cleaned = _strip_cpp_comments_and_literals(source)
    counter = r"(?:[A-Za-z_$][A-Za-z0-9_$]*\s*(?:->|\.)\s*)*local_abort_counts_"
    patterns = (
        rf"\+\+\s*{counter}",
        rf"{counter}\s*\+\+",
        rf"{counter}\s*\+=\s*1\b",
        rf"{counter}\s*=\s*{counter}\s*\+\s*1\b",
    )
    return sum(len(re.findall(pattern, cleaned)) for pattern in patterns)


def validate_abort_counter_ownership(clone: Path) -> dict[str, Any]:
    """Inspect the patched clone, independently of the binary's printed ratio."""
    clone = clone.resolve()
    transaction = clone / "cc/ss2pl/transaction.cc"
    workload = clone / "include/ycsb.hh"
    for path in (transaction, workload):
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"abort counter ownership source is missing or unsafe: {path}")
        try:
            path.resolve().relative_to(clone)
        except ValueError as exc:
            raise ContractError(f"abort counter ownership source escapes clone: {path}") from exc
    transaction_text = transaction.read_text(encoding="utf-8")
    workload_text = workload.read_text(encoding="utf-8")
    abort_body = _function_body(transaction_text, "TxExecutor::abort")
    transaction_increments = _abort_counter_increments(abort_body)
    workload_increments = _abort_counter_increments(workload_text)
    if transaction_increments != 0 or workload_increments != WORKLOAD_ABORT_INCREMENT_COUNT:
        raise ContractError(
            "abort counter ownership gate failed: "
            f"TxExecutor::abort increments={transaction_increments}, "
            f"workload increments={workload_increments}, "
            f"expected workload increments={WORKLOAD_ABORT_INCREMENT_COUNT}"
        )
    return {
        "transaction_source": str(transaction.relative_to(clone)),
        "transaction_sha256": sha256_file(transaction),
        "txexecutor_abort_increment_count": transaction_increments,
        "workload_source": str(workload.relative_to(clone)),
        "workload_sha256": sha256_file(workload),
        "workload_abort_increment_count": workload_increments,
        "expected_workload_abort_increment_count": WORKLOAD_ABORT_INCREMENT_COUNT,
    }


def _scan_cpp_tokens(preprocessed: bytes) -> dict[str, Any]:
    return _scan_cpp_tokens_for_study_lock(preprocessed, ())


def _scan_cpp_tokens_for_study_lock(
    preprocessed: bytes, study_lock_identifiers: Iterable[str]
) -> dict[str, Any]:
    text = preprocessed.decode("utf-8", "surrogateescape")
    study_identifiers = frozenset(str(item) for item in study_lock_identifiers)
    digest = hashlib.sha256()
    count = 0
    contexts: list[str | None] = []
    parentheses: list[str | None] = []
    previous: str | None = None
    last_closed_name: str | None = None
    axis_literal_functions: list[str | None] = []
    study_axis_literal_functions: list[str | None] = []
    study_axis_literal_hits: set[str] = set()
    study_identifier_counts: dict[str, int] = {}
    study_literal_hits: set[str] = set()
    identifier_hits: set[str] = set()
    literal_hits: set[str] = set()
    for token in _cpp_tokens(text):
        encoded = token.encode("utf-8", "surrogateescape")
        digest.update(f"{len(encoded):08x}:".encode("ascii"))
        digest.update(encoded)
        digest.update(b"\n")
        count += 1

        if token == WFG_AXIS_LITERAL:
            axis_literal_functions.append(
                next((name for name in reversed(contexts) if name), None)
            )
        else:
            if (
                re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", token)
                and re.search(r"(?i)(?:wfg|wait_?for_?graph)", token)
            ):
                identifier_hits.add(token)
            if token.startswith(('"', "'")) and _wfg_text_hits(token):
                literal_hits.add(token)

        if token == STUDY_LOCK_AXIS_LITERAL:
            study_axis_literal_functions.append(
                next((name for name in reversed(contexts) if name), None)
            )
        elif token.startswith(('"', "'")):
            if "SS2PL_LOCK_IMPL" in token:
                study_axis_literal_hits.add(token)
            for identifier in study_identifiers:
                if identifier in token:
                    study_literal_hits.add(token)
        elif token in study_identifiers:
            study_identifier_counts[token] = study_identifier_counts.get(token, 0) + 1

        if token == "(":
            parentheses.append(previous)
        elif token == ")":
            candidate = parentheses.pop() if parentheses else None
            last_closed_name = (
                candidate
                if candidate is not None
                and re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", candidate)
                else None
            )
        elif token == "{":
            contexts.append(last_closed_name if previous == ")" else None)
        elif token == "}" and contexts:
            contexts.pop()
        previous = token
    return {
        "preprocessed_sha256": _sha256_bytes(preprocessed),
        "cpp_token_sha256": digest.hexdigest(),
        "token_count": count,
        "wfg_axis_literal_functions": axis_literal_functions,
        "wfg_identifier_hits": sorted(identifier_hits),
        "wfg_literal_hits": sorted(literal_hits),
        "study_lock_axis_literal_functions": study_axis_literal_functions,
        "study_lock_axis_literal_hits": sorted(study_axis_literal_hits),
        "study_lock_identifier_counts": dict(sorted(study_identifier_counts.items())),
        "study_lock_literal_hits": sorted(study_literal_hits),
    }


def _token_hash(preprocessed: bytes) -> tuple[str, int]:
    scan = _scan_cpp_tokens(preprocessed)
    return str(scan["cpp_token_sha256"]), int(scan["token_count"])


def _preprocess(entry: Mapping[str, Any]) -> bytes:
    completed = _run_checked(
        _preprocess_argv(entry), cwd=Path(str(entry["directory"])), timeout=300, text=False
    )
    return bytes(completed.stdout)


def _preprocess_cache_identity(
    entry: Mapping[str, Any],
    source_state_sha256: str,
    scan_config_sha256: str = "",
) -> dict[str, str]:
    source = Path(_entry_source(entry))
    if not source.is_file() or source.is_symlink():
        raise ContractError(f"preprocess cache source is missing or unsafe: {source}")
    compile_argv = _entry_argv(entry)
    directory = str(Path(str(entry.get("directory", source.parent))).resolve())
    source_content_sha256 = sha256_file(source)
    identity = {
        "compile_argv_sha256": _sha256_bytes("\0".join(compile_argv).encode()),
        "directory_sha256": _sha256_bytes(directory.encode()),
        "source_path_sha256": _sha256_bytes(str(source).encode()),
        "source_content_sha256": source_content_sha256,
        "source_state_sha256": source_state_sha256,
        "scan_config_sha256": scan_config_sha256,
    }
    identity["cache_key_sha256"] = _sha256_bytes(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    )
    return identity


class PreprocessCache:
    """Cache token-scan results under an exact command/content/tree-state key."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self.requests = 0
        self.hits = 0
        self.avoided_preprocessed_bytes = 0

    def preprocess(
        self,
        entry: Mapping[str, Any],
        *,
        source_state_sha256: str,
        study_lock_identifiers: Iterable[str] = (),
    ) -> dict[str, Any]:
        request_started = time.monotonic()
        identifiers = tuple(sorted(str(item) for item in study_lock_identifiers))
        scan_state_sha256 = _sha256_bytes("\0".join(identifiers).encode())
        identity = _preprocess_cache_identity(
            entry, source_state_sha256, scan_state_sha256
        )
        key = identity["cache_key_sha256"]
        self.requests += 1
        cached = self._records.get(key)
        if cached is not None:
            self.hits += 1
            self.avoided_preprocessed_bytes += int(cached["receipt"]["preprocessed_bytes"])
            return {
                "scan": dict(cached["scan"]),
                "receipt": {
                    **cached["receipt"],
                    "cache_hit": True,
                    "request_duration_s": time.monotonic() - request_started,
                },
            }

        preprocess_started = time.monotonic()
        preprocessed = _preprocess(entry)
        preprocess_duration = time.monotonic() - preprocess_started
        tokenize_started = time.monotonic()
        scan = _scan_cpp_tokens_for_study_lock(preprocessed, identifiers)
        tokenize_duration = time.monotonic() - tokenize_started
        receipt = {
            **identity,
            "preprocessed_bytes": len(preprocessed),
            "token_count": int(scan["token_count"]),
            "preprocess_duration_s": preprocess_duration,
            "tokenize_duration_s": tokenize_duration,
            "request_duration_s": time.monotonic() - request_started,
            "cache_hit": False,
        }
        self._records[key] = {"scan": dict(scan), "receipt": dict(receipt)}
        return {"scan": scan, "receipt": receipt}

    def summary(self) -> dict[str, int]:
        return {
            "requests": self.requests,
            "hits": self.hits,
            "entries": len(self._records),
            "avoided_preprocessed_bytes": self.avoided_preprocessed_bytes,
        }


def _preprocess_with_receipt(
    entry: Mapping[str, Any],
    *,
    cache: PreprocessCache | None,
    source_state_sha256: str,
    study_lock_identifiers: Iterable[str] = (),
) -> dict[str, Any]:
    if cache is not None:
        return cache.preprocess(
            entry,
            source_state_sha256=source_state_sha256,
            study_lock_identifiers=study_lock_identifiers,
        )
    request_started = time.monotonic()
    preprocess_started = time.monotonic()
    preprocessed = _preprocess(entry)
    preprocess_duration = time.monotonic() - preprocess_started
    tokenize_started = time.monotonic()
    scan = _scan_cpp_tokens_for_study_lock(preprocessed, study_lock_identifiers)
    tokenize_duration = time.monotonic() - tokenize_started
    return {
        "scan": scan,
        "receipt": {
            "preprocessed_bytes": len(preprocessed),
            "token_count": int(scan["token_count"]),
            "preprocess_duration_s": preprocess_duration,
            "tokenize_duration_s": tokenize_duration,
            "request_duration_s": time.monotonic() - request_started,
            "cache_hit": False,
        },
    }


def _tracked_at_head(clone: Path, source: Path) -> bool:
    try:
        relative = source.resolve().relative_to(clone.resolve()).as_posix()
    except ValueError:
        return False
    argv = ["git", "-C", str(clone), "cat-file", "-e", f"HEAD:{relative}"]
    effective_timeout, limiting_stage = _bounded_timeout(30)
    try:
        completed = subprocess.run(
            argv, capture_output=True, check=False, timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        if limiting_stage is not None:
            raise ContractError(
                f"{limiting_stage.name} stage deadline exceeded while checking tracked source"
            ) from exc
        raise ContractError(f"tracked-source check timed out: {relative}") from exc
    return completed.returncode == 0


def _study_lock_header_declarations(clone: Path) -> dict[str, Any]:
    """Read the study-lock header and enumerate its declared C++ names."""
    clone = clone.resolve()
    header = clone / STUDY_LOCK_HEADER
    if not header.is_file() or header.is_symlink():
        raise ContractError(f"study-lock header is missing or unsafe: {header}")
    try:
        header.resolve().relative_to(clone)
    except ValueError as exc:
        raise ContractError(f"study-lock header escapes clone: {header}") from exc
    source = header.read_text(encoding="utf-8")
    tokens = list(_cpp_tokens(_strip_cpp_comments_and_literals(source)))
    identifier = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*\Z")
    excluded_functions = {
        "alignas", "alignof", "catch", "decltype", "for", "if", "noexcept",
        "defined", "requires", "sizeof", "static_assert", "switch", "typeid", "while",
    }
    names: set[str] = set()
    type_names: set[str] = set()

    def add_class_statement(statement: Sequence[str]) -> None:
        statement = list(statement)
        while len(statement) >= 2 and statement[0] in {"public", "private", "protected"}:
            if statement[1] != ":":
                break
            statement = statement[2:]
        if not statement:
            return
        if statement[0] == "using" and len(statement) > 1 and identifier.fullmatch(statement[1]):
            names.add(statement[1])
            return
        if statement[0] == "typedef":
            candidates = [token for token in statement[1:] if identifier.fullmatch(token)]
            if candidates:
                names.add(candidates[-1])
            return
        if "(" in statement:
            opening = statement.index("(")
            if opening and identifier.fullmatch(statement[opening - 1]):
                candidate = statement[opening - 1]
                if candidate not in excluded_functions:
                    names.add(candidate)
            return
        segments: list[list[str]] = [[]]
        angle = square = 0
        for token in statement:
            if token == "<":
                angle += 1
            elif token == ">" and angle:
                angle -= 1
            elif token == "[":
                square += 1
            elif token == "]" and square:
                square -= 1
            if token == "," and angle == square == 0:
                segments.append([])
            else:
                segments[-1].append(token)
        for segment in segments:
            for marker in ("=", "{"):
                if marker in segment:
                    segment = segment[:segment.index(marker)]
            candidates = [token for token in segment if identifier.fullmatch(token)]
            if candidates:
                candidate = candidates[-1]
                if candidate not in {"const", "constexpr", "static", "volatile"}:
                    names.add(candidate)

    def collect_class_members(opening: int, closing: int) -> None:
        statement: list[str] = []
        depth = 0
        for token in tokens[opening + 1:closing]:
            if token == "{" and depth == 0 and "(" in statement:
                add_class_statement(statement)
                statement = []
                depth = 1
                continue
            if token == "{":
                depth += 1
            elif token == "}" and depth:
                depth -= 1
                continue
            if depth:
                continue
            if token == ";":
                add_class_statement(statement)
                statement = []
            else:
                statement.append(token)

    function_scopes: list[bool] = []
    for index, token in enumerate(tokens):
        inside_function = any(function_scopes)
        if token in {"class", "struct", "enum"}:
            following = index + 1
            if token == "enum" and following < len(tokens) and tokens[following] == "class":
                following += 1
            if following < len(tokens) and identifier.fullmatch(tokens[following]):
                type_names.add(tokens[following])
                names.add(tokens[following])
                opening = next(
                    (position for position in range(following + 1, len(tokens))
                     if tokens[position] in {"{", ";"}),
                    -1,
                )
                if opening >= 0 and tokens[opening] == "{":
                    depth = 0
                    for closing in range(opening, len(tokens)):
                        if tokens[closing] == "{":
                            depth += 1
                        elif tokens[closing] == "}":
                            depth -= 1
                            if depth == 0:
                                collect_class_members(opening, closing)
                                break
        if (
            not inside_function
            and identifier.fullmatch(token)
            and token.endswith("_")
            and not token.startswith("SS2PL_")
        ):
            names.add(token)
        if (
            not inside_function
            and token == "("
            and index > 0
            and identifier.fullmatch(tokens[index - 1])
            and tokens[index - 1] not in excluded_functions
        ):
            names.add(tokens[index - 1])
        if token == "{":
            function_scopes.append(_function_name_before_brace(tokens, index) is not None)
        elif token == "}" and function_scopes:
            function_scopes.pop()
    names.update(
        name for name in type_names
        if any(
            tokens[index] == name and index + 1 < len(tokens) and tokens[index + 1] == "("
            for index in range(len(tokens))
        )
    )
    names = {name for name in names if name not in excluded_functions}
    if not type_names or not names:
        raise ContractError(
            "study-lock header declaration scan found no type or declared identifiers"
        )
    return {
        "path": STUDY_LOCK_HEADER,
        "sha256": sha256_file(header),
        "identifiers": sorted(names),
        "type_identifiers": sorted(type_names),
        "derivation": (
            "C++ tokens declared by class/struct/enum and alias names, function-like "
            "declarations outside function bodies, and direct class member declarations"
        ),
    }


def validate_default_stock_lock_absence(
    evidence: Mapping[str, Any]
) -> dict[str, Any]:
    """Record study-lock names observed in default-build preprocessed SS2PL TUs."""
    required = {
        "source_list", "header", "baseline_identifier_hits",
        "receptor_identifiers", "preprocessed", "checked_translation_units",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise ContractError(f"default stock-lock gate failed: missing={missing}")
    sources = evidence["source_list"]
    header = evidence["header"]
    rows = evidence["preprocessed"]
    if not isinstance(sources, list) or not sources:
        raise ContractError("default stock-lock gate failed: source population is empty")
    source_names = [str(item) for item in sources]
    if len(source_names) != len(set(source_names)):
        raise ContractError("default stock-lock gate failed: sources are not unique")
    if not isinstance(header, Mapping):
        raise ContractError("default stock-lock gate failed: header declaration receipt is missing")
    identifiers = header.get("identifiers")
    if (
        header.get("path") != STUDY_LOCK_HEADER
        or not _HASH_RE.fullmatch(str(header.get("sha256", "")))
        or not isinstance(identifiers, list)
        or not identifiers
        or len(identifiers) != len(set(str(item) for item in identifiers))
    ):
        raise ContractError("default stock-lock gate failed: header declaration receipt is invalid")
    declared_identifier_names = [str(item) for item in identifiers]
    baseline_identifier_hits = evidence["baseline_identifier_hits"]
    receptor_identifiers = evidence["receptor_identifiers"]
    if (
        not isinstance(baseline_identifier_hits, list)
        or not isinstance(receptor_identifiers, list)
        or any(not isinstance(item, str) for item in baseline_identifier_hits)
        or any(not isinstance(item, str) for item in receptor_identifiers)
        or len(baseline_identifier_hits) != len(set(baseline_identifier_hits))
        or len(receptor_identifiers) != len(set(receptor_identifiers))
        or not set(baseline_identifier_hits).issubset(declared_identifier_names)
        or set(receptor_identifiers)
        != set(declared_identifier_names) - set(baseline_identifier_hits)
    ):
        raise ContractError(
            "default stock-lock gate failed: identifier calibration receipt is invalid"
        )
    identifier_names = sorted(receptor_identifiers)
    if not identifier_names:
        return {
            **_uncollected_observation(ContractError(
                "default stock-lock identifier observation could not calibrate a nonempty set"
            )),
            "configuration": {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0},
            "header": dict(header),
            "baseline_identifier_hits": sorted(baseline_identifier_hits),
            "receptor_identifiers": [],
            "checked_identifiers": [],
        }
    if not isinstance(rows, list) or len(rows) != len(source_names):
        raise ContractError("default stock-lock gate failed: preprocessed population differs")
    checked = int(evidence["checked_translation_units"])
    if checked != len(source_names):
        raise ContractError("default stock-lock gate failed: checked TU count differs")

    observed_sources: set[str] = set()
    translation_units: list[dict[str, Any]] = []
    identifier_hits: list[dict[str, Any]] = []
    literal_hits: list[dict[str, Any]] = []
    bad_axis_literals: list[dict[str, Any]] = []
    allowed_locations: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("source"), str):
            raise ContractError("default stock-lock gate failed: malformed TU receipt")
        source = str(row["source"])
        scan = row.get("token_scan")
        if source not in source_names or source in observed_sources or not isinstance(scan, Mapping):
            raise ContractError("default stock-lock gate failed: TU identity mismatch")
        observed_sources.add(source)
        source_sha = str(row.get("sha256", ""))
        token_sha = str(scan.get("cpp_token_sha256", ""))
        if (
            source_sha != str(scan.get("preprocessed_sha256", ""))
            or not _HASH_RE.fullmatch(source_sha)
            or not _HASH_RE.fullmatch(token_sha)
            or not isinstance(scan.get("token_count"), int)
        ):
            raise ContractError("default stock-lock gate failed: TU hash/count receipt is invalid")
        counts = scan.get("study_lock_identifier_counts")
        strings = scan.get("study_lock_literal_hits")
        axis_strings = scan.get("study_lock_axis_literal_hits")
        locations = scan.get("study_lock_axis_literal_functions")
        if (
            not isinstance(counts, Mapping)
            or not isinstance(strings, list)
            or not isinstance(axis_strings, list)
            or not isinstance(locations, list)
        ):
            raise ContractError("default stock-lock gate failed: TU token scan is incomplete")
        unknown_count_names = sorted(set(str(item) for item in counts) - set(identifier_names))
        if unknown_count_names or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in counts.values()
        ):
            raise ContractError("default stock-lock gate failed: identifier count receipt is invalid")
        if counts:
            identifier_hits.append({"source": source, "counts": dict(counts)})
        if strings:
            literal_hits.append({"source": source, "literals": list(strings)})
        if axis_strings:
            bad_axis_literals.append({"source": source, "literals": list(axis_strings)})
        allowed_locations.extend(
            {"source": source, "function": function} for function in locations
        )
        translation_units.append({
            "translation_unit": source,
            "preprocessed_sha256": source_sha,
            "cpp_token_sha256": token_sha,
            "token_count": int(scan["token_count"]),
            "study_lock_identifier_counts": dict(counts),
            "study_lock_literal_hits": list(strings),
            "axis_label_count": len(locations),
        })

    util_source = next(
        (source for source in source_names if source.replace("\\", "/").endswith("cc/ss2pl/util.cc")),
        "",
    )
    expected_location = [{"source": util_source, "function": "ShowOptParameters"}]
    passed = not (
        observed_sources != set(source_names)
        or identifier_hits
        or literal_hits
        or bad_axis_literals
        or allowed_locations != expected_location
        or not util_source
    )
    return {
        "collected": True,
        "passed": passed,
        "configuration": {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0},
        "header": dict(header),
        "baseline_identifier_hits": sorted(baseline_identifier_hits),
        "receptor_identifiers": identifier_names,
        "checked_identifiers": identifier_names,
        "checked_translation_units": checked,
        "source_files": source_names,
        "translation_units": translation_units,
        "findings": {
            "identifier_hits": identifier_hits,
            "literal_hits": literal_hits,
            "bad_axis_literals": bad_axis_literals,
            "observed_sources_match": observed_sources == set(source_names),
            "allowed_locations": allowed_locations,
            "expected_location": expected_location,
        },
        "allowed_axis_label": {
            "literal": STUDY_LOCK_AXIS_LITERAL,
            "source": util_source,
            "function": "ShowOptParameters",
            "token_count": 1,
        },
    }


def _declared_difference_rows() -> list[dict[str, str]]:
    return [
        {"translation_unit": source, "reason": reason}
        for source, reason in INERT_DECLARED_DIFFERENCES.items()
    ]


def _inert_witness_claim() -> str:
    differences = "; ".join(
        f"{source}: {reason}"
        for source, reason in INERT_DECLARED_DIFFERENCES.items()
    )
    return (
        "This witness records whether, for every enumerated SS2PL translation unit outside "
        "the declared-difference table, the byte hash of the preprocessed C++ token "
        "sequence produced by the same compile command matched the unpatched tree. It also "
        "records the stock-lock identifier inspection for the default configuration "
        "(IMPL=0). These observations are not acceptance gates. The witness "
        "does not prove build-graph identity, binary identity, identity for the newly "
        "added ycsb target (which has no counterpart in the unpatched tree), or runtime "
        f"identity. The declared differences are: {differences}."
    )


def validate_inert_witness_receipt(witness: Mapping[str, Any]) -> None:
    """Validate the structure and internal consistency of the witness observation."""
    if not isinstance(witness.get("collected"), bool):
        raise ContractError("inert witness collected status is missing")
    if witness["collected"] is False:
        failure = witness.get("failure")
        if (
            not isinstance(failure, Mapping)
            or not isinstance(failure.get("type"), str)
            or not isinstance(failure.get("message"), str)
        ):
            raise ContractError("inert witness collection failure reason is missing")
        if witness.get("declared_translation_unit_differences") != _declared_difference_rows():
            raise ContractError("uncollected inert witness lacks its declaration table")
        return
    if witness.get("claim") != _inert_witness_claim():
        raise ContractError("inert witness claim is missing or differs from its contract")
    declarations = witness.get("declared_translation_unit_differences")
    if declarations != _declared_difference_rows():
        raise ContractError("inert witness declared-difference table differs from its contract")
    units = witness.get("translation_units")
    if not isinstance(units, list) or not units:
        raise ContractError("inert witness translation-unit receipts are missing")
    names = [str(unit.get("translation_unit", "")) for unit in units if isinstance(unit, Mapping)]
    if len(names) != len(units) or len(names) != len(set(names)):
        raise ContractError("inert witness translation-unit identities are malformed or duplicated")
    declared = set(INERT_DECLARED_DIFFERENCES)
    if not declared.issubset(names):
        raise ContractError("inert witness does not enumerate every declared-difference TU")
    observed_differences: set[str] = set()
    for unit in units:
        source = str(unit["translation_unit"])
        before_sha = str(unit.get("baseline_cpp_token_sha256", ""))
        after_sha = str(unit.get("patched_cpp_token_sha256", ""))
        before_count = unit.get("baseline_token_count")
        after_count = unit.get("patched_token_count")
        if (
            not _HASH_RE.fullmatch(before_sha)
            or not _HASH_RE.fullmatch(after_sha)
            or not isinstance(before_count, int)
            or not isinstance(after_count, int)
            or before_count < 0
            or after_count < 0
        ):
            raise ContractError(f"inert witness token identity is invalid for {source}")
        actual_match = (before_sha, before_count) == (after_sha, after_count)
        if unit.get("match") is not actual_match:
            raise ContractError(f"inert witness match flag is false evidence for {source}")
        expected_reason = INERT_DECLARED_DIFFERENCES.get(source)
        if unit.get("declared_difference_reason") != expected_reason:
            raise ContractError(f"inert witness declaration reason differs for {source}")
        if not actual_match:
            observed_differences.add(source)
    expected_exact_match = observed_differences == declared
    expected_undeclared_match = not bool(observed_differences - declared)
    if witness.get("observed_differing_translation_units") != sorted(observed_differences):
        raise ContractError("inert witness observed-difference list is inconsistent")
    if (
        witness.get("observed_differences_match_declaration") is not expected_exact_match
        or witness.get("all_undeclared_translation_units_match") is not expected_undeclared_match
    ):
        raise ContractError("inert witness comparison verdict is inconsistent")
    stock_gate = witness.get("default_stock_lock_gate")
    if not isinstance(stock_gate, Mapping) or not isinstance(stock_gate.get("collected"), bool):
        raise ContractError("inert witness default stock-lock observation is missing")
    if stock_gate["collected"] is False:
        failure = stock_gate.get("failure")
        if not isinstance(failure, Mapping) or not isinstance(failure.get("message"), str):
            raise ContractError("stock-lock collection failure reason is missing")
        return
    if not isinstance(stock_gate.get("passed"), bool):
        raise ContractError("inert witness default stock-lock verdict is missing")
    if stock_gate.get("configuration") != {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0}:
        raise ContractError("inert witness default stock-lock configuration is wrong")
    if set(str(item) for item in stock_gate.get("source_files", [])) != set(names):
        raise ContractError("inert witness stock-lock TU population differs from hash witness")
    header = stock_gate.get("header")
    declared = header.get("identifiers") if isinstance(header, Mapping) else None
    baseline_hits = stock_gate.get("baseline_identifier_hits")
    receptor = stock_gate.get("receptor_identifiers")
    if (
        not isinstance(declared, list)
        or not isinstance(baseline_hits, list)
        or not isinstance(receptor, list)
        or not receptor
        or any(not isinstance(item, str) for item in declared + baseline_hits + receptor)
        or set(receptor) != set(declared) - set(baseline_hits)
        or stock_gate.get("checked_identifiers") != sorted(receptor)
    ):
        raise ContractError("inert witness stock-lock identifier calibration is invalid")


def collect_inert_witness(
    clone: Path,
    patch: Path,
    entries: Sequence[Mapping[str, Any]],
    patch_state: dict[str, bool],
    *,
    preprocess_cache: PreprocessCache | None = None,
    baseline_source_state_sha256: str = "baseline",
    patched_source_state_sha256: str = "patched",
) -> dict[str, Any]:
    if not entries:
        raise ContractError("inert witness compile entry population is empty")
    sources = [str(entry.get("file", "")) for entry in entries]
    if len(sources) != len(set(sources)):
        raise ContractError("inert witness compile entry sources are not unique")
    existing = [entry for entry in entries if _tracked_at_head(clone, Path(str(entry["file"])))]
    if len(existing) != len(entries):
        missing = sorted(set(sources) - {str(entry.get("file", "")) for entry in existing})
        raise ContractError(
            f"inert witness includes translation units absent from the baseline: {missing}"
        )
    if not existing:
        raise ContractError("inert witness has no existing SS2PL translation units")
    stock_setup_failure: dict[str, Any] | None = None
    try:
        study_lock_header = _study_lock_header_declarations(clone)
        study_lock_identifiers = tuple(study_lock_header["identifiers"])
    except Exception as exc:
        study_lock_header = {}
        study_lock_identifiers = ()
        stock_setup_failure = _uncollected_observation(exc)
    command_hashes = [_sha256_bytes("\0".join(_entry_argv(entry)).encode()) for entry in existing]
    _apply_patch(clone, patch, reverse=True)
    patch_state["applied"] = False
    baseline: list[dict[str, Any]] = []
    try:
        baseline = [
            _preprocess_with_receipt(
                entry, cache=preprocess_cache,
                source_state_sha256=baseline_source_state_sha256,
                study_lock_identifiers=study_lock_identifiers,
            )
            for entry in existing
        ]
    finally:
        _apply_patch(clone, patch, reverse=False)
        patch_state["applied"] = True
    baseline_identifier_hits = sorted({
        identifier
        for result in baseline
        for identifier in result["scan"]["study_lock_identifier_counts"]
    })
    receptor_identifiers = sorted(
        set(study_lock_identifiers) - set(baseline_identifier_hits)
    )
    patched = [
        _preprocess_with_receipt(
            entry, cache=preprocess_cache,
            source_state_sha256=patched_source_state_sha256,
            study_lock_identifiers=receptor_identifiers,
        )
        for entry in existing
    ]
    units = []
    for entry, command_sha, before, after in zip(existing, command_hashes, baseline, patched):
        source = Path(str(entry["file"])).resolve().relative_to(clone.resolve()).as_posix()
        before_scan = before["scan"]
        after_scan = after["scan"]
        before_identity = (
            str(before_scan["cpp_token_sha256"]), int(before_scan["token_count"])
        )
        after_identity = (
            str(after_scan["cpp_token_sha256"]), int(after_scan["token_count"])
        )
        record = {
            "translation_unit": source,
            "compile_command_sha256": command_sha,
            "baseline_cpp_token_sha256": before_identity[0],
            "patched_cpp_token_sha256": after_identity[0],
            "baseline_token_count": before_identity[1],
            "patched_token_count": after_identity[1],
            "baseline_preprocessing": before["receipt"],
            "patched_preprocessing": after["receipt"],
            "match": before_identity == after_identity,
            "declared_difference_reason": INERT_DECLARED_DIFFERENCES.get(source),
        }
        units.append(record)
    mismatches = {record["translation_unit"] for record in units if not record["match"]}
    declared = set(INERT_DECLARED_DIFFERENCES)
    if stock_setup_failure is not None:
        stock_lock_gate = stock_setup_failure
    else:
        try:
            stock_lock_gate = validate_default_stock_lock_absence({
                "source_list": [record["translation_unit"] for record in units],
                "header": study_lock_header,
                "baseline_identifier_hits": baseline_identifier_hits,
                "receptor_identifiers": receptor_identifiers,
                "preprocessed": [
                    {
                        "source": record["translation_unit"],
                        "sha256": after["scan"]["preprocessed_sha256"],
                        "token_scan": after["scan"],
                    }
                    for record, after in zip(units, patched)
                ],
                "checked_translation_units": len(units),
            })
        except Exception as exc:
            stock_lock_gate = _uncollected_observation(exc)
    witness = {
        "collected": True,
        "configuration": {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0},
        "normalization": (
            "same compile command; preprocessor -P removes line markers; preprocessing removes "
            "comments; whitespace and empty lines are excluded while hashing length-delimited C++ tokens"
        ),
        "translation_units": units,
        "checked_translation_units": len(units),
        "declared_translation_unit_differences": _declared_difference_rows(),
        "observed_differing_translation_units": sorted(mismatches),
        "observed_differences_match_declaration": mismatches == declared,
        "all_undeclared_translation_units_match": not bool(mismatches - declared),
        "default_stock_lock_gate": stock_lock_gate,
        "claim": _inert_witness_claim(),
    }
    validate_inert_witness_receipt(witness)
    return witness


def collect_inert_witness_observation(
    clone: Path,
    patch: Path,
    entries: Sequence[Mapping[str, Any]],
    patch_state: dict[str, bool],
    **kwargs: Any,
) -> dict[str, Any]:
    try:
        return collect_inert_witness(clone, patch, entries, patch_state, **kwargs)
    except Exception as exc:
        return _uncollected_inert_witness(exc)


def _uncollected_inert_witness(exc: BaseException) -> dict[str, Any]:
    return {
        **_uncollected_observation(exc),
        "declared_translation_unit_differences": _declared_difference_rows(),
        "default_stock_lock_gate": {
            **_uncollected_observation(ContractError(
                "stock-lock inspection was not collected because inert witness collection failed"
            )),
        },
    }


def _configure(
    source: Path,
    build_dir: Path,
    *,
    arm: str,
    backoff: int,
    gflags_prefix: Path,
    glog_prefix: Path,
    thirdparty_root: Path,
    expected_cache: Mapping[str, str] | None = None,
) -> dict[str, str]:
    derived = _expected_cache(arm, backoff=backoff)
    expected = derived if expected_cache is None else dict(expected_cache)
    if expected != derived:
        raise ContractError("provided configure cache differs from arm/backoff")
    argv = [
        "cmake", "-S", str(source), "-B", str(build_dir),
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        f"-DCMAKE_PREFIX_PATH={gflags_prefix};{glog_prefix}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={thirdparty_root / 'masstree'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={thirdparty_root / 'mimalloc'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={thirdparty_root / 'googletest'}",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
        *[f"-D{key}={value}" for key, value in expected.items()],
    ]
    _run_checked(argv, timeout=600)
    observed = _cmake_cache(build_dir / "CMakeCache.txt")
    _validate_cache(expected, observed)
    return expected


def _condition_request_inputs(
    expected_cache: Mapping[str, str],
) -> tuple[tuple[str, str, int, int], ...]:
    rows = []
    for axis, macro in (
        ("impl", "SS2PL_LOCK_IMPL"),
        ("kind", "SS2PL_LOCK_KIND"),
        ("dlr", "SS2PL_DLR"),
        ("wfg", "SS2PL_WFG_DIAG"),
    ):
        cache_key = AXIS_CACHE_KEYS[axis]
        try:
            requested = int(expected_cache[cache_key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                f"condition request lacks integer cache value for {cache_key}"
            ) from exc
        rows.append((axis, macro, requested, AXIS_DEFAULTS[axis]))
    return tuple(rows)


def _require_condition_gates(
    source: Path,
    *,
    arm: str,
    stock_source: Path,
    expected_cache: Mapping[str, str],
    gflags_prefix: Path,
    glog_prefix: Path,
    thirdparty_root: Path,
) -> list[dict[str, Any]]:
    configure_args = (
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_PREFIX_PATH={gflags_prefix};{glog_prefix}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={thirdparty_root / 'masstree'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={thirdparty_root / 'mimalloc'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={thirdparty_root / 'googletest'}",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
        *(
            f"-D{key}={value}"
            for key, value in expected_cache.items()
            if key not in AXIS_CACHE_KEYS.values()
        ),
    )
    supply_records = []
    meaning_records = []
    for _axis, macro, requested, default in _condition_request_inputs(
        expected_cache
    ):
        captured = condition_meaning_gate.capture_define_inputs(
            source,
            stock_root=stock_source,
            configure_args=configure_args,
        )
        request = condition_meaning_gate.make_define_request(
            driver_id=f"tools.pegasus.run_ss2pl_lock_study:{arm}",
            macro=macro,
            requested_value=requested,
            default_value=default,
            stock_comparison=requested == default,
        )
        supply_records.append(
            condition_meaning_gate.evaluate_define_supply_effectuation(
                captured, request=request, cxx="c++", cmake="cmake",
            )
        )
        meaning_records.append(
            condition_meaning_gate.evaluate_define_runtime_meaning(
                captured, request=request, declaration=None, cxx="c++",
            )
        )
    admission = condition_meaning_gate.require_condition_gate_family(
        supply_records, meaning_records, use_class="raw-measurement",
    )
    if not admission.admitted:
        states = ", ".join(
            f"{record.macro}={record.terminal_status}/{record.reason_code}"
            for record in (*supply_records, *meaning_records)
        )
        raise ContractError(f"condition gate rejected SS2PL study: {states}")
    return [
        *(json.loads(record.canonical_json()) for record in supply_records),
        *(json.loads(record.canonical_json()) for record in meaning_records),
        json.loads(admission.canonical_json()),
    ]


def _find_binary(build_dir: Path, target: str) -> Path:
    matches = [path for path in build_dir.rglob(target) if path.is_file() and os.access(path, os.X_OK)]
    if len(matches) != 1:
        raise ContractError(f"expected exactly one {target}, found {matches}")
    return matches[0]


def _wfg_absence_evidence(
    binary: Path,
    entries: Sequence[Mapping[str, Any]],
    *,
    preprocess_cache: PreprocessCache | None = None,
    source_state_sha256: str = "patched",
) -> dict[str, Any]:
    sources = [_entry_source(entry) for entry in entries]
    if not sources or len(sources) != len(set(sources)):
        raise ContractError("WFG absence gate requires nonempty unique compile entry sources")
    symbols = _run_checked(["nm", "-a", "-C", str(binary)], timeout=120).stdout
    strings = _run_checked(["strings", "-a", str(binary)], timeout=120).stdout
    preprocessed = [
        _preprocess_with_receipt(
            entry, cache=preprocess_cache,
            source_state_sha256=source_state_sha256,
        )
        for entry in entries
    ]
    evidence = {
        "source_list": sources,
        "symbols": symbols,
        "strings": strings.splitlines(),
        "preprocessed": [
            {
                "source": source,
                "sha256": result["scan"]["preprocessed_sha256"],
                "token_scan": result["scan"],
                **result["receipt"],
            }
            for source, result in zip(sources, preprocessed)
        ],
        "checked_translation_units": len(entries),
    }
    return validate_wfg_absence(evidence)


def build_target(
    source: Path,
    stock_source: Path,
    build_root: Path,
    *,
    build_id: str,
    arm: str,
    backoff: int,
    gflags_prefix: Path,
    glog_prefix: Path,
    thirdparty_root: Path,
    jobs: int,
    target: str = "ycsb_ss2pl.exe",
    preprocess_cache: PreprocessCache | None = None,
    source_state_sha256: str = "patched",
) -> dict[str, Any]:
    build_dir = build_root / build_id
    if build_dir.exists():
        raise ContractError(f"build directory collision: {build_dir}")
    requested_cache = _expected_cache(arm, backoff=backoff)
    condition_gates = _require_condition_gates(
        source,
        arm=arm,
        stock_source=stock_source,
        expected_cache=requested_cache,
        gflags_prefix=gflags_prefix,
        glog_prefix=glog_prefix,
        thirdparty_root=thirdparty_root,
    )
    expected = _configure(
        source, build_dir, arm=arm, backoff=backoff,
        gflags_prefix=gflags_prefix, glog_prefix=glog_prefix,
        thirdparty_root=thirdparty_root,
        expected_cache=requested_cache,
    )
    if expected != requested_cache:
        raise ContractError("condition requests differ from configure cache values")
    _run_checked(["cmake", "--build", str(build_dir), "--target", target, "--parallel", str(jobs)], timeout=1800)
    binary = _find_binary(build_dir, target)
    entries = _target_compile_entries(build_dir, target)
    definitions = _validate_compile_definitions(entries, expected)
    binary_sha = sha256_file(binary)
    record: dict[str, Any] = {
        "build_id": build_id,
        "arm": arm,
        "backoff": backoff,
        "requested_cache": expected,
        "observed_cache": {key: _cmake_cache(build_dir / "CMakeCache.txt")[key] for key in expected},
        "compile_definitions": definitions,
        "binary": str(binary),
        "binary_sha256": binary_sha,
        "target": target,
        "condition_gates": condition_gates,
    }
    if arm in PERFORMANCE_ARMS:
        record["wfg_absence"] = _wfg_absence_evidence(
            binary, entries, preprocess_cache=preprocess_cache,
            source_state_sha256=source_state_sha256,
        )
    return record


_AXIS_PATTERNS = {
    "impl": re.compile(
        r"(?<![A-Za-z0-9_])(?:CCBENCH_SS2PL_LOCK_IMPL|SS2PL_LOCK_IMPL|IMPL)"
        r"(?:[ \t]*[=:][ \t]*|[ \t]+)([0-9]+)(?=$|[ \t,:])"
    ),
    "kind": re.compile(
        r"(?<![A-Za-z0-9_])(?:CCBENCH_SS2PL_LOCK_KIND|SS2PL_LOCK_KIND|KIND)"
        r"(?:[ \t]*[=:][ \t]*|[ \t]+)([0-9]+)(?=$|[ \t,:])"
    ),
    "dlr": re.compile(
        r"(?<![A-Za-z0-9_])(?:CCBENCH_SS2PL_DLR|SS2PL_DLR|DLR)"
        r"(?:[ \t]*[=:][ \t]*|[ \t]+)([0-9]+)(?=$|[ \t,:])"
    ),
    "wfg": re.compile(
        r"(?<![A-Za-z0-9_])(?:CCBENCH_SS2PL_WFG_DIAG|SS2PL_WFG_DIAG|WFG)"
        r"(?:[ \t]*[=:][ \t]*|[ \t]+)([0-9]+)(?=$|[ \t,:])"
    ),
}


def parse_runtime_axes(stdout: str) -> tuple[dict[str, int], str]:
    for line in stdout.splitlines():
        if not re.match(r"^[ \t]*#?ShowOptParameters\(\)[ \t]*:", line):
            continue
        values: dict[str, int] = {}
        for name, pattern in _AXIS_PATTERNS.items():
            match = pattern.search(line)
            if match:
                values[name] = int(match.group(1))
        if set(values) == set(_AXIS_PATTERNS):
            return values, line
    raise ContractError("ShowOptParameters line with all four SS2PL axes is missing")


def parse_runtime_flags(stdout: str) -> tuple[dict[str, str], list[str]]:
    flags: dict[str, str] = {}
    lines: list[str] = []
    pattern = re.compile(
        r"^[ \t]*#FLAGS_(ycsb_[A-Za-z0-9_]+)"
        r"(?:[ \t]*[=:][ \t]*|[ \t]+)([^ \t,]+)[ \t]*$"
    )
    for line in stdout.splitlines():
        match = pattern.fullmatch(line)
        if match is None:
            continue
        key, value = match.group(1), match.group(2)
        if key in flags and _canonical_scalar(flags[key]) != _canonical_scalar(value):
            raise ContractError(
                f"runtime workload flag {key} has conflicting duplicate values: "
                f"{flags[key]} != {value}"
            )
        flags[key] = value
        lines.append(line)
    return flags, lines


_METRIC_NUMBER_RE = re.compile(
    r"[-+]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][-+]?[0-9]+)?\Z"
)


def _metric(stdout: str, label: str, cast: type[int] | type[float]) -> int | float:
    pattern = re.compile(
        r"^[ \t]*" + re.escape(label)
        + r"(?:[ \t]*:[ \t]*|[ \t]+)(?P<value>.*?)[ \t]*$"
    )
    matches = [match for line in stdout.splitlines() if (match := pattern.fullmatch(line))]
    if len(matches) == 0:
        raise ContractError(f"runtime metric is missing: {label}")
    if len(matches) != 1:
        raise ContractError(
            f"runtime metric is ambiguous: {label} appears on {len(matches)} lines"
        )
    token = matches[0].group("value")
    if _METRIC_NUMBER_RE.fullmatch(token) is None:
        raise ContractError(f"runtime metric is not a finite number: {label}={token!r}")
    try:
        value = cast(token)
    except (ValueError, OverflowError) as exc:
        raise ContractError(
            f"runtime metric has an invalid {cast.__name__} value: {label}={token!r}"
        ) from exc
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError(f"runtime metric is not finite: {label}={token!r}")
    return value


def _json_events(stdout: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _thread_commits(stdout: str, events: Sequence[Mapping[str, Any]], threads: int) -> list[int]:
    for event in events:
        for key in ("thread_commit_counts", "per_thread_commit_counts"):
            value = event.get(key)
            if isinstance(value, list) and all(isinstance(item, int) for item in value):
                if len(value) != threads:
                    raise ContractError(f"{key} length {len(value)} != thread_num {threads}")
                return list(value)
        value = event.get("per_thread_commits")
        if isinstance(value, list) and all(isinstance(item, Mapping) for item in value):
            ordered = sorted(value, key=lambda item: int(item.get("thread_id", item.get("worker", -1))))
            commits = [int(item["commits"]) for item in ordered]
            if len(commits) == threads:
                return commits
    indexed = re.findall(r"(?:thread_commit_count|commit_count)\[([0-9]+)\]\s*:?\s*([0-9]+)", stdout)
    if indexed:
        values = {int(index): int(count) for index, count in indexed}
        if set(values) == set(range(threads)):
            return [values[index] for index in range(threads)]
    inline = re.findall(r"(?:per_)?thread_commit_counts\s*:\s*\[?([0-9, ]+)\]?", stdout)
    if inline:
        values = [int(item.strip()) for item in inline[-1].split(",") if item.strip()]
        if len(values) == threads:
            return values
    raise ContractError("per-thread commit counts are missing or incomplete")


def _gini(values: Sequence[int]) -> float:
    if not values or sum(values) == 0:
        return 0.0
    ordered = sorted(values)
    total = sum(ordered)
    n = len(ordered)
    return sum((2 * index - n - 1) * value for index, value in enumerate(ordered, 1)) / (n * total)


def _parse_layout(events: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    invalid_reason: ContractError | None = None
    for event in events:
        candidates = [event.get(key) for key in ("ss2pl_layout", "layout")]
        if "layout" in str(event.get("event", "")).lower():
            candidates.append(event)
        for value in candidates:
            if not isinstance(value, Mapping):
                continue
            candidate_reason: ContractError | None = None
            categories = {
                prefix: [name for name in value if str(name).startswith(prefix)]
                for prefix in ("sizeof", "alignof", "offsetof")
            }
            if not all(categories.values()):
                continue
            result = dict(value)
            for name in categories["sizeof"] + categories["alignof"]:
                numbers = list(_integer_leaves(result[name]))
                if not numbers or any(number <= 0 for number in numbers):
                    candidate_reason = ContractError(
                        f"layout field {name} must be a positive integer"
                    )
                    break
            if candidate_reason is not None:
                invalid_reason = candidate_reason
                continue
            for name in categories["offsetof"]:
                numbers = list(_integer_leaves(result[name]))
                if not numbers or any(number < 0 for number in numbers):
                    candidate_reason = ContractError(
                        f"layout field {name} must be a nonnegative integer"
                    )
                    break
            if candidate_reason is not None:
                invalid_reason = candidate_reason
                continue
            result["collected"] = True
            return result
    return _uncollected_observation(
        invalid_reason
        or ContractError("sizeof/alignof/offsetof SS2PL layout record was not emitted")
    )


def _integer_leaves(value: Any) -> Iterator[int]:
    if isinstance(value, int) and not isinstance(value, bool):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from _integer_leaves(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _integer_leaves(nested)


def _extract_snapshots(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for event in events:
        value: Any = event.get("wfg_snapshot")
        if isinstance(value, Mapping):
            snapshots.append(dict(value))
        elif isinstance(event.get("nodes"), list) and isinstance(event.get("edges"), list) and "wfg" in str(event.get("event", "")).lower():
            snapshots.append(dict(event))
    return snapshots


def _node_signature(node: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        node.get("thread_id"), node.get("attempt"), node.get("wait_lock_id"),
        node.get("request_mode"), node.get("commit_count"), node.get("abort_count"),
    )


def _edge_is_incompatible(request_mode: Any, holder_mode: Any) -> bool:
    request = str(request_mode).lower()
    holder = str(holder_mode).lower()
    shared = {"r", "read", "shared", "s"}
    return not (request in shared and holder in shared)


def _holder_evidence(holder: Mapping[str, Any], edge: Mapping[str, Any]) -> bool:
    if edge.get("holder_holds_lock") is True:
        return True
    held = holder.get("held_locks")
    if not isinstance(held, list):
        return False
    for item in held:
        if isinstance(item, Mapping) and item.get("lock_id") == edge.get("lock_id"):
            if edge.get("holder_mode") is None or item.get("mode") == edge.get("holder_mode"):
                return True
    return False


def _edge_signature(edge: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(edge.get(key)) for key in (
        "waiter_thread_id", "holder_thread_id", "lock_id",
        "request_mode", "holder_mode", "compatible",
    ))


def _has_directed_cycle(edges: Sequence[Mapping[str, Any]]) -> bool:
    graph: dict[Any, list[Any]] = {}
    for edge in edges:
        graph.setdefault(edge.get("waiter_thread_id"), []).append(edge.get("holder_thread_id"))
    visiting: set[Any] = set()
    visited: set[Any] = set()

    def visit(node: Any) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for following in graph.get(node, []):
            if visit(following):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph if node not in visited)


def validate_deadlock_evidence(
    snapshots: Sequence[Mapping[str, Any]], *, timed_out: bool
) -> dict[str, Any] | None:
    if not timed_out:
        return None
    for offset in range(max(0, len(snapshots) - 2)):
        group = snapshots[offset:offset + 3]
        if len(group) != 3:
            continue
        signatures = []
        topologies = []
        valid = True
        for snapshot in group:
            nodes = snapshot.get("nodes")
            edges = snapshot.get("edges")
            if not isinstance(nodes, list) or not isinstance(edges, list) or not nodes or not edges:
                valid = False
                break
            by_thread = {node.get("thread_id"): node for node in nodes if isinstance(node, Mapping)}
            if len(by_thread) != len(nodes):
                valid = False
                break
            for edge in edges:
                if not isinstance(edge, Mapping):
                    valid = False
                    break
                waiter = by_thread.get(edge.get("waiter_thread_id"))
                holder = by_thread.get(edge.get("holder_thread_id"))
                if waiter is None or holder is None:
                    valid = False
                    break
                if edge.get("lock_id") != waiter.get("wait_lock_id"):
                    valid = False
                    break
                if edge.get("compatible") is not False:
                    valid = False
                    break
                if edge.get("request_mode") != waiter.get("request_mode"):
                    valid = False
                    break
                if not _holder_evidence(holder, edge):
                    valid = False
                    break
                if edge.get("holder_mode") is None or not _edge_is_incompatible(
                    edge.get("request_mode"), edge.get("holder_mode")
                ):
                    valid = False
                    break
            if valid and not _has_directed_cycle(edges):
                valid = False
            signatures.append(sorted(_node_signature(node) for node in nodes))
            topologies.append(sorted(_edge_signature(edge) for edge in edges))
        if (
            valid
            and signatures[0] == signatures[1] == signatures[2]
            and topologies[0] == topologies[1] == topologies[2]
        ):
            return {"snapshot_indexes": [offset, offset + 1, offset + 2], "snapshot": dict(group[0])}
    return None


def _phase2_counters(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    for event in reversed(events):
        if all(key in event for key in ("conflict_count", "no_wait_failure_count", "acquisition_paths")):
            paths = event["acquisition_paths"]
            conflict_count = int(event["conflict_count"])
            failure_count = int(event["no_wait_failure_count"])
            if not isinstance(paths, Mapping) or not paths:
                break
            if conflict_count <= 0 or failure_count <= 0:
                raise ContractError(
                    "phase2 requires positive conflict and No-Wait failure observations"
                )
            return {
                "conflict_count": conflict_count,
                "no_wait_failure_count": failure_count,
                "acquisition_paths": dict(paths),
            }
    raise ContractError("phase2 conflict, No-Wait failure, and acquisition-path counters are missing")


def _observed_conflict_count(events: Sequence[Mapping[str, Any]]) -> int | None:
    for event in reversed(events):
        if "conflict_count" not in event:
            continue
        value = int(event["conflict_count"])
        if value < 0:
            raise ContractError("observed conflict count must be nonnegative")
        return value
    return None


def _admit_output(
    stdout: str,
    *,
    arm: str,
    workload: Mapping[str, Any],
    build: Mapping[str, Any],
    binary: Path,
    thread_num: int,
    require_thread_commits: bool,
    require_metrics: bool = True,
) -> dict[str, Any]:
    requested_cache = build.get("requested_cache")
    observed_cache = build.get("observed_cache")
    if not isinstance(requested_cache, Mapping) or not isinstance(observed_cache, Mapping):
        raise ContractError("build cache receipt is missing")
    _validate_cache(requested_cache, observed_cache)
    _validate_recorded_compile_definitions(build.get("compile_definitions", []), requested_cache)
    axes, show_line = parse_runtime_axes(stdout)
    validate_build_binding(ARM_CONFIG[arm], axes)
    flags, flag_lines = parse_runtime_flags(stdout)
    validate_workload_binding(workload, flags)
    current_sha = sha256_file(binary)
    if current_sha != build["binary_sha256"] or not _HASH_RE.fullmatch(current_sha):
        raise ContractError("binary sha256 changed after build admission")
    events = _json_events(stdout)
    metrics: dict[str, Any] = {}
    if require_metrics:
        abort_count = int(_metric(stdout, "abort_counts_", int))
        commit_count = int(_metric(stdout, "commit_counts_", int))
        displayed_rate = float(_metric(stdout, "abort_rate", float))
        metrics = canonical_abort_metrics(abort_count, commit_count, displayed_rate)
        metrics["throughput_tps"] = float(_metric(stdout, "throughput[tps]", float))
        if not math.isfinite(metrics["throughput_tps"]) or metrics["throughput_tps"] <= 0:
            raise ContractError("throughput must be finite and positive")
        metrics["actual_extime_s"] = float(_metric(stdout, "actual_extime", float))
        if not 9.0 <= metrics["actual_extime_s"] <= 15.0:
            raise ContractError(
                f"actual_extime is outside the accepted 10-second run window: {metrics['actual_extime_s']}"
            )
    if require_thread_commits and require_metrics:
        commits = _thread_commits(stdout, events, thread_num)
        if sum(commits) != metrics["commit_count"]:
            raise ContractError(
                f"per-thread commits sum {sum(commits)} != commit_counts_ {metrics['commit_count']}"
            )
        metrics["thread_commit_counts"] = commits
        metrics["starvation_observation"] = {
            "minimum": min(commits), "maximum": max(commits), "gini": _gini(commits),
            "zero_commit_threads": [index for index, value in enumerate(commits) if value == 0],
            "starvation_suspected": any(value == 0 for value in commits),
        }
    return {
        "runtime_axes": axes,
        "show_opt_parameters_line": show_line,
        "runtime_workload_flags": flags,
        "runtime_workload_flag_lines": flag_lines,
        "binary_sha256": current_sha,
        "metrics": metrics,
        "json_events": events,
        "layout": _parse_layout(events),
    }


def _read_proc_ticks() -> dict[int, tuple[int, int, str]]:
    result: dict[int, tuple[int, int, str]] = {}
    own_pid = os.getpid()
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        pid = int(path.name)
        if pid == own_pid:
            continue
        try:
            uid = path.stat().st_uid
            stat_fields = (path / "stat").read_text(encoding="utf-8").split()
            ticks = int(stat_fields[13]) + int(stat_fields[14])
            command = (path / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace").strip()
        except (FileNotFoundError, PermissionError, IndexError, ValueError, OSError):
            continue
        result[pid] = (uid, ticks, command[:512])
    return result


def observe_isolation(
    *, scope: str, block_attempt_id: str | None = None, sample_seconds: float = 0.25
) -> dict[str, Any]:
    before = _read_proc_ticks()
    time.sleep(sample_seconds)
    after = _read_proc_ticks()
    own_uid = os.getuid()
    other: list[dict[str, Any]] = []
    competing: list[dict[str, Any]] = []
    for pid, (uid, ticks_after, command) in after.items():
        previous = before.get(pid)
        if previous is None:
            continue
        delta = ticks_after - previous[1]
        if delta < 2:
            continue
        row = {"pid": pid, "uid": uid, "cpu_ticks_delta": delta, "command": command}
        if uid != own_uid:
            other.append(row)
        elif "ycsb_" in command and ".exe" in command:
            competing.append(row)
    proc_loadavg = Path("/proc/loadavg").read_text(encoding="ascii").strip()
    uptime_output, uptime_collection = _optional_command_output(["uptime"], timeout=10)
    uptime_text = uptime_output.strip() if uptime_output is not None else None
    load1 = float(proc_loadavg.split()[0])
    return {
        "scope": scope,
        "block_attempt_id": block_attempt_id,
        "monotonic_s": time.monotonic(),
        "uptime": uptime_text,
        "uptime_collection": uptime_collection,
        "proc_loadavg": proc_loadavg,
        "load1": load1,
        "other_user_cpu_processes": other,
        "competing_ycsb_processes": competing,
        "disturbed": bool(other or competing or load1 > 48.0),
        "disturbance_rule": "other-user or competing-ycsb CPU delta >=2 ticks, or load1 >48",
    }


def _qstat_elapse(pbs_jobid: str) -> dict[str, Any]:
    query_id = pbs_jobid.removeprefix("0:")
    output, record = _optional_command_output(["qstat", "-f", query_id], timeout=30)
    if output is None:
        return record
    record["qstat_stdout_sha256"] = record["stdout_sha256"]
    try:
        limits = re.findall(
            r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)",
            output,
        )
        remaining = re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$", output)
        if len(limits) != 1 or len(remaining) != 1:
            raise ContractError("qstat elapse fields are unavailable or ambiguous")
        limit_s = int(limits[0])
        remaining_s = int(remaining[0])
    except Exception as exc:
        record["collected"] = False
        record["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        return record
    record.update({
        "limit_s": limit_s,
        "remaining_s": remaining_s,
        "elapsed_s": limit_s - remaining_s,
    })
    return record


def _measurement_environment(node: str, pbs_jobid: str) -> dict[str, Any]:
    cpu_model = ""
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    uname = os.uname()
    selected_env = {
        key: os.environ[key]
        for key in ("PBS_QUEUE", "PBS_O_HOST", "OMP_NUM_THREADS")
        if key in os.environ
    }
    return {
        "node": node,
        "pbs_jobid": pbs_jobid,
        "cpu_model": cpu_model,
        "kernel": f"{uname.sysname} {uname.release}",
        "machine": uname.machine,
        "python": sys.version.split()[0],
        "selected_environment": selected_env,
    }


def _run_process(
    argv: Sequence[str], *, timeout_s: float, expected_timeout: bool | None
) -> tuple[int, str, str, bool, str]:
    process = subprocess.Popen(
        list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    timed_out = False
    termination = "natural"
    effective_timeout, limiting_stage = _bounded_timeout(timeout_s)
    try:
        stdout, stderr = process.communicate(timeout=effective_timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        termination = "term"
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            termination = "kill"
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    if timed_out and limiting_stage is not None:
        raise ContractError(
            f"{limiting_stage.name} stage deadline exceeded while running benchmark"
        )
    if expected_timeout is not None and timed_out != expected_timeout:
        raise ContractError(
            f"process timeout contract mismatch: expected_timeout={expected_timeout}, observed={timed_out}"
        )
    if not timed_out and process.returncode != 0:
        raise ContractError(f"benchmark exited {process.returncode}: {stderr[-4000:]}")
    return process.returncode, stdout, stderr, timed_out, termination


def _workload_argv(workload: Mapping[str, Any], *, threads: int, clocks_per_us: int, extime: int) -> list[str]:
    return [
        f"-clocks_per_us={clocks_per_us}", f"-extime={extime}", f"-thread_num={threads}",
        *[f"-{key}={value}" for key, value in workload.items()],
    ]


def _run_performance_once(
    *,
    build: Mapping[str, Any],
    arm: str,
    workload: Mapping[str, Any],
    thread_num: int,
    clocks_per_us: int,
    block_id: int,
    block_attempt: int,
    order_index: int,
    experiment: str,
    occasion: Mapping[str, str],
) -> dict[str, Any]:
    binary = Path(str(build["binary"]))
    argv = [str(binary), *_workload_argv(workload, threads=thread_num, clocks_per_us=clocks_per_us, extime=10)]
    start = time.monotonic()
    returncode, stdout, stderr, timed_out, termination = _run_process(argv, timeout_s=120, expected_timeout=False)
    end = time.monotonic()
    admitted = _admit_output(
        stdout, arm=arm, workload=workload, build=build, binary=binary,
        thread_num=thread_num, require_thread_commits=True,
    )
    return {
        **occasion,
        "experiment": experiment,
        "block_id": block_id,
        "block_attempt": block_attempt,
        "block_attempt_id": f"{experiment}-b{block_id}-a{block_attempt}",
        "order_index": order_index,
        "arm": arm,
        "thread_num": thread_num,
        "workload": dict(workload),
        "argv": argv[1:],
        "started_monotonic_s": start,
        "ended_monotonic_s": end,
        "duration_s": end - start,
        "returncode": returncode,
        "timed_out": timed_out,
        "termination": termination,
        "stdout_sha256": _sha256_bytes(stdout.encode()),
        "stderr_sha256": _sha256_bytes(stderr.encode()),
        **admitted,
    }


def _phase_accumulate(accumulator: dict[str, dict[str, float]], run: Mapping[str, Any]) -> None:
    arm = str(run["arm"])
    phase = "phase3" if arm == "B" else "phase4" if arm == "D" else f"arm_{arm}"
    row = accumulator.setdefault(phase, {
        "started_monotonic_s": float(run["started_monotonic_s"]),
        "ended_monotonic_s": float(run["ended_monotonic_s"]),
        "active_duration_s": 0.0,
    })
    row["started_monotonic_s"] = min(row["started_monotonic_s"], float(run["started_monotonic_s"]))
    row["ended_monotonic_s"] = max(row["ended_monotonic_s"], float(run["ended_monotonic_s"]))
    row["active_duration_s"] += float(run["duration_s"])


def _run_blocks(
    *,
    document: dict[str, Any],
    builds: Mapping[str, Mapping[str, Any]],
    arms: Sequence[str],
    threads: Sequence[int],
    workloads: Sequence[Mapping[str, Any]],
    blocks: int,
    experiment: str,
    clocks_per_us: int,
    max_block_retries: int,
    occasion: Mapping[str, str],
) -> None:
    for block_id in range(blocks):
        accepted = False
        for block_attempt in range(max_block_retries + 1):
            block_attempt_id = f"{experiment}-b{block_id}-a{block_attempt}-{uuid.uuid4().hex[:12]}"
            before = observe_isolation(scope="block_before", block_attempt_id=block_attempt_id)
            document["isolation_observations"].append(before)
            candidate: list[dict[str, Any]] = []
            if not before["disturbed"]:
                rotated = rotated_arm_order(arms, block_id)
                for workload in workloads:
                    for thread_num in threads:
                        for order_index, arm in enumerate(rotated):
                            build_key = arm if experiment != "E2" else f"{arm}-backoff0"
                            run = _run_performance_once(
                                build=builds[build_key], arm=arm, workload=workload,
                                thread_num=thread_num, clocks_per_us=clocks_per_us,
                                block_id=block_id, block_attempt=block_attempt,
                                order_index=order_index, experiment=experiment,
                                occasion=occasion,
                            )
                            run["block_attempt_id"] = block_attempt_id
                            candidate.append(run)
            after = observe_isolation(scope="block_after", block_attempt_id=block_attempt_id)
            document["isolation_observations"].append(after)
            if before["disturbed"] or after["disturbed"]:
                document["invalidated_blocks"].append({
                    "experiment": experiment, "block_id": block_id,
                    "block_attempt": block_attempt, "block_attempt_id": block_attempt_id,
                    "reason": "disturbance", "before": before, "after": after,
                    "discarded_runs": candidate,
                })
                continue
            document["performance_runs"].extend(candidate)
            for run in candidate:
                _phase_accumulate(document["phase_timings"], run)
            accepted = True
            break
        if not accepted:
            raise ContractError(
                f"block {experiment}/{block_id} exceeded disturbance retry limit {max_block_retries}"
            )


def rotated_arm_order(arms: Sequence[str], block_id: int) -> list[str]:
    if not arms or block_id < 0:
        raise ContractError("arm rotation requires nonempty arms and a nonnegative block")
    return [arms[(index + block_id) % len(arms)] for index in range(len(arms))]


def _run_phase_trial(
    *,
    phase: str,
    build: Mapping[str, Any],
    workload: Mapping[str, Any],
    trial: int,
    point: str,
    clocks_per_us: int,
    occasion: Mapping[str, str],
) -> dict[str, Any]:
    binary = Path(str(build["binary"])).resolve()
    argv = [str(binary), *_workload_argv(workload, threads=48, clocks_per_us=clocks_per_us, extime=10)]
    trial_dir = Path(tempfile.mkdtemp(
        dir=binary.parent, prefix=f"ss2pl-wfg-{phase}-{point}-t{trial}-",
    ))
    output_path = trial_dir / "final.json"
    argv.append(f"-ss2pl_wfg_output={output_path}")
    start = time.monotonic()
    expected_timeout = False if phase == "phase2" else None
    returncode, stdout, stderr, timed_out, termination = _run_process(
        argv, timeout_s=60 if phase == "phase1" else 62,
        expected_timeout=expected_timeout,
    )
    end = time.monotonic()
    stdout_path = trial_dir / "stdout.txt"
    stderr_path = trial_dir / "stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    wfg_output = {
        "path": str(output_path), "status": "missing",
        "sha256": None, "json": None, "error": None,
    }
    try:
        raw_output = output_path.read_bytes()
    except FileNotFoundError:
        pass
    except OSError as exc:
        wfg_output.update(status="read_error", error=str(exc))
    else:
        wfg_output["sha256"] = _sha256_bytes(raw_output)
        try:
            wfg_output["json"] = json.loads(raw_output.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            wfg_output.update(status="invalid_json", error=str(exc))
        else:
            wfg_output["status"] = "present"
    admitted = _admit_output(
        stdout, arm=phase, workload=workload, build=build, binary=binary,
        thread_num=48, require_thread_commits=False,
        require_metrics=phase != "phase1",
    )
    snapshots = _extract_snapshots(admitted["json_events"])
    accepted_cycle = validate_deadlock_evidence(snapshots, timed_out=timed_out)
    persistent_cycle = validate_deadlock_evidence(snapshots, timed_out=True)
    if phase == "phase2" and persistent_cycle is not None:
        raise ContractError("phase2 produced an accepted wait-for-graph cycle")
    counters = _phase2_counters(admitted["json_events"]) if phase == "phase2" else None
    conflict_count = _observed_conflict_count(admitted["json_events"])
    return {
        **occasion,
        "phase": phase, "point": point, "trial": trial,
        "block_id": trial, "thread_num": 48,
        "workload": dict(workload), "argv": argv[1:],
        "started_monotonic_s": start, "ended_monotonic_s": end,
        "duration_s": end - start, "returncode": returncode,
        "timed_out": timed_out, "termination": termination,
        "stdout_sha256": _sha256_bytes(stdout.encode()),
        "stderr_sha256": _sha256_bytes(stderr.encode()),
        "wfg_snapshots": snapshots,
        "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
        "wfg_output": wfg_output,
        "accepted_cycle": accepted_cycle,
        "cycle_observed": accepted_cycle is not None,
        "conflict_count": conflict_count,
        "conflict_observation": {
            "collected": conflict_count is not None,
            "count": conflict_count,
            "statement": (
                f"Observed conflict count: {conflict_count}."
                if conflict_count is not None
                else "No aggregate conflict counter was emitted before process termination."
            ),
        },
        "phase2_counters": counters,
        **{key: value for key, value in admitted.items() if key != "json_events"},
    }


def _run_controls_phases(
    document: dict[str, Any], builds: Mapping[str, Mapping[str, Any]],
    clocks_per_us: int, occasion: Mapping[str, str]
) -> None:
    points = {
        "high-contention": {**WORKLOAD_DEFAULT, "ycsb_tuple_num": 100, "ycsb_zipf_skew": 0},
        "headline": dict(WORKLOAD_DEFAULT),
    }
    for phase in ("phase1", "phase2"):
        phase_start = time.monotonic()
        active = 0.0
        for point, workload in points.items():
            for trial in range(3):
                run = _run_phase_trial(
                    phase=phase, build=builds[phase], workload=workload,
                    trial=trial, point=point, clocks_per_us=clocks_per_us,
                    occasion=occasion,
                )
                document["phase_runs"].append(run)
                active += run["duration_s"]
        phase_end = time.monotonic()
        document["phase_timings"][phase] = {
            "started_monotonic_s": phase_start,
            "ended_monotonic_s": phase_end,
            "active_duration_s": active,
        }
    phase1_runs = [run for run in document["phase_runs"] if run["phase"] == "phase1"]
    cycle_count = sum(run.get("accepted_cycle") is not None for run in phase1_runs)
    document["phase1_observation"] = {
        "trials": len(phase1_runs),
        "timeouts": sum(run.get("timed_out") is True for run in phase1_runs),
        "cycles_observed": cycle_count,
        "cycle_observation": f"{cycle_count} of {len(phase1_runs)} phase1 trials",
        "no_cycle_observed_in_window": cycle_count == 0,
        "statement": (
            "No persistent wait-for-graph cycle was observed in this observation window."
            if cycle_count == 0
            else "Persistent wait-for-graph cycles were observed in this observation window."
        ),
    }


def _validate_thirdparty(root: Path, policy: Mapping[str, Any]) -> list[dict[str, str]]:
    expected = {
        item["source_name"]: item["pin"]
        for item in policy["silo_ladder_rung1"]["third_party_sources"]
    }
    records = []
    for name, pin in expected.items():
        source = root / name
        if not source.is_dir() or source.is_symlink():
            raise ContractError(f"third-party source is not a real directory: {source}")
        head = _run_checked(["git", "-C", str(source), "rev-parse", "HEAD"]).stdout.strip()
        status = _run_checked(
            ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"]
        ).stdout
        if head != pin or status:
            raise ContractError(f"third-party source is not pinned-clean: {name}")
        records.append({"name": name, "path": str(source), "head": head, "status_porcelain": status})
    return records


@contextlib.contextmanager
def _timed_phase(document: dict[str, Any], name: str) -> Iterator[None]:
    start = time.monotonic()
    try:
        yield
    finally:
        end = time.monotonic()
        document["harness_timings"][name] = {
            "started_monotonic_s": start,
            "ended_monotonic_s": end,
            "duration_s": end - start,
        }


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ContractError(f"refusing to replace existing output: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, sort_keys=True, indent=2, ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--gflags-prefix", required=True, type=Path)
    parser.add_argument("--glog-prefix", required=True, type=Path)
    parser.add_argument("--thirdparty-root", required=True, type=Path)
    parser.add_argument("--clocks-per-us", required=True, type=int)
    parser.add_argument("--mode", required=True, choices=("sweep", "controls", "replication"))
    parser.add_argument("--max-block-retries", type=int, default=2)
    parser.add_argument("--jobs", type=int, default=48)
    parser.add_argument("--occasion-id")
    parser.add_argument("--build-cap-s", required=True, type=int)
    parser.add_argument("--run-cap-s", required=True, type=int)
    parser.add_argument("--collection-cap-s", required=True, type=int)
    return parser


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_root = args.repo_root.resolve(strict=True)
    patch = args.patch.resolve(strict=True)
    scratch_root = args.scratch_root.resolve(strict=True)
    gflags_prefix = args.gflags_prefix.resolve(strict=True)
    glog_prefix = args.glog_prefix.resolve(strict=True)
    thirdparty_root = args.thirdparty_root.resolve(strict=True)
    if (
        args.clocks_per_us <= 0 or not 1 <= args.jobs <= 48
        or args.max_block_retries < 0
        or min(args.build_cap_s, args.run_cap_s, args.collection_cap_s) <= 0
    ):
        raise ContractError("invalid clocks, jobs, block retry limit, or stage deadline")
    pbs_jobid = os.environ.get("PBS_JOBID", "")
    node = socket.gethostname()
    if not pbs_jobid or not node.startswith("bnode"):
        raise ContractError("SS2PL performance study must run inside a Pegasus bnode PBS job")
    occasion = {
        "occasion_id": args.occasion_id or f"{args.mode}-{uuid.uuid4().hex}",
        "pbs_jobid": pbs_jobid,
        "node": node,
    }
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "mode": args.mode,
        "aggregation_scope": "single occasion and single node; replication is never pooled",
        "occasion": occasion,
        "performance_runs": [],
        "phase_runs": [],
        "builds": [],
        "invalidated_blocks": [],
        "isolation_observations": [],
        "phase_timings": {},
        "harness_timings": {},
        "cleanup": {
            "reverse_attempted": False,
            "reverse_succeeded": False,
            "git_status_porcelain": None,
        },
        "pbs_elapse": {},
        "stage_deadlines": {},
        "environment": _measurement_environment(node, pbs_jobid),
        "process_internal_warmup": {
            "present": False,
            "statement": "the benchmark has no process-internal warmup interval",
        },
    }
    clone: Path | None = None
    stock_clone: Path | None = None
    patch_state = {"applied": False}
    preprocess_cache = PreprocessCache()
    baseline_source_state_sha256 = ""
    patched_source_state_sha256 = ""
    error: BaseException | None = None
    try:
        document["required_external_commands"] = validate_required_commands()
        document["pbs_elapse"]["start"] = _qstat_elapse(pbs_jobid)
        policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
        document["inputs"] = {
            "patch": str(patch), "patch_sha256": sha256_file(patch),
            "repo_root": str(repo_root), "clocks_per_us": args.clocks_per_us,
        }
        builds: dict[str, dict[str, Any]] = {}
        with _stage_deadline(document, "build", args.build_cap_s):
            document["inputs"]["third_party"] = _validate_thirdparty(thirdparty_root, policy)
            with _timed_phase(document, "canonical_and_clone"):
                canonical = verify_canonical_submodule(repo_root)
                document["canonical_submodule"] = canonical
                baseline_source_state_sha256 = _sha256_bytes(
                    f"baseline\0{canonical['head']}".encode()
                )
                patched_source_state_sha256 = _sha256_bytes(
                    f"patched\0{canonical['head']}\0{document['inputs']['patch_sha256']}".encode()
                )
                attempt_root = scratch_root / f"ss2pl-lock-study-{occasion['occasion_id']}"
                attempt_root.mkdir(mode=0o700)
                clone = attempt_root / "ccbench"
                stock_clone = attempt_root / "condition-gate-stock"
                build_root = attempt_root / "builds"
                build_root.mkdir()
                clone_network_free(Path(canonical["path"]), stock_clone)
                clone_network_free(Path(canonical["path"]), clone)
                _apply_patch(clone, patch, reverse=False)
                patch_state["applied"] = True
                document["abort_counter_ownership"] = validate_abort_counter_ownership(clone)

            with _timed_phase(document, "inert_witness"):
                try:
                    witness_build = build_root / "inert-witness"
                    expected = _configure(
                        clone, witness_build, arm="S", backoff=1,
                        gflags_prefix=gflags_prefix, glog_prefix=glog_prefix,
                        thirdparty_root=thirdparty_root,
                    )
                    witness_entries = _target_compile_entries(
                        witness_build, "bomb_ss2pl.exe"
                    )
                    _validate_compile_definitions(witness_entries, expected)
                    document["inert_witness"] = collect_inert_witness_observation(
                        clone, patch, witness_entries, patch_state,
                        preprocess_cache=preprocess_cache,
                        baseline_source_state_sha256=baseline_source_state_sha256,
                        patched_source_state_sha256=patched_source_state_sha256,
                    )
                except Exception as exc:
                    document["inert_witness"] = _uncollected_inert_witness(exc)

            with _timed_phase(document, "builds"):
                for arm in PERFORMANCE_ARMS:
                    builds[arm] = build_target(
                        clone, stock_clone, build_root,
                        build_id=arm, arm=arm, backoff=1,
                        gflags_prefix=gflags_prefix, glog_prefix=glog_prefix,
                        thirdparty_root=thirdparty_root, jobs=args.jobs,
                        preprocess_cache=preprocess_cache,
                        source_state_sha256=patched_source_state_sha256,
                    )
                if args.mode == "controls":
                    for arm in ("B", "D"):
                        key = f"{arm}-backoff0"
                        builds[key] = build_target(
                            clone, stock_clone, build_root,
                            build_id=key, arm=arm, backoff=0,
                            gflags_prefix=gflags_prefix, glog_prefix=glog_prefix,
                            thirdparty_root=thirdparty_root, jobs=args.jobs,
                            preprocess_cache=preprocess_cache,
                            source_state_sha256=patched_source_state_sha256,
                        )
                    for phase in ("phase1", "phase2"):
                        builds[phase] = build_target(
                            clone, stock_clone, build_root,
                            build_id=phase, arm=phase, backoff=1,
                            gflags_prefix=gflags_prefix, glog_prefix=glog_prefix,
                            thirdparty_root=thirdparty_root, jobs=args.jobs,
                            preprocess_cache=preprocess_cache,
                            source_state_sha256=patched_source_state_sha256,
                        )
                document["builds"] = list(builds.values())
                document["preprocessing_cache"] = preprocess_cache.summary()

        with _stage_deadline(document, "run", args.run_cap_s), _timed_phase(document, "measurements"):
            document["isolation_observations"].append(observe_isolation(scope="job_before"))
            if args.mode in {"sweep", "replication"}:
                blocks = SWEEP_BLOCKS if args.mode == "sweep" else REPLICATION_BLOCKS
                _run_blocks(
                    document=document, builds=builds, arms=PERFORMANCE_ARMS,
                    threads=THREADS, workloads=[WORKLOAD_DEFAULT], blocks=blocks,
                    experiment=args.mode, clocks_per_us=args.clocks_per_us,
                    max_block_retries=args.max_block_retries, occasion=occasion,
                )
                validate_matrix(
                    document["performance_runs"], arms=PERFORMANCE_ARMS,
                    threads=THREADS, blocks=range(blocks), experiment=args.mode,
                )
            else:
                e1_workloads = [
                    {**WORKLOAD_DEFAULT, "ycsb_rratio": ratio, "ycsb_zipf_skew": skew}
                    for skew in (0, 0.9) for ratio in (0, 50, 100)
                ]
                _run_blocks(
                    document=document, builds=builds, arms=PERFORMANCE_ARMS,
                    threads=(24, 48), workloads=e1_workloads, blocks=3,
                    experiment="E1", clocks_per_us=args.clocks_per_us,
                    max_block_retries=args.max_block_retries, occasion=occasion,
                )
                _run_blocks(
                    document=document, builds=builds, arms=("B", "D"),
                    threads=(1, 24, 48), workloads=[WORKLOAD_DEFAULT], blocks=3,
                    experiment="E2", clocks_per_us=args.clocks_per_us,
                    max_block_retries=args.max_block_retries, occasion=occasion,
                )
                validate_control_matrices(document["performance_runs"])
                _run_controls_phases(document, builds, args.clocks_per_us, occasion)
                validate_phase_matrix(document["phase_runs"])

        with _stage_deadline(document, "collection", args.collection_cap_s) as collection_deadline:
            validate_preprocessing_receipts(document)
            validate_mode_document(document, args.mode)
            collection_deadline.check()
            document["status"] = "complete"
    except BaseException as exc:  # cleanup and failure receipt are part of the contract
        error = exc
        document["status"] = "failed"
        document["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        cleanup = document["cleanup"]
        if clone is not None:
            cleanup["reverse_attempted"] = True
            try:
                if patch_state["applied"]:
                    _apply_patch(clone, patch, reverse=True)
                    patch_state["applied"] = False
                cleanup["reverse_succeeded"] = True
                cleanup["git_status_porcelain"] = _run_checked(
                    ["git", "-C", str(clone), "status", "--porcelain", "--untracked-files=all"]
                ).stdout
                validate_patch_cleanup(cleanup)
            except BaseException as cleanup_exc:
                cleanup["reverse_succeeded"] = False
                cleanup["failure"] = {"type": type(cleanup_exc).__name__, "message": str(cleanup_exc)}
                document["status"] = "failed"
                document["failure"] = {
                    "type": type(cleanup_exc).__name__,
                    "message": f"cleanup failed after {type(error).__name__ if error else 'successful run'}: {cleanup_exc}",
                }
                error = cleanup_exc
        document["pbs_elapse"]["end"] = _qstat_elapse(pbs_jobid)
        document["preprocessing_cache"] = preprocess_cache.summary()
        document["completed_monotonic_s"] = time.monotonic()
    return (0 if error is None and document["status"] == "complete" else 1), document


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        rc, document = run(args)
        _atomic_json(args.output.resolve(), document)
        return rc
    except BaseException as exc:
        print(f"ss2pl lock study failed before receipt publication: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
