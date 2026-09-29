"""The round CLI preserves driver bytes and gates auditor on preview."""
import json
from pathlib import Path
from types import SimpleNamespace

from orchestrator.campaign.silo_policy_contrast import ContrastLedger, DEFAULT_BUDGETS
from tools import silo_policy_contrast_round as R


def _ledger(tmp_path):
    root = tmp_path / "ledger"
    ledger = ContrastLedger.create(root, {
        "version": "silo-policy-contrast-test-2026-09-29", "cohort": "test", "arm": "llm-cpp",
        "series": 1, "form": "cpp", "submit_checkout": str(tmp_path), "checkout_head": "test",
        "pin": "test", "budgets": DEFAULT_BUDGETS})
    ledger.append("series-start")
    ledger.append("slot-result", logical_slot="stock-1", outcome="certified", quality="normal",
                  fitness_tps=10, abort_rate_pct=2, variant="stock")
    return root


def test_prepare_preserves_driver_stdout_and_critic_shape(tmp_path):
    root = _ledger(tmp_path)
    ledger = ContrastLedger(root)
    out = tmp_path / "out"
    first = R.prepare(ledger, 1, out, ledger_root=root)
    assert first["status"] == "critic-needed"
    prompt = (out / "critic-prompt.md").read_text()
    assert all(key in prompt for key in ("fitness_tps", "abort_rate_pct", "quality", "outcome"))
    critic = out / "critic.md"
    critic.write_text("## attribution\na\n## recommend\nb\n## avoid\nc\n## uncertainty\nd\n")
    raw = '{"self_history":"literal\\nbytes"}\n'
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=raw, stderr="")
    assert R.prepare(ledger, 1, out, ledger_root=root, critic_output=critic, run=run)["status"] == "coder-needed"
    assert (out / "coder-input.json").read_text() == raw
    assert "--contrast-ledger" in calls[0] and "--critic-output" in calls[0]
    assert [e["kind"] for e in ContrastLedger(root).events].count("critic-result") == 1


def test_preview_reject_records_without_auditor(tmp_path):
    root = _ledger(tmp_path)
    ledger = ContrastLedger(root)
    ledger.append("opportunity-start", a=1)
    coder = tmp_path / "coder.json"
    coder.write_text(json.dumps({"proposal": {"axis": "silo-function-policy", "implementation": "bad"}}))
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        if "--preview-diff" in argv:
            return SimpleNamespace(returncode=1, stdout=json.dumps({"passed": False, "working_diff": "",
                "diff_digest": "x", "subtype": "x", "rule_id": "x"}), stderr="")
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")
    out = tmp_path / "out"
    assert R.check(ledger, 1, coder, out, ledger_root=root, run=run)["status"] == "rejected"
    assert not (out / "auditor-prompt.md").exists()
    assert "--record-reject" in calls[1]
    end = ContrastLedger(root).events[-1]
    assert (end["reject_subtype"], end["reject_rule_id"]) == ("x", "x")
