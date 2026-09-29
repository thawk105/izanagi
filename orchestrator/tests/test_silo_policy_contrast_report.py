"""Generation eligibility and family adjustment use the actual ledger events."""
import json
import pytest

from orchestrator.campaign.silo_policy_contrast import ContrastLedger, DEFAULT_BUDGETS
from orchestrator.campaign import silo_policy_contrast_report as R


def _ledger(tmp_path, arm, series, events):
    root = tmp_path / f"{arm}-{series}"
    ledger = ContrastLedger.create(root, {
        "version": "silo-policy-contrast-test-2026-09-29", "cohort": "test",
        "arm": arm, "series": series, "form": "cpp" if arm in {"llm-cpp", "reference"} else "ir",
        "submit_checkout": str(tmp_path), "checkout_head": "test", "pin": "test",
        "budgets": DEFAULT_BUDGETS})
    for event in events:
        ledger.append(event["kind"], **{k: v for k, v in event.items() if k != "kind"})
    return root


def _cohort(tmp_path, *, search=False):
    roots = []
    for arm in R.ARMS:
        for series in range(1, 11):
            stock = {"kind": "slot-result", "logical_slot": "stock-1", "attempt": 0,
                     "outcome": "certified", "quality": "normal", "fitness_tps": 100,
                     "variant": f"stock-{arm}-{series}", "source_digest": "stock"}
            seed = {"kind": "slot-result", "logical_slot": "seed-1", "attempt": 0,
                    "outcome": "certified", "quality": "normal", "fitness_tps": 105,
                    "variant": f"seed-{arm}-{series}", "source_digest": "seed"}
            events = [{"kind": "series-start"}, stock, seed,
                      {"kind": "endpoint-fixed", "logical_slot": seed["logical_slot"],
                       "variant": seed["variant"], "source_digest": seed["source_digest"],
                       "fitness_tps": seed["fitness_tps"]},
                      *([{"kind": "slot-result", "logical_slot": "eval-1", "attempt": 0,
                          "outcome": "certified", "quality": "normal", "fitness_tps": 115,
                          "variant": f"eval-{arm}-{series}"}] if search else []),
                      *({"kind": "slot-result", "logical_slot": f"score-{i}", "attempt": 0,
                         "outcome": "certified", "quality": "normal",
                         "fitness_tps": (120 if arm.startswith("llm") else 100) if search else 110,
                         "variant": seed["variant"], "source_digest": seed["source_digest"]} for i in range(5)),
                      {"kind": "series-end", "reason": "a-exhausted"}]
            roots.append(_ledger(tmp_path, arm, series, events))
    for batch in range(1, 4):
        events = [{"kind": "series-start"}]
        events.extend({"kind": "slot-result", "logical_slot": f"ref-stock-{i}", "attempt": 0,
                       "outcome": "certified", "quality": "normal", "fitness_tps": 100+i,
                       "variant": f"ref-stock-{batch}-{i}"} for i in range(5))
        events.extend({"kind": "slot-result", "logical_slot": f"ref-fixed10-{i}", "attempt": 0,
                       "outcome": "certified", "quality": "normal", "fitness_tps": 110+i,
                       "variant": f"ref-fixed-{batch}-{i}"} for i in range(5))
        events.append({"kind": "series-end", "reason": "b-complete"})
        roots.append(_ledger(tmp_path, "reference", batch, events))
    return R.build_report(roots)


def test_seed_only_does_not_count_as_generation(tmp_path):
    report = _cohort(tmp_path)
    assert report["n"] == 10
    assert report["search_point_series_counts"] == dict.fromkeys(R.ARMS, 0)
    assert report["certified_endpoint_counts"] == dict.fromkeys(R.ARMS, 10)
    assert all(c["judgment"] == "generation-failed-both" for c in report["comparisons"])
    assert {c["family"] for c in report["comparisons"]} == {"A", "B"}


def test_holm_is_adjusted_within_each_two_comparison_family(tmp_path):
    report = _cohort(tmp_path, search=True)
    assert report["search_point_series_counts"] == dict.fromkeys(R.ARMS, 10)
    assert all(c["judgment"] == "conditional-superiority" for c in report["comparisons"])
    assert all(c["adjusted_p"] == R.Fraction(1, 512) for c in report["comparisons"])


def test_score_identity_must_match_fixed_endpoint(tmp_path):
    root = _ledger(tmp_path, "llm-cpp", 1, [
        {"kind": "series-start"},
        {"kind": "slot-result", "logical_slot": "stock-0", "outcome": "certified",
         "quality": "normal", "fitness_tps": 100, "variant": "stock"},
        {"kind": "endpoint-fixed", "logical_slot": "seed-0", "variant": "chosen",
         "source_digest": "source-a", "fitness_tps": 110},
        {"kind": "slot-result", "logical_slot": "score-0", "outcome": "certified",
         "quality": "normal", "fitness_tps": 110, "variant": "chosen",
         "source_digest": "source-b"},
        {"kind": "series-end", "reason": "a-exhausted"}])
    with pytest.raises(ValueError, match="score identity"):
        R._project(ContrastLedger(root), set(), [], [])
