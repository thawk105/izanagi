# -*- coding: utf-8 -*-
"""D95 paper-story A-1 exploratory two-arm measurement and materializer.

The measurement path deliberately reuses ``loop.run_campaign``.  It does not
disable the producer's default remeasurement.  Instead, a selected bench round
is eligible only when the WAL says ``rounds == 1``.  Invalid campaigns remain
first-class raw results and are never silently replaced or promoted.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import shutil
import shlex
import socket
import stat
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator import runner as calibrator_runner  # noqa: E402
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
RECEIPT_SCHEMA = "paper-story-a1-paired-receipt/v2"
JOB_TERMINAL_SCHEMA = "paper-story-a1-paired-job-terminal/v2"
SUBMISSION_SCHEMA = "paper-story-a1-paired-submission/v1"
ACQUISITION_SCHEMA = SUBMISSION_SCHEMA
COMPLETION_SCHEMA = "paper-story-a1-paired-scheduler-completion/v1"
PAIRING_DESIGN = "arm-grouped-positional-v1"
ARM_ORDER = ("adaptive", "static10")
WORKLOAD_ORDER = ("write-heavy", "balanced", "read-heavy")
EXPECTED_VERIFY_CONFIGS = ("legacy",)
PIPELINE_RELATIVE_PATH = "orchestrator/campaign/pipeline.py"
DRIVER_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.py"
POLICY_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.v1.json"
JOB_RELATIVE_PATH = "tools/pegasus/paper_story_a1_paired.sh"
SOURCE_RELATIVE_PATHS = (
    DRIVER_RELATIVE_PATH,
    POLICY_RELATIVE_PATH,
    PIPELINE_RELATIVE_PATH,
    JOB_RELATIVE_PATH,
)
MATERIALIZATION_RELATIVE_PATH = Path(
    "output/insights/2026-08-24_paper-story-a1-paired"
)
COMPLETION_MARKER = ".complete.json"
POLICY_SHA256 = "0112d4b351096aeca3bbc036735ba244045f512d9f2fb9566ed6b5bbb2648d44"
CONTROLLED_CCBENCH_DEFINES = frozenset({
    "BACK_OFF",
    "BACKOFF_FIXED",
    "NO_WAIT_LOCKING_IN_VALIDATION",
    "NO_WAIT_OF_TICTOC",
    "TRACE",
    "WAL",
})
_FULL_OID = re.compile(r"[0-9a-f]{40}")
_FULL_SHA256 = re.compile(r"[0-9a-f]{64}")
_PBS_JOBID = re.compile(r"(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*")
_NORMALIZED_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REQUEST_RE = re.compile(r"Request\s+(\S+)\s+submitted")
_PBS_QUEUE = "gen_S"
NQSV_QSTAT_STATES = frozenset({
    "ARR",
    "WAI",
    "QUE",
    "PRR",
    "RUN",
    "POR",
    "EXT",
    "HLD",
    "HOL",
    "SUS",
    "MIG",
    "STG",
})
_PBS_OBSERVATION_KEYS = frozenset({
    "pbs_jobid",
    "pbs_o_host",
    "pbs_o_workdir",
})
PBS_EVIDENCE_SCOPE = {
    "job_environment_fields": (
        "PBS_JOBID",
        "PBS_O_HOST",
        "PBS_O_WORKDIR",
    ),
    "omitted_job_observations": (
        "PBS_O_QUEUE (not exported by this NQSV site)",
        "stdout/stderr FD targets (not the qsub -o/-e delivery files on NQSV)",
    ),
    "queue_binding": "submission qstat_visibility only",
    "delivery_log_binding": (
        "scheduler completion receipt path/bytes SHA-256 plus job-terminal SHA-256"
    ),
}


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
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PaperStoryError(f"JSON read failed: {path}: {exc}") from exc
    if type(value) is not dict:
        raise PaperStoryError(f"JSON root is not an object: {path}")
    return value


def _decode_json_bytes(raw: bytes, label: str) -> dict:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PaperStoryError(f"JSON bytes decode failed: {label}: {exc}") from exc
    if type(value) is not dict:
        raise PaperStoryError(f"JSON bytes root is not an object: {label}")
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


def _normalize_request_id(value: str) -> str:
    """Match dispatch_compute's request-ID normalization exactly."""
    if type(value) is not str:
        raise PaperStoryError("request ID is not a string")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise PaperStoryError("request ID is empty")
    return normalized


def _validated_request_id(value: str, label: str) -> str:
    normalized = _normalize_request_id(value)
    if _NORMALIZED_REQUEST_ID.fullmatch(normalized) is None:
        raise PaperStoryError(f"{label} is unsafe")
    return normalized


def _parse_request_id(stdout: str) -> str:
    """Match dispatch_compute's NQSV-first, single-token-fallback parser."""
    if type(stdout) is not str:
        raise PaperStoryError("qsub stdout is not a string")
    match = _REQUEST_RE.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise PaperStoryError("qsub stdout does not contain one request ID")


