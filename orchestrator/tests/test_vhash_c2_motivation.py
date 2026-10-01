"""Offline C2 contracts; M1--M9 each have one isolated numerical/semantic witness."""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest.mock as mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import vhash_c2_motivation as C
from orchestrator.campaign import vhash_cicada_vlife as V
from orchestrator.campaign import condition_meaning_gate as gate
from orchestrator.campaign.materializer_admission import non_admissible_materializer
from orchestrator.tests.test_vhash_cicada_vlife import _payload3

POINT = "skew0-ops100-rr50"


def test_m1_perf_macros_exclude_instruments():
    assert C.macros("perf", "S") == ("IZANAGI_CICADA_LONGTX",)
    assert C.macros("diag", "S") == ("IZANAGI_CICADA_LONGTX", "IZANAGI_CICADA_VLIFE")


def test_m2_r_enables_ro_gcflag():
    for kind in ("perf", "diag"):
        for arm in ("R", "R-noLT"):
            assert "IZANAGI_CICADA_RO_GCFLAG" in C.macros(kind, arm)


def test_m3_no_long_worker_in_controls():
    assert C.flags(POINT, "R-noLT", "perf", 10, 3)["batch_th_num"] == 0
    assert C.flags(POINT, "S", "perf", 10, 3)["batch_th_num"] == 1


def test_m4_controls_keep_47_normal_workers():
    for arm in C.ARMS:
        assert C.flags(POINT, arm, "diag", 10, 3)["thread_num"] == 47


def _eligible(rate=.10, age=1000, commits=100):
    return dict(valid=True, long_completion_rate=rate, long_commits=commits,
                gc_boundary_mean_us=age)


def test_m5_completion_threshold_only():
    control = dict(valid=True, gc_boundary_mean_us=250)
    assert C.established(_eligible(), control)
    assert not C.established(_eligible(rate=.099), control)


def test_m6_boundary_ratio_threshold_only():
    assert C.established(_eligible(), dict(valid=True, gc_boundary_mean_us=250))
    assert not C.established(_eligible(), dict(valid=True, gc_boundary_mean_us=251))


def test_m7_round_rotation_and_even_reversal():
    expected = [("S", "R", "S-noLT", "R-noLT"),
                ("S", "R-noLT", "S-noLT", "R"),
                ("S-noLT", "R-noLT", "S", "R"),
                ("S-noLT", "R", "S", "R-noLT"),
                ("S", "R", "S-noLT", "R-noLT")]
    assert [C.arm_order(r) for r in range(1, 6)] == expected
    plan = C.measure_plan(POINT, "perf", 100, 5, 10)
    assert [p[1] for p in plan] == [a for group in expected for a in group]


def _diag(point=POINT, arm="R", age=1000, attempts=1000, commits=100):
    payload = _payload3()
    payload["build"].update(inline_version_opt=1, izanagi_long_kind=1)
    run_flags = C.flags(point, arm, "diag", 10, 3)
    payload["workers"] = [copy.deepcopy(payload["workers"][0]) for _ in
                          range(run_flags["thread_num"] + run_flags["batch_th_num"])]
    worker = payload["workers"][-1]
    if arm.endswith("-noLT"):
        attempts = commits = 0
    worker.update(attempts=[900, attempts], commits=[800, commits], install=40, detach=10)
    for w, count, mean in ((payload["workers"][0], 3, age), (worker, 1, 2 * age)):
        bucket = next(i for i, bound in enumerate(V.TIME_BOUNDS) if mean <= bound)
        w["gc_boundary_us"][bucket] = count
        w["gc_boundary_count"], w["gc_boundary_sum_us"] = count, count * mean
    for i, chain in enumerate(payload["hot_chains"]):
        chain["length"] = i + 1
    return dict(point=point, arm=arm, kind="diag", gc=10, extime=3, round=1,
                flags=run_flags, macros=list(C.macros("diag", arm)), rc=0,
                stdout=V.PREFIX + json.dumps(payload), hostname="nodeA",
                job_started_at="2026-10-01T00:00:00+00:00")


def test_m8_long_completion_uses_worker_slot_one():
    summary = C.summarize_run(_diag())
    assert (summary["long_attempts"], summary["long_commits"],
            summary["long_completion_rate"], summary["normal_commits"]) == (1000, 100, .1, 800)


def test_m9_b_uses_highest_completion():
    grid = [dict(point=p, established=True, boundary_ratio=ratio,
                 zero_control_mean=False, long_completion_rate=rate)
            for p, ratio, rate in (("a", 10, .2), ("b", 5, .8), ("c", 6, .1))]
    assert C.choose_points(grid) == {"A": "a", "B": "b"}
    grid[0]["long_completion_rate"] = .9
    assert C.choose_points(grid) == {"A": "a", "B": None}
    assert C.choose_points([]) == {"A": None, "B": None}


