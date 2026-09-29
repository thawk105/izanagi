"""Pure contracts for the diagnostic Cicada tuning producer."""
from __future__ import annotations

import copy
from contextlib import nullcontext
import json
import math
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tools.vhash_cicada_tuning import analysis as a, driver as d, model as m


def _raises(fn, kind=ValueError):
    try:
        fn()
    except kind:
        return
    raise AssertionError(f"expected {kind.__name__}")


def test_genomes_and_control():
    assert len(m.genomes()) == 24
    assert m.CONTROL in m.genomes()
    assert all(not g["INLINE_VERSION_PROMOTION"] or g["INLINE_VERSION_OPT"] for g in m.genomes())
    assert m.CONTROL == {"BACK_OFF": 1, "INLINE_VERSION_OPT": 0,
                         "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1,
                         "WRITE_LATEST_ONLY": 0}


def test_holdout_and_argv():
    assert "-ycsb_tuple_num=1000000" in m.runtime_argv(m.WORKLOADS["W2"], 1_000_000, 10)
    assert "-tuple_num=1000000" not in m.runtime_argv(m.WORKLOADS["W2"], 1_000_000, 10)
    for rr in (20, 80):
        _raises(lambda rr=rr: m.reject_holdout_ratio(rr))
        _raises(lambda: m.runtime_argv(m.Workload("W2", rr, 10), 1_000_000, 10))


def _commands(genome=None, wait=False):
    genome = genome or m.CONTROL
    definitions = {"TRACE": 0, "ADD_ANALYSIS": 0, **genome,
                   "WORKER1_INSERT_DELAY_RPHASE": int(wait)}
    if wait:
        definitions["WORKER1_INSERT_DELAY_RPHASE_US"] = 1000
    return [{"file": f"/tmp/cc/cicada/{name}.cc",
             "arguments": ["c++", *(f"-D{k}={v}" for k, v in definitions.items())]}
            for name in ("transaction", "util", "ycsb_cicada")]


def test_compile_binding_positive_and_negative():
    assert d.check_compile_commands(_commands(), m.CONTROL, False)["valid"]
    assert d.check_compile_commands(_commands(wait=True), m.CONTROL, True)["valid"]
    bad = _commands()
    bad[0]["arguments"][1] = "-DTRACE=1"
    _raises(lambda: d.check_compile_commands(bad, m.CONTROL, False))
    bad = _commands()
    bad[0]["arguments"] = [v.replace("-DWRITE_LATEST_ONLY=0", "-DWRITE_LATEST_ONLY=1")
                           for v in bad[0]["arguments"]]
    _raises(lambda: d.check_compile_commands(bad, m.CONTROL, False))
    bad = _commands(wait=True)
    bad[1]["arguments"] = [v for v in bad[1]["arguments"]
                           if not v.startswith("-DWORKER1_INSERT_DELAY_RPHASE_US=")]
    _raises(lambda: d.check_compile_commands(bad, m.CONTROL, True))


def test_runtime_flags_binding():
    argv = m.runtime_argv(m.WORKLOADS["W2"], 1_000_000, 10)
    lines = "\n".join(f"#FLAGS_{arg[1:].split('=')[0]}:\t{arg.split('=')[1]}"
                      for arg in argv)
    assert len(d.check_flags(lines, argv)) == len(argv)
    _raises(lambda: d.check_flags(lines.replace("#FLAGS_ycsb_rratio:\t50",
                                               "#FLAGS_ycsb_rratio:\t20"), argv))
    _raises(lambda: d.check_flags(lines.replace("#FLAGS_ycsb_tuple_num:\t1000000", ""), argv))


