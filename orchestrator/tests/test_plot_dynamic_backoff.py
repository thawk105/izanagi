# -*- coding: utf-8 -*-
"""End-to-end tests for the preregistered dynamic-backoff figure generator."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys

import pytest

from tools.pegasus.probes import t2187_adaptive_const_probe as producer
from tools.plotting import plot_dynamic_backoff as plot
from tools.plotting.plot_t2187_adaptive_consts import FigureLayoutError


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "plotting" / "plot_dynamic_backoff.py"
PERFORMANCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v2"
DIAGNOSTIC_SCHEMA = "izanagi-dynamic-backoff-trace/v2"
COUNTERFACTUAL_PERFORMANCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v3"
COUNTERFACTUAL_DIAGNOSTIC_SCHEMA = "izanagi-dynamic-backoff-trace/v3"
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
THREADS = (6, 12, 18, 24, 30, 36, 42, 48)
CELLS = (
    "none", "stock", "tuned", "tuned-u10240", "cw", "cw-as", "cw-as-dyn",
)
TRACE_CELLS = ("cw", "cw-as", "cw-as-dyn")
COHORT1_TRACE_CELLS = ("cw-as-dyn-p0", "cw-as-dyn-p1", "cw-as-dyn-p2")
COHORT2_TRACE_CELLS = (
    "cw-as-dyn-c2-p0", "cw-as-dyn-c2-p1", "cw-as-dyn-c2-p2",
)
PIN = "511c953"
FULL_PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PATCH_A = "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"
PATCH_B = "3" * 64
PATCH_C = "6" * 64
DRIVER_SHA = "4" * 64
PBS_SHA = "5" * 64
PATCH_STACK = [
    {"path": "patches/cicada-adaptive-params.patch", "sha256": PATCH_A},
    {"path": "patches/cicada-adaptive-dynamic.patch", "sha256": PATCH_B},
]
COUNTERFACTUAL_PATCH_STACK = [
    *PATCH_STACK,
    {
        "path": "patches/cicada-adaptive-counterfactual.patch",
        "sha256": PATCH_C,
    },
]

CELL_CONFIGS = {
    "none": (0, 100, 1000, 10, 0, 0, 0, 100, 100, 0, False),
    "stock": (1, 100, 1000, 10, 0, 0, 0, 100, 100, 0, True),
    "tuned": (1, 1, 1000, 2560, 0, 0, 0, 100, 100, 0, False),
    "tuned-u10240": (1, 1, 1000, 10240, 0, 0, 0, 100, 100, 0, False),
    "cw": (1, 1, 1000, 2560, 10000, 10240, 0, 100, 100, 0, False),
    "cw-as": (1, 1, 1000, 2560, 10000, 10240, 1, 1, 4, 0, False),
    "cw-as-dyn": (1, 1, 1000, 2560, 10000, 10240, 1, 1, 4, 1, False),
}
CONFIG_FIELDS = (
    "back_off", "step_us", "ceiling_us", "update_us", "count_window",
    "count_cap_us", "step_adapt", "step_min_us", "step_max_us",
    "dyn_ceiling", "is_stock_control",
)


def _stack_sha(stack: list[dict[str, str]] = PATCH_STACK) -> str:
    text = "izanagi-patch-stack/v1\n" + "".join(
        f"{row['path']} {row['sha256']}\n" for row in stack
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identity() -> dict:
    return {
        "repo_head": "1" * 40,
        "prereg_sha256": "2" * 64,
        "ccbench_commit": PIN,
        "ccbench_head": FULL_PIN,
        "driver_sha256": DRIVER_SHA,
        "pbs_sha256": PBS_SHA,
        "repo_status_clean": True,
        "patch_sha256": PATCH_A,
        "dynamic_patch_sha256": PATCH_B,
        "patch_stack": PATCH_STACK,
        "patch_stack_sha256": _stack_sha(),
        "records": 1_000_000,
        "extime_s": 3,
        "clocks_per_us": 2100,
    }


def _execution(rep_index: int, *, diagnostic: bool = False) -> dict:
    return {
        "driver_argv": [
            "python3", "tools/pegasus/probes/t2187_adaptive_const_probe.py",
            "--rep-index", str(rep_index),
            *(["--backoff-trace"] if diagnostic else []),
        ],
        "prologue_elapsed_s": 10.0 + rep_index,
        "prologue_cpu_s": 2.0 + rep_index / 10.0,
        "job_total_seconds": 100.0 + rep_index,
    }


def _use_counterfactual_stack(document: dict) -> None:
    schema = document["schema_version"]
    if schema == PERFORMANCE_SCHEMA:
        document["schema_version"] = COUNTERFACTUAL_PERFORMANCE_SCHEMA
    elif schema == DIAGNOSTIC_SCHEMA:
        document["schema_version"] = COUNTERFACTUAL_DIAGNOSTIC_SCHEMA
    else:
        raise AssertionError(schema)
    document["counterfactual_patch_sha256"] = PATCH_C
    document["patch_stack"] = COUNTERFACTUAL_PATCH_STACK
    document["patch_stack_sha256"] = _stack_sha(COUNTERFACTUAL_PATCH_STACK)


def _counterfactualize_inputs(performance: list[Path], diagnostic: Path) -> None:
    for path in [*performance, diagnostic]:
        document = json.loads(path.read_text(encoding="utf-8"))
        _use_counterfactual_stack(document)
        _write(path, document)


def _near_margin_ratio(mean_ratio: float, rep_index: int) -> float:
    """Return seven log-symmetric samples with a narrow CI around mean_ratio."""
    return math.exp(math.log(mean_ratio) + (rep_index - 3) * 0.0045)


def _arm_ratio(
    cell: str, workload: str, threads: int, rep_index: int,
) -> float:
    # The paired ratios deliberately produce accepted, rejected, and
    # inconclusive preregistered hypotheses in one full-size fixture.
    if cell == "cw-as-dyn" and workload == "read-heavy" and threads == 6:
        return 1.60
    if cell == "cw-as-dyn" and workload == "write-heavy" and threads == 48:
        return _near_margin_ratio(1.0425, rep_index)
    if cell == "cw-as-dyn" and workload == "balanced" and threads == 48:
        return 1.08
    if cell == "stock" and workload == "write-heavy" and threads == 6:
        return _near_margin_ratio(0.9575, rep_index)
    if cell in ("stock", "cw"):
        return 0.92 + rep_index * (0.04 / 6.0)
    if cell == "tuned-u10240":
        return 1.00 + rep_index * 0.01
    if cell == "cw-as-dyn":
        return 1.04 + rep_index * (0.04 / 6.0)
    return 1.0


def _performance_cell(
    cell: str, workload: str, threads: int, rep_index: int,
) -> dict:
    workload_factor = {
        "write-heavy": 0.90, "balanced": 1.00, "read-heavy": 1.18,
    }[workload]
    block_factor = 1.0 + 0.015 * rep_index
    tuned_tps = 900_000.0 * workload_factor * (threads / 6.0) * block_factor
    throughput = tuned_tps * _arm_ratio(cell, workload, threads, rep_index)
    config = dict(zip(CONFIG_FIELDS, CELL_CONFIGS[cell], strict=True))
    return {
        "cell": cell,
        "workload": workload,
        "threads": threads,
        **config,
        "binary_sha256": hashlib.sha256(cell.encode("utf-8")).hexdigest(),
        "throughputs": [throughput],
        "median_tps": throughput,
        "abort_rate": 0.01 + CELLS.index(cell) * 0.002 + threads / 10000.0
        + rep_index / 10000.0,
        "backoff_trace_symbol_count": 0,
        "backoff_trace_string_count": 0,
        "cell_format_fields": 11 if cell in TRACE_CELLS else 5,
    }


def _performance_document(rep_index: int) -> dict:
    order = list(CELLS[rep_index:] + CELLS[:rep_index])
    cells = [
        _performance_cell(cell, workload, threads, rep_index)
        for cell in order for workload in WORKLOADS for threads in THREADS
    ]
    assert len(cells) == 168
    return {
        "schema_version": PERFORMANCE_SCHEMA,
        "kind": "performance-only-probe",
        "rep_index": rep_index,
        "hostname": f"bnode{rep_index:03d}",
        "cell_order": order,
        **_identity(),
        **_execution(rep_index),
        "pbs_jobid": f"0:{980000 + rep_index}.nqsv",
        "cells": cells,
    }


def _producer_trace(*, zero_scored: bool = False) -> tuple[list[dict], dict, dict]:
    records = [
        "IZANAGI_BACKOFF_TRACE v=1 seq=0 tsc=1000000 window_us=100 "
        "window_commits=10000 trigger=0 backoff_before=100 backoff_after=101 "
        "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=-1",
    ]
    if not zero_scored:
        records.extend([
            "IZANAGI_BACKOFF_TRACE v=1 seq=1 tsc=1210000 window_us=100 "
            "window_commits=10100 trigger=1 backoff_before=101 backoff_after=102 "
            "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=0",
            "IZANAGI_BACKOFF_TRACE v=1 seq=2 tsc=1420000 window_us=100 "
            "window_commits=10000 trigger=2 backoff_before=102 backoff_after=102 "
            "gradient_sign=-1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=1",
            "IZANAGI_BACKOFF_TRACE v=1 seq=3 tsc=1630000 window_us=100 "
            "window_commits=10200 trigger=0 backoff_before=102 backoff_after=103 "
            "gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=1",
        ])
    retained = len(records)
    stdout = "\n".join([
        "unrelated benchmark output", *records,
        f"IZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates={retained} "
        f"retained={retained} dropped=0",
    ])
    return producer._parse_backoff_trace(stdout)


def _diagnostic_document(*, zero_scored: bool = False) -> dict:
    events, summary, directional = _producer_trace(zero_scored=zero_scored)
    runs = []
    for cell in TRACE_CELLS:
        for workload in WORKLOADS:
            for threads in (24, 48):
                runs.append({
                    "cell": cell,
                    "workload": workload,
                    "threads": threads,
                    **dict(zip(CONFIG_FIELDS, CELL_CONFIGS[cell], strict=True)),
                    "cell_format_fields": 11,
                    "genome": f"fixture:{cell}:{workload}:{threads}",
                    "binary_sha256": hashlib.sha256(cell.encode("utf-8")).hexdigest(),
                    "throughputs": [1_000_000.0 + 1000 * threads],
                    "median_tps": 1_000_000.0 + 1000 * threads,
                    "backoff_trace_symbol_count": 1,
                    "backoff_trace_string_count": 2,
                    "trace_events": copy.deepcopy(events),
                    "trace_summary": copy.deepcopy(summary),
                    "directional_success": copy.deepcopy(directional),
                })
    assert len(runs) == 18
    return {
        "schema_version": DIAGNOSTIC_SCHEMA,
        "kind": "diagnostic-backoff-trace",
        "headline_eligible": False,
        "rep_index": 0,
        "hostname": "bnode099",
        **_identity(),
        **_execution(0, diagnostic=True),
        "pbs_jobid": "0:980099.nqsv",
        "trace_runs": runs,
    }


def _policy_trace(*, terminal: bool) -> tuple[list[dict], dict, dict]:
    events = []
    for index, assigned in enumerate((0, 1, 0, 1)):
        events.append({
            "seq": index,
            "tsc": 1_000_000 + index * 210_000,
            "window_us": 100,
            "window_commits": 10_000 + index * 100,
            "trigger": "count",
            "backoff_before": 100 + index,
            "backoff_after": 101 + index,
            "gradient_sign": 1,
            "step_us": 1,
            "ceiling_us": 1000,
            "ceiling_changed": 0,
            "parity_branch": "none" if index == 0 else "increment",
            "assigned_invert": assigned,
            "recommended_delta_sign": (-1, 0, 1, 1)[index],
            "inversion_realized": 0,
            "both_actions_feasible": index % 2,
            **({"terminal_flush": 0} if terminal else {}),
        })
    if terminal:
        events.append({
            "seq": 4,
            "tsc": 1_840_000,
            "window_us": 100,
            "window_commits": 10_400,
            "trigger": "terminal",
            "backoff_before": 104,
            "backoff_after": 104,
            "gradient_sign": 0,
            "step_us": 1,
            "ceiling_us": 1000,
            "ceiling_changed": 0,
            "parity_branch": "none",
            "assigned_invert": -1,
            "recommended_delta_sign": 0,
            "inversion_realized": 0,
            "both_actions_feasible": 0,
            "terminal_flush": 1,
        })
    scored, successes, rate = plot._directional_success(events)
    summary = {
        "updates": 4,
        "retained": 4,
        "dropped": 0,
        **({"flushes": 1} if terminal else {}),
    }
    return events, summary, {
        "scored": scored, "successes": successes, "rate": rate,
    }


def _policy_diagnostic_document(*, cohort2: bool) -> dict:
    cells = COHORT2_TRACE_CELLS if cohort2 else COHORT1_TRACE_CELLS
    literals = (
        plot.COHORT2_CELL_LITERALS if cohort2 else plot.COHORT1_CELL_LITERALS
    )
    events, summary, directional = _policy_trace(terminal=cohort2)
    runs = []
    for policy, cell in enumerate(cells):
        for workload in WORKLOADS:
            for threads in (24, 48):
                runs.append({
                    "cell": cell,
                    "workload": workload,
                    "threads": threads,
                    **dict(zip(CONFIG_FIELDS, plot.CELL_CONFIGS[cell], strict=True)),
                    "cell_format_fields": 12,
                    "step_policy": policy,
                    "genome": f"fixture:{cell}:{workload}:{threads}",
                    "binary_sha256": hashlib.sha256(cell.encode("utf-8")).hexdigest(),
                    "throughputs": [1_000_000.0 + 1000 * threads],
                    "median_tps": 1_000_000.0 + 1000 * threads,
                    "backoff_trace_symbol_count": 1,
                    "backoff_trace_string_count": 2,
                    "trace_events": copy.deepcopy(events),
                    "trace_summary": copy.deepcopy(summary),
                    "directional_success": copy.deepcopy(directional),
                })
    document = {
        "schema_version": DIAGNOSTIC_SCHEMA,
        "kind": "diagnostic-backoff-trace",
        "headline_eligible": False,
        "rep_index": 0,
        "hostname": "bnode099",
        **_identity(),
        **_execution(0, diagnostic=True),
        "pbs_jobid": "0:980099.nqsv",
        "cell_order": list(cells),
        "grid_spec": ",".join(literals),
        "trace_runs": runs,
    }
    _use_counterfactual_stack(document)
    if cohort2:
        document["schema_version"] = plot.COHORT2_DIAGNOSTIC_SCHEMA
        document["extime_s"] = 6
        document["counterfactual_preregistration"] = (
            "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
        )
    return document


def _remove_policy_terminals(document: dict) -> None:
    for row in document["trace_runs"]:
        terminal = row["trace_events"].pop()
        assert terminal["terminal_flush"] == 1
        events = row["trace_events"]
        row["trace_summary"] = {
            "updates": len(events),
            "retained": len(events),
            "dropped": 0,
            "flushes": 0,
        }
        scored, successes, rate = plot._directional_success(events)
        row["directional_success"] = {
            "scored": scored,
            "successes": successes,
            "rate": rate,
        }


def _policy_fixture_inputs(
    tmp_path: Path, *, cohort2: bool,
) -> tuple[list[Path], Path]:
    performance = []
    for index in range(7):
        document = _performance_document(index)
        _use_counterfactual_stack(document)
        if cohort2:
            document["extime_s"] = 6
        performance.append(
            _write(tmp_path / f"policy-performance-rep-{index}.json", document)
        )
    diagnostic = _write(
        tmp_path / "policy-diagnostic.json",
        _policy_diagnostic_document(cohort2=cohort2),
    )
    return performance, diagnostic


def _write(path: Path, value: dict) -> Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return path


def _fixture_inputs(tmp_path: Path) -> tuple[list[Path], Path]:
    performance = [
        _write(tmp_path / f"performance-rep-{index}.json", _performance_document(index))
        for index in range(7)
    ]
    diagnostic = _write(tmp_path / "diagnostic.json", _diagnostic_document())
    return performance, diagnostic


def _run(
    tmp_path: Path, name: str, performance: list[Path], diagnostic: Path,
    extra: list[str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    prefix = tmp_path / name
    mpl_config = tmp_path / "mpl-config"
    mpl_config.mkdir(exist_ok=True)
    environment = dict(os.environ)
    environment["MPLCONFIGDIR"] = str(mpl_config)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        sys.executable, str(SCRIPT), str(prefix), "--trace-json", str(diagnostic),
        *(extra or []), *map(str, performance),
    ]
    result = subprocess.run(
        command, cwd=REPO, env=environment, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    return result, prefix


def _output_paths(prefix: Path) -> list[Path]:
    return [
        Path(f"{prefix}-{name}.{suffix}")
        for name in ("thread-axis", "contrasts", "diagnostic")
        for suffix in ("png", "pdf")
    ] + [Path(f"{prefix}.provenance.json")]


def test_full_size_fixture_writes_three_figures_and_frozen_statistics(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    result, prefix = _run(tmp_path, "dynamic", performance, diagnostic)
    assert result.returncode == 0, result.stderr
    for path in _output_paths(prefix):
        assert path.is_file() and path.stat().st_size > 0

    provenance_path = Path(f"{prefix}.provenance.json")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert set(provenance) == {
        "provenance_schema_version", "performance_schema_version",
        "diagnostic_schema_version", "generated_utc", "generator", "inputs",
        "outputs", "repo_head", "prereg_sha256", "ccbench_commit",
        "ccbench_head", "driver_sha256", "pbs_sha256", "repo_status_clean",
        "patch_sha256", "dynamic_patch_sha256", "patch_stack",
        "patch_stack_sha256", "pbs_jobids", "hostnames", "hostname_duplicates",
        "measurement_conditions", "ci95", "performance_values_certified",
        "performance_certification_notice", "performance_aggregates", "contrasts",
        "abort_contrasts", "hypotheses", "diagnostic", "captions", "reproduction",
    }
    assert provenance["provenance_schema_version"] == (
        "izanagi-dynamic-backoff-figure-provenance/v1"
    )
    assert provenance["performance_values_certified"] is False
    assert provenance["performance_certification_notice"] == "性能値は未認証"
    assert len(provenance["performance_aggregates"]) == 168
    assert len(provenance["contrasts"]) == 7
    assert all(len(contrast["points"]) == 24 for contrast in provenance["contrasts"])
    assert {value["status"] for value in provenance["hypotheses"].values()} >= {
        "accepted", "rejected", "inconclusive",
    }
    assert all(
        set(value) == {"acceptance_condition", "status", "failed_predicates"}
        for value in provenance["hypotheses"].values()
    )
    assert all(value["acceptance_condition"] for value in provenance["hypotheses"].values())
    assert len(provenance["abort_contrasts"]) == 7
    abort_point = provenance["abort_contrasts"][0]["points"][0]
    assert abort_point["n"] == 7
    assert abort_point["samples_percentage_points"] == pytest.approx([0.8] * 7)
    assert abort_point["mean_percentage_points"] == pytest.approx(0.8)
    assert abort_point["ci95_lower_percentage_points"] == pytest.approx(0.8)
    assert abort_point["ci95_upper_percentage_points"] == pytest.approx(0.8)
    assert provenance["diagnostic"]["throughput_plotted"] is False
    assert "診断 build 由来・計装系の軌跡・headline 不適格" in (
        provenance["captions"]["diagnostic"]
    )

    expected_hashes = {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [*performance, diagnostic]
    }
    assert len(provenance["inputs"]) == 8
    assert {row["path"]: row["sha256"] for row in provenance["inputs"]} == expected_hashes
    assert len(provenance["outputs"]) == 6
    assert provenance["ccbench_head"] == FULL_PIN
    assert provenance["driver_sha256"] == DRIVER_SHA
    assert provenance["pbs_sha256"] == PBS_SHA
    assert provenance["repo_status_clean"] is True
    assert provenance["hostname_duplicates"] == []
    for row in provenance["inputs"]:
        assert set((
            "driver_sha256", "pbs_sha256", "driver_argv", "repo_status_clean",
            "ccbench_head", "prologue_elapsed_s", "prologue_cpu_s",
            "job_total_seconds",
        )) <= set(row)
    assert all(
        row["sha256"] == hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest()
        for row in provenance["outputs"]
    )

    point = provenance["contrasts"][0]["points"][0]
    samples = point["log_ratio_samples"]
    expected_half = 2.4469118511449692 * statistics.stdev(samples) / math.sqrt(7)
    actual_half = point["ci95_upper_log_ratio"] - point["mean_log_ratio"]
    assert math.isclose(actual_half, expected_half, rel_tol=0.0, abs_tol=1e-12)
    wrong_half = 1.96 * statistics.stdev(samples) / math.sqrt(7)
    assert not math.isclose(actual_half, wrong_half, rel_tol=0.0, abs_tol=1e-5)


def test_plot_accepts_both_ab_and_abc_stacks(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    ab_data = plot.load_inputs(performance, diagnostic)
    assert ab_data["identity"]["patch_stack"] == PATCH_STACK
    assert ab_data["identity"]["patch_stack_version"] == "A+B"
    assert ab_data["performance_schema_version"] == PERFORMANCE_SCHEMA
    assert ab_data["diagnostic_schema_version"] == DIAGNOSTIC_SCHEMA

    _counterfactualize_inputs(performance, diagnostic)
    abc_data = plot.load_inputs(performance, diagnostic)
    assert abc_data["identity"]["patch_stack"] == COUNTERFACTUAL_PATCH_STACK
    assert abc_data["identity"]["patch_stack_version"] == "A+B+C"
    assert (
        abc_data["performance_schema_version"]
        == COUNTERFACTUAL_PERFORMANCE_SCHEMA
    )
    assert (
        abc_data["diagnostic_schema_version"]
        == COUNTERFACTUAL_DIAGNOSTIC_SCHEMA
    )

    invalid = _performance_document(0)
    invalid["counterfactual_patch_sha256"] = PATCH_C
    invalid["patch_stack"] = [
        PATCH_STACK[0], COUNTERFACTUAL_PATCH_STACK[-1],
    ]
    invalid["patch_stack_sha256"] = _stack_sha(invalid["patch_stack"])
    with pytest.raises(
        plot.FigureDataError, match=r"ordered A\+B or A\+B\+C stack",
    ):
        plot._common_identity(invalid, "invalid")


def test_plot_accepts_exact_cohort1_policy_grid_at_extime_three(
    tmp_path: Path,
):
    performance, diagnostic = _policy_fixture_inputs(tmp_path, cohort2=False)
    data = plot.load_inputs(performance, diagnostic)
    assert data["diagnostic_schema_version"] == COUNTERFACTUAL_DIAGNOSTIC_SCHEMA
    assert data["diagnostic"]["contract"] == "cohort1"
    assert data["diagnostic"]["cell_order"] == list(COHORT1_TRACE_CELLS)
    assert data["identity"]["extime_s"] == 3
    assert len(data["diagnostic"]["runs"]) == 18
    event = data["diagnostic"]["runs"][
        (COHORT1_TRACE_CELLS[2], "write-heavy", 48)
    ]["trace_events"][0]
    assert event["assigned_invert"] == 0
    assert event["recommended_delta_sign"] == -1
    assert "terminal_flush" not in event


def test_plot_accepts_exact_cohort2_grid_and_uses_artifact_cells_in_figure_loop(
    tmp_path: Path,
):
    performance, diagnostic = _policy_fixture_inputs(tmp_path, cohort2=True)
    data = plot.load_inputs(performance, diagnostic)
    assert data["diagnostic_schema_version"] == plot.COHORT2_DIAGNOSTIC_SCHEMA
    assert data["diagnostic"]["contract"] == "cohort2"
    assert data["diagnostic"]["cell_order"] == list(COHORT2_TRACE_CELLS)
    assert data["identity"]["extime_s"] == 6
    assert len(data["diagnostic"]["runs"]) == 18
    values = plot._diagnostic_values(data)
    assert len(values) == 18
    assert {row["cell"] for row in values} == set(COHORT2_TRACE_CELLS)
    run = data["diagnostic"]["runs"][
        (COHORT2_TRACE_CELLS[2], "write-heavy", 48)
    ]
    assert run["step_policy"] == 2
    assert run["trace_summary"] == {
        "updates": 4, "retained": 4, "dropped": 0, "flushes": 1,
    }
    assert run["trace_events"][-1]["trigger"] == "terminal"
    assert run["trace_events"][-1]["assigned_invert"] == -1
    figure, axes = plot.make_diagnostic_figure(data)
    try:
        assert axes.shape == (2, 3)
        assert [tick.get_text() for tick in axes[1, 0].get_xticklabels()] == list(
            COHORT2_TRACE_CELLS
        )
    finally:
        plot.plt.close(figure)


def test_cohort2_plot_accepts_zero_terminal_with_exact_summary(
    tmp_path: Path,
):
    performance, _diagnostic = _policy_fixture_inputs(tmp_path, cohort2=True)
    document = _policy_diagnostic_document(cohort2=True)
    _remove_policy_terminals(document)
    diagnostic = _write(tmp_path / "cohort2-zero-terminal.json", document)
    data = plot.load_inputs(performance, diagnostic)
    run = data["diagnostic"]["runs"][
        (COHORT2_TRACE_CELLS[2], "write-heavy", 48)
    ]
    assert len(run["trace_events"]) == 4
    assert all(event["terminal_flush"] == 0 for event in run["trace_events"])
    assert run["trace_summary"] == {
        "updates": 4,
        "retained": 4,
        "dropped": 0,
        "flushes": 0,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("updates", 3),
        ("retained", 3),
        ("dropped", 1),
        ("flushes", 1),
    ),
)
def test_cohort2_zero_terminal_requires_exact_summary(
    tmp_path: Path,
    field: str,
    value: int,
):
    document = _policy_diagnostic_document(cohort2=True)
    _remove_policy_terminals(document)
    document["trace_runs"][0]["trace_summary"][field] = value
    path = _write(tmp_path / f"bad-zero-terminal-{field}.json", document)
    with pytest.raises(plot.FigureDataError, match="schema v4 count contract"):
        plot._parse_diagnostic(path)


def test_plot_policy_grid_literals_and_field_counts_are_exact() -> None:
    assert plot.COUNTERFACTUAL_DIAGNOSTIC_SCHEMA == (
        "izanagi-dynamic-backoff-trace/v3"
    )
    assert plot.COHORT2_DIAGNOSTIC_SCHEMA == "izanagi-dynamic-backoff-trace/v4"
    assert plot.COHORT1_CELL_LITERALS == (
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    )
    assert plot.COHORT2_CELL_LITERALS == (
        "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0",
        "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1",
        "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2",
    )
    assert all(plot.CELL_FORMAT_FIELDS[cell] == 11 for cell in TRACE_CELLS)
    assert all(
        plot.CELL_FORMAT_FIELDS[cell] == 12
        for cell in (*COHORT1_TRACE_CELLS, *COHORT2_TRACE_CELLS)
    )
    assert [plot.CELL_CONFIGS[cell][5] for cell in COHORT2_TRACE_CELLS] == [
        9223372036854775807,
        9223372036854775807,
        9223372036854775807,
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("middle-terminal", "exactly one terminal event at the end"),
        ("double-terminal", "exactly one terminal event at the end"),
        ("normal-trigger", "trigger must be count"),
        ("missing-terminal-field", "terminal_flush"),
        ("step-policy", "step_policy does not match"),
        ("count-cap", "count_cap_us does not match"),
        ("extime", "extime_s must be exactly 6"),
        ("mixed-cell", "outside the exact 3 x 3 x 2 diagnostic grid"),
    ),
)
def test_cohort2_plot_contract_rejects_near_misses_and_nonfinal_terminal(
    tmp_path: Path,
    mutation: str,
    message: str,
):
    document = _policy_diagnostic_document(cohort2=True)
    row = document["trace_runs"][0]
    if mutation == "middle-terminal":
        terminal = row["trace_events"].pop()
        row["trace_events"].insert(1, terminal)
        for index, event in enumerate(row["trace_events"]):
            event["seq"] = index
            event["tsc"] = 1_000_000 + index * 210_000
    elif mutation == "double-terminal":
        terminal = dict(row["trace_events"][-1])
        terminal["seq"] = len(row["trace_events"])
        terminal["tsc"] += 1
        row["trace_events"].append(terminal)
    elif mutation == "normal-trigger":
        row["trace_events"][0]["trigger"] = "time"
    elif mutation == "missing-terminal-field":
        del row["trace_events"][0]["terminal_flush"]
    elif mutation == "step-policy":
        row["step_policy"] = 1
    elif mutation == "count-cap":
        row["count_cap_us"] -= 1
    elif mutation == "extime":
        document["extime_s"] = 5
    else:
        row["cell"] = COHORT1_TRACE_CELLS[0]
    path = _write(tmp_path / f"bad-{mutation}.json", document)
    with pytest.raises(plot.FigureDataError, match=message):
        plot._parse_diagnostic(path)


def test_plot_propagates_patch_c_hash_when_present(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    _counterfactualize_inputs(performance, diagnostic)
    data = plot.load_inputs(performance, diagnostic)
    staged = tmp_path / "staged-output"
    staged.write_bytes(b"staged")
    provenance = plot.build_provenance(
        data,
        [(staged, tmp_path / "published-output")],
        ["python3", str(SCRIPT)],
    )
    assert provenance["counterfactual_patch_sha256"] == PATCH_C
    assert provenance["patch_stack"] == COUNTERFACTUAL_PATCH_STACK
    assert provenance["patch_stack"][2]["sha256"] == PATCH_C


def test_plot_still_accepts_existing_ab_artifacts(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    result, prefix = _run(tmp_path, "existing-ab", performance, diagnostic)
    assert result.returncode == 0, result.stderr
    assert all(path.is_file() for path in _output_paths(prefix))
    provenance = json.loads(
        Path(f"{prefix}.provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["performance_schema_version"] == PERFORMANCE_SCHEMA
    assert provenance["diagnostic_schema_version"] == DIAGNOSTIC_SCHEMA
    assert provenance["patch_stack"] == PATCH_STACK
    assert "counterfactual_patch_sha256" not in provenance


def test_practical_margin_fixture_controls_verdicts_and_robust_endpoint(
    tmp_path: Path,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    data = plot.load_inputs(performance, diagnostic)
    contrasts = {row["hypothesis"]: row for row in data["contrasts"]}

    positive = next(
        point for point in contrasts["H1"]["points"]
        if (point["workload"], point["threads"]) == ("write-heavy", 48)
    )
    assert positive["mean_percent"] == pytest.approx(4.25, abs=0.01)
    assert 3.2 <= positive["ci95_lower_percent"] <= 3.8
    assert positive["ci95_upper_percent"] > 5.0
    assert positive["verdict"] == "実用優越"
    assert data["hypotheses"]["H1"]["status"] == "accepted"

    other_endpoint = next(
        point for point in contrasts["H1"]["points"]
        if (point["workload"], point["threads"]) == ("balanced", 48)
    )
    assert other_endpoint["ci95_lower_percent"] > 5.0

    negative = next(
        point for point in contrasts["H6"]["points"]
        if (point["workload"], point["threads"]) == ("write-heavy", 6)
    )
    assert negative["mean_percent"] == pytest.approx(-4.25, abs=0.01)
    assert -3.8 <= negative["ci95_upper_percent"] <= -3.2
    assert negative["ci95_lower_percent"] < -5.0
    assert negative["verdict"] == "実用劣化"

    # Second M11a tooth: pin the preregistered literal as well as behavior above.
    assert plot.PRACTICAL_PERCENT == 3.0


def test_large_log_ratio_percentages_use_independent_exponential_transform(
    tmp_path: Path,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    result, prefix = _run(tmp_path, "large-ratio", performance, diagnostic)
    assert result.returncode == 0, result.stderr
    provenance = json.loads(
        Path(f"{prefix}.provenance.json").read_text(encoding="utf-8")
    )
    h2 = next(
        row for row in provenance["contrasts"] if row["hypothesis"] == "H2"
    )
    point = next(
        candidate for candidate in h2["points"]
        if (candidate["workload"], candidate["threads"]) == ("read-heavy", 6)
    )

    # Recompute from the fixture with math.exp, independently of generator helpers.
    log_samples = [math.log(1.60)] * 7
    mean_log = statistics.fmean(log_samples)
    half_width = (
        2.4469118511449692 * statistics.stdev(log_samples) / math.sqrt(7)
    )
    expected = {
        "mean_percent": 100.0 * (math.exp(mean_log) - 1.0),
        "ci95_lower_percent": 100.0 * (math.exp(mean_log - half_width) - 1.0),
        "ci95_upper_percent": 100.0 * (math.exp(mean_log + half_width) - 1.0),
    }
    for key, value in expected.items():
        assert point[key] == pytest.approx(value, abs=1e-12)
        assert value == pytest.approx(60.0, abs=1e-12)


@pytest.mark.parametrize(
    "failure", ("insufficient-files", "duplicate-row", "duplicate-rep", "identity"),
)
def test_missing_duplicate_and_identity_mismatch_are_rejected(
    tmp_path: Path, failure: str,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    if failure == "insufficient-files":
        result, prefix = _run(
            tmp_path, "reject-insufficient-files", performance[:5], diagnostic,
        )
        assert result.returncode != 0
        assert not any(path.exists() for path in _output_paths(prefix))
        return
    changed = json.loads(performance[1].read_text(encoding="utf-8"))
    if failure == "duplicate-row":
        changed["cells"][-1] = changed["cells"][0]
    elif failure == "duplicate-rep":
        changed["rep_index"] = 0
        changed["cell_order"] = list(CELLS)
    else:
        changed["repo_head"] = "4" * 40
    replacement = _write(tmp_path / f"bad-{failure}.json", changed)
    performance[1] = replacement
    result, prefix = _run(tmp_path, f"reject-{failure}", performance, diagnostic)
    assert result.returncode != 0
    assert not any(path.exists() for path in _output_paths(prefix))


def _remove_coordinate(document: dict, coordinate: tuple[str, str, int]) -> None:
    before = len(document["cells"])
    document["cells"] = [
        row for row in document["cells"]
        if (row["cell"], row["workload"], row["threads"]) != coordinate
    ]
    assert len(document["cells"]) == before - 1


def test_six_files_point_missing_and_n_insufficient_follow_preregistration(
    tmp_path: Path,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    six = plot.load_inputs(performance[:-1], diagnostic)
    assert [row["rep_index"] for row in six["performance"]] == list(range(6))
    assert all(point["n"] == 6 for row in six["contrasts"] for point in row["points"])

    coordinate = ("cw-as-dyn", "write-heavy", 6)
    changed = json.loads(performance[0].read_text(encoding="utf-8"))
    _remove_coordinate(changed, coordinate)
    performance[0] = _write(tmp_path / "missing-one.json", changed)
    one_missing = plot.load_inputs(performance, diagnostic)
    h1_point = next(
        point for point in one_missing["contrasts"][0]["points"]
        if (point["workload"], point["threads"]) == ("write-heavy", 6)
    )
    assert h1_point["n"] == 6
    assert h1_point["rep_indices"] == list(range(1, 7))

    changed = json.loads(performance[1].read_text(encoding="utf-8"))
    _remove_coordinate(changed, coordinate)
    performance[1] = _write(tmp_path / "missing-two.json", changed)
    insufficient = plot.load_inputs(performance, diagnostic)
    h1_point = next(
        point for point in insufficient["contrasts"][0]["points"]
        if (point["workload"], point["threads"]) == ("write-heavy", 6)
    )
    assert h1_point["n"] == 5
    assert h1_point["verdict"] == "inconclusive"
    assert h1_point["verdict_reason"] == "n-insufficient"
    assert insufficient["hypotheses"]["H1"]["status"] == "inconclusive"
    assert {
        (row["workload"], row["threads"], row["reason"])
        for row in insufficient["hypotheses"]["H1"]["failed_predicates"]
    } >= {("write-heavy", 6, "n-insufficient")}


def test_hostname_duplicates_are_recorded_not_rejected(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    changed = json.loads(performance[1].read_text(encoding="utf-8"))
    changed["hostname"] = "bnode000"
    performance[1] = _write(tmp_path / "duplicate-host.json", changed)
    data = plot.load_inputs(performance, diagnostic)
    assert data["hostname_duplicates"] == ["bnode000"]


@pytest.mark.parametrize(
    ("failure", "message"),
    (
        ("missing-identity", "driver_sha256"),
        ("dirty-repo", "repo_status_clean must be true"),
        ("diagnostic-rep", "rep_index must be exactly 0"),
    ),
)
def test_execution_identity_and_diagnostic_rep_fail_closed(
    tmp_path: Path, failure: str, message: str,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    if failure == "diagnostic-rep":
        document = json.loads(diagnostic.read_text(encoding="utf-8"))
        document["rep_index"] = 1
        diagnostic = _write(tmp_path / "bad-diagnostic-rep.json", document)
    else:
        document = json.loads(performance[0].read_text(encoding="utf-8"))
        if failure == "missing-identity":
            del document["driver_sha256"]
        else:
            document["repo_status_clean"] = False
        performance[0] = _write(tmp_path / f"bad-{failure}.json", document)
    with pytest.raises(plot.FigureDataError, match=message):
        plot.load_inputs(performance, diagnostic)


def test_diagnostic_fixture_round_trips_producer_schema_and_nullable_rate(
    tmp_path: Path,
):
    performance, _diagnostic = _fixture_inputs(tmp_path)
    diagnostic = _write(
        tmp_path / "zero-scored-diagnostic.json",
        _diagnostic_document(zero_scored=True),
    )
    data = plot.load_inputs(performance, diagnostic)
    run = data["diagnostic"]["runs"][("cw", "write-heavy", 24)]
    assert run["trace_events"][0]["trigger"] == "time"
    assert run["trace_events"][0]["parity_branch"] == "none"
    assert type(run["trace_events"][0]["window_us"]) is int
    assert run["directional_success"] == {
        "scored": 0, "successes": 0, "rate": None,
    }


def test_layout_failure_leaves_no_partial_outputs(tmp_path: Path, monkeypatch):
    performance, diagnostic = _fixture_inputs(tmp_path)
    prefix = tmp_path / "layout-failure"
    original = plot.check_figure_layout
    calls = 0

    def reject_third_layout(figure, axes):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise FigureLayoutError("intentional fixture layout failure")
        original(figure, axes)

    monkeypatch.setattr(plot, "check_figure_layout", reject_third_layout)
    result = plot.main([
        str(prefix), "--trace-json", str(diagnostic), *map(str, performance),
    ])
    assert result != 0
    assert calls == 3
    assert not any(path.exists() for path in _output_paths(prefix))


def test_preregistered_threshold_has_no_cli_override(tmp_path: Path):
    performance, diagnostic = _fixture_inputs(tmp_path)
    result, prefix = _run(
        tmp_path, "threshold", performance, diagnostic,
        extra=["--equivalence-margin", "5"],
    )
    assert result.returncode != 0
    assert "unrecognized arguments" in result.stderr
    assert not any(path.exists() for path in _output_paths(prefix))


def test_dependency_backend_and_decimation_contract_are_explicit():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'mpl.use("Agg", force=True)' in source
    assert source.index('mpl.use("Agg", force=True)') < source.index(
        "import matplotlib.pyplot"
    )
    assert plot.MAX_TRAJECTORY_POINTS == 1024
    assert plot.EVENLY_SPACED_POINTS == 512
    assert plot.EXTREMA_BINS == 256
    for forbidden in ("scipy", "pandas", "seaborn"):
        assert forbidden not in source.lower()
    for path in (SCRIPT, Path(__file__)):
        assert not any(
            "\u0300" <= character <= "\u036f"
            for character in path.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
