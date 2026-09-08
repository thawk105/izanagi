# -*- coding: utf-8 -*-
"""T-2429 verify fan-out transport, worker, and receipt mutation guards."""
from __future__ import annotations

import hashlib
import hmac
import os
import shutil
import shlex
import subprocess
import sys
import threading
import types
from pathlib import Path
from unittest import mock

import pytest

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))

import commit_receipt_support as receipt_support  # noqa: E402
import campaign_lock_test_support  # noqa: E402
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
from orchestrator.verifier import (  # noqa: E402
    CAMPAIGN_WAL_SINK,
    QUALIFICATION_SINK,
)
from orchestrator.verifier.model import (  # noqa: E402
    CompiledProtocolSourceSnapshot,
    capture_compiled_protocol_source_snapshot,
)
from orchestrator.verifier.commit_receipt import (  # noqa: E402
    CommitReceiptError,
    admit_remote_verification_receipt,
    issue_commit_receipt,
    serialize_remote_verification_receipt,
    validate_live_receipt,
)


_RESULT_SECRET = bytes(range(32))


def _recorded_binding():
    return campaign_lock_test_support._binding_from_recorded_head()


def _task_fixture(
        tmp_path: Path, *, expected_binary_sha256: str | None = None,
        variant: str = "fanoutvariant", missing_source_root: bool = False,
) -> tuple[dict, Path, Path]:
    binary = tmp_path / "ycsb_silo.exe"
    binary.write_bytes(b"trace-enabled-test-binary")
    binary.chmod(0o700)
    genome, source, _admission = receipt_support._proof_build_binding(variant)
    if missing_source_root:
        missing_root = str(tmp_path / "source-does-not-exist")
        old_snapshot = source.proof_source_snapshot
        source = SourceEvidence(
            schema_version=source.schema_version,
            source_root=missing_root,
            ccbench_commit=source.ccbench_commit,
            genome_sha256=source.genome_sha256,
            src_token=source.src_token,
            source_bytes_sha256=source.source_bytes_sha256,
            tracked_clean=source.tracked_clean,
            tracked_diff_sha256=source.tracked_diff_sha256,
            tracked_paths=source.tracked_paths,
            proof_source_snapshot=CompiledProtocolSourceSnapshot(
                protocol=old_snapshot.protocol,
                ccbench_root=missing_root,
                normalized_sources=old_snapshot.normalized_sources,
            ),
            verification_variant=variant,
        )
    admission = derive_build_admission(
        build_run_context(generator_id=GeneratorId.BACKOFF_REPRO), source,
    )
    binding = _recorded_binding()
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
        expected_repo_head=binding.contract_loader_commit,
        contract_loader_blob_sha256s=dict(
            binding.contract_loader_blob_sha256s
        ),
        generator_id=GeneratorId.BACKOFF_REPRO,
    )
    task_path = tmp_path / "task.json"
    result_path = tmp_path / "result.json"
    pipeline._write_create_only_json(str(task_path), task)
    return task, task_path, result_path


def _worker_environment(tmp_path: Path) -> dict[str, str]:
    return {
        "USER": "fanout-user",
        "PBS_JOBID": "0:123.nqsv",
    }


def _run_worker(
        task_path: Path, result_path: Path, tmp_path: Path, **kwargs,
) -> int:
    task = pipeline._read_exact_json(str(task_path))
    scr_root = tmp_path / "scr"
    scr_root.mkdir(exist_ok=True)
    binding = types.SimpleNamespace(
        contract_loader_commit=task["expected_repo_head"],
        contract_loader_blob_sha256s=dict(
            task["contract_loader_blob_sha256s"]
        ),
    )
    return worker.run_worker(
        str(task_path), str(result_path),
        result_secret=_RESULT_SECRET,
        contract_loader_binding_resolver=lambda: binding,
        repo_head_resolver=lambda _root: task["expected_repo_head"],
        environment=_worker_environment(tmp_path),
        scr_root=str(scr_root),
        **kwargs,
    )


def _remote_receipt(task: dict, verify_payload: dict) -> dict:
    capability = receipt_support.verification_capabilities(
        (task["tag"],),
        sink_kind=task["receipt_sink_kind"],
        lock_identity_sha256=task["campaign_lock_sha256"],
        variant=task["variant"],
        operation_identity=task["build_attempt_id"],
    )[0]
    return serialize_remote_verification_receipt(
        capability, task_sha256=task["task_sha256"],
        verify_payload_sha256=pipeline._json_sha256(verify_payload),
    )


