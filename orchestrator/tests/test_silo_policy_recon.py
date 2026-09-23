"""Fixed reconnaissance schedule, real policy entry, and raw-rep aggregation."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from orchestrator.campaign import silo_policy_recon as R
from orchestrator.campaign import silo_policy_coverage as C
from orchestrator.campaign import silo_policy_ir as IR
from orchestrator.campaign.silo_policy_grammar import validate_policy
from orchestrator.campaign.silo_policy_compile import compile_policy
from test_silo_function_policy_template import _cxx, _git


@contextmanager
def _checkout(pin_commit, base_dir):
    with tempfile.TemporaryDirectory(prefix="policy-recon-source-") as tmp:
        source = Path(tmp) / "ccbench"
        subprocess.run(["git", "clone", "--shared", "--no-checkout", base_dir, str(source)],
                       check=True, capture_output=True)
        _git(source, "checkout", "--detach", pin_commit)
        yield str(source)


def test_body_entry_real_four_gates_before_build(tmp_path):
    body = IR.render_policy(IR.enumerate_recon()[0].ir)
    bad = body.replace("return 5u;", "return true;", 1)
    assert validate_policy(bad).accepted is False
    assert compile_policy(bad, compiler=_cxx(), scratch_dir=str(tmp_path)).accepted is True
    builds = []
    with patch.object(C, "checkout", _checkout), \
         patch.object(C, "_build_variant", side_effect=lambda *a, **k: builds.append(k)):
        with C._source("0000", body=body, compiler=_cxx(), scratch=tmp_path) as (_, contract):
            assert contract["stages"] == ("quarantine", "effects", "grammar", "compile")
            assert contract["checked_sha256"] == C.sha(body)
        with pytest.raises(ValueError, match="grammar/compile rejected"):
            with C._source("0000", body=bad, compiler=_cxx(), scratch=tmp_path):
                C._build_variant(None, None, trace=1, toolchain={}, dependencies={})
    assert builds == []
    with pytest.raises(ValueError, match="stock and body"):
        with C._source("stock", body=body, compiler=_cxx(), scratch=tmp_path):
            pass


def test_schedule_and_flags():
    seen = []
    for job in range(8):
        cases = R._cases("initial", job, None)
        assert [role for role, _, _ in cases[:2]] == ["ir", "ir"]
        assert cases[-1][:2] == ("abort0", "abort0")
        seen += [case_id for _, case_id, _ in cases[:2]]
        assert len(cases) == (4 if job in (0, 1) else 3)
    assert sorted(seen) == [c.case_id for c in IR.enumerate_recon()]
    assert [x[1] for x in R._cases("remeasure", None, "0101")] == ["abort0", "0101"]
    assert R.FLAGS == {"ycsb_tuple_num": "1000000", "thread_num": "48",
                       "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "false",
                       "ycsb_max_ope": "10", "extime": "3"}
    assert C.GENOME.flags[C.axis.FLAG] == 1
    assert C.locks.STOCK_G.flags["BACK_OFF"] == 1


def test_driver_verify_trace0_and_five_reps(tmp_path):
    @contextmanager
    def source(*args, **kwargs):
        yield tmp_path, {"accepted": True}

    evidence = SimpleNamespace(src_token="token", as_receipt=lambda: {"source": "same"})
    certified = {"certified": True, "verdict": "serializable", "exit_code": 0, "commits": 10}
    calls = []

    def build(source, path, **kwargs):
        calls.append(("build", kwargs["trace"], kwargs["stock"], kwargs["stock_backoff"]))
        return path / "binary", {"built": True}

    def run(binary, flags, **kwargs):
        calls.append(("run", kwargs["trace"]))
        if kwargs["trace"]:
            return dict(certified)
        return {"commits": 900, "aborts": 100, "throughput": 104.0}

    with patch.object(C, "_source", source), patch.object(C, "_build_variant", build), \
         patch.object(C, "_run", run), patch.object(C.source_digest, "resolve_evidence",
              return_value=evidence), patch.object(R, "_trace0", return_value={"clean": True}):
        row = R._one("ir", "0000", IR.enumerate_recon()[0], tmp_path / "a", {"cxx_path": "c++"}, {})
        assert row["status"] == "complete" and len(row["bench"]) == 5
        assert row["genome"]["flags"][C.axis.FLAG] == 1
        assert calls.count(("run", False)) == 5
        assert calls[:1] == [("build", 1, False, 1)]
        calls.clear()
        row = R._one("b0_l_w0", "B0-L-W0", None, tmp_path / "b", {"cxx_path": "c++"}, {})
        assert calls[0] == ("build", 1, True, 0)
        assert row["genome"]["flags"]["BACK_OFF"] == 0
        calls.clear()
        row = R._one("stock", "stock", None, tmp_path / "c", {"cxx_path": "c++"}, {})
        assert calls[0] == ("build", 1, True, 1)
        assert row["genome"]["flags"]["BACK_OFF"] == 1

    calls.clear()
    with patch.object(C, "_source", source), patch.object(C, "_build_variant", build), \
         patch.object(C, "_run", return_value={"certified": False}) as failed, \
         patch.object(C.source_digest, "resolve_evidence", return_value=evidence):
        row = R._one("ir", "0000", IR.enumerate_recon()[0], tmp_path / "d", {"cxx_path": "c++"}, {})
        assert row["status"] == "verify-not-certified" and row["bench"] == []
        assert failed.call_count == 2 and calls == [("build", 1, False, 1)]

    calls.clear()
    with patch.object(C, "_source", source), patch.object(C, "_build_variant", build), \
         patch.object(C, "_run", return_value=dict(certified)), \
         patch.object(C.source_digest, "resolve_evidence", return_value=evidence), \
         patch.object(R, "_trace0", return_value={"clean": False}):
        row = R._one("ir", "0000", IR.enumerate_recon()[0], tmp_path / "e", {"cxx_path": "c++"}, {})
        assert row["status"] == "trace0-not-clean" and row["bench"] == []


def test_build_variant_uses_only_fixed_genomes(tmp_path):
    configure = []

    def checked(argv, **kwargs):
        configure.append(argv)

    def built(argv, **kwargs):
        binary = Path(argv[2]) / "cc/silo/ycsb_silo.exe"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"binary")

    with patch.object(C.site_policy, "current_site", return_value="pegasus-compute"), \
         patch.object(C.site_policy, "refuses_heavy_work", return_value=False), \
         patch.object(C.compute, "_common_configure_args", return_value=[]), \
         patch.object(C, "_condition_gates", return_value=[{"admission": {"admitted": True}}]), \
         patch.object(C.compute, "_run_checked", side_effect=checked), \
         patch.object(C.locks, "_run_cmake_build", side_effect=built):
        for name, stock, backoff in (("stock", True, 1), ("b0", True, 0), ("ir", False, 1)):
            build = tmp_path / name
            C._build_variant(tmp_path, build, trace=1, toolchain={"cxx_path": "c++"},
                             dependencies={}, stock=stock, stock_backoff=backoff)
        with pytest.raises(ValueError, match="stock_backoff"):
            C._build_variant(tmp_path, tmp_path / "bad", trace=1,
                             toolchain={"cxx_path": "c++"}, dependencies={}, stock_backoff=0)
    assert "-DCCBENCH_BACK_OFF=1" in configure[0]
    assert "-DCCBENCH_BACK_OFF=0" in configure[1]
    assert all("-DCCBENCH_SILO_POLICY_VARIANT=1" not in command for command in configure[:2])
    assert "-DCCBENCH_SILO_POLICY_VARIANT=1" in configure[2]


def _row(role, case_id, *, throughput=104.0, rate=.1, complete=True):
    case = IR.enumerate_recon()[int(case_id, 2)] if role == "ir" else None
    body = IR.render_policy(case.ir) if case is not None else (
        IR.render_policy(IR.degenerate_policy()) if role == "abort0" else None)
    backoff = 0 if role == "b0_l_w0" else 1
    flags = {**C.locks._BASE, "BACK_OFF": backoff} if role in {"stock", "b0_l_w0"} else C.GENOME.flags
    commits = 900
    aborts = round(commits * rate / (1 - rate)) if rate < 1 else 900000
    actual_rate = aborts / (commits + aborts)
    return {"role": role, "case_id": case_id, "factors": list(case.factors) if case else None,
            "body_sha256": C.sha(body) if body else None,
            "genome": {"protocol": "silo", "flags": flags},
            "verify": {k: {"certified": True, "verdict": "serializable", "exit_code": 0,
                           "commits": 1} for k in ("legacy", "performance")},
            "trace0": {"clean": True}, "source_evidence": {"a": 1},
            "source_evidence_after": {"a": 1}, "status": "complete" if complete else "incomplete",
            "bench": [{"throughput": throughput, "commits": commits, "aborts": aborts,
                       "abort_rate": actual_rate} for _ in range(5)] if complete else []}


def _jobs(throughput=100.0, rate=.1):
    result = []
    for job in range(8):
        rows = [_row(role, cid, throughput=throughput if role == "abort0" else 100.0,
                     rate=rate) for role, cid, _ in R._cases("initial", job, None)]
        result.append({"schema_version": R.SCHEMA, "phase": "initial", "job": job,
                       "pbs_jobid": f"j{job}", "hostname": "host", "started_at": f"s{job}",
                       "pin": C.PIN, "toolchain": {"cxx": "g++"},
                       "workload": {"legacy": C.LEGACY, "performance": R.FLAGS,
                                    "bench_reps": 5, "numa": True},
                       "cases": rows})
    return result


def _aggregate(tmp_path, jobs, remeasure=()):
    initial = []
    for i, job in enumerate(jobs):
        path = tmp_path / f"i{i}.json"
        path.write_text(json.dumps(job))
        initial.append(path)
    rem = []
    for i, job in enumerate(remeasure):
        path = tmp_path / f"r{i}.json"
        path.write_text(json.dumps(job))
        rem.append(path)
    args = SimpleNamespace(initial=initial, remeasure=rem, out=tmp_path / "details.json",
                           projection_out=tmp_path / "projection.json")
    R.aggregate(args)
    return json.loads(args.out.read_text()), json.loads(args.projection_out.read_text())


def test_aggregate_exact_floor_and_no_candidate(tmp_path):
    jobs = _jobs()
    # Exactly 1.03 is not above the strict floor.
    jobs[0]["cases"][0]["bench"] = _row("ir", "0000", throughput=103)["bench"]
    detail, projection = _aggregate(tmp_path, jobs)
    assert detail["binary"] is False and detail["remeasure_candidates"] == []
    assert set(projection) == {"binary", "scope", "excluded"}
    assert "0000" not in json.dumps(projection)
    assert C.sha(IR.render_policy(IR.enumerate_recon()[0].ir)) not in json.dumps(projection)


def test_aggregate_remeasure_missing_same_job_and_reproduced(tmp_path):
    jobs = _jobs()
    jobs[0]["cases"][0]["bench"] = _row("ir", "0000", throughput=104)["bench"]
    detail, _ = _aggregate(tmp_path, jobs)
    assert detail["binary"] is None and detail["remeasure_candidates"] == ["0000"]
    rem = {**jobs[0], "phase": "remeasure", "job": "0000", "pbs_jobid": "new",
           "cases": [_row("abort0", "abort0", throughput=100),
                     _row("ir", "0000", throughput=104)]}
    assert _aggregate(tmp_path, jobs, [rem])[0]["binary"] is True
    rem["pbs_jobid"] = jobs[0]["pbs_jobid"]
    assert _aggregate(tmp_path, jobs, [rem])[0]["binary"] is None


def test_aggregate_hash_missing_zero_and_high_abort(tmp_path):
    jobs = _jobs()
    jobs[0]["cases"][0]["body_sha256"] = "bad"
    assert _aggregate(tmp_path, jobs)[0]["binary"] is None
    jobs = _jobs(rate=0)
    assert _aggregate(tmp_path, jobs)[0]["binary"] is None
    jobs = _jobs(rate=.1)
    jobs[0]["cases"][0] = _row("ir", "0000", throughput=104, rate=.21)
    assert _aggregate(tmp_path, jobs)[0]["binary"] is False
    jobs[0]["cases"][0] = _row("ir", "0000", throughput=104, rate=.2)
    assert _aggregate(tmp_path, jobs)[0]["binary"] is None  # candidate awaits remeasure


def test_aggregate_fixed_workload_and_controls_accept(tmp_path):
    jobs = _jobs()
    detail, projection = _aggregate(tmp_path, jobs)
    assert detail["binary"] is False and detail["errors"] == []
    assert projection["binary"] is False


@pytest.mark.parametrize("change,error", [
    ("workload", "workload"),
    ("abort0", "abort0 body sha256"),
    ("stock", "stock genome flags"),
    ("b0_l_w0", "b0_l_w0 genome flags"),
])
def test_aggregate_rejects_changed_initial_workload_or_control(tmp_path, change, error):
    jobs = _jobs()
    if change == "workload":
        for job in jobs:
            job["workload"]["bench_reps"] = 4
    elif change == "abort0":
        jobs[2]["cases"][-1]["body_sha256"] = "wrong"
    elif change == "stock":
        jobs[0]["cases"][2]["genome"]["flags"]["BACK_OFF"] = 0
    else:
        jobs[1]["cases"][2]["genome"]["flags"]["BACK_OFF"] = 1
    detail, projection = _aggregate(tmp_path, jobs)
    assert detail["binary"] is None and projection["binary"] is None
    assert any(error in message for message in detail["errors"])


def test_aggregate_fixed_remeasurement_workload_and_abort0_accept(tmp_path):
    jobs = _jobs()
    jobs[0]["cases"][0]["bench"] = _row("ir", "0000", throughput=104)["bench"]
    rem = {**jobs[0], "phase": "remeasure", "job": "0000", "pbs_jobid": "new",
           "cases": [_row("abort0", "abort0", throughput=100),
                     _row("ir", "0000", throughput=104)]}
    detail, projection = _aggregate(tmp_path, jobs, [rem])
    assert detail["binary"] is True and detail["errors"] == []
    assert projection["binary"] is True


@pytest.mark.parametrize("change,error", [
    ("workload", "workload"),
    ("abort0", "abort0 body sha256"),
])
def test_aggregate_rejects_changed_remeasurement_workload_or_abort0(tmp_path, change, error):
    jobs = _jobs()
    jobs[0]["cases"][0]["bench"] = _row("ir", "0000", throughput=104)["bench"]
    rem = {**jobs[0], "phase": "remeasure", "job": "0000", "pbs_jobid": "new",
           "cases": [_row("abort0", "abort0", throughput=100),
                     _row("ir", "0000", throughput=104)]}
    if change == "workload":
        rem["workload"] = {**rem["workload"], "numa": False}
    else:
        rem["cases"][0]["body_sha256"] = "wrong"
    detail, projection = _aggregate(tmp_path, jobs, [rem])
    assert detail["binary"] is None and projection["binary"] is None
    assert any(error in message for message in detail["errors"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
