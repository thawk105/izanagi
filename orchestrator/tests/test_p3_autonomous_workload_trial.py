# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import gc
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import time
import weakref
from pathlib import Path
from types import SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import claude_transport
from orchestrator.campaign import p3_autonomous_workload_trial as A
from orchestrator.campaign import s8b_prediction_runner as S
from orchestrator.campaign.claude_projected_provider import ClaudeProjectedRoleProvider
from orchestrator.campaign.s8b_prediction_runner import PredictionRunnerError
from calibrator import runner as calibrator_runner
from orchestrator.campaign import claude_projected_provider as P


class _CliGateReached(Exception):
    """Sentinel proving that an accepted CLI path reached its next operation."""


def _fake_drive(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(), dependency_prefix="",
):
    assert do_build is False
    assert dependency_prefix == ""
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


def _fake_drive_with_finite_metrics(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(),
):
    outcome = _fake_drive(
        cfg,
        perf,
        planner,
        coder,
        auditor,
        prior,
        sub,
        do_build,
        layout=layout,
        cache_root=cache_root,
        proposal_path=proposal_path,
        extra_sources=extra_sources,
    )
    outcome.update({
        "outcome": "certified",
        "variant": "fixture-finite-metrics",
        "fitness_tps": 12345.0,
        "records": {
            "bench_done": {
                "leading_indicators": {
                    "abort_rate": 0.079,
                    "llc_miss_rate": 0.124,
                    "latency_ns": 456.0,
                    "ipc": 2.5,
                }
            }
        },
    })
    return outcome


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


def _actual_campaign_layout(
    run_root: Path, *, trial_id: str,
) -> A.CampaignLayout:
    flags = A.WORKLOADS["ycsb-a"]
    descriptor, descriptor_record = A._descriptor_for(flags)
    cfg = A._campaign_for(
        workload="ycsb-a",
        workload_flags=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=1,
    )
    return A.CampaignLayout(
        str(run_root / "campaigns" / str(A.trigger.ident.campaign_id(cfg)))
    )


def test_generation_budget_boundary_at_ratified_launch() -> None:
    A._validate_generation_budget(1)
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A._validate_generation_budget(2)


def test_generation_budget_rejects_bool() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(True)


def test_generation_budget_rejects_int_subclass_with_overridden_add() -> None:
    class _ExpandingBudget(int):
        def __add__(self, other: object) -> int:
            return 4

    generations = _ExpandingBudget(1)
    assert int(generations) == 1
    assert list(range(1, generations + 1)) == [1, 2, 3]
    with pytest.raises(A.AutonomousTrialError, match="1..10 必須"):
        A._validate_generation_budget(generations)


def test_generation_budget_rejects_below_minimum() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(0)


def test_generation_budget_rejects_non_int_float() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(1.0)


def test_metric_projection_uses_ratio_keys_and_units() -> None:
    metrics = A._metric_projection({
        "fitness_tps": 12345,
        "records": {
            "bench_done": {
                "leading_indicators": {
                    "abort_rate": 0.079,
                    "latency_ns": 456.0,
                    "llc_miss_rate": 0.124,
                    "ipc": 2.5,
                }
            }
        },
    })

    assert set(metrics) == {
        "throughput_ops_sec",
        "abort_rate",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert metrics == {
        "throughput_ops_sec": 12345.0,
        "abort_rate": 0.079,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    assert type(metrics["throughput_ops_sec"]) is float


def test_metric_projection_rejects_only_invalid_numbers() -> None:
    def project(value):
        return A._metric_projection({
            "fitness_tps": value,
            "records": {
                "bench_done": {
                    "leading_indicators": {
                        "abort_rate": value,
                        "latency_ns": value,
                        "llc_miss_rate": value,
                        "ipc": value,
                    }
                }
            },
        })

    invalid = [
        None,
        True,
        False,
        float("nan"),
        float("inf"),
        -float("inf"),
        10**400,
    ]
    for value in invalid:
        assert all(metric is None for metric in project(value).values())
    assert all(metric is None for metric in project("0.5").values())
    for value in (0.0, -0.001, 1.5):
        assert set(project(value).values()) == {value}


def test_finite_metric_or_none_accepts_finite_boundaries() -> None:
    assert A._finite_metric_or_none(1.0) == 1.0
    assert A._finite_metric_or_none(sys.float_info.max) == sys.float_info.max


def test_role_metric_payloads_convert_only_percent_fields() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_ops_sec": 12345.0,
            "abort_rate": 0.079,
            "latency_ns": 456.0,
            "llc_miss_rate": 0.124,
            "ipc": 2.5,
        },
        contention_level="high",
    )

    assert set(perf_payload) == {
        "throughput_ops_sec",
        "abort_rate_pct",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert set(leading_payload) == {
        "contention_level",
        "cache_miss_rate_pct",
        "IPC_overall",
    }
    assert perf_payload["abort_rate_pct"] == 7.9
    assert leading_payload["cache_miss_rate_pct"] == 12.4
    assert perf_payload["llc_miss_rate"] == 0.124
    assert perf_payload["throughput_ops_sec"] == 12345.0
    assert perf_payload["latency_ns"] == 456.0
    assert perf_payload["ipc"] == 2.5
    assert leading_payload["IPC_overall"] == 2.5


def test_role_metric_payloads_preserve_out_of_range_ratios() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_ops_sec": 12345.0,
            "abort_rate": 1.5,
            "latency_ns": 456.0,
            "llc_miss_rate": -0.001,
            "ipc": 2.5,
        },
        contention_level="high",
    )

    assert perf_payload["abort_rate_pct"] == 150.0
    assert perf_payload["abort_rate_pct"] is not None
    assert leading_payload["cache_miss_rate_pct"] == -0.1
    assert leading_payload["cache_miss_rate_pct"] is not None


