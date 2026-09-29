"""Generation eligibility and family adjustment use the actual ledger events."""
import json

from orchestrator.campaign.silo_policy_contrast import LEDGER_SCHEMA
from orchestrator.campaign import silo_policy_contrast_report as R


def _ledger(tmp_path, arm, series, events):
    root = tmp_path / f"{arm}-{series}"
    (root / "events").mkdir(parents=True)
    (root / "header.json").write_text(json.dumps({"schema": LEDGER_SCHEMA,
        "version": "silo-policy-contrast-test-2026-09-29", "cohort": "test",
        "arm": arm, "series": series, "form": "cpp" if arm in {"llm-cpp", "reference"} else "ir",
        "submit_checkout": str(tmp_path), "checkout_head": "test", "pin": "test",
        "budgets": {"B": 10, "A": 30, "k": 2, "n_eval": 5,
        "machine_retries": 2, "role_retries": 2}}))
    for i, event in enumerate(events, 1):
        (root / "events" / f"{i:06d}-{event['kind']}.json").write_text(json.dumps(event))
    return root


def _cohort(tmp_path, *, search=False):
    roots = []
    for arm in R.ARMS:
        for series in range(1, 11):
            stock = {"kind": "slot-result", "logical_slot": "stock-1", "attempt": 0,
                     "outcome": "certified", "quality": "normal", "fitness_tps": 100,
                     "variant": f"stock-{arm}-{series}"}
            seed = {"kind": "slot-result", "logical_slot": "seed-1", "attempt": 0,
                    "outcome": "certified", "quality": "normal", "fitness_tps": 105,
                    "variant": f"seed-{arm}-{series}"}
            events = [{"kind": "series-start"}, stock, seed,
                      {"kind": "endpoint-fixed", "endpoint": seed},
                      *([{"kind": "slot-result", "logical_slot": "eval-1", "attempt": 0,
                          "outcome": "certified", "quality": "normal", "fitness_tps": 115,
                          "variant": f"eval-{arm}-{series}"}] if search else []),
                      *({"kind": "slot-result", "logical_slot": f"score-{i}", "attempt": 0,
                         "outcome": "certified", "quality": "normal",
                         "fitness_tps": (120 if arm.startswith("llm") else 100) if search else 110,
                         "variant": seed["variant"]} for i in range(5)),
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
