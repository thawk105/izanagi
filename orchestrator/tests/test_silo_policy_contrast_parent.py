"""Claude launch is the only external process seam."""
import json
from pathlib import Path
from types import SimpleNamespace

from orchestrator.campaign.silo_policy_contrast import ContrastLedger, LEDGER_SCHEMA
from tools.pegasus import silo_policy_contrast_parent as P


def _ledger(tmp_path):
    root = tmp_path / "ledger"
    (root / "events").mkdir(parents=True)
    (root / "header.json").write_text(json.dumps({"schema": LEDGER_SCHEMA,
        "version": "silo-policy-contrast-test-2026-09-29", "cohort": "test", "arm": "llm-ir",
        "series": 1, "form": "ir", "submit_checkout": str(tmp_path), "checkout_head": "test",
        "pin": "test", "budgets": {"B": 10, "A": 30, "k": 2, "n_eval": 5,
        "machine_retries": 2, "role_retries": 2}}))
    (root / "events" / "000001-series-start.json").write_text(json.dumps({"kind": "series-start"}))
    return root


def test_fresh_sessions_and_429_retry_same_a(tmp_path):
    root = _ledger(tmp_path)
    argv_seen = []
    outputs = [{"is_error": True, "api_error_status": 429}, {"is_error": False}]
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
