# -*- coding: utf-8 -*-
"""Exact future-authority qsub binding contract for T-126."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .artifacts import QualificationArtifactError
from .retry_index import RetryIndexError, validate_retry_index


_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_JOB_ID_TEXT = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_JOB_ID = re.compile(_JOB_ID_TEXT)
_STDOUT = re.compile(
    rf"(?:Request (?P<request>{_JOB_ID_TEXT}) submitted\.|"
    rf"(?P<plain>{_JOB_ID_TEXT}))\n")
QSUB_BINDING_KEYS = frozenset({
    "schema_version", "job_id", "nonce", "submission_intent_sha256",
    "qsub_invocation_sha256", "retry_index", "qsub_returncode",
    "qsub_stdout_raw",
})


class QsubBindingError(QualificationArtifactError):
    """A qsub binding is not the exact v2 authority corpus."""


def job_id_from_qsub_stdout(value: object) -> str:
    """Derive one canonical job ID from exact strict-decoded qsub stdout."""
    if type(value) is not str:
        raise QsubBindingError("qsub stdout must be an exact string")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise QsubBindingError("qsub stdout is not strict UTF-8") from exc
    match = _STDOUT.fullmatch(value)
    if match is None:
        raise QsubBindingError("qsub stdout grammar mismatch")
    return match.group("request") or match.group("plain")


def validate_qsub_binding(
        value: object, *, expected_nonce: str | None = None,
        expected_intent_sha256: str | None = None,
        expected_invocation_sha256: str | None = None,
        expected_retry_index: int | None = None,
        expected_job_id: str | None = None,
) -> dict[str, Any]:
    """Validate exact keys, exact scalar types, and stdout-derived job ID."""
    if type(value) is not dict or set(value) != QSUB_BINDING_KEYS:
        raise QsubBindingError("qsub binding key set mismatch")
    row: Mapping[str, Any] = value
    if row["schema_version"] != "t126-qsub-binding/v2":
        raise QsubBindingError("qsub binding schema must be v2")
    if type(row["job_id"]) is not str or _JOB_ID.fullmatch(
            row["job_id"]) is None:
        raise QsubBindingError("qsub binding job ID grammar mismatch")
    if type(row["nonce"]) is not str or _HEX32.fullmatch(row["nonce"]) is None:
        raise QsubBindingError("qsub binding nonce mismatch")
    if (type(row["submission_intent_sha256"]) is not str
            or _HEX64.fullmatch(row["submission_intent_sha256"]) is None):
        raise QsubBindingError("qsub binding intent hash mismatch")
    if (type(row["qsub_invocation_sha256"]) is not str
            or _HEX64.fullmatch(row["qsub_invocation_sha256"]) is None):
        raise QsubBindingError("qsub binding invocation hash mismatch")
    try:
        validate_retry_index(row["retry_index"])
    except RetryIndexError as exc:
        raise QsubBindingError(
            "qsub binding retry index must be exact int") from exc
    if expected_retry_index is not None:
        try:
            validate_retry_index(expected_retry_index)
        except RetryIndexError as exc:
            raise QsubBindingError(
                "expected qsub binding retry index must be exact int") from exc
    if type(row["qsub_returncode"]) is not int or row["qsub_returncode"] != 0:
        raise QsubBindingError("qsub binding returncode must be exact int zero")
    if job_id_from_qsub_stdout(row["qsub_stdout_raw"]) != row["job_id"]:
        raise QsubBindingError("qsub binding job ID is not stdout-derived")
    expected = (
        ("nonce", expected_nonce),
        ("submission_intent_sha256", expected_intent_sha256),
        ("qsub_invocation_sha256", expected_invocation_sha256),
        ("retry_index", expected_retry_index),
        ("job_id", expected_job_id),
    )
    for key, required in expected:
        if required is not None and row[key] != required:
            raise QsubBindingError(f"qsub binding {key} differs from authority")
    return dict(row)
