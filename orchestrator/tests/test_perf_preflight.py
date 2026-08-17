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

NO_PERF_RUN_CMD = ["/opt/ccbench/ycsb", "-thread_num=48"]
PERF_RUN_CMD = [
    "perf", "stat", "-e", "LLC-load-misses,LLC-loads,instructions,cycles",
    "--", "/opt/ccbench/ycsb", "-thread_num=48",
]


def _leading(*, ipc=None, llc_miss_rate=None, perf_raw=None):
    leading = {
        "throughput_tps": 100.0,
        "abort_rate": 0.1,
        "latency_ns": 10.0,
        "llc_miss_rate": llc_miss_rate,
        "ipc": ipc,
    }
    if perf_raw is not None:
        leading["perf_raw"] = perf_raw
    return leading


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
    assert perf_preflight.build_perf_observation(
        None, run_cmd=PERF_RUN_CMD,
        leading_indicators=_leading(ipc=1.5, llc_miss_rate=0.2),
    ) is None
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES, rc=2),
    )
    assert perf_preflight.use_perf_from_receipt(receipt) is False


def test_available_receipt_builds_exact_legacy_observation_shape():
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES),
    )

    observation = perf_preflight.build_perf_observation(
        receipt, run_cmd=PERF_RUN_CMD,
        leading_indicators=_leading(ipc=1.5, llc_miss_rate=0.2),
    )

    assert set(observation) == {
        "use_perf", "counter_status", "missing_leading_indicators", "preflight",
    }
    assert observation == {
        "use_perf": True,
        "counter_status": "complete",
        "missing_leading_indicators": [],
        "preflight": receipt,
    }
    assert perf_preflight.validate_perf_observation(
        observation, run_cmd=PERF_RUN_CMD,
        leading_indicators=_leading(ipc=1.5, llc_miss_rate=0.2),
    ) == observation


def _unavailable_receipt():
    return perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES, rc=2),
    )


def _degraded_observation():
    return {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": _unavailable_receipt(),
        "claim_scope": {
            "throughput": "eligible",
            "perf_required": "unsupported",
        },
    }


def test_degraded_builder_and_validator_require_exact_claim_scope():
    leading = _leading()
    observation = perf_preflight.build_perf_observation(
        _unavailable_receipt(), run_cmd=NO_PERF_RUN_CMD,
        leading_indicators=leading,
    )

    assert observation == _degraded_observation()
    assert perf_preflight.validate_perf_observation(
        observation, run_cmd=NO_PERF_RUN_CMD, leading_indicators=leading,
    ) == observation

    for mutation in (
        lambda value: value.pop("claim_scope"),
        lambda value: value["claim_scope"].update({"throughput": "unsupported"}),
        lambda value: value["claim_scope"].update({"extra": "eligible"}),
    ):
        changed = _degraded_observation()
        mutation(changed)
        with pytest.raises(perf_preflight.PerfPreflightError):
            perf_preflight.validate_perf_observation(
                changed, run_cmd=NO_PERF_RUN_CMD, leading_indicators=leading,
            )


def test_degraded_validator_rejects_perf_prefix_as_the_only_contradiction():
    with pytest.raises(perf_preflight.PerfPreflightError, match="perf stat prefix"):
        perf_preflight.validate_perf_observation(
            _degraded_observation(), run_cmd=PERF_RUN_CMD,
            leading_indicators=_leading(),
        )


def test_degraded_validator_rejects_non_null_ipc_as_the_only_contradiction():
    with pytest.raises(perf_preflight.PerfPreflightError, match=r"ipc.*non-null"):
        perf_preflight.validate_perf_observation(
            _degraded_observation(), run_cmd=NO_PERF_RUN_CMD,
            leading_indicators=_leading(ipc=1.5),
        )


def test_degraded_validator_requires_both_named_perf_indicators():
    for mutation in (
        lambda leading: leading.pop("ipc"),
        lambda leading: leading.pop("llc_miss_rate"),
        lambda leading: leading.update({"llc_miss_rate": 0.2}),
    ):
        leading = _leading()
        mutation(leading)
        with pytest.raises(perf_preflight.PerfPreflightError):
            perf_preflight.validate_perf_observation(
                _degraded_observation(), run_cmd=NO_PERF_RUN_CMD,
                leading_indicators=leading,
            )


