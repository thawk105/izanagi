# -*- coding: utf-8 -*-
"""Task-bound sibling-node worker for full-scale correctness repetitions."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Mapping, Optional

from ..calibrator.runner import CompetingBenchProbeError, competing_bench_pids
from ..verifier import CAMPAIGN_WAL_SINK, QUALIFICATION_SINK
from ..verifier.commit_receipt import serialize_remote_verification_receipt
from ..verifier.model import capture_compiled_protocol_source_snapshot
from . import pipeline
from .build_admission import (
    BuildAdmission,
    BuildAdmissionError,
    BuildProvenance,
    GeneratorId,
    ReviewId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    validate_build_admission_receipt,
    verify_review_receipt,
)
from .lock import bench_lock
from .model import Genome
from .source_digest import SourceEvidence


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEAD = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_TASK_KEYS = {
    "schema", "campaign_lock_sha256", "variant", "build_attempt_id", "tag",
    "rep", "trace_binary", "trace_bin_sha256", "workload_flags",
    "clocks_per_us", "numactl_prefix", "TRACE_TIMEOUT_S", "genome",
    "source_evidence", "build_admission", "receipt_sink_kind",
    "expected_repo_head", "task_sha256",
}


def _parse_genome(value: object) -> Genome:
    if type(value) is not str or "|" not in value:
        raise ValueError("task genome is not canonical")
    protocol, body = value.split("|", 1)
    if not protocol:
        raise ValueError("task genome is not canonical")
    flags: dict[str, int] = {}
    if body:
        for assignment in body.split(","):
            if "=" not in assignment:
                raise ValueError("task genome is not canonical")
            name, encoded = assignment.split("=", 1)
            if not name or name in flags:
                raise ValueError("task genome is not canonical")
            try:
                flags[name] = int(encoded)
            except ValueError as exc:
                raise ValueError("task genome is not canonical") from exc
    genome = Genome(protocol=protocol, flags=flags)
    if genome.canonical() != value:
        raise ValueError("task genome is not canonical")
    return genome


def _validate_task(value: object) -> tuple[dict, Genome, dict[str, str]]:
    if type(value) is not dict or set(value) != _TASK_KEYS:
        raise ValueError("verify fan-out task key set mismatch")
    task = dict(value)
    unsigned = dict(task)
    task_sha256 = unsigned.pop("task_sha256")
    flags = task["workload_flags"]
    if (task["schema"] != pipeline._VERIFY_FANOUT_TASK_SCHEMA
            or type(task_sha256) is not str
            or _HEX64.fullmatch(task_sha256) is None
            or pipeline._json_sha256(unsigned) != task_sha256
            or type(task["campaign_lock_sha256"]) is not str
            or _HEX64.fullmatch(task["campaign_lock_sha256"]) is None
            or type(task["trace_bin_sha256"]) is not str
            or _HEX64.fullmatch(task["trace_bin_sha256"]) is None
            or type(task["expected_repo_head"]) is not str
            or _HEAD.fullmatch(task["expected_repo_head"]) is None
            or any(type(task[key]) is not str or not task[key]
                   for key in ("variant", "build_attempt_id", "tag"))
            or task["tag"] != pipeline.PERFORMANCE_TAG
            or pipeline._VERIFY_FANOUT_COMPONENT_RE.fullmatch(task["variant"]) is None
            or pipeline._VERIFY_FANOUT_COMPONENT_RE.fullmatch(task["tag"]) is None
            or type(task["rep"]) is not int or isinstance(task["rep"], bool)
            or task["rep"] < 1
            or type(task["trace_binary"]) is not str
            or not os.path.isabs(task["trace_binary"])
            or type(task["clocks_per_us"]) is not int
            or isinstance(task["clocks_per_us"], bool)
            or task["clocks_per_us"] <= 0
            or type(task["TRACE_TIMEOUT_S"]) is not float
            or task["TRACE_TIMEOUT_S"] != pipeline.TRACE_TIMEOUT_S
            or type(task["numactl_prefix"]) is not list
            or any(type(item) is not str or not item
                   for item in task["numactl_prefix"])
            or type(flags) is not list
            or any(type(item) is not list or len(item) != 2
                   or type(item[0]) is not str or not item[0]
                   or type(item[1]) is not str
                   for item in flags)
            or len({item[0] for item in flags}) != len(flags)
            or type(task["source_evidence"]) is not dict
            or type(task["build_admission"]) is not dict
            or task["receipt_sink_kind"] not in {
                CAMPAIGN_WAL_SINK, QUALIFICATION_SINK}):
        raise ValueError("verify fan-out task binding mismatch")
    genome = _parse_genome(task["genome"])
    source = SourceEvidence.from_receipt(task["source_evidence"])
    if (source.genome_sha256
            != hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
            or task["build_admission"].get("source") != task["source_evidence"]):
        raise ValueError("task source/genome/build binding mismatch")
    return task, genome, dict(flags)


def _rehydrate_build_binding(
        task: Mapping[str, object], genome: Genome,
) -> tuple[SourceEvidence, BuildAdmission]:
    """Re-derive the public admission capability and compare its wire body."""
    source = SourceEvidence.from_receipt(task["source_evidence"])
    source._bind_runtime_verification(
        proof_source_snapshot=capture_compiled_protocol_source_snapshot(
            genome.protocol, source.source_root,
        ),
        verification_variant=str(task["variant"]),
    )
    receipt = task["build_admission"]
    provenance = BuildProvenance(receipt["class"])
    generator_id = (
        GeneratorId(receipt["generator_id"])
        if provenance is BuildProvenance.MACHINE_GENERATED
        else GeneratorId.BACKOFF_REPRO
    )
    context = build_run_context(generator_id=generator_id)
    checked = validate_build_admission_receipt(
        receipt, expected_policy=context.policy, expected_source=source,
    )
    generator_receipt = None
    review_receipt = None
    if provenance is BuildProvenance.MACHINE_GENERATED:
        generator_receipt = attest_generator_output(
            context, source,
            generator_input_sha256=checked["input_sha256"],
        )
    elif provenance is BuildProvenance.HUMAN_REVIEWED:
        review_receipt = verify_review_receipt(
            ReviewId(checked["review_id"]), source,
            receipt=checked["review_receipt"],
        )
    elif provenance is BuildProvenance.CODER_AUTHORED:
        raise BuildAdmissionError(
            "remote worker cannot mint coder-authored CLI authority"
        )
    admission = derive_build_admission(
        context, source, generator_receipt=generator_receipt,
        review_receipt=review_receipt,
    )
    if admission.as_wal_receipt() != checked:
        raise BuildAdmissionError("remote build admission re-derivation mismatch")
    return source, admission


def _safe_component(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    cleaned = cleaned.strip(".")
    return cleaned or fallback


def _node_job_root(
        *, environment: Mapping[str, str], scr_root: str = "/scr",
) -> Path:
    user = _safe_component(environment.get("USER", ""), "unknown-user")
    job = _safe_component(environment.get("PBS_JOBID", ""), "no-job")
    if os.path.isdir(scr_root):
        candidate = Path(scr_root) / user / "izanagi-verify-fanout" / job
        try:
            candidate.mkdir(mode=0o700, parents=True, exist_ok=True)
            return candidate
        except OSError:
            pass
    tmpdir = environment.get("TMPDIR") or tempfile.gettempdir()
    candidate = Path(tmpdir) / "izanagi-verify-fanout" / job
    candidate.mkdir(mode=0o700, parents=True, exist_ok=True)
    return candidate


def _copy_binary_exact(
        source_path: str, destination_dir: Path, expected_sha256: str,
) -> tuple[Optional[str], str]:
    destination_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = destination_dir / os.path.basename(source_path)
    source_fd = os.open(
        source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    destination_fd = -1
    source_hash = hashlib.sha256()
    try:
        source_mode = stat.S_IMODE(os.fstat(source_fd).st_mode)
        destination_fd = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            source_mode or 0o700,
        )
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            source_hash.update(chunk)
            offset = 0
            while offset < len(chunk):
                written = os.write(destination_fd, chunk[offset:])
                if written <= 0:
                    raise OSError("short binary copy")
                offset += written
        os.fsync(destination_fd)
    finally:
        os.close(source_fd)
        if destination_fd >= 0:
            os.close(destination_fd)
    observed = source_hash.hexdigest()
    if observed != expected_sha256:
        return None, observed
    local_hasher = hashlib.sha256()
    with destination.open("rb") as copied:
        while True:
            chunk = copied.read(1024 * 1024)
            if not chunk:
                break
            local_hasher.update(chunk)
    local_hash = local_hasher.hexdigest()
    if local_hash != expected_sha256:
        return None, local_hash
    return os.fspath(destination), local_hash


def _result_document(task: Mapping[str, object], outcome: dict) -> dict:
    return {
        "schema": pipeline._VERIFY_FANOUT_RESULT_SCHEMA,
        "task_sha256": task["task_sha256"],
        "build_attempt_id": task["build_attempt_id"],
        "tag": task["tag"],
        "rep": task["rep"],
        "trace_bin_sha256": task["trace_bin_sha256"],
        "outcome": outcome,
    }


def _abort_outcome(
        task: Mapping[str, object], *, reason: str, message: str,
        detail: Optional[dict] = None, verify_payload: Optional[dict] = None,
) -> dict:
    return _result_document(task, {
        "kind": "abort",
        "reason": reason,
        "message": message,
        "detail": dict(detail or {}),
        "workload_tag": task["tag"],
        "verify_payload": verify_payload,
    })


def _repo_head(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run_worker(
        task_path: str, result_path: str, *,
        repo_head_resolver: Optional[Callable[[Path], str]] = None,
        repetition_executor: Optional[Callable[..., object]] = None,
        competing_probe: Optional[Callable[[], list[str]]] = None,
        lock_factory: Optional[Callable[..., object]] = None,
        environment: Optional[Mapping[str, str]] = None,
        scr_root: str = "/scr",
) -> int:
    """Execute one task; a published result means exit zero."""
    env = dict(os.environ if environment is None else environment)
    try:
        task_raw = pipeline._read_exact_json(task_path)
        task, genome, workload_flags = _validate_task(task_raw)
    except Exception as exc:
        print(f"verify fan-out task rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    resolve_head = repo_head_resolver or _repo_head
    try:
        observed_head = resolve_head(repo_root)
    except Exception as exc:
        result = _abort_outcome(
            task, reason="verify-remote-unavailable",
            message="worker repo HEAD を確定できない → reject",
            detail={"worker_error": f"{type(exc).__name__}: {exc}"},
        )
        try:
            pipeline._write_create_only_json(result_path, result)
        except Exception as write_exc:
            print(f"verify fan-out result write failed: {write_exc}", file=sys.stderr)
            return 2
        return 0
    if observed_head != task["expected_repo_head"]:
        result = _abort_outcome(
            task, reason="verify-remote-unavailable",
            message="worker repo HEAD が task と不一致 → reject",
            detail={"worker_error": "repo HEAD mismatch"},
        )
        pipeline._write_create_only_json(result_path, result)
        return 0

    try:
        job_root = _node_job_root(environment=env, scr_root=scr_root)
        task_root = job_root / task["task_sha256"]
        local_binary, observed_sha256 = _copy_binary_exact(
            task["trace_binary"], task_root, task["trace_bin_sha256"],
        )
    except Exception as exc:
        result = _abort_outcome(
            task, reason="verify-remote-unavailable",
            message="trace binary を worker-local に複製できない → reject",
            detail={"worker_error": f"{type(exc).__name__}: {exc}"},
        )
        pipeline._write_create_only_json(result_path, result)
        return 0
    if local_binary is None:
        result = _abort_outcome(
            task, reason="verify-remote-unavailable",
            message="worker-local trace binary sha256 が task と不一致 → reject",
            detail={
                "worker_error": "trace binary sha256 mismatch",
                "expected": task["trace_bin_sha256"],
                "actual": observed_sha256,
            },
        )
        pipeline._write_create_only_json(result_path, result)
        return 0

    previous_lock = os.environ.get("IZANAGI_BENCH_LOCK")
    previous_tmpdir = os.environ.get("TMPDIR")
    try:
        source_evidence, build_admission = _rehydrate_build_binding(task, genome)
        node_tmp = task_root / "tmp"
        node_tmp.mkdir(mode=0o700, exist_ok=True)
        lock_path = job_root / "bench.lock"
        os.environ["IZANAGI_BENCH_LOCK"] = os.fspath(lock_path)
        os.environ["TMPDIR"] = os.fspath(node_tmp)
        acquire_lock = lock_factory or bench_lock
        probe = competing_probe or competing_bench_pids
        execute = repetition_executor or pipeline._execute_verification_repetition
        trace_dir = tempfile.mkdtemp(
            prefix=f"izanagi_eval_trace_{task['tag']}_", dir=node_tmp,
        )
        try:
            with acquire_lock():
                try:
                    competing = probe()
                except CompetingBenchProbeError as exc:
                    result = _abort_outcome(
                        task, reason="verify-probe-error",
                        message=(
                            "競合検知 probe (pgrep) 実行失敗 → S2 相当の "
                            f"verify ({task['tag']}) は競合の有無を確定できず "
                            "reject (環境故障・再評価可能, 規律3/4)"
                        ),
                        detail={"probe_error": exc.as_dict()},
                    )
                else:
                    if competing:
                        result = _abort_outcome(
                            task, reason="verify-competing-tenant",
                            message=(
                                "競合 ccbench ベンチを検知 → S2 相当の "
                                f"verify ({task['tag']}) は汚染計測のまま採用せず "
                                "reject (規律4)"
                            ),
                            detail={"competing": competing},
                        )
                    else:
                        execution = execute(
                            local_binary, trace_dir, workload_flags,
                            task["clocks_per_us"],
                            timeout_s=task["TRACE_TIMEOUT_S"],
                            numactl=tuple(task["numactl_prefix"]),
                            genome=genome,
                            source_evidence=source_evidence,
                            build_admission=build_admission,
                            receipt_sink_kind=task["receipt_sink_kind"],
                            receipt_lock_identity_sha256=(
                                task["campaign_lock_sha256"]
                            ),
                            receipt_variant=task["variant"],
                            receipt_operation_identity=task["build_attempt_id"],
                            receipt_workload_tag=task["tag"],
                            build_attempt_id=task["build_attempt_id"],
                            trace_binary_sha256=task["trace_bin_sha256"],
                            include_qualification_evidence=(
                                task["receipt_sink_kind"] == QUALIFICATION_SINK
                            ),
                            payload_binary=task["trace_binary"],
                        )
                        if execution.abort is not None:
                            abort = execution.abort
                            result = _abort_outcome(
                                task, reason=abort.reason,
                                message=abort.message, detail=abort.detail,
                                verify_payload=execution.verify_payload,
                            )
                        else:
                            remote_receipt = serialize_remote_verification_receipt(
                                execution.verification_capability,
                                task_sha256=task["task_sha256"],
                            )
                            result = _result_document(task, {
                                "kind": "success",
                                "verify_payload": execution.verify_payload,
                                "remote_verification_receipt": remote_receipt,
                            })
        finally:
            shutil.rmtree(trace_dir, ignore_errors=True)
        pipeline._write_create_only_json(result_path, result)
        return 0
    except Exception as exc:
        print(f"verify fan-out worker failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if previous_lock is None:
            os.environ.pop("IZANAGI_BENCH_LOCK", None)
        else:
            os.environ["IZANAGI_BENCH_LOCK"] = previous_lock
        if previous_tmpdir is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = previous_tmpdir


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args(argv)
    return run_worker(args.task, args.result)


if __name__ == "__main__":
    raise SystemExit(main())
