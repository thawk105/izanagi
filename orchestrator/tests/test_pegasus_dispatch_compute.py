# -*- coding: utf-8 -*-
"""Pegasus compute dispatcher の fake scheduler 境界テスト。

実 qsub は呼ばず、command runner・clock・sleep を全て注入する。
"""
from __future__ import annotations

import ast
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.pegasus import dispatch_compute as DC


_JOB_ID = "0:424242.nqsv"


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class _Scheduler:
    def __init__(
        self,
        *,
        states=("QUE", "RUN", "DONE", "EXT"),
        child_rc=0,
        accounting=True,
        visible=True,
        marker=True,
        initial_qstat_failures=0,
        initial_qstat_error="temporary qstat failure",
        qstat_error_stdout="",
        qsub_stdout=None,
        discovery_visible=True,
        qdel_returncode=0,
        qdel_exception=None,
        stdout=b"",
        stderr_prefix=b"",
        stage="child",
        log_style="script",
    ):
        self.states = list(states)
        self.child_rc = child_rc
        self.accounting = accounting
        self.visible = visible
        self.marker = marker
        self.initial_qstat_failures = initial_qstat_failures
        self.initial_qstat_error = initial_qstat_error
        self.qstat_error_stdout = qstat_error_stdout
        self.qsub_stdout = qsub_stdout
        self.discovery_visible = discovery_visible
        self.qdel_returncode = qdel_returncode
        self.qdel_exception = qdel_exception
        self.stdout = stdout
        self.stderr_prefix = stderr_prefix
        self.stage = stage
        self.log_style = log_style
        self.commands = []
        self.qstat_index = 0
        self.qstat_calls = 0

    @staticmethod
    def _completed(command, rc=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(command, rc, stdout, stderr)

    def _finish(self, cwd: Path):
        if self.log_style == "job-name":
            assert cwd.name == "fixture-nonce"
            log_stem = "izdw-fixture-no"
        elif self.log_style == "script":
            log_stem = "dispatch.sh"
        else:
            raise AssertionError(f"unknown log style: {self.log_style}")
        log_request_id = DC._normalize_request_id(_JOB_ID).split(".", 1)[0]
        (cwd / f"{log_stem}.o{log_request_id}").write_bytes(self.stdout)
        accounting = (
            b"\n".join((
                b"Request ID:             424242.nqsv",
                b"Group Name:             SFC",
                b"Started Request Time:   Thu Jul 30 10:03:23 2026",
                b"Ended Request Time:     Thu Jul 30 10:10:20 2026",
                b"  Elapse:               421S",
                b"",
            ))
            if self.accounting else b"ordinary child stderr\n"
        )
        (cwd / f"{log_stem}.e{log_request_id}").write_bytes(
            self.stderr_prefix
            + (b"\n" if self.stderr_prefix and not self.stderr_prefix.endswith(b"\n") else b"")
            + accounting,
        )
        (cwd / "result.json").write_text(
            json.dumps({
                "schema_version": "pegasus-dispatch-result/v1",
                "stage": self.stage,
                "child_rc": self.child_rc,
                "pbs_jobid": _JOB_ID,
                "hostname": "bnode114",
                "interpreter": "/bin/python3.10",
                "error": None,
            }) + "\n",
            encoding="utf-8",
        )
        if self.marker:
            (cwd / DC._COMPUTE_MARKER_NAME).write_text(
                json.dumps({
                    "schema_version": "pegasus-compute-visible/v1",
                    "pbs_jobid": _JOB_ID,
                    "hostname": "bnode114",
                }) + "\n",
                encoding="utf-8",
            )

    def __call__(self, command, **kwargs):
        command = list(command)
        self.commands.append((command, kwargs))
        cwd = Path(kwargs["cwd"])
        if command == ["qstat", "-Q"]:
            return self._completed(command, stdout="gen_S enabled\n")
        if command[0] == "qsub":
            return self._completed(
                command,
                stdout=(
                    f"Request {_JOB_ID} submitted to queue: gen_S.\n"
                    if self.qsub_stdout is None else self.qsub_stdout
                ),
            )
        if command[:2] == ["qstat", "-f"]:
            if len(command) == 2:
                if not self.discovery_visible:
                    return self._completed(command, stdout="unrelated request\n")
                return self._completed(
                    command,
                    stdout=(
                        f"Request ID = {_JOB_ID}\n"
                        f"Request Name = izdw-fixture-no\n"
                        f"Output Path = {cwd}\n"
                    ),
                )
            self.qstat_calls += 1
            if self.qstat_calls <= self.initial_qstat_failures:
                return self._completed(
                    command, rc=153, stderr=self.initial_qstat_error,
                )
            if not self.visible and self.qstat_index == 0:
                return self._completed(
                    command,
                    stdout="Batch Request does not exist on nqsv.\n",
                )
            state = (
                self.states[self.qstat_index]
                if self.qstat_index < len(self.states) else "DONE"
            )
            self.qstat_index += 1
            if state == "DONE":
                self._finish(cwd)
                return self._completed(
                    command,
                    stdout=(
                        f"Batch Request: {_JOB_ID} does not exist on nqsv.\n"
                    ),
                )
            if state == "ERROR":
                return self._completed(
                    command,
                    rc=153,
                    stdout=self.qstat_error_stdout,
                    stderr="temporary qstat failure",
                )
            return self._completed(
                command,
                stdout=f"Request ID = {_JOB_ID}\nRequest State = {state}\n",
            )
        if command[0] == "qdel":
            if self.qdel_exception is not None:
                raise self.qdel_exception
            return self._completed(command, rc=self.qdel_returncode)
        raise AssertionError(f"unexpected scheduler command: {command}")


def _dispatch(
    tmp_path: Path,
    scheduler: _Scheduler,
    *,
    poll_interval_s=5,
    queue_wait_timeout_s=20,
    accounting_grace_s=0,
    nonce="fixture-nonce",
    **kwargs,
):
    clock = _Clock()
    rc = DC.dispatch(
        ["orchestrator/tests/test_sample.py", "-q"],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        environ={
            "PATH": os.environ.get("PATH", ""),
            "IZANAGI_TASK_RUN_ID": "must-not-propagate",
            "IZANAGI_TASK_RUNS_ROOT": "/private/ledger",
            "PYTEST_ADDOPTS": "-q",
        },
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=poll_interval_s,
        queue_wait_timeout_s=queue_wait_timeout_s,
        accounting_grace_s=accounting_grace_s,
        nonce=nonce,
        **kwargs,
    )
    return rc, tmp_path / "dispatch" / nonce


def _dispatch_attestation_lines(captured):
    return [
        line
        for line in (captured.out + captured.err).splitlines()
        if line.startswith(DC._DISPATCH_OUTCOME_PREFIX)
    ]


def test_queue_wait_timeout_attests_child_not_started_once(tmp_path, capsys):
    scheduler = _Scheduler(states=("QUE", "QUE", "QUE", "QUE"))
    rc, _ = _dispatch(
        tmp_path,
        scheduler,
        queue_wait_timeout_s=10,
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert lines == [
        DC._DISPATCH_OUTCOME_PREFIX
        + '{"child_rc":null,"child_started":false,"kind":"infra",'
        '"reason":"queue-wait-timeout"}'
    ]
    assert lines[0].isascii()
    payload_text = lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):]
    payload = json.loads(payload_text)
    assert set(payload) == {"child_rc", "child_started", "kind", "reason"}
    assert payload_text == json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