def _sign_result(unsigned: dict, result_secret: bytes = _RESULT_SECRET) -> dict:
    return {
        **unsigned,
        "result_mac": hmac.new(
            result_secret, pipeline._canonical_json_bytes(unsigned), "sha256",
        ).hexdigest(),
    }


def _success_result(
        task: dict, *, commits: int, result_secret: bytes = _RESULT_SECRET,
) -> dict:
    verify_payload = {
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
    }
    unsigned = {
        "schema": pipeline._VERIFY_FANOUT_RESULT_SCHEMA,
        "task_sha256": task["task_sha256"],
        "build_attempt_id": task["build_attempt_id"],
        "tag": task["tag"],
        "rep": task["rep"],
        "trace_bin_sha256": task["trace_bin_sha256"],
        "outcome": {
            "kind": "success",
            "verify_payload": verify_payload,
            "remote_verification_receipt": _remote_receipt(
                task, verify_payload,
            ),
        },
    }
    return _sign_result(unsigned, result_secret)


def _authenticated_receipt_fixture(
        *, task_sha256: str, variant: str = "v",
        operation_identity: str = "op", workload_tag: str = "performance",
) -> tuple[dict, dict]:
    verify_payload = {"fixture": "authenticated-verifier-payload"}
    capability = receipt_support.verification_capabilities(
        (workload_tag,), sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256="a" * 64, variant=variant,
        operation_identity=operation_identity,
    )[0]
    receipt = serialize_remote_verification_receipt(
        capability, task_sha256=task_sha256,
        verify_payload_sha256=pipeline._json_sha256(verify_payload),
    )
    result = _sign_result({
        "schema": pipeline._VERIFY_FANOUT_RESULT_SCHEMA,
        "task_sha256": task_sha256,
        "build_attempt_id": operation_identity,
        "tag": workload_tag,
        "rep": 1,
        "trace_bin_sha256": "f" * 64,
        "outcome": {
            "kind": "success",
            "verify_payload": verify_payload,
            "remote_verification_receipt": receipt,
        },
    })
    return receipt, result


def _pipeline_case(
        pass_results, *, workload_reps: int,
        verify_fanout_hosts: tuple[str, ...], launcher,
        generator_id: GeneratorId = GeneratorId.BACKOFF_REPRO,
):
    campaign_fixtures._refresh_certified_writer_authority()
    layout = campaign_fixtures._tmp_layout()
    workload = CorrectnessWorkload(
        flags={"thread_num": "48", "extime": "3"},
        reps=workload_reps,
    )
    context = build_run_context(generator_id=generator_id)
    binding = _recorded_binding()

    def capability_resolver(source_evidence):
        return attest_generator_output(
            context, source_evidence,
            generator_input_sha256="f" * 64,
        )

    with (
        mock.patch.object(campaign_fixtures, "_BUILD_CONTEXT", context),
        mock.patch.object(
            pipeline, "_campaign_lock_contract_loader_binding",
            return_value=(
                binding.contract_loader_commit,
                dict(binding.contract_loader_blob_sha256s),
            ),
        ),
        campaign_fixtures._mock_pipeline_multipass(pass_results) as calls,
    ):
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
            build_context=context,
            capability_resolver=capability_resolver,
        )
    return result, calls, layout


