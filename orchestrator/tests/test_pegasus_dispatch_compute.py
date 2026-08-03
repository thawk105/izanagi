# -*- coding: utf-8 -*-
"""Pegasus compute dispatcher の fake scheduler 境界テスト。

実 qsub は呼ばず、command runner・clock・sleep を全て注入する。
"""
from __future__ import annotations

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
        states=("QUE", "RUN", "DONE"),
        child_rc=0,
        accounting=True,
        visible=True,
        marker=True,
        initial_qstat_failures=0,
        initial_qstat_error="temporary qstat failure",
        qstat_error_stdout="",
        qsub_stdout=None,
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
            return self._completed(command)
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
        "elapstim_req=00:30:00",
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


def test_accounting_grace_failure_relays_collected_stdout(tmp_path, capsys):
    scheduler = _Scheduler(
        accounting=False,
        stdout=b"accounting-infra-stdout\n",
    )
    rc, _ = _dispatch(tmp_path, scheduler)
    captured = capsys.readouterr()

    assert rc == DC.INFRA_RC
    assert "| accounting-infra-stdout\n" in captured.out


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


def test_m7_dispatcher_request_allowlist_isolated_redundant_gate(tmp_path):
    """M7 dispatcher allowlist 単独変異の期待赤 node。

    期待赤:
    ``orchestrator/tests/test_pegasus_dispatch_compute.py::test_m7_dispatcher_request_allowlist_isolated_redundant_gate``。
    dispatcher の env allowlist だけを無効化すると本 node は赤くなる。ただし親 pop と
    job script が同じ task_run 状態を除去するため、これは冗長 gate の構造 pin であり、
    DW-M03 に従って単独変異の受理挙動証拠から外す。
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
    生成 job script の ``unset`` だけを無効化すると本 node は赤くなる。ただし親 pop、
    dispatcher allowlist、``_job_run()`` の child-env pop が残るため冗長 gate であり、
    DW-M03 に従って単独変異の受理挙動証拠から外す。
    """

    script = DC._job_script(
        repo_root=_REPO,
        submission_dir=tmp_path,
        request_path=tmp_path / "request.json",
        probe_path=tmp_path / "interpreter_probe.py",
        walltime="00:30:00",
    )
    assert (
        "unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT "
        "IZANAGI_TASK_RUN_SIDECAR\n"
    ) in script


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
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)


def test_m6_qstat_success_without_request_qdels_and_create_only_latches(
    tmp_path, capsys,
):
    # M6/FA-9: qstat 成功なのに request 不在なら F47 型としてラッチする。
    scheduler = _Scheduler(visible=False)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    latch = tmp_path / "dispatch" / "submission-disabled.json"
    assert latch.is_file()
    original = latch.read_bytes()
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"]["kind"] == "f47"
    assert receipt["immediate_qstat_attempts"][0]["classification"] == (
        "success-request-absent"
    )
    assert receipt["f49_immediate"]["qstat_visible"] is False
    assert receipt["f49_immediate"]["qstat_succeeded"] is True
    assert "ユーザー自身の端末" in capsys.readouterr().err

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


def test_f47_literal_not_permitted_response_qdels_and_latches(tmp_path):
    scheduler = _Scheduler(
        initial_qstat_failures=3,
        initial_qstat_error="Not permitted to access",
    )
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert scheduler.qstat_calls == 1
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
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


def test_immediate_qstat_failures_exhaust_to_infra_without_latching(tmp_path):
    scheduler = _Scheduler(initial_qstat_failures=3)
    rc, submission = _dispatch(tmp_path, scheduler)
    assert rc == DC.INFRA_RC
    assert not (tmp_path / "dispatch" / "submission-disabled.json").exists()
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["outcome"]["kind"] == "infra"
    assert "immediate-qstat-unavailable-after-retries" in receipt["outcome"]["reason"]


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
    scheduler = _Scheduler(marker=False)
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
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)


@pytest.mark.parametrize(
    "tail",
    [
        "worker recovered from MemoryError\n",
        (
            "Request ID: 999999.nqsv\n"
            "Started Request Time: now\n"
            "Ended Request Time: later\n"
            "Elapse: 1S\n"
        ),
        (
            "Request ID: 424242.nqsv\n"
            "Started Request Time: now\n"
            "Elapse: 1S\n"
        ),
    ],
)
def test_accounting_requires_matching_request_id_and_all_nqsv_fields(tail):
    assert not DC._accounting_present({"tail": tail}, _JOB_ID)


def test_accounting_accepts_measured_nqsv_shape_only_when_id_matches():
    tail = (
        "Request ID:             424242.nqsv\n"
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


def test_hld_queue_timeout_qdels_and_receipts(tmp_path, capsys):
    scheduler = _Scheduler(states=("HLD", "HLD", "HLD"))
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


def test_scheduler_exception_after_qsub_qdels_and_receipts(tmp_path):
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
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads(
        (tmp_path / "dispatch" / "exception" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert "injected qstat failure" in receipt["outcome"]["reason"]


def test_overall_walltime_plus_grace_bound_qdels_running_job(tmp_path):
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
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads(
        (tmp_path / "dispatch" / "overall" / "receipt.json").read_text(
            encoding="utf-8",
        ),
    )
    assert "overall-timeout" in receipt["outcome"]["reason"]


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
    assert any(command[0] == "qdel" for command, _ in scheduler.commands)
    receipt = json.loads((submission / "receipt.json").read_text(encoding="utf-8"))
    assert "overall-timeout" in receipt["outcome"]["reason"]
    assert receipt["state_history"][-1]["elapsed_s"] == 4.0
    assert any(item["state"] == "RUN" for item in receipt["state_history"])


def test_nonzero_qstat_run_stdout_does_not_restart_deadline(tmp_path):
    trusted = _Scheduler(states=(
        "QUE", "RUN", "UNRECOGNIZED", "UNRECOGNIZED", "UNRECOGNIZED",
    ))
    trusted_rc, trusted_submission = _dispatch(
        tmp_path,
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
        states=("QUE", "ERROR", "UNRECOGNIZED", "UNRECOGNIZED"),
        qstat_error_stdout="Request State = RUN\n",
    )
    untrusted_rc, untrusted_submission = _dispatch(
        tmp_path,
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
    assert untrusted_rc == DC.INFRA_RC
    assert any(command[0] == "qdel" for command, _ in untrusted.commands)
    assert "overall-timeout" in untrusted_receipt["outcome"]["reason"]
    assert untrusted_receipt["state_history"][-1]["elapsed_s"] == 3.0
    assert untrusted_receipt["state_history"][-1]["state"] == "UNKNOWN"
    assert untrusted_receipt["queue_wait_s"] == 1.0
    assert untrusted_receipt["queue_wait_observed"] is True


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


def test_progress_output_is_explicitly_flushed():
    with mock.patch("builtins.print") as printed:
        DC._progress("状態: RUN")
    printed.assert_called_once_with("[Pegasus dispatch] 状態: RUN", flush=True)


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
