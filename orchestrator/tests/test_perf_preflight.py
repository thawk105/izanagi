from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.calibrator import perf_preflight


EVENT_LINES = (
    "<not counted>,,LLC-load-misses,0,100.00,,\n"
    "2,,LLC-loads,0,100.00,,\n"
    "3,,instructions,0,100.00,,\n"
    "4,,cycles,0,100.00,,\n"
)


def _runner_with_output(text, *, rc=0, stderr=""):
    calls = []

    def run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        Path(argv[argv.index("-o") + 1]).write_text(text, encoding="utf-8")
        return SimpleNamespace(returncode=rc, stdout="", stderr=stderr)

    run.calls = calls
    return run


def test_probe_accepts_only_zero_rc_with_all_requested_events():
    runner = _runner_with_output(EVENT_LINES)
    receipt = perf_preflight.probe_perf_availability(subprocess_runner=runner)

    assert receipt["status"] == "available"
    assert receipt["available"] is True
    assert receipt["parsed_events"] == [
        "LLC-load-misses", "LLC-loads", "instructions", "cycles",
    ]
    argv, kwargs = runner.calls[0]
    assert argv[:4] == ["perf", "stat", "-x,", "-o"]
    assert argv[-2:] == ["--", "/bin/true"]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert "<tmp>" not in argv[argv.index("-o") + 1]


@pytest.mark.parametrize(
    "factory,reason,status",
    [
        (lambda: _runner_with_output(EVENT_LINES, rc=2, stderr="denied"),
         "nonzero-rc", "unavailable"),
        (lambda: _runner_with_output("1,,cycles,0,100.00,,\n"),
         "requested-events-missing", "unavailable"),
    ],
)
def test_probe_classifies_nonzero_and_missing_events(factory, reason, status):
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=factory(),
    )
    assert receipt["status"] == status
    assert receipt["available"] is False
    assert receipt["reason"] == reason


@pytest.mark.parametrize(
    "exc,reason,status",
    [
        (FileNotFoundError("perf"), "perf-not-found", "unavailable"),
        (subprocess.TimeoutExpired(["perf"], 1), "probe-timeout", "probe_error"),
        (OSError("unexpected"), "probe-os-error", "probe_error"),
    ],
)
def test_probe_classifies_not_found_and_probe_errors(exc, reason, status):
    def raising(*_args, **_kwargs):
        raise exc

    receipt = perf_preflight.probe_perf_availability(subprocess_runner=raising)
    assert receipt["status"] == status
    assert receipt["reason"] == reason
    if status == "probe_error":
        with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
            perf_preflight.use_perf_from_receipt(receipt)


def test_probe_classifies_signal_as_probe_error():
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES, rc=-9),
    )
    assert receipt["status"] == "probe_error"
    assert receipt["reason"] == "probe-signal"
    assert receipt["rc"] == -9


def test_probe_classifies_non_utf8_output_as_probe_os_error():
    def run(argv, **_kwargs):
        Path(argv[argv.index("-o") + 1]).write_bytes(b"\xff")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    receipt = perf_preflight.probe_perf_availability(subprocess_runner=run)

    assert receipt["status"] == "probe_error"
    assert receipt["available"] is False
    assert receipt["reason"] == "probe-os-error"
    with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
        perf_preflight.use_perf_from_receipt(receipt)


def test_probe_records_policy_candidates_without_selecting_them():
    runner = _runner_with_output(EVENT_LINES, rc=2)
    receipt = perf_preflight.probe_perf_availability(
        perf_candidates=("/policy/perf-a", "/policy/perf-b"),
        subprocess_runner=runner,
    )
    assert runner.calls[0][0][0] == "perf"
    assert [call[0][0] for call in runner.calls[1:]] == [
        "/policy/perf-a", "/policy/perf-b",
    ]
    assert receipt["status"] == "unavailable"
    assert receipt["candidates"] == [
        {"path": "/policy/perf-a", "rc": 2, "executable": True},
        {"path": "/policy/perf-b", "rc": 2, "executable": True},
    ]


@pytest.mark.parametrize("field,value", [
    ("available", False),
    ("rc", 7),
    ("reason", "nonzero-rc"),
    ("parsed_events", []),
    ("status", "unavailable"),
])
def test_receipt_validator_rejects_inconsistent_claims(field, value):
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES),
    )
    receipt[field] = value
    with pytest.raises(perf_preflight.PerfPreflightError, match="不整合"):
        perf_preflight.validate_perf_preflight_receipt(receipt)


def test_receipt_validator_rejects_non_string_parsed_event_before_set_operations():
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES),
    )
    receipt["parsed_events"] = [{}]

    with pytest.raises(perf_preflight.PerfPreflightError, match="canonical subset"):
        perf_preflight.validate_perf_preflight_receipt(receipt)


def test_legacy_none_is_the_only_receiptless_perf_default():
    assert perf_preflight.use_perf_from_receipt(None) is True
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES, rc=2),
    )
    assert perf_preflight.use_perf_from_receipt(receipt) is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
