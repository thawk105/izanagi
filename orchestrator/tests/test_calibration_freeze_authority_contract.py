# -*- coding: utf-8 -*-
"""Calibration/freeze authority fixture manifest 契約の受入・負例。"""
from __future__ import annotations

import ast
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
EXPECTED_DEFERRED_FIXTURE_IDS = (
    "approved-freeze-reference",
    "bundle-identity-propagation",
    "candidate-type-preservation",
    "floor-seal-consistency",
    "post-cutoff-bundle-identity",
)
EXPECTED_STAGE0_BLOCKING_GATE_IDS = (
    "CFAB-STAGE6-POLICY-PREDICATE",
    "FREEZE-AX-TOPOLOGY",
    "FREEZE-CONFORMANCE-LITERAL",
)
EXPECTED_DEFERRED_GATE_IDS = (
    "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
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
        "raw_pending_count",
        "excluded_stage0_pending_count",
        "stage0_blocking_pending_count",
        "raw_blocking_gate_count",
        "excluded_stage0_gate_count",
        "stage0_blocking_gate_count",
        "raw_pending_fixture_ids",
        "unresolved_deferred_fixture_ids",
        "deferred_fixture_ids",
        "deferred_gate_ids",
        "stage0_blocking_gate_ids",
        "unresolved_count",
        "applicable_unresolved_count",
        "row_ids",
        "executable_fixture_ids",
    }
    assert result == {
        "status": "incomplete",
        "pending_count": 5,
        "raw_pending_count": 5,
        "excluded_stage0_pending_count": 5,
        "stage0_blocking_pending_count": 0,
        "raw_blocking_gate_count": 4,
        "excluded_stage0_gate_count": 1,
        "stage0_blocking_gate_count": 3,
        "raw_pending_fixture_ids": EXPECTED_DEFERRED_FIXTURE_IDS,
        "unresolved_deferred_fixture_ids": EXPECTED_DEFERRED_FIXTURE_IDS,
        "deferred_fixture_ids": EXPECTED_DEFERRED_FIXTURE_IDS,
        "deferred_gate_ids": EXPECTED_DEFERRED_GATE_IDS,
        "stage0_blocking_gate_ids": EXPECTED_STAGE0_BLOCKING_GATE_IDS,
        "unresolved_count": 2,
        "applicable_unresolved_count": 2,
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
            "stage 0 is incomplete: status=incomplete, raw_pending_count=5, "
            "excluded_stage0_pending_count=5, "
            "stage0_blocking_pending_count=0, applicable_unresolved_count=2, "
            "raw_blocking_gate_count=4, excluded_stage0_gate_count=1, "
            "stage0_blocking_gate_count=3"
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
        ("CFAB-R1-REVOCATION-RECORD", "user", "resolved"),
        ("CFAB-R2-STAGE0-COMPLETION", "user", "resolved"),
        ("CFAB-R3-STAGE6-PREDICATE", "user", "resolved"),
        ("CFAB-R4-CANCELLATION-RECORD", "user", "resolved"),
        ("CFAB-S8-S10-CONTRADICTION", "user", "resolved"),
        ("CFAB-STAGE6-POLICY-PREDICATE", "user", "unresolved"),
        (
            "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
            "stage1-and-later",
            "pending",
        ),
        ("FREEZE-AX-TOPOLOGY", "lower-impl-wave", "nonconforming"),
        ("FREEZE-CONFORMANCE-LITERAL", "lower-wa-wave", "unresolved"),
        ("FREEZE-U-A1", "user", "resolved"),
    )
    assignment_gate = _gate_by_id(
        manifest, "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT"
    )
    assert tuple(assignment_gate["owned_fixture_ids"]) == (
        EXPECTED_DEFERRED_FIXTURE_IDS
    )
    assert tuple(
        gate["gate_id"]
        for gate in manifest["required_gates"]["entries"]
        if "owned_fixture_ids" in gate
    ) == EXPECTED_DEFERRED_GATE_IDS


def test_design_revocation_record_schema_matches_validator() -> None:
    schema = contract._extract_design_revocation_schema(contract.DESIGN_DOC)

    assert schema == contract._UPPER_REVOCATION_SCHEMA
    assert tuple(key for key, _constraint in schema) == (
        "schema_version",
        "bundle_digest",
        "approval_raw_sha256",
        "revoked_by",
        "revoked_at",
        "scope",
        "reason",
    )
    assert not {
        "approver",
        "components",
        "authority_bundle_generation",
    }.intersection(key for key, _constraint in schema)


