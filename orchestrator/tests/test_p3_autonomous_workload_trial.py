# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import p3_autonomous_workload_trial as A
from orchestrator.campaign.claude_projected_provider import ClaudeProjectedRoleProvider
from orchestrator.campaign.s8b_prediction_runner import PredictionRunnerError
from calibrator import runner as calibrator_runner


def _fake_drive(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(),
):
    assert do_build is False
    assert cfg.search_config["descriptor_sha256"]
    assert perf.workload == cfg.search_config["ycsb"]
    assert auditor.diff_digest == hashlib.sha256(b"fixture diff").hexdigest()
    Path(layout.root).mkdir(parents=True, exist_ok=True)
    (Path(layout.root) / A.trigger.DIGEST_BASENAME).write_text(
        "fixture digest without performance", encoding="utf-8",
    )
    return {
        "outcome": "dry-pass",
        "variant": None,
        "stop_reason": "continue",
        "iteration": 1,
        "ran": True,
    }


def _fake_preview(coder, *, sub):
    return {
        "passed": True,
        "working_diff": "fixture diff",
        "diff_digest": hashlib.sha256(b"fixture diff").hexdigest(),
        "subtype": None,
        "reason": "",
        "forbidden_identifiers": [],
    }


class _RecordingFixture(A.FixtureRoleProvider):
    def __init__(self, role):
        super().__init__(role)
        self.payloads = []

    def invoke(self, *, invocation_id, payload):
        self.payloads.append(dict(payload))
        return super().invoke(invocation_id=invocation_id, payload=payload)


def test_fixture_trial_runs_ycsb_abc_and_binds_descriptor(tmp_path) -> None:
    run_root = tmp_path / "run"
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="fixture-abc",
        workloads=["ycsb-a", "ycsb-b", "ycsb-c"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
    )
    assert report["status"] == "complete"
    assert report["stop_policy"]["performance_early_stop"] is False
    assert report["claim_scope"]["scientific_claim"] is False
    ratios = [
        cell["descriptor"]["read_write"]["read_ratio_percent"]
        for cell in report["cells"]
    ]
    assert ratios == [50, 95, 100]
    for cell in report["cells"]:
        generation = cell["generations"][0]
        assert generation["outcome"] == "dry-pass"
        assert set(generation["roles"]) == {"planner", "coder", "auditor", "critic"}
        descriptor_sha = cell["descriptor_binding"]["output_sha256"]
        for event in generation["roles"].values():
            assert event["status"] == "valid"
            assert event["descriptor_sha256"] == descriptor_sha
            assert len(event["input_payload_sha256"]) == 64
            assert event["attempt"] == 1
            assert event["retry"] is False
    on_disk = json.loads((run_root / "report.json").read_text(encoding="utf-8"))
    assert on_disk == report
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert sum(event["event"] == "role-attempt" for event in events) == 12
    assert events[-1]["event"] == "run-finish"
    assert report["attempt_journal_sha256"] == hashlib.sha256(
        (run_root / "attempts.jsonl").read_bytes()
    ).hexdigest()
    for payload in providers["coder"].payloads:
        assert set(payload["planner_direction"]) == {"axis", "direction", "magnitude"}
        assert "justification" not in payload["planner_direction"]


class _InvalidPlanner:
    def invoke(self, *, invocation_id, payload):
        return A.ProviderResponse(
            raw_response='{"proposal":{},"extra":true}',
            provenance={"child_id": invocation_id},
        )


def test_invalid_role_is_single_attempt_and_stops_cell(tmp_path) -> None:
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["planner"] = _InvalidPlanner()
    report = A.run_trial(
        trial_id="invalid-planner",
        workloads=["ycsb-a"],
        generations=3,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
    )
    assert report["status"] == "partial"
    cell = report["cells"][0]
    assert cell["stop_reason"] == "role-invalid"
    assert len(cell["generations"]) == 1
    assert cell["generations"][0]["roles"]["planner"]["attempt"] == 1
    assert cell["generations"][0]["roles"]["planner"]["retry"] is False
    assert cell["generations"][0]["roles"]["planner"]["status"] == "invalid"


