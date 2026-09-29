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
    zero = driver.gc_plan_runs("wait_after_reads", 10000, skew=0)
    assert all(s["skew"] == 0 for s in zero)
    assert "-ycsb_zipf_skew=0" in driver._argv(tmp_path / "binary", zero[0])
    assert "-ycsb_zipf_skew=0.9" in driver._argv(tmp_path / "binary", specs[0])


@pytest.mark.parametrize("workload", ("normal", "many_ops"))
def test_gc_skew_zero_rejected_for_controls(workload, tmp_path):
    with pytest.raises(SystemExit) as exc:
        driver.main(["gc-run", "--workload", workload, "--skew", "0",
                     "--third-party-cache", str(tmp_path)])
    assert exc.value.code == 2


def _gc_job(workload="normal", wait_us=None, skew=0.9):
    records = []
    for spec in driver.gc_plan_runs(workload, wait_us, skew=skew):
        records.append({**spec, "valid": True,
            "perf_eligible": not spec["build_kind"].endswith("-count"),
            "throughput": 100, "gc_counters": _gc_payload() if spec["build_kind"].endswith("-count") else None,
            "longtx_counters": {"threads": [{"thid": 1, "long": False}]}})
    return {"command": "gc-run", "all_pass": True, "workload": workload,
            "wait_us": wait_us, "skew": skew,
            "records": records}


def _gc_jobs():
    return [_gc_job("wait_after_reads", wait, skew)
            for wait in (1000, 10000) for skew in (0.9, 0)] + [
            _gc_job("normal"), _gc_job("many_ops")]


@pytest.mark.parametrize("missing_index", range(6))
def test_gc_aggregate_rejects_each_missing_job(missing_index):
    jobs = _gc_jobs()
    jobs.pop(missing_index)
    with pytest.raises(ValueError, match="missing GC jobs"):
        driver.gc_aggregate_jobs(jobs)


def test_gc_aggregate_complete_and_missing_md1_md5():
    jobs = _gc_jobs()
    aggregate = driver.gc_aggregate_jobs(jobs)
    assert len(aggregate["cells"]) == 18
    cell = aggregate["cells"]["normal/wait=None/skew=0.9/gc=10"]
    assert len(cell["arms"]["E"]["performance"]) == 3
    assert len(cell["arms"]["E"]["gc"]) == 1
    assert cell["arms"]["E"]["throughput_median_tps"] == 100
    jobs[4]["records"].pop()
    with pytest.raises(ValueError, match="missing or extra cell"):
        driver.gc_aggregate_jobs(jobs)
    jobs = _gc_jobs()
    next(r for r in jobs[4]["records"] if r["build_kind"].endswith("-count"))["perf_eligible"] = True
    with pytest.raises(ValueError, match="mislabeled"):
        driver.gc_aggregate_jobs(jobs)
    with pytest.raises(ValueError, match="duplicate GC job"):
        driver.gc_aggregate_jobs([*_gc_jobs(), _gc_job("wait_after_reads", 1000, 0)])
    extra = _gc_job("normal")
    extra["wait_us"] = 1000
    with pytest.raises(ValueError, match="unexpected GC job"):
        driver.gc_aggregate_jobs([*_gc_jobs(), extra])
    jobs = _gc_jobs()
    jobs[0]["records"][0]["skew"] = 0
    with pytest.raises(ValueError, match="record condition differs"):
        driver.gc_aggregate_jobs(jobs)
    jobs = _gc_jobs()
    del jobs[0]["records"][0]["skew"]
    with pytest.raises(KeyError, match="skew"):
        driver.gc_aggregate_jobs(jobs)


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
    for job in jobs[:4]:
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
    cell = driver.gc_aggregate_jobs(jobs)["cells"]["wait_after_reads/wait=1000/skew=0.9/gc=10"]
    e = cell["arms"]["E"]["gc"][0]
    assert e["lag_wts_p50_upper_us"] == 2
    assert e["publish_count"] == e["begin_count"] == e["retention_count"] == 1
    assert e["publish_lag_rts_p50_upper_us"] == e["begin_lag_rts_p50_upper_us"] == 2
    assert e["retention_sum_us"] == e["retention_p50_upper_us"] == 8
    assert e["series"] == [[0, 4, 100]] and e["max_gap_intervals"] == 3
    comparisons = cell["gc_comparisons"]
    assert cell["skew"] == comparisons["primary_E_minus_E-hb"]["skew"] == 0.9
    assert cell["skew"] == comparisons["auxiliary_E-hb_minus_stock"]["skew"]
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
    assert job["skew"] == 0.9 and all(record["skew"] == 0.9 for record in job["records"])
    assert job["e_success_total"] == 0 and "success total is zero" in job["error"]
    assert job["all_pass"] is False
    calls = _gc_main_fixture(monkeypatch, tmp_path, success=1)
    assert driver.main(argv) == 0
    assert calls[:2] == ["gc-dependency", "gc-stock"]


