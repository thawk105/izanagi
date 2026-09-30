"""Five-arm hot block contracts and registered mutation witnesses."""
import hashlib
import json
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace

import pytest

from orchestrator.campaign import vhash_cicada_hot_block as h


def count_json(arm):
    workers = []
    for thid in range(256):
        worker = {name: 0 for name in h.COUNT_SCALARS}
        worker.update(thid=thid, hops=[0] * 7, snapshot_lag_cycles=[0] * 42)
        if thid == 0:
            worker.update(hot=3, update_commit=2, ro_commit=1,
                          install_count=0 if arm.startswith("post-") else 2,
                          install_wait_cycles=0 if arm.startswith("post-") else 14,
                          install_hold_cycles=0 if arm.startswith("post-") else 42,
                          snapshot_lag_count=1,
                          snapshot_lag_sum_cycles=2)
            worker["snapshot_lag_cycles"][2] = 1
            worker["hops"][4] = 3
        workers.append(worker)
    post = None
    if arm.startswith("post-"):
        post_workers = []
        for thid in range(256):
            item = {name: 0 for name in h.POST_SCALARS}
            item["thid"] = thid
            if thid == 0:
                item.update(publish_wait_cycles=20, publish_hold_cycles=30)
            post_workers.append(item)
        post = {"schema_version": 1, "k": h.ARM_K[arm], "workers": post_workers}
    return {"variant": {"schema_version": 2, "k": h.ARM_K[arm],
                        "sizeof_tuple": 64 + 16 * h.ARM_K[arm], "workers": workers},
            "post": post}


def row(job, round_, cell, arm, kind="perf", throughput=100):
    return {"job_index": job, "round": round_, "cell": cell, "arm": arm,
            "k": h.ARM_K[arm], "job_id": f"job-{job}", "node": f"node-{job}",
            "build": f"{kind}-{arm}", "build_kind": kind, "pin": h.PIN,
            "patch_sha256": {h.VARIANT: "a" * 64},
            "binary_sha256": hashlib.sha256(arm.encode()).hexdigest(),
            "perf_eligible": kind == "perf", "rc": 0, "throughput": throughput,
            "maxrss_kb": 100 + h.ARM_K[arm],
            "tuple_size_bytes": 64 + 16 * h.ARM_K[arm],
            "argv": ["-clocks_per_us=2100"]}


def jobs():
    raw = []
    for job in (0, 1):
        records = []
        for round_ in (job * 2, job * 2 + 1):
            for i, arm in enumerate(h.ARMS):
                records.append(row(job, round_, "rr5", arm,
                                   throughput=(100 + round_) * (1 + i / 10)))
        raw.append({"records": records})
    trace = [{**row(0, 0, cell, arm, "trace"),
              "trace": {"clean": True, "rc": 3, "total_cycles": 0,
                        "verdict": "indeterminate"}}
             for cell in h.TRACE_CELLS for arm in h.ARMS]
    trace += [{"cell": cell, "arm": "post-k8", "build_kind": "broken",
               "build": f"broken-{name}", "rc": 0,
               "trace": {"clean": True, "rc": 3, "total_cycles": 0,
                         "verdict": "indeterminate", "break": {
                             "fired": {"reached": 0, "changed": 0, "committed": 0},
                             "omitted": 0 if name == "stale-gap" else None,
                             "undetermined": 0 if name == "stale-gap" else None,
                             "witness_count": 0}}}
              for cell in ("T1", "T2") for name in (*h.BROKEN, "B2-probe")]
    raw.append({"records": trace})
    raw.append({"records": [{**row(0, 0, cell, arm, "count"),
                             "count": count_json(arm)}
                            for cell in h.COUNT_CELLS for arm in h.ARMS]})
    return raw


def aggregate(raw):
    return h.aggregate_jobs(raw, rounds=4, cells=("rr5",))


def test_grid_rotation_jobs():
    assert len(h.CELLS) == 12
    assert h.rotation(0, 0) == h.ARMS
    assert h.rotation(1, 0) == h.rotation(0, 1) == h.ARMS[1:] + h.ARMS[:1]
    assert [len(h.plan_perf(j)) for j in (0, 1, 2)] == [120] * 3
    assert [{r["round"] for r in h.plan_perf(j)} for j in (0, 1, 2)] == [
        {0, 1}, {2, 3}, {4, 5}]
    assert len(h.plan_count()) == 20
    assert [len(h.plan_trace(j)) for j in (0, 1)] == [18, 5]
    for job in (0, 1, 2):
        for round_ in (2 * job, 2 * job + 1):
            assert {r["arm"] for r in h.plan_perf(job) if r["round"] == round_} == set(h.ARMS)


