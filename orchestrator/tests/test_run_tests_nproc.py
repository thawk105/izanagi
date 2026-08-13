# -*- coding: utf-8 -*-
"""tools/run_tests.py の並列度・loadgroup command 組立て回帰 + positive control。

`_default_nproc` は環境 (使えるコア数) に自動追従し、上限 `_NPROC_CAP` で頭打ち、
環境変数 IZANAGI_TEST_NPROC で上書きできる。恒真化 (何を渡しても同じ値) に化けて
いないことを、入力ごとに異なる期待値を pin して固定する。
pytest でも 素の `python3 orchestrator/tests/test_run_tests_nproc.py` でも走る。
"""
from __future__ import annotations

import importlib.util
import contextlib
import io
import os
import sys
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "tools" / "run_tests.py"
_spec = importlib.util.spec_from_file_location("run_tests", _RUNNER)
assert _spec and _spec.loader
RT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RT)


def _with_env(monkeypatch_value):
    if monkeypatch_value is None:
        os.environ.pop("IZANAGI_TEST_NPROC", None)
    else:
        os.environ["IZANAGI_TEST_NPROC"] = monkeypatch_value


def _restore(saved):
    if saved is None:
        os.environ.pop("IZANAGI_TEST_NPROC", None)
    else:
        os.environ["IZANAGI_TEST_NPROC"] = saved


def test_available_cpus_positive_and_affinity_bounded():
    n = RT._available_cpus()
    assert n >= 1
    # affinity 尊重: 使えるコア数は物理総数を超えない
    assert n <= (os.cpu_count() or n)


def test_default_is_available_capped():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        _with_env(None)
        assert RT._default_nproc() == max(1, min(RT._available_cpus(), RT._NPROC_CAP))
        # 上限を超えない
        assert RT._default_nproc() <= RT._NPROC_CAP
    finally:
        _restore(saved)


def test_m2_compute_default_uses_full_affinity_while_other_keeps_cap():
    # M2: COMPUTE 分岐を消して常に cap すると、この 48 != 32 の境界が赤になる。
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        _with_env(None)
        with mock.patch.object(RT.site_policy, "available_cpus", return_value=48):
            assert RT._default_nproc(site=RT.site_policy.PEGASUS_COMPUTE) == 48
            assert RT._default_nproc(site=RT.site_policy.OTHER) == RT._NPROC_CAP
    finally:
        _restore(saved)


def test_env_max_removes_cap():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        for token in ("max", "all", "MAX"):
            _with_env(token)
            assert RT._default_nproc() == max(1, RT._available_cpus())
    finally:
        _restore(saved)


def test_env_numeric_override_wins_over_cap():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        # 上限より大きい明示値もそのまま採用 (ユーザーの明示上書きが最優先)
        _with_env(str(RT._NPROC_CAP + 9))
        assert RT._default_nproc() == RT._NPROC_CAP + 9
        _with_env("3")
        assert RT._default_nproc() == 3
    finally:
        _restore(saved)


def test_env_garbage_falls_back_to_default():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        expected = max(1, min(RT._available_cpus(), RT._NPROC_CAP))
        for token in ("", "  ", "abc", "0", "-4", "3.5"):
            _with_env(token)
            assert RT._default_nproc() == expected, token
    finally:
        _restore(saved)


_FIXTURE_PYTHON = "/fixture/python"
_FIXTURE_TARGET = "/fixture/orchestrator/tests"


def _command(args, *, use_xdist=True, has_target=False, default_nproc=7):
    return RT._build_pytest_command(
        args,
        use_xdist=use_xdist,
        default_nproc=default_nproc,
        has_target=has_target,
        python_executable=_FIXTURE_PYTHON,
        default_target=_FIXTURE_TARGET,
    )


def _acceptance_env():
    return mock.patch.dict(
        os.environ, {"PYTEST_ADDOPTS": "", "PYTEST_PLUGINS": ""},
    )


def test_build_command_xdist_default_uses_loadgroup():
    assert _command([]) == [
        _FIXTURE_PYTHON, "-m", "pytest", _FIXTURE_TARGET,
        "-n", "7", "--dist", "loadgroup",
    ]


def test_build_command_without_xdist_is_serial():
    assert _command([], use_xdist=False) == [
        _FIXTURE_PYTHON, "-m", "pytest", _FIXTURE_TARGET,
    ]


