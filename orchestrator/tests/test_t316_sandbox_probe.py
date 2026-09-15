# -*- coding: utf-8 -*-
"""T316 probe の observer → judge → receipt 結線を固定する独立 oracle。"""
from __future__ import annotations

import dataclasses
import errno
import functools
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
    assert source.index("_require_condition_gate") < source.index(
        'commands.extend((\n            ("ccbench-configure"'
    )
    assert "and not inside" not in source
    assert '"-DCCBENCH_BACKOFF_FIXED=-1"' in source
    assert '"-DCMAKE_CXX_FLAGS=-DBACKOFF_FIXED=-1"' not in source


def test_require_condition_gate_rejection_reports_detail_to_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    source = (
        _REPO / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    )
    root = tmp_path / "condition-gate-configure-failure"
    shutil.copytree(source, root)
    cmake_file = root / "CMakeLists.txt"
    cmake_file.write_text(
        cmake_file.read_text(encoding="utf-8")
        + '\nmessage(FATAL_ERROR "T316_CONFIGURE_DETAIL_WITNESS")\n',
        encoding="utf-8",
    )
    cxx = shutil.which("c++")
    cmake = shutil.which("cmake")
    assert cxx is not None and cmake is not None

    with pytest.raises(RuntimeError) as rejected:
        probe._require_condition_gate(
            root, stock_root=root / "stock",
            configure_args=("-DCCBENCH_BACKOFF_FIXED=-1",),
            cxx=cxx, cmake=cmake,
        )

    assert str(rejected.value) == (
        "condition gate rejected t316 CCBench build: "
        "supply=red/configure-failed, "
        "meaning=unestablished/meaning-witness-undeclared"
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith(
        "condition gate rejected t316 CCBench build: supply detail="
        "process returned rc=1; stderr="
    )
    assert "T316_CONFIGURE_DETAIL_WITNESS" in lines[0]
    assert "argv=" in lines[0]
    assert cmake in lines[0]
    assert lines[1] == (
        "condition gate rejected t316 CCBench build: meaning detail=<no detail>"
    )


@pytest.mark.parametrize("output_error_type", [OSError, ValueError, RuntimeError])
def test_require_condition_gate_rejection_survives_stderr_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    output_error_type: type[Exception],
) -> None:
    source = _REPO / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    root = tmp_path / "condition-gate-configure-failure"
    shutil.copytree(source, root)
    cmake_file = root / "CMakeLists.txt"
    cmake_file.write_text(
        cmake_file.read_text(encoding="utf-8")
        + '\nmessage(FATAL_ERROR "T316_STDERR_FAILURE_WITNESS")\n',
        encoding="utf-8",
    )
    cxx = shutil.which("c++")
    cmake = shutil.which("cmake")
    assert cxx is not None and cmake is not None
    attempted_writes: list[str] = []
    output_error = output_error_type("diagnostic stream cannot write")

    class UnwritableStderr:
        def write(self, text: str) -> int:
            attempted_writes.append(text)
            raise output_error

    with monkeypatch.context() as patch:
        patch.setattr(sys, "stderr", UnwritableStderr())
        with pytest.raises(RuntimeError) as rejected:
            probe._require_condition_gate(
                root, stock_root=root / "stock",
                configure_args=("-DCCBENCH_BACKOFF_FIXED=-1",),
                cxx=cxx, cmake=cmake,
            )

    assert type(rejected.value) is RuntimeError
    assert str(rejected.value) == (
        "condition gate rejected t316 CCBench build: "
        "supply=red/configure-failed, "
        "meaning=unestablished/meaning-witness-undeclared"
    )
    assert rejected.value.__cause__ is output_error
    assert len(attempted_writes) == 1
    assert attempted_writes[0].startswith(
        "condition gate rejected t316 CCBench build: supply detail="
        "process returned rc=1; stderr="
    )
    assert "T316_STDERR_FAILURE_WITNESS" in attempted_writes[0]
    assert "argv=" in attempted_writes[0]
    assert str(Path(cmake).resolve()) in attempted_writes[0]


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


@functools.lru_cache(maxsize=None)
def _condition_gate_family(
    comparison: str,
) -> tuple[Any, Any, Any]:
    gate = probe.condition_meaning_gate
    source = (
        _REPO
        / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    )
    request = gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    captured = gate.capture_define_inputs(
        source, stock_root=source / "stock", configure_args=(),
    )
    cxx = shutil.which("c++")
    cmake = shutil.which("cmake")
    assert cxx is not None and cmake is not None
    supply = gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake=cmake,
    )
    assert supply.terminal_status == "green"
    assert supply.reason_code == "stock-inert-preprocess-identical"
    assert supply.evidence["comparison"] == "stock-inert-identity"
    if comparison != supply.evidence["comparison"]:
        evidence = dict(supply.evidence)
        evidence["comparison"] = comparison
        supply = gate._arm_record(
            arm="supply-effectuation",
            terminal_status=supply.terminal_status,
            reason_code=supply.reason_code,
            request=request,
            request_digest=supply.request_digest,
            evidence=evidence,
        )
    meaning = gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=cxx,
    )
    admission = gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    return supply, meaning, admission


