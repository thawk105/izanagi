from __future__ import annotations

import types
import sys
from pathlib import Path

import pytest

from orchestrator.campaign import condition_meaning_gate as gate
from tools.pegasus.probes import t2228_driver_gate_liveness_probe as probe


DRIVER_ID = "orchestrator/campaign/backoff_repro.py"


def _record(
    *,
    arm: str,
    status: str,
    request_digest: str,
    record_id: str,
) -> gate.ConditionArmRecord:
    return gate.ConditionArmRecord(
        record_id=record_id,
        record_digest="b" * 64,
        arm=arm,
        terminal_status=status,
        reason_code=("test-green" if status == "green" else "test-red"),
        driver_id=DRIVER_ID,
        macro="BACKOFF_FIXED",
        request_digest=request_digest,
        evidence={},
    )


def _positive_observation() -> probe._GateObservation:
    request = gate.make_define_request(
        driver_id=DRIVER_ID,
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    digest = probe._request_digest(gate, request)
    supply = _record(
        arm="supply-effectuation",
        status="green",
        request_digest=digest,
        record_id="supply-record",
    )
    meaning = _record(
        arm="runtime-meaning",
        status="green",
        request_digest=digest,
        record_id="meaning-record",
    )
    admission = gate.ConditionFamilyAdmission(
        admission_id="admission",
        admission_digest="c" * 64,
        use_class="raw-measurement",
        admitted=True,
        record_ids=(supply.record_id, meaning.record_id),
        unestablished_meaning_macros=(),
    )
    return probe._GateObservation(
        requests=[request],
        supply_records=[supply],
        meaning_records=[meaning],
        admissions=[admission],
    )


def test_m1_exception_before_records_keeps_initial_result_false() -> None:
    def fail_before_gate() -> None:
        raise RuntimeError("pre-gate failure")

    result = probe._base_result("repro")
    _value, observed, completed, exception = probe._measure_call(
        gate,
        driver_id=DRIVER_ID,
        call=fail_before_gate,
    )
    if completed and probe._gate_success(gate, observed):
        result["ok"] = True
    result["exception"] = exception
    probe._finish_result(result)

    assert completed is False
    assert observed == probe._GateObservation()
    assert result["ok"] is False
    assert result["rc"] == 1


def test_m2_red_supply_record_cannot_pass_gate_result() -> None:
    observed = _positive_observation()
    assert probe._gate_success(gate, observed) is True
    original = observed.supply_records[0]
    observed.supply_records[0] = _record(
        arm="supply-effectuation",
        status="red",
        request_digest=original.request_digest,
        record_id=original.record_id,
    )

    assert probe._gate_success(gate, observed) is False


def test_m3_false_production_admission_cannot_pass_gate_result() -> None:
    observed = _positive_observation()
    assert probe._gate_success(gate, observed) is True
    original = observed.admissions[0]
    observed.admissions[0] = gate.ConditionFamilyAdmission(
        admission_id=original.admission_id,
        admission_digest=original.admission_digest,
        use_class=original.use_class,
        admitted=False,
        record_ids=original.record_ids,
        unestablished_meaning_macros=original.unestablished_meaning_macros,
    )

    assert probe._gate_success(gate, observed) is False


def test_m4_runtime_error_without_attribute_keeps_reason_code_null() -> None:
    error = RuntimeError("configure-timeout: text is not a reason attribute")

    document = probe._exception_document(error)

    assert document["type"] == "RuntimeError"
    assert document["message"] == str(error)
    assert document["reason_code"] is None
    assert document["cause"] is None
    assert document["context"] is None


def test_m5_aborted_sweep_summary_cannot_pass() -> None:
    observed = _positive_observation()
    green = types.SimpleNamespace(
        campaign_id="campaign", committed=2, aborted=0, evaluated=2, skipped=0,
    )
    aborted = types.SimpleNamespace(
        campaign_id="campaign", committed=2, aborted=1, evaluated=2, skipped=0,
    )

    assert probe._sweep_accepts(gate, observed, green) is True
    assert probe._sweep_accepts(gate, observed, aborted) is False


def test_m6_atomic_writer_refuses_existing_evidence(tmp_path: Path) -> None:
    destination = tmp_path / "repro.json"
    destination.write_text("existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        probe._write_atomic_create_only(destination, {"ok": True})

    assert destination.read_text(encoding="utf-8") == "existing\n"
    assert list(tmp_path.iterdir()) == [destination]


def _synthetic_freeze_with_one_inert_cell() -> dict:
    cell_ids = [f"cell-{index:02d}" for index in range(18)]
    cells = {}
    for index, cell_id in enumerate(cell_ids):
        cells[cell_id] = {
            "workload": "write-heavy",
            "configuration": "stock_common",
            "variant": {
                "flags": (
                    {"BACKOFF_FIXED": -1}
                    if index == 0
                    else {"WAL": 0}
                ),
            },
        }
    lap = list(cell_ids)
    return {
        "cells": cells,
        "schedule": {
            "floor": [lap],
            "test_block_1": [lap],
            "test_block_2": [lap],
        },
    }


def test_m7_reachability_counts_inert_request_from_freeze_data() -> None:
    reachability = probe._enumerate_s1_reachability(
        _synthetic_freeze_with_one_inert_cell(),
        __import__(
            "orchestrator.campaign.s1_direct_comparison",
            fromlist=["schedule_for_role"],
        ),
        gate,
    )

    assert reachability["cell_count"] == 18
    assert reachability["inert_request_count"] == 1
    assert probe._s1_reachability_success(reachability) is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