def test_design_cancellation_record_schema_matches_validator() -> None:
    schema = contract._extract_design_cancellation_schema(contract.DESIGN_DOC)

    assert schema == contract._UPPER_CANCELLATION_SCHEMA
    assert tuple(key for key, _constraint in schema) == (
        "schema_version",
        "pointer_raw_sha256",
        "cancelled_by",
        "cancelled_at",
        "scope",
        "reason",
    )
    assert not {
        "approver",
        "components",
        "authority_bundle_generation",
    }.intersection(key for key, _constraint in schema)


def test_design_stage6_structural_contract_matches_validator() -> None:
    predicates, control, execution_boundary, policy_gate = (
        contract._extract_stage6_contract(contract.DESIGN_DOC)
    )

    assert predicates == contract._EXPECTED_STAGE6_STRUCTURAL_PREDICATES
    assert control == contract._EXPECTED_STAGE6_STRUCTURAL_CONTROL
    assert execution_boundary == contract._EXPECTED_STAGE6_EXECUTION_BOUNDARY
    assert policy_gate == (
        "CFAB-STAGE6-POLICY-PREDICATE",
        "user",
        "unresolved",
    )
    assert policy_gate in contract._EXPECTED_REQUIRED_GATES


def test_design_stage0_projection_contract_matches_validator() -> None:
    fixture_ids = contract._extract_design_stage0_deferred_fixture_ids(
        contract.DESIGN_DOC
    )
    assert fixture_ids == EXPECTED_DEFERRED_FIXTURE_IDS
    assert fixture_ids == contract._EXPECTED_STAGE0_DEFERRED_FIXTURE_IDS

    formula = """excluded_gates   = blocking_gates ∩ {owner == stage1-and-later かつ owned_fixture_ids を持つ}
excluded_pending = pending_fixture_ids ∩ excluded_gates.owned_fixture_ids
effective_pending = raw_pending − excluded_pending
effective_gates   = blocking_gates − excluded_gates
incomplete ⇔ applicable_unresolved > 0 or effective_pending > 0 or effective_gates ≠ ∅"""
    design_text = contract.DESIGN_DOC.read_text(encoding="utf-8")
    assert design_text.count(formula) == 1


def test_design_stage0_deferred_fixture_list_drift_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "deferred fixture ID = `post-cutoff-bundle-identity`。"
    replacement = "deferred fixture ID = `unapproved-generation-no-authority`。"
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "stage 0 deferred fixture IDs do not exactly match "
        "manifest/module/design declarations",
    )


def test_stage0_remains_incomplete_after_r1_r2_r3_r4_projection() -> None:
    result = contract.validate_repository()
    assert result["status"] == "incomplete"
    assert result["raw_pending_count"] == 5
    assert result["excluded_stage0_pending_count"] == 5
    assert result["stage0_blocking_pending_count"] == 0
    assert result["applicable_unresolved_count"] == 2
    assert result["raw_blocking_gate_count"] == 4
    assert result["excluded_stage0_gate_count"] == 1
    assert result["stage0_blocking_gate_count"] == 3
    assert result["deferred_gate_ids"] == EXPECTED_DEFERRED_GATE_IDS
    assert result["stage0_blocking_gate_ids"] == (
        EXPECTED_STAGE0_BLOCKING_GATE_IDS
    )

    manifest = contract.load_manifest()
    blocking_statuses = {"unresolved", "pending", "nonconforming"}
    assert tuple(
        gate["gate_id"]
        for gate in manifest["required_gates"]["entries"]
        if gate["status"] in blocking_statuses
    ) == (
        "CFAB-STAGE6-POLICY-PREDICATE",
        "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
        "FREEZE-AX-TOPOLOGY",
        "FREEZE-CONFORMANCE-LITERAL",
    )

    try:
        contract.require_stage0_complete()
    except contract.ContractError as exc:
        assert str(exc) == (
            "stage 0 is incomplete: status=incomplete, raw_pending_count=5, "
            "excluded_stage0_pending_count=5, "
            "stage0_blocking_pending_count=0, applicable_unresolved_count=2, "
            "raw_blocking_gate_count=4, excluded_stage0_gate_count=1, "
            "stage0_blocking_gate_count=3"
        )
    else:
        raise AssertionError("the R1/R2/R3/R4 projection completed stage 0 early")


def test_required_gate_entries_have_independent_module_sha_pin() -> None:
    """snapshot pin として現行 fixture・manifest literal・module 定数の三者一致を固定する。"""

    manifest = contract.load_manifest()
    gates = manifest["required_gates"]
    entries_sha256 = hashlib.sha256(_canonical_bytes(gates["entries"])).hexdigest()
    assert entries_sha256 == gates["entries_sha256"]
    assert entries_sha256 == contract._EXPECTED_REQUIRED_GATES_ENTRIES_SHA256


