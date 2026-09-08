# -*- coding: utf-8 -*-
"""Compute-job completion waiting and accounting binding contracts."""
from __future__ import annotations

import builtins
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable

import pytest

from orchestrator.scheduler_nqsv import accounting_ended_result


_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "dev_wave_wait.py"
_SPEC = importlib.util.spec_from_file_location(
    "dev_wave_wait_compute_under_test",
    _TOOL,
)
assert _SPEC and _SPEC.loader
DW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = DW
_SPEC.loader.exec_module(DW)

_REQUEST_ID = "12345.pegasus"
_ACCOUNTING_TEXT = """\
Request ID: 12345.pegasus
Request Name: izanagi-floor
Started Request Time: Fri Sep  5 09:00:00 2026
Ended Request Time: Fri Sep  5 09:41:12 2026
Elapse: 00:41:12
"""


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


def _forbidden_run(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("effects.run and effects.run_unbounded must not be called")


def _effects(
    clock: _Clock,
    *,
    is_file: Callable[[Path], bool] = Path.is_file,
    read_text: Callable[[Path], str] | None = None,
    getenv: Callable[[str], str | None] = lambda _name: None,
    monotonic: Callable[[], float] | None = None,
    write_receipt_temp: Callable[[Path, bytes], Path] | None = None,
    rename: Callable[[Path, Path], None] | None = None,
) -> object:
    if read_text is None:
        read_text = lambda path: path.read_text(encoding="utf-8")
    return DW._Effects(
        run=_forbidden_run,
        run_unbounded=_forbidden_run,
        sleep=clock.sleep,
        kill=lambda _pid, _signum: None,
        is_file=is_file,
        read_text=read_text,
        getenv=getenv,
        monotonic=clock.monotonic if monotonic is None else monotonic,
        write_temp=lambda _content: Path("unused"),
        unlink=lambda path: path.unlink(missing_ok=True),
        write_receipt_temp=(
            DW._default_write_receipt_temp
            if write_receipt_temp is None
            else write_receipt_temp
        ),
        rename=os.rename if rename is None else rename,
    )


def _wait(
    tmp_path: Path,
    *,
    done_text: str | None = None,
    accounting_text: str | None = None,
) -> tuple[object, _Clock]:
    done_file = tmp_path / "done"
    accounting_file = tmp_path / "accounting"
    if done_text is not None:
        done_file.write_text(done_text, encoding="utf-8")
    if accounting_text is not None:
        accounting_file.write_text(accounting_text, encoding="utf-8")
    clock = _Clock()
    outcome = DW.wait_for_compute_job(
        request_id=_REQUEST_ID,
        done_file=done_file,
        accounting_file=accounting_file,
        max_wait_seconds=15,
        effects=_effects(clock),
    )
    return outcome, clock


def test_accounting_ended_result_accepts_target_bound_ended_record() -> None:
    result = accounting_ended_result(_ACCOUNTING_TEXT, _REQUEST_ID)

    assert result.ended is True
    assert result.reason == "ok"


@pytest.mark.parametrize(
    ("text", "ended", "reason"),
    (
        (
            "Request ID: 12345.pegasus\n"
            "Started Request Time: now\n"
            "Request ID: 99999.pegasus\r\n"
            "Ended Request Time: old-job-time\r\n",
            False,
            "request-id-count",
        ),
        (
            "Request ID: 12345.pegasus\r\n"
            "Ended Request Time: t\r\n",
            True,
            "ok",
        ),
        (
            "Ended Request Time: old\n"
            "Request ID: 12345.pegasus\n",
            False,
            "ended-before-target-request-id",
        ),
    ),
    ids=("other-job-ended", "all-crlf", "ended-before-target"),
)
def test_accounting_ended_result_binds_ended_to_target_record(
    text: str,
    ended: bool,
    reason: str,
) -> None:
    result = accounting_ended_result(text, _REQUEST_ID)

    assert result.ended is ended
    assert result.reason == reason


@pytest.mark.parametrize(
    ("text", "reason"),
    (
        (
            "Ended Request Time: Fri Sep  5 09:41:12 2026\n",
            "request-id-count",
        ),
        (
            _ACCOUNTING_TEXT + "Request ID: 12345.pegasus\n",
            "request-id-count",
        ),
        (
            _ACCOUNTING_TEXT.replace(
                "Request ID: 12345.pegasus",
                "Request ID: 99999.pegasus",
            ),
            "request-id-mismatch",
        ),
        (
            _ACCOUNTING_TEXT.replace(
                "Ended Request Time: Fri Sep  5 09:41:12 2026\n",
                "",
            ),
            "ended-field-missing",
        ),
    ),
    ids=("no-id", "duplicate-id", "mismatch", "no-ended-field"),
)
def test_accounting_ended_result_rejects_unbound_or_unended_records(
    text: str,
    reason: str,
) -> None:
    result = accounting_ended_result(text, _REQUEST_ID)

    assert result.ended is False
    assert result.reason == reason


@pytest.mark.parametrize(
    ("observed", "target"),
    (
        ("0:12345.pegasus", "12345.pegasus"),
        ("12345.pegasus", "0:12345.pegasus"),
    ),
    ids=("observed-prefix", "target-prefix"),
)
def test_accounting_ended_result_normalizes_zero_prefix(
    observed: str,
    target: str,
) -> None:
    text = _ACCOUNTING_TEXT.replace("12345.pegasus", observed, 1)

    result = accounting_ended_result(text, target)

    assert result.ended is True
    assert result.reason == "ok"


def test_accounting_ended_result_rejects_invalid_target_request_id() -> None:
    result = accounting_ended_result(_ACCOUNTING_TEXT, ".")

    assert result.ended is False
    assert result.reason == "invalid-target-request-id"


def test_accounting_ended_result_rejects_invalid_observed_request_id() -> None:
    text = _ACCOUNTING_TEXT.replace("12345.pegasus", ".", 1)

    result = accounting_ended_result(text, _REQUEST_ID)

    assert result.ended is False
    assert result.reason == "invalid-observed-request-id"


def test_wait_for_compute_job_accepts_done_evidence_alone(
    tmp_path: Path,
) -> None:
    outcome, clock = _wait(tmp_path, done_text="complete\n")

    assert outcome == DW._Outcome(DW.RC_OK)
    assert clock.sleeps == []


@pytest.mark.parametrize(
    ("done_text", "expected_rc"),
    (("complete\n", DW.RC_OK), (None, DW.RC_FAIL_CLOSED)),
    ids=("done-short-circuits", "accounting-failure-propagates"),
)
def test_done_evidence_controls_broken_accounting_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    done_text: str | None,
    expected_rc: int,
) -> None:
    done_file = tmp_path / "done"
    if done_text is not None:
        done_file.write_text(done_text, encoding="utf-8")
    accounting_file = tmp_path / "accounting"
    accounting_file.write_text(_ACCOUNTING_TEXT, encoding="utf-8")
    real_import = builtins.__import__

    def fail_accounting_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name == "orchestrator.scheduler_nqsv" and (
            "accounting_ended" in fromlist
        ):
            raise ModuleNotFoundError("accounting dependency unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_accounting_import)
    clock = _Clock()
    rc = DW.main(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            str(done_file),
            "--accounting-file",
            str(accounting_file),
            "--max-wait-seconds",
            "15",
        ],
        effects=_effects(clock),
    )

    assert rc == expected_rc
    assert clock.sleeps == []