def test_role_metric_payloads_reject_percent_overflow() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_ops_sec": sys.float_info.max,
            "abort_rate": sys.float_info.max,
            "latency_ns": sys.float_info.max,
            "llc_miss_rate": sys.float_info.max,
            "ipc": sys.float_info.max,
        },
        contention_level="high",
    )

    assert perf_payload["abort_rate_pct"] is None
    assert leading_payload["cache_miss_rate_pct"] is None
    assert perf_payload["llc_miss_rate"] == sys.float_info.max


def test_role_metric_payloads_preserve_unobserved_none() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_ops_sec": None,
            "abort_rate": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "ipc": None,
        },
        contention_level="medium",
    )

    assert all(value is None for value in perf_payload.values())
    assert leading_payload == {
        "contention_level": "medium",
        "cache_miss_rate_pct": None,
        "IPC_overall": None,
    }


def test_cli_default_is_literal_one_by_ast() -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(
            isinstance(argument, ast.Constant)
            and argument.value == "--max-generations"
            for argument in node.args
        )
    ]
    assert len(calls) == 1
    defaults = [
        keyword.value
        for keyword in calls[0].keywords
        if keyword.arg == "default"
    ]
    assert len(defaults) == 1
    default = defaults[0]
    assert isinstance(default, ast.Constant)
    assert type(default.value) is int
    assert default.value == 1


