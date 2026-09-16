# -*- coding: utf-8 -*-
"""tools/run_tests.py の argv 正規化・受入 preflight 回帰。

変異対応: V14 = acceptance の ``PYTEST_ADDOPTS.strip()`` 除去、
V15 = submodule auto-init の ``--no-fetch`` 除去。
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from unittest import mock

import pytest


_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.pegasus import dispatch_compute as DC
from orchestrator.campaign import login_headroom as LH
from orchestrator import test_selection_contract as CONTRACT


_RUNNER = _REPO / "tools" / "run_tests.py"
_SPEC = importlib.util.spec_from_file_location("run_tests_preflight_test", _RUNNER)
assert _SPEC and _SPEC.loader
RT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RT)

_CANONICAL_CLEANUP_EXCLUSION = CONTRACT.Exclusion(
    path=RT._SANCTIONED_CLEANUP_TEST_PATH,
    reason="消滅pid型occupancy issueを3 scan連続観測しcleanup testsがrc22になる",
    release_condition="dev-wave-cleanup-occupancy-churn taskがlandし、明示file走が全緑",
    ruling="2026-08-24 user direct known-red registration",
    set_version="dev-wave-cleanup-occupancy-churn-v1",
)
_CANONICAL_CLEANUP_EXCLUSIONS = (_CANONICAL_CLEANUP_EXCLUSION,)

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
        "IZANAGI_RUN_TESTS_SCOPE_UNIT", "IZANAGI_RUN_TESTS_SCOPE_CAP",
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV,
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV,
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


class _LookupRecordingEnvironment(dict[str, str]):
    """Record key-specific lookups while leaving generic ``items()`` copies alone."""

    def __init__(self, values):
        super().__init__(values)
        self.lookups: list[str] = []

    def __contains__(self, key):
        self.lookups.append(key)
        return super().__contains__(key)

    def __getitem__(self, key):
        self.lookups.append(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.lookups.append(key)
        return super().get(key, default)


def _create_submodule_markers(repo: Path) -> None:
    root = repo / "external" / "ccbench"
    root.mkdir(parents=True, exist_ok=True)
    (root / "CMakeLists.txt").write_text("fixture\n", encoding="utf-8")
    (root / ".git").write_text("gitdir: fixture\n", encoding="utf-8")


def _create_modules_cache(common_dir: Path) -> Path:
    cache = common_dir / "modules" / "external" / "ccbench"
    cache.mkdir(parents=True)
    return cache


def test_default_dispatch_leaves_timeout_kwargs_unset_without_overrides(monkeypatch):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)

    assert RT._default_dispatch(["-q"], environ={}) == 0

    kwargs = dispatch.call_args.kwargs
    assert "queue_wait_timeout_s" not in kwargs
    assert "overall_grace_s" not in kwargs


def test_default_dispatch_applies_queue_wait_timeout_override_independently(
    monkeypatch,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV: "1234.5",
    }

    assert RT._default_dispatch(["-q"], environ=environ) == 0

    kwargs = dispatch.call_args.kwargs
    assert kwargs["queue_wait_timeout_s"] == 1234.5
    assert "overall_grace_s" not in kwargs


def test_default_dispatch_applies_overall_grace_override_independently(
    monkeypatch,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV: "2345.5",
    }

    assert RT._default_dispatch(["-q"], environ=environ) == 0

    kwargs = dispatch.call_args.kwargs
    assert kwargs["overall_grace_s"] == 2345.5
    assert "queue_wait_timeout_s" not in kwargs


def test_default_dispatch_passes_distinct_timeout_overrides_independently(
    monkeypatch,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV: "111",
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV: "222",
    }

    assert RT._default_dispatch(["-q"], environ=environ) == 0

    kwargs = dispatch.call_args.kwargs
    assert kwargs["queue_wait_timeout_s"] == 111.0
    assert kwargs["overall_grace_s"] == 222.0


def test_default_dispatch_allows_zero_timeout_overrides(monkeypatch):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV: "0",
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV: "0",
    }

    assert RT._default_dispatch(["-q"], environ=environ) == 0

    kwargs = dispatch.call_args.kwargs
    assert kwargs["queue_wait_timeout_s"] == 0.0
    assert kwargs["overall_grace_s"] == 0.0


@pytest.mark.parametrize(
    "invalid_value", ["-1", "-1e-324", "nan", "inf", "not-a-number"],
)
def test_default_dispatch_rejects_invalid_queue_wait_timeout_override(
    monkeypatch, invalid_value,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV: invalid_value,
    }

    result = RT._invoke_dispatch(
        RT._default_dispatch, ["-q"], environ=environ,
    )

    assert result.rc == RT._PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()


@pytest.mark.parametrize(
    "invalid_value", ["-1", "-1e-324", "nan", "inf", "not-a-number"],
)
def test_default_dispatch_rejects_invalid_overall_grace_override(
    monkeypatch, invalid_value,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV: invalid_value,
    }

    result = RT._invoke_dispatch(
        RT._default_dispatch, ["-q"], environ=environ,
    )

    assert result.rc == RT._PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()


def test_default_dispatch_applies_walltime_and_timeout_overrides_independently(
    monkeypatch,
):
    dispatch = mock.Mock(return_value=0)
    monkeypatch.setattr(DC, "dispatch", dispatch)
    environ = {
        RT._DISPATCH_WALLTIME_OVERRIDE_ENV: "00:10:00",
        RT._DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV: "111",
        RT._DISPATCH_OVERALL_GRACE_OVERRIDE_ENV: "222",
    }

    assert RT._default_dispatch(["-q"], environ=environ) == 0

    kwargs = dispatch.call_args.kwargs
    assert kwargs["walltime"] == "00:10:00"
    assert kwargs["queue_wait_timeout_s"] == 111.0
    assert kwargs["overall_grace_s"] == 222.0


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


def test_partial_operation_key_differs_for_different_target_sets():
    first = RT._test_operation([
        "orchestrator/tests/test_queue_state.py",
    ])
    second = RT._test_operation([
        "orchestrator/tests/test_queue_state.py",
        "orchestrator/tests/test_login_headroom.py",
    ])

    assert first.startswith("tests-partial-")
    assert second.startswith("tests-partial-")
    assert first != second


def test_partial_operation_key_is_order_independent():
    targets = [
        "orchestrator/tests/test_queue_state.py",
        "orchestrator/tests/test_login_headroom.py",
    ]

    assert RT._test_operation(targets) == RT._test_operation(list(reversed(targets)))


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
        ["--confcutdir", "orchestrator/tests"],
        ["--confcutdir=orchestrator/tests"],
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


def test_nonacceptance_main_warns_once_on_stderr_and_preserves_rc(
    monkeypatch, capsys,
):
    events = []

    def preflight(name):
        return lambda args, repo: events.append(name) or 0

    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions", preflight("deletion"),
    )
    monkeypatch.setattr(RT, "_preflight_ruleops", preflight("ruleops"))
    monkeypatch.setattr(
        RT, "_preflight_submodule", preflight("submodule"),
    )
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda command, **kwargs: events.append("pytest") or 7,
    )

    assert RT.main(["/tmp/target.py"], site=RT.site_policy.OTHER) == 7
    assert events == ["deletion", "ruleops", "submodule", "pytest"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
    )


def test_acceptance_main_does_not_emit_nonacceptance_warning(monkeypatch, capsys):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT.subprocess, "call", lambda command, **kwargs: 7)

    assert RT.main([], site=RT.site_policy.OTHER) == 7
    assert capsys.readouterr() == ("", "")


def test_nonacceptance_reexecution_warns_in_parent_and_child_without_marker(
    monkeypatch, capsys,
):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_xdist_runtime_importable", lambda: True)
    monkeypatch.setattr(RT.subprocess, "call", lambda command, **kwargs: 9)

    def dispatch(args, *, environ):
        return RT.main(args, site=RT.site_policy.PEGASUS_COMPUTE)

    assert RT.main(
        ["/tmp/target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 9
    captured = capsys.readouterr()
    warning = (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
    )
    assert captured.out == ""
    assert captured.err == warning * 2


def test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent(
    monkeypatch, capsys,
):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT.subprocess, "call", lambda command, **kwargs: 9)
    monkeypatch.setattr(RT, "_print_granted_budget", lambda cap, reason: None)

    def run_bounded_child(args, cap, *, recording_session=None):
        with monkeypatch.context() as child:
            child.setenv(
                RT._BOUNDED_SCOPE_UNIT_ENV,
                "izanagi-run-tests-1234-deadbeefdeadbeef.scope",
            )
            child.setenv(RT._BOUNDED_SCOPE_CAP_ENV, str(cap))
            child.setattr(RT, "_bounded_scope_membership", lambda: True)
            rc = RT.main(args, site=RT.site_policy.PEGASUS_LOGIN)
        return RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, rc)

    monkeypatch.setattr(RT, "_run_bounded_scope", run_bounded_child)

    assert RT.main(
        ["/tmp/target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 9
    warning = (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == warning


@pytest.mark.parametrize(
    ("unit", "cap"),
    [
        ("", ""),
        ("izanagi-run-tests-1234-deadbeef.scope", "1234"),
        ("izanagi-run-tests-1234-deadbeefdeadbeef.scope", "01234"),
        ("izanagi-run-tests-1234-deadbeefdeadbeef.scope", "not-a-cap"),
    ],
    ids=["empty", "short-token", "noncanonical-cap", "nonnumeric-cap"],
)
def test_nonacceptance_malformed_bounded_marker_keeps_warning_before_refusal(
    monkeypatch, capsys, unit, cap,
):
    monkeypatch.setenv(RT._BOUNDED_SCOPE_UNIT_ENV, unit)
    monkeypatch.setenv(RT._BOUNDED_SCOPE_CAP_ENV, cap)
    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: False)

    assert RT.main(
        ["/tmp/target.py"], site=RT.site_policy.OTHER,
    ) == RT._PEGASUS_DISPATCH_RC
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
        "bounded scope marker と cgroup の memory.max / memory.oom.group が"
        "一致しないため、テスト実行を拒否します。\n"
    )


def test_nonacceptance_bounded_then_dispatch_warns_in_parent_and_compute_child(
    monkeypatch, capsys,
):
    monkeypatch.delenv(RT._BOUNDED_SCOPE_UNIT_ENV, raising=False)
    monkeypatch.delenv(RT._BOUNDED_SCOPE_CAP_ENV, raising=False)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_xdist_runtime_importable", lambda: True)
    monkeypatch.setattr(RT.subprocess, "call", lambda command, **kwargs: 9)
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CAP_OOM,
        ),
    )
    fingerprint = RT._TreeFingerprint("a" * 64, (1, 2, 3, 4, 5))
    monkeypatch.setattr(
        RT, "_tree_and_submodules_fingerprint", lambda repo: fingerprint,
    )

    def dispatch(args, *, environ):
        assert RT._BOUNDED_SCOPE_UNIT_ENV not in environ
        assert RT._BOUNDED_SCOPE_CAP_ENV not in environ
        with mock.patch.dict(os.environ, environ, clear=True):
            return RT.main(args, site=RT.site_policy.PEGASUS_COMPUTE)

    assert RT.main(
        ["/tmp/target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 9
    warning = (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        warning
        + f"bounded local に与えた予算: {LH.MAX_LOCAL_BUDGET_BYTES} bytes。test\n"
        + warning
    )


@pytest.mark.parametrize(
    ("failed_preflight", "failure_rc", "expected_events"),
    [
        ("deletion", 13, ["deletion"]),
        ("ruleops", 15, ["deletion", "ruleops"]),
        ("submodule", 14, ["deletion", "ruleops", "submodule"]),
    ],
)
def test_nonacceptance_warning_precedes_preflight_error_and_preserves_rc(
    monkeypatch,
    capsys,
    failed_preflight,
    failure_rc,
    expected_events,
):
    events = []

    def preflight(name):
        def run(args, repo):
            events.append(name)
            if name == failed_preflight:
                print(f"{name} preflight error", file=RT.sys.stderr)
                return failure_rc
            return 0

        return run

    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions", preflight("deletion"),
    )
    monkeypatch.setattr(RT, "_preflight_ruleops", preflight("ruleops"))
    monkeypatch.setattr(
        RT, "_preflight_submodule", preflight("submodule"),
    )

    assert RT.main(["/tmp/target.py"], site=RT.site_policy.OTHER) == failure_rc
    assert events == expected_events
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
        f"{failed_preflight} preflight error\n"
    )


def test_nonacceptance_collect_only_main_warns(monkeypatch, capsys):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT.subprocess, "call", lambda command, **kwargs: 0)

    assert RT.main(["--collect-only"], site=RT.site_policy.OTHER) == 0
    assert capsys.readouterr().err == (
        "警告: 受入形でない走行です。"
        "この結果を受入全走として扱わないでください。\n"
    )


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


def test_acceptance_unstaged_deletion_exact_legacy_bypass_is_rejected(
    tmp_path, monkeypatch, capsys,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", "1")
    assert RT._preflight_unstaged_deletions([], repo) == 13
    stderr = capsys.readouterr().err
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "許可して続行" not in stderr


@pytest.mark.parametrize("value", ["true", "01", " 1"])
def test_acceptance_unstaged_deletion_legacy_env_spellings_are_rejected(
    tmp_path, monkeypatch, value,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", value)
    assert RT._preflight_unstaged_deletions([], repo) == 13


def test_acceptance_unstaged_deletion_is_rejected_for_final_trigger(
    tmp_path, monkeypatch, capsys,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    monkeypatch.setenv("IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS", "1")
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    assert RT._preflight_unstaged_deletions([], repo) == 13
    stderr = capsys.readouterr().err
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "許可して続行" not in stderr


def test_acceptance_deletion_preflight_never_reads_legacy_bypass_env(
    tmp_path, monkeypatch,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    environ = _LookupRecordingEnvironment(os.environ)
    legacy_key = "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS"
    environ[legacy_key] = "yes"
    monkeypatch.setattr(RT.os, "environ", environ)

    assert RT._preflight_unstaged_deletions([], repo) == 13
    assert legacy_key not in environ.lookups


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CompletedProcess(["git"], 128, "", "failure"),
        FileNotFoundError("git"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
    ],
    ids=["git-rc-128", "git-file-not-found", "git-unicode-decode"],
)
def test_acceptance_deletion_git_failure_never_reads_legacy_bypass_env(
    tmp_path, monkeypatch, failure,
):
    legacy_key = "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS"
    environ = _LookupRecordingEnvironment(os.environ)
    environ[legacy_key] = "yes"
    monkeypatch.setattr(RT.os, "environ", environ)
    invoked = mock.Mock()
    if isinstance(failure, subprocess.CompletedProcess):
        invoked.return_value = failure
    else:
        invoked.side_effect = failure
    monkeypatch.setattr(RT.subprocess, "run", invoked)

    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    assert legacy_key not in environ.lookups


def test_targeted_run_does_not_invoke_deletion_gate(monkeypatch, tmp_path):
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)
    assert RT._preflight_unstaged_deletions(["/tmp/target.py"], tmp_path) == 0
    invoked.assert_not_called()


def test_targeted_run_with_unstaged_deletion_still_passes(
    monkeypatch, tmp_path,
):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    invoked = mock.Mock(side_effect=AssertionError("git must not run"))
    monkeypatch.setattr(RT.subprocess, "run", invoked)

    assert RT._preflight_unstaged_deletions(["tracked.txt"], repo) == 0
    invoked.assert_not_called()


def test_acceptance_run_passes_after_staged_deletion(tmp_path):
    repo = _tracked_repo(tmp_path)
    (repo / "tracked.txt").unlink()
    _git(repo, "add", "-A")

    staged = _git(repo, "diff", "--cached", "--name-status").stdout
    assert staged.splitlines() == ["D\ttracked.txt"]
    assert RT._preflight_unstaged_deletions([], repo) == 0


def test_dispatch_generated_request_env_drops_legacy_deletion_bypass(tmp_path):
    """親が新規生成する request の environment field だけを検査する。

    実 child process の environment と既存 request を読む側の再検査は射程外。
    """
    output_root = tmp_path / "dispatch"
    run_command = mock.Mock(side_effect=RuntimeError("stop after request write"))
    legacy_key = "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS"

    assert DC.dispatch(
        ["orchestrator/tests/test_run_tests_preflight.py", "-q"],
        repo_root=_REPO,
        output_root=output_root,
        environ={legacy_key: "yes", "PYTEST_ADDOPTS": "-q"},
        run_command=run_command,
        nonce="legacy-env-transport",
    ) == DC.INFRA_RC
    request = json.loads(
        (output_root / "legacy-env-transport" / "request.json").read_text(
            encoding="utf-8",
        ),
    )
    assert request["environment"] == {"PYTEST_ADDOPTS": "-q"}


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


def test_acceptance_deletion_git_rc_failure_fails_closed(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(
        RT.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 128, "", "failure"),
    )
    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    stderr = capsys.readouterr().err
    assert "git rc=128" in stderr
    assert "受入形は未検査" in stderr
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "続行します" not in stderr


def test_acceptance_deletion_git_unavailable_fails_closed(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(
        RT.subprocess, "run", mock.Mock(side_effect=FileNotFoundError("git")),
    )
    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    stderr = capsys.readouterr().err
    assert "実行不能" in stderr
    assert "受入形は未検査" in stderr
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "続行します" not in stderr


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CompletedProcess(["git"], 128, "", "failure"),
        FileNotFoundError("git"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
    ],
)
def test_final_deletion_git_failure_remains_unverified_and_fails_closed(
    monkeypatch, tmp_path, capsys, failure,
):
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    if isinstance(failure, subprocess.CompletedProcess):
        monkeypatch.setattr(RT.subprocess, "run", lambda *a, **kw: failure)
    else:
        monkeypatch.setattr(RT.subprocess, "run", mock.Mock(side_effect=failure))
    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    stderr = capsys.readouterr().err
    assert "受入形は未検査" in stderr
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "続行します" not in stderr


def test_nonfinal_deletion_decode_failure_fails_closed(
    monkeypatch, tmp_path, capsys,
):
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
    monkeypatch.setattr(RT.subprocess, "run", mock.Mock(side_effect=failure))
    assert RT._preflight_unstaged_deletions([], tmp_path) == 13
    stderr = capsys.readouterr().err
    assert "実行不能" in stderr
    assert "受入形は未検査" in stderr
    assert "git add -A" in stderr
    assert "復元" in stderr
    assert "続行します" not in stderr


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
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 7
    assert events == [
        "deletion", "ruleops", "submodule", ("dispatch", ["test_target.py"]),
    ]


def test_force_dispatch_login_bypasses_headroom_and_queue_after_preflights(
    monkeypatch,
):
    """禁止署名: 強制時は admission を読まず 13→15→14→dispatch とする。"""

    events = []

    def preflight(name):
        def run(args, repo):
            assert args == ["test_target.py"]
            events.append(name)
            return 0

        return run

    def dispatch(args, *, environ):
        events.append(("dispatch", list(args)))
        return 7

    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: None)
    monkeypatch.setattr(
        LH,
        "grant_budget",
        mock.Mock(side_effect=AssertionError("headroom must not be read")),
    )
    monkeypatch.setattr(
        RT,
        "_queue_dispatch_possible",
        mock.Mock(side_effect=AssertionError("queue must not be read")),
    )
    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions", preflight("deletion"),
    )
    monkeypatch.setattr(RT, "_preflight_ruleops", preflight("ruleops"))
    monkeypatch.setattr(RT, "_preflight_submodule", preflight("submodule"))

    assert RT.main(
        ["--force-dispatch", "test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 7
    assert events == [
        "deletion", "ruleops", "submodule", ("dispatch", ["test_target.py"]),
    ]


def test_without_force_dispatch_login_with_headroom_still_runs_local(
    monkeypatch,
):
    """通る正例: 無指定の LOGIN は余裕があれば local 実行を保つ。"""

    grant = mock.Mock(return_value=(LH.Admission.LOCAL, 1234, "test"))
    scope = mock.Mock(
        return_value=RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )
    monkeypatch.setattr(LH, "grant_budget", grant)
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)
    monkeypatch.setattr(
        RT,
        "_queue_dispatch_possible",
        mock.Mock(side_effect=AssertionError("local headroom needs no queue")),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
    ) == 0
    grant.assert_called_once_with(operation=RT._test_operation(["test_target.py"]))
    scope.assert_called_once_with(
        ["test_target.py"], 1234, recording_session=mock.ANY,
    )


def test_default_login_admission_calls_login_headroom_grant_budget(monkeypatch):
    grant = mock.Mock(return_value=(LH.Admission.DISPATCH, None, "test"))
    dispatch = mock.Mock(return_value=7)
    monkeypatch.setattr(LH, "grant_budget", grant)
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 7
    grant.assert_called_once_with(operation=RT._test_operation(["test_target.py"]))


def test_invalid_granted_budget_falls_back_to_dispatch(monkeypatch):
    dispatch = mock.Mock(return_value=7)
    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (LH.Admission.LOCAL, None, "test"),
    )
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(
        RT, "_run_bounded_scope",
        mock.Mock(side_effect=AssertionError("scope must not start")),
    )
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 7
    dispatch.assert_called_once()


@pytest.mark.parametrize(
    ("headroom_available", "queue_available", "expected"),
    [
        (True, True, "local"),
        (True, False, "local"),
        (False, True, "dispatch"),
        (False, False, "local"),
    ],
)
def test_login_headroom_and_queue_four_quadrants(
    monkeypatch,
    headroom_available,
    queue_available,
    expected,
):
    grants = []
    queue_checks = []
    caps = []
    dispatch = mock.Mock(return_value=7)

    def grant_budget(**kwargs):
        grants.append(kwargs)
        if headroom_available:
            return LH.Admission.LOCAL, 2000, "観測余裕=2000 bytes"
        if kwargs.get("min_bytes") == 0:
            return LH.Admission.LOCAL, 500, "観測余裕=500 bytes"
        return LH.Admission.DISPATCH, None, "観測余裕=500 bytes"

    def queue_status():
        queue_checks.append(True)
        return queue_available, "キュー gen_S は ENA=DIS、STS=INA"

    def run_scope(args, cap, *, recording_session=None):
        caps.append(cap)
        return RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0)

    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(RT, "_queue_dispatch_possible", queue_status)
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        run_scope,
    )
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)

    rc = RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    )

    assert rc == (0 if expected == "local" else 7)
    assert len(queue_checks) == (0 if headroom_available else 1)
    operation = RT._test_operation(["test_target.py"])
    expected_grants = (
        [{"operation": operation}]
        if headroom_available or queue_available
        else [
            {"operation": operation},
            {"min_bytes": 0, "operation": operation},
        ]
    )
    assert grants == expected_grants
    assert caps == ([2000 if headroom_available else 500] if expected == "local" else [])
    assert dispatch.call_count == (1 if expected == "dispatch" else 0)


def test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch(
    monkeypatch,
    capsys,
):
    # Parallel shards may create untracked files; this case assumes no tree change.
    fingerprint = RT._TreeFingerprint("a" * 64, (0, 0, 0, 0, 0))
    monkeypatch.setattr(
        RT, "_tree_and_submodules_fingerprint", lambda repo: fingerprint,
    )

    def grant_budget(**kwargs):
        if kwargs.get("min_bytes") == 0:
            return LH.Admission.LOCAL, 500, "観測余裕=500 bytes"
        return LH.Admission.DISPATCH, None, "観測余裕=500 bytes"

    dispatch = mock.Mock(side_effect=AssertionError("must not dispatch"))
    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(
        RT,
        "_queue_dispatch_possible",
        lambda: (False, "キュー gen_S は ENA=DIS、STS=INA"),
    )
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CAP_OOM,
        ),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == RT._PEGASUS_DISPATCH_RC
    error = capsys.readouterr().err
    assert "ログインの余裕もキューも無いため、いまは実行できません" in error
    assert "500 bytes" in error
    assert "ENA=DIS" in error
    assert "STS=INA" in error
    dispatch.assert_not_called()


def test_headroom_short_queue_unavailable_zero_budget_stops(monkeypatch, capsys):
    def grant_budget(**kwargs):
        reason = "予約控除後の観測余裕=0 bytes、現在使用量=99 bytes、実効天井=99 bytes"
        return LH.Admission.DISPATCH, None, reason

    dispatch = mock.Mock(side_effect=AssertionError("must not dispatch"))
    scope = mock.Mock(side_effect=AssertionError("scope must not start"))
    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(
        RT,
        "_queue_dispatch_possible",
        lambda: (False, "キュー gen_S は ENA=ENA、STS=INA"),
    )
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == RT._PEGASUS_DISPATCH_RC
    error = capsys.readouterr().err
    assert "0 bytes" in error
    assert "ENA=ENA" in error
    assert "STS=INA" in error
    dispatch.assert_not_called()
    scope.assert_not_called()


def test_queue_state_import_failure_is_treated_as_dispatch_available(
    monkeypatch,
):
    real_import = RT.importlib.import_module

    def fail_queue_state(name, *args, **kwargs):
        if name == "orchestrator.campaign.queue_state":
            raise ImportError("injected")
        return real_import(name, *args, **kwargs)

    dispatch = mock.Mock(return_value=9)
    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (LH.Admission.DISPATCH, None, "観測余裕=0 bytes"),
    )
    monkeypatch.setattr(RT.importlib, "import_module", fail_queue_state)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 9
    dispatch.assert_called_once()


def test_m7_local_enters_scope_before_parent_preflights(monkeypatch):
    events = []
    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions",
        lambda a, r: events.append("deletion") or 0,
    )
    monkeypatch.setattr(
        RT, "_preflight_ruleops", lambda a, r: events.append("ruleops") or 0,
    )
    monkeypatch.setattr(
        RT, "_preflight_submodule",
        lambda a, r: events.append("submodule") or 0,
    )
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: events.append("scope")
        or RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 0
    assert events == ["scope"]


def test_scope_argv_uses_only_supported_memory_properties():
    cap = LH.RESERVE_BYTES // 2
    unit = "izanagi-run-tests-1234-deadbeef.scope"
    command = RT._scope_command(
        ["test_target.py"], cap, unit, script_path=_RUNNER,
    )

    assert command == [
        "systemd-run", "--user", "--scope", "-q", f"--unit={unit}",
        "-p", "MemoryAccounting=yes", "-p", f"MemoryMax={cap}",
        "-p", "MemorySwapMax=0", "--",
        sys.executable, str(_RUNNER.resolve()), "test_target.py",
    ]
    assert all("MemoryOOMGroup" not in arg for arg in command)


def test_login_outcome_vocabulary_is_exactly_four_values():
    assert {outcome.value for outcome in RT._ScopeOutcome} == {
        "child_rc", "cap_oom", "headroom_short", "dispatch_infra",
    }


def test_scope_marker_requires_matching_cgroup_cap_and_oom_group(
    monkeypatch, tmp_path,
):
    unit = "izanagi-run-tests-1234-deadbeef.scope"
    cap = LH.RESERVE_BYTES // 2
    proc = tmp_path / "self.cgroup"
    proc.write_text(
        f"0::/user.slice/user-123.slice/app.slice/{unit}\n",
        encoding="utf-8",
    )
    cgroup_root = tmp_path / "cgroup"
    scope = cgroup_root / "user.slice" / "user-123.slice" / "app.slice" / unit
    scope.mkdir(parents=True)
    (scope / "memory.max").write_text(f"{cap}\n", encoding="utf-8")
    (scope / "memory.oom.group").write_text("0\n", encoding="utf-8")
    monkeypatch.setenv(RT._BOUNDED_SCOPE_UNIT_ENV, unit)
    monkeypatch.setenv(RT._BOUNDED_SCOPE_CAP_ENV, str(cap))
    monkeypatch.setattr(RT, "_PROC_SELF_CGROUP", proc)
    monkeypatch.setattr(RT, "_CGROUP_ROOT", cgroup_root)

    assert RT._bounded_scope_membership() is True
    assert (scope / "memory.oom.group").read_text(encoding="utf-8") == "1\n"
    (scope / "memory.max").write_text(f"{cap + 1}\n", encoding="utf-8")
    assert RT._bounded_scope_membership() is False


def _write_scope_properties(
    scope: Path,
    memory_max: str,
    *,
    oom_group: str = "1",
) -> None:
    (scope / "memory.max").write_text(f"{memory_max}\n", encoding="utf-8")
    (scope / "memory.oom.group").write_text(f"{oom_group}\n", encoding="utf-8")


_FULLWIDTH_DIGIT_TRANSLATION = str.maketrans(
    "0123456789",
    "０１２３４５６７８９",
)


def _stub_page_size(name: str, value: object) -> object:
    assert name == "SC_PAGE_SIZE", (
        f"unexpected os.sysconf key {name!r}; expected 'SC_PAGE_SIZE'"
    )
    return value


def _fullwidth_decimal(value: int) -> str:
    return str(value).translate(_FULLWIDTH_DIGIT_TRANSLATION)


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
def test_scope_properties_accept_page_floor_and_reject_other_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
):
    cap = 3 * page_size + page_size // 4 + 17
    floor = cap - cap % page_size
    assert cap % page_size != 0
    assert floor != cap
    monkeypatch.setattr(
        RT.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()

    _write_scope_properties(scope, str(floor))
    assert RT._scope_properties_are_enforced(scope, cap) is True
    _write_scope_properties(scope, str(cap))
    assert RT._scope_properties_are_enforced(scope, cap) is True

    for rejected in (
        str(cap + 1),
        str(floor + 1),
        str(floor - 1),
        str(cap - 1),
        "max",
        "",
        "   ",
        f"+{cap}",
        f"0{cap}",
        _fullwidth_decimal(cap),
        _fullwidth_decimal(floor),
    ):
        _write_scope_properties(scope, rejected)
        assert RT._scope_properties_are_enforced(scope, cap) is False

    _write_scope_properties(scope, str(floor), oom_group="0")
    assert RT._scope_properties_are_enforced(scope, cap) is False


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
@pytest.mark.parametrize(
    "invalid_page_size",
    [
        pytest.param(OSError("unavailable"), id="oserror"),
        pytest.param(ValueError("unavailable"), id="valueerror"),
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="none"),
        pytest.param("4096", id="string"),
    ],
)
def test_scope_properties_sysconf_failure_or_invalid_is_exact_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
    invalid_page_size: object,
):
    cap = 3 * page_size + page_size // 4 + 17
    floor = cap - cap % page_size
    assert cap % page_size != 0
    assert floor != cap
    monkeypatch.setattr(
        RT.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()
    _write_scope_properties(scope, str(floor))
    assert RT._scope_properties_are_enforced(scope, cap) is True

    if isinstance(invalid_page_size, BaseException):
        def fail_sysconf(name: str) -> int:
            _stub_page_size(name, None)
            raise invalid_page_size

        monkeypatch.setattr(RT.os, "sysconf", fail_sysconf)
    else:
        monkeypatch.setattr(
            RT.os,
            "sysconf",
            lambda name: _stub_page_size(name, invalid_page_size),
        )
    _write_scope_properties(scope, str(floor))
    assert RT._scope_properties_are_enforced(scope, cap) is False
    _write_scope_properties(scope, str(cap))
    assert RT._scope_properties_are_enforced(scope, cap) is True


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
def test_scope_properties_preserve_cap_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
):
    detector_cap = 3 * page_size + page_size // 4 + 17
    detector_floor = detector_cap - detector_cap % page_size
    assert detector_cap % page_size != 0
    assert detector_floor != detector_cap
    monkeypatch.setattr(
        RT.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()
    _write_scope_properties(scope, str(detector_floor))
    assert RT._scope_properties_are_enforced(scope, detector_cap) is True

    for cap, accepted, rejected in (
        (1, ("1", "0"), ("2",)),
        (page_size, (str(page_size),), (str(page_size - 1),)),
        (
            page_size + 1,
            (str(page_size + 1), str(page_size)),
            (str(page_size - 1), str(page_size + 2)),
        ),
        (0, ("0",), (str(-page_size),)),
        (-1, ("-1",), (str(-page_size),)),
    ):
        for memory_max in accepted:
            _write_scope_properties(scope, memory_max)
            assert RT._scope_properties_are_enforced(scope, cap) is True
        for memory_max in rejected:
            _write_scope_properties(scope, memory_max)
            assert RT._scope_properties_are_enforced(scope, cap) is False

    monkeypatch.setattr(
        RT.os,
        "sysconf",
        lambda _name: (_ for _ in ()).throw(
            AssertionError("nonpositive cap must not query page size"),
        ),
    )
    for cap in (0, -1):
        _write_scope_properties(scope, str(cap))
        assert RT._scope_properties_are_enforced(scope, cap) is True


@pytest.mark.parametrize(
    ("failure", "readback", "expected_events"),
    [
        ("write", "1\n", ["write"]),
        ("read", "1\n", ["write", "read"]),
        (None, "0\n", ["write", "read"]),
    ],
)
def test_scope_oom_group_write_and_readback_fail_closed(
    failure, readback, expected_events,
):
    events = []

    class OomGroupFile:
        def write_text(self, value, *, encoding):
            events.append("write")
            assert (value, encoding) == ("1\n", "utf-8")
            if failure == "write":
                raise OSError("injected write failure")

        def read_text(self, *, encoding):
            events.append("read")
            assert encoding == "utf-8"
            if failure == "read":
                raise OSError("injected read failure")
            return readback

    class Scope:
        def __truediv__(self, name):
            assert name == "memory.oom.group"
            return OomGroupFile()

    assert RT._attest_scope_oom_group(Scope()) is False
    assert events == expected_events


def test_failed_scope_oom_attestation_refuses_child_with_infra_rc(
    monkeypatch, capsys,
):
    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: False)
    monkeypatch.setattr(
        RT,
        "_preflight_unstaged_deletions",
        mock.Mock(side_effect=AssertionError("child must fail before pytest")),
    )

    assert RT.main(["test_target.py"], site=RT.site_policy.OTHER) == 16
    assert "memory.oom.group" in capsys.readouterr().err


def test_local_child_test_failure_never_falls_back(monkeypatch):
    dispatch = mock.Mock(side_effect=AssertionError("test red must not fallback"))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CHILD_RC, 5,
        ),
    )
    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions",
        mock.Mock(side_effect=AssertionError("parent preflight must not run")),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 5
    dispatch.assert_not_called()


def test_cap_oom_dirty_before_unchanged_after_dispatches_once(monkeypatch):
    """回帰: 開始時点の dirty は、local 試行が不変なら fallback を妨げない。"""

    dispatch = mock.Mock(return_value=9)
    dirty = RT._TreeFingerprint("a" * 64, (91, 127, 44, 0, 0))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CAP_OOM,
        ),
    )
    fingerprint = mock.Mock(side_effect=[dirty, dirty])
    monkeypatch.setattr(RT, "_tree_and_submodules_fingerprint", fingerprint)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 9
    assert fingerprint.call_count == 2
    dispatch.assert_called_once()


def test_cap_oom_changed_tree_does_not_dispatch(monkeypatch, capsys):
    dispatch = mock.Mock(side_effect=AssertionError("changed tree must not dispatch"))
    before = RT._TreeFingerprint("a" * 64, (91, 127, 44, 0, 0))
    after = RT._TreeFingerprint("b" * 64, (112, 203, 44, 0, 0))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CAP_OOM,
        ),
    )
    monkeypatch.setattr(
        RT,
        "_tree_and_submodules_fingerprint",
        mock.Mock(side_effect=[before, after]),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == RT._PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()
    error = capsys.readouterr().err
    assert "状態が変化" in error
    assert "aaaaaaaaaaaa -> bbbbbbbbbbbb" in error


def test_cap_oom_fingerprint_failure_does_not_dispatch(monkeypatch, capsys):
    dispatch = mock.Mock(side_effect=AssertionError("unknown state must not dispatch"))
    after = RT._TreeFingerprint("a" * 64, (91, 127, 44, 0, 0))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.CAP_OOM,
        ),
    )
    monkeypatch.setattr(
        RT,
        "_tree_and_submodules_fingerprint",
        mock.Mock(side_effect=[None, after]),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == RT._PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()
    assert "指紋を安全に取得できませんでした" in capsys.readouterr().err


def test_scope_disappearance_after_sample_keeps_child_rc(
    monkeypatch, tmp_path, capsys,
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return 1

    process.wait.side_effect = wait
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)

    def cgroup_path(path, unit):
        return None if state["disappeared"] else tmp_path

    def attest(path):
        assert not state["disappeared"], "post-run re-attestation is forbidden"
        return True

    def properties(path, cap):
        assert not state["disappeared"], "post-run property read is forbidden"
        return True

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 424242

    monkeypatch.setattr(RT, "_scope_cgroup_path", cgroup_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", attest)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", properties)
    monkeypatch.setattr(RT, "_read_scope_current", current)

    def events(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 0, 0

    monkeypatch.setattr(RT, "_read_scope_events", events)
    grant = mock.Mock()
    remember = mock.Mock()
    monkeypatch.setattr(LH, "remember_peak", remember)
    token = RT._scope_accounting.set(
        RT._ScopeAccounting(LH, "tests-partial", grant),
    )

    try:
        result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)
    finally:
        RT._scope_accounting.reset(token)
    assert result == RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 1)
    assert "bounded scope の観測ピーク: 424242 bytes" in capsys.readouterr().err
    grant.bind_scope.assert_called_once_with(tmp_path)
    remember.assert_called_once_with("tests-partial", 424242)


def test_scope_without_any_successful_event_sample_is_dispatch_infra(
    monkeypatch, tmp_path,
):
    process = mock.Mock(pid=4242)
    process.poll.return_value = None
    process.wait.return_value = 3
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", lambda path, cap: True)
    monkeypatch.setattr(RT, "_read_scope_current", lambda path: 1)
    monkeypatch.setattr(
        RT, "_read_scope_events", mock.Mock(side_effect=OSError("unreadable")),
    )

    result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)
    assert result == RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)


@pytest.mark.parametrize(
    ("oom_group_attested", "properties_attested"),
    [(False, True), (True, False)],
)
def test_scope_attestation_failure_stops_scope_and_is_dispatch_infra(
    monkeypatch, tmp_path, oom_group_attested, properties_attested,
):
    process = mock.Mock(pid=4242)
    process.poll.return_value = None
    stop = mock.Mock()
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(
        RT, "_attest_scope_oom_group", lambda path: oom_group_attested,
    )
    monkeypatch.setattr(
        RT,
        "_scope_properties_are_enforced",
        lambda path, cap: properties_attested,
    )
    monkeypatch.setattr(RT, "_stop_bounded_scope", stop)

    result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)

    assert result == RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)
    stop.assert_called_once_with(process, mock.ANY)
    process.wait.assert_not_called()


def test_continuing_samples_retain_cap_oom_and_highest_peak(
    monkeypatch, tmp_path, capsys,
):
    state = {"disappeared": False, "event_reads": 0, "current_reads": 0}
    second_sample = threading.Event()
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        assert second_sample.wait(1), "sampler did not continue to a second sample"
        state["disappeared"] = True
        return 137

    process.wait.side_effect = wait
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", lambda path, cap: True)

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        state["current_reads"] += 1
        return 100 if state["current_reads"] == 1 else 900

    def events(path):
        if state["disappeared"]:
            return 1, 1
        state["event_reads"] += 1
        if state["event_reads"] == 1:
            return 0, 0
        second_sample.set()
        return 1, 1

    monkeypatch.setattr(RT, "_read_scope_current", current)
    monkeypatch.setattr(RT, "_read_scope_events", events)
    grant = mock.Mock()
    remember = mock.Mock()
    monkeypatch.setattr(LH, "remember_peak", remember)
    token = RT._scope_accounting.set(
        RT._ScopeAccounting(LH, "tests-full", grant),
    )

    cap = LH.RESERVE_BYTES // 2
    try:
        result = RT._run_bounded_scope(["test_target.py"], cap)
    finally:
        RT._scope_accounting.reset(token)
    assert result == RT._ScopeResult(RT._ScopeOutcome.CAP_OOM)
    assert "bounded scope の観測ピーク: 900 bytes" in capsys.readouterr().err
    grant.bind_scope.assert_called_once_with(tmp_path)
    remember.assert_called_once_with("tests-full", cap)


@pytest.mark.parametrize("returncode", [137, -9], ids=["rc137", "sigkill"])
def test_signal_exit_without_final_cap_proof_is_dispatch_infra(
    monkeypatch, tmp_path, returncode,
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return returncode

    process.wait.side_effect = wait
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", lambda path, cap: True)
    monkeypatch.setattr(RT, "_read_scope_current", lambda path: 1)

    def events(path):
        if state["disappeared"]:
            raise OSError("scope disappeared before final events")
        return 0, 0

    monkeypatch.setattr(RT, "_read_scope_events", events)

    result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)
    assert result == RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        ((1, 0), RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)),
        ((0, 1), RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)),
        ((1, 1), RT._ScopeResult(RT._ScopeOutcome.CAP_OOM)),
    ],
)
def test_cap_oom_requires_both_max_and_oom_events(
    monkeypatch, tmp_path, events, expected,
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return 137

    process.wait.side_effect = wait
    monkeypatch.setattr(RT.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", lambda path, cap: True)

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 1

    def read_events(path):
        return events

    monkeypatch.setattr(RT, "_read_scope_current", current)
    monkeypatch.setattr(RT, "_read_scope_events", read_events)

    result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)
    assert result == expected


def test_login_headroom_import_failure_falls_back_to_dispatch(monkeypatch):
    real_import = RT.importlib.import_module

    def fail_login_headroom(name, *args, **kwargs):
        if name == "orchestrator.campaign.login_headroom":
            raise ImportError("injected")
        return real_import(name, *args, **kwargs)

    dispatch = mock.Mock(return_value=6)
    monkeypatch.setattr(RT.importlib, "import_module", fail_login_headroom)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 6
    dispatch.assert_called_once()


@pytest.mark.parametrize("flag", sorted(_EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS))
def test_login_dispatch_exemption_is_exact_closed_set(monkeypatch, flag):
    assert RT._PEGASUS_DISPATCH_EXEMPT_FLAGS == (
        _EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS
    )
    assert RT._has_dispatch_exempt_flag([flag]) is True


@pytest.mark.parametrize(
    "flag",
    sorted(_EXPECTED_PEGASUS_DISPATCH_EXEMPT_FLAGS - {"--help", "--version"}),
)
def test_login_non_immediate_dispatch_exempt_flags_enter_bounded_scope(
    monkeypatch, flag,
):
    scope = mock.Mock(
        return_value=RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )
    dispatch = mock.Mock(side_effect=AssertionError("local budget was granted"))
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        [flag],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 0
    scope.assert_called_once_with(
        [flag], LH.MAX_LOCAL_BUDGET_BYTES, recording_session=mock.ANY,
    )
    dispatch.assert_not_called()


def test_login_collect_only_from_pytest_addopts_enters_bounded_scope(
    monkeypatch,
):
    scope = mock.Mock(
        return_value=RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        [],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 0
    scope.assert_called_once_with(
        [], LH.MAX_LOCAL_BUDGET_BYTES, recording_session=mock.ANY,
    )


def test_login_collect_only_dispatches_when_bounded_budget_is_denied(
    monkeypatch,
):
    dispatch = mock.Mock(return_value=9)
    scope = mock.Mock(side_effect=AssertionError("denied budget must not run local"))
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        ["--collect-only"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 9
    scope.assert_not_called()
    dispatch.assert_called_once()


def test_login_help_bypasses_bounded_scope_and_dispatch(monkeypatch):
    scope = mock.Mock(side_effect=AssertionError("help must not enter scope"))
    dispatch = mock.Mock(side_effect=AssertionError("help must not dispatch"))
    admission = mock.Mock(side_effect=AssertionError("help needs no budget"))
    monkeypatch.setattr(RT, "_bounded_scope_membership", lambda: None)
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    call = mock.Mock(return_value=0)
    monkeypatch.setattr(RT.subprocess, "call", call)

    assert RT.main(
        ["--help"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=admission,
    ) == 0
    scope.assert_not_called()
    dispatch.assert_not_called()
    admission.assert_not_called()
    assert "--help" in call.call_args.args[0]


def test_bounded_scope_exemption_is_only_help_and_version(monkeypatch):
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    assert RT._PEGASUS_BOUNDED_SCOPE_EXEMPT_FLAGS == {"--help", "--version"}
    assert RT._has_bounded_scope_exempt_flag(["--help"])
    assert RT._has_bounded_scope_exempt_flag(["--version"])
    for flag in ("--collect-only", "--fixtures", "--markers", "--help=extra"):
        assert not RT._has_bounded_scope_exempt_flag([flag])


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
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 3
    dispatch.assert_called_once()


def test_previous_full_cap_estimate_dispatches_without_local_scope(monkeypatch):
    grants = []
    dispatch = mock.Mock(return_value=9)
    scope = mock.Mock(side_effect=AssertionError("estimated full run must dispatch"))
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "1")

    def grant_budget(**kwargs):
        grants.append(kwargs)
        return LH.Admission.DISPATCH, None, "前回の全走は cap 到達"

    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        [], site=RT.site_policy.PEGASUS_LOGIN, dispatch_fn=dispatch,
    ) == 9
    assert grants == [{"operation": "tests-full"}]
    scope.assert_not_called()
    dispatch.assert_called_once()


def test_previous_full_cap_estimate_dispatches_after_preflights(monkeypatch):
    events = []
    monkeypatch.setenv(RT._ACCEPTANCE_SHARDS_ENV, "1")

    def preflight(name):
        return lambda args, repo: events.append(name) or 0

    def dispatch(args, *, environ):
        events.append(("dispatch", list(args)))
        return 9

    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (
            LH.Admission.DISPATCH, None, "前回の全走は cap 到達",
        ),
    )
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(
        RT, "_preflight_unstaged_deletions", preflight("deletion"),
    )
    monkeypatch.setattr(RT, "_preflight_ruleops", preflight("ruleops"))
    monkeypatch.setattr(RT, "_preflight_submodule", preflight("submodule"))

    assert RT.main(
        [], site=RT.site_policy.PEGASUS_LOGIN, dispatch_fn=dispatch,
    ) == 9
    assert events == [
        "deletion", "ruleops", "submodule", ("dispatch", []),
    ]


def test_small_partial_estimate_still_tries_local_scope(monkeypatch):
    grants = []
    scope = mock.Mock(
        return_value=RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )

    def grant_budget(**kwargs):
        grants.append(kwargs)
        return LH.Admission.LOCAL, 1234, "小さい前回ピーク"

    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(RT, "_run_bounded_scope", scope)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
    ) == 0
    assert grants == [{"operation": RT._test_operation(["test_target.py"])}]
    scope.assert_called_once_with(
        ["test_target.py"], 1234, recording_session=mock.ANY,
    )


def test_login_local_scope_releases_budget_lease_on_infra(monkeypatch):
    lease = mock.Mock()
    grant = LH.BudgetGrant(LH.Admission.LOCAL, 1234, "test", lease)
    monkeypatch.setattr(LH, "grant_budget", lambda **kwargs: grant)
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, *, recording_session=None: RT._ScopeResult(
            RT._ScopeOutcome.DISPATCH_INFRA,
        ),
    )

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("infra must stop")),
    ) == RT._PEGASUS_DISPATCH_RC
    lease.release.assert_called_once_with()


def test_login_local_scope_releases_budget_lease_on_interrupt(monkeypatch):
    lease = mock.Mock()
    grant = LH.BudgetGrant(LH.Admission.LOCAL, 1234, "test", lease)
    monkeypatch.setattr(LH, "grant_budget", lambda **kwargs: grant)
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        mock.Mock(side_effect=KeyboardInterrupt),
    )

    with pytest.raises(KeyboardInterrupt):
        RT.main(
            ["test_target.py"],
            site=RT.site_policy.PEGASUS_LOGIN,
            dispatch_fn=mock.Mock(side_effect=AssertionError("must not dispatch")),
        )
    lease.release.assert_called_once_with()


def test_peak_and_lease_bookkeeping_failures_are_best_effort():
    broken = mock.Mock()
    broken.bind_scope.side_effect = RuntimeError("bind failed")
    broken.release.side_effect = RuntimeError("release failed")
    module = mock.Mock()
    module.remember_peak.side_effect = RuntimeError("write failed")

    RT._safe_bind_scope(broken, Path("/sys/fs/cgroup/test.scope"))
    RT._safe_release_grant(broken)
    RT._safe_remember_peak(module, "tests-partial", 1)


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


def test_force_dispatch_suspect_still_returns_infra_rc(monkeypatch):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))

    assert RT.main(
        ["--force-dispatch", "test_target.py"],
        site=RT.site_policy.PEGASUS_SUSPECT,
        dispatch_fn=mock.Mock(side_effect=AssertionError("suspect must not dispatch")),
    ) == RT._PEGASUS_DISPATCH_RC


@pytest.mark.parametrize(
    "site", [RT.site_policy.PEGASUS_COMPUTE, RT.site_policy.OTHER],
)
def test_force_dispatch_compute_and_other_run_locally_without_pytest_leak(
    monkeypatch, site,
):
    commands = []
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_xdist_runtime_importable", lambda: True)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda command, **kwargs: commands.append(command) or 0,
    )

    assert RT.main(
        ["--force-dispatch", "test_target.py"],
        site=site,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must run locally")),
    ) == 0
    assert len(commands) == 1
    assert "--force-dispatch" not in commands[0]


def test_suspect_refusal_observes_queue_once_and_includes_unavailable_hint(
    monkeypatch, capsys,
):
    queue_status = mock.Mock(return_value=(
        False,
        "キュー gen_S は ENA=DIS、STS=INAで、現在利用できません。",
    ))
    monkeypatch.setattr(RT, "_queue_dispatch_possible", queue_status)
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_SUSPECT,
    ) == RT._PEGASUS_DISPATCH_RC

    queue_status.assert_called_once_with()
    error = capsys.readouterr().err
    assert "ENA=DIS" in error
    assert "STS=INA" in error
    assert "性能測定は現時点では実施できません" in error


def test_suspect_never_enters_local_admission(monkeypatch):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_SUSPECT,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must not dispatch")),
        admit_fn=mock.Mock(side_effect=AssertionError("must not admit local")),
    ) == RT._PEGASUS_DISPATCH_RC


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
        sys.executable, "-m", "pytest",
        f"{target.resolve()}::test_sample",
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
        sys.executable, "-m", "pytest",
        str(target.resolve()),
    ]
    assert captured["kwargs"] == {"cwd": str(_REPO)}


@pytest.mark.parametrize(
    ("args", "expected_tail", "expected_exclusion"),
    [
        (
            ["--rootdir", "."],
            ["--rootdir", str(_REPO)],
            True,
        ),
        (
            ["--deselect=ignored.py::test_node"],
            ["--deselect=ignored.py::test_node"],
            False,
        ),
    ],
)
@pytest.mark.parametrize(
    "table_active",
    [True, False],
    ids=("active-table", "empty-table"),
)
def test_main_option_values_do_not_suppress_default_target(
    monkeypatch, args, expected_tail, expected_exclusion, table_active,
):
    entries = _CANONICAL_CLEANUP_EXCLUSIONS if table_active else ()
    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", entries)
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
    expected_exclusion = expected_exclusion and table_active
    expected_command = [sys.executable, "-m", "pytest"]
    if expected_exclusion:
        expected_command.append(f"--ignore={RT._SANCTIONED_CLEANUP_TEST_PATH}")
    expected_command.extend([
        str(_REPO / "orchestrator" / "tests"),
        *expected_tail,
    ])
    assert captured["command"] == expected_command


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