def test_wait_for_compute_job_accepts_accounting_evidence_alone(
    tmp_path: Path,
) -> None:
    outcome, clock = _wait(tmp_path, accounting_text=_ACCOUNTING_TEXT)

    assert outcome == DW._Outcome(DW.RC_OK)
    assert clock.sleeps == []


def test_wait_for_compute_job_accepts_both_evidence_sources(
    tmp_path: Path,
) -> None:
    outcome, clock = _wait(
        tmp_path,
        done_text="complete\n",
        accounting_text=_ACCOUNTING_TEXT,
    )

    assert outcome == DW._Outcome(DW.RC_OK)
    assert clock.sleeps == []


@pytest.mark.parametrize("done_text", ("", " \t\n"), ids=("empty", "whitespace"))
def test_wait_for_compute_job_rejects_empty_done_file(
    tmp_path: Path,
    done_text: str,
) -> None:
    outcome, clock = _wait(tmp_path, done_text=done_text)

    assert outcome.rc != 0
    assert outcome.stage == "compute-timeout"
    assert clock.sleeps == [15]


def test_wait_for_compute_job_rejects_done_directory(tmp_path: Path) -> None:
    (tmp_path / "done").mkdir()

    outcome, clock = _wait(tmp_path)

    assert outcome.rc != 0
    assert outcome.stage == "compute-timeout"
    assert clock.sleeps == [15]


