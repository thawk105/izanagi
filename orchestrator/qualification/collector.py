#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Login-side phase-two collector and read-only verifier for T-126."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional

from .artifacts import (
    PERMANENT_NONRETRY_FAILURES,
    QualificationArtifactError,
    QualificationRoot,
    ReceiptVerification,
    create_or_verify_bytes,
    create_or_verify_json,
    create_attempt,
    file_record,
    load_json_strict,
    load_jsonl_strict,
    read_regular_file,
    read_regular_file_with_identity,
    safe_relative_path,
    sha256_bytes,
    validate_retry_history,
    verify_manifest_closure,
)
from .attempt_ledger import SeriesAttemptLedger
from .contract import (
    RESERVATION_POLICY_RELATIVE_PATH,
    attempt_identity, load_protocol, series_identity, validate_protocol)
from .identity import (
    verify_recorded_series_identity,
    verify_submission_script_chain,
)
from .qsub_binding import validate_qsub_binding
from .retry_index import RetryIndexError, validate_retry_index
from .series import replay_ledger
from .t126_driver import verify as verify_attempt


_HEX64 = re.compile(r"[0-9a-f]{64}")
_JOB_ID = re.compile(r"(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*")
_CLEAN_RCS = {
    0: "lower_boundary",
    20: "upper_boundary",
    21: "indeterminate",
}
_FAILURE_CLASS_BY_RC = {
    30: "member-rejected",
    31: "pre-attestation",
    32: "reservation-unavailable",
    33: "pre-member-infrastructure",
    34: "pre-member-infrastructure",
    124: "pre-member-infrastructure",
    129: "scheduler-terminated",
    137: "scheduler-hard-kill",
    143: "scheduler-terminated",
}
_FILE_RECORD_KEYS = {"path", "size", "sha256"}
_JOB_RESULT_KEYS = {
    "schema_version", "pbs_jobid", "driver_rc", "failure_class",
    "nonce", "job_script_sha256", "completed_epoch",
    "job_started_monotonic_ns", "completed_monotonic_ns",
    "elapsed_ns", "wmax_s",
}
_RESULT_STAGING = re.compile(
    r"\.job-result\.json\.create-[1-9][0-9]*-[0-9a-f]{16}")
# global preflight の直後に回収してよい attempt 側 staging の lifecycle 集合。
# after-publish stage は canonical と同一 inode・同一 bytes を共有する第二の名前
# にすぎないので回収は情報保存的であり、後段の fail-closed 拒否 (series の
# read-only 検証・意味検査) より前に消しても唯一の複製を失わない。この集合に
# 載らない lifecycle (targetless / stage なし) はその bytes の唯一の複製なので、
# global preflight と意味検査を終えた後の in-function apply が担当する。
# attempt stage を unlink しうる site はこの定数を参照する 2 箇所
# (`_retire_after_publish_attempt_staging` と `_reconcile_job_results`) だけで、
# 両者は同じ 1 つの定数の補集合関係を担当する。したがって同一 stage が二重に
# unlink されることは構造的に起こりえない。
_EARLY_RETIRABLE_LIFECYCLES = ("after-publish",)


class CollectionError(QualificationArtifactError):
    """Post-job evidence cannot be closed without ambiguity."""


def _exact_retry_index(value: object, label: str) -> int:
    try:
        return validate_retry_index(value)
    except RetryIndexError as exc:
        raise CollectionError(f"{label} retry index is not exact") from exc


def _normalize_job_id(value: object) -> str:
    if type(value) is not str or _JOB_ID.fullmatch(value) is None:
        raise CollectionError("job id must match the strict scheduler grammar")
    return value[2:] if value.startswith("0:") else value


def _assert_static_nonsymlink_path(
        root: Path, path: Path, label: str) -> None:
    """Reject every pre-existing symlink component immediately before a read."""
    try:
        relative = path.absolute().relative_to(root.absolute())
    except ValueError as exc:
        raise CollectionError(f"{label} escapes its canonical root") from exc
    current = root
    components = (Path("."), *relative.parents[::-1], relative)
    checked: set[Path] = set()
    for suffix in components:
        candidate = current if suffix == Path(".") else root / suffix
        if candidate in checked:
            continue
        checked.add(candidate)
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise CollectionError(f"{label} path contains a symlink: {candidate}")


def _parse_accounting(data: bytes) -> dict[str, Any]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CollectionError("accounting evidence is not UTF-8") from exc
    fields: dict[str, list[str]] = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if "=" not in raw:
            raise CollectionError("accounting line is not exact key=value")
        key, value = (item.strip() for item in raw.split("=", 1))
        normalized = re.sub(r"[\s_]+", "_", key.lower())
        fields.setdefault(normalized, []).append(value)
    request_values = []
    for key in ("request_id", "request_name", "nqsv_request_id"):
        request_values.extend(fields.get(key, ()))
    exit_values = fields.get("exit_status", ())
    if len(request_values) != 1 or len(exit_values) != 1:
        raise CollectionError(
            "accounting requires one exact request ID and one Exit_status")
    try:
        exit_status = int(exit_values[0], 10)
    except ValueError as exc:
        raise CollectionError("accounting Exit_status is not an integer") from exc
    wall_values = []
    for key, values in fields.items():
        if key.startswith("resources_used") and "walltime" in key:
            wall_values.extend(values)
    if len(wall_values) != 1:
        raise CollectionError("accounting resources_used closure is missing")
    raw_walltime = wall_values[0]
    if raw_walltime.isdigit():
        walltime_s = int(raw_walltime)
    else:
        match = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", raw_walltime)
        if match is None:
            raise CollectionError("accounting walltime is not exact seconds/HMS")
        walltime_s = (
            int(match.group(1)) * 3600
            + int(match.group(2)) * 60 + int(match.group(3)))
    return {
        "job_id": _normalize_job_id(request_values[0]),
        "exit_status": exit_status,
        "fields": fields,
        "walltime_s": walltime_s,
    }


def _validate_accounting_result_anchor(
        accounting: Mapping[str, Any], *, job_id: str, wmax_s: int,
        job_result: Mapping[str, Any] | None = None,
        declared_exit_status: int | None = None) -> None:
    """Single producer/consumer anchor for accounting job ID and exit status."""
    expected_rc = (
        job_result["driver_rc"] if job_result is not None
        else declared_exit_status)
    if (accounting["job_id"] != _normalize_job_id(job_id)
            or accounting["walltime_s"] > wmax_s
            or (expected_rc is not None
                and accounting["exit_status"] != expected_rc)
            or (job_result is not None
                and declared_exit_status is not None
                and job_result["driver_rc"] != declared_exit_status)):
        raise CollectionError(
            "accounting/job-result canonical job ID, exit status, or Wmax mismatch")


def _scheduler_suffix(job_id: str) -> str:
    normalized = _normalize_job_id(job_id)
    match = re.match(r"([0-9]+)", normalized)
    return match.group(1) if match else normalized.split(".", 1)[0]


def _validate_scheduler_files(
        stdout_path: Path, stderr_path: Path, job_id: str,
        stdout_identity: tuple[int, int, int, int],
        stderr_identity: tuple[int, int, int, int]) -> None:
    suffix = re.escape(_scheduler_suffix(job_id))
    if (re.fullmatch(rf".+\.o{suffix}", stdout_path.name) is None
            or re.fullmatch(rf".+\.e{suffix}", stderr_path.name) is None):
        raise CollectionError("scheduler stdout/stderr names are not canonical .o/.e")
    if ((stdout_identity[0], stdout_identity[1])
            == (stderr_identity[0], stderr_identity[1])
            or stdout_path.absolute() == stderr_path.absolute()):
        raise CollectionError("scheduler stdout/stderr must be distinct files")


def _safe_record_path(attempt_dir: Path, row: object, label: str) -> Path:
    if type(row) is not dict or set(row) != _FILE_RECORD_KEYS:
        raise CollectionError(f"{label} file record key set mismatch")
    relative = row["path"]
    if type(relative) is not str or not relative:
        raise CollectionError(f"{label} file record path is empty")
    path = safe_relative_path(attempt_dir, relative, label)
    if file_record(path, relative_to=attempt_dir) != row:
        raise CollectionError(f"{label} file record hash/size mismatch")
    return path


