# -*- coding: utf-8 -*-
"""Automatic run_tests observation wiring and fail-open signal contracts."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from tools.pegasus import dispatch_compute as DC
from tools import task_runs
from tools.task_runs import AutomaticRun
from tools.task_runs import pytest_stats as PS
from orchestrator.campaign import login_headroom as LH


_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "tools" / "run_tests.py"
_SPEC = importlib.util.spec_from_file_location("run_tests_testops_observation", _RUNNER)
assert _SPEC and _SPEC.loader
RT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RT)


@pytest.fixture(autouse=True)
def _clean_observation_env(monkeypatch):
    for name in (
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR",
        "IZANAGI_TEST_TRIGGER",
        "IZANAGI_TASK_RUN_AUTO_RECORD",
        "PYTEST_ADDOPTS",
        "IZANAGI_RUN_TESTS_SCOPE_UNIT",
        "IZANAGI_RUN_TESTS_SCOPE_CAP",
    ):
        monkeypatch.delenv(name, raising=False)


def _run(tmp_path: Path, *, sidecar: Path | None = None) -> AutomaticRun:
    generation = tmp_path / "generation-000001"
    generation.mkdir(exist_ok=True)
    return AutomaticRun(
        generation_root=generation,
        task_run_id="20260819-pytest-run-01234567",
        generation_name=generation.name,
        sidecar_path=sidecar,
    )


def _patch_direct(monkeypatch, events):
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: events.append("deletion") or 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: events.append("ruleops") or 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: events.append("submodule") or 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)


def test_unset_id_starts_one_lazy_auto_run_after_preflight(monkeypatch, tmp_path):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    events: list[str] = []
    sidecar = tmp_path / "pytest-stats.json"
    run = _run(tmp_path, sidecar=sidecar)
    _patch_direct(monkeypatch, events)

    def start(repo_root):
        events.append("start")
        assert repo_root == _REPO
        return run, None

    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    monkeypatch.setattr(
        task_runs,
        "finish_automatic_test_run",
        lambda value, outcome: events.append(("finish", outcome)) or None,
    )
    records = []
    monkeypatch.setattr(
        RT,
        "_record_task_run",
        lambda **kwargs: records.append(kwargs) or (True, None),
    )

    def child(command, **kwargs):
        events.append("child")
        assert kwargs["env"][RT._TASK_RUN_AUTO_RECORD_ENV] == "0"
        assert kwargs["env"][RT._TASK_RUN_SIDECAR_ENV] == str(sidecar)
        return 3

    monkeypatch.setattr(RT.subprocess, "call", child)
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 3
    assert events[:5] == [
        "deletion", "ruleops", "submodule", "start", "child",
    ]
    assert events[-1] == ("finish", "completed")
    assert len(records) == 1
    assert records[0]["trigger"] == "unspecified"
    assert records[0]["task_run_id"] == run.task_run_id


def test_explicit_auto_off_preserves_exact_pytest_argv_and_call_shape(monkeypatch):
    monkeypatch.setenv("IZANAGI_TASK_RUN_AUTO_RECORD", "0")
    events = []
    _patch_direct(monkeypatch, events)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_default_nproc", lambda *, site: 4)
    start = mock.Mock(side_effect=AssertionError("explicit opt-out must not start"))
    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    called = []
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda *args, **kwargs: called.append((args, kwargs)) or 7,
    )

    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 7
    assert called == [(([
        sys.executable, "-m", "pytest",
        f"--ignore={_REPO / 'orchestrator' / 'tests' / 'test_sort_swo_oracle.py'}",
        str(_REPO / "orchestrator" / "tests"),
        "-n", "4", "--dist", "loadgroup", "-q",
    ],), {"cwd": str(_REPO)})]
    start.assert_not_called()


def test_four_gate_truth_table_is_fixed_literal_across_recording_routes(
    monkeypatch,
):
    # This table is the acceptance contract.  It deliberately does not derive
    # expected values from the implementation or compare two calls to it.
    cases = [
        (
            "direct-full",
            [],
            "",
            None,
            (True, False, False, True),
        ),
        (
            "direct-quiet",
            ["-q"],
            "",
            None,
            (True, False, False, True),
        ),
        (
            "direct-target",
            ["orchestrator/tests/test_x.py"],
            "",
            None,
            (False, False, False, False),
        ),
        (
            "selector",
            ["-k", "private"],
            "",
            None,
            (False, False, False, False),
        ),
        (
            "unknown-option",
            ["--unknown-option"],
            "",
            None,
            (False, False, False, False),
        ),
        (
            "dispatch",
            ["--force-dispatch", "orchestrator/tests/test_x.py"],
            "",
            None,
            (False, False, False, False),
        ),
        (
            "bounded-scope",
            ["orchestrator/tests/test_x.py"],
            "",
            "izanagi-run-tests-1234-deadbeef.scope",
            (False, False, False, False),
        ),
        (
            "addopts-selector",
            [],
            "-k private",
            None,
            (False, False, False, False),
        ),
        (
            "addopts-no-execution",
            [],
            "--collect-only",
            None,
            (False, True, True, False),
        ),
        (
            "addopts-dispatch-exempt",
            [],
            "--help",
            None,
            (False, True, True, False),
        ),
        (
            "addopts-unknown-option",
            [],
            "--unknown-option",
            None,
            (False, False, False, False),
        ),
        (
            "acceptance-target",
            ["orchestrator/tests"],
            "",
            None,
            (False, False, False, True),
        ),
        (
            "acceptance-nodeid",
            ["orchestrator/tests/test_x.py::test_y"],
            "",
            None,
            (False, False, False, False),
        ),
    ]
    for label, argv, addopts, scope_unit, expected in cases:
        if addopts:
            monkeypatch.setenv("PYTEST_ADDOPTS", addopts)
        else:
            monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
        if scope_unit is None:
            monkeypatch.delenv(RT._BOUNDED_SCOPE_UNIT_ENV, raising=False)
        else:
            monkeypatch.setenv(RT._BOUNDED_SCOPE_UNIT_ENV, scope_unit)
            monkeypatch.setenv(RT._BOUNDED_SCOPE_CAP_ENV, "1024")
        args, _force_dispatch = RT._consume_runner_options(argv)
        actual = (
            RT._is_full_suite(args),
            RT._has_no_execution_flag(args),
            RT._has_dispatch_exempt_flag(args),
            RT._is_acceptance_run(args),
        )
        assert actual == expected, label


def test_four_gate_values_survive_real_recording_routes(monkeypatch, tmp_path):
    """direct/dispatch/scope の実入口で recording 前後の gate を固定する。"""

    def gates(args):
        return (
            RT._is_full_suite(args),
            RT._has_no_execution_flag(args),
            RT._has_dispatch_exempt_flag(args),
            RT._is_acceptance_run(args),
        )

    run = _run(tmp_path)
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    monkeypatch.setattr(task_runs, "start_automatic_test_run", lambda _root: (run, None))
    monkeypatch.setattr(task_runs, "finish_automatic_test_run", lambda *_args: None)
    monkeypatch.setattr(RT, "_record_task_run", lambda **kwargs: (True, None))
    monkeypatch.setattr(RT.subprocess, "call", lambda *args, **kwargs: 0)

    direct_args = ["-q"]
    direct_before = gates(direct_args)
    RT._call_and_record(
        [sys.executable, "-m", "pytest"],
        direct_args,
        recording_session=RT._RecordingSession(repo_root=tmp_path),
    )
    assert direct_before == (True, False, False, True)
    assert gates(direct_args) == direct_before

    dispatch_args = ["target.py"]
    dispatch_before = gates(dispatch_args)
    RT._dispatch_and_record(
        lambda args, *, environ: DC._DispatchResult(0, child_started=True),
        dispatch_args,
        environ=RT._dispatch_environment(),
        recording_session=RT._RecordingSession(repo_root=tmp_path),
    )
    assert dispatch_before == (False, False, False, False)
    assert gates(dispatch_args) == dispatch_before

    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, **kwargs: RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )
    scope_args = ["target.py"]
    scope_before = gates(scope_args)
    RT._run_bounded_scope_and_record(
        scope_args,
        1024,
        recording_session=RT._RecordingSession(repo_root=tmp_path),
    )
    assert scope_before == (False, False, False, False)
    assert gates(scope_args) == scope_before


def test_bootstrap_failure_emits_diagnostic_and_preserves_rc_output(
    monkeypatch, capsys,
):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    _patch_direct(monkeypatch, [])
    monkeypatch.setattr(
        task_runs,
        "start_automatic_test_run",
        mock.Mock(side_effect=OSError("private path must not leak")),
    )

    def child(command, **kwargs):
        print("child stdout")
        print("child stderr", file=sys.stderr)
        return 5

    monkeypatch.setattr(RT.subprocess, "call", child)
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 5
    captured = capsys.readouterr()
    assert "child stdout\n" in captured.out
    assert "IZANAGI_TASK_RUN_DIAGNOSTIC_V1" not in captured.out
    assert "child stderr\n" in captured.err
    assert "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:filesystem\n" in captured.err
    assert "private path must not leak" not in captured.err
    assert str(_REPO) not in captured.err


def test_diagnostic_is_bounded_and_contains_no_path_selector_or_nodeid(capsys):
    RT._emit_recording_diagnostic("recording-unavailable:sidecar")
    output = capsys.readouterr().err
    assert output == "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:sidecar\n"
    assert "selector" not in output
    assert "::" not in output
    assert "/" not in output


def test_direct_child_receives_auto_off_and_sidecar(monkeypatch, tmp_path):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    sidecar = tmp_path / "pytest-stats.json"
    run = _run(tmp_path, sidecar=sidecar)
    monkeypatch.setattr(task_runs, "start_automatic_test_run", lambda _root: (run, None))
    monkeypatch.setattr(task_runs, "finish_automatic_test_run", lambda *_: None)
    _patch_direct(monkeypatch, [])
    records = []
    monkeypatch.setattr(RT, "_record_task_run", lambda **kwargs: records.append(kwargs) or (True, None))

    def child(command, **kwargs):
        assert kwargs["env"][RT._TASK_RUN_AUTO_RECORD_ENV] == "0"
        assert kwargs["env"][RT._TASK_RUN_SIDECAR_ENV] == str(sidecar)
        assert "IZANAGI_TASK_RUN_ID" not in kwargs["env"]
        assert "IZANAGI_TASK_RUNS_ROOT" not in kwargs["env"]
        return 0

    monkeypatch.setattr(RT.subprocess, "call", child)
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 0
    assert records[0]["sidecar"] == sidecar
    assert records[0]["sidecar_required"] is True


def _make_privacy_repo(root: Path) -> tuple[Path, Path]:
    repo = root / "privacy-repo"
    test_dir = repo / "orchestrator" / "tests"
    test_dir.mkdir(parents=True)
    sentinel_path = test_dir / "sentinel-path-PRIVATE_REPO_FILE.py"
    sentinel_path.write_text(
        "def test_placeholder():" + chr(10) + "    pass" + chr(10),
        encoding="utf-8",
    )
    (repo / "README.md").write_text("privacy fixture" + chr(10), encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "privacy-test",
        "GIT_AUTHOR_EMAIL": "privacy-test@example.invalid",
        "GIT_COMMITTER_NAME": "privacy-test",
        "GIT_COMMITTER_EMAIL": "privacy-test@example.invalid",
    })
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", "privacy-fixture"],
    ):
        subprocess.run(
            command, cwd=repo, env=env, check=True,
            capture_output=True, text=True,
        )
    return repo, sentinel_path


def test_entrypoint_privacy_sentinel_absent_from_all_recording_routes(
    monkeypatch, tmp_path, capsys,
):
    """実 entry point の direct/dispatch/bounded 生成 bytes を横断検査する。"""

    sentinel_selector = "SECRET_SELECTOR_PRIVATE"
    sentinel_node_id = "SECRET_NODE_ID_PRIVATE"
    sentinel_argv = "SECRET_ARGV_PRIVATE"
    routes = ("direct", "dispatch", "bounded")
    real_session = RT._RecordingSession
    real_start = task_runs.start_automatic_test_run
    real_popen = subprocess.Popen

    for route in routes:
        case = tmp_path / route
        case.mkdir()
        repo, sentinel_path = _make_privacy_repo(case)
        runs = []
        sidecar_bytes = []
        child_args = [
            str(sentinel_path) + "::" + sentinel_node_id,
            "-k", sentinel_selector,
            "--sentinel-argv", sentinel_argv,
        ]

        with monkeypatch.context() as scoped:
            scoped.setattr(RT, "_REPO", str(repo))
            scoped.setattr(
                RT, "_DEFAULT_TARGET", str(repo / "orchestrator" / "tests"),
            )
            dispatch_transport = case / "dispatch-transport"
            dispatch_transport.mkdir()
            os.chmod(dispatch_transport, 0o700)
            dispatch_sidecar = dispatch_transport / "pytest-stats.json"

            def session_with_transport(*args, **kwargs):
                session = real_session(repo_root=repo, *args, **kwargs)
                session.set_manual_sidecar(dispatch_sidecar)
                return session

            scoped.setattr(
                RT, "_RecordingSession",
                session_with_transport,
            )

            def start(repo_root, _start=real_start):
                result = _start(repo_root)
                if result[0] is not None:
                    runs.append(result[0])
                return result

            scoped.setattr(task_runs, "start_automatic_test_run", start)
            _patch_direct(scoped, [])

            def write_sidecar(path):
                sidecar = Path(path)
                PS._create_sidecar(sidecar, {
                    "collected": 1,
                    "passed": 1,
                    "failed": 0,
                    "skipped": 0,
                    "collected_node_digest": "abcdef123456",
                })
                sidecar_bytes.append(sidecar.read_bytes())

            if route == "direct":
                scoped.setattr(
                    RT.subprocess, "call",
                    lambda command, **kwargs: (
                        write_sidecar(kwargs["env"][RT._TASK_RUN_SIDECAR_ENV])
                        or 0
                    ),
                )
                assert RT.main(child_args, site=RT.site_policy.OTHER) == 0
            elif route == "dispatch":
                def dispatch(args, *, environ):
                    write_sidecar(environ[RT._TASK_RUN_SIDECAR_ENV])
                    return DC._DispatchResult(0, child_started=True)

                assert RT.main(
                    ["--force-dispatch", *child_args],
                    site=RT.site_policy.PEGASUS_LOGIN,
                    dispatch_fn=dispatch,
                ) == 0
            else:
                process = mock.Mock(pid=1234)

                def wait_and_write():
                    assert runs
                    write_sidecar(runs[0].sidecar_path)
                    return 0

                process.wait.side_effect = wait_and_write
                samples = RT._ScopeSamples()
                samples.attested = True
                samples.cgroup = case
                samples.last_events = (0, 0)
                samples.ready.set()
                scoped.setattr(
                    RT, "_bounded_scope_membership", lambda: None,
                )
                scoped.setattr(
                    RT, "_evaluate_login_admission",
                    lambda *args, **kwargs: (
                        None, 1024, None, "injected", mock.Mock(),
                    ),
                )
                scoped.setattr(
                    RT, "_tree_and_submodules_fingerprint",
                    lambda repo: mock.sentinel.privacy_fingerprint,
                )
                scoped.setattr(
                    RT, "_start_scope_sampler",
                    lambda *args: (samples, mock.Mock()),
                )
                def popen(command, *args, **kwargs):
                    if (
                        isinstance(command, (list, tuple))
                        and command
                        and command[0] == "systemd-run"
                    ):
                        return process
                    return real_popen(command, *args, **kwargs)

                scoped.setattr(RT.subprocess, "Popen", popen)
                assert RT.main(
                    child_args, site=RT.site_policy.PEGASUS_LOGIN,
                ) == 0

            assert len(runs) == 1
            task_dir = Path(runs[0].generation_root) / runs[0].task_run_id
            generated = b"".join(
                path.read_bytes()
                for path in (task_dir / "task.json", task_dir / "events.jsonl")
            )
            generated += b"".join(sidecar_bytes)
            generated += capsys.readouterr().err.encode("utf-8")
            for sentinel in (
                str(sentinel_path), sentinel_selector,
                sentinel_node_id, sentinel_argv,
            ):
                assert sentinel.encode("utf-8") not in generated, (
                    route, sentinel,
                )


def test_force_dispatch_consumes_shared_sidecar_once(monkeypatch, tmp_path):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    sidecar = tmp_path / "pytest-stats.json"
    run = _run(tmp_path, sidecar=sidecar)
    real_session = RT._RecordingSession
    def session_with_transport(*args, **kwargs):
        session = real_session(*args, **kwargs)
        session.set_manual_sidecar(sidecar)
        return session
    monkeypatch.setattr(RT, "_RecordingSession", session_with_transport)
    monkeypatch.setattr(task_runs, "start_automatic_test_run", lambda _root: (run, None))
    finishes = []
    monkeypatch.setattr(
        task_runs,
        "finish_automatic_test_run",
        lambda value, outcome: finishes.append((value, outcome)) or None,
    )
    records = []
    monkeypatch.setattr(RT, "_record_task_run", lambda **kwargs: records.append(kwargs) or (True, None))
    for name in ("_preflight_unstaged_deletions", "_preflight_ruleops", "_preflight_submodule"):
        monkeypatch.setattr(RT, name, lambda _args, _repo: 0)

    def dispatch(args, *, environ):
        assert environ[RT._TASK_RUN_AUTO_RECORD_ENV] == "0"
        assert environ[RT._TASK_RUN_SIDECAR_ENV] == str(sidecar)
        assert "IZANAGI_TASK_RUN_ID" not in environ
        assert "IZANAGI_TASK_RUNS_ROOT" not in environ
        return DC._DispatchResult(4, child_started=True)

    assert RT.main(
        ["--force-dispatch", "target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 4
    assert len(records) == 1
    assert records[0]["sidecar"] == sidecar
    assert records[0]["trigger"] == "unspecified"
    assert len(finishes) == 1


@pytest.mark.parametrize(
    ("receipt_name", "receipt"),
    [
        ("missing", 0),
        ("false", DC._DispatchResult(0, child_started=False)),
    ],
)
def test_dispatch_without_strict_child_started_is_diagnostic_only(
    monkeypatch, tmp_path, capsys, receipt_name, receipt,
):
    """qsub 後でも child 起動証拠が無ければ automatic task-run を作らない。"""

    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    start = mock.Mock(side_effect=AssertionError("receipt must precede start"))
    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    record = mock.Mock()
    monkeypatch.setattr(RT, "_record_task_run", record)
    session = RT._RecordingSession(repo_root=tmp_path)

    result = RT._dispatch_and_record(
        lambda args, *, environ: receipt,
        ["target.py"],
        environ=RT._dispatch_environment(session),
        recording_session=session,
    )

    assert result == 0, receipt_name
    start.assert_not_called()
    record.assert_not_called()
    assert capsys.readouterr().err == (
        "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 "
        "recording-unavailable:dispatch-no-child\n"
    )


def test_dispatch_starts_task_run_only_after_strict_child_receipt(
    monkeypatch, tmp_path,
):
    events = []
    run = _run(tmp_path)
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    monkeypatch.setattr(
        task_runs,
        "start_automatic_test_run",
        lambda _root: events.append("start") or (run, None),
    )
    monkeypatch.setattr(
        RT,
        "_record_task_run",
        lambda **kwargs: events.append("record") or (True, None),
    )
    monkeypatch.setattr(task_runs, "finish_automatic_test_run", lambda *_args: None)

    def dispatch(args, *, environ):
        events.append("dispatch")
        return DC._DispatchResult(0, child_started=True)

    result = RT._dispatch_and_record(
        dispatch,
        ["target.py"],
        environ=RT._dispatch_environment(),
        recording_session=RT._RecordingSession(repo_root=tmp_path),
    )

    assert result == 0
    assert events == ["dispatch", "start", "record"]


def test_dispatch_before_qsub_without_child_is_diagnostic_only(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    run = _run(tmp_path, sidecar=tmp_path / "pytest-stats.json")
    monkeypatch.setattr(
        task_runs, "start_automatic_test_run", lambda _root: (run, None),
    )
    monkeypatch.setattr(
        task_runs, "finish_automatic_test_run", lambda *_args: None,
    )
    records = []
    monkeypatch.setattr(
        RT, "_record_task_run", lambda **kwargs: records.append(kwargs),
    )
    _patch_direct(monkeypatch, [])
    dispatch_root = tmp_path / "dispatch"
    commands = []

    def before_qsub_failure(command, **kwargs):
        commands.append(list(command))
        if list(command[:2]) == ["qstat", "-Q"]:
            return subprocess.CompletedProcess(
                command, 1, stdout="", stderr="qsub-before-failure",
            )
        raise AssertionError("qsub must not be reached")

    def dispatch(args, *, environ):
        return DC.dispatch(
            args,
            task="tests",
            repo_root=_REPO,
            output_root=dispatch_root,
            environ=environ,
            run_command=before_qsub_failure,
            nonce="before-qsub",
        )

    assert RT.main(
        ["--force-dispatch", "target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == RT._PEGASUS_DISPATCH_RC
    assert records == []
    assert not any(command and command[0] == "qsub" for command in commands)
    diagnostic_lines = [
        line for line in capsys.readouterr().err.splitlines()
        if line.startswith("IZANAGI_TASK_RUN_DIAGNOSTIC_V1 ")
    ]
    assert diagnostic_lines == [
        "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 "
        "recording-unavailable:dispatch-no-child",
    ]


def test_dispatch_exception_projects_to_fixed_diagnostic(monkeypatch, capsys):
    monkeypatch.setenv("IZANAGI_TASK_RUN_AUTO_RECORD", "0")
    _patch_direct(monkeypatch, [])

    def raise_dispatch(args, *, environ):
        raise RuntimeError(
            "SECRET_REPO_PATH SECRET_SELECTOR_PRIVATE "
            "SECRET_NODE_ID_PRIVATE SECRET_ARGV_PRIVATE",
        )

    assert RT.main(
        ["--force-dispatch", "SECRET_REPO_PATH::SECRET_NODE_ID_PRIVATE"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=raise_dispatch,
    ) == RT._PEGASUS_DISPATCH_RC
    diagnostics = [
        line for line in capsys.readouterr().err.splitlines()
        if line.startswith("IZANAGI_TASK_RUN_DIAGNOSTIC_V1 ")
    ]
    assert diagnostics == [
        "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch",
    ]
    assert "SECRET_" not in diagnostics[0]


def test_bounded_child_receives_auto_off_and_sidecar(monkeypatch, tmp_path):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    sidecar = tmp_path / "pytest-stats.json"
    run = _run(tmp_path, sidecar=sidecar)
    monkeypatch.setattr(task_runs, "start_automatic_test_run", lambda _root: (run, None))
    session = RT._RecordingSession()
    captured = {}
    process = mock.Mock(pid=1234)
    process.wait.return_value = 0
    samples = RT._ScopeSamples()
    samples.attested = True
    samples.cgroup = tmp_path
    samples.last_events = (0, 0)
    samples.ready.set()
    sampler = mock.Mock()
    monkeypatch.setattr(RT, "_start_scope_sampler", lambda *args: (samples, sampler))
    monkeypatch.setattr(
        RT.subprocess,
        "Popen",
        lambda command, **kwargs: captured.update(kwargs) or process,
    )
    result = RT._run_bounded_scope(
        ["target.py"], LH.RESERVE_BYTES // 2, recording_session=session,
    )
    assert result == RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0)
    assert captured["env"][RT._TASK_RUN_AUTO_RECORD_ENV] == "0"
    assert captured["env"][RT._TASK_RUN_SIDECAR_ENV] == str(sidecar)


def test_bounded_popen_failure_does_not_start_automatic_task_run(
    monkeypatch, tmp_path, capsys,
):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    start = mock.Mock(side_effect=AssertionError("must not create task directory"))
    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    monkeypatch.setattr(
        RT.subprocess, "Popen", mock.Mock(side_effect=OSError("injected")),
    )

    session = RT._RecordingSession(repo_root=tmp_path)
    result = RT._run_bounded_scope_and_record(
        ["target.py"], 1024, recording_session=session,
    )

    assert result == RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)
    start.assert_not_called()
    assert not list(tmp_path.iterdir())
    assert "recording-unavailable:scope-outcome-dispatch-infra" in (
        capsys.readouterr().err
    )


def test_bounded_attestation_failure_does_not_start_automatic_task_run(
    monkeypatch, tmp_path,
):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    start = mock.Mock(side_effect=AssertionError("must not create task directory"))
    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    process = mock.Mock(pid=1234)
    samples = RT._ScopeSamples()
    samples.ready.set()
    sampler = mock.Mock()
    monkeypatch.setattr(
        RT.subprocess, "Popen", lambda *args, **kwargs: process,
    )
    monkeypatch.setattr(
        RT, "_start_scope_sampler", lambda *args: (samples, sampler),
    )
    monkeypatch.setattr(RT, "_stop_bounded_scope", mock.Mock())

    session = RT._RecordingSession(repo_root=tmp_path)
    result = RT._run_bounded_scope_and_record(
        ["target.py"], 1024, recording_session=session,
    )

    assert result == RT._ScopeResult(RT._ScopeOutcome.DISPATCH_INFRA)
    start.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_bounded_scope_non_child_outcome_is_diagnostic_only(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    run = _run(tmp_path, sidecar=tmp_path / "pytest-stats.json")
    monkeypatch.setattr(task_runs, "start_automatic_test_run", lambda _root: (run, None))
    record = mock.Mock()
    monkeypatch.setattr(RT, "_record_task_run", record)
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, **kwargs: RT._ScopeResult(RT._ScopeOutcome.CAP_OOM),
    )
    result = RT._run_bounded_scope_and_record(["target.py"], 1024)
    assert result == RT._ScopeResult(RT._ScopeOutcome.CAP_OOM)
    record.assert_not_called()
    assert capsys.readouterr().err == (
        "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:scope-outcome-cap-oom\n"
    )


def test_cap_oom_fallback_reuses_one_automatic_session(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    sidecar = tmp_path / "pytest-stats.json"
    run = _run(tmp_path, sidecar=sidecar)
    real_session = RT._RecordingSession
    def session_with_transport(*args, **kwargs):
        session = real_session(*args, **kwargs)
        session.set_manual_sidecar(sidecar)
        return session
    monkeypatch.setattr(RT, "_RecordingSession", session_with_transport)
    starts = []
    finishes = []
    records = []
    monkeypatch.setattr(
        task_runs,
        "start_automatic_test_run",
        lambda root: starts.append(root) or (run, None),
    )
    monkeypatch.setattr(
        task_runs,
        "finish_automatic_test_run",
        lambda value, outcome: finishes.append((value, outcome)) or None,
    )
    monkeypatch.setattr(
        RT,
        "_record_task_run",
        lambda **kwargs: records.append(kwargs) or (True, None),
    )
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap, **kwargs: RT._ScopeResult(RT._ScopeOutcome.CAP_OOM),
    )
    fingerprint = RT._TreeFingerprint("a" * 64, (0, 0, 0, 0, 0))
    monkeypatch.setattr(
        RT,
        "_tree_and_submodules_fingerprint",
        mock.Mock(side_effect=[fingerprint, fingerprint]),
    )
    captured = {}

    def dispatch(args, *, environ):
        captured.update(environ)
        return DC._DispatchResult(4, child_started=True)

    assert RT.main(
        ["target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 4
    assert len(starts) == 1
    assert len(records) == 1
    assert records[0]["task_run_id"] == run.task_run_id
    assert records[0]["sidecar"] == sidecar
    assert len(finishes) == 1
    assert finishes[0][1] == "completed"
    assert captured[RT._TASK_RUN_AUTO_RECORD_ENV] == "0"
    assert captured[RT._TASK_RUN_SIDECAR_ENV] == str(sidecar)
    assert "recording-unavailable:scope-outcome-cap-oom" in capsys.readouterr().err


def test_missing_sidecar_records_null_metrics_with_diagnostic(monkeypatch, tmp_path, capsys):
    run = _run(tmp_path, sidecar=tmp_path / "missing.json")
    session = RT._RecordingSession()
    session._automatic_run = run
    calls = []
    monkeypatch.setattr(
        task_runs,
        "record_test_run",
        lambda *args, **kwargs: calls.append(kwargs),
    )
    assert session.record(
        suite_id="pytest-targeted-abcdef123456",
        suite_kind="targeted",
        duration_s=1.0,
        exit_status=2,
    ) == (True, "recording-unavailable:sidecar")
    assert calls[0]["counts"] is None
    assert calls[0]["collected_node_digest"] is None
    assert capsys.readouterr().err == (
        "IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:sidecar\n"
    )


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_bootstrap(monkeypatch, exception_type):
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    monkeypatch.setattr(
        task_runs,
        "start_automatic_test_run",
        mock.Mock(side_effect=exception_type),
    )
    with pytest.raises(exception_type):
        RT._RecordingSession().ensure_started()


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_record(monkeypatch, tmp_path, exception_type):
    monkeypatch.setattr(
        task_runs,
        "record_test_run",
        mock.Mock(side_effect=exception_type),
    )
    with pytest.raises(exception_type):
        RT._record_task_run(
            task_run_id="20260819-pytest-run-01234567",
            root=tmp_path,
            suite_id="pytest-targeted-abcdef123456",
            suite_kind="targeted",
            duration_s=1.0,
            exit_status=0,
            trigger="unspecified",
            sidecar=None,
        )


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_sidecar_read(monkeypatch, tmp_path, exception_type):
    sidecar = tmp_path / "pytest-stats.json"
    monkeypatch.setattr(
        PS, "read_sidecar", mock.Mock(side_effect=exception_type),
    )
    with pytest.raises(exception_type):
        RT._record_task_run(
            task_run_id="20260819-pytest-run-01234567",
            root=tmp_path,
            suite_id="pytest-targeted-abcdef123456",
            suite_kind="targeted",
            duration_s=1.0,
            exit_status=0,
            trigger="unspecified",
            sidecar=sidecar,
        )


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_finish(monkeypatch, tmp_path, exception_type):
    run = _run(tmp_path, sidecar=None)
    monkeypatch.setattr(
        task_runs,
        "finish_automatic_test_run",
        mock.Mock(side_effect=exception_type),
    )
    session = RT._RecordingSession()
    session._automatic_run = run
    with pytest.raises(exception_type):
        session.finish("completed")


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_admission(monkeypatch, exception_type):
    module = SimpleNamespace(
        MAX_LOCAL_BUDGET_BYTES=1,
        Admission=LH.Admission,
        grant_budget=mock.Mock(side_effect=exception_type),
    )
    monkeypatch.setattr(RT, "_load_login_headroom", lambda: module)
    with pytest.raises(exception_type):
        RT._evaluate_login_admission(None)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_queue(monkeypatch, exception_type):
    monkeypatch.setattr(
        RT.importlib,
        "import_module",
        mock.Mock(side_effect=exception_type),
    )
    with pytest.raises(exception_type):
        RT._queue_dispatch_possible()


@pytest.mark.parametrize("helper", [RT._safe_bind_scope, RT._safe_release_grant])
@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_scope_cleanup(monkeypatch, helper, exception_type):
    grant = mock.Mock()
    method = "bind_scope" if helper is RT._safe_bind_scope else "release"
    getattr(grant, method).side_effect = exception_type
    with pytest.raises(exception_type):
        if helper is RT._safe_bind_scope:
            helper(grant, Path("/tmp/cgroup"))
        else:
            helper(grant)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_peak_remember(monkeypatch, exception_type):
    module = SimpleNamespace(
        remember_peak=mock.Mock(side_effect=exception_type),
    )
    with pytest.raises(exception_type):
        RT._safe_remember_peak(module, "tests", 123)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_recording_signal_is_re_raised_dispatch_setup(monkeypatch, exception_type):
    with pytest.raises(exception_type):
        RT._invoke_dispatch(
            mock.Mock(side_effect=exception_type), [], environ={},
        )


def test_manual_task_run_is_not_auto_finished(monkeypatch, tmp_path):
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260819-manual-01234567")
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    start = mock.Mock(side_effect=AssertionError("manual path must not auto-start"))
    finish = mock.Mock(side_effect=AssertionError("manual path must not auto-finish"))
    monkeypatch.setattr(task_runs, "start_automatic_test_run", start)
    monkeypatch.setattr(task_runs, "finish_automatic_test_run", finish)
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    _patch_direct(monkeypatch, [])
    records = []
    monkeypatch.setattr(RT, "_record_task_run", lambda **kwargs: records.append(kwargs) or (True, None))
    monkeypatch.setattr(RT.subprocess, "call", lambda *args, **kwargs: 0)
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 0
    start.assert_not_called()
    finish.assert_not_called()
    assert records[0]["task_run_id"] == "20260819-manual-01234567"
    assert records[0]["trigger"] == "final"


def test_coverage_contract_names_only_run_tests_routes():
    readme = (_REPO / "output" / "task-runs" / "README.md").read_text(
        encoding="utf-8",
    )
    for phrase in (
        "tools/run_tests.py",
        "raw pytest",
        "mutation local mode",
        "別 clone",
        "gate/preflight reject",
        "trigger=unspecified",
        "改竄検出を主張しない",
        "argv",
        "selector",
        "node ID",
        "repo file path",
    ):
        assert phrase in readme


def test_force_dispatch_real_path_sidecar_roundtrip_when_enabled(tmp_path, monkeypatch):
    """実 scheduler 経路の cross-node check; opt-in しない環境では未実走。"""

    if os.environ.get("IZANAGI_RUN_REAL_DISPATCH_TEST") != "1":
        pytest.skip("実 dispatch は環境許可時に親が実走する")
    if RT.site_policy.current_site() != RT.site_policy.PEGASUS_LOGIN:
        pytest.skip("Pegasus login node ではない")
    # /tmp は compute 側と共有されない site があるため、実 dispatch 用の
    # transport は /work の repo parent に置く。実 production では Unit A の
    # sibling transport lease を受け取るが、ここでは pytest hook が受理する
    # basename を使って B の transport/consume を独立に実証する。
    sidecar_parent = Path(tempfile.mkdtemp(
        prefix="izanagi-testops-dispatch-", dir=_REPO.parent,
    ))
    os.chmod(sidecar_parent, 0o700)
    sidecar = sidecar_parent / "pytest-stats.json"
    generation = tmp_path / "generation-000001"
    generation.mkdir()
    run = AutomaticRun(
        generation_root=generation,
        task_run_id="20260819-real-dispatch-01234567",
        generation_name=generation.name,
        sidecar_path=sidecar,
    )
    captured = []
    monkeypatch.delenv("IZANAGI_TASK_RUN_AUTO_RECORD", raising=False)
    monkeypatch.setattr(
        task_runs, "start_automatic_test_run", lambda _root: (run, None),
    )
    monkeypatch.setattr(
        task_runs, "finish_automatic_test_run", lambda *_args: None,
    )
    monkeypatch.setattr(
        task_runs, "record_test_run",
        lambda *args, **kwargs: captured.append(kwargs),
    )
    try:
        rc = RT.main(
            [
                "--force-dispatch",
                "orchestrator/tests/test_run_tests_testops_observation.py::test_diagnostic_is_bounded_and_contains_no_path_selector_or_nodeid",
            ],
            site=RT.site_policy.PEGASUS_LOGIN,
        )
        assert rc == 0
        assert len(captured) == 1
        assert captured[0]["counts"]["collected"] == 1
        digest = captured[0]["collected_node_digest"]
        assert isinstance(digest, str) and len(digest) == 12
    finally:
        shutil.rmtree(sidecar_parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
