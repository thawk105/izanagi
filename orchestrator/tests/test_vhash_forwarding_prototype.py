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


def _fwd_thread(**changes):
    row = {key: 0 for key in driver.FWD_FIELDS}
    row["thid"] = 1
    row.update(changes)
    return row


def test_counter_schema_rejects_missing_extra_and_non_integer():
    long = {"threads": [{"thid": 1, "long": 1, "commits": 2, "aborts": 0}]}
    for bad in ({key: val for key, val in _fwd_thread(attempts=1).items() if key != "success"},
                {**_fwd_thread(), "surplus": 0}, _fwd_thread(attempts=True),
                _fwd_thread(attempts=-1)):
        text = "CICADA_FWD_V1 " + json.dumps({"threads": [bad]}) + "\n"
        text += "CICADA_LONGTX_V1 " + json.dumps(long) + "\n"
        with pytest.raises(ValueError, match="counter thread schema invalid"):
            driver.parse_counter_lines(text, "count")
    long["threads"][0]["aborts"] = "0"
    with pytest.raises(ValueError, match="counter thread schema invalid"):
        driver.parse_counter_lines("CICADA_FWD_V1 {\"threads\": []}\nCICADA_LONGTX_V1 " +
                                   json.dumps(long), "count")


def test_smoke_requires_c_attempts_and_f_aborts_not_success():
    def record(policy, values):
        return {"workload": "many_ops", "build_kind": "count", "policy": policy,
                "fwd_counters": {"threads": [_fwd_thread(**values)]}}
    c = record("c", {"attempts": 5, "success": 0})
    f = record("f", {"f_aborts": 3})
    assert driver.smoke_count_status([c, f]) == {
        "c_attempts": 5, "c_success": 0, "f_aborts": 3, "accepted": True}
    assert not driver.smoke_count_status([c])["accepted"]
    assert not driver.smoke_count_status([f])["accepted"]


def test_inert_normalization_ignores_markers_and_blank_lines(monkeypatch):
    samples = iter((b"# 1 one\n token\n\nnext\n", b"# 2 two\n token\n \t\nnext\n",
                    b"# 1 one\n token\nnext\n", b"# 2 two\n token\nchanged\n"))
    monkeypatch.setattr(driver, "checked", lambda *a, **k: SimpleNamespace(stdout=next(samples)))
    entry = {"arguments": ["c++", "-c", "one.cc"], "directory": "/tmp"}
    assert driver._preprocess(entry) == driver._preprocess(entry)
    assert driver._preprocess(entry) != driver._preprocess(entry)


def test_aggregate_jobs_excludes_smoke_and_rejects_duplicate_rep():
    def record(rep, policy="c", kind="count"):
        return {"valid": True, "workload": "many_ops", "gc_inter_us": 100, "k": 3,
                "policy": policy, "build_kind": kind, "rep": rep,
                "perf_eligible": False, "throughput": 10,
                "fwd_counters": {"threads": [_fwd_thread(thid=47, attempts=5, success=2,
                                                         no_target=1, f_aborts=3)]},
                "thread_num": 48, "long_threads": 4}
    def job(command, records, job_id="one"):
        return {"command": command, "all_pass": True, "job_id": job_id,
                "hostname": "node", "conditions": {"zipf": .9}, "records": records}
    smoke = job("smoke", [record(0)], "smoke")
    run = job("run", [record(0)], "run")
    cell = driver.aggregate_jobs([smoke, run])["cells"]["many_ops/gc=100/k=3"]
    assert cell["c_summary"]["attempts"] == 5
    assert cell["thread_summary"]["c"]["long"]["attempts"] == 5
    assert cell["thread_summary"]["c"]["normal"]["attempts"] == 0
    assert cell["input_jobs"] == [{"job_id": "run", "hostname": "node", "skew": .9}]
    with pytest.raises(ValueError, match="duplicate record"):
        driver.aggregate_jobs([run, job("run", [record(0)], "other")])


def test_long_completion_zero_denominator_is_missing():
    assert driver._completion({"commits": 0, "aborts": 0}) is None
    assert driver._completion({"commits": 3, "aborts": 1}) == .75


def test_aggregate_cli_requires_explicit_raw_but_no_cache(tmp_path):
    with pytest.raises(SystemExit, match="2"):
        driver.main(["aggregate", "--output", str(tmp_path)])
    raw = tmp_path / "run.json"
    raw.write_text(json.dumps({"command": "run", "all_pass": True, "job_id": "j",
                               "hostname": "n", "conditions": {"zipf": .9}, "records": []}))
    assert driver.main(["aggregate", "--raw", str(raw), "--output", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "aggregate.json").read_text())["cells"] == {}