def _root_location_only_condition_gate_family(
    tmp_path: Path,
) -> tuple[Any, Any, Any]:
    gate = probe.condition_meaning_gate
    source = (
        _REPO
        / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    )
    root = tmp_path / "condition-gate-root-location-only"
    shutil.copytree(source, root)
    for header in (
        root / "include/backoff.hh",
        root / "stock/include/backoff.hh",
    ):
        header.write_text(
            header.read_text(encoding="utf-8")
            + '    static constexpr const char *condition_gate_file = __FILE__;\n',
            encoding="utf-8",
        )
    request = gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    captured = gate.capture_define_inputs(
        root, stock_root=root / "stock", configure_args=(),
    )
    cxx = shutil.which("c++")
    cmake = shutil.which("cmake")
    assert cxx is not None and cmake is not None
    supply = gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake=cmake,
    )
    assert supply.terminal_status == "green"
    assert supply.reason_code == "stock-inert-preprocess-root-location-only"
    assert supply.evidence["comparison"] == "stock-inert-root-location-only"
    meaning = gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=cxx,
    )
    admission = gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    assert admission.admitted is True
    return supply, meaning, admission


@functools.lru_cache(maxsize=None)
def _requested_default_condition_gate_family() -> tuple[Any, Any, Any]:
    gate = probe.condition_meaning_gate
    source = (
        _REPO
        / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    )
    request = gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=5,
        default_value=-1,
        stock_comparison=False,
    )
    captured = gate.capture_define_inputs(source, configure_args=())
    cxx = shutil.which("c++")
    cmake = shutil.which("cmake")
    assert cxx is not None and cmake is not None
    supply = gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake=cmake,
    )
    assert supply.terminal_status == "green"
    assert supply.reason_code == "requested-default-preprocess-different"
    assert supply.evidence["comparison"] == "requested-default-difference"
    meaning = gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=cxx,
    )
    admission = gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    assert admission.admitted is True
    return supply, meaning, admission


def _condition_gate_receipts(
    comparison: str = "stock-inert-identity",
    *,
    family: tuple[Any, Any, Any] | None = None,
) -> list[dict[str, Any]]:
    if family is None:
        family = _condition_gate_family(comparison)
    supply, meaning, admission = family
    return [
        {
            "arm": supply.arm,
            "record_digest": supply.record_digest,
            "terminal_status": supply.terminal_status,
            "reason_code": supply.reason_code,
            "comparison": supply.evidence.get("comparison"),
        },
        {
            "arm": meaning.arm,
            "record_digest": meaning.record_digest,
            "terminal_status": meaning.terminal_status,
            "reason_code": meaning.reason_code,
        },
        {
            "kind": "family-admission",
            "admission_digest": admission.admission_digest,
            "use_class": admission.use_class,
            "admitted": admission.admitted,
        },
    ]