def test_build_command_recognizes_all_parallel_nproc_spellings():
    for args in (
        ["-n", "4"],
        ["-n4"],
        ["--numprocesses=4"],
    ):
        assert _command(args) == [
            _FIXTURE_PYTHON, "-m", "pytest", _FIXTURE_TARGET,
            "--dist", "loadgroup", *args,
        ], args


def test_build_command_n0_disables_loadgroup_injection():
    assert _command(["-n0"]) == [
        _FIXTURE_PYTHON, "-m", "pytest", _FIXTURE_TARGET, "-n0",
    ]


def test_build_command_nonacceptance_user_dist_is_postposed_and_wins():
    target = "test_file.py::test_node"
    args = ["--dist", "load", target]
    assert _command(args, has_target=True) == [
        _FIXTURE_PYTHON, "-m", "pytest",
        "-n", "7", "--dist", "loadgroup", "--dist", "load", target,
    ]


def test_build_command_explicit_target_omits_default_target():
    target = "orchestrator/tests/test_campaign.py::test_source_digest_parse_options_defaults"
    assert _command([target], has_target=True) == [
        _FIXTURE_PYTHON, "-m", "pytest", "-n", "7",
        "--dist", "loadgroup", target,
    ]


def test_xdist_loadgroup_version_gate():
    assert RT._xdist_supports_loadgroup("2.5.0")
    assert RT._xdist_supports_loadgroup("3.8.0")
    assert not RT._xdist_supports_loadgroup("2.4.0")
    assert not RT._xdist_supports_loadgroup(None)
    assert not RT._xdist_supports_loadgroup("not-a-version")


