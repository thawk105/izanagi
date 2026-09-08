# -*- coding: utf-8 -*-
"""T-2429 verify fan-out transport, worker, and receipt mutation guards."""
from __future__ import annotations

import hashlib
import os
import shutil
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from unittest import mock

import pytest

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))

import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.campaign import pipeline, wal  # noqa: E402
from orchestrator.campaign import verify_fanout_worker as worker  # noqa: E402
from orchestrator.calibrator.runner import CompetingBenchProbeError  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import (  # noqa: E402
    Genome,
    STAGE_ABORT,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)
from orchestrator.campaign.pipeline import CorrectnessWorkload, PerfConfig  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    SourceEvidence,
)
from orchestrator.tests import test_campaign as campaign_fixtures  # noqa: E402
from orchestrator.verifier import CAMPAIGN_WAL_SINK  # noqa: E402
from orchestrator.verifier.model import (  # noqa: E402
    capture_compiled_protocol_source_snapshot,
)
from orchestrator.verifier.commit_receipt import (  # noqa: E402
    CommitReceiptError,
    admit_remote_verification_receipt,
    issue_commit_receipt,
    serialize_remote_verification_receipt,
    validate_live_receipt,
)


def _task_fixture(
        tmp_path: Path, *, expected_binary_sha256: str | None = None,
        variant: str = "fanoutvariant",
) -> tuple[dict, Path, Path]:
    binary = tmp_path / "ycsb_silo.exe"
    binary.write_bytes(b"trace-enabled-test-binary")
    binary.chmod(0o700)
    genome, source, admission = receipt_support._proof_build_binding(variant)
    task = pipeline._make_verify_fanout_task(
        campaign_lock_sha256="a" * 64,
        variant=variant,
        build_attempt_id="build-attempt",
        tag=pipeline.PERFORMANCE_TAG,
        rep=1,
        trace_binary=str(binary),
        trace_bin_sha256=(
            expected_binary_sha256
            if expected_binary_sha256 is not None
            else hashlib.sha256(binary.read_bytes()).hexdigest()
        ),
        workload_flags={"thread_num": "48", "extime": "3"},
        clocks_per_us=1800,
        numactl_prefix=("numactl", "--interleave=all"),
        genome=genome,
        source_evidence=source,
        build_admission=admission,
        receipt_sink_kind=CAMPAIGN_WAL_SINK,
        expected_repo_head="b" * 40,
    )
    task_path = tmp_path / "task.json"
    result_path = tmp_path / "result.json"
    pipeline._write_create_only_json(str(task_path), task)
    return task, task_path, result_path


def _worker_environment(tmp_path: Path) -> dict[str, str]:
    node_tmp = tmp_path / "node-tmp"
    node_tmp.mkdir()
    return {
        "USER": "fanout-user",
        "PBS_JOBID": "0:123.nqsv",
        "TMPDIR": str(node_tmp),
    }


def _run_worker(
        task_path: Path, result_path: Path, tmp_path: Path, **kwargs,
) -> int:
    return worker.run_worker(
        str(task_path), str(result_path),
        repo_head_resolver=lambda _root: "b" * 40,
        environment=_worker_environment(tmp_path),
        scr_root=str(tmp_path / "absent-scr"),
        **kwargs,
    )


def _remote_receipt(task: dict) -> dict:
    capability = receipt_support.verification_capabilities(
        (task["tag"],),
        sink_kind=task["receipt_sink_kind"],
        lock_identity_sha256=task["campaign_lock_sha256"],
        variant=task["variant"],
        operation_identity=task["build_attempt_id"],
    )[0]
    return serialize_remote_verification_receipt(
        capability, task_sha256=task["task_sha256"],
    )


def _success_result(task: dict, *, commits: int) -> dict:
    return {
        "schema": pipeline._VERIFY_FANOUT_RESULT_SCHEMA,
        "task_sha256": task["task_sha256"],
        "build_attempt_id": task["build_attempt_id"],
        "tag": task["tag"],
        "rep": task["rep"],
        "trace_bin_sha256": task["trace_bin_sha256"],
        "outcome": {
            "kind": "success",
            "verify_payload": {
                "build_attempt_id": task["build_attempt_id"],
                "verdict": "serializable",
                "certified": True,
                "commits": commits,
                "aborts": 7,
                "commit_witness": {
                    "commit_counts": commits,
                    "batch_commit_counts": 0,
                },
                "anomalies": 0,
                "workload": {"tag": task["tag"]},
                "proof_surfaces": {
                    "protocol": "silo", "X": "evidence-present",
                    "P": "evidence-present", "I": "evidence-present",
                },
            },
            "remote_verification_receipt": _remote_receipt(task),
        },
    }