def test_degraded_validator_rejects_every_non_null_raw_perf_counter():
    raw = {event: None for event in perf_preflight.PERF_EVENTS}
    raw["cycles"] = 1

    with pytest.raises(perf_preflight.PerfPreflightError, match="non-null perf raw"):
        perf_preflight.validate_perf_observation(
            _degraded_observation(), run_cmd=NO_PERF_RUN_CMD,
            leading_indicators=_leading(perf_raw=raw),
        )


def test_degraded_validator_accepts_wrapped_no_perf_command_and_null_raw_counters():
    leading = _leading(
        perf_raw={event: None for event in perf_preflight.PERF_EVENTS},
    )
    observation = _degraded_observation()

    assert perf_preflight.validate_perf_observation(
        observation,
        run_cmd="numactl --interleave=all /opt/ccbench/ycsb -thread_num=48",
        leading_indicators=leading,
    ) == observation


def test_probe_error_cannot_build_or_validate_an_observation():
    def raising(*_args, **_kwargs):
        raise OSError("probe failed")

    receipt = perf_preflight.probe_perf_availability(subprocess_runner=raising)
    observation = _degraded_observation()
    observation["preflight"] = receipt

    with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
        perf_preflight.build_perf_observation(
            receipt, run_cmd=NO_PERF_RUN_CMD, leading_indicators=_leading(),
        )
    with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
        perf_preflight.validate_perf_observation(
            observation, run_cmd=NO_PERF_RUN_CMD,
            leading_indicators=_leading(),
        )


def test_perf_claim_allowed_validates_then_applies_exact_scope():
    observation = _degraded_observation()
    kwargs = {
        "run_cmd": NO_PERF_RUN_CMD,
        "leading_indicators": _leading(),
    }

    assert perf_preflight.perf_claim_allowed(
        observation, "throughput", **kwargs,
    ) is True
    assert perf_preflight.perf_claim_allowed(
        observation, "perf_required", **kwargs,
    ) is False
    with pytest.raises(perf_preflight.PerfPreflightError, match="未知"):
        perf_preflight.perf_claim_allowed(observation, "latency", **kwargs)

    changed = _degraded_observation()
    changed["claim_scope"]["perf_required"] = "eligible"
    with pytest.raises(perf_preflight.PerfPreflightError, match="claim_scope"):
        perf_preflight.perf_claim_allowed(changed, "throughput", **kwargs)


def test_perf_claim_allowed_accepts_true_observation_without_degraded_scope():
    receipt = perf_preflight.probe_perf_availability(
        subprocess_runner=_runner_with_output(EVENT_LINES),
    )
    leading = _leading(ipc=1.5, llc_miss_rate=0.2)
    observation = perf_preflight.build_perf_observation(
        receipt, run_cmd=PERF_RUN_CMD, leading_indicators=leading,
    )

    assert perf_preflight.perf_claim_allowed(
        observation, "throughput", run_cmd=PERF_RUN_CMD,
        leading_indicators=leading,
    ) is True
    assert perf_preflight.perf_claim_allowed(
        observation, "perf_required", run_cmd=PERF_RUN_CMD,
        leading_indicators=leading,
    ) is True


def test_perf_claim_allowed_has_attributable_deny_seam(monkeypatch):
    observation = _degraded_observation()
    validate_calls = []
    decision_calls = []
    real_validate = perf_preflight.validate_perf_observation

    def validate_spy(value, **kwargs):
        validate_calls.append((value, kwargs))
        return real_validate(value, **kwargs)

    def deny(scope, claim):
        decision_calls.append((dict(scope), claim))
        return False

    monkeypatch.setattr(perf_preflight, "validate_perf_observation", validate_spy)
    monkeypatch.setattr(perf_preflight, "_claim_decision", deny)

    assert perf_preflight.perf_claim_allowed(
        observation, "throughput", run_cmd=NO_PERF_RUN_CMD,
        leading_indicators=_leading(),
    ) is False
    assert len(validate_calls) == 1
    assert decision_calls == [(observation["claim_scope"], "throughput")]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
