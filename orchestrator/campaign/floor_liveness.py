# -*- coding: utf-8 -*-
"""Bounded post-submit liveness classification for Pegasus floor jobs."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..qualification import artifacts
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


def _terminal_evidence(
    repo_root: Path, submission: Path, request_id: str,
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
        submission, _receipt = _load_bound_receipt(repo, request_id, nonce)
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
                        repo, submission, request_id,
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
    parser.add_argument("request_id")
    parser.add_argument("nonce")
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = classify(
            args.request_id,
            args.nonce,
            timeout_s=args.timeout_seconds,
            poll_interval_s=args.poll_interval_seconds,
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