@pytest.mark.parametrize(
    "states",
    [
        ("HLD", "HLD", "HLD", "HLD"),
        ("QUE", "QUE", "UNRECOGNIZED", "QUE"),
        ("QUE", "QUE", "ERROR", "QUE"),
    ],
    ids=("held", "unknown", "qstat-error"),
)
def test_queue_wait_timeout_without_queued_proof_attests_started(
    tmp_path, capsys, states,
):
    rc, _ = _dispatch(
        tmp_path,
        _Scheduler(states=states),
        queue_wait_timeout_s=10,
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert len(lines) == 1
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload == {
        "child_rc": None,
        "child_started": True,
        "kind": "infra",
        "reason": "queue-wait-timeout",
    }


def test_fast_ended_job_without_result_attests_started_when_run_was_unseen(
    tmp_path, capsys,
):
    scheduler = _Scheduler(states=("QUE", "DONE"))

    def discard_result_after_end(command, **kwargs):
        result = scheduler(command, **kwargs)
        result_path = Path(kwargs["cwd"]) / "result.json"
        if list(command)[:2] == ["qstat", "-f"] and result_path.exists():
            result_path.unlink()
        return result

    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=discard_result_after_end,
        clock=(clock := _Clock()),
        sleep=clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
        nonce="fast-ended-missing-result",
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert len(lines) == 1
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload["child_started"] is True
    assert payload["reason"] == "result/log/accounting-grace-expired"


def test_receipt_persist_failure_after_red_child_attests_started_and_rc(
    tmp_path, capsys,
):
    scheduler = _Scheduler(child_rc=1)
    with mock.patch.object(DC, "_persist_receipt", return_value=None):
        rc, _ = _dispatch(tmp_path, scheduler)
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert len(lines) == 1
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload == {
        "child_rc": 1,
        "child_started": True,
        "kind": "infra",
        "reason": "receipt-persist-failed",
    }


@pytest.mark.parametrize("child_rc", [0, 1, 13, DC.INFRA_RC])
def test_child_rc_passthrough_emits_no_infra_attestation(
    tmp_path, capsys, child_rc,
):
    rc, _ = _dispatch(tmp_path, _Scheduler(child_rc=child_rc))
    captured = capsys.readouterr()

    assert rc == child_rc
    assert _dispatch_attestation_lines(captured) == []


def test_success_receipt_explicitly_attests_child_started(tmp_path):
    result, _ = _dispatch(tmp_path, _Scheduler(child_rc=0))

    assert result == 0
    assert type(result) is DC._DispatchResult
    assert result.child_started is True


@pytest.mark.parametrize(
    ("raised", "expected_reason"),
    [
        (RuntimeError("unknown exception detail"), "unexpected-error"),
        (DC.DispatchError("unknown dispatch reason"), "dispatch-error"),
    ],
    ids=("unexpected-exception", "unknown-dispatch-reason"),
)
def test_unknown_exception_attestation_uses_closed_vocabulary(
    tmp_path, capsys, raised, expected_reason,
):
    def raise_unknown(_command, **_kwargs):
        raise raised

    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=raise_unknown,
        nonce="unknown-exception",
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert len(lines) == 1
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload["reason"] == expected_reason
    assert payload["reason"] in DC._DISPATCH_INFRA_REASONS
    assert str(raised) not in lines[0]


def test_setup_failure_attestation_is_fail_closed(tmp_path, capsys):
    rc = DC.dispatch(
        [],
        task="outside-closed-task-enum",
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    assert len(lines) == 1
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload == {
        "child_rc": None,
        "child_started": True,
        "kind": "infra",
        "reason": "setup-failure",
    }


@pytest.mark.parametrize(
    ("reason", "child_rc"),
    [("overall-timeout", None), ("queue-wait-timeout", 1)],
    ids=("nonqueue-reason", "observed-child-rc"),
)
def test_infra_attestation_false_is_reserved_for_consistent_queue_timeout(
    capsys, reason, child_rc,
):
    rc = DC._return_infra(
        reason,
        child_started=False,
        child_rc=child_rc,
    )
    lines = _dispatch_attestation_lines(capsys.readouterr())

    assert rc == DC.INFRA_RC
    payload = json.loads(lines[0][len(DC._DISPATCH_OUTCOME_PREFIX):])
    assert payload["child_started"] is True


def test_parent_dispatch_infra_returns_are_all_attested_by_helper():
    source = Path(DC.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("_dispatch_impl", "dispatch"):
        bare_returns = [
            node.lineno
            for node in ast.walk(functions[name])
            if isinstance(node, ast.Return)
            and (
                (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "INFRA_RC"
                )
                or (
                    isinstance(node.value, ast.Constant)
                    and node.value.value == DC.INFRA_RC
                )
            )
        ]
        assert bare_returns == []


def test_dispatch_state_machine_returns_child_rc_after_accounting(tmp_path):
    scheduler = _Scheduler(child_rc=9)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 9

    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == {
        "kind": "child", "rc": 9, "accounting_verified": True,
    }
    assert [entry["state"] for entry in receipt["state_history"]] == [
        "QUE", "RUN", "END",
    ]
    assert "queue_wait_included_in_parent_duration" not in receipt
    assert receipt["queue_wait_observed"] is True
    assert receipt["scheduler_logs"]["accounting_present"] is True
    assert receipt["f49_compute_marker"]["valid"] is True
    assert receipt["terminal_reason"] == "request-disappeared-after-visibility"

    commands = [command for command, _ in scheduler.commands]
    assert commands[0] == ["qstat", "-Q"]
    assert commands[1][:9] == [
        "qsub", "-A", "SFC", "-q", "gen_S", "-b", "1", "-l",
        f"elapstim_req={DC.DEFAULT_WALLTIME}",
    ]
    assert not any(command[0] in {
        "pegasusinfo", "rbudgetcheck", "check_quota",
    } for command in commands)
    request = json.loads((submission / "request.json").read_text(encoding="utf-8"))
    assert "IZANAGI_TASK_RUN_ID" not in request["environment"]
    assert "IZANAGI_TASK_RUNS_ROOT" not in request["environment"]
    assert request["environment"] == {"PYTEST_ADDOPTS": "-q"}


def test_nonzero_child_relays_stdout_to_parent_stdout(tmp_path, capsys):
    scheduler = _Scheduler(
        child_rc=7,
        stdout=(
            b"nonzero-child-stdout\n"
            b"[Pegasus dispatch] request 0:424242.nqsv child stdout end\n"
        ),
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == 7
    frame = f"[Pegasus dispatch] request {_JOB_ID} child stdout"
    assert f"{frame} begin\n" in captured.out
    assert f"{frame} end\n" in captured.out
    assert "| nonzero-child-stdout\n" in captured.out
    assert f"| {frame} end\n" in captured.out
    assert captured.out.count(f"{frame} end\n") == 2
    assert captured.out.count(f"\n{frame} end\n") == 1


def test_nonzero_child_relays_only_last_sixty_four_kib_of_stdout(
    tmp_path,
    capsys,
):
    payload = (
        b"failure-head-must-be-trimmed\n"
        + b"x" * (65536 + 200)
        + b"\nfailure-tail\n"
    )
    scheduler = _Scheduler(child_rc=8, stdout=payload)
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()
    frame = f"[Pegasus dispatch] request {_JOB_ID} child stdout"
    after_begin = captured.out.split(f"{frame} begin", 1)[1]
    begin_detail, framed = after_begin.split("\n", 1)
    relayed = framed.split(f"{frame} end\n", 1)[0]
    expected_tail = payload.decode("utf-8")[-65536:]
    expected_relay = "".join(
        f"| {line}" for line in expected_tail.splitlines(keepends=True)
    )

    assert rc == 8
    assert "failure-head-must-be-trimmed" not in captured.out
    assert relayed == expected_relay
    assert begin_detail == (
        f" (size={len(payload)} bytes, omitted_bytes={len(payload) - 65536})"
    )


def test_success_relays_only_last_four_kib_of_stdout(tmp_path, capsys):
    retained_character = "界"
    scheduler = _Scheduler(
        child_rc=0,
        stdout=(
            "green-prefix-must-be-trimmed\n" + retained_character * 2000
        ).encode("utf-8"),
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()
    frame = f"[Pegasus dispatch] request {_JOB_ID} child stdout"
    after_begin = captured.out.split(f"{frame} begin", 1)[1]
    begin_detail, framed = after_begin.split("\n", 1)
    relayed = framed.split(f"{frame} end\n", 1)[0]
    retained = retained_character * (4096 // len(retained_character.encode()))

    assert rc == 0
    assert "green-prefix-must-be-trimmed" not in captured.out
    assert relayed == f"| {retained}\n"
    assert begin_detail == (
        f" (size={len(scheduler.stdout)} bytes, "
        f"omitted_bytes={len(scheduler.stdout) - len(retained.encode())})"
    )


def test_child_stderr_relays_only_to_parent_stderr(tmp_path, capsys):
    scheduler = _Scheduler(
        child_rc=6,
        stdout=b"stream-stdout-sentinel\n",
        stderr_prefix=b"stream-stderr-sentinel\n",
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == 6
    assert "stream-stderr-sentinel" in captured.err
    assert "stream-stderr-sentinel" not in captured.out
    assert "stream-stdout-sentinel" in captured.out
    assert "stream-stdout-sentinel" not in captured.err


def test_relay_limits_are_literal_four_and_sixty_four_kib():
    assert DC.DEFAULT_SUCCESS_RELAY_LIMIT_BYTES == 4096
    assert DC.DEFAULT_FAILURE_RELAY_LIMIT_BYTES == 65536


def test_relay_exception_does_not_change_child_rc(tmp_path):
    scheduler = _Scheduler(
        child_rc=11,
        stdout=b"relay-exception-child-output\n",
    )
    with mock.patch.object(
        DC,
        "_emit",
        side_effect=RuntimeError("injected relay failure"),
    ) as emit_mock:
        rc, _ = _dispatch(tmp_path, scheduler)

    assert rc == 11
    assert emit_mock.called
    assert any(
        "child stdout relay aborted after relay error" in call.args[0]
        for call in emit_mock.call_args_list
    )


@pytest.mark.parametrize(
    "raised",
    [
        DC._SignalAbort(signal.SIGTERM),
        SystemExit(23),
    ],
)
def test_relay_does_not_swallow_signal_or_system_exit(raised):
    record = {
        "tail": "relay-interrupted\n",
        "size": 18,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC, "_emit", side_effect=raised) as emit_mock,
        pytest.raises(type(raised)),
    ):
        DC._relay_scheduler_logs(
            record,
            None,
            request_id=_JOB_ID,
            successful=False,
        )

    assert emit_mock.called


def test_relay_signal_from_first_emit_is_re_raised_before_abort_notice():
    emit_count = 0

    def interrupt_first_emit(_text, *, stream):
        nonlocal emit_count
        del stream
        emit_count += 1
        if emit_count == 1:
            raise DC._SignalAbort(signal.SIGTERM)

    record = {
        "tail": "relay-interrupted\n",
        "size": 18,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC, "_emit", side_effect=interrupt_first_emit),
        pytest.raises(DC._SignalAbort),
    ):
        DC._relay_scheduler_logs(
            record,
            None,
            request_id=_JOB_ID,
            successful=False,
        )

    assert emit_count == 1


def test_broken_pipe_stops_relay_redirects_fd_and_reports_on_other_stream():
    class _Stream:
        def __init__(self, fd):
            self.fd = fd

        def fileno(self):
            return self.fd

    parent_stdout = _Stream(17)
    parent_stderr = _Stream(19)
    emitted = []

    def broken_stdout(text, *, stream):
        if stream is parent_stdout:
            raise BrokenPipeError("reader closed")
        emitted.append((text, stream))

    record = {
        "tail": "child-output\n",
        "size": 13,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC.sys, "stdout", parent_stdout),
        mock.patch.object(DC.sys, "stderr", parent_stderr),
        mock.patch.object(DC, "_emit", side_effect=broken_stdout),
        mock.patch.object(DC.os, "open", return_value=23) as open_mock,
        mock.patch.object(DC.os, "dup2") as dup2_mock,
        mock.patch.object(DC.os, "close") as close_mock,
    ):
        DC._relay_scheduler_logs(
            record,
            record,
            request_id=_JOB_ID,
            successful=False,
        )

    open_mock.assert_called_once_with(os.devnull, os.O_WRONLY)
    dup2_mock.assert_called_once_with(23, 17)
    close_mock.assert_called_once_with(23)
    assert emitted == [(
        f"[Pegasus dispatch] request {_JOB_ID} "
        "child log relay aborted after broken pipe on stdout\n",
        parent_stderr,
    )]


def test_stderr_broken_pipe_reports_relay_abort_on_parent_stdout():
    class _Stream:
        def __init__(self, fd):
            self.fd = fd

        def fileno(self):
            return self.fd

    parent_stdout = _Stream(17)
    parent_stderr = _Stream(19)
    emitted = []

    def broken_stderr(text, *, stream):
        if stream is parent_stderr:
            raise BrokenPipeError("reader closed")
        emitted.append((text, stream))

    record = {
        "tail": "child-output\n",
        "size": 13,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC.sys, "stdout", parent_stdout),
        mock.patch.object(DC.sys, "stderr", parent_stderr),
        mock.patch.object(DC, "_emit", side_effect=broken_stderr),
        mock.patch.object(DC.os, "open", return_value=23) as open_mock,
        mock.patch.object(DC.os, "dup2") as dup2_mock,
        mock.patch.object(DC.os, "close") as close_mock,
    ):
        DC._relay_scheduler_logs(
            None,
            record,
            request_id=_JOB_ID,
            successful=False,
        )

    open_mock.assert_called_once_with(os.devnull, os.O_WRONLY)
    dup2_mock.assert_called_once_with(23, 19)
    close_mock.assert_called_once_with(23)
    assert emitted == [(
        f"[Pegasus dispatch] request {_JOB_ID} "
        "child log relay aborted after broken pipe on stderr\n",
        parent_stdout,
    )]


def test_broken_pipe_on_relay_and_notice_redirects_both_streams():
    class _Stream:
        def __init__(self, fd):
            self.fd = fd

        def fileno(self):
            return self.fd

    parent_stdout = _Stream(17)
    parent_stderr = _Stream(19)
    record = {
        "tail": "child-output\n",
        "size": 13,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC.sys, "stdout", parent_stdout),
        mock.patch.object(DC.sys, "stderr", parent_stderr),
        mock.patch.object(
            DC,
            "_emit",
            side_effect=BrokenPipeError("reader closed"),
        ),
        mock.patch.object(DC.os, "open", side_effect=[23, 29]) as open_mock,
        mock.patch.object(DC.os, "dup2") as dup2_mock,
        mock.patch.object(DC.os, "close") as close_mock,
    ):
        DC._relay_scheduler_logs(
            record,
            record,
            request_id=_JOB_ID,
            successful=False,
        )

    assert open_mock.call_args_list == [
        mock.call(os.devnull, os.O_WRONLY),
        mock.call(os.devnull, os.O_WRONLY),
    ]
    assert dup2_mock.call_args_list == [
        mock.call(23, 17),
        mock.call(29, 19),
    ]
    assert close_mock.call_args_list == [
        mock.call(23),
        mock.call(29),
    ]


def test_relay_exception_closes_started_frame_with_abort_notice():
    parent_stdout = object()
    emitted = []
    frame = f"[Pegasus dispatch] request {_JOB_ID} child stdout"

    def fail_after_begin(text, *, stream):
        emitted.append((text, stream))
        if text == "| child-output\n":
            raise RuntimeError("injected relay failure")

    record = {
        "tail": "child-output\n",
        "size": 13,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(DC.sys, "stdout", parent_stdout),
        mock.patch.object(DC, "_emit", side_effect=fail_after_begin),
    ):
        DC._relay_scheduler_logs(
            record,
            None,
            request_id=_JOB_ID,
            successful=False,
        )

    assert emitted == [
        (f"{frame} begin\n", parent_stdout),
        ("| child-output\n", parent_stdout),
        (f"{frame} relay aborted after relay error\n", parent_stdout),
    ]


@pytest.mark.parametrize(
    "raised",
    [
        DC._SignalAbort(signal.SIGTERM),
        SystemExit(23),
    ],
)
def test_relay_abort_notice_does_not_swallow_signal_or_system_exit(raised):
    emit_count = 0

    def fail_relay_then_interrupt_notice(_text, *, stream):
        nonlocal emit_count
        del stream
        emit_count += 1
        if emit_count == 1:
            raise RuntimeError("injected relay failure")
        raise raised

    record = {
        "tail": "child-output\n",
        "size": 13,
        "omitted_bytes": 0,
    }
    with (
        mock.patch.object(
            DC,
            "_emit",
            side_effect=fail_relay_then_interrupt_notice,
        ),
        pytest.raises(type(raised)),
    ):
        DC._relay_scheduler_logs(
            record,
            None,
            request_id=_JOB_ID,
            successful=False,
        )

    assert emit_count == 2


def test_relay_exception_happens_after_receipt_is_persisted(tmp_path):
    scheduler = _Scheduler(
        child_rc=12,
        stdout=b"receipt-order-child-output\n",
    )
    receipt_path = (
        tmp_path / "dispatch" / "fixture-nonce" / "receipt.json"
    )
    persisted_when_called = []

    def exploding_emit(_text, *, stream):
        del stream
        persisted_when_called.append(receipt_path.is_file())
        raise RuntimeError("injected relay failure")

    with mock.patch.object(DC, "_emit", exploding_emit):
        rc, submission = _dispatch(tmp_path, scheduler)

    assert rc == 12
    assert persisted_when_called
    assert all(persisted_when_called)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == {
        "kind": "child", "rc": 12, "accounting_verified": True,
    }


def test_missing_compute_marker_relays_collected_stdout(tmp_path, capsys):
    scheduler = _Scheduler(
        marker=False,
        stdout=b"marker-infra-stdout\n",
        stderr_prefix=b"marker-infra-stderr\n",
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert "| marker-infra-stdout\n" in captured.out
    assert captured.err.index("compute-marker-not-observed") < captured.err.index(
        "| marker-infra-stderr\n",
    )
    assert scheduler.qstat_calls == 4


def test_accounting_grace_failure_relays_collected_stdout(tmp_path, capsys):
    scheduler = _Scheduler(
        accounting=False,
        stdout=b"accounting-infra-stdout\n",
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert "| accounting-infra-stdout\n" in captured.out
    assert scheduler.qstat_calls == 4


def test_post_collection_exception_relays_collected_stdout(tmp_path, capsys):
    scheduler = _Scheduler(
        stage="interpreter",
        child_rc=DC.INFRA_RC,
        stdout=b"exception-infra-stdout\n",
        stderr_prefix=b"exception-infra-stderr\n",
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert "| exception-infra-stdout\n" in captured.out
    assert captured.err.index(
        "Pegasus dispatch infrastructure failure: "
        "job bootstrap failure: stage=interpreter",
    ) < captured.err.index("| exception-infra-stderr\n")
    assert scheduler.qstat_calls == 4


def test_m7_dispatcher_request_allowlist_isolated_redundant_gate(tmp_path):
    """M7 dispatcher allowlist 単独変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_m7_dispatcher_request_allowlist_isolated_redundant_gate``。
    dispatcher の env allowlist だけを無効化すると本 node は赤くなる。manual ID/root は
    親・job-run の両方で除去し、sidecar/auto-off は transport として保持する。
    """

    scheduler = _Scheduler()
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    request = json.loads((submission / "request.json").read_text(encoding="utf-8"))
    assert request["environment"] == {"PYTEST_ADDOPTS": "-q"}
    assert {
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR",
    }.isdisjoint(request["environment"])


def test_m7_job_script_unset_isolated_redundant_gate(tmp_path):
    """M7 job script 単独変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_m7_job_script_unset_isolated_redundant_gate``。
    生成 job script の manual ID/root ``unset`` だけを無効化すると本 node は赤くなる。
    sidecar/auto-off marker は意図的に job script で保持する。
    """

    script = DC._job_script(
        repo_root=_REPO,
        submission_dir=tmp_path,
        request_path=tmp_path / "request.json",
        probe_path=tmp_path / "interpreter_probe.py",
        walltime="00:30:00",
    )
    assert (
        "unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT\n"
    ) in script


def test_tests_task_env_allowlist_carries_only_recording_transport(tmp_path):
    scheduler = _Scheduler()
    sidecar = str(tmp_path / "pytest-stats.json")
    root = tmp_path / "dispatch"
    rc = DC.dispatch(
        ["orchestrator/tests/test_sample.py", "-q"],
        task="tests",
        repo_root=_REPO,
        output_root=root,
        environ={
            "PATH": os.environ.get("PATH", ""),
            "PYTEST_ADDOPTS": "-q",
            "IZANAGI_TASK_RUN_ID": "must-not-propagate",
            "IZANAGI_TASK_RUNS_ROOT": "/private/ledger",
            "IZANAGI_TASK_RUN_SIDECAR": sidecar,
            "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
            "IZANAGI_UNLISTED": "must-not-propagate",
        },
        run_command=scheduler,
        clock=_Clock(),
        sleep=lambda _seconds: None,
        poll_interval_s=5,
        nonce="recording-transport",
    )
    assert rc == 0
    request = json.loads(
        (root / "recording-transport" / "request.json").read_text(
            encoding="utf-8",
        )
    )
    assert request["environment"] == {
        "PYTEST_ADDOPTS": "-q",
        "IZANAGI_TASK_RUN_SIDECAR": sidecar,
        "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
    }
    assert "IZANAGI_TASK_RUN_ID" not in request["environment"]
    assert "IZANAGI_TASK_RUNS_ROOT" not in request["environment"]


def test_job_script_preserves_sidecar_and_auto_off(tmp_path):
    script = DC._job_script(
        repo_root=_REPO,
        submission_dir=tmp_path,
        request_path=tmp_path / "request.json",
        probe_path=tmp_path / "interpreter_probe.py",
        walltime="00:30:00",
    )
    assert "unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT\n" in script
    assert "IZANAGI_TASK_RUN_SIDECAR" not in script.split(
        "unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT\n", 1
    )[1].split("exec", 1)[0]
    assert "IZANAGI_TASK_RUN_AUTO_RECORD" not in script.split(
        "unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT\n", 1
    )[1].split("exec", 1)[0]


def test_job_run_passes_sidecar_and_auto_off_to_tests_child(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v2",
            "repo_root": str(_REPO),
            "task": "tests",
            "args": ["orchestrator/tests/test_sample.py", "-q"],
            "environment": {
                "IZANAGI_TASK_RUN_ID": "must-not-reach-child",
                "IZANAGI_TASK_RUNS_ROOT": "/private/ledger",
                "IZANAGI_TASK_RUN_SIDECAR": str(tmp_path / "pytest-stats.json"),
                "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
            },
        }) + "\n",
        encoding="utf-8",
    )
    rc, calls = _job_run_with_mocked_child(request)
    assert rc == 0
    assert len(calls) == 1
    child_env = calls[0][1]["env"]
    assert child_env["IZANAGI_TASK_RUN_SIDECAR"] == str(
        tmp_path / "pytest-stats.json"
    )
    assert child_env["IZANAGI_TASK_RUN_AUTO_RECORD"] == "0"
    assert "IZANAGI_TASK_RUN_ID" not in child_env
    assert "IZANAGI_TASK_RUNS_ROOT" not in child_env


def test_fa1_rc0_request_disappearance_is_terminal_within_one_poll(tmp_path):
    scheduler = _Scheduler(states=("STG", "RUN", "DONE"), child_rc=0)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_reason"] == "request-disappeared-after-visibility"
    assert receipt["state_history"][-1] == {
        "elapsed_s": 10.0,
        "state": "END",
        "qstat_rc": 0,
        "request_present": False,
    }
    assert "overall-timeout" not in json.dumps(receipt)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Request State = QUE\n", "QUE"),
        ("Request State = STG\n", "QUE"),
        ("Current State           = Staging\n", "QUE"),
        ("Current State           = Queued\n", "QUE"),
        ("Current State           = Running\n", "RUN"),
        ("Current State           = Held\n", "HLD"),
        ("Request State = EXT\n", "END"),
        ("Current State           = Exiting\n", "END"),
        ("Current State           = Post-running\n", "END"),
        ("Current State           = Completed\n", "END"),
    ],
)
def test_scheduler_state_accepts_nqsv_full_and_abbreviated_forms(text, expected):
    assert DC._scheduler_state(text) == expected


def _gate_qstat_result(*, state="QUE", rc=0, stdout=None, stderr=""):
    if stdout is None:
        stdout = (
            f"Request ID = {_JOB_ID}\nRequest State = {state}\n"
            if rc == 0 else ""
        )
    return subprocess.CompletedProcess(
        ["qstat", "-f", "424242.nqsv"], rc, stdout, stderr,
    )


@pytest.mark.parametrize(
    ("state", "normalized"),
    [("QUE", "QUE"), ("HLD", "HLD"), ("STG", "QUE")],
)
def test_fresh_qstat_gate_accepts_que_hld_and_stg_snapshots(
    tmp_path, state, normalized,
):
    commands = []

    def runner(command, **_kwargs):
        command = list(command)
        commands.append(command)
        if command[0] == "qstat":
            return _gate_qstat_result(state=state)
        return subprocess.CompletedProcess(command, 0, "", "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        retry_interval_s=0,
    )

    assert commands == [
        ["qstat", "-f", "424242.nqsv"],
        ["qdel", "424242.nqsv"],
    ]
    assert qdel["attempted"] is True
    assert qdel["cleanup_policy"] == "fresh-qstat-gate/v1"
    assert qdel["gate"]["scheduler_state"] == normalized
    assert qdel["gate"]["allowed"] is True
    assert qdel["request_id"] == "424242.nqsv"
    assert qdel["returncode"] == 0
    assert qdel["stdout"] == ""
    assert qdel["stderr"] == ""
    assert qdel["job_may_remain"] is False


@pytest.mark.parametrize(
    ("current_state", "normalized"),
    [("Queued", "QUE"), ("Held", "HLD"), ("Staging", "QUE")],
)
def test_fresh_qstat_gate_accepts_current_state_only_snapshots(
    tmp_path, current_state, normalized,
):
    commands = []
    stdout = f"Request ID = {_JOB_ID}\nCurrent State = {current_state}\n"

    def runner(command, **_kwargs):
        command = list(command)
        commands.append(command)
        if command[0] == "qstat":
            return _gate_qstat_result(stdout=stdout)
        return subprocess.CompletedProcess(command, 0, "", "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )

    assert commands == [
        ["qstat", "-f", "424242.nqsv"],
        ["qdel", "424242.nqsv"],
    ]
    assert qdel["attempted"] is True
    assert qdel["gate"]["scheduler_state"] == normalized


@pytest.mark.parametrize(
    "state_line",
    [
        "Request State = Queued",
        "Current State = QUE",
        "Request State = Waiting",
    ],
    ids=["request-full-form", "current-abbreviation", "request-waiting"],
)
def test_fresh_qstat_gate_rejects_state_vocabulary_from_wrong_field(
    tmp_path, state_line,
):
    stdout = f"Request ID = {_JOB_ID}\n{state_line}\n"
    assert DC._scheduler_state(stdout) is None
    assert DC._target_bound_qstat_state(stdout, _JOB_ID) is None
    commands = []

    def runner(command, **_kwargs):
        command = list(command)
        commands.append(command)
        return _gate_qstat_result(stdout=stdout)

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )

    assert commands == [["qstat", "-f", "424242.nqsv"]]
    assert sum(command[0] == "qdel" for command in commands) == 0
    assert qdel["attempted"] is False
    assert qdel["gate"]["scheduler_state"] == "UNKNOWN"
    assert qdel["gate"]["reason"] == "target-state-unknown"


def test_fresh_qstat_gate_skips_explicit_end_snapshot(tmp_path):
    commands = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        return _gate_qstat_result(state="EXT")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )

    assert commands == [["qstat", "-f", "424242.nqsv"]]
    assert qdel["attempted"] is False
    assert qdel["gate"]["scheduler_state"] == "END"
    assert qdel["gate"]["reason"] == "state-not-cancellable"