def test_stage0_pin_assignments_are_ast_literals() -> None:
    source_file = inspect.getsourcefile(contract)
    assert source_file is not None
    tree = ast.parse(Path(source_file).read_text(encoding="utf-8"))
    assignments: dict[str, ast.expr] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            assignments[node.targets[0].id] = node.value

    required_gates_sha = assignments[
        "_EXPECTED_REQUIRED_GATES_ENTRIES_SHA256"
    ]
    assert isinstance(required_gates_sha, ast.Constant)
    assert isinstance(required_gates_sha.value, str)
    assert len(required_gates_sha.value) == 64

    deferred_fixture_ids = assignments[
        "_EXPECTED_STAGE0_DEFERRED_FIXTURE_IDS"
    ]
    assert isinstance(deferred_fixture_ids, ast.Tuple)
    assert all(
        isinstance(element, ast.Constant) and isinstance(element.value, str)
        for element in deferred_fixture_ids.elts
    )


def test_projection_excludes_exact_deferred_fixture_positive_control() -> None:
    projection = contract._project_stage0_blockers(
        contract.load_manifest()["required_gates"]["entries"],
        contract.load_fixture_cases(),
    )
    assert projection["raw_pending_fixture_ids"] == EXPECTED_DEFERRED_FIXTURE_IDS
    assert projection["unresolved_deferred_fixture_ids"] == (
        EXPECTED_DEFERRED_FIXTURE_IDS
    )
    assert projection["excluded_stage0_pending_fixture_ids"] == (
        EXPECTED_DEFERRED_FIXTURE_IDS
    )
    assert projection["stage0_blocking_pending_fixture_ids"] == ()
    assert projection["excluded_stage0_gate_ids"] == EXPECTED_DEFERRED_GATE_IDS


def test_projection_retains_exact_nonassignment_blocking_gates() -> None:
    projection = contract._project_stage0_blockers(
        contract.load_manifest()["required_gates"]["entries"],
        contract.load_fixture_cases(),
    )
    assert projection["raw_blocking_gate_ids"] == (
        "CFAB-STAGE6-POLICY-PREDICATE",
        "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
        "FREEZE-AX-TOPOLOGY",
        "FREEZE-CONFORMANCE-LITERAL",
    )
    assert projection["stage0_blocking_gate_ids"] == (
        EXPECTED_STAGE0_BLOCKING_GATE_IDS
    )


def test_projection_requires_stage1_and_later_owner() -> None:
    cases = ({"fixture_id": "owned-case", "binding_state": "pending"},)
    for owner in ("user", "lower-impl-wave", "lower-wa-wave"):
        gates = (
            {
                "gate_id": f"OWNED-BY-{owner}",
                "owned_fixture_ids": ["owned-case"],
                "owner": owner,
                "status": "pending",
            },
        )
        projection = contract._project_stage0_blockers(gates, cases)
        assert projection["excluded_stage0_pending_fixture_ids"] == ()
        assert projection["excluded_stage0_gate_ids"] == ()
        assert projection["stage0_blocking_gate_ids"] == (f"OWNED-BY-{owner}",)


def test_projection_rejects_unknown_owned_fixture() -> None:
    gates = (
        {
            "gate_id": "FIXTURE-ASSIGNMENT",
            "owned_fixture_ids": ["unknown-case"],
            "owner": "stage1-and-later",
            "status": "pending",
        },
    )
    try:
        contract._project_stage0_blockers(gates, ())
    except contract.ContractError as exc:
        assert str(exc) == (
            "owned_fixture_ids names an unknown fixture: unknown-case"
        )
    else:
        raise AssertionError("an unknown owned fixture was projected out")


def test_projection_rejects_owned_executable_case() -> None:
    gates = (
        {
            "gate_id": "FIXTURE-ASSIGNMENT",
            "owned_fixture_ids": ["executable-case"],
            "owner": "stage1-and-later",
            "status": "pending",
        },
    )
    cases = ({"fixture_id": "executable-case", "binding_state": "executable"},)
    try:
        contract._project_stage0_blockers(gates, cases)
    except contract.ContractError as exc:
        assert str(exc) == (
            "owned_fixture_ids may contain only pending fixture cases: "
            "executable-case"
        )
    else:
        raise AssertionError("an executable owned fixture was projected out")


