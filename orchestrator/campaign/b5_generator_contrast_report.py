"""Read-only B-5 ledger consumer; no campaign execution or endpoint selection.

Registered results are conditional on the saved allocation and independence
assumptions. Pilot output deliberately contains descriptive statistics only.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Literal

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import b5_generator_contrast as core

ComparisonKey = tuple[str, str]
COMPARISONS = tuple((w, b) for w in core.WORKLOADS for b in core.ARMS[1:])
INDEPENDENCE = "登録した独立性の仮定の下で"
RESULT_KINDS = {"stock-start", "evaluation-result", "score-session", "proposal-rejected"}


def _positive(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0


def _cv(values):
    values = list(values)
    if len(values) < 2 or not all(_positive(x) for x in values):
        raise ValueError("CV requires finite positive sessions")
    return statistics.stdev(values) / statistics.mean(values)


def exact_sign_flip_p(differences) -> Fraction:
    """Inclusive upper tail of the mean, enumerated without floating tie error."""
    values = [Fraction(x) for x in differences]
    if not 1 <= len(values) <= 12:
        raise ValueError("sign flips require 1..12 pairs")
    observed = sum(values)
    # The common denominator turns sums into integers; dividing by n cancels.
    denominator = math.lcm(*(x.denominator for x in values))
    integers = [x.numerator * (denominator // x.denominator) for x in values]
    target = observed * denominator
    tail = sum(sum(s * x for s, x in zip(signs, integers)) >= target
               for signs in product((-1, 1), repeat=len(values)))
    return Fraction(tail, 2 ** len(values))


def holm_six(raw_p: Mapping[ComparisonKey, Fraction | float]) -> dict:
    """Fixed six-member family, including unavailable tests as computational 1."""
    if set(raw_p) - set(COMPARISONS):
        raise ValueError("unknown comparison")
    p = {}
    for key in COMPARISONS:
        value = raw_p.get(key, 1)
        try:
            value = Fraction(str(value)) if isinstance(value, float) else Fraction(value)
            p[key] = value if 0 <= value <= 1 else Fraction(1)
        except (ValueError, TypeError, OverflowError):
            p[key] = Fraction(1)
    adjusted, running = {}, Fraction(0)
    for rank, key in enumerate(sorted(COMPARISONS, key=lambda k: (p[k], k))):
        running = max(running, min(Fraction(1), (6 - rank) * p[key]))
        adjusted[key] = {"raw_p": p[key], "adjusted_p": running,
                         "significant": running <= Fraction(1, 20),
                         "threshold": Fraction(1, 20 * (6 - rank))}
    return adjusted


def stock_cv_floor(block_stock_sessions) -> dict:
    """The maximum of all 15 sessions' CV and each of three blocks' CV."""
    blocks = dict(block_stock_sessions)
    if set(blocks) != {1, 2, 3} or any(len(v) != core.BLOCK_STOCK_SESSIONS for v in blocks.values()):
        raise ValueError("floor requires three blocks of five sessions")
    cvs = {b: _cv(blocks[b]) for b in (1, 2, 3)}
    all_cv = _cv([x for b in (1, 2, 3) for x in blocks[b]])
    stock = max(all_cv, *cvs.values())
    f = max(0.03, stock)
    return {"cv_all": all_cv, "cv_block": cvs, "cv_stock": stock,
            "f": f, "delta": math.log1p(f)}


def pair_differences(llm, baseline) -> list[dict]:
    """Join projected series by registered series number, preserving omissions."""
    left, right = ({x["series"]: x for x in arm} for arm in (llm, baseline))
    pairs = []
    for r in range(1, 13):
        l, b = left.get(r), right.get(r)
        valid = l is not None and b is not None and _positive(l["score"]) and _positive(b["score"])
        pairs.append({"series": r, "block": l["block"] if l else (r - 1) // 4 + 1,
                      "difference": (math.log(l["score"]) - math.log(b["score"])) if valid else None,
                      "fallback_arms": [x["arm"] for x in (l, b) if x and x["fallback"]],
                      "endpoint_cvs": [x["endpoint_cv"] for x in (l, b)
                                       if x and not x["fallback"] and x["endpoint_cv"] is not None]})
    return pairs


def _analysis(pairs):
    usable = [p for p in pairs if p["difference"] is not None]
    ds = [p["difference"] for p in usable]
    blocks = {b: [p["difference"] for p in usable if p["block"] == b] for b in (1, 2, 3)}
    return {"n": len(ds), "differences": ds,
            "median": statistics.median(ds) if ds else None,
            "block_medians": {b: statistics.median(v) if v else None for b, v in blocks.items()},
            "raw_p": exact_sign_flip_p(ds) if ds else Fraction(1)}


def decide_comparison(pairs, *, floor, certified_counts,
                      invalid=False, missing=False, significant=False) -> dict:
    """Apply preregistration 7.4 in order; Holm is supplied after eligibility."""
    omitted = [p for p in pairs if p["fallback_arms"]]
    secondary_pairs = [p for p in pairs if not p["fallback_arms"]]
    use_secondary = len(omitted) >= 2
    selected = secondary_pairs if use_secondary else pairs
    primary, secondary = _analysis(pairs), _analysis(secondary_pairs)
    chosen = secondary if use_secondary else primary
    result = {"primary": primary, "secondary": secondary,
              "analysis": "secondary" if use_secondary else "primary",
              "excluded_pairs": [{"series": p["series"], "arms": p["fallback_arms"]} for p in omitted],
              "excluded_count": len(omitted), "certified_endpoint_counts": certified_counts,
              "raw_p": Fraction(1), "p_is_unavailable_placeholder": True}
    judgment = None
    if invalid:
        judgment = "protocol-nonconforming"
    elif (missing or any(p["difference"] is None for p in pairs) or floor is None
          or not all(type(floor.get(k)) in (int, float) and math.isfinite(floor[k]) for k in ("f", "delta"))):
        judgment = "indeterminate-missing"
    else:
        failed = [a for a, n in certified_counts.items() if n < 6]
        if failed:
            judgment = "generation-failed-both" if len(failed) == 2 else "generation-failed-" + failed[0]
        elif chosen["n"] < 6 or any(v is None for v in chosen["block_medians"].values()):
            judgment = "indeterminate-pairs"
        elif any(cv > 2 * floor["f"] for p in selected for cv in p["endpoint_cvs"]):
            judgment = "indeterminate-precision"
    if judgment is None:
        result.update(raw_p=chosen["raw_p"], p_is_unavailable_placeholder=False)
        median, delta = chosen["median"], floor["delta"]
        if significant and median > delta and all(x > 0 for x in chosen["block_medians"].values()):
            judgment = "conditional-superiority"
        elif abs(median) <= delta:
            judgment = "equivalent-within-floor"
        elif median < -delta:
            judgment = "reverse-descriptive-difference"
        else:
            judgment = "indeterminate-remaining"
    result["judgment"] = judgment
    if judgment == "conditional-superiority":
        result["qualification"] = INDEPENDENCE
    if use_secondary:
        result["population"] = "候補を採用できた系列の対に限った"
    if judgment == "equivalent-within-floor":
        result["interpretation"] = "観測差が比較 floor 内だった (母集団の等価性の証明ではない)"
    return result


def _load(source, invalid):
    """Load authoritative header/events, never the regenerable series view."""
    label = str(source) if isinstance(source, (str, Path)) else "in-memory-ledger"
    try:
        root = None
        if isinstance(source, (str, Path)):
            root = Path(source)
            header = json.loads((root / "header.json").read_text())
            events = []
            for i, path in enumerate(sorted((root / "events").glob("*.json")), 1):
                event = json.loads(path.read_text())
                if path.name != f"{i:06d}-{event.get('kind')}.json":
                    raise ValueError("event filename/sequence mismatch")
                events.append(event)
        elif isinstance(source, core.SeriesLedger):
            root = source.root
            header, events = source.header, source.events
        else:
            header, events = source["header"], source["events"]
        if not isinstance(header, dict) or not isinstance(events, list):
            raise ValueError("header/events shape")
        return {"header": header, "events": events, "source": label, "root": root}
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        invalid.append({"category": "schema-inconsistent", "source": label, "detail": str(exc)})
        return None


def _validate(ledger, invalid, purpose):
    h, events, source = ledger["header"], ledger["events"], ledger["source"]
    def bad(category, detail):
        invalid.append({"category": category, "source": source, "detail": detail,
                        "workload": h.get("workload"), "arm": h.get("arm")})
    required = {"schema", "cohort", "purpose", "arm", "workload", "series", "block", "mode",
                "repo_head", "pin", "perf_config", "verify_mode", "bench_max_rounds", "A", "B", "N_eval", "job"}
    if (not required <= h.keys() or h.get("schema") != core.LEDGER_SCHEMA
            or h.get("purpose") != purpose or h.get("arm") not in (*core.ARMS, "stock")
            or h.get("workload") not in core.WORKLOADS
            or type(h.get("series")) is not int or h.get("series") not in range(1, 13)
            or type(h.get("block")) is not int or h.get("block") not in (1, 2, 3)
            or not isinstance(h.get("cohort"), str) or not h.get("cohort")
            or not isinstance(h.get("job"), dict) or not isinstance(h.get("perf_config"), dict)
            or (h.get("A"), h.get("B"), h.get("N_eval")) != (core.A_PROPOSALS, core.B_EVALUATIONS, core.N_EVAL)):
        bad("schema-inconsistent", "header contract")
        return False
    stock = h["arm"] == "stock"
    if h["verify_mode"] != "legacy+performance" or h["bench_max_rounds"] != 3:
        bad("schema-inconsistent", "session protocol mismatch")
    if (h["mode"] != ("block-stock" if stock else "series")
            or stock and h["series"] != h["block"]
            or purpose == "registered" and not stock and h["block"] != (h["series"] - 1) // 4 + 1):
        bad("schema-inconsistent", "allocation mismatch")
    fixed, slots, attempts, ended = None, set(), {}, False
    clean = []
    for seq, e in enumerate(events, 1):
        if (not isinstance(e, dict) or not set(core.EVENT_FIELDS) <= e.keys()
                or e.get("event_seq") != seq or not isinstance(e.get("kind"), str) or e.get("kind") not in core.EVENT_KINDS
                or not isinstance(e.get("ts_utc"), str)):
            bad("schema-inconsistent", f"event {seq}")
            continue
        if (any(e.get(k) is not None and not isinstance(e[k], str) for k in
                ("logical_slot", "slot_key", "campaign_id", "outcome", "quality", "failure_class", "reason", "fallback"))
                or any(e.get(k) is not None and not isinstance(e[k], dict) for k in ("timing", "bench_payload", "provenance"))
                or any(e.get(k) is not None and type(e[k]) is not int for k in ("a", "b", "attempt", "value", "anomalies"))):
            bad("schema-inconsistent", f"event {seq} field types")
            continue
        if ended:
            bad("schema-inconsistent", "event after series-end")
        if e["kind"] == "series-end":
            ended = True
            if not isinstance(e.get("reason"), str) or e.get("reason") not in core.END_REASONS:
                bad("schema-inconsistent", "unknown end reason")
        clean.append(e)
        if any(e.get(k) is not None and not 0 <= e[k] <= cap for k, cap in (("a", core.A_PROPOSALS), ("b", core.B_EVALUATIONS))):
            bad("schema-inconsistent", f"event {seq} budget outside contract")
        if e.get("quality") == "normal" and isinstance(e.get("bench_payload"), dict):
            try:
                normal = core.classify_session(e["bench_payload"], core.N_EVAL) == "normal"
            except (TypeError, ValueError, AttributeError, OverflowError):
                normal = False
            if not normal:
                bad("schema-inconsistent", f"event {seq} quality evidence mismatch")
        if (e["kind"] in {"evaluation-result", "score-session", "stock-start", "block-stock"}
                and e.get("outcome") == "certified"
                and (not isinstance(e.get("bench_payload"), dict)
                     or e.get("fitness_tps") != e["bench_payload"].get("median_tps"))):
            bad("schema-inconsistent", f"event {seq} fitness/median mismatch")
        kind, logical, attempt = e["kind"], e["logical_slot"], e["attempt"]
        if kind == "endpoint-fixed":
            if fixed is not None:
                bad("slot-duplicate", "multiple endpoint-fixed events")
            fixed = e
            endpoint = e.get("endpoint")
            if endpoint is not None and (not isinstance(endpoint, dict) or endpoint not in clean[:-1]
                                        or endpoint.get("kind") != "evaluation-result"
                                        or endpoint.get("outcome") != "certified" or endpoint.get("quality") != "normal"):
                bad("schema-inconsistent", "endpoint not a certified source event")
        if kind == "score-session" and fixed is None:
            bad("score-before-endpoint", str(seq))
        if kind == "score-session" and fixed and fixed.get("endpoint") is None:
            bad("schema-inconsistent", "score without an endpoint")
        if fixed and kind in {"evaluation-result", "proposal-opportunity"}:
            bad("schema-inconsistent", "search after endpoint fixation")
        if kind == "score-session" and fixed and isinstance(fixed.get("endpoint"), dict):
            if e.get("value") != fixed["endpoint"].get("value") or e.get("proposal_sha256") != fixed["endpoint"].get("proposal_sha256"):
                bad("schema-inconsistent", "score endpoint identity mismatch")
        if e.get("fitness_tps") is not None and not _positive(e["fitness_tps"]):
            bad("nonfinite-score", f"event {seq} fitness must be finite positive")
        if e.get("score") is not None and not _positive(e["score"]):
            bad("nonfinite-score", "series score must be finite positive")
        if logical is not None and kind == "proposal-opportunity" and attempt is None and e["slot_key"] is None:
            continue  # A1 records the opportunity before any physical attempt exists.
        if logical is not None:
            try:
                slot_kind, number = logical.rsplit("-", 1)
                expected = core.slot_key(h["cohort"], h["arm"], h["workload"], h["series"], slot_kind, int(number), attempt)
                if type(attempt) is not int or not 0 <= attempt <= core.MAX_MACHINE_RETRIES or expected != e["slot_key"]:
                    raise ValueError("slot ownership")
                attempts.setdefault(logical, set()).add(attempt)
            except (ValueError, TypeError, AttributeError, KeyError):
                bad("attempt-unowned", f"event {seq}")
            if kind in RESULT_KINDS:
                if logical in slots:
                    bad("slot-duplicate", logical)
                slots.add(logical)
        elif e["slot_key"] is not None or attempt is not None:
            bad("attempt-unowned", f"event {seq}")
        elif kind in {"score-session", "evaluation-result", "stock-start"} and e.get("outcome") != "allocation-exhausted":
            bad("attempt-unowned", f"event {seq} missing logical slot")
    for logical, seen in attempts.items():
        if seen != set(range(max(seen) + 1)):
            bad("attempt-unowned", logical + " missing predecessor attempt")
    ends = [e for e in clean if e["kind"] == "series-end"]
    if ends and not stock:
        evaluations = [e for e in clean if e["kind"] == "evaluation-result"]
        b = ends[-1].get("b")
        if (type(b) is not int or len(evaluations) != b
                or [e["b"] for e in evaluations] != list(range(1, b + 1))):
            bad("schema-inconsistent", "evaluation count/sequence differs from terminal B")
    ledger["events"] = clean
    return True


def _reconcile(ledger, invalid):
    """Read crash evidence without changing any authoritative event."""
    root, events = ledger["root"], ledger["events"]
    if root is None:
        return []
    terminal_kinds = {"evaluation-result", "proposal-rejected", "score-session",
                      "stock-start", "block-stock", "machine-retry"}
    terminal = {e.get("slot_key") for e in events if e["kind"] in terminal_kinds}
    reconciled, seen = [], set()
    for e in events:
        if e["kind"] != "slot-attempt-start" or e["slot_key"] in terminal | seen:
            continue
        seen.add(e["slot_key"])
        relative = e.get("sidecar_dir")
        if not isinstance(relative, str):
            invalid.append({"category": "schema-inconsistent", "source": ledger["source"],
                            "detail": "attempt sidecar path missing"})
            continue
        path = root / relative
        if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
            invalid.append({"category": "schema-inconsistent", "source": ledger["source"],
                            "detail": "attempt sidecar path escapes ledger"})
            continue
        if (path / "pipeline-submitted.json").is_file():
            reconciled.append({**e, "outcome": "submitted-unresolved", "submitted": True,
                               "failure_class": "unclassified-missing", "source": ledger["source"]})
    return reconciled


def _normal(e):
    return e.get("outcome") == "certified" and e.get("quality") == "normal" and _positive(e.get("fitness_tps"))


def _stock_normal(e):
    # Reuse the producer's pure stock identity predicate; never re-read WAL.
    return (_normal(e) and e.get("src_token") is not None and e.get("variant") is not None
            and core._stock_established(e))


def _distribution(values):
    values = [v for v in values if type(v) in (int, float) and math.isfinite(v)]
    return {"values": values, "count": len(values), "median": statistics.median(values) if values else None,
            "max": max(values) if values else None, "missing": not values}


def _describe(ledger):
    events, h = ledger["events"], ledger["header"]
    observations = events + ledger.get("reconciled", [])
    # pipeline-submitted and terminal observations describe the SAME attempt.
    physical = {e["slot_key"]: e for e in observations if e.get("slot_key")}
    timing = [e.get("timing") or {} for e in physical.values()]
    waits = {}
    for e in events:
        provenance = e.get("provenance") or {}
        if (e["kind"] in {"evaluation-result", "proposal-rejected", "series-end"}
                and e.get("a") and type(provenance.get("proposal_wait_wall_s")) in (int, float)):
            waits.setdefault(e["a"], provenance)
    def wait_summary(rows):
        values = [r["proposal_wait_wall_s"] for r in rows]
        return {"count": len(values), "total_s": sum(values), "max_s": max(values, default=None)}
    handshake_wait = {**wait_summary(waits.values()), "by_status": {
        status: wait_summary(r for r in waits.values() if r.get("handshake_status") == status)
        for status in sorted({r.get("handshake_status", "proposal") for r in waits.values()})}}
    submitted = {e["logical_slot"] for e in observations if e.get("logical_slot") and (
        e.get("submitted") is True or e["kind"] == "pipeline-submitted"
        or e["kind"] in {"evaluation-result", "score-session", "stock-start", "block-stock"}
        and e.get("submitted") is not False and e.get("outcome") not in {
            "allocation-exhausted", "pre-start-failure", "rejected-preprocess", "duplicate-skip"})}
    counted_search = {e["logical_slot"] for e in events if e.get("logical_slot") in submitted
                      and e["logical_slot"].startswith("search-") and (
                          e.get("submitted") or e["kind"] in {"evaluation-result", "pipeline-submitted"})}
    unresolved_search = {e["logical_slot"] for e in ledger.get("reconciled", [])
                         if e["logical_slot"].startswith("search-")} - counted_search
    intervals = {k: _distribution(t.get(k) for t in timing) for k in (
        "subprocess_wall_s", "build_wall_s", "bench_wall_s", "bench_surrounding_wall_s", "verify_total_wall_s")}
    intervals["verify_intervals"] = [t.get("verify_intervals", []) for t in timing]
    intervals["verify_missing_reps"] = [t.get("verify_missing_reps") for t in timing]
    intervals["verify_truncated"] = [t.get("verify_truncated") for t in timing]
    intervals["session_by_outcome"] = {
        outcome: _distribution((e.get("timing") or {}).get("subprocess_wall_s")
                               for e in physical.values() if e.get("outcome") == outcome)
        for outcome in sorted({e.get("outcome") or "unknown" for e in physical.values()})}
    return {"arm": h["arm"], "workload": h["workload"], "series": h["series"], "block": h["block"],
            "A": max((e.get("a") or 0 for e in events), default=0),
            "B": max((e.get("b") or 0 for e in events), default=0) + len(unresolved_search),
            "logical_sessions": (len(submitted) if h["arm"] == "stock" else
                                 1 + len(submitted - {"stock-start-1"})),
            "attempted_logical_slots": len({e["logical_slot"] for e in physical.values()}),
            "preprocess_rejections": sum(e["kind"] == "proposal-rejected"
                                         and e.get("outcome") in {None, "rejected-preprocess"} for e in events),
            "exploration_quality_missing": sum(e["kind"] == "evaluation-result"
                                               and e.get("quality") == "quality-missing" for e in events),
            "physical_attempts": len(physical),
            "quality_rounds": [(e.get("bench_payload") or {}).get("rounds") for e in physical.values()],
            "stock": [e for e in events if e["kind"] == "stock-start"],
            "anomaly": [e for e in events if e.get("anomalies") or e.get("outcome") == "anomaly"],
            "unfinished": not events or events[-1]["kind"] != "series-end" or events[-1].get("reason") not in {"b-complete", "a-exhausted", "grid-exhausted"},
            "end_reason": events[-1].get("reason") if events else None,
            "timing": intervals, "handshake_wait": handshake_wait,
            "handshake_wait_seconds": _distribution(r["proposal_wait_wall_s"] for r in waits.values()),
            "queue_wait_seconds": None,
            "job_elapse": h.get("job", {}).get("Elapse"),
            "job_elapse_status": "recorded" if h.get("job", {}).get("Elapse") is not None else "missing-from-ledger",
            "interval_label": "trace+verifier+周辺処理 区間"}


def _project(ledger, disqualified, stocks, corrections):
    h, events = ledger["header"], ledger["events"]
    result = _describe(ledger)
    fixed = next((e for e in events if e["kind"] == "endpoint-fixed"), None)
    endpoint = fixed.get("endpoint") if fixed else None
    endpoint = endpoint if isinstance(endpoint, dict) and type(endpoint.get("value")) is int else None
    scores = [e for e in events if e["kind"] == "score-session"]
    revoked = endpoint is not None and (h["workload"], endpoint.get("value")) in disqualified
    quality_missing = any(e.get("quality") == "quality-missing" for e in scores)
    fallback = bool(fixed and (revoked or endpoint is None and fixed.get("fallback")))
    missing = None
    sessions = []
    if fallback:
        sessions = stocks.get((h["workload"], h["block"]), [])
        if len(sessions) != core.BLOCK_STOCK_SESSIONS:
            missing = "stock-unestablished"
    elif endpoint and len(scores) == core.N_EVAL and all(_normal(e) for e in scores):
        sessions = [e["fitness_tps"] for e in scores]
    else:
        missing = "quality-missing" if quality_missing else "machine-missing" if any(e.get("failure_class") == "machine" or e.get("outcome") in {"pre-start-failure", "machine-failure"} for e in events) else "unclassified-missing"
    starts = [e for e in events if e["kind"] == "stock-start"]
    if len(starts) != 1 or not all(_stock_normal(e) for e in starts):
        missing = "stock-unestablished"
    if (h["workload"], -1) in disqualified:
        missing = "stock-unestablished"
    if not events or events[-1]["kind"] != "series-end":
        missing = missing or "unclassified-missing"
    if revoked:
        corrections.append({"type": "結果の訂正", "reported_at": datetime.now(timezone.utc).isoformat(),
                            "workload": h["workload"], "arm": h["arm"], "series": h["series"],
                            "value": endpoint.get("value"), "failure_condition": "a", "original_endpoint": endpoint})
    score = statistics.median(sessions) if sessions and missing is None else None
    result.update(endpoint=endpoint, endpoint_revoked=revoked, certified_endpoint=endpoint is not None and not revoked,
                  score=score, score_sessions=sessions, endpoint_cv=_cv(sessions) if sessions and not fallback else None,
                  fallback=fallback, fallback_shared_block_stock=fallback, missing=missing,
                  failure_condition_a=revoked or bool(result["anomaly"]),
                  events=events)
    return result


def build_report(ledgers, *, purpose: Literal["pilot", "registered"]) -> dict:
    """Consume ledger directories or {header, events} snapshots without mutation."""
    if purpose not in {"pilot", "registered"}:
        raise ValueError("unknown purpose")
    invalid, loaded = [], []
    for source in ledgers:
        ledger = _load(source, invalid)
        if ledger is not None and _validate(ledger, invalid, purpose):
            ledger["reconciled"] = _reconcile(ledger, invalid)
            loaded.append(ledger)
    identities, session_owners = set(), {}
    configurations = {}
    for ledger in loaded:
        h = ledger["header"]
        configuration = {k: h[k] for k in ("repo_head", "pin", "perf_config", "verify_mode", "bench_max_rounds")}
        previous = configurations.setdefault(h["workload"], configuration)
        if configuration != previous:
            invalid.append({"category": "schema-inconsistent", "source": ledger["source"], "workload": h["workload"], "detail": "cohort configuration mismatch"})
        identity = (h["cohort"], h["arm"], h["workload"], h["series"])
        if identity in identities:
            invalid.append({"category": "slot-duplicate", "source": ledger["source"], "workload": h["workload"], "arm": h["arm"], "detail": str(identity)})
        identities.add(identity)
        for e in ledger["events"]:
            if e["kind"] in RESULT_KINDS and e.get("campaign_id"):
                sid = e["campaign_id"]
                if sid in session_owners:
                    invalid.append({"category": "slot-duplicate", "source": ledger["source"], "detail": "reused session " + str(sid)})
                session_owners[sid] = identity
    disqualified = {(x["header"]["workload"], e.get("value")) for x in loaded for e in x["events"]
                    if e.get("anomalies") or e.get("outcome") == "anomaly"}
    stocks, stock_descriptions = {}, []
    for ledger in loaded:
        h = ledger["header"]
        if h["arm"] != "stock":
            continue
        sessions = [e for e in ledger["events"] if e["kind"] == "stock-start"]
        values = [e["fitness_tps"] for e in sessions if _stock_normal(e)]
        if len(values) == core.BLOCK_STOCK_SESSIONS and (h["workload"], -1) not in disqualified:
            stocks[h["workload"], h["block"]] = values
        stock_descriptions.append({**_describe(ledger), "sessions": values,
                                   "descriptive_cv": _cv(values) if len(values) == 5 else None})
    corrections = []
    series = [_project(x, disqualified, stocks, corrections) for x in loaded if x["header"]["arm"] != "stock"]
    for ledger, row in zip((x for x in loaded if x["header"]["arm"] != "stock"), series):
        ends = [e for e in ledger["events"] if e["kind"] == "series-end"]
        if ends and ends[-1].get("score") is not None and not row["endpoint_revoked"] and ends[-1]["score"] != row["score"]:
            invalid.append({"category": "schema-inconsistent", "source": ledger["source"], "workload": row["workload"], "arm": row["arm"], "detail": "score differs from five fresh sessions"})
    report = {"schema": "b5-generator-contrast-report/v1", "purpose": purpose, "invalid": invalid,
              "series": series, "block_stock": stock_descriptions, "corrections": corrections,
              "reconciled_attempts": [e for x in loaded for e in x["reconciled"]],
              "disqualified": sorted(disqualified, key=str),
              "validation_scope": "Ledger schema, identities, configuration consistency and numeric rules; saved execution order and block separation require external registration evidence.",
              "cells": [{"workload": w, "arm": a, "series_count": sum(x["workload"] == w and x["arm"] == a for x in series),
                         "fallback_count": sum(x["workload"] == w and x["arm"] == a and x["fallback"] for x in series),
                         "missing_count": sum(x["workload"] == w and x["arm"] == a and x["missing"] is not None for x in series),
                         "unfinished_count": sum(x["workload"] == w and x["arm"] == a and x["unfinished"] for x in series),
                         "certified_endpoint_count": sum(x["workload"] == w and x["arm"] == a and x["certified_endpoint"] for x in series)}
                        for w in core.WORKLOADS for a in core.ARMS]}
    if purpose == "pilot":
        report["registered_judgment"] = "not-applicable-pilot"
        report["interpretation"] = "登録比較に必要な系列数・block・floorを満たさない。stock CV は記述統計。"
        return report
    report["registered_judgment"] = "see-comparisons"
    report["scope"] = "Frozen environment, workload and generators only; this report does not authorize cohort activation."
    report["assumption"] = INDEPENDENCE + "。block の再現は共通ショックを排除せず、独立性を証明しない。"
    floors, inputs, preliminary = {}, {}, {}
    cohorts = {x["header"]["cohort"] for x in loaded}
    if len(cohorts) != 1:
        invalid.append({"category": "schema-inconsistent", "detail": "registered cohort must be unique"})
    for w in core.WORKLOADS:
        try:
            floors[w] = stock_cv_floor({b: stocks.get((w, b), []) for b in (1, 2, 3)})
        except ValueError:
            floors[w] = None
        for b in core.ARMS[1:]:
            arms = {a: [s for s in series if s["workload"] == w and s["arm"] == a] for a in ("llm", b)}
            pairs = pair_differences(arms["llm"], arms[b])
            kwargs = dict(floor=floors[w], certified_counts={a: sum(s["certified_endpoint"] for s in rows) for a, rows in arms.items()},
                          invalid=any(
                              (i.get("workload") not in core.WORKLOADS or i["workload"] == w)
                              and (i.get("arm") not in core.ARMS or i["arm"] in ("llm", b)) for i in invalid),
                          missing=any(len(rows) != 12 or any(s["missing"] for s in rows) for rows in arms.values()))
            inputs[w, b] = (pairs, kwargs)
            preliminary[w, b] = decide_comparison(pairs, **kwargs)
    adjusted = holm_six({k: v["raw_p"] for k, v in preliminary.items()})
    comparisons = []
    for key in COMPARISONS:
        pairs, kwargs = inputs[key]
        comparisons.append({"workload": key[0], "baseline": key[1], **decide_comparison(pairs, **kwargs, significant=adjusted[key]["significant"]),
                            "adjusted_p": adjusted[key]["adjusted_p"], "holm_threshold": adjusted[key]["threshold"]})
    report.update(floors=floors, comparisons=comparisons)
    report["workloads"] = {w: {"conditional_superiority": all(x["judgment"] == "conditional-superiority" for x in comparisons if x["workload"] == w),
                               "llm_specific_gain_not_shown": any(x["judgment"] == "equivalent-within-floor" for x in comparisons if x["workload"] == w)} for w in core.WORKLOADS}
    report["all_workloads_superiority"] = all(x["conditional_superiority"] for x in report["workloads"].values())
    return report


def _jsonable(value):
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "value": float(value)}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(x) for x in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)  # retain invalid evidence without nonstandard JSON NaN
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-root", type=Path, action="append", required=True)
    parser.add_argument("--block-stock-root", type=Path, action="append", default=[])
    parser.add_argument("--purpose", choices=("pilot", "registered"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    roots = []
    for root in args.ledger_root + args.block_stock_root:
        roots.extend([root] if (root / "header.json").exists() else sorted(p.parent for p in root.rglob("header.json")) or [root])
    report = build_report(roots, purpose=args.purpose)
    args.out.write_text(json.dumps(_jsonable(report), ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print("workload\tarm\tseries\tscore\tfallback\tmissing")
    for s in report["series"]:
        print("\t".join(str(s[k]) for k in ("workload", "arm", "series", "score", "fallback", "missing")))
    print(report["registered_judgment"])
    for c in report.get("comparisons", []):
        print(c["workload"], c["baseline"], c["judgment"], c.get("qualification", ""), sep="\t")
    return 1 if report["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
