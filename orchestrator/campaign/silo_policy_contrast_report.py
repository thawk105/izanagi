"""Read-only silo policy contrast report from series and reference ledgers."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import statistics

from .b5_generator_contrast_report import (exact_sign_flip_p, _holm, _cv, stock_cv_floor,
                                            decide_comparison, INDEPENDENCE)
from .silo_policy_contrast import ContrastLedger, LEDGER_SCHEMA, series_state

ARMS = ("llm-cpp", "llm-ir", "random-ir", "evo-ir")
FAMILIES = {"A": (("llm-ir", "random-ir"), ("llm-ir", "evo-ir")),
            "B": (("llm-cpp", "random-ir"), ("llm-cpp", "evo-ir"))}


def _positive(x):
    return type(x) in (float, int) and math.isfinite(x) and x > 0


def _load(roots):
    ledgers = [ContrastLedger(Path(root)) for root in roots]
    identities = set()
    for ledger in ledgers:
        h = ledger.header
        if h["schema"] != LEDGER_SCHEMA or h["arm"] not in (*ARMS, "reference"):
            raise ValueError("invalid ledger header")
        identity = (h["cohort"], h["arm"], h["series"])
        if identity in identities:
            raise ValueError("duplicate series")
        identities.add(identity)
    return ledgers


def _events(ledger, kind):
    return [e for e in ledger.events if e["kind"] == kind]


def _normal(e):
    return e.get("outcome") == "certified" and e.get("quality") == "normal" and _positive(e.get("fitness_tps"))


def _slot_kind(e):
    return e.get("logical_slot", "").split("-")[0]


def _reference(ledgers, disqualified):
    refs = [x for x in ledgers if x.header["arm"] == "reference"]
    if {x.header["series"] for x in refs} != {1, 2, 3}:
        raise ValueError("three reference batches required")
    stock = {}
    fixed = {}
    for l in refs:
        rows = _events(l, "slot-result")
        for key, name in ((stock, "ref-stock"), (fixed, "ref-fixed10")):
            vals = [e["fitness_tps"] for e in rows if e.get("logical_slot", "").startswith(name + "-")
                    and _normal(e) and e.get("variant") not in disqualified]
            if len(vals) == 5:
                key[l.header["series"]] = vals
    return stock, fixed


def _project(ledger, disqualified, stock_values, corrections):
    h = ledger.header
    rows = _events(ledger, "slot-result")
    fixed = _events(ledger, "endpoint-fixed")
    endpoint = fixed[-1] if fixed else None
    variant = endpoint.get("variant") if endpoint else None
    revoked = variant in disqualified if variant is not None else False
    score_rows = [e for e in rows if _slot_kind(e) == "score"]
    if score_rows and (endpoint is None or any(
            e.get("variant") != endpoint.get("variant") or
            e.get("source_digest") != endpoint.get("source_digest")
            for e in score_rows)):
        raise ValueError("score identity differs from fixed endpoint")
    stock_rows = [e for e in rows if _slot_kind(e) == "stock"]
    stock_ok = len(stock_rows) == 1 and _normal(stock_rows[0]) and stock_rows[0].get("variant") not in disqualified
    end = _events(ledger, "series-end")
    reason = end[-1].get("reason") if end else None
    quality_missing = any(e.get("outcome") == "quality-missing" or e.get("quality") == "quality-missing"
                          for e in rows)
    missing = fallback = None
    sessions = []
    if not stock_ok:
        missing = "stock-unestablished"
    elif reason == "machine-retry-exhausted":
        missing = "machine-missing"
    elif endpoint is None or revoked:
        if endpoint is None and quality_missing:
            missing = "quality-missing"
        elif any(e.get("outcome") in {"machine-failure", "unclassified-missing"}
                 for e in rows):
            missing = "unclassified-missing"
        elif len(stock_values) != 15:
            missing = "stock-unestablished"
        else:
            fallback = True
            sessions = stock_values
    elif any(e.get("outcome") == "anomaly" or e.get("anomalies") for e in score_rows):
        if len(stock_values) == 15:
            fallback, sessions = True, stock_values
        else:
            missing = "stock-unestablished"
    elif len(score_rows) == 5 and all(_normal(e) for e in score_rows):
        sessions = [e["fitness_tps"] for e in score_rows]
    else:
        missing = "quality-missing" if quality_missing else "machine-missing" if any(
            e.get("outcome") == "machine-failure" for e in score_rows) else "unclassified-missing"
    if reason not in {"b-complete", "a-exhausted"}:
        missing = missing or "unclassified-missing"
    if revoked:
        corrections.append({"type": "結果の訂正", "reported_at": datetime.now(timezone.utc).isoformat(),
                            "arm": h["arm"], "series": h["series"], "variant": variant})
    search = [e for e in rows if _slot_kind(e) == "eval" and _normal(e) and e.get("variant") not in disqualified]
    seed = [e for e in rows if _slot_kind(e) == "seed" and _normal(e) and e.get("variant") not in disqualified]
    state = series_state(ledger)
    a_used, b_used = state["A"], state["B"]
    rejects = [e for e in _events(ledger, "opportunity-end") if e.get("outcome") == "rejected"]
    reject_breakdown = {}
    reject_rule_breakdown = {}
    for event in rejects:
        key = event.get("reject_subtype") or "unspecified"
        reject_breakdown[key] = reject_breakdown.get(key, 0) + 1
        rule = event.get("reject_rule_id") or "unspecified"
        reject_rule_breakdown[rule] = reject_rule_breakdown.get(rule, 0) + 1
    return {"arm": h["arm"], "series": h["series"], "A": a_used, "B": b_used,
            "end_reason": reason, "unfinished": bool(state["unfinished_slots"]) or reason not in {"b-complete", "a-exhausted"},
            "endpoint": endpoint, "endpoint_revoked": revoked,
            "certified_endpoint": bool(endpoint and not revoked),
            "search_point": bool(search), "endpoint_from_seed": bool(endpoint and _slot_kind(endpoint) == "seed"),
            "search_best_exceeds_seed": bool(search and seed and max(e["fitness_tps"] for e in search) > max(e["fitness_tps"] for e in seed)),
            "score": statistics.median(sessions) if sessions and missing is None else None,
            "score_sessions": sessions, "endpoint_cv": _cv(sessions) if sessions and not fallback and missing is None else None,
            "fallback": bool(fallback), "missing": missing,
            "anomaly_count": sum(e.get("outcome") == "anomaly" or bool(e.get("anomalies")) for e in rows),
            "reject_count": len(rejects), "reject_breakdown": reject_breakdown,
            "reject_rule_breakdown": reject_rule_breakdown,
            "outages": [e for e in _events(ledger, "opportunity-end") if e.get("outcome") == "outage"],
            "unique_variants": len({e.get("variant") for e in rows if e.get("variant") is not None})}


def _pairs(left, right, n):
    a = {x["series"]: x for x in left}
    b = {x["series"]: x for x in right}
    result = []
    for r in range(1, n + 1):
        x, y = a.get(r), b.get(r)
        valid = x and y and _positive(x["score"]) and _positive(y["score"])
        result.append({"series": r, "block": (r - 1) // 4 + 1,
                       "difference": math.log(x["score"] / y["score"]) if valid else None,
                       "fallback_arms": [z["arm"] for z in (x, y) if z and z["fallback"]],
                       "endpoint_cvs": [z["endpoint_cv"] for z in (x, y)
                                        if z and not z["fallback"] and z["endpoint_cv"] is not None]})
    return result


def build_report(roots, *, n: int | None = None):
    ledgers = _load(roots)
    inferred = len([l for l in ledgers if l.header["arm"] == "llm-cpp"])
    if n is None:
        n = inferred
    elif n != inferred:
        raise ValueError("n differs from ledger series count")
    if n not in {10, 12}:
        raise ValueError("n must be 10 or 12")
    if len([l for l in ledgers if l.header["arm"] in ARMS]) != 4 * n:
        raise ValueError("incomplete arm series")
    if len({l.header["cohort"] for l in ledgers}) != 1:
        raise ValueError("mixed cohorts")
    for arm in ARMS:
        if {l.header["series"] for l in ledgers if l.header["arm"] == arm} != set(range(1, n + 1)):
            raise ValueError("missing series")
    disqualified = {e.get("variant") for l in ledgers for e in _events(l, "slot-result")
                    if e.get("variant") is not None and (e.get("outcome") == "anomaly" or e.get("anomalies"))}
    stocks, fixed10 = _reference(ledgers, disqualified)
    pooled = [x for batch in (1, 2, 3) for x in stocks.get(batch, [])]
    try:
        floor = stock_cv_floor(stocks, v2=True)
    except ValueError:
        floor = None
    corrections = []
    series = [_project(l, disqualified, pooled, corrections) for l in ledgers if l.header["arm"] in ARMS]
    by_arm = {arm: [x for x in series if x["arm"] == arm] for arm in ARMS}
    search_counts = {arm: sum(x["search_point"] for x in rows) for arm, rows in by_arm.items()}
    certified_counts = {arm: sum(x["certified_endpoint"] for x in rows) for arm, rows in by_arm.items()}
    comparisons = []
    for family, members in FAMILIES.items():
        inputs = {}
        preliminary = {}
        for x, y in members:
            pairs = _pairs(by_arm[x], by_arm[y], n)
            kwargs = {"floor": floor, "v2": True,
                      # The B-5 core names this parameter after endpoints; this experiment
                      # supplies the preregistered search-point eligibility instead.
                      "certified_counts": {x: search_counts[x], y: search_counts[y]},
                      "missing": any(row["missing"] for row in (*by_arm[x], *by_arm[y]))}
            inputs[x, y] = pairs, kwargs
            preliminary[x, y] = decide_comparison(pairs, **kwargs)
        adjusted = _holm({key: value["raw_p"] for key, value in preliminary.items()}, members)
        for key in members:
            pairs, kwargs = inputs[key]
            decision = decide_comparison(pairs, **kwargs, significant=adjusted[key]["significant"])
            comparisons.append({"family": family, "llm_arm": key[0], "baseline": key[1], **decision,
                                "search_point_series_counts": kwargs["certified_counts"],
                                "certified_endpoint_counts": {arm: certified_counts[arm] for arm in key},
                                "adjusted_p": adjusted[key]["adjusted_p"],
                                "holm_threshold": adjusted[key]["threshold"]})
    stock_median = statistics.median(pooled) if len(pooled) == 15 else None
    fixed_values = [v for batch in (1, 2, 3) for v in fixed10.get(batch, [])]
    fixed_median = statistics.median(fixed_values) if len(fixed_values) == 15 else None
    descriptive = {arm: {"scores": [s["score"] for s in rows],
                         "A_used": sum(s["A"] for s in rows),
                         "reject_breakdown": {key: sum(s["reject_breakdown"].get(key, 0) for s in rows)
                                              for key in sorted({k for s in rows for k in s["reject_breakdown"]})},
                         "reject_rule_breakdown": {key: sum(s["reject_rule_breakdown"].get(key, 0) for s in rows)
                                                   for key in sorted({k for s in rows for k in s["reject_rule_breakdown"]})},
                         "fallback_count": sum(s["fallback"] for s in rows),
                         "missing_count": sum(s["missing"] is not None for s in rows),
                         "seed_endpoint_count": sum(s["endpoint_from_seed"] for s in rows),
                         "search_exceeds_seed_count": sum(s["search_best_exceeds_seed"] for s in rows),
                         "B_not_complete_count": sum(s["B"] < 10 for s in rows),
                         "endpoint_to_stock_ratios": [s["score"] / stock_median if s["score"] is not None and stock_median else None for s in rows],
                         "endpoint_to_fixed10_ratios": [s["score"] / fixed_median if s["score"] is not None and fixed_median else None for s in rows]}
                   for arm, rows in by_arm.items()}
    return {"schema": "silo-policy-contrast-report/v1", "n": n,
            "series": series, "comparisons": comparisons, "floor": floor,
            "descriptive": descriptive,
            "search_point_series_counts": search_counts, "certified_endpoint_counts": certified_counts,
            "disqualified_variants": sorted(disqualified), "corrections": corrections,
            "reference_stock": stocks, "reference_fixed10": fixed10,
            "shared_fallback_stock": len(pooled) == 15,
            "assumption": INDEPENDENCE,
            "llm_cpp_vs_ir": _pairs(by_arm["llm-cpp"], by_arm["llm-ir"], n)}


def _jsonable(x):
    if isinstance(x, Fraction):
        return {"numerator": x.numerator, "denominator": x.denominator, "value": float(x)}
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [_jsonable(v) for v in x]
    return x


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger-root", type=Path, action="append", required=True)
    p.add_argument("--n", type=int, choices=(10, 12))
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    roots = [child.parent for root in args.ledger_root for child in root.rglob("header.json")]
    report = build_report(roots, n=args.n)
    args.out.write_text(json.dumps(_jsonable(report), ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
