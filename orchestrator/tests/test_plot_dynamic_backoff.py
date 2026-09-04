# -*- coding: utf-8 -*-
"""End-to-end tests for the preregistered dynamic-backoff figure generator."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys

import pytest

from tools.plotting import plot_dynamic_backoff as plot
from tools.plotting.plot_t2187_adaptive_consts import FigureLayoutError


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "plotting" / "plot_dynamic_backoff.py"
PERFORMANCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v2"
DIAGNOSTIC_SCHEMA = "izanagi-dynamic-backoff-trace/v2"
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
THREADS = (6, 12, 18, 24, 30, 36, 42, 48)
CELLS = (
    "none", "stock", "tuned", "tuned-u10240", "cw", "cw-as", "cw-as-dyn",
)
TRACE_CELLS = ("cw", "cw-as", "cw-as-dyn")
PIN = "511c953"
PATCH_A = "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"
PATCH_B = "3" * 64
PATCH_STACK = [
    {"path": "patches/cicada-adaptive-params.patch", "sha256": PATCH_A},
    {"path": "patches/cicada-adaptive-dynamic.patch", "sha256": PATCH_B},
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


def _stack_sha() -> str:
    text = "izanagi-patch-stack/v1\n" + "".join(
        f"{row['path']} {row['sha256']}\n" for row in PATCH_STACK
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identity() -> dict:
    return {
        "repo_head": "1" * 40,
        "prereg_sha256": "2" * 64,
        "ccbench_commit": PIN,
        "patch_sha256": PATCH_A,
        "dynamic_patch_sha256": PATCH_B,
        "patch_stack": PATCH_STACK,
        "patch_stack_sha256": _stack_sha(),
        "records": 1_000_000,
        "extime_s": 3,
        "clocks_per_us": 2100,
    }


def _arm_ratio(cell: str, rep_index: int) -> float:
    # The paired ratios deliberately produce accepted, rejected, and
    # inconclusive preregistered hypotheses in one full-size fixture.
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
    throughput = tuned_tps * _arm_ratio(cell, rep_index)
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
        "pbs_jobid": f"0:{980000 + rep_index}.nqsv",
        "cells": cells,
    }


def _events() -> list[dict]:
    return [
        {
            "seq": seq,
            "tsc": 1_000_000 + 210_000 * seq,
            "window_us": 100,
            "window_commits": 10_000 + 10 * seq,
            "trigger": seq % 3,
            "backoff_before": 100 + seq,
            "backoff_after": 101 + seq,
            "gradient_sign": 1,
            "step_us": 1,
            "ceiling_us": 1000,
            "ceiling_changed": 0,
            "parity_branch": seq % 2,
        }
        for seq in range(64)
    ]


def _diagnostic_document() -> dict:
    events = _events()
    runs = []
    for cell in TRACE_CELLS:
        for workload in WORKLOADS:
            for threads in (24, 48):
                runs.append({
                    "cell": cell,
                    "workload": workload,
                    "threads": threads,
                    "genome": f"fixture:{cell}:{workload}:{threads}",
                    "binary_sha256": hashlib.sha256(cell.encode("utf-8")).hexdigest(),
                    "throughput_diagnostic_only": 1_000_000.0 + 1000 * threads,
                    "events": events,
                    "summary": {"updates": 64, "retained": 64, "dropped": 0},
                    "directional_success": {"scored": 63, "hits": 63, "rate": 1.0},
                })
    assert len(runs) == 18
    return {
        "schema_version": DIAGNOSTIC_SCHEMA,
        "kind": "diagnostic-backoff-trace",
        "headline_eligible": False,
        "hostname": "bnode099",
        **_identity(),
        "pbs_jobid": "0:980099.nqsv",
        "trace_runs": runs,
    }


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
        "patch_sha256", "dynamic_patch_sha256", "patch_stack",
        "patch_stack_sha256", "pbs_jobids", "hostnames",
        "measurement_conditions", "ci95", "performance_values_certified",
        "performance_certification_notice", "performance_aggregates", "contrasts",
        "hypotheses", "diagnostic", "captions", "reproduction",
    }
    assert provenance["provenance_schema_version"] == (
        "izanagi-dynamic-backoff-figure-provenance/v1"
    )
    assert provenance["performance_values_certified"] is False
    assert provenance["performance_certification_notice"] == "性能値は未認証"
    assert len(provenance["performance_aggregates"]) == 168
    assert len(provenance["contrasts"]) == 7
    assert all(len(contrast["points"]) == 24 for contrast in provenance["contrasts"])
    assert {value for value in provenance["hypotheses"].values()} >= {
        "accepted", "rejected", "inconclusive",
    }
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


@pytest.mark.parametrize(
    "failure", ("missing-file", "missing-row", "duplicate-row", "duplicate-rep", "identity"),
)
def test_missing_duplicate_and_identity_mismatch_are_rejected(
    tmp_path: Path, failure: str,
):
    performance, diagnostic = _fixture_inputs(tmp_path)
    if failure == "missing-file":
        result, prefix = _run(
            tmp_path, "reject-missing-file", performance[:-1], diagnostic,
        )
        assert result.returncode != 0
        assert not any(path.exists() for path in _output_paths(prefix))
        return
    changed = json.loads(performance[1].read_text(encoding="utf-8"))
    if failure == "missing-row":
        changed["cells"].pop()
    elif failure == "duplicate-row":
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
