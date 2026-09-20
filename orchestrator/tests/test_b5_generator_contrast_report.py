"""Independent statistical examples and authoritative JSON ledger fixtures."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import b5_generator_contrast_report as R

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
ARMS = ("llm", "random", "sweep-matched")
KEYS = tuple((w, b) for w in WORKLOADS for b in ARMS[1:])
FIELDS = ("a b logical_slot attempt slot_key proposal_path proposal_sha256 provenance campaign_id "
          "campaign_root variant build_attempt_id wal_sha256 outcome failure_class quality fitness_tps "
          "anomalies whiteboard_entry timing note").split()
STOCK_VARIANT = hashlib.sha256(
    b"silo|BACKOFF_FIXED=-1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
).hexdigest()[:12]


def ledger(arm="llm", series=1, workload="write-heavy", purpose="registered", score=200, fallback=False):
    block = (series - 1) // 4 + 1 if arm != "stock" else series
    h = dict(schema="b5-generator-contrast-ledger/v1", cohort="synthetic-registration", purpose=purpose,
             arm=arm, workload=workload, series=series, block=block,
             mode="block-stock" if arm == "stock" else "series", repo_head="f" * 40, pin="pinned",
             perf_config={"reps": 5}, verify_mode="legacy+performance", bench_max_rounds=3,
             A=30, B=10, N_eval=5, job={"PBS_JOBID": "fixture", "host": "fixture", "Elapse": 400},
             tier0_status="not-implemented", limits=[])
    events = []
    def add(kind, **kw):
        e = dict.fromkeys(FIELDS)
        e.update(event_seq=len(events) + 1, kind=kind, ts_utc="2026-09-20T10:00:00+00:00", **kw)
        events.append(e)
        return e
    def session(kind, slot, n, value, tps):
        key = f"b5-generator-contrast-v1|synthetic-registration|{arm}|{workload}|{series}|{slot}|{n}|attempt-0"
        return add(kind, a=10 if slot != "block-stock" else 0, b=10 if slot != "block-stock" else 0,
                   logical_slot=f"{slot}-{n}", attempt=0, slot_key=key, value=value,
                   proposal_path="proposal.json", proposal_sha256="d" * 64, provenance={},
                   campaign_id=key, campaign_root="/synthetic/" + key, variant=STOCK_VARIANT if value == -1 else "variant",
                   src_token="stock" if value == -1 else "candidate", outcome="certified", quality="normal",
                   fitness_tps=tps, anomalies=0, bench_payload={"rounds": 1, "tps": [tps] * 5,
                                                              "median_tps": tps, "settled": True, "unstable": False},
                   timing={"subprocess_wall_s": 60, "build_wall_s": 10, "bench_wall_s": 30,
                           "bench_surrounding_wall_s": 32, "verify_total_wall_s": 15,
                           "verify_intervals": [{"tag": "legacy", "wall_s": 3}],
                           "verify_missing_reps": 0, "verify_truncated": False})
    add("series-start", a=0, b=0)
    if arm == "stock":
        for i in range(1, 6):
            session("stock-start", "block-stock", i, -1, score)
        add("series-end", a=0, b=0, reason="b-complete")
    else:
        session("stock-start", "stock-start", 1, -1, 100)
        e = session("evaluation-result", "search", 1, 20, 9999)
        if fallback:
            e.update(outcome="build-failed", fitness_tps=None, quality=None)
        add("endpoint-fixed", a=10, b=10, endpoint=None if fallback else deepcopy(e),
            fallback="pending-block-stock" if fallback else None)
        if not fallback:
            for i in range(1, 6):
                session("score-session", "score", i, 20, score)
        add("series-end", a=10, b=10, reason="b-complete", score=None if fallback else score,
            score_sessions=[] if fallback else [score] * 5, fallback="pending-block-stock" if fallback else None)
    return {"header": h, "events": events}


def registered(llm=200, random=100, sweep=100):
    return [ledger(a, r, w, score={"llm": llm, "random": random, "sweep-matched": sweep}[a])
            for w in WORKLOADS for a in ARMS for r in range(1, 13)] + [
                ledger("stock", b, w, score=100) for w in WORKLOADS for b in (1, 2, 3)]


def save(tmp_path, doc, name="ledger"):
    root = tmp_path / name
    root.mkdir()
    (root / "events").mkdir()
    (root / "header.json").write_text(json.dumps(doc["header"]))
    for e in doc["events"]:
        (root / "events" / f"{e['event_seq']:06d}-{e['kind']}.json").write_text(json.dumps(e))
    (root / "series.json").write_text('{"score": 999999999}')
    return root


def pairs(difference=0.1):
    return [dict(series=i, block=(i - 1) // 4 + 1, difference=difference,
                 fallback_arms=[], endpoint_cvs=[0.01, 0.01]) for i in range(1, 13)]


def decide(ps=None, **kw):
    kwargs = dict(floor={"f": 0.03, "delta": math.log(1.03)},
                  certified_counts={"llm": 12, "random": 12}, baseline="random", significant=True)
    kwargs.update(kw)
    return R.decide_comparison(pairs() if ps is None else ps, **kwargs)


def test_sign_flip_equal_absolute_fixed_counts():
    assert R.exact_sign_flip_p([1] * 11 + [-1]) == Fraction(13, 4096)
    assert R.exact_sign_flip_p([1] * 10 + [-1] * 2) == Fraction(79, 4096)
    assert R.exact_sign_flip_p([1] * 12) == Fraction(1, 4096)
    assert R.exact_sign_flip_p([0] * 12) == 1
    assert R.exact_sign_flip_p([-1] * 12) == 1


def test_sign_flip_independent_small_enumeration_and_inclusive_ties():
    data = [2, -3, 5, 0]
    tail = 0
    for mask in range(16):
        total = 0
        for i in range(4):
            total += -data[i] if mask & (1 << i) else data[i]
        tail += total >= 4
    # Totals >=4 are 4, 6, 10, each twice because the fourth value is zero.
    assert tail == 6
    assert R.exact_sign_flip_p(data) == Fraction(6, 16)
    assert R.exact_sign_flip_p([0.1, -0.1]) == Fraction(3, 4)


@pytest.mark.parametrize("data", [[], [1] * 13, [float("inf")], [float("nan")]])
def test_sign_flip_rejects_invalid_sample(data):
    with pytest.raises((ValueError, OverflowError)):
        R.exact_sign_flip_p(data)


def test_holm_fixed_six_kills_m16():
    # 0.009 passes 0.05/5 but FAILS the registered 0.05/6.
    result = R.holm_six({KEYS[0]: Fraction(9, 1000)})
    assert len(result) == 6
    assert result[KEYS[0]]["adjusted_p"] == Fraction(54, 1000)
    assert result[KEYS[0]]["significant"] is False
    assert result[KEYS[0]]["threshold"] == Fraction(1, 120)
    assert all(result[k]["raw_p"] == 1 for k in KEYS[1:])


def test_holm_stage_threshold_and_family_dependence():
    p = {k: Fraction(1, 4096) for k in KEYS[:2]}
    p[KEYS[3]] = Fraction(1, 64)
    assert not R.holm_six(p)[KEYS[3]]["significant"]
    p[KEYS[2]] = Fraction(1, 4096)
    r = R.holm_six(p)
    assert r[KEYS[3]]["significant"]
    assert r[KEYS[3]]["adjusted_p"] == Fraction(3, 64)
    assert sorted(r[k]["threshold"] for k in KEYS) == [Fraction(1, 120), Fraction(1, 100),
              Fraction(1, 80), Fraction(1, 60), Fraction(1, 40), Fraction(1, 20)]


def test_holm_unavailable_holes_and_stepdown_stop():
    raw = {KEYS[0]: Fraction(9, 1000), KEYS[1]: Fraction(95, 10000), KEYS[2]: float("nan")}
    result = R.holm_six(raw)
    assert result[KEYS[2]]["raw_p"] == 1
    assert not result[KEYS[1]]["significant"]
    assert result[KEYS[1]]["adjusted_p"] == Fraction(54, 1000)


def test_stock_floor_four_cvs_and_sample_denominator():
    blocks = {1: [80, 90, 100, 110, 120], 2: [100] * 5, 3: [100] * 5}
    r = R.stock_cv_floor(blocks)
    assert r["cv_all"] == pytest.approx(math.sqrt(1000 / 14) / 100)
    assert r["cv_block"][1] == pytest.approx(math.sqrt(250) / 100)
    assert r["cv_stock"] == r["cv_block"][1]
    assert r["f"] == r["cv_stock"]
    assert r["delta"] == math.log1p(r["f"])
    blocks = {1: [100] * 5, 2: [200] * 5, 3: [300] * 5}
    r = R.stock_cv_floor(blocks)
    assert r["cv_stock"] == pytest.approx(math.sqrt(100000 / 14) / 200)
    assert r["cv_stock"] == r["cv_all"]
    assert R.stock_cv_floor({b: [100] * 5 for b in (1, 2, 3)})["f"] == 0.03


@pytest.mark.parametrize("blocks", [{1: [100] * 5}, {1: [0] * 5, 2: [1] * 5, 3: [1] * 5},
                                   {1: [float("inf")] * 5, 2: [1] * 5, 3: [1] * 5}])
def test_floor_missing_or_nonfinite(blocks):
    with pytest.raises(ValueError):
        R.stock_cv_floor(blocks)


def test_precision_boundary_equality_is_accepted():
    ps = pairs()
    ps[0]["endpoint_cvs"] = [0.06]
    assert decide(ps)["judgment"] == "conditional-superiority"
    ps[0]["endpoint_cvs"] = [math.nextafter(0.06, math.inf)]
    assert decide(ps)["judgment"] == "indeterminate-precision"


def test_fallback_one_to_two_recomputes_all_statistics():
    ps = pairs(0.1)
    ps[0].update(difference=-100, fallback_arms=["llm"])
    one = decide(ps)
    assert one["analysis"] == "primary"
    assert one["raw_p"] != Fraction(1, 2048)
    ps[1].update(difference=-100, fallback_arms=["random"])
    two = decide(ps)
    assert two["analysis"] == "secondary"
    assert two["raw_p"] == Fraction(1, 1024)
    assert two["secondary"]["median"] == 0.1
    assert two["secondary"]["block_medians"] == {1: 0.1, 2: 0.1, 3: 0.1}
    assert two["primary"]["block_medians"][1] == -49.95
    assert two["excluded_count"] == 2
    assert two["excluded_pairs"] == [{"series": 1, "arms": ["llm"]}, {"series": 2, "arms": ["random"]}]
    assert two["population"] == "候補を採用できた系列の対に限った"


def test_secondary_five_pairs_and_empty_block():
    ps = pairs()
    for i in range(7):
        ps[i]["fallback_arms"] = ["llm" if i % 2 else "random"]
    assert decide(ps, certified_counts={"llm": 9, "random": 8})["judgment"] == "indeterminate-pairs"
    ps = pairs()
    for p in ps[:4]:
        p["fallback_arms"] = ["random"]
    assert decide(ps, certified_counts={"llm": 12, "random": 8})["judgment"] == "indeterminate-pairs"


def test_order_protocol_before_missing_before_generation_before_precision():
    ps = pairs()
    ps[0]["endpoint_cvs"] = [10]
    opts = dict(invalid=True, missing=True, certified_counts={"llm": 0, "random": 0})
    assert decide(ps, **opts)["judgment"] == "protocol-nonconforming"
    opts["invalid"] = False
    assert decide(ps, **opts)["judgment"] == "indeterminate-missing"
    opts["missing"] = False
    assert decide(ps, **opts)["judgment"] == "generation-failed-both"
    opts["certified_counts"] = {"llm": 12, "random": 5}
    assert decide(ps, **opts)["judgment"] == "generation-failed-random"
    opts["certified_counts"] = {"llm": 6, "random": 6}
    assert decide(ps, **opts)["judgment"] == "indeterminate-precision"
    for p in ps:
        p["fallback_arms"] = ["random"]
    assert decide(ps, certified_counts={"llm": 0, "random": 0})["judgment"] == "generation-failed-both"
    assert decide(ps, **opts)["judgment"] == "indeterminate-pairs"


def test_later_decision_order_and_equivalence_is_not_nonsignificance():
    assert decide()["judgment"] == "conditional-superiority"
    assert decide()["qualification"] == "登録した独立性の仮定の下で"
    assert decide(pairs(0), significant=False)["judgment"] == "equivalent-within-floor"
    assert decide(pairs(math.log(1.03)))["judgment"] == "equivalent-within-floor"
    assert decide(pairs(-math.log(1.03)))["judgment"] == "equivalent-within-floor"
    assert decide(pairs(-0.1))["judgment"] == "reverse-descriptive-difference"
    assert decide(significant=False)["judgment"] == "indeterminate-remaining"
    ps = pairs()
    for p in ps[:4]:
        p["difference"] = -0.01
    assert decide(ps)["judgment"] == "indeterminate-remaining"


@pytest.mark.parametrize("llm,expected", [(200, "conditional-superiority"), (100, "equivalent-within-floor"),
                                          (50, "reverse-descriptive-difference")])
def test_registered_twelve_pairs_three_blocks(llm, expected):
    result = R.build_report(registered(llm), purpose="registered")
    assert result["invalid"] == []
    assert len(result["cells"]) == 9 and len(result["comparisons"]) == 6
    assert {c["judgment"] for c in result["comparisons"]} == {expected}
    for c in result["comparisons"]:
        assert c["primary"]["n"] == 12
        assert c["primary"]["block_medians"] == pytest.approx({b: math.log(llm / 100) for b in (1, 2, 3)})
        assert c["certified_endpoint_counts"] == {"llm": 12, c["baseline"]: 12}
    assert result["all_workloads_superiority"] == (llm == 200)


def test_one_baseline_win_is_not_workload_superiority():
    result = R.build_report(registered(200, 100, 200), purpose="registered")
    assert not result["all_workloads_superiority"]
    for w in result["workloads"].values():
        assert w == {"conditional_superiority": False, "llm_specific_gain_not_shown": True}
    assert [c["judgment"] for c in result["comparisons"]] == ["conditional-superiority", "equivalent-within-floor"] * 3


def test_pilot_json_descriptive_only_kills_m17(tmp_path):
    docs = [ledger(a, purpose="pilot") for a in ARMS] + [ledger("stock", purpose="pilot", score=100)]
    roots = [save(tmp_path, d, str(i)) for i, d in enumerate(docs)]
    result = R.build_report(roots, purpose="pilot")
    assert result["invalid"] == []
    assert result["registered_judgment"] == "not-applicable-pilot"
    assert not {"comparisons", "floors", "workloads", "all_workloads_superiority"} & result.keys()
    assert result["block_stock"][0]["descriptive_cv"] == 0
    s = result["series"][0]
    assert (s["A"], s["B"], s["logical_sessions"], s["physical_attempts"]) == (10, 10, 7, 7)
    assert s["score"] == 200 and s["endpoint"]["fitness_tps"] == 9999
    assert s["timing"]["subprocess_wall_s"]["max"] == 60
    assert s["job_elapse"] == 400
    assert s["llm_turn_seconds"]["missing"]
    out = tmp_path / "report.json"
    args = ["--purpose", "pilot", "--out", str(out), "--block-stock-root", str(roots[-1])]
    for root in roots[:-1]:
        args.extend(["--ledger-root", str(root)])
    assert R.main(args) == 0
    assert json.loads(out.read_text())["registered_judgment"] == "not-applicable-pilot"


def test_fresh_median_not_search_max_and_slow_endpoint_not_replaced():
    doc = ledger(score=50)
    values = [10, 40, 50, 60, 100]
    for e, x in zip((e for e in doc["events"] if e["kind"] == "score-session"), values):
        e["fitness_tps"] = x
    result = R.build_report([doc], purpose="registered")
    assert result["invalid"] == []
    s = result["series"][0]
    assert s["score"] == 50 and not s["fallback"]
    # Deviations from 52: -42,-12,-2,8,48; squares sum to 4280.
    assert s["endpoint_cv"] == pytest.approx(math.sqrt(4280 / 4) / 52)


def test_anomaly_cross_arm_cross_series_order_independent_and_workload_local():
    docs = [ledger(), ledger("random", 2), ledger(workload="balanced"), ledger("stock", score=100)]
    anomaly = docs[1]["events"][2]
    anomaly.update(outcome="anomaly", anomalies=1, quality=None, fitness_tps=None)
    docs[1]["events"][3]["endpoint"] = None
    docs[1]["events"][3]["fallback"] = "pending-block-stock"
    docs[1]["events"] = docs[1]["events"][:4] + [docs[1]["events"][-1]]
    docs[1]["events"][-1].update(event_seq=5, score=None)
    before = deepcopy(docs)
    result = R.build_report(docs, purpose="registered")
    assert result["invalid"] == []
    assert docs == before
    a, b, other = result["series"]
    assert a["fallback"] and b["fallback"] and a["score"] == b["score"] == 100
    assert not a["certified_endpoint"] and not b["certified_endpoint"]
    assert other["score"] == 200 and not other["fallback"]
    assert a["events"][2]["outcome"] == "certified"
    assert result["corrections"][0]["type"] == "結果の訂正"
    assert result["corrections"][0]["reported_at"]
    reverse = R.build_report(list(reversed(docs)), purpose="registered")
    assert sorted((s["arm"], s["series"], s["workload"], s["score"]) for s in result["series"]) == sorted(
        (s["arm"], s["series"], s["workload"], s["score"]) for s in reverse["series"])


@pytest.mark.parametrize("outcome,quality,expected", [("machine-failure", None, "machine-missing"),
                  ("certified", "quality-missing", "quality-missing"), ("submitted-unresolved", None, "unclassified-missing")])
def test_missing_score_never_uses_fallback(outcome, quality, expected):
    doc = ledger()
    doc["events"][4].update(outcome=outcome, quality=quality, fitness_tps=None)
    doc["events"][-1]["score"] = None
    result = R.build_report([doc, ledger("stock", score=100)], purpose="registered")
    s = result["series"][0]
    assert s["score"] is None and not s["fallback"] and s["missing"] == expected
    assert result["comparisons"][0]["raw_p"] == 1
    assert result["comparisons"][0]["p_is_unavailable_placeholder"]


@pytest.mark.parametrize("mutation,category", [("schema", "schema-inconsistent"), ("duplicate", "slot-duplicate"),
        ("attempt", "attempt-unowned"), ("early", "score-before-endpoint"), ("nan", "nonfinite-score")])
def test_invalid_categories_fail_closed_without_exception(mutation, category):
    doc = ledger()
    if mutation == "schema":
        doc["header"]["schema"] = "wrong"
    elif mutation == "duplicate":
        doc["events"][5].update({k: doc["events"][4][k] for k in ("logical_slot", "attempt", "slot_key", "campaign_id")})
    elif mutation == "attempt":
        doc["events"][4]["slot_key"] = "unowned"
    elif mutation == "early":
        doc["events"][3], doc["events"][4] = doc["events"][4], doc["events"][3]
        for i, e in enumerate(doc["events"], 1):
            e["event_seq"] = i
    else:
        doc["events"][4]["fitness_tps"] = float("nan")
    result = R.build_report([doc], purpose="registered")
    assert category in {x["category"] for x in result["invalid"]}
    assert result["comparisons"][0]["judgment"] == "protocol-nonconforming"
    assert all(c["raw_p"] == 1 for c in result["comparisons"])


def test_missing_json_and_duplicate_series(tmp_path):
    result = R.build_report([tmp_path / "absent"], purpose="registered")
    assert result["invalid"][0]["category"] == "schema-inconsistent"
    result = R.build_report([ledger(), ledger()], purpose="registered")
    assert "slot-duplicate" in {x["category"] for x in result["invalid"]}


def test_submission_duplicates_do_not_double_count_attempts():
    doc = ledger(purpose="pilot")
    original = deepcopy(doc["events"][2])
    original["kind"] = "pipeline-submitted"
    doc["events"].insert(2, original)
    for i, e in enumerate(doc["events"], 1):
        e["event_seq"] = i
    doc["events"][4]["endpoint"] = deepcopy(doc["events"][3])
    result = R.build_report([doc], purpose="pilot")
    assert result["invalid"] == []
    assert result["series"][0]["physical_attempts"] == 7
    assert result["series"][0]["logical_sessions"] == 7


def test_pilot_cannot_be_relabelled_registered():
    result = R.build_report([ledger(purpose="pilot")], purpose="registered")
    assert result["invalid"]
    assert result["comparisons"][0]["judgment"] == "protocol-nonconforming"
    assert not result["all_workloads_superiority"]


def test_a1_opportunity_before_physical_attempt_and_retry_accounting():
    doc = ledger(purpose="pilot")
    opportunity = dict.fromkeys(FIELDS)
    opportunity.update(kind="proposal-opportunity", logical_slot="search-1", a=1, b=0,
                       ts_utc="2026-09-20T10:00:00+00:00")
    retry = deepcopy(doc["events"][2])
    retry.update(kind="machine-retry", outcome="machine-failure", quality=None, fitness_tps=None)
    terminal = doc["events"][2]
    terminal.update(attempt=1, slot_key=terminal["slot_key"].replace("attempt-0", "attempt-1"))
    doc["events"][2:2] = [opportunity, retry]
    for i, e in enumerate(doc["events"], 1):
        e["event_seq"] = i
    doc["events"][5]["endpoint"] = deepcopy(terminal)
    result = R.build_report([doc], purpose="pilot")
    assert result["invalid"] == []
    s = result["series"][0]
    assert s["logical_sessions"] == 7 and s["physical_attempts"] == 8
    assert s["timing"]["session_by_outcome"]["machine-failure"]["count"] == 1


@pytest.mark.parametrize("field,value", [("timing", []), ("logical_slot", {}),
                                       ("campaign_id", []), ("kind", []), ("value", {})])
def test_malformed_event_shapes_report_invalid(field, value):
    doc = ledger()
    doc["events"][4][field] = value
    result = R.build_report([doc], purpose="registered")
    assert result["invalid"]
    assert result["comparisons"][0]["judgment"] == "protocol-nonconforming"


def test_fallback_uses_shared_block_and_retains_missing_stock():
    docs = [ledger("llm", 5, fallback=True), ledger("random", 5, fallback=True),
            ledger("stock", 1, score=100), ledger("stock", 2, score=321)]
    result = R.build_report(docs, purpose="registered")
    assert result["invalid"] == []
    assert [s["score"] for s in result["series"]] == [321, 321]
    assert all(s["fallback_shared_block_stock"] for s in result["series"])
    result = R.build_report(docs[:-1], purpose="registered")
    assert all(s["score"] is None and s["missing"] == "stock-unestablished" for s in result["series"])


def test_nonfinite_floor_precedes_generation_and_precision():
    result = decide(floor={"f": float("nan"), "delta": float("nan")},
                    certified_counts={"llm": 0, "random": 0})
    assert result["judgment"] == "indeterminate-missing"
    assert result["raw_p"] == 1


def test_score_anomaly_no_reselection_and_stock_anomaly_invalidates_floor():
    doc = ledger()
    doc["events"][4].update(outcome="anomaly", anomalies=1, fitness_tps=None, quality=None)
    doc["events"][-1].update(score=None, fallback="pending-block-stock")
    result = R.build_report([doc, ledger("stock", score=100)], purpose="registered")
    s = result["series"][0]
    assert s["score"] == 100 and s["endpoint_revoked"] and s["failure_condition_a"]
    stock = ledger("stock", score=100)
    stock["events"][1].update(outcome="anomaly", anomalies=1, fitness_tps=None)
    result = R.build_report([ledger(), stock], purpose="registered")
    assert result["series"][0]["missing"] == "stock-unestablished"
    assert result["floors"]["write-heavy"] is None


def test_stock_identity_mismatch_is_not_fallback_data():
    stock = ledger("stock", score=100)
    stock["events"][1]["variant"] = "wrong-stock-identity"
    result = R.build_report([ledger(fallback=True), stock], purpose="registered")
    assert result["series"][0]["missing"] == "stock-unestablished"
    assert result["series"][0]["score"] is None


def test_invalid_comparison_stays_in_family_without_poisoning_other_cells():
    docs = registered()
    doc = next(d for d in docs if d["header"]["arm"] == "random" and d["header"]["workload"] == "write-heavy")
    doc["events"][4]["bench_payload"]["tps"] = None
    report = R.build_report(docs, purpose="registered")
    assert report["invalid"]
    assert report["comparisons"][0]["judgment"] == "protocol-nonconforming"
    assert report["comparisons"][0]["raw_p"] == 1
    assert all(c["judgment"] == "conditional-superiority" for c in report["comparisons"][1:])


@pytest.mark.parametrize("old,new,check", [
    ("(6 - rank) * p[key]", "(5 - rank) * p[key]", "test_holm_fixed_six_kills_m16"),
    ('report["registered_judgment"] = "not-applicable-pilot"',
     'report["registered_judgment"] = "conditional-superiority"', "test_pilot_json_descriptive_only_kills_m17"),
    ("len(omitted) >= 2", "len(omitted) >= 3", "test_fallback_one_to_two_recomputes_all_statistics"),
    ("statistics.stdev(values)", "statistics.pstdev(values)", "test_stock_floor_four_cvs_and_sample_denominator"),
    ('"conditional_superiority": all(', '"conditional_superiority": any(', "test_one_baseline_win_is_not_workload_superiority"),
    ('if invalid:\n', 'if invalid and not missing:\n', "test_order_protocol_before_missing_before_generation_before_precision"),
    ('if failed:\n', 'if failed and not any(cv > 2 * floor["f"] for p in selected for cv in p["endpoint_cvs"]):\n',
     "test_order_protocol_before_missing_before_generation_before_precision"),
], ids=["M16", "M17", "fallback-threshold", "population-cv", "one-baseline", "order-1-2", "order-3-4"])
def test_registered_mutants_killed_independently(monkeypatch, tmp_path, old, new, check):
    # Compile in memory: no writes to the producer or to extra repository files.
    import types
    source = Path(R.__file__).read_text()
    assert old in source
    mutant = types.ModuleType("orchestrator.campaign.b5_report_mutant")
    mutant.__package__ = "orchestrator.campaign"
    mutant.__file__ = R.__file__
    exec(compile(source.replace(old, new), R.__file__, "exec"), mutant.__dict__)
    monkeypatch.setitem(globals(), "R", mutant)
    with pytest.raises(AssertionError):
        if check == "test_pilot_json_descriptive_only_kills_m17":
            globals()[check](tmp_path)
        else:
            globals()[check]()


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
