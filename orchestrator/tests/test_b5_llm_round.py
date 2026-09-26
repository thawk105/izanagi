"""B-5 round conversion contracts and preregistered MB1--MB8 targets.

Saved pilot inputs are read-only data. Every dependency is the production
implementation; fixtures write only within pytest's temporary directory.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import b5_llm_round as T  # noqa: E402
from orchestrator.campaign import b5_generator_contrast as B5  # noqa: E402
from orchestrator.campaign import p3_s4_loop as L  # noqa: E402

PILOT = ROOT / "output/insights/2026-09-20/t2797-b5-contrast"
LLM = PILOT / "llm"
KI = ROOT / "output/insights/2026-09-18/t2746-k2-loop-round2/materials/knowledge-input.json"


def _load(path):
    return json.loads(path.read_bytes())


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _fixture(tmp_path, *, evaluations=0, a=1, workload="write-heavy", series=1,
             cohort="b5-registered-v1"):
    ledger = tmp_path / "ledger"
    materials = tmp_path / "materials"
    header = _load(PILOT / "ledgers/llm/header.json")
    header.update(cohort=cohort, purpose="registered",
                  workload=workload, series=series)
    if cohort == B5.COHORT_REGISTERED_V2:
        header["prereg_version"] = B5.PREREG_VERSION_V2
    _write(ledger / "header.json", header)
    (ledger / "events").mkdir()
    # Copy the actual prefix through stock / the last completed evaluation.
    for path in sorted((PILOT / "ledgers/llm/events").glob("*.json")):
        event = _load(path)
        (ledger / "events" / path.name).write_bytes(path.read_bytes())
        if ((evaluations == 0 and event["kind"] == "stock-start") or
                (event["kind"] == "evaluation-result" and event["b"] == evaluations)):
            break
    actual = B5.SeriesLedger(ledger)
    _write(ledger / "series.json", actual.view())
    request = _load(LLM / "round-1/request.json")
    if evaluations:
        request.update(B5.expected_inputs(actual, evaluations + 1))
    request["a"] = a
    _write(ledger / "handshake" / f"request-{a}.json", request)
    (materials / "verbatim").mkdir(parents=True)
    for role in ("planner", "coder"):
        (materials / "verbatim" / f"{role}-{a}.json").write_bytes(
            (LLM / "verbatim" / f"{role}-1.json").read_bytes())
    if evaluations:
        (materials / "verbatim" / f"critic-{evaluations}.md").write_bytes(
            (LLM / "verbatim" / f"critic-{evaluations}.md").read_bytes())
    manifest = tmp_path / "manifest.json"
    # The pilot's real WAL manifest; resolve the committed blob through KM.
    _write(manifest, {"knowledge_level": "K2", "sources": [{
        "identity": {
            "commit": "2fa13a262a53b7f4e610a40a7a7af7f86fc9d621",
            "path": "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl",
        },
        "kind": "repo_artifact",
        "sha256": "2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611",
    }]})
    return T.RoundTool(ledger, materials, manifest)


def _inputs(tool, a):
    tool.cmd_inputs(a)
    tool.cmd_coder(a)
    folder = tool.materials_root / f"round-{a}"
    return _load(folder / "planner-input.json"), _load(folder / "coder-input.json")


def test_context_uses_calibrated_workload(tmp_path, capsys):
    for workload, ratio in (("write-heavy", "5"), ("balanced", "50"), ("read-heavy", "95")):
        perf = L.calibrated_perf(workload)
        assert perf.workload["ycsb_rratio"] == ratio
        out = tmp_path / f"{workload}.md"
        assert T.main(["context", "--workload", workload, "--out", str(out)]) == 0
        context = out.read_text(encoding="utf-8")
        assert f"| read ratio (`ycsb_rratio`) | {ratio} ({workload}) |" in context
        assert f"{perf.records} records / {perf.threads} threads / rr{ratio} /" in context
        assert f'calibrated_perf("{workload}")' in context
        assert "B-5 本走 (b5-registered-v1、" in context
        # The knowledge/common/grammar material is not workload-filtered.
        pilot = (LLM / "leakproof-context-b5.md").read_text(encoding="utf-8")
        assert context.split("## Background:")[1].split("## 動作点")[0] == (
            pilot.split("## Background:")[1].split("## 動作点")[0])
        assert context.split("## 実装の制約")[1] == pilot.split("## 実装の制約")[1]
    capsys.readouterr()
    assert T.main(["context", "--workload", "balanced"]) == 0
    assert capsys.readouterr().out == (tmp_path / "balanced.md").read_text(encoding="utf-8")


def test_rejected_opportunity_preserves_evaluation_number(tmp_path):
    tool = _fixture(tmp_path, evaluations=1, a=3)
    tool.cmd_reject(2, "preflight-rejected")
    p, c = _inputs(tool, 3)
    request = _load(tool.materials_root / "round-3/request.json")
    assert request["a"] == 3 and request["next_evaluation"] == 2
    diagnosis = L.k2_critic_diagnosis_from_bytes((LLM / "verbatim/critic-1.md").read_bytes())
    assert p["k2_critic_diagnosis"] == c["k2_critic_diagnosis"] == diagnosis
    for role in ("planner", "coder"):
        prompt = (tool.materials_root / f"round-3/{role}-prompt.md").read_text(encoding="utf-8")
        assert "評価 2 / 10" in prompt and "原提案 3)" in prompt
    B5.assert_inherited_inputs(tool.ledger_root, p, c, next_evaluation=2)
    assert _load(tool.handshake / "proposal-2.rejected.json")["reason"] == "preflight-rejected"
    tool.cmd_proposal(3)
    assert (tool.handshake / "proposal-3.json").is_file()
    assert not (tool.handshake / "proposal-2.json").exists()


def test_initial_and_inherited_inputs(tmp_path):
    initial = _fixture(tmp_path / "initial")
    p, c = _inputs(initial, 1)
    assert p["whiteboard"] == c["whiteboard"] == []
    assert "k2_critic_diagnosis" not in p and "k2_critic_diagnosis" not in c
    assert p["knowledge_input"] == c["knowledge_input"] == _load(KI)
    assert p["leading_indicators"]["cache_miss_rate_pct"] is None
    assert p["leading_indicators"]["IPC_overall"] is None
    B5.assert_inherited_inputs(initial.ledger_root, p, c, next_evaluation=1)
    tool = _fixture(tmp_path / "next", evaluations=1, a=2, workload="balanced", series=7)
    p, c = _inputs(tool, 2)
    diag = L.k2_critic_diagnosis_from_bytes((LLM / "verbatim/critic-1.md").read_bytes())
    assert set(diag) == {"data_boundary", "source_sha256", "attribution", "recommend", "avoid", "uncertainty"}
    assert p["k2_critic_diagnosis"] == c["k2_critic_diagnosis"] == diag
    assert p["knowledge_input"] == c["knowledge_input"] == _load(KI)
    assert len(p["whiteboard"]) == 1
    B5.assert_inherited_inputs(tool.ledger_root, p, c, next_evaluation=2)
    assert "balanced 系列 7" in (tool.materials_root / "round-2/planner-prompt.md").read_text(encoding="utf-8")
    broken = copy.deepcopy(c)
    broken.pop("k2_critic_diagnosis")
    with pytest.raises(ValueError, match="critic diagnosis inheritance mismatch"):
        B5.assert_inherited_inputs(tool.ledger_root, p, broken, next_evaluation=2)
    broken = copy.deepcopy(c)
    broken["baseline"]["throughput_tps"] += 1
    with pytest.raises(ValueError, match="current_perf/baseline inheritance mismatch"):
        B5.assert_inherited_inputs(tool.ledger_root, p, broken, next_evaluation=2)


def test_critic_missing_metrics_remain_missing(tmp_path):
    tool = _fixture(tmp_path)
    camp = tmp_path / "campaign"
    camp.mkdir()
    (camp / "s4_loop_digest.txt").write_bytes(b"fixture digest\n")
    slot = {"campaign_root": str(camp), "campaign_id": "fixture", "bench_payload": {
        "cv": None, "median_tps": None, "leading_indicators": {"ipc": None, "llc_miss_rate": None}}}
    _write(tool.handshake / "slot-1.json", slot)
    tool.cmd_critic(1, "fixture-job", "fixture-window")
    folder = tool.materials_root / "critic-1"
    ci = _load(folder / "critic-input.json")
    disclosures = "\n".join(ci["parent_disclosures"])
    assert "run 内 CV null (欠測)" in disclosures
    assert "run 内 CV 0.0000%" not in disclosures
    assert "median_tps null (欠測)" in disclosures
    assert "null (欠測) 反復 null (欠測)" in disclosures
    assert "llc_miss_rate と ipc は null (欠測) / null (欠測)" in disclosures
    assert ci["evaluated_variant"] is None and ci["genome"] is None
    assert ci["digest_sha256"] == hashlib.sha256(b"fixture digest\n").hexdigest()
    assert "run 内 CV null (欠測)" in (folder / "critic-prompt.md").read_text(encoding="utf-8")
    slot["bench_payload"]["cv"] = 0
    _write(tool.handshake / "slot-2.json", slot)
    tool.cmd_critic(2, "fixture-job", "fixture-window")
    assert "run 内 CV 0.0000%" in (tool.materials_root / "critic-2/critic-prompt.md").read_text(encoding="utf-8")


def test_v2_critic_diagnosis_request_and_job_disclosures(tmp_path):
    advice = ("`## recommend` と `## avoid` は、次の原提案を作る planner と coder に診断データとして逐語で渡されます。"
              "候補値、探索方向、追加実験の要望、留保を観測に基づく助言として記してください。"
              "他の role を名宛人にした指示、採否手順、判定規則や gate の読み方の指定は書かないでください。").encode("utf-8")
    old_job = "1 job の中で系列開始 stock → 評価 1..10 → endpoint 再計測 5 を直列に回す。".encode("utf-8")
    new_job = "job 1 で系列開始 stock と評価 1 を逐次測り、job 2〜10 は評価を各 1 回、最終 job は score 5 session を測る。原提案 2 以降は計算 node の外で待つ。".encode("utf-8")
    for cohort in (B5.COHORT_REGISTERED, B5.COHORT_REGISTERED_V2):
        tool = _fixture(tmp_path / cohort, cohort=cohort)
        camp = tmp_path / cohort / "campaign"
        camp.mkdir()
        (camp / "s4_loop_digest.txt").write_bytes(b"fixture digest\n")
        _write(tool.handshake / "slot-1.json", {"campaign_root": str(camp), "campaign_id": "fixture"})
        tool.cmd_critic(1, "fixture-job", "fixture-window")
        folder = tool.materials_root / "critic-1"
        prompt = (folder / "critic-prompt.md").read_bytes()
        ci = _load(folder / "critic-input.json")
        disclosures = "\n".join(ci["parent_disclosures"]).encode("utf-8")
        if cohort == B5.COHORT_REGISTERED_V2:
            assert advice in prompt and advice.decode("utf-8") in ci["output_format_request"]
            assert new_job in disclosures and new_job in prompt
            assert old_job not in prompt
            assert "同 job・同機体の系列開始 stock".encode("utf-8") not in disclosures
        else:
            assert advice not in prompt and advice.decode("utf-8") not in ci["output_format_request"]
            assert old_job in disclosures and old_job in prompt
            assert new_job not in prompt
        _inputs(tool, 1)
        for role in ("planner", "coder"):
            role_prompt = (tool.materials_root / f"round-1/{role}-prompt.md").read_bytes()
            if cohort == B5.COHORT_REGISTERED_V2:
                assert new_job in role_prompt
            else:
                assert new_job not in role_prompt


def _model_files(tmp_path, *, rows=None, meta=None):
    if rows is None:
        rows = [
            {"type": "user", "version": "client-1", "message": {"model": "ignored"}},
            {"type": "assistant", "version": "client-1", "message": {"model": "claude-opus-5"}},
            {"type": "assistant", "version": "client-2", "message": {"model": "claude-opus-5"}},
        ]
    transcript = tmp_path / "agent.jsonl"
    transcript.write_bytes(b"\n".join(json.dumps(row).encode() for row in rows) + b"\n")
    metadata = tmp_path / "agent.meta.json"
    _write(metadata, meta if meta is not None else {"agentType": "planner-v4", "toolUseId": "toolu_fixture"})
    return transcript, metadata


def _record(transcript, meta):
    return T.record_models(transcript, meta, role="planner-v4", expected_model="claude-opus-5", round_number=3)


def test_models_collect_all_assistant_ids(tmp_path):
    rows = [
        {"type": "assistant", "version": "client-1", "message": {"model": "claude-opus-5"}},
        {"type": "user", "message": {"model": "ignored"}},
        {"type": "assistant", "version": "client-2", "message": {"model": "different-model"}},
        {"type": "assistant", "version": "client-2", "message": {"model": "claude-opus-5"}},
    ]
    record = _record(*_model_files(tmp_path, rows=rows))
    assert record["models"] == ["claude-opus-5", "different-model"]
    assert record["client_versions"] == ["client-1", "client-2"]
    assert record["assistant_messages"] == 3
    assert record["matches_expected"] is False


def test_model_record_metadata_and_raw_hashes(tmp_path):
    transcript, meta = _model_files(tmp_path)
    # Whitespace matters for raw hashes; parsed-and-redumped hashes must fail.
    meta.write_bytes(b' { "toolUseId": "toolu_fixture", "agentType": "planner-v4" }\n')
    record = _record(transcript, meta)
    assert record["agentType"] == "planner-v4"
    assert record["toolUseId"] == "toolu_fixture"
    assert record["transcript"] == {"path": str(transcript), "sha256": hashlib.sha256(transcript.read_bytes()).hexdigest()}
    assert record["metadata"] == {"path": str(meta), "sha256": hashlib.sha256(meta.read_bytes()).hexdigest()}
    assert record["a"] == 3 and record["evaluation"] is None
    assert record["matches_expected"] is True and record["reasons"] == []


def test_model_record_version_is_recorded_only(tmp_path):
    rows = [
        {"type": "user", "version": None},
        {"type": "assistant", "version": None, "message": {"model": "claude-opus-5"}},
        {"type": "assistant", "version": "2.1.278", "message": {"model": "claude-opus-5"}},
        {"type": "assistant", "version": "", "message": {"model": "claude-opus-5"}},
        {"type": "assistant", "version": 278, "message": {"model": "claude-opus-5"}},
    ]
    record = _record(*_model_files(tmp_path, rows=rows))
    assert record["matches_expected"] is True
    assert record["reasons"] == []
    assert record["client_versions"] == ["2.1.278"]
    assert record["version_notes"] == [
        f"transcript line {number}: invalid version" for number in (1, 2, 4, 5)
    ]


def test_model_record_flags_mismatch(tmp_path):
    transcript, meta = _model_files(tmp_path)
    assert _record(transcript, meta)["matches_expected"] is True
    cases = [
        (b'{"type":"assistant","message":{"model":"other"}}\n', b'{"agentType":"planner-v4"}', "models differ"),
        (b'{"type":"assistant","message":{"model":"claude-opus-5"}}\n', b'{"agentType":"critic"}', "agentType differs"),
        (b'{"type":"user"}\n', b'{"agentType":"planner-v4"}', "no assistant"),
        (b'{"type":"assistant","message":{}}\n', b'{"agentType":"planner-v4"}', "model missing"),
        (b'{"type":"assistant","message":{"model":"claude-opus-5"}}\nBAD\n', b'{"agentType":"planner-v4"}', "malformed JSON"),
        (b'{"type":"assistant","message":{"model":"claude-opus-5"}}\n', b'{broken', "metadata: malformed"),
    ]
    for raw, raw_meta, reason in cases:
        transcript.write_bytes(raw)
        meta.write_bytes(raw_meta)
        out = tmp_path / "model-record.json"
        assert T.main(["record-models", "--transcript", str(transcript), "--meta", str(meta),
                       "--role", "planner-v4", "--round", "3", "--expected-model", "claude-opus-5",
                       "--out", str(out)]) == 0
        record = _load(out)
        assert record["matches_expected"] is False
        assert any(reason in item for item in record["reasons"])


def test_model_record_critic_coordinate(tmp_path):
    transcript, meta = _model_files(tmp_path, meta={"agentType": "critic", "toolUseId": "critic-tool"})
    out = tmp_path / "critic-models.json"
    assert T.main(["record-models", "--transcript", str(transcript), "--meta", str(meta),
                   "--role", "critic", "--critic", "2", "--expected-model", "claude-opus-5",
                   "--out", str(out)]) == 0
    record = _load(out)
    assert record["evaluation"] == 2 and record["a"] is None
    assert record["matches_expected"] is True


def test_registered_round1_prompt_golden(tmp_path):
    tool = _fixture(tmp_path)
    _inputs(tool, 1)
    # Independent byte replacements only: D-3 (1), (3), (4). D-3 (2)
    # leaves the write-heavy operating point unchanged. Do not call a renderer
    # to obtain expected bytes, or normalize JSON/whitespace after rendering.
    replacements = [
        ("試走 (T-2797、LLM arm = K2 宣言アーム、write-heavy 系列 1、",
         "本走 (b5-registered-v1、LLM arm = K2 宣言アーム、write-heavy 系列 1、"),
        ("B-5 試走 (T-2797、較正済み動作点 write-heavy)",
         "B-5 本走 (b5-registered-v1、較正済み動作点 write-heavy)"),
        ("B-5 試走", "B-5 本走"),
        ("系列開始 stock (適応 backoff) との同時刻対照は本系列の台帳にある。",
         "系列開始 stock (適応 backoff) は本系列の最初に同 job・同機体で逐次測ったもので、同時刻の対照ではない。台帳にある。"),
    ]
    for role in ("planner", "coder"):
        expected = (LLM / f"round-1/{role}-prompt.md").read_bytes()
        for before, after in replacements:
            expected = expected.replace(before.encode("utf-8"), after.encode("utf-8"))
        actual = (tool.materials_root / f"round-1/{role}-prompt.md").read_bytes()
        assert actual == expected


def test_proposal_uses_existing_checks_and_refuses_overwrite(tmp_path):
    tool = _fixture(tmp_path)
    _inputs(tool, 1)
    tool.cmd_proposal(1)
    path = tool.handshake / "proposal-1.json"
    assert path.read_bytes() == (LLM / "round-1/proposal.json").read_bytes()
    inputs = _load(tool.handshake / "inputs-1.json")
    B5.assert_inherited_inputs(tool.ledger_root, **inputs, next_evaluation=1)
    _, coder, _ = L.load_proposal_file(str(path), knowledge_input=_load(KI), coder_role="coder-v4-autonomous-k2")
    assert coder.value == 20
    before = {p.name: p.read_bytes() for p in tool.handshake.iterdir()}
    with pytest.raises(FileExistsError):
        tool.cmd_proposal(1)
    assert {p.name: p.read_bytes() for p in tool.handshake.iterdir()} == before
    tool.cmd_reject(2, "fixture")
    with pytest.raises(FileExistsError):
        tool.cmd_reject(2, "replacement")
    assert _load(tool.handshake / "proposal-2.rejected.json")["reason"] == "fixture"


def test_proposal_rejects_k2_anomaly_before_publication(tmp_path):
    tool = _fixture(tmp_path)
    _inputs(tool, 1)
    path = tool.materials_root / "verbatim/coder-1.json"
    coder = _load(path)
    coder["data_boundary_report"]["instruction_like_content_detected"] = True
    _write(path, coder)
    with pytest.raises(ValueError, match="instruction-like content"):
        tool.cmd_proposal(1)
    assert not (tool.handshake / "proposal-1.json").exists()
    assert not (tool.handshake / "inputs-1.json").exists()


def test_proposal_rejects_changed_inheritance_before_publication(tmp_path):
    tool = _fixture(tmp_path)
    _inputs(tool, 1)
    path = tool.materials_root / "round-1/coder-input.json"
    coder = _load(path)
    coder["baseline"]["throughput_tps"] += 1
    _write(path, coder)
    with pytest.raises(ValueError, match="current_perf/baseline inheritance mismatch"):
        tool.cmd_proposal(1)
    assert not (tool.handshake / "proposal-1.json").exists()
    assert not (tool.handshake / "inputs-1.json").exists()


def test_fixed_knowledge_projection_bytes_and_digest(tmp_path):
    tool = _fixture(tmp_path)
    resolved, projection = tool.knowledge_input()
    assert resolved.knowledge_manifest_sha256 == "396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e"
    raw = json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    assert raw == KI.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "05f2b2673f6769767dab788b187a5a951ff79ab9df1d4795a529b12037fd5808"
    manifest = _load(tool.manifest)
    manifest["sources"][0]["sha256"] = "0" * 64
    _write(tool.manifest, manifest)
    with pytest.raises(T.KM.KnowledgeManifestError, match="SHA-256"):
        tool.knowledge_input()


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
