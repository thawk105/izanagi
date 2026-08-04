# -*- coding: utf-8 -*-
"""T-244 P5-1/P5-2 provider and role-session isolation boundaries."""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import autonomous_trial_completeness as C  # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as A  # noqa: E402
from orchestrator.campaign import role_session_isolation as R  # noqa: E402
from orchestrator.campaign.claude_projected_provider import (  # noqa: E402
    ClaudeProjectedRoleProvider,
)
from orchestrator.campaign.role_session_isolation import (  # noqa: E402
    CrossRoleSessionTracker,
    RoleSessionIsolationError,
    evaluate_role_session_isolation,
)
from orchestrator.campaign.s8b_prediction_runner import (  # noqa: E402
    PredictionRunnerError,
)
from orchestrator.tests import test_autonomous_trial_completeness as F  # noqa: E402


def _role_file(path: Path, name: str) -> Path:
    path.write_text(
        "---\n"
        f"name: {name}\n"
        "description: fixture\n"
        'tools: ["Read"]\n'
        "model: opus\n"
        "effort: high\n"
        "---\n"
        "Return JSON only.\n",
        encoding="utf-8",
    )
    return path


def _executable(path: Path) -> Path:
    path.write_bytes(b"#!/bin/sh\nexit 0\n")
    path.chmod(0o700)
    return path


class _Runner:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def __call__(self, _argv, **_kwargs):
        envelope = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "num_turns": 1,
            "permission_denials": [],
            "result": '{"ok":true}',
            "session_id": self.session_id,
            "modelUsage": {
                "claude-opus-4-6": {"inputTokens": 3, "outputTokens": 2},
            },
            "usage": {"server_tool_use": {"web_search_requests": 0}},
        }
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(envelope, separators=(",", ":")).encode(),
            stderr=b"",
        )


def _provider(
    tmp_path: Path, *, role: str, session_id: str,
    tracker: CrossRoleSessionTracker,
) -> ClaudeProjectedRoleProvider:
    return ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / f"artifacts-{role}",
        role_file=_role_file(tmp_path / f"role-{role}.md", role),
        role_name=role,
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_executable(tmp_path / f"claude-{role}"),
        runner=_Runner(session_id),
        environ={"HOME": "/fixture/home"},
        cross_role_session_tracker=tracker,
    )


def _claude_artifact(tmp_path: Path, child_ids: tuple[object, ...]):
    run, events, report = F._complete_trial(tmp_path)
    report["provider"] = "claude-headless"
    events[0]["provider"] = "claude-headless"
    attempts = [event for event in events if event.get("event") == "role-attempt"]
    assert len(attempts) == len(child_ids)
    for event, child_id in zip(attempts, child_ids, strict=True):
        event["provenance"] = {"child_id": child_id}
    report_roles = report["cells"][0]["generations"][0]["roles"]
    for role, child_id in zip(F._ROLES, child_ids, strict=True):
        report_roles[role]["provenance"] = {"child_id": child_id}
    F._persist(run, events, report)
    return run, report


def test_leaf_docstring_keeps_unimplemented_dependency_without_owner_claim() -> None:
    docstring = inspect.getdoc(R)
    assert docstring is not None
    assert "remains unimplemented as a separate design dependency" in docstring
    assert "owns origin/query-slot issuance" not in docstring


def test_claude_run_rejects_injected_providers_before_artifact(tmp_path) -> None:
    assert "cross_role_session_tracker" not in inspect.signature(A.run_trial).parameters
    run_root = tmp_path / "run"
    with pytest.raises(A.AutonomousTrialError, match="caller 注入"):
        A.run_trial(
            trial_id="injected-provider-rejected",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            providers={},
        )
    assert not run_root.exists()