@pytest.mark.parametrize(
    "stdout",
    [
        (
            "Request ID = 999999.nqsv\nRequest State = QUE\n"
            f"Request ID = {_JOB_ID}\nRequest State = RUN\n"
        ),
        (
            f"Request ID = {_JOB_ID}\n"
            "Request State = QUE\nRequest State = RUN\n"
        ),
        (
            f"Request ID = {_JOB_ID}\n"
            "Request State = QUE\nCurrent State = Running\n"
        ),
        "Request ID = 424242.nqsv\nState = RUN\nRequest State = QUE\n",
        (
            "Request State = RUN\n"
            "Request ID = 424242.nqsv\nCurrent State = Queued\n"
        ),
    ],
    ids=[
        "mixed-block",
        "duplicate-state",
        "request-current-conflict",
        "bare-state-conflict",
        "state-before-target-id",
    ],
)
def test_target_bound_gate_rejects_malformed_or_conflicting_state(
    tmp_path, stdout,
):
    assert DC._target_bound_qstat_state(stdout, _JOB_ID) is None
    commands = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout, "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )
    assert commands == [["qstat", "-f", "424242.nqsv"]]
    assert qdel["attempted"] is False
    assert qdel["gate"]["scheduler_state"] == "UNKNOWN"
    assert qdel["gate"]["reason"] == "target-state-unknown"


@pytest.mark.parametrize(
    "leading_whitespace",
    ["\x0c", "\x0b", "\u00a0"],
    ids=["form-feed", "vertical-tab", "nbsp"],
)
def test_target_bound_gate_counts_state_whitespace_recognized_by_existing_parser(
    tmp_path, leading_whitespace,
):
    state_line = f"{leading_whitespace}State = RUN\n"
    assert len(leading_whitespace) == 1
    assert DC._scheduler_state(state_line) == "RUN"
    if leading_whitespace == "\x0c":
        assert state_line.encode("utf-8").startswith(b"\x0cState")
    newly_visible_cancellable = (
        "Request ID = 424242.nqsv\n"
        f"{leading_whitespace}State = QUE\n"
    )
    assert DC._scheduler_state(newly_visible_cancellable) == "QUE"
    assert DC._target_bound_qstat_state(newly_visible_cancellable, _JOB_ID) is None
    stdout = (
        "Request ID = 424242.nqsv\n"
        f"{state_line}"
        "Request State = QUE\n"
    )
    assert DC._target_bound_qstat_state(stdout, _JOB_ID) is None
    commands = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout, "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )

    assert commands == [["qstat", "-f", "424242.nqsv"]]
    assert qdel["attempted"] is False
    assert qdel["gate"]["scheduler_state"] == "UNKNOWN"
    assert qdel["gate"]["reason"] == "target-state-unknown"


def test_target_bound_gate_parser_accepts_consistent_request_and_current_state():
    stdout = (
        f"Request ID = {_JOB_ID}\n"
        "Request State = STG\nCurrent State = Staging\n"
    )
    assert DC._target_bound_qstat_state(stdout, _JOB_ID) == "QUE"


def test_target_bound_gate_parser_accepts_existing_bare_state_form():
    stdout = "Request ID = 424242.nqsv\nState = STG\n"
    assert DC._target_bound_qstat_state(stdout, _JOB_ID) == "QUE"


def test_malformed_request_id_runs_neither_qstat_nor_qdel(tmp_path):
    commands = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        raise AssertionError("malformed ID must not reach scheduler")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id="--all", cwd=tmp_path, environ={},
    )

    assert commands == []
    assert qdel["attempted"] is False
    assert qdel["gate"]["qstat"]["attempted"] is False
    assert qdel["gate"]["reason"] == "malformed-request-id"


@pytest.mark.parametrize(
    ("failures", "allowed"),
    [(1, True), (2, True), (3, False)],
    ids=["error-que", "error-error-que", "all-transient-errors"],
)
def test_fresh_qstat_gate_retries_only_bounded_transient_errors(
    tmp_path, failures, allowed,
):
    assert DC._fresh_qstat_gated_qdel.__kwdefaults__["qstat_attempts"] == (
        DC.DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS
    )
    commands = []
    qstat_calls = 0

    def runner(command, **_kwargs):
        nonlocal qstat_calls
        command = list(command)
        commands.append(command)
        if command[0] == "qstat":
            qstat_calls += 1
            if qstat_calls <= failures:
                return _gate_qstat_result(
                    rc=153, stderr="connection temporarily unavailable",
                )
            return _gate_qstat_result(state="QUE")
        return subprocess.CompletedProcess(command, 0, "", "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        qstat_attempts=3,
        retry_interval_s=0,
    )

    expected_qstat_calls = failures + 1 if allowed else 3
    assert qstat_calls == expected_qstat_calls
    assert len(qdel["gate"]["qstat_attempts"]) == expected_qstat_calls
    assert qdel["attempted"] is allowed
    assert sum(command[0] == "qdel" for command in commands) == int(allowed)
    if not allowed:
        assert qdel["gate"]["reason"] == "qstat-transient-retries-exhausted"


