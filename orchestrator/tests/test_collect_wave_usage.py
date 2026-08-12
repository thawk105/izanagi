# -*- coding: utf-8 -*-
"""tools/collect_wave_usage.py の非 gate artifact 収集テスト。"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tools import claude_session_ledger as LEDGER
from tools import collect_wave_usage as USAGE


def _report(
    *,
    model_calls: int = 1,
    sidechain_calls: int = 0,
    limit: bool = False,
    issues: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "population": {"files_scanned": 9, "limit_reached": limit},
        "root": {"model_calls": model_calls},
        "sidechains": {"model_calls": sidechain_calls},
        "issues": issues or {},
    }


def _argv(out: Path, *extra: str) -> list[str]:
    return [
        "--wave-id",
        "synthetic-wave",
        "--out",
        str(out),
        "--project",
        "synthetic-project",
        "--cwd-under",
        "/synthetic/izanagi",
        *extra,
    ]


def _load_artifact(out: Path) -> dict[str, Any]:
    with out.open(encoding="utf-8") as stream:
        return json.load(stream)


def _patch_other_site(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        USAGE.site_policy,
        "current_site",
        lambda **kwargs: USAGE.site_policy.OTHER,
    )


def _subprocess_env(tmp_path: Path) -> dict[str, str]:
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text(
        "import socket\nsocket.gethostname = lambda: 'synthetic-host'\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(tmp_path), existing) if part
    )
    return env


def _run_helper_process(
    tmp_path: Path, *argv: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.fspath(USAGE.__file__), *argv],
        cwd=USAGE._REPO_ROOT,
        env=_subprocess_env(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )


def test_zero_model_calls_is_missing_not_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    report = _report(model_calls=0, sidechain_calls=0)
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=report, exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "missing"
    assert artifact["collection"]["status"] != "complete"
    assert "observed_zero" not in json.dumps(artifact, sort_keys=True)


@pytest.mark.parametrize(
    ("limit", "issues"),
    [
        (True, None),
        (False, {"missing_project": ["synthetic-project"]}),
    ],
)
def test_zero_model_calls_is_missing_before_incomplete_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit: bool,
    issues: dict[str, list[str]] | None,
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    report = _report(model_calls=0, limit=limit, issues=issues)
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=report, exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "missing"
    assert artifact["collection"]["reasons"] == [
        "root.model_calls + sidechains.model_calls is zero"
    ]


def test_limit_reached_is_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    report = _report(limit=True)
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=report, exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "incomplete"
    assert "population.limit_reached is true" in artifact["collection"]["reasons"]
    assert artifact["ledger_report"] == report


def test_collector_argv_uses_equals_tokens_for_every_value_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    seen: list[str] = []

    def fake_collect(argv: list[str]) -> SimpleNamespace:
        seen.extend(argv)
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", fake_collect)

    assert USAGE.main(
        _argv(
            out,
            "--project",
            "synthetic-secondary",
            "--projects-root",
            "/synthetic/projects",
            "--since",
            "2026-08-13T00:00:00Z",
            "--until",
            "2026-08-13T01:00:00Z",
            "--max-files",
            "37",
        )
    ) == 0

    assert seen == [
        "--projects-root=/synthetic/projects",
        "--project=synthetic-project",
        "--project=synthetic-secondary",
        "--cwd-under=/synthetic/izanagi",
        "--since=2026-08-13T00:00:00Z",
        "--until=2026-08-13T01:00:00Z",
        "--max-files=37",
        "--include-sidechains",
    ]
    assert "--strict" not in seen
    artifact = _load_artifact(out)
    assert artifact["artifact_type"] == "izanagi.dev-wave.claude-usage"
    assert artifact["schema_version"] == 1
    assert artifact["selector"]["max_files"] == 37
    assert artifact["selector"]["include_sidechains"] is True
    assert artifact["selector"]["projects"] == [
        "synthetic-project",
        "synthetic-secondary",
    ]
    assert artifact["selector"]["projects_root"] == "/synthetic/projects"
    assert artifact["selector"]["since"] == "2026-08-13T00:00:00Z"
    assert artifact["selector"]["until"] == "2026-08-13T01:00:00Z"


def test_leading_dash_project_slug_reaches_collector_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    seen: list[list[str]] = []

    def fake_collect(argv: list[str]) -> SimpleNamespace:
        seen.append(argv)
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", fake_collect)

    assert USAGE.main(
        [
            "--wave-id",
            "synthetic-wave",
            "--out",
            str(out),
            "--project=-work-1-SFC-tanab-izanagi",
            "--cwd-under",
            "/synthetic/izanagi",
        ]
    ) == 0
    assert seen == [
        [
            "--project=-work-1-SFC-tanab-izanagi",
            "--cwd-under=/synthetic/izanagi",
            f"--max-files={LEDGER.MAX_MAX_FILES}",
            "--include-sidechains",
        ]
    ]
    assert _load_artifact(out)["selector"]["projects"] == [
        "-work-1-SFC-tanab-izanagi"
    ]


@pytest.mark.parametrize(
    ("status", "site", "expected_rc"),
    [
        ("complete", USAGE.site_policy.OTHER, 0),
        ("blocked", USAGE.site_policy.PEGASUS_LOGIN, 3),
        ("blocked", USAGE.site_policy.PEGASUS_SUSPECT, 1),
        ("incomplete", USAGE.site_policy.OTHER, 1),
        ("missing", USAGE.site_policy.OTHER, 1),
        ("error", USAGE.site_policy.OTHER, 1),
        ("synthetic-unknown", USAGE.site_policy.OTHER, 1),
    ],
)
def test_collection_status_exit_code_contract_preserves_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    site: str,
    expected_rc: int,
) -> None:
    out = tmp_path / "usage.json"
    monkeypatch.setattr(
        USAGE.site_policy,
        "current_site",
        lambda **kwargs: site,
    )

    def fake_collect(args: Any, observed_site: str) -> dict[str, Any]:
        assert observed_site == site
        return USAGE._artifact(
            args,
            site=observed_site,
            status=status,
            reasons=[] if status == "complete" else ["synthetic reason"],
        )

    monkeypatch.setattr(USAGE, "_collect", fake_collect)

    assert USAGE.main(_argv(out)) == expected_rc
    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == status
    assert artifact["collection"]["site"] == site


def test_issues_make_a_nonzero_collection_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    report = _report(issues={"missing_project": ["synthetic-project"]})
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=report, exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "incomplete"
    assert "collector reported issues" in artifact["collection"]["reasons"]


def test_helper_imports_public_collector_without_subprocess_or_json_reparse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)
    report = _report(model_calls=2)
    calls = 0

    def fake_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=report, exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", fake_collect)
    assert USAGE.main(_argv(out)) == 0
    assert calls == 1
    assert _load_artifact(out)["ledger_report"] == report

    source = Path(USAGE.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from_modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    calls_in_source = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert "subprocess" not in imported_modules
    assert "subprocess" not in imported_from_modules
    assert not any(
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "loads"
        for node in calls_in_source
    )
    assert "from tools.claude_session_ledger import" in source


def test_collector_exception_is_error_but_main_returns_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)

    def failing_collect(argv: list[str]) -> None:
        raise RuntimeError("synthetic collector failure")

    monkeypatch.setattr(USAGE, "collect_report", failing_collect)

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "error"
    assert artifact["collection"]["collector_exit_code"] is None
    assert artifact["ledger_report"] is None
    assert any("RuntimeError" in reason for reason in artifact["collection"]["reasons"])


def test_existing_output_is_not_overwritten_and_leaves_no_temporary_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    original = b"synthetic existing artifact\n"
    out.write_bytes(original)
    _patch_other_site(monkeypatch)
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=_report(), exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1

    assert out.read_bytes() == original
    assert list(tmp_path.glob(f".{out.name}.*.tmp")) == []


@pytest.mark.parametrize(
    "site",
    [
        USAGE.site_policy.PEGASUS_LOGIN,
        USAGE.site_policy.PEGASUS_SUSPECT,
    ],
)
def test_unclassified_site_is_blocked_without_calling_collector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str
) -> None:
    out = tmp_path / "usage.json"
    monkeypatch.setattr(
        USAGE.site_policy,
        "current_site",
        lambda **kwargs: site,
    )
    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)

    expected_rc = 3 if site == USAGE.site_policy.PEGASUS_LOGIN else 1
    assert USAGE.main(_argv(out)) == expected_rc

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "blocked"
    assert artifact["collection"]["site"] == site
    expected_reason = (
        "Pegasus login node blocks the unclassified collector"
        if site == USAGE.site_policy.PEGASUS_LOGIN
        else "site evidence is insufficient to run the unclassified collector"
    )
    assert artifact["collection"]["reasons"] == [expected_reason]
    assert artifact["ledger_report"] is None
    assert calls == 0


@pytest.mark.parametrize("hostname", [None, "pegasus02", "pegasus-next"])
def test_collector_site_classification_fails_closed_without_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: str | None,
) -> None:
    out = tmp_path / "usage.json"
    if hostname is None:
        monkeypatch.setattr(
            USAGE.site_policy.socket,
            "gethostname",
            lambda: (_ for _ in ()).throw(OSError("hostname unavailable")),
        )
    else:
        monkeypatch.setattr(
            USAGE.site_policy.socket, "gethostname", lambda: hostname
        )
    monkeypatch.setattr(USAGE.site_policy, "_has_nqsv", lambda: False)
    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)

    assert USAGE.main(_argv(out)) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "blocked"
    assert artifact["collection"]["site"] == USAGE.site_policy.PEGASUS_SUSPECT
    assert artifact["collection"]["reasons"] == [
        "site evidence is insufficient to run the unclassified collector"
    ]
    assert calls == 0


@pytest.mark.parametrize(
    ("site", "expected_rc"),
    [
        (USAGE.site_policy.PEGASUS_SUSPECT, 1),
        (USAGE.site_policy.PEGASUS_LOGIN, 3),
    ],
)
def test_suspect_site_is_collection_error_not_normal_policy_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
    expected_rc: int,
) -> None:
    out = tmp_path / "usage.json"
    monkeypatch.setattr(
        USAGE.site_policy,
        "current_site",
        lambda **kwargs: site,
    )
    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)

    assert USAGE.main(_argv(out)) == expected_rc
    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "blocked"
    assert artifact["collection"]["site"] == site
    assert calls == 0


def test_missing_project_never_falls_back_to_all_projects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)

    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)
    argv = [
        "--wave-id",
        "synthetic-wave",
        "--out",
        str(out),
        "--cwd-under",
        "/synthetic/izanagi",
    ]

    assert USAGE.main(argv) == 1

    artifact = _load_artifact(out)
    assert artifact["collection"]["status"] == "error"
    assert artifact["selector"]["projects"] == []
    assert calls == 0


def test_output_must_be_absolute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_other_site(monkeypatch)
    out = Path("synthetic-relative-usage.json")

    def forbidden_collect(argv: list[str]) -> None:
        raise AssertionError("invalid output must be rejected before collection")

    monkeypatch.setattr(USAGE, "collect_report", forbidden_collect)

    assert USAGE.main(_argv(out)) == 2
    assert not out.exists()


@pytest.mark.parametrize("marker_kind", ["file", "directory"])
def test_output_below_any_git_marker_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    marker_kind: str,
) -> None:
    checkout = tmp_path / "outer" / "synthetic-checkout"
    out = checkout / "nested" / "usage.json"
    out.parent.mkdir(parents=True)
    marker = checkout / ".git"
    if marker_kind == "file":
        marker.write_text("gitdir: synthetic-git-dir\n", encoding="utf-8")
    else:
        marker.mkdir()
        (marker / "HEAD").write_text(
            "ref: refs/heads/synthetic\n", encoding="utf-8"
        )
    _patch_other_site(monkeypatch)
    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)

    assert USAGE.main(_argv(out)) == 1
    assert not out.exists()
    assert calls == 0


def test_output_below_empty_git_directory_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = tmp_path / "outer" / "synthetic-checkout"
    out = checkout / "nested" / "usage.json"
    out.parent.mkdir(parents=True)
    (checkout / ".git").mkdir()
    _patch_other_site(monkeypatch)
    calls = 0

    def counted_collect(argv: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return SimpleNamespace(report=_report(), exit_code=0)

    monkeypatch.setattr(USAGE, "collect_report", counted_collect)

    assert USAGE.main(_argv(out)) == 0
    assert _load_artifact(out)["collection"]["status"] == "complete"
    assert calls == 1


def test_process_returns_two_when_required_arguments_are_missing(
    tmp_path: Path,
) -> None:
    completed = _run_helper_process(tmp_path)

    assert completed.returncode == 2


def test_process_help_documents_equals_project_and_exit_code_contract(
    tmp_path: Path,
) -> None:
    completed = _run_helper_process(tmp_path, "--help")

    assert completed.returncode == 0
    assert "--project=<slug>" in completed.stdout
    assert "0  collection.status=complete または --help" in completed.stdout
    assert "1  PEGASUS_SUSPECT の blocked、incomplete、missing、error" in completed.stdout
    assert "2  外側 argv を argparse が拒否" in completed.stdout
    assert "3  PEGASUS_LOGIN と確証できた site の blocked" in completed.stdout


def test_split_leading_dash_project_is_rejected_and_requires_equals_form(
    tmp_path: Path,
) -> None:
    out = tmp_path / "usage.json"
    completed = _run_helper_process(
        tmp_path,
        "--wave-id",
        "synthetic-wave",
        "--out",
        os.fspath(out),
        "--project",
        "-work-1-SFC-tanab-izanagi",
        "--cwd-under",
        "/synthetic/izanagi",
    )

    assert completed.returncode == 2
    assert not out.exists()


def test_process_returns_one_when_project_is_missing(tmp_path: Path) -> None:
    out = tmp_path / "missing-project.json"
    completed = _run_helper_process(
        tmp_path,
        "--wave-id",
        "synthetic-wave",
        "--out",
        os.fspath(out),
        "--cwd-under",
        "/synthetic/izanagi",
    )

    assert completed.returncode == 1
    assert _load_artifact(out)["collection"]["status"] == "error"


def test_process_returns_one_when_output_is_inside_repo(tmp_path: Path) -> None:
    out = USAGE._REPO_ROOT / f"synthetic-repo-usage-{tmp_path.name}.json"
    completed = _run_helper_process(tmp_path, *_argv(out))

    assert completed.returncode == 1
    assert not out.exists()


def test_process_returns_one_and_records_nonzero_collector_exit_code(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collector-error.json"
    projects_root = tmp_path / "missing-projects-root"
    completed = _run_helper_process(
        tmp_path,
        *_argv(out, "--projects-root", os.fspath(projects_root)),
    )

    assert completed.returncode == 1
    artifact = _load_artifact(out)
    assert artifact["collection"]["collector_exit_code"] == 2
    assert artifact["collection"]["status"] == "missing"


def test_missing_output_parent_is_not_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "missing-parent"
    out = parent / "usage.json"
    _patch_other_site(monkeypatch)
    monkeypatch.setattr(
        USAGE,
        "collect_report",
        lambda argv: SimpleNamespace(report=_report(), exit_code=0),
    )

    assert USAGE.main(_argv(out)) == 1
    assert not parent.exists()


def test_keyboard_interrupt_is_not_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "usage.json"
    _patch_other_site(monkeypatch)

    def interrupted_collect(argv: list[str]) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(USAGE, "collect_report", interrupted_collect)

    with pytest.raises(KeyboardInterrupt):
        USAGE.main(_argv(out))


def test_cwd_under_uses_path_boundary_and_combines_with_contains_as_and(
    tmp_path: Path,
) -> None:
    projects = tmp_path / "projects"
    project = projects / "synthetic-project"
    project.mkdir(parents=True)
    records = []
    for index, cwd in enumerate(
        (
            "/synthetic/izanagi",
            "/synthetic/izanagi/nested",
            "/synthetic/izanagi-fix",
        )
    ):
        records.append(
            {
                "type": "assistant",
                "requestId": f"request-{index}",
                "cwd": cwd,
                "timestamp": f"2026-01-10T00:00:0{index}Z",
                "message": {
                    "id": f"message-{index}",
                    "model": "claude-synthetic-test",
                    "content": [],
                    "usage": {
                        "cache_read_input_tokens": 1,
                        "cache_creation_input_tokens": 2,
                        "input_tokens": 3,
                        "output_tokens": 4,
                    },
                },
            }
        )
    with (project / "synthetic.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            json.dump(record, stream, separators=(",", ":"))
            stream.write("\n")

    boundary = LEDGER.collect_report(
        [
            "--projects-root",
            str(projects),
            "--project",
            "synthetic-project",
            "--cwd-under",
            "/synthetic/izanagi",
        ]
    )
    combined = LEDGER.collect_report(
        [
            "--projects-root",
            str(projects),
            "--project",
            "synthetic-project",
            "--cwd-under",
            "/synthetic/izanagi",
            "--cwd-contains",
            "nested",
        ]
    )

    assert boundary.report["root"]["model_calls"] == 2
    assert combined.report["root"]["model_calls"] == 1
    with pytest.raises(SystemExit) as raised:
        LEDGER.collect_report(["--cwd-under", "synthetic/izanagi"])
    assert raised.value.code == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
