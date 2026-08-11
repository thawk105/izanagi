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
    "freeze-history-immutability",
    "orphan-generation-no-authority",
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


def _ruling_by_id(document: dict[str, Any], ruling_id: str) -> dict[str, Any]:
    return next(
        ruling for ruling in document["rulings"] if ruling["ruling_id"] == ruling_id
    )


def _gate_by_id(document: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return next(
        gate
        for gate in document["required_gates"]["entries"]
        if gate["gate_id"] == gate_id
    )


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
        contract.validate_repository(fixture_root, design_doc)
    except contract.ContractError as exc:
        assert expected_reason in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ContractError containing {expected_reason!r}")


def test_real_repository_contract_is_consistent_but_incomplete() -> None:
    """裁定後の正しい exact 要約へ期待値を置換するだけで、受理集合には中立である。"""

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
        "pending_count": 5,
        "unresolved_count": 2,
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


def test_current_repository_is_rejected_as_stage0_incomplete() -> None:
    """裁定後の正しい blocker 診断へ期待値を置換するだけで、受理集合には中立である。"""

    try:
        contract.require_stage0_complete()
    except contract.ContractError as exc:
        assert str(exc) == (
            "stage 0 is incomplete: status=incomplete, pending=5, "
            "applicable_unresolved=2, blocking_gates=3"
        )
    else:
        raise AssertionError("the incomplete repository was accepted as stage 0 complete")


def test_adjudicated_ruling_and_gate_projection_is_exact() -> None:
    """snapshot pin として現行 fixture・manifest literal・module 定数の三者一致を固定する。"""

    profile = contract.load_ruling_profile()
    assert tuple(
        (ruling["ruling_id"], ruling["status"], ruling["selection"])
        for ruling in profile["rulings"]
    ) == (
        ("CFAB-Q1-PLACEMENT", "resolved", "outside-authority-directory"),
        ("CFAB-Q2-ACTOR", "resolved", "human-approval-and-activation"),
        ("CFAB-Q2-MEANING", "resolved", "digest-plus-inspection-receipt"),
        ("CFAB-Q3-LOCKSTEP", "resolved", "both-components-change"),
        ("CFAB-Q3-ROLLBACK", "resolved", "forward-compensating-generation"),
        ("CFAB-Q3-REVOCATION", "resolved", "no-lower-fallback-fail-closed"),
        ("CFAB-Q3-XF-POSITION", "resolved", "after-upper-activation"),
        ("CFAB-Q4-HEAD-MODE", "resolved", "literal-pinned"),
        ("CFAB-S-SEAL", "unresolved", None),
        ("CFAB-S-GUARANTEE", "unresolved", None),
        ("CFAB-B-SIDE-EFFECT", "unresolved", None),
        ("FREEZE-U-A1", "resolved", "activation-window"),
    )
    manifest = contract.load_manifest()
    assert tuple(
        (gate["gate_id"], gate["owner"], gate["status"])
        for gate in manifest["required_gates"]["entries"]
    ) == (
        ("CFAB-Q3-REVOCATION", "user", "resolved"),
        ("CFAB-Q3-ROLLBACK", "user", "resolved"),
        ("CFAB-Q3-XF-POSITION", "user", "resolved"),
        ("CFAB-S8-S10-CONTRADICTION", "user", "resolved"),
        (
            "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
            "stage1-and-later",
            "pending",
        ),
        ("FREEZE-AX-TOPOLOGY", "lower-impl-wave", "nonconforming"),
        ("FREEZE-CONFORMANCE-LITERAL", "lower-wa-wave", "unresolved"),
        ("FREEZE-U-A1", "user", "resolved"),
    )


def test_required_gate_entries_have_independent_module_sha_pin() -> None:
    """snapshot pin として現行 fixture・manifest literal・module 定数の三者一致を固定する。"""

    manifest = contract.load_manifest()
    gates = manifest["required_gates"]
    entries_sha256 = hashlib.sha256(_canonical_bytes(gates["entries"])).hexdigest()
    assert entries_sha256 == gates["entries_sha256"]
    assert entries_sha256 == contract._EXPECTED_REQUIRED_GATES_ENTRIES_SHA256


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


def test_case_and_manifest_hash_tamper_together_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    fixture_id = "approved-freeze-reference"
    _rewrite_case(
        fixture_root,
        fixture_id,
        lambda document: document.__setitem__(
            "entrypoint", document["entrypoint"] + "_changed"
        ),
    )

    def mutate(document: dict[str, Any]) -> None:
        entry = next(
            entry
            for entry in document["fixtures"]["entries"]
            if entry["fixture_id"] == fixture_id
        )
        case_path = fixture_root / entry["path"]
        entry["raw_sha256"] = hashlib.sha256(case_path.read_bytes()).hexdigest()
        _refresh_entries_sha(document, "fixtures")

    _rewrite_manifest(fixture_root, mutate)
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


def test_adjudicated_rollback_cannot_regress_to_unresolved(tmp_path: Path) -> None:
    """rollback の裁定前状態を新たに拒否し、profile の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-Q3-ROLLBACK").update(
            status="unresolved", selection=None
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "adjudicated and deferred ruling states do not match the independent pin",
    )


def test_adjudicated_revocation_cannot_regress_to_unresolved(tmp_path: Path) -> None:
    """revocation の裁定前状態を新たに拒否し、profile の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-Q3-REVOCATION").update(
            status="unresolved", selection=None
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "adjudicated and deferred ruling states do not match the independent pin",
    )


