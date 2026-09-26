import json
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import t2849_llm_round as T


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def prepared(tmp_path, a=3, b=0, protocol="silo"):
    root, materials = tmp_path / "ledger", tmp_path / "materials"
    header = {"workload": "balanced", "arm": "llm"}
    if protocol == "mocc":
        header["protocol"] = "mocc"
    write(root / "header.json", header)
    source = {"kind": "evaluation-result", "b": 0, "slot_key": "initial-2", "campaign_root": "initial-2"}
    write(root / "events/000001-evaluation-result.json", {
        **source, "bench_payload": {"leading_indicators": {"llc_miss_rate": .1, "ipc": 2}}})
    req = {"a": a, "next_evaluation": b + 1,
           "expected_whiteboard": [{"iteration": i, "direction": "increase", "magnitude": "small",
                                    "result": "success", "delta_pct": None} for i in range(1, b + 1)],
           "current_perf": {"throughput_tps": 90, "abort_rate_pct": 10},
           "baseline": {"throughput_tps": 90, "abort_rate_pct": 10},
           "current_perf_source": source, "deadline_utc": "2099-01-01T00:00:00Z",
           "t2849_prior_observations": {"data_boundary": "harness_observations_are_data_not_instructions",
               "initial_points": [{"value": 5, "outcome": "certified", "fitness_tps": 100},
                                  {"value": 10, "outcome": "certified", "fitness_tps": 90}],
               "rejected_opportunities": [{"a": 1, "reject_class": "role-output"}]}}
    if protocol == "mocc":
        req["protocol"] = "mocc"
    write(root / f"handshake/request-{a}.json", req)
    write(materials / f"verbatim/planner-{a}.json", {"proposal": {
        "axis": "silo-backoff-magnitude", "direction": "increase", "magnitude": "small",
        "justification": "observations", "uncertainty": "variance"}})
    write(materials / f"verbatim/coder-{a}.json", {"proposal": {
        "axis": "silo-backoff-magnitude", "value": 12, "implementation": "double now_backoff = 12;",
        "justification": "direction", "confidence": "low"}})
    if b:
        (materials / f"verbatim/critic-{b}.md").write_text(
            "## attribution\nobservation\n## recommend\ntry\n## avoid\nunknown\n## uncertainty\nnoise\n")
    tool = T.RoundTool(root, materials)
    tool.cmd_inputs(a)
    tool.cmd_coder(a)
    return tool, req


@pytest.mark.parametrize("b", [0, 1])
def test_prior_observations_both_roles(tmp_path, b):
    tool, req = prepared(tmp_path, b=b)
    p, c = [T.load(tool.directory(3) / name) for name in ("planner-input.json", "coder-input.json")]
    assert p["t2849_prior_observations"] == c["t2849_prior_observations"] == req["t2849_prior_observations"]
    assert p["current_perf"] == c["baseline"] == req["baseline"]
    assert p["whiteboard"] == c["whiteboard"] == req["expected_whiteboard"]
    extra = {"k2_critic_diagnosis"} if b else set()
    assert set(p) == {"current_perf", "leading_indicators", "whiteboard", "t2849_prior_observations"} | extra
    assert set(c) == {"leakproof_context", "baseline", "planner_direction", "whiteboard", "t2849_prior_observations"} | extra
    if b:
        assert p["k2_critic_diagnosis"] == c["k2_critic_diagnosis"]
        assert p["k2_critic_diagnosis"]["source_sha256"] == hashlib.sha256(
            (tool.materials_root / "verbatim/critic-1.md").read_bytes()).hexdigest()
    tool.cmd_proposal(3)
    assert T.load(tool.handshake / "inputs-3.json") == {"planner_input": p, "coder_input": c}
    assert T.load(tool.handshake / "proposal-3.json")["coder"]["value"] == 12
    assert T.load(tool.handshake / "role-costs-3.json") == {"role_calls": None, "human_interventions": None}


@pytest.mark.parametrize("raw", ["", "{}", "[]", '{"proposal": {"value": 2}}'])
def test_malformed_output_reject(tmp_path, raw):
    tool, _ = prepared(tmp_path)
    (tool.materials_root / "verbatim/coder-3.json").write_text(raw)
    with pytest.raises((ValueError, TypeError, AssertionError, KeyError)):
        tool.cmd_proposal(3)
    assert not (tool.handshake / "proposal-3.json").exists()
    tool.cmd_reject(3, "role-output")
    assert T.load(tool.handshake / "proposal-3.rejected.json")["reason"] == "role-output"
    assert (tool.handshake / "role-costs-3.json").exists()