def _assert_claude_call_rejected_before_side_effects(
    tmp_path: Path,
    *,
    trial_id: str,
    expected_match: str,
    **overrides,
) -> None:
    run_root = tmp_path / trial_id
    reached: list[str] = []
    originals = {
        "AttemptJournal": A.AttemptJournal,
        "ensure_exploration_namespace": A.ensure_exploration_namespace,
        "_provider_set": A._provider_set,
        "_assert_build_site_opted_in": A._assert_build_site_opted_in,
        "admit_claude_transport": A.admit_claude_transport,
    }

    def forbidden(name):
        def call(*args, **kwargs):
            reached.append(name)
            raise AssertionError(f"driver injection rejection reached {name}")

        return call

    arguments = {
        "trial_id": trial_id,
        "workloads": ["ycsb-a"],
        "generations": 1,
        "provider_kind": "claude-headless",
        "run_root": run_root,
        "sub": "/unused",
        "do_build": False,
    }
    arguments.update(overrides)
    try:
        for name in originals:
            setattr(A, name, forbidden(name))
        with pytest.raises(A.AutonomousTrialError, match=expected_match):
            A.run_trial(**arguments)
    finally:
        for name, original in originals.items():
            setattr(A, name, original)
    for name, original in originals.items():
        assert getattr(A, name) is original
    assert reached == []
    assert not run_root.exists()


@pytest.mark.parametrize(
    ("injected_names", "value_kind"),
    [
        pytest.param(("drive",), "current", id="drive-current"),
        pytest.param(("preview",), "current", id="preview-current"),
        pytest.param(("drive", "preview"), "current", id="both-current"),
        pytest.param(("drive",), "fake", id="drive-fake"),
        pytest.param(("preview",), "fake", id="preview-fake"),
        pytest.param(("drive", "preview"), "fake", id="both-fake"),
    ],
)
def test_claude_run_rejects_injected_drive_or_preview_before_artifact(
    tmp_path, injected_names, value_kind,
) -> None:
    def fake_drive(*args, **kwargs):
        raise AssertionError((args, kwargs))

    def fake_preview(*args, **kwargs):
        raise AssertionError((args, kwargs))

    values = (
        {
            "drive": A.trigger.drive_iteration,
            "preview": A._preview,
        }
        if value_kind == "current"
        else {"drive": fake_drive, "preview": fake_preview}
    )
    injected = {name: values[name] for name in injected_names}
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id=f"driver-{value_kind}-{'-'.join(injected_names)}",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        **injected,
    )


def test_claude_run_rejects_non_callable_drive_before_artifact(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="driver-non-callable",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        drive=object(),
    )


def test_claude_run_rejects_non_callable_preview_before_artifact(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="preview-non-callable",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        preview=object(),
    )


@pytest.mark.parametrize("injected_name", ["drive", "preview"])
def test_claude_run_rejects_adversarial_equality_driver_values_before_artifact(
    tmp_path, injected_name,
) -> None:
    class _LooksOmitted:
        def __eq__(self, other):
            del other
            return True

        def __ne__(self, other):
            del other
            return False

    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id=f"{injected_name}-adversarial-equality",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        **{injected_name: _LooksOmitted()},
    )


def test_claude_run_rejects_injected_drive_when_build_enabled(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="driver-build-enabled",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        do_build=True,
        drive=A.trigger.drive_iteration,
    )


def test_provider_injection_rejection_precedes_driver_injection(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="provider-before-driver",
        expected_match=(
            r"^claude-headless provider は caller 注入を許可しない\Z"
        ),
        providers={},
        drive=A.trigger.drive_iteration,
    )


def test_driver_injection_rejection_precedes_generation_budget(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="driver-before-generation-budget",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        generations=2,
        drive=A.trigger.drive_iteration,
    )


def test_driver_injection_rejection_precedes_wall_validation(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="driver-before-wall-validation",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        max_wall_s=0,
        drive=A.trigger.drive_iteration,
    )


def test_driver_injection_rejection_precedes_compute_transport(tmp_path) -> None:
    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="driver-before-compute-transport",
        expected_match=(
            r"^claude-headless drive/preview は caller 注入を許可しない\Z"
        ),
        allow_pegasus_compute_transport=True,
        drive=A.trigger.drive_iteration,
    )


