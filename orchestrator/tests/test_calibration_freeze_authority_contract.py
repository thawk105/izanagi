# -*- coding: utf-8 -*-
"""Calibration/freeze authority fixture manifest 契約の受入・負例。"""
from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.tests import calibration_freeze_authority_contract as contract


EXPECTED_ROW_IDS = (
    "CFAB-11.1-01",
    "CFAB-11.1-02",
    "CFAB-11.1-03",
    "CFAB-11.1-04",
    "CFAB-11.1-05",
    "CFAB-11.1-06",
    "CFAB-11.2-01",
    "CFAB-7.2-01",
    "CFAB-7.2-02",
    "CFAB-7.2-03",
)
EXPECTED_EXECUTABLE_FIXTURE_IDS = (
    "activation-head-consistency",
    "environment-floor-contract-consistency",
    "unapproved-generation-no-authority",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _write_record(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_bytes(value) + b"\n")


def _read_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes())


def _synthetic_repository(tmp_path: Path) -> tuple[Path, Path]:
    fixture_root = tmp_path / "calibration_freeze_authority"
    shutil.copytree(contract.FIXTURE_ROOT, fixture_root)
    design_doc = tmp_path / contract.DESIGN_DOC.name
    shutil.copy2(contract.DESIGN_DOC, design_doc)
    return fixture_root, design_doc


def _manifest_path(fixture_root: Path) -> Path:
    return fixture_root / "manifest.v1.json"


def _profile_path(fixture_root: Path) -> Path:
    return fixture_root / "ruling-profile.v1.json"


