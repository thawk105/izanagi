# -*- coding: utf-8 -*-
"""Typed verifier-result retention at the campaign pipeline boundary."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))

from orchestrator.campaign import pipeline, wal  # noqa: E402
from orchestrator.campaign.model import STAGE_ABORT, STAGE_COMMIT  # noqa: E402
from orchestrator.tests import test_campaign as campaign_fixtures  # noqa: E402
from orchestrator.tests import test_verify_fanout as fanout_fixtures  # noqa: E402
from orchestrator.verifier import result_to_dict  # noqa: E402
from orchestrator.verifier.model import VerifyResult  # noqa: E402


class _VerifyResultSubclass(VerifyResult):
    pass


def _trace_fixture(name: str) -> str:
    return (_HERE / "fixtures" / name / "trace_0.log").read_text(
        encoding="ascii",
    )


def _local_evaluation(trace_fixture: str):
    campaign_fixtures._refresh_certified_writer_authority()
    layout = campaign_fixtures._tmp_layout()
    result, _calls = campaign_fixtures._eval(
        layout,
        do_bench=False,
        trace_content=_trace_fixture(trace_fixture),
        ncommit=2,
    )
    return result, layout


def _terminal_payload(layout, stage: str) -> dict:
    terminals = [
        record.payload for record in wal.read_records(layout)
        if record.stage == stage
    ]
    assert len(terminals) == 1
    return terminals[0]


def test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding():
    """The real local verifier result remains bound to its real terminal WAL."""
    real_verifier = pipeline.verify_trace_dir_with_capability
    issued_results = []

    def capture_real_result(*args, **kwargs):
        issued = real_verifier(*args, **kwargs)
        issued_results.append(issued[0])
        return issued

    with mock.patch.object(
            pipeline, "verify_trace_dir_with_capability", capture_real_result):
        result, layout = _local_evaluation("r1_write_skew")

    assert result.aborted and not result.certified
    assert type(result.verify_result) is VerifyResult
    assert len(issued_results) == 1
    assert issued_results[0] is result.verify_result
    expected_wire = result_to_dict(result.verify_result)
    expected_wire.pop("trace_dir", None)
    abort_payload = _terminal_payload(layout, STAGE_ABORT)
    assert abort_payload["verify"] == expected_wire
    assert result.build_attempt_id == abort_payload["build_attempt_id"]


def test_remote_fanout_abort_does_not_reconstruct_typed_verify_result():
    """Authenticated wire admission never manufactures a local VerifyResult."""
    wire_verify = {
        "verdict": "non-serializable",
        "anomaly_count": 1,
        "anomalies": [{"phenomenon": "G2"}],
    }

    def launcher(_host, task_path, result_path, result_secret):
        task = pipeline._read_exact_json(task_path)
        verify_payload = {
            "build_attempt_id": task["build_attempt_id"],
            "verdict": "non-serializable",
            "certified": False,
            "commits": 2,
            "aborts": 1,
            "commit_witness": {
                "commit_counts": 2,
                "batch_commit_counts": 0,
            },
            "anomalies": 1,
            "workload": {"tag": task["tag"]},
            "proof_surfaces": {
                "protocol": "silo",
                "X": "evidence-present",
                "P": "evidence-present",
                "I": "evidence-present",
            },
        }
        unsigned = {
            "schema": pipeline._VERIFY_FANOUT_RESULT_SCHEMA,
            "task_sha256": task["task_sha256"],
            "build_attempt_id": task["build_attempt_id"],
            "tag": task["tag"],
            "rep": task["rep"],
            "trace_bin_sha256": task["trace_bin_sha256"],
            "outcome": {
                "kind": "abort",
                "reason": "non-serializable",
                "message": "remote verifier rejected",
                "detail": {"verify": wire_verify},
                "workload_tag": task["tag"],
                "verify_payload": verify_payload,
            },
        }
        pipeline._write_create_only_json(
            result_path,
            fanout_fixtures._sign_result(unsigned, result_secret),
        )
        return subprocess.CompletedProcess([], 0, stdout="", stderr="")

    result, _calls, layout = fanout_fixtures._pipeline_case(
        [(100, 0, 5, True), (200, 0, 6, True)],
        workload_reps=2,
        verify_fanout_hosts=("host1",),
        launcher=launcher,
    )

    assert result.aborted and not result.certified
    abort_payload = _terminal_payload(layout, STAGE_ABORT)
    assert abort_payload["reason"] == "non-serializable"
    assert abort_payload["verify"] == wire_verify
    assert result.verify_result is None


def test_abort_rejects_non_exact_verify_result():
    """The real abort gate rejects a wire dict and a VerifyResult subclass."""
    invalid_values = ({}, object.__new__(_VerifyResultSubclass))
    for invalid_value in invalid_values:
        forged = pipeline._RepetitionExecutionOutcome(
            abort=pipeline._RepetitionAbortOutcome(
                reason="non-serializable",
                message="fixture reject",
                detail={"verify": {}},
                workload_tag=pipeline.LEGACY_TAG,
            ),
            verify_result=invalid_value,
        )
        with mock.patch.object(
                pipeline, "_execute_verification_repetition",
                return_value=forged):
            with pytest.raises(
                    TypeError,
                    match="^verify_result must be an exact VerifyResult$"):
                _local_evaluation("r1_write_skew")


def test_accepted_evaluation_does_not_retain_one_pass_verify_result():
    """A real accepted evaluation is represented by COMMIT, not one pass value."""
    result, layout = _local_evaluation("g1_serial")

    assert result.certified and not result.aborted
    assert result.verify_result is None
    commit_payload = _terminal_payload(layout, STAGE_COMMIT)
    assert result.build_attempt_id == commit_payload["build_attempt_id"]


def test_prebuild_abort_retains_generated_build_attempt_id():
    """The pre-build terminal and EvalResult expose the same generated attempt."""
    campaign_fixtures._refresh_certified_writer_authority()
    layout = campaign_fixtures._tmp_layout()
    result, _calls = campaign_fixtures._eval(
        layout,
        do_bench=False,
        source_raises=True,
    )

    abort_payload = _terminal_payload(layout, STAGE_ABORT)
    assert result.aborted and result.build_attempt_id
    assert result.build_attempt_id == abort_payload["build_attempt_id"]
    assert result.verify_result is None


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
