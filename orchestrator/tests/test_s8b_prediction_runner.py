# -*- coding: utf-8 -*-
"""段 8b R3 trusted prediction runner の at-most-once・journal 契約テスト。

受入ベクトル V7 (`output/insights/2026-07-16_s8b-freeze-v2-design-material.md` 付録 2):
同一セル二重 claim 拒否 + claim 後 crash 模擬から再起動して当該セル missing 恒久確定
(journal に invocation record が 1 件も増えない) を中核に据える。
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path

import pytest

from orchestrator.campaign.s8b_prediction_runner import (
    CLAUDE_ENV_ALLOWLIST,
    CLAUDE_TIMEOUT_S,
    ClaudeHeadlessProvider,
    JOURNAL_SCHEMA_VERSION,
    JournalBinding,
    PRODUCTION_PROVIDER,
    PredictionJournal,
    PredictionRunnerError,
    ProviderResponse,
    _write_bytes_bound,
    build_rows_from_journal,
    drive_journal,
    ensure_run_header,
    main,
    materialize_predictions,
    resolve_journal,
)
from orchestrator.campaign.s8b_selector_freeze import verify_prediction_freeze

ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"

# jobs 列挙順 (build_prediction_jobs): sorted target × (on, off, swapped)
FIRST_AGENT_CELL = ("rr20", "on")
AGENT_CELLS = {("rr20", "on"), ("rr20", "swapped"), ("rr80", "on"), ("rr80", "swapped")}
OFF_CELLS = {("rr20", "off"), ("rr80", "off")}


def _freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _binding(
    *, pre_oracle_head: str = "2" * 40, role_sha256: str = "0" * 64,
    protocol_sha256: str = "1" * 64, freeze_sha256: str | None = None,
    provider_kind: str = "fixture",
) -> JournalBinding:
    return JournalBinding(
        pre_oracle_head=pre_oracle_head,
        protocol_sha256=protocol_sha256,
        freeze_sha256=freeze_sha256 or hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        provider_kind=provider_kind,
        role_file_sha256=role_sha256,
        parser_module_sha256=hashlib.sha256(
            (ROOT / "orchestrator/campaign/s8b_selector_output.py").read_bytes()
        ).hexdigest(),
    )


def _journal(path: Path, binding: JournalBinding) -> PredictionJournal:
    journal = PredictionJournal(path)
    ensure_run_header(
        journal, binding=binding, created_at="2026-07-22T00:00:00+00:00",
    )
    return journal


def _valid_raw(choice_id: str = "c01", rationale: str = "descriptor と機構を比較した") -> str:
    return json.dumps(
        {
            "schema_version": "8b-selector-output/v1",
            "choice_id": choice_id,
            "rationale": rationale,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _provenance(role_sha256: str, tag: str) -> dict:
    return {
        "child_id": f"child-{tag}",
        "role_file_sha256": role_sha256,
        "model": "fixture-model",
        "started_at": "2026-07-16T00:00:00Z",
        "finished_at": "2026-07-16T00:01:00Z",
        "fresh_context": True,
        "declared_tools": [],
        "observed_tool_events": [],
    }


class _RecordingProvider:
    """呼び出しセルを記録し、指定セルで crash を起こせる注入 provider。"""

    def __init__(self, *, role_sha256: str = "0" * 64, crash_on=None):
        self.role_sha256 = role_sha256
        self.crash_on = set(crash_on or ())
        self.called: list[tuple[str, str]] = []

    def __call__(self, *, target_holdout, arm, payload) -> ProviderResponse:
        cell = (target_holdout, arm)
        self.called.append(cell)
        if cell in self.crash_on:
            raise RuntimeError(f"simulated crash mid-invocation: {cell}")
        return ProviderResponse(
            raw_response=_valid_raw(),
            provenance=_provenance(self.role_sha256, f"{target_holdout}-{arm}"),
        )


def _invocation_count(journal: PredictionJournal, cell=None) -> int:
    records = journal.read_records()
    return sum(
        1
        for rec in records
        if rec.get("record_type") == "invocation"
        and (cell is None or (rec["target_holdout"], rec["arm"]) == cell)
    )


# ------------------------------------------------------------------- run header

def test_run_header_is_first_record_and_matches_binding(tmp_path) -> None:
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    records = journal.read_records()
    assert len(records) == 1
    assert records[0] == {
        "record_type": "run_header",
        "seq": 1,
        "schema": JOURNAL_SCHEMA_VERSION,
        "pre_oracle_head": binding.pre_oracle_head,
        "protocol_sha256": binding.protocol_sha256,
        "freeze_sha256": binding.freeze_sha256,
        "provider_kind": binding.provider_kind,
        "role_file_sha256": binding.role_file_sha256,
        "parser_module_sha256": binding.parser_module_sha256,
        "created_at": "2026-07-22T00:00:00+00:00",
    }
    assert resolve_journal(records, binding=binding) == {}


def test_resolve_rejects_headerless_journal(tmp_path) -> None:
    binding = _binding()
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    with pytest.raises(PredictionRunnerError, match="run_header"):
        resolve_journal(journal.read_records(), binding=binding)
    journal.append({
        "record_type": "claim", "target_holdout": "rr20", "arm": "on",
        "decision_method": "selector_agent", "input_payload_sha256": "a" * 64,
        "payload_path": "payload.json", "claimed_at": "2026-07-22T00:00:00Z",
    })
    with pytest.raises(PredictionRunnerError, match="run_header"):
        resolve_journal(journal.read_records(), binding=binding)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("pre_oracle_head", "3" * 40),
        ("protocol_sha256", "3" * 64),
        ("freeze_sha256", "4" * 64),
        ("provider_kind", "other-provider"),
        ("role_file_sha256", "5" * 64),
        ("parser_module_sha256", "6" * 64),
    ],
)
def test_run_header_mismatch_is_rejected(tmp_path, field, replacement) -> None:
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    mismatched = replace(binding, **{field: replacement})
    with pytest.raises(PredictionRunnerError, match=field):
        resolve_journal(journal.read_records(), binding=mismatched)


# --------------------------------------------------------------------------- V7

def test_v7_double_claim_is_protocol_violation(tmp_path) -> None:
    """同一セルへの二度目の claim record は protocol violation として拒否される。"""
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    claim = {
        "record_type": "claim",
        "target_holdout": "rr20",
        "arm": "on",
        "decision_method": "selector_agent",
        "input_payload_sha256": "a" * 64,
        "payload_path": "artifacts/payload_rr20_on.json",
        "claimed_at": "2026-07-16T00:00:00Z",
    }
    journal.append(claim)
    journal.append(dict(claim))  # 同一セルの二度目の claim

    with pytest.raises(PredictionRunnerError, match="二重 claim"):
        resolve_journal(journal.read_records(), binding=binding)


def test_v7_claim_then_crash_stays_missing_without_recall(tmp_path) -> None:
    """claim 後 crash → 再起動で当該セルは missing 恒久確定、再呼出も invocation 追記もない。"""
    freeze = _freeze()
    root = tmp_path
    head = _fixture_head(root)
    sources = _sources(root)
    binding = _binding(pre_oracle_head=head, role_sha256=sources["role"]["sha256"])
    journal = _journal(tmp_path / "journal.jsonl", binding)
    artifact_root = tmp_path / "artifacts"

    # 第 1 走: 最初の agent セルの invocation 中に crash させる。
    crashing = _RecordingProvider(
        role_sha256=sources["role"]["sha256"], crash_on={FIRST_AGENT_CELL},
    )
    with pytest.raises(RuntimeError, match="simulated crash"):
        drive_journal(
            freeze=freeze, journal=journal, artifact_root=artifact_root,
            root=root, binding=binding, provider=crashing,
        )

    # crash 後: claim は durable、invocation は 1 件も書かれていない。
    statuses = resolve_journal(journal.read_records(), binding=binding)
    assert statuses[FIRST_AGENT_CELL].kind == "claimed_missing"
    assert _invocation_count(journal, FIRST_AGENT_CELL) == 0
    invocations_before = _invocation_count(journal)

    # 再起動: 成功する provider を注入して drive をやり直す。
    resumed = _RecordingProvider(role_sha256=sources["role"]["sha256"])
    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=artifact_root,
        root=root, binding=binding, provider=resumed,
    )

    # 恒久 missing: 当該セルは再呼出されず invocation は依然 0 件。
    assert FIRST_AGENT_CELL not in resumed.called
    assert statuses[FIRST_AGENT_CELL].kind == "claimed_missing"
    assert _invocation_count(journal, FIRST_AGENT_CELL) == 0

    # 他の未着手 agent セルだけは再起動時に前進する (missing の巻き添えにしない)。
    assert set(resumed.called) == AGENT_CELLS - {FIRST_AGENT_CELL}
    invocations_after = _invocation_count(journal)
    assert invocations_after - invocations_before == len(AGENT_CELLS) - 1

    # R3 裁定: missing を choice_id=null/provenance=null で含む 6 行が組める。
    rows = build_rows_from_journal(freeze, journal, binding=binding)
    assert len(rows) == 6
    missing = next(
        row for row in rows
        if (row["target_holdout"], row["arm"]) == FIRST_AGENT_CELL
    )
    assert missing["status"] == "missing"
    for field in (
        "choice_id", "rationale", "parser_error_code", "raw_response_path",
        "raw_sha256", "agent_provenance",
    ):
        assert missing[field] is None

    predictions = root / "output/s8b-freeze/selector_predictions.json"
    document = materialize_predictions(
        freeze=freeze, journal=journal, predictions_path=predictions,
        generated_at="2026-07-22T00:10:00+00:00", pre_oracle_head=head,
        sources=sources, execution_policy=_policy(), binding=binding,
    )
    assert len(document["rows"]) == 6
    frozen_missing = next(
        row for row in document["rows"]
        if (row["target_holdout"], row["arm"]) == FIRST_AGENT_CELL
    )
    assert frozen_missing["status"] == "missing"
    assert frozen_missing["choice_id"] is None
    assert frozen_missing["agent_provenance"] is None
    verify_prediction_freeze(document, freeze=freeze, root=root)


# ------------------------------------------------------------- provider 未配線

def test_production_provider_refuses_before_claiming(tmp_path) -> None:
    """production 未配線 provider は claim を書く前に拒否し journal を汚染しない。"""
    freeze = _freeze()
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)

    with pytest.raises(PredictionRunnerError, match="未解禁"):
        drive_journal(
            freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
            root=tmp_path, binding=binding, provider=PRODUCTION_PROVIDER,
        )

    # off arm の static terminal は書かれ得るが、agent セルの claim は 1 件もない。
    records = journal.read_records()
    assert not any(rec["record_type"] == "claim" for rec in records)


def test_unwired_provider_call_raises() -> None:
    """未配線 provider を直接呼んでも fail-closed で拒否する。"""
    with pytest.raises(PredictionRunnerError, match="未配線"):
        PRODUCTION_PROVIDER(target_holdout="rr20", arm="on", payload={})


# ------------------------------------------------------------- protocol 違反

def test_invocation_without_claim_is_protocol_violation(tmp_path) -> None:
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    journal.append({
        "record_type": "invocation",
        "target_holdout": "rr20",
        "arm": "on",
        "status": "valid",
        "choice_id": "c01",
        "rationale": "x",
        "parser_error_code": None,
        "raw_response_path": "artifacts/raw_rr20_on.txt",
        "raw_sha256": "b" * 64,
        "receipt": {},
    })
    with pytest.raises(PredictionRunnerError, match="claim なき invocation"):
        resolve_journal(journal.read_records(), binding=binding)


def test_static_terminal_on_agent_arm_is_rejected(tmp_path) -> None:
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    journal.append({
        "record_type": "static_terminal",
        "target_holdout": "rr20",
        "arm": "on",
        "decision_method": "static_default",
        "choice_id": "c06",
    })
    with pytest.raises(PredictionRunnerError, match="off arm 専用"):
        resolve_journal(journal.read_records(), binding=binding)


def test_unknown_record_type_is_rejected(tmp_path) -> None:
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    journal.append({"record_type": "bogus", "target_holdout": "rr20", "arm": "on"})
    with pytest.raises(PredictionRunnerError, match="record_type"):
        resolve_journal(journal.read_records(), binding=binding)


# ------------------------------------------------------------- 正常駆動

def test_off_arms_are_static_terminal_without_invocation(tmp_path) -> None:
    """off arm 2 セルは invocation を持たない static terminal として区別される。"""
    freeze = _freeze()
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, binding=binding, provider=_RecordingProvider(),
    )
    for cell in OFF_CELLS:
        assert statuses[cell].kind == "static"
        assert statuses[cell].invocation is None
    # off セルに invocation record は存在しない。
    for cell in OFF_CELLS:
        assert _invocation_count(journal, cell) == 0


def test_invalid_raw_recorded_as_invalid_without_fallback(tmp_path) -> None:
    """strict parser を通らない応答は invalid として記録し既定構成へ fallback しない。"""
    freeze = _freeze()
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)

    class _BadProvider(_RecordingProvider):
        def __call__(self, *, target_holdout, arm, payload):
            self.called.append((target_holdout, arm))
            return ProviderResponse(
                raw_response="```json\n{}\n```",  # markdown fence → parser 拒否
                provenance=_provenance(self.role_sha256, f"{target_holdout}-{arm}"),
            )

    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, binding=binding, provider=_BadProvider(),
    )
    for cell in AGENT_CELLS:
        invocation = statuses[cell].invocation
        assert invocation is not None
        assert invocation["status"] == "invalid"
        assert invocation["choice_id"] is None  # fallback しない
        assert invocation["parser_error_code"] == "markdown_fence"


# ------------------------------------------------------ Claude headless provider

def _executable(tmp_path: Path) -> Path:
    executable = tmp_path / "claude-fixture"
    executable.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    executable.chmod(0o755)
    return executable


def _envelope(**overrides) -> dict:
    envelope = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "permission_denials": [],
        "result": _valid_raw(),
        "session_id": "session-fixture-001",
        "modelUsage": {
            "claude-opus-4-6": {"inputTokens": 120, "outputTokens": 30},
            "claude-haiku-4-5": {"inputTokens": 4, "outputTokens": 2},
        },
        "usage": {"server_tool_use": {"web_search_requests": 0, "web_fetch_requests": 0}},
        "duration_ms": 1500,
        "duration_api_ms": 1400,
        "total_cost_usd": 0.42,
        "stop_reason": "end_turn",
        "uuid": "uuid-fixture",
        "errors": [],
        "structured_output": None,
        "input_tokens": 120,
        "output_tokens": 30,
        "cache_read_input_tokens": 0,
        "future_cli_field": {"unknown": "allowed"},
    }
    assert len(envelope) == 20
    envelope.update(overrides)
    return envelope


class _FakeSubprocessRunner:
    def __init__(self, envelope: dict, *, returncode: int = 0):
        self.envelope = envelope
        self.returncode = returncode
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs)))
        return SimpleNamespace(
            returncode=self.returncode,
            stdout=json.dumps(
                self.envelope, ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8"),
            stderr=b"",
        )


def _provider_call(tmp_path: Path, envelope: dict):
    artifact_root = tmp_path / "artifacts"
    runner = _FakeSubprocessRunner(envelope)
    provider = ClaudeHeadlessProvider(
        artifact_root=artifact_root,
        role_file=ROOT / ".claude/agents/selector-8b.md",
        executable=_executable(tmp_path),
        runner=runner,
        environ={
            "PATH": "/fixture/bin", "HOME": "/fixture/home", "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "TERM": "dumb", "SECRET_TOKEN": "must-not-leak",
        },
    )
    payload = _payload_for_first_job()
    payload_bytes = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    _write_bytes_bound(artifact_root / "payload_rr20_on.json", payload_bytes)
    response = provider(target_holdout="rr20", arm="on", payload=payload)
    return provider, runner, response, payload_bytes


def _payload_for_first_job() -> dict:
    from orchestrator.campaign.s8b_selector_freeze import build_prediction_jobs
    from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
    from orchestrator.campaign.s8b_selector_input import build_selector_payload

    freeze = _freeze()
    first = next(
        job for job in build_prediction_jobs(freeze)
        if (job["target_holdout"], job["arm"]) == FIRST_AGENT_CELL
    )
    return build_selector_payload(
        descriptor_for_holdout(freeze["holdouts"][first["descriptor_source_holdout"]])
    )


def test_claude_headless_argv_stdin_env_and_neutral_cwd(tmp_path) -> None:
    provider, runner, response, payload_bytes = _provider_call(tmp_path, _envelope())
    assert len(runner.calls) == 1
    argv, kwargs = runner.calls[0]
    assert argv == [
        str(_executable_path := provider.executable),
        "-p",
        "--agent", "selector-8b-inline",
        "--agents", provider.inline_agents_json,
        "--output-format", "json",
        "--input-format", "text",
        "--effort", "high",
        "--setting-sources", "",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config", str(provider.mcp_config_path),
        "--no-session-persistence",
    ]
    assert Path(_executable_path).is_absolute()
    assert kwargs == {
        "input": payload_bytes,
        "cwd": str(provider.neutral_cwd),
        "env": {
            "PATH": "/fixture/bin", "HOME": "/fixture/home", "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "TERM": "dumb",
        },
        "timeout": CLAUDE_TIMEOUT_S,
        "check": False,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    assert set(kwargs["env"]) == set(CLAUDE_ENV_ALLOWLIST)
    assert list(provider.neutral_cwd.iterdir()) == []
    assert json.loads(provider.inline_agents_json)["selector-8b-inline"]["tools"] == []
    assert response.raw_response == _valid_raw()
    assert (provider.artifact_root / "envelope_rr20_on.json").read_bytes() == (
        runner.calls[0][1] and json.dumps(
            runner.envelope, ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
    )


def test_claude_headless_provenance_uses_envelope_measurements(tmp_path) -> None:
    provider, _, response, _ = _provider_call(tmp_path, _envelope())
    assert set(response.provenance) == {
        "child_id", "role_file_sha256", "model", "started_at", "finished_at",
        "fresh_context", "declared_tools", "observed_tool_events",
    }
    assert response.provenance["child_id"] == "session-fixture-001"
    assert response.provenance["model"] == "claude-opus-4-6"
    assert response.provenance["role_file_sha256"] == provider.role_file_sha256
    assert response.provenance["fresh_context"] is True
    assert response.provenance["declared_tools"] == []
    assert response.provenance["observed_tool_events"] == []
    started = response.provenance["started_at"]
    finished = response.provenance["finished_at"]
    assert isinstance(started, str) and "+00:00" in started
    assert isinstance(finished, str) and "+00:00" in finished
    assert started <= finished


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"is_error": True}, "is_error"),
        ({"subtype": "error"}, "type/subtype"),
        ({"num_turns": 2}, "num_turns"),
        ({"permission_denials": [{"tool": "Read"}]}, "permission_denials"),
        ({"result": {"choice_id": "c01"}}, "result は str"),
        ({"modelUsage": {"claude-haiku-4-5": {}}}, "claude-opus"),
    ],
)
def test_claude_headless_rejects_invalid_envelope(tmp_path, overrides, message) -> None:
    with pytest.raises(PredictionRunnerError, match=message):
        _provider_call(tmp_path, _envelope(**overrides))


def test_claude_headless_rejects_observed_server_tool_use(tmp_path) -> None:
    with pytest.raises(PredictionRunnerError, match="server tool use"):
        _provider_call(
            tmp_path,
            _envelope(usage={"server_tool_use": {"web_search_requests": 1}}),
        )


def _provider_with_raw_runner(tmp_path: Path, runner) -> tuple[ClaudeHeadlessProvider, dict]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact_root = tmp_path / "artifacts"
    provider = ClaudeHeadlessProvider(
        artifact_root=artifact_root,
        role_file=ROOT / ".claude/agents/selector-8b.md",
        executable=_executable(tmp_path), runner=runner,
        environ={"HOME": "/fixture/home"},
    )
    payload = _payload_for_first_job()
    payload_bytes = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    _write_bytes_bound(artifact_root / "payload_rr20_on.json", payload_bytes)
    return provider, payload


def test_claude_headless_rejects_duplicate_envelope_key(tmp_path) -> None:
    class _DuplicateRunner:
        def __call__(self, argv, **kwargs):
            return SimpleNamespace(
                returncode=0,
                stdout=b'{"type":"result","type":"result"}',
                stderr=b"",
            )

    provider, payload = _provider_with_raw_runner(tmp_path, _DuplicateRunner())
    with pytest.raises(PredictionRunnerError, match="duplicate key"):
        provider(target_holdout="rr20", arm="on", payload=payload)


def test_claude_headless_nonzero_and_timeout_are_fail_closed(tmp_path) -> None:
    class _NonzeroRunner:
        def __call__(self, argv, **kwargs):
            return SimpleNamespace(returncode=7, stdout=b'{"diagnostic":true}', stderr=b"x")

    provider, payload = _provider_with_raw_runner(tmp_path / "nonzero", _NonzeroRunner())
    with pytest.raises(PredictionRunnerError, match="nonzero rc"):
        provider(target_holdout="rr20", arm="on", payload=payload)
    assert (provider.artifact_root / "envelope_rr20_on.json").read_bytes() == b'{"diagnostic":true}'

    class _TimeoutRunner:
        def __call__(self, argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    provider, payload = _provider_with_raw_runner(tmp_path / "timeout", _TimeoutRunner())
    with pytest.raises(PredictionRunnerError, match="timeout"):
        provider(target_holdout="rr20", arm="on", payload=payload)


# --------------------------------------------------- freeze/journal payload 束縛

def _diverged_freeze(freeze: dict) -> dict:
    """holdout ID・derangement を保ったまま descriptor だけ変えた freeze を作る。

    threads を変えると各 holdout の descriptor projection (scale.threads) が変わり、
    build_prediction_jobs が算出する input_payload_sha256 が原 freeze と一致しなくなる。
    """
    diverged = json.loads(json.dumps(freeze))
    for entry in diverged["holdouts"].values():
        entry["threads"] = int(entry["threads"]) * 2
    return diverged


def test_build_rows_rejects_journal_bound_to_other_freeze(tmp_path) -> None:
    """freeze A で駆動した journal を別 descriptor の freeze B で materialize すると拒否。

    claim が束縛した canonical payload sha を job と照合しなければ、agent が実際に見た
    payload と異なる descriptor を消費したと誤って certified される (provenance 汚染)。
    """
    freeze_a = _freeze()
    binding = _binding()
    journal = _journal(tmp_path / "journal.jsonl", binding)
    drive_journal(
        freeze=freeze_a, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, binding=binding, provider=_RecordingProvider(),
    )
    # 原 freeze では全 agent セルが解決し build_rows は通る (回帰防止)。
    rows = build_rows_from_journal(freeze_a, journal, binding=binding)
    assert len(rows) == len(AGENT_CELLS) + len(OFF_CELLS)

    # 同一 holdout ID・derangement のまま descriptor だけ変えた freeze で付け替えを試みる。
    freeze_b = _diverged_freeze(freeze_a)
    # job sha が実際に分岐していること (テストの前提) を確認する。
    from orchestrator.campaign.s8b_selector_freeze import build_prediction_jobs
    sha_a = {(j["target_holdout"], j["arm"]): j["input_payload_sha256"]
             for j in build_prediction_jobs(freeze_a) if j["arm"] in ("on", "swapped")}
    sha_b = {(j["target_holdout"], j["arm"]): j["input_payload_sha256"]
             for j in build_prediction_jobs(freeze_b) if j["arm"] in ("on", "swapped")}
    assert all(sha_a[c] != sha_b[c] for c in sha_a)

    with pytest.raises(PredictionRunnerError, match="freeze/journal 束縛違反"):
        build_rows_from_journal(freeze_b, journal, binding=binding)


# --------------------------------------------------------- lock / bound writer

def test_drive_journal_rejects_second_concurrent_driver(tmp_path) -> None:
    freeze = _freeze()
    binding = _binding()
    journal = _journal(tmp_path / "selector-runs/journal.jsonl", binding)
    artifact_root = journal.path.parent

    class _NestedDriveProvider(_RecordingProvider):
        def __init__(self):
            super().__init__()
            self.second_was_rejected = False

        def __call__(self, *, target_holdout, arm, payload):
            if not self.second_was_rejected:
                with pytest.raises(PredictionRunnerError, match="lock"):
                    drive_journal(
                        freeze=freeze, journal=journal, artifact_root=artifact_root,
                        root=tmp_path, binding=binding,
                        provider=_RecordingProvider(),
                    )
                self.second_was_rejected = True
            return super().__call__(
                target_holdout=target_holdout, arm=arm, payload=payload,
            )

    provider = _NestedDriveProvider()
    drive_journal(
        freeze=freeze, journal=journal, artifact_root=artifact_root,
        root=tmp_path, binding=binding, provider=provider,
    )
    assert provider.second_was_rejected is True


def test_write_bytes_bound_is_create_only(tmp_path) -> None:
    destination = tmp_path / "artifact.bin"
    assert _write_bytes_bound(destination, b"first") == hashlib.sha256(b"first").hexdigest()
    with pytest.raises(PredictionRunnerError, match="create-only"):
        _write_bytes_bound(destination, b"second")
    assert destination.read_bytes() == b"first"


def test_write_bytes_bound_detects_real_file_readback_mismatch(tmp_path) -> None:
    destination = tmp_path / "artifact.bin"

    def corrupt_real_file(path: Path) -> bytes:
        path.write_bytes(b"corrupted-after-fsync")
        return path.read_bytes()

    with pytest.raises(PredictionRunnerError, match="read-back bytes 不一致"):
        _write_bytes_bound(destination, b"expected", _read_back=corrupt_real_file)
    assert destination.read_bytes() == b"corrupted-after-fsync"


# ------------------------------------------------------------- materialize 統合

def _fixture_head(root: Path) -> str:
    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()

    _git("init", "-q")
    _git(
        "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false",
        "commit", "--allow-empty", "-q", "-m", "fixture",
    )
    return _git("rev-parse", "HEAD")


def _sources(root: Path) -> dict:
    originals = {
        "holdout_freeze": FREEZE_PATH,
        "builder": ROOT / "orchestrator/campaign/s8b_selector_input.py",
        "role": ROOT / ".claude/agents/selector-8b.md",
        "input_schema": ROOT / "orchestrator/campaign/s8b_selector_catalog.json",
        "output_schema": ROOT / "orchestrator/campaign/s8b_selector_output_schema.json",
    }
    records = {}
    for name, original in originals.items():
        destination = root / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(original.read_bytes())
        records[name] = {
            "path": f"source/{name}",
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        }
    return records


def _policy() -> dict:
    return {
        "attempts_per_agent_cell": 1,
        "retry": False,
        "reuse_equal_payload_output": False,
        "fresh_context": True,
        "declared_tools": [],
    }


def test_materialize_seals_predictions_and_verifies(tmp_path) -> None:
    """全セル解決 → selector_predictions.json を exclusive-create で封印し verify を通す。"""
    freeze = _freeze()
    root = tmp_path
    head = _fixture_head(root)
    sources = _sources(root)
    binding = _binding(pre_oracle_head=head, role_sha256=sources["role"]["sha256"])
    journal = _journal(root / "journal.jsonl", binding)

    drive_journal(
        freeze=freeze, journal=journal, artifact_root=root / "artifacts",
        root=root, binding=binding,
        provider=_RecordingProvider(role_sha256=sources["role"]["sha256"]),
    )

    predictions_path = root / "output/s8b-freeze/selector_predictions.json"
    document = materialize_predictions(
        freeze=freeze,
        journal=journal,
        predictions_path=predictions_path,
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=head,
        sources=sources,
        execution_policy=_policy(),
        binding=binding,
    )
    # selector_basis が束縛されている (既存 API 経由)。
    assert document["selector_basis_sha256"]
    verify_prediction_freeze(document, freeze=freeze, root=root)

    # exclusive-create: 二度目の封印は拒否される。
    with pytest.raises(Exception):
        materialize_predictions(
            freeze=freeze,
            journal=journal,
            predictions_path=predictions_path,
            generated_at="2026-07-16T00:00:00Z",
            pre_oracle_head=head,
            sources=sources,
            execution_policy=_policy(),
            binding=binding,
        )


# -------------------------------------------------------------------- seal CLI

def _fixture_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def _seal_repo(tmp_path: Path, *, protocol_mismatch: bool = False) -> tuple[Path, str]:
    from orchestrator.campaign import s8b_approved, s8b_floor_campaign

    root = tmp_path / "seal-repo"
    root.mkdir()
    _fixture_git(root, "init", "-q")
    relative_sources = [
        "output/s8b-freeze/holdout_freeze.json",
        "orchestrator/campaign/s8b_selector_input.py",
        ".claude/agents/selector-8b.md",
        "orchestrator/campaign/s8b_selector_catalog.json",
        "orchestrator/campaign/s8b_selector_output_schema.json",
        "orchestrator/campaign/s8b_selector_output.py",
    ]
    for relative in relative_sources:
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    (root / "external/ccbench").mkdir(parents=True)
    _fixture_git(root, "add", *relative_sources)
    _fixture_git(
        root, "update-index", "--add", "--cacheinfo",
        f"160000,{s8b_approved.CCBENCH_FULL_SHA},external/ccbench",
    )
    _fixture_git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seal fixture base",
    )
    built = s8b_floor_campaign.build_protocol_document(
        s8b_approved.APPROVED_MASTER_SEED,
        s8b_approved.APPROVED_ENV_TAG,
        stock_configuration=s8b_approved.APPROVED_STOCK_CONFIGURATION,
        extime_s=s8b_approved.APPROVED_EXTIME_S,
        wired_min_rel_floor=s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR,
        root=root,
    )
    protocol_path = root / "output/s8b-freeze/floor_protocol.json"
    protocol_path.write_bytes(
        built.canonical_bytes + (b"\n" if protocol_mismatch else b""),
    )
    _fixture_git(root, "add", str(protocol_path.relative_to(root)))
    _fixture_git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "freeze protocol",
    )
    head = _fixture_git(root, "rev-parse", "HEAD")
    assert _fixture_git(root, "status", "--porcelain") == ""
    return root, head


class _SealRunner:
    def __init__(self):
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs)))
        envelope = _envelope(session_id=f"seal-session-{len(self.calls)}")
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                envelope, ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8"),
            stderr=b"",
        )


def test_seal_requires_explicit_provider_before_any_claim(tmp_path) -> None:
    root, head = _seal_repo(tmp_path)
    output = io.StringIO()
    error = io.StringIO()
    assert main(
        ["seal", "--pre-oracle-head", head], root=root,
        stdout=output, stderr=error,
    ) == 1
    assert "明示 opt-in" in error.getvalue()
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    assert not journal_path.exists()


def test_seal_rejects_tampered_freeze_before_any_claim(tmp_path) -> None:
    """差し替え freeze からの封印は claim 前に fail-closed で拒否される。

    v1 freeze 改変はニ層で検出される: 先行 = protocol 再導出時の builder 承認定数照合
    (APPROVED_FREEZE_SHA256)、後段 = seal read-once bytes の v1 trust root 照合
    (verify-use 間 TOCTOU 遮断の冗長ゲート、C2-7)。この fixture は先行層で落ちるため
    後段単独の検出力の証拠にはならない (変異裏取りは両層同時変異で行う)。executable は
    実行可能 fake を使う — 両層とも無効化されたとき preflight でなく封印進行そのもので
    赤くなる (rc==1 が破れる) 形を保つため。"""
    root, _ = _seal_repo(tmp_path)
    freeze_path = root / "output/s8b-freeze/holdout_freeze.json"
    freeze_path.write_bytes(freeze_path.read_bytes() + b"\n")
    _fixture_git(root, "add", str(freeze_path.relative_to(root)))
    _fixture_git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "tamper freeze",
    )
    head = _fixture_git(root, "rev-parse", "HEAD")
    output = io.StringIO()
    error = io.StringIO()
    runner = _SealRunner()
    assert main(
        ["seal", "--provider", "claude-headless", "--pre-oracle-head", head],
        root=root, provider_runner=runner, claude_executable=_executable(tmp_path),
        stdout=output, stderr=error,
    ) == 1
    assert "不一致" in error.getvalue()
    assert runner.calls == []
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    assert not journal_path.exists()


def test_seal_rejects_protocol_blob_not_equal_to_rederived_bytes(tmp_path) -> None:
    root, head = _seal_repo(tmp_path, protocol_mismatch=True)
    output = io.StringIO()
    error = io.StringIO()
    runner = _SealRunner()
    assert main(
        ["seal", "--provider", "claude-headless", "--pre-oracle-head", head],
        root=root, provider_runner=runner, claude_executable=tmp_path / "absent-claude",
        stdout=output, stderr=error,
    ) == 1
    assert "canonical 再導出と不一致" in error.getvalue()
    assert runner.calls == []
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    assert not journal_path.exists()


def test_seal_success_runs_four_agents_two_static_and_reloads_destination(tmp_path) -> None:
    root, head = _seal_repo(tmp_path)
    executable = _executable(tmp_path)
    runner = _SealRunner()
    output = io.StringIO()
    error = io.StringIO()
    assert main(
        ["seal", "--provider", "claude-headless", "--pre-oracle-head", head],
        root=root, provider_runner=runner, claude_executable=executable,
        stdout=output, stderr=error,
    ) == 0, error.getvalue()
    assert len(runner.calls) == 4
    destination = root / "output/s8b-freeze/selector_predictions.json"
    reloaded = json.loads(destination.read_text(encoding="utf-8"))
    assert len(reloaded["rows"]) == 6
    assert sum(row["decision_method"] == "selector_agent" for row in reloaded["rows"]) == 4
    assert sum(row["decision_method"] == "static_default" for row in reloaded["rows"]) == 2
    freeze = json.loads((root / "output/s8b-freeze/holdout_freeze.json").read_text())
    verify_prediction_freeze(reloaded, freeze=freeze, root=root)
    success = json.loads(output.getvalue())
    assert success == {
        "status": "sealed",
        "path": "output/s8b-freeze/selector_predictions.json",
        "body_sha256": reloaded["body_sha256"],
    }
    records = PredictionJournal(
        root / "output/s8b-freeze/selector-runs/journal.jsonl",
    ).read_records()
    assert records[0]["record_type"] == "run_header"
    assert sum(record["record_type"] == "invocation" for record in records) == 4
    assert sum(record["record_type"] == "static_terminal" for record in records) == 2