def test_wait_for_compute_job_rejects_mismatched_accounting(
    tmp_path: Path,
) -> None:
    mismatch = _ACCOUNTING_TEXT.replace(
        "Request ID: 12345.pegasus",
        "Request ID: 99999.pegasus",
    )

    outcome, clock = _wait(tmp_path, accounting_text=mismatch)

    assert outcome.rc != 0
    assert outcome.stage == "compute-timeout"
    assert clock.sleeps == [15]


def test_wait_for_compute_job_timeout_is_fail_closed(tmp_path: Path) -> None:
    outcome, clock = _wait(tmp_path)

    assert outcome.rc == DW.RC_FAIL_CLOSED
    assert outcome.stage == "compute-timeout"
    assert clock.sleeps == [15]


def test_wait_for_compute_job_clock_failure_is_fail_closed(tmp_path: Path) -> None:
    clock = _Clock()

    def fail_clock() -> float:
        raise OSError("clock unavailable")

    outcome = DW.wait_for_compute_job(
        request_id=_REQUEST_ID,
        done_file=tmp_path / "done",
        accounting_file=tmp_path / "accounting",
        max_wait_seconds=15,
        effects=_effects(clock, monotonic=fail_clock),
    )

    assert outcome == DW._Outcome(DW.RC_FAIL_CLOSED, "compute-clock")


def test_wait_for_compute_job_treats_done_read_oserror_as_no_evidence(
    tmp_path: Path,
) -> None:
    done_file = tmp_path / "done"
    done_file.write_text("complete\n", encoding="utf-8")
    accounting_file = tmp_path / "accounting"
    clock = _Clock()

    def read_text(path: Path) -> str:
        if path == done_file:
            raise OSError("not visible")
        return path.read_text(encoding="utf-8")

    outcome = DW.wait_for_compute_job(
        request_id=_REQUEST_ID,
        done_file=done_file,
        accounting_file=accounting_file,
        max_wait_seconds=15,
        effects=_effects(clock, read_text=read_text),
    )

    assert outcome == DW._Outcome(DW.RC_FAIL_CLOSED, "compute-timeout")


def test_done_success_does_not_call_effects_run_or_run_unbounded(
    tmp_path: Path,
) -> None:
    done_file = tmp_path / "done"
    done_file.write_text("complete\n", encoding="utf-8")
    clock = _Clock()
    effects = _effects(clock)
    assert effects.run is _forbidden_run
    assert effects.run_unbounded is _forbidden_run

    outcome = DW.wait_for_compute_job(
        request_id=_REQUEST_ID,
        done_file=done_file,
        accounting_file=tmp_path / "accounting",
        max_wait_seconds=15,
        effects=effects,
    )

    assert outcome == DW._Outcome(DW.RC_OK)


@pytest.mark.parametrize("source", ("done", "accounting"))
def test_compute_receipt_records_actual_evidence(
    tmp_path: Path,
    source: str,
) -> None:
    done_file = tmp_path / "done"
    accounting_file = tmp_path / "accounting"
    receipt_file = tmp_path / "compute-receipt.json"
    if source == "done":
        done_file.write_text("complete\n", encoding="utf-8")
    else:
        accounting_file.write_text(_ACCOUNTING_TEXT, encoding="utf-8")
    clock = _Clock()

    rc = DW.main(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            str(done_file),
            "--accounting-file",
            str(accounting_file),
            "--max-wait-seconds",
            "15",
            "--receipt-file",
            str(receipt_file),
        ],
        effects=_effects(clock),
    )

    assert rc == DW.RC_OK
    payload = json.loads(receipt_file.read_text(encoding="utf-8"))
    done_mtime_ns = payload.pop("done_mtime_ns")
    accounting_mtime_ns = payload.pop("accounting_mtime_ns")
    assert payload == {
        "schema_version": "dev-wave-compute-receipt/v1",
        "status": "success",
        "request_id": _REQUEST_ID,
        "done_file": str(done_file),
        "accounting_file": str(accounting_file),
        "done_evidence": source == "done",
        "accounting_evidence": source == "accounting",
    }
    assert done_mtime_ns == (
        done_file.stat().st_mtime_ns if source == "done" else None
    )
    assert accounting_mtime_ns == (
        accounting_file.stat().st_mtime_ns
        if source == "accounting"
        else None
    )


