from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess

import pytest

from tools.pegasus import t810_harness_schema as S
from tools.pegasus import t810_runner_policy as R


H1 = "1" * 64
H2 = "2" * 64


def _executable(tmp_path: Path, name: str = "CCBench-Silo") -> Path:
    path = tmp_path / name
    path.write_bytes(b"fixture executable")
    path.chmod(0o700)
    return path


def _policy(executable: Path) -> dict:
    return {
        "manifest_executable_realpath": str(executable),
        "canonical_benchmark_argv": [
            "-thread_num=48", "-ycsb_tuple_num=1000000", "-extime=3",
            "-clocks_per_us=2100", "-ycsb_rratio=50",
            "-ycsb_zipf_skew=0.9", "-ycsb_rmw=0",
        ],
        "preregistration_sha256": H1,
        "admission_policy_sha256": H2,
        "prereg_approval_id": "fixture-human-approval",
        "run_kind": "liveness",
    }


def _witness() -> dict:
    return {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA,
        "approval_id": "fixture-human-approval",
        "preregistration_sha256": H1, "policy_sha256": H2,
        "run_kinds": ["liveness"], "issued_on": "2026-08-12",
        "nonce": "fixture-only-witness-not-issued-by-production",
    }


def test_exact_allowlist_has_one_positive_shape(tmp_path):
    executable = _executable(tmp_path)
    policy = _policy(executable)
    assert R.validate_measurement_argv(
        policy, executable, policy["canonical_benchmark_argv"],
    ) == (str(executable), *policy["canonical_benchmark_argv"])


@pytest.mark.parametrize("mutation", [
    lambda argv: argv + ["-extra=1"],
    lambda argv: argv[:-1],
    lambda argv: [argv[1], argv[0], *argv[2:]],
    lambda argv: [*argv[:-1], "-ycsb_rmw=1"],
    lambda argv: ["certify", *argv],
])
def test_prefix_suffix_reordering_and_options_are_denied(tmp_path, mutation):
    executable = _executable(tmp_path)
    policy = _policy(executable)
    with pytest.raises(R.T810RunnerPolicyError):
        R.validate_measurement_argv(
            policy, executable, mutation(policy["canonical_benchmark_argv"]),
        )


def test_shell_string_different_executable_and_symlink_are_denied(tmp_path):
    executable = _executable(tmp_path)
    other = _executable(tmp_path, "other-benchmark")
    link = tmp_path / "benchmark-link"
    link.symlink_to(executable)
    policy = _policy(executable)
    with pytest.raises(R.T810RunnerPolicyError, match="shell string"):
        R.validate_measurement_argv(
            policy, executable, " ".join(policy["canonical_benchmark_argv"]),
        )
    with pytest.raises(R.T810RunnerPolicyError, match="manifest realpath"):
        R.validate_measurement_argv(policy, other, policy["canonical_benchmark_argv"])
    with pytest.raises(R.T810RunnerPolicyError, match="symlink"):
        R.validate_measurement_argv(policy, link, policy["canonical_benchmark_argv"])


@pytest.mark.parametrize("name", ["certify-t810", "calibration-runner", "trace-benchmark"])
def test_certification_family_entrypoints_are_denied_even_if_canonical(tmp_path, name):
    executable = _executable(tmp_path, name)
    policy = _policy(executable)
    with pytest.raises(R.T810RunnerPolicyError, match="entrypoint denied"):
        R.validate_measurement_argv(policy, executable, policy["canonical_benchmark_argv"])


def test_internal_fixture_runner_receives_exact_argv_and_empty_environment(tmp_path):
    executable = _executable(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    policy = _policy(executable)
    calls = []

    def fake_runner(argv, *, cwd, env):
        calls.append((tuple(argv), cwd, env))
        return subprocess.CompletedProcess(argv, 0, "123.5\n", "")

    result = R._run_allowed_measurement(
        policy, executable, policy["canonical_benchmark_argv"], _witness(),
        cwd=work, runner=fake_runner,
    )
    assert result.returncode == 0
    assert calls == [((str(executable), *policy["canonical_benchmark_argv"]), str(work), {})]


@pytest.mark.parametrize("change", [
    lambda witness: witness.pop("nonce"),
    lambda witness: witness.update(preregistration_sha256="3" * 64),
    lambda witness: witness.update(policy_sha256="3" * 64),
    lambda witness: witness.update(approval_id="some-other-approval"),
    lambda witness: witness.update(run_kinds=["main"]),
])
def test_invalid_launch_authorization_witness_is_denied(tmp_path, change):
    executable = _executable(tmp_path)
    policy = _policy(executable)
    witness = deepcopy(_witness())
    change(witness)
    with pytest.raises(R.T810RunnerPolicyError, match="authorization|witness"):
        R.validate_launch_authorization(policy, witness)


def test_public_effect_entry_denies_missing_witness_before_subprocess(tmp_path, monkeypatch):
    executable = _executable(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    called = False

    def bomb(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not be reached")

    monkeypatch.setattr(R.subprocess, "run", bomb)
    with pytest.raises(R.T810RunnerPolicyError, match="witness is required"):
        R.run_allowed_measurement(
            _policy(executable), executable,
            _policy(executable)["canonical_benchmark_argv"], None, cwd=work,
        )
    assert called is False


def test_runner_policy_rejects_unknown_and_missing_policy_fields(tmp_path):
    executable = _executable(tmp_path)
    for field, value in (("run_kind", None), ("unexpected", "value")):
        policy = _policy(executable)
        if value is None:
            policy.pop(field)
        else:
            policy[field] = value
        with pytest.raises(R.T810RunnerPolicyError, match="unknown or missing"):
            R.validate_measurement_argv(
                policy, executable, _policy(executable)["canonical_benchmark_argv"],
            )
