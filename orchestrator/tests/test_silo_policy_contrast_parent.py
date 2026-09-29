"""Claude launch is the only external process seam."""
import json
from pathlib import Path
from types import SimpleNamespace

from orchestrator.campaign.silo_policy_contrast import ContrastLedger, DEFAULT_BUDGETS, series_state
from tools.pegasus import silo_policy_contrast_parent as P


def _ledger(tmp_path):
    root = tmp_path / "ledger"
    ledger = ContrastLedger.create(root, {
        "version": "silo-policy-contrast-test-2026-09-29", "cohort": "test", "arm": "llm-ir",
        "series": 1, "form": "ir", "submit_checkout": str(tmp_path), "checkout_head": "test",
        "pin": "test", "budgets": DEFAULT_BUDGETS})
    ledger.append("series-start")
    return root


def test_fresh_sessions_and_429_retry_same_a(tmp_path):
    root = _ledger(tmp_path)
    argv_seen = []
    outputs = [{"is_error": True, "api_error_status": 429, "modelUsage": {"model-a": {}}},
               {"is_error": False, "modelUsage": {"model-b": {}}}]
    def spawn(argv, *, stdout, **kwargs):
        argv_seen.append(argv)
        stdout.write(json.dumps(outputs.pop(0)).encode())
        return SimpleNamespace(returncode=0)
    waits = []
    assert P.run_opportunity(root, 1, tmp_path / "out", settings=tmp_path / "settings.json",
        model="fixed", checkout=tmp_path, spawn=spawn, sleep=waits.append) == "empty"
    assert len(argv_seen) == 2 and all("--resume" not in a and "--session-id" not in a for a in argv_seen)
    assert all("--settings" in a and "--model" in a and "--allowedTools" in a for a in argv_seen)
    assert waits == [900]
    assert [e for e in ContrastLedger(root).events if e["kind"] == "opportunity-end"][-1]["a"] == 1
    assert series_state(root)["A"] == 1
    ends = [e for e in ContrastLedger(root).events if e["kind"] == "opportunity-end"]
    assert [e["models"] for e in ends] == [["model-a"], ["model-b"]]


def test_three_failures_end_series_without_consuming_a(tmp_path):
    root = _ledger(tmp_path)
    def spawn(argv, *, stdout, **kwargs):
        stdout.write(b"not-json")
        return SimpleNamespace(returncode=1)
    assert P.run_opportunity(root, 2, tmp_path / "out", settings=tmp_path / "settings.json",
        model="fixed", checkout=tmp_path, spawn=spawn) == "role-failure"
    ledger = ContrastLedger(root)
    assert [e for e in ledger.events if e["kind"] == "opportunity-end"][-1]["outcome"] == "role-failure"
    assert ledger.events[-1]["reason"] == "unclassified-missing"


def test_429_after_terminal_record_does_not_retry_or_duplicate(tmp_path):
    root = _ledger(tmp_path)
    launches = []
    def spawn(argv, *, stdout, **kwargs):
        launches.append(argv)
        ContrastLedger(root).append("opportunity-end", a=1, outcome="proposed",
                                    proposal_path="proposal.json", proposal_sha256="digest")
        stdout.write(json.dumps({"is_error": True, "api_error_status": 429}).encode())
        return SimpleNamespace(returncode=0)
    out = tmp_path / "out"
    waits = []
    kwargs = dict(settings=tmp_path / "settings.json", model="fixed", checkout=tmp_path,
                  spawn=spawn, sleep=waits.append)
    assert P.run_opportunity(root, 1, out, **kwargs) == "proposed"
    assert P.run_opportunity(root, 1, out, **kwargs) == "proposed"
    assert len(launches) == 1 and waits == []
    assert [(e["a"], e["outcome"]) for e in ContrastLedger(root).events
            if e["kind"] == "opportunity-end"] == [(1, "proposed")]