def test_nonzero_qstat_with_target_que_stdout_never_bypasses_transient_gate(
    tmp_path,
):
    commands = []
    stdout = f"Request ID = {_JOB_ID}\nRequest State = QUE\n"

    def runner(command, **_kwargs):
        command = list(command)
        commands.append(command)
        return _gate_qstat_result(
            rc=153,
            stdout=stdout,
            stderr="connection temporarily unavailable",
        )

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        qstat_attempts=3,
        retry_interval_s=0,
    )

    assert commands == [["qstat", "-f", "424242.nqsv"]] * 3
    assert qdel["attempted"] is False
    assert len(qdel["gate"]["qstat_attempts"]) == 3
    assert qdel["gate"]["reason"] == "qstat-transient-retries-exhausted"


def test_fresh_qstat_gate_cleanup_budget_stops_retry_and_records_elapsed(
    tmp_path,
):
    assert DC.DEFAULT_CLEANUP_BUDGET_S == 90.0
    clock = _Clock()
    commands = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        clock.now += 91
        return _gate_qstat_result(
            rc=153, stderr="connection temporarily unavailable",
        )

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        cleanup_budget_s=90,
        clock=clock,
        sleep=clock.sleep,
    )

    assert commands == [["qstat", "-f", "424242.nqsv"]]
    assert qdel["attempted"] is False
    assert qdel["cleanup_elapsed_s"] == 91
    assert qdel["gate"]["reason"] == "cleanup-budget-exhausted"


def test_fresh_qstat_gate_clock_failure_before_qdel_is_gate_exception(tmp_path):
    clock_calls = 0
    commands = []

    def clock():
        nonlocal clock_calls
        clock_calls += 1
        if clock_calls > 1:
            raise OSError("injected cleanup clock failure")
        return 0.0

    def runner(command, **_kwargs):
        commands.append(list(command))
        return _gate_qstat_result(state="QUE")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={}, clock=clock,
    )

    assert commands == []
    assert qdel["attempted"] is False
    assert qdel["cleanup_elapsed_s"] is None
    assert "injected cleanup clock failure" in qdel["cleanup_elapsed_exception"]
    assert qdel["gate"]["reason"] == "gate-exception"


def test_fresh_qstat_gate_clips_transient_sleep_to_remaining_budget(tmp_path):
    clock = _Clock()
    sleeps = []

    def runner(command, **_kwargs):
        return _gate_qstat_result(
            rc=153, stderr="connection temporarily unavailable",
        )

    def sleep(seconds):
        sleeps.append(seconds)
        clock.sleep(seconds)

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        cleanup_budget_s=90,
        retry_interval_s=3600,
        clock=clock,
        sleep=sleep,
    )

    assert sleeps == [90]
    assert qdel["attempted"] is False
    assert qdel["gate"]["reason"] == "cleanup-budget-exhausted"


def test_fresh_qstat_gate_only_guards_snapshot_not_qdel_time_que_can_run(
    tmp_path,
):
    """QUE snapshot 後の RUN 遷移は非 atomic gate の残余リスクである。"""

    scheduler_state = "QUE"
    commands = []

    def runner(command, **_kwargs):
        nonlocal scheduler_state
        command = list(command)
        commands.append(command)
        if command[0] == "qstat":
            return _gate_qstat_result(state=scheduler_state)
        scheduler_state = "RUN"
        return subprocess.CompletedProcess(command, 0, "", "")

    qdel = DC._fresh_qstat_gated_qdel(
        runner, request_id=_JOB_ID, cwd=tmp_path, environ={},
    )

    assert qdel["attempted"] is True
    assert qdel["gate"]["scheduler_state"] == "QUE"
    assert scheduler_state == "RUN"
    assert commands[-1] == ["qdel", "424242.nqsv"]
    assert sum(command[0] == "qstat" for command in commands) == 1


def test_qdel_result_is_not_overwritten_by_post_qdel_gate_clock_exception(
    tmp_path,
):
    qdel_returned = False
    commands = []

    def clock():
        if qdel_returned:
            raise RuntimeError("post-qdel clock failure")
        return 0.0

    def runner(command, **_kwargs):
        nonlocal qdel_returned
        command = list(command)
        commands.append(command)
        if command[0] == "qstat":
            return _gate_qstat_result(state="QUE")
        qdel_returned = True
        return subprocess.CompletedProcess(command, 153, "", "qdel rejected")

    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=_JOB_ID,
        cwd=tmp_path,
        environ={},
        clock=clock,
    )

    assert qdel["attempted"] is True
    assert qdel["returncode"] == 153
    assert qdel["gate"]["allowed"] is True
    assert qdel["job_may_remain"] is True
    assert qdel["cleanup_elapsed_s"] is None
    assert "post-qdel clock failure" in qdel["cleanup_elapsed_exception"]
    assert commands == [
        ["qstat", "-f", "424242.nqsv"],
        ["qdel", "424242.nqsv"],
    ]


@pytest.mark.parametrize("seam", ["qdel-return", "metadata", "persist"])
def test_cleanup_signal_after_qdel_is_once_only_and_preserves_first_result(
    monkeypatch, tmp_path, seam,
):
    scheduler = _Scheduler(
        initial_qstat_failures=1,
        initial_qstat_error="Not permitted to access",
    )
    injected = False

    def invoke_registered_handler():
        nonlocal injected
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        injected = True
        handler(signal.SIGTERM, None)

    if seam == "qdel-return":
        real_run = DC._run

        def inject_after_qdel_return(run_command, command, **kwargs):
            nonlocal injected
            result = real_run(run_command, command, **kwargs)
            if list(command)[0] == "qdel" and not injected:
                invoke_registered_handler()
            return result

        monkeypatch.setattr(DC, "_run", inject_after_qdel_return)
    elif seam == "metadata":
        real_capture = DC._capture

        def inject_before_metadata(result):
            nonlocal injected
            captured = real_capture(result)
            if list(result.args)[0] == "qdel" and not injected:
                invoke_registered_handler()
            return captured

        monkeypatch.setattr(DC, "_capture", inject_before_metadata)
    else:
        real_persist = DC._persist_receipt

        def inject_before_persist(*args, **kwargs):
            nonlocal injected
            payload = args[2]
            if payload.get("qdel", {}).get("returncode") == 0 and not injected:
                invoke_registered_handler()
            return real_persist(*args, **kwargs)

        monkeypatch.setattr(DC, "_persist_receipt", inject_before_persist)

    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        nonce=f"cleanup-signal-{seam}",
    )

    assert rc == DC.INFRA_RC
    assert injected is True
    commands = [command for command, _ in scheduler.commands]
    assert sum(command[0] == "qdel" for command in commands) == 1
    receipt_path = submission / "receipt.json"
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["outcome"] == {
        "kind": "infra",
        "reason": f"_SignalAbort: signal {signal.SIGTERM}",
        "rc": DC.INFRA_RC,
    }
    assert receipt["qdel"]["attempted"] is True
    assert receipt["qdel"]["returncode"] == 0
    assert receipt["qdel"]["stdout"] == ""
    assert receipt["qdel"]["stderr"] == ""
    assert receipt["qdel"]["job_may_remain"] is False
    assert len(receipt["qdel"]["gate"]["qstat_attempts"]) == 1


def test_cleanup_claim_latch_survives_post_qdel_capture_exception(
    monkeypatch, tmp_path,
):
    scheduler = _Scheduler(
        states=("QUE", "QUE"),
        initial_qstat_failures=1,
        initial_qstat_error="Not permitted to access",
    )
    real_capture = DC._capture
    injected = False

    def fail_once_after_qdel_result(result):
        nonlocal injected
        captured = real_capture(result)
        if list(result.args)[0] == "qdel" and not injected:
            injected = True
            raise RuntimeError("injected post-qdel capture failure")
        return captured

    monkeypatch.setattr(DC, "_capture", fail_once_after_qdel_result)
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        nonce="cleanup-capture-exception",
    )

    assert rc == DC.INFRA_RC
    assert injected is True
    commands = [command for command, _ in scheduler.commands]
    assert sum(command[0] == "qdel" for command in commands) == 1
    assert scheduler.qstat_calls == 2
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == {
        "kind": "infra",
        "reason": "RuntimeError: injected post-qdel capture failure",
        "rc": DC.INFRA_RC,
    }
    assert receipt["qdel"]["attempted"] is True
    assert receipt["qdel"]["returncode"] == 0
    assert receipt["qdel"]["stdout"] == ""
    assert receipt["qdel"]["stderr"] == ""
    assert receipt["qdel"]["job_may_remain"] is False
    assert len(receipt["qdel"]["gate"]["qstat_attempts"]) == 1


def _best_effort_qdel_references(source: str, filename: str):
    tree = ast.parse(source, filename=filename)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    aliases = {"_best_effort_qdel"}
    default_aliases = {}
    imports = []

    def is_alias(value):
        return (
            isinstance(value, ast.Name) and value.id in aliases
        ) or (
            isinstance(value, ast.Attribute)
            and value.attr == "_best_effort_qdel"
        )

    def propagate_unpacking(target, value):
        if isinstance(target, ast.Name):
            if is_alias(value):
                aliases.add(target.id)
            return
        if (
            isinstance(target, (ast.Tuple, ast.List))
            and isinstance(value, (ast.Tuple, ast.List))
            and len(target.elts) == len(value.elts)
        ):
            for nested_target, nested_value in zip(target.elts, value.elts):
                propagate_unpacking(nested_target, nested_value)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for imported in node.names:
                if imported.name == "_best_effort_qdel":
                    aliases.add(imported.asname or imported.name)
                    imports.append(imported.asname or imported.name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            positional = [*node.args.posonlyargs, *node.args.args]
            pairs = zip(positional[-len(node.args.defaults):], node.args.defaults)
            keyword_pairs = zip(node.args.kwonlyargs, node.args.kw_defaults)
            for argument, default in (*pairs, *keyword_pairs):
                if default is not None and is_alias(default):
                    default_aliases.setdefault(node, set()).add(argument.arg)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                propagate_unpacking(target, value)

    def enclosing_scope(node):
        names = []
        current = parents.get(node)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(current.name)
            current = parents.get(current)
        return ".".join(reversed(names)) or "<module>"

    callers = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        scoped_aliases = set()
        current = node
        while current is not None:
            scoped_aliases.update(default_aliases.get(current, ()))
            current = parents.get(current)
        direct = (
            isinstance(node.func, ast.Name)
            and node.func.id in aliases | scoped_aliases
        )
        attributed = (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "_best_effort_qdel"
        )
        if direct or attributed:
            callers.append(enclosing_scope(node))
    return sorted(imports), sorted(callers)


@pytest.mark.parametrize(
    ("source", "expected_imports", "expected_callers"),
    [
        (
            "def cleanup():\n"
            "    deleter = _best_effort_qdel\n"
            "    deleter()\n",
            [],
            ["cleanup"],
        ),
        (
            "class Cleanup:\n"
            "    def run(self):\n"
            "        _best_effort_qdel()\n",
            [],
            ["Cleanup.run"],
        ),
        (
            "from tools.pegasus.dispatch_compute import "
            "_best_effort_qdel as deleter\n",
            ["deleter"],
            [],
        ),
        (
            "from tools.pegasus import dispatch_compute as dc\n"
            "deleter = dc._best_effort_qdel\n"
            "def cleanup():\n"
            "    deleter(...)\n",
            [],
            ["cleanup"],
        ),
        (
            "from tools.pegasus import dispatch_compute as dc\n"
            "def cleanup(deleter=dc._best_effort_qdel):\n"
            "    deleter(...)\n",
            [],
            ["cleanup"],
        ),
        (
            "from tools.pegasus import dispatch_compute as dc\n"
            "deleter, marker = dc._best_effort_qdel, object()\n"
            "def cleanup():\n"
            "    deleter(...)\n",
            [],
            ["cleanup"],
        ),
    ],
    ids=[
        "alias-binding",
        "class-method",
        "cross-module-import",
        "attribute-alias-binding",
        "default-argument-alias",
        "unpacking-alias-binding",
    ],
)
def test_best_effort_qdel_reference_scanner_covers_bypass_shapes(
    source, expected_imports, expected_callers,
):
    assert _best_effort_qdel_references(source, "<synthetic>") == (
        expected_imports,
        expected_callers,
    )


def test_best_effort_qdel_production_caller_is_only_fresh_gate():
    references = []
    for root in (_REPO / "tools", _REPO / "orchestrator"):
        for path in root.rglob("*.py"):
            imports, callers = _best_effort_qdel_references(
                path.read_text(encoding="utf-8"), str(path),
            )
            if imports or callers:
                references.append((path.relative_to(_REPO).as_posix(), imports, callers))
    assert references == [(
        "tools/pegasus/dispatch_compute.py",
        [],
        ["_fresh_qstat_gated_qdel"],
    )]


def test_qstat_error_during_poll_does_not_end_or_latch_job(tmp_path):
    scheduler = _Scheduler(states=("QUE", "ERROR", "RUN", "DONE"))
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    assert not (tmp_path / "dispatch" / "submission-disabled.json").exists()
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert [item["state"] for item in receipt["state_history"]] == [
        "QUE", "QSTAT_ERROR", "RUN", "END",
    ]


def test_job_script_binds_interpreter_path_repo_and_no_network_bootstrap(tmp_path):
    source = DC._interpreter_probe_source()
    assert "import pytest" in source
    assert "import xdist" in source
    assert "import packaging" in source

    repo = _REPO
    submission = tmp_path / "submission"
    submission.mkdir()
    script = DC._job_script(
        repo_root=repo,
        submission_dir=submission,
        request_path=submission / "request.json",
        probe_path=submission / "interpreter_probe.py",
        walltime="00:30:00",
    )
    assert '&& "$resolved" "$PROBE"' in script
    assert 'selected=$resolved' in script
    assert 'export PATH="$(dirname "$selected"):$PATH"' in script
    assert f'REPO={repo}' in script
    assert "PBS_O_WORKDIR" not in script
    assert "pip " not in script


def test_fa15_job_name_logs_match_job_script_and_are_collected(tmp_path):
    """M15 job-name ログ候補削除変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_fa15_job_name_logs_match_job_script_and_are_collected``。
    ``_log_candidates()`` から PBS job-name 形だけを削除すると、job が正常終了しても
    実測形 ``<name>.o<ID>`` / ``<name>.e<ID>`` を収集できず rc=16 へ変わる。
    """

    scheduler = _Scheduler(log_style="job-name")
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0

    job_name = DC._job_name(submission.name)
    script = (submission / "dispatch.sh").read_text(encoding="utf-8")
    assert f"#PBS -N {job_name}\n" in script
    assert DC._log_candidates(
        submission, stream="stdout", request_id=_JOB_ID,
    )[0] == submission / f"{job_name}.o424242"
    qsub = next(
        command for command, _ in scheduler.commands if command[0] == "qsub"
    )
    assert qsub[qsub.index("-N") + 1] == job_name

    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert Path(receipt["scheduler_logs"]["stdout"]["path"]).name == (
        f"{job_name}.o424242"
    )
    assert Path(receipt["scheduler_logs"]["stderr"]["path"]).name == (
        f"{job_name}.e424242"
    )


def test_fa15_dispatch_script_log_names_remain_backward_compatible(tmp_path):
    scheduler = _Scheduler(log_style="script")
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert Path(receipt["scheduler_logs"]["stdout"]["path"]).name == (
        "dispatch.sh.o424242"
    )
    assert Path(receipt["scheduler_logs"]["stderr"]["path"]).name == (
        "dispatch.sh.e424242"
    )


def test_fa15_logs_for_another_request_id_are_not_discovered(tmp_path):
    submission = tmp_path / "069a77c03e-other"
    submission.mkdir()
    for stem in ("izdw-069a77c03e", "dispatch.sh"):
        (submission / f"{stem}.o424243").write_bytes(b"other stdout")
        (submission / f"{stem}.e424243").write_bytes(b"other stderr")

    assert DC._find_log(
        submission, stream="stdout", request_id="0:424242.nqsv",
    ) is None
    assert DC._find_log(
        submission, stream="stderr", request_id="0:424242.nqsv",
    ) is None


def test_m5_dual_layer_interpreter_rejection_changes_acceptance_only_together(
    tmp_path,
):
    """M5 両層変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_m5_dual_layer_interpreter_rejection_changes_acceptance_only_together``。
    probe と ``_job_run()`` は冗長 gate なので、Python 3.9 の受理挙動が変わるのは
    両方の version reject を同時に無効化した場合だけである (DW-M01/DW-M04)。
    """

    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v1",
            "repo_root": str(_REPO),
            "pytest_args": ["--help"],
            "environment": {},
        }) + "\n",
        encoding="utf-8",
    )

    with mock.patch.object(DC.sys, "version_info", (3, 9, 13)):
        try:
            exec(compile(DC._interpreter_probe_source(), "<probe>", "exec"), {})
        except SystemExit as exc:
            probe_rc = int(exc.code)
        else:  # pragma: no cover - probe source is required to terminate explicitly
            probe_rc = 0

    pipeline_rc = DC.INFRA_RC
    if probe_rc == 0:
        fake_uname = type("Uname", (), {"nodename": "bnode114"})()
        with mock.patch.object(DC.sys, "version_info", (3, 9, 13)), \
                mock.patch.object(DC.os, "uname", return_value=fake_uname), \
                mock.patch.object(DC.os, "chdir"), \
                mock.patch.object(DC.subprocess, "call", return_value=0):
            pipeline_rc = DC._job_run(request)

    assert pipeline_rc == DC.INFRA_RC


