# -*- coding: utf-8 -*-
"""T316 probe の observer → judge → receipt 結線を固定する独立 oracle。"""
from __future__ import annotations

import errno
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

import pytest


_REPO = Path(__file__).resolve().parents[2]
_MODULE_PATH = _REPO / "tools/pegasus/probes/t316_sandbox_backend_probe.py"
_SPEC = importlib.util.spec_from_file_location("t316_sandbox_backend_probe", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probe
_SPEC.loader.exec_module(probe)


def test_condition_gate_dominates_ccbench_configure():
    source = inspect.getsource(probe._execute_ccbench_build)
    assert source.index("_require_condition_gate") < source.index(
        "profile.run(argv"
    )
    assert '"-DCCBENCH_BACKOFF_FIXED=-1"' in source
    assert '"-DCMAKE_CXX_FLAGS=-DBACKOFF_FIXED=-1"' not in source

# 実装定数を共有しない。カテゴリ削除変異で parametrize 自体が消えない独立 oracle。
EXPECTED_S3_CATEGORIES = (
    "network_dns", "network_direct_ip", "network_proxy", "credential_home",
    "credential_ssh_agent", "credential_ssh_dir", "credential_codex_dir",
    "write_home", "write_repo", "write_tmp", "source_read_only",
)
EXPECTED_S5_CATEGORIES = ("system_command", "network", "file_write", "infinite_loop")
EXPECTED_S5_PROFILES = ("runtime", "build")
EXPECTED_CONTAINMENT_DENIALS = {
    "network_dns": frozenset({"EAI_AGAIN", "EAI_NONAME"}),
    "network_direct_ip": frozenset(
        {"EACCES", "EPERM", "ENETDOWN", "ENETUNREACH", "EHOSTUNREACH", "EAFNOSUPPORT"}
    ),
    "network_proxy": frozenset(
        {"EACCES", "EPERM", "ENETDOWN", "ENETUNREACH", "EHOSTUNREACH", "EAFNOSUPPORT"}
    ),
    "credential_home": frozenset({"ENOENT"}),
    "credential_ssh_agent": frozenset({"ENOENT"}),
    "credential_ssh_dir": frozenset({"ENOENT"}),
    "credential_codex_dir": frozenset({"ENOENT"}),
    "write_home": frozenset({"EACCES", "EPERM", "EROFS"}),
    "write_repo": frozenset({"EACCES", "EPERM", "EROFS"}),
    "write_tmp": frozenset({"EACCES", "EPERM", "EROFS"}),
    "source_read_only": frozenset({"EACCES", "EPERM", "EROFS"}),
    "scratch_write": frozenset(),
    "system_command": frozenset({"ENOENT"}),
    "network": frozenset(
        {"EACCES", "EPERM", "ENETDOWN", "ENETUNREACH", "EHOSTUNREACH", "EAFNOSUPPORT"}
    ),
    "file_write": frozenset({"EACCES", "EPERM", "EROFS"}),
    "escaped_descendant": frozenset(),
    "infinite_loop": frozenset(),
}
EXPECTED_CONTAINMENT_ABSENCES = {
    "network_dns": frozenset(),
    "network_direct_ip": frozenset(),
    "network_proxy": frozenset(),
    "credential_home": frozenset({"ENOENT"}),
    "credential_ssh_agent": frozenset({"ENOENT"}),
    "credential_ssh_dir": frozenset({"ENOENT"}),
    "credential_codex_dir": frozenset({"ENOENT"}),
    "write_home": frozenset({"ENOENT"}),
    "write_repo": frozenset({"ENOENT"}),
    "write_tmp": frozenset({"ENOENT"}),
    "source_read_only": frozenset({"ENOENT"}),
    "scratch_write": frozenset(),
    "system_command": frozenset({"ENOENT"}),
    "network": frozenset(),
    "file_write": frozenset({"ENOENT"}),
    "escaped_descendant": frozenset(),
    "infinite_loop": frozenset(),
}
EXPECTED_ACTIVE_DENIALS = {
    **EXPECTED_CONTAINMENT_DENIALS,
    "credential_home": frozenset(),
    "credential_ssh_agent": frozenset(),
    "credential_ssh_dir": frozenset(),
    "credential_codex_dir": frozenset(),
    "system_command": frozenset(),
}


def _paired(*, inside_state: str = "denied", inside_blocked: bool = True) -> dict[str, Any]:
    return {
        "attempted": True, "outside_success": True, "inside_blocked": inside_blocked,
        "outside_payload_state": "reached", "inside_payload_state": inside_state,
        "outside_process_state": "normal-exit", "inside_process_state": "normal-exit",
    }


def _good_s3() -> dict[str, dict[str, Any]]:
    observations = {category: _paired() for category in EXPECTED_S3_CATEGORIES}
    observations["scratch_write"] = {
        "attempted": True, "inside_success": True, "inside_payload_state": "reached",
        "inside_process_state": "normal-exit",
    }
    return observations


def _good_s4() -> dict[str, Any]:
    return {
        "attempted": True, "outside_pid_status": "alive-same-process",
        "inside_pid_status": "gone", "outside_payload_state": "reached",
        "inside_payload_state": "reached",
    }


def _good_s5() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        profile_name: {
            category: (_good_s4() if category == "infinite_loop" else _paired())
            for category in EXPECTED_S5_CATEGORIES
        }
        for profile_name in EXPECTED_S5_PROFILES
    }