def test_deferred_fixture_three_way_match_rejects_manifest_and_design_drift_together(
) -> None:
    manifest_ids = EXPECTED_DEFERRED_FIXTURE_IDS[:-1]
    design_ids = EXPECTED_DEFERRED_FIXTURE_IDS[:-1]
    try:
        contract._validate_stage0_deferred_fixture_ids(manifest_ids, design_ids)
    except contract.ContractError as exc:
        assert str(exc) == (
            "stage 0 deferred fixture IDs do not exactly match "
            "manifest/module/design declarations"
        )
    else:
        raise AssertionError("manifest/design drift bypassed the independent module literal")


def test_owned_fixture_ids_must_be_nonempty(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _gate_by_id(
            document, "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT"
        )["owned_fixture_ids"] = []

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "owned_fixture_ids must be non-empty",
    )


def test_owned_fixture_ids_must_be_unique_and_sorted(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def duplicate(document: dict[str, Any]) -> None:
        owned = _gate_by_id(
            document, "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT"
        )["owned_fixture_ids"]
        owned.append(owned[-1])

    _rewrite_manifest(fixture_root, duplicate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "owned_fixture_ids has duplicate fixture IDs",
    )

    fixture_root, design_doc = _synthetic_repository(tmp_path / "reordered")

    def reorder(document: dict[str, Any]) -> None:
        owned = _gate_by_id(
            document, "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT"
        )["owned_fixture_ids"]
        owned.reverse()

    _rewrite_manifest(fixture_root, reorder)
    _assert_rejected(
        fixture_root,
        design_doc,
        "owned_fixture_ids must use fixture ID order",
    )


def test_owned_fixture_ids_on_nonassignment_owner_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        _gate_by_id(
            document, "CFAB-STAGE6-POLICY-PREDICATE"
        )["owned_fixture_ids"] = [EXPECTED_DEFERRED_FIXTURE_IDS[0]]

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "owned_fixture_ids requires owner 'stage1-and-later'",
    )


def _fixture_obligation_summary(
    *, binding_state: str, assignment_status: str
) -> dict[str, Any]:
    synthetic_manifest = {
        "required_gates": {
            "entries": [
                {
                    "gate_id": EXPECTED_DEFERRED_GATE_IDS[0],
                    "owned_fixture_ids": list(EXPECTED_DEFERRED_FIXTURE_IDS),
                    "owner": "stage1-and-later",
                    "status": assignment_status,
                },
                {
                    "gate_id": "CFAB-STAGE6-POLICY-PREDICATE",
                    "owner": "user",
                    "status": "resolved",
                },
                {
                    "gate_id": "FREEZE-AX-TOPOLOGY",
                    "owner": "lower-impl-wave",
                    "status": "resolved",
                },
                {
                    "gate_id": "FREEZE-CONFORMANCE-LITERAL",
                    "owner": "lower-wa-wave",
                    "status": "resolved",
                },
            ]
        }
    }
    cases = tuple(
        {"fixture_id": fixture_id, "binding_state": binding_state}
        for fixture_id in EXPECTED_DEFERRED_FIXTURE_IDS
    )
    projection = contract._project_stage0_blockers(
        synthetic_manifest["required_gates"]["entries"], cases
    )
    expected_stage0_blocking_pending_fixture_ids = (
        EXPECTED_DEFERRED_FIXTURE_IDS
        if binding_state == "pending" and assignment_status == "resolved"
        else ()
    )
    assert projection["stage0_blocking_pending_fixture_ids"] == (
        expected_stage0_blocking_pending_fixture_ids
    )
    assert projection["stage0_blocking_gate_ids"] == ()
    return {
        "status": (
            "incomplete"
            if expected_stage0_blocking_pending_fixture_ids
            else "complete"
        ),
        "raw_pending_count": len(projection["raw_pending_fixture_ids"]),
        "raw_pending_fixture_ids": projection["raw_pending_fixture_ids"],
        "unresolved_deferred_fixture_ids": projection[
            "unresolved_deferred_fixture_ids"
        ],
        "deferred_fixture_ids": projection[
            "excluded_stage0_pending_fixture_ids"
        ],
        "deferred_gate_ids": projection["excluded_stage0_gate_ids"],
    }


def test_deferred_fixture_obligations_are_rejected_even_when_stage0_projection_complete(
    monkeypatch: Any,
) -> None:
    summary = _fixture_obligation_summary(
        binding_state="pending", assignment_status="pending"
    )
    monkeypatch.setattr(
        contract, "validate_repository", lambda *_args, **_kwargs: summary
    )

    try:
        contract.require_stage0_fixture_obligations_discharged()
    except contract.ContractError as exc:
        assert str(exc) == (
            "stage 0 fixture obligations are not discharged: "
            "raw_pending_count=5, unresolved_deferred_fixture_ids=["
            "approved-freeze-reference,bundle-identity-propagation,"
            "candidate-type-preservation,floor-seal-consistency,"
            "post-cutoff-bundle-identity], deferred_gate_ids=["
            "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT]"
        )
    else:
        raise AssertionError("deferred fixture obligations were treated as discharged")


