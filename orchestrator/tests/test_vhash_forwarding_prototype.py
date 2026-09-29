"""Login-only contract tests for Cicada forwarding diagnostics."""
from __future__ import annotations

from contextlib import nullcontext
import copy
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


def test_dependency_build_is_ungated_and_has_no_cicada_define(monkeypatch, tmp_path):
    monkeypatch.setattr(driver.compute, "_common_configure_args", lambda **kwargs: [])
    monkeypatch.setattr(driver, "_condition_gate", lambda *args: pytest.fail("dependency entered gate"))
    commands = []
    monkeypatch.setattr(driver, "checked", lambda argv, **kwargs: commands.append(argv))
    (tmp_path / "cc/cicada").mkdir(parents=True); (tmp_path / "cc/cicada/ycsb_cicada.exe").touch()
    assert driver._build_variant(tmp_path, tmp_path, "dependency", {}, {"cxx_path": "/fake/c++"})[1] == []
    assert len(commands) == 2 and not any("CICADA_" in arg for argv in commands for arg in argv)
@pytest.mark.parametrize("fail_dependency", (False, True))
def test_dependency_build_precedes_gate_and_failure_stops(monkeypatch, tmp_path, fail_dependency):
    monkeypatch.setattr(driver, "checked", lambda *a, **k: SimpleNamespace(stdout=b"head\n"))
    monkeypatch.setattr(driver, "_probe", lambda: {})
    for name in ("_load_policy", "_resolve_toolchain", "_prepare_dependencies"):
        monkeypatch.setattr(driver.compute, name, lambda *a: {})
    monkeypatch.setattr(driver.patchharness, "checkout", lambda *a: nullcontext(tmp_path)); monkeypatch.setattr(driver.patchharness, "applied", lambda *a: nullcontext())
    calls = []
    def build(source, directory, kind, dependencies, toolchain):
        calls.append(kind)
        if kind != "dependency" or fail_dependency:
            raise RuntimeError("stop")
        return driver.PATCH, [], 1.25
    monkeypatch.setattr(driver, "_build_variant", build)
    assert driver.main(["smoke", "--third-party-cache", str(tmp_path), "--output", str(tmp_path)]) == 1
    assert calls == (["dependency"] if fail_dependency else ["dependency", "stock"])
    job = json.loads(next(tmp_path.glob("raw-smoke-*.json")).read_text())
    assert ("dependency" in job["builds"]) is not fail_dependency and (fail_dependency or job["builds"]["dependency"]["seconds"] == 1.25)

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


def _gc_payload():
    return {"schema": 1, "mode": "e", "sample_us": 10, "clocks_per_us": 2100,
        "initial_versions": 100, "version_struct_bytes": 64,
        "threads": [{key: (i if key == "thid" else 0) for key in driver.GC_THREAD}
                    for i in (0, 1)],
        "uniform": {"count": 1, "negative": 0, "lag_rts_hist": [1]+[0]*41,
                    "lag_rts_sum_us": 1, "lag_rts_max_us": 1,
                    "lag_wts_hist": [1]+[0]*41, "live_sum": 100, "live_max": 100,
                    "argmin_rts_thid": [0, 1], "series": [], "series_stride": 1,
                    "max_gap_intervals": 1},
        "publish": {"count": 0, "lag_rts_hist": [0]*42, "interval_hist": [0]*42},
        "begin": {"count": 0, "lag_rts_hist": [0]*42},
        "retention": {"count": 0, "sum_us": 0, "hist": [0]*42}, "live_end": 100}


def test_gc_rotation_md4():
    assert [driver.gc_order_rotation(rep) for rep in range(4)] == [
        ("stock", "C", "E-hb", "E"), ("C", "E-hb", "E", "stock"),
        ("E-hb", "E", "stock", "C"), ("E", "stock", "C", "E-hb")]


def test_gc_line_exactly_once_and_schema_md2_md3():
    payload = _gc_payload()
    line = "CICADA_GC_V1 " + json.dumps(payload) + "\n"
    assert driver.parse_gc_line(line, True) == payload
    with pytest.raises(ValueError, match="expected 1 lines, found 2"):
        driver.parse_gc_line(line * 2, True)
    with pytest.raises(ValueError, match="expected 1 lines, found 0"):
        driver.parse_gc_line("", True)
    payload["unknown"] = 0
    with pytest.raises(ValueError, match="top schema"):
        driver.parse_gc_line("CICADA_GC_V1 " + json.dumps(payload), True)
    del payload["unknown"]
    payload["uniform"]["series"] = [[i, i, 100] for i in range(10000)]
    assert driver.parse_gc_line("CICADA_GC_V1 " + json.dumps(payload), True)["uniform"]["series"][-1][0] == 9999
    del payload["uniform"]["max_gap_intervals"]
    with pytest.raises(ValueError, match="uniform schema"):
        driver.parse_gc_line("CICADA_GC_V1 " + json.dumps(payload), True)


