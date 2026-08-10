# -*- coding: utf-8 -*-
"""Calibration-freeze authority executable fixtures の production 結線テスト。"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.tests.calibration_freeze_authority_contract import (  # noqa: E402
    load_fixture_cases,
    load_manifest,
)
from orchestrator.tests.calibration_freeze_authority_execution import (  # noqa: E402
    BUILDERS,
    execute_case,
    run_all_executable,
)


def _executable_cases() -> tuple:
    return tuple(
        case for case in load_fixture_cases()
        if case["binding_state"] == "executable"
    )


def test_executable_positive_controls_accept() -> None:
    observed = {
        case["fixture_id"]: execute_case(case, "positive_control")
        for case in _executable_cases()
    }
    assert observed
    assert observed == {fixture_id: "accept" for fixture_id in observed}


def test_executable_negative_cases_reject() -> None:
    observed = {
        case["fixture_id"]: execute_case(case, "negative_case")
        for case in _executable_cases()
    }
    assert observed
    assert observed == {fixture_id: "reject" for fixture_id in observed}


def test_run_all_executable_matches_manifest() -> None:
    manifest = load_manifest()
    cases_by_id = {case["fixture_id"]: case for case in load_fixture_cases()}
    manifest_ids = {
        entry["fixture_id"]
        for entry in manifest["fixtures"]["entries"]
    }
    expected = {
        fixture_id for fixture_id in manifest_ids
        if cases_by_id[fixture_id]["binding_state"] == "executable"
    }
    summary = run_all_executable()
    assert set(summary["executed"]) == expected
    assert set(summary["results"]) == expected
    assert all(
        set(result) == {"positive_control", "negative_case"}
        for result in summary["results"].values()
    )


def test_builder_registry_is_bijective() -> None:
    required = {
        selected["builder"]
        for case in _executable_cases()
        for selected in (case["positive_control"], case["negative_case"])
    }
    assert set(BUILDERS) == required


def test_execution_evidence_matches_fixture_declarations() -> None:
    cases = {
        case["fixture_id"]: case
        for case in _executable_cases()
    }
    summary = run_all_executable()
    assert set(summary["invocations"]) == set(cases)
    for fixture_id, recorded_cases in summary["invocations"].items():
        fixture = cases[fixture_id]
        assert set(recorded_cases) == {"positive_control", "negative_case"}
        for which, evidence in recorded_cases.items():
            declared = fixture[which]
            assert set(evidence) == {
                "arguments_sha256",
                "builder",
                "case_id",
                "decision",
                "entrypoint",
                "outcome_reason",
            }
            assert evidence["builder"] == declared["builder"]
            assert evidence["case_id"] == declared["case_id"]
            assert evidence["decision"] == declared["expected_decision"]
            assert evidence["entrypoint"] == fixture["entrypoint"].replace(":", ".")
            assert evidence["arguments_sha256"] == declared["case_id"].rsplit(
                "-sha256-", 1,
            )[1]


def test_negative_cases_reach_expected_production_gate() -> None:
    expected_reasons = {
        "activation-head-consistency": "activation head serial 不一致",
        "environment-floor-contract-consistency": (
            "protocol.contract_sha256 と resolver が返した env 契約が不一致"
        ),
        "freeze-history-immutability": "history-mutated",
        "orphan-generation-no-authority": "result-mismatch:generation_number",
        "unapproved-generation-no-authority": "pointer-approval",
    }
    summary = run_all_executable()
    observed = {
        fixture_id: records["negative_case"]["outcome_reason"]
        for fixture_id, records in summary["invocations"].items()
    }
    assert set(observed) == set(expected_reasons)
    for fixture_id, expected_reason in expected_reasons.items():
        assert expected_reason in observed[fixture_id]


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