def test_provider_kind_rejects_str_subclass_before_artifact(tmp_path) -> None:
    class _SneakyKind(str):
        pass

    _assert_claude_call_rejected_before_side_effects(
        tmp_path,
        trial_id="provider-kind-str-subclass",
        expected_match=r"^provider kind は plain str 必須: _SneakyKind\Z",
        provider_kind=_SneakyKind("claude-headless"),
    )


def test_driver_injection_rejection_creates_no_run_root_without_build_site_patch(
    tmp_path,
) -> None:
    run_root = tmp_path / "driver-before-run-root"
    reached: list[str] = []
    originals = {
        "AttemptJournal": A.AttemptJournal,
        "ensure_exploration_namespace": A.ensure_exploration_namespace,
        "_provider_set": A._provider_set,
    }

    def forbidden(name):
        def call(*args, **kwargs):
            reached.append(name)
            raise AssertionError(f"driver injection rejection reached {name}")

        return call

    try:
        for name in originals:
            setattr(A, name, forbidden(name))
        with pytest.raises(
            A.AutonomousTrialError,
            match=(
                r"^claude-headless drive/preview は caller 注入を許可しない\Z"
            ),
        ):
            A.run_trial(
                trial_id="driver-before-run-root",
                workloads=["ycsb-a"],
                generations=1,
                provider_kind="claude-headless",
                run_root=run_root,
                sub="/unused",
                do_build=False,
                drive=A.trigger.drive_iteration,
            )
    finally:
        for name, original in originals.items():
            setattr(A, name, original)
    for name, original in originals.items():
        assert getattr(A, name) is original
    assert reached == []
    assert not run_root.exists()


def test_omitted_claude_drivers_resolve_before_finish_trial(tmp_path) -> None:
    sequence: list[str] = []
    captured = {}
    original_provider_set = A._provider_set
    original_finish_trial = A._finish_trial
    expected_drive = A.trigger.drive_iteration
    expected_preview = A._preview

    def capture_provider_set(**kwargs):
        sequence.append("provider-set")
        assert kwargs["kind"] == "claude-headless"
        return {}

    def capture_finish_trial(**kwargs):
        sequence.append("finish-trial")
        captured.update(kwargs)
        return {"status": "captured"}

    try:
        A._provider_set = capture_provider_set
        A._finish_trial = capture_finish_trial
        report = A.run_trial(
            trial_id="omitted-claude-driver-resolution",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=tmp_path / "omitted-claude-driver-resolution",
            sub="/unused",
            do_build=False,
        )
    finally:
        A._finish_trial = original_finish_trial
        A._provider_set = original_provider_set
    assert A._provider_set is original_provider_set
    assert A._finish_trial is original_finish_trial
    assert report == {"status": "captured"}
    assert sequence == ["provider-set", "finish-trial"]
    assert captured["drive"] is expected_drive
    assert captured["preview"] is expected_preview
    assert captured["drive"] is not A._DRIVE_NOT_PROVIDED
    assert captured["preview"] is not A._PREVIEW_NOT_PROVIDED


def _fixture_preview(*args, **kwargs):
    del args, kwargs
    return {
        "passed": False,
        "working_diff": "",
        "diff_digest": "0" * 64,
        "subtype": "fixture",
        "reason": "deterministic pre-audit stop",
        "forbidden_identifiers": [],
    }


def _fixture_drive(*args, **kwargs):
    del args, kwargs
    return {
        "outcome": "rejected",
        "variant": "fixture-variant",
        "verdict": "fixture-verdict",
        "stop_reason": "continue",
        "iteration": 1,
        "ran": True,
        "records": {},
        "trigger_gate_binding_commitment": "b" * 64,
    }


