# -*- coding: utf-8 -*-
"""scheduler reservation leaf の fail-closed 挙動。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign.env_contract import IsolationPolicy  # noqa: E402
from orchestrator.campaign.reservation import (  # noqa: E402
    ReservationError,
    check_reservation,
    is_reservation_required,
    read_binding,
)


def _environ() -> dict[str, str]:
    return {
        "IZANAGI_RESERVATION_JOB_ID": "123.server",
        "IZANAGI_RESERVATION_REQUESTED_S": "200",
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": "900",
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": "1100",
        "IZANAGI_RESERVATION_HOST": "node-a",
        "IZANAGI_RESERVATION_BOOT_ID": "boot-a",
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "a" * 64,
        "IZANAGI_RESERVATION_NONCE": "nonce-a",
        "PBS_JOBID": "123.server",
    }


def _check(environ: dict[str, str], **overrides):
    args = {
        "required_s": 70,
        "safety_margin_s": 10,
        "environ": environ,
        "realtime_now_fn": lambda: 1000.0,
        "monotonic_now_fn": lambda: 50.0,
        "boot_id_read_fn": lambda: "boot-a",
    }
    args.update(overrides)
    return check_reservation(read_binding(environ), **args)


def test_read_binding_rejects_missing_empty_and_bad_numeric_values():
    for key, value in (
        ("IZANAGI_RESERVATION_JOB_ID", None),
        ("IZANAGI_RESERVATION_NONCE", ""),
        ("IZANAGI_RESERVATION_REQUESTED_S", "not-an-int"),
        ("IZANAGI_RESERVATION_DEADLINE_EPOCH", "nan"),
    ):
        environ = _environ()
        if value is None:
            del environ[key]
        else:
            environ[key] = value
        with pytest.raises(ReservationError):
            read_binding(environ)


@pytest.mark.parametrize("updates", [
    {"IZANAGI_RESERVATION_DEADLINE_EPOCH": "1101"},
    {"IZANAGI_RESERVATION_SCRIPT_SHA256": "A" * 64},
    {
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": "inf",
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": "inf",
    },
], ids=["deadline-relation", "script-sha256", "nonfinite-epoch"])
def test_read_binding_rejects_each_invalid_binding_field(updates):
    environ = _environ()
    environ.update(updates)
    with pytest.raises(ReservationError):
        read_binding(environ)


def test_environment_text_is_stripped_on_both_binding_and_live_sides():
    environ = _environ()
    environ["IZANAGI_RESERVATION_JOB_ID"] = " 123.server\n"
    environ["IZANAGI_RESERVATION_BOOT_ID"] = " boot-a "
    environ["PBS_JOBID"] = "\t123.server "
    binding = read_binding(environ)
    assert binding.job_id == "123.server"
    assert binding.boot_id == "boot-a"
    assert _check(environ, boot_id_read_fn=lambda: " boot-a\n").remaining_s == 100.0


def test_check_reservation_accepts_bound_job_and_derives_monotonic_deadline():
    checked = _check(_environ())
    assert checked.monotonic_deadline == 150.0
    assert checked.remaining_s == 100.0


@pytest.mark.parametrize(
    ("mutation", "overrides"),
    [
        ({"PBS_JOBID": "other.server"}, {}),
        ({}, {"boot_id_read_fn": lambda: "other-boot"}),
        ({}, {"required_s": 0}),
        ({}, {"required_s": 91}),
        ({}, {"realtime_now_fn": lambda: 899.0}),
    ],
    ids=["job-id-mismatch", "boot-id-mismatch", "zero-required", "insufficient-margin", "future-start"],
)
def test_check_reservation_rejects_each_negative_core(mutation, overrides):
    environ = _environ()
    environ.update(mutation)
    with pytest.raises(ReservationError):
        _check(environ, **overrides)


def test_recheck_uses_monotonic_deadline_despite_realtime_rollback():
    clock = {"realtime": 1000.0, "monotonic": 50.0}
    checked = _check(
        _environ(),
        realtime_now_fn=lambda: clock["realtime"],
        monotonic_now_fn=lambda: clock["monotonic"],
    )

    # wall clock が 100 秒後退しても、monotonic は前進して残り 50 秒になる。
    clock.update(realtime=900.0, monotonic=100.0)
    with pytest.raises(ReservationError):
        checked.recheck(monotonic_now_fn=lambda: clock["monotonic"])


def test_required_is_derived_from_typed_isolation_policy():
    assert is_reservation_required(IsolationPolicy(single_process=True, allow_resume=False)) is True
    assert is_reservation_required(IsolationPolicy(single_process=False, allow_resume=True)) is False
    with pytest.raises(ReservationError):
        is_reservation_required({"single_process": True})


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
