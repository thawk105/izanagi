#!/usr/bin/env python3
"""Fail-closed pairing gate for independent Mocc TRACE=1/TRACE=0 pilots."""
from __future__ import annotations

import argparse
import base64
import binascii
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import contract_loader_binding  # noqa: E402


PAIR_SCHEMA = "mocc-trace-pair-receipt/v3"
PILOT_SCHEMA = "mocc-trace-pilot-receipt/v4"
JOB_RESULT_SCHEMA = "mocc-trace-pilot-job-result/v2"
THROUGHPUT_SCHEMA = "mocc-trace-throughput/v1"
COUNTER_SCHEMA = "mocc-commit-counter-witness/v1"
SOURCE_CAPTURE_SCHEMA = "mocc-trace-judgment-source-capture/v1"
CHECKER_REPO_PATH = "orchestrator/campaign/mocc_trace_pair.py"
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_JOB_ID = re.compile(r"(?:0:)?[A-Za-z0-9._-]+\Z")
_TRACE1_PERFORMANCE_KEYS = frozenset(
    {
        "completed_txns",
        "elapsed_ns",
        "elapsed_s",
        "throughput_txns_per_s",
        "average_latency_s",
        "average_latency_us",
        "measurement_role",
    }
)
_TRACE0_VERDICT_KEYS = frozenset(
    {"verdict", "verifier_verdict", "certified_serializable", "anomaly_count"}
)


