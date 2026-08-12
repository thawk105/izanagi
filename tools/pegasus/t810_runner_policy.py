"""The single executable/argv mediation point for T-810 measurements."""
from __future__ import annotations

import hashlib
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
RUNNER_POLICY_SCHEMA = "t810-runner-policy/v1"
_POLICY_FIELDS = frozenset({
    "schema_version",
    "benchmark_executable_name",
    "executable_sha256",
    "canonical_benchmark_argv",
    "preregistration_sha256",
    "prereg_approval_id",
})
_FORBIDDEN_ENTRYPOINT_FRAGMENTS = (
    "calibration", "certify", "floor", "oracle", "trace",
)


def _digest(value: Any, name: str) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)):
        raise T810RunnerPolicyError(f"{name} is not SHA-256")
    return value


def _policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(policy, Mapping) or set(policy) != _POLICY_FIELDS:
        raise T810RunnerPolicyError("runner policy has unknown or missing fields")
    result = dict(policy)
    if result["schema_version"] != RUNNER_POLICY_SCHEMA:
        raise T810RunnerPolicyError("runner policy schema literal mismatch")
    for field in ("benchmark_executable_name", "prereg_approval_id"):
        if (not isinstance(result[field], str) or not result[field]
                or Path(result[field]).name != result[field]):
            raise T810RunnerPolicyError(f"runner policy {field} is invalid")
    _digest(result["executable_sha256"], "runner policy executable_sha256")
    _digest(result["preregistration_sha256"], "runner policy preregistration_sha256")
    canonical = result["canonical_benchmark_argv"]
    if (not isinstance(canonical, list) or not canonical
            or any(not isinstance(item, str) or not item for item in canonical)):
        raise T810RunnerPolicyError("canonical_benchmark_argv is not a non-empty argv")
    return result


def build_runner_policy(preregistration: Any, *, executable_sha256: str) -> Mapping[str, Any]:
    """Project the sole runner policy from a loader-verified preregistration."""
    try:
        from orchestrator.campaign.t810_preregistration import VerifiedT810Preregistration
    except ModuleNotFoundError as exc:  # node packages validate, but never construct policy
        raise T810RunnerPolicyError("preregistration loader is unavailable") from exc
    if not isinstance(preregistration, VerifiedT810Preregistration):
        raise T810RunnerPolicyError("verified preregistration from loader is required")
    measurement = preregistration.projection["measurement"]
    document = {
        "schema_version": RUNNER_POLICY_SCHEMA,
        "benchmark_executable_name": measurement["binary"]["benchmark"],
        "executable_sha256": _digest(executable_sha256, "executable_sha256"),
        "canonical_benchmark_argv": list(measurement["canonical_benchmark_argv"]),
        "preregistration_sha256": preregistration.sha256,
        "prereg_approval_id": preregistration.approval_id,
    }
    return _policy(document)


def validate_runner_policy(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate an exact serialized runner-policy artifact."""
    return _policy(value)


def _canonical_real_file(value: str | Path, name: str) -> Path:
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise T810RunnerPolicyError("cannot hash measurement executable") from exc
    return digest.hexdigest()


def validate_measurement_argv(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
) -> tuple[str, ...]:
    """Return the one preregistered exec argv; reject every other spelling."""
    document = _policy(policy)
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence):
        raise T810RunnerPolicyError("measurement argv must be an argv sequence, not a shell string")
    if any(not isinstance(item, str) or not item for item in argv):
        raise T810RunnerPolicyError("measurement argv contains a non-string or empty item")
    actual = _canonical_real_file(executable, "measurement executable")
    if actual.name != document["benchmark_executable_name"]:
        raise T810RunnerPolicyError("measurement executable differs from preregistration identity")
    if _sha256_file(actual) != document["executable_sha256"]:
        raise T810RunnerPolicyError("measurement executable digest mismatch")
    if list(argv) != document["canonical_benchmark_argv"]:
        raise T810RunnerPolicyError("measurement argv differs from canonical preregistration argv")
    lowered = (actual.name + "\n" + "\n".join(argv)).lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_ENTRYPOINT_FRAGMENTS):
        raise T810RunnerPolicyError("certification, calibration, oracle, floor, or trace entrypoint denied")
    return (str(actual), *argv)


def _require_token(
    policy: Mapping[str, Any], token: Any,
) -> schema.AuthorizationToken:
    document = _policy(policy)
    if not isinstance(token, schema.AuthorizationToken):
        raise T810RunnerPolicyError("verified AuthorizationToken is required")
    if (token.preregistration_sha256 != document["preregistration_sha256"]
            or token.document["approval_id"] != document["prereg_approval_id"]):
        raise T810RunnerPolicyError("AuthorizationToken preregistration binding mismatch")
    return token


def _subprocess_runner(
    token: schema.AuthorizationToken, argv: Sequence[str], *, cwd: str,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    if not isinstance(token, schema.AuthorizationToken):
        raise T810RunnerPolicyError("verified AuthorizationToken is required")
    return subprocess.run(
        list(argv), cwd=cwd, env=dict(env), check=False, shell=False,
        capture_output=True, text=True,
    )


def _run_allowed_measurement(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
    token: schema.AuthorizationToken, *, cwd: str | Path, runner: Runner,
) -> subprocess.CompletedProcess[str]:
    verified = _require_token(policy, token)
    command = validate_measurement_argv(policy, executable, argv)
    workdir = Path(cwd)
    if not workdir.is_absolute() or workdir.is_symlink() or not workdir.is_dir():
        raise T810RunnerPolicyError("measurement cwd must be a real absolute directory")
    result = runner(verified, command, cwd=str(workdir.resolve(strict=True)), env={})
    if not isinstance(result, subprocess.CompletedProcess):
        raise T810RunnerPolicyError("fixed runner returned an invalid result")
    return result


def run_allowed_measurement(
    policy: Mapping[str, Any], executable: str | Path, argv: Sequence[str],
    token: schema.AuthorizationToken, *, cwd: str | Path,
) -> subprocess.CompletedProcess[str]:
    """Run one measurement through the token-gated subprocess adapter."""
    return _run_allowed_measurement(
        policy, executable, argv, token, cwd=cwd, runner=_subprocess_runner,
    )