def test_gc_run_raw_skew_zero(monkeypatch, tmp_path):
    _gc_main_fixture(monkeypatch, tmp_path)
    assert driver.main(["gc-run", "--workload", "wait_after_reads", "--wait-us", "1000",
                        "--skew", "0", "--third-party-cache", str(tmp_path),
                        "--output", str(tmp_path)]) == 0
    job = json.loads(next(tmp_path.glob("raw-gc-run-*.json")).read_text())
    assert job["skew"] == 0 and job["all_pass"]
    assert job["records"] and all(record["skew"] == 0 for record in job["records"])


def test_gc_gate_rejection_evidence_is_saved(monkeypatch, tmp_path):
    calls = _gc_main_fixture(monkeypatch, tmp_path, gate_failure=True)
    assert driver.main(["gc-run", "--workload", "normal", "--third-party-cache",
                        str(tmp_path), "--output", str(tmp_path)]) == 1
    job = json.loads(next(tmp_path.glob("raw-gc-run-*.json")).read_text())
    assert calls == ["gc-dependency", "gc-stock"]
    assert job["condition_gate_evidence"]["meaning"]["admitted"] is False
    assert job["condition_gate_evidence"]["admission"]["admitted"] is False


def _target_counter_text(arm):
    gc = _gc_payload()
    gc["mode"] = "e" if arm.startswith("E-") and arm != "E-hb" else "hb" if arm == "E-hb" else "none"
    lines = []
    if arm != "stock":
        fwd = {"schema": 1, "policy": "f" if arm == "F" else "c", "k": 3,
               "threads": [_fwd_thread()]}
        if arm.startswith("C-") and arm != "C-min":
            fwd.update(schema=2, target="max" if arm == "C-max" else "partial",
                       once=arm == "C-partial-once")
            fwd["threads"] = [{**fwd["threads"][0], **{k: 0 for k in driver.TARGET_EXTRA},
                               "short_success": 0}]
            version = 2
        else:
            version = 1
        lines.append(f"CICADA_FWD_V{version} " + json.dumps(fwd))
    if arm in ("E-max", "E-max-once"):
        gc.update(schema=2, target="max", once=arm == "E-max-once")
        gc["threads"] = [{**row, **{k: 0 for k in driver.TARGET_EXTRA}}
                         for row in gc["threads"]]
        version = 2
    else:
        version = 1
    lines.append(f"CICADA_GC_V{version} " + json.dumps(gc))
    lines.append("CICADA_LONGTX_V1 " + json.dumps({"schema": 1, "threads": [
        {"thid": 1, "long": False, "commits": 1, "aborts": 0}]}))
    return "\n".join(lines) + "\n"


def _target_jobs():
    jobs = []
    for workload, wait, skew in sorted(driver.TARGET_JOBS, key=str):
        records = []
        for spec in driver.target_plan_runs(workload, wait, skew=skew):
            counted = spec["build_kind"].endswith("-count")
            stdout = _target_counter_text(spec["arm"]) if counted else \
                     "CICADA_LONGTX_V1 " + json.dumps({"schema": 1, "threads": [
                         {"thid": 1, "long": False, "commits": 1, "aborts": 0}]})
            fwd, gc, longtx = driver.parse_target_lines(stdout, spec["arm"], counted)
            records.append({**spec, "valid": True, "perf_eligible": not counted,
                            "argv": driver.target_argv(Path("/tmp/ycsb"), spec),
                            "stdout": {"text": stdout, "sha256": driver.sha_bytes(stdout.encode())},
                            "throughput": 100 if not counted else 999,
                            "gc_counters": gc, "fwd_counters": fwd,
                            "longtx_counters": longtx})
        jobs.append({"command": "target-run", "all_pass": True, "smoke": False,
                     "workload": workload, "wait_us": wait, "skew": skew, "records": records,
                     "ccbench_pin": driver.pin.CURRENT_PIN, "genome": driver.GC_GENOME,
                     "patch_sha256": {str(p.relative_to(driver.ROOT)): "0" * 64
                                      for p in driver.TARGET_STACK}})
    return jobs