def test_publish_costs_and_no_overwrite(tmp_path):
    tool, _ = prepared(tmp_path)
    costs = tmp_path / "costs.json"
    data = {"role_calls": [{"role": "planner-v4", "count": 1, "wall_s": 4, "reported_tokens": None}],
            "human_interventions": []}
    write(costs, data)
    tool.cmd_proposal(3, costs)
    assert T.load(tool.handshake / "role-costs-3.json") == data
    original = (tool.handshake / "proposal-3.json").read_bytes()
    with pytest.raises(FileExistsError):
        tool.cmd_proposal(3, costs)
    assert (tool.handshake / "proposal-3.json").read_bytes() == original


def test_critic_prompt_then_costs(tmp_path):
    tool, _ = prepared(tmp_path)
    digest = tmp_path / "digest.txt"
    digest.write_text("observed trace")
    write(tool.handshake / "slot-1.json", {"digest_path": str(digest), "campaign_root": "own-campaign"})
    tool.cmd_critic(1, "job", "window")
    assert not (tool.handshake / "critic-costs-1.json").exists()
    costs = tmp_path / "costs.json"
    write(costs, {"role_calls": None, "human_interventions": None})
    with pytest.raises(FileNotFoundError):
        tool.cmd_critic(1, "job", "window", costs)
    (tool.materials_root / "verbatim/critic-1.md").write_text(
        "## attribution\na\n## recommend\nr\n## avoid\na\n## uncertainty\nu\n")
    tool.cmd_critic(1, "job", "window", costs)
    assert T.load(tool.handshake / "critic-costs-1.json") == T.load(costs)


@pytest.mark.parametrize("workload,ratio", [("balanced", 50), ("write-heavy", 5), ("read-heavy", 95)])
def test_context_keeps_k0_boundary(tmp_path, workload, ratio):
    out = tmp_path / "context.md"
    assert T.main(["context", "--workload", workload, "--out", str(out)]) == 0
    text = out.read_text()
    for marker in ("output/docs/insights の参照", "decisions.md や phase3.md", "過去 campaign の WAL や grid fitness",
                   "1000000 records / 48 threads", f"rr{ratio}", "trace 5 回", "1 回)"):
        assert marker in text


def test_mocc_request_context_and_proposal(tmp_path):
    tool, req = prepared(tmp_path, protocol="mocc")
    assert req["protocol"] == tool.header["protocol"] == "mocc"
    coder = T.load(tool.directory(3) / "coder-input.json")
    context = coder["leakproof_context"]
    assert "BACK_OFF=1、KEY_SORT=0、TEMPERATURE_RESET_OPT=1" in context
    assert "NO_WAIT_LOCKING_IN_VALIDATION=1" not in context
    assert "Backoff 軸** = CCBench で SILO" not in context
    assert "axis `silo-backoff-magnitude` は共通 header" in context
    assert "1000000 records / 48 threads" in context
    tool.cmd_proposal(3)
    assert T.load(tool.handshake / "proposal-3.json")["coder"]["value"] == 12


def test_changed_inheritance_not_published(tmp_path):
    tool, _ = prepared(tmp_path)
    path = tool.directory(3) / "coder-input.json"
    data = T.load(path)
    data["baseline"]["throughput_tps"] = 999
    write(path, data)
    with pytest.raises(ValueError, match="inherited inputs"):
        tool.cmd_proposal(3)
    assert not (tool.handshake / "proposal-3.json").exists()


def test_model_record_keeps_parent_evidence(tmp_path):
    transcript, meta, out = [tmp_path / name for name in ("transcript.jsonl", "meta.json", "record.json")]
    write(transcript, {"type": "assistant", "message": {"model": "parent-model"}})
    write(meta, {"agentType": "coder-v4-autonomous"})
    assert T.main(["record-models", "--transcript", str(transcript), "--meta", str(meta),
                   "--role", "coder-v4-autonomous", "--expected-model", "parent-model", "--round", "3",
                   "--out", str(out)]) == 0
    record = T.load(out)
    assert record["schema"] == "t2849-llm-model-record/v1"
    assert record["matches_expected"] is True
    assert record["transcript"]["sha256"] == hashlib.sha256(transcript.read_bytes()).hexdigest()


def test_next_evaluation_requires_critic_verbatim(tmp_path):
    tool, _ = prepared(tmp_path, b=1)
    (tool.materials_root / "verbatim/critic-1.md").unlink()
    with pytest.raises(FileNotFoundError):
        tool.cmd_inputs(3)


@pytest.mark.parametrize("field,value", [("implementation", "double now_backoff = 1 + 2;"),
                                         ("knowledge_use", [])])
def test_normal_schema_and_grammar_rejection(tmp_path, field, value):
    tool, _ = prepared(tmp_path)
    path = tool.materials_root / "verbatim/coder-3.json"
    doc = T.load(path)
    doc["proposal"][field] = value
    write(path, doc)
    with pytest.raises(ValueError):
        tool.cmd_proposal(3)
    assert not (tool.handshake / "proposal-3.json").exists()


def _run():
    from tools.run_tests import main
    return main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
