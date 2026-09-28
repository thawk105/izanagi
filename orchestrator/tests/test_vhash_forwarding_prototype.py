"""Login-only contract tests for Cicada forwarding diagnostics."""
from __future__ import annotations

from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import vhash_forwarding_prototype as driver

FIGURE_PATH = (Path(__file__).resolve().parents[2] /
    "output/insights/2026-09-29/vhash-forwarding-prototype/make_figures.py")
_spec = importlib.util.spec_from_file_location("vhash_figures", FIGURE_PATH)
figures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(figures)


def test_order_rotation():
    plan = driver.plan_runs("run", "many_ops")
    for rep, expected in enumerate((("stock", "c", "f"), ("c", "f", "stock"),
                                    ("f", "stock", "c"))):
        actual = tuple(r["policy"] for r in plan if r["gc_inter_us"] == 100 and
                       r["k"] == 3 and r["rep"] == rep and r["build_kind"] != "count")
        assert actual == expected
        assert tuple(r["order_index"] for r in plan if r["gc_inter_us"] == 100 and
                     r["k"] == 3 and r["rep"] == rep and r["build_kind"] != "count") == (0, 1, 2)


def test_count_throughput_is_ineligible(monkeypatch, tmp_path):
    binary = tmp_path / "ycsb_cicada.exe"
    binary.write_bytes(b"fake")
    monkeypatch.setattr(driver, "_probe", lambda: {"competing": []})
    out = b'throughput[tps]:\t99\nCICADA_FWD_V1 {"threads": []}\nCICADA_LONGTX_V1 {"threads": []}\n'
    monkeypatch.setattr(driver.subprocess, "run", lambda *a, **k:
                        SimpleNamespace(returncode=0, stdout=out, stderr=b""))
    spec = next(r for r in driver.plan_runs("smoke", "normal") if r["build_kind"] == "count")
    record = driver._run_binary(binary, spec, {}, [])
    assert record["valid"]
    assert record["throughput"] == 99
    assert record["perf_eligible"] is False
    cell = driver.aggregate({"records": [record]})["cells"]["normal/gc=100/k=3"]
    assert cell["throughput"] == {"stock": [], "c": [], "f": []}


def test_counter_line_exactly_once():
    one = 'CICADA_FWD_V1 {"threads": []}\nCICADA_LONGTX_V1 {"threads": []}\n'
    assert driver.parse_counter_lines(one, "count")[0] == {"threads": []}
    with pytest.raises(ValueError, match="expected 1 lines, found 2"):
        driver.parse_counter_lines(one + 'CICADA_FWD_V1 {"threads": []}\n', "count")
    with pytest.raises(ValueError, match="expected 1 lines, found 0"):
        driver.parse_counter_lines('CICADA_LONGTX_V1 {"threads": []}\n', "count")


def test_gate_rejection_stops_build(monkeypatch, tmp_path):
    class Receipt:
        def __init__(self, admitted):
            self.admitted = admitted
        def canonical_json(self):
            return json.dumps({"admitted": self.admitted})
    monkeypatch.setattr(driver.condition, "capture_define_inputs", lambda *a, **k: object())
    monkeypatch.setattr(driver.condition, "make_define_request", lambda **k: object())
    monkeypatch.setattr(driver.condition, "_configured_define_compile_commands",
                        lambda *a, **k: nullcontext(object()))
    monkeypatch.setattr(driver.condition, "evaluate_define_supply_effectuation",
                        lambda *a, **k: Receipt(True))
    monkeypatch.setattr(driver.condition, "evaluate_define_runtime_meaning",
                        lambda *a, **k: Receipt(True))
    monkeypatch.setattr(driver.condition, "declare_define_runtime_meaning", lambda *a: object())
    monkeypatch.setattr(driver.condition, "require_condition_gate_family",
                        lambda *a, **k: Receipt(False))
    spawned = []
    monkeypatch.setattr(driver, "checked", lambda *a, **k: spawned.append(a))
    with pytest.raises(RuntimeError, match="condition gate rejected"):
        driver._build_variant(tmp_path, tmp_path / "build", "stock",
                              {name: tmp_path for name in ("gflags", "glog", "masstree",
                                                           "mimalloc", "googletest")},
                              {"cxx_path": "/fake/c++", "cc_path": "/fake/cc"})
    assert spawned == []


def test_figure_full_shape():
    import matplotlib
    matplotlib.use("Agg")
    cells = {}
    for workload in figures.WORKLOADS:
        for gc in figures.GC_VALUES:
            key = f"{workload}/gc={gc}/k=3"
            cells[key] = {"c_counters": [{"attempts": 100, "success": 40,
                                          **{r: 10 for r in figures.FAILURES}}],
                          "f_counters": [{"f_aborts": 20}],
                          "throughput": {arm: [{"rep": n, "value": 100 + n +
                                        {"stock": 0, "c": 5, "f": -5}[arm]}
                                        for n in range(3)] for arm in ("stock", "c", "f")},
                          "longtx": {arm: [{"commits": 20, "aborts": 2}]
                                     for arm in ("stock", "c", "f")}}
    fig, axes, major = figures.make_figure({"cells": cells})
    try:
        assert len(axes) == len(figures.WORKLOADS) * 4
        assert len(major) == len(figures.WORKLOADS)
        figures.check_figure_layout(fig, axes)
    finally:
        import matplotlib.pyplot as plt
        plt.close(fig)