def test_supervisor_error_still_writes_partial_terminal_report(tmp_path) -> None:
    def broken_preview(coder, *, sub):
        raise RuntimeError("preview fixture failure")

    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="supervisor-error",
        workloads=["ycsb-a", "ycsb-b"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=broken_preview,
    )
    assert report["status"] == "partial"
    assert report["fatal_error"] == {
        "type": "RuntimeError",
        "message": "preview fixture failure",
    }
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    assert (run_root / "report.json").is_file()
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in events][-2:] == [
        "supervisor-error",
        "run-finish",
    ]


def test_main_rejects_fixture_build_before_build_preparation(
    tmp_path, monkeypatch,
) -> None:
    def unexpected_build_preparation(*args, **kwargs):
        pytest.fail("fixture build rejection reached build preparation")

    monkeypatch.setattr(
        calibrator_runner, "competing_bench_pids", unexpected_build_preparation
    )
    monkeypatch.setattr(A, "checkout", unexpected_build_preparation)
    run_root = tmp_path / "run"
    ccbench_dir = tmp_path / "ccbench"

    with pytest.raises(A.AutonomousTrialError):
        A.main([
            "--trial-id", "fixture-build-rejected",
            "--provider", "fixture",
            "--ccbench-dir", str(ccbench_dir),
            "--run-root", str(run_root),
        ])

    assert not run_root.exists()
    assert not ccbench_dir.exists()


def test_main_accepts_fixture_no_build_at_cli_gate(tmp_path, monkeypatch) -> None:
    def stop_after_cli_gate(*args, **kwargs):
        raise ValueError("stop after CLI gate")

    monkeypatch.setattr(A, "assert_pinned_clean", stop_after_cli_gate)
    with pytest.raises(ValueError):
        A.main([
            "--trial-id", "fixture-no-build-accepted",
            "--provider", "fixture",
            "--no-build",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_main_accepts_claude_headless_build_at_cli_gate(
    tmp_path, monkeypatch,
) -> None:
    def stop_after_cli_gate():
        raise ValueError("stop after CLI gate")

    monkeypatch.setattr(calibrator_runner, "competing_bench_pids", stop_after_cli_gate)
    with pytest.raises(ValueError):
        A.main([
            "--trial-id", "claude-build-accepted",
            "--provider", "claude-headless",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def _role_file(path: Path) -> Path:
    path.write_text(
        """---
name: fixture-auditor
description: "fixture role"
tools: ["Read", "Grep"]
model: opus
effort: high
---

Return the requested JSON.
""",
        encoding="utf-8",
    )
    return path


def _executable(path: Path) -> Path:
    executable = path / "claude"
    executable.write_bytes(b"#!/bin/sh\nexit 99\n")
    executable.chmod(0o755)
    return executable


def _envelope(*, server_calls: int = 0) -> dict:
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "permission_denials": [],
        "result": '{"verdict":"pass"}',
        "session_id": "fresh-session-1",
        "modelUsage": {
            "claude-opus-4-6": {"inputTokens": 10, "outputTokens": 5},
        },
        "usage": {"server_tool_use": {"web_search_requests": server_calls}},
    }


class _Runner:
    def __init__(self, envelope):
        self.envelope = envelope
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(self.envelope, separators=(",", ":")).encode(),
            stderr=b"",
        )


def test_projected_provider_lowers_source_tools_and_binds_effective_prompt(tmp_path) -> None:
    runner = _Runner(_envelope())
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return one JSON object only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=runner,
        environ={"HOME": "/fixture/home", "SECRET": "not-forwarded"},
    )
    response = provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})
    inline = json.loads(provider.inline_agents_json)[provider.inline_agent_name]
    assert inline["tools"] == []
    assert provider.source_declared_tools == ["Read", "Grep"]
    assert "Return one JSON object only." in inline["prompt"]
    assert response.provenance["source_declared_tools"] == ["Read", "Grep"]
    assert response.provenance["declared_tools"] == []
    assert response.provenance["capability_lowering"] == "projection-only-tools-empty"
    assert response.provenance["effective_prompt_sha256"] == provider.effective_prompt_sha256
    assert set(runner.calls[0][1]["env"]) == {"HOME"}
    assert runner.calls[0][1]["cwd"] != str(Path(__file__).resolve().parents[2])


def test_projected_provider_rejects_server_tool_use(tmp_path) -> None:
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=_Runner(_envelope(server_calls=1)),
        environ={"HOME": "/fixture/home"},
    )
    with pytest.raises(PredictionRunnerError, match="server tool use"):
        provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
