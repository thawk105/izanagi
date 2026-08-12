from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign.t810_preregistration import (
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    ApprovalReceipt,
    load_t810_preregistration,
)
from tools.pegasus import t810_harness_schema as S
from tools.pegasus import t810_runner_policy as R


PREREG_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
APPROVAL_ID = "fixture-stage1-review-t810-v1"
ADMISSION_SHA256 = "2" * 64
CANONICAL_ARGV = [
    "-thread_num=48", "-ycsb_tuple_num=1000000", "-extime=3",
    "-clocks_per_us=2100", "-ycsb_rratio=50",
    "-ycsb_zipf_skew=0.9", "-ycsb_rmw=0",
]


def _preregistration():
    return load_t810_preregistration(
        PREREG_PATH,
        approval_receipt=ApprovalReceipt(
            artifact_sha256=PREREG_SHA256, approval_id=APPROVAL_ID,
            schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
        ),
    )


def _executable(tmp_path: Path, name: str = "CCBench-Silo") -> Path:
    path = tmp_path / name
    path.write_bytes(b"fixture executable")
    path.chmod(0o700)
    return path


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _policy(executable: Path) -> dict:
    return dict(R.build_runner_policy(
        _preregistration(), executable_sha256=_sha(executable),
    ))


def _witness() -> dict:
    return {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA,
        "approval_id": APPROVAL_ID,
        "preregistration_sha256": PREREG_SHA256,
        "policy_sha256": ADMISSION_SHA256,
        "run_kinds": ["liveness"], "issued_on": "2026-08-12",
        "nonce": "fixture-only-witness-not-issued-by-production",
    }


def _token():
    return S.verify_launch_authorization(
        _witness(), run_kind="liveness", preregistration_sha256=PREREG_SHA256,
        policy_sha256=ADMISSION_SHA256,
    )


def test_builder_projects_only_the_frozen_preregistration_contract(tmp_path):
    executable = _executable(tmp_path)
    assert _policy(executable) == {
        "schema_version": "t810-runner-policy/v1",
        "benchmark_executable_name": "CCBench-Silo",
        "executable_sha256": _sha(executable),
        "canonical_benchmark_argv": CANONICAL_ARGV,
        "preregistration_sha256": PREREG_SHA256,
        "prereg_approval_id": APPROVAL_ID,
    }
    with pytest.raises(R.T810RunnerPolicyError, match="verified preregistration"):
        R.build_runner_policy({}, executable_sha256=_sha(executable))


def test_exact_allowlist_has_one_positive_shape(tmp_path):
    executable = _executable(tmp_path)
    policy = _policy(executable)
    assert R.validate_measurement_argv(
        policy, executable, CANONICAL_ARGV,
    ) == (str(executable), *CANONICAL_ARGV)


@pytest.mark.parametrize("mutation", [
    lambda argv: argv + ["-extra=1"],
    lambda argv: argv[:-1],
    lambda argv: [argv[1], argv[0], *argv[2:]],
    lambda argv: [*argv[:-1], "-ycsb_rmw=1"],
    lambda argv: ["certify", *argv],
])
def test_prefix_suffix_reordering_and_options_are_denied(tmp_path, mutation):
    executable = _executable(tmp_path)
    with pytest.raises(R.T810RunnerPolicyError):
        R.validate_measurement_argv(_policy(executable), executable, mutation(CANONICAL_ARGV))


def test_shell_string_name_digest_and_symlink_mutations_are_denied(tmp_path):
    executable = _executable(tmp_path)
    other = _executable(tmp_path, "other-benchmark")
    link = tmp_path / "benchmark-link"
    link.symlink_to(executable)
    policy = _policy(executable)
    with pytest.raises(R.T810RunnerPolicyError, match="shell string"):
        R.validate_measurement_argv(policy, executable, " ".join(CANONICAL_ARGV))
    with pytest.raises(R.T810RunnerPolicyError, match="identity"):
        R.validate_measurement_argv(policy, other, CANONICAL_ARGV)
    executable.write_bytes(b"tampered executable")
    with pytest.raises(R.T810RunnerPolicyError, match="digest"):
        R.validate_measurement_argv(policy, executable, CANONICAL_ARGV)
    with pytest.raises(R.T810RunnerPolicyError, match="symlink"):
        R.validate_measurement_argv(policy, link, CANONICAL_ARGV)


def test_certification_family_entrypoint_is_denied_even_if_policy_is_self_consistent(tmp_path):
    executable = _executable(tmp_path, "trace-benchmark")
    policy = _policy(executable)
    policy["benchmark_executable_name"] = "trace-benchmark"
    with pytest.raises(R.T810RunnerPolicyError, match="entrypoint denied"):
        R.validate_measurement_argv(policy, executable, CANONICAL_ARGV)


def test_internal_fixture_runner_receives_token_exact_argv_and_empty_environment(tmp_path):
    executable = _executable(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    calls = []

    def fake_runner(token, argv, *, cwd, env):
        calls.append((token, tuple(argv), cwd, env))
        return subprocess.CompletedProcess(argv, 0, "123.5\n", "")

    token = _token()
    result = R._run_allowed_measurement(
        _policy(executable), executable, CANONICAL_ARGV, token,
        cwd=work, runner=fake_runner,
    )
    assert result.returncode == 0
    assert calls == [(token, (str(executable), *CANONICAL_ARGV), str(work), {})]


@pytest.mark.parametrize("invalid_token", [None, {}, _witness()])
def test_low_level_subprocess_adapter_rejects_non_token_before_effect(
    tmp_path, monkeypatch, invalid_token,
):
    called = False

    def bomb(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not be reached")

    monkeypatch.setattr(R.subprocess, "run", bomb)
    with pytest.raises(R.T810RunnerPolicyError, match="AuthorizationToken"):
        R._subprocess_runner(invalid_token, ["/bin/false"], cwd=str(tmp_path), env={})
    assert called is False


def test_public_effect_entry_denies_missing_token_before_subprocess(tmp_path, monkeypatch):
    executable = _executable(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    called = False

    def bomb(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not be reached")

    monkeypatch.setattr(R.subprocess, "run", bomb)
    with pytest.raises(R.T810RunnerPolicyError, match="AuthorizationToken"):
        R.run_allowed_measurement(
            _policy(executable), executable, CANONICAL_ARGV, None, cwd=work,
        )
    assert called is False


def test_runner_policy_rejects_unknown_and_missing_policy_fields(tmp_path):
    executable = _executable(tmp_path)
    for field, value in (("schema_version", None), ("unexpected", "value")):
        policy = _policy(executable)
        if value is None:
            policy.pop(field)
        else:
            policy[field] = value
        with pytest.raises(R.T810RunnerPolicyError, match="unknown or missing"):
            R.validate_measurement_argv(policy, executable, CANONICAL_ARGV)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
