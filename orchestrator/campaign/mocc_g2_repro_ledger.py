#!/usr/bin/env python3
"""Build the frozen MoCC TRACE=1 G2 reproduction-study ledger."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "mocc-g2-repro-ledger/v1"
STUDY_ID = "dev-wave-mocc-g2-repro-20260826"
FROZEN_COMMIT = "f7f6dd2e70ccb27f531011881e47c45617d3ffaf"
FROZEN_PREREGISTRATION_SHA256 = (
    "182abe5cdad001d8ec799bbf33d097674ad7292cd8e5880826ca56654dd6e235"
)
PLANNED_N = 42
EXPECTED_EXCLUDED_SUBMISSIONS = 2
DEFAULT_ROOT = Path("output/insights/2026-08-26_mocc-g2-repro")
SUBMIT_RECEIPT_SCHEMA_VERSION = "pegasus-submit-receipt/v2"
PILOT_RECEIPT_SCHEMA_VERSION = "mocc-trace-pilot-receipt/v3"
JOB_RESULT_SCHEMA_VERSION = "mocc-trace-pilot-job-result/v2"
FAILURE_SCHEMA_VERSION = "mocc-trace-pilot-failure/v1"
DENOMINATOR_VERDICTS = frozenset({"serializable", "non-serializable"})
LEDGER_COLUMNS = (
    "ordinal",
    "batch",
    "nonce",
    "request_id",
    "submit_epoch",
    "head",
)
EVIDENCE_FILES = (
    "submit-receipt.json",
    "reservation.json",
    "verifier.json",
    "failure.json",
    "job-result.json",
    "mocc-trace-pilot-receipt.json",
)
CLASSIFICATIONS = (
    "certified",
    "non_serializable",
    "indeterminate",
    "verifier_infra",
    "stage_failure",
    "no_verdict",
)
EXCLUDED_CLASSIFICATIONS = (
    "indeterminate",
    "verifier_infra",
    "stage_failure",
    "no_verdict",
)
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class LedgerError(ValueError):
    """The frozen study inputs do not satisfy the fail-closed contract."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise LedgerError(message)


def _reject(message: str) -> None:
    raise LedgerError(message)