def test_run_parses_cicada_stdout_without_show_opt(tmp_path=None):
    if tmp_path is None:
        with TemporaryDirectory() as tmp:
            return test_run_parses_cicada_stdout_without_show_opt(Path(tmp))
    run = {"workload": "W2", "stage": "j1", "perf": False, "records": 1_000_000,
           "gc_inter_us": 10, "genome": m.CONTROL, "rep": 0}
    gflags = m.runtime_argv(m.WORKLOADS["W2"], run["records"], run["gc_inter_us"])
    stdout = "\n".join([
        "#FLAGS_group_commit:\t\tfalse",
        *(f"#FLAGS_{arg[1:].split('=')[0]}:\t{arg.split('=')[1]}" for arg in gflags),
        "abort_counts_:\t2", "commit_counts_:\t100", "maxrss:\t216208 kB",
        "throughput[tps]:\t1000", "throughput[ops]:\t9999", "",
    ])
    with patch.object(d, "_check_site"), patch.object(d, "_check_solo"), \
         patch.object(d, "assert_holdout_observation_admitted"), \
         patch.object(d.subprocess, "run", return_value=SimpleNamespace(
             stdout=stdout, stderr="", returncode=0)):
        row = d._run_one(run, tmp_path / "binary", "binary-sha", tmp_path,
                         "job", None, "host")
    assert row["throughput_tps"] == 1000.0
    assert row["abort_count"] == 2 and row["commit_count"] == 100
    assert row["show_opt_raw"] is None
    assert len(row["flags_raw"]) >= len(gflags)


def test_perf_csv_suffix_and_missing_counter(tmp_path=None):
    if tmp_path is None:
        with TemporaryDirectory() as tmp:
            return test_perf_csv_suffix_and_missing_counter(Path(tmp))
    run = {"workload": "W2", "stage": "j0_calibration", "perf": True,
           "records": 1_000_000, "gc_inter_us": 10, "genome": m.CONTROL, "rep": 0}
    gflags = m.runtime_argv(m.WORKLOADS["W2"], run["records"], run["gc_inter_us"])
    stdout = "\n".join([
        *(f"#FLAGS_{arg[1:].split('=')[0]}:\t{arg.split('=')[1]}" for arg in gflags),
        "abort_counts_:\t0", "commit_counts_:\t100", "maxrss:\t100 kB",
        "throughput[tps]:\t1000", "",
    ])
    perf_raw = ["100,,LLC-loads:u,\n20,,LLC-load-misses:u,\n",
                "<not counted>,,LLC-loads:u,\n<not supported>,,LLC-load-misses:u,\n"]

    def completed(argv, **_kwargs):
        (tmp_path / Path(argv[argv.index("-o") + 1])).write_text(perf_raw.pop(0))
        return SimpleNamespace(stdout=stdout, stderr="", returncode=0)

    with patch.object(d, "_check_site"), patch.object(d, "_check_solo"), \
         patch.object(d, "assert_holdout_observation_admitted"), \
         patch.object(d.subprocess, "run", side_effect=completed):
        row = d._run_one(run, tmp_path / "binary", "binary-sha", tmp_path,
                         "job", None, "host")
        assert row["miss_rate"] == 0.2
        row = d._run_one(run, tmp_path / "binary", "binary-sha", tmp_path,
                         "job", None, "host")
        assert row["miss_rate"] is None


def test_rss_boundary_and_saturation():
    l3 = 1024
    assert a.rss_lower_bound([{"records": 1, "maxrss_kb": 3},
                              {"records": 2, "maxrss_kb": 4}], l3) == 2
    assert a.choose_records([{"records": 1, "maxrss_kb": 3, "miss_rate": None},
                             {"records": 2, "maxrss_kb": 4, "miss_rate": None}], l3) == {
                                 "records": 2, "reason": "D15_RSS_lower_bound_perf_unavailable"}
    points = [{"records": 1_000_000, "miss_rate": 0.30, "maxrss_kb": 1000},
              {"records": 2_000_000, "miss_rate": 0.50, "maxrss_kb": 1000},
              {"records": 4_000_000, "miss_rate": 0.505, "maxrss_kb": 1000}]
    assert a.choose_records(points, l3)["reason"] == "observed_saturation_candidate"


def test_wait_alive_boundary():
    assert a.wait_alive([100] * 3, [50] * 3)["alive"]
    assert not a.wait_alive([100] * 3, [95] * 3)["alive"]


