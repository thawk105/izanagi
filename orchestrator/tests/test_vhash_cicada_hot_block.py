"""Contracts for Cicada hot block driver and preregistered mutations."""
from copy import deepcopy
import hashlib

import pytest

from orchestrator.campaign import vhash_cicada_hot_block as h


def row(job, round_, cell, k, kind="perf", throughput=100.0):
    return {"job_index": job, "round": round_, "cell": cell, "k": k,
            "job_id": f"job-{job}", "node": f"node-{job}",
            "build": f"{kind}-k{k}", "build_kind": kind, "pin": h.PIN,
            "patch_sha256": {h.VARIANT: "a" * 64}, "binary_sha256": f"{k:064x}",
            "perf_eligible": kind == "perf", "rc": 0,
            "throughput": throughput, "maxrss_kb": 100 + k,
            "tuple_size_bytes": 64 + 16 * k}


def jobs():
    result = []
    for job in (0, 1):
        records = []
        for round_ in (job * 2, job * 2 + 1):
            records += [row(job, round_, "rr5", 0, throughput=100 + round_),
                        row(job, round_, "rr5", 1,
                            throughput=(100 + round_) * (1 + .1 * (round_ + 1)))]
        result.append({"records": records})
    trace = [{"cell": cell, "k": k, "build_kind": "trace",
              "build": f"trace-k{k}", "rc": 0,
              "trace": {"clean": True, "rc": 0, "total_cycles": 0,
                        "verdict": "indeterminate"}}
             for cell in h.TRACE_CELLS for k in (0, 1)]
    trace += [{"cell": cell, "k": 4, "build_kind": "broken",
               "build": f"broken-{broken}", "rc": 0,
               "trace": {"clean": True, "rc": 3, "total_cycles": 0,
                         "verdict": "indeterminate", "break": {
                             "fired": {"reached": 0, "changed": 0, "committed": 0},
                             "witness_count": 0}}}
              for cell in ("T1", "T2") for broken in h.BROKEN]
    result.append({"records": trace})
    result.append({"records": [{**row(0, 0, cell, k, "count"), "count": {"test": 1}}
                               for cell in h.COUNT_CELLS for k in (0, 1)]})
    return result


def aggregate(raw):
    return h.aggregate_jobs(raw, rounds=4, cells=("rr5",), ks=(0, 1))


def test_grid_rotation_jobs():
    assert len(h.CELLS) == 12
    assert h.rotation(0, 0) == h.KS
    assert h.rotation(1, 0) == h.rotation(0, 1) == h.KS[1:] + h.KS[:1]
    assert [len(h.plan_perf(j)) for j in (0, 1, 2)] == [120] * 3
    assert [{r["round"] for r in h.plan_perf(j)} for j in (0, 1, 2)] == [
        {0, 1}, {2, 3}, {4, 5}]
    assert len(h.plan_count()) == 20
    assert [len(h.plan_trace(j)) for j in (0, 1)] == [14, 5]


def test_build_list_isolated():
    specs = h.build_specs()
    assert len(specs) == 17
    for k in h.KS:
        perf = specs[f"perf-k{k}"]
        assert perf["trace"] == 0
        assert "CICADA_VHASH_COUNT" not in perf["macros"]
        assert perf["macros"]["CICADA_VHASH_WL"] == 1
        assert perf["patches"] == [h.VARIANT]
        assert specs[f"count-k{k}"]["macros"]["CICADA_VHASH_COUNT"] == 1
        assert specs[f"trace-k{k}"]["patches"] == [h.TRACE, h.VARIANT]
    assert specs["broken-B1"]["patches"] == [h.TRACE, h.VARIANT, h.BROKEN["B1"]]
    assert specs["broken-B2"]["patches"] == [h.TRACE, h.VARIANT, h.BROKEN["B2"]]


def test_m1_non_perf_record_never_enters_table():
    raw = jobs()
    raw[-1]["records"][0]["throughput"] = 10**9
    raw[-2]["records"][0]["throughput"] = 10**9
    values = aggregate(raw)["cells"]["rr5"]["1"]
    assert len(values["points"]) == 4
    assert values["median"] < 2