def _good_s6() -> dict[str, Any]:
    return {
        "attempted": True, "source_identity_valid": True,
        "outside_success": True, "inside_success": True, "success": True,
        "trace_disabled": True, "failure_stage": None,
        "toolchain": {"host_valid": True, "sandbox_valid": True},
        "condition_gates": _condition_gate_receipts(),
        "_condition_gate_family": _condition_gate_family(
            "stock-inert-identity"
        ),
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
    for missing in ("condition_gates", "_condition_gate_family"):
        observation = _good_s6()
        observation.pop(missing)
        verdict = probe.verdict_s6(observation)
        assert verdict.verdict == "inconclusive"
        assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


def test_s6_unissued_condition_records_cannot_replace_live_family() -> None:
    observation = _good_s6()
    supply, meaning, admission = _condition_gate_family(
        "stock-inert-identity"
    )
    unissued_supply = dataclasses.replace(supply)
    unissued_meaning = dataclasses.replace(meaning)
    assert unissued_supply.canonical_json() == supply.canonical_json()
    assert unissued_meaning.canonical_json() == meaning.canonical_json()
    assert unissued_supply._issuer_capability is None
    assert unissued_meaning._issuer_capability is None
    observation["_condition_gate_family"] = (
        unissued_supply,
        unissued_meaning,
        admission,
    )
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


def test_s6_receipt_summary_must_match_live_condition_conclusions() -> None:
    observation = _good_s6()
    observation["condition_gates"][0]["terminal_status"] = "red"
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


@pytest.mark.parametrize("pair_name", ("identity", "root-location-only"))
def test_s6_accepts_each_exact_inert_condition_gate_pair(
    pair_name: str,
    tmp_path: Path,
) -> None:
    if pair_name == "identity":
        family = _condition_gate_family("stock-inert-identity")
    else:
        family = _root_location_only_condition_gate_family(tmp_path)
    observation = _good_s6()
    observation["_condition_gate_family"] = family
    observation["condition_gates"] = _condition_gate_receipts(family=family)
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "go"
    assert verdict.reason_codes == ("S6_SANDBOX_BUILD_SUCCEEDED",)


@pytest.mark.parametrize(
    ("reason_family_name", "comparison_family_name"),
    (
        pytest.param(
            "identity",
            "root-location-only",
            id="identical_reason__root_location_comparison",
        ),
        pytest.param(
            "root-location-only",
            "identity",
            id="root_location_reason__identity_comparison",
        ),
    ),
)
def test_s6_rejects_crossed_inert_condition_gate_pair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    reason_family_name: str,
    comparison_family_name: str,
) -> None:
    gate = probe.condition_meaning_gate
    families = {
        "identity": _condition_gate_family("stock-inert-identity"),
        "root-location-only": _root_location_only_condition_gate_family(tmp_path),
    }
    reason_supply, meaning, admission = families[reason_family_name]
    comparison_supply = families[comparison_family_name][0]
    evidence = dict(reason_supply.evidence)
    evidence["comparison"] = comparison_supply.evidence["comparison"]
    request = gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    crossed_supply = gate._arm_record(
        arm=reason_supply.arm,
        terminal_status=reason_supply.terminal_status,
        reason_code=reason_supply.reason_code,
        request=request,
        request_digest=reason_supply.request_digest,
        evidence=evidence,
    )
    crossed_family = (crossed_supply, meaning, admission)
    monkeypatch.setattr(
        gate,
        "require_condition_gate_family",
        lambda _supply, _meaning, *, use_class: admission,
    )
    observation = _good_s6()
    observation["_condition_gate_family"] = crossed_family
    observation["condition_gates"] = _condition_gate_receipts(
        family=crossed_family,
    )
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


def test_s6_rejects_requested_default_preprocess_difference() -> None:
    family = _requested_default_condition_gate_family()
    observation = _good_s6()
    observation["_condition_gate_family"] = family
    observation["condition_gates"] = _condition_gate_receipts(family=family)
    verdict = probe.verdict_s6(observation)
    assert verdict.verdict == "inconclusive"
    assert verdict.reason_codes == ("S6_CONDITION_GATE_UNPROVEN",)


def test_s6_rejects_legacy_stock_identity_vocabulary() -> None:
    with pytest.raises(
        probe.condition_meaning_gate.ConditionMeaningGateError,
    ) as raised:
        _condition_gate_family("stock-identity")
    assert raised.value.reason_code == "admission-contract-invalid"
    assert raised.value.detail == (
        "green supply reason and comparison vocabulary disagree"
    )


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
    assert "_condition_gate_family" not in receipt["observations"]["S6"]
    assert receipt["observations"]["S6"]["condition_gates"] == (
        _condition_gate_receipts()
    )
    assert all(
        "evidence" not in item
        for item in receipt["observations"]["S6"]["condition_gates"]
    )
    assert (
        "condition gate receipt entries preserve live-validated digests and "
        "conclusions, not a reusable production-issuer capability"
        in receipt["limitations"]
    )
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