def test_gc_argv_and_count_perf_md1(tmp_path):
    specs = driver.gc_plan_runs("wait_after_reads", 10000)
    for arm in driver.GC_ARMS:
        spec = next(s for s in specs if s["arm"] == arm and s["build_kind"].endswith("-count"))
        argv = driver._argv(tmp_path / "binary", spec)
        assert "--cicada_gc_sample_us=10" in argv
        assert "--cicada_long_wait_us=10000" in argv
        assert ("--cicada_gc_slice_us=100" in argv) is arm.startswith("E")
        assert ("--cicada_gc_mode=hb" in argv) is (arm == "E-hb")
        assert ("--cicada_gc_mode=e" in argv) is (arm == "E")
        assert argv[0] != "numactl"
    assert len(specs) == 72


def _gc_job(workload="normal", wait_us=None):
    records = []
    for spec in driver.gc_plan_runs(workload, wait_us):
        records.append({**spec, "valid": True,
            "perf_eligible": not spec["build_kind"].endswith("-count"),
            "throughput": 100, "gc_counters": _gc_payload() if spec["build_kind"].endswith("-count") else None,
            "longtx_counters": {"threads": [{"thid": 1, "long": False}]}})
    return {"command": "gc-run", "all_pass": True, "workload": workload, "wait_us": wait_us,
            "records": records}


def _gc_jobs():
    return [_gc_job("wait_after_reads", 1000), _gc_job("wait_after_reads", 10000),
            _gc_job("normal"), _gc_job("many_ops")]


def test_gc_aggregate_complete_and_missing_md1_md5():
    jobs = _gc_jobs()
    aggregate = driver.gc_aggregate_jobs(jobs)
    cell = aggregate["cells"]["normal/wait=None/gc=10"]
    assert len(cell["arms"]["E"]["performance"]) == 3
    assert len(cell["arms"]["E"]["gc"]) == 1
    assert cell["arms"]["E"]["throughput_median_tps"] == 100
    jobs[2]["records"].pop()
    with pytest.raises(ValueError, match="missing or extra cell"):
        driver.gc_aggregate_jobs(jobs)
    jobs = _gc_jobs()
    next(r for r in jobs[2]["records"] if r["build_kind"].endswith("-count"))["perf_eligible"] = True
    with pytest.raises(ValueError, match="mislabeled"):
        driver.gc_aggregate_jobs(jobs)
    with pytest.raises(ValueError, match="missing GC jobs"):
        driver.gc_aggregate_jobs(_gc_jobs()[:-1])
    extra = _gc_job("normal")
    extra["wait_us"] = 1000
    with pytest.raises(ValueError, match="unexpected GC job"):
        driver.gc_aggregate_jobs([*_gc_jobs(), extra])


def test_md6_plan_and_argv_remain_unchanged():
    assert driver.order_rotation(0) == ("stock", "c", "f")
    assert len(driver.plan_runs("run", "normal")) == 33
    spec = driver.plan_runs("run", "normal")[0]
    assert driver._argv(Path("binary"), spec)[0:3] == ["numactl", "--interleave=all", "binary"]


@pytest.mark.parametrize("kind", ("gc-stock", "gc-c", "gc-e", "gc-stock-count", "gc-c-count", "gc-e-count"))
def test_gc_build_gates_every_macro_and_uses_tuned_genome(monkeypatch, tmp_path, kind):
    monkeypatch.setattr(driver.compute, "_common_configure_args", lambda **kwargs: [])
    seen, commands = [], []
    monkeypatch.setattr(driver, "_condition_gate", lambda source, macro, args, cxx:
                        seen.append((macro, tuple(args))) or {"admission": {"admitted": True}})
    monkeypatch.setattr(driver, "checked", lambda argv, **kwargs: commands.append(argv))
    binary = tmp_path / "cc/cicada/ycsb_cicada.exe"
    binary.parent.mkdir(parents=True)
    binary.touch()
    driver._build_variant(tmp_path, tmp_path, kind, {}, {"cxx_path": "/fake/c++"})
    assert [macro for macro, _ in seen] == list(driver.MACROS[kind])
    for key, value in driver.GC_GENOME.items():
        from orchestrator.campaign.model import cmake_cache_variable_for_axis
        arg = f"-D{cmake_cache_variable_for_axis('cicada', key)}={value}"
        assert arg in commands[0]
        assert all(arg in args for _, args in seen)