def test_build_list_isolated():
    specs = h.build_specs()
    assert len(specs) == 19
    for arm in h.ARMS:
        base = [h.VARIANT] + ([h.POST] if arm.startswith("post-") else [])
        assert specs[f"perf-{arm}"]["patches"] == base
        assert specs[f"count-{arm}"]["patches"] == base + [h.COUNT_V2]
        assert specs[f"trace-{arm}"]["patches"] == [h.TRACE] + base
        assert specs[f"perf-{arm}"]["trace"] == 0
        assert "CICADA_VHASH_COUNT" not in specs[f"perf-{arm}"]["macros"]
        assert specs[f"perf-{arm}"]["macros"]["CICADA_VHASH_WL"] == 1
        assert specs[f"count-{arm}"]["macros"]["CICADA_VHASH_COUNT"] == 1
    for name in h.BROKEN:
        assert specs[f"broken-{name}"]["patches"] == [
            h.TRACE, h.VARIANT, h.POST, h.BROKEN[name]]
    assert specs["broken-B2-probe"]["patches"] == [h.TRACE, h.VARIANT, h.B2_PROBE]


def test_m6_estimate_threshold_and_ladder():
    smoke = {"build_seconds": 300, "max_perf_run_seconds": 9,
             "max_count_run_seconds": 4, "trace_run_verify_seconds": 10,
             "smoke_seconds": 310, "mutation_seconds": 650,
             "focus_and_audit_seconds": 350,
             "build_sharing": {"mode": "shared-verified"}}
    first = h.estimate(smoke)["steps"][0]
    assert h.estimate(smoke)["threshold_node_seconds"] == 7200
    assert first["perf_job_seconds"] == 120 * 9 + 60
    assert first["count_job_seconds"] == 20 * 4 + 60
    assert first["trace_job_seconds"] == [180, 50]
    assert first["total_node_seconds"] == 310 + 300 + 3 * (120 * 9 + 60) + 20 * 4 + 60 + 230 + 1000
    huge = h.estimate({**smoke, "max_perf_run_seconds": 100})
    assert [x["rounds"] for x in huge["steps"]] == [6, 4, 4]
    assert [len(x["cells"]) for x in huge["steps"]] == [12, 12, 9]
    assert huge["stop"]
    assert not any(step["accepted"] for step in huge["steps"])
    base = first["total_node_seconds"] - smoke["smoke_seconds"]
    for wall, accepted in ((7200 - base, True), (7201 - base, False)):
        boundary = h.estimate({**smoke, "smoke_seconds": wall})
        assert boundary["steps"][0]["total_node_seconds"] == wall + base
        assert boundary["steps"][0]["accepted"] is accepted
        if not accepted:
            assert boundary["steps"][1]["rounds"] == 4


def test_m2_count_v2_only():
    raw = count_json("B-k1")["variant"]
    result = h.aggregate_count(raw, "B-k1")
    assert result["snapshot_lag_cycles"][2] == 1
    assert result["snapshot_lag_bucket_bounds"][2]["lower_us"] == 2 / 2100
    assert result["snapshot_lag_bucket_bounds"][-1]["upper_us"] is None
    assert result["install_wait_cycles_per_update_commit"] == 7
    with pytest.raises(ValueError):
        h.aggregate_count({**raw, "schema_version": 1}, "B-k1")
    raw["workers"][0]["snapshot_lag_cycles"] = [0] * 18
    with pytest.raises(ValueError):
        h.aggregate_count(raw, "B-k1")


def test_m9_post_count_line_required():
    payload = count_json("post-k8")
    text = h.COUNT_PREFIX + json.dumps(payload["variant"]) + "\n"
    with pytest.raises(ValueError, match="POST COUNT"):
        h.parse_count(text, "post-k8")
    full = text + h.POST_COUNT_PREFIX + json.dumps(payload["post"]) + "\n"
    assert h.parse_count(full, "post-k8")["post"] == payload["post"]
    with pytest.raises(ValueError, match="POST COUNT"):
        h.parse_count(full, "B-k8")
    assert h.aggregate_post_count(payload["post"], "post-k8", 2)["publish_wait_cycles_per_update_commit"] == 10
    assert h.aggregate_post_count(payload["post"], "post-k8", 0)["publish_hold_cycles_per_update_commit"] is None


def test_m3_pair_uses_same_job_and_round():
    raw = jobs()
    raw[0]["records"][0]["throughput"] = 10
    document = aggregate(raw)
    assert document["schema"] == "vhash-hot-aggregate/v2"
    result = document["cells"]["rr5"]
    assert result["post-k1/stock"]["points"][0]["ratio"] == 13
    assert result["post-k1/stock"]["points"][1]["ratio"] == pytest.approx(1.3)
    raw[1]["records"][0]["throughput"] = 1000
    by_round = {p["round"]: p["ratio"] for p in aggregate(raw)["cells"]["rr5"]["B-k1/stock"]["points"]}
    assert by_round[0] == pytest.approx(11)
    assert by_round[2] == pytest.approx(112.2 / 1000)
    assert set(result["post-k1/B-k1"]["by_node"]) == {"node-0", "node-1"}
    raw[0]["records"][3]["job_id"] = "wrong"
    with pytest.raises(ValueError, match="crosses job"):
        aggregate(raw)