def _pipeline_case(
        pass_results, *, workload_reps: int,
        verify_fanout_hosts: tuple[str, ...], launcher,
):
    campaign_fixtures._refresh_certified_writer_authority()
    layout = campaign_fixtures._tmp_layout()
    workload = CorrectnessWorkload(
        flags={"thread_num": "48", "extime": "3"},
        reps=workload_reps,
    )
    with campaign_fixtures._mock_pipeline_multipass(pass_results) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout,
            campaign_fixtures._AUTH_CONTRACT.env_tag, "deadbeef",
            PerfConfig(records=1000, threads=2), clocks_per_us=1800,
            numactl=campaign_fixtures._AUTH_CONTRACT.numactl,
            authorization_contract=campaign_fixtures._AUTHORIZATION,
            extra_correctness=[(pipeline.PERFORMANCE_TAG, workload)],
            verify_fanout_hosts=verify_fanout_hosts,
            verify_fanout_launcher=launcher,
            do_bench=False, log=lambda *_args: None,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    return result, calls, layout


def test_m1_worker_binary_sha_mismatch_aborts_before_executor(tmp_path: Path) -> None:
    _task, task_path, result_path = _task_fixture(
        tmp_path, expected_binary_sha256="f" * 64,
    )
    calls = []

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("sha mismatch must stop before executor")

    assert _run_worker(
        task_path, result_path, tmp_path,
        repetition_executor=forbidden_executor,
    ) == 0
    result = pipeline._read_exact_json(str(result_path))
    assert result["outcome"]["reason"] == "verify-remote-unavailable"
    assert "sha256 mismatch" in result["outcome"]["detail"]["worker_error"]
    assert calls == []


def test_worker_missing_binary_aborts_before_executor(tmp_path: Path) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
    Path(task["trace_binary"]).unlink()
    calls = []

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("missing binary must stop before executor")

    assert _run_worker(
        task_path, result_path, tmp_path,
        repetition_executor=forbidden_executor,
    ) == 0
    result = pipeline._read_exact_json(str(result_path))
    assert result["outcome"]["reason"] == "verify-remote-unavailable"
    assert "FileNotFoundError" in result["outcome"]["detail"]["worker_error"]
    assert calls == []


def test_m2_missing_remote_result_is_unavailable_abort() -> None:
    def launcher(_host, _task_path, _result_path):
        return subprocess.CompletedProcess([], 0, stdout="", stderr="")

    result, _calls, layout = _pipeline_case(
        [(100, 0, 5, True), (200, 0, 6, True)],
        workload_reps=2, verify_fanout_hosts=("host1",), launcher=launcher,
    )
    assert result.aborted and not result.certified and result.verdict == ""
    records = wal.read_records(layout)
    abort = [record for record in records if record.stage == STAGE_ABORT][-1]
    assert abort.payload["reason"] == "verify-remote-unavailable"
    assert abort.payload["remote"]["host"] == "host1"
    assert STAGE_COMMIT not in {record.stage for record in records}


def test_m3_remote_completion_is_emitted_in_rep_order() -> None:
    rep_two_done = threading.Event()
    completion_order: list[int] = []

    def launcher(_host, task_path, result_path):
        task = pipeline._read_exact_json(task_path)
        if task["rep"] == 1:
            assert rep_two_done.wait(timeout=5)
        pipeline._write_create_only_json(
            result_path, _success_result(task, commits=1000 + task["rep"]),
        )
        completion_order.append(task["rep"])
        if task["rep"] == 2:
            rep_two_done.set()
        return subprocess.CompletedProcess([], 0, stdout="", stderr="")

    result, _calls, layout = _pipeline_case(
        [(100, 0, 5, True), (1000, 0, 6, True)],
        workload_reps=3, verify_fanout_hosts=("host1", "host2"),
        launcher=launcher,
    )
    assert result.certified and completion_order == [2, 1]
    performance = [
        record.payload["commits"] for record in wal.read_records(layout)
        if (record.stage == STAGE_VERIFY_DONE
            and record.payload["workload"]["tag"] == pipeline.PERFORMANCE_TAG)
    ]
    assert performance == [1000, 1001, 1002]


