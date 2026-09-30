"""Workload-space plotter contracts, including pre-registered MB mutations."""
from __future__ import annotations

import json
import copy
import csv
from pathlib import Path
import pytest
from tools.plotting import plot_vhash_workload_space as P
from orchestrator.tests import test_vhash_cicada_vlife as A


def _point():
    return P.design()[0]


def _cid(point, genome="default"):
    return next(cid for cid, condition in P.V.CONDITIONS.items()
                if cid.startswith("W") and cid.endswith("-"+genome)
                and all(P.condition_point(condition)[k] == point[k] for k in P.FACTORS))


def _condition(point, genome="default"):
    return copy.deepcopy(P.V.CONDITIONS[_cid(point, genome)])


def _parsed(point, *, publications=2, deep=2000, commits=2000, candidate=200,
            live_delta=120000, aborts=0):
    payload = A._payload3()
    payload["build"].update(val_size=point["val"],
                            izanagi_ronly_pct=point["ro"],
                            izanagi_long_kind=("none", "batchU", "batchR").index(point["long"]))
    payload["workers"] = [copy.deepcopy(payload["workers"][0])
                          for _ in range(point["threads"])]
    worker = payload["workers"][0]
    worker["position"][0][:2] = [8000, deep]
    worker["position"][1][:2] = [9000, 1000]
    worker["hops"][0][:2] = [8000, deep]
    worker["hops"][1][:2] = [9000, 1000]
    worker["deep"][0] = deep
    worker["candidate"][0] = candidate
    worker["readonly_reads"] = 10000
    worker["attempts"][0] = commits + aborts
    worker["commits"][0] = commits
    worker["aborts"][0] = aborts
    worker["abort_reasons"][0] = aborts
    worker["install"] = live_delta
    worker["gc_boundary_count"] = publications
    worker["gc_boundary_us"][10] = publications
    worker["gc_boundary_sum_us"] = 1024 * publications
    return payload


def _run(point, payload):
    c = _condition(point)
    flags = [f"-{k}={v}" for k, v in {
        "tuple_num": c["records"], "ycsb_tuple_num": c["records"],
        "ycsb_max_ope": c["ycsb_max_ope"], "ycsb_rratio": c["ycsb_rratio"],
        "ycsb_zipf_skew": c["ycsb_zipf_skew"], "gc_inter_us": c["gc_inter_us"],
        "izanagi_ronly_pct": c["izanagi_ronly_pct"],
        "izanagi_long_kind": c["izanagi_long_kind"],
        "thread_num": c["thread_num"], "batch_th_num": c["batch_th_num"]}.items()]
    return {"argv": ["binary", *flags], "rc": 0,
            "stdout": P.V.PREFIX + json.dumps(payload),
            P.SCHEMA3["build_key"]: {"genome": "default", "val_size": point["val"]},
            "parsed": payload, "summary": P.V.summarize(payload),
            P.SCHEMA3["maxrss_kb"]: 123456}


def _install_parser(monkeypatch):
    # Kept as a call site for the original tests; the real parser is in use.
    return None


def _row(point, genome="default", passes=(True, True)):
    vals = []
    for hit in passes:
        vals.append({"H1": hit, "H2": hit, "H4-lag": hit, "H4-live": hit,
                     "h1": .2 if hit else 0, "h2": .1 if hit else 0,
                     "lag_us": 2048 if hit else 1, "live_ratio": 1.2 if hit else 1,
                     "depth8": .01, "abort_rate": .02,
                     "local_flag_opportunity": .2})
    row = {"id": f"W-{point['layer']}-{genome}-{point['skew']}-{point['rr']}-{point['long']}",
           "point": point, "genome": genome, "values": vals}
    row["states"] = {h: P.state([v[h] for v in vals]) for h in P.PREDICATES}
    row["states"]["H4"] = P.state([v["H4-lag"] or v["H4-live"] for v in vals])
    return row


def test_design_is_126_unique_points_and_two_genomes():
    pts = P.design()
    assert len(pts) == 126
    assert sum(p["layer"] == "S" for p in pts) == 72
    assert sum(p["layer"] == "O1" for p in pts) == 27
    assert sum(p["layer"] == "O2" for p in pts) == 27


def test_mb1_raw_reparse_rejects_saved_parsed_mismatch(monkeypatch):
    _install_parser(monkeypatch)
    point = _point()
    run = _run(point, _parsed(point))
    run["parsed"] = {**run["parsed"], "schema_version": 2}
    with pytest.raises(ValueError, match="stdout/parsed mismatch"):
        P._validated_run(run, point, "default")


def test_mb2_one_of_two_repetitions_is_boundary():
    row = _row(_point(), passes=(True, False))
    assert row["states"] == {"H1": "境界", "H2": "境界",
                             "H4-lag": "境界", "H4-live": "境界", "H4": "境界"}
    assert P.state((None, True)) == "判定不能"


def test_mb3_zero_publications_is_censored_pass(monkeypatch):
    _install_parser(monkeypatch)
    point = _point()
    values = P.metrics(P._validated_run(_run(point, _parsed(point, publications=0)),
                                      point, "default"), point["records"])
    assert values["H4-lag"] == "停止"
    assert P.state([values["H4-lag"]]*2) == "停止"