def test_cv_and_j2_boundary():
    assert math.isclose(a.sample_cv([1, 2, 3]), 0.5)
    rows = []
    for genome, tps in (("a", 100.0), ("b", 90.0), (m.canonical(m.CONTROL), 100.0)):
        rows.append({"stage": "j2", "perf": False, "exit_code": 0, "throughput_tps": tps,
                     "workload": "W1", "job_id": "job", "genome": genome, "gc_inter_us": 10})
    result = a.j2_best(rows, "W1", 0.1, [("a", 10), ("b", 10)], 3, expected_reps=1)
    assert ("b", 10) in result["observed_control_cv_width_candidates"]
    control_best = a.j2_best(rows, "W1", 0.1, [("a", 10), ("b", 10),
                                               (m.canonical(m.CONTROL), 10)], 3,
                             expected_reps=1)
    assert control_best["best"] == (m.canonical(m.CONTROL), 10)
    assert a.j2_best(rows, "W1", None, [("a", 10)], 3)["status"] == "undetermined"
    assert a.j2_best(rows, "W1", 0.1, [("a", 10)], 2)["status"] == "undetermined"
    assert a.j2_best(rows, "W1", 0.1, [("missing", 10)], 3)["status"] == "undetermined"


def test_j2_best_with_two_sessions_keeps_scores():
    control = m.canonical(m.CONTROL)
    rows = [{"stage": "j2", "perf": False, "exit_code": 0,
             "throughput_tps": tps, "workload": "W5", "job_id": "job",
             "genome": genome, "gc_inter_us": 10}
            for genome, tps in ((control, 100.0), ("candidate", 110.0))]
    result = a.j2_best(rows, "W5", 0.05, [(control, 10), ("candidate", 10)],
                       2, expected_reps=1)
    assert result["best"] == ("candidate", 10)
    assert result["best_score"] == 1.1
    assert result["scores"] == {f"{control}|10": 1.0, "candidate|10": 1.1}
    assert result["observed_control_cv_width_candidates"] is None
    assert result["candidate_status"] == "undetermined"
    assert result["candidate_reason"] == "control_cv_or_sessions_missing"
    missing_cv = a.j2_best(rows, "W5", None, [(control, 10), ("candidate", 10)],
                           3, expected_reps=1)
    assert missing_cv["best"] == result["best"]
    assert missing_cv["observed_control_cv_width_candidates"] is None


def test_build_isolates_masstree_and_preserves_failure_logs(tmp_path=None):
    if tmp_path is None:
        with TemporaryDirectory() as tmp:
            return test_build_isolates_masstree_and_preserves_failure_logs(Path(tmp))
    source = tmp_path / "source"
    source.mkdir()
    shared = tmp_path / "shared-masstree"
    shared.mkdir()
    (shared / "source.txt").write_text("original")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    deps = {"masstree": shared, "mimalloc": tmp_path / "mimalloc",
            "googletest": tmp_path / "googletest", "gflags": tmp_path / "gflags",
            "glog": tmp_path / "glog"}
    toolchain = {"cc_path": "/usr/bin/gcc", "cxx_path": "/usr/bin/g++"}
    seen = []

    def cmake(argv, **kwargs):
        log = kwargs["stdout"]
        log.write("command output\n")
        if "-S" in argv:
            masstree = Path(next(arg.split("=", 1)[1] for arg in argv
                                 if arg.startswith("-DFETCHCONTENT_SOURCE_DIR_MASSTREE=")))
            seen.append(masstree)
            assert (masstree / "source.txt").read_text() == "original"
            assert next(arg for arg in argv if arg.startswith("-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=")) == \
                f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={deps['mimalloc']}"
            return SimpleNamespace(returncode=0)
        if Path(argv[2]).name == f"build-{d.digest((m.canonical(m.CONTROL) + 'True').encode())[:12]}":
            binary = Path(argv[2]) / "cc/cicada/ycsb_cicada.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"binary")
            (Path(argv[2]) / "compile_commands.json").write_text("[]")
            return SimpleNamespace(returncode=0)
        return SimpleNamespace(returncode=2)

    with patch.object(d.subprocess, "run", side_effect=cmake), \
         patch.object(d, "check_compile_commands", return_value={"valid": True}):
        for wait in (False, True):
            try:
                result = d._build(source, scratch, deps, toolchain,
                                  {"genome": m.CONTROL, "wait": wait}, 2, output)
            except d.BuildFailure as exc:
                assert not wait
                record = exc.record
            else:
                assert wait
                record, binary = result
                assert binary.read_bytes() == b"binary"
                assert record["binary_sha256"] == d.digest(b"binary")
            assert record["build_rc"] == (0 if wait else 2)
            if not wait:
                assert record["failure_stage"] == "build" and record["failure_rc"] == 2
                assert Path(record["failure_log"]).read_text() == "command output\n"
            assert record["configure_log_sha256"] == d.digest(b"command output\n")
            assert record["build_log_sha256"] == d.digest(b"command output\n")
    assert len(set(seen)) == 2
    assert all(path.parent == scratch and ":" not in str(path) for path in seen)
    assert (shared / "source.txt").read_text() == "original"