def test_m1_worker_rehash_rejects_bytes_corrupted_after_copy(tmp_path: Path) -> None:
    _task, task_path, result_path = _task_fixture(tmp_path)
    calls = []

    def corrupt_copied_bytes(destination: Path) -> None:
        destination.write_bytes(b"corrupted-after-source-hash")

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("sha mismatch must stop before executor")

    assert _run_worker(
        task_path, result_path, tmp_path,
        repetition_executor=forbidden_executor,
        post_copy_hook=corrupt_copied_bytes,
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
    def launcher(_host, _task_path, _result_path, _result_secret):
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

    def launcher(_host, task_path, result_path, result_secret):
        task = pipeline._read_exact_json(task_path)
        if task["rep"] == 1:
            assert rep_two_done.wait(timeout=5)
        pipeline._write_create_only_json(
            result_path, _success_result(
                task, commits=1000 + task["rep"],
                result_secret=result_secret,
            ),
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
    payload, authenticated_result = _authenticated_receipt_fixture(
        task_sha256=task_sha256,
    )
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        admit_remote_verification_receipt(
            payload, expected_task_sha256="2" * 64,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", workload_tag="performance",
            authenticated_result=authenticated_result,
            result_secret=_RESULT_SECRET,
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
    payload, authenticated_result = _authenticated_receipt_fixture(
        task_sha256=task_sha256,
    )
    expected = {
        "expected_task_sha256": task_sha256,
        "lock_identity_sha256": "a" * 64,
        "variant": "v",
        "operation_identity": "op",
        "workload_tag": "performance",
        "authenticated_result": authenticated_result,
        "result_secret": _RESULT_SECRET,
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
    result.pop("result_mac")
    result[field] = replacement
    result = _sign_result(result)
    pipeline._write_create_only_json(str(result_path), result)
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 0, stdout="", stderr="",
        ),
        result_secret=_RESULT_SECRET,
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
        result_secret=_RESULT_SECRET,
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
    task, task_path, result_path = _task_fixture(tmp_path)
    calls = []
    scr_root = tmp_path / "scr"
    scr_root.mkdir()
    binding = types.SimpleNamespace(
        contract_loader_commit=task["expected_repo_head"],
        contract_loader_blob_sha256s=task["contract_loader_blob_sha256s"],
    )

    def forbidden_executor(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("repo HEAD mismatch must stop before executor")

    assert worker.run_worker(
        str(task_path), str(result_path),
        result_secret=_RESULT_SECRET,
        contract_loader_binding_resolver=lambda: binding,
        repo_head_resolver=lambda _root: "c" * 40,
        environment=_worker_environment(tmp_path),
        scr_root=str(scr_root),
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


def test_m7_remote_admit_rejects_dict_without_transport_secret() -> None:
    payload, authenticated_result = _authenticated_receipt_fixture(
        task_sha256="7" * 64,
    )
    with pytest.raises(CommitReceiptError, match="transport secret"):
        admit_remote_verification_receipt(
            payload, expected_task_sha256="7" * 64,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", workload_tag="performance",
            authenticated_result=authenticated_result,
        )


def test_m8_worker_uses_node_local_lock_path(tmp_path: Path) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
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
    assert str(lock_path).startswith(str(tmp_path / "scr"))
    assert ".izanagi" not in lock_path.parts
    assert not (
        tmp_path / "scr" / "fanout-user" / "izanagi-verify-fanout"
        / "0_123.nqsv" / task["task_sha256"]
    ).exists()


@pytest.mark.parametrize("drop_mac", (False, True))
def test_m11_head_rejects_mismatched_or_missing_result_hmac(
        tmp_path: Path, drop_mac: bool,
) -> None:
    task, _task_path, result_path = _task_fixture(tmp_path)
    result = _success_result(task, commits=1000)
    if drop_mac:
        result.pop("result_mac")
    else:
        result["result_mac"] = "0" * 64
    pipeline._write_create_only_json(str(result_path), result)
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 0, stdout="", stderr="",
        ), result_secret=_RESULT_SECRET,
    )
    assert admitted.abort is not None
    assert admitted.abort.reason == "verify-remote-unavailable"
    assert "HMAC mismatch or missing" in (
        admitted.abort.detail["remote"]["stderr_tail"]
    )


def test_head_rejects_authenticated_payload_not_bound_by_remote_receipt(
        tmp_path: Path,
) -> None:
    task, _task_path, result_path = _task_fixture(tmp_path)
    result = _success_result(task, commits=1000)
    result.pop("result_mac")
    result["outcome"]["verify_payload"]["commits"] = 1001
    result = _sign_result(result)
    pipeline._write_create_only_json(str(result_path), result)
    admitted = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess(
            [], 0, stdout="", stderr="",
        ), result_secret=_RESULT_SECRET,
    )
    assert admitted.abort is not None
    assert admitted.abort.reason == "verify-remote-unavailable"
    assert "remote receipt sink binding mismatch" in (
        admitted.abort.detail["remote"]["stderr_tail"]
    )


def test_m12_task_has_no_secret_and_launcher_sends_it_only_on_stdin(
        tmp_path: Path,
) -> None:
    task, task_path, _result_path = _task_fixture(tmp_path)
    assert set(task) == {
        "schema", "campaign_lock_sha256", "variant", "build_attempt_id",
        "tag", "rep", "trace_binary", "trace_bin_sha256",
        "workload_flags", "clocks_per_us", "numactl_prefix",
        "TRACE_TIMEOUT_S", "genome", "source_evidence",
        "proof_source_snapshot", "build_admission", "receipt_sink_kind",
        "generator_id", "expected_repo_head",
        "contract_loader_blob_sha256s", "task_sha256",
    }
    on_disk = pipeline._read_exact_json(str(task_path))
    assert set(on_disk) == set(task)

    completed = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
    with (
        mock.patch.dict(os.environ, {"PBS_JOBID": "1234.nqsv"}),
        mock.patch.object(
            pipeline.subprocess, "run", return_value=completed,
        ) as run,
    ):
        pipeline._default_verify_fanout_launcher(
            "host1", str(task_path), "/work/result.json", _RESULT_SECRET,
        )
    argv = run.call_args.args[0]
    assert _RESULT_SECRET not in argv
    assert run.call_args.kwargs["input"] == _RESULT_SECRET


def test_head_admitted_task_set_rejects_second_result_admission(
        tmp_path: Path,
) -> None:
    task, _task_path, result_path = _task_fixture(tmp_path)
    pipeline._write_create_only_json(
        str(result_path), _success_result(task, commits=1000),
    )
    admitted_tasks: set[str] = set()
    first = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        result_secret=_RESULT_SECRET,
        admitted_task_sha256s=admitted_tasks,
    )
    assert first.abort is None
    second = pipeline._admit_verify_fanout_result(
        task, host="host1", result_path=str(result_path),
        launch_result=subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        result_secret=_RESULT_SECRET,
        admitted_task_sha256s=admitted_tasks,
    )
    assert second.abort is not None
    assert second.abort.reason == "verify-remote-unavailable"
    assert "already admitted" in second.abort.detail["remote"]["stderr_tail"]


def test_m14_worker_closure_digest_mismatch_exits_without_result(
        tmp_path: Path,
) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
    mismatched = dict(task["contract_loader_blob_sha256s"])
    first_path = next(iter(mismatched))
    mismatched[first_path] = "0" * 64
    binding = types.SimpleNamespace(
        contract_loader_commit=task["expected_repo_head"],
        contract_loader_blob_sha256s=mismatched,
    )
    scr_root = tmp_path / "scr"
    scr_root.mkdir()
    executor_calls = []

    def forbidden_executor(*args, **kwargs):
        executor_calls.append((args, kwargs))
        raise AssertionError("closure mismatch must stop before executor")

    assert worker.run_worker(
        str(task_path), str(result_path), result_secret=_RESULT_SECRET,
        contract_loader_binding_resolver=lambda: binding,
        repo_head_resolver=lambda _root: task["expected_repo_head"],
        environment=_worker_environment(tmp_path),
        scr_root=str(scr_root), repetition_executor=forbidden_executor,
    ) != 0
    assert not result_path.exists()
    assert executor_calls == []


def test_m15_worker_unavailable_scr_exits_without_result(
        tmp_path: Path,
) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
    binding = types.SimpleNamespace(
        contract_loader_commit=task["expected_repo_head"],
        contract_loader_blob_sha256s=task["contract_loader_blob_sha256s"],
    )
    executor_calls = []

    def forbidden_executor(*args, **kwargs):
        executor_calls.append((args, kwargs))
        raise AssertionError("unavailable /scr must stop before executor")

    assert worker.run_worker(
        str(task_path), str(result_path), result_secret=_RESULT_SECRET,
        contract_loader_binding_resolver=lambda: binding,
        repo_head_resolver=lambda _root: task["expected_repo_head"],
        environment=_worker_environment(tmp_path),
        scr_root=str(tmp_path / "missing-scr"),
        repetition_executor=forbidden_executor,
    ) != 0
    assert not result_path.exists()
    assert executor_calls == []


def test_worker_missing_pbs_jobid_exits_without_result(tmp_path: Path) -> None:
    task, task_path, result_path = _task_fixture(tmp_path)
    binding = types.SimpleNamespace(
        contract_loader_commit=task["expected_repo_head"],
        contract_loader_blob_sha256s=task["contract_loader_blob_sha256s"],
    )
    scr_root = tmp_path / "scr"
    scr_root.mkdir()
    assert worker.run_worker(
        str(task_path), str(result_path), result_secret=_RESULT_SECRET,
        contract_loader_binding_resolver=lambda: binding,
        environment={"USER": "fanout-user"}, scr_root=str(scr_root),
    ) != 0
    assert not result_path.exists()


@pytest.mark.parametrize(
    "hosts", (("host1", "host1"), ("__CURRENT_HOST__",)),
)
def test_m16_evaluate_rejects_duplicate_or_current_host(hosts) -> None:
    if hosts == ("__CURRENT_HOST__",):
        hosts = (pipeline.socket.gethostname(),)
    with pytest.raises(ValueError, match="重複と current host"):
        _pipeline_case(
            [(100, 0, 5, True)], workload_reps=1,
            verify_fanout_hosts=hosts, launcher=lambda *_args: None,
        )


def test_non_backoff_repro_generator_keeps_all_repetitions_local() -> None:
    launcher_calls = []

    def forbidden_launcher(*args):
        launcher_calls.append(args)
        raise AssertionError("out-of-scope generator must not create remote task")

    result, calls, layout = _pipeline_case(
        [
            (100, 0, 5, True),
            (1000, 0, 6, True),
            (1001, 0, 7, True),
            (1002, 0, 8, True),
        ],
        workload_reps=3, verify_fanout_hosts=("host1",),
        launcher=forbidden_launcher,
        generator_id=GeneratorId.BACKOFF_SWEEP,
    )
    assert result.certified and not result.aborted
    assert len(calls["trace"]) == 4
    assert launcher_calls == []
    assert not os.path.exists(os.path.join(layout.root, "verify-fanout"))


def test_remote_receipt_bridge_rejects_qualification_sink() -> None:
    capability = receipt_support.verification_capabilities(
        ("performance",), sink_kind=QUALIFICATION_SINK,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op",
    )[0]
    with pytest.raises(CommitReceiptError, match="campaign-wal only"):
        serialize_remote_verification_receipt(
            capability, task_sha256="8" * 64,
            verify_payload_sha256="9" * 64,
        )


def test_default_launcher_preserves_one_quoted_bash_command() -> None:
    completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
    with (
        mock.patch.dict(os.environ, {"PBS_JOBID": "1234.nqsv"}),
        mock.patch.object(
            pipeline.subprocess, "run", return_value=completed,
        ) as run,
    ):
        assert pipeline._default_verify_fanout_launcher(
            "host1", "/work/task one.json", "/work/result one.json",
            _RESULT_SECRET,
        ) is completed
    argv = run.call_args.args[0]
    assert argv[:6] == [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
        "host1",
    ]
    assert argv[6:8] == ["bash", "-c"]
    remote_command = shlex.split(argv[8])[0]
    assert remote_command.startswith("cd ")
    assert " && exec env PBS_JOBID=1234.nqsv " in remote_command
    assert " -B -m orchestrator.campaign.verify_fanout_worker " in remote_command
    assert "--task '/work/task one.json' --result '/work/result one.json'" in remote_command
    assert run.call_args.kwargs == {
        "capture_output": True, "input": _RESULT_SECRET,
    }


def test_worker_uses_carried_snapshot_when_source_tree_is_absent(
        tmp_path: Path,
) -> None:
    task, task_path, result_path = _task_fixture(
        tmp_path, missing_source_root=True,
    )
    assert not Path(task["source_evidence"]["source_root"]).exists()
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
        result_secret=_RESULT_SECRET,
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
        task, genome, source.proof_source_snapshot,
    )
    assert rehydrated_source.as_receipt() == source.as_receipt()
    assert rehydrated_admission.as_wal_receipt() == admission.as_wal_receipt()