def test_gc_count_build_and_run_parse_fwd(monkeypatch, tmp_path):
    assert "CICADA_FWD_COUNT" not in driver.MACROS["gc-stock-count"]
    assert "CICADA_FWD_COUNT" in driver.MACROS["gc-c-count"]
    assert "CICADA_FWD_COUNT" in driver.MACROS["gc-e-count"]
    binary = tmp_path / "ycsb_cicada.exe"
    binary.write_bytes(b"fixture")
    monkeypatch.setattr(driver, "_probe", lambda: {})
    payload = json.dumps(_gc_payload())
    stdout = ("throughput[tps]:\t99\nCICADA_GC_V1 " + payload +
              '\nCICADA_FWD_V1 {"threads": []}\nCICADA_LONGTX_V1 {"threads": []}\n').encode()
    monkeypatch.setattr(driver.subprocess, "run", lambda *a, **k:
                        SimpleNamespace(returncode=0, stdout=stdout, stderr=b""))
    spec = next(s for s in driver.gc_plan_runs("wait_after_reads", 10000, smoke=True)
                if s["build_kind"] == "gc-e-count")
    record = driver._run_binary(binary, spec, {}, [])
    assert record["valid"] and record["fwd_counters"] == {"threads": []}
    assert record["perf_eligible"] is False


def test_gc_summary_retains_diagnostics_and_rep_differences():
    jobs = _gc_jobs()
    for job in jobs[:2]:
        for record in job["records"]:
            if not record["build_kind"].endswith("-count"):
                continue
            payload = copy.deepcopy(record["gc_counters"])
            arm_offset = {"stock": 0, "C": 1, "E-hb": 2, "E": 4}[record["arm"]]
            if record["arm"] == "E" and record["rep"] == 2:
                arm_offset += 9  # median differs from mean across paired reps
            payload["uniform"].update(lag_rts_sum_us=arm_offset + record["rep"] + 1,
                live_sum=100 + arm_offset + record["rep"],
                lag_wts_hist=[0, 1] + [0]*40,
                series=[[record["rep"], arm_offset, 100]], max_gap_intervals=3)
            payload["publish"].update(count=1, lag_rts_hist=[0, 1] + [0]*40)
            payload["begin"].update(count=1, lag_rts_hist=[0, 1] + [0]*40)
            payload["retention"].update(count=1, sum_us=8, hist=[0, 0, 0, 1] + [0]*38)
            record["gc_counters"] = payload
    cell = driver.gc_aggregate_jobs(jobs)["cells"]["wait_after_reads/wait=1000/gc=10"]
    e = cell["arms"]["E"]["gc"][0]
    assert e["lag_wts_p50_upper_us"] == 2
    assert e["publish_count"] == e["begin_count"] == e["retention_count"] == 1
    assert e["publish_lag_rts_p50_upper_us"] == e["begin_lag_rts_p50_upper_us"] == 2
    assert e["retention_sum_us"] == e["retention_p50_upper_us"] == 8
    assert e["series"] == [[0, 4, 100]] and e["max_gap_intervals"] == 3
    comparisons = cell["gc_comparisons"]
    assert comparisons["primary_E_minus_E-hb"]["lag_rts_mean_us"] == 2
    assert comparisons["auxiliary_E-hb_minus_stock"]["live_mean"] == 2
    assert comparisons["auxiliary_E-hb_minus_C"]["live_mean"] == 1
    assert comparisons["primary_E_minus_E-hb"]["retention_p50_upper_us"] == 0


def _gc_main_fixture(monkeypatch, tmp_path, *, gate_failure=False, success=0):
    monkeypatch.setattr(driver, "checked", lambda *a, **k: SimpleNamespace(stdout=b"head\n"))
    monkeypatch.setattr(driver, "_probe", lambda: {})
    for name in ("_load_policy", "_resolve_toolchain", "_prepare_dependencies"):
        monkeypatch.setattr(driver.compute, name, lambda *a, **k: {})
    monkeypatch.setattr(driver.patchharness, "checkout", lambda *a: nullcontext(tmp_path))
    monkeypatch.setattr(driver.patchharness, "applied", lambda *a: nullcontext())
    monkeypatch.setattr(driver.patchharness, "patch_files", lambda *a: ["cc/cicada/transaction.cc"])
    monkeypatch.setattr(driver.patchharness, "apply_patch", lambda *a: None)
    monkeypatch.setattr(driver, "_gc_inert_receipt", lambda *a: {"matched": True})
    calls = []
    def build(source, directory, kind, dependencies, toolchain):
        calls.append(kind)
        if gate_failure and kind == "gc-stock":
            exc = RuntimeError("condition gate rejected CICADA_LONGTX")
            exc.condition_gate_evidence = {"macro": "CICADA_LONGTX",
                "supply": {"admitted": True}, "meaning": {"admitted": False},
                "admission": {"admitted": False}}
            raise exc
        return driver.PATCH, [], 1.0
    monkeypatch.setattr(driver, "_build_variant", build)
    def run(binary, spec, common, gates):
        payload = _gc_payload() if spec["build_kind"].endswith("-count") else None
        if payload and spec["arm"] == "E":
            payload["threads"][0]["success"] = success
        return {**spec, "valid": True, "gc_counters": payload}
    monkeypatch.setattr(driver, "_run_binary", run)
    return calls


