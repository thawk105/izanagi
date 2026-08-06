# -*- coding: utf-8 -*-
"""task-run pytest/check recording の opt-in・privacy・fail-open 回帰。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import builtins
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import pytest

from tools.task_runs import init_pilot, start_run, validate_run
from tools.task_runs import pytest_stats as PS
import orchestrator.tests.conftest as CONF
from orchestrator.campaign import login_headroom as LH


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RT = _load(_REPO / "tools" / "run_tests.py", "run_tests_task_run_test")
TC = _load(_REPO / "tools" / "task_run_check.py", "task_run_check_test")


@pytest.fixture(autouse=True)
def _clean_stats_state(monkeypatch):
    PS._collected_node_ids.clear()
    for name in (
        "IZANAGI_TASK_RUN_ID", "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR", "IZANAGI_TEST_TRIGGER",
        "IZANAGI_TEST_SUITE_ID", "PYTEST_ADDOPTS",
        "IZANAGI_RUN_TESTS_SCOPE_UNIT", "IZANAGI_RUN_TESTS_SCOPE_CAP",
    ):
        monkeypatch.delenv(name, raising=False)


def test_opt_out_preserves_exact_command_and_call_shape(monkeypatch):
    called = []
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: True)
    monkeypatch.setattr(RT, "_xdist_version", lambda: "3.8.0")
    monkeypatch.setattr(RT, "_default_nproc", lambda *, site: 4)
    monkeypatch.setattr(RT.subprocess, "call", lambda *a, **kw: called.append((a, kw)) or 7)

    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 7
    assert called == [(([
        sys.executable, "-m", "pytest", str(_REPO / "orchestrator" / "tests"),
        "-n", "4", "--dist", "loadgroup", "-q",
    ],), {"cwd": str(_REPO)})]


@pytest.mark.parametrize("args", [[], ["-q"], ["-n", "2"], ["--color=yes"]])
def test_full_classification_closed_known_nonselectors(args):
    assert RT._suite_identity(args, "")[0] == "full"


@pytest.mark.parametrize("args", [
    ["orchestrator/tests/test_x.py"], ["-k", "secret expression"],
    ["-mfoo"], ["--lf"], ["-x"], ["--deselect=x::y"],
    ["--unknown-plugin-option"], ["--", "-q"],
    ["--help"], ["--version"], ["--setup-only"], ["--setup-plan"],
    ["--collect-only"], ["--fixtures"], ["--markers"], ["--trace-config"],
])
def test_targeted_classification_is_conservative(args):
    assert RT._suite_identity(args, "")[0] == "targeted"


def test_nonempty_pytest_addopts_forces_targeted():
    assert RT._suite_identity([], " -k private-selector ")[0] == "targeted"
    assert RT._suite_identity([], "   ") == ("full", "pytest-orchestrator-full")


def test_suite_id_contains_no_command_target_or_selector_text():
    selector = "private_selector_body"
    target = "orchestrator/tests/test_private_name.py::test_secret_node"
    kind, suite_id = RT._suite_identity([target, "-k", selector], "")
    assert kind == "targeted"
    assert suite_id.startswith("pytest-targeted-")
    assert len(suite_id.rsplit("-", 1)[1]) == 12
    assert selector not in suite_id
    assert "test_secret_node" not in suite_id
    assert "python" not in suite_id


def test_opt_in_keeps_pytest_argv_and_records_monotonic_result(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "final")
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    times = iter((10.0, 12.25))
    monkeypatch.setattr(RT.time, "monotonic", lambda: next(times))

    def fake_call(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["cwd"] = kwargs["cwd"]
        sidecar = Path(kwargs["env"]["IZANAGI_TASK_RUN_SIDECAR"])
        PS._create_sidecar(sidecar, {
            "collected": 2, "passed": 1, "failed": 1, "skipped": 0,
            "collected_node_digest": "abcdef123456",
        })
        return 1

    monkeypatch.setattr(RT.subprocess, "call", fake_call)
    monkeypatch.setattr(RT, "_record_task_run", lambda **kw: captured.update(record=kw))
    target = "orchestrator/tests/test_run_tests_task_run.py"
    assert RT.main([target, "-k", "one"], site=RT.site_policy.OTHER) == 1
    assert captured["command"] == [
        sys.executable, "-m", "pytest", str(_REPO / target), "-k", "one",
    ]
    assert captured["cwd"] == str(_REPO)
    assert Path(captured["env"]["IZANAGI_TASK_RUN_SIDECAR"]).is_absolute()
    assert not str(captured["env"]["IZANAGI_TASK_RUN_SIDECAR"]).startswith(str(_REPO))
    assert captured["record"]["duration_s"] == 2.25
    assert captured["record"]["exit_status"] == 1
    assert captured["record"]["trigger"] == "final"


def test_login_parent_records_once_and_dispatch_environment_has_no_run_id(
    monkeypatch, tmp_path,
):
    # 親 dispatcher seam の API 契約。M7 の受理挙動 kill は下の実 job 経路が担う。
    captured = {"records": []}
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "after-change")
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    times = iter((20.0, 24.5))
    monkeypatch.setattr(RT.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        RT,
        "_record_task_run",
        lambda **kwargs: captured["records"].append(kwargs),
    )

    def dispatch(args, *, environ):
        assert list(args) == ["test_target.py"]
        assert "IZANAGI_TASK_RUN_ID" not in environ
        assert "IZANAGI_TASK_RUNS_ROOT" not in environ
        assert "IZANAGI_TASK_RUN_SIDECAR" not in environ
        return 5

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 5
    assert len(captured["records"]) == 1
    record = captured["records"][0]
    assert record["exit_status"] == 5
    assert record["duration_s"] == 4.5
    assert record["sidecar"] is None


def test_previous_peak_estimate_dispatch_records_once(monkeypatch, tmp_path):
    records = []
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (
            LH.Admission.DISPATCH, None, "前回の部分走は cap 到達",
        ),
    )
    monkeypatch.setattr(RT, "_queue_dispatch_possible", lambda: (True, "queue"))
    monkeypatch.setattr(RT, "_record_task_run", lambda **kw: records.append(kw))
    times = iter((30.0, 32.0))
    monkeypatch.setattr(RT.time, "monotonic", lambda: next(times))
    dispatch = mock.Mock(return_value=6)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 6
    dispatch.assert_called_once()
    assert len(records) == 1
    assert records[0]["exit_status"] == 6
    assert records[0]["duration_s"] == 2.0


def test_m7_parent_dispatch_environment_isolated_redundant_gate(monkeypatch):
    """M7 親 pop 単独変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_run_tests_task_run.py::test_m7_parent_dispatch_environment_isolated_redundant_gate``。
    親の ``_dispatch_environment()`` の pop だけを無効化すると本 node は赤くなる。
    dispatcher allowlist と job script が同じ状態を除去するため冗長 gate であり、
    DW-M03 に従って単独変異の受理挙動証拠から外す。
    """

    task_run_state = {
        "IZANAGI_TASK_RUN_ID": "must-not-reach-child",
        "IZANAGI_TASK_RUNS_ROOT": "/private/ledger",
        "IZANAGI_TASK_RUN_SIDECAR": "/private/sidecar",
    }
    for name, value in task_run_state.items():
        monkeypatch.setenv(name, value)

    child_env = RT._dispatch_environment()

    assert set(task_run_state).isdisjoint(child_env)


def test_login_dispatch_exception_records_single_infra_rc(monkeypatch, tmp_path):
    records = []
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda a, r: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda a, r: 0)
    monkeypatch.setattr(RT, "_record_task_run", lambda **kw: records.append(kw))

    def fail(args, *, environ):
        raise OSError("injected")

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=fail,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == RT._PEGASUS_DISPATCH_RC
    assert len(records) == 1
    assert records[0]["exit_status"] == RT._PEGASUS_DISPATCH_RC


def test_local_scope_completion_records_once_in_scope_parent(monkeypatch):
    records = []
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setattr(RT, "_record_task_run", lambda **kw: records.append(kw))
    times = iter((30.0, 31.0))
    monkeypatch.setattr(RT.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap: RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0),
    )
    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 0
    assert len(records) == 1
    assert records[0]["exit_status"] == 0


def test_cap_oom_fallback_records_authoritative_compute_once(
    monkeypatch, tmp_path,
):
    records = []
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "ledger"))
    monkeypatch.setattr(RT, "_record_task_run", lambda **kw: records.append(kw))
    monkeypatch.setattr(
        RT,
        "_run_bounded_scope",
        lambda args, cap: RT._ScopeResult(RT._ScopeOutcome.CAP_OOM),
    )
    monkeypatch.setattr(RT, "_tree_and_submodules_clean", lambda repo: True)
    times = iter((30.0, 31.0, 32.0))
    monkeypatch.setattr(RT.time, "monotonic", lambda: next(times))
    dispatch = mock.Mock(return_value=4)

    assert RT.main(
        ["test_target.py"],
        site=RT.site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 4
    dispatch.assert_called_once()
    assert len(records) == 1
    assert records[0]["exit_status"] == 4


def test_scope_child_cannot_record_task_run_directly(monkeypatch, tmp_path):
    for name, value in {
        "IZANAGI_TASK_RUN_ID": "parent-only",
        "IZANAGI_TASK_RUNS_ROOT": "/private/ledger",
        "IZANAGI_TASK_RUN_SIDECAR": "/private/sidecar",
    }.items():
        monkeypatch.setenv(name, value)
    captured = {}
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return 0

    process.wait.side_effect = wait

    def popen(command, **kwargs):
        captured.update(kwargs)
        return process

    monkeypatch.setattr(RT.subprocess, "Popen", popen)
    monkeypatch.setattr(RT, "_scope_cgroup_path", lambda path, unit: tmp_path)
    monkeypatch.setattr(RT, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(RT, "_scope_properties_are_enforced", lambda path, cap: True)

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 1

    def events(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 0, 0

    monkeypatch.setattr(RT, "_read_scope_current", current)
    monkeypatch.setattr(RT, "_read_scope_events", events)

    result = RT._run_bounded_scope(["test_target.py"], LH.RESERVE_BYTES // 2)
    assert result == RT._ScopeResult(RT._ScopeOutcome.CHILD_RC, 0)
    assert "IZANAGI_TASK_RUN_ID" not in captured["env"]
    assert "IZANAGI_TASK_RUNS_ROOT" not in captured["env"]
    assert "IZANAGI_TASK_RUN_SIDECAR" not in captured["env"]


def test_sidecar_setup_and_record_failures_preserve_rc_and_output(monkeypatch, capsys):
    monkeypatch.setattr(RT, "_private_sidecar", mock.Mock(side_effect=OSError("injected")))
    monkeypatch.setattr(RT, "_record_task_run", mock.Mock(side_effect=ImportError("injected")))

    def child(command, **kwargs):
        assert kwargs == {"cwd": str(_REPO)}
        print("child stdout")
        print("child stderr", file=sys.stderr)
        return 5

    monkeypatch.setattr(RT.subprocess, "call", child)
    assert RT._call_and_record(["pytest"], [], "20260720-e2-01234567") == 5
    captured = capsys.readouterr()
    assert captured.out == "child stdout\n"
    assert captured.err == "child stderr\n"


def test_lazy_import_failure_preserves_child_rc_and_output(monkeypatch, capsys):
    real_import = builtins.__import__

    def failed_import(name, *args, **kwargs):
        if name.startswith("tools.task_runs"):
            raise ImportError("injected")
        return real_import(name, *args, **kwargs)

    def child(command, **kwargs):
        assert kwargs["cwd"] == str(_REPO)
        assert "IZANAGI_TASK_RUN_SIDECAR" in kwargs["env"]
        print("child stdout")
        print("child stderr", file=sys.stderr)
        return 3

    monkeypatch.setattr(builtins, "__import__", failed_import)
    monkeypatch.setattr(RT.subprocess, "call", child)
    assert RT._call_and_record(["pytest"], [], "20260720-e2-01234567") == 3
    captured = capsys.readouterr()
    assert captured.out == "child stdout\n"
    assert captured.err == "child stderr\n"


def test_corrupt_sidecar_records_null_metrics_without_output(monkeypatch, tmp_path, capsys):
    sidecar = tmp_path / "broken.json"
    sidecar.write_bytes(b'{"collected":')
    calls = []
    monkeypatch.setattr("tools.task_runs.record_test_run", lambda *a, **kw: calls.append(kw))
    RT._record_task_run(
        task_run_id="20260720-e2-01234567", root=tmp_path,
        suite_id="pytest-targeted-abcdef123456", suite_kind="targeted",
        duration_s=1.0, exit_status=2, trigger="unspecified", sidecar=sidecar,
    )
    assert calls[0]["counts"] is None
    assert calls[0]["collected_node_digest"] is None
    assert capsys.readouterr() == ("", "")


def test_record_failure_is_single_attempt(monkeypatch, tmp_path):
    os.chmod(tmp_path, 0o700)
    sidecar = tmp_path / "pytest-stats.json"
    PS._create_sidecar(sidecar, {
        "collected": 1, "passed": 1, "failed": 0, "skipped": 0,
        "collected_node_digest": "abcdef123456",
    })
    calls = []

    def record(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise OSError("injected")

    monkeypatch.setattr("tools.task_runs.record_test_run", record)
    RT._record_task_run(
        task_run_id="20260720-e2-01234567", root=tmp_path,
        suite_id="pytest-targeted-abcdef123456", suite_kind="targeted",
        duration_s=1.0, exit_status=0, trigger="final", sidecar=sidecar,
    )
    assert len(calls) == 1
    assert calls[0]["counts"]["passed"] == 1


def test_recording_interrupts_are_not_swallowed(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "tools.task_runs.record_test_run", mock.Mock(side_effect=KeyboardInterrupt),
    )
    with pytest.raises(KeyboardInterrupt):
        RT._record_task_run(
            task_run_id="20260720-e2-01234567", root=tmp_path,
            suite_id="pytest-targeted-abcdef123456", suite_kind="targeted",
            duration_s=1.0, exit_status=0, trigger="final", sidecar=None,
        )


def _session(*, worker=False, collected=3):
    reports = {
        "passed": [SimpleNamespace(nodeid="a::one")],
        "failed": [SimpleNamespace(nodeid="b::two")],
        "error": [SimpleNamespace(nodeid="c::three")],
        "skipped": [SimpleNamespace(nodeid="d::four")],
    }
    reporter = SimpleNamespace(stats=reports)
    manager = SimpleNamespace(get_plugin=lambda name: reporter if name == "terminalreporter" else None)
    config = SimpleNamespace(pluginmanager=manager)
    if worker:
        config.workerinput = {}
    items = [SimpleNamespace(nodeid="a::one"), SimpleNamespace(nodeid="b::two"),
             SimpleNamespace(nodeid="c::three")]
    return SimpleNamespace(config=config, items=items, testscollected=collected)


def test_sidecar_is_create_only_0600_and_contains_digest_not_node_names(tmp_path):
    session = _session()
    PS.note_collection(session)
    os.chmod(tmp_path, 0o700)
    path = (tmp_path / "pytest-stats.json").resolve()
    PS._create_sidecar(path, PS._count_stats(session))
    raw = path.read_text(encoding="ascii")
    data = json.loads(raw)
    expected = hashlib.sha256(b"a::one\0b::two\0c::three").hexdigest()[:12]
    assert data == {
        "collected": 3, "passed": 1, "failed": 2, "skipped": 1,
        "collected_node_digest": expected,
    }
    assert "a::one" not in raw and "b::two" not in raw
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        PS._create_sidecar(path, data)
    assert path.read_bytes() == original


def test_xdist_worker_is_noop(tmp_path, monkeypatch):
    path = (tmp_path / "worker.json").resolve()
    monkeypatch.setenv(PS.SIDECAR_ENV, str(path))
    session = _session(worker=True)
    PS.note_collection(session)
    PS.write_session_stats(session)
    assert PS._collected_node_ids == set()
    assert not path.exists()


@pytest.mark.parametrize("case", ["repo", "mode", "basename"])
def test_hook_rejects_non_wrapper_sidecar_paths_as_noop(monkeypatch, tmp_path, case):
    if case == "repo":
        parent = _REPO / ".task-run-sidecar-negative"
        parent.mkdir(mode=0o700, exist_ok=True)
        path = parent / "pytest-stats.json"
    else:
        parent = tmp_path / case
        parent.mkdir(mode=0o700)
        os.chmod(parent, 0o755 if case == "mode" else 0o700)
        path = parent / ("bad-name.json" if case == "basename" else "pytest-stats.json")
    try:
        monkeypatch.setenv(PS.SIDECAR_ENV, str(path.resolve()))
        PS.write_session_stats(_session())
        assert not path.exists()
    finally:
        if case == "repo":
            parent.rmdir()


def test_conftest_hook_absent_env_does_not_lazy_import(monkeypatch):
    imported = mock.Mock(side_effect=AssertionError("must not import"))
    monkeypatch.setattr(PS, "write_session_stats", imported)
    CONF.pytest_sessionfinish(_session(), 0)
    imported.assert_not_called()


@pytest.mark.parametrize(
    ("hook", "helper", "args"),
    [
        (CONF.pytest_collection_finish, "note_collection", lambda: (_session(),)),
        (
            CONF.pytest_xdist_node_collection_finished,
            "note_xdist_collection",
            lambda: (SimpleNamespace(config=_session().config), ["a::one"]),
        ),
        (CONF.pytest_sessionfinish, "write_session_stats", lambda: (_session(), 4)),
    ],
)
def test_conftest_hooks_swallow_exception_without_observable_change(
    monkeypatch, tmp_path, capsys, hook, helper, args,
):
    monkeypatch.setenv(PS.SIDECAR_ENV, str((tmp_path / "pytest-stats.json").resolve()))
    monkeypatch.setattr(PS, helper, mock.Mock(side_effect=OSError("injected")))
    call_args = args()
    assert hook(*call_args) is None
    assert capsys.readouterr() == ("", "")
    if helper == "write_session_stats":
        assert call_args[1] == 4


def test_check_wrapper_executes_only_fixed_argv(monkeypatch):
    calls = []
    monkeypatch.setattr(TC.subprocess, "call", lambda *a, **kw: calls.append((a, kw)) or 3)
    assert TC.main(["static-check"]) == 3
    assert calls == [((["python3", "tools/check_codex_agents.py"],), {"cwd": _REPO})]
    with pytest.raises(SystemExit) as error:
        TC.main(["python3", "-c", "anything"])
    assert error.value.code == 2
    assert len(calls) == 1


def test_check_wrapper_recording_failure_preserves_child_rc(monkeypatch):
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setattr(TC.subprocess, "call", lambda *a, **kw: 4)
    monkeypatch.setattr(TC, "_record", mock.Mock(side_effect=OSError("injected")))
    # main guards the complete recording operation as fail-open.
    assert TC.main(["docs-check"]) == 4


def test_check_wrapper_record_failure_is_single_attempt(monkeypatch):
    calls = mock.Mock(side_effect=OSError("injected"))
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setattr("tools.task_runs.record_test_run", calls)
    TC._record("docs-check", 1.0, 0)
    assert calls.call_count == 1


def test_check_wrapper_records_fixed_suite_kind_and_duration(monkeypatch, tmp_path):
    calls = []
    times = iter((4.0, 5.75))
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", "20260720-e2-01234567")
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path))
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "after-change")
    monkeypatch.setattr(TC.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(TC.subprocess, "call", lambda *a, **kw: 0)
    monkeypatch.setattr("tools.task_runs.record_test_run", lambda *a, **kw: calls.append((a, kw)))
    assert TC.main(["provenance-check"]) == 0
    assert len(calls) == 1
    positional, keywords = calls[0]
    assert positional[1] == "20260720-e2-01234567"
    assert keywords == {
        "suite_id": "provenance-check", "suite_kind": "provenance-check",
        "duration_s": 1.75, "exit_status": 0, "counts": None,
        "trigger": "after-change", "collected_node_digest": None,
    }


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_real_pytest_hook_records_aggregate_only_in_tmp_ledger(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.invalid", cwd=repo)
    _git("config", "user.name", "Task Run Test", cwd=repo)
    (repo / "seed").write_text("seed\n", encoding="utf-8")
    _git("add", "seed", cwd=repo)
    _git("commit", "-m", "seed", cwd=repo)
    root = repo / "task-runs"
    init_pilot(root)
    run_id = start_run(
        root, slug="e2", objective="E2 integration", task_class=2,
        task_kind="implementation",
    )
    sample = tmp_path / "test_sample.py"
    sample.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    monkeypatch.setenv("IZANAGI_TASK_RUN_ID", run_id)
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(root))
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    rc = RT.main(
        ["-q", "-p", "orchestrator.tests.conftest", str(sample)],
        site=RT.site_policy.OTHER,
    )
    assert rc == 0
    event = validate_run(root / run_id).events[-1]
    assert event["event"] == "test_run"
    assert event["suite_kind"] == "targeted"
    assert event["collected"] == 1
    assert event["passed"] == 1
    assert event["failed"] == 0
    assert event["skipped"] == 0
    assert isinstance(event["collected_node_digest"], str)
    serialized = json.dumps(event)
    assert "test_sample.py::test_ok" not in serialized


def test_live_xdist_controller_writes_one_valid_sidecar(tmp_path):
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    os.chmod(private, 0o700)
    sidecar = private / "pytest-stats.json"
    sample = tmp_path / "test_xdist_sample.py"
    sample.write_text(
        "import pytest\n"
        "@pytest.mark.xdist_group('a')\n"
        "def test_one(): assert True\n"
        "@pytest.mark.xdist_group('b')\n"
        "def test_two(): assert True\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env[PS.SIDECAR_ENV] = str(sidecar.resolve())
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "-n", "2", "--dist", "loadgroup",
            "-p", "orchestrator.tests.conftest", str(sample),
        ],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "2 passed" in result.stdout
    assert result.stderr == ""
    assert sidecar.read_bytes().count(b"\n") == 1
    stats = PS.read_sidecar(sidecar)
    assert stats is not None
    counts, digest = stats
    assert counts == {"collected": 2, "passed": 2, "failed": 0, "skipped": 0}
    assert isinstance(digest, str) and len(digest) == 12


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