def test_adjudicated_xf_position_cannot_regress_to_unresolved(tmp_path: Path) -> None:
    """X_f 位置の裁定前状態を新たに拒否し、profile の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-Q3-XF-POSITION").update(
            status="unresolved", selection=None
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "adjudicated and deferred ruling states do not match the independent pin",
    )


def test_adjudicated_u_a1_cannot_regress_to_unresolved(tmp_path: Path) -> None:
    """U-A1 の裁定前状態を新たに拒否し、profile の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "FREEZE-U-A1").update(
            status="unresolved", selection=None
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "adjudicated and deferred ruling states do not match the independent pin",
    )


def test_deferred_seal_ruling_cannot_be_resolved(tmp_path: Path) -> None:
    """先送り中の seal 解決を新たに拒否し、profile の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-S-SEAL").update(
            status="resolved", selection="S1"
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "adjudicated and deferred ruling states do not match the independent pin",
    )


def test_rejected_post_activation_lease_is_rejected(tmp_path: Path) -> None:
    """却下済み post-activation lease を新たに拒否し、enum の受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "FREEZE-U-A1").update(
            status="resolved", selection="post-activation-lease"
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "selection is outside its allowed enum",
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


def test_required_gate_removed_is_rejected(tmp_path: Path) -> None:
    """同じ gate 削除負例を index 指定から ID 指定へ変えるだけで、中立である。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        entries = document["required_gates"]["entries"]
        entries.remove(_gate_by_id(document, "CFAB-Q3-REVOCATION"))
        document["required_gates"]["count"] = len(entries)
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates entries do not exactly match",
    )


def test_required_gate_owner_changed_is_rejected(tmp_path: Path) -> None:
    """等価な owner drift 負例へ ID 指定で再照準するだけで、受理集合には中立である。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _gate_by_id(document, "FREEZE-AX-TOPOLOGY")["owner"] = "wrong-owner"
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates entries do not exactly match",
    )


def test_required_gate_resolved_without_evidence_is_rejected(tmp_path: Path) -> None:
    """裁定後の正例から依然負例の fixture assignment へ再照準するだけで、中立である。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _gate_by_id(
            document, "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT"
        )["status"] = "resolved"
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates entries do not exactly match",
    )


def test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected(
    tmp_path: Path,
) -> None:
    """hash 再計算済みの gate 並べ替えも新たに拒否し、受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        entries = document["required_gates"]["entries"]
        entries[0], entries[1] = entries[1], entries[0]
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates.entries_sha256 must match canonical entries bytes "
        "and the independent module pin",
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


def test_design_selection_column_matches_selection_enums(tmp_path: Path) -> None:
    """設計だけで selection を広げる drift を新たに拒否し、受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "| `FREEZE-U-A1` | resolved | `activation-window` |"
    replacement = (
        "| `FREEZE-U-A1` | resolved | `activation-window` / "
        "`post-activation-lease` |"
    )
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §8.1 selection column does not exactly match selection enums",
    )


def test_design_literals_hidden_in_html_comment_are_not_authoritative(
    tmp_path: Path,
) -> None:
    """comment にだけ canonical literal を残す文書を新たに拒否する。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "| `FREEZE-U-A1` | resolved | `activation-window` |"
    replacement = (
        "<!--\n"
        f"{target}\n"
        "-->\n"
        "<tr><td>FREEZE-U-A1</td><td>resolved</td>"
        "<td>activation-window / post-activation-lease</td></tr>"
    )
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document must not contain HTML comments",
    )


def test_design_stage_scope_matches_fixture_assignment_gate_id(tmp_path: Path) -> None:
    """設計の段集合だけを広げる drift を新たに拒否し、受理集合を狭める。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "段 1〜4 と段 6〜8 である"
    replacement = "段 1〜4 と段 5〜8 である"
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage scope does not exactly match the fixture assignment gate ID",
    )


def test_not_applicable_outside_applicability_rule_is_rejected(
    tmp_path: Path,
) -> None:
    """同じ Q3 負例を index 指定から ID 指定へ変えるだけで、中立である。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-Q3-ROLLBACK").update(
            status="not-applicable", selection=None
        )

    _rewrite_profile(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "not-applicable is forbidden outside CFAB-S-GUARANTEE",
    )


def test_resolved_ruling_without_design_selection_enum_is_rejected(
    tmp_path: Path,
) -> None:
    """裁定後の正例から依然負例の未裁定 B へ再照準するだけで、中立である。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _ruling_by_id(document, "CFAB-B-SIDE-EFFECT").update(
            status="resolved", selection="invented-choice"
        )

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