def test_main_warns_on_user_dist_override_without_reordering_args():
    stderr = io.StringIO()
    captured = {}

    def fake_call(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return 0

    target = "test_file.py::test_node"
    args = ["-n4", "--dist", "load", target]
    with mock.patch.object(RT, "_ensure_xdist", return_value=True), \
            mock.patch.object(RT, "_xdist_version", return_value="3.8.0"), \
            mock.patch.object(RT, "_preflight_unstaged_deletions", return_value=0), \
            mock.patch.object(RT, "_preflight_submodule", return_value=0), \
            mock.patch.object(RT.subprocess, "call", side_effect=fake_call), \
            contextlib.redirect_stderr(stderr):
        assert RT.main(args, site=RT.site_policy.OTHER) == 0

    assert "警告" in stderr.getvalue()
    assert "--dist loadgroup" in stderr.getvalue()
    assert captured["command"][-len(args):] == args
    assert captured["kwargs"] == {"cwd": str(_REPO)}


def test_dist_stays_nonselect_for_acceptance_classification():
    with _acceptance_env():
        assert "--dist" in RT._NONSELECT_VALUE_OPTIONS
        assert RT._is_acceptance_run(["--dist", "load"])


def test_main_rejects_acceptance_dist_split_with_rc17():
    stderr = io.StringIO()
    with _acceptance_env(), contextlib.redirect_stderr(stderr):
        assert RT.main(["--dist", "load"], site=RT.site_policy.OTHER) == 17
    assert "--dist loadgroup 以外" in stderr.getvalue()


def test_main_rejects_acceptance_dist_equals_spelling():
    with _acceptance_env():
        assert RT.main(["--dist=load"], site=RT.site_policy.OTHER) == 17


def test_acceptance_dist_rejection_precedes_preflight_and_xdist():
    preflight_deletions = mock.Mock(
        side_effect=AssertionError("deletion preflight must not run"),
    )
    preflight_ruleops = mock.Mock(
        side_effect=AssertionError("RuleOps preflight must not run"),
    )
    preflight_submodule = mock.Mock(
        side_effect=AssertionError("submodule preflight must not run"),
    )
    ensure_xdist = mock.Mock(
        side_effect=AssertionError("xdist setup must not run"),
    )
    dispatch = mock.Mock(
        side_effect=AssertionError("dispatch must not run"),
    )
    with _acceptance_env(), mock.patch.object(
        RT, "_preflight_unstaged_deletions", preflight_deletions,
    ), mock.patch.object(
        RT, "_preflight_ruleops", preflight_ruleops,
    ), mock.patch.object(
        RT, "_preflight_submodule", preflight_submodule,
    ), mock.patch.object(
        RT, "_ensure_xdist", ensure_xdist,
    ):
        assert RT.main(
            ["--force-dispatch", "--dist", "load"],
            site=RT.site_policy.PEGASUS_LOGIN,
            dispatch_fn=dispatch,
        ) == 17
    preflight_deletions.assert_not_called()
    preflight_ruleops.assert_not_called()
    preflight_submodule.assert_not_called()
    ensure_xdist.assert_not_called()
    dispatch.assert_not_called()


def test_main_rejects_unsafe_dist_even_when_loadgroup_is_last():
    with _acceptance_env():
        assert RT.main(
            ["--dist", "load", "--dist", "loadgroup"],
            site=RT.site_policy.OTHER,
        ) == 17


def test_main_rejects_unsafe_dist_with_n0_serial_shape():
    with _acceptance_env():
        assert RT.main(
            ["-n0", "--dist", "load"], site=RT.site_policy.OTHER,
        ) == 17


def test_main_allows_explicit_acceptance_loadgroup():
    captured = []

    def fake_call(command, **kwargs):
        captured.append((command, kwargs))
        return 0

    with _acceptance_env(), \
            mock.patch.object(RT, "_bounded_scope_membership", return_value=None), \
            mock.patch.object(RT, "_preflight_unstaged_deletions", return_value=0), \
            mock.patch.object(RT, "_preflight_ruleops", return_value=0), \
            mock.patch.object(RT, "_preflight_submodule", return_value=0), \
            mock.patch.object(RT, "_ensure_xdist", return_value=True), \
            mock.patch.object(RT, "_xdist_version", return_value="3.8.0"), \
            mock.patch.object(RT.subprocess, "call", side_effect=fake_call):
        for args in (
            ["--dist", "loadgroup"],
            ["--dist=loadgroup"],
            ["--dist", "loadgroup", "--dist=loadgroup"],
        ):
            assert RT.main(args, site=RT.site_policy.OTHER) == 0

    assert len(captured) == 3
    for (command, kwargs), args in zip(captured, (
        ["--dist", "loadgroup"],
        ["--dist=loadgroup"],
        ["--dist", "loadgroup", "--dist=loadgroup"],
    )):
        assert command[-len(args):] == args
        assert kwargs == {"cwd": str(_REPO)}


def test_acceptance_shape_is_false_when_pytest_plugins_is_set():
    with mock.patch.dict(
        os.environ,
        {"PYTEST_ADDOPTS": "", "PYTEST_PLUGINS": "scheduler_override"},
    ):
        assert not RT._is_acceptance_run([])


def test_acceptance_shape_ignores_blank_pytest_plugins():
    with mock.patch.dict(
        os.environ, {"PYTEST_ADDOPTS": "", "PYTEST_PLUGINS": " \t\n"},
    ):
        assert RT._is_acceptance_run([])


def test_other_preserves_cap_no_dispatch_and_legacy_xdist_pip_path():
    ensure = mock.Mock(return_value=False)
    dispatch = mock.Mock(side_effect=AssertionError("OTHER must not dispatch"))
    captured = {}

    def fake_call(command, **kwargs):
        captured["command"] = command
        return 0

    with mock.patch.object(RT, "_ensure_xdist", ensure), \
            mock.patch.object(RT, "_preflight_unstaged_deletions", return_value=0), \
            mock.patch.object(RT, "_preflight_ruleops", return_value=0), \
            mock.patch.object(RT, "_preflight_submodule", return_value=0), \
            mock.patch.object(RT.subprocess, "call", side_effect=fake_call):
        assert RT.main(
            ["fixture.py"], site=RT.site_policy.OTHER, dispatch_fn=dispatch,
        ) == 0

    ensure.assert_called_once_with()
    dispatch.assert_not_called()
    assert "-n" not in captured["command"]
    with mock.patch.object(RT.site_policy, "available_cpus", return_value=96):
        assert RT._default_nproc(site=RT.site_policy.OTHER) == 32


def test_legacy_xdist_installer_still_uses_user_pip_command():
    completed = type("Completed", (), {"returncode": 0})()
    with mock.patch.object(
        RT, "_xdist_installed", side_effect=(False, True),
    ), mock.patch.object(
        RT.subprocess, "run", return_value=completed,
    ) as invoked:
        assert RT._ensure_xdist()
    invoked.assert_called_once_with(
        [
            sys.executable, "-m", "pip", "install", "--user", "--quiet",
            "pytest-xdist",
        ],
        timeout=120,
    )


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                fails += 1
                print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if fails else 0)