def test_m2_binary_hash_checked_before_spawn(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"expected")
    manifest = {"builds": {"perf-k1": {"path": str(binary),
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "runtime_dependencies": {}}}}
    binary.write_bytes(b"changed")
    monkeypatch.setattr(h, "probe", lambda: (_ for _ in ()).throw(
        AssertionError("spawn reached")))
    with pytest.raises(RuntimeError, match="binary sha256 mismatch"):
        h.run_one(manifest, {"build": "perf-k1"}, scratch=tmp_path)


def test_m3_pair_uses_same_job_and_round():
    raw = jobs()
    raw[0]["records"][0]["throughput"] = 10
    raw[1]["records"][0]["throughput"] = 1000
    points = aggregate(raw)["cells"]["rr5"]["1"]["points"]
    by_round = {p["round"]: p["ratio"] for p in points}
    assert by_round[0] == pytest.approx(11)
    assert by_round[2] == pytest.approx(0.1339, rel=1e-2)
    raw[0]["records"][1]["job_id"] = "different-job"
    with pytest.raises(ValueError, match="crosses job"):
        aggregate(raw)


def test_m4_missing_and_duplicate_fail_closed():
    raw = jobs()
    missing = deepcopy(raw)
    missing[0]["records"].pop()
    with pytest.raises(ValueError, match="missing perf runs"):
        aggregate(missing)
    duplicate = deepcopy(raw)
    duplicate[0]["records"].append(deepcopy(duplicate[0]["records"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(duplicate)


def test_sha_mismatch_fails_closed():
    raw = jobs()
    raw[1]["records"][0]["binary_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="sha256 mismatch"):
        aggregate(raw)


def test_m5_cycle_disqualifies_arm():
    raw = jobs()
    raw[-2]["records"][1]["trace"].update(
        rc=1, total_cycles=1, verdict="non-serializable")
    result = aggregate(raw)
    assert result["disqualified_ks"] == [1]
    assert result["cells"]["rr5"] == {}


def test_trace_coverage_and_integrity_fail_closed():
    raw = jobs()
    raw[-2]["records"].pop(0)
    with pytest.raises(ValueError, match="trace coverage"):
        aggregate(raw)
    raw = jobs()
    raw[-2]["records"][0]["trace"]["clean"] = False
    with pytest.raises(ValueError, match="invalid trace"):
        aggregate(raw)


def test_count_coverage_fails_closed():
    raw = jobs()
    raw[-1]["records"].pop()
    with pytest.raises(ValueError, match="COUNT coverage"):
        aggregate(raw)


def test_m6_estimate_threshold_and_ladder():
    smoke = {"build_seconds": 500, "max_perf_run_seconds": 9,
             "max_count_run_seconds": 4, "trace_run_verify_seconds": 10,
             "smoke_seconds": 500}
    first = h.estimate(smoke)
    assert first["threshold_node_seconds"] == 7200
    assert first["steps"][0]["perf_job_seconds"] == 120 * 9 + 60
    assert first["steps"][0]["accepted"]
    ladder = h.estimate({**smoke, "max_perf_run_seconds": 100})
    assert [s["rounds"] for s in ladder["steps"]] == [6, 4, 4, 4]
    assert [len(s["cells"]) for s in ladder["steps"]] == [12, 12, 7, 7]
    assert ladder["steps"][3]["ks"] == [0, 1, 8]
    assert ladder["stop"]
    assert not any(s["accepted"] for s in ladder["steps"])
    boundary = h.estimate({**smoke, "max_perf_run_seconds": 15.97223})
    assert boundary["steps"][0]["total_node_seconds"] > 7200
    assert boundary["steps"][0]["accepted"] is False
    assert boundary["steps"][1]["rounds"] == 4


def test_broken_rules():
    b1 = {"build": "broken-B1", "trace": {"verdict": "non-serializable",
          "total_cycles": 1, "break": {"fired": {"reached": 2, "changed": 2,
          "committed": 1}, "witness_count": 1}}}
    assert h.broken_verdict(b1)["status"] == "detected"
    b1["trace"]["break"]["witness_count"] = 0
    assert h.broken_verdict(b1) == {"status": "undetected", "needs_B3": True}
    b2 = {"build": "broken-B2", "trace": {"verdict": "indeterminate",
          "total_cycles": 0, "break": {"fired": {"reached": 3, "changed": 3,
          "committed": 0}, "witness_count": 0}}}
    assert h.broken_verdict(b2)["status"] == "validation-stopped"
    b2["trace"]["break"]["fired"]["committed"] = 1
    assert h.broken_verdict(b2)["status"] == "prediction-failed"