def test_target_parse_accepts_real_longtx_line():
    # LONGTX line copied from smoke1-stock-stdout.txt (stage 6 smoke 1, stock).
    line = 'CICADA_LONGTX_V1 {"schema":1,"threads":[{"thid":0,"long":false,"commits":64304,"aborts":41268},{"thid":1,"long":false,"commits":64981,"aborts":41297},{"thid":2,"long":false,"commits":64944,"aborts":41099},{"thid":3,"long":false,"commits":64727,"aborts":40622},{"thid":4,"long":false,"commits":65264,"aborts":40925},{"thid":5,"long":false,"commits":65210,"aborts":41153},{"thid":6,"long":false,"commits":64459,"aborts":40477},{"thid":7,"long":false,"commits":64029,"aborts":40455},{"thid":8,"long":false,"commits":68288,"aborts":41361},{"thid":9,"long":false,"commits":64208,"aborts":41524},{"thid":10,"long":false,"commits":67337,"aborts":41846},{"thid":11,"long":false,"commits":67890,"aborts":41381},{"thid":12,"long":false,"commits":64647,"aborts":40999},{"thid":13,"long":false,"commits":66516,"aborts":41061},{"thid":14,"long":false,"commits":65838,"aborts":41852},{"thid":15,"long":false,"commits":65519,"aborts":40541},{"thid":16,"long":false,"commits":65793,"aborts":40702},{"thid":17,"long":false,"commits":68498,"aborts":41597},{"thid":18,"long":false,"commits":66000,"aborts":41715},{"thid":19,"long":false,"commits":66880,"aborts":41349},{"thid":20,"long":false,"commits":64206,"aborts":40999},{"thid":21,"long":false,"commits":65683,"aborts":41386},{"thid":22,"long":false,"commits":64312,"aborts":41220},{"thid":23,"long":false,"commits":68718,"aborts":41569},{"thid":24,"long":false,"commits":65666,"aborts":41321},{"thid":25,"long":false,"commits":65032,"aborts":41587},{"thid":26,"long":false,"commits":63987,"aborts":40865},{"thid":27,"long":false,"commits":67078,"aborts":41309},{"thid":28,"long":false,"commits":65428,"aborts":41193},{"thid":29,"long":false,"commits":65579,"aborts":41677},{"thid":30,"long":false,"commits":66573,"aborts":41430},{"thid":31,"long":false,"commits":65138,"aborts":41131},{"thid":32,"long":false,"commits":63838,"aborts":40336},{"thid":33,"long":false,"commits":65991,"aborts":40829},{"thid":34,"long":false,"commits":66131,"aborts":41544},{"thid":35,"long":false,"commits":64805,"aborts":40301},{"thid":36,"long":false,"commits":66971,"aborts":40617},{"thid":37,"long":false,"commits":65881,"aborts":40695},{"thid":38,"long":false,"commits":64118,"aborts":40615},{"thid":39,"long":false,"commits":67918,"aborts":40723},{"thid":40,"long":false,"commits":67039,"aborts":41518},{"thid":41,"long":false,"commits":65201,"aborts":41247},{"thid":42,"long":false,"commits":67211,"aborts":40863},{"thid":43,"long":false,"commits":67445,"aborts":41086},{"thid":44,"long":true,"commits":33,"aborts":67},{"thid":45,"long":true,"commits":4,"aborts":100},{"thid":46,"long":true,"commits":22,"aborts":83},{"thid":47,"long":true,"commits":20,"aborts":83}]}'
    fwd, gc, longtx = driver.parse_target_lines(line, "stock", False)
    assert fwd is None and gc is None
    assert longtx["schema"] == 1
    assert len(longtx["threads"]) == 48
    assert sum(row["long"] for row in longtx["threads"]) == 4


@pytest.mark.parametrize("schema", [0, 2, True, None])
def test_target_longtx_rejects_invalid_schema(schema):
    def change(payload):
        if schema is None:
            del payload["schema"]
        else:
            payload["schema"] = schema

    line = _replace_target_counter(_target_counter_text("stock"), "CICADA_LONGTX_V1 ", change)
    with pytest.raises(ValueError, match="longtx schema invalid"):
        driver.parse_target_lines(line, "stock", True)


def test_target_patch_stack():
    assert [p.name for p in driver.TARGET_STACK] == [
        "cicada-forwarding-variant.patch", "cicada-forwarding-gc.patch",
        "cicada-forwarding-target.patch"]
    assert driver.TARGET_PATCH == driver.ROOT / "patches/cicada-forwarding-target.patch"
    assert driver.GC_GENOME["REUSE_VERSION"] == 1