def _prepare_execution_binding_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, Path]:
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "GIT_TEMPLATE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_DEFAULT_HASH", "sha1")

    git = shutil.which("git")
    assert git is not None
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir()
    empty_template = tmp_path / "empty-git-template"
    empty_template.mkdir()
    bound_bytes = {
        "patches/silo-backoff-fixed.patch": b"fixture patch input\n",
        "orchestrator/campaign/patchharness.py": b"# fixture patch harness\n",
        "orchestrator/campaign/condition_meaning_gate.py": b"# fixture condition gate\n",
        "tools/pegasus/probes/t316_sandbox_backend_probe.py": b"print('fixture probe')\n",
        "tools/pegasus/probes/t316_sandbox_backend_probe.pbs": b"#!/bin/bash\nexit 0\n",
        "tools/pegasus/policies/t316_sandbox_backend_v1.json": b'{"fixture":"sandbox-policy"}\n',
        "tools/pegasus/policy.json": b'{"fixture":"shared-policy"}\n',
    }
    assert len(set(bound_bytes.values())) == len(bound_bytes)
    for relative, contents in bound_bytes.items():
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    repo_py = repo_root / "tools/pegasus/probes/t316_sandbox_backend_probe.py"
    repo_pbs = repo_root / "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"
    assert repo_py.read_bytes() != repo_pbs.read_bytes()

    subprocess.run(
        [git, "-C", str(repo_root), "init", f"--template={empty_template}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    subprocess.run(
        [git, "-C", str(repo_root), "add", "--all"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    subprocess.run(
        [
            git,
            "-C",
            str(repo_root),
            "-c",
            "user.name=T316 Fixture",
            "-c",
            "user.email=t316-fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "fixture",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    head = subprocess.run(
        [git, "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.strip()
    status = subprocess.run(
        [
            git,
            "-C",
            str(repo_root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert status.stdout == ""

    runtime_pbs = (tmp_path / "runtime-spool.pbs").resolve()
    runtime_pbs.write_bytes(repo_pbs.read_bytes())
    nodefile = (tmp_path / "PBS_NODEFILE").resolve()
    nodefile.write_text("compute-test.example\n", encoding="utf-8")
    assert not runtime_pbs.is_relative_to(repo_root)
    assert not nodefile.is_relative_to(repo_root)
    monkeypatch.setattr(
        probe.socket, "gethostname", lambda: "compute-test.example"
    )
    monkeypatch.setenv("PBS_JOBID", "12345.test")
    monkeypatch.setenv("IZANAGI_T316_EXPECTED_COMMIT", head)
    monkeypatch.setenv("IZANAGI_T316_EXPECTED_WORKTREE_ROOT", str(repo_root))
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    monkeypatch.setenv("IZANAGI_T316_RUNTIME_PBS", str(runtime_pbs))
    return repo_root, repo_py, repo_pbs, runtime_pbs


@pytest.mark.parametrize("state", ["unstaged", "staged"])
@pytest.mark.parametrize(
    "relative",
    [
        pytest.param("patches/silo-backoff-fixed.patch", id="patch"),
        pytest.param("orchestrator/campaign/patchharness.py", id="patchharness"),
        pytest.param("orchestrator/campaign/condition_meaning_gate.py", id="condition"),
        pytest.param("tools/pegasus/probes/t316_sandbox_backend_probe.py", id="probe"),
        pytest.param("tools/pegasus/probes/t316_sandbox_backend_probe.pbs", id="pbs"),
        pytest.param("tools/pegasus/policies/t316_sandbox_backend_v1.json", id="sandbox-policy"),
        pytest.param("tools/pegasus/policy.json", id="shared-policy"),
        pytest.param("unrelated.txt", id="unrelated"),
        pytest.param(None, id="clean"),
    ],
)
def test_execution_binding_shell_dirty_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    relative: str | None, state: str,
) -> None:
    repo_root, *_ = _prepare_execution_binding_repo(tmp_path, monkeypatch)
    if relative is not None:
        path = repo_root / relative
        with path.open("ab") as handle:
            handle.write(b"# dirty\n")
        if state == "staged":
            subprocess.run(
                ["git", "-C", str(repo_root), "add", "--", relative],
                check=True, capture_output=True, text=True, timeout=60,
            )
    source = (_REPO / "tools/pegasus/probes/t316_sandbox_backend_probe.pbs").read_text(
        encoding="utf-8"
    )
    start = "BOUND_PATHS=(\n"
    end = '[[ -z $DIRTY ]] || exit 3\n'
    assert source.count(start) == source.count(end) == 1
    begin = source.index(start)
    finish = source.index(end, begin) + len(end)
    # 実 PBS の検査を実 Git で実行し、下流の blob/runtime 検査による mask を避ける。
    result = subprocess.run(
        ["bash", "-c", 'set -euo pipefail\nREPO=$1\n' + source[begin:finish]
         + '\nprintf "T2543_AFTER_DIRTY\\n"\n', "t2543-dirty-gate", str(repo_root)],
        capture_output=True, text=True, timeout=60,
    )
    rejected = relative is not None and relative != "unrelated.txt"
    assert (result.returncode, result.stdout) == (
        (3, "") if rejected else (0, "T2543_AFTER_DIRTY\n")
    ), result.stderr


def test_execution_binding_shell_checks_precede_probe() -> None:
    source = (_REPO / "tools/pegasus/probes/t316_sandbox_backend_probe.pbs").read_text(
        encoding="utf-8"
    )
    anchors = (
        "BOUND_PATHS=(\n",
        'DIRTY=$(timeout --foreground --signal=TERM --kill-after=5 10s',
        '[[ -z $DIRTY ]] || exit 3\n',
        'RUNTIME_PBS=$(timeout --foreground --signal=TERM --kill-after=5 5s',
        'for relative in "${BOUND_PATHS[@]}"; do\n',
        '  [[ $LIVE_SHA == "$COMMITTED_SHA" ]] || exit 3\n',
        '[[ $RUNTIME_PBS_SHA == "$COMMITTED_PBS_SHA" ]] || exit 3\n',
        '  "$REPO/tools/pegasus/probes/t316_sandbox_backend_probe.py"',
    )
    assert all(source.count(anchor) == 1 for anchor in anchors)
    positions = [source.index(anchor) for anchor in anchors]
    assert positions == sorted(positions)


def test_execution_binding_binds_runtime_spool_to_pbs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, _repo_py, repo_pbs, _runtime_pbs = (
        _prepare_execution_binding_repo(tmp_path, monkeypatch)
    )
    binding = probe._execution_binding(repo_root)
    assert isinstance(binding, dict)
    pbs_sha256 = probe._sha256_file(repo_pbs)
    assert binding["runtime_sha256"]["runtime_pbs_spool"] == pbs_sha256
    assert (
        binding["runtime_sha256"][
            "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"
        ]
        == pbs_sha256
    )


def test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, repo_py, _repo_pbs, runtime_pbs = (
        _prepare_execution_binding_repo(tmp_path, monkeypatch)
    )
    runtime_pbs.write_bytes(repo_py.read_bytes())
    with pytest.raises(
        ValueError,
        match="^runtime PBS bytes differ from worktree PBS bytes$",
    ):
        probe._execution_binding(repo_root)


@pytest.fixture
def s6_bindable_root():
    # SandboxProfile masks /tmp before mounting source/cache/scratch. All live
    # inputs need mountable ancestors, not just the requested checkout. Keep
    # them in a disposable sibling layout on the workspace filesystem; TMPDIR
    # still names host-tmp, outside the writable scratch bind.
    with tempfile.TemporaryDirectory(prefix=".t316-live-", dir=_REPO) as directory:
        root = Path(directory).resolve(strict=True)
        assert not root.is_relative_to(Path("/tmp"))
        yield root


def _s6_fixture_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=T2607 Fixture",
         "-c", "user.email=t2607@example.invalid", "-c", "commit.gpgsign=false",
         *args], check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def _s6_live_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str):
    """Real tiny Git/CMake inputs; production harness and evaluators are intact.

    The fixture patch occupies the production relative path. observe_s6 itself
    must check out, apply, capture, evaluate and build it. This tests wiring;
    the full CCBench workload still requires the parent's compute acceptance.
    """
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_TEMPLATE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_DEFAULT_HASH", "sha1")
    repo = tmp_path / "repo"
    source = repo / "external/ccbench"
    fixture = _REPO / "orchestrator/tests/fixtures/condition_meaning_gate/supplied"
    shutil.copytree(fixture / "stock", source)
    options = source / "cmake/Options.cmake"
    options.parent.mkdir()
    options.write_text(
        "function(ccbench_universal_definitions out_var)\n"
        '  set(${out_var} "" PARENT_SCOPE)\nendfunction()\n', encoding="utf-8",
    )
    # Frozen names independent of the probe list. Reintroduced unused variables
    # produce real CMake stderr in the actual condition gate.
    cmake_text = '''cmake_minimum_required(VERSION 3.16)
project(t316_wiring_fixture LANGUAGES C CXX)
include(cmake/Options.cmake)
ccbench_universal_definitions(defines)
foreach(variable ENABLE_SANITIZER CCBENCH_TRACE CCBENCH_BACK_OFF
        CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION CCBENCH_NO_WAIT_OF_TICTOC
        CCBENCH_WAL CCBENCH_CCACHE CCBENCH_ADD_ANALYSIS CMAKE_PREFIX_PATH
        FETCHCONTENT_SOURCE_DIR_MASSTREE FETCHCONTENT_SOURCE_DIR_MIMALLOC
        FETCHCONTENT_SOURCE_DIR_GOOGLETEST)
  message(STATUS "${variable}=${${variable}}")
endforeach()
add_executable(ycsb_silo.exe cc/silo/transaction.cc)
target_compile_definitions(ycsb_silo.exe PRIVATE ${defines})
set_target_properties(ycsb_silo.exe PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/cc/silo")
'''
    if failure == "gate":
        cmake_text += 'message(FATAL_ERROR "T2607_GATE_FAILURE")\n'
    elif failure == "outside":
        cmake_text += '''if(CMAKE_BINARY_DIR MATCHES "s6-outside/ccbench-build")
  add_custom_command(TARGET ycsb_silo.exe PRE_LINK
    COMMAND "${CMAKE_COMMAND}" -E false)
endif()
'''
    (source / "CMakeLists.txt").write_text(cmake_text, encoding="utf-8")
    _s6_fixture_git(source, "init")
    _s6_fixture_git(source, "add", ".")
    _s6_fixture_git(source, "commit", "-m", "stock")
    pin = _s6_fixture_git(source, "rev-parse", "HEAD")
    shutil.copyfile(fixture / "cmake/Options.cmake", options)
    shutil.copyfile(fixture / "include/backoff.hh", source / "include/backoff.hh")
    patch = repo / "patches/silo-backoff-fixed.patch"
    patch.parent.mkdir()
    patch.write_text(_s6_fixture_git(source, "diff") + "\n", encoding="utf-8")
    _s6_fixture_git(source, "restore", ".")
    _s6_fixture_git(source, "commit", "--allow-empty", "-m", "wrong base")
    wrong_pin = _s6_fixture_git(source, "rev-parse", "HEAD")
    _s6_fixture_git(source, "checkout", "--detach", pin)
    dependencies = tmp_path / "dependencies"
    pins = {}
    for name in ("gflags", "glog"):
        dependency = dependencies / name
        dependency.mkdir(parents=True)
        (dependency / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.16)\n'
            'project(t316_dependency_fixture LANGUAGES NONE)\n'
            'install(FILES CMakeLists.txt DESTINATION share)\n', encoding="utf-8",
        )
        _s6_fixture_git(dependency, "init")
        _s6_fixture_git(dependency, "add", ".")
        _s6_fixture_git(dependency, "commit", "-m", "dependency")
        pins[name] = _s6_fixture_git(dependency, "rev-parse", "HEAD")
    cache = tmp_path / "cache"
    cache.mkdir()
    shared = repo / "tools/pegasus/policy.json"
    shared.parent.mkdir(parents=True)
    shared.write_text(json.dumps({"silo_ladder_rung1": {
        "dependency_pins": pins, "third_party_sources": [],
    }}), encoding="utf-8")
    _s6_fixture_git(repo, "init")
    _s6_fixture_git(repo, "add", ".")
    _s6_fixture_git(repo, "commit", "-m", "observer fixture with gitlink")
    host_tmp = tmp_path / "host-tmp"
    host_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(host_tmp))
    monkeypatch.setenv("IZANAGI_PEGASUS_THIRDPARTY_CACHE", str(cache))
    monkeypatch.setenv("IZANAGI_T139_DEPENDENCY_SOURCE_ROOT", str(dependencies))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    for name in ("home", "tmp", "empty-tmp", "python-shim"):
        (scratch / name).mkdir()
    (scratch / "python-shim/python3").symlink_to(Path(sys.executable).resolve())
    bwrap = shutil.which("bwrap")
    assert bwrap is not None, "live S6 wiring test requires bubblewrap"
    profile = probe.SandboxProfile(bwrap, repo, scratch, (dependencies, cache))
    policy = {"stage_budgets_s": {
        "s6_minimum_remaining_s": 0, "ccbench_build_cap_s": 120,
    }}
    return repo, source, scratch, profile, policy, pin, wrong_pin


def _observe_s6_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure="", *, tmpdir_mode=None,
):
    repo, stock, scratch, profile, policy, pin, wrong_pin = _s6_live_fixture(
        tmp_path, monkeypatch, failure,
    )
    if tmpdir_mode == "unset":
        monkeypatch.delenv("TMPDIR", raising=False)
    elif tmpdir_mode == "/tmp":
        monkeypatch.setenv("TMPDIR", "/tmp")
    events = []
    requested_roots = []
    gate = probe.condition_meaning_gate
    harness = probe.patchharness
    watched = {
        harness.apply_patch.__code__: "apply",
        harness.revert_worktree.__code__: "revert",
        probe._git_source_identity.__code__: "identity",
        probe._execute_ccbench_build.__code__: "build",
        gate.capture_define_inputs.__code__: "capture",
        probe._require_condition_gate.__code__: "gate",
        probe._run_command.__code__: "command",
    }

    def observe(frame, event, arg):
        if (event == "return" and frame.f_code == probe._git_source_identity.__code__
                and failure == "wrong-head-restored"
                and Path(frame.f_locals["path"]) in requested_roots):
            # Preserve the real wrong-HEAD observation, then remove the later
            # harness rejection as a competing reason. Neither checker is
            # replaced: applied() can proceed if the probe ignores this record.
            path = Path(frame.f_locals["path"])
            assert arg["valid"] is False
            assert arg["observed_head"] == wrong_pin
            _s6_fixture_git(path, "checkout", "--detach", pin)
            harness.assert_pinned_clean(str(path), pin)
            events.append(("restored-pinned-clean", path))
            return
        if event != "call" or frame.f_code not in watched:
            return
        kind = watched[frame.f_code]
        values = frame.f_locals
        if kind == "identity":
            path = Path(values["path"])
            if path != stock and path.name == "wt":
                requested_roots.append(path)
                assert values["expected_head"] == pin
                assert "BACKOFF_FIXED" not in (path / "include/backoff.hh").read_text()
                if failure in {"wrong-head", "wrong-head-restored"}:
                    _s6_fixture_git(path, "checkout", "--detach", wrong_pin)
                elif failure == "dirty":
                    (path / "untracked-base-witness").write_text("dirty\n")
            events.append((kind, path))
        elif kind in {"apply", "revert"}:
            if kind == "apply":
                # Fail at the first forbidden side effect, before a later
                # gate/build can mask M6. Real applied() has already passed
                # its pinned-clean check when it calls apply_patch().
                assert failure != "wrong-head-restored", (
                    "probe accepted the observed wrong HEAD; real harness accepted the restored base"
                )
                assert Path(values["patch_path"]) == repo / "patches/silo-backoff-fixed.patch"
            events.append((kind, Path(values["sub"])))
        elif kind == "build":
            events.append((kind, Path(values["source"]), values["inside"],
                           Path(values["stock_root"]), values["profile"]))
        elif kind in {"capture", "gate"}:
            key = "source_root" if kind == "capture" else "source"
            assert "BACKOFF_FIXED" in (Path(values[key]) / "include/backoff.hh").read_text()
            assert "BACKOFF_FIXED" not in (
                Path(values["stock_root"]) / "include/backoff.hh"
            ).read_text()
            events.append((kind, Path(values[key]), Path(values["stock_root"]),
                           tuple(values["configure_args"])))
        elif kind == "command":
            events.append((kind, tuple(values["argv"])))

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        if failure == "gate":
            with pytest.raises(RuntimeError, match="condition gate rejected"):
                probe.observe_s6(profile, repo, scratch, policy,
                                 time.monotonic_ns() + 600_000_000_000)
            result = None
        else:
            result = probe.observe_s6(profile, repo, scratch, policy,
                                      time.monotonic_ns() + 600_000_000_000)
    finally:
        sys.setprofile(previous)
    assert len(requested_roots) == 1
    requested = requested_roots[0]
    assert not requested.exists()
    assert _s6_fixture_git(stock, "status", "--porcelain", "--untracked-files=all") == ""
    assert str(requested) not in _s6_fixture_git(stock, "worktree", "list", "--porcelain")
    return result, events, requested, stock, scratch


def test_s6_live_requested_gate_and_both_build_roots_match(s6_bindable_root, monkeypatch):
    result, events, requested, stock, scratch = _observe_s6_wiring(s6_bindable_root, monkeypatch)
    assert result["outside_success"] is True, result
    assert result["inside_success"] is True, json.dumps(result["inside_build"], indent=2)
    assert result["trace_disabled"] is True
    builds = [event for event in events if event[0] == "build"]
    assert [(event[1], event[2], event[3]) for event in builds] == [
        (requested, False, stock), (requested, True, stock),
    ]
    captures = [event for event in events if event[0] == "capture"]
    assert [(event[1], event[2]) for event in captures] == [(requested, stock)] * 2
    configure_commands = []
    for event in events:
        if event[0] != "command":
            continue
        argv = event[1]
        if "-S" in argv and "-B" in argv and "-DCCBENCH_TRACE=0" in argv:
            configure_commands.append(argv)
    assert len(configure_commands) == 2
    assert [Path(argv[argv.index("-S") + 1]) for argv in configure_commands] == [requested] * 2
    assert [event for event in events if event[0] in {"apply", "revert"}] == [
        ("apply", requested), ("revert", requested),
    ]
    kinds = [event[0] for event in events]
    apply_index, revert_index = kinds.index("apply"), kinds.index("revert")
    assert all(apply_index < index < revert_index for index, kind in enumerate(kinds)
               if kind in {"build", "gate", "capture"})
    assert events.index(("identity", requested)) < apply_index
    assert not requested.is_relative_to(scratch)
    for build in builds:
        assert requested in build[4].readonly_roots
        argv = build[4].argv(["true"], build=True)
        assert argv is not None
        mount = ["--ro-bind", str(requested), str(requested)]
        assert any(argv[index:index + 3] == mount for index in range(len(argv) - 2))
    assert result["source_identity_valid"] is True
    assert result["source_identities"]["ccbench_requested_base"]["valid"] is True
    assert result["source_identities"]["ccbench_requested_base"]["path"] == str(requested)
    assert result["condition_gates"] == result["outside_build"]["condition_gates"]


@pytest.mark.parametrize("failure", ["wrong-head", "dirty"])
def test_s6_requested_base_identity_rejects_real_wrong_head_and_dirty(
    s6_bindable_root, monkeypatch, failure,
):
    result, events, requested, stock, scratch = _observe_s6_wiring(
        s6_bindable_root, monkeypatch, failure,
    )
    assert result["failure_stage"] == "source-identity"
    assert result["source_identity_valid"] is False
    identity = result["source_identities"]["ccbench_requested_base"]
    assert identity["valid"] is False
    if failure == "wrong-head":
        assert identity["observed_head"] != identity["expected_head"]
        assert identity["clean_including_untracked"] is True
    else:
        assert identity["observed_head"] == identity["expected_head"]
        assert identity["clean_including_untracked"] is False
    assert not any(event[0] in {"apply", "build", "gate", "capture"} for event in events)


def test_s6_requested_wrong_head_rejected_without_harness_mask(s6_bindable_root, monkeypatch):
    result, events, requested, stock, scratch = _observe_s6_wiring(
        s6_bindable_root, monkeypatch, "wrong-head-restored",
    )
    assert ("restored-pinned-clean", requested) in events
    assert result["failure_stage"] == "source-identity"
    assert result["source_identity_valid"] is False
    identity = result["source_identities"]["ccbench_requested_base"]
    assert identity["valid"] is False
    assert identity["observed_head"] != identity["expected_head"]
    assert identity["clean_including_untracked"] is True
    assert not any(event[0] in {"apply", "build", "gate", "capture"} for event in events)


@pytest.mark.parametrize("failure", ["outside", "gate"])
def test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception(
    s6_bindable_root, monkeypatch, failure,
):
    result, events, requested, stock, scratch = _observe_s6_wiring(
        s6_bindable_root, monkeypatch, failure,
    )
    assert [event for event in events if event[0] in {"apply", "revert"}] == [
        ("apply", requested), ("revert", requested),
    ]
    builds = [event for event in events if event[0] == "build"]
    assert [(event[1], event[2]) for event in builds] == [(requested, False)]
    if failure == "outside":
        assert result["outside_build"]["failure_stage"] == "ccbench-build"
        assert result["inside_build"]["failure_stage"] == "outside-control"


def test_s6_shared_configure_excludes_named_unused_variables():
    source = inspect.getsource(probe._execute_ccbench_build)
    for name in ("RULE_LAUNCH_COMPILE", "IZANAGI_GFLAGS_SRC_HEAD", "IZANAGI_GLOG_SRC_HEAD"):
        assert name not in source
    assert '"-DCCBENCH_BACKOFF_FIXED=-1"' in source
    assert "shutil.copytree" not in source


def test_s6_requested_checkout_inside_scratch_is_rejected_and_removed(s6_bindable_root, monkeypatch):
    repo, stock, scratch, profile, policy, pin, wrong_pin = _s6_live_fixture(
        s6_bindable_root, monkeypatch, "",
    )
    monkeypatch.setenv("TMPDIR", str(scratch / "tmp"))
    with pytest.raises(RuntimeError, match="S6 requested source must be outside scratch"):
        probe.observe_s6(profile, repo, scratch, policy,
                         time.monotonic_ns() + 600_000_000_000)
    assert list((scratch / "tmp").iterdir()) == []
    assert not (scratch / "s6-outside").exists()
    assert _s6_fixture_git(stock, "status", "--porcelain", "--untracked-files=all") == ""
    assert _s6_fixture_git(stock, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_s6_patch_and_harness_are_bound_execution_inputs():
    assert "patches/silo-backoff-fixed.patch" in probe._BOUND_RELATIVE_PATHS
    assert "orchestrator/campaign/patchharness.py" in probe._BOUND_RELATIVE_PATHS


@pytest.mark.parametrize("tmpdir_mode", ["unset", "/tmp"])
def test_s6_requested_checkout_avoids_masked_tmp(s6_bindable_root, monkeypatch, tmpdir_mode):
    repo, stock, scratch, profile, policy, pin, wrong_pin = _s6_live_fixture(
        s6_bindable_root, monkeypatch, "",
    )
    if tmpdir_mode == "unset":
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", tmpdir_mode)
    original_tmpdir = os.environ.get("TMPDIR")
    observed = []

    def stop_after_observing_source(build_profile, source, *args, **kwargs):
        requested = source.resolve(strict=True)
        observed.append(requested)
        assert requested.parent.parent == scratch.parent
        assert not requested.is_relative_to(Path("/tmp"))
        assert not requested.is_relative_to(scratch)
        assert "BACKOFF_FIXED" in (requested / "include/backoff.hh").read_text()
        assert requested in build_profile.readonly_roots
        assert os.environ.get("TMPDIR") == original_tmpdir
        return {"success": False, "failure_stage": "placement-observed"}

    monkeypatch.setattr(probe, "_execute_ccbench_build", stop_after_observing_source)
    result = probe.observe_s6(profile, repo, scratch, policy,
                              time.monotonic_ns() + 600_000_000_000)
    assert result["outside_build"]["failure_stage"] == "placement-observed"
    assert len(observed) == 1
    assert not observed[0].parent.exists()
    assert os.environ.get("TMPDIR") == original_tmpdir
    assert _s6_fixture_git(stock, "worktree", "list", "--porcelain").count("worktree ") == 1


@pytest.mark.parametrize("tmpdir_mode", ["unset", "/tmp"])
def test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir(
    s6_bindable_root, monkeypatch, tmpdir_mode,
):
    result, events, requested, stock, scratch = _observe_s6_wiring(
        s6_bindable_root, monkeypatch, tmpdir_mode=tmpdir_mode,
    )
    assert requested.parent.parent == scratch.parent
    assert not requested.is_relative_to(Path("/tmp"))
    assert not requested.is_relative_to(scratch)
    assert result["outside_success"] is True, result
    assert result["inside_success"] is True, json.dumps(result["inside_build"], indent=2)
    assert result["success"] is True
    assert result["trace_disabled"] is True
    assert result["source_identity_valid"] is True
    assert [(event[1], event[2], event[3]) for event in events if event[0] == "build"] == [
        (requested, False, stock), (requested, True, stock),
    ]
    assert [event for event in events if event[0] in {"apply", "revert"}] == [
        ("apply", requested), ("revert", requested),
    ]


def _run() -> int:
    """pytest fixtures と parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
