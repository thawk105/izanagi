# -*- coding: utf-8 -*-
"""Phase 3 stage 8c preregistration gate report.

The report is derived from the source evaluator at a requested commit.  It does
not authorize a formal measurement; CLI success only means that the source
preregistration report is effective.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Optional, Sequence

from . import s8c_preregistration as _prereg


__all__ = ("gate_report_at",)

_SCHEMA_VERSION = "s8c-gate-report/v1"
_STATUS_EFFECTIVE = "PREREGISTRATION_EFFECTIVE"
_STATUS_NOT_EFFECTIVE = "PREREGISTRATION_NOT_EFFECTIVE"


class _ArgumentParseError(Exception):
    """Argument parsing failed without writing plain-text CLI output."""


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _ArgumentParseError(message)


def _status_counts(members: object, values: object) -> dict[str, int]:
    counts = collections.Counter(item.status.value for item in values)
    return {member.value: counts[member.value] for member in members}


def _project_activation_report(
    report: _prereg.ActivationReport,
) -> dict[str, object]:
    """Project one source report without re-evaluating its conjunction."""
    return {
        "schema_version": _SCHEMA_VERSION,
        "status": (
            _STATUS_EFFECTIVE
            if report.effective is True
            else _STATUS_NOT_EFFECTIVE
        ),
        "authorization": {
            "authority": "USER",
            "report_effect": "DOES_NOT_AUTHORIZE",
            "decision_in_report": "NOT_REPRESENTED",
        },
        "source": {
            "commit": report.commit,
            "condition_freeze_valid": report.condition_freeze_valid,
            "freeze_generation": report.freeze_generation,
            "protected_sha256": report.protected_sha256,
            "freeze_reason_code": report.freeze_reason_code,
            "decider_version": report.decider_version,
            "decider_version_matches": report.decider_version_matches,
            "decider_version_reason_code": report.decider_version_reason_code,
            "core_module_blob_sha256": report.core_module_blob_sha256,
            "evaluator_module_blob_sha256": report.evaluator_module_blob_sha256,
            "projection_module_blob_sha256": report.projection_module_blob_sha256,
            "effective": report.effective,
        },
        "section5": {
            "source_findings_present": bool(report.section5_findings),
            "total": len(report.section5_findings),
            "status_counts": _status_counts(
                _prereg.FieldStatus,
                report.section5_findings,
            ),
            "findings": [
                {
                    "name": finding.name,
                    "status": finding.status.value,
                    "reason_code": finding.reason_code,
                }
                for finding in report.section5_findings
            ],
        },
        "predicates": {
            "total": len(report.predicates),
            "status_counts": _status_counts(
                _prereg.PredicateStatus,
                report.predicates,
            ),
            "results": [
                {
                    "id": result.id,
                    "status": result.status.value,
                    "reason_code": result.reason_code,
                    "evidence": [
                        {
                            "path": evidence.path,
                            "blob_sha256": evidence.blob_sha256,
                        }
                        for evidence in result.evidence
                    ],
                }
                for result in report.predicates
            ],
        },
    }


def gate_report_at(
    repo_root: Path | str,
    commit: str = "HEAD",
) -> dict[str, object]:
    """Re-evaluate ``commit`` once and return its structured gate report."""
    source = _prereg.activation_report_at(repo_root, commit)
    return _project_activation_report(source)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _error_json(exc: Exception) -> str:
    return json.dumps(
        {
            "schema_version": _SCHEMA_VERSION,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        },
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("-h", "--help", dest="help_requested", action="store_true")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    return parser


def _main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _build_parser().parse_args(argv)
        if args.help_requested:
            raise _ArgumentParseError("help requested")
        report = gate_report_at(args.repo_root, args.commit)
        source = report["source"]
        if not isinstance(source, dict):
            raise TypeError("gate report source must be an object")
        effective = source["effective"] is True
        rendered = _canonical_json(report)
    except Exception as exc:  # noqa: BLE001 - CLI failures have a fixed exit class
        print(_error_json(exc))
        return 2
    print(rendered)
    return 0 if effective else 1


if __name__ == "__main__":
    raise SystemExit(_main())