def _duplicate_rejecting_object(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _reject(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    _reject(f"non-finite JSON number is forbidden: {value}")


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise LedgerError(f"cannot read {label}: {path}: {exc}") from exc


def _json_from_bytes(raw: bytes, path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        _reject(f"JSON top level must be an object: {path}")
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ascii_positive_integer(text: str, label: str) -> int:
    if not text or any(char < "0" or char > "9" for char in text):
        _reject(f"{label} must be an ASCII positive integer")
    value = int(text)
    if value <= 0:
        _reject(f"{label} must be positive")
    return value


def _load_submission_ledger(root: Path) -> tuple[list[dict[str, Any]], str]:
    path = root / "submission-ledger.tsv"
    raw = _read_bytes(path, "submission ledger")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LedgerError(f"submission ledger is not UTF-8: {path}") from exc
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
        _reject(
            "submission ledger header must be exactly: "
            + "\t".join(LEDGER_COLUMNS)
        )
    rows: list[dict[str, Any]] = []
    for line_number, raw_row in enumerate(reader, start=2):
        if None in raw_row or any(value is None for value in raw_row.values()):
            _reject(f"malformed submission ledger row at line {line_number}")
        ordinal = _ascii_positive_integer(
            raw_row["ordinal"], f"line {line_number} ordinal"
        )
        batch = _ascii_positive_integer(
            raw_row["batch"], f"line {line_number} batch"
        )
        _ascii_positive_integer(
            raw_row["submit_epoch"], f"line {line_number} submit_epoch"
        )
        if ordinal != len(rows) + 1:
            _reject("submission ledger ordinals must be the sequence 1..42")
        if not raw_row["nonce"]:
            _reject(f"line {line_number} nonce must not be empty")
        if not raw_row["request_id"]:
            _reject(f"line {line_number} request_id must not be empty")
        if not _HEX40.fullmatch(raw_row["head"]):
            _reject(f"line {line_number} head must be lowercase 40-hex")
        if raw_row["head"] != FROZEN_COMMIT:
            _reject(
                f"line {line_number} head must equal frozen commit "
                f"{FROZEN_COMMIT}"
            )
        rows.append(
            {
                "ordinal": ordinal,
                "batch": batch,
                "nonce": raw_row["nonce"],
                "request_id": raw_row["request_id"],
            }
        )
    if len(rows) != PLANNED_N:
        _reject(
            f"submission ledger row count must be exactly {PLANNED_N}, got {len(rows)}"
        )
    nonces = [row["nonce"] for row in rows]
    if len(set(nonces)) != len(nonces):
        _reject("submission ledger nonces must be unique")
    request_ids = [row["request_id"] for row in rows]
    if len(set(request_ids)) != len(request_ids):
        _reject("submission ledger request_ids must be unique")
    for row in rows:
        expected_batch = (row["ordinal"] - 1) // 6 + 1
        if row["batch"] != expected_batch:
            _reject(
                "submission ledger must map ordinals 1..42 to batches 1..7 "
                f"with six runs each; ordinal {row['ordinal']} has batch "
                f"{row['batch']}, expected {expected_batch}"
            )
    return rows, _sha256(raw)


def _require_schema(
    value: Mapping[str, Any], path: Path, expected: str, label: str
) -> None:
    observed = value.get("schema_version")
    if observed != expected:
        _reject(
            f"{label} schema_version must be {expected}: {path}; "
            f"observed {observed!r}"
        )


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        _reject(f"{label} must be a non-empty string")
    return value


def _submit_receipt_identity(
    receipt: Mapping[str, Any], path: Path
) -> tuple[str, str, str]:
    _require_schema(
        receipt, path, SUBMIT_RECEIPT_SCHEMA_VERSION, "submit receipt"
    )
    nonce = _nonempty_string(
        receipt.get("submission_nonce"), f"submission_nonce in {path}"
    )
    source_commit = _nonempty_string(
        receipt.get("source_commit"), f"source_commit in {path}"
    )
    if not _HEX40.fullmatch(source_commit):
        _reject(f"source_commit must be lowercase 40-hex: {path}")
    qsub = receipt.get("qsub")
    if not isinstance(qsub, dict):
        _reject(f"qsub must be an object: {path}")
    request_id = _nonempty_string(
        qsub.get("request_id"), f"qsub.request_id in {path}"
    )
    if not isinstance(receipt.get("dry_run"), bool):
        _reject(f"dry_run must be a boolean: {path}")
    return nonce, source_commit, request_id


def _load_canonical_submissions(
    root: Path,
) -> tuple[
    dict[str, tuple[Path, dict[str, Any], bytes]],
    dict[str, Any],
]:
    submissions_dir = root / "submissions"
    if not submissions_dir.is_dir():
        _reject(f"canonical submissions directory is required: {submissions_dir}")
    try:
        entries = sorted(submissions_dir.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise LedgerError(
            f"cannot enumerate canonical submissions: {submissions_dir}: {exc}"
        ) from exc
    if any(not entry.is_dir() for entry in entries):
        _reject(
            "every canonical submissions entry must be a nonce directory: "
            f"{submissions_dir}"
        )

    by_nonce: dict[str, tuple[Path, dict[str, Any], bytes]] = {}
    included: dict[str, tuple[Path, dict[str, Any], bytes]] = {}
    excluded: list[dict[str, str]] = []
    excluded_dry_run_flags: list[bool] = []
    for entry in entries:
        path = entry / "submit-receipt.json"
        raw = _read_bytes(path, "submit receipt")
        receipt = _json_from_bytes(raw, path)
        nonce, source_commit, _ = _submit_receipt_identity(receipt, path)
        if entry.name != nonce:
            _reject(
                "canonical submission directory name must equal submission_nonce: "
                f"directory={entry.name!r}, receipt={nonce!r}"
            )
        if nonce in by_nonce:
            _reject(f"duplicate submission_nonce in canonical submissions: {nonce}")
        record = (entry, receipt, raw)
        by_nonce[nonce] = record
        if source_commit == FROZEN_COMMIT:
            if receipt["dry_run"] is not False:
                _reject(
                    "frozen-commit canonical submission must not be a dry-run: "
                    f"{path}"
                )
            included[nonce] = record
        else:
            dry_run = receipt.get("dry_run")
            excluded_dry_run_flags.append(dry_run)
            exclusion_kind = (
                "pre-freeze dry-run" if dry_run else "pre-freeze liveness probe"
            )
            excluded.append(
                {
                    "nonce": nonce,
                    "source_commit": source_commit,
                    "reason": (
                        f"{exclusion_kind}; source_commit differs from frozen commit"
                    ),
                }
            )

    if len(included) != PLANNED_N:
        _reject(
            "canonical submissions at frozen commit must contain exactly "
            f"{PLANNED_N} receipts, got {len(included)}"
        )
    if len(excluded) != EXPECTED_EXCLUDED_SUBMISSIONS:
        _reject(
            "canonical submissions must contain exactly two excluded pre-freeze "
            f"receipts, got {len(excluded)}"
        )
    if sorted(excluded_dry_run_flags) != [False, True]:
        _reject(
            "excluded pre-freeze submissions must be exactly one dry-run and "
            "one liveness probe"
        )
    closure = {
        "enumerated_submission_count": len(by_nonce),
        "frozen_commit_submission_count": len(included),
        "frozen_commit_nonces": sorted(included),
        "excluded_submissions": sorted(excluded, key=lambda item: item["nonce"]),
    }
    return included, closure


def _load_run_submit_receipts(
    root: Path,
    ledger_rows: Sequence[Mapping[str, Any]],
    canonical: Mapping[str, tuple[Path, dict[str, Any], bytes]],
) -> tuple[dict[str, tuple[Path, dict[str, Any], bytes]], set[str]]:
    runs_dir = root / "runs"
    if not runs_dir.is_dir():
        _reject(f"runs directory is required: {runs_dir}")
    try:
        run_entries = {path.name for path in runs_dir.iterdir() if path.is_dir()}
    except OSError as exc:
        raise LedgerError(
            f"cannot enumerate runs directory: {runs_dir}: {exc}"
        ) from exc
    expected_entries = {str(ordinal) for ordinal in range(1, PLANNED_N + 1)}
    if run_entries != expected_entries:
        _reject(
            "run directories must be exactly ordinals 1..42; "
            f"missing={sorted(expected_entries - run_entries)}, "
            f"extra={sorted(run_entries - expected_entries)}"
        )

    by_nonce: dict[str, tuple[Path, dict[str, Any], bytes]] = {}
    request_ids: set[str] = set()
    for row in ledger_rows:
        run_dir = runs_dir / str(row["ordinal"])
        path = run_dir / "submit-receipt.json"
        raw = _read_bytes(path, "run submit receipt")
        receipt = _json_from_bytes(raw, path)
        nonce, source_commit, request_id = _submit_receipt_identity(receipt, path)
        if nonce != row["nonce"]:
            _reject(
                "ordinal directory submit receipt nonce must equal its ledger row: "
                f"ordinal {row['ordinal']}"
            )
        if source_commit != FROZEN_COMMIT:
            _reject(
                f"run submit receipt source_commit must equal frozen commit: {path}"
            )
        if request_id != row["request_id"]:
            _reject(
                "submission ledger request_id must equal submit receipt "
                f"qsub.request_id: ordinal {row['ordinal']}"
            )
        if request_id in request_ids:
            _reject(f"duplicate request_id in run submit receipts: {request_id}")
        request_ids.add(request_id)
        canonical_record = canonical.get(nonce)
        if canonical_record is None:
            _reject(f"run nonce is absent from frozen canonical submissions: {nonce}")
        if raw != canonical_record[2]:
            _reject(
                "run submit receipt must be byte-identical to its canonical "
                f"submission receipt: ordinal {row['ordinal']}"
            )
        by_nonce[nonce] = (run_dir, receipt, raw)
    return by_nonce, set(by_nonce)


def classify_run(
    failure: Mapping[str, Any] | None,
    *,
    completed_receipt_present: bool,
) -> str:
    """Implement the pre-registration section 4 table in first-match order."""

    if failure is None:
        return "certified" if completed_receipt_present else "no_verdict"
    stage = failure.get("stage")
    rc = failure.get("rc")
    if stage == "verifier":
        if type(rc) is int and rc == 1:
            return "non_serializable"
        if type(rc) is int and rc == 3:
            return "indeterminate"
        if type(rc) is int and rc == 2:
            return "verifier_infra"
        return "no_verdict"
    if isinstance(stage, str) and stage:
        return "stage_failure"
    return "no_verdict"


def _result_projection(
    verifier: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[Any]]:
    if verifier is None:
        return None, []
    results = verifier.get("results")
    if not isinstance(results, list) or not results:
        return None, []
    first = results[0]
    if not isinstance(first, dict):
        return None, []
    anomalies = first.get("anomalies")
    if not isinstance(anomalies, list):
        anomalies = []
    phenomena = [
        anomaly.get("phenomenon") if isinstance(anomaly, dict) else None
        for anomaly in anomalies
    ]
    return first, phenomena


def is_g2_numerator(
    classification: str,
    result: Mapping[str, Any] | None,
    phenomena: Sequence[Any],
) -> bool:
    """Return the frozen run-level section 5 numerator predicate."""

    return bool(
        classification == "non_serializable"
        and result is not None
        and result.get("verdict") == "non-serializable"
        and type(result.get("total_cycles")) is int
        and result["total_cycles"] >= 1
        and any(phenomenon == "G2" for phenomenon in phenomena)
    )


def _binomial_cdf(k: int, n: int, probability: float) -> float:
    return sum(
        math.comb(n, value)
        * probability**value
        * (1.0 - probability) ** (n - value)
        for value in range(k + 1)
    )


def _binomial_upper_tail(k: int, n: int, probability: float) -> float:
    return sum(
        math.comb(n, value)
        * probability**value
        * (1.0 - probability) ** (n - value)
        for value in range(k, n + 1)
    )


def clopper_pearson(
    k: int, n: int, *, confidence: float = 0.95
) -> tuple[float, float]:
    """Equal-tailed exact binomial interval via finite sums and bisection."""

    if type(k) is not int or type(n) is not int or not 0 <= k <= n:
        raise ValueError("Clopper-Pearson requires integers satisfying 0 <= k <= n")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be strictly between zero and one")
    if n == 0:
        return 0.0, 1.0
    tail_probability = (1.0 - confidence) / 2.0

    if k == 0:
        lower = 0.0
    else:
        lo = 0.0
        hi = 1.0
        for _ in range(200):
            mid = (lo + hi) / 2.0
            if _binomial_upper_tail(k, n, mid) < tail_probability:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2.0

    if k == n:
        upper = 1.0
    else:
        lo = 0.0
        hi = 1.0
        for _ in range(200):
            mid = (lo + hi) / 2.0
            if _binomial_cdf(k, n, mid) > tail_probability:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2.0
    return lower, upper


def _optional_object(
    run_dir: Path, name: str, raw_by_name: Mapping[str, bytes]
) -> dict[str, Any] | None:
    raw = raw_by_name.get(name)
    if raw is None:
        return None
    return _json_from_bytes(raw, run_dir / name)


def _job_id_matches_request_id(job_id: Any, request_id: str, label: str) -> None:
    observed = _nonempty_string(job_id, label)
    normalized = observed[2:] if observed.startswith("0:") else observed
    if normalized != request_id:
        _reject(
            f"{label} must identify request_id {request_id!r}; observed {observed!r}"
        )


def _validate_outcome_consistency(
    *,
    ordinal: int,
    failure: Mapping[str, Any] | None,
    completed: Mapping[str, Any] | None,
    result: Mapping[str, Any] | None,
) -> None:
    verdict = result.get("verdict") if result is not None else None
    terminal_verdict = (
        isinstance(verdict, str) and verdict in DENOMINATOR_VERDICTS
    )
    stage = failure.get("stage") if failure is not None else None
    rc = failure.get("rc") if failure is not None else None

    if completed is not None and verdict != "serializable":
        _reject(
            "completed pilot receipt requires verifier verdict serializable: "
            f"ordinal {ordinal}, observed {verdict!r}"
        )
    if failure is None:
        if completed is None and terminal_verdict:
            _reject(
                "terminal verifier verdict without completed receipt or failure: "
                f"ordinal {ordinal}"
            )
        return
    if stage == "verifier" and rc == 1:
        if completed is not None or verdict != "non-serializable":
            _reject(
                "verifier rc=1 requires no completed receipt and verdict "
                f"non-serializable: ordinal {ordinal}, observed {verdict!r}"
            )
        return
    if stage == "verifier" and terminal_verdict:
        _reject(
            "verifier failure other than rc=1 contradicts a terminal verdict: "
            f"ordinal {ordinal}, rc={rc!r}, verdict={verdict!r}"
        )
    if stage != "verifier" and terminal_verdict and completed is None:
        _reject(
            "terminal verifier verdict before a non-verifier failure requires a "
            f"completed receipt: ordinal {ordinal}, stage={stage!r}"
        )


def _make_run(
    ledger_row: Mapping[str, Any],
    run_dir: Path,
    submit_receipt: Mapping[str, Any],
    submit_raw: bytes,
) -> dict[str, Any]:
    raw_by_name: dict[str, bytes] = {"submit-receipt.json": submit_raw}
    for name in EVIDENCE_FILES[1:]:
        path = run_dir / name
        if path.is_file():
            raw_by_name[name] = _read_bytes(path, name)

    failure = _optional_object(run_dir, "failure.json", raw_by_name)
    reservation = _optional_object(run_dir, "reservation.json", raw_by_name)
    completed = _optional_object(
        run_dir, "mocc-trace-pilot-receipt.json", raw_by_name
    )
    verifier = _optional_object(run_dir, "verifier.json", raw_by_name)
    job_result = _optional_object(run_dir, "job-result.json", raw_by_name)

    if failure is not None:
        _require_schema(
            failure,
            run_dir / "failure.json",
            FAILURE_SCHEMA_VERSION,
            "failure",
        )
        _nonempty_string(
            failure.get("stage"),
            f"failure stage at ordinal {ledger_row['ordinal']}",
        )
        if type(failure.get("rc")) is not int:
            _reject(
                f"failure rc must be an integer: ordinal {ledger_row['ordinal']}"
            )
    if completed is not None:
        _require_schema(
            completed,
            run_dir / "mocc-trace-pilot-receipt.json",
            PILOT_RECEIPT_SCHEMA_VERSION,
            "pilot receipt",
        )
    if job_result is not None:
        _require_schema(
            job_result,
            run_dir / "job-result.json",
            JOB_RESULT_SCHEMA_VERSION,
            "job-result",
        )

    request_id = ledger_row["request_id"]
    _, _, submit_request_id = _submit_receipt_identity(
        submit_receipt, run_dir / "submit-receipt.json"
    )
    if submit_request_id != request_id:
        _reject(
            "submission ledger request_id must equal run submit receipt "
            f"qsub.request_id: ordinal {ledger_row['ordinal']}"
        )
    if reservation is None:
        _reject(f"reservation.json is required: ordinal {ledger_row['ordinal']}")
    if reservation.get("nonce") != ledger_row["nonce"]:
        _reject(
            "reservation nonce must equal submission ledger nonce: "
            f"ordinal {ledger_row['ordinal']}"
        )
    reservation_host = _nonempty_string(
        reservation.get("host"),
        f"reservation host at ordinal {ledger_row['ordinal']}",
    )
    _job_id_matches_request_id(
        reservation.get("job_id"),
        request_id,
        f"reservation job_id at ordinal {ledger_row['ordinal']}",
    )

    if failure is not None:
        _job_id_matches_request_id(
            failure.get("pbs_jobid"),
            request_id,
            f"failure pbs_jobid at ordinal {ledger_row['ordinal']}",
        )
    if completed is not None:
        pbs = completed.get("pbs")
        if not isinstance(pbs, dict):
            _reject(
                f"pilot receipt pbs must be an object: ordinal {ledger_row['ordinal']}"
            )
        completed_host = _nonempty_string(
            pbs.get("hostname"),
            f"pilot receipt pbs.hostname at ordinal {ledger_row['ordinal']}",
        )
        if completed_host != reservation_host:
            _reject(
                "reservation host must equal pilot receipt pbs.hostname: "
                f"ordinal {ledger_row['ordinal']}"
            )
        _job_id_matches_request_id(
            pbs.get("jobid"),
            request_id,
            f"pilot receipt pbs.jobid at ordinal {ledger_row['ordinal']}",
        )
        source = completed.get("source")
        if (
            not isinstance(source, dict)
            or source.get("outer_repo_commit") != FROZEN_COMMIT
        ):
            _reject(
                "pilot receipt source.outer_repo_commit must equal frozen commit: "
                f"ordinal {ledger_row['ordinal']}"
            )
    if job_result is not None:
        if completed is None:
            _reject(
                f"job-result requires a pilot receipt: ordinal {ledger_row['ordinal']}"
            )
        _job_id_matches_request_id(
            job_result.get("pbs_jobid"),
            request_id,
            f"job-result pbs_jobid at ordinal {ledger_row['ordinal']}",
        )
        expected_receipt_sha = _sha256(
            raw_by_name["mocc-trace-pilot-receipt.json"]
        )
        if job_result.get("receipt_sha256") != expected_receipt_sha:
            _reject(
                "job-result receipt_sha256 must bind the pilot receipt: "
                f"ordinal {ledger_row['ordinal']}"
            )

    classification = classify_run(
        failure, completed_receipt_present=completed is not None
    )
    result, phenomena = _result_projection(verifier)
    _validate_outcome_consistency(
        ordinal=ledger_row["ordinal"],
        failure=failure,
        completed=completed,
        result=result,
    )
    if classification in {"certified", "non_serializable"} and result is None:
        _reject(
            "denominator run requires verifier.json results[0]: "
            f"ordinal {ledger_row['ordinal']}"
        )
    verdict = result.get("verdict") if result is not None else None
    in_denominator = bool(
        classification in {"certified", "non_serializable"}
        and isinstance(verdict, str)
        and verdict in DENOMINATOR_VERDICTS
    )
    if classification in {"certified", "non_serializable"} and not in_denominator:
        _reject(
            "denominator classification requires verdict serializable or "
            f"non-serializable: ordinal {ledger_row['ordinal']}"
        )
    if classification == "certified" and job_result is None:
        _reject(
            f"certified run requires job-result.json: ordinal {ledger_row['ordinal']}"
        )
    in_numerator = is_g2_numerator(classification, result, phenomena)

    stats = result.get("stats") if result is not None else None
    integrity = result.get("integrity") if result is not None else None
    return {
        "ordinal": ledger_row["ordinal"],
        "batch": ledger_row["batch"],
        "nonce": ledger_row["nonce"],
        "request_id": ledger_row["request_id"],
        "host": reservation_host,
        "classification": classification,
        "failure_stage": failure.get("stage") if failure is not None else None,
        "failure_rc": failure.get("rc") if failure is not None else None,
        "verdict": result.get("verdict") if result is not None else None,
        "total_cycles": result.get("total_cycles") if result is not None else None,
        "anomaly_count": result.get("anomaly_count") if result is not None else None,
        "phenomena": phenomena,
        "txns": stats.get("txns") if isinstance(stats, dict) else None,
        "integrity_clean": (
            integrity.get("clean") if isinstance(integrity, dict) else None
        ),
        "in_denominator": in_denominator,
        "in_numerator": in_numerator,
        "artifact_sha256": {
            name: _sha256(raw) for name, raw in sorted(raw_by_name.items())
        },
    }


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def _sensitivity_rows(
    runs: Sequence[Mapping[str, Any]], key: str
) -> list[dict[str, Any]]:
    groups: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[run[key]].append(run)
    ordered_keys = sorted(
        groups,
        key=lambda value: (value is None, str(value)),
    )
    return [
        {
            key: value,
            "k": sum(bool(run["in_numerator"]) for run in groups[value]),
            "m": sum(bool(run["in_denominator"]) for run in groups[value]),
        }
        for value in ordered_keys
    ]


def build_ledger(root: Path | str) -> dict[str, Any]:
    """Validate closure and return the complete JSON-compatible study ledger."""

    root = Path(root)
    ledger_rows, ledger_sha = _load_submission_ledger(root)
    canonical_receipts, submission_closure = _load_canonical_submissions(root)
    ledger_nonces = {row["nonce"] for row in ledger_rows}
    canonical_nonces = set(canonical_receipts)
    if ledger_nonces != canonical_nonces:
        _reject(
            "submission ledger and frozen canonical submission nonce sets must "
            f"match exactly; ledger_only={sorted(ledger_nonces - canonical_nonces)}, "
            f"canonical_only={sorted(canonical_nonces - ledger_nonces)}"
        )
    receipts, receipt_nonces = _load_run_submit_receipts(
        root, ledger_rows, canonical_receipts
    )
    if receipt_nonces != canonical_nonces:
        _reject(
            "runs and frozen canonical submission nonce sets must match exactly; "
            f"runs_only={sorted(receipt_nonces - canonical_nonces)}, "
            f"canonical_only={sorted(canonical_nonces - receipt_nonces)}"
        )

    preregistration_raw = _read_bytes(
        root / "pre-registration.md", "pre-registration document"
    )
    preregistration_sha = _sha256(preregistration_raw)
    if preregistration_sha != FROZEN_PREREGISTRATION_SHA256:
        _reject(
            "pre-registration SHA-256 must equal frozen pin "
            f"{FROZEN_PREREGISTRATION_SHA256}; observed {preregistration_sha}"
        )
    runs = [
        _make_run(row, *receipts[row["nonce"]])
        for row in ledger_rows
    ]
    classification_counts = Counter(run["classification"] for run in runs)
    m = sum(bool(run["in_denominator"]) for run in runs)
    k = sum(bool(run["in_numerator"]) for run in runs)
    missing = PLANNED_N - m
    lower, upper = clopper_pearson(k, m)
    reported_phenomena = Counter(
        phenomenon
        for run in runs
        if run["in_denominator"]
        for phenomenon in run["phenomena"]
        if isinstance(phenomenon, str)
    )
    non_g2_only_ordinals = [
        run["ordinal"]
        for run in runs
        if run["classification"] == "non_serializable"
        and run["phenomena"]
        and all(phenomenon in {"G0", "G1c"} for phenomenon in run["phenomena"])
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "study": {
            "id": STUDY_ID,
            "frozen_commit": FROZEN_COMMIT,
            "preregistration_sha256": preregistration_sha,
            "planned_N": PLANNED_N,
        },
        "submission_closure": submission_closure,
        "submission_ledger_sha256": ledger_sha,
        "runs": runs,
        "summary": {
            "N": PLANNED_N,
            "m": m,
            "k": k,
            "missing": missing,
            "classification_counts": {
                name: classification_counts[name] for name in CLASSIFICATIONS
            },
            "exclusions": {
                name: {
                    "count": classification_counts[name],
                    "ordinals": [
                        run["ordinal"]
                        for run in runs
                        if run["classification"] == name
                    ],
                }
                for name in EXCLUDED_CLASSIFICATIONS
            },
            "reported_phenomena_counts": dict(sorted(reported_phenomena.items())),
            "g0_g1c_only": {
                "count": len(non_g2_only_ordinals),
                "ordinals": non_g2_only_ordinals,
            },
        },
        "estimates": {
            "k_over_N": _ratio(k, PLANNED_N),
            "k_over_m": _ratio(k, m),
            "clopper_pearson_two_sided_95": {
                "lower": lower,
                "upper": upper,
            },
            "identification_interval": [
                k / PLANNED_N,
                (k + missing) / PLANNED_N,
            ],
            "effective_detection_power": 1.0 - 0.9**m,
            "planned_power_achieved": m == PLANNED_N,
        },
        "secondary_analysis_e": {
            "by_batch": _sensitivity_rows(runs, "batch"),
            "by_host": _sensitivity_rows(runs, "host"),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        help="create-only JSON destination; omit to write JSON to stdout",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        payload = build_ledger(args.root)
        raw = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
        if args.output is None:
            sys.stdout.write(raw)
        else:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(raw)
        return 0
    except (LedgerError, OSError) as exc:
        print(f"mocc_g2_repro_ledger: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