def _condition_gate_receipts() -> list[dict[str, Any]]:
    gate = probe.condition_meaning_gate
    request = gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    request_digest = gate._request_digest(request, ())
    supply = gate._arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code="stock-inert-preprocess-identical",
        request=request,
        request_digest=request_digest,
        evidence={
            "comparison": "stock-identity",
            "fixture": "independent-valid-record",
        },
    )
    meaning = gate._arm_record(
        arm="runtime-meaning",
        terminal_status="unestablished",
        reason_code="meaning-witness-undeclared",
        request=request,
        request_digest=request_digest,
        evidence={"witness_declared": False},
    )
    admission = gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    return [
        json.loads(supply.canonical_json()),
        json.loads(meaning.canonical_json()),
        json.loads(admission.canonical_json()),
    ]


def _good_s6() -> dict[str, Any]:
    return {
        "attempted": True, "source_identity_valid": True,
        "outside_success": True, "inside_success": True, "success": True,
        "trace_disabled": True, "failure_stage": None,
        "toolchain": {"host_valid": True, "sandbox_valid": True},
        "condition_gates": _condition_gate_receipts(),
    }


def _good_s7() -> dict[str, Any]:
    return {
        "attempted": True, "outside_success": True, "inside_success": True,
        "same_binary": True, "trace_disabled": True,
        "exclusivity_valid": True, "perf_output_valid": True,
        "effective_thread_count_valid": True, "warmup_valid": True,
        "elapsed_overhead_ratio_median": 1.01,
    }


def _good_stages() -> dict[str, dict[str, Any]]:
    return {
        "S1": {"attempted": True, "tools": {"bwrap": {"available": True, "path": "/bin/false"}}},
        "S2": {"attempted": True, "namespace_checks": {name: True for name in ("user", "pid", "net", "mnt")}},
        "S3": _good_s3(), "S4": _good_s4(), "S5": _good_s5(),
        "S6": _good_s6(), "S7": _good_s7(),
    }


def _command_record(
    stdout: str, *, rc: int = 0, executed: bool = True, timed_out: bool = False
) -> dict[str, Any]:
    data = stdout.encode()
    return {
        "attempted": True, "executed": executed, "rc": rc, "timed_out": timed_out,
        "stdout": probe._bounded_output(data), "stderr": probe._bounded_output(b""),
    }


class _SequenceRunner:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = list(records)

    def __call__(self, _argv: Any, **_kwargs: Any) -> dict[str, Any]:
        return self.records.pop(0)


def test_category_oracles_are_independent_literals() -> None:
    assert probe.S3_CATEGORIES == EXPECTED_S3_CATEGORIES
    assert probe.S5_CATEGORIES == EXPECTED_S5_CATEGORIES
    assert probe.S5_PROFILES == EXPECTED_S5_PROFILES
    assert probe._CONTAINMENT_DENIALS_BY_CATEGORY == EXPECTED_CONTAINMENT_DENIALS
    assert probe._PAYLOAD_NORMAL_RETURN_CODES == frozenset({0})


def test_containment_mechanism_table_matches_independent_literals() -> None:
    assert probe._CONTAINMENT_ERRNOS_BY_CATEGORY == {
        category: {
            "denial": EXPECTED_ACTIVE_DENIALS[category],
            "absence": EXPECTED_CONTAINMENT_ABSENCES[category],
        }
        for category in EXPECTED_CONTAINMENT_DENIALS
    }


@pytest.mark.parametrize(
    ("stage", "verdict_category", "sentinel_category"),
    [
        ("S3", "write_home", "write_home"),
        ("S5", "runtime_file_write", "file_write"),
        ("S5", "build_file_write", "file_write"),
    ],
)
def test_write_enoent_is_contained_by_absence_only_with_strict_controls(
    stage: str, verdict_category: str, sentinel_category: str
) -> None:
    target = "/same/positive-control-target"
    observation = {
        **_paired(inside_state="invalid", inside_blocked=False),
        "sentinel_category": sentinel_category,
        "inside_payload_detail": "ENOENT",
        "outside_path": target,
        "inside_path": target,
        "inside_side_effect_observed": False,
    }
    verdict = probe._paired_verdict(stage, verdict_category, observation)
    assert verdict.verdict == "go"
    assert verdict.reason_codes == (
        f"{stage}_{verdict_category}_CONTAINED_BY_ABSENCE".upper(),
    )


