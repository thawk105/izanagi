"""Real-size synthetic contract and failure tests for VHash hot-block figures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import copy

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools/plotting/plot_vhash_hot_block.py"

def plot_module():
    spec = importlib.util.spec_from_file_location("vhash_hot_block_plot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def fixture_document():
    plot = plot_module()
    cells = []
    def add(group, k, depth, keyset, value_mode="none", value_bytes=0, state_pattern=None):
        names = plot.WRITE_ARMS if group == "write" else (("linked_scattered", "contig_scalar") if group == "pilot" else plot.READ_ARMS)
        arms = []
        for index, name in enumerate(names):
            reps = [{"rep": rep, "order_pos": (rep + index) % len(names), "elapsed_ns": 800 * (100 + k + rep + index), "ns_per_op": 100 + k + rep + index, "checksum": 42} for rep in range(8)]
            events = {event: {"count": 16000 + index, "run_time_ns": 100000, "running_pct": 100.0} for event in plot.PERF_EVENTS}
            events["cache-references:u"]["count"] = 400
            events["cache-misses:u"]["count"] = 100
            arms.append({"arm": name, "footprint_bytes": (128 if keyset == "in" else 32768) * (32 + index), "footprint_per_key_bytes": 32 + index, "reps": reps, "perf": {"ops": 800, "events": events, "raw_stderr_paths": ["fixture-perf-a.txt", "fixture-perf-b.txt"]}})
        cells.append({"cell_id": f"cell-{len(cells)}", "group": group, "side": "write" if group == "write" else "read", "K": k, "depth": depth, "keyset": keyset, "n_keys": 128 if keyset == "in" else 32768, "capped": False, "value_mode": value_mode, "value_bytes": value_bytes, "state_pattern": state_pattern, "ops": 800, "wall_s": 1.0, "expected_checksum": 42, "shared_value_pool_bytes": (128 if keyset == "in" else 32768) * max(k + 4, (depth or 0) + 2) * value_bytes if value_mode == "external" else 0, "pilot_multiple": None, "arms": arms})
    for k in plot.K_VALUES:
        for depth in (0, k + 2):
            for keyset in plot.KEYSETS: add("k", k, depth, keyset)
    for depth in plot.DEPTH_VALUES:
        for keyset in plot.KEYSETS: add("depth", 8, depth, keyset)
    for k in (3, 8):
        for keyset in plot.KEYSETS:
            for pattern in plot.STATE_PATTERNS: add("state", k, 1, keyset, state_pattern=pattern)
    for k in (3, 8):
        for depth in (0, k - 1):
            for keyset in plot.KEYSETS:
                for value_mode in ("external", "inline"):
                    for size in (16, 64, 256): add("value", k, depth, keyset, value_mode, size)
    for k in plot.K_VALUES:
        for value_mode, size in plot.VALUE_ROWS:
            for keyset in plot.KEYSETS: add("write", k, None, keyset, value_mode, size)
    for multiple in (.5, 1, 2, 4, 8):
        add("pilot", 4, 0, "out")
        cells[-1]["pilot_multiple"] = multiple
    assert {g: sum(c["group"] == g for c in cells) for g in ("k", "depth", "state", "value", "write", "pilot")} == {"k": 24, "depth": 22, "state": 16, "value": 48, "write": 36, "pilot": 5}
    base = {"schema": plot.SCHEMA, "run_id": "fixture-pilot", "shard": "pilot", "host": "fixture-host", "started_utc": "2026-09-29T00:00:00Z", "finished_utc": "2026-09-29T00:01:00Z", "wall_s": 60.0, "source": {"bench_cc_sha256": "a" * 64, "driver_sha256": "b" * 64, "repo_head": "fixture"}, "build": {"compiler_path": "/usr/bin/g++-12", "compiler_version": "g++ 12", "argv": [], "binary_sha256": "c" * 64, "objdump_check": {"scalar_vector_ops": 0, "simd_cmp_ops": 1, "simd_mask_ops": 1, "passed": True}}, "env": {"python": "python3", "python_path": "/usr/bin/python3", "path": "/usr/bin", "cpu_model": "Fixture CPU", "avx2": True, "avx512f": False, "core": 1, "l2_bytes": 1000000, "llc_bytes": 10000000, "mem_available_bytes": 1000000000, "perf_path": "/usr/bin/perf", "perf_candidates_tried": ["/usr/bin/perf"], "perf_event_paranoid": 0, "perf_control_ok": True, "perf_known_work_ratio": 2.0, "single_tenant": {"ok": True, "competitors": []}}, "selfcheck": {"passed": True, "vectors": ["fixture"], "random_cases": 100}, "keyset_multiple": 2, "pilot_ref": None, "cells": []}
    shards = []
    for shard, groups in (("pilot", ("pilot",)), ("read-k", ("k",)), ("read-depth-state", ("depth", "state")), ("read-value", ("value",)), ("write", ("write",))):
        doc = copy.deepcopy(base)
        doc["shard"] = shard
        doc["run_id"] = "fixture-" + shard
        doc["pilot_ref"] = None if shard == "pilot" else "fixture-pilot"
        doc["cells"] = [cell for cell in cells if cell["group"] in groups]
        shards.append(doc)
    return shards

def write(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path

def invoke(tmp_path, doc, mode="k", second=None):
    docs = doc if isinstance(doc, list) else [doc]
    paths = [write(tmp_path / f"raw-{i}.json", item) for i, item in enumerate(docs)]
    if second is not None: paths.append(write(tmp_path / "second.json", second))
    prefix = tmp_path / "figure"
    env = dict(os.environ, MPLCONFIGDIR=str(tmp_path / "mpl"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, str(SCRIPT), mode, str(prefix), *map(str, paths)], cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    return result, prefix, paths[0]

def assert_empty(prefix):
    assert not any(Path(f"{prefix}.{suffix}").exists() for suffix in ("png", "pdf", "provenance.json", "summary.json"))

def reject(tmp_path, modify, reason, second=None):
    doc = fixture_document()
    modify(doc[1])
    result, prefix, _ = invoke(tmp_path, doc, second=second)
    assert result.returncode != 0
    assert reason in result.stderr, result.stderr
    assert_empty(prefix)

def test_modes_real_size_and_summary(tmp_path):
    doc = fixture_document()
    for mode in ("k", "depth", "write"):
        folder = tmp_path / mode
        folder.mkdir()
        result, prefix, _ = invoke(folder, doc, mode)
        assert result.returncode == 0, result.stderr
        for suffix in ("png", "pdf", "provenance.json", "summary.json"):
            assert Path(f"{prefix}.{suffix}").stat().st_size > 0
        provenance = json.loads(Path(f"{prefix}.provenance.json").read_text())
        summary = json.loads(Path(f"{prefix}.summary.json").read_text())
        assert len(summary["cells"]) == 151
        assert {c["group"] for c in summary["cells"]} == {"k", "depth", "state", "value", "write", "pilot"}
        assert len(provenance["points"]) == {"k": 96, "depth": 88, "write": 144}[mode]
        assert summary["cells"][0]["arms"][0]["perf_per_op"]["cycles:u"] == 20
        assert summary["cells"][0]["arms"][0]["cache_miss_rate"] == .25
        assert summary["cells"][0]["arms"][0]["perf_events"]["cycles:u"] == {"run_time_ns": 100000, "running_pct": 100.0}

def test_real_figure_passes_layout(tmp_path):
    plot = plot_module()
    sources = [write(tmp_path / f"raw-{i}.json", doc) for i, doc in enumerate(fixture_document())]
    cells, _, env = plot.load_raw(sources)
    summary = plot.summarise(cells)
    for mode in ("k", "depth", "write"):
        fig, axes, _, _ = plot.make_figure(mode, summary, env[0], env[1])
        try: plot.check_figure_layout(fig, axes)
        finally: plot.plt.close(fig)

def test_schema_rejected(tmp_path): reject(tmp_path, lambda d: d.update(schema="wrong"), "schema mismatch")
def test_duplicate_cell_id_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][1].update(cell_id=d["cells"][0]["cell_id"]), "duplicate cell_id")
def test_missing_arm_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"].pop(), "missing or duplicate arm")
def test_missing_rep_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["reps"].pop(), "missing or duplicate rep")
def test_nonfinite_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["reps"][0].update(ns_per_op=float("nan")), "non-finite")
def test_selfcheck_rejected(tmp_path): reject(tmp_path, lambda d: d["selfcheck"].update(passed=False), "selfcheck.passed")
def test_objdump_rejected(tmp_path): reject(tmp_path, lambda d: d["build"]["objdump_check"].update(passed=False), "build.objdump_check.passed")
@pytest.mark.parametrize("section,key", (("env", "cpu_model"), ("build", "compiler_version"), ("build", "binary_sha256")))
def test_environment_mismatch_rejected(tmp_path, section, key):
    second = fixture_document()[3]
    second[section][key] = "different"
    reject(tmp_path, lambda d: None, "environment mismatch", second)

def test_missing_grid_cell_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"].pop(0), "missing grid cell")
def test_long_label_layout_rejected_without_outputs(tmp_path):
    doc = fixture_document()
    for shard in doc: shard["env"]["cpu_model"] = "extremely-long-cpu-model-" * 100
    result, prefix, _ = invoke(tmp_path, doc)
    assert result.returncode != 0
    assert "text leaves figure" in result.stderr or "text bbox overlap" in result.stderr
    assert_empty(prefix)

def test_provenance_input_sha256_matches_file(tmp_path):
    result, prefix, source = invoke(tmp_path, fixture_document())
    assert result.returncode == 0, result.stderr
    provenance = json.loads(Path(f"{prefix}.provenance.json").read_text())
    assert provenance["inputs"][0]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    for suffix in ("png", "pdf"):
        assert provenance["outputs"][suffix]["sha256"] == hashlib.sha256(Path(f"{prefix}.{suffix}").read_bytes()).hexdigest()

def test_failure_key_rejected(tmp_path): reject(tmp_path, lambda d: d.update(failure="fixture failure"), "failed raw")
def test_v1_schema_rejected(tmp_path):
    doc = fixture_document()[1]
    doc["schema"] = "izanagi-vhash-hot-block-microbench/v1"
    result, prefix, _ = invoke(tmp_path, doc)
    assert result.returncode != 0 and "schema mismatch" in result.stderr
    assert_empty(prefix)
def test_missing_perf_event_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["perf"]["events"].pop("branch-misses:u"), "missing or unexpected perf event")
def test_low_running_pct_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["perf"]["events"]["cycles:u"].update(running_pct=99.4), "running_pct")
def test_pilot_ref_disagrees_between_shards(tmp_path):
    docs = fixture_document()[1:]
    docs[0]["pilot_ref"] = "other-pilot"
    result, prefix, _ = invoke(tmp_path, docs)
    assert result.returncode != 0 and "pilot_ref mismatch" in result.stderr
    assert_empty(prefix)
def test_pilot_raw_run_id_mismatch(tmp_path):
    docs = fixture_document()
    docs[0]["run_id"] = "other-pilot"
    result, prefix, _ = invoke(tmp_path, docs)
    assert result.returncode != 0 and "pilot_ref mismatch" in result.stderr
    assert_empty(prefix)
def test_checksum_mismatch_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["reps"][0].update(checksum=43), "checksum mismatch")
def test_paranoid_string_rejected(tmp_path): reject(tmp_path, lambda d: d["env"].update(perf_event_paranoid="0"), "perf_event_paranoid")
def test_perf_ops_mismatch_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["perf"].update(ops=801), "perf.ops mismatch")
def test_ns_per_op_mismatch_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0]["reps"][0].update(ns_per_op=999), "ns_per_op mismatch")
def test_bench_round_trip_ns_per_op_accepted(tmp_path):
    compiler = shutil.which("g++-12")
    assert compiler, "g++-12 required for producer format check"
    source = tmp_path / "print_cell.cc"
    source.write_text(
        '#define main benchmark_main\n'
        f'#include "{REPO / "tools/vhash_microbench/hot_block_bench.cc"}"\n'
        '#undef main\n'
        'int main() {\n'
        '  std::vector<ArmData> arms{{"contig_scalar", 32, {{100000001, 42, 0}}}};\n'
        '  print_cell(1000000, 42, 1, 0, arms);\n'
        '}\n', encoding="utf-8")
    binary = tmp_path / "print_cell"
    build = subprocess.run([compiler, *(
        "-O3 -DNDEBUG -std=c++20 -Wall -Wextra -Werror -fno-tree-vectorize "
        "-mavx2 -mbmi -mbmi2 -mpopcnt").split(), str(source), "-o", str(binary)],
        capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    run = subprocess.run([str(binary)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    rep = json.loads(run.stdout)["arms"][0]["reps"][0]
    cell = fixture_document()[0]["cells"][0]
    cell["ops"] = 1000000
    for arm in cell["arms"]:
        arm["perf"]["ops"] = cell["ops"]
        arm["reps"] = [dict(rep, rep=index) for index in range(8)]
    plot_module().validate_cell(cell)
def test_footprint_product_mismatch_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0]["arms"][0].update(footprint_bytes=1), "footprint mismatch")
def test_shared_value_pool_type_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0].update(shared_value_pool_bytes=-1), "shared_value_pool_bytes")
def test_shared_value_pool_bool_rejected(tmp_path): reject(tmp_path, lambda d: d["cells"][0].update(shared_value_pool_bytes=True), "shared_value_pool_bytes")

def test_output_replace_failure_removes_this_runs_products(tmp_path, monkeypatch):
    plot = plot_module()
    sources = [write(tmp_path / f"raw-{i}.json", doc) for i, doc in enumerate(fixture_document())]
    prefix = tmp_path / "figure"
    actual_replace = os.replace
    calls = []
    def fail_second(source, target):
        calls.append(target)
        if len(calls) == 2: raise OSError("injected replace failure")
        actual_replace(source, target)
    monkeypatch.setattr(os, "replace", fail_second)
    with pytest.raises(OSError, match="injected replace failure"):
        plot.run("k", prefix, sources)
    assert_empty(prefix)

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