def test_unresolved_deferred_fixture_ids_survive_resolved_assignment_gate(
    monkeypatch: Any,
) -> None:
    summary = _fixture_obligation_summary(
        binding_state="pending", assignment_status="resolved"
    )
    assert summary["deferred_fixture_ids"] == ()
    assert summary["deferred_gate_ids"] == ()
    assert summary["unresolved_deferred_fixture_ids"] == (
        EXPECTED_DEFERRED_FIXTURE_IDS
    )
    monkeypatch.setattr(
        contract, "validate_repository", lambda *_args, **_kwargs: summary
    )

    try:
        contract.require_stage0_fixture_obligations_discharged()
    except contract.ContractError as exc:
        assert str(exc) == (
            "stage 0 fixture obligations are not discharged: "
            "raw_pending_count=5, unresolved_deferred_fixture_ids=["
            "approved-freeze-reference,bundle-identity-propagation,"
            "candidate-type-preservation,floor-seal-consistency,"
            "post-cutoff-bundle-identity], deferred_gate_ids=[]"
        )
    else:
        raise AssertionError(
            "pending deferred fixtures disappeared after assignment resolved"
        )


def test_fixture_obligations_accept_all_executable_and_resolved_assignment(
    monkeypatch: Any,
) -> None:
    summary = _fixture_obligation_summary(
        binding_state="executable", assignment_status="resolved"
    )
    monkeypatch.setattr(
        contract, "validate_repository", lambda *_args, **_kwargs: summary
    )

    assert contract.require_stage0_fixture_obligations_discharged() is summary


def test_stage0_complete_predicate_does_not_call_fixture_obligation_predicate(
) -> None:
    source = inspect.getsource(contract.require_stage0_complete)
    assert "require_stage0_fixture_obligations_discharged" not in source


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


def test_r1_revocation_record_required_gate_removed_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        entries = document["required_gates"]["entries"]
        entries.remove(_gate_by_id(document, "CFAB-R1-REVOCATION-RECORD"))
        document["required_gates"]["count"] = len(entries)
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates entries do not exactly match",
    )


def test_r4_cancellation_record_required_gate_removed_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        entries = document["required_gates"]["entries"]
        entries.remove(_gate_by_id(document, "CFAB-R4-CANCELLATION-RECORD"))
        document["required_gates"]["count"] = len(entries)
        _refresh_entries_sha(document, "required_gates")

    _rewrite_manifest(fixture_root, mutate)
    _assert_rejected(
        fixture_root,
        design_doc,
        "required_gates entries do not exactly match",
    )


def test_stage6_policy_gate_cannot_be_resolved_early(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)

    def mutate(document: dict[str, Any]) -> None:
        entries = document["required_gates"]["entries"]
        _gate_by_id(document, "CFAB-STAGE6-POLICY-PREDICATE")["status"] = (
            "resolved"
        )
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


def test_design_fenced_decoy_is_not_authoritative(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_REVOCATION_TABLE_MARKER
    table = (
        marker
        + "\n\n"
        + contract._UPPER_REVOCATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_REVOCATION_SCHEMA
        )
    )
    target = "| `scope` | 逐語 `bundle-only` |"
    replacement = "| `scope` | 非空 string |"
    assert text.count(marker) == 1
    assert text.count(target) == 1
    text = text.replace(target, replacement, 1)
    text = text.replace(marker, f"```text\n{table}\n\n```\n\n{marker}", 1)
    design_doc.write_text(text, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation record schema does not exactly match validator schema",
    )


def test_design_cancellation_fenced_decoy_is_not_authoritative(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_CANCELLATION_TABLE_MARKER
    table = (
        marker
        + "\n\n"
        + contract._UPPER_CANCELLATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_CANCELLATION_SCHEMA
        )
    )
    target = "| `scope` | 逐語 `fork-loser-only` |"
    replacement = "| `scope` | 非空 string |"
    assert text.count(marker) == 1
    assert text.count(target) == 1
    text = text.replace(target, replacement, 1)
    text = text.replace(marker, f"```text\n{table}\n\n```\n\n{marker}", 1)
    design_doc.write_text(text, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation record schema does not exactly match validator schema",
    )


def test_design_revocation_plaintext_decoy_declaration_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_REVOCATION_TABLE_MARKER
    table = (
        marker
        + "\n\n"
        + contract._UPPER_REVOCATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_REVOCATION_SCHEMA
        )
    )
    broken_marker = marker.replace("束当たり 0/1 件", "束当たり 0/1件")
    assert broken_marker != marker
    assert text.count(marker) == 1
    text = text.replace(marker, f"注記: {table}\n\n{broken_marker}", 1)
    design_doc.write_text(text, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation record declaration is missing or duplicated",
    )


