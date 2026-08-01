# -*- coding: utf-8 -*-
"""tools/run_tests.py の argv 正規化・受入 preflight 回帰。

変異対応: V14 = acceptance の ``PYTEST_ADDOPTS.strip()`` 除去、
V15 = submodule auto-init の ``--no-fetch`` 除去。
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "tools" / "run_tests.py"
_SPEC = importlib.util.spec_from_file_location("run_tests_preflight_test", _RUNNER)
assert _SPEC and _SPEC.loader
RT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RT)

_EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS = frozenset({
    "--collect-only",
    "--co",
    "--help",
    "--version",
    "--markers",
    "--fixtures",
    "--fixtures-per-test",
    "--trace-config",
    "--setup-plan",
})


@pytest.fixture(autouse=True)
def _clean_runner_env(monkeypatch):
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT",
        "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", "IZANAGI_TEST_TRIGGER",
        "IZANAGI_TASK_RUN_ID", "PYTEST_ADDOPTS",
    ):
        monkeypatch.delenv(name, raising=False)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _tracked_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "runner@example.invalid")
    _git(repo, "config", "user.name", "Runner Test")
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-qm", "fixture")
    return repo


def _create_submodule_markers(repo: Path) -> None:
    root = repo / "external" / "ccbench"
    root.mkdir(parents=True, exist_ok=True)
    (root / "CMakeLists.txt").write_text("fixture\n", encoding="utf-8")
    (root / ".git").write_text("gitdir: fixture\n", encoding="utf-8")


def _create_modules_cache(common_dir: Path) -> Path:
    cache = common_dir / "modules" / "external" / "ccbench"
    cache.mkdir(parents=True)
    return cache


def test_normalize_position_and_path_options_once_from_caller_cwd(tmp_path):
    caller = tmp_path / "caller"
    target = caller / "tests" / "test_sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("def test_sample(): pass\n", encoding="utf-8")

    args = RT._normalize_args(
        [
            "tests/test_sample.py::test_sample",
            "-k", "tests/test_sample.py",
            "--rootdir", "root",
            "--junitxml=reports/result.xml",
            "--log-file", "logs/test.log",
            "-n", "4",
        ],
        caller,
    )

    assert args == [
        f"{target.resolve()}::test_sample",
        "-k", "tests/test_sample.py",
        "--rootdir", str((caller / "root").resolve()),
        f"--junitxml={(caller / 'reports/result.xml').resolve()}",
        "--log-file", str((caller / "logs/test.log").resolve()),
        "-n", "4",
    ]


@pytest.mark.parametrize(
    ("option", "spelling"),
    [
        ("--rootdir", "separate"),
        ("--confcutdir", "equals"),
        ("--basetemp", "separate"),
        ("--junitxml", "equals"),
        ("--log-file", "separate"),
    ],
)
def test_all_closed_path_value_options_are_absolutized(tmp_path, option, spelling):
    expected = str((tmp_path / "not-created").resolve())
    raw = [option, "not-created"] if spelling == "separate" else [
        f"{option}=not-created",
    ]
    normalized = RT._normalize_args(raw, tmp_path)
    assert normalized == (
        [option, expected] if spelling == "separate" else [f"{option}={expected}"]
    )


def test_non_path_option_values_and_missing_position_are_unchanged(tmp_path):
    assert RT._normalize_args(
        ["-k", "missing.py", "--color", "yes", "also-missing.py"], tmp_path,
    ) == ["-k", "missing.py", "--color", "yes", "also-missing.py"]


def test_relative_and_absolute_target_have_one_suite_identity(tmp_path):
    target = tmp_path / "test_private.py"
    target.write_text("def test_private(): pass\n", encoding="utf-8")
    relative = RT._normalize_args(["test_private.py::test_private"], tmp_path)
    absolute = RT._normalize_args([str(target) + "::test_private"], _REPO)
    assert relative == absolute
    assert RT._suite_identity(relative, "") == RT._suite_identity(absolute, "")


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["-q"],
        ["-qv"],
        ["-n", "8"],
        ["-n8"],
        ["--numprocesses=8"],
        ["--dist", "loadgroup"],
        ["--dist=loadgroup"],
        ["orchestrator/tests"],
        [str(_REPO / "orchestrator" / "tests")],
        ["-n", "2", "--color=yes"],
        ["-qvv"],
        ["--disable-warnings"],
        ["-s"],
    ],
)
def test_acceptance_shape_positive_controls(args):
    assert RT._is_acceptance_run(args)


@pytest.mark.parametrize(
    "args",
    [
        ["/tmp/outside.py"],
        [str(_REPO / "orchestrator" / "tests" / "test_run_tests_nproc.py")],
        [str(_REPO / "orchestrator" / "tests" / "test_run_tests_nproc.py")
         + "::test_available_cpus_positive_and_affinity_bounded"],
        ["-k", "selected"],
        ["-mselected"],
        ["-qkselected"],
        ["-qs"],
        ["--lf"],
        ["-o", "x=1"],
        ["-pno:plugin"],
        ["--override-ini=x=1"],
        ["--", "-q"],
        ["--collect-only"],
        ["--smoke-only"],
        ["-Z"],
        ["orchestrator/tests::test_node"],
    ],
)
def test_acceptance_shape_rejects_targeting_and_no_execution(args):
    assert not RT._is_acceptance_run(args)


@pytest.mark.parametrize("addopts", ["-k selected", "--collect-only"])
def test_nonempty_pytest_addopts_is_not_acceptance(monkeypatch, addopts):
    monkeypatch.setenv("PYTEST_ADDOPTS", addopts)
    assert not RT._is_acceptance_run([])


def test_v14_whitespace_only_addopts_keeps_default_deletion_gate(
    tmp_path, monkeypatch,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("PYTEST_ADDOPTS", " ")
    assert RT._preflight_unstaged_deletions([], repo) == 13


def test_disable_warnings_keeps_unstaged_deletion_gate(tmp_path):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    assert RT._preflight_unstaged_deletions(["--disable-warnings"], repo) == 13


def test_disable_warnings_passes_acceptance_preflights_without_deletion(tmp_path):
    repo = _tracked_repo(tmp_path)
    _create_submodule_markers(repo)
    assert RT._is_acceptance_run(["--disable-warnings"])
    assert RT._preflight_unstaged_deletions(["--disable-warnings"], repo) == 0
    assert RT._preflight_submodule(["--disable-warnings"], repo) == 0


def test_no_execution_flag_reads_pytest_addopts_and_malformed_is_not_skip(
    monkeypatch,
):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only -q")
    assert RT._has_no_execution_flag([])
    monkeypatch.setenv("PYTEST_ADDOPTS", "'unterminated")
    assert not RT._has_no_execution_flag([])
    assert not RT._is_acceptance_run([])
    assert RT._has_no_execution_flag(["--collect-only"])


def test_unstaged_deletion_gate_detects_count_and_scrubs_git_env(
    tmp_path, monkeypatch, capsys,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "poison"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "poison-tree"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "poison-index"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(tmp_path / "poison-objects"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "poison")
    monkeypatch.setenv("RUNNER_SENTINEL", "kept")
    real_run = subprocess.run
    captured = {}

    def recording_run(*args, **kwargs):
        captured["env"] = kwargs["env"]
        return real_run(*args, **kwargs)

    monkeypatch.setattr(RT.subprocess, "run", recording_run)
    assert RT._preflight_unstaged_deletions([], repo) == 13
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    ):
        assert name not in captured["env"]
    assert captured["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
    assert captured["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert captured["env"]["RUNNER_SENTINEL"] == "kept"
    stderr = capsys.readouterr().err
    assert "未 stage 削除を 1 件" in stderr
    assert "tracked.txt" in stderr
    assert "git add -A" in stderr


def test_unstaged_deletion_exact_bypass_warns_and_continues(
    tmp_path, monkeypatch, capsys,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", "1")
    assert RT._preflight_unstaged_deletions([], repo) == 0
    assert "許可して続行" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["true", "01", " 1"])
def test_unstaged_deletion_bypass_is_exact_one(tmp_path, monkeypatch, value):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", value)
    assert RT._preflight_unstaged_deletions([], repo) == 13


def test_final_trigger_forbids_unstaged_deletion_bypass(
    tmp_path, monkeypatch, capsys,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", "1")
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    assert RT._preflight_unstaged_deletions([], repo) == 13
    assert "final" in capsys.readouterr().err


def test_targeted_run_does_not_invoke_deletion_gate(monkeypatch, tmp_path):
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_unstaged_deletions(["/tmp/target.py"], tmp_path) == 0
    invoked.assert_not_called()


def test_targeted_run_does_not_invoke_ruleops_preflight(monkeypatch, tmp_path):
    invoked = mock.Mock(side_effect=AssertionError("RuleOps must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_ruleops(["/tmp/target.py"], tmp_path) == 0
    invoked.assert_not_called()


def test_m10_acceptance_ruleops_preflight_invokes_production_ledger(
    monkeypatch, tmp_path,
):
    completed = subprocess.CompletedProcess(["ruleops"], 0, "{}\n", "")
    invoked = mock.Mock(return_value=completed)
    monkeypatch.setattr(RT.subprocess, "run", invoked)

    assert RT._preflight_ruleops(["--disable-warnings"], tmp_path) == 0
    invoked.assert_called_once_with(
        [
            sys.executable,
            str(tmp_path / "tools" / "ruleops.py"),
            "check",
            "--repo",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_acceptance_ruleops_failure_propagates_rc_and_reason(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(
        RT.subprocess,
        "run",
        mock.Mock(return_value=subprocess.CompletedProcess(
            ["ruleops"], 2, "", "ruleops: schema-keys: unknown=['safe']\n",
        )),
    )
    assert RT._preflight_ruleops([], tmp_path) == 15
    stderr = capsys.readouterr().err
    assert "child rc=2" in stderr
    assert "schema-keys" in stderr


def test_acceptance_ruleops_timeout_is_rc15(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        RT.subprocess,
        "run",
        mock.Mock(side_effect=subprocess.TimeoutExpired(["ruleops"], 60)),
    )
    assert RT._preflight_ruleops([], tmp_path) == 15
    assert "child rc=timeout" in capsys.readouterr().err


def test_deletion_git_failure_warns_and_continues(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        RT.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 128, "", "failure"),
    )
    assert RT._preflight_unstaged_deletions([], tmp_path) == 0
    assert "警告" in capsys.readouterr().err


def test_deletion_git_unavailable_warns_and_continues(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(
        RT.subprocess, "run", mock.Mock(side_effect=FileNotFoundError("git")),
    )
    assert RT._preflight_unstaged_deletions([], tmp_path) == 0
    assert "警告" in capsys.readouterr().err


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CompletedProcess(["git"], 128, "", "failure"),
        FileNotFoundError("git"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
    ],
)
def test_final_deletion_git_failure_is_unverified_and_fails_closed(
    monkeypatch, tmp_path, capsys, failure,
):
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    if isinstance(failure, subprocess.CompletedProcess):
        monkeypatch.setattr(RT.subprocess, "run", lambda *a, **kw: failure)
    else:
        monkeypatch.setattr(RT.subprocess, "run", mock.Mock(side_effect=failure))
    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    stderr = capsys.readouterr().err
    assert "final" in stderr
    assert "未検査" in stderr


def test_nonfinal_deletion_decode_failure_warns_and_continues(
    monkeypatch, tmp_path, capsys,
):
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
    monkeypatch.setattr(RT.subprocess, "run", mock.Mock(side_effect=failure))
    assert RT._preflight_unstaged_deletions([], tmp_path) == 0
    assert "警告" in capsys.readouterr().err


def test_submodule_existing_real_markers_need_no_git(monkeypatch, tmp_path):
    _create_submodule_markers(tmp_path)
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_submodule([], tmp_path) == 0
    invoked.assert_not_called()


def test_submodule_marker_requires_nonsymlink_file_and_git_marker(tmp_path):
    root = tmp_path / "external" / "ccbench"
    root.mkdir(parents=True)
    marker = root / "CMakeLists.txt"
    marker.write_text("fixture\n", encoding="utf-8")
    assert not RT._submodule_is_initialized(tmp_path)

    (root / ".git").write_text("gitdir: fixture\n", encoding="utf-8")
    marker.unlink()
    marker.symlink_to(tmp_path / "outside")
    (tmp_path / "outside").write_text("fixture\n", encoding="utf-8")
    assert not RT._submodule_is_initialized(tmp_path)

    marker.unlink()
    marker.write_text("fixture\n", encoding="utf-8")
    (root / ".git").unlink()
    (root / ".git").symlink_to(tmp_path / "outside-git")
    (tmp_path / "outside-git").write_text("gitdir: fixture\n", encoding="utf-8")
    assert not RT._submodule_is_initialized(tmp_path)


def test_submodule_no_execution_shape_skips_missing_marker(monkeypatch, tmp_path):
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_submodule(["--collect-only"], tmp_path) == 0
    invoked.assert_not_called()


def test_submodule_no_execution_from_pytest_addopts_skips_missing_marker(
    monkeypatch, tmp_path,
):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_submodule([], tmp_path) == 0
    invoked.assert_not_called()


def test_targeted_missing_submodule_warns_without_init(
    monkeypatch, tmp_path, capsys,
):
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_submodule(["/tmp/target.py"], tmp_path) == 0
    invoked.assert_not_called()
    assert "targeted run" in capsys.readouterr().err


def test_v15_acceptance_missing_submodule_initializes_no_fetch_with_scrubbed_env(
    monkeypatch, tmp_path,
):
    common_dir = tmp_path / "common"
    _create_modules_cache(common_dir)
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    ):
        monkeypatch.setenv(name, str(tmp_path / f"poison-{name.lower()}"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "poison")
    monkeypatch.setenv("RUNNER_SENTINEL", "kept")
    captured = []

    def initialize(command, **kwargs):
        captured.append((command, kwargs))
        if command[-2:] == ["rev-parse", "--git-common-dir"]:
            return subprocess.CompletedProcess(command, 0, str(common_dir), "")
        _create_submodule_markers(tmp_path)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(RT.subprocess, "run", initialize)
    assert RT._preflight_submodule([], tmp_path) == 0
    assert captured[1][0] == [
        "git", "-C", str(tmp_path.resolve()), "submodule", "update", "--init",
        "--no-fetch", "--", "external/ccbench",
    ]
    assert len(captured) == 2
    for _, kwargs in captured:
        assert kwargs["timeout"] == 120
        for name in (
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
        ):
            assert name not in kwargs["env"]
        assert kwargs["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert kwargs["env"]["RUNNER_SENTINEL"] == "kept"


def test_submodule_marker_recheck_wins_over_git_rc(monkeypatch, tmp_path):
    common_dir = tmp_path / "common"
    _create_modules_cache(common_dir)

    def initialize(command, **kwargs):
        if command[-2:] == ["rev-parse", "--git-common-dir"]:
            return subprocess.CompletedProcess(command, 0, str(common_dir), "")
        _create_submodule_markers(tmp_path)
        return subprocess.CompletedProcess(command, 1, "", "failure-after-init")

    monkeypatch.setattr(RT.subprocess, "run", initialize)
    assert RT._preflight_submodule([], tmp_path) == 0


def test_acceptance_without_local_modules_cache_does_not_attempt_init(
    monkeypatch, tmp_path, capsys,
):
    common_dir = tmp_path / "common"
    calls = []

    def rev_parse_only(command, **kwargs):
        calls.append(command)
        assert command[-2:] == ["rev-parse", "--git-common-dir"]
        return subprocess.CompletedProcess(command, 0, str(common_dir), "")

    monkeypatch.setattr(RT.subprocess, "run", rev_parse_only)
    assert RT._preflight_submodule([], tmp_path) == 14
    assert len(calls) == 1
    stderr = capsys.readouterr().err
    assert "local modules cache" in stderr
    assert "git submodule update --init -- external/ccbench" in stderr


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CompletedProcess(["git"], 128, "", "failure"),
        FileNotFoundError("git"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
        subprocess.TimeoutExpired(["git"], 120),
    ],
)
def test_acceptance_common_dir_failure_never_attempts_init(
    monkeypatch, tmp_path, failure,
):
    invoked = mock.Mock()
    if isinstance(failure, subprocess.CompletedProcess):
        invoked.return_value = failure
    else:
        invoked.side_effect = failure
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_submodule([], tmp_path) == 14
    invoked.assert_called_once()


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired(["git"], 120),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
    ],
)
def test_acceptance_init_timeout_or_decode_failure_is_rc14(
    monkeypatch, tmp_path, failure,
):
    common_dir = tmp_path / "common"
    _create_modules_cache(common_dir)
    calls = []

    def fail_init(command, **kwargs):
        calls.append(command)
        if command[-2:] == ["rev-parse", "--git-common-dir"]:
            return subprocess.CompletedProcess(command, 0, str(common_dir), "")
        raise failure

    monkeypatch.setattr(RT.subprocess, "run", fail_init)
    assert RT._preflight_submodule([], tmp_path) == 14
    assert len(calls) == 2


def test_acceptance_submodule_still_missing_after_init_fails_closed(
    monkeypatch, tmp_path, capsys,
):
    common_dir = tmp_path / "common"
    _create_modules_cache(common_dir)

    def unsuccessful_init(command, **kwargs):
        if command[-2:] == ["rev-parse", "--git-common-dir"]:
            return subprocess.CompletedProcess(command, 0, str(common_dir), "")
        return subprocess.CompletedProcess(command, 1, "", "failure")

    monkeypatch.setattr(RT.subprocess, "run", unsuccessful_init)
    assert RT._preflight_submodule([], tmp_path) == 14
    stderr = capsys.readouterr().err
    assert "初期化できません" in stderr
    assert "git submodule update --init -- external/ccbench" in stderr


def test_main_deletion_preflight_failure_is_wired_before_xdist(monkeypatch):
    ensure = mock.Mock(side_effect=AssertionError("xdist must not run"))
    ruleops = mock.Mock(side_effect=AssertionError("RuleOps must not run"))
    submodule = mock.Mock(side_effect=AssertionError("submodule must not run"))
    deletion = mock.Mock(return_value=13)
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", deletion)
    monkeypatch.setattr(RT, "_preflight_ruleops", ruleops)
    monkeypatch.setattr(RT, "_preflight_submodule", submodule)
    assert RT.main([]) == 13
    deletion.assert_called_once_with([], Path(RT._REPO))
    ensure.assert_not_called()
    ruleops.assert_not_called()
    submodule.assert_not_called()


def test_main_ruleops_preflight_failure_is_wired_before_submodule_and_xdist(
    monkeypatch,
):
    ensure = mock.Mock(side_effect=AssertionError("xdist must not run"))
    deletion = mock.Mock(return_value=0)
    ruleops = mock.Mock(return_value=15)
    submodule = mock.Mock(side_effect=AssertionError("submodule must not run"))
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", deletion)
    monkeypatch.setattr(RT, "_preflight_ruleops", ruleops)
    monkeypatch.setattr(RT, "_preflight_submodule", submodule)
    assert RT.main([]) == 15
    deletion.assert_called_once_with([], Path(RT._REPO))
    ruleops.assert_called_once_with([], Path(RT._REPO))
    submodule.assert_not_called()
    ensure.assert_not_called()


def test_main_submodule_preflight_failure_is_wired_before_xdist(monkeypatch):
    ensure = mock.Mock(side_effect=AssertionError("xdist must not run"))
    deletion = mock.Mock(return_value=0)
    ruleops = mock.Mock(return_value=0)
    submodule = mock.Mock(return_value=14)
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", deletion)
    monkeypatch.setattr(RT, "_preflight_ruleops", ruleops)
    monkeypatch.setattr(RT, "_preflight_submodule", submodule)
    assert RT.main([]) == 14
    ensure.assert_not_called()
    deletion.assert_called_once_with([], Path(RT._REPO))
    ruleops.assert_called_once_with([], Path(RT._REPO))
    submodule.assert_called_once_with([], Path(RT._REPO))


def test_m1_login_dispatch_runs_after_13_15_14_and_before_xdist(monkeypatch):
    # M1: LOGIN を OTHER に落とすと dispatch event が消え、xdist 側へ到達して赤になる。
    events = []

    def preflight(name):
        return lambda args, repo: events.append(name) or 0

    def dispatch(args, *, environ):
        assert "IZANAGI_TASK_RUN_ID" not in environ
        events.append(("dispatch", list(args)))
        return 7

    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions", preflight("deletion"),
    )
    monkeypatch.setattr(RT, "_preflight_ruleops", preflight("ruleops"))
    monkeypatch.setattr(RT, "_preflight_submodule", preflight("submodule"))
    monkeypatch.setattr(
        RT,
        "_ensure_xdist",
        mock.Mock(side_effect=AssertionError("xdist must follow dispatch")),
    )

    classified_site = RT.site_policy.classify_site("pegasus02", {}, True)
    assert RT.main(
        ["test_target.py"],
        site=classified_site,
        dispatch_fn=dispatch,
    ) == 7
    assert events == [
        "deletion", "ruleops", "submodule", ("dispatch", ["test_target.py"]),
    ]


@pytest.mark.parametrize("flag", sorted(_EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS))
def test_login_dispatch_exemption_is_exact_closed_set(monkeypatch, flag):
    assert RT._PEGASUS_DISPATCH_EXEMPT_FLAGS == (
        _EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS
    )
    dispatch = mock.Mock(side_effect=AssertionError("must be exempt"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    monkeypatch.setattr(RT.subprocess, "call", lambda *a, **kw: 0)

    assert RT.main(
        [flag],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 0
    dispatch.assert_not_called()


@pytest.mark.parametrize("flag", ["--setup-only", "--setup-show"])
def test_login_setup_execution_shapes_are_not_dispatch_exempt(
    monkeypatch, flag,
):
    dispatch = mock.Mock(return_value=3)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    assert RT.main(
        [flag],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 3
    dispatch.assert_called_once()


def test_suspect_execution_refuses_without_dispatch_or_xdist(
    monkeypatch, capsys,
):
    dispatch = mock.Mock(side_effect=AssertionError("SUSPECT must not dispatch"))
    ensure = mock.Mock(side_effect=AssertionError("SUSPECT must not execute"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_SUSPECT,
        dispatch_fn=dispatch,
    ) == RT._PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()
    ensure.assert_not_called()
    assert "拒否" in capsys.readouterr().err


@pytest.mark.parametrize("version", [None, "2.4.9", "invalid"])
def test_compute_xdist_requirement_is_fail_closed_without_pip(
    monkeypatch, version,
):
    ensure = mock.Mock(side_effect=AssertionError("compute must not invoke pip path"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_xdist_version", lambda: version)
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    assert RT.main(
        ["test_target.py"], site=RT.site_policy.PEGASUS_COMPUTE,
    ) == RT._PEGASUS_DISPATCH_RC
    ensure.assert_not_called()


def test_compute_unimportable_xdist_is_fail_closed_without_pip(monkeypatch):
    ensure = mock.Mock(side_effect=AssertionError("compute must not invoke pip path"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_xdist_runtime_importable", lambda: False)
    monkeypatch.setattr(RT, "_ensure_xdist", ensure)
    assert RT.main(
        ["test_target.py"], site=RT.site_policy.PEGASUS_COMPUTE,
    ) == RT._PEGASUS_DISPATCH_RC
    ensure.assert_not_called()


def test_main_assembles_absolute_relative_target_from_other_cwd(
    monkeypatch, tmp_path,
):
    target = tmp_path / "test_sample.py"
    target.write_text("def test_sample(): pass\n", encoding="utf-8")
    captured = {}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)

    def fake_call(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(RT.subprocess, "call", fake_call)
    assert RT.main(
        ["test_sample.py::test_sample"], site=RT.site_policy.OTHER,
    ) == 0
    assert captured["command"] == [
        sys.executable, "-m", "pytest", f"{target.resolve()}::test_sample",
    ]
    assert captured["kwargs"] == {"cwd": str(_REPO)}


def test_main_absolutizes_plain_relative_target_from_other_cwd(
    monkeypatch, tmp_path,
):
    target = tmp_path / "test_sample.py"
    target.write_text("def test_sample(): pass\n", encoding="utf-8")
    captured = {}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda command, **kwargs: captured.update(
            command=command, kwargs=kwargs,
        ) or 0,
    )

    assert RT.main(["test_sample.py"], site=RT.site_policy.OTHER) == 0
    assert captured["command"] == [
        sys.executable, "-m", "pytest", str(target.resolve()),
    ]
    assert captured["kwargs"] == {"cwd": str(_REPO)}


@pytest.mark.parametrize(
    ("args", "expected_tail"),
    [
        (["--rootdir", "."], ["--rootdir", str(_REPO)]),
        (["--deselect=ignored.py::test_node"], ["--deselect=ignored.py::test_node"]),
    ],
)
def test_main_option_values_do_not_suppress_default_target(
    monkeypatch, args, expected_tail,
):
    captured = {}
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda values, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda values, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda values, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda command, **kwargs: captured.update(command=command) or 0,
    )

    assert RT.main(args, site=RT.site_policy.OTHER) == 0
    assert captured["command"] == [
        sys.executable, "-m", "pytest", str(_REPO / "orchestrator" / "tests"),
        *expected_tail,
    ]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
