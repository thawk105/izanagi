"""Local fork verification uses live verifier and receipt admission."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from orchestrator.campaign import pipeline, wal
from orchestrator.campaign.model import Genome, STAGE_COMMIT, STAGE_VERIFY_DONE
from orchestrator.campaign.pipeline import CorrectnessWorkload, PerfConfig
from orchestrator.tests import test_campaign as fixtures

_HERE = Path(__file__).resolve().parent


def _evaluate(*, concurrent: bool, red_rep: int | None = None,
              trace_failure: int | None = None, events=None,
              fork_pids=None, verify_calls=None):
    fixtures._refresh_certified_writer_authority()
    layout = fixtures._tmp_layout()
    context = fixtures._BUILD_CONTEXT
    live_verifier = pipeline.verify_trace_dir_with_capability
    live_fork = os.fork
    collected = []
    with fixtures._mock_pipeline_multipass([(2, 0, 1, True)] * 6):
        pipeline.verify_trace_dir_with_capability = live_verifier

        def observed_verify(directory, *, expected_commits=None, **kwargs):
            if verify_calls is not None:
                assert expected_commits == 2
            return live_verifier(directory, expected_commits=expected_commits, **kwargs)

        if verify_calls is not None:
            pipeline.verify_trace_dir_with_capability = observed_verify

        def observed_fork():
            if events is not None:
                events.append(("fork", len(collected)))
            pid = live_fork()
            if pid and fork_pids is not None:
                fork_pids.append(pid)
            return pid

        if events is not None or fork_pids is not None:
            pipeline.os.fork = observed_fork

        def trace(binary, directory, flags, clocks_per_us, **kwargs):
            rep = len(collected) - 1
            collected.append(directory)
            if events is not None:
                events.append(("trace", rep))
            if trace_failure is not None and rep == trace_failure:
                return pipeline._TraceRunResult(2, 1, 1, 2, 0)
            source = "r1_write_skew" if rep == red_rep else "g1_serial"
            shutil.copyfile(_HERE / "fixtures" / source / "trace_0.log",
                            Path(directory) / "trace_0.log")
            return pipeline._TraceRunResult(2, 0, 1, 2, 0)

        pipeline._run_trace = trace
        try:
            result = pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), layout,
                fixtures._AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1000, threads=2), clocks_per_us=1800,
                numactl=list(fixtures._AUTH_CONTRACT.numactl),
                authorization_contract=fixtures._AUTHORIZATION,
                extra_correctness=[(
                    pipeline.PERFORMANCE_TAG,
                    CorrectnessWorkload(
                        flags={"thread_num": "2", "extime": "1"}, reps=5,
                    ),
                )],
                verify_performance_concurrent=concurrent,
                do_bench=False, log=lambda *_: None, build_context=context,
            )
        finally:
            pipeline.os.fork = live_fork
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


def test_all_traces_collected_before_first_fork():
    events = []
    result, _, _ = _evaluate(concurrent=True, events=events)
    assert result.certified
    assert events[:6] == [("trace", rep) for rep in range(-1, 5)]
    assert events[6:] == [("fork", 6)] * 5


def test_failed_rep_reaps_every_later_child():
    pids = []
    try:
        result, _, _ = _evaluate(concurrent=True, red_rep=2, fork_pids=pids)
        assert result.aborted and result.verdict == "non-serializable"
        assert len(pids) == 5
        for pid in pids[3:]:
            with pytest.raises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
    finally:
        for pid in pids:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


def test_expected_commits_reaches_real_verifier_in_fork():
    result, records, _ = _evaluate(concurrent=True, verify_calls=True)
    assert result.certified and not result.aborted
    assert len([r for r in records if r.stage == STAGE_VERIFY_DONE]) == 6