def test_fixture_run_omitted_drivers_use_current_module_values(tmp_path) -> None:
    calls = {"drive": 0, "preview": 0}
    original_drive = A.trigger.drive_iteration
    original_preview = A._preview

    def drive(*args, **kwargs):
        calls["drive"] += 1
        return _fixture_drive(*args, **kwargs)

    def preview(*args, **kwargs):
        calls["preview"] += 1
        return _fixture_preview(*args, **kwargs)

    try:
        A.trigger.drive_iteration = drive
        A._preview = preview
        report = A.run_trial(
            trial_id="fixture-omitted-drivers",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=tmp_path / "fixture-omitted-drivers",
            sub="/unused",
            do_build=False,
        )
    finally:
        A._preview = original_preview
        A.trigger.drive_iteration = original_drive
    assert A.trigger.drive_iteration is original_drive
    assert A._preview is original_preview
    assert report["status"] == "complete"
    assert calls == {"drive": 1, "preview": 1}


def test_fixture_run_keeps_drive_and_preview_injection(tmp_path) -> None:
    calls = {"drive": 0, "preview": 0}

    def drive(*args, **kwargs):
        calls["drive"] += 1
        return _fixture_drive(*args, **kwargs)

    def preview(*args, **kwargs):
        calls["preview"] += 1
        return _fixture_preview(*args, **kwargs)

    report = A.run_trial(
        trial_id="fixture-explicit-drivers",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "fixture-explicit-drivers",
        sub="/unused",
        do_build=False,
        drive=drive,
        preview=preview,
    )
    assert report["status"] == "complete"
    assert calls == {"drive": 1, "preview": 1}


def test_tracker_pure_evaluator_rejects_duplicate_session_id() -> None:
    evaluation = evaluate_role_session_isolation(
        (("planner", "shared-session"), ("coder", "shared-session"))
    )
    assert evaluation.accepted is False
    tracker = CrossRoleSessionTracker()
    tracker.observe(role_name="planner", session_id="shared-session")
    with pytest.raises(RoleSessionIsolationError, match="mutually distinct"):
        tracker.observe(role_name="coder", session_id="shared-session")


def test_provider_set_shares_one_tracker_across_all_roles(tmp_path) -> None:
    calls: list[dict[str, object]] = []

    class _FakeProvider:
        def __init__(self, **kwargs) -> None:
            calls.append(kwargs)

        def close(self) -> None:
            return None

    providers = A._provider_set(
        kind="claude-headless",
        run_root=tmp_path / "run",
        executable="unused",
        projected_provider_factory=_FakeProvider,
    )
    assert list(providers) == list(A.ROLE_FILES)
    trackers = [call["cross_role_session_tracker"] for call in calls]
    assert len(trackers) == 4
    assert type(trackers[0]) is CrossRoleSessionTracker
    assert all(tracker is trackers[0] for tracker in trackers)


def test_constructor_rejects_tracker_subclass_before_artifact(tmp_path) -> None:
    class _TrackerSubclass(CrossRoleSessionTracker):
        pass

    artifact_root = tmp_path / "artifacts"
    with pytest.raises(PredictionRunnerError, match="exact 型"):
        ClaudeProjectedRoleProvider(
            artifact_root=artifact_root,
            role_file=_role_file(tmp_path / "role.md", "planner"),
            role_name="planner",
            mediated_contract="Return JSON only.",
            repository_root=_ROOT,
            executable=_executable(tmp_path / "claude"),
            environ={"HOME": "/fixture/home"},
            cross_role_session_tracker=_TrackerSubclass(),
        )
    assert not artifact_root.exists()


def test_separate_provider_instances_reject_shared_session(tmp_path) -> None:
    tracker = CrossRoleSessionTracker()
    planner = _provider(
        tmp_path, role="planner", session_id="shared-session", tracker=tracker,
    )
    coder = _provider(
        tmp_path, role="coder", session_id="shared-session", tracker=tracker,
    )
    try:
        planner.invoke(invocation_id="planner.one", payload={"x": 1})
        with pytest.raises(PredictionRunnerError) as caught:
            coder.invoke(invocation_id="coder.one", payload={"x": 1})
        assert isinstance(caught.value.__cause__, RoleSessionIsolationError)
    finally:
        coder.close()
        planner.close()