def test_target_count_throughput_ineligible():
    data = driver.target_aggregate_jobs(_target_jobs())
    cell = data["cells"]["many_ops/wait=None/skew=0.6/gc=10"]
    assert cell["arms"]["C-min"]["throughput_median_tps"] == 100
    assert len(cell["arms"]["C-min"]["performance"]) == 3
    assert all("throughput_tps" not in row for row in cell["arms"]["C-min"]["count"])
    assert all("series" not in row["gc"] for row in cell["arms"]["C-min"]["count"])


def test_target_v2_exactly_once():
    line = _target_counter_text("E-max")
    assert driver.parse_target_lines(line, "E-max", True)[1]["target"] == "max"
    doubled = line + next(x for x in line.splitlines() if x.startswith("CICADA_GC_V2 ")) + "\n"
    with pytest.raises(ValueError, match="expected 1 lines, found 2"):
        driver.parse_target_lines(doubled, "E-max", True)


def test_target_rotation():
    specs = driver.target_plan_runs("many_ops", None, skew=.9)
    for rep in range(3):
        actual = tuple(r["arm"] for r in specs if r["gc_inter_us"] == 10 and
                       not r["build_kind"].endswith("-count") and r["rep"] == rep)
        arms = driver.TARGET_ARMS["many_ops"]
        assert actual == arms[rep:] + arms[:rep]


@pytest.mark.parametrize("missing_index", range(7))
def test_target_aggregate_rejects_each_missing_job(missing_index):
    jobs = _target_jobs()
    jobs.pop(missing_index)
    with pytest.raises(ValueError, match="missing target jobs"):
        driver.target_aggregate_jobs(jobs)


def test_target_v2_schema():
    line = _target_counter_text("C-partial")
    assert driver.parse_target_lines(line, "C-partial", True)[0]["target"] == "partial"
    payload = json.loads(next(x.split(" ", 1)[1] for x in line.splitlines()
                              if x.startswith("CICADA_FWD_V2 ")))
    del payload["threads"][0]["no_room"]
    bad = "CICADA_FWD_V2 " + json.dumps(payload) + "\n" + "\n".join(
        x for x in line.splitlines() if not x.startswith("CICADA_FWD_V2 "))
    with pytest.raises(ValueError, match="thread schema"):
        driver.parse_target_lines(bad, "C-partial", True)


def test_target_success_rate_denominator():
    gc = _gc_payload()
    gc["threads"][0].update(requests=4, attempts=2, success=1, read_mismatch=1,
                            overflow=1, no_room=1, once_skipped=0)
    gc["threads"][1].update({k: 0 for k in driver.TARGET_EXTRA})
    assert driver.target_success_metrics(gc, "E")["success_rate"] == .25
    assert driver.target_success_metrics(gc, "E")["attempt_success_rate"] == .5


def test_target_arm_flags():
    assert "--cicada_gc_target=max" in driver.target_arm_flags("E-max")
    assert "--cicada_gc_target=now" not in driver.target_arm_flags("E-max")
    assert "--cicada_fwd_policy=f" in driver.target_arm_flags("F")
    assert "--cicada_fwd_once=true" in driver.target_arm_flags("C-partial-once")
    spec = next(s for s in driver.target_plan_runs("wait_after_reads", 10000)
                if s["arm"] == "E-max" and s["build_kind"].endswith("-count"))
    assert driver.target_argv(Path("/tmp/ycsb"), spec).count("--cicada_gc_sample_us=10") == 1


def test_target_default_v1_and_nondefault_rejects_v1():
    assert driver.parse_target_lines(_target_counter_text("C-min"), "C-min", True)[0]["schema"] == 1
    assert driver.parse_target_lines(_target_counter_text("E-now"), "E-now", True)[1]["schema"] == 1
    with pytest.raises(ValueError, match="CICADA_GC_V1 expected 0 lines"):
        driver.parse_target_lines(_target_counter_text("E-now"), "E-max", True)


def test_target_broken_requires_v2_forced_success():
    with pytest.raises(ValueError, match="CICADA_GC_V1 expected 0 lines"):
        driver.parse_target_lines(_target_counter_text("E-now"), "E-now", True, broken=True)

    v2 = _target_counter_text("E-max")
    with pytest.raises(ValueError, match="GC V2 thread schema invalid"):
        driver.parse_target_lines(v2, "E-max", True, broken=True)

    def broken_now(gc):
        gc["target"] = "now"
        for row in gc["threads"]:
            row["forced_success"] = 0

    now_v2 = _replace_target_counter(v2, "CICADA_GC_V2 ", broken_now)
    assert driver.parse_target_lines(now_v2, "E-now", True, broken=True)[1]["target"] == "now"
    with pytest.raises(ValueError, match="GC V2 top schema invalid"):
        driver.parse_target_lines(now_v2, "E-max", True, broken=True)