def test_mb4_region_requires_both_genomes():
    points = [p for p in P.design() if p["layer"] == "S"]
    rows = {}
    for p in points:
        for genome, passing in (("default", True), ("tuned", False)):
            row = _row(p, genome, (passing, passing))
            rows[(P._design_key(p), genome)] = row
    selected, insufficient = P.regions(rows)
    assert insufficient
    assert all(c["label"] == "未達" for c in selected)


def test_schema3_adapter_and_negative_build_abort_and_denominator(monkeypatch):
    _install_parser(monkeypatch)
    point = _point()
    payload = _parsed(point)
    run = _run(point, payload)
    assert P._validated_run(run, point, "default")["valid"]
    wrong_key = _run(point, payload)
    wrong_key[P.SCHEMA3["build_key"]]["genome"] = "best100"
    with pytest.raises(ValueError, match="build key"):
        P._validated_run(wrong_key, point, "default")
    bad = json.loads(json.dumps(payload))
    bad["build"][P.SCHEMA3["val_size"]] = 100
    with pytest.raises(ValueError, match="build key"):
        P._validated_run(_run(point, bad), point, "default")
    bad = json.loads(json.dumps(payload))
    bad["workers"][0][P.SCHEMA3["abort_reasons"]][0] = 1
    with pytest.raises(ValueError, match="abort reason"):
        P._validated_run(_run(point, bad), point, "default")
    low = _parsed(point, deep=0, candidate=0)
    for w in low["workers"]:
        w["position"][1] = [0]*18
    low["workers"][0]["position"][0] = [9999]+[0]*17
    low["workers"][0]["hops"][0] = [9999]+[0]*17
    values = P.metrics(P._validated_run(_run(point, low), point, "default"), point["records"])
    assert values["H1"] is None and values["H2"] is None


def test_schema3_abort_sides_and_hot_chain_table(tmp_path):
    point = _point()
    payload = _parsed(point, aborts=5)
    worker = payload["workers"][0]
    worker["aborts"] = [2, 3]
    worker["attempts"] = [2002, 3]
    worker["abort_reasons"] = [2, 3] + [0] * 16
    payload["hot_chains"][0] = {"key": 0, "status": "missing", "length": None}
    rep = P._validated_run(_run(point, payload), point, "default")
    assert rep["reasons"][P.ABORT_REASONS[0]] == {"normal": 2, "long_tx": 3}
    row = {"id": _cid(point), "point": point, "genome": "default",
           "reps": [rep, rep]}
    P.evaluate({"sample": row})
    P.write_tables({"sample": row}, [], True, tmp_path, [])
    with (tmp_path/"abort_reasons.csv").open(newline="") as stream:
        abort_rows = list(csv.DictReader(stream))
    first = next(r for r in abort_rows if r["reason"] == P.ABORT_REASONS[0])
    assert (first["normal"], first["long_tx"], first["total"]) == ("2", "3", "5")
    with (tmp_path/"hot_chains.csv").open(newline="") as stream:
        hot_rows = list(csv.DictReader(stream))
    assert hot_rows[0]["chain_status"] == "missing" and hot_rows[0]["chain_length"] == ""


def test_load_rejects_missing_repetition_duplicate_and_missing_points(tmp_path, monkeypatch):
    _install_parser(monkeypatch)
    point = _point()
    condition = _condition(point)
    run = _run(point, _parsed(point))
    cid = _cid(point)
    path = tmp_path/"one.json"
    raw = {"command": "measure", "schema_version": 3,
           "conditions": {cid: condition}, "runs": {cid: [run, run]}}
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="missing design"):
        P.load([path])
    raw["runs"][cid] = [run]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="fewer than two"):
        P.load([path])
    raw["runs"][cid] = [run, run]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="duplicate condition"):
        P.load([path, path])



def test_full_inventory_accepts_registered_points_and_rejects_duplicate_point(tmp_path, monkeypatch):
    conditions, runs = {}, {}
    for index, point in enumerate(P.design()):
        for genome in ("default", "tuned" if point["ops"] == 10 else "best100"):
            cid = _cid(point, genome)
            conditions[cid] = _condition(point, genome)
            runs[cid] = [{"synthetic": 1}, {"synthetic": 2}]
    monkeypatch.setattr(P, "_validated_run", lambda run, point, genome: {"valid": True})
    path = tmp_path/"full.json"
    path.write_text(json.dumps({"command": "measure", "schema_version": 3,
                                "conditions": conditions, "runs": runs}))
    rows, provenance = P.load([path])
    assert len(rows) == 252 and len(provenance) == 1
    duplicate = json.loads(path.read_text())
    duplicate["conditions"]["W-duplicate"] = conditions[_cid(_point())]
    duplicate["runs"]["W-duplicate"] = runs[_cid(_point())]
    path.write_text(json.dumps(duplicate))
    with pytest.raises(ValueError, match="duplicate point/genome"):
        P.load([path])


def test_real_size_figure_layout_and_artifacts(tmp_path):
    rows = {}
    for point in P.design():
        for genome in ("default", "tuned" if point["ops"] == 10 else "best100"):
            row = _row(point, genome)
            row["id"] = f"W-{len(rows):03d}"
            rows[(P._design_key(point), genome)] = row
    P.draw_skew(rows, tmp_path, [{"sha256": "synthetic"}])
    P.draw_axes(rows, tmp_path, [{"sha256": "synthetic"}])
    assert len(list(tmp_path.glob("*.png"))) == 7
    assert len(list(tmp_path.glob("*.pdf"))) == 7
    assert len(list(tmp_path.glob("*.provenance.json"))) == 7


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
