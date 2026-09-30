"""Preregistered md_39 launcher and decision mutation checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from orchestrator.campaign import vhash_econn_wscan as w


def _record(spec, *, insertion=0, rounds=0, detached=0, eligible=1, delayed=1):
    row = {key: 0 for key in w.WSCAN_FIELDS}
    row.update(thid=0, insertion_reached=insertion, rounds_ge2=rounds,
               rounds_max=2 if rounds else 0, detached=detached, eligible=eligible, delayed=delayed)
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
    result = w.aggregate([{"job": "count", "shards": 1, "smoke": False, "runs": rows}])
    assert result["complete"] is False
    assert result["arms"]["0.9:E-max:fix"]["diagnostic_instrumented_build"] is None


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