class PairValidationError(ValueError):
    """An input cannot be certified as a Mocc trace pair."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PairValidationError(message)


@dataclass(frozen=True)
class InputDocument:
    path: Path
    raw: bytes
    sha256: str
    value: dict[str, Any]


@dataclass(frozen=True)
class ValidatedLeg:
    mode: int
    normalized_jobid: str
    receipt: InputDocument
    job_result: InputDocument
    mode_evidence: InputDocument
    counter_witness: InputDocument
    source_captures: tuple[InputDocument, InputDocument]
    identity_evidence: InputDocument | None
    outer_commit: str
    base_oid: str
    new_oid: str
    cmake_target: str
    workload: dict[str, Any]
    projection: dict[str, Any]
    job_script_sha256: str
    compiler_version: str
    binary_sha256: str
    build_dir: str
    binary_path: str
    attempt_dir: str
    run_dir: str
    tool: dict[str, str]
    throughput: float | None
    output: dict[str, Any]


@dataclass(frozen=True)
class CheckerSourceBinding:
    expected_commit: str
    expected_sha256: str
    git_blob_oid: str
    git_blob_sha256: str
    live_sha256: str


def _reject(message: str) -> None:
    raise PairValidationError(message)


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _reject(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _reject(f"non-finite JSON number is forbidden: {value}")


def _read_json(path_text: str, label: str) -> InputDocument:
    path = Path(path_text)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise PairValidationError(f"{label} is unavailable: {path}") from exc
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            _reject(f"{label} is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
    finally:
        if fd >= 0:
            os.close(fd)
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise PairValidationError(f"{label} is not UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise PairValidationError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        _reject(f"{label} top level is not an object")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise PairValidationError(f"{label} path cannot be resolved") from exc
    return InputDocument(
        path=resolved,
        raw=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        value=value,
    )


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _reject(f"{label} is not an object")
    return value


def _string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        _reject(f"{label} is not a valid string")
    return value


def _integer(value: Any, label: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        _reject(f"{label} is not a valid integer")
    return value


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        _reject(f"{label} is not a number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        _reject(f"{label} is not a positive finite number")
    return result


def _sha256(value: Any, label: str) -> str:
    value = _string(value, label)
    if _HEX64.fullmatch(value) is None:
        _reject(f"{label} is not a lowercase SHA-256")
    return value


def _oid(value: Any, label: str) -> str:
    value = _string(value, label)
    if _HEX40.fullmatch(value) is None:
        _reject(f"{label} is not a full lowercase OID")
    return value


def _false(value: Any, label: str) -> None:
    if type(value) is not bool or value is not False:
        _reject(f"{label} is not strict false")


def _true(value: Any, label: str) -> None:
    if type(value) is not bool or value is not True:
        _reject(f"{label} is not strict true")


def _path_string(value: Any, label: str) -> str:
    value = _string(value, label)
    if not os.path.isabs(value):
        _reject(f"{label} is not absolute")
    return value


def _nested_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        found.update(value)
        for child in value.values():
            found.update(_nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_nested_keys(child))
    return found


def _strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            _strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return bool(left == right)


def _normalize_jobid(value: Any, label: str) -> tuple[str, str]:
    raw = _string(value, label)
    if _JOB_ID.fullmatch(raw) is None:
        _reject(f"{label} is unsafe")
    return raw, raw[2:] if raw.startswith("0:") else raw


def _validate_tool(value: Any, label: str) -> dict[str, str]:
    tool = _dict(value, label)
    if set(tool) != {"path", "sha256"}:
        _reject(f"{label} fields differ")
    return {
        "path": _path_string(tool.get("path"), f"{label}.path"),
        "sha256": _sha256(tool.get("sha256"), f"{label}.sha256"),
    }


def _validate_counter_witness(
    receipt_doc: InputDocument,
    counter_doc: InputDocument,
    index: int,
) -> int:
    artifacts = _dict(receipt_doc.value.get("artifacts"), "artifacts")
    if artifacts.get("commit_count_json") != "commit-count.json":
        _reject("commit counter witness artifact path differs")
    if counter_doc.path.name != artifacts["commit_count_json"]:
        _reject(f"leg {index} commit counter witness input path differs")
    if artifacts.get("commit_count_sha256") != counter_doc.sha256:
        _reject("commit counter witness bytes do not match the pilot receipt")
    witness = counter_doc.value
    if witness.get("schema_version") != COUNTER_SCHEMA:
        _reject("commit counter witness schema differs")
    count = _integer(witness.get("count"), "commit counter witness count", minimum=0)
    return count


def _validate_source_capture(
    capture_doc: InputDocument,
    binding: dict[str, Any],
    *,
    phase: str,
    short_phase: str,
    outer_commit: str,
    index: int,
) -> dict[str, Any]:
    expected_name = f"judgment-source-{short_phase}.json"
    if set(binding) != {"capture_path", "capture_sha256", "head", "clean"}:
        _reject(f"{phase} receipt source capture binding fields differ")
    if binding.get("capture_path") != expected_name:
        _reject(f"{phase} receipt source capture path differs")
    if capture_doc.path.name != expected_name:
        _reject(f"leg {index} {phase} source capture input path differs")
    if binding.get("capture_sha256") != capture_doc.sha256:
        _reject(f"{phase} source capture bytes do not match the pilot receipt")

    capture = capture_doc.value
    if set(capture) != {
        "schema_version",
        "capture_phase",
        "capture_ok",
        "head",
        "clean",
        "pathspec",
        "status_format",
        "status_bytes_base64",
        "command_rc",
    }:
        _reject(f"{phase} source capture shape differs")
    if capture.get("schema_version") != SOURCE_CAPTURE_SCHEMA:
        _reject(f"{phase} source capture schema differs")
    if capture.get("capture_phase") != phase:
        _reject(f"{phase} source capture phase differs")
    _true(capture.get("capture_ok"), f"{phase} source capture capture_ok")
    head = _oid(capture.get("head"), f"{phase} source capture HEAD")
    if head != outer_commit:
        _reject(f"{phase} source capture HEAD differs from outer commit")
    _true(capture.get("clean"), f"{phase} source capture clean")
    if capture.get("pathspec") != [".", ":(exclude)output"]:
        _reject(f"{phase} source capture pathspec differs")
    if (
        capture.get("status_format")
        != "git status --porcelain=v1 -z --untracked-files=all"
    ):
        _reject(f"{phase} source capture status format differs")
    encoded_status = capture.get("status_bytes_base64")
    if not isinstance(encoded_status, str):
        _reject(f"{phase} source capture status bytes are not encoded text")
    try:
        status_bytes = base64.b64decode(encoded_status, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise PairValidationError(
            f"{phase} source capture status bytes are not valid base64"
        ) from exc
    if status_bytes != b"":
        _reject(f"{phase} source capture status bytes are dirty")
    if capture.get("command_rc") != {"head": 0, "status": 0}:
        _reject(f"{phase} source capture command rc differs")
    if binding.get("head") != head:
        _reject(f"{phase} receipt source capture HEAD binding differs")
    _true(binding.get("clean"), f"{phase} receipt source capture clean")
    return {
        "capture_path": expected_name,
        "capture_sha256": capture_doc.sha256,
        "head": head,
        "clean": True,
    }


def _validate_source_captures(
    receipt_doc: InputDocument,
    pre_doc: InputDocument,
    post_doc: InputDocument,
    outer_commit: str,
    index: int,
) -> dict[str, Any]:
    source = _dict(receipt_doc.value.get("source"), "source")
    state = _dict(source.get("judgment_source_state"), "judgment_source_state")
    if set(state) != {
        "guarantee_name",
        "pre",
        "post",
        "head_unchanged",
        "residual_windows",
    }:
        _reject("judgment source state fields differ")
    if state.get("guarantee_name") != "pre/post endpoint consistency":
        _reject("judgment source state guarantee differs")
    _true(state.get("head_unchanged"), "judgment source state head_unchanged")
    if state.get("residual_windows") != [
        "temporary source changes between captures can be missed",
        "source changes after the post_judgment capture can be missed",
    ]:
        _reject("judgment source state residual windows differ")
    pre = _validate_source_capture(
        pre_doc,
        _dict(state.get("pre"), "judgment_source_state.pre"),
        phase="pre_judgment",
        short_phase="pre",
        outer_commit=outer_commit,
        index=index,
    )
    post = _validate_source_capture(
        post_doc,
        _dict(state.get("post"), "judgment_source_state.post"),
        phase="post_judgment",
        short_phase="post",
        outer_commit=outer_commit,
        index=index,
    )
    if pre["head"] != post["head"]:
        _reject("judgment source capture HEAD changed")
    return {"guarantee_name": state["guarantee_name"], "pre": pre, "post": post}


def _validate_common(
    receipt_doc: InputDocument, job_doc: InputDocument
) -> dict[str, Any]:
    receipt = receipt_doc.value
    job = job_doc.value
    if receipt.get("schema_version") != PILOT_SCHEMA:
        _reject("pilot receipt schema differs")
    if receipt.get("status") != "completed" or receipt.get("pilot") is not True:
        _reject("pilot receipt is not a strict completed pilot")
    _false(receipt.get("official_certification"), "official_certification")
    _false(receipt.get("eligible_for_refreeze"), "eligible_for_refreeze")
    if job.get("schema_version") != JOB_RESULT_SCHEMA:
        _reject("job-result schema differs")
    if job.get("receipt_sha256") != receipt_doc.sha256:
        _reject("job-result does not bind exact receipt bytes")

    mocc = _dict(receipt.get("mocc_trace"), "mocc_trace")
    build = _dict(receipt.get("build"), "build")
    source = _dict(receipt.get("source"), "source")
    workload = _dict(receipt.get("workload"), "workload")
    mode = _integer(mocc.get("trace_mode"), "mocc_trace.trace_mode")
    build_mode = _integer(build.get("trace_mode"), "build.trace_mode")
    if mode not in (0, 1) or build_mode != mode:
        _reject("receipt trace mode paths disagree")

    raw_jobid, normalized_jobid = _normalize_jobid(
        _dict(receipt.get("pbs"), "pbs").get("jobid"), "pbs.jobid"
    )
    job_raw, job_normalized = _normalize_jobid(job.get("pbs_jobid"), "job pbs_jobid")
    if raw_jobid != job_raw or normalized_jobid != job_normalized:
        _reject("job-result job ID does not bind the receipt")

    binary_sha = _sha256(build.get("binary_sha256"), "build.binary_sha256")
    if job.get("binary_sha256") != binary_sha:
        _reject("job-result binary SHA does not bind the receipt")
    job_script_sha = _sha256(job.get("job_script_sha256"), "job_script_sha256")

    new_oid = _oid(mocc.get("new_oid"), "mocc_trace.new_oid")
    base_oid = _oid(mocc.get("base_oid"), "mocc_trace.base_oid")
    target = _string(mocc.get("cmake_target"), "mocc_trace.cmake_target")
    source_binding = _dict(mocc.get("source_binding"), "mocc_trace.source_binding")
    if not (
        source_binding.get("new_oid") == new_oid
        and source.get("submodule_new_oid") == new_oid
        and source_binding.get("base_oid") == base_oid
        and source.get("submodule_base_oid") == base_oid
        and source_binding.get("cmake_target") == target
        and build.get("cmake_target") == target
    ):
        _reject("receipt source/target bindings disagree")
    mocc_workload = _dict(mocc.get("workload"), "mocc_trace.workload")
    workload_config = _dict(workload.get("config"), "workload.config")
    if not _strict_equal(mocc_workload, workload_config):
        _reject("receipt workload bindings disagree")

    report = _dict(
        receipt.get("trace0_preprocess_identity_report"),
        "trace0_preprocess_identity_report",
    )
    if set(report) != {"path", "sha256", "schema", "guarantee"}:
        _reject("identity report binding fields differ")
    if not _strict_equal(job.get("trace0_preprocess_identity_report"), report):
        _reject("job-result identity report binding differs")

    compiler = _dict(
        _dict(receipt.get("environment"), "environment").get("compiler"),
        "environment.compiler",
    )
    projection = dict(mocc)
    projection.pop("trace_mode", None)
    return {
        "mode": mode,
        "raw_jobid": raw_jobid,
        "normalized_jobid": normalized_jobid,
        "outer_commit": _oid(source.get("outer_repo_commit"), "outer_repo_commit"),
        "base_oid": base_oid,
        "new_oid": new_oid,
        "target": target,
        "workload": mocc_workload,
        "projection": projection,
        "job_script_sha": job_script_sha,
        "compiler_version": _string(compiler.get("version"), "compiler.version"),
        "binary_sha": binary_sha,
        "build_dir": _path_string(build.get("build_dir"), "build.build_dir"),
        "binary_path": _path_string(build.get("binary"), "build.binary"),
        "attempt_dir": _path_string(
            _dict(receipt.get("artifacts"), "artifacts").get("attempt_dir"),
            "artifacts.attempt_dir",
        ),
        "run_dir": _path_string(
            _dict(receipt.get("artifacts"), "artifacts").get("run_dir"),
            "artifacts.run_dir",
        ),
        "report": report,
    }


def _validate_trace1(
    receipt_doc: InputDocument,
    evidence: InputDocument,
    counter_count: int,
    common: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    receipt = receipt_doc.value
    artifacts = _dict(receipt.get("artifacts"), "artifacts")
    gates = _dict(receipt.get("gates"), "gates")
    environment = _dict(receipt.get("environment"), "environment")
    tools = _dict(receipt.get("correctness_tools"), "correctness_tools")
    report = common["report"]
    if artifacts.get("throughput_json") is not None:
        _reject("TRACE=1 throughput artifact reference must be null")
    if artifacts.get("throughput_sha256") is not None:
        _reject("TRACE=1 throughput SHA must be null")
    if artifacts.get("verifier_json") != "verifier.json":
        _reject("TRACE=1 verifier artifact reference differs")
    if artifacts.get("verifier_sha256") != evidence.sha256:
        _reject("TRACE=1 verifier bytes do not match the pilot receipt")
    if gates.get("workload_rc") != "0" or gates.get("verifier_rc") != "0":
        _reject("TRACE=1 workload/verifier gate did not succeed")
    if gates.get("trace0_preprocess_identity_rc") != "not-run":
        _reject("TRACE=1 identity checker gate must be not-run")
    if environment.get("trace0_preprocess_identity_checker_interpreter_path") is not None:
        _reject("TRACE=1 selected an identity checker interpreter")
    if not isinstance(environment.get("verifier_interpreter_path"), str):
        _reject("TRACE=1 verifier interpreter is absent")
    if any(value is not None for value in report.values()):
        _reject("TRACE=1 identity report binding must be null")
    if _nested_keys(receipt) & _TRACE1_PERFORMANCE_KEYS:
        _reject("TRACE=1 receipt contains an inline performance field")

    verifier = evidence.value
    results = verifier.get("results")
    result = results[0] if isinstance(results, list) and len(results) == 1 else None
    integrity = result.get("integrity") if isinstance(result, dict) else None
    stats = result.get("stats") if isinstance(result, dict) else None
    if (
        not isinstance(stats, dict)
        or type(stats.get("txns")) is not int
        or stats.get("txns") != counter_count
    ):
        _reject("TRACE=1 verifier transaction count differs from counter witness")
    certified = (
        type(verifier.get("runs")) is int
        and verifier.get("runs") == 1
        and type(verifier.get("certified_serializable")) is int
        and verifier.get("certified_serializable") == 1
        and type(verifier.get("non_serializable")) is int
        and verifier.get("non_serializable") == 0
        and type(verifier.get("indeterminate")) is int
        and verifier.get("indeterminate") == 0
        and isinstance(result, dict)
        and result.get("certified") is True
        and result.get("verdict") == "serializable"
        and type(result.get("anomaly_count")) is int
        and result.get("anomaly_count") == 0
        and result.get("anomalies") == []
        and isinstance(integrity, dict)
        and integrity.get("clean") is True
        and result.get("trace_dir") == artifacts.get("trace_dir")
    )
    if not certified:
        _reject("TRACE=1 verifier certified/anomaly/integrity predicate failed")
    if set(tools) != {"trace0_preprocess_identity_checker", "verifier"}:
        _reject("TRACE=1 correctness tool fields differ")
    if tools.get("trace0_preprocess_identity_checker") is not None:
        _reject("TRACE=1 identity checker tool must be null")
    tool = _validate_tool(tools.get("verifier"), "correctness_tools.verifier")
    return (
        {
            "certified_serializable": True,
            "anomaly_count": 0,
            "integrity_clean": True,
            "tool": {"kind": "verifier", **tool},
        },
        tool,
    )


def _validate_trace0(
    receipt_doc: InputDocument,
    evidence: InputDocument,
    identity_evidence: InputDocument,
    counter_count: int,
    common: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str], float]:
    receipt = receipt_doc.value
    artifacts = _dict(receipt.get("artifacts"), "artifacts")
    gates = _dict(receipt.get("gates"), "gates")
    environment = _dict(receipt.get("environment"), "environment")
    tools = _dict(receipt.get("correctness_tools"), "correctness_tools")
    report = common["report"]
    if artifacts.get("verifier_json") is not None:
        _reject("TRACE=0 verifier artifact reference must be null")
    if artifacts.get("verifier_sha256") is not None:
        _reject("TRACE=0 verifier SHA must be null")
    if artifacts.get("throughput_json") != "throughput.json":
        _reject("TRACE=0 throughput artifact reference differs")
    if artifacts.get("throughput_sha256") != evidence.sha256:
        _reject("TRACE=0 throughput bytes do not match the pilot receipt")
    if gates.get("workload_rc") != "0" or gates.get("verifier_rc") != "not-run":
        _reject("TRACE=0 workload/verifier separation gate differs")
    if gates.get("trace0_preprocess_identity_rc") != "0":
        _reject("TRACE=0 identity checker gate did not succeed")
    if environment.get("verifier_interpreter_path") is not None:
        _reject("TRACE=0 selected a verifier interpreter")
    if not isinstance(
        environment.get("trace0_preprocess_identity_checker_interpreter_path"), str
    ):
        _reject("TRACE=0 identity checker interpreter is absent")
    if _nested_keys(receipt) & _TRACE0_VERDICT_KEYS:
        _reject("TRACE=0 receipt contains an inline verifier verdict")
    if report.get("path") != "trace0-preprocess-identity.json":
        _reject("TRACE=0 identity report path differs")
    if report.get("sha256") != identity_evidence.sha256:
        _reject("TRACE=0 identity report bytes do not match the pilot receipt")
    if not isinstance(report.get("schema"), str) or not report["schema"].startswith(
        "izanagi-trace0-preprocess-identity/"
    ):
        _reject("TRACE=0 identity report schema differs")
    if not isinstance(report.get("guarantee"), str) or not report["guarantee"].strip():
        _reject("TRACE=0 identity report guarantee is empty")

    throughput = evidence.value
    if throughput.get("schema_version") != THROUGHPUT_SCHEMA:
        _reject("TRACE=0 throughput schema differs")
    if throughput.get("measurement_role") != "pilot-only; not official calibration":
        _reject("TRACE=0 throughput measurement role differs")
    completed = _integer(throughput.get("completed_txns"), "throughput.completed_txns", minimum=1)
    elapsed_ns = _integer(throughput.get("elapsed_ns"), "throughput.elapsed_ns", minimum=1)
    elapsed_s = _number(throughput.get("elapsed_s"), "throughput.elapsed_s", positive=True)
    rate = _number(
        throughput.get("throughput_txns_per_s"),
        "throughput.throughput_txns_per_s",
        positive=True,
    )
    latency_s = _number(
        throughput.get("average_latency_s"), "throughput.average_latency_s", positive=True
    )
    latency_us = _number(
        throughput.get("average_latency_us"), "throughput.average_latency_us", positive=True
    )
    workload = _dict(receipt.get("workload"), "workload")
    receipt_completed = _integer(
        workload.get("completed_txns"), "workload.completed_txns", minimum=1
    )
    receipt_elapsed_ns = _integer(
        workload.get("elapsed_ns"), "workload.elapsed_ns", minimum=1
    )
    receipt_elapsed_s = _number(
        workload.get("elapsed_s"), "workload.elapsed_s", positive=True
    )
    if not (
        receipt_completed == completed
        and completed == counter_count
        and receipt_elapsed_ns == elapsed_ns
        and receipt_elapsed_s == elapsed_s
    ):
        _reject("TRACE=0 throughput evidence does not bind receipt counters")
    recomputed_elapsed_s = elapsed_ns / 1_000_000_000
    recomputed_rate = completed / recomputed_elapsed_s
    recomputed_latency_s = recomputed_elapsed_s / completed
    if not (
        math.isclose(elapsed_s, recomputed_elapsed_s, rel_tol=1e-12, abs_tol=0.0)
        and math.isclose(rate, recomputed_rate, rel_tol=1e-12, abs_tol=0.0)
        and math.isclose(latency_s, recomputed_latency_s, rel_tol=1e-12, abs_tol=0.0)
        and math.isclose(latency_us, recomputed_latency_s * 1_000_000, rel_tol=1e-12, abs_tol=0.0)
    ):
        _reject("TRACE=0 throughput metrics do not recompute")
    if set(tools) != {"trace0_preprocess_identity_checker", "verifier"}:
        _reject("TRACE=0 correctness tool fields differ")
    if tools.get("verifier") is not None:
        _reject("TRACE=0 verifier tool must be null")
    tool = _validate_tool(
        tools.get("trace0_preprocess_identity_checker"),
        "correctness_tools.trace0_preprocess_identity_checker",
    )
    return (
        {
            "throughput_txns_per_s": rate,
            "measurement_role": "pilot-only; not official calibration",
            "identity_report": {
                "path": str(identity_evidence.path),
                "sha256": identity_evidence.sha256,
            },
            "tool": {"kind": "trace0-preprocess-identity-checker", **tool},
        },
        tool,
        rate,
    )


def validate_leg(parts: Sequence[str], index: int) -> ValidatedLeg:
    if len(parts) not in (6, 7):
        _reject(f"leg {index} must contain six fields for TRACE=1 or seven for TRACE=0")
    receipt_doc = _read_json(parts[0], f"leg {index} receipt")
    job_doc = _read_json(parts[1], f"leg {index} job-result")
    evidence = _read_json(parts[2], f"leg {index} mode evidence")
    common = _validate_common(receipt_doc, job_doc)
    mode = common["mode"]
    if mode == 1:
        if len(parts) != 6:
            _reject(f"TRACE=1 leg {index} must not provide identity evidence")
        counter_index, pre_index, post_index = 3, 4, 5
        identity_evidence = None
    else:
        if len(parts) != 7:
            _reject(f"TRACE=0 leg {index} must provide identity evidence")
        identity_evidence = _read_json(parts[3], f"leg {index} identity evidence")
        counter_index, pre_index, post_index = 4, 5, 6
    counter_witness = _read_json(
        parts[counter_index], f"leg {index} commit counter witness"
    )
    pre_capture = _read_json(
        parts[pre_index], f"leg {index} pre_judgment source capture"
    )
    post_capture = _read_json(
        parts[post_index], f"leg {index} post_judgment source capture"
    )
    counter_count = _validate_counter_witness(receipt_doc, counter_witness, index)
    source_state = _validate_source_captures(
        receipt_doc,
        pre_capture,
        post_capture,
        common["outer_commit"],
        index,
    )
    if mode == 1:
        correctness, tool = _validate_trace1(
            receipt_doc, evidence, counter_count, common
        )
        throughput = None
        union = {"correctness": correctness}
        evidence_kind = "verifier"
    else:
        if identity_evidence is None:
            _reject(f"TRACE=0 leg {index} identity evidence is absent")
        performance, tool, throughput = _validate_trace0(
            receipt_doc,
            evidence,
            identity_evidence,
            counter_count,
            common,
        )
        union = {"performance": performance}
        evidence_kind = "throughput"
    output = {
        "trace_mode": mode,
        "pbs_jobid": common["raw_jobid"],
        "build": {"binary_sha256": common["binary_sha"]},
        "receipt": {"path": str(receipt_doc.path), "sha256": receipt_doc.sha256},
        "job_result": {"path": str(job_doc.path), "sha256": job_doc.sha256},
        "mode_evidence": {
            "kind": evidence_kind,
            "path": str(evidence.path),
            "sha256": evidence.sha256,
        },
        "counter_witness": {
            "path": str(counter_witness.path),
            "sha256": counter_witness.sha256,
        },
        "judgment_source_state": {
            "guarantee_name": source_state["guarantee_name"],
            "pre": {
                "path": str(pre_capture.path),
                "sha256": pre_capture.sha256,
            },
            "post": {
                "path": str(post_capture.path),
                "sha256": post_capture.sha256,
            },
        },
        **union,
    }
    return ValidatedLeg(
        mode=mode,
        normalized_jobid=common["normalized_jobid"],
        receipt=receipt_doc,
        job_result=job_doc,
        mode_evidence=evidence,
        counter_witness=counter_witness,
        source_captures=(pre_capture, post_capture),
        identity_evidence=identity_evidence,
        outer_commit=common["outer_commit"],
        base_oid=common["base_oid"],
        new_oid=common["new_oid"],
        cmake_target=common["target"],
        workload=common["workload"],
        projection=common["projection"],
        job_script_sha256=common["job_script_sha"],
        compiler_version=common["compiler_version"],
        binary_sha256=common["binary_sha"],
        build_dir=common["build_dir"],
        binary_path=common["binary_path"],
        attempt_dir=common["attempt_dir"],
        run_dir=common["run_dir"],
        tool=tool,
        throughput=throughput,
        output=output,
    )


def _same(legs: Sequence[ValidatedLeg], attribute: str, label: str) -> Any:
    values = [getattr(leg, attribute) for leg in legs]
    if any(not _strict_equal(value, values[0]) for value in values[1:]):
        _reject(f"legs differ in {label}")
    return values[0]


def _unique(legs: Sequence[ValidatedLeg], attribute: str, label: str) -> None:
    values = [getattr(leg, attribute) for leg in legs]
    if len(set(values)) != len(values):
        _reject(f"legs are not distinct in {label}")


def _git_bytes(repo_root: Path, arguments: Sequence[str], label: str) -> bytes:
    try:
        return contract_loader_binding._run_git(repo_root, *arguments)
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise PairValidationError(f"{label} failed") from exc


def _regular_file_bytes(path: Path, label: str) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise PairValidationError(f"{label} is unavailable") from exc
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            _reject(f"{label} is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    finally:
        if fd >= 0:
            os.close(fd)


def _checker_source_binding(
    expected_commit: str,
    expected_sha256: str,
) -> CheckerSourceBinding:
    expected_commit = _oid(expected_commit, "--expected-checker-commit")
    expected_sha256 = _sha256(expected_sha256, "--expected-checker-sha256")
    checker_path = Path(__file__).resolve(strict=True)
    root_bytes = _git_bytes(
        checker_path.parent,
        ["rev-parse", "--show-toplevel"],
        "checker repository root lookup",
    )
    try:
        repo_root = Path(root_bytes.decode("utf-8").strip()).resolve(strict=True)
        relative_path = checker_path.relative_to(repo_root).as_posix()
    except (UnicodeDecodeError, OSError, ValueError) as exc:
        raise PairValidationError("checker path is outside its Git repository") from exc
    if relative_path != CHECKER_REPO_PATH:
        _reject("live checker repository path differs")
    object_type = _git_bytes(
        repo_root,
        ["cat-file", "-t", expected_commit],
        "expected checker commit lookup",
    ).decode("ascii", errors="replace").strip()
    if object_type != "commit":
        _reject("--expected-checker-commit does not name a commit")
    blob_oid = _git_bytes(
        repo_root,
        ["rev-parse", f"{expected_commit}:{CHECKER_REPO_PATH}"],
        "checker Git blob lookup",
    ).decode("ascii", errors="replace").strip()
    if _GIT_OID.fullmatch(blob_oid) is None:
        _reject("checker Git blob OID is invalid")
    blob_bytes = _git_bytes(
        repo_root,
        ["cat-file", "blob", blob_oid],
        "checker Git blob read",
    )
    blob_sha256 = hashlib.sha256(blob_bytes).hexdigest()
    live_sha256 = hashlib.sha256(
        _regular_file_bytes(checker_path, "live checker")
    ).hexdigest()
    if blob_sha256 != expected_sha256:
        _reject("checker Git blob SHA-256 differs from caller pin")
    if live_sha256 != blob_sha256:
        _reject("live checker SHA-256 differs from checker Git blob")
    return CheckerSourceBinding(
        expected_commit=expected_commit,
        expected_sha256=expected_sha256,
        git_blob_oid=blob_oid,
        git_blob_sha256=blob_sha256,
        live_sha256=live_sha256,
    )


def validate_pair(
    legs: Sequence[ValidatedLeg],
    expected_outer_commit: str,
    expected_checker_commit: str,
    expected_checker_sha256: str,
) -> dict[str, Any]:
    by_mode = {mode: [leg for leg in legs if leg.mode == mode] for mode in (0, 1)}
    n0, n1 = len(by_mode[0]), len(by_mode[1])
    if not (n0 == n1 and n0 >= 2):
        _reject("pair requires n_trace0 == n_trace1 >= 2")
    outer = _same(legs, "outer_commit", "outer repository commit")
    if outer != expected_outer_commit:
        _reject("outer repository commit differs from --expected-outer-commit")
    base_oid = _same(legs, "base_oid", "ccbench base OID")
    new_oid = _same(legs, "new_oid", "ccbench new OID")
    target = _same(legs, "cmake_target", "CMake target")
    workload = _same(legs, "workload", "workload tuple")
    projection = _same(legs, "projection", "receipt mocc_trace projection")
    job_script_sha = _same(legs, "job_script_sha256", "job script SHA-256")
    compiler_version = _same(legs, "compiler_version", "compiler version")
    binary_shas = {
        f"trace{mode}": [
            leg.binary_sha256
            for leg in sorted(
                by_mode[mode],
                key=lambda leg: (leg.normalized_jobid, leg.receipt.sha256),
            )
        ]
        for mode in (0, 1)
    }
    same_mode_binary_sha256_equal = all(
        len(set(mode_shas)) == 1 for mode_shas in binary_shas.values()
    )
    _unique(legs, "normalized_jobid", "normalized PBS job ID")
    _unique(legs, "build_dir", "build directory")
    _unique(legs, "binary_path", "binary path")
    _unique(legs, "attempt_dir", "attempt directory")
    _unique(legs, "run_dir", "run directory")
    receipt_hashes = [leg.receipt.sha256 for leg in legs]
    if len(set(receipt_hashes)) != len(receipt_hashes):
        _reject("leg receipt bytes are not distinct")

    ordered = sorted(
        legs,
        key=lambda leg: (leg.mode, leg.normalized_jobid, leg.receipt.sha256),
    )
    rates = [leg.throughput for leg in by_mode[0]]
    assert all(rate is not None for rate in rates)
    rate_values = [float(rate) for rate in rates if rate is not None]
    minimum = min(rate_values)
    maximum = max(rate_values)
    relative_width = (maximum - minimum) / minimum
    projection_bytes = json.dumps(
        projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    checker_binding = _checker_source_binding(
        expected_checker_commit,
        expected_checker_sha256,
    )
    return {
        "schema_version": PAIR_SCHEMA,
        "status": "accepted",
        "pairing_design": "trace-mode-grouped-unordered/v1",
        "n_per_trace_mode": n0,
        "official_certification": False,
        "eligible_for_refreeze": False,
        "prohibited_uses": {
            "headline": True,
            "certified_selection": True,
            "floor": True,
            "oracle": True,
            "fitness": True,
        },
        "identity": {
            "outer_repo_commit": outer,
            "ccbench_base_oid": base_oid,
            "ccbench_new_oid": new_oid,
            "cmake_target": target,
            "workload_tuple": workload,
            "receipt_mocc_trace_projection": projection,
            "receipt_mocc_trace_projection_sha256": hashlib.sha256(
                projection_bytes
            ).hexdigest(),
        },
        "build_identity": {
            "job_script_sha256": job_script_sha,
            "compiler_version": compiler_version,
            "binary_sha256_by_trace_mode": binary_shas,
            "same_mode_binary_sha256_equal": same_mode_binary_sha256_equal,
        },
        "separation": {
            "trace1_role": "correctness-only",
            "trace0_role": "performance-only",
            "distinct_job_ids": True,
            "distinct_build_dirs": True,
            "distinct_binary_paths": True,
            "distinct_attempt_dirs": True,
            "distinct_run_dirs": True,
        },
        "throughput_dispersion_by_trace_mode": {
            "trace0": {
                "min_txns_per_s": minimum,
                "max_txns_per_s": maximum,
                "relative_width": relative_width,
                "relative_width_formula": "(max-min)/min",
                "threshold_gate_applied": False,
            },
            "trace1": {
                "min_txns_per_s": None,
                "max_txns_per_s": None,
                "relative_width": None,
                "reason": "correctness-only; TRACE=1 counters are not performance evidence",
                "threshold_gate_applied": False,
            },
        },
        "legs": [leg.output for leg in ordered],
        "checker": {
            "generator": {
                "path": CHECKER_REPO_PATH,
                "sha256": checker_binding.live_sha256,
                "self_reported_not_external_trust_anchor": True,
            },
            "source_binding": {
                "expected_checker_commit": checker_binding.expected_commit,
                "expected_checker_sha256": checker_binding.expected_sha256,
                "git_blob_path": CHECKER_REPO_PATH,
                "git_blob_oid": checker_binding.git_blob_oid,
                "git_blob_sha256": checker_binding.git_blob_sha256,
                "live_checker_sha256": checker_binding.live_sha256,
                "expected_sha256_matches_git_blob": True,
                "live_checker_sha256_matches_git_blob": True,
            },
        },
    }


def _write_create_only(output: Path, payload: dict[str, Any]) -> None:
    sidecar = output.parent / "mocc-trace-pair-receipt.sha256"
    try:
        if output.resolve(strict=False) == sidecar.resolve(strict=False):
            _reject("pair output path collides with its SHA sidecar")
    except OSError as exc:
        raise PairValidationError("pair output path cannot be resolved") from exc
    raw = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    created_output = False
    created_sidecar = False
    try:
        with open(output, "xb") as handle:
            created_output = True
            handle.write(raw)
        with open(sidecar, "x", encoding="ascii") as handle:
            created_sidecar = True
            handle.write(digest + "\n")
    except Exception:
        if created_sidecar:
            try:
                sidecar.unlink()
            except OSError:
                pass
        if created_output:
            try:
                output.unlink()
            except OSError:
                pass
        raise


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--expected-outer-commit",
        required=True,
        help="exact 40-hex wave tip required for every leg",
    )
    parser.add_argument(
        "--expected-checker-commit",
        required=True,
        help="caller-pinned commit containing the checker source blob",
    )
    parser.add_argument(
        "--expected-checker-sha256",
        required=True,
        help="caller-pinned SHA-256 of the checker source blob",
    )
    parser.add_argument(
        "--leg",
        action="append",
        nargs="+",
        required=True,
        metavar="FILE",
        help=(
            "RECEIPT JOB_RESULT MODE_EVIDENCE, then IDENTITY_REPORT only for "
            "TRACE=0, followed by COUNTER_WITNESS SOURCE_PRE SOURCE_POST"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        expected = _oid(args.expected_outer_commit, "--expected-outer-commit")
        expected_checker_commit = _oid(
            args.expected_checker_commit, "--expected-checker-commit"
        )
        expected_checker_sha256 = _sha256(
            args.expected_checker_sha256, "--expected-checker-sha256"
        )
        legs = [validate_leg(parts, index) for index, parts in enumerate(args.leg)]
        payload = validate_pair(
            legs,
            expected,
            expected_checker_commit,
            expected_checker_sha256,
        )
        _write_create_only(args.output, payload)
        return 0
    except (PairValidationError, FileExistsError, OSError) as exc:
        print(f"mocc_trace_pair: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