def test_interpreter_stage_failure_is_fail_closed_and_preserved_in_receipt(
    tmp_path,
):
    scheduler = _Scheduler(stage="interpreter", child_rc=DC.INFRA_RC)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["result"]["stage"] == "interpreter"
    assert receipt["scheduler_logs"]["accounting_present"] is True
    assert receipt["outcome"]["kind"] == "infra"
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert scheduler.qstat_calls == 4
    assert receipt["qdel"]["cleanup_policy"] == "fresh-qstat-gate/v1"
    assert receipt["qdel"]["gate"]["scheduler_state"] == "END"


def test_m6_qstat_success_without_request_skips_qdel_and_create_only_latches(
    tmp_path, capsys,
):
    # M6/FA-9: qstat 成功なのに request 不在なら F47 型としてラッチする。
    scheduler = _Scheduler(visible=False)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    latch = tmp_path / "dispatch" / "submission-disabled.json"
    assert latch.is_file()
    original = latch.read_bytes()
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert scheduler.qstat_calls == 2
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"]["kind"] == "f47"
    assert receipt["immediate_qstat_attempts"][0]["classification"] == (
        "success-request-absent"
    )
    assert receipt["f49_immediate"]["qstat_visible"] is False
    assert receipt["f49_immediate"]["qstat_succeeded"] is True
    assert receipt["qdel"]["gate"]["reason"] == "request-absent"
    assert receipt["qdel"]["job_may_remain"] is True
    captured = capsys.readouterr()
    assert "ユーザー自身の端末" in captured.err
    assert "ジョブが残っている可能性" in captured.err

    second = _Scheduler()
    assert DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=second,
        nonce="must-not-run",
    ) == DC.INFRA_RC
    assert second.commands == []
    assert latch.read_bytes() == original


def test_immediate_qstat_transient_failure_retries_without_latching(tmp_path):
    scheduler = _Scheduler(initial_qstat_failures=1)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    assert not (tmp_path / "dispatch" / "submission-disabled.json").exists()
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert [item["returncode"] for item in receipt["immediate_qstat_attempts"]] == [
        153, 0,
    ]
    assert receipt["f49_immediate"] == {
        "qstat_succeeded": True,
        "qstat_visible": True,
    }


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("Not permitted to access", "permission"),
        ("Permission denied", "permission"),
        ("EACCES", "permission"),
        ("not authorized for request", "permission"),
        ("connection refused", "transient"),
        ("request timeout", "transient"),
        ("server busy", "transient"),
        ("unclassified scheduler error", "transient"),
    ],
)
def test_qstat_nonzero_response_classification_boundaries(response, expected):
    result = subprocess.CompletedProcess(
        ["qstat", "-f", _JOB_ID], 153, "", response,
    )
    assert DC._classify_qstat_response(result, _JOB_ID) == expected


def test_f47_literal_not_permitted_response_skips_qdel_and_latches(tmp_path):
    scheduler = _Scheduler(
        initial_qstat_failures=3,
        initial_qstat_error="Not permitted to access",
    )
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert scheduler.qstat_calls == 2
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    latch = json.loads(
        (tmp_path / "dispatch" / "submission-disabled.json").read_text(
            encoding="utf-8",
        ),
    )
    assert latch["reason"] == "qstat-permission-or-ownership-error"
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["immediate_qstat_attempts"][0]["classification"] == "permission"
    assert receipt["outcome"] == {
        "kind": "f47",
        "reason": "qstat-permission-or-ownership-error",
        "rc": DC.INFRA_RC,
    }
    assert receipt["qdel"]["gate"]["reason"] == "qstat-permission"


def test_immediate_qstat_failures_exhaust_to_infra_without_latching(tmp_path):
    scheduler = _Scheduler(initial_qstat_failures=3)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert not (tmp_path / "dispatch" / "submission-disabled.json").exists()
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"]["kind"] == "infra"
    assert "immediate-qstat-unavailable-after-retries" in receipt["outcome"]["reason"]
    assert scheduler.qstat_calls == 4
    assert [command for command, _ in scheduler.commands if command[0] == "qdel"] == [
        ["qdel", "424242.nqsv"],
    ]
    assert receipt["qdel"]["gate"]["scheduler_state"] == "QUE"
    assert receipt["qdel"]["gate"]["allowed"] is True


def test_compute_marker_is_cross_namespace_evidence_without_release_handshake(
    tmp_path,
):
    script = DC._job_script(
        repo_root=_REPO,
        submission_dir=tmp_path,
        request_path=tmp_path / "request.json",
        probe_path=tmp_path / "interpreter_probe.py",
        walltime="00:30:00",
    )
    assert DC._COMPUTE_MARKER_NAME in script
    assert script.index("mv \"$marker_tmp\" \"$MARKER\"") < script.index("selected=\"\"")
    assert "release" not in script.lower()
    assert "while" not in script


def test_missing_compute_marker_latches_only_after_visible_job_terminates(tmp_path):
    scheduler = _Scheduler(states=("QUE", "RUN", "DONE", "QUE"), marker=False)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    latch = json.loads(
        (tmp_path / "dispatch" / "submission-disabled.json").read_text(
            encoding="utf-8",
        ),
    )
    assert latch["reason"] == "compute-marker-not-observed"
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["f49_immediate"]["qstat_visible"] is True
    assert receipt["collection"]["compute_marker"]["valid"] is False
    assert scheduler.qstat_calls == 4
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert receipt["qdel"]["gate"]["reason"] == "terminal-history-conflict"


def test_create_only_nonce_collision_is_setup_infra_rc_with_receipt(tmp_path):
    root = tmp_path / "dispatch"
    (root / "duplicate").mkdir(parents=True)
    scheduler = _Scheduler()
    assert DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=root,
        run_command=scheduler,
        nonce="duplicate",
    ) == DC.INFRA_RC
    assert scheduler.commands == []
    receipt = json.loads(
        (root / "receipt-setup-duplicate.json").read_text(encoding="utf-8"),
    )
    assert receipt["outcome"]["kind"] == "infra"


def test_accounting_grace_failure_is_invocation_only_and_does_not_latch(
    tmp_path,
):
    scheduler = _Scheduler(accounting=False)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert not (tmp_path / "dispatch" / "submission-disabled.json").exists()
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"]["kind"] == "infra"
    assert "accounting-grace-expired" in receipt["outcome"]["reason"]
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert scheduler.qstat_calls == 4
    assert receipt["qdel"]["gate"]["scheduler_state"] == "END"