def test_design_cancellation_plaintext_decoy_declaration_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_CANCELLATION_TABLE_MARKER
    table = (
        marker
        + "\n\n"
        + contract._UPPER_CANCELLATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_CANCELLATION_SCHEMA
        )
    )
    broken_marker = marker.replace(
        "取消対象 pointer あたり\n0/1 件",
        "取消対象 pointer あたり 0/1 件",
    )
    assert broken_marker != marker
    assert text.count(marker) == 1
    text = text.replace(marker, f"注記: {table}\n\n{broken_marker}", 1)
    design_doc.write_text(text, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation record declaration is missing or duplicated",
    )


def test_design_revocation_fullwidth_homoglyph_decoy_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_REVOCATION_TABLE_MARKER
    table = _revocation_table(text)
    fullwidth_marker = marker.replace("record R", "record Ｒ")
    assert fullwidth_marker != marker
    mutated_table = table.replace(marker, fullwidth_marker, 1)
    target = "| `scope` | 逐語 `bundle-only` |"
    assert mutated_table.count(target) == 1
    mutated_table = mutated_table.replace(target, "| `scope` | 非空 string |", 1)
    decoy_table = (
        marker
        + "\n\n"
        + contract._UPPER_REVOCATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_REVOCATION_SCHEMA
        )
    )
    assert text.count(table) == 1
    poisoned = text.replace(table, decoy_table + "\n\n" + mutated_table, 1)
    assert poisoned.count(marker) == 1
    assert poisoned.count(fullwidth_marker) == 1
    design_doc.write_text(poisoned, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation record declaration is missing or duplicated",
    )


def test_design_cancellation_fullwidth_homoglyph_decoy_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    marker = contract._UPPER_CANCELLATION_TABLE_MARKER
    table = _cancellation_table(text)
    fullwidth_marker = marker.replace("record C", "record Ｃ")
    assert fullwidth_marker != marker
    mutated_table = table.replace(marker, fullwidth_marker, 1)
    target = "| `scope` | 逐語 `fork-loser-only` |"
    assert mutated_table.count(target) == 1
    mutated_table = mutated_table.replace(target, "| `scope` | 非空 string |", 1)
    decoy_table = (
        marker
        + "\n\n"
        + contract._UPPER_CANCELLATION_TABLE_HEADER
        + "\n".join(
            f"| `{key}` | {constraint} |"
            for key, constraint in contract._UPPER_CANCELLATION_SCHEMA
        )
    )
    assert text.count(table) == 1
    poisoned = text.replace(table, decoy_table + "\n\n" + mutated_table, 1)
    assert poisoned.count(marker) == 1
    assert poisoned.count(fullwidth_marker) == 1
    design_doc.write_text(poisoned, encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation record declaration is missing or duplicated",
    )


def _revocation_table(text: str) -> str:
    prefix = (
        contract._UPPER_REVOCATION_TABLE_MARKER
        + "\n\n"
        + contract._UPPER_REVOCATION_TABLE_HEADER
    )
    assert text.count(prefix) == 1
    start = text.index(prefix)
    end = text.index("\n\n", start + len(prefix))
    return text[start:end]


def _cancellation_table(text: str) -> str:
    prefix = (
        contract._UPPER_CANCELLATION_TABLE_MARKER
        + "\n\n"
        + contract._UPPER_CANCELLATION_TABLE_HEADER
    )
    assert text.count(prefix) == 1
    start = text.index(prefix)
    end = text.index("\n\n", start + len(prefix))
    return text[start:end]


def _move_revocation_table_into_fence(
    design_doc: Path,
    *,
    fence: str,
) -> None:
    text = design_doc.read_text(encoding="utf-8")
    table = _revocation_table(text)
    marker = contract._UPPER_REVOCATION_TABLE_MARKER
    assert table.startswith(marker)
    table_body = table[len(marker) :].lstrip("\n")
    table_with_terminator = table + "\n\n"
    assert text.count(table_with_terminator) == 1
    design_doc.write_text(
        text.replace(
            table_with_terminator,
            f"{marker}\n\n{fence}text\n{table_body}\n{fence}\n\n",
            1,
        ),
        encoding="utf-8",
    )