def test_m4_remote_receipt_rejects_task_sha_mismatch() -> None:
    task_sha256 = "1" * 64
    capability = receipt_support.verification_capabilities(
        ("performance",), sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op",
    )[0]
    payload = serialize_remote_verification_receipt(
        capability, task_sha256=task_sha256,
    )
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        admit_remote_verification_receipt(
            payload, expected_task_sha256="2" * 64,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", workload_tag="performance",
        )


@pytest.mark.parametrize(
    ("expected_field", "replacement"),
    (
        ("lock_identity_sha256", "b" * 64),
        ("variant", "other-variant"),
        ("operation_identity", "other-operation"),
        ("workload_tag", "other-tag"),
    ),
)
def test_remote_receipt_rejects_each_operation_binding_mismatch(
        expected_field: str, replacement: str,
) -> None:
    task_sha256 = "1" * 64
    capability = receipt_support.verification_capabilities(
        ("performance",), sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op",
    )[0]
    payload = serialize_remote_verification_receipt(
        capability, task_sha256=task_sha256,
    )
    expected = {
        "expected_task_sha256": task_sha256,
        "lock_identity_sha256": "a" * 64,
        "variant": "v",
        "operation_identity": "op",
        "workload_tag": "performance",
    }
    expected[expected_field] = replacement
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        admit_remote_verification_receipt(payload, **expected)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("task_sha256", "9" * 64),
        ("build_attempt_id", "other-build-attempt"),
        ("tag", "other-tag"),
        ("rep", 7),
        ("trace_bin_sha256", "8" * 64),
    ),
)
def test_head_rejects_each_remote_result_echo_mismatch(
        tmp_path: Path, field: str, replacement: object,
) -> None:
    task, _task_path, result_path = _task_fixture(tmp_path)
    result = _success_result(task, commits=1000)
    result[field] = replacement
    pipeline._write_create_only_json(str(result_path), result)
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 0, stdout="", stderr="",
        ),
    )
    assert admitted.abort is not None
    assert admitted.abort.reason == "verify-remote-unavailable"
    assert admitted.abort.detail["remote"] == {
        "host": "host1", "rep": 1, "rc": 0,
        "stderr_tail": "ValueError: remote result task echo mismatch",
    }


def test_head_rejects_nonzero_ssh_without_reading_result(tmp_path: Path) -> None:
    task, _task_path, result_path = _task_fixture(tmp_path)
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 23, stdout="", stderr="remote worker failed",
        ),
    )
    assert admitted.abort is not None
    assert admitted.abort.reason == "verify-remote-unavailable"
    assert admitted.abort.detail["remote"] == {
        "host": "host1", "rep": 1, "rc": 23,
        "stderr_tail": "remote worker failed",
    }


def test_m5_worker_competing_tenant_aborts_before_executor(tmp_path: Path) -> None:
    _task, task_path, result_path = _task_fixture(tmp_path)
    calls = []

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("competing tenant must stop before executor")

    assert _run_worker(
        task_path, result_path, tmp_path,
        competing_probe=lambda: ["999 /x/ycsb_silo.exe -thread_num=48"],
        repetition_executor=forbidden_executor,
    ) == 0
    result = pipeline._read_exact_json(str(result_path))
    assert result["outcome"]["reason"] == "verify-competing-tenant"
    assert result["outcome"]["detail"]["competing"]
    assert calls == []


def test_worker_probe_error_preserves_local_abort_reason(tmp_path: Path) -> None:
    _task, task_path, result_path = _task_fixture(tmp_path)
    calls = []

    def failing_probe():
        raise CompetingBenchProbeError(
            "unexpected-rc", ["pgrep", "fixture"], returncode=2,
            stderr="probe failed",
        )

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("probe failure must stop before executor")

    assert _run_worker(
        task_path, result_path, tmp_path,
        competing_probe=failing_probe,
        repetition_executor=forbidden_executor,
    ) == 0
    result = pipeline._read_exact_json(str(result_path))
    assert result["outcome"]["reason"] == "verify-probe-error"
    assert result["outcome"]["detail"]["probe_error"] == {
        "kind": "unexpected-rc", "argv": ["pgrep", "fixture"],
        "returncode": 2, "errno": None, "stdout_excerpt": "",
        "stderr_excerpt": "probe failed",
    }
    assert calls == []