def _rewrite_manifest(
    fixture_root: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    path = _manifest_path(fixture_root)
    document = _read_record(path)
    mutate(document)
    _write_record(path, document)


def _rewrite_case(
    fixture_root: Path,
    fixture_id: str,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    path = fixture_root / "cases" / f"{fixture_id}.json"
    document = _read_record(path)
    mutate(document)
    _write_record(path, document)


def _rewrite_profile(
    fixture_root: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    path = _profile_path(fixture_root)
    document = _read_record(path)
    mutate(document)
    _write_record(path, document)


def _refresh_entries_sha(document: dict[str, Any], section: str) -> None:
    document[section]["entries_sha256"] = hashlib.sha256(
        _canonical_bytes(document[section]["entries"])
    ).hexdigest()


def _assert_rejected(
    fixture_root: Path, design_doc: Path, expected_reason: str
) -> None:
    try:
        contract._validate_repository(fixture_root, design_doc)
    except contract.ContractError as exc:
        assert expected_reason in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ContractError containing {expected_reason!r}")


def test_real_repository_contract_is_consistent_but_incomplete() -> None:
    result = contract.validate_repository()
    assert set(result) == {
        "status",
        "pending_count",
        "unresolved_count",
        "row_ids",
        "executable_fixture_ids",
    }
    assert result == {
        "status": "incomplete",
        "pending_count": 7,
        "unresolved_count": 6,
        "row_ids": EXPECTED_ROW_IDS,
        "executable_fixture_ids": EXPECTED_EXECUTABLE_FIXTURE_IDS,
    }
    assert contract.extract_design_row_ids() == EXPECTED_ROW_IDS
    assert tuple(case["fixture_id"] for case in contract.load_fixture_cases()) == tuple(
        sorted(
            {
                "activation-head-consistency",
                "approved-freeze-reference",
                "bundle-identity-propagation",
                "candidate-type-preservation",
                "environment-floor-contract-consistency",
                "floor-seal-consistency",
                "freeze-history-immutability",
                "orphan-generation-no-authority",
                "post-cutoff-bundle-identity",
                "unapproved-generation-no-authority",
            }
        )
    )


def test_design_row_removed_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    target = "| `CFAB-7.2-02` |"
    matches = [line for line in lines if line.startswith(target)]
    assert len(matches) == 1
    design_doc.write_text(
        "".join(line for line in lines if not line.startswith(target)), encoding="utf-8"
    )
    _assert_rejected(fixture_root, design_doc, "row_coverage does not exactly match design row IDs")


def test_declared_design_row_removed_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "row ID = `CFAB-11.2-01`。\n"
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, "", 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "row_coverage does not exactly match design row IDs",
    )


def test_orphan_case_file_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    source = _read_record(fixture_root / "cases" / "approved-freeze-reference.json")
    source["fixture_id"] = "orphan-case"
    _write_record(fixture_root / "cases" / "orphan-case.json", source)
    _assert_rejected(fixture_root, design_doc, "orphan case files=['orphan-case']")


def test_manifest_entry_without_case_file_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    (fixture_root / "cases" / "approved-freeze-reference.json").unlink()
    _assert_rejected(
        fixture_root, design_doc, "missing case files=['approved-freeze-reference']"
    )


def test_manifest_raw_sha256_literal_tamper_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        document["fixtures"]["entries"][0]["raw_sha256"] = "0" * 64
        _refresh_entries_sha(document, "fixtures")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(fixture_root, design_doc, "fixture raw SHA-256 mismatch")


def test_case_file_bytes_tamper_with_manifest_unchanged_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_case(
        fixture_root,
        "approved-freeze-reference",
        lambda document: document.__setitem__(
            "entrypoint", document["entrypoint"] + "_changed"
        ),
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "fixture raw SHA-256 mismatch for approved-freeze-reference",
    )


def test_false_pending_count_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_manifest(
        fixture_root,
        lambda document: document["row_coverage"].__setitem__("pending_count", 8),
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "row_coverage.pending_count does not match pending fixture cases",
    )


def test_unresolved_binding_in_row_coverage_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        document["row_coverage"]["entries"][0]["fixture_id"] = (
            "unresolved:CFAB-Q3-ROLLBACK"
        )
        _refresh_entries_sha(document, "row_coverage")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(fixture_root, design_doc, "unresolved: binding is forbidden")


def test_executable_binding_without_positive_control_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_case(
        fixture_root,
        "activation-head-consistency",
        lambda document: document.__setitem__("positive_control", None),
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "executable binding_state requires both controls and null pending_reason",
    )


def test_pending_binding_with_positive_control_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    positive = {
        "builder": "pending-must-not-have-builder",
        "case_id": "pending-must-not-have-control",
        "expected_decision": "accept",
    }
    _rewrite_case(
        fixture_root,
        "approved-freeze-reference",
        lambda document: document.__setitem__("positive_control", positive),
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "pending binding_state requires null controls and a pending_reason",
    )


def test_s2_profile_without_not_applicable_guarantee_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        by_id = {ruling["ruling_id"]: ruling for ruling in document["rulings"]}
        by_id["CFAB-S-SEAL"].update(status="resolved", selection="S2")

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "CFAB-S-GUARANTEE must be not-applicable when CFAB-S-SEAL is S2",
    )


def test_manifest_status_cannot_claim_complete_while_gates_remain(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_manifest(
        fixture_root, lambda document: document.__setitem__("status", "complete")
    )
    _assert_rejected(
        fixture_root, design_doc, "manifest status disagrees with computed repository status"
    )


def test_fixture_entries_sha256_is_independent_self_consistency_check(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_manifest(
        fixture_root,
        lambda document: document["fixtures"].__setitem__("entries_sha256", "0" * 64),
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "fixtures.entries_sha256 does not match canonical entries bytes",
    )


def test_ruling_profile_order_drift_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        document["rulings"][0], document["rulings"][1] = (
            document["rulings"][1],
            document["rulings"][0],
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "ruling profile IDs/order do not exactly match design §8.1",
    )


def test_not_applicable_outside_applicability_rule_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        document["rulings"][4].update(status="not-applicable", selection=None)

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "not-applicable is forbidden outside CFAB-S-GUARANTEE",
    )


def test_resolved_ruling_without_design_selection_enum_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        document["rulings"][4].update(status="resolved", selection="invented-choice")

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "selection has no design-defined enum yet",
    )


def test_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    path = _manifest_path(fixture_root)
    raw = path.read_bytes()
    path.write_bytes(b'{"status":"incomplete",' + raw[1:])
    _assert_rejected(fixture_root, design_doc, "duplicate JSON key is forbidden: status")


def test_non_finite_json_constant_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    path = _manifest_path(fixture_root)
    raw = path.read_bytes()
    changed = raw.replace(b'"count":10', b'"count":NaN', 1)
    assert changed != raw
    path.write_bytes(changed)
    _assert_rejected(fixture_root, design_doc, "non-finite JSON constant is forbidden: NaN")


def test_unknown_case_key_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_case(
        fixture_root,
        "approved-freeze-reference",
        lambda document: document.__setitem__("unknown", "value"),
    )
    _assert_rejected(fixture_root, design_doc, "keys must be exact")


def test_placeholder_string_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_case(
        fixture_root,
        "approved-freeze-reference",
        lambda document: document.__setitem__("pending_reason", "TODO implement later"),
    )
    _assert_rejected(fixture_root, design_doc, "contains a placeholder string")


def test_bool_is_not_accepted_as_integer(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _rewrite_manifest(
        fixture_root,
        lambda document: document["fixtures"].__setitem__("count", True),
    )
    _assert_rejected(fixture_root, design_doc, "bool is forbidden")


def test_noncanonical_record_bytes_are_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    path = _profile_path(fixture_root)
    path.write_bytes(b" " + path.read_bytes())
    _assert_rejected(
        fixture_root, design_doc, "raw bytes are not canonical JSON plus one LF"
    )


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        temporary: tempfile.TemporaryDirectory[str] | None = None
        try:
            parameters = inspect.signature(test).parameters
            if parameters:
                assert tuple(parameters) == ("tmp_path",), (
                    f"unsupported plain-runner parameters for {test.__name__}: "
                    f"{tuple(parameters)}"
                )
                temporary = tempfile.TemporaryDirectory(
                    prefix="cfab-contract-", dir=str(ROOT)
                )
                test(Path(temporary.name))
            else:
                test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
        finally:
            if temporary is not None:
                temporary.cleanup()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