def _move_cancellation_table_into_fence(
    design_doc: Path,
    *,
    fence: str,
) -> None:
    text = design_doc.read_text(encoding="utf-8")
    table = _cancellation_table(text)
    marker = contract._UPPER_CANCELLATION_TABLE_MARKER
    assert table.startswith(marker)
    table_body = table[len(marker) :].lstrip("\n")
    table_with_terminator = table + "\n\n"
    assert text.count(table_with_terminator) == 1
    design_doc.write_text(
        text.replace(
            table_with_terminator,
            f"{marker}\n\n{fence}text\n{table_body}\n{fence}\n\n",
            1,
        ),
        encoding="utf-8",
    )


def _move_stage6_row_into_fence(design_doc: Path, *, fence: str) -> None:
    text = design_doc.read_text(encoding="utf-8")
    rows = [
        line
        for line in text.splitlines(keepends=True)
        if line.startswith("| 6 | 発効 X |")
    ]
    assert len(rows) == 1
    row = rows[0]
    design_doc.write_text(
        text.replace(row, f"{fence}text\n{row}{fence}\n", 1),
        encoding="utf-8",
    )


def test_design_revocation_table_only_in_tilde_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_revocation_table_into_fence(design_doc, fence="~~~")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation table is missing or duplicated",
    )


def test_design_revocation_table_only_in_long_backtick_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_revocation_table_into_fence(design_doc, fence="````")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation table is missing or duplicated",
    )


def test_design_cancellation_table_only_in_tilde_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_cancellation_table_into_fence(design_doc, fence="~~~")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation table is missing or duplicated",
    )


def test_design_cancellation_table_only_in_long_backtick_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_cancellation_table_into_fence(design_doc, fence="````")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation table is missing or duplicated",
    )


def test_design_stage6_row_only_in_tilde_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_stage6_row_into_fence(design_doc, fence="~~~")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 row is missing or duplicated",
    )


def test_design_stage6_row_only_in_long_backtick_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    _move_stage6_row_into_fence(design_doc, fence="````")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 row is missing or duplicated",
    )