def test_worker_repo_head_mismatch_aborts_before_copy_or_executor(
        tmp_path: Path,
) -> None:
    _task, task_path, result_path = _task_fixture(tmp_path)
    calls = []

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("repo HEAD mismatch must stop before executor")

    assert worker.run_worker(
        str(task_path), str(result_path),
        repo_head_resolver=lambda _root: "c" * 40,
        environment=_worker_environment(tmp_path),
        scr_root=str(tmp_path / "absent-scr"),
        repetition_executor=forbidden_executor,
    ) == 0
    result = pipeline._read_exact_json(str(result_path))
    assert result["outcome"]["reason"] == "verify-remote-unavailable"
    assert result["outcome"]["detail"]["worker_error"] == "repo HEAD mismatch"
    assert calls == []


def test_m6_empty_hosts_use_only_the_local_executor() -> None:
    launcher_calls = []

    def forbidden_launcher(*args):
        launcher_calls.append(args)
        raise AssertionError("empty host tuple must not enter remote transport")

    result, calls, layout = _pipeline_case(
        [
            (100, 0, 5, True),
            (1000, 0, 6, True),
            (1001, 0, 7, True),
            (1002, 0, 8, True),
        ],
        workload_reps=3, verify_fanout_hosts=(), launcher=forbidden_launcher,
    )
    assert result.certified and not result.aborted
    assert len(calls["trace"]) == 4
    assert launcher_calls == []
    assert not os.path.exists(os.path.join(layout.root, "verify-fanout"))


def test_m7_issue_commit_receipt_rejects_plain_dict() -> None:
    with pytest.raises(CommitReceiptError, match="not a capability"):
        issue_commit_receipt(
            [{"verdict": "serializable", "certified": True}],
            workload_tags=["performance"], sink_kind=CAMPAIGN_WAL_SINK,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", terminal_payload={"fitness_tps": 1.0},
        )


def test_m8_worker_uses_node_local_lock_path(tmp_path: Path) -> None:
    _task, task_path, result_path = _task_fixture(tmp_path)
    observed_lock_paths = []

    def executor(*args, **kwargs):
        observed_lock_paths.append(os.environ["IZANAGI_BENCH_LOCK"])

        def nonzero_trace(*_trace_args, **_trace_kwargs):
            return pipeline._TraceRunResult(1, 9, 1, 1, 0)

        return pipeline._execute_verification_repetition(
            *args, **kwargs, trace_runner=nonzero_trace,
        )

    assert _run_worker(
        task_path, result_path, tmp_path,
        competing_probe=lambda: [], repetition_executor=executor,
    ) == 0
    assert len(observed_lock_paths) == 1
    lock_path = Path(observed_lock_paths[0])
    assert lock_path.name == "bench.lock"
    assert "izanagi-verify-fanout" in lock_path.parts
    assert str(lock_path).startswith(str(tmp_path / "node-tmp"))
    assert ".izanagi" not in lock_path.parts


def test_default_launcher_preserves_one_quoted_bash_command() -> None:
    completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
    with mock.patch.object(pipeline.subprocess, "run", return_value=completed) as run:
        assert pipeline._default_verify_fanout_launcher(
            "host1", "/work/task one.json", "/work/result one.json",
        ) is completed
    argv = run.call_args.args[0]
    assert argv[:6] == [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
        "host1",
    ]
    assert argv[6:8] == ["bash", "-c"]
    remote_command = shlex.split(argv[8])[0]
    assert remote_command.startswith("cd ")
    assert " && exec " in remote_command
    assert " -B -m orchestrator.campaign.verify_fanout_worker " in remote_command
    assert "--task '/work/task one.json' --result '/work/result one.json'" in remote_command
    assert run.call_args.kwargs == {"capture_output": True, "text": True}


