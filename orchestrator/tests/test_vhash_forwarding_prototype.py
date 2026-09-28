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


@pytest.mark.parametrize("kind", ("stock", "fwd", "count"))
def test_gate_args_exclude_cicada_defines_but_build_keeps_them(monkeypatch, tmp_path, kind):
    monkeypatch.setattr(driver.compute, "_common_configure_args", lambda **kwargs: [])
    gate_calls, commands = [], []
    def gate(source, macro, args, cxx):
        gate_calls.append((macro, tuple(args)))
        return {"admission": {"admitted": True}}
    def checked(argv, **kwargs):
        commands.append(argv)
    monkeypatch.setattr(driver, "_condition_gate", gate)
    monkeypatch.setattr(driver, "checked", checked)
    build = tmp_path / "build"
    binary = build / "cc/cicada/ycsb_cicada.exe"
    binary.parent.mkdir(parents=True)
    binary.touch()
    driver._build_variant(tmp_path, build, kind, {}, {"cxx_path": "/fake/c++"})
    assert [macro for macro, _ in gate_calls] == list(driver.MACROS[kind])
    assert all("CICADA_" not in arg for _, args in gate_calls for arg in args)
    assert [arg for arg in commands[0] if arg.startswith("-DCMAKE_CXX_FLAGS=")] == [
        "-DCMAKE_CXX_FLAGS=" + " ".join("-D" + macro + "=1" for macro in driver.MACROS[kind])]


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
    long = {"threads": [{"thid": 1, "long": False, "commits": 2, "aborts": 0}]}
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


def test_counter_schema_matches_patch_boolean_long():
    # The patch streams is_long as JSON true/false, and counts as integers.
    for value in (False, True):
        line = ('CICADA_FWD_V1 ' + json.dumps({"threads": [_fwd_thread()]}) + '\n' +
                'CICADA_LONGTX_V1 ' + json.dumps({"schema": 1, "threads": [
                    {"thid": 1, "long": value, "commits": 3, "aborts": 0}]}) + '\n')
        assert driver.parse_counter_lines(line, "count")[1]["threads"][0]["long"] is value
    for bad in ({"long": 0}, {"commits": True}, {"aborts": -1},
                {"commits": "3"}, {"extra": 0}):
        row = {"thid": 1, "long": False, "commits": 3, "aborts": 0, **bad}
        line = ('CICADA_FWD_V1 {"threads": []}\nCICADA_LONGTX_V1 ' +
                json.dumps({"threads": [row]}))
        with pytest.raises(ValueError, match="counter thread schema invalid"):
            driver.parse_counter_lines(line, "count")
    row = {"thid": 1, "long": False, "commits": 3}
    with pytest.raises(ValueError, match="counter thread schema invalid"):
        driver.parse_counter_lines('CICADA_FWD_V1 {"threads": []}\nCICADA_LONGTX_V1 ' +
                                   json.dumps({"threads": [row]}), "count")


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


@pytest.mark.parametrize("marker", ("ycsb_cicada.exe", "ycsb_cicada"))
@pytest.mark.parametrize("surface", ("arguments", "command", "output"))
def test_compile_entry_selects_ycsb_target_among_four(tmp_path, marker, surface):
    source = "/src/cc/cicada/transaction.cc"
    entries = []
    for target in ("ycsb", "tpcc", "bomb", "sbomb"):
        name = marker if target == "ycsb" else f"{target}_cicada.exe"
        object_path = f"CMakeFiles/{name}.dir/transaction.cc.o"
        entry = {"file": source, "directory": str(tmp_path)}
        entry["arguments"] = ["c++", "-c", source]
        if surface == "arguments" or target != "ycsb":
            entry["arguments"] += ["-o", object_path]
        elif surface == "command":
            entry.pop("arguments")
            entry["command"] = f"c++ -c {source} -o {object_path}"
        else:
            entry["output"] = object_path
        entries.append(entry)
    commands = tmp_path / "compile_commands.json"
    commands.write_text(json.dumps(entries))
    assert driver._compile_entry(tmp_path, "transaction.cc") == entries[0]
    commands.write_text(json.dumps(entries[1:]))
    with pytest.raises(RuntimeError, match="found 0"):
        driver._compile_entry(tmp_path, "transaction.cc")
    commands.write_text(json.dumps([*entries, entries[0]]))
    with pytest.raises(RuntimeError, match="found 2"):
        driver._compile_entry(tmp_path, "transaction.cc")

def test_inert_uses_stock_target_commands_without_forwarding_macros(tmp_path, monkeypatch):
    entries = []
    for name in ("transaction.cc", "ycsb_cicada.cc"):
        source = f"/src/cc/cicada/{name}"
        entries.append({"file": source, "directory": str(tmp_path), "arguments":
            ["c++", "-DCICADA_FWD_ENABLE=0", "-DCICADA_FWD_COUNT=0", "-D", "CICADA_LONGTX=1",
             "-DKEEP=1", "-c", source, "-o", f"CMakeFiles/ycsb_cicada.exe.dir/{name}.o"]})
    (tmp_path / "compile_commands.json").write_text(json.dumps(entries)); calls = []
    def fake_checked(argv, **kwargs):
        calls.append(argv); return SimpleNamespace(stdout=b"# marker\n token\n")
    monkeypatch.setattr(driver, "checked", fake_checked); monkeypatch.setattr(driver.patchharness, "applied", lambda *a: nullcontext())
    receipt = driver._inert_receipt(tmp_path, tmp_path)
    assert receipt["matched"] and len(calls) == 4 and calls[:2] == calls[2:]
    assert all("-DKEEP=1" in argv and "CICADA_LONGTX=1" not in argv and not any(
        arg.startswith("-DCICADA_FWD_") for arg in argv) for argv in calls)
    assert all(removed == ["-DCICADA_FWD_ENABLE=0", "-DCICADA_FWD_COUNT=0", "-D", "CICADA_LONGTX=1"]
               for removed in receipt["removed_macro_args"].values())