def test_write_enoent_with_failed_positive_control_is_not_containment() -> None:
    observation = {
        **_paired(inside_state="invalid", inside_blocked=False),
        "sentinel_category": "write_home",
        "outside_success": False,
        "outside_payload_state": "invalid",
        "outside_payload_detail": "ENOENT",
        "inside_payload_detail": "ENOENT",
        "outside_path": "/same/path",
        "inside_path": "/same/path",
        "inside_side_effect_observed": False,
    }
    verdict = probe._paired_verdict("S3", "write_home", observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.verdict != "go"


def test_write_enoent_with_inside_side_effect_remains_no_go() -> None:
    observation = {
        **_paired(inside_state="invalid", inside_blocked=False),
        "sentinel_category": "file_write",
        "inside_payload_detail": "ENOENT",
        "outside_path": "/same/path",
        "inside_path": "/same/path",
        "inside_side_effect_observed": True,
    }
    verdict = probe._paired_verdict("S5", "build_file_write", observation)
    assert verdict.verdict == "no-go"
    assert verdict.reason_codes == ("S5_BUILD_FILE_WRITE_SIDE_EFFECT_OBSERVED",)


def test_write_enoent_with_different_positive_target_is_inconclusive() -> None:
    observation = {
        **_paired(inside_state="invalid", inside_blocked=False),
        "sentinel_category": "write_repo",
        "inside_payload_detail": "ENOENT",
        "outside_path": "/outside/path",
        "inside_path": "/inside/path",
        "inside_side_effect_observed": False,
    }
    verdict = probe._paired_verdict("S3", "write_repo", observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S3_WRITE_REPO_POSITIVE_CONTROL_TARGET_MISMATCH",)


def test_active_write_denial_keeps_contained_reason_code() -> None:
    verdict = probe._paired_verdict("S3", "write_repo", _paired())
    assert verdict.verdict == "go"
    assert verdict.reason_codes == ("S3_WRITE_REPO_CONTAINED",)


def test_outside_denial_reports_node_capability_unavailable() -> None:
    observation = {
        **_paired(),
        "outside_success": False,
        "outside_payload_state": "denied",
        "outside_payload_detail": "EAI_AGAIN",
    }
    verdict = probe._paired_verdict("S3", "network_dns", observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S3_NETWORK_DNS_NODE_CAPABILITY_UNAVAILABLE",)


@pytest.mark.parametrize("category", EXPECTED_S3_CATEGORIES)
def test_s3_failed_positive_control_is_inconclusive(category: str) -> None:
    observations = _good_s3()
    observations[category]["outside_success"] = False
    observations[category]["outside_payload_state"] = "missing"
    verdict = probe.verdict_s3(observations)
    assert verdict.verdict == "inconclusive"
    assert verdict.verdict != "go"


@pytest.mark.parametrize("profile_name", EXPECTED_S5_PROFILES)
@pytest.mark.parametrize("category", EXPECTED_S5_CATEGORIES)
def test_each_s5_containment_failure_is_not_go(profile_name: str, category: str) -> None:
    observations = _good_s5()
    if category == "infinite_loop":
        observations[profile_name][category]["inside_pid_status"] = "alive-same-process"
    else:
        observations[profile_name][category]["inside_blocked"] = False
        observations[profile_name][category]["inside_payload_state"] = "reached"
    assert probe.verdict_s5(observations).verdict == "no-go"


@pytest.mark.parametrize("inside_state", ["missing", "invalid", "error", "not-executed"])
def test_boolean_inside_blocked_cannot_replace_structured_sentinel(inside_state: str) -> None:
    observation = _paired(inside_state=inside_state, inside_blocked=True)
    verdict = probe._paired_verdict("S3", "network_dns", observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.verdict != "go"


def test_eexist_is_not_a_containment_denial() -> None:
    record = _command_record("T316_SENTINEL|write_repo|DENIED|EEXIST\n")
    parsed = probe._parse_payload_sentinel(record, "write_repo")
    assert parsed == {"state": "invalid", "detail": "EEXIST"}


@pytest.mark.parametrize(
    ("category", "errno_name", "expected"),
    [
        ("network_dns", "EAI_AGAIN", "denied"),
        ("network_direct_ip", "EAI_AGAIN", "invalid"),
        ("network_direct_ip", "ETIMEDOUT", "invalid"),
        ("write_repo", "EROFS", "denied"),
        ("write_repo", "ENOENT", "invalid"),
        ("credential_home", "ENOENT", "denied"),
    ],
)
def test_denial_errno_is_scoped_to_its_category(
    category: str, errno_name: str, expected: str
) -> None:
    record = _command_record(
        f"T316_SENTINEL|{category}|DENIED|{errno_name}\n"
    )
    assert probe._parse_payload_sentinel(record, category)["state"] == expected


@pytest.mark.parametrize("detail", ["ERROR", "ENOSYS"])
def test_unknown_or_error_sentinel_is_never_denied(detail: str) -> None:
    status = "ERROR" if detail == "ERROR" else "DENIED"
    record = _command_record(f"T316_SENTINEL|network|{status}|{detail}\n")
    assert probe._parse_payload_sentinel(record, "network")["state"] != "denied"


@pytest.mark.parametrize(
    ("record", "expected_state"),
    [
        (
            _command_record(
                "T316_SENTINEL|network_direct_ip|DENIED|ENETUNREACH\n",
                rc=-9,
                timed_out=True,
            ),
            "timed-out",
        ),
        (
            _command_record(
                "T316_SENTINEL|network_direct_ip|DENIED|ENETUNREACH\n",
                rc=7,
            ),
            "unexpected-exit",
        ),
    ],
)
def test_payload_sentinel_and_process_exit_are_independent(
    record: dict[str, Any], expected_state: str
) -> None:
    parsed = probe._parse_payload_sentinel(record, "network_direct_ip")
    assert parsed["state"] == "denied"
    assert probe._process_exit(record)["state"] == expected_state


def test_connection_refused_is_reachability_evidence_and_no_go(tmp_path: Path) -> None:
    runner = _SequenceRunner([
        _command_record("T316_SENTINEL|network_direct_ip|REACHED\n"),
        _command_record("T316_SENTINEL|network_direct_ip|DENIED|ECONNREFUSED\n"),
    ])
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._paired_command(
        profile, ["payload"], sentinel_category="network_direct_ip"
    )
    assert observation["inside_payload_state"] == "reached"
    assert probe._paired_verdict(
        "S3", "network_direct_ip", observation
    ).verdict == "no-go"


@pytest.mark.parametrize(
    ("inside_rc", "timed_out", "process_state"),
    [(-9, True, "timed-out"), (9, False, "unexpected-exit")],
)
def test_paired_command_rejects_denied_after_abnormal_exit(
    tmp_path: Path, inside_rc: int, timed_out: bool, process_state: str
) -> None:
    runner = _SequenceRunner([
        _command_record("T316_SENTINEL|network_direct_ip|REACHED\n"),
        _command_record(
            "T316_SENTINEL|network_direct_ip|DENIED|ENETUNREACH\n",
            rc=inside_rc,
            timed_out=timed_out,
        ),
    ])
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._paired_command(
        profile, ["payload"], sentinel_category="network_direct_ip"
    )
    assert observation["inside_blocked"] is False
    assert observation["inside_payload_state"] == "denied"
    assert observation["inside_process_state"] == process_state
    assert probe._paired_verdict(
        "S3", "network_direct_ip", observation
    ).verdict == "inconclusive"


def test_runner_seam_distinguishes_bwrap_setup_failure_from_payload_denial(tmp_path: Path) -> None:
    runner = _SequenceRunner([
        _command_record("T316_SENTINEL|network_dns|REACHED\n"),
        _command_record("", rc=125),
    ])
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._paired_command(
        profile, ["payload"], sentinel_category="network_dns"
    )
    assert observation["inside_blocked"] is False
    assert observation["inside_payload_state"] == "missing"
    assert observation["inside_process_state"] == "unexpected-exit"
    assert probe._paired_verdict("S3", "network_dns", observation).verdict == "inconclusive"


def test_poll_pid_identity_reports_a_live_same_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        probe, "_proc_identity", lambda _pid: (123, b"payload\0owned-token\0")
    )
    assert probe._poll_pid_identity(77, 123, "owned-token", 0) == "alive-same-process"


def test_actual_descendant_observer_preserves_inside_survival_no_go(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, ())
    records = iter([
        {
            "attempted": True, "executed": True,
            "pid_status": "alive-same-process", "payload_state": "reached",
            "host_pid": None, "start_ticks": 1, "owned_token_pids_before": {},
        },
        {
            "attempted": True, "executed": True,
            "pid_status": "alive-same-process", "payload_state": "reached",
            "host_pid": None, "start_ticks": 1, "owned_token_pids_before": {},
        },
    ])

    def fake_escape_runner(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return next(records)

    observation = probe.observe_s4(
        profile, sys.executable, scratch, escape_runner=fake_escape_runner
    )
    assert observation["inside_pid_status"] == "alive-same-process"
    assert probe.verdict_s4(observation).verdict == "no-go"


def test_actual_binary_descendant_observer_preserves_inside_survival_no_go(
    tmp_path: Path,
) -> None:
    scratch = tmp_path / "scratch-binary"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, ())
    records = iter([
        {
            "attempted": True, "executed": True,
            "pid_status": "alive-same-process", "payload_state": "reached",
            "host_pid": None, "start_ticks": 1, "owned_token_pids_before": {},
        },
        {
            "attempted": True, "executed": True,
            "pid_status": "alive-same-process", "payload_state": "reached",
            "host_pid": None, "start_ticks": 1, "owned_token_pids_before": {},
        },
    ])

    def fake_escape_runner(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return next(records)

    observation = probe._observe_binary_descendant(
        profile,
        tmp_path / "fake-binary",
        scratch,
        "s5-test",
        build=False,
        escape_runner=fake_escape_runner,
    )
    assert observation["inside_pid_status"] == "alive-same-process"
    assert probe._verdict_descendant(
        "S5", "S5_RUNTIME_INFINITE_LOOP", observation
    ).verdict == "no-go"


def test_identity_unresolved_cleanup_uses_owned_token_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scans = iter([{42: 9001}, {}])
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(probe, "_token_process_identities", lambda _token: next(scans))
    monkeypatch.setattr(
        probe, "_proc_identity", lambda pid: (9001, b"payload\0unique-token\0")
        if pid == 42 else None,
    )
    monkeypatch.setattr(probe.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(probe.time, "sleep", lambda _seconds: None)
    cleanup = probe._cleanup_exact_process(
        {
            "host_pid": None,
            "start_ticks": 9001,
            "pid_status": "identity-unresolved",
            "owned_token_pids_before": {},
        },
        "unique-token",
    )
    assert cleanup["method"] == "token-fallback"
    assert cleanup["candidate_pids"] == [42]
    assert cleanup["residual_pids"] == []
    assert cleanup["succeeded"] is True
    assert {pid for pid, _sig in killed} == {42}


@pytest.mark.parametrize(
    ("stage", "category"), [("S3", "write_repo"), ("S5", "file_write")]
)
def test_actual_write_observer_cannot_hide_inside_side_effect(
    tmp_path: Path, stage: str, category: str
) -> None:
    scratch = tmp_path / f"scratch-{stage}"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    outside_path = tmp_path / f"{stage}-outside"
    inside_path = tmp_path / f"{stage}-inside"
    calls = 0

    def runner(_argv: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        path = outside_path if calls == 0 else inside_path
        path.write_text("side effect", encoding="utf-8")
        calls += 1
        return _command_record(f"T316_SENTINEL|{category}|REACHED\n")

    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._observe_write_pair(
        profile, ["outside"], ["inside"], outside_path, inside_path, category
    )
    assert observation["inside_payload_state"] == "reached"
    assert observation["inside_blocked"] is False
    assert observation["inside_side_effect_observed"] is True
    # state を誤って denied に固定しても、marker が no-go を維持する。
    observation["inside_payload_state"] = "denied"
    observation["inside_blocked"] = True
    assert probe._paired_verdict(stage, category, observation).verdict == "no-go"


def test_actual_write_observer_uses_one_target_for_absence_control(
    tmp_path: Path,
) -> None:
    scratch = tmp_path / "scratch-absence"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    target = tmp_path / "paired-target"
    calls = 0

    def runner(_argv: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            target.write_text("outside positive", encoding="utf-8")
            return _command_record("T316_SENTINEL|write_home|REACHED\n")
        assert not target.exists()
        return _command_record("T316_SENTINEL|write_home|DENIED|ENOENT\n")

    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._observe_write_pair(
        profile, ["outside"], ["inside"], target, target, "write_home"
    )
    assert observation["outside_success"] is True
    assert observation["outside_path"] == observation["inside_path"] == str(target)
    assert observation["inside_side_effect_observed"] is False
    verdict = probe._paired_verdict("S3", "write_home", observation)
    assert verdict.verdict == "go"
    assert verdict.reason_codes == ("S3_WRITE_HOME_CONTAINED_BY_ABSENCE",)


@pytest.mark.parametrize(
    ("inside_sentinel", "inside_marker", "expected"),
    [
        ("T316_SENTINEL|system_command|DENIED|ENOENT\n", False, "go"),
        ("T316_SENTINEL|system_command|ERROR|COMMAND_EXIT_1\n", False, "no-go"),
        (
            "T316_SENTINEL|system_command|ERROR|SIDE_EFFECT_WITH_FAILURE\n",
            True,
            "no-go",
        ),
    ],
)
def test_system_observer_distinguishes_shell_absence_command_failure_and_side_effect(
    tmp_path: Path, inside_sentinel: str, inside_marker: bool, expected: str
) -> None:
    scratch = tmp_path / f"system-{expected}"
    scratch.mkdir()
    (scratch / "empty-tmp").mkdir()
    outside_path = tmp_path / f"system-{expected}-outside"
    inside_path = tmp_path / f"system-{expected}-inside"
    calls = 0

    def runner(_argv: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        if calls == 0:
            outside_path.write_text("outside", encoding="utf-8")
            sentinel = "T316_SENTINEL|system_command|REACHED\n"
        else:
            if inside_marker:
                inside_path.write_text("inside", encoding="utf-8")
            sentinel = inside_sentinel
        calls += 1
        return _command_record(sentinel)

    profile = probe.SandboxProfile("/bin/false", tmp_path, scratch, (), runner=runner)
    observation = probe._observe_system_pair(
        profile, tmp_path / "fake-binary", outside_path, inside_path, build=False
    )
    assert probe._paired_verdict(
        "S5", "runtime_system_command", observation
    ).verdict == expected


def test_cleanup_failure_makes_performance_inconclusive() -> None:
    observation = {**_good_s7(), "cleanup_integrity_valid": False}
    verdict = probe.verdict_s7(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S7_PREVIOUS_PAYLOAD_CLEANUP_UNPROVEN",)


def test_process_tenancy_keeps_excluded_system_and_own_observations() -> None:
    evidence = probe._classify_process_owners(
        {10: 0, 11: 100, 12: 997, 13: 1000, 14: 2000}, own_uid=1000
    )
    assert evidence["other_non_root_user_processes"] == {
        "present": True, "count": 3, "uids": [100, 997, 2000], "pids": [11, 12, 14]
    }
    assert evidence["other_non_system_user_processes"] == {
        "present": True, "count": 1, "uids": [2000], "pids": [14]
    }
    assert evidence["excluded_system_processes"] == {
        "present": True, "count": 3, "uids": [0, 100, 997], "pids": [10, 11, 12]
    }
    assert evidence["excluded_own_processes"] == {
        "present": True, "count": 1, "uids": [1000], "pids": [13]
    }


def test_system_daemons_do_not_count_as_co_tenants() -> None:
    snapshot = {
        "other_non_root_user_processes": {
            "present": True, "count": 18, "uids": [100, 997], "pids": list(range(18))
        },
        "other_non_system_user_processes": {
            "present": False, "count": 0, "uids": [], "pids": []
        },
        "load_average": [0.25, 0.5, 0.75],
        "nproc": 48,
    }
    assert probe._exclusive_snapshot_valid(snapshot, 1.0) is True


def test_other_non_system_user_process_prevents_exclusivity() -> None:
    snapshot = {
        "other_non_system_user_processes": {
            "present": True, "count": 1, "uids": [2000], "pids": [42]
        },
        "load_average": [0.0, 0.0, 0.0],
        "nproc": 48,
    }
    assert probe._exclusive_snapshot_valid(snapshot, 1.0) is False


def test_load_average_threshold_still_prevents_exclusivity() -> None:
    snapshot = {
        "other_non_system_user_processes": {
            "present": False, "count": 0, "uids": [], "pids": []
        },
        "load_average": [48.01, 0.0, 0.0],
        "nproc": 48,
    }
    assert probe._exclusive_snapshot_valid(snapshot, 1.0) is False


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (("go", "no-go", "blocked", "inconclusive"), "no-go"),
        (("go", "blocked", "inconclusive"), "blocked"),
        (("go", "inconclusive"), "inconclusive"),
    ],
)
def test_merge_priority_is_fail_closed(statuses: tuple[str, ...], expected: str) -> None:
    verdicts = [probe.StageVerdict("S3", value, (value,)) for value in statuses]
    assert probe._merge_stage_verdicts("S3", verdicts).verdict == expected


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        (probe.StageVerdict("S4", "no-go", ("x",)), "no-go"),
        (probe.StageVerdict("S4", "blocked", ("x",)), "blocked"),
        (probe.StageVerdict("S4", "inconclusive", ("x",)), "inconclusive"),
    ],
)
def test_overall_priority_is_fail_closed(replacement: Any, expected: str) -> None:
    verdicts = [probe.StageVerdict(f"S{index}", "go", ("ok",)) for index in range(1, 8)]
    verdicts[3] = replacement
    assert probe.aggregate_verdicts(verdicts).verdict == expected


@pytest.mark.parametrize(
    ("judge", "bad", "expected"),
    [
        (probe.verdict_s4, {**_good_s4(), "inside_pid_status": "alive-same-process"}, "no-go"),
        (probe.verdict_s4, {**_good_s4(), "inside_pid_status": "pidfile-missing"}, "inconclusive"),
        (probe.verdict_s6, {**_good_s6(), "outside_success": False}, "inconclusive"),
        (probe.verdict_s6, {**_good_s6(), "inside_success": False, "success": False}, "no-go"),
        (probe.verdict_s7, {**_good_s7(), "perf_output_valid": False}, "inconclusive"),
        (probe.verdict_s7, {**_good_s7(), "inside_success": False}, "no-go"),
    ],
)
def test_stage_judges_reject_injected_bad_observations(judge: Any, bad: dict[str, Any], expected: str) -> None:
    verdict = judge(bad)
    assert verdict.verdict == expected
    assert verdict.verdict != "go"


def test_s6_injected_success_without_condition_records_is_not_go() -> None:
    observation = _good_s6()
    observation.pop("condition_gates")
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


def _run_injected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stages: dict[str, dict[str, Any]]
) -> tuple[int, dict[str, Any]]:
    cache = tmp_path / "cache"
    dependencies = tmp_path / "dependencies"
    scratch = tmp_path / "scratch-root"
    for path in (cache, dependencies, scratch):
        path.mkdir()
    monkeypatch.setenv("PBS_JOBID", "12345.test")
    monkeypatch.setenv("IZANAGI_PEGASUS_THIRDPARTY_CACHE", str(cache))
    monkeypatch.setenv("IZANAGI_T139_DEPENDENCY_SOURCE_ROOT", str(dependencies))
    return probe.run_probe(
        _REPO, scratch,
        execution_binding={"test_injected": True},
        observer_runner=lambda stage, _observer: stages[stage],
    )


@pytest.mark.parametrize(
    ("stage", "replacement", "expected"),
    [
        ("S1", {"attempted": True, "tools": {"bwrap": {"available": False}}}, "no-go"),
        (
            "S2",
            {
                "attempted": True,
                "namespace_checks": {"user": False, "pid": True, "net": True, "mnt": True},
            },
            "no-go",
        ),
        (
            "S3",
            {
                **_good_s3(),
                "write_repo": _paired(inside_state="reached", inside_blocked=False),
            },
            "no-go",
        ),
        ("S4", {**_good_s4(), "inside_pid_status": "alive-same-process"}, "no-go"),
        (
            "S5",
            {
                **_good_s5(),
                "runtime": {
                    **_good_s5()["runtime"],
                    "system_command": _paired(
                        inside_state="reached", inside_blocked=False
                    ),
                },
            },
            "no-go",
        ),
        ("S6", {**_good_s6(), "outside_success": False}, "inconclusive"),
        ("S7", {**_good_s7(), "perf_output_valid": False}, "inconclusive"),
    ],
)
def test_injected_observer_flows_through_judge_and_overall(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    stage: str, replacement: dict[str, Any], expected: str,
) -> None:
    stages = _good_stages()
    stages[stage] = replacement
    rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    assert rc == 3
    assert receipt["overall_verdict"]["verdict"] == expected
    by_stage = {item["stage"]: item for item in receipt["stage_verdicts"]}
    assert by_stage[stage]["verdict"] == expected
    assert by_stage[stage]["verdict"] != "go"


def test_s5_build_system_side_effect_keeps_overall_no_go_with_write_absence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stages = _good_stages()
    same_target = "/home/tester/s5-build-write"
    stages["S5"]["build"]["file_write"] = {
        **_paired(inside_state="invalid", inside_blocked=False),
        "sentinel_category": "file_write",
        "inside_payload_detail": "ENOENT",
        "outside_path": same_target,
        "inside_path": same_target,
        "inside_side_effect_observed": False,
    }
    stages["S5"]["build"]["system_command"] = {
        **_paired(inside_state="reached", inside_blocked=False),
        "sentinel_category": "system_command",
        "inside_side_effect_observed": True,
    }
    rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    by_stage = {item["stage"]: item for item in receipt["stage_verdicts"]}
    assert rc == 3
    assert by_stage["S5"]["verdict"] == "no-go"
    assert "S5_BUILD_FILE_WRITE_CONTAINED_BY_ABSENCE" in by_stage["S5"]["reason_codes"]
    assert "S5_BUILD_SYSTEM_COMMAND_SIDE_EFFECT_OBSERVED" in by_stage["S5"]["reason_codes"]
    assert receipt["overall_verdict"]["verdict"] == "no-go"


@pytest.mark.parametrize("category", EXPECTED_S3_CATEGORIES)
def test_each_s3_category_failure_reaches_stage_and_overall(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, category: str
) -> None:
    stages = _good_stages()
    stages["S3"][category] = _paired(
        inside_state="reached", inside_blocked=False
    )
    rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    by_stage = {item["stage"]: item for item in receipt["stage_verdicts"]}
    assert rc == 3
    assert by_stage["S3"]["verdict"] == "no-go"
    assert receipt["overall_verdict"]["verdict"] == "no-go"


def test_s3_scratch_positive_control_failure_reaches_stage_and_overall(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stages = _good_stages()
    stages["S3"]["scratch_write"]["inside_success"] = False
    rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    by_stage = {item["stage"]: item for item in receipt["stage_verdicts"]}
    assert rc == 3
    assert by_stage["S3"]["verdict"] == "no-go"
    assert receipt["overall_verdict"]["verdict"] == "no-go"


@pytest.mark.parametrize("profile_name", EXPECTED_S5_PROFILES)
@pytest.mark.parametrize("category", EXPECTED_S5_CATEGORIES)
def test_each_s5_category_failure_reaches_stage_and_overall(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    profile_name: str, category: str,
) -> None:
    stages = _good_stages()
    if category == "infinite_loop":
        stages["S5"][profile_name][category]["inside_pid_status"] = "alive-same-process"
    else:
        stages["S5"][profile_name][category] = _paired(
            inside_state="reached", inside_blocked=False
        )
    rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    by_stage = {item["stage"]: item for item in receipt["stage_verdicts"]}
    assert rc == 3
    assert by_stage["S5"]["verdict"] == "no-go"
    assert receipt["overall_verdict"]["verdict"] == "no-go"


def test_receipt_publish_is_atomic_create_only_and_completed(tmp_path: Path) -> None:
    publisher = probe.ReceiptPublisher(tmp_path, "123.test")
    publisher.persist_partial({"stage": "S1"})
    publisher.persist_partial({"stage": "S2"})
    assert json.loads((publisher.job_dir / "PARTIAL.json").read_text())["stage"] == "S2"
    first = {
        "state": "complete",
        "completion_predicate": probe._completion_predicate(),
        "overall": "no-go",
        "serial": 1,
    }
    path = publisher.publish_final(first)
    before = path.read_bytes()
    assert (publisher.job_dir / "COMPLETED").read_text().strip() == probe._sha256_file(path)
    assert json.loads(path.read_text())["state"] == "complete"
    assert not (publisher.job_dir / "PARTIAL.json").exists()
    with pytest.raises(FileExistsError):
        publisher.publish_final({"state": "complete", "overall": "go", "serial": 2})
    assert path.read_bytes() == before


def test_publish_failure_never_leaves_canonical_partial_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    publisher = probe.ReceiptPublisher(tmp_path, "456.test")

    def fail_link(_source: Path, _destination: Path) -> None:
        raise OSError(errno.EINVAL, "injected link failure")

    monkeypatch.setattr(probe, "_link_noreplace", fail_link)
    with pytest.raises(OSError):
        publisher.publish_final({"state": "complete", "overall": "go"})
    assert not (publisher.job_dir / "receipt.json").exists()
    assert not (publisher.job_dir / "COMPLETED").exists()


def test_completed_marker_publish_is_atomic_and_create_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    publisher = probe.ReceiptPublisher(tmp_path, "marker.test")
    publisher.persist_partial({"state": "partial", "stage": "S7"})
    real_link = probe._link_noreplace

    def fail_marker(source: Path, destination: Path) -> None:
        if destination.name == "COMPLETED":
            raise OSError(errno.EIO, "injected marker publish failure")
        real_link(source, destination)

    monkeypatch.setattr(probe, "_link_noreplace", fail_marker)
    with pytest.raises(OSError):
        publisher.publish_final({"state": "complete", "overall": "go"})
    assert json.loads((publisher.job_dir / "receipt.json").read_text())["state"] == "complete"
    assert not (publisher.job_dir / "COMPLETED").exists()
    assert not (publisher.job_dir / "PARTIAL.json").exists()
    assert list(publisher.job_dir.glob(".COMPLETED.*.tmp")) == []


def test_completed_marker_short_write_never_publishes_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    publisher = probe.ReceiptPublisher(tmp_path, "short-write.test")
    monkeypatch.setattr(probe.os, "write", lambda _fd, _value: 0)
    with pytest.raises(OSError):
        publisher.publish_final({"state": "complete", "overall": "go"})
    assert (publisher.job_dir / "receipt.json").is_file()
    assert not (publisher.job_dir / "COMPLETED").exists()
    assert list(publisher.job_dir.glob(".COMPLETED.*.tmp")) == []


def test_publish_preflight_einval_stops_before_measurement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("PBS_JOBID", "789.test")
    monkeypatch.setattr(probe, "_execution_binding", lambda _repo: {"test": True})

    def fail_link(_source: Path, _destination: Path) -> None:
        raise OSError(errno.EINVAL, "injected EINVAL")

    measurement_started = False

    def forbidden_run_probe(*_args: Any, **_kwargs: Any) -> tuple[int, dict[str, Any]]:
        nonlocal measurement_started
        measurement_started = True
        raise AssertionError("measurement must not start after publish preflight failure")

    monkeypatch.setattr(probe.os, "link", fail_link)
    monkeypatch.setattr(probe, "run_probe", forbidden_run_probe)
    rc = probe.main(["--repo-root", str(tmp_path), "--scratch-root", str(scratch)])
    job_dir = tmp_path / "output/env/pegasus/t316-sandbox-backend/789.test"
    assert rc == 4
    assert measurement_started is False
    assert not (job_dir / "receipt.json").exists()
    assert not (job_dir / "COMPLETED").exists()
    assert list(job_dir.glob(".PUBLISH-PREFLIGHT*")) == []


def test_r3_1_coverage_does_not_overclaim(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rc, receipt = _run_injected(monkeypatch, tmp_path, _good_stages())
    assert rc == 0
    assert receipt["overall_verdict"]["verdict"] == "go"
    assert receipt["state"] == "complete"
    assert receipt["completion_predicate"] == {
        "and": [
            {"path_exists": "COMPLETED"},
            {"json_parseable": "receipt.json"},
            {"equals": [{"json_pointer": "/state"}, "complete"]},
        ]
    }
    assert [item["verdict"] for item in receipt["stage_verdicts"]] == ["go"] * 7
    coverage = receipt["r3_1_coverage"]
    assert coverage["overall_go_does_not_mean_r3_1_complete"] is True
    assert coverage["not_discharged_by_this_probe"] == [
        "stock and variant performance difference",
        "trace-enabled correctness run",
        "floor recalibration requirement determination",
    ]
    assert receipt["stage_verdicts"][-1]["reason_codes"] == [
        "S7_ELAPSED_OVERHEAD_SAMPLE_RECORDED_ONLY"
    ]


def test_containment_discharge_when_all_containment_stages_go(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _rc, receipt = _run_injected(monkeypatch, tmp_path, _good_stages())
    assert (
        "compute-node backend containment observations"
        in receipt["r3_1_coverage"]["discharged_by_this_probe"]
    )


def test_performance_discharge_when_s7_go(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _rc, receipt = _run_injected(monkeypatch, tmp_path, _good_stages())
    assert (
        "single stock trace-disabled binary sandbox elapsed-overhead sample"
        in receipt["r3_1_coverage"]["discharged_by_this_probe"]
    )


@pytest.mark.parametrize("stage", ["S1", "S2", "S3", "S4", "S5"])
def test_containment_discharge_requires_each_containment_stage_go(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stage: str
) -> None:
    stages = _good_stages()
    if stage == "S1":
        stages[stage] = {"attempted": True, "tools": {"bwrap": {"available": False}}}
    elif stage == "S2":
        stages[stage] = {
            "attempted": True,
            "namespace_checks": {"user": False, "pid": True, "net": True, "mnt": True},
        }
    elif stage == "S3":
        stages[stage]["write_repo"] = _paired(
            inside_state="reached", inside_blocked=False
        )
    elif stage == "S4":
        stages[stage]["inside_pid_status"] = "alive-same-process"
    else:
        stages[stage]["runtime"]["network"] = _paired(
            inside_state="reached", inside_blocked=False
        )
    _rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    assert (
        "compute-node backend containment observations"
        not in receipt["r3_1_coverage"]["discharged_by_this_probe"]
    )


def test_performance_discharge_requires_s7_go(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stages = _good_stages()
    stages["S7"]["perf_output_valid"] = False
    _rc, receipt = _run_injected(monkeypatch, tmp_path, stages)
    assert (
        "single stock trace-disabled binary sandbox elapsed-overhead sample"
        not in receipt["r3_1_coverage"]["discharged_by_this_probe"]
    )


def _run() -> int:
    """pytest fixtures と parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