def test_design_unclosed_fence_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(text + "\n```text\nunclosed\n", encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_long_fence_is_not_closed_by_shorter_marker(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(text + "\n````text\nhidden\n```\n", encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_fence_is_not_closed_by_different_marker(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(text + "\n~~~text\nhidden\n```\n", encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_invalid_backtick_info_decoy_is_rejected(
    tmp_path: Path,
) -> None:
    """invalid-info 検査を外すと唯一の canonical 表として受理される。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    table = _revocation_table(text)
    assert text.count(table) == 1
    design_doc.write_text(
        text.replace(
            table,
            f"```text`invalid\n{table}",
            1,
        ),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "invalid backtick fence info string",
    )


def test_design_tab_indented_fence_decoy_is_rejected(
    tmp_path: Path,
) -> None:
    """tab を indent 1 と数える実装だけが canonical decoy を受理する。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    table = _revocation_table(text)
    target = "| `scope` | 逐語 `bundle-only` |"
    assert table.count(target) == 1
    relaxed_table = table.replace(target, "| `scope` | 非空 string |", 1)
    assert text.count(table) == 1
    design_doc.write_text(
        text.replace(
            table,
            (
                f"\t```text\n{relaxed_table}\n```\n"
                f"{table}\n\t```\n```"
            ),
            1,
        ),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "fence marker with invalid indentation",
    )


def test_design_tilde_fence_info_may_contain_backtick(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n~~~text`valid\nnon-authoritative decoy\n~~~\n",
        encoding="utf-8",
    )
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_longer_fence_closer_is_accepted(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n````text\nnon-authoritative decoy\n`````\n",
        encoding="utf-8",
    )
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_tab_indented_fence_closer_is_rejected(tmp_path: Path) -> None:
    """正当な opener に対する closer 側の invalid indent だけを拒否する。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n```text\nnon-authoritative decoy\n\t```\n",
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "fence marker with invalid indentation",
    )


def test_design_three_space_indented_fence_closer_is_accepted(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n```text\nnon-authoritative decoy\n   ```\n",
        encoding="utf-8",
    )
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_fence_closer_with_non_whitespace_suffix_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n```text\nnon-authoritative decoy\n```spoof\n",
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_fence_closer_without_suffix_is_accepted(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n```text\nnon-authoritative decoy\n```\n",
        encoding="utf-8",
    )
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_space_tab_indented_fence_opener_is_rejected(
    tmp_path: Path,
) -> None:
    """1 space 後の tab は次の tab stop、つまり column 4 まで進む。"""

    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n \t```text\nnon-authoritative decoy\n```\n",
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "fence marker with invalid indentation",
    )


def test_design_three_space_indented_fence_opener_is_accepted(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n   ```text\nnon-authoritative decoy\n```\n",
        encoding="utf-8",
    )
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_crlf_unclosed_fence_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_bytes()
    design_doc.write_bytes(
        text + b"\r\n```text\r\nnon-authoritative decoy\r\n"
    )
    assert b"\r\n```text\r\n" in design_doc.read_bytes()
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_crlf_fence_is_accepted(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_bytes()
    design_doc.write_bytes(
        text + b"\r\n```text\r\nnon-authoritative decoy\r\n```\r\n"
    )
    assert b"\r\n```text\r\n" in design_doc.read_bytes()
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_short_fence_closer_with_trailing_spaces_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n````text\nnon-authoritative decoy\n```" + "   " + "\n",
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design document has an unclosed fenced code block",
    )


def test_design_fence_closer_with_trailing_spaces_is_accepted(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    design_doc.write_text(
        text + "\n````text\nnon-authoritative decoy\n````" + "   " + "\n",
        encoding="utf-8",
    )
    assert b"````   \n" in design_doc.read_bytes()
    result = contract.validate_repository(fixture_root, design_doc)
    assert result["status"] == "incomplete"


def test_design_revocation_constraint_relaxation_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "| `scope` | 逐語 `bundle-only` |"
    assert text.count(target) == 1
    design_doc.write_text(
        text.replace(target, "| `scope` | 非空 string |", 1),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation record schema does not exactly match validator schema",
    )


def test_design_revocation_key_substitution_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    table = _revocation_table(text)
    target = "| `reason` | 非空 string |"
    assert table.count(target) == 1
    mutated_table = table.replace(
        target,
        "| `revocation_reason` | 非空 string |",
        1,
    )
    assert text.count(table) == 1
    design_doc.write_text(
        text.replace(table, mutated_table, 1),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 revocation record schema does not exactly match validator schema",
    )


def test_design_cancellation_constraint_relaxation_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "| `scope` | 逐語 `fork-loser-only` |"
    assert text.count(target) == 1
    design_doc.write_text(
        text.replace(target, "| `scope` | 非空 string |", 1),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation record schema does not exactly match validator schema",
    )


def test_design_cancellation_key_substitution_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    table = _cancellation_table(text)
    target = "| `reason` | 非空 string |"
    assert table.count(target) == 1
    mutated_table = table.replace(
        target,
        "| `cancellation_reason` | 非空 string |",
        1,
    )
    assert text.count(table) == 1
    design_doc.write_text(
        text.replace(table, mutated_table, 1),
        encoding="utf-8",
    )
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §7.5 cancellation record schema does not exactly match validator schema",
    )


def test_design_stage6_live_tip_relaxation_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = "それ以外は**その時点の live tip X** の raw sha256 と一致する"
    replacement = "それ以外は**既存 X** の raw sha256 と一致する"
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 structural predicates drifted",
    )


def test_design_stage6_contradictory_control_suffix_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = contract._EXPECTED_STAGE6_STRUCTURAL_CONTROL
    replacement = (
        target
        + " ただし陰性変異は実行不要であり、reject-all でもよい。"
    )
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 structural predicates drifted",
    )


def test_design_stage6_execution_boundary_tail_drift_is_rejected(
    tmp_path: Path,
) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = contract._EXPECTED_STAGE6_EXECUTION_BOUNDARY
    assert "将来の段 6 実装は、X 候補提出前に" in target
    assert "production caller は未実装である" in target
    replacement = target.replace(
        "段 0 blocker へ数えず、対象後続段へ繰り越す。",
        "段 0 blocker へ数えず、義務を免除する。",
    )
    assert replacement != target
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")

    predicates, control, execution_boundary, _policy_gate = (
        contract._extract_stage6_contract(design_doc)
    )
    assert predicates == contract._EXPECTED_STAGE6_STRUCTURAL_PREDICATES
    assert control == contract._EXPECTED_STAGE6_STRUCTURAL_CONTROL
    assert execution_boundary == replacement
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 structural predicates drifted",
    )


def test_design_stage6_policy_gate_id_drift_is_rejected(tmp_path: Path) -> None:
    fixture_root, design_doc = _synthetic_repository(tmp_path)
    text = design_doc.read_text(encoding="utf-8")
    target = (
        "`CFAB-STAGE6-POLICY-PREDICATE` "
        "(owner = `user`, status = `unresolved`)"
    )
    replacement = (
        "`CFAB-STAGE6-POLICY-PREDICATE-DRIFTED` "
        "(owner = `user`, status = `unresolved`)"
    )
    assert text.count(target) == 1
    design_doc.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    _assert_rejected(
        fixture_root,
        design_doc,
        "design §10 stage 6 policy gate does not exactly match required_gates",
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