def test_failed_build_is_recorded_in_manifest(tmp_path=None):
    if tmp_path is None:
        with TemporaryDirectory() as tmp:
            return test_failed_build_is_recorded_in_manifest(Path(tmp))
    spec = {"schema": d.SCHEMA, "job_id": "build-failure", "stage": "j0",
            "build_parallelism": 1, "builds": [], "runs": []}
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    output = tmp_path / "output"
    output.mkdir()
    record = {"label": "test", "failure_stage": "configure", "failure_rc": 2,
              "failure_log": str(output / "build-test.configure.log")}

    def fake_run(argv, **kwargs):
        assert argv[:2] == ["git", "-C"]
        return SimpleNamespace(stdout="pin\n")

    with patch.object(d, "OUTPUT", output), patch.object(d, "_check_site"), \
         patch.object(d, "_check_solo"), \
         patch.object(d, "_prepare_toolchain", return_value=({}, {})), \
         patch.object(d.patchharness, "checkout", return_value=nullcontext(tmp_path)), \
         patch.object(d.subprocess, "run", side_effect=fake_run), \
         patch.object(d, "_build", side_effect=d.BuildFailure(record)):
        _raises(lambda: d.execute(spec_path, tmp_path, tmp_path), d.BuildFailure)
    manifest = json.loads((output / "build-failure/job-manifest.json").read_text())
    assert len(manifest["builds"]) == 2
    assert all(entry == record for entry in manifest["builds"])
    assert manifest["status"] == "failed"


def test_control_session_cv_metadata():
    rows = [{"stage": "j1", "perf": False, "exit_code": 0,
             "throughput_tps": value, "workload": "W1", "records": 1_000_000,
             "gc_inter_us": 10, "genome": m.canonical(m.CONTROL),
             "job_id": f"j{i}", "host": f"h{i % 2}", "submission_cluster": f"c{i % 2}"}
            for i, value in enumerate((100, 110, 90))]
    result = a.control_cv(rows, "W1", 1_000_000)
    assert result["session_count"] == result["job_count"] == 3
    assert result["cluster_count"] == result["host_count"] == 2
    assert math.isclose(result["cv"], 0.1)


def test_select_j1_tie_and_spec_determinism():
    control = m.canonical(m.CONTROL)
    candidates = [m.canonical(g) for g in m.genomes() if g != m.CONTROL][:2]
    rows = [{"stage": "j1", "perf": False, "exit_code": 0, "throughput_tps": 100.0,
             "workload": "W1", "job_id": "job", "genome": g, "gc_inter_us": 10}
            for g in [control, *candidates]]
    rows.append({**rows[-1], "perf": True, "throughput_tps": 10_000.0})
    assert a.select_j1(rows, 2)["W1"] == sorted(candidates)
    records = {w: 1_000_000 for w in m.WORKLOADS}
    first = d.make_spec("j1", records)
    assert first == d.make_spec("j1", records)
    assert len(first) == 4 and sum(len(s["runs"]) for s in first) > 0
    assert all(any(b["genome"] == m.CONTROL for b in s["builds"]) for s in first)
    selected = {w: [m.canonical(g) for g in m.genomes()[:3]] for w in m.WORKLOADS}
    j2 = d.make_spec("j2", records, selected=selected)
    assert j2 == d.make_spec("j2", records, selected=selected)
    assert len(j2) == 5 and all(s["stage"] == "j2" for s in j2)


def test_estimate_walltime():
    spec = {"build_parallelism": 2, "builds": [{"wait": False}] * 2 + [{"wait": True}],
            "runs": [{"workload": "W1"}] * 2}
    costs = {"dependencies_s": 10, "build_normal_s": 20, "build_wait_s": 30,
             "run_s": {"W1": 5}}
    assert a.estimate_walltime(spec, costs) == 2


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:
                failed += 1
                print("FAIL", name, repr(exc))
    return failed


if __name__ == "__main__":
    sys.exit(_run())
