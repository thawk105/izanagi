# -*- coding: utf-8 -*-
"""D95 paper-story A-1 exploratory two-arm measurement and materializer.

The measurement path deliberately reuses ``loop.run_campaign``.  It does not
disable the producer's default remeasurement.  Instead, a selected bench round
is eligible only when the WAL says ``rounds == 1``.  Invalid campaigns remain
first-class raw results and are never silently replaced or promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, ident, p2_2, pin, site_policy, wal  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
)
from .durable_root import DurableRootPolicy  # noqa: E402
from .layout import CampaignLayout, exploration_campaign_layout  # noqa: E402
from .loop import run_campaign  # noqa: E402
from .model import (  # noqa: E402
    CampaignConfig,
    Genome,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)
from .pipeline import PerfConfig  # noqa: E402


POLICY_PATH = Path(__file__).with_name("paper_story_a1_paired.v1.json")
STUDY_ID = "paper-story-a1-20260824-exploratory-v1"
RESULT_SCHEMA = "paper-story-a1-paired-result/v1"
RECEIPT_SCHEMA = "paper-story-a1-paired-receipt/v1"
JOB_TERMINAL_SCHEMA = "paper-story-a1-paired-job-terminal/v1"
PAIRING_DESIGN = "arm-grouped-positional-v1"
ARM_ORDER = ("adaptive", "static10")
WORKLOAD_ORDER = ("write-heavy", "balanced", "read-heavy")
EXPECTED_VERIFY_CONFIGS = ("legacy",)
PIPELINE_RELATIVE_PATH = "orchestrator/campaign/pipeline.py"
DRIVER_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.py"
POLICY_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.v1.json"
POLICY_SHA256 = "84b934f0feec7ad715f205c47ba5fb2880b70d4f9707f56ffab76bf7f17e2403"
_FULL_OID = re.compile(r"[0-9a-f]{40}")
_FULL_SHA256 = re.compile(r"[0-9a-f]{64}")
_PBS_JOBID = re.compile(r"(?:[0-9]+:)?[A-Za-z0-9._-]+")


class PaperStoryError(RuntimeError):
    """The A-1 preregistered contract is not satisfied."""


def _reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise PaperStoryError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _reject_constant(value: str):
    raise PaperStoryError(f"non-finite JSON constant: {value}")


def _read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(
                stream,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PaperStoryError(f"JSON read failed: {path}: {exc}") from exc
    if type(value) is not dict:
        raise PaperStoryError(f"JSON root is not an object: {path}")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _exclusive_write(path: Path, value: object) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        raw = _canonical_json_bytes(value)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def _exclusive_write_text(path: Path, value: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            fd = -1
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            label = "nan"
        elif value > 0:
            label = "+inf"
        else:
            label = "-inf"
        return {"nonfinite_number": label}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def validate_policy(policy: object) -> dict:
    if type(policy) is not dict:
        raise PaperStoryError("policy must be an exact JSON object")
    canonical = _read_json(POLICY_PATH)
    if set(policy) != set(canonical):
        raise PaperStoryError("policy top-level key set differs")
    for key, expected in canonical.items():
        if policy.get(key) != expected:
            raise PaperStoryError(f"policy field differs: {key}")
    if _sha256_file(POLICY_PATH) != POLICY_SHA256:
        raise PaperStoryError("tracked policy bytes differ from the preregistered hash")
    return policy


def load_policy() -> tuple[dict, str]:
    policy = validate_policy(_read_json(POLICY_PATH))
    return policy, POLICY_SHA256


def genomes(policy: Mapping[str, object]) -> list[Genome]:
    validate_policy(policy)
    return [
        Genome(arm["protocol"], dict(arm["flags"]))
        for arm in policy["arms"]
    ]


def workload_flags(policy: Mapping[str, object], workload_name: str) -> dict[str, str]:
    validate_policy(policy)
    workload = next(
        (item for item in policy["workloads"] if item["name"] == workload_name),
        None,
    )
    if workload is None:
        raise PaperStoryError(f"unknown workload: {workload_name}")
    scale = policy["scale"]
    return {
        "ycsb_zipf_skew": scale["ycsb_zipf_skew"],
        "ycsb_rratio": workload["ycsb_rratio"],
        "ycsb_rmw": scale["ycsb_rmw"],
        "ycsb_max_ope": scale["ycsb_max_ope"],
    }


def campaign_config(
    policy: Mapping[str, object], workload_name: str, *, contract=None,
) -> CampaignConfig:
    validate_policy(policy)
    contract = contract or p2_2._legacy_linux_contract()
    flags = workload_flags(policy, workload_name)
    search_config = {
        "schema": "paper-story-a1-paired-campaign/v1",
        "study_id": policy["study_id"],
        "arm_order": list(policy["arm_order"]),
        "arms": [
            {
                "name": arm["name"],
                "genome": Genome(arm["protocol"], dict(arm["flags"])).canonical(),
            }
            for arm in policy["arms"]
        ],
        "workload": {"name": workload_name, **flags},
        "scale": dict(policy["scale"]),
        "pairing_design": policy["pairing"]["design"],
        "formal": False,
        "promotion_prohibited": True,
    }
    cfg = CampaignConfig(
        spec_slug=f"paper-story-a1-{workload_name}",
        search_tag="paired",
        spec_content=(
            "D95 exploratory A-1 static10 minus adaptive, arm-grouped "
            f"positional comparison, workload={workload_name}"
        ),
        ccbench_commit=pin.CURRENT_PIN,
        search_config=search_config,
        trial=policy["study_id"],
    )
    return ident.bind_environment_contract(cfg, contract)


def _run_git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", os.fspath(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PaperStoryError(
            f"git {' '.join(args)} failed rc={proc.returncode}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_measure_environment(
    *,
    repo_root: Path,
    expected_head: str,
    output_root: Path,
    cache_root: Path,
    result_root: Path,
    pbs_jobid: str,
    site: str,
    observed_head: str,
    porcelain: str,
) -> dict[str, str]:
    """Pure fail-closed gate shared by the CLI and negative contract tests."""
    if site != site_policy.PEGASUS_COMPUTE:
        raise PaperStoryError("measure mode requires Pegasus compute")
    if not _FULL_OID.fullmatch(expected_head):
        raise PaperStoryError("expected HEAD must be one full lowercase OID")
    if observed_head != expected_head:
        raise PaperStoryError("current HEAD differs from expected HEAD")
    if porcelain:
        raise PaperStoryError("working tree is dirty")
    if not _PBS_JOBID.fullmatch(pbs_jobid):
        raise PaperStoryError("PBS_JOBID is missing or unsafe")
    resolved_repo = repo_root.resolve(strict=True)
    roots = {}
    for label, raw in (
        ("output_root", output_root),
        ("cache_root", cache_root),
        ("result_root", result_root),
    ):
        if not raw.is_absolute():
            raise PaperStoryError(f"{label} must be absolute")
        resolved = raw.resolve(strict=False)
        if _is_within(resolved, resolved_repo):
            raise PaperStoryError(f"{label} must be outside the repository")
        if os.path.lexists(raw) or os.path.lexists(resolved):
            raise PaperStoryError(f"{label} must not already exist")
        roots[label] = os.fspath(resolved)
    if len(set(roots.values())) != 3:
        raise PaperStoryError("output/cache/result roots must be distinct")
    return roots


def _source_binding(repo_root: Path, expected_head: str) -> dict:
    if _run_git(repo_root, "rev-parse", "HEAD") != expected_head:
        raise PaperStoryError("source HEAD moved before source binding")
    pipeline_path = repo_root / PIPELINE_RELATIVE_PATH
    pipeline_oid = _run_git(
        repo_root, "rev-parse", f"{expected_head}:{PIPELINE_RELATIVE_PATH}"
    )
    if not _FULL_OID.fullmatch(pipeline_oid):
        raise PaperStoryError("pipeline git blob OID is not a full lowercase OID")
    binding = {
        "measurement_source_commit": expected_head,
        "pipeline_path": PIPELINE_RELATIVE_PATH,
        "pipeline_git_blob_oid": pipeline_oid,
        "pipeline_source_sha256": _sha256_file(pipeline_path),
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }
    if not _FULL_SHA256.fullmatch(binding["pipeline_source_sha256"]):
        raise PaperStoryError("pipeline source SHA-256 is invalid")
    return binding


def positional_statistics(adaptive: Sequence[object], static10: Sequence[object]) -> dict:
    for label, values in (("adaptive", adaptive), ("static10", static10)):
        if len(values) != 5:
            raise PaperStoryError(f"{label} must contain exactly five points")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
            for value in values
        ):
            raise PaperStoryError(f"{label} contains a non-positive finite-number violation")
    differences = [float(static10[i]) - float(adaptive[i]) for i in range(5)]
    mean = statistics.fmean(differences)
    variance = sum((value - mean) ** 2 for value in differences) / 4
    return {
        "pairing_design": PAIRING_DESIGN,
        "contrast": "static10-minus-adaptive",
        "pairs": [
            {
                "pair_index": index,
                "adaptive_tps": float(adaptive[index]),
                "static10_tps": float(static10[index]),
                "signed_difference_tps": differences[index],
            }
            for index in range(5)
        ],
        "mean_signed_positional_difference_tps": mean,
        "sample_sd_positional_difference_tps": math.sqrt(variance),
        "sample_variance_positional_difference_tps2": variance,
        "observed_mean_negative": mean < 0,
    }


def _finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _numbers_equal(left: object, right: object) -> bool:
    return (
        _finite_number(left)
        and _finite_number(right)
        and float(left) == float(right)
    )


def _command_argv(value: object) -> list[str] | None:
    if isinstance(value, str):
        try:
            argv = shlex.split(value)
        except ValueError:
            return None
    elif (
        isinstance(value, list)
        and all(type(item) is str for item in value)
    ):
        argv = list(value)
    else:
        return None
    return argv if argv else None


def _frame_payload(frame: Mapping[str, object]) -> dict:
    payload = frame.get("payload")
    return payload if type(payload) is dict else {}


def _frame_ref(frame: Mapping[str, object]) -> dict:
    return {
        "line_number": _json_safe(frame.get("line_number")),
        "byte_start": _json_safe(frame.get("byte_start")),
        "byte_end": _json_safe(frame.get("byte_end")),
        "raw_sha256": _json_safe(frame.get("raw_sha256")),
        "stage": _json_safe(frame.get("stage")),
    }


def _valid_physical_frame(frame: Mapping[str, object]) -> bool:
    return (
        type(frame.get("line_number")) is int
        and frame["line_number"] > 0
        and type(frame.get("byte_start")) is int
        and frame["byte_start"] >= 0
        and type(frame.get("byte_end")) is int
        and frame["byte_end"] > frame["byte_start"]
        and type(frame.get("raw_sha256")) is str
        and _FULL_SHA256.fullmatch(frame["raw_sha256"]) is not None
    )


def _validate_source_binding(binding: object) -> bool:
    return (
        type(binding) is dict
        and set(binding) == {
            "measurement_source_commit", "pipeline_path",
            "pipeline_git_blob_oid", "pipeline_source_sha256",
            "evidence_level", "artifact_standalone_proof",
        }
        and type(binding["measurement_source_commit"]) is str
        and _FULL_OID.fullmatch(binding["measurement_source_commit"]) is not None
        and binding["pipeline_path"] == PIPELINE_RELATIVE_PATH
        and type(binding["pipeline_git_blob_oid"]) is str
        and _FULL_OID.fullmatch(binding["pipeline_git_blob_oid"]) is not None
        and type(binding["pipeline_source_sha256"]) is str
        and _FULL_SHA256.fullmatch(binding["pipeline_source_sha256"]) is not None
        and binding["evidence_level"] == "source-routed-trace0"
        and binding["artifact_standalone_proof"] is False
    )


def _validate_arm(
    arm_policy: Mapping[str, object],
    evidence: Mapping[str, object],
    *,
    env_tag: str,
    source_binding: Mapping[str, object],
) -> dict:
    name = arm_policy["name"]
    errors: list[str] = []
    attempts = evidence.get("attempts")
    if type(evidence.get("attempt_count")) is not int or evidence.get("attempt_count") != 1:
        errors.append("attempt-count-not-one")
    if type(attempts) is not list or len(attempts) != 1:
        attempts = []
    attempt = attempts[0] if attempts else {}
    attempt_id = attempt.get("build_attempt_id")
    frames = attempt.get("frames")
    if type(attempt_id) is not str or not attempt_id:
        errors.append("attempt-id-invalid")
    if type(frames) is not list:
        frames = []
    expected_stages = [
        STAGE_BUILD_START,
        STAGE_BUILD_DONE,
        *([STAGE_VERIFY_DONE] * len(EXPECTED_VERIFY_CONFIGS)),
        STAGE_BENCH_DONE,
        STAGE_COMMIT,
    ]
    stages = [frame.get("stage") for frame in frames if type(frame) is dict]
    if stages != expected_stages:
        errors.append("stage-sequence-mismatch")
    if evidence.get("last_terminal_stage") != STAGE_COMMIT:
        errors.append("final-terminal-not-commit")
    if evidence.get("last_stage") != STAGE_COMMIT:
        errors.append("commit-not-final-frame")
    variant = evidence.get("variant")
    for frame in frames:
        if type(frame) is not dict:
            errors.append("frame-not-object")
            continue
        payload = _frame_payload(frame)
        if (
            frame.get("variant") != variant
            or frame.get("env_tag") != env_tag
            or payload.get("build_attempt_id") != attempt_id
        ):
            errors.append("frame-attempt-variant-env-mismatch")
            break

    by_stage: dict[str, list[dict]] = {}
    for frame in frames:
        if type(frame) is dict:
            by_stage.setdefault(str(frame.get("stage")), []).append(frame)
    start = _frame_payload(by_stage.get(STAGE_BUILD_START, [{}])[0])
    build = _frame_payload(by_stage.get(STAGE_BUILD_DONE, [{}])[0])
    bench = _frame_payload(by_stage.get(STAGE_BENCH_DONE, [{}])[0])
    commit = _frame_payload(by_stage.get(STAGE_COMMIT, [{}])[0])
    verify_frames = by_stage.get(STAGE_VERIFY_DONE, [])

    expected_genome = Genome(
        arm_policy["protocol"], dict(arm_policy["flags"])
    ).canonical()
    if (
        start.get("genome") != expected_genome
        or type(start.get("src_token")) is not str
        or not start["src_token"]
    ):
        errors.append("source-genome-binding-mismatch")
    receipt_sha = start.get("build_admission_receipt_sha256")
    if (
        type(receipt_sha) is not str
        or _FULL_SHA256.fullmatch(receipt_sha) is None
        or build.get("build_admission_receipt_sha256") != receipt_sha
        or commit.get("build_admission_receipt_sha256") != receipt_sha
    ):
        errors.append("build-admission-binding-mismatch")

    verify_tags = []
    for frame in verify_frames:
        payload = _frame_payload(frame)
        workload = payload.get("workload")
        verify_tags.append(workload.get("tag") if type(workload) is dict else None)
        if payload.get("certified") is not True:
            errors.append("verify-not-certified")
    if verify_tags != list(EXPECTED_VERIFY_CONFIGS):
        errors.append("verify-config-sequence-mismatch")
    if commit.get("verify_configs") != list(EXPECTED_VERIFY_CONFIGS):
        errors.append("commit-verify-projection-mismatch")

    raw_tps = bench.get("tps")
    tps_valid = (
        type(raw_tps) is list
        and len(raw_tps) == 5
        and all(_finite_number(value) and value > 0 for value in raw_tps)
    )
    if not tps_valid:
        errors.append("tps-not-exact-five-positive-finite-nonbool")
    if bench.get("rep_notes") != []:
        errors.append("rep-notes-not-empty")
    rounds = bench.get("rounds")
    if type(rounds) is not int or rounds != 1:
        errors.append("rounds-not-one")
    if bench.get("unstable") is not False:
        errors.append("unstable-not-false")

    if tps_valid:
        median = statistics.median(float(value) for value in raw_tps)
        mean = statistics.fmean(float(value) for value in raw_tps)
        cv = statistics.stdev(float(value) for value in raw_tps) / mean
        if not _numbers_equal(bench.get("median_tps"), median):
            errors.append("bench-median-does-not-match-tps")
        if not _numbers_equal(bench.get("cv"), cv):
            errors.append("bench-cv-does-not-match-tps")
    if (
        not _numbers_equal(commit.get("fitness_tps"), bench.get("median_tps"))
        or not _numbers_equal(commit.get("cv"), bench.get("cv"))
        or commit.get("unstable") is not bench.get("unstable")
        or commit.get("high_variance") is not bench.get("high_variance")
    ):
        errors.append("bench-commit-numeric-projection-mismatch")

    perf_sha = build.get("perf_bin_sha256")
    configure_cmd = build.get("perf_configure_cmd")
    build_cmd = build.get("perf_build_cmd")
    configure_argv = _command_argv(configure_cmd)
    build_argv = _command_argv(build_cmd)
    run_argv = _command_argv(bench.get("run_cmd"))
    trace_defines = (
        [token for token in configure_argv if token.startswith("-DCCBENCH_TRACE=")]
        if configure_argv else []
    )
    expected_defines = [
        f"-DCCBENCH_{key}={arm_policy['flags'][key]}"
        for key in sorted(arm_policy["flags"])
    ]
    if (
        type(perf_sha) is not str
        or _FULL_SHA256.fullmatch(perf_sha) is None
        or configure_argv is None
        or trace_defines != ["-DCCBENCH_TRACE=0"]
        or any(configure_argv.count(token) != 1 for token in expected_defines)
        or build_argv is None
        or "--target" not in build_argv
        or "ycsb_silo.exe" not in build_argv
        or run_argv is None
        or not any("ycsb_silo.exe" in token for token in run_argv)
        or not _valid_physical_frame(build_frame)
        or not _valid_physical_frame(bench_frame)
        or not _validate_source_binding(source_binding)
    ):
        errors.append("trace0-source-route-incomplete")

    build_frame = by_stage.get(STAGE_BUILD_DONE, [{}])[0]
    bench_frame = by_stage.get(STAGE_BENCH_DONE, [{}])[0]
    result = {
        "name": name,
        "variant": _json_safe(variant),
        "genome": expected_genome,
        "valid": not errors,
        "errors": sorted(set(errors)),
        "raw_tps": _json_safe(raw_tps),
        "actual_rounds": _json_safe(rounds),
        "unstable": _json_safe(bench.get("unstable")),
        "rep_notes": _json_safe(bench.get("rep_notes")),
        "attempt_count": _json_safe(evidence.get("attempt_count")),
        "correctness_evidence": {
            "verify_configs": _json_safe(verify_tags),
            "certified": [
                _json_safe(_frame_payload(frame).get("certified"))
                for frame in verify_frames
            ],
            "verify_done_frames": [_frame_ref(frame) for frame in verify_frames],
        },
        "performance_trace0_evidence": {
            **dict(source_binding),
            "perf_bin_sha256": _json_safe(perf_sha),
            "perf_configure_cmd": _json_safe(configure_cmd),
            "perf_build_cmd": _json_safe(build_cmd),
            "bench_run_cmd": _json_safe(bench.get("run_cmd")),
            "build_done_frame": _frame_ref(build_frame),
            "bench_done_frame": _frame_ref(bench_frame),
        },
        "ordered_attempt_frames": [_frame_ref(frame) for frame in frames],
    }
    return result


def validate_workload_evidence(
    policy: Mapping[str, object],
    *,
    workload_name: str,
    campaign_id: str,
    env_tag: str,
    arms: Sequence[Mapping[str, object]],
    wal_evidence: Mapping[str, object],
    source_binding: Mapping[str, object],
    preexisting_errors: Sequence[str] = (),
) -> dict:
    validate_policy(policy)
    errors = list(preexisting_errors)
    if workload_name not in WORKLOAD_ORDER:
        errors.append("unexpected-workload")
    if type(campaign_id) is not str or not campaign_id:
        errors.append("campaign-id-invalid")
    if len(arms) != 2:
        errors.append("variant-set-cardinality-not-two")
    names = [arm.get("name") for arm in arms]
    if names != list(ARM_ORDER):
        errors.append("arm-order-or-set-mismatch")
    arm_results = {}
    for arm_policy in policy["arms"]:
        matches = [arm for arm in arms if arm.get("name") == arm_policy["name"]]
        if len(matches) != 1:
            errors.append(f"{arm_policy['name']}:arm-missing-or-duplicate")
            arm_results[arm_policy["name"]] = {
                "name": arm_policy["name"],
                "valid": False,
                "errors": ["arm-missing-or-duplicate"],
                "raw_tps": None,
            }
            continue
        arm_result = _validate_arm(
            arm_policy,
            matches[0],
            env_tag=env_tag,
            source_binding=source_binding,
        )
        arm_results[arm_policy["name"]] = arm_result
        errors.extend(f"{arm_policy['name']}:{item}" for item in arm_result["errors"])

    valid = not errors and all(item.get("valid") for item in arm_results.values())
    stats = None
    if valid:
        try:
            stats = positional_statistics(
                arm_results["adaptive"]["raw_tps"],
                arm_results["static10"]["raw_tps"],
            )
        except PaperStoryError as exc:
            errors.append(f"statistics-invalid:{exc}")
            valid = False
    return {
        "workload": workload_name,
        "campaign_id": campaign_id,
        "valid": valid,
        "errors": sorted(set(errors)),
        "arms": arm_results,
        "statistics": stats if valid else None,
        "wal_evidence": _json_safe(dict(wal_evidence)),
    }


def _serialize_frame(frame: wal.OrderedAttemptFrame) -> dict:
    return {
        "line_number": frame.line_number,
        "byte_start": frame.byte_start,
        "byte_end": frame.byte_end,
        "raw_sha256": _sha256_bytes(frame.raw_bytes),
        "variant": frame.record.variant,
        "stage": frame.record.stage,
        "env_tag": frame.record.env_tag,
        "payload": _json_safe(frame.record.payload),
    }


def _infer_arm_name(frames: Sequence[Mapping[str, object]], policy: Mapping[str, object]):
    starts = [frame for frame in frames if frame.get("stage") == STAGE_BUILD_START]
    if not starts:
        return None
    genome = _frame_payload(starts[0]).get("genome")
    matches = [
        arm["name"]
        for arm in policy["arms"]
        if Genome(arm["protocol"], dict(arm["flags"])).canonical() == genome
    ]
    return matches[0] if len(matches) == 1 else None


def collect_workload(
    policy: Mapping[str, object],
    *,
    workload_name: str,
    campaign_id: str,
    layout: CampaignLayout,
    admission_policy,
    env_tag: str,
    source_binding: Mapping[str, object],
    summary=None,
    campaign_error: str | None = None,
) -> dict:
    wal_path = Path(layout.wal_file)
    if wal_path.is_file():
        wal_raw = wal_path.read_bytes()
        wal_evidence = {
            "path": os.fspath(wal_path),
            "size": len(wal_raw),
            "sha256": _sha256_bytes(wal_raw),
        }
    else:
        wal_evidence = {"path": os.fspath(wal_path), "size": 0, "sha256": None}
    preexisting_errors = []
    if campaign_error is not None:
        preexisting_errors.append(f"campaign-error:{campaign_error}")
    if summary is not None and (
        summary.total != 2
        or summary.evaluated != 2
        or summary.skipped != 0
        or summary.identity_skipped != 0
    ):
        preexisting_errors.append("campaign-summary-not-fresh-exact-two")

    try:
        records = wal.read_records(layout)
        wal_evidence["records"] = [
            {
                "variant": record.variant,
                "stage": record.stage,
                "env_tag": record.env_tag,
                "payload": _json_safe(record.payload),
            }
            for record in records
        ]
    except Exception as exc:  # noqa: BLE001 - forensic fallback is part of the result
        records = []
        wal_evidence["records"] = []
        preexisting_errors.append(f"wal-read-error:{type(exc).__name__}:{exc}")

    arm_evidence: list[dict] = []
    try:
        states = wal.replay(layout, admission_policy=admission_policy)
    except Exception as exc:  # noqa: BLE001 - preserve invalid WAL rather than discard it
        states = {}
        preexisting_errors.append(f"wal-replay-error:{type(exc).__name__}:{exc}")
    for variant, state in states.items():
        attempts = []
        all_frames = []
        for attempt_id in state.attempts:
            try:
                frames = [
                    _serialize_frame(frame)
                    for frame in wal.ordered_attempt_frames(layout, attempt_id)
                ]
            except Exception as exc:  # noqa: BLE001
                frames = []
                preexisting_errors.append(
                    f"ordered-frames-error:{variant}:{attempt_id}:{type(exc).__name__}:{exc}"
                )
            all_frames.extend(frames)
            attempts.append({"build_attempt_id": attempt_id, "frames": frames})
        arm_evidence.append({
            "name": _infer_arm_name(all_frames, policy),
            "variant": variant,
            "attempt_count": len(state.attempts),
            "attempts": attempts,
            "last_terminal_stage": (
                state.last_terminal.stage if state.last_terminal is not None else None
            ),
            "last_stage": state.last.stage if state.last is not None else None,
        })
    arm_evidence.sort(
        key=lambda item: (
            list(ARM_ORDER).index(item["name"])
            if item["name"] in ARM_ORDER else len(ARM_ORDER),
            str(item["variant"]),
        )
    )
    return validate_workload_evidence(
        policy,
        workload_name=workload_name,
        campaign_id=campaign_id,
        env_tag=env_tag,
        arms=arm_evidence,
        wal_evidence=wal_evidence,
        source_binding=source_binding,
        preexisting_errors=preexisting_errors,
    )


def assemble_result(
    policy: Mapping[str, object],
    *,
    policy_sha256: str,
    source_binding: Mapping[str, object],
    workloads: Sequence[Mapping[str, object]],
    measurement_error: str | None = None,
) -> dict:
    validate_policy(policy)
    workload_names = [item.get("workload") for item in workloads]
    campaign_ids = [item.get("campaign_id") for item in workloads]
    complete = (
        measurement_error is None
        and workload_names == list(WORKLOAD_ORDER)
        and len(set(campaign_ids)) == 3
        and all(item.get("valid") is True for item in workloads)
    )
    all_negative = (
        complete
        and all(
            item["statistics"]["observed_mean_negative"] is True
            for item in workloads
        )
    )
    return {
        "schema_version": RESULT_SCHEMA,
        "study_id": STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "authority": "exploratory",
        "pairing_design": PAIRING_DESIGN,
        "policy_sha256": policy_sha256,
        "source_binding": dict(source_binding),
        "complete": complete,
        "measurement_error": measurement_error,
        "workloads": [_json_safe(dict(item)) for item in workloads],
        "cross_workload_conclusion": (
            {
                "observed_all_workloads_negative": all_negative,
                "claim_scope": "this one arm-grouped exploratory run only",
            }
            if complete else None
        ),
        "limitations": [
            "Arm-grouped ordinal positions are not shared time blocks.",
            "No causal effect, population mean, significance, or confidence interval is claimed.",
            "Source-routed trace0 evidence is not an artifact-standalone proof.",
            "An invalid workload suppresses every cross-workload conclusion.",
        ],
    }


def _prepare_runtime_roots(roots: Mapping[str, str], env_tag: str) -> None:
    result_root = Path(roots["result_root"])
    output_root = Path(roots["output_root"])
    try:
        result_root.mkdir(mode=0o700)
        output_root.mkdir(mode=0o700)
        (output_root / "env" / env_tag / "claims").mkdir(parents=True, mode=0o700)
    except OSError as exc:
        raise PaperStoryError(f"fresh runtime root creation failed: {exc}") from exc


def run_measurement(args) -> int:
    repo_root = _repo_root()
    policy, policy_sha = load_policy()
    if args.study_id != STUDY_ID:
        raise PaperStoryError("study ID differs from the preregistered ID")
    observed_head = _run_git(repo_root, "rev-parse", "HEAD")
    porcelain = _run_git(
        repo_root, "status", "--porcelain", "--untracked-files=all"
    )
    current_site = site_policy.current_site()
    roots = validate_measure_environment(
        repo_root=repo_root,
        expected_head=args.expected_head,
        output_root=Path(args.output_root),
        cache_root=Path(args.cache_root),
        result_root=Path(args.result_root),
        pbs_jobid=args.pbs_jobid,
        site=current_site,
        observed_head=observed_head,
        porcelain=porcelain,
    )
    site, contract, authorization = p2_2.resolve_site_runtime()
    if site != site_policy.PEGASUS_COMPUTE:
        raise PaperStoryError("resolved runtime is not Pegasus compute")
    loaded_calibration = p2_2._assert_matches_calibration(contract)
    _prepare_runtime_roots(roots, contract.env_tag)
    source_binding = _source_binding(repo_root, args.expected_head)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx
    )
    durable_policy = DurableRootPolicy(
        approved_roots=(Path(roots["output_root"]).resolve(),),
        forbidden_roots=(),
    )

    workload_results = []
    measurement_error = None
    for workload_name in WORKLOAD_ORDER:
        cfg = campaign_config(policy, workload_name, contract=contract)
        cfg = p2_2._campaign_cfg_for_site(cfg, site, contract)
        bound_cfg = ident.bind_admission_policy(cfg, build_context.policy)
        campaign_id = str(ident.campaign_id(bound_cfg))
        layout = exploration_campaign_layout(campaign_id, roots["output_root"])
        summary = None
        campaign_error = None
        try:
            p2_2._assert_single_tenant()
            perf = PerfConfig(
                records=policy["scale"]["records"],
                threads=policy["scale"]["threads"],
                workload=workload_flags(policy, workload_name),
                extime=policy["scale"]["extime_s"],
                reps=policy["scale"]["reps"],
            )

            def capability_resolver(evidence, *, workload_name=workload_name):
                generator_input = (
                    f"paper-story-a1-paired/v1|{STUDY_ID}|{workload_name}|"
                    f"{evidence.genome_sha256}"
                ).encode("utf-8")
                return attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=_sha256_bytes(generator_input),
                )

            summary = run_campaign(
                cfg,
                genomes(policy),
                perf,
                contract.env_tag,
                contract.clocks_per_us,
                numactl=list(contract.numactl),
                output_root=roots["output_root"],
                cache_root=roots["cache_root"],
                authorization_contract=authorization,
                env_contract=contract,
                expected_toolchain_manifest=toolchain_manifest,
                build_context=build_context,
                declared_use_class="exploration",
                capability_resolver=capability_resolver,
                durable_root_policy=durable_policy,
            )
            campaign_id = summary.campaign_id
            layout = CampaignLayout(summary.layout_root)
        except Exception as exc:  # noqa: BLE001 - invalid campaigns are landed raw
            campaign_error = f"{type(exc).__name__}: {exc}"
        collected = collect_workload(
            policy,
            workload_name=workload_name,
            campaign_id=campaign_id,
            layout=layout,
            admission_policy=build_context.policy,
            env_tag=contract.env_tag,
            source_binding=source_binding,
            summary=summary,
            campaign_error=campaign_error,
        )
        workload_results.append(collected)

    result = assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=source_binding,
        workloads=workload_results,
        measurement_error=measurement_error,
    )
    result_path = Path(roots["result_root"]) / "result.json"
    _exclusive_write(result_path, result)
    result_sha = _sha256_file(result_path)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "study_id": STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "route": "direct-qsub",
        "pbs_jobid": args.pbs_jobid,
        "host": socket.gethostname(),
        "recorded_epoch": int(time.time()),
        "policy": {
            "path": POLICY_RELATIVE_PATH,
            "sha256": policy_sha,
        },
        "source_binding": source_binding,
        "roots": roots,
        "result": {
            "path": os.fspath(result_path),
            "sha256": result_sha,
            "complete": result["complete"],
        },
        "calibration_sha256": getattr(loaded_calibration, "sha256", None),
    }
    _exclusive_write(Path(roots["result_root"]) / "receipt.json", receipt)
    return 0


def _verify_current_source(repo_root: Path, expected_head: str, binding: Mapping[str, object]):
    if _run_git(repo_root, "rev-parse", "HEAD") != expected_head:
        raise PaperStoryError("HEAD moved after measurement")
    if _run_git(repo_root, "status", "--porcelain", "--untracked-files=all"):
        raise PaperStoryError("working tree is dirty before materialization")
    if binding.get("measurement_source_commit") != expected_head:
        raise PaperStoryError("raw source commit differs from expected HEAD")
    oid = _run_git(repo_root, "rev-parse", f"{expected_head}:{PIPELINE_RELATIVE_PATH}")
    if oid != binding.get("pipeline_git_blob_oid"):
        raise PaperStoryError("pipeline git blob differs from raw source binding")
    if _sha256_file(repo_root / PIPELINE_RELATIVE_PATH) != binding.get(
        "pipeline_source_sha256"
    ):
        raise PaperStoryError("pipeline source bytes differ from raw source binding")


def _revalidate_raw_wals(result: Mapping[str, object], receipt: Mapping[str, object]) -> None:
    roots = receipt.get("roots")
    if type(roots) is not dict or type(roots.get("output_root")) is not str:
        raise PaperStoryError("receipt output root binding is missing")
    output_root = Path(roots["output_root"]).resolve(strict=True)
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    for workload in result["workloads"]:
        wal_evidence = workload.get("wal_evidence")
        if type(wal_evidence) is not dict or type(wal_evidence.get("path")) is not str:
            raise PaperStoryError("workload WAL evidence is missing")
        wal_path = Path(wal_evidence["path"])
        if not wal_path.is_absolute():
            raise PaperStoryError("WAL evidence path is not absolute")
        resolved = wal_path.resolve(strict=False)
        if not _is_within(resolved, output_root):
            raise PaperStoryError("WAL evidence path escaped the measured output root")
        if resolved.is_file():
            raw = resolved.read_bytes()
            if (
                wal_evidence.get("size") != len(raw)
                or wal_evidence.get("sha256") != _sha256_bytes(raw)
            ):
                raise PaperStoryError("raw WAL bytes differ from recorded digest")
        elif wal_evidence.get("size") != 0 or wal_evidence.get("sha256") is not None:
            raise PaperStoryError("missing WAL has a non-empty digest projection")
        if workload.get("valid") is not True:
            continue
        records = wal_evidence.get("records")
        env_tags = {
            record.get("env_tag")
            for record in records
            if type(record) is dict and type(record.get("env_tag")) is str
        } if type(records) is list else set()
        if len(env_tags) != 1:
            raise PaperStoryError("valid workload does not bind one WAL env tag")
        layout = CampaignLayout(os.fspath(resolved.parent.parent))
        recollected = collect_workload(
            load_policy()[0],
            workload_name=workload["workload"],
            campaign_id=workload["campaign_id"],
            layout=layout,
            admission_policy=context.policy,
            env_tag=next(iter(env_tags)),
            source_binding=result["source_binding"],
        )
        if recollected != workload:
            raise PaperStoryError("valid workload does not revalidate from raw WAL")


def validate_raw_documents(result: object, receipt: object, terminal: object, policy: object):
    validate_policy(policy)
    if type(result) is not dict or result.get("schema_version") != RESULT_SCHEMA:
        raise PaperStoryError("raw result schema differs")
    if type(receipt) is not dict or receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise PaperStoryError("raw receipt schema differs")
    if type(terminal) is not dict or terminal.get("schema_version") != JOB_TERMINAL_SCHEMA:
        raise PaperStoryError("job terminal schema differs")
    for document in (result, receipt, terminal):
        if document.get("study_id") != STUDY_ID:
            raise PaperStoryError("raw document study ID differs")
    if (
        result.get("formal") is not False
        or result.get("promotion_prohibited") is not True
        or receipt.get("formal") is not False
        or receipt.get("promotion_prohibited") is not True
    ):
        raise PaperStoryError("exploratory authority flags differ")
    if result.get("pairing_design") != PAIRING_DESIGN:
        raise PaperStoryError("pairing design differs")
    workloads = result.get("workloads")
    if type(workloads) is not list:
        raise PaperStoryError("result workloads is not a list")
    names = [item.get("workload") for item in workloads if type(item) is dict]
    ids = [item.get("campaign_id") for item in workloads if type(item) is dict]
    recomputed_complete = (
        result.get("measurement_error") is None
        and names == list(WORKLOAD_ORDER)
        and len(ids) == 3
        and len(set(ids)) == 3
        and all(item.get("valid") is True for item in workloads)
    )
    if result.get("complete") is not recomputed_complete:
        raise PaperStoryError("top-level complete does not match workload validity")
    if recomputed_complete:
        all_negative = True
        for item in workloads:
            arms = item.get("arms")
            if type(arms) is not dict or set(arms) != set(ARM_ORDER):
                raise PaperStoryError("materialized valid workload arm set differs")
            stats = positional_statistics(
                arms["adaptive"].get("raw_tps"),
                arms["static10"].get("raw_tps"),
            )
            if item.get("statistics") != stats:
                raise PaperStoryError("stored statistics do not recompute exactly")
            all_negative = all_negative and stats["observed_mean_negative"]
        expected_conclusion = {
            "observed_all_workloads_negative": all_negative,
            "claim_scope": "this one arm-grouped exploratory run only",
        }
        if result.get("cross_workload_conclusion") != expected_conclusion:
            raise PaperStoryError("cross-workload conclusion differs")
    elif result.get("cross_workload_conclusion") is not None:
        raise PaperStoryError("invalid result must have no cross-workload conclusion")
    if terminal.get("driver_rc") != 0 or terminal.get("status") != "finished":
        raise PaperStoryError("job did not terminate with a finished raw bundle")
    if terminal.get("pbs_jobid") != receipt.get("pbs_jobid"):
        raise PaperStoryError("job terminal PBS identity differs from receipt")
    binding = result.get("source_binding")
    if type(binding) is not dict:
        raise PaperStoryError("result source binding is missing")
    if terminal.get("expected_head") != binding.get("measurement_source_commit"):
        raise PaperStoryError("job terminal expected HEAD differs from source binding")
    if receipt.get("source_binding") != result.get("source_binding"):
        raise PaperStoryError("result and receipt source bindings differ")
    if not _validate_source_binding(result.get("source_binding")):
        raise PaperStoryError("source binding is incomplete")
    return result, receipt, terminal


def _readme(result: Mapping[str, object]) -> str:
    complete = result["complete"] is True
    conclusion = result.get("cross_workload_conclusion")
    all_negative = (
        conclusion.get("observed_all_workloads_negative")
        if type(conclusion) is dict else None
    )
    negative_text = "yes" if all_negative is True else "no" if complete else "not-assessable"
    conclusion_text = (
        "All three workload means are negative in this one observed run."
        if complete and all_negative is True
        else "The three workloads do not all have a negative observed mean in this run."
        if complete
        else "No cross-workload conclusion is available because at least one workload is invalid."
    )
    return (
        "# Paper-story A-1 exploratory positional comparison\n\n"
        f"Study: `{STUDY_ID}`\n\n"
        f"Complete: `{'true' if complete else 'false'}`\n\n"
        f"All-workload observed negative direction: `{negative_text}`\n\n"
        f"{conclusion_text}\n\n"
        "This result is exploratory, formal=false, and promotion is prohibited. "
        "The five positions are arm-grouped ordinal matches, not shared time blocks. "
        "They do not support causal, population, significance, confidence-interval, "
        "or repeatability claims. Trace0 evidence is source-routed and is not an "
        "artifact-standalone proof. Invalid input always means no cross-workload conclusion.\n"
    )


def create_materialization_destination(raw: Path) -> Path:
    destination = raw
    if not destination.is_absolute():
        destination = (Path.cwd() / destination).resolve(strict=False)
    else:
        destination = destination.resolve(strict=False)
    if os.path.lexists(destination):
        raise PaperStoryError("materialize destination already exists")
    if not destination.parent.is_dir():
        raise PaperStoryError("materialize destination parent does not exist")
    try:
        destination.mkdir(mode=0o700)
    except OSError as exc:
        raise PaperStoryError(f"exclusive destination creation failed: {exc}") from exc
    return destination


def run_materialize(args) -> int:
    repo_root = _repo_root()
    raw_result_path = Path(args.raw_result).resolve(strict=True)
    raw_receipt_path = Path(args.raw_receipt).resolve(strict=True)
    job_terminal_path = Path(args.job_terminal).resolve(strict=True)
    result = _read_json(raw_result_path)
    receipt = _read_json(raw_receipt_path)
    terminal = _read_json(job_terminal_path)
    policy, policy_sha = load_policy()
    validate_raw_documents(result, receipt, terminal, policy)
    if result.get("policy_sha256") != policy_sha:
        raise PaperStoryError("raw result policy hash differs from tracked policy")
    if receipt.get("policy") != {
        "path": POLICY_RELATIVE_PATH,
        "sha256": policy_sha,
    }:
        raise PaperStoryError("raw receipt policy binding differs")
    if receipt.get("result") != {
        "path": os.fspath(raw_result_path),
        "sha256": _sha256_file(raw_result_path),
        "complete": result["complete"],
    }:
        raise PaperStoryError("raw receipt result binding differs")
    if terminal.get("result_sha256") != _sha256_file(raw_result_path):
        raise PaperStoryError("job terminal result hash differs")
    if terminal.get("receipt_sha256") != _sha256_file(raw_receipt_path):
        raise PaperStoryError("job terminal receipt hash differs")
    _verify_current_source(repo_root, args.expected_head, result["source_binding"])
    _revalidate_raw_wals(result, receipt)

    destination = create_materialization_destination(Path(args.destination))
    materialized_receipt = {
        **receipt,
        "materialization": {
            "destination": os.fspath(destination),
            "raw_result": {
                "path": os.fspath(raw_result_path),
                "sha256": _sha256_file(raw_result_path),
            },
            "raw_receipt": {
                "path": os.fspath(raw_receipt_path),
                "sha256": _sha256_file(raw_receipt_path),
            },
            "job_terminal": {
                "path": os.fspath(job_terminal_path),
                "sha256": _sha256_file(job_terminal_path),
            },
        },
    }
    _exclusive_write(destination / "receipt.json", materialized_receipt)
    _exclusive_write(destination / "result.json", result)
    _exclusive_write_text(destination / "README.md", _readme(result))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    measure = sub.add_parser("measure")
    measure.add_argument("--study-id", required=True)
    measure.add_argument("--expected-head", required=True)
    measure.add_argument("--pbs-jobid", required=True)
    measure.add_argument("--output-root", required=True)
    measure.add_argument("--cache-root", required=True)
    measure.add_argument("--result-root", required=True)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--expected-head", required=True)
    materialize.add_argument("--raw-result", required=True)
    materialize.add_argument("--raw-receipt", required=True)
    materialize.add_argument("--job-terminal", required=True)
    materialize.add_argument("--destination", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "measure":
            return run_measurement(args)
        return run_materialize(args)
    except PaperStoryError as exc:
        print(f"paper-story A-1 refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
