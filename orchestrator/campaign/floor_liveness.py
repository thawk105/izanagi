# -*- coding: utf-8 -*-
"""Bounded post-submit liveness classification for Pegasus floor jobs."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..qualification import artifacts
from . import floor_job_checkpoint
from tools.pegasus import dispatch_compute


_NONCE_RE = re.compile(r"[0-9a-f]{32}")
_REQUEST_RE = re.compile(r"(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*")
_COMPUTE_HOST_RE = re.compile(r"bnode[0-9]+(?:\..*)?")
_QSTAT_ABSENT_RE = re.compile(
    r"(?i)(?:batch request(?::\s*\S+)?\s+does not exist|unknown job id)"
)
_ACCOUNTING_MARKERS = (
    "Request ID:",
    "Started Request Time:",
    "Ended Request Time:",
    "Elapse:",
)
_READ_LIMIT_BYTES = 64 * 1024
_SCHEMA = "pegasus-floor-liveness/v1"
_JOURNAL_SCHEMA = "s8b-floor-journal/v3"
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_HEX32_RE = re.compile(r"[0-9a-f]{32}")
_RESERVATION_BINDING_KEYS = frozenset({
    "event", "required_s", "safety_margin_s", "formula",
    "build_cap_per_cell_s", "shared_dependency_prebuild",
    "dependency_configure_cap_s", "dependency_target_cap_s",
    "verify_cap_per_attempt_s", "finalize_reserve_s", "pbs_jobid",
    "submission_nonce",
})
_CAMPAIGN_BINDING_KEYS = frozenset({
    "event", "schema", "protocol_sha256", "freeze_sha256",
    "manifest_sha256", "hostname", "boot_id", "job_id", "cpuset", "utc",
    "pid", "starttime", "execution_uuid", "pbs_jobid", "submission_nonce",
})
_SESSION_START_KEYS = frozenset({
    "event", "seq", "kind", "cell_id", "round", "retry_ordinal",
    "attempt_id", "trigger", "started_iso",
})

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


class LivenessError(ValueError):
    """The caller supplied an unsafe or unbound liveness query."""


def _normalize_request_id(value: str) -> str:
    if type(value) is not str or _REQUEST_RE.fullmatch(value) is None:
        raise LivenessError("request ID is malformed")
    try:
        return dispatch_compute._normalize_request_id(value)
    except dispatch_compute.DispatchError as exc:
        raise LivenessError("request ID is malformed") from exc


def _submission_dir(repo_root: Path, nonce: str) -> Path:
    if type(nonce) is not str or _NONCE_RE.fullmatch(nonce) is None:
        raise LivenessError("nonce must be 32 lowercase hexadecimal characters")
    return (
        repo_root
        / "output/env/pegasus/floor/attempts/submissions"
        / nonce
    )


def _load_bound_receipt(
    repo_root: Path, request_id: str, nonce: str,
) -> tuple[Path, Mapping[str, Any]]:
    submission = _submission_dir(repo_root, nonce)
    receipt_path = submission / "submit-receipt.json"
    try:
        receipt = artifacts.load_json_strict(receipt_path)
    except Exception as exc:
        raise LivenessError(f"submission receipt strict read failed: {exc}") from exc
    observed_job_id = receipt.get("job_id")
    if (
        receipt.get("schema_version") != "pegasus-floor-submit-receipt/v1"
        or receipt.get("nonce") != nonce
        or receipt.get("dry_run") is not False
        or type(observed_job_id) is not str
        or _normalize_request_id(observed_job_id) != _normalize_request_id(request_id)
    ):
        raise LivenessError("request ID/nonce do not match the real floor receipt")
    return submission, receipt


def _bounded_text(path: Path) -> str | None:
    try:
        if path.is_symlink() or not path.is_file():
            return None
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size <= _READ_LIMIT_BYTES:
                raw = handle.read(_READ_LIMIT_BYTES + 1)
            else:
                half = _READ_LIMIT_BYTES // 2
                first = handle.read(half)
                handle.seek(max(0, size - half))
                raw = first + b"\n...[bounded middle omitted]...\n" + handle.read(half)
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def _json_reason(path: Path) -> dict[str, Any] | None:
    text = _bounded_text(path)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, UnicodeError):
        return None
    if type(value) is not dict:
        return None
    fields = {
        key: value[key]
        for key in ("gate", "reason", "stage", "message", "rc", "driver_rc")
        if key in value
    }
    if not fields:
        return None
    return {"path": str(path), "fields": fields}


def _staging_candidates(repo_root: Path, request_id: str) -> tuple[Path, ...]:
    normalized = _normalize_request_id(request_id)
    names = []
    for name in (request_id, normalized, "0:" + normalized):
        if name not in names:
            names.append(name)
    root = repo_root / "output/env/pegasus/floor/job-staging"
    return tuple(root / name for name in names)


def _compute_marker(
    repo_root: Path, request_id: str, nonce: str,
) -> dict[str, Any]:
    for staging in _staging_candidates(repo_root, request_id):
        hostname_path = staging / "hostname.stdout"
        hostname_text = _bounded_text(hostname_path)
        if hostname_text is None:
            continue
        hostname = hostname_text.strip()
        receipt_path = staging / "submit-receipt.json"
        try:
            receipt = artifacts.load_json_strict(receipt_path)
            receipt_bound = (
                receipt.get("nonce") == nonce
                and type(receipt.get("job_id")) is str
                and _normalize_request_id(receipt["job_id"])
                == _normalize_request_id(request_id)
            )
        except Exception:
            receipt_bound = False
        valid = _COMPUTE_HOST_RE.fullmatch(hostname) is not None and receipt_bound
        return {
            "path": str(hostname_path),
            "present": True,
            "valid": valid,
            "hostname": hostname,
            "receipt_bound": receipt_bound,
        }
    return {"present": False, "valid": False}


def _stderr_reason(path: Path) -> dict[str, Any] | None:
    text = _bounded_text(path)
    if text is None:
        return None
    accounting_present = all(marker in text for marker in _ACCOUNTING_MARKERS)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if type(value) is dict and ("reason" in value or "gate" in value):
            return {
                "path": str(path),
                "kind": "structured-stderr",
                "fields": {
                    key: value[key]
                    for key in ("gate", "reason", "stage", "message", "rc")
                    if key in value
                },
                "accounting_present": accounting_present,
            }
    ordinary = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and set(line.strip()) != {"="}
        and not any(line.lstrip().startswith(marker) for marker in _ACCOUNTING_MARKERS)
    ]
    if ordinary:
        return {
            "path": str(path),
            "kind": "stderr-text",
            "text": "\n".join(ordinary[-20:]),
            "accounting_present": accounting_present,
        }
    if accounting_present:
        return {
            "path": str(path),
            "kind": "scheduler-accounting",
            "accounting_present": True,
        }
    return None


def _is_utc_text(value: object) -> bool:
    if type(value) is not str or not value:
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == dt.timedelta(0)


def _validate_journal_binding(
    records: Sequence[Mapping[str, object]], *, job_id: str, nonce: str,
) -> tuple[str | None, bool]:
    """Validate exact binding events and canonical session-start nodes."""

    bindings: list[tuple[str, str, str]] = []
    event_counts = {"reservation-preflight": 0, "campaign-start": 0}
    seen_seq: set[int] = set()
    seen_attempts: set[str] = set()
    seen_retries: set[tuple[str, int]] = set()
    last_cell: str | None = None
    for record in records:
        event = record.get("event")
        claims_binding = "pbs_jobid" in record or "submission_nonce" in record
        if event == "reservation-preflight":
            event_counts[event] += 1
            if claims_binding:
                integer_fields = _RESERVATION_BINDING_KEYS - {
                    "event", "formula", "shared_dependency_prebuild",
                    "pbs_jobid", "submission_nonce",
                }
                if (
                    set(record) != _RESERVATION_BINDING_KEYS
                    or record.get("event") != "reservation-preflight"
                    or type(record.get("formula")) is not str
                    or not record["formula"]
                    or type(record.get("shared_dependency_prebuild")) is not bool
                    or any(
                        type(record.get(field)) is not int or record[field] <= 0
                        for field in integer_fields
                    )
                ):
                    raise floor_job_checkpoint.CheckpointError(
                        "reservation-preflight binding shape is invalid"
                    )
                bindings.append((event, record["pbs_jobid"], record["submission_nonce"]))
        elif event == "campaign-start":
            event_counts[event] += 1
            if claims_binding:
                optional = set(record) - set(_CAMPAIGN_BINDING_KEYS)
                nullable_text = ("boot_id", "job_id", "cpuset")
                if (
                    optional not in (
                        set(), {"launch_certificate_sha256"},
                        {"execution_receipt"},
                        {"launch_certificate_sha256", "execution_receipt"},
                    )
                    or not _CAMPAIGN_BINDING_KEYS.issubset(record)
                    or record.get("schema") != _JOURNAL_SCHEMA
                    or any(
                        type(record.get(field)) is not str
                        or _HEX64_RE.fullmatch(record[field]) is None
                        for field in (
                            "protocol_sha256", "freeze_sha256", "manifest_sha256",
                        )
                    )
                    or "launch_certificate_sha256" in record
                    and (
                        type(record["launch_certificate_sha256"]) is not str
                        or _HEX64_RE.fullmatch(record["launch_certificate_sha256"])
                        is None
                    )
                    or "execution_receipt" in record
                    and type(record["execution_receipt"]) is not dict
                    or type(record.get("hostname")) is not str
                    or not record["hostname"]
                    or any(
                        record.get(field) is not None
                        and (type(record.get(field)) is not str or not record[field])
                        for field in nullable_text
                    )
                    or not _is_utc_text(record.get("utc"))
                    or type(record.get("pid")) is not int
                    or record["pid"] <= 0
                    or record.get("starttime") is not None
                    and (
                        type(record.get("starttime")) is not int
                        or record["starttime"] < 0
                    )
                    or type(record.get("execution_uuid")) is not str
                    or _HEX32_RE.fullmatch(record["execution_uuid"]) is None
                ):
                    raise floor_job_checkpoint.CheckpointError(
                        "campaign-start binding shape is invalid"
                    )
                bindings.append((event, record["pbs_jobid"], record["submission_nonce"]))
        elif claims_binding:
            raise floor_job_checkpoint.CheckpointError(
                "journal binding fields occur on a non-binding event"
            )

        if event != "session-start":
            continue
        if set(record) != _SESSION_START_KEYS:
            raise floor_job_checkpoint.CheckpointError(
                "session-start exact shape is invalid"
            )
        seq = record.get("seq")
        cell_id = record.get("cell_id")
        attempt_id = record.get("attempt_id")
        round_no = record.get("round")
        if (
            type(seq) is not int or seq < 0 or seq in seen_seq
            or type(cell_id) is not str or not cell_id
            or type(attempt_id) is not str or not attempt_id
            or attempt_id in seen_attempts
            or type(round_no) is not int or round_no <= 0
            or not _is_utc_text(record.get("started_iso"))
        ):
            raise floor_job_checkpoint.CheckpointError(
                "session-start identity is invalid or duplicated"
            )
        seen_seq.add(seq)
        seen_attempts.add(attempt_id)
        if record.get("kind") == "planned":
            if (
                record.get("retry_ordinal") is not None
                or record.get("trigger") is not None
                or attempt_id != f"{cell_id}::seq{seq}"
            ):
                raise floor_job_checkpoint.CheckpointError(
                    "planned session-start is not canonical"
                )
        elif record.get("kind") == "retry":
            ordinal = record.get("retry_ordinal")
            retry_key = (cell_id, ordinal)
            if (
                type(ordinal) is not int or ordinal <= 0
                or type(record.get("trigger")) is not str
                or not record["trigger"]
                or attempt_id != f"{cell_id}::retry{ordinal}"
                or retry_key in seen_retries
            ):
                raise floor_job_checkpoint.CheckpointError(
                    "retry session-start is not canonical"
                )
            seen_retries.add(retry_key)
        else:
            raise floor_job_checkpoint.CheckpointError(
                "session-start kind is invalid"
            )
        last_cell = cell_id

    if any(count > 1 for count in event_counts.values()):
        raise floor_job_checkpoint.CheckpointError(
            "journal binding event is not unique"
        )
    if not bindings:
        raise floor_job_checkpoint.CheckpointError(
            "journal has no canonical job-id/nonce binding"
        )
    for _event, observed_job, observed_nonce in bindings:
        if (
            type(observed_job) is not str
            or floor_job_checkpoint.normalize_job_id(observed_job)
            != floor_job_checkpoint.normalize_job_id(job_id)
            or observed_nonce != nonce
        ):
            raise floor_job_checkpoint.CheckpointError(
                "journal job-id/nonce bindings disagree"
            )
    return last_cell, bool(seen_seq)


def _terminal_evidence(
    repo_root: Path, submission: Path, request_id: str,
    nonce: str, receipt: Mapping[str, Any], evidence_root: Path | None,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for staging in _staging_candidates(repo_root, request_id):
        reason = _json_reason(staging / "failure.json")
        if reason is not None:
            reason["kind"] = "failure-json"
            evidence.append(reason)
        interpreter = _bounded_text(staging / "failure-interpreter.txt")
        if interpreter:
            evidence.append({
                "path": str(staging / "failure-interpreter.txt"),
                "kind": "job-staging-text",
                "text": interpreter.strip(),
            })
        driver = _bounded_text(staging / "floor-driver.stderr")
        if driver:
            evidence.append({
                "path": str(staging / "floor-driver.stderr"),
                "kind": "job-staging-stderr",
                "text": driver.strip(),
            })
        result = _json_reason(staging / "job-result.json")
        if result is not None:
            result["kind"] = "job-result"
            evidence.append(result)
    stderr = _stderr_reason(submission / "scheduler.stderr")
    if stderr is not None:
        evidence.append(stderr)
    external = _external_checkpoint_evidence(
        request_id, nonce, receipt=receipt, evidence_root=evidence_root,
        submission=submission,
    )
    if external is not None:
        evidence.append(external)
    if not evidence:
        evidence.append({
            "kind": "terminal-evidence-unavailable",
            "searched": [
                str(submission / "scheduler.stderr"),
                *[
                    str(staging)
                    for staging in _staging_candidates(repo_root, request_id)
                ],
            ],
        })
    return evidence


def _default_evidence_root(repo_root: Path) -> Path:
    git_entry = repo_root / ".git"
    common_dir = git_entry
    if git_entry.is_file() and not git_entry.is_symlink():
        try:
            line = git_entry.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            line = ""
        prefix = "gitdir: "
        if line.startswith(prefix):
            admin = Path(line[len(prefix):])
            if not admin.is_absolute():
                admin = repo_root / admin
            # Linked-worktree admin is <common>/.git/worktrees/<name>.
            if len(admin.parents) >= 2 and admin.parent.name == "worktrees":
                common_dir = admin.parent.parent
    return common_dir.parent.parent / "izanagi-job-evidence"


def _external_checkpoint_evidence(
    request_id: str,
    nonce: str,
    *,
    receipt: Mapping[str, Any],
    evidence_root: Path | None,
    submission: Path,
) -> dict[str, Any] | None:
    catalog_root = Path(evidence_root) if evidence_root is not None else None
    if catalog_root is None:
        return None
    submitted_at = receipt.get("submitted_at")
    receipt_job_id = receipt.get("job_id")
    if type(submitted_at) is not int:
        return {
            "kind": "external-job-checkpoint-unusable",
            "reason": "receipt submitted_at is unavailable",
        }
    try:
        if type(receipt_job_id) is not str:
            raise floor_job_checkpoint.CheckpointError(
                "receipt job ID is unavailable"
            )
        job_index, _time_index = floor_job_checkpoint.index_paths(
            catalog_root, receipt_job_id, nonce, submitted_at,
        )
    except (OSError, ValueError, TypeError) as exc:
        return {
            "kind": "external-job-checkpoint-unusable",
            "reason": str(exc),
        }
    sidecar_path = submission / "evidence-index-status.json"
    sidecar: Mapping[str, object] | None = None
    if sidecar_path.exists() or sidecar_path.is_symlink():
        try:
            sidecar = floor_job_checkpoint.load_index_status(
                sidecar_path,
                job_id=receipt_job_id,
                nonce=nonce,
                submitted_at=submitted_at,
            )
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            return {
                "kind": "external-job-checkpoint-unusable",
                "index_status_path": str(sidecar_path),
                "reason": str(exc),
            }
    if not job_index.exists() and not job_index.is_symlink():
        if sidecar is None:
            return None
        return {
            "kind": "external-job-index-status",
            "index_path": str(job_index),
            "index_status_path": str(sidecar_path),
            "index_probe_status": sidecar["login_probe_status"],
            "index_write_status": sidecar["index_write_status"],
            "evidence_root": sidecar["evidence_root"],
            "last_observed_stage": None,
            "cause": "unknown",
            "rerun_eligible": None,
        }
    try:
        index = floor_job_checkpoint.load_bound_index(
            catalog_root,
            job_id=receipt_job_id,
            nonce=nonce,
            submitted_at=submitted_at,
        )
        effective_root = Path(index["evidence_root"])
        if sidecar is not None and any(
            sidecar[field] != index[field]
            for field in (
                "catalog_root", "evidence_root", "requested_evidence_root",
                "login_probe_status",
            )
        ):
            raise floor_job_checkpoint.CheckpointError(
                "index status sidecar disagrees with published index"
            )
        indexed_checkpoint = Path(index["checkpoint_path"])
        if (
            not indexed_checkpoint.exists()
            and not indexed_checkpoint.is_symlink()
        ):
            return {
                "kind": "external-job-index",
                "index_path": str(job_index),
                "checkpoint_path": str(indexed_checkpoint),
                "index_probe_status": index["login_probe_status"],
                "index_write_status": (
                    sidecar["index_write_status"] if sidecar is not None
                    else "published"
                ),
                "last_observed_stage": None,
                "cause": "unknown",
                "rerun_eligible": None,
            }
        records, incomplete_tail, checkpoint_path = (
            floor_job_checkpoint.read_checkpoint(
                effective_root, receipt_job_id, nonce,
            )
        )
        if not records:
            raise floor_job_checkpoint.CheckpointError(
                "checkpoint has no complete records"
            )
        last = records[-1]
        linked = [
            record for record in records
            if record.get("transition") == "run-linked"
        ]
        join: dict[str, Any] = {"present": bool(linked), "valid": False}
        if linked:
            link = linked[-1]
            if (
                link.get("producer") != "s8b_floor_campaign.py"
                or link.get("stage") != "floor-driver"
                or type(link.get("run_dir")) is not str
                or type(link.get("journal_path")) is not str
            ):
                raise floor_job_checkpoint.CheckpointError(
                    "run-linked schema is invalid"
                )
            run_dir = Path(link["run_dir"])
            journal_path = Path(link["journal_path"])
            if not run_dir.is_absolute() or journal_path != run_dir / "journal.jsonl":
                raise floor_job_checkpoint.CheckpointError(
                    "run-linked journal path is not run_dir/journal.jsonl"
                )
            journal_records, journal_incomplete = (
                floor_job_checkpoint.read_journal_prefix(journal_path)
            )
            last_session_cell_id, sessions_present = _validate_journal_binding(
                journal_records, job_id=receipt_job_id, nonce=nonce,
            )
            join = {
                "present": True,
                "valid": True,
                "run_dir": str(run_dir),
                "journal_path": str(journal_path),
                "journal_incomplete_tail": journal_incomplete,
                "last_session_cell_id": (
                    last_session_cell_id if sessions_present else None
                ),
            }
        return {
            "kind": "external-job-checkpoint",
            "path": str(checkpoint_path),
            "index_path": str(job_index),
            "index_probe_status": index["login_probe_status"],
            "index_write_status": (
                sidecar["index_write_status"] if sidecar is not None
                else "published"
            ),
            "complete_record_count": len(records),
            "incomplete_tail": incomplete_tail,
            "last_observed_stage": last["stage"],
            "last_transition": last["transition"],
            "last_rc": last["rc"],
            "cause": {
                "rejected": "controlled-rejection",
                "failed": "controlled-failure",
            }.get(last["transition"], "unknown"),
            **({
                "observed_signal": (
                    last["command"].removeprefix("signal ")
                    if type(last.get("command")) is str
                    else None
                ),
            } if last["transition"] == "signalled" else {}),
            "rerun_eligible": None,
            "run_link": join,
        }
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return {
            "kind": "external-job-checkpoint-unusable",
            "index_path": str(job_index),
            "reason": str(exc),
        }


def _qstat_reports_absent(result: subprocess.CompletedProcess[str]) -> bool:
    response = "\n".join((result.stdout or "", result.stderr or ""))
    return _QSTAT_ABSENT_RE.search(response) is not None


def _result(
    classification: str,
    *,
    request_id: str,
    nonce: str,
    elapsed_s: float,
    **fields: Any,
) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA,
        "classification": classification,
        "request_id": request_id,
        "nonce": nonce,
        "elapsed_s": max(0.0, elapsed_s),
        "request_disappeared_is_success": False,
        **fields,
    }


def classify(
    request_id: str,
    nonce: str,
    *,
    timeout_s: float,
    repo_root: Path | None = None,
    evidence_root: Path | None = None,
    poll_interval_s: float = 1.0,
    qstat_timeout_s: float = 5.0,
    run_command: CommandRunner = subprocess.run,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
) -> dict[str, Any]:
    """Classify one submitted floor request without waiting past ``timeout_s``."""

    if timeout_s <= 0 or poll_interval_s <= 0 or qstat_timeout_s <= 0:
        raise LivenessError("timeout and polling intervals must be positive")
    repo = (
        Path(__file__).resolve().parents[2]
        if repo_root is None
        else Path(repo_root).resolve()
    )
    started = clock()
    deadline = started + timeout_s
    try:
        submission, receipt = _load_bound_receipt(repo, request_id, nonce)
    except LivenessError as exc:
        return _result(
            "indeterminate",
            request_id=request_id,
            nonce=nonce,
            elapsed_s=clock() - started,
            reason=str(exc),
        )
    normalized = _normalize_request_id(request_id)
    last_qstat: dict[str, Any] | None = None
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return _result(
                "indeterminate",
                request_id=request_id,
                nonce=nonce,
                elapsed_s=clock() - started,
                reason="overall timeout expired before a conclusive state",
                last_qstat=last_qstat,
            )
        try:
            observed = run_command(
                ["qstat", "-f", normalized],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=min(qstat_timeout_s, remaining),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            last_qstat = {
                "classification": "transient-exception",
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            response_class = dispatch_compute._classify_qstat_response(
                observed, normalized,
            )
            state = (
                dispatch_compute._scheduler_state(observed.stdout or "")
                if response_class == "success-request-visible"
                else None
            )
            last_qstat = {
                "returncode": int(observed.returncode),
                "classification": response_class,
                "state": state,
            }
            if response_class == "permission":
                return _result(
                    "indeterminate",
                    request_id=request_id,
                    nonce=nonce,
                    elapsed_s=clock() - started,
                    reason="qstat permission or ownership error",
                    last_qstat=last_qstat,
                )
            request_absent = (
                response_class == "success-request-absent"
                or _qstat_reports_absent(observed)
            )
            if request_absent or state == "END":
                return _result(
                    "finished",
                    request_id=request_id,
                    nonce=nonce,
                    elapsed_s=clock() - started,
                    request_disappeared=request_absent,
                    job_success=None,
                    evidence=_terminal_evidence(
                        repo, submission, request_id, nonce, receipt,
                        (
                            _default_evidence_root(repo)
                            if evidence_root is None else Path(evidence_root)
                        ),
                    ),
                    last_qstat=last_qstat,
                )
            if state in {"QUE", "HLD"}:
                return _result(
                    "queue-waiting",
                    request_id=request_id,
                    nonce=nonce,
                    elapsed_s=clock() - started,
                    scheduler_state=state,
                    last_qstat=last_qstat,
                )
            if state == "RUN":
                marker = _compute_marker(repo, request_id, nonce)
                if marker["valid"]:
                    return _result(
                        "running",
                        request_id=request_id,
                        nonce=nonce,
                        elapsed_s=clock() - started,
                        scheduler_state=state,
                        compute_marker=marker,
                        last_qstat=last_qstat,
                    )
                last_qstat["compute_marker"] = marker
        remaining = deadline - clock()
        if remaining <= 0:
            continue
        sleep(min(poll_interval_s, remaining))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="classify one submitted Pegasus floor request",
    )
    parser.add_argument("request_id", nargs="?")
    parser.add_argument("nonce", nargs="?")
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument("--evidence-root", type=Path)
    resolver = parser.add_mutually_exclusive_group()
    resolver.add_argument("--resolve-job-id")
    resolver.add_argument(
        "--resolve-time", nargs=2, type=int, metavar=("EARLIEST", "LATEST"),
    )
    parser.add_argument("--max-index-results", type=int, default=128)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.resolve_job_id is not None or args.resolve_time is not None:
        if args.request_id is not None or args.nonce is not None:
            parser.error("resolver modes do not accept request_id/nonce positionals")
        repo = Path(__file__).resolve().parents[2]
        catalog_root = (
            _default_evidence_root(repo)
            if args.evidence_root is None else args.evidence_root
        )
        try:
            if args.resolve_job_id is not None:
                matches = floor_job_checkpoint.resolve_indices_by_job(
                    catalog_root,
                    job_id=args.resolve_job_id,
                    max_entries=args.max_index_results,
                )
                query = {
                    "kind": "job-id", "job_id": args.resolve_job_id,
                }
            else:
                earliest, latest = args.resolve_time
                matches = floor_job_checkpoint.resolve_indices_by_time(
                    catalog_root,
                    earliest=earliest,
                    latest=latest,
                    max_entries=args.max_index_results,
                )
                query = {
                    "kind": "submitted-at", "earliest": earliest,
                    "latest": latest,
                }
            result = {
                "schema_version": "pegasus-floor-evidence-resolver/v1",
                "catalog_root": str(catalog_root),
                "query": query,
                "matches": matches,
            }
            rc = 0
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            result = {
                "schema_version": "pegasus-floor-evidence-resolver/v1",
                "catalog_root": str(catalog_root),
                "query": (
                    {"kind": "job-id", "job_id": args.resolve_job_id}
                    if args.resolve_job_id is not None
                    else {
                        "kind": "submitted-at",
                        "earliest": args.resolve_time[0],
                        "latest": args.resolve_time[1],
                    }
                ),
                "error": str(exc),
            }
            rc = 4
        print(json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ))
        return rc
    if (
        args.request_id is None
        or args.nonce is None
        or args.timeout_seconds is None
    ):
        parser.error(
            "classification requires request_id, nonce, and --timeout-seconds"
        )
    try:
        result = classify(
            args.request_id,
            args.nonce,
            timeout_s=args.timeout_seconds,
            poll_interval_s=args.poll_interval_seconds,
            evidence_root=args.evidence_root,
        )
    except LivenessError as exc:
        result = _result(
            "indeterminate",
            request_id=args.request_id,
            nonce=args.nonce,
            elapsed_s=0.0,
            reason=str(exc),
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return {
        "queue-waiting": 0,
        "running": 0,
        "finished": 3,
        "indeterminate": 4,
    }[result["classification"]]


if __name__ == "__main__":
    sys.exit(main())