def test_m5_cycle_disqualifies_arm():
    raw = jobs()
    target = next(r for r in raw[-2]["records"] if r["cell"] == "T1" and r["arm"] == "post-k1")
    target["trace"].update(rc=1, total_cycles=1, verdict="non-serializable")
    result = aggregate(raw)
    assert result["disqualified_arms"] == ["post-k1"]
    assert "post-k1/stock" not in result["cells"]["rr5"]
    assert "post-k1/B-k1" not in result["cells"]["rr5"]
    assert "B-k1/stock" in result["cells"]["rr5"]
    raw = jobs()
    target = next(r for r in raw[-2]["records"] if r["cell"] == "T1" and r["arm"] == "B-k1")
    target["trace"].update(rc=1, total_cycles=1, verdict="non-serializable")
    result = aggregate(raw)
    assert result["disqualified_arms"] == ["B-k1"]
    assert "B-k1/stock" not in result["cells"]["rr5"]
    assert "post-k1/B-k1" not in result["cells"]["rr5"]
    assert "post-k1/stock" in result["cells"]["rr5"]


def test_m5_stale_gap_trace_and_verdict():
    assert [len(h.plan_trace(j)) for j in (0, 1)] == [18, 5]
    assert {r["build"] for r in h.plan_trace(0) if r["build"].startswith("broken-")} == {
        "broken-B1", "broken-B2", "broken-stale-gap", "broken-B2-probe"}
    raw = jobs()
    raw[-2]["records"] = [r for r in raw[-2]["records"] if r["build"] != "broken-stale-gap"]
    with pytest.raises(ValueError, match="broken trace coverage"):
        aggregate(raw)
    record = {"build": "broken-stale-gap", "trace": {"verdict": "indeterminate",
              "total_cycles": 0, "break": {"omitted": 1, "undetermined": 2,
              "fired": {"reached": 1,
              "changed": 1, "committed": 1}, "witness_count": 0}}}
    assert h.broken_verdict(record)["status"] == "undetected"
    assert h.broken_verdict(record)["undetermined"] == 2
    record["trace"]["break"]["fired"]["reached"] = 0
    assert h.broken_verdict(record)["status"] == "unreached"
    raw = jobs()
    gap = next(r for r in raw[-2]["records"] if r["build"] == "broken-stale-gap"
               and r["cell"] == "T1")
    gap["trace"]["break"]["undetermined"] = 2
    assert aggregate(raw)["broken"]["broken-stale-gap:T1"]["undetermined"] == 2


def test_probe_join_and_missing_keys():
    probe = "\n".join([
        "CICADA_B2PROBE stage=read id=1:2 is_ronly=0 tx_wts=5 rts=3 p_ptr=0x1 p_wts=6 p_status=1 older_ptr=0x2 older_wts=4 read_index=0 key=0a01",
        "CICADA_B2PROBE stage=validate id=1:2 p_status=2 p_wts=6 start_ptr=0x1 reached_ptr=0x2 reached_eq_older=1",
        "CICADA_B2PROBE stage=end id=1:2 outcome=commit"])
    assert h._probe_events(probe)["committed"]["A"] == 1
    with pytest.raises(ValueError, match="missing"):
        h._probe_events(probe.replace(" reached_eq_older=1", ""))


@pytest.mark.parametrize("label,ro,status,read_wts,validate_wts,reached", [
    ("R", 1, 2, 6, 7, 0), ("A", 0, 2, 6, 7, 1),
    ("G", 0, 4, 6, 7, 1), ("M", 0, 4, 6, 6, 1),
    ("V", 0, 4, 6, 6, 0), ("U", 0, 1, 6, 6, 1),
])
def test_probe_actual_format_classification(label, ro, status, read_wts, validate_wts, reached):
    lines = [
        f"CICADA_B2PROBE stage=read id=1:2 is_ronly={ro} tx_wts=5 rts=3 p_ptr=0x1 p_wts={read_wts} p_status=1 older_ptr=0x2 older_wts=4 read_index=0 key=0a01",
        f"CICADA_B2PROBE stage=validate id=1:2 p_status={status} p_wts={validate_wts} start_ptr=0x3 reached_ptr=0x2 reached_eq_older={reached}",
        "CICADA_B2PROBE stage=end id=1:2 outcome=commit",
    ]
    result = h._probe_events("\n".join(lines))
    assert result["committed"] == {name: int(name == label) for name in "RAGMVU"}
    assert result["events"]["1:2"]["stages"]["validate"]["p_status"] == h.PROBE_STATUS[status]
    assert result["m_start_versions"] == ({"0x3": 1} if label == "M" else {})
    if label == "U":
        result = h._probe_events("\n".join((lines[0], lines[2])))
        assert result["committed"]["U"] == 1