@pytest.mark.parametrize(
    "tail",
    [
        "worker recovered from MemoryError\n",
        (
            "Request ID: 999999.nqsv\n"
            "Group Name: SFC\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Group Name: SFC\n"
            "Started Request Time: now\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Group Name: OTHER\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Group Name: SFC\n"
            "Group Name: SFC\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Group Name: SFC\n"
            "Group Name: OTHER\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
    ],
)
def test_accounting_requires_matching_request_id_and_all_nqsv_fields(tail):
    assert not DC._accounting_present({"tail": tail}, _JOB_ID)


def test_accounting_accepts_measured_nqsv_shape_only_when_id_matches():
    tail = (
        "Request ID:             424242.nqsv\n"
        "Group Name:             SFC\n"
        "Started Request Time:   Thu Jul 30 10:03:23 2026\n"
        "Ended Request Time:     Thu Jul 30 10:10:20 2026\n"
        "  Elapse:               421S\n"
    )
    assert DC._accounting_present({"tail": tail}, _JOB_ID)
    assert not DC._accounting_present({"tail": tail}, "424243.nqsv")


def test_success_without_any_persisted_receipt_is_infra_rc(tmp_path, capsys):
    scheduler = _Scheduler(
        child_rc=0,
        stdout=b"receipt-persist-failure-stdout\n",
        stderr_prefix=b"receipt-persist-failure-stderr\n",
    )
    with mock.patch.object(DC, "_persist_receipt", return_value=None):
        rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert "| receipt-persist-failure-stdout\n" in captured.out
    assert captured.err.index(
        "Pegasus dispatch receipt を永続化できませんでした。",
    ) < captured.err.index("| receipt-persist-failure-stderr\n")


def test_scheduler_logs_are_tail_bounded_with_explicit_omission(tmp_path):
    scheduler = _Scheduler(
        stdout=b"x" * 1000,
        stderr_prefix=b"y" * 1000,
    )
    rc, submission = _dispatch(tmp_path, scheduler, log_limit_bytes=512)
    assert rc == 0
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    stdout = receipt["scheduler_logs"]["stdout"]
    stderr = receipt["scheduler_logs"]["stderr"]
    assert stdout["omitted_bytes"] == 488
    assert "先頭 488 bytes を省略" in stdout["tail"]
    assert stderr["omitted_bytes"] > 0
    assert "Request ID:" in stderr["tail"]
    assert "Group Name:" in stderr["tail"]


def test_hld_queue_timeout_qdels_and_receipts(tmp_path, capsys):
    scheduler = _Scheduler(states=("HLD", "HLD", "HLD", "HLD"))
    clock = _Clock()
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
        nonce="hld",
    )
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert (
        "Pegasus dispatch infrastructure failure: queue-wait-timeout"
        in captured.err
    )
    assert "Pegasus dispatch setup failure" not in captured.err
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads(
        (tmp_path / "dispatch" / "hld" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert [item["state"] for item in receipt["state_history"]] == [
        "HLD", "HLD", "HLD",
    ]
    assert "queue-wait-timeout" in receipt["outcome"]["reason"]
    assert scheduler.qstat_calls == 4
    assert receipt["qdel"]["cleanup_policy"] == "fresh-qstat-gate/v1"
    assert receipt["qdel"]["gate"]["scheduler_state"] == "HLD"
    assert receipt["qdel"]["gate"]["allowed"] is True
    assert receipt["schema_version"] == "pegasus-dispatch-receipt/v2"


@pytest.mark.parametrize(
    ("qdel_returncode", "qdel_exception"),
    [(153, None), (0, OSError("injected qdel failure"))],
    ids=["nonzero", "exception"],
)
def test_allowed_qdel_failure_records_job_may_remain_and_warns(
    tmp_path, capsys, qdel_returncode, qdel_exception,
):
    scheduler = _Scheduler(
        states=("HLD", "HLD", "HLD", "HLD"),
        qdel_returncode=qdel_returncode,
        qdel_exception=qdel_exception,
    )
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        poll_interval_s=5,
        queue_wait_timeout_s=10,
        nonce=f"qdel-failure-{qdel_returncode}-{qdel_exception is not None}",
    )
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    qdel = receipt["qdel"]
    assert qdel["attempted"] is True
    assert qdel["gate"]["allowed"] is True
    assert qdel["job_may_remain"] is True
    assert scheduler.qstat_calls == 4
    assert len(qdel["gate"]["qstat_attempts"]) == 1
    assert [
        command for command, _ in scheduler.commands
        if command[0] in {"qstat", "qdel"} and command != ["qstat", "-Q"]
    ] == [
        ["qstat", "-f", "424242.nqsv"],
        ["qstat", "-f", "424242.nqsv"],
        ["qstat", "-f", "424242.nqsv"],
        ["qstat", "-f", "424242.nqsv"],
        ["qdel", "424242.nqsv"],
    ]
    assert "ジョブが残っている可能性" in captured.err
    if qdel_exception is None:
        assert qdel["returncode"] == 153
    else:
        assert "injected qdel failure" in qdel["exception"]


def test_claim_cleanup_finally_latches_and_blocks_next_dispatch(tmp_path):
    scheduler = _Scheduler(
        states=("HLD", "HLD", "HLD", "HLD"),
        qdel_returncode=153,
    )

    rc, _submission = _dispatch(
        tmp_path,
        scheduler,
        poll_interval_s=5,
        queue_wait_timeout_s=10,
        nonce="cleanup-latch",
    )

    assert rc == DC.INFRA_RC
    hold = tmp_path / "dispatch" / DC._ORPHAN_HOLD_NAME
    assert hold.is_file()
    second = _Scheduler()
    assert DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=second,
        nonce="must-not-run",
    ) == DC.INFRA_RC
    assert second.commands == []


def test_queue_wait_starts_when_qsub_returns_not_before_preflight(tmp_path):
    scheduler = _Scheduler()
    clock = _Clock()

    def delayed_scheduler(command, **kwargs):
        result = scheduler(command, **kwargs)
        if list(command) == ["qstat", "-Q"]:
            clock.now += 11
        elif list(command)[0] == "qsub":
            clock.now += 7
        return result

    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=delayed_scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="timing",
    )
    assert rc == 0
    receipt = json.loads(
        (tmp_path / "dispatch" / "timing" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert receipt["queue_wait_s"] == 5.0
    assert receipt["queue_wait_observed"] is True
    assert "queue_wait_included_in_parent_duration" not in receipt


def test_fast_job_without_observed_run_records_queue_wait_upper_bound(tmp_path):
    scheduler = _Scheduler(states=("QUE", "DONE"))
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["queue_wait_s"] == 5.0
    assert receipt["queue_wait_observed"] is False


def test_qsub_parse_failure_discovers_request_and_attempts_qdel(tmp_path):
    scheduler = _Scheduler(qsub_stdout="accepted with opaque response\n")
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    qdel = [command for command, _ in scheduler.commands if command[0] == "qdel"]
    assert qdel == [["qdel", "424242.nqsv"]]
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["request_id_discovery"]["matched_by"] == (
        "request-name+submission-dir"
    )
    assert receipt["qdel"]["attempted"] is True
    assert scheduler.qstat_calls == 1
    assert receipt["qdel"]["gate"]["scheduler_state"] == "QUE"


def test_request_id_discovery_failure_skips_gate_commands_and_warns(
    tmp_path, capsys,
):
    scheduler = _Scheduler(
        qsub_stdout="accepted with opaque response\n",
        discovery_visible=False,
    )
    rc, submission = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert scheduler.qstat_calls == 0
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["request_id_discovery"]["candidates"] == []
    assert receipt["qdel"]["cleanup_policy"] == "fresh-qstat-gate/v1"
    assert receipt["qdel"]["gate"]["qstat"]["attempted"] is False
    assert receipt["qdel"]["gate"]["reason"] == "request-id-unavailable"
    assert receipt["qdel"]["reason"] == (
        "qsub accepted but request ID discovery failed"
    )
    assert "ジョブが残っている可能性" in captured.err


def test_request_id_unavailable_precedes_initial_cleanup_clock_failure(tmp_path):
    clock_calls = 0
    commands = []

    def failing_clock():
        nonlocal clock_calls
        clock_calls += 1
        raise OSError("injected initial cleanup clock failure")

    def runner(command, **_kwargs):
        commands.append(list(command))
        raise AssertionError("missing request ID must not reach scheduler")

    submission_dir = tmp_path / "opaque-submission"
    qdel = DC._fresh_qstat_gated_qdel(
        runner,
        request_id=None,
        cwd=tmp_path,
        environ={},
        clock=failing_clock,
        job_name="izdw-opaque",
        submission_dir=submission_dir,
    )

    assert clock_calls == 0
    assert commands == []
    assert qdel["attempted"] is False
    assert qdel["gate"]["reason"] == "request-id-unavailable"
    assert qdel["reason"] == "qsub accepted but request ID discovery failed"
    assert qdel["job_name"] == "izdw-opaque"
    assert qdel["submission_dir"] == str(submission_dir)


def test_malformed_qsub_request_id_runs_no_qstat_by_id_or_qdel(tmp_path):
    scheduler = _Scheduler(qsub_stdout="Request --all submitted to queue.\n")
    rc, submission = _dispatch(tmp_path, scheduler)

    assert rc == DC.INFRA_RC
    assert scheduler.qstat_calls == 0
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert not any(
        command[:2] == ["qstat", "-f"] for command, _ in scheduler.commands
    )
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert "malformed-request-id" in receipt["outcome"]["reason"]
    assert receipt["qdel"]["gate"]["reason"] == "malformed-request-id"


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_qsub_success_signal_during_receipt_capture_discovers_and_qdels(
    monkeypatch, tmp_path, signum,
):
    scheduler = _Scheduler()
    real_capture = DC._capture
    interrupted = False

    def interrupt_qsub_capture(result):
        nonlocal interrupted
        if result.args[0] == "qsub" and not interrupted:
            interrupted = True
            raise DC._SignalAbort(signum)
        return real_capture(result)

    monkeypatch.setattr(DC, "_capture", interrupt_qsub_capture)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert interrupted is True
    qdel = [command for command, _ in scheduler.commands if command[0] == "qdel"]
    assert qdel == [["qdel", "424242.nqsv"]]
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["request_id_discovery"]["matched_by"] == (
        "request-name+submission-dir"
    )
    assert receipt["qdel"]["attempted"] is True
    assert receipt["outcome"]["reason"] == f"_SignalAbort: signal {signum}"
    assert scheduler.qstat_calls == 1
    assert receipt["qdel"]["gate"]["scheduler_state"] == "QUE"


def test_scheduler_exception_after_qsub_skips_qdel_and_receipts_gate_error(
    tmp_path,
):
    scheduler = _Scheduler()

    def exploding(command, **kwargs):
        if list(command)[:2] == ["qstat", "-f"]:
            scheduler.commands.append((list(command), kwargs))
            raise OSError("injected qstat failure")
        return scheduler(command, **kwargs)

    clock = _Clock()
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        run_command=exploding,
        clock=clock,
        sleep=clock.sleep,
        nonce="exception",
    )
    assert rc == DC.INFRA_RC
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads(
        (tmp_path / "dispatch" / "exception" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert "injected qstat failure" in receipt["outcome"]["reason"]
    assert receipt["qdel"]["gate"]["reason"] == "qstat-exception"
    assert len(receipt["qdel"]["gate"]["qstat_attempts"]) == 1


@pytest.mark.parametrize(
    "gate_reason",
    [
        "request-absent",
        "terminal-history-conflict",
        "request-id-unavailable",
        "state-not-cancellable",
        "fresh-cancellable-snapshot",
        None,
    ],
)
def test_orphan_hold_signature_uses_only_literal_job_may_remain(gate_reason):
    qdel = {"job_may_remain": True, "gate": {"reason": gate_reason}}
    assert DC._orphan_hold_required(qdel) is True


@pytest.mark.parametrize(
    "qdel",
    [
        {},
        {"job_may_remain": False},
        {"job_may_remain": 1},
        {"job_may_remain": "true"},
        {"job_may_remain": None},
    ],
)
def test_orphan_hold_signature_rejects_false_missing_and_non_bool(qdel):
    assert DC._orphan_hold_required(qdel) is False


@pytest.mark.parametrize("gate_reason", ["request-absent", "terminal-history-conflict"])
def test_request_absent_and_terminal_history_receipts_latch_hold(
    tmp_path, gate_reason,
):
    root = tmp_path / "dispatch"
    root.mkdir()
    qdel = {
        "attempted": False,
        "job_may_remain": True,
        "gate": {"reason": gate_reason},
    }

    hold = DC._latch_orphan_hold(
        root,
        qdel=qdel,
        submission_dir=root / "nonce",
        request_id=_JOB_ID,
        job_name="izdw-test",
    )

    assert hold == root / DC._ORPHAN_HOLD_NAME
    payload = json.loads(hold.read_text(encoding="utf-8"))
    assert payload["qdel"]["job_may_remain"] is True
    assert payload["qdel"]["gate"]["reason"] == gate_reason
    assert payload["request_id"] == _JOB_ID


def test_orphan_hold_record_is_create_only(tmp_path):
    root = tmp_path / "dispatch"
    root.mkdir()
    first_qdel = {
        "attempted": False,
        "job_may_remain": True,
        "gate": {"reason": "request-absent"},
    }
    hold = DC._latch_orphan_hold(
        root,
        qdel=first_qdel,
        submission_dir=root / "first",
        request_id=_JOB_ID,
        job_name="izdw-first",
    )
    assert hold is not None
    original = hold.read_bytes()

    second = DC._latch_orphan_hold(
        root,
        qdel={
            "attempted": True,
            "job_may_remain": True,
            "returncode": 153,
            "gate": {"reason": "state-not-cancellable"},
        },
        submission_dir=root / "second",
        request_id="999.nqsv",
        job_name="izdw-second",
    )

    assert second == hold
    assert hold.read_bytes() == original


def test_orphan_hold_write_error_is_recorded_and_not_reported_as_success(
    tmp_path, monkeypatch, capsys,
):
    root = tmp_path / "dispatch"
    root.mkdir()
    qdel = {
        "attempted": False,
        "job_may_remain": True,
        "gate": {"reason": "request-absent"},
    }

    def fail_write(path, payload, **kwargs):
        raise OSError("injected hold write failure")

    monkeypatch.setattr(DC, "_write_json_x", fail_write)
    result = DC._latch_orphan_hold(
        root,
        qdel=qdel,
        submission_dir=root / "nonce",
        request_id=_JOB_ID,
        job_name="izdw-test",
    )

    assert result is None
    assert "injected hold write failure" in qdel["hold_error"]
    assert not (root / DC._ORPHAN_HOLD_NAME).exists()
    assert "保存できませんでした" in capsys.readouterr().err


def test_existing_orphan_hold_blocks_before_any_scheduler_command(tmp_path, capsys):
    root = tmp_path / "dispatch"
    root.mkdir()
    (root / DC._ORPHAN_HOLD_NAME).write_text("not-json\n", encoding="utf-8")
    scheduler = _Scheduler()

    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=root,
        run_command=scheduler,
        nonce="must-not-exist",
    )

    assert rc == DC.INFRA_RC
    assert scheduler.commands == []
    assert not (root / "must-not-exist").exists()
    assert "orphan hold" in capsys.readouterr().err


def test_orphan_hold_lstat_error_blocks_before_any_scheduler_command(
    tmp_path, monkeypatch,
):
    root = tmp_path / "dispatch"
    root.mkdir()
    hold = root / DC._ORPHAN_HOLD_NAME
    real_lstat = os.lstat

    def indeterminate(path, *args, **kwargs):
        if Path(path) == hold:
            raise OSError("injected lstat failure")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(DC.os, "lstat", indeterminate)
    scheduler = _Scheduler()

    assert DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=root,
        run_command=scheduler,
        nonce="must-not-exist",
    ) == DC.INFRA_RC
    assert scheduler.commands == []
    assert not (root / "must-not-exist").exists()


def test_f47_latch_precedes_orphan_hold_and_hold_remains_independent(
    tmp_path, capsys,
):
    root = tmp_path / "dispatch"
    root.mkdir()
    f47 = root / "submission-disabled.json"
    f47.write_text("{}\n", encoding="utf-8")
    (root / DC._ORPHAN_HOLD_NAME).write_text("{}\n", encoding="utf-8")
    scheduler = _Scheduler()

    assert DC.dispatch([], output_root=root, run_command=scheduler) == DC.INFRA_RC
    first = capsys.readouterr().err
    assert "既存の F47 型ラッチ" in first
    assert "orphan hold があるため" not in first
    assert scheduler.commands == []

    f47.unlink()
    assert DC.dispatch([], output_root=root, run_command=scheduler) == DC.INFRA_RC
    second = capsys.readouterr().err
    assert "orphan hold があるため" in second
    assert scheduler.commands == []


def test_qsub_result_unobserved_discovers_and_holds_without_qdel(tmp_path):
    scheduler = _Scheduler()

    def interrupted_qsub(command, **kwargs):
        if list(command)[0] == "qsub":
            scheduler.commands.append((list(command), kwargs))
            raise DC._SignalAbort(signal.SIGTERM)
        return scheduler(command, **kwargs)

    clock = _Clock()
    root = tmp_path / "dispatch"
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=root,
        run_command=interrupted_qsub,
        clock=clock,
        sleep=clock.sleep,
        nonce="qsub-unknown",
    )

    assert rc == DC.INFRA_RC
    commands = [command for command, _ in scheduler.commands]
    assert [command[0] for command in commands] == ["qstat", "qsub", "qstat"]
    assert not any(command[0] == "qdel" for command in commands)
    hold = json.loads((root / DC._ORPHAN_HOLD_NAME).read_text(encoding="utf-8"))
    assert hold["qdel"]["attempted"] is False
    assert hold["qdel"]["gate"]["reason"] == "qsub-result-unobserved"
    assert hold["request_id"] is None
    # create-only hold の後で判明した request ID は receipt 側へだけ追記される。
    hold = json.loads((root / "qsub-unknown" / "receipt.json").read_text(encoding="utf-8"))
    assert hold["request_id"] == _JOB_ID