def _commands(arm="R"):
    # Independent fixture reproduces CMake's three target commands, including Boost.
    definitions = dict(ADD_ANALYSIS=0, KEY_SIZE=8, VAL_SIZE=4, MASSTREE_USE=1,
        TRACE=0, SINGLE_EXEC=0, WORKER1_INSERT_DELAY_RPHASE=0, PARTITION_TABLE=0,
        Linux=1, NDEBUG=1, BOOST_ALL_NO_LIB=1, BOOST_FILESYSTEM_DYN_LINK=1,
        BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0,
        REUSE_VERSION=1, WRITE_LATEST_ONLY=0, IZANAGI_CICADA_LONGTX=1)
    if arm == "R":
        definitions["IZANAGI_CICADA_RO_GCFLAG"] = 1
    return [dict(file="/source/cc/cicada/" + name,
                 arguments=["c++", *[f"-D{k}={v}" for k, v in definitions.items()],
                            "-o", "CMakeFiles/ycsb_cicada.exe.dir/" + name + ".o", "-c", name])
            for name in ("transaction.cc", "util.cc", "ycsb_cicada.cc")]


def test_compile_defines_bind_complete_target_and_genome():
    for arm in ("S", "R"):
        commands = _commands(arm)
        C.check_perf_defines(commands, arm)
        for row in commands:
            row["command"] = " ".join(row.pop("arguments"))
        C.check_perf_defines(commands, arm)
    for extra in ("-DIZANAGI_CICADA_VLIFE=1", "-DIZANAGI_CICADA_RO_GCFLAG_COUNT=1",
                  "-DTRACE=1", "-DUNEXPECTED=1", "-DVAL_SIZE=100"):
        commands = _commands()
        commands[0]["arguments"].append(extra)
        with pytest.raises(ValueError):
            C.check_perf_defines(commands, "R")
    with pytest.raises(ValueError):
        C.check_perf_defines(_commands()[:2], "R")
    with pytest.raises(ValueError):
        C.check_perf_defines(_commands("S"), "R")


def test_flags_match_source_definitions_and_diagnostic_scope():
    common = (C.ROOT / "external/ccbench/cc/cicada/include/common.hh").read_text()
    ycsb = (C.ROOT / "external/ccbench/include/ycsb.hh").read_text()
    import re
    stock = set(re.findall(r"DEFINE_\w+\(\s*(\w+),", common + ycsb))
    for point in C.POINTS:
        perf, diag = (C.flags(point, "S", k, 10, 3) for k in ("perf", "diag"))
        assert set(perf) - stock == {"izanagi_long_kind"}
        assert set(diag) - set(perf) == {"izanagi_ronly_pct", "izanagi_vlife_schema"}
        assert diag["izanagi_ronly_pct"] == -1 and diag["izanagi_vlife_schema"] == 3
        assert perf["worker1_insert_delay_rphase_us"] == 0
        assert perf["tuple_num"] == perf["ycsb_tuple_num"] == 1_000_000
        assert perf["ycsb_rratio"] == perf["rratio"] == C.POINTS[point]["rr"]
        assert perf["batch_max_ope"] == C.POINTS[point]["ops"]
    patch = V.PATCH.read_text()
    assert '+#if IZANAGI_CICADA_LONGTX\n+DEFINE_int32(izanagi_long_kind' in patch
    assert "DEFINE_int32(izanagi_ronly_pct" in patch


def test_real_condition_requests_and_materializer_identity():
    for macro in C.macros("diag", "R"):
        request = C.define_request(macro)
        spec, *_ = gate._validate_define_request(request)
        assert request.driver_id == C.DRIVER_ID
        assert request.requested_value == 1 and request.default_value == 0
        assert spec.target == "ycsb_cicada.exe"
        assert gate.declare_define_runtime_meaning(request)
    with pytest.raises(gate.ConditionMeaningGateError):
        C.define_request("IZANAGI_UNREGISTERED")
    assert non_admissible_materializer(C.MATERIALIZER)["materializer"] == C.DRIVER_ID + "._build_variant"
    assert non_admissible_materializer(C.MATERIALIZER)["admission_status"] == "non-admissible"


def test_smoke_grid_and_estimate_use_actual_run_counts():
    assert len(C.POINTS) == 27
    for skew in (0, .3, .6):
        plan = C.smoke_plan(skew)
        assert len(plan) == 26
        assert sum(p[2] == "diag" for p in plan) == 24
        assert sum(p[1].endswith("-noLT") for p in plan) == 6
        assert {p[4] for p in plan if p[2] == "perf"} == {1}
        assert {p[4] for p in plan if p[2] == "diag"} == {3}
        assert all(p[3] == 10 and p[5] == 1 for p in plan)
    assert C.job_estimate(42, 5, 10, 2)["estimated_s"] == 282
    assert C.job_estimate(42, 3, 3, 2)["estimated_s"] == 102


