# -*- coding: utf-8 -*-
"""Task-bound sibling-node worker for full-scale correctness repetitions."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


_TASK_SCHEMA = "verify-fanout-task/v1"
_RESULT_SCHEMA = "verify-fanout-result/v1"
_CAMPAIGN_WAL_SINK = "campaign-wal"
_BACKOFF_REPRO = "backoff-repro"
_PERFORMANCE_TAG = "performance"
_TRACE_TIMEOUT_S = 120.0
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEAD = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_TASK_KEYS = {
    "schema", "campaign_lock_sha256", "variant", "build_attempt_id", "tag",
    "rep", "trace_binary", "trace_bin_sha256", "workload_flags",
    "clocks_per_us", "numactl_prefix", "TRACE_TIMEOUT_S", "genome",
    "source_evidence", "proof_source_snapshot", "build_admission",
    "receipt_sink_kind", "generator_id", "expected_repo_head",
    "contract_loader_blob_sha256s", "task_sha256",
}


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _read_exact_json(path: str) -> dict[str, Any]:
    def exact_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read()
            descriptor = -1
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    value = json.loads(raw.decode("ascii"), object_pairs_hook=exact_object)
    if type(value) is not dict or raw != _canonical_json_bytes(value) + b"\n":
        raise ValueError("JSON evidence is not one canonical object")
    return value


def _write_create_only_json(path: str, value: object) -> None:
    encoded = _canonical_json_bytes(value) + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError("short create-only JSON write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(
        os.path.dirname(path) or ".",
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def _parse_genome(value: object):
    from .model import Genome

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


def _validate_task(value: object):
    from .source_digest import (
        SourceEvidence,
        deserialize_compiled_protocol_source_snapshot,
    )

    if type(value) is not dict or set(value) != _TASK_KEYS:
        raise ValueError("verify fan-out task key set mismatch")
    task = dict(value)
    unsigned = dict(task)
    task_sha256 = unsigned.pop("task_sha256")
    flags = task["workload_flags"]
    closure = task["contract_loader_blob_sha256s"]
    if (task["schema"] != _TASK_SCHEMA
            or type(task_sha256) is not str
            or _HEX64.fullmatch(task_sha256) is None
            or _json_sha256(unsigned) != task_sha256
            or type(task["campaign_lock_sha256"]) is not str
            or _HEX64.fullmatch(task["campaign_lock_sha256"]) is None
            or type(task["trace_bin_sha256"]) is not str
            or _HEX64.fullmatch(task["trace_bin_sha256"]) is None
            or type(task["expected_repo_head"]) is not str
            or _HEAD.fullmatch(task["expected_repo_head"]) is None
            or type(closure) is not dict or not closure
            or any(type(path) is not str or not path
                   or type(digest) is not str
                   or _HEX64.fullmatch(digest) is None
                   for path, digest in closure.items())
            or any(type(task[key]) is not str or not task[key]
                   for key in ("variant", "build_attempt_id", "tag"))
            or task["tag"] != _PERFORMANCE_TAG
            or _SAFE_COMPONENT.fullmatch(task["variant"]) is None
            or _SAFE_COMPONENT.fullmatch(task["tag"]) is None
            or type(task["rep"]) is not int or isinstance(task["rep"], bool)
            or task["rep"] < 1
            or type(task["trace_binary"]) is not str
            or not os.path.isabs(task["trace_binary"])
            or type(task["clocks_per_us"]) is not int
            or isinstance(task["clocks_per_us"], bool)
            or task["clocks_per_us"] <= 0
            or type(task["TRACE_TIMEOUT_S"]) is not float
            or task["TRACE_TIMEOUT_S"] != _TRACE_TIMEOUT_S
            or type(task["numactl_prefix"]) is not list
            or any(type(item) is not str or not item
                   for item in task["numactl_prefix"])
            or type(flags) is not list
            or any(type(item) is not list or len(item) != 2
                   or type(item[0]) is not str or not item[0]
                   or type(item[1]) is not str for item in flags)
            or len({item[0] for item in flags}) != len(flags)
            or type(task["source_evidence"]) is not dict
            or type(task["proof_source_snapshot"]) is not dict
            or type(task["build_admission"]) is not dict
            or task["receipt_sink_kind"] != _CAMPAIGN_WAL_SINK
            or task["generator_id"] != _BACKOFF_REPRO):
        raise ValueError("verify fan-out task binding mismatch")
    genome = _parse_genome(task["genome"])
    source = SourceEvidence.from_receipt(task["source_evidence"])
    snapshot = deserialize_compiled_protocol_source_snapshot(
        task["proof_source_snapshot"]
    )
    if (source.genome_sha256
            != hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
            or task["build_admission"].get("source") != task["source_evidence"]
            or snapshot.protocol != genome.protocol
            or snapshot.ccbench_root != source.source_root):
        raise ValueError("task source/genome/build binding mismatch")
    return task, genome, dict(flags), snapshot


def _validate_enforcement_closure(
        task: Mapping[str, object], *, binding_resolver=None,
):
    from .contract_loader_binding import capture_contract_loader_binding

    resolve = binding_resolver or capture_contract_loader_binding
    binding = resolve()
    if (task.get("expected_repo_head") != binding.contract_loader_commit
            or task.get("contract_loader_blob_sha256s")
            != dict(binding.contract_loader_blob_sha256s)):
        raise ValueError("worker enforcement closure mismatch")
    return binding


def _rehydrate_build_binding(task, genome, proof_source_snapshot):
    """Re-derive only BACKOFF_REPRO/stock admission from the carried snapshot."""
    from .build_admission import (
        BuildAdmissionError,
        BuildProvenance,
        GeneratorId,
        attest_generator_output,
        build_run_context,
        derive_build_admission,
        validate_build_admission_receipt,
    )
    from .source_digest import SourceEvidence

    source = SourceEvidence.from_receipt(task["source_evidence"])
    source._bind_runtime_verification(
        proof_source_snapshot=proof_source_snapshot,
        verification_variant=str(task["variant"]),
    )
    receipt = task["build_admission"]
    provenance = BuildProvenance(receipt["class"])
    if provenance not in {
            BuildProvenance.STOCK_BASELINE,
            BuildProvenance.MACHINE_GENERATED}:
        raise BuildAdmissionError(
            "remote worker accepts only BACKOFF_REPRO generated or stock source"
        )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_REPRO)
    checked = validate_build_admission_receipt(
        receipt, expected_policy=context.policy, expected_source=source,
    )
    generator_receipt = None
    if provenance is BuildProvenance.MACHINE_GENERATED:
        if checked.get("generator_id") != GeneratorId.BACKOFF_REPRO.value:
            raise BuildAdmissionError("remote build generator is not BACKOFF_REPRO")
        generator_receipt = attest_generator_output(
            context, source,
            generator_input_sha256=checked["input_sha256"],
        )
    admission = derive_build_admission(
        context, source, generator_receipt=generator_receipt,
    )
    if admission.as_wal_receipt() != checked:
        raise BuildAdmissionError("remote build admission re-derivation mismatch")
    return source, admission


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", value).strip(".")
    if not cleaned:
        raise ValueError("empty scheduler path component")
    return cleaned


def _node_job_root(
        *, environment: Mapping[str, str], scr_root: str = "/scr",
) -> Path:
    user_raw = environment.get("USER")
    job_raw = environment.get("PBS_JOBID")
    if type(user_raw) is not str or not user_raw:
        raise ValueError("USER is required for worker-local root")
    if type(job_raw) is not str or not job_raw:
        raise ValueError("PBS_JOBID is required for worker-local root")
    if type(scr_root) is not str or not os.path.isdir(scr_root):
        raise OSError("node-local /scr root is unavailable")
    candidate = (
        Path(scr_root) / _safe_component(user_raw)
        / "izanagi-verify-fanout" / _safe_component(job_raw)
    )
    candidate.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not candidate.is_dir():
        raise OSError("node-local worker root is not a directory")
    return candidate


def _copy_binary_exact(
        source_path: str, destination_dir: Path, expected_sha256: str, *,
        post_copy_hook: Optional[Callable[[Path], None]] = None,
) -> tuple[Optional[str], str]:
    destination_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = destination_dir / os.path.basename(source_path)
    source_fd = os.open(source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
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
    if post_copy_hook is not None:
        post_copy_hook(destination)
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


def _result_document(
        task: Mapping[str, object], outcome: dict, result_secret: bytes,
) -> dict:
    unsigned = {
        "schema": _RESULT_SCHEMA,
        "task_sha256": task["task_sha256"],
        "build_attempt_id": task["build_attempt_id"],
        "tag": task["tag"],
        "rep": task["rep"],
        "trace_bin_sha256": task["trace_bin_sha256"],
        "outcome": outcome,
    }
    return {
        **unsigned,
        "result_mac": hmac.new(
            result_secret, _canonical_json_bytes(unsigned), hashlib.sha256,
        ).hexdigest(),
    }


def _abort_outcome(
        task: Mapping[str, object], *, result_secret: bytes,
        reason: str, message: str, detail: Optional[dict] = None,
        verify_payload: Optional[dict] = None,
) -> dict:
    return _result_document(task, {
        "kind": "abort", "reason": reason, "message": message,
        "detail": dict(detail or {}), "workload_tag": task["tag"],
        "verify_payload": verify_payload,
    }, result_secret)


def _repo_head(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run_worker(
        task_path: str, result_path: str, *, result_secret: bytes,
        contract_loader_binding_resolver=None,
        repo_head_resolver: Optional[Callable[[Path], str]] = None,
        repetition_executor: Optional[Callable[..., object]] = None,
        competing_probe: Optional[Callable[[], list[str]]] = None,
        lock_factory: Optional[Callable[..., object]] = None,
        environment: Optional[Mapping[str, str]] = None,
        scr_root: str = "/scr",
        post_copy_hook: Optional[Callable[[Path], None]] = None,
) -> int:
    """Execute one authenticated task; a published result means exit zero."""
    if type(result_secret) is not bytes or len(result_secret) != 32:
        print("verify fan-out result secret is absent or malformed", file=sys.stderr)
        return 2
    try:
        task_raw = _read_exact_json(task_path)
        _validate_enforcement_closure(
            task_raw, binding_resolver=contract_loader_binding_resolver,
        )
    except Exception as exc:
        print(
            f"verify fan-out closure rejected: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    try:
        task, genome, workload_flags, proof_snapshot = _validate_task(task_raw)
    except Exception as exc:
        print(f"verify fan-out task rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    env = dict(os.environ if environment is None else environment)
    try:
        job_root = _node_job_root(environment=env, scr_root=scr_root)
    except Exception as exc:
        print(
            f"verify fan-out node-local root rejected: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    task_root = job_root / task["task_sha256"]
    try:
        task_root.mkdir(mode=0o700, exist_ok=False)
    except Exception as exc:
        print(
            f"verify fan-out task root rejected: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    previous_lock = os.environ.get("IZANAGI_BENCH_LOCK")
    previous_tmpdir = os.environ.get("TMPDIR")
    try:
        from ..calibrator.runner import CompetingBenchProbeError, competing_bench_pids
        from ..verifier.commit_receipt import serialize_remote_verification_receipt
        from . import pipeline
        from .lock import bench_lock

        repo_root = Path(__file__).resolve().parents[2]
        resolve_head = repo_head_resolver or _repo_head
        try:
            observed_head = resolve_head(repo_root)
        except Exception as exc:
            result = _abort_outcome(
                task, result_secret=result_secret,
                reason="verify-remote-unavailable",
                message="worker repo HEAD を確定できない → reject",
                detail={"worker_error": f"{type(exc).__name__}: {exc}"},
            )
            _write_create_only_json(result_path, result)
            return 0
        if observed_head != task["expected_repo_head"]:
            result = _abort_outcome(
                task, result_secret=result_secret,
                reason="verify-remote-unavailable",
                message="worker repo HEAD が task と不一致 → reject",
                detail={"worker_error": "repo HEAD mismatch"},
            )
            _write_create_only_json(result_path, result)
            return 0

        try:
            local_binary, observed_sha256 = _copy_binary_exact(
                task["trace_binary"], task_root, task["trace_bin_sha256"],
                post_copy_hook=post_copy_hook,
            )
        except Exception as exc:
            result = _abort_outcome(
                task, result_secret=result_secret,
                reason="verify-remote-unavailable",
                message="trace binary を worker-local に複製できない → reject",
                detail={"worker_error": f"{type(exc).__name__}: {exc}"},
            )
            _write_create_only_json(result_path, result)
            return 0
        if local_binary is None:
            result = _abort_outcome(
                task, result_secret=result_secret,
                reason="verify-remote-unavailable",
                message="worker-local trace binary sha256 が task と不一致 → reject",
                detail={
                    "worker_error": "trace binary sha256 mismatch",
                    "expected": task["trace_bin_sha256"],
                    "actual": observed_sha256,
                },
            )
            _write_create_only_json(result_path, result)
            return 0

        source_evidence, build_admission = _rehydrate_build_binding(
            task, genome, proof_snapshot,
        )
        node_tmp = task_root / "tmp"
        node_tmp.mkdir(mode=0o700, exist_ok=True)
        lock_path = task_root / "bench.lock"
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
                        task, result_secret=result_secret,
                        reason="verify-probe-error",
                        message=(
                            "競合検知 probe (pgrep) 実行失敗 → S2 相当の "
                            f"verify ({task['tag']}) は競合の有無を確定できず "
                            "reject (環境故障・再評価可能, 規律3/4)"
                        ), detail={"probe_error": exc.as_dict()},
                    )
                else:
                    if competing:
                        result = _abort_outcome(
                            task, result_secret=result_secret,
                            reason="verify-competing-tenant",
                            message=(
                                "競合 ccbench ベンチを検知 → S2 相当の "
                                f"verify ({task['tag']}) は汚染計測のまま採用せず "
                                "reject (規律4)"
                            ), detail={"competing": competing},
                        )
                    else:
                        execution = execute(
                            local_binary, trace_dir, workload_flags,
                            task["clocks_per_us"],
                            timeout_s=task["TRACE_TIMEOUT_S"],
                            numactl=tuple(task["numactl_prefix"]),
                            genome=genome, source_evidence=source_evidence,
                            build_admission=build_admission,
                            receipt_sink_kind=task["receipt_sink_kind"],
                            receipt_lock_identity_sha256=task["campaign_lock_sha256"],
                            receipt_variant=task["variant"],
                            receipt_operation_identity=task["build_attempt_id"],
                            receipt_workload_tag=task["tag"],
                            build_attempt_id=task["build_attempt_id"],
                            trace_binary_sha256=task["trace_bin_sha256"],
                            include_qualification_evidence=False,
                            payload_binary=task["trace_binary"],
                        )
                        if execution.abort is not None:
                            abort = execution.abort
                            result = _abort_outcome(
                                task, result_secret=result_secret,
                                reason=abort.reason, message=abort.message,
                                detail=abort.detail,
                                verify_payload=execution.verify_payload,
                            )
                        else:
                            verify_payload = execution.verify_payload
                            remote_receipt = serialize_remote_verification_receipt(
                                execution.verification_capability,
                                task_sha256=task["task_sha256"],
                                verify_payload_sha256=_json_sha256(verify_payload),
                            )
                            result = _result_document(task, {
                                "kind": "success",
                                "verify_payload": verify_payload,
                                "remote_verification_receipt": remote_receipt,
                            }, result_secret)
        finally:
            shutil.rmtree(trace_dir, ignore_errors=True)
        _write_create_only_json(result_path, result)
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
        shutil.rmtree(task_root, ignore_errors=True)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args(argv)
    result_secret = sys.stdin.buffer.read()
    if len(result_secret) != 32:
        print("verify fan-out result secret is absent or malformed", file=sys.stderr)
        return 2
    return run_worker(args.task, args.result, result_secret=result_secret)


if __name__ == "__main__":
    raise SystemExit(main())
