"""Contracts for Cicada hot block driver and preregistered mutations."""
from copy import deepcopy
import hashlib
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from orchestrator.campaign import vhash_cicada_hot_block as h


def count_json(k, *, commits=0):
    """The fields and bucket lengths emitted by the variant patch's fprintf stream."""
    workers = []
    for thid in range(256):
        worker = {name: 0 for name in h.COUNT_SCALARS}
        worker.update(thid=thid, hops=[0] * 7, snapshot_lag_ts=[0] * 18)
        if thid == 0:
            worker.update(hot=3, update_commit=commits, install_hold_cycles=42,
                          install_wait_cycles=14, install_count=2, ro_commit=1)
            worker["hops"][4] = 3
            worker["snapshot_lag_ts"][2] = 1
        workers.append(worker)
    return {"schema_version": 1, "k": k, "sizeof_tuple": 64 + 16 * k,
            "workers": workers}


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
              "trace": {"clean": True, "rc": 3, "total_cycles": 0,
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
    result.append({"records": [{**row(0, 0, cell, k, "count"),
                                 "count": count_json(k, commits=2)}
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


def test_patch_count_json_parse_and_worker_aggregation():
    value = count_json(1, commits=2)
    stdout = "throughput[tps]: 1\nCICADA_VHASH_COUNT_JSON " + json.dumps(value) + "\n"
    assert h.parse_count(stdout) == value
    totals = aggregate(jobs())["count"][1]["count"]
    assert totals["hot"] == 3
    assert totals["hops"] == [0, 0, 0, 0, 3, 0, 0]
    assert totals["snapshot_lag_ts"][2] == 1
    assert totals["install_hold_cycles_per_update_commit"] == 21
    assert totals["install_wait_cycles_per_update_commit"] == 7
    assert totals["realized_ro_commit_fraction"] == pytest.approx(1 / 3)
    assert "install_hold_cycles / update_commit" in h.COUNT_DERIVED[
        "install_hold_cycles_per_update_commit"]
    value["workers"][0]["hops"].pop()
    with pytest.raises(ValueError, match="COUNT bucket"):
        h.aggregate_count(value, 1)


def test_patch_break_event_stages_and_witness_attribution():
    stderr = "\n".join([
        "CICADA_BREAK_EVENT slug=stale-hot stage=reached tx_wts=4294967298 key=0a01 read_wts=4294967299",
        "CICADA_BREAK_EVENT slug=stale-hot stage=changed tx_wts=4294967298 key=0a01 read_wts=4294967297",
        "CICADA_BREAK_EVENT slug=stale-hot stage=committed tx_wts=4294967298 key=0a01 read_wts=4294967297",
        "CICADA_BREAK_FIRED slug=stale-hot reached=1 changed=1 committed=1",
    ])
    diagnostics = h._break_events(stderr, "broken-B1")
    assert diagnostics["event_stages"] == {"reached": 1, "changed": 1, "committed": 1}
    record = {"anomalies": [{"cycle": [7, 8], "edges": [{"from": 7, "to": 8,
        "reasons": [{"type": "rw", "key": "0a01", "u_ver": [1, 1],
                     "v_ver": [1, 3]}]}]}]}
    assert h._attribute(record, {4294967298: 7}, diagnostics["events"], 1)["witness_count"] == 1
    record["anomalies"][0]["edges"][0]["reasons"][0]["u_ver"] = [1, 3]
    assert h._attribute(record, {4294967298: 7}, diagnostics["events"], 1)["witness_count"] == 0
    with pytest.raises(ValueError, match="event/summary mismatch"):
        h._break_events(stderr.replace("committed=1", "committed=2"), "broken-B1")
    with pytest.raises(ValueError, match="malformed break event"):
        h._break_events(stderr.replace("stage=changed ", "stage=unknown "), "broken-B1")
    skip = stderr.replace("stale-hot", "skip-pending")
    assert h._break_events(skip, "broken-B2")["fired"]["committed"] == 1


def test_m6_estimate_threshold_and_ladder():
    smoke = {"build_seconds": 500, "max_perf_run_seconds": 9,
             "max_count_run_seconds": 4, "trace_run_verify_seconds": 10,
             "smoke_seconds": 500,
             "build_sharing": {"mode": "shared-verified", "reason": None}}
    first = h.estimate(smoke)
    assert first["threshold_node_seconds"] == 7200
    assert first["steps"][0]["perf_job_seconds"] == 120 * 9 + 60
    assert first["steps"][0]["count_job_seconds"] == 20 * 9 + 60
    assert first["steps"][0]["total_node_seconds"] == 500 + 3 * (120 * 9 + 60) + (20 * 9 + 60) + 2 * 14 * 10
    assert first["steps"][0]["accepted"]
    ladder = h.estimate({**smoke, "max_perf_run_seconds": 100})
    assert [s["rounds"] for s in ladder["steps"]] == [6, 4, 4, 4]
    assert [len(s["cells"]) for s in ladder["steps"]] == [12, 12, 7, 7]
    assert ladder["steps"][3]["ks"] == [0, 1, 8]
    assert ladder["stop"]
    assert not any(s["accepted"] for s in ladder["steps"])
    for wall, accepted in ((2879, True), (2880, False)):
        boundary = h.estimate({**smoke, "max_perf_run_seconds": 10,
                               "smoke_seconds": wall})
        assert boundary["steps"][0]["total_node_seconds"] == wall + 3 * (120 * 10 + 60) + (20 * 10 + 60) + 2 * 14 * 10
        assert boundary["steps"][0]["accepted"] is accepted
        if not accepted:
            assert boundary["steps"][1]["rounds"] == 4


def test_m7_manifest_patch_order_survives_sorted_json(tmp_path, monkeypatch):
    manifest = {"builds": {name: {"patch_order": spec["patches"],
        "patch_sha256": {path: "digest" for path in spec["patches"]}}
        for name, spec in h.build_specs().items()}}
    h.write_json(tmp_path / "manifest.json", manifest)
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["builds"]["trace-k4"]["patch_order"] == [h.TRACE, h.VARIANT]
    assert loaded["builds"]["broken-B1"]["patch_order"] == [h.TRACE, h.VARIANT, h.BROKEN["B1"]]
    assert loaded["builds"]["broken-B2"]["patch_order"] == [h.TRACE, h.VARIANT, h.BROKEN["B2"]]
    seen = []
    monkeypatch.setattr(h, "compute_only", lambda: None)
    monkeypatch.setattr(h, "probe", lambda: {})
    monkeypatch.setattr(h, "_load_manifest", lambda _: loaded)
    monkeypatch.setattr(h, "plan_trace", lambda *_: [
        {"build": name} for name in ("trace-k4", "broken-B1", "broken-B2")])
    monkeypatch.setattr(h, "sharing_preflight", lambda *_: None)
    monkeypatch.setattr(h, "sha", lambda _: "digest")
    monkeypatch.setattr(h, "strict_patches", lambda source, order: seen.append(order))
    monkeypatch.setattr(h, "run_one", lambda *_args, **_kw: {})
    @contextmanager
    def checkout(_pin):
        yield str(tmp_path)
    monkeypatch.setattr(h.patchharness, "checkout", checkout)
    args = SimpleNamespace(command="trace", output=tmp_path, scratch_root=tmp_path,
                           selection=None, job_index=0)
    h._run_job(args)
    assert seen == [[h.TRACE, h.VARIANT], [h.TRACE, h.VARIANT, h.BROKEN["B1"]],
                    [h.TRACE, h.VARIANT, h.BROKEN["B2"]]]


def test_m8_count_argv_extime():
    assert "-extime=3" in h._flags("rr5", "perf")
    assert "-extime=3" in h._flags("rr5", "count")
    assert "-extime=1" in h._flags("T1", "trace")
    assert "-extime=1" in h._flags("T1", "broken")


def test_m9_shared_binary_failure_stops_without_rebuild(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"changed")
    manifest = {"pin": h.PIN, "builds": {"count-k0": {"path": str(binary),
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "runtime_dependencies": {}}}}
    monkeypatch.setattr(h, "compute_only", lambda: None)
    monkeypatch.setattr(h, "probe", lambda: {})
    monkeypatch.setattr(h, "_load_manifest", lambda _: manifest)
    monkeypatch.setattr(h, "plan_count", lambda *_: [{"build": "count-k0"}])
    monkeypatch.setattr(h, "_build_all", lambda _: pytest.fail("rebuilt after sharing failure"))
    args = SimpleNamespace(command="count", output=tmp_path, scratch_root=tmp_path,
                           selection=None, job_index=None)
    with pytest.raises(RuntimeError, match="shared binary verification failed"):
        h._run_job(args)
    raw = json.loads((tmp_path / "raw-count-0.json").read_text())
    assert raw["build_sharing"]["mode"] == "unavailable"
    assert "sha256 mismatch" in raw["failure"]
    assert h.estimate({"build_sharing": raw["build_sharing"]})["stop"]


def test_shared_ldd_resolution_change_stops(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"expected")
    digest = hashlib.sha256(b"expected").hexdigest()
    manifest = {"builds": {"perf-k0": {"path": str(binary),
        "sha256": digest, "runtime_dependencies": {"/lib/old.so": digest}}}}
    monkeypatch.setattr(h, "runtime_dependency_paths", lambda _: ["/lib/new.so"])
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-k0"])


def test_shared_dependency_hash_checked_after_resolution(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"expected")
    dependency = tmp_path / "lib.so"
    dependency.write_bytes(b"changed")
    manifest = {"builds": {"perf-k0": {"path": str(binary),
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "runtime_dependencies": {str(dependency): hashlib.sha256(b"original").hexdigest()}}}}
    monkeypatch.setattr(h, "runtime_dependency_paths", lambda _: [dependency])
    assert "runtime dependency sha256 mismatch" in h.sharing_preflight(manifest, ["perf-k0"])
    dependency.unlink()
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-k0"])
    def unresolved(_):
        raise RuntimeError("unresolved binary dependency: lib.so => not found")
    monkeypatch.setattr(h, "runtime_dependency_paths", unresolved)
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-k0"])


def test_plot_series_uses_all_points_median_and_range():
    from tools.plotting.plot_vhash_cicada_hot_block import _series
    data = {"cells": {"rr5": {"1": {"points": [
        {"ratio": value} for value in (1, 2, 3, 20)]}}}}
    x, centers, errors, points = _series(data, ["rr5"], 1)
    assert x == [0]
    assert centers == [2.5]
    assert errors == [[1.5], [17.5]]
    assert points == [(0, 1), (0, 2), (0, 3), (0, 20)]


@pytest.mark.parametrize("rc,cycles,verdict,valid", [
    (3, 0, "indeterminate", True), (1, 1, "non-serializable", True),
    (0, 0, "serializable", False), (0, 0, "indeterminate", False),
    (3, 1, "non-serializable", False), (1, 0, "non-serializable", False),
    (3, 0, "serializable", False)])
def test_trace_verdict_contract(rc, cycles, verdict, valid):
    assert h._valid_trace_verdict({"rc": rc, "total_cycles": cycles,
                                   "verdict": verdict}) is valid
    if not valid:
        raw = jobs()
        raw[-2]["records"][0]["trace"].update(rc=rc, total_cycles=cycles, verdict=verdict)
        with pytest.raises(ValueError, match="invalid trace"):
            aggregate(raw)


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