def test_observed_nonzero_qsub_does_not_latch_orphan_hold(tmp_path):
    scheduler = _Scheduler()

    def rejected_qsub(command, **kwargs):
        if list(command)[0] == "qsub":
            scheduler.commands.append((list(command), kwargs))
            return subprocess.CompletedProcess(command, 153, "", "rejected")
        return scheduler(command, **kwargs)

    root = tmp_path / "dispatch"
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=root,
        run_command=rejected_qsub,
        nonce="qsub-rejected",
    )

    assert rc == DC.INFRA_RC
    assert not (root / DC._ORPHAN_HOLD_NAME).exists()
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)


def test_overall_walltime_plus_grace_bound_skips_qdel_for_fresh_running_job(
    tmp_path,
):
    scheduler = _Scheduler(states=("RUN", "RUN", "RUN"))
    clock = _Clock()
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        walltime="00:00:01",
        overall_grace_s=0,
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=1,
        queue_wait_timeout_s=20,
        nonce="overall",
    )
    assert rc == DC.INFRA_RC
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads(
        (tmp_path / "dispatch" / "overall" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert "overall-timeout" in receipt["outcome"]["reason"]
    assert scheduler.qstat_calls == 3
    assert receipt["qdel"]["gate"]["scheduler_state"] == "RUN"
    assert receipt["qdel"]["gate"]["reason"] == "state-not-cancellable"


def test_queue_wait_does_not_consume_observed_run_budget(tmp_path):
    scheduler = _Scheduler(states=("QUE", "QUE", "RUN", "RUN", "DONE"))
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
    )

    assert rc == 0
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["queue_wait_s"] == 2.0
    assert receipt["queue_wait_observed"] is True


def test_overall_grace_allows_done_at_observed_run_deadline(tmp_path):
    scheduler = _Scheduler(states=(
        "QUE", "RUN", "UNRECOGNIZED", "UNRECOGNIZED", "DONE",
    ))
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
    )

    assert rc == 0
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert "overall-timeout" not in receipt["outcome"].get("reason", "")


def test_post_run_unknown_state_uses_first_observation_deadline(tmp_path):
    scheduler = _Scheduler(states=(
        "QUE", "RUN", "RUN", "UNRECOGNIZED", "UNRECOGNIZED",
        "UNRECOGNIZED",
    ))
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
    )

    assert rc == DC.INFRA_RC
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert "overall-timeout" in receipt["outcome"]["reason"]
    assert receipt["state_history"][-1]["elapsed_s"] == 4.0
    assert any(item["state"] == "RUN" for item in receipt["state_history"])
    assert scheduler.qstat_calls == 6
    assert receipt["qdel"]["gate"]["scheduler_state"] == "UNKNOWN"


def test_nonzero_qstat_run_stdout_does_not_restart_deadline(tmp_path):
    trusted = _Scheduler(states=(
        "QUE", "RUN", "UNRECOGNIZED", "UNRECOGNIZED", "UNRECOGNIZED",
        "UNRECOGNIZED",
    ))
    trusted_rc, trusted_submission = _dispatch(
        tmp_path / "trusted",
        trusted,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
        nonce="trusted-run",
    )
    trusted_receipt = json.loads(
        (trusted_submission / "receipt.json").read_text(encoding="utf-8"),
    )

    untrusted = _Scheduler(
        states=(
            "QUE", "ERROR", "UNRECOGNIZED", "UNRECOGNIZED",
            "ERROR", "ERROR", "ERROR",
        ),
        qstat_error_stdout="Request State = RUN\n",
    )
    untrusted_rc, untrusted_submission = _dispatch(
        tmp_path / "untrusted",
        untrusted,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
        nonce="untrusted-run",
    )
    untrusted_receipt = json.loads(
        (untrusted_submission / "receipt.json").read_text(encoding="utf-8"),
    )

    assert trusted_rc == DC.INFRA_RC
    assert trusted_receipt["state_history"][-1]["elapsed_s"] == 4.0
    assert not any(command[0] == "qdel" for command, _ in trusted.commands)
    assert trusted.qstat_calls == 6
    assert trusted_receipt["qdel"]["gate"]["scheduler_state"] == "UNKNOWN"
    assert untrusted_rc == DC.INFRA_RC
    assert not any(command[0] == "qdel" for command, _ in untrusted.commands)
    assert "overall-timeout" in untrusted_receipt["outcome"]["reason"]
    assert untrusted_receipt["state_history"][-1]["elapsed_s"] == 3.0
    assert untrusted_receipt["state_history"][-1]["state"] == "UNKNOWN"
    assert untrusted_receipt["queue_wait_s"] == 1.0
    assert untrusted_receipt["queue_wait_observed"] is True
    assert untrusted.qstat_calls == 7
    assert len(untrusted_receipt["qdel"]["gate"]["qstat_attempts"]) == 3
    assert untrusted_receipt["qdel"]["gate"]["reason"] == (
        "qstat-transient-retries-exhausted"
    )


def test_trusted_run_after_nonzero_run_stdout_restarts_deadline(tmp_path):
    scheduler = _Scheduler(
        states=("QUE", "ERROR", "RUN", "RUN", "DONE"),
        qstat_error_stdout="Request State = RUN\n",
    )
    rc, submission = _dispatch(
        tmp_path,
        scheduler,
        walltime="00:00:02",
        overall_grace_s=1,
        poll_interval_s=1,
        queue_wait_timeout_s=10,
        accounting_grace_s=0,
    )

    assert rc == 0
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["queue_wait_s"] == 1.0
    assert receipt["queue_wait_observed"] is True


def test_unknown_scheduler_state_remains_bounded_by_overall_timeout(tmp_path):
    scheduler = _Scheduler(states=("UNRECOGNIZED",) * 4)
    clock = _Clock()
    rc = DC.dispatch(
        [],
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        walltime="00:00:01",
        overall_grace_s=0,
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=1,
        queue_wait_timeout_s=20,
        nonce="unknown",
    )
    assert rc == DC.INFRA_RC
    receipt = json.loads(
        (tmp_path / "dispatch" / "unknown" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert receipt["state_history"][0]["state"] == "UNKNOWN"
    assert "overall-timeout" in receipt["outcome"]["reason"]
    assert scheduler.qstat_calls == 3
    assert not any(command[0] == "qdel" for command, _ in scheduler.commands)
    assert receipt["qdel"]["gate"]["scheduler_state"] == "UNKNOWN"


def test_progress_output_is_explicitly_flushed():
    with mock.patch("builtins.print") as printed:
        DC._progress("状態: RUN")
    printed.assert_called_once_with("[Pegasus dispatch] 状態: RUN", flush=True)


def test_default_walltime_preserves_acceptance_runtime_margin():
    # [T-656] 受入全走で実測した最大所要時間と、既定値に要求する余裕。
    ACCEPTANCE_FULL_RUN_MAX_S = 1809
    REQUIRED_MARGIN_FACTOR = 1.25

    assert DC._walltime_seconds(DC.DEFAULT_WALLTIME) >= (
        ACCEPTANCE_FULL_RUN_MAX_S * REQUIRED_MARGIN_FACTOR
    )


def test_walltime_override_is_bound_to_pbs_and_total_bound(tmp_path):
    scheduler = _Scheduler()
    rc, _ = _dispatch(
        tmp_path,
        scheduler,
        walltime="01:02:03",
        overall_grace_s=7,
    )
    assert rc == 0
    qsub = next(command for command, _ in scheduler.commands if command[0] == "qsub")
    assert "elapstim_req=01:02:03" in qsub


def _job_run_with_mocked_child(request_path: Path, *, child_rc: int = 0):
    """計算ノード側 launcher を hostname / chdir / 子起動を注入して駆動する。"""

    fake_uname = type("Uname", (), {"nodename": "bnode114"})()
    calls: list[tuple[list[str], dict]] = []

    def record(argv, **kwargs):
        calls.append((list(argv), kwargs))
        return child_rc

    with mock.patch.object(DC.os, "uname", return_value=fake_uname), \
            mock.patch.object(DC.os, "chdir"), \
            mock.patch.object(DC, "_import_probe_modules"), \
            mock.patch.object(DC.subprocess, "call", side_effect=record):
        rc = DC._job_run(request_path)
    return rc, calls


def test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc(tmp_path):
    """M11 期待赤: _dispatch_impl の task 照合を外すと未知 task が scheduler へ届く。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc``。
    """

    assert set(DC.TASKS) == {"tests", "provenance"}
    assert DC.DEFAULT_TASK == "tests"

    root = tmp_path / "dispatch"
    scheduler = _Scheduler()
    rc = DC.dispatch(
        ["--range", "A..B"],
        task="shell",
        repo_root=_REPO,
        output_root=root,
        run_command=scheduler,
        nonce="unknown-task",
    )
    assert rc == DC.INFRA_RC
    assert scheduler.commands == []
    assert not (root / "unknown-task").exists()
    receipt = json.loads(
        (root / "receipt-setup-unknown-task.json").read_text(encoding="utf-8"),
    )
    assert receipt["outcome"]["kind"] == "infra"
    assert receipt["outcome"]["rc"] == DC.INFRA_RC
    assert "ValueError" in receipt["outcome"]["reason"]
    assert receipt["request"] == {"task": "shell", "args": ["--range", "A..B"]}

    # CLI 面も閉じている (argparse choices)。
    with pytest.raises(SystemExit) as raised:
        DC.main(["--task", "shell", "--range", "A..B"])
    assert raised.value.code == 2


def test_tests_task_env_allowlist_is_exact():
    assert DC.TASKS["tests"].env_allowlist == frozenset({
        "PYTEST_ADDOPTS",
        "IZANAGI_TEST_NPROC",
        "IZANAGI_TEST_TRIGGER",
        "IZANAGI_TASK_RUN_SIDECAR",
        "IZANAGI_TASK_RUN_AUTO_RECORD",
        "PYTHONDONTWRITEBYTECODE",
        "IZANAGI_T080_E2E",
        "IZANAGI_RUN_GROWTH_HELD_TESTS",
    })


def test_t080_e2e_opt_in_env_is_projected_into_tests_request(tmp_path):
    scheduler = _Scheduler()
    clock = _Clock()
    rc = DC.dispatch(
        ["orchestrator/tests/test_s8b_oracle_driver.py", "-q"],
        task="tests",
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        environ={
            "PATH": os.environ.get("PATH", ""),
            "IZANAGI_T080_E2E": "1",
            "IZANAGI_UNLISTED": "must-not-propagate",
        },
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="t080-opt-in-nonce",
    )
    assert rc == 0

    request = json.loads(
        (
            tmp_path / "dispatch" / "t080-opt-in-nonce" / "request.json"
        ).read_text(encoding="utf-8"),
    )
    assert request["environment"] == {"IZANAGI_T080_E2E": "1"}


def test_python_dont_write_bytecode_env_is_projected_into_tests_request(
    tmp_path,
):
    operational_scheduler = _Scheduler()
    operational_clock = _Clock()
    operational_rc = DC.dispatch(
        ["orchestrator/tests/test_pegasus_dispatch_compute.py", "-q"],
        task="tests",
        repo_root=_REPO,
        output_root=tmp_path / "operational-dispatch",
        environ={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "IZANAGI_UNLISTED": "must-not-propagate",
        },
        run_command=operational_scheduler,
        clock=operational_clock,
        sleep=operational_clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="pythondontwritebytecode-operational-nonce",
    )
    assert operational_rc == 0

    operational_request = json.loads(
        (
            tmp_path
            / "operational-dispatch"
            / "pythondontwritebytecode-operational-nonce"
            / "request.json"
        ).read_text(encoding="utf-8"),
    )
    assert operational_request["environment"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert "IZANAGI_UNLISTED" not in operational_request["environment"]

    sentinel_scheduler = _Scheduler()
    sentinel_clock = _Clock()
    sentinel_rc = DC.dispatch(
        ["orchestrator/tests/test_pegasus_dispatch_compute.py", "-q"],
        task="tests",
        repo_root=_REPO,
        output_root=tmp_path / "sentinel-dispatch",
        environ={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "sentinel-passthrough",
        },
        run_command=sentinel_scheduler,
        clock=sentinel_clock,
        sleep=sentinel_clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="pythondontwritebytecode-sentinel-nonce",
    )
    assert sentinel_rc == 0

    sentinel_request = json.loads(
        (
            tmp_path
            / "sentinel-dispatch"
            / "pythondontwritebytecode-sentinel-nonce"
            / "request.json"
        ).read_text(encoding="utf-8"),
    )
    assert (
        sentinel_request["environment"]["PYTHONDONTWRITEBYTECODE"]
        == "sentinel-passthrough"
    )


def test_provenance_task_binds_child_script_and_empty_env_allowlist(tmp_path):
    scheduler = _Scheduler()
    clock = _Clock()
    rc = DC.dispatch(
        ["--range", "72849d3..HEAD"],
        task="provenance",
        repo_root=_REPO,
        output_root=tmp_path / "dispatch",
        environ={
            "PATH": os.environ.get("PATH", ""),
            "PYTEST_ADDOPTS": "-q",
            "IZANAGI_TEST_NPROC": "48",
            "IZANAGI_TASK_RUN_ID": "must-not-propagate",
        },
        run_command=scheduler,
        clock=clock,
        sleep=clock.sleep,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="provenance-nonce",
    )
    assert rc == 0

    submission = tmp_path / "dispatch" / "provenance-nonce"
    request = json.loads((submission / "request.json").read_text(encoding="utf-8"))
    assert request["schema_version"] == "pegasus-dispatch-request/v2"
    assert request["task"] == "provenance"
    assert request["args"] == ["--range", "72849d3..HEAD"]
    # 空 allowlist: 親の pytest / task_run 環境は 1 つも request へ漏れない。
    assert request["environment"] == {}
    assert "pytest_args" not in request
    assert DC.TASKS["provenance"].env_allowlist == frozenset()
    assert DC.TASKS["provenance"].child_script == ("tools", "check_ai_provenance.py")

    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "pegasus-dispatch-receipt/v2"
    assert receipt["request"]["task"] == "provenance"
    assert receipt["request"]["args"] == ["--range", "72849d3..HEAD"]


def test_provenance_task_removes_recording_markers_at_every_hop(
    monkeypatch, tmp_path,
):
    sidecar = str(tmp_path / "stale-sidecar")
    monkeypatch.setenv("IZANAGI_TASK_RUN_SIDECAR", sidecar)
    monkeypatch.setenv("IZANAGI_TASK_RUN_AUTO_RECORD", "0")
    scheduler = _Scheduler()
    root = tmp_path / "dispatch"
    rc = DC.dispatch(
        ["--range", "A..B"],
        task="provenance",
        repo_root=_REPO,
        output_root=root,
        environ={
            "PATH": os.environ.get("PATH", ""),
            "IZANAGI_TASK_RUN_SIDECAR": sidecar,
            "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
        },
        run_command=scheduler,
        clock=_Clock(),
        sleep=lambda _seconds: None,
        poll_interval_s=5,
        queue_wait_timeout_s=20,
        accounting_grace_s=0,
        nonce="provenance-markers",
    )
    assert rc == 0
    submission = root / "provenance-markers"
    request = json.loads(
        (submission / "request.json").read_text(encoding="utf-8"),
    )
    assert "IZANAGI_TASK_RUN_SIDECAR" not in request["environment"]
    assert "IZANAGI_TASK_RUN_AUTO_RECORD" not in request["environment"]

    script = DC._job_script(
        repo_root=_REPO,
        submission_dir=submission,
        request_path=submission / "request.json",
        probe_path=submission / "interpreter_probe.py",
        walltime="00:30:00",
        task="provenance",
    )
    assert "unset IZANAGI_TASK_RUN_SIDECAR IZANAGI_TASK_RUN_AUTO_RECORD" in script

    request_path = tmp_path / "provenance-child-request.json"
    request_path.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v2",
            "repo_root": str(_REPO),
            "task": "provenance",
            "args": ["--range", "A..B"],
            "environment": {},
        }) + chr(10),
        encoding="utf-8",
    )
    child_rc, calls = _job_run_with_mocked_child(request_path)
    assert child_rc == 0
    child_env = calls[0][1]["env"]
    assert "IZANAGI_TASK_RUN_SIDECAR" not in child_env
    assert "IZANAGI_TASK_RUN_AUTO_RECORD" not in child_env


