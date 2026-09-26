"""Local fork verification uses live verifier and receipt admission."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from unittest import mock

import pytest

from orchestrator.campaign import pipeline, wal
from orchestrator.campaign.build_admission import build_run_context, GeneratorId
from orchestrator.campaign.model import Genome, STAGE_COMMIT, STAGE_VERIFY_DONE
from orchestrator.campaign.pipeline import CorrectnessWorkload, PerfConfig
from orchestrator.tests import test_campaign as fixtures

_HERE = Path(__file__).resolve().parent


def _evaluate(*, concurrent: bool, red_rep: int | None = None,
              trace_failure: int | None = None):
    fixtures._refresh_certified_writer_authority()
    layout = fixtures._tmp_layout()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    live_verifier = pipeline.verify_trace_dir_with_capability
    collected = []
    with (mock.patch.object(fixtures, "_BUILD_CONTEXT", context),
          fixtures._mock_pipeline_multipass([(2, 0, 1, True)] * 6)):
        pipeline.verify_trace_dir_with_capability = live_verifier

        def trace(binary, directory, flags, clocks_per_us, **kwargs):
            rep = len(collected) - 1
            collected.append(directory)
            if trace_failure is not None and rep == trace_failure:
                return pipeline._TraceRunResult(2, 1, 1, 2, 0)
            source = "r1_write_skew" if rep == red_rep else "g1_serial"
            shutil.copyfile(_HERE / "fixtures" / source / "trace_0.log",
                            Path(directory) / "trace_0.log")
            return pipeline._TraceRunResult(2, 0, 1, 2, 0)

        pipeline._run_trace = trace
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout,
            fixtures._AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=fixtures._AUTH_CONTRACT.numactl,
            authorization_contract=fixtures._AUTHORIZATION,
            extra_correctness=[(
                pipeline.PERFORMANCE_TAG,
                CorrectnessWorkload(flags={"thread_num": "2", "extime": "1"}, reps=5),
            )],
            verify_performance_concurrent=concurrent,
            do_bench=False, log=lambda *_: None, build_context=context,
        )
    return result, wal.read_records(layout), collected


def test_real_fork_five_receipts_and_rep_order():
    result, records, collected = _evaluate(concurrent=True)
    assert result.certified and not result.aborted
    assert len(collected) == 6
    verifies = [r for r in records if r.stage == STAGE_VERIFY_DONE]
    assert len(verifies) == 6
    assert [r.payload["workload"]["tag"] for r in verifies] == [
        "legacy", *["performance"] * 5,
    ]
    assert all(r.payload["certified"] is True for r in verifies)
    assert len([r for r in records if r.stage == STAGE_COMMIT]) == 1


def test_real_anomaly_stops_projection_and_matches_serial():
    concurrent, records, _ = _evaluate(concurrent=True, red_rep=2)
    serial, serial_records, _ = _evaluate(concurrent=False, red_rep=2)
    assert concurrent.aborted and serial.aborted
    assert concurrent.verdict == serial.verdict == "non-serializable"
    assert [r.stage for r in records] == [r.stage for r in serial_records]
    assert [
        {k: v for k, v in r.payload.items() if k != "build_attempt_id"}
        for r in records if r.stage == STAGE_VERIFY_DONE
    ] == [
        {k: v for k, v in r.payload.items() if k != "build_attempt_id"}
        for r in serial_records if r.stage == STAGE_VERIFY_DONE
    ]
    assert STAGE_COMMIT not in {r.stage for r in records}


def test_acquisition_failure_stops_later_trace_and_projection():
    result, records, collected = _evaluate(concurrent=True, trace_failure=2)
    assert result.aborted
    assert len(collected) == 4  # legacy plus reps 0, 1, 2
    assert len([r for r in records if r.stage == STAGE_VERIFY_DONE]) == 3
    assert STAGE_COMMIT not in {r.stage for r in records}
