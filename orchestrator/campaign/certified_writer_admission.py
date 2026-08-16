# -*- coding: utf-8 -*-
"""Read-only static admission used by certified-writer PBS wrappers.

This module composes existing strict readers and domain validators.  It does
not issue an execution receipt, probe hardware, or create an artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Mapping

from ..calibrator.schema_v2 import normalize_request_id
from . import (
    env_attestation,
    env_contract,
    floor_submit_receipt,
    s8b_floor_campaign,
    site_policy,
)
from ..qualification import artifacts, attempt_ledger, contract, qsub_binding


_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_CAPTURE_KEYS = {"qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"}
_T126_KEYS = {
    "schema_version", "qualification_lineage", "authority", "hold_enforced",
    "job_id", "qualification_series_id", "qualification_attempt_id", "nonce",
    "source_commit", "source_tree", "ccbench_gitlink", "job_script_sha256",
    "collector_sha256", "protocol_sha256", "request", "preflight",
    "retry_index", "retry_from_attempt_id", "retry_from_series_id",
    "retry_receipt_sha256", "submission_intent_sha256",
    "qsub_invocation_sha256", "qsub_binding_sha256", "dry_run",
    "submitted_epoch",
}


class AdmissionRejected(RuntimeError):
    """Static evidence is present but does not authorize this job."""


class AdmissionInputError(RuntimeError):
    """CLI input or the read-only execution environment is unavailable."""


def _exact(value: object, keys: set[str], label: str) -> Mapping:
    if type(value) is not dict or set(value) != keys:
        raise AdmissionRejected(f"{label} key set mismatch")
    return value


def _require_hash(value: object, pattern: re.Pattern[str], label: str) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise AdmissionRejected(f"{label} is invalid")
    return value


def _required_environment(environ: Mapping[str, str]) -> tuple[str, str]:
    nonce = environ.get("IZANAGI_SUBMISSION_NONCE")
    job_id = environ.get("PBS_JOBID")
    if (type(nonce) is not str or _HEX32.fullmatch(nonce) is None
            or type(job_id) is not str
            or _JOB_ID.fullmatch(normalize_request_id(job_id)) is None):
        raise AdmissionInputError("PBS job identity environment is incomplete")
    return nonce, job_id


def _validate_captures(value: object) -> None:
    captures = _exact(value, _CAPTURE_KEYS, "preflight captures")
    for capture in captures.values():
        row = _exact(capture, {"rc", "stdout_raw", "stderr_raw"}, "preflight capture")
        if (type(row["rc"]) is not int
                or row["rc"] != 0
                or type(row["stdout_raw"]) is not str
                or type(row["stderr_raw"]) is not str):
            raise AdmissionRejected("preflight capture scalar type mismatch")


def _policy(repo_root: Path) -> dict:
    try:
        return artifacts.load_source_json(repo_root / "tools/pegasus/policy.json")
    except Exception as exc:
        raise AdmissionInputError("Pegasus policy is unavailable") from exc


def _validate_request(
        value: object, policy: Mapping, *, walltime_s: object,
) -> None:
    request = _exact(value, {"project", "queue", "nodes", "elapstim_req_s"}, "request")
    if request != {
        "project": policy.get("project"),
        "queue": policy.get("queue"),
        "nodes": policy.get("nodes"),
        "elapstim_req_s": walltime_s,
    }:
        raise AdmissionRejected("request differs from mode-specific Pegasus policy")


def _git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
    except OSError as exc:
        raise AdmissionInputError("git is unavailable for source identity") from exc
    except subprocess.SubprocessError as exc:
        raise AdmissionRejected("source identity cannot be resolved") from exc
    return completed.stdout


def _blob(repo_root: Path, commit: str, relative: str) -> bytes:
    return _git(repo_root, "cat-file", "blob", f"{commit}:{relative}")


def _validate_source_blob(
        repo_root: Path, commit: str, relative: str, expected_sha256: str,
) -> bytes:
    raw = _blob(repo_root, commit, relative)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise AdmissionRejected(f"source blob hash mismatch: {relative}")
    return raw


def _t126_walltime_s(repo_root: Path, commit: str) -> int:
    raw = _blob(repo_root, commit, contract.RESERVATION_POLICY_RELATIVE_PATH)

    def reject_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise AdmissionRejected(
                    f"duplicate T126 reservation policy key: {key}"
                )
            value[key] = item
        return value

    try:
        policy = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                AdmissionRejected(
                    f"non-finite T126 reservation policy constant: {token}"
                )
            ),
        )
    except AdmissionRejected:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionRejected("T126 reservation policy cannot be decoded") from exc
    if type(policy) is not dict:
        raise AdmissionRejected("T126 reservation policy must be an object")
    walltime = policy.get("t126_qualification_walltime_s")
    if type(walltime) is not int or walltime <= 0:
        raise AdmissionRejected("T126 reservation walltime is invalid")
    return walltime


def _require_compute_and_calibration(
        registered: env_contract.ExecutionEnvironmentContract, repo_root: Path,
) -> None:
    if site_policy.current_site() != site_policy.PEGASUS_COMPUTE:
        raise AdmissionRejected("static admission requires Pegasus compute site")
    try:
        env_attestation.load_verified_calibration(registered, repo_root)
    except Exception as exc:
        raise AdmissionRejected("active calibration verification failed") from exc


def _admit_floor(
        repo_root: Path, receipt_path: Path, environ: Mapping[str, str],
) -> None:
    try:
        row = floor_submit_receipt.load_floor_submit_receipt(receipt_path)
    except floor_submit_receipt.FloorSubmitReceiptError as exc:
        raise AdmissionRejected(str(exc)) from exc
    nonce, pbs_job_id = _required_environment(environ)
    try:
        floor_submit_receipt.require_floor_submit_job_binding(
            row, expected_job_id=pbs_job_id, expected_nonce=nonce,
        )
    except floor_submit_receipt.FloorSubmitReceiptError as exc:
        raise AdmissionRejected(str(exc)) from exc
    commit = row["source_commit"]
    script_sha = row["job_script_sha256"]
    policy = _policy(repo_root)
    _validate_request(
        row["request"], policy, walltime_s=policy.get("floor_walltime_s"),
    )
    _validate_captures(row["preflight"])
    _validate_source_blob(repo_root, commit, row["job_script_path"], script_sha)
    try:
        document = s8b_floor_campaign.load_protocol(
            repo_root / "output/s8b-freeze/floor_protocol.json"
        )
        _normalized, registered = s8b_floor_campaign.validate_protocol_against_current(
            document
        )
    except Exception as exc:
        raise AdmissionRejected("floor protocol current validation failed") from exc
    _require_compute_and_calibration(registered, repo_root)


def _load_ledger(repo_root: Path, series_id: str) -> list[dict]:
    directory = (
        repo_root / "output/env/pegasus/qualification/t126/series"
        / series_id / "attempt-ledger"
    )
    if directory.is_symlink() or not directory.is_dir():
        raise AdmissionRejected("T126 attempt ledger directory is unsafe")
    paths = sorted(directory.glob("*.json"))
    if [path.name for path in paths] != [
            f"{index:04d}.json" for index in range(len(paths))]:
        raise AdmissionRejected("T126 attempt ledger is non-contiguous")
    try:
        return [artifacts.load_json_strict(path) for path in paths]
    except Exception as exc:
        raise AdmissionRejected("T126 attempt ledger strict read failed") from exc


def _validate_t126_submission_binding(
        repo_root: Path, receipt_path: Path, row: Mapping, protocol: Mapping,
) -> None:
    series_id = row["qualification_series_id"]
    events = _load_ledger(repo_root, series_id)
    try:
        state = attempt_ledger.replay_attempt_ledger(
            events, series_id=series_id,
            eligible_reasons=protocol["retry"]["eligible_reasons"],
        )
    except Exception as exc:
        raise AdmissionRejected("T126 attempt ledger replay failed") from exc
    expected_state = "initial_submitted" if row["retry_index"] == 0 else "retry_submitted"
    if (state.state != expected_state
            or state.last_attempt_id != row["qualification_attempt_id"]
            or state.last_retry_index != row["retry_index"]
            or state.last_nonce != row["nonce"]
            or state.last_job_id != row["job_id"]
            or state.last_submission_intent_sha256 != row["submission_intent_sha256"]
            or state.last_qsub_invocation_sha256 != row["qsub_invocation_sha256"]
            or state.last_submission_evidence_sha256 != row["qsub_binding_sha256"]):
        raise AdmissionRejected("T126 receipt differs from attempt ledger")
    if row["retry_index"] == 0:
        if any(row[key] is not None for key in (
                "retry_from_attempt_id", "retry_from_series_id",
                "retry_receipt_sha256")):
            raise AdmissionRejected("initial T126 receipt carries retry ancestry")
    else:
        retry_intent = events[-2]["payload"] if len(events) >= 2 else {}
        if (row["retry_from_series_id"] != series_id
                or row["retry_from_attempt_id"]
                != retry_intent.get("retry_from_attempt_id")
                or row["retry_receipt_sha256"]
                != retry_intent.get("retry_from_receipt_sha256")):
            raise AdmissionRejected("T126 retry ancestry differs from attempt ledger")
    try:
        binding_path = receipt_path.parent / "qsub-binding.json"
        invocation_path = receipt_path.parent / "qsub-invocation.json"
        binding = artifacts.load_json_strict(binding_path)
        invocation = artifacts.load_json_strict(invocation_path)
        invocation_sha = artifacts.sha256_file(invocation_path)
        binding_sha = artifacts.sha256_file(binding_path)
        qsub_binding.validate_qsub_binding(
            binding,
            expected_nonce=row["nonce"],
            expected_intent_sha256=row["submission_intent_sha256"],
            expected_invocation_sha256=row["qsub_invocation_sha256"],
            expected_retry_index=row["retry_index"],
            expected_job_id=row["job_id"],
        )
    except Exception as exc:
        raise AdmissionRejected("T126 qsub binding validation failed") from exc
    expected_invocation = {
        "nonce": row["nonce"],
        "retry_index": row["retry_index"],
        "submission_intent_sha256": row["submission_intent_sha256"],
    }
    if (invocation != expected_invocation
            or invocation_sha != row["qsub_invocation_sha256"]
            or binding_sha != row["qsub_binding_sha256"]):
        raise AdmissionRejected("T126 qsub evidence hash mismatch")


def _admit_t126(
        repo_root: Path, receipt_path: Path, environ: Mapping[str, str],
) -> None:
    try:
        receipt = artifacts.load_json_strict(receipt_path)
    except Exception as exc:
        raise AdmissionRejected("T126 receipt strict read failed") from exc
    row = _exact(receipt, _T126_KEYS, "T126 receipt")
    nonce, pbs_job_id = _required_environment(environ)
    if (row["schema_version"] != "t126-qualification-submit-receipt/v1"
            or row["qualification_lineage"] != "t126-only"
            or row["authority"] != "evidence-only/no-promotion"
            or row["hold_enforced"] is not False
            or row["dry_run"] is not False
            or row["nonce"] != nonce
            or type(row["job_id"]) is not str
            or _JOB_ID.fullmatch(row["job_id"]) is None
            or normalize_request_id(row["job_id"]) != normalize_request_id(pbs_job_id)
            or type(row["submitted_epoch"]) is not int
            or row["submitted_epoch"] <= 0):
        raise AdmissionRejected("T126 receipt envelope mismatch")
    commit = _require_hash(row["source_commit"], _HEX40, "source commit")
    for key in (
            "source_tree", "ccbench_gitlink", "qualification_series_id",
            "qualification_attempt_id", "job_script_sha256", "collector_sha256",
            "protocol_sha256", "submission_intent_sha256",
            "qsub_invocation_sha256", "qsub_binding_sha256"):
        _require_hash(row[key], _HEX40 if key in {"source_tree", "ccbench_gitlink"}
                      else _HEX64, key)
    _require_hash(row["nonce"], _HEX32, "nonce")
    if type(row["retry_index"]) is not int or row["retry_index"] not in (0, 1):
        raise AdmissionRejected("retry index is invalid")
    policy = _policy(repo_root)
    _validate_request(
        row["request"], policy,
        walltime_s=_t126_walltime_s(repo_root, commit),
    )
    _validate_captures(row["preflight"])
    job_raw = _validate_source_blob(
        repo_root, commit, "tools/pegasus/t126_qualification.sh",
        row["job_script_sha256"],
    )
    del job_raw
    _validate_source_blob(
        repo_root, commit, "tools/pegasus/collect_t126_qualification.py",
        row["collector_sha256"],
    )
    protocol_raw = _validate_source_blob(
        repo_root, commit, "orchestrator/qualification/t126_control_v1.json",
        row["protocol_sha256"],
    )
    try:
        protocol = contract.load_protocol_bytes(protocol_raw)
    except Exception as exc:
        raise AdmissionRejected("T126 committed protocol validation failed") from exc
    source_tree = _git(repo_root, "rev-parse", f"{commit}^{{tree}}").decode().strip()
    gitlink_fields = _git(
        repo_root, "ls-tree", commit, "external/ccbench"
    ).decode("utf-8", errors="strict").split()
    if (source_tree != row["source_tree"] or len(gitlink_fields) < 3
            or gitlink_fields[0:2] != ["160000", "commit"]
            or gitlink_fields[2] != row["ccbench_gitlink"]):
        raise AdmissionRejected("T126 source tree/gitlink mismatch")
    expected_attempt = contract.attempt_identity({
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": row["qualification_series_id"],
        "pbs_job_id": row["job_id"],
        "nonce": row["nonce"],
        "retry_index": row["retry_index"],
        "submission_intent_sha256": row["submission_intent_sha256"],
    })
    if expected_attempt != row["qualification_attempt_id"]:
        raise AdmissionRejected("T126 attempt identity mismatch")
    registered = env_contract.lookup(protocol["environment"]["env_tag"])
    environment = protocol["environment"]
    if environment != {
        "env_tag": registered.env_tag,
        "clocks_per_us": registered.clocks_per_us,
        "numactl": list(registered.numactl),
        "attestation_mode": registered.attestation_mode,
        "single_process": registered.isolation_policy.single_process,
        "allow_resume": registered.isolation_policy.allow_resume,
    }:
        raise AdmissionRejected("T126 protocol differs from current registry contract")
    _validate_t126_submission_binding(repo_root, receipt_path, row, protocol)
    _require_compute_and_calibration(registered, repo_root)


def admit(
        mode: str, *, repo_root: Path, receipt_path: Path,
        environ: Mapping[str, str] | None = None,
) -> None:
    """Run one read-only static admission; return only on acceptance."""
    if mode not in {"floor", "t126"}:
        raise AdmissionInputError("mode must be floor or t126")
    try:
        root = Path(repo_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AdmissionInputError("repo root is unavailable") from exc
    if not root.is_dir() or (root / ".git").is_symlink():
        raise AdmissionInputError("repo root is not a safe directory")
    receipt = Path(receipt_path)
    if receipt.is_symlink() or not receipt.is_file():
        raise AdmissionInputError("receipt is not a non-symlink regular file")
    env = os.environ if environ is None else environ
    if mode == "floor":
        _admit_floor(root, receipt, env)
    else:
        _admit_t126(root, receipt, env)