class _ClosableRecordingFixture(_RecordingFixture):
    def __init__(self, role, close_order=None):
        super().__init__(role)
        self.close_calls = 0
        self.close_order = close_order

    def close(self):
        self.close_calls += 1
        if self.close_order is not None:
            self.close_order.append(self.role)


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
    assert report["schema_version"] == "p3-autonomous-workload-trial-report/v2"
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
        assert "metrics" not in generation
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
    assert (run_root / "namespace.json").read_bytes() == (
        b'{"namespace":"exploration"}\n'
    )
    for payload in providers["coder"].payloads:
        assert set(payload["planner_direction"]) == {"axis", "direction", "magnitude"}
        assert "justification" not in payload["planner_direction"]
    for planner_payload, coder_payload, critic_payload in zip(
        providers["planner"].payloads,
        providers["coder"].payloads,
        providers["critic"].payloads,
        strict=True,
    ):
        assert planner_payload["schema_version"] == "p3-autonomous-workload-trial/v2"
        assert coder_payload["schema_version"] == "p3-autonomous-workload-trial/v2"
        assert critic_payload["schema_version"] == "p3-autonomous-workload-trial/v2"

        current_perf = planner_payload["current_perf"]
        leading_indicators = planner_payload["leading_indicators"]
        baseline = coder_payload["baseline"]
        critic_metrics = critic_payload["harness_result"]["metrics"]
        assert set(current_perf) == {
            "throughput_ops_sec",
            "abort_rate_pct",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert set(leading_indicators) == {
            "contention_level",
            "cache_miss_rate_pct",
            "IPC_overall",
        }
        assert set(baseline) == {
            "throughput_ops_sec",
            "abort_rate_pct",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert set(critic_metrics) == {
            "throughput_ops_sec",
            "abort_rate",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert "abort_rate_pct" not in critic_metrics
        assert "cache_miss_rate_pct" not in critic_metrics
        assert all(value is None for value in current_perf.values())
        assert all(
            leading_indicators[key] is None
            for key in ("cache_miss_rate_pct", "IPC_overall")
        )
        assert all(value is None for value in baseline.values())
        assert all(value is None for value in critic_metrics.values())


def test_generation_one_recipient_wiring_uses_role_projection(
    tmp_path, monkeypatch,
) -> None:
    expected_perf = {
        "throughput_ops_sec": 12345.0,
        "abort_rate_pct": 7.9,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    expected_leading = {
        "contention_level": "fixture-contention",
        "cache_miss_rate_pct": 12.4,
        "IPC_overall": 2.5,
    }
    calls = []

    def role_projection(current_metrics, *, contention_level):
        calls.append((dict(current_metrics), contention_level))
        return dict(expected_perf), dict(expected_leading)

    monkeypatch.setattr(A, "_role_metric_payloads", role_projection)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="generation-one-recipient-wiring",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
    )

    assert report["status"] == "complete"
    assert len(calls) == 1
    assert set(calls[0][0]) == {
        "throughput_ops_sec",
        "abort_rate",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert providers["planner"].payloads[0]["current_perf"] == expected_perf
    assert providers["planner"].payloads[0]["leading_indicators"] == expected_leading
    assert providers["coder"].payloads[0]["baseline"] == expected_perf


def test_generation_one_finite_metrics_preserve_recipient_units_and_report_schema(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="generation-one-finite-metrics",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
    )

    assert report["status"] == "complete"
    cell = report["cells"][0]
    generation_record = cell["generations"][0]
    assert generation_record["outcome"] == "certified"

    planner_payload = providers["planner"].payloads[0]
    coder_payload = providers["coder"].payloads[0]
    critic_payload = providers["critic"].payloads[0]
    common_keys = {
        "schema_version",
        "pilot_scope",
        "scientific_claim",
        "workload",
        "generation",
        "workload_descriptor",
        "descriptor_binding",
        "attempt_policy",
        "stop_policy",
    }
    assert set(planner_payload) == common_keys | {
        "current_perf",
        "leading_indicators",
        "whiteboard",
    }
    assert set(coder_payload) == common_keys | {
        "leakproof_context",
        "gating_spec",
        "planner_direction",
        "baseline",
        "whiteboard",
    }
    assert set(critic_payload) == common_keys | {
        "harness_result",
        "critic_digest",
    }

    critic_metrics = critic_payload["harness_result"]["metrics"]
    assert critic_metrics == {
        "throughput_ops_sec": 12345.0,
        "abort_rate": 0.079,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }

    planner_indicators = planner_payload["leading_indicators"]
    assert (
        planner_indicators["contention_level"]
        == cell["descriptor"]["contention"]["label"]
    )
    assert "metrics" not in generation_record


class _InvalidPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, *, invocation_id, payload):
        self.calls += 1
        return A.ProviderResponse(
            raw_response='{"proposal":{},"extra":true}',
            provenance={"child_id": invocation_id},
        )


def test_invalid_role_is_single_attempt_and_stops_cell(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 3)
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    planner = _InvalidPlanner()
    providers["planner"] = planner
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
    assert planner.calls == 1


def test_run_trial_rejects_unapproved_budget_before_artifact_creation(tmp_path) -> None:
    run_root = tmp_path / "run"
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A.run_trial(
            trial_id="unapproved-programmatic-budget",
            workloads=["ycsb-a"],
            generations=2,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
        )
    assert not run_root.exists()


def test_run_trial_rejects_compute_build_before_artifact_or_provider(
    tmp_path, monkeypatch,
) -> None:
    run_root = tmp_path / "run"
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A.run_trial(
            trial_id="compute-build-still-closed",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=True,
        )
    assert not run_root.exists()


def test_8c_internal_entrypoints_have_no_site_injection_surface() -> None:
    assert "site" not in inspect.signature(A._run_workload).parameters
    assert "site" not in inspect.signature(A._finish_trial).parameters


def test_run_workload_direct_compute_build_rejects_before_provider(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )

    class _Poison:
        def __getattr__(self, name):
            pytest.fail(f"compute rejection reached provider/journal: {name}")

    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A._run_workload(
            workload="ycsb-a", generations=1,
            providers={role: _Poison() for role in A.ROLE_FILES},
            journal=_Poison(), run_root=tmp_path / "run", sub="/unused",
            do_build=True, cache_root="", trial_id="compute-direct-rejected",
            started_monotonic=time.monotonic(), max_wall_s=60,
        )
    assert not (tmp_path / "run").exists()


def test_finish_trial_direct_compute_build_rejects_before_provider(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A._finish_trial(
            trial_id="compute-finish-rejected", selected=["ycsb-a"], generations=1,
            provider_kind="claude-headless", run_root=tmp_path / "run",
            sub="/unused", do_build=True, cache_root="", max_wall_s=60,
            drive=lambda *_a, **_k: pytest.fail("drive reached"),
            preview=lambda *_a, **_k: pytest.fail("preview reached"),
            journal=SimpleNamespace(), started="fixture",
            started_monotonic=time.monotonic(), active_providers={},
            fatal_error=None,
            transport_receipt=None,
        )
    assert not (tmp_path / "run").exists()


def test_compute_build_requires_matching_t276_transport_admission(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    source_env = {
        "PBS_JOBID": "12345.pegasus",
        "http_proxy": "http://proxy.example:18080",
        "https_proxy": "http://proxy.example:18443",
    }
    policy_bytes = json.dumps({
        "schema_version": "pegasus-claude-transport-policy/v1",
        "site": "PEGASUS_COMPUTE",
        "mode": "explicit-http-proxy-env",
        "endpoint_values": {
            "http_proxy": source_env["http_proxy"],
            "https_proxy": source_env["https_proxy"],
        },
    }).encode("utf-8")
    admission = claude_transport.evaluate_transport_admission(
        source_env=source_env,
        policy_bytes=policy_bytes,
        site=A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    receipt = admission.receipt.as_dict()

    A._assert_build_site_opted_in(
        True, allow_pegasus_compute_transport=True,
    )
    A._assert_build_transport_admitted(
        True,
        transport_admission=admission,
        transport_receipt=receipt,
    )

    with pytest.raises(A.AutonomousTrialError, match="transport admission"):
        A._assert_build_transport_admitted(
            True,
            transport_admission=None,
            transport_receipt=None,
        )
    mismatched = dict(receipt)
    mismatched["pbs_jobid"] = "67890.pegasus"
    with pytest.raises(A.AutonomousTrialError, match="run-level snapshot"):
        A._assert_build_transport_admitted(
            True,
            transport_admission=admission,
            transport_receipt=mismatched,
        )


def test_run_workload_other_build_reaches_drive_positive(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    run_root = tmp_path / "run"
    for child in (run_root, run_root / "raw", run_root / "proposals"):
        child.mkdir(exist_ok=True)
    campaign = A.CampaignLayout(str(tmp_path / "campaign"))
    monkeypatch.setattr(
        A, "exploration_campaign_layout", lambda _campaign_id: campaign,
    )
    calls = []

    def drive(*args, layout, **kwargs):
        calls.append((args, kwargs))
        assert args[7] is True
        assert "site" not in kwargs
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        (Path(layout.root) / A.trigger.DIGEST_BASENAME).write_text(
            "fixture digest", encoding="utf-8",
        )
        return {
            "outcome": "certified", "variant": "fixture-variant",
            "fitness_tps": 1.0, "stop_reason": "continue",
            "iteration": 1, "ran": True,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = A._run_workload(
        workload="ycsb-a", generations=1, providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"), run_root=run_root,
        sub="/unused", do_build=True, cache_root="",
        trial_id="other-build-positive", started_monotonic=time.monotonic(),
        max_wall_s=60, drive=drive, preview=_fake_preview,
    )
    assert len(calls) == 1
    assert result["generations"][0]["outcome"] == "certified"


def test_run_workload_direct_call_rejects_unapproved_budget(tmp_path) -> None:
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A._run_workload(
            workload="ycsb-a",
            generations=2,
            providers={},
            journal=SimpleNamespace(),
            run_root=tmp_path / "run",
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="unapproved-direct-budget",
            started_monotonic=0.0,
            max_wall_s=1,
        )


def test_run_workload_rejects_existing_campaign_state(tmp_path, monkeypatch) -> None:
    """Monkeypatched loader poisons any provider call, fixing gate ordering."""

    class _ProviderMustNotRun:
        def invoke(self, *, invocation_id, payload):
            pytest.fail(f"freshness rejection reached provider: {invocation_id}")

    monkeypatch.setattr(
        A.loop_core, "load_loop_state", lambda layout: A.loop_core.LoopState()
    )
    providers = {
        role: _ProviderMustNotRun()
        for role in ("planner", "coder", "auditor", "critic")
    }
    with pytest.raises(A.AutonomousTrialError, match="既存 campaign state"):
        A._run_workload(
            workload="ycsb-a",
            generations=1,
            providers=providers,
            journal=SimpleNamespace(),
            run_root=tmp_path / "run",
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="existing-state-rejected",
            started_monotonic=time.monotonic(),
            max_wall_s=60,
        )


def test_run_workload_accepts_fresh_campaign_state(tmp_path, monkeypatch) -> None:
    """Monkeypatched loader fixes the fresh branch before provider invocation."""

    monkeypatch.setattr(A.loop_core, "load_loop_state", lambda layout: None)
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = A._run_workload(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="fresh-state-accepted",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
    )
    assert [generation["outcome"] for generation in result["generations"]] == [
        "dry-pass"
    ]
    assert all(len(provider.payloads) == 1 for provider in providers.values())


def test_run_workload_rejects_actual_existing_campaign_state(tmp_path) -> None:
    class _ProviderMustNotRun:
        def invoke(self, *, invocation_id, payload):
            pytest.fail(f"actual freshness rejection reached provider: {invocation_id}")

    run_root = tmp_path / "run"
    trial_id = "actual-existing-state-rejected"
    layout = _actual_campaign_layout(run_root, trial_id=trial_id)
    A.loop_core.save_loop_state(layout, A.loop_core.LoopState())
    providers = {
        role: _ProviderMustNotRun()
        for role in ("planner", "coder", "auditor", "critic")
    }
    with pytest.raises(A.AutonomousTrialError, match="既存 campaign state"):
        A._run_workload(
            workload="ycsb-a",
            generations=1,
            providers=providers,
            journal=SimpleNamespace(),
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id=trial_id,
            started_monotonic=time.monotonic(),
            max_wall_s=60,
        )


def test_run_workload_accepts_actual_fresh_campaign_layout(tmp_path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    layout = _actual_campaign_layout(
        run_root, trial_id="actual-fresh-state-accepted"
    )
    assert not Path(layout.root).exists()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = A._run_workload(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="actual-fresh-state-accepted",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
    )
    assert [generation["outcome"] for generation in result["generations"]] == [
        "dry-pass"
    ]
    assert all(len(provider.payloads) == 1 for provider in providers.values())


def test_run_workload_build_passes_exploration_layout_to_trigger(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    passed_layouts = []

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(),
    ):
        assert do_build is True
        passed_layouts.append(layout)
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
        }

    result = A._run_workload(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=True,
        cache_root="/unused-cache",
        trial_id="build-exploration-layout",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=drive_build,
        preview=_fake_preview,
    )

    expected = tmp_path / "exploration" / "campaigns" / result["campaign_id"]
    assert Path(result["campaign_root"]) == expected
    assert [Path(layout.root) for layout in passed_layouts] == [expected]


def test_run_trial_build_public_entry_passes_exploration_layout_to_trigger(
    tmp_path, monkeypatch,
) -> None:
    """F5/M08: public run_trial から実際に trigger sink へ渡る root を見る。"""
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    passed_layouts = []

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(),
    ):
        assert do_build is True
        passed_layouts.append(layout)
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

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="public-build-exploration-layout",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
    )
    expected = (
        tmp_path / "exploration" / "campaigns" / report["cells"][0]["campaign_id"]
    )
    assert [Path(layout.root) for layout in passed_layouts] == [expected]
    assert Path(report["cells"][0]["campaign_root"]) == expected
    assert not (tmp_path / "campaigns" / report["cells"][0]["campaign_id"]).exists()


def test_run_workload_no_build_stays_trial_local(tmp_path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = A._run_workload(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="no-build-trial-local",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
    )

    assert Path(result["campaign_root"]) == (
        run_root / "campaigns" / result["campaign_id"]
    )


def test_freshness_wraps_malformed_json_with_cause(tmp_path) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))
    layout.ensure()
    Path(A.loop_core.loop_state_path(layout)).write_text(
        "{broken", encoding="utf-8"
    )
    with pytest.raises(A.AutonomousTrialError) as caught:
        A._assert_fresh_campaign_state(layout)
    assert type(caught.value.__cause__) is json.JSONDecodeError


def test_freshness_wraps_delta_pct_leak_with_cause(tmp_path) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))
    state = A.loop_core.LoopState(
        whiteboard=[
            A.loop_core.WhiteboardEntry(
                iteration=1,
                direction="increase",
                magnitude="small",
                result="fail",
                delta_pct=1.0,
            )
        ]
    )
    A.loop_core.save_loop_state(layout, state)
    with pytest.raises(A.AutonomousTrialError) as caught:
        A._assert_fresh_campaign_state(layout)
    assert type(caught.value.__cause__) is A.loop_core.WhiteboardLeakError


def test_freshness_does_not_reclassify_attribute_error(
    tmp_path, monkeypatch,
) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))

    def broken_loader(_layout):
        raise AttributeError("loader programming error")

    monkeypatch.setattr(A.loop_core, "load_loop_state", broken_loader)
    with pytest.raises(AttributeError, match="loader programming error"):
        A._assert_fresh_campaign_state(layout)


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


@pytest.mark.parametrize("outcome", ["success", "supervisor-error"])
def test_run_trial_closes_owned_providers_in_reverse_order(
    tmp_path, monkeypatch, outcome,
) -> None:
    close_order: list[str] = []
    owned = {
        role: _ClosableRecordingFixture(role, close_order)
        for role in ("planner", "coder", "auditor", "critic")
    }
    monkeypatch.setattr(A, "_provider_set", lambda **kwargs: owned)

    def preview(coder, *, sub):
        if outcome == "supervisor-error":
            raise RuntimeError("preview failure")
        return _fake_preview(coder, sub=sub)

    report = A.run_trial(
        trial_id=f"owned-{outcome}",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=preview,
    )
    assert report["status"] == ("complete" if outcome == "success" else "partial")
    assert close_order == ["critic", "auditor", "coder", "planner"]
    assert all(provider.close_calls == 1 for provider in owned.values())


def test_run_trial_does_not_close_injected_providers(tmp_path) -> None:
    providers = {
        role: _ClosableRecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="injected-ownership",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
    )
    assert report["status"] == "complete"
    assert all(provider.close_calls == 0 for provider in providers.values())
    assert providers["coder"].payloads[0]["workload"] == "ycsb-a"


def test_provider_set_closes_partial_projected_provider_set_in_reverse_order(
    tmp_path, monkeypatch,
) -> None:
    close_order: list[str] = []
    constructed: list[str] = []

    class _PartialProvider:
        def __init__(self, role):
            self.role = role

        def close(self):
            close_order.append(self.role)

    def provider_factory(**kwargs):
        role = tuple(A.ROLE_FILES)[len(constructed)]
        constructed.append(role)
        if role == "auditor":
            raise RuntimeError("partial construction failure")
        return _PartialProvider(role)

    monkeypatch.setattr(A, "ClaudeProjectedRoleProvider", provider_factory)
    with pytest.raises(RuntimeError, match="partial construction failure"):
        A._provider_set(
            kind="claude-headless",
            run_root=tmp_path / "run",
            executable="unused",
        )
    assert constructed == ["planner", "coder", "auditor"]
    assert close_order == ["coder", "planner"]


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


def test_main_rejects_unapproved_budget_before_build_preparation(
    tmp_path, monkeypatch,
) -> None:
    def unexpected_build_preparation(*args, **kwargs):
        pytest.fail("budget rejection reached build preparation")

    monkeypatch.setattr(A, "assert_pinned_clean", unexpected_build_preparation)
    monkeypatch.setattr(A, "checkout", unexpected_build_preparation)
    monkeypatch.setattr(
        calibrator_runner, "competing_bench_pids", unexpected_build_preparation
    )
    run_root = tmp_path / "run"
    ccbench_dir = tmp_path / "ccbench"
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A.main([
            "--trial-id", "unapproved-cli-budget",
            "--provider", "claude-headless",
            "--max-generations", "2",
            "--ccbench-dir", str(ccbench_dir),
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()
    assert not ccbench_dir.exists()


def test_main_default_generation_budget_is_one(tmp_path, monkeypatch) -> None:
    def stop_after_cli_gate(*args, **kwargs):
        raise _CliGateReached

    monkeypatch.setattr(A, "assert_pinned_clean", stop_after_cli_gate)
    with pytest.raises(_CliGateReached):
        A.main([
            "--trial-id", "fixture-no-build-accepted",
            "--provider", "fixture",
            "--no-build",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_main_rejects_claude_headless_build_outside_other_before_preparation(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )

    def unexpected_preparation():
        pytest.fail("8c compute rejection reached measurement preparation")

    monkeypatch.setattr(calibrator_runner, "competing_bench_pids", unexpected_preparation)
    run_root = tmp_path / "run"
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A.main([
            "--trial-id", "claude-build-accepted",
            "--provider", "claude-headless",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()


def test_main_accepts_claude_headless_no_build_at_cli_gate(
    tmp_path, monkeypatch,
) -> None:
    def stop_after_cli_gate(*args, **kwargs):
        raise _CliGateReached

    monkeypatch.setattr(A, "assert_pinned_clean", stop_after_cli_gate)
    with pytest.raises(_CliGateReached):
        A.main([
            "--trial-id", "claude-no-build-accepted",
            "--provider", "claude-headless",
            "--no-build",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_main_default_run_root_is_exploration_autonomous_trials(
    tmp_path, monkeypatch,
) -> None:
    captured = {}
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *args, **kwargs: None)

    def capture_run_trial(**kwargs):
        captured.update(kwargs)
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    assert A.main([
        "--trial-id", "default-exploration-root",
        "--provider", "fixture",
        "--no-build",
        "--ccbench-dir", str(tmp_path / "ccbench"),
    ]) == 0
    assert captured["run_root"] == (
        A.ROOT
        / "output"
        / "exploration"
        / "autonomous-trials"
        / "default-exploration-root"
    )


def test_main_explicit_run_root_still_wins(tmp_path, monkeypatch) -> None:
    captured = {}
    explicit = tmp_path / "explicit-run-root"
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *args, **kwargs: None)

    def capture_run_trial(**kwargs):
        captured.update(kwargs)
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    assert A.main([
        "--trial-id", "explicit-root",
        "--provider", "fixture",
        "--no-build",
        "--ccbench-dir", str(tmp_path / "ccbench"),
        "--run-root", str(explicit),
    ]) == 0
    assert captured["run_root"] == explicit


def test_main_help_names_exploration_autonomous_trials(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        A.main(["--help"])
    assert caught.value.code == 0
    help_text = capsys.readouterr().out
    assert "output/exploration/autonomous-trials/<trial-id>" in help_text
    assert "output/autonomous-trials/<trial-id>" not in help_text


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


def _projected_provider_call(tmp_path: Path) -> ClaudeProjectedRoleProvider:
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return one JSON object only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=_Runner(_envelope()),
        environ={"HOME": "/fixture/home"},
    )
    provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})
    return provider


def _assert_projected_cleanup_guard(
    *,
    neutral_root: Path,
    neutral_cwd: Path,
    cleanup_target: Path,
    artifact_root: Path,
    artifact_bytes: dict[Path, bytes],
    outside_marker: Path,
) -> None:
    """Projected provider の cleanup 静止境界を検査する。

    周辺 test を含む gate は明示 close の正常/異常、cleanup error 後の再試行、
    参照破棄後の fallback、静止した削除境界、owner close まで到達する。未到達
    なのは interpreter shutdown 中の live object、fork child の atexit、並行
    invoke/close、close 後の再 invoke、scope 外 callsite である。
    """
    assert not neutral_root.exists() and not neutral_root.is_symlink(), "root 消滅"
    assert not neutral_cwd.exists() and not neutral_cwd.is_symlink(), "cwd 消滅"
    assert artifact_root.is_dir() and not artifact_root.is_symlink(), "artifact_root 存続"
    artifact_bytes_unchanged = all(
        path.read_bytes() == expected for path, expected in artifact_bytes.items()
    )
    assert artifact_bytes_unchanged, "artifact bytes 不変"
    assert outside_marker.is_file(), "外部 marker 存続"
    resolved_artifact_root = artifact_root.resolve(strict=True)
    resolved_cleanup_target = cleanup_target.resolve(strict=False)
    artifact_inside_cleanup_target = (
        resolved_artifact_root == resolved_cleanup_target
        or resolved_artifact_root.is_relative_to(resolved_cleanup_target)
    )
    assert not artifact_inside_cleanup_target, "非交差"


@pytest.mark.parametrize(
    "predicate",
    ["root", "cwd", "artifact", "bytes", "marker", "nonintersection"],
)
def test_projected_cleanup_guard_rejects_each_predicate_independently(
    tmp_path, predicate,
) -> None:
    """各入力では指定 predicate だけを偽にし、projected guard の歯を固定する。"""
    neutral_root = tmp_path / "neutral-missing"
    neutral_cwd = tmp_path / "cwd-missing"
    cleanup_target = tmp_path / "cleanup-missing"
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    artifact_path = artifact_root / "payload.json"
    artifact_path.write_bytes(b"proof-chain")
    artifact_bytes = {artifact_path: artifact_path.read_bytes()}
    outside_marker = tmp_path / "outside.marker"
    outside_marker.write_bytes(b"outside")

    expected_message = {
        "root": "root 消滅",
        "cwd": "cwd 消滅",
        "artifact": "artifact_root 存続",
        "bytes": "artifact bytes 不変",
        "marker": "外部 marker 存続",
        "nonintersection": "非交差",
    }[predicate]
    if predicate == "root":
        neutral_root.mkdir()
    elif predicate == "cwd":
        neutral_cwd.mkdir()
    elif predicate == "artifact":
        real_artifact_root = tmp_path / "artifact-target"
        artifact_root.rename(real_artifact_root)
        artifact_root.symlink_to(real_artifact_root, target_is_directory=True)
    elif predicate == "bytes":
        artifact_path.write_bytes(b"mutated")
    elif predicate == "marker":
        outside_marker.unlink()
    elif predicate == "nonintersection":
        cleanup_target = artifact_root

    with pytest.raises(AssertionError, match=expected_message):
        _assert_projected_cleanup_guard(
            neutral_root=neutral_root,
            neutral_cwd=neutral_cwd,
            cleanup_target=cleanup_target,
            artifact_root=artifact_root,
            artifact_bytes=artifact_bytes,
            outside_marker=outside_marker,
        )


def _projected_cleanup_inputs(provider, tmp_path: Path) -> dict:
    outside_marker = tmp_path / "outside" / "marker"
    outside_marker.parent.mkdir(exist_ok=True)
    outside_marker.write_bytes(b"outside")
    (provider.neutral_root / "outside-link").symlink_to(outside_marker)
    return {
        "neutral_root": provider.neutral_root,
        "neutral_cwd": provider.neutral_cwd,
        "artifact_root": provider.artifact_root,
        "artifact_bytes": {
            path: path.read_bytes()
            for path in provider.artifact_root.iterdir()
            if path.is_file()
        },
        "outside_marker": outside_marker,
    }


def _rescue_projected_neutral_root(identity: Path) -> None:
    """Mutation failure 後も、記録済みの生 identity だけを best-effort 削除する。"""
    if not identity.is_symlink():
        shutil.rmtree(identity, ignore_errors=True)


def test_projected_provider_close_removes_only_neutral_tree(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        actual_cleanup_targets: list[Path] = []
        original_remove = P._remove_neutral_root

        def recording_remove(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            # M16 の危険 target は記録だけし、fixture の既知 identity を安全に削除する。
            return original_remove(recorded_identity, artifact_root)

        monkeypatch.setattr(P, "_remove_neutral_root", recording_remove)
        provider.close()
        provider.close()
        assert provider.cleanup_error is None
        assert not provider._neutral_root_finalizer.alive
        assert len(actual_cleanup_targets) == 1
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[0], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


def test_projected_provider_finalize_fallback_removes_only_neutral_tree(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        actual_cleanup_targets: list[Path] = []
        original_remove = S._remove_neutral_root
        provider_ref = weakref.ref(provider)

        def recording_remove(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            return original_remove(neutral_root_identity, artifact_root)

        monkeypatch.setattr(S, "_remove_neutral_root", recording_remove)
        del provider
        gc.collect()
        assert provider_ref() is None
        assert len(actual_cleanup_targets) == 1
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[0], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


def test_projected_provider_close_never_raises_and_retries_before_detach(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        original_remove = P._remove_neutral_root
        actual_cleanup_targets: list[Path] = []

        def fail_once(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            if len(actual_cleanup_targets) == 1:
                raise OSError("simulated cleanup failure")
            return original_remove(neutral_root_identity, artifact_root)

        monkeypatch.setattr(P, "_remove_neutral_root", fail_once)
        provider.close()
        assert isinstance(provider.cleanup_error, OSError)
        assert provider._neutral_root_finalizer.alive
        provider.close()
        assert len(actual_cleanup_targets) == 2
        assert not provider._neutral_root_finalizer.alive
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[-1], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


@pytest.mark.parametrize("failure", ["mcp-config", "home-missing", "environment-baseexception"])
def test_projected_provider_init_failure_removes_neutral_root(
    tmp_path, monkeypatch, failure,
) -> None:
    created_identities: list[Path] = []
    fallback_attempts: list[Path] = []
    original_create = P._create_neutral_root

    def recording_create(*args, **kwargs):
        result = original_create(*args, **kwargs)
        created_identities.append(result[1])
        return result

    def recording_fallback(neutral_root_identity, artifact_root):
        fallback_attempts.append(Path(neutral_root_identity))

    monkeypatch.setattr(P, "_create_neutral_root", recording_create)
    monkeypatch.setattr(S, "_finalize_neutral_root", recording_fallback)
    environ: dict[str, str] = {"HOME": "/fixture/home"}
    expected_error: type[BaseException] = PredictionRunnerError
    if failure == "mcp-config":
        def fail_write(*args, **kwargs):
            raise OSError("mcp write failure")

        monkeypatch.setattr(P, "_write_bytes_bound", fail_write)
        expected_error = OSError
    elif failure == "home-missing":
        environ = {}
    else:
        class _ExplodingEnvironment(dict):
            def __contains__(self, key):
                raise KeyboardInterrupt("environment mapping failure")

        environ = _ExplodingEnvironment(HOME="/fixture/home")
        expected_error = KeyboardInterrupt

    try:
        with pytest.raises(expected_error):
            ClaudeProjectedRoleProvider(
                artifact_root=tmp_path / "artifacts",
                role_file=_role_file(tmp_path / "role.md"),
                role_name="fixture-auditor",
                mediated_contract="Return JSON only.",
                repository_root=Path(__file__).resolve().parents[2],
                executable=_executable(tmp_path),
                environ=environ,
            )
        assert len(created_identities) == 1
        assert not created_identities[0].exists()
        assert fallback_attempts == []
    finally:
        for identity in created_identities:
            _rescue_projected_neutral_root(identity)


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