def test_remote_evidence_round_trip_is_single_use_and_preserves_projection() -> None:
    task_sha256 = "3" * 64
    serialized, authenticated_result = _authenticated_receipt_fixture(
        task_sha256=task_sha256,
    )
    evidence = admit_remote_verification_receipt(
        serialized, expected_task_sha256=task_sha256,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op", workload_tag="performance",
        authenticated_result=authenticated_result,
        result_secret=_RESULT_SECRET,
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


def test_m13_remote_receipt_rejects_second_admission() -> None:
    task_sha256 = "4" * 64
    serialized, authenticated_result = _authenticated_receipt_fixture(
        task_sha256=task_sha256,
    )
    first = admit_remote_verification_receipt(
        serialized, expected_task_sha256=task_sha256,
        lock_identity_sha256="a" * 64, variant="v",
        operation_identity="op", workload_tag="performance",
        authenticated_result=authenticated_result,
        result_secret=_RESULT_SECRET,
    )
    assert first is not None
    with pytest.raises(CommitReceiptError, match="already admitted"):
        admit_remote_verification_receipt(
            serialized, expected_task_sha256=task_sha256,
            lock_identity_sha256="a" * 64, variant="v",
            operation_identity="op", workload_tag="performance",
            authenticated_result=authenticated_result,
            result_secret=_RESULT_SECRET,
        )


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-q"]))