def test_aggregate_jobs_excludes_smoke_and_rejects_duplicate_rep():
    def record(spec):
        special = spec["gc_inter_us"] == 100 and spec["policy"] == "c" and \
                  spec["build_kind"] == "count" and spec["k"] == 3
        return {**spec, "valid": True, "perf_eligible": spec["build_kind"] != "count",
                "throughput": 10, "longtx_counters": {"threads": []},
                "fwd_counters": {"threads": [_fwd_thread(thid=47,
                    attempts=5 if special else 0, success=2 if special else 0,
                    no_target=1 if special else 0, f_aborts=3 if special else 0)]},
                "thread_num": 48, "long_threads": 4}
    def job(command, records, job_id="one"):
        return {"command": command, "all_pass": True, "job_id": job_id,
                "hostname": "node", "conditions": {"zipf": .9}, "records": records,
                "workload": "many_ops", "k_sweep": False}
    records = [record(spec) for spec in driver.plan_runs("run", "many_ops")]
    smoke = job("smoke", records, "smoke")
    run = job("run", records, "run")
    cell = driver.aggregate_jobs([smoke, run])["cells"]["many_ops/gc=100/k=3"]
    assert cell["c_summary"]["attempts"] == 5
    assert cell["thread_summary"]["c"]["long"]["attempts"] == 5
    assert cell["thread_summary"]["c"]["normal"]["attempts"] == 0
    assert cell["input_jobs"] == [{"job_id": "run", "hostname": "node", "skew": .9}]
    with pytest.raises(ValueError, match="duplicate record"):
        driver.aggregate_jobs([run, job("run", records, "other")])


def test_long_completion_zero_denominator_is_missing():
    assert driver._completion({"commits": 0, "aborts": 0}) is None
    assert driver._completion({"commits": 3, "aborts": 1}) == .75


def test_aggregate_cli_requires_explicit_raw_but_no_cache(tmp_path):
    with pytest.raises(SystemExit, match="2"):
        driver.main(["aggregate", "--output", str(tmp_path)])
    raw = tmp_path / "run.json"
    raw.write_text(json.dumps({"command": "smoke", "all_pass": True, "job_id": "j",
                               "hostname": "n", "conditions": {"zipf": .9}, "records": []}))
    assert driver.main(["aggregate", "--raw", str(raw), "--output", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "aggregate.json").read_text())["cells"] == {}


def _complete_job(workload, *, k_sweep=False):
    records = []
    for spec in driver.plan_runs("run", workload, k_sweep):
        records.append({**spec, "valid": True, "perf_eligible": spec["build_kind"] != "count",
                        "throughput": 10, "thread_num": 48,
                        "long_threads": 0 if workload == "normal" else 4,
                        "longtx_counters": {"threads": [
                            {"thid": 47, "long": workload != "normal", "commits": 3, "aborts": 0}]},
                        "fwd_counters": {"threads": [_fwd_thread()]}})
    return {"command": "run", "all_pass": True, "job_id": workload,
            "hostname": "node", "conditions": {"zipf": .9}, "workload": workload,
            "k_sweep": k_sweep, "records": records}


def test_aggregate_requires_every_planned_cell():
    jobs = [_complete_job(w) for w in driver.WORKLOADS]
    cells = driver.aggregate_jobs(jobs)["cells"]
    assert len(cells) == 9
    for job in jobs:
        for gc in driver.GC_VALUES:
            assert len(cells[f'{job["workload"]}/gc={gc}/k=3']["throughput"]["stock"]) == 3
    missing = _complete_job("normal")
    missing["records"] = [r for r in missing["records"] if not (
        r["gc_inter_us"] == 100 and r["policy"] == "f" and
        r["build_kind"] == "fwd" and r["rep"] == 2)]
    with pytest.raises(ValueError, match=r"missing planned cell: .*'normal', 100, 3, 'f', 'fwd', 2"):
        driver.aggregate_jobs([missing])
    empty = _complete_job("normal")
    empty["records"] = []
    with pytest.raises(ValueError, match="has no records"):
        driver.aggregate_jobs([empty])
    smoke = _complete_job("normal")
    smoke["command"] = "smoke"
    assert driver.aggregate_jobs([smoke])["cells"] == {}


def test_aggregate_k_sweep_requires_extra_cells():
    job = _complete_job("many_ops", k_sweep=True)
    assert len(driver.aggregate_jobs([job])["cells"]) == 5
    job["records"] = [r for r in job["records"] if r["k"] != 8]
    with pytest.raises(ValueError, match=r"missing planned cell: .*100, 8"):
        driver.aggregate_jobs([job])
