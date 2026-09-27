"""T-2851 runner contract tests; binary and node execution are fixture-only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.campaign import t2851_transfer_runner as runner
from orchestrator.verifier.core import verify_trace_dir


def _record():
    refs = {a: {"R0": "R0", "R1": "R1", "R2": "R2"}
            for a in ("wh-base", "bal-base", "rh-base")}
    binaries = {k: {"perf_path": "/unused/" + k, "perf_sha256": "0" * 64,
                    "trace_path": "/unused/" + k, "trace_sha256": "0" * 64,
                    "trace_ccbench_root": str(Path(__file__).resolve().parents[2] / "external/ccbench")}
                for k in ("R0", "R1", "R2", "K")}
    return dict(workload="ycsb", selection_rule="frozen", binaries=binaries,
                environment={"env_tag": "fixture", "clocks_per_us": 1777,
                             "numactl": ["numactl", "--localalloc"]},
                references={"silo": refs},
                search_groups=[dict(task="t", method="m", learning_cells=["wh-base"],
                                    independent_searches=["1"], reachability=False)],
                series=[dict(task="t", method="m", independent_search="1",
                             protocol="silo", anchor="wh-base", selected_identity="K")])


def _freeze():
    return runner.freeze_candidates(_record())


def test_trace_source_root_required_absolute_and_frozen():
    record = _record()
    source_root = record["binaries"]["K"]["trace_ccbench_root"]
    original = runner.freeze_candidates(record)
    for invalid in (None, "relative/ccbench"):
        record["binaries"]["K"]["trace_ccbench_root"] = invalid
        with pytest.raises(ValueError, match="incomplete binary pair"):
            runner.freeze_candidates(record)
    record["binaries"]["K"]["trace_ccbench_root"] = "/missing-ccbench"
    changed = runner.freeze_candidates(record)
    assert changed["sha256"] != original["sha256"]
    changed["binaries"]["K"]["trace_ccbench_root"] = source_root
    with pytest.raises(ValueError, match="freeze sha256 mismatch"):
        runner._require_freeze_hash(changed)


def test_cells_and_known_separate():
    y = runner.cells("ycsb")
    assert len(y) == 26 and sum(c.held_out for c in y) == 23
    assert len(runner.cells("tpcc", "s1")) == 12
    assert len(runner.cells("tpcc", "s2")) == 12
    assert runner.known_separate("silo", "bal-rmw1")
    assert not runner.known_separate("mocc", "bal-rmw1")
    assert not runner.known_separate("silo", "wh-rmw1")
    assert next(c for c in y if c.name == "wh-rr25").flags["ycsb_rratio"] == "25"
    assert next(c for c in y if c.name == "wh-base").flags["ycsb_rmw"] == "false"
    assert next(c for c in y if c.name == "wh-rmw1").flags["ycsb_rmw"] == "true"
    assert next(c for c in runner.cells("tpcc", "s2") if c.name == "s2-L-scan10").flags["tpcc_perc_delivery"] == "10"


def test_order_hand_calculated_and_prefix():
    names = ["c", "a", "b"]
    actual = runner.order_identities(names, workload="ycsb", stage=None,
                                     cohort=1, protocol="silo", cell="wh-base", block=1)
    assert actual == ("b", "a", "c")
    assert runner.order_identities(names, workload="ycsb", stage=None, cohort=1,
                                   protocol="silo", cell="wh-bbse", block=1) == ("c", "a", "b")
    assert any(actual != runner.order_identities(names, workload="ycsb", stage=None,
               cohort=1, protocol="silo", cell="wh-base", block=b) for b in range(2, 33))
    assert runner.order_identities(names, workload="tpcc", stage="s1", cohort=1,
                                   protocol="silo", cell="wh-base", block=1) != actual


def test_freeze_m_and_same_identity():
    frozen = _freeze()
    assert frozen["m_by_family"] == {"ycsb": 18}  # wh: 9 cells, 2 strong refs
    assert len(frozen["jobs"]) == 2 * 26
    assert frozen["sha256"] == runner._sha({k: frozen[k] for k in
        ("workload", "stage", "series", "search_groups", "selection_rule", "references", "binaries", "environment")})
    changed = _record()
    changed["series"][0]["selected_identity"] = "R1"
    same = runner.freeze_candidates(changed)
    assert any(x["same_identity"] for x in same["comparisons"])
    assert same["m_by_family"]["ycsb"] == 9
    assert all(x["kind"] == "descriptive" for x in frozen["comparisons"]
               if x["reference"] == "R0")


@pytest.mark.parametrize("change", ["missing", "duplicate", "exclusive", "unknown", "learning", "reference"])
def test_freeze_rejects_invalid(change):
    rec = _record()
    if change == "missing":
        rec["series"] = []
    elif change == "duplicate":
        rec["series"].append(dict(rec["series"][0]))
    elif change == "exclusive":
        rec["series"][0]["selection_failure"] = "failed"
    elif change == "unknown":
        rec["series"][0]["selected_identity"] = "absent"
    elif change == "learning":
        rec["search_groups"][0]["learning_cells"] = ["wh-rr25"]
    else:
        rec["references"]["silo"]["wh-base"]["R1"] = "absent"
    with pytest.raises(ValueError):
        runner.freeze_candidates(rec)


def test_environment_required_and_bound_to_hash():
    record = _record()
    del record["environment"]
    with pytest.raises(ValueError, match="^environment invalid$"):
        runner.freeze_candidates(record)
    record["environment"] = {"env_tag": "fixture", "clocks_per_us": 0,
                             "numactl": []}
    with pytest.raises(ValueError, match="^environment invalid$"):
        runner.freeze_candidates(record)
    frozen = _freeze()
    frozen["environment"]["clocks_per_us"] += 1
    with pytest.raises(ValueError, match="^freeze sha256 mismatch$"):
        runner.run_job(dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base"))


@pytest.mark.parametrize("field", ["jobs", "comparisons", "m_by_family"])
def test_mutated_derived_freeze_rejected_before_execution(field, monkeypatch):
    frozen = copy.deepcopy(_freeze())
    if field == "jobs":
        frozen["jobs"][0]["identities"] = ["R0"]
    elif field == "comparisons":
        frozen["comparisons"][0]["kind"] = "primary"
    else:
        frozen["m_by_family"]["ycsb"] += 1
    def forbidden(*args, **kwargs):
        raise AssertionError("execution reached")
    monkeypatch.setattr(runner.calibrator, "run_once", forbidden)
    with pytest.raises(ValueError, match="^freeze sha256 mismatch$"):
        runner.run_job(dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base"))
    with pytest.raises(ValueError, match="^freeze sha256 mismatch$"):
        runner.verify_candidate(dict(freeze=frozen, protocol="silo", cell="wh-base",
                                     identity="K"), trace_runner=forbidden)


def test_cohort_one_complete_keys_and_mixed_utc_max(monkeypatch):
    frozen = _freeze()
    records = [dict(stage=j["stage"], cohort=1, protocol=j["protocol"], cell=j["cell"],
                    hostname="old-node", end_utc="2026-01-01T00:00:00Z",
                    completed_blocks=32, isolation_start=True, isolation_end=True,
                    within_retry_limit=True, next_action="none")
               for j in frozen["jobs"] if j["cohort"] == 1]
    records[0]["end_utc"] = "2026-01-01T00:00:00.500000+00:00"
    monkeypatch.setattr(runner, "_utc", lambda: "2026-01-02T00:00:00Z")
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "new-node")
    spec = dict(freeze=frozen, cohort=2, protocol="silo", cell="wh-base")
    with pytest.raises(ValueError, match="^cohort1_records incomplete$"):
        runner.run_job(spec | {"cohort1_records": records[1:]})
    def forbidden(*args, **kwargs):
        raise AssertionError("measurement reached")
    monkeypatch.setattr(runner.calibrator, "run_once", forbidden)
    result = runner.run_job(spec | {"cohort1_records": records})
    assert result["next_action"] == "wait-24h" and result["completed_blocks"] == 0
    assert result["environment"] == frozen["environment"]
    monkeypatch.setattr(runner, "_utc", lambda: "2026-01-02T00:00:00.500000Z")
    monkeypatch.setattr(runner, "_probe", lambda *args, **kwargs: False)
    ontime = runner.run_job(spec | {"cohort1_records": records})
    assert ontime["next_action"] == "resubmit-isolation"


def test_activation_rejects_before_measurement(monkeypatch):
    frozen = _freeze()
    spec = dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-rr25")
    def forbidden(*a, **kw):
        raise AssertionError("measurement reached")
    monkeypatch.setattr(runner.calibrator, "run_once", forbidden)
    with pytest.raises(ValueError, match="activation"):
        runner.run_job(spec)
    with pytest.raises(ValueError, match="activation"):
        runner.verify_candidate(dict(spec, identity="K"))
    activation = {"decision_id": "D", "freeze_sha256": frozen["sha256"]}
    assert runner.activation_allowed(runner._find_cell(frozen, "wh-rr25"), frozen, activation)
    assert not runner.activation_allowed(runner._find_cell(frozen, "wh-rr25"), frozen,
                                         activation | {"freeze_sha256": "wrong"})
    assert runner.activation_allowed(runner._find_cell(frozen, "wh-base"), frozen, None)
    tpcc = {"sha256": "h"}
    cell = runner._find_cell({"workload": "tpcc", "stage": "s1"}, "s1-H-wh04")
    assert not runner.activation_allowed(cell, tpcc, {"decision_id": "D", "freeze_sha256": "h"})
    assert runner.activation_allowed(cell, tpcc, {"decision_id": "D", "freeze_sha256": "h",
                                                 "stage": "s1", "certification_path": "path"})


def test_cohort_two_boundary_and_rejections():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    args = dict(cohort1_last_end_utc=t.isoformat(), prior_hostname="A", current_hostname="A")
    for count in (0, 1):
        gate = runner.cohort2_admission(**args, same_host_rejections=count,
                                        cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
        assert gate["next_action"] == "resubmit-same-host" and not gate["measure"]
    third = runner.cohort2_admission(**args, same_host_rejections=2,
                                     cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
    assert third["measure"] and not third["separate_allocation"]
    early = runner.cohort2_admission(**(args | {"current_hostname": "B"}), same_host_rejections=0,
                                     cohort2_first_start_utc=(t + timedelta(hours=24, seconds=-1)).isoformat())
    assert early["next_action"] == "wait-24h" and not early["measure"]
    ontime = runner.cohort2_admission(**(args | {"current_hostname": "B"}), same_host_rejections=0,
                                      cohort2_first_start_utc=(t + timedelta(hours=24)).isoformat())
    assert ontime["measure"] and ontime["separate_allocation"]


def test_isolation_retry_once(monkeypatch):
    frozen = _freeze()
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: False)
    spec = dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base")
    first = runner.run_job(spec)
    assert first["next_action"] == "resubmit-isolation" and first["completed_blocks"] == 0
    second = runner.run_job(spec | {"attempt_history": [first]})
    assert second["next_action"] == "retry-exhausted"
    with pytest.raises(ValueError, match="retry limit"):
        runner.run_job(spec | {"attempt_history": [first, second]})


def test_job_failure_retry_once(tmp_path, monkeypatch):
    binary = tmp_path / "binary"
    binary.write_bytes(b"fake")
    record = _record()
    for pair in record["binaries"].values():
        pair.update(perf_path=str(binary), perf_sha256=hashlib.sha256(b"fake").hexdigest())
    frozen = runner.freeze_candidates(record)
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: True)
    def failed_process(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="failed")
    spec = dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base")
    first = runner.run_job(spec, subprocess_runner=failed_process)
    assert first["next_action"] == "resubmit-job-failure" and first["attempt"] == 1
    second = runner.run_job(spec | {"attempt_history": [first]}, subprocess_runner=failed_process)
    assert second["next_action"] == "retry-exhausted" and second["attempt"] == 2
    with pytest.raises(ValueError, match="retry limit"):
        runner.run_job(spec | {"attempt_history": [first, second]}, subprocess_runner=failed_process)


def test_verification_mapping():
    base = dict(completed=True, serializable=True, anomalies=0,
                witness_ok=True, certified=True)
    assert runner.verification_status(**base) == "certified"
    for change in (dict(completed=False), dict(witness_ok=False),
                   dict(certified=False), dict(serializable=None)):
        assert runner.verification_status(**(base | change)) == "indeterminate"
    assert runner.verification_status(**(base | {"anomalies": 1})) == "disqualified"
    assert runner.verification_status(**(base | {"serializable": False})) == "disqualified"


def test_verification_mapping_with_real_verifier_fixtures():
    fixtures = Path(__file__).parent / "fixtures"
    red = verify_trace_dir(str(fixtures / "r1_write_skew"), max_report=0)
    assert runner.verification_status(completed=True, serializable=red.serializable,
           anomalies=max(len(red.anomalies), red.total_cycles), witness_ok=True,
           certified=red.certified) == "disqualified"
    green_graph = verify_trace_dir(str(fixtures / "g1_serial"))
    assert green_graph.serializable and not green_graph.certified
    assert runner.verification_status(completed=True, serializable=green_graph.serializable,
           anomalies=max(len(green_graph.anomalies), green_graph.total_cycles),
           witness_ok=True, certified=green_graph.certified) == "indeterminate"


def test_verify_candidate_real_verifier_source_root_controls_certification(tmp_path):
    binary = tmp_path / "trace-binary"
    binary.write_bytes(b"fixture")
    source_root = Path(__file__).resolve().parents[2] / "external/ccbench"
    fixture = Path(__file__).parent / "fixtures/g1_serial/trace_0.log"
    assert source_root.is_dir() and fixture.is_file()
    def trace_runner(_binary, trace_dir, _flags, _clocks, **_kwargs):
        (Path(trace_dir) / "trace_0.log").write_bytes(fixture.read_bytes())
        return SimpleNamespace(returncode=0, trace_c_lines=2, abort_counts={},
                               commit_count_witness=2, batch_commit_count_witness=0)
    record = _record()
    record["binaries"]["K"].update(trace_path=str(binary),
        trace_sha256=hashlib.sha256(b"fixture").hexdigest())
    outcomes = []
    for root in (source_root, tmp_path / "missing-ccbench"):
        record["binaries"]["K"]["trace_ccbench_root"] = str(root)
        frozen = runner.freeze_candidates(record)
        assert frozen["binaries"]["K"]["trace_ccbench_root"] == str(root)
        checked = runner.verify_candidate(dict(freeze=frozen, protocol="silo",
                                                cell="wh-base", identity="K"),
                                          trace_runner=trace_runner)
        assert checked["trace_ccbench_root"] == str(root)
        assert checked["attempt"] == 1 and checked["anomalies"] == 0
        outcomes.append(checked)
    assert outcomes[0]["status"] == "certified" and outcomes[0]["reason"] == "serializable"
    assert outcomes[0]["verifier"]["certified"] is True
    assert outcomes[1]["status"] == "indeterminate" and outcomes[1]["reason"] == "indeterminate"
    assert outcomes[1]["verifier"]["certified"] is False


def test_tpcc_parser_from_result_cc_shape():
    stdout = "  Transaction type: Payment\n    commits: 8\n    aborts: 2\n  Transaction type: NewOrder\n    commits: 7\n    aborts: 0\n"
    assert runner.parse_tpcc_counts(stdout) == {"Payment": {"commits": 8, "aborts": 2},
                                                "NewOrder": {"commits": 7, "aborts": 0}}
    assert runner.parse_tpcc_counts(stdout.replace("    aborts: 2\n", "")) is None
    assert runner.parse_tpcc_counts(stdout + "  Transaction type: Payment\n") is None


def test_run_job_anchor_uses_real_run_once_with_subprocess_seam(tmp_path, monkeypatch):
    binary = tmp_path / "binary"
    binary.write_bytes(b"fake")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    record = _record()
    for pair in record["binaries"].values():
        pair.update(perf_path=str(binary), perf_sha256=digest)
    frozen = runner.freeze_candidates(record)
    calls = []
    def subprocess_runner(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="throughput[tps]:\t100\n", stderr="")
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: True)
    result = runner.run_job(dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base"),
                            subprocess_runner=subprocess_runner)
    assert result["completed_blocks"] == 32
    assert len(calls) == 1 + 32 * 4
    assert all("perf" not in str(cmd[0]) for cmd in calls)
    assert all("-clocks_per_us=1777" in cmd for cmd in calls)
    assert all(cmd[:2] == ["numactl", "--localalloc"] for cmd in calls)
    assert result["environment"] == frozen["environment"]
    assert result["blocks"][0]["runs"]["K"]["tps"] == 100


def _tpcc_record(stage="s1"):
    anchor = stage + "-H-base"
    return dict(workload="tpcc", stage=stage, selection_rule="frozen",
                  environment={"env_tag": "fixture", "clocks_per_us": 1777, "numactl": []},
                  series=[dict(task="t", method="m", independent_search="1",
                               protocol="silo", anchor=anchor, selected_identity="K")],
                  search_groups=[dict(task="t", method="m", learning_cells=[anchor],
                                      independent_searches=["1"], reachability=False)],
                  references={"silo": {"mode": "a", "R0": "R0", "reference_identity": "K"}},
                  binaries={k: dict(perf_path="/unused", perf_sha256="0" * 64,
                                    trace_path="/unused", trace_sha256="0" * 64,
                                    trace_ccbench_root=str(Path(__file__).resolve().parents[2] / "external/ccbench"))
                           for k in ("R0", "K")})


@pytest.mark.parametrize("stage,cell", [("s2", "s2-H-base"),
                                        ("s1", "s1-H-pay20")])
def test_verify_tpcc_anchor_is_indeterminate(stage, cell):
    frozen = runner.freeze_candidates(_tpcc_record(stage))
    spec = dict(freeze=frozen, protocol="silo", cell=cell, identity="K")
    if cell.endswith("pay20"):
        spec["activation"] = {"decision_id": "fixture", "freeze_sha256": frozen["sha256"],
                              "stage": stage, "certification_path": "fixture"}
    def forbidden(*args, **kwargs):
        raise AssertionError("trace runner reached")
    result = runner.verify_candidate(spec, trace_runner=forbidden)
    assert result["status"] == "indeterminate" and result["reason"] == "認定経路なし"
    assert result["attempt"] is None
    repeated = runner.verify_candidate(spec | {"attempt_history": [result]},
                                       trace_runner=forbidden)
    assert repeated["status"] == "indeterminate" and repeated["reason"] == "認定経路なし"
    assert repeated["attempt"] is None


def test_verify_tpcc_s1_real_verifier_v3_v2_and_witness(tmp_path):
    binary = tmp_path / "trace-binary"
    binary.write_bytes(b"fixture")
    source_root = Path(__file__).resolve().parents[2] / "external/ccbench"
    first = "C 0 0 2 1 0 1 0 0 1\nW 0 1 aa I 2 1\nE 0\n"
    second = "C 1 0 2 2 1 0 0 0 2\nR 1 1 aa 2 1\nE 1\n"
    v2 = "C 0 0 2 1 0 1\nW 0 aa U 2 1\nE 0\n"
    record = _tpcc_record()
    record["binaries"]["K"].update(trace_path=str(binary),
        trace_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    wrong_root = tmp_path / "wrong-ccbench"
    wrong_root.mkdir()
    cases = [("v3", (first, second), 2, source_root, True),
             ("missing-root", (first, second), 2, tmp_path / "missing", True),
             ("wrong-root", (first, second), 2, wrong_root, True),
             ("v2", (v2,), 1, source_root, True),
             ("v2-anomaly", (Path(__file__).parent / "fixtures/r1_write_skew/trace_0.log",),
              2, source_root, True),
             ("witness", (first, second), 2, source_root, False)]
    for name, frames, count, root, witness in cases:
        record["binaries"]["K"]["trace_ccbench_root"] = str(root)
        frozen = runner.freeze_candidates(record)
        def trace_runner(_binary, trace_dir, flags, _clocks, **_kwargs):
            assert flags["tpcc_perc_payment"] == "43"
            for index, frame in enumerate(frames):
                data = frame.read_text() if isinstance(frame, Path) else frame
                (Path(trace_dir) / f"trace_{index}.log").write_text(data)
            return SimpleNamespace(returncode=0, trace_c_lines=count,
                abort_counts={}, commit_count_witness=count,
                batch_commit_count_witness=0 if witness else 1)
        result = runner.verify_candidate(dict(freeze=frozen, protocol="silo",
            cell="s1-H-base", identity="K"), trace_runner=trace_runner)
        if name == "v3":
            assert result["status"] == "certified" and result["verifier"]["certified"]
            assert result["verifier"]["integrity"]["existence_violation_details"] == []
        elif name == "v2-anomaly":
            assert result["status"] == "disqualified"
        else:
            assert result["status"] == "indeterminate", (name, result)
            if name == "v2":
                assert result["reason"] == "trace-witness-unsupported-workload"
            if name == "witness":
                assert result["reason"] == "trace-witness-failed" and result["verifier"] is None


def test_ycsb_reverification_counts_only_trace_runs(monkeypatch, tmp_path):
    binary = tmp_path / "trace"
    binary.write_bytes(b"fake")
    record = _record()
    record["binaries"]["K"].update(trace_path=str(binary),
        trace_sha256=hashlib.sha256(b"fake").hexdigest())
    frozen = runner.freeze_candidates(record)
    spec = dict(freeze=frozen, protocol="silo", cell="wh-base", identity="K")
    trace_calls = []
    def trace_runner(*args, **kwargs):
        trace_calls.append(args)
        return SimpleNamespace(returncode=1, trace_c_lines=0, abort_counts=None,
            commit_count_witness=None, batch_commit_count_witness=None)
    def verifier(*args, **kwargs):
        raise AssertionError("witness failure reached verifier")
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "node-A")
    first = runner.verify_candidate(spec, trace_runner=trace_runner, verifier=verifier)
    assert first["status"] == "indeterminate" and first["attempt"] == 1
    same = runner.verify_candidate(spec | {"attempt_history": [first]},
        trace_runner=trace_runner, verifier=verifier)
    assert same["reason"] == "reverification-not-admitted" and same["attempt"] is None
    assert len(trace_calls) == 1
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "node-B")
    second = runner.verify_candidate(spec | {"attempt_history": [first, same]},
        trace_runner=trace_runner, verifier=verifier)
    assert second["status"] == "indeterminate" and second["attempt"] == 2
    assert len(trace_calls) == 2
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "node-C")
    exhausted = runner.verify_candidate(spec | {"attempt_history": [first, same, second]},
        trace_runner=trace_runner, verifier=verifier)
    assert exhausted["reason"] == "reverification-limit" and exhausted["attempt"] is None
    assert len(trace_calls) == 2


def test_trace_environment_and_prelaunch_failure(tmp_path, monkeypatch):
    binary = tmp_path / "trace"
    binary.write_bytes(b"fake")
    record = _record()
    record["binaries"]["K"].update(trace_path=str(binary),
        trace_sha256=hashlib.sha256(b"fake").hexdigest())
    frozen = runner.freeze_candidates(record)
    spec = dict(freeze=frozen, protocol="silo", cell="wh-base", identity="K")
    def fail_dir(*args, **kwargs):
        raise OSError("fixture directory failure")
    original = runner.tempfile.TemporaryDirectory
    monkeypatch.setattr(runner.tempfile, "TemporaryDirectory", fail_dir)
    failed = runner.verify_candidate(spec)
    assert failed["status"] == "indeterminate" and failed["attempt"] is None
    assert failed["reason"] == "OSError: fixture directory failure"
    monkeypatch.setattr(runner.tempfile, "TemporaryDirectory", original)
    seen = []
    def trace(binary_path, trace_dir, flags, clocks_per_us, **kwargs):
        seen.append((clocks_per_us, kwargs["numactl"]))
        return SimpleNamespace(returncode=1, trace_c_lines=0, abort_counts=None,
                               commit_count_witness=None, batch_commit_count_witness=None)
    observed = runner.verify_candidate(spec | {"attempt_history": [failed]},
                                       trace_runner=trace)
    assert observed["attempt"] == 1 and seen == [(1777, ["numactl", "--localalloc"])]
    assert observed["environment"] == frozen["environment"]


@pytest.mark.parametrize("change", ["rc", "empty", "abort", "commit", "batch"])
def test_trace_witness_each_missing_condition_is_indeterminate(change, tmp_path):
    binary = tmp_path / "trace"
    binary.write_bytes(b"fake")
    record = _record()
    record["binaries"]["K"].update(trace_path=str(binary),
        trace_sha256=hashlib.sha256(b"fake").hexdigest())
    frozen = runner.freeze_candidates(record)
    witness = dict(returncode=0, trace_c_lines=1, abort_counts={"abort": 1},
                   commit_count_witness=1, batch_commit_count_witness=0)
    key, value = {"rc": ("returncode", 1), "empty": ("trace_c_lines", 0),
                  "abort": ("abort_counts", None), "commit": ("commit_count_witness", None),
                  "batch": ("batch_commit_count_witness", 1)}[change]
    witness[key] = value
    def trace_runner(*args, **kwargs):
        return SimpleNamespace(**witness)
    def verifier(*args, **kwargs):
        raise AssertionError("invalid witness reached verifier")
    result = runner.verify_candidate(dict(freeze=frozen, protocol="silo", cell="wh-base",
                                          identity="K"), trace_runner=trace_runner,
                                     verifier=verifier)
    assert result["status"] == "indeterminate" and result["reason"] == "trace-witness-failed"
    assert result["attempt"] == 1


def test_freeze_cli_create_only(tmp_path):
    source, target = tmp_path / "input.json", tmp_path / "freeze.json"
    source.write_text(json.dumps(_record()))
    assert runner.main(["freeze", str(source), str(target)]) == 0
    assert json.loads(target.read_text())["sha256"] == _freeze()["sha256"]
    with pytest.raises(SystemExit) as exc:
        runner.main(["freeze", str(source), str(target)])
    assert exc.value.code != 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