def _manifest(attempt_dir: Path, *, exclude: set[str]) -> list[dict[str, Any]]:
    records = []
    for path in sorted(attempt_dir.rglob("*")):
        if path.is_symlink():
            raise CollectionError(f"attempt closure contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(attempt_dir).as_posix()
        if relative in exclude:
            continue
        if any(part.startswith(".") and ".create-" in part
               for part in PurePosixPath(relative).parts):
            raise CollectionError("attempt closure contains abandoned staging bytes")
        records.append(file_record(path, relative_to=attempt_dir))
    if not records:
        raise CollectionError("attempt closure is empty")
    return records


def derive_failure_class(
        *, accounting_rc: int, observations_recorded: int,
        series_present: bool, job_result_present: bool,
        recovered_pre_attempt: bool = False,
) -> str:
    """Closed-table failure classification; producer text is never authority."""
    if type(accounting_rc) is not int:
        raise CollectionError("accounting rc is not exact int")
    if accounting_rc in _CLEAN_RCS:
        if series_present:
            return "none"
        return "clean-rc-without-series-result"
    if recovered_pre_attempt:
        result = "pre-attempt-infrastructure"
    elif accounting_rc in _FAILURE_CLASS_BY_RC:
        result = _FAILURE_CLASS_BY_RC[accounting_rc]
    else:
        result = "unregistered-scheduler-failure"
    if observations_recorded > 0 and result in {
            "pre-attempt-infrastructure", "pre-member-infrastructure",
            "pre-attestation", "reservation-unavailable"}:
        return "post-observation-infrastructure"
    return result


def _has_accounting_result_mismatch(
        job_result: Mapping[str, Any] | None,
        accounting: Mapping[str, Any], *,
        accounting_failure: str,
        series_terminal: str | None = None) -> bool:
    """Classify the shared scheduler/result meaning edge for collect and verify."""
    return bool(
        job_result is not None
        and (job_result["driver_rc"] != accounting["exit_status"]
             or job_result["failure_class"] != accounting_failure
             or (series_terminal is not None
                 and _CLEAN_RCS.get(accounting["exit_status"]) is not None
                 and _CLEAN_RCS[accounting["exit_status"]]
                 != series_terminal)))


def _schema_validate(name: str, value: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:  # pragma: no cover - production dependency gate
        raise CollectionError("jsonschema is required for receipt validation") from exc
    schema_path = Path(__file__).resolve().parent / name
    try:
        schema = json.loads(read_regular_file(schema_path))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError(f"invalid bundled receipt schema: {name}") from exc
    errors = sorted(
        Draft7Validator(schema).iter_errors(dict(value)),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        raise CollectionError(
            f"{name} validation failed at {list(first.absolute_path)}: "
            f"{first.message}")


def _load_submission_snapshot(attempt_dir: Path) -> tuple[dict[str, Any], bytes]:
    manifest = load_json_strict(attempt_dir / "source/source-snapshots.json")
    if type(manifest) is not dict or "submission_receipt" not in manifest:
        raise CollectionError("submission snapshot manifest is missing")
    row = manifest["submission_receipt"]
    path = _safe_record_path(attempt_dir, {
        "path": row.get("path"), "size": row.get("size"), "sha256": row.get("sha256"),
    }, "submission snapshot")
    data = read_regular_file(path)
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError("submission snapshot JSON is invalid") from exc
    if type(value) is not dict:
        raise CollectionError("submission snapshot must be an object")
    return value, data


def _copy_external(
        capability, relative: str, source: Path, *,
        expected_bytes: bytes | None = None) -> Path:
    data = read_regular_file(source)
    if expected_bytes is not None and data != expected_bytes:
        raise CollectionError(f"external evidence differs from bound snapshot: {source}")
    return create_or_verify_bytes(capability, relative, data)


def _recover_pre_attempt(
        *, repo_root: Path, root: QualificationRoot, capability,
        attempt_id: str, submission_receipt: Path,
        submission_bytes: bytes) -> bool:
    """Create the immutable failure namespace when SIGKILL beat job startup."""
    attempt_dir = root.path / "attempts" / attempt_id
    if attempt_dir.exists() or attempt_dir.is_symlink():
        return False
    submit_bytes = submission_bytes
    try:
        submit = json.loads(submit_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError(
            "pre-attempt submission receipt is invalid") from exc
    if (type(submit) is not dict
            or submit.get("qualification_attempt_id") != attempt_id
            or _HEX64.fullmatch(
                submit.get("qualification_series_id", "")) is None):
        raise CollectionError(
            "pre-attempt submission does not bind the requested attempt")
    series_path = submission_receipt.with_name("series-identity.json")
    series_preimage = load_json_strict(series_path)
    series_id = series_identity(series_preimage)
    if series_id != submit["qualification_series_id"]:
        raise CollectionError("pre-attempt series identity mismatch")
    attempt_preimage = {
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": submit["job_id"],
        "nonce": submit["nonce"],
        "retry_index": submit["retry_index"],
        "submission_intent_sha256": submit["submission_intent_sha256"],
    }
    if attempt_identity(attempt_preimage) != attempt_id:
        raise CollectionError("pre-attempt identity does not recompute")
    try:
        protocol_bytes = subprocess.check_output(
            ["git", "-C", str(repo_root), "cat-file", "blob",
             f"{series_preimage['superproject_commit']}:"
             "orchestrator/qualification/t126_control_v1.json"],
            stderr=subprocess.DEVNULL, timeout=20)
        protocol = validate_protocol(json.loads(protocol_bytes))
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise CollectionError(
            f"cannot recover committed pre-attempt protocol: {exc}") from exc
    layout = create_attempt(
        root, capability, series_id=series_id, attempt_id=attempt_id)
    prefix = f"attempts/{attempt_id}"
    create_or_verify_json(capability, f"{prefix}/protocol.json", protocol)
    create_or_verify_json(
        capability, f"{prefix}/series-identity.json", series_preimage)
    create_or_verify_json(
        capability, f"{prefix}/attempt-identity.json", attempt_preimage)
    rows = {}
    for name in ("campaign_lock", "wal"):
        source = series_preimage["source_snapshots"][name]
        relative = source["path"]
        try:
            data = subprocess.check_output(
                ["git", "-C", str(repo_root), "cat-file", "blob",
                 f"{series_preimage['superproject_commit']}:{relative}"],
                stderr=subprocess.DEVNULL, timeout=20)
        except (OSError, subprocess.SubprocessError) as exc:
            raise CollectionError(
                f"cannot recover committed {name} snapshot: {exc}") from exc
        snapshot_name = (
            "campaign.lock.snapshot" if name == "campaign_lock"
            else "source-wal.snapshot.jsonl")
        target = create_or_verify_bytes(
            capability, f"{prefix}/source/{snapshot_name}", data)
        rows[name] = {
            "original_path": relative,
            **file_record(target, relative_to=layout.attempt_dir),
        }
    submit_target = create_or_verify_bytes(
        capability, f"{prefix}/source/submission-receipt.snapshot.json",
        submit_bytes)
    rows["submission_receipt"] = {
        "original_path": submission_receipt.relative_to(repo_root).as_posix(),
        **file_record(submit_target, relative_to=layout.attempt_dir),
    }
    binding_source = (
        submission_receipt
        if submit.get("schema_version") == "t126-qualification-recovered-submit/v1"
        else submission_receipt.with_name("qsub-binding.json"))
    binding_target = create_or_verify_bytes(
        capability, f"{prefix}/source/qsub-binding.snapshot.json",
        read_regular_file(binding_source))
    rows["qsub_binding"] = {
        "original_path": binding_source.relative_to(repo_root).as_posix(),
        **file_record(binding_target, relative_to=layout.attempt_dir),
    }
    invocation_source = submission_receipt.with_name("qsub-invocation.json")
    invocation_target = create_or_verify_bytes(
        capability, f"{prefix}/source/qsub-invocation.snapshot.json",
        read_regular_file(invocation_source))
    rows["qsub_invocation"] = {
        "original_path": invocation_source.relative_to(repo_root).as_posix(),
        **file_record(invocation_target, relative_to=layout.attempt_dir),
    }
    create_or_verify_json(
        capability, f"{prefix}/source/source-snapshots.json", {
            "schema_version": "t126-qualification-source-snapshots/v1",
            **rows,
        })
    return True


def _submission_evidence(
        path: Path, *, attempt_id: str,
        qualification_root: Path) -> tuple[dict[str, Any], bytes, bool]:
    """Return a final receipt or a fail-closed reconstruction from qsub binding."""
    _assert_static_nonsymlink_path(
        qualification_root, path, "submission evidence")
    raw = read_regular_file(path)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError("submission evidence JSON is invalid") from exc
    if type(value) is not dict:
        raise CollectionError("submission evidence must be an object")
    if value.get("schema_version") != "t126-qsub-binding/v2":
        return value, raw, False
    value = load_json_strict(path)
    intent_path = path.with_name("submission-intent.json")
    identity_path = path.with_name("series-identity.json")
    _assert_static_nonsymlink_path(
        qualification_root, intent_path, "submission intent")
    _assert_static_nonsymlink_path(
        qualification_root, identity_path, "submission series identity")
    intent = load_json_strict(intent_path)
    intent_retry_index = _exact_retry_index(
        intent.get("retry_index"), "submission intent")
    invocation_path = path.with_name("qsub-invocation.json")
    invocation = load_json_strict(invocation_path)
    invocation_sha = sha256_bytes(read_regular_file(invocation_path))
    preimage = load_json_strict(identity_path)
    series_id = series_identity(preimage)
    intent_sha = sha256_bytes(read_regular_file(intent_path))
    binding = validate_qsub_binding(
        value, expected_nonce=intent.get("nonce"),
        expected_intent_sha256=intent_sha,
        expected_invocation_sha256=invocation_sha,
        expected_retry_index=intent_retry_index)
    invocation_retry_index = _exact_retry_index(
        invocation.get("retry_index"), "qsub invocation")
    if (set(invocation) != {
            "nonce", "retry_index", "submission_intent_sha256"}
            or invocation.get("nonce") != binding["nonce"]
            or invocation_retry_index != binding["retry_index"]
            or invocation.get("submission_intent_sha256")
            != binding["submission_intent_sha256"]):
        raise CollectionError("qsub invocation claim semantics mismatch")
    attempt_preimage = {
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": binding["job_id"],
        "nonce": binding["nonce"],
        "retry_index": intent_retry_index,
        "submission_intent_sha256": intent_sha,
    }
    if (intent.get("qualification_series_id") != series_id
            or attempt_identity(attempt_preimage) != attempt_id):
        raise CollectionError("qsub binding cannot reconstruct attempt identity")
    recovered = {
        "schema_version": "t126-qualification-recovered-submit/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
        "job_id": binding["job_id"],
        "nonce": binding["nonce"],
        "retry_index": intent_retry_index,
        "submission_intent_sha256": intent_sha,
        "qsub_invocation_sha256": invocation_sha,
        "job_script_sha256":
            preimage["script_identity"]["tools/pegasus/t126_qualification.sh"],
        "qsub_binding_sha256": sha256_bytes(raw),
        "source_commit": preimage["superproject_commit"],
        "source_tree": preimage["superproject_tree"],
        "ccbench_gitlink": preimage["ccbench_gitlink"],
    }
    data = json.dumps(
        recovered, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii") + b"\n"
    return recovered, data, True


def _require_submitted_binding(
        *, repo_root: Path, capability, attempt_id: str,
        submission_path: Path, submit: Mapping[str, Any],
) -> tuple[SeriesAttemptLedger, Any]:
    """Verify the canonical ledger binding before any attempt artifact write."""
    series_id = submit.get("qualification_series_id")
    retry_index = _exact_retry_index(
        submit.get("retry_index"), "submission evidence")
    nonce = submit.get("nonce")
    job_id = _normalize_job_id(submit.get("job_id"))
    intent_sha = submit.get("submission_intent_sha256")
    expected_name = (
        "qsub-binding.json"
        if submit.get("schema_version")
        == "t126-qualification-recovered-submit/v1"
        else "submit-receipt.json")
    expected_path = (
        capability.root / "submissions" / str(nonce) / expected_name)
    _assert_static_nonsymlink_path(
        capability.root, submission_path, "submission evidence")
    if submission_path.absolute() != expected_path.absolute():
        raise CollectionError(
            "submission evidence is outside its canonical nonce path")
    if (_HEX64.fullmatch(series_id or "") is None
            or type(nonce) is not str
            or type(intent_sha) is not str
            or _HEX64.fullmatch(intent_sha) is None):
        raise CollectionError("submission cannot bind a canonical ledger attempt")
    expected_attempt = attempt_identity({
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": job_id,
        "nonce": nonce,
        "retry_index": retry_index,
        "submission_intent_sha256": intent_sha,
    })
    if expected_attempt != attempt_id:
        raise CollectionError("submission/attempt preimage mismatch")
    binding_path = (
        submission_path if submit.get("schema_version")
        == "t126-qualification-recovered-submit/v1"
        else submission_path.with_name("qsub-binding.json"))
    _assert_static_nonsymlink_path(
        capability.root, binding_path, "qsub binding")
    binding_bytes = read_regular_file(binding_path)
    invocation_path = binding_path.with_name("qsub-invocation.json")
    invocation_bytes = read_regular_file(invocation_path)
    invocation = load_json_strict(invocation_path)
    invocation_retry_index = _exact_retry_index(
        invocation.get("retry_index"), "qsub invocation")
    invocation_sha = sha256_bytes(invocation_bytes)
    binding = load_json_strict(binding_path)
    validate_qsub_binding(
        binding, expected_nonce=nonce,
        expected_intent_sha256=intent_sha,
        expected_invocation_sha256=invocation_sha,
        expected_retry_index=retry_index,
        expected_job_id=submit.get("job_id"))
    if (set(invocation) != {
            "nonce", "retry_index", "submission_intent_sha256"}
            or invocation.get("nonce") != nonce
            or invocation_retry_index != retry_index
            or invocation.get("submission_intent_sha256") != intent_sha
            or submit.get("qsub_invocation_sha256") != invocation_sha):
        raise CollectionError("submission invocation proof mismatch")
    if _normalize_job_id(binding["job_id"]) != job_id:
        raise CollectionError("qsub binding does not match submission")
    protocol = load_protocol(
        repo_root / "orchestrator/qualification/t126_control_v1.json")
    ledger = SeriesAttemptLedger(
        capability, series_id, protocol["retry"]["eligible_reasons"])
    state = ledger.replay
    if (state.state not in {
            "initial_submitted", "retry_submitted", "outcome_pending",
            "initial_failed", "retry_failed", "terminal"}
            or state.last_attempt_id != attempt_id
            or state.last_retry_index != retry_index
            or state.last_job_id != job_id
            or state.last_nonce != nonce
            or state.last_submission_intent_sha256 != intent_sha
            or state.last_qsub_invocation_sha256 != invocation_sha
            or state.last_submission_evidence_sha256
            != sha256_bytes(binding_bytes)):
        raise CollectionError(
            "series-global ledger does not exactly bind the submitted attempt")
    return ledger, state


def _job_result_fields(value: Mapping[str, Any], submit: Mapping[str, Any]) -> None:
    if (set(value) != _JOB_RESULT_KEYS
            or value["schema_version"] != "t126-qualification-job-result/v1"
            or _normalize_job_id(value["pbs_jobid"])
            != _normalize_job_id(submit["job_id"])
            or value["nonce"] != submit["nonce"]
            or value["job_script_sha256"] != submit["job_script_sha256"]
            or type(value["driver_rc"]) is not int
            or value["failure_class"] not in {
                "none", "member-rejected", "pre-attestation",
                "reservation-unavailable", "pre-member-infrastructure",
                "scheduler-hard-kill", "scheduler-terminated",
                "unregistered-scheduler-failure",
            }
            or type(value["completed_epoch"]) is not int
            or value["completed_epoch"] < 0
            or type(value["job_started_monotonic_ns"]) is not int
            or type(value["completed_monotonic_ns"]) is not int
            or type(value["elapsed_ns"]) is not int
            or type(value["wmax_s"]) is not int
            or value["elapsed_ns"] < 0
            or value["elapsed_ns"] != (
                value["completed_monotonic_ns"]
                - value["job_started_monotonic_ns"])
            or value["elapsed_ns"] > value["wmax_s"] * 1_000_000_000):
        raise CollectionError("job-result terminal identity/envelope is invalid")


def _validate_job_result_semantics(
        value: Mapping[str, Any], *, submit: Mapping[str, Any],
        protocol: Mapping[str, Any], series_preimage: Mapping[str, Any],
        series: Mapping[str, Any] | None) -> None:
    """One collect/public classifier for identity, Wmax, and series timing."""
    _job_result_fields(value, submit)
    verify_submission_script_chain(
        submission=submit, preimage=series_preimage, job_result=value)
    if value["wmax_s"] != protocol["timing"]["wmax_s"]:
        raise CollectionError("job-result deadline semantics mismatch")
    if series is None:
        return
    timing = series.get("timing_envelope")
    if (type(timing) is not dict
            or value["job_started_monotonic_ns"]
            != timing.get("job_started_monotonic_ns")
            or value["completed_monotonic_ns"]
            < timing.get("completed_monotonic_ns", -1)
            or value["completed_monotonic_ns"]
            - timing.get("job_started_monotonic_ns", 0)
            > protocol["timing"]["wmax_s"] * 1_000_000_000):
        raise CollectionError("job-result/series timing semantics mismatch")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _result_entry_stat(path: Path, *, expected_nlink: int, label: str):
    try:
        current = path.lstat()
    except OSError as exc:
        raise CollectionError(f"{label} cannot be inspected: {exc}") from exc
    if (stat.S_ISLNK(current.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or current.st_uid != os.getuid()
            or stat.S_IMODE(current.st_mode) != 0o600
            or current.st_nlink != expected_nlink):
        raise CollectionError(
            f"{label} lifecycle owner/mode/nlink mismatch")
    return current


def _decode_job_result(
        path: Path, submit: Mapping[str, Any],
) -> tuple[str, bytes, dict[str, Any] | None]:
    data = read_regular_file(path)
    try:
        value = json.loads(data)
        if type(value) is not dict:
            raise ValueError("not an object")
        _job_result_fields(value, submit)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError,
            KeyError, CollectionError):
        return "invalid", data, None
    return "valid", data, value


def _decode_structural_job_result(data: bytes) -> dict[str, Any] | None:
    """Recognize only the exact JSON object envelope before semantic gates."""
    try:
        value = json.loads(data)
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii") + b"\n"
    except (UnicodeDecodeError, json.JSONDecodeError, UnicodeEncodeError,
            ValueError):
        return None
    if (type(value) is not dict or set(value) != _JOB_RESULT_KEYS
            or canonical != data):
        return None
    return value


def _reconcile_result_namespace(
        directory: Path, *, submit: Mapping[str, Any], label: str,
) -> tuple[
        str, bytes | None, dict[str, Any] | None, Path | None, str | None]:
    """Preflight one publisher namespace without mutating either namespace."""
    if not directory.exists() and not directory.is_symlink():
        return "missing", None, None, None, None
    if directory.is_symlink() or not directory.is_dir():
        raise CollectionError(f"{label} job-result namespace is unsafe")
    target = directory / "job-result.json"
    prefixed = [
        entry for entry in directory.iterdir()
        if entry.name.startswith(".job-result.json.create-")]
    if any(_RESULT_STAGING.fullmatch(entry.name) is None for entry in prefixed):
        raise CollectionError(f"{label} job-result staging name mismatch")
    if len(prefixed) > 1:
        raise CollectionError(f"{label} has multiple job-result staging entries")
    stage = prefixed[0] if prefixed else None
    if not target.exists() and not target.is_symlink():
        if stage is not None:
            _result_entry_stat(
                stage, expected_nlink=1,
                label=f"{label} targetless staging")
        return (
            "missing", None, None, stage,
            "targetless" if stage is not None else None)
    target_links = 2 if stage is not None else 1
    target_stat = _result_entry_stat(
        target, expected_nlink=target_links,
        label=f"{label} canonical job-result")
    state, data, value = _decode_job_result(target, submit)
    if stage is not None:
        stage_stat = _result_entry_stat(
            stage, expected_nlink=2,
            label=f"{label} after-publish staging")
        if ((stage_stat.st_dev, stage_stat.st_ino)
                != (target_stat.st_dev, target_stat.st_ino)
                or read_regular_file(stage) != data):
            raise CollectionError(
                f"{label} after-publish inode/bytes mismatch")
    return (
        state, data, value, stage,
        "after-publish" if stage is not None else None)


def _apply_result_reconciliation(
        directory: Path, stage: Path | None, lifecycle: str | None) -> None:
    """Apply a previously validated cleanup only after global preflight."""
    if stage is None:
        return
    if lifecycle == "after-publish":
        _fsync_directory(directory)
    elif lifecycle != "targetless":
        raise CollectionError("job-result reconciliation lifecycle is invalid")
    stage.unlink()
    _fsync_directory(directory)


def _job_staging_directory(root: Path, submit: Mapping[str, Any]) -> Path:
    job_id = _normalize_job_id(submit.get("job_id"))
    nonce = submit.get("nonce")
    if type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise CollectionError("submission nonce cannot bind job staging")
    return root / "job-staging" / f"{job_id}.{nonce}"


def _rejected_result_evidence(
        qualification_root: Path, source: Path) -> dict[str, Any]:
    current = source.lstat()
    return {
        "schema_version": "t126-rejected-job-result-evidence/v1",
        "source_path": source.relative_to(qualification_root).as_posix(),
        "st_mode": current.st_mode,
        "st_uid": current.st_uid,
        "st_gid": current.st_gid,
        "st_dev": current.st_dev,
        "st_ino": current.st_ino,
        "st_nlink": current.st_nlink,
        "st_size": current.st_size,
        "sha256": sha256_bytes(read_regular_file(source)),
    }


def _preflight_job_result_namespaces(
        *, capability, attempt_dir: Path, submit: Mapping[str, Any],
) -> tuple[
        tuple[str, bytes | None, dict[str, Any] | None, Path | None,
              str | None],
        tuple[str, bytes | None, dict[str, Any] | None, Path | None,
              str | None]]:
    """Preflight both publisher namespaces before either one is mutated."""
    attempt_preflight = _reconcile_result_namespace(
        attempt_dir, submit=submit, label="attempt")
    staging_dir = _job_staging_directory(capability.root, submit)
    staging_preflight = _reconcile_result_namespace(
        staging_dir, submit=submit, label="early job-staging")
    return attempt_preflight, staging_preflight


def _retire_after_publish_attempt_staging(
        attempt_dir: Path,
        attempt_preflight: tuple[
            str, bytes | None, dict[str, Any] | None, Path | None,
            str | None]) -> None:
    """Retire the attempt stage that is only a second name for the canonical.

    An after-publish stage shares inode and bytes with the canonical entry, so
    unlinking it loses no information. A targetless stage is the only copy of
    its bytes, and the structural fail-closed rejections that still run below
    (series verification, series ledger, semantic gates) must be able to refuse
    without mutating it; targetless staging is therefore left to the in-function
    apply that runs after the global preflight and the semantic checks.
    """
    (_state, _bytes, _value, stage, lifecycle) = attempt_preflight
    if lifecycle not in _EARLY_RETIRABLE_LIFECYCLES:
        return
    _apply_result_reconciliation(attempt_dir, stage, lifecycle)


def _reconcile_job_results(
        *, capability, attempt_dir: Path, submit: Mapping[str, Any],
        protocol: Mapping[str, Any], series_preimage: Mapping[str, Any],
        series: Mapping[str, Any] | None, accounting: Mapping[str, Any],
        observations_recorded: int, recovered_pre_attempt: bool,
        attempt_preflight: tuple[
            str, bytes | None, dict[str, Any] | None, Path | None,
            str | None],
        staging_preflight: tuple[
            str, bytes | None, dict[str, Any] | None, Path | None,
            str | None],
) -> tuple[str, bytes | None, dict[str, Any] | None]:
    """Resolve attempt and early-job namespaces into one monotonic canonical."""
    (attempt_state, attempt_bytes, attempt_value,
     attempt_stage, attempt_lifecycle) = attempt_preflight
    staging_dir = _job_staging_directory(capability.root, submit)
    (staging_state, staging_bytes, staging_value,
     staging_stage, staging_lifecycle) = staging_preflight
    semantic_rejection = None
    if staging_state == "valid":
        try:
            _validate_job_result_semantics(
                staging_value, submit=submit, protocol=protocol,
                series_preimage=series_preimage, series=series)
            expected_failure = derive_failure_class(
                accounting_rc=accounting["exit_status"],
                observations_recorded=observations_recorded,
                series_present=series is not None,
                job_result_present=True,
                recovered_pre_attempt=recovered_pre_attempt,
            )
            if (staging_value["driver_rc"] != accounting["exit_status"]
                    or staging_value["failure_class"] != expected_failure):
                raise CollectionError(
                    "early job-result RC/class semantics mismatch")
        except (CollectionError, QualificationArtifactError) as exc:
            semantic_rejection = f"{type(exc).__name__}: {exc}"
    rejection_marker = staging_dir / "target-rejection.json"
    rejection_value = None
    rejection_bytes = None
    if rejection_marker.exists() or rejection_marker.is_symlink():
        marker_stat = _result_entry_stat(
            rejection_marker, expected_nlink=1,
            label="early job-staging target rejection")
        if stat.S_IMODE(marker_stat.st_mode) != 0o600:
            raise CollectionError("target rejection marker mode mismatch")
        rejection_bytes = read_regular_file(rejection_marker)
        rejection_value = load_json_strict(rejection_marker)
        if (set(rejection_value) != {
                "schema_version", "qualification_series_id",
                "qualification_attempt_id", "pbs_job_id", "nonce", "reason"}
                or rejection_value.get("schema_version")
                != "t126-job-result-target-rejection/v1"
                or rejection_value.get("qualification_series_id")
                != submit["qualification_series_id"]
                or rejection_value.get("qualification_attempt_id")
                != submit["qualification_attempt_id"]
                or type(rejection_value.get("pbs_job_id")) is not str
                or _normalize_job_id(rejection_value.get("pbs_job_id"))
                != _normalize_job_id(submit["job_id"])
                or rejection_value.get("nonce") != submit["nonce"]
                or rejection_value.get("reason")
                != "submitted-attempt-target-invalid"):
            raise CollectionError(
                "target rejection marker identity mismatch")
        if staging_state == "missing" and staging_stage is None:
            raise CollectionError(
                "target rejection marker lacks rejected result bytes")
    if (staging_state == "invalid" or semantic_rejection is not None
            or rejection_value is not None):
        structural_rejected = (
            _decode_structural_job_result(staging_bytes)
            if staging_bytes is not None else None)
        semantic_conflict = bool(
            attempt_state == "valid"
            and structural_rejected is not None
            and attempt_bytes != staging_bytes)
        rejected_target = staging_dir / "job-result.json"
        if not rejected_target.exists() and not rejected_target.is_symlink():
            rejected_target = staging_stage
        if rejected_target is None:
            raise CollectionError("rejected target bytes are unavailable")
        rejected_bytes = read_regular_file(rejected_target)
        result_copy = create_or_verify_bytes(
            capability,
            f"attempts/{attempt_dir.name}/rejected-evidence/"
            "early-job-result.bytes",
            rejected_bytes)
        evidence = _rejected_result_evidence(
            capability.root, rejected_target)
        evidence["preserved_result"] = file_record(
            result_copy, relative_to=attempt_dir)
        if semantic_rejection is not None:
            evidence["semantic_rejection"] = semantic_rejection
        if rejection_value is not None:
            marker_copy = create_or_verify_bytes(
                capability,
                f"attempts/{attempt_dir.name}/rejected-evidence/"
                "target-rejection.bytes",
                rejection_bytes)
            evidence["target_rejection"] = rejection_value
            evidence["preserved_marker"] = file_record(
                marker_copy, relative_to=attempt_dir)
        create_or_verify_json(
            capability,
            f"attempts/{attempt_dir.name}/rejected-evidence/"
            "early-job-result.json",
            evidence)
        if semantic_conflict:
            return "semantic-conflict", attempt_bytes, attempt_value
        # この fail-closed が守る公開側 gate は `_verify_post_job_receipt` の
        # `pointer_missing_canonical` であり、そこでの `canonical_state ==
        # "valid"` は `_validate_job_result_semantics` を通った意味的な判定で
        # ある。したがって発火条件も同じ意味判定へ揃える。構造だけ valid で
        # 意味検証に落ちる canonical は、公開側でも `canonical_state =
        # "invalid"` になり `job-result-publication-failed` の failure receipt が
        # 期待値として一致するので、pre-image どおりそこへ閉じるのが正しい。
        # 構造判定のまま raise すると受理集合を pre-image より狭め、閉じられた
        # はずの attempt を `initial_submitted` へ恒久固着させる。
        canonical_conflicts = attempt_state == "valid"
        if canonical_conflicts:
            try:
                _validate_job_result_semantics(
                    attempt_value, submit=submit, protocol=protocol,
                    series_preimage=series_preimage, series=series)
            except (CollectionError, QualificationArtifactError):
                canonical_conflicts = False
        if canonical_conflicts:
            raise CollectionError(
                "attempt canonical conflicts with a rejected early job-result")
        return "invalid", rejected_bytes, None
    if (staging_state != "missing"
            and attempt_state != "missing"
            and attempt_bytes != staging_bytes):
        raise CollectionError(
            "attempt and early job-staging canonical bytes differ")
    if attempt_lifecycle not in _EARLY_RETIRABLE_LIFECYCLES:
        # 早期回収した lifecycle の補集合だけをここで回収する。
        # `attempt_lifecycle is None` (stage なし) でもこの条件は真になるが、
        # `_apply_result_reconciliation` は `stage is None` で即 return するため
        # 挙動は不変である (`_reconcile_result_namespace` は stage を返さない
        # ときだけ lifecycle を None にするので、両者は常に同時に None になる)。
        _apply_result_reconciliation(
            attempt_dir, attempt_stage, attempt_lifecycle)
    _apply_result_reconciliation(
        staging_dir, staging_stage, staging_lifecycle)
    if staging_state == "missing":
        return attempt_state, attempt_bytes, attempt_value
    target = staging_dir / "job-result.json"
    canonical = attempt_dir / "job-result.json"
    if attempt_state == "missing":
        create_or_verify_bytes(
            capability,
            f"attempts/{attempt_dir.name}/job-result.json",
            staging_bytes)
    _fsync_directory(staging_dir)
    target.unlink()
    _fsync_directory(staging_dir)
    return _decode_job_result(canonical, submit)


def _assert_job_staging_closed(
        qualification_root: Path, submit: Mapping[str, Any], *,
        attempt_dir: Path | None = None) -> Mapping[str, Any] | None:
    directory = _job_staging_directory(qualification_root, submit)
    if not directory.exists() and not directory.is_symlink():
        return None
    if directory.is_symlink() or not directory.is_dir():
        raise CollectionError("early job-staging namespace is unsafe")
    remaining = [
        entry for entry in directory.iterdir()
        if entry.name == "job-result.json"
        or entry.name == "target-rejection.json"
        or entry.name.startswith(".job-result.json.create-")]
    if not remaining:
        return None
    rejected_path = (
        attempt_dir / "rejected-evidence/early-job-result.json"
        if attempt_dir is not None else None)
    if (rejected_path is not None and rejected_path.is_file()
            and not rejected_path.is_symlink()):
        evidence = load_json_strict(rejected_path)
        required = {
            "schema_version", "source_path", "st_mode", "st_uid", "st_gid",
            "st_dev", "st_ino", "st_nlink", "st_size", "sha256",
            "preserved_result",
        }
        optional = {
            "semantic_rejection", "target_rejection", "preserved_marker"}
        if (not required.issubset(evidence)
                or not set(evidence).issubset(required | optional)
                or evidence.get("schema_version")
                != "t126-rejected-job-result-evidence/v1"
                or ("target_rejection" in evidence)
                != ("preserved_marker" in evidence)):
            raise CollectionError(
                "rejected job-result evidence shape is not exact")
        try:
            target = qualification_root / evidence["source_path"]
            target.relative_to(directory)
        except (KeyError, TypeError, ValueError):
            target = directory / ".invalid-rejected-source"
        if (target.parent == directory
                and (target.name == "job-result.json"
                     or _RESULT_STAGING.fullmatch(target.name) is not None)
                and target.is_file() and not target.is_symlink()):
            current = _rejected_result_evidence(
                qualification_root, target)
            if all(evidence.get(key) == value
                   for key, value in current.items()):
                preserved = _safe_record_path(
                    attempt_dir, evidence["preserved_result"],
                    "preserved rejected job-result")
                expected_preserved = (
                    attempt_dir
                    / "rejected-evidence/early-job-result.bytes")
                if preserved.absolute() != expected_preserved.absolute():
                    raise CollectionError(
                        "preserved rejected job-result path is not canonical")
                if read_regular_file(preserved) == read_regular_file(target):
                    marker = directory / "target-rejection.json"
                    if not marker.exists() and not marker.is_symlink():
                        if "target_rejection" not in evidence:
                            return evidence
                    elif (marker.is_file() and not marker.is_symlink()
                          and load_json_strict(marker)
                          == evidence.get("target_rejection")):
                        preserved_marker = _safe_record_path(
                            attempt_dir, evidence["preserved_marker"],
                            "preserved target rejection")
                        expected_marker = (
                            attempt_dir
                            / "rejected-evidence/target-rejection.bytes")
                        if (preserved_marker.absolute()
                                != expected_marker.absolute()):
                            raise CollectionError(
                                "preserved target rejection path is not canonical")
                        if (read_regular_file(preserved_marker)
                                == read_regular_file(marker)):
                            return evidence
    raise CollectionError("early job-staging result is not reconciled")


def _rejected_conflict_is_semantically_invalid(
        evidence: Mapping[str, Any] | None, *, attempt_dir: Path,
        canonical_bytes: bytes | None, submit: Mapping[str, Any],
        protocol: Mapping[str, Any], series_preimage: Mapping[str, Any],
        series: Mapping[str, Any] | None, accounting: Mapping[str, Any],
        observations_recorded: int, recovered_pre_attempt: bool) -> bool:
    """Re-derive the one preserved A/B conflict admitted as publication failure."""
    if evidence is None or canonical_bytes is None:
        return False
    preserved = _safe_record_path(
        attempt_dir, evidence["preserved_result"],
        "preserved rejected job-result")
    rejected_bytes = read_regular_file(preserved)
    if rejected_bytes == canonical_bytes:
        return False
    try:
        rejected = _decode_structural_job_result(rejected_bytes)
        if rejected is None:
            return False
        _validate_job_result_semantics(
            rejected, submit=submit, protocol=protocol,
            series_preimage=series_preimage, series=series)
        expected_failure = derive_failure_class(
            accounting_rc=accounting["exit_status"],
            observations_recorded=observations_recorded,
            series_present=series is not None,
            job_result_present=True,
            recovered_pre_attempt=recovered_pre_attempt)
        if (rejected["driver_rc"] != accounting["exit_status"]
                or rejected["failure_class"] != expected_failure):
            raise CollectionError(
                "preserved early job-result RC/class semantics mismatch")
    except (KeyError, CollectionError, QualificationArtifactError):
        return True
    return False


def collect(
        *, repo_root: Path, attempt_id: str, submission_receipt: Path,
        job_result: Optional[Path], scheduler_stdout: Path,
        scheduler_stderr: Path, accounting: Path,
        fault_inject: Optional[Callable[[str], None]] = None,
) -> Path:
    """Close one attempt; every operation is exact-hash idempotent."""
    fault_inject = fault_inject or (lambda _stage: None)
    if _HEX64.fullmatch(attempt_id) is None:
        raise CollectionError("attempt id must be full lowercase sha256")
    root = QualificationRoot(repo_root)
    capability = root.issue()
    authoritative_submit, authoritative_submit_bytes, recovered_binding = (
        _submission_evidence(
            submission_receipt, attempt_id=attempt_id,
            qualification_root=capability.root))
    attempt_ledger, _ = _require_submitted_binding(
        repo_root=repo_root, capability=capability, attempt_id=attempt_id,
        submission_path=submission_receipt, submit=authoritative_submit)
    pre_protocol = load_protocol(
        repo_root / "orchestrator/qualification/t126_control_v1.json")
    pre_job_id = _normalize_job_id(authoritative_submit.get("job_id"))
    accounting_bytes = read_regular_file(accounting)
    accounting_record = _parse_accounting(accounting_bytes)
    _validate_accounting_result_anchor(
        accounting_record, job_id=pre_job_id,
        wmax_s=pre_protocol["timing"]["wmax_s"])
    stdout_bytes, stdout_identity = read_regular_file_with_identity(
        scheduler_stdout)
    stderr_bytes, stderr_identity = read_regular_file_with_identity(
        scheduler_stderr)
    _validate_scheduler_files(
        scheduler_stdout, scheduler_stderr, pre_job_id,
        stdout_identity, stderr_identity)
    recovered_pre_attempt = _recover_pre_attempt(
        repo_root=repo_root, root=root, capability=capability,
        attempt_id=attempt_id, submission_receipt=submission_receipt,
        submission_bytes=authoritative_submit_bytes)
    layout = root.layout(attempt_id)
    attempt_dir = layout.attempt_dir
    if attempt_dir.is_symlink() or not attempt_dir.is_dir():
        raise CollectionError("attempt directory is missing or unsafe")
    marker = load_json_strict(attempt_dir / "qualification-marker.json")
    protocol = load_protocol(attempt_dir / "protocol.json")
    if protocol != pre_protocol:
        raise CollectionError(
            "attempt protocol differs from accounting-first protocol")
    series_preimage = load_json_strict(attempt_dir / "series-identity.json")
    attempt_preimage = load_json_strict(attempt_dir / "attempt-identity.json")
    series_id = series_identity(series_preimage)
    if (attempt_identity(attempt_preimage) != attempt_id
            or marker.get("qualification_series_id") != series_id
            or marker.get("qualification_attempt_id") != attempt_id):
        raise CollectionError("attempt marker/identity chain mismatch")

    submit_bound, submit_snapshot_bytes = _load_submission_snapshot(attempt_dir)
    _assert_static_nonsymlink_path(
        capability.root, submission_receipt, "submission evidence")
    submit_external_bytes = read_regular_file(submission_receipt)
    if authoritative_submit_bytes != submit_snapshot_bytes:
        raise CollectionError(
            "external submission receipt differs from attempt snapshot")
    try:
        submit = json.loads(authoritative_submit_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError("submission receipt JSON is invalid") from exc
    if submit != submit_bound:
        raise CollectionError("submission receipt semantic snapshot mismatch")
    if (submit.get("schema_version") not in {
            "t126-qualification-submit-receipt/v1",
            "t126-qualification-recovered-submit/v1"}
            or submit.get("qualification_lineage") != "t126-only"
            or submit.get("authority") != "evidence-only/no-promotion"
            or submit.get("hold_enforced") is not False
            or submit.get("qualification_series_id") != series_id
            or submit.get("qualification_attempt_id") != attempt_id
            or _exact_retry_index(
                submit.get("retry_index"), "submission receipt")
            != _exact_retry_index(
                attempt_preimage.get("retry_index"), "attempt identity")):
        raise CollectionError("submission receipt identity mismatch")
    job_id = _normalize_job_id(submit.get("job_id"))
    if job_id != pre_job_id:
        raise CollectionError(
            "submission snapshot differs from accounting-first job ID")
    if (attempt_preimage.get("pbs_job_id") != job_id
            or attempt_preimage.get("nonce") != submit.get("nonce")
            or attempt_preimage.get("retry_index") != submit.get("retry_index")
            or attempt_preimage.get("submission_intent_sha256")
            != submit.get("submission_intent_sha256")):
        raise CollectionError("attempt identity is not submission-derived")

    attempt_preflight, staging_preflight = _preflight_job_result_namespaces(
        capability=capability, attempt_dir=attempt_dir, submit=submit)
    _retire_after_publish_attempt_staging(attempt_dir, attempt_preflight)

    series_path = attempt_dir / "series-result.json"
    series_present = series_path.is_file() and not series_path.is_symlink()
    series = load_json_strict(series_path) if series_present else None
    if series_present:
        verification = verify_attempt(attempt_dir)
        if verification.integrity_status != "valid":
            raise CollectionError(
                "series result failed read-only verification: "
                + "; ".join(verification.errors))
        terminal = series["terminal"]
        observations = len(series["bits"])
    else:
        terminal = None
        ledger = attempt_dir / "series-ledger.jsonl"
        if ((not ledger.is_file() or ledger.is_symlink())
                and not recovered_pre_attempt):
            raise CollectionError(
                "attempt failure is missing its canonical series ledger")
        observations = (
            0 if recovered_pre_attempt
            else replay_ledger(
                load_jsonl_strict(ledger), protocol).observations_recorded)
    canonical_state, canonical_job_result_bytes, result = (
        _reconcile_job_results(
            capability=capability, attempt_dir=attempt_dir, submit=submit,
            protocol=protocol, series_preimage=series_preimage,
            series=series, accounting=accounting_record,
            observations_recorded=observations,
            recovered_pre_attempt=recovered_pre_attempt,
            attempt_preflight=attempt_preflight,
            staging_preflight=staging_preflight))
    canonical_job_result = attempt_dir / "job-result.json"
    if job_result is not None:
        external_job_result_bytes = read_regular_file(job_result)
        if canonical_state != "valid":
            raise CollectionError(
                "missing/invalid canonical job-result cannot be replaced externally")
        if external_job_result_bytes != canonical_job_result_bytes:
            raise CollectionError(
                "external job-result differs from in-attempt record")
    clean_terminal = _CLEAN_RCS.get(accounting_record["exit_status"])
    if result is not None:
        try:
            _validate_job_result_semantics(
                result, submit=submit, protocol=protocol,
                series_preimage=series_preimage, series=series)
        except (CollectionError, QualificationArtifactError):
            canonical_state = "invalid"
            result = None

    accounting_failure_class = derive_failure_class(
        accounting_rc=accounting_record["exit_status"],
        observations_recorded=observations,
        series_present=series_present,
        job_result_present=result is not None,
        recovered_pre_attempt=recovered_pre_attempt,
    )
    accounting_mismatch = _has_accounting_result_mismatch(
        result, accounting_record,
        accounting_failure=accounting_failure_class,
        series_terminal=terminal if series_present else None)
    if canonical_state != "valid":
        failure_class = "job-result-publication-failed"
    elif accounting_mismatch:
        failure_class = "job-result-accounting-mismatch"
    else:
        failure_class = accounting_failure_class
    final_candidate = bool(
        canonical_state == "valid"
        and not accounting_mismatch
        and series_present
        and clean_terminal is not None
        and clean_terminal == terminal
        and failure_class == "none")

    prefix = f"attempts/{attempt_id}/post-job"
    copied = {
        "submission_receipt": create_or_verify_bytes(
            capability, f"{prefix}/submission-receipt.json",
            authoritative_submit_bytes),
        "scheduler_stdout": create_or_verify_bytes(
            capability, f"{prefix}/scheduler.o{_scheduler_suffix(job_id)}",
            stdout_bytes),
        "scheduler_stderr": create_or_verify_bytes(
            capability, f"{prefix}/scheduler.e{_scheduler_suffix(job_id)}",
            stderr_bytes),
        "accounting": create_or_verify_bytes(
            capability, f"{prefix}/accounting.txt", accounting_bytes),
    }
    if recovered_binding:
        copied["qsub_binding"] = _copy_external(
            capability, f"{prefix}/qsub-binding.json", submission_receipt,
            expected_bytes=submit_external_bytes)
    fault_inject("after-accounting-copy")
    if canonical_state in {"valid", "semantic-conflict"}:
        copied["job_result"] = _copy_external(
            capability, f"{prefix}/job-result.json", canonical_job_result,
            expected_bytes=canonical_job_result_bytes)
    fault_inject("after-job-result-copy")

    final_name = "final-qualification-receipt.json"
    failure_name = "attempt-failure-receipt.json"
    exclusion = {final_name, failure_name}
    closure = _manifest(attempt_dir, exclude=exclusion)
    verify_manifest_closure(attempt_dir, closure, excluded_names=exclusion)
    common = {
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
        "job_id": job_id,
        "retry_index": attempt_preimage["retry_index"],
        "scheduler_exit_status": accounting_record["exit_status"],
        "submission_receipt": file_record(
            copied["submission_receipt"], relative_to=attempt_dir),
        "submission_evidence_kind": (
            "recovered-qsub-binding" if recovered_binding else "submit-receipt"),
        "qsub_binding": (
            file_record(copied["qsub_binding"], relative_to=attempt_dir)
            if "qsub_binding" in copied else None),
        "job_result": (
            file_record(copied["job_result"], relative_to=attempt_dir)
            if "job_result" in copied else None),
        "scheduler_stdout": file_record(
            copied["scheduler_stdout"], relative_to=attempt_dir),
        "scheduler_stderr": file_record(
            copied["scheduler_stderr"], relative_to=attempt_dir),
        "accounting": file_record(copied["accounting"], relative_to=attempt_dir),
        "closure_manifest": closure,
    }
    if final_candidate:
        payload = {
            "schema_version": "t126-qualification-final-receipt/v1",
            **common,
            "statistical_claim": "none",
            "terminal": terminal,
            "series_result": file_record(series_path, relative_to=attempt_dir),
        }
        _schema_validate("t126_final_receipt_schema.json", payload)
        target = create_or_verify_json(
            capability, f"attempts/{attempt_id}/{final_name}", payload)
        failure_for_ledger = "none"
    else:
        retry_candidate = {
            "attempt_id": attempt_id,
            "observations_recorded": observations,
            "terminal": None,
            "failure_reason": failure_class,
        }
        try:
            pure_eligible = validate_retry_history([retry_candidate], protocol)
        except QualificationArtifactError:
            pure_eligible = False
        retry_eligible = bool(
            pure_eligible and attempt_preimage["retry_index"] == 0)
        payload = {
            "schema_version":
                "t126-qualification-attempt-failure-receipt/v1",
            **common,
            "attempt_phase": (
                "pre-attempt-recovery" if recovered_pre_attempt
                else "job-result-accounting-mismatch"
                if accounting_mismatch
                else "job-result-recovery"
                if canonical_state != "valid"
                else "post-series-terminal" if series_present
                else "attempt"),
            "failure_class": failure_class,
            "observations_recorded": observations,
            "retry_eligible": retry_eligible,
        }
        _schema_validate("t126_failure_receipt_schema.json", payload)
        target = create_or_verify_json(
            capability, f"attempts/{attempt_id}/{failure_name}", payload)
        failure_for_ledger = failure_class
    fault_inject("after-receipt-publish")

    ledger_state = attempt_ledger.replay
    target_sha256 = hashlib.sha256(read_regular_file(target)).hexdigest()
    if ledger_state.state in {"initial_failed", "retry_failed", "terminal"}:
        ledger_events = attempt_ledger.load()
        last_payload = (
            ledger_events[-1].get("payload", {}) if ledger_events else {})
        if (ledger_events[-1].get("event_type") == "attempt_outcome"
                and last_payload.get("qualification_attempt_id") == attempt_id
                and last_payload.get("receipt_sha256") == target_sha256):
            verified = verify_post_job_receipt(target, repo_root=repo_root)
            if verified.integrity_status != "valid":
                raise CollectionError(
                    "existing idempotent receipt no longer verifies")
            return target
        raise CollectionError(
            "series-global ledger is already closed by a different outcome")
    if (ledger_state.state not in {
            "initial_submitted", "retry_submitted", "outcome_pending"}
            or ledger_state.last_attempt_id != attempt_id
            or ledger_state.last_retry_index != attempt_preimage["retry_index"]):
        raise CollectionError(
            "series-global attempt ledger is missing or does not bind this attempt")
    attempt_ledger.prepare_outcome(
        attempt_id=attempt_id,
        retry_index=attempt_preimage["retry_index"],
        observations_recorded=observations,
        terminal=terminal if final_candidate else None,
        failure_class=failure_for_ledger,
        receipt_sha256=target_sha256,
    )
    fault_inject("after-outcome-pending")
    verified = _verify_post_job_receipt(
        target, repo_root=repo_root, allow_pending=True)
    if verified.integrity_status != "valid":
        raise CollectionError(
            "new post-job receipt failed read-only verification: "
            + "; ".join(verified.errors))
    attempt_ledger.finalize_outcome()
    fault_inject("after-outcome-finalize")
    verified = verify_post_job_receipt(target, repo_root=repo_root)
    if verified.integrity_status != "valid":
        raise CollectionError(
            "finalized receipt failed read-only verification: "
            + "; ".join(verified.errors))
    return target


def verify_post_job_receipt(
        receipt_path: Path, *, repo_root: Optional[Path] = None,
) -> ReceiptVerification:
    return _verify_post_job_receipt(
        receipt_path, repo_root=repo_root, allow_pending=False)


def _verify_post_job_receipt(
        receipt_path: Path, *, repo_root: Optional[Path],
        allow_pending: bool,
) -> ReceiptVerification:
    """Read-only final/failure consumer; re-derive every pointer and meaning."""
    try:
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise CollectionError("post-job receipt is missing or symlinked")
        receipt_path = receipt_path.resolve(strict=True)
        attempt_dir = receipt_path.parent
        if _HEX64.fullmatch(attempt_dir.name) is None:
            raise CollectionError("post-job receipt attempt path is invalid")
        expected = Path(
            "output/env/pegasus/qualification/t126/attempts") / attempt_dir.name
        if len(attempt_dir.parts) < 7 or Path(*attempt_dir.parts[-7:]) != expected:
            raise CollectionError(
                "post-job receipt is outside the exact qualification namespace")
        derived_repo = attempt_dir.parents[6]
        if repo_root is not None and repo_root.resolve() != derived_repo:
            raise CollectionError("post-job verifier repo root mismatch")
        repo_root = derived_repo
        value = load_json_strict(receipt_path)
        is_final = (
            value.get("schema_version") == "t126-qualification-final-receipt/v1")
        schema = (
            "t126_final_receipt_schema.json"
            if is_final else "t126_failure_receipt_schema.json")
        _schema_validate(schema, value)
        if value["qualification_attempt_id"] != attempt_dir.name:
            raise CollectionError("receipt/attempt path identity mismatch")
        marker = load_json_strict(attempt_dir / "qualification-marker.json")
        protocol = load_protocol(attempt_dir / "protocol.json")
        series_preimage = load_json_strict(
            attempt_dir / "series-identity.json")
        attempt_preimage = load_json_strict(
            attempt_dir / "attempt-identity.json")
        receipt_retry_index = _exact_retry_index(
            value.get("retry_index"), "post-job receipt")
        attempt_retry_index = _exact_retry_index(
            attempt_preimage.get("retry_index"), "attempt identity")
        series_id = series_identity(series_preimage)
        attempt_id = attempt_identity(attempt_preimage)
        if (value["qualification_series_id"] != series_id
                or value["qualification_attempt_id"] != attempt_id
                or marker.get("qualification_series_id") != series_id
                or marker.get("qualification_attempt_id") != attempt_id
                or receipt_retry_index != attempt_retry_index):
            raise CollectionError("receipt canonical identity mismatch")
        attempt_ledger = SeriesAttemptLedger(
            QualificationRoot(repo_root).issue(), series_id,
            protocol["retry"]["eligible_reasons"])
        ledger_state = attempt_ledger.replay
        receipt_sha = sha256_bytes(read_regular_file(receipt_path))
        ledger_events = attempt_ledger.load()
        if not ledger_events:
            raise CollectionError("receipt has no series-global ledger")
        ledger_last = ledger_events[-1]
        expected_kind = (
            "attempt_outcome_pending" if allow_pending else "attempt_outcome")
        if (ledger_last.get("event_type") != expected_kind
                or (not allow_pending and ledger_state.state not in {
                    "initial_failed", "retry_failed", "terminal"})):
            raise CollectionError(
                "receipt is not the finalized canonical ledger outcome")
        policy = json.loads(read_regular_file(
            repo_root / "tools/pegasus/policy.json"))
        reservation_policy = json.loads(read_regular_file(
            repo_root / RESERVATION_POLICY_RELATIVE_PATH))
        verify_recorded_series_identity(
            git_repo_root=repo_root, attempt_dir=attempt_dir,
            preimage=series_preimage, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy,
        )
        exclude = {
            "final-qualification-receipt.json",
            "attempt-failure-receipt.json",
        }
        verify_manifest_closure(
            attempt_dir, value["closure_manifest"], excluded_names=exclude)
        pointers = {
            "submission_receipt", "scheduler_stdout", "scheduler_stderr",
            "accounting",
        }
        if value.get("qsub_binding") is not None:
            pointers.add("qsub_binding")
        if value.get("job_result") is not None:
            pointers.add("job_result")
        if is_final:
            pointers.add("series_result")
        paths = {
            name: _safe_record_path(attempt_dir, value[name], name)
            for name in pointers
        }
        expected_pointer_paths = {
            "submission_receipt":
                attempt_dir / "post-job/submission-receipt.json",
            "scheduler_stdout": attempt_dir / (
                "post-job/scheduler.o" + _scheduler_suffix(value["job_id"])),
            "scheduler_stderr": attempt_dir / (
                "post-job/scheduler.e" + _scheduler_suffix(value["job_id"])),
            "accounting": attempt_dir / "post-job/accounting.txt",
        }
        if "job_result" in paths:
            expected_pointer_paths["job_result"] = (
                attempt_dir / "post-job/job-result.json")
        if "qsub_binding" in paths:
            expected_pointer_paths["qsub_binding"] = (
                attempt_dir / "post-job/qsub-binding.json")
        if is_final:
            expected_pointer_paths["series_result"] = (
                attempt_dir / "series-result.json")
        if any(paths[name].absolute() != expected.absolute()
               for name, expected in expected_pointer_paths.items()):
            raise CollectionError(
                "receipt pointer is not the canonical artifact path")
        submit_snapshot, snapshot_bytes = _load_submission_snapshot(attempt_dir)
        submit_retry_index = _exact_retry_index(
            submit_snapshot.get("retry_index"), "submission snapshot")
        if read_regular_file(paths["submission_receipt"]) != snapshot_bytes:
            raise CollectionError("final submission pointer differs from snapshot")
        source_manifest = load_json_strict(
            attempt_dir / "source/source-snapshots.json")
        binding_row = source_manifest.get("qsub_binding")
        binding_snapshot_path = _safe_record_path(
            attempt_dir, {
                "path": binding_row.get("path") if type(binding_row) is dict else None,
                "size": binding_row.get("size") if type(binding_row) is dict else None,
                "sha256": (
                    binding_row.get("sha256")
                    if type(binding_row) is dict else None),
            }, "qsub binding snapshot")
        binding_snapshot_bytes = read_regular_file(binding_snapshot_path)
        binding_snapshot_value = load_json_strict(binding_snapshot_path)
        invocation_row = source_manifest.get("qsub_invocation")
        invocation_snapshot_path = _safe_record_path(
            attempt_dir, {
                "path": (
                    invocation_row.get("path")
                    if type(invocation_row) is dict else None),
                "size": (
                    invocation_row.get("size")
                    if type(invocation_row) is dict else None),
                "sha256": (
                    invocation_row.get("sha256")
                    if type(invocation_row) is dict else None),
            }, "qsub invocation snapshot")
        invocation_snapshot = load_json_strict(invocation_snapshot_path)
        invocation_retry_index = _exact_retry_index(
            invocation_snapshot.get("retry_index"),
            "qsub invocation snapshot")
        invocation_snapshot_bytes = read_regular_file(
            invocation_snapshot_path)
        invocation_sha = sha256_bytes(invocation_snapshot_bytes)
        validate_qsub_binding(
            binding_snapshot_value,
            expected_nonce=submit_snapshot.get("nonce"),
            expected_intent_sha256=submit_snapshot.get(
                "submission_intent_sha256"),
            expected_invocation_sha256=invocation_sha,
            expected_retry_index=submit_retry_index,
            expected_job_id=submit_snapshot.get("job_id"))
        if (set(invocation_snapshot) != {
                "nonce", "retry_index", "submission_intent_sha256"}
                or invocation_snapshot.get("nonce")
                != submit_snapshot.get("nonce")
                or invocation_retry_index != submit_retry_index
                or invocation_snapshot.get("submission_intent_sha256")
                != submit_snapshot.get("submission_intent_sha256")
                or submit_snapshot.get("qsub_invocation_sha256")
                != invocation_sha
                or ledger_last["payload"].get("qsub_invocation_sha256")
                != invocation_sha
                or submit_snapshot.get("qsub_binding_sha256")
                != sha256_bytes(binding_snapshot_bytes)
                or ledger_last["payload"].get("submission_evidence_sha256")
                != sha256_bytes(binding_snapshot_bytes)):
            raise CollectionError(
                "submission/qsub binding/ledger evidence hash mismatch")
        job_id = _normalize_job_id(value["job_id"])
        accounting = _parse_accounting(read_regular_file(paths["accounting"]))
        _, stdout_identity = read_regular_file_with_identity(
            paths["scheduler_stdout"])
        _, stderr_identity = read_regular_file_with_identity(
            paths["scheduler_stderr"])
        _validate_scheduler_files(
            paths["scheduler_stdout"], paths["scheduler_stderr"], job_id,
            stdout_identity, stderr_identity)
        if submit_snapshot.get("qualification_attempt_id") != attempt_id:
            raise CollectionError("submission snapshot attempt identity mismatch")
        if (submit_snapshot.get("qualification_series_id") != series_id
                or _normalize_job_id(submit_snapshot.get("job_id")) != job_id
                or submit_snapshot.get("nonce") != attempt_preimage["nonce"]
                or submit_retry_index != attempt_retry_index
                or submit_snapshot.get("submission_intent_sha256")
                != attempt_preimage["submission_intent_sha256"]):
            raise CollectionError(
                "submission snapshot scheduler/attempt binding mismatch")
        verify_submission_script_chain(
            submission=submit_snapshot, preimage=series_preimage)
        if value["submission_evidence_kind"] == "recovered-qsub-binding":
            if (submit_snapshot.get("schema_version")
                    != "t126-qualification-recovered-submit/v1"):
                raise CollectionError(
                    "recovered evidence kind lacks recovered submission snapshot")
            binding = load_json_strict(paths["qsub_binding"])
            validate_qsub_binding(
                binding,
                expected_nonce=submit_snapshot.get("nonce"),
                expected_intent_sha256=submit_snapshot.get(
                    "submission_intent_sha256"),
                expected_invocation_sha256=invocation_sha,
                expected_retry_index=submit_snapshot.get("retry_index"),
                expected_job_id=submit_snapshot.get("job_id"))
            if _normalize_job_id(binding["job_id"]) != job_id:
                raise CollectionError(
                    "recovered qsub binding semantics mismatch")
        elif (submit_snapshot.get("schema_version")
                != "t126-qualification-submit-receipt/v1"
                or value.get("qsub_binding") is not None):
            raise CollectionError(
                "normal evidence kind/submission binding mismatch")
        job_result_value = None
        job_result_bytes = None
        semantic_series_path = attempt_dir / "series-result.json"
        semantic_series = (
            load_json_strict(semantic_series_path)
            if semantic_series_path.is_file()
            and not semantic_series_path.is_symlink()
            else None)
        if value.get("job_result") is not None:
            try:
                job_result_bytes = read_regular_file(paths["job_result"])
                job_result_value = json.loads(job_result_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CollectionError("pointed job-result JSON is invalid") from exc
            if type(job_result_value) is not dict:
                raise CollectionError("pointed job-result must be an object")
            _validate_job_result_semantics(
                job_result_value, submit=submit_snapshot, protocol=protocol,
                series_preimage=series_preimage, series=semantic_series)
        canonical_job_result = attempt_dir / "job-result.json"
        canonical_state = "missing"
        canonical_bytes = None
        if canonical_job_result.exists():
            _result_entry_stat(
                canonical_job_result, expected_nlink=1,
                label="public canonical job-result")
            canonical_bytes = read_regular_file(canonical_job_result)
            try:
                canonical_value = json.loads(canonical_bytes)
                if type(canonical_value) is not dict:
                    raise ValueError("not an object")
                _validate_job_result_semantics(
                    canonical_value, submit=submit_snapshot,
                    protocol=protocol, series_preimage=series_preimage,
                    series=semantic_series)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError,
                    KeyError, CollectionError, QualificationArtifactError):
                canonical_state = "invalid"
            else:
                canonical_state = "valid"
            if (job_result_bytes is not None
                    and canonical_bytes != job_result_bytes):
                raise CollectionError(
                    "pointed job-result differs from canonical attempt bytes")
        elif (job_result_bytes is not None
                and (is_final
                     or value.get("attempt_phase") != "pre-attempt-recovery")):
            raise CollectionError(
                "normal pointed job-result lacks its canonical attempt anchor")
        if (canonical_state != "valid"
                and value.get("job_result") is not None):
            raise CollectionError(
                "missing/invalid canonical job-result has a non-null pointer")
        pointer_missing_canonical = bool(
            canonical_state == "valid" and value.get("job_result") is None)
        if pointer_missing_canonical:
            raise CollectionError(
                "valid canonical job-result requires a non-null exact pointer")
        rejected_evidence = _assert_job_staging_closed(
            repo_root / "output/env/pegasus/qualification/t126",
            submit_snapshot, attempt_dir=attempt_dir)
        _validate_accounting_result_anchor(
            accounting, job_id=job_id,
            wmax_s=protocol["timing"]["wmax_s"],
            declared_exit_status=value["scheduler_exit_status"])
        if is_final:
            if job_result_value is None:
                raise CollectionError("final receipt requires semantic job-result")
            if job_result_value["failure_class"] != "none":
                raise CollectionError(
                    "final job-result must carry the clean failure class")
            verification = verify_attempt(attempt_dir)
            series_value = load_json_strict(paths["series_result"])
            series_timing = series_value["timing_envelope"]
            if (verification.integrity_status != "valid"
                    or verification.terminal != value["terminal"]
                    or _CLEAN_RCS.get(accounting["exit_status"])
                    != value["terminal"]
                    or job_result_value["driver_rc"]
                    != accounting["exit_status"]
                    or job_result_value["job_started_monotonic_ns"]
                    != series_timing["job_started_monotonic_ns"]
                    or job_result_value["completed_monotonic_ns"]
                    < series_timing["completed_monotonic_ns"]
                    or job_result_value["completed_monotonic_ns"]
                    - series_timing["job_started_monotonic_ns"]
                    > protocol["timing"]["wmax_s"] * 1_000_000_000):
                raise CollectionError("final series/accounting semantics mismatch")
            terminal = value["terminal"]
            observations = len(series_value["bits"])
            failure_class = "none"
        else:
            if value["retry_index"] == 1 and value["retry_eligible"] is not False:
                raise CollectionError("retry-of-retry cannot be eligible")
            if value["observations_recorded"] > 0 and value["retry_eligible"]:
                raise CollectionError("post-observation retry cannot be eligible")
            series_path = attempt_dir / "series-result.json"
            series_present = series_path.is_file() and not series_path.is_symlink()
            series_ledger = attempt_dir / "series-ledger.jsonl"
            recovered_pre_attempt = bool(
                value["submission_evidence_kind"]
                == "recovered-qsub-binding"
                and not series_ledger.exists())
            if series_present:
                verification = verify_attempt(attempt_dir)
                if verification.integrity_status != "valid":
                    raise CollectionError(
                        "failure receipt series result does not verify")
                observations = len(load_json_strict(series_path)["bits"])
                series_terminal = load_json_strict(series_path)["terminal"]
            elif recovered_pre_attempt:
                observations = 0
                series_terminal = None
            else:
                observations = replay_ledger(
                    load_jsonl_strict(series_ledger),
                    protocol).observations_recorded
                series_terminal = None
            accounting_failure = derive_failure_class(
                accounting_rc=accounting["exit_status"],
                observations_recorded=observations,
                series_present=series_present,
                job_result_present=value.get("job_result") is not None,
                recovered_pre_attempt=recovered_pre_attempt,
            )
            accounting_mismatch = _has_accounting_result_mismatch(
                job_result_value, accounting,
                accounting_failure=accounting_failure,
                series_terminal=series_terminal if series_present else None)
            rejected_semantic_conflict = (
                canonical_state == "valid"
                and _rejected_conflict_is_semantically_invalid(
                    rejected_evidence, attempt_dir=attempt_dir,
                    canonical_bytes=canonical_bytes,
                    submit=submit_snapshot, protocol=protocol,
                    series_preimage=series_preimage,
                    series=semantic_series, accounting=accounting,
                    observations_recorded=observations,
                    recovered_pre_attempt=recovered_pre_attempt))
            if rejected_semantic_conflict or pointer_missing_canonical:
                expected_failure = "job-result-publication-failed"
            elif canonical_state == "missing":
                expected_failure = "job-result-publication-failed"
            elif canonical_state != "valid":
                expected_failure = "job-result-publication-failed"
            elif accounting_mismatch:
                expected_failure = "job-result-accounting-mismatch"
            else:
                expected_failure = accounting_failure
            if value["failure_class"] != expected_failure:
                raise CollectionError("failure class is not accounting-derived")
            expected_phase = (
                "pre-attempt-recovery"
                if recovered_pre_attempt
                else "job-result-accounting-mismatch"
                if accounting_mismatch
                else "job-result-recovery"
                if (canonical_state != "valid"
                    or rejected_semantic_conflict
                    or pointer_missing_canonical)
                else "post-series-terminal"
                if series_present
                else "attempt")
            if value["attempt_phase"] != expected_phase:
                raise CollectionError("failure receipt attempt phase mismatch")
            if (job_result_value is not None
                    and not accounting_mismatch
                    and not rejected_semantic_conflict
                    and job_result_value["failure_class"]
                    != value["failure_class"]):
                raise CollectionError(
                    "job-result failure class differs from derived receipt class")
            terminal = None
            failure_class = value["failure_class"]
            if value["observations_recorded"] != observations:
                raise CollectionError(
                    "failure observations are not canonical-series-derived")
            retry_expected = bool(
                value["retry_index"] == 0
                and observations == 0
                and value["failure_class"]
                not in PERMANENT_NONRETRY_FAILURES
                and value["failure_class"]
                in protocol["retry"]["eligible_reasons"])
            if value["retry_eligible"] is not retry_expected:
                raise CollectionError(
                    "failure retry field is not protocol-derived")
        expected_ledger_payload = {
            "qualification_attempt_id": attempt_id,
            "retry_index": attempt_preimage["retry_index"],
            "observations_recorded": observations,
            "terminal": terminal,
            "failure_class": failure_class,
            "receipt_sha256": receipt_sha,
            "job_id": job_id,
            "nonce": attempt_preimage["nonce"],
            "submission_intent_sha256":
                attempt_preimage["submission_intent_sha256"],
            "qsub_invocation_sha256": invocation_sha,
            "submission_evidence_sha256":
                sha256_bytes(binding_snapshot_bytes),
        }
        expected_state = (
            "outcome_pending" if allow_pending else
            "terminal" if terminal is not None else
            "retry_failed" if attempt_preimage["retry_index"] == 1 else
            "initial_failed")
        if (ledger_last.get("payload") != expected_ledger_payload
                or ledger_state.state != expected_state):
            raise CollectionError(
                "receipt semantic payload/state differs from canonical ledger")
        return ReceiptVerification("valid", "valid", terminal, ())
    except Exception as exc:
        return ReceiptVerification(
            "invalid", "invalid", None,
            (f"{type(exc).__name__}: {exc}",),
        )