def test_probe_actual_format_missing_key_and_invalid_status():
    read = "CICADA_B2PROBE stage=read id=1:2 is_ronly=0 tx_wts=5 rts=3 p_ptr=0x1 p_wts=6 p_status=1 older_ptr=0x2 older_wts=4 read_index=0 key=0a01"
    end = "CICADA_B2PROBE stage=end id=1:2 outcome=commit"
    with pytest.raises(ValueError, match="B2 probe missing key"):
        h._probe_events("\n".join((read.replace(" key=0a01", ""), end)))
    with pytest.raises(ValueError, match="B2 probe invalid p_status"):
        h._probe_events("\n".join((read.replace("p_status=1", "p_status=7"), end)))


@pytest.mark.parametrize("status,name", [
    (0, "invalid"), (1, "pending"), (2, "aborted"), (3, "precommitted"),
    (4, "committed"), (5, "deleted"), (6, "unused"),
])
def test_probe_version_status_names(status, name):
    probe = "\n".join((
        f"CICADA_B2PROBE stage=read id=1:2 is_ronly=0 tx_wts=5 rts=3 p_ptr=0x1 p_wts=6 p_status={status} older_ptr=0x2 older_wts=4 read_index=0 key=0a01",
        "CICADA_B2PROBE stage=end id=1:2 outcome=abort",
    ))
    result = h._probe_events(probe)
    assert result["events"]["1:2"]["stages"]["read"]["p_status"] == name
    assert sum(result["committed"].values()) == 0