def _replace_target_counter(text, prefix, change):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            payload = json.loads(line[len(prefix):])
            change(payload)
            lines[index] = prefix + json.dumps(payload)
            return "\n".join(lines) + "\n"
    raise AssertionError("missing counter line: " + prefix)


def test_target_ehb_requests_without_attempts_accepted():
    line = _replace_target_counter(_target_counter_text("E-hb"), "CICADA_GC_V1 ",
        lambda gc: gc["threads"][0].update(requests=5, attempts=0, flag_raises=5))
    gc = driver.parse_target_lines(line, "E-hb", True)[1]
    metrics = driver.target_success_metrics(gc, "E")
    assert metrics["requests"] == 5 and metrics["flag_raises"] == 5
    assert metrics["success_rate"] is None
    assert all(value is None for value in metrics["failure_reasons_per_request"].values())
    bad = _replace_target_counter(_target_counter_text("E-max"), "CICADA_GC_V2 ",
        lambda gc: gc["threads"][0].update(requests=5, attempts=0, flag_raises=5))
    with pytest.raises(ValueError, match="E request accounting mismatch"):
        driver.target_success_metrics(driver.parse_target_lines(bad, "E-max", True)[1], "E")


def test_target_v2_schema_version_is_two():
    for arm, prefix, index in (("C-partial", "CICADA_FWD_V2 ", 0),
                               ("E-max", "CICADA_GC_V2 ", 1)):
        line = _target_counter_text(arm)
        assert driver.parse_target_lines(line, arm, True)[index]["schema"] == 2
        bad = _replace_target_counter(line, prefix, lambda value: value.update(schema=1))
        with pytest.raises(ValueError, match="schema invalid"):
            driver.parse_target_lines(bad, arm, True)


def test_target_gc_mode_matches_arm():
    for arm, prefix, mode in (("E-hb", "CICADA_GC_V1 ", "hb"),
                              ("E-now", "CICADA_GC_V1 ", "e"),
                              ("E-max", "CICADA_GC_V2 ", "e"),
                              ("stock", "CICADA_GC_V1 ", "none"),
                              ("C-min", "CICADA_GC_V1 ", "none"),
                              ("F", "CICADA_GC_V1 ", "none")):
        line = _target_counter_text(arm)
        assert driver.parse_target_lines(line, arm, True)[1]["mode"] == mode
        bad = _replace_target_counter(line, prefix,
                                      lambda value: value.update(mode="off" if mode != "off" else "e"))
        with pytest.raises(ValueError, match="GC mode does not match target arm"):
            driver.parse_target_lines(bad, arm, True)


@pytest.mark.parametrize("arm", ("stock", "C-min", "C-max", "C-partial",
                                  "C-partial-once", "F"))
def test_target_gc_mode_none_for_non_safepoint_builds(arm):
    assert "CICADA_GC_SAFEPOINT" not in driver.MACROS[driver.target_build_kind(arm, True)]
    line = _target_counter_text(arm)
    assert driver.parse_target_lines(line, arm, True)[1]["mode"] == "none"
    bad = _replace_target_counter(line, "CICADA_GC_V1 ",
                                  lambda value: value.update(mode="off"))
    with pytest.raises(ValueError, match="GC mode does not match target arm"):
        driver.parse_target_lines(bad, arm, True)


def test_target_policy_exercised_flag():
    jobs = _target_jobs()
    data = driver.target_aggregate_jobs(jobs)
    for cell in data["cells"].values():
        for arm, summary in cell["arms"].items():
            if arm != "stock":
                assert summary["policy_exercised"] is False
    record = next(r for r in jobs[0]["records"] if r["arm"] == "C-min" and
                  r["build_kind"].endswith("-count"))
    record["stdout"]["text"] = _replace_target_counter(record["stdout"]["text"],
        "CICADA_FWD_V1 ", lambda fwd: fwd["threads"][0].update(
            triggers=1, attempts=1, success=1))
    record["stdout"]["sha256"] = driver.sha_bytes(record["stdout"]["text"].encode())
    record["fwd_counters"] = driver.parse_target_lines(
        record["stdout"]["text"], "C-min", True)[0]
    updated = driver.target_aggregate_jobs(jobs)
    key = (f"{jobs[0]['workload']}/wait={jobs[0]['wait_us']}/skew={jobs[0]['skew']:g}/"
           f"gc={record['gc_inter_us']}")
    assert updated["cells"][key]["arms"]["C-min"]["policy_exercised"] is True
