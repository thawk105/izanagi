#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""終了済み PBS job の scheduler 出力と staging を final receipt に束縛する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


_ORCHESTRATOR = Path(__file__).resolve().parents[2] / "orchestrator"
if str(_ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR))

from calibrator.schema_v2 import normalize_request_id  # noqa: E402


class CollectionError(RuntimeError):
    """final receipt を安全に作れない。"""


_ACCOUNTING_RE = re.compile(
    r"(?i)(nqsv|request\s*(?:id|name)|exit[_ ]?status|resources_used|"
    r"cpu\s*time|memory|elap(?:sed|stim)|walltime)"
)


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise CollectionError(f"{label} must not be a symlink: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"{label} is missing or invalid: {path}: {exc}") from exc
    if type(value) is not dict:
        raise CollectionError(f"{label} must be a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CollectionError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CollectionError(f"required file is missing: {path}")
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _accounting_summary(stderr_text: str) -> list[str]:
    lines = stderr_text.splitlines()
    matches = [index for index, line in enumerate(lines) if _ACCOUNTING_RE.search(line)]
    if not matches:
        raise CollectionError("scheduler stderr has no recognizable accounting summary")
    # 最初の会計 marker 以降を生のまま保持する。stderr 非空/空は成否判定に使わない。
    return lines[matches[0]:]


def _staging_manifest(attempt_dir: Path, excluded: Iterable[Path]) -> list[dict[str, Any]]:
    excluded_resolved = {path.resolve() for path in excluded}
    records = []
    for path in sorted(attempt_dir.rglob("*")):
        if path.is_symlink():
            raise CollectionError(f"staging must not contain symlinks: {path}")
        if not path.is_file() or path.resolve() in excluded_resolved:
            continue
        records.append({
            "path": str(path.relative_to(attempt_dir)),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        })
    if not records:
        raise CollectionError("attempt staging is empty")
    return records


def _request_id(submit: Mapping[str, Any]) -> str:
    qsub = submit.get("qsub")
    if type(qsub) is not dict or type(qsub.get("request_id")) is not str:
        raise CollectionError("submit receipt has no qsub.request_id")
    return qsub["request_id"]


def _scheduler_name_matches(path: Path, *, stream: str, job_id: str) -> bool:
    suffix = ".o" if stream == "stdout" else ".e"
    forms = {job_id, job_id.split(".", 1)[0]}
    return any(path.name.endswith(suffix + form) for form in forms if form)


def build_final_receipt(
    *,
    attempt_dir: Path,
    job_staging: Path,
    stdout_path: Path,
    stderr_path: Path,
    output_path: Path,
    collected_epoch: Optional[int] = None,
) -> dict[str, Any]:
    if not attempt_dir.is_dir():
        raise CollectionError(f"calibrator attempt directory is missing: {attempt_dir}")
    submit_path = job_staging / "submit-receipt.json"
    acquisition_path = job_staging / "acquisition-receipt.json"
    result_path = job_staging / "job-result.json"
    submit = _load_object(submit_path, label="submit receipt")
    acquisition = _load_object(acquisition_path, label="acquisition receipt")
    result = _load_object(result_path, label="job result")

    submit_id = _request_id(submit)
    allocation = acquisition.get("allocation")
    if type(allocation) is not dict or type(allocation.get("pbs_jobid")) is not str:
        raise CollectionError("acquisition receipt has no allocation.pbs_jobid")
    allocation_id = allocation["pbs_jobid"]
    result_id = result.get("pbs_jobid")
    if type(result_id) is not str:
        raise CollectionError("job result has no pbs_jobid")
    normalized_submit_id = normalize_request_id(submit_id)
    if (normalized_submit_id != normalize_request_id(allocation_id)
            or normalized_submit_id != normalize_request_id(result_id)):
        raise CollectionError(
            "job ID mismatch: "
            f"submit={submit_id!r} allocation={allocation_id!r} result={result_id!r}"
        )
    if type(result.get("calibrate_rc")) is not int:
        raise CollectionError("job result has no integer calibrate_rc")
    if not _scheduler_name_matches(stdout_path, stream="stdout", job_id=submit_id):
        raise CollectionError("scheduler stdout filename does not carry the request ID")
    if not _scheduler_name_matches(stderr_path, stream="stderr", job_id=submit_id):
        raise CollectionError("scheduler stderr filename does not carry the request ID")

    try:
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise CollectionError(f"cannot read scheduler stderr: {exc}") from exc
    accounting = _accounting_summary(stderr_text)

    payload = {
        "schema_version": "pegasus-final-receipt/v1",
        "job_id": submit_id,
        "collected_epoch": int(time.time()) if collected_epoch is None else collected_epoch,
        "cross_checks": {
            "submit_vs_allocation_job_id": True,
            "submit_vs_job_result_job_id": True,
            "scheduler_filenames_carry_job_id": True,
            "scheduler_accounting_present": True,
        },
        "submit_receipt": _file_record(submit_path),
        "acquisition_receipt": _file_record(acquisition_path),
        "job_result": result,
        "scheduler_logs": {
            "stdout": _file_record(stdout_path),
            "stderr": _file_record(stderr_path),
            "accounting_summary_raw": accounting,
        },
        "staging_manifest": _staging_manifest(
            job_staging,
            excluded=(output_path, stdout_path, stderr_path),
        ),
        "calibrator_attempt_manifest": _staging_manifest(
            attempt_dir,
            excluded=(output_path, stdout_path, stderr_path),
        ),
    }
    return payload


def collect(
    *,
    attempt_dir: Path,
    job_staging: Path,
    stdout_path: Path,
    stderr_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    target = output_path or (attempt_dir / "final-receipt.json")
    payload = build_final_receipt(
        attempt_dir=attempt_dir,
        job_staging=job_staging,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_path=target,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise CollectionError(f"cannot create final receipt {target}: {exc}") from exc
    return target


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--job-staging", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True, dest="stdout_path")
    parser.add_argument("--stderr", type=Path, required=True, dest="stderr_path")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        target = collect(
            attempt_dir=args.attempt_dir,
            job_staging=args.job_staging,
            stdout_path=args.stdout_path,
            stderr_path=args.stderr_path,
            output_path=args.output,
        )
    except CollectionError as exc:
        error = {
            "schema_version": "pegasus-collector-error/v1",
            "ok": False,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
        json.dump(error, sys.stderr, ensure_ascii=False, sort_keys=True)
        sys.stderr.write("\n")
        return 2
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