def test_separate_provider_instances_accept_distinct_sessions(tmp_path) -> None:
    tracker = CrossRoleSessionTracker()
    planner = _provider(
        tmp_path, role="planner", session_id="planner-session", tracker=tracker,
    )
    coder = _provider(
        tmp_path, role="coder", session_id="coder-session", tracker=tracker,
    )
    try:
        assert planner.invoke(
            invocation_id="planner.one", payload={"x": 1},
        ).provenance["child_id"] == "planner-session"
        assert coder.invoke(
            invocation_id="coder.one", payload={"x": 1},
        ).provenance["child_id"] == "coder-session"
    finally:
        coder.close()
        planner.close()


def test_consumer_rejects_duplicate_child_id_without_runtime_tracker(tmp_path) -> None:
    run, report = _claude_artifact(
        tmp_path,
        ("planner-session", "shared-session", "shared-session", "critic-session"),
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-session-isolation\].*mutually distinct$",
    ):
        C.assert_autonomous_trial_completeness(
            report=report, attempt_journal=run / "attempts.jsonl",
        )


def test_file_verifier_rejects_persisted_duplicate_child_id(tmp_path) -> None:
    run, _report = _claude_artifact(
        tmp_path,
        ("planner-session", "shared-session", "shared-session", "critic-session"),
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-session-isolation\].*mutually distinct$",
    ):
        C.verify_autonomous_trial_files(
            run / "attempts.jsonl", run / "report.json",
        )


@pytest.mark.parametrize("bad_child_id", ["", None], ids=("empty", "non-string"))
def test_consumer_rejects_invalid_child_id(tmp_path, bad_child_id: object) -> None:
    run, report = _claude_artifact(
        tmp_path,
        ("planner-session", bad_child_id, "auditor-session", "critic-session"),
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-session-isolation\].*non-empty str$",
    ):
        C.assert_autonomous_trial_completeness(
            report=report, attempt_journal=run / "attempts.jsonl",
        )


def test_consumer_rejects_truthy_non_string_child_id(tmp_path) -> None:
    run, report = _claude_artifact(
        tmp_path,
        ("planner-session", 1, "auditor-session", "critic-session"),
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-session-isolation\].*non-empty str$",
    ):
        C.assert_autonomous_trial_completeness(
            report=report, attempt_journal=run / "attempts.jsonl",
        )


def test_consumer_rejects_missing_child_id_from_nonempty_provenance(tmp_path) -> None:
    run, report = _claude_artifact(
        tmp_path,
        tuple(f"{role}-session" for role in F._ROLES),
    )
    events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    coder = next(
        event
        for event in events
        if event.get("event") == "role-attempt" and event.get("role") == "coder"
    )
    coder["provenance"] = {"fixture": True}
    report["cells"][0]["generations"][0]["roles"]["coder"]["provenance"] = {
        "fixture": True,
    }
    F._persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-session-isolation\].*non-empty str$",
    ):
        C.assert_autonomous_trial_completeness(
            report=report, attempt_journal=run / "attempts.jsonl",
        )


def test_consumer_accepts_distinct_claude_child_ids(tmp_path) -> None:
    run, report = _claude_artifact(
        tmp_path,
        tuple(f"{role}-session" for role in F._ROLES),
    )
    C.assert_autonomous_trial_completeness(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


def test_consumer_accepts_invalid_claude_attempt_in_partial_run(tmp_path) -> None:
    run, events, report = F._role_invalid_trial(tmp_path)
    report["provider"] = "claude-headless"
    events[0]["provider"] = "claude-headless"
    F._persist(run, events, report)
    C.assert_autonomous_trial_completeness(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


def test_consumer_keeps_fixture_provider_acceptance(tmp_path) -> None:
    run, _events, report = F._complete_trial(tmp_path)
    C.assert_autonomous_trial_completeness(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