def test_empty_dispatch_environment_has_scratch_fallback():
    with mock.patch.dict("os.environ", {}, clear=True):
        with C.scratch_directory() as td:
            assert Path(td).is_dir()
            assert Path(td).parent == Path(tempfile.gettempdir())
        assert not Path(td).exists()


def test_patches_compose_strictly_in_declared_order():
    with tempfile.TemporaryDirectory() as td:
        source = Path(td)
        for rel in ("cc/cicada/transaction.cc", "cc/cicada/include/transaction.hh"):
            dest = source / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((C.ROOT / "external/ccbench" / rel).read_bytes())
        C.apply_patch(str(V.PATCH), str(source))
        C.apply_patch(str(C.R_PATCH), str(source))
        text = (source / "cc/cicada/transaction.cc").read_text()
        assert "#if IZANAGI_CICADA_LONGTX" in text and "#if IZANAGI_CICADA_RO_GCFLAG" in text
        # Applying the same instrument again must fail, rather than guessing/fuzzing.
        with pytest.raises(RuntimeError):
            C.apply_patch(str(V.PATCH), str(source))


def test_actual_ccbench_throughput_shape_and_rejections():
    source = (C.ROOT / "external/ccbench/common/result.cc").read_text()
    assert '"throughput[tps]:\\t" << result' in source
    assert C.parse_throughput("commit_counts_:\t100\nbatch_commit_counts_:\t2\n"
                              "throughput[tps]:\t34\nthroughput[ops]:\t800\n") == 34
    for text in ("", "throughput[tps]:\t-1\n", "throughput[tps]:\tnan\n",
                 "throughput[tps]:\t2\nthroughput[tps]:\t3\n"):
        with pytest.raises(ValueError):
            C.parse_throughput(text)


def test_real_schema3_summary_weighted_boundary_and_chains():
    row = _diag()
    summary = C.summarize_run(row)
    assert summary["gc_boundary_mean_us"] == 1250  # (3*1000 + 1*2000)/4
    assert summary["gc_boundary_p50_bucket_us"] == 1024
    assert summary["gc_publications"] == 4
    assert summary["logical_live_versions"] == 1_000_030
    assert summary["hot_chain_max"] == 8 and summary["hot_chain_median"] == 4.5
    assert "throughput_tps" not in summary
    with pytest.raises(ValueError):
        C.summarize_run({**row, "stdout": row["stdout"] + "\n" + row["stdout"]})
    assert C.summarize_run({**row, "rc": 1}) == {"rc": 1, "valid": False}
    assert C.summarize_run({**row, "rc": None})["valid"] is False


def test_remaining_establishment_boundaries_and_empty_observations():
    control = dict(valid=True, gc_boundary_mean_us=100)
    assert not C.established(_eligible(commits=99), control)
    assert not C.established(_eligible(age=999), control)
    assert not C.established(_eligible(rate=None), control)
    assert not C.established(_eligible(), dict(valid=True, gc_boundary_mean_us=None))
    assert not C.established({**_eligible(), "valid": False}, control)


def _perf(point=POINT, arm="R", gc=10, round_no=1, tps=10):
    return dict(point=point, arm=arm, kind="perf", gc=gc, extime=10, round=round_no,
                flags=C.flags(point, arm, "perf", gc, 10), rc=0,
                macros=list(C.macros("perf", arm)), stdout=f"throughput[tps]:\t{tps}\n",
                hostname="nodeA", job_started_at=f"2026-10-01T00:{gc:02}:00+00:00")


def test_measure_medians_pair_within_round_and_select_gc():
    rows = []
    for gc in (10, 100):
        for r, s, ratio in ((1, 100, 1), (2, 10, 2), (3, 1, 1000)):
            for arm, tps in zip(C.ARMS, (s, s * ratio, 2 * s, 2 * s * ratio)):
                rows.append(_perf(arm=arm, gc=gc, round_no=r, tps=tps * (2 if gc == 100 else 1)))
    doc = dict(command="measure", schema_version=1, runs=rows)
    diagnostic = dict(command="measure", schema_version=1, runs=[_diag(arm=a) for a in C.ARMS])
    result = C.aggregate([doc, diagnostic], "measure")
    pair = next(p for p in result["paired_ratios"]
                if p["kind"] == "perf" and p["gc"] == 10 and p["ratio"] == "R/S")
    assert pair["metrics"]["throughput_tps"] == 2  # ratio of medians would be 100/10
    assert result["main_gc"] == {POINT: 100}
    diag_median = next(m for m in result["medians"] if m["kind"] == "diag" and m["arm"] == "R")
    assert diag_median["metrics"]["gc_boundary_mean_us"] == 1250
    assert result["thresholds"] == dict(completion_rate=.10, long_commits=100, boundary_ratio=4, boundary_us=1000)
    with pytest.raises(ValueError):
        C.aggregate([{**doc, "runs": rows + [rows[0]]}], "measure")
    with pytest.raises(ValueError):
        C.aggregate([{**doc, "runs": rows[1:]}], "measure")
    broken = copy.deepcopy(rows)
    broken[0]["hostname"] = "other-node"
    with pytest.raises(ValueError):
        C.aggregate([{**doc, "runs": broken}], "measure")


