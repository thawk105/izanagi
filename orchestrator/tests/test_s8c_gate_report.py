# -*- coding: utf-8 -*-
"""Regression tests for the stage 8c gate-report projection and CLI."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import s8c_gate_report as M  # noqa: E402
from orchestrator.campaign import s8c_preregistration as P  # noqa: E402


def _evidence() -> tuple[P.EvidenceRef, ...]:
    """Reverse lexical order, with one duplicate path carrying distinct bytes."""
    return (
        P.EvidenceRef(path="z/report.json", blob_sha256="1" * 64),
        P.EvidenceRef(path="z/report.json", blob_sha256="2" * 64),
        P.EvidenceRef(path="a/report.json", blob_sha256="3" * 64),
    )


def _source_report(
    *,
    effective: bool = False,
    section5_findings: tuple[P.Section5Finding, ...] | None = None,
    predicates: tuple[P.PredicateResult, ...] | None = None,
) -> P.ActivationReport:
    if section5_findings is None:
        section5_findings = (
            P.Section5Finding("omega", P.FieldStatus.FILLED, "filled-source"),
            P.Section5Finding("beta", P.FieldStatus.INVALID, "invalid-source"),
            P.Section5Finding("alpha", P.FieldStatus.UNFILLED, "unfilled-source"),
        )
    if predicates is None:
        predicates = (
            P.PredicateResult(
                "C05", P.PredicateStatus.SATISFIED, "satisfied-source", _evidence()
            ),
            P.PredicateResult(
                "C04", P.PredicateStatus.UNSATISFIED, "unsatisfied-source", ()
            ),
            P.PredicateResult(
                "C03",
                P.PredicateStatus.EVIDENCE_UNDEFINED,
                "undefined-source",
                (),
            ),
            P.PredicateResult("C02", P.PredicateStatus.ERROR, "error-source", ()),
            P.PredicateResult(
                "C01",
                P.PredicateStatus.NOT_EVALUATED,
                "not-evaluated-source",
                (),
            ),
        )
    return P.ActivationReport(
        commit="a" * 40,
        condition_freeze_valid=True,
        freeze_generation=7,
        protected_sha256="b" * 64,
        freeze_reason_code="freeze-source",
        decider_version="s8c-decider/v6",
        decider_version_matches=True,
        decider_version_reason_code="decider-source",
        section5_findings=section5_findings,
        predicates=predicates,
        core_module_blob_sha256="c" * 64,
        evaluator_module_blob_sha256="d" * 64,
        projection_module_blob_sha256="e" * 64,
        effective=effective,
    )


def _all_satisfied_source(*, effective: bool) -> P.ActivationReport:
    findings = (
        P.Section5Finding("second", P.FieldStatus.FILLED, "second-filled"),
        P.Section5Finding("first", P.FieldStatus.FILLED, "first-filled"),
    )
    predicates = (
        P.PredicateResult("C02", P.PredicateStatus.SATISFIED, "second", ()),
        P.PredicateResult("C01", P.PredicateStatus.SATISFIED, "first", ()),
    )
    return _source_report(
        effective=effective,
        section5_findings=findings,
        predicates=predicates,
    )


@pytest.mark.parametrize(
    ("effective", "expected"),
    [
        (True, "PREREGISTRATION_EFFECTIVE"),
        (False, "PREREGISTRATION_NOT_EFFECTIVE"),
    ],
)
def test_m1_status_is_one_to_one_projection_of_source_effective(
    effective: bool,
    expected: str,
) -> None:
    source = _all_satisfied_source(effective=effective)
    report = M._project_activation_report(source)
    assert report["status"] == expected
    assert report["source"]["effective"] is effective


def test_m2_non_effective_cli_exit_is_one(monkeypatch, capsys) -> None:
    report = M._project_activation_report(_source_report(effective=False))
    monkeypatch.setattr(M, "gate_report_at", lambda repo_root, commit: report)
    assert M._main(["--repo-root", "/repo", "--commit", "candidate"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == report
    assert captured.err == ""


def test_m3_authorization_contract_does_not_decide_or_authorize() -> None:
    report = M._project_activation_report(_all_satisfied_source(effective=True))
    assert report["authorization"] == {
        "authority": "USER",
        "report_effect": "DOES_NOT_AUTHORIZE",
        "decision_in_report": "NOT_REPRESENTED",
    }


def test_m4_evidence_path_hash_order_and_count_are_exact() -> None:
    source = _source_report()
    report = M._project_activation_report(source)
    evidence = report["predicates"]["results"][0]["evidence"]
    assert evidence == [
        {"path": item.path, "blob_sha256": item.blob_sha256}
        for item in source.predicates[0].evidence
    ]
    assert [item["path"] for item in evidence] == [
        "z/report.json",
        "z/report.json",
        "a/report.json",
    ]
    assert len(evidence) == 3


def test_m5_source_status_reason_order_and_count_are_unchanged() -> None:
    source = _source_report()
    report = M._project_activation_report(source)
    assert [
        (item["name"], item["status"], item["reason_code"])
        for item in report["section5"]["findings"]
    ] == [
        (item.name, item.status.value, item.reason_code)
        for item in source.section5_findings
    ]
    assert [
        (item["id"], item["status"], item["reason_code"])
        for item in report["predicates"]["results"]
    ] == [
        (item.id, item.status.value, item.reason_code)
        for item in source.predicates
    ]
    assert report["section5"]["total"] == len(source.section5_findings)
    assert report["predicates"]["total"] == len(source.predicates)


def test_m6_gate_report_calls_activation_once_with_exact_args(monkeypatch) -> None:
    source = _source_report()
    spy = mock.Mock(return_value=source)
    monkeypatch.setattr(M._prereg, "activation_report_at", spy)
    repo_root = Path("/synthetic/repo")

    report = M.gate_report_at(repo_root, "candidate")

    spy.assert_called_once_with(repo_root, "candidate")
    assert report["source"]["commit"] == source.commit


def test_m7_status_counts_include_every_enum_member_and_zero() -> None:
    source = _source_report(
        section5_findings=(
            P.Section5Finding("only", P.FieldStatus.FILLED, "only-source"),
        ),
        predicates=(
            P.PredicateResult(
                "only", P.PredicateStatus.SATISFIED, "only-source", ()
            ),
        ),
    )
    report = M._project_activation_report(source)
    assert report["section5"]["status_counts"] == {
        "FILLED": 1,
        "UNFILLED": 0,
        "INVALID": 0,
    }
    assert report["predicates"]["status_counts"] == {
        "SATISFIED": 1,
        "UNSATISFIED": 0,
        "EVIDENCE_UNDEFINED": 0,
        "ERROR": 0,
        "NOT_EVALUATED": 0,
    }


def test_source_metadata_is_an_exact_projection() -> None:
    source = _source_report()
    report = M._project_activation_report(source)
    assert report["source"] == {
        "commit": source.commit,
        "condition_freeze_valid": source.condition_freeze_valid,
        "freeze_generation": source.freeze_generation,
        "protected_sha256": source.protected_sha256,
        "freeze_reason_code": source.freeze_reason_code,
        "decider_version": source.decider_version,
        "decider_version_matches": source.decider_version_matches,
        "decider_version_reason_code": source.decider_version_reason_code,
        "core_module_blob_sha256": source.core_module_blob_sha256,
        "evaluator_module_blob_sha256": source.evaluator_module_blob_sha256,
        "projection_module_blob_sha256": source.projection_module_blob_sha256,
        "effective": source.effective,
    }


def test_empty_section5_source_is_explicit_and_not_invented() -> None:
    report = M._project_activation_report(
        _source_report(section5_findings=())
    )
    assert report["section5"] == {
        "source_findings_present": False,
        "total": 0,
        "status_counts": {"FILLED": 0, "UNFILLED": 0, "INVALID": 0},
        "findings": [],
    }


def test_public_evaluation_api_exposes_no_arbitrary_report_projector() -> None:
    assert M.__all__ == ("gate_report_at",)
    assert callable(M.gate_report_at)
    assert not hasattr(M, "project_activation_report")


def test_effective_cli_exit_is_zero_and_json_is_canonical(monkeypatch, capsys) -> None:
    report = M._project_activation_report(_all_satisfied_source(effective=True))
    monkeypatch.setattr(M, "gate_report_at", lambda repo_root, commit: report)

    assert M._main(["--repo-root", "/repo", "--commit", "candidate"]) == 0

    captured = capsys.readouterr()
    expected = json.dumps(
        report,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert captured.out == expected + "\n"
    assert captured.err == ""


def test_predicate_error_is_non_effective_exit_one_not_exception_two(
    monkeypatch,
    capsys,
) -> None:
    source = _source_report(
        effective=False,
        predicates=(
            P.PredicateResult("C01", P.PredicateStatus.ERROR, "source-error", ()),
        ),
    )
    report = M._project_activation_report(source)
    monkeypatch.setattr(M, "gate_report_at", lambda repo_root, commit: report)

    assert M._main([]) == 1
    assert json.loads(capsys.readouterr().out) == report


def test_cli_evaluation_exception_is_json_exit_two(monkeypatch, capsys) -> None:
    def fail(repo_root: Path, commit: str) -> dict[str, object]:
        raise RuntimeError(f"cannot evaluate {repo_root}:{commit}")

    monkeypatch.setattr(M, "gate_report_at", fail)
    assert M._main(["--repo-root", "/repo", "--commit", "candidate"]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "schema_version": "s8c-gate-report/v1",
        "error": {
            "type": "RuntimeError",
            "message": "cannot evaluate /repo:candidate",
        },
    }
    assert captured.err == ""


def test_cli_serialization_exception_is_json_exit_two(monkeypatch, capsys) -> None:
    report = M._project_activation_report(_source_report())
    monkeypatch.setattr(M, "gate_report_at", lambda repo_root, commit: report)

    def fail(value: object) -> str:
        raise TypeError(f"cannot serialize {type(value).__name__}")

    monkeypatch.setattr(M, "_canonical_json", fail)
    assert M._main([]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "schema_version": "s8c-gate-report/v1",
        "error": {
            "type": "TypeError",
            "message": "cannot serialize dict",
        },
    }
    assert captured.err == ""


def test_real_repo_head_is_only_compared_with_its_source_report() -> None:
    source = P.activation_report_at(_ROOT, "HEAD")
    report = M.gate_report_at(_ROOT, "HEAD")
    expected_status = (
        "PREREGISTRATION_EFFECTIVE"
        if source.effective
        else "PREREGISTRATION_NOT_EFFECTIVE"
    )
    assert report["status"] == expected_status
    assert report["source"] == {
        "commit": source.commit,
        "condition_freeze_valid": source.condition_freeze_valid,
        "freeze_generation": source.freeze_generation,
        "protected_sha256": source.protected_sha256,
        "freeze_reason_code": source.freeze_reason_code,
        "decider_version": source.decider_version,
        "decider_version_matches": source.decider_version_matches,
        "decider_version_reason_code": source.decider_version_reason_code,
        "core_module_blob_sha256": source.core_module_blob_sha256,
        "evaluator_module_blob_sha256": source.evaluator_module_blob_sha256,
        "projection_module_blob_sha256": source.projection_module_blob_sha256,
        "effective": source.effective,
    }
    assert report["section5"]["source_findings_present"] is bool(
        source.section5_findings
    )
    assert report["section5"]["total"] == len(source.section5_findings)
    assert [
        (item["name"], item["status"], item["reason_code"])
        for item in report["section5"]["findings"]
    ] == [
        (item.name, item.status.value, item.reason_code)
        for item in source.section5_findings
    ]
    assert report["predicates"]["total"] == len(source.predicates)
    assert [
        {
            "id": item.id,
            "status": item.status.value,
            "reason_code": item.reason_code,
            "evidence": [
                {
                    "path": evidence.path,
                    "blob_sha256": evidence.blob_sha256,
                }
                for evidence in item.evidence
            ],
        }
        for item in source.predicates
    ] == report["predicates"]["results"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