def test_compute_receipt_publish_failure_is_fail_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    done_file = tmp_path / "done"
    done_file.write_text("complete\n", encoding="utf-8")
    clock = _Clock()

    def fail_write(_final_path: Path, _content: bytes) -> Path:
        raise OSError("cannot publish")

    rc = DW.main(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            str(done_file),
            "--accounting-file",
            str(tmp_path / "accounting"),
            "--receipt-file",
            str(tmp_path / "receipt.json"),
        ],
        effects=_effects(clock, write_receipt_temp=fail_write),
    )

    assert rc == DW.RC_FAIL_CLOSED
    assert "stage=compute-receipt rc=70" in capsys.readouterr().err


def test_compute_receipt_mtime_failure_uses_compute_stage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    done_file = tmp_path / "done"
    done_file.write_text("complete\n", encoding="utf-8")
    receipt_file = tmp_path / "receipt.json"
    clock = _Clock()

    def read_then_remove(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        path.unlink()
        return text

    rc = DW.main(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            str(done_file),
            "--accounting-file",
            str(tmp_path / "accounting"),
            "--receipt-file",
            str(receipt_file),
        ],
        effects=_effects(clock, read_text=read_then_remove),
    )

    assert rc == DW.RC_FAIL_CLOSED
    assert "stage=compute-receipt rc=70" in capsys.readouterr().err
    assert not receipt_file.exists()


@pytest.mark.parametrize(
    "missing",
    ("request-id", "done-file", "accounting-file"),
)
def test_compute_cli_requires_each_mandatory_argument(missing: str) -> None:
    values = {
        "request-id": _REQUEST_ID,
        "done-file": "done",
        "accounting-file": "accounting",
    }
    argv = ["compute"]
    for name, value in values.items():
        if name != missing:
            argv.extend((f"--{name}", value))

    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli(argv)

    assert raised.value.outcome == DW._Outcome(DW.RC_USAGE, "cli-usage")


def test_compute_cli_rejects_child_command() -> None:
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli(
            [
                "compute",
                "--request-id",
                _REQUEST_ID,
                "--done-file",
                "done",
                "--accounting-file",
                "accounting",
                "--",
                "child",
            ]
        )

    assert raised.value.outcome == DW._Outcome(DW.RC_USAGE, "cli-usage")


def test_compute_cli_rejects_unnormalizable_request_id() -> None:
    rc = DW.main(
        [
            "compute",
            "--request-id",
            ".",
            "--done-file",
            "done",
            "--accounting-file",
            "accounting",
        ]
    )

    assert rc == DW.RC_USAGE


def test_compute_cli_accepts_normal_request_id() -> None:
    command, args, child = DW._parse_cli(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            "done",
            "--accounting-file",
            "accounting",
        ]
    )

    assert command == "compute"
    assert args.request_id == _REQUEST_ID
    assert child == []


def test_compute_cli_uses_six_hour_default() -> None:
    command, args, child = DW._parse_cli(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            "done",
            "--accounting-file",
            "accounting",
        ]
    )

    assert command == "compute"
    assert args.max_wait_seconds == 21600
    assert child == []


def test_compute_main_does_not_enter_acceptance_lease_path(
    tmp_path: Path,
) -> None:
    done_file = tmp_path / "done"
    done_file.write_text("complete\n", encoding="utf-8")
    clock = _Clock()

    def forbid_lease(_name: str) -> str | None:
        raise AssertionError("acceptance lease path was touched")

    rc = DW.main(
        [
            "compute",
            "--request-id",
            _REQUEST_ID,
            "--done-file",
            str(done_file),
            "--accounting-file",
            str(tmp_path / "accounting"),
        ],
        effects=_effects(clock, getenv=forbid_lease),
    )

    assert rc == DW.RC_OK


def _run() -> int:
    """Keep this test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