def test_probe_actual_format_break_and_witness_join(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "_trace_rows", lambda _: ({"C": 1}, {}))
    payload = {"results": [{"verdict": "indeterminate", "total_cycles": 0,
                            "integrity": {name: 0 for name in h.INTEGRITY_ZERO}}]}
    monkeypatch.setattr(h.subprocess, "run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=3, stdout=json.dumps(payload).encode(), stderr=b""))
    witness = {"stage": "committed", "tx_wts": 5, "key": "0a01", "read_wts": 4}
    monkeypatch.setattr(h, "_attribute", lambda *_args: {
        "witness_count": 1, "examples": [], "witness_events": [witness]})
    read = "CICADA_B2PROBE stage=read id=1:2 is_ronly=0 tx_wts=5 rts=3 p_ptr=0x1 p_wts=6 p_status=1 older_ptr=0x2 older_wts=4 read_index=0 key=0a01"
    suffix = "\n".join((
        "CICADA_B2PROBE stage=validate id=1:2 p_status=2 p_wts=6 start_ptr=0x1 reached_ptr=0x2 reached_eq_older=1",
        "CICADA_B2PROBE stage=end id=1:2 outcome=commit",
        "CICADA_BREAK_EVENT slug=skip-pending stage=changed tx_wts=5 key=0a01 read_wts=4",
        "CICADA_BREAK_EVENT slug=skip-pending stage=committed tx_wts=5 key=0a01 read_wts=4",
        "CICADA_BREAK_FIRED slug=skip-pending reached=0 changed=1 committed=1",
        "CICADA_TRACE_INITIAL_WTS=1",
    ))
    result = h._verify_trace(tmp_path, tmp_path, 1, read + "\n" + suffix,
                             "broken-B2-probe", "broken")
    assert result["probe"]["committed"]["A"] == 1
    assert result["probe"]["witness"]["A"] == 1
    for changed in (read.replace("tx_wts=5", "tx_wts=8"),
                    read.replace("key=0a01", "key=0a02"),
                    read.replace("older_wts=4", "older_wts=9")):
        with pytest.raises(ValueError, match="no changed break event"):
            h._verify_trace(tmp_path, tmp_path, 1, changed + "\n" + suffix,
                            "broken-B2-probe", "broken")


def test_m10_probe_changed_and_committed_multisets(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "_trace_rows", lambda _: ({"C": 1}, {}))
    payload = {"results": [{"verdict": "indeterminate", "total_cycles": 0,
                            "integrity": {name: 0 for name in h.INTEGRITY_ZERO}}]}
    monkeypatch.setattr(h.subprocess, "run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=3, stdout=json.dumps(payload).encode(), stderr=b""))
    monkeypatch.setattr(h, "_attribute", lambda *_args: {
        "witness_count": 0, "examples": [], "witness_events": []})
    read = "CICADA_B2PROBE stage=read id=1:2 is_ronly=0 tx_wts=5 rts=3 p_ptr=0x1 p_wts=6 p_status=1 older_ptr=0x2 older_wts=4 read_index=0 key=0a01"
    end = "CICADA_B2PROBE stage=end id=1:2 outcome=commit"
    changed = "CICADA_BREAK_EVENT slug=skip-pending stage=changed tx_wts=5 key=0a01 read_wts=4"
    committed = changed.replace("stage=changed", "stage=committed")
    summary = "CICADA_BREAK_FIRED slug=skip-pending reached=0 changed=1 committed=1"
    base = [read, end, changed, committed, summary, "CICADA_TRACE_INITIAL_WTS=1"]
    h._verify_trace(tmp_path, tmp_path, 1, "\n".join(base), "broken-B2-probe", "broken")
    extra_probe = [read.replace("id=1:2", "id=1:3"),
                   end.replace("id=1:2 outcome=commit", "id=1:3 outcome=abort")]
    with pytest.raises(ValueError, match="changed break event"):
        h._verify_trace(tmp_path, tmp_path, 1, "\n".join(base + extra_probe),
                        "broken-B2-probe", "broken")
    extra_changed = [changed.replace("key=0a01", "key=0a02"),
                     summary.replace("changed=1", "changed=2")]
    with pytest.raises(ValueError, match="changed break event multiset mismatch"):
        h._verify_trace(tmp_path, tmp_path, 1,
                        "\n".join([read, end, changed, extra_changed[0], committed,
                                   extra_changed[1], base[-1]]), "broken-B2-probe", "broken")
    with pytest.raises(ValueError, match="committed break event multiset mismatch"):
        h._verify_trace(tmp_path, tmp_path, 1,
                        "\n".join([read, end, changed, summary.replace("committed=1", "committed=0"),
                                   base[-1]]), "broken-B2-probe", "broken")
    with pytest.raises(ValueError, match="committed break event multiset mismatch"):
        h._verify_trace(tmp_path, tmp_path, 1,
                        "\n".join([read, end.replace("outcome=commit", "outcome=abort"),
                                   changed, committed, summary, base[-1]]),
                        "broken-B2-probe", "broken")


def test_shared_binary_dependency_hashes(tmp_path, monkeypatch):
    binary, dependency = tmp_path / "binary", tmp_path / "library"
    binary.write_bytes(b"binary")
    dependency.write_bytes(b"library")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"builds": {"perf-stock": {"path": str(binary), "sha256": digest(binary),
                "runtime_dependencies": {str(dependency): digest(dependency)}}}}
    monkeypatch.setattr(h, "runtime_dependency_paths", lambda _: [dependency])
    assert h.sharing_preflight(manifest, ["perf-stock"]) is None
    dependency.write_bytes(b"changed")
    assert "dependency sha256 mismatch" in h.sharing_preflight(manifest, ["perf-stock"])
    dependency.write_bytes(b"library")
    binary.write_bytes(b"changed")
    assert "binary sha256 mismatch" in h.sharing_preflight(manifest, ["perf-stock"])


def test_missing_duplicate_hash_and_trace_coverage_fail_closed():
    raw = jobs()
    raw[0]["records"].pop()
    with pytest.raises(ValueError, match="missing perf runs"):
        aggregate(raw)
    raw = jobs()
    raw[0]["records"].append(dict(raw[0]["records"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(raw)
    raw = jobs()
    raw[0]["records"][0]["binary_sha256"] = "x" * 64
    with pytest.raises(ValueError, match="sha256 mismatch"):
        aggregate(raw)
    raw = jobs()
    raw[-2]["records"].pop()
    with pytest.raises(ValueError, match="broken trace coverage"):
        aggregate(raw)
    raw = jobs()
    raw[-1]["records"].pop()
    with pytest.raises(ValueError, match="COUNT coverage"):
        aggregate(raw)


@pytest.mark.parametrize("rc,cycles,verdict,valid", [
    (3, 0, "indeterminate", True), (1, 1, "non-serializable", True),
    (0, 0, "serializable", False), (0, 0, "indeterminate", False),
    (3, 1, "non-serializable", False), (1, 0, "non-serializable", False),
    (3, 0, "serializable", False)])
def test_trace_verdict_contract(rc, cycles, verdict, valid):
    value = {"rc": rc, "total_cycles": cycles, "verdict": verdict}
    assert h._valid_trace_verdict(value) is valid
    if not valid:
        raw = jobs()
        raw[-2]["records"][0]["trace"].update(value)
        with pytest.raises(ValueError, match="invalid trace"):
            aggregate(raw)


def test_break_event_summary_and_omission_required():
    lines = [
        "CICADA_BREAK_EVENT slug=post-stale-gap stage=reached tx_wts=2 key=0a01 read_wts=3",
        "CICADA_BREAK_FIRED slug=post-stale-gap reached=1 changed=0 committed=0",
        "CICADA_BREAK_OMITTED slug=post-stale-gap omitted=4",
        "CICADA_BREAK_UNDETERMINED slug=post-stale-gap undetermined=2"]
    parsed = h._break_events("\n".join(lines), "broken-stale-gap")
    assert parsed["omitted"] == 4
    assert parsed["undetermined"] == 2
    with pytest.raises(ValueError, match="omitted"):
        h._break_events("\n".join((lines[0], lines[1], lines[3])), "broken-stale-gap")
    with pytest.raises(ValueError, match="undetermined"):
        h._break_events("\n".join(lines[:-1]), "broken-stale-gap")
    with pytest.raises(ValueError, match="event/summary mismatch"):
        h._break_events("\n".join([lines[0], lines[1].replace("reached=1", "reached=2"),
                                    lines[2]]), "broken-stale-gap")


def test_broken_rules():
    record = {"build": "broken-B1", "trace": {"verdict": "non-serializable",
              "total_cycles": 1, "break": {"fired": {"reached": 2, "changed": 2,
              "committed": 1}, "witness_count": 1}}}
    assert h.broken_verdict(record)["status"] == "detected"
    record["trace"]["break"]["witness_count"] = 0
    assert h.broken_verdict(record) == {"status": "undetected", "needs_B3": True}
    b2 = {"build": "broken-B2", "cell": "T2", "trace": {"verdict": "indeterminate",
          "total_cycles": 0, "break": {"fired": {"reached": 3, "changed": 3,
          "committed": 0}, "witness_count": 0}}}
    assert h.broken_verdict(b2)["status"] == "validation-stopped"
    b2["trace"]["break"]["fired"]["committed"] = 1
    assert h.broken_verdict(b2)["status"] == "undetected"


@pytest.mark.parametrize("build", ["broken-B2", "broken-B2-probe"])
@pytest.mark.parametrize("reached,changed,committed", [
    (0, 0, 0), (1, 1, 0), (1, 1, 1), (2, 1, 1), (2, 2, 2)])
def test_m11_b2_verdict_records_observations(build, reached, changed, committed):
    record = {"build": build, "cell": "T1", "trace": {
        "verdict": "indeterminate", "total_cycles": 0,
        "break": {"fired": {"reached": reached, "changed": changed,
                            "committed": committed}, "witness_count": 0}}}
    result = h.broken_verdict(record)
    assert {key: result[key] for key in ("reached", "changed", "committed")} == {
        "reached": reached, "changed": changed, "committed": committed}
    assert result["status"] == ("unreached" if reached == 0 else
                                "undetected" if committed else "validation-stopped")
    assert "prediction_met" not in result


def test_perf_eligibility_and_pair_node_must_match():
    raw = jobs()
    raw[0]["records"][1]["perf_eligible"] = False
    with pytest.raises(ValueError, match="ineligible performance"):
        aggregate(raw)
    raw = jobs()
    raw[0]["records"][1]["node"] = "different"
    with pytest.raises(ValueError, match="crosses job or node"):
        aggregate(raw)


def test_m8_count_argv_extime():
    assert "-extime=3" in h._flags("rr5", "perf")
    assert "-extime=3" in h._flags("rr5", "count")
    assert "-extime=1" in h._flags("T1", "trace")
    assert "-extime=1" in h._flags("T1", "broken")
    assert "-group_commit=0" in h._flags("T1", "trace")
    assert "-group_commit=0" not in h._flags("rr5", "perf")


def test_no_post_count_on_b_and_no_variant_install_on_post():
    raw = jobs()
    b = next(r for r in raw[-1]["records"] if r["arm"] == "B-k1")
    b["count"]["post"] = count_json("post-k1")["post"]
    with pytest.raises(ValueError, match="unexpected POST"):
        aggregate(raw)
    raw = jobs()
    post = next(r for r in raw[-1]["records"] if r["arm"] == "post-k1")
    post["count"]["variant"]["workers"][0]["install_wait_cycles"] = 1
    with pytest.raises(ValueError, match="variant install"):
        aggregate(raw)


def test_m2_binary_hash_checked_before_spawn(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"changed")
    manifest = {"builds": {"perf-stock": {"path": str(binary),
                "sha256": hashlib.sha256(b"expected").hexdigest(),
                "runtime_dependencies": {}}}}
    monkeypatch.setattr(h, "probe", lambda: pytest.fail("benchmark probe reached"))
    with pytest.raises(RuntimeError, match="binary sha256 mismatch"):
        h.run_one(manifest, {"build": "perf-stock"}, scratch=tmp_path)


def test_m7_manifest_patch_order_survives_sorted_json(tmp_path, monkeypatch):
    specs = h.build_specs()
    payload = {"builds": {name: {"patch_order": spec["patches"],
              "patch_sha256": {path: "digest" for path in spec["patches"]}}
              for name, spec in specs.items()}}
    h.write_json(tmp_path / "manifest.json", payload)
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["builds"]["trace-post-k8"]["patch_order"] == [h.TRACE, h.VARIANT, h.POST]
    assert loaded["builds"]["broken-stale-gap"]["patch_order"] == [
        h.TRACE, h.VARIANT, h.POST, h.BROKEN["stale-gap"]]
    for name in ("B1", "B2"):
        assert loaded["builds"][f"broken-{name}"]["patch_order"] == [
            h.TRACE, h.VARIANT, h.POST, h.BROKEN[name]]
    seen = []
    monkeypatch.setattr(h, "compute_only", lambda: None)
    monkeypatch.setattr(h, "probe", lambda: {})
    monkeypatch.setattr(h, "_load_manifest", lambda _: loaded)
    names = ("trace-post-k8", "broken-B1", "broken-B2", "broken-stale-gap")
    monkeypatch.setattr(h, "plan_trace", lambda *_: [{"build": name} for name in names])
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
    assert seen == [loaded["builds"][name]["patch_order"] for name in names]


@pytest.mark.parametrize("build", ["trace-stock", "trace-B-k1", "trace-post-k8"])
def test_stock_and_k_integrity_violation_still_stops(tmp_path, monkeypatch, build):
    monkeypatch.setattr(h, "_trace_rows",
                        lambda _: ({"C": 1, "R": 0, "W": 0, "E": 1}, {}))
    record = {"verdict": "indeterminate", "total_cycles": 0,
              "integrity": {name: 0 for name in h.INTEGRITY_ZERO}}
    record["integrity"]["orphan_reads"] = 1
    monkeypatch.setattr(h.subprocess, "run", lambda *_a, **_kw: SimpleNamespace(
        returncode=3, stdout=json.dumps({"results": [record]}).encode(), stderr=b""))
    with pytest.raises(RuntimeError, match="trace integrity failed"):
        h._verify_trace(tmp_path, tmp_path, 1, "", build, "trace")


def test_plot_series_uses_all_points_median_and_range():
    from tools.plotting.plot_vhash_cicada_hot_block import _series
    data = {"cells": {"rr5": {"post-k1/stock": {"points": [
        {"ratio": value} for value in (1, 2, 3, 20)]}}}}
    x, centers, errors, points = _series(data, ["rr5"], "post-k1/stock")
    assert x == [0]
    assert centers == [2.5]
    assert errors == [[1.5], [17.5]]
    assert points == [(0, 1), (0, 2), (0, 3), (0, 20)]


def test_m1_non_perf_record_never_enters_table():
    raw = jobs()
    raw[-1]["records"][0]["throughput"] = 10**9
    raw[-2]["records"][0]["throughput"] = 10**9
    values = aggregate(raw)["cells"]["rr5"]["B-k1/stock"]
    assert len(values["points"]) == 4
    assert values["median"] < 2


def test_m4_missing_and_duplicate_fail_closed():
    missing = deepcopy(jobs())
    missing[0]["records"].pop()
    with pytest.raises(ValueError, match="missing perf runs"):
        aggregate(missing)
    duplicate = deepcopy(jobs())
    duplicate[0]["records"].append(deepcopy(duplicate[0]["records"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(duplicate)


def test_sha_mismatch_fails_closed():
    raw = jobs()
    raw[1]["records"][0]["binary_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="sha256 mismatch"):
        aggregate(raw)


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
    payload = count_json("B-k1")
    stdout = "throughput[tps]: 1\n" + h.COUNT_PREFIX + json.dumps(payload["variant"]) + "\n"
    assert h.parse_count(stdout, "B-k1") == payload
    totals = next(r["count"] for r in aggregate(jobs())["count"]
                  if r["arm"] == "B-k1")
    assert totals["hot"] == 3
    assert totals["hops"] == [0, 0, 0, 0, 3, 0, 0]
    assert totals["snapshot_lag_cycles"][2] == 1
    assert totals["install_hold_cycles_per_update_commit"] == 21
    assert totals["install_wait_cycles_per_update_commit"] == 7
    assert totals["realized_ro_commit_fraction"] == pytest.approx(1 / 3)
    assert "install_hold_cycles / update_commit" in h.COUNT_DERIVED[
        "install_hold_cycles_per_update_commit"]
    payload["variant"]["workers"][0]["hops"].pop()
    with pytest.raises(ValueError, match="COUNT bucket"):
        h.aggregate_count(payload["variant"], "B-k1")


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


def test_m9_shared_binary_failure_stops_without_rebuild(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"changed")
    manifest = {"pin": h.PIN, "builds": {"count-stock": {"path": str(binary),
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "runtime_dependencies": {}}}}
    monkeypatch.setattr(h, "compute_only", lambda: None)
    monkeypatch.setattr(h, "probe", lambda: {})
    monkeypatch.setattr(h, "_load_manifest", lambda _: manifest)
    monkeypatch.setattr(h, "plan_count", lambda *_: [{"build": "count-stock"}])
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
    manifest = {"builds": {"perf-stock": {"path": str(binary),
        "sha256": digest, "runtime_dependencies": {"/lib/old.so": digest}}}}
    monkeypatch.setattr(h, "runtime_dependency_paths", lambda _: ["/lib/new.so"])
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-stock"])


def test_shared_dependency_hash_checked_after_resolution(tmp_path, monkeypatch):
    binary = tmp_path / "bench"
    binary.write_bytes(b"expected")
    dependency = tmp_path / "lib.so"
    dependency.write_bytes(b"changed")
    manifest = {"builds": {"perf-stock": {"path": str(binary),
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "runtime_dependencies": {str(dependency): hashlib.sha256(b"original").hexdigest()}}}}
    monkeypatch.setattr(h, "runtime_dependency_paths", lambda _: [dependency])
    assert "runtime dependency sha256 mismatch" in h.sharing_preflight(manifest, ["perf-stock"])
    dependency.unlink()
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-stock"])
    def unresolved(_):
        raise RuntimeError("unresolved binary dependency: lib.so => not found")
    monkeypatch.setattr(h, "runtime_dependency_paths", unresolved)
    assert "ldd dependency resolution mismatch" in h.sharing_preflight(manifest, ["perf-stock"])


def test_broken_aggregate_four_classification_boundaries():
    raw = jobs()
    broken = [r for r in raw[-2]["records"] if r["build_kind"] == "broken"][:4]
    for record, clean, detected in zip(broken, (True, False, False, True),
                                       (True, True, False, False)):
        trace = record["trace"]
        trace["clean"] = clean
        trace["integrity"] = {"orphan_reads": 0 if clean else 2}
        trace["rows"] = {"C": 1}
        trace["expected_commits"] = 1
        if detected:
            trace.update(rc=1, total_cycles=1, verdict="non-serializable")
            trace["break"]["fired"]["committed"] = 1
            trace["break"]["witness_count"] = 1
    result = aggregate(raw)
    expected = ("detected-attributed-clean", "detected-attributed-integrity-violation",
                "integrity-violation-only", "not-detected")
    for record, name in zip(broken, expected):
        item = result["broken"][record["build"] + ":" + record["cell"]]
        assert item["classification"] == name
        assert item["classification_condition"] == result["broken_classification_conditions"][name]
        assert item["integrity_state"]["clean"] is record["trace"]["clean"]
        if not record["trace"]["clean"]:
            assert item["integrity_state"]["violations"] == {"orphan_reads": 2}


def test_m11_broken_integrity_violation_does_not_stop_trace_job(tmp_path, monkeypatch):
    specs = [{"build": "broken-B1", "cell": "T1"},
             {"build": "broken-B2", "cell": "T2"}]
    manifest = {"builds": {spec["build"]: {"patch_order": [], "patch_sha256": {}}
                           for spec in specs}}
    monkeypatch.setattr(h, "compute_only", lambda: None)
    monkeypatch.setattr(h, "probe", lambda: {})
    monkeypatch.setattr(h, "_load_manifest", lambda _: manifest)
    monkeypatch.setattr(h, "plan_trace", lambda *_: specs)
    monkeypatch.setattr(h, "sharing_preflight", lambda *_: None)
    monkeypatch.setattr(h, "strict_patches", lambda *_: None)
    monkeypatch.setattr(h, "_trace_rows", lambda _: ({"C": 1, "R": 1, "W": 0, "E": 1}, {}))
    @contextmanager
    def checkout(_pin):
        yield str(tmp_path)
    monkeypatch.setattr(h.patchharness, "checkout", checkout)
    results = iter([
        {"verdict": "non-serializable", "total_cycles": 1,
         "integrity": {"orphan_reads": 2}, "notes": ["orphan read"]},
        {"verdict": "indeterminate", "total_cycles": 0,
         "integrity": {k: 0 for k in h.INTEGRITY_ZERO}, "notes": []},
    ])
    def verify(*_args, **_kwargs):
        result = next(results)
        return SimpleNamespace(returncode=1 if result["total_cycles"] else 3,
                               stdout=json.dumps({"results": [result]}).encode(), stderr=b"")
    monkeypatch.setattr(h.subprocess, "run", verify)
    def run_one(_manifest, spec, *, scratch, source):
        slug = "stale-hot" if spec["build"] == "broken-B1" else "skip-pending"
        trace = h._verify_trace(scratch, source, 1,
            f"CICADA_BREAK_FIRED slug={slug} reached=0 changed=0 committed=0\n"
            "CICADA_TRACE_INITIAL_WTS=1\n", spec["build"], "broken")
        return {"build": spec["build"], "trace": trace}
    monkeypatch.setattr(h, "run_one", run_one)
    args = SimpleNamespace(command="trace", output=tmp_path, scratch_root=tmp_path,
                           selection=None, job_index=0)
    job = h._run_job(args)
    assert len(job["records"]) == 2
    first, second = job["records"]
    assert first["trace"]["clean"] is False
    assert first["trace"]["integrity"]["orphan_reads"] == 2
    assert first["trace"]["notes"] == ["orphan read"]
    assert first["trace"]["rows"]["C"] == 1
    assert first["trace"]["break"]["witness_count"] == 0
    assert second["trace"]["clean"] is True
    assert len(json.loads((tmp_path / "raw-trace-0.json").read_text())["records"]) == 2
