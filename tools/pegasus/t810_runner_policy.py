"""The single executable/argv mediation point for T-810 measurements."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence

try:
    from tools.pegasus import t810_harness_schema as schema
except ModuleNotFoundError:  # standalone node package under python3.10 -I
    import t810_harness_schema as schema  # type: ignore[no-redef]


class T810RunnerPolicyError(RuntimeError):
    """A fail-closed runner policy or launch-authorization violation."""


Runner = Callable[..., subprocess.CompletedProcess[str]]
_POLICY_FIELDS = frozenset({
    "manifest_executable_realpath",
    "canonical_benchmark_argv",
    "preregistration_sha256",
    "admission_policy_sha256",
    "prereg_approval_id",
    "run_kind",
})
_FORBIDDEN_ENTRYPOINT_FRAGMENTS = (
    "calibration", "certify", "floor", "oracle", "trace",
)


def _policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(policy, Mapping) or set(policy) != _POLICY_FIELDS:
        raise T810RunnerPolicyError("runner policy has unknown or missing fields")
    result = dict(policy)
    for field in (
        "manifest_executable_realpath", "preregistration_sha256",
        "admission_policy_sha256", "prereg_approval_id", "run_kind",
    ):
        if not isinstance(result[field], str) or not result[field]:
            raise T810RunnerPolicyError(f"runner policy {field} is invalid")
    canonical = result["canonical_benchmark_argv"]
    if (not isinstance(canonical, list) or not canonical
            or any(not isinstance(item, str) or not item for item in canonical)):
        raise T810RunnerPolicyError("canonical_benchmark_argv is not a non-empty argv")
    if result["run_kind"] not in schema.RUN_KINDS:
        raise T810RunnerPolicyError("runner policy run_kind is invalid")
    for field in ("preregistration_sha256", "admission_policy_sha256"):
        value = result[field]
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise T810RunnerPolicyError(f"runner policy {field} is not SHA-256")
    return result


def _canonical_real_file(value: str, name: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise T810RunnerPolicyError(f"{name} must be absolute")
    try:
        if path.is_symlink() or not path.is_file() or not path.stat().st_mode & 0o111:
            raise T810RunnerPolicyError(f"{name} must be a non-symlink executable regular file")
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise T810RunnerPolicyError(f"cannot resolve {name}") from exc
    if resolved != path:
        raise T810RunnerPolicyError(f"{name} is not its own realpath")
    return resolved


def validate_measurement_argv(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
) -> tuple[str, ...]:
    """Return the one allowed exec argv; reject every non-exact spelling."""
    document = _policy(policy)
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence):
        raise T810RunnerPolicyError("measurement argv must be an argv sequence, not a shell string")
    if any(not isinstance(item, str) or not item for item in argv):
        raise T810RunnerPolicyError("measurement argv contains a non-string or empty item")
    executable_text = str(executable)
    actual = _canonical_real_file(executable_text, "measurement executable")
    bound = _canonical_real_file(
        document["manifest_executable_realpath"], "manifest executable",
    )
    if actual != bound or executable_text != document["manifest_executable_realpath"]:
        raise T810RunnerPolicyError("measurement executable differs from manifest realpath")
    if list(argv) != document["canonical_benchmark_argv"]:
        raise T810RunnerPolicyError("measurement argv differs from canonical preregistration argv")
    lowered = (actual.name + "\n" + "\n".join(argv)).lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_ENTRYPOINT_FRAGMENTS):
        raise T810RunnerPolicyError("certification, calibration, oracle, floor, or trace entrypoint denied")
    return (str(actual), *argv)


def validate_launch_authorization(
    policy: Mapping[str, Any], witness: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Validate a caller-supplied witness without creating or repairing one."""
    document = _policy(policy)
    if witness is None:
        raise T810RunnerPolicyError("launch authorization witness is required")
    try:
        authorized = schema.validate_launch_authorization(witness)
    except schema.T810SchemaError as exc:
        raise T810RunnerPolicyError(f"invalid launch authorization witness: {exc}") from exc
    comparisons = (
        ("preregistration_sha256", document["preregistration_sha256"]),
        ("policy_sha256", document["admission_policy_sha256"]),
        ("approval_id", document["prereg_approval_id"]),
    )
    for field, expected in comparisons:
        if authorized[field] != expected:
            raise T810RunnerPolicyError(f"launch authorization {field} mismatch")
    if document["run_kind"] not in authorized["run_kinds"]:
        raise T810RunnerPolicyError("launch authorization does not include run_kind")
    return authorized


def _subprocess_runner(
    argv: Sequence[str], *, cwd: str, env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), cwd=cwd, env=dict(env), check=False, shell=False,
        capture_output=True, text=True,
    )


def _run_allowed_measurement(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
    witness: Mapping[str, Any] | None, *, cwd: str | Path,
    runner: Runner,
) -> subprocess.CompletedProcess[str]:
    validate_launch_authorization(policy, witness)
    command = validate_measurement_argv(policy, executable, argv)
    workdir = Path(cwd)
    if not workdir.is_absolute() or workdir.is_symlink() or not workdir.is_dir():
        raise T810RunnerPolicyError("measurement cwd must be a real absolute directory")
    result = runner(command, cwd=str(workdir.resolve(strict=True)), env={})
    if not isinstance(result, subprocess.CompletedProcess):
        raise T810RunnerPolicyError("fixed runner returned an invalid result")
    return result


def run_allowed_measurement(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
    witness: Mapping[str, Any] | None, *, cwd: str | Path,
) -> subprocess.CompletedProcess[str]:
    """Authorize and run one measurement through the fixed subprocess adapter."""
    return _run_allowed_measurement(
        policy, executable, argv, witness, cwd=cwd, runner=_subprocess_runner,
    )
