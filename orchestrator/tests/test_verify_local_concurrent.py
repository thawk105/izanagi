"""Local fork verification uses live verifier and receipt admission."""
from __future__ import annotations

import os
import json
import shutil
import time
from pathlib import Path

import pytest

from orchestrator.campaign import pipeline, wal
from orchestrator.verifier import parse
from orchestrator.campaign.model import Genome, STAGE_ABORT, STAGE_COMMIT, STAGE_VERIFY_DONE
from orchestrator.campaign.pipeline import CorrectnessWorkload, PerfConfig
from orchestrator.tests import test_campaign as fixtures

_HERE = Path(__file__).resolve().parent
_ORIGINAL_PARSE_WORKER = parse._parse_file_worker
_SLOW_POOL_DIRS = []
_SLOW_POOL_LOG = None


def _probe_parse_worker(task):
    if _SLOW_POOL_LOG is not None and any(
            task[1].startswith(directory + os.sep)
            for directory in _SLOW_POOL_DIRS):
        fd = os.open(_SLOW_POOL_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, f"{os.getpid()}\n".encode())
        finally:
            os.close(fd)
        time.sleep(30)
    return _ORIGINAL_PARSE_WORKER(task)


def _evaluate(*, concurrent: bool, red_rep: int | None = None,
              trace_failure: int | None = None, events=None,
              fork_pids=None, verify_calls=None, slow_reps=(),
              completion_log=None, distinct_first=False,
              slow_pool_log=None, killed_groups=None):
    global _SLOW_POOL_DIRS, _SLOW_POOL_LOG
    fixtures._refresh_certified_writer_authority()
    layout = fixtures._tmp_layout()
    context = fixtures._BUILD_CONTEXT
    live_verifier = pipeline.verify_trace_dir_with_capability
    live_fork = os.fork
    live_killpg = os.killpg
    live_parse_worker = parse._parse_file_worker
    collected = []
    with fixtures._mock_pipeline_multipass([(2, 0, 1, True)] * 6):
        pipeline.verify_trace_dir_with_capability = live_verifier

        def observed_verify(directory, *, expected_commits=None, **kwargs):
            if verify_calls is not None:
                assert expected_commits == 2
            rep = collected.index(directory) - 1
            result = live_verifier(directory, expected_commits=expected_commits, **kwargs)
            if rep in slow_reps:
                time.sleep(0.5)
            if completion_log is not None and rep >= 0:
                fd = os.open(completion_log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
                try:
                    os.write(fd, f"{rep}\n".encode())
                finally:
                    os.close(fd)
            return result

        if verify_calls is not None or slow_reps or completion_log is not None:
            pipeline.verify_trace_dir_with_capability = observed_verify

        if slow_pool_log is not None:
            _SLOW_POOL_DIRS = []
            _SLOW_POOL_LOG = slow_pool_log
            parse._parse_file_worker = _probe_parse_worker

        def observed_killpg(pgid, sig):
            if killed_groups is not None and sig == pipeline.signal.SIGKILL:
                killed_groups.append(pgid)
            return live_killpg(pgid, sig)

        if killed_groups is not None:
            pipeline.os.killpg = observed_killpg

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
            source = ("r1_write_skew" if rep == red_rep else
                      "g6_silo_serial_1thread" if distinct_first and rep == 0
                      else "g1_serial")
            shutil.copyfile(_HERE / "fixtures" / source / "trace_0.log",
                            Path(directory) / "trace_0.log")
            if slow_pool_log is not None and rep >= 3:
                shutil.copyfile(_HERE / "fixtures" / source / "trace_0.log",
                                Path(directory) / "trace_1.log")
                _SLOW_POOL_DIRS.append(directory)
            commits = 200 if distinct_first and rep == 0 else 2
            return pipeline._TraceRunResult(commits, 0, 1, commits, 0)

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
            pipeline.os.killpg = live_killpg
            parse._parse_file_worker = live_parse_worker
            _SLOW_POOL_DIRS = []
            _SLOW_POOL_LOG = None
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


def test_reverse_completion_projects_distinct_payloads_in_rep_order(tmp_path):
    completion_log = tmp_path / "completed"
    result, records, _ = _evaluate(
        concurrent=True, distinct_first=True, slow_reps=(0,),
        completion_log=str(completion_log),
    )
    assert result.certified
    assert int(completion_log.read_text().splitlines()[0]) != 0
    verifies = [r for r in records if r.stage == STAGE_VERIFY_DONE]
    assert [r.payload["commits"] for r in verifies] == [2, 200, 2, 2, 2, 2]


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
            with pytest.raises(ProcessLookupError):
                os.killpg(pid, 0)
    finally:
        for pid in pids:
            try:
                waited, _ = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                continue
            if waited == 0:
                os.killpg(pid, 9)
                os.waitpid(pid, 0)


def test_failed_rep_kills_later_groups_with_live_pool_workers(tmp_path):
    pids = []
    killed = []
    pool_log = tmp_path / "pool-pids"
    started = time.monotonic()
    result, records, _ = _evaluate(
        concurrent=True, red_rep=2, slow_reps=(2,),
        slow_pool_log=str(pool_log), fork_pids=pids, killed_groups=killed,
    )
    assert time.monotonic() - started < 15  # pool workers sleep for 30 seconds
    assert result.aborted and result.verdict == "non-serializable"
    assert len([r for r in records if r.stage == STAGE_VERIFY_DONE]) == 4
    assert pool_log.exists() and pool_log.read_text().strip()
    assert set(pids[3:]).issubset(set(killed))
    for pid in pids[3:]:
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
        with pytest.raises(ProcessLookupError):
            os.killpg(pid, 0)


def test_group_timeout_rejects_reaps_and_preserves_traces(tmp_path, monkeypatch):
    pids = []
    archive_root = tmp_path / "archive"
    monkeypatch.setenv("IZANAGI_TRACE_ARCHIVE_ROOT", str(archive_root))
    monkeypatch.setattr(pipeline, "_LOCAL_GROUP_GONE_TIMEOUT_S", 0.0)
    real_preserve = pipeline._preserve_trace_directory

    def preserve_fixture(trace_dir, root, **kwargs):
        # The proof source fixture is not a git checkout; archive the real
        # traces without that fixture-only source binding.
        return real_preserve(trace_dir, root, **{**kwargs, "evidence": None})

    monkeypatch.setattr(pipeline, "_preserve_trace_directory", preserve_fixture)
    live_check = pipeline._local_group_has_live_members

    def forced_timeout(pgid):
        return pgid == pids[0] or live_check(pgid)

    monkeypatch.setattr(pipeline, "_local_group_has_live_members", forced_timeout)
    result, records, collected = _evaluate(concurrent=True, fork_pids=pids)
    assert result.aborted and not result.certified
    assert [row.payload["reason"] for row in records if row.stage == STAGE_ABORT] == [
        "verify-local-unavailable",
    ]
    assert STAGE_COMMIT not in {row.stage for row in records}
    assert len(pids) == 5
    for pid in pids:
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
    inventories = [json.loads(path.read_text())
                   for path in archive_root.rglob("inventory.json")]
    assert {row["original_directory"] for row in inventories} == set(collected)
    assert all(row["status"] == "complete" for row in inventories)
    assert all(not Path(directory).exists() for directory in collected)


def test_group_checked_before_leader_reaped(monkeypatch):
    events = []
    pids = []
    live_check = pipeline._local_group_has_live_members
    live_waitpid = os.waitpid

    def observed_check(pgid):
        events.append(("check", pgid))
        return live_check(pgid)

    def observed_waitpid(pid, options):
        events.append(("reap", pid))
        return live_waitpid(pid, options)

    monkeypatch.setattr(pipeline, "_local_group_has_live_members", observed_check)
    monkeypatch.setattr(pipeline.os, "waitpid", observed_waitpid)
    result, _, _ = _evaluate(concurrent=True, fork_pids=pids)
    assert result.certified
    assert len(pids) == 5
    for pid in pids:
        assert events.index(("check", pid)) < events.index(("reap", pid))


def test_expected_commits_reaches_real_verifier_in_fork():
    result, records, _ = _evaluate(concurrent=True, verify_calls=True)
    assert result.certified and not result.aborted
    assert len([r for r in records if r.stage == STAGE_VERIFY_DONE]) == 6
