# -*- coding: utf-8 -*-
"""Real-process regression tests for the stage 8c CLI entrypoints.

These tests pin CLI/library transport equivalence, not decision semantics;
the existing predicate and invariant tests own semantic correctness.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import s8c_preregistration as P  # noqa: E402


_PREREG_PATH = _ROOT / P.CORE_MODULE_PATH
_GATE_PATH = _ROOT / "orchestrator/campaign/s8c_gate_report.py"
_TINY_REPO_FILES = (
    P.CORE_MODULE_PATH,
    P.EVALUATOR_MODULE_PATH,
    P.PROJECTION_MODULE_PATH,
    P.EVIDENCE_CONTRACT_PATH,
)
_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)
_ELEVEN_RESULT_EVALUATOR = b'''# -*- coding: utf-8 -*-
from pathlib import Path

from . import s8c_preregistration as core


class PredicateRegistry:
    def evaluate_all(self, commit: str, *, repo_root: Path):
        del commit, repo_root
        return tuple(
            core.PredicateResult(
                identifier,
                core.PredicateStatus.SATISFIED,
                "fixture",
                (),
            )
            for identifier in core.PREDICATE_IDS[:-1]
        )


_REGISTRY = PredicateRegistry()


def get_registry() -> PredicateRegistry:
    return _REGISTRY
'''
_RAISING_EVALUATOR = b'''# -*- coding: utf-8 -*-
from pathlib import Path


class PredicateRegistry:
    def evaluate_all(self, commit: str, *, repo_root: Path):
        del commit, repo_root
        raise RuntimeError("secret-detail")


_REGISTRY = PredicateRegistry()


def get_registry() -> PredicateRegistry:
    return _REGISTRY
'''
_VALUE_ERROR_RAISING_EVALUATOR = _RAISING_EVALUATOR.replace(
    b'raise RuntimeError("secret-detail")',
    b'raise ValueError("secret-detail")',
)
_RAISING_EVALUATORS = {
    "RuntimeError": _RAISING_EVALUATOR,
    "ValueError": _VALUE_ERROR_RAISING_EVALUATOR,
}
_NORMALIZER_DIAGNOSTIC_STDERR = (
    b'{"callsite":"_normalize_predicate_results",'
    b'"exception_type":"PreregistrationError",'
    b'"preregistration_reason":"predicate-result-type"}\n'
)
_EVALUATOR_DIAGNOSTIC_STDERR = (
    b'{"callsite":"default-registry.evaluate_all",'
    b'"exception_type":"RuntimeError",'
    b'"preregistration_reason":null}\n'
)
_VALUE_ERROR_EVALUATOR_DIAGNOSTIC_STDERR = (
    b'{"callsite":"default-registry.evaluate_all",'
    b'"exception_type":"ValueError",'
    b'"preregistration_reason":null}\n'
)


def _git(repo_root: Path, env: dict[str, str], *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return completed.stdout.strip()


@pytest.fixture(scope="module")
def closed_environment() -> dict[str, str]:
    env = {key: os.environ[key] for key in _ENV_ALLOWLIST if key in os.environ}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


@pytest.fixture(scope="module")
def tiny_repo(
    tmp_path_factory: pytest.TempPathFactory,
    closed_environment: dict[str, str],
) -> tuple[Path, str]:
    repo_root = tmp_path_factory.mktemp("s8c-cli-tiny-repo")
    for relative_path in _TINY_REPO_FILES:
        source = _ROOT / relative_path
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    _git(repo_root, closed_environment, "init", "-q")
    _git(repo_root, closed_environment, "add", "-A")
    _git(
        repo_root,
        closed_environment,
        "-c",
        "user.email=s8c-cli@example.invalid",
        "-c",
        "user.name=S8C CLI test",
        "commit",
        "-q",
        "-m",
        "s8c CLI fixture",
    )
    commit = _git(
        repo_root, closed_environment, "rev-parse", "--verify", "HEAD^{commit}"
    )

    (repo_root / "HEAD_ONLY.txt").write_text(
        "This file is unrelated to the stage 8c evaluation inputs.\n",
        encoding="utf-8",
    )
    _git(repo_root, closed_environment, "add", "-A")
    _git(
        repo_root,
        closed_environment,
        "-c",
        "user.email=s8c-cli@example.invalid",
        "-c",
        "user.name=S8C CLI test",
        "commit",
        "-q",
        "-m",
        "advance fixture HEAD",
    )
    head = _git(
        repo_root, closed_environment, "rev-parse", "--verify", "HEAD^{commit}"
    )
    assert head != commit
    return repo_root, commit


@pytest.fixture(scope="module")
def malformed_evaluator_repo(
    tmp_path_factory: pytest.TempPathFactory,
    closed_environment: dict[str, str],
) -> tuple[Path, str]:
    repo_root = tmp_path_factory.mktemp("s8c-cli-malformed-evaluator")
    for relative_path in (
        P.CORE_MODULE_PATH,
        P.PROJECTION_MODULE_PATH,
        P.EVIDENCE_CONTRACT_PATH,
    ):
        source = _ROOT / relative_path
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    evaluator_path = repo_root / P.EVALUATOR_MODULE_PATH
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_bytes(_ELEVEN_RESULT_EVALUATOR)

    _git(repo_root, closed_environment, "init", "-q")
    _git(repo_root, closed_environment, "add", "-A")
    _git(
        repo_root,
        closed_environment,
        "-c",
        "user.email=s8c-cli@example.invalid",
        "-c",
        "user.name=S8C CLI test",
        "commit",
        "-q",
        "-m",
        "malformed evaluator fixture",
    )
    commit = _git(
        repo_root, closed_environment, "rev-parse", "--verify", "HEAD^{commit}"
    )
    for relative_path in (
        P.CORE_MODULE_PATH,
        P.EVALUATOR_MODULE_PATH,
        P.PROJECTION_MODULE_PATH,
    ):
        blob = subprocess.run(
            ["git", "show", f"{commit}:{relative_path}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            env=closed_environment,
        ).stdout
        assert blob == (repo_root / relative_path).read_bytes()
    return repo_root, commit


@pytest.fixture(scope="module")
def raising_evaluator_repo(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    closed_environment: dict[str, str],
) -> tuple[Path, str]:
    exception_type = getattr(request, "param", "RuntimeError")
    evaluator_source = _RAISING_EVALUATORS[exception_type]
    repo_root = tmp_path_factory.mktemp("s8c-cli-raising-evaluator")
    for relative_path in (
        P.CORE_MODULE_PATH,
        P.PROJECTION_MODULE_PATH,
        P.EVIDENCE_CONTRACT_PATH,
    ):
        source = _ROOT / relative_path
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    evaluator_path = repo_root / P.EVALUATOR_MODULE_PATH
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_bytes(evaluator_source)

    _git(repo_root, closed_environment, "init", "-q")
    _git(repo_root, closed_environment, "add", "-A")
    _git(
        repo_root,
        closed_environment,
        "-c",
        "user.email=s8c-cli@example.invalid",
        "-c",
        "user.name=S8C CLI test",
        "commit",
        "-q",
        "-m",
        "raising evaluator fixture",
    )
    commit = _git(
        repo_root, closed_environment, "rev-parse", "--verify", "HEAD^{commit}"
    )
    for relative_path in (
        P.CORE_MODULE_PATH,
        P.EVALUATOR_MODULE_PATH,
        P.PROJECTION_MODULE_PATH,
    ):
        blob = subprocess.run(
            ["git", "show", f"{commit}:{relative_path}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            env=closed_environment,
        ).stdout
        assert blob == (repo_root / relative_path).read_bytes()
    return repo_root, commit


@pytest.fixture(scope="module")
def malformed_evaluator_oracle(
    malformed_evaluator_repo: tuple[Path, str],
    closed_environment: dict[str, str],
) -> dict[str, object]:
    repo_root, commit = malformed_evaluator_repo
    script = r'''
import json
import sys

from orchestrator.campaign import s8c_preregistration as P

commit = sys.argv[1]
plain = P.activation_report_at(".", commit)
diagnostic_report, diagnostics = P.activation_report_with_diagnostics_at(".", commit)

lines = [
    f"{'EFFECTIVE' if plain.effective else 'NOT_EFFECTIVE'} commit={plain.commit} freeze={plain.freeze_reason_code}",
    f"decider_version {plain.decider_version_reason_code}",
]
lines.extend(
    f"section5 {finding.status.value} {finding.name}: {finding.reason_code}"
    for finding in plain.section5_findings
)
lines.extend(
    f"{result.id} {result.status.value}: {result.reason_code}"
    for result in plain.predicates
)
payload = {
    "plain_report": P._jsonable(plain),
    "diagnostic_report": P._jsonable(diagnostic_report),
    "plain_digest": P._activation_report_digest(plain),
    "diagnostic_digest": P._activation_report_digest(diagnostic_report),
    "diagnostics": P._jsonable(diagnostics),
    "all_status_error_identity": all(
        result.status is P.PredicateStatus.ERROR for result in plain.predicates
    ),
    "all_evidence_empty_tuples": all(
        result.evidence == () for result in plain.predicates
    ),
    "json_stdout": json.dumps(
        P._jsonable(plain), ensure_ascii=False, sort_keys=True
    ) + "\n",
    "text_stdout": "\n".join(lines) + "\n",
}
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, commit],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=closed_environment,
    )
    assert completed.stderr == b""
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def raising_evaluator_oracle(
    raising_evaluator_repo: tuple[Path, str],
    closed_environment: dict[str, str],
) -> dict[str, object]:
    repo_root, commit = raising_evaluator_repo
    script = r'''
import json
import sys

from orchestrator.campaign import s8c_preregistration as P

commit = sys.argv[1]
report = P.activation_report_at(".", commit)
lines = [
    f"{'EFFECTIVE' if report.effective else 'NOT_EFFECTIVE'} commit={report.commit} freeze={report.freeze_reason_code}",
    f"decider_version {report.decider_version_reason_code}",
]
lines.extend(
    f"section5 {finding.status.value} {finding.name}: {finding.reason_code}"
    for finding in report.section5_findings
)
lines.extend(
    f"{result.id} {result.status.value}: {result.reason_code}"
    for result in report.predicates
)
payload = {
    "json_stdout": json.dumps(
        P._jsonable(report), ensure_ascii=False, sort_keys=True
    ) + "\n",
    "text_stdout": "\n".join(lines) + "\n",
}
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, commit],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=closed_environment,
    )
    assert completed.stderr == b""
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def oracle(
    tiny_repo: tuple[Path, str],
    closed_environment: dict[str, str],
) -> P.ActivationReport:
    """Evaluate once per worker: once serially, at most four times under xdist."""
    repo_root, commit = tiny_repo
    with mock.patch.dict(os.environ, closed_environment, clear=True):
        for relative_path in (
            P.CORE_MODULE_PATH,
            P.EVALUATOR_MODULE_PATH,
            P.PROJECTION_MODULE_PATH,
        ):
            assert P.read_blob_at(repo_root, commit, relative_path) == (
                _ROOT / relative_path
            ).read_bytes()

        report, diagnostics = P.activation_report_with_diagnostics_at(
            repo_root, commit
        )
        assert diagnostics == ()
        assert P.activation_report_at(repo_root, commit) == report
    reasons = tuple(item.reason_code for item in report.predicates)
    assert len(reasons) == 12
    assert len(set(reasons)) > 1
    assert not any(
        reason == "evaluator-exception"
        or reason.endswith("-blob-mismatch")
        or reason.endswith("-absent-at-commit")
        for reason in reasons
    )
    assert report.effective is False
    return report


@pytest.mark.parametrize(
    ("kind", "invocation"),
    [
        pytest.param("prereg", "path", id="prereg-path"),
        pytest.param("prereg", "module", id="prereg-module"),
        pytest.param("gate", "path", id="gate-path"),
        pytest.param("gate", "module", id="gate-module"),
    ],
)
def test_cli_entrypoint_matches_library_report(
    kind: str,
    invocation: str,
    tiny_repo: tuple[Path, str],
    oracle: P.ActivationReport,
    closed_environment: dict[str, str],
) -> None:
    repo_root, commit = tiny_repo
    if kind == "prereg":
        target = (
            [sys.executable, str(_PREREG_PATH)]
            if invocation == "path"
            else [
                sys.executable,
                "-m",
                "orchestrator.campaign.s8c_preregistration",
            ]
        )
        command = [
            *target,
            "check",
            "--json",
            "--repo-root",
            str(repo_root),
            "--commit",
            commit,
        ]
    else:
        target = (
            [sys.executable, str(_GATE_PATH)]
            if invocation == "path"
            else [
                sys.executable,
                "-m",
                "orchestrator.campaign.s8c_gate_report",
            ]
        )
        command = [
            *target,
            "--repo-root",
            str(repo_root),
            "--commit",
            commit,
        ]

    completed = subprocess.run(
        command,
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=closed_environment,
    )
    payload = json.loads(completed.stdout)
    expected_predicates = tuple(
        (item.id, item.status.value, item.reason_code)
        for item in oracle.predicates
    )

    if kind == "prereg":
        actual_commit = payload["commit"]
        actual_predicates = tuple(
            (item["id"], item["status"], item["reason_code"])
            for item in payload["predicates"]
        )
        actual_effective = payload["effective"]
    else:
        actual_commit = payload["source"]["commit"]
        actual_predicates = tuple(
            (item["id"], item["status"], item["reason_code"])
            for item in payload["predicates"]["results"]
        )
        actual_effective = payload["source"]["effective"]

    assert actual_commit == commit
    assert actual_predicates == expected_predicates
    assert actual_effective is oracle.effective
    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert completed.stderr == ""


def test_evaluator_exception_remains_fail_closed(
    malformed_evaluator_oracle: dict[str, object],
) -> None:
    plain = malformed_evaluator_oracle["plain_report"]
    diagnostic_report = malformed_evaluator_oracle["diagnostic_report"]
    assert isinstance(plain, dict)
    assert plain == diagnostic_report
    assert malformed_evaluator_oracle["plain_digest"] == (
        malformed_evaluator_oracle["diagnostic_digest"]
    )
    predicates = plain["predicates"]
    assert len(predicates) == 12
    assert malformed_evaluator_oracle["all_status_error_identity"] is True
    assert malformed_evaluator_oracle["all_evidence_empty_tuples"] is True
    assert all(item["reason_code"] == "evaluator-exception" for item in predicates)
    assert all(item["evidence"] == [] for item in predicates)
    assert plain["effective"] is False


def test_evaluator_exception_reason_names_real_normalizer_failure(
    malformed_evaluator_oracle: dict[str, object],
) -> None:
    assert malformed_evaluator_oracle["diagnostics"] == [
        {
            "callsite": "_normalize_predicate_results",
            "exception_type": "PreregistrationError",
            "preregistration_reason": "predicate-result-type",
        }
    ]


@pytest.mark.parametrize(
    "invocation",
    [pytest.param("path", id="path"), pytest.param("module", id="module")],
)
@pytest.mark.parametrize(
    "json_output",
    [pytest.param(False, id="text"), pytest.param(True, id="json")],
)
def test_evaluator_exception_cli_preserves_stdout_and_emits_one_diagnostic(
    invocation: str,
    json_output: bool,
    malformed_evaluator_repo: tuple[Path, str],
    malformed_evaluator_oracle: dict[str, object],
    closed_environment: dict[str, str],
) -> None:
    repo_root, commit = malformed_evaluator_repo
    target = (
        [sys.executable, str(repo_root / P.CORE_MODULE_PATH)]
        if invocation == "path"
        else [sys.executable, "-m", "orchestrator.campaign.s8c_preregistration"]
    )
    command = [
        *target,
        "check",
        "--repo-root",
        str(repo_root),
        "--commit",
        commit,
    ]
    if json_output:
        command.append("--json")
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        env=closed_environment,
    )
    expected_key = "json_stdout" if json_output else "text_stdout"
    expected_stdout = malformed_evaluator_oracle[expected_key]
    assert isinstance(expected_stdout, str)
    assert completed.stdout == expected_stdout.encode("utf-8")
    assert completed.returncode == 1
    assert completed.stderr == _NORMALIZER_DIAGNOSTIC_STDERR
    assert b"Traceback" not in completed.stderr
    assert str(repo_root).encode("utf-8") not in completed.stderr


@pytest.mark.parametrize(
    "invocation",
    [pytest.param("path", id="path"), pytest.param("module", id="module")],
)
@pytest.mark.parametrize(
    "json_output",
    [pytest.param(False, id="text"), pytest.param(True, id="json")],
)
@pytest.mark.parametrize(
    ("raising_evaluator_repo", "exception_type"),
    [
        pytest.param("RuntimeError", "RuntimeError", id="runtime-error"),
        pytest.param("ValueError", "ValueError", id="value-error"),
    ],
    indirect=["raising_evaluator_repo"],
)
def test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic(
    invocation: str,
    json_output: bool,
    raising_evaluator_repo: tuple[Path, str],
    exception_type: str,
    raising_evaluator_oracle: dict[str, object],
    closed_environment: dict[str, str],
) -> None:
    repo_root, commit = raising_evaluator_repo
    target = (
        [sys.executable, str(repo_root / P.CORE_MODULE_PATH)]
        if invocation == "path"
        else [sys.executable, "-m", "orchestrator.campaign.s8c_preregistration"]
    )
    command = [
        *target,
        "check",
        "--repo-root",
        str(repo_root),
        "--commit",
        commit,
    ]
    if json_output:
        command.append("--json")
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        env=closed_environment,
    )
    expected_key = "json_stdout" if json_output else "text_stdout"
    expected_stdout = raising_evaluator_oracle[expected_key]
    assert isinstance(expected_stdout, str)
    assert completed.stdout == expected_stdout.encode("utf-8")
    assert completed.returncode == 1
    if exception_type == "RuntimeError":
        assert completed.stderr == _EVALUATOR_DIAGNOSTIC_STDERR
    else:
        assert exception_type == "ValueError"
        assert completed.stderr == _VALUE_ERROR_EVALUATOR_DIAGNOSTIC_STDERR


def test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror(
    raising_evaluator_repo: tuple[Path, str],
    raising_evaluator_oracle: dict[str, object],
    closed_environment: dict[str, str],
    tmp_path: Path,
) -> None:
    repo_root, commit = raising_evaluator_repo
    return_value_path = tmp_path / "main-return-value"
    script = r'''
import sys
from pathlib import Path

from orchestrator.campaign import s8c_preregistration as P


class BrokenStderr:
    def write(self, value):
        del value
        raise OSError("diagnostic sink unavailable")

    def flush(self):
        pass


sys.stderr = BrokenStderr()
rc = P.main([
    "check", "--json", "--repo-root", ".", "--commit", sys.argv[1]
])
Path(sys.argv[2]).write_text(str(rc), encoding="ascii")
raise SystemExit(rc)
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, commit, str(return_value_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        env=closed_environment,
    )
    expected_stdout = raising_evaluator_oracle["json_stdout"]
    assert isinstance(expected_stdout, str)
    assert completed.stdout == expected_stdout.encode("utf-8")
    assert completed.returncode == 1
    assert completed.stderr == b""
    assert return_value_path.is_file()
    assert return_value_path.read_text(encoding="ascii") == "1"


def test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_value_error(
    raising_evaluator_repo: tuple[Path, str],
    raising_evaluator_oracle: dict[str, object],
    closed_environment: dict[str, str],
    tmp_path: Path,
) -> None:
    repo_root, commit = raising_evaluator_repo
    return_value_path = tmp_path / "main-return-value"
    script = r'''
import sys
from pathlib import Path

from orchestrator.campaign import s8c_preregistration as P


class BrokenStderr:
    def write(self, value):
        del value
        raise ValueError("diagnostic sink unavailable")

    def flush(self):
        pass


sys.stderr = BrokenStderr()
rc = P.main([
    "check", "--json", "--repo-root", ".", "--commit", sys.argv[1]
])
Path(sys.argv[2]).write_text(str(rc), encoding="ascii")
raise SystemExit(rc)
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, commit, str(return_value_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        env=closed_environment,
    )
    expected_stdout = raising_evaluator_oracle["json_stdout"]
    assert isinstance(expected_stdout, str)
    assert completed.stdout == expected_stdout.encode("utf-8")
    assert completed.returncode == 1
    assert completed.stderr == b""
    assert return_value_path.is_file()
    assert return_value_path.read_text(encoding="ascii") == "1"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
