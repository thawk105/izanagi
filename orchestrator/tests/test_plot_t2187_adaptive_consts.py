# -*- coding: utf-8 -*-
"""End-to-end tests for the T-2187 adaptive-constant figure generator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "plotting" / "plot_t2187_adaptive_consts.py"
SOURCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v1"
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
GRID_STEPS = (0.1, 0.25, 0.5, 1.0, 5.0, 100.0)
GRID_UPDATES = (10.0, 40.0, 160.0, 640.0, 2560.0)
THREAD_COUNTS = (6, 12, 18, 24, 30, 36, 42, 48)


def _cell(
    workload: str, *, name: str, threads: int, throughput: float,
    abort_rate: float, back_off: int, step_us: float = 100.0,
    update_us: float = 10.0,
) -> dict:
    stock = back_off == 1 and step_us == 100.0 and update_us == 10.0
    return {
        "cell": name,
        "workload": workload,
        "workload_flags": {
            "ycsb_zipf_skew": "0.9",
            "ycsb_rratio": {"write-heavy": "5", "balanced": "50",
                            "read-heavy": "95"}[workload],
            "ycsb_rmw": "0",
            "ycsb_max_ope": "10",
        },
        "threads": threads,
        "back_off": back_off,
        "step_us": step_us,
        "ceiling_us": 1000,
        "update_us": update_us,
        "is_stock_control": stock,
        "genome": "fixture-data-not-an-instruction",
        "binary_sha256": "b" * 64,
        "throughputs": [throughput],
        # Deliberately different: the generator must not use this aggregate.
        "median_tps": throughput + 12345.0,
        "abort_rate": abort_rate,
        "latency_ns": 1000.0,
        "run_cmd": "fixture-data-not-a-command",
        "measured_utc": "2026-09-02T00:00:00Z",
    }


def _document(
    *, mode: str, rep_index: int, throughput: float = 1_000_000.0,
    abort_rate: float = 0.01, env_tag: str = "pegasus-test",
    include_grid_no_backoff: bool = True,
) -> dict:
    stage = 1 if mode == "grid" else 2
    cells = []
    for workload in WORKLOADS:
        if mode == "grid":
            if include_grid_no_backoff:
                cells.append(_cell(
                    workload, name="none", threads=48,
                    throughput=throughput * 0.9, abort_rate=abort_rate * 1.1,
                    back_off=0,
                ))
            for step_us in GRID_STEPS:
                for update_us in GRID_UPDATES:
                    cells.append(_cell(
                        workload,
                        name=(
                            "stock" if step_us == 100.0 and update_us == 10.0
                            else f"s{step_us:g}-u{update_us:g}"
                        ),
                        threads=48,
                        throughput=throughput, abort_rate=abort_rate,
                        back_off=1, step_us=step_us, update_us=update_us,
                    ))
        else:
            for threads in THREAD_COUNTS:
                thread_scale = threads / THREAD_COUNTS[0]
                cells.append(_cell(
                    workload, name="none", threads=threads,
                    throughput=throughput * thread_scale * 0.9,
                    abort_rate=abort_rate * thread_scale * 1.1, back_off=0,
                ))
                cells.append(_cell(
                    workload, name="stock", threads=threads,
                    throughput=throughput * thread_scale,
                    abort_rate=abort_rate * thread_scale, back_off=1,
                ))
    return {
        "schema_version": SOURCE_SCHEMA,
        "kind": "performance-only-probe",
        "not_certified": NOT_CERTIFIED,
        "stage": stage,
        "grid_spec": "fixture",
        "env_tag": env_tag,
        "site": "pegasus",
        "host": f"bnode{rep_index:03d}",
        "pbs_jobid": f"0:{967200 + rep_index}.nqsv",
        "rep_index": rep_index,
        "records": 1_000_000,
        "extime_s": 3,
        "reps_per_job": 1,
        "clocks_per_us": 2100,
        "numactl": ["numactl", "--interleave=all"],
        "use_perf": False,
        "ccbench_commit": "511c953",
        "ccbench_head": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
        "cc": "/usr/bin/gcc",
        "cxx": "/usr/bin/g++",
        "patch_sha256": "a" * 64,
        "stock": {"step_us": 100.0, "ceiling_us": 1000, "update_us": 10},
        "started_utc": "2026-09-02T00:00:00Z",
        "finished_utc": "2026-09-02T00:01:00Z",
        "wall_seconds": 60.0,
        "cpu_seconds": 2700.0,
        "cpu_over_elapsed": 45.0,
        "cells": cells,
    }


def _write(path: Path, document: dict) -> Path:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _run(
    tmp_path: Path, mode: str, prefix_name: str, inputs: list[Path],
) -> tuple[subprocess.CompletedProcess[str], Path]:
    mpl_config = tmp_path / "mpl-config"
    mpl_config.mkdir(exist_ok=True)
    prefix = tmp_path / prefix_name
    environment = dict(os.environ)
    environment["MPLCONFIGDIR"] = str(mpl_config)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), mode, str(prefix), *map(str, inputs)],
        cwd=REPO,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    return result, prefix


def _assert_three_outputs(prefix: Path) -> dict:
    png = Path(f"{prefix}.png")
    pdf = Path(f"{prefix}.pdf")
    provenance_path = Path(f"{prefix}.provenance.json")
    assert png.is_file() and png.stat().st_size > 0
    assert pdf.is_file() and pdf.stat().st_size > 0
    assert provenance_path.is_file() and provenance_path.stat().st_size > 0
    return json.loads(provenance_path.read_text(encoding="utf-8"))


def _load_plot_module():
    spec = importlib.util.spec_from_file_location(
        "plot_t2187_adaptive_consts_test_target", SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grid_compares_stock_coordinate_with_no_backoff_reference(tmp_path: Path):
    inputs = [
        _write(
            tmp_path / f"grid-with-none-rep-{index}.json",
            _document(
                mode="grid", rep_index=index,
                throughput=float(index + 1) * 1_000_000.0,
                abort_rate=float(index + 1) / 100.0,
                include_grid_no_backoff=True,
            ),
        )
        for index in range(3)
    ]
    result, prefix = _run(tmp_path, "grid", "grid-with-none", inputs)
    assert result.returncode == 0, result.stderr
    provenance = _assert_three_outputs(prefix)

    for workload in WORKLOADS:
        workload_rows = [
            row for row in provenance["primary_values"]
            if row["workload"] == workload
        ]
        assert len(workload_rows) == 1 + len(GRID_STEPS) * len(GRID_UPDATES)
        assert {
            (row["step_us"], row["update_us"])
            for row in workload_rows if row["back_off"] == 1
        } == {
            (step_us, update_us)
            for step_us in GRID_STEPS for update_us in GRID_UPDATES
        }
    no_backoff_rows = [
        row for row in provenance["primary_values"]
        if row["cell"] == "none"
    ]
    assert {row["workload"] for row in no_backoff_rows} == set(WORKLOADS)
    assert all(row["back_off"] == 0 for row in no_backoff_rows)
    assert all(
        row["step_us"] == 100.0
        and row["ceiling_us"] == 1000.0
        and row["update_us"] == 10.0
        and row["is_stock_control"] is False
        for row in no_backoff_rows
    )
    assert all(row["n"] == 3 for row in no_backoff_rows)
    assert all(
        row["throughput"]["mean_tps"] == 1_800_000.0
        and row["throughput"]["ci95_half_tps"] is not None
        and math.isclose(
            row["abort_rate"]["mean_fraction"], 0.022,
            rel_tol=0.0, abs_tol=1e-15,
        )
        and row["abort_rate"]["ci95_half_fraction"] is not None
        for row in no_backoff_rows
    )
    assert "no backoff" in provenance["caption"]

    module = _load_plot_module()
    data = module.load_measurements("grid", inputs)
    figure, axes = module.make_figure(data)
    try:
        titles = [axis.get_title() for row in axes for axis in row]
        assert all("no backoff" in title for title in titles)
        assert all("95% CI +/-" in title for title in titles)
        assert sum("no backoff 1.800 M tps" in title for title in titles) == 3
        assert sum("no backoff 2.20%" in title for title in titles) == 3
        cell_annotations = [
            artist.get_text() for artist in figure.findobj()
            if getattr(artist, "get_gid", lambda: None)() == "cell-value"
        ]
        assert len(cell_annotations) == (
            2 * len(WORKLOADS) * len(GRID_STEPS) * len(GRID_UPDATES)
        )
        assert {text.splitlines()[-1] for text in cell_annotations} == {
            "111%", "91%",
        }
    finally:
        module.plt.close(figure)


def test_grid_n7_uses_student_t_and_provenance_hashes_all_inputs(tmp_path: Path):
    inputs = [
        _write(
            tmp_path / f"grid-rep-{index}.json",
            _document(
                mode="grid", rep_index=index,
                throughput=float(index + 1) * 1_000_000.0,
                abort_rate=float(index + 1) / 100.0,
            ),
        )
        for index in range(7)
    ]
    result, prefix = _run(tmp_path, "grid", "grid-n7", inputs)
    assert result.returncode == 0, result.stderr
    provenance = _assert_three_outputs(prefix)

    assert provenance["schema_version"] == SOURCE_SCHEMA
    assert provenance["not_certified"] == NOT_CERTIFIED
    assert len(provenance["inputs"]) == len(inputs)
    expected_hashes = {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in inputs
    }
    assert {
        row["path"]: row["sha256"] for row in provenance["inputs"]
    } == expected_hashes
    assert len(provenance["pbs_jobids"]) == 7

    point = next(
        row for row in provenance["primary_values"]
        if row["workload"] == "write-heavy" and row["cell"] == "stock"
    )
    assert point["n"] == 7
    assert point["throughput"]["samples_tps"] == [
        1_000_000.0, 2_000_000.0, 3_000_000.0, 4_000_000.0,
        5_000_000.0, 6_000_000.0, 7_000_000.0,
    ]
    assert point["throughput"]["mean_tps"] == 4_000_000.0
    # Hand calculation: t_(0.975,6) * s / sqrt(7).
    expected_t_half = 1_997_895.1583699482
    actual_half = point["throughput"]["ci95_half_tps"]
    assert math.isclose(actual_half, expected_t_half, rel_tol=0.0, abs_tol=0.01)
    # Negative lock: the old 1.96 approximation must not match at n=7.
    incorrect_196_half = 1_600_333.2986183427
    assert not math.isclose(
        actual_half, incorrect_196_half, rel_tol=0.0, abs_tol=1.0,
    )

    old_hash = provenance["inputs"][0]["sha256"]
    original = inputs[0].read_text(encoding="utf-8")
    inputs[0].write_text(original + " ", encoding="utf-8")
    changed, changed_prefix = _run(tmp_path, "grid", "grid-hash-changed", inputs)
    assert changed.returncode == 0, changed.stderr
    changed_provenance = _assert_three_outputs(changed_prefix)
    new_hash = changed_provenance["inputs"][0]["sha256"]
    assert new_hash != old_hash
    assert new_hash == hashlib.sha256(inputs[0].read_bytes()).hexdigest()


def test_threads_mode_writes_both_formats_and_marks_n1_ci_unavailable(tmp_path: Path):
    input_path = _write(
        tmp_path / "threads-rep-0.json",
        _document(mode="threads", rep_index=0),
    )
    result, prefix = _run(tmp_path, "threads", "threads", [input_path])
    assert result.returncode == 0, result.stderr
    provenance = _assert_three_outputs(prefix)
    assert provenance["mode"] == "threads"
    assert "n=1" in provenance["caption"]
    assert {row["cell"] for row in provenance["primary_values"]} == {
        "none", "stock",
    }
    assert {
        row["threads"] for row in provenance["primary_values"]
    } == set(THREAD_COUNTS)
    assert all(
        sum(
            row["workload"] == workload and row["cell"] == cell
            for row in provenance["primary_values"]
        ) == len(THREAD_COUNTS)
        for workload in WORKLOADS for cell in ("none", "stock")
    )
    assert all(
        row["throughput"]["ci95_half_tps"] is None
        and row["abort_rate"]["ci95_half_fraction"] is None
        for row in provenance["primary_values"]
    )


def test_schema_version_mismatch_is_rejected(tmp_path: Path):
    document = _document(mode="grid", rep_index=0)
    document["schema_version"] = SOURCE_SCHEMA + "-wrong"
    input_path = _write(tmp_path / "wrong-schema.json", document)
    result, prefix = _run(tmp_path, "grid", "wrong-schema", [input_path])
    assert result.returncode != 0
    assert "schema_version must exactly equal" in result.stderr
    assert not Path(f"{prefix}.provenance.json").exists()


def test_duplicate_cell_workload_threads_rep_index_is_rejected(tmp_path: Path):
    first = _write(
        tmp_path / "duplicate-a.json", _document(mode="grid", rep_index=3),
    )
    second_document = _document(mode="grid", rep_index=3)
    second_document["pbs_jobid"] = "0:999999.nqsv"
    second = _write(tmp_path / "duplicate-b.json", second_document)
    result, prefix = _run(tmp_path, "grid", "duplicate", [first, second])
    assert result.returncode != 0
    assert "duplicate (cell, workload, threads, rep_index)" in result.stderr
    assert not Path(f"{prefix}.png").exists()


def test_layout_check_rejects_an_intentionally_excessive_label(tmp_path: Path):
    input_path = _write(
        tmp_path / "long-label.json",
        _document(
            mode="threads", rep_index=0,
            env_tag="intentionally-too-long-" + "x" * 700,
        ),
    )
    result, prefix = _run(tmp_path, "threads", "long-label", [input_path])
    assert result.returncode != 0
    assert "FigureLayoutError" in result.stderr
    assert "text leaves figure" in result.stderr
    assert not Path(f"{prefix}.png").exists()
    assert not Path(f"{prefix}.pdf").exists()


def test_generator_dependency_backend_and_unicode_constraints_are_explicit():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'mpl.use("Agg", force=True)' in source
    assert source.index('mpl.use("Agg", force=True)') < source.index(
        "import matplotlib.pyplot"
    )
    for forbidden in ("scipy", "pandas", "seaborn"):
        assert forbidden not in source.lower()
    for path in (SCRIPT, Path(__file__)):
        assert not any("\u0300" <= character <= "\u036f"
                       for character in path.read_text(encoding="utf-8"))