def _read_bytes_once(path: Path, *, missing_ok: bool = False) -> bytes | None:
    """Read one regular-file snapshot without following a final symlink."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise PaperStoryError(f"required snapshot file is missing: {path}") from None
    except OSError as exc:
        raise PaperStoryError(f"snapshot open failed: {path}: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise PaperStoryError(f"snapshot source is not a regular file: {path}")
        remaining = before.st_size
        blocks = []
        while remaining:
            block = os.read(fd, min(1024 * 1024, remaining))
            if not block:
                raise PaperStoryError(f"snapshot source shortened while reading: {path}")
            blocks.append(block)
            remaining -= len(block)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise PaperStoryError(f"snapshot source changed while reading: {path}")
        return b"".join(blocks)
    finally:
        os.close(fd)


def _exclusive_write_bytes(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


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
    if type(value) is int:
        try:
            float(value)
        except OverflowError:
            return {
                "integer_out_of_finite_range": {
                    "sign": -1 if value < 0 else 1,
                    "bit_length": value.bit_length(),
                }
            }
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


def _paths_overlap(left: Path, right: Path) -> bool:
    return _is_within(left, right) or _is_within(right, left)


def _under_scr(path: Path) -> bool:
    scr = Path("/scr")
    return path == scr or _is_within(path, scr)


def _durable_measurement_base(policy: Mapping[str, object]) -> Path:
    execution = policy.get("execution")
    raw = (
        execution.get("durable_measurement_base")
        if type(execution) is dict else None
    )
    if type(raw) is not str:
        raise PaperStoryError("durable measurement base is missing from policy")
    base = Path(raw)
    if not base.is_absolute() or base.resolve(strict=False) != base:
        raise PaperStoryError("durable measurement base must be canonical absolute")
    return base


def _validate_attempt_root(attempt: Path, base: Path) -> Path:
    if not attempt.is_absolute() or attempt.resolve(strict=False) != attempt:
        raise PaperStoryError("acquisition attempt root must be canonical absolute")
    if attempt.parent != base or attempt == base:
        raise PaperStoryError(
            "acquisition attempt root must be one direct durable-base child"
        )
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", attempt.name) is None:
        raise PaperStoryError("acquisition attempt child name is unsafe")
    if os.path.lexists(attempt):
        try:
            info = attempt.lstat()
        except OSError as exc:
            raise PaperStoryError(f"acquisition attempt root stat failed: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise PaperStoryError("acquisition attempt root must be a real directory")
        if attempt.resolve(strict=True) != attempt:
            raise PaperStoryError("acquisition attempt root must not traverse a symlink")
    return attempt


def _attempt_root_identity(attempt: Path) -> dict[str, int]:
    try:
        info = attempt.lstat()
    except OSError as exc:
        raise PaperStoryError(f"attempt root identity stat failed: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PaperStoryError("attempt root identity requires a real directory")
    if attempt.resolve(strict=True) != attempt:
        raise PaperStoryError("attempt root identity traverses a symlink")
    return {"st_dev": info.st_dev, "st_ino": info.st_ino}


def _revalidate_attempt_root(roots: Mapping[str, object]) -> None:
    attempt_raw = roots.get("attempt_root")
    expected = roots.get("attempt_identity")
    if (
        type(attempt_raw) is not str
        or type(expected) is not dict
        or set(expected) != {"st_dev", "st_ino"}
        or type(expected.get("st_dev")) is not int
        or type(expected.get("st_ino")) is not int
    ):
        raise PaperStoryError("attempt root inode binding is missing")
    if _attempt_root_identity(Path(attempt_raw)) != expected:
        raise PaperStoryError("attempt root inode binding differs")


def _attempt_evidence_paths(attempt: Path) -> dict[str, str]:
    base = attempt.parent
    stem = attempt.name
    return {
        "submission_receipt": os.fspath(base / f"{stem}.submission.json"),
        "completion_receipt": os.fspath(base / f"{stem}.completion.json"),
        "stdout_path": os.fspath(base / f"{stem}.stdout"),
        "stderr_path": os.fspath(base / f"{stem}.stderr"),
    }


def _canonical_qsub_contract(
    *,
    repo_root: Path,
    study_id: str,
    source_commit: str,
    attempt: Path,
) -> tuple[list[str], dict[str, object]]:
    evidence = _attempt_evidence_paths(attempt)
    variables = {
        "IZANAGI_EXPECTED_HEAD": source_commit,
        "IZANAGI_A1_STUDY_ID": study_id,
        "IZANAGI_A1_ATTEMPT_ROOT": os.fspath(attempt),
        "IZANAGI_A1_ACQUISITION_RECEIPT": evidence["submission_receipt"],
        "IZANAGI_A1_COMPLETION_RECEIPT": evidence["completion_receipt"],
    }
    variable_text = ",".join(f"{key}={value}" for key, value in variables.items())
    options = {
        "v": variable_text,
        "variables": variables,
        "o": evidence["stdout_path"],
        "e": evidence["stderr_path"],
    }
    argv = [
        "qsub",
        "-v",
        variable_text,
        "-o",
        evidence["stdout_path"],
        "-e",
        evidence["stderr_path"],
        os.fspath((repo_root / JOB_RELATIVE_PATH).resolve(strict=True)),
    ]
    return argv, options


def _pbs_environment_observation() -> dict[str, str]:
    observation = {
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "pbs_o_host": os.environ.get("PBS_O_HOST"),
        "pbs_o_workdir": os.environ.get("PBS_O_WORKDIR"),
    }
    if any(type(value) is not str or not value for value in observation.values()):
        raise PaperStoryError("PBS environment observation is incomplete")
    return observation


def _validate_pbs_observation(
    observation: object,
    *,
    receipt: Mapping[str, object],
    repo_root: Path,
    request_id: str,
) -> dict[str, str]:
    if type(observation) is not dict or set(observation) != _PBS_OBSERVATION_KEYS:
        raise PaperStoryError("PBS environment observation shape differs")
    if any(type(observation.get(key)) is not str for key in _PBS_OBSERVATION_KEYS):
        raise PaperStoryError("PBS environment observation values differ")
    submit = receipt.get("submit_observation")
    if (
        _validated_request_id(observation["pbs_jobid"], "PBS_JOBID")
        != _validated_request_id(request_id, "submission request ID")
        or observation.get("pbs_o_host")
        != (submit.get("submit_host") if type(submit) is dict else None)
        or observation.get("pbs_o_workdir") != os.fspath(repo_root)
    ):
        raise PaperStoryError("PBS environment observation does not cross-bind receipt")
    return dict(observation)


def validate_acquisition_receipt(
    receipt: object,
    *,
    repo_root: Path,
    study_id: str,
    source_commit: str,
    request_id: str,
    pbs_observation: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
) -> dict[str, object]:
    policy = policy if policy is not None else load_policy()[0]
    if type(receipt) is not dict or set(receipt) != {
        "schema_version",
        "route",
        "study_id",
        "source_commit",
        "attempt_root",
        "request_id",
        "submission_receipt_path",
        "completion_receipt_path",
        "qsub_argv",
        "qsub_options",
        "submit_observation",
    }:
        raise PaperStoryError("submission receipt shape differs")
    if receipt.get("schema_version") != SUBMISSION_SCHEMA:
        raise PaperStoryError("submission receipt schema differs")
    if receipt.get("route") != "direct-qsub":
        raise PaperStoryError("acquisition route is not direct-qsub")
    if receipt.get("study_id") != study_id:
        raise PaperStoryError("acquisition study ID differs")
    if receipt.get("source_commit") != source_commit:
        raise PaperStoryError("acquisition source commit differs")
    receipt_request_id = receipt.get("request_id")
    if (
        _validated_request_id(receipt_request_id, "submission request ID")
        != _validated_request_id(request_id, "PBS_JOBID")
    ):
        raise PaperStoryError("acquisition request ID differs from PBS_JOBID")
    raw_attempt = receipt.get("attempt_root")
    if type(raw_attempt) is not str or not Path(raw_attempt).is_absolute():
        raise PaperStoryError("acquisition attempt root must be absolute")
    base = _durable_measurement_base(policy)
    attempt = _validate_attempt_root(Path(raw_attempt), base)
    repo = repo_root.resolve(strict=True)
    if _is_within(attempt, repo):
        raise PaperStoryError("acquisition attempt root must be outside the repository")
    if _under_scr(attempt):
        raise PaperStoryError("acquisition attempt root must not be under /scr")
    evidence = _attempt_evidence_paths(attempt)
    expected_argv, expected_options = _canonical_qsub_contract(
        repo_root=repo,
        study_id=study_id,
        source_commit=source_commit,
        attempt=attempt,
    )
    if receipt.get("submission_receipt_path") != evidence["submission_receipt"]:
        raise PaperStoryError("submission receipt durable path differs")
    if receipt.get("completion_receipt_path") != evidence["completion_receipt"]:
        raise PaperStoryError("completion receipt durable path differs")
    if receipt.get("qsub_argv") != expected_argv:
        raise PaperStoryError("canonical qsub argv differs")
    if receipt.get("qsub_options") != expected_options:
        raise PaperStoryError("canonical qsub -v/-o/-e options differ")
    observation = receipt.get("submit_observation")
    if type(observation) is not dict or set(observation) != {
        "submit_host",
        "qsub_stdout",
        "qsub_stdout_sha256",
        "qsub_stderr",
        "qsub_stderr_sha256",
        "qstat_visibility",
    }:
        raise PaperStoryError("submission observation shape differs")
    submit_host = observation.get("submit_host")
    if (
        type(submit_host) is not str
        or not submit_host
        or any(ord(character) < 0x20 for character in submit_host)
    ):
        raise PaperStoryError("submission host observation is invalid")
    qsub_stdout = observation.get("qsub_stdout")
    qsub_stderr = observation.get("qsub_stderr")
    if qsub_stderr != "":
        raise PaperStoryError("qsub stdout/stderr observation differs")
    parsed_request_id = _parse_request_id(qsub_stdout)
    if (
        _validated_request_id(parsed_request_id, "parsed qsub request ID")
        != _validated_request_id(receipt_request_id, "submission request ID")
    ):
        raise PaperStoryError("qsub stdout request ID differs")
    if (
        observation.get("qsub_stdout_sha256")
        != _sha256_bytes(qsub_stdout.encode("utf-8"))
        or observation.get("qsub_stderr_sha256")
        != _sha256_bytes(qsub_stderr.encode("utf-8"))
    ):
        raise PaperStoryError("qsub stdout/stderr observation hash differs")
    visibility = observation.get("qstat_visibility")
    if type(visibility) is not dict or set(visibility) != {
        "request_id", "visible", "state", "queue", "observed_epoch",
    }:
        raise PaperStoryError("qstat visibility observation shape differs")
    if (
        visibility.get("visible") is not True
        or type(visibility.get("state")) is not str
        or visibility["state"] not in NQSV_QSTAT_STATES
        or visibility.get("queue") != _PBS_QUEUE
        or type(visibility.get("observed_epoch")) is not int
        or visibility["observed_epoch"] <= 0
    ):
        raise PaperStoryError("qstat did not visibly bind the submitted request")
    if (
        _validated_request_id(
            visibility.get("request_id"), "qstat visibility request ID"
        )
        != _validated_request_id(receipt_request_id, "submission request ID")
    ):
        raise PaperStoryError("qstat did not visibly bind the submitted request")
    _validate_pbs_observation(
        pbs_observation,
        receipt=receipt,
        repo_root=repo,
        request_id=request_id,
    )
    return {
        "attempt_root": os.fspath(attempt),
        "attempt_identity": _attempt_root_identity(attempt),
        "raw_root": os.fspath(attempt / "raw"),
        "output_root": os.fspath(attempt / "raw" / "campaign-output"),
        "cache_root": os.fspath(attempt / "cache"),
        "result_root": os.fspath(attempt / "raw" / "results"),
        "tmp_root": os.fspath(attempt / "raw" / "tmp"),
        **evidence,
    }


def validate_completion_receipt(
    receipt: object,
    *,
    trusted_roots: Mapping[str, str],
    source_commit: str,
    request_id: str,
    submission_receipt_sha256: str,
    job_terminal_sha256: str,
) -> dict:
    if type(receipt) is not dict or set(receipt) != {
        "schema_version",
        "study_id",
        "source_commit",
        "attempt_root",
        "request_id",
        "submission_receipt",
        "scheduler_terminal",
        "stdout",
        "stderr",
        "job_terminal",
    }:
        raise PaperStoryError("scheduler completion receipt shape differs")
    if (
        receipt.get("schema_version") != COMPLETION_SCHEMA
        or receipt.get("study_id") != STUDY_ID
        or receipt.get("source_commit") != source_commit
        or receipt.get("attempt_root") != trusted_roots.get("attempt_root")
    ):
        raise PaperStoryError("scheduler completion receipt identity differs")
    if (
        _validated_request_id(
            receipt.get("request_id"), "completion request ID"
        )
        != _validated_request_id(request_id, "job receipt PBS_JOBID")
    ):
        raise PaperStoryError("scheduler completion receipt identity differs")
    expected_bindings = {
        "submission_receipt": (
            trusted_roots.get("submission_receipt"), submission_receipt_sha256
        ),
        "stdout": (trusted_roots.get("stdout_path"), None),
        "stderr": (trusted_roots.get("stderr_path"), None),
        "job_terminal": (
            os.fspath(Path(trusted_roots["raw_root"]) / "job-terminal.json"),
            job_terminal_sha256,
        ),
    }
    for label, (expected_path, expected_sha) in expected_bindings.items():
        binding = receipt.get(label)
        if type(binding) is not dict or set(binding) != {"path", "sha256"}:
            raise PaperStoryError(f"scheduler completion {label} binding differs")
        path = binding.get("path")
        digest = binding.get("sha256")
        if path != expected_path or type(digest) is not str:
            raise PaperStoryError(f"scheduler completion {label} identity differs")
        try:
            observed_sha = _sha256_file(Path(path))
        except OSError as exc:
            raise PaperStoryError(
                f"scheduler completion {label} bytes are unreadable: {exc}"
            ) from exc
        if digest != observed_sha or (expected_sha is not None and digest != expected_sha):
            raise PaperStoryError(f"scheduler completion {label} hash differs")
    terminal = receipt.get("scheduler_terminal")
    if type(terminal) is not dict or set(terminal) != {
        "qstat_visible",
        "state",
        "exit_status",
        "observed_epoch",
        "qstat_stdout",
        "qstat_stdout_sha256",
    }:
        raise PaperStoryError("scheduler terminal observation shape differs")
    qstat_stdout = terminal.get("qstat_stdout")
    if (
        terminal.get("qstat_visible") is not True
        or terminal.get("state") not in {"C", "F"}
        or type(terminal.get("exit_status")) is not int
        or terminal.get("exit_status") != 0
        or type(terminal.get("observed_epoch")) is not int
        or terminal["observed_epoch"] <= 0
        or type(qstat_stdout) is not str
        or not qstat_stdout
        or terminal.get("qstat_stdout_sha256")
        != _sha256_bytes(qstat_stdout.encode("utf-8"))
    ):
        raise PaperStoryError("scheduler terminal observation is incomplete")
    return receipt


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
    attempt_root: Path | None = None,
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
    roots: dict[str, str] = {}
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
    resolved_roots = [Path(value) for value in roots.values()]
    if len(set(roots.values())) != 3:
        raise PaperStoryError("output/cache/result roots must be distinct")
    for index, left in enumerate(resolved_roots):
        for right in resolved_roots[index + 1:]:
            if _paths_overlap(left, right):
                raise PaperStoryError("output/cache/result roots must not overlap")
    if any(_under_scr(item) for item in resolved_roots):
        raise PaperStoryError("measurement roots must not be under /scr")
    if attempt_root is not None:
        attempt = attempt_root.resolve(strict=False)
        expected = {
            "output_root": attempt / "raw" / "campaign-output",
            "cache_root": attempt / "cache",
            "result_root": attempt / "raw" / "results",
        }
        if any(Path(roots[key]) != value for key, value in expected.items()):
            raise PaperStoryError("measurement roots differ from fixed attempt topology")
    return roots


def _source_binding(repo_root: Path, expected_head: str) -> dict:
    if _run_git(repo_root, "rev-parse", "HEAD") != expected_head:
        raise PaperStoryError("source HEAD moved before source binding")
    files = {}
    for relative in SOURCE_RELATIVE_PATHS:
        oid = _run_git(repo_root, "rev-parse", f"{expected_head}:{relative}")
        if not _FULL_OID.fullmatch(oid):
            raise PaperStoryError(f"source git blob OID is invalid: {relative}")
        working_sha = _sha256_file(repo_root / relative)
        if not _FULL_SHA256.fullmatch(working_sha):
            raise PaperStoryError(f"working source SHA-256 is invalid: {relative}")
        files[relative] = {
            "git_blob_oid": oid,
            "working_sha256": working_sha,
        }
    binding = {
        "measurement_source_commit": expected_head,
        "files": files,
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }
    return binding


def _has_exact_five_points(values: Sequence[object]) -> bool:
    return len(values) == 5


def positional_statistics(adaptive: Sequence[object], static10: Sequence[object]) -> dict:
    for label, values in (("adaptive", adaptive), ("static10", static10)):
        if not _has_exact_five_points(values):
            raise PaperStoryError(f"{label} must contain exactly five points")
        if any(not _finite_number(value) or value <= 0 for value in values):
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
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


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
    if type(binding) is not dict or set(binding) != {
        "measurement_source_commit",
        "files",
        "evidence_level",
        "artifact_standalone_proof",
    }:
        return False
    files = binding.get("files")
    if type(files) is not dict or set(files) != set(SOURCE_RELATIVE_PATHS):
        return False
    for relative in SOURCE_RELATIVE_PATHS:
        item = files.get(relative)
        if (
            type(item) is not dict
            or set(item) != {"git_blob_oid", "working_sha256"}
            or type(item.get("git_blob_oid")) is not str
            or _FULL_OID.fullmatch(item["git_blob_oid"]) is None
            or type(item.get("working_sha256")) is not str
            or _FULL_SHA256.fullmatch(item["working_sha256"]) is None
        ):
            return False
    return (
        type(binding.get("measurement_source_commit")) is str
        and _FULL_OID.fullmatch(binding["measurement_source_commit"]) is not None
        and binding.get("evidence_level") == "source-routed-trace0"
        and binding.get("artifact_standalone_proof") is False
    )


def _cmake_defines(argv: Sequence[str] | None) -> dict[str, str] | None:
    if argv is None:
        return None
    values: dict[str, str] = {}
    for token in argv:
        match = re.fullmatch(r"-DCCBENCH_([A-Z0-9_]+)=(.*)", token)
        if match is None:
            continue
        key, value = match.groups()
        if key in values:
            return None
        values[key] = value
    return values


def _option_values(argv: Sequence[str] | None) -> dict[str, list[str]] | None:
    if argv is None:
        return None
    values: dict[str, list[str]] = {}
    index = 1
    while index < len(argv):
        token = argv[index]
        match = re.fullmatch(r"--?([A-Za-z0-9_]+)=(.*)", token)
        if match is not None:
            key, value = match.groups()
            values.setdefault(key, []).append(value)
        elif re.fullmatch(r"--?[A-Za-z0-9_]+", token) and index + 1 < len(argv):
            key = token.lstrip("-")
            if not argv[index + 1].startswith("-"):
                values.setdefault(key, []).append(argv[index + 1])
                index += 1
        index += 1
    return values


def _one_option(
    options: Mapping[str, Sequence[str]], aliases: Sequence[str], expected: object
) -> bool:
    observed = [value for alias in aliases for value in options.get(alias, ())]
    return observed == [str(expected)]


def _canonical_absolute_token(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() and path.resolve(strict=False) == path


def _compiler_define_path(token: str, prefix: str) -> str | None:
    if not token.startswith(prefix):
        return None
    value = token[len(prefix):]
    return value if _canonical_absolute_token(value) else None


def _trace0_commands_match(
    arm_policy: Mapping[str, object],
    policy: Mapping[str, object],
    workload_name: str,
    configure_argv: Sequence[str] | None,
    build_argv: Sequence[str] | None,
    run_argv: Sequence[str] | None,
    perf_bin_sha256: str,
) -> bool:
    expected_defines = {
        **{key: str(value) for key, value in arm_policy["flags"].items()},
        "TRACE": "0",
    }
    if (
        set(expected_defines) != CONTROLLED_CCBENCH_DEFINES
        or configure_argv is None
        or build_argv is None
        or run_argv is None
    ):
        return False

    define_tokens = [
        f"-DCCBENCH_{key}={expected_defines[key]}"
        for key in sorted(arm_policy["flags"])
    ] + ["-DCCBENCH_TRACE=0"]
    if len(configure_argv) != 9 + len(define_tokens):
        return False
    cmake_executable = configure_argv[0]
    source_token = configure_argv[2]
    build_token = configure_argv[4]
    c_compiler = _compiler_define_path(
        configure_argv[7], "-DCMAKE_C_COMPILER="
    )
    cxx_compiler = _compiler_define_path(
        configure_argv[8], "-DCMAKE_CXX_COMPILER="
    )
    expected_configure = [
        cmake_executable,
        "-S",
        source_token,
        "-B",
        build_token,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={c_compiler}",
        f"-DCMAKE_CXX_COMPILER={cxx_compiler}",
        *define_tokens,
    ]
    if any((
        not _canonical_absolute_token(cmake_executable),
        Path(cmake_executable).name != "cmake",
        not _canonical_absolute_token(source_token),
        not _canonical_absolute_token(build_token),
        c_compiler is None,
        cxx_compiler is None,
        list(configure_argv) != expected_configure,
    )):
        return False

    if len(build_argv) != 7:
        return False
    jobs = build_argv[6]
    expected_build = [
        cmake_executable,
        "--build",
        build_token,
        "--target",
        "ycsb_silo.exe",
        "-j",
        jobs,
    ]
    if (
        list(build_argv) != expected_build
        or not jobs.isdecimal()
        or int(jobs) <= 0
        or str(int(jobs)) != jobs
    ):
        return False

    configure_dir = Path(build_token)
    build_dir = Path(build_argv[2])
    if (
        configure_dir != build_dir
    ):
        return False
    executable = build_dir / "cc" / "silo" / "ycsb_silo.exe"
    try:
        executable_raw = _read_bytes_once(executable)
    except PaperStoryError:
        return False
    if executable_raw is None or _sha256_bytes(executable_raw) != perf_bin_sha256:
        return False
    workload = next(
        item for item in policy["workloads"] if item["name"] == workload_name
    )
    scale = policy["scale"]
    pegasus_contract = p2_2.env_contract.lookup("pegasus")
    expected_run = [
        "perf",
        "stat",
        "-e",
        ",".join(calibrator_runner.PERF_EVENTS),
        "--",
        os.fspath(executable),
        f"-thread_num={scale['threads']}",
        f"-ycsb_tuple_num={scale['records']}",
        f"-extime={scale['extime_s']}",
        f"-clocks_per_us={pegasus_contract.clocks_per_us}",
        f"-ycsb_zipf_skew={scale['ycsb_zipf_skew']}",
        f"-ycsb_rratio={workload['ycsb_rratio']}",
        f"-ycsb_rmw={scale['ycsb_rmw']}",
        f"-ycsb_max_ope={scale['ycsb_max_ope']}",
    ]
    return list(run_argv) == expected_run


def _validate_arm(
    arm_policy: Mapping[str, object],
    evidence: Mapping[str, object],
    *,
    policy: Mapping[str, object],
    workload_name: str,
    env_tag: str,
    source_binding: Mapping[str, object],
) -> dict:
    name = arm_policy["name"]
    errors: list[str] = []
    attempts = evidence.get("attempts")
    if type(evidence.get("attempt_count")) is not int or evidence.get("attempt_count") != 1:
        errors.append("attempt-count-not-one")
    if type(attempts) is not list or not attempts:
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
            or (
                payload.get("build_attempt_id") is not None
                and payload.get("build_attempt_id") != attempt_id
            )
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
    build_frame = by_stage.get(STAGE_BUILD_DONE, [{}])[0]
    bench_frame = by_stage.get(STAGE_BENCH_DONE, [{}])[0]
    physical_frames = evidence.get("all_evaluation_frames")
    if evidence.get("attempt_count") == 1 and physical_frames is not None and (
        type(physical_frames) is not list or physical_frames != frames
    ):
        errors.append("physical-evaluation-stage-binding-mismatch")

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
        and _has_exact_five_points(raw_tps)
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
    if (
        type(perf_sha) is not str
        or _FULL_SHA256.fullmatch(perf_sha) is None
        or not _trace0_commands_match(
            arm_policy,
            policy,
            workload_name,
            configure_argv,
            build_argv,
            run_argv,
            perf_sha,
        )
        or not _valid_physical_frame(build_frame)
        or not _valid_physical_frame(bench_frame)
        or not _validate_source_binding(source_binding)
    ):
        errors.append("trace0-source-route-incomplete")

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
    campaign_binding: Mapping[str, object] | None = None,
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
            policy=policy,
            workload_name=workload_name,
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
        "campaign_binding": _json_safe(dict(campaign_binding or {})),
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


def _campaign_id_from_preimage(workload_name: str, preimage: str) -> str:
    return (
        f"paper-story-a1-{workload_name}-paired-"
        f"{_sha256_bytes(preimage.encode('utf-8'))[:8]}"
    )


def _validate_campaign_preimage(
    policy: Mapping[str, object],
    workload_name: str,
    preimage: object,
    admission_policy,
) -> bool:
    if type(preimage) is not str:
        return False
    try:
        value = json.loads(preimage, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, PaperStoryError):
        return False
    if type(value) is not dict or type(value.get("search_config")) is not dict:
        return False
    search = value["search_config"]
    expected_arms = [
        {
            "name": arm["name"],
            "genome": Genome(arm["protocol"], dict(arm["flags"])).canonical(),
        }
        for arm in policy["arms"]
    ]
    expected_workload = {"name": workload_name, **workload_flags(policy, workload_name)}
    if any((
        value.get("trial") != STUDY_ID,
        value.get("search_tag") != "paired",
        value.get("spec_content") != (
            "D95 exploratory A-1 static10 minus adaptive, arm-grouped "
            f"positional comparison, workload={workload_name}"
        ),
        search.get("schema") != "paper-story-a1-paired-campaign/v1",
        search.get("study_id") != STUDY_ID,
        search.get("arm_order") != list(ARM_ORDER),
        search.get("arms") != expected_arms,
        search.get("workload") != expected_workload,
        search.get("scale") != policy["scale"],
        search.get("pairing_design") != PAIRING_DESIGN,
        search.get("formal") is not False,
        search.get("promotion_prohibited") is not True,
    )):
        return False
    if admission_policy is not None:
        try:
            expected_admission = json.loads(admission_policy._preimage_json)
        except (AttributeError, json.JSONDecodeError):
            return False
        if search.get("build_admission") != expected_admission:
            return False
    return True


def _snapshot_frames(raw: bytes, records, issues) -> list[dict]:
    issue_lines = {
        issue[0]
        for issue in issues
        if type(issue) is tuple and len(issue) >= 1 and type(issue[0]) is int
    }
    candidates = []
    offset = 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        end = offset + len(line)
        if line_number not in issue_lines and line.endswith(b"\n"):
            candidates.append((line_number, offset, end, line))
        offset = end
    if len(candidates) != len(records):
        raise PaperStoryError("WAL snapshot record/line projection differs")
    return [
        {
            "line_number": line_number,
            "byte_start": start,
            "byte_end": end,
            "raw_sha256": _sha256_bytes(line),
            "variant": record.variant,
            "stage": record.stage,
            "env_tag": record.env_tag,
            "payload": _json_safe(record.payload),
        }
        for record, (line_number, start, end, line) in zip(records, candidates)
    ]


def _arm_evidence_from_snapshot(
    physical_frames: Sequence[Mapping[str, object]], policy: Mapping[str, object]
) -> list[dict]:
    evaluation_stages = {
        STAGE_BUILD_START,
        STAGE_BUILD_DONE,
        STAGE_VERIFY_DONE,
        STAGE_BENCH_DONE,
        STAGE_COMMIT,
        STAGE_ABORT,
    }
    variants = []
    for frame in physical_frames:
        if frame.get("stage") in evaluation_stages and frame.get("variant") not in variants:
            variants.append(frame.get("variant"))
    arms = []
    for variant in variants:
        frames = [
            dict(frame)
            for frame in physical_frames
            if frame.get("variant") == variant and frame.get("stage") in evaluation_stages
        ]
        attempt_ids = []
        for frame in frames:
            if frame.get("stage") != STAGE_BUILD_START:
                continue
            attempt_id = _frame_payload(frame).get("build_attempt_id")
            if type(attempt_id) is str and attempt_id not in attempt_ids:
                attempt_ids.append(attempt_id)
        attempts = []
        for attempt_id in attempt_ids:
            selected = [
                frame
                for frame in frames
                if len(attempt_ids) == 1
                or _frame_payload(frame).get("build_attempt_id") == attempt_id
            ]
            attempts.append({"build_attempt_id": attempt_id, "frames": selected})
        terminals = [
            frame.get("stage")
            for frame in frames
            if frame.get("stage") in {STAGE_COMMIT, STAGE_ABORT}
        ]
        arms.append({
            "name": _infer_arm_name(frames, policy),
            "variant": variant,
            "attempt_count": len(attempt_ids),
            "attempts": attempts,
            "all_evaluation_frames": frames,
            "last_terminal_stage": terminals[-1] if terminals else None,
            "last_stage": frames[-1].get("stage") if frames else None,
        })
    arms.sort(key=lambda item: (
        list(ARM_ORDER).index(item["name"])
        if item["name"] in ARM_ORDER else len(ARM_ORDER),
        str(item["variant"]),
    ))
    return arms


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
    expected_campaign_preimage: str | None = None,
    expected_layout_root: str | None = None,
    preserved_external_errors: Sequence[str] = (),
) -> dict:
    wal_path = Path(layout.wal_file)
    preexisting_errors = list(preserved_external_errors)
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
        wal_raw = _read_bytes_once(wal_path, missing_ok=True)
    except PaperStoryError as exc:
        wal_raw = None
        preexisting_errors.append(f"wal-snapshot-open-error:{exc}")
    lock_path = Path(layout.lock_file)
    try:
        lock_raw = _read_bytes_once(lock_path, missing_ok=True)
    except PaperStoryError as exc:
        lock_raw = None
        preexisting_errors.append(f"campaign-lock-open-error:{exc}")
    wal_evidence = {
        "path": os.fspath(wal_path),
        "expected_env_tag": env_tag,
        "size": len(wal_raw) if wal_raw is not None else 0,
        "sha256": _sha256_bytes(wal_raw) if wal_raw is not None else None,
        "records": [],
        "line_issues": [],
        "truncated_tail": False,
    }
    if wal_raw is None:
        preexisting_errors.append("wal-snapshot-missing")
    if lock_raw is None:
        preexisting_errors.append("campaign-lock-snapshot-missing")
    lock_preimage = None
    physical_frames: list[dict] = []
    if wal_raw is not None and lock_raw is not None:
        try:
            with tempfile.TemporaryDirectory(prefix="paper-story-a1-snapshot-") as raw_tmp:
                snapshot = CampaignLayout(raw_tmp)
                Path(snapshot.runs_dir).mkdir(mode=0o700)
                _exclusive_write_bytes(Path(snapshot.lock_file), lock_raw)
                _exclusive_write_bytes(Path(snapshot.wal_file), wal_raw)
                lock_preimage = wal.read_lock(snapshot)
                records, issues, truncated_tail = wal.read_records_collected(snapshot)
                wal_evidence["line_issues"] = [list(issue) for issue in issues]
                wal_evidence["truncated_tail"] = truncated_tail
                wal_evidence["records"] = [
                    {
                        "variant": record.variant,
                        "stage": record.stage,
                        "env_tag": record.env_tag,
                        "payload": _json_safe(record.payload),
                    }
                    for record in records
                ]
                physical_frames = _snapshot_frames(wal_raw, records, issues)
                if issues:
                    preexisting_errors.append("wal-line-issues-present")
                if truncated_tail:
                    preexisting_errors.append("wal-truncated-tail")
                try:
                    replayed = wal.replay(snapshot, admission_policy=admission_policy)
                    replay_variants = set(replayed)
                    physical_variants = {
                        frame["variant"] for frame in physical_frames
                        if frame["stage"] in {
                            STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE,
                            STAGE_BENCH_DONE, STAGE_COMMIT, STAGE_ABORT,
                        }
                    }
                    if replay_variants != physical_variants:
                        preexisting_errors.append("wal-replay-physical-variant-mismatch")
                except Exception as exc:  # noqa: BLE001
                    preexisting_errors.append(f"wal-replay-error:{type(exc).__name__}")
        except Exception as exc:  # noqa: BLE001 - retain a bounded forensic result
            preexisting_errors.append(f"wal-snapshot-read-error:{type(exc).__name__}")

    if expected_campaign_preimage is None and admission_policy is not None:
        cfg = ident.bind_admission_policy(
            campaign_config(policy, workload_name), admission_policy
        )
        expected_campaign_preimage = ident.canonical_preimage(cfg)
    expected_id = (
        _campaign_id_from_preimage(workload_name, expected_campaign_preimage)
        if type(expected_campaign_preimage) is str else None
    )
    layout_root = Path(layout.root).resolve(strict=False)
    if (
        lock_preimage != expected_campaign_preimage
        or not _validate_campaign_preimage(
            policy, workload_name, lock_preimage, admission_policy
        )
    ):
        preexisting_errors.append("campaign-lock-preimage-mismatch")
    if expected_id != campaign_id:
        preexisting_errors.append("campaign-id-recomputed-mismatch")
    if layout_root.name != campaign_id:
        preexisting_errors.append("campaign-layout-id-mismatch")
    if expected_layout_root is not None and layout_root != Path(
        expected_layout_root
    ).resolve(strict=False):
        preexisting_errors.append("campaign-layout-root-mismatch")
    if wal_path.resolve(strict=False) != layout_root / "runs" / "wal.jsonl":
        preexisting_errors.append("campaign-wal-path-mismatch")
    campaign_binding = {
        "layout_root": os.fspath(layout_root),
        "wal_path": os.fspath(wal_path.resolve(strict=False)),
        "campaign_lock_path": os.fspath(lock_path.resolve(strict=False)),
        "campaign_lock_size": len(lock_raw) if lock_raw is not None else 0,
        "campaign_lock_sha256": (
            _sha256_bytes(lock_raw) if lock_raw is not None else None
        ),
        "canonical_preimage": lock_preimage,
        "recomputed_campaign_id": expected_id,
    }
    arm_evidence = _arm_evidence_from_snapshot(physical_frames, policy)
    return validate_workload_evidence(
        policy,
        workload_name=workload_name,
        campaign_id=campaign_id,
        env_tag=env_tag,
        arms=arm_evidence,
        wal_evidence=wal_evidence,
        source_binding=source_binding,
        preexisting_errors=preexisting_errors,
        campaign_binding=campaign_binding,
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
    wal_paths = [
        item.get("campaign_binding", {}).get("wal_path")
        if type(item.get("campaign_binding")) is dict else None
        for item in workloads
    ]
    complete = (
        measurement_error is None
        and workload_names == list(WORKLOAD_ORDER)
        and len(set(campaign_ids)) == 3
        and len(wal_paths) == 3
        and None not in wal_paths
        and len(set(wal_paths)) == 3
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
        "pbs_evidence_scope": _json_safe(PBS_EVIDENCE_SCOPE),
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
    cache_root = Path(roots["cache_root"])
    try:
        result_root.mkdir(mode=0o700)
        output_root.mkdir(mode=0o700)
        cache_root.mkdir(mode=0o700)
        (output_root / "env" / env_tag / "claims").mkdir(parents=True, mode=0o700)
    except OSError as exc:
        raise PaperStoryError(f"fresh runtime root creation failed: {exc}") from exc


def run_measurement(args) -> int:
    repo_root = _repo_root()
    policy, policy_sha = load_policy()
    if args.study_id != STUDY_ID:
        raise PaperStoryError("study ID differs from the preregistered ID")
    acquisition_path = Path(args.acquisition_receipt)
    if not acquisition_path.is_absolute() or acquisition_path.resolve(
        strict=True
    ) != acquisition_path:
        raise PaperStoryError("acquisition receipt path must be canonical absolute")
    acquisition_raw = _read_bytes_once(acquisition_path)
    if acquisition_raw is None:  # pragma: no cover - missing_ok is false
        raise PaperStoryError("acquisition receipt is missing")
    acquisition_sha = _sha256_bytes(acquisition_raw)
    if acquisition_sha != args.acquisition_receipt_sha256:
        raise PaperStoryError("acquisition receipt bytes differ from job binding")
    acquisition = _decode_json_bytes(acquisition_raw, "acquisition receipt")
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=args.study_id,
        source_commit=args.expected_head,
        request_id=args.pbs_jobid,
        pbs_observation=_pbs_environment_observation(),
        policy=policy,
    )
    if os.fspath(acquisition_path) != trusted_roots["submission_receipt"]:
        raise PaperStoryError("submission receipt path differs from durable topology")
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
        attempt_root=Path(trusted_roots["attempt_root"]),
    )
    if any(roots[key] != trusted_roots[key] for key in roots):
        raise PaperStoryError("CLI roots differ from acquisition receipt topology")
    roots = dict(trusted_roots)
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
        campaign_preimage = ident.canonical_preimage(bound_cfg)
        expected_layout_root = layout.root
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
            expected_campaign_preimage=campaign_preimage,
            expected_layout_root=expected_layout_root,
        )
        workload_results.append(collected)

    result = assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=source_binding,
        workloads=workload_results,
        measurement_error=measurement_error,
    )
    _revalidate_attempt_root(roots)
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
        "submission_receipt": {
            "path": os.fspath(acquisition_path),
            "sha256": acquisition_sha,
        },
        "scheduler_completion_receipt": {
            "path": trusted_roots["completion_receipt"],
        },
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
    if not _validate_source_binding(binding):
        raise PaperStoryError("raw source binding shape differs")
    for relative in SOURCE_RELATIVE_PATHS:
        expected = binding["files"][relative]
        oid = _run_git(repo_root, "rev-parse", f"{expected_head}:{relative}")
        if oid != expected.get("git_blob_oid"):
            raise PaperStoryError(f"git blob differs from raw source binding: {relative}")
        if _sha256_file(repo_root / relative) != expected.get("working_sha256"):
            raise PaperStoryError(f"working bytes differ from raw source binding: {relative}")


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
        if resolved.parent.parent.parent != output_root:
            raise PaperStoryError("WAL evidence is not in the canonical campaign layout")
        records = wal_evidence.get("records")
        env_tags = {
            record.get("env_tag")
            for record in records
            if type(record) is dict and type(record.get("env_tag")) is str
        } if type(records) is list else set()
        if not env_tags and type(wal_evidence.get("expected_env_tag")) is str:
            env_tags = {wal_evidence["expected_env_tag"]}
        if len(env_tags) != 1:
            raise PaperStoryError("workload does not bind one WAL env tag")
        layout = CampaignLayout(os.fspath(resolved.parent.parent))
        campaign_binding = workload.get("campaign_binding")
        if type(campaign_binding) is not dict:
            raise PaperStoryError("workload campaign binding is missing")
        recollected = collect_workload(
            load_policy()[0],
            workload_name=workload["workload"],
            campaign_id=workload["campaign_id"],
            layout=layout,
            admission_policy=context.policy,
            env_tag=next(iter(env_tags)),
            source_binding=result["source_binding"],
            expected_campaign_preimage=campaign_binding.get("canonical_preimage"),
            expected_layout_root=campaign_binding.get("layout_root"),
            preserved_external_errors=[
                error for error in workload.get("errors", [])
                if type(error) is str and (
                    error.startswith("campaign-error:")
                    or error == "campaign-summary-not-fresh-exact-two"
                )
            ],
        )
        if recollected != workload:
            raise PaperStoryError("workload does not revalidate from raw WAL snapshot")


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
    if result.get("pbs_evidence_scope") != _json_safe(PBS_EVIDENCE_SCOPE):
        raise PaperStoryError("PBS evidence scope disclosure differs")
    workloads = result.get("workloads")
    if type(workloads) is not list:
        raise PaperStoryError("result workloads is not a list")
    names = [item.get("workload") for item in workloads if type(item) is dict]
    ids = [item.get("campaign_id") for item in workloads if type(item) is dict]
    wal_paths = [
        item.get("campaign_binding", {}).get("wal_path")
        if type(item.get("campaign_binding")) is dict else None
        for item in workloads if type(item) is dict
    ]
    recomputed_complete = (
        result.get("measurement_error") is None
        and names == list(WORKLOAD_ORDER)
        and len(ids) == 3
        and len(set(ids)) == 3
        and len(wal_paths) == 3
        and None not in wal_paths
        and len(set(wal_paths)) == 3
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
    if (
        type(terminal.get("driver_rc")) is not int
        or terminal.get("driver_rc") != 0
        or type(terminal.get("shell_rc")) is not int
        or terminal.get("shell_rc") != 0
        or terminal.get("status") != "finished"
    ):
        raise PaperStoryError("job did not terminate with a finished raw bundle")
    if (
        _validated_request_id(terminal.get("pbs_jobid"), "terminal PBS_JOBID")
        != _validated_request_id(receipt.get("pbs_jobid"), "receipt PBS_JOBID")
    ):
        raise PaperStoryError("job terminal PBS identity differs from receipt")
    pbs_observation = terminal.get("pbs_observation")
    if (
        type(pbs_observation) is not dict
        or set(pbs_observation) != _PBS_OBSERVATION_KEYS
        or pbs_observation.get("pbs_jobid") != terminal.get("pbs_jobid")
    ):
        raise PaperStoryError("job terminal PBS environment observation differs")
    binding = result.get("source_binding")
    if type(binding) is not dict:
        raise PaperStoryError("result source binding is missing")
    if terminal.get("expected_head") != binding.get("measurement_source_commit"):
        raise PaperStoryError("job terminal expected HEAD differs from source binding")
    if (
        terminal.get("observed_head") != terminal.get("expected_head")
        or terminal.get("porcelain") != ""
    ):
        raise PaperStoryError("job terminal did not observe H0 clean")
    if receipt.get("source_binding") != result.get("source_binding"):
        raise PaperStoryError("result and receipt source bindings differ")
    if terminal.get("terminal_source_binding") != result.get("source_binding"):
        raise PaperStoryError("terminal source bytes differ from result source binding")
    roots = receipt.get("roots")
    if (
        type(roots) is not dict
        or terminal.get("completion_receipt_path") != roots.get("completion_receipt")
    ):
        raise PaperStoryError("terminal completion receipt path differs")
    if terminal.get("attempt_identity") != roots.get("attempt_identity"):
        raise PaperStoryError("terminal attempt root inode binding differs")
    submission = receipt.get("submission_receipt")
    if (
        type(submission) is not dict
        or terminal.get("submission_receipt_sha256") != submission.get("sha256")
    ):
        raise PaperStoryError("terminal submission receipt hash differs")
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
        "For each workload, the observed mean of its five signed positional "
        "differences is negative in this one run."
        if complete and all_negative is True
        else "The three workloads do not all have a negative observed mean of their "
        "five signed positional differences in this run."
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
        "artifact-standalone proof. Invalid input always means no cross-workload conclusion.\n\n"
        "PBS evidence scope: the job observes PBS_JOBID, PBS_O_HOST, and "
        "PBS_O_WORKDIR. PBS_O_QUEUE is not exported by this NQSV site and is not "
        "claimed as a job observation. NQSV stdout/stderr FD targets are not the "
        "qsub -o/-e delivery files; their delivered bytes are bound only by the "
        "scheduler completion receipt SHA-256 values and the job-terminal SHA-256.\n"
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


def _exact_materialization_destination(repo_root: Path, raw: Path) -> Path:
    destination = raw if raw.is_absolute() else Path.cwd() / raw
    destination = destination.resolve(strict=False)
    expected = (repo_root / MATERIALIZATION_RELATIVE_PATH).resolve(strict=False)
    if destination != expected:
        raise PaperStoryError("materialize destination is not the exact A-1 insight leaf")
    if os.path.lexists(destination):
        raise PaperStoryError("materialize destination already exists")
    if not destination.parent.is_dir():
        raise PaperStoryError("materialize destination parent does not exist")
    return destination


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_staging_noreplace(staging: Path, destination: Path) -> None:
    rename_noreplace = 1
    at_fdcwd = -100
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise PaperStoryError("renameat2 no-replace is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    rc = renameat2(
        at_fdcwd,
        os.fsencode(staging),
        at_fdcwd,
        os.fsencode(destination),
        rename_noreplace,
    )
    if rc != 0:
        error = ctypes.get_errno()
        raise PaperStoryError(
            f"no-replace materialization publish failed: {os.strerror(error)}"
        )
    _fsync_directory(destination.parent)


def _publish_complete_staging(
    staging: Path, destination: Path, completion: Mapping[str, object]
) -> None:
    _exclusive_write(staging / COMPLETION_MARKER, completion)
    _fsync_directory(staging)
    _publish_staging_noreplace(staging, destination)


def _remove_unpublished_staging(
    staging: Path, identity: tuple[int, int]
) -> None:
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(f"staging cleanup stat failed: {exc}") from exc
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("staging cleanup identity differs")
    try:
        shutil.rmtree(staging)
    except OSError as exc:
        raise PaperStoryError(f"staging cleanup failed: {exc}") from exc


def _publish_materialization_bundle(
    destination: Path,
    materialized_receipt: Mapping[str, object],
    result: Mapping[str, object],
) -> None:
    staging = destination.parent / f".{destination.name}.staging-{os.getpid()}"
    try:
        staging.mkdir(mode=0o700)
        staging_info = staging.lstat()
    except OSError as exc:
        raise PaperStoryError(f"exclusive staging creation failed: {exc}") from exc
    staging_identity = (staging_info.st_dev, staging_info.st_ino)
    published = False
    try:
        _exclusive_write(staging / "receipt.json", materialized_receipt)
        _exclusive_write(staging / "result.json", result)
        _exclusive_write_text(staging / "README.md", _readme(result))
        completion = {
            "schema_version": "paper-story-a1-paired-materialization-complete/v1",
            "destination": os.fspath(destination),
            "files": {
                name: _sha256_file(staging / name)
                for name in ("README.md", "receipt.json", "result.json")
            },
        }
        _publish_complete_staging(staging, destination, completion)
        published = True
    finally:
        if not published:
            _remove_unpublished_staging(staging, staging_identity)


def run_materialize(args) -> int:
    repo_root = _repo_root()
    raw_result_path = Path(args.raw_result).resolve(strict=True)
    raw_receipt_path = Path(args.raw_receipt).resolve(strict=True)
    job_terminal_path = Path(args.job_terminal).resolve(strict=True)
    completion_receipt_path = Path(args.completion_receipt).resolve(strict=True)
    result = _read_json(raw_result_path)
    receipt = _read_json(raw_receipt_path)
    terminal = _read_json(job_terminal_path)
    policy, policy_sha = load_policy()
    validate_raw_documents(result, receipt, terminal, policy)
    acquisition_binding = receipt.get("submission_receipt")
    if (
        type(acquisition_binding) is not dict
        or set(acquisition_binding) != {"path", "sha256"}
        or type(acquisition_binding.get("path")) is not str
        or type(acquisition_binding.get("sha256")) is not str
    ):
        raise PaperStoryError("raw receipt acquisition binding differs")
    acquisition_path = Path(acquisition_binding["path"])
    if not acquisition_path.is_absolute() or acquisition_path.resolve(
        strict=True
    ) != acquisition_path:
        raise PaperStoryError("materialized acquisition path is not canonical absolute")
    acquisition_raw = _read_bytes_once(acquisition_path)
    if (
        acquisition_raw is None
        or _sha256_bytes(acquisition_raw) != acquisition_binding["sha256"]
        or terminal.get("submission_receipt_sha256") != acquisition_binding["sha256"]
    ):
        raise PaperStoryError("acquisition receipt bytes do not cross-bind")
    acquisition = _decode_json_bytes(acquisition_raw, "materialized acquisition receipt")
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=STUDY_ID,
        source_commit=args.expected_head,
        request_id=receipt.get("pbs_jobid"),
        pbs_observation=terminal.get("pbs_observation"),
        policy=policy,
    )
    _revalidate_attempt_root(receipt.get("roots", {}))
    if receipt.get("roots") != trusted_roots:
        raise PaperStoryError("raw receipt roots differ from fixed acquisition topology")
    if receipt.get("scheduler_completion_receipt") != {
        "path": trusted_roots["completion_receipt"]
    }:
        raise PaperStoryError("raw receipt scheduler completion binding differs")
    if (
        raw_result_path != Path(trusted_roots["result_root"]) / "result.json"
        or raw_receipt_path != Path(trusted_roots["result_root"]) / "receipt.json"
        or job_terminal_path != Path(trusted_roots["raw_root"]) / "job-terminal.json"
        or completion_receipt_path != Path(trusted_roots["completion_receipt"])
    ):
        raise PaperStoryError("raw document paths differ from fixed attempt topology")
    completion_raw = _read_bytes_once(completion_receipt_path)
    if completion_raw is None:  # pragma: no cover - missing_ok is false
        raise PaperStoryError("scheduler completion receipt is missing")
    completion = _decode_json_bytes(completion_raw, "scheduler completion receipt")
    validate_completion_receipt(
        completion,
        trusted_roots=trusted_roots,
        source_commit=args.expected_head,
        request_id=receipt.get("pbs_jobid"),
        submission_receipt_sha256=acquisition_binding["sha256"],
        job_terminal_sha256=_sha256_file(job_terminal_path),
    )
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

    destination = _exact_materialization_destination(repo_root, Path(args.destination))
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
            "scheduler_completion_receipt": {
                "path": os.fspath(completion_receipt_path),
                "sha256": _sha256_bytes(completion_raw),
            },
        },
    }
    _publish_materialization_bundle(destination, materialized_receipt, result)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    measure = sub.add_parser("measure")
    measure.add_argument("--study-id", required=True)
    measure.add_argument("--expected-head", required=True)
    measure.add_argument("--pbs-jobid", required=True)
    measure.add_argument("--acquisition-receipt", required=True)
    measure.add_argument("--acquisition-receipt-sha256", required=True)
    measure.add_argument("--output-root", required=True)
    measure.add_argument("--cache-root", required=True)
    measure.add_argument("--result-root", required=True)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--expected-head", required=True)
    materialize.add_argument("--raw-result", required=True)
    materialize.add_argument("--raw-receipt", required=True)
    materialize.add_argument("--job-terminal", required=True)
    materialize.add_argument("--completion-receipt", required=True)
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