def test_gc_smoke_requires_e_success_and_dependency_first(monkeypatch, tmp_path):
    calls = _gc_main_fixture(monkeypatch, tmp_path)
    argv = ["gc-smoke", "--third-party-cache", str(tmp_path), "--output", str(tmp_path)]
    assert driver.main(argv) == 1
    job = json.loads(next(tmp_path.glob("raw-gc-smoke-*.json")).read_text())
    assert calls[:2] == ["gc-dependency", "gc-stock"]
    assert job["e_success_total"] == 0 and "success total is zero" in job["error"]
    assert job["all_pass"] is False
    calls = _gc_main_fixture(monkeypatch, tmp_path, success=1)
    assert driver.main(argv) == 0
    assert calls[:2] == ["gc-dependency", "gc-stock"]


def test_gc_gate_rejection_evidence_is_saved(monkeypatch, tmp_path):
    calls = _gc_main_fixture(monkeypatch, tmp_path, gate_failure=True)
    assert driver.main(["gc-run", "--workload", "normal", "--third-party-cache",
                        str(tmp_path), "--output", str(tmp_path)]) == 1
    job = json.loads(next(tmp_path.glob("raw-gc-run-*.json")).read_text())
    assert calls == ["gc-dependency", "gc-stock"]
    assert job["condition_gate_evidence"]["meaning"]["admitted"] is False
    assert job["condition_gate_evidence"]["admission"]["admitted"] is False


@pytest.mark.parametrize("failure", ("build", "run", "parse", "observation"))
def test_broken_e_infrastructure_failure_is_nonzero(monkeypatch, tmp_path, failure):
    path = Path(__file__).resolve().parents[2] / "tmp-verify/launch_cicada_run_gc.py"
    spec = importlib.util.spec_from_file_location("gc_launcher", path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    root = tmp_path / "repo"
    (root / launcher.POLICY_REL).parent.mkdir(parents=True)
    (root / launcher.POLICY_REL).write_text("{}")
    out = tmp_path / "out"
    out.mkdir()
    args = SimpleNamespace(repo_root=root, out_dir=out, job="GC", third_party_cache=tmp_path)
    monkeypatch.setattr(launcher, "JOBS", {"GC": {"BROKEN_E": [("G10-e", 8)]}})
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="head"))
    site = SimpleNamespace(current_site=lambda **k: {}, refuses_heavy_work=lambda *a: False)
    legacy = SimpleNamespace(_load_policy=lambda *a: {}, _resolve_toolchain=lambda *a: {},
                             _prepare_dependencies=lambda *a: {})
    harness = SimpleNamespace(checkout=lambda *a, **k: nullcontext(root),
                              assert_pinned_clean=lambda *a: None)
    monkeypatch.setattr(launcher, "patch_metadata", lambda *a: {})
    monkeypatch.setattr(launcher, "apply_owned_patch", lambda *a: None)
    monkeypatch.setattr(launcher, "configure_values", lambda *a: [])
    monkeypatch.setattr(launcher, "require_condition_gate", lambda *a: {})
    monkeypatch.setattr(launcher, "cache_values", lambda *a: {})
    if failure == "build":
        def fail_build(*a):
            raise RuntimeError("broken E build failed")
        monkeypatch.setattr(launcher, "build_variant", fail_build)
    else:
        monkeypatch.setattr(launcher, "build_variant", lambda *a: root / "binary")
        if failure == "run":
            def fail_run(*a):
                raise RuntimeError("broken E launch failed")
            monkeypatch.setattr(launcher, "run_one", fail_run)
        elif failure == "parse":
            monkeypatch.setattr(launcher, "run_one", lambda *a: {
                "build": "BROKEN_E", "error": "invalid CICADA_GC_V1 line", "gc_counters": None})
        else:
            monkeypatch.setattr(launcher, "run_one", lambda *a: {
                "build": "BROKEN_E", "error": None,
                "gc_counters": {"threads": [{"early_publishes": 0,
                    "early_publish_then_fail": 0, "held_changed": 0}]}})
    assert launcher.run_job(args, None, legacy, site, harness, None) == (0 if failure == "observation" else 1)
    result = json.loads((out / "result-GC.json").read_text())
    if failure == "build":
        assert result["builds"]["BROKEN_E"]["status"] == "failed"
    elif failure in ("run", "parse"):
        assert result["runs"]["BROKEN_E-G10-e-t8"]["error" if failure == "parse" else "exception"]
    else:
        assert result["broken_observation"]["BROKEN_E-G10-e-t8"]["reached"] is False