def test_smoke_aggregation_records_all_points_and_stops_without_candidates():
    rows = [_diag(), _diag(arm="R-noLT", age=100)]
    doc = dict(command="smoke", schema_version=1, runs=rows)
    result = C.aggregate([doc], "smoke")
    assert len(result["grid"]) == 27 and result["established_count"] == 1
    assert result["selected"] == {"A": POINT, "B": None}
    assert not result["measure_allowed"]  # missing two skew jobs and other runs
    doc["runs"][0] = _diag(commits=99)
    result = C.aggregate([doc], "smoke")
    assert result["selected"] == {"A": None, "B": None}
    with pytest.raises(ValueError):
        C.aggregate([doc, doc], "smoke")


def test_full_smoke_selection_requires_perf_liveness_success():
    documents = []
    for skew in (0, .3, .6):
        rows = []
        for point, arm, kind, gc, extime, _ in C.smoke_plan(skew):
            if kind == "diag":
                row = _diag(point, arm, age=100 if arm.endswith("-noLT") else 1000)
            else:
                row = _perf(point, arm)
                row.update(extime=extime, flags=C.flags(point, arm, kind, gc, extime))
            rows.append(row)
        documents.append(dict(command="smoke", schema_version=1, runs=rows))
    result = C.aggregate(documents, "smoke")
    assert result["grid_complete"] and result["measure_allowed"]
    assert result["established_count"] == 27
    documents[0]["runs"][-1]["rc"] = 1
    assert not C.aggregate(documents, "smoke")["measure_allowed"]


def test_import_preserves_vlife_acceptance_and_outputs():
    before = copy.deepcopy(V.CONDITIONS), V.MACROS, V._flags("A-none-gc10", 1000, 2100)
    functions = (V.main, V._smoke_records, V.parse_vlife_line, V._run)
    importlib.reload(C)
    assert before == (V.CONDITIONS, V.MACROS, V._flags("A-none-gc10", 1000, 2100))
    assert functions == (V.main, V._smoke_records, V.parse_vlife_line, V._run)


def test_run_metadata_and_real_parse_without_compute():
    from datetime import datetime
    import hashlib
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        binary = root / "binary"
        binary.write_bytes(b"metadata fixture; never executed")
        for kind, extime in (("diag", 3), ("perf", 10)):
            stdout = _diag()["stdout"] if kind == "diag" else "throughput[tps]:\t123\n"
            # Only process execution is replaced; summarize_run uses the real parser/echo check.
            with mock.patch.object(V, "_run", return_value=dict(rc=0, stdout=stdout,
                                    argv=[str(binary)], parse_error=None)) as launch:
                row = C._run_one(binary, (POINT, "R", kind, 10, extime, 1), root, "job-start", 0)
            assert launch.call_args.kwargs == dict(cwd=root, instrumented=kind == "diag",
                                                  genome="tuned", val_size=4)
            assert row["binary_sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
            assert row["hostname"] and datetime.fromisoformat(row["started_at"]).utcoffset().total_seconds() == 0
            assert row["argv"] == [str(binary)] and row["rc"] == 0 and row["summary"]["valid"]


def test_cli_aggregate_needs_no_compute_and_preserves_output():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source, output = root / "smoke.json", root / "summary.json"
        source.write_text(json.dumps(dict(command="smoke", schema_version=1, runs=[])))
        with mock.patch.dict("os.environ", {}, clear=True):
            assert C.main(["aggregate", "--smoke", str(source), "--out", str(output)]) == 0
        assert not json.loads(output.read_text())["measure_allowed"]
        with pytest.raises(FileExistsError):
            C.main(["aggregate", "--smoke", str(source), "--out", str(output)])


if __name__ == "__main__":
    # Keep direct invocation useful and routed through the repository runner.
    from tools.run_tests import main as _run
    raise SystemExit(_run([str(Path(__file__).resolve())]))
