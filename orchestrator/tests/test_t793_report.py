from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

import pytest

import orchestrator.publication.report as report_module
from orchestrator.publication.report import (
    _scan_d291_supersession,
    approval_report_to_dict,
    build_approval_report,
    main,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_D291_FOLD_COMMIT = "b13b7ea840ad51199f40b3a534c9d1cdb422af2e"


def _fold_decisions_blob() -> bytes:
    return subprocess.run(
        ["git", "show", f"{CANONICAL_D291_FOLD_COMMIT}:docs/decisions.md"],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def test_deny_only_report_contains_authority_and_both_submission_denials() -> None:
    rendered = approval_report_to_dict(REPOSITORY_ROOT)
    assert rendered["submission_authority"] == "not_granted"
    assert rendered["pilot_submission"] == "forbidden"
    assert rendered["main_submission"] == "forbidden"
    assert rendered["supersession_scan"] == {
        "status": "possible_supersession",
        "decision_ids": ["D292"],
    }
    assert set(rendered["roles"]) == {"publication_core", "source_addendum_b"}
    for role in rendered["roles"].values():
        assert role["approval_status"] == "not_asserted_after_supersession"
        assert role["submission_authority"] == "not_granted"


def test_authority_none_is_bound_to_d291_without_rewriting_documents() -> None:
    rendered = build_approval_report(REPOSITORY_ROOT)
    assert rendered["authority_binding"] == {
        "canonical_source": "D291",
        "document_envelope_authority": "none",
        "document_bytes_rewritten": "no",
    }
    for role in rendered["roles"].values():
        assert role["approval_authority"] == "canonical_decision_D291"
        assert role["document_envelope_authority"] == "none"


def test_actual_head_d292_reference_is_reported_fail_closed() -> None:
    decisions = (REPOSITORY_ROOT / "docs" / "decisions.md").read_bytes()
    scan = _scan_d291_supersession(decisions)
    assert scan.status == "possible_supersession"
    assert scan.decision_ids == ("D292",)


def test_later_explicit_supersession_stops_current_approval_assertion() -> None:
    decisions = _fold_decisions_blob()
    decisions += (
        "\n## D999. synthetic supersession\n\n"
        "**決定:** D291 の publication_core role の承認を失効させる。\n"
    ).encode()
    scan = _scan_d291_supersession(decisions)
    assert scan.status == "possible_supersession"
    assert scan.decision_ids == ("D999",)


def test_later_reference_is_possible_supersession_even_when_negated() -> None:
    decisions = _fold_decisions_blob()
    decisions += (
        "\n## D999. synthetic non-supersession\n\n"
        "**決定:** D291 を supersede しない。\n"
    ).encode()
    assert _scan_d291_supersession(decisions).status == "possible_supersession"


def test_fenced_later_reference_is_also_fail_closed() -> None:
    decisions = _fold_decisions_blob()
    decisions += (
        "\n## D999. synthetic fenced decoy\n\n"
        "```text\nD291 を supersede する。\n```\n"
    ).encode()
    assert _scan_d291_supersession(decisions).status == "possible_supersession"


def test_later_decision_without_d291_reference_keeps_positive_scan() -> None:
    decisions = _fold_decisions_blob() + (
        "\n## D999. unrelated later decision\n\n"
        "**決定:** unrelated authority remains unchanged.\n"
    ).encode()
    scan = _scan_d291_supersession(decisions)
    assert scan.status == "none_found"
    assert scan.decision_ids == ()


def test_public_renderer_accepts_only_repository_root_not_report_object() -> None:
    assert tuple(inspect.signature(approval_report_to_dict).parameters) == (
        "repository_root",
    )
    assert tuple(inspect.signature(build_approval_report).parameters) == (
        "repository_root",
    )
    assert not hasattr(report_module, "ApprovalReport")
    assert not hasattr(report_module, "SupersessionScan")
    with pytest.raises(TypeError):
        approval_report_to_dict({"roles": (), "supersession_scan": "forged"})


def test_cli_json_is_deterministic_and_deny_only(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(REPOSITORY_ROOT)]) == 0
    first = capsys.readouterr().out
    assert main([str(REPOSITORY_ROOT)]) == 0
    second = capsys.readouterr().out
    assert first == second
    assert first.endswith("\n")
    decoded = json.loads(first)
    assert decoded["submission_authority"] == "not_granted"
    assert decoded["pilot_submission"] == "forbidden"
    assert decoded["main_submission"] == "forbidden"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