def test_provenance_probe_omits_pytest_and_xdist_imports():
    source = DC._interpreter_probe_source("provenance")
    assert "import pytest" not in source
    assert "import xdist" not in source
    assert "import packaging" not in source
    # 版数 gate は task に依らず残る (_job_run と二層冗長)。
    assert "if sys.version_info < (3, 10):" in source
    assert "raise SystemExit(1)" in source

    default_source = DC._interpreter_probe_source()
    assert default_source == DC._interpreter_probe_source("tests")
    assert "import pytest" in default_source
    assert "import xdist" in default_source


def test_job_run_accepts_v1_request_as_tests_task(tmp_path):
    """M12 期待赤: v1 受理を外すと queue 待ち中の in-flight job が rc=16 で死ぬ。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_job_run_accepts_v1_request_as_tests_task``。
    """

    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v1",
            "repo_root": str(_REPO),
            "pytest_args": ["orchestrator/tests", "-q"],
            "environment": {"PYTEST_ADDOPTS": "-q"},
        }) + "\n",
        encoding="utf-8",
    )

    rc, calls = _job_run_with_mocked_child(request, child_rc=7)
    assert rc == 7
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[1] == str(_REPO / "tools" / "run_tests.py")
    assert argv[2:] == ["orchestrator/tests", "-q"]
    assert kwargs["env"]["PYTEST_ADDOPTS"] == "-q"
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["stage"] == "child"
    assert result["child_rc"] == 7
    assert result["error"] is None


def test_job_run_passes_python_dont_write_bytecode_env_to_tests_child(tmp_path):
    request = tmp_path / "request.json"
    sentinel = "sentinel-child-env"
    request.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v2",
            "repo_root": str(_REPO),
            "task": "tests",
            "args": ["orchestrator/tests", "-q"],
            "environment": {"PYTHONDONTWRITEBYTECODE": sentinel},
        }) + "\n",
        encoding="utf-8",
    )

    rc, calls = _job_run_with_mocked_child(request)
    assert rc == 0
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == sentinel


@pytest.mark.parametrize(
    "payload",
    [
        {
            "schema_version": "pegasus-dispatch-request/v3",
            "task": "tests",
            "args": [],
        },
        {
            "schema_version": "pegasus-dispatch-request/v2",
            "task": "shell",
            "args": [],
        },
        {
            "schema_version": "pegasus-dispatch-request/v2",
            "task": 3,
            "args": [],
        },
    ],
    ids=["unknown-schema", "unknown-task", "non-string-task"],
)
def test_job_run_rejects_unknown_schema_and_task(tmp_path, payload):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"repo_root": str(_REPO), "environment": {}, **payload}) + "\n",
        encoding="utf-8",
    )

    rc, calls = _job_run_with_mocked_child(request)
    assert rc == DC.INFRA_RC
    assert calls == []
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["stage"] == "bootstrap"
    assert result["child_rc"] == DC.INFRA_RC
    assert result["error"] is not None


@pytest.mark.parametrize(
    ("task", "script"),
    [("tests", "run_tests.py"), ("provenance", "check_ai_provenance.py")],
)
def test_job_run_launches_task_specific_child_script(tmp_path, task, script):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({
            "schema_version": "pegasus-dispatch-request/v2",
            "repo_root": str(_REPO),
            "task": task,
            "args": ["--range", "A..B"],
            "environment": {},
        }) + "\n",
        encoding="utf-8",
    )

    rc, calls = _job_run_with_mocked_child(request)
    assert rc == 0
    argv, _ = calls[0]
    assert argv[1] == str(_REPO / "tools" / script)
    assert argv[2:] == ["--range", "A..B"]


def test_tests_task_remains_default_and_receipt_records_task(tmp_path):
    scheduler = _Scheduler()
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == 0

    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "pegasus-dispatch-receipt/v2"
    assert receipt["request"]["task"] == "tests"
    assert receipt["request"]["args"] == [
        "orchestrator/tests/test_sample.py", "-q",
    ]
    assert "pytest_args" not in receipt["request"]

    request = json.loads((submission / "request.json").read_text(encoding="utf-8"))
    assert request["task"] == "tests"
    assert request["args"] == ["orchestrator/tests/test_sample.py", "-q"]
    assert request["environment"] == {"PYTEST_ADDOPTS": "-q"}


def test_run_tests_default_dispatch_passes_tests_task(monkeypatch):
    """B-R11: 唯一の production caller が task を明示することを固定する。"""

    from tools import run_tests

    seen: dict = {}

    def fake_dispatch(args, **kwargs):
        seen["args"] = list(args)
        seen["kwargs"] = kwargs
        return 5

    monkeypatch.setattr(DC, "dispatch", fake_dispatch)
    rc = run_tests._default_dispatch(["-q"], environ={"PATH": "/usr/bin"})
    assert rc == 5
    assert seen["args"] == ["-q"]
    assert seen["kwargs"]["task"] == "tests"
    assert seen["kwargs"]["task"] in DC.TASKS
    assert Path(seen["kwargs"]["repo_root"]).resolve() == _REPO.resolve()
    assert seen["kwargs"]["environ"] == {"PATH": "/usr/bin"}
    assert "walltime" not in seen["kwargs"]


def test_run_tests_default_dispatch_passes_walltime_override(monkeypatch):
    from tools import run_tests

    seen: dict = {}

    def fake_dispatch(args, **kwargs):
        seen["args"] = list(args)
        seen["kwargs"] = kwargs
        return 5

    monkeypatch.setattr(DC, "dispatch", fake_dispatch)
    rc = run_tests._default_dispatch(
        ["-q"],
        environ={
            "PATH": "/usr/bin",
            "IZANAGI_DISPATCH_WALLTIME_OVERRIDE": "00:02:00",
        },
    )
    assert rc == 5
    assert seen["kwargs"]["walltime"] == "00:02:00"


def test_dev_wave_check_maps_dispatch_infra_rc_off_provenance_reason(tmp_path):
    """B-R7: rc=16 は dispatch の infra 失敗であって provenance 違反ではない。

    dev-wave の check 分類は spec 名だけを見ていたため、queue 満杯・qstat 権限
    エラー・receipt 永続失敗のいずれもが receipt に「provenance 違反」として載って
    いた。所有分割上 tools/dev_waves/ の test は本 wave では持たないので、rc 契約の
    消費側検査を dispatcher 側の境界テストとしてここに置く。

    検査するのは「provenance 理由から外れること」だけである — `ReasonCode` に
    infra 相当の値は無く、`CHECK_FAILED` は全 fallback と同値なので、台帳上は
    他の check 失敗と区別できない (段 6 レビュー B の MF-2)。

    fake は `python3 -c` ではなく checkout 直下の実 `tools/check_*.py` として置く:
    `CheckSpec.__post_init__` の trust root 検査は恒真ではなく、段 6 の受入全走
    (計算ノード request 874774.nqsv) で `-c` 形が実際に
    `ValueError: fixed check script is outside the trust root` で弾かれた。
    """

    from tools.dev_waves.checker import CheckSpec, run_check_specs
    from tools.dev_waves.schema import ReasonCode

    assert DC.INFRA_RC == 16
    assert not [name for name in ReasonCode.__members__ if "INFRA" in name], (
        "infra 専用の理由コードが増えたら rc=16 の写像先を見直すこと")
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "check_fake_infra.py").write_text(
        f"raise SystemExit({DC.INFRA_RC})\n", encoding="utf-8")
    (tools / "check_fake_violation.py").write_text(
        "raise SystemExit(1)\n", encoding="utf-8")
    deadline = time.clock_gettime_ns(time.CLOCK_BOOTTIME) + 60_000_000_000

    infra = run_check_specs(
        (CheckSpec(
            "provenance", (sys.executable, "tools/check_fake_infra.py"), 30,
        ),),
        tmp_path,
        total_deadline_boottime_ns=deadline,
    )
    assert infra[0].status == "fail"
    assert infra[0].reason is not ReasonCode.PROVENANCE_FAILED
    assert infra[0].reason is ReasonCode.CHECK_FAILED

    violation = run_check_specs(
        (CheckSpec(
            "provenance", (sys.executable, "tools/check_fake_violation.py"), 30,
        ),),
        tmp_path,
        total_deadline_boottime_ns=deadline,
    )
    assert violation[0].status == "fail"
    assert violation[0].reason is ReasonCode.PROVENANCE_FAILED


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
