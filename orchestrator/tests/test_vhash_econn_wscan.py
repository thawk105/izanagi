"""Preregistered md_39 launcher and decision mutation checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from orchestrator.campaign import vhash_econn_wscan as w


def _record(spec, *, insertion=0, rounds=0, detached=0, eligible=1, delayed=1):
    row = {key: 0 for key in w.WSCAN_FIELDS}
    row.update(thid=0, insertion_reached=insertion, rounds_ge2=rounds,
               rounds_max=2 if rounds else 0, detached=detached, eligible=eligible, delayed=delayed,
               reach_both=1 if insertion and rounds else 0,
               detached_reach_both=1 if insertion and rounds and detached else 0)
    return {"spec": spec, "rc": 0, "parse_error": None,
            "counters": {"wscan": {"threads": [row]}}}


def test_patch_stacks_mb2():
    assert w.PATCHES[("count", "pre")] == w.VGT
    assert w.PATCHES[("count", "fix")] == (*w.VGT, w.CAP)
    assert w.PATCHES[("repro", "pre")] == (*w.VGT, w.PROBE)
    assert w.PATCHES[("repro", "fix")] == (*w.VGT, w.PROBE, w.CAP)
    assert w.PATCHES[("repro", "broken")] == (*w.VGT, w.PROBE, w.CAP, w.BROKEN)


def test_matrix_and_shards():
    repro, count = w.plan_runs("repro"), w.plan_runs("count")
    assert len(repro) == 20 and len(count) == 18
    assert len({x["id"] for x in repro}) == 20
    assert sum(x["group"] == "N" for x in repro) == 8
    assert sum(x["group"] == "K1" for x in repro) == 3
    assert sum(x["group"] == "K12" for x in repro) == 9
    assert all({x["variant"] for x in repro[i::4]} >= {"pre", "fix"} for i in range(4))
    assert all({x["variant"] for x in count[i::4]} >= {"pre", "fix"} for i in range(4))
    assert {(x["skew"], x["arm"], x["variant"]) for x in count} == {
        (skew, arm, variant) for skew in (.9, 0) for arm, variant in
        (("E-hb", "pre"), ("E-max", "pre"), ("E-max", "fix"))}


def test_argv_mb3():
    specs = w.plan_runs("repro")
    k12 = next(x for x in specs if x["group"] == "K12")
    k1 = next(x for x in specs if x["group"] == "K1")
    n = next(x for x in specs if x["group"] == "N" and x["delay_us"] == 0)
    a, b, c = (w.argv_for(Path("/tmp/ycsb"), x) for x in (k12, k1, n))
    assert "--cicada_wscan_k2=true" in a and "--cicada_wscan_k1=true" in a
    assert "--cicada_wscan_k2=false" in b and "--cicada_wscan_k1=true" in b
    assert "--cicada_wscan_k2=false" in c and "--cicada_wscan_k1=false" in c
    assert "--cicada_wscan_delay_us=1000" in a and "--cicada_wscan_delay_us=0" in c
    assert "--cicada_gc_target=max" in a
    assert "--cicada_gc_mode=hb" in w.argv_for(Path("/tmp/ycsb"), w.plan_runs("count")[0]) or any(
        "--cicada_gc_mode=hb" in w.argv_for(Path("/tmp/ycsb"), x) for x in w.plan_runs("count"))


def test_counter_schema_missing_field_rejected():
    row = {key: 0 for key in w.WSCAN_FIELDS}
    row["thid"] = 0
    top = dict(schema="CICADA_WSCAN_V1", delay_us=1000, k1=True, k2=True,
               k1_key=1, gc_detach_matches=0, threads=[row])
    assert w._line("CICADA_WSCAN_V1 " + json.dumps(top), "CICADA_WSCAN_V1", w.WSCAN_FIELDS,
                  frozenset(top)) == top
    del row["insertion_reached"]
    try:
        w._line("CICADA_WSCAN_V1 " + json.dumps(top), "CICADA_WSCAN_V1", w.WSCAN_FIELDS,
                frozenset(top))
    except ValueError:
        pass
    else:
        raise AssertionError("missing field accepted")


def test_patch_ordered_wscan_thread_line_parses():
    line = ('CICADA_WSCAN_V1 {"schema":"CICADA_WSCAN_V1","delay_us":1000,'
            '"k1":true,"k2":true,"k1_key":1,"gc_detach_matches":0,"threads":[{'
            '"thid":0,"eligible":1,"delayed":1,"insertion_reached":1,'
            '"rounds_sum":2,"rounds_max":2,"rounds_ge2":1,"detached":1,'
            '"post_scan_detached":0,"probe_aborts":0,"k1_redirects":0,'
            '"k1_read_collisions":0,"k2_flag_raises":0,"reach_both":1,'
            '"detached_reach_both":1}]}')
    spec = next(s for s in w.plan_runs("repro") if s["group"] == "K12")
    with patch.object(w.base, "parse_target_lines", return_value=(None, {}, {})):
        parsed = w.parse_lines(line, "repro", "pre", "E-max", spec)
    assert parsed["wscan"]["threads"][0]["detached_reach_both"] == 1


def test_positive_requires_reach_mb1():
    spec = next(s for s in w.plan_runs("repro") if s["group"] == "K12" and s["variant"] == "pre")
    assert w.repro_verdict("K12", "pre", [_record(spec, detached=1)], False) == "positive_unestablished"
    assert w.repro_verdict("K12", "pre", [_record(spec, insertion=1, rounds=1, detached=1)], False) == "fired"
    assert w.repro_verdict("K12", "pre", [_record(spec, insertion=1, detached=1)], False) == "positive_unestablished"


def test_repair_requires_same_job_trigger_mb4():
    spec = next(s for s in w.plan_runs("repro") if s["group"] == "K12" and s["variant"] == "fix")
    clean = _record(spec, insertion=1, rounds=1)
    assert w.repro_verdict("K12", "fix", [clean], False) == "indeterminate"
    assert w.repro_verdict("K12", "fix", [clean], True) == "repair_success"
    assert w.repro_verdict("K12", "fix", [_record(spec, insertion=1)], True) == "indeterminate"


def test_missing_run_is_not_complete():
    raw = {"job": "repro", "shards": 4, "smoke": False, "runs": []}
    result = w.aggregate([raw])
    assert result["complete"] is False and result["preregistered_success"] is False
    assert len(result["missing"]) == 20
    assert result["arms"]["K12:fix"]["verdict"] == "invalid"


def test_missing_cap_line_cannot_complete_count():
    specs = w.plan_runs("count")
    gc = {"threads": [{key: 0 for key in w.base.GC_THREAD}], "uniform": {
        "count": 1, "negative": 0, "lag_rts_hist": [1] + [0] * 41,
        "lag_rts_sum_us": 1, "lag_rts_max_us": 1, "lag_wts_hist": [1] + [0] * 41,
        "live_sum": 1, "live_max": 1, "argmin_rts_thid": [0], "series": [],
        "series_stride": 1, "max_gap_intervals": 1},
        "retention": {"count": 0, "sum_us": 0, "hist": [0] * 42},
        "publish": {"count": 0, "lag_rts_hist": [0] * 42},
        "begin": {"count": 0, "lag_rts_hist": [0] * 42},
        "live_end": 1, "version_struct_bytes": 64}
    longtx = {"threads": [{"thid": 0, "long": False}]}
    rows = [{"spec": spec, "rc": 0, "parse_error": None,
             "counters": {"gc": gc, "longtx": longtx, "cap": None}}
            for spec in specs]
    result = w.aggregate([{"job": "count", "shards": 1, "shard": 0,
                           "planned_ids": [s["id"] for s in specs], "runs": rows}])
    assert result["complete"] is False
    assert result["arms"]["0.9:E-max:fix"]["diagnostic_instrumented_build"] is None


def _full_record(spec, *, reach=0, fired=0, rounds_max=0):
    record = _record(spec, insertion=reach, rounds=reach, detached=fired)
    row = record["counters"]["wscan"]["threads"][0]
    row["rounds_max"] = rounds_max
    row["reach_both"] = reach
    row["detached_reach_both"] = fired if reach else 0
    patches = list(w.PATCHES[(spec["job"], spec["variant"])])
    record.update(pin="pin", head="head", kind="gc-e-count", genome={"axis": 1},
                  patches=patches, patch_sha256={name: "digest-" + name for name in patches})
    record["counters"].update(gc={"uniform": {"count": 1, "lag_rts_sum_us": 1,
                                              "lag_rts_max_us": 1, "live_sum": 1}},
                              longtx={"threads": []}, cap={"threads": [{key: 0 for key in w.CAP_FIELDS}]})
    return record


def _repro_raws(records, shards=1):
    return [{"job": "repro", "shards": shards, "shard": shard, "extra": False,
             "planned_ids": [s["id"] for s in w.plan_runs("repro")[shard::shards]],
             "runs": [r for r, index in records if index == shard]}
            for shard in range(shards)]


def test_rounds_max_uses_max_mb5():
    specs = w.plan_runs("repro")
    rows = [(_full_record(spec, rounds_max=1), 0) for spec in specs]
    result = w.aggregate(_repro_raws(rows))
    assert result["arms"]["N:pre"]["totals"]["rounds_max"] == 1
    assert result["arms"]["N:pre"]["verdict"] != "P1_refuted"
    target = next(r for r, _ in rows if r["spec"]["group"] == "N" and r["spec"]["variant"] == "pre")
    target["counters"]["wscan"]["threads"][0]["rounds_max"] = 2
    result = w.aggregate(_repro_raws(rows))
    assert result["arms"]["N:pre"]["verdict"] == "P1_refuted"
    assert target["spec"]["id"] in result["arms"]["N:pre"]["p1_run_ids"]


def test_aggregate_rejects_invalid_shard_assignments():
    specs = w.plan_runs("repro")
    rows = [(_full_record(spec), spec["order"] % 2) for spec in specs]
    fix = next(r for r, shard in rows if shard == 1 and r["spec"]["group"] == "K12" and r["spec"]["variant"] == "fix")
    trigger = next(r for r, shard in rows if shard == 1 and r["spec"]["group"] == "K12" and r["spec"]["variant"] == "pre")
    fix["counters"]["wscan"]["threads"][0]["reach_both"] = 1
    trigger["counters"]["wscan"]["threads"][0].update(reach_both=1, detached_reach_both=1, detached=1)
    valid = _repro_raws(rows, 2)
    assert w.aggregate(valid)["arms"]["K12:fix"]["verdict"] == "repair_success"
    for change in (lambda raws: raws[1].pop("shard"),
                   lambda raws: raws[1].pop("shards"),
                   lambda raws: raws[1].update(shard=0),
                   lambda raws: raws[1].update(shard=2),
                   lambda raws: raws[1].update(shards=3),
                   lambda raws: raws[1]["planned_ids"].pop(),
                   lambda raws: raws[1]["runs"].append(raws[0]["runs"].pop())):
        raws = _repro_raws(rows, 2)
        change(raws)
        result = w.aggregate(raws)
        assert result["invalid"] and result["complete"] is False
        assert result["arms"]["K12:fix"]["verdict"] == "invalid"


def test_wscan_top_types_and_argv_mb6():
    spec = next(s for s in w.plan_runs("repro") if s["group"] == "K12")
    row = {key: 0 for key in w.WSCAN_FIELDS}
    top = dict(schema="CICADA_WSCAN_V1", delay_us=spec["delay_us"], k1=True, k2=True,
               k1_key=1, gc_detach_matches=0, threads=[row])
    def parse():
        with patch.object(w.base, "parse_target_lines", return_value=(None, {}, {})):
            return w.parse_lines("CICADA_WSCAN_V1 " + json.dumps(top), "repro", "pre", "E-max", spec)
    assert parse()["wscan"] == top
    for key, bad in (("k1", 1), ("k2", 0), ("delay_us", True), ("k1_key", -1),
                     ("gc_detach_matches", True), ("delay_us", 999), ("k2", False)):
        original = top[key]
        top[key] = bad
        try:
            parse()
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid {key}={bad}")
        top[key] = original


def test_repair_requires_same_shard_mb7():
    specs = w.plan_runs("repro")
    rows = []
    for spec in specs:
        shard = spec["order"] % 2
        rows.append((_full_record(spec, reach=1 if spec["group"] == "K12" and spec["variant"] == "fix" and shard == 1 else 0,
                                  fired=0), shard))
    trigger = next(r for r, shard in rows if shard == 0 and r["spec"]["group"] == "K12" and r["spec"]["variant"] == "pre")
    trigger["counters"]["wscan"]["threads"][0].update(reach_both=1, detached_reach_both=1, detached=1)
    result = w.aggregate(_repro_raws(rows, 2))
    assert result["arms"]["K12:fix"]["verdict"] == "indeterminate"
    same_shard_trigger = next(r for r, shard in rows if shard == 1 and r["spec"]["group"] == "K12" and r["spec"]["variant"] == "pre")
    same_shard_trigger["counters"]["wscan"]["threads"][0].update(reach_both=1, detached_reach_both=1, detached=1)
    result = w.aggregate(_repro_raws(rows, 2))
    assert result["arms"]["K12:fix"]["verdict"] == "repair_success"


def test_run_rejects_mixed_head_before_execution_mb8():
    specs = w.plan_runs("repro")
    receipts = {}
    for variant in {s["variant"] for s in specs}:
        receipts[variant] = (Path("/tmp/binary"), dict(pin="pin", kind="gc-e-count", genome={"axis": 1},
            head="head-a" if variant == "pre" else "head-b", patch_sha256={"shared": "same"},
            gate_receipts=[{"admission": {"admitted": True}} for _ in w.base.MACROS["gc-e-count"]],
            dependency_gate_receipts=[]))
    with patch.object(w, "require_compute"), patch.object(w, "require_external", side_effect=lambda p: Path(p)), \
         patch.object(w, "_binary", side_effect=lambda binaries, job, variant: receipts[variant]), \
         patch.object(w.subprocess, "run", side_effect=AssertionError("binary executed")):
        try:
            w.run("repro", Path("/tmp/builds"), 0, 4, Path("/tmp/raw"))
        except ValueError as exc:
            assert "provenance" in str(exc)
        else:
            raise AssertionError("mixed HEAD accepted")


def test_extra_matrix_and_trigger():
    extra = w.plan_runs("repro", extra=True)
    assert len(extra) == 9 and all(s["group"] == "K12" and s["delay_us"] == 10000 for s in extra)
    assert "--cicada_wscan_delay_us=10000" in w.argv_for(Path("/tmp/ycsb"), extra[0])
    base = w.plan_runs("repro")
    rows = [_full_record(spec) for spec in base]
    assert w.extra_round_required(rows)
    next(r for r in rows if r["spec"]["variant"] == "pre" and r["spec"]["group"] == "K12")["counters"]["wscan"]["threads"][0]["reach_both"] = 1
    assert not w.extra_round_required(rows)


def test_count_mean_uses_sample_count():
    specs = w.plan_runs("count")
    records = []
    for spec in specs:
        record = _full_record(spec)
        uniform = record["counters"]["gc"]["uniform"]
        uniform.update(count=1, lag_rts_sum_us=10, live_sum=20, lag_rts_max_us=10)
        records.append((record, 0))
    target = next(r for r, _ in records if r["spec"]["skew"] == .9 and
                  r["spec"]["arm"] == "E-max" and r["spec"]["variant"] == "fix")
    target["counters"]["gc"]["uniform"].update(count=9, lag_rts_sum_us=900,
                                                  live_sum=1800, lag_rts_max_us=100)
    result = w.aggregate([{"job": "count", "shards": 1, "shard": 0, "extra": False,
                           "planned_ids": [s["id"] for s in specs],
                           "runs": [r for r, _ in records]}])
    metrics = result["arms"]["0.9:E-max:fix"]["diagnostic_instrumented_build"]
    assert metrics == {"lag_rts_mean_us": 920 / 11, "lag_rts_max_us": 100,
                       "live_mean": 1840 / 11}


def test_run_rejects_nonadmitted_gate():
    receipts = [dict(pin="pin", kind="gc-e-count", genome={}, head="head",
                     patch_sha256={"shared": "same"},
                     gate_receipts=[{"admission": {"admitted": False}} for _ in w.base.MACROS["gc-e-count"]],
                     dependency_gate_receipts=[])]
    try:
        w._compare_provenance(receipts)
    except ValueError as exc:
        assert "nonadmitted" in str(exc)
    else:
        raise AssertionError("nonadmitted gate accepted")


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:
                failed += 1
                print("FAIL", name, type(exc).__name__, exc)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
