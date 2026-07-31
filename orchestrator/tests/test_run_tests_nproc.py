# -*- coding: utf-8 -*-
"""tools/run_tests.py の並列度・loadgroup command 組立て回帰 + positive control。

`_default_nproc` は環境 (使えるコア数) に自動追従し、上限 `_NPROC_CAP` で頭打ち、
環境変数 IZANAGI_TEST_NPROC で上書きできる。恒真化 (何を渡しても同じ値) に化けて
いないことを、入力ごとに異なる期待値を pin して固定する。
pytest でも 素の `python3 orchestrator/tests/test_run_tests_nproc.py` でも走る。
"""
from __future__ import annotations

import importlib.util
import importlib
import builtins
import contextlib
import io
import os
from pathlib import Path
import tempfile
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


def test_runner_uses_canonical_policy_module_identity():
    assert RT.pegasus_policy is importlib.import_module("pegasus_policy")


def test_module_import_does_not_import_packaging():
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "packaging" or name.startswith("packaging."):
            raise AssertionError("packaging imported before xdist version branch")
        return real_import(name, *args, **kwargs)

    with mock.patch.object(builtins, "__import__", side_effect=guarded):
        spec = importlib.util.spec_from_file_location("run_tests_lazy_packaging", _RUNNER)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module._wrapper_local_response(["--version"]) == 0


def test_compute_default_uses_full_affinity_and_rejects_oversubscribe():
    saved = RT._CURRENT_SITE
    saved_env = os.environ.pop("IZANAGI_TEST_NPROC", None)
    try:
        RT._CURRENT_SITE = RT.pegasus_policy.classify_site(
            "bnode114", "0:123.nqsv", range(48),
        )
        assert RT._default_nproc() == 48
        try:
            RT._validate_explicit_nproc(["-n", "49"], RT._CURRENT_SITE)
        except RT.pegasus_policy.SitePolicyError:
            pass
        else:
            raise AssertionError("compute oversubscription was accepted")
        assert RT._validate_explicit_nproc(["-n0"], RT._CURRENT_SITE) == 0
        assert RT._validate_explicit_nproc(["-n", "48"], RT._CURRENT_SITE) == 48
        for args in (
            ["-n", "auto"],
            ["--numprocesses", "logical"],
            ["--numprocesses=AUTO"],
        ):
            assert RT._validate_explicit_nproc(args, RT._CURRENT_SITE) == 48
    finally:
        RT._CURRENT_SITE = saved
        if saved_env is not None:
            os.environ["IZANAGI_TEST_NPROC"] = saved_env


def test_other_preserves_xdist_auto_and_logical_spellings():
    observation = RT.pegasus_policy.classify_site(
        "developer-workstation", None, range(8),
    )
    assert observation.site_kind is RT.pegasus_policy.OTHER
    for args in (
        ["-n", "auto"],
        ["--numprocesses", "logical"],
        ["--numprocesses=AUTO"],
    ):
        assert RT._validate_explicit_nproc(args, observation) is None


def test_compute_symbolic_nproc_uses_u1_resolver_for_actual_pytest_argv():
    saved_site = RT._CURRENT_SITE
    observation = RT.pegasus_policy.classify_site(
        "bnode114", "0:123.nqsv", range(48),
    )
    dispatcher = importlib.import_module("pegasus.test_dispatch")
    captured = {}
    resolver_calls = []
    symbolic_results = {"auto": 37, "logical": 29}

    def fake_call(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return 0

    def resolve_test_workers(explicit_workers, actual_observation):
        assert actual_observation is observation
        resolver_calls.append(explicit_workers)
        if explicit_workers in symbolic_results:
            return symbolic_results[explicit_workers]
        raise AssertionError(
            f"symbolic U1 resolver was bypassed: {explicit_workers!r}"
        )

    try:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "pre-submit-authorization.json"
            marker.write_text("{}\n", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"IZANAGI_TEST_WORKER_AUTH": str(marker)},
                clear=False,
            ), mock.patch.object(
                RT, "_observe_runner_site", return_value=observation,
            ), mock.patch.object(
                RT.pegasus_policy,
                "resolve_test_workers",
                side_effect=resolve_test_workers,
            ), mock.patch.object(
                dispatcher, "authorize_runner", return_value={"bound": True},
            ), mock.patch.object(
                RT, "_ensure_xdist", return_value=True,
            ), mock.patch.object(
                RT, "_xdist_version", return_value="3.8.0",
            ), mock.patch.object(
                RT, "_preflight_unstaged_deletions", return_value=0,
            ), mock.patch.object(
                RT, "_preflight_ruleops", return_value=0,
            ), mock.patch.object(
                RT, "_preflight_submodule", return_value=0,
            ), mock.patch.object(
                RT.subprocess, "call", side_effect=fake_call,
            ), mock.patch.object(
                RT,
                "_finish_compute_runner",
                side_effect=lambda _authorization, **kwargs: kwargs[
                    "runner_exit_status"
                ],
            ):
                os.environ.pop("IZANAGI_TASK_RUN_ID", None)
                os.environ.pop("IZANAGI_TASK_RUNS_ROOT", None)
                for args, option, symbolic in (
                    (["-n", "auto"], "-n", "auto"),
                    (
                        ["--numprocesses", "logical"],
                        "--numprocesses",
                        "logical",
                    ),
                ):
                    captured.clear()
                    resolver_calls.clear()
                    assert RT.main(args) == 0
                    assert symbolic not in captured["command"]
                    index = captured["command"].index(option)
                    assert captured["command"][index:index + 2] == [
                        option,
                        str(symbolic_results[symbolic]),
                    ]
                    assert captured["kwargs"] == {"cwd": str(_REPO)}
                    assert resolver_calls == [symbolic, symbolic]
    finally:
        RT._CURRENT_SITE = saved_site


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


def test_build_command_user_dist_is_postposed_and_wins():
    args = ["--dist", "load"]
    assert _command(args) == [
        _FIXTURE_PYTHON, "-m", "pytest", _FIXTURE_TARGET,
        "-n", "7", "--dist", "loadgroup", "--dist", "load",
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
    other = RT.pegasus_policy.classify_site(
        "unit-test.invalid", None, range(4),
    )
    with mock.patch.object(RT, "_observe_runner_site", return_value=other), \
            mock.patch.object(RT, "_ensure_xdist", return_value=True), \
            mock.patch.object(RT, "_xdist_version", return_value="3.8.0"), \
            mock.patch.object(RT, "_preflight_unstaged_deletions", return_value=0), \
            mock.patch.object(RT, "_preflight_submodule", return_value=0), \
            mock.patch.object(RT.subprocess, "call", side_effect=fake_call), \
            contextlib.redirect_stderr(stderr):
        assert RT.main(args) == 0

    assert "警告" in stderr.getvalue()
    assert "--dist loadgroup" in stderr.getvalue()
    assert captured["command"][-len(args):] == args
    assert captured["kwargs"] == {"cwd": str(_REPO)}


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
