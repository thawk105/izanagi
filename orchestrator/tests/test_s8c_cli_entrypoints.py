# -*- coding: utf-8 -*-
"""Real-process regression tests for the stage 8c CLI entrypoints."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture(scope="module")
def tiny_repo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    repo_root = tmp_path_factory.mktemp("s8c-cli-tiny-repo")
    for relative_path in _TINY_REPO_FILES:
        source = _ROOT / relative_path
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    _git(repo_root, "init", "-q")
    _git(repo_root, "add", "-A")
    _git(
        repo_root,
        "-c",
        "user.email=s8c-cli@example.invalid",
        "-c",
        "user.name=S8C CLI test",
        "commit",
        "-q",
        "-m",
        "s8c CLI fixture",
    )
    commit = _git(repo_root, "rev-parse", "--verify", "HEAD^{commit}")
    return repo_root, commit


@pytest.fixture(scope="module")
def oracle(tiny_repo: tuple[Path, str]) -> P.ActivationReport:
    repo_root, commit = tiny_repo
    for relative_path in (
        P.CORE_MODULE_PATH,
        P.EVALUATOR_MODULE_PATH,
        P.PROJECTION_MODULE_PATH,
    ):
        assert P.read_blob_at(repo_root, commit, relative_path) == (
            _ROOT / relative_path
        ).read_bytes()

    report = P.activation_report_at(repo_root, commit)
    reasons = tuple(item.reason_code for item in report.predicates)
    assert len(reasons) == 12
    assert len(set(reasons)) > 1
    assert not any(
        reason == "evaluator-exception"
        or reason.endswith("-blob-mismatch")
        or reason.endswith("-absent-at-commit")
        for reason in reasons
    )
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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