def test_worker_success_uses_real_executor_and_head_admission(tmp_path: Path) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
    fixture = _HERE / "fixtures/g1_serial/trace_0.log"

    def executor(*args, **kwargs):
        trace_dir = Path(args[1])

        def trace_runner(*_trace_args, **_trace_kwargs):
            shutil.copyfile(fixture, trace_dir / "trace_0.log")
            return pipeline._TraceRunResult(2, 0, 1, 2, 0)

        return pipeline._execute_verification_repetition(
            *args, **kwargs, trace_runner=trace_runner,
        )

    assert _run_worker(
        task_path, result_path, tmp_path,
        competing_probe=lambda: [], repetition_executor=executor,
    ) == 0
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 0, stdout="", stderr="",
        ),
    )
    assert admitted.abort is None
    assert admitted.verify_payload["certified"] is True
    assert admitted.verification_capability is not None


def test_worker_rederives_machine_generated_build_admission() -> None:
    variant = "machinevariant"
    genome = Genome("silo", {})
    source_root = receipt_support.proof_source_root()
    source = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(source_root),
        ccbench_commit="deadbeef",
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="c" * 64,
        source_bytes_sha256="d" * 64,
        tracked_clean=False,
        tracked_diff_sha256="e" * 64,
        tracked_paths=("include/generated.hh",),
        proof_source_snapshot=capture_compiled_protocol_source_snapshot(
            "silo", source_root,
        ),
        verification_variant=variant,
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_REPRO)
    generator_receipt = attest_generator_output(
        context, source, generator_input_sha256="f" * 64,
    )
    admission = derive_build_admission(
        context, source, generator_receipt=generator_receipt,
    )
    task = {
        "variant": variant,
        "source_evidence": source.as_receipt(),
        "build_admission": dict(admission.as_wal_receipt()),
    }
    rehydrated_source, rehydrated_admission = worker._rehydrate_build_binding(
        task, genome,
    )
    assert rehydrated_source.as_receipt() == source.as_receipt()
    assert rehydrated_admission.as_wal_receipt() == admission.as_wal_receipt()


def test_remote_evidence_round_trip_is_single_use_and_preserves_projection() -> None:
    task_sha256 = "3" * 64
    capability = receipt_support.verification_capabilities(
        ("performance",), sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op",
    )[0]
    serialized = serialize_remote_verification_receipt(
        capability, task_sha256=task_sha256,
    )
    evidence = admit_remote_verification_receipt(
        serialized, expected_task_sha256=task_sha256,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op", workload_tag="performance",
    )
    with pytest.raises(AttributeError, match="immutable"):
        evidence._nonce = object()
    receipt = issue_commit_receipt(
        [evidence], workload_tags=["performance"],
        sink_kind=CAMPAIGN_WAL_SINK, lock_identity_sha256="a" * 64,
        variant="v", operation_identity="op",
        terminal_payload={"fitness_tps": 1.0},
    )
    projected = validate_live_receipt(
        receipt, sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        terminal_payload={"fitness_tps": 1.0},
    )
    assert set(projected["verifier_evidence"][0]) == {
        "workload_tag", "verdict", "certified", "verifier_result_sha256",
    }
    with pytest.raises(CommitReceiptError, match="already consumed"):
        issue_commit_receipt(
            [evidence], workload_tags=["performance"],
            sink_kind=CAMPAIGN_WAL_SINK, lock_identity_sha256="a" * 64,
            variant="v", operation_identity="op",
            terminal_payload={"fitness_tps": 1.0},
        )


def test_remote_evidence_rejects_duplicate_task_in_one_commit() -> None:
    task_sha256 = "4" * 64
    capabilities = receipt_support.verification_capabilities(
        ("performance", "performance"), sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op",
    )
    serialized = [
        serialize_remote_verification_receipt(
            capability, task_sha256=task_sha256,
        )
        for capability in capabilities
    ]
    evidence = [
        admit_remote_verification_receipt(
            payload, expected_task_sha256=task_sha256,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", workload_tag="performance",
        )
        for payload in serialized
    ]
    with pytest.raises(CommitReceiptError, match="duplicate remote tasks"):
        issue_commit_receipt(
            evidence, workload_tags=["performance", "performance"],
            sink_kind=CAMPAIGN_WAL_SINK, lock_identity_sha256="a" * 64,
            variant="v", operation_identity="op",
            terminal_payload={"fitness_tps": 1.0},
        )


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-q"]))
